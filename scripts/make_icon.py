"""Render the app icon (PNG + Windows ICO) from the idle cat sprite: python scripts/make_icon.py"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from tinypaws.sprites import PALETTE, SPRITES  # noqa: E402

app = QApplication([])
rows = SPRITES['idle']
img = QImage(len(rows[0]), len(rows), QImage.Format_ARGB32)
img.fill(0)
for y, r in enumerate(rows):
    for x, c in enumerate(r):
        if c != '.':
            img.setPixelColor(x, y, QColor(PALETTE[c]))
big = img.scaled(240, 240, Qt.KeepAspectRatio, Qt.FastTransformation)
icon = QImage(256, 256, QImage.Format_ARGB32)
icon.fill(0)
from PySide6.QtGui import QPainter  # noqa: E402
p = QPainter(icon)
p.drawImage((256 - big.width()) // 2, (256 - big.height()) // 2, big)
p.end()
out = os.path.join(ROOT, 'packaging')
assert icon.save(os.path.join(out, 'tinypaws.png'))
assert icon.save(os.path.join(out, 'tinypaws.ico'), 'ICO'), 'Qt ICO plugin missing'
print('icons written')
