Quick session orientation for the playbook — run at the start of every session.

This is the playbook repo itself, not a downstream iOS project. There's no
`CLAUDE.md`, no `WORKLOG.md`, no `MANUAL-TASKS.md`. The state of the world lives
in git, `CHANGELOG.md`, `inbox.md`, and open PRs.

Steps:
1. Run `git branch --show-current` and `git status --short` — current branch +
   dirty state
2. Run `git log --oneline -5` — recent commits on the current branch
3. Run `git rev-list --left-right --count origin/main...HEAD 2>/dev/null` to
   show ahead/behind state vs. `origin/main`
4. Run `git fetch --dry-run --prune 2>&1` to detect local branches whose
   remotes have been deleted (stale branches a previous session left behind).
   Don't actually prune — just report.
5. Check open PRs: `gh pr list --state open --limit 10` (if `gh` is available)
6. Show the date and one-line title of the most recent CHANGELOG entry
   (`grep -m1 '^## ' CHANGELOG.md`). This is the playbook's "current state"
   for downstream `/upgrade` consumers.
7. Count pending inbox entries: `grep -c '^### ' inbox.md` (each `### ` heading
   is one un-curated lesson). If > 0, mention that `/curate` is available.

Present as a concise briefing — not a wall of text:

```
## Playbook Session Briefing

**Branch:** <branch> | **vs origin/main:** <N ahead, M behind>
**Latest CHANGELOG entry:** <date> — <title>
**Inbox:** <N pending entries> (run /curate to process)

### Recent commits
<git log --oneline -5 output>

### Open PRs
- #<N> <title> — <branch>

### Flags
- ⚠️ <uncommitted changes, stale local branches, ahead-of-origin without push>
- ✓ Clean — no flags <if nothing to report>
```

After presenting, ask: "What would you like to work on?"

## Things this command intentionally does NOT do

- It does not read `CLAUDE.md` / `WORKLOG.md` / `MANUAL-TASKS.md` / `.playbook-version`.
  Those are downstream-project artifacts; the playbook itself doesn't carry them.
- It does not check Dependabot. The playbook has no app dependencies to update —
  it's a documentation and tooling repo.
- It does not auto-curate the inbox. That's `/curate`'s job, run intentionally.
