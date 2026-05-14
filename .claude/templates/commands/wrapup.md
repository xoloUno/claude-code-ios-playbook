End-of-session wrap-up — commit and update docs.

Steps:
1. Run `git status` — review all changes (staged, unstaged, untracked)
2. Show the user a summary of what changed this session
3. **Stage selectively** — never `git add .` blindly. Group related changes into
   logical commits if multiple features/fixes were worked on.
4. **Write conventional commit message(s):**
   - Format: `type(scope): short description`
   - Include `Co-Authored-By: Claude <noreply@anthropic.com>`
   - **Local sessions:** include `[skip ci]` unless the user says otherwise
   - **Cloud sessions:** do NOT include `[skip ci]`
5. **Update "Current State"** in CLAUDE.md:
   - Set "Last updated" to today's date
   - Update "Build status"
   - Update "Last completed work" with what this session did
   - Update "Next up" with what the next session should focus on
6. **Update WORKLOG.md** — append a new entry at the top (below the header):
   ```markdown
   ## [DATE] — [Brief description of session focus]

   **What changed:**
   - [Bullet points of changes — files, features, fixes]

   **Decisions:**
   - [Key decisions and rationale]

   **Blockers:**
   - [Open issues or next-session priorities]
   - None. [if nothing is blocked]
   ```
7. **Update `release-notes-draft.md`** if any user-facing changes were made
8. **Check scope items** in CLAUDE.md — check off any completed items
9. **Create/update `MANUAL-TASKS.md`** if the session produced human-only tasks
10. Push to `dev` or feature branch (not `main` unless the user explicitly asks)
11. Confirm to the user: what was committed, what branch, what's next

If there are no changes to commit, say so and skip to step 11.
