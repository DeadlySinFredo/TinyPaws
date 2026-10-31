"""Optional sounds (off by default). All sounds are synthesised here – no third-party audio files.

Each sound is rendered once to a small 16-bit mono WAV in the config dir and played with QSoundEffect.
The pet brain only reports events (pet.sfx); this module decides what is audible.
"""
import math
import random
import struct
import time
import wave

RATE = 22050


def _env(t, dur, attack=0.02, release=0.08):
    a = min(1.0, t / attack) if attack else 1.0
    r = min(1.0, max(0.0, (dur - t) / release)) if release else 1.0
    return a * r


def _tone(dur, freq, harm=(1.0,), vib=0.0, noise=0.0, attack=0.02, release=0.08, seed=1):
    """freq: Hz or f(t) -> Hz; harm: harmonic weights; noise: 0..1 mix."""
    rnd = random.Random(seed)
    out, ph = [], 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        f = freq(t) if callable(freq) else freq
        f *= 1 + vib * math.sin(2 * math.pi * 6 * t)
        ph += 2 * math.pi * f / RATE
        v = sum(w * math.sin(k * ph) for k, w in enumerate(harm, 1)) / sum(harm)
        v = (1 - noise) * v + noise * rnd.uniform(-1, 1)
        out.append(v * _env(t, dur, attack, release))
    return out


def _glide(points):
    """Piecewise-linear frequency curve [(t, hz), ...]."""
    def f(t):
        for (t0, f0), (t1, f1) in zip(points, points[1:]):
            if t <= t1:
                return f0 + (f1 - f0) * (t - t0) / max(1e-9, t1 - t0)
        return points[-1][1]
    return f


def _cat(t):
    return _glide([(0, 620), (0.14, 1050), (0.5, 560)])(t)


def _gap(s):
    return [0.0] * int(s * RATE)


def _mix(*parts):
    return [x for p in parts for x in p]


SOUNDS = {
    'voice_cat': lambda: _tone(0.5, _cat, (1, 0.35, 0.15), vib=0.02, attack=0.03, release=0.18),
    'voice_dog': lambda: _mix(_tone(0.13, _glide([(0, 480), (0.13, 260)]), (1, 0.6, 0.4, 0.2), noise=0.25, attack=0.005),
                              _gap(0.08),
                              _tone(0.13, _glide([(0, 500), (0.13, 270)]), (1, 0.6, 0.4, 0.2), noise=0.25, attack=0.005)),
    'voice_fox': lambda: _mix(*[_mix(_tone(0.09, _glide([(0, 900), (0.05, 1500), (0.09, 1100)]), (1, 0.3)), _gap(0.05))
                                for _ in range(3)]),
    'voice_rabbit': lambda: _mix(*[_mix(_tone(0.04, 300, (1,), noise=0.8, attack=0.002, release=0.03, seed=i), _gap(0.07))
                                   for i in range(4)]),
    'voice_dragon': lambda: [v * (0.6 + 0.4 * math.sin(2 * math.pi * 28 * i / RATE)) for i, v in
                             enumerate(_tone(0.6, _glide([(0, 140), (0.6, 95)]), (1, 0.8, 0.6, 0.5, 0.4), noise=0.2,
                                             attack=0.05, release=0.2))],
    'voice_bird': lambda: _mix(*[_mix(_tone(0.06, _glide([(0, 2600), (0.06, 3600)]), (1,), attack=0.005, release=0.02),
                                      _gap(0.04)) for _ in range(3)]),
    'horn': lambda: _mix(_tone(0.35, lambda t: 330, (1, 0.5, 0.33), attack=0.02, release=0.05),
                         [a + b for a, b in zip(_tone(0.45, 330, (1, 0.5, 0.33)), _tone(0.45, 415, (1, 0.5, 0.33)))]),
    'pop': lambda: _mix(_tone(0.025, 1, (1,), noise=1.0, attack=0.001, release=0.02), _tone(0.05, 1300, (1,), attack=0.002, release=0.04)),
    'bonk': lambda: _tone(0.16, _glide([(0, 760), (0.16, 280)]), (1, 0.2), noise=0.15, attack=0.002, release=0.1),
    'blip': lambda: _tone(0.12, _glide([(0, 1200), (0.12, 2400)]), (1,), attack=0.005, release=0.04),
}


def render(name, path):
    """Write SOUNDS[name] as a normalised 16-bit mono WAV; returns duration in seconds."""
    data = SOUNDS[name]()
    peak = max(1e-9, max(abs(v) for v in data))
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b''.join(struct.pack('<h', int(v / peak * 0.5 * 32767)) for v in data))  # -6 dB headroom
    return len(data) / RATE


class Player:
    """Plays named sounds with a volume (0-100) and a per-sound cooldown so floods stay polite."""
    COOLDOWN = 0.35

    def __init__(self, cache_dir, volume=30):
        from PySide6.QtCore import QUrl
        from PySide6.QtMultimedia import QSoundEffect
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.fx, self.last, self.volume = {}, {}, volume
        for name in SOUNDS:
            path = cache_dir / ('%s.wav' % name)
            if not path.exists():
                render(name, path)
            e = QSoundEffect()
            e.setSource(QUrl.fromLocalFile(str(path)))
            self.fx[name] = e
        self.set_volume(volume)

    def set_volume(self, volume):
        self.volume = max(0, min(100, int(volume)))
        for e in self.fx.values():
            e.setVolume(self.volume / 100)

    def play(self, name, now=None):
        now = time.monotonic() if now is None else now
        if name not in self.fx or self.volume == 0 or now - self.last.get(name, -1e9) < self.COOLDOWN:
            return False
        self.last[name] = now
        self.fx[name].play()
        return True
