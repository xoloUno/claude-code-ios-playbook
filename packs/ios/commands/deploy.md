Deploy the current state to TestFlight from this local machine.

Prerequisites — abort if any fail:
- This MUST be a local session (not cloud — cloud sessions cannot run fastlane)
- `.env.fastlane` must exist in the project root
- Must be on `main` branch (if not, its PR must merge first; see the core merge checklist)
- The working tree must be clean (`git status --porcelain` prints nothing)
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
6. Restore fastlane's project edits. fastlane sets the build number and signing at archive
   time without committing them, in `project.pbxproj` and sometimes in `Info.plist`, so
   restore just the ones that changed:
   `git diff --name-only -z -- '*.pbxproj' '*Info.plist' | xargs -0 git checkout --`.
   If `git status --porcelain` still lists changes, they aren't fastlane's: stop and ask
   the user.
7. Never commit to or push `main`. On a `chore/` branch, update "Current State" with the
   deploy in the project-owned part of the instructions file (`AGENTS.md` when it carries
   the playbook core markers, otherwise `CLAUDE.md`), add any commits fastlane left on
   `main`, and open a PR

Fallback if local build/upload fails:
- Restore fastlane's edits as in step 6
- Trigger the GitHub Actions workflow: `gh workflow run testflight.yml`
- Monitor: `gh run list --workflow=testflight.yml --limit 1`
