# TASK-308 MQL5 compile diagnostic artifact proof and success reclassification boundary

## Scope

- planning-only
- diagnostic-proof-boundary-only
- not compile execution
- not MetaEditor execution in TASK-308
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-308
- TASK-308 does not create TASK-304 success result doc
- Inventory only; no MT5 run; no trading authorization.

## Current Baseline

- current HEAD: 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification
- current tag: v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-307 compile_success=false
- TASK-307 task304_success_result_created=false
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Future Success Reclassification Minimum Conditions

- future GPT boundary explicitly authorizes success reclassification attempt
- future task may re-run MetaEditor compile-only only against quarantine copy
- future task must capture quarantine .ex5 metadata before deletion
- future task must output artifact metadata to stdout only
- future task must not copy .ex5 into repository
- future task must not save compile log into repository
- future task must compute quarantine artifact hash before deleting quarantine directory
- future task must output quarantine artifact size
- future task must output quarantine artifact path as temporary path only
- future task must delete quarantine directory before completion
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must still not run MT5 terminal
- future task must still not run Strategy Tester
- future task must still not trade
- future task must not create official manifest / evidence / report unless separately authorized

## Next Boundary

- future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification
- TASK-309 must not be entered directly
