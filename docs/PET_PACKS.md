# TinyPaws pet packs (format 1)

🇬🇧 English · [🇩🇪 Deutsch (below)](#-tinypaws-tierpakete-format-1-deutsch)

A pet pack is a **ZIP file** with exactly two files that are used:

| File | Content |
|---|---|
| `manifest.json` | Description (see below) |
| `sheet.png` | Sprite sheet: all images in a grid of equally sized cells, transparent background |

Everything else in the ZIP is ignored and **never** extracted. Packs contain no code.

## Quickest way

1. Tray menu → **“Export pet as template…”** – saves your current pet as a pack.
2. Unzip it and repaint `sheet.png` in a pixel editor (Aseprite, LibreSprite, Krita, GIMP). Keep cells and positions.
3. Change `id` and `name` in `manifest.json`, zip both files again.
4. Tray menu → **“Import pet pack…”**, then pick it under “Choose pet”.

## manifest.json

```json
{
  "format": 1,
  "id": "my-pet",
  "name": "My pet",
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

| Field | Rule |
|---|---|
| `format` | `1` |
| `id` | `a-z`, `0-9`, `-`, max. 32 characters; name of the install folder |
| `name` | 1–40 characters, shown in the settings |
| `base` | Behaviour/sounds: `cat`, `dog`, `fox`, `rabbit`, `dragon`, `bird` (bird/dragon fly) |
| `cell` | Cell size `[width, height]` in pixels, each 8–256 |
| `density` | Pixels per TinyPaws unit; the pet is 16 units tall → `3` for 48 px pets, `1` for 16 px pets. Must divide `cell` |
| `frames` | Name → list of cells `[column, row]` (0-based). Animations = several cells |

**Required:** `idle`, `stand`, `walk`.

**Single frames** (the first cell counts): `idle` (sitting, facing the viewer), `blink`, `happy`, `surprised`,
`stand` (standing sideways, facing right), `stand_blink`, `jump`, `sit`, `stretch`, `sleep`,
`lounge` (lying on a window edge, paws hanging over), `flex` (GigaChad), `cinema` (paws up).

**Animations** (any number of cells, stretched to the length needed): `walk`, `run` (gallop/flight), `sneak`.

More cells than 16/12/16 are all used (smoother, same speed); fewer are stretched.
Missing frames are substituted (e.g. `blink` → `idle`, `run` → `walk`, `lounge` → `sleep`).

Side views face **right**; TinyPaws mirrors them itself. The pet stands bottom-centre in its cell.

## Limits (security)

ZIP max. 8 MB, each file max. 16 MB unpacked, image max. 4096×4096 px, max. 250 colours, max. 64 cells per animation.
Pixels with less than 50 % opacity are transparent. Invalid packs are rejected with an error message; broken installed
packs are skipped at start-up.

Installed to `~/.config/tinypaws/packs/<id>/` (Windows: `%APPDATA%\TinyPaws\packs`, macOS: `~/Library/Application Support/TinyPaws/packs`).

---

# 🇩🇪 TinyPaws-Tierpakete (Format 1, Deutsch)

Ein Tierpaket ist eine **ZIP-Datei** mit genau zwei verwendeten Dateien:

| Datei | Inhalt |
|---|---|
| `manifest.json` | Beschreibung (siehe unten) |
| `sheet.png` | Spritesheet: alle Bilder in einem Raster gleich großer Zellen, transparenter Hintergrund |

Alles andere im ZIP wird ignoriert und **nie** entpackt. Pakete enthalten keinen Code.

### Schnellster Weg

1. Tray-Menü → **„Tier als Vorlage exportieren…“** – speichert dein aktuelles Tier als Paket.
2. ZIP entpacken, `sheet.png` in einem Pixel-Programm umzeichnen (Aseprite, LibreSprite, Krita, GIMP).
   Zellen und Positionen beibehalten.
3. In `manifest.json` `id` und `name` ändern, beide Dateien wieder zippen.
4. Tray-Menü → **„Tierpaket importieren…“**, dann unter Einstellungen → Tier auswählen.

### manifest.json

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

Mehr Zellen als 16/12/16 werden komplett genutzt (flüssiger, gleiche Geschwindigkeit), weniger werden gestreckt.
Fehlende Bilder werden ersetzt (z. B. `blink` → `idle`, `run` → `walk`, `lounge` → `sleep`).

Seitliche Bilder schauen **nach rechts**; TinyPaws spiegelt sie selbst. Das Tier steht unten mittig in
seiner Zelle.

### Grenzen (Sicherheit)

ZIP max. 8 MB, jede Datei entpackt max. 16 MB, Bild max. 4096×4096 px, max. 250 Farben,
max. 64 Zellen pro Animation. Pixel mit Deckkraft < 50 % sind transparent.
Ungültige Pakete werden mit einer Fehlermeldung abgewiesen; kaputte installierte Pakete werden beim
Start übersprungen.

Installiert wird nach `~/.config/tinypaws/packs/<id>/` (Windows: `%APPDATA%\TinyPaws\packs`, macOS: `~/Library/Application Support/TinyPaws/packs`).
