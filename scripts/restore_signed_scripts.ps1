param(
    [switch] $Quiet
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string] $Message)

    if (-not $Quiet) {
        Write-Host $Message
    }
}

function Normalize-Text {
    param([string] $Text)

    return ($Text -replace "`r`n", "`n") -replace "`r", "`n"
}

function Remove-LocalAuthenticodeTrailer {
    param([string] $Text)

    $beginMarker = "# SI" + "G # Begin signature block"
    $endMarker = "# SI" + "G # End signature block"
    $beginIndex = $Text.IndexOf($beginMarker, [System.StringComparison]::Ordinal)

    if ($beginIndex -lt 0) {
        return $Text
    }

    $endIndex = $Text.IndexOf($endMarker, $beginIndex, [System.StringComparison]::Ordinal)
    if ($endIndex -lt 0) {
        throw "Found a local Authenticode trailer start without an end marker."
    }

    $afterEnd = $endIndex + $endMarker.Length
    while (($afterEnd -lt $Text.Length) -and (($Text[$afterEnd] -eq "`r") -or ($Text[$afterEnd] -eq "`n"))) {
        $afterEnd++
    }

    return $Text.Substring(0, $beginIndex).TrimEnd("`r", "`n") + "`r`n" + $Text.Substring($afterEnd)
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $ProjectRoot
try {
    $statusLines = @(git status --porcelain -- "*.ps1")
    $changedTrackedPowerShellFiles = @()

    foreach ($line in $statusLines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if ($line.StartsWith("??")) {
            continue
        }

        $path = $line.Substring(3).Trim()
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Substring(1, $path.Length - 2)
        }

        if ($path.ToLowerInvariant().EndsWith(".ps1")) {
            $changedTrackedPowerShellFiles += $path
        }
    }

    if ($changedTrackedPowerShellFiles.Count -eq 0) {
        Write-Status "No tracked PowerShell script changes to restore."
        exit 0
    }

    foreach ($path in $changedTrackedPowerShellFiles) {
        if (-not (Test-Path $path)) {
            throw "Tracked PowerShell script is modified but missing locally: $path"
        }

        $workingContent = Get-Content -Raw -Encoding UTF8 -Path $path
        $workingWithoutTrailer = Remove-LocalAuthenticodeTrailer $workingContent

        if ($workingWithoutTrailer -eq $workingContent) {
            throw "Refusing to restore non-signature PowerShell change: $path"
        }

        $headContent = (git show "HEAD:$path") -join "`n"
        if ((Normalize-Text $workingWithoutTrailer).TrimEnd() -ne (Normalize-Text $headContent).TrimEnd()) {
            throw "Refusing to restore $path because it contains changes besides the local Authenticode trailer."
        }

        Write-Status "Restoring local signature-only change: $path"
        git restore -- $path
        if ($LASTEXITCODE -ne 0) {
            throw "git restore failed for $path with exit code $LASTEXITCODE"
        }
    }
}
finally {
    Pop-Location
}
