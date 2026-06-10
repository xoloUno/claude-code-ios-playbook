---
description: Build commands, TestFlight/App Store deploy, version lifecycle, cloud limitations
globs: **/Fastfile, **/fastlane/**, **/*.yml, **/project.yml
---

# Build & Deploy

See `ios-project-playbook.md` for full CI/CD reference.

## Ruby & bundler environment

Every `fastlane` lane runs under **bundler**, which needs **Homebrew Ruby** — the
`Gemfile.lock` pins bundler 4.0.3, and macOS's built-in system Ruby (2.6, at `/usr/bin`)
doesn't ship it. Two gotchas make this bite, and a bare `bundle exec` is how they surface:

- **`bundle` resolves to the wrong Ruby.** macOS `path_helper` (run by `/etc/zprofile` in
  every *login* shell, including the agent's non-interactive one) front-loads `/usr/bin`
  ahead of `/opt/homebrew/opt/ruby/bin` — so `bundle` finds system Ruby 2.6 and fails with a
  bundler-version error, **even when `~/.zshenv` prepends Homebrew Ruby** (path_helper runs
  *after* `.zshenv`). The durable fix is one line in **`~/.zprofile`** (which runs after
  path_helper): `export PATH="/opt/homebrew/opt/ruby/bin:$PATH"`. Then every shell resolves
  Ruby 4.x and no per-command prefix is needed.
- **Until a machine is fixed that way, prefix every bundler invocation** with the Homebrew
  Ruby path. `/deploy` and `/release` already do; for any ad-hoc lane, use the same prefix:

  ```bash
  export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && bundle exec fastlane <lane>
  ```

Sanity check before a long lane: `bundle -v` should print `4.0.3` (not `1.17.2`, the version
system Ruby 2.6 bundles) — if it prints the wrong one, your PATH is resolving the wrong Ruby.

## Quick Commands (local)

```bash
# Compile check
xcodebuild build -scheme [APP_NAME] -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -quiet

# TestFlight upload  (needs Homebrew Ruby on PATH — see "Ruby & bundler environment")
bundle exec fastlane beta

# App Store upload
bundle exec fastlane release
```

## Local TestFlight Deploy (Preferred)

```bash
# Via slash command (recommended)
/deploy

# Manual alternative (Homebrew Ruby prefixed — see "Ruby & bundler environment")
export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && set -a && source .env.fastlane && set +a && bundle exec fastlane beta
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

# Upload + ship — these lanes are common to every app
bundle exec fastlane upload_metadata     # Sync metadata only
bundle exec fastlane upload_screenshots  # Upload screenshots only
bundle exec fastlane release             # Build + upload binary with metadata
```

Metadata lives in `fastlane/metadata/<locale>/`. Edit those files before running `/release`.

**Screenshots — Shotsmith is the standard pipeline** (Flara's): it composes captioned + gradient
ASC images and wraps frames-cli internally for bezels; bootstrap emits a `compose_screenshots`
lane for it. A project's *capture* lanes depend on its surfaces, so read the exact names from
`bundle exec fastlane --list` (or the Fastfile) rather than assuming:
- **In-app screens** (every app): XCUITest capture → `compose_screenshots`.
- **Manual-gesture surfaces** *only if the app has them*: Live Activity / widget / Control Center
  via `/capture-manual-surfaces` (e.g. `widget_screenshots`, `control_center_screenshot`).

See [`screenshot-pipeline.md`](screenshot-pipeline.md) for the raw → framed → composed contract.
Install Shotsmith once per machine: `pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0`.

> Apps still on the older frames-cli `screenshots`/`frame_screenshots` lanes should migrate to
> Shotsmith (the standard) — it's a superset (gradient + captions on top of device bezels).

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
**Xcode MCP Bridge** (`xcrun mcpbridge` — previews, docs search, diagnostics; requires
Xcode running; Xcode 27 adds device-interaction and String Catalog localization tools
plus exportable first-party agent skills — see `wwdc26-ios27.md`),
**Apple Docs MCP** (API verification), **GitHub MCP** (CI status, PRs), and
**Context7** (third-party library docs).

See the playbook's `claude-code-plugins-setup.md` for setup instructions — bundled
with the playbook plugin, or read it at
https://github.com/xoloUno/claude-code-ios-playbook/blob/main/claude-code-plugins-setup.md.

Cloud sessions do not have access to MCP tools. Use GitHub Actions for
build verification (push to branch → Build Check workflow). For API
verification in cloud sessions, fall back to web search on developer.apple.com.
