Agent-driven capture loop for iOS system-surface screenshots that need human gestures
(Live Activity on Lock Screen, Home Screen widget, Control Center). The agent automates
prep — boot, language switch, status-bar override, app launch — and the user performs
the Simulator gesture, then types `ready` in chat between surfaces.

See `.claude/rules/screenshot-pipeline.md` for the four-layer artifact model, gesture
inventory, and filename conventions, and `.claude/rules/status-bar-overrides.md` for the
canonical status-bar override block. Do NOT duplicate that content here.

Steps:

1. **Read project state.**
   - Source `.env.project` (or equivalent). Required: `BUNDLE_ID`, `PRIMARY_SIM`. Optional:
     `WATCH_SIM`. If any required value is missing, abort with a clear error.
   - Read the project's shotsmith `config.json` (commonly at `fastlane/shotsmith/config.json`
     or `shotsmith/config.json`) for `locales` and any `manual_surfaces` list.
   - If `manual_surfaces` is unset, fall back to the canonical set: `LockScreen_LiveActivity`,
     `HomeScreen_Widget`, `ControlCenter`.
   - Confirm `fastlane/manual-captures/` exists. If not, offer to `mkdir -p` it.

2. **Confirm scope.**
   - Compute `N = len(manual_surfaces)`, `M = len(locales)`, `X = N * M`.
   - Print:
     ```
     I'll capture N surfaces × M locales = X screenshots into fastlane/manual-captures/<locale>/.
     Per-locale flow: I prep the simulator (boot, language, status bar, launch app), you
     perform the gesture in the Simulator window, then type `ready` in chat and I capture.
     Continue?
     ```
   - Wait for explicit confirmation in chat. Do not proceed on silence.

3. **Outer loop — for each locale in `locales`:**

   a. Boot `$PRIMARY_SIM` if not already booted (`xcrun simctl bootstatus -b "$PRIMARY_SIM"`),
      then `open -a Simulator`.

   b. Switch the simulator's device language for this locale if it isn't already set.
      Use `xcrun simctl spawn "$PRIMARY_SIM" defaults write -g AppleLanguages -array <code>`
      and reboot the sim. Skip if already on that locale (track state across the loop).

   c. Apply the status-bar override (canonical block from `.claude/rules/status-bar-overrides.md`).

   d. Launch the app: `xcrun simctl launch "$PRIMARY_SIM" "$BUNDLE_ID" -WIDGET_DEMO_MODE YES
      -FASTLANE_SNAPSHOT YES`. Wait briefly for the app to settle.

4. **Inner loop — for each surface in `manual_surfaces`:**

   a. Look up the gesture for the current surface in the gesture inventory in
      `.claude/rules/screenshot-pipeline.md`. Tell the user the **exact** gesture in chat.
      Examples (verify against the rule, do not invent):
      - `LockScreen_LiveActivity` — "Press Cmd+L in the Simulator to lock the device. Confirm
        the Live Activity is visible on the lock screen, then type `ready`."
      - `HomeScreen_Widget` — "Return to home screen (Cmd+Shift+H), confirm the widget is
        visible, then type `ready`."
      - `ControlCenter` — "Open Control Center (drag from top-right corner of the simulated
        device), confirm the Control Widget is visible, then type `ready`."

   b. Wait for chat input. Accept `ready`, `done`, `go`, `ok` (case-insensitive) as proceed
      signals. If the user types something else:
      - "redo", "back", "previous" → back up one surface and re-run from step (a).
      - "skip" → skip this surface, log it as missing in the end-of-run summary.
      - "cancel", "stop", "abort" → exit the loop, jump to step 6.
      - Anything else → ask the user to clarify; do not capture.

   c. Capture:
      ```
      xcrun simctl io "$PRIMARY_SIM" screenshot \
        "fastlane/manual-captures/<locale>/<NN>_<surface>.png"
      ```
      Use the `<NN>_<surface>` numbering convention from the rule (verify against
      `screenshot-pipeline.md` — typically `90_LockScreen_LiveActivity`,
      `91_HomeScreen_Widget`, `92_ControlCenter`).

   d. Verify the file exists and is non-empty (`test -s <path>`). If empty or missing,
      report the failure and ask the user before retrying.

5. **Edge cases.**
   - If any `simctl` command fails, report the exact command and stderr to the user and ask
     before retrying. Do not silently retry.
   - If the user cancels mid-loop, leave already-captured PNGs in place.
   - Do NOT script Quartz drag or any other gesture automation. Gestures are manual by
     design.

6. **End-of-run summary.**
   - Print a tree of captured files under `fastlane/manual-captures/` (e.g. `tree
     fastlane/manual-captures/` or a manual `find ... -type f | sort`).
   - List any surfaces that were skipped or failed.
   - Suggest next step: `bundle exec fastlane compose_screenshots` (or whatever the
     project's compose lane is named — check the Fastfile if unsure) to stage these into
     `raw/` and run shotsmith.
   - Remind the user: per the screenshot-pipeline rule's gitignore policy, manual-capture
     PNGs are tracked in git. If shipping a release, `git add fastlane/manual-captures/`
     and commit them with the release.

Important:
- Do NOT use `read -p` or any interactive shell-prompting pattern. The agent prompts via
  chat output and waits for chat input.
- Do NOT script gestures. Manual gestures are the contract of this command.
- Reference `.claude/rules/screenshot-pipeline.md` and `.claude/rules/status-bar-overrides.md`
  for canonical specs. If either rule file is missing, abort with a clear error rather
  than guessing the gesture inventory or override block.
- Treat each capture as a discrete checkpoint — verify the PNG before moving to the next
  surface so a failure mid-loop doesn't cascade.
