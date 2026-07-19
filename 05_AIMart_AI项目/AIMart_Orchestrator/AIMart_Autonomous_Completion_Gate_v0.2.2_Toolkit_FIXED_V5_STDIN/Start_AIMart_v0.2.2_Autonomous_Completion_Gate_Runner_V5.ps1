param(
    [string]$ProjectRoot = "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack",
    [string]$TargetVersion = "v0.2.2",
    [switch]$AllowDirtyStart
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "AIMart Completion Gate Runner V5 - $TargetVersion"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptFile = Join-Path $ScriptRoot "codex\V0.2.2_AUTONOMOUS_COMPLETION_GATE_PROMPT_EN.md"
if (-not (Test-Path -LiteralPath $PromptFile)) { throw "Prompt file missing: $PromptFile" }
if (-not (Test-Path -LiteralPath $ProjectRoot)) { throw "Project root missing: $ProjectRoot" }

Set-Location -LiteralPath $ProjectRoot

$CodexCommand = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $CodexCommand) { $CodexCommand = Get-Command codex -ErrorAction SilentlyContinue }
if (-not $CodexCommand) { throw "Codex executable not found in PATH." }
$CodexExe = $CodexCommand.Source

$Branch = (git branch --show-current).Trim()
$DirtyBefore = (git status --short | Measure-Object).Count

Write-Host "== AIMart Autonomous Completion Gate Runner V5 ==" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host "Target       : $TargetVersion"
Write-Host "Branch       : $Branch"
Write-Host "Codex exe    : $CodexExe"
Write-Host "Dirty files  : $DirtyBefore"
Write-Host ""

if ($DirtyBefore -gt 0 -and -not $AllowDirtyStart) {
    Write-Host "The working tree is not clean. This runner will stop to avoid mixing versions." -ForegroundColor Red
    Write-Host "Commit/stash changes first, or rerun with -AllowDirtyStart if intentional." -ForegroundColor Yellow
    exit 20
}

$LogDir = Join-Path $ProjectRoot "codex_runs\autonomous_v0_2_2_completion_gate_v5"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReleaseDir = Join-Path $ProjectRoot "releases\$TargetVersion"

