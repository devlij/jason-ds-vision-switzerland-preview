#!/usr/bin/env python3
"""Bake the label-bar finish from a pure pre-text photograph.

The photograph stays pure: no tint, scrim, shadow, or type over the art.
A uniform 190px #0e0e12 bar and a 2px hairline are added under the photo.

Masters
  16:9  1920×1270   photo 1920×1080
  4:5    864×1270   photo 864×1080
  9:16  1080×2110   photo 1080×1920

On-image type, all of it inside the bar:
  caption, "Scenario: …", disclosure,
  "Jason D’s Vision" (curly apostrophe U+2019),
  "Jason A. Devlin" in Allura.

This Switzerland bake does not embed EU AI Act Art. 50 chunks.
Image Assistant re-stamps new masters after they land.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SANS = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
SANS_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
ALLURA = Path(__file__).resolve().parent / "fonts" / "Allura-Regular.ttf"

BRAND = "Jason D\u2019s Vision"
SIGNATURE_NAME = "Jason A. Devlin"
DISCLOSURE = "AI-generated artistic interpretation \u00b7 Not a photograph."

BAR_H = 190
HAIRLINE = 2
BAR_BG = (0x0E, 0x0E, 0x12)
HAIR = (0xE4, 0xE4, 0xEA)
INK = (255, 255, 255)
INK_SCENARIO = (214, 214, 222)
INK_DISCLOSURE = (176, 176, 186)

PHOTO = {"16x9": (1920, 1080), "4x5": (864, 1080), "9x16": (1080, 1920)}
CANVAS = {"16x9": (1920, 1270), "4x5": (864, 1270), "9x16": (1080, 2110)}
PNG_SIG = b"\x89PNG\r\n\x1a\n"
ART50_KEYS = ("Title", "Description", "Copyright", "Software", "Comment")


def pretext_paths(folder: str, entry_id: str) -> dict[str, Path]:
    directory = ROOT / "library" / "pretext" / "Switzerland" / folder
    stem = entry_id.lower()
    return {
        "16x9": directory / f"{stem}-16x9.png",
        "4x5": directory / f"{stem}-4x5.png",
        "9x16": directory / f"{stem}-9x16.png",
    }


def master_paths(folder: str, entry_id: str) -> dict[str, Path]:
    directory = ROOT / "library" / "world" / "Switzerland" / folder
    stem = entry_id.lower()
    return {
        "16x9": directory / f"{stem}-16x9.png",
        "4x5": directory / f"{stem}-4x5.png",
        "9x16": directory / f"{stem}-9x16.png",
    }


def fit(im: Image.Image, tw: int, th: int) -> Image.Image:
    """Center-crop to the target aspect, then Lanczos to the exact photo size."""
    im = im.convert("RGB")
    w, h = im.size
    target = tw / th
    current = w / h
    if abs(current - target) > 1e-6:
        if current > target:
            new_w = int(round(h * target))
            left = (w - new_w) // 2
            im = im.crop((left, 0, left + new_w, h))
        else:
            new_h = int(round(w / target))
            top = max(0, (h - new_h) // 2)
            im = im.crop((0, top, w, top + new_h))
    if im.size != (tw, th):
        im = im.resize((tw, th), Image.Resampling.LANCZOS)
    return im


def _bbox(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int, int, int]:
    return font.getbbox(text, anchor="lt")


def _measure(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    left, top, right, bottom = _bbox(font, text)
    return right - left, bottom - top


def _fonts(scale: float) -> dict[str, ImageFont.FreeTypeFont]:
    def px(size: float, floor: int) -> int:
        return max(floor, int(round(size * scale)))

    return {
        "cap": ImageFont.truetype(str(SANS_BOLD), px(28, 15)),
        "sc": ImageFont.truetype(str(SANS), px(18, 12)),
        "disc": ImageFont.truetype(str(SANS), px(16, 11)),
        "brand": ImageFont.truetype(str(SANS), px(20, 13)),
        "name": ImageFont.truetype(str(ALLURA), px(46, 28)),
    }


def _stack_size(lines: list[tuple[str, ImageFont.FreeTypeFont]], gap: int) -> tuple[int, int]:
    width = 0
    height = 0
    for index, (text, font) in enumerate(lines):
        w, h = _measure(font, text)
        width = max(width, w)
        height += h
        if index:
            height += gap
    return width, height


def layout_fonts(width: int, caption: str, scenario: str) -> tuple[dict[str, ImageFont.FreeTypeFont], int]:
    if not ALLURA.exists():
        raise SystemExit(f"Allura font missing: {ALLURA}")
    scale = 1.0 if width >= 1600 else (0.9 if width >= 1000 else 0.78)
    for _ in range(18):
        fonts = _fonts(scale)
        gap = max(4, int(round(6 * scale)))
        margin = max(20, int(round(width * 0.028)))
        col_gap = max(16, int(round(width * 0.018)))
        left_w, left_h = _stack_size(
            [(caption, fonts["cap"]), (scenario, fonts["sc"]), (DISCLOSURE, fonts["disc"])],
            gap,
        )
        right_w, right_h = _stack_size(
            [(BRAND, fonts["brand"]), (SIGNATURE_NAME, fonts["name"])],
            gap,
        )
        content_h = BAR_H - HAIRLINE
        if (
            margin * 2 + col_gap + left_w + right_w <= width
            and left_h <= content_h - 16
            and right_h <= content_h - 12
        ):
            return fonts, gap
        scale *= 0.94
    raise SystemExit(f"label text does not fit a {width}px bar")


def draw_label_bar(
    photo: Image.Image,
    caption: str,
    scenario_label: str,
    middle_line: str | None = None,
) -> Image.Image:
    photo = photo.convert("RGB")
    pw, ph = photo.size
    canvas = Image.new("RGB", (pw, ph + BAR_H), BAR_BG)
    canvas.paste(photo, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, ph, pw - 1, ph + HAIRLINE - 1), fill=HAIR)

    # Daylight variants pass middle_line so the bar does not invent a
    # "Scenario:" timestamp or a weather line. Masters keep the prefix.
    scenario = middle_line if middle_line is not None else f"Scenario: {scenario_label}"
    fonts, gap = layout_fonts(pw, caption, scenario)
    margin = max(20, int(round(pw * 0.028)))
    col_gap = max(16, int(round(pw * 0.018)))
    left = [
        (caption, fonts["cap"], INK),
        (scenario, fonts["sc"], INK_SCENARIO),
        (DISCLOSURE, fonts["disc"], INK_DISCLOSURE),
    ]
    right = [
        (BRAND, fonts["brand"], INK),
        (SIGNATURE_NAME, fonts["name"], INK),
    ]

    def stack_height(rows: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int]]]) -> int:
        total = 0
        for index, (text, font, _ink) in enumerate(rows):
            total += _measure(font, text)[1]
            if index:
                total += gap
        return total

    def stack_width(rows: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int]]]) -> int:
        return max(_measure(font, text)[0] for text, font, _ink in rows)

    left_w = stack_width(left)
    right_w = stack_width(right)
    if margin + left_w + col_gap + right_w + margin > pw:
        raise SystemExit(f"label overflow on {pw}px: caption {caption!r}")

    content_top = ph + HAIRLINE
    content_h = BAR_H - HAIRLINE

    def draw_stack(rows: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int]]], x_align: str) -> None:
        block_h = stack_height(rows)
        y = content_top + max(0, (content_h - block_h) // 2)
        block_w = stack_width(rows)
        for text, font, ink in rows:
            text_w, text_h = _measure(font, text)
            left_edge, top_edge, _right, _bottom = _bbox(font, text)
            x = margin if x_align == "left" else pw - margin - block_w
            if x_align == "right":
                x = x + (block_w - text_w)
            draw.text((x - left_edge, y - top_edge), text, font=font, fill=ink, anchor="lt")
            y += text_h + gap

    draw_stack(left, "left")
    draw_stack(right, "right")
    return canvas


def _place(src: Path, dest: Path) -> None:
    if not src.exists():
        raise SystemExit(f"missing pre-text: {src}")
    im = Image.open(src).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="PNG", compress_level=9)


def _photo_for(fmt: str, paths: dict[str, Path]) -> Image.Image:
    tw, th = PHOTO[fmt]
    specific = paths.get(fmt)
    if specific is not None and specific.exists():
        return fit(Image.open(specific), tw, th)
    primary = paths["16x9"]
    if not primary.exists():
        raise SystemExit(f"missing primary pre-text: {primary}")
    return fit(Image.open(primary), tw, th)


def _text_keys(path: Path) -> set[str]:
    data = path.read_bytes()
    if data[:8] != PNG_SIG:
        raise SystemExit(f"not a png: {path}")
    keys: set[str] = set()
    i = 8
    while i + 8 <= len(data):
        length = struct.unpack(">I", data[i : i + 4])[0]
        ctype = data[i + 4 : i + 8]
        chunk = data[i + 8 : i + 8 + length]
        if ctype in (b"tEXt", b"iTXt", b"zTXt"):
            keys.add(chunk.split(b"\x00", 1)[0].decode("latin-1", "replace"))
        i += 12 + length
        if ctype == b"IEND":
            break
    return keys


def save_master(im: Image.Image, path: Path, photo: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="PNG", compress_level=9)
    stamped = _text_keys(path) & set(ART50_KEYS)
    if stamped:
        raise SystemExit(f"Art. 50 chunks were written and must not be: {path} {sorted(stamped)}")
    with Image.open(path) as saved:
        saved.load()
        if saved.size != im.size:
            raise SystemExit(f"bad size {path} {saved.size}")
        top = saved.crop((0, 0, photo.width, photo.height)).convert("RGB")
        if ImageChops.difference(top, photo).getbbox() is not None:
            raise SystemExit(f"photo pixels were altered: {path}")
        bar_px = saved.getpixel((2, saved.height - 1))
        if bar_px[:3] != BAR_BG:
            raise SystemExit(f"label bar background {path} {bar_px}")
        hair_px = saved.getpixel((2, photo.height))
        if hair_px[:3] != HAIR:
            raise SystemExit(f"hairline missing {path} {hair_px}")
        # A pixel just under the hairline and a pixel in the photo's last row
        # must not share the bar color by accident of a full-frame scrim.
        if saved.getpixel((2, 2))[:3] == BAR_BG and saved.getpixel((photo.width // 2, 2))[:3] == BAR_BG:
            raise SystemExit(f"photo looks covered by the bar color: {path}")


def composite_one(
    entry_id: str,
    folder: str,
    caption: str,
    scenario_label: str,
    source: Path,
    source_4x5: Path,
    source_9x16: Path,
) -> dict[str, Path]:
    if "Scenario:" in scenario_label:
        raise SystemExit(f"{entry_id} scenario_label should not include the Scenario prefix")
    if "\u2019" not in BRAND:
        raise SystemExit("brand apostrophe is not U+2019")
    paths = pretext_paths(folder, entry_id)
    _place(source, paths["16x9"])
    _place(source_4x5, paths["4x5"])
    _place(source_9x16, paths["9x16"])
    photos = {fmt: _photo_for(fmt, paths) for fmt in ("16x9", "4x5", "9x16")}
    outs = master_paths(folder, entry_id)
    for fmt, photo in photos.items():
        if photo.size != PHOTO[fmt]:
            raise SystemExit(f"{entry_id} {fmt} photo {photo.size}")
        finished = draw_label_bar(photo, caption, scenario_label)
        if finished.size != CANVAS[fmt]:
            raise SystemExit(f"{entry_id} {fmt} canvas {finished.size}")
        save_master(finished, outs[fmt], photo)
    return outs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Bake Switzerland label-bar masters from pure photos.")
    parser.add_argument("entry_id")
    parser.add_argument("--folder", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--scenario", required=True, help="Scenario label without the Scenario: prefix")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-4x5", type=Path, required=True)
    parser.add_argument("--source-9x16", type=Path, required=True)
    args = parser.parse_args(argv)
    outs = composite_one(
        args.entry_id,
        args.folder,
        args.caption,
        args.scenario,
        args.source,
        args.source_4x5,
        args.source_9x16,
    )
    for fmt, path in outs.items():
        with Image.open(path) as im:
            print(f"composited {args.entry_id} {fmt} {path.relative_to(ROOT)} {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
