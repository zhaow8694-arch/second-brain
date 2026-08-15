# TASK-318 MT5 no-trade startup authorization planning boundary

TASK-318 is planning-only and authorization-boundary-only.

This packet defines future MT5 no-trade startup authorization conditions. It is
not an MT5 startup execution task.

## Boundary

- planning-only
- authorization-boundary-only
- mt5-no-trade-startup-authorization-plan
- not MT5 run in TASK-318
- not terminal64.exe execution in TASK-318
- not terminal.exe execution in TASK-318
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not MetaEditor execution in TASK-318
- not MQL5 compile in TASK-318
- no MT5 terminal run executed in TASK-318
- no terminal64.exe executed in TASK-318
- no terminal.exe executed in TASK-318
- no Strategy Tester executed in TASK-318
- no backtest executed in TASK-318
- no trading executed in TASK-318
- no MetaEditor executed in TASK-318
- no MQL5 compile executed in TASK-318
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no generated no-trade startup config in repository
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- Inventory only; no MT5 run; no trading authorization.

## Current State

- current HEAD: a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview
- current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary
- TASK-313 defined MT5 no-trade startup boundary
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-316 defined dry-run config boundary
- TASK-317 defined stdout-only config template preview
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Future TASK-319 Entry Conditions

- future TASK-319 must be separately authorized by GPT
- TASK-319 must not be entered directly
- future TASK-319 must re-check MQ5 inventory remains 7 files
- future TASK-319 must re-check Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-319 must prove no repo .ex5 artifact before any startup action
- future TASK-319 must prove no repo compile log before any startup action
- future TASK-319 must prove no terminal data directory in repository
- future TASK-319 must prove no startup log in repository unless separately authorized
- future TASK-319 must prove no generated no-trade startup config in repository unless separately authorized
- future TASK-319 must keep no-trade authorization false
- future TASK-319 must not run Strategy Tester
- future TASK-319 must not backtest
- future TASK-319 must not trade
- future TASK-319 must not create official manifest
- future TASK-319 must not create evidence
- future TASK-319 must not create report
