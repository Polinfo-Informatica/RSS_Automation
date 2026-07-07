param(
    [switch] $Force
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonPath = Join-Path $ProjectRoot "env\Scripts\python.exe"
$RuntimeScript = Join-Path $ProjectRoot "RSS_Automation.py"

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment executable not found: $PythonPath"
}

if (-not (Test-Path $RuntimeScript)) {
    throw "RSS automation launcher not found: $RuntimeScript"
}

$arguments = @($RuntimeScript, "--backup-config-only")
if ($Force) {
    $arguments += "--force-config-backup"
}

Write-Host "Starting RSS config backup."
Write-Host "Project root: $ProjectRoot"
Write-Host "Force: $Force"

Push-Location $ProjectRoot
try {
    & $PythonPath @arguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "RSS config backup failed with exit code $exitCode"
    }
}
finally {
    Pop-Location
}

Write-Host "RSS config backup completed successfully."
