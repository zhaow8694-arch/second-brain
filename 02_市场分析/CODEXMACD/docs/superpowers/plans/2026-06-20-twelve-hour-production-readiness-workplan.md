# Twelve-Hour Production Readiness Workplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the SniperTrendEA v8.66/v8.67 line from backtest candidate status toward a production-ready, forward-test-ready system with stronger robustness evidence, better tooling, cleaner parameters, operational safety checks, and complete documentation.

**Architecture:** Treat the EA as a trading system, not only a source file. The system has five layers: strategy logic, parameter set, MT5 execution environment, validation pipeline, and operations/monitoring. This 12-hour block must improve all five layers without overwriting historical files or falsely declaring the system safe for full real-money deployment.

**Tech Stack:** MetaTrader 5 Strategy Tester, MQL5, PowerShell batch runners, `.set` files, HTML reports, CSV/Markdown matrices, `WORK_LOG.md`, `HANDOFF_NEXT_WINDOW.md`.

---

## 1. Important framing

This 12-hour plan is not a promise that the EA becomes guaranteed profitable or risk-free. No backtest can prove that.

The realistic 12-hour objective is:

```text
Move from “promising backtest candidate” to “structured production-readiness candidate suitable for demo/forward testing and possibly later micro-lot live observation.”
```

Do not call the EA fully real-live-ready unless these are completed:

```text
Spread pressure validated or blocker solved.
Slippage pressure validated or test method documented.
Quarterly and monthly stability analyzed.
v8.67 engineering version compiled and regression-tested.
Forward/demo monitoring package created.
Emergency stop and operating checklist documented.
```

---

## 2. Current project state

Current main candidate:

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

Old grok8.6 anchor:

```text
557,505.36 USD
```

Stage 1 pressure validation result:

```text
Smoke test passed.
Date-shift high sensitivity groups: 0.
Most date-shift groups: medium sensitivity.
Fixed-spread feasibility: inconclusive/blocker.
Aggressive parameter remains observation only.
```

Key files already produced:

```text
E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
E:\CODEXMACD\WORK_LOG.md
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_summary.md
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
E:\CODEXMACD\docs\superpowers\plans\2026-06-20-five-hour-pressure-validation-workplan.md
E:\CODEXMACD\docs\superpowers\plans\2026-06-20-v866-pressure-walkforward-validation.md
```

---

## 3. Non-negotiable rules

- Do not overwrite old `.mq5`, `.ex5`, `.set`, `.htm`, `.csv`, `.ini`, `.md`, or log files.
- Do not modify production EA source until the engineering task begins.
- Do not change grok8.6 core entry logic casually.
- Do not use aggressive parameters as the main line.
- Do not claim full live readiness if spread/slippage remain unresolved.
- Do not rely only on net profit.
- Every run, including failed and losing runs, must be archived.
- Every module must update `E:\CODEXMACD\WORK_LOG.md`.
- If a blocker appears, document it and continue with the next independent task if safe.

---

## 4. Twelve-hour work structure

| Time block | Module | Main purpose |
|---|---|---|
| 0:00-0:45 | Task 1: integrity review and tool repair | Fix reporting issues, verify paths, review Stage 1 outputs |
| 0:45-2:15 | Task 2: quarterly breakdown | 2012-2023 quarter stability for A/B/C/D |
| 2:15-4:15 | Task 3: monthly breakdown core | 2012-2023 monthly stability for B/C first |
| 4:15-5:15 | Task 4: fixed-spread blocker investigation | Verify whether MT5 supports real fixed-spread config in this environment |
| 5:15-6:15 | Task 5: slippage-test design | Decide whether slippage can be tested without source changes; if not, design temp EA only |
| 6:15-8:15 | Task 6: v8.67 production-engineering version | Parameter governance, version header, debug telemetry, default robust settings |
| 8:15-9:45 | Task 7: v8.67 compile and regression tests | Compile and run regression windows |
| 9:45-10:45 | Task 8: operations/forward-monitor package | Demo/live observation checklist, logs, monitor CSV templates |
| 10:45-11:30 | Task 9: production-readiness report | Summarize readiness, risks, blockers, go/no-go |
| 11:30-12:00 | Task 10: final handoff and cleanup | Update handoff, log, next action list |

If a long backtest block finishes early, use extra time for additional monthly windows or spread/slippage blocker work. Do not invent risky code changes to fill time.

---

