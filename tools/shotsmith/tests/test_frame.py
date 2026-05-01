"""Tests for shotsmith frame.

Uses subprocess mocking via a fake `frames` shim on PATH to avoid requiring
the real frames-cli during tests.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import textwrap
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shotsmith import config as config_mod  # noqa: E402
from shotsmith import frame as frame_mod  # noqa: E402


def _write_config(tmp_path: Path, frames_cli: str = "frames") -> Path:
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
        "pipeline": {"frames_cli": frames_cli, "verify_strict": True},
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    (tmp_path / "captions.json").write_text("{}")
    return cfg_path


def _install_fake_frames(tmp_path: Path, write_suffix: str = "_framed") -> Path:
    """Create a fake `frames` shim on PATH that copies inputs to OUTPUT_DIR/<name><suffix>.png."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    shim = bin_dir / "frames"
    shim.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env python3
        import shutil, sys
        from pathlib import Path
        # Args: -o OUT_DIR FILE1 FILE2 ...
        args = sys.argv[1:]
        out_idx = args.index("-o") + 1
        out_dir = Path(args[out_idx])
        out_dir.mkdir(parents=True, exist_ok=True)
        files = args[out_idx + 1:]
        for f in files:
            src = Path(f)
            dest = out_dir / f"{{src.stem}}{write_suffix}{{src.suffix}}"
            shutil.copy(src, dest)
    """))
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _make_raw(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (200, 400), (50, 50, 200)).save(path)


def test_frame_requires_pipeline_block(tmp_path):
    cfg_path = _write_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    del raw["pipeline"]
    cfg_path.write_text(json.dumps(raw))
    cfg = config_mod.load(cfg_path)
    with pytest.raises(frame_mod.FrameError, match="pipeline"):
        frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")


def test_frame_errors_on_missing_raw(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    with pytest.raises(frame_mod.FrameError, match="raw/"):
        frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")


def test_frame_errors_on_empty_raw(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    cfg.raw_dir("iphone", "en-US").mkdir(parents=True)
    with pytest.raises(frame_mod.FrameError, match="no source PNGs"):
        frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")


def test_frame_writes_normalized_filenames(tmp_path, monkeypatch):
    cfg = config_mod.load(_write_config(tmp_path))
    bin_dir = _install_fake_frames(tmp_path, write_suffix="_framed")
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")
    _make_raw(raw_dir / "02.png")

    result = frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")
    assert len(result.written) == 2
    framed_dir = cfg.framed_dir("iphone", "en-US")
    assert (framed_dir / "01.png").exists()
    assert (framed_dir / "02.png").exists()
    # No _framed.png suffix should remain
    assert not list(framed_dir.glob("*_framed*.png"))


def test_frame_skips_already_framed_unless_force(tmp_path, monkeypatch):
    cfg = config_mod.load(_write_config(tmp_path))
    bin_dir = _install_fake_frames(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")
    framed_dir = cfg.framed_dir("iphone", "en-US")
    framed_dir.mkdir(parents=True, exist_ok=True)
    _make_raw(framed_dir / "01.png")  # pre-existing

    result = frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")
    assert len(result.written) == 0
    assert len(result.skipped) == 1
    assert "already framed" in result.skipped[0][1]

    # With force, it re-frames
    result_forced = frame_mod.frame_locale(
        cfg, locale="en-US", device_key="iphone", force=True
    )
    assert len(result_forced.written) == 1
    assert len(result_forced.skipped) == 0


def test_frame_dry_run_doesnt_invoke_frames_cli(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path, frames_cli="nonexistent-cmd"))
    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")
    result = frame_mod.frame_locale(
        cfg, locale="en-US", device_key="iphone", dry_run=True,
    )
    # Should not have raised even though frames_cli doesn't exist
    assert len(result.written) == 1


def test_frame_errors_when_frames_cli_not_on_path(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path, frames_cli="definitely-not-installed-xyz"))
    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")
    with pytest.raises(frame_mod.FrameError, match="not found on PATH"):
        frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")


# ---------- input_mapping ----------

def _write_config_with_mapping(tmp_path: Path) -> Path:
    cfg_path = _write_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["input_mapping"] = {
        "iphone": {
            # canonical → source (XCUITest names on the right; consumer-facing
            # canonical names on the left)
            "01_LiveActivities.png":   "from_simctl_NotificationCenter.png",
            "02_HomeScreen.png":        "01_HomeScreen.png",
            "08_HomeScreenDark.png":    "05_HomeScreenDark.png",
        }
    }
    cfg_path.write_text(json.dumps(raw))
    return cfg_path


def test_frame_with_mapping_renames_to_canonical(tmp_path, monkeypatch):
    cfg = config_mod.load(_write_config_with_mapping(tmp_path))
    bin_dir = _install_fake_frames(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "from_simctl_NotificationCenter.png")
    _make_raw(raw_dir / "01_HomeScreen.png")
    _make_raw(raw_dir / "05_HomeScreenDark.png")

    result = frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")
    assert len(result.written) == 3

    framed_dir = cfg.framed_dir("iphone", "en-US")
    # Outputs use canonical names, NOT source names.
    assert (framed_dir / "01_LiveActivities.png").exists()
    assert (framed_dir / "02_HomeScreen.png").exists()
    assert (framed_dir / "08_HomeScreenDark.png").exists()
    # Source names are NOT in framed/
    assert not (framed_dir / "01_HomeScreen.png").exists()
    assert not (framed_dir / "05_HomeScreenDark.png").exists()


def test_frame_with_mapping_skips_when_source_missing(tmp_path, monkeypatch):
    cfg = config_mod.load(_write_config_with_mapping(tmp_path))
    bin_dir = _install_fake_frames(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    raw_dir = cfg.raw_dir("iphone", "en-US")
    # Only one of three sources present; other two should be skipped with
    # actionable reason mentioning the source filename.
    _make_raw(raw_dir / "01_HomeScreen.png")

    result = frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")
    assert len(result.written) == 1
    assert len(result.skipped) == 2
    skipped_reasons = " ".join(reason for _, reason in result.skipped)
    assert "from_simctl_NotificationCenter.png" in skipped_reasons
    assert "05_HomeScreenDark.png" in skipped_reasons


def test_frame_without_mapping_uses_identity(tmp_path, monkeypatch):
    # Backward-compat: with no input_mapping, raw filename = framed filename.
    cfg = config_mod.load(_write_config(tmp_path))
    bin_dir = _install_fake_frames(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")
    _make_raw(raw_dir / "02.png")

    result = frame_mod.frame_locale(cfg, locale="en-US", device_key="iphone")
    framed_dir = cfg.framed_dir("iphone", "en-US")
    assert (framed_dir / "01.png").exists()
    assert (framed_dir / "02.png").exists()


def test_config_input_mapping_validates_shape(tmp_path):
    cfg_path = _write_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["input_mapping"] = "not an object"
    cfg_path.write_text(json.dumps(raw))
    with pytest.raises(config_mod.ConfigError, match="input_mapping"):
        config_mod.load(cfg_path)


def test_config_input_mapping_validates_inner_shape(tmp_path):
    cfg_path = _write_config(tmp_path)
    raw = json.loads(cfg_path.read_text())
    raw["input_mapping"] = {"iphone": "not an object"}
    cfg_path.write_text(json.dumps(raw))
    with pytest.raises(config_mod.ConfigError, match="iphone"):
        config_mod.load(cfg_path)


def test_config_source_filename_helper(tmp_path):
    cfg = config_mod.load(_write_config_with_mapping(tmp_path))
    assert cfg.source_filename("iphone", "01_LiveActivities.png") == "from_simctl_NotificationCenter.png"
    # Identity for canonical names not in the mapping
    assert cfg.source_filename("iphone", "anything_else.png") == "anything_else.png"
    # Identity for devices with no mapping
    assert cfg.source_filename("ipad", "any.png") == "any.png"
