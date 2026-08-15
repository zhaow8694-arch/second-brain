# TASK-301 v0.6.0 compile-readiness planning packet

## Scope

- planning-only
- future compile-readiness candidate
- not implementation authorization
- not MT5 run
- not Strategy Tester run
- not backtest authorization
- not simulation / real trading authorization
- not evidence / manifest / report creation
- not MetaEditor execution
- not MQL5 compile execution
- no .ex5 artifact generated
- no compile log generated
- stdout-only / read-only planning validation

## Baseline

- current HEAD: fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation
- current tag: v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation
- MQ5 inventory 7 files
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade false
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.

## Boundary

- TASK-301 creates a v0.6.0 compile-readiness planning packet only.
- TASK-301 does not authorize implementation.
- TASK-301 does not authorize MT5 run, Strategy Tester run, backtest, simulation, real trading, or profitability optimization.
- TASK-301 does not authorize MQL5 compile, MetaEditor execution, .ex5 generation, compile log generation, manifest generation, evidence generation, or report generation.
- TASK-301 does not modify MQ5 / MQH.
- TASK-301 does not change authorization / trading / execution fields.
- TASK-302 must not be entered directly without GPT authorization.
- GPT must define a separate future boundary before TASK-302.

## Exit Criteria

- v060-compile-readiness-planning check is added to release validation bundle.
- fast-no-trade-dev profile includes v060-compile-readiness-planning check.
- workflow-closure-audit includes v060-compile-readiness-planning check.
- project-state-docs PASS.
- project-state-docs-self-test PASS.
- git diff --check PASS.
