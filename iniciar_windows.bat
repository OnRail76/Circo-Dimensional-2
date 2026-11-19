@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_BIN=py -3"
) else (
    set "PYTHON_BIN=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo Preparando entorno virtual de Circo Dimensional 2...
    %PYTHON_BIN% -m venv .venv
    if errorlevel 1 goto fail
)

".venv\Scripts\python.exe" -c "import pygame; from importlib.metadata import version; assert version('pygame-ce') == '2.5.8'" >nul 2>&1
if errorlevel 1 (
    echo Instalando Pygame Community Edition sin compilar codigo fuente...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --only-binary=:all: -r requirements.txt
    if errorlevel 1 goto fail
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
exit /b 0

:fail
echo ERROR: No ha sido posible configurar el juego.
echo Comprueba que tienes Python 3.10 o posterior y conexion a Internet.
pause
exit /b 1
