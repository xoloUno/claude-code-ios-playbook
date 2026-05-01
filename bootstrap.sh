#!/bin/bash
set -euo pipefail
# ═══════════════════════════════════════════════════════
# CONFIGURE THESE FOUR VARIABLES
# ═══════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════
# CONFIG — loaded from env files, no need to edit this script
# ═══════════════════════════════════════════════════════
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Identity (one-time setup)
if [[ -f "$SCRIPT_DIR/.env.playbook" ]]; then
  # shellcheck source=.env.playbook.example
  source "$SCRIPT_DIR/.env.playbook"
else
  echo "⚠️  No .env.playbook found — copy .env.playbook.example and fill in your values."
fi

# Project (edit per project)
if [[ -f "$SCRIPT_DIR/.env.project" ]]; then
  # shellcheck source=.env.project.example
  source "$SCRIPT_DIR/.env.project"
else
  echo "❌ No .env.project found — copy .env.project.example and fill in your app details."
  exit 1
fi

# Fallbacks for identity vars (project vars have no fallback — they're required)
TEAM_ID="${TEAM_ID:-YOUR_TEAM_ID}"
ORG="${ORG:-YourGitHubOrg}"

# Validate required project vars
for var in APP_NAME BUNDLE_ID REPO_NAME; do
  [[ -n "${!var:-}" ]] || { echo "❌ $var is not set in .env.project"; exit 1; }
done
MINIMUM_IOS="${MINIMUM_IOS:-26.0}"
PRIMARY_SIM="${PRIMARY_SIM:-iPhone 17 Pro}"
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
# appshot — keep config + captions, ignore intermediate PNG dirs
fastlane/appshot/screenshots/
fastlane/appshot/final/
fastlane/appshot/.appshot/config.backup.json
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
  # ── Uncomment after running: bundle exec fastlane snapshot init
  # ── Then move SnapshotHelper.swift into ${APP_NAME}UITests/
  # ${APP_NAME}UITests:
  #   type: bundle.ui-testing
  #   platform: iOS
  #   sources:
  #     - path: ${APP_NAME}UITests
  #   dependencies:
  #     - target: $APP_NAME
  #   settings:
  #     base:
  #       PRODUCT_BUNDLE_IDENTIFIER: ${BUNDLE_ID}.uitests
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
# --- UI test target for screenshots ---
mkdir -p "${APP_NAME}UITests"
cat > "${APP_NAME}UITests/ScreenshotTests.swift" << SCREENSHOTSWIFT
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
        // Wait for the main view to load
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
SCREENSHOTSWIFT
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
cat > fastlane/capture_widgets.sh << 'CAPTUREWIDGETS'
#!/usr/bin/env bash
# Capture lock-screen (Live Activity) and home-screen (widget) screenshots.
#
# Prereqs:
#   • App must be built and installed on the target simulator (run beta/release
#     lane first, or `xcodebuild build -destination` into the sim).
#   • The home-screen widget must be placed ONCE manually on the simulator — this
#     persists in simulator state across boots. (Simulator → long-press → add widget.)
#   • App should honor launch arg -WIDGET_DEMO_MODE YES to auto-start a
#     deterministic Live Activity for capture.
#
# Usage (called by `fastlane widget_screenshots`):
#   ./fastlane/capture_widgets.sh "iPhone 17 Pro Max" com.example.app "fastlane/screenshots/en-US/iPhone 6.9\" Display"
set -euo pipefail

DEVICE="${1:?device name required (e.g. 'iPhone 17 Pro Max')}"
BUNDLE_ID="${2:?bundle identifier required}"
OUTPUT_DIR="${3:?output directory required}"

mkdir -p "$OUTPUT_DIR"

echo "📱 Booting $DEVICE…"
xcrun simctl boot "$DEVICE" 2>/dev/null || true
open -a Simulator
xcrun simctl bootstatus "$DEVICE" -b >/dev/null

echo "🕘 Overriding status bar (9:41, full signal, charged, no carrier/5G)…"
# --dataNetwork hide hides the 5G/LTE label (otherwise the Wi-Fi icon gets
# pushed to a second row in Control Center). --operatorName "" blanks the
# carrier text. Together these produce the cleanest App Store status bar.
xcrun simctl status_bar "$DEVICE" override \
  --time "9:41" --dataNetwork hide --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiMode active --wifiBars 3 \
  --operatorName ""

