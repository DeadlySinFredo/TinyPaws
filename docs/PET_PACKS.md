# TinyPaws-Tierpakete (Format 1)

Ein Tierpaket ist eine **ZIP-Datei** mit genau zwei verwendeten Dateien:

| Datei | Inhalt |
|---|---|
| `manifest.json` | Beschreibung (siehe unten) |
| `sheet.png` | Spritesheet: alle Bilder in einem Raster gleich großer Zellen, transparenter Hintergrund |

Alles andere im ZIP wird ignoriert und **nie** entpackt. Pakete enthalten keinen Code.

## Schnellster Weg

1. Tray-Menü → **„Tier als Vorlage exportieren…“** – speichert dein aktuelles Tier als Paket.
2. ZIP entpacken, `sheet.png` in einem Pixel-Programm umzeichnen (Aseprite, LibreSprite, Krita, GIMP).
   Zellen und Positionen beibehalten.
3. In `manifest.json` `id` und `name` ändern, beide Dateien wieder zippen.
4. Tray-Menü → **„Tierpaket importieren…“**, dann unter Einstellungen → Tier auswählen.

## manifest.json

```json
{
  "format": 1,
  "id": "mein-tier",
  "name": "Mein Tier",
  "base": "cat",
  "sheet": "sheet.png",
  "cell": [60, 60],
  "columns": 16,
  "density": 3,
  "frames": {
    "idle":  [[0, 0]],
    "stand": [[4, 0]],
    "walk":  [[13, 0], [14, 0], [15, 0], [0, 1]]
  }
}
```

| Feld | Regel |
|---|---|
| `format` | `1` |
| `id` | `a-z`, `0-9`, `-`, max. 32 Zeichen; Ordnername der Installation |
| `name` | 1–40 Zeichen, Anzeige in den Einstellungen |
| `base` | Verhalten/Laute: `cat`, `dog`, `fox`, `rabbit`, `dragon`, `bird` (Vogel/Drache fliegen) |
| `cell` | Zellgröße `[breite, höhe]` in Pixeln, je 8–256 |
| `density` | Pixel pro TinyPaws-Einheit; das Tier ist 16 Einheiten groß → bei 48-px-Tieren `3`, bei 16-px-Tieren `1`. Muss `cell` teilen |
| `frames` | Name → Liste von Zellen `[spalte, zeile]` (0-basiert). Animationen = mehrere Zellen |

**Pflicht:** `idle`, `stand`, `walk`.

**Einzelbilder** (erste Zelle zählt): `idle` (sitzt, schaut nach vorn), `blink`, `happy`, `surprised`,
`stand` (steht seitlich, schaut nach rechts), `stand_blink`, `jump`, `sit`, `stretch`, `sleep`,
`lounge` (liegt auf einer Fensterkante, Pfoten hängen über), `flex` (GigaChad), `cinema` (Pfoten hoch).

**Animationen** (beliebig viele Zellen, werden auf die benötigte Länge gestreckt):
`walk`, `run` (Galopp/Flug), `sneak` (Anschleichen).

Fehlende Bilder werden ersetzt (z. B. `blink` → `idle`, `run` → `walk`, `lounge` → `sleep`).

Seitliche Bilder schauen **nach rechts**; TinyPaws spiegelt sie selbst. Das Tier steht unten mittig in
seiner Zelle.

## Grenzen (Sicherheit)

ZIP max. 8 MB, jede Datei entpackt max. 16 MB, Bild max. 4096×4096 px, max. 250 Farben,
max. 64 Zellen pro Animation. Pixel mit Deckkraft < 50 % sind transparent.
Ungültige Pakete werden mit einer Fehlermeldung abgewiesen; kaputte installierte Pakete werden beim
Start übersprungen.

Installiert wird nach `~/.config/tinypaws/packs/<id>/`.
