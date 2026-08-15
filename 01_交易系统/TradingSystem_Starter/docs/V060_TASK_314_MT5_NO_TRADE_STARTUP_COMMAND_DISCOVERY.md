# TASK-314 MT5 no-trade startup command discovery boundary

- command-discovery-only
- mt5-startup-preparation-only
- not MT5 run in TASK-314
- not terminal64.exe execution in TASK-314
- not terminal.exe execution in TASK-314
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-314
- no Strategy Tester executed in TASK-314
- no backtest executed in TASK-314
- no trading executed in TASK-314
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet
- current tag: v0.5.109-task-313-mt5-no-trade-startup-boundary
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-315 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-315 must not be entered directly

## Discovery Scope

- TASK-314 may statically check common Windows MT5 terminal candidate paths.
- TASK-314 may use pathlib / os.path.exists / shutil.which for discovery.
- TASK-314 must output future no-trade startup command template to stdout only.
- TASK-314 must not execute discovered terminal candidates.
- future_startup_command_executed=false

## Future TASK-315 Minimum Entry Conditions

- future GPT boundary explicitly authorizes MT5 terminal no-trade startup
- future startup must remain no-trade
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must not create official manifest unless separately authorized
- future startup must not create evidence unless separately authorized
- future startup must not create report unless separately authorized
- future startup must use no-trade startup template
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must capture startup result stdout-only unless separately authorized
- future startup must not copy external evidence
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
