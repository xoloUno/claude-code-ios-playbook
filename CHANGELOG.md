# Playbook Changelog

Recent changes to the iOS project playbook. When starting a Claude Code session in a
project that uses this playbook, read this file to check if the project needs updating.

Each entry describes what changed, which playbook files were affected, and what to do
in your project to adopt the change.

---

## 2026-04-21 — CloudKit sync patterns added to §4.4

**What changed:** Three lessons from the Flara project added to §4.4 CloudKit & Push
Notifications in `ios-project-playbook.md`:

- **CKQuery + encrypted fields pitfall** — new row in Common CloudKit Pitfalls table:
  never use `CKQuery` on encrypted-only record types in Production; use
  `recordZoneChanges(since: nil)` instead.
- **Debounce push pattern** — cancel-and-debounce concurrent `save()` calls to prevent
  last-writer-wins race conditions under `savePolicy: .changedKeys`.
- **Three sync triggers** — always implement silent push + 15s polling + pull-to-refresh;
  `CKDatabaseSubscription` alone is unreliable on TestFlight/low battery.

**Affected files:** `ios-project-playbook.md`
**Action needed in your project:** Review your CloudKit sync layer against these patterns.

---

## 2026-04-10 — Externalize config to env files, fix bootstrap path resolution

**What changed:** `bootstrap.sh` no longer requires manual editing. All configuration is
loaded from two gitignored env files:

- **`.env.playbook`** — identity and credentials (Team ID, GitHub org, ASC keys). Set once.
- **`.env.project`** — app-specific vars (APP_NAME, BUNDLE_ID, REPO_NAME, MINIMUM_IOS).
  Edit before each bootstrap run.

**Bug fixes:**
- Fixed two `BASH_SOURCE[0]` relative path resolution bugs that caused bootstrap to fail
  after `cd`-ing into the new project directory (lines 905 and 943). Both now use
  `SCRIPT_DIR` resolved once at script start.

**New files:**
- **`.env.project.example`** — template for per-project config

**Updated files:**
- **`bootstrap.sh`** — sources env files, validates required vars, removed hardcoded placeholders
- **`.gitignore`** — added `.env.project`
- **`getting-started.md`** — updated one-time setup (add `.env.playbook` step) and
  per-project workflow (use `.env.project` instead of editing script). Steps renumbered
  from 5 to 4.

**How to upgrade your project:** No project-side changes needed — this only affects the
playbook's bootstrap workflow. Existing projects are unaffected.

---

## 2026-04-09 — Session lifecycle commands, /upgrade, testing + privacy rules

**What changed:** Major expansion of slash commands and rules:

**New slash commands:**
- **`/status`** — automated session startup briefing (replaces the startup checklist rule).
  Shows project state, branch, last session summary, flags for uncommitted changes,
  pending manual tasks, stale rules, and open Dependabot PRs.
- **`/wrapup`** — automated session end (replaces the end checklist rule). Commits,
  updates CLAUDE.md Current State, writes WORKLOG entry, updates release notes, pushes.
- **`/upgrade`** — syncs a project with playbook changes. Reads CHANGELOG.md, identifies
  entries newer than the project's `.playbook-version` marker, walks through each change
  with apply/skip/manual recommendations.
- **`/context-health`** — session hygiene gauge. Reports uncommitted files/lines, push
  status, WORKLOG freshness. Recommends checkpoint when indicators are high.

**New rules:**
- **`testing.md`** — testing strategy for solo indie v1 (what to test, what to skip,
  Swift Testing conventions, no-mock persistence philosophy)
- **`privacy-manifest.md`** — when and how to update PrivacyInfo.xcprivacy, required
  reason API categories, third-party SDK guidance

**Removed:**
- **`session-checklists.md`** — replaced by `/status` and `/wrapup` commands

**Other changes:**
- `bootstrap.sh` now copies all playbook slash commands (except `/curate`) into projects
- `bootstrap.sh` creates `.playbook-version` file for `/upgrade` tracking
- Slash commands table in `code-style.md` updated with all 10 commands

