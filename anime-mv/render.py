"""Procedural anime-style motion graphics for "Kutemukan Tuhan di Dirimu" (first 30 s).

Usage:
    python3 render.py                      # full 0-30 s render -> out/part1_0-30s.mp4
    python3 render.py --stills 3 12 20     # PNG stills at given times -> out/still_*.png
"""
import argparse
import math
import os
import random
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from timing import (INTRO_1, INTRO_2, V1_L1, V1_L2, V1_L3, V1_L4a, V1_L4b, BEAT)

W, H = 1920, 1080
FPS = 30
DURATION = 30.0
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "out")
AUDIO = os.path.join(HERE, "audio", "song.mp3")

# Scene boundaries (seconds)
T_GATE = 5.05        # zoom into the gunungan gate begins
T_DUSK = 5.95        # dusk landscape fully revealed
T_ROOM = 10.55       # cut to the room
T_DESK = 14.75       # close-up of the song sheet
T_ROOF = 19.35       # exterior: notes fly over the roofs
T_END = 29.55        # final bloom


# ----------------------------------------------------------------------------
# math helpers
# ----------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def ss(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0)) if e1 != e0 else float(x >= e1)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def mix_rgb(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def font(name, size):
    return _font(name, int(size))


@lru_cache(maxsize=256)
def _font(name, size):
    path = os.path.join(FONTS, name)
    f = ImageFont.truetype(path, size)
    if "[wght]" in name or name in ("Caveat.ttf", "Playfair.ttf", "PlayfairItalic.ttf",
                                    "Cormorant.ttf", "CormorantItalic.ttf"):
        pass
    return f


def var_font(name, size, weight):
    f = ImageFont.truetype(os.path.join(FONTS, name), int(size))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


@lru_cache(maxsize=64)
def vfont(name, size, weight):
    return var_font(name, size, weight)


# ----------------------------------------------------------------------------
# image helpers
# ----------------------------------------------------------------------------
def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    cols = np.zeros((h, 3), np.float32)
    pos = [s[0] for s in stops]
    for c in range(3):
        cols[:, c] = np.interp(ys, pos, [s[1][c] for s in stops])
    arr = np.repeat(cols[:, None, :], w, axis=1)
    a = np.full((h, w, 1), 255, np.float32)
    return Image.fromarray(np.concatenate([arr, a], 2).astype(np.uint8), "RGBA")


