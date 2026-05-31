$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"
$BackendPidFile = Join-Path $RuntimeDir "backend.pid"

function Write-Step([string]$Message) {
    Write-Host "[EchoPet] $Message"
}

Push-Location $RepoRoot
try {
    if (Test-Path $FrontendPidFile) {
        $pidText = (Get-Content $FrontendPidFile -Raw).Trim()
        if ($pidText) {
            $frontend = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
            if ($frontend) {
                Write-Step "Stopping frontend pid=$pidText..."
                Stop-Process -Id ([int]$pidText) -Force
            }
        }
        Remove-Item -LiteralPath $FrontendPidFile -Force
    }
    else {
        Write-Step "No frontend pid file found."
    }

    if (Test-Path $BackendPidFile) {
        $pidText = (Get-Content $BackendPidFile -Raw).Trim()
        if ($pidText) {
            $backend = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
            if ($backend) {
                Write-Step "Stopping local backend pid=$pidText..."
                Stop-Process -Id ([int]$pidText) -Force
            }
        }
        Remove-Item -LiteralPath $BackendPidFile -Force
    }
    else {
        Write-Step "No local backend pid file found."
    }

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Step "Stopping Docker backend..."
        docker compose stop echopet-backend
    }
    else {
        Write-Step "Docker not found, skip stopping container backend."
    }
    Write-Step "Stopped."
}
finally {
    Pop-Location
}
