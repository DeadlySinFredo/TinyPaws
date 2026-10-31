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

## Messwerte (KDE, 3440×1440, Skalierung 6)
~2 % CPU (eines Kerns) im Leerlauf bei 30 Bilder/s, 8 Bilder/s im Schlaf; ~136 MB RAM.
Bewegung mit 60 Bilder/s noch nicht gemessen (#3 Performance).

## Tests
`python3 -m unittest discover -s tests -t .` – 58 Tests: Bewegung, Prioritäten, alle Szenen/Memes × alle
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
