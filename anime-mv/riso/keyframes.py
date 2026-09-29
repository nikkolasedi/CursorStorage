"""Nine riso-print keyframes for 'Kutemukan Tuhan di Dirimu' (style frames for feedback)."""
import math
import os
import random
import sys
from multiprocessing import Pool

from engine import Frame, W, H, bezier, T
from characters import boy, girl, mama, papa, eye, kamboja
from ui import (grad, radial, sunburst, giant, date_tag, caption_card, toast, lyric, print_marks,
                paper_box, check, heart, church, fit, MONO, MONO_B, SERIF_I, HEAVY, BLACK)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def kf1_title(fr):
    radial(fr, "pink", 1300, 560, 900, 0.55, 0.0)
    sunburst(fr, "orange", 1300, 560, n=36, tone=0.18, rot=0.05)
    ox, oy, s = 1300, 560, 1350
    eye(fr, 0, 0, ox, oy, s, 1, "open", "orange", k=1.0)
    church(fr, None, ox + 0.035 * s, oy + 0.17 * s, 0.028 * s, knock=True)
    fr.apply_knock()
    fr.text("navy", (90, 250), "KUTEMUKAN", HEAVY, 190)
    fr.text("navy", (90, 460), "TUHAN", HEAVY, 190)
    fr.text("orange", (90, 670), "DI DIRIMU", HEAVY, 190)
    fr.text("navy", (96, 900), "sebuah dokumenter tentang hati yang menunggu", SERIF_I, 50)
    fr.rect("pink", (96, 930, 700, 938))
    date_tag(fr, "2023.09.05", "rewind")
    toast(fr, 96, 110, "STATUS: MENUNGGU", "hari ke-0001 / ??? ", w=470, icon="pink")
    print_marks(fr, "KTDD  01/09  00:05  PROLOG")


def kf2_verse1(fr):
    grad(fr, "orange", (0, 0, W, H), 0.0, 0.45)
    giant(fr, "MENUNGGU", "pink", W / 2, 400, 520, tone=1.0)
    # notebook with a hand-written staff
    o = -170
    paper_box(fr, (1000, 700 + o, 1860, 1010 + o), outline="navy")
    fr.rect("pink", (1000, 700 + o, 1860, 716 + o))
    for i in range(5):
        y = 780 + o + i * 22
        fr.line("navy", [(1040, y), (1820, y)], 2.4)
    for k, (x, dy) in enumerate([(1120, 30), (1230, 0), (1340, 44), (1450, -20), (1560, 22), (1690, -8)]):
        y = 820 + o + dy * 0.8
        fr.ellipse("navy", (x - 16, y - 11, x + 16, y + 11))
        fr.line("navy", [(x + 14, y), (x + 14, y - 80)], 4)
    fr.text("navy", (1040, 960 + o), "lagu untukmu (draft 37)", SERIF_I, 44, anchor="lm")
    boy(fr, 640, 520, 250, expr="open", mouth="flat", look=(0.6, 0.9), blush=0.2)
    date_tag(fr, "2023.09.05", "rewind")
    toast(fr, W - 600, 150, "MENUNGGU...", "0412 hari  |  lagu: 37 draft", w=540)
    caption_card(fr, "PENGKHOTBAH 3:11", "semua indah tepat di waktu-Nya  (parafrase)", x=70, y=120)
    lyric(fr, "Sudah lama ku menunggu, sampai selesai kutulis lagu")
    print_marks(fr, "KTDD  02/09  00:11  VERSE 1")


