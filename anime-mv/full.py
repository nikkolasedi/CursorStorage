"""Full-song renderer: timeline of scenes, transitions and lyric styles.

Usage:
    python3 full.py                       # whole song -> out/full.mp4
    python3 full.py --stills 40 60 100    # PNG stills
    python3 full.py --start 30 --end 60   # partial render
"""
import argparse
import json
import math
import os
import subprocess
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import render as R
import scenes_a as A
import scenes_b as B
from render import W, H, FPS, clamp, lerp, ss, ease_in_out, ease_out_cubic, blur, glow_layer, screen_add

HERE = os.path.dirname(os.path.abspath(__file__))
SONG_END = 221.59
LYRICS = json.load(open(os.path.join(HERE, "lyrics.json")))

# (start, scene function, transition into this scene, lyric style)
TIMELINE = [
    (0.0, R.compose, None, None),
    (30.0, A.s_flashback, "flash", "vhs"),
    (36.55, A.s_halte, "fade", "grey"),
    (41.5, A.s_routine, "slide", "sub"),
    (46.9, A.s_stained, "iris", "gold"),
    (51.55, A.s_phone, "glitch", "sub"),
    (61.9, A.s_map, "slide", "gold"),
    (66.8, A.s_shatter, "zoom", "sub"),
    (71.9, A.s_megamendung, "flash", "gold"),
    (84.9, A.s_mama, "wipe", "warm"),
    (95.2, A.s_manga, "glitch", "manga"),
    (111.5, A.s_kalau, None, "manga"),
    (115.0, A.s_lanterns, "flash", "sub"),
    (125.4, B.s_happy, "zoom", "pop"),
    (130.4, B.s_match, "slide", "pop"),
    (139.7, B.s_puzzle, "wipe", "ink"),
    (151.9, B.s_ride, "iris", "pop"),
    (158.45, B.s_candles, "fade", "gold"),
    (160.9, B.s_call, "slide", "sub"),
    (163.75, B.s_family, "wipe", "warm"),
    (172.2, B.s_rpg, "glitch", "rpg"),
    (178.35, B.s_lake, "flash", "ink"),
    (183.2, B.s_cook, "slide", "pop"),
    (188.7, B.s_search, "zoom", "ink"),
    (193.9, B.s_clockstop, "iris", "warm"),
    (200.0, B.s_proposal, "flash", "gold"),
    (206.4, B.s_blueprint, "wipe", "blueprint"),
    (216.4, B.s_finale, "flash", "gold"),
]
TRANS_D = 0.4

STYLES = {
    # font, size, y, text colour, sung colour, glow colour, weight, box
    "sub": ("PlayfairItalic.ttf", 76, 930, (255, 255, 255), (255, 214, 120), (120, 90, 255), 600, None),
    "vhs": ("PressStart2P.ttf", 40, 930, (255, 250, 230), (255, 200, 90), (60, 30, 20), None, None),
    "grey": ("CormorantItalic.ttf", 84, 120, (255, 255, 255), (255, 214, 80), (60, 60, 70), 700, None),
    "gold": ("PlayfairItalic.ttf", 76, 960, (255, 248, 230), (255, 206, 110), (200, 90, 40), 600, None),
    "ink": ("CormorantItalic.ttf", 84, 960, (60, 30, 40), (200, 40, 80), None, 700, None),
    "warm": ("Baloo2.ttf", 70, 960, (255, 255, 255), (255, 230, 120), (160, 60, 60), 800, None),
    "manga": ("Bangers.ttf", 74, 990, (0, 0, 0), (200, 20, 40), None, None, "manga"),
    "pop": ("Baloo2.ttf", 76, 970, (255, 255, 255), (255, 240, 120), (220, 60, 110), 800, "stroke"),
    "rpg": ("PressStart2P.ttf", 36, 930, (255, 255, 255), (255, 230, 120), None, None, "rpg"),
    "blueprint": ("PressStart2P.ttf", 36, 1000, (255, 255, 255), (255, 220, 120), (40, 90, 200), None, None),
}


def scene_index(t):
    idx = 0
    for i, (st, *_rest) in enumerate(TIMELINE):
        if t >= st:
            idx = i
    return idx


