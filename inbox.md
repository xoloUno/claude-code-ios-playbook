# Playbook Inbox

Lessons learned, gotchas, suggestions, and patterns discovered during Claude Code
sessions across all projects. Entries are written automatically by sessions in other
project directories. Periodically review this file in a dedicated playbook session to
curate worthwhile additions into the playbook, templates, or rules.

## How entries get here

Each bootstrapped project has a `.claude/rules/playbook-inbox.md` rule that tells
Claude Code to add entries here when it discovers something worth capturing.

## Curation process

In a Claude Code session in the `_playbook/` directory:
1. Read this file
2. Give each unnumbered entry the next entry number (below), raising the counter each time,
   then sort all entries newest first, with higher numbers first on the same date
3. For each entry, decide: **adopt** (update playbook/template/rules), **defer**, or **discard**
4. Adopted entries → make the change, then delete the entry
5. Deferred entries → leave them for next review
6. Discarded entries → delete them
7. If all entries are processed, leave only this header

## Entry format

**Next entry number:** 76

Capturing sessions append new entries at the bottom of this file without a number; curation
numbers them. Numbers are permanent IDs: never renumber an entry or reuse a removed number,
and keep the counter when the inbox is empty. Use the IDs when discussing entries. A numbered
entry's heading reads `### #[NUMBER] — [DATE] — [PROJECT_NAME]`.

```markdown
### [DATE] — [PROJECT_NAME]

**Category:** gotcha | suggestion | pattern | correction | tooling
**Context:** [what was being done when this was discovered]
**Lesson:** [the actual insight — be specific]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

---

### #67 — 2026-11-03 — Flara
**Category:** suggestion
**Context:** After App Review approved 2.2.1, the plan was to bump `MARKETING_VERSION` to 2.3.0, per the Version Lifecycle rule. The only change waiting was one Swift line (the legal-pages base URL), metadata URLs and a description link fix, and the app's roadmap already used 2.3.0 for a feature tier. The owner asked whether this was really 2.2.2, and it shipped as 2.2.2.
**Lesson:** Brainstorm topic, not a settled lesson. Bumping to the next minor right after an approval guesses the next release's size before any work exists. A patch bump (2.2.1 → 2.2.2) is the smallest valid number that reopens the version train, and it can still be raised to 2.3.0 while that version is unsubmitted, once a feature lands. Bumping to minor by default can mislabel hotfixes and use up version numbers a roadmap has already assigned.
**Suggested action:** Discuss changing `packs/ios/rules/build-deploy.md` (Version Lifecycle, line 113) and `ios-project-playbook.md` §6.5 (lines 1515 and 1529) to: bump to the next patch after approval, and raise it to minor or major when feature work starts. Check first that App Store Connect lets you change a prepared version's number before submission.

### #61 — 2026-11-02 — KendibahApp
**Category:** suggestion
**Context:** Every `/deploy` run prompted for permission, even right after the owner approved
the upload in chat.
**Lesson:** The pack's deploy step is one inline command (`export PATH=… && export LC_ALL=… &&
set -a && source .env.fastlane && set +a && bundle exec fastlane beta`). It reads credentials
and uploads, so auto mode asks every time, and a prefix allow rule can't match it because it
starts with `export`. A project script (`scripts/testflight-upload.sh`) that checks for a clean
`main`, runs the lane with Homebrew Ruby, logs to `$TMPDIR`, prints the build number, and undoes
fastlane's pbxproj and Info.plist edits can be allowed by exact name in
`.claude/settings.local.json`. That removes the prompt and the manual restore step. The chat
approval per upload stays.
**Suggested action:** Have bootstrap emit `scripts/testflight-upload.sh` (and a release
counterpart), point `packs/ios/commands/deploy.md` and `release.md` at them, and mention the
optional local allow rule in getting-started.

### #28 — 2026-10-27 — DachipariApp
**Category:** gap
**Context:** `bootstrap.sh` produced an iPhone-first, portrait, iOS-only project (XcodeGen target, CI building only the iOS simulator, fastlane `platform :ios`). The spec is a tvOS + iPadOS app with Universal Purchase.
**Lesson:** A multiplatform app needs one XcodeGen target with `supportedDestinations: [iOS, tvOS]` (one bundle ID, so Universal Purchase works), `TARGETED_DEVICE_FAMILY` `2,3` for iPad + TV with no iPhone, and a CI build per platform. The playbook has no tvOS guidance, so each project has to retarget by hand.
**Suggested action:** Add a bootstrap platforms option (iphone / ipad / tvos) that sets destinations, device family, orientation and CI destinations, or note in getting-started.md what to change for non-iPhone apps.

### #26 — 2026-10-27 — DachipariApp
**Category:** gotcha
**Context:** Planning a tvOS + iPadOS camera app (Continuity Camera on Apple TV). The spike plan logged results to a JSONL file in Documents and assumed the TV could use two Continuity Cameras at once.
**Lesson:** WWDC23 session 10256 ("Discover Continuity Camera for tvOS") says `.documentDirectory` is in the tvOS headers but fails with a runtime error. tvOS apps should use only `.cachesDirectory`, which can be purged between launches. The same session says only one Continuity Camera can be connected to an Apple TV at a time. The SDK headers don't mention either limit.
**Suggested action:** If the playbook adds tvOS guidance, include both: Caches-only file storage on tvOS (pull logs before the app quits, or move data to iCloud), and a single Continuity Camera per Apple TV.