def kf3_verse2(fr):
    rng = random.Random(3)
    for _ in range(140):
        x, y, l = rng.uniform(-100, W), rng.uniform(-100, H), rng.uniform(40, 140)
        fr.line("navy", [(x, y), (x + l * 0.25, y + l)], 2, tone=0.5)
    x0, y0, x1, y1 = 140, 230, 1260, 700
    paper_box(fr, (x0 - 40, y0 - 100, x1 + 40, y1 + 90), outline="navy")
    for i in range(6):
        y = y0 + i * (y1 - y0) / 5
        fr.line("navy", [(x0, y), (x1, y)], 1.6, tone=0.6)
        fr.text("navy", (x0 - 14, y), f"{100 - i * 20}", MONO, 20, anchor="rm")
    for i, yr in enumerate(("2023", "2024", "2025")):
        x = x0 + i * (x1 - x0) / 2
        fr.text("navy", (x, y1 + 36), yr, MONO_B, 24, anchor="mm")
    sy = (y1 - y0) / 580
    pts = [(x0, y0 + 60 * sy), (x0 + 120, y0 + 30 * sy), (x0 + 250, y0 + 180 * sy), (x0 + 380, y0 + 150 * sy), (x0 + 520, y0 + 330 * sy),
           (x0 + 650, y0 + 300 * sy), (x0 + 800, y0 + 470 * sy), (x0 + 950, y0 + 440 * sy), (x1, y1 - 20)]
    fr.poly("pink", pts + [(x1, y1), (x0, y1)], 0.35)
    fr.line("pink", pts, 9)
    fr.line("navy", pts, 3)
    fr.ellipse("orange", (x1 - 22, y1 - 42, x1 + 22, y1 + 2))
    fr.text("navy", (x0, y0 - 60), "HARAPAN (%)", MONO_B, 34, anchor="lm")
    fr.text("orange", (x0 + 560, y0 - 58), "tampaknya aku terbiasa", SERIF_I, 42, anchor="lm")
    giant(fr, "RUSUK?", "orange", 1600, 300, 230, maxw=540)
    boy(fr, 1600, 720, 180, expr="cry", mouth="sad", look=(-0.3, 0.6), headphones=False, blush=0.1)
    date_tag(fr, "2024.06.14", "rewind")
    caption_card(fr, "KEJADIAN 2:21-22", "tulang rusuk yang dulu hilang  (parafrase)", x=100, y=H - 240)
    toast(fr, 900, H - 225, "3 THN = 1.095 HARI", "kabar baru: 0", w=420, icon="pink")
    lyric(fr, "Saat itu tak banyak harapan", y=H - 60, size=50, box=True)
    print_marks(fr, "KTDD  03/09  00:37  VERSE 2")


def phone_church_photo(fr, x0, y0, x1, y1):
    grad(fr, "orange", (x0, y0, x1, y1), 0.7, 0.1)
    grad(fr, "pink", (x0, y0, x1, y1), 0.0, 0.6)
    church(fr, "navy", (x0 + x1) / 2 + 120, y1 - 60, 110, tone=0.85)
    fr.rect("navy", (x0, y1 - 60, x1, y1), tone=0.6)


def kf4_fyp(fr):
    sunburst(fr, "pink", 960, 560, n=28, tone=1.0, rot=0.02)
    for i, ch in enumerate("FYP"):
        giant(fr, ch, "orange", 330, 250 + i * 300, 330)
    px0, py0, px1, py1 = 700, 70, 1220, 1110
    fr.rect("navy", (px0 - 24, py0 - 24, px1 + 24, py1), radius=60)
    paper_box(fr, (px0, py0 + 40, px1, py1), radius=30, outline=None)
    ph = (px0 + 20, py0 + 130, px1 - 20, py0 + 610)
    phone_church_photo(fr, *ph)
    girl(fr, px0 + 170, py0 + 420, 80, expr="open", mouth="smile", look=(0.4, 0), blush=0.5)
    fr.apply_knock()
    fr.clear((px0, ph[3], px1, py1))
    fr.ellipse("pink", (px0 + 24, py0 + 64, px0 + 76, py0 + 116))
    fr.text("navy", (px0 + 92, py0 + 90), "@kamu  /  Gereja St. ???", MONO_B, 22, anchor="lm")
    heart(fr, "pink", px0 + 60, ph[3] + 50, 30)
    fr.text("navy", (px0 + 108, ph[3] + 50), "1 suka  (aku)", MONO_B, 26, anchor="lm")
    fr.text("navy", (px0 + 30, ph[3] + 100), "gereja yang mungkin", SERIF_I, 40)
    fr.text("navy", (px0 + 30, ph[3] + 146), "hanya aku yang tahu", SERIF_I, 40)
    heart(fr, "orange", 1560, 520, 230)
    heart(fr, "navy", 1580, 540, 230, tone=0.3)
    date_tag(fr, "2025.03.02", "play")
    toast(fr, W - 620, 150, "NOTIFIKASI", "1 postingan untukmu", w=500)
    toast(fr, W - 560, 780, "ALGORITMA?", "atau rencana-Nya.", w=480, icon="pink")
    lyric(fr, "Tapi fotomu di gereja itu, diam-diam melintas di FYP-ku", y=H - 90)
    print_marks(fr, "KTDD  04/09  00:57  PRE-CHORUS")


