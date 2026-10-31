"""Pet brain: priority state machine, actions and meme scenes. Pure Python, no Qt.

Coordinates are screen pixels. pet.x/pet.y = top-left of the 16x16 pet box,
s = pixel scale. render() returns a list of draw items consumed by the renderer:
  ('sprite', name, x, y, flip) ('rect', x, y, w, h, color[, alpha])
  ('text', str, cx, baseline_y, px, color) ('bubble', str, cx, bottom_y)
  ('rays', cx, cy, t, alpha, radius) ('spot', cx, top, bottom, w_top, w_bot, alpha)
"""
import math
import random

from .sprites import BREEDS, SIZES, skin

P_IDLE, P_RANDOM, P_CHAT, P_USER, P_SCENE = range(5)
GRAVITY = 140  # * s px/s^2
CONFETTI = ['#ff4d6d', '#ffd23f', '#3fbf5f', '#3a6fd9', '#c77dff', '#ff9f1c']
RAINBOW = ['#ff4d4d', '#ff9f1c', '#ffd23f', '#3fbf5f', '#3a8bd9', '#9d4dff']
LOCO_W, WAGON_W = 40, 26

POEMS = {
    'de': [
        ["Er schläft achtzehn Stunden.", "Er bereut nichts.", "Er ist GigaChat."],
        ["Andere jagen Mäuse.", "Mäuse jagen IHN.", "Um Autogramme."],
        ["Kein Kratzbaum zu hoch,", "kein Karton zu klein.", "So muss es sein."],
        ["Er wirft deine Tasse runter.", "Langsam. Mit Augenkontakt.", "Respekt."],
    ],
    'en': [
        ["He sleeps eighteen hours.", "He regrets nothing.", "He is GigaChat."],
        ["Others chase mice.", "Mice chase HIM.", "For autographs."],
        ["No tower too tall,", "no box too small.", "He fits them all."],
        ["He knocks your mug down.", "Slowly. Eye contact.", "Respect."],
    ],
}


class Action:
    prio = P_RANDOM

    def __init__(self, prio=None):
        self.t = 0.0
        if prio is not None:
            self.prio = prio

    def start(self, pet):
        pass

    def step(self, pet, dt):
        return True

    def update(self, pet, dt):
        self.t += dt
        return self.step(pet, dt)

    def draw(self, pet, out):
        pet.draw_self(out)


class Idle(Action):
    prio = P_IDLE

    def __init__(self, dur=2.0, frame='stand', prio=None):
        super().__init__(prio)
        self.dur, self.frame = dur, frame

    def step(self, pet, dt):
        pet.y = pet.floor
        blink = {'idle': 'blink', 'stand': 'stand_blink'}.get(self.frame)
        pet.frame = blink if blink and (self.t % 3.1) < 0.15 else self.frame
        return self.t >= self.dur


# gait style -> (frames, logical units/s, seconds per cycle); speed/cycle chosen so paws don't slide
GAITS = {'walk': (16, 12, 0.55), 'run': (12, 36, 0.42), 'sneak': (16, 6, 0.85)}
FLYERS = ('bird', 'dragon')  # their 'run' is flight: arc through the air


def gait_frame(style, t):
    n, _, cycle = GAITS[style]
    return '%s%d' % (style, int(t / cycle * n) % n)


class Walk(Action):
    def __init__(self, tx, speed=1.0, prio=None, style=None):
        super().__init__(prio)
        self.tx = tx
        self.style = style or ('run' if speed >= 2 else 'sneak' if speed < 0.75 else 'walk')

    def start(self, pet):
        self.x0 = pet.x

    def step(self, pet, dt):
        pet.y = pet.floor
        if self.style == 'run' and pet.species in FLYERS:
            p = 1 - abs(self.tx - pet.x) / max(1.0, abs(self.tx - self.x0))
            pet.y -= min(pet.H * 0.4, 30 * pet.s) * math.sin(math.pi * p)
        v = GAITS[self.style][1] * pet.s
        d = self.tx - pet.x
        if abs(d) <= v * dt:
            pet.x = self.tx
            return True
        pet.facing = 1 if d > 0 else -1
        pet.x += pet.facing * v * dt
        pet.frame = gait_frame(self.style, self.t)
        return False


class Sleep(Action):
    def __init__(self, dur=12.0, prio=None):
        super().__init__(prio)
        self.dur, self.zt = dur, 0.0

    @property
    def dozing(self):
        return self.t < self.dur

    def step(self, pet, dt):
        pet.y = pet.floor
        if self.dozing:
            pet.frame = 'sleep'
            self.zt += dt
            if self.zt > 1.2:
                self.zt = 0
                pet.emit(kind='text', text='z', x=pet.cx + 5 * pet.s * pet.facing, y=pet.y + 6 * pet.s,
                         vx=4 * pet.s * pet.facing, vy=-10 * pet.s, ttl=2.0, size=4 * pet.s, color='#ffffff')
            return False
        pet.frame = 'stretch'
        return self.t >= self.dur + 0.8


class Jump(Action):
    def start(self, pet):
        self.vy = -55 * pet.s
        self.vx = 20 * pet.s * pet.facing

    def step(self, pet, dt):
        self.vy += GRAVITY * pet.s * dt
        pet.y += self.vy * dt
        pet.x = pet.clampx(pet.x + self.vx * dt)
        pet.frame = 'jump'
        if pet.y >= pet.floor and self.vy > 0:
            pet.y = pet.floor
            pet.frame = 'sit'
            return True
        return False


class Held(Action):
    """User drags the pet; after release it falls back to the floor."""
    prio = P_USER

    def start(self, pet):
        self.vy = 0.0

    def step(self, pet, dt):
        if pet.held:
            pet.frame = 'surprised'
            self.vy = 0.0
            return False
        self.vy += GRAVITY * pet.s * dt
        pet.y = min(pet.floor, pet.y + self.vy * dt)
        pet.frame = 'jump'
        if pet.y >= pet.floor:
            pet.frame = 'sit'
            return True
        return False


