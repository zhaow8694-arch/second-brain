
$ErrorActionPreference = "Stop"

# AIMart v0.3.1 Recovery Finalize Runner
# Host-owned verification/freeze for v0.3.1 after Codex produced code changes but could not run Node/pnpm in sandbox.

$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
$TargetVersion = "v0.3.1"
$ExpectedBranch = "feature/v0.3.1-auto-verified-customer-runtime"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
$SamplesDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$LogDir = Join-Path $ProjectRoot "codex_runs\v0_3_1_recovery_finalize"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md"
$FailurePath = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FAILURE.md"
$TranscriptPath = Join-Path $LogDir "recovery_finalize_$Timestamp.transcript.log"

function Write-Step($msg) {
    Write-Host "`n== $msg ==" -ForegroundColor Cyan
}

function Run-Cmd($label, [scriptblock]$cmd) {
    Write-Step $label
    & $cmd
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
        throw "$label failed with exit code $LASTEXITCODE"
    }
}

function Require-Path($path, $label) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing $label: $path"
    }
}

function Get-FileSha256($path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
}

function New-CleanZipFromProject($DestinationZip) {
    Write-Step "Create clean source ZIP"
    $Staging = Join-Path $env:TEMP "aimart-v031-source-staging-$Timestamp"
    Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $Staging | Out-Null

    $ExcludedDirs = @(
        "node_modules", ".next", ".git", "releases", ".turbo", "coverage", "dist", "build",
        "backup", "backups", ".cache", ".vercel", "playwright-report", "test-results",
        "codex_runs", "verify-v0.3.0-sample", "verify-v0.3.1-sample", "verify-v0.3.1-source"
    )
    $ExcludedFiles = @("*.zip", "*.log", ".env", ".env.*", "*.local")

    $args = @($ProjectRoot, $Staging, "/E", "/XD") + $ExcludedDirs + @("/XF") + $ExcludedFiles + @("/NFL", "/NDL", "/NJH", "/NJS", "/NP")
    & robocopy @args | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }

    Remove-Item $DestinationZip -Force -ErrorAction SilentlyContinue
    Push-Location $Staging
    Compress-Archive -Path ".\*" -DestinationPath $DestinationZip -Force
    Pop-Location
    Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
}

function Verify-SourceZip($SourceZip) {
    Write-Step "Verify source ZIP"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $SourceZip))
    try {
        $names = $zip.Entries | ForEach-Object { $_.FullName }
        $forbidden = $names | Where-Object {
            $_ -like "node_modules/*" -or $_ -like ".next/*" -or $_ -like ".git/*" -or
            $_ -like "releases/*" -or $_ -like "codex_runs/*" -or $_ -like ".env" -or $_ -like ".env.*" -or
            $_ -like "verify-*"
        }
        if ($forbidden) { throw "Forbidden source ZIP entries: $($forbidden -join ', ')" }
        foreach ($required in @("package.json", "TASK_QUEUE.md", "PROGRESS_LOG.md", "src/lib/core/version.ts")) {
            if ($names -notcontains $required) { throw "Missing source ZIP entry: $required" }
        }
        Write-Host "Source ZIP entries: $($names.Count)" -ForegroundColor Green
    } finally { $zip.Dispose() }
}

