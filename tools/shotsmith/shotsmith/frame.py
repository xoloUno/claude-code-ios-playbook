"""Wrap frames-cli to add device bezels.

Reads PNGs from `<input>/<locale>/raw/` and invokes frames-cli to write framed
output to `<input>/<locale>/framed/`. Never modifies the raw/ directory.

frames-cli's CLI shape (per viticci/frames-cli):
    frames -o OUTPUT_DIR INPUT_FILES...

We invoke it once per (device, locale) batch so it can apply the right device
bezel based on the source image dimensions (frames-cli auto-detects device).

Honors `config.input_mapping` to translate capture-tool naming (e.g. XCUITest's
`01_HomeScreen.png`) into the consumer-facing canonical naming used by
captions.json (e.g. `02_HomeScreen.png` if a hero shot was numbered ahead).
Without a mapping, raw → framed is identity (`01.png` → `01.png`).

Skips files already present in framed/ unless `--force` is set, so iterative
re-runs are cheap. Reports written/skipped counts in the same shape as compose.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import devices
from .config import Config


class FrameError(RuntimeError):
    pass


@dataclass
class FrameResult:
    locale: str
    device: str
    written: list[Path]
    skipped: list[tuple[str, str]]  # (filename, reason)


def frame_locale(
    config: Config,
    locale: str,
    device_key: str,
    force: bool = False,
    dry_run: bool = False,
) -> FrameResult:
    """Frame all raw PNGs for one (locale, device) into framed/.

    Returns paths under `framed_dir`, named per the canonical scheme (which
    may differ from raw/ filenames if `config.input_mapping` is set).
    """
    if config.pipeline is None:
        raise FrameError(
            "Config has no `pipeline` block — frame requires "
            "pipeline.frames_cli to be configured."
        )

    devices.get(device_key)  # validates device_key
    raw_dir = config.raw_dir(device_key, locale)
    framed_dir = config.framed_dir(device_key, locale)

    if not raw_dir.is_dir():
        raise FrameError(
            f"{device_key}/{locale}: raw/ directory not found at {raw_dir}. "
            f"Run capture first."
        )

    targets = _resolve_targets(config, device_key, raw_dir)
    if not targets:
        raise FrameError(
            f"{device_key}/{locale}: no source PNGs to frame in {raw_dir}. "
            f"Either capture first, or check your input_mapping if configured."
        )

    if not dry_run:
        framed_dir.mkdir(parents=True, exist_ok=True)

    to_frame: list[tuple[Path, str]] = []  # (source_path, canonical_name)
    skipped: list[tuple[str, str]] = []
    for source_name, canonical_name in targets:
        source_path = raw_dir / source_name
        if not source_path.is_file():
            skipped.append((
                canonical_name,
                f"source {source_name} not found in raw/ "
                f"(check input_mapping or capture step)",
            ))
            continue
        target_path = framed_dir / canonical_name
        if target_path.exists() and not force:
            skipped.append((canonical_name, "already framed (pass --force to rebuild)"))
            continue
        to_frame.append((source_path, canonical_name))

    written: list[Path] = []
    if not to_frame:
        return FrameResult(
            locale=locale, device=device_key, written=written, skipped=skipped
        )

    if dry_run:
        for _, canonical in to_frame:
            written.append(framed_dir / canonical)
        return FrameResult(
            locale=locale, device=device_key, written=written, skipped=skipped
        )

    # frames-cli writes output named after its input file. To get canonical
    # names in framed/, we invoke frames-cli with sources from raw/ and then
    # rename the output to the canonical name. We process all targets in one
    # frames-cli invocation when source names equal canonical names; otherwise
    # we invoke per-file so we can rename precisely.
    _invoke_frames_cli(config, framed_dir, to_frame, written)

    return FrameResult(
        locale=locale, device=device_key, written=written, skipped=skipped
    )


def _resolve_targets(
    config: Config, device_key: str, raw_dir: Path
) -> list[tuple[str, str]]:
    """Return list of (source_filename, canonical_filename) pairs to frame.

    With `input_mapping` configured: iterates the mapping, source files come
    from the mapping values.
    Without mapping: iterates every PNG in raw_dir, source = canonical.
    """
    if config.input_mapping and device_key in config.input_mapping:
        device_map = config.input_mapping[device_key]
        return [(source, canonical) for canonical, source in device_map.items()]
    return [(p.name, p.name) for p in sorted(raw_dir.glob("*.png"))]


def _invoke_frames_cli(
    config: Config,
    framed_dir: Path,
    to_frame: list[tuple[Path, str]],
    written: list[Path],
) -> None:
    """Run frames-cli for each source, then rename output to canonical name.

    We run frames-cli once per file (rather than batched) because its output
    filename is derived from its input filename, and we need to rename each
    output to its canonical name regardless of what frames-cli chose.
    """
    for source_path, canonical_name in to_frame:
        cmd = [config.pipeline.frames_cli, "-o", str(framed_dir)]
        cmd.extend(config.pipeline.frames_args)
        cmd.append(str(source_path))

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False,
            )
        except FileNotFoundError as e:
            raise FrameError(
                f"frames-cli not found on PATH (looked for "
                f"'{config.pipeline.frames_cli}'). Install it or set "
                f"pipeline.frames_cli in your config to the right command name."
            ) from e

        if result.returncode != 0:
            raise FrameError(
                f"frames-cli exited {result.returncode} for {source_path.name}.\n"
                f"stdout: {result.stdout.strip()}\n"
                f"stderr: {result.stderr.strip()}"
            )

        # Find frames-cli's output and rename to canonical.
        produced = _find_produced(framed_dir, source_path)
        if produced is None:
            # frames-cli silently skipped — verify will catch missing output.
            continue
        target = framed_dir / canonical_name
        if produced != target:
            if target.exists():
                target.unlink()
            shutil.move(str(produced), str(target))
        written.append(target)


def _find_produced(framed_dir: Path, source: Path) -> Path | None:
    """Locate frames-cli's output for a given source.

    frames-cli may write `<source.stem>_framed.png` (default) or `<source.name>`
    (some versions / configs). Try both.
    """
    suffixed = framed_dir / f"{source.stem}_framed{source.suffix}"
    if suffixed.exists():
        return suffixed
    bare = framed_dir / source.name
    if bare.exists():
        return bare
    return None
