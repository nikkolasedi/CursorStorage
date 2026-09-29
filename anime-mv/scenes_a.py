"""Scenes for Verse 2, Pre-Chorus and Chorus 1 (30 s - 125 s)."""
import math
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt
from scipy.spatial import Delaunay, cKDTree

import cast as C
import render as R
from render import (W, H, clamp, lerp, ss, ease_out_back, ease_out_cubic, ease_in_out, vgrad, glow_layer,
                    screen_add, paste, ss_draw, blur, text_sprite, font, vfont, kamboja_rot, sparkle_sprite,
                    note_sprite, camera, mix_rgb)


def grey(img, amount=1.0):
    a = np.asarray(img, np.float32)
    g = a[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32)
    a[..., :3] = a[..., :3] * (1 - amount) + g[..., None] * amount
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def tint(img, rgb_mul, amount=1.0):
    a = np.asarray(img, np.float32)
    g = a[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32)
    toned = g[..., None] * np.array(rgb_mul, np.float32)
    a[..., :3] = a[..., :3] * (1 - amount) + toned * amount
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def label(img, text, x, y, fname, size, col, alpha=1.0, weight=None, glow=0, glow_color=None, stroke=0,
          stroke_color=(0, 0, 0), anchor="c", shadow=None):
    spr, (ax, ay) = text_sprite(text, fname, size, col, weight=weight, glow=glow, glow_color=glow_color,
                                stroke=stroke, stroke_color=stroke_color, shadow=shadow)
    if anchor == "c":
        paste(img, spr, x, y, alpha)
    else:
        paste(img, spr, x - ax, y - ay, alpha, center=False)
    return spr


def pop(t, t0, dur=0.35):
    return ease_out_back((t - t0) / dur, 2.0) if t > t0 else 0.0


def pop_paste(img, spr, x, y, t, t0, dur=0.35, alpha=1.0):
    k = pop(t, t0, dur)
    if k <= 0.01:
        return
    sp = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.BILINEAR)
    paste(img, sp, x, y, alpha * clamp((t - t0) / 0.12))


# ----------------------------------------------------------------------------
# 30.0 - 36.55  VHS flashback "sudah siap" -> God's hourglass
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def flash_room():
    img = vgrad(W, H, [(0, (236, 214, 190)), (1, (206, 170, 140))])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 820, W, H), fill=(150, 108, 84, 255))
    for x in range(0, W, 120):
        d.line((x, 820, x - 200, H), fill=(130, 92, 72, 255), width=3)
    # mirror
    d.ellipse((1180, 170, 1600, 760), fill=(120, 80, 60, 255))
    d.ellipse((1200, 190, 1580, 740), fill=(200, 222, 230, 255))
    for k in range(3):
        d.line((1260 + k * 40, 260, 1330 + k * 40, 330), fill=(245, 250, 255, 255), width=10)
    # wall calendar 2023
    d.rectangle((360, 160, 620, 460), fill=(250, 246, 236, 255))
    d.rectangle((360, 160, 620, 240), fill=(196, 40, 60, 255))
    d.text((490, 200), "2023", font=font("DelaGothic.ttf", 54), fill=(255, 250, 240, 255), anchor="mm")
    for r in range(4):
        for c in range(7):
            x, y = 380 + c * 34, 270 + r * 44
            d.rectangle((x, y, x + 24, y + 30), outline=(180, 160, 150, 255))
    d.ellipse((440 + 3 * 34 - 8, 270 + 2 * 44 - 8, 440 + 3 * 34 + 26, 270 + 2 * 44 + 38), outline=(200, 30, 50, 255), width=4)
    return img


def vhs(img, t, strength=1.0):
    a = np.asarray(img, np.float32).copy()
    rng = np.random.default_rng(int(t * 30))
    # chroma shift
    a[..., 0] = np.roll(a[..., 0], int(4 * strength), axis=1)
    a[..., 2] = np.roll(a[..., 2], -int(4 * strength), axis=1)
    # tracking bands
    for _ in range(2):
        y0 = int(rng.uniform(0, H - 40))
        a[y0:y0 + 26] = np.roll(a[y0:y0 + 26], int(rng.uniform(-30, 30) * strength), axis=1)
    band_y = int((t * 260) % (H + 200)) - 100
    lo, hi = max(0, band_y), min(H, band_y + 60)
    if hi > lo:
        a[lo:hi, :, :3] += 26 * strength
    a[::3, :, :3] *= 1 - 0.18 * strength
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def draw_hourglass(img, t, x, y, sc, prog):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    hw, hh = 170 * sc, 300 * sc
    wood = (120, 72, 36, 255)
    glass = (220, 240, 255, 90)
    d.polygon([(x - hw, y - hh), (x + hw, y - hh), (x + 14 * sc, y), (x + hw, y + hh), (x - hw, y + hh), (x - 14 * sc, y)], fill=glass)
    # sand top (shrinks) and bottom (grows)
    top_lvl = lerp(0.2, 0.98, prog)
    yt = y - hh + (hh - 10) * top_lvl
    wt = hw * (1 - top_lvl) * 0.95 + 14 * sc
    d.polygon([(x - wt, yt), (x + wt, yt), (x, y)], fill=(245, 200, 110, 255))
    mound = hh * 0.9 * prog
    d.polygon([(x - hw * 0.92, y + hh - 6), (x + hw * 0.92, y + hh - 6), (x + hw * 0.3, y + hh - mound),
               (x - hw * 0.3, y + hh - mound)], fill=(245, 200, 110, 255))
    if prog < 0.99:
        d.line((x, y, x, y + hh - mound), fill=(255, 214, 130, 255), width=int(6 * sc))
    for yy in (y - hh - 30 * sc, y + hh):
        d.rounded_rectangle((x - hw - 40 * sc, yy, x + hw + 40 * sc, yy + 30 * sc), radius=10 * sc, fill=wood)
    for xx in (x - hw - 20 * sc, x + hw + 10 * sc):
        d.rectangle((xx, y - hh, xx + 12 * sc, y + hh), fill=wood)
    d.line((x - hw * 0.7, y - hh * 0.9, x - hw * 0.3, y - hh * 0.4), fill=(255, 255, 255, 170), width=int(8 * sc))
    img.alpha_composite(layer)


def s_flashback(t):
    img = flash_room().copy()
    k = ss(33.9, 34.8, t)
    # the boy, proud and ready
    arm = 160 if 30.8 < t < 34.2 else 20
    eyes = "sparkle" if t < 33.9 else "open"
    mouth = "open" if 30.8 < t < 33.9 else ("o" if t > 34.2 else "smile")
    boy = C.chibi_scaled(1.25, "boy", eyes, mouth, 10, arm, True, False, 0)
    bob = abs(math.sin(t * 6)) * 12 if t < 33.9 else 0
    paste(img, boy, 800, 560 - bob)
    # reflection in the mirror
    ref = C.chibi_scaled(0.8, "boy", eyes, mouth, arm, 10, True, False, 0)
    ref = ref.transpose(Image.FLIP_LEFT_RIGHT)
    paste(img, ref, 1390, 520 - bob * 0.6, 0.55)
    if 30.8 < t < 34.1:
        bub = C.speech_bubble("SUDAH SIAP!", size=78, spiky=True)
        pop_paste(img, bub, 480, 250, t, 30.85)
        for i in range(6):
            a = i / 6 * math.pi * 2 + t * 2
            paste(img, sparkle_sprite(60), 800 + math.cos(a) * 280, 460 + math.sin(a) * 200, 0.8 * (0.5 + 0.5 * math.sin(t * 8 + i)))
    # heaven opens: rays + hourglass (Tuhan lebih tahu)
    if k > 0:
        rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rays)
        for i in range(9):
            xx = 700 + i * 70 + math.sin(t + i) * 20
            rd.polygon([(xx, -20), (xx + 50, -20), (xx + 180 - i * 30, H), (xx - 120 - i * 10, H)], fill=(255, 236, 170, 40))
        img = screen_add(img, blur(rays, 20), k)
        hy = lerp(-400, 380, ease_out_cubic((t - 34.0) / 1.2))
        prog = clamp((t - 34.4) / 6.0)
        draw_hourglass(img, t, 960, hy, 0.95, prog)
        img = screen_add(img, glow_layer(W, H, 960, hy, 500, (255, 220, 150), 0.5 * k, 2), 1)
    sep = 1 - 0.75 * k
    img = tint(img, (1.12, 0.95, 0.72), sep)
    img = vhs(img, t, 1 - k * 0.8)
    if t < 34.3:
        label(img, "PLAY \u25B6", 150, 90, "PressStart2P.ttf", 34, (255, 255, 255), 0.9, anchor="c")
        label(img, "SEP 2023", 1700, 1000, "PressStart2P.ttf", 34, (255, 230, 160), 0.9)
    return img


