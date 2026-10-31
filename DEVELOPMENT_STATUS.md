# Entwicklungsstand (2026-10-31, v0.2.0)

## Funktioniert (auf CachyOS / KDE Plasma / Wayland via XWayland live geprüft)
- Katze erscheint unten auf dem gewählten Monitor über der Taskleiste, über normalen Fenstern, ohne Taskleisteneintrag.
- Laufen, Rennen, Sitzen, Blinzeln, Schlafen mit „z"-Partikeln, Aufwachen/Strecken, Springen, Ball, Kaffee, Teleport-Glitch.
- Ziehen mit der Maus + Herunterfallen; Klicks neben der Katze gehen durch.
- Schaut zum Mauszeiger, wenn sie in der Nähe ist und idle ist.
- Hype Train, GigaChad, Absolute Cinema über Testpanel, Tray und Chat-Simulation.
- Einstellungen + Position werden gespeichert und beim Start wiederhergestellt; Autostart per XDG.
- OBS lädt nur die Bilder des gewählten Tiers (~180 KB statt ~9 MB).
- OBS-Browser-Quelle `http://127.0.0.1:8737/` (in Einstellungen aktivierbar), live im Browser geprüft: Katze erscheint transparent und synchron.
- Twitch-Chat anonym: live mit 5 öffentlichen Kanälen verbunden, Chatnachrichten empfangen.
- Tiere jetzt in 48×48 Pixeln (Dichte 3), Standardgröße 96 px (Skalierung 6 ≈ 3 Mauszeiger), runde Glanzaugen, Schnurrhaare.
- Echter Gangzyklus mit Knie/Pfotenheben: Gehen (8 Frames), Galopp (6), Anschleichen (8, geduckt); Geschwindigkeit passend zur Schrittlänge (keine rutschenden Pfoten).
- 6 Tierarten: Katze, Hund, Fuchs (buschiger Schwanz), Hase (Schlappohren nach hinten, Puschel), Drache (Hörner, Flügel schlagen beim Fliegen), Vogel (eigener Körper: hüpft, fliegt mit Flügelschlag, breitet bei GigaChad die Flügel aus). Vogel und Drache fliegen beim Rennen im Bogen durch die Luft.
- 11 Memes über eine datengetriebene Meme-Engine (Zeitleiste aus Schritten): This is Fine (Flammen + Kaffee), Bonk (Spielzeughammer + Sterne), Let Him Cook (Kochmütze + Herd + Dampf), Dramatic Exit (Koffer, läuft weg, fällt zurück), Achievement (Pokal + Banner), RIP (Grabstein, „Nur Spaß!“), Sus, Cat Distribution System (zweites Tier aus dem Karton), Tanz-Party (Noten), Brainrot (Chaos), Schreckmoment (Geist). Alle per Testpanel und Chat auslösbar.
- Eigene Tiere: Vorlage exportieren → umzeichnen → importieren; geprüft per Round-Trip-Test (pixelgenau), Szenen-Test mit Paket-Tier und Abwehr bösartiger ZIPs (Pfad-Tricks, falsche Felder, fehlende Dateien).
- Twitch EventSub: Hype Train (Start → Zug-Szene mit echten Top-Unterstützern, Level-Up → Jubel, Ende → große Feier), Follows, Abos, Geschenk-Abos, Bits, Raids. Login per Device-Code. Geprüft: Mapping per Tests, Fehlerpfad gegen echte Twitch-API (ungültige Client-ID wird sauber gemeldet). **Nicht geprüft**: echter Login + echte Events (braucht deine Client-ID).
- Fenster klettern (KDE): Tier läuft zur Fensterkante, klettert die Seite hoch (Laufzyklus um 90° gedreht), springt oben drauf, schläft mit herabhängenden Vorderpfoten und Schwanz, fährt mit, wenn das Fenster verschoben wird, fällt herunter, wenn es geschlossen/minimiert wird, und springt danach wieder runter. Nur Fenster, die kleiner als der Bildschirm und nicht verdeckt sind. Testpanel: „Fenster klettern“.
- Eigenleben: Kratzbaum (nur Katze), Kissen-Nickerchen, Bett mit Decke, Fernsehen mit Popcorn, im Karton sitzen, Wollknäuel, Mausjagd, Knochen (nur Hund), Besuch von einem anderen Tier; das Tier macht das (und seltene Memes) zufällig von selbst, gewichtet nach Zufallsaktivität und passend zur Tierart. Auch per Chat/Testpanel.
- Gegenstände im gleichen detaillierten Stil (48er-Raster, Schattierung): Lok mit Speichenrädern, Kuppelstange, Laterne; Waggons mit Namensschild; Kinosessel mit Knöpfen; Pizza, Kaffeetasse mit Herz und Dampf, Popcorn, Banane, Ball.
- Flüssiger: Gehen 16, Galopp 12, Schleichen 16 Bilder pro Zyklus (~30 Bilder/s); nach dem Laufen bleibt das Tier seitlich stehen statt ruckartig nach vorne zu drehen.
- Rassen: Katze Tuxedo/Rot getigert/Grau/Weiß/Schwarz/Creme, Hund Beagle/Golden Retriever/Husky/Corgi/Schwarzer Labrador/Weiß, Fuchs Rot/Polar/Silber/Wüste, Hase Wild/Weiß/Grau/Schwarz, Drache Grün/Rot/Lila/Gold, Vogel Wellensittich blau/grün, Kanarienvogel, Rotkehlchen.
- Katze ursprünglich: Chibi-Stil schwarz-weiß (Tuxedo), große Glanzaugen, Schattierung; Idle/Überrascht/Cinema frontal sitzend, Laufen/Springen/Schlafen seitlich.
- Gemessen: ~2 % CPU (30 FPS, 1 Kern), ~120 MB RSS; im Schlaf 8 FPS.

