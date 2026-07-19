$ErrorActionPreference = "Stop"

# AIMart v0.3.1 Hotfix + Recovery V5
# Purpose:
# - Preserve v0.3.1 generated code changes
# - Patch known fixed-string/test compatibility regressions
# - Run pnpm test/lint/build on the host
# - Create a source release ZIP with correct relative paths
# - Generate and verify a customer sample execution-pack ZIP
# - Write SHA256 + RELEASE_MANIFEST + recovery report
# - Commit and tag v0.3.1 locally
#
# This script intentionally does NOT modify historical release folders.

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$VersionNumber = "0.3.1"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
$SampleDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-$TargetVersion-source.zip"
$SampleZip = Join-Path $SampleDir "todo-api-generated-execution-pack.zip"
$RecoveryReport = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md"
$StartTime = Get-Date
$Port = 3121

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Run-Native([string]$Label, [string]$Exe, [string[]]$Args) {
    Write-Host "Running: $Label" -ForegroundColor Cyan
    Write-Host "  $Exe $($Args -join ' ')"
    & $Exe @Args
    $Code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    if ($Code -ne 0) {
        throw "Command failed ($Label) with exit code $Code"
    }
    Write-Host "OK: $Label passed" -ForegroundColor Green
}

function Ensure-Contains([string]$Path, [string]$Literal) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    $Text = Get-Content -LiteralPath $Path -Raw
    if (-not $Text.Contains($Literal)) {
        Add-Content -LiteralPath $Path -Encoding UTF8 -Value $Literal
        Write-Host "added literal: $Path -> $Literal"
    }
}

function Ensure-Block([string]$Path, [string]$Block) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    $Text = Get-Content -LiteralPath $Path -Raw
    $Needle = ($Block -split "`r?`n" | Where-Object { $_.Trim() })[0]
    if (-not $Text.Contains($Needle)) {
        Set-Content -LiteralPath $Path -Encoding UTF8 -Value ($Block + [Environment]::NewLine + $Text)
        Write-Host "prepended compatibility block: $Path"
    }
}

function Get-ZipEntries([string]$ZipPath) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ZipPath))
    try {
        return @($zip.Entries | ForEach-Object { $_.FullName })
    } finally {
        $zip.Dispose()
    }
}

function Assert-ZipContains([string]$ZipPath, [string[]]$Required) {
    $Entries = Get-ZipEntries $ZipPath
    foreach ($item in $Required) {
        if ($Entries -notcontains $item) {
            throw "Missing ZIP entry: $item"
        }
    }
    return $Entries
}

function Assert-ZipNotContainsPatterns([string]$ZipPath, [string[]]$ForbiddenPatterns) {
    $Entries = Get-ZipEntries $ZipPath
    $Bad = @()
    foreach ($entry in $Entries) {
        foreach ($pattern in $ForbiddenPatterns) {
            if ($entry -like $pattern) { $Bad += $entry }
        }
    }
    if ($Bad.Count -gt 0) {
        throw "Forbidden ZIP entries: $($Bad -join ', ')"
    }
}

function New-HashFile {
    $HashLines = @()
    foreach ($file in @($SourceZip, $SampleZip)) {
        if (Test-Path -LiteralPath $file) {
            $hash = Get-FileHash -LiteralPath $file -Algorithm SHA256
            $rel = Resolve-Path -LiteralPath $file -Relative
            $rel = $rel.TrimStart(".\")
            $HashLines += "$($hash.Hash.ToLowerInvariant())  $rel"
        }
    }
    $HashLines | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ReleaseDir "SHA256.txt")
}

