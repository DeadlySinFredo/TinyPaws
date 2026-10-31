# Architektur

**Stack:** Python 3 + PySide6 (Qt 6). Begründung: auf dem Zielsystem bereits installiert, kein Build-Schritt,
Qt läuft auf Linux/Windows/macOS, transparente Fenster + Click-Through nativ, ~1 % CPU / ~100 MB RAM gemessen.
Die Logik ist Qt-frei und damit portierbar (z. B. Rust/Tauri oder Browser-Overlay für OBS).

| Modul | Aufgabe |
|---|---|
| `tinypaws/cat32.py` | Tier-Generator: Formen auf 32er-Raster, gerastert 1,5× fein (48×48, Dichte 3), automatische Schattierung + Kontur. Köpfe pro Tierart (`HEADS`), Gangzyklus (`GAITS`: Phase pro Bein, Schritt, Pfotenhub, Knie), Rassen (`BREEDS`) per Umfärben auf private Palettenzeichen; Sprite-Präfix über `skin(tier, rasse)`. |
| `tinypaws/props48.py` | Gegenstände mit demselben Generator (Box/Ellipse/Rad-Helfer, Schattierung je Farbe), gleiche logische Größen wie zuvor. |
| `tinypaws/sprites.py` | Palette, Props als Zeichen-Raster, `DENSITY` (Pixel pro logischer Einheit: Katze 2, Props 1) und `SIZES` in logischen Einheiten. |
| `tinypaws/brain.py` | Animation Engine / State Machine: `Pet`, Aktionen (`Idle`, `Walk`, `Sleep`, `Jump`, `Held`, `Emote`, `Teleport`), Szenen (`HypeTrain`, `GigaChad`, `Cinema`), Partikel, Sprechblasen, gewichteter Zufall, Event-Routing (`handle_event`), `make_action` aus JSON-Specs. Erzeugt eine Liste von Zeichen-Befehlen. |
| `brain.MEMES` / `Meme` | Meme-Engine: jedes Meme ist eine Liste von Schritten (Dauer, Posen, Sprechblase DE/EN, Gegenstände mit Animation drop/rise/flicker, Effekte, Hüpfen, Weglaufen/Zurückkommen, Chaos). Neues Meme = neuer Eintrag. |
| `tinypaws/reactions.py` + `.json` | Chat Reaction Engine ohne KI: Regex, Chance, Regel-/globaler Cooldown, Längenlimit, kaputte Regeln werden übersprungen. |
| `tinypaws/settings.py` | Validierte JSON-Einstellungen (atomar geschrieben), XDG-Autostart. |
| `tinypaws/obs.py` | OBS-Browser-Quelle: `ThreadingHTTPServer` auf 127.0.0.1, Seite + `sprites.json` + SSE-Stream der Draw-Items. |
| `tinypaws/twitch.py` | Anonymer Twitch-IRC-Client (TLS, `justinfan`), Parser → einheitliche Events, Reconnect mit Backoff, Queue max. 200; Kanalname wird validiert (kein IRC-Injection). |
| `tinypaws/app.py` | Qt-Frontend: Renderer, Overlay, Handle, Tray, Testpanel, Einrichtungsassistent, DE/EN. |

## Prioritäten
`P_IDLE < P_RANDOM < P_CHAT < P_USER < P_SCENE`. Höhere Priorität unterbricht; gleiche Priorität nur bei
Idle/Random. Chat/Szenen, die nicht sofort laufen können, kommen in eine Warteschlange (max. 5).
Ziehen ist während Szenen gesperrt.

## Fenster-Modell (Click-Through)
1. **Overlay**: bildschirmgroß, `WindowTransparentForInput` – zeichnet alles, nimmt nie Klicks.
2. **Handle**: 16×16·scale großes, fast unsichtbares Fenster, folgt der Katze – nur hier wirken Klicks.

## Wayland
KWin erlaubt Wayland-Clients weder Positionierung noch „immer oben". TinyPaws startet daher automatisch über
XWayland (`QT_QPA_PLATFORM=xcb`) mit `X11BypassWindowManagerHint` (kein Taskleisteneintrag) und hebt die
Fenster alle 2 s an. `TINYPAWS_NATIVE_WAYLAND=1` schaltet das ab (dann eingeschränkt).
Geplant: echtes `wlr-layer-shell` via `layer-shell-qt` (auf dem System vorhanden).

## Event-Format
`{"type": "chat"|"follow"|"sub"|"gift_sub"|"bits"|"donation"|"raid"|"hype_train"|..., "user": str, "text": str, "level": int, "names": [str]}`
Stream-Connectors liefern nur dieses Format an `brain.handle_event`. Chat-Text wird nie ausgeführt, nur per Regex gematcht.
