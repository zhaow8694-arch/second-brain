# v8.67 Next Stage Small Batch Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the repaired v8.67 MT5 execution chain into a controlled, backed-up, small-batch validation process starting with B dateshift 16 cases.

**Architecture:** Keep the current MT5 portable terminal as the execution engine, but make `HCSJ/scripts/run_v867_next_stage.ps1` the only entrypoint for v8.67 batches. Every batch creates immutable run folders, copies `.set` into MT5 `Profiles\Tester` before launch, archives 5 required artifacts plus report images/logs, writes matrix rows, and appends `WORK_LOG.md`.

**Tech Stack:** Windows PowerShell 5.1, MetaTrader 5 portable terminal at `D:\MT5测试\MetaTrader 5`, MT5 HTML reports, CSV matrices, Markdown stage reports.

---

## Current Facts

- MT5 chain is fixed for precheck after syncing `.set` files into `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester`.
- B precheck run `20260619_1547_precheck` passed both windows.
- A precheck run `20260619_1548_precheck` passed both windows.
- B old window is weak: `2012-2019 profit=55826.12, PF=1.17, trades=250`.
- B recent window is strong and reproduced anchor: `2020-2026 profit=556052.56, PF=2.27, trades=203`.
- Next work should not blindly expand to C/D. First prove whether B is boundary-sensitive.

## Dateshift Definition

Use inward boundary trimming so the test never depends on future data:

```text
shift00 = original window
shift01 = FromDate + 1 day, ToDate - 1 day
shift02 = FromDate + 2 days, ToDate - 2 days
shift03 = FromDate + 3 days, ToDate - 3 days
shift04 = FromDate + 4 days, ToDate - 4 days
shift05 = FromDate + 5 days, ToDate - 5 days
shift06 = FromDate + 6 days, ToDate - 6 days
shift07 = FromDate + 7 days, ToDate - 7 days
```

Base windows:

```text
2012-2019 = 2012.01.01 to 2019.12.31
2020-2026 = 2020.01.01 to 2026.06.30
```

Example:

```text
v866_B_dateshift_2012-2019_shift03_r01_case0007
FromDate=2012.01.04
ToDate=2019.12.28
```

## File Structure

- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`
  - Add `dateshift` module support.
  - Add `-Scenarios` and `-NoRun` parameters.
  - Add batch manifest and log archiving.

- No change expected: `E:\CODEXMACD\HCSJ\archive_backtest_data.ps1`
  - Already fixed for empty report candidate arrays.

- Create by execution: `E:\CODEXMACD\HCSJ\v8.67_validation_runs\<run_id>\`
  - Generated `.ini` configs.

- Create by execution: `E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\<run_id>\`
  - Generated `.set` copies.

- Create by execution: `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\`
  - Per-case 5-piece archive, PNG report assets, logs, manifests.

- Create by execution: `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\`
  - `matrix.csv`
  - `dateshift_stage_report.md`

## Naming Rules

Case id format:

```text
v866_<Object>_<Module>_<Window>_<Scenario>_r01_case<NNNN>
```

B dateshift order:

```text
case0001 = B 2012-2019 shift00
case0002 = B 2020-2026 shift00
case0003 = B 2012-2019 shift01
case0004 = B 2020-2026 shift01
case0005 = B 2012-2019 shift02
case0006 = B 2020-2026 shift02
case0007 = B 2012-2019 shift03
case0008 = B 2020-2026 shift03
case0009 = B 2012-2019 shift04
case0010 = B 2020-2026 shift04
case0011 = B 2012-2019 shift05
case0012 = B 2020-2026 shift05
case0013 = B 2012-2019 shift06
case0014 = B 2020-2026 shift06
case0015 = B 2012-2019 shift07
case0016 = B 2020-2026 shift07
```

## Backup Rules

Before execution:

```text
Create: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\_batch_manifest.csv
Create: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\_source_snapshot\
Copy: HCSJ\scripts\run_v867_next_stage.ps1
Copy: base .set files for selected objects
Copy: generated .ini files after NoRun generation
Record: SHA256, size, last write time for every copied source
```

During execution:

```text
Copy each generated .set into:
D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester\<case_id>.set

Keep original MT5 report files in:
D:\MT5测试\MetaTrader 5\SingleEAReports\

Copy report .htm and matching .png files into:
E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\<window>\<case_id>\
```

After execution:

```text
Copy terminal log:
D:\MT5测试\MetaTrader 5\logs\<yyyymmdd>.log

