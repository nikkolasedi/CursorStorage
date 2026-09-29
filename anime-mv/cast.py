"""Original chibi cast: the songwriter (boy), the girl, Mama and Papa."""
import math
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

import render as R

SKIN = (250, 216, 188)
SKIN_SH = (232, 180, 156)
INK = (40, 28, 40)

PALETTES = {
    "boy": dict(hair=(34, 28, 46), top=(46, 92, 156), top2=(230, 196, 120), bottom=(44, 44, 70)),
    "girl": dict(hair=(70, 42, 36), top=(250, 248, 244), top2=(150, 190, 230), bottom=(250, 248, 244)),
    "mama": dict(hair=(40, 30, 36), top=(206, 64, 90), top2=(255, 214, 120), bottom=(120, 70, 44)),
    "papa": dict(hair=(40, 34, 40), top=(130, 84, 50), top2=(230, 190, 120), bottom=(50, 44, 50)),
    "mama2": dict(hair=(52, 36, 32), top=(90, 150, 120), top2=(255, 230, 160), bottom=(90, 60, 50)),
    "papa2": dict(hair=(60, 60, 64), top=(60, 90, 130), top2=(210, 210, 230), bottom=(46, 46, 60)),
}


def _arm(d, s, shoulder, ang_deg, length, col, hand_col):
    a = math.radians(ang_deg)
    ex = shoulder[0] + math.sin(a) * length
    ey = shoulder[1] + math.cos(a) * length
    d.line((shoulder[0] * s, shoulder[1] * s, ex * s, ey * s), fill=col, width=int(34 * s))
    d.ellipse(((shoulder[0] - 17) * s, (shoulder[1] - 17) * s, (shoulder[0] + 17) * s, (shoulder[1] + 17) * s), fill=col)
    d.ellipse(((ex - 19) * s, (ey - 19) * s, (ex + 19) * s, (ey + 19) * s), fill=hand_col)
    return ex, ey


