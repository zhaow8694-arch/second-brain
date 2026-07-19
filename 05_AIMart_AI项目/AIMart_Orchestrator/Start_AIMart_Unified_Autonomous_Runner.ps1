param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$PromptFile = "",
    [int]$PollSeconds = 15,
    [switch]$AllowParallel
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Get-SafeGitText {
    param([string[]]$Args)
    try {
        $out = & git @Args 2>$null
        if ($LASTEXITCODE -ne 0) { return "" }
        return ($out | Out-String).Trim()
    } catch {
        return ""
    }
}

Write-Section "AIMart Unified Autonomous Runner"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

if (-not $PromptFile) {
    $PromptFile = Join-Path $PSScriptRoot "codex\NEXT_TASK_PROMPT_UNIFIED_RUNNER.md"
}

if (-not (Test-Path -LiteralPath $PromptFile)) {
    throw "Prompt file not found: $PromptFile"
}

$CodexCommand = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $CodexCommand) {
    $CodexCommand = Get-Command codex -ErrorAction SilentlyContinue
}
if (-not $CodexCommand) {
    throw "Codex CLI not found in PATH."
}
$CodexExe = $CodexCommand.Source

$ExistingCodex = Get-Process codex -ErrorAction SilentlyContinue
if ($ExistingCodex -and -not $AllowParallel) {
    Write-Warning "A Codex process is already running."
    Write-Host "This runner is designed to avoid multiple windows/runs."
    Write-Host "If your current v0.2 task is still running, do NOT start another run."
    Write-Host ""
    Write-Host "Codex processes:"
    $ExistingCodex | Select-Object Id, ProcessName, StartTime | Format-Table | Out-String | Write-Host
    Write-Host ""
    $answer = Read-Host "Type START to intentionally start a new run anyway, or press Enter to exit"
    if ($answer -ne "START") {
        Write-Host "Exited without starting a new Codex run." -ForegroundColor Yellow
        exit 0
    }
}

$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunDir = Join-Path $ProjectRoot "codex_runs\unified_autonomous\$RunStamp"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$CombinedLog = Join-Path $RunDir "combined.log"
$RunnerStatus = Join-Path $RunDir "runner_status.txt"
$PromptCopy = Join-Path $RunDir "prompt.md"
Copy-Item -LiteralPath $PromptFile -Destination $PromptCopy -Force

Write-Host "Project root : $ProjectRoot"
Write-Host "Codex        : $CodexExe"
Write-Host "Prompt       : $PromptFile"
Write-Host "Run dir      : $RunDir"
Write-Host "Combined log : $CombinedLog"
Write-Host ""
Write-Host "This is one-window mode. Do not open a separate monitor window." -ForegroundColor Green
Write-Host "The runner will print heartbeat status and log tails here." -ForegroundColor Green

# Start Codex in a background job so this same window can monitor status.
# Important: approval/sandbox flags are placed before `exec` for Codex CLI compatibility.
$job = Start-Job -Name "aimart-codex-unified-$RunStamp" -ScriptBlock {
    param($CodexExe, $ProjectRoot, $PromptFile, $CombinedLog)

    Set-Location -LiteralPath $ProjectRoot
    $prompt = Get-Content -LiteralPath $PromptFile -Raw

    "===== CODEX RUN START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') =====" | Out-File -FilePath $CombinedLog -Encoding UTF8
    "ProjectRoot: $ProjectRoot" | Out-File -FilePath $CombinedLog -Encoding UTF8 -Append

    & $CodexExe --cd $ProjectRoot --sandbox workspace-write --ask-for-approval never exec $prompt 2>&1 |
        Tee-Object -FilePath $CombinedLog -Append

    $exit = $LASTEXITCODE
    "===== CODEX RUN END $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') EXIT=$exit =====" | Out-File -FilePath $CombinedLog -Encoding UTF8 -Append
    exit $exit
} -ArgumentList $CodexExe, $ProjectRoot, $PromptFile, $CombinedLog

$start = Get-Date
$lastLength = -1
$staleCount = 0
$loop = 0

