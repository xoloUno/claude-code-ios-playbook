"""Config loading + validation.

The config is a JSON document describing how to compose screenshots: where to
read framed input PNGs from, where to write composed output PNGs to, what
background to draw, what font and size to use for captions, and which locales
to iterate.

Schema is validated at load time — invalid configs raise ConfigError with a
specific message rather than failing later during composition.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import devices


SUPPORTED_VERSION = 2


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Background:
    type: str
    stops: list[str]
    angle: int
    dither: int = 0  # Gaussian noise sigma 0..255; 0 disables. Subtle range: 4..12.


@dataclass(frozen=True)
class CaptionStyle:
    font: str
    color: str
    size_iphone: int
    size_ipad: int
    position: str
    padding_pct: float
    max_lines: int
    line_height: float
    # Optional per-device padding overrides. None falls back to padding_pct.
    # Useful when one device wants tighter framing (e.g. iPad to recover
    # image_area on its wider canvas).
    padding_pct_iphone: float | None = None
    padding_pct_ipad: float | None = None

    def padding_for(self, device_key: str) -> float:
        if device_key == "iphone" and self.padding_pct_iphone is not None:
            return self.padding_pct_iphone
        if device_key == "ipad" and self.padding_pct_ipad is not None:
            return self.padding_pct_ipad
        return self.padding_pct


@dataclass(frozen=True)
class Pipeline:
    capture_hook: str | None  # path to project-defined capture script; None disables capture step
    frames_cli: str           # command on PATH (default "frames")
    frames_args: list[str]    # extra args to frames-cli invocation
    verify_strict: bool       # True = pipeline aborts on verify errors; False = warn-only


@dataclass(frozen=True)
class ManualInputDevice:
    source: str         # config-relative path template; supports {locale}
    files: list[str]    # expected manual-input filenames (e.g. ["90_LockScreen.png", ...])


@dataclass(frozen=True)
class ManualInputs:
    """Declared manual-gesture inputs that get staged into raw/ before frame.

    Per-device map of {device_key: {source: <path-template>, files: [...]}}.
    `source` is config-relative and supports `{locale}` substitution. The
    `stage` pipeline step copies declared files from
    `<source>/<file>` into `<raw_dir>/<file>` for each (device, locale).
    """
    by_device: dict[str, ManualInputDevice]

    def for_device(self, device_key: str) -> ManualInputDevice | None:
        return self.by_device.get(device_key)


@dataclass(frozen=True)
class SubtitleStyle:
    font: str
    color: str
    size_iphone: int
    size_ipad: int
    max_lines: int
    line_height: float
    spacing_pct: float  # gap between caption and subtitle, as % of canvas height


@dataclass(frozen=True)
class Config:
    version: int
    input_paths: dict[str, str]
    output_paths: dict[str, str]
    background: Background
    caption: CaptionStyle
    captions_file: str
    locales: list[str]
    config_dir: Path = field(repr=False)
    subtitle: SubtitleStyle | None = None
    pipeline: Pipeline | None = None
    # Per-device map of canonical filename → source filename in raw/.
    # Used by `frame` to translate capture-tool naming (XCUITest writes
    # `01_HomeScreen.png`) into the consumer-facing canonical naming
    # (captions.json keys, e.g. `02_HomeScreen.png` if a hero shot was
    # numbered ahead of it). Defaults to identity if absent.
    input_mapping: dict[str, dict[str, str]] | None = None
    # Declared manual-gesture inputs (Live Activity stack, Home Screen widget,
    # Control Center) that the `stage` pipeline step copies from a tracked
    # source dir into raw/ before framing. None = no manual_inputs declared
    # (stage is a no-op).
    manual_inputs: ManualInputs | None = None

    def source_filename(self, device_key: str, canonical: str) -> str:
        """Return the raw/ filename for a canonical name (identity if no mapping)."""
        if self.input_mapping is None:
            return canonical
        device_map = self.input_mapping.get(device_key)
        if not device_map:
            return canonical
        return device_map.get(canonical, canonical)

    def raw_dir(self, device_key: str, locale: str) -> Path:
        return self._device_subdir(device_key, locale, "raw")

    def framed_dir(self, device_key: str, locale: str) -> Path:
        return self._device_subdir(device_key, locale, "framed")

    def manual_source_dir(self, device_key: str, locale: str) -> Path | None:
        """Resolve the manual_inputs source dir for (device, locale), or None
        if no manual_inputs is declared for this device."""
        if self.manual_inputs is None:
            return None
        device_block = self.manual_inputs.for_device(device_key)
        if device_block is None:
            return None
        return self.resolve(device_block.source.format(locale=locale))

    def _device_subdir(self, device_key: str, locale: str, sub: str) -> Path:
        template = self.input_paths.get(device_key)
        if template is None:
            raise ConfigError(f"No input path configured for device '{device_key}'")
        return self.resolve(template.format(locale=locale)) / sub

    def device_keys(self) -> list[str]:
        return [k for k in self.input_paths if k in devices.DEVICES]

    def caption_size(self, device_key: str) -> int:
        if device_key == "iphone":
            return self.caption.size_iphone
        if device_key == "ipad":
            return self.caption.size_ipad
        raise ConfigError(f"No caption size defined for device '{device_key}'")

    def subtitle_size(self, device_key: str) -> int:
        if self.subtitle is None:
            raise ConfigError("Config has no subtitle block")
        if device_key == "iphone":
            return self.subtitle.size_iphone
        if device_key == "ipad":
            return self.subtitle.size_ipad
        raise ConfigError(f"No subtitle size defined for device '{device_key}'")

    def resolve(self, path: str) -> Path:
        """Resolve a config-relative path to an absolute Path."""
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.config_dir / p).resolve()


def load(config_path: Path) -> Config:
    config_path = Path(config_path).resolve()
    if not config_path.is_file():
        raise ConfigError(f"Config not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e

    return _build(raw, config_dir=config_path.parent)


def _build(raw: dict, config_dir: Path) -> Config:
    _require(raw, "version")
    if raw["version"] == 1:
        raise ConfigError(
            "Config schema v1 is no longer supported. shotsmith uses schema v2, "
            "which reads framed PNGs from <input>/<locale>/framed/ instead of "
            "<input>/<locale>/. To migrate: bump \"version\" to 2 in your config, "
            "and reorganize input paths so framed PNGs live in a framed/ subdir "
            "with raw captures in a sibling raw/ subdir. See README.md \"Directory "
            "contract\" section for details."
        )
    if raw["version"] != SUPPORTED_VERSION:
        raise ConfigError(
            f"Unsupported config version {raw['version']}; "
            f"this shotsmith supports version {SUPPORTED_VERSION}"
        )

    _require(raw, "input")
    _require(raw, "output")
    _require(raw, "background")
    _require(raw, "caption")
    _require(raw, "captions_file")
    _require(raw, "locales")

    bg_raw = raw["background"]
    _require(bg_raw, "type", parent="background")
    if bg_raw["type"] != "linear-gradient":
        raise ConfigError(
            f"Unsupported background type '{bg_raw['type']}'; "
            f"only 'linear-gradient' is supported"
        )
    _require(bg_raw, "stops", parent="background")
    _require(bg_raw, "angle", parent="background")
    if len(bg_raw["stops"]) < 2:
        raise ConfigError("background.stops must contain at least 2 colors")

    cap_raw = raw["caption"]
    for key in ("font", "color", "size_iphone", "size_ipad", "position",
                "padding_pct", "max_lines", "line_height"):
        _require(cap_raw, key, parent="caption")
    if cap_raw["position"] not in ("footer", "header"):
        raise ConfigError(
            f"caption.position must be 'footer' or 'header', got '{cap_raw['position']}'"
        )

    locales = raw["locales"]
    if not isinstance(locales, list) or not locales:
        raise ConfigError("locales must be a non-empty list")

    dither_raw = bg_raw.get("dither", 0)
    if not isinstance(dither_raw, (int, float)) or dither_raw < 0 or dither_raw > 255:
        raise ConfigError(
            f"background.dither must be an integer in 0..255, got {dither_raw!r}"
        )

    input_mapping: dict[str, dict[str, str]] | None = None
    if "input_mapping" in raw:
        mapping_raw = raw["input_mapping"]
        if not isinstance(mapping_raw, dict):
            raise ConfigError("input_mapping must be an object keyed by device")
        input_mapping = {}
        for device_key, device_map in mapping_raw.items():
            if not isinstance(device_map, dict):
                raise ConfigError(
                    f"input_mapping.{device_key} must be an object "
                    f"of canonical → source filenames"
                )
            for canonical, source in device_map.items():
                if not isinstance(source, str):
                    raise ConfigError(
                        f"input_mapping.{device_key}.{canonical} must be a "
                        f"string filename, got {type(source).__name__}"
                    )
            input_mapping[device_key] = dict(device_map)

    manual_inputs: ManualInputs | None = None
    if "manual_inputs" in raw:
        mi_raw = raw["manual_inputs"]
        if not isinstance(mi_raw, dict):
            raise ConfigError("manual_inputs must be an object keyed by device")
        by_device: dict[str, ManualInputDevice] = {}
        for device_key, dev_raw in mi_raw.items():
            if not isinstance(dev_raw, dict):
                raise ConfigError(
                    f"manual_inputs.{device_key} must be an object with "
                    f"'source' and 'files' fields"
                )
            for k in ("source", "files"):
                if k not in dev_raw:
                    raise ConfigError(
                        f"manual_inputs.{device_key} missing required field '{k}'"
                    )
            if not isinstance(dev_raw["source"], str):
                raise ConfigError(
                    f"manual_inputs.{device_key}.source must be a string path template"
                )
            files_raw = dev_raw["files"]
            if not isinstance(files_raw, list) or not files_raw:
                raise ConfigError(
                    f"manual_inputs.{device_key}.files must be a non-empty list of filenames"
                )
            for fname in files_raw:
                if not isinstance(fname, str):
                    raise ConfigError(
                        f"manual_inputs.{device_key}.files entries must be strings, "
                        f"got {type(fname).__name__}"
                    )
            by_device[device_key] = ManualInputDevice(
                source=dev_raw["source"],
                files=list(files_raw),
            )
        manual_inputs = ManualInputs(by_device=by_device)

    pipeline: Pipeline | None = None
    if "pipeline" in raw:
        pl_raw = raw["pipeline"]
        if not isinstance(pl_raw, dict):
            raise ConfigError("pipeline must be an object")
        pipeline = Pipeline(
            capture_hook=pl_raw.get("capture_hook") or None,
            frames_cli=pl_raw.get("frames_cli", "frames"),
            frames_args=list(pl_raw.get("frames_args", [])),
            verify_strict=bool(pl_raw.get("verify_strict", True)),
        )

    subtitle: SubtitleStyle | None = None
    if "subtitle" in raw:
        sub_raw = raw["subtitle"]
        for key in ("font", "color", "size_iphone", "size_ipad",
                    "max_lines", "line_height", "spacing_pct"):
            _require(sub_raw, key, parent="subtitle")
        subtitle = SubtitleStyle(
            font=sub_raw["font"],
            color=sub_raw["color"],
            size_iphone=int(sub_raw["size_iphone"]),
            size_ipad=int(sub_raw["size_ipad"]),
            max_lines=int(sub_raw["max_lines"]),
            line_height=float(sub_raw["line_height"]),
            spacing_pct=float(sub_raw["spacing_pct"]),
        )

    return Config(
        version=raw["version"],
        input_paths=dict(raw["input"]),
        output_paths=dict(raw["output"]),
        background=Background(
            type=bg_raw["type"],
            stops=list(bg_raw["stops"]),
            angle=int(bg_raw["angle"]),
            dither=int(dither_raw),
        ),
        caption=CaptionStyle(
            font=cap_raw["font"],
            color=cap_raw["color"],
            size_iphone=int(cap_raw["size_iphone"]),
            size_ipad=int(cap_raw["size_ipad"]),
            position=cap_raw["position"],
            padding_pct=float(cap_raw["padding_pct"]),
            max_lines=int(cap_raw["max_lines"]),
            line_height=float(cap_raw["line_height"]),
            padding_pct_iphone=(
                float(cap_raw["padding_pct_iphone"])
                if "padding_pct_iphone" in cap_raw else None
            ),
            padding_pct_ipad=(
                float(cap_raw["padding_pct_ipad"])
                if "padding_pct_ipad" in cap_raw else None
            ),
        ),
        captions_file=raw["captions_file"],
        locales=list(locales),
        config_dir=config_dir,
        subtitle=subtitle,
        pipeline=pipeline,
        input_mapping=input_mapping,
        manual_inputs=manual_inputs,
    )


def _require(d: dict, key: str, parent: str | None = None) -> None:
    if key not in d:
        loc = f"{parent}.{key}" if parent else key
        raise ConfigError(f"Missing required config field: {loc}")
