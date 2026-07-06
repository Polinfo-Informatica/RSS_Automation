$ErrorActionPreference = "Stop"

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

function Invoke-GitCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    $processInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $processInfo.FileName = "git"
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true

    foreach ($argument in $Arguments) {
        $processInfo.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $processInfo

    [void] $process.Start()
    $standardOutput = $process.StandardOutput.ReadToEnd()
    $standardError = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    return [PSCustomObject]@{
        ExitCode = $process.ExitCode
        Text = (($standardOutput, $standardError) -join "`n").Trim()
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

Invoke-GitWithRetry "Switching to main" @("checkout", "main")
Invoke-GitWithRetry "Pulling main" @("pull")
Invoke-GitWithRetry "Merging develop into main" @("merge", "develop")
Invoke-GitWithRetry "Pushing main" @("push")
Invoke-GitWithRetry "Switching back to develop" @("checkout", "develop")
Invoke-GitWithRetry "Merging main back into develop" @("merge", "main")
Invoke-GitWithRetry "Pushing develop" @("push")

Write-Host ""
Write-Host "Merge workflow completed successfully."
