End-of-session wrap-up — commit cleanly, push, leave the repo in good shape.

This is the **universal** `/wrapup`. The order below is load-bearing, not stylistic:
a record mutation appended *after* the commit lands uncommitted; a validation gate
appended after the commit can't block it; a branch decision appended after the commit
has already hit `main`. Kind- and project-specific steps come from the profile, but
each one must slot into its correct stage here — the hook says where.

## Load first — bind the project profile, then order its steps

Before doing anything that mutates, read these **if present** and merge the steps under
their `## /wrapup` heading into the flow:

- `.claude/command-profile.md` — the kind layer (iOS, Python, …).
- `.claude/command-profile.local.md` — this project's own escape hatch.
- `.claude/project.yml` — declarative facts the steps reference.

Place each profile step at its correct stage below. **Invariant:** record mutations
whose output should be committed run *before* staging; validation gates run *after* all
intended mutations and *before* the commit; the branch decision precedes the commit so
work never lands on the protected default.

## Flow (in order)

1. **Orient.** `git status` — review staged, unstaged, untracked. Show the user a
   concise summary of what changed this session.

2. **Decide the branch route — before any commit.** If on `main` (or the repo's
   protected default), do **NOT** commit there: create a feature branch
   (`feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`) from HEAD so the commit
   lands on the branch. If already on a feature branch, stay on it. Direct commit/push
   to the default is only ever on explicit per-session authorization — "wrap up" alone
   in chat is **not** authorization.

3. **Apply record mutations** — profile-driven; each fires only when relevant. These
   produce content that must be committed, so they run **before staging**. Common kinds:
   - changelog / release-notes entry;
   - version-file sync (keep declared `version_files` in lockstep on a bump);
   - session-state / worklog update — e.g. `CLAUDE.md` "Current State", `WORKLOG.md`
     (only if present);
   - manual-tasks handoff — if the session produced human-only tasks, append them to
     `MANUAL-TASKS.md` (the profile may specify the format);
   - prose-humanizer on touched user-facing prose (this is a *mutation*, not a gate).

4. **Run validation gates** — profile-driven; each fires only when declared (tests,
   preflight, lint). A failing gate blocks the commit: fix it or get explicit
   acknowledgement first. Gates run *after* the mutations (so they check the final tree)
   and *before* the commit (so they can still block it).

5. **Stage selectively** — never `git add .` blindly, and always with explicit
   pathspecs. Group related changes into logical commits when several concerns were
   touched.

6. **Commit.** Conventional message: `type(scope): short description`
   (`feat` / `fix` / `docs` / `refactor` / `chore` / `test` …), then
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Anything about `[skip ci]` is
   kind-specific — it comes from the profile, not from here.

7. **Push / PR.**
   - On a branch created in step 2 off the default: `git push -u origin <branch>` and
     open a PR with `gh pr create`. Report the URL.
   - On a pre-existing feature branch: push; if no PR exists, offer to create one.
   - Never `git push --force` without an explicit request.

8. **Confirm** to the user: what was committed, which branch, the PR URL (if any), and
   what the next session should pick up.

If there is nothing to commit, say so and skip to step 8.
