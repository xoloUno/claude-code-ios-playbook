End-of-session wrap-up for the playbook — commit cleanly, push, leave the repo in good shape.

This is the playbook repo itself. Wrap-up looks different from a downstream iOS
project: there's no `CLAUDE.md` Current State to update, no `WORKLOG.md` diary,
no `release-notes-draft.md`. The session record is `CHANGELOG.md` (for
downstream consumers) and the commit history.

Steps:

1. Run `git status` — review staged, unstaged, untracked files.
2. Show the user a concise summary of what changed this session.
3. **Decide whether the change is downstream-visible.** A change is downstream-visible
   if a project that bootstrapped from this playbook should care:
   - `bootstrap.sh` changes
   - Any file under `.claude/rules/` (these get copied into every bootstrapped project)
   - Any file under `.claude/templates/` (these get copied into bootstrapped projects)
   - Any file under `.claude/commands/` **other than** `curate.md` (the rest get copied)
   - `ios-project-playbook.md` content changes
   - `CLAUDE-TEMPLATE.md` changes
   - New tools or skills the playbook ships
   - `getting-started.md` workflow changes
   Internal-only changes that need NO CHANGELOG entry: typo fixes in the playbook's
   own `.claude/commands/curate.md` / `status.md` / `wrapup.md`, edits to `inbox.md`,
   `README.md` polish, repo-level metadata.
4. **If the change is downstream-visible, add a `CHANGELOG.md` entry.** New entries go
   immediately under the `---` separator near the top, before any prior dated entries.
   Follow the existing format strictly:
   ```markdown
   ## YYYY-MM-DD — <one-line title>

   <2-4 sentence summary of what changed and why it matters to downstream projects.>

   **Files affected:**
   - `path/to/file.md` — <what changed>

   **What to do in your project:**
   - <concrete steps the downstream session should take to adopt, or "nothing — this
     only affects newly-bootstrapped projects">
   ```
   If the change retracts or replaces earlier guidance, add the `Superseded by:` /
   `Partially superseded by:` banner under the older entry's `##` heading per the
   convention documented at the top of `CHANGELOG.md`.
5. **Stage selectively** — never `git add .` blindly. Group related changes into
   logical commits when multiple concerns were touched.
6. **Write conventional commit message(s):**
   - Format: `type(scope): short description`
   - Types: `feat`, `fix`, `docs`, `refactor`, `chore` (use `chore` for inbox curation
     and other meta work that has no downstream effect)
   - Scopes commonly used in this repo: `playbook`, `bootstrap`, `rules`, `commands`,
     `inbox`, `changelog`
   - Append `Co-Authored-By: Claude <noreply@anthropic.com>`
   - Do NOT add `[skip ci]` — the playbook has no CI lanes that need skipping
7. **Branch routing:**
   - On `main`: do **NOT** push directly. Create a feature branch
     (`feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`) from HEAD, push it,
     and open a PR with `gh pr create`. Report the PR URL.
   - On a feature branch: push with `git push -u origin <branch>`. If no PR exists,
     offer to create one.
   - Exception: routine inbox curation when the user has explicitly approved direct
     pushing for that session. Wait for explicit authorization — "wrap up" alone in
     chat is not authorization to push to `main`.
8. **Inbox housekeeping (only if relevant):** if this session adopted entries from
   `inbox.md` into the playbook, the curate workflow already handled deletions —
   but check that `inbox.md` no longer references work that's now landed.
9. Confirm to the user: what was committed, what branch, PR URL (if applicable),
   what's next.

If there are no changes to commit, say so and skip to step 9.

## Notes

- Don't `git push --force` without explicit user request.
- For multi-file changes, prefer one commit per logical unit. Don't bundle a
  CHANGELOG entry with an unrelated bug fix.
- This file (`/wrapup` for the playbook) is intentionally separate from the iOS
  project `/wrapup` template that lives at `.claude/templates/commands/wrapup.md`
  and ships to bootstrapped projects via `bootstrap.sh`.
