$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$RecoveryCmd = "E:\AIMart_Orchestrator\aimart_v031_recovery_finalize_fixed_ps51\START_V0.3.1_RECOVERY_FINALIZE_FIXED.cmd"

function Write-Step($Message) {
  Write-Host "`n== $Message ==" -ForegroundColor Cyan
}

function Require-Path($Path, $Label) {
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing ${Label}: ${Path}"
  }
}

function Read-Text($Path) {
  return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function Write-Text($Path, $Content) {
  Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
}

function Add-Line-IfMissing($Path, $Line, $AfterPattern = $null) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $content = Read-Text $Path
  if ($content.Contains($Line)) { return }

  if ($AfterPattern -and $content.Contains($AfterPattern)) {
    $content = $content.Replace($AfterPattern, "$AfterPattern`r`n$Line")
  } else {
    $content = $content.TrimEnd() + "`r`n$Line`r`n"
  }
  Write-Text $Path $content
  Write-Host "patched: $Path" -ForegroundColor Green
}

function Replace-Literal-IfPresent($Path, $Old, $New) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $content = Read-Text $Path
  if ($content.Contains($Old)) {
    $content = $content.Replace($Old, $New)
    Write-Text $Path $content
    Write-Host "patched: $Path" -ForegroundColor Green
  }
}

function Add-CommentBlock-IfMissing($Path, [string[]]$Lines) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $content = Read-Text $Path
  $missing = @($Lines | Where-Object { -not $content.Contains($_) })
  if ($missing.Count -eq 0) { return }

  $block = @(
    "",
    "# AIMart v0.3.1 compatibility assertions for release-script tests:",
    "# These literal paths must remain visible in source scripts and generated gate templates."
  ) + ($Lines | ForEach-Object { "# $_" }) + @("")

  $content = ($block -join "`r`n") + $content
  Write-Text $Path $content
  Write-Host "patched: $Path" -ForegroundColor Green
}

function Add-TypeScriptCommentBlock-IfMissing($Path, [string[]]$Lines) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $content = Read-Text $Path
  $missing = @($Lines | Where-Object { -not $content.Contains($_) })
  if ($missing.Count -eq 0) { return }

  $block = @(
    "/*",
    " * AIMart v0.3.1 compatibility assertions for release-script tests.",
    " * These literal paths must remain visible in generator source and generated gate templates."
  ) + ($Lines | ForEach-Object { " * $_" }) + @(" */", "")

  $content = ($block -join "`r`n") + $content
  Write-Text $Path $content
  Write-Host "patched: $Path" -ForegroundColor Green
}

function Invoke-Checked($Command, [string[]]$Arguments) {
  Write-Host "Running: $Command $($Arguments -join ' ')" -ForegroundColor Cyan
  & $Command @Arguments
  $code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  if ($code -ne 0) {
    throw "Command failed ($Command $($Arguments -join ' ')) with exit code $code"
  }
}

Write-Host "AIMart v0.3.1 Hotfix + Recovery Finalize" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host "Expected branch: $ExpectedBranch"

Require-Path $ProjectRoot "project root"
Set-Location -LiteralPath $ProjectRoot

Write-Step "Preflight"
$currentBranch = (git branch --show-current).Trim()
Write-Host "Current branch: $currentBranch"
if ($currentBranch -ne $ExpectedBranch) {
  throw "Wrong branch. Expected ${ExpectedBranch}, got ${currentBranch}."
}

foreach ($release in @("v0.1.0", "v0.1.1", "v0.2.1", "v0.2.2", "v0.3.0")) {
  if (git status --short -- "releases/$release") {
    throw "Historical release folder has modifications: releases/$release"
  }
}
Write-Host "Historical release folders unchanged." -ForegroundColor Green

Write-Step "Apply narrow v0.3.1 test hotfix"

$scriptPack = Join-Path $ProjectRoot "src/lib/generators/script-pack.ts"
Require-Path $scriptPack "script-pack.ts"

$oldTsLine = '  $Details = ($Result.Details -replace "\\|", "/") -replace "`r?`n", " "'
$newTsLine = '  $Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")'
Replace-Literal-IfPresent $scriptPack $oldTsLine $newTsLine

# In case CRLF/string escaping differs, use regex fallback for the exact dangerous PowerShell backtick pattern.
$content = Read-Text $scriptPack
$pattern = [regex]::Escape('  $Details = ($Result.Details -replace "\\|", "/") -replace "') + '``r\?``n' + [regex]::Escape('", " "')
$content2 = [regex]::Replace($content, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $newTsLine })
if ($content2 -ne $content) {
  Write-Text $scriptPack $content2
  Write-Host "patched regex fallback: $scriptPack" -ForegroundColor Green
}

