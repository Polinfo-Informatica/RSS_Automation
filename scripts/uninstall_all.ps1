param(
    [switch] $RemoveRuntimeData,
    [switch] $RemoveVirtualEnvironment,
    [switch] $RemoveLocalGitHook
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-Step {
    param(
        [string] $Name,
        [scriptblock] $Action
    )

    Write-Host ""
    Write-Host "=== $Name ==="
    & $Action
}

function Get-DownloadsFolder {
    try {
        $shell = New-Object -ComObject Shell.Application
        $folder = $shell.NameSpace("shell:Downloads")
        if ($null -ne $folder -and $null -ne $folder.Self -and $folder.Self.Path) {
            return $folder.Self.Path
        }
    }
    catch {
        Write-Warning "Could not read Windows Downloads known folder through Shell.Application: $($_.Exception.Message)"
    }

    return (Join-Path $env:USERPROFILE "Downloads")
}

if (-not (Test-IsAdministrator)) {
    throw "Run this script from an elevated PowerShell window: right-click PowerShell and choose 'Run as administrator'."
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$TaskUninstaller = Join-Path $ProjectRoot "scripts\uninstall_tixati_rss_task.ps1"
$VenvPath = Join-Path $ProjectRoot "env"
$GitHookPath = Join-Path $ProjectRoot ".git\hooks\pre-commit"
$RuntimeRoot = Join-Path (Get-DownloadsFolder) "RSS_Automation"

Write-Host "RSS Automation full uninstaller"
Write-Host "Project root: $ProjectRoot"
Write-Host "Runtime root: $RuntimeRoot"
Write-Host "Remove runtime data: $RemoveRuntimeData"
Write-Host "Remove virtual environment: $RemoveVirtualEnvironment"
Write-Host "Remove local Git hook: $RemoveLocalGitHook"

Invoke-Step "Remove scheduled tasks" {
    if (Test-Path $TaskUninstaller) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $TaskUninstaller
        if ($LASTEXITCODE -ne 0) {
            throw "Scheduled task uninstaller failed with exit code $LASTEXITCODE"
        }
    }
    else {
        foreach ($taskName in @("RSS Automation - Tixati", "RSS Automation - Config Backup Shutdown")) {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($null -eq $task) {
                Write-Host "Scheduled task not found: $taskName"
                continue
            }

            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "Scheduled task removed: $taskName"
        }
    }
}

if ($RemoveLocalGitHook) {
    Invoke-Step "Remove local Git hook" {
        if (Test-Path $GitHookPath) {
            Remove-Item $GitHookPath -Force
            Write-Host "Removed: $GitHookPath"
        }
        else {
            Write-Host "Local Git hook not found: $GitHookPath"
        }
    }
}

if ($RemoveVirtualEnvironment) {
    Invoke-Step "Remove Python virtual environment" {
        if (Test-Path $VenvPath) {
            Remove-Item $VenvPath -Recurse -Force
            Write-Host "Removed: $VenvPath"
        }
        else {
            Write-Host "Virtual environment not found: $VenvPath"
        }
    }
}

if ($RemoveRuntimeData) {
    Invoke-Step "Remove runtime data" {
        if (Test-Path $RuntimeRoot) {
            Remove-Item $RuntimeRoot -Recurse -Force
            Write-Host "Removed: $RuntimeRoot"
        }
        else {
            Write-Host "Runtime root not found: $RuntimeRoot"
        }
    }
}
else {
    Write-Host ""
    Write-Host "Runtime data was preserved. Use -RemoveRuntimeData to delete: $RuntimeRoot"
}

Write-Host ""
Write-Host "Uninstallation completed."
