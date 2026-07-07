$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RestoreScript = Join-Path $ProjectRoot "scripts\restore_signed_scripts.ps1"
$SignScript = Join-Path $ProjectRoot "scripts\sign_local_scripts.ps1"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    Write-Host ""
    Write-Host "Running $Name..."
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $ProjectRoot
try {
    Invoke-Step "Signature-only script restore" { powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RestoreScript }
    Invoke-Step "Git pull" { git pull }
    Invoke-Step "Quality checks" { .\scripts\check.ps1 }
    Invoke-Step "RSS Automation" { python RSS_Automation.py }
    Invoke-Step "Local script signing" { powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SignScript }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Update, checks, runtime, and local script signing completed successfully."