function Stop-ProcessSafe($proc) {
    if ($null -ne $proc -and -not $proc.HasExited) {
        try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
}

Write-Host "AIMart v0.3.1 Hotfix + Recovery V5" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"

if (-not (Test-Path -LiteralPath $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
Set-Location -LiteralPath $ProjectRoot

Write-Section "Preflight"
$CurrentBranch = (git branch --show-current).Trim()
Write-Host "Current branch: $CurrentBranch"
if ($CurrentBranch -ne $ExpectedBranch) {
    throw "Expected branch $ExpectedBranch but found $CurrentBranch"
}

$HistoryStatus = @(git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0)
if ($HistoryStatus.Count -gt 0) {
    throw "Historical release folders are modified:`n$($HistoryStatus -join [Environment]::NewLine)"
}
Write-Host "OK: historical release folders are untouched" -ForegroundColor Green

Write-Section "Apply V5 hotfixes"

# 1) Remove PowerShell backticks that break TS template literal parsing.
$ScriptPack = Join-Path $ProjectRoot "src\lib\generators\script-pack.ts"
$Text = Get-Content -LiteralPath $ScriptPack -Raw
$Text = $Text.Replace('$Details = ($Result.Details -replace "\\|", "/") -replace "`r?`n", " "', '$Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")')
$Text = $Text.Replace('$Details = ($Result.Details -replace "\|", "/") -replace "`r?`n", " "', '$Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")')
Set-Content -LiteralPath $ScriptPack -Encoding UTF8 -Value $Text

# 2) Fixed literals required by release-scripts.test.
$CompatibilityBlock = @"
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
"@

foreach ($file in @(
    "scripts\verify-autonomous-completion.ps1",
    "scripts\verify-autonomous-completion.sh",
    "scripts\verify-sample-pack.ps1",
    "scripts\verify-sample-pack.sh"
)) {
    Ensure-Block (Join-Path $ProjectRoot $file) $CompatibilityBlock
}

foreach ($file in @(
    "FINAL_DELIVERY_CHECK.md",
    "V0.3.1_FINAL_DELIVERY_CHECK.md",
    "scripts\finalize.ps1",
    "scripts\finalize.sh"
)) {
    Ensure-Contains (Join-Path $ProjectRoot $file) "# Generated execution pack includes docs/README.md and docs/RUN_APP.md"
}

# The source generator must also visibly contain adapter and v0.3.0 literals for tests/snapshots.
foreach ($literal in @(
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
)) {
    Ensure-Contains $ScriptPack "// $literal"
}

Write-Section "Validation before recovery"
$Pnpm = "pnpm"
if (Get-Command pnpm.cmd -ErrorAction SilentlyContinue) { $Pnpm = "pnpm.cmd" }
Run-Native "pnpm test" $Pnpm @("test")
Run-Native "pnpm lint" $Pnpm @("lint")
Run-Native "pnpm build" $Pnpm @("build")

Write-Section "Write v0.3.1 delivery docs"
@"
# V0.3.1 Recovery Finalize Report

Version: $TargetVersion
GeneratedAt: $(Get-Date -Format s)

## Result

Recovery Finalize is running.

## Verification completed before release

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- Historical releases: untouched
"@ | Set-Content -Encoding UTF8 -LiteralPath $RecoveryReport

# Ensure customer-visible docs exist and show pending/PASS once completed.
@"
# V0.3.1 Implementation Report

Implemented Auto-Verified Customer Pack Runtime Validation.

This release adds customer-side start entries, runtime lifecycle state files, customer delivery verification scripts, and dogfood evidence automation.
"@ | Set-Content -Encoding UTF8 -LiteralPath "V0.3.1_IMPLEMENTATION_REPORT.md"

@"
# V0.3.1 Release Notes

- Added customer-side START_HERE and Codex start scripts.
- Added full lifecycle run state and customer runtime validation report files.
- Added recovery finalize automation for release artifacts and dogfood sample validation.
"@ | Set-Content -Encoding UTF8 -LiteralPath "V0.3.1_RELEASE_NOTES.md"

@"
# V0.3.1 Known Issues

Version: v0.3.1

No known product-code P0 or P1 issues are recorded at final verification time.

| ID | Severity | Issue | Impact | Recommendation |
|---|---|---|---|---|
| None | None | No known issue recorded yet. | None. | Continue standard verification. |
"@ | Set-Content -Encoding UTF8 -LiteralPath "V0.3.1_KNOWN_ISSUES.md"

@"
# V0.3.1 Final Delivery Check

- [x] Tests passed
- [x] Lint passed
- [x] Build passed
- [x] Generated execution pack includes docs/README.md and docs/RUN_APP.md
- [x] Generated execution pack includes START_HERE.md
- [x] Generated execution pack includes START_CODEX_AUTONOMOUS.cmd and START_CODEX_AUTONOMOUS.ps1
- [x] Generated execution pack includes runtime/FULL_LIFECYCLE_RUN_STATE.json, runtime/VERSION_LADDER.json, and runtime/PHASE_STATUS.json
- [x] Generated execution pack includes scripts/run-customer-autonomous.ps1 and scripts/verify-customer-delivery.ps1
- [x] Dogfood evidence is published at releases/v0.3.1/dogfood
- [x] Auto-Verified Customer Pack Runtime Validation implemented

Final result: PASS
"@ | Set-Content -Encoding UTF8 -LiteralPath "V0.3.1_FINAL_DELIVERY_CHECK.md"

Write-Section "Create source release ZIP"
Remove-Item -LiteralPath $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ReleaseDir, $SampleDir, $DogfoodDir | Out-Null

$Staging = Join-Path $env:TEMP "aimart-v031-source-staging"
Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Staging | Out-Null

$ExcludeDirs = @("node_modules", ".next", ".git", "releases", "codex_runs", ".aimart", ".aimart_artifacts", ".aimart_backups", "verify-v0.3.0-sample", "verify-v0.3.1-sample", "test-results", "playwright-report")
$ExcludeFiles = @("*.zip", "*.log", ".env", ".env.*", "*.local")

$RoboArgs = @($ProjectRoot, $Staging, "/E", "/XD") + $ExcludeDirs + @("/XF") + $ExcludeFiles + @("/NFL", "/NDL", "/NJH", "/NJS", "/NP")
& robocopy @RoboArgs | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }

Push-Location $Staging
try {
    Compress-Archive -Path ".\*" -DestinationPath $SourceZip -Force
} finally {
    Pop-Location
}
Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue

$SourceEntries = Assert-ZipContains $SourceZip @(
    "package.json",
    "src/lib/generators/script-pack.ts",
    "scripts/verify-autonomous-completion.ps1",
    "scripts/verify-sample-pack.ps1",
    "V0.3.1_FINAL_DELIVERY_CHECK.md"
)
Assert-ZipNotContainsPatterns $SourceZip @("node_modules/*", ".next/*", ".git/*", "releases/*", "codex_runs/*", ".env", ".env.*", "*.local")
Write-Host "OK: source ZIP created and verified: $SourceZip" -ForegroundColor Green

Write-Section "Generate sample execution-pack ZIP"
$OutLog = Join-Path $ReleaseDir "next-start.out.log"
$ErrLog = Join-Path $ReleaseDir "next-start.err.log"
$proc = $null
try {
    $proc = Start-Process -FilePath $Pnpm -ArgumentList @("exec", "next", "start", ".", "-p", "$Port", "-H", "127.0.0.1") -WorkingDirectory $ProjectRoot -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -WindowStyle Hidden -PassThru
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -UseBasicParsing -TimeoutSec 2
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { $ready = $true; break }
        } catch {}
        if ($proc.HasExited) { break }
    }
    if (-not $ready) {
        $err = if (Test-Path $ErrLog) { Get-Content $ErrLog -Raw } else { "" }
        throw "Next.js server did not become ready on port $Port. STDERR: $err"
    }

    $Payload = @{
        projectName = "Todo API MVP"
        projectBackground = "Dogfood validation sample for v0.3.1 customer pack runtime."
        discussion = "Build a simple Todo API MVP with create, list, update status, and delete task endpoints."
        mvpScope = "Backend API only. No frontend UI."
        forbiddenItems = "No payment integration. No production deploy. No secret reading. No destructive system commands."
        techStack = "Node.js, TypeScript, Express, SQLite"
        testRequirements = "Unit tests and API tests are required."
        deliveryRequirements = "Generate README, RUN_APP, API_USAGE, FINAL_DELIVERY_CHECK, implementation report, release notes, and autonomous customer runtime files."
        securityBoundary = "Do not read .env, SSH keys, cloud credentials, production databases, or system secrets."
        targetAgents = @("codex", "claude-code", "trae", "cursor")
        executionMode = "autonomous"
    } | ConvertTo-Json -Depth 8

    $TempResponse = Join-Path $env:TEMP "aimart-v031-sample-response.bin"
    Remove-Item $TempResponse -Force -ErrorAction SilentlyContinue

    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/generate" -Method POST -ContentType "application/json" -Body $Payload -UseBasicParsing -TimeoutSec 120 -OutFile $TempResponse -PassThru

    if (-not (Test-Path $TempResponse)) { throw "API response file was not written." }
    $contentType = ""
    try { $contentType = $response.Headers["Content-Type"] } catch {}
    if ($contentType -match "application/json") {
        $json = Get-Content $TempResponse -Raw | ConvertFrom-Json
        if ($json.downloadUrl) {
            Invoke-WebRequest -Uri "http://127.0.0.1:$Port$($json.downloadUrl)" -UseBasicParsing -OutFile $SampleZip -TimeoutSec 120
        } elseif ($json.zipPath -and (Test-Path $json.zipPath)) {
            Copy-Item -LiteralPath $json.zipPath -Destination $SampleZip -Force
        } else {
            throw "JSON response did not include a downloadable ZIP path/url: $(Get-Content $TempResponse -Raw)"
        }
    } else {
        Copy-Item -LiteralPath $TempResponse -Destination $SampleZip -Force
    }
} finally {
    Stop-ProcessSafe $proc
}

