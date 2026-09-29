"""Scenes for the end of Chorus 1, Verse 3, Chorus 2 and the Outro (125 s - end)."""
import math
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

import cast as C
import render as R
from render import (W, H, clamp, lerp, ss, ease_out_back, ease_out_cubic, ease_in_out, vgrad, glow_layer,
                    screen_add, paste, ss_draw, blur, text_sprite, font, vfont, kamboja_rot, sparkle_sprite, camera,
                    mix_rgb)
from scenes_a import grey, label, pop, pop_paste, heart_sprite, heart_poly, mega_mendung, draw_hand


def sunburst(t, c1, c2, n=20, cx=W / 2, cy=H / 2, speed=0.2):
    img = Image.new("RGBA", (W, H), c1 + (255,))
    d = ImageDraw.Draw(img)
    for i in range(n):
        a0 = i / n * math.pi * 2 + t * speed
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + math.cos(a0) * 2400, cy + math.sin(a0) * 2400),
                   (cx + math.cos(a1) * 2400, cy + math.sin(a1) * 2400)], fill=c2 + (255,))
    return img


def confetti(img, t, t0, n=120, seed=1, colors=((230, 40, 50), (255, 255, 255), (255, 200, 60), (80, 180, 255))):
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for i in range(n):
        el = t - t0 - rng.uniform(0, 0.6)
        if el < 0:
            continue
        x = rng.uniform(0, W) + math.sin(el * 3 + i) * 40
        y = -40 + el * rng.uniform(250, 500)
        if y > H + 40:
            continue
        a = el * rng.uniform(3, 9)
        w_, h_ = 18, 10 * abs(math.cos(a)) + 2
        col = colors[i % len(colors)]
        d.polygon([(x + math.cos(a) * w_ - math.sin(a) * h_, y + math.sin(a) * w_ + math.cos(a) * h_),
                   (x - math.cos(a) * w_ - math.sin(a) * h_, y - math.sin(a) * w_ + math.cos(a) * h_),
                   (x - math.cos(a) * w_ + math.sin(a) * h_, y - math.sin(a) * w_ - math.cos(a) * h_),
                   (x + math.cos(a) * w_ + math.sin(a) * h_, y + math.sin(a) * w_ - math.cos(a) * h_)], fill=col + (255,))


# ----------------------------------------------------------------------------
# 125.4 - 130.4  pop-art joy: so happy to know you
# ----------------------------------------------------------------------------
def s_happy(t):
    img = sunburst(t, (255, 200, 60), (255, 150, 60), 22, speed=0.4)
    img.alpha_composite(R.kawung_field(W, H, 120, (255, 255, 255, 40)))
    jump = abs(math.sin((t - 125.4) * math.pi / R.BEAT)) * 90
    boy = C.chibi_scaled(1.15, "boy", "happy", "open", 160, 160, True, False, 0)
    paste(img, boy, 760, 600 - jump)
    if t > 127.0:
        k = ease_out_back((t - 127.0) / 0.5)
        girl = C.chibi_scaled(1.15, "girl", "sparkle", "open", 150, 20, True, False, -1)
        paste(img, girl, lerp(W + 300, 1180, k), 600 - abs(math.sin((t - 127) * math.pi / R.BEAT + 1)) * 60)
    for i in range(8):
        a = i / 8 * math.pi * 2 + t * 1.5
        paste(img, heart_sprite(60 + (i % 3) * 20), 960 + math.cos(a) * 620, 520 + math.sin(a) * 330, 0.9)
    confetti(img, t, 125.5, 140, 2)
    return img


# ----------------------------------------------------------------------------
# 130.4 - 139.7  hundreds of matches: compatibility meter
# ----------------------------------------------------------------------------
TAGS = ["Misa Minggu", "Kopi susu", "Lagu galau", "Bakso", "Kucing", "Hujan sore", "Kulineran", "Doa malam",
        "Nonton film", "Jalan pagi", "Martabak", "Pantai"]


@lru_cache(maxsize=None)
def tag_chip(text, col):
    f = vfont("Baloo2.ttf", 44, 800)
    w = int(f.getlength(text) + 120)
    def fn(d, s):
        d.rounded_rectangle((0, 0, (w - 1) * s, 79 * s), radius=40 * s, fill=col + (255,))
        d.ellipse((14 * s, 14 * s, 66 * s, 66 * s), fill=(255, 255, 255, 255))
        d.line((26 * s, 40 * s, 36 * s, 52 * s, 56 * s, 28 * s), fill=col + (255,), width=8 * s, joint="curve")
        d.text((84 * s, 40 * s), text, font=vfont("Baloo2.ttf", 44 * s, 800), fill=(255, 255, 255, 255), anchor="lm")
    return ss_draw(w, 80, fn)


def s_match(t):
    img = vgrad(W, H, [(0, (255, 236, 244)), (1, (230, 236, 255))])
    pct = int(100 * ease_in_out(clamp((t - 130.6) / 3.8)))
    done = pct >= 100
    if done:
        img = screen_add(img, glow_layer(W, H, W / 2, 470, 900, (255, 160, 200), 0.5, 2), 1)
    # avatars
    for x, who in ((420, "boy"), (1500, "girl")):
        d = ImageDraw.Draw(img)
        d.ellipse((x - 170, 260, x + 170, 600), fill=(255, 255, 255, 255), outline=(255, 120, 160, 255), width=10)
        head = C.chibi_scaled(0.85, who, "happy" if done else "open", "open" if done else "smile", 10, 10, True, False, 0)
        crop = head.crop((0, 0, head.width, int(head.height * 0.62)))
        paste(img, crop, x, 430 + (0 if not done else -abs(math.sin(t * 6)) * 14))
    # ring meter
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cx, cy, r = W / 2, 430, 180
    rd.arc((cx - r, cy - r, cx + r, cy + r), 0, 360, fill=(240, 220, 230, 255), width=40)
    rd.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * pct / 100, fill=(255, 90, 140, 255), width=40)
    img.alpha_composite(ring)
    label(img, f"{pct}%", cx, cy - 10, "DelaGothic.ttf", 120, (255, 80, 130))
    label(img, "kecocokan", cx, cy + 90, "Baloo2.ttf", 44, (150, 90, 120), weight=700)
    # tags pop around
    rng = random.Random(3)
    cols = [(255, 110, 150), (110, 170, 255), (255, 170, 70), (120, 200, 140), (180, 130, 230)]
    for i, tg in enumerate(TAGS):
        t0 = 130.8 + i * 0.3
        row, col = i // 4, i % 4
        x = 300 + col * 440 + (row % 2) * 110
        y = 690 + row * 88
        pop_paste(img, tag_chip(tg, cols[i % len(cols)]), x, y, t, t0)
    if done:
        st, _ = text_sprite("MATCH!", "DelaGothic.ttf", 150, (255, 255, 255), stroke=8, stroke_color=(255, 80, 130),
                            shadow=(8, 10, (200, 40, 90)))
        pop_paste(img, st.rotate(-10, expand=True), W / 2, 150, t, 134.5, 0.4)
        confetti(img, t, 134.5, 90, 7, ((255, 90, 140), (255, 200, 80), (120, 180, 255), (255, 255, 255)))
    return img


# ----------------------------------------------------------------------------
# 139.7 - 151.9  dozens of differences, puzzle pieces that complete each other
# ----------------------------------------------------------------------------
DIFFS = [("Bubur diaduk", "Bubur tidak diaduk"), ("Pedas level 5", "Tidak pedas"), ("Begadang", "Tidur cepat"),
         ("Kopi hitam", "Teh manis")]


