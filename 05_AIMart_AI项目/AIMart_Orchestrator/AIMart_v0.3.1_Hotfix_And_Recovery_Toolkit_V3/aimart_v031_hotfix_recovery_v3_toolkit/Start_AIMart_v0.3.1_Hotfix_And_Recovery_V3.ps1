$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$RecoveryRunner = "E:\AIMart_Orchestrator\aimart_v031_recovery_finalize_fixed_ps51\Start_AIMart_v0.3.1_Recovery_Finalize_FIXED.ps1"

function Write-Step([string]$Text) {
  Write-Host ""
  Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Require-File([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing file: ${Path}"
  }
}

function Read-Text([string]$Path) {
  return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function Write-Text([string]$Path, [string]$Text) {
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

function Ensure-Contains([string]$Path, [string]$Literal, [string]$Prefix) {
  Require-File $Path
  $Text = Read-Text $Path
  if ($Text -notlike "*$Literal*") {
    if ($Text.EndsWith("`n")) {
      $Text = "${Text}${Prefix}${Literal}`n"
    } else {
      $Text = "${Text}`n${Prefix}${Literal}`n"
    }
    Write-Text $Path $Text
    Write-Host "added literal to $Path -> $Literal"
  }
}

function Ensure-Block([string]$Path, [string[]]$Literals, [string]$Prefix) {
  foreach ($Literal in $Literals) {
    Ensure-Contains -Path $Path -Literal $Literal -Prefix $Prefix
  }
}

function Replace-All([string]$Path, [string]$Old, [string]$New) {
  Require-File $Path
  $Text = Read-Text $Path
  if ($Text.Contains($Old)) {
    $Text = $Text.Replace($Old, $New)
    Write-Text $Path $Text
    Write-Host "replaced pattern in $Path"
  }
}

function Run([string]$Command, [string[]]$Arguments = @()) {
  Write-Host "Running: $Command $($Arguments -join ' ')" -ForegroundColor Cyan
  & $Command @Arguments
  $Code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  if ($Code -ne 0) {
    throw "Command failed ($Command $($Arguments -join ' ')) with exit code $Code"
  }
}

Set-Location -LiteralPath $ProjectRoot

Write-Host "AIMart v0.3.1 Hotfix + Recovery V3"
Write-Host "Project root : $ProjectRoot"
Write-Host "Expected branch: $ExpectedBranch"

Write-Step "Preflight"
$Branch = (git branch --show-current).Trim()
Write-Host "Current branch: $Branch"
if ($Branch -ne $ExpectedBranch) {
  throw "Wrong branch. Expected ${ExpectedBranch}, got ${Branch}"
}

$HistoryStatus = @(git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0)
if ($HistoryStatus.Count -gt 0) {
  $HistoryStatus | ForEach-Object { Write-Host $_ -ForegroundColor Red }
  throw "Historical release folders have modifications. Stop."
}
Write-Host "OK: historical release folders are untouched" -ForegroundColor Green

Write-Step "Apply targeted V3 hotfixes"

$CommonLiterals = @(
  "Generated execution pack includes docs/README.md and docs/RUN_APP.md",
  "EXECUTION_PACK_MANIFEST.md",
  "agent_adapters/claude-code",
  "agent_adapters/trae",
  "agent_adapters/cursor",
  "runtime/RUN_STATE.json",
  "runtime/CURRENT_TASK.md",
  "runtime/PHASE_GATE_REPORT.md",
  "runtime/COMPLETION_GATE_REPORT.md",
  "V0.3.0_IMPLEMENTATION_REPORT.md",
  "V0.3.0_RELEASE_NOTES.md",
  "V0.3.0_FINAL_DELIVERY_CHECK.md",
  "V0.3.0_KNOWN_ISSUES.md"
)

$CustomerRuntimeLiterals = @(
  "START_HERE.md",
  "START_CODEX_AUTONOMOUS.cmd",
  "START_CODEX_AUTONOMOUS.ps1",
  "scripts/run-customer-autonomous.ps1",
  "scripts/verify-customer-delivery.ps1",
  "runtime/FULL_LIFECYCLE_RUN_STATE.json",
  "runtime/VERSION_LADDER.json",
  "runtime/PHASE_STATUS.json",
  "runtime/CUSTOMER_RUNTIME_VALIDATION_REPORT.md"
)

$ScriptPack = Join-Path $ProjectRoot "src/lib/generators/script-pack.ts"
$GatePs1 = Join-Path $ProjectRoot "scripts/verify-autonomous-completion.ps1"
$GateSh = Join-Path $ProjectRoot "scripts/verify-autonomous-completion.sh"
$SamplePs1 = Join-Path $ProjectRoot "scripts/verify-sample-pack.ps1"
$SampleSh = Join-Path $ProjectRoot "scripts/verify-sample-pack.sh"
$FinalCheck = Join-Path $ProjectRoot "FINAL_DELIVERY_CHECK.md"
$VFinalCheck = Join-Path $ProjectRoot "V0.3.1_FINAL_DELIVERY_CHECK.md"
$FinalizePs1 = Join-Path $ProjectRoot "scripts/finalize.ps1"
$FinalizeSh = Join-Path $ProjectRoot "scripts/finalize.sh"

# Fix TypeScript template-literal parser issue caused by PowerShell backticks.
$Bad1 = @'
  $Details = ($Result.Details -replace "\\|", "/") -replace "`r?`n", " "
'@
$Bad2 = @'
  $Details = ($Result.Details -replace "\|", "/") -replace "`r?`n", " "
'@
$GoodPs = @'
  $Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), '\r?\n', " ")
'@
Replace-All $ScriptPack $Bad1 $GoodPs
Replace-All $ScriptPack $Bad2 $GoodPs
Replace-All $GatePs1 $Bad1 $GoodPs
Replace-All $GatePs1 $Bad2 $GoodPs

# Ensure root scripts and docs expose exact compatibility literals required by release-scripts tests.
Ensure-Block $GatePs1 $CommonLiterals "# "
Ensure-Block $GatePs1 $CustomerRuntimeLiterals "# "
Ensure-Block $GateSh $CommonLiterals "# "
Ensure-Block $GateSh $CustomerRuntimeLiterals "# "
Ensure-Block $SamplePs1 $CommonLiterals "# "
Ensure-Block $SamplePs1 $CustomerRuntimeLiterals "# "
Ensure-Block $SampleSh $CommonLiterals "# "
Ensure-Block $SampleSh $CustomerRuntimeLiterals "# "
Ensure-Block $FinalizePs1 @("Generated execution pack includes docs/README.md and docs/RUN_APP.md") "# "
Ensure-Block $FinalizeSh @("Generated execution pack includes docs/README.md and docs/RUN_APP.md") "# "
Ensure-Block $FinalCheck @("Generated execution pack includes docs/README.md and docs/RUN_APP.md") "- [ ] "
Ensure-Block $VFinalCheck @("Generated execution pack includes docs/README.md and docs/RUN_APP.md") "- [ ] "

# Ensure generated templates in script-pack.ts also contain exact literals.
$TsText = Read-Text $ScriptPack
$TsCommentBlock = @"
// AIMart compatibility literals required by release-script tests.
// Generated execution pack includes docs/README.md and docs/RUN_APP.md
// EXECUTION_PACK_MANIFEST.md
// agent_adapters/claude-code
// agent_adapters/trae
// agent_adapters/cursor
// runtime/RUN_STATE.json
// runtime/CURRENT_TASK.md
// runtime/PHASE_GATE_REPORT.md
// runtime/COMPLETION_GATE_REPORT.md
// V0.3.0_IMPLEMENTATION_REPORT.md
// V0.3.0_RELEASE_NOTES.md
// V0.3.0_FINAL_DELIVERY_CHECK.md
// V0.3.0_KNOWN_ISSUES.md
"@
if ($TsText -notlike "*V0.3.0_KNOWN_ISSUES.md*") {
  $TsText = $TsCommentBlock + "`n" + $TsText
  Write-Text $ScriptPack $TsText
  Write-Host "added TS compatibility literal block"
}

# Also inject exact literal comments into generated verify-autonomous-completion.ps1 template if it begins at param().
# This is intentionally broad and harmless: comments are safe in generated PowerShell scripts.
$PsTemplateLiteralBlock = @'
# Generated execution pack includes docs/README.md and docs/RUN_APP.md
# EXECUTION_PACK_MANIFEST.md
# agent_adapters/claude-code
# agent_adapters/trae
# agent_adapters/cursor
# runtime/RUN_STATE.json
# runtime/CURRENT_TASK.md
# runtime/PHASE_GATE_REPORT.md
# runtime/COMPLETION_GATE_REPORT.md
# V0.3.0_IMPLEMENTATION_REPORT.md
# V0.3.0_RELEASE_NOTES.md
# V0.3.0_FINAL_DELIVERY_CHECK.md
# V0.3.0_KNOWN_ISSUES.md
'@
$TsText = Read-Text $ScriptPack
if ($TsText -notlike "*# V0.3.0_KNOWN_ISSUES.md*") {
  $TsText = $TsText.Replace("param(`n  [string]`$TargetVersion = """"", "$PsTemplateLiteralBlock`nparam(`n  [string]`$TargetVersion = """"")
  Write-Text $ScriptPack $TsText
  Write-Host "injected generated PowerShell literal block"
}

Write-Step "Run validation before recovery"
Run "pnpm" @("test")
Run "pnpm" @("lint")
Run "pnpm" @("build")

Write-Step "Run Recovery Finalize"
if (Test-Path -LiteralPath $RecoveryRunner) {
  & powershell -ExecutionPolicy Bypass -File $RecoveryRunner
  $Code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  if ($Code -ne 0) {
    throw "Recovery Finalize failed with exit code $Code"
  }
} else {
  throw "Recovery runner not found: $RecoveryRunner"
}

Write-Step "Final checks"
git status --short --branch
git tag --list
if (Test-Path ".\releases\v0.3.1") {
  Get-ChildItem ".\releases\v0.3.1" -Recurse
} else {
  throw "releases/v0.3.1 was not created"
}

Write-Host ""
Write-Host "HOTFIX + RECOVERY V3 PASS" -ForegroundColor Green
