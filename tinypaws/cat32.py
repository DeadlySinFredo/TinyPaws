"""High-detail 32x32 cat frames, drawn procedurally (ellipses/lines) then shaded + outlined.

Rendered at density 2: on screen the cat keeps its 16-unit size, with twice the detail.
"""
import math

W = 32


def _blank(w=W, h=W):
    return [['.'] * w for _ in range(h)]


def _ell(g, cx, cy, rx, ry, c):
    for y in range(max(0, int(cy - ry - 1)), min(len(g), int(cy + ry + 2))):
        for x in range(max(0, int(cx - rx - 1)), min(len(g[0]), int(cx + rx + 2))):
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                g[y][x] = c


def _line(g, pts, r, c):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            _ell(g, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r, c)


def _tri(g, a, b, c, col):
    xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
    for y in range(max(0, int(min(ys))), min(len(g), int(max(ys)) + 1)):
        for x in range(max(0, int(min(xs))), min(len(g[0]), int(max(xs)) + 1)):
            px, py = x + .5, y + .5
            d1 = (px - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (py - b[1])
            d2 = (px - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (py - c[1])
            d3 = (px - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (py - a[1])
            if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
                g[y][x] = col


def _px(g, pts, c):
    for x, y in pts:
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            g[y][x] = c


def _finish(g):
    """Shade fur (top highlight, bottom shadow) and add a 1px dark outline."""
    h, w = len(g), len(g[0])
    s = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] == 'O':
                if y + 1 >= h or g[y + 1][x] == '.':
                    s[y][x] = 'D'
                elif y == 0 or g[y - 1][x] == '.':
                    s[y][x] = 'H'
    out = [r[:] for r in s]
    for y in range(h):
        for x in range(w):
            if s[y][x] == '.' and any(0 <= y + dy < h and 0 <= x + dx < w and s[y + dy][x + dx] != '.'
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'K'
    return [''.join(r) for r in out]


def _eyes(g, pts, mode):
    """Big chibi eyes, 3x4 px, top-left at each point."""
    for x, y in pts:
        if mode == 'closed':
            _px(g, [(x, y + 2), (x + 1, y + 1), (x + 2, y + 2)], 'S')
        elif mode == 'wide':
            for j in range(5):
                _px(g, [(x - 1 + i, y - 1 + j) for i in range(4)], 'W')
            _px(g, [(x, y + 1), (x + 1, y + 1), (x, y + 2), (x + 1, y + 2)], 'E')
        else:
            for j in range(4):
                _px(g, [(x + i, y + j) for i in range(3)], 'E')
            _px(g, [(x, y), (x + 1, y), (x, y + 1)], 'W')  # big catchlight
            _px(g, [(x + 2, y + 3)], 'W')


def _head(g, hx, hy, eyes='open'):
    """Chibi 3/4 head facing right, centred at (hx, hy)."""
    _tri(g, (hx - 7, hy - 2), (hx - 5, hy - 11), (hx - 0.5, hy - 5.5), 'O')
    _tri(g, (hx + 0.5, hy - 5.5), (hx + 5, hy - 11), (hx + 7, hy - 2), 'O')
    _tri(g, (hx - 5.5, hy - 4), (hx - 4.8, hy - 8.8), (hx - 2.2, hy - 5.5), 'P')
    _tri(g, (hx + 2, hy - 5.5), (hx + 4.6, hy - 8.8), (hx + 5.5, hy - 4), 'P')
    _ell(g, hx, hy, 8, 6.8, 'O')
    _ell(g, hx + 1.5, hy + 3.2, 5, 3.2, 'L')
    _px(g, [(int(hx) + 1, int(hy) - 4), (int(hx) + 1, int(hy) - 3), (int(hx) + 1, int(hy) - 2)], 'L')
    _eyes(g, [(int(hx) - 5, int(hy) - 2), (int(hx) + 3, int(hy) - 2)], eyes)
    _px(g, [(int(hx) + 1, int(hy) + 2), (int(hx) + 2, int(hy) + 2)], 'P')
    _px(g, [(int(hx), int(hy) + 4), (int(hx) + 1, int(hy) + 4), (int(hx) + 3, int(hy) + 4)], 'K')
    _px(g, [(int(hx) - 5, int(hy) + 3), (int(hx) + 6, int(hy) + 3)], 'P')  # blush


def front(eyes='open', arms='down'):
    """Front-facing sitting chibi cat (idle pose); arms='up' = ABSOLUTE CINEMA."""
    g = _blank()
    _line(g, [(23, 29), (28.5, 27.5), (29, 20)], 1.6, 'O')
    _ell(g, 29, 19.5, 1.7, 1.7, 'D')
    if arms == 'up':
        _line(g, [(10, 22), (5, 10)], 1.7, 'O')
        _line(g, [(22, 22), (27, 10)], 1.7, 'O')
        _ell(g, 4.5, 8, 2.4, 2.3, 'L')
        _ell(g, 27.5, 8, 2.4, 2.3, 'L')
    _ell(g, 16, 24.5, 7.5, 6, 'O')
    _ell(g, 16, 24.5, 4, 4.5, 'L')
    _ell(g, 11.5, 29.6, 2.8, 1.5, 'L')
    _ell(g, 20.5, 29.6, 2.8, 1.5, 'L')
    if arms == 'down':
        _line(g, [(12, 21), (13, 27.5)], 1.5, 'O')
        _line(g, [(20, 21), (19, 27.5)], 1.5, 'O')
        _ell(g, 13.3, 28.6, 2, 1.4, 'L')
        _ell(g, 18.7, 28.6, 2, 1.4, 'L')
    _tri(g, (7, 9), (8.5, 0.5), (13.5, 4.5), 'O')
    _tri(g, (18.5, 4.5), (23.5, 0.5), (25, 9), 'O')
    _tri(g, (8.8, 6.5), (9.3, 2.8), (12.2, 4.8), 'P')
    _tri(g, (19.8, 4.8), (22.7, 2.8), (23.2, 6.5), 'P')
    _ell(g, 16, 11, 9, 7.3, 'O')
    _ell(g, 16, 14.8, 5.6, 3.6, 'L')
    _px(g, [(15, 5), (16, 5), (15, 6), (16, 6), (15, 7), (16, 7)], 'L')  # tuxedo blaze
    _eyes(g, [(10, 9), (19, 9)], eyes)
    _px(g, [(15, 13), (16, 13)], 'P')
    _px(g, [(14, 15), (15, 16), (16, 16), (17, 15)], 'K')
    _px(g, [(9, 14), (10, 14), (21, 14), (22, 14)], 'P')
    return _finish(g)


def _leg(g, top, bottom, c, paw=True):
    _line(g, [top, bottom], 1.5, c)
    if paw:
        _ell(g, bottom[0] + .6, bottom[1] + .3, 2, 1.3, 'L')


LEGS = {  # far back, far front, near back, near front: (top_x, bottom_x)
    'stand': ((9, 9), (19, 19), (12, 12), (22, 22)),
    'walk1': ((9, 11), (19, 16), (12, 9), (22, 25)),
    'walk2': ((9, 6), (19, 22), (12, 14), (22, 19)),
}


def _standing(legs='stand', eyes='open', shift=0, tail=True):
    g = _blank(W + shift, W)
    o = shift / 2
    fb, ff, nb, nf = LEGS[legs]
    if tail:
        wag = {'walk1': 1, 'walk2': -1}.get(legs, 0)
        _line(g, [(6 + o, 19), (3 + o, 13), (4 + o + wag, 6)], 1.6, 'O')
        _ell(g, 4 + o + wag, 5.5, 1.6, 1.6, 'D')
    for (a, b) in (fb, ff):
        _leg(g, (a + o, 22), (b + o, 28.8), 'D')
    _ell(g, 14 + o, 22, 8.5, 5, 'O')
    _ell(g, 19 + o, 23, 3.4, 3, 'L')
    for x in (9, 12, 15):
        _px(g, [(int(x + o), 15), (int(x + o), 16), (int(x + o) + 1, 16)], 'D')
    for (a, b) in (nb, nf):
        _leg(g, (a + o, 23), (b + o, 28.8), 'O')
    _head(g, 22 + o, 11.5, eyes)
    return g


def stand(legs='stand', eyes='open'):
    return _finish(_standing(legs, eyes))


def sit(eyes='open'):
    g = _blank()
    _line(g, [(10, 29.5), (4, 29), (2.5, 25)], 1.5, 'O')
    _ell(g, 14, 22, 7, 7.5, 'O')
    _ell(g, 12, 25.5, 6, 4.5, 'O')
    _ell(g, 19, 21, 3.4, 4, 'L')
    _leg(g, (18, 22), (18, 29), 'D')
    _leg(g, (21, 22), (21, 29), 'O')
    _ell(g, 9, 29.3, 2.4, 1.3, 'L')
    _head(g, 20, 11.5, eyes)
    return _finish(g)


def jump(eyes='open'):
    g = _blank()
    _line(g, [(6, 16), (2.5, 12), (2, 7)], 1.6, 'O')
    _leg(g, (9, 19), (4, 25), 'D')
    _leg(g, (20, 19), (26, 25), 'D')
    _ell(g, 15, 17, 10, 5, 'O')
    _ell(g, 21, 18.5, 3.5, 2.8, 'L')
    _leg(g, (11, 20), (6, 27), 'O')
    _leg(g, (22, 20), (28, 26.5), 'O')
    _head(g, 23, 11.5, eyes)
    return _finish(g)


def sleep():
    g = _blank()
    _ell(g, 15, 25.5, 11, 5.2, 'O')
    for x in (8, 11, 14):
        _px(g, [(x, 21), (x, 22), (x + 1, 22)], 'D')
    _head(g, 23, 24.5, 'closed')
    _line(g, [(4, 28), (8, 30.3), (17, 30.3)], 1.3, 'D')
    return _finish(g)


def flex():
    g = _standing(shift=8, tail=True)
    _line(g, [(15, 17), (8, 17), (8, 10)], 1.7, 'D')  # back arm (behind body would be hidden; keep visible)
    _ell(g, 10.5, 15.5, 2.4, 2, 'D')
    _ell(g, 8, 9, 2.1, 2.1, 'L')
    _line(g, [(27, 19), (34, 19), (34, 12)], 1.8, 'O')
    _ell(g, 31, 17.2, 2.8, 2.2, 'O')  # bicep
    _ell(g, 34, 10.5, 2.2, 2.2, 'L')
    for x in range(20, 33):  # sunglasses
        _px(g, [(x, 9)], 'N')
    for x in (20, 21, 22, 23, 28, 29, 30, 31):
        _px(g, [(x, 10), (x, 11), (x, 12)], 'N')
    _px(g, [(21, 10), (29, 10)], 'S')
    return _finish(g)


FRAMES = {
    'idle': front(), 'blink': front('closed'), 'happy': front('closed'),
    'walk1': stand('walk1'), 'walk2': stand('walk2'), 'jump': jump(),
    'sit': sit(), 'surprised': front('wide'), 'stretch': jump('closed'),
    'sleep': sleep(), 'flex': flex(), 'cinema': front(arms='up'),
}
