"""Optional sound: own synthesised sounds, off by default, polite, fully switchable."""
import os
import random
import struct
import tempfile
import unittest
import wave
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication([])

from tinypaws import app as A, brain, settings, sound  # noqa: E402


class Synth(unittest.TestCase):
    def test_every_sound_is_a_short_quiet_wav(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            for name in sound.SOUNDS:
                p = Path(d) / (name + '.wav')
                dur = sound.render(name, p)
                self.assertTrue(0.03 < dur < 1.0, name)
                with wave.open(str(p)) as w:
                    self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, sound.RATE))
                    frames = w.readframes(w.getnframes())
                peak = max(abs(v) for (v,) in struct.iter_unpack('<h', frames))
                self.assertTrue(8000 < peak <= 16384, (name, peak))  # normalised to -6 dB, never clipping

    def test_player_cooldown_and_volume(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            p = sound.Player(Path(d), volume=40)
            self.assertTrue(p.play('pop', now=10.0))
            self.assertFalse(p.play('pop', now=10.1))     # flood protection
            self.assertTrue(p.play('pop', now=10.5))
            self.assertFalse(p.play('nonexistent', now=11))
            p.set_volume(0)
            self.assertFalse(p.play('horn', now=20))      # 0 % = silent
            p.set_volume(250)
            self.assertEqual(p.volume, 100)


class Events(unittest.TestCase):
    def pet(self, sp='dog'):
        return brain.Pet(1920, 1080, scale=4, rng=random.Random(1), species=sp)

    def run_until(self, p, a, cond, secs=40):
        p.play(a)
        for _ in range(int(secs * 30)):
            p.update(1 / 30)
            if cond():
                return True
        return False

    def test_scene_events(self):
        p = self.pet()
        self.assertTrue(self.run_until(p, brain.HypeTrain(1), lambda: 'horn' in p.sfx))
        p = self.pet()
        self.assertTrue(self.run_until(p, brain.Meme('bonk', prio=brain.P_USER), lambda: 'bonk' in p.sfx))
        p = self.pet()
        p.confetti(5)
        self.assertIn('pop', p.sfx)
        p = self.pet()
        p.play(brain.Teleport(prio=brain.P_USER))
        self.assertIn('blip', p.sfx)

    def test_voice_on_poke_bubble(self):
        p = self.pet('bird')
        p.play(brain.Emote(('happy',), 1, bubble=brain.SPECIES['bird'], prio=brain.P_USER))
        self.assertEqual(p.sfx, ['voice'])


class AppSwitch(unittest.TestCase):
    def test_off_by_default_and_live_toggle(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            env = os.environ.get('XDG_CONFIG_HOME')
            os.environ.update(XDG_CONFIG_HOME=d, XDG_CURRENT_DESKTOP='none')
            try:
                c = A.TinyPaws(APP, dict(settings.DEFAULTS, first_run_done=True, obs=False))
                self.assertIsNone(c.player)
                c.pet.sound('pop')
                c.tick()
                self.assertEqual(c.pet.sfx, [])           # drained silently
                c.apply_settings(dict(c.cfg, sound=True, volume=20))
                self.assertIsNotNone(c.player)
                self.assertEqual(c.player.volume, 20)
                self.assertTrue((Path(d) / 'tinypaws' / 'sounds' / 'voice_cat.wav').exists())
                c.apply_settings(dict(c.cfg, sound=False))
                self.assertIsNone(c.player)
            finally:
                os.environ.pop('XDG_CONFIG_HOME', None) if env is None else os.environ.__setitem__('XDG_CONFIG_HOME', env)


if __name__ == '__main__':
    unittest.main()