while ($job.State -eq "Running") {
    Start-Sleep -Seconds $PollSeconds
    $loop += 1
    $elapsed = New-TimeSpan -Start $start -End (Get-Date)

    $logExists = Test-Path -LiteralPath $CombinedLog
    $length = if ($logExists) { (Get-Item -LiteralPath $CombinedLog).Length } else { 0 }
    $lastWrite = if ($logExists) { (Get-Item -LiteralPath $CombinedLog).LastWriteTime } else { $null }

    if ($length -eq $lastLength) {
        $staleCount += 1
    } else {
        $staleCount = 0
        $lastLength = $length
    }

    $branch = Get-SafeGitText @("branch", "--show-current")
    $statusShort = Get-SafeGitText @("status", "--short")
    $statusCount = if ([string]::IsNullOrWhiteSpace($statusShort)) { 0 } else { ($statusShort -split "`n").Count }

    $releaseV020 = Test-Path -LiteralPath (Join-Path $ProjectRoot "releases\v0.2.0")
    $releaseV021 = Test-Path -LiteralPath (Join-Path $ProjectRoot "releases\v0.2.1")
    $codexProcesses = (Get-Process codex -ErrorAction SilentlyContinue | Measure-Object).Count

    $line = "[{0}] elapsed={1:hh\:mm\:ss} job={2} codex_processes={3} branch={4} changes={5} log_bytes={6} stale_ticks={7} v0.2.0={8} v0.2.1={9}" -f `
        (Get-Date -Format "HH:mm:ss"), $elapsed, $job.State, $codexProcesses, $branch, $statusCount, $length, $staleCount, $releaseV020, $releaseV021

    Write-Host $line

    $line | Out-File -FilePath $RunnerStatus -Encoding UTF8 -Append

    # Print a short log tail periodically, but not every heartbeat.
    if ($loop % 4 -eq 0 -and $logExists) {
        Write-Host ""
        Write-Host "---- recent Codex log tail ----" -ForegroundColor DarkCyan
        Get-Content -LiteralPath $CombinedLog -Tail 20
        Write-Host "---- end log tail ----" -ForegroundColor DarkCyan
        Write-Host ""
    }

    # Warning only. Do not kill the run automatically.
    if ($staleCount -ge 12) {
        Write-Warning "Combined log has not grown for about $($staleCount * $PollSeconds) seconds. Codex may still be reasoning, but check after completion if this persists."
    }
}

Write-Section "Codex job finished"

Receive-Job -Job $job -Keep | Out-String | Out-File -FilePath (Join-Path $RunDir "receive_job_output.txt") -Encoding UTF8
$jobState = $job.State
Remove-Job -Job $job -Force -ErrorAction SilentlyContinue

Write-Host "Job state: $jobState"
Write-Host "Combined log: $CombinedLog"

if (Test-Path -LiteralPath $CombinedLog) {
    Write-Host ""
    Write-Host "---- final Codex log tail ----" -ForegroundColor DarkCyan
    Get-Content -LiteralPath $CombinedLog -Tail 80
    Write-Host "---- end final log tail ----" -ForegroundColor DarkCyan
}

Write-Section "Post-run checks"

Write-Host "Git branch:"
git branch --show-current

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Tags:"
git tag --list

Write-Host ""
Write-Host "Release directories:"
Get-ChildItem ".\releases" -Directory -ErrorAction SilentlyContinue | Select-Object Name, LastWriteTime | Format-Table

Write-Host ""
if (Test-Path ".\releases\v0.2.0") {
    Write-Host "v0.2.0 release exists:" -ForegroundColor Green
    Get-ChildItem ".\releases\v0.2.0" -Recurse | Select-Object FullName, Length, LastWriteTime | Format-Table
} else {
    Write-Host "v0.2.0 release not found." -ForegroundColor Yellow
}

if (Test-Path ".\releases\v0.2.1") {
    Write-Host "v0.2.1 release exists:" -ForegroundColor Green
    Get-ChildItem ".\releases\v0.2.1" -Recurse | Select-Object FullName, Length, LastWriteTime | Format-Table
}

Write-Host ""
Write-Host "Unified runner finished. Review the summary above. No extra monitor window was required." -ForegroundColor Green
