"""High-detail pet frames, drawn procedurally (ellipses/lines) then shaded + outlined.

Shapes are designed on a 32-unit grid and rasterised K times finer (48x48 px),
rendered at density 3: the pet keeps its 16-unit layout size with 3x the detail.
"""
import math

W = 32   # design grid
K = 1.5  # raster pixels per design unit
DENSITY = 3


def _blank(w=W, h=W):
    return [['.'] * int(w * K) for _ in range(int(h * K))]


def _ell(g, cx, cy, rx, ry, c):
    _ell_px(g, cx * K, cy * K, rx * K, ry * K, c)


def _ell_px(g, cx, cy, rx, ry, c):
    for y in range(max(0, int(cy - ry - 1)), min(len(g), int(cy + ry + 2))):
        for x in range(max(0, int(cx - rx - 1)), min(len(g[0]), int(cx + rx + 2))):
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                g[y][x] = c


def _line(g, pts, r, c):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2 * K) + 1
        for i in range(n + 1):
            t = i / n
            _ell_px(g, (x0 + (x1 - x0) * t) * K, (y0 + (y1 - y0) * t) * K, r * K, r * K, c)


def _tri(g, a, b, c, col):
    a, b, c = [(p[0] * K, p[1] * K) for p in (a, b, c)]
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
    """Fill design-grid cells (each covers ~K x K raster pixels)."""
    for x, y in pts:
        for yy in range(int(y * K), int((y + 1) * K)):
            for xx in range(int(x * K), int((x + 1) * K)):
                if 0 <= yy < len(g) and 0 <= xx < len(g[0]):
                    g[yy][xx] = c


def _thin(g, p0, p1, c):
    """1-raster-pixel line (whiskers)."""
    (x0, y0), (x1, y1) = (p0[0] * K, p0[1] * K), (p1[0] * K, p1[1] * K)
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        x, y = int(x0 + (x1 - x0) * i / n), int(y0 + (y1 - y0) * i / n)
        if 0 <= y < len(g) and 0 <= x < len(g[0]) and g[y][x] != '.':
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
    """Big chibi eyes (~3x4 design units, top-left at each point), round with catchlights."""
    for x, y in pts:
        cx, cy = x + 1.5, y + 2
        if mode == 'closed':
            _line(g, [(cx - 1.4, cy + 0.3), (cx, cy - 0.6), (cx + 1.4, cy + 0.3)], 0.35, 'S')
        elif mode == 'wide':
            _ell(g, cx, cy, 2.1, 2.5, 'W')
            _ell(g, cx, cy + 0.2, 0.9, 1.1, 'E')
        else:
            _ell(g, cx, cy, 1.6, 2.1, 'E')
            _ell(g, cx, cy + 0.9, 1.1, 0.9, 'g')
            _ell(g, cx, cy + 0.2, 0.8, 1.2, 'E')
            _ell(g, cx - 0.6, cy - 0.9, 0.7, 0.7, 'W')  # catchlight
            _ell(g, cx + 0.8, cy + 1.2, 0.35, 0.35, 'W')


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
    for dy in (-0.6, 0.6):
        _thin(g, (hx + 3, hy + 3), (hx + 7.8, hy + 2.6 + dy * 2), 'S')


def _front_head_cat(g, eyes):
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
    for dy in (-0.8, 0.8):
        _thin(g, (12.5, 15), (7.6, 14.6 + dy), 'S')
        _thin(g, (19.5, 15), (24.4, 14.6 + dy), 'S')


def front(eyes='open', arms='down', sp='cat'):
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
    HEADS[sp][1](g, eyes)
    return _finish(g)


def _leg(g, top, bottom, c, paw=True):
    _line(g, [top, bottom], 1.5, c)
    if paw:
        _ell(g, bottom[0] + .6, bottom[1] + .3, 2, 1.3, 'L')


# style: (frames, stride px, paw lift px, body drop px, leg phases: far hind, far front, near hind, near front)
GAITS = {
    'stand': (1, 0, 0, 0, (0, 0, 0, 0)),
    'walk': (8, 7, 2.6, 0, (0.5, 0.75, 0.0, 0.25)),   # lateral-sequence walk
    'run': (6, 10, 4.0, 0, (0.08, 0.6, 0.0, 0.5)),     # gallop: hinds then fronts
    'sneak': (8, 4, 1.6, 3, (0.5, 0.75, 0.0, 0.25)),  # crouched stalk
}
SWING = 0.4  # part of the cycle a paw is in the air


