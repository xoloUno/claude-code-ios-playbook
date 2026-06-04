---
description: App Intents / App Shortcuts gotchas — the 10-entry build-time cap and unreliable simulator dispatch
globs: **/*Intent*.swift, **/*Shortcut*.swift, **/*AppShortcuts*.swift
---

# App Intents & App Shortcuts

Two empirically-verified traps when working with `AppShortcutsProvider` / App Intents. Both cost
real debugging time because neither surfaces where you'd first look.

## `AppShortcutsProvider` is hard-capped at 10 entries

`AppShortcutsProvider.appShortcuts` accepts at most **10 entries per app**. Going over fails the
build:

> error: Found N App Shortcuts, but each app may have at most 10

The cap is enforced by **`appintentsmetadataprocessor`** (an Xcode build phase), **not** by
SourceKit or the Swift compiler — so the file compiles, SourceKit looks happy, and the failure
only appears during a full build's app-intents processing step. Easy to miss when iterating
without building. Apple's guidance ("between 4 and 10 of the most useful shortcuts", WWDC22
"Implement App Shortcuts with App Intents") is enforced as a hard upper bound.

The limit is on the **registered entry count**, not source lines — a
`for case in SomeEnum.allCases` loop inside `AppShortcutsBuilder` compiles but still generates
too many entries at build time and is rejected.

**When an app has more than ~10 first-class actions**, the pattern is:

1. Register the most broadly-useful subset (≤10, including any generic "open picker" entry).
2. Use a **parameterized intent** (e.g. `StartIntent(target: SomeEnum)`) so Siri voice-matches
   `"<verb> <any value>"` via the enum's `caseDisplayRepresentations` — one entry covers the
   whole set.
3. Layer dynamic `UIApplication.shared.shortcutItems` (a separate API, with its own ~4-entry
   home-screen limit) for recency-driven menu entries. The two coexist cleanly.

A quick count when you need one: `grep -c "AppShortcut(" <YourShortcutsProvider>.swift`.

## AppShortcut dispatch can fail on the Simulator — verify on a real device

AppShortcut **dispatch** (tapping a shortcut from Spotlight or the Shortcuts app) has been seen
to fail on the Simulator even for a known-good, shipping configuration: the shortcuts appear in
Spotlight / Shortcuts (so metadata extraction works), but tapping returns "Shortcuts couldn't
find shortcut" / "Unable to run app shortcut". Verified on the iOS 26.5 simulator (2026-05-14)
against an App Store configuration that dispatched correctly on a real device with the **same
binary**. Sim reboot, erase, app reinstall, and fresh DerivedData did **not** fix it — it's a
simulator-only dispatch failure, not an app bug.

**Apply:**

- Do not iterate on `AppShortcutsProvider` changes through the Simulator — each cycle burns
  install/test/erase time confirming nothing. Verify dispatch on a **real device** (TestFlight
  build) before committing follow-ups.
- The build-time surfaces ARE checkable without a device: the 10-cap above, and the extracted
  `.appintents/extract.actionsdata` metadata (`autoShortcuts` count, `phraseTemplates`,
  `shortTitle`, `systemImageName`). Inspect those to confirm what the metadata processor
  produced — they catch build-time issues (wrong icon, missing phrase), not runtime dispatch.
- Mixing pre-baked and parameterized variants of the same intent type may not coexist cleanly;
  verify on a real device before relying on it.

See [`simulator.md`](simulator.md) for the broader "the simulator lies" gotchas.
