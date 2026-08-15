# TASK-309 MQL5 compile-only success reclassification boundary

## Scope

- planning-only
- success-reclassification-boundary-only
- not compile execution
- not MetaEditor execution in TASK-309
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-309
- TASK-309 does not create TASK-304 success result doc
- TASK-309 does not reclassify compile success
- Inventory only; no MT5 run; no trading authorization.

## Current Baseline

- current HEAD: 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary
- current tag: v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed quarantine_ex5_artifact_count=1
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-307 compile_success=false
- TASK-307 task304_success_result_created=false
- TASK-308 defined diagnostic artifact proof boundary
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
- future task must compute quarantine artifact hash before deleting quarantine directory
- future task must output quarantine artifact hash to stdout only
- future task must output quarantine artifact size
- future task must output quarantine artifact temporary path only
- future task must not copy .ex5 into repository
- future task must not save compile log into repository
- future task must capture compile log semantic result to stdout only
- future task must prove compile_log_semantic_success=true
- future task must prove compile_log_errors=0
- future task must prove quarantine_ex5_artifact_detected=true
- future task must prove quarantine_ex5_artifact_count>=1
- future task must delete quarantine directory before completion
- future task must prove quarantine_deleted=true
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must not run MT5 terminal
- future task must not run Strategy Tester
- future task must not backtest
- future task must not trade
- future task must not create official manifest
- future task must not create evidence
- future task must not create report
- future task must not copy external evidence
- future success reclassification must remain compile-only and no-trade
- future success reclassification must not imply deployment readiness
- future success reclassification must not imply strategy readiness
- future success reclassification must not imply backtest readiness
- future success reclassification must not imply trading authorization

## Next Boundary

- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix
- TASK-310 must not be entered directly
