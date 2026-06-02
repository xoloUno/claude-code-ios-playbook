---
description: Git branch strategy, commit conventions, and session commit behavior
globs: **/*
---

# Git & Version History

## Branch Strategy

```
main          ← always shippable; protected (never commit directly)
feature/*     ← one branch per feature
fix/*         ← one branch per bug fix
```

Never commit directly to `main`. Land work through a feature or fix branch and a PR.

Some projects also run an integration branch (commonly `dev`) that features merge into
before `main` — that's an *optional* per-project convention, not assumed here. The
`/wrapup` flow routes the branch generically: on the protected default it cuts a branch;
on an existing feature branch it stays put.

**Concurrent Claude Code sessions:** Use **worktrees** (`/worktree`) when running
multiple sessions against the same repo. A branch only isolates commit history —
files on disk are shared. Without worktrees, sessions overwrite each other's work.

## Commit Convention

Format: `type(scope): short description`

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`. Packs may add kind-specific
types (e.g. the iOS pack adds `ui`).

Rules: ≤72 char subject, present tense, no trailing period.

## Claude Code Commit Behavior

At session end (the universal mechanics; the full sequence is driven by `/wrapup`):
1. `git status` — review changes
2. Stage selectively with explicit pathspecs (never `git add .` blindly)
3. Conventional commit + `Co-Authored-By: Claude <noreply@anthropic.com>`
4. Push to a feature/fix branch, not `main`

**Session-end record mutations** — updating a changelog or release notes, a `WORKLOG.md`,
a `CLAUDE.md` "Current State", manual-tasks handoff, `[skip ci]` policy — are **not
universal**. They are driven by `/wrapup` and the project's `command-profile` (each fires
only when that kind/project declares it), so they live there rather than being welded into
this core rule.

## Git Timing Guidance

Commit early and often — don't accumulate a session's worth of changes in one
giant commit. A good rhythm: commit after each logical unit of work (a feature
wired up, a bug fixed, a refactor complete). This makes `git log` useful and
reverts surgical. If a session produces more than ~3 files of changes, it should
probably be multiple commits.

## Tagging Releases

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin --tags
```