echo "🚀 Launching $BUNDLE_ID with -WIDGET_DEMO_MODE YES…"
xcrun simctl launch "$DEVICE" "$BUNDLE_ID" -WIDGET_DEMO_MODE YES -FASTLANE_SNAPSHOT YES >/dev/null
sleep 4  # let Live Activity start + render

echo "🔒 Locking screen (Cmd+L in Simulator)…"
osascript <<'APPLESCRIPT'
tell application "Simulator" to activate
delay 0.4
tell application "System Events" to keystroke "l" using command down
APPLESCRIPT
sleep 2

LOCK_PNG="$OUTPUT_DIR/90_LockScreen_LiveActivity.png"
echo "📸 Capturing lock screen → $LOCK_PNG"
xcrun simctl io "$DEVICE" screenshot "$LOCK_PNG"

echo "🔓 Unlocking (Cmd+Shift+H twice → home)…"
osascript <<'APPLESCRIPT'
tell application "Simulator" to activate
delay 0.3
tell application "System Events"
  keystroke "h" using {command down, shift down}
  delay 0.5
  keystroke "h" using {command down, shift down}
end tell
APPLESCRIPT
sleep 2

HOME_PNG="$OUTPUT_DIR/91_HomeScreen_Widget.png"
echo "📸 Capturing home screen → $HOME_PNG"
xcrun simctl io "$DEVICE" screenshot "$HOME_PNG"

echo ""
echo "✅ Captured:"
echo "   • $LOCK_PNG"
echo "   • $HOME_PNG"
echo ""
echo "Next: run 'bundle exec fastlane frame_screenshots' to apply Apple Frames,"
echo "or they'll be framed automatically if you invoked via widget_screenshots lane."
CAPTUREWIDGETS
chmod +x fastlane/capture_widgets.sh

cat > fastlane/capture_control_center.sh << 'CAPTURECC'
#!/usr/bin/env bash
# Capture iOS Control Center screenshot via simctl + Quartz mouse drag.
#
# Worth running only if your app ships a Control Widget (ControlKit, iOS 18+).
# If not, Control Center shows only iOS defaults — no app-specific marketing value.
#
# Prereqs:
#   • Your terminal app needs Accessibility permission to send synthesized mouse
#     events. macOS prompts the first time you run this. Grant it in:
#       System Settings → Privacy & Security → Accessibility → enable Terminal/iTerm
#   • Swift on PATH (`/usr/bin/swift`, ships with Xcode Command Line Tools).
#   • App built + installed on the target simulator if your Control Widget needs
#     the host app installed to register itself.
#
# Usage (called by `fastlane control_center_screenshot`):
#   ./fastlane/capture_control_center.sh "iPhone 17 Pro Max" "fastlane/screenshots/en-US/iPhone 6.9\" Display"
set -euo pipefail

DEVICE="${1:?device name required (e.g. 'iPhone 17 Pro Max')}"
OUTPUT_DIR="${2:?output directory required}"
mkdir -p "$OUTPUT_DIR"

echo "📱 Booting $DEVICE…"
xcrun simctl boot "$DEVICE" 2>/dev/null || true
open -a Simulator
xcrun simctl bootstatus "$DEVICE" -b >/dev/null

echo "🕘 Overriding status bar (9:41, full signal, charged, no carrier/5G)…"
# --dataNetwork hide hides the 5G/LTE label (otherwise the Wi-Fi icon gets
# pushed to a second row in Control Center). --operatorName "" blanks the
# carrier text. Together these produce the cleanest App Store status bar.
xcrun simctl status_bar "$DEVICE" override \
  --time "9:41" --dataNetwork hide --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiMode active --wifiBars 3 \
  --operatorName ""

# Make sure we're on home (not in any app)
osascript <<'APPLESCRIPT'
tell application "Simulator" to activate
delay 0.4
tell application "System Events" to keystroke "h" using {command down, shift down}
APPLESCRIPT
sleep 1

