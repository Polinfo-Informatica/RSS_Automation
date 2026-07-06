$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    Write-Host $Name
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Invoke-Checked "Running Ruff check..." { python -m ruff check . }
Invoke-Checked "Running Ruff format check..." { python -m ruff format --check . }
Invoke-Checked "Running mypy..." { python -m mypy rss_automation }
Invoke-Checked "Running pytest..." { python -m pytest }

Write-Host "All checks passed."
