"""Detailed props (same 48-raster generator as the pets, density 3).

Design coordinates are 2x the logical size, so layouts the brain relies on
(cab window, chair seat, wagon plate) keep their old logical positions.
"""
import math

from .cat32 import K, _blank, _ell, _finish, _line, _thin, _tri

COLORS = {
    'q': '#f06a5e', 'u': '#6b9cf0', 'y': '#c9a227', 'n': '#4a4a58', 's': '#c4c4d0',
    't': '#1f8f86', 'j': '#e0a965', 'i': '#2b8f45', 'k': '#6fdc8a', 'z': '#ffe680',
}
SHADE = {'R': ('q', 'r'), 'B': ('u', 'b'), 'Y': ('z', 'y'), 'N': ('n', None), 'T': ('W', 't'),
         'W': (None, 's'), 'G': ('k', 'i'), 'M': ('j', None), 'S': ('s', 'n'), 'C': ('W', 'j')}


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


PROPS = {'chair': chair(), 'chair_front': chair_front(), 'loco': loco(), 'ball': ball(), 'pizza': pizza(),
         'coffee': coffee(), 'popcorn': popcorn(), 'banana': banana(),
         **{'wagon%d' % i: wagon(i) for i in range(4)}}
