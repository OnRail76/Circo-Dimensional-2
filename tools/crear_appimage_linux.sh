#!/usr/bin/env bash
# Construye un AppImage x86_64 real y autocontenido con el pulpo normal.
# Ejecución: ./tools/crear_appimage_linux.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
ROOT="$PWD"
VERSION="$(python3 -c 'from circo.config import VERSION; print(VERSION)')"
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "ERROR: este script está preparado para Linux x86_64" >&2
  exit 1
fi
command -v curl >/dev/null || { echo 'Necesitas curl'; exit 1; }
command -v python3 >/dev/null || { echo 'Necesitas python3'; exit 1; }

VENV="$ROOT/.build/linux/venv"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install --only-binary=:all: -r requirements.txt 'pyinstaller>=6,<7'
"$VENV/bin/python" -m PyInstaller --noconfirm --clean --onedir \
  --name CircoDimensional2 --collect-all pygame \
  --add-data "assets:assets" main.py

APPDIR="$ROOT/.build/linux/CircoDimensional2.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/bin" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp -a "$ROOT/dist/CircoDimensional2" "$APPDIR/usr/lib/"
cat > "$APPDIR/usr/bin/circo-dimensional-2" <<'BINRUN'
#!/bin/sh
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
exec "$HERE/usr/lib/CircoDimensional2/CircoDimensional2" "$@"
BINRUN
chmod +x "$APPDIR/usr/bin/circo-dimensional-2"
cp assets/icons/pulpo_normal_256.png "$APPDIR/circo-dimensional-2.png"
cp assets/icons/pulpo_normal_256.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/circo-dimensional-2.png"
cat > "$APPDIR/circo-dimensional-2.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Circo Dimensional 2
Comment=Dom y los pulpos rebotadores — Tony C. Ware
Exec=circo-dimensional-2
Icon=circo-dimensional-2
Categories=Game;ArcadeGame;
Terminal=false
StartupNotify=true
DESKTOP
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$HERE/usr/bin/circo-dimensional-2" "$@"
APPRUN
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/lib/CircoDimensional2/CircoDimensional2"

# Etapa 2: terminar desde AppDir. Reutilizable sin reconstruir PyInstaller.
exec bash "$ROOT/tools/finalizar_appimage_linux.sh"
