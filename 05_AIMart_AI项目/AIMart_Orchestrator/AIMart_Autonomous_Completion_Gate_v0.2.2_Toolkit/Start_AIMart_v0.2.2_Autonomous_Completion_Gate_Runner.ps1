param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.2.2",
    [string]$TargetBranch = "feature/v0.2.2-autonomous-completion-gate",
    [switch]$AllowDirtyStart
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "AIMart $TargetVersion Autonomous Completion Gate Runner"

function Write-Section($Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Shorten($Text, $Max = 140) {
    if ($null -eq $Text) { return "" }
    $s = [string]$Text
    if ($s.Length -le $Max) { return $s }
    return $s.Substring(0, $Max - 3) + "..."
}

function Get-DirtyCount {
    try {
        $status = git -C $ProjectRoot status --short 2>$null
        if (-not $status) { return 0 }
        return @($status).Count
    } catch { return -1 }
}

function Get-CurrentBranch {
    try { return (git -C $ProjectRoot branch --show-current 2>$null).Trim() } catch { return "unknown" }
}

function Get-LatestProgress {
    $path = Join-Path $ProjectRoot "PROGRESS_LOG.md"
    if (Test-Path $path) {
        return @(Get-Content $path -Tail 8 -Encoding UTF8)
    }
    return @("PROGRESS_LOG.md not found.")
}

function Get-ReleaseStatus {
    $releaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"
    $sourceZip = $null
    $sampleZip = Join-Path $releaseDir "samples\todo-api-generated-execution-pack.zip"
    $sha = Join-Path $releaseDir "SHA256.txt"
    $manifest = Join-Path $releaseDir "RELEASE_MANIFEST.txt"
    if (Test-Path $releaseDir) {
        $sourceZip = Get-ChildItem $releaseDir -Filter "*.zip" -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "*source*" -or $_.Name -like "aimart-orchestrator-$TargetVersion*" } |
            Select-Object -First 1
    }
    return [pscustomobject]@{
        ReleaseDir = $releaseDir
        ReleaseExists = Test-Path $releaseDir
        SourceZipExists = $null -ne $sourceZip
        SampleZipExists = Test-Path $sampleZip
        ShaExists = Test-Path $sha
        ManifestExists = Test-Path $manifest
    }
}

function Get-CompletionGateStatus {
    $known = Join-Path $ProjectRoot "V0.2.2_KNOWN_ISSUES.md"
    $final = Join-Path $ProjectRoot "V0.2.2_FINAL_DELIVERY_CHECK.md"
    $release = Get-ReleaseStatus
    if ($release.ReleaseExists -and $release.SourceZipExists -and $release.SampleZipExists -and $release.ShaExists -and $release.ManifestExists -and (Test-Path $final)) {
        return "READY_FOR_FINAL_GATE_OR_PASS"
    }
    if (Test-Path $known) {
        $txt = Get-Content $known -Raw -Encoding UTF8
        if ($txt -match "FAIL|BLOCKER|missing|failed") { return "ISSUES_RECORDED" }
    }
    return "RUNNING_OR_UNKNOWN"
}

