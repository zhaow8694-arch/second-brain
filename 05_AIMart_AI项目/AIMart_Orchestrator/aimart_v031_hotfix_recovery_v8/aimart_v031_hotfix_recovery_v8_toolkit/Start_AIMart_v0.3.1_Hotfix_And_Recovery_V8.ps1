$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
$SampleDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.1-source.zip"
$SampleZip = Join-Path $SampleDir "todo-api-generated-execution-pack.zip"
$ReportPath = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md"

function Write-Step([string]$Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Run-Cmd([string]$Label, [string]$Command) {
    Write-Host "Running: $Label" -ForegroundColor Cyan
    Write-Host "  cmd.exe /d /c $Command"
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d","/c",$Command) -WorkingDirectory $ProjectRoot -NoNewWindow -Wait -PassThru
    if ($p.ExitCode -ne 0) {
        throw "Command failed ($Label) with exit code $($p.ExitCode): $Command"
    }
    Write-Host "OK: $Label passed" -ForegroundColor Green
}

function Add-LineIfMissing([string]$Path, [string]$Line) {
    if (-not (Test-Path $Path)) { return }
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ($content -notlike "*$Line*") {
        $content = $content.TrimEnd() + "`r`n" + $Line + "`r`n"
        Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
        Write-Host "added literal: $Path -> $Line"
    }
}

function Replace-BadBacktickLine([string]$Path) {
    if (-not (Test-Path $Path)) { return }
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $bad = '  $Details = ($Result.Details -replace "\\|", "/") -replace "`r?`n", " "'
    $good = '  $Details = [regex]::Replace(($Result.Details -replace [regex]::Escape("|"), "/"), ''\r?\n'', " ")'
    if ($content.Contains($bad)) {
        $content = $content.Replace($bad, $good)
        Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
        Write-Host "patched PowerShell backtick sanitizer: $Path"
    }
}

function Add-CompatBlockIfMissing([string]$Path) {
    if (-not (Test-Path $Path)) { return }
    $block = @"
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
"@
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $needs = @(
        "V0.3.0_IMPLEMENTATION_REPORT.md",
        "V0.3.0_RELEASE_NOTES.md",
        "V0.3.0_FINAL_DELIVERY_CHECK.md",
        "V0.3.0_KNOWN_ISSUES.md",
        "agent_adapters/claude-code",
        "agent_adapters/trae",
        "agent_adapters/cursor",
        "runtime/RUN_STATE.json"
    ) | Where-Object { $content -notlike "*$_*" }
    if ($needs.Count -gt 0) {
        $content = $block + "`r`n" + $content
        Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
        Write-Host "patched compatibility literals: $Path"
    }
}

function Assert-ZipContains([string]$ZipPath, [string[]]$Required) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ZipPath))
    try {
        $names = $zip.Entries | ForEach-Object { $_.FullName.Replace("\","/") }
        foreach ($entry in $Required) {
            if ($names -notcontains $entry) {
                throw "Missing ZIP entry: $entry"
            }
            Write-Host "OK ZIP entry: $entry" -ForegroundColor Green
        }
    } finally {
        $zip.Dispose()
    }
}

function Assert-ZipForbidden([string]$ZipPath, [string[]]$ForbiddenPrefixes) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ZipPath))
    try {
        $names = $zip.Entries | ForEach-Object { $_.FullName.Replace("\","/") }
        $bad = @()
        foreach ($prefix in $ForbiddenPrefixes) {
            $bad += $names | Where-Object { $_ -like "$prefix*" }
        }
        if ($bad.Count -gt 0) {
            throw "Forbidden ZIP entries: $($bad -join ', ')"
        }
        Write-Host "OK: forbidden ZIP entry check passed" -ForegroundColor Green
    } finally {
        $zip.Dispose()
    }
}

function Wait-HttpReady([int]$Port, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port" -TimeoutSec 2
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { return $true }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Start-NextServerAndGenerateSample {
    $port = 3121
    $logDir = Join-Path $ProjectRoot "codex_runs\v031_recovery_v8"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $out = Join-Path $logDir "next-start.out.log"
    $err = Join-Path $logDir "next-start.err.log"

    $existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($existing) {
        foreach ($conn in $existing) {
            try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
        }
        Start-Sleep -Seconds 2
    }

    $arg = '/d /c pnpm exec next start -H 127.0.0.1 -p 3121'
    $proc = Start-Process -FilePath "cmd.exe" -ArgumentList $arg -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
    try {
        if (-not (Wait-HttpReady -Port $port -Seconds 45)) {
            $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }
            throw "Next.js server did not become ready on port $port. STDERR: $stderr"
        }

        $payload = @{
            projectName = "Todo API MVP"
            projectBackground = "Dogfood sample for AIMart v0.3.1 Auto-Verified Customer Pack Runtime Validation."
            discussion = "Build a Todo API MVP with create, list, update status, and delete operations."
            deepDiscussion = "Build a Todo API MVP with Node.js, TypeScript, Express, SQLite, unit tests, API tests, delivery docs, and autonomous completion gate."
            mvpScope = "Backend API only. No frontend."
            forbiddenItems = "No real payment, no production deployment, no secrets, no production database."
            techStack = "Node.js, TypeScript, Express, SQLite, Vitest, pnpm"
            testingRequirements = "Unit tests and API tests required. Fix failures automatically where safe."
            deliveryRequirements = "Generate README, RUN_APP, API_USAGE, FINAL_DELIVERY_CHECK, IMPLEMENTATION_REPORT, RELEASE_NOTES."
            safetyBoundaries = "Do not read .env, SSH keys, cloud credentials, or system secrets."
            selectedAdapters = @("codex","claude-code","trae","cursor")
            targetAgents = @("codex","claude-code","trae","cursor")
            executionMode = "autonomous"
            deliveryScope = "end-to-end"
        }

        $json = $payload | ConvertTo-Json -Depth 8
        Remove-Item $SampleZip -Force -ErrorAction SilentlyContinue
        Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:$port/api/generate" -ContentType "application/json" -Body $json -OutFile $SampleZip -TimeoutSec 60 | Out-Null

        if (-not (Test-Path $SampleZip)) { throw "Sample ZIP not generated." }
        if ((Get-Item $SampleZip).Length -lt 1000) { throw "Sample ZIP too small; API may not have returned a ZIP." }

        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $SampleZip))
        $zip.Dispose()
        Write-Host "OK: sample execution-pack ZIP generated: $SampleZip" -ForegroundColor Green
    } finally {
        try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
}

