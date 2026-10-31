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
            pet = brain.Pet(800, 300, scale=3)
            pet.play(brain.Cinema())
            pet.update(0.1)
            srv.publish(800, 300, 3, pet.render())
            with urllib.request.urlopen(base + 'stream', timeout=5) as r:
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
