$ErrorActionPreference = "Stop"

param(
    [string] $TaskName = "RSS Automation - Tixati",
    [int] $HourlyInterval = 1
)

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