def kf5_reveal(fr):
    radial(fr, "orange", 1250, 480, 1000, 0.6, 0.0)
    sunburst(fr, "pink", 1250, 480, n=40, tone=0.5)
    rng = random.Random(5)
    for _ in range(9):
        kamboja(fr, rng.uniform(900, 1850), rng.uniform(80, 1000), rng.uniform(26, 50), rng.uniform(0, 6))
    girl(fr, 1260, 470, 250, expr="open", mouth="smile", look=(-0.3, 0), blush=0.7)
    fr.text("navy", (90, 110), "PARAS", HEAVY, 165)
    fr.text("orange", (90, 300), "+ IMAN", HEAVY, 165)
    fr.line("navy", [(96, 520), (640, 520)], 10)
    fr.text("navy", (90, 550), "= SATU", HEAVY, 165)
    fr.text("pink", (90, 740), "INSAN", HEAVY, 165)
    fr.text("navy", (560, 850), "(masih ada,", SERIF_I, 44, anchor="lm")
    fr.text("navy", (560, 896), "ternyata)", SERIF_I, 44, anchor="lm")
    date_tag(fr, "2025.03.02", "play")
    lyric(fr, "Bahwa yang cantik paras dan iman masih bisa kutemukan dalam satu insan", size=56)
    print_marks(fr, "KTDD  05/09  01:12  PRE-CHORUS")


def gauge(fr, cx, cy, r, val, label):
    for i in range(0, 181, 3):
        a = math.radians(180 + i)
        ink = "pink" if i / 180 < val else "navy"
        rr = r * (1.0 if i % 15 else 1.06)
        fr.line(ink, [(cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82), (cx + math.cos(a) * rr, cy + math.sin(a) * rr)],
                7 if i % 15 == 0 else 4)
    a = math.radians(180 + 180 * val)
    fr.stroke("navy", [(cx - math.cos(a) * 30, cy - math.sin(a) * 30), (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)], 16, 4, taper=False)
    fr.ellipse("orange", (cx - 34, cy - 34, cx + 34, cy + 34))
    fr.text("navy", (cx, cy + 120), label, HEAVY, 190, anchor="mm")


def kf6_mama(fr):
    grad(fr, "pink", (0, 0, W, H), 0.55, 0.15, vertical=False)
    giant(fr, "TUHAN", "orange", 520, 230, 330, maxw=920)
    mama(fr, 500, 640, 215, expr="happy", mouth="open")
    paper_box(fr, (1060, 170, 1840, 880), radius=24)
    fr.text("navy", (1100, 230), "P(JODOH | di tangan Tuhan)", MONO_B, 32, anchor="lm")
    gauge(fr, 1450, 600, 300, 0.97, "99,9%")
    fr.text("navy", (1100, 835), "sumber: kata Mama  /  Amsal 19:14", SERIF_I, 38, anchor="lm")
    date_tag(fr, "2025.05.18", "play")
    lyric(fr, "Kata Mama jodoh ada di tangan Tuhan")
    print_marks(fr, "KTDD  06/09  01:26  CHORUS")


