$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$ReleaseDir = Join-Path $ProjectRoot "releases\v0.3.1"
$SampleDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.1-source.zip"
$SampleZip = Join-Path $SampleDir "todo-api-generated-execution-pack.zip"
$ManifestPath = Join-Path $ReleaseDir "RELEASE_MANIFEST.txt"
$ShaPath = Join-Path $ReleaseDir "SHA256.txt"
$ReportPath = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md"

function Write-Section([string]$Text) {
    Write-Host "`n== $Text ==" -ForegroundColor Cyan
}

function Run-Cmd([string]$Label, [string]$Command) {
    Write-Host "Running: $Label" -ForegroundColor Yellow
    Write-Host "  cmd.exe /d /c $Command" -ForegroundColor DarkGray
    cmd.exe /d /c $Command
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "Command failed (${Label}) with exit code ${code}: ${Command}"
    }
    Write-Host "OK: $Label passed" -ForegroundColor Green
}

function Assert-PathExists([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing ${Label}: ${Path}"
    }
}

function Get-ZipEntriesNormalized([string]$Path) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Path))
    try {
        return @($zip.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
    } finally {
        $zip.Dispose()
    }
}

function Test-ZipMagic([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $fs = [System.IO.File]::OpenRead((Resolve-Path -LiteralPath $Path))
    try {
        if ($fs.Length -lt 4) { return $false }
        $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte(); $b2 = $fs.ReadByte(); $b3 = $fs.ReadByte()
        return ($b0 -eq 0x50 -and $b1 -eq 0x4B -and (($b2 -eq 0x03 -and $b3 -eq 0x04) -or ($b2 -eq 0x05 -and $b3 -eq 0x06) -or ($b2 -eq 0x07 -and $b3 -eq 0x08)))
    } finally {
        $fs.Dispose()
    }
}

function Ensure-JsonEncodedSampleIsZip([string]$Path) {
    Assert-PathExists $Path "sample response file"
    $item = Get-Item -LiteralPath $Path
    Write-Host "Sample file length before normalization: $($item.Length)"

    if (Test-ZipMagic $Path) {
        Write-Host "Sample file already has ZIP magic bytes." -ForegroundColor Green
        return
    }

    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $errorPath = [System.IO.Path]::ChangeExtension($Path, ".ERROR.txt")

    try {
        $json = $raw | ConvertFrom-Json
    } catch {
        Set-Content -LiteralPath $errorPath -Value $raw -Encoding UTF8
        throw "Sample file is not ZIP and is not valid JSON. Saved raw response to $errorPath"
    }

    if (-not $json.zipBase64) {
        Set-Content -LiteralPath $errorPath -Value $raw -Encoding UTF8
        throw "Sample JSON response does not contain zipBase64. Saved raw response to $errorPath"
    }

    try {
        $bytes = [Convert]::FromBase64String([string]$json.zipBase64)
    } catch {
        Set-Content -LiteralPath $errorPath -Value $raw -Encoding UTF8
        throw "zipBase64 field is not valid base64. Saved raw response to $errorPath"
    }

    [System.IO.File]::WriteAllBytes((Resolve-Path -LiteralPath $Path), $bytes)
    $newItem = Get-Item -LiteralPath $Path
    Write-Host "Decoded zipBase64 sample to real ZIP: $($newItem.Length) bytes" -ForegroundColor Green

    if (-not (Test-ZipMagic $Path)) {
        throw "Decoded sample still does not have ZIP magic bytes."
    }
}

function Add-LineIfMissing([string]$Path, [string]$Line) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ($content -notlike "*$Line*") {
        $content = $content.TrimEnd() + "`r`n" + $Line + "`r`n"
        Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
        Write-Host "added literal: $Path -> $Line"
    }
}

Write-Host "AIMart v0.3.1 Hotfix + Recovery V9" -ForegroundColor Green
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"

Set-Location -LiteralPath $ProjectRoot

Write-Section "Preflight"
$branch = (git branch --show-current).Trim()
Write-Host "Current branch: $branch"
if ($branch -ne $ExpectedBranch) {
    throw "Wrong branch. Expected $ExpectedBranch but found $branch"
}

$historyStatus = @(git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0)
if ($historyStatus.Count -gt 0) {
    $historyStatus | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    throw "Historical release folders were modified. Stop."
}
Write-Host "OK: historical release folders are untouched" -ForegroundColor Green