@lru_cache(maxsize=256)
def chibi(who="boy", eyes="open", mouth="smile", arm_l=10, arm_r=10, blush=True, pray=False, look=0):
    """Front-facing chibi. Arm angles in degrees (0 = hanging, 90 = sideways, 170 = raised)."""
    pal = PALETTES[who]
    base = who.rstrip("2")
    w, h = 360, 560
    s = 2
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S = lambda *p: [v * s for v in p]
    cx, hy, hr = 180, 180, 128
    hair = pal["hair"] + (255,)
    top = pal["top"] + (255,)
    top2 = pal["top2"] + (255,)
    bottom = pal["bottom"] + (255,)
    skin = SKIN + (255,)

    # long hair behind (girl), bun (mama)
    if base == "girl":
        d.rounded_rectangle(S(cx - 150, hy - 40, cx + 150, hy + 270), radius=90 * s, fill=hair)
    if base == "mama":
        d.ellipse(S(cx - 70, hy - 175, cx + 70, hy - 60), fill=hair)
        d.ellipse(S(cx - 40, hy - 160, cx - 10, hy - 130), fill=(255, 214, 120, 255))

    # legs
    for lx in (cx - 44, cx + 14):
        d.rounded_rectangle(S(lx, 440, lx + 30, 530), radius=12 * s, fill=bottom if base != "girl" else skin)
        d.rounded_rectangle(S(lx - 8, 516, lx + 36, 546), radius=14 * s, fill=(60, 44, 50, 255))
    # body
    if base in ("girl", "mama"):
        d.polygon(S(cx - 70, 300, cx + 70, 300, cx + 118, 470, cx - 118, 470), fill=top if base == "girl" else bottom)
        if base == "mama":
            # batik sarong: parang stripes clipped to the skirt
            stripes = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sd = ImageDraw.Draw(stripes)
            for k in range(-6, 8):
                x0 = cx + k * 26
                sd.line(S(x0 - 20, 470, x0 + 30, 392), fill=top2, width=5 * s)
            skirt = Image.new("L", img.size, 0)
            ImageDraw.Draw(skirt).polygon(S(cx - 70, 300, cx + 70, 300, cx + 118, 470, cx - 118, 470), fill=255)
            stripes.putalpha(Image.fromarray(np.minimum(np.asarray(stripes.getchannel("A")), np.asarray(skirt))))
            img.alpha_composite(stripes)
            d.polygon(S(cx - 70, 300, cx + 70, 300, cx + 90, 390, cx - 90, 390), fill=top)
            d.ellipse(S(cx - 12, 316, cx + 12, 340), fill=top2)
        else:
            d.line(S(cx - 104, 440, cx + 104, 440), fill=pal["top2"] + (255,), width=6 * s)
            d.polygon(S(cx - 40, 300, cx + 40, 300, cx, 340), fill=pal["top2"] + (255,))
    else:
        d.rounded_rectangle(S(cx - 78, 296, cx + 78, 452), radius=34 * s, fill=top)
        # batik kawung dots on the shirt
        for yy in range(318, 446, 26):
            for xx in range(int(cx - 60), int(cx + 66), 26):
                d.ellipse(S(xx - 5, yy - 3, xx + 5, yy + 3), fill=top2)
        d.polygon(S(cx - 30, 296, cx + 30, 296, cx, 330), fill=skin)
        d.rectangle(S(cx - 78, 430, cx + 78, 452), fill=bottom)
    # arms
    armcol = top if base != "mama" else top
    if pray:
        for sg in (-1, 1):
            d.line(S(cx + sg * 72, 320, cx + sg * 26, 392), fill=armcol, width=34 * s)
            d.ellipse(S(cx + sg * 72 - 17, 303, cx + sg * 72 + 17, 337), fill=armcol)
        d.ellipse(S(cx - 30, 330, cx + 30, 410), fill=skin)
        d.line(S(cx, 336, cx, 404), fill=SKIN_SH + (255,), width=3 * s)
    else:
        _arm(d, s, (cx - 72, 318), -arm_l, 100, armcol, skin)
        _arm(d, s, (cx + 72, 318), arm_r, 100, armcol, skin)
    # neck + head
    d.rectangle(S(cx - 22, 270, cx + 22, 304), fill=SKIN_SH + (255,))
    d.ellipse(S(cx - hr, hy - hr, cx + hr, hy + hr * 0.95), fill=skin)
    # ears
    for sg in (-1, 1):
        d.ellipse(S(cx + sg * hr - 18, hy - 6, cx + sg * hr + 18, hy + 40), fill=skin)

    # hair front
    if base == "boy":
        d.pieslice(S(cx - hr - 8, hy - hr - 14, cx + hr + 8, hy + hr * 0.9), 180, 360, fill=hair)
        rng = random.Random(3)
        for k in range(9):
            x0 = cx - hr + 6 + k * 30
            d.polygon(S(x0 - 8, hy - 30, x0 + 40, hy - 30, x0 + 12 + rng.uniform(-6, 10), hy + 10 + rng.uniform(0, 22)), fill=hair)
        d.polygon(S(cx - hr - 6, hy - 40, cx - hr + 30, hy - 40, cx - hr - 4, hy + 50), fill=hair)
        d.polygon(S(cx + hr + 6, hy - 40, cx + hr - 30, hy - 40, cx + hr + 4, hy + 50), fill=hair)
        d.line(S(cx + 6, hy - hr - 8, cx + 30, hy - hr - 40, cx + 60, hy - hr - 30), fill=hair, width=9 * s)
    elif base == "girl":
        d.pieslice(S(cx - hr - 14, hy - hr - 16, cx + hr + 14, hy + hr * 1.0), 180, 360, fill=hair)
        for k in range(7):
            x0 = cx - hr + 20 + k * 36
            d.ellipse(S(x0 - 18, hy - 50, x0 + 30, hy + 8 + (k % 2) * 10), fill=hair)
        for sg in (-1, 1):
            d.rounded_rectangle(S(cx + sg * (hr - 6) - 22, hy - 30, cx + sg * (hr - 6) + 22, hy + 170), radius=20 * s, fill=hair)
    elif base == "mama":
        d.pieslice(S(cx - hr - 6, hy - hr - 10, cx + hr + 6, hy + hr * 0.8), 180, 360, fill=hair)
        d.chord(S(cx - hr, hy - hr + 10, cx + hr, hy + 40), 180, 360, fill=hair)
        d.line(S(cx - 60, hy - 100, cx + 30, hy - 116), fill=(150, 140, 150, 255), width=5 * s)
    elif base == "papa":
        d.pieslice(S(cx - hr - 4, hy - hr - 6, cx + hr + 4, hy + hr * 0.7), 180, 360, fill=hair)
        # peci (black songkok)
        d.polygon(S(cx - 106, hy - 70, cx + 106, hy - 70, cx + 94, hy - 150, cx - 94, hy - 150), fill=(24, 22, 28, 255))
        d.ellipse(S(cx - 94, hy - 166, cx + 94, hy - 134), fill=(34, 32, 40, 255))
        d.line(S(cx - 104, hy - 84, cx + 104, hy - 84), fill=(200, 170, 100, 255), width=3 * s)

    # face
    ex = (cx - 50 + look * 8, cx + 50 + look * 8)
    ey = hy + 36
    for x in ex:
        if eyes == "closed":
            d.arc(S(x - 22, ey - 10, x + 22, ey + 20), 200, 340, fill=INK + (255,), width=6 * s)
        elif eyes == "happy":
            d.arc(S(x - 22, ey - 4, x + 22, ey + 30), 200, 340, fill=INK + (255,), width=7 * s)
        elif eyes == "flat":
            d.line(S(x - 20, ey + 6, x + 20, ey + 6), fill=INK + (255,), width=6 * s)
        else:
            d.ellipse(S(x - 20, ey - 26, x + 20, ey + 26), fill=INK + (255,))
            d.ellipse(S(x - 17, ey - 6, x + 17, ey + 24), fill=(90, 70, 110, 255) if base != "girl" else (120, 70, 50, 255))
            d.ellipse(S(x - 12, ey - 20, x + 2, ey - 6), fill=(255, 255, 255, 255))
            d.ellipse(S(x + 6, ey + 6, x + 12, ey + 12), fill=(255, 255, 255, 230))
            if eyes == "sparkle":
                d.polygon(S(x + 8, ey - 22, x + 11, ey - 12, x + 20, ey - 10, x + 11, ey - 7, x + 8, ey + 2, x + 5, ey - 7, x - 4, ey - 10, x + 5, ey - 12), fill=(255, 255, 255, 255))
    if base == "papa":
        for x in ex:
            d.ellipse(S(x - 30, ey - 30, x + 30, ey + 30), outline=(30, 30, 40, 255), width=5 * s)
        d.line(S(ex[0] + 30, ey, ex[1] - 30, ey), fill=(30, 30, 40, 255), width=4 * s)
        d.chord(S(cx - 40, ey + 44, cx + 40, ey + 76), 180, 360, fill=(40, 34, 40, 255))
    if blush:
        for x in (cx - 82, cx + 82):
            d.ellipse(S(x - 24, ey + 32, x + 24, ey + 48), fill=(255, 140, 150, 150))
    my = hy + 96
    if mouth == "smile":
        d.arc(S(cx - 20, my - 20, cx + 20, my + 8), 20, 160, fill=INK + (255,), width=5 * s)
    elif mouth == "open":
        d.chord(S(cx - 22, my - 14, cx + 22, my + 22), 0, 180, fill=(170, 60, 70, 255))
        d.chord(S(cx - 12, my + 4, cx + 12, my + 20), 0, 180, fill=(250, 130, 140, 255))
    elif mouth == "o":
        d.ellipse(S(cx - 10, my - 8, cx + 10, my + 14), fill=(170, 60, 70, 255))
    elif mouth == "sad":
        d.arc(S(cx - 18, my, cx + 18, my + 26), 200, 340, fill=INK + (255,), width=5 * s)
    else:
        d.line(S(cx - 14, my + 4, cx + 14, my + 4), fill=INK + (255,), width=5 * s)
    # kamboja hairpin for the girl, lace veil hint
    img = img.resize((w, h), Image.LANCZOS)
    if base == "girl":
        img.alpha_composite(R.kamboja_sprite(70), (cx + 60, hy - 120))
    return img


