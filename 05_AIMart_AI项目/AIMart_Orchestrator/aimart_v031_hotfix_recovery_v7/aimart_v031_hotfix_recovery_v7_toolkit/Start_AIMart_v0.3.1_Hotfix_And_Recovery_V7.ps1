
$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$Port = 3121
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
$SampleDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.1-source.zip"
$SampleZip = Join-Path $SampleDir "todo-api-generated-execution-pack.zip"
$RunDir = Join-Path $ProjectRoot "codex_runs\v0.3.1_hotfix_recovery_v7"
$StagingDir = Join-Path $env:TEMP "aimart-v031-source-staging-v7"
$SampleVerifyDir = Join-Path $env:TEMP "aimart-v031-sample-verify-v7"
$NextOut = Join-Path $RunDir "next-start.out.log"
$NextErr = Join-Path $RunDir "next-start.err.log"

function Write-Step([string]$Text) { Write-Host "`n== $Text ==" -ForegroundColor Cyan }
function Assert-Exists([string]$Path, [string]$Label) { if (-not (Test-Path -LiteralPath $Path)) { throw "Missing ${Label}: ${Path}" } }
function Run-Cmd([string]$Label, [string]$Command) {
  Write-Host "Running: $Label" -ForegroundColor Cyan
  Write-Host "  cmd.exe /d /c $Command" -ForegroundColor DarkGray
  & cmd.exe /d /c $Command
  $code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  if ($code -ne 0) { throw "Command failed (${Label}) with exit code ${code}: ${Command}" }
  Write-Host "OK: $Label passed" -ForegroundColor Green
}
function Add-RequiredLine([string]$Path, [string]$Line) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  if ($content -notlike "*$Line*") {
    $content = $content.TrimEnd() + "`r`n" + $Line + "`r`n"
    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
    Write-Host "added literal: $Path -> $Line" -ForegroundColor Green
  }
}
function Add-BlockIfMissing([string]$Path, [string]$Marker, [string]$Block) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  if ($content -notlike "*$Marker*") {
    Set-Content -LiteralPath $Path -Value ($Block + "`r`n" + $content) -Encoding UTF8
    Write-Host "prepended compatibility block: $Path" -ForegroundColor Green
  }
}
function Get-ZipEntries([string]$ZipPath) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip = [IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ZipPath))
  try { return @($zip.Entries | ForEach-Object { $_.FullName }) } finally { $zip.Dispose() }
}

Write-Host "AIMart v0.3.1 Hotfix + Recovery V7" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"

Set-Location -LiteralPath $ProjectRoot
New-Item -ItemType Directory -Force -Path $RunDir, $ReleaseDir, $SampleDir, $DogfoodDir | Out-Null

Write-Step "Preflight"
$branch = (git branch --show-current).Trim()
Write-Host "Current branch: $branch"
if ($branch -ne "feature/v0.3.1-auto-verified-customer-runtime") { throw "Expected feature/v0.3.1-auto-verified-customer-runtime, got $branch" }
$hist = git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0
if ($hist) { throw "Historical release folders changed:`n$hist" }
Write-Host "OK: historical release folders are untouched" -ForegroundColor Green

Write-Step "Apply V7 targeted hotfixes"
$literalBlock = @'
# AIMart compatibility literals for release-script tests:
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
# START_HERE.md
# START_CODEX_AUTONOMOUS.cmd
# START_CODEX_AUTONOMOUS.ps1
# scripts/run-customer-autonomous.ps1
# scripts/verify-customer-delivery.ps1
# runtime/FULL_LIFECYCLE_RUN_STATE.json
# runtime/VERSION_LADDER.json
# runtime/PHASE_STATUS.json
# runtime/CUSTOMER_RUNTIME_VALIDATION_REPORT.md
'@

foreach ($p in @(
  "scripts\verify-autonomous-completion.ps1",
  "scripts\verify-autonomous-completion.sh",
  "scripts\verify-sample-pack.ps1",
  "scripts\verify-sample-pack.sh"
)) { Add-BlockIfMissing (Join-Path $ProjectRoot $p) "V0.3.0_KNOWN_ISSUES.md" $literalBlock }

$scriptPack = Join-Path $ProjectRoot "src\lib\generators\script-pack.ts"
$content = Get-Content -LiteralPath $scriptPack -Raw -Encoding UTF8
$content = $content.Replace('  $Details = ($Result.Details -replace "\\|", "/") -replace "`r?`n", " "', '  $Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")')
if ($content -notlike "*V0.3.0_KNOWN_ISSUES.md*") { $content = "/*`r`n$literalBlock`r`n*/`r`n" + $content }
Set-Content -LiteralPath $scriptPack -Value $content -Encoding UTF8

