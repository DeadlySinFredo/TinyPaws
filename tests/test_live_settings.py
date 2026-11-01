"""Settings apply live: no process restart, every change takes effect."""
import json
import os
import tempfile
import unittest
import urllib.request

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication([])

from tinypaws import app as A, settings  # noqa: E402


class LiveSettings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.get(k) for k in ('XDG_CONFIG_HOME', 'XDG_CURRENT_DESKTOP')}
        os.environ.update(XDG_CONFIG_HOME=self.tmp.name, XDG_CURRENT_DESKTOP='none')
        cfg = dict(settings.DEFAULTS, first_run_done=True, obs=False, obs_port=8791)
        self.c = A.TinyPaws(APP, cfg)

    def tearDown(self):
        self.c._stop_obs()
        for k, v in self.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def apply(self, **kw):
        self.c.apply_settings(dict(self.c.cfg, **kw))
        for _ in range(3):
            self.c.tick()

    def test_name_random_fps_scale(self):
        self.c.apply_settings(dict(self.c.cfg, name='Keks', random_level=2.0, fps=45, scale=3))
        p = self.c.pet
        self.assertEqual(p.y, p.floor)  # re-laid out on the floor at the new size
        self.c.tick()
        self.assertEqual((p.name, p.random_level, p.s), ('Keks', 2.0, 3))
        self.assertEqual(self.c.renderer.s, 3)
        self.assertEqual(self.c.handle.width(), 48)
        self.assertEqual(settings.load()['name'], 'Keks')  # persisted

    def test_pet_switch_from_settings(self):
        self.apply(animal='fox', breed='arctic')
        self.assertEqual((self.c.pet.species, self.c.skin), ('fox', 'fox/arctic:'))

    def test_obs_on_port_change_off(self):
        self.apply(obs=True)
        self.assertTrue(self.c.obs)
        urllib.request.urlopen('http://127.0.0.1:8791/').read()
        self.apply(obs_port=8792)
        self.assertEqual(self.c.obs.port, 8792)
        self.assertIn('8792', '\n'.join(self.c.status_lines()))
        self.apply(obs=False)
        self.assertIsNone(self.c.obs)
        with self.assertRaises(OSError):
            urllib.request.urlopen('http://127.0.0.1:8792/', timeout=2)

    def test_busy_port_is_reported_not_fatal(self):
        import socket
        s = socket.socket()
        s.bind(('127.0.0.1', 8793))
        s.listen()
        try:
            self.apply(obs=True, obs_port=8793)
            self.assertIsNone(self.c.obs)
            self.assertIn('8793', self.c.obs_error)
            self.assertIn('8793', '\n'.join(self.c.status_lines()))
            self.c.tick()  # pet keeps running
        finally:
            s.close()

    def test_language_rebuilds_menu(self):
        self.apply(lang='en')
        texts = [a.text() for a in self.c.menu.actions()]
        self.assertIn('Copy OBS link', texts)
        self.assertIn('Pet:', self.c.status_lines()[0])

    def test_twitch_channel_toggle(self):
        self.apply(twitch_channel='tinypawstest')
        self.assertEqual(self.c.twitch.channel, 'tinypawstest')
        self.apply(twitch_channel='')
        self.assertIsNone(self.c.twitch)


if __name__ == '__main__':
    unittest.main()