def kf7_kalau(fr):
    inks = ("orange", "pink", "navy")
    labels = (("A", "tidak pindah kerja"), ("B", "tidak pindah kota"), ("C", "tidak foto di gereja"))
    pw = W / 3
    for i, ink in enumerate(inks):
        x0 = i * pw
        grad(fr, ink, (x0, 0, x0 + pw, H), 0.75 if ink != "navy" else 0.4, 0.25 if ink != "navy" else 0.08)
        cx = x0 + pw / 2
        fr.text("navy", (cx, 150), f"SKENARIO {labels[i][0]}", MONO_B, 40, anchor="mm")
        fr.text("navy", (cx, 210), labels[i][1], SERIF_I, 52, anchor="mm")
        if i == 0:
            fr.rect("navy", (cx - 140, 380, cx + 140, 560), radius=14)
            fr.rect("navy", (cx - 50, 340, cx + 50, 400), radius=12)
            fr.knock("rect", (cx - 30, 360, cx + 30, 386))
        elif i == 1:
            pin = [(cx + math.cos(a) * 110, 420 + math.sin(a) * 110) for a in [math.pi * (0.8 + 1.4 * k / 30) for k in range(31)]] + [(cx, 620)]
            fr.poly("navy", pin)
            fr.knock("ellipse", (cx - 45, 375, cx + 45, 465))
            fr.stroke("navy", bezier((cx - 260, 700), (cx, 600), (cx + 260, 700)), 10, taper=False)
        else:
            church(fr, "pink", cx, 620, 100)
        fr.apply_knock()
        fr.text("navy", (cx, 820), "peluang bertemu", MONO, 28, anchor="mm")
        fr.text("navy", (cx, 900), "0,0%", HEAVY, 120, anchor="mm")
    size = fit("KALAU SAJA", HEAVY, 400, W - 60)
    fr.text("navy", (W / 2 + 12, 612), "KALAU SAJA", HEAVY, size, anchor="mm")
    fr.apply_knock()
    fr.knock("text", (W / 2, 600), "KALAU SAJA", HEAVY, size, "mm")
    date_tag(fr, "∞.∞.∞", "alt")
    lyric(fr, "...yang perlahan berubah menjadi rasa syukur", y=H - 70, size=54)
    print_marks(fr, "KTDD  07/09  01:40  CHORUS")


def kf8_papa(fr):
    grad(fr, "orange", (0, 0, W, H), 0.2, 0.6)
    giant(fr, "RESTU", "pink", 500, 190, 300, maxw=860)
    papa(fr, 500, 680, 205, expr="happy", mouth="smile")
    cx0, cy0, cx1, cy1 = 1010, 150, 1840, 880
    paper_box(fr, (cx0, cy0, cx1, cy1), outline="navy", ow=6)
    fr.rect("navy", (cx0, cy0, cx1, cy0 + 110))
    fr.knock("text", ((cx0 + cx1) / 2, cy0 + 56), "RAPOR CALON MENANTU", HEAVY, 70, "mm")
    rows = (("BIBIT", "keturunan baik"), ("BOBOT", "iman & kasih"), ("BEBET", "masakannya enak"))
    for i, (k, v) in enumerate(rows):
        y = cy0 + 190 + i * 150
        fr.text("navy", (cx0 + 50, y), k, HEAVY, 96, anchor="lm")
        fr.text("navy", (cx0 + 330, y + 6), v, SERIF_I, 50, anchor="lm")
        fr.rect("orange", (cx1 - 150, y - 50, cx1 - 50, y + 50), radius=12)
        check(fr, "navy", cx1 - 130, y + 2, 64)
        fr.line("navy", [(cx0 + 40, y + 85), (cx1 - 40, y + 85)], 2, tone=0.7)
    # rotated stamp
    scx, scy, r = 1620, 740, 105
    ring = [(scx + math.cos(a) * r, scy + math.sin(a) * r) for a in [k / 60 * math.tau for k in range(61)]]
    fr.line("pink", ring, 10)
    fr.line("pink", [(scx + math.cos(a) * r * 0.82, scy + math.sin(a) * r * 0.82) for a in [k / 60 * math.tau for k in range(61)]], 4)
    fr.text("pink", (scx, scy - 10), "DIRESTUI", HEAVY, 52, anchor="mm")
    fr.text("pink", (scx, scy + 44), "- PAPA -", MONO_B, 22, anchor="mm")
    fr.text("navy", (cx0 + 50, cy1 - 70), "Semua ada di dirimu.", SERIF_I, 52, anchor="lm")
    date_tag(fr, "2026.06.21", "play")
    lyric(fr, "Kata Papa bibit bobot bebet, semua ada di dirimu")
    print_marks(fr, "KTDD  08/09  02:52  CHORUS 2")