## 5. Task 1: Integrity review and tool repair, 0:00-0:45

Purpose:

```text
Start from a clean operational picture before running more work.
```

Files to inspect:

```text
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv
E:\CODEXMACD\HCSJ\scripts\five_hour_stage1_unattended_runner.ps1
E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1
```

Steps:

- [ ] Read the Stage 1 summary and identify any formatting/reporting bug.
- [ ] Fix literal variable-path display if reports show `$Master`, `$DateCsv`, etc. instead of real paths.
- [ ] Confirm master matrices have non-empty metric fields.
- [ ] Confirm report archive paths exist for smoke, date-shift, walk-forward, and spread feasibility.
- [ ] Create a small `production_readiness` matrix directory.
- [ ] Append Task 1 result to `WORK_LOG.md`.

Output:

```text
E:\CODEXMACD\HCSJ\matrix\production_readiness
```

Success criteria:

```text
Stage 1 artifacts are readable, metric fields are valid, and any report formatting issue is repaired without changing historical raw data.
```

---

## 6. Task 2: Quarterly breakdown, 0:45-2:15

Purpose:

```text
Check whether profits are concentrated in a few quarters or spread across many quarters.
```

Objects:

```text
A: v8.6 robust case0502
B: v8.66 robust case0010
C: v8.66 aggressive case0005
D: v8.66 conservative case0401
```

Period:

```text
2012 Q1 through 2023 Q4
```

Expected runs:

```text
4 objects × 48 quarters = 192 runs
```

Output files:

```text
E:\CODEXMACD\HCSJ\matrix\production_readiness\quarterly_breakdown_matrix.csv
E:\CODEXMACD\HCSJ\matrix\production_readiness\quarterly_breakdown_summary.csv
```

Summary fields:

```text
object_id,version,set_role,quarter_count,completed_count,total_net_profit,profitable_quarter_count,profitable_quarter_ratio,worst_quarter,best_quarter,worst_quarter_profit,best_quarter_profit,max_single_quarter_profit_share,max_consecutive_losing_quarters,pf_avg,pf_min,max_equity_dd_pct_max,stability_rating,decision,notes
```

Decision rules:

```text
Good: profitable quarters >= 60%, no single quarter contributes more than 35% of total profit, no severe losing streak.
Watch: profitable quarters 45%-60%, or one quarter dominates.
Risk: profitable quarters < 45%, or a few quarters explain most of total profit.
```

Work log entry must include:

```text
Run count, completed count, best/worst candidate, whether B remains main candidate.
```

---

## 7. Task 3: Monthly breakdown core, 2:15-4:15

Purpose:

```text
Measure fine-grained stability and detect long weak periods before demo/live testing.
```

First phase objects:

```text
B: v8.66 robust case0010
C: v8.66 aggressive case0005
```

Period:

```text
2012.01 through 2023.12
```

Expected first-phase runs:

```text
2 objects × 144 months = 288 runs
```

If time remains, extend to:

```text
A and D, another 288 runs.
```

Output files:

```text
E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_core_matrix.csv
E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_core_summary.csv
```

Summary fields:

```text
object_id,version,set_role,month_count,completed_count,total_net_profit,profitable_month_count,profitable_month_ratio,worst_month,best_month,worst_month_profit,best_month_profit,max_single_month_profit_share,max_consecutive_losing_months,max_consecutive_losing_month_loss,pf_avg,pf_min,monthly_stability_rating,decision,notes
```

Decision rules:

```text
Good: profitable months >= 50%, max consecutive losing months <= 5, no extreme single-month dependency.
Watch: profitable months 40%-50%, or losing streak 6-8 months.
Risk: profitable months < 40%, or losing streak > 8 months, or one month dominates total profit.
```

Important:

```text
Monthly breakdown may contain many low-trade months because H4 strategy frequency is limited. Interpret with trade count, not profit alone.
```

---

## 8. Task 4: Fixed-spread blocker investigation, 4:15-5:15

Purpose:

```text
Resolve or clearly document the fixed-spread blocker.
```

Current blocker:

```text
The proven runner does not yet have a verified MT5 fixed-spread config hook.
```

Steps:

- [ ] Search existing MT5 `.ini` files in project for spread-related fields.
- [ ] Check whether MT5 tester config supports `Spread`, `SpreadMode`, or another fixed-spread field in this environment.
- [ ] Run a single technical feasibility test if a candidate field is found.
- [ ] Confirm from report/config whether spread actually changed.
- [ ] If confirmed, run a small 6-run spread mini-test for object B only.
- [ ] If not confirmed, write a blocker note and do not fabricate results.

