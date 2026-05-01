"""Tests for shotsmith pipeline orchestration."""

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
from shotsmith import pipeline as pipeline_mod  # noqa: E402


def _write_config(
    tmp_path: Path, capture_hook: str | None = None,
    verify_strict: bool = True,
) -> Path:
    pl = {"frames_cli": "frames", "verify_strict": verify_strict}
    if capture_hook is not None:
        pl["capture_hook"] = capture_hook
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
        "pipeline": pl,
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    (tmp_path / "captions.json").write_text(json.dumps({"01.png": {"en": "Hi"}}))
    return cfg_path


def _install_fake_frames(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    shim = bin_dir / "frames"
    shim.write_text(textwrap.dedent("""\
        #!/usr/bin/env python3
        # Reads PNGs and writes them framed at 1470x3000 (iPhone 6.9" expected).
        from PIL import Image
        import shutil, sys
        from pathlib import Path
        args = sys.argv[1:]
        out_idx = args.index("-o") + 1
        out_dir = Path(args[out_idx])
        out_dir.mkdir(parents=True, exist_ok=True)
        for f in args[out_idx + 1:]:
            src = Path(f)
            framed = Image.new("RGB", (1470, 3000), (10, 10, 10))
            framed.paste(Image.open(src).resize((1100, 2400)), (185, 300))
            framed.save(out_dir / f"{src.stem}_framed{src.suffix}")
    """))
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _make_raw(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (200, 400), (50, 50, 200)).save(path)


def test_pipeline_invalid_step_raises(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    with pytest.raises(pipeline_mod.PipelineError, match="Invalid step"):
        pipeline_mod.run(cfg, steps=("frame", "bogus"))


def test_pipeline_capture_step_requires_hook(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))  # no capture_hook
    with pytest.raises(pipeline_mod.PipelineError, match="capture_hook"):
        pipeline_mod.run(cfg, steps=("capture", "frame"))


def test_pipeline_strict_aborts_on_verify_errors(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path, verify_strict=True))
    framed_dir = cfg.framed_dir("iphone", "en-US")
    framed_dir.mkdir(parents=True)
    # Plant a PNG at the ASC composed canvas size — that's the real "prior
    # composition leaked into framed/" signature, which verify still treats
    # as an error.
    Image.new("RGB", (1320, 2868)).save(framed_dir / "bad.png")
    with pytest.raises(pipeline_mod.PipelineError, match="verify failed"):
        pipeline_mod.run(cfg, steps=("compose",))


def test_pipeline_non_strict_continues_on_verify_errors(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path, verify_strict=False))
    framed_dir = cfg.framed_dir("iphone", "en-US")
    framed_dir.mkdir(parents=True)
    Image.new("RGB", (1320, 2868)).save(framed_dir / "bad.png")
    # Should not raise — runs compose anyway (which will skip the file since
    # it's not in captions). This is the non-strict contract.
    result = pipeline_mod.run(cfg, steps=("compose",))
    assert result.verify_report.errors  # errors still surfaced


def test_pipeline_frame_then_compose_end_to_end(tmp_path, monkeypatch):
    cfg_path = _write_config(tmp_path, verify_strict=False)
    cfg = config_mod.load(cfg_path)
    bin_dir = _install_fake_frames(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")

    result = pipeline_mod.run(cfg, steps=("frame", "compose"))
    assert len(result.frame_results) == 1
    assert len(result.frame_results[0].written) == 1
    assert len(result.compose_results) == 1
    assert len(result.compose_results[0].written) == 1
    composed = result.compose_results[0].written[0]
    assert composed.exists()
    img = Image.open(composed)
    assert img.size == (1320, 2868)


def test_pipeline_capture_invokes_hook_with_env(tmp_path, monkeypatch):
    # Capture hook script that writes a marker file to SHOTSMITH_RAW_DIR.
    hook = tmp_path / "capture.sh"
    hook.write_text(textwrap.dedent("""\
        #!/usr/bin/env bash
        echo "device=$SHOTSMITH_DEVICE locale=$SHOTSMITH_LOCALE raw=$SHOTSMITH_RAW_DIR" \\
            > "$SHOTSMITH_RAW_DIR/marker.txt"
    """))
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    cfg = config_mod.load(_write_config(
        tmp_path, capture_hook=str(hook), verify_strict=False,
    ))

    result = pipeline_mod.run(cfg, steps=("capture",))
    assert len(result.capture_results) == 1
    marker = cfg.raw_dir("iphone", "en-US") / "marker.txt"
    assert marker.exists()
    contents = marker.read_text()
    assert "device=iphone" in contents
    assert "locale=en-US" in contents


def test_pipeline_dry_run_does_not_invoke_subprocesses(tmp_path):
    cfg = config_mod.load(_write_config(
        tmp_path, capture_hook="/nonexistent", verify_strict=False,
    ))
    raw_dir = cfg.raw_dir("iphone", "en-US")
    _make_raw(raw_dir / "01.png")
    # Should not raise even though capture_hook doesn't exist and frames isn't on PATH
    pipeline_mod.run(cfg, steps=("frame", "compose"), dry_run=True)
