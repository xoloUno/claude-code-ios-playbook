"""shotsmith CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, devices
from .captions import Captions, CaptionsError
from .compose import ComposeResult, compose_locale
from .config import Config, ConfigError, load as load_config
from .frame import FrameError, FrameResult, frame_locale
from .pipeline import DEFAULT_STEPS, VALID_STEPS, PipelineError, run as run_pipeline
from .verify import format_report, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shotsmith",
        description=(
            "Compose App Store screenshots: orchestrate capture → frame → compose. "
            "Stable raw/+framed/+composed/ directory contract."
        ),
    )
    parser.add_argument("--version", action="version", version=f"shotsmith {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared filters
    def add_common_filters(p):
        p.add_argument("--config", "-c", required=True, type=Path, help="Path to config.json")
        p.add_argument(
            "--locale", action="append",
            help="Restrict to one or more locales (default: all in config). Repeatable.",
        )
        p.add_argument(
            "--device", action="append", choices=sorted(devices.DEVICES.keys()),
            help="Restrict to one or more devices. Repeatable.",
        )

    p_compose = sub.add_parser("compose", help="Compose screenshots from framed/ inputs")
    add_common_filters(p_compose)
    p_compose.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be composed without writing PNGs.",
    )

    p_frame = sub.add_parser("frame", help="Frame raw/ inputs via frames-cli into framed/")
    add_common_filters(p_frame)
    p_frame.add_argument(
        "--force", action="store_true",
        help="Re-frame PNGs even if framed/ already contains them.",
    )
    p_frame.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be framed without invoking frames-cli.",
    )

    p_verify = sub.add_parser("verify", help="Validate raw/+framed/+composed/ directory contract")
    add_common_filters(p_verify)

    p_pipeline = sub.add_parser(
        "pipeline", help="Run capture (optional) → frame → compose end-to-end"
    )
    add_common_filters(p_pipeline)
    p_pipeline.add_argument(
        "--steps", default=",".join(DEFAULT_STEPS),
        help=(
            f"Comma-separated steps to run. Valid: {','.join(VALID_STEPS)}. "
            f"Default: {','.join(DEFAULT_STEPS)} (capture is opt-in via --steps capture,...)."
        ),
    )
    p_pipeline.add_argument(
        "--force", action="store_true",
        help="Pass --force to the frame step (re-frame existing).",
    )
    p_pipeline.add_argument(
        "--dry-run", action="store_true",
        help="Plan everything without invoking subprocesses or writing PNGs.",
    )

    args = parser.parse_args(argv)

    if args.command == "compose":
        return _cmd_compose(args)
    if args.command == "frame":
        return _cmd_frame(args)
    if args.command == "verify":
        return _cmd_verify(args)
    if args.command == "pipeline":
        return _cmd_pipeline(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _load_or_die(path: Path) -> Config:
    try:
        return load_config(path)
    except ConfigError as e:
        print(f"❌ Config error: {e}", file=sys.stderr)
        sys.exit(2)


def _cmd_compose(args) -> int:
    config = _load_or_die(args.config)
    try:
        captions = Captions.load(config.resolve(config.captions_file))
    except CaptionsError as e:
        print(f"❌ Captions error: {e}", file=sys.stderr)
        return 2

    locales = args.locale or config.locales
    device_keys = args.device or config.device_keys()

    total_written = 0
    total_skipped = 0
    for device_key in device_keys:
        for locale in locales:
            try:
                result = compose_locale(
                    config=config, locale=locale, device_key=device_key,
                    captions=captions, dry_run=args.dry_run,
                )
            except FileNotFoundError as e:
                print(f"⚠️  {device_key}/{locale}: {e}", file=sys.stderr)
                continue
            _print_compose_result(result, dry_run=args.dry_run)
            total_written += len(result.written)
            total_skipped += len(result.skipped)

    verb = "would write" if args.dry_run else "wrote"
    print(f"\n✅ Done. {verb} {total_written} image(s); skipped {total_skipped}.")
    return 0


def _cmd_frame(args) -> int:
    config = _load_or_die(args.config)
    locales = args.locale or config.locales
    device_keys = args.device or config.device_keys()

    total_written = 0
    total_skipped = 0
    for device_key in device_keys:
        for locale in locales:
            try:
                result = frame_locale(
                    config, locale=locale, device_key=device_key,
                    force=args.force, dry_run=args.dry_run,
                )
            except FrameError as e:
                print(f"❌ {device_key}/{locale}: {e}", file=sys.stderr)
                return 1
            _print_frame_result(result, dry_run=args.dry_run)
            total_written += len(result.written)
            total_skipped += len(result.skipped)

    verb = "would frame" if args.dry_run else "framed"
    print(f"\n✅ Done. {verb} {total_written} image(s); skipped {total_skipped}.")
    return 0


def _cmd_verify(args) -> int:
    config = _load_or_die(args.config)
    locales = args.locale or config.locales
    device_keys = args.device or config.device_keys()
    report = verify(config, device_keys=device_keys, locales=locales)
    print(format_report(report))
    if report.errors:
        return 2
    if report.warnings:
        return 1
    return 0


def _cmd_pipeline(args) -> int:
    config = _load_or_die(args.config)
    steps = tuple(s.strip() for s in args.steps.split(",") if s.strip())
    locales = args.locale or config.locales
    device_keys = args.device or config.device_keys()

    print(f"▶ Pipeline steps: {','.join(steps)}")
    try:
        result = run_pipeline(
            config, steps=steps, device_keys=device_keys, locales=locales,
            force_frame=args.force, dry_run=args.dry_run,
        )
    except PipelineError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    if result.verify_report.errors or result.verify_report.warnings:
        print("\n— verify —")
        print(format_report(result.verify_report))

    if result.frame_results:
        print("\n— frame —")
        for fr in result.frame_results:
            _print_frame_result(fr, dry_run=args.dry_run)

    if result.compose_results:
        print("\n— compose —")
        for cr in result.compose_results:
            _print_compose_result(cr, dry_run=args.dry_run)

    print("\n✅ Pipeline done.")
    return 0


def _print_compose_result(result: ComposeResult, dry_run: bool) -> None:
    label = f"{result.device}/{result.locale}"
    if result.written:
        verb = "would write" if dry_run else "wrote"
        print(f"  {label}: {verb} {len(result.written)} image(s)")
    for filename, reason in result.skipped:
        print(f"  {label}: skipped {filename} ({reason})")


def _print_frame_result(result: FrameResult, dry_run: bool) -> None:
    label = f"{result.device}/{result.locale}"
    if result.written:
        verb = "would frame" if dry_run else "framed"
        print(f"  {label}: {verb} {len(result.written)} image(s)")
    for filename, reason in result.skipped:
        print(f"  {label}: skipped {filename} ({reason})")


if __name__ == "__main__":
    sys.exit(main())
