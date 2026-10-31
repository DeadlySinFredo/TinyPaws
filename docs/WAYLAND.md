# Wayland & TinyPaws (Machbarkeit Layer-Shell, Issue #3)

## Ist-Stand (Standard)
KWin erlaubt normalen Wayland-Fenstern weder freie Positionierung noch „immer oben“. TinyPaws startet daher
unter Wayland automatisch über **XWayland** (`QT_QPA_PLATFORM=xcb`): Overlay + Griff-Fenster mit
`X11BypassWindowManagerHint`, Anheben alle 2 s. Live geprüft auf KDE Plasma 6.8.

Einschränkungen von XWayland: Vollbild-Spiele/-Videos können das Tier überdecken; ein neu geöffnetes Fenster kann
bis zu 2 s darüber liegen; Bildschirmskalierung ≠ 100 % ungetestet.

## Geprüft: native Layer-Shell (`zwlr_layer_shell_v1` über `layer-shell-qt`)
Versuch am 2026-10-31 mit `scripts/layershell_probe.py` (KDE Plasma 6.8, layer-shell-qt 6.8.2, PySide6 6.12):

| Frage | Ergebnis |
|---|---|
| Python-Anbindung vorhanden? | Nein. Aber `LayerShellQt::Window::get(QWindow*)` ist exportiert; per `ctypes` aufrufbar, das Ergebnis per `shiboken6.wrapInstance` als `QObject` nutzbar. |
| Eigenschaften setzbar? | Ja: `layer` (Overlay), `anchors` (alle Kanten), `keyboardInteractivity` (keine), `exclusionZone`, `margins`, `screen`. |
| Liegt das Overlay über allem, korrekt positioniert? | Ja (Ebene *Overlay* liegt über normalen und Vollbild-Fenstern sowie dem Panel). |
| Nur das Overlay als Layer-Fläche? | **Nein.** `QT_WAYLAND_SHELL_INTEGRATION=layer-shell` gilt prozessweit: auch Startfenster/Einstellungen werden randlose Layer-Flächen über allem → unbedienbar. |
| Klickdurchlass per Eingabe-Maske | nicht abschließend geprüft |

## Fazit
Machbar, aber nur mit einem **separaten Overlay-Prozess** (Layer-Shell) neben dem normalen UI-Prozess (xdg-shell):
Zeichen-Befehle per lokalem Socket (ähnlich dem OBS-Stream), Eingaben (Ziehen, Doppelklick) zurück an den UI-Prozess,
Eingabe-Maske = Tier-Rechtecke statt eigener Griff-Fenster. Vorteile: echtes „über allem“ (auch Vollbild), kein
Anheben-Timer, keine XWayland-Abhängigkeit. Nur auf Compositors mit Layer-Shell (KDE, wlroots: Sway, Hyprland …),
**nicht GNOME** – dort bleibt XWayland nötig.

Bis dahin bleibt XWayland der Standard und getestete Weg. Umsetzung als eigenes Folge-Issue.
