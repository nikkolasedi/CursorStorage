"""Render a 5-second "I love you Agnes" motion graphic to agnes.mp4."""
import math
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
DURATION = 5.0
FRAMES = int(FPS * DURATION)
OUT = "agnes.mp4"

SANS = ImageFont.truetype("fonts/Montserrat.ttf", 64)
try:
    SANS.set_variation_by_name("Light")
except Exception:
    pass
SCRIPT = ImageFont.truetype("fonts/GreatVibes-Regular.ttf", 300)

GOLD = (255, 214, 170)
ROSE = (255, 120, 150)

random.seed(7)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def heart_points(cx, cy, size, n=80):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * size / 32, cy - y * size / 32))
    return pts


def make_background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.65)) ** 2 + ((yy - H * 0.48) / (H * 0.75)) ** 2)
    d = np.clip(d, 0, 1)[..., None]
    center = np.array([92, 18, 44], np.float32)
    edge = np.array([12, 3, 10], np.float32)
    img = center * (1 - d) + edge * d
    img += np.random.default_rng(1).normal(0, 1.5, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


BG = make_background()


class Particle:
    def __init__(self):
        self.x = random.uniform(0, W)
        self.y0 = random.uniform(-100, H + 200)
        self.speed = random.uniform(40, 140)
        self.size = random.uniform(14, 46)
        self.sway = random.uniform(10, 40)
        self.phase = random.uniform(0, 2 * math.pi)
        self.alpha = random.uniform(0.15, 0.55)
        self.is_heart = random.random() < 0.6
        self.color = random.choice([ROSE, (255, 160, 180), GOLD])

    def pos(self, t):
        y = (self.y0 - self.speed * t) % (H + 300) - 150
        x = self.x + math.sin(t * 1.3 + self.phase) * self.sway
        return x, y


PARTICLES = [Particle() for _ in range(55)]


def draw_particles(t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fade_in = ease_in_out(t / 0.8)
    for p in PARTICLES:
        x, y = p.pos(t)
        a = int(255 * p.alpha * fade_in)
        if p.is_heart:
            d.polygon(heart_points(x, y, p.size), fill=p.color + (a,))
        else:
            r = p.size * 0.22
            d.ellipse((x - r, y - r, x + r, y + r), fill=p.color + (a,))
    return layer.filter(ImageFilter.GaussianBlur(2))


LINE1 = "I  L O V E  Y O U"
LINE1_Y = 330
_widths = [SANS.getlength(c) for c in LINE1]
_extra = 8
LINE1_W = sum(_widths) + _extra * (len(LINE1) - 1)

AGNES = "Agnes"
_bbox = SCRIPT.getbbox(AGNES)
AGNES_W = _bbox[2] - _bbox[0]
AGNES_H = _bbox[3] - _bbox[1]
AGNES_X = (W - AGNES_W) / 2 - _bbox[0]
AGNES_Y = 470 - _bbox[1]


def draw_line1(t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = (W - LINE1_W) / 2
    visible = [c for c in LINE1 if c != " "]
    idx = 0
    for c, cw in zip(LINE1, _widths):
        if c != " ":
            start = 0.35 + idx * 0.07
            k = ease_out_cubic((t - start) / 0.6)
            if k > 0:
                dy = (1 - k) * 40
                d.text((x, LINE1_Y + dy), c, font=SANS, fill=GOLD + (int(255 * k),))
            idx += 1
        x += cw + _extra
    return layer, len(visible)


def draw_agnes(t):
    reveal = ease_in_out((t - 1.2) / 1.5)
    if reveal <= 0:
        return None
    text = Image.new("L", (W, H), 0)
    ImageDraw.Draw(text).text((AGNES_X, AGNES_Y), AGNES, font=SCRIPT, fill=255)

    left = (W - AGNES_W) / 2 - 40
    edge = left + (AGNES_W + 80) * reveal
    xs = np.arange(W, dtype=np.float32)
    ramp = np.clip((edge - xs) / 60.0, 0, 1)
    mask = (np.asarray(text, np.float32) * ramp[None, :]).astype(np.uint8)
    return Image.fromarray(mask, "L"), edge, reveal


def compose(t):
    frame = BG.copy().convert("RGBA")
    frame.alpha_composite(draw_particles(t))

    line1, _ = draw_line1(t)
    glow1 = line1.filter(ImageFilter.GaussianBlur(10))
    frame.alpha_composite(glow1)
    frame.alpha_composite(line1)

    agnes = draw_agnes(t)
    beat = 0.0
    if agnes is not None:
        mask, edge, reveal = agnes

        for bt in (3.1, 3.45):
            beat = max(beat, math.exp(-((t - bt) / 0.09) ** 2))

        glow_strength = 0.7 + 0.8 * beat
        glow = Image.new("RGBA", (W, H), ROSE + (0,))
        glow.putalpha(mask.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(min(255, v * glow_strength))))
        frame.alpha_composite(glow)

        solid = Image.new("RGBA", (W, H), (255, 236, 226, 0))
        solid.putalpha(mask)
        frame.alpha_composite(solid)

        if reveal < 1:
            spark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(spark)
            sy = AGNES_Y + _bbox[1] + AGNES_H * 0.55
            for r, a in ((60, 40), (30, 90), (12, 220)):
                sd.ellipse((edge - r, sy - r, edge + r, sy + r), fill=(255, 225, 200, a))
            frame.alpha_composite(spark.filter(ImageFilter.GaussianBlur(8)))

    heart_k = ease_out_back((t - 2.7) / 0.5)
    if heart_k > 0:
        hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hl)
        size = 70 * heart_k * (1 + 0.25 * beat)
        cx, cy = W / 2, 885
        hd.polygon(heart_points(cx, cy, size * 1.25), fill=ROSE + (90,))
        glowh = hl.filter(ImageFilter.GaussianBlur(18))
        hd2 = ImageDraw.Draw(hl)
        hd2.polygon(heart_points(cx, cy, size), fill=(255, 90, 125, 255))
        frame.alpha_composite(glowh)
        frame.alpha_composite(hl)

        line_k = ease_out_cubic((t - 2.9) / 0.6)
        if line_k > 0:
            ld = ImageDraw.Draw(frame)
            half = 260 * line_k
            for sign in (-1, 1):
                x0 = cx + sign * 80
                ld.line((x0, cy, x0 + sign * half, cy), fill=GOLD + (int(170 * line_k),), width=2)

    if beat > 0:
        flash = Image.new("RGBA", (W, H), (255, 110, 140, int(28 * beat)))
        frame.alpha_composite(flash)

    zoom = 1 + 0.035 * ease_in_out(t / DURATION)
    if zoom != 1:
        zw, zh = int(W / zoom), int(H / zoom)
        x0, y0 = (W - zw) // 2, (H - zh) // 2
        frame = frame.crop((x0, y0, x0 + zw, y0 + zh)).resize((W, H), Image.LANCZOS)

    fade = ease_in_out(t / 0.4) * (1 - ease_in_out((t - 4.6) / 0.4))
    if fade < 1:
        black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        frame = Image.blend(black, frame, fade)

    return frame.convert("RGB")


def main():
    proc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", OUT,
        ],
        stdin=subprocess.PIPE,
    )
    for i in range(FRAMES):
        t = i / FPS
        proc.stdin.write(compose(t).tobytes())
        if i in (45, 75, 100, 130):
            compose(t).save(f"preview_{i:03d}.png")
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    main()
