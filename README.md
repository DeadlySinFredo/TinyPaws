# TinyPaws

Kleine Pixel-Tiere (Katze, Hund, Fuchs, Hase, Drache, Vogel – je 4–6 Rassen), die auf deinem Desktop lebt – läuft herum, schläft, springt, macht Unsinn
und reagiert (später) auf Twitch/Kick/YouTube/TikTok-Events. Ohne KI, ~1 % CPU, ~100 MB RAM.

*A tiny pixel cat living on your desktop. No AI required. German/English UI.*

## Schnellstart (Linux, CachyOS/KDE getestet)

```bash
sudo pacman -S pyside6     # falls nicht vorhanden
./install.sh               # Menüeintrag
python3 -m tinypaws --panel
```

- Erster Start: Einrichtungsassistent (Name, Pixel-Größe, FPS, Zufallsaktivität, Sprache, Monitor, Autostart, Gedichte).
- **Linke Maustaste auf der Katze**: ziehen und fallen lassen. **Doppelklick**: Miau. **Rechtsklick**: Menü.
- Überall sonst gehen Klicks durch zu deinen Fenstern.
- Tray-Icon: Testpanel, Meme-Szenen, Interaktion an/aus, Einstellungen, Beenden.
- `--panel` öffnet das Testpanel, `--reset` startet den Assistenten neu.
- Einstellungen: `~/.config/tinypaws/settings.json`, Autostart: `~/.config/autostart/tinypaws.desktop`.

## Testpanel

Alle Aktionen, die drei Meme-Szenen (**Hype Train** mit Level 1–10, **GigaChad**, **Absolute Cinema**),
simulierte Stream-Events (Follow/Abo/Raid) und eine Chat-Simulation – ohne Streaming-Plattform.

## OBS

Einstellungen → „OBS-Browser-Quelle" aktivieren. In OBS: Quelle **Browser**, URL `http://127.0.0.1:8737/`,
Breite/Höhe = deine Bildschirmauflösung (ohne Taskleiste). Hintergrund ist transparent, alles läuft synchron
zur Desktop-Katze. Server lauscht nur auf localhost.

## Twitch

Einstellungen → „Twitch-Kanal (nur lesen)“ → Kanalname eintragen. Anonymer Lesezugang über Twitch-IRC,
**kein Login, kein Token**. Erkannt: Chat, Abos/Resubs, Geschenk-Abos, Bits, Raids. Automatischer
Reconnect mit Backoff. Hype Train braucht EventSub + OAuth (kommt später) – bis dahin über Chat
„hype train“ oder das Testpanel.

## Chat-Reaktionen

Regeln in [`tinypaws/reactions.json`](tinypaws/reactions.json): Regex-Muster, Chance, Cooldown,
Priorität, Aktion. Neue Reaktionen = neuer JSON-Eintrag, kein Code.

## Tests

```bash
python3 -m unittest discover -s tests -t .
python3 scripts/render_preview.py preview.png   # Szenen offscreen als PNG rendern
```

Siehe [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md).
