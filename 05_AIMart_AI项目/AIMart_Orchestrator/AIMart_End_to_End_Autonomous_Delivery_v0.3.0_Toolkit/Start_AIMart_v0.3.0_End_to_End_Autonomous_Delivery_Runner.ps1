param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.3.0",
    [string]$TargetBranch = "feature/v0.3.0-end-to-end-autonomous-delivery",
    [switch]$AllowDirtyStart
)

$ErrorActionPreference = "Stop"
$RunnerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptFile = Join-Path $RunnerRoot "codex\V0.3.0_END_TO_END_AUTONOMOUS_DELIVERY_PROMPT_EN.md"

function Write-Section($Text) {
    Write-Host "`n== $Text ==" -ForegroundColor Cyan
}

function Get-ShortGitStatus {
    try {
        return (git -C $ProjectRoot status --short | Out-String).Trim()
    } catch {
        return "git status unavailable: $($_.Exception.Message)"
    }
}

function Get-CurrentBranch {
    try { return (git -C $ProjectRoot branch --show-current).Trim() } catch { return "unknown" }
}

function Get-DirtyCount {
    $s = Get-ShortGitStatus
    if ([string]::IsNullOrWhiteSpace($s)) { return 0 }
    return ($s -split "`n" | Where-Object { $_.Trim() }).Count
}

function Show-FileTail($Path, $Lines = 18) {
    if (Test-Path $Path) {
        Get-Content -LiteralPath $Path -Tail $Lines -ErrorAction SilentlyContinue
    }
}

function Get-CompletionGateStatus {
    $finalCheck = Join-Path $ProjectRoot "V0.3.0_FINAL_DELIVERY_CHECK.md"
    $known = Join-Path $ProjectRoot "V0.3.0_KNOWN_ISSUES.md"
    if (Test-Path $known) {
        $text = Get-Content -LiteralPath $known -Raw -ErrorAction SilentlyContinue
        if ($text -match "Completion Gate status:\s*PASS" -or $text -match "Autonomous Completion Gate.*PASS") { return "PASS" }
        if ($text -match "Completion Gate status:\s*FAIL" -or $text -match "Autonomous Completion Gate.*FAIL") { return "FAIL" }
    }
    if (Test-Path $finalCheck) {
        $text = Get-Content -LiteralPath $finalCheck -Raw -ErrorAction SilentlyContinue
        if ($text -match "Completion Gate.*PASS") { return "PASS" }
        if ($text -match "Completion Gate.*FAIL") { return "FAIL" }
    }
    return "RUNNING_OR_UNKNOWN"
}

function Show-Status($StartTime, $Process, $StdoutLog, $StderrLog, $CombinedLog) {
    Clear-Host
    $elapsed = New-TimeSpan -Start $StartTime -End (Get-Date)
    $branch = Get-CurrentBranch
    $dirty = Get-DirtyCount
    $releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $sampleZip = Join-Path $releaseDir "samples\todo-api-generated-execution-pack.zip"
    $gate = Get-CompletionGateStatus
    $codexCount = @(Get-Process codex -ErrorAction SilentlyContinue).Count + @(Get-Process Codex -ErrorAction SilentlyContinue).Count
    $logUpdated = "none"
    $logSize = 0
    if (Test-Path $CombinedLog) {
        $li = Get-Item $CombinedLog
        $logUpdated = $li.LastWriteTime.ToString("HH:mm:ss")
        $logSize = $li.Length
    }
    $state = if ($Process -and -not $Process.HasExited) { "Running" } elseif ($Process) { "Finished" } else { "NotStarted" }
    $exit = if ($Process -and $Process.HasExited) { $Process.ExitCode } else { "running" }

    Write-Host "AIMart End-to-End Autonomous Delivery Runner" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Started        : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $state"
    Write-Host "Exit code      : $exit"
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirty"
    Write-Host "Codex procs    : $codexCount"
    Write-Host "Log updated    : $logUpdated"
    Write-Host "Log size       : $logSize bytes"
    Write-Host "CompletionGate : $gate"

    Write-Section "Release Output"
    if (Test-Path $releaseDir) {
        Get-ChildItem $releaseDir -Recurse | Select-Object Mode, LastWriteTime, Length, FullName | Format-Table -AutoSize
    } else {
        Write-Host "$releaseDir not created yet." -ForegroundColor Yellow
    }
    if (Test-Path $sampleZip) {
        Write-Host "Sample execution pack: found" -ForegroundColor Green
    } else {
        Write-Host "Sample execution pack: not found yet" -ForegroundColor Yellow
    }

    Write-Section "Recent Progress"
    $progress = Join-Path $ProjectRoot "PROGRESS_LOG.md"
    if (Test-Path $progress) { Get-Content $progress -Tail 10 -Encoding UTF8 } else { Write-Host "PROGRESS_LOG.md not found." }

    Write-Section "Latest STDOUT Tail"
    Show-FileTail $StdoutLog 12

    Write-Section "Latest STDERR Tail"
    Show-FileTail $StderrLog 18

    Write-Section "Known Issues"
    $known = Join-Path $ProjectRoot "V0.3.0_KNOWN_ISSUES.md"
    if (Test-Path $known) { Get-Content $known -Tail 20 -Encoding UTF8 } else { Write-Host "$known not created yet." -ForegroundColor Yellow }

    Write-Host "`nDo not close this window while running. Ctrl+C stops only this runner." -ForegroundColor DarkYellow
}

