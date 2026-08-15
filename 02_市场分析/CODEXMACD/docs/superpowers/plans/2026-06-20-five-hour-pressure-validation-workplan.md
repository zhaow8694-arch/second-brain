# Five-Hour Pressure Validation Workplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute a five-hour validation block that prioritizes smoke testing, date-shift robustness, bidirectional walk-forward checks, spread feasibility, and stage reporting for the v8.66 robust main candidate.

**Architecture:** Do not modify EA source code. Reuse the established MT5 batch-backtest workflow, archive every `.set`, `.ini`, `.htm`, `_metrics.csv`, and `_notes.md`, and update `WORK_LOG.md` after each module. Stop batch execution if smoke testing or tester口径 validation fails.

**Tech Stack:** MetaTrader 5 Strategy Tester, MQL5 EX5 artifacts, PowerShell batch scripts, `.set` files, HTML reports, CSV/Markdown matrices, `E:\CODEXMACD\WORK_LOG.md`.

---

## 1. Relationship to the larger plan

This five-hour workplan is a controlled execution slice of:

```text
E:\CODEXMACD\docs\superpowers\plans\2026-06-20-v866-pressure-walkforward-validation.md
```

It does not attempt to complete the entire 720/1008-run validation campaign.

It focuses on the highest-value first-stage checks:

1. Smoke test
2. Date-shift test
3. Reverse walk-forward: train/select on `2020-2026`, validate on `2012-2019`
4. Forward walk-forward: train/select on `2012-2019`, validate on `2020-2026`
5. Fixed-spread feasibility check
6. Stage summary and handoff update

---

## 2. Current main candidate

Primary candidate:

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set
```

Known control result:

```text
2020.01.01-2026.06.30
Net profit: 556,052.56
PF: 2.27
Trades: 203
```

Reference anchor:

```text
grok8.6 old anchor net profit: 557,505.36
```

---

## 3. Test objects

Use these four objects for the first-stage validation block:

| Object ID | Version | Set file | Purpose |
|---|---|---|---|
| A | v8.6 | `E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_robust_main_case0502.set` | Old-version robust/high-return reference |
| B | v8.66 | `E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set` | Current main candidate |
| C | v8.66 | `E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_aggressive_case0005.set` | High-profit observation candidate |
| D | v8.66 | `E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_conservative_case0401.set` | Low-drawdown observation candidate |

---

## 4. Time-boxed schedule

| Time block | Module | Expected action |
|---|---|---|
| 0-20 min | Preparation + smoke test | Create directories/matrix, run one B control smoke test |
| 20-90 min | Date-shift test | Run 64 date-shift cases |
| 90-160 min | Reverse walk-forward | Run/select `2020-2026` then validate `2012-2019` |
| 160-230 min | Forward walk-forward | Run/select `2012-2019` then validate `2020-2026` |
| 230-270 min | Fixed-spread feasibility | Run minimal technical feasibility checks only |
| 270-290 min | Stage summary | Generate `pressure_walkforward_stage1_summary.md` |
| 290-300 min | Handoff cleanup | Update `WORK_LOG.md` and `HANDOFF_NEXT_WINDOW.md` |

Do not start a new large batch during the final 10 minutes.

---

## 5. Output paths

Create and use these paths:

```text
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\stage1_five_hour
E:\CODEXMACD\HCSJ\set\pressure_walkforward\stage1_five_hour
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward
E:\CODEXMACD\HCSJ\logs\pressure_walkforward
```

Required output files:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_feasibility_summary.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
```

---

## 6. Global execution rules

- Do not modify EA source code during this five-hour block.
- Do not overwrite any historical `.set`, report, matrix, or log.
- Every run gets a unique run id.
- Every run must archive `.set`, `.ini`, `.htm`, `_metrics.csv`, and `_notes.md`.
- Failed, timeout, no-report, no-trade, and losing runs must be recorded.
- If the smoke test fails, stop batch execution and document the blocker.
- If fixed spread cannot be verified, record a blocker instead of pretending spread stress is valid.
- Every module completion must append to `E:\CODEXMACD\WORK_LOG.md`.

---

## 7. Task 1: Preparation and smoke test, 0-20 min

**Files:**

- Create or update: `E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv`
- Create output folders under `stage1_five_hour`
- Modify: `E:\CODEXMACD\WORK_LOG.md`

Steps:

- [ ] Create required output directories.
- [ ] Create the master matrix if it does not exist.
- [ ] Confirm the EX5 files exist in the MT5 Experts folder.
- [ ] Copy object B `.set` into MT5 tester profile using a unique smoke-test name.
- [ ] Run object B on `2020.01.01-2026.06.30`.
- [ ] Parse report metrics.
- [ ] Compare net profit to known value `556,052.56`.
- [ ] Save all run artifacts.
- [ ] Append a `WORK_LOG.md` entry.

Expected run count:

```text
1
```

Success condition:

```text
Report generated, net profit/PF/drawdown/trades parsed, result close to known object B control result.
```

Stop condition:

```text
No report, blank metrics, wrong EA, wrong .set, or large unexplained drift from known value.
```

---

## 8. Task 2: Date-shift test, 20-90 min

Purpose:

```text
Detect whether results depend on exact start/end dates.
```

Objects:

```text
A, B, C, D
```

Base windows:

```text
2012.01.01-2019.12.31
2020.01.01-2026.06.30
```

Shift cases:

| Case | Start date | End date |
|---|---|---|
| 0000 | original | original |
| 0001 | start + 1 month | original |
| 0002 | start + 3 months | original |
| 0003 | original | end - 1 month |
| 0004 | original | end - 3 months |
| 0005 | start + 1 month | end - 1 month |
| 0006 | start + 3 months | end - 3 months |
| 0007 | start + 6 months | end - 6 months |

