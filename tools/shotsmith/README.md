# shotsmith

Compose App Store screenshots: gradient backgrounds, captions, multi-locale —
takes already-framed PNGs (from `frames-cli` or any other framer) and produces
ASC-ready submission images.

Built as a replacement for `appshot-cli`'s caption + gradient layer. Uses
Pillow (FreeType + HarfBuzz) for typography. Pure Python, single dependency.
Wraps `frames-cli` for device bezels.

## Status

Phase 4.5 — orchestrator complete. iPhone 6.9" + iPad 13" supported.
Multi-locale supported. Watch is not yet handled (see the playbook's
`thank-you-so-much-drifting-cocoa.md` plan §3 for the deferred decision).

## Install

From the playbook (development):

```bash
cd tools/shotsmith
pip install -r requirements.txt
./bin/shotsmith --version
```

As a package (once spun out to its own repo):

```bash
pipx install shotsmith
```

## Directory contract

shotsmith enforces a stable per-device directory layout. For each device's
configured input path, two siblings hold the intermediate and final-input
PNGs:

```
<input.{device}>/<locale>/
├── raw/        ← capture output (XCUITest, simctl). NEVER overwritten.
└── framed/     ← frames-cli output. NEVER overwritten. shotsmith reads from here.

<output.{device}>/<locale>/   ← shotsmith composed output (per preset)
```

Loose PNGs at the locale root are an anti-pattern — `shotsmith verify` flags
them. The contract makes "edit a caption and re-render" cheap (seconds; no
re-capture or re-frame) while ensuring intermediates are never silently lost.

## Usage

Four subcommands. All take `--config`, `--locale` (repeatable), `--device`
(repeatable). With no filter flags, every (device × locale) combination runs.

```bash
# Compose only — reads from <input>/<locale>/framed/
./bin/shotsmith compose  --config path/to/config.json
./bin/shotsmith compose  --config path/to/config.json --locale en-US --device iphone --dry-run

# Frame only — wraps frames-cli, reads raw/, writes framed/
./bin/shotsmith frame    --config path/to/config.json
./bin/shotsmith frame    --config path/to/config.json --force   # re-frame existing

# Verify directory contract — reports errors (alpha, dim mismatch, orphans) + warnings (missing dirs)
./bin/shotsmith verify   --config path/to/config.json

# Pipeline — verify, then frame + compose end-to-end
./bin/shotsmith pipeline --config path/to/config.json
./bin/shotsmith pipeline --config path/to/config.json --steps capture,frame,compose
./bin/shotsmith pipeline --config path/to/config.json --steps compose   # just re-render
```

`pipeline --steps` defaults to `frame,compose`. Add `capture` if your config
defines a `pipeline.capture_hook`.

## Config

A `config.json` describes inputs, outputs, the gradient, the caption style,
and which locales to render. See `templates/config.example.json`:

```json
{
  "version": 2,
  "input":  { "iphone": "fastlane/screenshots/{locale}/iPhone 6.9\" Display" },
  "output": { "iphone": "fastlane/shotsmith/final/iphone/{locale}" },
  "pipeline": {
    "capture_hook": "scripts/capture-screenshots.sh",
    "frames_cli":   "frames",
    "verify_strict": true
  },
  "background": {
    "type": "linear-gradient",
    "stops": ["#FF5F6D", "#FFC371"],
    "angle": 180,
    "dither": 6
  },
  "caption": {
    "font": "New York Small Bold",
    "color": "#1B1B1B",
    "size_iphone": 115,
    "size_ipad": 130,
    "position": "footer",
    "padding_pct": 3.0,
    "max_lines": 2,
    "line_height": 1.15
  },
  "captions_file": "captions.json",
  "locales": ["en-US", "es-ES", "es-MX"]
}
```

Path templates use `{locale}` and are resolved relative to the config file's
directory. Note: `input.{device}` names the per-device root; `raw/` and
`framed/` subdirs underneath `<input>/<locale>/` are created and managed by
shotsmith.

### Input mapping (optional, recommended for multi-source pipelines)

Capture tools rarely write filenames that match what you want to ship. XCUITest
captures in implementation order; ASC displays in alphabetical order; consumer
order (which screen is the marketing hero?) is independent of both. And once
you mix capture sources — XCUITest for in-app, simctl for system surfaces,
SwiftUI ImageRenderer for Live Activities (Phase 7) — every source has its
own naming conventions.

`input_mapping` is a per-device dict translating **canonical filename**
(captions.json key) → **source filename** (whatever the capture tool wrote
into `raw/`). The frame step uses this lookup, so `framed/` always ends up
with canonical names that match captions.json.