def transition(a, b, p, kind, t):
    if kind == "fade" or kind is None:
        return Image.blend(a, b, p)
    if kind == "flash":
        out = Image.blend(a, b, ss(0.4, 0.6, p))
        k = 1 - abs(p - 0.5) * 2
        out.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(240 * k ** 1.3))))
        return out
    if kind == "slide":
        e = ease_in_out(p)
        out = Image.new("RGBA", (W, H))
        out.paste(a, (int(-e * W), 0))
        out.paste(b, (int(W - e * W), 0))
        return out
    if kind == "iris":
        r = ease_in_out(p) * 1200 + 1
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=255)
        return Image.composite(b, a, blur(m, 6))
    if kind == "wipe":
        e = ease_in_out(p)
        x = lerp(-400, W + 400, e)
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        md.polygon([(-400, 0), (x + 200, 0), (x - 200, H), (-400, H)], fill=255)
        out = Image.composite(b, a, m)
        edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ed = ImageDraw.Draw(edge)
        ed.line((x + 200, 0, x - 200, H), fill=(255, 214, 120, 255), width=26)
        for k in range(12):
            yy = k * H / 12
            xx = x + 200 - 400 * k / 12
            ed.ellipse((xx - 22, yy - 22, xx + 22, yy + 22), outline=(160, 40, 60, 255), width=6)
        out.alpha_composite(edge)
        return out
    if kind == "zoom":
        e = ease_in_out(p)
        za = R.camera(a, 1 + e * 0.6)
        zb = R.camera(b, 1.3 - e * 0.3)
        return Image.blend(za, zb, e)
    if kind == "glitch":
        src = a if p < 0.5 else b
        arr = np.asarray(src, np.uint8).copy()
        k = 1 - abs(p - 0.5) * 2
        rng = np.random.default_rng(int(t * 97))
        for _ in range(int(14 * k) + 1):
            y0 = int(rng.uniform(0, H - 60))
            hh = int(rng.uniform(10, 80))
            arr[y0:y0 + hh] = np.roll(arr[y0:y0 + hh], int(rng.uniform(-200, 200) * k), axis=1)
        arr[..., 0] = np.roll(arr[..., 0], int(20 * k), axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -int(20 * k), axis=1)
        return Image.fromarray(arr, "RGBA")
    return Image.blend(a, b, p)


def compose_scene(i, t):
    img = TIMELINE[i][1](t)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return img


def split_words(words, fname, size, weight, maxw):
    widths = [R.word_advance(fname, size, w[0], weight) for w in words]
    total = sum(widths) + size * 0.28 * (len(words) - 1)
    if total <= maxw or len(words) < 2:
        return [words]
    best, bi = 1e9, 1
    acc = 0
    for i in range(1, len(words)):
        acc += widths[i - 1]
        d = abs(acc - (total - acc))
        if d < best:
            best, bi = d, i
    return [words[:bi], words[bi:]]


_SCRIM = {}


def scrim(top):
    if top not in _SCRIM:
        a = np.zeros((H, W), np.float32)
        ys = np.arange(H)
        prof = np.clip((ys - 760) / 320, 0, 1) ** 1.5 * 170 if not top else np.clip((300 - ys) / 300, 0, 1) ** 1.5 * 170
        a[:] = prof[:, None]
        img = Image.new("RGBA", (W, H), (10, 6, 20, 0))
        img.putalpha(Image.fromarray(a.astype(np.uint8)))
        _SCRIM[top] = img
    return _SCRIM[top]


def draw_lyrics(img, t):
    for li, line in enumerate(LYRICS):
        if line["start"] < 30.0:
            continue
        nxt = LYRICS[li + 1]["start"] if li + 1 < len(LYRICS) else SONG_END
        if line["start"] - 0.3 <= t <= min(line["end"] + 0.4, nxt - 0.15) + 0.5:
            style = TIMELINE[scene_index(line["start"])][3] or "sub"
            _, _, y, col, _, _, _, box = STYLES[style]
            if sum(col) > 600 and box in (None, "stroke"):
                a = clamp((t - line["start"] + 0.3) / 0.3) * (1 - clamp((t - min(line["end"] + 0.4, nxt - 0.15)) / 0.5))
                paste_scrim = R.with_alpha(scrim(y < 500), a)
                img.alpha_composite(paste_scrim)
            break
    for li, line in enumerate(LYRICS):
        if line["start"] < 30.0:
            continue
        nxt = LYRICS[li + 1]["start"] if li + 1 < len(LYRICS) else SONG_END
        t_in = line["start"] - 0.3
        t_out = min(line["end"] + 0.4, nxt - 0.15)
        if not (t_in <= t <= t_out + 0.5):
            continue
        style = TIMELINE[scene_index(line["start"])][3] or "sub"
        fname, size, y, col, hi, glow_c, weight, box = STYLES[style]
        words = [tuple(w) for w in line["words"]]
        rows = split_words(words, fname, size, weight, 1650)
        lh = size * 1.25
        y0 = y - (len(rows) - 1) * lh
        if box == "manga":
            f = R.vfont(fname, size, weight) if weight else R.font(fname, size)
            maxw = max(sum(R.word_advance(fname, size, w[0], weight) for w in r) + size * 0.28 * (len(r) - 1) for r in rows)
            a = clamp((t - t_in) / 0.2) * (1 - clamp((t - t_out) / 0.3))
            box_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(box_img)
            bd.rectangle((W / 2 - maxw / 2 - 40, y0 - size * 0.9, W / 2 + maxw / 2 + 40, y + size * 0.55),
                         fill=(255, 255, 255, int(250 * a)), outline=(0, 0, 0, int(255 * a)), width=6)
            img.alpha_composite(box_img)
        if box == "rpg":
            a = clamp((t - t_in) / 0.2) * (1 - clamp((t - t_out) / 0.3))
            box_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(box_img)
            bd.rectangle((120, y0 - 80, W - 120, y + 70), fill=(20, 24, 70, int(240 * a)), outline=(255, 255, 255, int(255 * a)), width=8)
            img.alpha_composite(box_img)
            # typewriter
            text = " ".join(w[0] for w in words)
            span = max(0.4, words[-1][1] - words[0][1] + 0.5)
            n = int(len(text) * clamp((t - words[0][1] + 0.1) / span))
            A.label(img, text[:n], 180, y0 - 20, fname, size, col, a, anchor="tl")
            continue
        if box == "stroke":
            for r_i, row in enumerate(rows):
                _stroke_line(img, row, t, W / 2, y0 + r_i * lh, fname, size, col, hi, glow_c, weight, t_out)
            continue
        for r_i, row in enumerate(rows):
            R.draw_lyric(img, row, t, W / 2, y0 + r_i * lh - size * 0.7, fname, size, align="center", color=col, hi=hi,
                         glow=12 if glow_c else 0, glow_color=glow_c or col, weight=weight, out_t=t_out,
                         style="drop" if style in ("manga", "pop") else "rise")


