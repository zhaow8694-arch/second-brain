# v8.6-v8.66 Robust Parameter Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable MT5 testing workflow that compares SniperTrendEA v8.6 and v8.66 across multiple historical windows, searches for robust best parameter sets, and rejects overfit parameter groups.

**Architecture:** Use v8.6 as the baseline profit anchor and v8.66 as the candidate structure-risk version. Run fixed-parameter baselines first, then bounded parameter searches, then cross-window validation and robustness scoring. Every `.set`, report, metrics table, log, and failed run is archived without overwriting historical files.

**Tech Stack:** MetaTrader 5 Strategy Tester, MQL5 EA source/EX5 builds, `.set` parameter files, HTML backtest reports, CSV/Markdown result matrices, `E:\CODEXMACD\WORK_LOG.md` for traceability.

---

## 1. Scope and non-goals

This plan covers both overfitting control and best-setting discovery.

The objective is not to find the highest single-period net profit. The objective is to find parameter sets that keep the grok8.6 profit backbone, reduce or stabilize drawdown, and remain effective across different market regimes.

This plan must not overwrite older source files, `.set` files, reports, or matrices. Every run receives a unique name and archive folder.

This plan does not change EA source code unless a compile/runtime defect blocks valid testing. If code changes become necessary, create a new minor version and record the reason in `WORK_LOG.md` before testing resumes.

---

## 2. EA versions under test

Baseline old version:

`SniperTrendEA v8.6`

Known baseline anchor:

`E:\GROKMACD\SniperTrendEA_v8.6.mq5`

Candidate new version:

`E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5`

Candidate EX5 snapshot:

`E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.ex5`

Main previous anchor result for full-window sanity check:

`557,505.36 USD` net profit for v8.6 on `XAUUSD H4 2020.01.01-2026.06.30`, deposit `20000`, leverage `1:100`.

---

## 3. Fixed test口径

All valid comparisons must use the same test口径.

Required fixed settings:

- Symbol: `XAUUSD`
- Timeframe: `H4`
- Deposit: `20000 USD`
- Leverage: `1:100`
- MT5 working directory: `D:\MT5测试\MetaTrader 5`
- Tester config must explicitly load `.set` via `ExpertParameters=<relative_set_file_name>`
- `.set` files must be copied to `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester` before each run
- Strategy tester model must stay consistent across all runs
- Spread mode must stay consistent across all runs
- Report output must use unique names
- `ReplaceReport=1` is allowed only inside each unique output folder/name
- `ShutdownTerminal=1` should be used for batch automation

Every run must record:

- EA version
- source file path
- EX5 file path
- `.set` path
- time window
- tester model
- spread setting
- deposit
- leverage
- start/end date
- report path
- run status
- net profit
- profit factor
- max balance drawdown
- max equity drawdown
- relative equity drawdown
- total trades
- win rate
- consecutive loss information if available
- notes about invalid/failure conditions

---

## 4. Required historical windows

The three required independent windows are:

- `2012-2014`
- `2015-2019`
- `2017-2023`

Use exact date boundaries:

- `2012-2014`: `2012.01.01` to `2014.12.31`
- `2015-2019`: `2015.01.01` to `2019.12.31`
- `2017-2023`: `2017.01.01` to `2023.12.31`

Optional later control windows:

- `2020-2025`: compare with previous main development口径
- `2020-2026.06.30`: compare with known v8.6 full anchor `557,505.36 USD`

The optional windows are not substitutes for the three required windows.

---

## 5. Parameter search philosophy

Best setting means robust best setting, not highest profit.

A parameter set is preferred only if it satisfies all of these ideas:

- It performs acceptably across multiple time windows.
- It avoids catastrophic performance in the worst window.
- It does not depend on one special market period for most of its profit.
- It does not reduce trade count so much that the EA only looks stable because it barely trades.
- Small parameter changes do not cause cliff-like result collapse.
- Drawdown improves or stays controlled without destroying the grok8.6收益主线.

---

## 6. Parameter classes

Do not optimize all `77` v8.66 input settings at once.

Parameter classes:

