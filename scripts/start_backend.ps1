param(
    [switch]$InstallDeps,
    [switch]$Background,
    [switch]$NoReload,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$VenvPath = Join-Path $RepoRoot "backend\.venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"
$BackendRequirements = Join-Path $RepoRoot "backend\requirements.txt"
$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$MpvPaths = @(
    "C:\Users\thyss\tools\mpv-dev",
    "C:\Users\thyss\tools\mpv"
)

function Write-Step([string]$Message) {
    Write-Host "[EchoPet] $Message"
}

function Ensure-BackendVenv {
    if (-not (Test-Path $PythonPath)) {
        Write-Step "Creating backend venv..."
        py -3.11 -m venv $VenvPath
    }

    $pipPath = Join-Path $VenvPath "Scripts\pip.exe"
    if (-not (Test-Path $pipPath)) {
        & $PythonPath -m ensurepip --upgrade
    }
}

function Test-BackendDepsReady {
    if (-not (Test-Path $PythonPath)) {
        return $false
    }

    & $PythonPath -c "import fastapi, pydantic_settings, pytest, faster_whisper" *> $null
    return ($LASTEXITCODE -eq 0)
}

function Install-BackendDeps {
    Write-Step "Installing backend dependencies..."
    & $PythonPath -m pip install -r $BackendRequirements
}

function Stop-OldBackend {
    $staleBackends = Get-CimInstance Win32_Process | Where-Object {
        (($_.Name -match "python") -or ($_.Name -match "uvicorn")) -and $_.CommandLine -like "*backend.main:app*"
    }
    foreach ($proc in $staleBackends) {
        Write-Step "Stopping stale backend process pid=$($proc.ProcessId)..."
        Stop-Process -Id $proc.ProcessId -Force
    }

    if (-not (Test-Path $BackendPidFile)) {
        return
    }

    $pidText = (Get-Content $BackendPidFile -Raw).Trim()
    if (-not $pidText) {
        Remove-Item -LiteralPath $BackendPidFile -Force
        return
    }

    $oldProcess = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
    if ($oldProcess) {
        Write-Step "Stopping previous backend process pid=$pidText..."
        Stop-Process -Id ([int]$pidText) -Force
    }
    Remove-Item -LiteralPath $BackendPidFile -Force
}

foreach ($path in $MpvPaths) {
    if ($path -and (Test-Path $path)) {
        $env:PATH = "$path;$env:PATH"
    }
}

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
Ensure-BackendVenv
if ($InstallDeps -or -not (Test-BackendDepsReady)) {
    Install-BackendDeps
}

Push-Location $RepoRoot
try {
    $arguments = @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$Port")
    if (-not $NoReload -and -not $Background) {
        $arguments += "--reload"
    }

    if ($Background) {
        Stop-OldBackend
        $process = Start-Process `
            -FilePath $PythonPath `
            -ArgumentList $arguments `
            -WorkingDirectory $RepoRoot `
            -PassThru
        Set-Content -LiteralPath $BackendPidFile -Value $process.Id -Encoding ASCII
        Write-Step "Backend started pid=$($process.Id) at http://127.0.0.1:$Port"
    }
    else {
        & $PythonPath @arguments
    }
}
finally {
    Pop-Location
}
