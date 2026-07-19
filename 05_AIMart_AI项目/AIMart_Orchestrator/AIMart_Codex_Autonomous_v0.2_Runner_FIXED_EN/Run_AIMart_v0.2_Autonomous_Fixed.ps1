param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
)

$ErrorActionPreference = "Stop"
try { chcp 65001 | Out-Null } catch {}
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Write-Host "== AIMart v0.2 Autonomous Runner Fixed ==" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

$Codex = (Get-Command codex -ErrorAction Stop).Source
Write-Host "Codex executable: $Codex"

Set-Location -LiteralPath $ProjectRoot

$PromptSource = Join-Path $PSScriptRoot "codex\V0.2_AUTONOMOUS_PROMPT_EN.md"
$PromptDir = Join-Path $ProjectRoot "codex"
$PromptPath = Join-Path $PromptDir "V0.2_AUTONOMOUS_PROMPT_EN.md"
New-Item -ItemType Directory -Force -Path $PromptDir | Out-Null
Copy-Item -LiteralPath $PromptSource -Destination $PromptPath -Force

$LogDir = Join-Path $ProjectRoot "codex_runs\autonomous_v0_2_fixed"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $LogDir "codex_v02_fixed_$Timestamp.stdout.log"
$StderrLog = Join-Path $LogDir "codex_v02_fixed_$Timestamp.stderr.log"
$CombinedLog = Join-Path $LogDir "codex_v02_fixed_$Timestamp.combined.log"
$HelpLog = Join-Path $LogDir "codex_exec_help_$Timestamp.txt"

try {
    & $Codex exec --help > $HelpLog 2>&1
    Write-Host "Codex exec help saved: $HelpLog"
} catch {
    Write-Warning "Could not save codex exec help: $($_.Exception.Message)"
}

$CurrentBranch = ""
try { $CurrentBranch = (git branch --show-current).Trim() } catch {}
Write-Host "Current branch: $CurrentBranch"

if ($CurrentBranch -ne "feature/v0.2.0-autonomous-mode") {
    $Existing = git branch --list "feature/v0.2.0-autonomous-mode"
    if ($Existing) {
        Write-Host "Switching to existing branch feature/v0.2.0-autonomous-mode"
        git checkout feature/v0.2.0-autonomous-mode
    } else {
        Write-Host "Creating branch feature/v0.2.0-autonomous-mode"
        git checkout -b feature/v0.2.0-autonomous-mode
    }
}

Write-Host "Prompt copied to: $PromptPath"
Write-Host "Stdout log: $StdoutLog"
Write-Host "Stderr log: $StderrLog"
Write-Host "Combined log: $CombinedLog"
Write-Host ""
Write-Host "== Starting Codex autonomous execution ==" -ForegroundColor Green
Write-Host "This may run for a long time. Do not close this window unless you want to stop the run."

$InnerCommand = @"
`$ErrorActionPreference = 'Continue'
try { chcp 65001 | Out-Null } catch {}
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
`$env:CODEX_NON_INTERACTIVE = '1'
Get-Content -LiteralPath '$PromptPath' -Raw | codex exec --cd '$ProjectRoot' --sandbox workspace-write --ask-for-approval never -
exit `$LASTEXITCODE
"@

$EncodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($InnerCommand))

$Proc = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $EncodedCommand) `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -Wait `
    -PassThru

$ExitCode = $Proc.ExitCode

"==== STDOUT ====" | Set-Content -Encoding UTF8 -Path $CombinedLog
Get-Content -LiteralPath $StdoutLog -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 -Path $CombinedLog
"`n==== STDERR ====" | Add-Content -Encoding UTF8 -Path $CombinedLog
Get-Content -LiteralPath $StderrLog -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 -Path $CombinedLog

Write-Host ""
Write-Host "== Codex process finished ==" -ForegroundColor Cyan
Write-Host "Exit code: $ExitCode"
Write-Host "Stdout log: $StdoutLog"
Write-Host "Stderr log: $StderrLog"
Write-Host "Combined log: $CombinedLog"

Write-Host ""
Write-Host "== Quick post-run checks ==" -ForegroundColor Cyan
try {
    Write-Host "Git branch: $((git branch --show-current).Trim())"
    Write-Host "Git status:"
    git status --short
} catch {
    Write-Warning "Git status failed: $($_.Exception.Message)"
}

$ReleaseDir = Join-Path $ProjectRoot "releases\v0.2.0"
if (Test-Path -LiteralPath $ReleaseDir) {
    Write-Host "Release directory exists: $ReleaseDir" -ForegroundColor Green
    Get-ChildItem -LiteralPath $ReleaseDir -Recurse | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
} else {
    Write-Warning "Release directory not found yet: $ReleaseDir"
}

Write-Host ""
Write-Host "If artifacts are not generated, inspect combined log first:"
Write-Host $CombinedLog
Write-Host ""
Write-Host "To resume a Codex session, use the session id shown in the log, for example:"
Write-Host "codex resume <session-id>"

if ($ExitCode -ne 0) {
    Write-Warning "Codex exited with non-zero exit code $ExitCode. Check logs."
}
