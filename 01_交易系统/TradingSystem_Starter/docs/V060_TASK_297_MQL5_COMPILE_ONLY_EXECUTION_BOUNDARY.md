# TASK-297 MQL5 compile-only execution boundary

## Boundary

- compile-only-task
- future compile-only candidate
- requires GPT explicit authorization
- artifact quarantine checked
- no MT5 run
- no Strategy Tester
- no backtest
- no trading
- no MQL5 compile executed
- no MetaEditor executed
- no .ex5 artifact generated
- no compile log
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary
- current tag: v0.5.95-task-296-mql5-compile-only-artifact-quarantine
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-298 must be separately authorized by GPT
- future TASK-298 must not be entered directly

## Non-Execution Guard

- TASK-297 defines a future compile-only execution boundary only.
- TASK-297 does not execute MQL5 compile.
- TASK-297 does not execute MetaEditor.
- TASK-297 does not start terminal64.exe.
- TASK-297 does not run MT5.
- TASK-297 does not run Strategy Tester.
- TASK-297 does not run backtest / simulation / real trading.
- TASK-297 does not generate .ex5 artifacts.
- TASK-297 does not generate compile logs.
- TASK-297 does not generate manifest / evidence / report outputs.
- TASK-297 does not modify MQ5 / MQH files.

## Future Authorization

- Future TASK-298 must be separately authorized by GPT before any compile-only command can be executed.
- Future TASK-298 must prove artifact quarantine before and after any authorized compile-only action.
- Future TASK-298 must remain no-trade unless GPT defines a separate boundary.
