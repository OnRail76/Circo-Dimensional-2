# Construye un EXE completo y autónomo en Windows x64.
# Abre PowerShell en la carpeta del juego y ejecuta:
# powershell -ExecutionPolicy Bypass -File tools/crear_exe_windows.ps1
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
$Venv = Join-Path $Root '.build\windows\venv'
python -m venv "$Venv"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual con Python.' }
$Python = Join-Path $Venv 'Scripts\python.exe'
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar pip.' }
& $Python -m pip install --only-binary=:all: -r requirements.txt 'pyinstaller>=6,<7'
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name CircoDimensional2 `
    --icon 'assets\icons\pulpo_normal.ico' `
    --collect-all pygame `
    --add-data 'assets;assets' main.py
if ($LASTEXITCODE -ne 0) { throw 'La compilación del EXE ha fallado.' }
Write-Host "Ejecutable listo: $Root\dist\CircoDimensional2.exe"
