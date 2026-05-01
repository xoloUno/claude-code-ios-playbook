"""Pipeline orchestrator: capture (optional hook) → frame → compose.

Always runs `verify` first. If `pipeline.verify_strict` is true (default),
verify errors abort before any work. Warnings never abort, only get surfaced.

Capture is opt-in via `--steps capture`. Default `--steps frame,compose`
matches the typical workflow: capture once (expensive), iterate on framing
+ composition (cheap).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .captions import Captions, CaptionsError
from .compose import ComposeResult, compose_locale
from .config import Config
from .frame import FrameError, FrameResult, frame_locale
from .verify import VerifyReport, format_report, verify

VALID_STEPS = ("capture", "frame", "compose")
DEFAULT_STEPS = ("frame", "compose")


class PipelineError(RuntimeError):
    pass


@dataclass
class PipelineResult:
    verify_report: VerifyReport
    capture_results: list[tuple[str, str, int]] = field(default_factory=list)  # (device, locale, exit_code)
    frame_results: list[FrameResult] = field(default_factory=list)
    compose_results: list[ComposeResult] = field(default_factory=list)


def run(
    config: Config,
    steps: tuple[str, ...] = DEFAULT_STEPS,
    device_keys: list[str] | None = None,
    locales: list[str] | None = None,
    force_frame: bool = False,
    dry_run: bool = False,
) -> PipelineResult:
    for step in steps:
        if step not in VALID_STEPS:
            raise PipelineError(
                f"Invalid step '{step}'. Valid: {', '.join(VALID_STEPS)}"
            )

    device_keys = device_keys or config.device_keys()
    locales = locales or config.locales

    result = PipelineResult(verify_report=VerifyReport())

    # Verify always runs. Errors abort iff pipeline.verify_strict is true.
    # We verify the CURRENT state before doing work — so a fresh project with
    # empty raw/ + framed/ will only show warnings, which is fine.
    pre_verify = verify(config, device_keys=device_keys, locales=locales)
    result.verify_report.merge(pre_verify)
    strict = config.pipeline is None or config.pipeline.verify_strict
    if strict and pre_verify.errors:
        raise PipelineError(
            f"verify failed (strict mode):\n{format_report(pre_verify)}"
        )

    if "capture" in steps:
        if config.pipeline is None or not config.pipeline.capture_hook:
            raise PipelineError(
                "Step 'capture' requested but pipeline.capture_hook is not "
                "configured. Either remove 'capture' from --steps or set "
                "pipeline.capture_hook to your project's capture script path."
            )
        for device_key in device_keys:
            for locale in locales:
                exit_code = _run_capture_hook(
                    config, device_key, locale, dry_run=dry_run
                )
                result.capture_results.append((device_key, locale, exit_code))
                if exit_code != 0:
                    raise PipelineError(
                        f"capture hook failed for {device_key}/{locale} "
                        f"(exit {exit_code})"
                    )

    if "frame" in steps:
        for device_key in device_keys:
            for locale in locales:
                try:
                    fr = frame_locale(
                        config, locale=locale, device_key=device_key,
                        force=force_frame, dry_run=dry_run,
                    )
                    result.frame_results.append(fr)
                except FrameError as e:
                    raise PipelineError(f"frame failed: {e}") from e

    if "compose" in steps:
        try:
            captions = Captions.load(config.resolve(config.captions_file))
        except CaptionsError as e:
            raise PipelineError(f"captions load failed: {e}") from e

        for device_key in device_keys:
            for locale in locales:
                try:
                    cr = compose_locale(
                        config=config, locale=locale, device_key=device_key,
                        captions=captions, dry_run=dry_run,
                    )
                    result.compose_results.append(cr)
                except FileNotFoundError as e:
                    # Surface as warning, not pipeline failure — verify already
                    # told the user about missing inputs.
                    result.verify_report.warnings.append(
                        f"compose skipped {device_key}/{locale}: {e}"
                    )

    return result


def _run_capture_hook(
    config: Config, device_key: str, locale: str, dry_run: bool
) -> int:
    """Invoke the project's capture hook for one (device, locale).

    Hook receives:
      SHOTSMITH_DEVICE   = device key (e.g. 'iphone')
      SHOTSMITH_LOCALE   = locale (e.g. 'en-US')
      SHOTSMITH_RAW_DIR  = absolute path to write raw PNGs into
    """
    hook = config.pipeline.capture_hook
    hook_path = config.resolve(hook) if not Path(hook).is_absolute() else Path(hook)
    if not hook_path.is_file():
        raise PipelineError(f"capture_hook not found: {hook_path}")

    raw_dir = config.raw_dir(device_key, locale)
    if not dry_run:
        raw_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["SHOTSMITH_DEVICE"] = device_key
    env["SHOTSMITH_LOCALE"] = locale
    env["SHOTSMITH_RAW_DIR"] = str(raw_dir)

    if dry_run:
        return 0

    proc = subprocess.run([str(hook_path)], env=env, check=False)
    return proc.returncode
