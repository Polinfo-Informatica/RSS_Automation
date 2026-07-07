param(
    [int] $HourlyInterval = 1,
    [switch] $RuntimeOnly,
    [switch] $SkipDependencies,
    [switch] $SkipGitHooks,
    [switch] $SkipLocalSigning
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

function Invoke-External {
    param(
        [string] $Name,
        [scriptblock] $Action
    )

    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Find-PythonCommand {
    $pyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        return @($pyLauncher.Source, "-3.14")
    }

    $python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        return @($python.Source)
    }

    throw "Python was not found. Install Python 3.14 or make python.exe/py.exe available on PATH."
}

function Test-7ZipAvailable {
    foreach ($command in @("7z.exe", "7zz.exe", "7za.exe")) {
        if ($null -ne (Get-Command $command -ErrorAction SilentlyContinue)) {
            return $true
        }
    }

    foreach ($candidate in @(
        "$env:ProgramFiles\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    )) {
        if ($candidate -and (Test-Path $candidate)) {
            return $true
        }
    }

    return $false
}

if (-not (Test-IsAdministrator)) {
    throw "Run this script from an elevated PowerShell window: right-click PowerShell and choose 'Run as administrator'."
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $ProjectRoot "env\Scripts\python.exe"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$DevRequirementsFile = Join-Path $ProjectRoot "requirements-dev.txt"
$RuntimeScript = Join-Path $ProjectRoot "RSS_Automation.py"
$TaskInstaller = Join-Path $ProjectRoot "scripts\install_tixati_rss_task.ps1"
$HookInstaller = Join-Path $ProjectRoot "scripts\install_local_git_hooks.ps1"
$Signer = Join-Path $ProjectRoot "scripts\sign_local_scripts.ps1"

Write-Host "RSS Automation full installer"
Write-Host "Project root: $ProjectRoot"
Write-Host "Hourly interval: $HourlyInterval"
Write-Host "Runtime only: $RuntimeOnly"

Invoke-Step "Create or verify Python virtual environment" {
    if (-not (Test-Path $VenvPython)) {
        $pythonCommand = Find-PythonCommand
        Write-Host "Creating virtual environment: $ProjectRoot\env"
        Invoke-External "Python venv creation" { & $pythonCommand[0] @($pythonCommand[1..($pythonCommand.Count - 1)]) -m venv (Join-Path $ProjectRoot "env") }
    }

    if (-not (Test-Path $VenvPython)) {
        throw "Virtual environment Python was not created: $VenvPython"
    }

    & $VenvPython --version
}

if (-not $SkipDependencies) {
    Invoke-Step "Install Python dependencies" {
        Invoke-External "pip upgrade" { & $VenvPython -m pip install --upgrade pip }

        if ($RuntimeOnly) {
            Invoke-External "runtime dependency installation" { & $VenvPython -m pip install -r $RequirementsFile }
        }
        else {
            Invoke-External "development dependency installation" { & $VenvPython -m pip install -r $DevRequirementsFile }
        }
    }
}

Invoke-Step "Verify 7-Zip availability" {
    if (Test-7ZipAvailable) {
        Write-Host "7-Zip detected."
    }
    else {
        Write-Warning "7-Zip was not detected. Runtime will still run, but 7z log/backup compaction requires 7-Zip. Install 7-Zip or set archive_7z_command in settings.json."
    }
}

Invoke-Step "Create runtime folder structure and starter config files" {
    Push-Location $ProjectRoot
    try {
        Invoke-External "runtime folder setup" {
            & $VenvPython -c "from pathlib import Path; from rss_automation.settings import get_project_root, load_settings, setup_folders; setup_folders(load_settings(Path('settings.json'), get_project_root()))"
        }
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipGitHooks -and (Test-Path (Join-Path $ProjectRoot ".git")) -and (Test-Path $HookInstaller)) {
    Invoke-Step "Install local Git protection hooks" {
        Invoke-External "Git hook installation" { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $HookInstaller }
    }
}

Invoke-Step "Install scheduled tasks" {
    Invoke-External "scheduled task installation" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $TaskInstaller -HourlyInterval $HourlyInterval
    }
}

if (-not $SkipLocalSigning -and (Test-Path $Signer)) {
    Invoke-Step "Sign local PowerShell scripts when local signer exists" {
        Invoke-External "local script signing" { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Signer }
    }
}

Write-Host ""
Write-Host "Installation completed."
Write-Host "Installed scheduled tasks:"
Write-Host "  RSS Automation - Tixati"
Write-Host "  RSS Automation - Config Backup Shutdown"
Write-Host "Runtime root follows the current Windows Downloads folder: <Downloads>\RSS_Automation"
Write-Host "Scheduled executions use the invisible wscript launcher."
