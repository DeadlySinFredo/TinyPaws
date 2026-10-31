"""Detailed props (same 48-raster generator as the pets, density 3).

Design coordinates are 2x the logical size, so layouts the brain relies on
(cab window, chair seat, wagon plate) keep their old logical positions.
"""
import math

from .cat32 import K, _blank, _ell, _finish, _line, _thin, _tri

COLORS = {
    'q': '#f06a5e', 'u': '#6b9cf0', 'y': '#c9a227', 'n': '#4a4a58', 's': '#c4c4d0',
    't': '#1f8f86', 'j': '#e0a965', 'i': '#2b8f45', 'k': '#6fdc8a', 'z': '#ffe680',
    'o': '#ff9f1c', 'x': '#c8955a', 'X': '#9c6d3a', 'v': '#e8e8f0',
}
SHADE = {'R': ('q', 'r'), 'B': ('u', 'b'), 'Y': ('z', 'y'), 'N': ('n', None), 'T': ('W', 't'),
         'W': (None, 'v'), 'G': ('k', 'i'), 'M': ('j', None), 'S': ('s', 'n'), 'C': ('W', 'j'),
         'x': ('j', 'X')}


def _box(g, x0, y0, x1, y1, c):
    """Fill design-space rectangle [x0, x1) x [y0, y1)."""
    for y in range(max(0, int(y0 * K)), min(len(g), int(y1 * K))):
        for x in range(max(0, int(x0 * K)), min(len(g[0]), int(x1 * K))):
            g[y][x] = c


def _wheel(g, cx, cy, r, spokes=6, phase=0.0):
    _ell(g, cx, cy, r, r, 'N')
    _ell(g, cx, cy, r - 1.2, r - 1.2, 'n')
    for k in range(spokes):
        a = phase + k * math.pi / spokes * 2
        _thin(g, (cx, cy), (cx + math.cos(a) * (r - 1.2), cy + math.sin(a) * (r - 1.2)), 'S')
    _ell(g, cx, cy, 1.4, 1.4, 'Y')


def chair():
    g = _blank(48, 36)
    _ell(g, 24, 6, 18, 5, 'R')
    _box(g, 6, 5, 42, 26, 'R')
    for x in (15, 24, 33):  # tufted buttons + seams
        _ell(g, x, 11, 0.9, 0.9, 'r')
        _thin(g, (x, 12), (x, 21), 'r')
    for x in (19.5, 28.5):
        _ell(g, x, 16, 0.9, 0.9, 'r')
    _box(g, 6, 22, 42, 26, 'r')  # seat cushion top
    _box(g, 6, 26, 42, 32, 'R')  # seat front
    for x0 in (0, 40):
        _box(g, x0, 18, x0 + 8, 32, 'R')
        _ell(g, x0 + 4, 18.5, 4, 3, 'R')
    _box(g, 8, 18, 8.7, 32, 'K')
    _box(g, 39.3, 18, 40, 32, 'K')
    for x0 in (3, 42):
        _box(g, x0, 32, x0 + 3, 36, 'M')
    return _finish(g, SHADE)


def chair_front():
    rows = [list(r) for r in chair()]
    for y, row in enumerate(rows):
        for x in range(len(row)):
            if not (x < 8 * K or x >= 40 * K or y >= 22 * K):  # armrests + seat front cover the sitter
                row[x] = '.'
    return [''.join(r) for r in rows]


