# Architecture

🇬🇧 English · [🇩🇪 Deutsch (below)](#-architektur-deutsch)

**Stack:** Python 3 + PySide6 (Qt 6). Reasons: no build step, Qt runs on Linux/Windows/macOS, transparent
windows + click-through are native, measured ~2 % CPU / ~145 MB RAM. The pet logic is Qt-free and therefore portable
(e.g. to Rust/Tauri or a browser overlay for OBS).

| Module | Purpose |
|---|---|
| `tinypaws/cat32.py` | Pet generator: shapes on a 32 grid, rasterised 1.5× finer (48×48, density 3), automatic shading + outline. Heads per species (`HEADS`), gait cycle (`GAITS`: phase per leg, stride, paw lift, knee), breeds (`BREEDS`) by recolouring onto private palette chars; sprite prefix via `skin(species, breed)`. |
| `tinypaws/props48.py` | Props with the same generator (box/ellipse/wheel helpers, shading per colour). |
| `tinypaws/sprites.py` | Palette, all sprites as character grids, `DENSITY` (pixels per logical unit: generator 3, HD sheets 6), `SIZES` in logical units, `GAIT_FRAMES` per skin. |
| `tinypaws/brain.py` | Animation engine / state machine: `Pet`, actions (`Idle`, `Walk`, `Sleep`, `Jump`, `Held`, `Emote`, `Teleport`, `Climb`, `Roam`), scenes (`HypeTrain`, `GigaChad`, `Cinema`), particles, speech bubbles, weighted randomness, event routing (`handle_event`), `make_action` from JSON specs. Produces a list of draw commands. |
| `brain.MEMES` / `Meme` | Meme engine: each meme is a list of steps (duration, poses, DE/EN speech bubble, props with drop/rise/flicker animation, effects, hopping, walking off/coming back, chaos). New meme = new entry. |
| `tinypaws/reactions.py` + `.json` | Chat reaction engine without AI: regex, chance, per-rule/global cooldown, length limit, broken rules are skipped. |
| `tinypaws/settings.py` | Validated JSON settings (written atomically), config folder and autostart per OS (XDG / Windows registry / macOS LaunchAgent). |
| `tinypaws/obs.py` | OBS browser source: `ThreadingHTTPServer` on 127.0.0.1, page + `sprites.json` + SSE stream of the draw items. One server for the whole run; `set_skin` swaps the versioned sprite set, the page reloads on a version change and reconnects by itself (keepalive/watchdog). |
| `tinypaws/twitch.py` | Anonymous Twitch IRC client (TLS, `justinfan`), parser → unified events, reconnect with back-off, queue max. 200; channel names are validated (no IRC injection). |
| `tinypaws/eventsub.py` | Twitch EventSub via QWebSocket, login via OAuth device code (the user's public client ID), token only in the system keyring (`secretstore.py`), refresh, keepalive watchdog, reconnect with back-off, `session_reconnect` only to Twitch hosts. `map_notification` translates into TinyPaws events. With EventSub active the app ignores subs/bits/raids from IRC (no double reactions). |
| `tinypaws/secretstore.py` | Small secrets (Twitch token) in the OS keyring: Linux Secret Service (`secret-tool`), macOS Keychain (`security`), Windows Credential Manager (advapi32 via `ctypes`); without a backend memory only. |
| `tinypaws/sound.py` | Optional sounds, all synthesised (WAV via the standard library), `QSoundEffect` with volume and cooldown; the brain only reports events (`pet.sfx`). |
| `tinypaws/screens.py` | Monitor topology: neighbouring monitors (touching edges, vertical overlap), also with negative coordinates. The app binds overlay/handles to the target monitor via `setScreen()`, renders sprites at device resolution and reacts to hotplug/resolution changes. |
| `tinypaws/kwin.py` | Loads a KWin script at runtime that reports the normal windows (stacking order) every 0.4 s over D-Bus to `org.tinypaws.TinyPaws`; the JSON is validated. `Pet.set_windows` turns them into ledges (not too narrow, not maximised, not covered); `Climb` uses them. |
| `assets/pets/<species>/<breed>/` | HD sheets (pack format) of the built-in pets; `packs.load_builtin_hd` loads the active pet and replaces the generated frames of the same name. Missing/broken → generator frames stay. `sprites.GAIT_FRAMES` remembers the number of gait frames per skin; `brain.gait_frame` uses it with the same cycle time. |
| `tinypaws/packs.py` | Pet packs: export a built-in pet as template, import with validation (format, sizes, cells, colours, only exact file names from the ZIP), cut the sheet into frames with fallbacks, register under `pack/<id>:`. Spec: docs/PET_PACKS.md. |
| `tinypaws/app.py` | Qt front end: renderer, overlay, handle, tray, start window (`Home`), test panel, settings (`apply_settings` applies live), setup wizard, single instance (`QLocalServer`), companion pets (up to 3, `Follow`/`NapTogether`/`PlayTogether` in the brain), DE/EN. |
| `packaging/`, `.github/workflows/build.yml` | PyInstaller spec, app icon, Arch PKGBUILD; CI builds + tests Linux/Windows/macOS, tag `v*` → release. |

## Priorities
`P_IDLE < P_RANDOM < P_CHAT < P_USER < P_SCENE`. Higher priority interrupts; equal priority only for idle/random.
Chat/scenes that cannot run right away are queued (max. 5). Dragging is locked during scenes.

## Window model (click-through)
1. **Overlay**: screen-sized, `WindowTransparentForInput` – draws everything, never takes clicks.
2. **Handle**: a nearly invisible 16×16·scale window that follows the pet – only here clicks have an effect.

## Wayland
KWin lets Wayland clients neither position themselves nor stay on top. TinyPaws therefore starts automatically via
XWayland (`QT_QPA_PLATFORM=xcb`) with `X11BypassWindowManagerHint` (no taskbar entry) and raises its windows every 2 s.
`TINYPAWS_NATIVE_WAYLAND=1` turns this off (then limited). Native `wlr-layer-shell` via `layer-shell-qt`: feasibility
checked (docs/WAYLAND.md), needs a separate overlay process.

## Event format
`{"type": "chat"|"follow"|"sub"|"gift_sub"|"bits"|"donation"|"raid"|"hype_train"|..., "user": str, "text": str, "level": int, "names": [str]}`
Stream connectors only hand this format to `brain.handle_event`. Chat text is never executed, only matched by regex.

---

# 🇩🇪 Architektur (Deutsch)

**Stack:** Python 3 + PySide6 (Qt 6). Begründung: auf dem Zielsystem bereits installiert, kein Build-Schritt,
Qt läuft auf Linux/Windows/macOS, transparente Fenster + Click-Through nativ, ~2 % CPU / ~145 MB RAM gemessen.
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
| `tinypaws/eventsub.py` | Twitch EventSub per QWebSocket, Login per OAuth Device Code (öffentliche Client-ID des Nutzers), Token nur im System-Schlüsselbund (`secretstore.py`), Refresh, Keepalive-Watchdog, Reconnect mit Backoff, `session_reconnect` nur zu Twitch-Hosts. `map_notification` übersetzt in TinyPaws-Events. Bei aktivem EventSub ignoriert die App Abo/Bits/Raid aus IRC (keine Doppelreaktion). |
| `tinypaws/secretstore.py` | Kleine Geheimnisse (Twitch-Token) im System-Schlüsselbund: Linux Secret Service (`secret-tool`), macOS Schlüsselbund (`security`), Windows Anmeldeinformationsverwaltung (advapi32 per `ctypes`); ohne Backend nur im Speicher. |
| `tinypaws/sound.py` | Optionale Töne, alle selbst synthetisiert (WAV per Standardbibliothek), `QSoundEffect` mit Lautstärke und Abklingzeit; das Brain meldet nur Ereignisse (`pet.sfx`). |
| `tinypaws/screens.py` | Monitor-Topologie: Nachbarmonitore (Kanten berühren sich, vertikale Überlappung), auch bei negativen Koordinaten. Die App ordnet Overlay/Griffe per `setScreen()` dem Zielmonitor zu, rendert Sprites in Geräteauflösung und reagiert auf Hotplug/Auflösungswechsel. |
| `tinypaws/kwin.py` | Lädt zur Laufzeit ein KWin-Skript, das alle 0,4 s die normalen Fenster (Stapelreihenfolge) per D-Bus an `org.tinypaws.TinyPaws` meldet; JSON wird validiert. `Pet.set_windows` macht daraus „Kanten“ (nicht zu schmal, nicht maximiert, nicht verdeckt); `Climb` nutzt sie. |
| `assets/pets/<tier>/<rasse>/` | HD-Sheets (Paketformat) der eingebauten Tiere; `packs.load_builtin_hd` lädt das aktive Tier und ersetzt die generierten Frames gleichen Namens. Fehlt/defekt → Generator-Frames bleiben. `sprites.GAIT_FRAMES` merkt sich je Skin die Zahl der Lauf-Bilder; `brain.gait_frame` nutzt sie bei gleicher Zykluszeit. |
| `tinypaws/packs.py` | Tierpakete: Export eines eingebauten Tiers als Vorlage, Import mit Validierung (Format, Größen, Zellen, Farben, nur exakte Dateinamen aus dem ZIP), Zerschneiden des Sheets in Frames mit Ersatzbildern, Registrierung unter `pack/<id>:`. Spezifikation: docs/PET_PACKS.md. |
| `tinypaws/app.py` | Qt-Frontend: Renderer, Overlay, Handle, Tray, Startfenster (`Home`), Testpanel, Einstellungen (`apply_settings` wirkt live), Einrichtungsassistent, Einzelinstanz (`QLocalServer`), Begleiter-Tiere (bis 3, `Follow`/`NapTogether`/`PlayTogether` im Brain), DE/EN. |
| `packaging/`, `.github/workflows/build.yml` | PyInstaller-Spec, App-Icon, Arch-PKGBUILD; CI baut + testet Linux/Windows/macOS, Tag `v*` → Release. |

### Prioritäten
`P_IDLE < P_RANDOM < P_CHAT < P_USER < P_SCENE`. Höhere Priorität unterbricht; gleiche Priorität nur bei
Idle/Random. Chat/Szenen, die nicht sofort laufen können, kommen in eine Warteschlange (max. 5).
Ziehen ist während Szenen gesperrt.

### Fenster-Modell (Click-Through)
1. **Overlay**: bildschirmgroß, `WindowTransparentForInput` – zeichnet alles, nimmt nie Klicks.
2. **Handle**: 16×16·scale großes, fast unsichtbares Fenster, folgt der Katze – nur hier wirken Klicks.

### Wayland
KWin erlaubt Wayland-Clients weder Positionierung noch „immer oben". TinyPaws startet daher automatisch über
XWayland (`QT_QPA_PLATFORM=xcb`) mit `X11BypassWindowManagerHint` (kein Taskleisteneintrag) und hebt die
Fenster alle 2 s an. `TINYPAWS_NATIVE_WAYLAND=1` schaltet das ab (dann eingeschränkt).
Natives `wlr-layer-shell` via `layer-shell-qt`: Machbarkeit geprüft (docs/WAYLAND.md), braucht einen eigenen Overlay-Prozess.

### Event-Format
`{"type": "chat"|"follow"|"sub"|"gift_sub"|"bits"|"donation"|"raid"|"hype_train"|..., "user": str, "text": str, "level": int, "names": [str]}`
Stream-Connectors liefern nur dieses Format an `brain.handle_event`. Chat-Text wird nie ausgeführt, nur per Regex gematcht.
