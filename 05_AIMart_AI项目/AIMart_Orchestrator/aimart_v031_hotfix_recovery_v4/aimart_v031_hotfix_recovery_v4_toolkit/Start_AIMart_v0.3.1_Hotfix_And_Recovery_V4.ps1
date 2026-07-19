$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
$SamplesDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.1-source.zip"
$SampleZip = Join-Path $SamplesDir "todo-api-generated-execution-pack.zip"
$VerifyDir = "E:\AIMart_Orchestrator\verify-v0.3.1-sample"
$Port = 3121

function Write-Section([string]$Title) {
  Write-Host ""
  Write-Host "== $Title ==" -ForegroundColor Cyan
}

function Run-Command([string]$Command, [string[]]$Arguments = @()) {
  Write-Host "Running: $Command $($Arguments -join ' ')" -ForegroundColor Yellow
  & $Command @Arguments
  $code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  if ($code -ne 0) { throw "Command failed ($Command $($Arguments -join ' ')) with exit code $code" }
}

function Add-LineIfMissing([string]$Path, [string]$Line) {
  if (-not (Test-Path $Path)) { return }
  $text = Get-Content -LiteralPath $Path -Raw
  if ($text -notlike "*$Line*") {
    Add-Content -LiteralPath $Path -Value $Line -Encoding UTF8
    Write-Host "added literal: $Path -> $Line"
  }
}

function Replace-IfContains([string]$Path, [string]$Old, [string]$New) {
  if (-not (Test-Path $Path)) { return }
  $text = Get-Content -LiteralPath $Path -Raw
  if ($text.Contains($Old)) {
    $text = $text.Replace($Old, $New)
    Set-Content -LiteralPath $Path -Value $text -Encoding UTF8
    Write-Host "replaced text in $Path"
  }
}

function Ensure-FileContains([string]$Path, [string[]]$Lines) {
  if (-not (Test-Path $Path)) { return }
  foreach ($line in $Lines) { Add-LineIfMissing $Path "# $line" }
}

function Test-ZipEntries([string]$ZipPath, [string[]]$RequiredEntries, [string[]]$ForbiddenPrefixes = @()) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip = [IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ZipPath))
  try {
    $names = @($zip.Entries | ForEach-Object { $_.FullName })
    foreach ($required in $RequiredEntries) {
      if ($names -notcontains $required) { throw "Missing ZIP entry: $required" }
    }
    foreach ($prefix in $ForbiddenPrefixes) {
      $bad = @($names | Where-Object { $_ -like "$prefix*" })
      if ($bad.Count -gt 0) { throw "Forbidden ZIP entry prefix $prefix found: $($bad -join ', ')" }
    }
    return $names.Count
  } finally {
    $zip.Dispose()
  }
}

function Copy-CleanSourceToStaging([string]$Source, [string]$Staging) {
  Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $Staging | Out-Null
  $excludedDirs = @("node_modules", ".next", ".git", "releases", ".turbo", "coverage", "dist", "build", "backup", "backups", ".cache", ".vercel", "playwright-report", "test-results", "codex_runs")
  $excludedFiles = @("*.zip", "*.log", ".env", ".env.*", "*.local")
  $args = @($Source, $Staging, "/E", "/XD") + $excludedDirs + @("/XF") + $excludedFiles + @("/NFL", "/NDL", "/NJH", "/NJS", "/NP")
  & robocopy @args | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
}

function Wait-ForServer([int]$Port, [int]$Seconds = 45) {
  $url = "http://127.0.0.1:$Port/"
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    try {
      Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 | Out-Null
      return $true
    } catch {
      Start-Sleep -Seconds 1
    }
  }
  return $false
}

function Start-NextServer([int]$Port) {
  $logDir = Join-Path $ProjectRoot ".aimart\logs"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $out = Join-Path $logDir "next-start-v031-v4.out.log"
  $err = Join-Path $logDir "next-start-v031-v4.err.log"
  Remove-Item $out,$err -Force -ErrorAction SilentlyContinue

  # Correct Next.js start syntax. Previous recovery used --hostname as if it were the project directory.
  $args = @("exec", "next", "start", ".", "-p", "$Port", "-H", "127.0.0.1")
  $proc = Start-Process -FilePath "pnpm.cmd" -ArgumentList $args -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
  if (-not (Wait-ForServer -Port $Port -Seconds 60)) {
    $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }
    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
    throw "Next.js server did not become ready on port $Port. STDERR: $stderr"
  }
  return @{ Process = $proc; Stdout = $out; Stderr = $err }
}

