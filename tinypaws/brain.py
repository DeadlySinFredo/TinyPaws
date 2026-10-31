"""Pet brain: priority state machine, actions and meme scenes. Pure Python, no Qt.

Coordinates are screen pixels. pet.x/pet.y = top-left of the 16x16 pet box,
s = pixel scale. render() returns a list of draw items consumed by the renderer:
  ('sprite', name, x, y, flip) ('rect', x, y, w, h, color[, alpha])
  ('text', str, cx, baseline_y, px, color) ('bubble', str, cx, bottom_y)
  ('rays', cx, cy, t, alpha, radius) ('spot', cx, top, bottom, w_top, w_bot, alpha)
"""
import math
import random

from .sprites import SIZES

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

    def __init__(self, dur=2.0, frame='idle', prio=None):
        super().__init__(prio)
        self.dur, self.frame = dur, frame

    def step(self, pet, dt):
        pet.y = pet.floor
        blink = self.frame == 'idle' and (self.t % 3.1) < 0.15
        pet.frame = 'blink' if blink else self.frame
        return self.t >= self.dur


class Walk(Action):
    def __init__(self, tx, speed=1.0, prio=None):
        super().__init__(prio)
        self.tx, self.speed = tx, speed

    def step(self, pet, dt):
        pet.y = pet.floor
        v = 30 * self.speed * pet.s
        d = self.tx - pet.x
        if abs(d) <= v * dt:
            pet.x = self.tx
            return True
        pet.facing = 1 if d > 0 else -1
        pet.x += pet.facing * v * dt
        pet.frame = 'walk1' if int(self.t * 6 * self.speed) % 2 == 0 else 'walk2'
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
            pet.x += 120 * s * dt
            pet.frame = 'walk1' if int(self.t * 12) % 2 else 'walk2'
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
            v = 60 * s * dt
            if abs(d) <= v:
                pet.x = self.target
                self._go('sit')
            else:
                pet.facing = 1 if d > 0 else -1
                pet.x += pet.facing * v
                pet.frame = 'walk1' if int(self.t * 12) % 2 else 'walk2'
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


class Pet:
    def __init__(self, W, H, scale=4, rng=None, random_level=1.0, lang='de', name='Mochi', poems=True):
        self.W, self.H, self.s = W, H, scale
        self.rng = rng or random.Random()
        self.random_level, self.lang, self.name, self.poems = random_level, lang, name, poems
        self.x, self.y = W / 2, self.floor
        self.facing, self.frame = 1, 'idle'
        self.action, self.queue, self.particles = None, [], []
        self.bubble, self.held = None, False

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
            (0.7 * L, lambda: Sleep(r.uniform(8, 20))),
            (1.0 * L, lambda: Jump()),
            (0.5 * L, lambda: Walk(r.uniform(0, self.maxx), speed=3.0)),
            (0.4 * L, lambda: Emote(('walk1', 'jump'), 3.0, 4, prop='ball', bounce=True, prio=U)),
            (0.3 * L, lambda: Emote(('sit', 'happy'), 3.5, 1.5, prop='coffee', prio=U)),
            (0.1 * L, lambda: Teleport(prio=U)),
        ]
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

    def draw_self(self, out, frame=None):
        name = frame or self.frame
        w, h = SIZES[name]
        out.append(('sprite', name, self.x + (16 - w) * self.s / 2, self.y + (16 - h) * self.s, self.facing < 0))

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