class Emote(Action):
    """Generic reaction: frame loop, optional bubble, prop, confetti, head shake."""
    prio = P_CHAT

    def __init__(self, frames=('happy',), dur=2.5, fps=4, bubble=None, prop=None,
                 confetti=0, flip=False, bounce=False, drop=False, prio=None):
        super().__init__(prio)
        self.frames, self.dur, self.fps = list(frames), dur, fps
        self.bubble, self.prop, self.confetti = bubble, prop, confetti
        self.flip, self.bounce, self.drop = flip, bounce, drop

    def start(self, pet):
        if self.bubble:
            pet.say(self.bubble, min(self.dur, 3.5))
        if self.confetti:
            pet.confetti(self.confetti)

    def step(self, pet, dt):
        pet.y = pet.floor
        i = int(self.t * self.fps)
        pet.frame = self.frames[i % len(self.frames)]
        if self.flip:
            pet.facing = 1 if i % 2 == 0 else -1
        return self.t >= self.dur

    def draw(self, pet, out):
        pet.draw_self(out)
        if self.prop and self.prop in SIZES:
            s = pet.s
            w, h = SIZES[self.prop]
            px = pet.cx + pet.facing * 11 * s - w * s / 2
            py = pet.floor + 16 * s - h * s
            if self.bounce:
                py -= abs(math.sin(self.t * 6)) * 8 * s
            if self.drop:
                py -= max(0.0, 1 - self.t / 0.6) * 60 * s
            out.append(('sprite', self.prop, px, py, False))


class Teleport(Action):
    def __init__(self, tx=None, bubble=None, prio=None):
        super().__init__(prio)
        self.tx, self.bubble, self.moved = tx, bubble, False

    def start(self, pet):
        if self.tx is None:
            self.tx = pet.rng.uniform(0, pet.maxx)
        if self.bubble:
            pet.say(self.bubble, 1.2)

    def step(self, pet, dt):
        pet.y = pet.floor
        pet.frame = 'surprised'
        if self.t >= 0.6 and not self.moved:
            pet.x, self.moved = pet.clampx(self.tx), True
        return self.t >= 1.2

    def draw(self, pet, out):
        s, r = pet.s, pet.rng
        if int(self.t * 20) % 2:
            pet.draw_self(out)
        for _ in range(6):
            out.append(('rect', pet.x + r.uniform(-2, 16) * s, pet.y + r.uniform(0, 15) * s,
                        r.uniform(2, 8) * s, s, r.choice(['#00ffff', '#ff00ff', '#ffffff'])))


class HypeTrain(Action):
    """Notice -> run off-screen -> drive a steam train across -> fall back home."""
    prio = P_SCENE

    def __init__(self, level=1, names=(), honk='TUUT TUUT!'):
        super().__init__()
        self.level = max(1, min(int(level), 10))
        self.names = [str(n)[:20] for n in names][:self.level]
        self.honk, self.phase = honk, 'notice'

    def start(self, pet):
        self.home = pet.x
        self.smoke_t, self.front, self.vy = 0.0, 0.0, 0.0
        self.honked, self.celebrated, self.cel_t = False, False, 0.0
        self.rainbow = self.level >= 5 or pet.rng.random() < 0.05
        pet.say('!', 0.9)

    @property
    def length(self):
        return LOCO_W + self.level * WAGON_W

    def step(self, pet, dt):
        s = pet.s
        if self.phase == 'notice':
            pet.y, pet.frame = pet.floor, 'surprised'
            if self.t > 0.9:
                self.phase = 'runoff'
            return False
        if self.phase == 'runoff':
            pet.facing = 1
            pet.x += GAITS['run'][1] * 1.5 * s * dt
            pet.frame = gait_frame('run', self.t * 1.5)
            if pet.x > pet.W + 4 * s:
                self.phase, self.front = 'train', -LOCO_W * s
            return False
        if self.phase == 'train':
            self.front += 45 * s * dt
            top = pet.H - 27 * s
            pet.x, pet.y, pet.facing, pet.frame = self.front - 1.5 * s, top + 4 * s, 1, 'idle'
            self.smoke_t += dt
            if self.smoke_t > 0.07:
                self.smoke_t = 0
                col = pet.rng.choice(RAINBOW) if self.rainbow else pet.rng.choice(['#d8d8e0', '#b8b8c4', '#f0f0f4'])
                pet.emit(kind='rect', x=self.front + 29 * s, y=top, vx=-12 * s + pet.rng.uniform(-4, 4) * s,
                         vy=-28 * s, ttl=1.6, w=3 * s, h=3 * s, color=col, g=-4)
            center = self.front + LOCO_W * s / 2
            if not self.honked and center > pet.W * 0.25:
                self.honked = True
                pet.say(self.honk, 1.5)
            if not self.celebrated and center > pet.W * 0.5:
                self.celebrated, self.cel_t = True, self.t
                pet.confetti(80, x=pet.W / 2, y=pet.H * 0.5)
            if self.front - self.level * WAGON_W * s > pet.W:
                self.phase = 'return'
                pet.x, pet.y, pet.facing = self.home, -16 * s, -1
            return False
        # return: fall back from the sky to the old spot
        self.vy += GRAVITY * s * dt
        pet.y += self.vy * dt
        pet.frame = 'jump'
        if pet.y >= pet.floor:
            pet.y, pet.frame = pet.floor, 'sit'
            return True
        return False

    def draw(self, pet, out):
        if self.phase != 'train':
            pet.draw_self(out)
            return
        s = pet.s
        pet.draw_self(out)  # driver sits behind the cab window
        out.append(('sprite', 'loco', self.front, pet.H - 27 * s, False))
        for i in range(self.level):
            wx = self.front - (i + 1) * WAGON_W * s
            out.append(('sprite', 'wagon%d' % (i % 4), wx, pet.H - 19 * s, False))
            if i < len(self.names):
                out.append(('text', self.names[i], wx + WAGON_W * s / 2, pet.H - 10 * s, 3.4 * s, '#2b1d16'))
        if self.celebrated and self.t - self.cel_t < 3.0:
            out.append(('text', 'HYPE TRAIN LV %d!' % self.level, pet.W / 2, pet.H * 0.4, 10 * s, '#ffd23f'))


