[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$NoWorker,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$StateDir = Join-Path $RepoRoot ".dev"
$StatePath = Join-Path $StateDir "run-state.json"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$ApiUrl = "http://localhost:8081"
$ApiHealthUrl = "http://localhost:8081/health"
$FrontendUrl = "http://localhost:3000"
$SwaggerUrl = "http://localhost:8081/docs"
$BrowserApiBaseUrl = "http://localhost:8081/api/v1"
$DockerTimeoutSeconds = 150
$StartupTimeoutSeconds = 90
$ApiBaseConflictDetected = $false

Set-Location -LiteralPath $RepoRoot

function Write-Step {
    param([string]$Message)
    Write-Host "[exam-dev] $Message"
}

function Fail {
    param([string]$Message)
    Write-Host "[exam-dev] ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
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
        Write-Step "Ignoring unreadable stale state file: $StatePath"
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
    foreach ($listener in $listeners) {
        $ownerProcessId = [int]$listener.OwningProcess
        if (Test-ProcessBelongsToRepo -ProcessId $ownerProcessId -State $State) {
            [void](Stop-ProcessTreeIfProject -ProcessId $ownerProcessId -Reason "port $Port" -State $State)
        } else {
            $processInfo = Get-ProcessInfo -ProcessId $ownerProcessId
            $safeCommand = if ($processInfo.CommandLine) { $processInfo.CommandLine } else { "" }
            Fail "Port $Port is used by an unrelated or uncertain process. PID=$ownerProcessId Name=$($processInfo.Name) CommandLine=$safeCommand. Close it or free the port before running again."
        }
    }
}

function Write-State {
    param([hashtable]$State)
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    $tmpPath = "$StatePath.tmp"
    $State | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $tmpPath -Encoding UTF8
    Move-Item -LiteralPath $tmpPath -Destination $StatePath -Force
}

function Get-SingleEnvValue {
    param([string]$Path, [string]$Name)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match "^\s*$([regex]::Escape($Name))\s*=\s*(.+?)\s*$") {
            return $matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Inspect-ApiBaseOverrides {
    Write-Step "Checking browser-facing API env overrides."
    $parentValue = [Environment]::GetEnvironmentVariable("NEXT_PUBLIC_API_BASE_URL", "Process")
    if ($parentValue -and $parentValue -ne $BrowserApiBaseUrl) {
        Write-Step "Conflicting process env NEXT_PUBLIC_API_BASE_URL=$parentValue"
        $script:ApiBaseConflictDetected = $true
    }

    $files = @(
        (Join-Path $RepoRoot "apps\web\.env.local"),
        (Join-Path $RepoRoot "apps\web\.env.development.local"),
        (Join-Path $RepoRoot "apps\web\.env"),
        (Join-Path $RepoRoot ".env.local")
    )
    foreach ($file in $files) {
        $value = Get-SingleEnvValue -Path $file -Name "NEXT_PUBLIC_API_BASE_URL"
        if ($value -and $value -ne $BrowserApiBaseUrl) {
            Write-Step "Conflicting API URL in $($file): $value"
            $script:ApiBaseConflictDetected = $true
        }
    }
    Write-Step "Next.js reads public env values at process startup; restart the frontend after env changes."
    Write-Step "This runner forces NEXT_PUBLIC_API_BASE_URL=$BrowserApiBaseUrl for the spawned frontend process."
}

function Test-StaleNextDevApiCache {
    $nextDevPath = Join-Path $RepoRoot "apps\web\.next\dev"
    if (-not (Test-Path -LiteralPath $nextDevPath)) {
        return $false
    }
    $files = @(Get-ChildItem -LiteralPath $nextDevPath -Recurse -File -Include *.js,*.mjs,*.json -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) {
        return $false
    }
    $match = $files | Select-String -Pattern "127\.0\.0\.1:8081" -Quiet -ErrorAction SilentlyContinue
    return [bool]$match
}

function Clear-StaleNextDevCacheIfNeeded {
    $nextDevPath = Join-Path $RepoRoot "apps\web\.next\dev"
    if ($script:ApiBaseConflictDetected -or (Test-StaleNextDevApiCache)) {
        if (Test-Path -LiteralPath $nextDevPath) {
            Write-Step "Removing stale Next dev cache because it may contain an old browser-facing API host."
            Remove-Item -LiteralPath $nextDevPath -Recurse -Force
        }
    }
}

function Assert-Prerequisites {
    Write-Step "Checking prerequisites."
    if (-not (Test-CommandExists "powershell.exe")) {
        Fail "Windows PowerShell was not found."
    }
    if (-not (Test-CommandExists "docker")) {
        Fail "Docker CLI was not found. Install Docker Desktop and retry."
    }
    if (-not (Test-CommandExists "pnpm")) {
        Fail "pnpm was not found. Install/enable pnpm before running this project."
    }
    if (-not (Test-Path -LiteralPath $PythonPath)) {
        Fail ".venv is missing. Create it from the repo root, for example: py -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt; pnpm install"
    }
    foreach ($requiredPath in @("docker-compose.yml", "apps\api", "apps\web")) {
        if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $requiredPath))) {
            Fail "Required path is missing: $requiredPath"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "node_modules"))) {
        Fail "pnpm dependencies appear missing: node_modules was not found. Run pnpm install manually, then retry."
    }
}

