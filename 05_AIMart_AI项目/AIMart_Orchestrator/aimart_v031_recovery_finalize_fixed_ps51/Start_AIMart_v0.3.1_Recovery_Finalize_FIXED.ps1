param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.3.1",
    [switch]$SkipCommit
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "== $Title ==" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "OK: $Message" -ForegroundColor Green
}

function Write-Warn([string]$Message) {
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Assert-PathExists([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing ${Label}: ${Path}"
    }
}

function Invoke-CheckedCommand([string]$CommandLine, [string]$Label) {
    Write-Host "Running: $Label" -ForegroundColor Cyan
    Write-Host "  $CommandLine"
    cmd.exe /c $CommandLine
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (${Label}) with exit code ${LASTEXITCODE}: ${CommandLine}"
    }
    Write-Ok "$Label passed"
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function New-CleanDirectory([string]$Path) {
    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-ZipEntryNames([string]$ZipPath) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ZipPath))
    try {
        return @($zip.Entries | ForEach-Object { $_.FullName })
    } finally {
        $zip.Dispose()
    }
}

function Assert-ZipDoesNotContain([string]$ZipPath, [string[]]$ForbiddenPatterns) {
    $names = Get-ZipEntryNames $ZipPath
    $bad = @()
    foreach ($name in $names) {
        foreach ($pattern in $ForbiddenPatterns) {
            if ($name -like $pattern) {
                $bad += $name
                break
            }
        }
    }
    if ($bad.Count -gt 0) {
        throw "Source ZIP contains forbidden entries: $($bad -join ', ')"
    }
    Write-Ok "source ZIP forbidden-entry check passed"
}

function Assert-ZipContains([string]$ZipPath, [string[]]$RequiredEntries) {
    $names = Get-ZipEntryNames $ZipPath
    foreach ($entry in $RequiredEntries) {
        if ($names -notcontains $entry) {
            throw "ZIP is missing required entry: ${entry}"
        }
    }
    Write-Ok "sample execution-pack required-entry check passed"
}

function Write-Report([string]$Path, [string]$Status, [string]$Body) {
@"
# V0.3.1 Recovery Finalize Report

Version: v0.3.1
Status: $Status
Generated At: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

$Body
"@ | Out-File -LiteralPath $Path -Encoding UTF8
}

