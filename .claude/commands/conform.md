Audit this project against the latest playbook and propose remediation.

Complements `/upgrade`: `/upgrade` is delta-driven (applies CHANGELOG entries since last sync),
`/conform` is state-driven (compares the project's current shape to what the playbook now
expects, regardless of CHANGELOG). Run after long absences or when CHANGELOG entries may have
been missed.

Steps:

1. **Locate the playbook directory**, using the first option that resolves to an existing
   directory containing `CHANGELOG.md`:
   a. The `$PLAYBOOK_HOME` environment variable, if set.
   b. The `PLAYBOOK_HOME` value in `~/.config/playbook/config` (`source` it, or grep the line).
   c. Legacy fallback — the `**Inbox location:**` line in `.claude/rules/playbook-inbox.md`,
      with the trailing `/inbox.md` stripped. Skip this if the line still holds an unsubstituted
      token (`$PLAYBOOK_HOME` or legacy `PLAYBOOK_PATH`).
   d. If none resolve, ask the user for the playbook directory absolute path before proceeding.

2. **Audit silently — gather all drift items into memory before presenting anything.** Run the
   six checks below without asking the user yet. Collect a list of `{category, severity, item,
   action}` rows.

   **Check A — Stale playbook-copied rule files (severity: HIGH, auto-fixable)**
   - Playbook rules live in `<playbook>/core/rules/*.md` (universal — every project) plus
     `<playbook>/packs/<pack>/rules/*.md` for the project's pack; compose flattens both into the
     project's single `.claude/rules/`. Audit `core/rules/` always (except in opted-in projects;
     see below), and also `packs/ios/rules/`
     when the project is iOS (heuristic: `.claude/rules/build-deploy.md` present). Other packs
     extend this as they gain rules.
   - For each source rule, compared against the project's `.claude/rules/<name>.md`:
     - If absent from `.claude/rules/`: drift = MISSING
     - If present: `diff` against the playbook source. Account for known substitutions:
       - `playbook-inbox.md`: ignore differences in the `**Inbox location:**` line (always substituted)
       - `build-deploy.md`, `testing.md`: ignore `iPhone 17 Pro` vs `${PRIMARY_SIM}` value differences
       - `build-deploy.md`, `testing.md`: ignore `[APP_NAME]` vs the resolved scheme
         argument. Get it the way compose does: load `.env.project` into the environment
         (`set -a; . ./.env.project; set +a`, if the file exists), then run
         `bash <playbook>/resolve-xcode-scheme.sh <project>`. Empty output means unresolved,
         and the placeholder is expected to remain.
     - If non-trivial diff: drift = STALE
   - **Opted-in projects.** If the project's `AGENTS.md` carries the playbook core markers
     (`<!-- playbook:core:begin -->` / `<!-- playbook:core:end -->`), the core rules are the
     generated block. Don't audit `core/rules/`, and never report its files as MISSING.
     Instead:
     - Compare the text between the markers with `<playbook>/core/agents-core.md`, ignoring
       line endings. If it differs: drift = STALE_CORE_BLOCK.
     - If any `core/rules/` filename is present in `.claude/rules/`: drift = DUPLICATE_CORE
       (manual). It loads alongside the block. Remove it only after confirming it's an
       unmodified playbook copy.
     - Audit the pack rules as usual.

   **Check B — Stale/missing playbook-copied slash commands (severity: HIGH, auto-fixable)**
   - **The expected shared-command set depends on the bridge type** — same iOS heuristic as
     Checks A and C (`.claude/rules/build-deploy.md` present ⇒ iOS):
     - **iOS (composed copies via `compose-claude.sh`):** every shared command it emits — all of
       `<playbook>/.claude/commands/*.md` EXCEPT `curate.md` (`status`, `wrapup`, `conform`,
       `context-health`, `inbox`, `test`, `upgrade`, `capture-manual-surfaces`).
     - **non-iOS (live symlinks via `bridge-symlink.sh`):** exactly `status`, `wrapup`, `conform`,
       `context-health`, `inbox`, `test` — the same set as `bridge-symlink.sh` `COMMANDS`. `upgrade`
       (moot when the symlinked source is always current) and `capture-manual-surfaces` (iOS-only)
       are **intentional exclusions, not drift** — never report them MISSING here.
   - For each command in the project's expected set:
     - If absent from `.claude/commands/`: drift = MISSING
     - If present: `diff` against `<playbook>/.claude/commands/<name>.md`. If non-trivial diff:
       drift = STALE. (A symlinked command *is* the source, so a bridged repo never shows STALE.)

   **Check C — Missing iOS-pack slash commands (severity: MEDIUM, manual)**
   - **Pack-gated:** only run this check for iOS projects — heuristic: `.claude/rules/build-deploy.md`
     is present. For non-iOS projects, skip Check C entirely; they carry no iOS-pack commands and
     a "missing" report would be a false positive.
   - The iOS pack ships six commands in `<playbook>/packs/ios/commands/`: `feature`, `gen-tests`,
     `review`, `deploy`, `release`, `preflight`. For each, if missing from `.claude/commands/`:
     drift = MISSING. These are normally emitted by `compose-claude.sh`; recomposing (or copying
     `<playbook>/packs/ios/commands/<name>.md` and re-applying the `${PRIMARY_SIM}`/profile/locale
     markers from `.env.project`) restores them.

   **Check D — Instructions-file template gaps (severity: LOW, advisory only)**
   - Read `<playbook>/CLAUDE-TEMPLATE.md` and extract H2 section titles (`## ...`).
   - Read the project's instructions file and extract H2 section titles. The instructions
     file is `AGENTS.md` when it carries the playbook core markers; otherwise it's
     `CLAUDE.md`. In an opted-in project, `CLAUDE.md` is a symlink to `AGENTS.md`; read
     `AGENTS.md`, and don't report the symlink as a gap.
   - For each section in the template that is absent from the project: drift = TEMPLATE_GAP.
   - Do NOT auto-fix these — the instructions file is project-specific and section gaps are
     usually a judgment call. Just surface for review.

   **Check E — Doc bloat (severity: LOW, advisory)**
   - Check for `MILESTONES.md`, `FEEDBACK.md`, or files matching
     `SESSION-*.md` / `LOG-*.md` at project root (these aren't part of the playbook shape).
   - If found: drift = DOC_BLOAT. Recommendation: see Appendix C of `ios-project-playbook.md`
     for the consolidation walkthrough.

   **Check F — Stranded `.claude/` files (severity: LOW, advisory)**
   - List files in project's `.claude/rules/` and `.claude/commands/`.
   - For each, check whether it exists in the playbook source — a rule under `core/rules/` or
     `packs/<pack>/rules/`, or a command under `.claude/commands/` (except `curate.md`) or
     `packs/<pack>/commands/`. If it matches none: drift = STRANDED. Could be an intentional
     project-specific custom file (keep) or a stale leftover (remove). Don't decide — flag for
     the user.

   **Check G — Untracked playbook rule files (gitignore silent-untrack) (severity: HIGH, advisory)**
   - Catches a failure Check A is blind to: a buggy project `.gitignore` (an inline-comment
     no-op like `*.log # logs`, or an unanchored pattern such as `scratch` or `*.md`) silently
     keeps a `.claude/rules/<name>.md` file from being tracked. Check A still reports the file
     OK (its on-disk content matches the playbook) and `git status` stays clean (git ignores
     it), so the rule is present in *this* checkout but absent from version control — it
     vanishes on a fresh clone. `bootstrap.sh`'s anchor fix only protects newly bootstrapped
     projects; existing repos carry the bug invisibly.
   - For each `.claude/rules/*.md` present on disk, test tracking with
     `git ls-files --error-unmatch <file>` (run from the project root). Non-zero exit ⇒ the
     file is not tracked → drift = UNTRACKED.
   - For each UNTRACKED file, run `git check-ignore -v <file>`:
     - **matches** ⇒ the file is gitignored — the dangerous silent case. Capture the offending
       `<gitignore-path>:<line>:<pattern>` so the user can repair the exact rule.
     - **no match** ⇒ merely untracked-new (it already shows in `git status`; lower urgency —
       usually just needs `git add`). Note which case each item is.
   - Applies uniformly to symlink-bridged repos: their `.claude/rules/*.md` are tracked
     mode-120000 symlinks, so a symlink swallowed by a bad ignore pattern is just as silently
     absent.
   - **Advisory — never auto-fix.** The remediation edits the project-owned `.gitignore`
     (anchor or repair the offending pattern), then `git add`s the rule file; surface the
     offending pattern and leave both edits to the user.

3. **Present the consolidated report** as a single markdown table:

   ```
   ## Conformance Audit — <project name> (<branch>)

   | Category | Status | Items |
   |---|---|---|
   | Rule files | ⚠️ N stale, M missing | testing.md (stale), wwdc25-ios26.md (missing), ... |
   | Untracked rules | ❌ N untracked | playbook-inbox.md (gitignored by .gitignore:12 `*.md`), ... |
   | Playbook commands | ⚠️ N stale, M missing | upgrade.md (stale), ... |
   | iOS-pack commands | ❌ N missing | preflight.md (packs/ios/commands/) |
   | Core block (opted-in) | ⚠️ stale / N duplicate core rules | git-workflow.md (duplicate), ... |
   | Instructions-file sections | ⚠️ N gaps | "Distribution", ... |
   | Doc bloat | ⚠️ N found | MILESTONES.md (see Appendix C) |
   | Stranded files | ⚠️ N found | .claude/commands/custom.md |

   Overall: N drift items, M auto-fixable, K advisory.
   ```

   If everything is aligned, present a single line: `✓ Project conforms to the playbook — no drift detected.` and stop.

4. **Ask the user how to proceed.** Use `AskUserQuestion` with three options:
   - **Apply all auto-fixable** — apply the HIGH-severity *auto-fixable* items (stale/missing
     rule files and playbook commands — Checks A and B) without per-item confirmation. Skip
     MEDIUM/LOW items, and skip Check G (HIGH but advisory — its fix touches the project-owned
     `.gitignore`, which `/conform` never rewrites).
   - **Walk one by one** — present each drift item individually and let the user
     accept/skip/defer per item.
   - **Just report** — make no changes; the report is the deliverable.

5. **Apply approved fixes:**
   - **Stale or missing playbook rule files (Check A):** copy from the file's playbook home —
     `<playbook>/core/rules/<name>.md` or `<playbook>/packs/<pack>/rules/<name>.md` — overwriting
     the project version. Re-apply known substitutions:
     - `playbook-inbox.md`: substitute the `$PLAYBOOK_HOME` token with the playbook directory
     - `build-deploy.md`, `testing.md`: if `.env.project` exists and defines `PRIMARY_SIM`
       with a value other than `iPhone 17 Pro`, sed-substitute `iPhone 17 Pro` to that value
     - `build-deploy.md`, `testing.md`: substitute `[APP_NAME]` with the output of
       `bash <playbook>/resolve-xcode-scheme.sh <project>`, run after loading `.env.project` as
       above. The output is already shell-quoted; use it verbatim. If it's empty, leave the
       placeholder and report it
     - **Opted-in projects:** fix STALE_CORE_BLOCK with
       `python3 <playbook>/compose-agents-md.py write <project> <playbook>`. This updates only
       the marked block. Never copy `core/rules/` files in, and never auto-remove a
       DUPLICATE_CORE file.
   - **Stale or missing playbook commands (Check B):** for a **composed (iOS)** project, copy from
     `<playbook>/.claude/commands/` overwriting the project version (NEVER copy `curate.md`). For a
     **symlink-bridged (non-iOS)** project a STALE result can't occur (the command *is* the
     source); if one is genuinely MISSING, re-link with `<playbook>/bridge-symlink.sh <project>`
     rather than copying a file in.
   - **Missing iOS-pack commands (Check C):** skipped entirely for non-iOS projects. For iOS
     projects, do not auto-apply; point the user at `<playbook>/packs/ios/commands/<name>.md` to
     copy (re-applying the `.env.project` markers), or have them re-run
     `compose-claude.sh <project> ios`.
   - **Duplicate core rules (Check A, opted-in), instructions-file template gaps (Check D),
     doc bloat (Check E), stranded files (Check F),
     untracked rule files (Check G):** do not auto-apply. Surface again at the end as "manual
     follow-ups." Check G is HIGH-severity but still manual — its fix repairs the project-owned
     `.gitignore` and then `git add`s the rule file; report the offending pattern and the
     `git add` needed, and let the user make both edits.

6. **Show a final summary:**

   ```
   ## Conformance Pass — Done

   ✅ Applied: N items (list)
   ⏭️  Skipped: N items (list)
   📋 Manual follow-ups: N items (list — bootstrap commands, instructions-file gaps, doc bloat,
       stranded files)
   ```

   If any rule files or commands were updated, suggest the user run `git diff` to review and
   then commit.

Important:
- This is a read-mostly command — only Check A and Check B writes are auto-applied, and only
  with the user's explicit approval in step 4.
- Treat project-specific files (`AGENTS.md` outside the playbook core markers, `CLAUDE.md`,
  fastlane/metadata, project.yml) as user-owned —
  surface drift but never overwrite.
- If the playbook directory can't be located in step 1, abort with a clear error message
  rather than guessing.
- For diff comparisons in Check A and Check B, use `diff -q` (quiet) to detect any
  difference, then re-diff verbosely only for items the user wants to inspect.
- Check G is detection-only (`git ls-files` / `git check-ignore`); it never edits `.gitignore`
  or stages files. It complements Check A: A compares rule *content*, G confirms the rule is
  actually under version control.
- The project may legitimately have stranded files (custom slash commands, project-specific
  rules). Stranded ≠ wrong. The user decides.
