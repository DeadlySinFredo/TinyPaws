import os
import random
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tinypaws import brain, packs, sprites  # noqa: E402
from tinypaws.sprites import BREEDS, SIZES, skin  # noqa: E402

W, H, S = 1920, 1080, 6


class HDSprites(unittest.TestCase):
    def test_every_breed_loads_hd_with_extra_frames(self):
        for sp in BREEDS:
            for br in BREEDS[sp]:
                self.assertTrue(packs.load_builtin_hd(sp, br), (sp, br))
                pre = skin(sp, br)
                self.assertEqual(sprites.GAIT_FRAMES[pre], {'walk': 32, 'run': 24, 'sneak': 32}, (sp, br))
                self.assertEqual(sprites.DENSITY[pre + 'walk31'], 6)
                self.assertEqual(SIZES[pre + 'idle'], (20, 20))

    def test_same_speed_more_frames(self):
        """A full walk cycle still takes the same time; HD just has twice the steps in it."""
        packs.load_builtin_hd('cat', 'tuxedo')
        n, _, cycle = brain.GAITS['walk']
        frames = [brain.gait_frame('walk', i / 1000 * cycle, skin('cat', 'tuxedo')) for i in range(1000)]
        self.assertEqual(len(set(frames)), 2 * n)  # 32 instead of 16 ...
        self.assertEqual(frames[0], 'walk0')
        self.assertEqual(brain.gait_frame('walk', cycle + 1e-6, skin('cat', 'tuxedo')), 'walk0')  # ... same cycle

    def test_hd_pets_run_scenes_and_memes(self):
        for sp in BREEDS:
            br = next(iter(BREEDS[sp]))
            packs.load_builtin_hd(sp, br)
            p = brain.Pet(W, H, scale=S, rng=random.Random(1), species=sp, breed=br)
            p.set_windows([('w', 600, 500, 700, 400)])
            for a in (brain.Walk(10, prio=brain.P_USER), brain.Walk(1500, style='run', prio=brain.P_USER),
                      brain.HypeTrain(2), brain.Cinema(), brain.Meme('exit', prio=brain.P_USER),
                      brain.Climb('w', nap=1, prio=brain.P_USER)):
                p.play(a)
                for _ in range(30 * 30):
                    p.update(1 / 30)
                    for it in p.render():
                        if it[0] == 'sprite':
                            self.assertIn(it[1], SIZES, (sp, it[1]))
                    if p.action is not a:
                        break
                self.assertEqual(p.y, p.floor, (sp, type(a).__name__))


if __name__ == '__main__':
    unittest.main()
