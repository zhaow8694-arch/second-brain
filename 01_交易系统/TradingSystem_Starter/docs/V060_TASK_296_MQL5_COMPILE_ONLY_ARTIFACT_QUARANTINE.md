# TASK-296 MQL5 compile-only artifact quarantine boundary

## Scope

- artifact-quarantine-only
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not trading authorization
- no MQL5 compile executed in TASK-296
- no MetaEditor executed in TASK-296
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.

## Baseline

- current HEAD: acda17c TASK-295 implement MQL5 compile-only command discovery boundary
- current tag: v0.5.94-task-295-mql5-compile-only-command-discovery
- MetaEditor candidate discovered in TASK-295
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Future TASK-297 Boundary

- future TASK-297 must be separately authorized by GPT before any compile execution
- TASK-297 must not be entered directly
- future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes
- future compile-only execution must check repository has no .ex5 before and after compile
- future compile-only execution must check repository has no compile log before and after compile
- future compile-only execution must not create official manifest / evidence / report
- future compile-only execution must remain no-trade

## Minimum TASK-297 Safety Requirements

- pre-compile check: no .ex5 in repository
- pre-compile check: no compile log in repository
- pre-compile check: MQ5 inventory 7 files
- pre-compile check: trading keywords false
- compile-only command may be executed only after GPT defines TASK-297 boundary
- post-compile check: no .ex5 in repository unless separately authorized
- post-compile check: no compile log in repository unless separately authorized
- post-compile check: no MT5 run
- post-compile check: no Strategy Tester
- post-compile check: no trading