function Show-Dashboard($StartTime, $Process, $CombinedLog, $AttemptName, $ExitCode = $null) {
    Clear-Host
    $elapsed = New-TimeSpan -Start $StartTime -End (Get-Date)
    $branch = Get-CurrentBranch
    $dirty = Get-DirtyCount
    $release = Get-ReleaseStatus
    $gate = Get-CompletionGateStatus
    $running = $false
    try { if ($Process -and -not $Process.HasExited) { $running = $true } } catch {}

    Write-Host "AIMart Autonomous Completion Gate Runner" -ForegroundColor Green
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Attempt        : $AttemptName"
    Write-Host "Started        : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "Job state      : $(if ($running) { 'Running' } else { 'Finished' })"
    Write-Host "Exit code      : $(if ($null -eq $ExitCode) { if ($running) { 'running' } else { 'unknown' } } else { $ExitCode })"
    Write-Host "Git branch     : $branch"
    Write-Host "Dirty files    : $dirty"
    Write-Host "CompletionGate : $gate"

    Write-Section "Release Output"
    if ($release.ReleaseExists) {
        Write-Host "Release dir    : exists"
        Write-Host "Source ZIP     : $($release.SourceZipExists)"
        Write-Host "Sample ZIP     : $($release.SampleZipExists)"
        Write-Host "SHA256.txt     : $($release.ShaExists)"
        Write-Host "Manifest       : $($release.ManifestExists)"
        Get-ChildItem $release.ReleaseDir -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 12 Mode, LastWriteTime, Length, FullName |
            Format-Table -AutoSize
    } else {
        Write-Host "$($release.ReleaseDir) not created yet." -ForegroundColor Yellow
    }

    Write-Section "Recent Progress"
    Get-LatestProgress | ForEach-Object { Write-Host (Shorten $_ 180) }

    Write-Section "Latest Codex Log Tail"
    if (Test-Path $CombinedLog) {
        Get-Content $CombinedLog -Tail 18 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host (Shorten $_ 180) }
    } else {
        Write-Host "Log not created yet."
    }

    Write-Section "Known Issues"
    $known = Join-Path $ProjectRoot "V0.2.2_KNOWN_ISSUES.md"
    if (Test-Path $known) {
        Get-Content $known -Tail 12 -Encoding UTF8 | ForEach-Object { Write-Host (Shorten $_ 180) }
    } else {
        Write-Host "$known not created yet."
    }

    Write-Host ""
    Write-Host "Do not close this window while running. Press Ctrl+C only if you want to stop the autonomous run." -ForegroundColor DarkYellow
}

function Start-CodexAttempt($AttemptName, [string[]]$Arguments, $LogDir) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $stdout = Join-Path $LogDir "codex_v022_${AttemptName}_$timestamp.stdout.log"
    $stderr = Join-Path $LogDir "codex_v022_${AttemptName}_$timestamp.stderr.log"
    $combined = Join-Path $LogDir "codex_v022_${AttemptName}_$timestamp.combined.log"

    Write-Section "Starting Codex attempt: $AttemptName"
    Write-Host "Logs:"
    Write-Host "  stdout : $stdout"
    Write-Host "  stderr : $stderr"
    Write-Host "  combined: $combined"

    $proc = Start-Process -FilePath "codex" -ArgumentList $Arguments -WorkingDirectory $ProjectRoot -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $start = Get-Date

    while (-not $proc.HasExited) {
        if (Test-Path $stdout) { Get-Content $stdout -Tail 120 -ErrorAction SilentlyContinue | Set-Content $combined -Encoding UTF8 }
        if (Test-Path $stderr) { Add-Content $combined "`n--- STDERR ---"; Get-Content $stderr -Tail 80 -ErrorAction SilentlyContinue | Add-Content $combined }
        Show-Dashboard -StartTime $start -Process $proc -CombinedLog $combined -AttemptName $AttemptName
        Start-Sleep -Seconds 5
    }

    if (Test-Path $stdout) { Get-Content $stdout -ErrorAction SilentlyContinue | Set-Content $combined -Encoding UTF8 }
    if (Test-Path $stderr) { Add-Content $combined "`n--- STDERR ---"; Get-Content $stderr -ErrorAction SilentlyContinue | Add-Content $combined }

    Show-Dashboard -StartTime $start -Process $proc -CombinedLog $combined -AttemptName $AttemptName -ExitCode $proc.ExitCode

    return [pscustomobject]@{
        Attempt = $AttemptName
        ExitCode = $proc.ExitCode
        Stdout = $stdout
        Stderr = $stderr
        Combined = $combined
    }
}

Write-Section "Preflight"
if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}
Set-Location -LiteralPath $ProjectRoot

