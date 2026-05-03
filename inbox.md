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

### 2026-04-27 — HVACApp

**Category:** pattern
**Context:** Mid-session, Erik asked to design a parallel-agent
worktree workflow: (1) coordinator decomposes work into N independent
tasks, (2) creates `.worktrees/task-NN` per task, (3) spawns Task agents
in parallel via `run_in_background: true`, (4) opens PRs for green ones,
(5) merges and cleans up worktrees. Implemented as
`.claude/rules/parallel-worktrees.md` + `.claude/commands/parallel-tasks.md`
in HVACApp.

**Lesson:** For multi-file refactors with N truly independent tasks
(SwiftLint cleanup across 30+ files, multi-platform build verification,
adding tests for N independent modules), worktree-parallelism with
background agents is a real efficiency multiplier. Each agent works in
isolation in its own checkout, can build/lint/test what it changed, and
opens a PR. The coordinator polls completions (no sleep/poll — runtime
notifies on background agent completion), then squash-merges greens and
surfaces reds for triage. Cap at 8 to avoid CI rate-limits and disk
exhaustion (~500MB per worktree with DerivedData).

NOT a fit for: cohesive single-feature changes, sequential dependencies,
quick (<10 min) work where setup overhead dwarfs savings, tasks that
edit the same file (merge conflicts).

**Suggested action:** Port the pattern to the playbook as a stock
slash command + rule. The slash command (`/parallel-tasks`) takes a
markdown task spec file with allow-lists and forbid-lists per task,
validates non-overlap, spawns agents, manages PR lifecycle, runs
preflight on main. Worth a section in `ios-project-playbook.md` Phase 3
(Development Conventions) covering when to reach for this vs sequential
edits. The HVACApp implementation is at
`/Users/erikj/Documents/JJ AIR/99-WIP/erik/App/HVACApp/.claude/{rules,commands}/parallel-*`
— copy verbatim or refine.

### 2026-04-28 — Flara

**Category:** pattern
**Context:** Building first-ever ASC watchOS screenshot pipeline for
Flara v2.0. No existing automation in the project, no good
off-the-shelf option, lots of small ASC-specific gotchas.

**Lesson:** A complete watchOS marketing screenshot pipeline that
ships well-composed framed captures to ASC is roughly 200 lines of
bash + ImageMagick + a handful of Swift launch-arg hooks. Worth
templatizing because every gotcha below cost real iteration time:

1. **ASC slot dimensions are exact, per device class.** Apple Watch
   Ultra accepts 410×502 OR 422×514 (Apple Watch Ultra 3 simulator
   captures at 422×514 native). Other classes have their own
   dimensions. Found in `fastlane/deliver/lib/deliver/app_screenshot.rb`
   in the `DEVICE_TYPE_TO_DIMENSIONS` map. The composed marketing PNG
   must be at one of those exact sizes — no padding, no scaling-up.
2. **ASC rejects watch screenshots with alpha (PNG32).** Error code
   `IMAGE_ALPHA_NOT_ALLOWED`. iPhone screenshots accept alpha, watch
   does not. ImageMagick's `-alpha off` only marks the channel
   inactive — you need `PNG24:output.png` prefix in the output to
   actually drop the alpha channel from the file.
