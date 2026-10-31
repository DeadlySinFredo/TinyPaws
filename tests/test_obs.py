import json
import unittest
import urllib.error
import urllib.request

from tinypaws import brain
from tinypaws.obs import ObsServer


class Obs(unittest.TestCase):
    def test_page_assets_and_stream(self):
        srv = ObsServer(port=0)
        try:
            base = 'http://127.0.0.1:%d/' % srv.port
            self.assertIn(b'<canvas', urllib.request.urlopen(base).read())
            assets = json.load(urllib.request.urlopen(base + 'sprites.json'))
            self.assertIn('loco', assets['sprites'])
            self.assertIn('idle', assets['sprites'])
            from tinypaws.obs import VISITOR_FRAME
            others = [k for k in assets['sprites'] if ':' in k]  # other skins: only visitor idle/walk frames
            self.assertTrue(others and all(VISITOR_FRAME.match(k.split(':', 1)[1]) and '/' not in k for k in others))
        finally:
            srv.close()
        srv = ObsServer(port=0, skin='dog/husky:')
        try:
            base = 'http://127.0.0.1:%d/' % srv.port
            names = json.load(urllib.request.urlopen(base + 'sprites.json'))['sprites']
            self.assertIn('dog/husky:run3', names)
            self.assertIn('loco', names)
            self.assertNotIn('blink', names)  # base-cat poses only as visitor idle/walk
            self.assertNotIn('fox:blink', names)  # other pets: no poses beyond visitor idle/walk
            pet = brain.Pet(800, 300, scale=3)
            pet.play(brain.Cinema())
            pet.update(0.1)
            srv.publish(800, 300, 3, pet.render())
            with urllib.request.urlopen(base + 'stream', timeout=5) as r:
                line = r.readline()
                while not line.startswith(b'data: '):
                    line = r.readline()
            frame = json.loads(line[len(b'data: '):])
            self.assertEqual((frame['w'], frame['s']), (800, 3))
            self.assertTrue(any(it[0] == 'sprite' and it[1] == 'chair' for it in frame['items']))
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(base + 'etc/passwd')
        finally:
            srv.close()


if __name__ == '__main__':
    unittest.main()


class PetSwitch(unittest.TestCase):
    """P0 (issue #3): switching pets must never leave an open OBS page with a mismatched sprite set."""

    def setUp(self):
        from tinypaws import packs
        packs.load_builtin_hd('dog', 'husky')
        self.srv = ObsServer(port=0, skin='')
        self.base = 'http://127.0.0.1:%d/' % self.srv.port

    def tearDown(self):
        self.srv.close()

    def _event(self, stream):
        """Next SSE event as (type, data)."""
        kind, data = 'message', None
        while True:
            line = stream.readline().decode().rstrip('\n')
            if line.startswith('event: '):
                kind = line[7:]
            elif line.startswith('data: '):
                data = line[6:]
            elif line == '' and data is not None:
                return kind, data

    def test_switch_keeps_connection_and_versions_sprites(self):
        pet = brain.Pet(800, 300, scale=3)
        stream = urllib.request.urlopen(self.base + 'stream', timeout=10)
        v1 = json.load(urllib.request.urlopen(self.base + 'sprites.json'))['version']
        self.srv.publish(800, 300, 3, pet.render())
        while json.loads(self._event(stream)[1]).get('v') != v1:
            pass
        self.srv.set_skin('dog/husky:')
        pet.skin = 'dog/husky:'
        pet.update(0.1)
        self.srv.publish(800, 300, 3, pet.render())
        frames = [json.loads(d) for k, d in (self._event(stream) for _ in range(3)) if k == 'message']
        v2 = frames[-1]['v']
        self.assertNotEqual(v1, v2)  # same connection, new version announced
        assets = json.load(urllib.request.urlopen(self.base + 'sprites.json'))
        self.assertEqual(assets['version'], v2)
        names = assets['sprites']
        self.assertIn('dog/husky:idle', names)
        self.assertIn('dog/husky:walk31', names)  # HD in-between frames too, not just the generator's names
        self.assertNotIn('blink', names)  # no old cat pose keys mixed in (base-cat idle/walk only for visitors)
        for v in ('dog:idle', 'fox:walk3', 'bird:walk0', 'idle'):  # visitors (base breeds) can walk in
            self.assertIn(v, names)
        for it in frames[-1]['items']:
            if it[0] == 'sprite':
                self.assertIn(it[1], names)  # every sprite of a v2 frame exists in the v2 set
        stream.close()

    def test_idle_stream_sends_keepalive(self):
        stream = urllib.request.urlopen(self.base + 'stream', timeout=10)
        self._event(stream)  # current frame
        self.assertEqual(self._event(stream)[0], 'ping')
        stream.close()

    def test_versions_unique_across_restarts(self):
        other = ObsServer(port=0, skin='')
        try:
            self.assertNotEqual(other.version, self.srv.version)
        finally:
            other.close()

    def test_page_reloads_sprites_on_version_change(self):
        page = urllib.request.urlopen(self.base).read().decode()
        self.assertIn("f.v!==ver", page)  # frames of another version trigger a reload, never a mixed draw
        self.assertIn("addEventListener('ping'", page)
        self.assertIn('Date.now()-seen>6000', page)  # watchdog reconnect
