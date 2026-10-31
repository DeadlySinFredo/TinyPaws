"""Qt desktop front-end.

Layout: one full-screen, input-transparent overlay draws everything (pet, trains,
effects), plus a tiny invisible "handle" window that follows the pet and is the
only thing that receives mouse input. So clicks never get blocked except on the pet.
"""
import argparse
import math
import os
import sys
import time

from . import brain, settings
from .obs import ObsServer
from .reactions import ChatEngine
from .sprites import PALETTE, SPRITES

TR = {
    'de': dict(panel='Testpanel', settings='Einstellungen', interact='Interaktion (Ziehen)', quit='Beenden',
               walk='Laufen', run='Rennen', jump='Springen', sleep='Schlafen', sit='Sitzen', dance='Tanzen',
               teleport='Teleport', pizza='Pizza', coffee='Kaffee', ball='Ball', hype='Hype Train',
               giga='GigaChad', cinema='Absolute Cinema', follow='Follow', sub='Abo', raid='Raid',
               send='Chat senden', force='Cooldown/Zufall ignorieren', level='Level', name='Name',
               scale='Pixel-Größe', fps='FPS', random='Zufallsaktivität (%)', lang='Sprache',
               autostart='Beim Login starten', screen='Monitor', poems='GigaChad-Gedichte',
               welcome='Willkommen bei TinyPaws! Richte deine Katze ein.', animal='Tier',
               scenes='Meme-Szenen', events='Stream-Events (Simulation)', chat='Chat-Simulation',
               actions='Aktionen', obs='OBS-Browser-Quelle'),
    'en': dict(panel='Test panel', settings='Settings', interact='Interaction (drag)', quit='Quit',
               walk='Walk', run='Run', jump='Jump', sleep='Sleep', sit='Sit', dance='Dance',
               teleport='Teleport', pizza='Pizza', coffee='Coffee', ball='Ball', hype='Hype Train',
               giga='GigaChad', cinema='Absolute Cinema', follow='Follow', sub='Sub', raid='Raid',
               send='Send chat', force='Ignore cooldown/chance', level='Level', name='Name',
               scale='Pixel size', fps='FPS', random='Random activity (%)', lang='Language',
               autostart='Start on login', screen='Monitor', poems='GigaChad poems',
               welcome='Welcome to TinyPaws! Set up your cat.', animal='Animal',
               scenes='Meme scenes', events='Stream events (simulated)', chat='Chat simulation',
               actions='Actions', obs='OBS browser source'),
}
DEMO_NAMES = ['PixelFuchs92', 'NyanNina', 'Bernd_TTV', 'LokiLoaf', 'xXChonkXx', 'Mausi', 'TurboTom',
              'Keksi', 'ZugFan', 'Lenny']


def _platform_setup():
    # KWin/Wayland forbids clients to position windows or keep them above; XWayland allows both.
    if os.environ.get('WAYLAND_DISPLAY') and not os.environ.get('QT_QPA_PLATFORM') \
            and not os.environ.get('TINYPAWS_NATIVE_WAYLAND'):
        os.environ['QT_QPA_PLATFORM'] = 'xcb'


from PySide6.QtCore import QPointF, QRectF, Qt, QTimer  # noqa: E402
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetricsF, QGuiApplication, QIcon, QImage,  # noqa: E402
                           QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,  # noqa: E402
                               QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMenu,
                               QPushButton, QSpinBox, QSystemTrayIcon, QVBoxLayout, QWidget)


