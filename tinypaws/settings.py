"""Local JSON settings + XDG autostart. No network, no telemetry."""
import json
import os
import sys
from pathlib import Path

DEFAULTS = dict(name='Mochi', animal='cat', breed='', scale=6, fps=30, random_level=1.0, lang='de',
                autostart=False, screen=0, x=None, poems=True, interact=True, obs=False, obs_port=8737, twitch_channel='', first_run_done=False)


def config_dir():
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'tinypaws'


def load(path=None):
    path = Path(path or config_dir() / 'settings.json')
    cfg = dict(DEFAULTS)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    # validate: a broken file must never crash startup
    for k, lo, hi, typ in (('scale', 1, 12, int), ('fps', 5, 60, int), ('screen', 0, 16, int),
                           ('random_level', 0.0, 3.0, float), ('obs_port', 1024, 65535, int)):
        try:
            cfg[k] = max(lo, min(hi, typ(cfg[k])))
        except (TypeError, ValueError):
            cfg[k] = DEFAULTS[k]
    cfg['name'] = str(cfg['name'])[:24] or DEFAULTS['name']
    cfg['twitch_channel'] = str(cfg['twitch_channel']).strip().lstrip('#').lower()[:25]
    from .sprites import BREEDS  # lazy: keep settings importable without building sprites
    if cfg['animal'] not in BREEDS:
        cfg['animal'] = 'cat'
    if cfg['breed'] not in BREEDS[cfg['animal']]:
        cfg['breed'] = next(iter(BREEDS[cfg['animal']]))
    cfg['lang'] = cfg['lang'] if cfg['lang'] in ('de', 'en') else 'de'
    if cfg['x'] is not None and not isinstance(cfg['x'], (int, float)):
        cfg['x'] = None
    return cfg


def save(cfg, path=None):
    path = Path(path or config_dir() / 'settings.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps({k: cfg[k] for k in DEFAULTS}, indent=2), encoding='utf-8')
    tmp.replace(path)


def autostart_file():
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'autostart' / 'tinypaws.desktop'


def set_autostart(enabled):
    f = autostart_file()
    if not enabled:
        f.unlink(missing_ok=True)
        return
    root = Path(__file__).resolve().parent.parent
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('[Desktop Entry]\nType=Application\nName=TinyPaws\nComment=Pixel desktop pet\n'
                 'Exec=env PYTHONPATH="%s" "%s" -m tinypaws\nX-KDE-autostart-after=panel\n'
                 'X-GNOME-Autostart-enabled=true\n' % (root, sys.executable), encoding='utf-8')
