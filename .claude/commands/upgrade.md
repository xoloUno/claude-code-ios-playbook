Sync this project with the latest playbook changes.

This command reads the playbook's CHANGELOG.md and applies changes that are newer than
this project's last upgrade.

Steps:
1. Read this project's `.playbook-version` file. If it doesn't exist, this project has
   never been upgraded — all CHANGELOG entries are relevant. Set the baseline to
   "beginning of time."
2. Determine the playbook location from `.claude/rules/playbook-inbox.md` — look for the
   line starting with `**Inbox location:**` and extract the directory path. If the rule
   doesn't exist or still has `PLAYBOOK_PATH`, ask the user for the playbook directory.
3. Read the playbook's `CHANGELOG.md`
4. Identify all entries with dates **after** the project's `.playbook-version` date
5. For each relevant entry (newest first), present:
   - What changed (summary)
   - The "How to upgrade your project" steps
   - Your recommendation: **apply** (you can make this change now), **skip** (not relevant
     to this project), or **manual** (needs human action)
6. Ask the user which entries to apply
7. For each applied entry:
   - Make the changes described in the upgrade steps
   - For rule file updates: copy the latest version from the playbook's `.claude/rules/`
     directory, re-applying the `PLAYBOOK_PATH` substitution if needed
   - For template/config changes: apply the specific changes described
8. After all entries are processed, update `.playbook-version` with today's date:
   ```
   # Last synced with playbook CHANGELOG
   2026-04-09
   ```
9. Add `.playbook-version` to git staging
10. Show a summary: N applied, N skipped, N manual (list manual items)

Important:
- Read each file before modifying it
- If a change conflicts with project-specific customizations, flag it and ask the user
- Never overwrite project-specific content in CLAUDE.md (scope, decisions, data models, etc.)
- Rule files can be replaced safely since they're generic; commands may have project tweaks