def _stroke_line(img, row, t, x, y, fname, size, col, hi, glow_c, weight, t_out):
    space = size * 0.28
    widths = [R.word_advance(fname, size, w[0], weight) for w in row]
    total = sum(widths) + space * (len(row) - 1)
    cx = x - total / 2
    out_a = 1 - ss(t_out, t_out + 0.4, t)
    for (wt, ws, we), wd in zip(row, widths):
        p = clamp((t - (ws - 0.2)) / 0.3)
        if p > 0 and out_a > 0:
            sung = ss(ws - 0.05, ws + 0.1, t) * (1 - ss(we, we + 0.5, t))
            c = R.mix_rgb(col, hi, sung)
            spr, (ax, ay) = R.text_sprite(wt, fname, size, c, weight=weight, stroke=7, stroke_color=glow_c,
                                          shadow=(5, 7, (60, 20, 50)))
            k = R.ease_out_back(p, 2.2)
            sp = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.BILINEAR)
            bounce = math.sin(clamp((t - ws) / 0.3) * math.pi) * 14 if t > ws else 0
            R.paste(img, sp, cx + wd / 2 - ax + spr.width / 2 - wd / 2 + (0), y - bounce - size * 0.1, out_a * clamp(p * 3))
        cx += wd + space


def compose_full(t):
    i = scene_index(t)
    img = None
    if i + 1 < len(TIMELINE) and TIMELINE[i + 1][2] and t > TIMELINE[i + 1][0] - TRANS_D / 2:
        st = TIMELINE[i + 1][0]
        p = (t - (st - TRANS_D / 2)) / TRANS_D
        img = transition(compose_scene(i, t), compose_scene(i + 1, t), p, TIMELINE[i + 1][2], t)
    elif i > 0 and TIMELINE[i][2] and t < TIMELINE[i][0] + TRANS_D / 2:
        st = TIMELINE[i][0]
        p = (t - (st - TRANS_D / 2)) / TRANS_D
        img = transition(compose_scene(i - 1, t), compose_scene(i, t), p, TIMELINE[i][2], t)
    else:
        img = compose_scene(i, t)
    if t >= 30.0 - 0.3:
        draw_lyrics(img, t)
    return img


def render_frame(t):
    img = compose_full(t)
    fade = ss(0.0, 0.9, t) * (1 - ss(SONG_END - 0.8, SONG_END, t))
    grain = 1.3 if t < R.T_DUSK else 0.8
    return R.finish(img, t, vig=0.85, grain=grain, fade=fade)


def _worker(i):
    return render_frame(i / FPS).tobytes()


def render_video(start, end, out_path, workers):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    frames = list(range(int(round(start * FPS)), int(round(end * FPS))))
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-ss", str(start), "-t", str(end - start), "-i", R.AUDIO, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for n, buf in enumerate(pool.imap(_worker, frames, chunksize=4)):
            proc.stdin.write(buf)
            if n % 150 == 0:
                print(f"frame {n}/{len(frames)} (t={frames[n] / FPS:.1f}s)", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=SONG_END)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(R.OUT, "full.mp4"))
    a = ap.parse_args()
    if a.stills:
        os.makedirs(R.OUT, exist_ok=True)
        for t in a.stills:
            Image.fromarray(render_frame(t)).save(os.path.join(R.OUT, f"full_{t:06.2f}.png"))
            print("still", t, flush=True)
        return
    render_video(a.start, a.end, a.out, a.workers)


if __name__ == "__main__":
    main()
