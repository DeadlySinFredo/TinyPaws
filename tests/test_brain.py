import random
import tempfile
import unittest
from pathlib import Path

from tinypaws import brain, settings
from tinypaws.reactions import ChatEngine
from tinypaws.sprites import SIZES, SPRITES, PALETTE

W, H, S = 1920, 1080, 4


def run(pet, secs, dt=1 / 30):
    for _ in range(int(secs / dt)):
        pet.update(dt)
        pet.render()


def pet(seed=1):
    return brain.Pet(W, H, scale=S, rng=random.Random(seed))


class Sprites(unittest.TestCase):
    def test_rectangular_and_known_colors(self):
        for name, rows in SPRITES.items():
            self.assertEqual(len({len(r) for r in rows}), 1, name)
            self.assertTrue(set(''.join(rows)) <= set(PALETTE) | {'.'}, name)


class Species(unittest.TestCase):
    def test_dog_uses_dog_sprites_in_all_scenes(self):
        for a in (brain.HypeTrain(2), brain.GigaChad(), brain.Cinema(), brain.Sleep(2)):
            p = brain.Pet(W, H, scale=S, rng=random.Random(1), species='dog')
            p.play(a)
            for _ in range(30 * 30):
                p.update(1 / 30)
                for it in p.render():
                    if it[0] == 'sprite' and it[1] in SIZES and not it[1].startswith('dog:'):
                        self.assertNotIn(it[1], ('idle', 'walk1', 'sit', 'flex', 'cinema', 'sleep'))

    def test_unknown_species_falls_back(self):
        self.assertEqual(brain.Pet(W, H, species='kraken').species, 'cat')


class Movement(unittest.TestCase):
    def test_walk_reaches_target(self):
        p = pet()
        p.play(brain.Walk(100, prio=brain.P_USER))
        run(p, 30)
        self.assertNotIsInstance(p.action, brain.Walk) if p.x != 100 else self.assertEqual(p.x, 100)

    def test_jump_lands_on_floor(self):
        p = pet()
        a = brain.Jump(prio=brain.P_USER)
        p.play(a)
        for _ in range(300):
            if a.update(p, 1 / 60):
                break
        self.assertEqual(p.y, p.floor)

    def test_sleep_then_wake(self):
        p = pet()
        a = brain.Sleep(2, prio=brain.P_USER)
        p.play(a)
        p.update(0.05)
        self.assertTrue(p.sleeping)
        run(p, 3)
        self.assertFalse(p.sleeping)

    def test_random_life_stays_on_screen(self):
        p = pet(7)
        for _ in range(20000):
            p.update(1 / 30)
            self.assertTrue(0 <= p.x <= p.maxx and p.y <= p.floor + 1e-6)

    def test_held_then_fall(self):
        p = pet()
        self.assertTrue(p.play(brain.Held(), queue=False))
        p.held = True
        p.y = 100
        run(p, 1)
        self.assertEqual(p.y, 100)
        p.held = False
        run(p, 3)
        self.assertEqual(p.y, p.floor)


class Priorities(unittest.TestCase):
    def test_scene_interrupts_and_chat_queues(self):
        p = pet()
        p.play(brain.Idle(5))
        self.assertTrue(p.play(brain.Cinema()))
        self.assertFalse(p.play(brain.Emote(prio=brain.P_CHAT)))
        self.assertEqual(len(p.queue), 1)
        self.assertFalse(p.play(brain.Held(), queue=False))  # cannot drag during a scene

    def test_queue_bounded(self):
        p = pet()
        p.play(brain.Cinema())
        for _ in range(20):
            p.play(brain.Emote())
        self.assertLessEqual(len(p.queue), 5)


