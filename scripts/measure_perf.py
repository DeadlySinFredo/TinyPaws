"""Measure TinyPaws CPU/RAM on the real desktop: idle, sleeping, walking (issue #3 performance).

usage: python scripts/measure_perf.py [seconds-per-phase]   (stop the normal TinyPaws first)
Prints CPU % of one core and RSS per phase, plus repaints/s and repainted area.
"""
import os
import resource
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tinypaws import settings as _settings  # noqa: E402
from tinypaws.app import _platform_setup  # noqa: E402

# work on a throw-away copy of the settings: measuring must never change the user's real config
_real = _settings.config_dir() / 'settings.json'
_tmp = tempfile.mkdtemp(prefix='tinypaws-measure-')
os.makedirs(os.path.join(_tmp, 'tinypaws'))
if _real.exists():
    shutil.copy(_real, os.path.join(_tmp, 'tinypaws', 'settings.json'))
os.environ['XDG_CONFIG_HOME'] = _tmp
_platform_setup()
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
from tinypaws import app as A, brain, settings  # noqa: E402

SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 15
cfg = dict(settings.load(), companions=[], obs=False, twitch_channel='', twitch_client_id='', climb=False)
c = A.TinyPaws(app, cfg)
for key in filter(None, os.environ.get('TP_COMPANIONS', '').split(',')):  # e.g. dog/husky,fox/red,bird/canary
    c.add_companion(key)
stats = {'paints': 0, 'area': 0}
orig = c.overlay.paintEvent


def counting(e):
    stats['paints'] += 1
    stats['area'] += e.rect().width() * e.rect().height()
    orig(e)


c.overlay.paintEvent = counting
p = c.pet
phases = [
    ('idle', lambda: p.play(brain.Idle(10 ** 6, prio=brain.P_SCENE + 1))),
    ('sleep', lambda: p.play(brain.Sleep(10 ** 6, prio=brain.P_SCENE + 1))),
    ('walk', None),
]
results, state = [], {}


def cpu():
    t = os.times()
    return t.user + t.system


def walker():
    if state.get('name') != 'walk':
        return
    for q in [p] + [comp['pet'] for comp in c.companions]:
        if not isinstance(q.action, brain.Walk):
            q.action = None
            q.play(brain.Walk(q.rng.uniform(0, q.maxx), prio=brain.P_SCENE + 1))


def start(i):
    if i == len(phases):
        for r in results:
            print('%-6s CPU %5.1f %%  RSS %4d MB  repaints/s %5.1f  area/repaint %7d px' % r)
        app.quit()
        return
    name, setup = phases[i]
    for q in [p] + [comp['pet'] for comp in c.companions]:
        q.action, q.queue = None, []
        if setup and q is not p:
            q.play(brain.Sleep(10 ** 6, prio=brain.P_SCENE + 1) if name == 'sleep' else brain.Idle(10 ** 6, prio=brain.P_SCENE + 1))
    if setup:
        setup()
    state.update(name=name)
    QTimer.singleShot(2000, lambda: begin(i))  # settle


def begin(i):
    stats.update(paints=0, area=0)
    state.update(c0=cpu(), t0=time.monotonic())
    QTimer.singleShot(int(SECS * 1000), lambda: end(i))


def end(i):
    dt = time.monotonic() - state['t0']
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
    results.append((phases[i][0], 100 * (cpu() - state['c0']) / dt, rss, stats['paints'] / dt,
                    stats['area'] // max(1, stats['paints'])))
    start(i + 1)


w = QTimer()
w.timeout.connect(walker)
w.start(200)
QTimer.singleShot(1500, lambda: start(0))
app.exec()
