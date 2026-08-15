# v8.67 B/C WF20 WF12 Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and execute a controlled B/C `wf20` and `wf12` validation batch so v8.66 B remains the mainline unless C proves it can keep both recent-window edge and old-window stability.

**Architecture:** This plan extends the existing v8.67 runner instead of creating a second execution system. `wf20` and `wf12` are treated as fixed-candidate walk-forward validation batches first, not as true optimizer re-selection; this avoids pretending we have retrained parameters when we only have current B/C candidate sets. Each object/window run produces the same five-piece archive, matrix row, logs, and comparison report format already used by `dateshift`.

**Tech Stack:** PowerShell 5.1, MetaTrader 5 Strategy Tester, existing `run_v867_next_stage.ps1`, existing MT5 `.set` files, CSV/Markdown reports under `E:\CODEXMACD\HCSJ`.

---

## 1. My current judgment

B is still the mainline. C is the challenger.

Reason:
- B has the better balanced profile from the completed dateshift run: recent-window retention is strong, drawdown is lower than C, and old-window behavior is acceptable.
- C has the best 2020-2026 profit, but it is the aggressive candidate and has higher old-window drawdown than B.
- C should not replace B after one dateshift success. It must pass `wf20` and `wf12` with the same artifact discipline before it can enter spread/slippage and monthly slicing as a serious replacement candidate.

Important distinction:
- This plan performs fixed-candidate walk-forward validation.
- This plan does not perform true optimizer re-selection.
- If we later need true walk-forward optimization, that should become a separate plan with explicit parameter mining, optimization ranges, selection rules, and out-of-sample validation.

---

## 2. Definitions

### `wf20`

Meaning:
- Treat the current B/C candidate sets as recent-era candidates.
- Validate them on the older market window.

Window:
- Validation window: `2012-2019`
- `FromDate=2012.01.01`
- `ToDate=2019.12.31`

Purpose:
- Answer whether B/C, which are attractive in the 2020-2026 environment, still survive the 2012-2019 market regime.
- This is the guardrail against overfitting to recent market behavior.

### `wf12`

Meaning:
- Reverse fixed-candidate validation.
- Score the same B/C candidate sets on the recent market window while treating older-window survival as the reference discipline.

Window:
- Validation window: `2020-2026`
- `FromDate=2020.01.01`
- `ToDate=2026.06.30`

Purpose:
- Confirm that old-window survivability does not come at the cost of losing the recent-window edge.
- This is especially important for C because C's recent-window profit is high but its old-window drawdown is also higher.

---

## 3. Candidate objects

### B: mainline

Expert:
- `SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5`

Base set:
- `v866_2020-2026_control_robust_case0010.set`

Label:
- `v8.66_robust_main_case0010`

Role:
- Mainline candidate.
- Default survivor unless C proves materially better without unacceptable old-window degradation.

Known dateshift baseline:
- `2012-2019`: profit `55826.12`, PF `1.17`, min trades around `249`, max DD% around `57.36`
- `2020-2026`: profit `556052.56`, median retention around `0.9022`, PF around `2.26`, min trades around `200`, max DD% around `26.07`

### C: challenger

Expert:
- `SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5`

Base set:
- `v866_2020-2026_control_aggressive_case0005.set`

Label:
- `v8.66_aggressive_case0005`

Role:
- Aggressive challenger.
- Must beat B on recent strength and remain close enough on old-window stability.

Known dateshift baseline:
- `2012-2019`: profit `57221.99`, PF `1.15`, min trades around `249`, max DD% around `60.76`
- `2020-2026`: profit `716968.27`, median retention around `0.8959`, PF around `2.28`, min trades around `200`, max DD% around `28.31`

---

## 4. Batch naming

Run B and C separately to avoid the previous PowerShell array argument trap where `-Objects A C D` only executed the first object.

### Batch 1: `wf20_B`

RunId:
- `20260619_1710_wf20_B`

Parameters:
- `Module=wf20`
- `Objects=B`
- `Windows=2012-2019`
- `Scenarios=validate`
- `TimeoutSeconds=240`
- `ForceCloseTerminal=true`

Case ID:
- `v866_B_wf20_2012-2019_validate_r01_case0001`

### Batch 2: `wf20_C`

RunId:
- `20260619_1715_wf20_C`

Parameters:
- `Module=wf20`
- `Objects=C`
- `Windows=2012-2019`
- `Scenarios=validate`
- `TimeoutSeconds=240`
- `ForceCloseTerminal=true`