# Preflight
if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path $PromptFile)) { throw "Prompt file not found: $PromptFile" }

$CodexCmd = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $CodexCmd) { $CodexCmd = Get-Command codex -ErrorAction SilentlyContinue }
if (-not $CodexCmd) { throw "Codex CLI not found in PATH." }
$CodexExe = $CodexCmd.Source

Write-Section "Preflight"
Write-Host "Codex executable: $CodexExe"
Write-Host "Project root: $ProjectRoot"
Write-Host "Target version: $TargetVersion"

$currentBranch = Get-CurrentBranch
$dirtyBefore = Get-DirtyCount
Write-Host "Current branch: $currentBranch"
Write-Host "Dirty files before start: $dirtyBefore"

if ($dirtyBefore -gt 0 -and -not $AllowDirtyStart) {
    Write-Host "`nThe working tree is not clean. To prevent mixing versions, this runner will stop." -ForegroundColor Red
    Write-Host "Commit or stash existing changes first, or rerun with -AllowDirtyStart only if intentional." -ForegroundColor Yellow
    exit 10
}

$tags = git -C $ProjectRoot tag --list
if ($tags -notcontains "v0.2.2") {
    Write-Host "v0.2.2 tag not found. v0.3.0 should start after v0.2.2 is frozen." -ForegroundColor Red
    exit 11
}

# Branch setup
$branches = git -C $ProjectRoot branch --list $TargetBranch
if ($currentBranch -ne $TargetBranch) {
    if ($branches) {
        git -C $ProjectRoot checkout $TargetBranch | Out-Host
    } else {
        git -C $ProjectRoot checkout -b $TargetBranch | Out-Host
    }
}

$LogDir = Join-Path $ProjectRoot "codex_runs\autonomous_v0_3_0_end_to_end_delivery"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $LogDir "codex_v030_$Timestamp.stdout.log"
$StderrLog = Join-Path $LogDir "codex_v030_$Timestamp.stderr.log"
$CombinedLog = Join-Path $LogDir "codex_v030_$Timestamp.combined.log"
$InvokeScript = Join-Path $LogDir "invoke_codex_v030_$Timestamp.ps1"

$invokeContent = @"
`$ErrorActionPreference = 'Continue'
`$prompt = Get-Content -LiteralPath '$PromptFile' -Raw
`$prompt | & '$CodexExe' --cd '$ProjectRoot' -c 'approval_policy="never"' -c 'sandbox_mode="workspace-write"' exec - 1> '$StdoutLog' 2> '$StderrLog'
`$code = `$LASTEXITCODE
"=== STDOUT ===" | Set-Content -Path '$CombinedLog' -Encoding UTF8
if (Test-Path '$StdoutLog') { Get-Content '$StdoutLog' | Add-Content -Path '$CombinedLog' -Encoding UTF8 }
"`n=== STDERR ===" | Add-Content -Path '$CombinedLog' -Encoding UTF8
if (Test-Path '$StderrLog') { Get-Content '$StderrLog' | Add-Content -Path '$CombinedLog' -Encoding UTF8 }
exit `$code
"@
$invokeContent | Set-Content -LiteralPath $InvokeScript -Encoding UTF8

Write-Section "Starting Codex"
Write-Host "Prompt file : $PromptFile"
Write-Host "Stdout log  : $StdoutLog"
Write-Host "Stderr log  : $StderrLog"
Write-Host "Combined log: $CombinedLog"
Write-Host "Mode        : codex exec - via STDIN, approval never, workspace-write"

$StartTime = Get-Date
$proc = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $InvokeScript) -PassThru -WindowStyle Hidden

while (-not $proc.HasExited) {
    Show-Status $StartTime $proc $StdoutLog $StderrLog $CombinedLog
    Start-Sleep -Seconds 5
    $proc.Refresh()
}

Show-Status $StartTime $proc $StdoutLog $StderrLog $CombinedLog

Write-Section "Post-run Summary"
git -C $ProjectRoot status --short --branch
Write-Host "Tags:"
git -C $ProjectRoot tag --list
Write-Host "Release:"
$releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
if (Test-Path $releaseDir) { Get-ChildItem $releaseDir -Recurse } else { Write-Host "releases\$TargetVersion not found." -ForegroundColor Yellow }
Write-Host "Combined log: $CombinedLog"
Write-Host "Exit code   : $($proc.ExitCode)"
if ($proc.ExitCode -ne 0) { exit $proc.ExitCode }