try {
    Write-Section "AIMart v0.3.1 Recovery Finalize — FIXED PS5.1"
    Write-Host "Project root  : $ProjectRoot"
    Write-Host "Target version: $TargetVersion"

    Assert-PathExists $ProjectRoot "project root"
    Set-Location -LiteralPath $ProjectRoot

    $Branch = (git branch --show-current).Trim()
    Write-Host "Current branch: $Branch"
    if ($Branch -ne "feature/v0.3.1-auto-verified-customer-runtime") {
        throw "Expected branch feature/v0.3.1-auto-verified-customer-runtime but got ${Branch}"
    }

    Write-Section "Historical release protection"
    $HistoryStatus = (git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0 | Out-String).Trim()
    if ($HistoryStatus) {
        throw "Historical release folders have changes. Refusing to continue.`n$HistoryStatus"
    }
    Write-Ok "historical release folders are untouched"

    Write-Section "Validation commands"
    Invoke-CheckedCommand "pnpm test" "pnpm test"
    Invoke-CheckedCommand "pnpm lint" "pnpm lint"
    Invoke-CheckedCommand "pnpm build" "pnpm build"

    $ReleaseDir = Join-Path $ProjectRoot "releases\v0.3.1"
    $SamplesDir = Join-Path $ReleaseDir "samples"
    New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
    New-Item -ItemType Directory -Force -Path $SamplesDir | Out-Null

    Write-Section "Create source release ZIP"
    $SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.1-source.zip"
    $StagingDir = Join-Path $env:TEMP "aimart-v031-source-staging"
    New-CleanDirectory $StagingDir

    $ExcludedDirs = @(
        "node_modules", ".next", ".git", "releases", "codex_runs", ".aimart", ".aimart_artifacts", ".aimart_backups",
        ".turbo", "coverage", "dist", "build", "backup", "backups", ".cache", ".vercel", "playwright-report", "test-results",
        "verify-v0.2.1-sample", "verify-v0.3.0-sample", "verify-v0.3.1-sample"
    )
    $ExcludedFiles = @("*.zip", "*.log", ".env", ".env.*", "*.local")
    $RoboArgs = @($ProjectRoot, $StagingDir, "/E", "/XD") + $ExcludedDirs + @("/XF") + $ExcludedFiles + @("/NFL", "/NDL", "/NJH", "/NJS", "/NP")
    & robocopy @RoboArgs | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code ${LASTEXITCODE}"
    }

    Remove-Item -LiteralPath $SourceZip -Force -ErrorAction SilentlyContinue
    Push-Location $StagingDir
    Compress-Archive -Path ".\*" -DestinationPath $SourceZip -Force
    Pop-Location
    Remove-Item -LiteralPath $StagingDir -Recurse -Force -ErrorAction SilentlyContinue
    Assert-PathExists $SourceZip "source ZIP"
    Write-Ok "source ZIP created: $SourceZip"

    Assert-ZipDoesNotContain $SourceZip @(
        "node_modules/*", ".next/*", ".git/*", "releases/*", "codex_runs/*", ".env", ".env.*", "*.pem", "*.key", "*.pfx"
    )

    Write-Section "Generate sample execution-pack ZIP"
    $SampleZip = Join-Path $SamplesDir "todo-api-generated-execution-pack.zip"
    Remove-Item -LiteralPath $SampleZip -Force -ErrorAction SilentlyContinue

    $Port = 3121
    $ServerOut = Join-Path $env:TEMP "aimart-v031-next.out.log"
    $ServerErr = Join-Path $env:TEMP "aimart-v031-next.err.log"
    Remove-Item -LiteralPath $ServerOut -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $ServerErr -Force -ErrorAction SilentlyContinue

    $Server = Start-Process -FilePath "pnpm.cmd" -ArgumentList @("run", "start", "--", "--hostname", "127.0.0.1", "--port", "$Port") -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $ServerOut -RedirectStandardError $ServerErr -PassThru
    try {
        $Ready = $false
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 1
            try {
                $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -UseBasicParsing -TimeoutSec 2
                if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                    $Ready = $true
                    break
                }
            } catch {}
        }
        if (-not $Ready) {
            throw "Next.js server did not become ready on port ${Port}. STDERR: $(Get-Content -LiteralPath $ServerErr -Raw -ErrorAction SilentlyContinue)"
        }

        $Payload = @{
            projectName = "Todo API MVP"
            projectBackground = "Dogfood sample for AIMart v0.3.1 customer runtime validation."
            discussion = "Build a simple Todo API with create, list, update status, and delete operations. The generated execution pack must include customer start entrypoints, lifecycle state, completion gates, and agent adapters."
            mvpScope = "Backend API only. No frontend UI."
            forbiddenItems = "No payment integration. No production deployment. No reading secrets. No real database migration."
            techStack = "Node.js, TypeScript, Express, SQLite, Vitest"
            testRequirements = "Unit tests and API tests are required. Completion gate must pass before delivery."
            deliveryRequirements = "Generate README, RUN_APP, SECURITY_AND_PERMISSIONS, final delivery check, release notes, and customer autonomous entrypoints."
            securityBoundary = "Do not read .env, SSH keys, cloud credentials, or system secrets."
            selectedAgents = @("codex", "claude-code", "trae", "cursor")
            executionMode = "autonomous"
            deliveryMode = "end-to-end"
        }
        $Json = $Payload | ConvertTo-Json -Depth 10
        $TmpResponse = Join-Path $env:TEMP "aimart-v031-generate-response.bin"
        Remove-Item -LiteralPath $TmpResponse -Force -ErrorAction SilentlyContinue
        Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/generate" -Method Post -ContentType "application/json" -Body $Json -OutFile $TmpResponse -UseBasicParsing -TimeoutSec 120
        Copy-Item -LiteralPath $TmpResponse -Destination $SampleZip -Force
    } finally {
        if ($Server -and -not $Server.HasExited) {
            Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
        }
    }

    Assert-PathExists $SampleZip "sample execution-pack ZIP"
    Write-Ok "sample execution-pack ZIP created: $SampleZip"

    $RequiredSampleEntries = @(
        "START_HERE.md",
        "START_CODEX_AUTONOMOUS.cmd",
        "START_CODEX_AUTONOMOUS.ps1",
        "START_CODEX_SUPERVISED.cmd",
        "START_CODEX_SUPERVISED.ps1",
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
        "scripts/run-customer-autonomous.sh",
        "scripts/verify-customer-delivery.ps1",
        "scripts/verify-customer-delivery.sh",
        "agent_adapters/codex/AGENTS.md",
        "agent_adapters/codex/CODEX_AUTONOMOUS_PROMPT.md",
        "agent_adapters/claude-code/CLAUDE.md",
        "agent_adapters/trae/TRAE_RUNBOOK.md",
        "agent_adapters/cursor/CURSOR_RUNBOOK.md",
        "docs/README.md",
        "docs/RUN_APP.md",
        "docs/SECURITY_AND_PERMISSIONS.md"
    )
    Assert-ZipContains $SampleZip $RequiredSampleEntries

    Write-Section "Write SHA256 and release manifest"
    $SourceHash = Get-FileSha256 $SourceZip
    $SampleHash = Get-FileSha256 $SampleZip
    $ShaPath = Join-Path $ReleaseDir "SHA256.txt"
    @(
        "$SourceHash  aimart-orchestrator-v0.3.1-source.zip",
        "$SampleHash  samples/todo-api-generated-execution-pack.zip"
    ) | Out-File -LiteralPath $ShaPath -Encoding UTF8

    $ManifestPath = Join-Path $ReleaseDir "RELEASE_MANIFEST.txt"