class GigaChad(Action):
    prio = P_SCENE

    def __init__(self, poem=True, lang='de'):
        super().__init__()
        self.poem, self.lang, self.line = poem, lang, -1

    def start(self, pet):
        self.lines = pet.rng.choice(POEMS.get(self.lang, POEMS['en'])) if self.poem else ['GIGACHAT.']

    @property
    def total(self):
        return 2.4 + 2.0 * len(self.lines) + 1.0

    def step(self, pet, dt):
        pet.y = pet.floor
        if self.t < 0.6:
            pet.frame = 'idle'
        elif self.t < 2.2:  # slow dramatic head turn
            pet.frame = 'idle'
            pet.facing = 1 if int((self.t - 0.6) / 0.4) % 2 == 0 else -1
        else:
            pet.facing, pet.frame = 1, 'flex'
            i = int((self.t - 2.4) / 2.0)
            if 0 <= i < len(self.lines) and i != self.line:
                self.line = i
                pet.say(self.lines[i], 2.0)
            if pet.rng.random() < 0.15:
                pet.emit(kind='rect', x=pet.cx + pet.rng.uniform(-14, 14) * pet.s, y=pet.y + pet.rng.uniform(0, 12) * pet.s,
                         vx=0, vy=-6 * pet.s, ttl=0.6, w=pet.s, h=pet.s, color='#fff6a8', g=0)
        return self.t >= self.total

    def draw(self, pet, out):
        if self.t >= 1.8:
            a = min(1.0, (self.t - 1.8) / 0.6)
            out.append(('rays', pet.cx, pet.y + 8 * pet.s, self.t, a, 42 * pet.s))
        pet.draw_self(out)


class Cinema(Action):
    """Armchair appears, pet sits, raises both paws: ABSOLUTE CINEMA."""
    prio = P_SCENE
    SIT = 5.5

    def __init__(self, title='ABSOLUTE CINEMA'):
        super().__init__()
        self.title, self.phase, self.t0 = title, 'appear', 0.0

    def start(self, pet):
        s = pet.s
        self.chair_x = max(0.0, min(pet.W - 24 * s, pet.x + pet.facing * 28 * s))
        self.target = self.chair_x + 4 * s
        pet.confetti(20, x=self.chair_x + 12 * s, y=pet.H - 9 * s, colors=['#ffffff', '#d8d8e0'])

    def _go(self, phase):
        self.phase, self.t0 = phase, self.t

    def step(self, pet, dt):
        s, dtp = pet.s, self.t - self.t0
        if self.phase == 'appear':
            pet.y, pet.frame = pet.floor, 'surprised'
            if dtp > 0.6:
                self._go('walk')
            return False
        if self.phase == 'walk':
            pet.y = pet.floor
            d = self.target - pet.x
            v = GAITS['walk'][1] * 2 * s * dt
            if abs(d) <= v:
                pet.x = self.target
                self._go('sit')
            else:
                pet.facing = 1 if d > 0 else -1
                pet.x += pet.facing * v
                pet.frame = gait_frame('walk', self.t * 2)
            return False
        if self.phase == 'sit':
            pet.y, pet.frame = pet.floor - 5 * s, ('sit' if dtp < 0.5 else 'cinema')
            if dtp > self.SIT:
                pet.confetti(20, x=self.chair_x + 12 * s, y=pet.H - 9 * s, colors=['#ffffff', '#d8d8e0'])
                self._go('vanish')
            return False
        pet.y, pet.frame = pet.floor, 'idle'
        return dtp > 0.6

    def draw(self, pet, out):
        s = pet.s
        cx, chair_y = self.chair_x + 12 * s, pet.H - 18 * s
        sitting = self.phase == 'sit' and self.t - self.t0 >= 0.5
        if sitting:
            out.append(('spot', cx, 0, pet.H, 6 * s, 20 * s, min(1.0, (self.t - self.t0 - 0.5) / 0.5)))
            for side in (-1, 1):  # film strips
                fx = cx + side * 24 * s - 3 * s
                out.append(('rect', fx, chair_y - 2 * s, 6 * s, 20 * s, '#1b1b1b'))
                for k in range(5):
                    out.append(('rect', fx + s, chair_y + k * 4 * s - s, s, 2 * s, '#ffffff'))
                    out.append(('rect', fx + 4 * s, chair_y + k * 4 * s - s, s, 2 * s, '#ffffff'))
        if self.phase != 'vanish':
            out.append(('sprite', 'chair', self.chair_x, chair_y, False))
        pet.draw_self(out)
        if self.phase == 'sit':
            out.append(('sprite', 'chair_front', self.chair_x, chair_y, False))
        if sitting:
            out.append(('sprite', 'popcorn', self.chair_x + 25 * s, pet.H - 9 * s, False))
            out.append(('text', self.title, cx, chair_y - 10 * s, 6 * s, '#ffffff'))


