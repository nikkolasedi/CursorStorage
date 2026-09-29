"""Print-design furniture: halftone gradients, sunbursts, date tags, caption cards, UI toasts."""
import math

import numpy as np
from PIL import Image

from engine import W, H, SS, font, bezier

MONO, MONO_B = "SpaceMono.ttf", "SpaceMono-Bold.ttf"
SERIF_I = "InstrumentSerif-Italic.ttf"
HEAVY, BLACK = "Anton.ttf", "ArchivoBlack.ttf"


def grad(fr, ink, box, t0, t1, vertical=True):
    x0, y0, x1, y1 = [int(v * SS) for v in box]
    w, h = x1 - x0, y1 - y0
    if vertical:
        g = np.linspace(t0, t1, h)[:, None] * np.ones((1, w))
    else:
        g = np.ones((h, 1)) * np.linspace(t0, t1, w)[None, :]
    fr.paste_layer(ink, Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)), (x0 / SS, y0 / SS))


def radial(fr, ink, cx, cy, r, t0, t1):
    y, x = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
    d = np.sqrt((x - cx * SS) ** 2 + (y - cy * SS) ** 2) / (r * SS)
    g = t0 + (t1 - t0) * np.clip(d, 0, 1)
    fr.paste_layer(ink, Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)))


def sunburst(fr, ink, cx, cy, n=24, r=2400, tone=1.0, rot=0.0):
    for k in range(n):
        a0 = rot + k * math.tau / n
        a1 = a0 + math.tau / n / 2
        fr.poly(ink, [(cx, cy), (cx + math.cos(a0) * r, cy + math.sin(a0) * r), (cx + math.cos(a1) * r, cy + math.sin(a1) * r)], tone)


def fit(text, fname, size, maxw):
    w = font(fname, size).getlength(text)
    return size if w <= maxw else size * maxw / w


def giant(fr, text, ink, cx, cy, size, tone=1.0, fname=HEAVY, maxw=W - 80, anchor="mm"):
    fr.text(ink, (cx, cy), text, fname, fit(text, fname, size, maxw), tone, anchor)


def tri(fr, ink, x, y, s, left=True):
    pts = [(x + s, y - s * 0.6), (x + s, y + s * 0.6), (x, y)] if left else [(x, y - s * 0.6), (x, y + s * 0.6), (x + s, y)]
    fr.poly("navy", pts, 0.0)
    fr.poly(ink, pts)


def date_tag(fr, date, mode="rewind", x1=W - 60, y0=52):
    """Top-right broadcast tag: [<< REWIND 2023.09.05] / [> 2025.03.02] / [o LIVE 2026.09.29]."""
    label = {"rewind": "REWIND", "play": "PUTAR", "live": "LIVE", "alt": "ALT"}[mode]
    size = 34
    tw = fr.text_width(f"{label}  {date}", MONO_B, size)
    x0 = x1 - tw - 110
    fr.rect("navy", (x0, y0, x1, y0 + 70))
    ic = x0 + 34
    if mode == "rewind":
        tri(fr, "pink", ic - 18, y0 + 35, 20); tri(fr, "pink", ic + 2, y0 + 35, 20)
    elif mode == "play":
        tri(fr, "orange", ic - 10, y0 + 35, 24, left=False)
    elif mode == "live":
        fr.ellipse("navy", (ic - 14, y0 + 21, ic + 14, y0 + 49), 0.0)
        fr.ellipse("pink", (ic - 14, y0 + 21, ic + 14, y0 + 49))
        fr.ellipse("orange", (ic - 14, y0 + 21, ic + 14, y0 + 49))
    else:
        fr.text("navy", (ic, y0 + 35), "?", MONO_B, 40, 0.0, anchor="mm")
        fr.text("pink", (ic, y0 + 35), "?", MONO_B, 40, anchor="mm")
    fr.knock("text", (x0 + 78, y0 + 36), f"{label}  {date}", MONO_B, size, "lm")


def paper_box(fr, box, radius=0, outline="navy", ow=4):
    fr.knock("rect", box) if not radius else fr.knock("poly", _rrect(box, radius))
    fr.apply_knock()
    if outline:
        pts = _rrect(box, radius) if radius else [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3]), (box[0], box[1])]
        fr.line(outline, pts + [pts[0]], ow)


