#!/usr/bin/env bash
# Circo Dimensional 2 — publicación segura sobre repositorio recién creado.
# Admite que GitHub haya creado una LICENSE inicial. No fuerza historial.
# Uso: bash PUBLICAR_EN_GITHUB.sh OnRail76/Circo-Dimensional-2
set -Eeuo pipefail
IFS=$'\n\t'

SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-OnRail76/Circo-Dimensional-2}"
if [[ ! "$TARGET" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
    echo "ERROR: indica usuario/repositorio (ej. OnRail76/Circo-Dimensional-2)." >&2
    exit 2
fi

for cmd in git sha256sum tar; do
    command -v "$cmd" >/dev/null || { echo "ERROR: falta $cmd" >&2; exit 2; }
done
for required in main.py circo/config.py README.md LICENSE HISTORIA_ORIGINAL.txt \
    docs/ATLAS_VISUAL_Y_MEMORIA_CIRCO_DIMENSIONAL_2_v1.0.0.pdf \
    docs/MANUAL_ILUSTRADO_CIRCO_DIMENSIONAL_2_v1.0.0.pdf \
    assets/cover/caratula_oficial.png .github/workflows/tests.yml; do
    [[ -f "$SOURCE/$required" ]] || { echo "ERROR: archivo ausente: $required" >&2; exit 2; }
done

printf '\n[1/5] Comprobando integridad del paquete...\n'
(cd "$SOURCE" && sha256sum -c SHA256SUMS.txt >/dev/null) || {
    echo "ERROR: el manifiesto SHA-256 no coincide con el paquete." >&2
    exit 2
}

URL="${CD2_GIT_REMOTE:-https://github.com/${TARGET}.git}"
TEMP="$(mktemp -d "${TMPDIR:-/tmp}/cd2-publicar.XXXXXXXX")"
trap 'rm -rf -- "$TEMP"' EXIT
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    gh auth setup-git >/dev/null 2>&1 || true
fi

printf '[2/5] Conectando con %s...\n' "$TARGET"
if ! git clone --quiet "$URL" "$TEMP/repo"; then
    echo 'ERROR: no se pudo clonar. Comprueba la conexión y tus permisos de GitHub.' >&2
    exit 3
fi
if [[ "$(git -C "$TEMP/repo" branch --show-current)" != "main" ]]; then
    echo 'ERROR: la rama por defecto no es main; no se ha modificado nada.' >&2
    exit 3
fi
# Se acepta un repositorio totalmente nuevo o uno creado con solo LICENSE.
# No se pisa contenido de un proyecto ya existente.
mapfile -t existing < <(git -C "$TEMP/repo" ls-files)
for file in "${existing[@]}"; do
    if [[ "$file" != 'LICENSE' ]]; then
        echo "ERROR: el repositorio ya contiene $file; se cancela para protegerlo." >&2
        exit 3
    fi
done

printf '[3/5] Añadiendo juego, fuentes, documentación y recursos...\n'
# Importar todo salvo los archivos que Git ignora; no eliminar el historial remoto.
tar -C "$SOURCE" --exclude='./.git' --exclude='./.venv' --exclude='./__pycache__' \
    --exclude='./.pytest_cache' -cf - . | tar -C "$TEMP/repo" -xf -
git -C "$TEMP/repo" add --all
COUNT="$(git -C "$TEMP/repo" ls-files | wc -l | tr -d ' ')"
if (( COUNT < 130 )); then
    echo "ERROR: solo $COUNT archivos preparados; se esperaba al menos 130." >&2
    exit 4
fi
if git -C "$TEMP/repo" diff --cached --quiet; then
    echo 'No hay archivos nuevos para publicar; quizá ya se publicó.'
    exit 0
fi

printf '[4/5] Creando commit con %s archivos...\n' "$COUNT"
if ! git -C "$TEMP/repo" var GIT_AUTHOR_IDENT >/dev/null 2>&1; then
    echo 'ERROR: configura git user.name y user.email antes de publicar.' >&2
    exit 4
fi
git -C "$TEMP/repo" commit --quiet -m 'Publicar Circo Dimensional 2 v1.0.0 - juego, fuentes, manual y atlas corregido'
SHA="$(git -C "$TEMP/repo" rev-parse HEAD)"

printf '[5/5] Subiendo a main (sin --force)...\n'
if ! git -C "$TEMP/repo" push origin HEAD:main; then
    echo 'ERROR: GitHub ha rechazado el push. No se han forzado cambios remotos.' >&2
    echo 'Si falta autenticación, ejecuta: gh auth login && gh auth setup-git' >&2
    exit 5
fi
printf '\n¡PUBLICACIÓN COMPLETA!\n'
printf 'Repositorio: https://github.com/%s\n' "$TARGET"
printf 'Commit: https://github.com/%s/commit/%s\n' "$TARGET" "$SHA"
printf 'Archivos versionados: %s\n' "$COUNT"
printf 'Pruebas CI: https://github.com/%s/actions\n' "$TARGET"
printf 'Para la Release, comprueba Actions y utiliza RELEASE_NOTES.md.\n'