- Frozen parameters: original grok8.6 profit-backbone settings that should remain unchanged during the first search stage.
- Common parameters: parameters shared by v8.6 and v8.66 and safe to compare in matched ranges.
- Risk parameters: v8.66 risk throttle, lot scale, drawdown warning, max open positions, cooldown, consecutive-loss controls.
- Structure parameters: v8.66 structure score, no-structure penalty, quality floor, breakout score, trendline/touch settings.
- Debug/display parameters: never optimized unless needed for diagnosis.

Initial recommendation:

- First optimize risk parameters in a narrow range.
- Then optimize structure parameters in a narrow range.
- Only then consider common core signal parameters.
- Keep each optimization batch to a small number of active dimensions.

---

## 7. Required archive structure

Use this archive structure:

```text
E:\CODEXMACD\HCSJ\
  backtest_archive\
    v8.6\
      2012-2014\
      2015-2019\
      2017-2023\
    v8.66\
      2012-2014\
      2015-2019\
      2017-2023\
  set\
    v8.6\
      2012-2014\
      2015-2019\
      2017-2023\
    v8.66\
      2012-2014\
      2015-2019\
      2017-2023\
  matrix\
  logs\
```

Every run must have a unique run id.

Recommended run id format:

`<version>_<window>_<stage>_round<NN>_case<NNNN>`

Example:

`v866_2015-2019_risksearch_round01_case0007`

Files produced from that run:

- `v866_2015-2019_risksearch_round01_case0007.set`
- `v866_2015-2019_risksearch_round01_case0007.htm`
- `v866_2015-2019_risksearch_round01_case0007_metrics.csv`
- `v866_2015-2019_risksearch_round01_case0007_config.ini`
- `v866_2015-2019_risksearch_round01_case0007_notes.md`

Failed, losing, no-trade, invalid, and crashed runs must also be archived.

---

## 8. Robustness scoring model

Use hard filters first. Only parameter sets passing the hard filters receive a robustness score.

Hard filters:

- No required window may have catastrophic loss.
- Total trade count must not collapse compared with the corresponding baseline.
- PF must not fall below the minimum acceptable threshold for that window.
- Max equity drawdown must not materially worsen unless profit retention clearly compensates and the case is marked as aggressive.
- The set must not depend on a single year for most of its total profit.
- Minor nearby parameter changes must not collapse the result.

Suggested robustness score:

```text
RobustnessScore =
  ProfitRetentionScore
+ DrawdownControlScore
+ ProfitFactorStabilityScore
+ WorstWindowProtectionScore
+ TradeCountStabilityScore
+ YearlyDistributionScore
+ ParameterSensitivityScore
```

Recommended interpretation:

- `90+`: strong robust candidate
- `80-89`: usable candidate
- `70-79`: watchlist candidate
- `<70`: reject for main recommendation

The score is a decision aid. If the score conflicts with obvious risk behavior, human review overrides the score.

---

## 9. Required candidate categories

Final output should not be only one `.set`.

Each EA version should produce these categories when possible:

- Robust main setting: best balance of cross-window profit, drawdown, PF, and trade stability.
- Aggressive high-profit setting: higher return while still passing overfitting checks.
- Conservative low-drawdown setting: lower drawdown and smoother behavior, allowed to sacrifice more profit.

The robust main setting is the primary candidate for future development and forward testing.

---

## 10. Execution tasks

### Task 1: Establish folders and run ledger

**Files:**

- Create folders under `E:\CODEXMACD\HCSJ\backtest_archive`
- Create folders under `E:\CODEXMACD\HCSJ\set`
- Create or update `E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_matrix.csv`
- Modify `E:\CODEXMACD\WORK_LOG.md`

- [ ] Create required v8.6 and v8.66 archive folders.
- [ ] Create required v8.6 and v8.66 `.set` folders.
- [ ] Create the master matrix with fixed columns.
- [ ] Add a `WORK_LOG.md` entry stating that the robust parameter search campaign has started.

Master matrix columns:

```csv
run_id,version,window,stage,round,case_id,status,source_file,ex5_file,set_file,config_file,report_file,start_date,end_date,symbol,timeframe,model,spread,deposit,leverage,net_profit,profit_factor,max_balance_dd,max_balance_dd_pct,max_equity_dd,max_equity_dd_pct,relative_equity_dd,relative_equity_dd_pct,total_trades,win_rate,robustness_score,candidate_class,decision,notes
```