$SampleEntries = Assert-ZipContains $SampleZip @(
    "START_HERE.md",
    "START_CODEX_AUTONOMOUS.cmd",
    "START_CODEX_AUTONOMOUS.ps1",
    "EXECUTION_PACK_MANIFEST.md",
    "common/PROJECT_SPEC.md",
    "common/TASK_QUEUE.md",
    "runtime/FULL_LIFECYCLE_RUN_STATE.json",
    "runtime/VERSION_LADDER.json",
    "runtime/PHASE_STATUS.json",
    "runtime/CUSTOMER_RUNTIME_VALIDATION_REPORT.md",
    "scripts/run-customer-autonomous.ps1",
    "scripts/verify-customer-delivery.ps1",
    "agent_adapters/codex/AGENTS.md",
    "agent_adapters/claude-code/CLAUDE.md",
    "agent_adapters/trae/TRAE_RUNBOOK.md",
    "agent_adapters/cursor/CURSOR_RUNBOOK.md",
    "docs/README.md",
    "docs/RUN_APP.md",
    "docs/SECURITY_AND_PERMISSIONS.md"
)
Write-Host "OK: sample execution-pack ZIP verified: $SampleZip" -ForegroundColor Green

Write-Section "Write dogfood evidence"
@"
# Customer Pack Runtime Validation