def loco():
    g = _blank(80, 54)
    _box(g, 0, 4, 31, 9, 'r')  # cab roof
    _box(g, 2, 8, 28, 44, 'B')
    _box(g, 6, 14, 22, 26, 'b')
    _box(g, 8, 16, 20, 24, '.')  # cab window: the driver shows through
    _box(g, 6, 26, 22, 27, 'Y')
    _thin(g, (5, 30), (5, 42), 'b')
    _thin(g, (23, 30), (23, 42), 'b')
    _box(g, 26, 20, 72, 44, 'R')  # boiler
    _ell(g, 72, 32, 3.5, 12, 'R')
    for x in (36, 48, 60):
        _box(g, x, 20, x + 2, 44, 'Y')
    _ell(g, 45, 19, 5, 5, 'Y')  # dome
    _box(g, 56, 8, 66, 22, 'N')  # chimney
    _box(g, 53, 2, 69, 8, 'N')
    _box(g, 70, 20, 78, 28, 'S')  # lamp
    _ell(g, 74, 24, 2.2, 2.2, 'Y')
    _ell(g, 73.4, 23.4, 0.7, 0.7, 'W')
    _tri(g, (70, 42), (80, 53), (70, 53), 'S')  # cowcatcher
    _box(g, 0, 42, 74, 47, 'N')
    for cx in (14, 38, 58):
        _wheel(g, cx, 46.5, 6.5)
    _line(g, [(14, 48), (38, 48), (58, 48)], 0.6, 'S')  # connecting rod
    return _finish(g, SHADE)


WAGON_COLORS = (('R', 'r'), ('B', 'b'), ('G', 'i'), ('Y', 'y'))


def wagon(i):
    c, dark = WAGON_COLORS[i]
    g = _blank(52, 38)
    _box(g, 2, 8, 50, 28, c)
    _box(g, 0, 6, 52, 9, dark)
    for x in (4, 48):
        _thin(g, (x, 10), (x, 26), dark)
    _box(g, 6, 12, 46, 22, 'C')  # name plate
    _box(g, 0, 26, 52, 30, 'N')
    _box(g, 0, 21, 2, 25, 'N')
    for cx in (12, 40):
        _wheel(g, cx, 31.5, 5.5, 5)
    return _finish(g, SHADE)


def ball():
    g = _blank(14, 14)
    _ell(g, 7, 7, 6.3, 6.3, 'T')
    _line(g, [(1.5, 5), (5, 7.5), (8.5, 7.5), (12.5, 5)], 0.5, 'W')
    _line(g, [(7, 1), (7, 13)], 0.4, 'Y')
    return _finish(g, SHADE)


def pizza():
    g = _blank(20, 18)
    _tri(g, (0.5, 3), (19.5, 3), (10, 17.5), 'Y')
    _ell(g, 10, 2.6, 9.8, 2.4, 'M')  # crust
    for x, y in ((6, 6.5), (13, 7), (9.5, 11.5)):
        _ell(g, x, y, 1.9, 1.7, 'R')
        _ell(g, x - 0.5, y - 0.5, 0.5, 0.5, 'q')
    for x, y in ((4, 8.5), (15.5, 9.5), (11, 15)):  # basil
        _ell(g, x, y, 0.9, 0.6, 'G')
    _line(g, [(14, 13), (14.6, 15.5)], 0.5, 'Y')  # cheese drip
    return _finish(g, SHADE)


def coffee():
    g = _blank(18, 16)
    for x in (4, 8):  # steam
        _line(g, [(x, 3.2), (x + 1, 2), (x, 0.8), (x + 1, 0)], 0.35, 'S')
    _ell(g, 14.5, 9.5, 3, 3.5, 'W')
    _ell(g, 14.5, 9.5, 1.3, 1.9, '.')
    _ell(g, 7, 14.5, 6, 1.4, 'W')
    _ell(g, 7, 5, 6, 1.6, 'W')
    g2 = g
    for y in range(int(5 * K), int(14.5 * K)):
        for x in range(int(1 * K), int(13 * K)):
            g2[y][x] = 'W'
    _ell(g, 7, 5, 5, 1.1, 'M')  # coffee surface
    _ell(g, 6.3, 10, 1.1, 1, 'R')
    _ell(g, 7.7, 10, 1.1, 1, 'R')
    _tri(g, (5.3, 10.3), (8.7, 10.3), (7, 12.3), 'R')  # heart
    return _finish(g, SHADE)


