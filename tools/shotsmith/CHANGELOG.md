# shotsmith Changelog

Notable changes per release. shotsmith follows [semver](https://semver.org/);
schema-breaking config changes bump the major version.

---

## v0.2.0 — 2026-05-03

First release as a standalone repo, spun off from
[`xoloUno/claude-code-ios-playbook`](https://github.com/xoloUno/claude-code-ios-playbook)
where shotsmith was developed in-tree from v0.1.0 through v0.2.0. Earlier
release history is preserved in the playbook's CHANGELOG and in this repo's
git history (via `git subtree split`).

### What's in v0.2.0

- **Composition pipeline** — `compose` subcommand renders ASC-ready PNGs
  from already-framed inputs. Supports linear gradients (with optional
  Gaussian-noise dither), New York / SF Pro / arbitrary system fonts,
  per-device caption sizes, optional subtitle line, per-device caption +
  subtitle + padding overrides, forced line breaks (`\n` in caption text),
  multi-line wrapping with ellipsis truncation, and locale → language
  fallback for caption resolution (`es-MX` → `es`).
- **Framing wrapper** — `frame` subcommand wraps `frames-cli`. Reads from
  `<input>/<locale>/raw/`, writes to `<input>/<locale>/framed/`, never
  overwrites raws.
- **Manual-input staging** — `stage` subcommand + `manual_inputs` config
  block. Declared manual-gesture captures (Live Activity, Home Screen
  widget, Control Center) get copied from a tracked source dir into
  `raw/` before frame. `verify` reports a hard error when a declared
  source file is missing.
- **Pipeline orchestrator** — `pipeline` subcommand runs verify → stage →
  frame → compose end-to-end. `--steps` flag for partial runs (e.g.
  `--steps compose` to re-render after a caption tweak). Optional
  `pipeline.capture_hook` for project-defined upstream capture scripts.
- **Verify** — `verify` subcommand validates the directory contract:
  errors for orphan PNGs at the locale root, missing `manual_inputs`
  sources, and PNGs in `framed/` that match the ASC composed canvas size
  (the "appshot-final masquerading as framed input" bug class). Warnings
  for missing `raw/` or `framed/` dirs and for `framed/` PNGs that don't
  match the default `frames-cli` output dimensions.
- **Input mapping** — per-device `canonical_filename → source_filename`
  translation at frame time. Lets capture tools (XCUITest, simctl,
  manual) write whatever filenames they want; framed/ ends up with the
  canonical names that match `captions.json`.
- **Subtitle support** — optional second text line beneath each caption
  with its own font, color, sizes, max lines, and spacing. Activated
  per-image via dict-form caption entries.
- **Three bundled gradient presets** at `templates/presets/`: `mauve`
  (dusty purple → coral), `royal-purple` (deep violet → coral; used by
  Flara), `apple-music` (deep red → coral).
- **Friendly Pillow diagnostic** — `bin/shotsmith` shim catches missing
  Pillow and prints the exact `pip install` command for the active
  Python interpreter, instead of letting an `ImportError` traceback
  bubble up.
- **83 tests passing** across `test_compose.py`, `test_frame.py`,
  `test_stage.py`, `test_verify.py`, `test_pipeline.py`.

### Install (v0.2.0)

```bash
pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0
shotsmith --version
```

### Known limitations

- iPhone 6.9" + iPad 13" only. Smaller iPhone slots are auto-scaled by
  ASC; Apple Watch is intentionally not handled (screen-only ASC
  submissions; the watch hardware corner-radius clips composed art).
- macOS-focused. The font resolver looks in `/System/Library/Fonts`,
  `/Library/Fonts`, and `~/Library/Fonts`. Linux + Windows would work
  for composition itself but font discovery would need extension.
- No PyPI release yet. Install via `pipx install git+...` for now;
  PyPI publication is queued for after a second project consumer has
  battle-tested the schema.
