# iOS Project Playbook

Master operational guide for solo indie iOS development. Covers the full lifecycle from
project creation to App Store submission. Written for Claude Code to follow — every step
is concrete, copy-pasteable, and tested.

**Last verified:** March 2026 (Xcode 26.3, macOS 26, GitHub Actions `macos-26` runners)

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
- Team ID: `3UH727U953`
- Developer: Erik Jimenez / hello@xolo.uno / domain: xolo.uno

### 0.2 One-Command Project Bootstrap

Run this from the parent directory where you want the project folder created.
Replace the four variables at the top — everything else is automatic.

> **Note:** The canonical version of this script is `_playbook/bootstrap.sh`. If you
> edit the script, update this section to match (or vice versa).

```bash
#!/bin/bash
set -euo pipefail
# ═══════════════════════════════════════════════════════
# CONFIGURE THESE FOUR VARIABLES
# ═══════════════════════════════════════════════════════
APP_NAME="MyApp"			# Display name and Xcode scheme
BUNDLE_ID="uno.xolo.myapp"		# Reverse-domain bundle identifier
REPO_NAME="myapp-app"			# GitHub repository name
MINIMUM_IOS="26.0"			# Deployment target
# ═══════════════════════════════════════════════════════
TEAM_ID="3UH727U953"
ORG="xoloUno"
# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
require_file() { [[ -f "$1" ]] || { echo "❌ Expected file not found: $1"; exit 1; }; }
require_dir()  { [[ -d "$1" ]] || { echo "❌ Expected directory not found: $1"; exit 1; }; }

# ═══════════════════════════════════════════════════════
# PREREQUISITE CHECKS
# ═══════════════════════════════════════════════════════
echo "🔍 Checking prerequisites..."
for cmd in git xcodegen gh; do
  command -v "$cmd" &>/dev/null || { echo "❌ Required tool '$cmd' not found. Install it first."; exit 1; }
done
gh auth status &>/dev/null || { echo "❌ GitHub CLI not authenticated. Run: gh auth login"; exit 1; }
if [[ -d "$REPO_NAME" ]]; then
  echo "❌ Directory '$REPO_NAME' already exists. Remove it or choose a different REPO_NAME."
  exit 1
fi
echo "✓ All prerequisites met"

echo "🚀 Bootstrapping $APP_NAME..."
# --- Create project directory ---
mkdir -p "$REPO_NAME" && cd "$REPO_NAME"
# --- Git init ---
git init
require_dir .git
# --- .gitignore ---
cat > .gitignore << 'GITIGNORE'
# Xcode
*.xcuserstate
xcuserdata/
*.xccheckout
*.moved-aside
DerivedData/
*.hmap
*.ipa
*.dSYM.zip
*.dSYM

# Build artifacts
build/

# CocoaPods (not used, but just in case)
Pods/

# Credentials — never commit
*.p12
*.mobileprovision
AuthKey_*.p8
Secrets.swift
.env
.env.*

# OS junk
.DS_Store

# Claude Code local scratchpads
MANUAL-TASKS.md
WORKLOG.md
GITIGNORE

# --- XcodeGen project.yml ---
cat > project.yml << XCODEGEN
name: $APP_NAME
options:
  bundleIdPrefix: ${BUNDLE_ID%.*}
  deploymentTarget:
    iOS: "$MINIMUM_IOS"
  xcodeVersion: "26.3"
  generateEmptyDirectories: true
settings:
  base:
    DEVELOPMENT_TEAM: $TEAM_ID
    SWIFT_VERSION: "6.0"
    MARKETING_VERSION: "0.1.0"
    CURRENT_PROJECT_VERSION: 1
    GENERATE_INFOPLIST_FILE: YES
    INFOPLIST_KEY_CFBundleDisplayName: "$APP_NAME"
    CODE_SIGN_STYLE: Automatic
    SWIFT_STRICT_CONCURRENCY: complete
    ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon
targets:
  $APP_NAME:
    type: application
    platform: iOS
    sources:
      - path: $APP_NAME
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: $BUNDLE_ID
        INFOPLIST_KEY_UILaunchScreen_Generation: YES
        INFOPLIST_KEY_ITSAppUsesNonExemptEncryption: false
        INFOPLIST_KEY_UISupportedInterfaceOrientations: UIInterfaceOrientationPortrait
        INFOPLIST_KEY_UISupportedInterfaceOrientations~ipad:
          - UIInterfaceOrientationPortrait
          - UIInterfaceOrientationPortraitUpsideDown
          - UIInterfaceOrientationLandscapeLeft
          - UIInterfaceOrientationLandscapeRight
    dependencies: []
packages: {}
XCODEGEN

# --- Create source directory + app entry point ---
mkdir -p "$APP_NAME"

cat > "$APP_NAME/${APP_NAME}App.swift" << APPSWIFT
import SwiftUI

@main
struct ${APP_NAME}App: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
APPSWIFT

cat > "$APP_NAME/ContentView.swift" << CONTENTSWIFT
import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Image(systemName: "checkmark.circle.fill")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("$APP_NAME is running")
        }
        .padding()
    }
}

#Preview {
    ContentView()
}
CONTENTSWIFT
# --- Create standard subdirectories ---
mkdir -p "$APP_NAME/Models" "$APP_NAME/Views" "$APP_NAME/Services"
# --- Create asset catalog with placeholder icon ---
mkdir -p "$APP_NAME/Assets.xcassets/AppIcon.appiconset"
mkdir -p "$APP_NAME/Assets.xcassets/AccentColor.colorset"
cat > "$APP_NAME/Assets.xcassets/Contents.json" << 'ASSETROOT'
{ "info": { "version": 1, "author": "xcode" } }
ASSETROOT
cat > "$APP_NAME/Assets.xcassets/AppIcon.appiconset/Contents.json" << 'ICONJSON'
{ "images": [{ "idiom": "universal", "platform": "ios", "size": "1024x1024" }], "info": { "version": 1, "author": "xcode" } }
ICONJSON
cat > "$APP_NAME/Assets.xcassets/AccentColor.colorset/Contents.json" << 'ACCENTJSON'
{ "colors": [{ "idiom": "universal" }], "info": { "version": 1, "author": "xcode" } }
ACCENTJSON

# --- Generate Xcode project ---
require_file project.yml
echo "📦 Running xcodegen..."
xcodegen generate
require_dir "${APP_NAME}.xcodeproj"
echo "✓ Xcode project generated"
# --- Gemfile for Fastlane ---
cat > Gemfile << 'GEMFILE'
source "https://rubygems.org"
gem "fastlane"
GEMFILE

# --- Fastlane config ---
mkdir -p fastlane

cat > fastlane/Appfile << APPFILE
app_identifier "$BUNDLE_ID"
team_id "$TEAM_ID"
APPFILE

cat > fastlane/Fastfile << 'FASTFILE'
default_platform(:ios)

platform :ios do

  desc "Build and upload to TestFlight"
  lane :beta do
    app_store_connect_api_key(
      key_id: ENV["ASC_KEY_ID"],
      issuer_id: ENV["ASC_ISSUER_ID"],
      key_filepath: ENV["ASC_KEY_FILEPATH"]
    )

    increment_build_number(
      build_number: latest_testflight_build_number + 1,
      xcodeproj: Dir.glob("*.xcodeproj").first
    )

    update_code_signing_settings(
      use_automatic_signing: false,
      path: Dir.glob("*.xcodeproj").first,
      team_id: CredentialsManager::AppfileConfig.try_fetch_value(:team_id),
      profile_name: ENV["PROVISIONING_PROFILE_NAME"],
      bundle_identifier: CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier),
      code_sign_identity: "Apple Distribution"
    )

    # If app has extension targets (widgets, etc.), add a second
    # update_code_signing_settings block per target here.
    # See §4.1 for multi-target signing.

    build_app(
      scheme: Dir.glob("*.xcodeproj").first.sub(".xcodeproj", ""),
      export_method: "app-store",
      export_options: {
        provisioningProfiles: {
          CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier) =>
            ENV["PROVISIONING_PROFILE_NAME"]
          # Add extension bundle IDs here if needed:
          # "uno.xolo.appname.widgets" => "AppName Widgets App Store"
        }
      }
    )

    upload_to_testflight(skip_waiting_for_build_processing: true)
  end

  desc "Upload to App Store Connect for review"
  lane :release do
    app_store_connect_api_key(
      key_id: ENV["ASC_KEY_ID"],
      issuer_id: ENV["ASC_ISSUER_ID"],
      key_filepath: ENV["ASC_KEY_FILEPATH"]
    )

    increment_build_number(
      build_number: latest_testflight_build_number + 1,
      xcodeproj: Dir.glob("*.xcodeproj").first
    )

    update_code_signing_settings(
      use_automatic_signing: false,
      path: Dir.glob("*.xcodeproj").first,
      team_id: CredentialsManager::AppfileConfig.try_fetch_value(:team_id),
      profile_name: ENV["PROVISIONING_PROFILE_NAME"],
      bundle_identifier: CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier),
      code_sign_identity: "Apple Distribution"
    )

    # If app has extension targets, add signing blocks here (same as beta lane).

    build_app(
      scheme: Dir.glob("*.xcodeproj").first.sub(".xcodeproj", ""),
      export_method: "app-store",
      export_options: {
        provisioningProfiles: {
          CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier) =>
            ENV["PROVISIONING_PROFILE_NAME"]
          # Add extension bundle IDs here if needed (same as beta lane).
        }
      }
    )

    upload_to_app_store(
      skip_screenshots: true,
      skip_metadata: true,
      precheck_include_in_app_purchases: false,
      submit_for_review: false,
      automatic_release: false
    )
  end

end
FASTFILE

# --- GitHub Actions workflows ---
mkdir -p .github/workflows

cat > .github/workflows/build-check.yml << 'BUILDCHECK'
name: Build Check

on:
  push:
    branches-ignore:
      - main

concurrency:
  group: build-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    name: Xcode Build
    if: "!contains(github.event.head_commit.message, '[skip build]')"
    runs-on: macos-26
    steps:
      - uses: actions/checkout@v4

      - name: Install XcodeGen
        run: brew install xcodegen

      - name: Generate Xcode project
        run: xcodegen generate

      - name: Build for Simulator
        run: |
          SCHEME=$(ls -d *.xcodeproj | head -1 | sed 's/.xcodeproj//')
          xcodebuild build \
            -scheme "$SCHEME" \
            -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
            -skipPackagePluginValidation \
            -quiet \
            CODE_SIGN_IDENTITY="" \
            CODE_SIGNING_REQUIRED=NO

      - name: Lint
        run: |
          brew install swiftlint
          swiftlint lint --strict --quiet
BUILDCHECK

cat > .github/workflows/testflight.yml << 'TESTFLIGHT'
name: TestFlight Deploy

on:
  workflow_dispatch:

concurrency:
  group: testflight
  cancel-in-progress: false

jobs:
  deploy:
    name: Build & Upload to TestFlight
    runs-on: macos-26
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Select Xcode
        run: sudo xcode-select -s /Applications/Xcode_26.3.app/Contents/Developer

      - name: Install XcodeGen
        run: brew install xcodegen

      - name: Generate Xcode project
        run: xcodegen generate

      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: "3.3"
          bundler-cache: true

      - name: Install Apple certificate
        env:
          CERTIFICATE_P12: ${{ secrets.CERTIFICATE_P12 }}
          CERTIFICATE_PASSWORD: ${{ secrets.CERTIFICATE_PASSWORD }}
        run: |
          KEYCHAIN_PATH=$RUNNER_TEMP/app-signing.keychain-db
          KEYCHAIN_PASSWORD=$(openssl rand -hex 16)

          security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
          security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
          security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"

          CERT_PATH=$RUNNER_TEMP/certificate.p12
          echo -n "$CERTIFICATE_P12" | base64 --decode -o "$CERT_PATH"
          security import "$CERT_PATH" \
            -P "$CERTIFICATE_PASSWORD" \
            -A \
            -t cert \
            -f pkcs12 \
            -k "$KEYCHAIN_PATH"

          security set-key-partition-list -S apple-tool:,apple: -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
          security list-keychains -d user -s "$KEYCHAIN_PATH" $(security list-keychains -d user | tr -d '"')

      - name: Install provisioning profile
        env:
          PROVISIONING_PROFILE: ${{ secrets.PROVISIONING_PROFILE }}
        run: |
          PROFILE_PATH=~/Library/MobileDevice/Provisioning\ Profiles
          mkdir -p "$PROFILE_PATH"
          echo -n "$PROVISIONING_PROFILE" | base64 --decode -o "$PROFILE_PATH/ci_profile.mobileprovision"

      - name: Write App Store Connect API key
        run: |
          mkdir -p fastlane
          printf '%s\n' "$APP_STORE_CONNECT_API_KEY" > fastlane/AuthKey.p8
        env:
          APP_STORE_CONNECT_API_KEY: ${{ secrets.APP_STORE_CONNECT_API_KEY }}

      - name: Build & Upload to TestFlight
        run: bundle exec fastlane beta
        env:
          ASC_KEY_ID: ${{ secrets.ASC_KEY_ID }}
          ASC_ISSUER_ID: ${{ secrets.ASC_ISSUER_ID }}
          ASC_KEY_FILEPATH: fastlane/AuthKey.p8
          PROVISIONING_PROFILE_NAME: ${{ secrets.PROVISIONING_PROFILE_NAME }}

      - name: Clean up secrets
        if: always()
        run: |
          rm -f fastlane/AuthKey.p8
          rm -f ~/Library/MobileDevice/Provisioning\ Profiles/ci_profile.mobileprovision
          KEYCHAIN_PATH=$RUNNER_TEMP/app-signing.keychain-db
          security delete-keychain "$KEYCHAIN_PATH" 2>/dev/null || true
TESTFLIGHT

# --- Legal docs directory (for GitHub Pages) ---
mkdir -p docs

cat > docs/index.html << LANDINGHTML
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>$APP_NAME</title>
<style>body{font-family:-apple-system,system-ui;max-width:600px;margin:40px auto;padding:0 20px}a{color:#007AFF}</style>
</head>
<body>
<h1>$APP_NAME</h1>
<ul>
  <li><a href="privacy.html">Privacy Policy</a></li>
  <li><a href="terms.html">Terms of Service</a></li>
</ul>
</body>
</html>
LANDINGHTML

# Placeholder legal docs — fill in before App Store submission
cat > docs/privacy.html << 'PRIVACYHTML'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Privacy Policy</title>
<style>body{font-family:-apple-system,system-ui;max-width:700px;margin:40px auto;padding:0 20px;line-height:1.6}</style>
</head>
<body>
<h1>Privacy Policy</h1>
<p><strong>Last updated:</strong> [DATE]</p>
<p>[APP_NAME] ("the App") is developed by [DEVELOPER_NAME]. This policy explains what data the App collects and how it is used.</p>
<h2>Data Collection</h2>
<p>[Describe what data the app collects, stores, and transmits. Be specific.]</p>
<h2>Third-Party Services</h2>
<p>[List any third-party SDKs: analytics, crash reporting, etc. Link to their privacy policies.]</p>
<h2>Contact</h2>
<p>[CONTACT_EMAIL]</p>
</body>
</html>
PRIVACYHTML

cat > docs/terms.html << 'TERMSHTML'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Terms of Service</title>
<style>body{font-family:-apple-system,system-ui;max-width:700px;margin:40px auto;padding:0 20px;line-height:1.6}</style>
</head>
<body>
<h1>Terms of Service</h1>
<p><strong>Last updated:</strong> [DATE]</p>
<p>[APP_NAME] is provided by [DEVELOPER_NAME]. By using the App, you agree to these terms.</p>
<h2>Usage</h2>
<p>[Standard terms. Customize per app.]</p>
<h2>Contact</h2>
<p>[CONTACT_EMAIL]</p>
</body>
</html>
TERMSHTML

# --- Fastlane metadata directory ---
mkdir -p fastlane/metadata/en-US
touch fastlane/metadata/en-US/{name.txt,subtitle.txt,description.txt,keywords.txt,release_notes.txt,privacy_url.txt,support_url.txt}

# --- Release notes draft ---
cat > release-notes-draft.md << 'RELNOTES'
# Release Notes Draft

Track user-facing changes here between App Store submissions.
Claude Code should update this at the end of every session with significant work.

## Next Version (unreleased)

- Initial release
RELNOTES

# --- Work log (session diary, gitignored) ---
cat > WORKLOG.md << 'WORKLOG'
# [APP_NAME] Work Log

> Session diary for Claude Code sessions. Reverse-chronological.
> CLAUDE.md is the reference doc; this file tracks what happened session by session.
> This file is gitignored — local scratchpad only.

---
WORKLOG

# --- Dependabot for SPM dependency updates ---
cat > .github/dependabot.yml << 'DEPENDABOT'
version: 2
updates:
  - package-ecosystem: "swift"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
DEPENDABOT

# --- SwiftLint config ---
cat > .swiftlint.yml << 'SWIFTLINT'
# SwiftLint configuration — keep lean, override only what matters
excluded:
  - DerivedData
  - build
  - .build
  - Pods

disabled_rules:
  - trailing_comma          # personal preference — allow trailing commas
  - todo                    # TODOs are fine during development

opt_in_rules:
  - empty_count             # prefer .isEmpty over .count == 0
  - closure_spacing
  - contains_over_first_not_nil
  - fatal_error_message
  - first_where
  - modifier_order
  - overridden_super_call
  - private_action
  - private_outlet
  - unneeded_parentheses_in_closure_argument
  - vertical_whitespace_closing_braces

line_length:
  warning: 120
  error: 200

type_body_length:
  warning: 300
  error: 500

file_length:
  warning: 500
  error: 1000
SWIFTLINT

# --- Lefthook (pre-commit hooks) ---
cat > lefthook.yml << 'LEFTHOOK'
glob_matcher: doublestar

pre-commit:
  parallel: true
  commands:
    swiftlint:
      glob: "**/*.{swift}"
      run: /opt/homebrew/bin/swiftlint lint --strict --quiet {staged_files}
    gitleaks:
      run: /opt/homebrew/bin/gitleaks protect --staged --verbose

commit-msg:
  commands:
    conventional-commit:
      run: |
        MSG=$(head -1 "{1}")
        echo "$MSG" | grep -qE '^(feat|fix|docs|refactor|test|chore|ui|perf|ci)(\([a-z0-9-]+\))?!?: .{1,72}$' || \
        (echo "❌ Commit message must follow conventional commits format" && \
         echo "   Example: feat(live-activity): add stop button" && exit 1)
LEFTHOOK

# --- Privacy manifest placeholder ---
cat > "$APP_NAME/PrivacyInfo.xcprivacy" << 'PRIVACY'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>NSPrivacyTracking</key>
	<false/>
	<key>NSPrivacyTrackingDomains</key>
	<array/>
	<key>NSPrivacyCollectedDataTypes</key>
	<array/>
	<key>NSPrivacyAccessedAPITypes</key>
	<array>
		<dict>
			<key>NSPrivacyAccessedAPIType</key>
			<string>NSPrivacyAccessedAPICategoryUserDefaults</string>
			<key>NSPrivacyAccessedAPITypeReasons</key>
			<array>
				<string>CA92.1</string>
			</array>
		</dict>
	</array>
</dict>
</plist>
PRIVACY

# --- Claude Code hooks (auto-lint on file edit) ---
mkdir -p .claude
cat > .claude/hooks.json << 'CLAUDEHOOKS'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Create",
        "hooks": [
          {
            "type": "command",
            "command": "swiftlint lint --quiet --path \"$CLAUDE_FILE_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
CLAUDEHOOKS

# --- Claude Code custom slash commands ---
mkdir -p .claude/commands

cat > .claude/commands/feature.md << 'FEATURECMD'
Scaffold a new feature module for $ARGUMENTS:
1. Create `Views/$ARGUMENTSView.swift` with a basic SwiftUI view + preview
2. Create `ViewModels/$ARGUMENTSViewModel.swift` with @Observable class
3. Create `Tests/$ARGUMENTSTests.swift` with Swift Testing import and placeholder test
4. Wire it into the navigation/routing structure
5. Follow all conventions in CLAUDE.md (adaptive colors, no force unwraps, etc.)
FEATURECMD

cat > .claude/commands/test.md << 'TESTCMD'
Generate Swift Testing tests for $ARGUMENTS:
1. Import Testing framework
2. Test all public methods with parameterized inputs where appropriate
3. Test error cases and edge conditions
4. Use @Test macro and #expect/#require assertions
5. Follow Arrange-Act-Assert pattern
6. Name tests descriptively: test_methodName_condition_expectedResult
TESTCMD

cat > .claude/commands/review.md << 'REVIEWCMD'
Review the current changes (staged or unstaged) for:
1. Swift 6 concurrency safety — @MainActor, Sendable conformance, data races
2. Retain cycles — closures capturing self without [weak self] where needed
3. Accessibility — VoiceOver labels, Dynamic Type support, color contrast
4. Privacy manifest — any new API usage that needs NSPrivacyAccessedAPITypes
5. Force unwraps or unhandled optionals
6. Any deviation from CLAUDE.md conventions

Be specific about file names and line numbers. Suggest fixes, not just problems.
REVIEWCMD

cat > .claude/commands/deploy.md << 'DEPLOYCMD'
Deploy the current state to TestFlight from this local machine.

Prerequisites — abort if any fail:
- This MUST be a local session (not cloud — cloud sessions cannot run fastlane)
- `.env.fastlane` must exist in the project root
- Must be on `main` branch (offer to merge dev/feature branch first if not)
- Provisioning profiles must be installed locally (see check below)

Steps:
1. **Check provisioning profiles** before anything else. Run:
   `ls ~/Library/MobileDevice/Provisioning\ Profiles/`
   Verify that every profile name referenced in the Fastfile's `update_code_signing_settings`
   and `provisioningProfiles` is installed. If any are missing, STOP — do not run fastlane.
   Tell the user which profiles are missing and that they need to download them from
   Apple Developer Portal → Profiles and copy them to `~/Library/MobileDevice/Provisioning Profiles/`.
   Offer to fall back to GitHub Actions instead.
2. Verify build compiles: build for iOS Simulator via XcodeBuildMCP
3. Run SwiftLint: `/opt/homebrew/bin/swiftlint lint --strict --quiet`
4. Run: `export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && set -a && source .env.fastlane && set +a && bundle exec fastlane beta`
5. If upload succeeds, ask user if they want to tag this release
6. Push main with `[skip ci]` to sync remote without triggering any workflows
7. Update "Current State" in CLAUDE.md with the deploy

Fallback if local build/upload fails:
- Restore any project files modified by fastlane: `git checkout -- *.xcodeproj`
- Trigger the GitHub Actions workflow: `gh workflow run testflight.yml`
- Monitor: `gh run list --workflow=testflight.yml --limit 1`
DEPLOYCMD

# --- Install Lefthook hooks ---
if command -v lefthook &> /dev/null; then
  lefthook install
else
  echo "⚠️  Lefthook not installed. Run: brew install lefthook && lefthook install"
fi
# --- Generate CLAUDE.md from template ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/CLAUDE-TEMPLATE.md"
if [[ -f "$TEMPLATE" ]]; then
  APP_NAME_LOWER=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]')
  sed -e "s|\[APP_NAME\]|$APP_NAME|g" \
      -e "s|\[uno\.xolo\.appname\]|$BUNDLE_ID|g" \
      -e "s|\[appname\]|$APP_NAME_LOWER|g" \
      -e "s|\[REPO_NAME\]|$REPO_NAME|g" \
      "$TEMPLATE" > CLAUDE.md
  require_file CLAUDE.md
  echo "✓ CLAUDE.md generated from template"
else
  echo "⚠️  CLAUDE-TEMPLATE.md not found at $TEMPLATE — skipping CLAUDE.md generation"
fi
# --- Initial commit ---
git add -A
git commit -m "chore: bootstrap $APP_NAME project
XcodeGen project, Fastlane CI/CD, GitHub Actions workflows,
SwiftLint, Lefthook pre-commit hooks, Dependabot, privacy manifest,
Claude Code hooks and slash commands, legal doc templates.
Co-Authored-By: Claude <noreply@anthropic.com>"
git log --oneline -1 >/dev/null || { echo "❌ Initial commit failed"; exit 1; }
echo "✓ Initial commit created"
# --- Create GitHub repo and push ---
echo "🌐 Creating GitHub repo..."
gh repo create "$ORG/$REPO_NAME" --private --source=. --push
gh repo view "$ORG/$REPO_NAME" --json name >/dev/null || { echo "❌ GitHub repo creation failed"; exit 1; }
echo "✓ GitHub repo created and pushed"
echo ""
echo "✅ $APP_NAME bootstrapped successfully!"
echo ""
echo "📁 Project: $(pwd)"
echo "🔗 Repo:    https://github.com/$ORG/$REPO_NAME"
echo ""
echo "⚠️  MANUAL STEPS REMAINING:"
echo "   1. Register bundle ID in Apple Developer Portal"
echo "   2. Create app record in App Store Connect"
echo "   3. Create provisioning profile for $BUNDLE_ID"
echo "   4. Add GitHub Secrets (see Phase 1 in ios-project-playbook.md)"
echo "   5. Enable GitHub Pages (Settings → Pages → main branch, /docs folder)"
echo "   6. Open CLAUDE.md and fill in project-specific sections (core problem, tech stack, etc.)"
echo ""
```

