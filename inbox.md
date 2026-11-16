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

**Next entry number:** 127

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

### #125 — 2026-11-16 — Kendibah

**Category:** gotcha
**Context:** Reviewing a parallel session's work after it merged its PR branch into another PR's
branch and resolved the conflicts.
**Lesson:** The session put new feature work (about 280 lines: four providers' settings and a
function moved to another file) into the conflict resolution of merge commit `75538d6`. Nothing
shows it: `git log` of either branch lists only the merge, the source PR's diff doesn't contain
it, and the merge review (Codex on the source branch's head) ran before it existed. `git show
--remerge-diff <merge>` lists exactly what a merge changed beyond the automatic merge, and
`--stat` gives the file list.
**Suggested action:** Core Git rule: keep new work in its own commit after the merge, never in a
merge's conflict resolution. In "Second opinions", have a review of a branch that contains merges
run `git show --remerge-diff` on each merge since the last review.

### #124 — 2026-11-16 — Kendibah

**Category:** tooling
**Context:** Reading files from other branches in the agent's zsh shell with
`B=origin/main; git show $B:Packages/KendibahKit/...`.
**Lesson:** zsh reads a colon right after a bare `$VAR` as a history modifier, so
`$B:Packages/...` applies `:P` (realpath) and git gets
`/Users/.../origin/mainackages/...`, then fails with "ambiguous argument … unknown revision or
path". The same happens for any path starting with a modifier letter (`:h`, `:t`, `:r`, `:e`,
`:a`, `:A`, `:l`, `:u`, `:q`, `:x`), for example `$REF:tests/…` or `$REF:assets/…`. Braces fix
it: `git show "${REF}:path"`. Bash doesn't do this, so a command written for bash breaks only in
zsh. It cost three failed calls in one session.
**Suggested action:** Add a line to the core's Git section or a shell-tips note: in zsh, write
`"${REF}:path"` for `git show` and `git cat-file`, never `$REF:path`.

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

### #117 — 2026-11-16 — Kendibah

**Category:** gotcha
**Context:** Extending another session's PR (#127) by merging a second PR's branch into its
worktree (`~/dev/<app>-worktrees/<name>`). The worktree was clean and at the pushed tip, so it
looked idle, but the owner said that PR's session was still working there.
**Lesson:** A clean worktree at the pushed tip doesn't mean nobody is in it, and a session's
reported cwd doesn't show which worktree it uses: that session reported the main checkout as
its cwd while it built in the worktree by absolute path. My merge-in-progress sat under its
builds for about 25 minutes. `list_sessions` does show it: a row with that `prNumber` and
`isRunning: true`. What recovered it: back up every touched path, reset the worktree to its
pushed commit, redo the work in a worktree of its own, message the session with the window,
and push only once it says it's done (a fast-forward).
**Suggested action:** Add to the core's Git or Session hygiene: before editing, merging into
or building in a worktree or branch you didn't create, check `list_sessions` for a running
session bound to its PR, and work in your own worktree until it's idle.

### #116 — 2026-11-16 — Kendibah

**Category:** tooling
**Context:** A Claude Desktop side session in a worktree (`.claude/worktrees/<name>`) finishing a
docs PR and following the core's "Handoffs and records" step for `MANUAL-TASKS.md` and
`WORKLOG.md`, which live gitignored in the main checkout.
**Lesson:** The desktop app's worktree guard blocks Edit and Write on main-checkout files ("Use
the worktree path instead"), and it refuses symlinks into the worktree as well. A worktree
session therefore can't keep those scratchpads, and getting around the guard through the shell
would defeat it. What worked: write the exact text to apply (the WORKLOG entry, the
MANUAL-TASKS lines) to the shared side-session notes folder, name that file in the wrap-up, and
have the owner start the follow-up session in the main checkout to apply it.
**Suggested action:** Add to the core's "Handoffs and records": a session that can't write the
main checkout's scratchpads leaves their text in the shared notes folder (or the PR body) and
says so in its report; the next main-checkout session applies it before other work.

### #105 — 2026-11-13 — Kendibah

**Category:** gotcha
**Context:** Under autonomy in the Claude desktop app with Auto-fix on: PR #117 waited only on Build Check, and the owner had approved a TestFlight upload to follow the merge.
**Lesson:** The desktop app's PR monitor wakes the session for CI failures, merge conflicts and review comments, but not when CI passes. The run passed, no event came, and the merge and upload waited about an hour until the owner asked why TestFlight had no new build. The session can't poll CI, so a turn that ends with "I'll merge when CI passes" makes a promise nothing will trigger.
**Suggested action:** In core "Autonomy", when a turn ends with a merge (or a follow-on step like an upload) waiting only on CI, say plainly that it resumes when the owner next messages, and offer GitHub auto-merge for that PR as the owner's choice (it covers the merge, not later steps).

### #99 — 2026-11-13 — Kendibah

**Category:** tooling
**Context:** Composing captioned App Store screenshots with shotsmith 0.2.0 for the iPhone medium and large displays and iPhone Duo.
**Lesson:** shotsmith 0.2.0's device registry has only `iphone` (1320 × 2868) and `ipad` (2064 × 2752), so it can't compose the now-required medium display (1206 × 2622) or any iPhone Duo size. Its `compose` also saves the RGBA canvas as is, so every PNG carries an alpha channel, which Apple's spec page says screenshots can't have. Its per-image function takes any canvas: a small driver run on shotsmith's own interpreter (the `#!` line of `$(command -v shotsmith)`) can call `shotsmith.compose._compose_one(canvas_size=…)` per canvas and save with `.convert("RGB")`. `Captions.lookup(device_key=…)` honors `caption_<key>` for any key. Patching `compose._add_dither` gives coarser grain: noise drawn at 1/3 size and enlarged with bicubic. Kendibah's `scripts/compose-screenshots.py` does this, adding layered two-device shots and a check that fails when a caption would be cut off with an ellipsis.
**Suggested action:** Add device profiles for the medium display and iPhone Duo (both orientations) to shotsmith, save RGB, and expose grain size; until then, point `screenshot-pipeline.md` at the driver pattern.

### #89 — 2026-11-11 — Kendibah

**Category:** tooling
**Context:** Under playbook autonomy, an agent tried to finish a PR (final push without `[skip ci]` plus `gh pr ready`) after the owner had only asked for UI changes.
**Lesson:** Claude Code's auto-mode classifier denied it as an "unrequested commit in a connected app", even though the playbook's Autonomy section allows merging a PR that meets the checklist. Routine commits and `[skip ci]` pushes to the task branch went through; the merge-prep step didn't. Ask the owner "Merge PR #N?" once the checklist is met rather than relying on the autonomy rule, and keep doing independent work meanwhile.
**Suggested action:** Note in the core's Autonomy section that the host may still require an explicit go-ahead for the final merge steps, so agents ask once instead of retrying.

### #88 — 2026-11-11 — Kendibah

**Category:** gotcha
**Context:** A PR's Build Check showed "failure"; the agent nearly debugged code.
**Lesson:** A GitHub-hosted macOS job that is never picked up runs about 15 minutes with zero steps, then the run concludes `failure` while the job reads `cancelled`. Its check-run annotation says "The job was not acquired by Runner of type hosted even after multiple attempts": runner capacity, not code and not billing (a billing block names payments or a spending limit). Read the annotation (`gh api repos/<o>/<r>/check-runs/<job-id>/annotations`) before debugging, and re-run. Also check a PR's last CI result before calling a branch green; this one sat failed for a day unnoticed because later pushes carried `[skip ci]`.
**Suggested action:** Extend the core's "A CI job that fails in seconds with no steps may be a billing block" line to cover this runner-not-acquired case.

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
