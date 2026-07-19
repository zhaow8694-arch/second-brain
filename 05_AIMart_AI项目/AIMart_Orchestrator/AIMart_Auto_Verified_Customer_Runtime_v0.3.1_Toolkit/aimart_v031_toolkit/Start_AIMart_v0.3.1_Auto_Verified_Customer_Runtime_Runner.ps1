param(
    [switch]$AllowDirtyStart
)

$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$TargetBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$ToolkitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptFile = Join-Path $ToolkitRoot "codex\V0.3.1_AUTO_VERIFIED_CUSTOMER_RUNTIME_PROMPT_EN.md"
$LogRoot = Join-Path $ProjectRoot "codex_runs\autonomous_v0_3_1_auto_verified_customer_runtime"
$StartedAt = Get-Date
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $LogRoot "codex_v031_$Stamp.stdout.log"
$StderrLog = Join-Path $LogRoot "codex_v031_$Stamp.stderr.log"
$CombinedLog = Join-Path $LogRoot "codex_v031_$Stamp.combined.log"

function Invoke-GitText($Arguments) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "git"
    foreach ($arg in $Arguments) { [void]$psi.ArgumentList.Add($arg) }
    $psi.WorkingDirectory = $ProjectRoot
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    return ($out + $err).Trim()
}

function Get-GitBranch { Invoke-GitText @("branch", "--show-current") }
function Get-GitStatusShort { Invoke-GitText @("status", "--short", "--branch") }
function Get-GitDirtyCount {
    $status = Invoke-GitText @("status", "--short")
    if ([string]::IsNullOrWhiteSpace($status)) { return 0 }
    return ($status -split "`n" | Where-Object { $_.Trim().Length -gt 0 }).Count
}

function Show-State($Job, $Process) {
    Clear-Host
    $elapsed = (Get-Date) - $StartedAt
    $branch = Get-GitBranch
    $dirty = Get-GitDirtyCount
    $releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $sampleZip = Join-Path $releaseDir "samples\todo-api-generated-execution-pack.zip"
    $knownIssues = Join-Path $ProjectRoot "V0.3.1_KNOWN_ISSUES.md"
    $finalCheck = Join-Path $ProjectRoot "V0.3.1_FINAL_DELIVERY_CHECK.md"
    $gate = "RUNNING_OR_UNKNOWN"
    if (Test-Path $knownIssues) {
        $kiText = Get-Content $knownIssues -Raw -ErrorAction SilentlyContinue
        if ($kiText -match "PASS") { $gate = "PASS_OR_PARTIAL_PASS" }
        if ($kiText -match "FAIL|P0|P1|BLOCKER") { $gate = "FAIL_OR_NEEDS_REVIEW" }
    }
    if (Test-Path $finalCheck) {
        $fcText = Get-Content $finalCheck -Raw -ErrorAction SilentlyContinue
        if ($fcText -match "Autonomous Completion Gate.*PASS|Completion Gate status: PASS") { $gate = "PASS" }
    }

    $codexCount = (Get-Process codex -ErrorAction SilentlyContinue | Measure-Object).Count
    $logUpdated = "not yet"
    $logSize = 0
    if (Test-Path $CombinedLog) {
        $logItem = Get-Item $CombinedLog
        $logUpdated = $logItem.LastWriteTime.ToString("HH:mm:ss")
        $logSize = $logItem.Length
    }

    Write-Host "AIMart Auto-Verified Customer Runtime Runner" -ForegroundColor Cyan
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Started        : $($StartedAt.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $($Job.State)"
    if ($Process) { Write-Host "Process id     : $($Process.Id)" }
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirty"
    Write-Host "Codex procs    : $codexCount"
    Write-Host "Log updated    : $logUpdated"
    Write-Host "Log size       : $logSize bytes"
    Write-Host "CompletionGate : $gate"

    Write-Host "`n== Release Output ==" -ForegroundColor Cyan
    if (Test-Path $releaseDir) {
        Get-ChildItem $releaseDir -Recurse | Select-Object Mode, LastWriteTime, Length, FullName | Format-Table -AutoSize
    } else {
        Write-Host "$releaseDir not created yet." -ForegroundColor Yellow
    }
    if (Test-Path $sampleZip) {
        Write-Host "Sample execution pack: present" -ForegroundColor Green
    } else {
        Write-Host "Sample execution pack: not found yet" -ForegroundColor Yellow
    }

    Write-Host "`n== Latest Log Tail ==" -ForegroundColor Cyan
    if (Test-Path $CombinedLog) {
        Get-Content $CombinedLog -Tail 30 -ErrorAction SilentlyContinue
    } else {
        Write-Host "Log not created yet." -ForegroundColor Yellow
    }

    Write-Host "`nDo not close this window while running. Ctrl+C stops only this runner." -ForegroundColor DarkYellow
}

if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path $PromptFile)) { throw "Prompt file not found: $PromptFile" }

