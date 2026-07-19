param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.2.2",
    [switch]$AllowDirtyStart
)

$ErrorActionPreference = "Stop"
$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptSource = Join-Path $ToolRoot "codex\V0.2.2_AUTONOMOUS_COMPLETION_GATE_PROMPT_EN.md"
$RunName = "autonomous_v0_2_2_completion_gate_fixed_stdin"

function Write-Section($Title) {
    Write-Host "`n== $Title ==" -ForegroundColor Cyan
}

function Get-GitBranch {
    try { return (git branch --show-current).Trim() } catch { return "unknown" }
}

function Get-GitDirtyFiles {
    try { return @(git status --short) } catch { return @() }
}

function Get-LatestCombinedLog($LogDir) {
    if (-not (Test-Path $LogDir)) { return $null }
    return Get-ChildItem $LogDir -Recurse -File -Filter "*.combined.log" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function Show-Dashboard($StartedAt, $Job, $CombinedLog, $ProjectRoot, $TargetVersion) {
    $elapsed = (Get-Date) - $StartedAt
    $branch = Get-GitBranch
    $dirty = @(Get-GitDirtyFiles).Count
    $releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $sampleZip = Join-Path $releaseDir "samples\todo-api-generated-execution-pack.zip"
    $knownIssues = Join-Path $ProjectRoot "V0.2.2_KNOWN_ISSUES.md"
    $progress = Join-Path $ProjectRoot "PROGRESS_LOG.md"
    $logExists = Test-Path $CombinedLog
    $logItem = if ($logExists) { Get-Item $CombinedLog } else { $null }
    $codexCount = @(Get-Process codex -ErrorAction SilentlyContinue).Count + @(Get-Process Codex -ErrorAction SilentlyContinue).Count

    Clear-Host
    Write-Host "AIMart Autonomous Completion Gate Runner - FIXED STDIN" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Started        : $($StartedAt.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $($Job.State)"
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirty"
    Write-Host "Codex procs    : $codexCount"
    if ($logItem) {
        Write-Host "Log updated    : $($logItem.LastWriteTime.ToString('HH:mm:ss'))"
        Write-Host "Log size       : $($logItem.Length) bytes"
    } else {
        Write-Host "Log updated    : not created yet"
        Write-Host "Log size       : 0 bytes"
    }

    Write-Section "Release Output"
    if (Test-Path $releaseDir) {
        Get-ChildItem $releaseDir -Recurse | Select-Object Mode,LastWriteTime,Length,FullName | Format-Table -AutoSize | Out-String | Write-Host
    } else {
        Write-Host "$releaseDir not created yet." -ForegroundColor Yellow
    }
    if (Test-Path $sampleZip) { Write-Host "Sample execution pack: found" -ForegroundColor Green } else { Write-Host "Sample execution pack: not found yet" -ForegroundColor Yellow }

    Write-Section "Recent Progress"
    if (Test-Path $progress) { Get-Content $progress -Tail 8 -Encoding UTF8 | ForEach-Object { Write-Host $_ } }
    else { Write-Host "PROGRESS_LOG.md not found." -ForegroundColor Yellow }

    Write-Section "Latest Codex Log Tail"
    if (Test-Path $CombinedLog) { Get-Content $CombinedLog -Tail 24 -Encoding UTF8 | ForEach-Object { Write-Host $_ } }
    else { Write-Host "Combined log not created yet." -ForegroundColor Yellow }

    Write-Section "Known Issues"
    if (Test-Path $knownIssues) { Get-Content $knownIssues -Tail 20 -Encoding UTF8 | ForEach-Object { Write-Host $_ } }
    else { Write-Host "$knownIssues not created yet." -ForegroundColor Yellow }

    Write-Host "`nDo not close this window while running. Press Ctrl+C only if you want to stop the autonomous run." -ForegroundColor DarkGray
}

Write-Section "Preflight"
if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path $PromptSource)) { throw "Prompt not found: $PromptSource" }

$codexCmd = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $codexCmd) { $codexCmd = Get-Command codex -ErrorAction SilentlyContinue }
if (-not $codexCmd) { throw "Codex CLI not found in PATH." }
$CodexExe = $codexCmd.Source
Write-Host "Codex executable: $CodexExe"

Set-Location -LiteralPath $ProjectRoot
$branch = Get-GitBranch
Write-Host "Current branch: $branch"

