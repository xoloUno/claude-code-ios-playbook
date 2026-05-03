"""Tests for shotsmith verify."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shotsmith import config as config_mod  # noqa: E402
from shotsmith import verify as verify_mod  # noqa: E402


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "version": 2,
        "input": {"iphone": "input/iphone/{locale}"},
        "output": {"iphone": "output/iphone/{locale}"},
        "background": {"type": "linear-gradient", "stops": ["#000000", "#FFFFFF"], "angle": 180},
        "caption": {
            "font": "New York Small Bold", "color": "#1B1B1B",
            "size_iphone": 60, "size_ipad": 60, "position": "footer",
            "padding_pct": 3.0, "max_lines": 2, "line_height": 1.15,
        },
        "captions_file": "captions.json",
        "locales": ["en-US"],
        "pipeline": {"frames_cli": "frames", "verify_strict": True},
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    (tmp_path / "captions.json").write_text(json.dumps({"a.png": {"en": "Hi"}}))
    return cfg_path


def _make_png(
    path: Path,
    size: tuple[int, int],
    mode: str = "RGB",
    alpha: int = 255,
) -> None:
    """Synthesize a test PNG. `alpha` only applies when mode includes alpha."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "RGB":
        fill = (100, 100, 100)
    else:
        fill = (100, 100, 100, alpha)
    Image.new(mode, size, fill).save(path)


def test_verify_warns_when_raw_and_framed_missing(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    report = verify_mod.verify(cfg)
    assert report.ok  # missing raw/framed are warnings, not errors
    assert any("raw/" in w for w in report.warnings)
    assert any("framed/" in w for w in report.warnings)


def test_verify_clean_with_proper_inputs(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    raw_dir = cfg.raw_dir("iphone", "en-US")
    framed_dir = cfg.framed_dir("iphone", "en-US")
    _make_png(raw_dir / "01.png", (1100, 2400))
    _make_png(framed_dir / "01.png", (1470, 3000))  # matches DeviceProfile.framed_*
    report = verify_mod.verify(cfg)
    assert report.ok
    assert not report.warnings


def test_verify_accepts_rgba_with_transparent_borders(tmp_path):
    # frames-cli's actual output is RGBA with transparent borders around the
    # device frame. shotsmith composes that over the gradient. Transparency
    # in framed/ is therefore normal — verify must not flag it.
    cfg = config_mod.load(_write_config(tmp_path))
    framed_dir = cfg.framed_dir("iphone", "en-US")
    _make_png(framed_dir / "01.png", (1470, 3000), mode="RGBA", alpha=0)
    report = verify_mod.verify(cfg)
    assert not any("transparency" in e for e in report.errors)
    assert not any("alpha" in e for e in report.errors)


def test_verify_rejects_asc_composed_size_in_framed(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    framed_dir = cfg.framed_dir("iphone", "en-US")
    _make_png(framed_dir / "01.png", (1320, 2868))  # ASC composed iPhone size
    report = verify_mod.verify(cfg)
    assert not report.ok
    assert any("ASC composed size" in e for e in report.errors)


def test_verify_warns_but_does_not_error_on_unexpected_framed_dimensions(tmp_path):
    # Frames-cli output dims vary by capture device; treat mismatches as
    # warnings, not errors, so projects can use any iPad sim with ASC iPad 13"
    # canvas without false-positive verify failures.
    cfg = config_mod.load(_write_config(tmp_path))
    framed_dir = cfg.framed_dir("iphone", "en-US")
    _make_png(framed_dir / "01.png", (999, 999))
    report = verify_mod.verify(cfg)
    assert not any("differ from default" in e for e in report.errors)
    assert any("differ from default" in w for w in report.warnings)


def test_verify_rejects_orphan_pngs_at_locale_root(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    locale_root = cfg.framed_dir("iphone", "en-US").parent
    locale_root.mkdir(parents=True, exist_ok=True)
    _make_png(locale_root / "stray.png", (100, 100))
    report = verify_mod.verify(cfg)
    assert not report.ok
    assert any("at root of" in e for e in report.errors)


def test_verify_errors_when_manual_inputs_source_dir_missing(tmp_path):
    # Declare manual_inputs but don't create the source dir.
    raw = json.loads(_write_config(tmp_path).read_text())
    raw["manual_inputs"] = {
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png"],
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(raw))
    cfg = config_mod.load(tmp_path / "config.json")

    report = verify_mod.verify(cfg)
    assert not report.ok
    assert any("manual_inputs source dir missing" in e for e in report.errors)


def test_verify_errors_when_manual_inputs_file_missing(tmp_path):
    raw = json.loads(_write_config(tmp_path).read_text())
    raw["manual_inputs"] = {
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png", "91_HomeScreen.png"],
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(raw))
    cfg = config_mod.load(tmp_path / "config.json")

    # Source dir exists with one file, the other missing
    src = tmp_path / "manual-captures" / "en-US"
    _make_png(src / "90_LockScreen.png", (10, 10))

    report = verify_mod.verify(cfg)
    assert not report.ok
    msg = next(e for e in report.errors if "manual_inputs source(s) missing" in e)
    assert "91_HomeScreen.png" in msg
    assert "90_LockScreen.png" not in msg  # only the missing one is named


def test_verify_clean_when_manual_inputs_satisfied(tmp_path):
    raw = json.loads(_write_config(tmp_path).read_text())
    raw["manual_inputs"] = {
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png"],
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(raw))
    cfg = config_mod.load(tmp_path / "config.json")

    src = tmp_path / "manual-captures" / "en-US"
    _make_png(src / "90_LockScreen.png", (10, 10))
    raw_dir = cfg.raw_dir("iphone", "en-US")
    framed_dir = cfg.framed_dir("iphone", "en-US")
    _make_png(raw_dir / "01.png", (1100, 2400))
    _make_png(framed_dir / "01.png", (1470, 3000))

    report = verify_mod.verify(cfg)
    # No manual_inputs errors; warnings about raw/framed are still allowed
    assert not any("manual_inputs" in e for e in report.errors)


def test_verify_format_report_summarizes():
    report = verify_mod.VerifyReport()
    assert "clean" in verify_mod.format_report(report)
    report.warnings.append("a warning")
    assert "warning(s)" in verify_mod.format_report(report)
    report.errors.append("an error")
    assert "❌" in verify_mod.format_report(report)
