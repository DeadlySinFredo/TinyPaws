"""Pet packs: user-made pets as ZIP = manifest.json + one PNG sprite sheet. No code, ever.

Workflow: export_pack() writes a template from a built-in pet -> the user repaints
the PNG in any pixel editor -> import_pack() validates and installs it -> load_packs()
registers the frames under the sprite prefix 'pack/<id>:'. Format spec: docs/PET_PACKS.md
"""
import io
import json
import re
import sys
import zipfile
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QColor, QImage

from . import sprites
from .cat32 import GAITS

FORMAT = 1
MAX_ZIP = 8 * 1024 * 1024          # bytes, compressed
MAX_MEMBER = 16 * 1024 * 1024      # bytes, uncompressed (zip bombs)
MAX_SHEET = 4096                   # px per side
MAX_COLORS = 250
ID_RE = re.compile(r'^[a-z0-9-]{1,32}$')
SINGLE = ['idle', 'blink', 'happy', 'surprised', 'stand', 'stand_blink', 'jump', 'sit', 'stretch',
          'sleep', 'lounge', 'flex', 'cinema']
ANIMS = {k: v[0] for k, v in GAITS.items() if k != 'stand'}  # walk/run/sneak -> frame count the brain expects
FALLBACK = {'blink': 'idle', 'happy': 'blink', 'surprised': 'idle', 'stand_blink': 'stand', 'jump': 'stand',
            'sit': 'idle', 'stretch': 'jump', 'sleep': 'sit', 'lounge': 'sleep', 'flex': 'stand', 'cinema': 'idle'}
REQUIRED = ('idle', 'stand', 'walk')


class PackError(ValueError):
    pass


def packs_dir():
    from .settings import config_dir
    return config_dir() / 'packs'