3. **frames-cli's watch bezels include the band/strap.** Watch Ultra 3
   bezel renders ~600×960 with the case in the middle and Alpine
   Loop above/below. Cropping to a square (600×600) leaves visible
   strap residue at the case corners. Cropping tighter (600×540)
   eliminates it but the resulting image is wider than the 422×514
   ASC slot allows. Practical solution: don't use frames-cli for
   watch — draw the bezel directly in ImageMagick. Concentric
   titanium (#6e6661) + black ring around a rounded watch screen
   gives a clean 422×514 result with full design control.
4. **Sheet auto-presentation needs a launch arg + a deferred Task.**
   To capture a sheet (picker, stop confirmation), the home view has
   to render BEHIND the sheet first. Implement as
   `-WATCH_SHOW_PICKER` / `-WATCH_SHOW_STOP` launch args read in
   `.onAppear`, then `Task { try? await Task.sleep(for: .seconds(0.5));
   showPicker = true }`. The sleep is mandatory — `.onAppear` fires
   before SwiftUI has the sheet in the view tree.
5. **ScrollViewReader.scrollTo races view layout.** The capture
   script needs ≥5s sleep after `simctl launch -FASTLANE_SNAPSHOT`
   for the demo data to load AND the scroll to land. With 3s the
   list shows the default top-of-cards position; with 5s the
   intended scroll target is in view. Inside the view itself, wrap
   the scroll in `Task { try? await Task.sleep(for: .seconds(0.6));
   proxy.scrollTo(...) }` — same race.
6. **Demo data needs different shapes per screen.** Home view wants
   3 active running cards filling the small viewport. Picker wants
   an empty deck so Popular items render vibrant/addable, not
   dimmed-already-added. Solve with two functions
   (`loadWatchDemoData` + `loadWatchPickerDemoData`) and route in
   `FlaraWatchApp.task` based on the launch arg.
7. **Locale switching is per-launch-arg, not per-sim.** Pass
   `-AppleLanguages "(es-ES)" -AppleLocale es_ES` to `simctl launch`.
   No need to shutdown/reboot the sim between locales.

**Suggested action:** Port the pipeline as two playbook scripts:
`capture-watch-screenshots.sh` (the simctl driver, parameterized by
locale and screen) and `compose-watch-marketing.sh` (the ImageMagick
bezel + gradient + caption composer). Plus a small `WATCH_SCREENSHOTS.md`
rule capturing the seven gotchas above as a checklist. Reference
implementation at `xoloUno/flara-app` after merge: `scripts/capture-
watch-screenshots.sh`, `scripts/compose-watch-marketing.sh`. Bonus: a
`README` in `_templates/watch-screenshots/` showing the recommended
ImageMagick layered draw (concentric rounded rects + alpha mask) and
a sample appshot config for projects that want fancier captioning.

### 2026-05-03 — Flara

**Category:** pattern + suggestion
**Context:** Recapturing all Flara screenshots end-to-end on the
shotsmith v2 pipeline exposed that the screenshot pipeline has two
distinct input classes that share a directory namespace but want
opposite gitignore policies:
- **Regenerable app captures** — XCUITest- or simctl-driven app
  surfaces (HomeScreen, SymptomPicker, etc.). Fast to regenerate,
  shift visually with every UI tweak. Live at
  `fastlane/screenshots/<locale>/<device>/raw/` and are gitignored.
- **Human-required system-surface captures** — iOS UI rendered by
  SpringBoard, not the app: Notification Center stack with the Live
  Activity expanded, Home Screen page showing the widget, Control
  Center pulled down with the Control Widget. Slow to regenerate
  (require a person in the loop because Quartz drag and Cmd+L
  automation never reliably worked), and rarely change (only when
  iOS major UI shifts, the Live Activity / widget design changes,
  or a new locale is added). Live at `fastlane/system-surface-pngs/`
  and are tracked.

The Fastfile's `:compose_screenshots` lane stages the tracked dir
into the gitignored dir right before invoking shotsmith, so the two
flows merge for the actual compose step.

**Lesson:** Pipelines that mix automated and manual capture should
split inputs into two named directories with opposite gitignore
policies. The split solves three problems at once: (1) keeps git
history small by ignoring the regenerable bulk, (2) preserves the
slow-to-regenerate inputs as a versionable source of truth so anyone
can run the pipeline cold without you on the keyboard, and (3) makes
the cadence intent legible — "regenerate this every UI tweak" vs
"recapture once per release / when the surface changes."

The pattern works well in Flara but has discoverability problems for
new contributors: the separation is real but invisible. No README in
either directory explains why one is gitignored and the other isn't.
The dir name `system-surface-pngs/` is project-specific (LA stack,
widget, CC) when the underlying pattern is general (manual-capture
inputs that the pipeline stages but doesn't regenerate).

**Suggested action:**

1. Document this as the **"two-input-tree pattern"** in the playbook's
   screenshot section. Make it explicit which dir is which and why.

2. Recommend a more general directory name in the iOS template:
   `fastlane/manual-captures/` rather than the Flara-specific
   `system-surface-pngs/`. Projects that don't have manual-capture
   surfaces (apps without Live Activity / widgets / Control Widget)
   can skip the dir entirely.

3. Ship a one-page `README.md` template that drops into
   `manual-captures/` explaining: what lives here, when to recapture,
   how the compose lane stages it, and the "once per release" cadence
   convention. The README is the "loud about itself" mechanism that's
   currently missing.

4. Update the bootstrap iOS template's `.gitignore` to ignore
   `fastlane/screenshots/` and `fastlane/shotsmith/composed/` but
   **not** `fastlane/manual-captures/`. Calls out the policy in the
   gitignore itself with a comment.

5. Mention in the iOS template README that this dir is opt-in: list
   the surfaces that typically warrant it (Live Activity, Home Screen
   widget, Lock Screen widget, Control Widget) and the gestures
   required to capture each. Reference Flara's
   `fastlane/capture_widgets.sh` and `fastlane/capture_control_center.sh`
   as the canonical implementation.

6. Optional follow-up: shotsmith itself could grow a `manual_inputs`
   config block that names the tracked dir directly, so the staging
   step lives inside shotsmith instead of being copy-paste Ruby in
   each project's Fastfile. That's a shotsmith change, not a playbook
   change — capture as a separate inbox entry if pursued.