def radial_alpha(w, h, cx, cy, r, power=2.0, sx=1.0, sy=1.0):
    y, x = np.ogrid[0:h, 0:w]
    d = np.sqrt(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** power


def glow_layer(w, h, cx, cy, r, color, strength=1.0, power=2.0, sx=1.0, sy=1.0):
    a = radial_alpha(w, h, cx, cy, r, power, sx, sy) * strength
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def screen_add(base, layer, amount=1.0):
    """Additive blend of RGBA layer (premultiplied by its alpha) onto RGB(A) base."""
    b = np.asarray(base.convert("RGB"), np.float32)
    l = np.asarray(layer, np.float32)
    a = l[..., 3:4] / 255.0 * amount
    out = b + l[..., :3] * a
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")


def with_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    al = img.getchannel("A").point(lambda v: int(v * a))
    img.putalpha(al)
    return img


def paste(base, sprite, x, y, alpha=1.0, center=True):
    if alpha <= 0.003:
        return
    if center:
        x -= sprite.width // 2
        y -= sprite.height // 2
    base.alpha_composite(with_alpha(sprite, alpha), (int(x), int(y))) if (
        0 <= x and 0 <= y and x + sprite.width <= base.width and y + sprite.height <= base.height
    ) else _paste_clipped(base, with_alpha(sprite, alpha), int(x), int(y))


def _paste_clipped(base, sprite, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.width, x + sprite.width), min(base.height, y + sprite.height)
    if x1 <= x0 or y1 <= y0:
        return
    crop = sprite.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    base.alpha_composite(crop, (x0, y0))


def ss_draw(w, h, fn, scale=2):
    """Supersampled drawing: fn(draw, s) draws with coordinates multiplied by s."""
    img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fn(d, scale)
    return img.resize((w, h), Image.LANCZOS)


def blur(img, r):
    return img.filter(ImageFilter.GaussianBlur(r)) if r > 0.3 else img


def camera(img, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0):
    """Zoom/rotate around (cx, cy) keeping output size W x H."""
    if abs(zoom - 1) < 1e-4 and abs(rot) < 1e-4:
        return img
    if abs(rot) > 1e-4:
        img = img.rotate(rot, resample=Image.BICUBIC, center=(cx, cy))
    cw, ch = W / zoom, H / zoom
    box = (cx - cw * (cx / W), cy - ch * (cy / H), cx + cw * (1 - cx / W), cy + ch * (1 - cy / H))
    return img.resize((W, H), Image.BICUBIC, box=box)


# ----------------------------------------------------------------------------
# sprites
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def kamboja_sprite(size=96, tint=0):
    """Frangipani (bunga kamboja): five overlapping petals, white with a yellow heart."""
    s = 4
    S = size * s
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    petal = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pd = ImageDraw.Draw(petal)
    pd.ellipse((S * 0.40, S * 0.04, S * 0.66, S * 0.52), fill=(255, 255, 255, 255))
    pa = np.asarray(petal).astype(np.float32)
    yy = np.linspace(0, 1, S)[:, None]
    heart = np.clip((yy - 0.25) / 0.3, 0, 1)
    base_col = np.array([255, 250, 240]) if tint == 0 else np.array([255, 214, 226])
    col = base_col[None, None, :] * (1 - heart[..., None]) + np.array([255, 196, 60])[None, None, :] * heart[..., None]
    pa[..., :3] = col
    petal = Image.fromarray(pa.astype(np.uint8), "RGBA")
    for k in range(5):
        img.alpha_composite(petal.rotate(k * 72 + 8, resample=Image.BICUBIC, center=(S / 2, S / 2)))
    d = ImageDraw.Draw(img)
    for k in range(5):
        a = math.radians(k * 72 + 8 - 90)
        d.line((S / 2, S / 2, S / 2 + math.cos(a) * S * 0.2, S / 2 + math.sin(a) * S * 0.2),
               fill=(235, 160, 40, 150), width=s * 2)
    d.ellipse((S / 2 - S * 0.04, S / 2 - S * 0.04, S / 2 + S * 0.04, S / 2 + S * 0.04), fill=(230, 150, 30, 255))
    return img.resize((size, size), Image.LANCZOS)


@lru_cache(maxsize=None)
def kamboja_rot(size, angle_idx, tint=0):
    return kamboja_sprite(size, tint).rotate(angle_idx * 10, resample=Image.BICUBIC)


@lru_cache(maxsize=None)
def note_sprite(kind=0, size=80, color=(255, 236, 170)):
    """Glowing music note: 0 = eighth note, 1 = beamed pair."""
    s = 4
    S = size * s
    img = Image.new("RGBA", (S * 2, S * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = color + (255,)
    ox, oy = S * 0.5, S * 0.5
    def head(cx, cy):
        hd = Image.new("RGBA", (S * 2, S * 2), (0, 0, 0, 0))
        ImageDraw.Draw(hd).ellipse((cx - S * 0.17, cy - S * 0.12, cx + S * 0.17, cy + S * 0.12), fill=c)
        return hd.rotate(22, center=(cx, cy), resample=Image.BICUBIC)
    if kind == 0:
        img.alpha_composite(head(ox + S * 0.35, oy + S * 0.78))
        d.rectangle((ox + S * 0.48, oy + S * 0.1, ox + S * 0.52, oy + S * 0.76), fill=c)
        d.polygon([(ox + S * 0.52, oy + S * 0.1), (ox + S * 0.78, oy + S * 0.36),
                   (ox + S * 0.74, oy + S * 0.52), (ox + S * 0.52, oy + S * 0.3)], fill=c)
    else:
        img.alpha_composite(head(ox + S * 0.2, oy + S * 0.82))
        img.alpha_composite(head(ox + S * 0.72, oy + S * 0.72))
        d.rectangle((ox + S * 0.33, oy + S * 0.18, ox + S * 0.37, oy + S * 0.8), fill=c)
        d.rectangle((ox + S * 0.85, oy + S * 0.08, ox + S * 0.89, oy + S * 0.7), fill=c)
        d.polygon([(ox + S * 0.33, oy + S * 0.18), (ox + S * 0.89, oy + S * 0.08),
                   (ox + S * 0.89, oy + S * 0.2), (ox + S * 0.33, oy + S * 0.3)], fill=c)
    img = img.resize((size * 2, size * 2), Image.LANCZOS)
    g = blur(img, size * 0.18)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(g)
    out.alpha_composite(img)
    return out


@lru_cache(maxsize=None)
def sparkle_sprite(size=48, color=(255, 240, 200)):
    arr = np.zeros((size, size, 4), np.float32)
    y, x = np.mgrid[0:size, 0:size] - size / 2 + 0.5
    r = np.sqrt(x * x + y * y) / (size / 2)
    star = np.clip(1 - np.abs(x) / 1.2, 0, 1) * np.clip(1 - np.abs(y) / (size / 2), 0, 1) + \
        np.clip(1 - np.abs(y) / 1.2, 0, 1) * np.clip(1 - np.abs(x) / (size / 2), 0, 1)
    core = np.clip(1 - r, 0, 1) ** 3
    a = np.clip(star * 0.9 + core, 0, 1)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a * 255
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ----------------------------------------------------------------------------
# global overlays
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def grain_frames():
    rng = np.random.default_rng(7)
    frames = []
    for _ in range(6):
        n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        img = Image.fromarray(np.clip(128 + n * 22, 0, 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR)
        frames.append(np.asarray(img, np.float32) - 128)
    return frames


@lru_cache(maxsize=None)
def vignette_arr():
    y, x = np.ogrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.68)) ** 2)
    return np.clip(1 - np.clip(d - 0.55, 0, 1) ** 1.6 * 0.85, 0, 1)[..., None].astype(np.float32)


def finish(img, t, vig=1.0, grain=1.0, fade=1.0):
    arr = np.asarray(img.convert("RGB"), np.float32)
    v = vignette_arr()
    arr = arr * (1 - vig + vig * v)
    g = grain_frames()[int(t * FPS) % 6]
    arr += g[..., None] * 0.18 * grain
    arr *= fade
    return np.clip(arr, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------
# lyrics / kinetic typography
# ----------------------------------------------------------------------------
@lru_cache(maxsize=512)
def text_sprite(text, fname, size, color, stroke=0, stroke_color=(0, 0, 0), weight=None, glow=0,
                glow_color=None, shadow=None):
    f = vfont(fname, size, weight) if weight else font(fname, size)
    l, t_, r, b = f.getbbox(text, stroke_width=stroke)
    pad = int(size * 0.5) + glow * 3
    w, h = r - l + pad * 2, b - t_ + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        dx, dy, sc = shadow
        d.text((pad - l + dx, pad - t_ + dy), text, font=f, fill=sc + (255,), stroke_width=stroke,
               stroke_fill=sc + (255,))
    d.text((pad - l, pad - t_), text, font=f, fill=color + (255,), stroke_width=stroke,
           stroke_fill=stroke_color + (255,))
    if glow:
        gc = glow_color or color
        m = Image.new("RGBA", (w, h), gc + (0,))
        m.putalpha(img.getchannel("A"))
        g = blur(m, glow)
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out.alpha_composite(g)
        out.alpha_composite(g)
        out.alpha_composite(img)
        img = out
    # anchor offset: position where the text origin sits inside the sprite
    return img, (pad - l, pad - t_)


def word_advance(fname, size, text, weight=None):
    f = vfont(fname, size, weight) if weight else font(fname, size)
    return f.getlength(text)


def draw_lyric(base, words, t, x, y, fname, size, align="left", color=(255, 255, 255),
               hi=(255, 214, 120), glow=10, glow_color=(120, 170, 255), weight=None,
               out_t=None, style="rise", space=None):
    """Karaoke kinetic line: words fade/rise in at their start, glow gold while sung."""
    space = space if space is not None else size * 0.28
    widths = [word_advance(fname, size, w[0], weight) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    if align == "center":
        x0 = x - total / 2
    elif align == "right":
        x0 = x - total
    else:
        x0 = x
    out_a = 1.0 if out_t is None else 1 - ss(out_t, out_t + 0.5, t)
    if out_a <= 0:
        return
    cx = x0
    for (wtxt, ws, we), wd in zip(words, widths):
        lead = 0.22
        p = clamp((t - (ws - lead)) / 0.45)
        if p <= 0:
            cx += wd + space
            continue
        sung = ss(ws - 0.05, ws + 0.1, t) * (1 - ss(we, we + 0.6, t))
        col = mix_rgb(color, hi, sung)
        spr, (ax, ay) = text_sprite(wtxt, fname, size, col, weight=weight, glow=glow, glow_color=glow_color)
        e = ease_out_cubic(p)
        if style == "rise":
            dy = (1 - e) * size * 0.45
            dx = 0
        elif style == "drop":
            dy = -(1 - ease_out_back(p)) * size * 0.6
            dx = 0
        else:
            dy = 0
            dx = (1 - e) * size * 0.3
        bounce = math.sin(clamp((t - ws) / 0.35) * math.pi) * size * 0.06 if t > ws else 0
        a = e * out_a
        if p < 1 and style != "drop":
            spr = blur(spr, (1 - e) * 6)
        paste(base, spr, cx - ax + dx, y - ay + dy - bounce, a, center=False)
        cx += wd + space


def draw_write_on(base, words, t, x, y, fname, size, color, glow_color, glow=8, weight=None):
    """Handwriting reveal: each word is wiped on left-to-right across its sung duration."""
    space = size * 0.3
    widths = [word_advance(fname, size, w[0], weight) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    cx = x - total / 2
    tip = None
    for (wtxt, ws, we), wd in zip(words, widths):
        dur = min(max(0.35, (we - ws) * 0.8), 0.9)
        p = clamp((t - ws + 0.05) / dur)
        if p > 0:
            spr, (ax, ay) = text_sprite(wtxt, fname, size, color, weight=weight, glow=glow, glow_color=glow_color)
            cut = int(ax + wd * ease_in_out(p) + (glow * 2 if p >= 1 else 0))
            cut = min(spr.width, cut) if p < 1 else spr.width
            if cut > 0:
                part = spr.crop((0, 0, cut, spr.height))
                paste(base, part, cx - ax, y - ay, 1.0, center=False)
            if p < 1:
                tip = (cx + wd * ease_in_out(p), y + size * 0.55)
        cx += wd + space
    return tip


# ----------------------------------------------------------------------------
# SCENE A: wayang kulit prologue (0 - ~5.9 s)
# ----------------------------------------------------------------------------
GUN_W, GUN_H = 760, 1120   # gunungan sprite size (includes the gapit handle)


def gunungan_outline(w, h, s):
    """Leaf/mountain silhouette of the kayon; returns polygon points (scaled by s)."""
    pts_r = []
    body_h = h * 0.86
    base_y = body_h
    for i in range(0, 101):
        v = i / 100.0
        y = base_y - v * body_h * 0.97
        hw = w * 0.47 * (1 - v) ** 0.72 * (1 + 0.42 * math.sin(math.pi * min(1, v * 1.05)))
        hw *= 1 - 0.08 * math.exp(-((v - 0.82) / 0.07) ** 2)
        pts_r.append((w / 2 + hw, y))
    pts_l = [(w - x, y) for x, y in reversed(pts_r)]
    pts = pts_r + pts_l
    return [(x * s, y * s) for x, y in pts]


@lru_cache(maxsize=None)
def gunungan_masks():
    """Returns (shadow_mask L, door_mask L) for the kayon, carved with tatahan holes."""
    s = 2
    w, h = GUN_W, GUN_H
    m = Image.new("L", (w * s, h * s), 0)
    d = ImageDraw.Draw(m)
    outline = gunungan_outline(w, h, s)
    d.polygon(outline, fill=255)
    body_h = h * 0.86
    # gapit (the horn/wood handle the dalang holds)
    d.rectangle(((w / 2 - 9) * s, (body_h - 10) * s, (w / 2 + 9) * s, (h - 4) * s), fill=255)
    d.polygon([((w / 2 - 22) * s, (h - 4) * s), ((w / 2 + 22) * s, (h - 4) * s),
               ((w / 2 + 9) * s, (h - 60) * s), ((w / 2 - 9) * s, (h - 60) * s)], fill=255)

    # inset rows of punched dots (tatahan) following the outline
    inner = []
    cx = w / 2
    for k, inset in enumerate((0.93, 0.86)):
        for i in range(0, 101, 2):
            v = i / 100.0
            if v > 0.95:
                continue
            y = body_h - v * body_h * 0.97
            hw = w * 0.47 * (1 - v) ** 0.72 * (1 + 0.42 * math.sin(math.pi * min(1, v * 1.05)))
            hw *= 1 - 0.08 * math.exp(-((v - 0.82) / 0.07) ** 2)
            for sign in (-1, 1):
                x = cx + sign * hw * inset
                yy = y - 14 if v < 0.02 else y
                r = 4.2 if k == 0 else 3.0
                if yy < body_h - 18:
                    d.ellipse(((x - r) * s, (yy - r) * s, (x + r) * s, (yy + r) * s), fill=0)

    # tree of life: trunk + symmetrical curling branches with leaf holes
    gate_top = body_h - 250
    trunk_top = body_h * 0.14
    def line(p, q, wd):
        d.line((p[0] * s, p[1] * s, q[0] * s, q[1] * s), fill=0, width=int(wd * s))
    def leaf(x, y, r, ang):
        lf = [(x + math.cos(ang) * r * 1.8, y + math.sin(ang) * r * 1.8),
              (x + math.cos(ang + 1.9) * r * 0.6, y + math.sin(ang + 1.9) * r * 0.6),
              (x - math.cos(ang) * r * 0.4, y - math.sin(ang) * r * 0.4),
              (x + math.cos(ang - 1.9) * r * 0.6, y + math.sin(ang - 1.9) * r * 0.6)]
        d.polygon([(a * s, b * s) for a, b in lf], fill=0)
    # trunk as a pair of slits
    for off in (-7, 7):
        line((cx + off, gate_top), (cx + off * 0.5, trunk_top), 5)
    rng = random.Random(3)
    for j, yb in enumerate(np.linspace(gate_top - 40, trunk_top + 60, 7)):
        span = (w * 0.34) * (1 - (gate_top - yb) / (gate_top - trunk_top) * 0.75)
        for sign in (-1, 1):
            prev = (cx, yb)
            for k in range(1, 9):
                u = k / 8
                px = cx + sign * span * u
                py = yb - math.sin(u * math.pi * 0.9) * 70 - u * 30 + math.sin(u * 7 + j) * 6
                line(prev, (px, py), 6 - u * 3)
                prev = (px, py)
                if k % 2 == 0:
                    leaf(px, py - 10, 9 - u * 3, -math.pi / 2 + sign * (0.5 + u))
                    leaf(px, py + 8, 7 - u * 2, math.pi / 2 - sign * (0.2 + u * 0.5))
            # curl at the tip
            ex, ey = prev
            for q in range(10):
                a0 = q / 10 * math.pi * 1.6
                r0 = 18 * (1 - q / 12)
                p1 = (ex + sign * math.sin(a0) * r0, ey - math.cos(a0) * r0 + 18)
                d.ellipse(((p1[0] - 2.6) * s, (p1[1] - 2.6) * s, (p1[0] + 2.6) * s, (p1[1] + 2.6) * s), fill=0)
    # peak ornament: small flame-shaped holes
    for i in range(6):
        yy = trunk_top - 30 - i * 26
        r = 9 - i * 1.2
        d.ellipse(((cx - r) * s, (yy - r * 1.4) * s, (cx + r) * s, (yy + r * 1.4) * s), fill=0)
    # two birds (garuda-ish chevrons) on the branches
    for sign in (-1, 1):
        bx, by = cx + sign * 150, body_h * 0.36
        d.polygon([((bx - 30) * s, by * s), (bx * s, (by + 12) * s), ((bx + 30) * s, by * s),
                   (bx * s, (by - 6) * s)], fill=0)
    # gate (gapura) with roof tiers; the door opening is the portal into the next scene
    gx0, gx1 = cx - 120, cx + 120
    gy0, gy1 = gate_top, body_h - 26
    for tier in range(3):
        yy = gy0 + tier * 30
        inset = 20 + tier * 26
        d.polygon([((gx0 + inset - 40 + tier * 20) * s, (yy + 28) * s), ((cx) * s, (yy - 10) * s),
                   ((gx1 - inset + 40 - tier * 20) * s, (yy + 28) * s)], fill=0)
        d.polygon([((gx0 + inset - 26 + tier * 20) * s, (yy + 22) * s), ((cx) * s, (yy - 0) * s),
                   ((gx1 - inset + 26 - tier * 20) * s, (yy + 22) * s)], fill=255)
    # pillars
    for px in (gx0 + 18, gx1 - 18):
        d.rectangle(((px - 7) * s, (gy0 + 95) * s, (px + 7) * s, gy1 * s), fill=0)
    # door arch
    door = Image.new("L", (w * s, h * s), 0)
    dd = ImageDraw.Draw(door)
    dx0, dx1, dy0, dy1 = cx - 62, cx + 62, gy0 + 110, gy1 - 4
    dd.rectangle((dx0 * s, (dy0 + 40) * s, dx1 * s, dy1 * s), fill=255)
    dd.pieslice((dx0 * s, dy0 * s, dx1 * s, (dy0 + 90) * s), 180, 360, fill=255)
    # door is closed initially: two leaves drawn as solid, with a thin center slit
    d.rectangle(((cx - 1.5) * s, (dy0 + 30) * s, (cx + 1.5) * s, dy1 * s), fill=0)
    # steps
    for k in range(3):
        d.rectangle(((cx - 90 - k * 16) * s, (gy1 + 4 + k * 7) * s, (cx + 90 + k * 16) * s,
                     (gy1 + 7 + k * 7) * s), fill=0)
    m = m.resize((w, h), Image.LANCZOS)
    door = door.resize((w, h), Image.LANCZOS)
    return m, door, ((dx0 + dx1) / 2, (dy0 + dy1) / 2 + 10)


@lru_cache(maxsize=None)
def kelir_base():
    """The shadow-puppet screen: warm cloth lit by the blencong oil lamp."""
    rng = np.random.default_rng(11)
    base = vgrad(W, H, [(0, (206, 128, 56)), (0.45, (244, 190, 112)), (1, (170, 84, 36))])
    arr = np.asarray(base, np.float32)
    weave = rng.normal(0, 1, (H, W)).astype(np.float32)
    weave = np.asarray(blur(Image.fromarray(np.clip(128 + weave * 40, 0, 255).astype(np.uint8)), 0.8), np.float32) - 128
    fib = (np.sin(np.arange(W) * 1.9)[None, :] * 3 + np.sin(np.arange(H) * 2.3)[:, None] * 3)
    arr[..., :3] += (weave * 0.12 + fib)[..., None]
    glow = radial_alpha(W, H, W * 0.55, H * 0.38, W * 0.75, 1.4)[..., None]
    arr[..., :3] = arr[..., :3] * (0.45 + 0.75 * glow)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


@lru_cache(maxsize=None)
def kelir_frame():
    """Carved wooden frame of the screen with a batik parang border strip."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    wood = (46, 18, 10, 255)
    d.rectangle((0, 0, W, 46), fill=wood)
    d.rectangle((0, H - 58, W, H), fill=wood)
    gold = (196, 142, 60, 255)
    for y0 in (38, H - 58):
        d.rectangle((0, y0, W, y0 + 8), fill=(120, 40, 20, 255))
        for x in range(-40, W + 40, 34):
            d.line((x, y0 + 8, x + 20, y0), fill=gold, width=2)
    # parang motif on the bottom beam
    for x in range(-60, W + 60, 46):
        d.arc((x, H - 46, x + 40, H - 10), 200, 340, fill=gold, width=3)
        d.ellipse((x + 16, H - 34, x + 24, H - 26), outline=gold, width=2)
    return img


def batik_kawung_tile(size, color, lw=2):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    r = size * 0.36
    for ang in (0, 90, 180, 270):
        a = math.radians(ang + 45)
        ex, ey = c + math.cos(a) * r * 0.72, c + math.sin(a) * r * 0.72
        e = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ed = ImageDraw.Draw(e)
        ed.ellipse((ex - r * 0.55, ey - r * 0.33, ex + r * 0.55, ey + r * 0.33), outline=color, width=lw)
        ed.ellipse((ex - 3, ey - 3, ex + 3, ey + 3), fill=color)
        img.alpha_composite(e.rotate(-(ang + 45), center=(ex, ey), resample=Image.BICUBIC))
    d.ellipse((c - 4, c - 4, c + 4, c + 4), fill=color)
    return img


@lru_cache(maxsize=None)
def kawung_field(w, h, size, color):
    tile = batik_kawung_tile(size, color)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(0, h, size):
        for x in range(0, w, size):
            img.alpha_composite(tile, (x, y))
    return img


def gunungan_transform(t):
    """(x, y, scale, rot_deg, flip_x, blur_px, shadow_alpha) of the kayon at time t."""
    rise = ease_out_cubic((t - 0.55) / 1.6)
    x = 1390
    y = lerp(H + 620, 520, rise)
    sc = 0.78
    blur_px = lerp(26, 1.2, ss(0.6, 2.4, t))
    rot = math.sin(t * 1.7) * 2.2 * (1 - ss(4.3, 4.6, t))
    flip = 1.0
    if t > 4.35:
        # move to center then twirl: the traditional kayon spin that ends a scene
        mv = ease_in_out((t - 4.35) / 0.55)
        x = lerp(1390, W / 2, mv)
        spin = ease_in_out((t - 4.45) / 0.75)
        flip = math.cos(spin * math.pi * 4)
    if t > T_GATE:
        z = (t - T_GATE) / (T_DUSK - T_GATE)
        sc = 0.78 * math.exp(ease_in_out(z) * 3.35)
    return x, y, sc, rot, flip, blur_px, 1.0


def scene_wayang(t):
    img = kelir_base().copy()
    flick = 0.9 + 0.06 * math.sin(t * 13.1) + 0.04 * math.sin(t * 29.7 + 1) + 0.03 * math.sin(t * 5.3)
    lamp = glow_layer(W, H, W * 0.55, H * 0.33, 820, (255, 214, 140), 0.55 * flick, 1.6)
    img = screen_add(img, lamp, 0.6)
    arr = np.asarray(img, np.float32)
    arr[..., :3] *= flick * (1 - 0.85 * ss(T_GATE, T_GATE + 0.45, t))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    shadow, door, (dcx, dcy) = gunungan_masks()
    x, y, sc, rot, flip, bl, _ = gunungan_transform(t)
    fw = max(2, int(GUN_W * sc * abs(flip)))
    fh = int(GUN_H * sc)
    sm = shadow.resize((fw, fh), Image.BILINEAR)
    if abs(rot) > 0.01:
        sm = sm.rotate(rot, resample=Image.BICUBIC, expand=True)
    sm = blur(sm, bl * min(1.0, sc / 0.78) if sc < 2 else bl)
    # anchor: the door center stays pinned at the zoom target
    ax = (dcx / GUN_W) * sm.width
    ay = (dcy / GUN_H) * sm.height
    zoom_target = (W / 2, H / 2 + 40)
    if t > T_GATE:
        z = ease_in_out((t - T_GATE) / 0.6)
        px = lerp(x, zoom_target[0], z)
        py_door = lerp(y - GUN_H * 0.78 / 2 + dcy * 0.78, zoom_target[1], z)
    else:
        px = x
        py_door = y - GUN_H * 0.78 / 2 + dcy * 0.78
    ox, oy = px - ax, py_door - ay
    shadow_col = Image.new("RGBA", sm.size, (26, 10, 6, 255))
    shadow_col.putalpha(sm.point(lambda v: int(v * 0.93)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _paste_clipped(layer, shadow_col, int(ox), int(oy))
    img.alpha_composite(layer)
    img.alpha_composite(kelir_frame())

    # a second, smaller wayang shadow: a bird (burung) crossing, for life
    if 1.8 < t < 4.4:
        u = (t - 1.8) / 2.6
        bx = lerp(-120, 900, u)
        by = 260 + math.sin(u * 6) * 30
        flap = math.sin(t * 9)
        bird = Image.new("RGBA", (220, 120), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bird)
        bd.polygon([(20, 60 - flap * 40), (100, 62), (200, 58 - flap * 40), (110, 76), (60, 72)],
                   fill=(26, 10, 6, 200))
        bd.ellipse((96, 54, 130, 74), fill=(26, 10, 6, 200))
        paste(img, blur(bird, 3), bx, by, 0.85 * ss(1.8, 2.3, t) * (1 - ss(3.9, 4.4, t)))
    return img, (ox, oy, sm.width, sm.height, door, sc, flip, rot)


def door_mask_for(t, info):
    ox, oy, sw, sh, door, sc, flip, rot = info
    open_amt = ease_out_cubic((t - (T_GATE + 0.12)) / 0.5)
    dm = door
    if open_amt < 1:
        # doors swinging open: reveal a vertical strip that widens from the center
        arr = np.asarray(dm, np.float32)
        cols = np.abs(np.arange(arr.shape[1]) - arr.shape[1] / 2) / (62 + 1e-6)
        strip = (cols <= open_amt * 1.05).astype(np.float32)
        dm = Image.fromarray((arr * strip[None, :]).astype(np.uint8))
    dm = dm.resize((sw, sh), Image.BILINEAR)
    full = Image.new("L", (W, H), 0)
    full.paste(dm, (int(ox), int(oy)))
    return blur(full, 2)


# ----------------------------------------------------------------------------
# SCENE B: dusk over sawah terraces and a volcano, title card (5.1 - 10.55 s)
# ----------------------------------------------------------------------------
def cloud_mask(w, h, seed, n=26, flat=0.55):
    rng = random.Random(seed)
    s = 2
    m = Image.new("L", (w * s, h * s), 0)
    d = ImageDraw.Draw(m)
    base_y = h * 0.8
    for i in range(n):
        u = rng.random()
        cx = w * (0.14 + 0.72 * u)
        r = h * (0.1 + 0.2 * math.sin(math.pi * u) * rng.uniform(0.7, 1.1))
        cy = base_y - r * rng.uniform(0.3, 1.2) * (0.4 + math.sin(math.pi * u))
        cy = max(cy, r + 6)
        d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=255)
    d.rectangle((0, base_y * s, w * s, h * s), fill=0)
    d.rounded_rectangle((w * 0.1 * s, (base_y - h * 0.1) * s, w * 0.9 * s, (base_y + h * 0.03) * s),
                        radius=h * 0.065 * s, fill=255)
    return m.resize((w, h), Image.LANCZOS)


@lru_cache(maxsize=None)
def anime_cloud(w, h, seed, lit=(255, 206, 190), shade=(122, 92, 160), rim=(255, 236, 200), sun_dx=-1.0):
    m = cloud_mask(w, h, seed)
    ma = np.asarray(m, np.float32) / 255
    yy = np.linspace(0, 1, h)[:, None]
    shade_t = np.clip((yy - 0.25) / 0.6, 0, 1)
    col = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        col[..., c] = lit[c] * (1 - shade_t) + shade[c] * shade_t
    # rim light on the side facing the sun
    shift = np.roll(ma, int(-sun_dx * 14), axis=1)
    shift = np.roll(shift, 10, axis=0)
    rim_a = np.clip(ma - shift, 0, 1)
    rim_a = np.asarray(blur(Image.fromarray((rim_a * 255).astype(np.uint8)), 2), np.float32) / 255
    for c in range(3):
        col[..., c] = col[..., c] * (1 - rim_a) + rim[c] * rim_a
    # inner soft shading blobs
    inner = np.asarray(blur(m, 18), np.float32) / 255
    col *= (0.82 + 0.18 * inner)[..., None]
    out = np.dstack([col, ma * 255])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


@lru_cache(maxsize=None)
def dusk_layers():
    """Static parallax layers for the dusk landscape (rendered at 1.25x width for panning)."""
    LW = int(W * 1.3)
    L = {}
    # volcano with a thin plume
    v = Image.new("RGBA", (LW, H), (0, 0, 0, 0))
    def draw_volcano(d, s):
        pts = [(0, 900), (300, 820), (620, 620), (820, 430), (880, 405), (940, 402), (1000, 420),
               (1180, 560), (1480, 720), (1900, 820), (LW, 860), (LW, H), (0, H)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=(96, 62, 120, 255))
        # snow-less ridges highlighted by the dusk
        for k in range(5):
            x0 = 850 + k * 22
            d.line(((x0) * s, 418 * s, (x0 - 120 + k * 50) * s, (600 + k * 20) * s), fill=(122, 80, 136, 110), width=3 * s)
        d.polygon([(880 * s, 405 * s), (940 * s, 402 * s), (930 * s, 414 * s), (890 * s, 414 * s)], fill=(60, 36, 80, 255))
    v = ss_draw(LW, H, draw_volcano)
    L["volcano"] = v
    # far hills
    rng = random.Random(5)
    def hills(d, s, base, amp, col, seed):
        r = random.Random(seed)
        pts = [(0, H)]
        for x in range(0, LW + 40, 40):
            y = base + math.sin(x / 260 + seed) * amp + math.sin(x / 90 + seed * 2) * amp * 0.3
            pts.append((x, y))
        pts.append((LW, H))
        d.polygon([(x * s, y * s) for x, y in pts], fill=col)
    L["hill1"] = ss_draw(LW, H, lambda d, s: hills(d, s, 800, 26, (70, 48, 96, 255), 1.3))
    # sawah terraces: stepped strips that catch the sky reflection
    def terraces(d, s):
        for k in range(7):
            y0 = 860 + k * 34
            col = (40 + k * 4, 34 + k * 3, 70 - k * 3, 255)
            pts = [(0, H)]
            for x in range(0, LW + 30, 30):
                pts.append((x, y0 + math.sin(x / 210 + k * 1.3) * 14))
            pts.append((LW, H))
            d.polygon([(x * s, y * s) for x, y in pts], fill=col)
            # water reflection line
            ln = [(x * s, (y0 + 4 + math.sin(x / 210 + k * 1.3) * 14) * s) for x in range(0, LW + 30, 30)]
            d.line(ln, fill=(255, 170, 140, 150 - k * 15), width=3 * s)
    L["terraces"] = ss_draw(LW, H, terraces)
    # coconut palms silhouettes
    def palms(d, s):
        for (px, base, hgt, lean) in [(160, H + 10, 520, 0.18), (330, H + 10, 430, -0.1),
                                      (2250, H + 10, 560, -0.22), (2080, H + 10, 400, 0.08)]:
            topx, topy = px + lean * hgt, base - hgt
            pts = []
            for i in range(21):
                u = i / 20
                x = px + lean * hgt * u ** 1.4
                y = base - hgt * u
                pts.append((x, y))
            for i in range(len(pts) - 1):
                wd = 22 - 12 * i / 20
                d.line((pts[i][0] * s, pts[i][1] * s, pts[i + 1][0] * s, pts[i + 1][1] * s), fill=(20, 14, 34, 255), width=int(wd * s))
            for k in range(9):
                ang = -math.pi / 2 + (k - 4) * 0.42 + rng.uniform(-0.1, 0.1)
                ln = 200 + rng.uniform(-30, 40)
                prev = (topx, topy)
                for j in range(1, 13):
                    u = j / 12
                    x = topx + math.cos(ang) * ln * u * 1.25
                    y = topy + math.sin(ang) * ln * u + (ln * 0.55) * u * u
                    wd = 12 * (1 - u) + 2
                    d.line((prev[0] * s, prev[1] * s, x * s, y * s), fill=(20, 14, 34, 255), width=int(wd * s))
                    # leaflets
                    for sg in (-1, 1):
                        lx = x + math.cos(ang + sg * 1.4) * 34 * (1 - u * 0.6)
                        ly = y + math.sin(ang + sg * 1.4) * 34 * (1 - u * 0.6) + 22
                        d.line((x * s, y * s, lx * s, ly * s), fill=(20, 14, 34, 255), width=int(3 * s))
                    prev = (x, y)
            d.ellipse(((topx - 22) * s, (topy - 10) * s, (topx + 22) * s, (topy + 26) * s), fill=(20, 14, 34, 255))
    L["palms"] = ss_draw(LW, H, palms)
    L["cloud1"] = anime_cloud(1100, 420, 21)
    L["cloud2"] = anime_cloud(800, 320, 44, lit=(255, 190, 176), shade=(150, 96, 170))
    L["cloud3"] = anime_cloud(1300, 380, 9, lit=(255, 222, 205), shade=(110, 90, 170))
    return L


def dusk_sky(t, horizon_shift=0.0):
    return vgrad(W, H, [(0, (34, 38, 104)), (0.28, (98, 72, 156)), (0.5 + horizon_shift, (236, 128, 142)),
                        (0.66 + horizon_shift, (255, 184, 128)), (0.78, (255, 222, 170)), (1, (255, 180, 130))])


def birds(img, t, t0, n=7, x0=200, y0=330, speed=160, scale=1.0, col=(30, 18, 50, 255)):
    d = ImageDraw.Draw(img)
    for i in range(n):
        row = i // 2 * (1 if i % 2 else -1)
        bx = x0 + (t - t0) * speed - abs(row) * 34 * scale + i * 6
        by = y0 + row * 22 * scale + math.sin(t * 2 + i) * 4
        f = math.sin(t * 8 + i * 1.3)
        sz = 14 * scale
        d.line([(bx - sz, by - f * sz * 0.6), (bx, by), (bx + sz, by - f * sz * 0.6)], fill=col, width=max(2, int(3 * scale)))


def petals_field(img, t, seed, n, t0, area=(0, 0, W, H), wind=(-220, 60), size=(18, 42), alpha=1.0, tint=0,
                 blur_near=False):
    rng = random.Random(seed)
    for i in range(n):
        sx = rng.uniform(area[0], area[2] + 600)
        sy = rng.uniform(area[1] - 200, area[3])
        sp = rng.uniform(0.6, 1.4)
        sz = int(rng.uniform(*size))
        ph = rng.uniform(0, 6.28)
        el = (t - t0) * sp
        x = sx + wind[0] * el + math.sin(el * 1.3 + ph) * 40
        y = sy + wind[1] * el + math.sin(el * 2.1 + ph) * 30
        span = area[2] - area[0] + 800
        x = (x - area[0] + 400) % span + area[0] - 400
        ang = int(((el * 90 * sp + ph * 57) % 360) / 10) % 36
        spr = kamboja_rot(sz, ang, tint)
        a = alpha * (0.7 + 0.3 * math.sin(el * 3 + ph))
        paste(img, spr, x, y, a)


def scene_dusk(t):
    L = dusk_layers()
    u = clamp((t - 5.0) / 5.6)
    img = dusk_sky(t)
    # sun + god rays
    sun_x, sun_y = 1330 - u * 50, 650 + u * 50
    img = screen_add(img, glow_layer(W, H, sun_x, sun_y, 900, (255, 170, 110), 0.55, 1.8), 1)
    img = screen_add(img, glow_layer(W, H, sun_x, sun_y, 90, (255, 246, 220), 0.9, 1.4), 1)
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for k in range(14):
        a = k / 14 * math.pi * 2 + t * 0.05
        spread = 0.035
        rd.polygon([(sun_x, sun_y), (sun_x + math.cos(a - spread) * 2200, sun_y + math.sin(a - spread) * 2200),
                    (sun_x + math.cos(a + spread) * 2200, sun_y + math.sin(a + spread) * 2200)],
                   fill=(255, 230, 190, 34))
    img = screen_add(img, blur(rays, 14), 0.9)
    # clouds drift
    pan = u * 180
    paste(img, L["cloud3"], 420 - pan * 0.25 + t * 6, 170, 0.95)
    paste(img, L["cloud1"], 1600 - pan * 0.35 - t * 4, 250, 1.0)
    paste(img, L["cloud2"], 250 - pan * 0.45, 470, 0.85)
    # volcano plume
    plume = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plume)
    vx = 910 - pan * 0.5 + 0 - 180
    for k in range(10):
        yy = 395 - k * 34
        xx = vx + 90 + math.sin(t * 0.8 + k * 0.6) * 10 + k * k * 1.6
        r = 22 + k * 7
        pd.ellipse((xx - r, yy - r * 0.7, xx + r, yy + r * 0.7), fill=(230, 180, 196, 60 - k * 5))
    img.alpha_composite(blur(plume, 8))
    paste(img, L["volcano"], -180 - pan * 0.5, 0, 1.0, center=False)
    img = screen_add(img, glow_layer(W, H, sun_x, 760, 1000, (255, 140, 120), 0.35, 2.5, sy=0.35), 1)
    paste(img, L["hill1"], -240 - pan * 0.7, 0, 1.0, center=False)
    birds(img, t, 5.5, n=7, x0=380, y0=320, speed=120, scale=1.0)
    paste(img, L["terraces"], -260 - pan * 0.9, 0, 1.0, center=False)
    petals_field(img, t, 3, 14, 5.0, wind=(-260, 80), size=(18, 34), alpha=0.9)
    paste(img, L["palms"], -300 - pan * 1.3, 0, 1.0, center=False)
    petals_field(img, t, 8, 5, 5.0, wind=(-420, 120), size=(60, 90), alpha=0.95)
    return img


def draw_title(img, t):
    """Anime-OP style title card: slam-in letters over a red brush band + rotating kawung halo."""
    t0 = 7.55
    if t < t0 - 0.2:
        return img
    out_a = 1 - ss(10.2, 10.55, t)
    # rotating ornament halo
    halo_a = ss(t0, t0 + 0.6, t) * out_a
    if halo_a > 0:
        ring = _title_ring()
        r = ring.rotate(-t * 12, resample=Image.BICUBIC)
        paste(img, r, W / 2, 470, halo_a * 0.85)
    # brush band
    band_p = ease_out_cubic((t - t0) / 0.35)
    if band_p > 0:
        band = _brush_band()
        cut = int(band.width * band_p)
        if cut > 2:
            paste(img, band.crop((0, 0, cut, band.height)), (W - band.width) / 2, 430, out_a, center=False)
    lines = [("KUTEMUKAN", 118, 330, 0.0), ("TUHAN", 190, 470, 0.35), ("DI DIRIMU", 118, 640, 0.7)]
    for text, size, y, delay in lines:
        f = font("DelaGothic.ttf", size)
        total = f.getlength(text) + (len(text) - 1) * size * 0.04
        x = W / 2 - total / 2
        for i, ch in enumerate(text):
            adv = f.getlength(ch) + size * 0.04
            if ch == " ":
                x += adv
                continue
            lt = t0 + delay + i * 0.035
            p = clamp((t - lt) / 0.32)
            if p <= 0:
                x += adv
                continue
            spr, (ax, ay) = text_sprite(ch, "DelaGothic.ttf", size, (255, 252, 244), stroke=3,
                                        stroke_color=(40, 16, 40), glow=6, glow_color=(255, 200, 150),
                                        shadow=(8, 9, (200, 30, 60)))
            sc = lerp(2.4, 1.0, ease_out_back(p, 2.2))
            if abs(sc - 1) > 0.01:
                spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
            cx = x - ax + (spr.width / sc) / 2
            cy = y - ay + (spr.height / sc) / 2
            paste(img, spr, cx, cy, clamp(p * 3) * out_a)
            x += adv
    # subtitle
    sub_p = clamp((t - (t0 + 1.25)) / 0.6)
    if sub_p > 0:
        spr, (ax, ay) = text_sprite("~  sebuah puisi yang dinyanyikan  ~", "CormorantItalic.ttf", 50,
                                    (255, 246, 230), glow=7, glow_color=(40, 14, 44), weight=700)
        paste(img, spr, W / 2, 820 + (1 - ease_out_cubic(sub_p)) * 20, sub_p * out_a)
        spr2, _ = text_sprite("nikkolas_ep", "Cormorant.ttf", 36, (255, 230, 206), weight=700, glow=6,
                              glow_color=(40, 14, 44))
        paste(img, spr2, W / 2, 880, sub_p * out_a * 0.9)
    # speed-line sparkles on impact
    for k, (lt, sx) in enumerate([(t0 + 0.35, 700), (t0 + 0.55, 1250), (t0 + 0.8, 980)]):
        p = clamp((t - lt) / 0.5)
        if 0 < p < 1:
            sp = sparkle_sprite(int(lerp(40, 180, ease_out_cubic(p))))
            paste(img, sp, sx, 470 + (k - 1) * 90, (1 - p) * out_a)
    return img


@lru_cache(maxsize=None)
def _title_ring():
    size = 900
    def fn(d, s):
        c = size / 2
        for r, wd, a in [(410, 3, 170), (392, 1, 120), (300, 2, 90)]:
            d.ellipse(((c - r) * s, (c - r) * s, (c + r) * s, (c + r) * s), outline=(255, 226, 170, a), width=wd * s)
        for k in range(24):
            a0 = k / 24 * math.pi * 2
            x, y = c + math.cos(a0) * 401, c + math.sin(a0) * 401
            e = 16
            d.ellipse(((x - e) * s, (y - e * 0.55) * s, (x + e) * s, (y + e * 0.55) * s), outline=(255, 214, 150, 170), width=2 * s)
            d.ellipse(((x - 3) * s, (y - 3) * s, (x + 3) * s, (y + 3) * s), fill=(255, 230, 180, 200))
        for k in range(48):
            a0 = k / 48 * math.pi * 2
            d.line(((c + math.cos(a0) * 312) * s, (c + math.sin(a0) * 312) * s,
                    (c + math.cos(a0) * 330) * s, (c + math.sin(a0) * 330) * s), fill=(255, 226, 170, 110), width=2 * s)
    return ss_draw(size, size, fn)


@lru_cache(maxsize=None)
def _brush_band():
    w, h = 1500, 230
    rng = random.Random(4)
    def fn(d, s):
        for k in range(26):
            y = rng.uniform(40, h - 40)
            th = rng.uniform(12, 40)
            x0 = rng.uniform(0, 80)
            x1 = w - rng.uniform(0, 120)
            d.rounded_rectangle((x0 * s, (y - th / 2) * s, x1 * s, (y + th / 2) * s), radius=th / 2 * s,
                                fill=(196, 24, 54, 150))
        d.rounded_rectangle((40 * s, 60 * s, (w - 60) * s, (h - 60) * s), radius=50 * s, fill=(210, 28, 60, 230))
    return ss_draw(w, h, fn)


# ----------------------------------------------------------------------------
# SCENE C1: the songwriter's room at night (10.55 - 14.75 s)
# ----------------------------------------------------------------------------
WIN = (1010, 120, 1790, 770)   # window rect in room space


@lru_cache(maxsize=None)
def city_night():
    """Jakarta-ish skyline behind the window (Monas + towers) with lit windows."""
    x0, y0, x1, y1 = WIN
    w, h = x1 - x0 + 200, y1 - y0 + 40
    img = vgrad(w, h, [(0, (14, 18, 52)), (0.55, (44, 38, 96)), (0.85, (108, 66, 120)), (1, (150, 90, 120))])
    rng = random.Random(12)
    d = ImageDraw.Draw(img)
    for _ in range(90):
        sx, sy = rng.uniform(0, w), rng.uniform(0, h * 0.5)
        r = rng.choice([0.8, 1.0, 1.4])
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(230, 230, 255, rng.randint(120, 255)))
    # moon
    mx, my = w * 0.78, h * 0.2
    img = screen_add(img, glow_layer(w, h, mx, my, 180, (190, 200, 255), 0.6, 2), 1)
    d = ImageDraw.Draw(img)
    d.ellipse((mx - 42, my - 42, mx + 42, my + 42), fill=(250, 246, 226, 255))
    d.ellipse((mx - 26, my - 50, mx + 58, my + 34), fill=(30, 30, 76, 255))
    # skyline
    layers = [((58, 46, 100), 0.62, 0.35), ((36, 30, 74), 0.7, 0.55), ((22, 20, 50), 0.8, 0.8)]
    for col, base, lit_p in layers:
        x = -20
        while x < w:
            bw = rng.uniform(40, 110)
            bh = rng.uniform(60, 260) * (1.3 if rng.random() < 0.15 else 1)
            top = h * base - bh * 0.6 + rng.uniform(-10, 30)
            d.rectangle((x, top, x + bw, h), fill=col + (255,))
            if rng.random() < 0.2:
                d.line((x + bw / 2, top, x + bw / 2, top - 30), fill=col + (255,), width=3)
                d.ellipse((x + bw / 2 - 3, top - 34, x + bw / 2 + 3, top - 28), fill=(255, 80, 80, 255))
            for wy in np.arange(top + 10, h - 6, 14):
                for wx in np.arange(x + 6, x + bw - 6, 12):
                    if rng.random() < 0.18 * lit_p:
                        d.rectangle((wx, wy, wx + 5, wy + 7), fill=(255, 214, 140, rng.randint(140, 255)))
            x += bw + rng.uniform(2, 12)
        if col == layers[0][0]:
            # Monas: obelisk with a golden flame
            mxp = w * 0.33
            top = h * 0.2
            d.polygon([(mxp - 12, h), (mxp - 7, top + 60), (mxp + 7, top + 60), (mxp + 12, h)], fill=(70, 56, 112, 255))
            d.polygon([(mxp - 38, top + 60), (mxp + 38, top + 60), (mxp + 26, top + 74), (mxp - 26, top + 74)], fill=(70, 56, 112, 255))
            d.rectangle((mxp - 6, top + 30, mxp + 6, top + 60), fill=(70, 56, 112, 255))
            d.polygon([(mxp - 8, top + 30), (mxp, top), (mxp + 9, top + 30)], fill=(255, 196, 80, 255))
            img = screen_add(img, glow_layer(w, h, mxp, top + 16, 50, (255, 190, 90), 0.8, 2), 1)
            d = ImageDraw.Draw(img)
    return img


@lru_cache(maxsize=None)
def room_static():
    """Room interior: walls, window frame, curtains, desk, guitar, shelf."""
    def fn(d, s):
        S = lambda *p: [v * s for v in p]
        # back wall
        d.rectangle(S(0, 0, W, H), fill=(34, 40, 78, 255))
        # wall panel lines (kos-kosan wallpaper stripes)
        for x in range(0, W, 64):
            d.line(S(x, 0, x, 820), fill=(40, 47, 88, 255), width=2 * s)
        # floor
        d.rectangle(S(0, 820, W, H), fill=(26, 26, 54, 255))
        # window hole (transparent, city is composited under)
        d.rectangle(S(*WIN), fill=(0, 0, 0, 0))
        x0, y0, x1, y1 = WIN
        fr = (58, 40, 40, 255)
        d.rectangle(S(x0 - 22, y0 - 22, x1 + 22, y0), fill=fr)
        d.rectangle(S(x0 - 22, y1, x1 + 22, y1 + 30), fill=fr)
        d.rectangle(S(x0 - 22, y0, x0, y1), fill=fr)
        d.rectangle(S(x1, y0, x1 + 22, y1), fill=fr)
        mx = (x0 + x1) / 2
        d.rectangle(S(mx - 8, y0, mx + 8, y1), fill=fr)
        d.rectangle(S(x0, y0 + 190, x1, y0 + 202), fill=fr)
        # teralis (window grille) with a simple floral curl
        for gx in np.linspace(x0 + 60, x1 - 60, 8):
            d.line(S(gx, y0 + 202, gx, y1), fill=(30, 22, 30, 230), width=3 * s)
        for gy in (y0 + 380, y0 + 560):
            d.line(S(x0, gy, x1, gy), fill=(30, 22, 30, 230), width=3 * s)
        # desk
        d.rectangle(S(760, 700, 1900, 742), fill=(78, 50, 44, 255))
        d.rectangle(S(760, 742, 1900, 760), fill=(48, 30, 30, 255))
        d.rectangle(S(800, 760, 830, 1000), fill=(40, 26, 28, 255))
        d.rectangle(S(1840, 760, 1870, 1000), fill=(40, 26, 28, 255))
        # guitar leaning on the wall
        gx, gy = 330, 740
        d.ellipse(S(gx - 150, gy - 30, gx + 150, gy + 250), fill=(120, 60, 34, 255))
        d.ellipse(S(gx - 115, gy - 190, gx + 115, gy + 40), fill=(120, 60, 34, 255))
        d.ellipse(S(gx - 44, gy - 50, gx + 44, gy + 38), fill=(30, 18, 16, 255))
        d.polygon(S(gx - 16, gy - 70, gx + 16, gy - 70, gx + 60, gy - 520, gx + 34, gy - 524), fill=(60, 34, 24, 255))
        d.polygon(S(gx + 32, gy - 520, gx + 66, gy - 518, gx + 80, gy - 610, gx + 40, gy - 612), fill=(48, 26, 20, 255))
        for k in range(6):
            d.line(S(gx - 10 + k * 4, gy + 150, gx + 42 + k * 2, gy - 590), fill=(210, 200, 170, 160), width=1 * s)
        d.rectangle(S(gx - 50, gy + 140, gx + 50, gy + 158), fill=(40, 22, 18, 255))
        # small shelf with a cross (salib) and a framed photo
        d.rectangle(S(560, 170, 860, 184), fill=(70, 46, 40, 255))
        d.rectangle(S(700, 70, 708, 170), fill=(200, 170, 110, 255))
        d.rectangle(S(680, 100, 728, 108), fill=(200, 170, 110, 255))
        d.rectangle(S(600, 110, 660, 170), fill=(90, 70, 70, 255))
        d.rectangle(S(606, 116, 654, 164), fill=(150, 130, 160, 255))
        # books
        for k, (bw, bh, col) in enumerate([(18, 60, (140, 60, 60)), (14, 52, (60, 90, 140)),
                                           (20, 66, (180, 150, 80)), (16, 48, (90, 120, 90))]):
            bx = 760 + sum(b[0] + 4 for b in [(18,), (14,), (20,), (16,)][:k])
            d.rectangle(S(bx, 170 - bh, bx + bw, 170), fill=col + (255,))
    return ss_draw(W, H, fn)


@lru_cache(maxsize=None)
def boy_sprite():
    """Original character (back view): messy anime hair, hoodie, headphones on his neck."""
    w, h = 620, 700
    def fn(d, s):
        S = lambda pts: [(x * s, y * s) for x, y in pts]
        body = (18, 22, 44, 255)
        hair = (14, 14, 28, 255)
        cx = 300
        # torso / hoodie
        d.polygon(S([(cx - 70, 250), (cx + 70, 250), (cx + 200, 330), (cx + 240, 700), (cx - 240, 700), (cx - 200, 330)]), fill=body)
        d.ellipse(S([(cx - 215, 300), (cx - 125, 420)]), fill=body)
        d.ellipse(S([(cx + 125, 300), (cx + 215, 420)]), fill=body)
        # hood lump
        d.ellipse(S([(cx - 120, 225), (cx + 120, 330)]), fill=(24, 28, 56, 255))
        # right arm reaching forward to the desk
        d.polygon(S([(cx + 170, 330), (cx + 250, 380), (cx + 230, 560), (cx + 120, 600), (cx + 110, 520), (cx + 160, 470)]), fill=body)
        # left arm
        d.polygon(S([(cx - 170, 330), (cx - 250, 390), (cx - 250, 560), (cx - 150, 600), (cx - 150, 500)]), fill=body)
        # neck
        d.rectangle(S([(cx - 34, 180), (cx + 34, 260)]), fill=(26, 24, 40, 255))
        # head
        d.ellipse(S([(cx - 105, 20), (cx + 105, 240)]), fill=hair)
        # hair: a rounded mass plus a few big curved clumps (anime-style tufts)
        rng = random.Random(8)
        d.ellipse(S([(cx - 118, 14), (cx + 118, 214)]), fill=hair)
        def clump(ang, length, width, bend):
            bx, by = cx + math.cos(ang) * 92, 118 + math.sin(ang) * 92
            tip = (bx + math.cos(ang + bend) * length, by + math.sin(ang + bend) * length)
            nx, ny = -math.sin(ang), math.cos(ang)
            mid = (bx + math.cos(ang + bend * 0.5) * length * 0.55, by + math.sin(ang + bend * 0.5) * length * 0.55)
            d.polygon(S([(bx + nx * width, by + ny * width), (mid[0] + nx * width * 0.45, mid[1] + ny * width * 0.45),
                         tip, (mid[0] - nx * width * 0.45, mid[1] - ny * width * 0.45),
                         (bx - nx * width, by - ny * width)]), fill=hair)
        for i, ang in enumerate(np.linspace(math.pi * 1.05, math.pi * 1.95, 7)):
            clump(ang, 44 + (i % 3) * 10, 30, 0.35 if i < 3 else -0.35)
        # nape tufts pointing down
        for k, (x, ln) in enumerate([(-80, 46), (-44, 64), (-8, 52), (30, 66), (66, 48)]):
            d.polygon(S([(cx + x - 22, 186), (cx + x + 22, 186), (cx + x + 8 + rng.uniform(-4, 4), 186 + ln)]), fill=hair)
        # side flicks over the ears
        d.polygon(S([(cx - 110, 110), (cx - 160, 196), (cx - 96, 176)]), fill=hair)
        d.polygon(S([(cx + 110, 110), (cx + 162, 190), (cx + 96, 176)]), fill=hair)
        # ahoge (a single stray strand)
        d.line(S([(cx + 10, 0 + 10), (cx + 30, -10 + 10), (cx + 60, 4 + 10)]), fill=hair, width=8 * s)
        # ears
        d.ellipse(S([(cx - 118, 120), (cx - 92, 168)]), fill=(38, 30, 46, 255))
        d.ellipse(S([(cx + 92, 120), (cx + 118, 168)]), fill=(38, 30, 46, 255))
        # headphones around the neck
        d.arc(S([(cx - 90, 180), (cx + 90, 320)]), 200, 340, fill=(60, 64, 110, 255), width=12 * s)
        d.rounded_rectangle(S([(cx - 120, 236), (cx - 74, 290)]), radius=16 * s, fill=(70, 76, 130, 255))
        d.rounded_rectangle(S([(cx + 74, 236), (cx + 120, 290)]), radius=16 * s, fill=(70, 76, 130, 255))
    img = ss_draw(w, h, fn)
    # rim lights: warm from the desk lamp (left), cool from the window (right/top)
    a = np.asarray(img.getchannel("A"), np.float32) / 255
    def rim(dx, dy, col, strength, width):
        sh = np.roll(np.roll(a, dx, axis=1), dy, axis=0)
        e = np.clip(a - sh, 0, 1)
        e = np.asarray(blur(Image.fromarray((e * 255).astype(np.uint8)), width), np.float32) / 255 * a
        layer = np.zeros((h, w, 4), np.float32)
        layer[..., :3] = col
        layer[..., 3] = np.clip(e * strength, 0, 1) * 255
        return Image.fromarray(layer.astype(np.uint8), "RGBA")
    img.alpha_composite(rim(5, 3, (255, 184, 110), 0.9, 1.6))
    img.alpha_composite(rim(-4, 5, (140, 170, 255), 0.7, 1.4))
    return img


def rain_on_window(img, t, rect, density=110, col=(190, 205, 255)):
    x0, y0, x1, y1 = rect
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(1)
    for i in range(density):
        sx = rng.uniform(x0 - 100, x1)
        sp = rng.uniform(900, 1500)
        ph = rng.uniform(0, 1)
        ln = rng.uniform(26, 60)
        y = y0 + ((t * sp / (y1 - y0) + ph) % 1.0) * (y1 - y0 + 80) - 40
        x = sx + (y - y0) * 0.18
        d.line((x, y, x + ln * 0.18, y + ln), fill=col + (rng.randint(60, 130),), width=2)
    # droplets on the glass
    rng2 = random.Random(2)
    for i in range(46):
        dx = rng2.uniform(x0 + 10, x1 - 10)
        base_y = rng2.uniform(y0 + 10, y1 - 10)
        slide = ((t * rng2.uniform(10, 50) + rng2.uniform(0, 200)) % 300) if rng2.random() < 0.3 else 0
        dy = min(y1 - 8, base_y + slide)
        r = rng2.uniform(2, 5)
        d.ellipse((dx - r, dy - r, dx + r, dy + r * 1.2), fill=(220, 230, 255, 120))
        d.ellipse((dx - r * 0.4, dy - r * 0.6, dx, dy - r * 0.1), fill=(255, 255, 255, 190))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle(rect, fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    img.alpha_composite(layer)


def draw_clock(img, t, cx, cy, r):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=(70, 46, 40, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(236, 226, 206, 255))
    for k in range(12):
        a = k / 12 * math.pi * 2
        d.line((cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8, cx + math.cos(a) * r * 0.92,
                cy + math.sin(a) * r * 0.92), fill=(60, 40, 40, 255), width=3)
    # time races forward: waiting for a long, long time
    speed = 1 + 30 * ss(11.1, 12.6, t)
    ang = (t - 10.5) * speed * 0.9
    mh = ang
    hh = ang / 12
    for a, ln, wd in ((mh, 0.78, 4), (hh, 0.5, 7)):
        aa = a - math.pi / 2
        d.line((cx, cy, cx + math.cos(aa) * r * ln, cy + math.sin(aa) * r * ln), fill=(40, 26, 30, 255), width=wd)
    d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(190, 40, 60, 255))


MONTHS = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES"]


def calendar_page(year, month):
    return _calendar_page(year, month)


@lru_cache(maxsize=None)
def _calendar_page(year, month):
    w, h = 170, 210
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, h), fill=(246, 240, 228, 255))
    d.rectangle((0, 0, w, 58), fill=(200, 36, 58, 255))
    f = font("DelaGothic.ttf", 30)
    d.text((w / 2, 30), str(year), font=f, fill=(255, 250, 240, 255), anchor="mm")
    f2 = font("DelaGothic.ttf", 56)
    d.text((w / 2, 118), MONTHS[month], font=f2, fill=(40, 30, 50, 255), anchor="mm")
    f3 = font("Cormorant.ttf", 22)
    for k in range(4):
        d.line((20, 160 + k * 11, w - 20, 160 + k * 11), fill=(180, 170, 160, 255), width=1)
    d.text((w / 2, 196), "doa & rindu", font=f3, fill=(160, 60, 70, 255), anchor="mm")
    for x in (40, w - 40):
        d.ellipse((x - 6, -6, x + 6, 6), fill=(60, 60, 70, 255))
    return img


def draw_calendar(img, t, x, y):
    # pages flip from JAN 2023 onwards, accelerating: three years of waiting
    p = ss(11.0, 14.3, t) ** 1.3
    idx = int(p * 38)
    cur = (2023 + (idx // 12), idx % 12)
    nxt = (2023 + ((idx + 1) // 12), (idx + 1) % 12)
    paste(img, calendar_page(*nxt), x, y, 1.0)
    frac = (p * 38) % 1.0 if 0 < p < 1 else 0
    page = calendar_page(*cur)
    if frac > 0.02:
        fall = frac
        pg = page.rotate(-fall * 50, resample=Image.BICUBIC, expand=True)
        pg = pg.resize((pg.width, max(1, int(pg.height * (1 - fall * 0.5)))), Image.BILINEAR)
        paste(img, pg, x + fall * 160, y + fall * fall * 380, 1 - fall)
    else:
        paste(img, page, x, y, 1.0)


def scene_room(t):
    u = clamp((t - T_ROOM) / (T_DESK - T_ROOM))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    city = city_night()
    x0, y0, x1, y1 = WIN
    img.alpha_composite(city, (x0 - 100 + int(u * 40), y0 - 20))
    rain_on_window(img, t, WIN)
    img.alpha_composite(room_static())
    # curtains swaying
    cur = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cur)
    sway = math.sin(t * 1.3) * 12
    for side, xa in ((0, x0 - 40), (1, x1 - 120)):
        pts = []
        for k in range(0, 21):
            yy = y0 - 30 + k * (y1 - y0 + 80) / 20
            off = math.sin(k * 0.8 + t * 1.3) * 10 + sway * (k / 20)
            pts.append((xa + off + (160 if side else 0) * 0, yy))
        right = [(x + 160 + math.sin(i * 1.1 + t) * 8, y) for i, (x, y) in enumerate(reversed(pts))]
        cd.polygon(pts + right, fill=(120, 52, 72, 235))
        for k in range(5):
            xx = xa + 20 + k * 30
            cd.line((xx + sway * 0.3, y0 - 30, xx + sway, y1 + 50), fill=(90, 36, 56, 200), width=6)
    img.alpha_composite(cur)
    draw_clock(img, t, 520, 330, 70)
    draw_calendar(img, t, 520, 590)
    # desk items: lamp, papers, crumpled balls
    d = ImageDraw.Draw(img)
    d.polygon([(860, 700), (960, 700), (930, 690), (890, 690)], fill=(40, 30, 40, 255))
    d.line((910, 690, 950, 560), fill=(40, 30, 40, 255), width=8)
    d.line((950, 560, 1010, 520), fill=(40, 30, 40, 255), width=8)
    d.polygon([(980, 500), (1070, 540), (1040, 580), (960, 540)], fill=(210, 60, 70, 255))
    for (bx, by, r) in [(1560, 690, 22), (1620, 700, 16), (1700, 688, 24)]:
        d.polygon([(bx + math.cos(a) * r * (0.8 + 0.3 * math.sin(a * 5)), by + math.sin(a) * r * (0.7 + 0.3 * math.cos(a * 3)))
                   for a in np.linspace(0, 6.28, 12)], fill=(210, 200, 186, 255))
    d.polygon([(1120, 704), (1400, 704), (1390, 690), (1130, 690)], fill=(236, 230, 214, 255))
    img.alpha_composite(boy_sprite(), (1000, 360))
    # lamp glow cone
    cone = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(cone).polygon([(1010, 560), (1070, 555), (1420, 720), (840, 740)], fill=(255, 190, 110, 60))
    img = screen_add(img, blur(cone, 20), 1)
    img = screen_add(img, glow_layer(W, H, 1030, 560, 520, (255, 170, 90), 0.55, 2.0), 1)
    img = screen_add(img, glow_layer(W, H, (x0 + x1) / 2, (y0 + y1) / 2, 700, (90, 110, 220), 0.25, 2), 1)
    # floating dust motes in the lamp light
    rng = random.Random(33)
    for i in range(40):
        mx = 900 + rng.uniform(0, 600) + math.sin(t * 0.6 + i) * 20
        my = 480 + rng.uniform(0, 280) + math.cos(t * 0.5 + i * 2) * 20
        a = 0.3 + 0.3 * math.sin(t * 2 + i)
        paste(img, sparkle_sprite(10), mx, my, a)
    return camera(img, zoom=1.02 + u * 0.08, cx=1200, cy=560)


# ----------------------------------------------------------------------------
# SCENE C2: close-up of the song sheet on the desk (14.75 - 19.35 s)
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def desk_topdown():
    rng = np.random.default_rng(4)
    base = vgrad(W, H, [(0, (74, 44, 34)), (1, (52, 30, 26))])
    arr = np.asarray(base, np.float32)
    xs = np.arange(W)[None, :]
    ys = np.arange(H)[:, None]
    grain = np.sin(ys / 9 + np.sin(xs / 190) * 3 + np.sin(xs / 43) * 0.6) * 10
    arr[..., :3] += grain[..., None] * np.array([1, 0.7, 0.5])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    # crumpled drafts
    rng2 = random.Random(9)
    for (bx, by, r) in [(230, 250, 70), (320, 860, 60), (1720, 180, 58), (1640, 900, 76), (180, 560, 50)]:
        pts = [(bx + math.cos(a) * r * rng2.uniform(0.75, 1.1), by + math.sin(a) * r * rng2.uniform(0.75, 1.1))
               for a in np.linspace(0, 6.28, 16)]
        d.polygon(pts, fill=(222, 214, 196, 255))
        for k in range(5):
            a = rng2.uniform(0, 6.28)
            d.line((bx, by, bx + math.cos(a) * r * 0.9, by + math.sin(a) * r * 0.9), fill=(180, 170, 150, 255), width=3)
    # rosary (rosario) coiled on the desk
    beads = []
    for k in range(59):
        a = k / 59 * math.pi * 2
        beads.append((1540 + math.cos(a) * 150 + math.sin(a * 3) * 12, 640 + math.sin(a) * 100))
    for (x, y) in beads:
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(150, 110, 170, 255))
        d.ellipse((x - 3, y - 5, x, y - 2), fill=(230, 210, 240, 255))
    tail_x, tail_y = 1540, 740
    for k in range(6):
        y = tail_y + k * 18
        d.ellipse((tail_x - 7, y - 7, tail_x + 7, y + 7), fill=(150, 110, 170, 255))
    d.rectangle((tail_x - 5, tail_y + 110, tail_x + 5, tail_y + 190), fill=(212, 176, 100, 255))
    d.rectangle((tail_x - 28, tail_y + 128, tail_x + 28, tail_y + 138), fill=(212, 176, 100, 255))
    # coffee cup (kopi) top view
    d.ellipse((1480, 150, 1680, 350), fill=(236, 232, 224, 255))
    d.ellipse((1500, 170, 1660, 330), fill=(70, 38, 22, 255))
    d.ellipse((1530, 190, 1580, 220), fill=(120, 70, 44, 255))
    d.rounded_rectangle((1670, 225, 1740, 275), radius=20, fill=(236, 232, 224, 255))
    return img


@lru_cache(maxsize=None)
def paper_sheet():
    w, h = 1060, 820
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((14, 18, w, h), fill=(0, 0, 0, 90))
    d.rectangle((0, 0, w - 14, h - 18), fill=(246, 238, 220, 255))
    for y in range(120, h - 30, 36):
        d.line((30, y, w - 44, y), fill=(190, 200, 220, 255), width=1)
    d.line((90, 0, 90, h - 18), fill=(230, 150, 150, 255), width=2)
    return blur(img, 0.4)


def scene_desk(t):
    u = clamp((t - T_DESK) / (T_ROOF - T_DESK))
    img = desk_topdown().copy()
    paper = paper_sheet().copy()
    pd = ImageDraw.Draw(paper)
    # music staves being written with notes as the line progresses
    staff_y = [360, 560]
    ink = (40, 44, 90, 255)
    prog = ss(15.0, 19.2, t)
    for si, sy in enumerate(staff_y):
        for k in range(5):
            pd.line((120, sy + k * 14, 980, sy + k * 14), fill=(90, 90, 120, 255), width=2)
        # hand-drawn treble-ish clef
        pd.arc((128, sy - 8, 160, sy + 60), 0, 360, fill=ink, width=3)
        pd.line((150, sy - 26, 150, sy + 76), fill=ink, width=3)
        rng = random.Random(40 + si)
        n_notes = 16
        for k in range(n_notes):
            np_ = (si * n_notes + k + 1) / (2 * n_notes)
            if np_ > prog:
                break
            nx = 200 + k * 48
            ny = sy + 56 - rng.randint(0, 8) * 7
            pd.ellipse((nx - 9, ny - 7, nx + 9, ny + 7), fill=ink)
            pd.line((nx + 8, ny, nx + 8, ny - 46), fill=ink, width=3)
            if k % 2 == 0:
                pd.line((nx + 8, ny - 46, nx + 56, ny - 46 - rng.randint(-2, 2) * 4), fill=ink, width=5)
    # title of the song, already written
    spr, (ax, ay) = text_sprite("untukmu,", "Caveat.ttf", 58, (160, 40, 60), weight=700)
    paste(paper, spr, 110 - ax + 30, 44 - ay, 1.0, center=False)
    # the lyric being handwritten on the page in sync with the vocal
    lyric_layer = Image.new("RGBA", paper.size, (0, 0, 0, 0))
    tip = draw_write_on(lyric_layer, V1_L2, t, paper.width / 2 + 40, 200, "Caveat.ttf", 88, (30, 34, 80),
                        (80, 90, 180), glow=0, weight=600)
    paper.alpha_composite(lyric_layer)
    # notes lift off the page at the end of the line
    rot = -4 + u * 2
    pr = paper.rotate(rot, resample=Image.BICUBIC, expand=True)
    px, py = W / 2 - pr.width / 2 + 20, H / 2 - pr.height / 2 + 10
    img.alpha_composite(pr, (int(px), int(py)))
    # pen following the writing tip
    if tip is None:
        tip = (paper.width - 120, 260) if t > 16 else (160, 210)
    ang = math.radians(-rot)
    tx, ty = tip[0] - paper.width / 2, tip[1] - paper.height / 2
    sx = W / 2 + 20 + tx * math.cos(ang) - ty * math.sin(ang)
    sy = H / 2 + 10 + tx * math.sin(ang) + ty * math.cos(ang)
    wob = math.sin(t * 22) * 3
    pen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pdr = ImageDraw.Draw(pen)
    ex, ey = sx + 260, sy + 330
    pdr.line((sx + 30 + 16, sy + 26 + 16, ex + 16, ey + 16), fill=(0, 0, 0, 80), width=34)
    pdr.line((sx + 30, sy + 26 + wob, ex, ey), fill=(24, 26, 40, 255), width=28)
    pdr.line((sx + 24, sy + 14 + wob, ex - 6, ey - 12), fill=(90, 96, 140, 255), width=4)
    pdr.polygon([(sx, sy + wob), (sx + 40, sy + 18 + wob), (sx + 22, sy + 40 + wob)], fill=(212, 176, 100, 255))
    img.alpha_composite(pen)
    # lamp pool of light
    img = screen_add(img, glow_layer(W, H, 820, 380, 1100, (255, 176, 96), 0.38, 1.6), 1)
    # steam from the coffee
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(steam)
    for k in range(3):
        pts = [(1580 + k * 20 + math.sin(t * 2 + j * 0.5 + k) * 18, 250 - j * 14) for j in range(14)]
        sd.line(pts, fill=(255, 240, 220, 70), width=10)
    img.alpha_composite(blur(steam, 6))
    # finished line: notes and sparkles float up from the page
    if t > 18.6:
        rng = random.Random(90)
        for i in range(22):
            born = 18.6 + i * 0.03
            p = clamp((t - born) / 1.2)
            if p <= 0:
                continue
            nx = 560 + rng.uniform(0, 800)
            ny = 700 - rng.uniform(0, 300) - ease_out_cubic(p) * 420
            spr = note_sprite(i % 2, int(rng.uniform(36, 60)))
            paste(img, spr, nx + math.sin(p * 6 + i) * 20, ny, clamp(p * 4) * (1 - ss(0.8, 1, p) * 0.3))
    return camera(img, zoom=1.12 - u * 0.06 + ss(18.7, 19.35, t) * 0.25, cx=W / 2, cy=H / 2,
                  rot=math.sin(t * 0.3) * 0.8)


# ----------------------------------------------------------------------------
# SCENE D: notes fly over kampung roofs toward a church at dawn (19.35 - 30 s)
# ----------------------------------------------------------------------------
PAN_W = 3400


@lru_cache(maxsize=None)
def roofs_layers():
    L = {}
    rng = random.Random(21)
    # far hill + church (right end of the panorama)
    def far(d, s):
        pts = [(0, 760)]
        for x in range(0, PAN_W + 40, 40):
            y = 760 - 90 * math.exp(-((x - 1960) / 420) ** 2) + math.sin(x / 300) * 14
            pts.append((x, y))
        pts += [(PAN_W, H), (0, H)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=(40, 34, 78, 255))
    L["far"] = ss_draw(PAN_W, H, far)
    L["church"] = church_sprite()

    # kampung rooftops (genteng), water towers (toren), tangled cables
    def roofs(d, s, base, col, lit, seed, scale):
        r = random.Random(seed)
        x = -60
        windows = []
        while x < PAN_W:
            bw = r.uniform(160, 300) * scale
            bh = r.uniform(60, 150) * scale
            top = base - bh
            roof_h = r.uniform(50, 90) * scale
            d.rectangle(((x) * s, top * s, (x + bw) * s, H * s), fill=col)
            # pitched genteng roof with tiles
            rc = (int(col[0] * 1.6 + 24), int(col[1] * 1.1 + 6), int(col[2] * 0.9), 255)
            d.polygon([((x - 14) * s, top * s), ((x + bw / 2) * s, (top - roof_h) * s), ((x + bw + 14) * s, top * s)], fill=rc)
            for k in range(1, 5):
                yy = top - roof_h * k / 5
                half = (bw / 2 + 14) * (1 - k / 5)
                d.line(((x + bw / 2 - half) * s, yy * s, (x + bw / 2 + half) * s, yy * s), fill=(rc[0] - 20, rc[1] - 10, rc[2] - 6, 255), width=int(2 * s))
            # moonlit ridge
            d.line(((x - 14) * s, top * s, (x + bw / 2) * s, (top - roof_h) * s), fill=(150, 150, 210, 200), width=int(3 * s))
            if r.random() < 0.35:
                tx = x + r.uniform(20, bw - 60)
                d.rectangle((tx * s, (top - roof_h * 0.4 - 50 * scale) * s, (tx + 40 * scale) * s, (top - roof_h * 0.4) * s), fill=(70, 80, 120, 255))
                d.line((tx * s, (top - roof_h * 0.4) * s, (tx - 6) * s, (top - roof_h * 0.4 + 30 * scale) * s), fill=col, width=int(3 * s))
            if r.random() < 0.3:
                ax_ = x + r.uniform(30, bw - 30)
                d.line((ax_ * s, (top - roof_h * 0.6) * s, ax_ * s, (top - roof_h * 0.6 - 60 * scale) * s), fill=col, width=int(3 * s))
                for q in range(3):
                    d.line(((ax_ - 20 + q * 4) * s, (top - roof_h * 0.6 - 50 * scale + q * 10) * s,
                            (ax_ + 20 - q * 4) * s, (top - roof_h * 0.6 - 50 * scale + q * 10) * s), fill=col, width=int(2 * s))
            for wy in np.arange(top + 22 * scale, H, 70 * scale):
                for wx in np.arange(x + 24 * scale, x + bw - 40 * scale, 70 * scale):
                    windows.append((wx, wy, 30 * scale, 36 * scale, r.random() < lit))
            x += bw + r.uniform(-10, 20)
        for (wx, wy, ww, wh, on) in windows:
            c = (255, 206, 130, 255) if on else (col[0] + 10, col[1] + 12, col[2] + 22, 255)
            d.rectangle((wx * s, wy * s, (wx + ww) * s, (wy + wh) * s), fill=c)
            if on:
                d.line(((wx + ww / 2) * s, wy * s, (wx + ww / 2) * s, (wy + wh) * s), fill=(160, 110, 70, 255), width=int(2 * s))
    L["roofs_mid"] = ss_draw(PAN_W, H, lambda d, s: roofs(d, s, 850, (34, 30, 64, 255), 0.05, 5, 0.8), scale=1)
    L["roofs_near"] = ss_draw(PAN_W, H, lambda d, s: roofs(d, s, 1000, (20, 18, 42, 255), 0.03, 6, 1.25), scale=1)

    def cables(d, s):
        poles = [(x, r) for x, r in [(260, 0), (1150, 0), (2050, 0), (2950, 0)]]
        for (px, _) in poles:
            d.rectangle(((px - 7) * s, 340 * s, (px + 7) * s, H * s), fill=(16, 14, 32, 255))
            d.rectangle(((px - 60) * s, 380 * s, (px + 60) * s, 390 * s), fill=(16, 14, 32, 255))
            d.rectangle(((px - 40) * s, 420 * s, (px + 40) * s, 428 * s), fill=(16, 14, 32, 255))
            d.rounded_rectangle(((px - 22) * s, 470 * s, (px + 22) * s, 520 * s), radius=6 * s, fill=(26, 24, 46, 255))
        for i in range(len(poles) - 1):
            a, b = poles[i][0], poles[i + 1][0]
            for k, (y0, sag) in enumerate([(384, 90), (384, 120), (424, 80), (424, 140), (470, 160), (386, 60)]):
                off = (k - 2) * 18
                pts = []
                for j in range(41):
                    u = j / 40
                    x = lerp(a + off * 0.3, b + off * 0.3, u)
                    y = y0 + sag * 4 * u * (1 - u)
                    pts.append((x * s, y * s))
                d.line(pts, fill=(16, 14, 32, 255), width=int(2.4 * s))
    L["cables"] = ss_draw(PAN_W, H, cables, scale=1)
    # the boy's window (origin of the notes), on the near layer
    return L


@lru_cache(maxsize=None)
def church_sprite():
    """A small hilltop church with a bell tower and a glowing cross."""
    w, h = 360, 380
    def fn(d, s):
        S = lambda pts: [(x * s, y * s) for x, y in pts]
        col = (26, 22, 52, 255)
        d.polygon(S([(60, 380), (60, 230), (160, 150), (260, 230), (260, 380)]), fill=col)
        d.rectangle(S([(220, 130), (300, 380)]), fill=col)
        d.polygon(S([(212, 134), (260, 50), (308, 134)]), fill=col)
        d.rectangle(S([(256, 6), (264, 52)]), fill=(255, 226, 150, 255))
        d.rectangle(S([(244, 18), (276, 26)]), fill=(255, 226, 150, 255))
        for x0 in (90, 140, 190):
            d.rounded_rectangle(S([(x0, 260), (x0 + 24, 320)]), radius=12 * s, fill=(255, 196, 110, 255))
        d.ellipse(S([(144, 186), (176, 218)]), fill=(255, 210, 130, 255))
        d.rounded_rectangle(S([(246, 170), (274, 220)]), radius=14 * s, fill=(255, 196, 110, 255))
    img = ss_draw(w, h, fn)
    g = blur(img, 10)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(img)
    return out


def dawn_sky(t):
    k = ss(22.5, 29.5, t)
    top = mix_rgb((14, 16, 48), (40, 44, 110), k)
    mid = mix_rgb((34, 30, 84), (130, 88, 160), k)
    low = mix_rgb((60, 44, 100), (255, 170, 150), k)
    hor = mix_rgb((80, 54, 110), (255, 222, 180), k)
    return vgrad(W, H, [(0, top), (0.4, mid), (0.66, low), (0.8, hor), (1, hor)])


def pan_x(t):
    u = ease_in_out((t - T_ROOF) / (T_END + 0.5 - T_ROOF))
    return u * (PAN_W - W) * 1.0


def note_path(t, i, rng_vals, pan, cam_church):
    born, life, sy, amp, ph, kind, sz = rng_vals
    p = (t - born) / life
    if p <= 0 or p >= 1:
        return None
    win_x, win_y = 230 - pan * 1.25, 690
    cx, cy = cam_church
    mx = lerp(win_x, cx, 0.45)
    my = min(win_y, cy) - 280 + sy
    q = ease_in_out(p) * 0.3 + p * 0.7
    x = (1 - q) ** 2 * win_x + 2 * (1 - q) * q * mx + q * q * cx
    y = (1 - q) ** 2 * win_y + 2 * (1 - q) * q * my + q * q * cy
    x += math.sin(p * 9 + ph) * amp
    y += math.cos(p * 7 + ph) * amp * 0.6
    return x, y, p


def scene_roofs(t):
    L = roofs_layers()
    pan = pan_x(t)
    img = dawn_sky(t)
    # stars fading as dawn arrives
    d = ImageDraw.Draw(img)
    rng = random.Random(77)
    star_a = 1 - ss(24, 29, t)
    for _ in range(140):
        sx, sy = rng.uniform(0, W), rng.uniform(0, H * 0.55)
        tw = 0.5 + 0.5 * math.sin(t * rng.uniform(2, 5) + rng.uniform(0, 6))
        d.ellipse((sx - 1.3, sy - 1.3, sx + 1.3, sy + 1.3), fill=(255, 255, 255, int(200 * tw * star_a)))
    # big moon setting on the left
    mxp, myp = 250 - pan * 0.1, 340 + (t - T_ROOF) * 8
    img = screen_add(img, glow_layer(W, H, mxp, myp, 380, (170, 180, 255), 0.5 * (1 - 0.5 * ss(25, 29, t)), 2), 1)
    d = ImageDraw.Draw(img)
    d.ellipse((mxp - 120, myp - 120, mxp + 120, myp + 120), fill=(246, 244, 230, 255))
    for (cx_, cy_, r_) in [(-30, -20, 30), (40, 30, 20), (10, 60, 14), (-60, 40, 16)]:
        d.ellipse((mxp + cx_ - r_, myp + cy_ - r_, mxp + cx_ + r_, myp + cy_ + r_), fill=(226, 224, 214, 255))
    # dawn glow behind the church hill
    church_wx = 1960
    cam_church = (church_wx - pan * 0.45, 600)
    k = ss(23.5, 29.5, t)
    img = screen_add(img, glow_layer(W, H, cam_church[0], 720, 1300, (255, 180, 130), 0.2 + 0.5 * k, 2.2, sy=0.45), 1)
    paste(img, L["far"], -pan * 0.45, 0, 1.0, center=False)
    ch = L["church"]
    paste(img, ch, cam_church[0], 668 - ch.height / 2 + 12, 1.0)
    img = screen_add(img, glow_layer(W, H, cam_church[0] + 80, 480, 160, (255, 220, 150), 0.4 + 0.6 * k, 2), 1)
    paste(img, L["roofs_mid"], -pan * 0.75, 0, 1.0, center=False)
    paste(img, L["cables"], -pan * 1.0, 0, 1.0, center=False)

    # particle stream: notes that become kamboja petals as the meaning "lands"
    rng = random.Random(55)
    stream = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    petal_mix = ss(23.6, 25.2, t)
    for i in range(150):
        born = T_ROOF - 0.4 + i * 0.07
        vals = (born, rng.uniform(4.5, 6.5), rng.uniform(-160, 160), rng.uniform(20, 80), rng.uniform(0, 6.28),
                rng.randint(0, 1), rng.uniform(34, 64))
        pos = note_path(t, i, vals, pan, cam_church)
        if pos is None:
            continue
        x, y, p = pos
        a = clamp(p * 6) * (1 - ss(0.88, 1.0, p))
        m = clamp(petal_mix + (p - 0.5) * 0.8 * petal_mix)
        if m < 0.99:
            paste(stream, note_sprite(vals[5], int(vals[6])), x, y, a * (1 - m))
        if m > 0.01:
            ang = int(((t * 120 + i * 37) % 360) / 10) % 36
            paste(stream, kamboja_rot(int(vals[6] * 0.8), ang, i % 3 == 0), x, y, a * m)
    img.alpha_composite(stream)

    # the swirl around the church on "perasaanku"
    sw = ss(27.6, 28.4, t)
    if sw > 0:
        for i in range(40):
            a0 = i / 40 * math.pi * 2 + (t - 27.6) * 2.2
            rr = lerp(420, 150, ease_out_cubic((t - 27.6) / 2.0)) * (0.8 + 0.2 * math.sin(i * 3))
            x = cam_church[0] + math.cos(a0) * rr
            y = 520 + math.sin(a0) * rr * 0.45
            ang = int(((t * 200 + i * 30) % 360) / 10) % 36
            paste(img, kamboja_rot(34 + (i % 3) * 8, ang, i % 2), x, y, sw * 0.95)
    paste(img, L["roofs_near"], -pan * 1.25, 0, 1.0, center=False)
    # the boy's lit window on the near roofs where the song comes from
    wx = 170 - pan * 1.25
    if wx > -300:
        dd = ImageDraw.Draw(img)
        dd.rectangle((wx, 640, wx + 150, 760), fill=(255, 200, 120, 255))
        dd.line((wx + 75, 640, wx + 75, 760), fill=(120, 70, 50, 255), width=5)
        dd.line((wx, 700, wx + 150, 700), fill=(120, 70, 50, 255), width=5)
        img = screen_add(img, glow_layer(W, H, wx + 75, 700, 260, (255, 180, 100), 0.6, 2), 1)
    # final bloom into white-gold
    fl = ss(28.6, 30.0, t)
    if fl > 0:
        img = screen_add(img, glow_layer(W, H, cam_church[0] + 80, 480, 1600 * (0.4 + fl), (255, 236, 200), fl * 1.4, 1.2), 1)
    return img


# ----------------------------------------------------------------------------
# lyrics layer per time
# ----------------------------------------------------------------------------
def lyrics_layer(img, t):
    if t < 5.0:
        draw_lyric(img, INTRO_1[:4], t, 140, 380, "CormorantItalic.ttf", 92, color=(50, 20, 14), hi=(130, 30, 24),
                   glow=0, weight=600, out_t=4.55)
        draw_lyric(img, INTRO_1[4:], t, 140, 500, "CormorantItalic.ttf", 92, color=(50, 20, 14), hi=(130, 30, 24),
                   glow=0, weight=600, out_t=4.55)
    if 5.2 < t < 7.9:
        draw_write_on(img, INTRO_2, t, W / 2, 470, "Caveat.ttf", 150, (255, 250, 240), (255, 140, 120), glow=14,
                      weight=600) if t < 7.55 else _fade_write(img, t)
    if T_ROOM < t < T_DESK + 0.2:
        draw_lyric(img, V1_L1, t, 120, 930, "PlayfairItalic.ttf", 104, color=(240, 244, 255), hi=(255, 206, 120),
                   glow=14, glow_color=(90, 120, 255), weight=600, out_t=14.35)
    if T_ROOF < t < 24.2:
        draw_lyric(img, V1_L3, t, W / 2, 150, "PlayfairItalic.ttf", 96, align="center", color=(240, 244, 255),
                   hi=(255, 214, 140), glow=14, glow_color=(110, 130, 255), weight=600, out_t=23.55, style="drop")
    if 23.4 < t < 30:
        draw_lyric(img, V1_L4a, t, W / 2, 130, "PlayfairItalic.ttf", 92, align="center", color=(255, 250, 244),
                   hi=(255, 206, 120), glow=14, glow_color=(255, 140, 150), weight=600, out_t=29.3)
        draw_lyric(img, V1_L4b, t, W / 2, 250, "Playfair.ttf", 120, align="center", color=(255, 250, 244),
                   hi=(255, 196, 110), glow=20, glow_color=(255, 130, 150), weight=800, out_t=29.4, style="drop")


def _fade_write(img, t):
    a = 1 - ss(7.55, 7.85, t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_write_on(layer, INTRO_2, 7.55, W / 2, 470 - (t - 7.55) * 120, "Caveat.ttf", 150, (255, 250, 240),
                  (255, 140, 120), glow=14, weight=600)
    paste(img, blur(layer, (1 - a) * 8), 0, 0, a, center=False)


# ----------------------------------------------------------------------------
# frame compositor
# ----------------------------------------------------------------------------
def flash(img, t, at, dur=0.35, col=(255, 250, 240), peak=0.9):
    k = 1 - abs(t - at) / dur
    if k <= 0:
        return img
    layer = Image.new("RGBA", (W, H), col + (int(255 * peak * k ** 1.5),))
    img.alpha_composite(layer)
    return img


def light_streak_wipe(img, t, at, dur=0.4):
    p = (t - (at - dur / 2)) / dur
    if not 0 < p < 1:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = lerp(-600, W + 600, ease_in_out(p))
    d.polygon([(x - 260, 0), (x + 60, 0), (x - 140, H), (x - 460, H)], fill=(255, 240, 220, 220))
    return screen_add(img, blur(layer, 40), 1.4)


def render_frame(t):
    img = compose(t)
    fade_in = ss(0.0, 0.9, t)
    grain = 1.3 if t < T_DUSK else 1.0
    return finish(img, t, vig=0.9, grain=grain, fade=fade_in)


def compose(t):
    if t < T_GATE:
        img, _ = scene_wayang(t)
    elif t < T_DUSK:
        a_img, info = scene_wayang(t)
        b_img = scene_dusk(t)
        mask = door_mask_for(t, info)
        img = Image.composite(b_img, a_img, mask)
        # warm light pouring out of the opening doors
        img = screen_add(img, Image.merge("RGBA", (Image.new("L", (W, H), 255), Image.new("L", (W, H), 220),
                                                   Image.new("L", (W, H), 170), blur(mask, 40))),
                         0.6 * (1 - ss(T_DUSK - 0.3, T_DUSK, t)))
    elif t < T_ROOM:
        img = draw_title(scene_dusk(t), t)
    elif t < T_DESK:
        img = scene_room(t)
    elif t < T_ROOF:
        img = scene_desk(t)
    else:
        img = scene_roofs(t)

    lyrics_layer(img, t)

    img = light_streak_wipe(img, t, T_ROOM, 0.5)
    img = flash(img, t, T_ROOM, 0.25, peak=0.7)
    img = flash(img, t, T_DESK, 0.18, col=(255, 220, 170), peak=0.55)
    img = flash(img, t, T_ROOF, 0.3, col=(255, 240, 200), peak=0.8)
    # beat pulse on the title card
    if 7.55 < t < 10.4:
        ph = ((t - 7.55) / BEAT) % 1.0
        img = screen_add(img, glow_layer(W, H, W / 2, 470, 900, (255, 160, 140), 0.18 * (1 - ph) ** 3, 2), 1)
    return img


def _worker(i):
    t = i / FPS
    return render_frame(t).tobytes()


def render_video(start, end, out_path, workers):
    os.makedirs(OUT, exist_ok=True)
    frames = list(range(int(start * FPS), int(end * FPS)))
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", str(start), "-t", str(end - start), "-i", AUDIO,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={end - start - 0.6}:d=0.6",
           "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for n, buf in enumerate(pool.imap(_worker, frames, chunksize=4)):
            proc.stdin.write(buf)
            if n % 60 == 0:
                print(f"frame {n}/{len(frames)}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=DURATION)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(OUT, "part1_0-30s.mp4"))
    a = ap.parse_args()
    if a.stills:
        os.makedirs(OUT, exist_ok=True)
        for t in a.stills:
            Image.fromarray(render_frame(t)).save(os.path.join(OUT, f"still_{t:05.2f}.png"))
            print("still", t)
        return
    render_video(a.start, a.end, a.out, a.workers)


if __name__ == "__main__":
    main()