## Getestet
- `python3 -m unittest discover -s tests -t .` – 45 Tests (inkl. Tierpakete, EventSub-Mapping, Klettern: Fensterfilter, kompletter Ablauf, Mitfahren, Herunterfallen, jedes Meme mit jeder Tierart, alle Tierarten/Rassen in allen Szenen, Fliegen, Gangarten, Hund in allen Szenen, OBS-Server und Twitch-Parser/Validierung): Sprites, Bewegung, Schlaf, Ziehen/Fallen, 20 000 Zufallsschritte bleiben auf dem Bildschirm, Prioritäten/Queue, alle drei Szenen laufen durch (Hype Train kehrt zur Startposition zurück), Chat-Matching, Cooldowns, kaputte Regex, Event-Routing, Settings-Roundtrip + Validierung.
- `scripts/render_preview.py` rendert Szenen offscreen als PNG (visuell geprüft).
- Live-Start + Screenshot auf dem Desktop.

## Fehlt noch
Siehe ROADMAP: weitere Tierarten, echte Stream-Connectors, OBS-Modus, mehr Memes/Gegenstände, Editor, KI, Windows/macOS-Pakete, Wandern zwischen Monitoren, Sound.

## Technische Einschränkungen
- Fensterklettern nur unter KDE Plasma: ein KWin-Skript wird zur Laufzeit geladen (keine dauerhafte KWin-Änderung) und meldet Fenstergeometrien per D-Bus; beim Beenden (auch SIGTERM) wird es entladen. Bei Bildschirmskalierung ≠ 100 % können XWayland- und KWin-Koordinaten abweichen (ungetestet).
- Native Wayland: KWin verbietet Positionierung/„immer oben" → XWayland. Vollbild-Spiele können die Katze überdecken.
- Fenster-Raise alle 2 s: ganz kurz kann ein neu geöffnetes Fenster über der Katze liegen.
- Settings-Änderung startet den Prozess neu.

## Nächste Schritte
1. Twitch EventSub (Hype Train/Follows). 2. Twitch-Login mit echter Client-ID live testen; Fenster klettern für GNOME/Windows/macOS. 3. Mehr Memes.
