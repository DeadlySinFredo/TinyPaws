"""Chat reaction engine without AI: regex rules, chance, per-rule and global cooldowns."""
import json
import re
import sys
import time
import random
from pathlib import Path

DEFAULT_PATH = Path(__file__).with_name('reactions.json')
MAX_MSG = 300


class ChatEngine:
    def __init__(self, rules, global_cooldown=4.0, rng=None, clock=time.monotonic):
        self.rules, self.gcd = [], global_cooldown
        self.rng, self.clock = rng or random.Random(), clock
        self.last, self.rule_last = -1e9, {}
        for r in rules:
            try:
                pats = [re.compile(p, re.IGNORECASE) for p in r['patterns']]
            except (re.error, KeyError, TypeError) as e:
                print('tinypaws: skip rule %r: %s' % (r.get('id'), e), file=sys.stderr)
                continue
            self.rules.append(dict(r, _pats=pats, cooldown=float(r.get('cooldown', 10)),
                                   chance=float(r.get('chance', 0.5)), prio=int(r.get('prio', 0))))
        self.rules.sort(key=lambda r: -r['prio'])

    @classmethod
    def from_file(cls, path=DEFAULT_PATH, **kw):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(data.get('rules', []), data.get('global_cooldown', 4.0), **kw)

    def match(self, text):
        text = text[:MAX_MSG]
        for r in self.rules:
            if any(p.search(text) for p in r['_pats']):
                return r
        return None

    def handle(self, user, text, now=None, force=False):
        """Return the matching rule if the pet should react now, else None."""
        rule = self.match(str(text))
        if not rule:
            return None
        if force:
            return rule
        now = self.clock() if now is None else now
        if not rule.get('bypass_global') and now - self.last < self.gcd:
            return None
        if now - self.rule_last.get(rule['id'], -1e9) < rule['cooldown']:
            return None
        if self.rng.random() > rule['chance']:
            return None
        self.last = self.rule_last[rule['id']] = now
        return rule