```json
"input_mapping": {
  "iphone": {
    "01_LiveActivities.png":   "from_simctl_NotificationCenter.png",
    "02_HomeScreen.png":        "01_HomeScreen.png",
    "03_SymptomPicker.png":     "02_SymptomPicker.png",
    "04_SymptomDetail.png":     "03_SymptomDetail.png",
    "05_StopConfirmation.png":  "04_StopConfirmation.png",
    "06_ControlCenter.png":     "from_simctl_ControlCenter.png",
    "07_HomeScreenWidgets.png": "from_simctl_HomeScreen.png",
    "08_HomeScreenDark.png":    "05_HomeScreenDark.png"
  }
}
```

Without `input_mapping`, shotsmith uses identity — every PNG in `raw/` becomes
the same filename in `framed/`. So simple pipelines need no mapping at all.

`shotsmith verify` reports each canonical name whose source file isn't in
`raw/` so you can see which capture step is missing. `shotsmith frame` skips
those with an actionable reason ("source X.png not found in raw/ — check
input_mapping or capture step").

### Pipeline block (optional)

Adding a `pipeline` block to the config enables the `frame`, `verify`, and
`pipeline` subcommands. Without it, only `compose` works.

| Field | Default | Purpose |
|---|---|---|
| `capture_hook` | none | Path to your project's capture script. Called per (device, locale) with env vars `SHOTSMITH_DEVICE`, `SHOTSMITH_LOCALE`, `SHOTSMITH_RAW_DIR`. Hook writes raw PNGs into `$SHOTSMITH_RAW_DIR`. |
| `frames_cli` | `"frames"` | Command name for frames-cli on PATH. |
| `frames_args` | `[]` | Extra args appended to every frames-cli invocation. |
| `verify_strict` | `true` | Pipeline aborts on verify errors. Set `false` to downgrade errors to warnings. |

`background.dither` is an optional Gaussian-noise sigma applied to the
gradient — a subtle film-grain overlay that breaks up gradient banding on
8-bit displays. `0` (default) disables. Subtle range is `4..12`; higher
values produce visible grain. Inspired by Arc browser's gradient treatment.

### Captions file

A separate JSON keyed by input PNG filename, each entry keyed by language code.
Each value can be either a **string** (caption only) or a **dict** with
`caption` and optional `subtitle` keys:

```json
{
  "01_HomeScreen.png": {
    "en":    { "caption": "Track everything", "subtitle": "in one place" },
    "es":    { "caption": "Todo en un solo lugar", "subtitle": "en tiempo real" },
    "es-MX": { "caption": "Todo en un solo lugar", "subtitle": "en tiempo real" }
  },
  "02_Detail.png": {
    "en":    "Drill down with one tap",
    "es":    "Profundiza con un solo toque"
  }
}
```

The string form is shorthand for `{"caption": "...", "subtitle": null}` —
backward-compatible with the original schema.

shotsmith tries the full locale first (`es-MX`), then the language portion
(`es`), then skips the image with a warning.

### Per-device caption + subtitle overrides

Each per-locale dict-form value can carry device-specific override keys
alongside the defaults. When rendering for device X, shotsmith tries
`caption_X` first, falls back to `caption`. Same for `subtitle_X` /
`subtitle`. The two resolve independently — you can override only the
caption for iPhone without touching subtitles.

```json
{
  "01_HomeScreen.png": {
    "en": {
      "caption":        "Track everything in one place",
      "caption_iphone": "Track everything\nin one place",
      "subtitle":       "in real time"
    }
  }
}
```

Common use case: iPhone wants a forced line break for visual punch, iPad's
wider canvas reads better as a single line. Just add `caption_iphone` (or
`caption_ipad`) with the device-specific copy. Devices without an override
fall back to `caption`.

### Per-device padding (`padding_pct_iphone`, `padding_pct_ipad`)

The `caption.padding_pct` value is the default; optional `padding_pct_iphone`
and `padding_pct_ipad` overrides let you tighten or loosen the caption_area
on a specific device. Useful when one device's canvas proportions make the
default feel wrong — for example, iPad's wider canvas can take less padding
to recover image_area height for the framed PNG.

```json
"caption": {
  "padding_pct":      3.5,
  "padding_pct_ipad": 2.0
}
```

### Forced line breaks

Use `\n` (a literal newline character in the JSON string — JSON parses `\n`
as a newline natively) to force a line break inside any caption or subtitle.
Each forced segment is then independently word-wrapped to fit the available
width, sharing the `max_lines` budget across all segments.

```json
{
  "01.png": {
    "en": {
      "caption": "Track everything\nin one place",
      "subtitle": "in real time"
    }
  }
}
```

If the total wrapped lines exceed `max_lines`, the last visible line is
truncated with an ellipsis. Empty segments (`\n\n`) are collapsed — to add
vertical gap, increase `subtitle.spacing_pct` instead.

### Subtitle (optional)

Add a `subtitle` block alongside `caption` to enable a smaller secondary line
beneath each caption. The subtitle has its own font, color, sizes, and max
lines. `spacing_pct` controls the gap between caption and subtitle (as a
percent of canvas height).

```json
"subtitle": {
  "font": "New York Small Regular",
  "color": "#FFFFFF",
  "size_iphone": 60,
  "size_ipad": 70,
  "max_lines": 1,
  "line_height": 1.15,
  "spacing_pct": 1.5
}
```

If the `subtitle` config block is omitted, no subtitle is ever rendered (and
any subtitle text in the captions file is ignored). If present, it activates
per image based on the caption-file value: dict-form entries with a non-empty
`subtitle` get one; string-form or dict-form-without-subtitle entries get
caption-only layout.

### Font resolution

Two ways to specify the font in `caption.font`:

1. **Family + style name** — e.g. `"New York Small Bold"`. shotsmith searches
   `/System/Library/Fonts`, `/Library/Fonts`, and `~/Library/Fonts` for matching
   files using Apple's optical-size + weight naming convention
   (`NewYorkSmall-Bold.otf`).
2. **Direct path** — anything containing `/` or ending in `.ttf`/`.otf`/`.ttc`
   is used verbatim, e.g. `"/Library/Fonts/NewYorkSmall-Bold.otf"`.

If the family-name lookup fails, shotsmith prints the directories searched and
patterns tried so you can fix it.

## Layout model

For the App Store convention (`position: "footer"`):

```
+---------------------------------+ y=0
|                                 |
|   [framed PNG, fitted into      |
|    image area, centered]        |
|                                 |
+---------------------------------+ y=image_area_height
|                                 |
|   <Caption, wrapped, centered>  |
|   <Subtitle, optional>          |
|                                 |
+---------------------------------+ y=canvas_height
```

```
caption_area_height
  = (caption_font × line_height × caption_max_lines)
  + (subtitle_font × subtitle_line_height × subtitle_max_lines)  [if subtitle]
  + (canvas_height × subtitle_spacing_pct / 100)                 [if subtitle]
  + (2 × canvas_height × caption_padding_pct / 100)
image_area_height = canvas_height − caption_area_height
```

The framed PNG is scaled to fit `image_area_height` while preserving aspect
ratio. The text block (caption + spacing + subtitle) is vertically centered
within `caption_area_height`.

## Devices

| Key | ASC slot | Default caption size |
|---|---|---|
| `iphone` | iPhone 6.9" Display (1320 × 2868) | 115 |
| `ipad`   | iPad 13" Display (2064 × 2752) | 130 |

These are Apple's required ASC submission sizes. Apple auto-scales them down
to smaller iPhone/iPad slots — uploading 6.9" + 13" covers every device class.
See the iOS playbook's `build-deploy.md` for the full ASC matrix.

## Tests

```bash
cd tools/shotsmith
pip install -r requirements.txt pytest
pytest tests/
```

The end-to-end test synthesizes a fake framed PNG, runs the full compose
pipeline, and asserts output dimensions. Golden-image diffs are deferred to
Phase 2 of the implementation plan (parity check against appshot in Flara).

## Phase 2 gradient finalists

Three palettes carried forward for the Flara parity check, saved at
[templates/presets/](templates/presets/):

- **mauve** — `#A56FB4` → `#FF6B5C` (soft dusty purple → coral)
- **royal-purple** — `#6B4FBB` → `#FF6B5C` (cool deep violet → coral)
- **apple-music** — `#FA2D48` → `#FF6B5C` (deep red → coral, no purple)

All share `dither: 30`, white captions, `New York Small Bold`. See
[templates/presets/README.md](templates/presets/README.md) for the
re-rendering recipe and Phase 2 adoption notes.

## Roadmap

- **Phase 2**: side-by-side parity check against appshot output for Flara
- **Phase 3**: multi-locale + iPad polish
- **Phase 4**: Flara migration; retire `appshot-cli` and `patch-appshot.sh`
- **Phase 5**: watch composition decision (depends on Apple's actual stance on
  framed watch screenshots — see playbook plan §3)
- **Phase 6**: bootstrap.sh integration; ship to new projects by default
- **Future**: spin off to its own `xoloUno/shotsmith` repo + PyPI release once
  the schema stabilizes after a few real ASC submissions

## Why not appshot?

Flara's screenshot pipeline used `appshot-cli` for caption + gradient
composition, but the install required a 22-line monkey-patch
(`patch-appshot.sh`) to override the built-in iPhone/iPad font-size strategy
— captions rendered illegibly small at ASC sizes otherwise. The patch had to
be re-applied after every `npm install -g appshot-cli`. shotsmith eliminates
the patch by exposing font size directly in the config.

## Why keep frames-cli?

`frames-cli` (viticci's port of MacStories' Apple Frames) handles the device
bezel layer well and is independently maintained. shotsmith takes its output
as input and adds the gradient + caption — separation of concerns.
