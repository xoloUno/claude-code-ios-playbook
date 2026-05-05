Quick session orientation — run this at the start of every session.

Steps:
1. Read CLAUDE.md and summarize the **Current State** section (last updated date,
   build status, last completed work, next up)
2. Read the latest entry in `WORKLOG.md` (if it exists) — show date and key points
3. Run `git log --oneline -10` — show recent commits
4. Run `git branch --show-current` — confirm which branch we're on
5. Run `git status` — flag any uncommitted changes from a previous session.
   If uncommitted changes exist, ask the user whether to commit, stash, or discard
   before proceeding.
6. Check if `MANUAL-TASKS.md` exists and has unchecked items (`- [ ]`). If so,
   list them and ask if any have been completed.
7. Check for open Dependabot PRs: `gh pr list --label dependencies --state open`
   (if `gh` is available). Mention any that are open.
8. Check if the project has a `.playbook-version` file. If it exists, compare against
   the playbook's CHANGELOG.md to see if there are newer entries. If outdated, suggest
   running `/upgrade`.

Present all of this as a concise briefing — not a wall of text. Use this format:

```
## Session Briefing

**Project:** [app name] | **Branch:** [branch] | **Build:** [status]
**Last session:** [date] — [one-line summary from WORKLOG]
**Next up:** [from Current State]

### Flags
- ⚠️ [any uncommitted changes, pending manual tasks, stale rules, open Dependabot PRs]
- ✓ Clean — no flags [if nothing to report]
```

After presenting the briefing, ask: "What would you like to work on?"
