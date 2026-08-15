# v8.66 Pressure and Walk-Forward Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate whether `v8.66_robust_main_case0010.set` is genuinely robust or partly fitted to fixed years by running date-shift, walk-forward, spread, slippage, and period-breakdown tests before any v8.67 code development.

**Architecture:** Keep EA source unchanged during this validation phase. Use the existing MT5 batch runner style to generate unique `.set`, `.ini`, `.htm`, `_metrics.csv`, and `_notes.md` files for every run. Store every result, including failures, in versioned archive folders and summarize each batch into CSV/Markdown matrices.

**Tech Stack:** MetaTrader 5 Strategy Tester, MQL5 EX5 artifacts, `.set` files, HTML reports, PowerShell batch scripts, CSV/Markdown matrices, `E:\CODEXMACD\WORK_LOG.md`.

---

## 1. Scope

This plan continues the project after the completed v8.6/v8.66 robust parameter search.

Primary question:

```text
Does v8.66 robust main case0010 remain stable outside the 2020-2026 anchor window, or is it partly fitted to fixed years?
```

Secondary questions:

```text
Can v8.66 aggressive case0005 survive pressure tests, or is it only a high-risk/high-return observation set?
Can v8.66 conservative case0401 provide useful risk-control ideas for v8.67?
Should v8.67 development proceed from v8.66 robust main case0010?
```

This plan must not modify EA source code unless a dedicated slippage-test EA is explicitly required and separately approved or recorded.

---

## 2. Required context files

Before executing this plan, read these files:

```text
E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
E:\CODEXMACD\WORK_LOG.md
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_summary.md
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_matrix.csv
E:\CODEXMACD\HCSJ\matrix\robust_parameter_group_scores.csv
E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v86-v866-robust-parameter-search.md
```

Current main candidate:

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set
```

High-return observation candidate:

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_aggressive_case0005.set
```

Conservative observation candidate:

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_conservative_case0401.set
```

v8.6 reference candidates:

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_robust_main_case0502.set
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_aggressive_case0005.set
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_conservative_case0002.set
```

---

## 3. Non-negotiable rules

- Do not overwrite old `.mq5`, `.ex5`, `.set`, `.htm`, `.csv`, `.ini`, or `.md` files.
- Do not select parameters only by net profit.
- Do not run large batches until a single smoke run proves MT5 loaded the EA and `.set` correctly.
- Do not treat `v8.66_aggressive_case0005.set` as the main line unless it survives pressure tests.
- Do not optimize all 77 input settings.
- Do not discard failed, no-trade, timeout, or losing runs.
- Do not change grok8.6 core entry logic during this validation phase.
- Every batch must update `E:\CODEXMACD\WORK_LOG.md`.

---

## 4. Test objects

Use four primary objects.

| Object ID | Version | Set file | Purpose |
|---|---|---|---|
| A | v8.6 | `v8.6_robust_main_case0502.set` | Old-version robust/high-return reference |
| B | v8.66 | `v8.66_robust_main_case0010.set` | Current main candidate |
| C | v8.66 | `v8.66_aggressive_case0005.set` | High-profit observation candidate |
| D | v8.66 | `v8.66_conservative_case0401.set` | Low-drawdown observation candidate |

Optional v8.6 baseline object can be added later if needed, but the first execution package should stay focused on these four.

---

## 5. Fixed tester口径

All valid runs must use the same baseline tester口径 unless the test intentionally changes spread or slippage.

| Field | Value |
|---|---|
| Symbol | `XAUUSD` |
| Period | `H4` |
| Deposit | `20000 USD` |
| Leverage | `1:100` |
| MT5 directory | `D:\MT5测试\MetaTrader 5` |
| Report mode | unique report name, no overwrite |
| Set loading | `ExpertParameters=<relative_set_file_name>` copied to MT5 tester profile |
| Archive root | `E:\CODEXMACD\HCSJ` |

---

## 6. Output directories

Create these folders before executing tests:

```text
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\date_shift
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\walkforward_2012_2019_to_2020_2026
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\walkforward_2020_2026_to_2012_2019
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\spread_stress
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\slippage_stress
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\quarterly_breakdown
E:\CODEXMACD\HCSJ\backtest_archive\pressure_walkforward\monthly_breakdown
E:\CODEXMACD\HCSJ\set\pressure_walkforward
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward
E:\CODEXMACD\HCSJ\logs\pressure_walkforward
```

