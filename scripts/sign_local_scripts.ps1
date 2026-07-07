param(
    [string] $SignerScript = "C:\Users\kaosk\source\repos\RSS_Automation\Local Scripts\Local_Sign.ps1",
    [switch] $Require
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SignerScript)) {
    $message = "Local signer script not found: $SignerScript"
    if ($Require) {
        throw $message
    }

    Write-Host "$message. Skipping local script signing."
    exit 0
}

Write-Host "Running local script signer: $SignerScript"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SignerScript
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    throw "Local script signer failed with exit code $exitCode"
}
