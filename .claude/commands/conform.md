Audit this project against the latest playbook and propose remediation.

Complements `/upgrade`: `/upgrade` is delta-driven (applies CHANGELOG entries since last sync),
`/conform` is state-driven (compares the project's current shape to what the playbook now
expects, regardless of CHANGELOG). Run after long absences or when CHANGELOG entries may have
been missed.

Steps:

1. **Locate the playbook directory** — read `.claude/rules/playbook-inbox.md` and extract the
   path from the `**Inbox location:**` line (strip the trailing `/inbox.md`). If the rule file
   doesn't exist or still contains `PLAYBOOK_PATH`, ask the user for the playbook directory
   absolute path before proceeding.

2. **Audit silently — gather all drift items into memory before presenting anything.** Run the
   six checks below without asking the user yet. Collect a list of `{category, severity, item,
   action}` rows.

   **Check A — Stale playbook-copied rule files (severity: HIGH, auto-fixable)**
   - For each file in `<playbook>/.claude/rules/*.md`:
     - If absent from `.claude/rules/`: drift = MISSING
     - If present: `diff` against playbook source. Account for known substitutions:
       - `playbook-inbox.md`: ignore differences in the `**Inbox location:**` line (always substituted)
       - `build-deploy.md`, `testing.md`: ignore `iPhone 17 Pro` vs `${PRIMARY_SIM}` value differences
     - If non-trivial diff: drift = STALE

   **Check B — Stale playbook-copied slash commands (severity: HIGH, auto-fixable)**
   - For each file in `<playbook>/.claude/commands/*.md` EXCEPT `curate.md`:
     - If absent from `.claude/commands/`: drift = MISSING
     - If present: `diff` against playbook source. If non-trivial diff: drift = STALE

   **Check C — Missing bootstrap-emitted slash commands (severity: MEDIUM, manual)**
   - Read `<playbook>/bootstrap.sh` and extract command names from heredoc patterns
     (`cat > .claude/commands/<name>.md << '<MARKER>'`). Standard set as of writing:
     `feature`, `test`, `review`, `deploy`, `release`, `preflight`.
   - For each, if missing from `.claude/commands/`: drift = MISSING. Note the bootstrap.sh line
     range so the user can copy the heredoc body manually (these can't be auto-applied because
     the heredoc may have substitutions and the bootstrap context isn't reproducible here).

   **Check D — CLAUDE.md template gaps (severity: LOW, advisory only)**
   - Read `<playbook>/CLAUDE-TEMPLATE.md` and extract H2 section titles (`## ...`).
   - Read project's `CLAUDE.md` and extract H2 section titles.
   - For each section in the template that is absent from the project: drift = TEMPLATE_GAP.
   - Do NOT auto-fix these — CLAUDE.md is project-specific and section gaps are usually a
     judgment call. Just surface for review.

   **Check E — Doc bloat (severity: LOW, advisory)**
   - Check for the presence of `MILESTONES.md`, `FEEDBACK.md`, or files matching
     `SESSION-*.md` / `LOG-*.md` at project root (these aren't part of the playbook shape).
   - If found: drift = DOC_BLOAT. Recommendation: see Appendix C of `ios-project-playbook.md`
     for the consolidation walkthrough.

   **Check F — Stranded `.claude/` files (severity: LOW, advisory)**
   - List files in project's `.claude/rules/` and `.claude/commands/`.
   - For each, check if it exists in the playbook source OR matches a bootstrap.sh heredoc
     emission name. If neither: drift = STRANDED. Could be an intentional project-specific
     custom file (keep) or a stale leftover (remove). Don't decide — flag for the user.

3. **Present the consolidated report** as a single markdown table:

   ```
   ## Conformance Audit — <project name> (<branch>)

   | Category | Status | Items |
   |---|---|---|
   | Rule files | ⚠️ N stale, M missing | testing.md (stale), wwdc25-ios26.md (missing), ... |
   | Playbook commands | ⚠️ N stale, M missing | upgrade.md (stale), ... |
   | Bootstrap commands | ❌ N missing | preflight.md (bootstrap.sh:1267-1332) |
   | CLAUDE.md sections | ⚠️ N gaps | "Distribution", ... |
   | Doc bloat | ⚠️ N found | MILESTONES.md (see Appendix C) |
   | Stranded files | ⚠️ N found | .claude/commands/custom.md |

   Overall: N drift items, M auto-fixable, K advisory.
   ```

   If everything is aligned, present a single line: `✓ Project conforms to the playbook — no drift detected.` and stop.

4. **Ask the user how to proceed.** Use `AskUserQuestion` with three options:
   - **Apply all auto-fixable** — apply HIGH-severity items (stale/missing rule files and
     playbook commands) without per-item confirmation. Skip MEDIUM/LOW items.
   - **Walk one by one** — present each drift item individually and let the user
     accept/skip/defer per item.
   - **Just report** — make no changes; the report is the deliverable.

5. **Apply approved fixes:**
   - **Stale or missing playbook rule files (Check A):** copy from `<playbook>/.claude/rules/`
     overwriting the project version. Re-apply known substitutions:
     - `playbook-inbox.md`: substitute `PLAYBOOK_PATH` with the playbook directory
     - `build-deploy.md`, `testing.md`: if `.env.project` exists and defines `PRIMARY_SIM`
       with a value other than `iPhone 17 Pro`, sed-substitute `iPhone 17 Pro` to that value
   - **Stale or missing playbook commands (Check B):** copy from `<playbook>/.claude/commands/`
     overwriting the project version. NEVER copy `curate.md`.
   - **Missing bootstrap commands (Check C):** do not auto-apply. Show the user the
     `bootstrap.sh` line range and instruct them to either re-bootstrap a fresh project to
     copy the file from, or open `bootstrap.sh` and copy the heredoc body manually.
   - **CLAUDE.md template gaps (Check D), doc bloat (Check E), stranded files (Check F):** do
     not auto-apply. Surface again at the end as "manual follow-ups."

6. **Show a final summary:**

   ```
   ## Conformance Pass — Done

   ✅ Applied: N items (list)
   ⏭️  Skipped: N items (list)
   📋 Manual follow-ups: N items (list — bootstrap commands, CLAUDE.md gaps, doc bloat,
       stranded files)
   ```

   If any rule files or commands were updated, suggest the user run `git diff` to review and
   then commit.

Important:
- This is a read-mostly command — only Check A and Check B writes are auto-applied, and only
  with the user's explicit approval in step 4.
- Treat project-specific files (CLAUDE.md, fastlane/metadata, project.yml) as user-owned —
  surface drift but never overwrite.
- If the playbook directory can't be located in step 1, abort with a clear error message
  rather than guessing.
- For diff comparisons in Check A and Check B, use `diff -q` (quiet) to detect any
  difference, then re-diff verbosely only for items the user wants to inspect.
- The project may legitimately have stranded files (custom slash commands, project-specific
  rules). Stranded ≠ wrong. The user decides.