def popcorn():
    g = _blank(16, 20)
    for x, y in ((3, 7), (6, 5.5), (9, 6), (12.5, 7), (4.5, 4), (8, 3), (11, 4), (7, 1.5), (13.5, 5)):
        _ell(g, x, y, 2.1, 1.9, 'C')
        _ell(g, x + 0.5, y + 0.4, 0.6, 0.5, 'Y')
    _tri(g, (1, 8), (15, 8), (13, 19.5), 'W')
    _tri(g, (1, 8), (13, 19.5), (3, 19.5), 'W')
    for x0 in (2.2, 7, 11.8):  # red stripes, narrowing to the bottom
        _tri(g, (x0, 8), (x0 + 2.4, 8), (x0 * 0.8 + 2.4 * 0.8 + 1.4, 19.5), 'R')
        _tri(g, (x0, 8), (x0 * 0.8 + 2.4 * 0.8 + 1.4, 19.5), (x0 * 0.8 + 1.6, 19.5), 'R')
    _ell(g, 8, 13.5, 2.6, 2, 'Y')
    return _finish(g, SHADE)


def banana():
    g = _blank(16, 14)
    _line(g, [(2, 9.5), (5.5, 11.5), (10, 11), (13, 7.5), (13.6, 3)], 2.2, 'Y')
    _line(g, [(4, 9), (9.5, 9.6), (12, 6.5)], 0.6, 'z')
    _ell(g, 1.2, 9.2, 1, 1, 'M')
    _line(g, [(13.6, 3), (13.4, 0.6)], 0.8, 'M')
    return _finish(g, SHADE)


def flame(i):
    """Cartoon flame (This is Fine), two flicker frames."""
    g = _blank(16, 24)
    sway = (-1.5, 1.5)[i]
    _ell(g, 8, 17, 6.5, 6.5, 'R')
    _tri(g, (1.8, 16), (14.2, 16), (8 + sway * 1.5, 1), 'R')
    _ell(g, 8, 18.5, 4.5, 4.5, 'o')
    _tri(g, (3.8, 18), (12.2, 18), (8 - sway, 6), 'o')
    _ell(g, 8, 20, 2.5, 2.8, 'Y')
    _tri(g, (5.6, 20), (10.4, 20), (8 + sway * 0.5, 12), 'Y')
    return _finish(g)


def hammer(down):
    """Squeaky toy mallet: raised (diagonal) or striking (horizontal)."""
    g = _blank(24, 24)
    if down:  # head lying flat on top of the victim
        _line(g, [(22, 2), (13, 12)], 1.1, 'M')
        _line(g, [(4, 15), (20, 15)], 3.6, 'R')
        for x in (7, 17):
            _line(g, [(x, 12), (x, 18)], 0.6, 'Y')
    else:
        _line(g, [(4, 21), (14, 9)], 1.1, 'M')
        _line(g, [(9, 2), (21, 14)], 3.6, 'R')
        for a, b in (((9, 6), (13, 2)), ((17, 14), (21, 10))):
            _line(g, [a, b], 0.6, 'Y')
    return _finish(g, SHADE)


def chefhat():
    g = _blank(20, 16)
    for x, y, r in ((5, 6.5, 4.4), (10, 4.8, 5), (15, 6.5, 4.4)):
        _ell(g, x, y, r, r * 0.9, 'W')
    _box(g, 4, 9, 16, 15, 'W')
    _thin(g, (8, 10), (8, 14), 'v')
    _thin(g, (12, 10), (12, 14), 'v')
    return _finish(g, SHADE)


def stove():
    g = _blank(32, 24)
    _box(g, 2, 9, 30, 24, 'S')
    _box(g, 1, 8, 31, 10, 'N')
    _box(g, 6, 13, 22, 21, 'N')
    _box(g, 7.5, 14.5, 20.5, 19.5, 'o')  # oven glow
    for x in (25.5, 28):
        _ell(g, x, 14, 1, 1, 'N')
    _ell(g, 14, 6.5, 9, 2, 'N')  # pan
    _line(g, [(22, 6.5), (30, 4)], 0.8, 'M')
    _ell(g, 12, 5.6, 3.2, 1.1, 'W')  # egg
    _ell(g, 12.4, 5.4, 1.1, 0.8, 'Y')
    _ell(g, 17, 5.8, 1.6, 0.8, 'M')  # bacon-ish bit
    return _finish(g, SHADE)


