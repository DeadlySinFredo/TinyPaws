"""Pixel-art sprites as character grids. Pure data, no Qt. '.' = transparent.

Each sprite is a list of equal-length strings; each char maps to PALETTE.
Pet frames come from cat32 (32x32, density 2 = 16 logical units); props are density 1.
"""
from .cat32 import FRAMES

PALETTE = {
    'K': '#14111c', 'O': '#33303f', 'D': '#211e2b', 'L': '#f6f2ea', 'P': '#ff8fa3',
    'E': '#1b1b1b', 'W': '#ffffff', 'N': '#26262e', 'S': '#8a8a96', 'R': '#d93a3a',
    'r': '#9c2424', 'Y': '#ffd23f', 'B': '#3a6fd9', 'b': '#25479c', 'G': '#3fbf5f',
    'M': '#7a4a24', 'C': '#fff7e0', 'T': '#2ec4b6', 'H': '#4d4960', 'g': '#5cc24a',
}


def _blank(w, h):
    return [['.'] * w for _ in range(h)]


def _grid(rows, w=None):
    w = w or max(len(r) for r in rows)
    return [list(r[:w].ljust(w, '.')) for r in rows]


def _put(g, x, y, s):
    if 0 <= y < len(g):
        for i, c in enumerate(s):
            if c != ' ' and 0 <= x + i < len(g[0]):
                g[y][x + i] = c


def _rect(g, x, y, w, h, c, outline='K'):
    for j in range(h):
        for i in range(w):
            edge = outline and (i in (0, w - 1) or j in (0, h - 1))
            _put(g, x + i, y + j, outline if edge else c)


def _circle(g, cx, cy, r, c, outline='K'):
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            d = i * i + j * j
            if d <= r * r + r:
                _put(g, cx + i, cy + j, outline if d > (r - 1) * r else c)


def _rows(g):
    return [''.join(r) for r in g]


# ---------------------------------------------------------------- props
def _chair():
    g = _blank(24, 18)
    _rect(g, 3, 0, 18, 12, 'R')
    for x in (7, 12, 16):
        _put(g, x, 4, 'r')
        _put(g, x, 8, 'r')
    _rect(g, 0, 9, 4, 7, 'R')
    _rect(g, 20, 9, 4, 7, 'R')
    _rect(g, 3, 11, 18, 5, 'r')
    _put(g, 1, 16, "KM")
    _put(g, 1, 17, "KK")
    _put(g, 21, 16, "MK")
    _put(g, 21, 17, "KK")
    return g


def _chair_front():
    g = _chair()
    for y, row in enumerate(g):
        for x in range(24):
            if not (x < 4 or x >= 20 or y >= 11):
                row[x] = '.'
    return g


def _loco():
    g = _blank(40, 27)
    _rect(g, 0, 2, 15, 3, 'r')
    _rect(g, 1, 4, 13, 18, 'B')
    _rect(g, 3, 7, 8, 6, 'B')
    for j in range(8, 12):
        for i in range(4, 10):
            g[j][i] = '.'  # cab window: the driver shows through
    _rect(g, 13, 10, 24, 12, 'R')
    for x in (18, 24, 30):
        for y in range(11, 21):
            _put(g, x, y, 'Y')
    _rect(g, 20, 7, 5, 4, 'Y')
    _rect(g, 28, 3, 5, 8, 'N')
    _rect(g, 27, 1, 7, 3, 'N')
    _rect(g, 36, 11, 3, 10, 'S')
    _put(g, 37, 13, 'Y')
    _rect(g, 35, 21, 5, 4, 'S')
    _rect(g, 0, 21, 37, 2, 'N')
    for cx in (7, 19, 29):
        _circle(g, cx, 23, 3, 'N')
        _put(g, cx, 23, 'S')
    return g


def _wagon(c):
    g = _blank(26, 19)
    _rect(g, 1, 4, 24, 10, c)
    _rect(g, 3, 6, 20, 5, 'C')
    _rect(g, 0, 13, 26, 2, 'N')
    for cx in (6, 19):
        _circle(g, cx, 15, 3, 'N')
        _put(g, cx, 15, 'S')
    return g


def _ball():
    g = _blank(7, 7)
    _circle(g, 3, 3, 3, 'T')
    _put(g, 2, 2, 'W')
    return g


PIZZA = ["KKKKKKKKKK", "KMMMMMMMMK", "KYYRYYYRYK", ".KYYYRYYK.", ".KYRYYYYK.",
         "..KYYYRK..", "..KYYYYK..", "...KYRK...", "....KK...."]
COFFEE = ["..S.S....", "...S.S...", "KKKKKKK..", "KWWWWWKKK", "KWMMMWK.K",
          "KWWWWWKKK", "KWWWWWK..", ".KKKKK..."]
POPCORN = [".Y.YY.Y.", "YYYYYYYY", "KYYYYYYK", "KRWRWRWK", "KRWRWRWK",
           ".KWRWRK.", ".KWRWRK.", ".KWRWRK.", ".KKKKKK."]
BANANA = ["......KK", ".....KYK", "....KYYK", "...KYYK.", "KKKYYYK.", "KYYYYK..", ".KKKK..."]

SPRITES = {k: _rows(v) if isinstance(v[0], list) else _rows(_grid(v)) for k, v in {
    'chair': _chair(), 'chair_front': _chair_front(), 'loco': _loco(),
    'wagon0': _wagon('R'), 'wagon1': _wagon('B'), 'wagon2': _wagon('G'), 'wagon3': _wagon('Y'),
    'ball': _ball(), 'pizza': PIZZA, 'coffee': COFFEE, 'popcorn': POPCORN, 'banana': BANANA,
}.items()}

SPRITES.update(FRAMES)
# pixels per logical unit; the brain lays out in logical units, the renderer draws at scale/density
DENSITY = {k: 2 for k in FRAMES}
SIZES = {k: (len(v[0]) // DENSITY.get(k, 1), len(v) // DENSITY.get(k, 1)) for k, v in SPRITES.items()}
