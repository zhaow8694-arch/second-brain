$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.2"
$PreviousVersion = "v0.3.1"
$TargetBranch = "feature/v0.3.2-autonomous-runner-hardening"
$ToolkitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptPath = Join-Path $ToolkitRoot "codex\V0.3.2_AUTONOMOUS_RUNNER_HARDENING_PROMPT_EN.md"
$RunRoot = Join-Path $ProjectRoot "codex_runs\autonomous_v0_3_2_runner_hardening"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $RunRoot "codex_v032_${Timestamp}.stdout.log"
$StderrLog = Join-Path $RunRoot "codex_v032_${Timestamp}.stderr.log"
$CombinedLog = Join-Path $RunRoot "codex_v032_${Timestamp}.combined.log"
$WrapperCmd = Join-Path $RunRoot "run_codex_v032_${Timestamp}.cmd"

function Write-Section([string]$Title) {
    Write-Host "`n== $Title ==" -ForegroundColor Cyan
}

function Require-Path([string]$Label, [string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing ${Label}: ${Path}"
    }
}

function Get-GitText([string]$Args) {
    $out = cmd.exe /d /c "git $Args" 2>&1
    return @($out)
}

function Show-Status([string]$State, [int]$ElapsedSeconds = 0) {
    $branch = (cmd.exe /d /c "git branch --show-current" 2>$null | Out-String).Trim()
    $dirty = @(cmd.exe /d /c "git status --short" 2>$null).Count
    $releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $sampleZip = Join-Path $releaseDir "samples\todo-api-generated-execution-pack.zip"
    $sourceZip = Join-Path $releaseDir "aimart-orchestrator-v0.3.2-source.zip"
    $logInfo = "not created"
    if (Test-Path $CombinedLog) {
        $item = Get-Item $CombinedLog
        $logInfo = "$($item.LastWriteTime.ToString('HH:mm:ss')) / $($item.Length) bytes"
    }
    Clear-Host
    Write-Host "AIMart v0.3.2 Autonomous Runner Hardening" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Previous       : $PreviousVersion"
    Write-Host "Started        : $Timestamp"
    Write-Host "Elapsed        : $ElapsedSeconds sec"
    Write-Host "State          : $State"
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirty"
    Write-Host "Log            : $logInfo"
    Write-Host "Release dir    : $(if (Test-Path $releaseDir) { 'exists' } else { 'not created yet' })"
    Write-Host "Source ZIP     : $(if (Test-Path $sourceZip) { 'exists' } else { 'not found yet' })"
    Write-Host "Sample ZIP     : $(if (Test-Path $sampleZip) { 'exists' } else { 'not found yet' })"
    if (Test-Path $CombinedLog) {
        Write-Host "`n== Latest log tail ==" -ForegroundColor Cyan
        Get-Content $CombinedLog -Tail 24 -ErrorAction SilentlyContinue
    }
    Write-Host "`nDo not close this window while running. Ctrl+C stops only this runner."
}

Write-Host "AIMart v0.3.2 Autonomous Runner Hardening" -ForegroundColor Green
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"

Write-Section "Preflight"
Require-Path "project root" $ProjectRoot
Require-Path "prompt" $PromptPath
Set-Location -LiteralPath $ProjectRoot

$Codex = (Get-Command codex -ErrorAction SilentlyContinue)
if (-not $Codex) {
    $CodexExe = "C:\Users\Administrator\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe"
    Require-Path "Codex executable" $CodexExe
} else {
    $CodexExe = $Codex.Source
}
Write-Host "Codex executable: $CodexExe"

$branch = (cmd.exe /d /c "git branch --show-current" | Out-String).Trim()
$dirtyBefore = @(cmd.exe /d /c "git status --short").Count
Write-Host "Current branch: $branch"
Write-Host "Dirty files before start: $dirtyBefore"
if ($dirtyBefore -ne 0) {
    throw "Working tree is not clean. Freeze or stash existing changes before starting $TargetVersion."
}

$previousTag = (cmd.exe /d /c "git tag --list $PreviousVersion" | Out-String).Trim()
if (-not $previousTag) {
    throw "Required previous tag $PreviousVersion not found."
}
$head = (cmd.exe /d /c "git rev-parse HEAD" | Out-String).Trim()
$prev = (cmd.exe /d /c "git rev-parse $PreviousVersion" | Out-String).Trim()
if ($head -ne $prev) {
    throw "HEAD does not point to $PreviousVersion. HEAD=$head $PreviousVersion=$prev"
}

