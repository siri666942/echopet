param(
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendRoot = Join-Path $RepoRoot "DyberPet-main"
$VenvPath = Join-Path $FrontendRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    py -3.11 -m venv $VenvPath
}

$PipPath = Join-Path $VenvPath "Scripts\pip.exe"
if (-not (Test-Path $PipPath)) {
    & $PythonPath -m ensurepip --upgrade
}

if ($InstallDeps) {
    & $PythonPath -m pip install `
        PySide6 `
        PySide6-Fluent-Widgets `
        PySideSix-Frameless-Window `
        pynput `
        tendo `
        pillow `
        psutil `
        numpy `
        apscheduler
}

Push-Location $FrontendRoot
try {
    & $PythonPath "run_DyberPet.py"
}
finally {
    Pop-Location
}