# ----------------------------------------------------------------------------
# 36.55 - 41.5  grey rain at the halte, an angkot passes
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def halte_bg():
    img = vgrad(W, H, [(0, (150, 158, 170)), (0.7, (190, 196, 204)), (1, (120, 126, 136))])
    d = ImageDraw.Draw(img)
    rng = random.Random(4)
    x = -50
    while x < W:
        bw, bh = rng.uniform(90, 200), rng.uniform(150, 420)
        d.rectangle((x, 700 - bh, x + bw, 760), fill=(170, 176, 188, 255))
        x += bw + rng.uniform(5, 30)
    d.rectangle((0, 760, W, H), fill=(96, 100, 110, 255))
    d.rectangle((0, 760, W, 790), fill=(140, 144, 152, 255))
    # halte shelter
    d.rectangle((520, 360, 1400, 392), fill=(70, 76, 90, 255))
    for px in (560, 1350):
        d.rectangle((px, 392, px + 18, 780), fill=(70, 76, 90, 255))
    d.rectangle((600, 640, 1320, 660), fill=(90, 96, 110, 255))
    for px in (640, 1270):
        d.rectangle((px, 660, px + 12, 760), fill=(90, 96, 110, 255))
    d.rectangle((1420, 280, 1440, 780), fill=(70, 76, 90, 255))
    d.rounded_rectangle((1370, 230, 1600, 310), radius=12, fill=(40, 90, 160, 255))
    d.text((1485, 270), "HALTE", font=font("DelaGothic.ttf", 44), fill=(255, 255, 255, 255), anchor="mm")
    return img


def draw_angkot(img, x, y, t):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x, y - 210, x + 560, y), radius=30, fill=(70, 150, 200, 255))
    d.polygon([(x, y - 60), (x - 40, y - 60), (x - 30, y - 150), (x + 40, y - 205)], fill=(70, 150, 200, 255))
    for k in range(4):
        d.rounded_rectangle((x + 30 + k * 124, y - 190, x + 134 + k * 124, y - 120), radius=10, fill=(200, 222, 236, 255))
    d.polygon([(x - 20, y - 130), (x + 20, y - 190), (x + 20, y - 130)], fill=(200, 222, 236, 255))
    d.rectangle((x, y - 100, x + 560, y - 80), fill=(240, 240, 240, 255))
    d.text((x + 280, y - 90), "M44  KAMPUNG MELAYU - SENEN", font=font("DelaGothic.ttf", 18), fill=(40, 60, 90, 255), anchor="mm")
    for wx in (x + 90, x + 460):
        d.ellipse((wx - 50, y - 50, wx + 50, y + 50), fill=(30, 30, 36, 255))
        d.ellipse((wx - 22, y - 22, wx + 22, y + 22), fill=(170, 170, 180, 255))
        a = t * 18
        d.line((wx + math.cos(a) * 20, y + math.sin(a) * 20, wx - math.cos(a) * 20, y - math.sin(a) * 20), fill=(90, 90, 100, 255), width=5)


def s_halte(t):
    img = halte_bg().copy()
    boy = C.chibi_scaled(0.9, "boy", "flat", "sad", 6, 6, False, False, 0)
    paste(img, boy, 960, 560 + math.sin(t * 1.5) * 3)
    # puddle ripples
    d = ImageDraw.Draw(img)
    rng = random.Random(8)
    for i in range(24):
        px, py = rng.uniform(0, W), rng.uniform(800, H)
        ph = (t * rng.uniform(0.8, 1.4) + rng.random()) % 1
        r = 8 + ph * 60
        d.ellipse((px - r, py - r * 0.3, px + r, py + r * 0.3), outline=(200, 206, 216, int(200 * (1 - ph))), width=2)
    # angkot drives past with a splash
    ax = lerp(W + 100, -800, clamp((t - 37.6) / 2.4))
    if -700 < ax < W + 90:
        draw_angkot(img, ax, 860, t)
        for i in range(30):
            sx = ax + 90 + rng.uniform(-40, 60)
            sy = 880 - rng.uniform(0, 140)
            d.ellipse((sx - 5, sy - 5, sx + 5, sy + 5), fill=(210, 220, 235, 200))
    img = grey(img, 0.85)
    # the only colour: his yellow umbrella leaning on the bench
    ud = ImageDraw.Draw(img)
    ux, uy = 1180, 640
    ud.line((ux, uy, ux + 60, uy - 250), fill=(60, 50, 40, 255), width=6)
    ud.polygon([(ux + 60, uy - 250), (ux + 20, uy - 90), (ux + 110, uy - 110)], fill=(250, 200, 50, 255))
    R.rain_on_window(img, t, (0, 0, W, H), density=260, col=(220, 226, 240))
    return img


# ----------------------------------------------------------------------------
# 41.5 - 46.9  routine grid: 1095 days of being used to it
# ----------------------------------------------------------------------------
def s_routine(t):
    img = vgrad(W, H, [(0, (40, 60, 70)), (1, (22, 34, 44))])
    d = ImageDraw.Draw(img)
    panels = [(80, 90, 930, 520), (990, 90, 1840, 520), (80, 560, 930, 990), (990, 560, 1840, 990)]
    cols = [(236, 222, 196), (220, 232, 222), (226, 222, 236), (214, 222, 236)]
    fade = ss(45.3, 46.6, t)
    for i, (x0, y0, x1, y1) in enumerate(panels):
        d.rounded_rectangle((x0, y0, x1, y1), radius=30, fill=cols[i] + (255,))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if i == 0:   # alarm clock shaking
            sh = math.sin(t * 60) * 8 if (t * 1.3) % 1 < 0.5 else 0
            d.ellipse((cx - 110 + sh, cy - 110, cx + 110 + sh, cy + 110), fill=(220, 70, 70, 255))
            d.ellipse((cx - 90 + sh, cy - 90, cx + 90 + sh, cy + 90), fill=(255, 250, 240, 255))
            for sg in (-1, 1):
                d.ellipse((cx + sg * 90 - 40 + sh, cy - 150, cx + sg * 90 + 40 + sh, cy - 90), fill=(220, 70, 70, 255))
            d.line((cx + sh, cy, cx + sh, cy - 70), fill=(40, 40, 40, 255), width=8)
            d.line((cx + sh, cy, cx + 50 + sh, cy + 20), fill=(40, 40, 40, 255), width=8)
            d.text((cx, y1 - 40), "06.00", font=font("PressStart2P.ttf", 30), fill=(90, 60, 60, 255), anchor="mm")
        elif i == 1:  # kopi with steam
            d.rounded_rectangle((cx - 100, cy - 60, cx + 100, cy + 120), radius=24, fill=(250, 250, 246, 255))
            d.ellipse((cx + 70, cy - 20, cx + 150, cy + 70), outline=(250, 250, 246, 255), width=18)
            d.ellipse((cx - 94, cy - 76, cx + 94, cy - 40), fill=(90, 50, 30, 255))
            for k in range(3):
                pts = [(cx - 40 + k * 40 + math.sin(t * 3 + j * 0.7 + k) * 14, cy - 90 - j * 14) for j in range(10)]
                d.line(pts, fill=(160, 170, 170, 255), width=8)
            d.text((cx, y1 - 40), "kopi", font=font("Caveat.ttf", 50), fill=(60, 80, 70, 255), anchor="mm")
        elif i == 2:  # laptop with code
            d.rounded_rectangle((cx - 190, cy - 140, cx + 190, cy + 90), radius=14, fill=(50, 54, 70, 255))
            d.rectangle((cx - 170, cy - 122, cx + 170, cy + 72), fill=(28, 32, 48, 255))
            n = int((t * 8) % 12)
            for k in range(n):
                ln = (k * 37) % 200 + 60
                d.rectangle((cx - 150 + (k % 3) * 20, cy - 110 + k * 15, cx - 150 + (k % 3) * 20 + ln, cy - 102 + k * 15),
                            fill=[(120, 200, 255, 255), (250, 200, 120, 255), (160, 240, 160, 255)][k % 3])
            d.polygon([(cx - 230, cy + 90), (cx + 230, cy + 90), (cx + 260, cy + 120), (cx - 260, cy + 120)], fill=(70, 74, 92, 255))
        else:  # bed, moon, zzz
            d.rounded_rectangle((cx - 230, cy + 10, cx + 230, cy + 110), radius=20, fill=(120, 130, 180, 255))
            d.rounded_rectangle((cx - 220, cy - 30, cx - 100, cy + 30), radius=20, fill=(250, 250, 255, 255))
            d.ellipse((cx + 120, cy - 170, cx + 200, cy - 90), fill=(255, 230, 150, 255))
            d.ellipse((cx + 140, cy - 184, cx + 220, cy - 104), fill=cols[3] + (255,))
            for k in range(3):
                zp = (t * 0.8 + k * 0.33) % 1
                d.text((cx - 60 + k * 30 + zp * 40, cy - 60 - zp * 120), "z", font=font("DelaGothic.ttf", 40 + k * 10),
                       fill=(80, 90, 140, int(255 * (1 - zp))), anchor="mm")
    img = grey(img, 0.6 * fade)
    # day counter over the grid
    days = int(1 + 1094 * ease_in_out(clamp((t - 41.6) / 4.2)))
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle((560, 430, 1360, 650), radius=40, fill=(20, 26, 36, 235), outline=(255, 214, 120, 255), width=5)
    img.alpha_composite(plate)
    label(img, "HARI KE-", 960, 480, "PressStart2P.ttf", 34, (255, 214, 120))
    label(img, f"{days:,}".replace(",", "."), 960, 580, "DelaGothic.ttf", 120, (255, 250, 240), glow=10, glow_color=(255, 160, 90))
    return img


