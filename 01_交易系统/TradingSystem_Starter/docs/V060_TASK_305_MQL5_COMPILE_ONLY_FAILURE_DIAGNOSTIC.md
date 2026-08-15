# TASK-305 MQL5 compile-only failure diagnostic capture

This document is a failure diagnostic boundary. It is not evidence, not a report, not a TASK-304 success result, and not compile success.

- diagnostic-only
- not compile success
- not TASK-304 success result
- compile_exit_code=1 was observed in TASK-304
- TASK-305 may re-run MetaEditor compile-only only against quarantine copy
- compile log must be stdout-only
- compile log must not be saved to repository
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no MT5 terminal run
- no Strategy Tester run
- no backtest
- no trading
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet
- current tag: v0.5.100-task-303-v060-compile-only-execution-authorization
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
- TASK-306 must not be entered directly
- future TASK-306 must be separately authorized by GPT before any MQ5 fixes or compile retry

## Diagnostic Scope

- TASK-305 is limited to stdout-only diagnostic capture for the prior TASK-304 compile_exit_code=1 outcome.
- TASK-305 does not create a TASK-304 success result document.
- TASK-305 does not create a TASK-304 success tag.
- TASK-305 does not copy quarantine logs into the repository.
- TASK-305 does not authorize MQ5 fixes, compile retry beyond this diagnostic boundary, MT5 terminal run, Strategy Tester, backtest, simulation trading, real trading, manifest generation, evidence generation, or report generation.

## Safety Exit Criteria

- diagnostic capture prints compile_exit_code to stdout.
- diagnostic capture prints compile_success=false when compile_exit_code is nonzero.
- diagnostic capture prints compile log excerpt between compile_log_excerpt_start and compile_log_excerpt_end when compile_exit_code is nonzero.
- quarantine directory is deleted after the diagnostic attempt.
- repository has no .ex5 artifacts.
- repository has no compile logs.
- repository MQ5 / MQH files remain unmodified.
- MQ5 inventory remains 7 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.