def _foot(phase, stride, lift):
    """Paw offset along the cycle: in the air it arcs forward, on the ground it slides back."""
    if phase < SWING:
        u = phase / SWING
        return -stride / 2 + stride * u, math.sin(math.pi * u) * lift
    u = (phase - SWING) / (1 - SWING)
    return stride / 2 - stride * u, 0.0


def _jleg(g, hip, foot, up, front, c, crouch=0.0):
    """Two-segment leg: front knees fold back under a lifted paw, hind hocks point back."""
    mx, my = (hip[0] + foot[0]) / 2, (hip[1] + foot[1]) / 2
    knee = (mx + (-1 if front else -1.6) * (0.4 + up * 0.5 + crouch), my - up * 0.3)
    if c == 'O':  # near legs get their own outline so they read against the body
        _line(g, [(hip[0], hip[1] + 2.5), knee, foot], 2.25, 'K')
    _line(g, [hip, knee, foot], 1.45, c)
    _ell(g, foot[0] + .7, foot[1] + .2, 2, 1.25, 'L' if c == 'O' else 'D')


def _standing(style='stand', i=0, eyes='open', shift=0, tail=True, sp='cat'):
    g = _blank(W + shift, W)
    o = shift / 2
    n, stride, lift, drop, phases = GAITS[style]
    t = i / n
    bob = -0.7 * abs(math.sin(2 * math.pi * t)) if style == 'walk' else 0.0
    if style == 'run':
        bob = -1.2 * math.sin(2 * math.pi * t)
    by = 20 + drop + bob
    if tail:
        if style == 'run':
            pts = [(6 + o, by - 2), (2.5 + o, by - 4.5), (1.5 + o, by - 8 + math.sin(2 * math.pi * t))]
        elif style == 'sneak':
            pts = [(6 + o, by - 1), (2.5 + o, by + 1), (1.8 + o, by - 2 + math.sin(2 * math.pi * t))]
        else:
            sway = 1.4 * math.sin(2 * math.pi * t)
            pts = [(6 + o, by - 3), (3 + o, by - 9), (4 + o + sway, by - 16)]
        _line(g, pts, 1.6, 'O')
        _ell(g, pts[-1][0], pts[-1][1], 1.6, 1.6, 'D')
    hips = ((8.5, by), (18.5, by), (11.5, by + 1), (20.5, by + 1))  # far hind, far front, near hind, near front
    for k in (0, 1, 2, 3):
        dx, up = _foot((t + phases[k]) % 1.0, stride, lift)
        hx, hy = hips[k]
        c = 'D' if k < 2 else 'O'
        _jleg(g, (hx + o, hy), (hx + o + dx, 28.8 - up), up, k % 2 == 1, c, drop * 0.6)
        if k == 1:  # body between far and near legs
            _ell(g, 14 + o, by, 8.5 + (0.8 * math.cos(2 * math.pi * t) if style == 'run' else 0), 4.6, 'O')
            _ell(g, 19 + o, by + 1, 3.4, 3, 'L')
            for x in (9, 12, 15):
                _px(g, [(int(x + o), int(by - 4)), (int(x + o), int(by - 3)), (int(x + o) + 1, int(by - 3))], 'D')
    hy = 10.5 + drop * 1.1 + bob * 0.6
    HEADS[sp][0](g, 22 + o + (1 if style == 'sneak' else 0), hy, eyes)
    return g


def stand(style='stand', i=0, eyes='open', sp='cat'):
    return _finish(_standing(style, i, eyes, sp=sp))


def sit(eyes='open', sp='cat'):
    g = _blank()
    _line(g, [(10, 29.5), (4, 29), (2.5, 25)], 1.5, 'O')
    _ell(g, 14, 22, 7, 7.5, 'O')
    _ell(g, 12, 25.5, 6, 4.5, 'O')
    _ell(g, 19, 21, 3.4, 4, 'L')
    _leg(g, (18, 22), (18, 29), 'D')
    _leg(g, (21, 22), (21, 29), 'O')
    _ell(g, 9, 29.3, 2.4, 1.3, 'L')
    HEADS[sp][0](g, 20, 11.5, eyes)
    return _finish(g)