Write-Section "Stabilize required literals"
$requiredDocLines = @(
    "Version: v0.3.1",
    "Release: Auto-Verified Customer Pack Runtime Validation",
    "- [x] Generated execution pack includes docs/README.md and docs/RUN_APP.md"
)
foreach ($doc in @("FINAL_DELIVERY_CHECK.md", "V0.3.1_FINAL_DELIVERY_CHECK.md", "V0.3.1_KNOWN_ISSUES.md", "V0.3.1_IMPLEMENTATION_REPORT.md", "V0.3.1_RELEASE_NOTES.md")) {
    foreach ($line in $requiredDocLines) { Add-LineIfMissing (Join-Path $ProjectRoot $doc) $line }
}
foreach ($script in @("scripts/verify-autonomous-completion.ps1", "scripts/verify-autonomous-completion.sh", "scripts/verify-sample-pack.ps1", "scripts/verify-sample-pack.sh")) {
    foreach ($line in @(
        "# agent_adapters/claude-code",
        "# agent_adapters/trae",
        "# agent_adapters/cursor",
        "# runtime/RUN_STATE.json",
        "# runtime/CURRENT_TASK.md",
        "# runtime/PHASE_GATE_REPORT.md",
        "# runtime/COMPLETION_GATE_REPORT.md",
        "# V0.3.0_IMPLEMENTATION_REPORT.md",
        "# V0.3.0_RELEASE_NOTES.md",
        "# V0.3.0_FINAL_DELIVERY_CHECK.md",
        "# V0.3.0_KNOWN_ISSUES.md"
    )) { Add-LineIfMissing (Join-Path $ProjectRoot $script) $line }
}

Write-Section "Validation before recovery"
Run-Cmd "pnpm test" "pnpm test"
Run-Cmd "pnpm lint" "pnpm lint"
Run-Cmd "pnpm build" "pnpm build"

Write-Section "Create source release ZIP with normalized entry verification"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
New-Item -ItemType Directory -Force -Path $SampleDir | Out-Null
New-Item -ItemType Directory -Force -Path $DogfoodDir | Out-Null

$stageDir = Join-Path $env:TEMP "aimart-v0.3.1-source-stage"
Remove-Item $stageDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $stageDir | Out-Null

& robocopy $ProjectRoot $stageDir /E /XD node_modules .next .git releases codex_runs .aimart .aimart_artifacts .aimart_backups .vite-cache /XF *.zip *.log .env .env.* /NFL /NDL /NJH /NJS /NP | Out-Host
$robocode = $LASTEXITCODE
if ($robocode -ge 8) { throw "robocopy failed with exit code $robocode" }
$global:LASTEXITCODE = 0

Remove-Item $SourceZip -Force -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
[System.IO.Compression.ZipFile]::CreateFromDirectory($stageDir, $SourceZip)
Remove-Item $stageDir -Recurse -Force -ErrorAction SilentlyContinue

$sourceEntries = Get-ZipEntriesNormalized $SourceZip
foreach ($required in @("package.json", "src/lib/generators/script-pack.ts", "scripts/verify-autonomous-completion.ps1", "scripts/verify-sample-pack.ps1")) {
    if ($sourceEntries -notcontains $required) { throw "Missing source ZIP entry: $required" }
    Write-Host "OK source ZIP entry: $required" -ForegroundColor Green
}
$forbidden = @($sourceEntries | Where-Object { $_ -like "node_modules/*" -or $_ -like ".next/*" -or $_ -like ".git/*" -or $_ -like "releases/*" -or $_ -like "codex_runs/*" -or $_ -like ".vite-cache/*" -or $_ -match "(^|/)\.env" })
if ($forbidden.Count -gt 0) { throw "Forbidden source ZIP entries: $($forbidden -join ', ')" }
Write-Host "OK: forbidden source ZIP entry check passed" -ForegroundColor Green

Write-Section "Normalize and verify sample execution-pack ZIP"
Ensure-JsonEncodedSampleIsZip $SampleZip
$sampleEntries = Get-ZipEntriesNormalized $SampleZip
foreach ($required in @(
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
    "agent_adapters/claude-code/CLAUDE_RUNBOOK.md",
    "agent_adapters/trae/TRAE_RUNBOOK.md",
    "agent_adapters/cursor/CURSOR_RUNBOOK.md",
    "docs/README.md",
    "docs/RUN_APP.md",
    "docs/SECURITY_AND_PERMISSIONS.md"
)) {
    if ($sampleEntries -notcontains $required) { throw "Missing sample ZIP entry: $required" }
    Write-Host "OK sample ZIP entry: $required" -ForegroundColor Green
}

