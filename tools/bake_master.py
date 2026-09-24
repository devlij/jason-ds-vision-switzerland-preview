"""Bake exact caption, scenario, disclosure, and signature onto a master."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

SIGNATURE = "Jason D\u2019s Vision"
DISCLOSURE = "AI-generated artistic interpretation \u00b7 Not a photograph."

FONT_REGULAR = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
FONT_SEMIBOLD = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"


def _cover(im: Image.Image, width: int, height: int) -> Image.Image:
    src = im.convert("RGB")
    scale = max(width / src.width, height / src.height)
    resized = src.resize(
        (max(1, round(src.width * scale)), max(1, round(src.height * scale))),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _scrim(base: Image.Image) -> Image.Image:
    width, height = base.size
    mask = Image.new("L", (1, height), 0)
    pixels = mask.load()
    start = int(height * 0.58)
    span = max(1, height - start)
    for y in range(height):
        if y < start:
            pixels[0, y] = 0
            continue
        t = (y - start) / span
        t = t * t * (3 - 2 * t)
        pixels[0, y] = int(188 * t)
    mask = mask.resize((width, height))
    dark = Image.new("RGB", (width, height), (8, 4, 4))
    return Image.composite(dark, base, mask)


def _font(path: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, max(8, int(round(size))))


def bake(
    source: str,
    dest: str,
    width: int,
    height: int,
    caption: str,
    scenario_line: str,
) -> None:
    image = _scrim(_cover(Image.open(source), width, height))
    draw = ImageDraw.Draw(image)
    caption_font = _font(FONT_SEMIBOLD, width * 0.016)
    scenario_font = _font(FONT_REGULAR, width * 0.012)
    disclosure_font = _font(FONT_REGULAR, width * 0.010)
    signature_font = _font(FONT_SEMIBOLD, width * 0.018)

    margin_x = width * 0.032
    margin_b = height * 0.034
    gap = height * 0.008

    def measure(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
        box = draw.textbbox((0, 0), text, font=font)
        return box[2] - box[0], box[3] - box[1]

    _, disclosure_h = measure(DISCLOSURE, disclosure_font)
    _, scenario_h = measure(scenario_line, scenario_font)
    caption_w, caption_h = measure(caption, caption_font)
    signature_w, _ = measure(SIGNATURE, signature_font)

    disclosure_y = height - margin_b - disclosure_h
    scenario_y = disclosure_y - gap - scenario_h
    caption_y = scenario_y - gap - caption_h
    signature_x = width - margin_x - signature_w
    # Keep the caption clear of the signature on the same band.
    if margin_x + caption_w > signature_x - width * 0.02:
        caption_font = _font(FONT_SEMIBOLD, width * 0.014)
        caption_w, caption_h = measure(caption, caption_font)
        caption_y = scenario_y - gap - caption_h

    def paint(xy: tuple[float, float], text: str, font: ImageFont.FreeTypeFont, fill: tuple[int, int, int]) -> None:
        x, y = xy
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=fill)

    paint((margin_x, caption_y), caption, caption_font, (255, 255, 255))
    paint((margin_x, scenario_y), scenario_line, scenario_font, (236, 228, 224))
    paint((margin_x, disclosure_y), DISCLOSURE, disclosure_font, (214, 204, 198))
    paint((signature_x, caption_y), SIGNATURE, signature_font, (255, 255, 255))

    image.save(dest, format="PNG", optimize=True)
    saved = Image.open(dest)
    if saved.size != (width, height):
        raise SystemExit(f"bad size {saved.size} for {dest}")