def suitcase():
    g = _blank(20, 16)
    _line(g, [(7, 5), (7, 2), (13, 2), (13, 5)], 0.7, 'N')
    _box(g, 1, 4, 19, 15.5, 'M')
    for x in (5, 15):
        _box(g, x, 4, x + 1.4, 15.5, 'X')
    _box(g, 8, 7, 12, 10, 'R')  # stickers
    _ell(g, 4, 12, 1.4, 1.4, 'B')
    _box(g, 13.5, 11, 17, 13.5, 'Y')
    return _finish(g, {**SHADE, 'M': ('j', 'X')})


def trophy():
    g = _blank(20, 24)
    for x in (3.5, 16.5):
        _ell(g, x, 8, 2.6, 3.2, 'Y')
        _ell(g, x, 8, 1.2, 1.8, '.')
    _box(g, 4, 3, 16, 9, 'Y')
    _ell(g, 10, 9, 6, 5.5, 'Y')
    _ell(g, 10, 3, 6, 1.4, 'y')
    _box(g, 8.6, 13.5, 11.4, 18, 'Y')
    _box(g, 5, 18, 15, 23.5, 'M')
    _box(g, 7, 19.5, 13, 22, 'Y')
    _ell(g, 7.5, 7, 0.8, 1.6, 'W')
    return _finish(g, SHADE)


def tombstone():
    g = _blank(24, 28)
    _ell(g, 12, 10, 10, 8.5, 'S')
    _box(g, 2, 10, 22, 25, 'S')
    _thin(g, (16, 6), (14, 10), 'n')
    _thin(g, (14, 10), (16, 13), 'n')
    _ell(g, 12, 26, 12, 2.5, 'G')
    for x in (3, 8, 15, 20):
        _tri(g, (x - 1, 25), (x + 1, 25), (x, 22.5), 'G')
    return _finish(g, SHADE)


def box(front_only=False):
    """Cardboard box; front_only = the front face drawn over a pet sitting inside."""
    g = _blank(40, 24)
    if not front_only:
        _tri(g, (2, 9), (12, 9), (-1, 2), 'x')  # open flaps
        _tri(g, (28, 9), (38, 9), (41, 2), 'x')
        _box(g, 4, 6, 36, 10, 'X')
    _box(g, 2, 9, 38, 24, 'x')
    _box(g, 17, 9, 23, 13, 'C')  # tape
    _thin(g, (6, 15), (12, 15), 'X')  # 'fragile' scribble
    _thin(g, (6, 17), (10, 17), 'X')
    return _finish(g, SHADE)


def ghost():
    g = _blank(24, 28)
    _ell(g, 12, 10, 10, 9, 'W')
    _box(g, 2, 10, 22, 23, 'W')
    for x in (2, 8.7, 15.4):
        _tri(g, (x, 22), (x + 6.6, 22), (x + 3.3, 27), 'W')
    _ell(g, 8, 10, 1.8, 2.4, 'N')
    _ell(g, 16, 10, 1.8, 2.4, 'N')
    _ell(g, 12, 16, 2.4, 3, 'N')
    _ell(g, 4.5, 13.5, 1.4, 0.8, 'P')
    _ell(g, 19.5, 13.5, 1.4, 0.8, 'P')
    return _finish(g, SHADE)


PROPS = {'chair': chair(), 'chair_front': chair_front(), 'loco': loco(), 'ball': ball(), 'pizza': pizza(),
         'coffee': coffee(), 'popcorn': popcorn(), 'banana': banana(),
         'flame0': flame(0), 'flame1': flame(1), 'hammer_up': hammer(False), 'hammer_down': hammer(True),
         'chefhat': chefhat(), 'stove': stove(), 'suitcase': suitcase(), 'trophy': trophy(),
         'tombstone': tombstone(), 'box': box(), 'box_front': box(True), 'ghost': ghost(),
         **{'wagon%d' % i: wagon(i) for i in range(4)}}