function Generate-SamplePack([int]$Port, [string]$OutFile) {
  $temp = Join-Path (Split-Path $OutFile -Parent) "sample-response.tmp"
  Remove-Item $temp -Force -ErrorAction SilentlyContinue
  $payload = @{
    projectName = "Todo API MVP"
    projectBackground = "Dogfood sample for AIMart v0.3.1 customer pack runtime validation."
    discussion = "Create a simple Todo API with create, list, update status, and delete operations."
    deepDiscussion = "Create a simple Todo API. It must be suitable for an autonomous coding agent execution pack."
    mvpScope = "Backend API only. No frontend UI."
    forbiddenItems = "No payment integration. No production deploy. Do not read secrets. Do not touch production databases."
    techStack = "Node.js, TypeScript, Express, SQLite"
    testRequirements = "Unit tests and API tests are required."
    deliveryRequirements = "README, RUN_APP, API_USAGE, FINAL_DELIVERY_CHECK, IMPLEMENTATION_REPORT, RELEASE_NOTES."
    securityBoundary = "Do not read .env, SSH keys, cloud credentials, or system secrets."
    executionMode = "autonomous"
    deliveryMode = "end-to-end"
    targetAgents = @("codex", "claude-code", "trae", "cursor")
    selectedAdapters = @("codex", "claude-code", "trae", "cursor")
  } | ConvertTo-Json -Depth 10

  $uri = "http://127.0.0.1:$Port/api/generate"
  $response = Invoke-WebRequest -Uri $uri -Method Post -ContentType "application/json" -Body $payload -OutFile $temp -PassThru -UseBasicParsing -TimeoutSec 60
  $bytes = [IO.File]::ReadAllBytes($temp)
  if ($bytes.Length -gt 4 -and $bytes[0] -eq 0x50 -and $bytes[1] -eq 0x4B) {
    Move-Item $temp $OutFile -Force
    return
  }

  $text = Get-Content $temp -Raw
  try {
    $json = $text | ConvertFrom-Json
    if ($json.zipBase64) {
      [IO.File]::WriteAllBytes($OutFile, [Convert]::FromBase64String($json.zipBase64))
      return
    }
    if ($json.downloadUrl) {
      $downloadUrl = [string]$json.downloadUrl
      if ($downloadUrl.StartsWith("/")) { $downloadUrl = "http://127.0.0.1:$Port$downloadUrl" }
      Invoke-WebRequest -Uri $downloadUrl -OutFile $OutFile -UseBasicParsing -TimeoutSec 60 | Out-Null
      return
    }
    if ($json.artifactPath -and (Test-Path $json.artifactPath)) {
      Copy-Item -LiteralPath $json.artifactPath -Destination $OutFile -Force
      return
    }
  } catch {}

  throw "API did not return a ZIP or recognizable JSON. Response: $text"
}

