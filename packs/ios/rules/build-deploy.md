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

Local deploy saves ~250 GitHub Actions credits per upload and is faster.
**Prerequisite:** `.env.fastlane` must exist in project root. See `ios-project-playbook.md` §1.6.

> **App extensions (widgets, etc.):** If this project has extension targets, the Fastfile
> needs a separate `update_code_signing_settings` call and provisioning profile per target.
> See `ios-project-playbook.md` §4.1 for the full multi-target signing setup.

## App Store Release

```bash
# Via slash command (recommended — validates metadata, syncs, builds, uploads)
/release

# Individual lanes for granular control (the lanes bootstrap emits)
bundle exec fastlane widget_screenshots  # Live Activity + widget via simctl — or prefer /capture-manual-surfaces
bundle exec fastlane compose_screenshots # Shotsmith pipeline: stage → frame → compose (captioned + gradient)
bundle exec fastlane upload_metadata     # Sync metadata only
bundle exec fastlane upload_screenshots  # Upload screenshots only
bundle exec fastlane release             # Build + upload binary with metadata
```

Metadata lives in `fastlane/metadata/en-US/`. Edit those files before running `/release`.
Screenshots go in `fastlane/screenshots/en-US/` — see `ios-project-playbook.md` §4.5.

**Screenshot tooling prerequisite:** `compose_screenshots` shells out to
[shotsmith](https://github.com/xoloUno/shotsmith), which wraps frames-cli internally for
device bezels. Install once per machine:
`pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0`. The full directory
contract and the human-in-the-loop manual-capture step are in
[`screenshot-pipeline.md`](screenshot-pipeline.md) and the `/capture-manual-surfaces` command.

**Required screenshot simulators (ASC auto-scales these to smaller sizes):**

| ASC Category | Simulator | Resolution | Required? |
|---|---|---|---|
| **iPhone 6.9"** | **iPhone 17 Pro Max** | **1320 × 2868** | **Yes** — or 6.5" as fallback |
| **iPad 13"** | **iPad Pro 13-inch (M5)** | **2064 × 2752** | **Yes** if app supports iPad |
| iPhone 6.5" | iPhone 14 Plus | 1284 × 2778 | Fallback only |
| iPhone 6.3" | iPhone 17 Pro | 1179 × 2556 | **Not accepted** — scaling target |
| iPad Pro 11" | iPad Pro 11-inch | 1668 × 2388 | **Not accepted** — scaling target |

ASC accepts only 6.9" (iPhone) and 13" (iPad) as submissions per [Apple's spec](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/).
Uploading only 6.3" or 11" blocks "Add for Review." Apple auto-scales 6.9" down to
every smaller iPhone size and 13" to 11" iPad. See `ios-project-playbook.md` §Phase 5.

## Version Lifecycle

After any version is approved on the App Store, immediately bump `MARKETING_VERSION`
in `project.yml` to the next minor version. ASC closes the version train on approval —
new TestFlight builds will be rejected until the version is incremented. See
`ios-project-playbook.md` §6.5.

## Cloud Session Limitations

**Cannot:** Run `xcodebuild`, `fastlane`, test on Simulator, modify `.pbxproj`.
**Should not:** Push to `main` — local sessions handle merges and deploys.
**Can:** Edit Swift files, commit/push to `dev` or feature branches, plan, write features.

## Available Plugins & MCP Servers

Local sessions have access to: **XcodeBuildMCP** (builds, tests, simulators),
**Xcode MCP Bridge** (previews, docs search, diagnostics — requires Xcode running),
**Apple Docs MCP** (API verification), **GitHub MCP** (CI status, PRs), and
**Context7** (third-party library docs).

See `_playbook/claude-code-plugins-setup.md` for setup instructions.

Cloud sessions do not have access to MCP tools. Use GitHub Actions for
build verification (push to branch → Build Check workflow). For API
verification in cloud sessions, fall back to web search on developer.apple.com.
