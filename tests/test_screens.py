"""Multi-monitor (issue #3): neighbour detection + pets wandering across simulated screens."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from tinypaws.screens import exits, neighbour

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Topology(unittest.TestCase):
    #   [0 1920x1040][1 2560x1000]   [3 far away]
    #   [2 below 0]
    RECTS = [(0, 0, 1920, 1040), (1920, 0, 2560, 1000), (0, 1080, 1920, 1040), (9000, 0, 800, 600)]

    def test_neighbours(self):
        self.assertEqual(neighbour(self.RECTS, 0, 1), 1)
        self.assertEqual(neighbour(self.RECTS, 1, -1), 0)
        self.assertIsNone(neighbour(self.RECTS, 0, -1))
        self.assertIsNone(neighbour(self.RECTS, 1, 1))     # gap to screen 3
        self.assertIsNone(neighbour(self.RECTS, 2, 1))     # screen 1 does not overlap vertically enough
        self.assertEqual(exits(self.RECTS, 0), (1,))
        self.assertEqual(exits(self.RECTS, 3), ())

    def test_small_vertical_overlap_is_not_a_door(self):
        self.assertIsNone(neighbour([(0, 0, 100, 100), (100, 80, 100, 100)], 0, 1))


SCRIPT = r'''
import json, sys
from PySide6.QtWidgets import QApplication
app = QApplication([])
from tinypaws import app as A, brain, settings
from PySide6.QtGui import QGuiApplication
cfg = dict(settings.DEFAULTS, first_run_done=True, obs=False, roam=True, screen=0, scale=4)
c = A.TinyPaws(app, cfg)
out = {'screens': [(s.availableGeometry().getRect(), s.devicePixelRatio()) for s in QGuiApplication.screens()]}
p = c.pet
out['exits0'] = list(p.exits)
p.x = p.maxx - 10
p.play(brain.Roam(1, prio=brain.P_USER))
for _ in range(30 * 20):
    c.tick_dt = 1 / 30
    p.update(1 / 30)
    if p.left_by:
        c._roam_over(p.left_by)
        break
for _ in range(30 * 5):
    p.update(1 / 30)
out['screen_after'] = c.cfg['screen']
out['overlay'] = c.overlay.geometry().getRect()
out['pet'] = [p.x, p.y, p.floor, p.W, p.H]
out['exits1'] = list(p.exits)
c.cfg['screen'] = 7  # monitor unplugged
c._screens_changed()
out['fallback'] = [c.cfg['screen'], c.overlay.geometry().getRect()]
print('RESULT' + json.dumps(out))
'''


class Wandering(unittest.TestCase):
    def test_walks_onto_the_next_monitor(self):
        with tempfile.TemporaryDirectory() as d:
            conf = os.path.join(d, 'screens.json')
            with open(conf, 'w') as fh:
                json.dump({'screens': [
                    {'name': 'A', 'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'logicalDpi': 96, 'dpr': 1},
                    {'name': 'B', 'x': 1920, 'y': 0, 'width': 2560, 'height': 1440, 'logicalDpi': 96, 'dpr': 2}]}, fh)
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen:configfile=' + conf, XDG_CONFIG_HOME=d,
                       XDG_CURRENT_DESKTOP='none', PYTHONPATH=ROOT)
            res = subprocess.run([sys.executable, '-c', SCRIPT], env=env, capture_output=True, text=True, timeout=120)
            line = [ln for ln in res.stdout.splitlines() if ln.startswith('RESULT')]
            self.assertTrue(line, res.stderr[-2000:])
            out = json.loads(line[0][6:])
        if len(out['screens']) < 2:
            self.skipTest('this Qt offscreen plugin ignores the screen config')
        self.assertEqual(out['exits0'], [1])
        self.assertEqual(out['screen_after'], 1)
        self.assertEqual(out['overlay'], out['screens'][1][0])     # overlay moved to monitor B
        x, y, floor, w, h = out['pet']
        self.assertEqual((w, h), tuple(out['screens'][1][0][2:]))  # pet world = monitor B
        self.assertTrue(0 <= x <= w and y <= floor + 1e-6)         # walked in, standing on B's floor
        self.assertEqual(out['exits1'], [-1])
        self.assertEqual(out['fallback'][0], 0)                    # unplugged -> primary


if __name__ == '__main__':
    unittest.main()
