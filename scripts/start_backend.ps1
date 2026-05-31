param(
    [switch]$InstallDeps,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $RepoRoot "backend\.venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"
$MpvPaths = @(
    "C:\Users\thyss\tools\mpv-dev",
    "C:\Users\thyss\tools\mpv"
)

foreach ($path in $MpvPaths) {
    if ($path -and (Test-Path $path)) {
        $env:PATH = "$path;$env:PATH"
    }
}

if (-not (Test-Path $PythonPath)) {
    py -3.11 -m venv $VenvPath
}

$PipPath = Join-Path $VenvPath "Scripts\pip.exe"
if (-not (Test-Path $PipPath)) {
    & $PythonPath -m ensurepip --upgrade
}

if ($InstallDeps) {
    & $PythonPath -m pip install `
        fastapi==0.115.0 `
        "uvicorn[standard]==0.30.6" `
        sqlalchemy==2.0.35 `
        pydantic==2.9.2 `
        pydantic-settings==2.5.2 `
        httpx==0.27.2 `
        psutil==6.0.0 `
        pywin32==306 `
        openai==1.50.2 `
        python-multipart==0.0.12 `
        python-mpv==1.0.7 `
        numpy==1.26.4
}

Push-Location $RepoRoot
try {
    & $PythonPath -m uvicorn backend.main:app --reload --host 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}
