# V060 First Low-Risk Implementation Plan

## Document Nature

- This document is planning-only.
- This document is not implementation authorization.
- This document records no MQ5 modification.
- TASK-DOC-237 does not authorize MQ5 modification.
- TASK-DOC-237 does not authorize an MT5 run.
- TASK-DOC-237 does not authorize trading.
- TASK-DOC-237 does not authorize real trading.
- TASK-DOC-237 does not authorize profitability optimization.
- TASK-DOC-237 does not create manifest / fixture / report / directory.
- TASK-DOC-237 does not copy external evidence.

## Stable Boundaries

- docs/V060_TRANSITION_BOUNDARY.md exists and remains fixed.
- docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md exists and remains fixed.
- docs/WORKFLOW_SIMPLIFICATION_BOUNDARY.md exists and remains fixed.
- TASK-DOC-237 must not redefine those stable boundaries.
- TASK-DOC-237 only defines the first low-risk implementation plan under those stable boundaries.

## Current Baseline

- Current phase remains v0.5.0.
- Current HEAD remains b3a981d TASK-DOC-236 update state after TASK-235.
- Current latest tag is v0.5.38-task-236-project-state-synced.
- Tracked working tree was clean after TASK-DOC-236 commit.
- MQ5 root exists.
- TASK-235 scanned 7 files: 1 .mq5 and 6 .mqh.
- MQ5 inventory files:
  - config/InputConfig.mqh
  - core/EaController.mqh
  - execution/ExecutionManager.mqh
  - logger/Logger.mqh
  - risk/RiskManager.mqh
  - signals/SignalEngine.mqh
  - TradingSystem.mq5
- input parameter lines: 34.
- InpEnableTrading appears in 4 files.
- RiskManager appears in 2 files.
- SignalEngine appears in 4 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade trading keywords are all false.
- Current MQ5 codebase is pure framework / no active trading instructions.
- OnInit / OnTick / OnDeinit are present in framework files.
- Inventory only; no MT5 run; no trading authorization.
- v0.6.0 implementation has not started.

## Future Candidate Slice

Recommended future candidate name:

TASK-238 v0.6.0 no-trade observability scaffold

This is a future candidate only. It is not authorized by TASK-DOC-237.

If ChatGPT later authorizes TASK-238 with an explicit boundary, it may become the first low-risk implementation slice. TASK-DOC-237 does not execute TASK-238 and does not authorize implementation.

## Future TASK-238 Candidate Boundary

- Scope: no-trade observability scaffold only.
- Keep InpEnableTrading false by default.
- Do not introduce Buy / Sell / OrderSend / PositionOpen / CTrade.
- Do not trigger real trading, simulated trading, backtest trading, or order sending.
- Do not create official evidence.
- Do not create manifest.
- Do not copy external evidence.
- Do not modify backtest/sets.
- Do not optimize profitability.
- Do not run MT5 unless a later ChatGPT task defines an explicit boundary.

## Low-Risk Planning Directions

Future TASK-238 may plan low-risk changes such as:

- strengthen read-only state observability;
- strengthen no-trade logging / telemetry contract;
- define non-trading state output for signal / risk / controller modules;
- add text-level safety guard / validator coverage;
- preserve that MQ5 still contains no trading execution keywords.

## Future Implementation Entry Conditions

Before any future TASK-238 implementation may begin:

- TASK-DOC-237 must be reviewed, validated, committed, and tagged by Trae if explicitly assigned.
- release validation bundle selective checks for project-state-docs / project-state-docs-self-test / mq5-inventory must PASS.
- ChatGPT must issue a separate explicit TASK-238 boundary.
- tracked working tree must be clean.
- there must be no unauthorized MQ5 modification.

## Future Implementation Acceptance Conditions

Any future TASK-238 implementation must satisfy:

- MQ5 inventory remains PASS.
- Trading keywords remain false.
- InpEnableTrading default still must not authorize trading.
- No manifest / fixture / report / external evidence is produced.
- MT5 is not run unless separately authorized by ChatGPT.
- official manifest and backtest/sets remain unmodified unless separately authorized.
- project-state-docs validator PASS.
- git diff --check PASS.

## TASK-DOC-237 Exit Criteria

- Only allowed docs and validator / test files are created or updated.
- docs/V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md exists.
- MQ5 is not modified.
- MT5 is not run.
- No manifest / fixture / report / directory is created.
- external evidence is not copied.
- release validation bundle selective checks PASS.
- git diff --check PASS.
- git status --short shows only allowed modified files and existing untracked items.

## Next Boundary

- Do not directly enter TASK-238.
- Do not directly enter v0.6.0 implementation.
- Do not directly modify MQ5.
- Do not directly run MT5.
- The next task boundary must be issued by ChatGPT.