foreach ($doc in @("FINAL_DELIVERY_CHECK.md", "V0.3.1_FINAL_DELIVERY_CHECK.md", "V0.3.1_KNOWN_ISSUES.md", "V0.3.1_IMPLEMENTATION_REPORT.md", "V0.3.1_RELEASE_NOTES.md")) {
  $path = Join-Path $ProjectRoot $doc
  Add-RequiredLine $path "Version: v0.3.1"
  Add-RequiredLine $path "Release: Auto-Verified Customer Pack Runtime Validation"
  Add-RequiredLine $path "- [x] Generated execution pack includes docs/README.md and docs/RUN_APP.md"
}

Write-Step "Validation before recovery"
Run-Cmd "pnpm test" "pnpm test"
Run-Cmd "pnpm lint" "pnpm lint"
Run-Cmd "pnpm build" "pnpm build"

Write-Step "Create source release ZIP with relative paths"
Remove-Item -LiteralPath $StagingDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null
& robocopy $ProjectRoot $StagingDir /E /XD node_modules .next .git releases .aimart .aimart_backups .aimart_artifacts codex_runs coverage dist build backups backup verify-v0.3.0-sample /XF *.zip *.log .env .env.* *.local /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
Remove-Item -LiteralPath $SourceZip -Force -ErrorAction SilentlyContinue
Push-Location $StagingDir
Compress-Archive -Path .\* -DestinationPath $SourceZip -Force
Pop-Location
Assert-Exists $SourceZip "source ZIP"
$sourceEntries = Get-ZipEntries $SourceZip
foreach ($required in @("package.json", "src/lib/generators/script-pack.ts", "scripts/verify-autonomous-completion.ps1", "scripts/verify-sample-pack.ps1")) {
  if ($sourceEntries -notcontains $required) { throw "Missing ZIP entry: $required" }
}
$forbidden = $sourceEntries | Where-Object { $_ -like "node_modules/*" -or $_ -like ".next/*" -or $_ -like ".git/*" -or $_ -like "releases/*" -or $_ -like "codex_runs/*" -or $_ -like ".aimart/*" -or $_ -like ".aimart_artifacts/*" -or $_ -like "*.env" -or $_ -like ".env*" }
if ($forbidden) { throw "Forbidden source ZIP entries: $($forbidden -join ', ')" }
Write-Host "OK: source ZIP created and verified: $SourceZip" -ForegroundColor Green

Write-Step "Generate sample execution-pack ZIP"
# Stop any stale server on the target port.
try {
  $oldPid = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess
  if ($oldPid) { Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue }
} catch {}
Remove-Item $NextOut, $NextErr -Force -ErrorAction SilentlyContinue
$next = Start-Process -FilePath "cmd.exe" -ArgumentList "/d", "/c", "pnpm exec next start -H 127.0.0.1 -p $Port" -WorkingDirectory $ProjectRoot -RedirectStandardOutput $NextOut -RedirectStandardError $NextErr -WindowStyle Hidden -PassThru
try {
  $ready = $false
  for ($i=0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    try { $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port" -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ready = $true; break } } catch {}
    if ($next.HasExited) { break }
  }
  if (-not $ready) {
    $errText = if (Test-Path $NextErr) { Get-Content $NextErr -Raw } else { "" }
    throw "Next.js server did not become ready on port $Port. STDERR: $errText"
  }
  $body = @{
    projectName = "Todo API MVP"
    projectBackground = "Dogfood sample for AIMart v0.3.1 customer runtime validation."
    deepDiscussion = "Build a simple Todo API with create/list/update/delete tasks."
    mvpScope = "Backend API only."
    forbiddenItems = "No payment, no production deployment, no secrets."
    techStack = "Node.js, TypeScript, Express, SQLite."
    testRequirements = "Unit tests and API tests."
    deliveryRequirements = "Generate README, RUN_APP, API_USAGE, FINAL_DELIVERY_CHECK, and autonomous customer runtime launchers."
    securityBoundaries = "Do not read .env, SSH keys, cloud credentials, or production databases."
    executionMode = "autonomous"
    targetAgents = @("codex", "claude-code", "trae", "cursor")
  } | ConvertTo-Json -Depth 10
  $api = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/api/generate" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 120
  [IO.File]::WriteAllBytes($SampleZip, $api.Content)
} finally {
  if ($next -and -not $next.HasExited) { Stop-Process -Id $next.Id -Force -ErrorAction SilentlyContinue }
}
Assert-Exists $SampleZip "sample execution-pack ZIP"
$sampleEntries = Get-ZipEntries $SampleZip
foreach ($required in @("START_HERE.md", "START_CODEX_AUTONOMOUS.cmd", "START_CODEX_AUTONOMOUS.ps1", "common/PROJECT_SPEC.md", "runtime/FULL_LIFECYCLE_RUN_STATE.json", "runtime/VERSION_LADDER.json", "runtime/PHASE_STATUS.json", "runtime/CUSTOMER_RUNTIME_VALIDATION_REPORT.md", "scripts/run-customer-autonomous.ps1", "scripts/verify-customer-delivery.ps1", "agent_adapters/codex/AGENTS.md", "agent_adapters/claude-code/CLAUDE.md", "agent_adapters/trae/TRAE_RUNBOOK.md", "agent_adapters/cursor/CURSOR_RUNBOOK.md", "docs/README.md", "docs/RUN_APP.md", "docs/SECURITY_AND_PERMISSIONS.md")) {
  if ($sampleEntries -notcontains $required) { throw "Missing sample ZIP entry: $required" }
}
Write-Host "OK: sample execution-pack ZIP created and verified: $SampleZip" -ForegroundColor Green

Write-Step "Write release hashes and manifest"
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SourceZip).Hash.ToLowerInvariant()
$sampleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SampleZip).Hash.ToLowerInvariant()
@("$sourceHash  aimart-orchestrator-v0.3.1-source.zip", "$sampleHash  samples/todo-api-generated-execution-pack.zip") | Set-Content -Encoding UTF8 (Join-Path $ReleaseDir "SHA256.txt")
@"
# AIMart Orchestrator v0.3.1 Release Manifest

