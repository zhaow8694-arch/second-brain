# TASK-317 MT5 no-trade startup config template preview

## Scope

- stdout-only-config-template-preview
- no config file generated in TASK-317
- not MT5 run in TASK-317
- not terminal64.exe execution in TASK-317
- not terminal.exe execution in TASK-317
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-317
- no terminal64.exe executed in TASK-317
- no terminal.exe executed in TASK-317
- no Strategy Tester executed in TASK-317
- no backtest executed in TASK-317
- no trading executed in TASK-317
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no no-trade config file generated in repository
- Inventory only; no MT5 run; no trading authorization.

## Baseline

- current HEAD: a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary
- current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-316 defined dry-run config boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Stdout-Only Future Template Fields

- future terminal path placeholder
- future quarantine data path placeholder outside repository
- future no-trade config template
- InpEnableTrading=false
- no Strategy Tester
- no backtest
- no trading
- no official manifest
- no evidence
- no report
- stdout-only startup result unless separately authorized

## Future Boundary

- future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5
- TASK-318 must not be entered directly