function Test-DockerReady {
    docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

function Ensure-DockerReady {
    Write-Step "Checking Docker engine."
    if (Test-DockerReady) {
        Write-Step "Docker engine is ready."
        return
    }

    $dockerDesktopPaths = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Docker\Docker\Docker Desktop.exe")
    )
    $dockerDesktop = $dockerDesktopPaths | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if (-not $dockerDesktop) {
        Fail "Docker engine is unavailable and Docker Desktop was not found in the standard Windows install path."
    }

    Write-Step "Docker engine is unavailable. Launching Docker Desktop."
    Start-Process -FilePath $dockerDesktop | Out-Null
    $deadline = (Get-Date).AddSeconds($DockerTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        if (Test-DockerReady) {
            Write-Step "Docker engine is ready."
            return
        }
        Write-Step "Waiting for Docker engine..."
    }
    Fail "Docker engine did not become available within $DockerTimeoutSeconds seconds."
}

function Get-ContainerState {
    param([string]$Name)
    $output = docker inspect --format "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" $Name 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $output) {
        return ""
    }
    return [string]$output
}

function Wait-HealthyContainer {
    param([string]$Name, [int]$TimeoutSeconds)
    Write-Step "Waiting for $Name to be running and healthy."
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $state = Get-ContainerState -Name $Name
        if ($state -match "^running\|healthy$" -or $state -match "^running\|none$") {
            Write-Step "$Name is ready."
            return
        }
        Start-Sleep -Seconds 2
    }
    Write-Host "docker compose ps:"
    docker compose ps
    Write-Host "Recent docker compose logs:"
    docker compose logs --tail 50
    Fail "$Name did not become healthy."
}

function Run-Migrations {
    Write-Step "Running Alembic migrations."
    Push-Location (Join-Path $RepoRoot "apps\api")
    try {
        & $PythonPath -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            Fail "Alembic migration failed. Docker services were left running for debugging."
        }
    } finally {
        Pop-Location
    }
}

function New-EncodedCommand {
    param([string]$CommandText)
    [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($CommandText))
}

function Escape-PSLiteral {
    param([string]$Value)
    $Value.Replace("'", "''")
}

function Start-DevTerminal {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Body
    )
    $safeTitle = Escape-PSLiteral -Value $Title
    $safeWorkingDirectory = Escape-PSLiteral -Value $WorkingDirectory
    $command = @"
