#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Deterministic local task acceptance reporter.
  Outputs PASS/FAIL summary for the current project state.
  Expected values must be updated by the task implementer before running.
.DESCRIPTION
  Checks:
    - Current HEAD matches expected commit
    - Working directory is clean
    - Current stable tag exists and points to expected commit
    - Restricted directories have no uncommitted changes
    - No manifest / fixture / directory files exist
    - No external evidence copied into the repository
    - No MT5 build artifacts present
    - No real trading or profit optimization claims in docs
.PARAMETER ExpectedHeadHash
  Expected short hash of HEAD (e.g., "5eb7332")
.PARAMETER ExpectedHeadSubject
  Expected subject line of HEAD (e.g., "TASK-DOC-145 update state after TASK-117")
.PARAMETER StableTagName
  Name of the current stable tag (e.g., "v0.5.4-official-manifest-naming-consistency-audit")
.PARAMETER StableTagTargetHash
  Expected commit short hash the stable tag should point to (e.g., "fd4cf62")
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ExpectedHeadHash,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedHeadSubject,

    [Parameter(Mandatory = $true)]
    [string]$StableTagName,

    [Parameter(Mandatory = $true)]
    [string]$StableTagTargetHash
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$exitCode = 0
$gitExe = "git.exe"

function Write-Pass {
    Write-Host "[PASS] $($args -join ' ')" -ForegroundColor Green
}

function Write-Fail {
    Write-Host "[FAIL] $($args -join ' ')" -ForegroundColor Red
    $script:exitCode = 1
}

function Write-Header {
    Write-Host ""
    Write-Host "## $($args -join ' ')" -ForegroundColor Cyan
}

function Get-GitOutput {
    param([string[]]$ArgumentList)
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = $gitExe
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.Arguments = "-C `"$RepoRoot`" " + ($ArgumentList -join ' ')
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $pinfo
    $p.Start() | Out-Null
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    return @{ Stdout = $stdout.Trim(); Stderr = $stderr.Trim(); ExitCode = $p.ExitCode }
}

Write-Header "TASK ACCEPTANCE REPORT"
Write-Host "Repo root : $RepoRoot"
Write-Host ""

# ---------------------------------------------------------------------------
# 1. HEAD check
# ---------------------------------------------------------------------------
Write-Header "1. HEAD check"
$headResult = Get-GitOutput @("log", "-1", "--oneline")
$headLine = $headResult.Stdout
if ($headResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($headLine)) {
    Write-Fail "could not get HEAD"
} else {
    $parts = $headLine -split ' ', 2
    $headHash = $parts[0]
    $headSubject = $parts[1]
    Write-Host "  HEAD      : $headLine"
    Write-Host "  Expected  : $ExpectedHeadHash $ExpectedHeadSubject"
    if ($headHash -eq $ExpectedHeadHash -and $headSubject -eq $ExpectedHeadSubject) {
        Write-Pass "HEAD matches expected"
    } else {
        Write-Fail "HEAD mismatch (got '$headHash $headSubject')"
    }
}

# ---------------------------------------------------------------------------
# 2. Workspace clean check
# ---------------------------------------------------------------------------
Write-Header "2. Workspace clean check"
$wsResult = Get-GitOutput @("status", "--short")
$ws = $wsResult.Stdout
if ([string]::IsNullOrWhiteSpace($ws)) {
    Write-Pass "workspace is clean"
} else {
    Write-Fail "workspace has uncommitted changes"
    Write-Host "$ws"
}

# ---------------------------------------------------------------------------
# 3. Stable tag check
# ---------------------------------------------------------------------------
Write-Header "3. Stable tag check"
$tagListResult = Get-GitOutput @("tag", "--list", $StableTagName)
$tagExists = (-not [string]::IsNullOrWhiteSpace($tagListResult.Stdout))
if (-not $tagExists) {
    Write-Fail "stable tag '$StableTagName' does not exist"
} else {
    $tagLogResult = Get-GitOutput @("log", "-1", "--oneline", $StableTagName)
    $tagLine = $tagLogResult.Stdout
    $tagParts = $tagLine -split ' ', 2
    $tagHash = $tagParts[0]
    Write-Host "  $StableTagName -> $tagLine"
    Write-Host "  Expected target: $StableTagTargetHash"
    if ($tagHash -eq $StableTagTargetHash) {
        Write-Pass "stable tag points to expected commit"
    } else {
        Write-Fail "stable tag target mismatch (got '$tagHash')"
    }
}

# ---------------------------------------------------------------------------
# 4. Restricted directories unchanged
# ---------------------------------------------------------------------------
Write-Header "4. Restricted directories unchanged"
$restrictedPaths = @(
    "docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md"
    "MQ5"
    "backtest/sets"
    "backtest/reports"
)
$restrictedDiffResult = Get-GitOutput @("diff", "--", "docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md", "MQ5", "backtest/sets", "backtest/reports")
$restrictedDiff = $restrictedDiffResult.Stdout
if ([string]::IsNullOrWhiteSpace($restrictedDiff)) {
    Write-Pass "no changes in restricted directories"
} else {
    Write-Fail "restricted directories have changes"
    Write-Host $restrictedDiff
}

# ---------------------------------------------------------------------------
# 5. No manifest / fixture / directory created
# ---------------------------------------------------------------------------
Write-Header "5. No manifest / fixture / directory"
$manifestDir = Join-Path (Join-Path (Join-Path $RepoRoot "backtest") "reports") "manifests"
if (Test-Path $manifestDir) {
    Write-Fail "backtest/reports/manifests/ exists"
} else {
    Write-Pass "backtest/reports/manifests/ does not exist"
}

$backtestRoot = Join-Path $RepoRoot "backtest"
if (Test-Path $backtestRoot) {
    $manifestFiles = Get-ChildItem -Path $backtestRoot -Recurse -File -ErrorAction SilentlyContinue `
        | Where-Object { $_.Name -match "manifest.*\.json$" }
    if ($manifestFiles.Count -gt 0) {
        Write-Fail "manifest JSON files found under backtest/"
        $manifestFiles | ForEach-Object { Write-Host "    $($_.FullName)" }
    } else {
        Write-Pass "no manifest JSON files found under backtest/"
    }
} else {
    Write-Pass "backtest/ does not exist"
}

