"""Local JSON settings + XDG autostart. No network, no telemetry."""
import json
import os
import re
import sys
from pathlib import Path

DEFAULTS = dict(name='Mochi', animal='cat', breed='', pack='', scale=6, fps=30, random_level=1.0, lang='de',
                autostart=False, screen=0, x=None, poems=True, interact=True, obs=False, obs_port=8737, twitch_channel='', twitch_client_id='', climb=True, first_run_done=False)


def config_dir():
    if os.environ.get('XDG_CONFIG_HOME'):
        return Path(os.environ['XDG_CONFIG_HOME']) / 'tinypaws'
    if sys.platform == 'win32':
        return Path(os.environ.get('APPDATA') or Path.home()) / 'TinyPaws'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'TinyPaws'
    return Path.home() / '.config' / 'tinypaws'


def launch_cmd():
    """argv that starts TinyPaws again: the bundled executable, or python -m tinypaws from source."""
    if getattr(sys, 'frozen', False):  # PyInstaller build
        return [sys.executable]
    return [sys.executable, '-m', 'tinypaws']


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
    cfg['pack'] = cfg['pack'] if isinstance(cfg['pack'], str) and re.match(r'^[a-z0-9-]{0,32}$', cfg['pack']) else ''
    cfg['twitch_client_id'] = str(cfg['twitch_client_id']).strip().lower()
    if not re.match(r'^[a-z0-9]{20,40}$', cfg['twitch_client_id']):
        cfg['twitch_client_id'] = ''
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
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'LaunchAgents' / 'org.tinypaws.TinyPaws.plist'
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'autostart' / 'tinypaws.desktop'


def set_autostart(enabled):
    """Start on login: XDG autostart (Linux), HKCU Run key (Windows), LaunchAgent (macOS)."""
    cmd = launch_cmd() + ['--autostart']  # stays in the tray, no start window
    root = str(Path(__file__).resolve().parent.parent)  # source checkout needs it on PYTHONPATH
    if sys.platform == 'win32':
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0,
                            winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, 'TinyPaws', 0, winreg.REG_SZ, ' '.join('"%s"' % c for c in cmd))
            else:
                try:
                    winreg.DeleteValue(k, 'TinyPaws')
                except FileNotFoundError:
                    pass
        return
    f = autostart_file()
    if not enabled:
        f.unlink(missing_ok=True)
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'darwin':
        args = ''.join('<string>%s</string>' % c for c in cmd)
        f.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<plist version="1.0"><dict>'
                     '<key>Label</key><string>org.tinypaws.TinyPaws</string>'
                     '<key>ProgramArguments</key><array>%s</array>'
                     '<key>EnvironmentVariables</key><dict><key>PYTHONPATH</key><string>%s</string></dict>'
                     '<key>RunAtLoad</key><true/></dict></plist>\n' % (args, root), encoding='utf-8')
        return
    f.write_text('[Desktop Entry]\nType=Application\nName=TinyPaws\nComment=Pixel desktop pet\n'
                 'Exec=env PYTHONPATH="%s" %s\nX-KDE-autostart-after=panel\n'
                 'X-GNOME-Autostart-enabled=true\n' % (root, ' '.join('"%s"' % c for c in cmd)), encoding='utf-8')