@"
# AIMart Orchestrator v0.3.1 Release Manifest

Generated At: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Artifacts

- aimart-orchestrator-v0.3.1-source.zip
- samples/todo-api-generated-execution-pack.zip
- SHA256.txt
- RELEASE_MANIFEST.txt

## Verification

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP forbidden-entry check: PASS
- sample execution-pack required entries: PASS
- historical release protection: PASS

## Customer Runtime Validation

The sample execution pack includes customer-facing START_HERE and START_CODEX entrypoints, lifecycle runtime state files, customer delivery verification scripts, and independent agent adapters for Codex, Claude Code, Trae, and Cursor.
"@ | Out-File -LiteralPath $ManifestPath -Encoding UTF8

    Write-Section "Write recovery finalize report"
    $ReportPath = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md"
    Write-Report $ReportPath "PASS" @"
## Checks

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- release directory: PASS
- source ZIP: PASS
- sample execution-pack ZIP: PASS
- SHA256: PASS
- source ZIP forbidden entries: PASS
- sample required entries: PASS
- historical releases untouched: PASS

## Artifacts

- releases/v0.3.1/aimart-orchestrator-v0.3.1-source.zip
- releases/v0.3.1/samples/todo-api-generated-execution-pack.zip
- releases/v0.3.1/SHA256.txt
- releases/v0.3.1/RELEASE_MANIFEST.txt
"@

    $KnownIssues = Join-Path $ProjectRoot "V0.3.1_KNOWN_ISSUES.md"
    if (Test-Path -LiteralPath $KnownIssues) {
        Add-Content -LiteralPath $KnownIssues -Encoding UTF8 -Value "`nRecovery Finalize status: PASS. No P0/P1 blocker found during host-side recovery finalize."
    }

    Write-Section "Commit and tag"
    git add .
    $StatusBeforeCommit = (git status --short | Out-String).Trim()
    if ($StatusBeforeCommit) {
        git commit -m "feat: add v0.3.1 customer pack runtime validation"
    } else {
        Write-Warn "No changes to commit."
    }

    $ExistingTag = (git tag --list "v0.3.1" | Out-String).Trim()
    if ($ExistingTag) {
        git tag -d v0.3.1
    }
    git tag v0.3.1

    Write-Section "Final status"
    git status --short --branch
    git show --no-patch --oneline v0.3.1
    Get-ChildItem -LiteralPath $ReleaseDir -Recurse

    Write-Host ""
    Write-Host "RECOVERY FINALIZE PASS" -ForegroundColor Green
    exit 0
} catch {
    Write-Host ""
    Write-Host "RECOVERY FINALIZE FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    try {
        $ReportPath = Join-Path $ProjectRoot "V0.3.1_RECOVERY_FINALIZE_REPORT.md"
        Write-Report $ReportPath "FAIL" "Error: $($_.Exception.Message)"
    } catch {}
    exit 1
}