Copy tester log:
D:\MT5测试\MetaTrader 5\Tester\logs\<yyyymmdd>.log

Destination:
E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\_logs\
```

Do not delete `SingleEAReports` during this stage. Deletion makes debugging harder.

## Result Gates

Execution gate:

```text
PASS = .set + .ini + .htm + _metrics.csv + _notes.md all exist, status=completed
FAIL = any required artifact missing, timeout, no report, no trades, parser failure
```

B 2020-2026 dateshift gate:

```text
Green:
median profit_retention >= 0.85
minimum profit_retention >= 0.70
median PF >= 2.00
minimum trade_count >= 180

Yellow:
median profit_retention >= 0.75
minimum profit_retention >= 0.60
median PF >= 1.70
minimum trade_count >= 160

Red:
any profit_retention < 0.60
any PF < 1.40
any trade_count < 150
any net profit <= 0
```

B 2012-2019 dateshift gate:

```text
Green:
all shifts net profit > 0
median PF >= 1.15
minimum trade_count >= 220
max_dd_pct <= 65

Yellow:
all shifts net profit > 0
median PF >= 1.05
minimum trade_count >= 200
max_dd_pct <= 75

Red:
any shift net profit <= 0
any PF < 1.00
any trade_count < 180
any max_dd_pct > 75
```

Kill switch:

```text
Stop batch expansion if:
2 or more MT5/no-report failures occur in one run_id
B 2020-2026 has 2 or more shifts with profit_retention < 0.60
B 2012-2019 has 2 or more shifts with PF < 1.00
any run produces zero trades
terminal64.exe remains running after timeout cleanup
```

## Task 1: Extend Runner Parameters

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Add module choices**

Change the module parameter to:

```powershell
[ValidateSet('precheck','dateshift','wf20','wf12','spread','slippage','quarter','month_core','month_full')]
[string]$Module = 'precheck',
```

- [ ] **Step 2: Add scenario and dry-run controls**

Add parameters:

```powershell
[string[]]$Scenarios = @(),
[switch]$NoRun,
```

- [ ] **Step 3: Define default scenarios by module**

Add function:

```powershell
function Get-DefaultScenarios {
    param([string]$Module)
    if($Module -eq 'dateshift') {
        return @('shift00','shift01','shift02','shift03','shift04','shift05','shift06','shift07')
    }
    if($Module -eq 'precheck') {
        return @('shift00')
    }
    throw "Module not implemented in runner yet: $Module"
}
```

- [ ] **Step 4: Verify syntax**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& 'E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1' -Module precheck -Objects B -Windows 2020-2026 -NoRun"
```

Expected:

```text
No MT5 terminal starts.
The script creates configs, sets, matrix header, and source snapshot for a unique run_id.
```

## Task 2: Implement Dateshift Date Calculation

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Add date parser**

Add function:

```powershell
function Convert-Mt5Date {
    param([string]$Date)
    return [datetime]::ParseExact($Date, 'yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
}
```

- [ ] **Step 2: Add MT5 date formatter**

Add function:

```powershell
function Format-Mt5Date {
    param([datetime]$Date)
    return $Date.ToString('yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
}
```

- [ ] **Step 3: Add scenario offset**

Add function:

```powershell
function Get-ScenarioOffsetDays {
    param([string]$Scenario)
    if($Scenario -match '^shift([0-7][0-9]?)$') {
        $n = [int]$Matches[1]
        if($n -ge 0 -and $n -le 7) { return $n }
    }
    throw "Unsupported dateshift scenario: $Scenario"
}
```

- [ ] **Step 4: Apply inward trimming**

Change the date selection inside `Invoke-OneBacktest`:

```powershell
$offsetDays = Get-ScenarioOffsetDays -Scenario $scenario
$fromDate = Format-Mt5Date ((Convert-Mt5Date $dates.From).AddDays($offsetDays))
$toDate = Format-Mt5Date ((Convert-Mt5Date $dates.To).AddDays(-1 * $offsetDays))
Write-TesterConfig -ConfigPath $configFile -Expert $candidate['Expert'] -SetFileName "$id.set" -FromDate $fromDate -ToDate $toDate -ReportName $reportName
```

