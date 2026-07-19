param([string]$TargetVersion = "")
$ErrorActionPreference = "Continue"
$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir
if (-not $TargetVersion) {
  $Pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
  $TargetVersion = "v$($Pkg.version)"
}
if (-not $TargetVersion.StartsWith("v")) { $TargetVersion = "v$TargetVersion" }
$ReportDir = Join-Path $RootDir "codex_runs"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$ReportPath = Join-Path $ReportDir "verify-autonomous-completion-$TargetVersion.md"
$Results = @()
function Add-Result([string]$Gate, [string]$Status, [string]$Details) {
  $script:Results += [pscustomobject]@{ Gate = $Gate; Status = $Status; Details = $Details }
}
function Invoke-NativeGate([string]$Gate, [string[]]$Command) {
  Write-Host "[Autonomous Completion Gate] $Gate"
  & $Command[0] $Command[1..($Command.Count - 1)]
  $Code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
  if ($Code -eq 0) { Add-Result $Gate "PASS" "exit 0" } else { Add-Result $Gate "FAIL" "exit $Code" }
}
function Invoke-ScriptGate([string]$Gate, [string]$ScriptName) {
  try {
    & (Join-Path $PSScriptRoot $ScriptName) -TargetVersion $TargetVersion
    Add-Result $Gate "PASS" "ok"
  } catch {
    Add-Result $Gate "FAIL" $_.Exception.Message
  }
}
Invoke-NativeGate "pnpm test" @("pnpm", "test")
Invoke-NativeGate "pnpm lint" @("pnpm", "lint")
Invoke-NativeGate "pnpm build" @("pnpm", "build")
Invoke-ScriptGate "verify-release" "verify-release.ps1"
Invoke-ScriptGate "verify-source-zip" "verify-source-zip.ps1"
Invoke-ScriptGate "verify-sample-pack" "verify-sample-pack.ps1"
Invoke-ScriptGate "verify-history-releases" "verify-history-releases.ps1"
foreach ($Path in @("IMPLEMENTATION_REPORT.md", "RELEASE_NOTES.md", "FINAL_DELIVERY_CHECK.md", "V0.3.0_IMPLEMENTATION_REPORT.md", "V0.3.0_RELEASE_NOTES.md", "V0.3.0_FINAL_DELIVERY_CHECK.md", "V0.3.0_KNOWN_ISSUES.md")) {
  if (Test-Path $Path) { Add-Result "final delivery document $Path" "PASS" "exists" } else { Add-Result "final delivery document $Path" "FAIL" "missing" }
}
$GitStatus = git status --short --branch
Add-Result "git status" "PASS" ($GitStatus -join "; ")
try {
  $Head = (git rev-parse HEAD).Trim()
  $TagCommit = (git rev-parse $TargetVersion).Trim()
  if ($Head -eq $TagCommit) { Add-Result "target version tag" "PASS" "$TargetVersion -> $Head" } else { Add-Result "target version tag" "FAIL" "$TargetVersion -> $TagCommit, HEAD -> $Head" }
} catch {
  Add-Result "target version tag" "FAIL" $_.Exception.Message
}
$Final = if (($Results | Where-Object { $_.Status -eq "FAIL" }).Count -eq 0) { "PASS" } else { "FAIL" }
@("# Autonomous Completion Gate Report", "", "TargetVersion: $TargetVersion", "", "| Gate | Status | Details |", "|---|---|---|") + ($Results | ForEach-Object { "| $($_.Gate) | $($_.Status) | $($_.Details -replace '\|','/') |" }) + @("", "Git status: $($GitStatus -join '; ')", "", "Final result: $Final") | Set-Content -Encoding UTF8 $ReportPath
Write-Host "[Autonomous Completion Gate] $Final report=$ReportPath"
if ($Final -ne "PASS") { throw "Autonomous Completion Gate FAIL. See $ReportPath" }