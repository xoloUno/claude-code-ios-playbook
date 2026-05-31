# Status Bar Overrides Rule

Every script that captures a Simulator screenshot for the App Store must run the
same `xcrun simctl status_bar override` block before launching the target app.
Refactors that "simplify" the block by dropping flags produce screenshots that
get rejected, look amateur, or surface visual bugs in Control Center.

## The canonical block

```bash
xcrun simctl status_bar "$DEVICE" override \
  --time "9:41" \
  --dataNetwork hide \
  --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 \
  --wifiMode active --wifiBars 3 \
  --operatorName ""
```

Run this **after** `xcrun simctl boot "$DEVICE"` and **before**
`xcrun simctl launch …`.

## Why each flag exists

| Flag | Purpose | What breaks if dropped |
|---|---|---|
| `--time "9:41"` | Apple's marketing convention since the 2007 iPhone keynote — every screenshot in App Store listings reads 9:41. | Screenshots show the actual capture time, mixing test/release timestamps across the set. Reviewers notice. |
| `--dataNetwork hide` | Removes the 5G/LTE label between the carrier name and Wi-Fi icon. | In Control Center captures, Wi-Fi gets pushed to a second row when the data network label fits next to it. The whole status row visibly shifts. In normal in-app captures, the 5G label exposes that this is a real test device, not the marketing intent. |
| `--batteryState charged --batteryLevel 100` | Battery icon shows full + plugged. | Screenshots with a half-empty battery look like a draft. Inconsistent levels across a set look unprofessional. |
| `--cellularMode active --cellularBars 4` | Forces full cellular signal. | Some captures show "No Service" or weak signal — the simulator inherits whatever the host's last state was. |
| `--wifiMode active --wifiBars 3` | Forces full Wi-Fi signal. | Same as cellular — inconsistent or missing icons across the set. |
| `--operatorName ""` | Blanks the carrier text. | Default sims show "Carrier" verbatim in screenshots — Apple's review treats this as a marketing error, and reviewers in regional App Store fronts read "Carrier" as the literal word. |

## Scripts that must carry the block

- `fastlane/capture_widgets.sh` — Live Activity lock screen + Home Screen widget
- `scripts/capture-screenshots.sh` (project-side) — main XCUITest / simctl capture driver
- Any `capture-watch-screenshots.sh` (per `screenshot-pipeline.md`)
- The agent-driven `/capture-manual-surfaces` flow (Control Center, Notification Center, etc.)

The playbook's `bootstrap.sh` emits these scripts with the block intact. If you
refactor any of them, the block stays whole.

## Refactor checklist

When you touch a capture script:

1. The status-bar override block must run between `simctl bootstatus` and
   `simctl launch`. Don't move it after the launch — the override doesn't
   apply to a process that's already started.
2. All seven flags from the canonical block must be present. If you have a
   reason to drop one, write a comment explaining why next to the override
   call so the next refactor doesn't re-drop it.
3. Re-capture one screenshot post-refactor and visually confirm: 9:41 in the
   clock, no carrier name, no 5G/LTE label, full bars on both icons,
   full battery + lightning bolt.
4. For Control Center captures specifically, also confirm the Wi-Fi icon is on
   the same row as the cellular icon (single-row status). If it wraps to two
   rows, `--dataNetwork hide` got dropped.

## Why this rule exists

A downstream session refactored several capture scripts in a single commit and
silently dropped `--operatorName ""` and `--dataNetwork hide` from all of
them. The drop wasn't caught for weeks because the captures still rendered —
just with "Carrier" visible and the Control Center status row wrapping. By
the time it surfaced, those flags had to be re-added across multiple scripts
in multiple projects. This rule documents *why* the flags exist.
