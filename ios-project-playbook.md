# iOS Project Playbook

Master operational guide for solo indie iOS development. Covers the full lifecycle from
project creation to App Store submission. Written for Claude Code to follow — every step
is concrete, copy-pasteable, and tested.

**Last verified:** April 2026 (Xcode 26.3, macOS 26, GitHub Actions `macos-26` runners)

> **This repo is public.** Never hardcode real credentials, Team IDs, names, emails,
> domains, or org names. Use generic placeholders (`YOUR_TEAM_ID`, `com.example.*`,
> `you@example.com`, `YourOrg`). Real values belong in `.env.playbook` (gitignored).

## Table of Contents

- [Phase 0: Automated Project Bootstrap](#phase-0-automated-project-bootstrap)
- [Phase 1: CI/CD Pipeline Setup](#phase-1-cicd-pipeline-setup)
- [Phase 2: StoreKit 2 Subscriptions Setup](#phase-2-storekit-2-subscriptions-setup)
- [Phase 3: Development Conventions](#phase-3-development-conventions)
- [Phase 4: Adding Features & Extensions](#phase-4-adding-features--extensions)
- [Phase 5: Screenshot Workflow](#phase-5-screenshot-workflow)
- [Phase 6: App Store Submission](#phase-6-app-store-submission)
- [ASC Field Location Cheat Sheet](#asc-field-location-cheat-sheet)
- [Phase 7: Post-Launch Monitoring](#phase-7-post-launch-monitoring-add-when-app-is-live)
- [Appendix A: Why These Tools](#appendix-a-why-these-tools)
- [Appendix B: Decision Trees](#appendix-b-decision-trees)
- [Appendix C: Migrating an Existing Project to the Playbook](#appendix-c-migrating-an-existing-project-to-the-playbook)
- [Appendix D: Maintaining the Playbook](#appendix-d-maintaining-the-playbook)
- [Appendix E: Glossary](#appendix-e-glossary)

---

## Phase 0: Automated Project Bootstrap

### 0.1 Prerequisites (one-time setup, already done)

- Apple Developer Program membership ($99/year) — active
- Xcode 26 installed with command line tools
- Homebrew installed (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- Homebrew Ruby installed (`brew install ruby`) — macOS system Ruby (2.6) cannot run modern bundler; Homebrew Ruby (4.x) is required for `bundle exec fastlane`
- XcodeGen installed (`brew install xcodegen`)
- Fastlane installed (`brew install fastlane`)
- SwiftLint installed (`brew install swiftlint`)
- Lefthook installed (`brew install lefthook`)
- Gitleaks installed (`brew install gitleaks`)
- GitHub CLI installed (`brew install gh`) and authenticated (`gh auth login`)
- Team ID: `YOUR_TEAM_ID` (set in `.env.playbook`)
- Developer: Your Name / you@example.com / domain: example.com

### 0.2 One-Command Project Bootstrap

Run `bootstrap.sh` from the parent directory where you want the project folder
created. Configuration lives in two env files — `bootstrap.sh` itself is never
edited.

```bash
# One-time per machine: identity + Apple Developer credentials
cp _playbook/.env.playbook.example _playbook/.env.playbook
# Per project: app name, bundle ID, repo name, deployment target
cp _playbook/.env.project.example _playbook/.env.project
# Edit both, then from the parent directory:
bash '_playbook/bootstrap.sh'
```

> **`.env.playbook`** holds values that stay the same across projects:
> `TEAM_ID`, `ORG` (GitHub), and ASC API credentials.
>
> **`.env.project`** holds the per-project values you change for each new app:
> `APP_NAME`, `BUNDLE_ID`, `REPO_NAME`, `MINIMUM_IOS`.
>
> The script hard-fails with `❌ No .env.project found` if the project file is
> missing, so create it before running.

**What the script creates:**
- XcodeGen `project.yml` (single source of truth — never edit .pbxproj manually)
- Compilable SwiftUI app with entry point and ContentView
- Asset catalog with icon placeholder
- `PrivacyInfo.xcprivacy` privacy manifest (pre-filled with UserDefaults reason)
- Fastlane with `beta` and `release` lanes
- Two GitHub Actions workflows (Build Check with SwiftLint + TestFlight Deploy)
- Dependabot config for automatic SPM dependency update PRs
- SwiftLint config (`.swiftlint.yml`)
- Lefthook pre-commit hooks (SwiftLint, Gitleaks, conventional commit validation)
- Claude Code hooks (auto-lint on every file edit)
- Claude Code slash commands (`/feature`, `/test`, `/review`)
- Legal doc templates for GitHub Pages hosting
- Fastlane metadata directory for future automation
- Release notes draft file
- Proper .gitignore

**What it does NOT do (manual steps):**
- Register the bundle ID in the Apple Developer Portal
- Create the app in App Store Connect
- Create the provisioning profile
- Add GitHub Secrets
- Fill in project-specific sections of CLAUDE.md (core problem, tech stack, UI direction, etc.)
- Install Lefthook and Gitleaks if not already installed (`brew install lefthook gitleaks`)

---

## Phase 1: CI/CD Pipeline Setup

### 1.1 Apple Developer Portal — Certificate & Profile

**Distribution certificate (one-time, shared across all apps):**

If you already have an Apple Distribution certificate exported as `.p12` and base64-encoded,
skip to 1.2. Otherwise:

1. [developer.apple.com/account/resources/certificates](https://developer.apple.com/account/resources/certificates) → **+** → **Apple Distribution**
2. Follow the CSR process → download the certificate
3. Open **Keychain Access** → find the cert under "My Certificates"
4. Right-click → Export as `.p12` → set a password
5. Base64 encode: `base64 -i YourCert.p12 | pbcopy`

**Provisioning profile (one per app):**

1. [developer.apple.com/account/resources/profiles](https://developer.apple.com/account/resources/profiles) → **+**
2. Distribution → **App Store Connect** → select your bundle ID → select your distribution certificate
3. Name it exactly: `"AppName App Store"` (this name is referenced in Fastlane)
4. Download and base64 encode: `base64 -i AppName_App_Store.mobileprovision | pbcopy`

### 1.2 App Store Connect API Key (one-time, shared across all apps)

If you already have an ASC API key, skip to 1.3.

1. [appstoreconnect.apple.com/access/integrations/api](https://appstoreconnect.apple.com/access/integrations/api) → **+**
2. Name: "GitHub Actions", Role: **App Manager** or **Admin**
3. Download the `.p8` file (one-time download)
4. Note the **Key ID** and **Issuer ID**

### 1.3 GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions** and add:

| Secret | Value | Shared across apps? |
|---|---|---|
| `APP_STORE_CONNECT_API_KEY` | Raw `.p8` file contents | Yes |
| `ASC_KEY_ID` | API Key ID | Yes |
| `ASC_ISSUER_ID` | Issuer ID | Yes |
| `CERTIFICATE_P12` | Base64-encoded `.p12` | Yes |
| `CERTIFICATE_PASSWORD` | `.p12` export password | Yes |
| `PROVISIONING_PROFILE` | Base64-encoded `.mobileprovision` | **No — per app** |
| `PROVISIONING_PROFILE_NAME` | Exact name from portal (e.g. "MyApp App Store") | **No — per app** |

**Reuse tip:** The first five secrets are identical across all your apps. Only the provisioning
profile secrets change per app. Consider using GitHub Organization secrets for the shared ones.

### 1.4 How the CI/CD Works

| Workflow | Trigger | Purpose |
|---|---|---|
| **Build Check** | Push to any branch except `main` | Simulator compile check — catches errors in cloud sessions |
| **TestFlight Deploy** | Manual dispatch only (`workflow_dispatch`) | Emergency fallback — normally use `/deploy` locally |

**Local sessions deploy locally.** Use the `/deploy` slash command to build, sign, and
upload to TestFlight from your machine. This is faster than CI and costs zero GitHub
Actions credits. Local sessions should include `[skip ci]` in commit messages to skip
all workflows (they verify builds locally and deploy locally).

**Cloud sessions rely on Build Check.** Cloud sessions cannot build or deploy. They
must NOT include `[skip ci]` — the Build Check workflow is their only compilation
verification. Cloud sessions should never push to `main`.

**Triggering TestFlight from CLI:** If local Fastlane fails or you need to deploy
remotely, trigger the workflow manually: `gh workflow run testflight.yml`

**XcodeGen in CI:** Both workflows install XcodeGen and regenerate the project before
building. This prevents version drift between `project.yml` and the generated `.pbxproj`.

### 1.5 Troubleshooting CI/CD

| Error | Cause | Fix |
|---|---|---|
| `invalid curve name (OpenSSL)` | Wrong `.p8` key or Ruby OpenSSL 3.x issue | Verify correct key; try `brew install fastlane` instead of Bundler |
| `Could not find 'bundler' (4.x)` | macOS system Ruby (2.6) lacks modern bundler | Prepend Homebrew Ruby: `export PATH="/opt/homebrew/opt/ruby/bin:$PATH"` then retry |
| `invalid byte sequence in US-ASCII` | Fastlane gym crashes parsing build logs without UTF-8 locale | Set `export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8` before running fastlane |
| `No profiles for 'bundle.id'` | Profile not installed or name mismatch | `PROVISIONING_PROFILE_NAME` must match the portal name exactly |
| `Cloud signing permission error` | Using `-allowProvisioningUpdates` | Use manual signing via `update_code_signing_settings` |
| `Missing required icon file` | No 1024x1024 PNG in asset catalog | Add icon before first TestFlight upload |
| `Missing Info.plist CFBundleIconName` | Info.plist missing icon key | XcodeGen handles this — regenerate project |
| `Invalid bundle... orientations` | Missing iPad orientations | Already in bootstrap `project.yml` |
| App Store validation rejects alpha channel | Icon PNG has transparency | Strip with PIL (see Phase 6) |
| `gitleaks: command not found` in pre-commit | Claude Code sessions don't inherit full shell PATH | Use full Homebrew paths in `lefthook.yml` (see fix below) |

### 1.6 Local TestFlight Deploy Setup

Store your App Store Connect API key in a shared location (same key works across all apps):

The `.p8` key file is stored at `~/Documents/Xcode/AuthKey_YOUR_ASC_KEY_ID.p8` (shared
across all apps). If starting fresh, download the key from App Store Connect → Users
and Access → Integrations → App Store Connect API and save it there.

In each project root, create `.env.fastlane` (already gitignored via `.env.*`):

```
ASC_KEY_ID=YOUR_ASC_KEY_ID
ASC_ISSUER_ID=YOUR_ASC_ISSUER_ID
ASC_KEY_FILEPATH=~/Documents/Xcode/AuthKey_YOUR_ASC_KEY_ID.p8
```

These three values are identical across all apps — copy the same `.env.fastlane` into
each new project root. The `PROVISIONING_PROFILE_NAME` is not needed here because the
Fastfile handles signing configuration per-target.

Verify it works:

```bash
export PATH="/opt/homebrew/opt/ruby/bin:$PATH"
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
set -a && source .env.fastlane && set +a && bundle exec fastlane beta
```

The `PATH` export ensures Homebrew Ruby (4.x with bundler 4.x) is used instead of macOS
system Ruby (2.6). The `LC_ALL`/`LANG` exports prevent fastlane's gym error handler from
crashing with `invalid byte sequence in US-ASCII` when parsing build logs. Both are
required for every `bundle exec fastlane` invocation.

Once verified, use `/deploy` in Claude Code sessions for all future TestFlight uploads.
The GitHub Actions TestFlight workflow remains available via `gh workflow run testflight.yml`
for emergencies (e.g., local machine unavailable).

**Key gotchas learned the hard way:**

1. **Never use cloud-managed signing on CI** — manual signing with `update_code_signing_settings` is reliable. Cloud signing randomly fails on headless runners.
2. **Provisioning profile name must match in three places:** Apple Developer Portal, `update_code_signing_settings`, and `export_options.provisioningProfiles`. A mismatch in any one silently produces an unsigned build.
3. **After Xcode updates,** `xcodebuild` may fail with "failed to load a required plug-in" — run `xcodebuild -runFirstLaunch` to fix. Check Xcode → Settings → Components if you get "iOS X.X is not installed" errors.

---

## Phase 2: StoreKit 2 Subscriptions Setup

> **Why native?** As of March 2026, Apple's App Store Connect analytics include subscription
> cohort analysis, peer group benchmarks, and an Analytics Reports API — closing the gap that
> previously justified third-party wrappers. StoreKit 2 + `SubscriptionStoreView` handles
> purchases, paywall UI, and entitlement checking with zero dependencies.
>
> **Optional alternative:** If you need cross-platform subscriptions (iOS + Android) or
> server-side entitlement validation without building your own backend, consider
> [RevenueCat](https://www.revenuecat.com). For single-platform iOS apps, native is recommended.

### 2.1 App Store Connect — Subscription Products

**Step 0: Verify Paid Applications Agreement is active.**
App Store Connect → Business → Paid Applications must show **Active** (green). Without this,
no IAP works — not even in sandbox. This is the most common invisible blocker.

**Create subscription group:**
1. ASC → My Apps → your app → Subscriptions → **+** next to "Subscription Groups"
2. Name: e.g. "Premium" or "AppName Unlimited"
3. **Immediately add localization:** Click into group → "Subscription Group Localization" → **+** → select language → fill Display Name → Save. This is required but the UI never flags it as missing.

**Create products inside the group:**

| Product | Reference Name | Product ID | Duration |
|---|---|---|---|
| Annual | "Annual Subscription" | `your.bundle.id.annual` | 1 Year |
| Monthly | "Monthly Subscription" | `your.bundle.id.monthly` | 1 Month |

Product IDs are permanent and cannot be changed. For each product: set pricing (base country first, Apple auto-generates other regions) and add localization (display name + description).

Both products should show status **"Ready to Submit"**.

### 2.2 App Code Integration

**SubscriptionManager — listens for transaction updates and checks entitlements:**

```swift
import StoreKit

@MainActor
@Observable
final class SubscriptionManager {
    private(set) var isSubscribed = false
    private var updateTask: Task<Void, Never>?

    /// Product IDs — must match App Store Connect exactly
    static let productIDs: Set<String> = [
        "your.bundle.id.annual",
        "your.bundle.id.monthly"
    ]

    init() {
        updateTask = Task { [weak self] in
            for await result in Transaction.updates {
                if case .verified = result {
                    await self?.checkSubscription()
                }
            }
        }
        Task { await checkSubscription() }
    }

    func checkSubscription() async {
        var hasActive = false
        for await result in Transaction.currentEntitlements {
            if case .verified(let transaction) = result,
               transaction.productType == .autoRenewable,
               transaction.revocationDate == nil {
                hasActive = true
                break
            }
        }
        isSubscribed = hasActive
    }

    deinit { updateTask?.cancel() }
}
```

**Show paywall with `SubscriptionStoreView`:**

```swift
import StoreKit
import SwiftUI

struct PaywallView: View {
    @Environment(SubscriptionManager.self) private var subscriptionManager

    var body: some View {
        SubscriptionStoreView(groupID: "YOUR_SUBSCRIPTION_GROUP_ID") {
            // Optional marketing content above the product list
            VStack(spacing: 12) {
                Image(systemName: "star.fill")
                    .font(.largeTitle)
                Text("Unlock Everything")
                    .font(.title2.bold())
                Text("Get unlimited access to all features.")
                    .foregroundStyle(.secondary)
            }
            .padding()
        }
        .subscriptionStoreControlStyle(.prominentPicker)
        .storeButton(.visible, for: .restorePurchases)
        .onInAppPurchaseCompletion { _, result in
            if case .success(.success) = result {
                await subscriptionManager.checkSubscription()
            }
        }
    }
}
```

**Finding your Subscription Group ID:** In App Store Connect → your app → Subscriptions →
click your subscription group → the Group ID is shown in the group details (numeric string).
You can also find it in your StoreKit Configuration file.

**Wire it up in your App entry point:**

```swift
@main
struct YourApp: App {
    @State private var subscriptionManager = SubscriptionManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(subscriptionManager)
        }
    }
}
```

**Gate features on subscription status:**
`if subscriptionManager.isSubscribed { /* premium feature */ }`

### 2.3 StoreKit Configuration File (for Previews & Testing)

Create a StoreKit Configuration file for Xcode Previews and simulator testing without
needing a sandbox account:

1. File → New → File → StoreKit Configuration File
2. Add your subscription group and products (IDs must match ASC)
3. In your scheme: Edit Scheme → Run → Options → StoreKit Configuration → select the file
4. **CRITICAL:** Uncheck "StoreKit Configuration" for Release/Archive schemes — it overrides
   real App Store products

This gives you instant purchase testing in Previews and simulators without sandbox sign-in.

**XcodeGen users:** The `.storekit` file lives at the project root, outside your main
source directory. You must explicitly add it to your target's `sources:` in `project.yml`
or it won't appear in Xcode's project navigator or scheme options:
```yaml
targets:
  MyApp:
    sources:
      - path: MyApp
      - path: MyApp.storekit   # ← must be listed explicitly
```
Run `xcodegen generate` after adding this entry.

### 2.4 App Store Server Notifications (optional)

For most solo indie apps without a backend, server notifications are unnecessary — StoreKit 2's
`Transaction.updates` and `Transaction.currentEntitlements` handle everything client-side.

If you do have a backend that gates features on subscription status:
1. ASC → your app → App Information → App Store Server Notifications
2. Enter your server endpoint URL in **both** Production and Sandbox fields → Version 2
3. Implement the [App Store Server Notifications V2](https://developer.apple.com/documentation/appstoreservernotifications) listener

### 2.5 Common StoreKit 2 Pitfalls

| Problem | Cause | Fix |
|---|---|---|
| **Products not loading** | Paid Applications Agreement inactive | ASC → Business → accept agreement |
| **Products not loading** | Products not "Ready to Submit" | Ensure pricing + localization are set for each product in ASC |
| **`SubscriptionStoreView` empty** | Wrong subscription group ID | Use the numeric Group ID from ASC, not the group name |
| **Purchases work in sim but not TestFlight** | StoreKit Configuration still active in scheme | Uncheck it in Release/Archive scheme options |
| **`Transaction.currentEntitlements` empty after purchase** | Not awaiting the async sequence correctly | Use `for await` loop, not `.first` |
| **"Cannot connect to iTunes Store"** | Paid Applications Agreement inactive | Accept in ASC → Business |
| **Promotional offer not applying** | Missing JWS authentication | JWS is now required for promotional offers and introductory offer eligibility APIs (back-deployed to iOS 15). See Apple's [StoreKit updates](https://developer.apple.com/documentation/updates/storekit). |

> **New in iOS 26:** `SubscriptionOfferView` provides a built-in SwiftUI view for
> merchandising auto-renewable subscriptions. Check Apple Developer Documentation
> before building a custom offer UI.

### 2.6 Sandbox Testing

- TestFlight builds use Apple's sandbox automatically
- Sandbox subscriptions renew on accelerated schedule: 1 month = 5 min, 1 year = 1 hour
- Auto-renews up to 6 times then expires
- Create sandbox testers: ASC → Users and Access → Sandbox → Testers
- Sandbox account setting on device: Settings → Apple Account → scroll down → Sandbox Account
- Easiest: just attempt a purchase in TestFlight — iOS prompts for sandbox sign-in
- Use the StoreKit Configuration file (Section 2.3) for faster iteration during development

---

## Phase 3: Development Conventions

### 3.1 Git Workflow

```
main          ← always shippable; tagged on every submission
dev           ← active development; merges into main before submission
feature/*     ← one branch per feature
fix/*         ← one branch per bug fix
```

Never commit directly to `main`. Push to `dev` or feature branches. Merge to `main` only
when ready for TestFlight or App Store.

**Concurrent Claude Code sessions:** If you run multiple Claude Code sessions against the
same repo simultaneously, use **worktrees** (`/worktree` in Claude Code) to give each
session an isolated working directory. A branch alone only isolates commit history — the
files on disk are shared across all sessions using the same directory. Without worktrees,
one session's edits silently overwrite another's uncommitted work.

### 3.2 Commit Messages (Conventional Commits)

Format: `type(scope): short description`

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `ui`

Rules: subject ≤72 chars, present tense, no trailing period, `Co-Authored-By: Claude <noreply@anthropic.com>` trailer.

**Local sessions:** Include `[skip ci]` in commit message to skip all CI workflows.
Local sessions verify builds via XcodeBuildMCP and deploy via `/deploy` — no CI needed.
**Cloud sessions:** Do NOT include `[skip ci]` — Build Check must verify their code compiles.

**Gotcha — 72 char limit includes `[skip ci]`:** The Lefthook conventional commit regex
validates the full subject line including the `[skip ci]` suffix (11 chars). This leaves
only ~61 chars for `type(scope): description`. If the commit hook rejects your message, it's
almost always a length issue — shorten the description or move details to the commit body.

**Gotcha — scope is required by default regex:** The bootstrap `lefthook.yml` regex requires
a scope in parentheses: `type(scope): description`. A bare `docs: fix typo` will be rejected.
Always include a scope like `docs(legal): fix typo`.

### 3.3 Code Style

- Swift 6.2 strict concurrency (mandatory as of Xcode 26) — `@MainActor` on view models, `async/await` everywhere
- No third-party UI libraries — SwiftUI + system components only
- ViewModels use `@Observable` (not `ObservableObject`)
- No force unwraps — `guard let` / `if let` always
- File naming matches primary type
- No comments explaining what — only why
- Previews required for every SwiftUI View
- System adaptive colors throughout — never hardcode `Color.black` / `Color.white`
- Async init consumers re-verify preconditions — don't trust bootstrap state (see §4.4)

**SwiftLint gotcha — whitespace after code removal:** When deleting a code block (e.g.
removing a Section from a List), check for trailing blank lines before closing braces.
SwiftLint's `vertical_whitespace_closing_braces` rule will reject the commit if an empty
line sits before a `}`. Always clean up blank lines after removing code.

**Debugging gotcha — `print()` beats `Logger` for temporary diagnostics:** When Xcode's
console filter isn't surfacing your `Logger` categories (its filter is substring-based, not
a structured category filter), drop temporary `print("[TAG] …")` calls with a unique prefix.
Faster iteration than fighting Console.app's subsystem filters. Strip them in a follow-up
commit once the path is verified.

### 3.4 Swift 6.2 Concurrency Model

As of Xcode 26, strict concurrency is **mandatory** — data race safety is enforced by the
compiler, not opt-in. Key concepts:

- **`nonisolated(nonsending)` is the default.** Nonisolated async functions run on the
  caller's actor. A function called from `@MainActor` stays on `@MainActor` — no implicit
  hop to the cooperative pool. This eliminates the most common class of concurrency errors.
- **`@concurrent`** — use this annotation when a function should explicitly run off the
  caller's actor (e.g., CPU-heavy work that would block the main thread).
- **Approachable Concurrency** is enabled by default in new Xcode 26 projects. For existing
  projects, enable it incrementally — it changes runtime behavior (where code runs), not just
  compile-time diagnostics. Swift 6.2 provides migration fix-its.
- **`@MainActor` on view models** remains the correct pattern — the new defaults reinforce
  this by keeping downstream calls on MainActor automatically.

### 3.5 WWDC25 & iOS 26 Awareness

Claude Code's training predates WWDC25. Before writing code using any framework introduced
at or after WWDC25, search Apple Developer Documentation to verify current APIs.

Key changes: iOS version jumped 18 → 26 (skipped 19–25). Liquid Glass design system applies
automatically. SceneKit soft-deprecated. Metal 4 introduced. FoundationModels framework for
on-device AI. SF Symbols 7.

### 3.6 Cloud vs Local Session Capabilities

**Cloud sessions CAN:** Edit Swift files, commit/push, plan architecture, write features.

**Cloud sessions CANNOT:** Run `xcodebuild`, `fastlane`, test on Simulator, modify `.pbxproj`.
Defer Xcode project structure changes (new targets, entitlements) to local sessions.

---

## Phase 4: Adding Features & Extensions

### 4.1 Adding a Widget Extension

1. Add the target to `project.yml` (local session — requires XcodeGen regeneration)
2. Create the widget source directory with entry point
3. Add shared files (models, intents) with target membership in both targets
4. Add App Group capability if widget needs shared data
5. **Update fastlane and CI for multi-target signing** (see below)

#### Fastlane: Multi-Target Signing

The bootstrap Fastfile only signs the main app target. When you add an extension (widget,
share extension, etc.), you need a separate provisioning profile and a second
`update_code_signing_settings` call for each additional target.

**Fastfile changes** — add a second signing block per extension target:

```ruby
# Main app target (already in Fastfile)
update_code_signing_settings(
  use_automatic_signing: false,
  path: "YourApp.xcodeproj",
  team_id: CredentialsManager::AppfileConfig.try_fetch_value(:team_id),
  profile_name: ENV["PROVISIONING_PROFILE_NAME"],
  bundle_identifier: CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier),
  code_sign_identity: "Apple Distribution",
  targets: ["YourApp"]                      # ← add targets filter
)

# Extension target (add this)
update_code_signing_settings(
  use_automatic_signing: false,
  path: "YourApp.xcodeproj",
  team_id: CredentialsManager::AppfileConfig.try_fetch_value(:team_id),
  profile_name: "YourApp Widgets App Store", # ← separate profile for extension
  bundle_identifier: "com.example.yourapp.widgets",
  code_sign_identity: "Apple Distribution",
  targets: ["YourAppWidgets"]
)
```

Update `export_options` to include all bundle IDs:

```ruby
build_app(
  scheme: "YourApp",
  export_method: "app-store",
  export_options: {
    provisioningProfiles: {
      "com.example.yourapp" => ENV["PROVISIONING_PROFILE_NAME"],
      "com.example.yourapp.widgets" => "YourApp Widgets App Store"
    }
  }
)
```

Apply the same changes to both `beta` and `release` lanes.

#### CI: Multiple Provisioning Profiles

In `testflight.yml`, install each extension's profile as a separate file:

```yaml
- name: Install provisioning profiles
  env:
    PROVISIONING_PROFILE: ${{ secrets.PROVISIONING_PROFILE }}
    PROVISIONING_PROFILE_WIDGETS: ${{ secrets.PROVISIONING_PROFILE_WIDGETS }}
  run: |
    PROFILE_PATH=~/Library/MobileDevice/Provisioning\ Profiles
    mkdir -p "$PROFILE_PATH"
    echo -n "$PROVISIONING_PROFILE" | base64 --decode -o "$PROFILE_PATH/ci_profile.mobileprovision"
    echo -n "$PROVISIONING_PROFILE_WIDGETS" | base64 --decode -o "$PROFILE_PATH/ci_widgets_profile.mobileprovision"
```

Update the cleanup step to remove all profiles:

```yaml
- name: Clean up secrets
  if: always()
  run: |
    rm -f fastlane/AuthKey.p8
    rm -f ~/Library/MobileDevice/Provisioning\ Profiles/ci_profile.mobileprovision
    rm -f ~/Library/MobileDevice/Provisioning\ Profiles/ci_widgets_profile.mobileprovision
    KEYCHAIN_PATH=$RUNNER_TEMP/app-signing.keychain-db
    security delete-keychain "$KEYCHAIN_PATH" 2>/dev/null || true
```

**GitHub secrets needed per extension:**

| Secret | Value |
|---|---|
| `PROVISIONING_PROFILE_WIDGETS` | Base64-encoded `.mobileprovision` for the extension |

Create the extension's provisioning profile in Apple Developer Portal → Profiles using
the extension's bundle ID and the same distribution certificate.

#### Apple Developer Portal Checklist

For each extension target:
- [ ] Register the extension bundle ID (e.g. `com.example.yourapp.widgets`)
- [ ] Create a provisioning profile for it (App Store distribution)
- [ ] If using App Groups: register the group ID and enable on both app + extension bundle IDs
- [ ] Base64-encode the profile and add as a GitHub secret

### 4.2 Subscriptions (StoreKit 2)

StoreKit 2 is built into iOS — no SPM package needed. See Phase 2 for full setup.

> **If you need RevenueCat** (cross-platform or server-side entitlements), add to `project.yml`:
> ```yaml
> packages:
>   RevenueCat:
>     url: https://github.com/RevenueCat/purchases-ios
>     from: "5.0.0"
> ```
> And add `RevenueCat` + `RevenueCatUI` products to your target dependencies.

### 4.3 Adding Other SPM Dependencies

Same pattern — add under `packages` with version, add to target `dependencies`.

### 4.4 CloudKit & Push Notifications

CloudKit sync and silent push notifications for cross-device updates are commonly deployed
together. This section covers gotchas learned across multiple projects — not full setup.
Apple's CloudKit documentation covers the happy path; this is what it doesn't tell you.

#### Common CloudKit Pitfalls

| Problem | Cause | Fix |
|---|---|---|
| **"Invalid bundle ID for container"** on zone creation | Dev portal's container-to-bundle allowlist is stale | Dev portal → App ID → iCloud → Configure → **uncheck** the container → Save → wait 30 s → **re-check** → Save → download manual profiles in Xcode. This forces Apple's backend to regenerate the allowlist record. Not documented in Apple's official docs. |
| **Simulator CloudKit is flaky** (random failures, `cloudd` cache corruption) | Simulator's CloudKit stack is unreliable for development | Use a **physical device** for all CloudKit dev work. Plan for this from day one — don't waste hours debugging `cloudd` cache state on Simulator. |
| **Can't remove a field from Production schema** | CloudKit Production schemas are **append-only** | Do a dead-code audit on every synced model field **before** clicking Deploy Schema Changes. Dead fields in Production are permanent. |
| **`CKError.unknownItem` on first fetch** | Development env uses schema-on-write — a record type with zero saved records doesn't exist yet | Catch `.unknownItem` in any fetch-all-on-bootstrap code and treat it as an empty result set. Without this, first-ever bootstrap on a fresh container throws mid-pipeline. |
| **Push notifications broken in Debug builds** | `aps-environment` hardcoded to `production` in entitlements | Use `aps-environment: development` in source entitlements. Xcode automatically substitutes `production` at archive/distribution time. Hardcoding `production` breaks Debug + Simulator builds. |
| **`CKQuery` fails on encrypted-only record types** | `encryptedValues` fields cannot be indexed; `CKQuery` requires at least one queryable field | Use `recordZoneChanges(since: nil)` for initial fetch — it uses change tracking with no indexing requirement. Works in Development but silently breaks in Production otherwise. |

#### Sync Patterns

**Debounce pushes to prevent concurrent race conditions.** When multiple mutations happen in
quick succession (e.g., user starts a timer then sets severity), each `save()` triggers a
separate CloudKit push. With `savePolicy: .changedKeys` (last-writer-wins), a stale push can
complete last and overwrite the correct value. Fix: cancel-and-debounce — cancel any pending
push Task on each `save()`, wait 500ms for mutations to settle, then push final state once.

**Always implement three sync triggers.** `CKDatabaseSubscription` silent push notifications
are unreliable — Apple deprioritizes them on low battery, and TestFlight/Development builds
are flakier than Production. Never rely on push alone:

1. **Silent push** via `CKDatabaseSubscription` — primary trigger
2. **Polling fallback** — 15-second timer while app is in the foreground
3. **Pull-to-refresh** on all list views — user-initiated

The delta fetch (`recordZoneChanges` since last token) is cheap — it returns immediately if
nothing changed.

#### Self-Healing Async Init

When app bootstrap is async and can fail (CloudKit zone creation, StoreKit product fetch,
HealthKit authorization), downstream mutation paths should **re-verify preconditions**
rather than assume bootstrap succeeded. Concretely: a `push()` method should check
account status and ensure the zone exists before calling `modifyRecords`, not just call
`modifyRecords` blindly.

```swift
// Bad — assumes bootstrap always succeeded
func push(_ record: CKRecord) async throws {
    try await container.privateCloudDatabase.modifyRecords(saving: [record], deleting: [])
}

// Good — re-verifies preconditions on every call
func push(_ record: CKRecord) async throws {
    guard try await container.accountStatus() == .available else { return }
    try await ensureZoneExists()   // no-ops if already created
    try await container.privateCloudDatabase.modifyRecords(saving: [record], deleting: [])
}
```

> This pattern is how Flara survived signing into iCloud mid-launch on a fresh device —
> the first bootstrap failed (no account yet), but the first save self-healed by
> re-running the zone-creation check.

The same principle applies to any async capability: StoreKit product loading, HealthKit
authorization, CoreLocation permissions. If init can fail, don't trust that it succeeded.

### 4.5 Control Center Widget Intents (App Group Bridge)

If your app ships a Control Widget (`ControlWidgetButton`/`ControlWidgetToggle`)
backed by an `AppIntent`, do NOT return `OpensIntent(OpenURLIntent(...))` from the
intent. On iOS 26, the URL is silently dropped on the way back to the app —
`.onOpenURL` never fires. The `openAppWhenRun: true` flag still foregrounds the app,
but the payload is lost. (Home-screen widgets using `Link` / `.widgetURL` keep working
through the standard URL handler — leave those alone.)

**Reliable pattern: shared App Group UserDefaults bridge.**

1. The intent (running in the widget extension's process) writes the requested action
   to App Group UserDefaults — e.g. a `pendingAction` key with the payload + a
   timestamp.
2. The intent returns plain `.result()` (no `OpensIntent`) and relies on
   `openAppWhenRun: true` to foreground the app.
3. The app drains and clears the entry on `.task` (cold launch) and on
   `.onChange(of: scenePhase)` when active (warm launch). Atomic clear-on-read makes
   double-fire safe across both hooks.
4. Apply a freshness window (~30s) so a stale tap from hours ago doesn't produce a
   phantom action on a much later launch.

Put the bridge type in a shared SPM package so both the app target and the widget
extension import the same key constants without drift.

---

## Phase 5: Screenshot Workflow

Screenshots are required for App Store submission and are the single biggest factor in
conversion. This workflow handles the full pipeline: automated capture on simulators,
professional framing and design, and export at correct sizes.

### Required Device Sizes (blocks submission if missing)

Per [Apple's screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/),
ASC accepts only two submission sizes as of 2026 — and auto-scales them to every
smaller device category. Capture the top two, let Apple scale the rest.

| ASC Size Label | Simulator Device | Resolution | Required? |
|---|---|---|---|
| **iPhone 6.9"** | **iPhone 17 Pro Max** | **1320 × 2868** | **Yes** — or 6.5" as fallback |
| **iPad 13"** | **iPad Pro 13-inch (M5)** | **2064 × 2752** | **Yes** if app supports iPad |
| iPhone 6.5" | iPhone 14 Plus | 1284 × 2778 | Fallback only — required only if no 6.9" |
| iPhone 6.3" | iPhone 17 Pro | 1179 × 2556 | **Not accepted** — scaling target only |
| iPad Pro 11" | iPad Pro 11-inch | 1668 × 2388 | **Not accepted** — scaling target only |

**Important:** ASC auto-scales 6.9" submissions down to 6.5", 6.3", 6.1", and older
sizes. A 13" iPad submission auto-scales to 11" iPad. **iPhone 6.3" (1179×2556) and
iPad Pro 11" (1668×2388) are NOT accepted as submissions** — uploading only those
sizes blocks "Add for Review." Capture on iPhone 17 Pro Max and iPad Pro 13-inch
(M5); these are the only two simulators required.

**If you need iPhone 17 Pro or iPad Pro 11" specifically as your marketing frame**
(e.g., those are the devices most of your users have), capture on the larger
ASC-accepted simulator (17 Pro Max / iPad 13") and let Apple Frames CLI's
`--device "iPhone 17 Pro"` flag override the auto-detected bezel. The pixel
dimensions still meet ASC's required 6.9" / 13" submission sizes; only the
displayed frame changes.

Minimum 1 screenshot per required size. Upload 3–5 on the 6.9" primary for
marketing impact.

### Step 1: Automated Capture with Fastlane Snapshot

Fastlane `snapshot` drives UI Tests across multiple simulators concurrently. Write the
test once, capture every screen on every required device in one command.

**One-time setup:**

```bash
# Initialize snapshot (creates Snapfile + SnapshotHelper.swift)
cd your-project
fastlane snapshot init
```

Move `SnapshotHelper.swift` into your UI Test target.

**Snapfile** (in `fastlane/` directory):

```ruby
# Only the two ASC-accepted submission sizes — Apple auto-scales to everything smaller
devices([
  "iPhone 17 Pro Max",      # 6.9" — REQUIRED (1320×2868)
  "iPad Pro 13-inch (M5)"   # 13"  — REQUIRED if app supports iPad (2064×2752)
])

languages(["en-US"])

scheme("YourAppUITests")     # ← your UI test scheme name

output_directory("./fastlane/screenshots")
clear_previous_screenshots(true)

# Clean status bar (removes carrier, sets time to 9:41, full battery)
override_status_bar(true)

# Run simulators in parallel for speed
concurrent_simulators(true)
```

The `snapshot init` command generates a `ScreenshotTests.swift` template. Customize it
to navigate through your app's key screens, calling `snapshot("01_ScreenName")` at each.
Use `-FASTLANE_SNAPSHOT` launch argument to detect snapshot mode and load demo data.

```bash
# Capture all screenshots across all devices
bundle exec fastlane snapshot
```

After running, `fastlane/screenshots/` contains all raw PNGs organized by language
and device, plus an HTML summary page for review.

> **Quick alternative:** If you haven't set up UI Tests yet, XcodeBuildMCP can capture
> screenshots on demand during a Claude Code session — faster for one-off captures but
> doesn't scale like `snapshot`.

#### Reference: cleanest manual status-bar override

`override_status_bar(true)` in the Snapfile sets sensible defaults (9:41, full
signal, charged) but leaves the carrier name and 5G/LTE label visible. For
manual `simctl` runs (e.g., the `widget_screenshots` and `control_center_screenshot`
lanes — which the bootstrap installs with the full override), use:

```bash
xcrun simctl status_bar "<DEVICE>" override \
  --time "9:41" --dataNetwork hide \
  --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiMode active --wifiBars 3 \
  --operatorName ""
```

`--dataNetwork hide` is the one most projects miss — without it, the 5G/LTE
label takes width next to the cellular bars and pushes the Wi-Fi icon onto a
second row inside Control Center. `--operatorName ""` blanks the carrier text.
Use the same flags on iPad (where the default carrier label is "Carrier" even
though most iPads represent Wi-Fi-only).

> **Note:** `--time` only sets the *visible status-bar time/date display*, not
> the iOS system clock. Calendar widgets, the Lock Screen big date, and
> Notification Center all read from the system clock (which follows the host
> Mac). There is no public `simctl date` command. If a marketing-friendly date
> matters, change the host Mac's date or compose a layout without date-driven
> widgets — there is no simulator-only path as of iOS 26.

#### XCUITest tips that save reshoots

- **Prefer direct accessibility-identifier taps** over `press(forDuration:)` +
  contextMenu items in screenshot tests. Direct taps are faster and dramatically
  more reliable, especially when the underlying view uses SwiftUI's
  Button-inside-Button + `.contextMenu` composition.
- **Synchronously detect `-FASTLANE_SNAPSHOT` in any service that reads
  `UserDefaults` in `init()`** (theme manager, settings singleton, feature
  flags). SwiftUI evaluates the first body using whatever `init()` produced
  *before* any `.task` modifier runs, so XCUITest's snapshot can capture a
  frame using the persisted user value (e.g., dark mode) even when `.task`
  later corrects it. Belt-and-suspenders: also call
  `xcrun simctl ui <DEVICE> appearance light` (or `dark`) before
  `xcodebuild test` so the system appearance can't bleed through.

```swift
// In your ThemeManager / Settings / FeatureFlags init():
init() {
    let args = ProcessInfo.processInfo.arguments
    if args.contains("-FASTLANE_SNAPSHOT") {
        appearance = args.contains("-DARK_MODE") ? .dark : .light
        return  // skip the UserDefaults read
    }
    appearance = AppAppearance(rawValue: UserDefaults.standard.string(forKey: "appearance") ?? "") ?? .system
}
```

### Step 2: Frame Screenshots

Raw simulator screenshots won't convert users. Two tracks — pick based on how much
marketing polish you need.

#### Track A — Apple Frames CLI (recommended default)

Federico Viticci's [Apple Frames CLI](https://github.com/viticci/frames-cli) applies
the MacStories Apple Frames 4 device bezels from the command line. Free, open source,
agent-friendly (`--json` mode + `FRAMES_ASSETS` env var), no Shortcuts.app dependency
— it downloads its own asset pack (~40 MB) on first run.

**One-time install:**

```bash
git clone https://github.com/viticci/frames-cli.git
cd frames-cli && pip3 install Pillow
mkdir -p ~/.local/bin
ln -s "$(pwd)/frames" ~/.local/bin/frames
frames setup          # downloads Apple Frames 4 assets from cdn.macstories.net
```

Ensure `~/.local/bin` is in your `PATH`. Verify with `frames --version`.

**Optional Claude Code skill:** The repo ships a skill at `skill/SKILL.md`. Install
once to `~/.claude/skills/frames-cli/SKILL.md` so Claude Code sessions have native
awareness of flags and batch patterns.

**Framing is automatic.** The bootstrapped `screenshots` lane calls `frame_screenshots`
at the end, so `bundle exec fastlane screenshots` captures and frames in one command.
Framed files land alongside the raw ones with a `_framed.png` suffix. To run framing
standalone against already-captured screenshots: `bundle exec fastlane frame_screenshots`.

**Manual invocation (without Fastlane):**

```bash
for dir in fastlane/screenshots/en-US/*/; do
  frames -o "$dir" "$dir"*.png
done
```

Delete raw PNGs before uploading, or use a separate output directory and point
`deliver` there.

**Device detection note:** The CLI auto-detects from pixel dimensions and picks the
newest frame matching the resolution. A 1320×2868 screenshot (captured on iPhone
17 Pro Max) auto-frames as iPhone 17 Pro Max — no mismatch, native 6.9" frame.
A 2064×2752 iPad screenshot auto-frames as the matching iPad Pro 13" model.

**Useful flags:**
- `--color "Cosmic Orange"` / `-c random` — brand-matched or varied frame colors
- `-b 3` — merge in batches (e.g., 15 shots → 5 merged panoramas)
- `--json` — machine-readable output for pipelines
- `frames list` / `frames info screenshot.png` — inspect supported devices and detect what a file is

#### Track B — appshot-cli + Apple Frames CLI (when you need captions + backgrounds)

Apple Frames CLI only applies device bezels — no captions, no branded backgrounds.
For marketing screenshots with captions, gradient backgrounds, and multi-locale
support, layer **[appshot-cli](https://www.npmjs.com/package/appshot-cli)** on
top of Apple Frames CLI. Every web-based mockup tool we tried (AppMockUp,
AppDrift, AppLaunchpad) is too janky to recommend; appshot-cli is the only
CLI option that's actually agent-friendly and reproducible.

The pipeline is two CLIs in sequence:

```
raw simctl/UITest PNGs
        ↓ frames CLI            (Track A — adds device bezels)
framed PNGs (e.g. with iPhone 17 Pro Max bezel)
        ↓ appshot build --no-frame   (adds caption + gradient + multi-locale)
final marketing PNGs
        ↓ deliver
App Store Connect
```

**One-time install:**

```bash
npm install -g appshot-cli
./scripts/patch-appshot.sh   # bootstrap-emitted; tunes caption font sizes
```

The patch step is required because appshot v2 hard-caps caption font size at
86px (iPhone) / 88px (iPad), which is too small to read at App Store thumbnail
size and too small to force readable line wraps. The bootstrap-emitted patch
script (`scripts/patch-appshot.sh`) bumps these to 115/130 by default — tune
to your design with `APPSHOT_IPHONE_FONT=120 APPSHOT_IPAD_FONT=140 ./scripts/patch-appshot.sh`.

> **Re-run the patch after any `npm install -g appshot-cli` upgrade** — the
> patches live inside `node_modules/appshot-cli/dist/...` and a fresh install
> silently clobbers them.

**Project layout (bootstrap-emitted):**

```
fastlane/appshot/
├── .appshot/
│   ├── config.json              ← gradient, font, layout — TUNE THIS
│   └── captions/
│       ├── iphone.json          ← {filename: {lang: caption}}
│       └── ipad.json
├── screenshots/                 ← (gitignored) staged input PNGs per device
│   ├── iphone/
│   └── ipad/
└── final/                       ← (gitignored) appshot output, copied to fastlane/screenshots/
    ├── iphone/
    └── ipad/
```

**Tune `.appshot/config.json` per project.** The starter has a sunset
gradient (`#FF5F6D → #FFC371`) and "New York Small Bold" font. Swap for your
brand colors and font:

```json
{
  "version": 2,
  "layout": "footer",
  "caption": {
    "font": "New York Small Bold",
    "color": "#1B1B1B"
  },
  "background": {
    "mode": "gradient",
    "gradient": {
      "colors": ["#FF5F6D", "#FFC371"],
      "direction": "top-bottom"
    }
  },
  "devices": {
    "iphone": { "input": "./screenshots/iphone", "resolution": "1320x2868" },
    "ipad":   { "input": "./screenshots/ipad",   "resolution": "2064x2752" }
  },
  "output": "./final"
}
```

> **Caption font naming gotcha.** appshot's `parseFontName` only recognizes
> the literal suffixes `Bold` and `Italic`. To get the bold weight of a
> macOS optical-size variant (e.g. New York Small, New York Medium), the
> font name has to literally end in `Bold` so the parser strips the suffix
> and sets SVG `font-weight=700`. Apple's font license explicitly permits
> SF Pro and the New York family for marketing materials about Apple-platform
> apps; both work well. If you want a custom font, install it system-wide and
> reference it by family-name + `Bold` suffix.

**Fill `.appshot/captions/{iphone,ipad}.json` with one entry per screenshot
filename, with one key per language code:**

```json
{
  "01_HomeScreen.png": {
    "en": "Track everything in one tap",
    "es": "Registra todo con un toque"
  },
  "02_KeyFeature.png": {
    "en": "Privacy-first by design",
    "es": "Privacidad ante todo"
  }
}
```

**Run the pipeline:**

```bash
# 1. Capture + frame (Track A)
bundle exec fastlane screenshots

# 2. Caption with appshot (per locale)
bundle exec fastlane appshot_screenshots                           # default en-US/en
bundle exec fastlane appshot_screenshots locale:es-ES lang:es      # Spanish locale

# 3. Upload
bundle exec fastlane upload_screenshots
```

The `appshot_screenshots` lane stages framed PNGs from
`fastlane/screenshots/{locale}/` into `fastlane/appshot/screenshots/`,
runs `appshot build --langs <lang>`, then copies the captioned output back
into the deliver dirs. For multi-locale projects, call the lane once per
locale.

> **Raw preservation is automatic.** The bootstrapped `frame_screenshots`
> lane snapshots all raw (unframed) captures into `fastlane/screenshots/{locale}/<device>/raw/`
> the first time it runs, *before* invoking the `frames` CLI. This means you
> can re-frame with a different bezel color (`frames --color "Deep Blue"`) or
> re-caption with new copy *without re-capturing* — the raw PNGs are still
> there. The `_framed.png` siblings (Apple Frames CLI's default output naming)
> additionally preserve the post-frame state, so re-captioning alone is
> already cheap. If the lesson "we forgot to keep raws" hits you mid-cycle,
> the raws are already saved.

**Multi-locale tip — share captions across regional variants.** If your app
ships `es-ES` and `es-MX` with effectively-identical Spanish captions, point
both at the same `lang: es` build. iOS's Spanish localization is shared, so
the marginal `Localizable.xcstrings` overrides for `es-MX` rarely produce
visibly different marketing screenshots. Saves capture time without hurting
ASC submission quality.

**Design tips that apply regardless of tool:** Lead with your core value
prop, not settings. First 2–3 screenshots are a mini-story. Use large
readable captions (visible at thumbnail size). Real in-app UI inside device
frames — Apple rejects pure marketing mockups.

### Step 2.5: Lock Screen (Live Activity) & Home Screen (Widget) Capture

Fastlane `snapshot` drives UI tests — it can't reach the lock screen or home screen
because those are SpringBoard, not your app. For Live Activity and widget marketing
shots, use the `widget_screenshots` lane (bootstrap.sh installs it and a companion
`fastlane/capture_widgets.sh` helper).

**What it does:**
1. Boots the target simulator and overrides the status bar (9:41, full signal).
2. Launches your app with `-WIDGET_DEMO_MODE YES` so you can auto-start a Live
   Activity in a deterministic state (wire this launch-arg check in your
   `@main` app struct — start an `ActivityKit` activity with canned demo data).
3. Locks the simulator via Cmd+L (AppleScript → Simulator.app), captures the
   lock screen — the Live Activity is visible.
4. Unlocks, goes home, captures the home screen with your widget.
5. Optionally chains `frame_screenshots` to apply Apple Frames.

**One-time manual setup per simulator:**

Add the home-screen widget **once** via the simulator UI — long-press the home
screen → `+` → find your widget → Add. This state persists in the simulator's
`CoreSimulator` data container across boots and across `bundle exec fastlane` runs,
so you only do it once per simulator device.

> **⚠️ Never `xcrun simctl uninstall <DEVICE> <BUNDLE_ID>` in a capture pipeline.**
> Uninstall removes the app **and all of its extensions/widgets** — wiping the
> user's manual placements of home-screen widgets, Lock Screen Live Activity
> widget, and Control Center widget. Reinstalling does NOT bring those layouts
> back. To neutralize persisted UserDefaults during snapshot mode, use launch-arg
> detection in app code (`init()` reads `-FASTLANE_SNAPSHOT`) — see the
> "XCUITest tips that save reshoots" subsection above. Uninstall as a clean-state
> shortcut costs 5–15 minutes of widget rearrangement to undo.

For Live Activities, no manual setup is needed — the script triggers the activity
via launch argument. Your app needs to honor it:

```swift
// In your @main App or AppDelegate
if CommandLine.arguments.contains("-WIDGET_DEMO_MODE") {
  Task { await LiveActivityDemoSeeder.start() }   // your seeder
}
```

**Usage:**

```bash
# Default: iPhone 17 Pro Max → fastlane/screenshots/en-US/iPhone 6.9" Display/
bundle exec fastlane widget_screenshots

# Override device or skip auto-framing
bundle exec fastlane widget_screenshots device:"iPhone 17 Pro Max" frame:false
```

**Output files:**
- `90_LockScreen_LiveActivity.png` — full-resolution lock screen with Live Activity
- `91_HomeScreen_Widget.png` — full-resolution home screen with widget

Both land in the `iPhone 6.9" Display` directory by default, so `deliver` uploads
them alongside the regular screenshots. The `9x_` prefix sorts them after your
main in-app screens; rename to reorder.

**Limitations:**
- Simulator must be in the foreground during the AppleScript `keystroke` calls.
  Don't run this on a machine where you're actively working — it'll steal focus.
- Dynamic Island screenshots aren't supported by `simctl screenshot` (the
  Dynamic Island is a compositor overlay, not part of the captured frame on
  current simulators). Capture those on a real device via QuickTime screen
  mirroring + screenshot.
- StandBy mode screenshots require a real device charging in landscape — no
  simulator path as of iOS 26.

### Step 2.6: Control Center Capture (Control Widget apps only)

If your app ships a **Control Widget** (`ControlWidgetButton` / `ControlWidgetToggle`
via ControlKit, iOS 18+), a Control Center screenshot showing your widget is
App Store-worthy marketing. If not, skip this step — Control Center with only
iOS defaults shows nothing app-specific.

> **⚠️ Place your Control Widget into Control Center once, manually, then keep it
> there.** Add the widget via the simulator UI (long-press Control Center → `+` →
> add your control). Same warning as §2.5: do **not** `xcrun simctl uninstall` the
> app between captures — uninstall removes the Control Center placement (and the
> home-screen widget, and the Lock Screen Live Activity widget) and reinstall does
> not bring them back.

The `control_center_screenshot` lane drives a synthetic mouse swipe via an
inline Swift script that calls `CGEvent.post(tap:)` on CoreGraphics — Swift
ships with Xcode Command Line Tools, no extra dep. Control Center has no
keyboard shortcut in Simulator.app, so keystroke automation can't reach it.

**One-time prerequisite — Accessibility permission:**

Sending synthesized mouse events to another app requires Accessibility
permission. The first time you run the lane, macOS will prompt — or silently
refuse and the swipe will do nothing. Grant your terminal app access:

> **System Settings → Privacy & Security → Accessibility →** enable
> **Terminal** (or **iTerm**, whichever you run `fastlane` from).

This is a one-time grant per terminal app. Without it, the script runs without
errors but Control Center stays closed.

**Usage:**

```bash
# Default: iPhone 17 Pro Max → fastlane/screenshots/en-US/iPhone 6.9" Display/
bundle exec fastlane control_center_screenshot

# Override device or skip auto-framing
bundle exec fastlane control_center_screenshot device:"iPad Pro 13-inch (M5)" frame:false
```

**How it works:**
1. Boots the simulator, overrides the status bar.
2. Sends Cmd+Shift+H to ensure SpringBoard is foregrounded.
3. Reads the Simulator.app window's screen position via AppleScript.
4. Inlines a Swift script (run via `swift -`) that calls
   `CGEvent(mouseEventSource:mouseType:…).post(tap: .cghidEventTap)` for a
   25-step mouse drag from the top-right corner of the simulated screen
   down ~600 points, simulating a user swiping Control Center open.
5. Captures via `xcrun simctl io ... screenshot` once Control Center has
   settled (~1.5s).
6. Dismisses with Cmd+Shift+H and chains `frame_screenshots` unless
   `frame:false` is passed.

**Output file:** `92_ControlCenter.png` in the `iPhone 6.9" Display` directory.

**Troubleshooting:**

| Symptom | Cause | Fix |
|---|---|---|
| Lane runs cleanly, but the screenshot is just the home screen | Terminal lacks Accessibility permission | Grant it in System Settings (above), re-run |
| `Simulator window: 0,0  0×0` in the log | Simulator.app wasn't frontmost when the AppleScript queried | Click the Simulator window once, then re-run |
| Control Center opens but is partially off-screen | Simulator window dragged below the screen edge | Move the Simulator window fully on-screen, re-run |
| Works on iPhone, fails on iPad | iPad Control Center has the same gesture but from a slightly different origin — script's `WIN_W - 40` offset works for both, but verify | If iPad fails, increase the offset to `WIN_W - 60` in `capture_control_center.sh` |

**Why not XCUITest?** UI tests *can* drive SpringBoard via
`XCUIApplication(bundleIdentifier: "com.apple.springboard")` and would be
cleaner long-term, but they require your project to already have the snapshot
UI test target wired up. The Swift+CoreGraphics path runs the moment
`bootstrap.sh` finishes — no UI test setup needed.

### Step 3: Export and Upload

Export from your design tool at the exact required resolutions. Then either:

**Manual upload:** Drag and drop into ASC on the version page. Upload 3–5 for
your primary 6.3" size, then 1 each for 6.5" and iPad 13".

**Automated upload via Fastlane deliver:**

```ruby
lane :upload_screenshots do
  deliver(
    skip_binary_upload: true,
    skip_metadata: true,
    overwrite_screenshots: true,
    screenshots_path: "./fastlane/screenshots"
  )
end
```

```bash
bundle exec fastlane upload_screenshots
```

This uploads all screenshots in the correct directories to ASC automatically. The
directory structure must match Fastlane's expected format:

```
fastlane/screenshots/en-US/
├── iPhone 6.3" Display/
│   ├── 01_HomeScreen.png
│   ├── 02_KeyFeature.png
│   └── 03_DetailView.png
├── iPhone 6.5" Display/
│   └── 01_HomeScreen.png
└── iPad 13" Display/
    └── 01_HomeScreen.png
```

### Recommended Workflow by Project Stage

| Stage | Capture | Frame | Caption / Background | Upload |
|---|---|---|---|---|
| **First app / v1 launch** | Manual on 2 simulators (or XcodeBuildMCP) | Apple Frames CLI | None — bare bezels are fine | Manual in ASC |
| **Second app onward** | Fastlane `snapshot` | `fastlane frame_screenshots` | None | Fastlane `deliver` |
| **Marketing-heavy app** | Fastlane `snapshot` | `fastlane frame_screenshots` | `fastlane appshot_screenshots` (per locale) | Fastlane `deliver` |

Don't over-engineer this on your first app. Raw capture + Apple Frames CLI gets
you professional framed screenshots in under 5 minutes. Add appshot captions and
branded gradients later when you need marketing polish.

---

## Phase 6: App Store Submission

> **Note:** Many steps in this phase require human action in App Store Connect or the
> Apple Developer Portal. When Claude Code is guiding you
> through submission, it will write remaining manual steps to `MANUAL-TASKS.md` in your
> project root so you have a persistent checklist that survives across sessions.
> See the CLAUDE.md template's "Manual Tasks Handoff Rule" for details.

### 6.1 Pre-Submission Checklist

**Legal & Hosting:**
- [ ] Privacy policy finalized in `docs/privacy.html` — all placeholders replaced
- [ ] Terms of service finalized in `docs/terms.html`
- [ ] GitHub Pages enabled (repo Settings → Pages → main branch, /docs folder)
- [ ] Both URLs verified accessible

**App Store Connect:**
- [ ] App record exists (name, bundle ID, SKU)
- [ ] Categories set (primary + secondary)
- [ ] Age rating questionnaire completed
- [ ] App Privacy questionnaire completed and published
- [ ] Privacy Policy URL entered (only appears AFTER publishing privacy questionnaire)
- [ ] Support URL entered
- [ ] Copyright filled (e.g. "2026 Your Name")
- [ ] Pricing set to **Free** (even with IAP subscriptions)
- [ ] Content Rights answered ("No" if no third-party content)

**App Store Metadata (on version page):**
- [ ] Name (30 char max)
- [ ] Subtitle (30 char max)
- [ ] Promotional Text (170 char max)
- [ ] Description (4000 char max)
- [ ] Keywords (100 char max, comma-separated, no spaces after commas)
- [ ] What's New / Release Notes
- [ ] Screenshots for ALL required sizes (see below)

**Subscription apps — required by Guideline 3.1.2(c):**
- [ ] EULA: either select Apple's Standard License Agreement in ASC (App Information →
  License Agreement), or upload a custom EULA
- [ ] App Store description includes functional links to Privacy Policy and Terms of Use (EULA)
- [ ] In-app purchase flow displays: subscription title, length, price, and links to
  Privacy Policy and Terms of Use. `SubscriptionStoreView` handles title, length, and
  price automatically. Add Terms/Privacy URLs via the subscription group's App Store
  localization in ASC, or use `.subscriptionStoreControlStyle()` modifiers.

**HealthKit apps — required by Guideline 2.5.1:**
- [ ] App UI clearly identifies HealthKit functionality (not just in code — the reviewer
  must see "Apple Health" mentioned visibly in the UI, e.g. settings screen, onboarding,
  or save confirmation buttons)

**Required Screenshot Sizes (blocks submission if missing):**

| Size | Simulator | Resolution | Required? |
|---|---|---|---|
| iPhone 6.9" | **iPhone 17 Pro Max** | 1320 × 2868 | **Yes** — or 6.5" as fallback |
| iPad 13" | **iPad Pro 13-inch (M5)** | 2064 × 2752 | **Yes** if app supports iPad |
| iPhone 6.5" | iPhone 14 Plus | 1284 × 2778 | Fallback only — required if no 6.9" |
| iPhone 6.3" | iPhone 17 Pro | 1179 × 2556 | **Not accepted** — scaling target only |
| iPad Pro 11" | iPad Pro 11-inch | 1668 × 2388 | **Not accepted** — scaling target only |

Upload 6.9" + 13" iPad — ASC auto-scales these down to every smaller device.
Uploading only 6.3" or 11" blocks "Add for Review." See **Phase 5: Screenshot
Workflow** for the full capture-and-design pipeline.

**Build & Code:**
- [ ] `MARKETING_VERSION` set to `1.0.0` in `project.yml`
- [ ] App icon: 1024×1024 PNG, **no alpha channel**, in asset catalog
- [ ] `ITSAppUsesNonExemptEncryption` = false (already in bootstrap project.yml)
- [ ] All `#if DEBUG` gates verified — no test code in Release
- [ ] No hardcoded test API keys in Release

**Strip icon alpha channel:**
```python
from PIL import Image
img = Image.open('AppIcon.png')
bg = Image.new('RGB', img.size, (255, 255, 255))
bg.paste(img, mask=img.split()[3])
bg.save('AppIcon.png', 'PNG')
```

### 6.2 App Privacy Questionnaire Guidance

**Apps with native StoreKit 2 subscriptions + HealthKit (no third-party analytics):**
- Collect data? **Yes**
- Select: Health (HealthKit)
- Linked to identity? **No**. Used for tracking? **No**. Purpose: **App Functionality**
- Note: Native StoreKit 2 doesn't send purchase data to third parties, so Purchase History
  and Device ID categories are not needed unless you add other SDKs

**Apps with no third-party SDKs:** Collect data? **No**

**Age rating for health logging apps:** Medical/Treatment = **None**, Health/Wellness = **Yes** → 9+ rating.

### 6.3 Submission Day

1. Run `/deploy` from a local Claude Code session (or `bundle exec fastlane beta` manually)
2. Wait for processing (~5–30 min)
3. In ASC version page: select the build, verify all metadata and screenshots
4. App Review Information: contact info + reviewer notes (explain the core flow step by step)
5. Click **Add for Review** → **Submit for Review**

**Review notes template:**
```
[App Name] is a [brief description].

To test the core flow:
1. [Step 1]
2. [Step 2]
3. [Step 3]

No account or sign-in is required. [Any special notes about permissions, trial, etc.]
```

### 6.4 Post-Submission

```bash
git tag -a v1.0.0 -m "App Store v1 submission"
git push origin --tags
```

Monitor: typical review 24–48 hours. If rejected, fix and resubmit.

After approval with `automatic_release: false`: manually release in ASC when ready.

### 6.5 Post-Release Version Bump

**Immediately after a version is approved and released on the App Store**, bump
`MARKETING_VERSION` in `project.yml` to the next minor version:

```yaml
MARKETING_VERSION: "1.1.0"  # was 1.0.0 — bump after App Store release
```

**Why:** App Store Connect closes the version train once a version is approved.
New TestFlight builds submitted under the old version will fail with:
"Invalid Pre-Release Train. The train version 'X.Y.Z' is closed for new build submissions."

This is a blocking error — no builds can be uploaded until the version is bumped.

**When to bump:**
- After App Store approval (regardless of whether you use automatic or manual release)
- Use the next minor version (1.0.0 → 1.1.0) unless you're planning a major release
- Commit as: `chore(version): bump to X.Y.0 for post-release development`
- Add to `MANUAL-TASKS.md` if the session that triggers the release can't do it immediately

### 6.6 Common Rejection Reasons

| Reason | Guideline | Prevention |
|---|---|---|
| Crashes on launch | 2.1 | Test on physical device; verify `#if DEBUG` key switching |
| Incomplete metadata | 2.3 | Fill every ASC field; all required screenshot sizes |
| Broken privacy/support URLs | 2.3 | Verify URLs load before submitting |
| HealthKit not identified in UI | 2.5.1 | Show "Apple Health" text in visible UI (settings, onboarding, buttons) — not just in code |
| Missing purpose strings | 2.5.1 | Check all Info.plist usage descriptions |
| Debug UI visible in production | 2.3.1 | Gate behind `#if DEBUG` |
| Placeholder content | 2.3.1 | Replace all "[YOUR NAME]" text |
| App icon has alpha channel | 2.3 | Strip transparency (see Python snippet above) |
| Content Rights not answered | 2.3 | Answer in App Information (easy to miss) |
| Pricing not set | 3.1.1 | Explicitly select Free even for IAP apps |
| Missing EULA/Terms link | 3.1.2(c) | Add Terms of Use link in description AND select EULA in ASC |
| Subscription info incomplete | 3.1.2(c) | Purchase flow must show title, length, price, Terms + Privacy links |

**Handling rejections:**
- You cannot swap the build on a rejected submission — create a new submission with a new build
- Reply to the rejection in Resolution Center to provide context, but the resubmission
  is done through the normal submission flow (select new build on the version page)
- In the App Review Information → Notes field, explain what changed since the last review
- Bump build number, push to main, wait for TestFlight processing, then submit

---

## ASC Field Location Cheat Sheet

| Field | Location in ASC |
|---|---|
| Screenshots, description, keywords, What's New | Version page |
| Promotional text | Version page, above description |
| Support URL, Marketing URL | Version page, bottom |
| Build selection | Version page, Build section |
| Review notes, contact info | Version page, App Review Information (bottom) |
| Categories, Age Rating, Content Rights | App Information (left sidebar) |
| License Agreement (EULA) | App Information → License Agreement |
| App Privacy + Privacy Policy URL | App Information → App Privacy |
| Pricing | Pricing and Availability (left sidebar) |
| Subscription products | Subscriptions (left sidebar) |

---

## Phase 7: Post-Launch Monitoring (Add When App is Live)

Don't set up analytics before you have something to measure. Add these when your app
is live on the App Store or has active TestFlight users.

### 7.1 Recommended Analytics Stack (Free Tier)

| Category | Tool | Free Tier | Setup Time |
|---|---|---|---|
| Usage analytics | TelemetryDeck | 100K signals/month | 4 minutes |
| Crash reporting | Sentry | 5K errors/month | 20 minutes |
| Performance | MetricKit (Apple native) | Unlimited (built-in) | 15 minutes |
| Revenue | App Store Connect Analytics | Free (built-in) | 0 minutes |

**TelemetryDeck** (telemetrydeck.com): Privacy-first analytics that requires no ATT
prompt. Add the SPM package, initialize with your app ID, send signals. Provides
retention and funnels.

```swift
import TelemetryDeck

// In your App.init()
let config = TelemetryDeck.Config(appID: "YOUR-APP-ID")
TelemetryDeck.initialize(config: config)

// Send signals anywhere
TelemetryDeck.signal("symptomStarted", parameters: ["type": "headache"])
```

**Sentry** (sentry.io): Real-time crash reporting with breadcrumbs and GitHub
integration. Catches crashes that Xcode Organizer misses (only users who opt into
diagnostics show up in Organizer).

**MetricKit**: ~20 lines of code gives you production performance data — launch times,
hang rates, memory peaks, disk writes, termination reasons. Forward payloads to
TelemetryDeck for visualization.

**App Store Connect Analytics** (March 2026 overhaul): Now includes 100+ metrics with
subscription cohort analysis, peer group benchmarks (conversion rate, proceeds per download),
offer performance tracking, and an Analytics Reports API for offline analysis. Use up to 7
simultaneous filters for drill-down. See the [Analytics Guide](https://developer.apple.com/help/app-store-connect-analytics/).

### 7.2 Future Automation Worth Considering

These aren't in the bootstrap script because they add complexity that isn't justified
until you're managing multiple apps or have a meaningful user base:

**git-cliff** — automated changelog generation from conventional commits. Replace the
manual `release-notes-draft.md` workflow when managing 3+ apps. Install: `brew install
git-cliff`. Parses your git history and generates `CHANGELOG.md` automatically.

**Xcode Cloud** — Apple provides 25 free compute hours/month with your Developer Program
membership (worth ~$93/month on GitHub Actions). Could supplement your GitHub Actions
pipeline for builds and TestFlight uploads while keeping GitHub Actions for lightweight
checks (lint, secret scanning) on free Linux minutes. Requires Xcode 26.3+ and a
`ci_post_clone.sh` script to run XcodeGen in CI.

**Periphery** — dead code detection. Run `brew install periphery && periphery scan
--setup` monthly before releases to find unused types and functions. Keeps the codebase
lean as it grows.

---

## Appendix A: Why These Tools

| Tool | Why this one | Alternatives considered |
|---|---|---|
| **XcodeGen** | YAML project definition, never touch `.pbxproj`. Clean diffs, no merge conflicts on project files. | Tuist (Swift-based config, better for large modular projects but heavier), manual `.pbxproj` (merge conflicts are brutal) |
| **Fastlane** | De facto iOS automation standard. One command for signing, building, uploading. Huge community and plugin ecosystem. | Xcode Cloud (25 free hrs/month but limited customization), manual `xcodebuild` (works but tedious at scale) |
| **SwiftLint** | Standard Swift linter, 200+ rules, 30% faster in recent versions. Catches style issues pre-commit. | swift-format (Apple's official formatter, but fewer rules and less community adoption) |
| **Lefthook** | Fast Go binary, parallel hook execution, no runtime dependencies. Config is one YAML file. | Husky (Node.js dependency — overkill for a Swift project), pre-commit (Python dependency) |
| **Gitleaks** | Catches secrets in staged files before commit. Simple, fast, no config needed for common patterns. | Betterleaks (successor by original Gitleaks creator — better recall, drop-in replacement, recommended for new projects) |
| **GitHub Actions** | Free for public repos, generous minutes for private. `macos-26` runners with Xcode 26.3. | Xcode Cloud (limited customization), Bitrise (free tier exists, iOS-focused), CircleCI |
| **Conventional Commits** | Machine-parseable commit messages. Enables automated changelogs, semantic versioning. Enforced by Lefthook hook. | Free-form commits (no tooling integration) |

## Appendix B: Decision Trees

### StoreKit 2 vs. RevenueCat

```
Do you need cross-platform subscriptions (iOS + Android)?
├── Yes → RevenueCat (handles both platforms, server-side entitlements)
└── No → Do you need server-side entitlement validation?
    ├── Yes, and I don't want to build a backend → RevenueCat
    └── No, or I have a backend → Native StoreKit 2
```

### Cloud vs. Local Claude Code Session

```
What do you need to do?
├── Write Swift code, plan architecture, commit/push → Cloud session works
├── Build, test on Simulator, run Fastlane → Local session required
├── Modify project structure (new targets, entitlements) → Local session required
└── Deploy to TestFlight → Local session (/deploy) or CI (push to main)
```

### XcodeBuildMCP vs. Xcode MCP Bridge

```
Is Xcode running?
├── No → XcodeBuildMCP (works standalone via xcodebuild CLI, 59 tools)
└── Yes → Both complement each other:
    ├── Xcode MCP Bridge → previews, documentation search, diagnostics (20 tools)
    └── XcodeBuildMCP → builds, simulator management, UI automation (59 tools)
```

## Appendix C: Migrating an Existing Project to the Playbook

This walkthrough is for projects that pre-date the playbook and want to adopt it.
Greenfield projects from `bootstrap.sh` already conform.

### When to migrate

Look for these symptoms:
- `CLAUDE.md` has grown past ~250 lines and mixes reference, session log, and rules
- A separate `MILESTONES.md` or session log file lives at project root
- A `FEEDBACK.md` (or similar) mixes closed `[x]` items and open `[ ]` items
- Operational rules are inline in `CLAUDE.md` rather than under `.claude/rules/`

### Five-step consolidation pass

1. **Audit.** Get line counts for `CLAUDE.md`, `MILESTONES.md`, `FEEDBACK.md`, and
   any other docs that look load-bearing. Identify role overlap.
2. **Fold milestone history into `WORKLOG.md`.** Move `MILESTONES.md` content to
   `WORKLOG.md` as a single condensed entry titled `Pre-<date> milestone summary`,
   then `git rm MILESTONES.md`.
3. **Slim `FEEDBACK.md` to open items only.** Closed `[x]` items live in git history;
   delete them from the working file. Aim for <150 lines.
4. **Slim `CLAUDE.md`.** Move operational rules → `.claude/rules/` (use the playbook
   files as templates). Move session-by-session detail → `WORKLOG.md`. Keep
   `CLAUDE.md` as stable reference: project overview, core loop, tech stack,
   architecture, scope rules, key product decisions.
5. **Update the `Related Context Files` table** in `CLAUDE.md` to reflect the new
   structure.

Reference: HVACApp's adoption commit (`5b35626 chore(playbook): adopt rules/cmds;
slim CLAUDE.md; fold MILESTONES`) shows the concrete shape — net ~830 lines of
tracked content removed while gaining ~1400 lines of `.claude/` rules/commands.

### Future: `/conform` slash command (roadmap)

A `/conform` command is on the roadmap to automate the broader case: full-state audit
of a project against the latest playbook expectation. It complements `/upgrade`
(delta-driven via CHANGELOG) by detecting drift in:

- Missing or stale `.claude/rules/*.md` files (compared to playbook source)
- Missing slash commands (e.g. `/preflight` added later)
- `CLAUDE.md` template gaps (sections added to `CLAUDE-TEMPLATE.md` since project bootstrap)
- Stale `lefthook.yml`, `Fastfile`, GitHub workflow files
- Doc bloat (the migration scenario above)
- Stranded files in `.claude/` that aren't in the playbook (custom keepers vs leftovers)

Until `/conform` ships, run the manual five-step pass above when symptoms appear.

## Appendix D: Maintaining the Playbook

### When Xcode updates

After installing a new Xcode version:

1. Run `xcodebuild -runFirstLaunch` to install simulator runtimes and developer tools
2. Check Xcode → Settings → Components for required iOS platform downloads
3. Verify your project compiles: `xcodebuild build -scheme YourApp -destination 'generic/platform=iOS'`
4. If using XcodeGen, regenerate: `xcodegen generate`
5. If CI fails, check GitHub's [runner images changelog](https://github.com/actions/runner-images) for the latest `macos-*` runner and Xcode version

### When iOS ships a new major version

1. Update `MINIMUM_IOS` in `bootstrap.sh` (for new projects only — don't bump existing apps without testing)
2. Update `ios-project-playbook.md` date stamp and verify all tool versions
3. Check for new StoreKit, CloudKit, or SwiftUI APIs that affect playbook guidance
4. Review WWDC session notes for framework deprecations

### Local debugging without Claude Code

If Claude Code is unavailable and you need to debug locally:

```bash
# Build and run
xcodebuild build -scheme YourApp -destination 'platform=iOS Simulator,name=iPhone 17 Pro'

# Run tests
xcodebuild test -scheme YourApp -destination 'platform=iOS Simulator,name=iPhone 17 Pro'

# Lint
/opt/homebrew/bin/swiftlint lint --strict

# Deploy to TestFlight
export PATH="/opt/homebrew/opt/ruby/bin:$PATH"
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
set -a && source .env.fastlane && set +a
bundle exec fastlane beta
```

## Appendix E: Glossary

| Term | What it is |
|---|---|
| **XcodeGen** | Generates `.xcodeproj` from a human-readable `project.yml`. Eliminates merge conflicts on project files. |
| **Fastlane** | Ruby-based automation toolkit for iOS builds, code signing, and App Store uploads. |
| **SwiftLint** | Linter that enforces Swift code style and catches common mistakes. |
| **Lefthook** | Git hooks manager — runs linters and checks before commits. Written in Go, no dependencies. |
| **Gitleaks / Betterleaks** | Pre-commit secret scanners — catch API keys and credentials before they're committed. |
| **Conventional Commits** | Commit message format (`type(scope): description`) that enables automated tooling. |
| **ASC** | App Store Connect — Apple's portal for managing apps, TestFlight, and App Store submissions. |
| **MCP** | Model Context Protocol — standard for connecting AI assistants (like Claude Code) to external tools. |
| **XcodeBuildMCP** | MCP server that gives Claude Code access to Xcode build, simulator, and debugging tools (59 tools). |
| **Xcode MCP Bridge** | Apple's native MCP server shipped with Xcode 26.3. Provides previews, docs search, diagnostics (20 tools). |
