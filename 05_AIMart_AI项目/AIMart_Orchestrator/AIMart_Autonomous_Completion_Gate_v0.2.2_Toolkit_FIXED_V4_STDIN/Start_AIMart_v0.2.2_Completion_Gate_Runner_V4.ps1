$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.2.2"
$ToolkitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptPath = Join-Path $ToolkitRoot "codex\V0.2.2_AUTONOMOUS_COMPLETION_GATE_PROMPT_EN.md"
$RunDir = Join-Path $ProjectRoot "codex_runs\autonomous_v0_2_2_completion_gate_v4"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $RunDir "codex_v022_v4_$Timestamp.stdout.log"
$StderrLog = Join-Path $RunDir "codex_v022_v4_$Timestamp.stderr.log"
$CombinedLog = Join-Path $RunDir "codex_v022_v4_$Timestamp.combined.log"
$PidFile = Join-Path $RunDir "codex_v022_v4_$Timestamp.pid.txt"

function Write-Section($Text) {
    Write-Host "`n== $Text ==" -ForegroundColor Cyan
}

function Get-GitBranch {
    try { return ((git -C $ProjectRoot branch --show-current 2>$null) | Out-String).Trim() } catch { return "unknown" }
}

function Get-DirtyCount {
    try { return @((git -C $ProjectRoot status --short 2>$null)).Count } catch { return -1 }
}

function Get-ReleaseSummary {
    $ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    if (-not (Test-Path $ReleaseDir)) {
        return "$ReleaseDir not created yet."
    }
    return ((Get-ChildItem $ReleaseDir -Recurse | Select-Object Mode, LastWriteTime, Length, FullName | Out-String -Width 220).Trim())
}

function Get-RecentProgress {
    $Path = Join-Path $ProjectRoot "PROGRESS_LOG.md"
    if (-not (Test-Path $Path)) { return "PROGRESS_LOG.md not found." }
    return ((Get-Content $Path -Tail 8 -Encoding UTF8) -join "`n")
}

function Get-LogTail {
    if (-not (Test-Path $CombinedLog)) { return "Combined log not created yet." }
    return ((Get-Content $CombinedLog -Tail 25 -ErrorAction SilentlyContinue) -join "`n")
}

function Get-KnownIssuesSummary {
    $Path = Join-Path $ProjectRoot "V0.2.2_KNOWN_ISSUES.md"
    if (-not (Test-Path $Path)) { return "$Path not created yet." }
    return ((Get-Content $Path -Tail 20 -Encoding UTF8) -join "`n")
}

function Get-CompletionGateStatus {
    $ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $VerifyScript = Join-Path $ProjectRoot "scripts\verify-autonomous-completion.ps1"
    if ((Test-Path $ReleaseDir) -and (Test-Path $VerifyScript)) { return "READY_OR_COMPLETED" }
    return "RUNNING_OR_UNKNOWN"
}