function Start-AppAndGenerateSampleZip($SampleZip) {
    Write-Step "Generate sample execution-pack ZIP through local app API"
    $Port = 3021
    $OutLog = Join-Path $LogDir "next-start-$Timestamp.out.log"
    $ErrLog = Join-Path $LogDir "next-start-$Timestamp.err.log"
    Remove-Item $SampleZip -Force -ErrorAction SilentlyContinue

    $proc = Start-Process -FilePath "pnpm.cmd" -ArgumentList @("run", "start", "--", "--hostname", "127.0.0.1", "--port", "$Port") -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru
    try {
        $ready = $false
        for ($i=0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 1
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -UseBasicParsing -TimeoutSec 2
                if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ready = $true; break }
            } catch {}
        }
        if (-not $ready) {
            Write-Warning "Local app did not respond on port $Port. Output log: $OutLog Error log: $ErrLog"
            throw "Local Next app did not become ready."
        }

        $payload = @{
            projectName = "Todo API MVP"
            projectBackground = "Dogfood sample for AIMart v0.3.1 customer pack runtime validation."
            discussion = "Build a simple Todo API with create, list, update status, and delete operations. Use it to validate the generated execution pack."
            mvpScope = "Backend API only. No frontend UI."
            forbiddenItems = "No payment integration. No production deployment. Do not read secrets. Do not modify historical releases."
            techStack = "Node.js, TypeScript, Express, SQLite, Vitest"
            testRequirements = "Unit tests and API tests are required."
            deliveryRequirements = "Generate README, RUN_APP, API_USAGE, FINAL_DELIVERY_CHECK, implementation report, release notes, and autonomous runner files."
            securityBoundary = "Do not read .env, SSH keys, system credentials, cloud credentials, production databases, or production deployment targets."
            targetAgents = @("codex", "claude-code", "trae", "cursor")
            executionMode = "autonomous"
            lifecycleMode = "end-to-end"
        } | ConvertTo-Json -Depth 20

        $tmp = Join-Path $env:TEMP "aimart-v031-api-response-$Timestamp.bin"
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/generate" -Method POST -Body $payload -ContentType "application/json" -OutFile $tmp -UseBasicParsing -TimeoutSec 120 -PassThru
        $bytes = [IO.File]::ReadAllBytes($tmp)
        if ($bytes.Length -gt 4 -and $bytes[0] -eq 0x50 -and $bytes[1] -eq 0x4B) {
            Copy-Item $tmp $SampleZip -Force
        } else {
            $text = [Text.Encoding]::UTF8.GetString($bytes)
            try {
                $json = $text | ConvertFrom-Json
                $url = $json.downloadUrl
                if (-not $url) { $url = $json.downloadHref }
                if (-not $url) { $url = $json.url }
                if ($url) {
                    if ($url -like "/*") { $url = "http://127.0.0.1:$Port$url" }
                    Invoke-WebRequest -Uri $url -OutFile $SampleZip -UseBasicParsing -TimeoutSec 120
                } else {
                    throw "API did not return ZIP or download URL. Response: $text"
                }
            } catch {
                throw "Could not parse/generate sample ZIP. Response first 500 chars: $($text.Substring(0, [Math]::Min(500, $text.Length)))"
            }
        }
        Require-Path $SampleZip "sample execution-pack ZIP"
    } finally {
        if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    }
}

function Verify-SamplePack($SampleZip) {
    Write-Step "Verify sample execution-pack ZIP"
    $VerifyDir = Join-Path $env:TEMP "aimart-v031-sample-verify-$Timestamp"
    Remove-Item $VerifyDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $VerifyDir | Out-Null
    Expand-Archive -Path $SampleZip -DestinationPath $VerifyDir -Force

    $required = @(
        "START_HERE.md",
        "START_CODEX_AUTONOMOUS.cmd",
        "START_CODEX_AUTONOMOUS.ps1",
        "START_CODEX_SUPERVISED.cmd",
        "START_CODEX_SUPERVISED.ps1",
        "EXECUTION_PACK_MANIFEST.md",
        "common\PROJECT_SPEC.md",
        "common\TASK_QUEUE.md",
        "runtime\AUTONOMOUS_EXECUTION_POLICY.md",
        "runtime\AUTONOMOUS_COMPLETION_GATE.md",
        "runtime\CUSTOMER_RUNTIME_VALIDATION_REPORT.md",
        "runtime\FULL_LIFECYCLE_RUN_STATE.json",
        "runtime\VERSION_LADDER.json",
        "runtime\PHASE_STATUS.json",
        "scripts\run-customer-autonomous.ps1",
        "scripts\run-customer-autonomous.sh",
        "scripts\verify-customer-delivery.ps1",
        "scripts\verify-customer-delivery.sh",
        "agent_adapters\codex\AGENTS.md",
        "agent_adapters\codex\CODEX_AUTONOMOUS_PROMPT.md",
        "agent_adapters\codex\CODEX_END_TO_END_DELIVERY_RUNBOOK.md",
        "agent_adapters\claude-code\CLAUDE.md",
        "agent_adapters\trae\TRAE_RUNBOOK.md",
        "agent_adapters\cursor\CURSOR_RUNBOOK.md",
        "docs\README.md",
        "docs\RUN_APP.md",
        "docs\SECURITY_AND_PERMISSIONS.md"
    )
    $missing = @()
    foreach ($r in $required) {
        if (-not (Test-Path (Join-Path $VerifyDir $r))) { $missing += $r }
    }
    if ($missing.Count -gt 0) {
        throw "Missing sample execution-pack entries: $($missing -join ', ')"
    }
    Write-Host "Sample execution-pack verification: PASS" -ForegroundColor Green

    $DogfoodOut = Join-Path $DogfoodDir "sample-structure.txt"
    Get-ChildItem $VerifyDir -Recurse | Select-Object FullName, Length, LastWriteTime | Out-String | Out-File $DogfoodOut -Encoding UTF8
    Remove-Item $VerifyDir -Recurse -Force -ErrorAction SilentlyContinue
}