**Playbook files affected:** `.claude/commands/` (4 new), `.claude/rules/` (2 new, 1 removed),
`bootstrap.sh`, `.claude/rules/code-style.md`

**How to upgrade your project:**

1. Delete `.claude/rules/session-checklists.md` (replaced by commands)
2. Copy new rules from playbook `.claude/rules/`: `testing.md`, `privacy-manifest.md`
3. Copy new commands from playbook `.claude/commands/`: `status.md`, `wrapup.md`,
   `upgrade.md`, `context-health.md`
4. Create `.playbook-version` in project root with today's date:
   ```
   # Last synced with playbook CHANGELOG
   2026-04-09
   ```
5. Update the slash commands table in `.claude/rules/code-style.md` (add `/status`,
   `/wrapup`, `/upgrade`, `/context-health`)

---

## 2026-04-09 — Add cross-project playbook inbox with slash commands

**What changed:** New `inbox.md` file in the playbook root serves as a shared inbox where
Claude Code sessions in any bootstrapped project can log lessons learned, gotchas,
suggestions, and patterns. Two slash commands drive the workflow:

- **`/inbox {lesson}`** — available in every bootstrapped project. Logs a structured
  entry (date, project, category, context, lesson, suggested action) to the playbook's
  `inbox.md`. Can be run with an argument or interactively.
- **`/curate`** — available in the `_playbook/` directory. Walks through inbox entries
  one by one, recommends adopt/defer/discard, makes adopted changes to playbook files,
  and cleans up processed entries.

A `.claude/rules/playbook-inbox.md` rule provides guidance on what qualifies as inbox-worthy.
`bootstrap.sh` substitutes the absolute playbook path into the rule and copies the `/inbox`
command at project creation time.

**Playbook files affected:** `inbox.md` (new), `.claude/rules/playbook-inbox.md` (new),
`.claude/commands/inbox.md` (new), `.claude/commands/curate.md` (new), `bootstrap.sh`,
`.claude/rules/code-style.md` (slash commands table)

**How to upgrade your project:**

1. Copy `.claude/rules/playbook-inbox.md` from the playbook into your project's
   `.claude/rules/`
2. Replace `PLAYBOOK_PATH` in the copied file with the absolute path to your
   `_playbook/` directory (e.g. `~/Code/_playbook`)
3. Copy `.claude/commands/inbox.md` from the playbook into your project's
   `.claude/commands/`

---

## 2026-04-09 — Restructure CLAUDE-TEMPLATE.md: extract rules to .claude/rules/

**What changed:** CLAUDE-TEMPLATE.md reduced from 542 lines to ~190 lines. All operational
rules (git workflow, build/deploy, code style, WWDC25, session checklists, manual tasks,
work log) extracted into path-scoped `.claude/rules/` files that Claude Code loads
automatically by glob match. Two new rules added:

- **session-health.md** — context window awareness, proactive checkpointing, crash recovery
- **git-workflow.md** — now includes git timing guidance (commit early and often)

The core CLAUDE-TEMPLATE.md retains only project identity: overview, tech stack, UI
direction, data models, monetization, scope rules, key decisions, and App Store metadata.

`bootstrap.sh` updated to copy `.claude/rules/` files into bootstrapped projects.

**Playbook files affected:** `CLAUDE-TEMPLATE.md`, `bootstrap.sh`, `.claude/rules/` (new)

**How to upgrade your project:**

1. Create `.claude/rules/` directory in your project root
2. Copy all `.md` files from the playbook's `.claude/rules/` into your project's
   `.claude/rules/`
3. Remove the following sections from your project's `CLAUDE.md` (they now live in rules):
   - Code Style & Conventions
   - Automated Quality Tools
   - WWDC25 & iOS 26 Awareness
   - Git & Version History
   - Build & Deploy
   - Session Startup Checklist / Session End Checklist
   - Manual Tasks Handoff Rule
   - Work Log Rule