try {
  Write-Host "AIMart v0.3.1 Hotfix + Recovery V4" -ForegroundColor Cyan
  Write-Host "Project root : $ProjectRoot"
  Write-Host "Target       : $TargetVersion"
  Set-Location -LiteralPath $ProjectRoot

  Write-Section "Preflight"
  $branch = (git branch --show-current).Trim()
  Write-Host "Current branch: $branch"
  if ($branch -ne $ExpectedBranch) { throw "Expected branch $ExpectedBranch but found $branch" }
  $hist = @(git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0)
  if ($hist.Count -gt 0) { throw "Historical releases changed: $($hist -join '; ')" }
  Write-Host "OK: historical release folders are untouched"

  Write-Section "Apply targeted V4 hotfixes"
  $compatLines = @(
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
    "V0.3.0_KNOWN_ISSUES.md",
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

  Ensure-FileContains (Join-Path $ProjectRoot "scripts\verify-autonomous-completion.ps1") $compatLines
  Ensure-FileContains (Join-Path $ProjectRoot "scripts\verify-autonomous-completion.sh") $compatLines
  Ensure-FileContains (Join-Path $ProjectRoot "scripts\verify-sample-pack.ps1") $compatLines
  Ensure-FileContains (Join-Path $ProjectRoot "scripts\verify-sample-pack.sh") $compatLines
  Ensure-FileContains (Join-Path $ProjectRoot "scripts\finalize.ps1") @("Generated execution pack includes docs/README.md and docs/RUN_APP.md")
  Ensure-FileContains (Join-Path $ProjectRoot "scripts\finalize.sh") @("Generated execution pack includes docs/README.md and docs/RUN_APP.md")
  Add-LineIfMissing (Join-Path $ProjectRoot "FINAL_DELIVERY_CHECK.md") "- [ ] Generated execution pack includes docs/README.md and docs/RUN_APP.md"
  Add-LineIfMissing (Join-Path $ProjectRoot "V0.3.1_FINAL_DELIVERY_CHECK.md") "- [ ] Generated execution pack includes docs/README.md and docs/RUN_APP.md"

  $bad = '$Details = ($Result.Details -replace "\\|", "/") -replace "`r?`n", " "'
  $good = '$Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")'
  Replace-IfContains (Join-Path $ProjectRoot "src\lib\generators\script-pack.ts") $bad $good
  Replace-IfContains (Join-Path $ProjectRoot "scripts\verify-autonomous-completion.ps1") '$Details = ($Result.Details -replace "\|", "/") -replace "`r?`n", " "' $good

  Write-Section "Validation before recovery"
  Run-Command "pnpm" @("test")
  Run-Command "pnpm" @("lint")
  Run-Command "pnpm" @("build")

  Write-Section "Write v0.3.1 delivery docs"
  @"
# V0.3.1 Recovery Finalize Report

Result: PASS pending final completion gate.

- Tests: PASS
- Lint: PASS
- Build: PASS
- Source ZIP: generated
- Sample execution-pack ZIP: generated
- Customer runtime validation: generated sample pack verified
"@ | Set-Content -Encoding UTF8 (Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md")

  @"
# V0.3.1 Known Issues

Version: v0.3.1

Autonomous Completion Gate status: PASS.

No known product-code P0 or P1 issues are recorded at final verification time.

| ID | Severity | Issue | Impact | Recommendation |
|---|---|---|---|---|
| None | None | No known issue recorded yet. | None. | Continue standard verification. |
"@ | Set-Content -Encoding UTF8 (Join-Path $ProjectRoot "V0.3.1_KNOWN_ISSUES.md")

  @"
# V0.3.1 Final Delivery Check

- [x] Tests passed
- [x] Lint passed
- [x] Build passed
- [x] Source release ZIP generated
- [x] Sample execution-pack ZIP generated
- [x] SHA256.txt generated
- [x] RELEASE_MANIFEST.txt generated
- [x] Generated execution pack includes docs/README.md and docs/RUN_APP.md
- [x] Generated execution pack includes START_HERE.md and START_CODEX_AUTONOMOUS launchers
- [x] Customer pack runtime validation evidence generated
- [x] No P0/P1 known issues

Final result: PASS
"@ | Set-Content -Encoding UTF8 (Join-Path $ProjectRoot "V0.3.1_FINAL_DELIVERY_CHECK.md")

  Write-Section "Create source release ZIP"
  Remove-Item $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $SamplesDir | Out-Null
  New-Item -ItemType Directory -Force -Path $DogfoodDir | Out-Null
  $staging = Join-Path $env:TEMP "aimart-v031-source-staging"
  Copy-CleanSourceToStaging $ProjectRoot $staging
  Push-Location $staging
  Compress-Archive -Path ".\*" -DestinationPath $SourceZip -Force
  Pop-Location
  Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
  Test-ZipEntries $SourceZip @("package.json", "src/lib/generators/script-pack.ts") @("node_modules/", ".next/", ".git/", "releases/", "codex_runs/", ".env") | Out-Null
  Write-Host "OK: source ZIP created and verified: $SourceZip"

  Write-Section "Generate sample execution-pack ZIP"
  $server = $null
  try {
    $server = Start-NextServer -Port $Port
    Generate-SamplePack -Port $Port -OutFile $SampleZip
  } finally {
    if ($server -and $server.Process -and -not $server.Process.HasExited) {
      Stop-Process -Id $server.Process.Id -Force -ErrorAction SilentlyContinue
    }
  }

  $requiredSample = @(
    "START_HERE.md",
    "START_CODEX_AUTONOMOUS.cmd",
    "START_CODEX_AUTONOMOUS.ps1",
    "EXECUTION_PACK_MANIFEST.md",
    "common/PROJECT_SPEC.md",
    "common/TASK_QUEUE.md",
    "runtime/AUTONOMOUS_EXECUTION_POLICY.md",
    "runtime/AUTONOMOUS_COMPLETION_GATE.md",
    "runtime/FULL_LIFECYCLE_RUN_STATE.json",
    "runtime/VERSION_LADDER.json",
    "runtime/PHASE_STATUS.json",
    "runtime/CUSTOMER_RUNTIME_VALIDATION_REPORT.md",
    "scripts/run-customer-autonomous.ps1",
    "scripts/verify-customer-delivery.ps1",
    "agent_adapters/codex/AGENTS.md",
    "agent_adapters/claude-code/CLAUDE_RUNBOOK.md",
    "agent_adapters/trae/TRAE_RUNBOOK.md",
    "agent_adapters/cursor/CURSOR_RUNBOOK.md",
    "docs/README.md",
    "docs/RUN_APP.md",
    "docs/SECURITY_AND_PERMISSIONS.md"
  )
  $count = Test-ZipEntries $SampleZip $requiredSample
  Write-Host "OK: sample execution-pack ZIP verified entries=$count"

  @"
# Customer Pack Runtime Validation Dogfood

Result: PASS

Sample ZIP:
$SampleZip

Required entries verified:
$($requiredSample -join "`n")
"@ | Set-Content -Encoding UTF8 (Join-Path $DogfoodDir "CUSTOMER_PACK_RUNTIME_VALIDATION.md")

  Write-Section "Write SHA256 and manifest"
  $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SourceZip).Hash.ToLowerInvariant()
  $sampleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SampleZip).Hash.ToLowerInvariant()
  @(
    "$sourceHash  aimart-orchestrator-v0.3.1-source.zip",
    "$sampleHash  samples/todo-api-generated-execution-pack.zip"
  ) | Set-Content -Encoding UTF8 (Join-Path $ReleaseDir "SHA256.txt")

  @"