function Write-InvocationScript {
    param(
        [string]$AttemptName,
        [string[]]$CodexArgList,
        [string]$InvokeScript,
        [string]$StdoutLog,
        [string]$StderrLog
    )
    $EncodedPrompt = $PromptFile.Replace("'", "''")
    $EncodedCodex = $CodexExe.Replace("'", "''")
    $EncodedProject = $ProjectRoot.Replace("'", "''")
    $ArgLiteral = ($CodexArgList | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ", "
    $body = @"
`$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath '$EncodedProject'
`$PromptText = Get-Content -LiteralPath '$EncodedPrompt' -Raw
`$CodexExe = '$EncodedCodex'
`$CodexArgList = @($ArgLiteral)
Write-Output '== Codex invocation attempt: $AttemptName =='
Write-Output ('Executable: ' + `$CodexExe)
Write-Output ('Arguments : ' + (`$CodexArgList -join ' '))
`$PromptText | & `$CodexExe @CodexArgList 1> '$($StdoutLog.Replace("'", "''"))' 2> '$($StderrLog.Replace("'", "''"))'
`$Exit = `$LASTEXITCODE
Write-Output ('Codex exit code: ' + `$Exit)
exit `$Exit
"@
    Set-Content -LiteralPath $InvokeScript -Value $body -Encoding UTF8
}

function Get-FileTailText {
    param([string]$Path, [int]$Tail = 20)
    if (Test-Path -LiteralPath $Path) {
        try { return (Get-Content -LiteralPath $Path -Tail $Tail -ErrorAction Stop | Out-String) }
        catch { return "Unable to read log: $Path`n$($_.Exception.Message)" }
    }
    return ""
}

function Show-Status {
    param(
        [string]$AttemptName,
        [System.Diagnostics.Process]$Process,
        [string]$StdoutLog,
        [string]$StderrLog,
        [datetime]$Started
    )
    Clear-Host
    $Elapsed = New-TimeSpan -Start $Started -End (Get-Date)
    $Dirty = (git status --short | Measure-Object).Count
    $CodexProcCount = (Get-Process codex -ErrorAction SilentlyContinue | Measure-Object).Count + (Get-Process Codex -ErrorAction SilentlyContinue | Measure-Object).Count
    $LogTime = "not created"
    $LogSize = 0
    if (Test-Path -LiteralPath $StdoutLog) { $f = Get-Item -LiteralPath $StdoutLog; $LogTime = $f.LastWriteTime.ToString('HH:mm:ss'); $LogSize += $f.Length }
    if (Test-Path -LiteralPath $StderrLog) { $f = Get-Item -LiteralPath $StderrLog; $LogSize += $f.Length }
    $ReleaseStatus = if (Test-Path -LiteralPath $ReleaseDir) { "exists" } else { "not created yet" }
    $GateStatus = "RUNNING_OR_UNKNOWN"
    $Known = Join-Path $ProjectRoot "V0.2.2_KNOWN_ISSUES.md"
    if (Test-Path -LiteralPath (Join-Path $ReleaseDir "RELEASE_MANIFEST.txt")) { $GateStatus = "ARTIFACTS_PRESENT_PENDING_FINAL_CHECK" }
    if (Test-Path -LiteralPath $Known) {
        $KnownText = Get-Content -LiteralPath $Known -Raw
        if ($KnownText -match "PASS") { $GateStatus = "PASS_OR_REVIEW_REPORT" }
        if ($KnownText -match "FAIL|BLOCKER|P0|P1") { $GateStatus = "KNOWN_ISSUES_PRESENT" }
    }
    Write-Host "AIMart Autonomous Completion Gate Runner V5" -ForegroundColor Cyan
    Write-Host "Target project : $ProjectRoot"
    Write-Host "Target version : $TargetVersion"
    Write-Host "Attempt        : $AttemptName"
    Write-Host "Started        : $($Started.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed        : $($Elapsed.ToString())"
    Write-Host "Process state  : $($(if ($Process.HasExited) { 'Finished' } else { 'Running' }))"
    Write-Host "Exit code      : $($(if ($Process.HasExited) { $Process.ExitCode } else { 'running' }))"
    Write-Host "Git branch     : $Branch"
    Write-Host "Dirty files    : $Dirty"
    Write-Host "Codex procs    : $CodexProcCount"
    Write-Host "Log updated    : $LogTime"
    Write-Host "Log size       : $LogSize bytes"
    Write-Host "CompletionGate : $GateStatus"
    Write-Host ""
    Write-Host "== Release Output ==" -ForegroundColor Cyan
    if (Test-Path -LiteralPath $ReleaseDir) { Get-ChildItem -LiteralPath $ReleaseDir -Recurse | Select-Object Mode,LastWriteTime,Length,Name | Format-Table | Out-String | Write-Host }
    else { Write-Host "$ReleaseDir not created yet." -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "== Latest STDOUT Tail ==" -ForegroundColor Cyan
    Write-Host (Get-FileTailText -Path $StdoutLog -Tail 18)
    Write-Host "== Latest STDERR Tail ==" -ForegroundColor Cyan
    Write-Host (Get-FileTailText -Path $StderrLog -Tail 18)
    Write-Host ""
    Write-Host "Do not close this window while running. Ctrl+C stops only this runner." -ForegroundColor Yellow
}

$Attempts = @(
    @{ Name = "global-config-exec-stdin"; Args = @("--cd", $ProjectRoot, "-c", 'approval_policy="never"', "-c", 'sandbox_mode="workspace-write"', "exec", "-") },
    @{ Name = "exec-options-stdin"; Args = @("exec", "--cd", $ProjectRoot, "-c", 'approval_policy="never"', "-c", 'sandbox_mode="workspace-write"', "-") }
)

$FinalExit = 999
$FinalAttempt = "none"
$FinalStdout = $null
$FinalStderr = $null

foreach ($Attempt in $Attempts) {
    $AttemptName = $Attempt.Name
    $StdoutLog = Join-Path $LogDir "codex_v022_v5_${Timestamp}_${AttemptName}.stdout.log"
    $StderrLog = Join-Path $LogDir "codex_v022_v5_${Timestamp}_${AttemptName}.stderr.log"
    $InvokeScript = Join-Path $LogDir "invoke_codex_v5_${Timestamp}_${AttemptName}.ps1"
    Write-InvocationScript -AttemptName $AttemptName -CodexArgList $Attempt.Args -InvokeScript $InvokeScript -StdoutLog $StdoutLog -StderrLog $StderrLog

    Write-Host "== Starting attempt: $AttemptName ==" -ForegroundColor Cyan
    Write-Host "Invocation script: $InvokeScript"
    $Started = Get-Date
    $Proc = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $InvokeScript) -WindowStyle Hidden -PassThru

    while (-not $Proc.HasExited) {
        Show-Status -AttemptName $AttemptName -Process $Proc -StdoutLog $StdoutLog -StderrLog $StderrLog -Started $Started
        Start-Sleep -Seconds 5
        try { $Proc.Refresh() } catch {}
    }
    Show-Status -AttemptName $AttemptName -Process $Proc -StdoutLog $StdoutLog -StderrLog $StderrLog -Started $Started
    $FinalExit = $Proc.ExitCode
    $FinalAttempt = $AttemptName
    $FinalStdout = $StdoutLog
    $FinalStderr = $StderrLog

    if ($FinalExit -eq 0) { break }

    $ErrText = Get-FileTailText -Path $StderrLog -Tail 40
    if ($ErrText -match "unexpected argument|unrecognized option|unknown option") {
        Write-Host "Attempt failed due to CLI argument compatibility. Trying next fallback..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        continue
    }
    else {
        Write-Host "Attempt failed with non-compatibility error. Not trying fallback." -ForegroundColor Red
        break
    }
}

$CombinedLog = Join-Path $LogDir "codex_v022_v5_${Timestamp}_${FinalAttempt}.combined.log"
@("--- STDOUT ---", (Get-FileTailText -Path $FinalStdout -Tail 100000), "--- STDERR ---", (Get-FileTailText -Path $FinalStderr -Tail 100000)) | Set-Content -LiteralPath $CombinedLog -Encoding UTF8

Write-Host ""
Write-Host "== Post-run summary ==" -ForegroundColor Cyan
git status --short --branch
Write-Host "Tags:"; git tag --list
Write-Host "Release:"; if (Test-Path -LiteralPath $ReleaseDir) { Get-ChildItem -LiteralPath $ReleaseDir -Recurse } else { Write-Host "releases\$TargetVersion not found." -ForegroundColor Yellow }
Write-Host "Last attempt: $FinalAttempt"
Write-Host "Exit code   : $FinalExit"
Write-Host "Combined log: $CombinedLog"

if ($FinalExit -ne 0) { exit $FinalExit }
exit 0
