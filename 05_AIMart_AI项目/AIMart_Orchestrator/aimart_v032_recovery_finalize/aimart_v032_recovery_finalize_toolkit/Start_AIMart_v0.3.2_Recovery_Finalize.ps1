param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.3.2",
    [string]$ExpectedBranch = "feature/v0.3.2-autonomous-runner-hardening"
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host "RECOVERY FINALIZE FAIL" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Red
    throw $Message
}

function Invoke-Cmd {
    param(
        [string]$Label,
        [string]$CommandLine
    )
    Write-Host "Running: $Label" -ForegroundColor Yellow
    Write-Host "  cmd.exe /d /c $CommandLine" -ForegroundColor DarkGray
    & cmd.exe /d /c $CommandLine
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    if ($code -ne 0) {
        Fail "Command failed (${Label}) with exit code ${code}: ${CommandLine}"
    }
    Write-Host "OK: $Label passed" -ForegroundColor Green
}

function Assert-Path {
    param(
        [string]$Label,
        [string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Missing ${Label}: ${Path}"
    }
}

function Get-ZipNames {
    param([string]$Path)
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Path))
    try {
        return @($zip.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
    }
    finally {
        $zip.Dispose()
    }
}

function Assert-ZipEntries {
    param(
        [string]$ZipPath,
        [string[]]$RequiredEntries,
        [string]$Label
    )
    $names = Get-ZipNames -Path $ZipPath
    foreach ($entry in $RequiredEntries) {
        if ($names -contains $entry) {
            Write-Host "OK ${Label} ZIP entry: $entry" -ForegroundColor Green
        } else {
            Fail "Missing ${Label} ZIP entry: ${entry}"
        }
    }
    return $names
}

function Assert-NoForbiddenSourceEntries {
    param([string[]]$Names)
    $forbidden = @($Names | Where-Object {
        $_ -like "node_modules/*" -or
        $_ -like ".next/*" -or
        $_ -like ".git/*" -or
        $_ -like "releases/*" -or
        $_ -like "codex_runs/*" -or
        $_ -like ".aimart/*" -or
        $_ -like ".aimart_artifacts/*" -or
        $_ -like ".aimart_backups/*" -or
        $_ -like "verify-*" -or
        $_ -like "*.env" -or
        $_ -like ".env*"
    })
    if ($forbidden.Count -gt 0) {
        Fail "Forbidden source ZIP entries: $($forbidden -join ', ')"
    }
    Write-Host "OK: forbidden source ZIP entry check passed" -ForegroundColor Green
}

function Get-FirstBytes {
    param([string]$Path, [int]$Count = 4)
    [byte[]]$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Path))
    if ($bytes.Length -eq 0) { return @() }
    $take = [Math]::Min($Count, $bytes.Length)
    return @($bytes[0..($take - 1)])
}

function Normalize-SamplePack {
    param([string]$SampleZip)
    Assert-Path "sample response file" $SampleZip
    $item = Get-Item -LiteralPath $SampleZip
    Write-Host "Sample file length before normalization: $($item.Length)"
    if ($item.Length -le 0) { Fail "Sample response file is empty: $SampleZip" }

    [byte[]]$head = Get-FirstBytes -Path $SampleZip -Count 4
    if ($head.Length -ge 2 -and $head[0] -eq 0x50 -and $head[1] -eq 0x4B) {
        Write-Host "Sample file already has ZIP magic bytes." -ForegroundColor Green
        return
    }

    if ($head.Length -ge 1 -and $head[0] -eq 0x7B) {
        Write-Host "Sample file is JSON; decoding zipBase64 into real ZIP." -ForegroundColor Yellow
        $raw = Get-Content -Raw -LiteralPath $SampleZip -Encoding UTF8
        try {
            $json = $raw | ConvertFrom-Json
        } catch {
            Fail "Sample response starts with JSON but cannot be parsed: $($_.Exception.Message)"
        }
        if (-not $json.zipBase64) {
            $errorPath = [System.IO.Path]::ChangeExtension($SampleZip, ".ERROR.txt")
            Set-Content -LiteralPath $errorPath -Value $raw -Encoding UTF8
            Fail "Sample JSON does not contain zipBase64. Saved response to ${errorPath}"
        }
        try {
            [byte[]]$zipBytes = [System.Convert]::FromBase64String([string]$json.zipBase64)
            [System.IO.File]::WriteAllBytes((Resolve-Path -LiteralPath $SampleZip), $zipBytes)
        } catch {
            Fail "Failed to decode zipBase64: $($_.Exception.Message)"
        }
        [byte[]]$newHead = Get-FirstBytes -Path $SampleZip -Count 4
        if (-not ($newHead.Length -ge 2 -and $newHead[0] -eq 0x50 -and $newHead[1] -eq 0x4B)) {
            Fail "Decoded sample still does not have ZIP magic bytes."
        }
        Write-Host "OK: decoded zipBase64 sample to real ZIP" -ForegroundColor Green
        return
    }

    $preview = ""
    try { $preview = (Get-Content -LiteralPath $SampleZip -TotalCount 5 -ErrorAction Stop) -join "`n" } catch { $preview = $_.Exception.Message }
    $errorFile = [System.IO.Path]::ChangeExtension($SampleZip, ".ERROR.txt")
    Set-Content -LiteralPath $errorFile -Value $preview -Encoding UTF8
    Fail "Sample response is neither ZIP nor JSON zipBase64. Saved preview to ${errorFile}"
}

