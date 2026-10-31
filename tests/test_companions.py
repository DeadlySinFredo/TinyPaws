"""Several pets at once (issue #3): social behaviour, management, OBS sprites, limits."""
import json
import os
import random
import tempfile
import unittest
import urllib.request

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QPointF  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication([])

from tinypaws import app as A, brain, settings  # noqa: E402
from tinypaws.sprites import SIZES  # noqa: E402

W, H, S = 1920, 1080, 4


def pair(a='cat', b='dog'):
    p, q = (brain.Pet(W, H, scale=S, rng=random.Random(i), species=sp) for i, sp in ((1, a), (2, b)))
    p.x, q.x = 200, 1400
    p.friends, q.friends = [q], [p]
    return p, q


def run(pets, secs):
    for _ in range(int(secs * 30)):
        for p in pets:
            p.update(1 / 30)
            for it in p.render():
                if it[0] == 'sprite':
                    assert it[1] in SIZES, it[1]


class Social(unittest.TestCase):
    def test_follow_catches_up(self):
        p, q = pair()
        q.play(brain.Idle(60, prio=brain.P_USER))
        p.play(brain.Follow(q, 40, prio=brain.P_USER))
        run([p, q], 25)  # 1100 px at ~67 px/s
        self.assertLess(abs(p.x - (q.x - q.facing * 18 * S)), 4 * S)

    def test_nap_together(self):
        p, q = pair('fox', 'rabbit')
        a = brain.NapTogether(q, prio=brain.P_USER)
        p.play(a)
        slept = False
        for _ in range(30 * 20):
            run([p, q], 1 / 30)
            slept = slept or (p.frame == 'sleep' and q.sleeping)
        self.assertTrue(slept)
        self.assertLess(abs(p.x - q.x), 20 * S)

    def test_play_ball_between_them(self):
        p, q = pair('dog', 'bird')
        a = brain.PlayTogether(q, prio=brain.P_USER)
        p.play(a)
        while not a.met:
            run([p, q], 1 / 30)
        run([p, q], 0.5)
        balls = [it for it in p.render() if it[0] == 'sprite' and it[1] == 'ball']
        self.assertEqual(len(balls), 1)
        lo, hi = sorted((p.cx, q.cx))
        self.assertTrue(lo - 8 * S <= balls[0][2] <= hi + 8 * S)

    def test_random_life_with_friends_stays_valid(self):
        p, q = pair('dragon', 'cat')
        run([p, q], 120)
        for x in (p, q):
            self.assertTrue(0 <= x.x <= x.maxx or isinstance(x.action, brain.Meme))


class Management(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.get(k) for k in ('XDG_CONFIG_HOME', 'XDG_CURRENT_DESKTOP')}
        os.environ.update(XDG_CONFIG_HOME=self.tmp.name, XDG_CURRENT_DESKTOP='none')
        self.c = A.TinyPaws(APP, dict(settings.DEFAULTS, first_run_done=True, obs=True, obs_port=8794))

    def tearDown(self):
        self.c._stop_obs()
        for comp in self.c.companions:
            comp['handle'].close()
        for k, v in self.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def test_add_toggle_remove_and_limit(self):
        c = self.c
        for key in ('dog/husky', 'fox/red', 'bird/canary'):
            self.assertTrue(c.add_companion(key))
        self.assertFalse(c.add_companion('rabbit/wild'))  # limit: 3 companions
        self.assertEqual([e['key'] for e in settings.load()['companions']], ['dog/husky', 'fox/red', 'bird/canary'])
        drawn = set()
        for _ in range(60):
            c.tick()
            drawn |= {it[1].split(':')[0] + ':' for it in c.items if it[0] == 'sprite' and ':' in it[1]}
        self.assertTrue({comp['pet'].skin for comp in c.companions} <= drawn)
        fox = c.companions[1]['pet'].skin
        c.toggle_companion(1, False)
        for _ in range(30):
            c.tick()
            self.assertFalse(any(it[0] == 'sprite' and it[1].startswith(fox) for it in c.items))
        self.assertFalse(settings.load()['companions'][1]['enabled'])
        c.remove_companion(0)
        self.assertEqual([e['key'] for e in c.cfg['companions']], ['fox/red', 'bird/canary'])

    def test_obs_serves_companion_sprites(self):
        self.c.add_companion('dog/husky')
        names = json.load(urllib.request.urlopen('http://127.0.0.1:8794/sprites.json'))['sprites']
        self.assertIn('dog/husky:walk31', names)
        self.assertIn('idle', names)  # main pet (base cat)

    def test_drag_moves_only_that_pet(self):
        c = self.c
        c.add_companion('dog/beagle')
        main_x = c.pet.x
        comp = c.companions[0]
        h = comp['handle']
        c.grab(QPointF(h.x() + 5, h.y() + 5), 1)
        c.drag(QPointF(h.x() + 205, h.y() + 5))
        c.release()
        self.assertEqual(c.pet.x, main_x)
        self.assertTrue(comp['pet'].held is False)

    def test_chat_can_reach_companions(self):
        c = self.c
        c.add_companion('dog/husky')
        targets = {id(c._event_target({'type': 'chat'})) for _ in range(50)}
        self.assertEqual(targets, {id(c.pet), id(c.companions[0]['pet'])})
        self.assertIs(c._event_target({'type': 'hype_train'}), c.pet)  # scenes stay with the main pet


if __name__ == '__main__':
    unittest.main()