`$Host.UI.RawUI.WindowTitle = '$safeTitle'
Set-Location -LiteralPath '$safeWorkingDirectory'
$Body
"@
    $encoded = New-EncodedCommand -CommandText $command
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $encoded) -PassThru
}

function Wait-HttpReady {
    param([string]$Url, [string]$Name, [int]$TimeoutSeconds)
    Write-Step "Waiting for $Name at $Url."
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Step "$Name is responding."
                return
            }
        } catch {
        }
        Start-Sleep -Seconds 2
    }
    Fail "$Name did not respond at $Url within $TimeoutSeconds seconds."
}

function Confirm-PortOwnedByStartedProcess {
    param([int]$Port, [int]$TerminalPid)
    $listeners = @(Get-PortListeners -Port $Port)
    foreach ($listener in $listeners) {
        if (Test-DescendantOfAny -ProcessId ([int]$listener.OwningProcess) -ParentPids @($TerminalPid)) {
            return
        }
    }
    Fail "Port $Port is not served by the process started by this runner."
}

function Stop-StartedProcesses {
    param([int[]]$ProcessIds)
    $state = Get-State
    foreach ($processIdToStop in $ProcessIds) {
        [void](Stop-ProcessTreeIfProject -ProcessId $processIdToStop -Reason "startup failure cleanup" -State $state)
    }
}

Assert-Prerequisites
Inspect-ApiBaseOverrides

$stateBefore = Get-State
foreach ($recordedProcessId in @(Get-RecordedPids -State $stateBefore)) {
    [void](Stop-ProcessTreeIfProject -ProcessId $recordedProcessId -Reason "previous runner state" -State $stateBefore)
}

Clear-ProjectPort -Port 3000 -State $stateBefore
Clear-ProjectPort -Port 8081 -State $stateBefore

if ($Clean) {
    $nextCache = Join-Path $RepoRoot "apps\web\.next"
    if (Test-Path -LiteralPath $nextCache) {
        Write-Step "Clean mode: removing apps/web/.next only."
        Remove-Item -LiteralPath $nextCache -Recurse -Force
    }
} else {
    Clear-StaleNextDevCacheIfNeeded
}

Ensure-DockerReady
Write-Step "Starting PostgreSQL and Redis with docker compose."
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Fail "docker compose up -d failed."
}
Wait-HealthyContainer -Name "exam_postgres" -TimeoutSeconds 90
Wait-HealthyContainer -Name "exam_redis" -TimeoutSeconds 90

Run-Migrations

$runState = @{
    timestamp = (Get-Date).ToString("o")
    repositoryPath = $RepoRoot
    ports = @{ api = 8081; web = 3000 }
    urls = @{ frontend = $FrontendUrl; api = $ApiUrl; swagger = $SwaggerUrl }
    apiTerminalPid = $null
    webTerminalPid = $null
    workerTerminalPid = $null
}
$startedPids = @()

try {
    Write-Step "Starting API in a visible terminal."
    $apiBody = @"
`$env:AI_PROVIDER = 'mock'
`$env:EMAIL_PROVIDER = 'mock'
`$env:FRONTEND_BASE_URL = '$FrontendUrl'
`$env:BACKEND_CORS_ORIGINS = '$FrontendUrl'
& '$((Escape-PSLiteral -Value $PythonPath))' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8081
"@
    $apiProcess = Start-DevTerminal -Title "Exam API" -WorkingDirectory (Join-Path $RepoRoot "apps\api") -Body $apiBody
    $runState.apiTerminalPid = $apiProcess.Id
    $startedPids += $apiProcess.Id
    Write-State -State $runState
    Wait-HttpReady -Url $ApiHealthUrl -Name "API health" -TimeoutSeconds $StartupTimeoutSeconds
    Confirm-PortOwnedByStartedProcess -Port 8081 -TerminalPid $apiProcess.Id

    if (-not $NoWorker) {
        Write-Step "Starting Celery worker in a visible terminal."
        $workerBody = @"
`$env:AI_PROVIDER = 'mock'
`$env:EMAIL_PROVIDER = 'mock'
& '$((Escape-PSLiteral -Value $PythonPath))' -m celery -A apps.worker.worker:celery_app worker --loglevel=INFO --pool=solo
"@
        $workerProcess = Start-DevTerminal -Title "Exam Worker" -WorkingDirectory $RepoRoot -Body $workerBody
        $runState.workerTerminalPid = $workerProcess.Id
        $startedPids += $workerProcess.Id
        Write-State -State $runState
    } else {
        Write-Step "Skipping worker startup because -NoWorker was provided."
    }

    Write-Step "Starting frontend in a visible terminal."
    $webBody = @"
`$env:NEXT_PUBLIC_API_BASE_URL = '$BrowserApiBaseUrl'
& pnpm --filter web dev
"@
    $webProcess = Start-DevTerminal -Title "Exam Web" -WorkingDirectory $RepoRoot -Body $webBody
    $runState.webTerminalPid = $webProcess.Id
    $startedPids += $webProcess.Id
    Write-State -State $runState
    Wait-HttpReady -Url $FrontendUrl -Name "frontend" -TimeoutSeconds $StartupTimeoutSeconds
    Confirm-PortOwnedByStartedProcess -Port 3000 -TerminalPid $webProcess.Id

    if (-not $NoBrowser) {
        Write-Step "Opening browser at $FrontendUrl."
        Start-Process $FrontendUrl | Out-Null
    } else {
        Write-Step "Skipping browser open because -NoBrowser was provided."
    }

    Write-Host ""
    Write-Host "Frontend: $FrontendUrl"
    Write-Host "API:      $ApiUrl"
    Write-Host "Swagger:  $SwaggerUrl"
    Write-Host ""
    Write-Host "Use localhost consistently. Do not mix localhost with 127.0.0.1 in browser URLs."
    exit 0
} catch {
    Write-Host "[exam-dev] ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Stop-StartedProcesses -ProcessIds $startedPids
    exit 1
}
