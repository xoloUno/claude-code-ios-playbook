Review and process the playbook inbox.

Steps:
1. Read `inbox.md` in this directory
2. If empty (no entries below the header), say "Inbox is empty — nothing to curate" and stop
3. For each entry, present it to the user with a recommendation:
   - **Adopt** — the lesson is worth adding to the playbook, a template, or a rule file.
     State specifically which file should change and what the change would be.
   - **Defer** — interesting but not actionable yet. Leave it for next review.
   - **Discard** — not useful, already covered, or too project-specific.
4. Ask the user for their decision on each entry (or let them batch: "adopt all", etc.)
5. For adopted entries:
   - Make the actual change to the appropriate file (playbook, CLAUDE-TEMPLATE.md,
     `.claude/rules/*.md`, `bootstrap.sh`, etc.)
   - Remove the entry from `inbox.md`
   - Add a CHANGELOG.md entry if the change is significant
6. For discarded entries: remove them from `inbox.md`
7. For deferred entries: leave them in `inbox.md`
8. After processing all entries, show a summary:
   - N adopted (list which files were changed)
   - N deferred
   - N discarded

Important:
- Read each referenced file before modifying it
- Keep changes minimal and consistent with existing style
- If an entry suggests a change that conflicts with existing playbook guidance, flag
  the conflict to the user rather than silently overriding
