#!/usr/bin/env bash
# Finaliza el AppImage desde el AppDir creado por PyInstaller, SIN recompilar.
# Si la herramienta de empaquetado no está instalada, descarga el binario oficial.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT=""
for guess in \
  "$SCRIPT_DIR/Circo_Dimensional_2_Pygame" \
  "$SCRIPT_DIR" \
  "$(pwd)/Circo_Dimensional_2_Pygame" \
  "$(pwd)"; do
  if [[ -f "$guess/circo/config.py" && -d "$guess/.build/linux/CircoDimensional2.AppDir" ]]; then
    PROJECT="$(cd "$guess" && pwd)"
    break
  fi
done

if [[ -z "$PROJECT" ]]; then
  echo 'ERROR: No encuentro el AppDir ya generado por PyInstaller.' >&2
  echo 'Sitúate en la carpeta en la que descomprimiste CIRCO DIMENSIONAL 2,' >&2
  echo 'la misma desde la que lanzaste CREAR_APPIMAGE_LINUX.sh, y repite.' >&2
  echo 'Si borraste .build/, ejecuta el creador completo de AppImage.' >&2
  exit 1
fi

if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  echo 'ERROR: el empaquetado de este juego está preparado para Linux x86_64.' >&2
  exit 1
fi

ROOT="$PROJECT"
APPDIR="$ROOT/.build/linux/CircoDimensional2.AppDir"
if [[ ! -x "$APPDIR/AppRun" || ! -f "$APPDIR/circo-dimensional-2.desktop" ]]; then
  echo "ERROR: AppDir incompleto en $APPDIR" >&2
  exit 1
fi
if [[ ! -e "$APPDIR/.DirIcon" ]]; then
  ln -s circo-dimensional-2.png "$APPDIR/.DirIcon"
fi

VERSION="$(cd "$ROOT" && python3 -c 'from circo.config import VERSION; print(VERSION)')"
mkdir -p "$ROOT/.build/linux" "$ROOT/dist"
OUTPUT="$ROOT/dist/Circo_Dimensional_2_v${VERSION}_x86_64.AppImage"
TOOL="${APPIMAGETOOL:-$ROOT/.build/linux/appimagetool-x86_64.AppImage}"

if [[ ! -s "$TOOL" ]]; then
  if [[ -n "${APPIMAGETOOL:-}" ]]; then
    echo "ERROR: APPIMAGETOOL no existe o está vacío: $TOOL" >&2
    exit 1
  fi
  command -v curl >/dev/null || { echo 'ERROR: necesitas curl'; exit 1; }
  tmp="${TOOL}.part"
  trap 'rm -f "$tmp"' EXIT
  echo 'Descargando appimagetool oficial (nombre correcto: .AppImage)...'
  if ! curl -fL --retry 2 --connect-timeout 20 --max-time 180 \
       -o "$tmp" 'https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage'; then
    echo 'Error descargando appimagetool. Puedes obtenerlo desde:' >&2
    echo 'https://github.com/AppImage/appimagetool/releases/tag/1.9.1' >&2
    echo 'y ejecutar de nuevo el script.' >&2
    exit 1
  fi
  if [[ ! -s "$tmp" ]]; then
    echo 'ERROR: la descarga de appimagetool está vacía.' >&2
    exit 1
  fi
  mv "$tmp" "$TOOL"
  trap - EXIT
fi
chmod +x "$TOOL"

echo "Creando AppImage a partir del AppDir existente: $APPDIR"
# Evita la dependencia de FUSE para EJECUTAR la herramienta, útil en Bazzite.
# El AppImage final se inicia normalmente; APPIMAGE_EXTRACT_AND_RUN=1 es una
# alternativa de ejecución cuando FUSE no está disponible en el equipo destino.
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" "$APPDIR" "$OUTPUT"
if [[ ! -s "$OUTPUT" ]]; then
  echo "ERROR: la herramienta no generó un AppImage: $OUTPUT" >&2
  exit 1
fi
chmod +x "$OUTPUT"
echo "¡LISTO! AppImage: $OUTPUT"
echo "Para ejecutarlo: '$OUTPUT'"
echo 'Si Bazzite informa de FUSE: APPIMAGE_EXTRACT_AND_RUN=1 "<ruta>.AppImage"'
