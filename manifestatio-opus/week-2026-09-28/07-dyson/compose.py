#!/usr/bin/env python3
"""Composite exact typewriter copy onto the Dyson (Sun 4 Oct) bases."""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, "/workspace/manifestatio-opus")
from compose.overlay import (  # noqa: E402
    BLUE,
    GREEN_PAPER,
    INK,
    RED,
    crop_4x5,
    draw_line,
    draw_words,
    font,
    hand_font,
    line_width,
    paint_highlight,
)

SRC = Path("/opt/cursor/artifacts/assets")
BASES = {1: "dyson-01-base-v3.jpg"}
OUT_DIR = Path(__file__).parent / "slides"
ART = Path("/opt/cursor/artifacts")
X = 96
MAX_W = 680
Y0 = 630
SPACE = 14


def hand(draw, lines, xy, size=28, gap=32):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=hand_font(size), fill=INK)
        y += gap


def segments(img, parts, y, size=30, x=X):
    """parts: list of (text, marks) drawn left to right on one line."""
    for i, (text, marks) in enumerate(parts):
        pad = 12 if "circle" in marks else 0
        x += pad if i else 0
        tw, _ = draw_line(img, ImageDraw.Draw(img), text, (x, y), size, marks)
        x += tw + SPACE + pad


def text_block(img, lines, y, size=30, gap=48):
    """lines: list of parts lists (see segments). Returns y after the block."""
    for parts in lines:
        if parts:
            segments(img, parts, y, size)
        y += gap
    return y


def star(draw, cx, cy, r=22):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.line(pts + [pts[0]], fill=INK, width=3)


def slide01(img):
    draw = ImageDraw.Draw(img)
    x, y = 88, 736
    tw, th = line_width(draw, "QUIZ", font(30), extra_gap=4)
    paint_highlight(img, (x, y), tw, th)
    draw = ImageDraw.Draw(img)
    draw_words(draw, "QUIZ", (x, y), font(30), extra_gap=4)

    y += 50
    draw_words(draw, "1. How many prototypes before it worked?", (x, y), font(22))
    y += 34
    draw_words(draw, "A) 512   B) 5,127   C) 51,270", (x + 22, y), font(20))

    y += 46
    draw_words(draw, "2. Who paid the bills while he built?", (x, y), font(22))
    y += 34
    draw_words(draw, "A) investors   B) Deirdre's teaching salary", (x + 22, y), font(20))
    y += 30
    draw_words(draw, "C) a bank", (x + 22, y), font(20))

    hand(draw, ["If you can't", "answer this,", "you have to", "read this."],
         (642, 798), 26, 30)
    draw.arc((712, 742, 772, 802), start=200, end=70, fill=INK, width=3)
    draw.line([(760, 750), (768, 740)], fill=INK, width=3)
    draw.line([(768, 740), (774, 756)], fill=INK, width=3)


def slide02(img):
    text_block(img, [
        [("Bags clog.", {})],
        [("Airflow dies.", {})],
        [("Suction dies.", {})],
        [],
        [("The refill was", {"red_underline": True})],
        [("the real business.", {"red_underline": True})],
    ], Y0 + 20, size=32, gap=52)


def slide03(img):
    text_block(img, [
        [("Deirdre taught art.", {})],
        [],
        [("Her salary funded", {})],
        [("5,127", {"circle": True}), ("prototypes.", {})],
    ], Y0 + 30, size=32, gap=54)
    hand(ImageDraw.Draw(img), ["art-teacher", "salary"], (590, Y0 + 96), 30, 32)


def slide04(img):
    text_block(img, [
        [("Cyclonic separation.", {})],
        [],
        [("No bag.", {"highlight": True})],
        [("Suction that", {})],
        [("does not fade.", {})],
    ], Y0 + 30, size=32, gap=54)


def slide05(img):
    text_block(img, [
        [("Incumbents said no.", {})],
        [],
        [("Bags were the business", {"circle": True, "ucolor": RED})],
        [("they were protecting.", {})],
    ], Y0 + 30, size=32, gap=56)


def slide06(img):
    text_block(img, [
        [("So he sold it himself.", {})],
        [],
        [("And he", {})],
        [("still", {"highlight": True}),
         ("owns", {"highlight": True, "green_underline": True}),
         ("the company.", {"highlight": True})],
    ], Y0 + 30, size=32, gap=54)


def slide07(img):
    y = text_block(img, [
        [("The lesson:", {})],
        [],
        [("if the old product", {})],
        [("needs a refill,", {})],
        [("own the machine", {"highlight": True})],
        [("that doesn't.", {"highlight": True})],
    ], Y0 + 20, size=32, gap=52)
    star(ImageDraw.Draw(img), 640, y - 120)


def slide08(img):
    y = text_block(img, [
        [("This is one story on", {})],
        [("Manifestatio.Opus.", {})],
        [("The Duolingo for", {"highlight": True})],
        [("business enthusiasts.", {"highlight": True})],
        [("Try it now.", {})],
    ], Y0 - 10, size=30, gap=46)
    draw = ImageDraw.Draw(img)
    ly = y + 6
    draw_line(img, draw, "Launch your next business idea.", (X, ly), 27,
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
        img = Image.open(SRC / BASES.get(i, f"dyson-{stem}-base.jpg")).convert("RGBA")
        painter(img)
        final = crop_4x5(img.convert("RGB"))
        final.save(OUT_DIR / f"{stem}.png")
        final.save(OUT_DIR / f"{stem}.jpg", quality=92, optimize=True)
        final.save(ART / f"manifestatio-dyson-{stem}.jpg", quality=92, optimize=True)
        print("wrote", stem)


if __name__ == "__main__":
    main()
