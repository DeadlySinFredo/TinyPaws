"""Pixel-art sprites as character grids. Pure data, no Qt. '.' = transparent.

Each sprite is a list of equal-length strings; each char maps to PALETTE.
Pets come from cat32, props from props48; both are 48-raster grids at density 3.
"""
from .cat32 import BREEDS, DENSITY as PET_DENSITY, EXTRA_PALETTE, FRAMES, skin  # noqa: F401 (re-exported)
from .props48 import COLORS as PROP_COLORS, PROPS

PALETTE = {
    'K': '#14111c', 'O': '#33303f', 'D': '#211e2b', 'L': '#f6f2ea', 'P': '#ff8fa3',
    'E': '#1b1b1b', 'W': '#ffffff', 'N': '#26262e', 'S': '#8a8a96', 'R': '#d93a3a',
    'r': '#9c2424', 'Y': '#ffd23f', 'B': '#3a6fd9', 'b': '#25479c', 'G': '#3fbf5f',
    'M': '#7a4a24', 'C': '#fff7e0', 'T': '#2ec4b6', 'H': '#4d4960', 'g': '#5cc24a',
    'A': '#c98b4f', 'a': '#9b6334', 'h': '#e2ab6f', 'c': '#fbf3e4',
}


SPRITES = dict(PROPS)
SPRITES.update(FRAMES)
PALETTE.update(EXTRA_PALETTE)
PALETTE.update(PROP_COLORS)
# pixels per logical unit; the brain lays out in logical units, the renderer draws at scale/density
DENSITY = {k: PET_DENSITY for k in SPRITES}
SIZES = {k: (len(v[0]) // DENSITY.get(k, 1), len(v) // DENSITY.get(k, 1)) for k, v in SPRITES.items()}