Create these summary files:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_stress_summary.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\slippage_stress_summary.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\quarterly_breakdown.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\monthly_breakdown.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_final_summary.md
```

---

## 7. Master matrix schema

Use this CSV schema for the master matrix:

```csv
run_id,module,object_id,version,set_role,window,stage,case_id,status,source_file,ex5_file,set_file,config_file,report_file,start_date,end_date,symbol,timeframe,model,spread_mode,spread_level,slippage_level,deposit,leverage,net_profit,profit_retention_pct,profit_factor,max_balance_dd,max_balance_dd_pct,max_equity_dd,max_equity_dd_pct,relative_equity_dd,relative_equity_dd_pct,total_trades,trade_count_retention_pct,win_rate,avg_profit_per_trade,worst_period_flag,sensitivity_rating,decision,notes
```

Every run must append one row.

---

## 8. Run naming convention

Use this format:

```text
<version>_<object_id>_<module>_<window>_round<NN>_case<NNNN>
```

Examples:

```text
v866_B_dateshift_2020-2026_round01_case0003
v866_C_spread_2012-2019_round01_case0014
v86_A_walkfwd_early_to_late_round01_case0008
```

Each run must save:

```text
<run_id>.set
<run_id>.ini
<run_id>.htm
<run_id>_metrics.csv
<run_id>_notes.md
```

---

## 9. Execution order

Execute in this order:

1. Smoke test
2. Date-shift test
3. Walk-forward from 2020-2026 to 2012-2019
4. Walk-forward from 2012-2019 to 2020-2026
5. Spread stress test
6. Slippage feasibility test and slippage stress test
7. Quarterly breakdown
8. Monthly breakdown
9. Final report and recommendation

Do not start the next module until the previous module has a summary CSV and a `WORK_LOG.md` entry.

---

## 10. Task 1: Smoke test

**Files:**

- Read: final candidate `.set` files listed in Section 4
- Create: `E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv`
- Modify: `E:\CODEXMACD\WORK_LOG.md`

Steps:

- [ ] Create all output directories listed in Section 6.
- [ ] Create the master matrix with the schema in Section 7.
- [ ] Run one smoke backtest for object B on `2020.01.01-2026.06.30`.
- [ ] Confirm the report contains non-empty net profit, PF, drawdown, and trade count.
- [ ] Confirm the result is close to the known object B value `556,052.56`; small drift is acceptable only if tester口径 is documented.
- [ ] Save `.set`, `.ini`, `.htm`, `_metrics.csv`, `_notes.md`.
- [ ] Append a `WORK_LOG.md` entry with status and paths.

Success condition:

```text
MT5 loads the intended EX5 and intended .set, report is generated, metrics parse correctly.
```

Stop condition:

```text
If the smoke run opens MT5 but produces no report, or report metrics are blank, do not batch run. Fix execution chain first.
```

---

## 11. Task 2: Date-shift test

Purpose:

```text
Check whether results depend on exact start/end dates.
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

| Case | Start date rule | End date rule |
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
4 objects × 2 windows × 8 shift cases = 64 runs
```

Summary metrics:

```text
net_profit_avg, net_profit_min, net_profit_std, profit_factor_avg, max_equity_dd_pct_max, trade_count_min, trade_count_std, sensitivity_rating
```

Decision rules:

```text
Low sensitivity: no severe loss, PF mostly >= 1.5, trade count stable, max drawdown not worse by more than roughly 20%-30%.
Medium sensitivity: one weak shift but no catastrophic collapse.
High sensitivity: one or more shifted windows collapse, lose heavily, or trade count falls sharply.
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv
```

---

## 12. Task 3: Walk-forward test, train 2020-2026 then validate 2012-2019

Purpose:

```text
Directly test whether current strong 2020-2026 performance is fixed-year fitting.
```

Training window:

```text
2020.01.01-2026.06.30
```

Validation window:

```text
2012.01.01-2019.12.31
```

v8.6 candidate count:

```text
12 training candidates, select top 3 robust candidates, run 6 sensitivity validations.
```

v8.66 candidate count:

```text
18 training candidates, select top 3 robust candidates, run 6 sensitivity validations.
```

Expected run count:

```text
48 runs
```

Selection rule:

```text
Do not pick top net profit only. Pick by robust score using profit, PF, drawdown, trade count, and parameter stability.
```

Fixed-year risk rule:

```text
If a candidate is excellent in 2020-2026 but weak or losing in 2012-2019, mark fixed-year overfitting risk high.
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv
```

---

## 13. Task 4: Walk-forward test, train 2012-2019 then validate 2020-2026

Purpose:

```text
Check whether parameters discovered in earlier market regimes generalize to the later anchor window.
```

Training window:

```text
2012.01.01-2019.12.31
```

Validation window:

```text
2020.01.01-2026.06.30
```

Expected run count:

```text
48 runs
```

Decision rule:

```text
If a parameter set performs well in early training and still keeps at least 85%-95% of the 2020-2026 anchor quality, it is a strong generalization candidate.
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv
```

---

## 14. Task 5: Fixed spread stress test

Purpose:

```text
Check whether the EA depends on ideal trading cost assumptions.
```

Important precondition:

```text
Before full spread testing, run one technical feasibility check to confirm the MT5 tester config actually applies fixed spread. If fixed spread cannot be verified, record this as a blocker and do not pretend the test is valid.
```

Objects:

```text
A, B, C, D
```

Windows:

```text
2012.01.01-2019.12.31
2020.01.01-2026.06.30
```

Spread levels:

| Level | Meaning |
|---|---|
| 1.0x | current baseline |
| 1.5x | medium pressure |
| 2.0x | high pressure |
| 2.5x | extreme pressure |
| 3.0x | limit pressure |

Expected run count:

```text
40 runs after feasibility is confirmed
```

Pass criteria:

```text
1.5x: profit retention >= 85%, PF >= 1.8 preferred.
2.0x: profit retention >= 70%, PF >= 1.5 preferred.
2.5x: no catastrophic collapse, drawdown not worse by about 1.3x.
3.0x: decline is allowed, system failure is not.
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_stress_summary.csv
```

---

## 15. Task 6: Slippage stress test

Purpose:

```text
Check whether execution price deviation destroys edge.
```

Important precondition:

```text
MT5 Strategy Tester may not provide reliable slippage simulation via .ini. First confirm feasibility. If direct tester slippage is not possible, create a separate plan for a temporary slippage-test EA before modifying code.
```

Objects:

```text
A, B, C, D
```

Windows:

```text
2012.01.01-2019.12.31
2020.01.01-2026.06.30
```

Slippage levels:

| Level | Meaning |
|---|---|
| 0 | baseline |
| 1 | mild |
| 2 | medium |
| 3 | high |
| 5 | extreme |

Expected run count:

```text
40 runs if slippage simulation is technically valid
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\slippage_stress_summary.csv
```

If slippage requires EA code change, do not edit the production EA. Create a separate temporary file name only after recording the reason:

```text
E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
```

---

## 16. Task 7: Quarterly breakdown

Purpose:

```text
Check whether profit is concentrated in a small number of quarters.
```

Objects:

```text
A, B, C, D
```

Period:

```text
2012 Q1 through 2023 Q4
```

Expected run count:

```text
4 objects × 48 quarters = 192 runs
```

Summary fields:

```text
profitable_quarter_ratio,worst_quarter_profit,best_quarter_profit,max_single_quarter_profit_share,max_consecutive_losing_quarters,total_quarter_net_profit,quarterly_stability_rating
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\quarterly_breakdown.csv
```

---

## 17. Task 8: Monthly breakdown

Purpose:

```text
Measure fine-grained stability and longest weak periods.
```

Recommended first phase:

```text
Only B and C from 2012.01 through 2023.12.
```

Expected first-phase run count:

```text
2 objects × 144 months = 288 runs
```

Optional full phase:

```text
4 objects × 144 months = 576 runs
```

Summary fields:

```text
profitable_month_ratio,worst_month_profit,best_month_profit,max_single_month_profit_share,max_consecutive_losing_months,total_month_net_profit,monthly_stability_rating
```

Required output:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\monthly_breakdown.csv
```

