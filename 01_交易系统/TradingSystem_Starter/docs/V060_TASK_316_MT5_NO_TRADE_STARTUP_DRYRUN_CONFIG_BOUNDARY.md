# TASK-316 MT5 no-trade startup dry-run config boundary

## Scope

- planning-only
- startup-dryrun-config-boundary-only
- not MT5 run in TASK-316
- not terminal64.exe execution in TASK-316
- not terminal.exe execution in TASK-316
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-316
- no terminal64.exe executed in TASK-316
- no terminal.exe executed in TASK-316
- no Strategy Tester executed in TASK-316
- no backtest executed in TASK-316
- no trading executed in TASK-316
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no no-trade config file generated in repository
- Inventory only; no MT5 run; no trading authorization.

## Baseline

- current HEAD: 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary
- current tag: v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Future TASK-317 Minimum Entry Conditions

- future TASK-317 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-317 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup attempt
- future startup must remain no-trade
- future startup must use isolated startup quarantine outside repository
- future startup must use no-trade config
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must prove no terminal data directory exists in repository before startup
- future startup must prove no startup log exists in repository before startup
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must not create official manifest unless separately authorized
- future startup must not create evidence unless separately authorized
- future startup must not create report unless separately authorized
- future startup must capture startup result stdout-only unless separately authorized
- future startup must clean up quarantine unless separately authorized
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