4. Add a note near the top of your `CLAUDE.md` pointing to `.claude/rules/`:
   > Operational rules (git workflow, build/deploy, code style, WWDC25, session checklists,
   > manual tasks, work log, session health) live in `.claude/rules/` and are loaded
   > automatically by path glob. Do not duplicate them here.

---

## 2026-04-09 — Public release: PII scrub + .env.playbook pattern

**What changed:** Scrubbed all personal identifiers, Apple Developer credentials,
and hardcoded org/domain references to prepare the playbook for public GitHub release.

- All Team IDs, ASC Key IDs, Issuer IDs, email, name, and domain replaced with
  generic placeholders (`YOUR_TEAM_ID`, `com.example.*`, etc.)
- Added `.env.playbook.example` — users copy to `.env.playbook` and fill in their
  own values. `.env.playbook` is gitignored.
- `bootstrap.sh` config section now has a comment pointing to `.env.playbook`
- File paths using absolute `/Users/...` replaced with `~` shorthand
- Example project names generalized to `MyApp`

**Playbook files affected:** All files.

**How to upgrade your project:**

1. Copy `.env.playbook.example` to `.env.playbook` and fill in your Apple Developer
   credentials (Team ID, ASC Key ID, Issuer ID, org, email, domain)
2. Add `.env.playbook` to your global gitignore if not already covered

---

## 2026-04-08 — CloudKit & Push Notifications gotchas + async init pattern

**What changed:** Added §4.4 covering CloudKit + Push Notifications integration
gotchas learned across multiple projects. Also added async init and
debugging tips to §3.3 Code Style.

New coverage:
- **CloudKit pitfalls table** — "Invalid bundle ID" fix, Simulator flakiness,
  Production schema immutability, CKError.unknownItem on empty containers
- **aps-environment rule** — use `development` in source; Xcode handles production
- **Self-healing async init pattern** — mutation paths re-verify preconditions,
  with Swift code example for CloudKit push
- **print() debugging tip** — when Logger categories don't surface in Xcode console

**Playbook files affected:** `ios-project-playbook.md`

**How to upgrade your project:**

These are reference sections — no project file changes needed. If your project
uses CloudKit, review §4.4 for gotchas. The async init pattern (§4.4) and
debugging tip (§3.3) apply to any project.

---

## 2026-04-02 — Automated release lane with metadata and screenshots

**What changed:** The release pipeline is now fully automated. Previously the `release`
lane skipped both metadata and screenshots (`skip_metadata: true`). Now it syncs metadata
from `fastlane/metadata/en-US/` to App Store Connect on every release.

New additions:
- **Pre-populated metadata files** — `name.txt`, `description.txt`, `release_notes.txt`,
  URLs auto-filled with GitHub Pages links; new `promotional_text.txt` and `marketing_url.txt`
- **Deliverfile** — configures `deliver` with safe defaults (`force: true`, no auto-submit)
- **Snapfile** — configured for required ASC device sizes (6.5" iPhone, iPad 13")
- **ScreenshotTests.swift** — UI test template for automated screenshot capture
- **Commented-out UI test target** in `project.yml` (uncomment after `fastlane snapshot init`)
- **3 new Fastlane lanes:** `screenshots`, `upload_metadata`, `upload_screenshots`
- **release.yml** — GitHub Actions workflow for App Store release (manual dispatch)
- **`/release` slash command** — validates metadata, syncs, builds, uploads, tags

**Playbook files affected:** `bootstrap.sh`, `CLAUDE-TEMPLATE.md`

**How to upgrade your project:**

1. Create `fastlane/Deliverfile`:
   ```ruby
   app_identifier CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier)
   force true
   submit_for_review false
   automatic_release false
   precheck_include_in_app_purchases false
   ```

