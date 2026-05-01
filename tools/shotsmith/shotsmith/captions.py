"""Captions file loading + per-locale + per-device lookup.

The captions file is a JSON dict keyed by input PNG filename. Each entry is a
dict keyed by short language code (e.g. 'en', 'es', 'es-MX'). The value per
locale can be either:

- A **string** — caption only, no subtitle, same for every device.
- A **dict** — `{"caption": "...", "subtitle": "...",
  "caption_iphone": "...", "subtitle_ipad": "..."}`.

  Per-device overrides:
  - `caption_<device>` overrides `caption` when rendering for that device.
  - `subtitle_<device>` overrides `subtitle` when rendering for that device.

  Lookup order for a given device X: try `caption_X`, fall back to `caption`.
  Independent for subtitle.

  Common use cases:
  - iPhone hero shot has a forced line break; iPad runs single-line on the
    wider canvas: `{"caption": "Real time symptom tracking",
    "caption_iphone": "Real time\\nsymptom tracking"}`.
  - Different copy entirely per device: pass both `caption_iphone` and
    `caption_ipad`; omit `caption` entirely if every device has an override.

Locales used by the iteration loop are full BCP-47 codes ('en-US', 'es-MX').
We try the full locale first, then fall back to the language portion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class CaptionsError(ValueError):
    pass


@dataclass(frozen=True)
class CaptionEntry:
    caption: str
    subtitle: str | None = None


class Captions:
    def __init__(self, data: dict[str, dict[str, str | dict]]):
        self._data = data

    @classmethod
    def load(cls, path: Path) -> "Captions":
        path = Path(path)
        if not path.is_file():
            raise CaptionsError(f"Captions file not found: {path}")
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise CaptionsError(f"Invalid JSON in {path}: {e}") from e
        if not isinstance(data, dict):
            raise CaptionsError(f"Captions root must be an object, got {type(data).__name__}")
        return cls(data)

    def lookup(
        self,
        filename: str,
        locale: str,
        device_key: str | None = None,
    ) -> CaptionEntry | None:
        """Look up a caption + optional subtitle for image + locale + device.

        Locale resolution: full locale first ('es-MX'), then language ('es'),
        then None.

        Device resolution (only when value is a dict): `caption_<device>`
        overrides `caption`; `subtitle_<device>` overrides `subtitle`.
        Independent — a screen can override only the caption for one device,
        or only the subtitle for another, etc.
        """
        entry = self._data.get(filename)
        if not entry:
            return None
        raw = entry.get(locale)
        if raw is None:
            lang = locale.split("-", 1)[0]
            raw = entry.get(lang)
        if raw is None:
            return None
        if isinstance(raw, str):
            return CaptionEntry(caption=raw)
        if isinstance(raw, dict):
            cap = self._resolve(raw, "caption", device_key) or ""
            sub = self._resolve(raw, "subtitle", device_key) or None
            return CaptionEntry(caption=cap, subtitle=sub)
        raise CaptionsError(
            f"{filename}/{locale}: caption value must be a string or "
            f"{{caption, subtitle}} dict, got {type(raw).__name__}"
        )

    @staticmethod
    def _resolve(raw: dict, base_key: str, device_key: str | None) -> str | None:
        """Look up `<base_key>_<device_key>` first, fall back to `<base_key>`."""
        if device_key:
            override = raw.get(f"{base_key}_{device_key}")
            if override is not None:
                return override
        return raw.get(base_key)

    def filenames(self) -> list[str]:
        return list(self._data.keys())
