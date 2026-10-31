#!/bin/sh
# Installs a TinyPaws menu entry for the current user (Linux). Needs python + PySide6.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
python3 -c "import PySide6" 2>/dev/null || { echo "PySide6 missing: sudo pacman -S pyside6  (or: pip install --user PySide6)"; exit 1; }
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/tinypaws.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=TinyPaws
Comment=Pixel desktop pet
Exec=env PYTHONPATH="$ROOT" python3 -m tinypaws
Icon=$ROOT/tinypaws/icon.png
Categories=Game;Amusement;
DESK
echo "Installed. Start from the app menu or: PYTHONPATH=\"$ROOT\" python3 -m tinypaws --panel"
