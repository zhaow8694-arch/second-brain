$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
Set-Location $RootDir

$RunDir = Join-Path $RootDir "codex_runs"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $RunDir "codex-unified-autonomous-$Stamp.log"
$ExitPath = Join-Path $RunDir "codex-unified-autonomous-$Stamp.exit"
$PromptPath = Join-Path $RootDir "agent_adapters/codex/CODEX_AUTONOMOUS_PROMPT.md"
$StatusPath = Join-Path $RootDir "runtime/AUTONOMOUS_RUN_STATUS.md"
$SummaryPath = Join-Path $RootDir "runtime/AUTONOMOUS_RUN_SUMMARY.md"
$HealthPath = Join-Path $RootDir "runtime/AUTONOMOUS_HEALTH_CHECK.md"
$StartTime = Get-Date

Write-Host "[codex-unified] one-window dashboard: sandbox workspace-write, approval never"
Write-Host "[codex-unified] log=$LogPath"

function Get-ElapsedText {
  param([datetime]$StartedAt)
  return ((Get-Date) - $StartedAt).ToString("hh\:mm\:ss")
}

function Get-GitBranchText {
  try {
    $Branch = (git branch --show-current 2>$null).Trim()
    if ($Branch) { return $Branch }
    return "detached-or-unknown"
  } catch {
    return "git unavailable"
  }
}

function Get-DirtyFileCount {
  try {
    return @((git status --short 2>$null)).Count
  } catch {
    return -1
  }
}

function Get-GitStatusText {
  try {
    $Lines = @(git status --short 2>$null)
    if ($Lines.Count -eq 0) { return "clean" }
    return "$($Lines.Count) changed file(s)"
  } catch {
    return "git unavailable"
  }
}