class Renderer:
    def __init__(self, scale):
        self.s, self.cache = scale, {}

    def pixmap(self, name, flip=False):
        pm = self.cache.get((name, flip))
        if pm is None:
            rows = SPRITES[name]
            img = QImage(len(rows[0]), len(rows), QImage.Format_ARGB32)
            img.fill(0)
            for y, row in enumerate(rows):
                for x, c in enumerate(row):
                    if c != '.':
                        img.setPixelColor(x, y, QColor(PALETTE[c]))
            img = img.scaled(img.width() * self.s, img.height() * self.s, Qt.IgnoreAspectRatio,
                             Qt.FastTransformation)
            pm = QPixmap.fromImage(img)
            if flip:
                pm = pm.transformed(QTransform().scale(-1, 1))
            self.cache[(name, flip)] = pm
        return pm

    def paint(self, p, items, width):
        for it in items:
            k = it[0]
            if k == 'sprite':
                p.drawPixmap(int(it[2]), int(it[3]), self.pixmap(it[1], it[4]))
            elif k == 'rect':
                p.fillRect(QRectF(int(it[1]), int(it[2]), int(it[3]), int(it[4])), QColor(it[5]))
            elif k == 'text':
                self.text(p, *it[1:])
            elif k == 'bubble':
                self.bubble(p, it[1], it[2], it[3], width)
            elif k == 'rays':
                self.rays(p, *it[1:])
            elif k == 'spot':
                self.spot(p, *it[1:])

    @staticmethod
    def _font(px):
        f = QFont('DejaVu Sans Mono')
        f.setStyleHint(QFont.Monospace)
        f.setBold(True)
        f.setPixelSize(max(8, int(px)))
        return f

    def text(self, p, s, cx, y, px, color):
        f = self._font(px)
        path = QPainterPath()
        path.addText(QPointF(cx - QFontMetricsF(f).horizontalAdvance(s) / 2, y), f, s)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.strokePath(path, QPen(QColor('#1b1b1b'), max(1.0, px / 7)))
        p.fillPath(path, QColor(color))
        p.setRenderHint(QPainter.Antialiasing, False)

    def bubble(self, p, s, cx, bottom, width):
        f = self._font(10 + self.s * 1.5)
        fm = QFontMetricsF(f)
        w, h = fm.horizontalAdvance(s) + 16, fm.height() + 10
        x = max(4.0, min(width - w - 4, cx - w / 2))
        y = max(4.0, bottom - h - 6)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QPen(QColor('#2b1d16'), 2))
        p.setBrush(QColor('#ffffff'))
        p.drawRoundedRect(QRectF(x, y, w, h), 6, 6)
        p.drawPolygon(QPolygonF([QPointF(cx - 5, y + h - 1), QPointF(cx + 5, y + h - 1), QPointF(cx, y + h + 6)]))
        p.setFont(f)
        p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, s)
        p.setRenderHint(QPainter.Antialiasing, False)

    def rays(self, p, cx, cy, t, alpha, radius):
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 215, 64, int(110 * alpha)))
        for i in range(12):
            a = t * 0.5 + i * math.pi / 6
            p.drawPolygon(QPolygonF([QPointF(cx, cy),
                                     QPointF(cx + radius * math.cos(a - 0.1), cy + radius * math.sin(a - 0.1)),
                                     QPointF(cx + radius * math.cos(a + 0.1), cy + radius * math.sin(a + 0.1))]))
        p.setRenderHint(QPainter.Antialiasing, False)

    def spot(self, p, cx, top, bottom, wt, wb, alpha):
        g = QLinearGradient(0, top, 0, bottom)
        g.setColorAt(0, QColor(255, 250, 220, int(20 * alpha)))
        g.setColorAt(1, QColor(255, 250, 220, int(110 * alpha)))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawPolygon(QPolygonF([QPointF(cx - wt, top), QPointF(cx + wt, top),
                                 QPointF(cx + wb, bottom), QPointF(cx - wb, bottom)]))


# BypassWindowManager: no taskbar entry, exact placement; stacking kept via periodic raise_() in tick
_TOP = (Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
        | Qt.X11BypassWindowManagerHint)


class Overlay(QWidget):
    def __init__(self, ctl):
        super().__init__(None, _TOP | Qt.WindowTransparentForInput)
        self.ctl, self.items = ctl, []
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle('TinyPaws')

    def paintEvent(self, _):
        p = QPainter(self)
        self.ctl.renderer.paint(p, self.items, self.width())


