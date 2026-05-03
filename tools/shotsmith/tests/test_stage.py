"""Tests for shotsmith stage step (manual_inputs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shotsmith import config as config_mod  # noqa: E402
from shotsmith import stage as stage_mod  # noqa: E402


def _write_config(
    tmp_path: Path,
    manual_inputs: dict | None = None,
) -> Path:
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
    if manual_inputs is not None:
        cfg["manual_inputs"] = manual_inputs
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    (tmp_path / "captions.json").write_text(json.dumps({"a.png": {"en": "Hi"}}))
    return cfg_path


def _make_png(path: Path, size: tuple[int, int] = (10, 10)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (100, 100, 100)).save(path)


def test_stage_no_op_without_manual_inputs(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    result = stage_mod.stage_locale(cfg, locale="en-US", device_key="iphone")
    assert result.written == []
    assert result.skipped == []


def test_stage_copies_declared_files_into_raw(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png", "91_HomeScreen.png"],
        }
    })
    cfg = config_mod.load(cfg_path)

    src = tmp_path / "manual-captures" / "en-US"
    _make_png(src / "90_LockScreen.png")
    _make_png(src / "91_HomeScreen.png")

    result = stage_mod.stage_locale(cfg, locale="en-US", device_key="iphone")

    assert sorted(result.written) == ["90_LockScreen.png", "91_HomeScreen.png"]
    assert result.skipped == []
    raw_dir = cfg.raw_dir("iphone", "en-US")
    assert (raw_dir / "90_LockScreen.png").is_file()
    assert (raw_dir / "91_HomeScreen.png").is_file()


def test_stage_reports_missing_source_file(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png", "91_HomeScreen.png"],
        }
    })
    cfg = config_mod.load(cfg_path)

    src = tmp_path / "manual-captures" / "en-US"
    _make_png(src / "90_LockScreen.png")  # 91 intentionally missing

    result = stage_mod.stage_locale(cfg, locale="en-US", device_key="iphone")

    assert result.written == ["90_LockScreen.png"]
    assert len(result.skipped) == 1
    assert result.skipped[0][0] == "91_HomeScreen.png"
    assert "missing" in result.skipped[0][1]


def test_stage_dry_run_does_not_copy(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png"],
        }
    })
    cfg = config_mod.load(cfg_path)

    src = tmp_path / "manual-captures" / "en-US"
    _make_png(src / "90_LockScreen.png")

    result = stage_mod.stage_locale(cfg, locale="en-US", device_key="iphone", dry_run=True)
    assert result.written == ["90_LockScreen.png"]
    raw_dir = cfg.raw_dir("iphone", "en-US")
    assert not (raw_dir / "90_LockScreen.png").exists()


def test_stage_skips_devices_not_declared(tmp_path):
    # Only iphone has manual_inputs — staging ipad is a no-op.
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90_LockScreen.png"],
        }
    })
    # Add ipad to input/output so device_keys() returns it
    raw = json.loads(cfg_path.read_text())
    raw["input"]["ipad"] = "input/ipad/{locale}"
    raw["output"]["ipad"] = "output/ipad/{locale}"
    cfg_path.write_text(json.dumps(raw))
    cfg = config_mod.load(cfg_path)

    result = stage_mod.stage_locale(cfg, locale="en-US", device_key="ipad")
    assert result.written == []
    assert result.skipped == []


def test_stage_locale_template_expands(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {
            "source": "manual-captures/{locale}",
            "files": ["90.png"],
        }
    })
    cfg = config_mod.load(cfg_path)

    # Two locale-specific source dirs
    _make_png(tmp_path / "manual-captures" / "en-US" / "90.png")
    _make_png(tmp_path / "manual-captures" / "es-ES" / "90.png")

    en = stage_mod.stage_locale(cfg, locale="en-US", device_key="iphone")
    es = stage_mod.stage_locale(cfg, locale="es-ES", device_key="iphone")

    assert en.written == ["90.png"]
    assert es.written == ["90.png"]
    assert (cfg.raw_dir("iphone", "en-US") / "90.png").is_file()
    assert (cfg.raw_dir("iphone", "es-ES") / "90.png").is_file()


def test_config_rejects_invalid_manual_inputs_shape(tmp_path):
    # source must be a string
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {"source": 123, "files": ["x.png"]}
    })
    with pytest.raises(config_mod.ConfigError, match="source must be a string"):
        config_mod.load(cfg_path)


def test_config_rejects_empty_files_list(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {"source": "x/{locale}", "files": []}
    })
    with pytest.raises(config_mod.ConfigError, match="non-empty list"):
        config_mod.load(cfg_path)


def test_config_rejects_non_string_filenames(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {"source": "x/{locale}", "files": ["valid.png", 42]}
    })
    with pytest.raises(config_mod.ConfigError, match="must be strings"):
        config_mod.load(cfg_path)


def test_config_rejects_missing_source_field(tmp_path):
    cfg_path = _write_config(tmp_path, manual_inputs={
        "iphone": {"files": ["x.png"]}
    })
    with pytest.raises(config_mod.ConfigError, match="missing required field 'source'"):
        config_mod.load(cfg_path)
