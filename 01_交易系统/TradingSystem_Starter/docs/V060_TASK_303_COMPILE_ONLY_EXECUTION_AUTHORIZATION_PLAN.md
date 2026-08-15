# TASK-303 v0.6.0 compile-only execution authorization planning packet

## Scope

- planning-only
- authorization-boundary-only
- future compile-only execution candidate
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not manifest generation authorization
- not evidence generation authorization
- not report generation authorization
- no MQL5 compile executed in TASK-303
- no MetaEditor executed in TASK-303
- no MT5 run in TASK-303
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.

## Baseline

- current HEAD: 15c675e TASK-302 implement MQL5 compile-only execution preflight gate
- current tag: v0.5.99-task-302-mql5-compile-only-preflight-gate
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Future Authorization Boundary

- TASK-304 must not be entered directly
- future TASK-304 must be separately authorized by GPT before any compile execution
- compile-only execution authorization requires all preflight gates PASS
- compile-only execution authorization must remain no-trade
- compile-only execution authorization must not run MT5 terminal
- compile-only execution authorization must not run Strategy Tester
- compile-only execution authorization must not create official manifest
- compile-only execution authorization must not copy external evidence
- compile-only execution authorization must include pre/post repo artifact checks
- compile-only execution authorization must check repo_ex5_artifacts=false before execution
- compile-only execution authorization must check repo_compile_logs=false before execution
- compile-only execution authorization must check trading_keywords=false before execution
- compile-only execution authorization must check MQ5 inventory remains 7 files before execution

## Future TASK-304 Minimum Entry Conditions

- mql5-compile-only-boundary PASS
- mql5-compile-only-command-discovery PASS
- mql5-compile-only-artifact-quarantine PASS
- mql5-compile-only-execution-boundary PASS
- mql5-compile-only-dryrun PASS
- mql5-compile-only-dryrun-execution PASS
- mql5-compile-only-preflight-gate PASS
- v060-compile-readiness-planning PASS
- mq5-static-compile-readiness PASS
- mq5-compile-readiness-final-summary PASS
- MQ5 inventory 7 files
- trading keywords false
- repo_ex5_artifacts=false
- repo_compile_logs=false
- future GPT boundary explicitly says compile execution is allowed
