"""Original cast drawn directly into riso ink layers (bust portraits, idol-anime style)."""
import math
import random

from engine import bezier, T


def mirror(pts):
    return [(-x, y) for x, y in pts]


FACE_R = [(0.0, -1.05), (0.55, -0.95), (0.9, -0.55), (0.93, -0.1), (0.88, 0.25), (0.74, 0.56), (0.5, 0.84), (0.22, 1.02), (0.0, 1.08)]


def face_outline():
    right = FACE_R
    left = mirror(right[::-1])
    return right + left[1:]


def eye(fr, cx, cy, ox, oy, s, side, expr, iris_ink, look=(0, 0), lash=1.0, k=1.18):
    # draw in eye-local units scaled by k around the eye centre
    ox, oy = ox + cx * s * (1 - k), oy + cy * s * (1 - k)
    s = s * k
    P = lambda pts: T(pts, ox, oy, s)
    sg = 1 if side > 0 else -1
    if expr in ("closed", "happy"):
        arc = bezier((cx - 0.24, cy + 0.02), (cx, cy + (0.14 if expr == "closed" else -0.16)), (cx + 0.26, cy + 0.02), n=16)
        fr.stroke("navy", P(arc), 0.07 * s, 0.06 * s)
        for k in range(3 if expr == "closed" else 0):
            x = cx + (k - 1) * 0.12
            fr.stroke("navy", P([(x, cy + 0.1), (x + 0.02 * sg, cy + 0.2)]), 0.025 * s, taper=True)
        return
    h = 0.24 if expr != "surprised" else 0.28
    # eye white area stays paper; iris
    ix, iy = cx + look[0] * 0.08, cy + 0.03 + look[1] * 0.05
    rx, ry = 0.15, 0.2 if expr != "surprised" else 0.17
    fr.ellipse(iris_ink, ((ix - rx) * s + ox, (iy - ry) * s + oy, (ix + rx) * s + ox, (iy + ry) * s + oy), 1.0)
    fr.ellipse("navy", ((ix - rx) * s + ox, (iy - ry) * s + oy, (ix + rx) * s + ox, (iy + ry * 0.2) * s + oy), 0.55)
    fr.ellipse("navy", ((ix - 0.07) * s + ox, (iy - 0.1) * s + oy, (ix + 0.07) * s + ox, (iy + 0.08) * s + oy), 1.0)
    fr.stroke("navy", P(bezier((ix - rx, iy), (ix, iy + ry * 1.25), (ix + rx, iy), n=12)), 0.02 * s, taper=False)
    # highlights knocked out to paper
    fr.knock("ellipse", ((ix - 0.11) * s + ox, (iy - 0.16) * s + oy, (ix - 0.01) * s + ox, (iy - 0.05) * s + oy))
    fr.knock("ellipse", ((ix + 0.05) * s + ox, (iy + 0.07) * s + oy, (ix + 0.1) * s + ox, (iy + 0.12) * s + oy))
    st = [(ix + 0.07, iy - 0.2), (ix + 0.085, iy - 0.135), (ix + 0.15, iy - 0.12), (ix + 0.085, iy - 0.105),
          (ix + 0.07, iy - 0.04), (ix + 0.055, iy - 0.105), (ix - 0.01, iy - 0.12), (ix + 0.055, iy - 0.135)]
    fr.knock("poly", P(st))
    # upper lash: thick-thin with a flick at the outer corner; iris is clipped above it
    lash_pts = bezier((cx - 0.25 * sg, cy - 0.04), (cx - 0.02 * sg, cy - h - 0.02), (cx + 0.3 * sg, cy - 0.1), n=20)
    above = P(lash_pts + [(cx + 0.3 * sg, cy - 0.6), (cx - 0.25 * sg, cy - 0.6)])
    fr.erase_ink(iris_ink, above)
    fr.erase_ink("navy", above)
    fr.stroke("navy", P(lash_pts), 0.05 * s * lash, 0.09 * s * lash, taper=False)
    fr.stroke("navy", P([(cx + 0.27 * sg, cy - 0.1), (cx + 0.36 * sg, cy - 0.18)]), 0.05 * s, taper=True)
    fr.stroke("navy", P([(cx + 0.24 * sg, cy - 0.06), (cx + 0.33 * sg, cy - 0.04)]), 0.03 * s, taper=True)
    # lower lash
    fr.stroke("navy", P(bezier((cx - 0.12 * sg, cy + 0.25), (cx + 0.05 * sg, cy + 0.28), (cx + 0.2 * sg, cy + 0.2), n=10)), 0.025 * s)
    if expr == "cry":
        fr.ellipse("navy", ((cx + 0.02) * s + ox, (cy + 0.3) * s + oy, (cx + 0.08) * s + ox, (cy + 0.42) * s + oy), 0.0)
        fr.knock("poly", P([(cx + 0.05, cy + 0.26), (cx + 0.11, cy + 0.4), (cx + 0.05, cy + 0.45), (cx - 0.01, cy + 0.4)]))