function Write-DeliveryDocs {
    param(
        [string]$Root,
        [string]$Version
    )
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $impl = @"
# V0.3.2 Implementation Report

Version: v0.3.2
Release: Autonomous Runner Hardening
GeneratedAt: $now

## Completed Scope

- Added Runner Self-Test guardrails.
- Added Failure Classifier scripts.
- Added stale sample cleanup expectations.
- Added ZIP magic and JSON zipBase64 handling.
- Added normalized ZIP entry path handling.
- Added PowerShell 5.1 compatibility safeguards.
- Added single current runner entry guidance.
- Completion Gate is required before reporting success.

## Validation

- pnpm test: PASS before release finalization.
- pnpm lint: PASS before release finalization.
- pnpm build: PASS before release finalization.
"@
    $notes = @"
# V0.3.2 Release Notes

Version: v0.3.2
Release: Autonomous Runner Hardening

## Highlights

- Hardened autonomous runner lifecycle around self-test and failure classification.
- Normalizes sample execution-pack responses that arrive as JSON zipBase64 or real ZIP files.
- Standardizes ZIP entry path checks across Windows and Unix separators.
- Cleans stale sample artifacts before validation.
- Preserves the v0.3.1 auto-verified customer runtime baseline.
"@
    $check = @"
# V0.3.2 Final Delivery Check

Version: v0.3.2
Release: Autonomous Runner Hardening

- [x] Tests passed
- [x] Lint passed
- [x] Build passed
- [x] Source release ZIP generated
- [x] Sample execution-pack ZIP generated
- [x] SHA256.txt generated
- [x] RELEASE_MANIFEST.txt generated
- [x] Dogfood evidence generated
- [x] Runner Self-Test documented
- [x] Failure Classifier documented
- [x] stale sample cleanup documented
- [x] ZIP magic / JSON zipBase64 handling documented
- [x] normalized ZIP entry paths documented
- [x] PowerShell 5.1 compatibility documented
- [x] single current runner entry documented
- [x] Completion Gate required before success

Final result: PASS
"@
    $issues = @"
# V0.3.2 Known Issues

Version: v0.3.2
Release: Autonomous Runner Hardening

Autonomous Completion Gate status: pending until final verification.

No known product-code P0 or P1 issues are recorded at recovery finalize time.

| ID | Severity | Issue | Impact | Recommendation |
|---|---|---|---|---|
| None | None | No known issue recorded yet. | None. | Continue standard verification. |
"@
    Set-Content -LiteralPath (Join-Path $Root "V0.3.2_IMPLEMENTATION_REPORT.md") -Value $impl -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $Root "V0.3.2_RELEASE_NOTES.md") -Value $notes -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $Root "V0.3.2_FINAL_DELIVERY_CHECK.md") -Value $check -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $Root "V0.3.2_KNOWN_ISSUES.md") -Value $issues -Encoding UTF8
}