Case ID:
- `v866_C_wf20_2012-2019_validate_r01_case0001`

### Batch 3: `wf12_B`

RunId:
- `20260619_1720_wf12_B`

Parameters:
- `Module=wf12`
- `Objects=B`
- `Windows=2020-2026`
- `Scenarios=validate`
- `TimeoutSeconds=240`
- `ForceCloseTerminal=true`

Case ID:
- `v866_B_wf12_2020-2026_validate_r01_case0001`

### Batch 4: `wf12_C`

RunId:
- `20260619_1725_wf12_C`

Parameters:
- `Module=wf12`
- `Objects=C`
- `Windows=2020-2026`
- `Scenarios=validate`
- `TimeoutSeconds=240`
- `ForceCloseTerminal=true`

Case ID:
- `v866_C_wf12_2020-2026_validate_r01_case0001`

---

## 5. Folder conventions

All output must stay under the existing v8.67 validation tree.

Generated INI:
- `E:\CODEXMACD\HCSJ\v8.67_validation_runs\<run_id>\config\<window>\<case_id>.ini`

Generated SET:
- `E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\<run_id>\<window>\<case_id>.set`

MT5 Tester SET mirror:
- `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester\<case_id>.set`

Archive case folder:
- `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\<window>\<case_id>\`

Matrix:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\matrix.csv`

Per-run stage report:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\wf_stage_report.md`

Combined B/C comparison:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\wf20_wf12_BC_comparison_20260619.md`

Work log:
- `E:\CODEXMACD\WORK_LOG.md`

---

## 6. Required archive package per case

Every case folder must contain these five required files:

- `<case_id>.set`
- `<case_id>.ini`
- `<case_id>.htm`
- `<case_id>_metrics.csv`
- `<case_id>_notes.md`

Every case should also retain available PNG assets copied from MT5 report output.

Required per-run backup:
- `_batch_manifest.csv`
- `_source_snapshot\run_v867_next_stage.ps1`
- `_logs\terminal_YYYYMMDD.log`
- `_logs\tester_YYYYMMDD.log`

The run is not acceptable if the `.htm` report or `_metrics.csv` file is missing.

---

## 7. Pass, green, and elimination thresholds

### Global elimination thresholds

Eliminate the case immediately if any condition is true:

- MT5 does not generate a report.
- The report exists but cannot be parsed into `_metrics.csv`.
- Net profit is `<= 0`.
- Profit factor is `< 1.00`.
- Trades are `< 180`.
- Max DD% is `> 75`.
- Required five-piece archive is incomplete.

### `wf20` old-window validation thresholds

Pass:
- Net profit `> 0`
- Profit factor `>= 1.10`
- Trades `>= 220`
- Max DD% `<= 70`

Green:
- Profit factor `>= 1.15`
- Trades `>= 240`
- Max DD% `<= 65`
- Net profit is not worse than the object's dateshift old-window baseline by more than `15%`

Object comparison:
- C may beat B on old-window profit, but C is not promoted if C's max DD% is more than `10` percentage points worse than B.
- B keeps mainline status if B passes and C's only advantage is higher recent-window profit.

### `wf12` recent-window validation thresholds

Pass:
- Net profit `> 0`
- Profit retention versus the object's recent dateshift baseline `>= 0.80`
- Profit factor `>= 2.00`
- Trades `>= 190`
- Max DD% `<= 35`

Green:
- Profit retention versus the object's recent dateshift baseline `>= 0.90`
- Profit factor `>= 2.20`
- Trades `>= 200`
- Max DD% `<= 30`

Object comparison:
- C can become the preferred challenger only if it passes `wf20` and `wf12`.
- C can challenge B for mainline only if C's `wf12` profit advantage remains material and C's `wf20` drawdown is not materially worse than B.
- Material recent-window profit advantage means C recent-window net profit is at least `15%` higher than B.
- Material old-window drawdown penalty means C old-window max DD% is more than `10` percentage points worse than B.

### Final decision table

`B pass + C fail`:
- Keep B as mainline.
- Stop C from spread/slippage.

`B pass + C pass, C old-window weaker`:
- Keep B as mainline.
- Let C continue only as challenger.

`B pass + C pass, C recent much stronger and old-window not materially worse`:
- Keep B as current mainline.
- Promote C to equal-depth next validation: spread, slippage, quarter, and month-core.