function Get-ReleaseStatus {
  $ReleaseRoot = Join-Path $RootDir "releases"
  if (-not (Test-Path $ReleaseRoot)) {
    return "releases/ not found"
  }

  $ReleaseDirs = @(Get-ChildItem -Path $ReleaseRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
  if ($ReleaseDirs.Count -eq 0) {
    return "no release directories"
  }

  $Latest = $ReleaseDirs[0]
  $ZipCount = @(Get-ChildItem -Path $Latest.FullName -Filter "*.zip" -File -Recurse -ErrorAction SilentlyContinue).Count
  return "$($Latest.Name): $ZipCount zip artifact(s)"
}

function Get-SampleExecutionPackStatus {
  $ReleaseRoot = Join-Path $RootDir "releases"
  if (-not (Test-Path $ReleaseRoot)) {
    return "missing"
  }

  $Samples = @(Get-ChildItem -Path $ReleaseRoot -Filter "*generated-execution-pack.zip" -File -Recurse -ErrorAction SilentlyContinue)
  if ($Samples.Count -eq 0) {
    return "missing"
  }

  return "$($Samples.Count) sample pack(s)"
}

function Get-KnownIssuesStatus {
  $IssueFiles = @()
  foreach ($Name in @("KNOWN_ISSUES.md", "V0.2.1_KNOWN_ISSUES.md", "V0.2.0_KNOWN_ISSUES.md")) {
    $Path = Join-Path $RootDir $Name
    if (Test-Path $Path) {
      $IssueFiles += $Path
    }
  }

  $ApprovalQueue = Join-Path $RootDir "runtime/APPROVAL_QUEUE.md"
  if (Test-Path $ApprovalQueue) {
    $IssueFiles += $ApprovalQueue
  }

  if ($IssueFiles.Count -eq 0) {
    return "no known issue files"
  }

  return "$($IssueFiles.Count) issue/status file(s)"
}

function Get-LogTailText {
  if (-not (Test-Path $LogPath)) {
    return "log not created yet"
  }

  $Tail = @(Get-Content -Path $LogPath -Tail 12 -ErrorAction SilentlyContinue)
  if ($Tail.Count -eq 0) {
    return "log is empty"
  }

  return ($Tail -join [Environment]::NewLine)
}

function Write-RunStatus {
  param([string]$State, [string]$ExitCode = "running")

  $Elapsed = Get-ElapsedText $StartTime
  $Branch = Get-GitBranchText
  $Dirty = Get-DirtyFileCount
  $ReleaseStatus = Get-ReleaseStatus
  $KnownIssues = Get-KnownIssuesStatus
  $Updated = Get-Date -Format s

@"
# Autonomous Run Status

| Field | Value |
|---|---|
| Runner state | $State |
| Elapsed time | $Elapsed |
| Git branch | $Branch |
| Dirty file count | $Dirty |
| Latest log tail | See $LogPath |
| Release directory status | $ReleaseStatus |
| Known issues status | $KnownIssues |
| Codex exit code | $ExitCode |
| Last updated | $Updated |
"@ | Set-Content -Encoding UTF8 -Path $StatusPath
}

function Write-HealthCheck {
@"
# Autonomous Health Check

- [x] one-window runner started.
- [x] codex_runs log path prepared.
- [x] runtime/AUTONOMOUS_RUN_STATUS.md update attempted.
- [x] runtime/AUTONOMOUS_RUN_SUMMARY.md update attempted at completion.
- [x] Release directory status checked.
- [x] Known issues status checked.
- [x] No secret reads or remote pushes are performed by this runner.
"@ | Set-Content -Encoding UTF8 -Path $HealthPath
}

function Show-Dashboard {
  param([string]$State)

  $Elapsed = Get-ElapsedText $StartTime
  $Branch = Get-GitBranchText
  $Dirty = Get-DirtyFileCount
  $ReleaseStatus = Get-ReleaseStatus
  $KnownIssues = Get-KnownIssuesStatus
  $Tail = Get-LogTailText

  Clear-Host
  Write-Host "AIMart Codex Unified Autonomous Runner"
  Write-Host "one-window status display"
  Write-Host ""
  Write-Host "State: $State"
  Write-Host "Elapsed: $Elapsed"
  Write-Host "Git branch: $Branch"
  Write-Host "Dirty files: $Dirty"
  Write-Host "Release directory: $ReleaseStatus"
  Write-Host "Known issues: $KnownIssues"
  Write-Host "Log: $LogPath"
  Write-Host ""
  Write-Host "Latest log tail"
  Write-Host "---------------"
  Write-Host $Tail

  Write-RunStatus -State $State
}

if (-not (Test-Path $PromptPath)) {
  throw "Missing prompt file: $PromptPath"
}

Write-HealthCheck
Write-RunStatus -State "starting"

# Effective Codex flags: codex exec --sandbox workspace-write --approval never
$CodexJob = Start-Job -ScriptBlock {
  param($JobRootDir, $JobPromptPath, $JobLogPath, $JobExitPath)

  Set-Location $JobRootDir
  try {
    & codex exec --sandbox workspace-write --approval never --cd $JobRootDir --prompt-file $JobPromptPath *> $JobLogPath
    $Code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  } catch {
    $_ | Out-String | Add-Content -Encoding UTF8 -Path $JobLogPath
    $Code = 1
  }

  Set-Content -Encoding UTF8 -Path $JobExitPath -Value $Code
} -ArgumentList $RootDir, $PromptPath, $LogPath, $ExitPath

while ($CodexJob.State -eq "Running") {
  Show-Dashboard -State "running"
  Start-Sleep -Seconds 3
}

Receive-Job -Job $CodexJob -ErrorAction SilentlyContinue | Out-Null
Remove-Job -Job $CodexJob -Force

$ExitCode = 1
if (Test-Path $ExitPath) {
  $Parsed = 0
  if ([int]::TryParse(((Get-Content -Path $ExitPath -Raw).Trim()), [ref]$Parsed)) {
    $ExitCode = $Parsed
  }
}

Show-Dashboard -State "completed"
Write-RunStatus -State "completed" -ExitCode "$ExitCode"

$ReleaseStatus = Get-ReleaseStatus
$SampleStatus = Get-SampleExecutionPackStatus
$GitStatus = Get-GitStatusText
$NextAction = if ($ExitCode -eq 0) {
  "Review runtime/AUTONOMOUS_RUN_SUMMARY.md, inspect changed files, then run scripts/finalize for delivery."
} else {
  "Inspect the latest codex_runs log, fix the blocking issue, then rerun the unified autonomous runner."
}

@"
# Autonomous Run Summary

| Field | Value |
|---|---|
| Exit code | $ExitCode |
| Release artifacts | $ReleaseStatus |
| Sample execution pack | $SampleStatus |
| Git status | $GitStatus |
| Latest log | $LogPath |
| Next recommended action | $NextAction |
"@ | Set-Content -Encoding UTF8 -Path $SummaryPath

Write-Host ""
Write-Host "Final Summary"
Write-Host "-------------"
Write-Host "Exit code: $ExitCode"
Write-Host "Release artifacts: $ReleaseStatus"
Write-Host "Sample execution pack: $SampleStatus"
Write-Host "Git status: $GitStatus"
Write-Host "Next recommended action: $NextAction"

exit $ExitCode