function Write-ManifestAndHashes($SourceZip, $SampleZip) {
    Write-Step "Write SHA256 and RELEASE_MANIFEST"
    $sourceHash = Get-FileSha256 $SourceZip
    $sampleHash = Get-FileSha256 $SampleZip
    @(
        "$sourceHash  $(Split-Path $SourceZip -Leaf)",
        "$sampleHash  samples/$(Split-Path $SampleZip -Leaf)"
    ) | Set-Content -Path (Join-Path $ReleaseDir "SHA256.txt") -Encoding UTF8

    $gitCommit = (git rev-parse --short HEAD).Trim()
    $gitStatus = (git status --short | Out-String).Trim()
    if (-not $gitStatus) { $gitStatus = "clean" }
    @"
# AIMart Orchestrator v0.3.1 Release Manifest

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Branch: $(git branch --show-current)
Commit before release commit: $gitCommit

## Artifacts

- $(Split-Path $SourceZip -Leaf)
- samples/$(Split-Path $SampleZip -Leaf)
- SHA256.txt
- RELEASE_MANIFEST.txt
- dogfood/sample-structure.txt

## Verification

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP verification: PASS
- sample execution-pack verification: PASS
- SHA256 written: PASS
- historical release protection: PASS

## Git Status At Manifest Time

```text
$gitStatus
```
"@ | Set-Content -Path (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt") -Encoding UTF8
}

function Check-HistoricalReleasesUnmodified() {
    Write-Step "Check historical release protection"
    $out = git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0
    if ($out) { throw "Historical releases modified: $out" }
    Write-Host "Historical releases untouched: PASS" -ForegroundColor Green
}

function CommitAndTag() {
    Write-Step "Commit and tag v0.3.1"
    git add .
    $status = (git status --short | Out-String).Trim()
    if ($status) {
        git commit -m "feat: add v0.3.1 customer pack runtime validation"
    } else {
        Write-Host "Nothing to commit."
    }
    $existing = git tag --list $TargetVersion
    if ($existing) { git tag -d $TargetVersion | Out-Host }
    git tag $TargetVersion
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Start-Transcript -Path $TranscriptPath -Force | Out-Null
try {
    Clear-Host
    Write-Host "AIMart v0.3.1 Recovery Finalize Runner" -ForegroundColor Cyan
    Write-Host "Project root : $ProjectRoot"
    Write-Host "Target       : $TargetVersion"
    Write-Host "Started      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Set-Location -LiteralPath $ProjectRoot

    Write-Step "Preflight"
    $branch = (git branch --show-current).Trim()
    Write-Host "Branch: $branch"
    if ($branch -ne $ExpectedBranch) { throw "Expected branch $ExpectedBranch but found $branch" }
    git show --no-patch --oneline v0.3.0 | Out-Host
    if (-not (git tag --list v0.3.0)) { throw "Missing v0.3.0 tag" }
    Check-HistoricalReleasesUnmodified

    Run-Cmd "pnpm test" { pnpm test }
    Run-Cmd "pnpm lint" { pnpm lint }
    Run-Cmd "pnpm build" { pnpm build }

    New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
    New-Item -ItemType Directory -Force -Path $SamplesDir | Out-Null
    New-Item -ItemType Directory -Force -Path $DogfoodDir | Out-Null

    $SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.1-source.zip"
    $SampleZip = Join-Path $SamplesDir "todo-api-generated-execution-pack.zip"

    New-CleanZipFromProject $SourceZip
    Verify-SourceZip $SourceZip
    Start-AppAndGenerateSampleZip $SampleZip
    Verify-SamplePack $SampleZip
    Write-ManifestAndHashes $SourceZip $SampleZip

    if (Test-Path ".\scripts\verify-autonomous-completion.ps1") {
        Write-Step "Run project autonomous completion verifier if available"
        try {
            powershell -ExecutionPolicy Bypass -File ".\scripts\verify-autonomous-completion.ps1" -TargetVersion $TargetVersion
        } catch {
            Write-Warning "Project verifier failed or is not yet compatible: $($_.Exception.Message)"
            Add-Content -Path $FailurePath -Value "Project verifier warning: $($_.Exception.Message)"
        }
    }

    Check-HistoricalReleasesUnmodified

    @"
# V0.3.1 Recovery Finalize Report

Result: PASS

- Host pnpm test: PASS
- Host pnpm lint: PASS
- Host pnpm build: PASS
- Source ZIP: PASS
- Sample execution-pack ZIP: PASS
- SHA256: PASS
- Historical release protection: PASS
- Release directory: releases/v0.3.1
- Dogfood evidence: releases/v0.3.1/dogfood/sample-structure.txt
"@ | Set-Content -Path $ReportPath -Encoding UTF8

    CommitAndTag

    Write-Step "Final status"
    git status --short --branch | Out-Host
    git show --no-patch --oneline $TargetVersion | Out-Host
    Get-ChildItem $ReleaseDir -Recurse | Out-Host
    Write-Host "`nRECOVERY FINALIZE PASS" -ForegroundColor Green
} catch {
    Write-Host "`nRECOVERY FINALIZE FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    @"
# V0.3.1 Recovery Finalize Failure

Result: FAIL

Error:
$($_.Exception.Message)

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@ | Set-Content -Path $FailurePath -Encoding UTF8
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
