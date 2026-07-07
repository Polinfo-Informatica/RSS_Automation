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

function Get-GitStatusLines {
    return @(git status --porcelain)
}

function Assert-CleanWorkingTree {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Reason
    )

    $status = Get-GitStatusLines
    if ($status.Count -eq 0) {
        return
    }

    Write-Host ""
    Write-Host "Local non-signature changes were found ${Reason}:"
    $status | ForEach-Object { Write-Host $_ }
    Write-Host ""
    Write-Host "The update workflow only auto-commits changes it created itself by running Ruff format."
    Write-Host "Resolve these existing local changes first, then run this script again."

    throw "Working tree is not clean."
}

function Get-ChangedFiles {
    return @(git diff --name-only)
}

function Commit-RuffFormattingChanges {
    $changedFiles = Get-ChangedFiles
    if ($changedFiles.Count -eq 0) {
        Write-Host "No Ruff formatting changes to commit."
        return
    }

    $unexpectedFiles = @($changedFiles | Where-Object { -not $_.ToLowerInvariant().EndsWith(".py") })
    if ($unexpectedFiles.Count -gt 0) {
        Write-Host ""
        Write-Host "Unexpected files changed after Ruff format:"
        $unexpectedFiles | ForEach-Object { Write-Host $_ }
        throw "Refusing to auto-commit non-Python changes."
    }

    Write-Host ""
    Write-Host "Ruff formatting changed these files:"
    $changedFiles | ForEach-Object { Write-Host $_ }

    & git add -- $changedFiles
    if ($LASTEXITCODE -ne 0) {
        throw "git add failed with exit code $LASTEXITCODE"
    }

    & git commit -m "Apply Ruff formatting"
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed with exit code $LASTEXITCODE"
    }

    & git push
    if ($LASTEXITCODE -ne 0) {
        throw "git push failed with exit code $LASTEXITCODE"
    }
}

Push-Location $ProjectRoot
try {
    Invoke-Step "Signature-only script restore" { powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RestoreScript }
    Assert-CleanWorkingTree "before pulling"
    Invoke-Step "Git pull" { git pull }
    Assert-CleanWorkingTree "after pulling"
    Invoke-Step "Ruff format" { python -m ruff format . }
    Invoke-Step "Commit Ruff formatting changes" { Commit-RuffFormattingChanges }
    Invoke-Step "Quality checks" { .\scripts\check.ps1 }
    Invoke-Step "RSS Automation" { python RSS_Automation.py }
    Invoke-Step "Local script signing" { powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SignScript }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Update, formatting, checks, runtime, and local script signing completed successfully."

