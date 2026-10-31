"""Wayland layer-shell feasibility probe (issue #3). KDE/wlroots only, needs layer-shell-qt.

Shows a red square as a layer-shell overlay surface plus an ordinary label window, then takes a
screenshot to <dir>/shot.png. Finding: the shell integration is process-wide, so the label also
becomes a layer surface. Details: docs/WAYLAND.md. usage: python scripts/layershell_probe.py <dir>
"""
import ctypes, os, sys
os.environ['QT_QPA_PLATFORM'] = 'wayland'
os.environ['QT_WAYLAND_SHELL_INTEGRATION'] = 'layer-shell;xdg-shell'
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QRegion
from PySide6.QtWidgets import QApplication, QWidget, QLabel
import shiboken6
app = QApplication([])
lib = ctypes.CDLL('libLayerShellQtInterface.so.6')
get = lib._ZN12LayerShellQt6Window3getEP7QWindow
get.restype = ctypes.c_void_p; get.argtypes = [ctypes.c_void_p]

class Ov(QWidget):
    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(QRect(200, self.height()-200, 160, 160), QColor(255, 60, 60, 220))
ov = Ov(None, Qt.FramelessWindowHint)
ov.setAttribute(Qt.WA_TranslucentBackground)
ov.winId()  # create the QWindow
ptr = get(shiboken6.getCppPointer(ov.windowHandle())[0])
lw = shiboken6.wrapInstance(ptr, __import__('PySide6.QtCore', fromlist=['QObject']).QObject)
mo = lw.metaObject()
print('props:', [mo.property(i).name() for i in range(mo.propertyOffset(), mo.propertyCount())])
print('set layer', lw.setProperty('layer', 3))          # LayerOverlay
print('set anchors', lw.setProperty('anchors', 15))     # top|bottom|left|right
print('set kbd', lw.setProperty('keyboardInteractivity', 0))
print('set excl', lw.setProperty('exclusionZone', -1) if mo.indexOfProperty('exclusionZone') >= 0 else 'n/a')
scr = app.primaryScreen().geometry(); ov.resize(scr.width(), scr.height())
ov.setMask(QRegion(200, scr.height()-200, 160, 160))  # input only here
ov.show()
normal = QLabel('normales Fenster (xdg)'); normal.resize(400, 120); normal.show()
QTimer.singleShot(3000, lambda: (os.system('spectacle -b -n -f -o %s/shot.png' % sys.argv[1]), print('platform', app.platformName(), 'ov handle', type(ov.windowHandle()).__name__)))
QTimer.singleShot(4500, app.quit)
app.exec()