# Read the Simulator window's screen position + size
WIN_GEOM="$(osascript <<'APPLESCRIPT'
tell application "System Events"
  tell process "Simulator"
    set winPos to position of window 1
    set winSize to size of window 1
    return ((item 1 of winPos) as text) & "," & ((item 2 of winPos) as text) & "," & ((item 1 of winSize) as text) & "," & ((item 2 of winSize) as text)
  end tell
end tell
APPLESCRIPT
)"
IFS=',' read -r WIN_X WIN_Y WIN_W WIN_H <<< "$WIN_GEOM"
echo "Simulator window: ${WIN_X},${WIN_Y}  ${WIN_W}×${WIN_H}"

# Title bar ~28pt; swipe origin = right edge of status bar; pull down ~600pt
TITLE_BAR=28
START_X=$(( WIN_X + WIN_W - 40 ))
START_Y=$(( WIN_Y + TITLE_BAR + 8 ))
END_Y=$(( WIN_Y + TITLE_BAR + 600 ))

echo "🔽 Swiping ($START_X, $START_Y) → ($START_X, $END_Y) to invoke Control Center…"
osascript -e 'tell application "Simulator" to activate'
sleep 0.4

swift - "$START_X" "$START_Y" "$START_X" "$END_Y" <<'SWIFTEOF'
import CoreGraphics
import Foundation
let args = CommandLine.arguments
guard args.count >= 5,
      let sx = Double(args[1]), let sy = Double(args[2]),
      let ex = Double(args[3]), let ey = Double(args[4])
else { fputs("usage: drag sx sy ex ey\n", stderr); exit(1) }
func post(_ type: CGEventType, _ x: Double, _ y: Double) {
    CGEvent(mouseEventSource: nil, mouseType: type,
            mouseCursorPosition: CGPoint(x: x, y: y),
            mouseButton: .left)?.post(tap: .cghidEventTap)
}
post(.leftMouseDown, sx, sy)
Thread.sleep(forTimeInterval: 0.05)
let steps = 25
for i in 1...steps {
    let t = Double(i) / Double(steps)
    post(.leftMouseDragged, sx + (ex - sx) * t, sy + (ey - sy) * t)
    Thread.sleep(forTimeInterval: 0.012)
}
post(.leftMouseUp, ex, ey)
SWIFTEOF

sleep 1.5  # let Control Center settle into open state

CC_PNG="$OUTPUT_DIR/92_ControlCenter.png"
echo "📸 Capturing Control Center → $CC_PNG"
xcrun simctl io "$DEVICE" screenshot "$CC_PNG"

# Dismiss Control Center
osascript -e 'tell application "Simulator" to activate' \
          -e 'tell application "System Events" to keystroke "h" using {command down, shift down}'

echo ""
echo "✅ Captured: $CC_PNG"
echo ""
echo "Tip: if Control Center didn't open, your terminal probably lacks Accessibility"
echo "     permission. Grant it in System Settings → Privacy & Security → Accessibility,"
echo "     then re-run."
CAPTURECC
chmod +x fastlane/capture_control_center.sh

# --- appshot-cli scaffolding (Track B: captioned + gradient marketing screenshots) ---
mkdir -p fastlane/appshot/.appshot/captions
mkdir -p fastlane/appshot/screenshots/iphone fastlane/appshot/screenshots/ipad
touch fastlane/appshot/screenshots/iphone/.gitkeep fastlane/appshot/screenshots/ipad/.gitkeep
cat > fastlane/appshot/.appshot/config.json << 'APPSHOTCONFIG'
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
APPSHOTCONFIG
cat > fastlane/appshot/.appshot/captions/iphone.json << 'IPHONECAPTIONS'
{
  "01_HomeScreen.png": {
    "en": "Your headline here"
  },
  "02_KeyFeature.png": {
    "en": "What makes the app worth it"
  }
}
IPHONECAPTIONS
cat > fastlane/appshot/.appshot/captions/ipad.json << 'IPADCAPTIONS'
{
  "01_HomeScreen.png": {
    "en": "Your headline here"
  },
  "02_KeyFeature.png": {
    "en": "What makes the app worth it"
  }
}
IPADCAPTIONS