# ----------------------------------------------------------------------------
# 46.9 - 51.55  stained glass: the missing rib
# ----------------------------------------------------------------------------
GL_X0, GL_Y0, GL_W, GL_H = 560, 40, 800, 1000


def arch_mask(w, h):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rectangle((0, h * 0.42, w, h), fill=255)
    d.pieslice((0, 0, w * 2, h * 0.84), 180, 270, fill=255)
    d.pieslice((-w, 0, w, h * 0.84), 270, 360, fill=255)
    return m


@lru_cache(maxsize=None)
def stained_window():
    w, h = GL_W, GL_H
    pic = vgrad(w, h, [(0, (40, 70, 170)), (0.5, (80, 130, 210)), (0.62, (250, 200, 90)), (1, (40, 120, 70))])
    d = ImageDraw.Draw(pic)
    # sun of God's love
    d.ellipse((w / 2 - 110, 150, w / 2 + 110, 370), fill=(255, 220, 90, 255))
    for k in range(12):
        a = k / 12 * math.pi * 2
        d.polygon([(w / 2 + math.cos(a) * 120, 260 + math.sin(a) * 120), (w / 2 + math.cos(a + 0.12) * 220, 260 + math.sin(a + 0.12) * 220),
                   (w / 2 + math.cos(a - 0.12) * 220, 260 + math.sin(a - 0.12) * 220)], fill=(255, 190, 70, 255))
    # garden hills and a tree
    d.polygon([(0, 700), (200, 620), (420, 690), (640, 610), (w, 680), (w, h), (0, h)], fill=(50, 150, 80, 255))
    d.rectangle((600, 470, 640, 700), fill=(120, 70, 40, 255))
    d.ellipse((520, 360, 720, 540), fill=(40, 170, 90, 255))
    for (fx, fy) in [(560, 420), (650, 400), (610, 480), (680, 460)]:
        d.ellipse((fx - 14, fy - 14, fx + 14, fy + 14), fill=(220, 50, 60, 255))
    # a man asleep in the garden
    d.ellipse((140, 760, 230, 840), fill=(240, 200, 160, 255))
    d.rounded_rectangle((210, 770, 520, 850), radius=40, fill=(220, 220, 240, 255))
    d.polygon([(250, 770), (300, 740), (420, 760), (480, 780)], fill=(220, 220, 240, 255))
    # voronoi glass cells: small brightness variation per pane
    rng = np.random.default_rng(3)
    pts = rng.uniform([0, 0], [w, h], (170, 2))
    yy, xx = np.mgrid[0:h, 0:w]
    tree = cKDTree(pts)
    _, lab = tree.query(np.stack([xx.ravel(), yy.ravel()], 1))
    lab = lab.reshape(h, w)
    var = rng.uniform(0.82, 1.15, len(pts))[lab]
    arr = np.asarray(pic, np.float32)
    arr[..., :3] *= var[..., None]
    edges = (lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))
    edges = np.asarray(Image.fromarray((edges * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), np.float32) / 255
    arr[..., :3] = arr[..., :3] * (1 - edges[..., None]) + 24 * edges[..., None]
    pic = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(pic)
    # thick leading around the figure
    d.ellipse((140, 760, 230, 840), outline=(24, 20, 24, 255), width=8)
    d.rounded_rectangle((210, 770, 520, 850), radius=40, outline=(24, 20, 24, 255), width=8)
    mask = arch_mask(w, h)
    pic.putalpha(mask)
    frame = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    fm = arch_mask(w + 60, h + 60)
    fr = Image.new("RGBA", fm.size, (60, 46, 50, 255))
    fr.putalpha(fm)
    frame.alpha_composite(fr)
    frame.alpha_composite(pic, (30, 30))
    return frame


@lru_cache(maxsize=None)
def rib_sprite():
    s = 2
    img = Image.new("RGBA", (360 * s, 200 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.arc((20 * s, 20 * s, 340 * s, 360 * s), 200, 340, fill=(255, 236, 170, 255), width=26 * s)
    d.arc((20 * s, 20 * s, 340 * s, 360 * s), 200, 340, fill=(24, 20, 24, 255), width=4 * s)
    img = img.resize((360, 200), Image.LANCZOS)
    g = blur(img, 16)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(g)
    out.alpha_composite(img)
    return out


def s_stained(t):
    img = vgrad(W, H, [(0, (20, 16, 30)), (1, (36, 26, 40))])
    dim = 1 - 0.45 * ss(49.5, 51.4, t)
    win = stained_window()
    beams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beams)
    for i, col in enumerate([(90, 140, 255), (255, 200, 90), (60, 200, 110), (255, 90, 90)]):
        x = GL_X0 + 120 + i * 180
        bd.polygon([(x, 500), (x + 140, 500), (x + 320 + i * 40, H), (x - 60 + i * 30, H)], fill=col + (46,))
    img = screen_add(img, blur(beams, 30), dim)
    img.alpha_composite(win, (GL_X0 - 30, GL_Y0 - 30))
    img = screen_add(img, glow_layer(W, H, W / 2, 400, 700, (255, 220, 170), 0.35 * dim, 2), 1)
    # the rib lifts from the sleeping man ... and is gone
    rib = rib_sprite()
    rise = ease_in_out((t - 47.3) / 1.6)
    ra = 1 - ss(48.5, 49.3, t)
    paste(img, rib, GL_X0 + 360, GL_Y0 + 760 - rise * 280, ra)
    # the empty space left where she should be
    if t > 48.7:
        e = ss(48.7, 49.6, t)
        d = ImageDraw.Draw(img)
        cx, cy = GL_X0 + 600, GL_Y0 + 800
        pts = []
        for i in range(60):
            a = i / 60 * math.pi * 2
            x = 16 * math.sin(a) ** 3
            y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
            pts.append((cx + x * 5, cy + y * 5))
        d.polygon(pts, fill=(18, 14, 20, int(255 * e)))
        d.line(pts + [pts[0]], fill=(255, 220, 150, int(180 * e * (0.6 + 0.4 * math.sin(t * 5)))), width=4)
    arr = np.asarray(img, np.float32)
    arr[..., :3] *= dim
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    # floating dust
    rng = random.Random(1)
    for i in range(30):
        paste(img, sparkle_sprite(12), rng.uniform(500, 1500) + math.sin(t + i) * 20, (rng.uniform(0, H) - t * 20) % H, 0.4)
    return camera(img, 1.0 + 0.05 * ss(46.9, 51.5, t), W / 2, H / 2)


# ----------------------------------------------------------------------------
# 51.55 - 61.9  phone feed: her photo at the church appears on my FYP
# ----------------------------------------------------------------------------
PH_W, PH_H = 560, 1000


def post_cat(d, w, h):
    d.rectangle((0, 0, w, h), fill=(90, 200, 190, 255))
    cx, cy = w / 2, h / 2
    d.ellipse((cx - 150, cy - 40, cx + 150, cy + 200), fill=(240, 150, 60, 255))
    d.ellipse((cx - 120, cy - 200, cx + 120, cy + 20), fill=(240, 150, 60, 255))
    for sg in (-1, 1):
        d.polygon([(cx + sg * 110, cy - 150), (cx + sg * 60, cy - 190), (cx + sg * 115, cy - 250)], fill=(240, 150, 60, 255))
        d.ellipse((cx + sg * 50 - 16, cy - 110, cx + sg * 50 + 16, cy - 70), fill=(40, 30, 30, 255))
    for k in range(3):
        d.line((cx - 40 + k * 40, cy - 200, cx - 30 + k * 30, cy - 160), fill=(200, 110, 40, 255), width=10)
    d.polygon([(cx - 12, cy - 60), (cx + 12, cy - 60), (cx, cy - 46)], fill=(250, 120, 140, 255))
    return "#kucingoren"


def post_nasgor(d, w, h):
    d.rectangle((0, 0, w, h), fill=(250, 214, 120, 255))
    cx, cy = w / 2, h / 2
    d.ellipse((cx - 220, cy - 120, cx + 220, cy + 160), fill=(250, 250, 250, 255))
    d.chord((cx - 160, cy - 110, cx + 160, cy + 130), 180, 360, fill=(200, 110, 50, 255))
    d.rectangle((cx - 160, cy + 8, cx + 160, cy + 20), fill=(200, 110, 50, 255))
    d.ellipse((cx - 70, cy - 120, cx + 70, cy - 40), fill=(255, 255, 250, 255))
    d.ellipse((cx - 26, cy - 100, cx + 26, cy - 60), fill=(255, 190, 40, 255))
    for k in range(8):
        d.ellipse((cx - 150 + k * 40, cy + 40, cx - 130 + k * 40, cy + 60), fill=(80, 170, 70, 255))
    return "#nasigoreng"


def post_macet(d, w, h):
    d.rectangle((0, 0, w, h), fill=(250, 150, 110, 255))
    d.rectangle((0, h * 0.35, w, h), fill=(80, 80, 90, 255))
    rng = random.Random(2)
    for r in range(5):
        for c in range(4):
            x = 30 + c * 130 + (r % 2) * 50
            y = h * 0.4 + r * 110
            col = rng.choice([(230, 60, 60), (60, 120, 220), (240, 240, 240), (250, 200, 60)])
            d.rounded_rectangle((x, y, x + 100, y + 70), radius=18, fill=col + (255,))
            d.ellipse((x + 70, y + 20, x + 96, y + 46), fill=(255, 60, 60, 255))
    return "#macetlagi"


def post_senja(d, w, h):
    for i in range(h):
        k = i / h
        d.line((0, i, w, i), fill=mix_rgb((120, 80, 200), (255, 170, 100), k) + (255,))
    d.ellipse((w / 2 - 90, h * 0.45 - 90, w / 2 + 90, h * 0.45 + 90), fill=(255, 240, 200, 255))
    d.rectangle((0, h * 0.6, w, h), fill=(60, 50, 110, 255))
    for k in range(6):
        d.line((w / 2 - 120 + k * 10, h * 0.62 + k * 30, w / 2 + 120 - k * 10, h * 0.62 + k * 30), fill=(255, 200, 150, 255), width=6)
    return "#senjakala"


def post_church(img, w, h):
    d = ImageDraw.Draw(img)
    for i in range(h):
        k = i / h
        d.line((0, i, w, i), fill=mix_rgb((150, 200, 255), (255, 236, 220), k) + (255,))
    # twin-spire church facade
    cx = w / 2
    d.rectangle((cx - 190, 280, cx + 190, 760), fill=(236, 230, 220, 255))
    for sx in (cx - 190, cx + 110):
        d.rectangle((sx, 200, sx + 80, 760), fill=(226, 220, 210, 255))
        d.polygon([(sx - 6, 200), (sx + 40, 60), (sx + 86, 200)], fill=(200, 190, 180, 255))
        d.line((sx + 40, 60, sx + 40, 20), fill=(200, 170, 90, 255), width=5)
        d.line((sx + 26, 36, sx + 54, 36), fill=(200, 170, 90, 255), width=5)
    d.ellipse((cx - 60, 320, cx + 60, 440), fill=(120, 150, 210, 255))
    d.rounded_rectangle((cx - 60, 560, cx + 60, 760), radius=60, fill=(120, 80, 60, 255))
    d.rectangle((0, 760, w, h), fill=(210, 200, 190, 255))
    girl = C.chibi_scaled(0.78, "girl", "happy", "smile", 10, 140, True, False, 0)
    img.alpha_composite(girl, (int(cx - girl.width / 2 + 60), 520))
    return "Minggu pagi, misa \u2728"


@lru_cache(maxsize=None)
def feed_strip():
    posts = [post_cat, post_nasgor, post_macet, post_senja, post_cat, post_church]
    strip = Image.new("RGBA", (PH_W, PH_H * len(posts)), (0, 0, 0, 255))
    caps = []
    for i, fn in enumerate(posts):
        p = Image.new("RGBA", (PH_W, PH_H), (0, 0, 0, 255))
        cap = fn(p, PH_W, PH_H) if fn is post_church else fn(ImageDraw.Draw(p), PH_W, PH_H)
        d = ImageDraw.Draw(p)
        d.rectangle((0, PH_H - 190, PH_W, PH_H), fill=(0, 0, 0, 90))
        d.text((30, PH_H - 150), "@" + ["meongku", "dapurmama", "infojkt", "langitsore", "meongku", "pengguna_rahasia"][i],
               font=vfont("Baloo2.ttf", 34, 800), fill=(255, 255, 255, 255))
        d.text((30, PH_H - 100), cap, font=vfont("Baloo2.ttf", 30, 600), fill=(255, 255, 255, 255))
        strip.alpha_composite(p, (0, i * PH_H))
        caps.append(cap)
    return strip


def heart_poly(cx, cy, s, n=48):
    pts = []
    for i in range(n):
        a = i / n * math.pi * 2
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + x * s, cy + y * s))
    return pts


