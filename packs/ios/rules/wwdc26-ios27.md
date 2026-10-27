---
description: WWDC26, iOS 27, and Xcode 27 awareness and verification rules
globs: **/*.swift
---

# WWDC26 & iOS 27 / Xcode 27 Awareness

**Current state (checked 2026-10-27): iOS 27 and Xcode 27 have shipped. The current
Xcode is 27.1 (27A9275) with the iOS 27.1 SDK. WWDC26 was 2026-06-08.**

Claude Code's training data predates WWDC26. iOS 27, Xcode 27, and everything below
exist — do not treat them as hallucinations, and do not rely on training knowledge for
any API introduced or changed at WWDC26. Verify with the **apple-docs MCP tool** first,
exactly as `wwdc25-ios26.md` requires for WWDC25 material.

**Platform facts:** iOS 27, iPadOS 27, macOS 27, watchOS 27, tvOS 27, visionOS 27;
Swift 6.4. **Xcode 27 is Apple-silicon-only.** Most items below were first verified on
Xcode 27 beta **27A5194q**; the Xcode MCP and iPhone Duo sections were rechecked on 27.1.
Re-verify an older item before relying on it in release tooling.

## Frameworks that require apple-docs verification before use

In addition to the `wwdc25-ios26.md` list: **Foundation Models** (WWDC26 additions:
image input, server models, third-party model protocol, Dynamic Profiles), **Core AI**
(new framework for on-device LLMs), **App Intents** (Siri personal-context additions),
and any SwiftUI API introduced or changed in SDK 27.

> **SDK 27 source break — `@State` is now a macro, not a property wrapper.** Existing
> views can stop compiling after an SDK update ("used before being initialized",
> "invalid redeclaration of synthesized property", "extraneous argument label"). The
> obvious fix — reordering init assignments — is WRONG and changes runtime behavior.
> Consult Apple's `swiftui-whats-new-27` skill (see below) before touching it.

## First-party Xcode agent skills (verified 27A5194q)

Xcode 27 ships seven agent skills, exportable for use in any agent:

```sh
xcrun mcpbridge run-agent skills export --output-dir <dir> --replace-existing
```

(`xcrun agent` is an alias of `mcpbridge`; the export **requires Xcode running**;
default output dir is `./xcode-skills`.) Skills: `swiftui-specialist` (best practices),
`swiftui-whats-new-27` (SDK 27 changes + deprecations — the authority for the `@State`
macro break above), `test-modernizer` (XCTest → Swift Testing migration),
`device-interaction` (subagent skill; needs Xcode's MCP tools), `audit-xcode-security-settings`,
`uikit-app-modernization`, `c-bounds-safety`.

**Claude Code does not read `~/.agents/skills`** (verified) — link exported skills into
`~/.claude/skills/` (or a project's `.claude/skills/`) to make Claude Code see them.
Codex/Gemini/Cursor read `~/.agents/skills` directly. Knowledge-only skills (SwiftUI,
testing) work anywhere; `device-interaction` and the security audit need Xcode's
`xcode-tools` MCP server and degrade outside it.

## Xcode MCP tools (`xcrun mcpbridge`)

`mcpbridge` is the stdio MCP bridge agents connect through; it targets the Xcode that
`xcode-select` picks (`MCP_XCODE_PID` overrides). **Use the tool names the server lists** —
they change between releases, and the exported skills lag: `device-interaction` still says
`DeviceEventSynthesize`, while Xcode 27.1 exposes `DeviceInteractionSynthesize`.

Headless mode is optional: `xcrun mcp-server` manages the service (`status`, `open`, and
sudo-only `enable` / `allow-folder` / `approve`). A connection that already works doesn't need
it, and turning it on is the user's call.

Seen in Flara's workflow (not reproduced elsewhere): opening an XcodeGen project in Xcode,
including through these tools, rewrote tracked files — a scheme's version and a String
Catalog's formatting. Close the workspace and revert, or regenerate.

See `build-deploy.md` for how this relates to the third-party MCP servers.

## iPhone Duo (foldable, iOS 27.1)

Checked against the iOS 27.1 SDK:
- Gate Duo-only layout on `@Environment(\.toolbarVerticalEdge)` (nil wherever there's no
  vertical toolbar column), not on the device model. `ToolbarItem(…).axisBehavior(.verticalPreferred)`
  puts an item in that column.
- `GeometryProxy.reservedRegions(kind: .division)` gives the crease frame when half-open;
  `onHingeChange` reports hinge changes.
- `simctl` has no fold command: set poses in Device Hub. To capture one screen, find its ID
  with `xcrun simctl io <device> enumerate`, then `screenshot --display=<id>`.
- Framing needs frames-cli 1.5.0+ and its new asset pack (see `ios-project-playbook.md`,
  Track A).

## Localization agents

Xcode 27 translates String Catalogs agent-natively (coordinator + sub-agents over the
String Catalog MCP tools; output is marked "Machine Translated"). The agents auto-read
`AGENTS.md`, `CLAUDE.md`, and files they reference (e.g. `TRANSLATION.md`). Apple
bundles per-locale style guides for 16 locales — **none for Spanish or Portuguese** —
so the project glossary carries that weight (see `metadata-translation.md`).