foreach ($Path in @(
    "releases\v0.3.1\aimart-orchestrator-v0.3.1-source.zip",
    "releases\v0.3.1\samples\todo-api-generated-execution-pack.zip",
    "releases\v0.3.1\SHA256.txt",
    "releases\v0.3.1\RELEASE_MANIFEST.txt",
    "releases\v0.3.1\dogfood\CUSTOMER_PACK_RUNTIME_VALIDATION.md"
)) {
    Require-Path "v0.3.1 frozen artifact" (Join-Path $ProjectRoot $Path)
}

if ($branch -ne $TargetBranch) {
    $existing = (cmd.exe /d /c "git branch --list $TargetBranch" | Out-String).Trim()
    if ($existing) {
        Write-Host "Switching to existing branch $TargetBranch"
        cmd.exe /d /c "git checkout $TargetBranch" | Write-Host
    } else {
        Write-Host "Creating branch $TargetBranch"
        cmd.exe /d /c "git checkout -b $TargetBranch" | Write-Host
    }
}

New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null

Write-Section "Start Codex"
$PromptEsc = $PromptPath.Replace('^','^^').Replace('&','^&')
$CodexEsc = $CodexExe.Replace('^','^^').Replace('&','^&')
$ProjectEsc = $ProjectRoot.Replace('^','^^').Replace('&','^&')
$StdoutEsc = $StdoutLog.Replace('^','^^').Replace('&','^&')
$StderrEsc = $StderrLog.Replace('^','^^').Replace('&','^&')
$Wrapper = @"
@echo off
cd /d "$ProjectEsc"
type "$PromptEsc" | "$CodexEsc" --cd "$ProjectEsc" -c approval_policy="never" -c sandbox_mode="workspace-write" exec - > "$StdoutEsc" 2> "$StderrEsc"
exit /b %ERRORLEVEL%
"@
Set-Content -Path $WrapperCmd -Value $Wrapper -Encoding ASCII

$Process = Start-Process -FilePath "cmd.exe" -ArgumentList @('/d','/c', $WrapperCmd) -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden
$start = Get-Date
$lastLength = -1
$stallCount = 0
while (-not $Process.HasExited) {
    if (Test-Path $StdoutLog -or Test-Path $StderrLog) {
        $parts = @()
        if (Test-Path $StdoutLog) { $parts += "--- STDOUT ---"; $parts += (Get-Content $StdoutLog -Tail 80 -ErrorAction SilentlyContinue) }
        if (Test-Path $StderrLog) { $parts += "--- STDERR ---"; $parts += (Get-Content $StderrLog -Tail 80 -ErrorAction SilentlyContinue) }
        $parts | Set-Content -Encoding UTF8 $CombinedLog
    }
    $elapsed = [int]((Get-Date) - $start).TotalSeconds
    Show-Status "Running" $elapsed
    if (Test-Path $CombinedLog) {
        $len = (Get-Item $CombinedLog).Length
        if ($len -eq $lastLength) { $stallCount++ } else { $stallCount = 0; $lastLength = $len }
        if ($stallCount -gt 120) { Write-Host "Potential stall: log unchanged for a long time." -ForegroundColor Yellow }
    }
    Start-Sleep -Seconds 5
    $Process.Refresh()
}

if (Test-Path $StdoutLog -or Test-Path $StderrLog) {
    $parts = @()
    if (Test-Path $StdoutLog) { $parts += "--- STDOUT ---"; $parts += (Get-Content $StdoutLog -Tail 200 -ErrorAction SilentlyContinue) }
    if (Test-Path $StderrLog) { $parts += "--- STDERR ---"; $parts += (Get-Content $StderrLog -Tail 200 -ErrorAction SilentlyContinue) }
    $parts | Set-Content -Encoding UTF8 $CombinedLog
}

Show-Status "Finished" ([int]((Get-Date) - $start).TotalSeconds)
Write-Host "`n== Codex exit code ==" -ForegroundColor Cyan
Write-Host $Process.ExitCode
Write-Host "Combined log: $CombinedLog"

Write-Host "`n== Post-run summary ==" -ForegroundColor Cyan
cmd.exe /d /c "git status --short --branch"
cmd.exe /d /c "git tag --list"
if (Test-Path (Join-Path $ProjectRoot "releases\v0.3.2")) {
    Get-ChildItem (Join-Path $ProjectRoot "releases\v0.3.2") -Recurse
} else {
    Write-Host "releases\v0.3.2 not found yet." -ForegroundColor Yellow
}

if ($Process.ExitCode -ne 0) {
    throw "Codex exited with code $($Process.ExitCode). See $CombinedLog"
}