@lru_cache(maxsize=None)
def heart_sprite(size=80, col=(255, 70, 110)):
    s = 4
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon(heart_poly(size * s / 2, size * s / 2, size * s / 36), fill=col + (255,))
    return img.resize((size, size), Image.LANCZOS)


def feed_pos(t):
    swipes = [51.8, 52.5, 53.1, 53.7, 54.25, 54.8]
    pos = 0.0
    for i, st in enumerate(swipes[:5]):
        dur = 0.4 if i < 4 else 0.7
        pos += ease_in_out((t - st) / dur)
    return pos


def s_phone(t):
    img = vgrad(W, H, [(0, (40, 24, 60)), (1, (18, 12, 30))])
    rng = random.Random(5)
    for i in range(18):
        bx, by = rng.uniform(0, W), rng.uniform(0, H)
        img = screen_add(img, glow_layer(W, H, bx, by, rng.uniform(60, 160), rng.choice([(255, 120, 180), (120, 140, 255), (255, 200, 120)]), 0.35, 1.5), 1) if i < 6 else img
    screen = Image.new("RGBA", (PH_W, PH_H), (0, 0, 0, 255))
    strip = feed_strip()
    off = int(feed_pos(t) * PH_H)
    screen.alpha_composite(strip.crop((0, off, PH_W, off + PH_H)))
    sd = ImageDraw.Draw(screen)
    sd.text((PH_W / 2 - 90, 60), "Mengikuti", font=vfont("Baloo2.ttf", 30, 600), fill=(220, 220, 220, 200), anchor="mm")
    sd.text((PH_W / 2 + 80, 60), "FYP", font=vfont("Baloo2.ttf", 34, 800), fill=(255, 255, 255, 255), anchor="mm")
    sd.line((PH_W / 2 + 55, 84, PH_W / 2 + 105, 84), fill=(255, 255, 255, 255), width=4)
    # side buttons
    liked = t > 57.85
    for k, yy in enumerate((520, 640, 760)):
        if k == 0:
            hs = heart_sprite(70, (255, 60, 100) if liked else (255, 255, 255))
            kk = 1 + 0.4 * math.sin(clamp((t - 57.85) / 0.3) * math.pi) if liked else 1
            hs2 = hs.resize((int(70 * kk), int(70 * kk)))
            screen.alpha_composite(hs2, (int(PH_W - 70 - 35 * kk), int(yy - 35 * kk)))
        else:
            sd.ellipse((PH_W - 100, yy - 30, PH_W - 40, yy + 30), fill=(255, 255, 255, 230))
    # double tap hearts on the photo
    if t > 57.8:
        for i in range(10):
            p = clamp((t - 57.8 - i * 0.12) / 1.2)
            if 0 < p < 1:
                hx = PH_W / 2 + math.sin(i * 2.3) * 140
                hy = 520 - p * 380
                hs = heart_sprite(int(60 + 30 * math.sin(i)))
                paste(screen, hs, hx, hy, 1 - p)
    # phone body
    phone = Image.new("RGBA", (PH_W + 60, PH_H + 60), (0, 0, 0, 0))
    pd = ImageDraw.Draw(phone)
    pd.rounded_rectangle((0, 0, PH_W + 60, PH_H + 60), radius=70, fill=(20, 20, 26, 255))
    m = Image.new("L", (PH_W, PH_H), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, PH_W, PH_H), radius=46, fill=255)
    screen.putalpha(m)
    phone.alpha_composite(screen, (30, 30))
    pd.rounded_rectangle((PH_W / 2 - 50, 44, PH_W / 2 + 110, 72), radius=14, fill=(10, 10, 14, 255))
    zoom = 1 + 0.12 * ease_in_out((t - 55.0) / 1.2)
    rot = -4 + 4 * ease_in_out((t - 55.0) / 1.2)
    ph = phone.resize((int(phone.width * zoom), int(phone.height * zoom)), Image.BICUBIC).rotate(rot, resample=Image.BICUBIC, expand=True)
    img = screen_add(img, glow_layer(W, H, W / 2, H / 2, 700, (180, 120, 255), 0.4, 2), 1)
    paste(img, ph, W / 2, H / 2 + 20)
    # thumb double-tapping
    if 57.2 < t < 58.6:
        tp = (t - 57.2) / 1.4
        tap = abs(math.sin(clamp((t - 57.6) / 0.4) * math.pi * 2)) * 30
        th = Image.new("RGBA", (240, 420), (0, 0, 0, 0))
        ImageDraw.Draw(th).rounded_rectangle((30, 20, 210, 420), radius=90, fill=(240, 196, 168, 255))
        ImageDraw.Draw(th).rounded_rectangle((70, 40, 170, 130), radius=40, fill=(250, 226, 214, 255))
        paste(img, th.rotate(20, expand=True), W / 2 + 160, lerp(H + 200, 820, ease_out_cubic(tp * 3)) + tap - (1 - clamp((58.6 - t) / 0.3)) * -300)
    # F Y P stickers on "eF Ye Pe ku"
    for ch, t0, x, y, col in (("F", 60.5, 520, 300, (255, 90, 120)), ("Y", 60.84, 1400, 380, (90, 200, 255)),
                              ("P", 61.19, 1420, 760, (255, 210, 80))):
        spr, _ = text_sprite(ch, "DelaGothic.ttf", 230, col, stroke=10, stroke_color=(255, 255, 255), shadow=(10, 12, (40, 20, 60)))
        pop_paste(img, spr.rotate(-12 + (ord(ch) % 5) * 6, expand=True, resample=Image.BICUBIC), x, y, t, t0)
    return img


