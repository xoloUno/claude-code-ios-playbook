Log a lesson learned to the shared playbook inbox.

If $ARGUMENTS is provided, use it as the lesson description. Otherwise, ask the user
what they want to capture.

Steps:
1. Determine the lesson to log. If $ARGUMENTS is empty, ask the user:
   "What did you discover? (gotcha, pattern, suggestion, correction, tooling tip)"
2. Read the project's CLAUDE.md to get the app name for the entry
3. Classify the category: gotcha | suggestion | pattern | correction | tooling
4. Write a new entry at the bottom of the inbox file (just above any trailing whitespace).
   The inbox file path is defined in `.claude/rules/playbook-inbox.md` — look for the
   line starting with `**Inbox location:**` to find the absolute path.

Entry format:
```markdown
### [TODAY'S DATE] — [APP_NAME from CLAUDE.md]

**Category:** [category]
**Context:** [what was being worked on in this session — infer from recent activity]
**Lesson:** [the insight — be specific and actionable]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

5. Confirm to the user what was logged and where

If the inbox file doesn't exist or the path in the rule is still `PLAYBOOK_PATH`
(not substituted), tell the user the playbook path needs to be configured.