class Climb(Action):
    """Walk to a window's side, climb up the wall, nap on top with paws hanging over, jump down."""
    prio = P_RANDOM
    SPEED = 18  # logical units/s up the wall

    def __init__(self, ledge_id, nap=None, prio=None):
        super().__init__(prio)
        self.id, self.nap, self.phase, self.t0, self.vy = ledge_id, nap, 'approach', 0.0, 0.0

    def _ledge(self, pet):
        return next((l for l in pet.ledges if l[0] == self.id), None)

    def _go(self, phase):
        self.phase, self.t0 = phase, self.t

    def start(self, pet):
        s = pet.s
        l = self._ledge(pet)
        if l is None:
            self.phase = 'done'
            return
        _, x0, x1, top = l
        sides = [(x0 - 16 * s, 1), (x1, -1)]  # stand just outside the left / right wall, facing it
        sides = [sd for sd in sides if 0 <= sd[0] <= pet.maxx]
        if not sides:
            self.phase = 'done'
            return
        self.base_x, self.side = min(sides, key=lambda sd: abs(sd[0] - pet.x))
        self.top, self.lx = top, x0
        self.nap = self.nap if self.nap is not None else pet.rng.uniform(15, 35)
        self.spot = pet.rng.uniform(x0 + 2 * s, max(x0 + 2 * s, x1 - 18 * s))

    def step(self, pet, dt):
        s, lt = pet.s, self.t - self.t0
        if self.phase == 'done':
            return True
        l = self._ledge(pet)
        if self.phase in ('climb', 'hop', 'walk_top', 'lounge', 'wake'):
            if l is None:
                self._go('down')  # window closed / minimized / covered: fall off
            else:
                if self.phase != 'climb':  # ride along when the window is dragged
                    pet.x += l[1] - self.lx
                self.top, self.lx = l[3], l[1]
                if self.phase != 'climb' and not (l[1] - 8 * s <= pet.cx <= l[2] + 8 * s):
                    self._go('down')
        if self.phase == 'approach':
            pet.y = pet.floor
            d = self.base_x - pet.x
            v = GAITS['walk'][1] * s * dt
            if abs(d) <= v:
                pet.x, pet.facing = self.base_x, self.side
                self._go('climb')
            else:
                pet.facing = 1 if d > 0 else -1
                pet.x += pet.facing * v
                pet.frame = gait_frame('walk', self.t)
        elif self.phase == 'climb':
            pet.facing = self.side
            pet.y -= self.SPEED * s * dt
            pet.frame = gait_frame('walk', self.t * 1.3)
            if pet.y <= self.top - 8 * s:
                self.hop_from = pet.x
                self._go('hop')
        elif self.phase == 'hop':
            u = min(1.0, lt / 0.35)
            pet.frame = 'jump'
            pet.x = self.hop_from + self.side * 10 * s * u
            pet.y = self.top - 16 * s - math.sin(math.pi * u) * 4 * s
            if u >= 1:
                self._go('walk_top')
        elif self.phase == 'walk_top':
            pet.y = self.top - 16 * s
            d = self.spot - pet.x
            v = GAITS['walk'][1] * s * dt
            if abs(d) <= v:
                pet.facing = pet.rng.choice((1, -1))
                self._go('lounge')
            else:
                pet.facing = 1 if d > 0 else -1
                pet.x += pet.facing * v
                pet.frame = gait_frame('walk', self.t)
        elif self.phase == 'lounge':
            pet.y, pet.frame = self.top - 16 * s, 'lounge'
            if pet.rng.random() < dt * 0.8:
                pet.emit(kind='text', text='z', x=pet.cx + pet.facing * 5 * s, y=pet.y + 8 * s,
                         vx=4 * s * pet.facing, vy=-10 * s, ttl=2.0, size=4 * s, color='#ffffff', g=0)
            if lt >= self.nap:
                self._go('wake')
        elif self.phase == 'wake':
            pet.y, pet.frame = self.top - 16 * s, 'stretch'
            if lt >= 0.8:
                self._go('down')
        elif self.phase == 'down':
            self.vy += GRAVITY * s * dt
            pet.y = min(pet.floor, pet.y + self.vy * dt)
            pet.frame = 'jump'
            if pet.y >= pet.floor:
                pet.frame = 'sit'
                return True
        return False

    def draw(self, pet, out):
        if self.phase == 'climb':  # walk cycle turned upright: belly to the wall, head up
            pet.draw_self(out, angle=-90 if pet.facing > 0 else 90)
        else:
            pet.draw_self(out, top=self.phase == 'lounge')


def _tr(v, lang):
    """Bilingual text: (de, en) tuple or plain string."""
    return (v[0] if lang == 'de' else v[1]) if isinstance(v, tuple) else v


FIRE = [('flame', -8, None, 'flicker', 'back'), ('flame', 17, None, 'flicker'), ('flame', 22, None, 'flicker')]
CHAOS_FRAMES = ['jump', 'surprised', 'sleep', 'flex', 'cinema', 'sit', 'run3', 'sneak5', 'happy', 'stretch']
CHAOS_TALK = ['???', 'brrr', '404', 'LOL', '*glitch*', 'AAA', 'bruh', '...wtf']