Expected run count:

```text
4 objects × 2 windows × 8 shifts = 64
```

Summary file:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv
```

Required summary fields:

```text
object_id,version,set_role,base_window,run_count,completed_count,net_profit_avg,net_profit_min,net_profit_max,net_profit_std,pf_avg,pf_min,max_equity_dd_pct_max,total_trades_min,total_trades_max,sensitivity_rating,decision,notes
```

Decision rules:

```text
Low sensitivity: no severe loss, PF mostly >= 1.5, trade count stable, drawdown not much worse.
Medium sensitivity: one weak shift, no collapse.
High sensitivity: collapse, heavy loss, sharp trade-count drop, or drawdown explosion.
```

After completion:

- [ ] Write `date_shift_summary.csv`.
- [ ] Append module result to `WORK_LOG.md`.

---

## 9. Task 3: Reverse walk-forward, 90-160 min

Purpose:

```text
Check whether parameters selected from 2020-2026 fail on 2012-2019.
```

Training/selecting window:

```text
2020.01.01-2026.06.30
```

Validation window:

```text
2012.01.01-2019.12.31
```

Expected run count:

```text
48
```

Practical five-hour version:

- Use the already identified candidate families from the previous robust search.
- Do not run a massive new optimizer.
- Run a bounded candidate grid around known robust/aggressive/conservative regions.
- Select by robustness score, not by net profit only.

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv
```

Required conclusion:

```text
fixed_year_risk = low / medium / high
```

Decision rules:

```text
Excellent in 2020-2026 and stable in 2012-2019 = lower fixed-year risk.
Excellent in 2020-2026 but weak/loss-making in 2012-2019 = high fixed-year risk.
Aggressive high-profit but poor validation = do not promote aggressive.
Robust moderate-profit and stable validation = keep robust as main candidate.
```

After completion:

- [ ] Write walk-forward CSV.
- [ ] Append result to `WORK_LOG.md`.

---

## 10. Task 4: Forward walk-forward, 160-230 min

Purpose:

```text
Check whether parameters selected from 2012-2019 generalize to 2020-2026.
```

Training/selecting window:

```text
2012.01.01-2019.12.31
```

Validation window:

```text
2020.01.01-2026.06.30
```

Expected run count:

```text
48
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv
```

Decision rules:

```text
Early-window candidate also strong in late window = strong generalization.
Early-window candidate fails late window = early overfit.
Late-window quality only appears in late-optimized settings = fixed-year risk remains.
```

After completion:

- [ ] Write walk-forward CSV.
- [ ] Append result to `WORK_LOG.md`.

---

## 11. Task 5: Fixed-spread feasibility check, 230-270 min

Purpose:

```text
Determine whether MT5 tester config can reliably apply fixed spread in this environment.
```

Do not run full 40-run spread stress yet.

Minimal checks:

- [ ] Run object B with current/default spread on `2020.01.01-2026.06.30`.
- [ ] Run object B with intended enlarged fixed spread setting on the same window.
- [ ] Inspect report/config to confirm whether spread changed.
- [ ] If confirmed, record that full spread stress can be executed later.
- [ ] If not confirmed, record blocker and do not fabricate spread sensitivity conclusions.

Expected run count:

```text
2
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_feasibility_summary.csv
```

Decision values:

```text
spread_feasibility = confirmed / blocked / inconclusive
```

---

## 12. Task 6: Stage summary, 270-290 min

Create:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
```

The summary must answer:

```text
Did smoke test pass?
Does date shifting expose boundary sensitivity?
Does reverse walk-forward indicate fixed-year overfitting?
Does forward walk-forward support generalization?
Can fixed-spread testing be trusted in this MT5 environment?
Is v8.66 robust case0010 still the main candidate?
Can v8.66 aggressive case0005 be promoted, or should it remain observation only?
What should the next execution block do?
```

After completion:

- [ ] Append summary path and main conclusions to `WORK_LOG.md`.

---

## 13. Task 7: Handoff cleanup, 290-300 min

Do not launch new runs during this block.

Update:

```text
E:\CODEXMACD\WORK_LOG.md
E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
```

The handoff update must include:

```text
Completed modules
Incomplete modules
Important result paths
Main candidate status
Aggressive candidate status
Known blockers
Recommended next step
```

---

## 14. Expected total workload

Expected first-stage run count:

| Module | Runs |
|---|---:|
| Smoke test | 1 |
| Date shift | 64 |
| Reverse walk-forward | 48 |
| Forward walk-forward | 48 |
| Spread feasibility | 2 |
| Total | 163 |

This is the intended five-hour workload.

---

## 15. Things not to do in this five-hour block

- Do not run full monthly breakdown.
- Do not run full quarterly breakdown.
- Do not run full 40-case spread stress unless spread feasibility is confirmed and time remains after reporting.
- Do not create a slippage-test EA.
- Do not modify production EA source code.
- Do not promote aggressive parameters based only on profit.
- Do not continue batch execution if smoke test fails.

---

## 16. Completion definition

This five-hour block is complete when:

```text
Smoke test completed or blocker recorded.
Date-shift test completed or blocker recorded.
Reverse walk-forward completed or blocker recorded.
Forward walk-forward completed or blocker recorded.
Spread feasibility completed or blocker recorded.
Stage summary report created.
WORK_LOG.md updated.
HANDOFF_NEXT_WINDOW.md updated.
No historical files overwritten.
```