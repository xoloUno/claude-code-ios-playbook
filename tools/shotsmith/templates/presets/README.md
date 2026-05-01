# Phase 2 gradient finalists

Three palettes selected from the iPhone gradient batch comparison
(2026-04-28). Each is a complete config that runs against the local test
fixtures so the rendered samples can be re-inspected without re-batching.

| Preset | Top | Bottom | Notes |
|---|---|---|---|
| [mauve.json](mauve.json) | `#A56FB4` | `#FF6B5C` | Soft dusty purple → coral. Most editorial. |
| [royal-purple.json](royal-purple.json) | `#6B4FBB` | `#FF6B5C` | Cool deep violet → coral. Most contrast. |
| [apple-music.json](apple-music.json) | `#FA2D48` | `#FF6B5C` | Deep red → coral, no purple. Most cohesive. |

All three share:
- `dither: 30` — Arc-style film grain
- `caption.color: #FFFFFF` — white reads against all three top stops
- `font: "New York Small Bold"` at 115px iPhone / 130px iPad
- `angle: 180` (top → bottom)

## Re-rendering

```bash
cd tools/shotsmith
./bin/shotsmith compose --config templates/presets/mauve.json --device iphone
open tests/fixtures/sample-output/presets/mauve/iphone/en-US/01_HomeScreen.png
```

## Phase 2 plan

When Phase 2 starts (parity check against appshot in Flara), copy the
chosen preset's `background` and `caption` blocks into Flara's
`fastlane/shotsmith/config.json`, then point `input` and `output` at
Flara's actual paths. Render all 8 captioned screenshots and compare
against the current appshot output before deciding which preset ships.