`B fail + C pass`:
- Do not immediately replace B.
- Mark B as degraded.
- Run one confirmation batch for C before changing mainline.

`B fail + C fail`:
- Stop B/C branch.
- Return to A/D or parameter mining.

---

## 8. Runner implementation plan

### Task 1: Enable `wf20` and `wf12` modules in the runner

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Confirm module gate**

Find the current guard that rejects modules other than `precheck` and `dateshift`.

Expected current behavior:

```powershell
if ($Module -notin @('precheck','dateshift')) {
    throw "Module not implemented in runner yet: $Module"
}
```

- [ ] **Step 2: Replace the gate**

Use this module list:

```powershell
$implementedModules = @('precheck', 'dateshift', 'wf20', 'wf12')
if ($Module -notin $implementedModules) {
    throw "Module not implemented in runner yet: $Module"
}
```

- [ ] **Step 3: Preserve PowerShell 5.1 Chinese path compatibility**

After editing the runner, convert the file to UTF-8 BOM:

```powershell
$path = 'E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1'
$text = Get-Content -LiteralPath $path -Raw
$utf8Bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($path, $text, $utf8Bom)
```

Expected result:
- Windows PowerShell 5.1 reads `D:\MT5测试\...` paths correctly.

### Task 2: Add scenario defaults for `wf20` and `wf12`

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Update scenario default logic**

Where the runner chooses default scenarios, add:

```powershell
switch ($Module) {
    'precheck'  { @('base') }
    'dateshift' { @('shift00', 'shift01', 'shift02', 'shift03', 'shift04', 'shift05', 'shift06', 'shift07') }
    'wf20'      { @('validate') }
    'wf12'      { @('validate') }
}
```

- [ ] **Step 2: Keep comma splitting**

Keep the existing scenario expansion that splits comma strings:

```powershell
$expandedScenarios = @(
    $Scenarios |
        ForEach-Object { $_ -split ',' } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { $_.Trim() }
)
```

Expected result:
- `-Scenarios validate` and `-Scenarios validate,extra` are both parsed safely.

### Task 3: Add module date range resolver

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Add a date range helper**

Add this helper near the existing date/window helpers:

```powershell
function Resolve-ValidationDateRange {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Module,

        [Parameter(Mandatory = $true)]
        [string]$Window,

        [Parameter(Mandatory = $true)]
        [string]$Scenario
    )

    if ($Module -eq 'wf20') {
        return @{
            Window = '2012-2019'
            FromDate = '2012.01.01'
            ToDate = '2019.12.31'
            Scenario = 'validate'
        }
    }

    if ($Module -eq 'wf12') {
        return @{
            Window = '2020-2026'
            FromDate = '2020.01.01'
            ToDate = '2026.06.30'
            Scenario = 'validate'
        }
    }

    return $null
}
```

- [ ] **Step 2: Use helper only for `wf20` and `wf12`**

In the case-building loop, before dateshift offset logic, add:

```powershell
$wfRange = Resolve-ValidationDateRange -Module $Module -Window $window -Scenario $scenario
if ($null -ne $wfRange) {
    $effectiveWindow = $wfRange.Window
    $fromDate = $wfRange.FromDate
    $toDate = $wfRange.ToDate
    $effectiveScenario = $wfRange.Scenario
} else {
    $effectiveWindow = $window
    $effectiveScenario = $scenario
}
```

Expected result:
- `wf20` cannot accidentally run on `2020-2026`.
- `wf12` cannot accidentally run on `2012-2019`.

### Task 4: Generate WF case IDs

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Add WF naming branch**

Where the runner creates the case ID, add a branch for `wf20` and `wf12`:

```powershell
if ($Module -in @('wf20', 'wf12')) {
    $caseId = 'v866_{0}_{1}_{2}_{3}_r01_case{4:d4}' -f $objectKey, $Module, $effectiveWindow, $effectiveScenario, $caseNumber
}
```

Expected case IDs:

```text
v866_B_wf20_2012-2019_validate_r01_case0001
v866_C_wf20_2012-2019_validate_r01_case0001
v866_B_wf12_2020-2026_validate_r01_case0001
v866_C_wf12_2020-2026_validate_r01_case0001
```

- [ ] **Step 2: Keep existing precheck and dateshift IDs unchanged**

Do not rename old `precheck` or `dateshift` cases.

Expected result:
- Existing archived dateshift evidence remains comparable.