# ----------------------------------------------------------------------------
# 61.9 - 66.8  a map of Indonesia: a church only I know
# ----------------------------------------------------------------------------
ISLANDS = {
    "sumatra": [(95.2, 5.5), (97.0, 5.2), (98.7, 3.8), (100.4, 2.3), (101.5, 1.8), (103.5, 0.9), (104.5, -1.0), (106.0, -3.0),
                (105.8, -5.8), (104.5, -5.9), (102.3, -4.0), (100.4, -1.0), (98.8, 1.5), (97.2, 3.0), (95.4, 4.6)],
    "java": [(105.2, -6.8), (106.0, -5.9), (108.0, -6.2), (110.4, -6.9), (112.6, -6.9), (114.4, -7.7), (114.5, -8.7),
             (112.0, -8.3), (110.0, -8.1), (108.0, -7.8), (106.4, -7.4)],
    "bali": [(114.6, -8.1), (115.7, -8.3), (115.2, -8.8), (114.5, -8.4)],
    "kalimantan": [(109.0, 1.5), (109.7, 2.0), (111.0, 1.5), (113.0, 3.0), (115.0, 4.5), (117.0, 7.0), (119.2, 5.0), (118.0, 1.0),
                   (117.5, -1.0), (116.4, -3.8), (114.5, -3.5), (112.0, -3.3), (110.2, -2.9), (109.0, -0.5)],
    "sulawesi": [(119.4, -5.5), (120.4, -5.6), (120.5, -3.0), (121.3, -4.7), (122.8, -4.9), (121.2, -2.6), (122.2, -1.2),
                 (123.3, -0.9), (121.5, -1.0), (120.7, 0.4), (124.8, 1.4), (125.1, 1.6), (123.0, 0.9), (120.2, 0.9),
                 (119.8, -0.9), (118.8, -2.8), (119.4, -3.6)],
    "papua": [(131.0, -1.2), (132.5, -0.4), (135.0, -3.3), (137.8, -1.5), (141.0, -2.6), (143.0, -3.5), (144.0, -6.5),
              (141.0, -9.1), (139.0, -8.1), (137.8, -8.4), (138.0, -7.0), (136.0, -4.6), (133.5, -3.9), (132.0, -2.8)],
    "halmahera": [(127.5, 2.0), (128.2, 1.6), (128.0, 0.5), (128.7, 0.3), (127.9, -0.8), (127.4, 0.6)],
    "seram": [(128.0, -3.0), (130.8, -3.1), (130.3, -3.7), (128.2, -3.6)],
    "flores": [(119.8, -8.5), (123.0, -8.3), (122.8, -8.8), (119.9, -8.9)],
    "sumbawa": [(116.9, -8.4), (119.1, -8.3), (118.8, -8.8), (117.0, -9.0)],
    "lombok": [(115.9, -8.3), (116.6, -8.3), (116.5, -8.9), (116.0, -8.8)],
    "timor": [(123.6, -10.1), (125.2, -8.6), (127.2, -8.4), (124.4, -9.8)],
    "sumba": [(119.0, -9.6), (120.8, -9.9), (120.2, -10.3), (119.1, -9.9)],
}


def geo(lon, lat):
    return (lon - 94.0) * 38 + 40, (7.5 - lat) * 58 + 40


@lru_cache(maxsize=None)
def map_base():
    img = vgrad(W, H, [(0, (236, 224, 196)), (1, (222, 206, 172))])
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(2)
    for y in range(40, H, 40):
        d.line((0, y, W, y), fill=(210, 196, 166, 255))
    for x in range(40, W, 40):
        d.line((x, 0, x, H), fill=(210, 196, 166, 255))
    for name, pts in ISLANDS.items():
        pp = [geo(*p) for p in pts]
        d.polygon([(x + 8, y + 10) for x, y in pp], fill=(190, 170, 140, 255))
        d.polygon(pp, fill=(150, 196, 120, 255), outline=(90, 120, 80, 255))
    # compass rose
    cx, cy = 1700, 180
    for a, ln, col in ((0, 90, (160, 40, 50)), (math.pi, 90, (80, 60, 50)), (math.pi / 2, 60, (80, 60, 50)), (-math.pi / 2, 60, (80, 60, 50))):
        d.polygon([(cx + math.sin(a) * ln, cy - math.cos(a) * ln), (cx + math.cos(a) * 14, cy + math.sin(a) * 14),
                   (cx - math.cos(a) * 14, cy - math.sin(a) * 14)], fill=col + (255,))
    d.text((cx, cy - 110), "U", font=font("CinzelDeco.ttf", 34), fill=(120, 60, 50, 255), anchor="mm")
    d.text((300, 980), "INDONESIA", font=font("CinzelDeco.ttf", 72), fill=(120, 80, 60, 255), anchor="mm")
    return img


def s_map(t):
    img = map_base().copy()
    pin = geo(110.4, -7.05)
    d = ImageDraw.Draw(img)
    # dotted journey lines from across the archipelago
    for k, src in enumerate([(106.8, -6.2), (98.7, 3.6), (119.4, -5.1), (124.8, 1.5)]):
        a = geo(*src)
        p = clamp((t - 62.0 - k * 0.2) / 1.4)
        for j in range(int(30 * p)):
            u = j / 30
            x = lerp(a[0], pin[0], u)
            y = lerp(a[1], pin[1], u) - math.sin(u * math.pi) * 120
            d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(190, 60, 70, 200))
    # pin drop + church icon
    drop = ease_out_back((t - 63.0) / 0.5, 2.5)
    if t > 63.0:
        px, py = pin[0], pin[1] - 20 - (1 - clamp((t - 63.0) / 0.4)) * 300
        pd = ImageDraw.Draw(img)
        pd.ellipse((pin[0] - 26, pin[1] - 8, pin[0] + 26, pin[1] + 8), fill=(0, 0, 0, 80))
        pd.polygon([(px - 40, py - 80), (px + 40, py - 80), (px, py)], fill=(220, 50, 70, 255))
        pd.ellipse((px - 46, py - 150, px + 46, py - 58), fill=(220, 50, 70, 255))
        pd.rectangle((px - 18, py - 118, px + 18, py - 86), fill=(255, 255, 255, 255))
        pd.polygon([(px - 22, py - 118), (px, py - 136), (px + 22, py - 118)], fill=(255, 255, 255, 255))
        pd.line((px, py - 150, px, py - 134), fill=(255, 255, 255, 255), width=3)
        pd.line((px - 6, py - 145, px + 6, py - 145), fill=(255, 255, 255, 255), width=3)
    # spotlight: only I know
    z = ease_in_out((t - 63.4) / 1.6)
    if z > 0:
        dark = Image.new("RGBA", (W, H), (20, 14, 30, 0))
        a = 1 - R.radial_alpha(W, H, pin[0], pin[1] - 60, lerp(2000, 320, z), 0.8)
        dark.putalpha(Image.fromarray((np.clip(a, 0, 1) * 200 * z).astype(np.uint8)))
        img.alpha_composite(dark)
    if t > 64.6:
        label(img, "(cuma aku yang tahu)", pin[0] + 300, pin[1] - 170, "Caveat.ttf", 64, (255, 240, 220),
              clamp((t - 64.6) / 0.4), weight=700, glow=8, glow_color=(255, 120, 150))
    return camera(img, 1 + 0.7 * z, lerp(W / 2, pin[0], z), lerp(H / 2, pin[1] - 60, z))


