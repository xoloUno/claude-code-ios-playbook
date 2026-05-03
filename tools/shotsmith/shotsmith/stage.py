"""Stage manual-gesture inputs into raw/.

When a config declares `manual_inputs.{device}` with a source path template
and a list of files, the stage step copies each file from
`<source>/<file>` into `<raw_dir>/<file>` for each (device, locale).

This replaces per-project Fastfile staging blocks: the staging contract
lives in shotsmith config (one source of truth), and verify can report
specific missing manual-input files end-to-end (instead of a downstream
"missing source for 02_HomeScreen.png via input_mapping" indirection).

A config without `manual_inputs` makes stage a no-op — `pipeline` keeps
DEFAULT_STEPS = ("stage", "frame", "compose") so projects that don't use
manual_inputs aren't affected.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config


class StageError(RuntimeError):
    pass


@dataclass
class StageResult:
    device: str
    locale: str
    written: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (filename, reason)


def stage_locale(
    config: Config,
    locale: str,
    device_key: str,
    dry_run: bool = False,
) -> StageResult:
    """Stage all declared manual_inputs files for one (device, locale).

    Returns StageResult with `written` list and `skipped` tuples. Skipped
    reasons describe missing source files; the caller should treat those
    as fatal (verify catches them too — the duplication is intentional so
    shotsmith stage standalone is also safe).
    """
    result = StageResult(device=device_key, locale=locale)

    if config.manual_inputs is None:
        return result  # no-op when not configured
    device_block = config.manual_inputs.for_device(device_key)
    if device_block is None:
        return result  # no manual_inputs declared for this device

    source_dir = config.manual_source_dir(device_key, locale)
    raw_dir = config.raw_dir(device_key, locale)

    if not dry_run:
        raw_dir.mkdir(parents=True, exist_ok=True)

    for filename in device_block.files:
        src = source_dir / filename
        dst = raw_dir / filename
        if not src.is_file():
            result.skipped.append(
                (filename, f"source missing at {src}")
            )
            continue
        if dry_run:
            result.written.append(filename)
            continue
        shutil.copy2(src, dst)
        result.written.append(filename)

    return result


def stage_all(
    config: Config,
    device_keys: list[str] | None = None,
    locales: list[str] | None = None,
    dry_run: bool = False,
) -> list[StageResult]:
    """Stage manual_inputs for every (device, locale) combination."""
    device_keys = device_keys or config.device_keys()
    locales = locales or config.locales
    results: list[StageResult] = []
    for device_key in device_keys:
        for locale in locales:
            results.append(
                stage_locale(config, locale=locale, device_key=device_key, dry_run=dry_run)
            )
    return results