@lru_cache(maxsize=None)
def batik_parang(w, h):
    img = Image.new("RGBA", (w, h), (120, 60, 30, 255))
    d = ImageDraw.Draw(img)
    for k in range(-20, 40):
        x = k * 50
        d.line((x, 0, x - h, h), fill=(230, 180, 90, 255), width=16)
        for j in range(0, h, 60):
            d.ellipse((x - j - 10, j - 10, x - j + 10, j + 10), fill=(90, 40, 20, 255))
    return img


def puzzle_half(left, scale):
    s = scale
    w, h = int(760 * s), int(720 * s)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    cx, cy = w if left else 0, h * 0.46
    pts = heart_poly(cx, cy, 22 * s, 80)
    d.polygon(pts, fill=255)
    if left:
        d.rectangle((cx, 0, w, h), fill=0)
        d.ellipse((cx - 50 * s, cy - 50 * s, cx + 50 * s, cy + 50 * s), fill=255)
    else:
        d.ellipse((cx - 50 * s, cy - 50 * s, cx + 50 * s, cy + 50 * s), fill=0)
    tex = batik_parang(w, h) if left else Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if not left:
        bg = Image.new("RGBA", (w, h), (20, 40, 90, 255))
        mm = mega_mendung(w, int(h * 0.7), 13)
        bg.alpha_composite(mm, (0, int(h * 0.12)))
        tex = bg
    tex = tex.copy()
    tex.putalpha(m)
    edge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    outline = m.filter(__import__("PIL.ImageFilter", fromlist=["x"]).FIND_EDGES)
    edge.putalpha(outline)
    tex.alpha_composite(edge)
    return tex


@lru_cache(maxsize=None)
def puzzle_pieces():
    return puzzle_half(True, 1.0), puzzle_half(False, 1.0)


def s_puzzle(t):
    img = vgrad(W, H, [(0, (250, 240, 226)), (1, (236, 222, 200))])
    join = ease_in_out((t - 147.3) / 1.9)
    if t < 144.3:
        # differences list
        for i, (a, b) in enumerate(DIFFS):
            t0 = 140.8 + i * 0.75
            y = 260 + i * 170
            pop_paste(img, C.speech_bubble(a, size=48, maxw=500), 520, y, t, t0)
            pop_paste(img, C.speech_bubble(b, size=48, maxw=500), 1400, y, t, t0 + 0.2)
            neq, _ = text_sprite("\u2260", "DejaVuSans-Bold.ttf" if False else "Baloo2.ttf", 110, (220, 60, 90), weight=800)
            pop_paste(img, neq, 960, y, t, t0 + 0.35)
        paste(img, C.chibi_scaled(0.55, "boy", "open", "o", 10, 10, True, False, 0), 160, 900)
        paste(img, C.chibi_scaled(0.55, "girl", "open", "o", 10, 10, True, False, 0), 1760, 900)
        return img
    lp, rp = puzzle_pieces()
    fade = ss(144.2, 144.8, t)
    gap = lerp(520, 0, join)
    wob = math.sin(t * 2) * 12 * (1 - join)
    paste(img, lp, W / 2 - lp.width / 2 - gap, 520 + wob, fade)
    paste(img, rp, W / 2 + rp.width / 2 + gap, 520 - wob, fade)
    if join >= 1:
        k = clamp((t - 149.2) / 0.5)
        img = R.flash(img, t, 149.2, 0.2, (255, 250, 230), 0.8)
        img = screen_add(img, glow_layer(W, H, W / 2, 520, 800, (255, 180, 200), 0.6 * k, 2), 1)
        for i in range(24):
            a = i / 24 * math.pi * 2
            rr = 400 + ease_out_cubic((t - 149.2) / 1.5) * 300
            paste(img, sparkle_sprite(50), W / 2 + math.cos(a) * rr, 520 + math.sin(a) * rr * 0.7, 1 - clamp((t - 150) / 1.5))
        label(img, "saling melengkapi", W / 2, 150, "Caveat.ttf", 110, (180, 40, 70), clamp((t - 149.4) / 0.4), weight=700)
    return img


# ----------------------------------------------------------------------------
# 151.9 - 158.45  scooter ride through the sawah; rain, one shared raincoat
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def ride_layers():
    L = {}
    LW = W * 2
    def hills(d, s):
        pts = [(0, 600)] + [(x, 560 + math.sin(x / 300) * 50 + math.sin(x / 90) * 10) for x in range(0, LW + 40, 40)] + [(LW, H), (0, H)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=(110, 170, 110, 255))
        for k in range(3):
            mx = 400 + k * 1400
            d.polygon([((mx - 500) * s, 600 * s), (mx * s, 250 * s), ((mx + 520) * s, 600 * s)], fill=(120, 150, 190, 255))
    L["far"] = ss_draw(LW, H, hills)
    def sawah(d, s):
        for k in range(6):
            y0 = 640 + k * 40
            col = (90 + k * 12, 180 - k * 6, 70, 255)
            d.rectangle((0, y0 * s, LW * s, (y0 + 40) * s), fill=col)
            for x in range(0, LW, 60):
                d.line((x * s, (y0 + 6) * s, (x + 10) * s, (y0 - 12) * s), fill=(60, 140, 50, 255), width=3 * s)
        for hx in (500, 1900, 3200):
            d.polygon([((hx - 90) * s, 660 * s), (hx * s, 600 * s), ((hx + 90) * s, 660 * s)], fill=(150, 100, 60, 255))
            d.rectangle(((hx - 70) * s, 660 * s, (hx + 70) * s, 700 * s), fill=(190, 150, 100, 255))
    L["sawah"] = ss_draw(LW, H, sawah)
    def palms(d, s):
        for px in range(200, LW, 520):
            d.line((px * s, 900 * s, (px + 30) * s, 560 * s), fill=(90, 70, 50, 255), width=16 * s)
            for k in range(7):
                a = -math.pi / 2 + (k - 3) * 0.5
                d.line(((px + 30) * s, 560 * s, (px + 30 + math.cos(a) * 170) * s, (560 + math.sin(a) * 90 + 70) * s),
                       fill=(50, 130, 60, 255), width=12 * s)
    L["palms"] = ss_draw(LW, H, palms)
    return L