# ----------------------------------------------------------------------------
# 66.8 - 71.9  "PESIMIS" shatters: her charm breaks my pessimism
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def pesimis_shards():
    spr, _ = text_sprite("PESIMIS", "DelaGothic.ttf", 260, (150, 156, 170), stroke=6, stroke_color=(80, 84, 96))
    w, h = spr.size
    rng = np.random.default_rng(5)
    pts = np.vstack([rng.uniform([0, 0], [w, h], (70, 2)), [[0, 0], [w, 0], [0, h], [w, h]],
                     [[x, 0] for x in np.linspace(0, w, 8)], [[x, h] for x in np.linspace(0, w, 8)]])
    tri = Delaunay(pts)
    shards = []
    for simp in tri.simplices:
        poly = [tuple(pts[i]) for i in simp]
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        x0, y0, x1, y1 = int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1
        if x1 - x0 < 2 or y1 - y0 < 2:
            continue
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        piece = spr.copy()
        piece.putalpha(Image.fromarray(np.minimum(np.asarray(spr.getchannel("A")), np.asarray(m))))
        piece = piece.crop((x0, y0, x1, y1))
        if piece.getbbox() is None:
            continue
        shards.append((piece, (x0 + x1) / 2 - w / 2, (y0 + y1) / 2 - h / 2))
    return spr, shards


def s_shatter(t):
    hit = 68.7
    k = ss(hit, hit + 0.6, t)
    cold = vgrad(W, H, [(0, (70, 74, 86)), (1, (40, 42, 52))])
    warm = vgrad(W, H, [(0, (255, 150, 170)), (0.5, (255, 200, 150)), (1, (255, 236, 190))])
    if k > 0:
        m = Image.fromarray((np.clip(R.radial_alpha(W, H, W / 2, H / 2, 2200 * k + 1, 0.6), 0, 1) * 255).astype(np.uint8))
        img = Image.composite(warm, cold, m)
        rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rays)
        for i in range(18):
            a = i / 18 * math.pi * 2 + t * 0.2
            rd.polygon([(W / 2, H / 2), (W / 2 + math.cos(a - 0.06) * 2000, H / 2 + math.sin(a - 0.06) * 2000),
                        (W / 2 + math.cos(a + 0.06) * 2000, H / 2 + math.sin(a + 0.06) * 2000)], fill=(255, 255, 230, 60))
        img = screen_add(img, blur(rays, 10), k)
    else:
        img = cold
        R.rain_on_window(img, t, (0, 0, W, H), density=200, col=(170, 176, 190))
    spr, shards = pesimis_shards()
    cx, cy = W / 2, H / 2 - 40
    if t < hit:
        shake = math.sin(t * 50) * 6 * ss(hit - 0.8, hit, t)
        paste(img, spr, cx + shake, cy)
        # cracks forming
        d = ImageDraw.Draw(img)
        rng = random.Random(3)
        cr = ss(hit - 1.0, hit, t)
        for i in range(10):
            a = rng.uniform(0, 6.28)
            x, y = cx, cy
            for j in range(int(6 * cr)):
                nx, ny = x + math.cos(a) * 60, y + math.sin(a) * 40
                d.line((x, y, nx, ny), fill=(240, 244, 255, 220), width=3)
                x, y = nx, ny
                a += rng.uniform(-0.6, 0.6)
        # a grey raincloud over the word
        cl = R.anime_cloud(700, 260, 3, lit=(160, 164, 176), shade=(100, 104, 116), rim=(200, 204, 214))
        paste(img, cl, cx, cy - 260 + math.sin(t * 2) * 6, 0.95)
    else:
        el = t - hit
        rng = random.Random(9)
        for piece, ox, oy in shards:
            vx, vy = ox * 3.2 + rng.uniform(-200, 200), oy * 5 + rng.uniform(-300, 100)
            rot = rng.uniform(-400, 400) * el
            x = cx + ox + vx * el
            y = cy + oy + vy * el + 900 * el * el
            pr = piece.rotate(rot, expand=True, resample=Image.BILINEAR)
            paste(img, pr, x, y, clamp(1 - el / 1.6))
        # charm blooms where pessimism was
        for i in range(40):
            a = i / 40 * math.pi * 2
            r = ease_out_cubic(el / 1.2) * (300 + (i % 5) * 60)
            ang = int(((t * 150 + i * 23) % 360) / 10) % 36
            paste(img, kamboja_rot(40 + (i % 3) * 14, ang, i % 2), cx + math.cos(a) * r * 1.4, cy + math.sin(a) * r * 0.9,
                  clamp(el * 3) * (1 - ss(2.5, 3.2, el)))
        p = pop(t, hit + 0.35, 0.5)
        if p > 0:
            ps, _ = text_sprite("PESONA", "DelaGothic.ttf", 230, (255, 250, 240), stroke=6, stroke_color=(220, 60, 100),
                                glow=18, glow_color=(255, 120, 160), shadow=(10, 12, (200, 40, 90)))
            pop_paste(img, ps, cx, cy, t, hit + 0.35, 0.5)
    img = R.flash(img, t, hit, 0.25, peak=0.9)
    return img


# ----------------------------------------------------------------------------
# 71.9 - 84.9  mega mendung (Cirebon batik) portrait: beauty + faith in one person
# ----------------------------------------------------------------------------
MM_BANDS = [(18, 40, 90), (30, 70, 140), (50, 100, 180), (80, 140, 210), (130, 180, 230), (190, 220, 245), (240, 248, 255)]


@lru_cache(maxsize=None)
def mega_mendung(w, h, seed):
    m = np.asarray(R.cloud_mask(w, h, seed, n=16), np.float32) > 127
    dist = distance_transform_edt(m)
    band = np.clip((dist / 13).astype(int), 0, len(MM_BANDS) - 1)
    cols = np.array(MM_BANDS, np.float32)[band]
    edge = (np.abs(dist / 13 - np.round(dist / 13)) < 0.12) & m
    cols[edge] = [240, 248, 255]
    out = np.dstack([cols, m * 255.0])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def s_megamendung(t):
    img = vgrad(W, H, [(0, (150, 30, 50)), (1, (100, 16, 36))])
    # faint parang lines on the red ground
    d = ImageDraw.Draw(img)
    for k in range(-20, 40):
        x = k * 90 + (t * 20) % 90
        d.line((x, 0, x - 600, H), fill=(170, 44, 64, 255), width=10)
    for i, (x, y, w, h, seed, sp) in enumerate([(300, 220, 700, 300, 4, 14), (1580, 260, 760, 320, 7, -10),
                                                (260, 860, 800, 330, 11, 12), (1640, 880, 700, 300, 13, -12),
                                                (960, 110, 600, 240, 17, 8)]):
        cl = mega_mendung(w, h, seed)
        paste(img, cl, x + math.sin(t * 0.3 + i) * 30 + sp * (t - 72), y)
    # the girl, praying, with a halo
    img = screen_add(img, glow_layer(W, H, W / 2, 470, 460, (255, 230, 170), 0.8, 1.6), 1)
    halo = R._title_ring().resize((620, 620), Image.LANCZOS).rotate(-t * 8, resample=Image.BICUBIC)
    paste(img, halo, W / 2, 470, 0.6)
    eyes = "closed" if t < 80.9 else "happy"
    girl = C.chibi_scaled(1.25, "girl", eyes, "smile", 10, 10, True, True, 0)
    paste(img, girl, W / 2, 560 + math.sin(t * 1.2) * 8)
    # veil (mantilla)
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.chord((W / 2 - 190, 180 + math.sin(t * 1.2) * 8, W / 2 + 190, 640), 180, 360, fill=(255, 255, 255, 70))
    for k in range(10):
        a = math.pi + k / 9 * math.pi
        vd.ellipse((W / 2 + math.cos(a) * 180 - 10, 410 + math.sin(a) * 220 - 10, W / 2 + math.cos(a) * 180 + 10,
                    410 + math.sin(a) * 220 + 10), outline=(255, 255, 255, 140), width=2)
    img.alpha_composite(veil)
    # paras (beauty) and iman (faith) icons merge into one heart
    merge = ease_in_out((t - 80.2) / 1.4)
    heart_c = (W / 2, 640)
    for t0, x, icon, word in ((74.28, 560, "flower", "paras"), (75.18, 1360, "cross", "iman")):
        if t < t0:
            continue
        px = lerp(x, heart_c[0], merge)
        py = lerp(560, heart_c[1], merge)
        a = 1 - ss(0.85, 1.0, merge)
        if icon == "flower":
            spr = R.kamboja_sprite(200, 1)
        else:
            spr = _cross_sprite()
        pop_paste(img, spr, px, py + math.sin(t * 2) * 10, t, t0, 0.4, a)
        if merge < 0.3:
            label(img, word, x, 720, "Caveat.ttf", 80, (255, 246, 230), clamp((t - t0) / 0.3) * (1 - merge / 0.3), weight=700,
                  glow=8, glow_color=(255, 120, 150))
    if merge > 0.8:
        hk = pop(t, 81.3, 0.5)
        hs = heart_sprite(int(180 * max(0.01, hk)), (255, 90, 130))
        img = screen_add(img, glow_layer(W, H, heart_c[0], heart_c[1], 300, (255, 160, 180), 0.8 * hk, 2), 1)
        paste(img, hs, heart_c[0], heart_c[1] + math.sin(t * 4) * 6)
        for i in range(10):
            a = i / 10 * math.pi * 2 + t
            paste(img, sparkle_sprite(40), heart_c[0] + math.cos(a) * 200, heart_c[1] + math.sin(a) * 140, 0.8)
    R.petals_field(img, t, 21, 10, 72, wind=(-160, 60), size=(22, 40), alpha=0.8)
    return img