mkdir -p scripts
cat > scripts/patch-appshot.sh << 'PATCHAPPSHOT'
#!/usr/bin/env bash
# Patch the globally-installed appshot-cli so caption typography matches your
# project's design. Patches modify node_modules/, so a fresh `npm install -g`
# clobbers them — re-run this script after any appshot upgrade.
#
# Why patch at all:
#   appshot v2 caps caption font size at 86px (iPhone) / 88px (iPad). That's
#   too small to read at App Store thumbnail size and too small to force
#   readable line wraps via the chars-per-line heuristic.
#
# Tune to your design:
#   APPSHOT_IPHONE_FONT=120 APPSHOT_IPAD_FONT=140 ./scripts/patch-appshot.sh
#
# Defaults (115/130) were chosen for the bootstrapped sunset gradient + "New
# York Small Bold" caption. Adjust upward for shorter captions or downward for
# longer ones.
set -euo pipefail

IPHONE_FONT="${APPSHOT_IPHONE_FONT:-115}"
IPAD_FONT="${APPSHOT_IPAD_FONT:-130}"

APPSHOT_DIR="$(dirname "$(readlink -f "$(command -v appshot)" 2>/dev/null || command -v appshot)" )/../lib/node_modules/appshot-cli"
if [ ! -d "$APPSHOT_DIR" ]; then
  APPSHOT_DIR="/opt/homebrew/lib/node_modules/appshot-cli"
fi
if [ ! -d "$APPSHOT_DIR" ]; then
  echo "❌ Could not locate appshot-cli install. Tried: $APPSHOT_DIR"
  echo "   Install with: npm install -g appshot-cli"
  exit 1
fi

patch_size() {
  local file="$1" size="$2"
  if [ ! -f "$file" ]; then
    echo "❌ Missing $file"
    exit 1
  fi
  cp -n "$file" "${file}.bak" 2>/dev/null || true
  sed -i '' -E "s/fontMin: [0-9]+/fontMin: ${size}/" "$file"
  sed -i '' -E "s/fontMax: [0-9]+/fontMax: ${size}/" "$file"
  echo "✅ $(basename "$file"): fontMin=${size}, fontMax=${size}"
}

echo "Patching appshot-cli at $APPSHOT_DIR"
patch_size "$APPSHOT_DIR/dist/core/device-strategies/iphone.js" "$IPHONE_FONT"
patch_size "$APPSHOT_DIR/dist/core/device-strategies/ipad.js"   "$IPAD_FONT"
echo ""
echo "Done. Re-run after any 'npm install -g appshot-cli'."
PATCHAPPSHOT
chmod +x scripts/patch-appshot.sh

cat > fastlane/Fastfile << 'FASTFILE'
default_platform(:ios)

# Defense-in-depth: ensure UTF-8 locale even if the lane is invoked without
# the LC_ALL/LANG export prefix. Without this, gym crashes on any non-ASCII
# byte in build logs (`invalid byte sequence in US-ASCII`). The slash
# commands also export these, but a lane invoked directly would otherwise
# inherit whatever the shell has.
before_all do
  ENV["LC_ALL"] ||= "en_US.UTF-8"
  ENV["LANG"] ||= "en_US.UTF-8"
  ENV["LANGUAGE"] ||= "en_US.UTF-8"