Save this script as `bootstrap.sh` in your `_playbook` folder (or it may already be there).
Run with `bash '_playbook/bootstrap.sh'` after editing the four variables.

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
| App Store validation rejects alpha channel | Icon PNG has transparency | Strip with PIL (see Phase 5) |
| `gitleaks: command not found` in pre-commit | Claude Code sessions don't inherit full shell PATH | Use full Homebrew paths in `lefthook.yml` (see fix below) |

### 1.6 Local TestFlight Deploy Setup

Store your App Store Connect API key in a shared location (same key works across all apps):

The `.p8` key file is stored at `~/Documents/Xcode/AuthKey_GXSJ996C83.p8` (shared
across all apps). If starting fresh, download the key from App Store Connect → Users
and Access → Integrations → App Store Connect API and save it there.

In each project root, create `.env.fastlane` (already gitignored via `.env.*`):

```
ASC_KEY_ID=GXSJ996C83
ASC_ISSUER_ID=13ef7cd0-b5b7-46b4-991b-32d6ee6da1bd
ASC_KEY_FILEPATH=/Users/erikj/Documents/Xcode/AuthKey_GXSJ996C83.p8
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

1. Never use cloud-managed signing on CI — manual signing with `update_code_signing_settings` is reliable.
2. Fastlane runs from the `fastlane/` subdirectory — file paths are relative to that folder.
3. Fastlane's `export_method` only accepts `"app-store"` (not `"app-store-connect"`).
4. Provisioning profile name must match exactly in three places: Apple portal, `update_code_signing_settings`, and `export_options.provisioningProfiles`.
5. Register your app in App Store Connect BEFORE the first CI build.
6. The same distribution certificate works across all your apps.
7. Always run `xcodegen generate` in CI if you use XcodeGen.
8. After Xcode updates, `xcodebuild` may fail with "failed to load a required plug-in" —
   run `xcodebuild -runFirstLaunch` to fix. This reinstalls simulator runtimes and
   developer tools. Also check that the iOS platform is installed in Xcode → Settings →
   Components if you get "iOS X.X is not installed" errors.
9. **Homebrew Ruby is required for local fastlane** — macOS ships Ruby 2.6 which lacks
   bundler 4.x. Always prepend `/opt/homebrew/opt/ruby/bin` to `PATH` before running
   `bundle exec fastlane`. The `/deploy` slash command handles this automatically.
10. **UTF-8 locale required for fastlane** — without `LC_ALL=en_US.UTF-8`, fastlane's
    gym crashes with `invalid byte sequence in US-ASCII` when parsing Xcode build logs.

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

- Swift 6 strict concurrency — `@MainActor` on view models, `async/await` everywhere
- No third-party UI libraries — SwiftUI + system components only
- ViewModels use `@Observable` (not `ObservableObject`)
- No force unwraps — `guard let` / `if let` always
- File naming matches primary type
- No comments explaining what — only why
- Previews required for every SwiftUI View
- System adaptive colors throughout — never hardcode `Color.black` / `Color.white`

**SwiftLint gotcha — whitespace after code removal:** When deleting a code block (e.g.
removing a Section from a List), check for trailing blank lines before closing braces.
SwiftLint's `vertical_whitespace_closing_braces` rule will reject the commit if an empty
line sits before a `}`. Always clean up blank lines after removing code.

### 3.4 WWDC25 & iOS 26 Awareness

Claude Code's training predates WWDC25. Before writing code using any framework introduced
at or after WWDC25, search Apple Developer Documentation to verify current APIs.

Key changes: iOS version jumped 18 → 26 (skipped 19–25). Liquid Glass design system applies
automatically. SceneKit soft-deprecated. Metal 4 introduced. FoundationModels framework for
on-device AI. SF Symbols 7.

### 3.5 Cloud vs Local Session Capabilities

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
  bundle_identifier: "uno.xolo.yourapp.widgets",
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
      "uno.xolo.yourapp" => ENV["PROVISIONING_PROFILE_NAME"],
      "uno.xolo.yourapp.widgets" => "YourApp Widgets App Store"
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
- [ ] Register the extension bundle ID (e.g. `uno.xolo.yourapp.widgets`)
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

---

## Phase 4.5: Screenshot Workflow

Screenshots are required for App Store submission and are the single biggest factor in
conversion. This workflow handles the full pipeline: automated capture on simulators,
professional framing and design, and export at correct sizes.

### Required Device Sizes (blocks submission if missing)

| ASC Size Label | Simulator Device | Resolution | Required? |
|---|---|---|---|
| iPhone 6.5" | iPhone 14 Plus | 1284 × 2778 | **Yes** — blocks "Add for Review" |
| iPad 13" | iPad Pro 13-inch (M5) | 2064 × 2752 | **Yes** — blocks "Add for Review" |
| iPhone 6.3" | iPhone 16/17 Pro | 1179 × 2556 | Optional — scales from 6.5" |
| iPhone 6.9" | iPhone 16 Pro Max | 1260 × 2736 | Optional — can replace 6.5" requirement |

**Important:** ASC screenshot categories are defined by resolution, not device generation.
iPhone 17 Pro outputs 6.3" resolution — it does NOT satisfy the 6.5" requirement. You
must use iPhone 14 Plus (or iPhone 13 Pro Max) for the 6.5" category.

Minimum 1 screenshot per required size. Upload 3–5 on your primary size (6.5") for
marketing impact. Add 6.3" or 6.9" screenshots optionally for newer device marketing.

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
# Devices matching all three required ASC sizes
devices([
  "iPhone 17 Pro",             # 6.3" — primary marketing size
  "iPhone 14 Plus",             # 6.5" — required for submission (1284x2778)
  "iPad Pro 13-inch (M5)"     # 13"  — required even for iPhone-only
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

**UI Test file** (in your UI Test target):

```swift
import XCTest

