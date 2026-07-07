$ErrorActionPreference = "Stop"

$CertificateThumbprint = "D5A53E6B578CFE698A71A62C665DF0BBF8EBE060"
$RepoRoot = "C:\Users\kaosk\source\repos\RSS_Automation"

$CodeSignCert = Get-ChildItem -Path Cert:\CurrentUser\My |
    Where-Object { $_.Thumbprint -eq $CertificateThumbprint }

if ($null -eq $CodeSignCert) {
    throw "Certificate not found: $CertificateThumbprint"
}

$ScriptsToSign = @(
    "$RepoRoot\scripts\install_tixati_rss_task.ps1",
    "$RepoRoot\scripts\run_rss_if_tixati_open.ps1",
    "$RepoRoot\scripts\merge_develop_to_main.ps1",
    "$RepoRoot\scripts\update_check_run.ps1"
)

foreach ($ScriptPath in $ScriptsToSign) {
    if (Test-Path $ScriptPath) {
        Write-Host "Signing: $ScriptPath"
        Set-AuthenticodeSignature -FilePath $ScriptPath -Certificate $CodeSignCert | Out-Host
    }
}

# SIG # Begin signature block
# MIIFhQYJKoZIhvcNAQcCoIIFdjCCBXICAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQU56021hl8edI6bkJX9L9JKbzZ
# il6gggMYMIIDFDCCAfygAwIBAgIQSOBHXmSrerBCV13wFelV1DANBgkqhkiG9w0B
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
# FTAjBgkqhkiG9w0BCQQxFgQUAtfu/0+MSBQf/3uoOXeMw8bT1bYwDQYJKoZIhvcN
# AQEBBQAEggEAZU6aA7o5HuTFIhMG8PK19hh2Bx6sVuSu7Trm7XV2LbkgbuZiWPBi
# m4rNqOAdyyuNN/DHV27Q2FRv0UmxKd96rh5NsHKD8peF7YfXDcd0QkA2cDbbogZe
# 4u7Cm0zufFYMqE2AgMNEQxZS/lnkmvBCQ0bmD4OM2BtbZcBZ1TH5D0HAvDUzfYpq
# DpW8zBjLOBz9rCGY/lgJ3HT+odROGc5F/3/YfHjUCi3LPf5Tnlp2h8LTkJ61L1NF
# GlYViji/iXOXEx2aboT7xoAdPv/g04g9qvTp+fSWm2hxoi6lEFYMY8Zxqyhus4TB
# RWOJylV7yESWOC5Sa3/c5ObQWjzWXMsIhg==
# SIG # End signature block
