# TASK-311 MQL5 compile success reclassification decision boundary

## Boundary

- planning-only
- success-reclassification-decision-boundary-only
- not compile execution
- not MetaEditor execution in TASK-311
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-311
- TASK-311 does not store artifact hash
- TASK-311 does not create TASK-304 success result doc

## TASK-310 Observed State

- TASK-310 observed artifact_hash_captured=true
- TASK-310 observed quarantine_ex5_artifact_size_bytes=70178
- TASK-310 observed compile_exit_code=1
- TASK-310 observed compile_log_semantic_success=true
- TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly
- TASK-310 compile_success=false
- TASK-310 success_reclassification_done=false
- TASK-310 task304_success_result_created=false
- TASK-310 repo_ex5_artifacts=false
- TASK-310 repo_compile_logs=false
- TASK-310 repo_mq5_modified=false
- TASK-310 artifact hash was stdout-only and must not be stored in repository

## Repository Safety State

- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic
- current tag: v0.5.106-task-310-mql5-compile-artifact-hash-capture
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Future Decision Minimum Conditions

- future GPT boundary explicitly authorizes success reclassification decision
- future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash
- future task must not store artifact hash in repository unless GPT explicitly authorizes hash recording
- future task must keep artifact metadata stdout-only unless separately authorized
- future task must prove compile_log_semantic_success=true
- future task must prove compile_log_errors=0
- future task must prove quarantine_ex5_artifact_detected=true
- future task must prove quarantine_ex5_artifact_count>=1
- future task must prove quarantine artifact hash is captured
- future task must prove quarantine artifact size is captured
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
- future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry
- TASK-312 must not be entered directly
