param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.2.1",
    [int]$RefreshSeconds = 8
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Section($Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Get-ShortGitStatusCount {
    try {
        $status = git -C $ProjectRoot status --short 2>$null
        if ($null -eq $status) { return 0 }
        return @($status).Count
    } catch { return -1 }
}

function Get-GitBranch {
    try { return (git -C $ProjectRoot branch --show-current 2>$null).Trim() } catch { return "unknown" }
}

function Get-LastLines([string]$Path, [int]$Count = 18) {
    if (-not (Test-Path $Path)) { return @() }
    try { return Get-Content -LiteralPath $Path -Tail $Count -Encoding UTF8 } catch { return @("Unable to read: $Path", $_.Exception.Message) }
}

function Get-LatestProgressLines {
    $path = Join-Path $ProjectRoot "PROGRESS_LOG.md"
    if (-not (Test-Path $path)) { return @("PROGRESS_LOG.md not found") }
    try { return Get-Content -LiteralPath $path -Tail 8 -Encoding UTF8 } catch { return @("Unable to read PROGRESS_LOG.md") }
}

function Show-Dashboard {
    param(
        [datetime]$StartTime,
        [string]$CombinedLog,
        [string]$ExitCodeFile,
        [string]$RunDir,
        [object]$Job
    )

    $elapsed = New-TimeSpan -Start $StartTime -End (Get-Date)
    $branch = Get-GitBranch
    $dirtyCount = Get-ShortGitStatusCount
    $releaseDir = Join-Path $ProjectRoot ("releases\" + $TargetVersion)
    $sampleZip = Join-Path $releaseDir "samples\todo-api-generated-execution-pack.zip"
    $knownIssues = Join-Path $ProjectRoot ("V" + $TargetVersion.TrimStart('v') + "_KNOWN_ISSUES.md")
    $codexProcesses = @(Get-Process codex -ErrorAction SilentlyContinue)
    $logInfo = if (Test-Path $CombinedLog) { Get-Item $CombinedLog } else { $null }
    $exitText = if (Test-Path $ExitCodeFile) { Get-Content $ExitCodeFile -Raw } else { "running" }

    Clear-Host
    Write-Host "AIMart Unified Autonomous Visual Runner" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Started        : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $($Job.State)"
    Write-Host "Exit code      : $exitText"
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirtyCount"
    Write-Host "Codex procs    : $(@($codexProcesses).Count)"
    if ($logInfo) {
        Write-Host "Log updated    : $($logInfo.LastWriteTime.ToString('HH:mm:ss'))"
        Write-Host "Log size       : $($logInfo.Length) bytes"
    } else {
        Write-Host "Log            : waiting for first output"
    }

    Write-Section "Release Output"
    if (Test-Path $releaseDir) {
        Get-ChildItem -LiteralPath $releaseDir -Recurse -File -ErrorAction SilentlyContinue |
            Select-Object -First 12 FullName, Length, LastWriteTime |
            Format-Table -AutoSize | Out-String | Write-Host
    } else {
        Write-Host "$releaseDir not created yet." -ForegroundColor Yellow
    }
    if (Test-Path $sampleZip) {
        Write-Host "Sample execution pack: FOUND" -ForegroundColor Green
    } else {
        Write-Host "Sample execution pack: not found yet" -ForegroundColor Yellow
    }

    Write-Section "Recent Progress"
    Get-LatestProgressLines | ForEach-Object { Write-Host $_ }

    Write-Section "Latest Codex Log Tail"
    Get-LastLines $CombinedLog 22 | ForEach-Object { Write-Host $_ }

    Write-Section "Known Issues"
    if (Test-Path $knownIssues) {
        Get-LastLines $knownIssues 10 | ForEach-Object { Write-Host $_ }
    } else {
        Write-Host "$knownIssues not created yet." -ForegroundColor DarkYellow
    }

    Write-Host ""
    Write-Host "Do not close this window while running. Press Ctrl+C only if you want to stop the autonomous run." -ForegroundColor DarkGray
}

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

$CodexExe = (Get-Command codex.exe -ErrorAction SilentlyContinue).Source
if (-not $CodexExe) {
    $CodexExe = (Get-Command codex -ErrorAction SilentlyContinue).Source
}
if (-not $CodexExe) {
    throw "Codex CLI was not found in PATH."
}

$RunnerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptPath = Join-Path $RunnerRoot "codex\NEXT_TASK_PROMPT_UNIFIED_RUNNER.md"
if (-not (Test-Path $PromptPath)) {
    throw "Prompt file not found: $PromptPath"
}
$PromptText = Get-Content -LiteralPath $PromptPath -Raw -Encoding UTF8

$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunDir = Join-Path $ProjectRoot ("codex_runs\unified_visual_" + $TargetVersion.Replace('.', '_') + "_" + $RunStamp)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$CombinedLog = Join-Path $RunDir "codex.combined.log"
$ExitCodeFile = Join-Path $RunDir "codex.exitcode.txt"
$PromptCopy = Join-Path $RunDir "prompt.md"
Set-Content -LiteralPath $PromptCopy -Value $PromptText -Encoding UTF8

$ArgArray = @(
    "--cd", $ProjectRoot,
    "--sandbox", "workspace-write",
    "--ask-for-approval", "never",
    "exec",
    $PromptText
)

$StartTime = Get-Date

Write-Section "Starting Codex"
Write-Host "Codex executable: $CodexExe"
Write-Host "Run dir        : $RunDir"
Write-Host "Combined log   : $CombinedLog"
Write-Host "Prompt copy    : $PromptCopy"
Write-Host ""
Write-Host "Starting autonomous Codex job..."

$Job = Start-Job -Name "AIMart-$TargetVersion-UnifiedVisualRunner" -ScriptBlock {
    param($ProjectRoot, $CodexExe, $ArgArray, $CombinedLog, $ExitCodeFile)
    $ErrorActionPreference = "Continue"
    Set-Location -LiteralPath $ProjectRoot
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting Codex: $CodexExe" | Out-File -LiteralPath $CombinedLog -Encoding UTF8 -Append
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Args: $($ArgArray[0..([Math]::Min($ArgArray.Count-2, 7))] -join ' ') ..." | Out-File -LiteralPath $CombinedLog -Encoding UTF8 -Append
    & $CodexExe @ArgArray 2>&1 | ForEach-Object {
        $_.ToString() | Out-File -LiteralPath $CombinedLog -Encoding UTF8 -Append
    }
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    Set-Content -LiteralPath $ExitCodeFile -Value $code -Encoding UTF8
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Codex exited with code $code" | Out-File -LiteralPath $CombinedLog -Encoding UTF8 -Append
    return $code
} -ArgumentList $ProjectRoot, $CodexExe, $ArgArray, $CombinedLog, $ExitCodeFile

while ($Job.State -in @("Running", "NotStarted")) {
    Show-Dashboard -StartTime $StartTime -CombinedLog $CombinedLog -ExitCodeFile $ExitCodeFile -RunDir $RunDir -Job $Job
    Start-Sleep -Seconds $RefreshSeconds
}

Receive-Job $Job -Keep | Out-Null
Show-Dashboard -StartTime $StartTime -CombinedLog $CombinedLog -ExitCodeFile $ExitCodeFile -RunDir $RunDir -Job $Job

Write-Section "Final Checks"
$exitCode = if (Test-Path $ExitCodeFile) { (Get-Content $ExitCodeFile -Raw).Trim() } else { "unknown" }
Write-Host "Codex exit code: $exitCode"
Write-Host "Run directory  : $RunDir"
Write-Host "Combined log   : $CombinedLog"

Write-Host ""
Write-Host "Git status:" -ForegroundColor Cyan
git -C $ProjectRoot status --short --branch

Write-Host ""
Write-Host "Tags:" -ForegroundColor Cyan
git -C $ProjectRoot tag --list

$FinalReleaseDir = Join-Path $ProjectRoot ("releases\" + $TargetVersion)
Write-Host ""
Write-Host "Release directory:" -ForegroundColor Cyan
if (Test-Path $FinalReleaseDir) {
    Get-ChildItem -LiteralPath $FinalReleaseDir -Recurse | Format-Table -AutoSize
} else {
    Write-Host "$FinalReleaseDir was not created." -ForegroundColor Yellow
}

if ($exitCode -ne "0") {
    Write-Host ""
    Write-Host "Codex exited non-zero. Read the combined log above before retrying." -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host "Autonomous run finished. Review git status and release artifacts, then commit/tag manually if acceptable." -ForegroundColor Green
}