end

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
    # See ios-project-playbook.md §4.1 for multi-target signing.
    build_app(
      scheme: Dir.glob("*.xcodeproj").first.sub(".xcodeproj", ""),
      export_method: "app-store",
      export_options: {
        provisioningProfiles: {
          CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier) =>
            ENV["PROVISIONING_PROFILE_NAME"]
          # Add extension bundle IDs here if needed:
          # "com.example.appname.widgets" => "AppName Widgets App Store"
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
      skip_metadata: false,
      force: true,
      precheck_include_in_app_purchases: false,
      submit_for_review: false,
      automatic_release: false
    )
  end

  desc "Capture screenshots on all required device sizes and apply Apple Frames"
  lane :screenshots do
    capture_screenshots(
      scheme: Dir.glob("*.xcodeproj").first.sub(".xcodeproj", "") + "UITests"
    )
    frame_screenshots
  end

  desc "Apply Apple Frames to captured screenshots (requires frames-cli on PATH)"
  lane :frame_screenshots do
    Dir.glob("../fastlane/screenshots/en-US/*/").each do |dir|
      # Preserve raws before first framing so re-framing or re-captioning later
      # doesn't require re-capturing on the simulator. Snapshot once; frames
      # CLI's `_framed.png` sibling convention preserves the framed step too.
      raw_dir = "#{dir}raw"
      if !Dir.exist?(raw_dir) || Dir.empty?(raw_dir)
        sh("mkdir -p #{raw_dir.shellescape}")
        Dir.glob("#{dir}*.png").reject { |f| f.end_with?("_framed.png") }.each do |f|
          sh("cp #{f.shellescape} #{raw_dir.shellescape}/")
        end
      end
      sh("frames -o #{dir.shellescape} #{dir.shellescape}*.png")
    end
  end

  desc "Caption framed screenshots with appshot-cli (run once per locale)"
  lane :appshot_screenshots do |options|
    locale = options[:locale] || "en-US"
    lang   = options[:lang]   || "en"

    iphone_src = "../fastlane/screenshots/#{locale}/iPhone 6.9\" Display"
    ipad_src   = "../fastlane/screenshots/#{locale}/iPad 13\" Display"
    iphone_in  = "../fastlane/appshot/screenshots/iphone"
    ipad_in    = "../fastlane/appshot/screenshots/ipad"

    sh("rm -f #{iphone_in.shellescape}/*.png #{ipad_in.shellescape}/*.png 2>/dev/null || true")

    # Stage framed PNGs into appshot input, dropping the `_framed` suffix so
    # caption JSON keys (e.g. "01_HomeScreen.png") match the staged filenames.
    Dir.glob("#{iphone_src}/*_framed.png").each do |f|
      dest = "#{iphone_in}/#{File.basename(f).sub('_framed.png', '.png')}"
      sh("cp #{f.shellescape} #{dest.shellescape}")
    end
    Dir.glob("#{ipad_src}/*_framed.png").each do |f|
      dest = "#{ipad_in}/#{File.basename(f).sub('_framed.png', '.png')}"
      sh("cp #{f.shellescape} #{dest.shellescape}")
    end

    Dir.chdir("../fastlane/appshot") do
      sh("appshot build --no-frame --langs #{lang}")
    end

    # Copy captioned output back. The unframed-raw originals (01_X.png) get
    # overwritten — recover from screenshots/<locale>/<device>/raw/ if needed.
    iphone_out = "../fastlane/appshot/final/iphone/#{lang}"
    ipad_out   = "../fastlane/appshot/final/ipad/#{lang}"
    sh("cp #{iphone_out.shellescape}/*.png \"#{iphone_src}\"/") if Dir.exist?(iphone_out)
    sh("cp #{ipad_out.shellescape}/*.png \"#{ipad_src}\"/")     if Dir.exist?(ipad_out)
  end

  desc "Capture lock-screen (Live Activity) and home-screen (widget) shots via simctl"
  lane :widget_screenshots do |options|
    device = options[:device] || "iPhone 17 Pro Max"
    bundle_id = CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier)
    output_dir = options[:output] || "fastlane/screenshots/en-US/iPhone 6.9\" Display"
    sh("../fastlane/capture_widgets.sh #{device.shellescape} #{bundle_id.shellescape} #{output_dir.shellescape}")
    frame_screenshots if options[:frame] != false
  end

  desc "Capture Control Center (with your Control Widget) via Quartz mouse drag"
  lane :control_center_screenshot do |options|
    device = options[:device] || "iPhone 17 Pro Max"
    output_dir = options[:output] || "fastlane/screenshots/en-US/iPhone 6.9\" Display"
    sh("../fastlane/capture_control_center.sh #{device.shellescape} #{output_dir.shellescape}")
    frame_screenshots if options[:frame] != false
  end

  desc "Sync metadata to App Store Connect (no binary, no screenshots)"
  lane :upload_metadata do
    app_store_connect_api_key(
      key_id: ENV["ASC_KEY_ID"],
      issuer_id: ENV["ASC_ISSUER_ID"],
      key_filepath: ENV["ASC_KEY_FILEPATH"]
    )
    deliver(
      skip_binary_upload: true,
      skip_screenshots: true,
      force: true
    )
  end

  desc "Upload screenshots to App Store Connect (no binary, no metadata)"
  lane :upload_screenshots do
    app_store_connect_api_key(
      key_id: ENV["ASC_KEY_ID"],
      issuer_id: ENV["ASC_ISSUER_ID"],
      key_filepath: ENV["ASC_KEY_FILEPATH"]
    )
    deliver(
      skip_binary_upload: true,
      skip_metadata: true,
      overwrite_screenshots: true,
      force: true
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
            -destination 'platform=iOS Simulator,name=__PRIMARY_SIM__' \
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
cat > .github/workflows/release.yml << 'RELEASE'
name: App Store Release
on:
  workflow_dispatch:
concurrency:
  group: release
  cancel-in-progress: false
jobs:
  release:
    name: Build & Upload to App Store
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
      - name: Build & Upload to App Store
        run: bundle exec fastlane release
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
RELEASE
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
# ASC character limits: name 30, subtitle 30, description 4000,
# keywords 100 (comma-separated, no spaces after commas),
# release_notes 4000, promotional_text 170
mkdir -p fastlane/metadata/en-US
echo "$APP_NAME" > fastlane/metadata/en-US/name.txt
cat > fastlane/metadata/en-US/subtitle.txt << 'SUBTITLE'
SUBTITLE
cat > fastlane/metadata/en-US/description.txt << METADESC
$APP_NAME — [one-sentence value proposition].

[Describe the core experience in 2-3 sentences. What does the app do and why should someone download it?]

Key features:
- [Feature 1]
- [Feature 2]
- [Feature 3]
METADESC
cat > fastlane/metadata/en-US/keywords.txt << 'KEYWORDS'
KEYWORDS
echo "Initial release." > fastlane/metadata/en-US/release_notes.txt
echo "https://$ORG.github.io/$REPO_NAME/privacy.html" > fastlane/metadata/en-US/privacy_url.txt
echo "https://$ORG.github.io/$REPO_NAME/" > fastlane/metadata/en-US/support_url.txt
cat > fastlane/metadata/en-US/promotional_text.txt << 'PROMO'
PROMO
echo "https://$ORG.github.io/$REPO_NAME/" > fastlane/metadata/en-US/marketing_url.txt
# --- Fastlane Deliverfile ---
cat > fastlane/Deliverfile << 'DELIVERFILE'
app_identifier CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier)
force true  # Skip interactive HTML preview (required for non-interactive sessions)
submit_for_review false
automatic_release false
precheck_include_in_app_purchases false
DELIVERFILE
# --- Fastlane Snapfile ---
cat > fastlane/Snapfile << SNAPFILE
# Only the two ASC-accepted submission sizes — Apple auto-scales to everything smaller
devices([
  "iPhone 17 Pro Max",        # 6.9" — REQUIRED for submission (1320x2868)
  "iPad Pro 13-inch (M5)"     # 13"  — REQUIRED if app supports iPad (2064x2752)
])

