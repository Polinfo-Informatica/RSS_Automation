param(
    [string] $TaskName = "RSS Automation - Tixati",
    [string] $ShutdownBackupTaskName = "RSS Automation - Config Backup Shutdown"
)

$ErrorActionPreference = "Stop"

foreach ($name in @($TaskName, $ShutdownBackupTaskName)) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Host "Scheduled task not found: $name"
        continue
    }

    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "Scheduled task removed: $name"
}