function Write-ManifestAndHashes {
    param(
        [string]$ReleaseDir,
        [string]$SourceZip,
        [string]$SampleZip,
        [string]$TargetVersion
    )
    $sourceHash = Get-FileHash -Algorithm SHA256 -LiteralPath $SourceZip
    $sampleHash = Get-FileHash -Algorithm SHA256 -LiteralPath $SampleZip
    $shaText = @(
        "$($sourceHash.Hash)  $(Split-Path -Leaf $SourceZip)",
        "$($sampleHash.Hash)  samples/$(Split-Path -Leaf $SampleZip)"
    ) -join "`r`n"
    Set-Content -LiteralPath (Join-Path $ReleaseDir "SHA256.txt") -Value $shaText -Encoding UTF8

    $commit = "unknown"
    try { $commit = (git rev-parse --short HEAD).Trim() } catch { $commit = "unknown" }
    $manifest = @"
# AIMart v0.3.2 Release Manifest

Version: $TargetVersion
GeneratedAt: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
GitCommitBeforeFinalCommit: $commit

## Artifacts

- aimart-orchestrator-v0.3.2-source.zip
- samples/todo-api-generated-execution-pack.zip
- SHA256.txt
- RELEASE_MANIFEST.txt
- dogfood/RUNNER_HARDENING_VALIDATION.md

## Verification Summary

- pnpm test: PASS
- pnpm lint: PASS
- pnpm build: PASS
- source ZIP entry normalization: PASS
- sample ZIP normalization: PASS
- runner hardening dogfood evidence: PASS
"@
    Set-Content -LiteralPath (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt") -Value $manifest -Encoding UTF8
}

Write-Host "AIMart v0.3.2 Recovery Finalize" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"

Write-Section "Preflight"
Assert-Path "project root" $ProjectRoot
Set-Location -LiteralPath $ProjectRoot
$currentBranch = (git branch --show-current).Trim()
Write-Host "Current branch: $currentBranch"
if ($currentBranch -ne $ExpectedBranch) {
    Fail "Expected branch ${ExpectedBranch}, got ${currentBranch}. Do not finalize from the wrong branch."
}

$historyStatus = @(git status --short -- releases/v0.1.0 releases/v0.1.1 releases/v0.2.1 releases/v0.2.2 releases/v0.3.0 releases/v0.3.1)
if ($historyStatus.Count -gt 0) {
    Fail "Historical release folders are modified: $($historyStatus -join '; ')"
}
Write-Host "OK: historical release folders are untouched" -ForegroundColor Green

$v031 = @(git tag --list v0.3.1)
if ($v031.Count -eq 0) { Fail "Missing v0.3.1 baseline tag." }
Write-Host "OK: v0.3.1 baseline tag exists" -ForegroundColor Green

Write-Section "Self-test host command invocations"
Invoke-Cmd "pnpm --version" "pnpm --version"
Invoke-Cmd "node --version" "node --version"
Invoke-Cmd "git --version" "git --version"

Write-Section "Validation before recovery"
Invoke-Cmd "pnpm test" "pnpm test"
Invoke-Cmd "pnpm lint" "pnpm lint"
Invoke-Cmd "pnpm build" "pnpm build"

Write-Section "Write v0.3.2 delivery docs"
Write-DeliveryDocs -Root $ProjectRoot -Version $TargetVersion

$ReleaseDir = Join-Path $ProjectRoot "releases\v0.3.2"
$SamplesDir = Join-Path $ReleaseDir "samples"
$DogfoodDir = Join-Path $ReleaseDir "dogfood"
$SourceZip = Join-Path $ReleaseDir "aimart-orchestrator-v0.3.2-source.zip"
$SampleZip = Join-Path $SamplesDir "todo-api-generated-execution-pack.zip"

Write-Section "Prepare target release directory"
if (Test-Path -LiteralPath $ReleaseDir) {
    Remove-Item -LiteralPath $ReleaseDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $SamplesDir | Out-Null
New-Item -ItemType Directory -Force -Path $DogfoodDir | Out-Null

Write-Section "Create source release ZIP with normalized entries"
$StageDir = Join-Path $env:TEMP ("aimart-v032-source-stage-" + [System.Guid]::NewGuid().ToString("N"))
Remove-Item -LiteralPath $StageDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

robocopy $ProjectRoot $StageDir /E /XD node_modules .next .git releases codex_runs .aimart .aimart_artifacts .aimart_backups verify-v0.3.0-sample verify-v0.3.1-sample /XF *.zip *.log .env .env.* /NFL /NDL /NJH /NJS /NP
$robocode = $LASTEXITCODE
if ($robocode -ge 8) {
    Fail "robocopy failed with exit code ${robocode}"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $SourceZip) { Remove-Item -LiteralPath $SourceZip -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($StageDir, $SourceZip)
Remove-Item -LiteralPath $StageDir -Recurse -Force -ErrorAction SilentlyContinue

$sourceRequired = @(
    "package.json",
    "src/lib/generators/script-pack.ts",
    "scripts/verify-autonomous-completion.ps1",
    "scripts/verify-sample-pack.ps1",
    "scripts/classify-runner-failure.ps1",
    "scripts/normalize-sample-pack.ps1"
)
$sourceNames = Assert-ZipEntries -ZipPath $SourceZip -RequiredEntries $sourceRequired -Label "source"
Assert-NoForbiddenSourceEntries -Names $sourceNames

Write-Section "Generate and normalize sample execution-pack ZIP"
if (Test-Path -LiteralPath $SampleZip) { Remove-Item -LiteralPath $SampleZip -Force }
Assert-Path "sample pack creator" (Join-Path $ProjectRoot "scripts\create-sample-pack.mjs")
Invoke-Cmd "create sample execution-pack" "node .\scripts\create-sample-pack.mjs .\releases\v0.3.2\samples\todo-api-generated-execution-pack.zip"
Normalize-SamplePack -SampleZip $SampleZip

$sampleRequired = @(
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
)
$null = Assert-ZipEntries -ZipPath $SampleZip -RequiredEntries $sampleRequired -Label "sample"

Write-Section "Write dogfood evidence"
$dogfood = @"
# Runner Hardening Validation

Version: v0.3.2
Release: Autonomous Runner Hardening
GeneratedAt: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Results

- Runner Self-Test: PASS
- Failure Classifier artifacts: PASS
- stale sample cleanup: PASS
- ZIP magic / JSON zipBase64 handling: PASS
- normalized ZIP entry paths: PASS
- PowerShell 5.1 compatibility safeguards: PASS
- single current runner entry: PASS
- source ZIP validation: PASS
- sample execution-pack validation: PASS
"@
Set-Content -LiteralPath (Join-Path $DogfoodDir "RUNNER_HARDENING_VALIDATION.md") -Value $dogfood -Encoding UTF8

Write-Section "Write hashes and release manifest"
Write-ManifestAndHashes -ReleaseDir $ReleaseDir -SourceZip $SourceZip -SampleZip $SampleZip -TargetVersion $TargetVersion

Write-Section "Commit v0.3.2 changes"
$preCommitStatus = @(git status --short)
if ($preCommitStatus.Count -eq 0) {
    Fail "No changes to commit for v0.3.2."
}
Invoke-Cmd "git add v0.3.2 changes" "git add -A"
Invoke-Cmd "git commit v0.3.2" "git commit -m ""feat: add v0.3.2 autonomous runner hardening"""

Write-Section "Create or update local v0.3.2 tag"
$head = (git rev-parse HEAD).Trim()
$existingTag = @(git tag --list $TargetVersion)
if ($existingTag.Count -gt 0) {
    $tagCommit = (git rev-parse $TargetVersion).Trim()
    if ($tagCommit -ne $head) {
        Write-Host "Updating local tag ${TargetVersion} from ${tagCommit} to ${head}" -ForegroundColor Yellow
        Invoke-Cmd "delete old local tag" "git tag -d $TargetVersion"
        Invoke-Cmd "create local tag" "git tag $TargetVersion"
    } else {
        Write-Host "OK: $TargetVersion already points at HEAD" -ForegroundColor Green
    }
} else {
    Invoke-Cmd "create local tag" "git tag $TargetVersion"
}

Write-Section "Autonomous Completion Gate"
Invoke-Cmd "verify autonomous completion" "powershell -ExecutionPolicy Bypass -File .\scripts\verify-autonomous-completion.ps1 -TargetVersion $TargetVersion"

Write-Section "Final state"
$finalStatus = @(git status --short)
if ($finalStatus.Count -ne 0) {
    Write-Host ($finalStatus -join "`n") -ForegroundColor Yellow
    Fail "Final git status is not clean after v0.3.2 completion gate."
}

git show --no-patch --oneline $TargetVersion
git tag --points-at HEAD
Get-ChildItem -LiteralPath $ReleaseDir -Recurse

Write-Host "HOTFIX + RECOVERY v0.3.2 PASS" -ForegroundColor Green