function Show-Status($State, $ExitCode, $StartTime, $Process) {
    Clear-Host
    $Elapsed = (Get-Date) - $StartTime
    $CodexProcs = @(Get-Process codex -ErrorAction SilentlyContinue).Count
    $LogUpdated = "not created"
    $LogSize = 0
    if (Test-Path $CombinedLog) {
        $Item = Get-Item $CombinedLog
        $LogUpdated = $Item.LastWriteTime.ToString("HH:mm:ss")
        $LogSize = $Item.Length
    }

    Write-Host "AIMart Autonomous Completion Gate Runner V4" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Started        : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($Elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $State"
    Write-Host "Exit code      : $ExitCode"
    Write-Host "Git branch     : $(Get-GitBranch)"
    Write-Host "Dirty files    : $(Get-DirtyCount)"
    Write-Host "Codex procs    : $CodexProcs"
    Write-Host "Log updated    : $LogUpdated"
    Write-Host "Log size       : $LogSize bytes"
    Write-Host "CompletionGate : $(Get-CompletionGateStatus)"

    Write-Section "Release Output"
    Write-Host (Get-ReleaseSummary)

    Write-Section "Recent Progress"
    Write-Host (Get-RecentProgress)

    Write-Section "Latest Codex Log Tail"
    Write-Host (Get-LogTail)

    Write-Section "Known Issues"
    Write-Host (Get-KnownIssuesSummary)

    if ($State -eq "Running") {
        Write-Host "`nDo not close this window while running. Press Ctrl+C only if you want to stop the autonomous run." -ForegroundColor Yellow
    }
}

function Invoke-CodexAttemptWithCmd($Name, [string[]]$Args) {
    $CmdLine = '"' + $CodexExe + '" ' + (($Args | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"','\"') + '"' } else { $_ } }) -join ' ') + ' < "' + $PromptPath + '" > "' + $StdoutLog + '" 2> "' + $StderrLog + '"'
    "== Attempt: $Name ==" | Set-Content $CombinedLog -Encoding UTF8
    "Command: $CmdLine" | Add-Content $CombinedLog -Encoding UTF8

    $StartTime = Get-Date
    $Proc = Start-Process -FilePath "cmd.exe" -ArgumentList @('/c', $CmdLine) -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru
    $Proc.Id | Set-Content $PidFile -Encoding UTF8

    while (-not $Proc.HasExited) {
        if (Test-Path $StdoutLog) { "`n--- STDOUT ---" | Set-Content $CombinedLog -Encoding UTF8; Get-Content $StdoutLog -ErrorAction SilentlyContinue | Add-Content $CombinedLog -Encoding UTF8 }
        if (Test-Path $StderrLog) { "`n--- STDERR ---" | Add-Content $CombinedLog -Encoding UTF8; Get-Content $StderrLog -ErrorAction SilentlyContinue | Add-Content $CombinedLog -Encoding UTF8 }
        Show-Status "Running" "running" $StartTime $Proc
        Start-Sleep -Seconds 5
        $Proc.Refresh()
    }

    if (Test-Path $StdoutLog) { "`n--- STDOUT ---" | Set-Content $CombinedLog -Encoding UTF8; Get-Content $StdoutLog -ErrorAction SilentlyContinue | Add-Content $CombinedLog -Encoding UTF8 }
    if (Test-Path $StderrLog) { "`n--- STDERR ---" | Add-Content $CombinedLog -Encoding UTF8; Get-Content $StderrLog -ErrorAction SilentlyContinue | Add-Content $CombinedLog -Encoding UTF8 }
    Show-Status "Finished" $Proc.ExitCode $StartTime $Proc
    return $Proc.ExitCode
}

Write-Section "Preflight"
if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path $PromptPath)) { throw "Prompt file not found: $PromptPath" }

$CodexCmd = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $CodexCmd) { $CodexCmd = Get-Command codex -ErrorAction SilentlyContinue }
if (-not $CodexCmd) { throw "Codex executable not found in PATH." }
$CodexExe = $CodexCmd.Source
Write-Host "Codex executable: $CodexExe"

Set-Location -LiteralPath $ProjectRoot
$Branch = Get-GitBranch
Write-Host "Current branch: $Branch"
$DirtyBefore = Get-DirtyCount
Write-Host "Dirty files before start: $DirtyBefore"
if ($DirtyBefore -ne 0) {
    Write-Host "The working tree is not clean. To prevent mixing versions, this runner will stop." -ForegroundColor Red
    Write-Host "Commit or stash existing changes first." -ForegroundColor Yellow
    exit 3
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

# Primary form: codex exec -c ... -  (stdin prompt)
$ExitCode = Invoke-CodexAttemptWithCmd "exec-config-stdin" @('exec','-c','approval_policy=never','-c','sandbox_mode=workspace-write','-')

# Fallback form: codex -c ... exec -  (stdin prompt)
if ($ExitCode -ne 0) {
    Write-Host "Primary attempt failed with exit code $ExitCode. Trying fallback argument order..." -ForegroundColor Yellow
    $StdoutLog = Join-Path $RunDir "codex_v022_v4_${Timestamp}_fallback.stdout.log"
    $StderrLog = Join-Path $RunDir "codex_v022_v4_${Timestamp}_fallback.stderr.log"
    $CombinedLog = Join-Path $RunDir "codex_v022_v4_${Timestamp}_fallback.combined.log"
    $ExitCode = Invoke-CodexAttemptWithCmd "global-config-exec-stdin" @('-c','approval_policy=never','-c','sandbox_mode=workspace-write','exec','-')
}

Write-Section "Post-run summary"
git -C $ProjectRoot status --short --branch
Write-Host "`nTags:"
git -C $ProjectRoot tag --list
Write-Host "`nRelease:"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
if (Test-Path $ReleaseDir) { Get-ChildItem $ReleaseDir -Recurse } else { Write-Host "releases\$TargetVersion not found." -ForegroundColor Yellow }
Write-Host "`nLast exit code: $ExitCode"
Write-Host "Combined log: $CombinedLog"

if ($ExitCode -ne 0) { exit $ExitCode }