### Task 2: Compile or confirm EA build artifacts

**Files:**

- Use `E:\GROKMACD\SniperTrendEA_v8.6.mq5`
- Use `E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5`
- Archive compile logs in `E:\CODEXMACD\HCSJ\logs`

- [ ] Confirm v8.6 EX5 exists or compile it from the true grok8.6 source.
- [ ] Confirm v8.66 EX5 exists or compile from the r68 candidate source.
- [ ] Copy EX5 files to the MT5 Experts folder with versioned names.
- [ ] Archive compile logs.
- [ ] Record compile result in `WORK_LOG.md`.

Valid compile condition:

`0 errors` in the compile log and EX5 output exists.

### Task 3: Fixed-parameter baseline pass

**Files:**

- Use original v8.6 `.set`
- Use current v8.66 r68 `.set`
- Save reports under the required archive folders
- Save `.set` files under the required `set` folders

- [ ] Run v8.6 original setting on `2012-2014`.
- [ ] Run v8.6 original setting on `2015-2019`.
- [ ] Run v8.6 original setting on `2017-2023`.
- [ ] Run v8.66 r68 setting on `2012-2014`.
- [ ] Run v8.66 r68 setting on `2015-2019`.
- [ ] Run v8.66 r68 setting on `2017-2023`.
- [ ] Save every `.set`, config, HTML report, and metrics row.
- [ ] Compare fixed v8.66 against fixed v8.6 before any optimization.

Decision rule:

If v8.66 only improves after optimization but fixed r68 is weak across the required windows, mark v8.66 as needing stronger validation.

### Task 4: Bounded v8.6 parameter search

**Files:**

- Save all generated v8.6 `.set` files under `E:\CODEXMACD\HCSJ\set\v8.6\<window>`
- Save all reports under `E:\CODEXMACD\HCSJ\backtest_archive\v8.6\<window>`
- Append all results to `robust_parameter_search_matrix.csv`

- [ ] Freeze high-risk/core parameters that define the original grok8.6收益主线.
- [ ] Select a small common-parameter search range.
- [ ] Search parameters on `2012-2014`.
- [ ] Validate top robust candidates on `2015-2019` and `2017-2023`.
- [ ] Search parameters on `2015-2019`.
- [ ] Validate top robust candidates on `2012-2014` and `2017-2023`.
- [ ] Search parameters on `2017-2023`.
- [ ] Validate top robust candidates on `2012-2014` and `2015-2019`.
- [ ] Rank all candidates using hard filters and robustness score.

Reject rule:

Any v8.6 set that wins only one window and fails the others is rejected as overfit, even if its single-window profit is highest.

### Task 5: Bounded v8.66 risk-layer search

**Files:**

- Save all generated v8.66 risk `.set` files under `E:\CODEXMACD\HCSJ\set\v8.66\<window>`
- Save all reports under `E:\CODEXMACD\HCSJ\backtest_archive\v8.66\<window>`
- Append all results to `robust_parameter_search_matrix.csv`

- [ ] Start from the r68 candidate setting.
- [ ] Keep core grok8.6 signal parameters frozen.
- [ ] Search only the risk-layer parameters in narrow ranges.
- [ ] Run the same sample-in and sample-out validation pattern as v8.6.
- [ ] Compare risk-layer candidates against fixed r68 and fixed v8.6 baseline.
- [ ] Reject risk settings that reduce drawdown only by destroying trade frequency or profit retention.

Primary risk-layer parameters:

- `InpRiskPercent`
- `InpUseRiskThrottle`
- `InpMaxDailyDDPercent`
- `InpConsecutiveLossLimit`
- `InpCooldownBars`
- `InpMaxOpenPositions`
- `InpRiskLotScale`
- `InpRiskWarningDDRatio`
- `InpMaxPeakDDPercent`
- `InpPeakDDWarningRatio`

### Task 6: Bounded v8.66 structure-layer search

**Files:**

