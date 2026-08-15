# TASK-300 MQL5 compile-only dry-run execution simulation

## Scope

- dry-run-execution-only
- artifact-quarantine enforced
- future compile-only task must be separately authorized by GPT
- stdout-only simulation
- current HEAD: 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary
- current tag: v0.5.96-task-298-mql5-compile-only-dryrun
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- TASK-301 must not be entered directly
- future compile-only execution must remain no-trade
- future compile-only execution must not create manifest / evidence / report unless separately authorized
- Inventory only; no MT5 run; no trading authorization.

## Boundary

TASK-300 simulates the future compile-only execution path as a stdout-only
candidate output. It validates that TASK-296 artifact quarantine and TASK-298
dry-run constraints are still in force before any future compile-only task can
be separately authorized by GPT.

This task does not execute MetaEditor, terminal64.exe, MT5, Strategy Tester,
MQL5 compile, backtest, simulation, or real trading. It does not generate .ex5
artifacts, compile logs, manifests, evidence, reports, fixtures, or directories.

## Candidate Output

- candidate_compile_command_generated=true
- candidate_compile_command_executed=false
- metaeditor_executed=false
- mql5_compile_executed=false
- mt5_run=false
- strategy_tester=false
- backtest=false
- trading_authorization=false
- ex5_artifact_generated=false
- compile_log_generated=false
- manifest_generated=false
- evidence_generated=false
- report_generated=false

## Exit Criteria

- mql5-compile-only-dryrun-execution PASS
- project-state-docs PASS
- project-state-docs-self-test PASS
- mq5-inventory PASS with MQ5 inventory remains 7 files
- trading keyword scan confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- git diff --check PASS
- tracked workspace changes stay inside the TASK-300 allowed files
