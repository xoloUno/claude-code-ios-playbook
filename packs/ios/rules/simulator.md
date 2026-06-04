---
description: Simulator build/run hygiene — install over (don't uninstall), and never strip entitlements via signing overrides
globs: **/*
---

# Simulator build & run hygiene

Two traps when building or running an app on a booted simulator for verification. Both are
correctness-critical: one silently destroys hand-built sim state, the other crashes the app at
launch.

## Install over the existing build — never uninstall to redeploy

When deploying to a booted simulator for visual verification, **install over the current build;
do not uninstall first.** Use `xcrun simctl install booted <App.app>` (overwrites the bundle in
place), and make sure no `xcodebuild`/build-agent step is chained with an uninstall.

**Why:** `simctl uninstall <bundle-id>` cascades and wipes manually-configured sim state that's
expensive to recreate — pinned Home Screen widgets, Control Center button placement, and the app
container (in-progress state, preferences, trial/subscription flags). The manual-capture
screenshot flow (see [`screenshot-pipeline.md`](screenshot-pipeline.md)) depends on exactly that
state.

**Apply:**

- UI verification: `xcrun simctl install booted <App.app>` → `xcrun simctl launch booted <bundle-id>`. No uninstall.
- To reset only app preferences (e.g. clear a leaked appearance/theme between captures):
  surgically `rm <container>/Library/Preferences/<bundle-id>.plist`, not `simctl uninstall`.
- A true cold-install test is rare — ask first.
- Same rule for watchOS / iPadOS sims, not just iPhone.

## Don't strip entitlements via signing overrides on entitlement-gated apps

For sim builds of an app gated by an Apple framework that asserts on a missing entitlement at
init, **build with default project signing and no signing overrides.** Specifically do NOT pass
`CODE_SIGNING_ALLOWED=NO` and do NOT pass `CODE_SIGN_IDENTITY="-"` — both end up with no `.xcent`
(entitlements) embedded in the binary, and the framework then traps at startup.

Concretely: an app declaring `com.apple.developer.icloud-services: [CloudKit]` traps with
`_os_crash` (SIGTRAP) when `CKContainer(identifier:)` runs at init if the binary carries no
iCloud entitlement. Verified on the iOS 26.5 sim (2026-05-14): both override flags crash at
launch; **no signing flags** lets Xcode apply "Sign to Run Locally" ad-hoc signing while keeping
the entitlements file. The command that works:

```bash
xcodebuild build -scheme <Scheme> -configuration Debug \
  -destination 'platform=iOS Simulator,id=<UDID>'
```

**Apply:** when delegating a sim build (e.g. to a build agent that defaults to
`CODE_SIGNING_ALLOWED=NO`), instruct it explicitly: "Do NOT pass `CODE_SIGNING_ALLOWED=NO`; do
NOT override `CODE_SIGN_IDENTITY`; use default project signing." Generalizes to any framework
that asserts on a missing entitlement at init — **CloudKit, MapKit, WeatherKit, App Attest**, etc.
