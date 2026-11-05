---
description: Simulator and device-loop hygiene — install over (don't uninstall), pin and boot one sim by UDID, never strip entitlements via signing overrides, and know what the Simulator can't prove
globs: **/*
---

# Simulator build & run hygiene

Three traps when building or running an app on a booted simulator for verification. All are
correctness-critical: one silently destroys hand-built sim state, one splits your work across two
sims, and one crashes the app at launch. Shorter traps and Simulator limits have their own
sections.

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

## Pin one simulator by UDID when names repeat

The same device name can exist on several installed runtimes (an "iPhone 17 Pro Max" on both
iOS 26.5 and 27.0, say). Name lookups then resolve per tool: `simctl … | head -1` and
`xcodebuild -destination 'platform=iOS Simulator,name=…'` can land on different sims, so you
prep one and build, install or capture on the other. Resolve the UDID once and use it
everywhere: `simctl` takes a UDID wherever it takes a name, and `xcodebuild` takes
`-destination 'platform=iOS Simulator,id=<UDID>'`.

Boot it first: `xcrun simctl boot <UDID>; xcrun simctl bootstatus <UDID> -b`. Given a
shut-down destination, `xcodebuild test` has sat for 10+ minutes with no output and never
booted it. Write the full log to a file rather than piping through `grep` or `-quiet`, so a
hang shows as an empty log instead of a slow test.

On Xcode 27.1, the iOS 27.1 runtime offers only the iPhone Duo device type, so checking a fix
on 27.1 means creating a Duo sim.

## Simulator tooling traps

- Regenerating with `xcodegen generate` while Xcode has the project open resets Xcode's run
  destination, and the next Xcode or MCP run quietly uses another sim. Re-select it.
- After one Xcode run with a `.storekit` configuration, `simctl launch` on that sim keeps the
  local StoreKit environment and its test transactions. A clean "never purchased" state
  needs a fresh sim.
- A screenshot taken right after a tap can show the previous frame. Wait about a second, or
  use `xcrun simctl io <UDID> screenshot`.
- To capture `print` output, run `xcrun simctl launch --console <UDID> <bundle-id>` in the
  background redirected to a file; `--stdout=<path>` wrote nothing.
- Crash reports land in `~/Library/Logs/DiagnosticReports/<App>-<date>.ips`.

## What the Simulator can't prove

Seen on the iOS 27.0 and 27.1 Simulators; each looks like an app bug:
- `RemoteMediaSession.start` (NowPlaying) throws `internalFailure`. Test it on a device.
- Multicast discovery (SSDP over `NWConnectionGroup`) receives only its own looped-back
  packets, never the devices' unicast replies. Test networking modules in a scratch macOS
  SwiftPM harness that copies the module sources, then on a device.
- A synthesized tap doesn't end a `DragGesture(minimumDistance: 0)` used as a tap target; a
  finger on a device does.

Anything that crosses app suspension (a handshake approved in another app, background
delivery) needs a device test too: a Mac or the Simulator never suspends the app.

## Device test loops

- Reinstalling without changing `CFBundleVersion` can leave iOS running the old build of an
  app extension. Pass `CURRENT_PROJECT_VERSION=$(date +%Y%m%d%H%M)` to each device build in a
  test loop, and have probe code log its own `CFBundleVersion`.
- An extension is suspended between system callbacks, so a log written from a detached `Task`
  may never reach disk. Write synchronously under a lock (`Synchronization.Mutex`).
- `devicectl device copy from --domain-type appGroupDataContainer` reads only under
  `Library`, `Documents` or `tmp`, not the container root.

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