languages(["en-US"])

scheme("${APP_NAME}UITests")

output_directory("./fastlane/screenshots")
clear_previous_screenshots(true)

# Clean status bar (removes carrier, sets time to 9:41, full battery)
override_status_bar(true)
SNAPFILE
# --- Screenshot directory ---
mkdir -p fastlane/screenshots/en-US
touch fastlane/screenshots/.gitkeep
# --- Release notes draft ---
cat > release-notes-draft.md << 'RELNOTES'
# Release Notes Draft
Track user-facing changes here between App Store submissions.
Claude Code should update this at the end of every session with significant work.
## Next Version (unreleased)
- Initial release
RELNOTES
# --- Work log (session diary, gitignored) ---
cat > WORKLOG.md << WORKLOG
# ${APP_NAME} Work Log

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
cat > .claude/commands/release.md << 'RELEASECMD'
Submit the current state to App Store Connect from this local machine.

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
2. **Verify metadata is populated and within ASC limits.** Check that `fastlane/metadata/en-US/`
   files are not empty placeholders. At minimum: name.txt, description.txt, keywords.txt,
   and release_notes.txt must have real content. Warn the user about any empty files.
   Validate character limits — reject if exceeded:
   - name.txt: 30 chars max
   - subtitle.txt: 30 chars max
   - description.txt: 4000 chars max
   - keywords.txt: 100 chars max (comma-separated, no spaces after commas)
   - release_notes.txt: 4000 chars max
   - promotional_text.txt: 170 chars max
