param(
    [string] $TaskName = "RSS Automation - Tixati",
    [int] $HourlyInterval = 1
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    throw "Run this script from an elevated PowerShell window: right-click PowerShell and choose 'Run as administrator'."
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RunnerScript = Join-Path $ProjectRoot "scripts\run_rss_if_tixati_open.ps1"

if (-not (Test-Path $RunnerScript)) {
    throw "Runtime wrapper script not found: $RunnerScript"
}

$escapedRunner = $RunnerScript.Replace('"', '\"')
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$escapedRunner`"" `
    -WorkingDirectory $ProjectRoot

$startupTrigger = New-ScheduledTaskTrigger -AtStartup
$hourlyTrigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Hours $HourlyInterval) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

$description = "Runs RSS Automation at Windows startup and every $HourlyInterval hour(s), but only when Tixati is running."

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger @($startupTrigger, $hourlyTrigger) `
    -Principal $principal `
    -Settings $settings `
    -Description $description `
    -Force | Out-Null

Write-Host "Scheduled task installed or updated: $TaskName"
Write-Host "User: $currentUser"
Write-Host "Run level: Highest available privileges"
Write-Host "Triggers: Windows startup; every $HourlyInterval hour(s)"
Write-Host "Condition: wrapper exits unless Tixati is running"
Write-Host "Manual test command: Start-ScheduledTask -TaskName '$TaskName'"

# SIG # Begin signature block
# MIIFhQYJKoZIhvcNAQcCoIIFdjCCBXICAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUWAbzDBxUpiIQtrMw1FMwV8GG
# +gugggMYMIIDFDCCAfygAwIBAgIQSOBHXmSrerBCV13wFelV1DANBgkqhkiG9w0B
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
# FTAjBgkqhkiG9w0BCQQxFgQUtFrwns6VM8e18/7M8rf1CAeqjJEwDQYJKoZIhvcN
# AQEBBQAEggEAEH9KJoBLRQTEHp2fRbnw9e+9kSDQuWk86bfYWeEwgSs+64aXQoTE
# fVOn8JBdGtI4Z1VlOgEvXLCwzQWsi+rOqVvgRbq/Bt1caENNoJFMZHtgMLNQJ8mO
# CzzFTh45NNM4Uer/IqrZmh5XdXjzcpR2kDHUz2dn86wu1KXgBTAT2ou8PO0568Sa
# wqOKGGvOvjM7UTWgZAJUWn245RLJ8jAiNmJ7cNIbmWG10xtXX9C/SdZdH4RwgebH
# bSYQa5X1isMuDvg6rFxStoVtunPysnL1NH/m/wVHNHFpDN2ealKNl+za7DlfbNoN
# +JuYIE95HK90Dar8nub6G3J3ANO6oLcvPA==
# SIG # End signature block