Output files:

```text
E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_feasibility_recheck.csv
E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_feasibility_notes.md
```

Decision values:

```text
confirmed
blocked
inconclusive
```

If confirmed and time remains, mini-test levels:

```text
1.0x, 1.5x, 2.0x
```

Windows:

```text
2012-2019
2020-2026
```

Mini-test runs:

```text
1 object × 3 spread levels × 2 windows = 6 runs
```

---

## 9. Task 5: Slippage-test design, 5:15-6:15

Purpose:

```text
Design a valid slippage pressure method without corrupting the production EA.
```

Steps:

- [ ] Determine whether MT5 tester can simulate slippage through config in current environment.
- [ ] If direct config is unavailable, create a written design for a temporary slippage-test EA.
- [ ] Do not modify production v8.66/v8.67 source in this task.
- [ ] If a temp EA is needed, plan it as a separate file only.

Possible temp file name:

```text
E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
```

Slippage levels to design:

```text
0, 1, 2, 3, 5
```

Output:

```text
E:\CODEXMACD\docs\superpowers\plans\2026-06-20-slippage-test-ea-design.md
E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_test_feasibility.md
```

Decision:

```text
direct_config_possible
requires_temp_ea
blocked
```

---

## 10. Task 6: v8.67 production-engineering version, 6:15-8:15

Purpose:

```text
Create a cleaner engineering version for demo/forward testing without changing the core entry edge.
```

Source input:

```text
E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5
```

New source output:

```text
E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
```

Required changes:

1. Version header:

```text
v8.67_grokbase_production_ready
Based on v8.66 r68 robust main case0010
```

2. Default input values:

```text
Align defaults with v8.66_robust_main_case0010.set
```

3. Input parameter governance:

```text
Group 77 input settings into clear blocks:
- Core signal parameters
- Filter parameters
- Risk parameters
- Structure score parameters
- Debug/telemetry parameters
- Do-not-optimize parameters
```

4. Add optional telemetry inputs:

```text
InpEnableDecisionLog=false
InpDecisionLogLevel=1
InpLogSignalReasons=false
InpLogRiskState=false
InpLogStructureScore=false
```

5. Add decision logging without changing trading decisions:

```text
When disabled, behavior should remain equivalent to v8.66 robust defaults.
When enabled, log why a signal is accepted/rejected and how lot size is scaled.
```

6. Add safety identity:

```text
EA version string
Parameter profile string
Recommended set name string
```

Do not change:

```text
MACD entry logic
MA200 filter behavior
Ignition exit behavior
Order execution rules except logging/safety identity
```

Output:

```text
E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
```

Work log must record every source change.

---

## 11. Task 7: v8.67 compile and regression tests, 8:15-9:45

Purpose:

```text
Confirm v8.67 compiles and preserves v8.66 robust behavior before any further development.
```

Compile output:

```text
E:\CODEXMACD\HCSJ\logs\compile_v867_grokbase_production_ready_<timestamp>.log
D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_<timestamp>.ex5
```

Regression windows:

```text
2012-2014
2015-2019
2017-2023
2020-2025
2020-2026.06.30
```

Expected regression runs:

```text
5
```

Success criteria:

```text
Compile: 0 errors.
2020-2026 net profit close to v8.66 robust case0010, unless logging/default alignment is intentionally different and documented.
PF >= 2.0 on 2020-2026.
Trade count close to 203 on 2020-2026.
No report-generation failure.
```

Output:

```text
E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_regression_matrix.csv
E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_regression_summary.md
```

If regression fails:

```text
Do not patch blindly. Preserve failing source snapshot and document blocker.
```

---

## 12. Task 8: Operations and forward-monitor package, 9:45-10:45

Purpose:

```text
Prepare the system for demo/forward testing discipline.
```

Create folder:

```text
E:\CODEXMACD\HCSJ\forward_monitor
```

Create files:

```text
E:\CODEXMACD\HCSJ\forward_monitor\forward_test_trade_log.csv
E:\CODEXMACD\HCSJ\forward_monitor\forward_test_daily_equity.csv
E:\CODEXMACD\HCSJ\forward_monitor\forward_test_incident_log.csv
E:\CODEXMACD\HCSJ\forward_monitor\forward_test_checklist.md
E:\CODEXMACD\HCSJ\forward_monitor\live_micro_observation_rules.md
```

