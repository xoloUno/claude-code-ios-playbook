---
description: Git branch strategy, commit conventions, and session commit behavior
globs: **/*.swift, **/*.yml, **/project.yml
---

# Git & Version History

**Remote:** GitHub — `https://github.com/YourOrg/[REPO_NAME]`

## Branch Strategy

```
main          ← always shippable; tagged on every submission
dev           ← active development
feature/*     ← one branch per feature
fix/*         ← one branch per bug fix
```

Never commit directly to `main`. Merge from `dev` or feature branches only.

**Concurrent Claude Code sessions:** Use **worktrees** (`/worktree`) when running
multiple sessions against the same repo. A branch only isolates commit history —
files on disk are shared. Without worktrees, sessions overwrite each other's
uncommitted work.

## Commit Convention

Format: `type(scope): short description`

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `ui`

Rules: ≤72 char subject, present tense, no trailing period.

## Claude Code Commit Behavior

At session end:
1. `git status` — review changes
2. Stage selectively (never `git add .` blindly)
3. Conventional commit + `Co-Authored-By: Claude <noreply@anthropic.com>`
4. **Local sessions:** Include `[skip ci]` in message — local sessions handle build + deploy
   **Cloud sessions:** Do NOT include `[skip ci]` — CI must verify the build
5. Push to `dev` or feature branch (not `main`)
6. **Update "Current State" section** in CLAUDE.md (mandatory)
7. **Update `WORKLOG.md`** with detailed session diary entry (see work-log rule)
8. **Update `release-notes-draft.md`** with user-facing changes

## Git Timing Guidance

Commit early and often — don't accumulate a session's worth of changes in one
giant commit. A good rhythm: commit after each logical unit of work (a feature
wired up, a bug fixed, a refactor complete). This makes `git log` useful and
reverts surgical. If a session produces more than ~3 files of changes, consider
whether it should be multiple commits.

## Tagging Releases

```bash
git tag -a v1.0.0 -m "App Store v1 submission"
git push origin --tags
```