def face(fr, ox, oy, s, expr="smile", mouth="smile", look=(0, 0), iris="orange", blush=0.6, brow=0.0):
    P = lambda pts: T(pts, ox, oy, s)
    outline = face_outline()
    fr.knock("poly", P(outline))
    fr.apply_knock()
    # soft skin shading on one side (orange halftone), outline in navy
    fr.poly("orange", P([(0.5, -0.4), (0.93, -0.1), (0.88, 0.25), (0.74, 0.56), (0.5, 0.84), (0.6, 0.3)]), 0.18)
    fr.stroke("navy", P(outline[3:-3]), 0.02 * s, 0.03 * s, taper=False)
    for side in (-1, 1):
        cx = 0.4 * side
        eye(fr, cx, 0.18, ox, oy, s, side, expr, iris, look)
        # brows
        by = -0.2 - brow * 0.06
        fr.stroke("navy", P(bezier((cx - 0.18 * side, by + 0.03 + brow * 0.04), (cx, by - 0.05), (cx + 0.2 * side, by + 0.02), n=10)), 0.03 * s)
    # nose, mouth
    fr.stroke("navy", P([(0.03, 0.5), (0.0, 0.56)]), 0.025 * s)
    if mouth == "smile":
        fr.stroke("navy", P(bezier((-0.11, 0.72), (0.0, 0.8), (0.12, 0.71), n=10)), 0.03 * s)
    elif mouth == "open":
        fr.poly("navy", P(bezier((-0.13, 0.7), (0.0, 0.93), (0.13, 0.7), n=12)), 1.0)
        fr.poly("pink", P(bezier((-0.07, 0.8), (0.0, 0.9), (0.07, 0.8), n=8)), 1.0)
    elif mouth == "o":
        fr.ellipse("navy", ((-0.06) * s + ox, 0.68 * s + oy, 0.06 * s + ox, 0.84 * s + oy), 1.0)
    elif mouth == "sad":
        fr.stroke("navy", P(bezier((-0.1, 0.78), (0.0, 0.7), (0.1, 0.78), n=10)), 0.03 * s)
    else:
        fr.stroke("navy", P([(-0.08, 0.74), (0.08, 0.74)]), 0.028 * s)
    # blush + anime blush lines
    if blush > 0:
        for side in (-1, 1):
            cx = 0.52 * side
            fr.ellipse("pink", ((cx - 0.2) * s + ox, 0.4 * s + oy, (cx + 0.2) * s + ox, 0.56 * s + oy), blush)
            for k in range(3):
                x = cx - 0.1 + k * 0.08
                fr.stroke("pink", P([(x + 0.03, 0.43), (x - 0.02, 0.53)]), 0.022 * s)


def spiky_bangs(fr, ox, oy, s, n=9, y_top=-1.0, y_tip=-0.05, spread=1.0, seed=2, ink="navy"):
    rng = random.Random(seed)
    P = lambda pts: T(pts, ox, oy, s)
    for i in range(n):
        u = i / (n - 1)
        x = (-0.95 + 1.9 * u) * spread
        tip_y = y_tip + rng.uniform(-0.1, 0.12) - (0.25 if i in (0, n - 1) else 0) * -1
        tip_x = x + rng.uniform(-0.12, 0.12) + (0.08 if u > 0.5 else -0.08)
        w = 0.2 + rng.uniform(0, 0.06)
        base_y = y_top + abs(u - 0.5) * 0.3
        bend = 0.12 if u > 0.5 else -0.12
        mid = (base_y + tip_y) / 2
        fr.poly(ink, P(bezier((x - w, base_y), (x - w * 0.9, mid), (tip_x - bend * 0.8, tip_y - 0.12), (tip_x, tip_y), n=12) +
                       bezier((tip_x, tip_y), (tip_x - bend * 0.2, tip_y - 0.3), (x + w * 0.7, mid - 0.1), (x + w, base_y), n=12)))


