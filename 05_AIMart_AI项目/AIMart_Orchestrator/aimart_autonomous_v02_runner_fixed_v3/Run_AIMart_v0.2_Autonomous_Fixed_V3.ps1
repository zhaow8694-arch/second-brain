param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
)

$ErrorActionPreference = "Stop"
try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RunnerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptSource = Join-Path $RunnerRoot "codex\V0.2_AUTONOMOUS_PROMPT_EN.md"

Write-Host "== AIMart v0.2.0 Codex Autonomous Runner FIXED V3 ==" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $PromptSource)) {
    throw "Prompt source not found: $PromptSource"
}

$CodexCommand = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $CodexCommand) { $CodexCommand = Get-Command codex -ErrorAction SilentlyContinue }
if (-not $CodexCommand) { throw "Codex CLI was not found in PATH. Please install Codex or add it to PATH." }
$CodexExe = $CodexCommand.Source
Write-Host "Codex executable: $CodexExe"

Set-Location -LiteralPath $ProjectRoot

# Prepare project-side prompt copy for traceability.
$ProjectCodexDir = Join-Path $ProjectRoot "codex"
New-Item -ItemType Directory -Force -Path $ProjectCodexDir | Out-Null
$PromptCopy = Join-Path $ProjectCodexDir "V0.2_AUTONOMOUS_PROMPT_EN.md"
Copy-Item -LiteralPath $PromptSource -Destination $PromptCopy -Force
$PromptText = Get-Content -LiteralPath $PromptCopy -Raw -Encoding UTF8

$RunDir = Join-Path $ProjectRoot "codex_runs\autonomous_v0_2_fixed_v3"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$HelpLog = Join-Path $RunDir "codex_exec_help_$Timestamp.txt"
$StdoutLog = Join-Path $RunDir "codex_v02_fixed_v3_$Timestamp.stdout.log"
$StderrLog = Join-Path $RunDir "codex_v02_fixed_v3_$Timestamp.stderr.log"
$CombinedLog = Join-Path $RunDir "codex_v02_fixed_v3_$Timestamp.combined.log"
$AttemptInfoLog = Join-Path $RunDir "codex_v02_fixed_v3_$Timestamp.attempts.txt"

# Save help output for diagnostics.
try {
    & $CodexExe exec --help > $HelpLog 2>&1
} catch {
    "Unable to capture codex exec --help: $($_.Exception.Message)" | Set-Content -Path $HelpLog -Encoding UTF8
}

# Ensure we are on a v0.2 feature branch without touching historical release branches/tags.
$currentBranch = (git branch --show-current).Trim()
if ($currentBranch -ne "feature/v0.2.0-autonomous-mode") {
    $existing = git branch --list "feature/v0.2.0-autonomous-mode"
    if ($existing) {
        git checkout "feature/v0.2.0-autonomous-mode" | Out-Host
    } else {
        git checkout -b "feature/v0.2.0-autonomous-mode" | Out-Host
    }
}

function Invoke-CodexAttempt {
    param(
        [string[]]$Arguments,
        [string]$AttemptName,
        [string]$OutLog,
        [string]$ErrLog
    )

    "===== $AttemptName =====" | Add-Content -Path $AttemptInfoLog -Encoding UTF8
    ($Arguments | ForEach-Object { "ARG: $_" }) | Add-Content -Path $AttemptInfoLog -Encoding UTF8

    Write-Host "== Starting Codex attempt: $AttemptName ==" -ForegroundColor Cyan
    Write-Host "This may run for a long time. Do not close this window unless you want to stop the run."

    $oldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $CodexExe @Arguments 1> $OutLog 2> $ErrLog
        $exit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorAction
    }
    Write-Host "== Codex attempt finished: $AttemptName, exit code $exit ==" -ForegroundColor Yellow
    return $exit
}

# Codex v0.137.0 does not accept --ask-for-approval after `exec`.
# Put runtime flags before the subcommand.
$Args1 = @(
    "--cd", $ProjectRoot,
    "--sandbox", "workspace-write",
    "--ask-for-approval", "never",
    "exec",
    $PromptText
)