def draw_scooter(img, x, y, t, rain):
    d = ImageDraw.Draw(img)
    for wx in (x - 150, x + 150):
        d.ellipse((wx - 52, y - 52, wx + 52, y + 52), fill=(30, 30, 36, 255))
        d.ellipse((wx - 26, y - 26, wx + 26, y + 26), fill=(180, 180, 190, 255))
        for k in range(3):
            a = t * 20 + k * 2.09
            d.line((wx, y, wx + math.cos(a) * 24, y + math.sin(a) * 24), fill=(80, 80, 90, 255), width=4)
    d.polygon([(x - 200, y - 40), (x + 80, y - 40), (x + 200, y - 30), (x + 180, y - 110), (x + 120, y - 150), (x - 20, y - 110),
               (x - 190, y - 110)], fill=(230, 60, 70, 255))
    d.rounded_rectangle((x - 180, y - 140, x + 20, y - 110), radius=12, fill=(40, 40, 50, 255))
    d.line((x + 150, y - 150, x + 170, y - 240), fill=(40, 40, 50, 255), width=10)
    d.line((x + 140, y - 240, x + 200, y - 240), fill=(40, 40, 50, 255), width=10)
    d.ellipse((x + 190, y - 150, x + 222, y - 118), fill=(255, 240, 180, 255))
    # riders (side view chibis with helmets)
    for rx, who, hcol, body in ((x + 40, "boy", (250, 250, 250), (46, 92, 156)), (x - 110, "girl", (255, 170, 200), (250, 248, 244))):
        bob = math.sin(t * 12 + rx) * 3
        d.rounded_rectangle((rx - 45, y - 280 + bob, rx + 45, y - 130 + bob), radius=30, fill=body + (255,))
        d.ellipse((rx - 70, y - 420 + bob, rx + 70, y - 280 + bob), fill=C.SKIN + (255,))
        d.chord((rx - 78, y - 432 + bob, rx + 78, y - 290 + bob), 150, 390, fill=hcol + (255,))
        d.rectangle((rx + 20, y - 370 + bob, rx + 74, y - 340 + bob), fill=(90, 110, 140, 200))
        d.ellipse((rx + 30, y - 336 + bob, rx + 44, y - 322 + bob), fill=(40, 28, 40, 255))
        d.ellipse((rx + 10, y - 316 + bob, rx + 40, y - 304 + bob), fill=(255, 140, 150, 160))
        if who == "girl":
            d.rounded_rectangle((rx - 90, y - 350 + bob, rx - 40, y - 250 + bob), radius=20, fill=(70, 42, 36, 255))
    d.line((x + 80, y - 240, x + 150, y - 230), fill=(46, 92, 156, 255), width=24)
    if rain > 0:
        coat = Image.new("RGBA", img.size, (0, 0, 0, 0))
        cd = ImageDraw.Draw(coat)
        cd.polygon([(x - 200, y - 110), (x - 170, y - 340), (x - 100, y - 440), (x + 20, y - 450), (x + 110, y - 420), (x + 140, y - 300),
                    (x + 200, y - 120)], fill=(80, 170, 255, int(150 * rain)))
        img.alpha_composite(coat)


def s_ride(t):
    rain = ss(156.3, 157.2, t)
    sky = vgrad(W, H, [(0, mix_rgb((90, 170, 250), (110, 120, 140), rain)), (0.6, mix_rgb((200, 230, 255), (160, 166, 176), rain)),
                       (1, (200, 220, 230))])
    img = sky
    L = ride_layers()
    u = t - 151.9
    for k in range(3):
        paste(img, R.anime_cloud(700, 260, 50 + k, lit=(255, 255, 255), shade=(200, 210, 230)), (400 + k * 700 - u * 30) % (W + 700) - 350, 200 + k * 40)
    paste(img, L["far"], -(u * 60) % W, 0, 1, center=False)
    paste(img, L["sawah"], -(u * 180) % W, 0, 1, center=False)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 880, W, H), fill=(80, 80, 90, 255))
    for x in range(-200, W + 200, 200):
        xx = x - (u * 700) % 200
        d.rectangle((xx, 960, xx + 100, 976), fill=(250, 250, 250, 255))
    # roadside posts count the years
    for i, yr in enumerate(["2024", "2025", "2026"]):
        px = W + 200 + i * 900 - u * 700
        if -200 < px < W + 200:
            d.rectangle((px, 700, px + 16, 880), fill=(250, 250, 250, 255))
            d.rounded_rectangle((px - 80, 640, px + 96, 710), radius=10, fill=(40, 140, 80, 255), outline=(255, 255, 255, 255), width=4)
            d.text((px + 8, 675), yr, font=font("DelaGothic.ttf", 40), fill=(255, 255, 255, 255), anchor="mm")
    paste(img, L["palms"], -(u * 400) % W, 60, 1, center=False)
    draw_scooter(img, 900 + math.sin(u) * 20, 900, t, rain)
    if rain > 0:
        R.rain_on_window(img, t, (0, 0, W, H), density=int(260 * rain) + 1, col=(220, 230, 250))
    return img