- Save all generated v8.66 structure `.set` files under `E:\CODEXMACD\HCSJ\set\v8.66\<window>`
- Save all reports under `E:\CODEXMACD\HCSJ\backtest_archive\v8.66\<window>`
- Append all results to `robust_parameter_search_matrix.csv`

- [ ] Start from the best risk-layer candidate.
- [ ] Keep core signal parameters frozen.
- [ ] Search structure parameters in narrow ranges.
- [ ] Prefer soft scoring and lot adjustment over hard rejection.
- [ ] Run sample-in and sample-out validation.
- [ ] Reject structure settings that improve one period while harming cross-period stability.

Primary structure-layer parameters:

- `InpUseStructureScore`
- `InpRejectNoStructure`
- `InpSwingLookback`
- `InpStructureScanBars`
- `InpMinTrendlineTouches`
- `InpTrendlineTouchATR`
- `InpMinBreakoutDistanceATR`
- `InpMinBreakoutScore`
- `InpNoStructurePenalty`
- `InpMinStructureQualityFloor`
- `InpShowStructureDebug`

### Task 7: Sensitivity and stress validation

**Files:**

- Save stress `.set` files under the same version/window folder with `stress` in the run id
- Save reports under the same version/window report folder with `stress` in the run id
- Append results to `robust_parameter_search_matrix.csv`

- [ ] Apply minor parameter perturbations around each finalist.
- [ ] Shift date boundaries slightly when practical.
- [ ] Test widened spread when practical.
- [ ] Compare yearly performance distribution inside each required window.
- [ ] Reject candidates with cliff-like sensitivity.

Sensitivity rejection examples:

- A small `InpRiskLotScale` change causes profit or drawdown to collapse.
- A small structure score threshold change removes too many trades.
- One year contributes most of the total profit while other years are flat or negative.

### Task 8: Final selection and report

**Files:**

- Create `E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_summary.md`
- Create final selected `.set` files under `E:\CODEXMACD\HCSJ\set\final_candidates`
- Modify `E:\CODEXMACD\WORK_LOG.md`

- [ ] Select v8.6 robust main, aggressive, and conservative candidates when available.
- [ ] Select v8.66 robust main, aggressive, and conservative candidates when available.
- [ ] Compare v8.66 against v8.6 by window and by final category.
- [ ] State whether v8.66 preserves the grok8.6收益主线.
- [ ] State whether v8.66 lowers drawdown honestly or only by reducing trade count.
- [ ] State each version's overfitting level: no obvious, light, medium, or heavy.
- [ ] Record all chosen and rejected parameter regions.
- [ ] Add a final campaign summary to `WORK_LOG.md`.

Final report must include:

- Full performance comparison table
- Candidate `.set` path list
- Archive directory list
- Overfitting judgment
- Best-setting rationale
- Rejected-setting rationale
- Residual risks
- Recommended next action

---

## 11. Decision rules for final recommendation

Recommended main candidate must satisfy:

- It is profitable across the required windows or has clearly explainable weakness in one early-data window.
- It has no catastrophic sample-out failure.
- It keeps trade count reasonably close to baseline behavior.
- It improves or stabilizes drawdown relative to the appropriate baseline.
- It does not require extreme parameter values.
- It survives nearby-parameter sensitivity checks.

Aggressive candidate may accept higher drawdown if:

- Profit retention is meaningfully better.
- Sample-out behavior remains acceptable.
- Trade count is not artificially collapsed.
- The user understands it is not the main robust setting.

Conservative candidate may accept lower profit if:

- Drawdown reduction is meaningful.
- It remains active enough to be statistically useful.
- It does not simply avoid trading.

---

## 12. Completion definition

This plan is complete when these deliverables exist:

- v8.6 fixed baseline reports for all three required windows
- v8.66 fixed baseline reports for all three required windows
- v8.6 bounded search archive with all `.set` and reports retained
- v8.66 bounded risk/structure search archive with all `.set` and reports retained
- Master CSV matrix with every run, including failures
- Summary Markdown report with final recommendations
- Final candidate `.set` package for robust, aggressive, and conservative categories where available
- `WORK_LOG.md` updated for every major batch and final conclusion

---

## 13. Immediate next action after approval

After the user approves execution, start with Task 1 only.

Do not begin parameter search before the fixed baseline pass is archived and reviewed.