# Meme timelines. Step keys: t (s), frames, fps, flip, bubble, confetti, fx (stars/steam/notes/hearts/glitch),
# props [(name, dx, dy, anim, layer, label)] in pet-box units (dy None = stands on the floor),
# hop, chaos, hidden, walk_off, home. Names starting with '@' are the pet's own frames (a second pet).
MEMES = {
    'thisisfine': [
        {'t': 0.6, 'frames': ['surprised'], 'props': FIRE},
        {'t': 4.0, 'frames': ['sit'], 'bubble': ('Alles gut.', 'This is fine.'),
         'props': FIRE + [('coffee', 12, None, None)]},
    ],
    'bonk': [
        {'t': 0.6, 'frames': ['stand'], 'props': [('hammer_up', 9, -12, None)]},
        {'t': 0.35, 'frames': ['surprised'], 'bubble': '*BONK*', 'props': [('hammer_down', 2, -8, None)]},
        {'t': 1.6, 'frames': ['sleep'], 'fx': 'stars'},
        {'t': 0.6, 'frames': ['stretch']},
    ],
    'cook': [
        {'t': 0.5, 'frames': ['surprised'], 'props': [('chefhat', 6, -5, 'drop')]},
        {'t': 4.0, 'frames': ['stand', 'stand_blink'], 'fps': 1.5, 'fx': 'steam', 'bubble': 'Let him cook!',
         'props': [('chefhat', 6, -5, None), ('stove', 14, None, None)]},
    ],
    'exit': [
        {'t': 1.8, 'frames': ['stand'], 'bubble': ('Ich bin raus.', "I'm out."), 'props': [('suitcase', 10, None, 'drop')]},
        {'walk_off': True, 'props': [('suitcase', 10, None, None)]},
        {'t': 2.0, 'hidden': True},
        {'home': True, 'bubble': ('...doch nicht.', '...never mind.')},
    ],
    'achievement': [
        {'t': 3.5, 'frames': ['happy', 'idle'], 'fps': 2, 'confetti': 50, 'text': 'ACHIEVEMENT UNLOCKED',
         'props': [('trophy', 14, None, 'drop')]},
    ],
    'rip': [
        {'t': 0.4, 'frames': ['surprised']},
        {'t': 3.0, 'frames': ['sleep'], 'props': [('tombstone', -11, None, 'rise', 'back', 'RIP')]},
        {'t': 1.2, 'frames': ['surprised', 'jump'], 'fps': 4, 'bubble': ('Nur Spaß!', 'Just kidding!')},
    ],
    'sus': [
        {'t': 3.5, 'frames': ['stand', 'stand_blink'], 'fps': 1.2, 'flip': True, 'bubble': 'sus...'},
    ],
    'cds': [
        {'t': 0.6, 'frames': ['surprised'], 'props': [('box', 14, None, 'drop')]},
        {'t': 3.5, 'frames': ['happy', 'idle'], 'fps': 2, 'fx': 'hearts',
         'bubble': ('Cat Distribution System hat geliefert!', 'The Cat Distribution System delivered!'),
         'props': [('box', 14, None, None), ('@idle', 16, -4, 'rise'), ('box_front', 14, None, None)]},
    ],
    'party': [
        {'t': 4.0, 'frames': ['happy', 'jump', 'walk1', 'jump'], 'fps': 6, 'flip': True, 'fx': 'notes',
         'bubble': ('Tanz-Party!', 'Dance party!')},
    ],
    'brainrot': [{'t': 4.0, 'chaos': True, 'fx': 'glitch'}],
    # ---- everyday life (also picked by the random life, see LIFE)
    'scratch': [
        {'t': 0.5, 'frames': ['surprised'], 'props': [('scratchpost', 13, None, 'drop', 'back')]},
        {'t': 3.0, 'frames': ['stretch', 'jump'], 'fps': 5, 'bubble': ('*kratz kratz*', '*scratch scratch*'),
         'props': [('scratchpost', 13, None, None, 'back')]},
    ],
    'pillow': [
        {'t': 0.5, 'frames': ['happy'], 'props': [('pillow', 0, None, 'drop', 'back')]},
        {'t': 6.0, 'frames': ['sleep'], 'lift': 3, 'fx': 'zz', 'props': [('pillow', 0, None, None, 'back')]},
        {'t': 0.8, 'frames': ['stretch'], 'props': [('pillow', 0, None, None, 'back')]},
    ],
    'bed': [
        {'t': 0.6, 'frames': ['happy'], 'props': [('bed', -4, None, 'drop', 'back')]},
        {'t': 7.0, 'frames': ['sleep'], 'lift': 4, 'fx': 'zz',
         'props': [('bed', -4, None, None, 'back'), ('bed_front', -4, None, None)]},
        {'t': 0.8, 'frames': ['stretch'], 'props': [('bed', -4, None, None, 'back')]},
    ],
    'tv': [
        {'t': 0.5, 'frames': ['surprised'], 'face': 1, 'props': [('tv0', 20, None, 'drop')]},
        {'t': 6.0, 'frames': ['sit'], 'face': 1, 'bubble': ('*guckt Cartoons*', '*watching cartoons*'),
         'props': [('tv', 20, None, 'flicker'), ('popcorn', 13, None, None)]},
    ],
    'boxsit': [
        {'t': 0.5, 'frames': ['surprised'], 'props': [('box', -2, None, 'drop', 'back')]},
        {'t': 5.0, 'frames': ['idle', 'blink'], 'fps': 0.7, 'lift': 3, 'bubble': ('Wenn ich passe, sitze ich.', 'If I fits, I sits.'),
         'props': [('box', -2, None, None, 'back'), ('box_front', -2, None, None)]},
        {'t': 0.4, 'frames': ['jump'], 'hop': True, 'props': [('box', -2, None, None, 'back')]},
    ],
    'yarn': [
        {'t': 3.5, 'frames': ['walk1', 'jump', 'walk5', 'sit'], 'fps': 4, 'props': [('yarn', 13, None, 'bounce')]},
    ],
    'mousechase': [
        {'t': 0.6, 'frames': ['surprised'], 'bubble': '!', 'props': [('mousetoy', 18, None, 'drop')]},
        {'walk_off': 'run', 'props': [('mousetoy', 19, None, 'bounce')]},
        {'t': 1.5, 'hidden': True},
        {'home': True},
    ],
    'bone': [
        {'t': 4.0, 'frames': ['sit', 'happy'], 'fps': 1.5, 'bubble': ('*knabber*', '*chomp*'),
         'props': [('bone', 12, None, 'drop')]},
    ],
    'visitor': [
        {'t': 4.5, 'frames': ['idle', 'happy'], 'fps': 1, 'fx': 'hearts', 'bubble': ('Besuch!', 'A visitor!'),
         'props': [('%visitor', 18, None, 'arrive')]},
    ],
    'scare': [
        {'t': 0.5, 'frames': ['stand'], 'props': [('ghost', -12, -1, 'rise', 'back')]},
        {'t': 0.7, 'frames': ['surprised'], 'hop': True, 'bubble': ('BUH!', 'BOO!'),
         'props': [('ghost', -10, -1, None, 'back')]},
        {'t': 1.5, 'frames': ['surprised', 'jump'], 'fps': 8, 'bubble': 'AAAH!'},
    ],
}


