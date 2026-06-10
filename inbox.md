# Playbook Inbox

Lessons learned, gotchas, suggestions, and patterns discovered during Claude Code
sessions across all projects. Entries are written automatically by sessions in other
project directories. Periodically review this file in a dedicated playbook session to
curate worthwhile additions into the playbook, templates, or rules.

## How entries get here

Each bootstrapped project has a `.claude/rules/playbook-inbox.md` rule that tells
Claude Code to append entries here when it discovers something worth capturing.

## Curation process

In a Claude Code session in the `_playbook/` directory:
1. Read this file
2. For each entry, decide: **adopt** (update playbook/template/rules), **defer**, or **discard**
3. Adopted entries → make the change, then delete the entry
4. Deferred entries → leave them for next review
5. Discarded entries → delete them
6. If all entries are processed, leave only this header

## Entry format

```markdown
### [DATE] — [PROJECT_NAME]

**Category:** gotcha | suggestion | pattern | correction | tooling
**Context:** [what was being done when this was discovered]
**Lesson:** [the actual insight — be specific]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

---

### 2026-04-27 — HVACApp

**Category:** pattern
**Context:** HVACApp is an internal-team field-ops app distributed via
TestFlight to a small group, never to the public App Store. Its app shape
is meaningfully different from the playbook's assumed solo-dev-public-app:
a single shared iCloud account across team devices, a `Device` @Model
registry, session switching with passcode protection for elevated roles,
role-based access (Owner/Manager/Technician), no StoreKit, no public app
icon urgency, no marketing screenshots, no privacy/terms hosting needed.

**Lesson:** "Internal/team-distributed app" is a distinct archetype the
playbook doesn't currently address. The playbook templates and slash
commands assume public-App-Store-bound apps (StoreKit setup as Phase 2,
detailed App Store metadata + screenshot + privacy hosting in Phase 5-6).
For internal apps, large chunks of the playbook are skippable, and other
patterns (multi-user session management, device registry, role-based
access, TestFlight-only distribution) are essential but unaddressed.

**Suggested action:** Add a dedicated section to `ios-project-playbook.md`
— maybe "Phase 8: Internal/team apps" or fold into Phase 4. Cover:
- Session manager + device registry pattern (HVACApp's `SessionManager`
  + `Device` @Model is a good reference)
- Role-based access (Owner > Manager > Technician permission ladder)
- Passcode-protected session switching (CryptoKit salted SHA-256)
- TestFlight-only distribution flow (no /release lane needed)
- Reactive `currentUser` from session store (computed property pattern,
  not stored `let` parameter)
- ChangeLog audit trail conventions
Also: `.env.project` could grow a `DISTRIBUTION_MODE=public|internal|enterprise`
that drives whether `/release`, `appshot`, `docs/legal` get installed.

---

### 2026-06-03 — Flara

**Category:** gotcha
**Context:** Re-capturing App Store screenshots with both iOS/watchOS 26.4 AND
26.5 sims installed (the same device names exist for two runtimes). The capture
scripts resolved the sim by `simctl list devices "<name>" available | head -1`
for locale + status-bar prep, but ran the actual capture via
`xcodebuild -destination "platform=iOS Simulator,name=<name>"`. With two
runtimes exposing the same name, the two resolvers landed on *different* sims:
simctl prepped one device while xcodebuild built/installed/ran on another. The
prepped sim kept a weeks-stale app install, and a Live Activity rendered the
*old* widget-extension UI even though HEAD had the new code — because the
installed `.appex` on that sim was stale.
**Lesson:** Name-based sim resolution is ambiguous the moment two runtimes are
installed; `simctl ... | head -1` and `xcodebuild -destination name=...` can
silently pick different devices. Resolve a UDID once and pin BOTH paths to it —
`simctl` ops on `$udid`, and `xcodebuild -destination "platform=iOS Simulator,id=$udid"`.
**Suggested action:** Update the bootstrap `capture-screenshots.sh` /
`capture-watch-screenshots.sh` templates to (a) accept an explicit UDID via env
var (`IPHONE_UDID` / `IPAD_UDID` / `WATCH_UDID`) and (b) pass `-destination id=<udid>`
to xcodebuild, never `name=`. Add a multi-runtime-ambiguity note to
`screenshot-pipeline.md`.

### 2026-06-03 — Flara

**Category:** pattern
**Context:** The stale-`.appex` above made the Live Activity show the old button.
The obvious fix — `simctl uninstall` + reinstall — was vetoed because it wipes
the user's manually pinned Home Screen widgets + Control Center button that the
manual-capture flow depends on (already a documented trap in
`screenshot-pipeline.md`).
**Lesson:** To refresh a stale app binary/extension on a sim WITHOUT losing
SpringBoard widget state, use an in-place upgrade install: `simctl install <udid>
<Fresh.app>` over the existing install (NO uninstall). It swaps the binary +
embedded extensions while preserving Home Screen layout, widget instances, and
Control Center assignments — exactly like an App Store update. Diagnose staleness
first by comparing the installed extension's mtime to DerivedData:
`stat "$(xcrun simctl get_app_container <udid> <bundleid> app)/PlugIns/<Ext>.appex/<Ext>"`.
And when recapturing a surface AFTER a UI change, add a human verification gate
("confirm the NEW UI is rendering before I capture") — it caught two stale
captures this session before they reached ASC.
**Suggested action:** Add to `screenshot-pipeline.md`: (1) the
in-place-install-vs-uninstall distinction for refreshing a stale binary while
preserving pinned widgets, (2) the appex-mtime staleness diagnostic, (3) the
verify-before-capture gate for manual recaptures of changed surfaces.

### 2026-06-03 — Flara

**Category:** tooling
**Context:** Running `bundle exec fastlane compose_screenshots` /
`upload_screenshots` from the Claude Code Bash tool (non-interactive shell).
**Lesson:** Two local-run gotchas. (1) The tool's shell put system Ruby 2.6
(`/usr/bin`) ahead of Homebrew Ruby on PATH, so `bundle` failed with "Could not
find 'bundler' (4.0.3)". Fix: `export PATH="/opt/homebrew/opt/ruby/bin:$PATH"`
before `bundle exec` — the project has no rbenv/mise and relies on Homebrew Ruby
being first, which an interactive login shell arranges but the tool shell did
not. (2) deliver's `sync_screenshots: true` is beta-gated: it hard-errors unless
`FASTLANE_ENABLE_BETA_DELIVER_SYNC_SCREENSHOTS=1` is set in the environment at
invocation — a lane that uses `sync_screenshots` does NOT set it itself.
**Suggested action:** For local iOS sessions, prepend the Homebrew Ruby bin to
PATH (or document the project's Ruby source) before fastlane. If a lane uses
`sync_screenshots`, either set `ENV["FASTLANE_ENABLE_BETA_DELIVER_SYNC_SCREENSHOTS"] = "1"`
inside the lane or document that it must be passed at invocation. Worth a
one-liner in `build-deploy.md`.

### 2026-06-03 — Flara

**Category:** suggestion
**Context:** Shipping a metadata/copy-only polish release (Flara v2.1.1) where
the binary (build 80) was already on TestFlight and device-verified — only App
Store text changed (description prices removed, release notes refreshed, review
notes trimmed).
**Lesson:** The `/release` command's `release` lane couples build + metadata +
submit into one path. Running it for a metadata-only change forces a redundant
new archive (new build number) and would submit a binary that is NOT the
device-verified one. We hand-ran `upload_metadata` + `submit_for_review`
instead — there's no single-command equivalent for "resubmit existing verified
build with new metadata."
**Suggested action:** Add a first-class metadata-only path to `/release` (e.g.
`/release --metadata-only`) that skips archiving, attaches the latest verified
TestFlight build to the version, syncs metadata, and submits. Polish/copy-only
resubmissions are common enough to deserve their own lane.