$ExitCode = Invoke-CodexAttempt -Arguments $Args1 -AttemptName "global-flags-before-exec" -OutLog $StdoutLog -ErrLog $StderrLog

$stderrText = ""
if (Test-Path -LiteralPath $StderrLog) { $stderrText = Get-Content -LiteralPath $StderrLog -Raw -ErrorAction SilentlyContinue }

# Fallback for Codex versions that prefer config overrides instead of --ask-for-approval.
if ($ExitCode -ne 0 -and ($stderrText -match "ask-for-approval" -or $stderrText -match "unexpected argument" -or $stderrText -match "unrecognized")) {
    Write-Host "First attempt failed due to CLI argument compatibility. Retrying with -c approval_policy override..." -ForegroundColor Yellow
    $StdoutLog2 = Join-Path $RunDir "codex_v02_fixed_v3_$Timestamp.retry.stdout.log"
    $StderrLog2 = Join-Path $RunDir "codex_v02_fixed_v3_$Timestamp.retry.stderr.log"
    $Args2 = @(
        "--cd", $ProjectRoot,
        "-c", 'approval_policy="never"',
        "-c", 'sandbox_mode="workspace-write"',
        "exec",
        $PromptText
    )
    $ExitCode = Invoke-CodexAttempt -Arguments $Args2 -AttemptName "config-overrides-before-exec" -OutLog $StdoutLog2 -ErrLog $StderrLog2
    "`n===== RETRY STDOUT =====`n" | Add-Content -Path $StdoutLog -Encoding UTF8
    if (Test-Path -LiteralPath $StdoutLog2) { Get-Content -LiteralPath $StdoutLog2 -Raw | Add-Content -Path $StdoutLog -Encoding UTF8 }
    "`n===== RETRY STDERR =====`n" | Add-Content -Path $StderrLog -Encoding UTF8
    if (Test-Path -LiteralPath $StderrLog2) { Get-Content -LiteralPath $StderrLog2 -Raw | Add-Content -Path $StderrLog -Encoding UTF8 }
}

"==== STDOUT ====\n" | Set-Content -Path $CombinedLog -Encoding UTF8
if (Test-Path -LiteralPath $StdoutLog) { Get-Content -LiteralPath $StdoutLog -Raw | Add-Content -Path $CombinedLog -Encoding UTF8 }
"\n==== STDERR ====\n" | Add-Content -Path $CombinedLog -Encoding UTF8
if (Test-Path -LiteralPath $StderrLog) { Get-Content -LiteralPath $StderrLog -Raw | Add-Content -Path $CombinedLog -Encoding UTF8 }
"\n==== ATTEMPTS ====\n" | Add-Content -Path $CombinedLog -Encoding UTF8
if (Test-Path -LiteralPath $AttemptInfoLog) { Get-Content -LiteralPath $AttemptInfoLog -Raw | Add-Content -Path $CombinedLog -Encoding UTF8 }

Write-Host ""
Write-Host "== Codex process finished ==" -ForegroundColor Cyan
Write-Host "Exit code: $ExitCode"
Write-Host "Stdout log: $StdoutLog"
Write-Host "Stderr log: $StderrLog"
Write-Host "Combined log: $CombinedLog"

Write-Host ""
Write-Host "== Quick post-run checks ==" -ForegroundColor Cyan
Write-Host "Git branch: $((git branch --show-current).Trim())"
Write-Host "Git status:"
git status --short | Out-Host

$ReleaseDir = Join-Path $ProjectRoot "releases\v0.2.0"
if (Test-Path -LiteralPath $ReleaseDir) {
    Write-Host "Release directory found: $ReleaseDir" -ForegroundColor Green
    Get-ChildItem -LiteralPath $ReleaseDir -Recurse | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize | Out-Host
} else {
    Write-Warning "Release directory not found yet: $ReleaseDir"
}

if ($ExitCode -ne 0) {
    Write-Warning "Codex exited with non-zero exit code $ExitCode. Check combined log first: $CombinedLog"
}
exit $ExitCode