# ---------------------------------------------------------------- export (template)
def export_pack(skin, dest, pack_id='my-pet', name='Mein Tier', base='cat'):
    """Write a built-in pet (sprite prefix `skin`) as an editable pack ZIP."""
    cells, frames = [], {}
    for k in SINGLE:
        frames[k] = [len(cells)]
        cells.append(sprites.SPRITES[skin + k])
    for anim, n in ANIMS.items():
        frames[anim] = list(range(len(cells), len(cells) + n))
        cells += [sprites.SPRITES[skin + '%s%d' % (anim, i)] for i in range(n)]
    fw = max(len(c[0]) for c in cells)
    fh = max(len(c) for c in cells)
    cols = 16
    img = QImage(cols * fw, ((len(cells) + cols - 1) // cols) * fh, QImage.Format_ARGB32)
    img.fill(0)
    for i, rows in enumerate(cells):
        # centred horizontally, bottom-aligned: the brain lays frames out the same way
        ox, oy = (i % cols) * fw + (fw - len(rows[0])) // 2, (i // cols) * fh + fh - len(rows)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    img.setPixelColor(ox + x, oy + y, QColor(sprites.PALETTE[ch]))
    manifest = {'format': FORMAT, 'id': pack_id, 'name': name, 'base': base, 'sheet': 'sheet.png',
                'cell': [fw, fh], 'columns': cols, 'density': sprites.DENSITY.get(skin + 'idle', 3),
                'frames': {k: [[i % cols, i // cols] for i in v] for k, v in frames.items()}}
    buf = io.BytesIO()
    ba = QByteArray()
    qb = QBuffer(ba)
    qb.open(QIODevice.WriteOnly)
    img.save(qb, 'PNG')
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
        z.writestr('sheet.png', bytes(ba))
    Path(dest).write_bytes(buf.getvalue())


# ---------------------------------------------------------------- validate / install
def _read_member(z, name):
    try:
        info = z.getinfo(name)  # exact name only: no paths from the archive are ever used on disk
    except KeyError:
        raise PackError('%s fehlt' % name)
    if info.file_size > MAX_MEMBER:
        raise PackError('%s zu groß' % name)
    return z.read(info)


def validate(manifest, sheet):
    """Check manifest + decoded sheet; return (manifest, QImage). Raises PackError."""
    if not isinstance(manifest, dict) or manifest.get('format') != FORMAT:
        raise PackError('unbekanntes Paketformat')
    pid, name, base = manifest.get('id'), manifest.get('name'), manifest.get('base', 'cat')
    if not isinstance(pid, str) or not ID_RE.match(pid):
        raise PackError('id ungültig (a-z, 0-9, -)')
    if not isinstance(name, str) or not 0 < len(name) <= 40:
        raise PackError('name ungültig')
    if base not in sprites.BREEDS:
        raise PackError('base muss eine Tierart sein: %s' % ', '.join(sprites.BREEDS))
    cell, cols, dens = manifest.get('cell'), manifest.get('columns'), manifest.get('density')
    if not (isinstance(cell, list) and len(cell) == 2 and all(isinstance(v, int) and 8 <= v <= 256 for v in cell)):
        raise PackError('cell ungültig')
    if not (isinstance(dens, int) and 1 <= dens <= 8 and cell[0] % dens == 0 and cell[1] % dens == 0):
        raise PackError('density muss cell teilen')
    if sheet.isNull() or sheet.width() > MAX_SHEET or sheet.height() > MAX_SHEET:
        raise PackError('sheet.png ungültig oder zu groß')
    frames = manifest.get('frames')
    if not isinstance(frames, dict):
        raise PackError('frames fehlt')
    for k, v in frames.items():
        if k not in SINGLE and k not in ANIMS:
            raise PackError('unbekannter Frame: %s' % k)
        if not (isinstance(v, list) and v and len(v) <= 64 and all(
                isinstance(c, list) and len(c) == 2 and all(isinstance(i, int) and i >= 0 for i in c)
                and (c[0] + 1) * cell[0] <= sheet.width() and (c[1] + 1) * cell[1] <= sheet.height() for c in v)):
            raise PackError('Zellen von %s ungültig' % k)
    missing = [k for k in REQUIRED if k not in frames]
    if missing:
        raise PackError('Pflicht-Frames fehlen: %s' % ', '.join(missing))
    return manifest, sheet


def read_zip(path):
    p = Path(path)
    if p.stat().st_size > MAX_ZIP:
        raise PackError('Datei zu groß')
    try:
        with zipfile.ZipFile(p) as z:
            manifest = json.loads(_read_member(z, 'manifest.json').decode('utf-8'))
            png = _read_member(z, 'sheet.png')
    except (zipfile.BadZipFile, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise PackError('kaputtes Paket: %s' % e)
    sheet = QImage.fromData(png, 'PNG')
    return validate(manifest, sheet)


def import_pack(path):
    """Validate and install; returns the pack id. Only manifest.json + sheet.png are written."""
    manifest, sheet = read_zip(path)
    to_frames(manifest, sheet)  # also enforces the color limit before installing
    d = packs_dir() / manifest['id']
    d.mkdir(parents=True, exist_ok=True)
    manifest['sheet'] = 'sheet.png'
    (d / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    sheet.save(str(d / 'sheet.png'), 'PNG')
    return manifest['id']


# ---------------------------------------------------------------- load
_char_next = [0x3000]  # private char range for pack colors, after the built-in breed chars


def to_frames(manifest, sheet):
    """Cut the sheet into char-grid frames for every name the brain uses (with fallbacks)."""
    fw, fh = manifest['cell']
    colors, cut = {}, {}

    def grid(c):
        rows = []
        for y in range(c[1] * fh, (c[1] + 1) * fh):
            row = []
            for x in range(c[0] * fw, (c[0] + 1) * fw):
                px = sheet.pixelColor(x, y)
                if px.alpha() < 128:
                    row.append('.')
                    continue
                key = px.name()
                if key not in colors:
                    if len(colors) >= MAX_COLORS:
                        raise PackError('zu viele Farben (max. %d)' % MAX_COLORS)
                    colors[key] = None
                row.append(key)
            rows.append(row)
        return rows

    src = manifest['frames']
    for k in SINGLE:
        name = k
        while name not in src:
            name = FALLBACK.get(name, 'idle')
        cut[k] = grid(src[name][0])
    for anim, n in ANIMS.items():
        cells = src.get(anim) or src['walk']
        for i in range(n):
            cut['%s%d' % (anim, i)] = grid(cells[i * len(cells) // n])
    cut['walk1'], cut['walk2'] = cut['walk4'], cut['walk12']
    return cut, list(colors)


def register(manifest, sheet):
    """Add a pack's frames to the global sprite tables; returns its sprite prefix."""
    cut, colors = to_frames(manifest, sheet)
    chars = {}
    for c in colors:
        ch = chr(_char_next[0])
        _char_next[0] += 1
        chars[c] = ch
        sprites.PALETTE[ch] = c
    prefix = 'pack/%s:' % manifest['id']
    for k, rows in cut.items():
        sprites.SPRITES[prefix + k] = [''.join('.' if p == '.' else chars[p] for p in r) for r in rows]
        sprites.DENSITY[prefix + k] = manifest['density']
        sprites.SIZES[prefix + k] = (len(rows[0]) // manifest['density'], len(rows) // manifest['density'])
    return prefix


def load_packs():
    """Register every installed pack; returns {id: (name, base)}. Broken packs are skipped."""
    out = {}
    d = packs_dir()
    for p in sorted(d.iterdir()) if d.is_dir() else []:
        try:
            manifest = json.loads((p / 'manifest.json').read_text(encoding='utf-8'))
            manifest, sheet = validate(manifest, QImage(str(p / 'sheet.png')))
            if manifest['id'] != p.name:
                raise PackError('id passt nicht zum Ordner')
            register(manifest, sheet)
            out[manifest['id']] = (manifest['name'], manifest['base'])
        except (OSError, ValueError) as e:
            print('tinypaws: skip pack %s: %s' % (p.name, e), file=sys.stderr)
    return out
