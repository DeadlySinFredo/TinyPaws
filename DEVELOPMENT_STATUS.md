# Entwicklungsstand (v0.3.0 + Arbeit an #3, Stand 2026-10-31)

Legende: **live** = auf CachyOS/KDE Plasma 6 (Wayland, App über XWayland) am echten Desktop geprüft ·
**Test** = nur automatisiert/offscreen geprüft · **offen** = nicht abgenommen.

## Desktop-Haustier
| Funktion | Stand |
|---|---|
| Tier über allen Fenstern, Klicks gehen durch, Ziehen/Fallenlassen, kein Taskleisteneintrag | live |
| 6 Tierarten, 28 Rassen; HD-Sheets 120×120 (Dichte 6) mit 32/24/32 Lauf-/Galopp-/Schleich-Bildern, Generator als Ersatz | live (alle 28 durchgeschaltet) |
| Gangarten Gehen/Galopp/Schleichen, Vogel/Drache fliegen; 60 Bilder/s nur in Bewegung | live |
| Eigenleben (Kratzbaum, Kissen, Bett, TV, Karton, Wolle, Mausjagd, Knochen, Besuch) + seltene Memes zufällig | live (Stichproben), Test (jede Szene × jede Tierart) |
| 11 Memes + Hype Train, GigaChad, Absolute Cinema | Test (alle × alle Tierarten), live Stichproben |
| Fenster klettern + oben schlafen (KDE, Laufzeit-KWin-Skript) | live bestätigt |
| Startfenster (Twitch/OBS-Knöpfe, Tierwahl, Status), Einzelinstanz, Tray, App-Icon | live |
| Mehrere Tiere: bis zu 3 Begleiter (Startfenster: hinzufügen, an/aus, entfernen), eigene Griffe, laufen einander hinterher, spielen Ball, schlafen nebeneinander; Chat-Reaktionen verteilen sich, Stream-Szenen bleiben beim Haupttier; OBS zeigt alle | Test (soziale Aktionen, Verwaltung, Limit, Ziehen, OBS-Sprites); Messung live |
| Mehrere Monitore: optional zwischen benachbarten Monitoren wandern; an-/abgesteckte Monitore, Auflösungs-/Dock-Änderungen werden übernommen | Test (simulierte 2 Monitore, unterschiedliche Größe/DPI); **offen:** echter Mehrmonitor-Desktop |
| Einstellungen wirken sofort, ohne Neustart | Test (6 Fälle), Startfenster-Status live |
| Tierpakete (Vorlage exportieren, importieren, auswählen) | Test (pixelgenauer Round-Trip, bösartige ZIPs) |

## Streaming
| Funktion | Stand |
|---|---|
| OBS-Browserquelle (127.0.0.1, transparent) | live im Browser; **offen:** echte OBS-App |
| OBS bei Tierwechsel/App-Neustart ohne Reload (#3 P0, PR #4) | live im Browser (225 Messpunkte, 0 fehlende Bilder) |
| Twitch-Chat (anonym, IRC) | live (öffentliche Kanäle) |
| Twitch-Login (Device-Code) + EventSub-Abos | live (Konto verbunden, Abos ohne Fehler) |
| Reaktion auf echte Follow/Abo/Bits/Raid/Hype-Train-Events | Test (Mapping); **offen:** echte Events |
| Chat-Regeln: 45 Regex-Regeln in `reactions.json`, Cooldowns, Spam-Schutz | Test |

## Builds
| Plattform | Stand |
|---|---|
| Linux/Windows/macOS-Pakete per GitHub Actions, Tests laufen auf allen drei | CI grün |
| Release v0.3.0 mit allen drei Paketen | veröffentlicht (Repo privat) |
| Arch/CachyOS-PKGBUILD | lokal gebaut |
| Windows-/macOS-Pakete auf echter Hardware | **offen** (Overlay, Klickdurchlass, Tray, Autostart, DPI) |

## Messwerte (KDE, 3440×1440, Skalierung 6, `scripts/measure_perf.py`)
Nur geänderte Bildbereiche werden neu gezeichnet (vorher jedes Mal das ganze bildschirmgroße Overlay):

| Zustand | CPU (1 Kern) vorher → nachher | neu gezeichnete Fläche je Bild | Bilder/s |
|---|---|---|---|
| Leerlauf | 0,1 % → 0,1 % | 4,8 Mio. → ~16 000 px | ~1 |
| Schlaf | 0,8 % → 0,3 % | 4,8 Mio. → ~16 000 px | 8 |
| Laufen | 4,7 % → 1,6 % | 4,8 Mio. → ~16 000 px | 60 |

RAM ~144 MB (RSS, HD-Tier geladen). **4 HD-Tiere gleichzeitig, alle laufend: 4,3 % CPU, 165 MB RAM**; Leerlauf 0,2 %, Schlaf 0,5 %. Last des Compositors sinkt zusätzlich (nicht separat gemessen).

## Tests
`python3 -m unittest discover -s tests -t .` – 61 Tests (inkl. pixelgenauer Vergleich Teil- vs. Voll-Neuzeichnen über alle Szenen): Bewegung, Prioritäten, alle Szenen/Memes × alle
Tierarten, Klettern, HD-Sprites (Bildzahl, Zyklusdauer, Szenen), Tierpakete, Chat, Twitch-Parser,
EventSub-Mapping, OBS (inkl. Tierwechsel/Reconnect), Live-Einstellungen, Settings-Validierung.

## Technische Einschränkungen
- Native Wayland: KWin verbietet Positionierung/„immer oben“ für Clients → TinyPaws läuft über XWayland
  (`X11BypassWindowManagerHint`, Anheben alle 2 s; ein neues Fenster kann kurz darüber liegen).
  Vollbild-Spiele können das Tier überdecken. Layer-Shell-Alternative wird in #3 geprüft.
- Fensterklettern nur KDE; bei Bildschirmskalierung ≠ 100 % ungetestet.
- Windows/macOS: unsigniert; Twitch-Token dort ohne `secret-tool` nur im Speicher.
- Besuchertiere sind immer die Grundrasse ihrer Art.

## Nächste Schritte
Siehe Issue #3: Performance-Messung, Multi-Monitor, Multi-Pet, Wayland-Layer-Shell, Sound, Streaming-Härtung.
