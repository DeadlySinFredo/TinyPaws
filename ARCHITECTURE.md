# Architektur

**Stack:** Python 3 + PySide6 (Qt 6). Begründung: auf dem Zielsystem bereits installiert, kein Build-Schritt,
Qt läuft auf Linux/Windows/macOS, transparente Fenster + Click-Through nativ, ~2 % CPU / ~136 MB RAM gemessen.
Die Logik ist Qt-frei und damit portierbar (z. B. Rust/Tauri oder Browser-Overlay für OBS).

| Modul | Aufgabe |
|---|---|
| `tinypaws/cat32.py` | Tier-Generator: Formen auf 32er-Raster, gerastert 1,5× fein (48×48, Dichte 3), automatische Schattierung + Kontur. Köpfe pro Tierart (`HEADS`), Gangzyklus (`GAITS`: Phase pro Bein, Schritt, Pfotenhub, Knie), Rassen (`BREEDS`) per Umfärben auf private Palettenzeichen; Sprite-Präfix über `skin(tier, rasse)`. |
| `tinypaws/props48.py` | Gegenstände mit demselben Generator (Box/Ellipse/Rad-Helfer, Schattierung je Farbe), gleiche logische Größen wie zuvor. |
| `tinypaws/sprites.py` | Palette, alle Sprites als Zeichen-Raster, `DENSITY` (Pixel pro logischer Einheit: Generator 3, HD-Sheets 6), `SIZES` in logischen Einheiten, `GAIT_FRAMES` je Skin. |
| `tinypaws/brain.py` | Animation Engine / State Machine: `Pet`, Aktionen (`Idle`, `Walk`, `Sleep`, `Jump`, `Held`, `Emote`, `Teleport`), Szenen (`HypeTrain`, `GigaChad`, `Cinema`), Partikel, Sprechblasen, gewichteter Zufall, Event-Routing (`handle_event`), `make_action` aus JSON-Specs. Erzeugt eine Liste von Zeichen-Befehlen. |
| `brain.MEMES` / `Meme` | Meme-Engine: jedes Meme ist eine Liste von Schritten (Dauer, Posen, Sprechblase DE/EN, Gegenstände mit Animation drop/rise/flicker, Effekte, Hüpfen, Weglaufen/Zurückkommen, Chaos). Neues Meme = neuer Eintrag. |
| `tinypaws/reactions.py` + `.json` | Chat Reaction Engine ohne KI: Regex, Chance, Regel-/globaler Cooldown, Längenlimit, kaputte Regeln werden übersprungen. |
| `tinypaws/settings.py` | Validierte JSON-Einstellungen (atomar geschrieben), Konfig-Ordner und Autostart je System (XDG / Windows-Registry / macOS-LaunchAgent). |
| `tinypaws/obs.py` | OBS-Browser-Quelle: `ThreadingHTTPServer` auf 127.0.0.1, Seite + `sprites.json` + SSE-Stream der Draw-Items. Ein Server für die ganze Laufzeit; `set_skin` tauscht den versionierten Sprite-Satz, die Seite lädt bei Versionswechsel nach und verbindet sich per Keepalive/Watchdog selbst neu. |
| `tinypaws/twitch.py` | Anonymer Twitch-IRC-Client (TLS, `justinfan`), Parser → einheitliche Events, Reconnect mit Backoff, Queue max. 200; Kanalname wird validiert (kein IRC-Injection). |
| `tinypaws/eventsub.py` | Twitch EventSub per QWebSocket, Login per OAuth Device Code (öffentliche Client-ID des Nutzers), Token nur via `secret-tool` (Secret Service), Refresh, Keepalive-Watchdog, Reconnect mit Backoff, `session_reconnect` nur zu Twitch-Hosts. `map_notification` übersetzt in TinyPaws-Events. Bei aktivem EventSub ignoriert die App Abo/Bits/Raid aus IRC (keine Doppelreaktion). |
| `tinypaws/kwin.py` | Lädt zur Laufzeit ein KWin-Skript, das alle 0,4 s die normalen Fenster (Stapelreihenfolge) per D-Bus an `org.tinypaws.TinyPaws` meldet; JSON wird validiert. `Pet.set_windows` macht daraus „Kanten“ (nicht zu schmal, nicht maximiert, nicht verdeckt); `Climb` nutzt sie. |
| `assets/pets/<tier>/<rasse>/` | HD-Sheets (Paketformat) der eingebauten Tiere; `packs.load_builtin_hd` lädt das aktive Tier und ersetzt die generierten Frames gleichen Namens. Fehlt/defekt → Generator-Frames bleiben. `sprites.GAIT_FRAMES` merkt sich je Skin die Zahl der Lauf-Bilder; `brain.gait_frame` nutzt sie bei gleicher Zykluszeit. |
| `tinypaws/packs.py` | Tierpakete: Export eines eingebauten Tiers als Vorlage, Import mit Validierung (Format, Größen, Zellen, Farben, nur exakte Dateinamen aus dem ZIP), Zerschneiden des Sheets in Frames mit Ersatzbildern, Registrierung unter `pack/<id>:`. Spezifikation: docs/PET_PACKS.md. |
| `tinypaws/app.py` | Qt-Frontend: Renderer, Overlay, Handle, Tray, Startfenster (`Home`), Testpanel, Einstellungen (`apply_settings` wirkt live), Einrichtungsassistent, Einzelinstanz (`QLocalServer`), DE/EN. |
| `packaging/`, `.github/workflows/build.yml` | PyInstaller-Spec, App-Icon, Arch-PKGBUILD; CI baut + testet Linux/Windows/macOS, Tag `v*` → Release. |

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
