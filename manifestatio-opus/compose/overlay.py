"""Typewriter overlay for Manifestatio.Opus slides.

Highlights brighten the paper first. Ink is always drawn last, full black.
Never composite a translucent color over letters.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/tmp/fonts/SpecialElite-Regular.ttf"
HAND_PATH = "/tmp/fonts/Caveat-Regular.ttf"

# Bright highlighter on the paper, matching identity/highlight-reference.jpg
YELLOW_PAPER = (255, 236, 110, 230)
GREEN_PAPER = (186, 210, 140, 200)
INK = (28, 26, 24, 255)
BLUE = (59, 126, 161, 255)
RED = (196, 69, 54, 255)
GREEN = (122, 158, 92, 255)
WORD_GAP = 10


def font(size, path=FONT_PATH):
    return ImageFont.truetype(path, size)


def hand_font(size):
    path = HAND_PATH if Path(HAND_PATH).exists() else FONT_PATH
    return ImageFont.truetype(path, size)


def measure(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def line_width(draw, text, fnt, extra_gap=WORD_GAP):
    w = 0
    first = True
    for word in text.split(" "):
        if not first:
            sw, _ = measure(draw, " ", fnt)
            w += sw + extra_gap
        ww, _ = measure(draw, word, fnt)
        w += ww
        first = False
    return w, measure(draw, "Hg", fnt)[1]


def paint_highlight(img, xy, w, h, color=YELLOW_PAPER, pad=6):
    """Brighten the paper behind a phrase. Call this before drawing ink."""
    x, y = xy
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        [x - pad, y - pad + 4, x + w + pad, y + h + pad - 2],
        radius=4,
        fill=color,
    )
    base = img.convert("RGBA")
    img.paste(Image.alpha_composite(base, layer))


def draw_words(draw, text, xy, fnt, fill=INK, extra_gap=WORD_GAP):
    x, y = xy
    first = True
    for word in text.split(" "):
        if not first:
            sw, _ = measure(draw, " ", fnt)
            x += sw + extra_gap
        draw.text((x, y), word, font=fnt, fill=fill)
        ww, _ = measure(draw, word, fnt)
        x += ww
        first = False
    return x - xy[0], measure(draw, "Hg", fnt)[1]


def underline(draw, xy, w, color=BLUE, thickness=3, y_off=26):
    x, y = xy
    draw.line([(x, y + y_off), (x + w, y + y_off + 2)], fill=color, width=thickness)


def circle_words(draw, xy, w, h, color=BLUE):
    x, y = xy
    draw.ellipse([x - 10, y - 8, x + w + 12, y + h + 10], outline=color, width=3)


def draw_line(img, draw, text, xy, size, marks=None, extra_gap=WORD_GAP):
    """Measure, paint paper marks, then stamp full-black typewriter ink."""
    marks = marks or {}
    fnt = font(size)
    tw, th = line_width(draw, text, fnt, extra_gap=extra_gap)
    if "highlight" in marks:
        paint_highlight(img, xy, tw, th, marks.get("color", YELLOW_PAPER))
        draw = ImageDraw.Draw(img)
    if "underline" in marks:
        underline(draw, xy, tw, marks.get("ucolor", BLUE), y_off=th + 4)
    if "green_underline" in marks:
        underline(draw, xy, tw, GREEN, thickness=4, y_off=th + 4)
    if "red_underline" in marks:
        underline(draw, xy, tw, RED, thickness=3, y_off=th + 4)
    if "circle" in marks:
        circle_words(draw, xy, tw, th, marks.get("ucolor", BLUE))
    draw_words(draw, text, xy, fnt, extra_gap=extra_gap)
    return tw, th


def crop_4x5(img, size=(1080, 1350)):
    target_h = int(round(img.width / 0.8))
    extra = img.height - target_h
    top = extra // 2
    return img.crop((0, top, img.width, top + target_h)).resize(
        size, Image.Resampling.LANCZOS
    )
