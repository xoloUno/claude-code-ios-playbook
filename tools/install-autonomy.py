#!/usr/bin/env python3
"""install-autonomy.py — install the guardrails behind the core "Autonomy" policy.

    python3 tools/install-autonomy.py --dry-run   # show what would change; write nothing
    python3 tools/install-autonomy.py             # show, then ask before writing
    python3 tools/install-autonomy.py --yes       # show, then write without asking

It merges settings/autonomy.json into ~/.claude/settings.json (lists are extended, never
replaced; the old file is backed up first), copies autonomy-guard.py and codex-review.sh into
~/.config/playbook/tools/, creates an empty ~/.config/playbook/pii-words.txt for you to fill,
and adds PLAYBOOK_AUTONOMY=off to ~/.config/playbook/config. Autonomy stays off until you
change that line to "on", after the canary. Re-running is safe: nothing is duplicated.
"""
import copy
import difflib
import json
import os
import re
import shutil
import stat
import sys
import time

PLAYBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
PB_DIR = os.path.join(HOME, ".config", "playbook")
TOOLS = os.path.join(PB_DIR, "tools")
CONFIG = os.path.join(PB_DIR, "config")
WORDS = os.path.join(PB_DIR, "pii-words.txt")
COPIES = ("autonomy-guard.py", "codex-review.sh")
WORDS_TEMPLATE = """\
# One word or phrase per line; matching ignores case. autonomy-guard.py blocks a push to a
# public repo when an outgoing commit's contents, message, author or committer contains one.
# Add your real name, email, home path (/Users/<you>), real bundle IDs, Team IDs, and the
# names of employers or clients. This file never leaves this machine.
"""


def merge(base, extra):
    out = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        elif isinstance(value, list) and isinstance(out.get(key), list):
            out[key] = out[key] + [v for v in value if v not in out[key]]
        else:  # the guardrail value wins; the diff shows the user what changes
            out[key] = copy.deepcopy(value)
    return out


def template():
    with open(os.path.join(PLAYBOOK, "settings", "autonomy.json")) as f:
        return json.loads(f.read().replace("__PLAYBOOK_HOME__", PLAYBOOK))


def read(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None


def plan():
    """Return [(path, old_text_or_None, new_text, mode)] for every file that would change.
    Order matters: the off switch is written first and the guard last, because the guard's
    presence is what enables autonomy, so a failure partway through leaves it off."""
    changes = []
    cfg = read(CONFIG) or ""
    if not re.search(r"^\s*(export\s+)?PLAYBOOK_AUTONOMY=", cfg, re.M):
        line = ("\n# Core \"Autonomy\" policy: keep off until the canary passes, then set to on.\n"
                "export PLAYBOOK_AUTONOMY=off\n")
        changes.append((CONFIG, read(CONFIG), cfg.rstrip("\n") + "\n" + line if cfg else
                        line.lstrip("\n"), None))
    if read(WORDS) is None:
        changes.append((WORDS, None, WORDS_TEMPLATE, 0o600))
    old = read(SETTINGS)
    current = json.loads(old) if old and old.strip() else {}
    new = json.dumps(merge(current, template()), indent=2) + "\n"
    if json.loads(new) != current:
        changes.append((SETTINGS, old, new, None))
    for name in reversed(COPIES):  # autonomy-guard.py last
        dst = os.path.join(TOOLS, name)
        src_text = read(os.path.join(PLAYBOOK, "tools", name))
        if read(dst) != src_text:
            changes.append((dst, read(dst), src_text, 0o755))
    return changes


def show(changes):
    if not changes:
        print("Nothing to change: the autonomy guardrails are already installed.")
        return
    for path, old, new, _ in changes:
        label = path.replace(HOME, "~", 1)
        if old is None:
            print(f"--- create {label}")
        sys.stdout.writelines(difflib.unified_diff(
            (old or "").splitlines(True), new.splitlines(True), label, label, n=2))
        print()


def apply(changes):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for path, old, new, mode in changes:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if path == SETTINGS and old is not None:
            shutil.copy2(path, f"{path}.bak-{stamp}")
        tmp = f"{path}.tmp-{stamp}"
        with open(tmp, "w") as f:
            f.write(new)
        if mode is None and old is not None:  # keep the existing file's permissions
            mode = stat.S_IMODE(os.stat(path).st_mode)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
        print(f"wrote {path.replace(HOME, '~', 1)}")
    print("\nAutonomy is installed but OFF. After the canary, set PLAYBOOK_AUTONOMY=on in "
          "~/.config/playbook/config. Fill in ~/.config/playbook/pii-words.txt first.")


def main(argv):
    if not set(argv) <= {"--dry-run", "--yes"}:
        sys.exit(__doc__)
    changes = plan()
    show(changes)
    if not changes or "--dry-run" in argv:
        return
    if "--yes" not in argv:
        try:
            answer = input("Apply these changes? [y/N] ")
        except EOFError:  # no terminal: treat as "no"
            answer = ""
        if answer.strip().lower() != "y":
            print("\nNothing written.")
            return
    apply(changes)


if __name__ == "__main__":
    main(sys.argv[1:])
