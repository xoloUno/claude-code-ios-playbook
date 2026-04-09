---
description: WWDC25 and iOS 26 framework verification rules
globs: **/*.swift
---

# WWDC25 & iOS 26 Awareness

**Current date context: April 2026. The current shipping OS is iOS 26 (released fall 2025).**

Claude Code's training data predates WWDC25 (June 9–13, 2025). Before writing any code
that touches new frameworks, use the **apple-docs MCP tool** to verify the current API.
Do not rely on training knowledge for anything introduced at or after WWDC25.

**OS naming:** iOS 18 → iOS 26 (skipping 19–25). All platforms: iPadOS 26, macOS Tahoe 26,
watchOS 26, tvOS 26, visionOS 26. Xcode 26.

**Liquid Glass:** iOS 26 visual design system — translucent, layered UI. SwiftUI apps get
adaptations automatically. Use standard components and let the system style them.

**SF Symbols 7:** Updated library. Verify symbol names exist before using them.

## Framework Verification Rule

Before writing code using any Apple framework introduced at or after WWDC25, Claude Code
MUST use the **apple-docs MCP tool** to look up the current API. This replaces web search
— the MCP tool queries Apple's official documentation JSON API directly and returns
accurate, up-to-date results including beta status and deprecation flags. For third-party
libraries (TelemetryDeck, Sentry, etc.), use the **Context7 MCP tool** if available.

If MCP tools are unavailable (e.g. cloud session), fall back to web search on
developer.apple.com.

Frameworks that always require verification before use: ActivityKit, AppIntents, WidgetKit,
FoundationModels, HealthKit (iOS 26 additions), Metal 4, RealityKit, any SwiftUI modifier
introduced after iOS 18.