# random-life weights: (meme, weight, species allowed or None = all)
LIFE = [
    ('scratch', 0.35, ('cat',)), ('pillow', 0.3, None), ('bed', 0.2, None), ('tv', 0.2, None),
    ('boxsit', 0.3, ('cat', 'fox', 'rabbit')), ('yarn', 0.3, ('cat',)), ('mousechase', 0.2, ('cat', 'fox', 'dog')),
    ('bone', 0.35, ('dog',)), ('visitor', 0.08, None),
    ('thisisfine', 0.03, None), ('sus', 0.08, None), ('party', 0.05, None), ('brainrot', 0.02, None),
    ('cook', 0.04, None), ('cds', 0.03, None), ('scare', 0.03, None),
]


class Meme(Action):
    """Plays a MEMES timeline."""
    prio = P_CHAT

    def __init__(self, name, prio=None):
        super().__init__(prio)
        self.name, self.steps, self.i, self.t0 = name, MEMES[name], -1, 0.0

    def start(self, pet):
        self.home, self.vy, self.chaos_t = pet.x, 0.0, 0.0
        others = [sp for sp in BREEDS if sp != pet.species]
        sp = pet.rng.choice(others)
        self.visitor = skin(sp, pet.rng.choice(list(BREEDS[sp])))  # another animal drops by
        self._enter(pet, 0)

    def _enter(self, pet, i):
        self.i, self.t0 = i, self.t
        if i >= len(self.steps):
            return
        st = self.steps[i]
        if st.get('bubble'):
            pet.say(_tr(st['bubble'], pet.lang), min(st.get('t', 3.0), 3.0))
        if st.get('confetti'):
            pet.confetti(st['confetti'])
        if st.get('walk_off'):
            pet.facing = -1 if pet.x < pet.W / 2 else 1  # leave through the nearer edge
        if st.get('home'):
            pet.x, pet.y, self.vy, pet.facing = self.home, -16 * pet.s, 0.0, 1

    def step(self, pet, dt):
        st, lt, s = self.steps[self.i], self.t - self.t0, pet.s
        if st.get('walk_off'):
            style = 'run' if st['walk_off'] == 'run' else 'walk'
            pet.y = pet.floor
            pet.x += pet.facing * GAITS[style][1] * (1 if style == 'run' else 1.5) * s * dt
            pet.frame = gait_frame(style, lt * (1 if style == 'run' else 1.5))
            done = pet.x < -16 * s or pet.x > pet.W or lt > 15
        elif st.get('home'):
            self.vy += GRAVITY * s * dt
            pet.y = min(pet.floor, pet.y + self.vy * dt)
            pet.frame = 'jump' if pet.y < pet.floor else 'sit'
            done = pet.y >= pet.floor
        else:
            pet.y = pet.floor - (math.sin(math.pi * min(1.0, lt / st['t'])) * 12 * s if st.get('hop') else 0)
            pet.y -= st.get('lift', 0) * s
            done = lt >= st['t']
        if st.get('face'):
            pet.facing = st['face']
        if st.get('frames'):
            k = int(lt * st.get('fps', 4))
            pet.frame = st['frames'][k % len(st['frames'])]
            if st.get('flip'):
                pet.facing = 1 if k % 2 == 0 else -1
        if st.get('chaos'):
            self.chaos_t -= dt
            if self.chaos_t <= 0:
                self.chaos_t = 0.2
                pet.frame = pet.rng.choice(CHAOS_FRAMES)
                pet.facing = pet.rng.choice((1, -1))
                pet.x = pet.clampx(pet.x + pet.rng.uniform(-3, 3) * s)
                if pet.rng.random() < 0.3:
                    pet.say(pet.rng.choice(CHAOS_TALK), 0.6)
        self._fx(pet, st.get('fx'), dt)
        if done:
            self._enter(pet, self.i + 1)
        return self.i >= len(self.steps)

    def _fx(self, pet, fx, dt):
        s, r = pet.s, pet.rng
        if not fx or r.random() > dt * (0.8 if fx == 'zz' else 8):  # particles per second
            return
        if fx == 'stars':
            a = self.t * 6
            pet.emit(kind='text', text='*', x=pet.cx + math.cos(a) * 7 * s, y=pet.y + 9 * s + math.sin(a) * 2 * s,
                     ttl=0.5, size=4 * s, color='#ffd23f', g=0)
        elif fx == 'steam':
            pet.emit(x=pet.cx + pet.facing * 13 * s + r.uniform(-3, 3) * s, y=pet.floor + 6 * s, vy=-12 * s,
                     ttl=1.0, w=2 * s, h=2 * s, color='#e8e8f0', g=-2)
        elif fx == 'notes':
            pet.emit(kind='text', text=r.choice('♪♫'), x=pet.cx + r.uniform(-8, 8) * s, y=pet.y, vy=-14 * s,
                     ttl=1.5, size=5 * s, color=r.choice(CONFETTI), g=0)
        elif fx == 'zz':
            pet.emit(kind='text', text='z', x=pet.cx + pet.facing * 5 * s, y=pet.y + 6 * s, vx=4 * s * pet.facing,
                     vy=-10 * s, ttl=2.0, size=4 * s, color='#ffffff', g=0)
        elif fx == 'hearts':
            pet.emit(kind='text', text='♥', x=pet.cx + pet.facing * 12 * s + r.uniform(-6, 6) * s, y=pet.y,
                     vy=-10 * s, ttl=1.4, size=4 * s, color='#ff4d6d', g=0)

    def draw(self, pet, out):
        st = self.steps[min(self.i, len(self.steps) - 1)]
        lt, s = self.t - self.t0, pet.s
        props = st.get('props', [])
        for layer in ('back', 'front'):
            for p in props:
                if (p[4] if len(p) > 4 and p[4] else 'front') == layer:
                    self._prop(pet, out, p, lt)
            if layer == 'back' and not st.get('hidden'):
                pet.draw_self(out)
        if st.get('text'):
            out.append(('text', _tr(st['text'], pet.lang), pet.cx, pet.y - 8 * s, 4 * s, '#ffd23f'))
        if st.get('fx') == 'glitch':
            for _ in range(5):
                out.append(('rect', pet.x + pet.rng.uniform(-4, 16) * s, pet.y + pet.rng.uniform(0, 15) * s,
                            pet.rng.uniform(2, 10) * s, s, pet.rng.choice(['#00ffff', '#ff00ff', '#ffffff'])))

    def _prop(self, pet, out, p, lt):
        name, dx, dy, anim = p[:4]
        s = pet.s
        if anim == 'flicker':
            name += str(int(lt * 8 + dx) % 2)
        own = name[0] in '@%'
        if name.startswith('@'):
            name = pet.skin + name[1:]
        elif name == '%visitor':
            name = self.visitor + ('idle' if lt >= 1.5 else gait_frame('walk', lt))
        w, h = SIZES[name]
        x = pet.x + (dx if pet.facing > 0 else 16 - dx - w) * s
        y = pet.H - h * s if dy is None else pet.y + dy * s
        if anim == 'arrive':  # walk in from beyond the far side
            x += pet.facing * max(0.0, 1 - lt / 1.5) * pet.W * 0.3
        elif anim == 'bounce':
            y -= abs(math.sin(lt * 6)) * 6 * s
        elif anim == 'drop':
            y -= max(0.0, 1 - lt / 0.4) * 50 * s
        elif anim == 'rise':
            y += max(0.0, 1 - lt / 0.5) * (h if dy is None else 8) * s
        out.append(('sprite', name, x, y, own and pet.facing > 0))  # a second pet faces the first
        if len(p) > 5:
            out.append(('text', p[5], x + w * s / 2, y + h * s * 0.55, 3.5 * s, '#26262e'))


