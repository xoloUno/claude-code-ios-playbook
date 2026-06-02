Run this project's test suite and report the result.

This is the **universal** `/test`. It runs the same in any project — it executes the
project's declared test command (or its kind's default) and reports pass/fail. It does
**not** write tests; the command to run is never hardcoded here, it comes from the
project's facts and its kind profile, so one skeleton serves a pytest project, an
`xcodebuild` project, or a project with no runner at all.

(To *generate* tests, that's a kind-specific authoring command — e.g. the iOS pack's
`/gen-tests` — not this verb.)

## Load first — resolve the command, then run

Before running anything, read these files **if present** and merge the steps under their
`## /test` heading into the flow below:

- `.claude/project.yml` — `test_command` (the exact command to run) and `kind`.
- `.claude/command-profile.md` — the kind layer: the kind's default test command and any
  pre/post steps (e.g. iOS confirms the simulator first).
- `.claude/command-profile.local.md` — this project's own escape-hatch overrides.

If none are present, the universal steps stand alone.

## Universal steps

1. **Resolve the command**, in priority order:
   - `project.yml` `test_command`, if set — run it verbatim.
   - else the command the kind profile's `## /test` supplies (e.g. `pytest -q`,
     `xcodebuild test …`).
   - else look for an obvious runner — a `tests/` directory, `*Tests.swift`, a
     `Package.swift` with a test target. If you find one, run its conventional command;
     if you find nothing, **report "no test runner configured" and stop**. That is a clean
     no-op, not an error — the right outcome for a docs or Dynamo project.
2. **Scope, if asked.** With `$ARGUMENTS`, narrow the run to it — a test file, a suite
   name, a `-k` filter, an `-only-testing:` target — using the runner's own idiom. With no
   arguments, run the whole suite.
3. **Run it** from the repo root. Don't bury the result in noise.
4. **Report** a one-line verdict plus the actionable details:
   - ✅ **PASS** — N tests, 0 failures.
   - ❌ **FAIL** — list the failing tests and the first actionable error per failure.
   - ⏭️ **SKIPPED** — no test runner configured (say why).

Then fold in any `## /test` steps the profile files contributed.

## Notes

- `/test` is a **gate**, not a mutation: it changes nothing in the working tree. Run it
  freely, as often as you like.
- It runs the same suite `/wrapup` uses as its pre-commit validation gate — `/test` just
  surfaces it as a verb you can invoke on demand.
