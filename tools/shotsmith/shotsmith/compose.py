"""Core composition: gradient background + framed PNG + caption.

Layout model (for `position: "footer"`, the App Store convention):

    +---------------------------------+ y=0
    |                                 |
    |   [framed device PNG, fitted    |
    |    into image_area, centered]   |
    |                                 |
    +---------------------------------+ y=image_area_height
    |                                 |
    |   <Caption text, wrapped,       |
    |    centered, max_lines lines>   |
    |                                 |
    +---------------------------------+ y=canvas_height

For `position: "header"` the layout flips. The caption_area_height is sized
to hold `max_lines` lines at the configured font size + line_height, plus
padding above and below.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from . import devices, fonts
from .captions import Captions
from .config import Config


@dataclass
class ComposeResult:
    locale: str
    device: str
    written: list[Path]
    skipped: list[tuple[str, str]]  # (filename, reason)


def compose_locale(
    config: Config,
    locale: str,
    device_key: str,
    captions: Captions,
    dry_run: bool = False,
) -> ComposeResult:
    """Compose all screenshots for one locale + device combination."""
    device = devices.get(device_key)

    output_template = config.output_paths.get(device_key)
    if not output_template:
        raise ValueError(f"No output path configured for device '{device_key}'")

    # v2 directory contract: framed PNGs live in <input>/<locale>/framed/.
    input_dir = config.framed_dir(device_key, locale)
    output_dir = config.resolve(output_template.format(locale=locale))

    if not input_dir.is_dir():
        raise FileNotFoundError(
            f"Input directory not found for {device_key}/{locale}: {input_dir}"
        )

    written: list[Path] = []
    skipped: list[tuple[str, str]] = []
    caption_size = config.caption_size(device_key)
    caption_font = fonts.load(config.caption.font, caption_size)

    subtitle_font = None
    subtitle_size = 0
    if config.subtitle is not None:
        subtitle_size = config.subtitle_size(device_key)
        subtitle_font = fonts.load(config.subtitle.font, subtitle_size)

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    for filename in sorted(captions.filenames()):
        src = input_dir / filename
        if not src.is_file():
            skipped.append((filename, f"input missing: {src}"))
            continue

        entry = captions.lookup(filename, locale, device_key=device_key)
        if entry is None:
            skipped.append((filename, f"no caption for locale '{locale}'"))
            continue

        out_path = output_dir / filename
        if dry_run:
            written.append(out_path)
            continue

        composed = _compose_one(
            src=src,
            canvas_size=(device.width, device.height),
            background=config.background,
            caption_text=entry.caption,
            caption_font=caption_font,
            caption_size=caption_size,
            caption_color=config.caption.color,
            caption_position=config.caption.position,
            padding_pct=config.caption.padding_for(device_key),
            max_lines=config.caption.max_lines,
            line_height=config.caption.line_height,
            subtitle_text=entry.subtitle,
            subtitle_font=subtitle_font,
            subtitle_size=subtitle_size,
            subtitle_style=config.subtitle,
        )
        composed.save(out_path, format="PNG")
        written.append(out_path)

    return ComposeResult(
        locale=locale, device=device_key, written=written, skipped=skipped
    )


def _compose_one(
    src: Path,
    canvas_size: tuple[int, int],
    background,
    caption_text: str,
    caption_font: ImageFont.FreeTypeFont,
    caption_size: int,
    caption_color: str,
    caption_position: str,
    padding_pct: float,
    max_lines: int,
    line_height: float,
    subtitle_text: str | None = None,
    subtitle_font: ImageFont.FreeTypeFont | None = None,
    subtitle_size: int = 0,
    subtitle_style=None,  # SubtitleStyle from config
) -> Image.Image:
    canvas_w, canvas_h = canvas_size
    padding_px = int(canvas_h * padding_pct / 100)

    caption_line_px = int(caption_size * line_height)
    caption_block_h = caption_line_px * max_lines

    # Subtitle is optional; only contributes height when present AND text exists.
    has_subtitle = (
        subtitle_text and subtitle_font is not None and subtitle_style is not None
    )
    subtitle_line_px = 0
    subtitle_block_h = 0
    spacing_px = 0
    if has_subtitle:
        subtitle_line_px = int(subtitle_size * subtitle_style.line_height)
        subtitle_block_h = subtitle_line_px * subtitle_style.max_lines
        spacing_px = int(canvas_h * subtitle_style.spacing_pct / 100)

    caption_area_h = (
        caption_block_h + spacing_px + subtitle_block_h + (2 * padding_px)
    )
    image_area_h = canvas_h - caption_area_h

    canvas = _draw_gradient(canvas_w, canvas_h, background.stops, background.angle)
    if getattr(background, "dither", 0) > 0:
        canvas = _add_dither(canvas, background.dither)

    src_img = Image.open(src).convert("RGBA")
    fitted = _fit_into(src_img, max_w=canvas_w, max_h=image_area_h)

    if caption_position == "footer":
        image_y = (image_area_h - fitted.height) // 2
        caption_area_y = image_area_h
    elif caption_position == "header":
        image_y = caption_area_h + (image_area_h - fitted.height) // 2
        caption_area_y = 0
    else:
        raise ValueError(f"Unsupported caption position '{caption_position}'")

    image_x = (canvas_w - fitted.width) // 2
    canvas.paste(fitted, (image_x, image_y), fitted)

    _draw_caption_block(
        canvas=canvas,
        caption_text=caption_text,
        caption_font=caption_font,
        caption_color=caption_color,
        caption_max_lines=max_lines,
        caption_line_px=caption_line_px,
        subtitle_text=subtitle_text if has_subtitle else None,
        subtitle_font=subtitle_font if has_subtitle else None,
        subtitle_color=subtitle_style.color if has_subtitle else None,
        subtitle_max_lines=subtitle_style.max_lines if has_subtitle else 0,
        subtitle_line_px=subtitle_line_px,
        spacing_px=spacing_px,
        area=(0, caption_area_y, canvas_w, caption_area_y + caption_area_h),
        side_padding_px=padding_px,
    )

    return canvas


def _fit_into(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    src_w, src_h = img.size
    scale = min(max_w / src_w, max_h / src_h, 1.0)
    if scale >= 1.0:
        return img
    new_size = (int(src_w * scale), int(src_h * scale))
    return img.resize(new_size, resample=Image.LANCZOS)


def _draw_gradient(width: int, height: int, stops: list[str], angle: int) -> Image.Image:
    """Draw a linear gradient.

    Currently only `angle` 0 (left→right) and 180 (top→bottom) are supported.
    Other angles raise — keeps the implementation honest until we need them.
    """
    if angle not in (0, 180):
        raise ValueError(
            f"Only angle=0 (left-to-right) and angle=180 (top-to-bottom) "
            f"are supported, got {angle}"
        )
    if len(stops) != 2:
        raise ValueError(
            f"Multi-stop gradients are not yet implemented; expected 2 stops, "
            f"got {len(stops)}"
        )
    start = _hex_to_rgb(stops[0])
    end = _hex_to_rgb(stops[1])
    canvas = Image.new("RGB", (width, height))
    pixels = canvas.load()

    if angle == 180:
        for y in range(height):
            t = y / max(height - 1, 1)
            color = _lerp(start, end, t)
            for x in range(width):
                pixels[x, y] = color
    else:  # angle == 0
        for x in range(width):
            t = x / max(width - 1, 1)
            color = _lerp(start, end, t)
            for y in range(height):
                pixels[x, y] = color

    return canvas.convert("RGBA")


def _draw_caption_block(
    canvas: Image.Image,
    caption_text: str,
    caption_font: ImageFont.FreeTypeFont,
    caption_color: str,
    caption_max_lines: int,
    caption_line_px: int,
    subtitle_text: str | None,
    subtitle_font: ImageFont.FreeTypeFont | None,
    subtitle_color: str | None,
    subtitle_max_lines: int,
    subtitle_line_px: int,
    spacing_px: int,
    area: tuple[int, int, int, int],
    side_padding_px: int,
) -> None:
    """Draw a vertically-centered text block: caption on top, optional subtitle
    below. Each row is independently wrapped + truncated to its own max_lines.

    Total block height = caption_block + spacing + subtitle_block (if subtitle).
    The whole block is centered within `area`.
    """
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = area
    available_w = (x1 - x0) - 2 * side_padding_px

    caption_lines = _wrap(
        caption_text, caption_font, max_w=available_w,
        max_lines=caption_max_lines, draw=draw,
    )
    caption_block_h = caption_line_px * len(caption_lines)

    subtitle_lines: list[str] = []
    subtitle_block_h = 0
    if subtitle_text and subtitle_font is not None:
        subtitle_lines = _wrap(
            subtitle_text, subtitle_font, max_w=available_w,
            max_lines=subtitle_max_lines, draw=draw,
        )
        subtitle_block_h = subtitle_line_px * len(subtitle_lines)

    has_subtitle = bool(subtitle_lines)
    total_h = caption_block_h + (spacing_px + subtitle_block_h if has_subtitle else 0)
    block_y = y0 + ((y1 - y0) - total_h) // 2

    _draw_text_rows(
        draw=draw, lines=caption_lines, font=caption_font, color=caption_color,
        x_left=x0, x_right=x1, y_start=block_y, line_px=caption_line_px,
    )

    if has_subtitle:
        sub_y = block_y + caption_block_h + spacing_px
        _draw_text_rows(
            draw=draw, lines=subtitle_lines, font=subtitle_font, color=subtitle_color,
            x_left=x0, x_right=x1, y_start=sub_y, line_px=subtitle_line_px,
        )


def _draw_text_rows(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    color: str,
    x_left: int,
    x_right: int,
    y_start: int,
    line_px: int,
) -> None:
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = x_left + ((x_right - x_left) - line_w) // 2 - bbox[0]
        y = y_start + i * line_px - bbox[1]
        draw.text((x, y), line, fill=color, font=font)


def _wrap(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_w: int,
    max_lines: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    """Wrap text honoring explicit `\\n` breaks AND auto greedy-wrapping.

    Explicit `\\n` in the input forces a line break. Each forced segment is
    then greedy-wrapped to fit `max_w`, sharing the `max_lines` budget across
    all segments. If the total exceeds `max_lines`, the last visible line is
    truncated with an ellipsis.

    Empty segments (from `\\n\\n`) are ignored — to add vertical gap, use
    spacing between caption + subtitle blocks instead.
    """
    if not text:
        return [""]

    out: list[str] = []
    for segment in text.split("\n"):
        if len(out) >= max_lines:
            break
        segment = segment.strip()
        if not segment:
            continue
        remaining = max_lines - len(out)
        out.extend(_wrap_segment(segment, font, max_w, remaining, draw))

    if not out:
        return [""]

    if len(out) > max_lines:
        out = out[:max_lines]

    # If the very last line was truncated by the budget AND there's more text
    # we couldn't fit, append an ellipsis. We detect "more text was elided" by
    # re-wrapping the input with no max_lines limit and comparing total count.
    full = []
    for segment in text.split("\n"):
        segment = segment.strip()
        if segment:
            full.extend(_wrap_segment(segment, font, max_w, max_lines * 100, draw))
    if len(full) > len(out):
        last = out[-1]
        while last:
            candidate = last + "…"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if (bbox[2] - bbox[0]) <= max_w:
                out[-1] = candidate
                break
            last = last[:-1]
        else:
            out[-1] = "…"

    return out


def _wrap_segment(
    segment: str,
    font: ImageFont.FreeTypeFont,
    max_w: int,
    max_lines: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    """Greedy word-wrap one explicit segment (no `\\n` inside)."""
    words = segment.split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                return lines
    lines.append(current)
    return lines[:max_lines]


def _add_dither(img: Image.Image, sigma: int) -> Image.Image:
    """Overlay subtle Gaussian grain to disguise gradient banding.

    Pillow's `effect_noise` produces a single-channel Gaussian noise image
    centered on 128. We add it (with -128 offset, so it's signed +/- noise)
    to each RGB channel — sigma controls how much grain. Subtle range is
    4..12; higher values produce visible film grain.

    The noise canvas alpha channel is preserved unchanged.
    """
    if sigma <= 0:
        return img
    has_alpha = img.mode == "RGBA"
    if has_alpha:
        alpha = img.split()[-1]
        rgb = img.convert("RGB")
    else:
        rgb = img

    noise = Image.effect_noise(rgb.size, sigma).convert("RGB")
    grained = ImageChops.add(rgb, noise, scale=1, offset=-128)

    if has_alpha:
        grained = grained.convert("RGBA")
        grained.putalpha(alpha)
    return grained


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    if len(s) != 6:
        raise ValueError(f"Expected #RRGGBB hex color, got {hex_str!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def _lerp(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )
