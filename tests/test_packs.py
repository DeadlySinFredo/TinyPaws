import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tinypaws import brain, packs, sprites  # noqa: E402


class Packs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get('XDG_CONFIG_HOME')
        os.environ['XDG_CONFIG_HOME'] = self.tmp.name
        self.zip = Path(self.tmp.name) / 'tpl.zip'

    def tearDown(self):
        if self.old is None:
            os.environ.pop('XDG_CONFIG_HOME', None)
        else:
            os.environ['XDG_CONFIG_HOME'] = self.old
        self.tmp.cleanup()

    def _strip(self, rows):
        """Pixels as (x, y, color) relative to the frame's bottom centre."""
        h, w = len(rows), len(rows[0])
        return {(x - w // 2, y - h, sprites.PALETTE[c]) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}

    def test_export_import_roundtrip_matches_original_pixels(self):
        packs.export_pack('dog/husky:', self.zip, 'husky-x', 'Husky X', 'dog')
        pid = packs.import_pack(self.zip)
        self.assertEqual(pid, 'husky-x')
        self.assertEqual(packs.load_packs()['husky-x'], ('Husky X', 'dog'))
        for k in ('idle', 'walk3', 'run7', 'sleep', 'lounge'):
            self.assertEqual(self._strip(sprites.SPRITES['pack/husky-x:' + k]),
                             self._strip(sprites.SPRITES['dog/husky:' + k]), k)

    def test_pack_pet_runs_every_scene(self):
        packs.export_pack('', self.zip, 'mini', 'Mini', 'cat')
        packs.import_pack(self.zip)
        packs.load_packs()
        p = brain.Pet(1920, 1080, scale=4, species='cat')
        p.skin = 'pack/mini:'
        for a in (brain.HypeTrain(2), brain.Cinema(), brain.Meme('cds', prio=brain.P_USER), brain.Sleep(2)):
            p.play(a)
            for _ in range(30 * 20):
                p.update(1 / 30)
                for it in p.render():
                    if it[0] == 'sprite':
                        self.assertIn(it[1], sprites.SIZES)

    def _bad(self, manifest=None, extra=None, sheet=True):
        packs.export_pack('', self.zip, 'ok', 'Ok', 'cat')
        with zipfile.ZipFile(self.zip) as z:
            m, png = json.loads(z.read('manifest.json')), z.read('sheet.png')
        m.update(manifest or {})
        out = Path(self.tmp.name) / 'bad.zip'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('manifest.json', json.dumps(m))
            if sheet:
                z.writestr('sheet.png', png)
            for name, data in (extra or {}).items():
                z.writestr(name, data)
        return out

    def test_rejects_bad_packs(self):
        for bad in ({'id': '../../etc'}, {'format': 2}, {'base': 'kraken'}, {'cell': [5000, 10]},
                    {'density': 7}, {'frames': {'idle': [[0, 0]]}}, {'frames': {'evil': [[0, 0]]}},
                    {'frames': {'idle': [[999, 0]], 'stand': [[0, 0]], 'walk': [[0, 0]]}}):
            with self.assertRaises(packs.PackError, msg=bad):
                packs.import_pack(self._bad(bad))
        with self.assertRaises(packs.PackError):
            packs.import_pack(self._bad(sheet=False))

    def test_extra_archive_members_are_never_extracted(self):
        pid = packs.import_pack(self._bad(extra={'../../evil.sh': 'rm -rf ~', 'run.py': 'print(1)'}))
        installed = {p.name for p in (packs.packs_dir() / pid).iterdir()}
        self.assertEqual(installed, {'manifest.json', 'sheet.png'})
        self.assertFalse((Path(self.tmp.name) / 'evil.sh').exists())


if __name__ == '__main__':
    unittest.main()
