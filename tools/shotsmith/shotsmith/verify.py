"""Verify the shotsmith pipeline directory contract.

For each (device, locale) configured, checks:
- raw/ exists (warns if missing)
- framed/ exists (warns if missing)
- Each PNG in framed/ has the expected frames-cli output dimensions
- No PNG in framed/ matches the ASC composed size exactly (= already composed
  — caught the "appshot-final-masquerading-as-framed-input" bug class).
  We do NOT flag transparency in framed/: some frames-cli variants output RGBA
  with transparent borders around the device frame, which shotsmith composes
  over the gradient (the gradient shows through, by design).
- No PNG at the locale root (anti-pattern: PNGs belong in raw/ or framed/)

Returns a structured `VerifyReport` describing errors + warnings. Errors block
`shotsmith pipeline` when `pipeline.verify_strict: true` (default). Warnings
never block but are surfaced to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from . import devices
from .config import Config


@dataclass
class VerifyReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def merge(self, other: "VerifyReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def verify(
    config: Config,
    device_keys: list[str] | None = None,
    locales: list[str] | None = None,
) -> VerifyReport:
    """Run all verify checks. Returns a report with errors + warnings."""
    report = VerifyReport()
    device_keys = device_keys or config.device_keys()
    locales = locales or config.locales

    for device_key in device_keys:
        device = devices.get(device_key)
        for locale in locales:
            report.merge(_verify_one(config, device, device_key, locale))

    return report


def _verify_one(
    config: Config, device, device_key: str, locale: str
) -> VerifyReport:
    report = VerifyReport()
    raw_dir = config.raw_dir(device_key, locale)
    framed_dir = config.framed_dir(device_key, locale)
    locale_root = raw_dir.parent  # the per-locale dir containing raw/ + framed/

    # Orphan PNGs at the locale root are an anti-pattern signal.
    if locale_root.is_dir():
        orphans = sorted(locale_root.glob("*.png"))
        if orphans:
            report.errors.append(
                f"{device_key}/{locale}: {len(orphans)} PNG(s) at root of "
                f"{locale_root} — PNGs belong in raw/ or framed/ subdirs only. "
                f"First offender: {orphans[0].name}"
            )

    # raw/ presence — warning, not error (capture step may not have run yet)
    if not raw_dir.is_dir() or not list(raw_dir.glob("*.png")):
        report.warnings.append(
            f"{device_key}/{locale}: raw/ is missing or empty at {raw_dir}. "
            f"Run capture (XCUITest or your project's capture script) first."
        )

    # framed/ presence — warning, not error
    framed_pngs = sorted(framed_dir.glob("*.png")) if framed_dir.is_dir() else []
    if not framed_pngs:
        report.warnings.append(
            f"{device_key}/{locale}: framed/ is missing or empty at {framed_dir}. "
            f"Run `shotsmith frame --config X --device {device_key} --locale {locale}`."
        )
        return report  # nothing to inspect inside framed/

    # Inspect each framed PNG.
    for png in framed_pngs:
        try:
            with Image.open(png) as img:
                w, h = img.size
                mode = img.mode
        except Exception as e:
            report.errors.append(f"{png}: failed to open ({e})")
            continue

        # Reject if dimensions match the ASC composed size (= already composed).
        if (w, h) == (device.width, device.height):
            report.errors.append(
                f"{png}: dimensions {w}x{h} match ASC composed size for {device_key} — "
                f"this is shotsmith's OUTPUT size, not frames-cli's output. The PNG "
                f"appears to be a prior composition (appshot final or shotsmith composed). "
                f"Move it out of framed/ and re-run frame from raw/."
            )
            continue

        # Warn if dimensions don't match the default expected frames-cli output
        # for this device profile. Downgraded from error to warning because
        # frames-cli output dimensions legitimately vary by capture device:
        # capturing on iPad Pro 11" produces different framed dims than iPad
        # Pro 13", and projects may pick whichever capture device suits them
        # while still composing to the same ASC slot. The real safety net is
        # the "matches ASC composed size" check above, which catches the
        # actual bug class (prior composition placed into framed/).
        if (w, h) != (device.framed_width, device.framed_height):
            report.warnings.append(
                f"{png}: dimensions {w}x{h} differ from default frames-cli "
                f"output {device.framed_width}x{device.framed_height} for "
                f"{device_key}. Likely fine if you're capturing on a different "
                f"sim than the DeviceProfile default."
            )

        # Note: we don't flag transparency in framed/. Some frames-cli variants
        # legitimately output RGBA with transparent borders surrounding the
        # device frame — shotsmith composes that over the gradient, which is
        # the desired visual (gradient shows through the transparent border).
        # The actual signature of "prior composition leaked into framed/" is
        # the ASC-canvas-size match check above, which is sufficient.

    return report


def format_report(report: VerifyReport) -> str:
    """Human-readable report for CLI output."""
    out: list[str] = []
    for err in report.errors:
        out.append(f"❌ {err}")
    for warn in report.warnings:
        out.append(f"⚠️  {warn}")
    if report.ok and not report.warnings:
        out.append("✅ verify clean")
    elif report.ok:
        out.append(
            f"✅ verify passed with {len(report.warnings)} warning(s)"
        )
    else:
        out.append(
            f"❌ verify failed: {len(report.errors)} error(s), "
            f"{len(report.warnings)} warning(s)"
        )
    return "\n".join(out)
