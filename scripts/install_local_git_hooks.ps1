$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$HookPath = Join-Path $ProjectRoot ".git\hooks\pre-commit"
$HookDirectory = Split-Path -Parent $HookPath

if (-not (Test-Path $HookDirectory)) {
    New-Item -ItemType Directory -Force -Path $HookDirectory | Out-Null
}

$hookContent = @'
#!/bin/sh

blocked=0
begin_marker="# SIG # Begin signature block"

for file in $(git diff --cached --name-only -- "*.ps1"); do
    if git show ":$file" | grep -Fq "$begin_marker"; then
        echo "Refusing to commit signed PowerShell script: $file" >&2
        blocked=1
    fi
done

if [ "$blocked" -ne 0 ]; then
    echo "Run scripts/restore_signed_scripts.ps1 before committing, then sign locally after pulling/merging." >&2
    exit 1
fi

exit 0
'@

Set-Content -Path $HookPath -Value $hookContent -Encoding ASCII
Write-Host "Installed local pre-commit hook: $HookPath"
Write-Host "The hook blocks commits that contain Authenticode signature trailers in tracked .ps1 files."
