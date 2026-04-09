---
description: Session startup and end checklists for Claude Code sessions
globs: **/CLAUDE.md
---

# Session Startup Checklist

1. Read CLAUDE.md fully
2. **Read `WORKLOG.md`** — review recent session history for context
3. `git log --oneline -10` — see recent changes
4. Verify correct branch (create one if needed)
5. Check GitHub Actions for last build status
6. **Check `MANUAL-TASKS.md`** — are there pending human tasks from last session?
7. **Check for open Dependabot PRs** — merge any dependency updates if CI passes
8. Which v1 feature are we building? Is it IN SCOPE?
9. Re-read any files you're about to edit
10. Framework introduced after WWDC25? Use apple-docs MCP to verify API first
11. Ask the user what to work on if not specified

# Session End Checklist

1. `git status` — review everything
2. Stage selectively, write conventional commit
3. Push to `dev` or feature branch
4. **Update "Current State"** in CLAUDE.md (mandatory)
5. **Update `WORKLOG.md`** with detailed session diary entry (see work-log rule)
6. Check off completed scope items
7. **Update `release-notes-draft.md`** with user-facing changes
8. **Create/update `MANUAL-TASKS.md`** if there are human-only tasks (see manual-tasks rule)
