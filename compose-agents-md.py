#!/usr/bin/env python3
"""compose-agents-md.py — render the playbook core block into a project's AGENTS.md.

Called by compose-claude.sh only when the project's AGENTS.md mentions a playbook core
marker (the explicit opt-in). Two subcommands:

  check <target> <playbook-dir>   validate everything; print "opted-in"; write nothing
  write <target> <playbook-dir>   validate again, then replace only the bytes between the
                                  markers (atomic; no write when nothing changed)

Opted-in layout (all must hold, or the command exits 2 and changes nothing):
  - AGENTS.md has exactly one line that is exactly BEGIN and one that is exactly END,
    BEGIN first, and no other line mentions a marker
  - AGENTS.md is a regular file, and CLAUDE.md is a symlink whose target is exactly
    "AGENTS.md" (relative, same directory). In local tests the symlink loaded from the
    repo root and from subdirectories, while an "@AGENTS.md" import did not load AGENTS.md
    in fresh, unapproved headless launches from a subdirectory. Any other CLAUDE.md is
    rejected.
  - .claude/CLAUDE.md does not exist
  - <playbook-dir>/core/agents-core.md exists, is non-empty, and contains no marker

Bytes outside the markers, including line endings, are never modified. Inserting the
markers the first time is a reviewed migration step, not something this script does.
"""
import os
import sys
import tempfile

BEGIN = b"<!-- playbook:core:begin -->"
END = b"<!-- playbook:core:end -->"
MARKER_PREFIX = b"playbook:core:"
ALIAS_TARGET = "AGENTS.md"


class LayoutError(Exception):
    pass


def _split_lines(data):
    """Split into lines that keep their terminators, so joining restores the exact bytes."""
    return data.splitlines(keepends=True)


def _content(line):
    return line.rstrip(b"\r\n")


def validate(target, playbook_dir):
    agents = os.path.join(target, "AGENTS.md")
    claude = os.path.join(target, "CLAUDE.md")
    source = os.path.join(playbook_dir, "core", "agents-core.md")

    if os.path.islink(agents):
        raise LayoutError("AGENTS.md is a symlink; opted-in projects need a regular file")
    if not os.path.isfile(agents):
        raise LayoutError("AGENTS.md is missing")
    if os.path.lexists(os.path.join(target, ".claude", "CLAUDE.md")):
        raise LayoutError(".claude/CLAUDE.md exists; it would load as a second instruction body")
    if not os.path.islink(claude) or os.readlink(claude) != ALIAS_TARGET:
        raise LayoutError("CLAUDE.md must be a symlink whose target is exactly 'AGENTS.md' "
                          "(ln -s AGENTS.md CLAUDE.md)")

    if not os.path.isfile(source):
        raise LayoutError(f"core block source not found: {source}")
    with open(source, "rb") as f:
        body = f.read()
    if not body.strip():
        raise LayoutError("core block source is empty")
    if MARKER_PREFIX in body:
        raise LayoutError("core block source must not contain marker text")

    with open(agents, "rb") as f:
        data = f.read()
    lines = _split_lines(data)
    begins = [i for i, l in enumerate(lines) if _content(l) == BEGIN]
    ends = [i for i, l in enumerate(lines) if _content(l) == END]
    stray = [i for i, l in enumerate(lines)
             if MARKER_PREFIX in l and i not in begins and i not in ends]
    if stray:
        raise LayoutError(f"AGENTS.md line {stray[0] + 1} mentions a marker but is not exactly a delimiter line")
    if len(begins) != 1 or len(ends) != 1:
        raise LayoutError(f"AGENTS.md needs exactly one begin and one end marker (found {len(begins)} and {len(ends)})")
    if begins[0] > ends[0]:
        raise LayoutError("AGENTS.md markers are reversed (end before begin)")
    return agents, data, lines, begins[0], ends[0], body


def render(lines, b, e, body):
    begin_line = lines[b]
    eol = b"\r\n" if begin_line.endswith(b"\r\n") else b"\n"
    body_lines = [_content(l) + eol for l in _split_lines(body)]
    return b"".join(lines[: b + 1]) + b"".join(body_lines) + b"".join(lines[e:])


def main(argv):
    if len(argv) != 4 or argv[1] not in ("check", "write"):
        print("usage: compose-agents-md.py check|write <target> <playbook-dir>", file=sys.stderr)
        return 64
    cmd, target, playbook_dir = argv[1], argv[2], argv[3]
    unchanged = "Nothing was written." if cmd == "check" else "AGENTS.md was not changed."
    try:
        agents, data, lines, b, e, body = validate(target, playbook_dir)
    except LayoutError as err:
        print(f"✗ AGENTS.md layout invalid: {err}. {unchanged}", file=sys.stderr)
        return 2
    except OSError as err:
        print(f"✗ could not read the layout: {err}. {unchanged}", file=sys.stderr)
        return 2
    if cmd == "check":
        print("opted-in")
        return 0
    new = render(lines, b, e, body)
    if new == data:
        print("✓ AGENTS.md core block already current")
        return 0
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(agents), prefix=".AGENTS.md.")
        with os.fdopen(fd, "wb") as f:
            f.write(new)
        os.chmod(tmp, os.stat(agents).st_mode & 0o777)
        os.replace(tmp, agents)
    except OSError as err:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        print(f"✗ could not write AGENTS.md: {err}. AGENTS.md was not changed.", file=sys.stderr)
        return 1
    print("✓ AGENTS.md core block updated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
