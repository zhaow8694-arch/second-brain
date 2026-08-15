# TASK-302 MQL5 compile-only execution preflight gate

## Scope

- preflight-gate-only
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not trading authorization
- no MQL5 compile executed in TASK-302
- no MetaEditor executed in TASK-302
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.

## Baseline

- current HEAD: 2f0498b TASK-301 create v060 compile-readiness planning packet
- current tag: v0.5.98-task-301-v060-compile-readiness-planning
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Preflight Gate

- all previous compile-only boundary checks must pass before future compile execution
- artifact quarantine must pass before future compile execution
- future compile-only command must remain stdout-only unless GPT separately authorizes artifact handling
- future TASK-303 must be separately authorized by GPT before any compile execution
- TASK-303 must not be entered directly
- future compile execution remains unauthorized in TASK-302
- compile_execution_authorized=false
- metaeditor_executed=false
- mql5_compile_executed=false
- mt5_run=false
- trading_authorization=false
- ex5_artifact_generated=false
- compile_log_generated=false
- repo_ex5_artifacts=false
- repo_compile_logs=false

## Future TASK-303 Minimum Conditions

- preflight check: mql5-compile-only-boundary PASS
- preflight check: mql5-compile-only-command-discovery PASS
- preflight check: mql5-compile-only-artifact-quarantine PASS
- preflight check: mql5-compile-only-execution-boundary PASS
- preflight check: mql5-compile-only-dryrun PASS
- preflight check: mql5-compile-only-dryrun-execution PASS
- preflight check: v060-compile-readiness-planning PASS
- preflight check: MQ5 inventory 7 files
- preflight check: trading keywords false
- preflight check: repo_ex5_artifacts=false
- preflight check: repo_compile_logs=false
- post-compile requirement: no MT5 run
- post-compile requirement: no Strategy Tester
- post-compile requirement: no trading
- post-compile requirement: no manifest/evidence/report unless separately authorized

## Exit Criteria

- mql5-compile-only-preflight-gate PASS
- fast-no-trade-dev profile includes mql5-compile-only-preflight-gate
- workflow-closure-audit includes mql5-compile-only-preflight-gate
- project-state-docs PASS
- project-state-docs-self-test PASS
- git diff --check PASS
