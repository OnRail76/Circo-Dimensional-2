#!/bin/sh
# Circo Dimensional 2: entorno aislado para no alterar Python del sistema.
set -eu
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: No se encuentra $PYTHON_BIN. Instala Python 3.10 o superior."
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Preparando entorno virtual de Circo Dimensional 2..."
  if ! "$PYTHON_BIN" -m venv .venv; then
    echo "ERROR: No se pudo crear .venv. Comprueba que tu Python tiene el modulo venv."
    echo "En Debian/Ubuntu puede ser necesario instalar python3-venv."
    exit 1
  fi
fi

if ! .venv/bin/python -c 'import pygame; from importlib.metadata import version; assert version("pygame-ce") == "2.5.8"' >/dev/null 2>&1; then
  echo "Instalando Pygame Community Edition (sin compilar desde fuentes)..."
  if ! .venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: -r requirements.txt; then
    echo "ERROR: No se pudo instalar Pygame CE. Comprueba la conexion y la arquitectura de Python."
    echo "Reintenta con ./iniciar_linux.sh; si falla, envia el nuevo error."
    exit 1
  fi
fi

exec .venv/bin/python main.py
