"""Partial repaints must be pixel-identical to full repaints: no ghost trails."""
import os
import random
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtGui import QImage, QPainter, QRegion  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication([])

from tinypaws import brain  # noqa: E402
from tinypaws.app import Renderer  # noqa: E402

W, H, S = 900, 420, 3


def full(r, items):
    img = QImage(W, H, QImage.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    r.paint(p, items, W)
    p.end()
    return img


class PartialRepaint(unittest.TestCase):
    def check(self, make, frames=240, species='cat'):
        r = Renderer(S)
        pet = brain.Pet(W, H, scale=S, rng=random.Random(5), species=species)
        pet.x = 300
        pet.set_windows([('w', 520, 150, 300, 270)])
        pet.play(make())
        canvas = full(r, [])
        prev = []
        for i in range(frames):
            pet.update(1 / 30)
            items = pet.render()
            dirty = QRegion()
            for rect in r.bounds(prev, W) + r.bounds(items, W):
                dirty += rect
            p = QPainter(canvas)
            p.setClipRegion(dirty)
            p.setCompositionMode(QPainter.CompositionMode_Clear)  # what Qt does for a translucent widget
            p.fillRect(canvas.rect(), 0)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            r.paint(p, items, W)
            p.end()
            prev = items
            if i % 20 == 19:
                self.assertEqual(canvas, full(r, items), 'ghost pixels at frame %d' % i)

    def test_walk_run_and_bubbles(self):
        self.check(lambda: brain.Meme('party', prio=brain.P_USER))
        self.check(lambda: brain.Walk(10, speed=3, prio=brain.P_USER))

    def test_scenes(self):
        for make in (lambda: brain.HypeTrain(2, ['Keksi', 'Mausi']), lambda: brain.GigaChad(lang='de'),
                     lambda: brain.Cinema()):
            self.check(make, frames=400)

    def test_memes_and_climb(self):
        for name in ('bonk', 'thisisfine', 'scare', 'visitor', 'achievement'):
            self.check(lambda name=name: brain.Meme(name, prio=brain.P_USER), frames=160)
        self.check(lambda: brain.Climb('w', nap=1, prio=brain.P_USER), frames=600)
        self.check(lambda: brain.Walk(800, style='run', prio=brain.P_USER), frames=120, species='bird')


if __name__ == '__main__':
    unittest.main()
