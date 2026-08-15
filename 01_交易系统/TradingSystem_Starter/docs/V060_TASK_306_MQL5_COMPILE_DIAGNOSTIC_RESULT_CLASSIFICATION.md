# TASK-306 MQL5 compile-only diagnostic result classification

## Scope

- diagnostic-classification-only
- not compile execution
- not MetaEditor execution in TASK-306
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not simulation / real trading authorization
- not TASK-304 success result

## Baseline

- TASK-305 completed.
- current HEAD: c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture
- current tag: v0.5.101-task-305-mql5-compile-only-failure-diagnostic
- compile_exit_code=1 observed in TASK-305
- compile log excerpt indicated Result: 0 errors, 0 warnings
- task304_success_result_created=false
- repo_ex5_artifacts=false
- repo_compile_logs=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Classification

- compile_result_classification=metaeditor_exit_code_anomaly
- compile_log_semantic_success=true
- compile_success=false
- task304_success_result_created=false
- followup_required=true
- This separates MetaEditor process exit code interpretation from compile log semantic result.
- This does not mark TASK-304 as success.
- This does not create a TASK-304 success result document.

## Safety

- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- no fixture generated
- no external evidence copied
- no MQ5/MQH modification
- no authorization / trading / execution field changed to true
- Inventory only; no MT5 run; no trading authorization.

## Next Boundary

- future TASK-307 must be separately authorized by GPT before any compile retry or MQ5 fix
- TASK-307 must not be entered directly