### Task 5: Add WF report generation

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`

- [ ] **Step 1: Add report function**

Add a function that reads the per-run `matrix.csv` and writes:

```text
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\wf_stage_report.md
```

Required report sections:

```markdown
# WF Stage Report

## Run

## Cases

## Threshold Result

## Decision

## Archive Checklist
```

- [ ] **Step 2: Add threshold labels**

Use these labels in the report:

```text
PASS
GREEN
FAIL_ELIMINATED
FAIL_ARCHIVE_INCOMPLETE
```

- [ ] **Step 3: Decision text**

Use this exact decision language:

```text
Continue: object passed this WF module.
Continue as challenger only: object passed but is not eligible to replace B yet.
Stop: object failed a required WF threshold.
Review manually: metrics are parsed but comparison baseline is missing.
```

Expected result:
- Each of the four runs has a human-readable stage report next to its matrix.

### Task 6: Add combined B/C comparison script block

**Files:**
- Modify: `E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1`
- Modify: `E:\CODEXMACD\WORK_LOG.md`

- [ ] **Step 1: Add a comparison mode or standalone report helper**

The report should combine these matrix files:

```text
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1710_wf20_B\matrix.csv
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1715_wf20_C\matrix.csv
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1720_wf12_B\matrix.csv
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1725_wf12_C\matrix.csv
```

Output:

```text
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\wf20_wf12_BC_comparison_20260619.md
```

- [ ] **Step 2: Comparison columns**

The combined report table must include:

```text
object,module,window,profit,pf,trades,max_dd_pct,retention_vs_dateshift_baseline,status,decision
```

- [ ] **Step 3: Work log append**

Append this template to `E:\CODEXMACD\WORK_LOG.md`:

```markdown
## 2026-06-19 v8.67 B/C WF20 WF12

- Runs:
  - `20260619_1710_wf20_B`
  - `20260619_1715_wf20_C`
  - `20260619_1720_wf12_B`
  - `20260619_1725_wf12_C`
- Report: `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\wf20_wf12_BC_comparison_20260619.md`
- Decision:
  - B mainline status:
  - C challenger status:
  - Next batch:
```

Expected result:
- A future session can continue from the work log without reverse-engineering the archive.

---

## 9. Execution commands

Run these only after the runner supports `wf20` and `wf12`.

### Command 1: B `wf20`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module wf20 -RunId "20260619_1710_wf20_B" -Objects B -Windows 2012-2019 -Scenarios validate -ForceCloseTerminal -TimeoutSeconds 240
```

Expected artifacts:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1710_wf20_B\matrix.csv`
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1710_wf20_B\wf_stage_report.md`
- `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1710_wf20_B\2012-2019\v866_B_wf20_2012-2019_validate_r01_case0001\`

### Command 2: C `wf20`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module wf20 -RunId "20260619_1715_wf20_C" -Objects C -Windows 2012-2019 -Scenarios validate -ForceCloseTerminal -TimeoutSeconds 240
```

Expected artifacts:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1715_wf20_C\matrix.csv`
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1715_wf20_C\wf_stage_report.md`
- `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1715_wf20_C\2012-2019\v866_C_wf20_2012-2019_validate_r01_case0001\`

### Command 3: B `wf12`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module wf12 -RunId "20260619_1720_wf12_B" -Objects B -Windows 2020-2026 -Scenarios validate -ForceCloseTerminal -TimeoutSeconds 240
```

Expected artifacts:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1720_wf12_B\matrix.csv`
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1720_wf12_B\wf_stage_report.md`
- `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1720_wf12_B\2020-2026\v866_B_wf12_2020-2026_validate_r01_case0001\`

### Command 4: C `wf12`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1" -Module wf12 -RunId "20260619_1725_wf12_C" -Objects C -Windows 2020-2026 -Scenarios validate -ForceCloseTerminal -TimeoutSeconds 240
```

