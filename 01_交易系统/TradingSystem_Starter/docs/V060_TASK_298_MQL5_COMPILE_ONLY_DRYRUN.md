# TASK-298 MQL5 compile-only dry-run simulation

## Boundary

- dry-run-only
- artifact-quarantine enforced
- future compile-only task must be separately authorized by GPT
- stdout-only simulation
- current HEAD: 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary
- current tag: v0.5.95-task-296-mql5-compile-only-artifact-quarantine
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- TASK-299 must not be entered directly
- Inventory only; no MT5 run; no trading authorization.

## Dry-Run Guard

- TASK-298 simulates the MetaEditor compile-only execution flow as stdout-only validation.
- TASK-298 does not execute MetaEditor.
- TASK-298 does not execute MQL5 compile.
- TASK-298 does not start terminal64.exe.
- TASK-298 does not run MT5.
- TASK-298 does not generate .ex5 artifacts.
- TASK-298 does not generate compile logs.
- TASK-298 does not generate manifest / evidence / report outputs.
- TASK-298 does not modify MQ5 / MQH files.
- TASK-298 does not change authorization / trading / execution fields.

## Future Authorization

- Future compile-only task must be separately authorized by GPT before any real compile command.
- Future TASK-299 must not be entered directly.
- Future TASK-299 must remain no-trade and preserve artifact quarantine unless GPT defines a separate boundary.
