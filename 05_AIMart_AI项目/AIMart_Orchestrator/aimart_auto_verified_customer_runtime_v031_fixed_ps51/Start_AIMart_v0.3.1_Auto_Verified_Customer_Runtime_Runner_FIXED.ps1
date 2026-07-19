param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.3.1",
    [string]$TargetBranch = "feature/v0.3.1-auto-verified-customer-runtime"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptFile = Join-Path $ScriptRoot "codex\V0.3.1_AUTO_VERIFIED_CUSTOMER_RUNTIME_PROMPT_EN.md"
$RunRoot = Join-Path $ProjectRoot "codex_runs\autonomous_v0_3_1_customer_runtime_fixed_ps51"
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $RunRoot "codex_v031_$Stamp.stdout.log"
$StderrLog = Join-Path $RunRoot "codex_v031_$Stamp.stderr.log"
$CombinedLog = Join-Path $RunRoot "codex_v031_$Stamp.combined.log"
$CmdFile = Join-Path $RunRoot "run_codex_v031_$Stamp.cmd"

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Get-GitStatusShort {
    Push-Location $ProjectRoot
    try { return (git status --short | Out-String).Trim() } finally { Pop-Location }
}

function Get-Branch {
    Push-Location $ProjectRoot
    try { return (git branch --show-current).Trim() } finally { Pop-Location }
}

function Show-State([System.Diagnostics.Process]$Proc) {
    Clear-Host
    $elapsed = (Get-Date) - $StartTime
    $branch = Get-Branch
    $dirty = (git -C $ProjectRoot status --short | Measure-Object -Line).Lines
    $releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $knownIssues = Join-Path $ProjectRoot "V0.3.1_KNOWN_ISSUES.md"
    $stdoutInfo = if (Test-Path $StdoutLog) { Get-Item $StdoutLog } else { $null }
    $stderrInfo = if (Test-Path $StderrLog) { Get-Item $StderrLog } else { $null }
    $logSize = 0
    $logTime = "not created yet"
    if ($stdoutInfo) { $logSize += $stdoutInfo.Length; $logTime = $stdoutInfo.LastWriteTime.ToString("HH:mm:ss") }
    if ($stderrInfo) { $logSize += $stderrInfo.Length; $logTime = $stderrInfo.LastWriteTime.ToString("HH:mm:ss") }
    $state = if ($Proc -and -not $Proc.HasExited) { "Running" } elseif ($Proc) { "Finished" } else { "Not started" }
    $exit = if ($Proc -and $Proc.HasExited) { $Proc.ExitCode } elseif ($Proc) { "running" } else { "unknown" }

    Write-Host "AIMart v0.3.1 Auto-Verified Customer Runtime Runner" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Started        : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $state"
    Write-Host "Exit code      : $exit"
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirty"
    Write-Host "Log updated    : $logTime"
    Write-Host "Log size       : $logSize bytes"

    Write-Section "Release Output"
    if (Test-Path $releaseDir) { Get-ChildItem $releaseDir -Recurse | Select-Object Mode,LastWriteTime,Length,Name | Format-Table -AutoSize } else { Write-Host "$releaseDir not created yet." -ForegroundColor Yellow }

    Write-Section "Latest STDOUT Tail"
    if (Test-Path $StdoutLog) { Get-Content $StdoutLog -Tail 15 }
    Write-Section "Latest STDERR Tail"
    if (Test-Path $StderrLog) { Get-Content $StderrLog -Tail 15 }

    Write-Section "Known Issues"
    if (Test-Path $knownIssues) { Get-Content $knownIssues -Tail 20 } else { Write-Host "$knownIssues not created yet." -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Do not close this window while running. Ctrl+C stops only this runner." -ForegroundColor DarkYellow
}

Write-Section "Preflight"
$CodexExe = (Get-Command codex.exe -ErrorAction SilentlyContinue).Source
if (-not $CodexExe) { $CodexExe = (Get-Command codex -ErrorAction Stop).Source }
Write-Host "Codex executable: $CodexExe"
if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path $PromptFile)) { throw "Prompt file not found: $PromptFile" }

Push-Location $ProjectRoot
try {
    $status = (git status --short | Out-String).Trim()
    $branch = (git branch --show-current).Trim()
    Write-Host "Current branch: $branch"
    Write-Host "Dirty files before start: $((git status --short | Measure-Object -Line).Lines)"
    if ($status) {
        Write-Host "Working tree is not clean. Runner will stop to prevent mixing versions." -ForegroundColor Red
        git status --short --branch
        exit 10
    }
    $tagCheck = (git show --no-patch --oneline v0.3.0 2>$null | Out-String).Trim()
    if (-not $tagCheck) { throw "Required base tag v0.3.0 was not found." }
    if ($branch -ne $TargetBranch) {
        $existing = (git branch --list $TargetBranch | Out-String).Trim()
        if ($existing) { git checkout $TargetBranch | Out-Null } else { git checkout -b $TargetBranch | Out-Null }
    }
}
finally { Pop-Location }

# Build a CMD wrapper that works in Windows PowerShell 5.1.
# It avoids ProcessStartInfo.ArgumentList and passes the prompt through stdin to `codex exec -`.
$cmdText = @"
@echo off
setlocal
cd /d "$ProjectRoot"
type "$PromptFile" | "$CodexExe" --cd "$ProjectRoot" -c approval_policy=never -c sandbox_mode=workspace-write exec - > "$StdoutLog" 2> "$StderrLog"
set CODEX_EXIT=%ERRORLEVEL%
type "$StdoutLog" > "$CombinedLog"
echo. >> "$CombinedLog"
echo --- STDERR --- >> "$CombinedLog"
type "$StderrLog" >> "$CombinedLog"
exit /b %CODEX_EXIT%
"@
$cmdText | Set-Content -Path $CmdFile -Encoding ASCII

$StartTime = Get-Date
Write-Section "Starting Codex"
Write-Host "CMD wrapper: $CmdFile"
$Proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$CmdFile`"" -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden

while (-not $Proc.HasExited) {
    Show-State $Proc
    Start-Sleep -Seconds 5
    $Proc.Refresh()
}

Show-State $Proc
Write-Section "Post-run Summary"
Push-Location $ProjectRoot
try {
    git status --short --branch
    Write-Host ""
    Write-Host "Tags:"
    git tag --list
    Write-Host ""
    Write-Host "Release:"
    $rel = Join-Path $ProjectRoot "releases\$TargetVersion"
    if (Test-Path $rel) { Get-ChildItem $rel -Recurse } else { Write-Host "releases\$TargetVersion not found." -ForegroundColor Red }
    Write-Host ""
    Write-Host "Exit code: $($Proc.ExitCode)"
    Write-Host "Combined log: $CombinedLog"
}
finally { Pop-Location }

if ($Proc.ExitCode -ne 0) {
    Write-Host "Codex exited with non-zero code. Review the combined log." -ForegroundColor Red
    exit $Proc.ExitCode
}
