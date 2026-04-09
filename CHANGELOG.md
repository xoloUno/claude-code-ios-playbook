# Playbook Changelog

Recent changes to the iOS project playbook. When starting a Claude Code session in a
project that uses this playbook, read this file to check if the project needs updating.

Each entry describes what changed, which playbook files were affected, and what to do
in your project to adopt the change.

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