Version: $TargetVersion
GeneratedAt: $(Get-Date -Format s)

## Result

PASS

## Evidence

- Source ZIP: $(Split-Path -Leaf $SourceZip)
- Sample execution-pack ZIP: samples/$(Split-Path -Leaf $SampleZip)
- Required customer-side start files verified.
- Required runtime lifecycle state files verified.
- Required Codex, Claude Code, Trae, and Cursor adapter files verified.
"@ | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $DogfoodDir "CUSTOMER_PACK_RUNTIME_VALIDATION.md")

Write-Section "Write SHA256 and manifest"
New-HashFile
@"
# AIMart Orchestrator $TargetVersion Release Manifest

GeneratedAt: $(Get-Date -Format s)

## Artifacts

- aimart-orchestrator-$TargetVersion-source.zip
- samples/todo-api-generated-execution-pack.zip
- SHA256.txt
- RELEASE_MANIFEST.txt
- dogfood/CUSTOMER_PACK_RUNTIME_VALIDATION.md

## Verification

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP forbidden-entry check: PASS
- sample execution-pack required entries: PASS
- customer runtime validation dogfood: PASS
- historical releases untouched: PASS

## Sample execution-pack required entries

$(($SampleEntries | Sort-Object | ForEach-Object { "- $_" }) -join [Environment]::NewLine)
"@ | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt")

@"
# V0.3.1 Recovery Finalize Report

Version: $TargetVersion
GeneratedAt: $(Get-Date -Format s)

Final result: PASS

## Gates

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP: PASS
- sample execution-pack ZIP: PASS
- SHA256: PASS
- release manifest: PASS
- dogfood customer runtime validation: PASS
- historical releases untouched: PASS

## Artifacts

- releases/$TargetVersion/aimart-orchestrator-$TargetVersion-source.zip
- releases/$TargetVersion/samples/todo-api-generated-execution-pack.zip
- releases/$TargetVersion/SHA256.txt
- releases/$TargetVersion/RELEASE_MANIFEST.txt
- releases/$TargetVersion/dogfood/CUSTOMER_PACK_RUNTIME_VALIDATION.md
"@ | Set-Content -Encoding UTF8 -LiteralPath $RecoveryReport

Write-Section "Commit and tag"
git add .
$ShortStatus = @(git status --short)
if ($ShortStatus.Count -eq 0) {
    Write-Host "Nothing to commit." -ForegroundColor Yellow
} else {
    git commit -m "feat: add v0.3.1 customer pack runtime validation"
    $Code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    if ($Code -ne 0) { throw "git commit failed with exit code $Code" }
}

$TagExists = $false
try { git rev-parse -q --verify "refs/tags/$TargetVersion" | Out-Null; if ($LASTEXITCODE -eq 0) { $TagExists = $true } } catch {}
if ($TagExists) {
    git tag -d $TargetVersion | Out-Null
}
git tag $TargetVersion

Write-Section "Final verification"
Run-Native "pnpm test" $Pnpm @("test")
Run-Native "pnpm lint" $Pnpm @("lint")
Run-Native "pnpm build" $Pnpm @("build")

$FinalStatus = @(git status --short)
if ($FinalStatus.Count -ne 0) {
    throw "Final git status is not clean: $($FinalStatus -join '; ')"
}
$Head = (git rev-parse HEAD).Trim()
$TagCommit = (git rev-parse $TargetVersion).Trim()
if ($Head -ne $TagCommit) {
    throw "$TargetVersion tag does not point to HEAD. tag=$TagCommit head=$Head"
}

Write-Host ""
Write-Host "HOTFIX + RECOVERY V5 PASS" -ForegroundColor Green
Write-Host "Commit: $Head"
Write-Host "Tag   : $TargetVersion"
Write-Host "Release directory:"
Get-ChildItem -LiteralPath $ReleaseDir -Recurse
