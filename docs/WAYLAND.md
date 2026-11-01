# Wayland & TinyPaws (layer-shell feasibility)

🇬🇧 English · [🇩🇪 Deutsch (below)](#-wayland--tinypaws-machbarkeit-layer-shell-deutsch)

## Current state (default)
KWin lets normal Wayland windows neither position themselves freely nor stay on top. On Wayland TinyPaws therefore
starts automatically via **XWayland** (`QT_QPA_PLATFORM=xcb`): overlay + handle windows with
`X11BypassWindowManagerHint`, raised every 2 s. Checked live on KDE Plasma 6.8.

XWayland limits: full-screen games/videos can cover the pet; a newly opened window can cover it for up to 2 s;
display scaling ≠ 100 % untested.

## Checked: native layer shell (`zwlr_layer_shell_v1` via `layer-shell-qt`)
Experiment on 2026-10-31 with `scripts/layershell_probe.py` (KDE Plasma 6.8, layer-shell-qt 6.8.2, PySide6 6.12):

| Question | Result |
|---|---|
| Python bindings available? | No. But `LayerShellQt::Window::get(QWindow*)` is exported; callable via `ctypes`, the result usable as a `QObject` via `shiboken6.wrapInstance`. |
| Can the properties be set? | Yes: `layer` (overlay), `anchors` (all edges), `keyboardInteractivity` (none), `exclusionZone`, `margins`, `screen`. |
| Is the overlay above everything, correctly positioned? | Yes (the *overlay* layer is above normal and full-screen windows and the panel). |
| Only the overlay as a layer surface? | **No.** `QT_WAYLAND_SHELL_INTEGRATION=layer-shell` applies to the whole process: the start window/settings also become borderless layer surfaces above everything → unusable. |
| Click-through via input mask | not fully checked |

## Conclusion
Feasible, but only with a **separate overlay process** (layer shell) next to the normal UI process (xdg-shell):
draw commands over a local socket (like the OBS stream), input (drag, double-click) back to the UI process, input
mask = pet rectangles instead of separate handle windows. Benefits: truly on top of everything (even full screen), no
raise timer, no XWayland dependency. Only on compositors with layer shell (KDE, wlroots: Sway, Hyprland …),
**not GNOME** – XWayland stays necessary there.

Until then XWayland remains the default and tested path.

---

# 🇩🇪 Wayland & TinyPaws (Machbarkeit Layer-Shell, Deutsch)

### Ist-Stand (Standard)
KWin erlaubt normalen Wayland-Fenstern weder freie Positionierung noch „immer oben“. TinyPaws startet daher
unter Wayland automatisch über **XWayland** (`QT_QPA_PLATFORM=xcb`): Overlay + Griff-Fenster mit
`X11BypassWindowManagerHint`, Anheben alle 2 s. Live geprüft auf KDE Plasma 6.8.

Einschränkungen von XWayland: Vollbild-Spiele/-Videos können das Tier überdecken; ein neu geöffnetes Fenster kann
bis zu 2 s darüber liegen; Bildschirmskalierung ≠ 100 % ungetestet.

### Geprüft: native Layer-Shell (`zwlr_layer_shell_v1` über `layer-shell-qt`)
Versuch am 2026-10-31 mit `scripts/layershell_probe.py` (KDE Plasma 6.8, layer-shell-qt 6.8.2, PySide6 6.12):

| Frage | Ergebnis |
|---|---|
| Python-Anbindung vorhanden? | Nein. Aber `LayerShellQt::Window::get(QWindow*)` ist exportiert; per `ctypes` aufrufbar, das Ergebnis per `shiboken6.wrapInstance` als `QObject` nutzbar. |
| Eigenschaften setzbar? | Ja: `layer` (Overlay), `anchors` (alle Kanten), `keyboardInteractivity` (keine), `exclusionZone`, `margins`, `screen`. |
| Liegt das Overlay über allem, korrekt positioniert? | Ja (Ebene *Overlay* liegt über normalen und Vollbild-Fenstern sowie dem Panel). |
| Nur das Overlay als Layer-Fläche? | **Nein.** `QT_WAYLAND_SHELL_INTEGRATION=layer-shell` gilt prozessweit: auch Startfenster/Einstellungen werden randlose Layer-Flächen über allem → unbedienbar. |
| Klickdurchlass per Eingabe-Maske | nicht abschließend geprüft |

### Fazit
Machbar, aber nur mit einem **separaten Overlay-Prozess** (Layer-Shell) neben dem normalen UI-Prozess (xdg-shell):
Zeichen-Befehle per lokalem Socket (ähnlich dem OBS-Stream), Eingaben (Ziehen, Doppelklick) zurück an den UI-Prozess,
Eingabe-Maske = Tier-Rechtecke statt eigener Griff-Fenster. Vorteile: echtes „über allem“ (auch Vollbild), kein
Anheben-Timer, keine XWayland-Abhängigkeit. Nur auf Compositors mit Layer-Shell (KDE, wlroots: Sway, Hyprland …),
**nicht GNOME** – dort bleibt XWayland nötig.

Bis dahin bleibt XWayland der Standard und getestete Weg.