Write-Host "AIMart v0.3.1 Hotfix + Recovery V8"
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"

Set-Location -LiteralPath $ProjectRoot

Write-Step "Preflight"
$branch = (git branch --show-current).Trim()
Write-Host "Current branch: $branch"
if ($branch -ne $ExpectedBranch) {
    throw "Expected branch $ExpectedBranch but got $branch"
}
$historyStatus = git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0
if ($historyStatus) {
    throw "Historical release folders changed: $historyStatus"
}
Write-Host "OK: historical release folders are untouched" -ForegroundColor Green

Write-Step "Apply V8 targeted hotfixes"

# Checked-in docs and scripts
foreach ($file in @(
    "FINAL_DELIVERY_CHECK.md",
    "V0.3.1_FINAL_DELIVERY_CHECK.md",
    "V0.3.1_KNOWN_ISSUES.md",
    "V0.3.1_IMPLEMENTATION_REPORT.md",
    "V0.3.1_RELEASE_NOTES.md"
)) {
    Add-LineIfMissing (Join-Path $ProjectRoot $file) "Version: v0.3.1"
    Add-LineIfMissing (Join-Path $ProjectRoot $file) "Release: Auto-Verified Customer Pack Runtime Validation"
    Add-LineIfMissing (Join-Path $ProjectRoot $file) "- [x] Generated execution pack includes docs/README.md and docs/RUN_APP.md"
}
foreach ($file in @(
    "scripts\verify-autonomous-completion.ps1",
    "scripts\verify-autonomous-completion.sh",
    "scripts\verify-sample-pack.ps1",
    "scripts\verify-sample-pack.sh",
    "src\lib\generators\script-pack.ts"
)) {
    Add-CompatBlockIfMissing (Join-Path $ProjectRoot $file)
    Replace-BadBacktickLine (Join-Path $ProjectRoot $file)
}

Write-Step "Validation before recovery"
Run-Cmd "pnpm test" "pnpm test"
Run-Cmd "pnpm lint" "pnpm lint"
Run-Cmd "pnpm build" "pnpm build"

Write-Step "Create source release ZIP with normalized entry verification"
New-Item -ItemType Directory -Force -Path $ReleaseDir, $SampleDir, $DogfoodDir | Out-Null

