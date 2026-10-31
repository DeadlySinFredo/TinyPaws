# PyInstaller spec: one-folder app for Linux/Windows/macOS. Build: pyinstaller packaging/tinypaws.spec
import sys

ROOT = SPECPATH + '/..'
# Qt modules TinyPaws never imports: keeps the bundle small
EXCLUDES = ['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtQml', 'PySide6.QtQuick',
            'PySide6.Qt3DCore', 'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtPdf', 'PySide6.QtSql',
            'PySide6.QtDesigner', 'PySide6.QtBluetooth', 'PySide6.QtPositioning', 'tkinter']

a = Analysis([ROOT + '/packaging/tinypaws_entry.py'], pathex=[ROOT],
             datas=[(ROOT + '/tinypaws/reactions.json', 'tinypaws'), (ROOT + '/assets/pets', 'assets/pets')],
             hiddenimports=['PySide6.QtDBus', 'PySide6.QtWebSockets', 'PySide6.QtNetwork'],
             excludes=EXCLUDES)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='TinyPaws', console=False,
          icon=ROOT + '/packaging/tinypaws.ico' if sys.platform == 'win32' else None)
coll = COLLECT(exe, a.binaries, a.datas, name='TinyPaws')
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='TinyPaws.app', bundle_identifier='org.tinypaws.TinyPaws',
                 info_plist={'LSUIElement': True, 'NSHighResolutionCapable': True})  # no Dock icon: lives in the tray