def hair_highlight(fr, ox, oy, s, y=-0.72, span=0.7):
    """Angel-ring highlight: erase navy in a band, print pink there."""
    P = lambda pts: T(pts, ox, oy, s)
    arc = lambda x: y + 0.12 - 0.1 * (1 - (x / span) ** 2)
    x0, x1 = -span * 0.15, span * 0.85
    top = [(x0 + (x1 - x0) * i / 16, arc(x0 + (x1 - x0) * i / 16)) for i in range(17)]
    fr.stroke("pink", P(top), 0.035 * s, taper=True)
    for k, L in enumerate((0.16, 0.26, 0.32, 0.24, 0.14)):
        x = x0 + (x1 - x0) * (k + 0.5) / 5
        y0 = arc(x) - L * 0.4
        fr.stroke("navy", P(bezier((x - 0.03, y0), (x + 0.02, y0 + L * 0.5), (x + 0.01, y0 + L), n=8)), 0.05 * s, tone=0.0)


def kamboja(fr, x, y, r, rot=0.0):
    pts_all = []
    for k in range(5):
        a = rot + k * math.tau / 5
        tip = (x + math.cos(a) * r, y + math.sin(a) * r)
        l = (x + math.cos(a - 0.5) * r * 0.55, y + math.sin(a - 0.5) * r * 0.55)
        rr = (x + math.cos(a + 0.35) * r * 0.6, y + math.sin(a + 0.35) * r * 0.6)
        petal = bezier((x, y), l, tip, n=8) + bezier(tip, rr, (x, y), n=8)
        pts_all.append(petal)
    for petal in pts_all:
        fr.knock("poly", petal)
    fr.apply_knock()
    for petal in pts_all:
        fr.stroke("navy", petal, r * 0.06, taper=False)
    fr.ellipse("orange", (x - r * 0.3, y - r * 0.3, x + r * 0.3, y + r * 0.3), 1.0)


def batik_collar(fr, ox, oy, s, ink="orange"):
    P = lambda pts: T(pts, ox, oy, s)
    body = [(-1.6, 2.6), (-1.5, 1.7), (-0.9, 1.35), (-0.32, 1.25), (0, 1.62), (0.32, 1.25), (0.9, 1.35), (1.5, 1.7), (1.6, 2.6)]
    fr.poly(ink, P(body), 1.0)
    # kawung motif knocked out of the shirt
    for row in range(4):
        for col in range(-4, 5):
            cx, cy = col * 0.36 + (row % 2) * 0.18, 1.62 + row * 0.26
            if abs(cx) < 0.12 and cy < 1.7:
                continue
            for a in range(4):
                ang = a * math.pi / 2 + math.pi / 4
                ex, ey = cx + math.cos(ang) * 0.06, cy + math.sin(ang) * 0.06
                fr.knock("ellipse", ((ex - 0.04) * s + ox, (ey - 0.025) * s + oy, (ex + 0.04) * s + ox, (ey + 0.025) * s + oy))
    fr.stroke("navy", P([(-0.32, 1.25), (0, 1.62), (0.32, 1.25)]), 0.03 * s, taper=False)
    fr.stroke("navy", P(body[:4]), 0.03 * s, taper=False)
    fr.stroke("navy", P(body[5:]), 0.03 * s, taper=False)


def neck(fr, ox, oy, s):
    P = lambda pts: T(pts, ox, oy, s)
    fr.poly("orange", P([(-0.26, 0.85), (0.26, 0.85), (0.26, 1.2), (0, 1.4), (-0.26, 1.2)]), 0.28)
    fr.stroke("navy", P([(-0.26, 0.85), (-0.27, 1.3)]), 0.025 * s)
    fr.stroke("navy", P([(0.26, 0.85), (0.27, 1.3)]), 0.025 * s)


# ----------------------------------------------------------------------------
def boy(fr, ox, oy, s, expr="open", mouth="smile", look=(0, 0), headphones=True, blush=0.35):
    P = lambda pts: T(pts, ox, oy, s)
    # hair back mass
    fr.poly("navy", P(bezier((-1.05, 0.3), (-1.35, -1.55), (0.1, -1.5), n=20) + bezier((0.1, -1.5), (1.4, -1.5), (1.05, 0.3), n=20)))
    neck(fr, ox, oy, s)
    batik_collar(fr, ox, oy, s, "orange")
    fr.apply_knock()
    face(fr, ox, oy, s, expr, mouth, look, iris="orange", blush=blush)
    spiky_bangs(fr, ox, oy, s, n=9, y_top=-1.1, y_tip=-0.12, seed=4)
    # side locks
    for sg in (-1, 1):
        fr.poly("navy", P([(0.86 * sg, -0.7), (1.06 * sg, -0.2), (0.98 * sg, 0.42), (0.86 * sg, 0.05)]))
    # ahoge
    fr.stroke("navy", P(bezier((0.05, -1.45), (0.3, -1.85), (0.55, -1.6), n=12)), 0.08 * s, 0.02 * s)
    hair_highlight(fr, ox, oy, s, -0.95, 0.75)
    if headphones:
        band = bezier((-1.08, -0.05), (-1.25, -1.85), (0, -1.62), n=20) + bezier((0, -1.62), (1.25, -1.85), (1.08, -0.05), n=20)[1:]
        fr.stroke("orange", P(band), 0.1 * s, taper=False)
        for sg in (-1, 1):
            fr.ellipse("orange", ((1.05 * sg - 0.2) * s + ox, -0.25 * s + oy, (1.05 * sg + 0.2) * s + ox, 0.3 * s + oy), 1.0)
            fr.ellipse("navy", ((1.05 * sg - 0.09) * s + ox, -0.12 * s + oy, (1.05 * sg + 0.09) * s + ox, 0.17 * s + oy), 0.5)


