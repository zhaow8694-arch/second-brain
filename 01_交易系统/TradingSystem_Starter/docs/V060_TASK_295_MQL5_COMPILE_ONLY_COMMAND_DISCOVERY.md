# TASK-295 MQL5 compile-only command discovery boundary

## Boundary Type

- command-discovery-only
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not trading authorization
- no MQL5 compile executed in TASK-295
- no MetaEditor executed in TASK-295
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.

## Baseline

- current HEAD: 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet
- current tag: v0.5.93-task-294-future-mql5-compile-only-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- TASK-DOC-294 boundary doc remains fixed and unmodified.

## Allowed Discovery

- Static check of common Windows MetaEditor candidate paths only.
- Static check of PATH candidates with shutil.which only.
- Candidate paths may be printed to stdout.
- Future compile-only command template may be printed to stdout.
- not executed status must be printed.
- no .ex5 generated status must be printed.

## Forbidden Actions

- Do not execute metaeditor64.exe.
- Do not execute metaeditor.exe.
- Do not execute any /compile command.
- Do not create compile log.
- Do not create .ex5 artifact.
- Do not run terminal64.exe.
- Do not run MT5.
- Do not run Strategy Tester.
- Do not run backtest, simulation trading, or real trading.
- Do not create manifest / fixture / report / directory.
- Do not create compile log / evidence log / screenshot / artifact.
- Do not copy external evidence.
- Do not modify MQ5 / MQH.
- Do not add MQ5 / MQH files.
- Do not introduce Buy / Sell / OrderSend / PositionOpen / CTrade.
- Do not set any authorization / trading / execution field to true.

## Future TASK-296 Boundary

- future TASK-296 must be separately authorized by GPT before any compile execution.
- TASK-296 must not be entered directly.
- future compile-only task must remain no-trade.
- future compile-only task must not create manifest / evidence / report unless separately authorized.
- future compile-only task must quarantine or prevent .ex5 artifact generation before compile execution is allowed.

## Exit Criteria

- mql5-compile-only-command-discovery PASS
- mql5-compile-only-boundary PASS
- mq5-compile-readiness-final-summary PASS
- mq5-static-compile-readiness PASS
- mq5-static-symbol-consistency PASS
- mq5-telemetry-aggregation PASS
- mq5-observability-helper-consistency PASS
- mq5-lifecycle-route-consistency PASS
- mq5-static-include-consistency PASS
- mq5-static-interface-consistency PASS
- mq5-no-trade-observability PASS
- mq5-inventory PASS
- project-state-docs PASS
- project-state-docs-self-test PASS
- git diff --check PASS
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- no MT5 run, no MetaEditor execution, no MQL5 compile, no .ex5 artifact, no compile log
