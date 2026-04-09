# CLAUDE.md — [APP_NAME]

This file is the single source of truth for every Claude Code session on this project.
Read it fully before writing any code or suggesting any architecture changes.

> **Reference:** For CI/CD setup, StoreKit 2 subscription setup, and App Store submission
> procedures, see `ios-project-playbook.md` in the `_playbook/` directory.

## Table of Contents

- [Project Overview](#project-overview)
- [Current State](#current-state)
- [Tech Stack](#tech-stack)
- [Target Project Structure](#target-project-structure)
- [UI Direction](#ui-direction)
- [Data Models](#data-models)
- [Monetization](#monetization)
- [Scope Rules](#scope-rules--enforce-these-strictly)
- [Key Product Decisions](#key-product-decisions-dont-revisit-these)
- [Code Style & Conventions](#code-style--conventions)
- [Automated Quality Tools](#automated-quality-tools)
- [App Store Metadata](#app-store-metadata-for-reference)
- [WWDC25 & iOS 26 Awareness](#%EF%B8%8F-wwdc25--ios-26-awareness--read-this-first)
- [Git & Version History](#git--version-history)
- [Build & Deploy](#build--deploy)
- [Session Startup Checklist](#session-startup-checklist)
- [Session End Checklist](#session-end-checklist)
- [Manual Tasks Handoff Rule](#manual-tasks-handoff-rule)
- [Work Log Rule](#work-log-rule)

---

## Project Overview

**App Name:** [APP_NAME]
**Bundle ID:** [com.example.appname]
**URL Scheme:** `[appname]://`
**Xcode Scheme:** [APP_NAME]
**Team ID:** YOUR_TEAM_ID
**Platform:** iOS 26+ (iPhone first, no iPad or Mac targets in v1)
**Developer:** Solo indie dev, 2–5 hrs/week available
**Goal:** [e.g. Ship focused v1 to App Store within N weeks, reach $X/month MRR]

### The Core Problem This App Solves

[One paragraph — what gap exists and how this app fills it. This anchors every decision.]

### The Core Loop (Never Deviate From This in v1)

1. [User does X]
2. [App responds with Y]
3. [Result Z is stored/displayed]
4. Done.

**Architecture summary:** [e.g. No backend. All persistence is local (UserDefaults/SwiftData)
and HealthKit. No user accounts. No server.]

---

## Current State

**Last updated:** [DATE]

**Build status:** [e.g. Compiles, CI green, TestFlight working]

**Last completed work:**
- [What was done in the most recent session]

**Next up:** [What the next session should focus on]

> **Update this section and WORKLOG.md at the end of every session.** CLAUDE.md gets a
> summary update; WORKLOG.md gets the detailed session diary entry. Full session history
> lives in `WORKLOG.md`.

---

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Swift 6 | Modern concurrency, strict safety |
| UI | SwiftUI | Required for widgets and controls |
| Data | [UserDefaults / SwiftData / etc.] | [Why] |
| Subscriptions | StoreKit 2 (native) | Built-in, no dependency, ASC analytics now sufficient |
| Minimum deployment | iOS 26.0 | Current OS; unlocks iOS 26 APIs |

---

## Target Project Structure

```
[APP_NAME]/
├── [APP_NAME]App.swift          # App entry point
├── ContentView.swift            # Root navigation
│
├── Models/
│   └── [list key models]
│
├── Views/
│   └── [list key views]
│
├── Services/
│   └── [list key services]
│
└── CLAUDE.md                    # This file
```

---

## UI Direction

### Aesthetic & Tone

- System adaptive colors throughout — never hardcode `Color.black` or `Color.white`
- [Describe visual style: reference apps, design language]
- System font (SF Pro) throughout
- Liquid Glass system styling applies automatically — do not fight it

### Key Screens

[Describe each major screen with ASCII wireframes where helpful]

---

## Data Models

[Define key structs/enums with Swift code blocks]

---

## [Domain-Specific Section]

[e.g. HealthKit Integration, Metal Rendering, MapKit, etc. — whatever is core to this app.
Include authorization flows, edge cases, and key implementation rules.]

---

## Monetization

### Model

[e.g. App-managed trial → subscription → freemium fallback]

**Provider:** StoreKit 2 (native)

### Pricing

| Plan | Price | Display |
|---|---|---|
| Annual | $X/year | "$X/month — best value" |
| Monthly | $X/month | "$X/month" |
| Free tier | $0 | [What's included] |

### Subscription Group ID

`"[NUMERIC_GROUP_ID]"` — from ASC → Subscriptions → your group → Group ID.

### Product IDs

| Product | Product ID |
|---|---|
| Annual | `[BUNDLE_ID].annual` |
| Monthly | `[BUNDLE_ID].monthly` |

### Subscription Check

```swift
// Use SubscriptionManager from Phase 2 of the playbook
// Gate features: if subscriptionManager.isSubscribed { ... }
// Show paywall: SubscriptionStoreView(groupID: "[NUMERIC_GROUP_ID]")
```

---

## Scope Rules — Enforce These Strictly

### IN SCOPE for v1

- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] [Feature 3]

### OUT OF SCOPE for v1 (do not build, do not discuss)

- [Feature A — deferred to v2]
- [Feature B — unnecessary complexity]

---

## Key Product Decisions (Don't Revisit These)

1. [Decision 1 — rationale]
2. [Decision 2 — rationale]
3. [Decision 3 — rationale]

---

## Code Style & Conventions

- **Swift 6 strict concurrency** — `@MainActor` on view models, `async/await` everywhere
- **No third-party UI libraries** — SwiftUI only, system components only
- **ViewModels are `@Observable`** (not `ObservableObject`)
- **No force unwraps** — `guard let` / `if let`, handle all optionals
- **File naming** matches primary type (one type per file)
- **No comments explaining what** — only why (write self-documenting code)
- **Previews required** for every SwiftUI View
- **SwiftLint enforced** — `.swiftlint.yml` in project root. CI fails on violations.

---

## Automated Quality Tools

### Claude Code Hooks (`.claude/hooks.json`)

A PostToolUse hook runs SwiftLint automatically after every file edit or creation.
This is deterministic — unlike CLAUDE.md instructions, hooks always fire. If SwiftLint
reports issues, fix them before committing.

### Pre-Commit Hooks (Lefthook)

`lefthook.yml` runs three checks before every commit:
1. **SwiftLint** — lint all staged `.swift` files
2. **Gitleaks** — scan for accidentally committed secrets, API keys, tokens
3. **Conventional commit validation** — reject commit messages that don't match
   the `type(scope): description` format

These fire automatically on `git commit`. Claude Code's commits go through the same
hooks — no bypass.

### Claude Code Slash Commands (`.claude/commands/`)

| Command | What it does |
|---|---|
| `/feature {name}` | Scaffolds View + ViewModel + Tests for a new feature |
| `/test {target}` | Generates Swift Testing tests with @Test macros |
| `/review` | Reviews staged changes for concurrency, accessibility, privacy |
| `/deploy` | Builds, signs, and uploads to TestFlight from local machine |
| `/release` | Syncs metadata, builds, and uploads to App Store Connect |

### Dependabot (`.github/dependabot.yml`)

Automatically creates PRs for outdated SPM dependencies weekly. Review and merge
them — don't let dependencies go stale.

---

## App Store Metadata (For Reference)

**App name:** [APP_NAME]
**Subtitle:** [30 char max]
**Bundle ID:** [com.example.appname]

**Target keywords:** [comma-separated keywords for ASO]

**Core value prop:** [One sentence for App Store description lead]

**Primary target audience:** [Who this app is for]

---

## ⚠️ WWDC25 & iOS 26 Awareness — Read This First

**Current date context: March 2026. The current shipping OS is iOS 26 (released fall 2025).**

Claude Code's training data predates WWDC25 (June 9–13, 2025). Before writing any code
that touches new frameworks, use the **apple-docs MCP tool** to verify the current API.
Do not rely on training knowledge for anything introduced at or after WWDC25.

**OS naming:** iOS 18 → iOS 26 (skipping 19–25). All platforms: iPadOS 26, macOS Tahoe 26,
watchOS 26, tvOS 26, visionOS 26. Xcode 26.

**Liquid Glass:** iOS 26 visual design system — translucent, layered UI. SwiftUI apps get
adaptations automatically. Use standard components and let the system style them.

**SF Symbols 7:** Updated library. Verify symbol names exist before using them.

### Framework Verification Rule

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

---

## Git & Version History

**Remote:** GitHub — `https://github.com/YourOrg/[REPO_NAME]`

### Branch Strategy

```
main          ← always shippable; tagged on every submission
dev           ← active development
feature/*     ← one branch per feature
fix/*         ← one branch per bug fix
```

Never commit directly to `main`. Merge from `dev` or feature branches only.

**Concurrent Claude Code sessions:** Use **worktrees** (`/worktree`) when running multiple
sessions against the same repo. A branch only isolates commit history — files on disk are
shared. Without worktrees, sessions overwrite each other's uncommitted work.

### Commit Convention

Format: `type(scope): short description`

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `ui`

Rules: ≤72 char subject, present tense, no trailing period.

### Claude Code Commit Behavior

At session end:
1. `git status` — review changes
2. Stage selectively (never `git add .` blindly)
3. Conventional commit + `Co-Authored-By: Claude <noreply@anthropic.com>`
4. **Local sessions:** Include `[skip ci]` in message — local sessions handle build + deploy
   **Cloud sessions:** Do NOT include `[skip ci]` — CI must verify the build
5. Push to `dev` or feature branch (not `main`)
6. **Update "Current State" section** in this file (mandatory)
7. **Update `WORKLOG.md`** with detailed session diary entry (see Work Log Rule below)
8. **Update `release-notes-draft.md`** with user-facing changes

### Tagging Releases

```bash
git tag -a v1.0.0 -m "App Store v1 submission"
git push origin --tags
```

---

## Build & Deploy

See `ios-project-playbook.md` for full CI/CD reference.

### Quick Commands (local)

```bash
# Compile check
xcodebuild build -scheme [APP_NAME] -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -quiet

# TestFlight upload
bundle exec fastlane beta

# App Store upload
bundle exec fastlane release
```

### Local TestFlight Deploy (Preferred)

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

### App Store Release

```bash
# Via slash command (recommended — validates metadata, syncs, builds, uploads)
/release

# Individual lanes for granular control
bundle exec fastlane upload_metadata     # Sync metadata only
bundle exec fastlane upload_screenshots  # Upload screenshots only
bundle exec fastlane release             # Build + upload binary with metadata
```

Metadata lives in `fastlane/metadata/en-US/`. Edit those files before running `/release`.
Screenshots go in `fastlane/screenshots/en-US/` — see `ios-project-playbook.md` §4.5 for
the capture-and-design workflow.

**Required screenshot simulators (ASC rejects wrong resolutions):**

| ASC Category | Simulator | Resolution | Required? |
|---|---|---|---|
| iPhone 6.5" | **iPhone 14 Plus** | 1284 × 2778 | **Yes** — blocks "Add for Review" |
| iPad 13" | **iPad Pro 13-inch (M5)** | 2064 × 2752 | **Yes** — blocks "Add for Review" |
| iPhone 6.3" | iPhone 16/17 Pro | 1179 × 2556 | Optional |
| iPhone 6.9" | iPhone 16 Pro Max | 1260 × 2736 | Optional |

ASC categories are resolution-based. iPhone 17 Pro is 6.3" — it does NOT satisfy the 6.5"
requirement. Always use iPhone 14 Plus (or iPhone 13 Pro Max) for the mandatory 6.5" size.

### Version Lifecycle

After any version is approved on the App Store, immediately bump `MARKETING_VERSION`
in `project.yml` to the next minor version. ASC closes the version train on approval —
new TestFlight builds will be rejected until the version is incremented. See
`ios-project-playbook.md` §5.5 for details.

### Cloud Session Limitations

**Cannot:** Run `xcodebuild`, `fastlane`, test on Simulator, modify `.pbxproj`.
**Should not:** Push to `main` — local sessions handle merges and deploys.

**Can:** Edit Swift files, commit/push to `dev` or feature branches, plan, write features.

### Available Plugins & MCP Servers

This project has the following Claude Code extensions available in local sessions:

- **XcodeBuildMCP** — use for building, testing, and simulator management.
  Prefer this over raw `xcodebuild` shell commands.
- **GitHub MCP** — use for checking CI status, reading Actions logs,
  creating issues and PRs.
- **Apple Docs MCP** — use to look up Apple framework APIs before writing
  code. Replaces web search for API verification.
- **Apple Platform Build Tools** — reference docs for xcrun ecosystem.
  Consult the Agent Skill when composing complex xcodebuild commands.
- **Xcode MCP Bridge** — Apple's native bridge (Xcode 26.3+). Provides
  documentation search, render previews, and deep IDE integration. Requires
  Xcode running with MCP Tools enabled in Settings → Intelligence.
- **Context7** — fetch current docs for third-party libraries (TelemetryDeck,
  Sentry, etc.) when training data may be stale.

Cloud sessions do not have access to MCP tools. Use GitHub Actions for
build verification in cloud sessions (push to branch → Build Check workflow).
For API verification in cloud sessions, fall back to web search on
developer.apple.com.

**Telegram channel:** Start with `claude --channels plugin:telegram@claude-plugins-official`
to enable mobile monitoring of long-running sessions via Telegram DM.

---

## Session Startup Checklist

1. Read this file fully
2. **Read `WORKLOG.md`** — review recent session history for context
3. `git log --oneline -10` — see recent changes
4. Verify correct branch (create one if needed)
5. Check GitHub Actions for last build status
6. **Check `MANUAL-TASKS.md`** — are there pending human tasks from last session?
7. **Check for open Dependabot PRs** — merge any dependency updates if CI passes
8. Which v1 feature are we building? Is it IN SCOPE?
9. Re-read any files you're about to edit
10. Framework introduced after WWDC25? Use apple-docs MCP to verify API first
11. Ask the user what to work on if not specified

## Session End Checklist

1. `git status` — review everything
2. Stage selectively, write conventional commit
3. Push to `dev` or feature branch
4. **Update "Current State"** in this file (mandatory)
5. **Update `WORKLOG.md`** with detailed session diary entry (see Work Log Rule below)
6. Check off completed scope items
7. **Update `release-notes-draft.md`** with user-facing changes
8. **Create/update `MANUAL-TASKS.md`** if there are human-only tasks (see rule below)

---

## Manual Tasks Handoff Rule

Whenever a session produces tasks that require human action — things Claude Code cannot
do itself — Claude Code MUST write them to `MANUAL-TASKS.md` in the project root rather
than listing them in the chat. This prevents tasks from getting buried in conversation
history and avoids wasting tokens re-listing them later.

**When to create/update this file:**
- Tasks requiring App Store Connect UI (screenshots, metadata, review submission)
- Tasks requiring the Apple Developer Portal (certificates, profiles, bundle IDs)
- Tasks requiring GitHub repo settings (secrets, Pages, branch protection)
- Tasks requiring physical device testing that Claude Code cannot perform
- Any step that requires a human login, GUI interaction, or manual verification

**Before writing tasks:** Claude Code should first check whether it can actually perform
the task itself (via MCP tools, CLI, or Fastlane). Only write tasks to the file that
genuinely require human hands.

**File format:**

```markdown
# Manual Tasks

> Auto-generated by Claude Code. Check off items as you complete them.
> Delete this file or clear all items when everything is done.

## From session: [date] — [brief description of what was worked on]

- [ ] Task 1 — specific, actionable instruction
- [ ] Task 2 — include exact navigation paths (e.g. "ASC → App Information → App Privacy")
- [ ] Task 3 — include any values to enter (e.g. "set price to $14.99/year")
```

**Rules for writing tasks:**
- Be specific — include exact navigation paths, field names, and values
- Group by destination (all ASC tasks together, all Developer Portal tasks together)
- If a task has a prerequisite, note it (e.g. "Do after Task 2 — needs the profile name")
- New sessions append to the file under a new date heading; don't overwrite previous tasks
- If all tasks from a previous session are done, Claude Code can remove that section

**At session start:** Check if `MANUAL-TASKS.md` exists with uncompleted items. Ask the
user if they've completed them before proceeding with work that depends on those tasks.

**This file is gitignored** — add `MANUAL-TASKS.md` to `.gitignore`. It's a local
scratchpad, not project documentation.

---

## Work Log Rule

`WORKLOG.md` is a **gitignored local scratchpad** that tracks work session-by-session in
reverse chronological order. CLAUDE.md is the reference doc (rarely changes); WORKLOG.md
is the session diary (changes every session).

**Why:** When returning to a project after days or weeks, Claude Code reads the worklog
and resumes work contextually — decisions, blockers, and what changed are all there
without re-reading the entire codebase or git history.

**At session end:** Append a new entry at the top (below the header) with this format:

```markdown
## [DATE] — [Brief description of session focus]

**What changed:**
- [Bullet points of changes made — files, features, fixes]

**Decisions:**
- [Key decisions and rationale — why this approach, what was deferred]

**Blockers:**
- [Open issues, things needing human action, or next-session priorities]
- None. [if nothing is blocked]
```

**Rules:**
- Entries are reverse-chronological (newest first)
- Be specific about files and features changed — future sessions use this to orient
- Record decisions and their rationale — this prevents re-litigating settled questions
- Note blockers even if minor — they become the next session's starting point
- When prior sprints accumulate, condense old entries into a summary section at the bottom
- This file is gitignored — it's a local scratchpad, not project documentation
