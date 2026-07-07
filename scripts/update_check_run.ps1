$ErrorActionPreference = "Stop"

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

Invoke-Step "Git pull" { git pull }
Invoke-Step "Ruff format" { python -m ruff format . }
Invoke-Step "Quality checks" { .\scripts\check.ps1 }
Invoke-Step "RSS Automation" { python RSS_Automation.py }

Write-Host ""
Write-Host "Update, checks, and runtime completed successfully."
