# TASK-307 MQL5 compile diagnostic artifact classification

- diagnostic-artifact-classification-only
- not TASK-304 success result
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- TASK-307 may re-run MetaEditor compile-only only against quarantine copy
- quarantine artifact inspection before cleanup
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- task304_success_result_created=false
- compile_success=false unless a future GPT boundary explicitly reclassifies success
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 560079c TASK-306 implement MQL5 compile-only diagnostic result classification
- current tag: v0.5.102-task-306-mql5-compile-diagnostic-classification
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-308 must be separately authorized by GPT before any compile retry or MQ5 fix
- TASK-308 must not be entered directly

## Scope

TASK-307 adds the third diagnostic dimension for compile-only analysis:
quarantine-local artifact presence. It classifies whether a quarantine `.ex5`
appeared before cleanup, while keeping repository state clean and keeping
TASK-304 success uncreated.

This planning and tooling state does not authorize MT5 terminal execution,
Strategy Tester, backtest, simulation, real trading, manifest generation,
evidence generation, report generation, or any repository artifact copy.