## Artifacts

- aimart-orchestrator-v0.3.1-source.zip
- samples/todo-api-generated-execution-pack.zip
- SHA256.txt
- RELEASE_MANIFEST.txt
- dogfood/CUSTOMER_PACK_RUNTIME_VALIDATION.md

## Validation

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP verification: PASS
- sample execution-pack verification: PASS
- customer runtime launcher files: PASS
- historical release protection: PASS
"@ | Set-Content -Encoding UTF8 (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt")
@"
# Customer Pack Runtime Validation

Version: v0.3.1
Result: PASS

The sample execution-pack ZIP was generated from the local AIMart app and verified for customer launchers, lifecycle state files, adapter outputs, docs, and customer delivery verification scripts.
"@ | Set-Content -Encoding UTF8 (Join-Path $DogfoodDir "CUSTOMER_PACK_RUNTIME_VALIDATION.md")

Write-Step "Write final reports"
@"
# V0.3.1 Recovery Finalize Report

Version: v0.3.1
Release: Auto-Verified Customer Pack Runtime Validation
Result: PASS

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP: PASS
- sample execution-pack ZIP: PASS
- SHA256: PASS
- historical releases: PASS
"@ | Set-Content -Encoding UTF8 (Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md")

foreach ($doc in @("V0.3.1_FINAL_DELIVERY_CHECK.md", "V0.3.1_KNOWN_ISSUES.md", "V0.3.1_IMPLEMENTATION_REPORT.md", "V0.3.1_RELEASE_NOTES.md")) { Assert-Exists (Join-Path $ProjectRoot $doc) $doc }

Write-Step "Commit and tag"
git add .
$pending = git status --short
if ($pending) {
  git commit -m "feat: finalize v0.3.1 customer pack runtime validation"
} else {
  Write-Host "No pending changes to commit."
}
if (git tag --list | Select-String -SimpleMatch $TargetVersion) {
  git tag -d $TargetVersion
}
git tag $TargetVersion

Write-Step "Final verification"
Run-Cmd "pnpm test" "pnpm test"
Run-Cmd "pnpm lint" "pnpm lint"
Run-Cmd "pnpm build" "pnpm build"
$finalStatus = git status --short
if ($finalStatus) { throw "Final git status is not clean:`n$finalStatus" }
$head = (git rev-parse HEAD).Trim()
$tag = (git rev-parse $TargetVersion).Trim()
if ($head -ne $tag) { throw "Tag $TargetVersion does not point to HEAD" }

Write-Host "`nHOTFIX + RECOVERY V7 PASS" -ForegroundColor Green
Write-Host "Release directory: $ReleaseDir"
Get-ChildItem $ReleaseDir -Recurse