def girl(fr, ox, oy, s, expr="open", mouth="smile", look=(0, 0), veil=True, blush=0.6, flower=True):
    P = lambda pts: T(pts, ox, oy, s)
    if veil:
        # lace mantilla behind the hair: pink halftone with a scalloped edge
        edge = []
        for i in range(29):
            a = math.pi * (1.05 + i / 28 * 0.9)
            edge.append((math.cos(a) * 1.55, -0.35 + math.sin(a) * 1.35))
        fr.poly("pink", P(edge + [(1.55, 1.4), (1.3, 2.6), (-1.3, 2.6), (-1.55, 1.4)]), 0.22)
        for i in range(0, 28, 2):
            a0 = math.pi * (1.05 + i / 28 * 0.9)
            a1 = math.pi * (1.05 + (i + 2) / 28 * 0.9)
            p0 = (math.cos(a0) * 1.55, -0.35 + math.sin(a0) * 1.35)
            p1 = (math.cos(a1) * 1.55, -0.35 + math.sin(a1) * 1.35)
            mid = ((p0[0] + p1[0]) / 2 * 1.08, (p0[1] + p1[1]) / 2 * 1.08 - 0.03)
            fr.stroke("pink", P(bezier(p0, mid, p1, n=8)), 0.03 * s, taper=False)
    # long hair behind
    fr.poly("navy", P(bezier((-1.0, -0.6), (-1.6, 1.4), (-1.3, 3.0), n=20) + [(-0.6, 3.0), (-0.7, 1.2)] +
                     [(0.7, 1.2), (0.6, 3.0)] + bezier((1.3, 3.0), (1.6, 1.4), (1.0, -0.6), n=20) +
                     bezier((1.0, -0.6), (0.6, -1.6), (0, -1.55), n=10) + bezier((0, -1.55), (-0.6, -1.6), (-1.0, -0.6), n=10)))
    neck(fr, ox, oy, s)
    # white blouse with a pink ribbon, lace collar
    body = [(-1.5, 2.8), (-1.35, 1.75), (-0.8, 1.38), (-0.3, 1.28), (0, 1.5), (0.3, 1.28), (0.8, 1.38), (1.35, 1.75), (1.5, 2.8)]
    fr.stroke("navy", P(body[:4]), 0.03 * s, taper=False)
    fr.stroke("navy", P(body[5:]), 0.03 * s, taper=False)
    fr.poly("pink", P([(-0.2, 1.52), (0, 1.62), (0.2, 1.52), (0.25, 1.78), (0, 1.66), (-0.25, 1.78)]), 1.0)
    for k in range(9):
        x = -0.8 + k * 0.2
        fr.stroke("navy", P(bezier((x, 1.4 + abs(x) * 0.08), (x + 0.1, 1.5 + abs(x) * 0.08), (x + 0.2, 1.4 + abs(x) * 0.08), n=6)), 0.018 * s, taper=False)
    face(fr, ox, oy, s, expr, mouth, look, iris="orange", blush=blush)
    # soft bangs (rounded clumps) + side locks framing the face
    rng = random.Random(9)
    for i in range(8):
        u = i / 7
        x = -0.9 + 1.8 * u
        tip = (x + (0.1 if u > 0.5 else -0.1), -0.2 + rng.uniform(-0.05, 0.1))
        w = 0.2
        fr.poly("navy", P(bezier((x - w, -1.0), (x - w * 0.3, -0.5), tip, n=10) + bezier(tip, (x + w * 0.8, -0.55), (x + w, -1.0), n=10)))
    fr.poly("navy", P(bezier((0, -1.1), (-0.8, -1.25), (-1.0, -0.6), n=10) + [(0, -0.8)]))
    fr.poly("navy", P(bezier((0, -1.1), (0.8, -1.25), (1.0, -0.6), n=10) + [(0, -0.8)]))
    for sg in (-1, 1):
        fr.poly("navy", P(bezier((0.85 * sg, -0.7), (1.1 * sg, 0.4), (0.8 * sg, 1.4), n=14) + [(0.72 * sg, 0.9), (0.84 * sg, 0.0)]))
    hair_highlight(fr, ox, oy, s, -0.98, 0.7)
    if flower:
        kamboja(fr, ox + 0.78 * s, oy - 0.82 * s, 0.34 * s, rot=0.3)


