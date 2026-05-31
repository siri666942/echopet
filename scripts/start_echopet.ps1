param(
    [switch]$Build,
    [switch]$LocalBackend,
    [switch]$InstallBackendDeps,
    [switch]$InstallFrontendDeps,
    [switch]$ForceReindex,
    [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$FrontendRoot = Join-Path $RepoRoot "DyberPet-main"
$FrontendVenv = Join-Path $FrontendRoot ".venv"
$FrontendPython = Join-Path $FrontendVenv "Scripts\python.exe"
$FrontendRequirements = Join-Path $FrontendRoot "requirements.txt"
$BackendPython = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"
$MusicDir = Join-Path $RepoRoot "backend\music"
$MusicManifestFile = Join-Path $RuntimeDir "music_manifest.sha256"
$WhisperModelDir = Join-Path $RepoRoot "backend\models\faster-whisper"
$HuggingFaceCacheDir = Join-Path $RepoRoot "backend\models\huggingface"

function Write-Step([string]$Message) {
    Write-Host "[EchoPet] $Message"
}

function Ensure-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name not found. $Hint"
    }
}

function Wait-Backend([int]$Port) {
    $url = "http://127.0.0.1:$Port/"
    for ($i = 0; $i -lt 60; $i++) {
        try {
            Invoke-RestMethod -Uri $url -TimeoutSec 2 | Out-Null
            return
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "Backend did not become ready at $url"
}

function Get-MusicSignature {
    if (-not (Test-Path $MusicDir)) {
        New-Item -ItemType Directory -Path $MusicDir | Out-Null
    }

    $files = Get-ChildItem -LiteralPath $MusicDir -Recurse -File -Include *.mp3, *.wav, *.flac |
        Sort-Object FullName

    if (-not $files) {
        return ""
    }

    $lines = foreach ($file in $files) {
        $relative = $file.FullName.Substring($MusicDir.Length).TrimStart("\", "/")
        "$relative|$($file.Length)|$($file.LastWriteTimeUtc.Ticks)"
    }
    $raw = [string]::Join("`n", $lines)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([BitConverter]::ToString($hash) -replace "-", "")
}

function Sync-MusicIndex {
    $signature = Get-MusicSignature
    if (-not $signature) {
        Write-Step "No local music files found, skipping reindex."
        return
    }

    $previous = ""
    if (Test-Path $MusicManifestFile) {
        $previous = (Get-Content $MusicManifestFile -Raw).Trim()
    }

    if ($ForceReindex -or $signature -ne $previous) {
        Write-Step "Music library changed, running backend reindex..."
        if ($LocalBackend) {
            & $BackendPython -m backend.scripts.reindex_music
        }
        else {
            docker compose exec -T echopet-backend python -m backend.scripts.reindex_music
        }
        Set-Content -LiteralPath $MusicManifestFile -Value $signature -Encoding ASCII
    }
    else {
        Write-Step "Music library unchanged, skipping reindex."
    }
}

function Ensure-WhisperModel {
    Write-Step "Preparing faster-whisper model..."
    New-Item -ItemType Directory -Path $WhisperModelDir -Force | Out-Null
    New-Item -ItemType Directory -Path $HuggingFaceCacheDir -Force | Out-Null

    $previousWhisperModelDir = $env:WHISPER_MODEL_DIR
    $previousHfHome = $env:HF_HOME
    $previousHfCache = $env:HUGGINGFACE_HUB_CACHE
    try {
        $env:WHISPER_MODEL_DIR = $WhisperModelDir
        $env:HF_HOME = $HuggingFaceCacheDir
        $env:HUGGINGFACE_HUB_CACHE = Join-Path $HuggingFaceCacheDir "hub"
        if ($LocalBackend) {
            & $BackendPython -m backend.scripts.download_whisper_model
        }
        else {
            docker compose exec -T echopet-backend python -m backend.scripts.download_whisper_model
        }
    }
    finally {
        $env:WHISPER_MODEL_DIR = $previousWhisperModelDir
        $env:HF_HOME = $previousHfHome
        $env:HUGGINGFACE_HUB_CACHE = $previousHfCache
    }
}

function Start-Backend {
    if ($LocalBackend) {
        Write-Step "Starting local backend..."
        $backendArgs = @(
            "-ExecutionPolicy", "Bypass",
            "-File", (Join-Path $RepoRoot "scripts\start_backend.ps1"),
            "-Background",
            "-Port", "$BackendPort"
        )
        if ($InstallBackendDeps) {
            $backendArgs += "-InstallDeps"
        }
        Start-Process `
            -FilePath "powershell" `
            -ArgumentList $backendArgs `
            -WorkingDirectory $RepoRoot `
            -WindowStyle Hidden `
            -Wait
        return
    }

    Ensure-Command "docker" "Install/open Docker Desktop first."
    if ($Build) {
        Write-Step "Starting backend with docker compose build..."
        docker compose up -d --build
    }
    else {
        Write-Step "Starting backend with docker compose..."
        docker compose up -d
    }
}

function Ensure-FrontendVenv {
    if (-not (Test-Path $FrontendPython)) {
        Write-Step "Creating frontend venv..."
        py -3.11 -m venv $FrontendVenv
        $script:InstallFrontendDeps = $true
    }

    if ($InstallFrontendDeps) {
        Write-Step "Installing frontend dependencies..."
        & $FrontendPython -m pip install -r $FrontendRequirements
    }
}

function Stop-OldFrontend {
    if (-not (Test-Path $FrontendPidFile)) {
        return
    }

    $pidText = (Get-Content $FrontendPidFile -Raw).Trim()
    if (-not $pidText) {
        Remove-Item -LiteralPath $FrontendPidFile -Force
        return
    }

    $oldProcess = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
    if ($oldProcess) {
        Write-Step "Stopping previous frontend process pid=$pidText..."
        Stop-Process -Id ([int]$pidText) -Force
    }
    Remove-Item -LiteralPath $FrontendPidFile -Force
}

function Start-Frontend {
    Stop-OldFrontend
    Write-Step "Starting frontend..."
    $process = Start-Process `
        -FilePath $FrontendPython `
        -ArgumentList @("run_DyberPet.py") `
        -WorkingDirectory $FrontendRoot `
        -PassThru
    Set-Content -LiteralPath $FrontendPidFile -Value $process.Id -Encoding ASCII
    Write-Step "Frontend started pid=$($process.Id)."
}

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

Push-Location $RepoRoot
try {
    Start-Backend
    Wait-Backend -Port $BackendPort
    Write-Step "Backend is ready at http://127.0.0.1:$BackendPort"

    Ensure-WhisperModel
    Sync-MusicIndex
    Ensure-FrontendVenv
    Start-Frontend

    Write-Step "All set. Use scripts\stop_echopet.ps1 to stop EchoPet."
}
finally {
    Pop-Location
}
