---
description: WWDC26, iOS 27, and Xcode 27 awareness and verification rules
globs: **/*.swift
---

# WWDC26 & iOS 27 / Xcode 27 Awareness

**Current date context: June 2026. The current shipping OS is iOS 26. iOS 27 and
Xcode 27 were announced at WWDC26 (2026-06-08) and are in developer beta.**

Claude Code's training data predates WWDC26. iOS 27, Xcode 27, and everything below
exist — do not treat them as hallucinations, and do not rely on training knowledge for
any API introduced or changed at WWDC26. Verify with the **apple-docs MCP tool** first,
exactly as `wwdc25-ios26.md` requires for WWDC25 material.

**Platform facts:** iOS 27, iPadOS 27, macOS 27, watchOS 27, tvOS 27, visionOS 27;
Swift 6.4. **Xcode 27 is Apple-silicon-only.** Beta caveat: everything in this rule was
verified on Xcode 27 beta build **27A5194q** — re-verify behavior at GM before relying
on it in release tooling.

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
DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer \
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

`mcpbridge` is a stdio MCP bridge to a running Xcode (server name `xcode-tools`; the
binary also exists in Xcode 26.5, without the skills-export subcommand). Tools are
**session-scoped to a workspace tab** — `tools/list` returns nothing headless. Known
tools (from Apple's own skills): `XcodeGlob`/`XcodeGrep`/`XcodeRead`/`XcodeLS`/`XcodeUpdate`,
`GetTargetBuildSettings`, `DeviceInteractionStartSession`/`DeviceInteractionInstallAndRun`/
`DeviceEventSynthesize`/`DeviceInteractionEndSession`, and the localization tools
(`LocalizationPlanner`, `StringCatalogRead`/`StringCatalogContext`/`StringCatalogEdit`).
See `build-deploy.md` for how this relates to the third-party MCP servers.

## Localization agents

Xcode 27 translates String Catalogs agent-natively (coordinator + sub-agents over the
String Catalog MCP tools; output is marked "Machine Translated"). The agents auto-read
`AGENTS.md`, `CLAUDE.md`, and files they reference (e.g. `TRANSLATION.md`). Apple
bundles per-locale style guides for 16 locales — **none for Spanish or Portuguese** —
so the project glossary carries that weight (see `metadata-translation.md`).
