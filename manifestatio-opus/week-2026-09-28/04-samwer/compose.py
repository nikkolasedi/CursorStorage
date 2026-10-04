#!/usr/bin/env python3
"""Composite exact typewriter copy onto the Samwer bases. Slide 1 is the locked quiz cover."""

import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, "/workspace/manifestatio-opus")
from compose.overlay import (  # noqa: E402
    BLUE,
    GREEN_PAPER,
    INK,
    crop_4x5,
    draw_line,
    draw_words,
    font,
    hand_font,
    line_width,
)

HERE = Path(__file__).parent
SRC = Path("/opt/cursor/artifacts/assets")
OUT_DIR = HERE / "slides"
ART = Path("/opt/cursor/artifacts")
X = 96
Y0 = 630
MAX_W = 680


def fit(img, text, size):
    draw = ImageDraw.Draw(img)
    while size > 20 and line_width(draw, text, font(size))[0] > MAX_W:
        size -= 1
    return size


def text_block(img, lines, y, size=30, gap=48):
    size = min(fit(img, t, size) for t, _ in lines if t)
    for text, marks in lines:
        if text:
            draw_line(img, ImageDraw.Draw(img), text, (X, y), size, marks)
        y += gap
    return y


def segments(img, parts, y, size=30):
    """parts: list of (text, marks) drawn left to right on one line."""
    x = X
    for text, marks in parts:
        draw = ImageDraw.Draw(img)
        if marks:
            tw, _ = draw_line(img, draw, text, (x, y), size, marks)
        else:
            tw, _ = draw_words(draw, text, (x, y), font(size))
        x += tw + 22


def star(draw, cx, cy, r=22):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.line(pts + [pts[0]], fill=INK, width=3)


def slide02(img):
    text_block(img, [
        ("The Samwer brothers", {}),
        ("cloned US winners", {"highlight": True}),
        ("and launched them", {}),
        ("in Europe first.", {}),
    ], Y0 + 20, size=32, gap=52)


def slide03(img):
    y = text_block(img, [("Alando cloned eBay.", {})], Y0, 32, 60)
    segments(img, [("Sold in", {}), ("100 days", {"circle": True})], y, 32)
    y += 60
    segments(img, [("for about", {}),
                   ("$43 million.", {"circle": True, "highlight": True, "color": GREEN_PAPER})],
             y, 32)


def slide04(img):
    y = text_block(img, [("Zappos?", {}), ("They built Zalando.", {"highlight": True})],
                   Y0, 32, 58)
    y += 10
    segments(img, [("IPO about", {}),
                   ("€5.3B.", {"circle": True, "highlight": True, "color": GREEN_PAPER})],
             y, 32)


def slide05(img):
    y = text_block(img, [("Groupon?", {}), ("CityDeal.", {"highlight": True}),
                         ("Sold back in months", {})], Y0, 32, 56)
    segments(img, [("for about", {}), ("$126M.", {"circle": True})], y, 32)


def slide06(img):
    y = text_block(img, [("The edge", {}), ("wasn't creativity.", {"red_underline": True})],
                   Y0, 32, 56)
    y += 20
    segments(img, [("It was", {}), ("speed", {"highlight": True})], y, 32)
    text_block(img, [("plus relentless execution.", {})], y + 56, 32)


def slide07(img):
    y = text_block(img, [
        ("The lesson:", {}),
        ("in business,", {}),
        ("execution often", {"highlight": True}),
        ("beats invention.", {"highlight": True}),
    ], Y0 + 10, size=34, gap=56)
    star(ImageDraw.Draw(img), 640, y - 60)


def slide08(img):
    y = text_block(img, [
        ("This is one story on", {}),
        ("Manifestatio.Opus.", {}),
        ("The Duolingo for", {"highlight": True}),
        ("business enthusiasts.", {"highlight": True}),
        ("Try it now.", {}),
    ], Y0 - 10, size=30, gap=46)
    ly = y + 6
    draw_line(img, ImageDraw.Draw(img), "Launch your next business idea.", (X, ly), 27,
              {"underline": True})
    draw = ImageDraw.Draw(img)
    hx, hy = 600, ly - 110
    draw.text((hx, hy), "link in bio", font=hand_font(32), fill=INK)
    draw.line([(hx + 40, hy + 42), (hx - 10, ly - 8)], fill=BLUE, width=3)
    draw.line([(hx - 10, ly - 8), (hx + 6, ly - 12)], fill=BLUE, width=3)
    draw.line([(hx - 10, ly - 8), (hx - 6, ly - 24)], fill=BLUE, width=3)


SLIDES = {2: slide02, 3: slide03, 4: slide04, 5: slide05, 6: slide06, 7: slide07, 8: slide08}


def save(final, stem):
    final.save(OUT_DIR / f"{stem}.png")
    final.save(OUT_DIR / f"{stem}.jpg", quality=92, optimize=True)
    final.save(ART / f"manifestatio-samwer-{stem}.jpg", quality=92, optimize=True)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cover = HERE / "quiz-cover-example"
    shutil.copy(cover / "01-quiz-example.png", OUT_DIR / "01.png")
    Image.open(cover / "01-quiz-example.png").convert("RGB").save(
        OUT_DIR / "01.jpg", quality=92, optimize=True)
    shutil.copy(OUT_DIR / "01.jpg", ART / "manifestatio-samwer-01.jpg")
    for i, painter in SLIDES.items():
        stem = f"{i:02d}"
        img = Image.open(SRC / f"samwer-{stem}-base.jpg").convert("RGBA")
        painter(img)
        save(crop_4x5(img.convert("RGB")), stem)
        print("wrote", stem)


if __name__ == "__main__":
    main()
