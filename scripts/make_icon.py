"""Render the app icon from the HD tuxedo cat: python scripts/make_icon.py

Writes tinypaws/icon.png (runtime: window/tray), packaging/tinypaws.png (bundles; PyInstaller
converts it to .ico/.icns) and packaging/tinypaws.ico.
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QRadialGradient  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
N = 512
sheet = QImage(os.path.join(ROOT, 'assets', 'pets', 'cat', 'tuxedo', 'sheet.png')).convertToFormat(QImage.Format_ARGB32)
cat = sheet.copy(0, 0, 120, 120)  # idle: sitting, facing the viewer
box = [120, 120, 0, 0]
for y in range(120):
    for x in range(120):
        if cat.pixelColor(x, y).alpha() >= 128:
            box = [min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y)]
cat = cat.copy(box[0], box[1], box[2] - box[0] + 1, box[3] - box[1] + 1)
k = int(N * 0.78 / max(cat.width(), cat.height()))  # whole-pixel scale keeps it crisp
big = cat.scaled(cat.width() * k, cat.height() * k, Qt.IgnoreAspectRatio, Qt.FastTransformation)

icon = QImage(N, N, QImage.Format_ARGB32)
icon.fill(0)
p = QPainter(icon)
p.setRenderHint(QPainter.Antialiasing)
r = QRectF(N * 0.03, N * 0.03, N * 0.94, N * 0.94)
path = QPainterPath()
path.addRoundedRect(r, N * 0.2, N * 0.2)
g = QLinearGradient(0, 0, 0, N)
g.setColorAt(0, QColor('#ffcf6b'))
g.setColorAt(1, QColor('#ff7a59'))
p.fillPath(path, g)
glow = QRadialGradient(QPointF(N / 2, N * 0.42), N * 0.45)
glow.setColorAt(0, QColor(255, 255, 255, 120))
glow.setColorAt(1, QColor(255, 255, 255, 0))
p.fillPath(path, glow)
x0, y0 = (N - big.width()) // 2, int(N * 0.93) - big.height()
# white sticker outline: the silhouette stamped around the cat
sil = big.copy()
sil.fill(0)
sp = QPainter(sil)
sp.drawImage(0, 0, big)
sp.setCompositionMode(QPainter.CompositionMode_SourceIn)
sp.fillRect(sil.rect(), QColor('white'))
sp.end()
o = max(4, k)
for dx, dy in ((-o, 0), (o, 0), (0, -o), (0, o), (-o, -o), (o, o), (-o, o), (o, -o)):
    p.drawImage(x0 + dx, y0 + dy, sil)
p.setRenderHint(QPainter.Antialiasing, False)
p.drawImage(x0, y0, big)
p.end()

for path_, img in ((os.path.join(ROOT, 'tinypaws', 'icon.png'), icon),
                   (os.path.join(ROOT, 'packaging', 'tinypaws.png'), icon)):
    assert img.save(path_), path_
assert icon.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(
    os.path.join(ROOT, 'packaging', 'tinypaws.ico'), 'ICO')
print('icons written')