Expected artifacts:
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1725_wf12_C\matrix.csv`
- `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1725_wf12_C\wf_stage_report.md`
- `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1725_wf12_C\2020-2026\v866_C_wf12_2020-2026_validate_r01_case0001\`

---

## 10. Execution order

- [ ] **Step 1: Modify runner for `wf20` and `wf12`**

Complete Tasks 1-5.

- [ ] **Step 2: Run B `wf20`**

Run Command 1.

- [ ] **Step 3: Inspect B `wf20` artifacts**

Required:
- `matrix.csv` exists.
- `wf_stage_report.md` exists.
- Case archive contains the five required files.
- MT5 terminal is closed after run.

- [ ] **Step 4: Run C `wf20`**

Run Command 2.

- [ ] **Step 5: Inspect C `wf20` artifacts**

Use the same checklist as Step 3.

- [ ] **Step 6: Stop if either `wf20` is eliminated**

If B fails and C fails, stop the B/C branch.

If C fails but B passes, keep B and do not run C through deeper spread/slippage.

- [ ] **Step 7: Run B `wf12`**

Run Command 3.

- [ ] **Step 8: Inspect B `wf12` artifacts**

Use the same checklist as Step 3.

- [ ] **Step 9: Run C `wf12`**

Run Command 4.

- [ ] **Step 10: Inspect C `wf12` artifacts**

Use the same checklist as Step 3.

- [ ] **Step 11: Generate combined comparison**

Create:

```text
E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\wf20_wf12_BC_comparison_20260619.md
```

- [ ] **Step 12: Append work log**

Append the result summary to:

```text
E:\CODEXMACD\WORK_LOG.md
```

---

## 11. Result recording template

Use this template inside `wf20_wf12_BC_comparison_20260619.md`:

```markdown
# v8.67 B/C WF20 WF12 Comparison - 2026-06-19

## Source runs

| RunId | Object | Module | Window | Status |
|---|---:|---:|---:|---:|
| 20260619_1710_wf20_B | B | wf20 | 2012-2019 |  |
| 20260619_1715_wf20_C | C | wf20 | 2012-2019 |  |
| 20260619_1720_wf12_B | B | wf12 | 2020-2026 |  |
| 20260619_1725_wf12_C | C | wf12 | 2020-2026 |  |

## Metrics

| Object | Module | Window | Profit | PF | Trades | Max DD% | Retention | Status | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B | wf20 | 2012-2019 |  |  |  |  |  |  |  |
| C | wf20 | 2012-2019 |  |  |  |  |  |  |  |
| B | wf12 | 2020-2026 |  |  |  |  |  |  |  |
| C | wf12 | 2020-2026 |  |  |  |  |  |  |  |

## Decision

- B mainline:
- C challenger:
- Next execution:

## Notes

- `wf20` is old-window validation.
- `wf12` is recent-window reverse validation.
- This report is fixed-candidate validation, not optimizer re-selection.
```

Use this template inside each case `_notes.md`:

```markdown
# Case Notes

- RunId:
- CaseId:
- Object:
- Module:
- Window:
- Scenario:
- Expert:
- Base set:
- Generated set:
- Generated ini:
- Report:
- Metrics:
- Archive status:
- Threshold status:
- Decision:
- Operator note:
```

---

## 12. Backup discipline

Before running each batch:
- Keep the existing source base `.set` untouched.
- Generate a new `.set` under the run-specific `HCSJ\set\v8.67_validation_runs\<run_id>\...` folder.
- Copy the generated `.set` into MT5 Tester profile before launch.

During each batch:
- Close conflicting MT5 terminal before running when `-ForceCloseTerminal` is used.
- Let only one MT5 test run at a time.
- Wait for report generation before archiving.

After each batch:
- Archive `.set`, `.ini`, `.htm`, `_metrics.csv`, `_notes.md`.
- Copy terminal/tester logs into `_logs`.
- Copy runner into `_source_snapshot`.
- Write or update `_batch_manifest.csv`.
- Append final human-readable status only after files exist.

Do not overwrite old run folders.

---

## 13. Acceptance criteria

The plan is complete only when all conditions are true:

- `wf20_B` has one complete archived case.
- `wf20_C` has one complete archived case.
- `wf12_B` has one complete archived case.
- `wf12_C` has one complete archived case.
- Each run has `matrix.csv`.
- Each run has `wf_stage_report.md`.
- Combined comparison report exists.
- `WORK_LOG.md` contains the final B/C WF decision.
- No final recommendation promotes C above B unless C passes both WF directions and does not carry a material old-window drawdown penalty.

---

## 14. Recommended next action after this plan

Execute the runner modification first, then run only `wf20_B`.

Reason:
- It is the smallest safe proof that the new module wiring works.
- It avoids burning time on four MT5 runs if `wf20/wf12` module routing still has a date or set-copy issue.
- Once `wf20_B` produces a valid five-piece archive, the other three runs are mechanical.
