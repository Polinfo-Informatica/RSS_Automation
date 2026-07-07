$ErrorActionPreference = "Stop"

param(
    [string] $TaskName = "RSS Automation - Tixati"
)

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Host "Scheduled task not found: $TaskName"
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Scheduled task removed: $TaskName"