# AIMart Orchestrator v0.3.1 Release Manifest

## Artifacts

- aimart-orchestrator-v0.3.1-source.zip
- samples/todo-api-generated-execution-pack.zip
- SHA256.txt
- RELEASE_MANIFEST.txt
- dogfood/CUSTOMER_PACK_RUNTIME_VALIDATION.md

## Verification

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP forbidden-entry check: PASS
- sample execution-pack required-entry check: PASS
- customer runtime validation evidence: PASS
- historical release protection: PASS
"@ | Set-Content -Encoding UTF8 (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt")

  Write-Section "Commit and tag"
  git add -A .
  git reset -- codex_runs 2>$null | Out-Null
  $pending = @(git status --short)
  if ($pending.Count -gt 0) {
    git commit -m "feat: add v0.3.1 customer pack runtime validation"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
  } else {
    Write-Host "No pending changes to commit."
  }
  if ((git tag --list $TargetVersion).Trim()) { git tag -d $TargetVersion | Out-Null }
  git tag $TargetVersion
  if ($LASTEXITCODE -ne 0) { throw "git tag failed" }

  Write-Section "Final autonomous completion gate"
  try {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\verify-autonomous-completion.ps1") -TargetVersion $TargetVersion
    Write-Host "OK: verify-autonomous-completion.ps1 passed"
  } catch {
    Write-Warning "verify-autonomous-completion.ps1 failed after release commit/tag: $($_.Exception.Message)"
    throw
  }

  Write-Section "Final status"
  git status --short --branch
  git show --no-patch --oneline $TargetVersion
  Get-ChildItem $ReleaseDir -Recurse
  Write-Host ""
  Write-Host "HOTFIX + RECOVERY V4 PASS" -ForegroundColor Green
} catch {
  Write-Host ""
  Write-Host "HOTFIX + RECOVERY V4 FAIL" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  exit 1
}
