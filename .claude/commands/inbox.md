Log a lesson learned to the shared playbook inbox.

If $ARGUMENTS is provided, use it as the lesson description. Otherwise, ask the user
what they want to capture.

Steps:
1. Determine the lesson to log. If $ARGUMENTS is empty, ask the user:
   "What did you discover? (gotcha, pattern, suggestion, correction, tooling tip)"
2. Read the project's CLAUDE.md to get the app name for the entry
3. Classify the category: gotcha | suggestion | pattern | correction | tooling
4. Resolve the inbox file, using the first option that yields an existing playbook
   directory (the inbox is `<playbook>/inbox.md`):
   a. The `$PLAYBOOK_HOME` environment variable, if set.
   b. The `PLAYBOOK_HOME` value in `~/.config/playbook/config` (`source` it, or grep the line).
   c. Legacy fallback — the `**Inbox location:**` line in `.claude/rules/playbook-inbox.md`
      (in a composed copy it holds the resolved absolute path). Skip this if the line still
      holds an unsubstituted token — `$PLAYBOOK_HOME` (a live symlinked rule) or legacy
      `PLAYBOOK_PATH`.
   d. If none resolve, ask the user for the playbook directory.
   Then write a new entry at the bottom of the inbox file (just above any trailing whitespace).

Entry format:
```markdown
### [TODAY'S DATE] — [APP_NAME from CLAUDE.md]

**Category:** [category]
**Context:** [what was being worked on in this session — infer from recent activity]
**Lesson:** [the insight — be specific and actionable]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

5. Confirm to the user what was logged and where

If none of the options in step 4 yield an existing inbox file, tell the user the playbook
path needs to be configured (`$PLAYBOOK_HOME` / `~/.config/playbook/config`).
