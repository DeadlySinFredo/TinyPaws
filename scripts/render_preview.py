"""Render scene snapshots to PNG offscreen (visual check without a desktop).

usage: python scripts/render_preview.py out.png
"""
import os
import random
import sys

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from tinypaws import brain  # noqa: E402
from tinypaws.app import Renderer  # noqa: E402

W, H, S = 640, 240, 3
SHOTS = [('idle', None, 0.5), ('sleep', lambda: brain.Sleep(5), 2), ('jump', lambda: brain.Jump(), 0.35),
         ('pizza', lambda: brain.Emote(('surprised', 'happy'), 3, 1, prop='pizza', drop=True, bubble='PixelFuchs92: Pizza?'), 1.2),
         ('hype', lambda: brain.HypeTrain(3, ['Keksi', 'Mausi', 'Tom']), 5.5),
         ('giga', lambda: brain.GigaChad(lang='de'), 3.0), ('cinema', lambda: brain.Cinema(), 5.0)]

app = QApplication([])
r = Renderer(S)
out = QImage(W, H * len(SHOTS), QImage.Format_ARGB32)
out.fill(QColor('#5a6b7d'))
p = QPainter(out)
for i, (name, make, secs) in enumerate(SHOTS):
    pet = brain.Pet(W, H, scale=S, rng=random.Random(3))
    pet.x = 200
    pet.play(make() if make else brain.Idle(99, prio=brain.P_USER))
    for _ in range(int(secs * 30)):
        pet.update(1 / 30)
    p.save()
    p.translate(0, i * H)
    p.fillRect(0, H - 1, W, 1, QColor('#000'))
    r.paint(p, pet.render(), W)
    r.text(p, name, 40, 20, 14, '#ffffff')
    p.restore()
p.end()
out.save(sys.argv[1] if len(sys.argv) > 1 else 'preview.png')