# ----------------------------------------------------------------------------
# 158.45 - 160.9  votive candles: prayers offered
# ----------------------------------------------------------------------------
def s_candles(t):
    img = vgrad(W, H, [(0, (20, 12, 16)), (1, (50, 26, 20))])
    d = ImageDraw.Draw(img)
    for row in range(4):
        y = 560 + row * 130
        d.rectangle((120 + row * 40, y + 60, W - 120 - row * 40, y + 80), fill=(90, 60, 40, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    rng = random.Random(3)
    n = 0
    for row in range(4):
        y = 560 + row * 130
        for c in range(16 - row):
            x = 200 + row * 40 + c * (1520 - row * 80) / (15 - row)
            lit_t = 158.5 + rng.uniform(0, 2.0)
            d.rounded_rectangle((x - 22, y - 10, x + 22, y + 60), radius=8, fill=(200, 40, 50, 255))
            d.rectangle((x - 16, y - 16, x + 16, y), fill=(250, 240, 220, 255))
            if t > lit_t:
                k = clamp((t - lit_t) / 0.2)
                fl = 1 + 0.15 * math.sin(t * 20 + c)
                d.ellipse((x - 7 * k, y - 18 - 32 * fl * k, x + 7 * k, y - 18), fill=(255, 220, 120, 255))
                d.ellipse((x - 3, y - 20 - 16 * k, x + 3, y - 20), fill=(255, 255, 240, 255))
                gd.ellipse((x - 60, y - 100, x + 60, y + 20), fill=(255, 170, 80, int(90 * k)))
                n += 1
    img = screen_add(img, blur(glow, 30), 1.2)
    # folded hands in the foreground
    hands = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hands)
    hd.polygon([(820, H), (900, 760), (960, 700), (1020, 760), (1100, H)], fill=(40, 24, 24, 255))
    hd.line((960, 710, 960, 900), fill=(70, 44, 40, 255), width=4)
    img.alpha_composite(hands)
    # prayers rising as light
    for i in range(30):
        p = ((t - 158.4) * 0.4 + i / 30) % 1
        paste(img, sparkle_sprite(16), 400 + (i * 97) % 1100 + math.sin(p * 6 + i) * 30, 500 - p * 500, (1 - p) * 0.9)
    return img


# ----------------------------------------------------------------------------
# 160.9 - 163.75  longing: a video call under the same moon
# ----------------------------------------------------------------------------
def s_call(t):
    img = Image.new("RGBA", (W, H))
    left = vgrad(W // 2, H, [(0, (20, 30, 80)), (1, (50, 60, 130))])
    right = vgrad(W // 2, H, [(0, (80, 30, 70)), (1, (150, 70, 120))])
    img.paste(left, (0, 0))
    img.paste(right, (W // 2, 0))
    d = ImageDraw.Draw(img)
    for x0, who in ((0, "boy"), (W // 2, "girl")):
        wx0 = x0 + 120
        d.rectangle((wx0, 100, wx0 + 300, 400), fill=(10, 14, 40, 255), outline=(90, 70, 60, 255), width=12)
        d.ellipse((wx0 + 180, 150, wx0 + 250, 220), fill=(250, 246, 220, 255))
        spr = C.chibi_scaled(0.95, who, "open", "smile", 10, 130 if who == "boy" else 10, True, False, 0)
        if who == "girl":
            spr = C.chibi_scaled(0.95, who, "open", "smile", 130, 10, True, False, 0)
        paste(img, spr, x0 + W // 4 + (60 if who == "boy" else -60), 640)
        # phone in hand showing the other
        px = x0 + W // 4 + (170 if who == "boy" else -170)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((px - 60, 430, px + 60, 640), radius=16, fill=(20, 20, 26, 255))
        d.rectangle((px - 50, 444, px + 50, 626), fill=(250, 220, 230, 255) if who == "boy" else (200, 220, 255, 255))
        other = C.chibi_scaled(0.22, "girl" if who == "boy" else "boy", "happy", "smile", 10, 10, True, False, 0)
        paste(img, other, px, 540)
    d.line((W // 2, 0, W // 2, H), fill=(255, 255, 255, 180), width=6)
    k = 0.5 + 0.5 * math.sin((t - 161) * math.pi * 2 / R.BEAT)
    hs = heart_sprite(int(170 + 30 * k), (255, 90, 130))
    img = screen_add(img, glow_layer(W, H, W // 2, 200, 240, (255, 140, 170), 0.5 + 0.3 * k, 2), 1)
    paste(img, hs, W // 2, 200)
    return img


# ----------------------------------------------------------------------------
# 163.75 - 172.2  family blessing: tumpeng dinner, then prayers in the group chat
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def dinner_bg():
    img = vgrad(W, H, [(0, (250, 220, 170)), (1, (230, 190, 140))])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 700, W, H), fill=(130, 80, 50, 255))
    d.rounded_rectangle((160, 640, 1760, 800), radius=30, fill=(170, 40, 50, 255))
    for x in range(180, 1740, 60):
        d.ellipse((x, 690, x + 36, 726), outline=(255, 214, 120, 255), width=3)
    return img


def draw_tumpeng(img, x, y):
    d = ImageDraw.Draw(img)
    d.ellipse((x - 260, y - 40, x + 260, y + 60), fill=(190, 150, 90, 255))
    for k in range(0, 520, 26):
        d.line((x - 260 + k, y - 30, x - 250 + k, y + 50), fill=(160, 120, 70, 255), width=3)
    d.polygon([(x - 150, y), (x, y - 330), (x + 150, y)], fill=(255, 210, 60, 255))
    d.polygon([(x - 30, y - 290), (x, y - 360), (x + 30, y - 290)], fill=(230, 60, 60, 255))
    for k, (ox, col) in enumerate([(-210, (240, 240, 230)), (-170, (140, 90, 50)), (170, (70, 150, 60)), (210, (200, 90, 40)),
                                   (-120, (250, 250, 240)), (120, (120, 80, 40))]):
        d.ellipse((x + ox - 36, y - 20, x + ox + 36, y + 30), fill=col + (255,))
        if col == (240, 240, 230) or col == (250, 250, 240):
            d.ellipse((x + ox - 14, y - 8, x + ox + 14, y + 16), fill=(255, 190, 40, 255))


CHAT = [(168.1, "L", "Mama", "Selamat pagi, Nak. Sudah makan?"), (169.3, "R", "Ibu", "Pagi! Sehat-sehat ya semuanya"),
        (170.2, "L", "Papa", "Kami doakan kalian berdua"), (171.0, "R", "Bapak", "Amin. Tuhan memberkati")]


def s_family(t):
    if t < 167.9:
        img = dinner_bg().copy()
        for x, who in ((260, "papa"), (500, "mama"), (1420, "mama2"), (1660, "papa2")):
            spr = C.chibi_scaled(0.8, who, "happy", "open" if int(t * 3 + x) % 3 == 0 else "smile", 40, 40, True, False, 0)
            paste(img, spr, x, 470 + abs(math.sin(t * 3 + x)) * 8)
        paste(img, C.chibi_scaled(0.7, "boy", "happy", "smile", 10, 60, True, False, 0), 790, 500)
        paste(img, C.chibi_scaled(0.7, "girl", "happy", "smile", 60, 10, True, False, 0), 1130, 500)
        draw_tumpeng(img, 960, 700)
        for i in range(8):
            p = ((t - 163.8) * 0.5 + i / 8) % 1
            paste(img, heart_sprite(40), 300 + i * 190, 300 - p * 200, (1 - p) * clamp((t - 164.5) / 0.5))
        R.draw_lyric  # noqa
        return img
    img = vgrad(W, H, [(0, (230, 222, 210)), (1, (214, 206, 196))])
    img.alpha_composite(R.kawung_field(W, H, 140, (180, 170, 160, 60)))
    d = ImageDraw.Draw(img)
    x0, x1 = 560, 1360
    d.rounded_rectangle((x0, 30, x1, 1050), radius=40, fill=(236, 229, 221, 255), outline=(40, 40, 50, 255), width=16)
    d.rectangle((x0 + 8, 40, x1 - 8, 170), fill=(40, 120, 100, 255))
    d.text((x0 + 170, 105), "Keluarga Besar", font=vfont("Baloo2.ttf", 50, 800), fill=(255, 255, 255, 255), anchor="lm")
    paste(img, heart_sprite(50, (255, 120, 140)), x0 + 580, 105)
    d.ellipse((x0 + 50, 60, x0 + 140, 150), fill=(250, 216, 188, 255))
    y = 230
    for (t0, side, who, msg) in CHAT:
        if t < t0:
            break
        bub = C.speech_bubble(f"{who}: {msg}", size=36, maxw=520)
        k = pop(t, t0, 0.3)
        bx = x0 + 60 + bub.width / 2 if side == "L" else x1 - 60 - bub.width / 2
        pop_paste(img, bub, bx, y + bub.height / 2, t, t0, 0.3)
        y += bub.height + 10
    if t > 171.4:
        spr, _ = text_sprite("AMIN", "DelaGothic.ttf", 140, (255, 255, 255), stroke=8, stroke_color=(40, 120, 100))
        pop_paste(img, spr.rotate(8, expand=True), 1600, 850, t, 171.5)
    return img


# ----------------------------------------------------------------------------
# 172.2 - 178.35  Papa's pixel RPG status screen: bibit, bobot, bebet
# ----------------------------------------------------------------------------
def pixelate(img, f=6):
    small = img.resize((img.width // f, img.height // f), Image.BILINEAR)
    return small.resize(img.size, Image.NEAREST)


def s_rpg(t):
    img = vgrad(W, H, [(0, (40, 30, 90)), (0.6, (90, 70, 170)), (1, (40, 130, 90))])
    d = ImageDraw.Draw(img)
    for i in range(40):
        x = (i * 211) % W
        y = (i * 97) % 500
        d.rectangle((x, y, x + 8, y + 8), fill=(255, 255, 255, 200 if (int(t * 4) + i) % 3 else 60))
    d.rectangle((0, 820, W, H), fill=(60, 150, 70, 255))
    papa = C.chibi_scaled(1.25, "papa", "happy" if t > 175.7 else "open", "open" if t > 175.7 else "flat", 10,
                          160 if t > 175.7 else 20, True, False, 0)
    paste(img, papa, 450, 560 + (abs(math.sin(t * 8)) * 20 if t > 175.7 else 0))
    img = pixelate(img, 6)
    # status window
    win = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(win)
    x0, y0, x1, y1 = 900, 120, 1800, 760
    wd.rectangle((x0, y0, x1, y1), fill=(20, 24, 70, 235), outline=(255, 255, 255, 255), width=8)
    wd.rectangle((x0 + 14, y0 + 14, x1 - 14, y1 - 14), outline=(120, 140, 255, 255), width=3)
    img.alpha_composite(win)
    label(img, "STATUS: KAMU", x0 + 60, y0 + 70, "PressStart2P.ttf", 40, (255, 230, 120), anchor="tl")
    girl = C.chibi_scaled(0.36, "girl", "happy", "smile", 10, 10, True, False, 0)
    paste(img, pixelate(girl, 3), x1 - 110, y0 + 120)
    for i, (name, t0) in enumerate((("BIBIT", 173.67), ("BOBOT", 174.65), ("BEBET", 175.25))):
        y = y0 + 220 + i * 130
        label(img, name, x0 + 60, y, "PressStart2P.ttf", 38, (255, 255, 255), anchor="tl")
        fill = ease_out_cubic((t - t0) / 0.5)
        d = ImageDraw.Draw(img)
        d.rectangle((x0 + 330, y - 4, x0 + 780, y + 44), outline=(255, 255, 255, 255), width=4)
        if fill > 0:
            d.rectangle((x0 + 336, y + 2, x0 + 336 + 438 * fill, y + 38), fill=(90, 230, 120, 255))
        if fill >= 1:
            label(img, "MAX", x0 + 555, y + 20, "PressStart2P.ttf", 28, (20, 60, 30))
    if t > 175.74:
        spr, _ = text_sprite("LULUS!", "PressStart2P.ttf", 90, (255, 80, 80), stroke=6, stroke_color=(255, 255, 255))
        pop_paste(img, spr.rotate(-12, expand=True), 1350, 690, t, 175.8, 0.3)
        lv, _ = text_sprite("RESTU PAPA +100", "PressStart2P.ttf", 44, (255, 240, 120), stroke=4, stroke_color=(60, 30, 20))
        k = clamp((t - 176.2) / 0.3)
        paste(img, lv, 450, 180 - (t - 176.2) * 40, k * (1 - ss(177.8, 178.3, t)))
        confetti(img, t, 175.9, 60, 4, ((255, 230, 120), (120, 230, 150), (255, 120, 120)))
    return img


# ----------------------------------------------------------------------------
# 178.35 - 183.2  faith and love that calm me: a still lake at dawn
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def lake_bg():
    img = vgrad(W, H, [(0, (170, 190, 230)), (0.45, (250, 214, 210)), (0.55, (255, 236, 214)), (1, (170, 196, 220))])
    d = ImageDraw.Draw(img)
    for k, (base, col) in enumerate([(520, (150, 150, 190)), (560, (120, 130, 170)), (590, (90, 110, 150))]):
        pts = [(0, H)] + [(x, base - 90 * math.exp(-((x - 400 - k * 500) / 380) ** 2) - 60 * math.exp(-((x - 1500 + k * 200) / 300) ** 2))
                          for x in range(0, W + 40, 40)] + [(W, 600), (W, H)]
        d.polygon(pts, fill=col + (255,))
    d.rectangle((0, 600, W, H), fill=(200, 210, 230, 255))
    return img


def s_lake(t):
    img = lake_bg().copy()
    img = screen_add(img, glow_layer(W, H, 1250, 560, 700, (255, 220, 190), 0.6, 2), 1)
    d = ImageDraw.Draw(img)
    for i in range(6):
        p = ((t - 178.3) * 0.25 + i / 6) % 1
        r = 60 + p * 700
        d.ellipse((960 - r, 800 - r * 0.18, 960 + r, 800 + r * 0.18), outline=(255, 255, 255, int(160 * (1 - p))), width=3)
    for i in range(12):
        y = 640 + i * 36
        d.line((200 + (i * 173) % 900, y, 400 + (i * 173) % 900, y), fill=(255, 240, 230, 140), width=3)
    # wooden boat with the couple
    bob = math.sin(t * 1.2) * 8
    d.polygon([(760, 780 + bob), (1160, 780 + bob), (1100, 840 + bob), (820, 840 + bob)], fill=(110, 70, 50, 255))
    d.line((760, 780 + bob, 1160, 780 + bob), fill=(160, 110, 70, 255), width=6)
    for x, who in ((900, "boy"), (1030, "girl")):
        spr = C.chibi_scaled(0.42, who, "closed", "smile", 10, 10, True, True, 0)
        paste(img, spr, x, 690 + bob)
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for k in range(4):
        x = (t * 30 + k * 600) % (W + 800) - 400
        md.ellipse((x - 500, 560 + k * 20, x + 500, 660 + k * 20), fill=(255, 255, 255, 60))
    img.alpha_composite(blur(mist, 30))
    return img


# ----------------------------------------------------------------------------
# 183.2 - 188.7  her cooking: delicious and healthy (+HP)
# ----------------------------------------------------------------------------
INGR = [((220, 30, 40), "chili"), ((150, 70, 140), "shallot"), ((240, 80, 60), "tomato"), ((70, 160, 60), "leaf"),
        ((250, 240, 220), "garlic"), ((255, 170, 40), "carrot")]


def s_cook(t):
    img = Image.new("RGBA", (W, H), (230, 230, 226, 255))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 120):
        for y in range(0, H, 120):
            d.rectangle((x + 3, y + 3, x + 117, y + 117), fill=(244, 244, 240, 255))
    d.rounded_rectangle((460, 140, 1460, 1000), radius=60, fill=(50, 50, 56, 255))
    for (bx, by) in ((700, 330), (1220, 330), (700, 820), (1220, 820)):
        d.ellipse((bx - 110, by - 110, bx + 110, by + 110), outline=(90, 90, 96, 255), width=10)
    cx, cy = 960, 560
    flame = 0.8 + 0.2 * math.sin(t * 20)
    for k in range(12):
        a = k / 12 * math.pi * 2
        d.ellipse((cx + math.cos(a) * 250 - 20, cy + math.sin(a) * 250 - 20 * flame, cx + math.cos(a) * 250 + 20,
                   cy + math.sin(a) * 250 + 20 * flame), fill=(80, 140, 255, 255))
    # wajan (wok)
    d.ellipse((cx - 330, cy - 330, cx + 330, cy + 330), fill=(40, 40, 44, 255))
    d.ellipse((cx - 300, cy - 300, cx + 300, cy + 300), fill=(70, 70, 76, 255))
    d.rounded_rectangle((cx + 320, cy - 30, cx + 620, cy + 30), radius=20, fill=(90, 60, 40, 255))
    # ingredients drop in and get tossed
    rng = random.Random(6)
    for i in range(28):
        col, kind = INGR[i % len(INGR)]
        t0 = 183.3 + i * 0.1
        el = t - t0
        if el < 0:
            continue
        ang = rng.uniform(0, 6.28)
        rad = rng.uniform(20, 230)
        stir = (t - 183.3) * 2.0
        tx = cx + math.cos(ang + stir) * rad
        ty = cy + math.sin(ang + stir) * rad
        drop = 1 - ease_out_cubic(el / 0.4)
        x, y = tx, ty - drop * 700
        r = rng.uniform(18, 34)
        if kind == "chili":
            d.rounded_rectangle((x - r * 1.6, y - r * 0.4, x + r * 1.6, y + r * 0.4), radius=int(r * 0.4), fill=col + (255,))
        elif kind == "leaf":
            d.ellipse((x - r * 1.5, y - r * 0.6, x + r * 1.5, y + r * 0.6), fill=col + (255,))
        else:
            d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
            d.ellipse((x - r * 0.5, y - r * 0.5, x + r * 0.2, y), fill=(255, 255, 255, 90))
    # spatula stirring
    sa = (t - 183.2) * 3
    sx, sy = cx + math.cos(sa) * 120, cy + math.sin(sa) * 120
    d.line((sx, sy, sx + 460, sy - 380), fill=(150, 100, 60, 255), width=26)
    d.rounded_rectangle((sx - 60, sy - 40, sx + 60, sy + 40), radius=16, fill=(190, 190, 196, 255))
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(steam)
    for k in range(6):
        pts = [(cx - 200 + k * 80 + math.sin(t * 3 + j * 0.6 + k) * 20, cy - 100 - j * 40) for j in range(12)]
        sd.line(pts, fill=(255, 255, 255, 110), width=24)
    img.alpha_composite(blur(steam, 14))
    for i, (txt, t0, x, col) in enumerate((("ENAK!", 185.7, 350, (255, 90, 60)), ("+100 HP", 186.9, 1600, (60, 200, 90)),
                                           ("SEHAT!", 187.5, 1560, (60, 150, 255)))):
        spr, _ = text_sprite(txt, "DelaGothic.ttf" if i == 0 else "PressStart2P.ttf", 110 if i == 0 else 56, col,
                             stroke=8, stroke_color=(255, 255, 255))
        pop_paste(img, spr.rotate(10 - i * 8, expand=True), x, 260 + i * 260 - max(0, t - t0) * 30, t, t0)
    for i in range(8):
        p = ((t - 186.9) * 0.6 + i / 8) % 1 if t > 186.9 else -1
        if p >= 0:
            paste(img, heart_sprite(50, (255, 90, 110)), 1500 + math.sin(i * 2) * 150, 900 - p * 600, 1 - p)
    return img


# ----------------------------------------------------------------------------
# 188.7 - 193.9  what else am I searching for?
# ----------------------------------------------------------------------------
def s_search(t):
    img = Image.new("RGBA", (W, H), (250, 250, 252, 255))
    logo = [("C", (66, 133, 244)), ("a", (234, 67, 53)), ("r", (251, 188, 5)), ("i", (52, 168, 83)), ("!", (234, 67, 53))]
    x = 960 - 200
    for ch, col in logo:
        spr, (ax, ay) = text_sprite(ch, "Baloo2.ttf", 150, col, weight=800)
        paste(img, spr, x - ax, 200 - ay, 1, center=False)
        x += vfont("Baloo2.ttf", 150, 800).getlength(ch)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((360, 400, 1560, 500), radius=50, fill=(255, 255, 255, 255), outline=(210, 210, 220, 255), width=4)
    d.ellipse((400, 425, 446, 471), outline=(120, 120, 130, 255), width=6)
    d.line((440, 465, 460, 485), fill=(120, 120, 130, 255), width=6)
    q = "apa lagi yang kucari?"
    n = int(len(q) * clamp((t - 188.8) / 1.6))
    d.text((490, 450), q[:n] + ("|" if int(t * 3) % 2 else ""), font=vfont("Baloo2.ttf", 50, 600), fill=(40, 40, 50, 255), anchor="lm")
    if 190.6 < t < 191.6:
        for k in range(8):
            a = k / 8 * math.pi * 2 + t * 8
            d.ellipse((960 + math.cos(a) * 40 - 8, 640 + math.sin(a) * 40 - 8, 960 + math.cos(a) * 40 + 8,
                       640 + math.sin(a) * 40 + 8), fill=(66, 133, 244, int(255 * (k + 1) / 8)))
    if t > 191.6:
        d.text((380, 560), "Sekitar 1 hasil (0,00 detik)", font=vfont("Baloo2.ttf", 34, 500), fill=(120, 120, 130, 255), anchor="lm")
        k = pop(t, 191.8, 0.4)
        card = Image.new("RGBA", (1200, 300), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 1199, 299), radius=30, fill=(255, 240, 246, 255), outline=(255, 150, 180, 255), width=5)
        cd.text((300, 90), "Kamu", font=vfont("Baloo2.ttf", 80, 800), fill=(200, 40, 90, 255), anchor="lm")
        cd.text((300, 190), "Satu-satunya yang kucari. Sudah ditemukan.", font=vfont("Baloo2.ttf", 40, 600),
                fill=(90, 70, 80, 255), anchor="lm")
        head = C.chibi_scaled(0.5, "girl", "happy", "smile", 10, 10, True, False, 0)
        card.alpha_composite(head.crop((0, 0, head.width, int(head.height * 0.62))), (60, 40))
        pop_paste(img, card, 960, 790, t, 191.8, 0.4)
        if t > 192.5:
            for i in range(10):
                a = i / 10 * math.pi * 2 + t
                paste(img, heart_sprite(40), 960 + math.cos(a) * 700, 790 + math.sin(a) * 200, 0.7)
    return img


# ----------------------------------------------------------------------------
# 193.9 - 200.0  callback: the clock in his room finally stops
# ----------------------------------------------------------------------------
def s_clockstop(t):
    img = vgrad(W, H, [(0, (255, 226, 190)), (1, (250, 196, 150))])
    img = screen_add(img, glow_layer(W, H, 1500, 200, 1200, (255, 250, 220), 0.6, 1.5), 1)
    d = ImageDraw.Draw(img)
    for i in range(6):
        x = 1200 + i * 120
        d.polygon([(x, 0), (x + 60, 0), (x - 500, H), (x - 600, H)], fill=(255, 250, 230, 40))
    cx, cy, r = 960, 470, 320
    d.ellipse((cx - r - 24, cy - r - 24, cx + r + 24, cy + r + 24), fill=(120, 70, 50, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(252, 246, 234, 255))
    for k in range(12):
        a = k / 12 * math.pi * 2
        d.line((cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82, cx + math.cos(a) * r * 0.94, cy + math.sin(a) * r * 0.94),
               fill=(70, 50, 50, 255), width=8)
    stop_t = 198.67
    p = clamp((t - 193.9) / (stop_t - 193.9))
    speed = (1 - p) ** 2
    ang = 12 * (1 - (1 - p) ** 3) * math.pi * 2
    if t >= stop_t:
        ang = 12 * math.pi * 2
    for a, ln, wd, col in ((ang, 0.8, 10, (60, 40, 40)), (ang / 12, 0.55, 16, (60, 40, 40))):
        aa = a - math.pi / 2
        d.line((cx, cy, cx + math.cos(aa) * r * ln, cy + math.sin(aa) * r * ln), fill=col + (255,), width=wd)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(200, 40, 60, 255))
    if t >= stop_t:
        k = clamp((t - stop_t) / 0.4)
        img = screen_add(img, glow_layer(W, H, cx, cy, 600, (255, 240, 200), 0.8 * (1 - k * 0.5), 2), 1)
        for i in range(16):
            a = i / 16 * math.pi * 2
            rr = r + 40 + ease_out_cubic(k) * 160
            paste(img, sparkle_sprite(50), cx + math.cos(a) * rr, cy + math.sin(a) * rr, 1 - clamp((t - stop_t - 0.6) / 0.8))
        label(img, "TING!", cx + 420, cy - 280, "Bangers.ttf", 120, (255, 90, 90), k, stroke=6, stroke_color=(255, 255, 255))
        paste(img, C.chibi_scaled(0.75, "girl", "happy", "open", 150, 10, True, False, 0), 1560, 720, k)
        paste(img, C.chibi_scaled(0.75, "boy", "sparkle", "open", 10, 150, True, False, 0), 360, 720, k)
    else:
        paste(img, C.chibi_scaled(0.75, "boy", "open", "o", 10, 10, True, False, 1), 360, 720)
    return img


# ----------------------------------------------------------------------------
# 200.0 - 206.4  the proposal at the church, golden hour
# ----------------------------------------------------------------------------
def s_proposal(t):
    img = vgrad(W, H, [(0, (250, 150, 110)), (0.5, (255, 200, 140)), (0.75, (255, 230, 180)), (1, (180, 110, 90))])
    img = screen_add(img, glow_layer(W, H, 1500, 620, 900, (255, 240, 200), 0.7, 1.6), 1)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 760), (600, 700), (1300, 720), (W, 690), (W, H), (0, H)], fill=(120, 70, 70, 255))
    ch = R.church_sprite().resize((720, 760), Image.LANCZOS)
    tinted = Image.new("RGBA", ch.size, (100, 50, 60, 255))
    tinted.putalpha(ch.getchannel("A"))
    tinted.alpha_composite(ch.point(lambda v: v) if False else Image.new("RGBA", ch.size, (0, 0, 0, 0)))
    paste(img, ch, 1450, 360)
    R.petals_field(img, t, 44, 16, 200, wind=(-200, 50), size=(20, 38), alpha=0.9)
    # silhouettes: she stands, he kneels
    sil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sil)
    col = (60, 30, 40, 255)
    gx, gy = 1000, 820
    sd.ellipse((gx - 50, gy - 420, gx + 50, gy - 320), fill=col)
    sd.rounded_rectangle((gx - 70, gy - 440, gx + 60, gy - 180), radius=50, fill=col)
    sd.polygon([(gx - 60, gy - 320), (gx + 50, gy - 320), (gx + 120, gy), (gx - 130, gy)], fill=col)
    bx, by = 760, 820
    kneel = ease_in_out((t - 202.4) / 1.4)
    head_y = lerp(by - 440, by - 330, kneel)
    sd.ellipse((bx - 50, head_y, bx + 50, head_y + 100), fill=col)
    sd.polygon([(bx - 60, head_y + 90), (bx + 60, head_y + 90), (bx + 70, by - 160 + (1 - kneel) * -40), (bx - 70, by - 160 + (1 - kneel) * -40)], fill=col)
    sd.polygon([(bx - 60, by - 170), (bx + 90, by - 170), (bx + 110, by), (bx + 60, by), (bx + 40, by - 100), (bx - 60, by)], fill=col)
    arm_x = lerp(bx + 40, bx + 150, kneel)
    sd.line((bx + 30, head_y + 130, arm_x, head_y + 170), fill=col, width=30)
    img.alpha_composite(sil)
    if t > 204.9:
        k = pop(t, 204.9, 0.4)
        rb = Image.new("RGBA", (160, 140), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rb)
        rd.rectangle((30, 70, 130, 130), fill=(160, 30, 50, 255))
        rd.polygon([(30, 70), (130, 70), (120, 20), (40, 20)], fill=(190, 40, 60, 255))
        rd.ellipse((58, 40, 102, 84), outline=(255, 220, 120, 255), width=8)
        rd.polygon([(72, 36), (88, 36), (80, 22)], fill=(220, 240, 255, 255))
        pop_paste(img, rb, arm_x + 30, head_y + 150, t, 204.9, 0.4)
        img = screen_add(img, glow_layer(W, H, arm_x + 30, head_y + 130, 220, (255, 240, 200), k, 2), 1)
        for i in range(10):
            a = i / 10 * math.pi * 2 + t * 2
            paste(img, sparkle_sprite(50), arm_x + 30 + math.cos(a) * 110, head_y + 140 + math.sin(a) * 90, 0.9 * k)
    bars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bars)
    bh = int(120 * ss(200.0, 201.0, t))
    bd.rectangle((0, 0, W, bh), fill=(0, 0, 0, 255))
    bd.rectangle((0, H - bh, W, H), fill=(0, 0, 0, 255))
    img.alpha_composite(bars)
    return img


# ----------------------------------------------------------------------------
# 206.4 - 216.4  blueprint: building a Catholic household (a joglo house with a cross)
# ----------------------------------------------------------------------------
def house_segments():
    cx, gy = 960, 860
    segs = []
    def add(pts, tag):
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b, tag))
    add([(cx - 520, gy), (cx + 520, gy)], "ground")
    add([(cx - 420, gy), (cx - 420, gy - 300), (cx + 420, gy - 300), (cx + 420, gy)], "walls")
    add([(cx - 560, gy - 300), (cx - 300, gy - 460), (cx + 300, gy - 460), (cx + 560, gy - 300)], "roof")
    add([(cx - 300, gy - 460), (cx - 160, gy - 620), (cx + 160, gy - 620), (cx + 300, gy - 460)], "roof")
    add([(cx - 160, gy - 620), (cx - 60, gy - 700), (cx + 60, gy - 700), (cx + 160, gy - 620)], "roof")
    add([(cx - 70, gy), (cx - 70, gy - 190), (cx + 70, gy - 190), (cx + 70, gy)], "door")
    for wx in (cx - 300, cx + 180):
        add([(wx, gy - 230), (wx + 120, gy - 230), (wx + 120, gy - 120), (wx, gy - 120), (wx, gy - 230)], "window")
        add([(wx + 60, gy - 230), (wx + 60, gy - 120)], "window")
    add([(cx, gy - 700), (cx, gy - 860)], "cross")
    add([(cx - 55, gy - 810), (cx + 55, gy - 810)], "cross")
    return segs


SEG_TIMES = {"ground": (206.5, 207.4), "walls": (207.4, 208.9), "roof": (208.9, 209.9), "door": (209.9, 210.6),
             "window": (210.6, 211.6), "cross": (211.63, 212.6)}


def s_blueprint(t):
    fill = ss(213.6, 215.0, t)
    img = vgrad(W, H, [(0, (26, 70, 140)), (1, (18, 50, 110))])
    d = ImageDraw.Draw(img)
    for x in range(0, W, 40):
        d.line((x, 0, x, H), fill=(50, 100, 170, 255) if x % 200 else (70, 120, 190, 255), width=1)
    for y in range(0, H, 40):
        d.line((0, y, W, y), fill=(50, 100, 170, 255) if y % 200 else (70, 120, 190, 255), width=1)
    if fill > 0:
        warm = vgrad(W, H, [(0, (255, 170, 120)), (0.6, (255, 220, 170)), (1, (130, 170, 90))])
        m = Image.new("L", (W, H), int(255 * fill))
        img = Image.composite(warm, img, m)
        d = ImageDraw.Draw(img)
        cx, gy = 960, 860
        body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(body)
        bd.rectangle((cx - 420, gy - 300, cx + 420, gy), fill=(250, 236, 214, int(255 * fill)))
        for (a, b, c) in ((300, 460, 560), (160, 620, 300), (60, 700, 160)):
            pass
        bd.polygon([(cx - 560, gy - 300), (cx - 300, gy - 460), (cx + 300, gy - 460), (cx + 560, gy - 300)], fill=(170, 70, 50, int(255 * fill)))
        bd.polygon([(cx - 300, gy - 460), (cx - 160, gy - 620), (cx + 160, gy - 620), (cx + 300, gy - 460)], fill=(150, 60, 44, int(255 * fill)))
        bd.polygon([(cx - 160, gy - 620), (cx - 60, gy - 700), (cx + 60, gy - 700), (cx + 160, gy - 620)], fill=(130, 50, 40, int(255 * fill)))
        bd.rectangle((cx - 70, gy - 190, cx + 70, gy), fill=(120, 70, 40, int(255 * fill)))
        for wx in (cx - 300, cx + 180):
            bd.rectangle((wx, gy - 230, wx + 120, gy - 120), fill=(255, 210, 120, int(255 * fill)))
        img.alpha_composite(body)
    d = ImageDraw.Draw(img)
    line_col = (255, 255, 255, int(255 * (1 - fill * 0.6)))
    for (a, b, tag) in house_segments():
        t0, t1 = SEG_TIMES[tag]
        p = clamp((t - t0) / (t1 - t0))
        if p <= 0:
            continue
        col = line_col if tag != "cross" else (255, 220, 120, 255)
        e = (lerp(a[0], b[0], p), lerp(a[1], b[1], p))
        d.line((a[0], a[1], e[0], e[1]), fill=col, width=6 if tag != "cross" else 12)
    if t > 211.6:
        k = ss(211.6, 212.6, t)
        img = screen_add(img, glow_layer(W, H, 960, 860 - 780, 260, (255, 220, 130), 0.9 * k, 2), 1)
    # annotations
    if fill < 0.8:
        a = 1 - fill
        for txt, x, y, t0 in (("RUMAH", 330, 560, 209.05), ("TANGGA", 1590, 560, 209.53), ("KATOLIK", 1300, 130, 211.63)):
            if t > t0:
                label(img, txt, x, y, "PressStart2P.ttf", 34, (255, 255, 255), a * clamp((t - t0) / 0.3))
        d = ImageDraw.Draw(img)
        if t > 207.4:
            d.line((540, 900, 1380, 900), fill=(255, 255, 255, int(200 * a)), width=2)
            label(img, "12 m", 960, 930, "PressStart2P.ttf", 24, (255, 255, 255), a)
    if fill > 0.5:
        k = clamp((fill - 0.5) * 2)
        paste(img, C.chibi_scaled(0.62, "boy", "happy", "open", 10, 60, True, False, 0), 560, 900, k)
        paste(img, C.chibi_scaled(0.62, "girl", "happy", "open", 60, 10, True, False, 0), 1360, 900, k)
        R.petals_field(img, t, 61, 14, 213.6, wind=(-150, 60), size=(20, 36), alpha=k)
    return img


# ----------------------------------------------------------------------------
# 216.4 - end  fireworks, and a question with only one answer
# ----------------------------------------------------------------------------
def firework(img, t, t0, x, y, col, n=36, r=320):
    el = t - t0
    if el < 0 or el > 2.2:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if el < 0.35:
        yy = lerp(H, y, el / 0.35)
        d.ellipse((x - 5, yy - 5, x + 5, yy + 5), fill=col + (255,))
    else:
        e = el - 0.35
        rr = ease_out_cubic(e / 1.0) * r
        a = int(255 * clamp(1 - e / 1.8))
        for i in range(n):
            ang = i / n * math.pi * 2
            px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr + e * e * 60
            d.line((x + math.cos(ang) * rr * 0.7, y + math.sin(ang) * rr * 0.7 + e * e * 60, px, py), fill=col + (a,), width=5)
            d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(255, 255, 255, a))
    img.alpha_composite(blur(layer, 2))
    img.alpha_composite(layer)


def s_finale(t):
    img = vgrad(W, H, [(0, (10, 12, 40)), (0.7, (50, 30, 80)), (1, (90, 50, 80))])
    d = ImageDraw.Draw(img)
    cx, gy = 960, 1000
    col = (30, 20, 40, 255)
    d.rectangle((cx - 300, gy - 200, cx + 300, gy), fill=col)
    d.polygon([(cx - 400, gy - 200), (cx - 200, gy - 320), (cx + 200, gy - 320), (cx + 400, gy - 200)], fill=col)
    d.polygon([(cx - 200, gy - 320), (cx - 100, gy - 420), (cx + 100, gy - 420), (cx + 200, gy - 320)], fill=col)
    d.rectangle((cx - 6, gy - 520, cx + 6, gy - 420), fill=(255, 220, 120, 255))
    d.rectangle((cx - 40, gy - 490, cx + 40, gy - 478), fill=(255, 220, 120, 255))
    for wx in (cx - 220, cx + 120):
        d.rectangle((wx, gy - 160, wx + 100, gy - 80), fill=(255, 200, 110, 255))
    img = screen_add(img, glow_layer(W, H, cx, gy - 470, 200, (255, 220, 130), 0.8, 2), 1)
    for i, (t0, x, y, c) in enumerate([(216.5, 400, 300, (255, 90, 120)), (216.9, 1500, 260, (120, 200, 255)),
                                       (217.4, 960, 200, (255, 220, 100)), (218.0, 650, 380, (160, 255, 160)),
                                       (218.6, 1300, 360, (255, 140, 220)), (219.2, 300, 220, (255, 200, 90)),
                                       (219.5, 1650, 420, (200, 150, 255)), (220.0, 960, 300, (255, 255, 255))]):
        firework(img, t, t0, x, y, c)
    # the question card
    if t > 217.0:
        k = pop(t, 217.0, 0.5)
        card = Image.new("RGBA", (900, 460), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 899, 459), radius=40, fill=(255, 250, 244, 245), outline=(255, 150, 180, 255), width=6)
        cd.text((450, 110), "Maukah kamu?", font=vfont("Baloo2.ttf", 90, 800), fill=(180, 40, 80, 255), anchor="mm")
        clicked = t > 219.1
        for bx, txt in ((230, "YA"), (670, "YA!")):
            fillc = (255, 90, 130, 255) if (clicked and txt == "YA!") else (255, 150, 180, 255)
            cd.rounded_rectangle((bx - 170, 250, bx + 170, 380), radius=60, fill=fillc)
            cd.text((bx, 315), txt, font=vfont("Baloo2.ttf", 70, 800), fill=(255, 255, 255, 255), anchor="mm")
        a = 1 - ss(220.4, 220.9, t)
        pop_paste(img, card, 960, 470, t, 217.0, 0.5, a)
        # cursor moves to "YA!" and clicks
        if t < 220.4:
            mp = ease_in_out((t - 217.8) / 1.2)
            mx, my = lerp(1500, 960 + 220, mp), lerp(900, 470 + 90, mp)
            press = 0.85 if 219.05 < t < 219.25 else 1.0
            cur = Image.new("RGBA", (80, 110), (0, 0, 0, 0))
            ImageDraw.Draw(cur).polygon([(4, 4), (4, 90), (26, 70), (44, 106), (58, 100), (40, 64), (72, 64)],
                                        fill=(255, 255, 255, 255), outline=(20, 20, 20, 255))
            cur = cur.resize((int(80 * press), int(110 * press)))
            paste(img, cur, mx, my, 1, center=False)
        if t > 219.1:
            for i in range(30):
                el = t - 219.1
                ang = i / 30 * math.pi * 2
                rr = ease_out_cubic(el / 1.2) * (400 + (i % 4) * 80)
                paste(img, heart_sprite(40 + (i % 3) * 20), 1180 + math.cos(ang) * rr, 560 + math.sin(ang) * rr * 0.7,
                      clamp(1 - el / 1.6))
    if t > 220.5:
        k = clamp((t - 220.5) / 0.4)
        label(img, "Kutemukan Tuhan di Dirimu", 960, 470, "PlayfairItalic.ttf", 110, (255, 246, 230), k, weight=700,
              glow=16, glow_color=(255, 130, 160))
    return img