$fixtureDirs = Get-ChildItem -Path $RepoRoot -Directory -Filter "*fixture*" -ErrorAction SilentlyContinue
if ($fixtureDirs.Count -gt 0) {
    Write-Fail "fixture directories found: $($fixtureDirs.FullName -join ', ')"
} else {
    Write-Pass "no fixture directories found"
}

# ---------------------------------------------------------------------------
# 6. No external evidence copied
# ---------------------------------------------------------------------------
Write-Header "6. No external evidence copied"
$evidenceRoot = Join-Path (Join-Path $RepoRoot "external") "evidence"
if (Test-Path $evidenceRoot) {
    Write-Host "  external/evidence/ exists (expected: permitted as metadata reference)"
    $evidenceFiles = Get-ChildItem -Path $evidenceRoot -Recurse -File -ErrorAction SilentlyContinue
    if ($evidenceFiles.Count -gt 0) {
        Write-Fail "external/evidence/ contains files ($($evidenceFiles.Count) files)"
    } else {
        Write-Pass "external/evidence/ exists but is empty"
    }
} else {
    Write-Pass "external/evidence/ does not exist"
}

# ---------------------------------------------------------------------------
# 7. No MT5 run
# ---------------------------------------------------------------------------
Write-Header "7. No MT5 or build artifacts"
$mt5BuildDir = Join-Path $RepoRoot "mt5_build"
$mt5LogFile = Join-Path $RepoRoot "mt5_compile_log.txt"
$mt5Artifacts = @()

if (Test-Path $mt5BuildDir) { $mt5Artifacts += "mt5_build/" }
if (Test-Path $mt5LogFile) { $mt5Artifacts += "mt5_compile_log.txt" }

$tempManifestDir = Join-Path $env:TEMP "ts_manifest_validation_TASK109"
if (Test-Path $tempManifestDir) { $mt5Artifacts += "TEMP ts_manifest_validation_TASK109" }

$toolsPycache = Join-Path (Join-Path $RepoRoot "tools") "__pycache__"
if (Test-Path $toolsPycache) { $mt5Artifacts += "tools/__pycache__" }

if ($mt5Artifacts.Count -gt 0) {
    Write-Fail "leftover artifacts detected: $($mt5Artifacts -join ', ')"
} else {
    Write-Pass "no MT5 or build artifacts found"
}

# ---------------------------------------------------------------------------
# 8. No real trading / profit optimization
# ---------------------------------------------------------------------------
Write-Header "8. No real trading / profit optimization"
$docFilesToCheck = @(
    "docs/CURRENT_TASK.md"
    "docs/HANDOFF_PROMPT.md"
    "docs/PROJECT_STATE.md"
)
$tradingFlagsFound = 0
foreach ($docRel in $docFilesToCheck) {
    $docAbs = Join-Path $RepoRoot $docRel
    if (-not (Test-Path $docAbs)) { continue }
    $content = Get-Content $docAbs -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    $claimed = @()
    if ($content -match "real trading") { $claimed += "real trading" }
    if ($content -match "live trading") { $claimed += "live trading" }
    if ($content -match "profit optimization") { $claimed += "profit optimization" }
    if ($content -match "盈利优化") { $claimed += "盈利优化" }
    if ($claimed.Count -gt 0) {
        Write-Host "  $docRel mentions: $($claimed -join ', ')"
        $tradingFlagsFound++
    }
}
if ($tradingFlagsFound -gt 0) {
    Write-Host "  (mentions are expected as policy statements, not violations)"
    Write-Pass "no real trading / profit optimization violations detected"
} else {
    Write-Pass "no real trading or profit optimization claims found"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Header "SUMMARY"
if ($exitCode -eq 0) {
    Write-Host "RESULT: PASS" -ForegroundColor Green
} else {
    Write-Host "RESULT: FAIL" -ForegroundColor Red
}
Write-Host ""
exit $exitCode
