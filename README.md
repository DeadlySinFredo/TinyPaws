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
- **Startfenster** (Klick aufs Tray-Symbol oder TinyPaws erneut starten): große Knöpfe **Mit Twitch verbinden** und **In OBS einbinden**, Tierauswahl, Testpanel, Einstellungen.
- **Tier wechseln**: Tray-Menü oder Rechtsklick auf das Tier → „Tier wählen“ (sofort, ohne Neustart), oder oben im Testpanel.
- Tray-Icon: Testpanel, Meme-Szenen, Interaktion an/aus, Einstellungen, Beenden.
- `--panel` öffnet das Testpanel, `--reset` startet den Assistenten neu.
- Einstellungen: `~/.config/tinypaws/settings.json`, Autostart: `~/.config/autostart/tinypaws.desktop`.

## Installation

**Downloads (neueste Version):** [Alle Releases](https://github.com/DeadlySinFredo/TinyPaws/releases) · [Neuestes Release](https://github.com/DeadlySinFredo/TinyPaws/releases/latest)

| System | Download | Weg |
|---|---|---|
| **CachyOS / Arch** | – | `packaging/arch/PKGBUILD`: `cd packaging/arch && TINYPAWS_REPO=file://$PWD/../.. TINYPAWS_BRANCH=dev makepkg -si` (privates Repo → lokaler Checkout). Danach im Startmenü „TinyPaws“ oder `tinypaws`. |
| **Linux (andere)** | [TinyPaws-linux-x86_64.tar.gz](https://github.com/DeadlySinFredo/TinyPaws/releases/latest/download/TinyPaws-linux-x86_64.tar.gz) | Entpacken, `TinyPaws/TinyPaws` starten. |
| **Windows 10/11** | [TinyPaws-windows-x86_64.zip](https://github.com/DeadlySinFredo/TinyPaws/releases/latest/download/TinyPaws-windows-x86_64.zip) | Entpacken, `TinyPaws.exe` starten. Unsigniert: SmartScreen → „Weitere Informationen“ → „Trotzdem ausführen“. |
| **macOS (Apple Silicon)** | [TinyPaws-macos-arm64.zip](https://github.com/DeadlySinFredo/TinyPaws/releases/latest/download/TinyPaws-macos-arm64.zip) | Entpacken, `TinyPaws.app` per Rechtsklick → „Öffnen“ (unsigniert). Lebt im Tray, kein Dock-Symbol. |

Builds entstehen automatisch bei jedem Push (GitHub Actions, Reiter „Actions“ → Artefakte);
ein Tag `v*` erzeugt ein Release mit allen drei Paketen.

## Testpanel

Alle Aktionen, die drei Meme-Szenen (**Hype Train** mit Level 1–10, **GigaChad**, **Absolute Cinema**),
simulierte Stream-Events (Follow/Abo/Raid) und eine Chat-Simulation – ohne Streaming-Plattform.

## Fenster klettern (KDE Plasma)

Das Tier klettert ab und zu an Fenstern hoch und schläft oben drauf. Dafür lädt TinyPaws beim Start
ein kleines KWin-Skript (nur solange die App läuft). Abschaltbar in den Einstellungen.

## Eigene Tiere

Tray-Menü → „Tier als Vorlage exportieren…“, Spritesheet umzeichnen, „Tierpaket importieren…“.
Format und Regeln: [docs/PET_PACKS.md](docs/PET_PACKS.md).

## OBS

Tray-Menü → **„OBS-Link kopieren“** (schaltet die Quelle bei Bedarf ein). In OBS: Quelle **Browser**, Link einfügen,
Breite/Höhe = deine Bildschirmauflösung (ohne Taskleiste). Hintergrund ist transparent, alles läuft synchron
zur Desktop-Katze. Server lauscht nur auf localhost.

## Twitch

Einstellungen → „Twitch-Kanal (nur lesen)“ → Kanalname eintragen. Anonymer Lesezugang über Twitch-IRC,
**kein Login, kein Token**. Erkannt: Chat, Abos/Resubs, Geschenk-Abos, Bits, Raids. Automatischer
Reconnect mit Backoff.

**Echter Hype Train + Follows (Twitch-Login, einmalig einrichten):**

1. <https://dev.twitch.tv/console/apps> → „Anwendung registrieren“ (öffnet TinyPaws auch selbst): Name z. B. `TinyPaws-<dein Name>`,
   OAuth-Redirect `http://localhost`, Kategorie „Other“, Client-Typ **Öffentlich**.
2. Tray-Menü → **„Mit Twitch verbinden“**: beim ersten Mal öffnet sich die Twitch-Entwicklerseite und ein
   Fenster, in das du die **Client-ID** einfügst. Danach zeigt TinyPaws einen Code und öffnet
   twitch.tv/activate – dort bestätigen. Kein Passwort geht durch TinyPaws. Der Chat deines Kanals wird
   automatisch mit verbunden.

Der Zugangsschlüssel liegt danach verschlüsselt im System-Schlüsselbund (Secret Service/KWallet),
nicht in einer Datei. Dann kommen Hype Train (Start, Level-Up, Ende), Follows, Abos, Geschenk-Abos,
Bits und Raids über Twitch EventSub; Abmelden über das Tray-Menü.

## Chat-Reaktionen

Regeln in [`tinypaws/reactions.json`](tinypaws/reactions.json): Regex-Muster, Chance, Cooldown,
Priorität, Aktion. Neue Reaktionen = neuer JSON-Eintrag, kein Code.

## Tests

```bash
python3 -m unittest discover -s tests -t .
python3 scripts/render_preview.py preview.png   # Szenen offscreen als PNG rendern
```

Siehe [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md).

## Lizenz

MIT – siehe [LICENSE](LICENSE). Alle Grafiken, Texte und Gedichte sind eigene Werke.
