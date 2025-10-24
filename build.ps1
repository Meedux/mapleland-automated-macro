<#
PowerShell build script for MapleLand Bot

What it does:
- Creates a virtual environment (optional)
- Installs dependencies from requirements.txt
- Pre-downloads EasyOCR models into `easyocr_models` (so they can be bundled)
- Runs PyInstaller to create a one-folder distributable

Usage (PowerShell):
    .\build.ps1 [-Clean] [-OneFile]

Notes:
- Prefer one-dir (--onedir) for reliability with EasyOCR/PyTorch.
- If you want a single EXE, pass -OneFile, but startup may be much slower and larger.
#>
param(
    [switch]$Clean,
    [switch]$OneFile
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvDir = "$root\.venv"
$python = "$venvDir\Scripts\python.exe"
$pip = "$venvDir\Scripts\pip.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating virtualenv at $venvDir"
    python -m venv $venvDir
}

Write-Host "Installing requirements"
& $pip install --upgrade pip
if (Test-Path "$root\requirements.txt") {
    & $pip install -r "$root\requirements.txt"
} else {
    Write-Host "No requirements.txt found. Please create one with project's dependencies." -ForegroundColor Yellow
}

# Pre-download EasyOCR models into easyocr_models folder
$easyocr_models_dir = Join-Path $root 'easyocr_models'
if (-not (Test-Path $easyocr_models_dir)) {
    New-Item -ItemType Directory -Path $easyocr_models_dir | Out-Null
}

Write-Host "Pre-downloading EasyOCR models into $easyocr_models_dir"
$downloadScript = @"
import easyocr, os
model_dir = r'''$easyocr_models_dir'''
try:
    r = easyocr.Reader(['en'], gpu=False, model_storage_directory=model_dir)
    print('EasyOCR models ready in', model_dir)
except Exception as e:
    print('EasyOCR model download/initialization failed:', e)
"@

$downloadScriptFile = Join-Path $env:TEMP 'easyocr_download.py'
Set-Content -Path $downloadScriptFile -Value $downloadScript -Encoding UTF8
& $python $downloadScriptFile

# Prepare PyInstaller command
$distName = 'MaplelandBot'
$addData = @(
    "assets;assets",
    "config;config",
    "easyocr_models;easyocr_models"
)

$addDataArgs = $addData | ForEach-Object { "--add-data `"$_`"" } | Out-String
$pyinstallerExe = Join-Path $venvDir 'Scripts\pyinstaller.exe'
if (-not (Test-Path $pyinstallerExe)) {
    Write-Host "PyInstaller not found in venv, installing..."
    & $pip install pyinstaller
}

if ($Clean) {
    Write-Host "Cleaning previous build/dist/spec files"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$root\build","$root\dist","$root\$distName.spec","$root\dist\$distName"  
}

$modeFlag = if ($OneFile) { '--onefile' } else { '--onedir' }
$windowed = '--windowed'

Write-Host "Running PyInstaller (this may take a while)..."
$pyCmd = "& `"$pyinstallerExe`" --noconfirm --clean $modeFlag $windowed $addDataArgs --hidden-import easyocr --hidden-import PIL --hidden-import cv2 --hidden-import numpy --name `$distName` main.py"
Invoke-Expression $pyCmd

Write-Host "Build finished. Check the 'dist' folder for output."