def jump(eyes='open', sp='cat'):
    g = _blank()
    _line(g, [(6, 16), (2.5, 12), (2, 7)], 1.6, 'O')
    _leg(g, (9, 19), (4, 25), 'D')
    _leg(g, (20, 19), (26, 25), 'D')
    _ell(g, 15, 17, 10, 5, 'O')
    _ell(g, 21, 18.5, 3.5, 2.8, 'L')
    _leg(g, (11, 20), (6, 27), 'O')
    _leg(g, (22, 20), (28, 26.5), 'O')
    HEADS[sp][0](g, 23, 11.5, eyes)
    return _finish(g)


def sleep(sp='cat'):
    g = _blank()
    _ell(g, 15, 25.5, 11, 5.2, 'O')
    for x in (8, 11, 14):
        _px(g, [(x, 21), (x, 22), (x + 1, 22)], 'D')
    HEADS[sp][0](g, 23, 24.5, 'closed')
    _line(g, [(4, 28), (8, 30.3), (17, 30.3)], 1.3, 'D')
    return _finish(g)


def flex(sp='cat'):
    g = _standing(shift=8, tail=True, sp=sp)
    _line(g, [(15, 17), (8, 17), (8, 10)], 1.7, 'D')  # back arm (behind body would be hidden; keep visible)
    _ell(g, 10.5, 15.5, 2.4, 2, 'D')
    _ell(g, 8, 9, 2.1, 2.1, 'L')
    _line(g, [(27, 19), (34, 19), (34, 12)], 1.8, 'O')
    _ell(g, 31, 17.2, 2.8, 2.2, 'O')  # bicep
    _ell(g, 34, 10.5, 2.2, 2.2, 'L')
    l, r = (21, 29) if sp == 'cat' else (25, 30)  # eye x positions of the side head at hx=26
    for x in range(l - 1, r + 3):  # sunglasses
        _px(g, [(x, 9 if sp == 'cat' else 8)], 'N')
    for x in (l - 1, l, l + 1, l + 2, r, r + 1, r + 2):
        _px(g, [(x, y) for y in ((10, 11, 12) if sp == 'cat' else (9, 10, 11))], 'N')
    _px(g, [(l, 10 if sp == 'cat' else 9), (r + 1, 10 if sp == 'cat' else 9)], 'S')
    return _finish(g)


def _head_dog(g, hx, hy, eyes='open'):
    """Puppy 3/4 head facing right: floppy ear, long snout, big nose."""
    _ell(g, hx, hy, 7.5, 6.5, 'O')
    _ell(g, hx + 4.5, hy + 2.6, 4.2, 2.9, 'L')
    _px(g, [(int(hx) + 1, int(hy) - 5), (int(hx) + 1, int(hy) - 4), (int(hx) + 2, int(hy) - 3)], 'L')
    _ell(g, hx - 3.5, hy + 0.5, 2.7, 5.2, 'M')  # floppy ear
    _eyes(g, [(int(hx) - 1, int(hy) - 3), (int(hx) + 4, int(hy) - 3)], eyes)
    _ell(g, hx + 7.7, hy + 1.3, 1.6, 1.3, 'E')
    _px(g, [(int(hx) + 7, int(hy) + 0)], 'W')
    _px(g, [(int(hx) + 4, int(hy) + 4), (int(hx) + 5, int(hy) + 4), (int(hx) + 6, int(hy) + 4)], 'K')
    if eyes == 'closed':
        _px(g, [(int(hx) + 5, int(hy) + 5), (int(hx) + 6, int(hy) + 5), (int(hx) + 5, int(hy) + 6)], 'P')  # tongue


def _front_head_dog(g, eyes):
    _ell(g, 8, 11.5, 3, 6, 'M')
    _ell(g, 24, 11.5, 3, 6, 'M')
    _ell(g, 16, 10.5, 7.5, 6.8, 'O')
    _ell(g, 16, 15, 5.2, 3.6, 'L')
    _px(g, [(15, 5), (16, 5), (15, 6), (16, 6), (15, 7), (16, 7), (15, 8), (16, 8)], 'L')
    _eyes(g, [(10, 9), (19, 9)], eyes)
    _ell(g, 16, 13.4, 2, 1.3, 'E')
    _px(g, [(15, 13)], 'W')
    _px(g, [(14, 16), (15, 16), (16, 16), (17, 16)], 'K')
    if eyes == 'closed':
        _px(g, [(15, 17), (16, 17), (15, 18), (16, 18)], 'P')  # tongue out = happy