Set-Location -LiteralPath $ProjectRoot
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

$CodexExe = (Get-Command codex.exe -ErrorAction SilentlyContinue).Source
if (-not $CodexExe) { $CodexExe = (Get-Command codex -ErrorAction SilentlyContinue).Source }
if (-not $CodexExe) { throw "Codex executable not found in PATH." }

Write-Host "== Preflight ==" -ForegroundColor Cyan
Write-Host "Codex executable: $CodexExe"
Write-Host "Current branch: $(Get-GitBranch)"
Write-Host "Dirty files before start: $(Get-GitDirtyCount)"

$tagCheck = Invoke-GitText @("show", "--no-patch", "--oneline", "v0.3.0")
if ([string]::IsNullOrWhiteSpace($tagCheck)) { throw "Required tag v0.3.0 not found." }

$currentBranch = Get-GitBranch
if ($currentBranch -ne $TargetBranch) {
    $branches = Invoke-GitText @("branch", "--list", $TargetBranch)
    if ([string]::IsNullOrWhiteSpace($branches)) {
        Write-Host "Creating branch $TargetBranch from current HEAD..." -ForegroundColor Cyan
        git checkout -b $TargetBranch | Out-Host
    } else {
        Write-Host "Switching to existing branch $TargetBranch..." -ForegroundColor Cyan
        git checkout $TargetBranch | Out-Host
    }
}

$dirtyCount = Get-GitDirtyCount
if ($dirtyCount -gt 0 -and -not $AllowDirtyStart) {
    Write-Host "`nThe working tree is not clean. To prevent mixing versions, this runner will stop." -ForegroundColor Red
    Write-Host "Commit or stash existing changes first, or rerun with -AllowDirtyStart only if intentional." -ForegroundColor Yellow
    exit 10
}

$PromptText = Get-Content -LiteralPath $PromptFile -Raw
$CodexArgs = @("--cd", $ProjectRoot, "-c", "approval_policy=never", "-c", "sandbox_mode=workspace-write", "exec", "-")

$Job = Start-Job -ArgumentList $CodexExe, $CodexArgs, $PromptText, $StdoutLog, $StderrLog, $CombinedLog -ScriptBlock {
    param($CodexExe, $CodexArgs, $PromptText, $StdoutLog, $StderrLog, $CombinedLog)
    "== Codex command ==" | Set-Content -Encoding UTF8 $CombinedLog
    ($CodexExe + " " + ($CodexArgs -join " ")) | Add-Content -Encoding UTF8 $CombinedLog
    "== STDOUT / STDERR will be merged after process exits ==" | Add-Content -Encoding UTF8 $CombinedLog
    $PromptText | & $CodexExe @CodexArgs > $StdoutLog 2> $StderrLog
    $code = $LASTEXITCODE
    "`n--- STDOUT ---" | Add-Content -Encoding UTF8 $CombinedLog
    if (Test-Path $StdoutLog) { Get-Content $StdoutLog | Add-Content -Encoding UTF8 $CombinedLog }
    "`n--- STDERR ---" | Add-Content -Encoding UTF8 $CombinedLog
    if (Test-Path $StderrLog) { Get-Content $StderrLog | Add-Content -Encoding UTF8 $CombinedLog }
    exit $code
}

$Process = $null
Start-Sleep -Seconds 1
try {
    $child = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match [regex]::Escape($CodexExe) -and $_.CommandLine -match "exec" } | Sort-Object CreationDate -Descending | Select-Object -First 1
    if ($child) { $Process = Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
} catch {}

while ($Job.State -eq "Running") {
    Show-State $Job $Process
    Start-Sleep -Seconds 5
}

Receive-Job $Job -Keep | Out-Null
Show-State $Job $Process

Write-Host "`n== Post-run Summary ==" -ForegroundColor Cyan
git status --short --branch | Out-Host
Write-Host "Tags:" -ForegroundColor Cyan
git tag --list | Out-Host
$releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
if (Test-Path $releaseDir) {
    Write-Host "Release:" -ForegroundColor Cyan
    Get-ChildItem $releaseDir -Recurse | Out-Host
} else {
    Write-Host "Release directory not found: $releaseDir" -ForegroundColor Red
}
Write-Host "Combined log: $CombinedLog"
Write-Host "Runner finished. Press any key to close this window."