$dirty = @(Get-GitDirtyFiles)
Write-Host "Dirty files before start: $($dirty.Count)"
if ($dirty.Count -gt 0 -and -not $AllowDirtyStart) {
    Write-Host "`nThe working tree is not clean. To prevent mixing versions, this runner will stop." -ForegroundColor Yellow
    Write-Host "Commit or stash existing changes first, or rerun with -AllowDirtyStart only if you intentionally want to continue." -ForegroundColor Yellow
    exit 10
}

$ProjectCodexDir = Join-Path $ProjectRoot "codex"
New-Item -ItemType Directory -Force -Path $ProjectCodexDir | Out-Null
$ProjectPrompt = Join-Path $ProjectCodexDir "V0.2.2_AUTONOMOUS_COMPLETION_GATE_PROMPT_EN.md"
Copy-Item -LiteralPath $PromptSource -Destination $ProjectPrompt -Force

$LogDir = Join-Path $ProjectRoot "codex_runs\$RunName"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$CombinedLog = Join-Path $LogDir "codex_v022_fixed_stdin_$Timestamp.combined.log"
$ExitCodeFile = Join-Path $LogDir "codex_v022_fixed_stdin_$Timestamp.exitcode.txt"

Write-Section "Starting Codex"
Write-Host "Using stdin prompt mode: codex ... exec --cd <project> -"
Write-Host "Combined log: $CombinedLog"

$StartedAt = Get-Date
$job = Start-Job -Name "AIMart-v022-completion-gate" -ScriptBlock {
    param($CodexExe, $ProjectRoot, $PromptFile, $CombinedLog, $ExitCodeFile)
    $ErrorActionPreference = "Continue"
    Set-Location -LiteralPath $ProjectRoot
    $PromptText = Get-Content -LiteralPath $PromptFile -Raw -Encoding UTF8
    $ArgList = @(
        "-c", "approval_policy=never",
        "-c", "sandbox_mode=workspace-write",
        "exec",
        "--cd", $ProjectRoot,
        "-"
    )
    "AIMart fixed stdin runner started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $CombinedLog -Encoding UTF8
    "Command: codex -c approval_policy=never -c sandbox_mode=workspace-write exec --cd `"$ProjectRoot`" -" | Add-Content $CombinedLog -Encoding UTF8
    "" | Add-Content $CombinedLog -Encoding UTF8
    try {
        $PromptText | & $CodexExe @ArgList 2>&1 | Tee-Object -FilePath $CombinedLog -Append
        $exit = $LASTEXITCODE
        if ($null -eq $exit) { $exit = 0 }
        $exit | Out-File $ExitCodeFile -Encoding ASCII
        exit $exit
    } catch {
        "RUNNER_EXCEPTION: $($_.Exception.Message)" | Add-Content $CombinedLog -Encoding UTF8
        99 | Out-File $ExitCodeFile -Encoding ASCII
        exit 99
    }
} -ArgumentList $CodexExe, $ProjectRoot, $ProjectPrompt, $CombinedLog, $ExitCodeFile

while ($job.State -eq "Running") {
    Show-Dashboard -StartedAt $StartedAt -Job $job -CombinedLog $CombinedLog -ProjectRoot $ProjectRoot -TargetVersion $TargetVersion
    Start-Sleep -Seconds 5
}

Receive-Job $job -Keep | Out-Null
Show-Dashboard -StartedAt $StartedAt -Job $job -CombinedLog $CombinedLog -ProjectRoot $ProjectRoot -TargetVersion $TargetVersion

Write-Section "Post-run summary"
$exitCode = "unknown"
if (Test-Path $ExitCodeFile) { $exitCode = (Get-Content $ExitCodeFile -Raw).Trim() }
Write-Host "Exit code: $exitCode"
Write-Host "Combined log: $CombinedLog"
Write-Host "Git status:"
git status --short --branch
Write-Host "Tags:"
git tag --list
Write-Host "Release:"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
if (Test-Path $ReleaseDir) { Get-ChildItem $ReleaseDir -Recurse } else { Write-Host "$ReleaseDir not found." -ForegroundColor Yellow }

if ($exitCode -ne "0") {
    Write-Host "`nCodex exited with non-zero or unknown exit code. Check combined log above." -ForegroundColor Yellow
} else {
    Write-Host "`nCodex run finished with exit code 0." -ForegroundColor Green
}