- [ ] **Step 5: Verify generated dates**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module dateshift -Objects B -Windows both -Scenarios shift03 -NoRun
```

Expected generated `.ini` values:

```text
2012-2019 shift03: FromDate=2012.01.04, ToDate=2019.12.28
2020-2026 shift03: FromDate=2020.01.04, ToDate=2026.06.27
```

## Task 3: Add Batch Manifest and Source Snapshot

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Add SHA256 helper**

Add function:

```powershell
function Get-FileSha256 {
    param([string]$Path)
    if(!(Test-Path -LiteralPath $Path)) { return '' }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}
```

- [ ] **Step 2: Create snapshot directory**

After creating `$archiveRoot`, add:

```powershell
$sourceSnapshotDir = Join-Path $archiveRoot '_source_snapshot'
$logsDir = Join-Path $archiveRoot '_logs'
New-Item -ItemType Directory -Force -Path $sourceSnapshotDir, $logsDir | Out-Null
Copy-Item -LiteralPath (Join-Path $Hcsj 'scripts\run_v867_next_stage.ps1') -Destination (Join-Path $sourceSnapshotDir 'run_v867_next_stage.ps1')
```

- [ ] **Step 3: Write batch manifest**

Create manifest path:

```powershell
$batchManifest = Join-Path $archiveRoot '_batch_manifest.csv'
[System.IO.File]::WriteAllText($batchManifest, "type,path,size,last_write_time,sha256`r`n", [System.Text.UTF8Encoding]::new($false))
```

Append source rows for runner and base `.set` files:

```powershell
foreach($objectCode in $Objects) {
    $path = $candidateMap[$objectCode]['BaseSet']
    $item = Get-Item -LiteralPath $path
    $row = @('base_set',$item.FullName,$item.Length,$item.LastWriteTime.ToString('s'),(Get-FileSha256 $item.FullName))
    [System.IO.File]::AppendAllText($batchManifest, (($row | ForEach-Object { CsvEscape $_ }) -join ',') + "`r`n", [System.Text.UTF8Encoding]::new($false))
}
```

- [ ] **Step 4: Archive MT5 logs after each batch**

At the end of the script, add:

```powershell
$todayLogName = (Get-Date).ToString('yyyyMMdd') + '.log'
$terminalLog = Join-Path (Join-Path $Mt5 'logs') $todayLogName
$testerLog = Join-Path (Join-Path $Mt5 'Tester\logs') $todayLogName
if(Test-Path -LiteralPath $terminalLog) { Copy-Item -LiteralPath $terminalLog -Destination (Join-Path $logsDir "terminal_$todayLogName") -Force }
if(Test-Path -LiteralPath $testerLog) { Copy-Item -LiteralPath $testerLog -Destination (Join-Path $logsDir "tester_$todayLogName") -Force }
```

- [ ] **Step 5: Verify backup artifacts**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module dateshift -Objects B -Windows both -Scenarios shift00 -NoRun
```

Expected:

```text
_batch_manifest.csv exists
_source_snapshot\run_v867_next_stage.ps1 exists
No existing artifact is overwritten
```

## Task 4: Execute B Dateshift 16 Cases

**Files:**
- Generated: `E:\CODEXMACD\HCSJ\v8.67_validation_runs\<run_id>\`
- Generated: `E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\<run_id>\`
- Generated: `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\`
- Generated: `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\matrix.csv`
- Modify: `E:\CODEXMACD\WORK_LOG.md`

- [ ] **Step 1: Choose run_id**

Use:

```text
20260619_1600_dateshift_B
```

If that folder exists, use:

```text
20260619_1600_dateshift_B_01
```

- [ ] **Step 2: Execute**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module dateshift -RunId "20260619_1600_dateshift_B" -Objects B -Windows both -Scenarios shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07 -ForceCloseTerminal -TimeoutSeconds 240
```

Expected:

```text
16 completed rows
RunId=20260619_1600_dateshift_B
Matrix=E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1600_dateshift_B\matrix.csv
```

- [ ] **Step 3: Verify 5-piece archive**

Run:

```powershell
$run='20260619_1600_dateshift_B'
$root="E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\$run"
Get-ChildItem -Path $root -Directory -Recurse |
  Where-Object { $_.Name -like 'v866_*_case*' } |
  ForEach-Object {
    $id=$_.Name
    $expected=@("$id.set","$id.ini","$id.htm","$id`_metrics.csv","$id`_notes.md")
    $missing=@()
    foreach($name in $expected){ if(-not (Test-Path -LiteralPath (Join-Path $_.FullName $name))){ $missing += $name } }
    [pscustomobject]@{Case=$id; Missing=($missing -join ';'); Status=if($missing.Count -eq 0){'OK'}else{'MISSING'}}
  }
```

