#!/usr/bin/env python3
"""Composite exact typewriter copy onto the Louis Vuitton test-run bases."""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, "/workspace/manifestatio-opus")
from compose.overlay import (  # noqa: E402
    BLUE,
    INK,
    crop_4x5,
    draw_line,
    draw_words,
    font,
    hand_font,
    line_width,
    paint_highlight,
)

SRC = Path("/opt/cursor/artifacts/assets")
OUT_DIR = Path(__file__).parent / "slides"
ART = Path("/opt/cursor/artifacts")
X = 96
MAX_W = 680
Y0 = 630


def hand(draw, lines, xy, size=28, gap=32):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=hand_font(size), fill=INK)
        y += gap


def fit(img, text, size):
    draw = ImageDraw.Draw(img)
    while size > 20 and line_width(draw, text, font(size))[0] > MAX_W:
        size -= 1
    return size


def text_block(img, lines, y, size=30, gap=48):
    """lines: list of (text, marks). Returns y after the block."""
    size = min(fit(img, t, size) for t, _ in lines if t)
    for text, marks in lines:
        draw = ImageDraw.Draw(img)
        if text:
            draw_line(img, draw, text, (X, y), size, marks)
        y += gap
    return y


def slide01(img):
    draw = ImageDraw.Draw(img)
    x, y = 88, 724
    tw, th = line_width(draw, "QUIZ", font(30), extra_gap=4)
    paint_highlight(img, (x, y), tw, th)
    draw = ImageDraw.Draw(img)
    draw_words(draw, "QUIZ", (x, y), font(30), extra_gap=4)

    y += 50
    draw_words(draw, "1. Why were his trunks", (x, y), font(22))
    y += 32
    draw_words(draw, "flat on top?", (x + 22, y), font(22))
    y += 34
    draw_words(draw, "A) Cost   B) Stacking   C) Style", (x + 22, y), font(20))

    y += 46
    draw_words(draw, "2. The LV monogram was born", (x, y), font(22))
    y += 32
    _, h = draw_words(draw, "in 1896 to fight ___.", (x + 22, y), font(22))
    bx = x + 22 + line_width(draw, "in 1896 to fight", font(22))[0] + 12
    draw.line([(bx, y + h + 4), (bx + 44, y + h + 6)], fill=BLUE, width=3)
    y += 34
    draw_words(draw, "A) Rivals   B) Fakes   C) Tax", (x + 22, y), font(20))

    hand(draw, ["If you can't", "answer this,", "you have to", "read this."],
         (628, 786), 26, 30)
    draw.arc((700, 730, 760, 790), start=200, end=70, fill=INK, width=3)
    draw.line([(748, 738), (756, 728)], fill=INK, width=3)
    draw.line([(756, 728), (762, 744)], fill=INK, width=3)


def year_line(img, year, rest, y, size):
    draw = ImageDraw.Draw(img)
    tw, _ = draw_line(img, draw, year, (X, y), size, {"circle": True})
    draw_words(ImageDraw.Draw(img), rest, (X + tw + 22, y), font(size))


def slide02(img):
    y = text_block(img, [
        ("1835.", {}),
        ("A 13-year-old leaves", {}),
        ("the Jura on foot.", {}),
        ("", {}),
        ("Destination: Paris.", {"highlight": True}),
    ], Y0)
    draw = ImageDraw.Draw(img)
    draw_words(draw, "About", (X, y), font(30))
    ax = X + line_width(draw, "About", font(30))[0] + 22
    tw, _ = draw_line(img, draw, "400 km.", (ax, y), 30, {"circle": True})
    hand(ImageDraw.Draw(img), ["took him", "two years"], (ax + tw + 50, y - 20), 32, 34)


def slide03(img):
    text_block(img, [
        ("1837: apprentice to a", {}),
        ("Paris box-maker and packer.", {}),
        ("", {}),
        ("He learned how the rich travel,", {}),
        ("and what breaks on the way.", {"highlight": True}),
    ], Y0 + 20)


def slide04(img):
    text_block(img, [
        ("The flaw:", {}),
        ("trunks had rounded tops.", {}),
        ("", {}),
        ("You couldn't stack them.", {"red_underline": True}),
    ], Y0 + 40, size=32, gap=52)


def slide05(img):
    year_line(img, "1858:", "flat top.", Y0, 30)
    text_block(img, [
        ("Canvas, not leather.", {}),
        ("Lighter. Water-resistant.", {}),
        ("Stackable.", {"highlight": True}),
        ("", {}),
        ("Made for trains and steamships.", {"underline": True}),
    ], Y0 + 48)


def slide06(img):
    text_block(img, [("Then came the copies.", {"red_underline": True})], Y0, 30)
    y = Y0 + 70
    year_line(img, "1888:", "his name goes on", y, 28)
    text_block(img, [("the canvas.", {})], y + 44, 28)
    year_line(img, "1896:", "son Georges draws", y + 100, 28)
    text_block(img, [("the Monogram.", {}), ("", {}),
                     ("The logo was built to fight fakes.", {"highlight": True})],
               y + 144, 28, 44)


def slide07(img):
    y = text_block(img, [
        ("The lesson:", {}),
        ("he didn't invent luggage.", {}),
        ("", {}),
        ("He fixed one annoying flaw", {"highlight": True}),
        ("right when travel changed.", {}),
    ], Y0 + 10, size=31, gap=50)
    draw = ImageDraw.Draw(img)
    cx, cy, r = 720, y - 60, 22
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.line(pts + [pts[0]], fill=INK, width=3)


def slide08(img):
    y = text_block(img, [
        ("This is one story on", {}),
        ("Manifestatio.Opus.", {}),
        ("The Duolingo for", {"highlight": True}),
        ("business enthusiasts.", {"highlight": True}),
        ("Try it now.", {}),
    ], Y0 - 10, size=30, gap=46)
    draw = ImageDraw.Draw(img)
    ly = y + 6
    tw, th = draw_line(img, draw, "Launch your next business idea.", (X, ly), 27,
                       {"underline": True})
    draw = ImageDraw.Draw(img)
    hx, hy = 600, ly - 110
    hand(draw, ["link in bio"], (hx, hy), 32)
    draw.line([(hx + 40, hy + 42), (hx - 10, ly - 8)], fill=BLUE, width=3)
    draw.line([(hx - 10, ly - 8), (hx + 6, ly - 12)], fill=BLUE, width=3)
    draw.line([(hx - 10, ly - 8), (hx - 6, ly - 24)], fill=BLUE, width=3)


SLIDES = [slide01, slide02, slide03, slide04, slide05, slide06, slide07, slide08]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, painter in enumerate(SLIDES, 1):
        stem = f"{i:02d}"
        img = Image.open(SRC / f"lv-{stem}-base.jpg").convert("RGBA")
        painter(img)
        final = crop_4x5(img.convert("RGB"))
        final.save(OUT_DIR / f"{stem}.png")
        final.save(OUT_DIR / f"{stem}.jpg", quality=92, optimize=True)
        final.save(ART / f"manifestatio-lv-test-{stem}.jpg", quality=92, optimize=True)
        print("wrote", stem)


if __name__ == "__main__":
    main()