Trade log fields:

```csv
date,time,account_type,symbol,timeframe,ea_version,set_name,ticket,direction,lot,entry_price,sl,tp,exit_price,profit,spread_at_entry,spread_at_exit,slippage_estimate,max_floating_dd,open_reason,close_reason,ea_log_excerpt,manual_intervention,notes
```

Daily equity fields:

```csv
date,account_type,balance,equity,margin,free_margin,open_positions,daily_profit,daily_drawdown_pct,max_intraday_drawdown_pct,notes
```

Incident log fields:

```csv
date,time,severity,event_type,description,impact,action_taken,resolved,notes
```

Checklist must include:

```text
Before attaching EA
After attaching EA
Daily check
Weekly check
Emergency stop condition
Do-not-trade condition
Parameter file verification
VPS/terminal restart check
```

---

## 13. Task 9: Production-readiness report, 10:45-11:30

Purpose:

```text
Produce a single go/no-go document for demo testing, micro-live observation, and future development.
```

Create:

```text
E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report.md
```

The report must answer:

```text
Is v8.66 robust case0010 still the main candidate?
Is v8.67 production-ready source created and regression-tested?
Is demo/forward testing allowed?
Is micro-live observation allowed?
Is full real-money live trading allowed?
What blockers remain?
What exact set file should be used?
What exact EA file should be used?
What account risk settings should be used?
What conditions force shutdown?
```

Decision levels:

```text
Level 0: not ready
Level 1: ready for more backtest only
Level 2: ready for demo/forward test
Level 3: ready for micro-lot live observation
Level 4: ready for controlled live deployment
```

Expected current target after 12 hours:

```text
Level 2, possibly Level 3 only if spread/slippage blockers are resolved.
```

Do not declare Level 4 in this block unless all major blockers are solved.

---

## 14. Task 10: Final handoff and cleanup, 11:30-12:00

Purpose:

```text
Make the next window able to continue without friction.
```

Update:

```text
E:\CODEXMACD\WORK_LOG.md
E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
```

Update content:

```text
What was completed
What failed
What remains blocked
Current main EA file
Current main set file
Current readiness level
Next recommended task
All important report paths
```

Do not start new long-running backtests in the final 30 minutes.

---

## 15. If time remains after all tasks

Use extra time in this order:

1. Extend monthly breakdown from B/C to A/D.
2. Run additional v8.67 regression on `2024-2026.06.30`.
3. Add a `SET_MANIFEST.md` explaining every final candidate set.
4. Improve report parser to include long/short trade split and consecutive loss count.
5. Prepare a future plan for true fixed-spread/slippage validation.

Do not use extra time to make speculative signal changes.

---

## 16. Expected 12-hour deliverables

Expected deliverables:

```text
Quarterly breakdown matrix and summary
Monthly breakdown core matrix and summary
Spread feasibility recheck note
Slippage feasibility/design note
v8.67 production-ready source file
v8.67 default robust set file
v8.67 compile log
v8.67 regression matrix and summary
Forward-monitor package
Production-readiness report
Updated WORK_LOG.md
Updated HANDOFF_NEXT_WINDOW.md
```

---

## 17. Final readiness interpretation

After this 12-hour block:

```text
If v8.67 compiles and matches v8.66 robust behavior, and quarterly/monthly analysis is acceptable, the system may be considered demo/forward-test ready.
```

```text
If spread and slippage remain unresolved, the system should not be considered full real-money live ready.
```

```text
If spread/slippage are resolved and results remain stable, micro-lot live observation can be considered with strict risk limits.
```

---

## 18. Micro-live observation conditions, if eventually approved

Only consider micro-live observation if all are true:

```text
Main set remains v8.66/v8.67 robust case0010 lineage.
Aggressive set is not used.
Risk percent is reduced to 0.05-0.10 or minimum lot.
Account is isolated.
Daily max loss stop is defined.
Manual emergency stop is documented.
Forward monitor files are active.
No unresolved EA compile/regression issue exists.
```

---

## 19. Completion definition

This 12-hour plan is complete when:

```text
All completed modules are archived.
All blockers are documented.
Production readiness report exists.
Forward-monitor package exists.
v8.67 engineering status is known.
WORK_LOG.md is updated.
HANDOFF_NEXT_WINDOW.md is updated.
No historical file was overwritten.
```