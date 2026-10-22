#!/usr/bin/env python3
"""autonomy-guard.py — Claude Code PreToolUse hook for the core "Autonomy" policy.

Installed by tools/install-autonomy.py to ~/.config/playbook/tools/. Its presence there is
what turns the core "Autonomy" section on (with PLAYBOOK_AUTONOMY not "off"). It reads the
hook JSON on stdin and prints a decision only when one is needed; silence means "no opinion",
and Claude Code's own permission rules still apply.

  deny  pushes to main/master or the remote's default branch, force pushes, --mirror, --all,
        --no-verify, and deleting a protected branch, in any spelling (git -C, -c, refspecs)
  deny  a push to a public repo whose outgoing commits contain a secret (gitleaks) or a word
        from ~/.config/playbook/pii-words.txt (contents, messages, author and committer)
  deny  Edit/Write into the playbook checkout from another project (inbox.md excepted)
  ask   tag pushes, other branch deletions, gh api writes, and a public push with no word list
  ask   commits, pushes, PR creation and merges while autonomy is off

Text parsing is best effort: it covers the spellings Claude writes, not a determined bypass.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".config", "playbook", "config")
WORDS = os.path.join(HOME, ".config", "playbook", "pii-words.txt")
PROTECTED = {"main", "master"}
SEPARATORS = {"&&", "||", ";", "|", "&", "|&", "(", ")"}
WRAPPERS = {"env", "command", "exec", "time", "nohup", "builtin"}
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
PUSH_OPTS_WITH_ARG = {"--repo", "--receive-pack", "--exec", "-o", "--push-option"}
FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def decide(kind, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": kind,
        "permissionDecisionReason": f"autonomy-guard: {reason}"}}))
    sys.exit(0)


def git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=20)
    return r.stdout.strip() if r.returncode == 0 else None


def config_value(name):
    if os.environ.get(name):
        return os.environ[name]
    try:
        with open(CONFIG) as f:
            for line in f:
                m = re.match(rf'\s*(?:export\s+)?{name}=["\']?([^"\'\s#]*)', line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return None


def autonomy_off(cwd):
    if (config_value("PLAYBOOK_AUTONOMY") or "").lower() == "off":
        return True
    root = git(cwd, "rev-parse", "--show-toplevel") or cwd
    try:
        with open(os.path.join(root, ".claude", "project.yml")) as f:
            return any(re.match(r"\s*autonomy:\s*['\"]?off\b", line) for line in f)
    except OSError:
        return False


def commands(text):
    """Split a shell command line into simple commands (lists of words)."""
    lex = shlex.shlex(text.replace("\n", ";"), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    out, cur = [], []
    try:
        for tok in lex:
            if tok in SEPARATORS:
                out.append(cur)
                cur = []
            else:
                cur.append(tok)
    except ValueError:  # unbalanced quotes: fall back to plain splitting
        return [text.split()]
    return [c for c in out + [cur] if c]


def strip_wrappers(words):
    while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in WRAPPERS):
        words = words[1:]
    return words


def parse_git(words, cwd):
    """Return (repo_dir, subcommand, args) for a git invocation, else None."""
    words = strip_wrappers(words)
    if not words or os.path.basename(words[0]) != "git":
        return None
    i, repo = 1, cwd
    while i < len(words) and words[i].startswith("-"):
        opt = words[i]
        if opt in GIT_OPTS_WITH_ARG and i + 1 < len(words):
            if opt == "-C":
                repo = os.path.join(repo, words[i + 1])
            i += 2
        else:
            i += 1
    if i >= len(words):
        return None
    return repo, words[i], words[i + 1:]


def current_branch(repo):
    return git(repo, "symbolic-ref", "--short", "-q", "HEAD")


def protected_names(repo, remote):
    names = set(PROTECTED)
    head = git(repo, "symbolic-ref", "--short", "-q", f"refs/remotes/{remote}/HEAD")
    if head and "/" in head:
        names.add(head.split("/", 1)[1])
    return names


def is_public(repo, remote):
    cached = git(repo, "config", "--get", "playbook.public")
    if cached in ("true", "false"):
        return cached == "true"
    url = git(repo, "remote", "get-url", remote)
    try:
        r = subprocess.run(["gh", "repo", "view", url or "", "--json", "visibility",
                            "-q", ".visibility"], capture_output=True, text=True, timeout=15)
        vis = r.stdout.strip().upper() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        vis = ""
    if vis in ("PUBLIC", "PRIVATE", "INTERNAL"):
        git(repo, "config", "playbook.public", "true" if vis == "PUBLIC" else "false")
        return vis == "PUBLIC"
    return True  # unknown visibility: scan as if public


def pii_words():
    try:
        with open(WORDS) as f:
            return [w.strip() for w in f if w.strip() and not w.lstrip().startswith("#")]
    except OSError:
        return []


def scan_outgoing(repo, remote, sources):
    words = pii_words()
    if not words:
        decide("ask", f"public repo push, but {WORDS} is missing or empty; add your personal "
                      "words (names, real bundle IDs, home paths) before pushing")
    shas = set()
    for src in sources:
        out = git(repo, "rev-list", src, "--not", f"--remotes={remote}") or ""
        shas.update(out.split())
    for sha in sorted(shas):
        text = git(repo, "show", "--format=%an%n%ae%n%cn%n%ce%n%B", sha) or ""
        low = text.lower()
        for w in words:
            if w.lower() in low:
                decide("deny", f"commit {sha[:7]} contains '{w}' from pii-words.txt; remove it "
                               "before pushing to a public repo")
    if shas:
        if not shutil.which("gitleaks"):
            decide("ask", "public repo push, but gitleaks isn't installed (brew install gitleaks)")
        spec = " ".join(sources) + f" --not --remotes={remote}"
        r = subprocess.run(["gitleaks", "git", repo, "--no-banner", "--redact",
                            f"--log-opts={spec}"], capture_output=True, text=True, timeout=120)
        if r.returncode == 1:
            decide("deny", "gitleaks found a secret in the outgoing commits")


def check_push(repo, args, off):
    flags, positional, i = [], [], 0
    while i < len(args):
        a = args[i]
        if a in PUSH_OPTS_WITH_ARG:
            i += 2
            continue
        (flags if a.startswith("-") else positional).append(a)
        i += 1
    if any(f in ("--dry-run", "-n") for f in flags):
        return
    if any(f in ("--force", "-f") or f.startswith(("--force-with-lease", "--force-if-includes"))
           for f in flags):
        decide("deny", "force pushes always need the user")
    if any(f in ("--mirror", "--all", "--branches") for f in flags):
        decide("deny", "this push would include the default branch")
    if "--no-verify" in flags:
        decide("deny", "--no-verify skips the push guards")
    remote = positional[0] if positional else (git(repo, "config", "--get",
              f"branch.{current_branch(repo)}.remote") or "origin")
    refspecs = positional[1:]
    protected = protected_names(repo, remote)
    deleting = any(f in ("--delete", "-d") for f in flags)
    tags = any(f in ("--tags", "--follow-tags") for f in flags)
    sources = []
    if not refspecs:
        branch = current_branch(repo)
        if branch in protected:
            decide("deny", f"pushing '{branch}' directly; open a PR instead")
        if branch:
            sources.append(branch)
    for spec in refspecs:
        if spec.startswith("+"):
            decide("deny", f"'{spec}' is a force push")
        src, _, dst = spec.partition(":")
        if not _:
            dst = src
        if src == "HEAD":
            src = current_branch(repo) or "HEAD"
        if dst == "HEAD":
            dst = current_branch(repo) or "HEAD"
        name = dst[len("refs/heads/"):] if dst.startswith("refs/heads/") else dst
        if deleting or (_ and not src):
            if name in protected:
                decide("deny", f"deleting '{name}' always needs the user")
            deleting = True
            continue
        if name in protected:
            decide("deny", f"pushing to '{name}' directly; open a PR instead")
        if dst.startswith("refs/tags/") or git(repo, "show-ref", "--verify", "-q",
                                               f"refs/tags/{src}") is not None:
            tags = True
        else:
            sources.append(src)
    if deleting:
        decide("ask", "deleting a remote branch: make sure it's merged")
    if tags:
        decide("ask", "tag pushes always need the user")
    if is_public(repo, remote):
        scan_outgoing(repo, remote, sources)
    if off:
        decide("ask", "autonomy is off: approve this push")


def check_gh(words, off):
    words = strip_wrappers(words)
    if not words or os.path.basename(words[0]) != "gh" or len(words) < 2:
        return
    sub = words[1:3]
    if sub[:2] in (["pr", "merge"], ["pr", "create"]) and off:
        decide("ask", f"autonomy is off: approve 'gh {' '.join(sub)}'")
    if sub[0] != "api":
        return
    args = words[2:]
    method, fields, endpoint = None, [], None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-X", "--method") and i + 1 < len(args):
            method = args[i + 1].upper()
            i += 2
            continue
        if a.startswith("--method="):
            method = a.split("=", 1)[1].upper()
        elif a in ("-f", "-F", "--field", "--raw-field") and i + 1 < len(args):
            fields.append(args[i + 1])
            i += 2
            continue
        elif a == "--input":
            fields.append("<input>")
        elif not a.startswith("-") and endpoint is None:
            endpoint = a
        i += 1
    if endpoint == "graphql":
        if any("mutation" in f for f in fields):
            decide("ask", "GitHub GraphQL mutation (repo settings or data)")
        return
    if (method or ("POST" if fields else "GET")) != "GET":
        decide("ask", "gh api write (repo settings or data)")


def check_bash(cmd, cwd, depth=0):
    off = autonomy_off(cwd)
    found_push = False
    for words in commands(cmd):
        inner = strip_wrappers(words)
        if depth < 3 and inner and os.path.basename(inner[0]) in ("sh", "bash", "zsh") \
                and "-c" in inner[1:-1]:
            check_bash(inner[inner.index("-c", 1) + 1], cwd, depth + 1)
        elif depth < 3 and inner and inner[0] == "eval":
            check_bash(" ".join(inner[1:]), cwd, depth + 1)
        parsed = parse_git(words, cwd)
        if parsed:
            repo, sub, args = parsed
            if sub == "push":
                found_push = True
                check_push(repo, args, off)
            elif sub == "commit" and off:
                decide("ask", "autonomy is off: approve this commit")
        check_gh(words, off)
    if not found_push and re.search(r"(\$\(|`)[^)`]*\bgit\b[^)`]*\bpush\b", cmd):
        decide("ask", "a git push inside a command substitution can't be checked")


def check_file_tool(tool_input, cwd):
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    home = config_value("PLAYBOOK_HOME")
    if not path or not home:
        return
    pb = os.path.realpath(os.path.expanduser(home))
    target = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    here = os.path.realpath(cwd)
    inside = lambda p: p == pb or p.startswith(pb + os.sep)
    if inside(target) and not inside(here) and target != os.path.join(pb, "inbox.md"):
        decide("deny", "edit the playbook from its own checkout and a PR; other projects may "
                       "only append to inbox.md")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    cwd = data.get("cwd") or os.getcwd()
    tool, tool_input = data.get("tool_name"), data.get("tool_input") or {}
    if tool == "Bash":
        check_bash(tool_input.get("command") or "", cwd)
    elif tool in FILE_TOOLS:
        check_file_tool(tool_input, cwd)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # never break the session; ask instead of guessing
        decide("ask", f"guard error ({type(e).__name__}: {e}); approve manually")
