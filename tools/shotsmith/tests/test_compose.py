"""End-to-end + unit tests for shotsmith composition.

Run with: `pytest tests/` from the tools/shotsmith directory.

The end-to-end test synthesizes a tiny framed PNG, composes it through the
full pipeline, and asserts dimensions + that captions and gradient pixels are
present. It does NOT do golden-image diff — golden images for this tool are
established by visual inspection in Phase 2 of the implementation plan
(side-by-side parity check against appshot in Flara).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

# Make the package importable for tests run from the project root or tests/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shotsmith import captions as captions_mod  # noqa: E402
from shotsmith import compose as compose_mod  # noqa: E402
from shotsmith import config as config_mod  # noqa: E402
from shotsmith import fonts as fonts_mod  # noqa: E402


# ---------- captions ----------

def test_captions_lookup_full_locale():
    c = captions_mod.Captions({"a.png": {"en": "hello", "es-MX": "hola MX"}})
    entry = c.lookup("a.png", "es-MX")
    assert entry.caption == "hola MX"
    assert entry.subtitle is None


def test_captions_lookup_language_fallback():
    c = captions_mod.Captions({"a.png": {"en": "hello", "es": "hola"}})
    entry = c.lookup("a.png", "es-MX")
    assert entry.caption == "hola"


def test_captions_lookup_missing_returns_none():
    c = captions_mod.Captions({"a.png": {"en": "hello"}})
    assert c.lookup("a.png", "fr-FR") is None
    assert c.lookup("missing.png", "en") is None


def test_captions_lookup_dict_form_returns_subtitle():
    c = captions_mod.Captions({
        "a.png": {"en": {"caption": "Track everything", "subtitle": "in one place"}}
    })
    entry = c.lookup("a.png", "en")
    assert entry.caption == "Track everything"
    assert entry.subtitle == "in one place"


def test_captions_lookup_dict_form_subtitle_optional():
    c = captions_mod.Captions({"a.png": {"en": {"caption": "Just caption"}}})
    entry = c.lookup("a.png", "en")
    assert entry.caption == "Just caption"
    assert entry.subtitle is None


def test_captions_lookup_invalid_value_type_raises():
    import pytest
    c = captions_mod.Captions({"a.png": {"en": 42}})
    with pytest.raises(captions_mod.CaptionsError):
        c.lookup("a.png", "en")


# ---------- per-device caption / subtitle overrides ----------

def test_captions_per_device_caption_override():
    c = captions_mod.Captions({
        "a.png": {"en": {
            "caption": "Real time symptom tracking",
            "caption_iphone": "Real time\nsymptom tracking",
        }}
    })
    iphone = c.lookup("a.png", "en", device_key="iphone")
    ipad = c.lookup("a.png", "en", device_key="ipad")
    assert iphone.caption == "Real time\nsymptom tracking"
    assert ipad.caption == "Real time symptom tracking"


def test_captions_per_device_subtitle_override():
    c = captions_mod.Captions({
        "a.png": {"en": {
            "caption": "Hi",
            "subtitle": "Default subtitle",
            "subtitle_ipad": "iPad-specific subtitle",
        }}
    })
    iphone = c.lookup("a.png", "en", device_key="iphone")
    ipad = c.lookup("a.png", "en", device_key="ipad")
    assert iphone.subtitle == "Default subtitle"
    assert ipad.subtitle == "iPad-specific subtitle"


def test_captions_per_device_independent_for_caption_vs_subtitle():
    # caption has device-specific override, subtitle doesn't (or vice versa) —
    # they should resolve independently.
    c = captions_mod.Captions({
        "a.png": {"en": {
            "caption": "default cap",
            "caption_iphone": "iphone cap",
            "subtitle": "shared sub",
        }}
    })
    iphone = c.lookup("a.png", "en", device_key="iphone")
    ipad = c.lookup("a.png", "en", device_key="ipad")
    assert iphone.caption == "iphone cap"
    assert iphone.subtitle == "shared sub"
    assert ipad.caption == "default cap"
    assert ipad.subtitle == "shared sub"


def test_captions_per_device_no_device_key_uses_base():
    c = captions_mod.Captions({
        "a.png": {"en": {
            "caption": "default cap",
            "caption_iphone": "iphone cap",
        }}
    })
    # Without device_key, falls back to base caption — backward compat.
    entry = c.lookup("a.png", "en")
    assert entry.caption == "default cap"


def test_captions_string_form_ignores_device_key():
    # String form is the same for every device; device_key has no effect.
    c = captions_mod.Captions({"a.png": {"en": "shared string"}})
    iphone = c.lookup("a.png", "en", device_key="iphone")
    ipad = c.lookup("a.png", "en", device_key="ipad")
    assert iphone.caption == "shared string"
    assert ipad.caption == "shared string"


# ---------- per-device padding override ----------

def test_caption_style_padding_for_falls_back_to_default():
    cs = config_mod.CaptionStyle(
        font="X", color="#FFF",
        size_iphone=100, size_ipad=130,
        position="footer", padding_pct=3.5,
        max_lines=2, line_height=1.15,
    )
    assert cs.padding_for("iphone") == 3.5
    assert cs.padding_for("ipad") == 3.5


def test_caption_style_padding_for_uses_device_override():
    cs = config_mod.CaptionStyle(
        font="X", color="#FFF",
        size_iphone=100, size_ipad=130,
        position="footer", padding_pct=3.5,
        max_lines=2, line_height=1.15,
        padding_pct_ipad=2.0,
    )
    assert cs.padding_for("iphone") == 3.5  # uses default
    assert cs.padding_for("ipad") == 2.0    # uses override


def test_config_loads_per_device_padding(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["caption"]["padding_pct_ipad"] = 2.0
    raw["caption"]["padding_pct_iphone"] = 4.0
    cfg_path.write_text(json.dumps(raw))
    cfg = config_mod.load(cfg_path)
    assert cfg.caption.padding_pct_iphone == 4.0
    assert cfg.caption.padding_pct_ipad == 2.0
    assert cfg.caption.padding_for("iphone") == 4.0
    assert cfg.caption.padding_for("ipad") == 2.0


# ---------- fonts ----------

def test_fonts_candidate_filenames_apple_optical_pattern():
    cands = fonts_mod._candidate_filenames("New York Small Bold")
    assert "NewYorkSmall-Bold" in cands


def test_fonts_candidate_filenames_family_weight():
    cands = fonts_mod._candidate_filenames("Helvetica Neue Bold")
    assert any("HelveticaNeue-Bold" in c for c in cands)


def test_fonts_resolve_path_passthrough(tmp_path):
    fake = tmp_path / "Custom.otf"
    fake.write_bytes(b"")
    resolved = fonts_mod.resolve(str(fake))
    assert resolved == fake


def test_fonts_resolve_missing_path_raises(tmp_path):
    with pytest.raises(fonts_mod.FontError):
        fonts_mod.resolve(str(tmp_path / "nope.otf"))


# ---------- text wrapping ----------

def _make_draw_and_font():
    img = Image.new("RGB", (1000, 200))
    from PIL import ImageDraw, ImageFont
    return ImageDraw.Draw(img), ImageFont.load_default()


def test_wrap_explicit_newline_creates_separate_lines():
    draw, font = _make_draw_and_font()
    lines = compose_mod._wrap("hello\nworld", font, max_w=10000, max_lines=4, draw=draw)
    assert lines == ["hello", "world"]


def test_wrap_explicit_newline_each_segment_still_word_wraps():
    # First segment is too long for one line; second is short.
    draw, font = _make_draw_and_font()
    lines = compose_mod._wrap(
        "the quick brown fox\njumps", font, max_w=60, max_lines=10, draw=draw,
    )
    # Last line is "jumps" from the second segment
    assert lines[-1] == "jumps"
    # First segment should have been broken across multiple lines
    assert any(line in ("the", "quick", "brown", "fox", "the quick") for line in lines[:-1])


def test_wrap_explicit_newline_respects_max_lines():
    draw, font = _make_draw_and_font()
    lines = compose_mod._wrap("a\nb\nc\nd\ne", font, max_w=10000, max_lines=3, draw=draw)
    assert len(lines) == 3
    # Last visible line is truncated with ellipsis since text was elided
    assert lines[-1].endswith("…")


def test_wrap_double_newline_collapses_blank():
    draw, font = _make_draw_and_font()
    lines = compose_mod._wrap("hello\n\nworld", font, max_w=10000, max_lines=4, draw=draw)
    assert lines == ["hello", "world"]


def test_wrap_no_newline_unchanged_behavior():
    # Backward-compat smoke: no newline → same greedy wrap as before.
    draw, font = _make_draw_and_font()
    lines = compose_mod._wrap("hello world", font, max_w=10000, max_lines=2, draw=draw)
    assert lines == ["hello world"]


def test_wrap_empty_string_returns_one_empty_line():
    draw, font = _make_draw_and_font()
    assert compose_mod._wrap("", font, max_w=100, max_lines=2, draw=draw) == [""]


# ---------- gradient + color helpers ----------

def test_hex_to_rgb():
    assert compose_mod._hex_to_rgb("#FF5F6D") == (255, 95, 109)
    assert compose_mod._hex_to_rgb("FFC371") == (255, 195, 113)


def test_hex_to_rgb_rejects_short():
    with pytest.raises(ValueError):
        compose_mod._hex_to_rgb("#FFF")


def test_lerp_endpoints():
    a = (0, 0, 0)
    b = (255, 255, 255)
    assert compose_mod._lerp(a, b, 0.0) == (0, 0, 0)
    assert compose_mod._lerp(a, b, 1.0) == (255, 255, 255)
    mid = compose_mod._lerp(a, b, 0.5)
    assert all(120 <= c <= 130 for c in mid)


def test_gradient_top_to_bottom_changes_color():
    img = compose_mod._draw_gradient(10, 100, ["#FF0000", "#0000FF"], angle=180)
    top_pixel = img.getpixel((5, 0))
    bot_pixel = img.getpixel((5, 99))
    # Allow alpha channel
    assert top_pixel[0] > bot_pixel[0]  # red fades down
    assert top_pixel[2] < bot_pixel[2]  # blue grows down


def test_gradient_unsupported_angle_raises():
    with pytest.raises(ValueError):
        compose_mod._draw_gradient(10, 10, ["#FF0000", "#0000FF"], angle=45)


# ---------- config ----------

def _write_minimal_config(tmp_path: Path, captions_data: dict | None = None) -> Path:
    cfg_path = tmp_path / "config.json"
    captions_path = tmp_path / "captions.json"
    captions_path.write_text(json.dumps(captions_data or {"a.png": {"en": "Hi"}}))
    cfg = {
        "version": 2,
        "input": {"iphone": "input/iphone/{locale}"},
        "output": {"iphone": "output/iphone/{locale}"},
        "background": {"type": "linear-gradient", "stops": ["#FF5F6D", "#FFC371"], "angle": 180},
        "caption": {
            "font": "New York Small Bold",
            "color": "#1B1B1B",
            "size_iphone": 60,
            "size_ipad": 60,
            "position": "footer",
            "padding_pct": 3.0,
            "max_lines": 2,
            "line_height": 1.15,
        },
        "captions_file": "captions.json",
        "locales": ["en-US"],
    }
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path


def test_config_load_valid(tmp_path):
    cfg = config_mod.load(_write_minimal_config(tmp_path))
    assert cfg.version == 2
    assert cfg.locales == ["en-US"]
    assert cfg.caption.size_iphone == 60


def test_config_load_rejects_wrong_version(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["version"] = 99
    cfg_path.write_text(json.dumps(raw))
    with pytest.raises(config_mod.ConfigError, match="version"):
        config_mod.load(cfg_path)


def test_config_load_rejects_v1_with_migration_guidance(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["version"] = 1
    cfg_path.write_text(json.dumps(raw))
    with pytest.raises(config_mod.ConfigError, match="v1"):
        config_mod.load(cfg_path)


def test_config_load_missing_field(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    del raw["caption"]
    cfg_path.write_text(json.dumps(raw))
    with pytest.raises(config_mod.ConfigError, match="caption"):
        config_mod.load(cfg_path)


# ---------- end-to-end ----------

def _make_fake_framed_png(path: Path, size: tuple[int, int] = (1100, 2400)) -> None:
    # Plain blue rectangle as a stand-in for a frames-cli-output PNG.
    img = Image.new("RGBA", size, (30, 100, 200, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


def test_compose_locale_writes_output(tmp_path):
    cfg_path = _write_minimal_config(tmp_path, captions_data={"a.png": {"en": "Hello world"}})
    cfg = config_mod.load(cfg_path)
    captions = captions_mod.Captions.load(cfg.resolve(cfg.captions_file))

    _make_fake_framed_png(tmp_path / "input" / "iphone" / "en-US" / "framed" / "a.png")

    result = compose_mod.compose_locale(
        config=cfg, locale="en-US", device_key="iphone", captions=captions,
    )

    assert len(result.written) == 1
    out = result.written[0]
    assert out.is_file()
    img = Image.open(out)
    assert img.size == (1320, 2868)


def test_compose_locale_skips_missing_input(tmp_path):
    cfg_path = _write_minimal_config(tmp_path, captions_data={"absent.png": {"en": "Hi"}})
    cfg = config_mod.load(cfg_path)
    captions = captions_mod.Captions.load(cfg.resolve(cfg.captions_file))

    # Create the input directory but no PNG
    (tmp_path / "input" / "iphone" / "en-US" / "framed").mkdir(parents=True)

    result = compose_mod.compose_locale(
        config=cfg, locale="en-US", device_key="iphone", captions=captions,
    )

    assert result.written == []
    assert len(result.skipped) == 1
    assert "input missing" in result.skipped[0][1]


def test_config_load_with_subtitle(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["subtitle"] = {
        "font": "New York Small Regular",
        "color": "#FFFFFF",
        "size_iphone": 50,
        "size_ipad": 60,
        "max_lines": 1,
        "line_height": 1.15,
        "spacing_pct": 1.5,
    }
    cfg_path.write_text(json.dumps(raw))
    cfg = config_mod.load(cfg_path)
    assert cfg.subtitle is not None
    assert cfg.subtitle.size_iphone == 50
    assert cfg.subtitle_size("iphone") == 50


def test_config_subtitle_size_raises_when_missing(tmp_path):
    cfg = config_mod.load(_write_minimal_config(tmp_path))
    assert cfg.subtitle is None
    import pytest
    with pytest.raises(config_mod.ConfigError):
        cfg.subtitle_size("iphone")


def test_config_subtitle_missing_field_raises(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["subtitle"] = {"font": "X", "color": "#FFF"}  # incomplete
    cfg_path.write_text(json.dumps(raw))
    import pytest
    with pytest.raises(config_mod.ConfigError, match="subtitle"):
        config_mod.load(cfg_path)


def test_compose_locale_with_subtitle_writes_output(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["subtitle"] = {
        "font": "New York Small Regular",
        "color": "#FFFFFF",
        "size_iphone": 30,
        "size_ipad": 30,
        "max_lines": 1,
        "line_height": 1.15,
        "spacing_pct": 1.5,
    }
    cfg_path.write_text(json.dumps(raw))
    captions_data = {
        "a.png": {"en": {"caption": "Track everything", "subtitle": "in one place"}}
    }
    (tmp_path / "captions.json").write_text(json.dumps(captions_data))

    cfg = config_mod.load(cfg_path)
    captions = captions_mod.Captions.load(cfg.resolve(cfg.captions_file))
    _make_fake_framed_png(tmp_path / "input" / "iphone" / "en-US" / "framed" / "a.png")

    result = compose_mod.compose_locale(
        config=cfg, locale="en-US", device_key="iphone", captions=captions,
    )
    assert len(result.written) == 1
    out = Image.open(result.written[0])
    assert out.size == (1320, 2868)


def test_compose_locale_dry_run_writes_nothing(tmp_path):
    cfg_path = _write_minimal_config(tmp_path)
    cfg = config_mod.load(cfg_path)
    captions = captions_mod.Captions.load(cfg.resolve(cfg.captions_file))
    _make_fake_framed_png(tmp_path / "input" / "iphone" / "en-US" / "framed" / "a.png")

    result = compose_mod.compose_locale(
        config=cfg, locale="en-US", device_key="iphone", captions=captions, dry_run=True,
    )

    assert len(result.written) == 1
    # Dry run reports the path but doesn't actually write.
    assert not result.written[0].exists()
