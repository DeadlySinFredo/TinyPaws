# Entwicklungsstand (2026-10-31, v0.2.0)

## Funktioniert (auf CachyOS / KDE Plasma / Wayland via XWayland live geprüft)
- Katze erscheint unten auf dem gewählten Monitor über der Taskleiste, über normalen Fenstern, ohne Taskleisteneintrag.
- Laufen, Rennen, Sitzen, Blinzeln, Schlafen mit „z"-Partikeln, Aufwachen/Strecken, Springen, Ball, Kaffee, Teleport-Glitch.
- Ziehen mit der Maus + Herunterfallen; Klicks neben der Katze gehen durch.
- Schaut zum Mauszeiger, wenn sie in der Nähe ist und idle ist.
- Hype Train, GigaChad, Absolute Cinema über Testpanel, Tray und Chat-Simulation.
- Einstellungen + Position werden gespeichert und beim Start wiederhergestellt; Autostart per XDG.
- OBS-Browser-Quelle `http://127.0.0.1:8737/` (in Einstellungen aktivierbar), live im Browser geprüft: Katze erscheint transparent und synchron.
- Twitch-Chat anonym: live mit 5 öffentlichen Kanälen verbunden, Chatnachrichten empfangen.
- Tiere jetzt in 48×48 Pixeln (Dichte 3), Standardgröße 96 px (Skalierung 6 ≈ 3 Mauszeiger), runde Glanzaugen, Schnurrhaare.
- Echter Gangzyklus mit Knie/Pfotenheben: Gehen (8 Frames), Galopp (6), Anschleichen (8, geduckt); Geschwindigkeit passend zur Schrittlänge (keine rutschenden Pfoten).
- Hund (Beagle-Welpe) + Rassen: Katze Tuxedo/Rot getigert/Grau/Weiß/Schwarz/Creme, Hund Beagle/Golden Retriever/Husky/Corgi/Schwarzer Labrador/Weiß.
- Katze ursprünglich: Chibi-Stil schwarz-weiß (Tuxedo), große Glanzaugen, Schattierung; Idle/Überrascht/Cinema frontal sitzend, Laufen/Springen/Schlafen seitlich.
- Gemessen: ~2 % CPU (30 FPS, 1 Kern), ~115 MB RSS; im Schlaf 8 FPS.

## Getestet
- `python3 -m unittest discover -s tests -t .` – 29 Tests (inkl. Gangarten, Hund in allen Szenen, OBS-Server und Twitch-Parser/Validierung): Sprites, Bewegung, Schlaf, Ziehen/Fallen, 20 000 Zufallsschritte bleiben auf dem Bildschirm, Prioritäten/Queue, alle drei Szenen laufen durch (Hype Train kehrt zur Startposition zurück), Chat-Matching, Cooldowns, kaputte Regex, Event-Routing, Settings-Roundtrip + Validierung.
- `scripts/render_preview.py` rendert Szenen offscreen als PNG (visuell geprüft).
- Live-Start + Screenshot auf dem Desktop.

## Fehlt noch
Siehe ROADMAP: weitere Tierarten, echte Stream-Connectors, OBS-Modus, mehr Memes/Gegenstände, Editor, KI, Windows/macOS-Pakete, Wandern zwischen Monitoren, Sound.

## Technische Einschränkungen
- Native Wayland: KWin verbietet Positionierung/„immer oben" → XWayland. Vollbild-Spiele können die Katze überdecken.
- Fenster-Raise alle 2 s: ganz kurz kann ein neu geöffnetes Fenster über der Katze liegen.
- Settings-Änderung startet den Prozess neu.

## Nächste Schritte
1. Twitch EventSub (Hype Train/Follows). 2. Vogel, Fuchs, Hase, Drache. 3. Mehr Memes.
