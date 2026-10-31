"""Window ledges on KDE Plasma (Wayland/X11) via a runtime KWin script.

Wayland hides other apps' windows from clients, so a tiny KWin script reports
normal window geometries over D-Bus. It is loaded only while TinyPaws runs
(no persistent KWin config change) and unloaded on quit.
"""
import json
import sys

from PySide6.QtCore import ClassInfo, QObject, Slot
from PySide6.QtDBus import QDBusConnection, QDBusInterface

SERVICE = 'org.tinypaws.TinyPaws'
PLUGIN = 'tinypaws_windows'
SCRIPT = """
function send() {
    var out = [];
    var list = workspace.stackingOrder;
    for (var i = 0; i < list.length; i++) {
        var w = list[i];
        if (!w.normalWindow || w.minimized || w.fullScreen) continue;
        if (!(w.onAllDesktops || w.desktops.indexOf(workspace.currentDesktop) >= 0)) continue;
        if (String(w.resourceClass).toLowerCase().indexOf("tinypaws") >= 0) continue;
        var g = w.frameGeometry;
        out.push([String(w.internalId), g.x, g.y, g.width, g.height]);
    }
    callDBus("%s", "/", "%s", "windows", JSON.stringify(out));
}
var tinypawsTimer = new QTimer();
tinypawsTimer.interval = 400;
tinypawsTimer.timeout.connect(send);
tinypawsTimer.start();
send();
""" % (SERVICE, SERVICE)


@ClassInfo({'D-Bus Interface': SERVICE})
class _Receiver(QObject):
    def __init__(self, cb):
        super().__init__()
        self.cb = cb

    @Slot(str)
    def windows(self, data):
        self.cb(data)


def parse(data, limit=64):
    """Validate the script's JSON: [[id, x, y, w, h], ...] (bottom-to-top stacking)."""
    try:
        rows = json.loads(data)
    except ValueError:
        return []
    out = []
    for r in rows[:limit] if isinstance(rows, list) else []:
        if (isinstance(r, list) and len(r) == 5 and isinstance(r[0], str)
                and all(isinstance(v, (int, float)) for v in r[1:])):
            out.append((r[0][:64], float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    return out


class KWinWindows:
    def __init__(self, script_path):
        self.windows, self.ok = [], False
        bus = QDBusConnection.sessionBus()
        if not bus.isConnected() or not bus.registerService(SERVICE):
            print('tinypaws: window climbing off (D-Bus service unavailable)', file=sys.stderr)
            return
        self._rx = _Receiver(self._on)
        bus.registerObject('/', self._rx, QDBusConnection.ExportAllSlots)
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(SCRIPT, encoding='utf-8')
        ks = QDBusInterface('org.kde.KWin', '/Scripting', 'org.kde.kwin.Scripting', bus)
        if not ks.isValid():
            print('tinypaws: window climbing off (no KWin)', file=sys.stderr)
            return
        ks.call('unloadScript', PLUGIN)  # leftover from a crashed run
        args = ks.call('loadScript', str(script_path), PLUGIN).arguments()
        sid = args[0] if args else -1
        if not isinstance(sid, int) or sid < 0:
            print('tinypaws: window climbing off (KWin refused script)', file=sys.stderr)
            return
        QDBusInterface('org.kde.KWin', '/Scripting/Script%d' % sid, 'org.kde.kwin.Script', bus).call('run')
        self.ok = True

    def _on(self, data):
        self.windows = parse(data)

    def close(self):
        if self.ok:
            QDBusInterface('org.kde.KWin', '/Scripting', 'org.kde.kwin.Scripting',
                           QDBusConnection.sessionBus()).call('unloadScript', PLUGIN)
            self.ok = False
