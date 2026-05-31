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
   and `provisioningProfiles` is installed (__PROVISIONING_PROFILES__). If any are missing, STOP — do not run fastlane.
   Tell the user which profiles are missing and that they need to download them from
   Apple Developer Portal → Profiles and copy them to `~/Library/MobileDevice/Provisioning Profiles/`.
   Offer to fall back to GitHub Actions instead.
2. **Verify metadata is populated and within ASC limits.** Check that the `fastlane/metadata/`
   locale dirs (__METADATA_LOCALES__) are not empty placeholders. At minimum: name.txt, description.txt, keywords.txt,
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
