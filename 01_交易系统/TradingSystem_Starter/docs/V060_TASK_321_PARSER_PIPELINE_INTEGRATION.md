# TASK-321 Parser pipeline integration

- TASK-321 parser pipeline integration
- parser-pipeline-integration-only
- parser-manifest-integration
- planning-only
- not MT5 run in TASK-321
- not terminal64.exe execution in TASK-321
- not terminal.exe execution in TASK-321
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-321
- no terminal64.exe executed in TASK-321
- no terminal.exe executed in TASK-321
- no Strategy Tester executed in TASK-321
- no backtest executed in TASK-321
- no trading executed in TASK-321
- no manifest generated in repository during TASK-321
- no external evidence copied into repository
- no startup log generated in repository
- no terminal data directory created in repository
- Inventory only; no MT5 run; no trading authorization.
- TASK-319 completed
- TASK-319 completion commit is 5f0a697 TASK-319 implement MT5 no-trade startup preflight gate
- TASK-319 completion tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate
- future TASK-320 requires GPT boundary before any MT5 terminal startup attempt
- TASK-320 must not be entered directly
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false

## Scope

TASK-321 completes parser pipeline integration without MT5 execution:

- `tools/parse_mql5_compile_log.py`
- `tools/parse_backtest_set_params.py`
- `tools/parse_backtest_runtime_summary.py` JSON output
- `tools/run_evidence_parser_pipeline.py`
- `tools/validate_parser_manifest_integration.py`
- `tools/validate_backtest_set_params.py`
- `python/strategy_pipeline/` Phase 1 skeleton
- `docs/Strategy_Pipeline_Architecture_v0.md`

## Safety

- stdout-only parser outputs unless separately authorized
- no repository .ex5 artifacts
- no repository compile logs
- no MQ5 modification
- no backtest/sets modification
- no profitability optimization