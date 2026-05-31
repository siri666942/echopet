docker compose logs --tail 100 echopet-backend$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"

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

    Write-Step "Stopping Docker backend..."
    docker compose stop echopet-backend
    Write-Step "Stopped."
}
finally {
    Pop-Location
}
