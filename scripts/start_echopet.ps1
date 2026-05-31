param(
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

$BackendScript = Join-Path $PSScriptRoot "start_backend.ps1"
$FrontendScript = Join-Path $PSScriptRoot "start_frontend.ps1"

$backendArgs = @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", $BackendScript
)

if ($InstallDeps) {
    $backendArgs += "-InstallDeps"
}

Start-Process powershell -ArgumentList $backendArgs | Out-Null
Start-Sleep -Seconds 3

if ($InstallDeps) {
    & $FrontendScript -InstallDeps
}
else {
    & $FrontendScript
}
