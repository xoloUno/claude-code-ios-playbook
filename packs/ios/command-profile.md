# iOS command profile

Kind-layer extensions for the universal `/status` and `/wrapup`, shared by every
iOS app composed from this pack. The universal skeleton loads this file at runtime
and folds each section in at the right stage. **Every step below is conditional** —
guarded by a cheap existence check or a declared fact — so one profile fits every
iOS app without overfitting the richest one.

## /status

Fold these into the briefing after the universal git steps:

- **Build status.** If `CLAUDE.md` has a "Current State" section with a build field,
  surface it as a `**Build:** <status>` headline line. (The build command itself lives
  in `.claude/rules/build-deploy.md`; `/status` reports, it doesn't build.)
- **Dependabot lens.** If `gh` is available, `gh pr list --label dependencies --state open`
  — mention any open dependency PRs as a flag. Skip silently if `gh` is absent.
- **Playbook freshness.** If a `.playbook-version` file exists, compare its date to the
  newest dated entry in the playbook's `CHANGELOG.md`. If the playbook has newer entries,
  add a flag suggesting `/upgrade`. Skip if `.playbook-version` is absent.

## /test

The universal `/test` resolves which command to run; this kind layer supplies the Xcode
default. (To *write* tests, use `/gen-tests` — a separate iOS-pack command, not this verb.)

- **Simulator first.** Before launching a run, confirm the build/test simulator exists:
  `xcrun simctl list devices available` should include the simulator named in
  `.claude/rules/testing.md` ("Running tests" — this project's primary sim). If it's
  missing, FAIL with the `xcrun simctl create` / Xcode > Settings > Platforms hint rather
  than letting `xcodebuild` fail late.
- **Command.** Run the suite with the `xcodebuild test …` invocation in
  `.claude/rules/testing.md` — that line already carries this project's scheme and
  simulator (composed in), so it's the single source of truth, not duplicated here. The
  same rule documents the Swift Testing conventions and the SwiftData `TEST_HOST` gotcha;
  read it if a run fails oddly.
- **Scope.** With `$ARGUMENTS`, narrow the run via `-only-testing:<Target>/<Suite>[/<test>]`.
- **Report.** ✅ / ❌ with the failing test identifiers and the first failure message each.

## /wrapup

Slot these into the universal flow at the stage named — not in list order.

**Record mutations (stage 3 — before staging):**

- **Release notes.** If user-facing changes were made and a `release-notes-draft.md`
  exists (or the app keeps one), update it.
- **Prose-humanizer.** If this session touched user-facing prose — `release-notes-draft.md`
  or `fastlane/metadata/en-US/description.txt` — invoke the `prose-humanizer` subagent on
  each before commit, to cut AI-tells (decorative adjectives, inflated verbs, significance
  padding) so the text reads natural to App Store reviewers. **Skip non-English**
  `fastlane/metadata/<locale>/description.txt` — they're translations, and humanizing them
  risks breaking translation accuracy; non-English locales drift between releases on purpose
  and `/release` retranslates them fresh from en-US per `.claude/rules/metadata-translation.md`.
  Requires the `writing-prose-like-a-human-for-agents` plugin; if it isn't installed, skip
  this step and say so in the wrap-up summary. (Prose-humanizer is a *mutation*, not a gate.)
- **Scope items.** If `CLAUDE.md` has a scope/checklist section, check off any items this
  session completed.

**Commit (stage 6):**

- **`[skip ci]`.** On a **local** session, append `[skip ci]` to the commit subject unless
  the user says otherwise. On a **cloud** session, do **not** — let CI run. (This is the
  iOS-specific rule the universal skeleton deliberately stays silent about.)