@MainActor
class ScreenshotTests: XCTestCase {

    private lazy var app: XCUIApplication = {
        let application = XCUIApplication()
        application.launchArguments.append("-FASTLANE_SNAPSHOT")
        return application
    }()

    override func setUp() async throws {
        continueAfterFailure = false
        setupSnapshot(app)
        app.launch()
    }

    func testCaptureScreenshots() {
        captureLightModeScreenshots()
        captureDarkModeScreenshots()
    }

    private func captureLightModeScreenshots() {
        sleep(1)

        // Screenshot 1: Home screen / main view
        snapshot("01_HomeScreen")

        // Screenshot 2: Navigate to key feature
        // app.buttons["feature-button"].tap()
        // sleep(1)
        snapshot("02_KeyFeature")

        // Screenshot 3: Detail view or result
        // app.cells.firstMatch.tap()
        // sleep(1)
        snapshot("03_DetailView")

        // Screenshot 4: Settings or secondary feature
        // app.tabBars.buttons["Settings"].tap()
        // sleep(1)
        snapshot("04_Settings")
    }

    private func captureDarkModeScreenshots() {
        // Screenshot 5: Key screen in dark mode
        XCUIDevice.shared.appearance = .dark
        sleep(2)
        snapshot("05_HomeScreenDark")

        // Restore light mode
        XCUIDevice.shared.appearance = .light
    }
}
```

**Mock/demo data tip:** Use the `-FASTLANE_SNAPSHOT` launch argument to detect when
running under snapshot and load compelling demo data instead of an empty state:

```swift
// In your app code
if ProcessInfo.processInfo.arguments.contains("-FASTLANE_SNAPSHOT") {
    // Load demo data that makes screenshots look great
}
```

**Run capture:**

```bash
# Capture all screenshots across all devices
bundle exec fastlane snapshot

