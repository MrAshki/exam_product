[CmdletBinding()]
param(
    [switch]$StopInfrastructure
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$StateDir = Join-Path $RepoRoot ".dev"
$StatePath = Join-Path $StateDir "run-state.json"

function Write-Step {
    param([string]$Message)
    Write-Host "[exam-dev] $Message"
}

function Get-ProcessInfo {
    param([int]$ProcessId)
    Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
}

function Get-DecodedCommand {
    param([string]$CommandLine)
    if (-not $CommandLine) {
        return ""
    }
    $match = [regex]::Match($CommandLine, "(?i)-EncodedCommand\s+([A-Za-z0-9+/=]+)")
    if (-not $match.Success) {
        return ""
    }
    try {
        return [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($match.Groups[1].Value))
    } catch {
        return ""
    }
}

function Get-ChildProcessIds {
    param([int]$ParentProcessId)
    $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ParentProcessId" -ErrorAction SilentlyContinue)
    $ids = @()
    foreach ($child in $children) {
        $ids += [int]$child.ProcessId
        $ids += Get-ChildProcessIds -ParentProcessId ([int]$child.ProcessId)
    }
    return $ids
}

function Get-State {
    if (-not (Test-Path -LiteralPath $StatePath)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
    } catch {
        Write-Step "State file exists but is unreadable; treating it as stale."
        return $null
    }
}

function Get-RecordedPids {
    param($State)
    $recordedProcessIds = @()
    if ($null -eq $State) {
        return $recordedProcessIds
    }
    foreach ($name in @("apiTerminalPid", "webTerminalPid", "workerTerminalPid")) {
        if ($State.PSObject.Properties.Name -contains $name -and $State.$name) {
            $recordedProcessIds += [int]$State.$name
        }
    }
    return $recordedProcessIds
}

function Test-DescendantOfAny {
    param([int]$ProcessId, [int[]]$ParentPids)
    foreach ($parentPid in $ParentPids) {
        if ($ProcessId -eq $parentPid) {
            return $true
        }
        $descendants = @(Get-ChildProcessIds -ParentProcessId $parentPid)
        if ($descendants -contains $ProcessId) {
            return $true
        }
    }
    return $false
}

function Test-ProcessBelongsToRepo {
    param([int]$ProcessId, $State)
    $processInfo = Get-ProcessInfo -ProcessId $ProcessId
    if ($null -eq $processInfo) {
        return $false
    }
    $commandLine = [string]$processInfo.CommandLine
    $decoded = Get-DecodedCommand -CommandLine $commandLine
    if ($commandLine -like "*$RepoRoot*" -or $decoded -like "*$RepoRoot*") {
        return $true
    }

    $recordedPids = @(Get-RecordedPids -State $State)
    if ($recordedPids.Count -gt 0 -and (Test-DescendantOfAny -ProcessId $ProcessId -ParentPids $recordedPids)) {
        return $true
    }

    return $false
}

function Stop-ProcessTreeIfProject {
    param([int]$ProcessId, [string]$Reason, $State)
    if (-not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {
        return $false
    }
    if (-not (Test-ProcessBelongsToRepo -ProcessId $ProcessId -State $State)) {
        $processInfo = Get-ProcessInfo -ProcessId $ProcessId
        Write-Step "Skipping PID $ProcessId because it is not verified as this project. Name=$($processInfo.Name)"
        return $false
    }

    Write-Step "Stopping project process tree PID $ProcessId ($Reason)."
    $tree = @(Get-ChildProcessIds -ParentProcessId $ProcessId)
    [array]::Reverse($tree)
    foreach ($childPid in $tree) {
        Stop-Process -Id $childPid -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    return $true
}

function Get-PortListeners {
    param([int]$Port)
    @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Sort-Object -Property OwningProcess -Unique)
}

function Clear-ProjectPort {
    param([int]$Port, $State)
    $listeners = @(Get-PortListeners -Port $Port)
    if ($listeners.Count -eq 0) {
        Write-Step "Port $Port is free."
        return
    }
    foreach ($listener in $listeners) {
        $ownerProcessId = [int]$listener.OwningProcess
        if (Test-ProcessBelongsToRepo -ProcessId $ownerProcessId -State $State) {
            [void](Stop-ProcessTreeIfProject -ProcessId $ownerProcessId -Reason "port $Port" -State $State)
        } else {
            $processInfo = Get-ProcessInfo -ProcessId $ownerProcessId
            Write-Step "Port $Port is used by an unrelated or uncertain process; leaving it alone. PID=$ownerProcessId Name=$($processInfo.Name)"
        }
    }
}

$state = Get-State
$recordedPids = @(Get-RecordedPids -State $state)
if ($recordedPids.Count -eq 0) {
    Write-Step "No recorded app processes found."
} else {
    foreach ($recordedProcessId in $recordedPids) {
        [void](Stop-ProcessTreeIfProject -ProcessId $recordedProcessId -Reason "recorded runner state" -State $state)
    }
}

Clear-ProjectPort -Port 3000 -State $state
Clear-ProjectPort -Port 8081 -State $state

if (Test-Path -LiteralPath $StatePath) {
    Remove-Item -LiteralPath $StatePath -Force
    Write-Step "Removed $StatePath."
}

if ($StopInfrastructure) {
    Write-Step "Stopping Docker Compose services without removing containers or volumes."
    Push-Location $RepoRoot
    try {
        docker compose stop
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[exam-dev] ERROR: docker compose stop failed." -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Step "Leaving PostgreSQL and Redis running. Use -StopInfrastructure to stop Docker services."
}

Write-Step "Stop complete."
exit 0