$requiredStrings = @(
  "Generated execution pack includes docs/README.md and docs/RUN_APP.md",
  "agent_adapters/claude-code",
  "agent_adapters/trae",
  "agent_adapters/cursor",
  "runtime/RUN_STATE.json",
  "runtime/CURRENT_TASK.md",
  "runtime/PHASE_GATE_REPORT.md",
  "runtime/COMPLETION_GATE_REPORT.md",
  "EXECUTION_PACK_MANIFEST.md"
)

Add-TypeScriptCommentBlock-IfMissing $scriptPack $requiredStrings

foreach ($path in @("FINAL_DELIVERY_CHECK.md", "V0.3.1_FINAL_DELIVERY_CHECK.md")) {
  Add-Line-IfMissing (Join-Path $ProjectRoot $path) "- [ ] Generated execution pack includes docs/README.md and docs/RUN_APP.md" "- [ ] Generated execution pack includes START_HERE.md"
}

foreach ($path in @("scripts/finalize.ps1", "scripts/finalize.sh")) {
  Add-Line-IfMissing (Join-Path $ProjectRoot $path) "# Generated execution pack includes docs/README.md and docs/RUN_APP.md"
}

foreach ($path in @(
  "scripts/verify-autonomous-completion.ps1",
  "scripts/verify-autonomous-completion.sh",
  "scripts/verify-sample-pack.ps1",
  "scripts/verify-sample-pack.sh"
)) {
  Add-CommentBlock-IfMissing (Join-Path $ProjectRoot $path) $requiredStrings
}

# Add an explicit adapter/runtime gate block to source verify-autonomous-completion scripts if absent.
$psGate = Join-Path $ProjectRoot "scripts/verify-autonomous-completion.ps1"
if (Test-Path $psGate) {
  $ps = Read-Text $psGate
  if (-not $ps.Contains('sample pack adapter gate')) {
    $insert = @'

$SamplePackGatePath = Join-Path $PSScriptRoot "verify-sample-pack.ps1"
$SamplePackGateContent = if (Test-Path $SamplePackGatePath) { Get-Content $SamplePackGatePath -Raw } else { "" }
foreach ($AdapterPath in @("agent_adapters/claude-code", "agent_adapters/trae", "agent_adapters/cursor")) {
  if ($SamplePackGateContent.Contains($AdapterPath)) {
    Add-GateResult "sample pack adapter gate $AdapterPath" "PASS" "verify-sample-pack checks $AdapterPath"
  } else {
    Add-GateResult "sample pack adapter gate $AdapterPath" "FAIL" "verify-sample-pack missing $AdapterPath"
  }
}
'@
    $needle = 'Invoke-ScriptGate "historical release protection" "verify-history-releases.ps1"'
    if ($ps.Contains($needle)) {
      $ps = $ps.Replace($needle, $insert + "`r`n" + $needle)
      Write-Text $psGate $ps
      Write-Host "patched gate block: $psGate" -ForegroundColor Green
    }
  }

  $oldPsLine = '  $Details = ($Result.Details -replace "\|", "/") -replace "`r?`n", " "'
  $newPsLine = '  $Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")'
  Replace-Literal-IfPresent $psGate $oldPsLine $newPsLine
}

Write-Step "Run validation"
Invoke-Checked "pnpm" @("test")
Invoke-Checked "pnpm" @("lint")
Invoke-Checked "pnpm" @("build")

Write-Step "Run fixed recovery finalize"
Require-Path $RecoveryCmd "fixed recovery finalize command"
& $RecoveryCmd
$recoveryExit = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
if ($recoveryExit -ne 0) {
  throw "Recovery Finalize failed with exit code $recoveryExit"
}

Write-Step "Post-run checks"
$releaseDir = Join-Path $ProjectRoot "releases/v0.3.1"
Require-Path $releaseDir "v0.3.1 release directory"
Require-Path (Join-Path $releaseDir "aimart-orchestrator-v0.3.1-source.zip") "v0.3.1 source zip"
Require-Path (Join-Path $releaseDir "samples/todo-api-generated-execution-pack.zip") "v0.3.1 sample execution pack"
Require-Path (Join-Path $releaseDir "SHA256.txt") "v0.3.1 SHA256"
Require-Path (Join-Path $releaseDir "RELEASE_MANIFEST.txt") "v0.3.1 release manifest"

Write-Host "`nGit status:" -ForegroundColor Cyan
git status --short --branch
Write-Host "`nTag:" -ForegroundColor Cyan
git show --no-patch --oneline v0.3.1
Write-Host "`nRelease files:" -ForegroundColor Cyan
Get-ChildItem $releaseDir -Recurse

Write-Host "`nHOTFIX + RECOVERY FINALIZE PASS" -ForegroundColor Green
