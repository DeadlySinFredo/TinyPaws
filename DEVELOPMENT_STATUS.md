# Development status (v0.4.0, as of 2026-11-01)

🇬🇧 English · [🇩🇪 Deutsch (below)](#-entwicklungsstand-v040-stand-2026-11-01)

Legend: **live** = checked on a real desktop (CachyOS/KDE Plasma 6, Wayland, app via XWayland) ·
**test** = automated/off-screen only · **open** = not verified yet.

## Desktop pet
| Feature | Status |
|---|---|
| Pet above all windows, clicks pass through, drag & drop, no taskbar entry | live |
| 6 species, 28 breeds; HD sheets 120×120 (density 6) with 32/24/32 walk/gallop/sneak frames, generator as fallback | live (all 28 switched through) |
| Gaits walk/gallop/sneak, birds/dragons fly; 60 fps only while moving | live |
| Everyday life (scratching post, pillow, bed, TV, box, yarn, mouse chase, bone, visitor) + rare random memes | live (samples), test (every scene × every species) |
| 11 memes + Hype Train, GigaChad, Absolute Cinema | test (all × all species), live samples |
| Window climbing + napping on top (KDE, runtime KWin script) | live confirmed |
| Start window (Twitch/OBS buttons, pet choice, status), single instance, tray, app icon | live |
| Sounds (optional, **off** by default, volume 0–100 %): synthesised per-species voices, train horn, confetti, bonk, teleport; cooldown against floods | test (synthesis, events, player, toggling), live: all sounds loaded/played on a real audio device |
| Several pets: up to 3 companions (start window: add, on/off, remove), own drag handles, follow each other, play ball, sleep side by side; chat reactions are spread, stream scenes stay with the main pet; OBS shows all | test (social actions, management, limit, dragging, OBS sprites); measured live |
| Screen adaptation: overlay is bound to the target monitor, pixel art crisp at device resolution for 125 %/200 %, optional auto size (~1/15 of usable height, manual size kept), position kept proportionally on monitor/resolution change, negative monitor coordinates | test with 3 simulated monitors (1920×1080 100 %, 2560×1440 200 %, 3440×1440 125 % offset left/up) on Qt 6.9.1 and 6.12; live 3440×1440 100 %; **open:** real mixed DPI/portrait |
| Several monitors: optionally wander between neighbouring monitors; plugged/unplugged monitors, resolution/dock changes are applied | test (2 simulated monitors, different size/DPI); **open:** real multi-monitor desktop |
| Settings apply instantly, no restart | test (6 cases), start-window status live |
| Pet packs (export template, import, select) | test (pixel-exact round trip, malicious ZIPs) |

## Streaming
| Feature | Status |
|---|---|
| OBS browser source (127.0.0.1, transparent) | live in a browser; **open:** real OBS app |
| OBS survives pet switches/app restarts without reload | live in a browser (225 samples, 0 missing frames) |
| Twitch chat (anonymous, IRC) | live (public channels) |
| Twitch login (device code) + EventSub subscriptions | live (account connected, subscriptions without errors) |
| Reactions to real follow/sub/bits/raid/Hype Train events | test (mapping); **open:** real events |
| Twitch token in the system keyring: Linux Secret Service, macOS Keychain, Windows Credential Manager; logout/refresh/revocation | test (life cycle), real storage in CI on Windows/macOS |
| Chat rules: 45 regex rules in `reactions.json`, cooldowns, spam protection | test |

## Builds
| Platform | Status |
|---|---|
| Linux/Windows/macOS packages via GitHub Actions, tests run on all three | CI green |
| Release v0.4.0 with all three packages | published |
| Arch/CachyOS PKGBUILD | built locally |
| Windows/macOS packages on real hardware | **open** (overlay, click-through, tray, autostart, DPI) |

## Measurements (KDE, 3440×1440, scale 6, `scripts/measure_perf.py`)
Only changed regions are repainted (previously the whole screen-sized overlay every frame):

| State | CPU (1 core) before → after | repainted area per frame | fps |
|---|---|---|---|
| Idle | 0.1 % → 0.1 % | 4.8 M → ~16,000 px | ~1 |
| Sleep | 0.8 % → 0.3 % | 4.8 M → ~16,000 px | 8 |
| Walking | 4.7 % → 1.6 % | 4.8 M → ~16,000 px | 60 |

RAM ~144 MB (RSS, HD pet loaded). **4 HD pets at once, all walking: 4.3 % CPU, 165 MB RAM**; idle 0.2 %, sleep 0.5 %. Compositor load drops as well (not measured separately).

## Tests
`python3 -m unittest discover -s tests -t .` – 84 tests (incl. pixel-exact partial vs. full repaint across all scenes, simulated multi-monitor/DPI scenarios): movement, priorities, all scenes/memes × all species, climbing, HD sprites (frame count, cycle time, scenes), pet packs, chat, Twitch parser, EventSub mapping, OBS (incl. pet switch/reconnect), live settings, settings validation.

## Technical limits
- Native Wayland: KWin forbids clients to position themselves or stay on top → TinyPaws runs via XWayland
  (`X11BypassWindowManagerHint`, raised every 2 s; a newly opened window can briefly cover the pet).
  Full-screen games can cover the pet. Layer-shell alternative: feasibility checked, see docs/WAYLAND.md.
- Window climbing on KDE only; untested with display scaling ≠ 100 %.
- Windows/macOS: unsigned.
- Visiting animals are always the base breed of their species.

## Next steps
Verification on real hardware (Windows/macOS, multi-monitor with mixed scaling, OBS app, real Twitch events); native Wayland overlay (layer shell in its own process); code signing.

---

# 🇩🇪 Entwicklungsstand (v0.4.0, Stand 2026-11-01)

Legende: **live** = auf CachyOS/KDE Plasma 6 (Wayland, App über XWayland) am echten Desktop geprüft ·
**Test** = nur automatisiert/offscreen geprüft · **offen** = nicht abgenommen.

### Desktop-Haustier
| Funktion | Stand |
|---|---|
| Tier über allen Fenstern, Klicks gehen durch, Ziehen/Fallenlassen, kein Taskleisteneintrag | live |
| 6 Tierarten, 28 Rassen; HD-Sheets 120×120 (Dichte 6) mit 32/24/32 Lauf-/Galopp-/Schleich-Bildern, Generator als Ersatz | live (alle 28 durchgeschaltet) |
| Gangarten Gehen/Galopp/Schleichen, Vogel/Drache fliegen; 60 Bilder/s nur in Bewegung | live |
| Eigenleben (Kratzbaum, Kissen, Bett, TV, Karton, Wolle, Mausjagd, Knochen, Besuch) + seltene Memes zufällig | live (Stichproben), Test (jede Szene × jede Tierart) |
| 11 Memes + Hype Train, GigaChad, Absolute Cinema | Test (alle × alle Tierarten), live Stichproben |
| Fenster klettern + oben schlafen (KDE, Laufzeit-KWin-Skript) | live bestätigt |
| Startfenster (Twitch/OBS-Knöpfe, Tierwahl, Status), Einzelinstanz, Tray, App-Icon | live |
| Töne (optional, Standard **aus**, Lautstärke 0–100 %): selbst synthetisierte Tierstimmen je Art, Lok-Hupe, Konfetti, Bonk, Teleport; Abklingzeit gegen Flut | Test (Synthese, Ereignisse, Player, Umschalten), live: alle Töne auf echtem Audiogerät geladen/abgespielt |
| Mehrere Tiere: bis zu 3 Begleiter (Startfenster: hinzufügen, an/aus, entfernen), eigene Griffe, laufen einander hinterher, spielen Ball, schlafen nebeneinander; Chat-Reaktionen verteilen sich, Stream-Szenen bleiben beim Haupttier; OBS zeigt alle | Test (soziale Aktionen, Verwaltung, Limit, Ziehen, OBS-Sprites); Messung live |
| Bildschirm-Anpassung: Overlay wird dem Zielmonitor zugeordnet (vorher auf alte Monitorgröße gekappt), Pixelart scharf in Geräteauflösung bei 125 %/200 %, optionale Auto-Größe (~1/15 der nutzbaren Höhe, manuelle Größe bleibt), Position proportional bei Monitor-/Auflösungswechsel, negative Monitor-Koordinaten | Test mit 3 simulierten Monitoren (1920×1080 100 %, 2560×1440 200 %, 3440×1440 125 % links/oben versetzt) auf Qt 6.9.1 und 6.12; live 3440×1440 100 %; **offen:** echte gemischte DPI/Hochformat |
| Mehrere Monitore: optional zwischen benachbarten Monitoren wandern; an-/abgesteckte Monitore, Auflösungs-/Dock-Änderungen werden übernommen | Test (simulierte 2 Monitore, unterschiedliche Größe/DPI); **offen:** echter Mehrmonitor-Desktop |
| Einstellungen wirken sofort, ohne Neustart | Test (6 Fälle), Startfenster-Status live |
| Tierpakete (Vorlage exportieren, importieren, auswählen) | Test (pixelgenauer Round-Trip, bösartige ZIPs) |

### Streaming
| Funktion | Stand |
|---|---|
| OBS-Browserquelle (127.0.0.1, transparent) | live im Browser; **offen:** echte OBS-App |
| OBS bei Tierwechsel/App-Neustart ohne Reload | live im Browser (225 Messpunkte, 0 fehlende Bilder) |
| Twitch-Chat (anonym, IRC) | live (öffentliche Kanäle) |
| Twitch-Login (Device-Code) + EventSub-Abos | live (Konto verbunden, Abos ohne Fehler) |
| Reaktion auf echte Follow/Abo/Bits/Raid/Hype-Train-Events | Test (Mapping); **offen:** echte Events |
| Twitch-Token im System-Schlüsselbund: Linux Secret Service, macOS Schlüsselbund, Windows Anmeldeinformationsverwaltung; Abmelden/Refresh/Widerruf | Test (Lebenszyklus), echte Ablage in CI auf Windows/macOS |
| Chat-Regeln: 45 Regex-Regeln in `reactions.json`, Cooldowns, Spam-Schutz | Test |

### Builds
| Plattform | Stand |
|---|---|
| Linux/Windows/macOS-Pakete per GitHub Actions, Tests laufen auf allen drei | CI grün |
| Release v0.4.0 mit allen drei Paketen | veröffentlicht |
| Arch/CachyOS-PKGBUILD | lokal gebaut |
| Windows-/macOS-Pakete auf echter Hardware | **offen** (Overlay, Klickdurchlass, Tray, Autostart, DPI) |

### Messwerte (KDE, 3440×1440, Skalierung 6, `scripts/measure_perf.py`)
Nur geänderte Bildbereiche werden neu gezeichnet (vorher jedes Mal das ganze bildschirmgroße Overlay):

| Zustand | CPU (1 Kern) vorher → nachher | neu gezeichnete Fläche je Bild | Bilder/s |
|---|---|---|---|
| Leerlauf | 0,1 % → 0,1 % | 4,8 Mio. → ~16 000 px | ~1 |
| Schlaf | 0,8 % → 0,3 % | 4,8 Mio. → ~16 000 px | 8 |
| Laufen | 4,7 % → 1,6 % | 4,8 Mio. → ~16 000 px | 60 |

RAM ~144 MB (RSS, HD-Tier geladen). **4 HD-Tiere gleichzeitig, alle laufend: 4,3 % CPU, 165 MB RAM**; Leerlauf 0,2 %, Schlaf 0,5 %. Last des Compositors sinkt zusätzlich (nicht separat gemessen).

### Tests
`python3 -m unittest discover -s tests -t .` – 84 Tests (inkl. pixelgenauer Vergleich Teil- vs. Voll-Neuzeichnen über alle Szenen, simulierte Mehrmonitor-/DPI-Szenarien): Bewegung, Prioritäten, alle Szenen/Memes × alle
Tierarten, Klettern, HD-Sprites (Bildzahl, Zyklusdauer, Szenen), Tierpakete, Chat, Twitch-Parser,
EventSub-Mapping, OBS (inkl. Tierwechsel/Reconnect), Live-Einstellungen, Settings-Validierung.

### Technische Einschränkungen
- Native Wayland: KWin verbietet Positionierung/„immer oben“ für Clients → TinyPaws läuft über XWayland
  (`X11BypassWindowManagerHint`, Anheben alle 2 s; ein neues Fenster kann kurz darüber liegen).
  Vollbild-Spiele können das Tier überdecken. Layer-Shell-Alternative: Machbarkeit geprüft, siehe docs/WAYLAND.md.
- Fensterklettern nur KDE; bei Bildschirmskalierung ≠ 100 % ungetestet.
- Windows/macOS: unsigniert.
- Besuchertiere sind immer die Grundrasse ihrer Art.

### Nächste Schritte
Abnahme auf echter Hardware (Windows/macOS, Mehrmonitor mit gemischter Skalierung, OBS-App, echte Twitch-Ereignisse); natives Wayland-Overlay (Layer-Shell in eigenem Prozess); Code-Signierung.
