---
description: Build commands, TestFlight/App Store deploy, version lifecycle, cloud limitations
globs: **/Fastfile, **/fastlane/**, **/*.yml, **/project.yml
---

# Build & Deploy

See `ios-project-playbook.md` for full CI/CD reference.

## Quick Commands (local)

```bash
# Compile check
xcodebuild build -scheme [APP_NAME] -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -quiet

# TestFlight upload
bundle exec fastlane beta

# App Store upload
bundle exec fastlane release
```

## Local TestFlight Deploy (Preferred)

```bash
# Via slash command (recommended)
/deploy

# Manual alternative
set -a && source .env.fastlane && set +a && bundle exec fastlane beta
```

Local deploy saves ~250 GitHub Actions credits per upload and gives faster feedback.
**Prerequisite:** `.env.fastlane` must exist in project root. See `ios-project-playbook.md` §1.6.

> **App extensions (widgets, etc.):** If this project has extension targets, the Fastfile
> needs a separate `update_code_signing_settings` call and provisioning profile per target.
> See `ios-project-playbook.md` §4.1 for the full multi-target signing setup.

## App Store Release

```bash
# Via slash command (recommended — validates metadata, syncs, builds, uploads)
/release

# Individual lanes for granular control
bundle exec fastlane upload_metadata     # Sync metadata only
bundle exec fastlane upload_screenshots  # Upload screenshots only
bundle exec fastlane release             # Build + upload binary with metadata
```

Metadata lives in `fastlane/metadata/en-US/`. Edit those files before running `/release`.
Screenshots go in `fastlane/screenshots/en-US/` — see `ios-project-playbook.md` §4.5.

**Required screenshot simulators (ASC rejects wrong resolutions):**

| ASC Category | Simulator | Resolution | Required? |
|---|---|---|---|
| iPhone 6.5" | **iPhone 14 Plus** | 1284 × 2778 | **Yes** — blocks "Add for Review" |
| iPad 13" | **iPad Pro 13-inch (M5)** | 2064 × 2752 | **Yes** — blocks "Add for Review" |
| iPhone 6.3" | iPhone 16/17 Pro | 1179 × 2556 | Optional |
| iPhone 6.9" | iPhone 16 Pro Max | 1260 × 2736 | Optional |

ASC categories are resolution-based. iPhone 17 Pro is 6.3" — it does NOT satisfy the 6.5"
requirement. Always use iPhone 14 Plus (or iPhone 13 Pro Max) for the mandatory 6.5" size.

## Version Lifecycle

After any version is approved on the App Store, immediately bump `MARKETING_VERSION`
in `project.yml` to the next minor version. ASC closes the version train on approval —
new TestFlight builds will be rejected until the version is incremented. See
`ios-project-playbook.md` §6.5 for details.

## Cloud Session Limitations

**Cannot:** Run `xcodebuild`, `fastlane`, test on Simulator, modify `.pbxproj`.
**Should not:** Push to `main` — local sessions handle merges and deploys.
**Can:** Edit Swift files, commit/push to `dev` or feature branches, plan, write features.

## Available Plugins & MCP Servers

Local sessions have access to: **XcodeBuildMCP** (builds, tests, simulators),
**Xcode MCP Bridge** (previews, docs search, diagnostics — requires Xcode running),
**Apple Docs MCP** (API verification), **GitHub MCP** (CI status, PRs), and
**Context7** (third-party library docs).

See `_playbook/claude-code-plugins-setup.md` for full setup instructions.

Cloud sessions do not have access to MCP tools. Use GitHub Actions for
build verification (push to branch → Build Check workflow). For API
verification in cloud sessions, fall back to web search on developer.apple.com.
