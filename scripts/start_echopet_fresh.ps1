$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$FrontendRoot = Join-Path $RepoRoot "DyberPet-main"
$FrontendPython = Join-Path $FrontendRoot ".venv\Scripts\python.exe"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"
$BackendPort = 8001
$BackendUrl = "http://127.0.0.1:$BackendPort"

function Write-Step([string]$Message) {
    Write-Host "[EchoPet] $Message"
}

function Stop-StaleProcesses {
    $frontendTargets = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -match "python") -and $_.CommandLine -like "*run_DyberPet.py*"
    }
    $backendTargets = Get-CimInstance Win32_Process | Where-Object {
        (($_.Name -match "python") -or ($_.Name -match "uvicorn")) -and $_.CommandLine -like "*backend.main:app*"
    }

    $allTargets = @($frontendTargets) + @($backendTargets) | Sort-Object ProcessId -Unique
    foreach ($proc in $allTargets) {
        Write-Step "Stopping stale process pid=$($proc.ProcessId)..."
        Stop-Process -Id $proc.ProcessId -Force
    }

    Remove-Item -LiteralPath $FrontendPidFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $RuntimeDir "backend.pid") -Force -ErrorAction SilentlyContinue
}

function Wait-BackendReady {
    $url = "$BackendUrl/api/context"
    for ($i = 0; $i -lt 30; $i++) {
        try {
            Invoke-RestMethod -Uri $url -TimeoutSec 2 | Out-Null
            return
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    throw "Backend did not become ready at $url"
}

function Start-FrontendSingle {
    if (-not (Test-Path $FrontendPython)) {
        throw "Frontend venv not found: $FrontendPython"
    }

    $env:ECHOPET_BACKEND_URL = $BackendUrl
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
    Stop-StaleProcesses

    Write-Step "Starting backend..."
    & powershell -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\start_backend.ps1") -Background -Port $BackendPort
    Wait-BackendReady
    Write-Step "Backend is ready at $BackendUrl."

    Write-Step "Starting single frontend..."
    Start-FrontendSingle

    Write-Step "All set."
}
finally {
    Pop-Location
}
