"""Font discovery.

Two ways to specify a font in the config:

1. **Direct path** — anything containing '/' or ending in .ttf/.otf/.ttc/.ttx.
   Used verbatim.
2. **Family + style name** — e.g. "New York Small Bold", "Helvetica Neue Bold".
   We search standard macOS font directories for a matching file using two
   naming conventions:

   a. **Apple optical-size + weight** — `<Family><OpticalSize>-<Weight>.otf`
      e.g. "New York Small Bold" → NewYorkSmall-Bold.otf
   b. **Family-Style** — `<Family>-<Style>.{otf,ttf}` or `<FamilyStyle>.{otf,ttf}`
      e.g. "Helvetica Neue Bold" → HelveticaNeue-Bold.ttf

If discovery fails, FontError lists the directories searched and the patterns
tried so the user can either move/install the font or pass an explicit path.
"""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont


FONT_DIRS: list[Path] = [
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
    Path.home() / "Library" / "Fonts",
]

FONT_EXTENSIONS = (".otf", ".ttf", ".ttc")


WEIGHT_WORDS = {
    "Thin", "ExtraLight", "Light", "Regular", "Medium",
    "Semibold", "SemiBold", "Bold", "Heavy", "Black",
    "Italic", "BoldItalic", "MediumItalic", "RegularItalic",
}

OPTICAL_WORDS = {"Small", "Medium", "Large", "ExtraLarge"}


class FontError(ValueError):
    pass


def load(name_or_path: str, size: int) -> ImageFont.FreeTypeFont:
    path = resolve(name_or_path)
    try:
        return ImageFont.truetype(str(path), size=size)
    except OSError as e:
        raise FontError(f"Failed to load font {path}: {e}") from e


def resolve(name_or_path: str) -> Path:
    if _looks_like_path(name_or_path):
        p = Path(name_or_path).expanduser()
        if not p.is_file():
            raise FontError(f"Font path not found: {p}")
        return p

    # Most-specific candidate wins, regardless of which directory it lives in.
    # Without this ordering, a variable-font master in /System/Library/Fonts
    # (e.g. NewYork.ttf, which defaults to Regular weight) shadows the
    # dedicated optical+weight cut in /Library/Fonts (NewYorkSmall-Bold.otf).
    candidates = _candidate_filenames(name_or_path)
    dirs = [d for d in FONT_DIRS if d.is_dir()]
    for candidate in candidates:
        for ext in FONT_EXTENSIONS:
            for directory in dirs:
                hit = directory / f"{candidate}{ext}"
                if hit.is_file():
                    return hit

    raise FontError(
        f"Could not find font '{name_or_path}'. Searched:\n"
        + "\n".join(f"  - {d}" for d in FONT_DIRS)
        + "\n\nTried filename patterns:\n"
        + "\n".join(f"  - {c}.{{otf,ttf,ttc}}" for c in candidates)
        + "\n\nFix: either install the font, or pass an absolute path "
        "(e.g. \"/Library/Fonts/NewYorkSmall-Bold.otf\") in config.caption.font."
    )


def _looks_like_path(s: str) -> bool:
    if "/" in s:
        return True
    return s.lower().endswith(FONT_EXTENSIONS)


def _candidate_filenames(name: str) -> list[str]:
    """Generate candidate font filenames from a 'Family Style' name.

    For 'New York Small Bold' generates (in order of preference):
      - NewYorkSmall-Bold        (Apple optical-size + weight pattern)
      - NewYork-SmallBold
      - NewYorkSmallBold
      - NewYork-Small-Bold
    """
    words = name.split()
    if not words:
        return []

    # Identify weight + optical-size words from the tail
    weight_parts: list[str] = []
    optical_parts: list[str] = []
    family_parts: list[str] = []

    for word in words:
        if word in WEIGHT_WORDS:
            weight_parts.append(word)
        elif word in OPTICAL_WORDS:
            optical_parts.append(word)
        else:
            family_parts.append(word)

    family = "".join(family_parts)
    optical = "".join(optical_parts)
    weight = "".join(weight_parts)

    candidates: list[str] = []
    if family and optical and weight:
        candidates.append(f"{family}{optical}-{weight}")
        candidates.append(f"{family}-{optical}{weight}")
        candidates.append(f"{family}{optical}{weight}")
    if family and weight:
        candidates.append(f"{family}-{weight}")
        candidates.append(f"{family}{weight}")
    if family:
        candidates.append(family)
    # Fallback: literal name with spaces stripped
    no_space = "".join(words)
    if no_space not in candidates:
        candidates.append(no_space)
    return candidates