Expected:

```text
16 rows with Status=OK
```

- [ ] **Step 4: Verify no terminal residue**

Run:

```powershell
Get-Process -Name terminal64 -ErrorAction SilentlyContinue
```

Expected:

```text
No process returned
```

## Task 5: Generate Dateshift Stage Report

**Files:**
- Create: `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\dateshift_stage_report.md`
- Read: `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\matrix.csv`
- Modify: `E:\CODEXMACD\WORK_LOG.md`

- [ ] **Step 1: Calculate window baselines**

Use shift00 rows:

```text
2012-2019 baseline profit = shift00 profit
2020-2026 baseline profit = shift00 profit
```

- [ ] **Step 2: Add matrix-derived fields in report**

Report each case with:

```text
case_id
window
scenario
profit
profit_retention
pf
max_dd_pct
trade_count
gate_color
reason
artifact_html
```

- [ ] **Step 3: Use this report structure**

```markdown
# v8.67 Dateshift Stage Report

run_id: <run_id>
module: dateshift
objects: B
windows: 2012-2019 / 2020-2026
scenarios: shift00-shift07

## Executive Decision

Decision: Continue / Hold / Stop
Reason: <specific reason based on gates>

## 2020-2026 Recent Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate |
|---|---:|---:|---:|---:|---:|---|

## 2012-2019 Old Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate |
|---|---:|---:|---:|---:|---:|---|

## Artifact Index

| case_id | html | metrics | notes |
|---|---|---|---|

## Next Action

<one concrete next action>
```

- [ ] **Step 4: Append WORK_LOG**

Append:

```text
## yyyy-MM-dd HH:mm:ss +08:00 - v8.67 dateshift B stage report
类型：报告生成
run_id: <run_id>
模块：dateshift
回测数量：16
成功：<n>
失败：<n>
初筛结论：通过 / 边缘 / 淘汰
下一步：扩 A/C/D 或进入 wf20 或中止复盘
输出路径：
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\matrix.csv
- report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\dateshift_stage_report.md
```

## Task 6: Decision Tree After B Dateshift

**Files:**
- Read: `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\dateshift_stage_report.md`
- Modify: `E:\CODEXMACD\WORK_LOG.md`

- [ ] **Step 1: If Green**

Run A/C/D dateshift only after B is green:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module dateshift -RunId "20260619_1630_dateshift_ACD" -Objects A,C,D -Windows both -Scenarios shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07 -ForceCloseTerminal -TimeoutSeconds 240
```

Purpose:

```text
Check whether B's robustness is genuinely better than A/C/D, not merely profitable in the anchor window.
```

- [ ] **Step 2: If Yellow**

Do not expand to A/C/D. Run wf20 next:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module wf20 -RunId "20260619_1630_wf20_B" -Objects B -Windows 2012-2019 -ForceCloseTerminal -TimeoutSeconds 240
```

Purpose:

```text
Test whether parameters selected on recent structure degrade too much on the old validation window.
```

- [ ] **Step 3: If Red**

Stop expansion. Write a failure review:

```text
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\dateshift_failure_review.md
```

Required contents:

```text
Worst 3 cases by profit_retention
Worst 3 cases by PF
Worst 3 cases by max_dd_pct
Any zero-trade or missing-report case
Whether failure is old-window-only or both-window
Recommendation: keep B as recent-window candidate only, or revisit parameter selection
```

## Execution Purpose Summary

Precheck purpose:

```text
Prove MT5 automation and artifact chain are working.
```

Dateshift purpose:

```text
Detect whether B depends on exact date boundaries.
```

wf20 purpose:

```text
Validate recent-window selected behavior on older market structure.
```

wf12 purpose:

```text
Validate old-window selected behavior on recent market structure.
```

Spread/slippage purpose:

```text
Measure live-cost fragility after cross-window behavior is acceptable.
```

Quarter/month purpose:

```text
Find concentration risk and long dry spells after main robustness gates pass.
```

## Self-Review

- Spec coverage: This plan covers execution purpose, small steps, backup rules, naming, gates, result templates, and next decision branches.
- Placeholder scan: No `TBD`, no undefined shift semantics, no open-ended "handle later" steps.
- Type consistency: Uses existing runner path, existing artifact roots, existing object codes A/B/C/D, existing MT5 paths, and current B/A precheck facts.