---

## 18. Task 9: Final summary and recommendation

Create final report:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_final_summary.md
```

The final report must answer:

```text
Is v8.66 robust main case0010 still the recommended main line?
Is v8.66 aggressive case0005 promoted, retained as observation, or rejected?
Is fixed-year overfitting risk low, medium, or high?
Is spread sensitivity low, medium, or high?
Is slippage sensitivity low, medium, or high?
Is date-boundary sensitivity low, medium, or high?
Is monthly/quarterly stability acceptable?
Should v8.67 development begin?
If v8.67 begins, should it focus on parameter governance, risk layer, structure layer, or debug telemetry?
```

Recommended final decision format:

| Candidate | Role | Decision | Reason |
|---|---|---|---|
| v8.66 robust case0010 | Main | keep / reject / retest | ... |
| v8.66 aggressive case0005 | Observation | promote / keep observation / reject | ... |
| v8.66 conservative case0401 | Risk reference | keep / reject | ... |
| v8.6 case0502 | Reference | keep reference / reject | ... |

---

## 19. Work log requirements

Every task completion must append to:

```text
E:\CODEXMACD\WORK_LOG.md
```

Use this format:

```text
## yyyy-MM-dd HH:mm:ss - <module name>
- Type: backtest / matrix / report / blocker / code-change
- Scope: ...
- Inputs: ...
- Outputs: ...
- Run count: ...
- Completed: ...
- Failed: ...
- Key metrics: ...
- Decision: ...
- Next step: ...
```

If a blocker occurs, record:

```text
- What failed
- Exact command or MT5 behavior
- Which files were created before failure
- Whether partial results are valid
- What must be fixed before continuing
```

---

## 20. Completion definition

This plan is complete only when:

```text
Smoke test completed and logged.
Date-shift summary created.
Both walk-forward summaries created.
Spread feasibility and spread summary completed or blocker documented.
Slippage feasibility and slippage summary completed or blocker documented.
Quarterly breakdown completed.
Monthly breakdown first phase completed.
Final summary report created.
WORK_LOG.md updated for every module.
No historical file was overwritten.
```

---

## 21. Recommended first execution step

After this plan is approved, execute only Task 1 first.

Do not start 64-run date-shift batch until the smoke test proves that:

```text
MT5 loads the correct EX5.
MT5 loads the correct .set.
The generated report is parsed correctly.
The result is close to the known v8.66 robust case0010 control result.
```