$codexCmd = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codexCmd) {
    throw "codex executable was not found in PATH."
}
Write-Host "Codex executable: $($codexCmd.Source)"

$currentBranch = Get-CurrentBranch
$dirtyBefore = Get-DirtyCount

Write-Host "Current branch: $currentBranch"
Write-Host "Dirty files before start: $dirtyBefore"

if ($dirtyBefore -gt 0 -and -not $AllowDirtyStart) {
    Write-Host ""
    Write-Host "The working tree is not clean. To prevent mixing versions, this runner will stop." -ForegroundColor Red
    Write-Host "Commit or stash existing changes first, or rerun with -AllowDirtyStart only if you intentionally want to continue."
    exit 3
}

if ($currentBranch -ne $TargetBranch) {
    $exists = git branch --list $TargetBranch
    if ($exists) {
        git checkout $TargetBranch
    } else {
        git checkout -b $TargetBranch
    }
}

$RunnerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptSource = Join-Path $RunnerRoot "codex\V0.2.2_AUTONOMOUS_COMPLETION_GATE_PROMPT.md"
if (-not (Test-Path $PromptSource)) {
    throw "Prompt file missing: $PromptSource"
}
$PromptTargetDir = Join-Path $ProjectRoot "codex"
New-Item -ItemType Directory -Force -Path $PromptTargetDir | Out-Null
$PromptTarget = Join-Path $PromptTargetDir "V0.2.2_AUTONOMOUS_COMPLETION_GATE_PROMPT.md"
Copy-Item $PromptSource $PromptTarget -Force

$PromptText = Get-Content $PromptTarget -Raw -Encoding UTF8
$LogDir = Join-Path $ProjectRoot "codex_runs\autonomous_v0_2_2_completion_gate"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$attempts = @(
    [pscustomobject]@{
        Name = "global-flags-before-exec"
        Args = @("--cd", $ProjectRoot, "--sandbox", "workspace-write", "--ask-for-approval", "never", "exec", $PromptText)
    },
    [pscustomobject]@{
        Name = "config-overrides"
        Args = @("--cd", $ProjectRoot, "-c", "approval_policy=never", "-c", "sandbox_mode=workspace-write", "exec", $PromptText)
    },
    [pscustomobject]@{
        Name = "workspace-no-approval-flag"
        Args = @("--cd", $ProjectRoot, "--sandbox", "workspace-write", "exec", $PromptText)
    }
)

$results = @()
foreach ($attempt in $attempts) {
    $result = Start-CodexAttempt -AttemptName $attempt.Name -Arguments $attempt.Args -LogDir $LogDir
    $results += $result
    if ($result.ExitCode -eq 0) {
        break
    }
    $err = ""
    if (Test-Path $result.Stderr) { $err = Get-Content $result.Stderr -Raw -ErrorAction SilentlyContinue }
    if ($err -notmatch "unexpected argument|unrecognized option|unknown option") {
        break
    }
    Write-Host "Attempt failed due to argument compatibility. Trying fallback..." -ForegroundColor Yellow
}

Write-Section "Post-run summary"
git -C $ProjectRoot status --short --branch
Write-Host ""
Write-Host "Tags:"
git -C $ProjectRoot tag --list
Write-Host ""
Write-Host "Release:"
if (Test-Path (Join-Path $ProjectRoot "releases\$TargetVersion")) {
    Get-ChildItem (Join-Path $ProjectRoot "releases\$TargetVersion") -Recurse
} else {
    Write-Host "releases\$TargetVersion not found." -ForegroundColor Yellow
}

$last = $results[-1]
Write-Host ""
Write-Host "Last attempt: $($last.Attempt)"
Write-Host "Exit code   : $($last.ExitCode)"
Write-Host "Combined log: $($last.Combined)"
Write-Host ""
Write-Host "Runner finished. If the completion gate passed, review final git status and release artifacts."