class Pet:
    def __init__(self, W, H, scale=4, rng=None, random_level=1.0, lang='de', name='Mochi', poems=True,
                 species='cat', breed=''):
        self.W, self.H, self.s = W, H, scale
        self.rng = rng or random.Random()
        self.random_level, self.lang, self.name, self.poems = random_level, lang, name, poems
        self.species = species if species in SPECIES else 'cat'
        self.skin = skin(self.species, breed)
        self.x, self.y = W / 2, self.floor
        self.facing, self.frame = 1, 'idle'
        self.action, self.queue, self.particles = None, [], []
        self.bubble, self.held, self.ledges = None, False, []

    floor = property(lambda self: self.H - 16 * self.s)
    maxx = property(lambda self: self.W - 16 * self.s)
    cx = property(lambda self: self.x + 8 * self.s)

    @property
    def sleeping(self):
        return isinstance(self.action, Sleep) and self.action.dozing

    def clampx(self, x):
        return max(0.0, min(self.maxx, x))

    def play(self, action, queue=True):
        """Start action if it outranks the current one; else queue chat/scene events."""
        cur = self.action
        if cur is None or action.prio > cur.prio or (action.prio == cur.prio and action.prio <= P_RANDOM):
            self.action = action
            action.start(self)
            return True
        if queue and action.prio >= P_CHAT and len(self.queue) < 5:
            self.queue.append(action)
        return False

    def update(self, dt):
        dt = min(dt, 0.1)
        if self.action is None:
            self.play(self.queue.pop(0) if self.queue else self.pick_random())
        if self.action.update(self, dt):
            self.action = None
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += p['g'] * self.s * dt
            p['ttl'] -= dt
        self.particles = [p for p in self.particles if p['ttl'] > 0]
        if self.bubble:
            self.bubble[1] -= dt
            if self.bubble[1] <= 0:
                self.bubble = None

    def pick_random(self):
        r, L, U = self.rng, self.random_level, P_RANDOM
        table = [
            (4.0, lambda: Walk(r.uniform(0, self.maxx))),
            (3.0, lambda: Idle(r.uniform(1.5, 4.0))),
            (1.2, lambda: Idle(r.uniform(2.0, 5.0), frame='sit')),
            (1.2, lambda: Idle(r.uniform(2.0, 5.0), frame='idle')),  # sit facing the viewer
            (0.7 * L, lambda: Sleep(r.uniform(8, 20))),
            (1.0 * L, lambda: Jump()),
            (0.5 * L, lambda: Walk(r.uniform(0, self.maxx), style='run')),
            (0.4 * L, lambda: Walk(r.uniform(0, self.maxx), style='sneak')),
            (0.4 * L, lambda: Emote(('walk1', 'jump'), 3.0, 4, prop='ball', bounce=True, prio=U)),
            (0.3 * L, lambda: Emote(('sit', 'happy'), 3.5, 1.5, prop='coffee', prio=U)),
            (0.1 * L, lambda: Teleport(prio=U)),
        ] + [(w * L, lambda n=n: Meme(n, prio=U)) for n, w, only in LIFE if not only or self.species in only]
        if self.ledges:
            table.append((0.9 * L, lambda: Climb(r.choice(self.ledges)[0])))
        pick = r.uniform(0, sum(w for w, _ in table))
        for w, make in table:
            pick -= w
            if pick <= 0:
                return make()
        return Idle()

    def say(self, text, dur=2.5):
        self.bubble = [str(text)[:80], dur]

    def emit(self, kind='rect', x=0, y=0, vx=0, vy=0, ttl=1.0, w=4, h=4, color='#ffffff',
             text='', size=12, g=60):
        if len(self.particles) < 400:
            self.particles.append(dict(kind=kind, x=x, y=y, vx=vx, vy=vy, ttl=ttl, w=w, h=h,
                                       color=color, text=text, size=size, g=g))

    def confetti(self, n=40, x=None, y=None, colors=CONFETTI):
        x = self.cx if x is None else x
        y = self.y if y is None else y
        for _ in range(n):
            a = self.rng.uniform(-math.pi, 0)
            v = self.rng.uniform(20, 70) * self.s
            self.emit(x=x, y=y, vx=math.cos(a) * v, vy=math.sin(a) * v, ttl=self.rng.uniform(1.0, 2.2),
                      w=self.s, h=self.s, color=self.rng.choice(colors))

    def draw_self(self, out, frame=None, angle=0, top=False):
        """top=True: align the sprite's top with the box (for frames taller than 16 that hang below)."""
        name = self.skin + (frame or self.frame)
        w, h = SIZES[name]
        y = self.y if top else self.y + (16 - h) * self.s
        out.append(('sprite', name, self.x + (16 - w) * self.s / 2, y, self.facing < 0, angle))

    def set_windows(self, windows, ox=0.0, oy=0.0):
        """Window rects (id, x, y, w, h; bottom-to-top, screen coords) -> ledges the pet can nap on."""
        s, out = self.s, []
        rects = [(i, x - ox, y - oy, w, h) for i, x, y, w, h in windows]
        for k, (wid, x, y, w, h) in enumerate(rects):
            x0, x1 = max(0.0, x), min(float(self.W), x + w)
            if x1 - x0 < 24 * s or not (16 * s <= y <= self.floor - 24 * s):
                continue  # too narrow, too high (maximized) or too low to bother
            cx = (x0 + x1) / 2
            if any(ax <= cx <= ax + aw and ay <= y - 2 <= ay + ah for _, ax, ay, aw, ah in rects[k + 1:]):
                continue  # top edge hidden under a window that is above it
            out.append((wid, x0, x1, y))
        self.ledges = out

    def render(self):
        out = []
        (self.action.draw(self, out) if self.action else self.draw_self(out))
        for p in self.particles:
            if p['kind'] == 'text':
                out.append(('text', p['text'], p['x'], p['y'], p['size'], p['color']))
            else:
                out.append(('rect', p['x'], p['y'], p['w'], p['h'], p['color']))
        if self.bubble:
            out.append(('bubble', self.bubble[0], self.cx, self.y - 2 * self.s))
        return out


