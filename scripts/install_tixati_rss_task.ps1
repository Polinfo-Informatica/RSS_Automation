param(
    [string] $TaskName = "RSS Automation - Tixati",
    [string] $ShutdownBackupTaskName = "RSS Automation - Config Backup Shutdown",
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
$HiddenLauncherScript = Join-Path $ProjectRoot "scripts\run_hidden.vbs"
$RunnerScript = Join-Path $ProjectRoot "scripts\run_rss_if_tixati_open.ps1"
$BackupRunnerScript = Join-Path $ProjectRoot "scripts\run_config_backup.ps1"

if (-not (Test-Path $HiddenLauncherScript)) {
    throw "Hidden launcher script not found: $HiddenLauncherScript"
}

if (-not (Test-Path $RunnerScript)) {
    throw "Runtime wrapper script not found: $RunnerScript"
}

if (-not (Test-Path $BackupRunnerScript)) {
    throw "Config backup wrapper script not found: $BackupRunnerScript"
}

$escapedHiddenLauncher = $HiddenLauncherScript.Replace('"', '\"')
$escapedRunner = $RunnerScript.Replace('"', '\"')
$action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "//B //Nologo `"$escapedHiddenLauncher`" `"$escapedRunner`"" `
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

$escapedBackupRunner = $BackupRunnerScript.Replace('"', '\"')
$backupAction = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "//B //Nologo `"$escapedHiddenLauncher`" `"$escapedBackupRunner`" -Force" `
    -WorkingDirectory $ProjectRoot

$shutdownSubscription = "<QueryList><Query Id='0' Path='System'><Select Path='System'>*[System[Provider[@Name='User32'] and EventID=1074]]</Select></Query></QueryList>"
$shutdownTrigger = New-CimInstance `
    -ClientOnly `
    -Namespace "root/Microsoft/Windows/TaskScheduler" `
    -ClassName "MSFT_TaskEventTrigger" `
    -Property @{
        Enabled = $true
        Subscription = $shutdownSubscription
    }

if (-not $shutdownTrigger.PSObject.TypeNames.Contains("Microsoft.Management.Infrastructure.CimInstance#MSFT_TaskTrigger")) {
    $shutdownTrigger.PSObject.TypeNames.Insert(0, "Microsoft.Management.Infrastructure.CimInstance#MSFT_TaskTrigger")
}

$backupSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $ShutdownBackupTaskName `
    -Action $backupAction `
    -Trigger $shutdownTrigger `
    -Principal $principal `
    -Settings $backupSettings `
    -Description "Creates a forced RSS config backup when Windows shutdown or restart is initiated." `
    -Force | Out-Null

Write-Host "Scheduled task installed or updated: $TaskName"
Write-Host "User: $currentUser"
Write-Host "Run level: Highest available privileges"
Write-Host "Triggers: Windows startup; every $HourlyInterval hour(s)"
Write-Host "Condition: wrapper exits unless Tixati is running"
Write-Host "Window: invisible wscript launcher"
Write-Host "Manual test command: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "Shutdown backup task installed or updated: $ShutdownBackupTaskName"
Write-Host "Trigger: Windows shutdown/restart initiated event"
Write-Host "Window: invisible wscript launcher"
Write-Host "Manual test command: Start-ScheduledTask -TaskName '$ShutdownBackupTaskName'"
