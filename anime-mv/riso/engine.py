"""Risograph print engine.

A frame is a set of ink layers (L images, 0 = no ink, 255 = full ink) drawn at 2x.
Mid-tones are converted to halftone dots per ink (each with its own screen angle),
layers are slightly misregistered, then overprinted onto cream paper by multiplication.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
SS = 2
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")

PAPER = np.array([243, 234, 214], np.float32)
INKS = {
    "orange": np.array([233, 104, 52], np.float32),
    "navy": np.array([36, 50, 112], np.float32),
    "pink": np.array([240, 104, 150], np.float32),
}
ORDER = ("pink", "orange", "navy")
SCREEN_ANGLE = {"pink": 15, "orange": 75, "navy": 45}
DOT_PITCH = 9 * SS


@lru_cache(maxsize=None)
def screen(ink):
    a = math.radians(SCREEN_ANGLE[ink])
    y, x = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
    u = (x * math.cos(a) + y * math.sin(a)) / DOT_PITCH * 2 * math.pi
    v = (-x * math.sin(a) + y * math.cos(a)) / DOT_PITCH * 2 * math.pi
    return ((np.cos(u) + np.cos(v)) * 0.25 + 0.5).astype(np.float32)


@lru_cache(maxsize=None)
def grain(seed=0):
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (H // 24, W // 24)).astype(np.float32)
    blot = np.asarray(Image.fromarray(small).resize((W, H), Image.BICUBIC), np.float32)
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    return blot, fine


def font(name, size):
    return _font(name, int(size))


@lru_cache(maxsize=256)
def _font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


class Frame:
    def __init__(self):
        self.L = {k: Image.new("L", (W * SS, H * SS), 0) for k in INKS}
        self.D = {k: ImageDraw.Draw(v) for k, v in self.L.items()}
        self.knock_mask = Image.new("L", (W * SS, H * SS), 0)
        self.KD = ImageDraw.Draw(self.knock_mask)

    # --- primitives (coordinates in 1x units) --------------------------------
    def _v(self, tone):
        return int(np.clip(tone, 0, 1) * 255)

    def poly(self, ink, pts, tone=1.0):
        self.D[ink].polygon([(x * SS, y * SS) for x, y in pts], fill=self._v(tone))

    def ellipse(self, ink, box, tone=1.0):
        x0, y0, x1, y1 = box
        self.D[ink].ellipse((min(x0, x1) * SS, min(y0, y1) * SS, max(x0, x1) * SS, max(y0, y1) * SS), fill=self._v(tone))

    def rect(self, ink, box, tone=1.0, radius=0):
        x0, y0, x1, y1 = box
        b = (min(x0, x1) * SS, min(y0, y1) * SS, max(x0, x1) * SS, max(y0, y1) * SS)
        if radius:
            self.D[ink].rounded_rectangle(b, radius=radius * SS, fill=self._v(tone))
        else:
            self.D[ink].rectangle(b, fill=self._v(tone))

    def line(self, ink, pts, width, tone=1.0):
        self.D[ink].line([(x * SS, y * SS) for x, y in pts], fill=self._v(tone), width=max(1, int(width * SS)), joint="curve")

    def stroke(self, ink, pts, w0, w1=None, tone=1.0, taper=True):
        """Thick-thin ink stroke along a polyline (brush-like, tapered ends)."""
        w1 = w0 if w1 is None else w1
        n = len(pts)
        if n < 2:
            return
        left, right = [], []
        for i in range(n):
            x, y = pts[i]
            xa, ya = pts[max(0, i - 1)]
            xb, yb = pts[min(n - 1, i + 1)]
            dx, dy = xb - xa, yb - ya
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            u = i / (n - 1)
            w = w0 + (w1 - w0) * u
            if taper:
                w *= min(1, math.sin(math.pi * u) * 1.6 + 0.15)
            left.append((x + nx * w / 2, y + ny * w / 2))
            right.append((x - nx * w / 2, y - ny * w / 2))
        self.poly(ink, left + right[::-1], tone)

    def text(self, ink, xy, s, fname, size, tone=1.0, anchor="la"):
        f = font(fname, size * SS)
        self.D[ink].text((xy[0] * SS, xy[1] * SS), s, font=f, fill=self._v(tone), anchor=anchor)

    def text_width(self, s, fname, size):
        return font(fname, size).getlength(s)

    def knock(self, shape, *args):
        """Erase all inks inside a shape (paper shows through)."""
        if shape == "ellipse":
            x0, y0, x1, y1 = args[0]
            self.KD.ellipse((x0 * SS, y0 * SS, x1 * SS, y1 * SS), fill=255)
        elif shape == "poly":
            self.KD.polygon([(x * SS, y * SS) for x, y in args[0]], fill=255)
        elif shape == "rect":
            x0, y0, x1, y1 = args[0]
            self.KD.rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), fill=255)
        elif shape == "text":
            xy, s, fname, size, anchor = args
            self.KD.text((xy[0] * SS, xy[1] * SS), s, font=font(fname, size * SS), fill=255, anchor=anchor)

    def erase_ink(self, ink, pts):
        self.D[ink].polygon([(x * SS, y * SS) for x, y in pts], fill=0)

    def clear(self, box):
        """Erase every ink inside a rectangle immediately."""
        for ink in self.L:
            self.rect(ink, box, 0.0)

    def apply_knock(self):
        if self.knock_mask.getbbox():
            for k in self.L:
                self.L[k] = Image.composite(Image.new("L", self.L[k].size, 0), self.L[k], self.knock_mask)
                self.D[k] = ImageDraw.Draw(self.L[k])
            self.knock_mask = Image.new("L", (W * SS, H * SS), 0)
            self.KD = ImageDraw.Draw(self.knock_mask)

    def paste_layer(self, ink, img_l, xy=(0, 0)):
        """Max-merge an L image (already at 2x) into an ink layer."""
        base = self.L[ink]
        tmp = Image.new("L", base.size, 0)
        tmp.paste(img_l, (int(xy[0] * SS), int(xy[1] * SS)))
        self.L[ink] = Image.fromarray(np.maximum(np.asarray(base), np.asarray(tmp)))
        self.D[ink] = ImageDraw.Draw(self.L[ink])

    # --- output ---------------------------------------------------------------
    def render(self, t=0.0, misreg=1.0, boil=True):
        self.apply_knock()
        blot, fine = grain(0)
        out = np.ones((H, W, 3), np.float32) * PAPER
        out *= (1 + fine[..., None] * 0.018)
        frame_seed = int(t * 12) if boil else 0
        rng = np.random.default_rng(frame_seed)
        for i, ink in enumerate(ORDER):
            v = np.asarray(self.L[ink], np.float32) / 255
            if not v.any():
                continue
            # halftone: solid stays solid, mid tones become dots
            ht = (v > screen(ink)).astype(np.float32)
            cov = np.where(v > 0.97, 1.0, ht)
            cov_img = Image.fromarray((cov * 255).astype(np.uint8)).resize((W, H), Image.BOX)
            c = np.asarray(cov_img, np.float32) / 255
            # misregistration + slight per-frame drift ("boil")
            base_off = {"pink": (4, -3), "orange": (-3, 2), "navy": (0, 0)}[ink]
            dx = int(round(base_off[0] * misreg + (rng.uniform(-1, 1) if boil else 0)))
            dy = int(round(base_off[1] * misreg + (rng.uniform(-1, 1) if boil else 0)))
            c = shift(c, dx, dy)
            # uneven drum ink density
            c = c * np.clip(0.92 + blot * 0.035 + fine * 0.04, 0.6, 1.0)
            ink_c = INKS[ink] / 255
            out *= 1 - c[..., None] * (1 - ink_c[None, None, :])
        # paper fibres
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = a[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def bezier(p0, p1, p2, p3=None, n=24):
    pts = []
    for i in range(n + 1):
        u = i / n
        if p3 is None:
            x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
            y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
        else:
            x = (1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u * u * p2[0] + u ** 3 * p3[0]
            y = (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u * u * p2[1] + u ** 3 * p3[1]
        pts.append((x, y))
    return pts


def T(pts, ox, oy, s, flip=False):
    """Transform local unit coordinates to frame coordinates."""
    return [((-x if flip else x) * s + ox, y * s + oy) for x, y in pts]
