# TASK-310 MQL5 compile artifact hash capture diagnostic

## Scope

- artifact-hash-capture-diagnostic-only
- not success reclassification
- not TASK-304 success result
- TASK-310 may re-run MetaEditor compile-only only against quarantine copy
- artifact hash must be stdout-only
- artifact hash must not be saved to repository
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- Inventory only; no MT5 run; no trading authorization.

## Current Baseline

- current HEAD: f31b85e TASK-309 create MQL5 compile-only success reclassification boundary
- current tag: v0.5.105-task-309-mql5-compile-success-reclassification-boundary
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed quarantine_ex5_artifact_count=1
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-309 defined success reclassification boundary but did not execute success reclassification
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- success_reclassification_done=false
- task304_success_result_created=false
- compile_success=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Authorized Diagnostic Boundary

- MetaEditor compile-only may be executed only against a quarantine copy
- quarantine directory must remain outside the repository
- quarantine .ex5 may exist only temporarily inside the quarantine directory
- compile log may exist only temporarily inside the quarantine directory
- quarantine artifact SHA256 and size may be emitted to stdout only
- artifact hash must not be saved to repository
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- quarantine directory must be deleted before completion
- repo_ex5_artifacts=false after cleanup
- repo_compile_logs=false after cleanup
- repo_mq5_modified=false after cleanup
- success_reclassification_done=false
- task304_success_result_created=false
- compile_success=false
- no MT5 terminal run
- no Strategy Tester run
- no backtest
- no trading
- no manifest generated
- no evidence generated
- no report generated
- no external evidence copied

## Next Boundary

- future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix
- TASK-311 must not be entered directly
