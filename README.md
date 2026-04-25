# Claude Code iOS Playbook

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-iOS_26+-blue.svg)](https://developer.apple.com/ios/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-purple.svg)](https://docs.anthropic.com/en/docs/claude-code)

A complete operational playbook for building and shipping iOS apps as a solo indie
developer using [Claude Code](https://docs.anthropic.com/en/docs/claude-code). One
script bootstraps a full Xcode project with CI/CD, code signing, linting, pre-commit
hooks, and App Store submission pipeline — then Claude Code handles the day-to-day
development.

## Table of Contents

- [TL;DR](#tldr)
- [What this is](#what-this-is)
- [Who this is for](#who-this-is-for)
- [Files](#files)
- [Setup](#setup)
- [Tech stack](#tech-stack)

## TL;DR

1. Copy `.env.playbook.example` to `.env.playbook`, fill in your Apple Developer details (one-time)
2. Copy `.env.project.example` to `.env.project`, fill in `APP_NAME`, `BUNDLE_ID`, `REPO_NAME`, `MINIMUM_IOS` (per project)
3. Run `bash bootstrap.sh` from the parent directory where you want the project folder created
4. Open the project folder in Claude Code and start building

You get a production-ready Xcode project with GitHub Actions CI/CD, Fastlane for
TestFlight and App Store deployment, SwiftLint, Gitleaks, conventional commits,
and a `CLAUDE.md` that teaches Claude Code how to work in your project.

## What this is

This playbook is written for Claude Code to follow — every step is concrete, tested, and
copy-pasteable. It covers the full lifecycle:

- **Bootstrap** a new iOS project with one command
- **CI/CD** with GitHub Actions (build checks, TestFlight deploys, App Store releases)
- **Code signing** with manual provisioning profiles and Fastlane
- **StoreKit 2** subscription setup
- **Development conventions** (Git workflow, Swift 6, SwiftUI patterns)
- **Feature scaffolding** (widgets, extensions, SPM dependencies)
- **CloudKit & Push Notifications** (gotchas, async init patterns)
- **Screenshot automation** for App Store submissions
- **App Store submission** checklist and common rejection fixes

## Who this is for

Solo indie iOS developers who want to ship apps efficiently with Claude Code as their
primary development tool. The playbook assumes:

- Apple Developer Program membership
- macOS with Xcode installed
- Basic familiarity with Terminal (you don't need to be a command-line expert)
- GitHub account

If you're brand new, start with `getting-started.md`.

## Files

| File | What it does |
|---|---|
| **`ios-project-playbook.md`** | The main playbook. Covers every phase from bootstrap to post-launch monitoring. This is what Claude Code reads to understand how your projects work. |
| **`bootstrap.sh`** | One-command project bootstrap script. Creates a full Xcode project, Fastlane config, GitHub Actions workflows, linting, hooks, legal templates, and pushes to GitHub. |
| **`getting-started.md`** | Step-by-step guide for first-time setup. Walks through prerequisites, creating your first project, and daily workflow. Start here if this is your first time. |
| **`CLAUDE-TEMPLATE.md`** | Template for per-project `CLAUDE.md` files. The bootstrap script uses this to generate each project's Claude Code configuration. |
| **`claude-code-plugins-setup.md`** | Guide for setting up Claude Code plugins and MCP servers for iOS development (XcodeBuildMCP, Apple's Xcode MCP bridge, etc.). |
| **`CHANGELOG.md`** | Documents playbook updates with upgrade instructions for existing projects. |
| **`.env.playbook.example`** | Template for your personal configuration (Team ID, ASC credentials, GitHub org). Copy to `.env.playbook` and fill in your values once. |
| **`.env.project.example`** | Template for per-project configuration (`APP_NAME`, `BUNDLE_ID`, `REPO_NAME`, `MINIMUM_IOS`). Copy to `.env.project` and edit before each new project. |

## Setup

### Prerequisites

- Xcode (with command line tools)
- Homebrew: `brew install xcodegen fastlane swiftlint lefthook gitleaks gh ruby`
- GitHub CLI authenticated: `gh auth login`
- Apple Developer Program membership

### Configuration (one-time)

```bash
cp .env.playbook.example .env.playbook
# Edit .env.playbook with your Apple Developer credentials (Team ID, ASC keys, GitHub org)
```

### Create your first project

```bash
# Per project: copy and edit .env.project (APP_NAME, BUNDLE_ID, REPO_NAME, MINIMUM_IOS)
cp .env.project.example .env.project
# Then run bootstrap from the parent directory where the project folder should land
bash bootstrap.sh
```

You never edit `bootstrap.sh` itself — both env files are loaded automatically.
The script hard-fails if `.env.project` is missing, so create it first.

The script prints manual steps you'll need to complete in the Apple Developer Portal
and App Store Connect (registering the bundle ID, creating a provisioning profile, etc.).
See `getting-started.md` for a detailed walkthrough with screenshots.

### Start developing

```bash
cd YourApp
claude
```

Claude Code reads your project's `CLAUDE.md` automatically and knows how to build,
test, lint, commit, and deploy.

## Tech stack

Every project created by this playbook uses:

- **Swift 6** with strict concurrency
- **SwiftUI** (no UIKit, no third-party UI libraries)
- **XcodeGen** for project generation (never edit `.pbxproj` manually)
- **Fastlane** for code signing, building, and uploading
- **GitHub Actions** for CI (build checks + automated deploys)
- **SwiftLint** + **Gitleaks** via Lefthook pre-commit hooks
- **Conventional Commits** enforced by commit-msg hook

## License

MIT
