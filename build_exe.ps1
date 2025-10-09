<#
build_exe.ps1

Creates a one-file Windows executable for the project using PyInstaller.
This script creates/uses a local build virtual environment at .build_env so it doesn't pollute your global Python.

Usage:
  # run with normal privileges (may need ExecutionPolicy Bypass):
  PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1

  # skip installing requirements/pyinstaller (faster if already installed in .build_env):
  PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1 -NoInstall

Notes:
 - The resulting exe will be at .\dist\MTG-Collection-Manager.exe
 - The script will include the local `data` folder in the exe bundle so runtime data is available.
 - If your application needs other data folders or non-Python files, add more --add-data entries below.
#>
<# build_exe.ps1 - simplified safe build script
Creates a one-file Windows exe using PyInstaller in an isolated .build_env venv.
Usage: PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1 [-NoInstall]
#>

param(
    [switch]$NoInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Push-Location $root

function info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function err($m)  { Write-Host "[ERROR] $m" -ForegroundColor Red }

# find python (prefer py launcher)
$pythonCmd = $null
$pythonArgs = ''
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = 'py'
    $pythonArgs = '-3'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = 'python'
    $pythonArgs = ''
}
if (-not $pythonCmd) { err 'No Python found (py or python). Install Python 3.'; exit 1 }

$venv = Join-Path $root '.build_env'
if (-not (Test-Path $venv)) {
    info "Creating venv at $venv"
    if ($pythonArgs -ne '') { & $pythonCmd $pythonArgs -m venv $venv } else { & $pythonCmd -m venv $venv }
    if ($LASTEXITCODE -ne 0) { err 'Failed creating venv'; exit 1 }
} else { info "Using existing venv at $venv" }

$pyexe = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $pyexe)) { err "Expected python at $pyexe"; exit 1 }

if (-not $NoInstall) {
    info 'Upgrading pip and installing build deps'
    & $pyexe -m pip install --upgrade pip setuptools wheel
    if (Test-Path (Join-Path $root 'requirements.txt')) {
        info 'Installing project requirements'
        & $pyexe -m pip install -r (Join-Path $root 'requirements.txt')
    } else { warn 'No requirements.txt found, skipping project deps' }
    info 'Installing PyInstaller'
    & $pyexe -m pip install pyinstaller
}

$exeName = 'MTG-Collection-Manager'
$spec = @('--noconfirm','--onefile','--console','--name',$exeName)
if (Test-Path (Join-Path $root 'data')) { $spec += '--add-data'; $spec += 'data;data' }
$spec += 'run.py'

info 'Running PyInstaller (this can take a minute)'
& $pyexe -m PyInstaller @spec

$target = Join-Path $root ("dist\$exeName.exe")
if (Test-Path $target) { info "Build complete: $target"; exit 0 } else { err 'Build failed; check output above and build folder'; exit 2 }

Pop-Location

