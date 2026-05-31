---
description: Swift code style, conventions, and automated quality tooling
globs: **/*.swift
---

# Code Style & Conventions

- **Swift 6 strict concurrency** — `@MainActor` on view models, `async/await` everywhere
- **No third-party UI libraries** — SwiftUI only, system components only
- **ViewModels are `@Observable`** (not `ObservableObject`)
- **No force unwraps** — `guard let` / `if let`, handle all optionals
- **File naming** matches primary type (one type per file)
- **No comments explaining what** — only why (write self-documenting code)
- **Previews required** for every SwiftUI View
- **SwiftLint enforced** — `.swiftlint.yml` in project root. CI fails on violations.

# Automated Quality Tools

## Claude Code Hooks (`.claude/hooks.json`)

A PostToolUse hook runs SwiftLint after every file edit or creation. Unlike CLAUDE.md
instructions, hooks always fire. If SwiftLint reports issues, fix them before committing.

## Pre-Commit Hooks (Lefthook)

`lefthook.yml` runs three checks before every commit:
1. **SwiftLint** — lint all staged `.swift` files
2. **Gitleaks** — scan for accidentally committed secrets, API keys, tokens
3. **Conventional commit validation** — reject commit messages that don't match
   the `type(scope): description` format

These fire on `git commit`. Claude Code's commits go through the same hooks — no bypass.

## Claude Code Slash Commands (`.claude/commands/`)

| Command | What it does |
|---|---|
| `/status` | Session startup briefing — branch, state, flags, what's next |
| `/wrapup` | Session end — commit, update CLAUDE.md, WORKLOG, push |
| `/feature {name}` | Scaffolds View + ViewModel + Tests for a new feature |
| `/test {target}` | Generates Swift Testing tests with @Test macros |
| `/review` | Reviews staged changes for concurrency, accessibility, privacy |
| `/preflight` | Pre-deploy gate — validates simulators, ASC metadata, git state |
| `/deploy` | Builds, signs, and uploads to TestFlight from local machine |
| `/release` | Syncs metadata, builds, and uploads to App Store Connect |
| `/inbox {lesson}` | Logs a lesson learned to the shared playbook inbox |
| `/upgrade` | Syncs project with latest playbook changes via CHANGELOG |
| `/context-health` | Session hygiene gauge — uncommitted work, push status |

## Dependabot (`.github/dependabot.yml`)

Creates PRs for outdated SPM dependencies weekly. Review and merge them — don't let
dependencies go stale.
