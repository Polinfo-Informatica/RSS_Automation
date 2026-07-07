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

Invoke-GitWithRetry "Switching to main" @("checkout", "main")
Invoke-GitWithRetry "Pulling main" @("pull")
Invoke-GitWithRetry "Merging develop into main" @("merge", "develop")
Invoke-GitWithRetry "Pushing main" @("push")
Invoke-GitWithRetry "Switching back to develop" @("checkout", "develop")
Invoke-GitWithRetry "Merging main back into develop" @("merge", "main")
Invoke-GitWithRetry "Pushing develop" @("push")

Write-Host ""
Write-Host "Merge workflow completed successfully."

# SIG # Begin signature block
# MIIFhQYJKoZIhvcNAQcCoIIFdjCCBXICAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUB49wUSPdXFAFsHkWNe7Y9OTu
# Bq6gggMYMIIDFDCCAfygAwIBAgIQSOBHXmSrerBCV13wFelV1DANBgkqhkiG9w0B
# AQUFADAiMSAwHgYDVQQDDBdQb3dlclNoZWxsIENvZGUgU2lnbmluZzAeFw0yNTA5
# MzAwNzQ5MDNaFw0yNjA5MzAwODA5MDNaMCIxIDAeBgNVBAMMF1Bvd2VyU2hlbGwg
# Q29kZSBTaWduaW5nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1zRM
# YsMQnBIWe/tz+wp0rRno7d6SBX4n9D0AadfZH+AvmrUHBAa7ZAzjjnVEtHz+ptB6
# iR8OXLLWWGh3BRq0/0ToKacvV2KbS+vqJPnPzSHnI7JbM8r2xSMUSdK4z2FmicOI
# pnLweWadpz1WsDKJnFMwIh+bG5dcUIy2BcmxkyBFD+R4jLWP2hlUrRwczVjLcwHS
# 6Ej7MIIUGu2sQ3oyqAXUXT+28vTjJBzFE350iRqTcnnXf0qnfnBiT2v1uXyieDuc
# w3kxCvAG5a/u7OM9DXPLcfMenSjpTKk0gJeyUZuc+e5yzewseiNvUGNcNboWBAAd
# CEJZAHCDJkdiAKRYlQIDAQABo0YwRDAOBgNVHQ8BAf8EBAMCB4AwEwYDVR0lBAww
# CgYIKwYBBQUHAwMwHQYDVR0OBBYEFFP5ZPMO4TzMVmNq8LLUzLBUmmyAMA0GCSqG
# SIb3DQEBBQUAA4IBAQDJAASsoy0ZUSXE+ASki8NbvCBSv0umvH8cksdFXxjJKYGX
# eOQ23vZTC/vJ7IqnosXnlW9GhKdpJnYG3EUpas2z6kuN8xMKkJWzw0SAoRkHmo2D
# VH05auUrgEi6i6by/eZc5WMDmaZB6FMn6Gw+lae7KVTCwgfFQV75vB7XPvh8lOfX
# WuhDzf8Tiel729XCEKIi934Q6BfZd3ZEFX8o/jousZHNAWMe+RWRSLuht6NHO5xc
# c1zDEbHYl7cfZD0L0dsJAtlQUFbrNcfky2wP2b6DtT4AtgLFYXERZErQ6iSWBGE2
# yPh+Z9wI/i6VsH+ayMpusOX/gKeDQC3kHoGiL++pMYIB1zCCAdMCAQEwNjAiMSAw
# HgYDVQQDDBdQb3dlclNoZWxsIENvZGUgU2lnbmluZwIQSOBHXmSrerBCV13wFelV
# 1DAJBgUrDgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAAoQKAADAZBgkqhkiG
# 9w0BCQMxDAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIB
# FTAjBgkqhkiG9w0BCQQxFgQU7uSLJ0GUD/tgnKhgEq9O7SsAM+IwDQYJKoZIhvcN
# AQEBBQAEggEAjtIUPefadf41whu19Sr8TcE6M5Gicu2kRu+DY+MJATu0H/pZm+I4
# x07g44O1PX/+HB1Vbyhdm2ly3HSJcZzrNO2aVll47knz6oaCyjKe/rP9ANVDvvo8
# opw7zVMMMW0ljVOlOcoAdz5aCts8hFDIRug4QCS8KLBTdSVwa/3Djc5HLZwjdhgs
# JtXL989t6/VHWR8woMKcuaP/+cEJJBq6vffWFxeoSoTDOXd/wWQC/Aq0g4GN8Mbd
# GaJE9W3eL1j6EVwfkmPwJTdWnCenRfdTEfMDtCvVmnnRfSjMbcvEaw8Jew14SCi8
# K0o8g65MhjE7tvmNLbSbmGD7Jo4orwdHVA==
# SIG # End signature block