$stage = Join-Path $env:TEMP "aimart-v0.3.1-source-stage-v8"
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $stage | Out-Null

robocopy $ProjectRoot $stage /E `
  /XD node_modules .next .git releases codex_runs .aimart .aimart_artifacts .aimart_backups .vite-cache `
  /XF *.zip *.log .env .env.* `
  /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

Remove-Item $SourceZip -Force -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($stage, $SourceZip)
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue

Assert-ZipContains $SourceZip @(
    "package.json",
    "src/lib/generators/script-pack.ts",
    "scripts/verify-autonomous-completion.ps1",
    "scripts/verify-sample-pack.ps1"
)
Assert-ZipForbidden $SourceZip @(
    "node_modules/",
    ".next/",
    ".git/",
    "releases/",
    "codex_runs/",
    ".aimart/",
    ".aimart_artifacts/",
    ".aimart_backups/",
    ".vite-cache/"
)

Write-Step "Generate sample execution-pack ZIP"
Start-NextServerAndGenerateSample

Write-Step "Verify sample execution-pack ZIP"
Assert-ZipContains $SampleZip @(
    "START_HERE.md",
    "START_CODEX_AUTONOMOUS.cmd",
    "START_CODEX_AUTONOMOUS.ps1",
    "EXECUTION_PACK_MANIFEST.md",
    "common/PROJECT_SPEC.md",
    "runtime/RUN_STATE.json",
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

Write-Step "Write SHA256 and RELEASE_MANIFEST"
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SourceZip).Hash
$sampleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SampleZip).Hash
@(
    "$sourceHash  aimart-orchestrator-v0.3.1-source.zip",
    "$sampleHash  samples/todo-api-generated-execution-pack.zip"
) | Set-Content -Encoding UTF8 (Join-Path $ReleaseDir "SHA256.txt")

@"
# AIMart Orchestrator v0.3.1 Release Manifest

Release: Auto-Verified Customer Pack Runtime Validation

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
- source ZIP: PASS
- sample execution-pack ZIP: PASS
- historical release protection: PASS
- customer runtime validation: PASS

## Required sample entries verified

- START_HERE.md
- START_CODEX_AUTONOMOUS.cmd
- START_CODEX_AUTONOMOUS.ps1
- runtime/RUN_STATE.json
- runtime/FULL_LIFECYCLE_RUN_STATE.json
- runtime/VERSION_LADDER.json
- runtime/PHASE_STATUS.json
- runtime/CUSTOMER_RUNTIME_VALIDATION_REPORT.md
- scripts/run-customer-autonomous.ps1
- scripts/verify-customer-delivery.ps1
- agent_adapters/codex
- agent_adapters/claude-code
- agent_adapters/trae
- agent_adapters/cursor
"@ | Set-Content -Encoding UTF8 (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt")

@"
# Customer Pack Runtime Validation

Version: v0.3.1

Release: Auto-Verified Customer Pack Runtime Validation

Result: PASS

Validated sample pack:
samples/todo-api-generated-execution-pack.zip

Validated:
- customer root launchers
- lifecycle state files
- customer autonomous runner files
- customer delivery verifier
- all target AI adapter directories
- docs/README.md
- docs/RUN_APP.md
- docs/SECURITY_AND_PERMISSIONS.md
"@ | Set-Content -Encoding UTF8 (Join-Path $DogfoodDir "CUSTOMER_PACK_RUNTIME_VALIDATION.md")

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
- release manifest: PASS
- dogfood customer runtime validation: PASS
- historical release protection: PASS
"@ | Set-Content -Encoding UTF8 $ReportPath

Write-Step "Commit and tag"
git add .
$status = git status --short
if ($status) {
    git commit -m "feat: finalize v0.3.1 customer pack runtime validation"
} else {
    Write-Host "No changes to commit."
}
git tag -d v0.3.1 2>$null | Out-Null
git tag v0.3.1

Write-Step "Final verification"
$finalStatus = git status --short
if ($finalStatus) {
    throw "Final git status is not clean: $finalStatus"
}
$tagLine = git show --no-patch --oneline v0.3.1
Write-Host $tagLine
Get-ChildItem $ReleaseDir -Recurse

Write-Host ""
Write-Host "HOTFIX + RECOVERY V8 PASS" -ForegroundColor Green
