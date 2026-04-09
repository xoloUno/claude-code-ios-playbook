# CLAUDE.md — [APP_NAME]

This file is the single source of truth for every Claude Code session on this project.
Read it fully before writing any code or suggesting any architecture changes.

> **Reference:** For CI/CD setup, StoreKit 2 subscription setup, and App Store submission
> procedures, see `ios-project-playbook.md` in the `_playbook/` directory.
>
> **Operational rules** (git workflow, build/deploy, code style, WWDC25, session checklists,
> manual tasks, work log, session health) live in `.claude/rules/` and are loaded
> automatically by path glob. Do not duplicate them here.

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

## App Store Metadata (For Reference)

**App name:** [APP_NAME]
**Subtitle:** [30 char max]
**Bundle ID:** [com.example.appname]

**Target keywords:** [comma-separated keywords for ASO]

**Core value prop:** [One sentence for App Store description lead]

**Primary target audience:** [Who this app is for]
