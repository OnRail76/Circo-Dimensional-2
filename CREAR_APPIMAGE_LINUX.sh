#!/usr/bin/env bash
set -euo pipefail
AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$AQUI/tools/crear_appimage_linux.sh" "$@"
