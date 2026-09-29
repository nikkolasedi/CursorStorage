import os
import sys
import time

from engine import Frame
from characters import boy, girl, mama, papa

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(out, exist_ok=True)
t0 = time.time()
fr = Frame()
s = 150
boy(fr, 260, 420, s)
girl(fr, 740, 420, s, expr="open", mouth="smile")
mama(fr, 1220, 460, s)
papa(fr, 1680, 440, s)
img = fr.render(0.0)
img.save(os.path.join(out, "cast_sheet.png"))
print("done", time.time() - t0, file=sys.stderr)
