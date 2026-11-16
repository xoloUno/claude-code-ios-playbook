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
# A passing -quiet log can print "error: the following command failed with exit code 0 but
# produced no further output". Judge the build by its exit status, not by grepping "error:".

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

**Profiles from an agent's shell.** When a device build needs a profile refresh
(`-allowProvisioningUpdates`, say after Apple grants a restricted entitlement), `xcodebuild`
in an agent's shell reports "No Accounts" even with an Apple ID signed in to Xcode, then
blames the entitlement ("requires approval from Apple"). Pass the ASC API key from
`.env.fastlane` instead: `-authenticationKeyPath "$ASC_KEY_FILEPATH" -authenticationKeyID
"$ASC_KEY_ID" -authenticationKeyIssuerID "$ASC_ISSUER_ID"`. Keep profile backups outside the
profile folders: `xcodebuild` tries to load every file there and logs a warning per backup on
each archive, burying real signing errors.

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

A lane that passes `sync_screenshots: true` to `deliver` fails unless
`FASTLANE_ENABLE_BETA_DELIVER_SYNC_SCREENSHOTS=1` is set (still beta-gated in fastlane 2.232).
Set `ENV["FASTLANE_ENABLE_BETA_DELIVER_SYNC_SCREENSHOTS"] = "1"` inside the lane, or export it
when invoking.

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

**Screenshot sizes** (checked against [Apple's spec](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/)
on 2026-11-16; re-check it before a submission):

| ASC category | Simulator | Resolution | Required? |
|---|---|---|---|
| **iPhone with Dynamic Island (medium)** | **iPhone 17 Pro** | **1206 × 2622** (or 1179 × 2556) | **Yes**, at least one |
| iPhone with Dynamic Island (large) | iPhone 17 Pro Max | 1320 × 2868 | Recommended; otherwise scaled |
| **iPad 13"** | **iPad Pro 13-inch (M5)** | **2064 × 2752** | **Yes** if the app runs on iPad |
| iPhone Duo | iPhone Duo | outer 1398 × 2034, inner 2007 × 2853, either orientation | From April 2027 for iOS 27.1 SDK apps; earns the Duo badge |

- Until 2026 the 6.9" set was the required one. The bootstrap capture defaults and
  shotsmith's device registry still target 1320 × 2868, so a new submission also needs a
  medium set.
- Images can't carry an alpha channel, and `simctl io screenshot` PNGs do. Save as RGB before
  uploading.
- The Duo set needs fastlane 2.241.1 or later (`APP_IPHONE_DUO`). Use one size and
  orientation across the set.
- `deliver` reads only the images directly inside `screenshots/<locale>/`, and after each
  upload it reorders every set by file name. File numbers set the product-page order, so
  names must be unique across devices.
- A metadata-only or screenshot-only `deliver` still reads the version from the newest
  `*.ipa` in the project root and renames the editable App Store version to match. Pass
  `skip_app_version_update: true` in those lanes.

See `ios-project-playbook.md` §Phase 5.

## Version Lifecycle

After any version is approved on the App Store, immediately bump `MARKETING_VERSION`
in `project.yml` to the next **patch** version (2.2.1 → 2.2.2). ASC closes the version train
on approval — new TestFlight builds will be rejected until the version is incremented. Raise
it to the next minor or major when feature work for that release starts; ASC lets you change
a version's number until it's submitted. See `ios-project-playbook.md` §6.5.

## Cloud Session Limitations

**Cannot:** Run `xcodebuild`, `fastlane`, test on Simulator, modify `.pbxproj`.
**Should not:** Push to `main` — local sessions handle merges and deploys.
**Can:** Edit Swift files, commit/push to `dev` or feature branches, plan, write features.

**XcodeGen projects:** adding, removing or renaming a source file changes the tracked
`project.pbxproj`, and CI that runs `xcodegen generate` first will hide a stale one. Regenerate
and commit the result before merge. If the session can't run XcodeGen, say so in the PR body and
`MANUAL-TASKS.md` so a local session does it before merging.

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
build verification (open a PR → Build Check workflow). For API
verification in cloud sessions, fall back to web search on developer.apple.com.