def _fill(text, user, name):
    return text.replace('{user}', user).replace('{name}', name) if text else text


def make_action(spec, pet, user=''):
    """Build an action from a reaction spec dict (from reactions.json)."""
    t = spec.get('type', 'emote')
    bubble = _fill(spec.get('bubble'), user, pet.name)
    if t == 'hypetrain':
        return HypeTrain(spec.get('level', 1), spec.get('names', [user] if user else []))
    if t == 'gigachad':
        return GigaChad(poem=pet.poems, lang=pet.lang)
    if t == 'cinema':
        return Cinema()
    if t == 'meme' and spec.get('name') in MEMES:
        return Meme(spec['name'])
    if t == 'sleep':
        a = Sleep(spec.get('dur', 8), prio=P_CHAT)
    elif t == 'jump':
        a = Jump(prio=P_CHAT)
    elif t == 'run':
        a = Walk(pet.rng.uniform(0, pet.maxx), speed=3.0, prio=P_CHAT)
    elif t == 'teleport':
        return Teleport(bubble=bubble, prio=P_CHAT)
    elif t == 'dance':
        return Emote(('happy', 'jump', 'walk1', 'jump'), spec.get('dur', 3.0), 6, bubble=bubble,
                     confetti=spec.get('confetti', 0), flip=True, prio=P_CHAT)
    else:
        return Emote(spec.get('frames', ['happy']), spec.get('dur', 2.5), spec.get('fps', 4), bubble=bubble,
                     prop=spec.get('prop'), confetti=spec.get('confetti', 0), flip=spec.get('flip', False),
                     bounce=spec.get('bounce', False), drop=spec.get('drop', False), prio=P_CHAT)
    if bubble:
        pet.say(bubble, 2.5)
    return a


THANKS = {'de': 'Danke', 'en': 'Thanks'}
SPECIES = {'cat': 'Miau!', 'dog': 'Wuff!', 'fox': 'Ring-ding-ding!', 'rabbit': '*mümmel*',
           'dragon': 'Rawr!', 'bird': 'Piep piep!'}  # species -> its sound


def handle_event(pet, engine, ev, force=False):
    """Route a unified stream event to the pet. Returns the action played/queued or None."""
    kind, user = ev.get('type'), str(ev.get('user', ''))[:25]
    thx = THANKS.get(pet.lang, 'Thanks')
    if kind == 'chat':
        text = str(ev.get('text', ''))
        rule = engine.handle(user, text, force=force)
        if not rule:
            return None
        if user:
            pet.say('%s: %s' % (user, text[:50]), 2.5)
        a = make_action(rule['action'], pet, user)
    elif kind == 'hype_train':
        a = HypeTrain(ev.get('level', 1), ev.get('names', []))
    elif kind == 'hype_level':
        a = Emote(('happy', 'jump'), 2.5, 6, bubble='HYPE LEVEL %d!' % ev.get('level', 2), confetti=60)
    elif kind == 'hype_end':
        done = {'de': 'Hype Train geschafft! Level %d', 'en': 'Hype Train done! Level %d'}
        a = Emote(('happy', 'jump', 'walk1', 'jump'), 4.0, 6, bubble=done.get(pet.lang, done['en']) % ev.get('level', 1),
                  confetti=150, flip=True)
    elif kind == 'follow':
        a = Emote(('happy', 'jump'), 2.5, 4, bubble='%s %s!' % (thx, user), confetti=25)
    elif kind in ('sub', 'gift_sub', 'bits', 'donation', 'superchat', 'membership', 'gift'):
        a = Emote(('happy', 'jump', 'walk1', 'jump'), 3.5, 6, bubble='%s %s! <3' % (thx, user), confetti=70, flip=True)
    elif kind == 'raid':
        a = Emote(('surprised', 'jump'), 3.0, 4, bubble='RAID! %s' % user, confetti=100)
    else:
        return None
    pet.play(a)
    return a