HEADS = {'cat': (_head, _front_head_cat), 'dog': (_head_dog, _front_head_dog)}
_DOG = str.maketrans('ODHL', 'Aahc')  # recolor cat fur chars to dog palette


def frames(sp='cat'):
    f = {
        'idle': front(sp=sp), 'blink': front('closed', sp=sp), 'happy': front('closed', sp=sp),
        'jump': jump(sp=sp),
        'sit': sit(sp=sp), 'surprised': front('wide', sp=sp), 'stretch': jump('closed', sp=sp),
        'sleep': sleep(sp=sp), 'flex': flex(sp=sp), 'cinema': front(arms='up', sp=sp),
    }
    for style in ('walk', 'run', 'sneak'):
        for i in range(GAITS[style][0]):
            f['%s%d' % (style, i)] = stand(style, i, sp=sp)
    f['walk2'] = f['walk4']  # walk1/walk2: legacy two-frame names used by emotes and reactions.json
    if sp == 'dog':
        f = {'dog:' + k: [r.translate(_DOG) for r in v] for k, v in f.items()}
    return f


# breed -> colors for the species' fur chars; first breed per species = base look (no prefix needed)
BREEDS = {
    'cat': {
        'tuxedo': ('Tuxedo (schwarz-weiß)', None),
        'orange': ('Rote Tigerkatze', ('#e8913a', '#b5611c', '#f7b567', '#fff1dc')),
        'gray': ('Graue Kurzhaar', ('#8b909e', '#626674', '#acb1bd', '#eef0f4')),
        'white': ('Weiße Katze', ('#f1eee8', '#cfc8bd', '#ffffff', '#fde4ea')),
        'black': ('Schwarze Katze', ('#25222c', '#16141b', '#3a3644', '#2e2b36')),
        'cream': ('Creme / Siam-Look', ('#efe0c4', '#c7ab80', '#fff3dc', '#fff9ee')),
    },
    'dog': {
        'beagle': ('Beagle', None),
        'golden': ('Golden Retriever', ('#e3a857', '#b77b30', '#f3c982', '#fbe8c3', '#cc8d3d')),
        'husky': ('Husky', ('#6f7683', '#4b515c', '#929aa6', '#f4f6f8', '#4b515c')),
        'corgi': ('Corgi', ('#e48a3a', '#b8652a', '#f3ad69', '#fdf6ec', '#c96f2b')),
        'black': ('Schwarzer Labrador', ('#2b2724', '#1b1816', '#433c37', '#3a342f', '#1b1816')),
        'white': ('Weißer Hund', ('#f4f2ee', '#cfcac2', '#ffffff', '#ffffff', '#2b2724')),
    },
}
_FUR = {'cat': 'ODHL', 'dog': 'AahcM'}  # chars each breed palette replaces


def skin(species, breed):
    """Sprite-name prefix for a species/breed ('' = base cat)."""
    base = next(iter(BREEDS[species]))
    if breed == base or breed not in BREEDS[species]:
        return '' if species == 'cat' else species + ':'
    return '%s/%s:' % (species, breed)


FRAMES, EXTRA_PALETTE = {}, {}
_next = 0x100  # breed colors get private chars above Latin-1 so they never clash with base palette chars
for _sp, _breeds in BREEDS.items():
    _base = frames(_sp)
    FRAMES.update(_base)
    for _br, (_label, _cols) in _breeds.items():
        if not _cols:
            continue
        _chars = ''.join(chr(_next + i) for i in range(len(_cols)))
        EXTRA_PALETTE.update(zip(_chars, _cols))
        _next += len(_cols)
        _tr = str.maketrans(_FUR[_sp], _chars)
        for _k, _v in _base.items():
            FRAMES[skin(_sp, _br) + _k.split(':')[-1]] = [r.translate(_tr) for r in _v]