2. Create `fastlane/Snapfile` (update scheme and devices for your app):
   ```ruby
   # Devices matching ASC required screenshot sizes
   devices([
     "iPhone 14 Plus",             # 6.5" — REQUIRED for submission (1284x2778)
     "iPad Pro 13-inch (M5)"      # 13"  — REQUIRED for submission (2064x2752)
   ])
   languages(["en-US"])
   scheme("YourAppUITests")
   output_directory("./fastlane/screenshots")
   clear_previous_screenshots(true)
   override_status_bar(true)
   ```
   **Important:** ASC requires iPhone 6.5" screenshots (1284x2778). iPhone 17 Pro
   outputs 6.3" resolution — it does NOT satisfy this requirement. Use iPhone 13 Pro Max
   or iPhone 14 Plus for the mandatory 6.5" size.

3. Populate `fastlane/metadata/en-US/` files with real content (name, description,
   keywords, release notes, URLs). Add `promotional_text.txt` and `marketing_url.txt`.

4. Add 3 new lanes to your `Fastfile` (`screenshots`, `upload_metadata`,
   `upload_screenshots`) — see `bootstrap.sh` for the full lane definitions.

5. Update the `release` lane: change `skip_metadata: false`, add `force: true`.

6. Copy `.github/workflows/release.yml` from `bootstrap.sh` (mirrors `testflight.yml`
   but runs `fastlane release`).

7. Copy `.claude/commands/release.md` from `bootstrap.sh`.

8. Add `/release` row to your `CLAUDE.md` slash commands table.

9. Create `fastlane/screenshots/en-US/` directory and `fastlane/screenshots/.gitkeep`.

10. (Optional) Create `YourAppUITests/ScreenshotTests.swift` and uncomment the UI test
    target in `project.yml` after running `bundle exec fastlane snapshot init`.

---

## 2026-04-02 — Harden /deploy command (profile check, PATH fix, cleanup)

**What changed:** The `/deploy` slash command now checks that provisioning profiles are
installed locally *before* running fastlane. Previously, fastlane would modify
`project.pbxproj` with signing settings, then fail when profiles were missing — leaving
dirty project files that had to be manually restored.

Also fixed: SwiftLint now uses full Homebrew path (`/opt/homebrew/bin/swiftlint`), the
fastlane invocation includes PATH and locale exports in both template versions, and the
fallback section now includes `git checkout -- *.xcodeproj` to restore project files.

**Playbook files affected:** `bootstrap.sh`, `ios-project-playbook.md` (deploy command)

**How to upgrade your project:**

Replace `.claude/commands/deploy.md` with the updated version. Key changes:
1. New step 1 checks `~/Library/MobileDevice/Provisioning Profiles/` for required
   profiles before running fastlane — stops early if missing
2. SwiftLint uses full path: `/opt/homebrew/bin/swiftlint lint --strict --quiet`
3. Fastlane invocation includes PATH + locale exports:
   `export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && set -a && source .env.fastlane && set +a && bundle exec fastlane beta`
4. Fallback now restores project files: `git checkout -- *.xcodeproj`

See `bootstrap.sh` or `ios-project-playbook.md` for the full updated command.

---

## 2026-04-02 — Fix lefthook pre-commit hooks (PATH + glob)

**What changed:** Two fixes to `lefthook.yml`:

1. **PATH fix:** Claude Code sessions don't always inherit the full shell PATH, so
   Homebrew-installed binaries (`gitleaks`, `swiftlint`) fail with `command not found`.
   Fixed by using full paths (`/opt/homebrew/bin/...`).

2. **Glob fix:** Lefthook's default glob matcher (`gobwas`) treats `**` as matching 1+
   directories, not 0+. So `*.{swift}` only matched root-level files and missed
   subdirectories. Fixed by adding `glob_matcher: doublestar` (standard behavior where
   `**` matches 0+ directories) and using `**/*.{swift}` as the glob pattern.

**Playbook files affected:** `bootstrap.sh`, `ios-project-playbook.md` (lefthook template
+ troubleshooting table)

**How to upgrade your project:**

Replace your `lefthook.yml` with:

```yaml
glob_matcher: doublestar

pre-commit:
  parallel: true
  commands:
    swiftlint:
      glob: "**/*.{swift}"
      run: /opt/homebrew/bin/swiftlint lint --strict --quiet {staged_files}
    gitleaks:
      run: /opt/homebrew/bin/gitleaks protect --staged --verbose

commit-msg:
  commands:
    conventional-commit:
      run: |
        MSG=$(head -1 "{1}")
        echo "$MSG" | grep -qE '^(feat|fix|docs|refactor|test|chore|ui|perf|ci)(\([a-z0-9-]+\))?!?: .{1,72}$' || \
        (echo "❌ Commit message must follow conventional commits format" && \
         echo "   Example: feat(live-activity): add stop button" && exit 1)
```

The `commit-msg` hook uses only shell builtins (`head`, `grep`, `echo`) so it doesn't
need the PATH fix.

---

## 2026-04-02 — Document multi-target fastlane signing for app extensions

**What changed:** Added comprehensive guidance for signing app extensions (widgets, share
extensions, etc.) in fastlane and CI. The bootstrap Fastfile template now includes
comments showing where to add extension targets. Section 4.1 in the playbook now covers
the full multi-target setup: Fastfile changes, CI provisioning profile installation,
GitHub secrets, and Apple Developer Portal checklist.

**Playbook files affected:** `ios-project-playbook.md` (§4.1 expanded),
`CLAUDE-TEMPLATE.md` (callout added to Build & Deploy), `bootstrap.sh` (Fastfile comments)

**How to upgrade your project:**

If your app has extension targets (widgets, etc.):
1. Update your `Fastfile` to add a `targets:` filter to the existing
   `update_code_signing_settings` call for the main app target
2. Add a second `update_code_signing_settings` block for each extension target with
   its own `profile_name`, `bundle_identifier`, and `targets` filter
3. Update `export_options.provisioningProfiles` in `build_app` to include all bundle IDs
4. Apply the same changes to both `beta` and `release` lanes
5. In `testflight.yml`, update the "Install provisioning profile" step to install
   each extension's profile as a separate `.mobileprovision` file, and update cleanup
6. Add `PROVISIONING_PROFILE_<EXT>` GitHub secrets for each extension

If your app is single-target, no changes needed.

---

## 2026-04-02 — Add WORKLOG.md session diary pattern

**What changed:** Projects now use a separate `WORKLOG.md` file as a gitignored session
diary. CLAUDE.md remains the stable reference doc; WORKLOG.md tracks what happened
session by session (what changed, decisions, blockers). This keeps CLAUDE.md clean and
gives new sessions rich context without re-reading the codebase.

**Playbook files affected:** `CLAUDE-TEMPLATE.md`, `bootstrap.sh`,
`ios-project-playbook.md`, `getting-started.md`

**How to upgrade your project:**

1. Add `WORKLOG.md` to your `.gitignore` (alongside `MANUAL-TASKS.md`)
2. Create `WORKLOG.md` in your project root with this header:
   ```markdown
   # [APP_NAME] Work Log

   > Session diary for Claude Code sessions. Reverse-chronological.
   > CLAUDE.md is the reference doc; this file tracks what happened session by session.
   > This file is gitignored — local scratchpad only.

   ---
   ```
3. In your `CLAUDE.md`, update the "Current State" callout to:
   > Update this section and WORKLOG.md at the end of every session. CLAUDE.md gets a
   > summary update; WORKLOG.md gets the detailed session diary entry.
4. Add to your Session Startup Checklist (as step 2, after reading CLAUDE.md):
   - **Read `WORKLOG.md`** — review recent session history for context
5. Add to your Session End Checklist (after updating Current State):
   - **Update `WORKLOG.md`** with detailed session diary entry
6. Add the "Work Log Rule" section to your CLAUDE.md (see `CLAUDE-TEMPLATE.md` for
   the full section including entry format and rules)
7. If your CLAUDE.md has accumulated session history in the Current State section,
   migrate it into WORKLOG.md entries and trim Current State back to a summary
