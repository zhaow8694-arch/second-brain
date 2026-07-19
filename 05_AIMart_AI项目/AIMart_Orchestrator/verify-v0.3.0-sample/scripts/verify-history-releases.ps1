param([string]$TargetVersion = "")
$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir
Write-Host "[Autonomous Completion Gate] verify-history-releases TargetVersion=$TargetVersion"
$Frozen = @("releases/v0.1.0", "releases/v0.1.1", "releases/v0.2.1", "releases/v0.2.2")
foreach ($Path in $Frozen) {
  if (-not (Test-Path $Path)) { throw "Missing frozen historical release folder: $Path" }
}
$Dirty = @()
$Dirty += git diff --name-only -- $Frozen
$Dirty += git diff --cached --name-only -- $Frozen
if ($Dirty.Count -gt 0) { throw "Historical releases modified: $($Dirty -join ', ')" }
if ((git tag --list v0.2.2).Trim()) {
  $ChangedSince = @(git diff --name-only v0.2.2 HEAD -- $Frozen)
  if ($ChangedSince.Count -gt 0) { throw "Historical release changes since v0.2.2: $($ChangedSince -join ', ')" }
}
Write-Host "[verify-history-releases] PASS"