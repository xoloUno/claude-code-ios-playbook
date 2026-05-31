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
   and `provisioningProfiles` is installed (__PROVISIONING_PROFILES__). If any are missing, STOP — do not run fastlane.
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