class Handle(QWidget):
    """Invisible window over the pet: drag, double-click, context menu."""

    def __init__(self, ctl):
        super().__init__(None, _TOP)
        self.ctl = ctl
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setCursor(Qt.OpenHandCursor)
        self.setWindowTitle('TinyPaws handle')

    def paintEvent(self, _):
        QPainter(self).fillRect(self.rect(), QColor(0, 0, 0, 1))  # alpha 1: still receives clicks

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.ctl.grab(e.globalPosition())
        elif e.button() == Qt.RightButton:
            self.ctl.menu.exec(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        self.ctl.drag(e.globalPosition())

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.ctl.release()

    def mouseDoubleClickEvent(self, _):
        self.ctl.do('poke')


class SettingsDialog(QDialog):
    def __init__(self, cfg, first_run=False):
        super().__init__()
        t = TR[cfg['lang']]
        self.cfg = cfg
        self.setWindowTitle('TinyPaws – ' + t['settings'])
        form = QFormLayout(self)
        if first_run:
            form.addRow(QLabel(t['welcome']))
        self.name = QLineEdit(cfg['name'])
        self.name.setMaxLength(24)
        self.animal = QComboBox()
        self.animal.addItem('Katze / Cat', 'cat')
        self.scale = QSpinBox(minimum=1, maximum=12, value=cfg['scale'])
        self.fps = QSpinBox(minimum=5, maximum=60, value=cfg['fps'])
        self.rand = QSpinBox(minimum=0, maximum=300, value=int(cfg['random_level'] * 100))
        self.lang = QComboBox()
        self.lang.addItem('Deutsch', 'de')
        self.lang.addItem('English', 'en')
        self.lang.setCurrentIndex(0 if cfg['lang'] == 'de' else 1)
        self.screen = QComboBox()
        for i, sc in enumerate(QGuiApplication.screens()):
            self.screen.addItem('%d: %s' % (i, sc.name()), i)
        self.screen.setCurrentIndex(min(cfg['screen'], self.screen.count() - 1))
        self.autostart = QCheckBox(checked=cfg['autostart'])
        self.poems = QCheckBox(checked=cfg['poems'])
        self.obs = QCheckBox('http://127.0.0.1:%d/' % cfg['obs_port'], checked=cfg['obs'])
        for k, w in (('name', self.name), ('animal', self.animal), ('scale', self.scale), ('fps', self.fps),
                     ('random', self.rand), ('lang', self.lang), ('screen', self.screen),
                     ('autostart', self.autostart), ('poems', self.poems), ('obs', self.obs)):
            form.addRow(t[k], w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def result_cfg(self):
        return dict(self.cfg, name=self.name.text().strip() or 'Mochi', animal=self.animal.currentData(),
                    scale=self.scale.value(), fps=self.fps.value(), random_level=self.rand.value() / 100,
                    lang=self.lang.currentData(), screen=self.screen.currentData(),
                    autostart=self.autostart.isChecked(), poems=self.poems.isChecked(), obs=self.obs.isChecked(),
                    first_run_done=True)


class Panel(QWidget):
    """Local test buttons: every animation, scene and stream event without any platform."""

    def __init__(self, ctl):
        super().__init__()
        t = ctl.t
        self.setWindowTitle('TinyPaws – ' + t('panel'))
        v = QVBoxLayout(self)
        for title, keys in ((t('actions'), ['walk', 'run', 'jump', 'sleep', 'sit', 'dance', 'teleport',
                                            'pizza', 'coffee', 'ball']),
                            (t('scenes'), ['giga', 'cinema']),
                            (t('events'), ['follow', 'sub', 'raid'])):
            box = QGroupBox(title)
            g = QGridLayout(box)
            for i, k in enumerate(keys):
                b = QPushButton(t(k))
                b.clicked.connect(lambda *_, k=k: ctl.do(k))
                g.addWidget(b, i // 4, i % 4)
            v.addWidget(box)
            if keys[0] == 'giga':
                row = QHBoxLayout()
                self.level = QSpinBox(minimum=1, maximum=10, value=3)
                b = QPushButton(t('hype'))
                b.clicked.connect(lambda *_: ctl.do('hype', level=self.level.value()))
                row.addWidget(QLabel(t('level')))
                row.addWidget(self.level)
                row.addWidget(b)
                g.addLayout(row, 1, 0, 1, 4)
        box = QGroupBox(t('chat'))
        g = QGridLayout(box)
        self.user = QLineEdit('PixelFuchs92')
        self.msg = QLineEdit('Wo ist meine Pizza?')
        self.force = QCheckBox(t('force'), checked=True)
        send = QPushButton(t('send'))
        send.clicked.connect(self.send)
        self.msg.returnPressed.connect(self.send)
        self.status = QLabel('')
        g.addWidget(self.user, 0, 0)
        g.addWidget(self.msg, 0, 1, 1, 2)
        g.addWidget(self.force, 1, 0, 1, 2)
        g.addWidget(send, 1, 2)
        g.addWidget(self.status, 2, 0, 1, 3)
        v.addWidget(box)
        self.ctl = ctl

    def send(self):
        a = brain.handle_event(self.ctl.pet, self.ctl.engine,
                               {'type': 'chat', 'user': self.user.text(), 'text': self.msg.text()},
                               force=self.force.isChecked())
        self.status.setText('-> %s' % (type(a).__name__ if a else '—'))


class TinyPaws:
    def __init__(self, app, cfg, show_panel=False):
        self.app, self.cfg = app, cfg
        screens = QGuiApplication.screens()
        scr = screens[cfg['screen']] if cfg['screen'] < len(screens) else QGuiApplication.primaryScreen()
        self.geo = scr.availableGeometry()  # stay above the panel/taskbar
        s = cfg['scale']
        self.pet = brain.Pet(self.geo.width(), self.geo.height(), scale=s, random_level=cfg['random_level'],
                             lang=cfg['lang'], name=cfg['name'], poems=cfg['poems'])
        if cfg['x'] is not None:
            self.pet.x = self.pet.clampx(cfg['x'])
        self.engine = ChatEngine.from_file()
        self.renderer = Renderer(s)
        self.overlay = Overlay(self)
        self.overlay.setGeometry(self.geo)
        self.overlay.show()
        self.handle = Handle(self)
        self.handle.resize(16 * s, 16 * s)
        if cfg['interact']:
            self.handle.show()
        self.drag_off, self.items, self.hpos, self.cursor_t, self.raise_t = None, None, None, 0.0, 0.0
        self.panel, self.obs = None, None
        if cfg['obs']:
            try:
                self.obs = ObsServer(cfg['obs_port'], cfg['fps'])
            except OSError as e:  # port taken: desktop pet still works
                print('tinypaws: OBS server off: %s' % e, file=sys.stderr)
        self._build_menu()
        self.last = time.monotonic()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000 // cfg['fps'])
        if show_panel:
            self.show_panel()

    def t(self, k):
        return TR[self.cfg['lang']].get(k, k)

    def _build_menu(self):
        m = QMenu()
        m.addAction(self.t('panel'), self.show_panel)
        for k in ('hype', 'giga', 'cinema', 'sleep', 'dance'):
            m.addAction(self.t(k), lambda k=k: self.do(k))
        self.interact_act = m.addAction(self.t('interact'))
        self.interact_act.setCheckable(True)
        self.interact_act.setChecked(self.cfg['interact'])
        self.interact_act.toggled.connect(self.set_interact)
        m.addAction(self.t('settings'), self.open_settings)
        m.addSeparator()
        m.addAction(self.t('quit'), self.quit)
        self.menu = m
        self.tray = QSystemTrayIcon(QIcon(self.renderer.pixmap('idle')))
        self.tray.setToolTip('TinyPaws – %s' % self.cfg['name'])
        self.tray.setContextMenu(m)
        self.tray.activated.connect(lambda r: self.show_panel() if r == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    # ---------------------------------------------------------------- loop
    def tick(self):
        now = time.monotonic()
        dt, self.last = now - self.last, now
        pet = self.pet
        self.cursor_t += dt
        if self.cursor_t > 0.4 and type(pet.action) is brain.Idle:
            self.cursor_t = 0
            c = QCursor.pos()
            dx = c.x() - (self.geo.x() + pet.cx)
            if abs(dx) < 300 and abs(c.y() - (self.geo.y() + pet.y)) < 300:
                pet.facing = 1 if dx > 0 else -1  # watch the mouse
        self.raise_t += dt
        if self.raise_t > 2.0:
            self.raise_t = 0
            self.overlay.raise_()
            self.handle.raise_()
        pet.update(dt)
        items = pet.render()
        if items != self.items:
            self.items = self.overlay.items = items
            self.overlay.update()
            if self.obs:
                self.obs.publish(self.geo.width(), self.geo.height(), self.cfg['scale'], items)
        hp = (self.geo.x() + int(pet.x), self.geo.y() + int(pet.y))
        if hp != self.hpos and self.drag_off is None:
            self.hpos = hp
            self.handle.move(*hp)
        want = 125 if pet.sleeping else 1000 // self.cfg['fps']  # power save while asleep
        if self.timer.interval() != want:
            self.timer.setInterval(want)

    # ---------------------------------------------------------------- input
    def grab(self, gp):
        if self.pet.play(brain.Held(), queue=False):
            self.pet.held = True
            self.drag_off = (gp.x() - self.handle.x(), gp.y() - self.handle.y())

    def drag(self, gp):
        if self.drag_off is None:
            return
        pet = self.pet
        pet.x = pet.clampx(gp.x() - self.drag_off[0] - self.geo.x())
        pet.y = max(0.0, min(pet.floor, gp.y() - self.drag_off[1] - self.geo.y()))
        self.handle.move(self.geo.x() + int(pet.x), self.geo.y() + int(pet.y))

    def release(self):
        self.pet.held, self.drag_off = False, None
        self.cfg['x'] = self.pet.x
        settings.save(self.cfg)

    def set_interact(self, on):
        self.cfg['interact'] = on
        self.handle.setVisible(on)
        settings.save(self.cfg)

    def do(self, k, level=3):
        p, B, U = self.pet, brain, brain.P_USER
        if k in ('follow', 'sub', 'raid'):
            B.handle_event(p, self.engine, {'type': k, 'user': p.rng.choice(DEMO_NAMES)})
            return
        make = {
            'poke': lambda: B.Emote(('happy', 'jump'), 1.5, 4, bubble='Miau!', prio=U),
            'walk': lambda: B.Walk(p.rng.uniform(0, p.maxx), prio=U),
            'run': lambda: B.Walk(p.rng.uniform(0, p.maxx), speed=3.0, prio=U),
            'jump': lambda: B.Jump(prio=U),
            'sleep': lambda: B.Sleep(10, prio=U),
            'sit': lambda: B.Idle(4, frame='sit', prio=U),
            'dance': lambda: B.make_action({'type': 'dance', 'confetti': 30}, p),
            'teleport': lambda: B.Teleport(prio=U),
            'pizza': lambda: B.Emote(('surprised', 'happy', 'sit'), 3.5, 1.2, prop='pizza', drop=True, prio=U),
            'coffee': lambda: B.Emote(('sit', 'happy'), 3.5, 1.5, prop='coffee', prio=U),
            'ball': lambda: B.Emote(('walk1', 'jump'), 3.0, 4, prop='ball', bounce=True, prio=U),
            'hype': lambda: B.HypeTrain(level, p.rng.sample(DEMO_NAMES, min(level, len(DEMO_NAMES)))),
            'giga': lambda: B.GigaChad(poem=p.poems, lang=p.lang),
            'cinema': lambda: B.Cinema(),
        }[k]
        p.play(make())

    # ---------------------------------------------------------------- windows
    def show_panel(self):
        if self.panel is None:
            self.panel = Panel(self)
        self.panel.show()
        self.panel.raise_()

    def open_settings(self):
        d = SettingsDialog(self.cfg)
        if d.exec():
            self.cfg = d.result_cfg()
            self.cfg['x'] = self.pet.x
            settings.save(self.cfg)
            settings.set_autostart(self.cfg['autostart'])
            # shortcut: restart to apply scale/screen/lang everywhere; fine for a settings change
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            os.environ['PYTHONPATH'] = root + os.pathsep + os.environ.get('PYTHONPATH', '')
            os.execv(sys.executable, [sys.executable, '-m', 'tinypaws'])

    def quit(self):
        self.cfg['x'] = self.pet.x
        settings.save(self.cfg)
        if self.obs:
            self.obs.close()
        self.app.quit()


def main(argv=None):
    ap = argparse.ArgumentParser(prog='tinypaws')
    ap.add_argument('--panel', action='store_true', help='open the test panel on start')
    ap.add_argument('--reset', action='store_true', help='forget settings and run setup again')
    args = ap.parse_args(argv)
    _platform_setup()
    app = QApplication(sys.argv[:1])
    app.setApplicationName('TinyPaws')
    app.setQuitOnLastWindowClosed(False)
    cfg = settings.load() if not args.reset else dict(settings.DEFAULTS)
    if not cfg['first_run_done']:
        d = SettingsDialog(cfg, first_run=True)
        if d.exec():
            cfg = d.result_cfg()
        cfg['first_run_done'] = True
        settings.save(cfg)
        settings.set_autostart(cfg['autostart'])
    _ctl = TinyPaws(app, cfg, show_panel=args.panel)  # noqa: F841 keep alive
    return app.exec()
