param(
    [string[]] $TixatiProcessNames = @("tixati")
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonPath = Join-Path $ProjectRoot "env\Scripts\python.exe"
$RuntimeScript = Join-Path $ProjectRoot "RSS_Automation.py"

$runningTixati = @()
foreach ($processName in $TixatiProcessNames) {
    $runningTixati += @(Get-Process -Name $processName -ErrorAction SilentlyContinue)
}

if ($runningTixati.Count -eq 0) {
    Write-Host "Tixati is not running. RSS automation skipped."
    exit 0
}

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment executable not found: $PythonPath"
}

if (-not (Test-Path $RuntimeScript)) {
    throw "RSS automation launcher not found: $RuntimeScript"
}

Write-Host "Tixati is running. Starting RSS automation."
Write-Host "Project root: $ProjectRoot"

Push-Location $ProjectRoot
try {
    & $PythonPath $RuntimeScript
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "RSS automation failed with exit code $exitCode"
    }
}
finally {
    Pop-Location
}

Write-Host "RSS automation completed successfully."