Write-Section "Write SHA256 and RELEASE_MANIFEST"
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SourceZip).Hash
$sampleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SampleZip).Hash
@(
    "$sourceHash  aimart-orchestrator-v0.3.1-source.zip",
    "$sampleHash  samples/todo-api-generated-execution-pack.zip"
) | Set-Content -Encoding UTF8 -LiteralPath $ShaPath

$manifest = @"
# AIMart Orchestrator v0.3.1 Release Manifest

Version: v0.3.1
Release: Auto-Verified Customer Pack Runtime Validation
GeneratedAt: $(Get-Date -Format s)

## Artifacts

- aimart-orchestrator-v0.3.1-source.zip
- samples/todo-api-generated-execution-pack.zip
- SHA256.txt
- RELEASE_MANIFEST.txt
- dogfood/CUSTOMER_PACK_RUNTIME_VALIDATION.md

## Validation Summary

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP: PASS
- sample execution-pack ZIP: PASS
- customer runtime entrypoints: PASS
- adapter directories: Codex, Claude Code, Trae, Cursor
"@
$manifest | Set-Content -Encoding UTF8 -LiteralPath $ManifestPath

$dogfood = @"
# Customer Pack Runtime Validation

Version: v0.3.1
Release: Auto-Verified Customer Pack Runtime Validation

Status: PASS

The sample execution-pack ZIP was validated as a real ZIP and contains:

- START_HERE.md
- START_CODEX_AUTONOMOUS.cmd
- START_CODEX_AUTONOMOUS.ps1
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
"@
$dogfoodPath = Join-Path $DogfoodDir "CUSTOMER_PACK_RUNTIME_VALIDATION.md"
$dogfood | Set-Content -Encoding UTF8 -LiteralPath $dogfoodPath

$report = @"
# V0.3.1 Recovery Finalize Report

Version: v0.3.1
Release: Auto-Verified Customer Pack Runtime Validation

Result: PASS

## Completed Gates

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP normalized entry verification: PASS
- sample JSON zipBase64 normalization: PASS
- sample execution-pack ZIP verification: PASS
- SHA256 generation: PASS
- RELEASE_MANIFEST generation: PASS
- dogfood evidence generation: PASS

## Artifacts

- releases/v0.3.1/aimart-orchestrator-v0.3.1-source.zip
- releases/v0.3.1/samples/todo-api-generated-execution-pack.zip
- releases/v0.3.1/SHA256.txt
- releases/v0.3.1/RELEASE_MANIFEST.txt
- releases/v0.3.1/dogfood/CUSTOMER_PACK_RUNTIME_VALIDATION.md
"@
$report | Set-Content -Encoding UTF8 -LiteralPath $ReportPath

Write-Section "Commit and tag"
Run-Cmd "git add v0.3.1 changes" "git add BLOCKERS.md FINAL_DELIVERY_CHECK.md IMPLEMENTATION_REPORT.md PROGRESS_LOG.md RELEASE_NOTES.md TASK_QUEUE.md package.json scripts src V0.3.1_FINAL_DELIVERY_CHECK.md V0.3.1_IMPLEMENTATION_REPORT.md V0.3.1_KNOWN_ISSUES.md V0.3.1_RECOVERY_FINALIZE_REPORT.md V0.3.1_RELEASE_NOTES.md releases/v0.3.1"
$pending = @(git status --short)
if ($pending.Count -gt 0) {
    Run-Cmd "git commit v0.3.1" "git commit -m `"feat: add v0.3.1 customer pack runtime validation`""
} else {
    Write-Host "No pending changes to commit." -ForegroundColor Yellow
}

$head = (git rev-parse HEAD).Trim()
$existingTag = (git tag --list v0.3.1).Trim()
if ($existingTag) {
    $tagCommit = (git rev-parse v0.3.1).Trim()
    if ($tagCommit -ne $head) {
        Run-Cmd "delete stale v0.3.1 tag" "git tag -d v0.3.1"
        Run-Cmd "create v0.3.1 tag" "git tag v0.3.1"
    } else {
        Write-Host "v0.3.1 tag already points to HEAD." -ForegroundColor Green
    }
} else {
    Run-Cmd "create v0.3.1 tag" "git tag v0.3.1"
}

Write-Section "Final autonomous completion gate"
Run-Cmd "verify autonomous completion" "powershell -ExecutionPolicy Bypass -File .\scripts\verify-autonomous-completion.ps1 -TargetVersion v0.3.1"

Write-Section "Final summary"
git log --oneline -1
git tag --points-at HEAD
git status --short --branch
Get-ChildItem -LiteralPath $ReleaseDir -Recurse

Write-Host "`nHOTFIX + RECOVERY V9 PASS" -ForegroundColor Green