def mama(fr, ox, oy, s, expr="happy", mouth="open", look=(0, 0)):
    P = lambda pts: T(pts, ox, oy, s)
    fr.ellipse("navy", (ox - 0.7 * s, oy - 2.05 * s, ox + 0.7 * s, oy - 0.95 * s), 1.0)
    fr.poly("navy", P(bezier((-1.0, 0.1), (-1.3, -1.45), (0, -1.4), n=16) + bezier((0, -1.4), (1.3, -1.45), (1.0, 0.1), n=16)))
    neck(fr, ox, oy, s)
    body = [(-1.6, 2.6), (-1.5, 1.7), (-0.9, 1.35), (-0.32, 1.25), (0, 1.8), (0.32, 1.25), (0.9, 1.35), (1.5, 1.7), (1.6, 2.6)]
    fr.poly("pink", P(body), 1.0)
    for k in range(20):
        x, y = -1.3 + (k % 5) * 0.62 + (k // 5 % 2) * 0.3, 1.65 + (k // 5) * 0.24
        fr.knock("ellipse", ((x - 0.05) * s + ox, (y - 0.05) * s + oy, (x + 0.05) * s + ox, (y + 0.05) * s + oy))
    fr.apply_knock()
    fr.ellipse("orange", (ox - 0.12 * s, oy + 1.7 * s, ox + 0.12 * s, oy + 1.94 * s), 1.0)
    face(fr, ox, oy, s, expr, mouth, look, blush=0.5)
    fr.poly("navy", P(bezier((-0.95, -0.2), (-0.9, -1.25), (0.1, -1.15), n=14) + bezier((0.1, -1.15), (0.9, -1.2), (0.95, -0.2), n=14) +
                     bezier((0.95, -0.2), (0.4, -0.75), (0.0, -0.8), n=10) + bezier((0.0, -0.8), (-0.4, -0.75), (-0.95, -0.2), n=10)))
    hair_highlight(fr, ox, oy, s, -1.02, 0.6)
    fr.ellipse("orange", (ox - 0.55 * s, oy - 1.85 * s, ox - 0.3 * s, oy - 1.6 * s), 1.0)


def papa(fr, ox, oy, s, expr="happy", mouth="smile", look=(0, 0)):
    P = lambda pts: T(pts, ox, oy, s)
    fr.poly("navy", P(bezier((-1.0, 0.0), (-1.2, -1.2), (0, -1.2), n=12) + bezier((0, -1.2), (1.2, -1.2), (1.0, 0.0), n=12)))
    neck(fr, ox, oy, s)
    batik_collar(fr, ox, oy, s, "orange")
    fr.apply_knock()
    face(fr, ox, oy, s, expr, mouth, look, blush=0.25)
    for sg in (-1, 1):
        fr.poly("navy", P([(0.98 * sg, -0.66), (0.72 * sg, -0.66), (0.8 * sg, -0.35), (0.88 * sg, -0.05), (0.96 * sg, -0.3)]))
    fr.poly("navy", P([(-0.98, -0.62), (0.98, -0.62), (0.88, -1.4), (-0.88, -1.4)]))
    fr.ellipse("navy", (ox - 0.88 * s, oy - 1.5 * s, ox + 0.88 * s, oy - 1.3 * s), 1.0)
    fr.stroke("orange", P([(-0.97, -0.72), (0.97, -0.72)]), 0.05 * s, taper=False)
    for sg in (-1, 1):
        cx = 0.4 * sg
        pts = [(cx + math.cos(a) * 0.3, 0.2 + math.sin(a) * 0.27) for a in [i / 24 * math.tau for i in range(25)]]
        fr.stroke("navy", T(pts, ox, oy, s), 0.035 * s, taper=False)
    fr.stroke("navy", P([(-0.1, 0.18), (0.1, 0.18)]), 0.03 * s, taper=False)
    fr.poly("navy", P(bezier((-0.3, 0.66), (0, 0.52), (0.3, 0.66), n=10) + bezier((0.3, 0.66), (0, 0.6), (-0.3, 0.66), n=10)))