def scaled(spr, k):
    return spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.LANCZOS)


@lru_cache(maxsize=64)
def chibi_scaled(k, *args, **kw):
    return scaled(chibi(*args, **kw), k)


def speech_bubble(text, fname="Baloo2.ttf", size=54, weight=800, col=(40, 28, 40), spiky=False, maxw=620):
    return _bubble(text, fname, size, weight, col, spiky, maxw)


@lru_cache(maxsize=64)
def _bubble(text, fname, size, weight, col, spiky, maxw):
    f = R.vfont(fname, size, weight)
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if f.getlength(test) > maxw and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = test
    lines.append(cur)
    tw = max(f.getlength(l) for l in lines)
    lh = size * 1.15
    bw, bh = int(tw + 90), int(lh * len(lines) + 70)
    W_, H_ = bw + 80, bh + 110
    s = 2
    img = Image.new("RGBA", (W_ * s, H_ * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0 = 40, 30
    if spiky:
        pts = []
        n = 26
        for i in range(n):
            a = i / n * math.pi * 2
            r = 1.0 if i % 2 == 0 else 1.18
            pts.append(((x0 + bw / 2 + math.cos(a) * bw / 2 * r) * s, (y0 + bh / 2 + math.sin(a) * bh / 2 * r) * s))
        d.polygon(pts, fill=(255, 255, 255, 255), outline=(30, 20, 30, 255))
    else:
        d.polygon([((x0 + 60) * s, (y0 + bh - 10) * s), ((x0 + 40) * s, (y0 + bh + 60) * s), ((x0 + 120) * s, (y0 + bh - 10) * s)],
                  fill=(255, 255, 255, 255))
        d.rounded_rectangle((x0 * s, y0 * s, (x0 + bw) * s, (y0 + bh) * s), radius=40 * s, fill=(255, 255, 255, 255),
                            outline=(40, 28, 40, 255), width=5 * s)
        d.line([((x0 + 62) * s, (y0 + bh - 2) * s), ((x0 + 40) * s, (y0 + bh + 60) * s), ((x0 + 118) * s, (y0 + bh - 2) * s)],
               fill=(40, 28, 40, 255), width=5 * s)
    fs = R.vfont(fname, size * s, weight)
    for i, l in enumerate(lines):
        d.text(((x0 + bw / 2) * s, (y0 + 35 + lh * i + lh / 2) * s), l, font=fs, fill=col + (255,), anchor="mm")
    return img.resize((W_, H_), Image.LANCZOS)
