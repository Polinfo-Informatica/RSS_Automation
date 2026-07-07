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

# SIG # Begin signature block
# MIIFhQYJKoZIhvcNAQcCoIIFdjCCBXICAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUHXzgkPKvFQ2NyZIIeF1RkfSx
# gYSgggMYMIIDFDCCAfygAwIBAgIQSOBHXmSrerBCV13wFelV1DANBgkqhkiG9w0B
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
# FTAjBgkqhkiG9w0BCQQxFgQUIND/NSuEBCAtFaJCKYV+HX2nSGgwDQYJKoZIhvcN
# AQEBBQAEggEALyLLD13waMNtCBGC6wcS49weCNMSqHmY2thSTu1KA5PSfiS39KA5
# IIvRT+klyxSpTc2jkFrjnC3SfQYeQLb/e3GqskdtjqbbPMmHNXgsHeGRm/38+hsT
# hwsCaPV/McMWNY5JWFUqKVGM8ckEUUOnszfWLfRevEPMLLjHsu+qYoNdFYAObzgQ
# RXKNLpoPe/4FGcy88Ty2016XtCoPWTpW0u+GwTWtByeVwOcRcOO3fWnf03BeoyZl
# 0gosILol/joi66iFD/L5K790eraUAH4bV8b0pPdcFL75U8CeYXlZFlkRhmLCRnnQ
# NlPakjKM1/xCZhwu7dw8IxDxMvOvCM0e9w==
# SIG # End signature block
