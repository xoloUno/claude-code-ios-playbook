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

#### Track B — shotsmith (when you need captions + gradients + multi-locale)

Apple Frames CLI only applies device bezels. For marketing screenshots with
captions, gradient backgrounds, and multi-locale rendering, use **shotsmith** —
a standalone Python composer at
[github.com/xoloUno/shotsmith](https://github.com/xoloUno/shotsmith). It
replaces the prior appshot-cli + `patch-appshot.sh` pipeline (retired
2026-05-03; see [CHANGELOG.md](CHANGELOG.md) for migration history).
shotsmith was developed in this playbook from v0.1.0 through v0.2.0 and
spun off to its own repo on 2026-05-03 for decoupled release cadence. It
wraps frames-cli for the bezel step and adds a Pillow (FreeType +
HarfBuzz) layer for typography — gradients, captions, optional subtitles,
per-device overrides, multi-locale, and a stable per-device directory
contract that preserves raws and framed intermediates.

**The durable reference is [`.claude/rules/screenshot-pipeline.md`](.claude/rules/screenshot-pipeline.md)**.
That rule covers the four artifact layers (`raw/` → `framed/` → `composed/`),
the two-input-tree pattern (regenerable XCUITest captures vs. tracked
manual-gesture captures), the agent-driven manual-capture loop, and the watch
checklist. The rule auto-loads in any project directory; this section is the
quick-start reference for the human-readable docs.

The pipeline:

```
raw simctl/UITest PNGs (in fastlane/screenshots/<locale>/<device>/raw/)
        ↓ shotsmith frame    (wraps frames-cli; writes to framed/)
framed PNGs
        ↓ shotsmith compose  (gradient + caption + optional subtitle)
final ASC-ready PNGs (in fastlane/shotsmith/composed/<style>/<locale>/<device>/)
        ↓ deliver
App Store Connect
```

**One-time install (per machine).** shotsmith uses Pillow as its only
runtime dependency:

```bash
pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0
shotsmith --version   # verifies install
```

Or for development from a clone:

```bash
git clone https://github.com/xoloUno/shotsmith.git
cd shotsmith && pip install -r requirements.txt
ln -s "$(pwd)/bin/shotsmith" ~/.local/bin/shotsmith
```

frames-cli must also be on `PATH` (see Track A above for that one-time
install).

**Optional Claude Code skill** — shotsmith ships a standalone skill at
`skill/SKILL.md` in its repo. Install once to give any session in any
project shotsmith awareness:

```bash
mkdir -p ~/.claude/skills/shotsmith
ln -s /path/to/shotsmith/skill/SKILL.md ~/.claude/skills/shotsmith/SKILL.md
```

When `bootstrap.sh` runs and shotsmith isn't on `PATH`, it prints these
install hints and continues — bootstrap doesn't hard-block on optional
tooling.

**Project layout (bootstrap-emitted).** Two input trees with opposite gitignore
policies — see the rule for the full rationale:

```
fastlane/
├── shotsmith/
│   ├── config.json                               ← TUNE THIS (gradient, captions, locales)
│   ├── captions.json                             ← {filename: {lang: caption|{caption,subtitle}}}
│   └── composed/<style>/<locale>/<device>/       ← (gitignored) ASC-ready output
├── manual-captures/<locale>/                     ← TRACKED — manual-gesture inputs
│   ├── 90_LockScreen_LiveActivity.png            ← Live Activity stack
│   ├── 91_HomeScreen_Widget.png                  ← Home Screen widget page
│   └── 92_ControlCenter.png                      ← Control Center swipe-down
└── screenshots/<locale>/<device>/                ← (gitignored) regenerable
    ├── raw/                                      ← XCUITest/simctl output
    └── framed/                                   ← frames-cli output (via shotsmith)
```

`fastlane/manual-captures/` is **intentionally tracked** — those PNGs are
recaptured "once per release" via the agent-driven `/capture-manual-surfaces`
slash command (defined in the playbook, propagated to every project at
bootstrap). All other screenshot directories are regenerable.

**Tune `fastlane/shotsmith/config.json` per project.** Starter template
(see [shotsmith's `templates/config.example.json`](https://github.com/xoloUno/shotsmith/blob/main/templates/config.example.json)
for the full schema with subtitle, dither, per-device overrides, and
`input_mapping`):

```json
{
  "version": 2,
  "input":  { "iphone": "../screenshots/{locale}/iPhone 6.9\" Display" },
  "output": { "iphone": "composed/royal-purple/{locale}/iPhone 6.9\" Display" },
  "pipeline": { "frames_cli": "frames", "verify_strict": true },
  "background": {
    "type": "linear-gradient",
    "stops": ["#6B4FBB", "#FF6B5C"],
    "angle": 180,
    "dither": 30
  },
  "caption": {
    "font": "New York Small Bold",
    "color": "#FFFFFF",
    "size_iphone": 115,
    "size_ipad": 130,
    "padding_pct": 3.5,
    "max_lines": 2
  },
  "captions_file": "captions.json",
  "locales": ["en-US", "es-ES", "es-MX"],
  "manual_inputs": {
    "iphone": {
      "source": "../manual-captures/{locale}",
      "files": [
        "90_LockScreen_LiveActivity.png",
        "91_HomeScreen_Widget.png",
        "92_ControlCenter.png"
      ]
    }
  }
}
```

The `manual_inputs` block declares which manual-gesture captures (Live
Activity, Home Screen widget, Control Center) shotsmith should stage into
`raw/` before framing. `shotsmith verify` reports a hard error when any
declared source file is missing on disk — so a fresh-bootstrap or
fresh-clone run names the missing capture file directly instead of hiding
it inside an `input_mapping` indirection. Omit the block entirely if your
app has no manual-gesture surfaces.

Three preset palettes are bundled at
[shotsmith's `templates/presets/`](https://github.com/xoloUno/shotsmith/tree/main/templates/presets):
**mauve** (dusty purple → coral), **royal-purple** (deep violet → coral, used
by Flara), and **apple-music** (deep red → coral). Copy any one as your
starting point.

**Captions file** (`fastlane/shotsmith/captions.json`) — one entry per
screenshot filename, one key per language code. The string form is shorthand
for caption-only; the dict form supports an optional subtitle and per-device
overrides:

```json
{
  "01_HomeScreen.png": {
    "en":    { "caption": "Track everything", "subtitle": "in one place" },
    "en-US": { "caption_iphone": "Track everything\nin one place" },
    "es":    "Todo en un solo lugar"
  }
}
```

shotsmith resolves locale → language fallback (`es-MX` → `es` → skip with
warning), so regional variants share a single language entry by default.

**Run the pipeline.** One command captures the manual-gesture inputs (if any
have changed), stages them, frames everything, composes the final PNGs, and
hands off to `deliver`:

```bash
# 1. (Optional, once per release) Capture manual-gesture surfaces
#    Live Activity, Home Screen widget, Control Center — agent-driven.
/capture-manual-surfaces                           # Claude Code slash command

# 2. Capture in-app screens (XCUITest) — project-specific
./scripts/capture-screenshots.sh                   # writes to <locale>/<device>/raw/

# 3. Stage manual-captures + run frame + compose
bundle exec fastlane compose_screenshots           # invokes `shotsmith pipeline`

# 4. Upload
bundle exec fastlane upload_screenshots
```

The `compose_screenshots` lane (bootstrap-emitted) is a one-line wrapper
around `shotsmith pipeline` (with an install-check that prints a
friendly hint if shotsmith isn't on PATH) — staging is handled inside
shotsmith via the `manual_inputs` config block (the `stage` step), and
`input_mapping` renames the `90/91/92_` prefixes into canonical caption
keys at frame time. Multi-locale runs in a single pass — `config.json`
lists the locales, shotsmith iterates them.

> **Raw + framed preservation is automatic.** shotsmith's directory contract
> writes to `raw/` and `framed/` siblings under each device dir and never
> overwrites them. Re-running `compose` with new caption text or gradient
> stops re-renders the composed output in seconds without re-capturing or
> re-framing. `shotsmith verify` flags loose PNGs at the locale root and
> stale orphans before you ship.

**Multi-locale tip — share captions across regional variants.** Add both
`es-ES` and `es-MX` to `locales` in `config.json` and provide a single `es`
key in `captions.json`. shotsmith's locale-fallback resolution picks up the
language portion automatically. Manual-captures still need to be mirrored
per locale — for now via `cp -r manual-captures/es-ES manual-captures/es-MX`
if the rendered surfaces are visually identical between regional variants.

**Watch screenshots are screen-only.** Apple Watch submissions go to ASC as
raw `simctl io screenshot` output (422×514 native for Ultra 3) with no
framing, no gradient, no caption — the watch hardware's display
corner-radius would clip any added art at viewing time. shotsmith never
touches the watch path; the `compose_screenshots` lane stages the raw watch
PNGs directly into the composed-output tree alongside iPhone/iPad. See the
"Watch screenshot capture" section of `screenshot-pipeline.md` for the
seven-gotcha checklist.

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

### Step 2.6: Manual-capture surfaces (Control Center, Live Activity, Home Screen widget)

Three screenshot surfaces are rendered by SpringBoard rather than your app —
the **Live Activity stack on the Lock Screen**, the **Home Screen page with
your widget**, and **Control Center pulled down with your Control Widget**.
None can be reached by XCUITest. Earlier versions of this playbook tried
synthesized mouse drags (Quartz `CGEvent.post`) and AppleScript `Cmd+L`
keystroke automation — both were unreliable enough across machines that they
were retired. The current flow is **agent-driven** instead: Claude Code runs
the prep (boot, locale, status bar, app launch), you perform the gesture in
the Simulator window, type `ready` in chat, and Claude captures.

> **Opt-in.** This step only matters if your app ships a Live Activity
> (`ActivityKit`), a Home Screen widget (`WidgetKit`), or a Control Widget
> (`ControlKit`, iOS 18+). Apps without those surfaces skip Step 2.6 entirely
> — there's nothing app-specific in the iOS-default Control Center / lock
> screen / home screen to capture.

**Required reading:**

- `.claude/rules/screenshot-pipeline.md` — the four-layer pipeline + the
  two-input-tree pattern + the gesture inventory + an inlined fallback script
  for non-Claude-Code workflows.
- `.claude/rules/status-bar-overrides.md` — the canonical status-bar block.

**Where the captures land:**

```
fastlane/manual-captures/<locale>/
├── 90_LockScreen_LiveActivity.png
├── 91_HomeScreen_Widget.png
└── 92_ControlCenter.png
```

**Tracked in git** (unlike the regenerable `fastlane/screenshots/`). These are
"once per release" inputs — recapture only when iOS major version changes,
your widget/LA UI changes, or a new locale is added. The `:compose_screenshots`
Fastfile lane stages them into the iPhone `raw/` tree before invoking
shotsmith.

> **⚠️ Never `xcrun simctl uninstall <DEVICE> <BUNDLE_ID>` between captures.**
> Uninstall removes the app **and all of its extensions/widgets** — wiping
> the manual placements of the home-screen widget, the Live Activity, and
> the Control Center widget. Reinstalling does not bring those layouts back.
> See §2.5 for launch-arg detection patterns that neutralize persisted
> UserDefaults without uninstalling.

**Usage:**

```bash
# In Claude Code:
/capture-manual-surfaces

# The agent walks every (locale × surface) pair: prep → prompt you →
# capture → verify → next.
```

After capturing, run shotsmith via the compose lane to stage manual-captures
into `raw/` and produce ASC-ready images:

```bash
bundle exec fastlane compose_screenshots
```

**One-time manual setup per simulator (same as §2.5):** Add your home-screen
widget and Control Widget once via the simulator UI. Both placements persist
across reboots and `bundle exec fastlane` runs in the simulator's
`CoreSimulator` data container.

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

| Stage | Capture | Frame + Caption + Background | Upload |
|---|---|---|---|
| **First app / v1 launch** | Manual on 2 simulators (or XcodeBuildMCP) | Apple Frames CLI (Track A) — bare bezels | Manual in ASC |
| **Second app onward** | Fastlane `snapshot` | `fastlane frame_screenshots` (Track A) | Fastlane `deliver` |
| **Marketing-heavy app** | Fastlane `snapshot` + `/capture-manual-surfaces` | `fastlane compose_screenshots` (Track B — shotsmith) | Fastlane `deliver` |

Don't over-engineer this on your first app. Raw capture + Apple Frames CLI gets
you professional framed screenshots in under 5 minutes. Add shotsmith captions
and branded gradients later when you need marketing polish.

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

### `/conform` slash command (full-state audit)

The `/conform` command automates the broader case: a full-state audit of a project against
the latest playbook expectation. It complements `/upgrade` (delta-driven via CHANGELOG) by
direct comparison rather than CHANGELOG replay. It detects drift in:

- Missing or stale `.claude/rules/*.md` files (compared to playbook source)
- Missing or stale playbook-copied slash commands
- Missing bootstrap-emitted slash commands (e.g. `/preflight` added later)
- `CLAUDE.md` template gaps (sections added to `CLAUDE-TEMPLATE.md` since project bootstrap)
- Doc bloat (the migration scenario above — `MILESTONES.md`, `FEEDBACK.md`, scattered logs)
- Stranded files in `.claude/` that aren't in the playbook (custom keepers vs. leftovers)

Run `/conform` from any bootstrapped iOS project. It presents drift as a single table, then
asks how to proceed: apply all auto-fixable, walk one-by-one, or just report. Stale or
missing playbook-copied files are auto-applied with user approval; CLAUDE.md gaps, doc
bloat, and stranded files are surfaced as manual follow-ups (the user decides intent).

When to reach for it:
- Returning to a project after a long absence
- After a major playbook update — run `/upgrade` first (CHANGELOG-driven), then `/conform`
  to catch anything the upgrade missed
- Adopting the playbook on an existing project — combine with the five-step pass above

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