3. **Sync metadata** to App Store Connect:
   `export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && set -a && source .env.fastlane && set +a && bundle exec fastlane upload_metadata`
4. Verify build compiles: build for iOS Simulator via XcodeBuildMCP
5. Run SwiftLint: `/opt/homebrew/bin/swiftlint lint --strict --quiet`
6. **Build and upload binary:**
   `export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && set -a && source .env.fastlane && set +a && bundle exec fastlane release`
7. Ask user if screenshots need uploading. If yes and `fastlane/screenshots/` has content:
   `bundle exec fastlane upload_screenshots`
   Otherwise remind them to upload manually in App Store Connect.
8. If upload succeeds, ask user if they want to tag this release (e.g. `v1.0.0`)
9. Push main with `[skip ci]` to sync remote without triggering any workflows
10. Update "Current State" in CLAUDE.md with the release

Fallback if local build/upload fails:
- Restore any project files modified by fastlane: `git checkout -- *.xcodeproj`
- Trigger the GitHub Actions workflow: `gh workflow run release.yml`
- Monitor: `gh run list --workflow=release.yml --limit 1`
RELEASECMD
cat > .claude/commands/preflight.md << 'PREFLIGHTCMD'
Pre-deploy gate — validate everything before kicking off a build/upload cycle.

Run this before /deploy or /release. Catches missing simulators, ASC character-limit
violations, and forgotten metadata fields — all of which fail late and waste a full
build cycle.

Steps:

1. **Simulator availability** — Run `xcrun simctl list devices available` and confirm
   the project's required simulators exist. Standard set:
   - iPhone 6.9" screenshots: iPhone 17 Pro Max
   - iPad 13" screenshots: iPad Pro 13-inch (M5)
   - Build/run target: __PRIMARY_SIM__
   Skip iPad checks if the project does not ship iPad. If a required sim is missing,
   FAIL — suggest `xcrun simctl create` or downloading the runtime via
   Xcode > Settings > Platforms.

2. **ASC metadata character limits** — For each locale directory under
   `fastlane/metadata/`, validate text files against ASC limits using `wc -m`
   (subtract 1 for trailing newline):
   - `name.txt` ≤ 30
   - `subtitle.txt` ≤ 30
   - `keywords.txt` ≤ 100
   - `description.txt` ≤ 4000
   - `release_notes.txt` ≤ 4000
   - `promotional_text.txt` ≤ 170
   Report file path, current count, and overage for any file over limit.

3. **Metadata field completeness** — For each locale dir, confirm BOTH
   `release_notes.txt` AND `promotional_text.txt` exist and are non-empty (not just
   whitespace, not just stale placeholders like "Initial release."). Catches
   multi-locale ships where a field gets forgotten on some locales.