def _rrect(box, r, n=6):
    x0, y0, x1, y1 = box
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def caption_card(fr, ref, aside, x=70, y=H - 260, ink="orange"):
    """Citation card: heavy ref label + italic serif paraphrase."""
    size = 30
    tw = fr.text_width(ref, MONO_B, size)
    fr.rect(ink, (x, y, x + tw + 44, y + 54))
    fr.text("navy", (x + 22, y + 27), ref, MONO_B, size, anchor="lm")
    aw = fr.text_width(aside, SERIF_I, 44)
    paper_box(fr, (x, y + 54, x + max(aw, tw) + 44, y + 128), outline=None)
    fr.line("navy", [(x, y + 128), (x + max(aw, tw) + 44, y + 128)], 3)
    fr.text("navy", (x + 22, y + 92), aside, SERIF_I, 44, anchor="lm")


def toast(fr, x, y, title, body, w=520, icon="orange"):
    h = 116
    paper_box(fr, (x, y, x + w, y + h), radius=18)
    fr.rect(icon, (x + 20, y + 22, x + 72, y + 74), radius=10)
    fr.text("navy", (x + 92, y + 22), title, MONO_B, 24)
    fr.text("navy", (x + 92, y + 58), body, MONO, 22)


def lyric(fr, text, y=H - 110, size=64, ink="navy", box=True, maxw=W - 300):
    size = fit(text, SERIF_I, size, maxw)
    tw = fr.text_width(text, SERIF_I, size)
    if box:
        paper_box(fr, (W / 2 - tw / 2 - 40, y - size * 0.72, W / 2 + tw / 2 + 40, y + size * 0.62), outline=None)
        fr.rect("pink", (W / 2 - tw / 2 - 40, y + size * 0.62, W / 2 + tw / 2 + 40, y + size * 0.62 + 8))
    fr.text(ink, (W / 2, y), text, SERIF_I, size, anchor="mm")


def print_marks(fr, code):
    """Registration crosshairs and a slug line, like an untrimmed riso sheet."""
    for cx, cy in ((34, 34), (W - 34, H - 34)):
        for ink in ("navy", "pink", "orange"):
            fr.line(ink, [(cx - 16, cy), (cx + 16, cy)], 1.6)
            fr.line(ink, [(cx, cy - 16), (cx, cy + 16)], 1.6)
        fr.line("navy", bezier((cx - 9, cy), (cx - 9, cy - 9), (cx, cy - 9), n=6) + bezier((cx, cy - 9), (cx + 9, cy - 9), (cx + 9, cy), n=6) +
                bezier((cx + 9, cy), (cx + 9, cy + 9), (cx, cy + 9), n=6) + bezier((cx, cy + 9), (cx - 9, cy + 9), (cx - 9, cy), n=6), 1.6)
    fr.text("navy", (70, H - 34), code, MONO, 18, anchor="lm")
    for i, ink in enumerate(("pink", "orange", "navy")):
        fr.rect(ink, (W - 250 + i * 46, H - 46, W - 214 + i * 46, H - 22))


def check(fr, ink, x, y, s, w=None):
    fr.stroke(ink, [(x, y), (x + s * 0.35, y + s * 0.35), (x + s, y - s * 0.55)], w or s * 0.16, taper=False)


def heart(fr, ink, cx, cy, r, tone=1.0):
    pts = []
    for i in range(60):
        t = i / 60 * math.tau
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 16, cy + y * r / 16))
    fr.poly(ink, pts, tone)


def church(fr, ink, cx, base, s, tone=1.0, knock=False):
    """Simple Indonesian parish church facade (tower, cross, arched door)."""
    shapes = [
        [(-0.9, 0), (-0.9, -0.9), (0, -1.5), (0.9, -0.9), (0.9, 0)],
        [(-0.25, -1.2), (-0.25, -2.1), (0, -2.45), (0.25, -2.1), (0.25, -1.2)],
        [(-0.04, -2.45), (0.04, -2.45), (0.04, -2.85), (-0.04, -2.85)],
        [(-0.17, -2.72), (0.17, -2.72), (0.17, -2.64), (-0.17, -2.64)],
    ]
    for sh in shapes:
        pts = [(cx + x * s, base + y * s) for x, y in sh]
        (fr.knock("poly", pts) if knock else fr.poly(ink, pts, tone))
    if not knock:
        door = [(cx - 0.22 * s, base)] + [(cx + math.cos(a) * 0.22 * s, base - 0.45 * s - math.sin(a) * 0.22 * s)
                                          for a in np.linspace(math.pi, 0, 12)] + [(cx + 0.22 * s, base)]
        fr.knock("poly", door)
        fr.knock("ellipse", (cx - 0.1 * s, base - 1.85 * s, cx + 0.1 * s, base - 1.65 * s))
