# Playbook Inbox

Lessons learned, gotchas, suggestions, and patterns discovered during Claude Code
sessions across all projects. Entries are written automatically by sessions in other
project directories. Periodically review this file in a dedicated playbook session to
curate worthwhile additions into the playbook, templates, or rules.

## How entries get here

Each bootstrapped project has a `.claude/rules/playbook-inbox.md` rule that tells
Claude Code to add entries here when it discovers something worth capturing.

## Curation process

In a Claude Code session in the `_playbook/` directory:
1. Read this file
2. Give each unnumbered entry the next entry number (below), raising the counter each time,
   then sort all entries newest first, with higher numbers first on the same date
3. For each entry, decide: **adopt** (update playbook/template/rules), **defer**, or **discard**
4. Adopted entries → make the change, then delete the entry
5. Deferred entries → leave them for next review
6. Discarded entries → delete them
7. If all entries are processed, leave only this header

## Entry format

**Next entry number:** 22

Capturing sessions append new entries at the bottom of this file without a number; curation
numbers them. Numbers are permanent IDs: never renumber an entry or reuse a removed number,
and keep the counter when the inbox is empty. Use the IDs when discussing entries. A numbered
entry's heading reads `### #[NUMBER] — [DATE] — [PROJECT_NAME]`.

```markdown
### [DATE] — [PROJECT_NAME]

**Category:** gotcha | suggestion | pattern | correction | tooling
**Context:** [what was being done when this was discovered]
**Lesson:** [the actual insight — be specific]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

---
