"""Pixel-art sprites as character grids. Pure data, no Qt. '.' = transparent.

Each sprite is a list of equal-length strings; each char maps to PALETTE.
Pet frames are 16x16 (wider frames are centred on the 16px box by the brain).
"""

PALETTE = {
    'K': '#2b1d16', 'O': '#f2a541', 'D': '#c9762b', 'L': '#fff1d6', 'P': '#ff8fa3',
    'E': '#1b1b1b', 'W': '#ffffff', 'N': '#26262e', 'S': '#8a8a96', 'R': '#d93a3a',
    'r': '#9c2424', 'Y': '#ffd23f', 'B': '#3a6fd9', 'b': '#25479c', 'G': '#3fbf5f',
    'M': '#7a4a24', 'C': '#fff7e0', 'T': '#2ec4b6',
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


# ---------------------------------------------------------------- cat
_HEAD = [
    "................",
    "..........K...K.",
    ".........KOK.KOK",
    ".........KOOKOOK",
    ".........KODOOOK",
    ".........KOEOOEK",
    ".........KOOPOOK",
    ".........KLOOOLK",
    "..........KOOOK.",
]
_BODY = [
    "...KKKKKKKKOOOK.",
    "..KOODOODOOOOOK.",
    "..KOOOOOOOOOOOK.",
    "..KOLLLLLLLLOOK.",
    "...KKKKKKKKKKK..",
]
_LEGS = {
    'stand': ["...KO.KO...KO.KO", "...KK.KK...KK.KK"],
    'walk1': ["..KO..KO..KO..KO", "..KK..KK..KK..KK"],
    'walk2': ["....KOKO....KOKO", "....KKKK....KKKK"],
    'jump': [".KO..........KO.", "KK............KK"],
    'sit': ["...KOOOK..KOK...", "...KKKKK..KKK..."],
}
_TAIL = [(1, 4, "K"), (0, 5, "KOK"), (0, 6, "KOK"), (0, 7, "KOK"), (1, 8, "KOOK")]


def _cat(legs='stand', eyes=None, tail=True):
    g = _grid(_HEAD + _BODY + _LEGS[legs], 16)
    if tail:
        for x, y, s in _TAIL:
            _put(g, x, y, s)
    if eyes:
        for row in g:
            for i, c in enumerate(row):
                if c == 'E':
                    row[i] = eyes
    return g


def _sleep():
    head = [r.replace('E', 'K') for r in _HEAD[1:8]]
    return _grid(["."] * 5 + head + [
        "..KKKKKKKOOOOOK.",
        "..KOODOODOOOOOK.",
        "KOKOOOOOOOOOOOK.",
        "KKKKKKKKKKKKKKK.",
    ], 16)


def _flex():
    base = _cat(tail=False)
    g = _blank(20, 16)
    for y, row in enumerate(base):
        for x, c in enumerate(row):
            if c != '.':
                g[y][x + 2] = c
    _put(g, 12, 5, "NNKNNN")  # sunglasses
    for x, y, s in [(18, 7, "KK"), (17, 8, "KOK"), (17, 9, "KOK"), (15, 10, "KOOOK"), (15, 11, "KKKK"),
                    (0, 7, "KK"), (0, 8, "KOK"), (0, 9, "KOK"), (0, 10, "KOOOK"), (1, 11, "KKKK")]:
        _put(g, x, y, s)
    return g


def _cinema():
    g = _grid([
        "................",
        "................",
        "....K......K....",
        "...KOK....KOK...",
        "...KOOKKKKOOK...",
        "...KOOOOOOOOK...",
        "...KOEOOOOEOK...",
        "...KOOOPPOOOK...",
        "...KLOOKKOOLK...",
        "....KKOOOOKK....",
        "...KOOOOOOOOK...",
        "..KOOLLLLLLOOK..",
        "..KOOLLLLLLOOK..",
        "..KOOOOOOOOOOK..",
        "..KOOKOOOOKOOK..",
        "..KKKKKKKKKKKK..",
    ], 16)
    arm = [(0, 0, "KK"), (0, 1, "KOK"), (1, 2, "KOK"), (1, 3, "KOK"), (2, 4, "KOK"),
           (2, 5, "KO"), (2, 6, "KO"), (2, 7, "KO"), (2, 8, "KO"), (2, 9, "KO")]
    for x, y, s in arm:
        _put(g, x, y, s)
        _put(g, 16 - x - len(s), y, s[::-1])
    return g


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
    'idle': _cat(), 'blink': _cat(eyes='K'), 'happy': _cat(eyes='K'),
    'walk1': _cat('walk1'), 'walk2': _cat('walk2'), 'jump': _cat('jump'),
    'sit': _cat('sit'), 'surprised': _cat(eyes='W'), 'stretch': _cat('jump', eyes='K'),
    'sleep': _sleep(), 'flex': _flex(), 'cinema': _cinema(),
    'chair': _chair(), 'chair_front': _chair_front(), 'loco': _loco(),
    'wagon0': _wagon('R'), 'wagon1': _wagon('B'), 'wagon2': _wagon('G'), 'wagon3': _wagon('Y'),
    'ball': _ball(), 'pizza': PIZZA, 'coffee': COFFEE, 'popcorn': POPCORN, 'banana': BANANA,
}.items()}

SIZES = {k: (len(v[0]), len(v)) for k, v in SPRITES.items()}