# Or add a Fastlane lane
# lane :screenshots do
#   capture_screenshots
# end
# Then: bundle exec fastlane screenshots
```

After running, `fastlane/screenshots/` will contain all raw PNGs organized by language
and device, plus an HTML summary page for quick review.

**Alternative: Manual capture with XcodeBuildMCP**

If you haven't set up UI Tests yet, XcodeBuildMCP can capture screenshots on demand
during a Claude Code session:

```
# In Claude Code (local session):
"Build and run the app on iPhone 17 Pro simulator, navigate to the home screen,
and take a screenshot. Then do the same on iPhone 14 Plus and iPad Pro 13-inch."
```

This is faster for one-off captures but doesn't scale like Fastlane `snapshot` does.

### Step 2: Design and Frame Screenshots

Raw simulator screenshots won't convert users. Add device frames, captions, and
branded backgrounds using one of these free tools:

**Recommended: AppMockUp Studio** — https://app-mockup.com
- Free, web-based, no account required
- Modern device frames (iPhone 16/17 Pro, iPad Pro, clay and real styles)
- Panoramic backgrounds that connect across your screenshot set
- Drag-and-drop positioning, text overlays, logo placement
- Export at exact ASC-required resolutions

**Alternative: AppDrift** — https://appdrift.co
- Free drag-and-drop editor, all device frames, batch export, no watermarks
- AI translation for localized captions (pay-as-you-go)
- Good for generating all required sizes from one design

**Alternative: AppLaunchpad** — https://theapplaunchpad.com
- 150+ device frames including latest models
- Auto-generates prices for other device sizes from one design
- Free tier with 3 templates

**Design tips that affect conversion:**
- Lead with your core value prop, not a settings screen
- First 2–3 screenshots matter most — treat them as a mini-story
- Large, readable text captions (visible even at thumbnail size in search results)
- Use your app's accent color as the background theme for brand consistency
- Put the actual app UI inside device frames — Apple rejects pure marketing mockups
  without real in-app screenshots

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

| Stage | Capture | Design | Upload |
|---|---|---|---|
| **First app / v1 launch** | Manual on 3 simulators (or XcodeBuildMCP) | AppMockUp Studio (free, 20 min) | Manual in ASC |
| **Second app onward** | Fastlane `snapshot` (one command) | AppMockUp Studio | Manual in ASC |
| **Mature workflow** | Fastlane `snapshot` | AppMockUp Studio or `frameit` | Fastlane `deliver` |

Don't over-engineer this on your first app. Manual capture + AppMockUp Studio gets you
professional results in under 30 minutes. Add Fastlane automation when you're updating
screenshots regularly across multiple apps.

---

## Phase 5: App Store Submission

> **Note:** Many steps in this phase require human action in App Store Connect or the
> Apple Developer Portal. When Claude Code is guiding you
> through submission, it will write remaining manual steps to `MANUAL-TASKS.md` in your
> project root so you have a persistent checklist that survives across sessions.
> See the CLAUDE.md template's "Manual Tasks Handoff Rule" for details.

### 5.1 Pre-Submission Checklist

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
- [ ] Copyright filled (e.g. "2026 Erik Jimenez")
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
| iPhone 6.5" | iPhone 14 Plus | 1284 × 2778 | **Yes** — blocks "Add for Review" if missing |
| iPad 13" | iPad Pro 13" (M5) | 2064 × 2752 | **Yes** — blocks "Add for Review" if missing |
| iPhone 6.3" | iPhone 16/17 Pro | 1179 × 2556 | Optional — scales from 6.5" |
| iPhone 6.9" | iPhone 16 Pro Max | 1260 × 2736 | Optional — can replace 6.5" requirement |

Minimum 1 screenshot per required size. The 6.5" and iPad 13" categories use older device
resolutions — do not substitute newer devices (e.g. iPhone 17 Pro is 6.3", not 6.5").
See **Phase 4.5: Screenshot Workflow** below for the full capture-and-design pipeline.

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

### 5.2 App Privacy Questionnaire Guidance

**Apps with native StoreKit 2 subscriptions + HealthKit (no third-party analytics):**
- Collect data? **Yes**
- Select: Health (HealthKit)
- Linked to identity? **No**. Used for tracking? **No**. Purpose: **App Functionality**
- Note: Native StoreKit 2 doesn't send purchase data to third parties, so Purchase History
  and Device ID categories are not needed unless you add other SDKs

**Apps with no third-party SDKs:** Collect data? **No**

**Age rating for health logging apps:** Medical/Treatment = **None**, Health/Wellness = **Yes** → 9+ rating.

### 5.3 Submission Day

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

### 5.4 Post-Submission

```bash
git tag -a v1.0.0 -m "App Store v1 submission"
git push origin --tags
```

Monitor: typical review 24–48 hours. If rejected, fix and resubmit.

After approval with `automatic_release: false`: manually release in ASC when ready.

### 5.5 Post-Release Version Bump

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

### 5.6 Common Rejection Reasons

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

## Phase 6: Post-Launch Monitoring (Add When App is Live)

Don't set up analytics before you have something to measure. Add these when your app
is live on the App Store or has active TestFlight users.

### 6.1 Recommended Analytics Stack (Free Tier)

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

### 6.2 Future Automation Worth Considering

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