def kf9_outro(fr):
    radial(fr, "pink", 960, 560, 1100, 0.9, 0.2)
    sunburst(fr, "orange", 960, 700, n=32, tone=0.35)
    giant(fr, "MAUKAH?", "navy", W / 2, 190, 300, tone=1.0)
    boy(fr, 330, 640, 190, expr="open", mouth="open", look=(0.8, 0), headphones=False, blush=0.6)
    girl(fr, 1590, 620, 190, expr="surprised", mouth="o", look=(-0.8, 0), blush=0.9)
    # ring box on a paper spotlight
    bx, by = 960, 700
    fr.knock("ellipse", (bx - 290, by - 290, bx + 290, by + 290))
    fr.apply_knock()
    fr.line("navy", [(bx + math.cos(a) * 290, by + math.sin(a) * 290) for a in [k / 60 * math.tau for k in range(61)]], 5)
    fr.rect("navy", (bx - 150, by + 10, bx + 150, by + 190), radius=18)
    fr.poly("navy", [(bx - 150, by + 10), (bx - 130, by - 170), (bx + 130, by - 170), (bx + 150, by + 10)])
    lid = [(bx - 118, by - 8), (bx - 104, by - 150), (bx + 104, by - 150), (bx + 118, by - 8)]
    fr.erase_ink("navy", lid)
    fr.poly("pink", lid, 0.55)
    fr.rect("orange", (bx - 150, by + 10, bx + 150, by + 34))
    ring = [(bx + math.cos(a) * 58, by + 95 + math.sin(a) * 42) for a in [k / 48 * math.tau for k in range(49)]]
    fr.rect("navy", (bx - 90, by + 60, bx + 90, by + 170), radius=14, tone=0.0)
    fr.rect("pink", (bx - 90, by + 60, bx + 90, by + 170), radius=14, tone=0.3)
    fr.line("orange", ring, 15)
    fr.line("navy", [(bx + math.cos(a) * 66, by + 95 + math.sin(a) * 50) for a in [k / 48 * math.tau for k in range(49)]], 3)
    gem = [(bx, by + 18), (bx + 30, by + 50), (bx, by + 66), (bx - 30, by + 50)]
    fr.erase_ink("navy", gem)
    fr.poly("orange", gem)
    fr.line("navy", gem + [gem[0]], 3)
    fr.knock("poly", [(bx - 4, by + 26), (bx + 12, by + 48), (bx - 4, by + 56), (bx - 16, by + 48)])
    for ang in range(200, 341, 35):
        a = math.radians(ang)
        fr.stroke("navy", [(bx + math.cos(a) * 190, by + 40 + math.sin(a) * 190), (bx + math.cos(a) * 250, by + 40 + math.sin(a) * 250)], 8)
    paper_box(fr, (660, 330, 1260, 440), radius=18)
    fr.text("navy", (690, 355), "SISA 1 PERTANYAAN", MONO_B, 26)
    for i, lbl in enumerate(("YA", "YA!")):
        x = 690 + i * 280
        fr.rect("orange" if i == 0 else "pink", (x, 390, x + 250, 428), radius=10)
        fr.text("navy", (x + 125, 409), lbl, MONO_B, 26, anchor="mm")
    date_tag(fr, "2026.09.29", "live")
    lyric(fr, "Maukah kamu membangun rumah tangga Katolik bersamaku?", y=H - 90, size=60)
    print_marks(fr, "KTDD  09/09  03:28  OUTRO")


FRAMES = [kf1_title, kf2_verse1, kf3_verse2, kf4_fyp, kf5_reveal, kf6_mama, kf7_kalau, kf8_papa, kf9_outro]


def run(i):
    fn = FRAMES[i]
    fr = Frame()
    fn(fr)
    img = fr.render(t=i * 0.7)
    path = os.path.join(OUT, f"kf{i + 1:02d}_{fn.__name__.split('_', 1)[1]}.png")
    img.save(path)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    idx = [int(a) - 1 for a in sys.argv[1:]] or range(len(FRAMES))
    with Pool(4) as p:
        for path in p.imap(run, idx):
            print(path)
