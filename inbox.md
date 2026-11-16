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

**Next entry number:** 129

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

### #122 — 2026-11-16 — Kendibah (kendibah-web)

**Category:** gotcha
**Context:** Making a feature-comparison table and a support form readable on iPhone, and moving
the site from Inter/Lora to Helvetica.
**Lesson:** (1) To stack a table into one block per row with `td::before { content:
attr(data-label) }`, position the label absolutely and pad the cell. Making the `td` a grid or
flex container splits "Yes, with a <a>TV setting</a>" into separate items that wrap apart. A
label like "Google TV" needed 6.5em at 15 px. (2) Inputs, selects and textareas need a
`font-size` of 16 px or more, or iOS Safari zooms in on focus. (3) Helvetica has no medium
weight, so `font-weight: 500` falls back to regular; list `"Helvetica Neue"` first so Apple
devices get its Medium.
**Suggested action:** Add to the web/marketing-site notes.

### #121 — 2026-11-16 — Kendibah (kendibah-web)

**Category:** pattern
**Context:** Checking a static HTML page at phone width before opening a PR, in a desktop-app
session.
**Lesson:** The built-in browser loaded a local static site through a `.claude/launch.json`
entry running `python3 -m http.server 8765 --bind 127.0.0.1` and `preview_start`, although the
browser skill says it can't reach servers Claude starts (that holds for cloud sessions).
`resize_window` (mobile 375×812, a custom 320×640, then desktop) plus one JS check,
`document.documentElement.scrollWidth === innerWidth` and a scan for elements whose
`getBoundingClientRect().right > innerWidth`, gives a pass/fail for sideways scrolling that
screenshots don't. The first `navigate` inside a `browser_batch` failed; a standalone `navigate`
worked. Synthetic events need `{bubbles: true}` to reach a form-level listener. The global
gitignore doesn't cover `launch.json`, so delete it before committing.
**Suggested action:** Add to the web/marketing-site notes as the standard phone-width check.

### #119 — 2026-11-16 — Kendibah (kendibah-web)

**Category:** gotcha
**Context:** Adding a support form to the static kendibah.com site (Cloudflare Pages) that
builds a `mailto:` link with the TV brand, model and message filled in.
**Lesson:** Cloudflare's email obfuscation runs only on the custom domain, not on the
`*.pages.dev` branch previews, so a preview can't show whether a mailto feature survives it. On
kendibah.com it rewrote the plain `mailto:` link to `/cdn-cgi/l/email-protection#…` and injected
`email-decode.min.js`, but left alone an address the script builds (`'hello' + '@' +
'xolo.uno'`). Verify mailto features on the live domain after merging, and read the built
link's `href` in the browser instead of clicking it, which would open the owner's Mail.
**Suggested action:** In the marketing/support-site notes: build email addresses in script for
mailto features, and check them on the custom domain, not the preview.

### #99 — 2026-11-13 — Kendibah

**Category:** tooling
**Context:** Composing captioned App Store screenshots with shotsmith 0.2.0 for the iPhone medium and large displays and iPhone Duo.
**Lesson:** shotsmith 0.2.0's device registry has only `iphone` (1320 × 2868) and `ipad` (2064 × 2752), so it can't compose the now-required medium display (1206 × 2622) or any iPhone Duo size. Its `compose` also saves the RGBA canvas as is, so every PNG carries an alpha channel, which Apple's spec page says screenshots can't have. Its per-image function takes any canvas: a small driver run on shotsmith's own interpreter (the `#!` line of `$(command -v shotsmith)`) can call `shotsmith.compose._compose_one(canvas_size=…)` per canvas and save with `.convert("RGB")`. `Captions.lookup(device_key=…)` honors `caption_<key>` for any key. Patching `compose._add_dither` gives coarser grain: noise drawn at 1/3 size and enlarged with bicubic. Kendibah's `scripts/compose-screenshots.py` does this, adding layered two-device shots and a check that fails when a caption would be cut off with an ellipsis.
**Suggested action:** Add device profiles for the medium display and iPhone Duo (both orientations) to shotsmith, save RGB, and expose grain size; until then, point `screenshot-pipeline.md` at the driver pattern.

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
