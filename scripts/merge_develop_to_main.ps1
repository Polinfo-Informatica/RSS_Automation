$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RestoreScript = Join-Path $ProjectRoot "scripts\restore_signed_scripts.ps1"
$SignScript = Join-Path $ProjectRoot "scripts\sign_local_scripts.ps1"

$MaxAttempts = 3
$RetryDelaySeconds = 5

$ConnectionErrorPattern = @(
    "could not resolve host",
    "failed to connect",
    "connection timed out",
    "connection reset",
    "connection was reset",
    "connection refused",
    "operation timed out",
    "network is unreachable",
    "the remote end hung up unexpectedly",
    "rpc failed",
    "early eof",
    "ssl_error_syscall",
    "schannel",
    "unable to access.*github\.com"
) -join "|"

function Test-ConnectionErrorText {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Text
    )

    return $Text -match $ConnectionErrorPattern
}

function Invoke-LocalScript {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Description,

        [Parameter(Mandatory = $true)]
        [string] $ScriptPath
    )

    Write-Host ""
    Write-Host $Description
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "$Description failed with exit code $exitCode."
    }
}

function Test-WorkingTreeClean {
    $status = @(git status --porcelain)
    if ($status.Count -eq 0) {
        return
    }

    Write-Host ""
    Write-Host "Local non-signature changes remain after signature restore:"
    $status | ForEach-Object { Write-Host $_ }
    Write-Host ""
    Write-Host "Resolve these before merging. For local formatting-only changes, use:"
    Write-Host "git restore <path>"
    Write-Host ""
    throw "Working tree is not clean. Merge aborted before branch checkout."
}

function Invoke-GitCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $text = ($output | ForEach-Object { $_.ToString() } | Out-String).Trim()
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    return [PSCustomObject]@{
        ExitCode = $exitCode
        Text = $text
    }
}

function Invoke-GitWithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Description,

        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Write-Host ""
        Write-Host "$Description (attempt $attempt of $MaxAttempts)"
        Write-Host "git $($Arguments -join ' ')"

        $result = Invoke-GitCommand -Arguments $Arguments
        $exitCode = $result.ExitCode
        $text = $result.Text

        if ($text) {
            Write-Host $text
        }

        if ($exitCode -eq 0) {
            return
        }

        if ((Test-ConnectionErrorText -Text $text) -and ($attempt -lt $MaxAttempts)) {
            Write-Warning "Connection-related Git error detected. Retrying in $RetryDelaySeconds seconds..."
            Start-Sleep -Seconds $RetryDelaySeconds
            continue
        }

        throw "$Description failed with exit code $exitCode."
    }
}

Push-Location $ProjectRoot
try {
    Invoke-LocalScript "Restoring signature-only PowerShell changes" $RestoreScript
    Test-WorkingTreeClean
    Invoke-GitWithRetry "Switching to main" @("checkout", "main")
    Invoke-GitWithRetry "Pulling main" @("pull")
    Invoke-GitWithRetry "Merging develop into main" @("merge", "develop")
    Invoke-GitWithRetry "Pushing main" @("push")
    Invoke-GitWithRetry "Switching back to develop" @("checkout", "develop")
    Invoke-GitWithRetry "Merging main back into develop" @("merge", "main")
    Invoke-GitWithRetry "Pushing develop" @("push")
    Invoke-LocalScript "Signing local PowerShell scripts" $SignScript
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Merge workflow completed successfully."
