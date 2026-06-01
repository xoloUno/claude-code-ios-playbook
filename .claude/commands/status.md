Quick session orientation — run at the start of every session.

This is the **universal** `/status`. It runs the same in any project — the playbook
repo itself, an iOS app, a Python tool. Everything kind- or project-specific is
layered on at runtime from a profile (see the load-first hook); this file holds only
what is true everywhere.

## Load first — bind the project profile, then report

Before gathering anything, read these files **if present** and merge the steps under
their `## /status` heading into the briefing below. `/status` mutates nothing, so a
read-only briefing may fold the extra checks in anywhere:

- `.claude/command-profile.md` — the kind layer (iOS, Python, …): type-level checks.
- `.claude/command-profile.local.md` — this project's own escape-hatch checks.
- `.claude/project.yml` — declarative facts (`kind`, `test_command`, `version_files`, …)
  the checks above may reference.

If none are present, the universal steps stand alone.

## Universal steps

1. `git branch --show-current` and `git status --short` — current branch + dirty state.
2. `git log --oneline -5` — recent commits on the current branch.
3. `git rev-list --left-right --count @{upstream}...HEAD 2>/dev/null` — ahead/behind vs
   the branch's upstream. Always `@{upstream}`, never a hardcoded `origin/main`: it
   resolves to whatever this branch tracks and stays silent when there is no upstream.
4. Open PRs: `gh pr list --state open --limit 10` (if `gh` is available).
5. If `CLAUDE.md` is present **and** has a "Current State" / "current status" section,
   summarize it (last-updated date, what's in flight, next up). If it has no such
   section — e.g. a principles-only operating guide — skip it; don't invent one.
6. If `WORKLOG.md` is present, read its latest entry — show the date and key points.
7. If `MANUAL-TASKS.md` is present with unchecked items (`- [ ]`), list them and ask
   whether any are now done.

Then fold in whatever `## /status` checks the profile files contributed.

## Briefing format

Present a concise briefing — not a wall of text. The header carries the universal
fields; the profile contributes its own headline lines (build, version, CI, phase,
inbox count, …):

```
## Session Briefing

**Branch:** <branch> | **vs upstream:** <N ahead, M behind, or "no upstream">
<profile headline lines, if any>

### Recent commits
<git log --oneline -5 output>

### Open PRs
- #<N> <title> — <branch>

### Flags
- ⚠️ <uncommitted changes, stale branches, ahead-of-origin without push, profile flags>
- ✓ Clean — no flags <if nothing to report>
```

After presenting, ask: "What would you like to work on?"