4. **Git state** —
   - `git status` must be clean (warn if untracked files)
   - Current branch must NOT be `main` — should be `dev`, `release/*`, or feature/*
   - Branch should be pushed and up-to-date with origin

5. **Version sanity** — Read `MARKETING_VERSION` from `project.yml`. Ask the user
   what version they think they're shipping. If mismatch, FAIL.

6. **Build number** — Read `CURRENT_PROJECT_VERSION` from `project.yml`. Check whether
   a git tag like `v<MARKETING>-beta.<BUILD>` already exists. If yes, warn — the build
   number likely needs a bump.

Present results as a PASS / FAIL / WARN table:

```
## Preflight — v1.2.0 build 71

| Check | Status | Detail |
|---|---|---|
| Simulators | ✅ PASS | iPhone 17 Pro Max, iPad Pro 13" M5 available |
| Metadata char limits | ❌ FAIL | en-US/subtitle.txt: 31 chars (max 30) |
| Metadata completeness | ✅ PASS | All 12 locales have release_notes + promotional_text |
| Git state | ⚠️ WARN | On dev, 2 unpushed commits |
| Version | ✅ PASS | MARKETING_VERSION 1.2.0 matches |
| Build number | ✅ PASS | 71 (no existing tag) |

Overall: ❌ FAIL — fix metadata char limits before deploy.
```

If any check FAILs, refuse to proceed and offer to fix the failing items. Only after
all checks PASS (or the user explicitly overrides) should /deploy or /release be invoked.
PREFLIGHTCMD
# --- Copy playbook slash commands (except curate, which is playbook-only) ---
PLAYBOOK_DIR="$SCRIPT_DIR"
CMDS_SRC="$PLAYBOOK_DIR/.claude/commands"
if [[ -d "$CMDS_SRC" ]]; then
  for cmd in "$CMDS_SRC"/*.md; do
    cmd_name=$(basename "$cmd")
    [[ "$cmd_name" == "curate.md" ]] && continue  # playbook-only command
    cp "$cmd" .claude/commands/"$cmd_name"
  done
  echo "✓ Playbook slash commands copied (/inbox, /status, /wrapup, /context-health, /upgrade)"
fi
# --- Claude Code rules (path-scoped, auto-loaded) ---
RULES_SRC="$PLAYBOOK_DIR/.claude/rules"
if [[ -d "$RULES_SRC" ]]; then
  mkdir -p .claude/rules
  for rule in "$RULES_SRC"/*.md; do
    cp "$rule" .claude/rules/
  done
  # Substitute playbook path into the inbox rule so sessions know where to write
  if [[ -f .claude/rules/playbook-inbox.md ]]; then
    sed -i '' "s|PLAYBOOK_PATH|$PLAYBOOK_DIR|g" .claude/rules/playbook-inbox.md
  fi
  echo "✓ Claude Code rules copied to .claude/rules/"
else
  echo "⚠️  No .claude/rules/ found in playbook — skipping rule generation"
fi
# --- Substitute PRIMARY_SIM into emitted files ---
# Marker substitution (always runs, even with default value)
for f in .github/workflows/build-check.yml .claude/commands/preflight.md; do
  [[ -f "$f" ]] && sed -i '' "s|__PRIMARY_SIM__|${PRIMARY_SIM}|g" "$f"
done
# Literal substitution in copied rule files (only when overridden)
if [[ "${PRIMARY_SIM}" != "iPhone 17 Pro" ]]; then
  for f in .claude/rules/build-deploy.md .claude/rules/testing.md; do
    [[ -f "$f" ]] && sed -i '' "s|iPhone 17 Pro|${PRIMARY_SIM}|g" "$f"
  done
fi
# --- Playbook version marker (for /upgrade command) ---
cat > .playbook-version << 'PBVERSION'
# Last synced with playbook CHANGELOG
PBVERSION
echo "$(date +%Y-%m-%d)" >> .playbook-version
echo "✓ Playbook version marker created"
# --- Install Lefthook hooks ---
if command -v lefthook &> /dev/null; then
  lefthook install
else
  echo "⚠️  Lefthook not installed. Run: brew install lefthook && lefthook install"
fi
# --- Generate CLAUDE.md from template ---
TEMPLATE="$SCRIPT_DIR/CLAUDE-TEMPLATE.md"
if [[ -f "$TEMPLATE" ]]; then
  APP_NAME_LOWER=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]')
  sed -e "s|\[APP_NAME\]|$APP_NAME|g" \
      -e "s|\[com\.example\.appname\]|$BUNDLE_ID|g" \
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
# --- Verify project compiles ---
echo "🔨 Verifying project compiles..."
xcodegen generate --quiet 2>/dev/null
if xcodebuild build -scheme "$APP_NAME" -destination 'generic/platform=iOS Simulator' -quiet 2>/dev/null; then
  echo "✓ Build verified"
else
  echo "⚠️  Build verification failed — project may need manual fixes. Run 'xcodebuild build' for details."
fi
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