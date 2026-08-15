# TASK-DOC-294 future MQL5 compile-only boundary packet

## Boundary Type

- planning-only / boundary-only
- future MQL5 compile-only candidate
- not implementation authorization
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not evidence generation authorization
- not manifest generation authorization
- not external evidence copy authorization

## Baseline

- current HEAD: 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report
- current tag: v0.5.92-task-293-mq5-compile-readiness-final-summary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.

## TASK-DOC-294 Safety Boundary

- no compile executed in TASK-DOC-294
- no MetaEditor executed in TASK-DOC-294
- no .ex5 artifact generated
- no MT5 run
- no MQL5 compile
- no trading authorization
- no manifest / fixture / report / directory
- no external evidence
- no MQ5 / MQH modification
- TASK-DOC-294 only records the future compile-only boundary and validator entry point.

## Future Compile-Only Candidate

- future compile-only task must be separately authorized by GPT
- future compile-only task must remain no-trade
- future compile-only task must not create manifest / evidence / report
- future compile-only task must only produce stdout / terminal result unless separately authorized
- TASK-295 must not be entered directly without a new GPT boundary

## Minimal Future Scope

- allowed action: invoke compile-only command only if explicitly authorized later
- forbidden action: MT5 terminal run
- forbidden action: Strategy Tester
- forbidden action: backtest
- forbidden action: simulation / real trading
- forbidden action: copying external evidence
- forbidden action: creating official manifest
- forbidden action: modifying mq5 trading behavior

## Exit Criteria

- mql5-compile-only-boundary PASS
- mq5-compile-readiness-final-summary PASS
- project-state-docs PASS
- project-state-docs-self-test PASS
- mq5-inventory PASS
- mq5-no-trade-observability PASS
- git diff --check PASS
- no MT5 run, no MetaEditor execution, no MQL5 compile, no .ex5 artifact