@lru_cache(maxsize=None)
def _cross_sprite():
    def fn(d, s):
        d.rounded_rectangle((80 * s, 10 * s, 120 * s, 190 * s), radius=8 * s, fill=(255, 214, 110, 255))
        d.rounded_rectangle((30 * s, 50 * s, 170 * s, 90 * s), radius=8 * s, fill=(255, 214, 110, 255))
    img = ss_draw(200, 200, fn)
    g = blur(img, 14)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(img)
    return out


# ----------------------------------------------------------------------------
# 84.9 - 95.2  "Kata Mama": red thread held in God's hands
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def living_room():
    img = vgrad(W, H, [(0, (250, 226, 170)), (1, (236, 200, 140))])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 820, W, H), fill=(170, 110, 70, 255))
    for x in range(0, W, 160):
        for y in range(820, H, 80):
            d.rectangle((x + ((y // 80) % 2) * 80, y, x + 76 + ((y // 80) % 2) * 80, y + 76), fill=(186, 124, 80, 255))
    # framed cross, family photo, a tokek-free wall clock and a rice cooker
    d.rectangle((900, 120, 1020, 300), fill=(120, 70, 40, 255))
    d.rectangle((952, 140, 968, 280), fill=(255, 220, 140, 255))
    d.rectangle((920, 180, 1000, 196), fill=(255, 220, 140, 255))
    d.rectangle((1180, 160, 1420, 320), fill=(120, 70, 40, 255))
    d.rectangle((1196, 176, 1404, 304), fill=(200, 220, 230, 255))
    for k, c in enumerate([(206, 64, 90), (130, 84, 50), (46, 92, 156)]):
        d.ellipse((1230 + k * 60, 210, 1270 + k * 60, 250), fill=(250, 216, 188, 255))
        d.rectangle((1226 + k * 60, 250, 1274 + k * 60, 300), fill=c + (255,))
    d.rounded_rectangle((1500, 640, 1800, 820), radius=10, fill=(150, 90, 60, 255))
    d.rounded_rectangle((1560, 540, 1700, 640), radius=40, fill=(250, 250, 250, 255))
    d.rectangle((1580, 600, 1680, 612), fill=(230, 80, 80, 255))
    return img


def draw_hand(d, x, y, sc, mirror, col):
    sg = -1 if mirror else 1
    d.rounded_rectangle((x - 110 * sc, y - 70 * sc, x + 110 * sc, y + 90 * sc), radius=int(70 * sc), fill=col)
    for k in range(4):
        fx = x - 90 * sc + k * 58 * sc
        d.rounded_rectangle((fx, y - 190 * sc + abs(k - 1.5) * 24 * sc, fx + 50 * sc, y - 20 * sc), radius=int(25 * sc), fill=col)
    xa, xb = sorted((x + sg * 60 * sc, x + sg * 200 * sc))
    d.rounded_rectangle((xa, y - 60 * sc, xb, y + 10 * sc), radius=int(30 * sc), fill=col)


def s_mama(t):
    sky = ease_in_out((t - 88.6) / 1.2)
    if sky < 1:
        room = living_room().copy()
        mama = C.chibi_scaled(1.2, "mama", "open", "open" if int(t * 6) % 2 and t < 90.4 else "smile", 150, 12, True, False, 0)
        boy = C.chibi_scaled(1.1, "boy", "open", "smile", 10, 10, True, False, -1)
        paste(room, mama, 560, 560)
        paste(room, boy, 1300, 590 + abs(math.sin(t * 3)) * 8)
        if t > 85.2:
            bub = C.speech_bubble("Jodoh itu di tangan Tuhan, Nak.", size=52, maxw=560)
            pop_paste(room, bub, 760, 200, t, 85.3)
    heaven = None
    if sky > 0:
        heaven = vgrad(W, H, [(0, (70, 90, 190)), (0.6, (250, 190, 200)), (1, (255, 230, 190))])
        heaven = screen_add(heaven, glow_layer(W, H, W / 2, 200, 900, (255, 240, 200), 0.8, 1.6), 1)
        for i, (cx_, cy_) in enumerate([(300, 820), (1600, 860), (960, 980)]):
            paste(heaven, R.anime_cloud(900, 340, 30 + i, lit=(255, 240, 240), shade=(230, 190, 220)), cx_, cy_)
        hands = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hands)
        col = (255, 226, 170, 235)
        draw_hand(hd, 520, 700, 1.3, False, col)
        draw_hand(hd, 1400, 700, 1.3, True, col)
        hg = blur(hands, 30)
        heaven.alpha_composite(hg)
        heaven.alpha_composite(hands)
        # red thread between two tiny people
        pull = ease_in_out((t - 90.6) / 3.0)
        bx, gx = lerp(560, 860, pull), lerp(1360, 1060, pull)
        pts = []
        for j in range(41):
            u = j / 40
            x = lerp(bx, gx, u)
            y = 520 + math.sin(u * math.pi) * lerp(60, -40, pull) + math.sin(u * 12 + t * 3) * 6 * (1 - pull)
            pts.append((x, y))
        td = ImageDraw.Draw(heaven)
        td.line(pts, fill=(220, 30, 50, 255), width=7)
        paste(heaven, C.chibi_scaled(0.42, "boy", "happy", "smile", 10, 90, True, False, 0), bx - 30, 460)
        paste(heaven, C.chibi_scaled(0.42, "girl", "happy", "smile", 90, 10, True, False, 0), gx + 30, 460)
        if t > 93.4:
            hk = pop(t, 93.6, 0.5)
            hs = heart_sprite(max(1, int(160 * hk)), (230, 40, 70))
            heaven = screen_add(heaven, glow_layer(W, H, W / 2, 470, 260, (255, 120, 140), 0.7 * hk, 2), 1)
            paste(heaven, hs, W / 2, 470)
    if heaven is None:
        return room
    if sky >= 1:
        return heaven
    # the camera tilts up from the living room into the sky
    out = Image.new("RGBA", (W, H))
    off = int(sky * H)
    out.paste(heaven.crop((0, H - off, W, H)), (0, 0))
    out.paste(room.crop((0, 0, W, H - off)), (0, off))
    return out


# ----------------------------------------------------------------------------
# 95.2 - 111.5  manga panels: "kalau saja..."
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def screentone(w, h, step=12, r=3.0, col=(0, 0, 0, 90)):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(0, h, step):
        for x in range((y // step) % 2 * step // 2, w, step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    return img


def speed_lines(w, h, t, cx, cy, n=60, col=(0, 0, 0, 200)):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(int(t * 12))
    for i in range(n):
        a = rng.uniform(0, 6.28)
        r0 = rng.uniform(260, 420)
        d.polygon([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a + 0.02) * 1600, cy + math.sin(a + 0.02) * 1600),
                   (cx + math.cos(a - 0.02) * 1600, cy + math.sin(a - 0.02) * 1600)], fill=col)
    return img


def panel_office(t, w, h):
    p = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    d = ImageDraw.Draw(p)
    p.alpha_composite(screentone(w, h))
    d.rectangle((40, 60, 360, h), fill=(230, 230, 230, 255), outline=(0, 0, 0, 255), width=5)
    for y in range(90, h, 60):
        for x in range(70, 340, 70):
            d.rectangle((x, y, x + 40, y + 36), fill=(90, 90, 90, 255))
    d.text((200, 30), "KANTOR", font=font("Bangers.ttf", 44), fill=(0, 0, 0, 255), anchor="mm")
    gx = lerp(360, w - 240, ease_in_out((t - 95.4) / 4.0))
    girl = grey(C.chibi_scaled(0.75, "girl", "open", "smile", 60, -60, False, False, 1), 1)
    paste(p, girl, gx, h - 230)
    d.rectangle((gx - 70, h - 250, gx + 70, h - 170), fill=(200, 170, 130, 255), outline=(0, 0, 0, 255), width=4)
    d.line((gx - 70, h - 230, gx + 70, h - 230), fill=(0, 0, 0, 255), width=3)
    label(p, "PINDAH KERJA!", w - 200, 90, "Bangers.ttf", 70, (0, 0, 0), 1, stroke=4, stroke_color=(255, 255, 255))
    return p


def panel_train(t, w, h):
    p = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    p.alpha_composite(speed_lines(w, h, t, w / 2, h / 2, 40, (0, 0, 0, 120)))
    d = ImageDraw.Draw(p)
    tx = lerp(w + 50, -900, clamp((t - 100.6) / 4.0))
    d.rounded_rectangle((tx, h / 2 - 120, tx + 1100, h / 2 + 90), radius=30, fill=(245, 245, 245, 255), outline=(0, 0, 0, 255), width=6)
    d.polygon([(tx, h / 2 - 120), (tx - 80, h / 2 + 90), (tx, h / 2 + 90)], fill=(245, 245, 245, 255), outline=(0, 0, 0, 255))
    d.rectangle((tx - 40, h / 2 + 10, tx + 1100, h / 2 + 30), fill=(200, 40, 40, 255))
    for k in range(8):
        d.rectangle((tx + 40 + k * 130, h / 2 - 90, tx + 140 + k * 130, h / 2 - 20), fill=(60, 60, 60, 255))
    paste(p, grey(C.chibi_scaled(0.3, "girl", "happy", "smile", 10, 150, False, False, 0), 1), tx + 350, h / 2 - 55)
    d.rectangle((0, h / 2 + 100, w, h / 2 + 116), fill=(0, 0, 0, 255))
    d.rounded_rectangle((60, 40, 470, 120), radius=10, fill=(30, 30, 30, 255))
    d.text((265, 80), "\u2192 KOTA BARU", font=font("Bangers.ttf", 52), fill=(255, 255, 255, 255), anchor="mm")
    return p


def panel_photo(t, w, h):
    p = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    p.alpha_composite(screentone(w, h, 10, 2.4))
    ch = grey(R.church_sprite(), 1).resize((720, 760))
    paste(p, ch, w / 2 + 380, h - 360)
    girl = grey(C.chibi_scaled(0.9, "girl", "happy", "open", 10, 165, False, False, 0), 1)
    paste(p, girl, w / 2 + 360, h - 250)
    # phone in the foreground
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((150, 120, 560, h + 60), radius=40, fill=(20, 20, 20, 255))
    d.rectangle((180, 170, 530, h), fill=(230, 230, 230, 255))
    paste(d._image if False else p, grey(C.chibi_scaled(0.4, "girl", "happy", "open", 10, 165, False, False, 0), 1), 355, 380)
    snap = 109.2
    if t > snap:
        k = 1 - clamp((t - snap) / 0.5)
        p.alpha_composite(Image.new("RGBA", (w, h), (255, 255, 255, int(230 * k))))
        spr, _ = text_sprite("CKREK!", "Bangers.ttf", 190, (0, 0, 0), stroke=8, stroke_color=(255, 255, 255))
        pop_paste(p, spr.rotate(8, expand=True), w / 2 - 80, 180, t, snap, 0.3)
    return p


def manga_page(t):
    img = Image.new("RGBA", (W, H), (250, 250, 248, 255))
    rects = [((40, 40, 930, 560), 95.2, panel_office, (-1, 0)), ((990, 40, 1880, 560), 100.4, panel_train, (1, 0)),
             ((40, 600, 1880, 1040), 105.6, panel_photo, (0, 1))]
    for (x0, y0, x1, y1), t0, fn, (dx, dy) in rects:
        if t < t0 - 0.05:
            continue
        p = ease_out_cubic((t - t0) / 0.45)
        w, h = x1 - x0, y1 - y0
        panel = fn(t, w, h)
        pd = ImageDraw.Draw(panel)
        pd.rectangle((0, 0, w - 1, h - 1), outline=(0, 0, 0, 255), width=8)
        ox, oy = (1 - p) * dx * 900, (1 - p) * dy * 700
        img.alpha_composite(panel, (int(x0 + ox), int(y0 + oy)))
    return img


def s_manga(t):
    img = manga_page(t)
    return grey(img, 0.9)


def s_kalau(t):
    el = t - 111.5
    img = manga_page(111.4)
    img = grey(img, 1)
    shake = math.sin(t * 70) * 16 * (1 - ss(113.8, 115, t))
    img = camera(img, 1 + el * 0.06, W / 2 + shake, H / 2, rot=math.sin(t * 30) * 1.5)
    if int(t * 10) % 5 == 0 and t < 114:
        a = 255 - np.asarray(img, np.uint8)
        a[..., 3] = 255
        img = Image.fromarray(a, "RGBA")
    for i, (t0, x, y, sz) in enumerate([(111.6, 520, 330, 200), (112.35, 1380, 640, 240), (112.9, 800, 820, 150),
                                        (113.3, 1500, 250, 130)]):
        if t > t0:
            spr, _ = text_sprite("KALAU...", "Bangers.ttf", sz, (255, 255, 255), stroke=10, stroke_color=(0, 0, 0))
            pop_paste(img, spr.rotate(-8 + i * 6, expand=True), x, y, t, t0, 0.25, 1 - ss(114.3, 115, t))
    img.alpha_composite(speed_lines(W, H, t, W / 2, H / 2, 50, (0, 0, 0, 150)))
    return img


# ----------------------------------------------------------------------------
# 115.0 - 125.4  grey panels become sky lanterns: gratitude
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def lantern_sprite(size=90):
    def fn(d, s):
        d.polygon([(size * 0.2 * s, size * 0.1 * s), (size * 0.8 * s, size * 0.1 * s), (size * 0.9 * s, size * 0.95 * s),
                   (size * 0.1 * s, size * 0.95 * s)], fill=(255, 150, 70, 255))
        d.polygon([(size * 0.3 * s, size * 0.2 * s), (size * 0.7 * s, size * 0.2 * s), (size * 0.75 * s, size * 0.85 * s),
                   (size * 0.25 * s, size * 0.85 * s)], fill=(255, 210, 120, 255))
        d.ellipse((size * 0.4 * s, size * 0.8 * s, size * 0.6 * s, size * 0.98 * s), fill=(255, 250, 220, 255))
    img = ss_draw(size, size, fn)
    g = blur(img, size * 0.3)
    out = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    gg = g.resize((size * 2, size * 2))
    out.alpha_composite(gg)
    out.alpha_composite(img, (size // 2, size // 2))
    return out


def s_lanterns(t):
    sat = ss(115.0, 119.0, t)
    img = vgrad(W, H, [(0, (14, 16, 50)), (0.55, (60, 40, 100)), (0.62, (255, 160, 120)), (1, (30, 24, 60))])
    d = ImageDraw.Draw(img)
    rng = random.Random(4)
    for _ in range(120):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.5)
        d.ellipse((x - 1.4, y - 1.4, x + 1.4, y + 1.4), fill=(255, 255, 255, 200))
    # far hills
    d.polygon([(0, 660), (300, 600), (700, 640), (1100, 590), (1500, 630), (W, 600), (W, 680), (0, 680)], fill=(30, 24, 60, 255))
    sky = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rng = random.Random(11)
    for i in range(46):
        born = 114.6 + i * 0.2
        el = t - born
        if el < 0:
            continue
        x = rng.uniform(100, W - 100) + math.sin(el * 0.8 + i) * 40
        y = 700 - el * rng.uniform(40, 80)
        sz = int(rng.uniform(40, 110) * (1 - clamp(el / 20) * 0.5))
        paste(sky, lantern_sprite(max(20, sz)), x, y, clamp(el * 2))
    img.alpha_composite(sky)
    # the lake mirrors everything
    top = img.crop((0, 0, W, 680))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).resize((W, H - 680))
    arr = np.asarray(refl, np.float32)
    rows = np.arange(arr.shape[0])
    shift = (np.sin(rows * 0.15 + t * 3) * 6).astype(int)
    for r in range(0, arr.shape[0], 2):
        arr[r:r + 2] = np.roll(arr[r:r + 2], shift[r], axis=1)
    arr[..., :3] *= 0.6
    img.paste(Image.fromarray(arr.astype(np.uint8), "RGBA"), (0, 680))
    # pier + the boy, hands folded in gratitude
    d = ImageDraw.Draw(img)
    d.rectangle((1200, 760, W, 790), fill=(20, 16, 30, 255))
    for px in range(1220, W, 120):
        d.rectangle((px, 790, px + 16, 900), fill=(20, 16, 30, 255))
    pray = t > 121.3
    boy = C.chibi_scaled(0.75, "boy", "closed" if pray else "open", "smile", 150 if not pray else 10, 10, False, pray, 0)
    silh = Image.new("RGBA", boy.size, (20, 16, 30, 255))
    silh.putalpha(boy.getchannel("A"))
    paste(img, silh, 1500, 760 - boy.height / 2 + 10)
    if not pray:
        pass
    img = grey(img, 1 - sat)
    if t > 121.8:
        img = screen_add(img, glow_layer(W, H, 1500, 560, 400, (255, 210, 150), 0.6 * ss(121.8, 122.8, t), 2), 1)
    return img