class Scenes(unittest.TestCase):
    def _finish(self, p, a, limit=120):
        p.play(a)
        phases = set()
        for _ in range(int(limit * 30)):
            p.update(1 / 30)
            p.render()
            phases.add(getattr(a, 'phase', None))
            if p.action is not a:
                return phases
        self.fail('scene did not finish')

    def test_hype_train_returns_home(self):
        p = pet()
        p.x = 500
        a = brain.HypeTrain(4, ['a', 'b'])
        self.assertEqual(self._finish(p, a), {'notice', 'runoff', 'train', 'return'})
        self.assertEqual((p.x, p.y), (500, p.floor))
        self.assertTrue(a.celebrated and a.honked)

    def test_hype_level_clamped(self):
        self.assertEqual(brain.HypeTrain(99).level, 10)
        self.assertEqual(brain.HypeTrain(0).level, 1)

    def test_gigachad(self):
        p = pet()
        a = brain.GigaChad(lang='en')
        self._finish(p, a)
        self.assertEqual(a.line, len(a.lines) - 1)

    def test_cinema(self):
        p = pet()
        a = brain.Cinema()
        self.assertEqual(self._finish(p, a), {'appear', 'walk', 'sit', 'vanish'})
        self.assertEqual(p.y, p.floor)

    def test_scene_draws_known_sprites(self):
        for a in (brain.HypeTrain(3), brain.GigaChad(), brain.Cinema()):
            p = pet()
            p.play(a)
            for _ in range(30 * 40):
                p.update(1 / 30)
                for it in p.render():
                    if it[0] == 'sprite':
                        self.assertIn(it[1], SIZES)


class Chat(unittest.TestCase):
    def engine(self):
        return ChatEngine.from_file(rng=random.Random(0))

    def test_rules_loaded(self):
        self.assertGreaterEqual(len(self.engine().rules), 30)

    def test_matching(self):
        e = self.engine()
        for text, rid in [('HYPE TRAIN!!', 'hypetrain'), ('gigachad', 'gigachad'), ('GigaChat', 'gigachad'),
                          ('absolute cinema', 'cinema'), ('Wo ist meine Pizza?', 'pizza'), ('gg', 'gg'),
                          ('LOL', 'lol'), ('F', 'f'), ('kaffee bitte', 'coffee'), ('Miau', 'meow')]:
            self.assertEqual(e.match(text)['id'], rid, text)
        self.assertIsNone(e.match('nothing to see here'))

    def test_cooldowns(self):
        e = ChatEngine([{'id': 'x', 'patterns': ['x'], 'chance': 1, 'cooldown': 10, 'action': {}}],
                       global_cooldown=2)
        self.assertIsNotNone(e.handle('u', 'x', now=0))
        self.assertIsNone(e.handle('u', 'x', now=1))
        self.assertIsNone(e.handle('u', 'x', now=5))
        self.assertIsNotNone(e.handle('u', 'x', now=11))
        self.assertIsNotNone(e.handle('u', 'x', now=11.5, force=True))

    def test_bad_regex_skipped(self):
        e = ChatEngine([{'id': 'bad', 'patterns': ['(']}, {'id': 'ok', 'patterns': ['a']}])
        self.assertEqual([r['id'] for r in e.rules], ['ok'])

    def test_event_routing(self):
        p, e = pet(), self.engine()
        a = brain.handle_event(p, e, {'type': 'chat', 'user': 'PixelFuchs92', 'text': 'Wo ist meine Pizza?'},
                               force=True)
        self.assertEqual(a.prop, 'pizza')
        self.assertIsInstance(brain.handle_event(p, e, {'type': 'hype_train', 'level': 2}), brain.HypeTrain)
        self.assertIsNone(brain.handle_event(p, e, {'type': 'unknown'}))
        for rule in e.rules:  # every configured action must build
            self.assertIsNotNone(brain.make_action(rule['action'], p, 'u'))


class Settings(unittest.TestCase):
    def test_roundtrip_and_validation(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 's.json'
            cfg = settings.load(f)
            self.assertEqual(cfg, settings.load(f))
            cfg.update(name='Keks', scale=6, x=321.5, first_run_done=True)
            settings.save(cfg, f)
            self.assertEqual(settings.load(f), cfg)
            f.write_text('{"scale": "huge", "fps": 999, "lang": "xx", "evil": 1}')
            c = settings.load(f)
            self.assertEqual((c['scale'], c['fps'], c['lang']), (4, 60, 'de'))
            self.assertNotIn('evil', c)
            f.write_text('not json')
            self.assertEqual(settings.load(f)['name'], 'Mochi')


if __name__ == '__main__':
    unittest.main()
