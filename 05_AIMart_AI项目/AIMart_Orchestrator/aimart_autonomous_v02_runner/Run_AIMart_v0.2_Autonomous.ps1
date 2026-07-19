param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
)

# AIMart v0.2 Codex Autonomous Runner
# This script is designed to avoid repeated approval prompts by using Codex exec
# with workspace-write and approval never when supported by the installed Codex CLI.

$ErrorActionPreference = "Continue"

function Write-Section($Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Add-ArgIfSupported {
    param(
        [string[]]$Args,
        [string]$HelpText,
        [string]$Flag,
        [string[]]$Values
    )
    if ($HelpText -match [Regex]::Escape($Flag)) {
        return $Args + @($Flag) + $Values
    }
    return $Args
}

Write-Section "AIMart v0.2 autonomous runner"
Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    Write-Error "Project root not found: $ProjectRoot"
    exit 1
}

Set-Location -LiteralPath $ProjectRoot

try {
    $CodexCommand = Get-Command codex -ErrorAction Stop
} catch {
    Write-Error "Codex CLI was not found in PATH. Please install Codex CLI or open a shell where codex is available."
    exit 1
}

$CodexExe = $CodexCommand.Source
Write-Host "Codex executable: $CodexExe"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourcePrompt = Join-Path $ScriptDir "codex\V0.2_AUTONOMOUS_PROMPT.md"
$ProjectCodexDir = Join-Path $ProjectRoot "codex"
$PromptFile = Join-Path $ProjectCodexDir "V0.2_AUTONOMOUS_PROMPT.md"

New-Item -ItemType Directory -Force -Path $ProjectCodexDir | Out-Null

if (Test-Path -LiteralPath $SourcePrompt) {
    Copy-Item -LiteralPath $SourcePrompt -Destination $PromptFile -Force
} elseif (-not (Test-Path -LiteralPath $PromptFile)) {
    Write-Error "Prompt file not found. Expected either $SourcePrompt or $PromptFile"
    exit 1
}

$RunRoot = Join-Path $ProjectRoot "codex_runs\autonomous_v0_2"
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$HelpLog = Join-Path $RunRoot "codex_exec_help_$Stamp.txt"
$PromptCopy = Join-Path $RunRoot "V0.2_AUTONOMOUS_PROMPT_$Stamp.md"
$CombinedLog = Join-Path $RunRoot "codex_autonomous_v0_2_$Stamp.combined.log"
$CommandLog = Join-Path $RunRoot "codex_autonomous_v0_2_$Stamp.command.txt"

Copy-Item -LiteralPath $PromptFile -Destination $PromptCopy -Force

Write-Section "Detecting Codex exec options"
$ExecHelpText = (& $CodexExe exec --help 2>&1 | Out-String)
$ExecHelpText | Out-File $HelpLog -Encoding UTF8
Write-Host "Codex exec help saved: $HelpLog"

$Args = @("exec")

if ($ExecHelpText -match "--cd") {
    $Args += @("--cd", $ProjectRoot)
} else {
    Write-Host "Codex exec help did not show --cd; using current working directory instead." -ForegroundColor Yellow
}

if ($ExecHelpText -match "--sandbox") {
    $Args += @("--sandbox", "workspace-write")
} else {
    Write-Host "Codex exec help did not show --sandbox; continuing without explicit sandbox flag." -ForegroundColor Yellow
}

$ApprovalAdded = $false
if ($ExecHelpText -match "--ask-for-approval") {
    $Args += @("--ask-for-approval", "never")
    $ApprovalAdded = $true
} elseif ($ExecHelpText -match "--approval-policy") {
    $Args += @("--approval-policy", "never")
    $ApprovalAdded = $true
} elseif ($ExecHelpText -match "(?m)^\s*-c," -or $ExecHelpText -match "--config") {
    $Args += @("-c", "approval_policy=never")
    $ApprovalAdded = $true
}

if ($ApprovalAdded) {
    Write-Host "Approval policy: never" -ForegroundColor Green
} else {
    Write-Host "No explicit approval flag detected for codex exec; continuing without approval flag." -ForegroundColor Yellow
}

$PromptText = Get-Content -LiteralPath $PromptFile -Raw -Encoding UTF8
$Args += @($PromptText)

@"
Codex executable:
$CodexExe

Arguments excluding prompt body:
$($Args[0..([Math]::Max(0, $Args.Count - 2))] -join ' ')

Prompt file:
$PromptFile

Combined log:
$CombinedLog
"@ | Out-File $CommandLog -Encoding UTF8

Write-Host "Prompt saved: $PromptCopy"
Write-Host "Combined log: $CombinedLog"
Write-Host "Command log: $CommandLog"

Write-Section "Starting Codex autonomous execution"
Write-Host "This may run for a long time. Do not close this window unless you want to stop the run." -ForegroundColor Yellow

# Use combined stream logging to avoid Windows PowerShell treating native stderr as a terminating script error.
& $CodexExe @Args 2>&1 | Tee-Object -FilePath $CombinedLog
$ExitCode = $LASTEXITCODE

Write-Section "Codex run completed"
Write-Host "Exit code: $ExitCode"
Write-Host "Combined log: $CombinedLog"

if ($ExitCode -ne 0) {
    Write-Host "Codex exited with a non-zero code. Review the combined log before retrying." -ForegroundColor Yellow
    exit $ExitCode
}

Write-Host "AIMart v0.2 autonomous run completed successfully." -ForegroundColor Green
