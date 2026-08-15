#!/usr/bin/env python3
"""CLI self-test for the current project state docs validator."""

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_project_state_docs.py"

DEFAULT_COMMIT = "e6f3555 TASK-DOC-115 update state after TASK-TAG-016"
DEFAULT_FUNCTIONAL_TASK = (
    "951bfe2 TASK-072 verify v0.2.0 Python tool safety coverage"
)
DEFAULT_BOUNDARY_LINES = [
    "当前下一步任务未定。",
    "不要直接进入 TASK-311。",
    "不要直接进入 v0.6.0。",
    "不要直接修改 MQ5。",
    "不要直接修改 backtest/sets。",
    "不要直接进入真实交易。",
    "必须先由 ChatGPT 制定下一任务边界。",
]

DEFAULT_PLAN_TEXT = """# V060 First Low-Risk Implementation Plan

- planning-only
- not implementation authorization
- no MQ5 modification
- no MT5 run
- no trading authorization
- TASK-238 v0.6.0 no-trade observability scaffold
- Buy / Sell / OrderSend / PositionOpen / CTrade
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK238_BOUNDARY_TEXT = """# V060 TASK-238 No-Trade Scaffold Boundary

- planning-only
- no-trade scaffold
- future candidate
- TASK-238
- Buy / Sell / OrderSend / PositionOpen / CTrade 均 false
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK239_BOUNDARY_TEXT = """# V060 TASK-239 First Implementation Slice Boundary

- first authorized low-risk implementation slice
- planning + boundary only
- InpEnableTrading false
- Buy / Sell / OrderSend / PositionOpen / CTrade 鍧?false
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK260_OBSERVABILITY_EXTENSION_PLAN_TEXT = """# V060 TASK-260 First Observability Extension Plan

- planning-only
- future candidate
- no-trade observability extension
- not implementation authorization
- no MQ5 modification in TASK-DOC-260
- no MT5 run
- no trading authorization
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 6451e78 TASK-259 implement read-only decision rejection reason snapshot contract
- current tag: v0.5.61-task-259-read-only-decision-rejection-reason
- MQ5 inventory remains 7 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.
- TASK-261 must not be entered directly; GPT must define a separate future task boundary.
"""

DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT = """# V060 TASK-261 Observability Extension Next Plan

- planning-only
- future candidate
- no-trade observability extension
- no-trade scaffold
- not implementation authorization
- no MQ5 modification in TASK-DOC-261
- no MT5 run
- no trading authorization
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: cb7675f TASK-DOC-260 create first observability extension planning packet
- current tag: v0.5.62-task-260-first-observability-extension-plan
- MQ5 inventory remains 7 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.
- TASK-262 must not be entered directly.
- GPT must define a separate future boundary before TASK-262.
"""

DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT = """# V060 TASK-262 Observability Extension Follow-up Plan

- planning-only
- future candidate
- no-trade observability extension
- no-trade scaffold
- not implementation authorization
- no MQ5 modification in TASK-DOC-262
- no MT5 run
- no trading authorization
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 527486d TASK-DOC-261 create next observability extension planning packet
- current tag: v0.5.63-task-261-observability-extension-next-plan
- MQ5 inventory remains 7 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.
- TASK-263 must not be entered directly.
- GPT must define a separate future boundary before TASK-263.
"""

DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT = """# V060 TASK-263 Observability Extension Future Plan

- planning-only
- future candidate
- no-trade observability extension
- no-trade scaffold
- not implementation authorization
- no MQ5 modification in TASK-DOC-263
- no MT5 run
- no trading authorization
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 69f12a6 TASK-DOC-262 create follow-up observability extension planning packet
- current tag: v0.5.64-task-262-observability-extension-followup-plan
- MQ5 inventory remains 7 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.
- TASK-264 must not be entered directly.
- GPT must define a separate future boundary before TASK-264.
"""

DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT = """# TASK-DOC-294 future MQL5 compile-only boundary packet

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
- no compile executed in TASK-DOC-294
- no MetaEditor executed in TASK-DOC-294
- no .ex5 artifact generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report
- current tag: v0.5.92-task-293-mq5-compile-readiness-final-summary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future compile-only task must be separately authorized by GPT
- future compile-only task must remain no-trade
- future compile-only task must not create manifest / evidence / report
- future compile-only task must only produce stdout / terminal result unless separately authorized
- TASK-295 must not be entered directly without a new GPT boundary
- allowed action: invoke compile-only command only if explicitly authorized later
- forbidden action: MT5 terminal run
- forbidden action: Strategy Tester
- forbidden action: backtest
- forbidden action: simulation / real trading
- forbidden action: copying external evidence
- forbidden action: creating official manifest
- forbidden action: modifying mq5 trading behavior
"""

DEFAULT_TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_TEXT = """# TASK-295 MQL5 compile-only command discovery boundary

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
- current HEAD: 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet
- current tag: v0.5.93-task-294-future-mql5-compile-only-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-296 must be separately authorized by GPT before any compile execution
- TASK-296 must not be entered directly
- future compile-only task must remain no-trade
- future compile-only task must not create manifest / evidence / report unless separately authorized
- future compile-only task must quarantine or prevent .ex5 artifact generation before compile execution is allowed
"""

DEFAULT_TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_TEXT = """# TASK-296 MQL5 compile-only artifact quarantine boundary

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
- current HEAD: acda17c TASK-295 implement MQL5 compile-only command discovery boundary
- current tag: v0.5.94-task-295-mql5-compile-only-command-discovery
- MetaEditor candidate discovered in TASK-295
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-297 must be separately authorized by GPT before any compile execution
- TASK-297 must not be entered directly
- future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes
- future compile-only execution must check repository has no .ex5 before and after compile
- future compile-only execution must check repository has no compile log before and after compile
- future compile-only execution must not create official manifest / evidence / report
- future compile-only execution must remain no-trade
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
"""

DEFAULT_TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_TEXT = """# TASK-297 MQL5 compile-only execution boundary

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
"""

DEFAULT_TASK298_MQL5_COMPILE_ONLY_DRYRUN_TEXT = """# TASK-298 MQL5 compile-only dry-run simulation

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
"""

DEFAULT_TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_TEXT = """# TASK-300 MQL5 compile-only dry-run execution simulation

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
"""

DEFAULT_TASK301_V060_COMPILE_READINESS_PLANNING_TEXT = """# TASK-301 v0.6.0 compile-readiness planning packet

- planning-only
- future compile-readiness candidate
- not implementation authorization
- not MT5 run
- not Strategy Tester run
- not backtest authorization
- not simulation / real trading authorization
- not evidence / manifest / report creation
- current HEAD: fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation
- current tag: v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation
- MQ5 inventory 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade false
- TASK-302 must not be entered directly without GPT authorization
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT = """# TASK-302 MQL5 compile-only execution preflight gate

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
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 2f0498b TASK-301 create v060 compile-readiness planning packet
- current tag: v0.5.98-task-301-v060-compile-readiness-planning
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- all previous compile-only boundary checks must pass before future compile execution
- artifact quarantine must pass before future compile execution
- future compile-only command must remain stdout-only unless GPT separately authorizes artifact handling
- future TASK-303 must be separately authorized by GPT before any compile execution
- TASK-303 must not be entered directly
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
"""

DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT = """# TASK-303 v0.6.0 compile-only execution authorization planning packet

- planning-only
- authorization-boundary-only
- future compile-only execution candidate
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not manifest generation authorization
- not evidence generation authorization
- not report generation authorization
- no MQL5 compile executed in TASK-303
- no MetaEditor executed in TASK-303
- no MT5 run in TASK-303
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 15c675e TASK-302 implement MQL5 compile-only execution preflight gate
- current tag: v0.5.99-task-302-mql5-compile-only-preflight-gate
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- TASK-304 must not be entered directly
- future TASK-304 must be separately authorized by GPT before any compile execution
- compile-only execution authorization requires all preflight gates PASS
- compile-only execution authorization must remain no-trade
- compile-only execution authorization must not run MT5 terminal
- compile-only execution authorization must not run Strategy Tester
- compile-only execution authorization must not create official manifest
- compile-only execution authorization must not copy external evidence
- compile-only execution authorization must include pre/post repo artifact checks
- compile-only execution authorization must check repo_ex5_artifacts=false before execution
- compile-only execution authorization must check repo_compile_logs=false before execution
- compile-only execution authorization must check trading_keywords=false before execution
- compile-only execution authorization must check MQ5 inventory remains 7 files before execution
- mql5-compile-only-boundary PASS
- mql5-compile-only-command-discovery PASS
- mql5-compile-only-artifact-quarantine PASS
- mql5-compile-only-execution-boundary PASS
- mql5-compile-only-dryrun PASS
- mql5-compile-only-dryrun-execution PASS
- mql5-compile-only-preflight-gate PASS
- v060-compile-readiness-planning PASS
- mq5-static-compile-readiness PASS
- mq5-compile-readiness-final-summary PASS
- MQ5 inventory 7 files
- trading keywords false
- repo_ex5_artifacts=false
- repo_compile_logs=false
- future GPT boundary explicitly says compile execution is allowed
"""

DEFAULT_TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_TEXT = """# TASK-305 MQL5 compile-only failure diagnostic capture

- diagnostic-only
- not compile success
- not TASK-304 success result
- compile_exit_code=1 was observed in TASK-304
- TASK-305 may re-run MetaEditor compile-only only against quarantine copy
- compile log must be stdout-only
- compile log must not be saved to repository
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no MT5 terminal run
- no Strategy Tester run
- no backtest
- no trading
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet
- current tag: v0.5.100-task-303-v060-compile-only-execution-authorization
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
- TASK-306 must not be entered directly
- future TASK-306 must be separately authorized by GPT before any MQ5 fixes or compile retry
"""

DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT = """# TASK-306 MQL5 compile-only diagnostic result classification

- diagnostic-classification-only
- not compile execution
- not MetaEditor execution in TASK-306
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- compile_exit_code=1 observed in TASK-305
- compile log excerpt indicated Result: 0 errors, 0 warnings
- compile_result_classification=metaeditor_exit_code_anomaly
- compile_log_semantic_success=true
- compile_success=false
- task304_success_result_created=false
- followup_required=true
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture
- current tag: v0.5.101-task-305-mql5-compile-only-failure-diagnostic
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
- future TASK-307 must be separately authorized by GPT before any compile retry or MQ5 fix
- TASK-307 must not be entered directly
"""

DEFAULT_TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_TEXT = """# TASK-307 MQL5 compile diagnostic artifact classification

- diagnostic-artifact-classification-only
- not TASK-304 success result
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- TASK-307 may re-run MetaEditor compile-only only against quarantine copy
- quarantine artifact inspection before cleanup
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- task304_success_result_created=false
- compile_success=false unless a future GPT boundary explicitly reclassifies success
- current HEAD: 560079c TASK-306 implement MQL5 compile-only diagnostic result classification
- current tag: v0.5.102-task-306-mql5-compile-diagnostic-classification
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
- future TASK-308 must be separately authorized by GPT before any compile retry or MQ5 fix
- TASK-308 must not be entered directly
"""

DEFAULT_TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_TEXT = """# TASK-308 MQL5 compile diagnostic artifact proof and success reclassification boundary

- planning-only
- diagnostic-proof-boundary-only
- not compile execution
- not MetaEditor execution in TASK-308
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-308
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-307 compile_success=false
- TASK-307 task304_success_result_created=false
- TASK-308 does not create TASK-304 success result doc
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification
- current tag: v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification
- TASK-309 must not be entered directly
- future GPT boundary explicitly authorizes success reclassification attempt
- future task may re-run MetaEditor compile-only only against quarantine copy
- future task must capture quarantine .ex5 metadata before deletion
- future task must output artifact metadata to stdout only
- future task must not copy .ex5 into repository
- future task must not save compile log into repository
- future task must compute quarantine artifact hash before deleting quarantine directory
- future task must output quarantine artifact size
- future task must output quarantine artifact path as temporary path only
- future task must delete quarantine directory before completion
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must still not run MT5 terminal
- future task must still not run Strategy Tester
- future task must still not trade
- future task must not create official manifest / evidence / report unless separately authorized
"""

DEFAULT_TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_TEXT = """# TASK-309 MQL5 compile-only success reclassification boundary

- planning-only
- success-reclassification-boundary-only
- not compile execution
- not MetaEditor execution in TASK-309
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-309
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed quarantine_ex5_artifact_count=1
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-307 compile_success=false
- TASK-307 task304_success_result_created=false
- TASK-308 defined diagnostic artifact proof boundary
- TASK-309 does not create TASK-304 success result doc
- TASK-309 does not reclassify compile success
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary
- current tag: v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix
- TASK-310 must not be entered directly
- future GPT boundary explicitly authorizes success reclassification attempt
- future task may re-run MetaEditor compile-only only against quarantine copy
- future task must capture quarantine .ex5 metadata before deletion
- future task must compute quarantine artifact hash before deleting quarantine directory
- future task must output quarantine artifact hash to stdout only
- future task must output quarantine artifact size
- future task must output quarantine artifact temporary path only
- future task must not copy .ex5 into repository
- future task must not save compile log into repository
- future task must capture compile log semantic result to stdout only
- future task must prove compile_log_semantic_success=true
- future task must prove compile_log_errors=0
- future task must prove quarantine_ex5_artifact_detected=true
- future task must prove quarantine_ex5_artifact_count>=1
- future task must delete quarantine directory before completion
- future task must prove quarantine_deleted=true
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must not run MT5 terminal
- future task must not run Strategy Tester
- future task must not backtest
- future task must not trade
- future task must not create official manifest
- future task must not create evidence
- future task must not create report
- future task must not copy external evidence
- future success reclassification must remain compile-only and no-trade
- future success reclassification must not imply deployment readiness
- future success reclassification must not imply strategy readiness
- future success reclassification must not imply backtest readiness
- future success reclassification must not imply trading authorization
"""

DEFAULT_TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_TEXT = """# TASK-310 MQL5 compile artifact hash capture diagnostic

- artifact-hash-capture-diagnostic-only
- not success reclassification
- not TASK-304 success result
- TASK-310 may re-run MetaEditor compile-only only against quarantine copy
- artifact hash must be stdout-only
- artifact hash must not be saved to repository
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- success_reclassification_done=false
- task304_success_result_created=false
- compile_success=false
- future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix
- TASK-311 must not be entered directly
- no MT5 terminal run
- no Strategy Tester run
- no backtest
- no trading
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: f31b85e TASK-309 create MQL5 compile-only success reclassification boundary
- current tag: v0.5.105-task-309-mql5-compile-success-reclassification-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT = """# TASK-311 MQL5 compile success reclassification decision boundary

- planning-only
- success-reclassification-decision-boundary-only
- not compile execution
- not MetaEditor execution in TASK-311
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-311
- TASK-310 observed artifact_hash_captured=true
- TASK-310 observed quarantine_ex5_artifact_size_bytes=70178
- TASK-310 observed compile_exit_code=1
- TASK-310 observed compile_log_semantic_success=true
- TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly
- TASK-310 compile_success=false
- TASK-310 success_reclassification_done=false
- TASK-310 task304_success_result_created=false
- TASK-310 repo_ex5_artifacts=false
- TASK-310 repo_compile_logs=false
- TASK-310 repo_mq5_modified=false
- TASK-310 artifact hash was stdout-only and must not be stored in repository
- TASK-311 does not store artifact hash
- TASK-311 does not create TASK-304 success result doc
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic
- current tag: v0.5.106-task-310-mql5-compile-artifact-hash-capture
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry
- TASK-312 must not be entered directly
- future GPT boundary explicitly authorizes success reclassification decision
- future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash
- future task must not store artifact hash in repository unless GPT explicitly authorizes hash recording
- future task must keep artifact metadata stdout-only unless separately authorized
- future task must prove compile_log_semantic_success=true
- future task must prove compile_log_errors=0
- future task must prove quarantine_ex5_artifact_detected=true
- future task must prove quarantine_ex5_artifact_count>=1
- future task must prove quarantine artifact hash is captured
- future task must prove quarantine artifact size is captured
- future task must delete quarantine directory before completion
- future task must prove quarantine_deleted=true
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must not run MT5 terminal
- future task must not run Strategy Tester
- future task must not backtest
- future task must not trade
- future task must not create official manifest
- future task must not create evidence
- future task must not create report
- future task must not copy external evidence
- future success reclassification must remain compile-only and no-trade
- future success reclassification must not imply deployment readiness
- future success reclassification must not imply strategy readiness
- future success reclassification must not imply backtest readiness
- future success reclassification must not imply trading authorization
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT = """# TASK-312 MQL5 compile-only success reclassification decision

- controlled-success-reclassification-attempt
- success_reclassification_decision=PASS
- compile_only_reclassified_success=true
- compile_success=true
- compile_success_scope=compile-only-diagnostic
- not trading authorization
- not deployment readiness
- not backtest readiness
- not strategy readiness
- MetaEditor executed only against quarantine copy
- MQL5 compile executed only against quarantine copy
- MT5 terminal run=false
- Strategy Tester run=false
- trading_executed=false
- quarantine_ex5_artifact_detected=true
- quarantine_ex5_artifact_count>=1
- artifact_hash_captured=true
- artifact_hash_stdout_only=true
- artifact_hash_saved_to_repo=false
- do not include actual artifact hash value in this doc
- quarantine_ex5_artifact_size_bytes captured
- quarantine_deleted=true
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary
- current tag: v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-313 must be separately authorized by GPT before any MT5 run, Strategy Tester, backtest, deployment, or trading-related step
- TASK-313 must not be entered directly
"""

DEFAULT_TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_TEXT = """# TASK-313 MT5 terminal no-trade startup boundary packet

- planning-only
- mt5-startup-boundary-only
- future MT5 terminal no-trade startup candidate
- not MT5 run in TASK-313
- not terminal64.exe execution in TASK-313
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- not evidence generation authorization
- not manifest generation authorization
- not report generation authorization
- no MT5 terminal run executed in TASK-313
- no Strategy Tester executed in TASK-313
- no backtest executed in TASK-313
- no trading executed in TASK-313
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision
- current tag: v0.5.108-task-312-mql5-compile-success-reclassification-decision
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-314 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup
- future task must remain no-trade
- future task must not run Strategy Tester
- future task must not run backtest
- future task must not run simulation trading
- future task must not run real trading
- future task must not place orders
- future task must not create official manifest unless separately authorized
- future task must not create evidence unless separately authorized
- future task must not create report unless separately authorized
- future task must use a no-trade config
- future task must prove InpEnableTrading=false before startup
- future task must prove trading keywords false before startup
- future task must prove MQ5 inventory remains 7 files before startup
- future task must prove repo_ex5_artifacts=false before startup
- future task must prove repo_compile_logs=false before startup
- future task must prove repo_mq5_modified=false before startup
- future task must capture terminal startup result stdout-only unless separately authorized
- future task must not copy external evidence
- future task must not imply deployment readiness
- future task must not imply strategy readiness
- future task must not imply backtest readiness
- future task must not imply trading authorization
"""

DEFAULT_TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_TEXT = """# TASK-314 MT5 no-trade startup command discovery boundary

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
"""

DEFAULT_TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_TEXT = """# TASK-315 MT5 no-trade startup quarantine preparation boundary

- planning-only
- startup-quarantine-preparation-only
- not MT5 run in TASK-315
- not terminal64.exe execution in TASK-315
- not terminal.exe execution in TASK-315
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-315
- no terminal64.exe executed in TASK-315
- no terminal.exe executed in TASK-315
- no Strategy Tester executed in TASK-315
- no backtest executed in TASK-315
- no trading executed in TASK-315
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary
- current tag: v0.5.110-task-314-mt5-no-trade-startup-command-discovery
- TASK-314 discovered MT5 terminal candidate
- TASK-314 future_startup_command_executed=false
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-316 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-316 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup attempt
- future startup must remain no-trade
- future startup must use an isolated startup quarantine outside repository
- future startup must not use repository as terminal data directory
- future startup must not write terminal logs into repository
- future startup must not create evidence / manifest / report unless separately authorized
- future startup must not copy external evidence
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must not attach EA to live trading chart unless separately authorized
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must prove no terminal data directory exists in repository before startup
- future startup must prove no startup log exists in repository before startup
- future startup must capture startup result stdout-only unless separately authorized
- future startup must clean up quarantine unless separately authorized
- future startup must prove repo_ex5_artifacts=false after startup
- future startup must prove repo_compile_logs=false after startup
- future startup must prove repo_mq5_modified=false after startup
- future startup must prove trading_keywords=false after startup
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
"""

DEFAULT_TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_TEXT = """# TASK-316 MT5 no-trade startup dry-run config boundary

- planning-only
- startup-dryrun-config-boundary-only
- not MT5 run in TASK-316
- not terminal64.exe execution in TASK-316
- not terminal.exe execution in TASK-316
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-316
- no terminal64.exe executed in TASK-316
- no terminal.exe executed in TASK-316
- no Strategy Tester executed in TASK-316
- no backtest executed in TASK-316
- no trading executed in TASK-316
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no no-trade config file generated in repository
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary
- current tag: v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-317 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-317 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup attempt
- future startup must remain no-trade
- future startup must use isolated startup quarantine outside repository
- future startup must use no-trade config
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must prove no terminal data directory exists in repository before startup
- future startup must prove no startup log exists in repository before startup
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must not create official manifest unless separately authorized
- future startup must not create evidence unless separately authorized
- future startup must not create report unless separately authorized
- future startup must capture startup result stdout-only unless separately authorized
- future startup must clean up quarantine unless separately authorized
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
"""

DEFAULT_TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_TEXT = """# TASK-317 MT5 no-trade startup config template preview

- stdout-only-config-template-preview
- no config file generated in TASK-317
- not MT5 run in TASK-317
- not terminal64.exe execution in TASK-317
- not terminal.exe execution in TASK-317
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-317
- no terminal64.exe executed in TASK-317
- no terminal.exe executed in TASK-317
- no Strategy Tester executed in TASK-317
- no backtest executed in TASK-317
- no trading executed in TASK-317
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no no-trade config file generated in repository
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary
- current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-316 defined dry-run config boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5
- TASK-318 must not be entered directly
- future terminal path placeholder
- future quarantine data path placeholder outside repository
- future no-trade config template
- InpEnableTrading=false
- no Strategy Tester
- no backtest
- no trading
- no official manifest
- no evidence
- no report
- stdout-only startup result unless separately authorized
"""

DEFAULT_TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_TEXT = """# TASK-318 MT5 no-trade startup authorization planning boundary

- planning-only
- authorization-boundary-only
- mt5-no-trade-startup-authorization-plan
- not MT5 run in TASK-318
- not terminal64.exe execution in TASK-318
- not terminal.exe execution in TASK-318
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not MetaEditor execution in TASK-318
- not MQL5 compile in TASK-318
- no MT5 terminal run executed in TASK-318
- no terminal64.exe executed in TASK-318
- no terminal.exe executed in TASK-318
- no Strategy Tester executed in TASK-318
- no backtest executed in TASK-318
- no trading executed in TASK-318
- no MetaEditor executed in TASK-318
- no MQL5 compile executed in TASK-318
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no generated no-trade startup config in repository
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- current HEAD: a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview
- current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary
- TASK-317 defined stdout-only config template preview
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-319 must be separately authorized by GPT
- TASK-319 must not be entered directly
- Inventory only; no MT5 run; no trading authorization.
"""

DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT = """# TASK-319 MT5 no-trade startup preflight gate

- planning-only
- startup-preflight-gate-only
- mt5-no-trade-startup-preflight-gate
- not MT5 run in TASK-319
- not terminal64.exe execution in TASK-319
- not terminal.exe execution in TASK-319
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-319
- no terminal64.exe executed in TASK-319
- no terminal.exe executed in TASK-319
- no Strategy Tester executed in TASK-319
- no backtest executed in TASK-319
- no trading executed in TASK-319
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no no-trade config file generated in repository
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 718c7cf TASK-317-318 implement MT5 no-trade startup config template and authorization boundaries
- current tag: v0.5.113-task-317-318-mt5-no-trade-startup-config-auth-boundaries
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-316 defined dry-run config boundary
- TASK-317 defined stdout-only no-trade config template
- TASK-318 defined startup authorization plan
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-320 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-320 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup attempt
- future startup must remain no-trade
- future startup must use isolated startup quarantine outside repository
- future startup must use no-trade config
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must prove no terminal data directory exists in repository before startup
- future startup must prove no startup log exists in repository before startup
- future startup must prove no generated no-trade config file exists in repository before startup
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must capture startup result stdout-only unless separately authorized
- future startup must clean up quarantine unless separately authorized
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
"""

DEFAULT_TASK321_PARSER_PIPELINE_INTEGRATION_TEXT = """# TASK-321 Parser pipeline integration

- TASK-321 parser pipeline integration
- parser-pipeline-integration-only
- parser-manifest-integration
- not MT5 run in TASK-321
- not terminal64.exe execution in TASK-321
- not Strategy Tester authorization
- not backtest authorization
- not trading authorization
- no MT5 terminal run executed in TASK-321
- no manifest generated in repository during TASK-321
- no external evidence copied into repository
- TASK-319 completed
- TASK-319 completion commit is 5f0a697 TASK-319 implement MT5 no-trade startup preflight gate
- TASK-319 completion tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate
- future TASK-320 requires GPT boundary before any MT5 terminal startup attempt
- TASK-320 must not be entered directly
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
"""


def fail(message):
    print("Project state docs self-test failed")
    print(message)
    return 1


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_validator(project_root):
    command = [
        sys.executable,
        str(project_root / "tools" / "validate_project_state_docs.py"),
    ]
    return subprocess.run(
        command,
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )


def combined_output(result):
    return f"{result.stdout}\n{result.stderr}"


def ensure_prerequisites():
    if not VALIDATOR_PATH.exists():
        return f"validator script not found: {VALIDATOR_PATH}"
    return ""


def suspicious_fragment():
    return "".join(chr(codepoint) for codepoint in [0x8930, 0x64B3, 0x58A0])


def doc_text(
    include_role_boundary=True,
    boundary_lines=None,
    current_commit=DEFAULT_COMMIT,
    functional_task=DEFAULT_FUNCTIONAL_TASK,
):
    if boundary_lines is None:
        boundary_lines = DEFAULT_BOUNDARY_LINES

    role_boundary = """
## TASK-DOC Role Boundary

- TASK-DOC docs edits must be made by Codex.
- Builder / Trae may only review, validate, git add, and git commit.
- Builder / Trae must not directly write docs content.
- Builder / Trae must not define the next stage boundary.
- The next task boundary must be defined by ChatGPT.
"""
    boundary_text = "\n".join(boundary_lines)
    return (
        "# Sample state doc\n\n"
        "当前最新提交：\n\n"
        f"{current_commit}\n\n"
        "当前最新工程任务：\n\n"
        "80e162b TASK-085 add ExecutionManager explicit no-trade guard\n\n"
        "当前最新功能任务：\n\n"
        f"{functional_task}\n\n"
        "当前阶段：\n\n"
        "v0.5.0：official evidence archive policy and reproducibility boundary\n\n"
        "当前最新稳定标签：\n\n"
        "v0.2.2-execution-manager-no-trade-guard\n\n"
        "稳定标签目标：\n\n"
        "1c93d1b TASK-DOC-087 update state after TASK-086\n\n"
        "历史稳定标签引用：\n\n"
        "v0.2.1-mq5-safety-guardrails\n\n"
        "a808d8e TASK-DOC-084 update state after TASK-084\n\n"
        "v0.2.0-runtime-parser-input-samples\n\n"
        "e35a13b TASK-DOC-073 update state after TASK-072\n\n"
        "v0.1.9-runtime-report-quality\n\n"
        "v0.1.8-engineering-toolchain-stable\n\n"
        "v0.1.7-core-signal-log-throttle\n\n"
        "## 已完成任务记录\n\n"
        "- TASK-087 completed：define v0.3.0 MQ5 backtest validation boundary\n\n"
        "## TASK-087 结果\n\n"
        "- v0.3.0 boundary defined as MQ5 backtest validation and no-trade execution-chain validation stage\n"
        "- v0.3.0 allowed scope is MQ5 backtest entry audit\n"
        "- v0.3.0 allowed scope is Strategy Tester / backtest run evidence recording\n"
        "- v0.3.0 allowed scope is no-trade execution-chain validation\n"
        "- v0.3.0 allowed scope is InpEnableTrading=false behavior validation\n"
        "- v0.3.0 allowed scope is RiskManager / ExecutionManager rejection-path validation\n"
        "- v0.3.0 allowed scope is backtest logs, reports, and sample-quality enhancement\n"
        "- v0.3.0 does not represent live trading\n"
        "- v0.3.0 does not represent real trading readiness\n"
        "- v0.3.0 does not represent a completed profitable strategy\n"
        "- v0.3.0 only allows no-trade backtest validation and evidence collection\n"
        "- v0.3.0 still forbids real trading\n"
        "- v0.3.0 still forbids CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify / PositionClose / OrderClose\n"
        "- v0.3.0 still forbids ATR / position sizing / stop loss / take profit\n"
        "- v0.3.0 still forbids AI / multi-symbol / multi-account\n"
        "- v0.3.0 still forbids Martingale / grid / averaging-down\n"
        "- v0.3.0 still forbids profit optimization\n\n"
        "- TASK-097 completed：TASK-097 define v0.4.0 backtest evidence archive and report parser quality boundary\n\n"
        "## TASK-097 results\n\n"
        "- define v0.4.0 backtest evidence archive and report parser quality boundary\n"
        "- v0.4.0：回测证据归档、报告解析与可复现性增强阶段\n"
        "- v0.3.0 phase closure audit completed\n"
        "- v0.4.0 allowed scope: backtest evidence archive planning\n"
        "- v0.4.0 allowed scope: Strategy Tester report / log evidence metadata normalization\n"
        "- v0.4.0 allowed scope: report parser quality improvement\n"
        "- v0.4.0 allowed scope: no-trade evidence reproducibility checks\n"
        "- v0.4.0 allowed scope: evidence manifest / report consistency validation\n"
        "- v0.4.0 allowed scope: parsing already generated MT5 reports or logs when explicitly provided\n"
        "- v0.4.0 allowed scope: tool / docs improvements for evidence quality only\n"
        "- v0.4.0 forbids real trading\n"
        "- v0.4.0 forbids live trading readiness claim\n"
        "- v0.4.0 forbids profit optimization\n"
        "- v0.4.0 forbids parameter optimization for profit\n"
        "- v0.4.0 forbids CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify\n"
        "- v0.4.0 forbids ATR / position sizing / stop loss / take profit\n"
        "- v0.4.0 forbids AI / multi-symbol / multi-account\n"
        "- v0.4.0 forbids Martingale / grid / averaging-down\n"
        "- v0.4.0 forbids direct MQ5 modification unless a future ChatGPT task explicitly allows it\n"
        "- v0.4.0 forbids direct backtest/sets modification unless a future ChatGPT task explicitly allows it\n"
        "- v0.4.0 forbids MT5 run unless a future ChatGPT task explicitly allows it\n"
        "- TASK-097 does not add parser implementation\n"
        "- TASK-097 does not create evidence files\n"
        "- TASK-097 does not run MT5\n"
        "- TASK-097 does not modify MQ5\n"
        "- TASK-097 does not modify backtest/sets\n"
        "- TASK-097 does not create tag\n\n"
        "- TASK-112 completed: TASK-112 define v0.5.0 evidence archive policy boundary\n"
        "- 38f1ce2 TASK-112 define v0.5.0 evidence archive policy boundary\n"
        "- TASK-DOC-135 updated project state after TASK-112\n"
        "- current latest engineering / boundary task updated to 38f1ce2 TASK-112 define v0.5.0 evidence archive policy boundary\n"
        "- TASK-109 real external evidence read-only end-to-end manifest validation passed\n"
        "- TASK-109 chain: real external TesterBacktest.html + 日志.txt -> parser outputs -> temporary manifest -> schema validator -> passed\n"
        "- run_engineering_toolchain_checks.py passed, 17/17 PASS after TASK-112\n"
        "- validate_python_tool_safety.py passed, 26 tools after TASK-112\n"
        "- current next boundary remains TASK-118\n"
        "- TASK-117 completed\n"
        "- fc7361c TASK-117 update local agent execution reporting protocol\n"
        "- current latest engineering / protocol task updated to fc7361c TASK-117 update local agent execution reporting protocol\n"
        "- AGENTS.md now defines local agent execution and reporting protocol\n"
        "- no files modified by TASK-117 outside AGENTS.md\n"
        "- no tag moved by TASK-117\n"
        "- no push by TASK-117\n"
        "- no MT5 run by TASK-117\n"
        "- current next boundary updated to TASK-118\n"
        "- current next boundary remains TASK-118\n"
        "- TASK-118 completed\n"
        "- 9f27267 TASK-118 add deterministic local task acceptance reporter\n"
        "- new tool added: tools/task_acceptance_report.ps1\n"
        "- no files modified by TASK-118 outside tools/task_acceptance_report.ps1\n"
        "- no tag moved by TASK-118\n"
        "- no push by TASK-118\n"
        "- no MT5 run by TASK-118\n"
        "- no manifest created by TASK-118\n"
        "- current next boundary updated to TASK-119\n"
        "- current next boundary remains TASK-119\n"
        "- TASK-119 completed\n"
        "- de16dcd TASK-DOC-147 update state after TASK-TAG-031\n"
        "- tools/task_acceptance_report.ps1 coverage audited: PASS, 8/8 checks\n"
        "- no files modified by TASK-119\n"
        "- no tag moved by TASK-119\n"
        "- no push by TASK-119\n"
        "- no MT5 run by TASK-119\n"
        "- no manifest created by TASK-119\n"
        "- current next boundary updated to TASK-120\n"
        "- current next boundary remains TASK-120\n"
        "- TASK-120 completed\n"
        "- 10f248f TASK-120 add official manifest filename path validator\n"
        "- new tool added: tools/validate_official_manifest_path_policy.py\n"
        "- no files modified by TASK-120 outside tools/\n"
        "- no tag moved by TASK-120\n"
        "- no push by TASK-120\n"
        "- no MT5 run by TASK-120\n"
        "- no manifest created by TASK-120\n"
        "- current next boundary updated to TASK-121\n"
        "- current next boundary remains TASK-121\n"
        "- TASK-121 completed\n"
        "- official manifest path policy validator coverage audit passed\n"
        "- validator covers backtest/reports/manifests/ directory rule\n"
        "- validator covers {taskId}_{evidenceSetId}_manifest.json filename format\n"
        "- validator covers TASK-\\d+ taskId format\n"
        "- validator covers ASCII-safe evidenceSetId\n"
        "- validator rejects spaces in manifest filename\n"
        "- validator rejects Chinese characters in manifest filename\n"
        "- validator rejects absolute paths\n"
        "- validator rejects path traversal\n"
        "- validator rejects non-manifests directory\n"
        "- validator rejects already existing target file\n"
        "- validator self-test passed, 9/9 PASS\n"
        "- engineering toolchain passed, 18/18 PASS\n"
        "- task_acceptance_report.ps1 PASS after TASK-121\n"
        "- current gap: none\n"
        "- current next boundary updated to TASK-122\n"
        "- current next boundary remains TASK-122\n"
        "- TASK-122 completed\n"
        "- official manifest creation preflight boundary audit passed\n"
        "- official manifest storage policy is defined: backtest/reports/manifests/\n"
        "- official manifest naming policy is defined: {taskId}_{evidenceSetId}_manifest.json\n"
        "- official manifest filename/path validator completed\n"
        "- evidence manifest generator completed\n"
        "- evidence manifest schema validator completed\n"
        "- Strategy Tester HTML parser completed\n"
        "- MT5 log no-trade parser completed\n"
        "- task_acceptance_report.ps1 available\n"
        "- backtest/reports/manifests/ still not created\n"
        "- no official manifest exists yet\n"
        "- external evidence has not been copied\n"
        "- MT5 has not been run\n"
        "- suitable for future first official manifest dry-run task definition\n"
        "- current next boundary updated to TASK-123\n"
        "- current next boundary remains TASK-123\n"
        "- TASK-123 completed\n"
        "- b93ecb5 TASK-123 define first official manifest dry-run boundary\n"
        "- TASK-122 / TASK-DOC-155 / TASK-TAG-036 / TASK-DOC-156 / TASK-123 closed loop completed\n"
        "- first official manifest dry-run boundary defined\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- dry-run may generate manifest only in a temporary directory\n"
        "- dry-run must use generate_evidence_manifest.py\n"
        "- dry-run must use validate_evidence_manifest_schema.py\n"
        "- dry-run must use validate_official_manifest_path_policy.py\n"
        "- dry-run must use task_acceptance_report.ps1\n"
        "- dry-run artifacts must be cleaned before task end\n"
        "- dry-run does not represent official archive creation\n"
        "- dry-run does not represent live trading readiness\n"
        "- dry-run does not represent real trading availability\n"
        "- dry-run does not represent profitability\n"
        "- dry-run does not authorize real trading\n"
        "- dry-run does not authorize copying evidence\n"
        "- current next boundary updated to TASK-124\n"
        "- current next boundary remains TASK-124\n"
        "- TASK-124 completed\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- TASK-122 / TASK-DOC-155 / TASK-TAG-036 / TASK-DOC-156 / TASK-123 / TASK-DOC-157 closed loop completed\n"
        "- first official manifest dry-run boundary defined\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-125\n"
        "- current next boundary remains TASK-125\n"
        "- TASK-125 completed\n"
        "- current latest commit updated to a0e6ce7 TASK-DOC-158 update state after TASK-124\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run boundary defined\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-126\n"
        "- current next boundary remains TASK-126\n"
        "- TASK-126 completed\n"
        "- current latest commit remains a0e6ce7 TASK-DOC-158 update state after TASK-124\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run boundary remains effective\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-127\n"
        "- current next boundary remains TASK-127\n"
        "- TASK-127 completed\n"
        "- current latest commit updated to d09e87e TASK-DOC-160 update state after TASK-126\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-128\n"
        "- current next boundary remains TASK-128\n"
        "- TASK-128 completed\n"
        "- current latest commit updated to 5f8a272 TASK-DOC-161 update state after TASK-127\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run boundary remains effective\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-129\n"
        "- current next boundary remains TASK-129\n"
        "- TASK-129 completed\n"
        "- current latest commit updated to e3cfb79 TASK-DOC-162 update state after TASK-128\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-130\n"
        "- current next boundary remains TASK-130\n"
        "- TASK-130 completed\n"
        "- current latest commit updated to f07f3ee TASK-DOC-163 update state after TASK-129\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-131\n"
        "- current next boundary remains TASK-131\n"
        "- TASK-131 completed\n"
        "- current latest commit updated to a1ffd7b TASK-DOC-164 update state after TASK-130\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-132\n"
        "- current next boundary remains TASK-132\n"
        "- TASK-132 completed\n"
        "- current latest commit updated to ea786a2 TASK-DOC-165 update state after TASK-131\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-133\n"
        "- current next boundary remains TASK-133\n"
        "- TASK-133 completed\n"
        "- current latest commit updated to abfbcef TASK-DOC-166 update state after TASK-132\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-134\n"
        "- current next boundary remains TASK-134\n"
        "- TASK-134 completed\n"
        "- current latest commit updated to fdf8643 TASK-DOC-167 update state after TASK-133\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-135\n"
        "- current next boundary remains TASK-135\n"
        "- TASK-135 completed\n"
        "- current latest commit updated to e21ca46 TASK-DOC-168 update state after TASK-134\n"
        "- current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5\n"
        "- first official manifest dry-run completed\n"
        "- future dry-run must not create official manifest\n"
        "- future dry-run must not create fixture\n"
        "- future dry-run must not create directory\n"
        "- future dry-run must not copy external evidence\n"
        "- future dry-run must not run MT5\n"
        "- current next boundary updated to TASK-136\n"
        "- current next boundary remains TASK-136\n"
        "- TASK-136 completed\n"
        "- first official manifest promotion readiness audit passed\n"
        "- current HEAD is 2176692 TASK-DOC-170 update state after TASK-TAG-037\n"
        "- current stable tag remains v0.5.11-first-official-manifest-dry-run-summary-closure\n"
        "- v0.5.11-first-official-manifest-dry-run-summary-closure points to 29acb6b TASK-DOC-169 update state after TASK-135\n"
        "- first official manifest dry-run closed loop completed\n"
        "- backtest/reports/manifests/ still not created\n"
        "- no official repository manifest exists\n"
        "- official manifest storage policy defined\n"
        "- official manifest naming policy defined\n"
        "- official manifest path validator completed\n"
        "- generator completed\n"
        "- schema validator completed\n"
        "- HTML parser completed\n"
        "- log parser completed\n"
        "- task_acceptance_report.ps1 available\n"
        "- current gap: none\n"
        "- suitable for future first official manifest creation authorization task\n"
        "- current next boundary updated to TASK-137\n"
        "- current next boundary remains TASK-137\n"
        "- TASK-137 completed\n"
        "- commit recorded: 7103cd0 TASK-137 define first official manifest creation authorization boundary\n"
        "- first official manifest creation authorization boundary defined\n"
        "- future creation task must be separately authorized by a future explicit task\n"
        "- TASK-137 did not create official manifest\n"
        "- TASK-137 did not create backtest/reports/manifests/\n"
        "- TASK-137 did not create fixture\n"
        "- TASK-137 did not copy external evidence\n"
        "- TASK-137 did not run MT5\n"
        "- TASK-137 did not enter real trading\n"
        "- TASK-137 did not perform profit optimization\n"
        "- future creation task must use path policy validator\n"
        "- future creation task must use {taskId}_{evidenceSetId}_manifest.json naming convention\n"
        "- future creation task must use backtest/reports/manifests/\n"
        "- future creation task must use generate_evidence_manifest.py\n"
        "- future creation task must use validate_evidence_manifest_schema.py\n"
        "- future creation task must use validate_official_manifest_path_policy.py\n"
        "- future creation task must use task_acceptance_report.ps1\n"
        "- future creation task must record repositoryState\n"
        "- future creation task must record tags\n"
        "- future creation task must record files[] metadata only\n"
        "- future creation task must not copy external evidence\n"
        "- future creation task must not claim live trading readiness / real trading availability / profitability\n"
        "- future creation task must not authorize real trading\n"
        "- v0.5.12 only means promotion readiness audit closed\n"
        "- v0.5.12 does not mean official manifest has been created\n"
        "- no official repository manifest exists\n"
        "- backtest/reports/manifests/ still not created\n"
        "- current stable tag remains v0.5.12-first-official-manifest-promotion-readiness-audit -> 1d3dd4e\n"
        "- current next boundary updated to TASK-138\n"
        "- current next boundary remains TASK-138\n"
        "- TASK-138 completed\n"
        "- first official manifest creation authorization boundary coverage audit passed\n"
        "- current HEAD is a8e5993 TASK-DOC-174 update state after TASK-TAG-039\n"
        "- current stable tag remains v0.5.13-first-official-manifest-creation-authorization-boundary\n"
        "- v0.5.13-first-official-manifest-creation-authorization-boundary points to e869bef TASK-DOC-173 update state after TASK-137\n"
        "- v0.5.12-first-official-manifest-promotion-readiness-audit still points to 1d3dd4e\n"
        "- v0.5.11-first-official-manifest-dry-run-summary-closure still points to 29acb6b\n"
        "- v0.5.10-official-manifest-creation-preflight-audit still points to 890dfa5\n"
        "- TASK-137 / TASK-DOC-173 / TASK-TAG-039 / TASK-DOC-174 / TASK-138 closed loop completed\n"
        "- first official manifest creation authorization boundary coverage satisfied\n"
        "- creation task must use path policy validator\n"
        "- creation task must use {taskId}_{evidenceSetId}_manifest.json naming convention\n"
        "- creation task must use backtest/reports/manifests/\n"
        "- creation task must use generate_evidence_manifest.py\n"
        "- creation task must use validate_evidence_manifest_schema.py\n"
        "- creation task must use validate_official_manifest_path_policy.py\n"
        "- creation task must use task_acceptance_report.ps1\n"
        "- creation task must record repositoryState / tags / metadata-only files[]\n"
        "- creation task must not copy external evidence\n"
        "- creation task must not claim live trading readiness / real trading availability / profitability\n"
        "- creation task must not authorize real trading\n"
        "- current gap: none\n"
        "- suitable for future first official manifest creation implementation task\n"
        "- current next boundary updated to TASK-139\n"
        "- current next boundary remains TASK-139\n"
        "- TASK-139 completed\n"
        "- 1a57ed1 TASK-139 create first official evidence manifest\n"
        "- first official repository manifest created\n"
        "- official manifest path: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json\n"
        "- backtest/reports/manifests/ directory created\n"
        "- this manifest is the only authorized manifest created\n"
        "- no other manifest / report created\n"
        "- path policy validator passed with --no-check-overwrite\n"
        "- schema validator passed\n"
        "- engineering toolchain checks passed, 18/18 PASS\n"
        "- noTradeAssertions.passed = true\n"
        "- riskApproved = 0\n"
        "- executionAttempts = 0\n"
        "- totalTrades = 0\n"
        "- totalDeals = 0\n"
        "- buyTrades = 0\n"
        "- sellTrades = 0\n"
        "- InpEnableTrading = false\n"
        "- stable tag recorded as v0.5.14-first-official-manifest-creation-authorization-coverage-audit -> e5f1405\n"
        "- files[] records external evidence metadata only; no evidence copy\n"
        "- safetyAssertions all true\n"
        "- official manifest does not represent live trading readiness\n"
        "- official manifest does not represent real trading availability\n"
        "- official manifest does not represent profitability\n"
        "- official manifest does not authorize real trading\n"
        "- current latest engineering task updated to 1a57ed1 TASK-139 create first official evidence manifest\n"
        "- current next boundary updated to TASK-140\n"
        "- current next boundary remains TASK-140\n"
        "- TASK-140 completed\n"
        "- first official evidence manifest archive closure readiness audit passed\n"
        "- current HEAD is 54e8e6a TASK-DOC-178 update state after TASK-TAG-041\n"
        "- current stable tag is v0.5.15-first-official-evidence-manifest\n"
        "- v0.5.15-first-official-evidence-manifest points to 0a57e91 TASK-DOC-177 update state after TASK-139\n"
        "- v0.5.14-first-official-manifest-creation-authorization-coverage-audit still points to e5f1405\n"
        "- v0.5.13-first-official-manifest-creation-authorization-boundary still points to e869bef\n"
        "- v0.5.12-first-official-manifest-promotion-readiness-audit still points to 1d3dd4e\n"
        "- v0.5.11-first-official-manifest-dry-run-summary-closure still points to 29acb6b\n"
        "- v0.5.10-official-manifest-creation-preflight-audit still points to 890dfa5\n"
        "- official manifest archive closure readiness satisfied\n"
        "- official manifest exists\n"
        "- official manifest is the only manifest\n"
        "- official manifest path is correct: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json\n"
        "- schema validator PASS\n"
        "- path policy validator PASS with --no-check-overwrite\n"
        "- engineering toolchain 18/18 PASS\n"
        "- validate_project_state_docs.py PASS\n"
        "- test_validate_project_state_docs.py PASS\n"
        "- TesterBacktest.html was not copied\n"
        "- 日志.txt was not copied\n"
        "- current gap: none\n"
        "- suitable for future v0.5.0 official evidence archive closure audit / tag\n"
        "- current next boundary updated to TASK-141\n"
        "- current next boundary remains TASK-141\n"
        "- TASK-141 completed\n"
        "- v0.5.0 official evidence archive closure readiness audit passed\n"
        "- current HEAD is 0543a09 TASK-DOC-180 update state after TASK-TAG-042\n"
        "- current stable tag is v0.5.16-official-evidence-archive-closure-readiness-audit\n"
        "- v0.5.16-official-evidence-archive-closure-readiness-audit points to ed5eb4b TASK-DOC-179 update state after TASK-140\n"
        "- v0.5.0 official evidence archive policy defined\n"
        "- official manifest storage policy defined\n"
        "- official manifest naming policy defined\n"
        "- official manifest path validator completed\n"
        "- evidence manifest generator completed\n"
        "- evidence manifest schema validator completed\n"
        "- Strategy Tester HTML parser completed\n"
        "- MT5 log no-trade parser completed\n"
        "- task_acceptance_report.ps1 available\n"
        "- first official manifest creation authorization boundary defined\n"
        "- first official evidence manifest created\n"
        "- suitable for future v0.5.0 phase closure audit / tag\n"
        "- current next boundary updated to TASK-142\n"
        "- current next boundary remains TASK-142\n"
        "- TASK-142 completed\n"
        "- v0.5.0 official evidence archive phase closure readiness audit passed\n"
        "- current HEAD is e35bcf2 TASK-DOC-182 update state after TASK-TAG-043\n"
        "- current stable tag is v0.5.17-v050-official-evidence-archive-closure-readiness\n"
        "- v0.5.17-v050-official-evidence-archive-closure-readiness points to 8702fd5 TASK-DOC-181 update state after TASK-141\n"
        "- suitable for future v0.5.0 phase closure stable tag\n"
        "- current next boundary updated to TASK-143\n"
        "- current next boundary remains TASK-143\n"
        "- TASK-143 completed\n"
        "- v0.5.0 official evidence archive final phase closure audit passed\n"
        "- current HEAD is c6edc02 TASK-DOC-184 update state after TASK-TAG-044\n"
        "- current stable tag is v0.5.18-v050-official-evidence-archive-phase-closure-readiness\n"
        "- v0.5.18-v050-official-evidence-archive-phase-closure-readiness points to ed4017b TASK-DOC-183 update state after TASK-142\n"
        "- v0.5.0 final phase closure satisfied\n"
        "- suitable for future v0.5.0 final phase closure stable tag\n"
        "- current next boundary updated to TASK-144\n"
        "- current next boundary remains TASK-144\n"
        "- TASK-144 completed\n"
        "- v0.5.0 final phase closure tag completion audit passed\n"
        "- current HEAD is 26caea9 TASK-DOC-186 update state after TASK-TAG-045\n"
        "- current stable tag is v0.5.19-v050-official-evidence-archive-final-phase-closure\n"
        "- v0.5.19-v050-official-evidence-archive-final-phase-closure points to 38b343c TASK-DOC-185 update state after TASK-143\n"
        "- v0.5.0 final phase closure fixed by v0.5.19\n"
        "- engineering toolchain 19/19 PASS\n"
        "- suitable for future v0.5.0 final closure documentation / transition boundary\n"
        "- current next boundary updated to TASK-145\n"
        "- current next boundary remains TASK-145\n"
        "- TASK-145 completed\n"
        "- v0.5.0 final closure documentation transition boundary readiness audit passed\n"
        "- current HEAD is 30025ea TASK-DOC-188 update state after TASK-TAG-046\n"
        "- current stable tag is v0.5.20-v050-final-closure-documentation-transition-boundary-readiness\n"
        "- v0.5.20-v050-final-closure-documentation-transition-boundary-readiness points to 61fb9c0 TASK-DOC-187 update state after TASK-144\n"
        "- v0.5.0 final closure documentation / transition boundary readiness fixed by v0.5.20\n"
        "- v0.5.0 official evidence archive final phase closure fixed by v0.5.19\n"
        "- first official evidence manifest fixed by v0.5.15\n"
        "- suitable for future v0.5.0 final closure documentation stable tag\n"
        "- suitable for future ChatGPT-defined v0.6.0 transition boundary\n"
        "- current next boundary updated to TASK-146\n"
        "- current next boundary remains TASK-146\n"
        "- do not directly enter v0.6.0\n"
        "- TASK-146 completed\n"
        "- v0.5.0 final closure documentation transition boundary completion audit passed\n"
        "- current HEAD is 924debc TASK-DOC-190 update state after TASK-TAG-047\n"
        "- current stable tag is v0.5.21-v050-final-closure-documentation-transition-boundary\n"
        "- v0.5.21-v050-final-closure-documentation-transition-boundary points to 3d3cfd9 TASK-DOC-189 update state after TASK-145\n"
        "- v0.5.0 final closure documentation / transition boundary fixed by v0.5.21\n"
        "- v0.5.21 does not automatically enter v0.6.0\n"
        "- suitable for future v0.6.0 transition boundary planning task\n"
        "- current next boundary updated to TASK-147\n"
        "- current next boundary remains TASK-147\n"
        "- new tool added: tools/validate_official_manifest_path_policy.py\n"
        "- new tool added: tools/test_validate_official_manifest_path_policy.py\n"
        "- integrated into run_engineering_toolchain_checks.py\n"
        "- engineering toolchain 19/19 PASS after TASK-120\n"
        "- TASK-114 completed\n"
        "- d432a37 TASK-114 define official manifest storage naming policy\n"
        "- current latest engineering / policy task updated to d432a37 TASK-114 define official manifest storage naming policy\n"
        "- official manifest storage path defined: backtest/reports/manifests/\n"
        "- official manifest naming convention recorded: {taskId}_{evidenceSetId}_manifest.json\n"
        "- metadata-only external evidence reference policy recorded\n"
        "- official manifest creation boundary recorded\n"
        "- reproducibility checklist placeholder recorded\n"
        "- TASK-115 completed\n"
        "- f87ac9c TASK-DOC-140 update state after TASK-TAG-028\n"
        "- current stable tag remains v0.5.2-official-manifest-storage-naming-policy -> b3b30a7\n"
        "- official manifest storage / naming policy coverage audited\n"
        "- storage path backtest/reports/manifests/ is recorded\n"
        "- backtest/reports/manifests/ is defined only and not created\n"
        "- naming convention is recorded: {taskId}_{evidenceSetId}_manifest.json\n"
        "- generate_evidence_manifest.py can generate schemaVersion, taskId, evidenceSetId, externalEvidenceRoot, files[], repositoryState, tags, notes, and safetyAssertions\n"
        "- validate_evidence_manifest_schema.py can validate all required fields\n"
        "- backtest/reports/manifests/ does not exist\n"
        "- current gap: manifestRevision field is documented as a placeholder but generator does not implement it\n"
        "- recommended next candidate: official manifest filename/path validator\n"
        "- TASK-116 completed\n"
        "- 229997d TASK-DOC-142 update state after TASK-TAG-029\n"
        "- current stable tag remains v0.5.3-official-manifest-storage-naming-coverage-audit -> e6b579f\n"
        "- final official manifest naming convention is {taskId}_{evidenceSetId}_manifest.json\n"
        "- docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md records {taskId}_{evidenceSetId}_manifest.json\n"
        "- no conflicting format found: {evidenceSetId}_{taskId}_manifest.json\n"
        "- docs are fully consistent on the official manifest naming convention\n"
        "- generate_evidence_manifest.py does not hard-code filename rule\n"
        "- no tool currently enforces {taskId}_{evidenceSetId}_manifest.json\n"
        "- current gap: no official manifest filename/path validator exists\n"
        "- current gap: naming convention is documented only\n"
        "- recommended next candidate: official manifest creation preflight checklist\n"
        "- define v0.5.0 evidence archive policy boundary\n"
        "- v0.4.0 phase closure completed\n"
        "- v0.5.0 boundary defined as official evidence archive policy and reproducibility boundary\n"
        "- v0.5.0 allowed scope: evidence archive policy definition\n"
        "- v0.5.0 allowed scope: official repository manifest boundary definition\n"
        "- v0.5.0 allowed scope: metadata-only evidence references\n"
        "- v0.5.0 allowed scope: evidence sanitization policy\n"
        "- v0.5.0 allowed scope: reproducibility checklist\n"
        "- v0.5.0 allowed scope: official manifest naming/location convention\n"
        "- v0.5.0 allowed scope: external evidence retention policy\n"
        "- v0.5.0 allowed scope: parser/generator hardening only when explicitly authorized\n"
        "- v0.5.0 allowed scope: documentation / validation tooling updates\n"
        "- v0.5.0 forbidden scope: no real trading\n"
        "- v0.5.0 forbidden scope: no live trading readiness claim\n"
        "- v0.5.0 forbidden scope: no real trading allowed claim\n"
        "- v0.5.0 forbidden scope: no profitability claim\n"
        "- v0.5.0 forbidden scope: no profit optimization\n"
        "- v0.5.0 forbidden scope: no MT5 run unless future task explicitly authorizes\n"
        "- v0.5.0 forbidden scope: no copying external evidence unless future task explicitly authorizes\n"
        "- v0.5.0 forbidden scope: no repository manifest creation unless future task explicitly authorizes\n"
        "- v0.5.0 forbidden scope: no MQ5 modification unless future task explicitly authorizes\n"
        "- v0.5.0 forbidden scope: no backtest/sets modification unless future task explicitly authorizes\n"
        "- v0.5.0 forbidden scope: no OrderSend / Buy / Sell / CTrade / PositionOpen / PositionClose / OrderModify / OrderClose\n"
        "- v0.5.0 does not mean live trading readiness\n"
        "- v0.5.0 does not mean real trading availability\n"
        "- v0.5.0 does not mean profitable strategy completion\n"
        "- v0.5.0 does not mean permission to run MT5\n"
        "- v0.5.0 does not mean permission to copy evidence\n"
        "- v0.5.0 does not mean permission to create official manifest yet\n\n"
        "## TASK-DOC-236 update state after TASK-235\n\n"
        "- current task is TASK-DOC-236 update state after TASK-235\n"
        "- TASK-DOC-236 target is to sync TASK-235 read-only MQ5 strategy inventory audit results\n"
        "- TASK-235 completed\n"
        "- TASK-235 read-only MQ5 strategy inventory audit PASS\n"
        "- current HEAD is 0fc2b95 TASK-DOC-234 update state after TASK-233\n"
        "- tracked working tree clean before TASK-DOC-236 edits\n"
        "- current phase remains v0.5.0\n"
        "- current stable tag remains v0.5.37-v060-implementation-readiness-tooling-validation\n"
        "- v0.5.37 points to 915b6c4 TASK-166 implement v0.6.0 implementation planning boundary validator\n"
        "- MQ5 root exists\n"
        "- scanned 7 MQ5 files: 1 .mq5 and 6 .mqh\n"
        "- scanned file: config/InputConfig.mqh\n"
        "- scanned file: core/EaController.mqh\n"
        "- scanned file: execution/ExecutionManager.mqh\n"
        "- scanned file: logger/Logger.mqh\n"
        "- scanned file: risk/RiskManager.mqh\n"
        "- scanned file: signals/SignalEngine.mqh\n"
        "- scanned file: TradingSystem.mq5\n"
        "- input parameter lines: 34\n"
        "- InpEnableTrading appears in 4 files\n"
        "- RiskManager appears in 2 files\n"
        "- SignalEngine appears in 4 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade trading keywords are all false\n"
        "- current MQ5 codebase is pure framework / no active trading instructions\n"
        "- OnInit / OnTick / OnDeinit are present in framework files\n"
        "- inventory output includes: Inventory only; no MT5 run; no trading authorization.\n"
        "- tools/run_release_validation_bundle.py --only mq5-inventory PASS\n"
        "- tools/run_release_validation_bundle.py --only project-state-docs PASS\n"
        "- tools/run_release_validation_bundle.py --only project-state-docs-self-test PASS\n"
        "- TASK-235 did not modify MQ5 files\n"
        "- TASK-235 did not run MT5\n"
        "- TASK-235 did not create manifest / fixture / report / directory\n"
        "- TASK-235 did not copy external evidence\n"
        "- v0.6.0 implementation has not started\n"
        "- suitable for ChatGPT to define the first v0.6.0 low-risk implementation planning task\n\n"
        "## TASK-DOC-237 create first v0.6.0 low-risk implementation planning packet\n\n"
        "- TASK-DOC-237 is a doc-only planning task\n"
        "- docs/V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md exists\n"
        "- TASK-DOC-237 does not enter v0.6.0 implementation\n"
        "- TASK-DOC-237 does not modify MQ5\n"
        "- TASK-DOC-237 does not run MT5\n"
        "- current latest tag is v0.5.38-task-236-project-state-synced\n"
        "- future candidate slice is TASK-238 v0.6.0 no-trade observability scaffold\n"
        "- TASK-238 is a future candidate only and is not authorized by TASK-DOC-237\n"
        "- future TASK-238 candidate must not introduce Buy / Sell / OrderSend / PositionOpen / CTrade\n\n"
        "## TASK-DOC-238 define low-risk no-trade observability scaffold boundary\n\n"
        "- current task is TASK-DOC-238 define low-risk no-trade observability scaffold boundary\n"
        "- TASK-DOC-238 is planning-only and defines a future candidate boundary\n"
        "- docs/V060_TASK_238_NO_TRADE_SCAFFOLD_BOUNDARY.md exists\n"
        "- TASK-DOC-238 does not enter TASK-238 implementation\n"
        "- TASK-DOC-238 does not enter v0.6.0 implementation\n"
        "- TASK-DOC-238 does not modify MQ5\n"
        "- TASK-DOC-238 does not run MT5\n"
        "- TASK-DOC-238 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-238 does not copy external evidence\n"
        "- TASK-DOC-238 does not modify official manifest / backtest/sets\n"
        "- current latest tag is v0.5.39-task-237-first-low-risk-plan\n"
        "- TASK-238 future candidate scope is no-trade observability scaffold only\n"
        "- InpEnableTrading false remains the safety baseline\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade 均 false\n"
        "- current MQ5 codebase remains pure framework / no active trading instructions\n"
        "- Inventory only; no MT5 run; no trading authorization.\n\n"
        "## TASK-DOC-239 define first authorized v0.6.0 low-risk implementation slice boundary\n\n"
        "- current task is TASK-DOC-239 define first authorized v0.6.0 low-risk implementation slice boundary\n"
        "- TASK-DOC-239 defines the first authorized low-risk implementation slice boundary\n"
        "- TASK-DOC-239 is planning + boundary only\n"
        "- docs/V060_TASK_239_FIRST_IMPLEMENTATION_SLICE_BOUNDARY.md exists\n"
        "- current latest tag is v0.5.40-task-238-no-trade-scaffold-boundary\n"
        "- TASK-DOC-238 no-trade scaffold boundary remains the reference baseline\n"
        "- InpEnableTrading false remains the safety baseline\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade 鍧?false\n"
        "- current MQ5 codebase remains pure framework / no active trading instructions\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-DOC-239 does not modify MQ5\n"
        "- TASK-DOC-239 does not run MT5\n"
        "- TASK-DOC-239 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-239 does not copy external evidence\n"
        "- TASK-DOC-239 does not modify official manifest / backtest/sets\n"
        "- TASK-DOC-239 does not enter TASK-240\n"
        "- TASK-DOC-239 does not enter v0.6.0 full implementation\n\n"
        "## TASK-240 implement v0.6.0 no-trade observability scaffold\n\n"
        "- current task is TASK-240 implement v0.6.0 no-trade observability scaffold\n"
        "- TASK-240 is first authorized v0.6.0 low-risk implementation slice\n"
        "- TASK-240 is limited to no-trade observability scaffold\n"
        "- TASK-240 remains limited to no-trade observability scaffold\n"
        "- TASK-240 does not enter v0.6.0 full implementation\n"
        "- current latest tag is v0.5.41-task-239-first-implementation-slice-boundary\n"
        "- InpEnableTrading false remains the safety baseline\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade 鍧?false\n"
        "- current MQ5 codebase remains pure framework / no active trading instructions\n"
        "- no-trade observability scaffold output is read-only\n"
        "- no-trade observability scaffold logs include: Inventory only; no MT5 run; no trading authorization.\n"
        "- no-trade observability scaffold logs include: no-trade observability scaffold\n"
        "- TASK-240 adds only read-only observability input controls\n"
        "- TASK-240 adds only no-trade logging / telemetry contract helper output\n"
        "- TASK-240 adds only OnInit and optional throttled OnTick observability state output\n"
        "- TASK-240 does not modify execution/ExecutionManager.mqh\n"
        "- TASK-240 does not modify risk/RiskManager.mqh\n"
        "- TASK-240 does not modify signals/SignalEngine.mqh\n"
        "- TASK-240 does not run MT5\n"
        "- TASK-240 does not run backtest\n"
        "- TASK-240 does not trigger real trading\n"
        "- TASK-240 does not trigger simulated trading\n"
        "- TASK-240 does not send orders\n"
        "- TASK-240 does not create manifest / fixture / report / directory\n"
        "- TASK-240 does not copy external evidence\n"
        "- TASK-240 does not modify official manifest / backtest/sets\n"
        "- MQ5 inventory must remain PASS with trading keywords false\n\n"
        "## TASK-DOC-241 sync TASK-240 no-trade observability scaffold state to project docs\n\n"
        "- current task is TASK-DOC-241 sync TASK-240 no-trade observability scaffold state to project docs\n"
        "- TASK-DOC-241 objective is to sync TASK-240 no-trade observability scaffold state to project docs\n"
        "- TASK-240 completed no-trade observability scaffold\n"
        "- TASK-240 remains first authorized v0.6.0 low-risk implementation slice\n"
        "- TASK-240 remains limited to no-trade observability scaffold\n"
        "- TASK-240 completed only a no-trade observability scaffold, not v0.6.0 full implementation\n"
        "- current phase remains v0.5.0 with first v0.6.0 implementation slice in progress\n"
        "- current HEAD is f9771d9 TASK-240 implement no-trade observability scaffold\n"
        "- current latest tag is v0.5.42-task-240-v060-no-trade-observability-scaffold\n"
        "- InpEnableTrading false remains the safety baseline\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade 閸?false\n"
        "- current MQ5 codebase remains pure framework / no active trading instructions\n"
        "- no-trade observability scaffold output is read-only\n"
        "- no-trade observability scaffold logs include: Inventory only; no MT5 run; no trading authorization.\n"
        "- no-trade observability scaffold logs include: no-trade observability scaffold\n"
        "- TASK-240 MQ5 inventory remains PASS\n"
        "- TASK-240 trading keywords remain all false\n"
        "- TASK-DOC-241 does not modify MQ5 / MQH\n"
        "- TASK-DOC-241 does not run MT5\n"
        "- TASK-DOC-241 does not run backtest or real trading\n"
        "- TASK-DOC-241 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-241 does not copy external evidence\n"
        "- TASK-DOC-241 does not modify official manifest / backtest/sets\n"
        "- TASK-DOC-241 does not commit\n\n"
        "## TASK-242 implement mq5 no-trade observability contract validator\n\n"
        "- current task is TASK-242 implement mq5 no-trade observability contract validator\n"
        "- TASK-242 objective is to implement a read-only MQ5 no-trade observability contract validator\n"
        "- TASK-242 creates tools/validate_mq5_no_trade_observability.py\n"
        "- TASK-242 creates tools/test_validate_mq5_no_trade_observability.py\n"
        "- TASK-242 integrates mq5-no-trade-observability into tools/run_release_validation_bundle.py\n"
        "- current HEAD is d5babfa TASK-DOC-241 update state after TASK-240\n"
        "- current latest tag is v0.5.43-task-241-sync-task-240-state\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- TASK-242 static validation confirms TASK-240 no-trade observability scaffold remains present\n"
        "- mq5 no-trade observability contract validator checks InpEnableTrading default false\n"
        "- mq5 no-trade observability contract validator checks no MT5 run\n"
        "- mq5 no-trade observability contract validator checks no trading authorization\n"
        "- mq5 no-trade observability contract validator checks no-trade observability scaffold\n"
        "- mq5 no-trade observability contract validator checks Inventory only; no MT5 run; no trading authorization.\n"
        "- mq5 no-trade observability contract validator checks Buy / Sell / OrderSend / PositionOpen / CTrade remain absent from mq5 source files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- TASK-242 does not modify MQ5 / MQH\n"
        "- TASK-242 does not run MT5\n"
        "- TASK-242 does not run backtest\n"
        "- TASK-242 does not enter real trading\n"
        "- TASK-242 does not enter simulated trading\n"
        "- TASK-242 does not send orders\n"
        "- TASK-242 does not create manifest / fixture / report / directory\n"
        "- TASK-242 does not copy external evidence\n"
        "- TASK-242 does not modify official manifest / backtest/sets\n"
        "- TASK-242 does not commit\n\n"
        "## TASK-243 implement structured no-trade observability status snapshot\n\n"
        "- current task is TASK-243 implement structured no-trade observability status snapshot\n"
        "- TASK-243 is a low-risk MQ5 implementation slice\n"
        "- TASK-243 implementation scope is limited to structured no-trade observability status snapshot\n"
        "- TASK-242 completed mq5 no-trade observability contract validator\n"
        "- TASK-242 commit is 8f59b3b TASK-242 implement mq5 no-trade observability contract validator\n"
        "- TASK-242 tag is v0.5.44-task-242-mq5-no-trade-observability-validator\n"
        "- current HEAD is 8f59b3b TASK-242 implement mq5 no-trade observability contract validator\n"
        "- current latest tag is v0.5.44-task-242-mq5-no-trade-observability-validator\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- structured no-trade observability status snapshot records mode=no-trade observability scaffold\n"
        "- structured no-trade observability status snapshot records inventory_notice=Inventory only; no MT5 run; no trading authorization.\n"
        "- structured no-trade observability status snapshot records enable_trading\n"
        "- structured no-trade observability status snapshot records observability_enabled\n"
        "- structured no-trade observability status snapshot records init_log_enabled\n"
        "- structured no-trade observability status snapshot records tick_log_enabled\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-243 does not run MT5\n"
        "- TASK-243 does not execute backtest\n"
        "- TASK-243 does not enter real trading\n"
        "- TASK-243 does not enter simulated trading\n"
        "- TASK-243 does not send orders\n"
        "- TASK-243 does not create manifest / fixture / report / directory\n"
        "- TASK-243 does not copy external evidence\n"
        "- TASK-243 does not modify official manifest / backtest/sets\n"
        "- TASK-243 does not commit\n\n"
        "## TASK-244 implement read-only MQ5 component status snapshot contract\n\n"
        "- current task is TASK-244 implement read-only MQ5 component status snapshot contract\n"
        "- TASK-244 is a low-risk MQ5 implementation slice\n"
        "- TASK-244 implementation scope is limited to read-only MQ5 component status snapshot contract\n"
        "- TASK-243 completed structured no-trade observability status snapshot\n"
        "- TASK-243 commit is f28f788 TASK-243 implement structured no-trade observability status snapshot\n"
        "- TASK-243 tag is v0.5.45-task-243-structured-no-trade-observability-snapshot\n"
        "- current HEAD is f28f788 TASK-243 implement structured no-trade observability status snapshot\n"
        "- current latest tag is v0.5.45-task-243-structured-no-trade-observability-snapshot\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only MQ5 component status snapshot contract records controller_status=ready\n"
        "- read-only MQ5 component status snapshot contract records logger_status=ready\n"
        "- read-only MQ5 component status snapshot contract records signal_status=read-only framework\n"
        "- read-only MQ5 component status snapshot contract records risk_status=read-only framework\n"
        "- read-only MQ5 component status snapshot contract records execution_status=read-only framework\n"
        "- read-only MQ5 component status snapshot contract records all_components_no_trade=true\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-244 does not run MT5\n"
        "- TASK-244 does not run backtest\n"
        "- TASK-244 does not enter real trading\n"
        "- TASK-244 does not enter simulated trading\n"
        "- TASK-244 does not send orders\n"
        "- TASK-244 does not create manifest / fixture / report / directory\n"
        "- TASK-244 does not copy external evidence\n"
        "- TASK-244 does not modify official manifest / backtest/sets\n"
        "- TASK-244 does not commit\n\n"
        "## TASK-245 implement no-trade lifecycle telemetry event contract\n\n"
        "- current task is TASK-245 implement no-trade lifecycle telemetry event contract\n"
        "- TASK-245 is a low-risk MQ5 implementation slice\n"
        "- TASK-245 implementation scope is limited to no-trade lifecycle telemetry event contract\n"
        "- TASK-244 completed read-only MQ5 component status snapshot contract\n"
        "- TASK-244 commit is 98fb991 TASK-244 implement read-only MQ5 component status snapshot contract\n"
        "- TASK-244 tag is v0.5.46-task-244-read-only-component-status-snapshot\n"
        "- current HEAD is 98fb991 TASK-244 implement read-only MQ5 component status snapshot contract\n"
        "- current latest tag is v0.5.46-task-244-read-only-component-status-snapshot\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- no-trade lifecycle telemetry event contract records lifecycle_event=init\n"
        "- no-trade lifecycle telemetry event contract records lifecycle_event=tick\n"
        "- no-trade lifecycle telemetry event contract records lifecycle_event=deinit\n"
        "- no-trade lifecycle telemetry event contract records no_trade_guard=active\n"
        "- no-trade lifecycle telemetry event contract records trading_authorization=false\n"
        "- no-trade lifecycle telemetry event contract records mt5_run_required=false\n"
        "- no-trade lifecycle telemetry event contract records evidence_generation=false\n"
        "- no-trade lifecycle telemetry event contract records manifest_generation=false\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-245 does not run MT5\n"
        "- TASK-245 does not run backtest\n"
        "- TASK-245 does not enter real trading\n"
        "- TASK-245 does not enter simulated trading\n"
        "- TASK-245 does not send orders\n"
        "- TASK-245 does not create manifest / fixture / report / directory\n"
        "- TASK-245 does not copy external evidence\n"
        "- TASK-245 does not modify official manifest / backtest/sets\n"
        "- TASK-245 does not commit\n\n"
        "## TASK-246 implement MQ5 read-only runtime status snapshot logging\n\n"
        "- current task is TASK-246 implement MQ5 read-only runtime status snapshot logging\n"
        "- TASK-246 is a low-risk MQ5 implementation slice\n"
        "- TASK-246 implementation scope is limited to read-only runtime status snapshot logging\n"
        "- TASK-245 completed no-trade lifecycle telemetry event contract\n"
        "- TASK-245 commit is 8f6762c TASK-245 implement no-trade lifecycle telemetry event contract\n"
        "- TASK-245 tag is v0.5.47-task-245-no-trade-lifecycle-telemetry\n"
        "- current HEAD is 8f6762c TASK-245 implement no-trade lifecycle telemetry event contract\n"
        "- current latest tag is v0.5.47-task-245-no-trade-lifecycle-telemetry\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only runtime status snapshot logging records runtime_status_snapshot=true\n"
        "- read-only runtime status snapshot logging records controller_status\n"
        "- read-only runtime status snapshot logging records logger_status\n"
        "- read-only runtime status snapshot logging records signal_status\n"
        "- read-only runtime status snapshot logging records risk_status\n"
        "- read-only runtime status snapshot logging records execution_status\n"
        "- read-only runtime status snapshot logging records no_trade_guard=active\n"
        "- read-only runtime status snapshot logging records trading_authorization=false\n"
        "- read-only runtime status snapshot logging records mt5_run_required=false\n"
        "- read-only runtime status snapshot logging records evidence_generation=false\n"
        "- read-only runtime status snapshot logging records manifest_generation=false\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-246 does not run MT5\n"
        "- TASK-246 does not run backtest\n"
        "- TASK-246 does not enter real trading\n"
        "- TASK-246 does not enter simulated trading\n"
        "- TASK-246 does not send orders\n"
        "- TASK-246 does not create manifest / fixture / report / directory\n"
        "- TASK-246 does not copy external evidence\n"
        "- TASK-246 does not modify official manifest / backtest/sets\n"
        "- TASK-246 does not commit\n\n"
        "## TASK-247 implement MQ5 no-trade performance metrics contract\n\n"
        "- current task is TASK-247 implement MQ5 no-trade performance metrics contract\n"
        "- TASK-247 is a low-risk MQ5 implementation slice\n"
        "- TASK-247 implementation scope is limited to MQ5 no-trade performance metrics contract\n"
        "- TASK-246 completed read-only runtime status snapshot logging\n"
        "- TASK-246 commit is b85b824 TASK-246 implement read-only runtime status snapshot logging\n"
        "- TASK-246 tag is v0.5.48-task-246-read-only-runtime-status-snapshot\n"
        "- current HEAD is b85b824 TASK-246 implement read-only runtime status snapshot logging\n"
        "- current latest tag is v0.5.48-task-246-read-only-runtime-status-snapshot\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- MQ5 no-trade performance metrics contract records runtime_metrics_snapshot=true\n"
        "- MQ5 no-trade performance metrics contract records tick_count\n"
        "- MQ5 no-trade performance metrics contract records oninit_call_count\n"
        "- MQ5 no-trade performance metrics contract records ondeinit_call_count\n"
        "- MQ5 no-trade performance metrics contract records last_tick_timestamp\n"
        "- MQ5 no-trade performance metrics contract records all_components_no_trade=true\n"
        "- MQ5 no-trade performance metrics contract records trading_authorization=false\n"
        "- MQ5 no-trade performance metrics contract records mt5_run_required=false\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-247 does not run MT5\n"
        "- TASK-247 does not run backtest\n"
        "- TASK-247 does not enter real trading\n"
        "- TASK-247 does not enter simulated trading\n"
        "- TASK-247 does not send orders\n"
        "- TASK-247 does not create manifest / fixture / report / directory\n"
        "- TASK-247 does not copy external evidence\n"
        "- TASK-247 does not modify official manifest / backtest/sets\n"
        "- TASK-247 does not commit\n\n"
        "## TASK-248 implement MQ5 no-trade safety guard invariant contract\n\n"
        "- current task is TASK-248 implement MQ5 no-trade safety guard invariant contract\n"
        "- TASK-248 is a low-risk MQ5 implementation slice\n"
        "- TASK-248 implementation scope is limited to no-trade safety guard invariant contract\n"
        "- TASK-247 completed no-trade performance metrics contract\n"
        "- TASK-247 commit is 99e3763 TASK-247 implement no-trade performance metrics contract\n"
        "- TASK-247 tag is v0.5.49-task-247-no-trade-performance-metrics\n"
        "- current HEAD is 99e3763 TASK-247 implement no-trade performance metrics contract\n"
        "- current latest tag is v0.5.49-task-247-no-trade-performance-metrics\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- no-trade safety guard invariant contract records safety_guard_snapshot=true\n"
        "- no-trade safety guard invariant contract records no_trade_guard=active\n"
        "- no-trade safety guard invariant contract records invariant_trading_disabled=true\n"
        "- no-trade safety guard invariant contract records invariant_execution_disabled=true\n"
        "- no-trade safety guard invariant contract records invariant_order_submission_disabled=true\n"
        "- no-trade safety guard invariant contract records invariant_position_management_disabled=true\n"
        "- no-trade safety guard invariant contract records invariant_external_evidence_disabled=true\n"
        "- no-trade safety guard invariant contract records invariant_manifest_generation_disabled=true\n"
        "- no-trade safety guard invariant contract records invariant_mt5_run_required=false\n"
        "- no-trade safety guard invariant contract records invariant_all_components_no_trade=true\n"
        "- no-trade safety guard invariant contract records trading_authorization=false\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-248 does not run MT5\n"
        "- TASK-248 does not run backtest\n"
        "- TASK-248 does not enter real trading\n"
        "- TASK-248 does not enter simulated trading\n"
        "- TASK-248 does not send orders\n"
        "- TASK-248 does not create manifest / fixture / report / directory\n"
        "- TASK-248 does not copy external evidence\n"
        "- TASK-248 does not modify official manifest / backtest/sets\n"
        "- TASK-248 does not add MQ5 / MQH files\n"
        "- TASK-248 does not commit\n\n"
        "## TASK-249 implement MQ5 read-only metrics aggregation & historical events contract\n\n"
        "- current task is TASK-249 implement MQ5 read-only metrics aggregation & historical events contract\n"
        "- TASK-249 is a low-risk MQ5 implementation slice\n"
        "- TASK-249 implementation scope is limited to read-only metrics aggregation & historical events contract\n"
        "- TASK-248 completed no-trade safety guard invariant contract\n"
        "- TASK-248 commit is 26ecbfe TASK-248 implement no-trade safety guard invariant contract\n"
        "- TASK-248 tag is v0.5.50-task-248-no-trade-safety-guard-invariant\n"
        "- current HEAD is 26ecbfe TASK-248 implement no-trade safety guard invariant contract\n"
        "- current latest tag is v0.5.50-task-248-no-trade-safety-guard-invariant\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only metrics aggregation & historical events contract records metrics_aggregation_snapshot=true\n"
        "- read-only metrics aggregation & historical events contract records historical_events_count\n"
        "- read-only metrics aggregation & historical events contract records last_n_ticks_metrics\n"
        "- read-only metrics aggregation & historical events contract records aggregated_component_status\n"
        "- read-only metrics aggregation & historical events contract records no_trade_guard=active\n"
        "- read-only metrics aggregation & historical events contract records trading_authorization=false\n"
        "- read-only metrics aggregation & historical events contract records mt5_run_required=false\n"
        "- read-only metrics aggregation & historical events contract records evidence_generation=false\n"
        "- read-only metrics aggregation & historical events contract records manifest_generation=false\n"
        "- read-only metrics aggregation & historical events contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-249 does not run MT5\n"
        "- TASK-249 does not run backtest\n"
        "- TASK-249 does not enter real trading\n"
        "- TASK-249 does not enter simulated trading\n"
        "- TASK-249 does not send orders\n"
        "- TASK-249 does not create manifest / fixture / report / directory\n"
        "- TASK-249 does not copy external evidence\n"
        "- TASK-249 does not modify official manifest / backtest/sets\n"
        "- TASK-249 does not add MQ5 / MQH files\n"
        "- TASK-249 does not commit\n\n"
        "## TASK-250 implement MQ5 read-only system health & observability summary contract\n\n"
        "- current task is TASK-250 implement MQ5 read-only system health & observability summary contract\n"
        "- TASK-250 is a low-risk MQ5 implementation slice\n"
        "- TASK-250 implementation scope is limited to read-only system health & observability summary contract\n"
        "- TASK-249 completed read-only metrics aggregation & historical events contract\n"
        "- TASK-249 commit is 1ad896a TASK-249 implement read-only metrics aggregation & historical events contract\n"
        "- TASK-249 tag is v0.5.51-task-249-read-only-metrics-aggregation\n"
        "- current HEAD is 1ad896a TASK-249 implement read-only metrics aggregation & historical events contract\n"
        "- current latest tag is v0.5.51-task-249-read-only-metrics-aggregation\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only system health & observability summary contract records system_health_snapshot=true\n"
        "- read-only system health & observability summary contract records observability_enabled\n"
        "- read-only system health & observability summary contract records last_snapshot_timestamp\n"
        "- read-only system health & observability summary contract records aggregated_component_status\n"
        "- read-only system health & observability summary contract records all_components_no_trade=true\n"
        "- read-only system health & observability summary contract records trading_authorization=false\n"
        "- read-only system health & observability summary contract records mt5_run_required=false\n"
        "- read-only system health & observability summary contract records evidence_generation=false\n"
        "- read-only system health & observability summary contract records manifest_generation=false\n"
        "- read-only system health & observability summary contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-250 does not run MT5\n"
        "- TASK-250 does not run backtest\n"
        "- TASK-250 does not enter real trading\n"
        "- TASK-250 does not enter simulated trading\n"
        "- TASK-250 does not send orders\n"
        "- TASK-250 does not create manifest / fixture / report / directory\n"
        "- TASK-250 does not copy external evidence\n"
        "- TASK-250 does not modify official manifest / backtest/sets\n"
        "- TASK-250 does not add MQ5 / MQH files\n"
        "- TASK-250 does not commit\n\n"
        "## TASK-251 implement MQ5 read-only signal context snapshot contract\n\n"
        "- current task is TASK-251 implement MQ5 read-only signal context snapshot contract\n"
        "- TASK-251 is a low-risk MQ5 implementation slice\n"
        "- TASK-251 implementation scope is limited to read-only signal context snapshot contract\n"
        "- TASK-250 completed read-only system health & observability summary contract\n"
        "- TASK-250 commit is d50c34b TASK-250 implement read-only system health & observability summary contract\n"
        "- TASK-250 tag is v0.5.52-task-250-read-only-system-health-observability\n"
        "- current HEAD is d50c34b TASK-250 implement read-only system health & observability summary contract\n"
        "- current latest tag is v0.5.52-task-250-read-only-system-health-observability\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only signal context snapshot contract records signal_context_snapshot=true\n"
        "- read-only signal context snapshot contract records signal_layer_mode=read-only framework\n"
        "- read-only signal context snapshot contract records signal_context_available=true\n"
        "- read-only signal context snapshot contract records signal_direction_authorized=false\n"
        "- read-only signal context snapshot contract records signal_execution_authorized=false\n"
        "- read-only signal context snapshot contract records signal_order_intent=false\n"
        "- read-only signal context snapshot contract records signal_external_evidence_required=false\n"
        "- read-only signal context snapshot contract records signal_manifest_generation=false\n"
        "- read-only signal context snapshot contract records no_trade_guard=active\n"
        "- read-only signal context snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-251 does not run MT5\n"
        "- TASK-251 does not run backtest\n"
        "- TASK-251 does not enter real trading\n"
        "- TASK-251 does not enter simulated trading\n"
        "- TASK-251 does not send orders\n"
        "- TASK-251 does not create manifest / fixture / report / directory\n"
        "- TASK-251 does not copy external evidence\n"
        "- TASK-251 does not modify official manifest / backtest/sets\n"
        "- TASK-251 does not add MQ5 / MQH files\n"
        "- TASK-251 does not commit\n\n"
        "## TASK-252 implement MQ5 read-only risk context snapshot contract\n\n"
        "- current task is TASK-252 implement MQ5 read-only risk context snapshot contract\n"
        "- TASK-252 is a low-risk MQ5 implementation slice\n"
        "- TASK-252 implementation scope is limited to read-only risk context snapshot contract\n"
        "- TASK-251 completed read-only signal context snapshot contract\n"
        "- TASK-251 commit is 56a8fae TASK-251 implement read-only signal context snapshot contract\n"
        "- TASK-251 tag is v0.5.53-task-251-read-only-signal-context\n"
        "- current HEAD is 56a8fae TASK-251 implement read-only signal context snapshot contract\n"
        "- current latest tag is v0.5.53-task-251-read-only-signal-context\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only risk context snapshot contract records risk_context_snapshot=true\n"
        "- read-only risk context snapshot contract records risk_layer_mode=read-only framework\n"
        "- read-only risk context snapshot contract records risk_context_available=true\n"
        "- read-only risk context snapshot contract records risk_authorization=false\n"
        "- read-only risk context snapshot contract records risk_sizing_authorized=false\n"
        "- read-only risk context snapshot contract records risk_exposure_authorized=false\n"
        "- read-only risk context snapshot contract records risk_execution_authorized=false\n"
        "- read-only risk context snapshot contract records risk_external_evidence_required=false\n"
        "- read-only risk context snapshot contract records risk_manifest_generation=false\n"
        "- read-only risk context snapshot contract records no_trade_guard=active\n"
        "- read-only risk context snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-252 does not run MT5\n"
        "- TASK-252 does not run backtest\n"
        "- TASK-252 does not enter real trading\n"
        "- TASK-252 does not enter simulated trading\n"
        "- TASK-252 does not send orders\n"
        "- TASK-252 does not create manifest / fixture / report / directory\n"
        "- TASK-252 does not copy external evidence\n"
        "- TASK-252 does not modify official manifest / backtest/sets\n"
        "- TASK-252 does not add MQ5 / MQH files\n"
        "- TASK-252 does not commit\n\n"
        "## TASK-253 implement MQ5 read-only execution context snapshot contract\n\n"
        "- current task is TASK-253 implement MQ5 read-only execution context snapshot contract\n"
        "- TASK-253 is a low-risk MQ5 implementation slice\n"
        "- TASK-253 implementation scope is limited to read-only execution context snapshot contract\n"
        "- TASK-252 completed read-only risk context snapshot contract\n"
        "- TASK-252 commit is 3dd463d TASK-252 implement read-only risk context snapshot contract\n"
        "- TASK-252 tag is v0.5.54-task-252-read-only-risk-context\n"
        "- current HEAD is 3dd463d TASK-252 implement read-only risk context snapshot contract\n"
        "- current latest tag is v0.5.54-task-252-read-only-risk-context\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only execution context snapshot contract records execution_context_snapshot=true\n"
        "- read-only execution context snapshot contract records execution_layer_mode=read-only framework\n"
        "- read-only execution context snapshot contract records execution_context_available=true\n"
        "- read-only execution context snapshot contract records execution_authorization=false\n"
        "- read-only execution context snapshot contract records execution_request_authorized=false\n"
        "- read-only execution context snapshot contract records execution_route_authorized=false\n"
        "- read-only execution context snapshot contract records execution_dispatch_authorized=false\n"
        "- read-only execution context snapshot contract records execution_external_evidence_required=false\n"
        "- read-only execution context snapshot contract records execution_manifest_generation=false\n"
        "- read-only execution context snapshot contract records no_trade_guard=active\n"
        "- read-only execution context snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-253 does not run MT5\n"
        "- TASK-253 does not run backtest\n"
        "- TASK-253 does not enter real trading\n"
        "- TASK-253 does not enter simulated trading\n"
        "- TASK-253 does not send orders\n"
        "- TASK-253 does not create manifest / fixture / report / directory\n"
        "- TASK-253 does not copy external evidence\n"
        "- TASK-253 does not modify official manifest / backtest/sets\n"
        "- TASK-253 does not add MQ5 / MQH files\n"
        "- TASK-253 does not commit\n\n"
        "## TASK-DOC-254 update project state docs after TASK-253\n\n"
        "- current task is TASK-DOC-254 update project state docs after TASK-253\n"
        "- TASK-DOC-254 is a project state docs sync task\n"
        "- TASK-253 completed read-only execution context snapshot contract\n"
        "- TASK-253 commit is 7773a2f TASK-253 implement read-only execution context snapshot contract\n"
        "- TASK-253 tag is v0.5.55-task-253-read-only-execution-context\n"
        "- current HEAD is 7773a2f TASK-253 implement read-only execution context snapshot contract\n"
        "- current latest tag is v0.5.55-task-253-read-only-execution-context\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only execution context snapshot contract is synced to project state docs\n"
        "- read-only execution context snapshot contract fields remain execution_context_snapshot=true\n"
        "- read-only execution context snapshot contract fields remain execution_layer_mode=read-only framework\n"
        "- read-only execution context snapshot contract fields remain execution_context_available=true\n"
        "- read-only execution context snapshot contract fields remain execution_authorization=false\n"
        "- read-only execution context snapshot contract fields remain execution_request_authorized=false\n"
        "- read-only execution context snapshot contract fields remain execution_route_authorized=false\n"
        "- read-only execution context snapshot contract fields remain execution_dispatch_authorized=false\n"
        "- read-only execution context snapshot contract fields remain execution_external_evidence_required=false\n"
        "- read-only execution context snapshot contract fields remain execution_manifest_generation=false\n"
        "- read-only execution context snapshot contract fields remain no_trade_guard=active\n"
        "- validate_mq5_no_trade_observability.py covers TASK-253 execution context fields and controller path\n"
        "- test_validate_mq5_no_trade_observability.py covers TASK-253 execution context fields and controller path\n"
        "- MQ5 inventory remains 7 files\n"
        "- trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory created\n"
        "- no external evidence copied\n"
        "- official manifest remains unchanged\n"
        "- backtest/sets remains unchanged\n"
        "- high-efficiency mode remains active\n"
        "- GPT defines boundaries\n"
        "- Codex modifies allowed files only and does not commit for this task\n"
        "- Trae reviews, validates, commits, tags, and audits when explicitly assigned\n"
        "- TASK-DOC-254 does not modify MQ5\n"
        "- TASK-DOC-254 does not run MT5\n"
        "- TASK-DOC-254 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-254 does not copy external evidence\n"
        "- TASK-DOC-254 does not commit\n"
        "## TASK-255 implement MQ5 read-only pipeline context aggregation snapshot contract\n\n"
        "- current task is TASK-255 implement MQ5 read-only pipeline context aggregation snapshot contract\n"
        "- TASK-255 is a low-risk MQ5 implementation slice\n"
        "- TASK-255 implementation scope is limited to read-only pipeline context aggregation snapshot contract\n"
        "- TASK-DOC-254 completed project state docs sync after TASK-253\n"
        "- TASK-DOC-254 commit is 44369dd TASK-DOC-254 update project state docs after TASK-253\n"
        "- TASK-DOC-254 tag is v0.5.56-task-254-sync-task-253-state\n"
        "- current HEAD is 44369dd TASK-DOC-254 update project state docs after TASK-253\n"
        "- current latest tag is v0.5.56-task-254-sync-task-253-state\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_context_snapshot=true\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_layer_mode=read-only framework\n"
        "- read-only pipeline context aggregation snapshot contract records signal_context_linked=true\n"
        "- read-only pipeline context aggregation snapshot contract records risk_context_linked=true\n"
        "- read-only pipeline context aggregation snapshot contract records execution_context_linked=true\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_authorization=false\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_direction_authorized=false\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_risk_authorized=false\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_execution_authorized=false\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_dispatch_authorized=false\n"
        "- read-only pipeline context aggregation snapshot contract records pipeline_intent=false\n"
        "- read-only pipeline context aggregation snapshot contract records all_pipeline_layers_no_trade=true\n"
        "- read-only pipeline context aggregation snapshot contract records no_trade_guard=active\n"
        "- read-only pipeline context aggregation snapshot contract records trading_authorization=false\n"
        "- read-only pipeline context aggregation snapshot contract records mt5_run_required=false\n"
        "- read-only pipeline context aggregation snapshot contract records evidence_generation=false\n"
        "- read-only pipeline context aggregation snapshot contract records manifest_generation=false\n"
        "- read-only pipeline context aggregation snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- TASK-255 does not run MT5\n"
        "- TASK-255 does not run backtest\n"
        "- TASK-255 does not enter real trading\n"
        "- TASK-255 does not enter simulated trading\n"
        "- TASK-255 does not send orders\n"
        "- TASK-255 does not create manifest / fixture / report / directory\n"
        "- TASK-255 does not copy external evidence\n"
        "- TASK-255 does not modify official manifest / backtest/sets\n"
        "- TASK-255 does not add MQ5 / MQH files\n"
        "- TASK-255 does not commit\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-DOC-256 update state after TASK-255\n\n"
        "- current task is TASK-DOC-256 update state after TASK-255\n"
        "- TASK-DOC-256 is a doc-only project state sync task\n"
        "- TASK-255 completed read-only pipeline context aggregation snapshot contract\n"
        "- TASK-255 commit is fc215ea TASK-255 implement read-only pipeline context aggregation snapshot contract\n"
        "- TASK-255 tag is v0.5.57-task-255-read-only-pipeline-context\n"
        "- current HEAD is fc215ea TASK-255 implement read-only pipeline context aggregation snapshot contract\n"
        "- current latest tag is v0.5.57-task-255-read-only-pipeline-context\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only pipeline context aggregation snapshot contract is synced to project state docs\n"
        "- MQ5 inventory remains 7 files\n"
        "- mq5-no-trade-observability PASS\n"
        "- mq5-inventory PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-DOC-256 confirms MQ5 inventory remains 7 files\n"
        "- TASK-DOC-256 confirms no MT5 run\n"
        "- TASK-DOC-256 confirms no trading authorization\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory created\n"
        "- no external evidence copied\n"
        "- official manifest remains unchanged\n"
        "- backtest/sets remains unchanged\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- TASK-DOC-256 does not modify MQ5\n"
        "- TASK-DOC-256 does not modify MQH\n"
        "- TASK-DOC-256 does not run MT5\n"
        "- TASK-DOC-256 does not run backtest\n"
        "- TASK-DOC-256 does not enter simulated trading\n"
        "- TASK-DOC-256 does not enter real trading\n"
        "- TASK-DOC-256 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-256 does not copy external evidence\n"
        "- TASK-DOC-256 does not commit\n"
        "- TASK-DOC-256 does not create tag\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-257 implement MQ5 read-only authorization matrix snapshot contract\n\n"
        "- current task is TASK-257 implement MQ5 read-only authorization matrix snapshot contract\n"
        "- TASK-257 is a low-risk MQ5 implementation slice\n"
        "- TASK-257 implementation scope is limited to read-only authorization matrix snapshot contract\n"
        "- TASK-DOC-256 completed project state docs sync after TASK-255\n"
        "- TASK-DOC-256 commit is 678a77f TASK-DOC-256 update state after TASK-255\n"
        "- TASK-DOC-256 tag is v0.5.58-task-256-sync-task-255-state\n"
        "- current HEAD is 678a77f TASK-DOC-256 update state after TASK-255\n"
        "- current latest tag is v0.5.58-task-256-sync-task-255-state\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only authorization matrix snapshot contract records authorization_matrix_snapshot=true\n"
        "- read-only authorization matrix snapshot contract records authorization_matrix_mode=read-only framework\n"
        "- read-only authorization matrix snapshot contract records signal_authorization=false\n"
        "- read-only authorization matrix snapshot contract records signal_direction_authorized=false\n"
        "- read-only authorization matrix snapshot contract records risk_authorization=false\n"
        "- read-only authorization matrix snapshot contract records risk_sizing_authorized=false\n"
        "- read-only authorization matrix snapshot contract records risk_exposure_authorized=false\n"
        "- read-only authorization matrix snapshot contract records execution_authorization=false\n"
        "- read-only authorization matrix snapshot contract records execution_request_authorized=false\n"
        "- read-only authorization matrix snapshot contract records execution_dispatch_authorized=false\n"
        "- read-only authorization matrix snapshot contract records pipeline_authorization=false\n"
        "- read-only authorization matrix snapshot contract records pipeline_intent=false\n"
        "- read-only authorization matrix snapshot contract records trading_authorization=false\n"
        "- read-only authorization matrix snapshot contract records all_authorizations_false=true\n"
        "- read-only authorization matrix snapshot contract records all_pipeline_layers_no_trade=true\n"
        "- read-only authorization matrix snapshot contract records no_trade_guard=active\n"
        "- read-only authorization matrix snapshot contract records mt5_run_required=false\n"
        "- read-only authorization matrix snapshot contract records evidence_generation=false\n"
        "- read-only authorization matrix snapshot contract records manifest_generation=false\n"
        "- read-only authorization matrix snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade\n"
        "- TASK-257 does not run MT5\n"
        "- TASK-257 does not create manifest / fixture / report / directory\n"
        "- TASK-257 does not copy external evidence\n"
        "- TASK-257 does not add MQ5 / MQH files\n"
        "- TASK-257 does not commit\n"
        "- no more doc-only completion chain; continue directly with low-risk no-trade implementation slice only when ChatGPT defines the boundary\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-258 implement MQ5 read-only decision gate snapshot contract\n\n"
        "- current task is TASK-258 implement MQ5 read-only decision gate snapshot contract\n"
        "- TASK-258 is a low-risk MQ5 implementation slice\n"
        "- TASK-258 implementation scope is limited to read-only decision gate snapshot contract\n"
        "- TASK-257 completed read-only authorization matrix snapshot contract\n"
        "- TASK-257 commit is 950a71e TASK-257 implement read-only authorization matrix snapshot contract\n"
        "- TASK-257 tag is v0.5.59-task-257-read-only-authorization-matrix\n"
        "- current HEAD is 950a71e TASK-257 implement read-only authorization matrix snapshot contract\n"
        "- current latest tag is v0.5.59-task-257-read-only-authorization-matrix\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only decision gate snapshot contract records decision_gate_snapshot=true\n"
        "- read-only decision gate snapshot contract records decision_gate_mode=read-only framework\n"
        "- read-only decision gate snapshot contract records decision_state=blocked_no_trade\n"
        "- read-only decision gate snapshot contract records decision_candidate_available=false\n"
        "- read-only decision gate snapshot contract records decision_direction_authorized=false\n"
        "- read-only decision gate snapshot contract records decision_risk_authorized=false\n"
        "- read-only decision gate snapshot contract records decision_execution_authorized=false\n"
        "- read-only decision gate snapshot contract records decision_dispatch_authorized=false\n"
        "- read-only decision gate snapshot contract records decision_output_authorized=false\n"
        "- read-only decision gate snapshot contract records decision_intent=false\n"
        "- read-only decision gate snapshot contract records all_authorizations_false=true\n"
        "- read-only decision gate snapshot contract records all_pipeline_layers_no_trade=true\n"
        "- read-only decision gate snapshot contract records no_trade_guard=active\n"
        "- read-only decision gate snapshot contract records trading_authorization=false\n"
        "- read-only decision gate snapshot contract records mt5_run_required=false\n"
        "- read-only decision gate snapshot contract records evidence_generation=false\n"
        "- read-only decision gate snapshot contract records manifest_generation=false\n"
        "- read-only decision gate snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade\n"
        "- TASK-258 does not run MT5\n"
        "- TASK-258 does not create manifest / fixture / report / directory\n"
        "- TASK-258 does not copy external evidence\n"
        "- TASK-258 does not add MQ5 / MQH files\n"
        "- TASK-258 does not commit\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-259 implement MQ5 read-only decision rejection reason snapshot contract\n\n"
        "- current task is TASK-259 implement MQ5 read-only decision rejection reason snapshot contract\n"
        "- TASK-259 is a low-risk MQ5 implementation slice\n"
        "- TASK-259 implementation scope is limited to read-only decision rejection reason snapshot contract\n"
        "- TASK-258 completed read-only decision gate snapshot contract\n"
        "- TASK-258 commit is f1f53e6 TASK-258 implement read-only decision gate snapshot contract\n"
        "- TASK-258 tag is v0.5.60-task-258-read-only-decision-gate\n"
        "- current HEAD is f1f53e6 TASK-258 implement read-only decision gate snapshot contract\n"
        "- current latest tag is v0.5.60-task-258-read-only-decision-gate\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- read-only decision rejection reason snapshot contract records decision_rejection_snapshot=true\n"
        "- read-only decision rejection reason snapshot contract records decision_rejection_mode=read-only framework\n"
        "- read-only decision rejection reason snapshot contract records rejection_reason=no_trade_guard_active\n"
        "- read-only decision rejection reason snapshot contract records rejection_trading_authorization=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_signal_authorization=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_risk_authorization=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_execution_authorization=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_pipeline_authorization=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_external_evidence=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_manifest_generation=false\n"
        "- read-only decision rejection reason snapshot contract records rejection_mt5_run_required=false\n"
        "- read-only decision rejection reason snapshot contract records decision_state=blocked_no_trade\n"
        "- read-only decision rejection reason snapshot contract records decision_intent=false\n"
        "- read-only decision rejection reason snapshot contract records all_authorizations_false=true\n"
        "- read-only decision rejection reason snapshot contract records no_trade_guard=active\n"
        "- read-only decision rejection reason snapshot contract records trading_authorization=false\n"
        "- read-only decision rejection reason snapshot contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- MQ5 inventory must remain 7 files\n"
        "- v0.6.0 implementation slices remain limited to no-trade scaffold / static validation\n"
        "- MQ5 inventory and no-trade observability contract must continue PASS\n"
        "- trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade\n"
        "- TASK-259 does not run MT5\n"
        "- TASK-259 does not create manifest / fixture / report / directory\n"
        "- TASK-259 does not copy external evidence\n"
        "- TASK-259 does not add MQ5 / MQH files\n"
        "- TASK-259 does not commit\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-DOC-260 create first observability extension planning packet\n\n"
        "- current task is TASK-DOC-260 create first observability extension planning packet\n"
        "- TASK-DOC-260 is planning-only\n"
        "- TASK-DOC-260 creates docs/V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md\n"
        "- TASK-DOC-260 does not authorize implementation\n"
        "- TASK-259 completed read-only decision rejection reason snapshot contract\n"
        "- TASK-259 commit is 6451e78 TASK-259 implement read-only decision rejection reason snapshot contract\n"
        "- TASK-259 tag is v0.5.61-task-259-read-only-decision-rejection-reason\n"
        "- current HEAD is 6451e78 TASK-259 implement read-only decision rejection reason snapshot contract\n"
        "- current latest tag is v0.5.61-task-259-read-only-decision-rejection-reason\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- first observability extension planning packet is future candidate only\n"
        "- no-trade observability extension remains planning-only\n"
        "- not implementation authorization\n"
        "- MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-DOC-260 does not modify MQ5 / MQH\n"
        "- TASK-DOC-260 does not run MT5\n"
        "- TASK-DOC-260 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-260 does not copy external evidence\n"
        "- TASK-DOC-260 does not commit\n"
        "- TASK-DOC-260 does not tag\n"
        "- TASK-261 must not be entered directly\n"
        "- GPT must define a separate future TASK-261 boundary\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter TASK-261, MT5 run, trading, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-DOC-261 create next observability extension planning packet\n\n"
        "- current task is TASK-DOC-261 create next observability extension planning packet\n"
        "- TASK-DOC-261 is planning-only\n"
        "- TASK-DOC-261 creates docs/V060_TASK_261_OBSERVABILITY_EXTENSION_NEXT_PLAN.md\n"
        "- TASK-DOC-261 does not authorize implementation\n"
        "- TASK-DOC-260 completed first observability extension planning packet\n"
        "- TASK-DOC-260 commit is cb7675f TASK-DOC-260 create first observability extension planning packet\n"
        "- TASK-DOC-260 tag is v0.5.62-task-260-first-observability-extension-plan\n"
        "- current HEAD is cb7675f TASK-DOC-260 create first observability extension planning packet\n"
        "- current latest tag is v0.5.62-task-260-first-observability-extension-plan\n"
        "- current phase remains v0.5.0 with v0.6.0 low-risk implementation slices in progress\n"
        "- next observability extension planning packet is future candidate only\n"
        "- no-trade observability extension remains planning-only\n"
        "- no-trade scaffold remains the active safety boundary\n"
        "- not implementation authorization\n"
        "- MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-DOC-261 does not modify MQ5 / MQH\n"
        "- TASK-DOC-261 does not run MT5\n"
        "- TASK-DOC-261 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-261 does not copy external evidence\n"
        "- TASK-DOC-261 does not commit\n"
        "- TASK-DOC-261 does not tag\n"
        "- TASK-262 must not be entered directly\n"
        "- GPT must define a separate future boundary before TASK-262\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter TASK-262, MT5 run, trading, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-DOC-262 create follow-up observability extension planning packet\n\n"
        "- current task is TASK-DOC-262 create follow-up observability extension planning packet\n"
        "- TASK-DOC-262 is planning-only\n"
        "- TASK-DOC-262 creates docs/V060_TASK_262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN.md\n"
        "- TASK-DOC-262 does not authorize implementation\n"
        "- TASK-DOC-261 completed next observability extension planning packet\n"
        "- TASK-DOC-261 commit is 527486d TASK-DOC-261 create next observability extension planning packet\n"
        "- TASK-DOC-261 tag is v0.5.63-task-261-observability-extension-next-plan\n"
        "- current HEAD is 527486d TASK-DOC-261 create next observability extension planning packet\n"
        "- current latest tag is v0.5.63-task-261-observability-extension-next-plan\n"
        "- follow-up observability extension planning packet is future candidate only\n"
        "- no-trade observability extension remains planning-only\n"
        "- not implementation authorization\n"
        "- MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-DOC-262 does not modify MQ5 / MQH\n"
        "- TASK-DOC-262 does not run MT5\n"
        "- TASK-DOC-262 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-262 does not copy external evidence\n"
        "- TASK-DOC-262 does not commit\n"
        "- TASK-DOC-262 does not tag\n"
        "- TASK-263 must not be entered directly\n"
        "- GPT must define a separate future boundary before TASK-263\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter TASK-263, MT5 run, trading, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-DOC-263 create future observability extension planning packet\n\n"
        "- current task is TASK-DOC-263 create future observability extension planning packet\n"
        "- TASK-DOC-263 is planning-only\n"
        "- TASK-DOC-263 creates docs/V060_TASK_263_OBSERVABILITY_EXTENSION_FUTURE_PLAN.md\n"
        "- TASK-DOC-263 does not authorize implementation\n"
        "- TASK-DOC-262 completed follow-up observability extension planning packet\n"
        "- TASK-DOC-262 commit is 69f12a6 TASK-DOC-262 create follow-up observability extension planning packet\n"
        "- TASK-DOC-262 tag is v0.5.64-task-262-observability-extension-followup-plan\n"
        "- current HEAD is 69f12a6 TASK-DOC-262 create follow-up observability extension planning packet\n"
        "- current latest tag is v0.5.64-task-262-observability-extension-followup-plan\n"
        "- future observability extension planning packet is future candidate only\n"
        "- no-trade observability extension remains planning-only\n"
        "- not implementation authorization\n"
        "- MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-DOC-263 does not modify MQ5 / MQH\n"
        "- TASK-DOC-263 does not run MT5\n"
        "- TASK-DOC-263 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-263 does not copy external evidence\n"
        "- TASK-DOC-263 does not commit\n"
        "- TASK-DOC-263 does not tag\n"
        "- TASK-264 must not be entered directly\n"
        "- GPT must define a separate future boundary before TASK-264\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter TASK-264, MT5 run, trading, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-264 implement MQ5 read-only observability consolidation contract\n\n"
        "- current task is TASK-264 implement MQ5 read-only observability consolidation contract\n"
        "- TASK-264 is a low-risk MQ5 implementation slice\n"
        "- TASK-264 is not a planning packet\n"
        "- TASK-264 must not continue planning packet chain\n"
        "- TASK-DOC-263 completed future observability extension planning packet\n"
        "- TASK-DOC-263 commit is d7fe9b6 TASK-DOC-263 create future observability extension planning packet\n"
        "- TASK-DOC-263 tag is v0.5.65-task-263-observability-extension-future-plan\n"
        "- current HEAD is d7fe9b6 TASK-DOC-263 create future observability extension planning packet\n"
        "- current latest tag is v0.5.65-task-263-observability-extension-future-plan\n"
        "- implementation scope is limited to read-only observability consolidation contract\n"
        "- no-trade scaffold remains the active safety boundary\n"
        "- static validation remains required\n"
        "- MQ5 inventory remains 7 files\n"
        "- TASK-264 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-264 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-264 does not run MT5\n"
        "- TASK-264 does not run backtest\n"
        "- TASK-264 does not enter simulated trading\n"
        "- TASK-264 does not enter real trading\n"
        "- TASK-264 does not create manifest / fixture / report / directory\n"
        "- TASK-264 does not copy external evidence\n"
        "- TASK-264 does not modify official manifest / backtest/sets\n"
        "- TASK-264 does not add MQ5 / MQH files\n"
        "- TASK-264 does not commit\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-265 implement MQ5 read-only observability contract registry snapshot\n\n"
        "- current task is TASK-265 implement MQ5 read-only observability contract registry snapshot\n"
        "- TASK-265 is a low-risk MQ5 implementation slice\n"
        "- TASK-265 does not create a new planning packet\n"
        "- TASK-264 completed read-only observability consolidation contract\n"
        "- TASK-264 commit is 40896e9 TASK-264 implement read-only observability consolidation contract\n"
        "- TASK-264 tag is v0.5.66-task-264-read-only-observability-consolidation\n"
        "- current HEAD is 40896e9 TASK-264 implement read-only observability consolidation contract\n"
        "- current latest tag is v0.5.66-task-264-read-only-observability-consolidation\n"
        "- implementation scope is limited to read-only observability contract registry snapshot\n"
        "- no-trade scaffold remains the active safety boundary\n"
        "- static validation remains required\n"
        "- MQ5 inventory remains 7 files\n"
        "- TASK-265 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-265 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- TASK-265 does not run MT5\n"
        "- TASK-265 does not run backtest\n"
        "- TASK-265 does not enter simulated trading\n"
        "- TASK-265 does not enter real trading\n"
        "- TASK-265 does not create manifest / fixture / report / directory\n"
        "- TASK-265 does not copy external evidence\n"
        "- TASK-265 does not modify official manifest / backtest/sets\n"
        "- TASK-265 does not add MQ5 / MQH files\n"
        "- TASK-265 does not commit\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-266 implement fast no-trade development validation profile\n\n"
        "- current task is TASK-266 implement fast no-trade development validation profile\n"
        "- TASK-266 implement fast no-trade development validation profile\n"
        "- TASK-266 is a tooling efficiency task\n"
        "- TASK-266 is tooling + docs + self-test update\n"
        "- TASK-266 does not modify MQ5 / MQH\n"
        "- TASK-266 does not run MT5\n"
        "- TASK-266 does not create manifest / fixture / report / directory\n"
        "- TASK-266 does not copy external evidence\n"
        "- TASK-266 does not commit\n"
        "- TASK-265 completed read-only observability contract registry snapshot\n"
        "- TASK-265 commit is 139265d TASK-265 implement read-only observability contract registry snapshot\n"
        "- TASK-265 tag is v0.5.67-task-265-observability-contract-registry\n"
        "- current HEAD is 139265d TASK-265 implement read-only observability contract registry snapshot\n"
        "- current latest tag is v0.5.67-task-265-observability-contract-registry\n"
        "- implementation scope is limited to fast no-trade development validation profile\n"
        "- new profile is fast-no-trade-dev\n"
        "- fast no-trade development validation profile\n"
        "- python tools/run_release_validation_bundle.py --profile fast-no-trade-dev\n"
        "- no-trade scaffold remains the active safety boundary\n"
        "- static validation remains required\n"
        "- MQ5 inventory remains 7 files\n"
        "- TASK-266 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- v060-implementation-boundary PASS\n"
        "- v060-implementation-readiness PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-266 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-267 implement one-command fast no-trade preflight runner\n\n"
        "- current task is TASK-267 implement one-command fast no-trade preflight runner\n"
        "- TASK-267 implement one-command fast no-trade preflight runner\n"
        "- TASK-267 is a tooling efficiency task\n"
        "- TASK-267 is tooling + docs + self-test update\n"
        "- TASK-266 completed fast no-trade development validation profile\n"
        "- TASK-266 commit is f23ce3e TASK-266 implement fast no-trade development validation profile\n"
        "- TASK-266 tag is v0.5.68-task-266-fast-no-trade-dev-profile\n"
        "- current HEAD is f23ce3e TASK-266 implement fast no-trade development validation profile\n"
        "- current latest tag is v0.5.68-task-266-fast-no-trade-dev-profile\n"
        "- implementation scope is limited to one-command fast no-trade preflight runner\n"
        "- new runner is tools/run_fast_no_trade_preflight.py\n"
        "- one-command fast no-trade preflight runner\n"
        "- python tools/run_fast_no_trade_preflight.py\n"
        "- fast-no-trade-dev profile remains the default release validation profile\n"
        "- runner supports --doc-only\n"
        "- runner supports --strict-mq5\n"
        "- runner supports --skip-profile\n"
        "- TASK-267 does not modify MQ5 / MQH\n"
        "- TASK-267 does not run MT5\n"
        "- TASK-267 does not run backtest\n"
        "- TASK-267 does not enter simulated trading\n"
        "- TASK-267 does not enter real trading\n"
        "- TASK-267 does not create manifest / fixture / report / directory\n"
        "- TASK-267 does not copy external evidence\n"
        "- TASK-267 does not commit\n"
        "- MQ5 inventory remains 7 files\n"
        "- TASK-267 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- fast-no-trade-dev profile PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-267 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-268 implement allowed-change guard for fast no-trade preflight\n\n"
        "- current task is TASK-268 implement allowed-change guard for fast no-trade preflight\n"
        "- TASK-268 implement allowed-change guard for fast no-trade preflight\n"
        "- TASK-268 is a tooling efficiency task\n"
        "- TASK-268 is tooling + docs + self-test update\n"
        "- TASK-267 completed one-command fast no-trade preflight runner\n"
        "- TASK-267 commit is 1f2de5c TASK-267 implement one-command fast no-trade preflight runner\n"
        "- TASK-267 tag is v0.5.69-task-267-fast-no-trade-preflight\n"
        "- current HEAD is 1f2de5c TASK-267 implement one-command fast no-trade preflight runner\n"
        "- current latest tag is v0.5.69-task-267-fast-no-trade-preflight\n"
        "- implementation scope is limited to allowed-change guard for fast no-trade preflight\n"
        "- allowed-change guard\n"
        "- new guard remains in tools/run_fast_no_trade_preflight.py\n"
        "- run_fast_no_trade_preflight.py\n"
        "- --check-allowed-changes\n"
        "- --allow\n"
        "- --allow-prefix\n"
        "- fast-no-trade-dev profile remains the default release validation profile\n"
        "- TASK-268 does not modify MQ5 / MQH\n"
        "- TASK-268 does not run MT5\n"
        "- TASK-268 does not run backtest\n"
        "- TASK-268 does not enter simulated trading\n"
        "- TASK-268 does not enter real trading\n"
        "- TASK-268 does not create manifest / fixture / report / directory\n"
        "- TASK-268 does not copy external evidence\n"
        "- TASK-268 does not commit\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-268 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- fast-no-trade-dev profile PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-268 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-269 implement read-only observability error/exception logging contract\n\n"
        "- current task is TASK-269 implement read-only observability error/exception logging contract\n"
        "- TASK-269 implement read-only observability error/exception logging contract\n"
        "- TASK-269 is a low-risk MQ5 implementation slice\n"
        "- TASK-269 implementation scope is limited to read-only observability error/exception logging contract\n"
        "- TASK-268 completed allowed-change guard for fast no-trade preflight\n"
        "- TASK-268 commit is a0f0200 TASK-268 implement allowed-change guard for fast no-trade preflight\n"
        "- TASK-268 tag is v0.5.70-task-268-fast-no-trade-allowed-change-guard\n"
        "- current HEAD is a0f0200 TASK-268 implement allowed-change guard for fast no-trade preflight\n"
        "- current latest tag is v0.5.70-task-268-fast-no-trade-allowed-change-guard\n"
        "- read-only observability error/exception logging contract records error_snapshot=true\n"
        "- read-only observability error/exception logging contract records error_type=read-only framework\n"
        "- read-only observability error/exception logging contract records error_timestamp\n"
        "- read-only observability error/exception logging contract records component_origin\n"
        "- read-only observability error/exception logging contract records error_details\n"
        "- read-only observability error/exception logging contract records all_observability_outputs_read_only=true\n"
        "- read-only observability error/exception logging contract records all_authorizations_false=true\n"
        "- read-only observability error/exception logging contract records no_trade_guard=active\n"
        "- read-only observability error/exception logging contract records trading_authorization=false\n"
        "- read-only observability error/exception logging contract records mt5_run_required=false\n"
        "- read-only observability error/exception logging contract records evidence_generation=false\n"
        "- read-only observability error/exception logging contract records manifest_generation=false\n"
        "- read-only observability error/exception logging contract records Inventory only; no MT5 run; no trading authorization.\n"
        "- LogReadOnlyObservabilityErrorSnapshot\n"
        "- OnTick error/exception logging remains gated by InpObservabilityLogOnTick\n"
        "- TASK-269 preserves TASK-243 through TASK-268 no-trade observability outputs\n"
        "- TASK-269 does not run MT5\n"
        "- TASK-269 does not run backtest\n"
        "- TASK-269 does not enter simulated trading\n"
        "- TASK-269 does not enter real trading\n"
        "- TASK-269 does not send orders\n"
        "- TASK-269 does not create manifest / fixture / report / directory\n"
        "- TASK-269 does not copy external evidence\n"
        "- TASK-269 does not modify official manifest / backtest/sets\n"
        "- TASK-269 does not add MQ5 / MQH files\n"
        "- TASK-269 does not commit\n"
        "- MQ5 inventory remains 7 files\n"
        "- TASK-269 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- fast-no-trade-dev profile remains the default release validation profile\n"
        "- future default preference is python tools/run_fast_no_trade_preflight.py --strict-mq5 --check-allowed-changes ...\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-269 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-270 implement fast preflight allowed-change presets\n\n"
        "- current task is TASK-270 implement fast preflight allowed-change presets\n"
        "- TASK-270 implement fast preflight allowed-change presets\n"
        "- TASK-270 is a tooling efficiency task\n"
        "- TASK-270 is tooling + docs + self-test update\n"
        "- TASK-269 completed read-only observability error/exception logging contract\n"
        "- TASK-269 commit is 5ebdf74 TASK-269 implement read-only observability error/exception logging contract\n"
        "- TASK-269 tag is v0.5.71-task-269-read-only-observability-error-snapshot\n"
        "- current HEAD is 5ebdf74 TASK-269 implement read-only observability error/exception logging contract\n"
        "- current latest tag is v0.5.71-task-269-read-only-observability-error-snapshot\n"
        "- implementation scope is limited to fast preflight allowed-change presets\n"
        "- --allow-preset\n"
        "- doc-state\n"
        "- tooling-preflight\n"
        "- mq5-observability\n"
        "- allowed-change guard can now use short preset commands\n"
        "- python tools/run_fast_no_trade_preflight.py --doc-only --check-allowed-changes --allow-preset doc-state\n"
        "- python tools/run_fast_no_trade_preflight.py --doc-only --check-allowed-changes --allow-preset tooling-preflight\n"
        "- python tools/run_fast_no_trade_preflight.py --strict-mq5 --check-allowed-changes --allow-preset mq5-observability\n"
        "- TASK-270 does not modify MQ5 / MQH\n"
        "- TASK-270 does not run MT5\n"
        "- TASK-270 does not run backtest\n"
        "- TASK-270 does not enter simulated trading\n"
        "- TASK-270 does not enter real trading\n"
        "- TASK-270 does not create manifest / fixture / report / directory\n"
        "- TASK-270 does not copy external evidence\n"
        "- TASK-270 does not commit\n"
        "- TASK-270 does not tag\n"
        "- TASK-270 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-270 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- fast-no-trade-dev profile PASS\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-270 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-271 implement read-only telemetry aggregation for error & metrics\n\n"
        "- current task is TASK-271 implement read-only telemetry aggregation for error & metrics\n"
        "- TASK-271 implement read-only telemetry aggregation for error & metrics\n"
        "- TASK-271 is a low-risk MQ5 implementation slice\n"
        "- TASK-271 implementation scope is limited to read-only telemetry aggregation snapshot\n"
        "- TASK-270 completed fast preflight allowed-change presets\n"
        "- TASK-270 commit is 6b9c3a8 TASK-270 implement fast no-trade preflight presets\n"
        "- TASK-270 tag is v0.5.72-task-270-fast-no-trade-preflight-presets\n"
        "- current HEAD is 6b9c3a8 TASK-270 implement fast no-trade preflight presets\n"
        "- current latest tag is v0.5.72-task-270-fast-no-trade-preflight-presets\n"
        "- read-only telemetry aggregation snapshot records telemetry_aggregation_snapshot=true\n"
        "- read-only telemetry aggregation snapshot records aggregated_errors_linked=true\n"
        "- read-only telemetry aggregation snapshot records aggregated_metrics_linked=true\n"
        "- read-only telemetry aggregation snapshot records all_observability_outputs_read_only=true\n"
        "- read-only telemetry aggregation snapshot records all_authorizations_false=true\n"
        "- read-only telemetry aggregation snapshot records no_trade_guard=active\n"
        "- read-only telemetry aggregation snapshot records trading_authorization=false\n"
        "- read-only telemetry aggregation snapshot records mt5_run_required=false\n"
        "- read-only telemetry aggregation snapshot records evidence_generation=false\n"
        "- read-only telemetry aggregation snapshot records manifest_generation=false\n"
        "- read-only telemetry aggregation snapshot records Inventory only; no MT5 run; no trading authorization.\n"
        "- LogReadOnlyTelemetryAggregationSnapshot\n"
        "- OnTick telemetry aggregation remains gated by InpObservabilityLogOnTick\n"
        "- TASK-271 preserves TASK-243 through TASK-270 no-trade observability outputs\n"
        "- TASK-271 does not run MT5\n"
        "- TASK-271 does not run backtest\n"
        "- TASK-271 does not enter simulated trading\n"
        "- TASK-271 does not enter real trading\n"
        "- TASK-271 does not send orders\n"
        "- TASK-271 does not create manifest / fixture / report / directory\n"
        "- TASK-271 does not copy external evidence\n"
        "- TASK-271 does not modify official manifest / backtest/sets\n"
        "- TASK-271 does not add MQ5 / MQH files\n"
        "- TASK-271 does not commit\n"
        "- TASK-271 does not tag\n"
        "- TASK-271 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-271 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- fast-no-trade-dev profile remains available\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-271 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-272 implement read-only controller summary snapshot\n\n"
        "- current task is TASK-272 implement read-only controller summary snapshot\n"
        "- TASK-272 implement read-only controller summary snapshot\n"
        "- TASK-272 is a low-risk MQ5 implementation slice\n"
        "- TASK-272 implementation scope is limited to read-only controller summary snapshot consolidation\n"
        "- TASK-271 completed read-only telemetry aggregation for error & metrics in the current working tree\n"
        "- current HEAD is 6b9c3a8 TASK-270 implement fast no-trade preflight presets\n"
        "- current latest tag is v0.5.72-task-270-fast-no-trade-preflight-presets\n"
        "- read-only controller summary snapshot records controller_summary_snapshot=true\n"
        "- read-only controller summary snapshot records init_path_linked=true\n"
        "- read-only controller summary snapshot records tick_path_linked=true\n"
        "- read-only controller summary snapshot records deinit_path_linked=true\n"
        "- read-only controller summary snapshot records all_observability_outputs_read_only=true\n"
        "- read-only controller summary snapshot records all_authorizations_false=true\n"
        "- read-only controller summary snapshot records no_trade_guard=active\n"
        "- read-only controller summary snapshot records trading_authorization=false\n"
        "- read-only controller summary snapshot records mt5_run_required=false\n"
        "- read-only controller summary snapshot records evidence_generation=false\n"
        "- read-only controller summary snapshot records manifest_generation=false\n"
        "- read-only controller summary snapshot records Inventory only; no MT5 run; no trading authorization.\n"
        "- LogReadOnlyControllerSummarySnapshot\n"
        "- OnTick controller summary remains gated by InpObservabilityLogOnTick\n"
        "- TASK-272 preserves TASK-243 through TASK-271 no-trade observability outputs\n"
        "- TASK-272 does not run MT5\n"
        "- TASK-272 does not run backtest\n"
        "- TASK-272 does not enter simulated trading\n"
        "- TASK-272 does not enter real trading\n"
        "- TASK-272 does not send orders\n"
        "- TASK-272 does not create manifest / fixture / report / directory\n"
        "- TASK-272 does not copy external evidence\n"
        "- TASK-272 does not modify official manifest / backtest/sets\n"
        "- TASK-272 does not add MQ5 / MQH files\n"
        "- TASK-272 does not commit\n"
        "- TASK-272 does not tag\n"
        "- TASK-272 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-272 confirms MQ5 inventory remains 7 files\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- fast-no-trade-dev profile remains available\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-272 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-273 implement fast preflight review summary output\n\n"
        "- current task is TASK-273 implement fast preflight review summary output\n"
        "- TASK-273 implement fast preflight review summary output\n"
        "- TASK-273 is a tooling efficiency task\n"
        "- TASK-273 implementation scope is limited to fast no-trade preflight review summary output\n"
        "- TASK-271/272 completed and closed together\n"
        "- TASK-271/272 commit is e691022 TASK-271-272 implement read-only telemetry aggregation and controller summary snapshots\n"
        "- TASK-271/272 tag is v0.5.73-task-271-272-read-only-telemetry-controller-summary\n"
        "- current HEAD is e691022 TASK-271-272 implement read-only telemetry aggregation and controller summary snapshots\n"
        "- current latest tag is v0.5.73-task-271-272-read-only-telemetry-controller-summary\n"
        "- tools/run_fast_no_trade_preflight.py supports --review-summary\n"
        "- --review-summary prints fast_no_trade_review_summary=true\n"
        "- --review-summary prints preflight_result=PASS or preflight_result=FAIL\n"
        "- --review-summary prints mode=default / doc-only / strict-mq5\n"
        "- --review-summary prints allowed_change_check=PASS / FAIL / SKIPPED\n"
        "- --review-summary prints unexpected_changes_count\n"
        "- --review-summary prints suggested_git_add\n"
        "- review summary is stdout-only\n"
        "- review summary does not create report / manifest / fixture / directory\n"
        "- suggested_git_add excludes known existing untracked .vscode/ logs/ tools/__pycache__/ package-lock.json and root text file\n"
        "- TASK-273 does not modify MQ5 / MQH\n"
        "- TASK-273 does not run MT5\n"
        "- TASK-273 does not run backtest\n"
        "- TASK-273 does not enter simulated trading\n"
        "- TASK-273 does not enter real trading\n"
        "- TASK-273 does not send orders\n"
        "- TASK-273 does not create manifest / fixture / report / directory\n"
        "- TASK-273 does not copy external evidence\n"
        "- TASK-273 does not modify official manifest / backtest/sets\n"
        "- TASK-273 does not commit\n"
        "- TASK-273 does not tag\n"
        "- TASK-273 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-273 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-273 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade preflight review summary is ready for Trae compressed review handoff\n"
        "- do not directly enter TASK-274\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-274 implement fast preflight Trae command preview output\n\n"
        "- current task is TASK-274 implement fast preflight Trae command preview output\n"
        "- TASK-274 implement fast preflight Trae command preview output\n"
        "- TASK-274 is a tooling efficiency task\n"
        "- TASK-274 implementation scope is limited to fast preflight Trae command preview output\n"
        "- TASK-273 completed fast preflight review summary output\n"
        "- TASK-273 commit is 2008abe TASK-273 implement fast preflight review summary output\n"
        "- TASK-273 tag is v0.5.74-task-273-fast-preflight-review-summary\n"
        "- current HEAD is 2008abe TASK-273 implement fast preflight review summary output\n"
        "- current latest tag is v0.5.74-task-273-fast-preflight-review-summary\n"
        "- tools/run_fast_no_trade_preflight.py supports --emit-trae-command\n"
        "- --emit-trae-command requires --review-summary\n"
        "- --emit-trae-command requires --check-allowed-changes\n"
        "- --emit-trae-command requires --task-id\n"
        "- --emit-trae-command requires --commit-message\n"
        "- --emit-trae-command requires --tag-name\n"
        "- --task-id / --commit-message / --tag-name are required for Trae command preview\n"
        "- Trae command preview prints trae_command_preview=true\n"
        "- Trae command preview prints command_block_start and command_block_end\n"
        "- Trae command preview prints git add / git commit / git tag / git rev-parse commands\n"
        "- Trae command preview is stdout-only\n"
        "- Trae command preview does not execute git add / commit / tag\n"
        "- Trae command preview does not create report / manifest / fixture / directory\n"
        "- TASK-274 does not modify MQ5 / MQH\n"
        "- TASK-274 does not run MT5\n"
        "- TASK-274 does not run backtest\n"
        "- TASK-274 does not enter simulated trading\n"
        "- TASK-274 does not enter real trading\n"
        "- TASK-274 does not send orders\n"
        "- TASK-274 does not create manifest / fixture / report / directory\n"
        "- TASK-274 does not copy external evidence\n"
        "- TASK-274 does not modify official manifest / backtest/sets\n"
        "- TASK-274 does not commit\n"
        "- TASK-274 does not tag\n"
        "- TASK-274 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-274 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-274 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade preflight Trae command preview is ready for compressed handoff\n"
        "- do not directly enter TASK-275\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-275 implement fast preflight workflow presets\n\n"
        "- current task is TASK-275 implement fast preflight workflow presets\n"
        "- TASK-275 implement fast preflight workflow presets\n"
        "- TASK-275 is a tooling efficiency task\n"
        "- TASK-275 implementation scope is limited to fast preflight workflow presets\n"
        "- TASK-274 completed fast preflight Trae command preview output\n"
        "- TASK-274 commit is de9b66b TASK-274 implement fast preflight Trae command preview output\n"
        "- TASK-274 tag is v0.5.75-task-274-fast-preflight-trae-command-preview\n"
        "- current HEAD is de9b66b TASK-274 implement fast preflight Trae command preview output\n"
        "- current latest tag is v0.5.75-task-274-fast-preflight-trae-command-preview\n"
        "- tools/run_fast_no_trade_preflight.py supports --workflow-preset\n"
        "- --workflow-preset supports doc-state\n"
        "- --workflow-preset supports tooling-preflight\n"
        "- --workflow-preset supports mq5-observability\n"
        "- workflow preset compresses preflight + allowed-change guard + review summary + Trae command preview commands\n"
        "- workflow preset can combine with --emit-trae-command\n"
        "- workflow preset can combine with --task-id / --commit-message / --tag-name\n"
        "- workflow preset can stack with extra --allow / --allow-prefix\n"
        "- workflow preset conflicts with manual --doc-only / --strict-mq5 / --check-allowed-changes / --allow-preset / --review-summary\n"
        "- workflow preset summary prints workflow_preset=<NAME>\n"
        "- workflow preset summary prints allowed_presets=\n"
        "- workflow preset summary prints allowed_change_guard=true\n"
        "- workflow preset summary prints allowed_change_check=PASS/FAIL\n"
        "- workflow preset summary prints fast_no_trade_review_summary=true\n"
        "- workflow preset Trae command preview prints trae_command_preview=true\n"
        "- workflow preset does not execute git add / commit / tag\n"
        "- workflow preset does not create report / manifest / fixture / directory\n"
        "- TASK-275 does not modify MQ5 / MQH\n"
        "- TASK-275 does not run MT5\n"
        "- TASK-275 does not run backtest\n"
        "- TASK-275 does not enter simulated trading\n"
        "- TASK-275 does not enter real trading\n"
        "- TASK-275 does not send orders\n"
        "- TASK-275 does not create manifest / fixture / report / directory\n"
        "- TASK-275 does not copy external evidence\n"
        "- TASK-275 does not modify official manifest / backtest/sets\n"
        "- TASK-275 does not commit\n"
        "- TASK-275 does not tag\n"
        "- TASK-275 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 浠嶄负 7 files\n"
        "- TASK-275 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-275 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade workflow presets are ready for compressed Trae preflight handoff\n"
        "- do not directly enter TASK-276\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-276 implement fast preflight state report stdout\n\n"
        "- current task is TASK-276 implement fast preflight state report stdout\n"
        "- TASK-276 implement fast preflight state report stdout\n"
        "- TASK-276 is a tooling efficiency task\n"
        "- TASK-276 implementation scope is limited to fast preflight state report stdout\n"
        "- TASK-275 completed fast preflight workflow presets\n"
        "- TASK-275 commit is 1bc332c TASK-275 implement fast preflight workflow presets\n"
        "- TASK-275 tag is v0.5.76-task-275-fast-preflight-workflow-presets\n"
        "- current HEAD is 1bc332c TASK-275 implement fast preflight workflow presets\n"
        "- current latest tag is v0.5.76-task-275-fast-preflight-workflow-presets\n"
        "- tools/run_fast_no_trade_preflight.py supports --state-report\n"
        "- --state-report prints fast_no_trade_state_report=true\n"
        "- --state-report prints current_head\n"
        "- --state-report prints current_tags_at_head\n"
        "- --state-report prints modified_files\n"
        "- --state-report prints untracked_files\n"
        "- --state-report prints allowed_change_guard\n"
        "- --state-report prints allowed_change_check\n"
        "- --state-report prints unexpected_changes_count\n"
        "- --state-report prints mq5_inventory_expected=7 files\n"
        "- --state-report prints trading_keywords=false\n"
        "- --state-report prints mt5_run=false\n"
        "- --state-report prints trading_executed=false\n"
        "- --state-report prints manifest_created=false\n"
        "- --state-report prints fixture_created=false\n"
        "- --state-report prints report_created=false\n"
        "- --state-report prints external_evidence_copied=false\n"
        "- --state-report prints official_manifest_modified=false\n"
        "- --state-report prints backtest_sets_modified=false\n"
        "- --state-report prints backtest_manifests_modified=false\n"
        "- state report is stdout-only and does not create files\n"
        "- state report can combine with --workflow-preset / --review-summary / --emit-trae-command\n"
        "- state report does not execute git add / commit / tag\n"
        "- TASK-276 does not modify MQ5 / MQH\n"
        "- TASK-276 does not run MT5\n"
        "- TASK-276 does not run backtest\n"
        "- TASK-276 does not enter simulated trading\n"
        "- TASK-276 does not enter real trading\n"
        "- TASK-276 does not send orders\n"
        "- TASK-276 does not create manifest / fixture / report / directory\n"
        "- TASK-276 does not copy external evidence\n"
        "- TASK-276 does not modify official manifest / backtest/sets\n"
        "- TASK-276 does not commit\n"
        "- TASK-276 does not tag\n"
        "- TASK-276 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 娴犲秳璐?7 files\n"
        "- TASK-276 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-276 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade state report stdout is ready for compressed Codex/Trae handoff\n"
        "- do not directly enter TASK-277\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-277 implement compact Trae handoff instruction output\n\n"
        "- current task is TASK-277 implement compact Trae handoff instruction output\n"
        "- TASK-277 implement compact Trae handoff instruction output\n"
        "- TASK-277 is a tooling efficiency task\n"
        "- TASK-277 implementation scope is limited to compact Trae handoff instruction output\n"
        "- TASK-276 completed fast preflight state report stdout\n"
        "- TASK-276 commit is 8217709 TASK-276 implement fast preflight state report stdout\n"
        "- TASK-276 tag is v0.5.77-task-276-fast-preflight-state-report\n"
        "- current HEAD is 8217709 TASK-276 implement fast preflight state report stdout\n"
        "- current latest tag is v0.5.77-task-276-fast-preflight-state-report\n"
        "- tools/run_fast_no_trade_preflight.py supports --emit-trae-handoff\n"
        "- --emit-trae-handoff prints trae_handoff_instruction=true\n"
        "- --emit-trae-handoff prints handoff_block_start\n"
        "- --emit-trae-handoff prints 发给：Trae\n"
        "- --emit-trae-handoff prints a compact Trae review / validation / commit / tag instruction block\n"
        "- --emit-trae-handoff requires --state-report\n"
        "- --emit-trae-handoff requires --review-summary\n"
        "- --emit-trae-handoff requires --emit-trae-command\n"
        "- --emit-trae-handoff requires --check-allowed-changes\n"
        "- --emit-trae-handoff requires --task-id / --commit-message / --tag-name\n"
        "- --emit-trae-handoff requires allowed_change_check=PASS\n"
        "- --emit-trae-handoff requires suggested_git_add not BLOCKED and not SKIPPED\n"
        "- handoff output is stdout-only and does not create files\n"
        "- handoff output does not execute git add / commit / tag\n"
        "- handoff block commands are PowerShell line-by-line commands and do not use &&\n"
        "- TASK-277 does not modify MQ5 / MQH\n"
        "- TASK-277 does not run MT5\n"
        "- TASK-277 does not run backtest\n"
        "- TASK-277 does not enter simulated trading\n"
        "- TASK-277 does not enter real trading\n"
        "- TASK-277 does not send orders\n"
        "- TASK-277 does not create manifest / fixture / report / directory\n"
        "- TASK-277 does not copy external evidence\n"
        "- TASK-277 does not modify official manifest / backtest/sets\n"
        "- TASK-277 does not commit\n"
        "- TASK-277 does not tag\n"
        "- TASK-277 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-277 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-277 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade compact Trae handoff output is ready for compressed review / validation / commit / tag handoff\n"
        "- do not directly enter TASK-278\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-278 implement compact preflight combined report output\n\n"
        "- current task is TASK-278 implement compact preflight combined report output\n"
        "- TASK-278 implement compact preflight combined report output\n"
        "- TASK-278 is a tooling efficiency task\n"
        "- TASK-278 implementation scope is limited to compact preflight combined report output\n"
        "- TASK-277 completed compact Trae handoff instruction output\n"
        "- TASK-277 commit is 90bb6b8 TASK-277 implement compact Trae handoff instruction output\n"
        "- TASK-277 tag is v0.5.78-task-277-fast-preflight-trae-handoff\n"
        "- current HEAD is 90bb6b8 TASK-277 implement compact Trae handoff instruction output\n"
        "- current latest tag is v0.5.78-task-277-fast-preflight-trae-handoff\n"
        "- tools/run_fast_no_trade_preflight.py supports --compact-report\n"
        "- new parameter is --compact-report\n"
        "- --compact-report prints fast_no_trade_compact_report=true\n"
        "- --compact-report includes fast_no_trade_state_report\n"
        "- --compact-report prints current_head / current_tags_at_head\n"
        "- --compact-report prints workflow_preset / profile\n"
        "- --compact-report prints allowed_change_guard / allowed_change_check / unexpected_changes_count\n"
        "- --compact-report prints modified_files / untracked_files\n"
        "- --compact-report includes Trae command preview\n"
        "- --compact-report includes review-summary\n"
        "- --compact-report prints mq5_inventory_expected=7 files\n"
        "- --compact-report prints trading_keywords=false\n"
        "- compact report is stdout-only and does not create files\n"
        "- compact report can combine with --workflow-preset / --state-report / --review-summary / --emit-trae-command / --emit-trae-handoff\n"
        "- compact report can combine with --allow / --allow-prefix / --allow-preset\n"
        "- compact report does not execute git add / commit / tag\n"
        "- TASK-278 does not modify MQ5 / MQH\n"
        "- TASK-278 does not run MT5\n"
        "- TASK-278 does not run backtest\n"
        "- TASK-278 does not enter simulated trading\n"
        "- TASK-278 does not enter real trading\n"
        "- TASK-278 does not send orders\n"
        "- TASK-278 does not create manifest / fixture / report / directory\n"
        "- TASK-278 does not copy external evidence\n"
        "- TASK-278 does not modify official manifest / backtest/sets\n"
        "- TASK-278 does not commit\n"
        "- TASK-278 does not tag\n"
        "- TASK-278 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-278 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-278 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade compact combined report output is ready for compressed Codex/Trae handoff\n"
        "- do not directly enter TASK-279\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-279 implement release bundle summary compression\n\n"
        "- current task is TASK-279 implement release bundle summary compression\n"
        "- TASK-279 implement release bundle summary compression\n"
        "- TASK-279 is a tooling efficiency task\n"
        "- TASK-279 implementation scope is limited to release bundle summary compression\n"
        "- TASK-278 completed compact preflight combined report output\n"
        "- TASK-278 commit is 7e93d14 TASK-278 implement compact preflight combined report output\n"
        "- TASK-278 tag is v0.5.79-task-278-compact-preflight-report\n"
        "- current HEAD is 7e93d14 TASK-278 implement compact preflight combined report output\n"
        "- current latest tag is v0.5.79-task-278-compact-preflight-report\n"
        "- tools/run_release_validation_bundle.py supports --compressed-summary\n"
        "- new parameter is --compressed-summary\n"
        "- --compressed-summary prints release_validation_compressed_summary=true\n"
        "- --compressed-summary includes fast_no_trade_state_report\n"
        "- --compressed-summary prints workflow_preset\n"
        "- --compressed-summary prints allowed_change_check\n"
        "- --compressed-summary prints mq5_inventory_expected=7 files\n"
        "- --compressed-summary prints trading_keywords=false\n"
        "- --compressed-summary prints project-state-docs / project-state-docs-self-test\n"
        "- --compressed-summary includes Trae command preview\n"
        "- --compressed-summary includes review summary\n"
        "- compressed summary is stdout-only and does not create files\n"
        "- compressed summary can combine with --only / --skip / --profile / --fast-no-trade-dev\n"
        "- compressed summary can combine with --workflow-preset / --state-report / --review-summary / --emit-trae-command / --emit-trae-handoff\n"
        "- compressed summary does not execute git add / commit / tag\n"
        "- TASK-279 does not modify MQ5 / MQH\n"
        "- TASK-279 does not run MT5\n"
        "- TASK-279 does not run backtest\n"
        "- TASK-279 does not enter simulated trading\n"
        "- TASK-279 does not enter real trading\n"
        "- TASK-279 does not send orders\n"
        "- TASK-279 does not create manifest / fixture / report / directory\n"
        "- TASK-279 does not copy external evidence\n"
        "- TASK-279 does not modify official manifest / backtest/sets\n"
        "- TASK-279 does not commit\n"
        "- TASK-279 does not tag\n"
        "- TASK-279 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-279 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-279 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- fast-no-trade release bundle compressed summary is ready for compressed Codex/Trae handoff\n"
        "- do not directly enter TASK-280\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-280 implement no-trade development workflow closure audit\n\n"
        "- current task is TASK-280 implement no-trade development workflow closure audit\n"
        "- TASK-280 implement no-trade development workflow closure audit\n"
        "- TASK-280 is a tooling + audit task\n"
        "- TASK-280 implementation scope is limited to no-trade development workflow closure audit\n"
        "- TASK-279 completed release bundle summary compression\n"
        "- TASK-279 baseline commit is 7e93d14 TASK-278 implement release bundle summary compression\n"
        "- TASK-279 tag is v0.5.79-task-278-compact-preflight-report\n"
        "- current HEAD is 7e93d14 TASK-278 implement release bundle summary compression\n"
        "- current latest tag is v0.5.79-task-278-compact-preflight-report\n"
        "- tools/run_fast_no_trade_preflight.py supports --workflow-closure-audit\n"
        "- tools/run_release_validation_bundle.py supports --workflow-closure-audit\n"
        "- new parameter is --workflow-closure-audit\n"
        "- --workflow-closure-audit prints workflow_closure_audit=true\n"
        "- --workflow-closure-audit prints release_ready_closure_audit=true\n"
        "- --workflow-closure-audit includes fast_no_trade_state_report\n"
        "- --workflow-closure-audit includes fast_no_trade_review_summary\n"
        "- --workflow-closure-audit prints workflow_preset\n"
        "- --workflow-closure-audit prints allowed_change_check\n"
        "- --workflow-closure-audit includes Trae handoff block status\n"
        "- --workflow-closure-audit includes validator/self-test summary\n"
        "- --workflow-closure-audit prints mq5_inventory_expected=7 files\n"
        "- --workflow-closure-audit prints trading_keywords=false\n"
        "- workflow closure audit is stdout-only and does not create files\n"
        "- workflow closure audit does not execute git add / commit / tag\n"
        "- TASK-280 does not modify MQ5 / MQH\n"
        "- TASK-280 does not run MT5\n"
        "- TASK-280 does not run backtest\n"
        "- TASK-280 does not enter simulated trading\n"
        "- TASK-280 does not enter real trading\n"
        "- TASK-280 does not send orders\n"
        "- TASK-280 does not create manifest / fixture / report / directory\n"
        "- TASK-280 does not copy external evidence\n"
        "- TASK-280 does not modify official manifest / backtest/sets\n"
        "- TASK-280 does not commit\n"
        "- TASK-280 does not tag\n"
        "- TASK-280 does not push\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-280 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-280 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- workflow closure audit summary is ready for final no-trade release closure review\n"
        "- do not directly enter TASK-281\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-DOC-281 freeze no-trade workflow closure state after TASK-280\n\n"
        "- current task is TASK-DOC-281 freeze no-trade workflow closure state after TASK-280\n"
        "- TASK-DOC-281 freeze no-trade workflow closure state after TASK-280\n"
        "- TASK-DOC-281 is doc/tooling state sync only\n"
        "- TASK-280 completed no-trade development workflow closure audit\n"
        "- TASK-280 commit is 304b4aa TASK-280 implement no-trade development workflow closure audit\n"
        "- TASK-280 tag is v0.5.80-task-280-no-trade-workflow-closure-audit\n"
        "- fast-no-trade-dev profile is the default fast validation entry\n"
        "- run_fast_no_trade_preflight.py supports --workflow-preset\n"
        "- run_fast_no_trade_preflight.py supports --state-report\n"
        "- run_fast_no_trade_preflight.py supports --review-summary\n"
        "- run_fast_no_trade_preflight.py supports --emit-trae-command\n"
        "- run_fast_no_trade_preflight.py supports --emit-trae-handoff\n"
        "- run_fast_no_trade_preflight.py supports --compact-report\n"
        "- run_fast_no_trade_preflight.py supports --workflow-closure-audit\n"
        "- run_release_validation_bundle.py supports --compressed-summary\n"
        "- run_release_validation_bundle.py supports --workflow-closure-audit\n"
        "- run_release_validation_bundle.py supports --profile fast-no-trade-dev\n"
        "- current default Codex validation mode: py tools/run_release_validation_bundle.py --compressed-summary --workflow-closure-audit --profile fast-no-trade-dev\n"
        "- current default Trae review mode uses generated Trae handoff block, continuous commit/tag, and validates tag points to HEAD\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- TASK-DOC-281 confirms MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-DOC-281 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- TASK-DOC-281 does not modify MQ5 / MQH\n"
        "- TASK-DOC-281 does not run MT5\n"
        "- TASK-DOC-281 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-281 does not copy external evidence\n"
        "- future preflight tooling optimization is frozen unless validation efficiency becomes bottleneck\n"
        "- next candidate should shift to read-only compile-readiness / MQ5 static interface consistency, not more workflow tooling\n"
        "- do not directly enter TASK-282\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-282 implement read-only compile-readiness boundary\n\n"
        "- current task is TASK-282 implement read-only compile-readiness boundary\n"
        "- TASK-282 implement read-only compile-readiness boundary\n"
        "- TASK-282 is a read-only boundary verification task\n"
        "- TASK-282 objective is to build MQ5 EA compile-readiness boundary\n"
        "- compile-readiness boundary verifies no-trade / read-only observability scaffold safety\n"
        "- compile-readiness boundary verifies MQ5 static interface consistency\n"
        "- TASK-282 keeps the fast no-trade workflow tooling baseline\n"
        "- TASK-282 baseline commit is 304b4aa TASK-280 implement no-trade development workflow closure audit\n"
        "- TASK-282 baseline tag is v0.5.80-task-280-no-trade-workflow-closure-audit\n"
        "- run_release_validation_bundle.py includes read-only compile-readiness boundary check\n"
        "- fast-no-trade-dev profile includes read-only compile-readiness boundary check\n"
        "- compile-readiness check is read-only and stdout-only\n"
        "- compile-readiness check does not run MT5\n"
        "- compile-readiness check does not modify MQ5 / MQH\n"
        "- compile-readiness check does not create manifest / fixture / report / directory\n"
        "- compile-readiness check does not copy external evidence\n"
        "- compile-readiness check confirms MQ5 inventory remains 7 files\n"
        "- compile-readiness check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 浠嶄负 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- TASK-282 does not modify MQ5 / MQH\n"
        "- TASK-282 does not run MT5\n"
        "- TASK-282 does not execute backtest\n"
        "- TASK-282 does not enter simulated trading\n"
        "- TASK-282 does not enter real trading\n"
        "- TASK-282 does not create manifest / fixture / report / directory\n"
        "- TASK-282 does not copy external evidence\n"
        "- next candidate should remain read-only MQ5 static interface consistency unless ChatGPT defines a new boundary\n"
        "- do not directly enter TASK-283\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## TASK-283 implement MQ5 static interface consistency audit\n\n"
        "- current task is TASK-283 implement MQ5 static interface consistency audit\n"
        "- TASK-283 implement MQ5 static interface consistency audit\n"
        "- TASK-283 is a read-only / no-trade MQ5 interface audit\n"
        "- TASK-283 objective is static consistency check for MQ5 core module interfaces\n"
        "- MQ5 static interface consistency audit verifies TradingSystem.mq5 routes OnInit / OnTick / OnDeinit through EaController\n"
        "- MQ5 static interface consistency audit verifies EaController includes InputConfig / Logger / SignalEngine / RiskManager / ExecutionManager\n"
        "- MQ5 static interface consistency audit verifies Logger helper availability for no-trade observability scaffold\n"
        "- MQ5 static interface consistency audit verifies SignalEngine / RiskManager / ExecutionManager Init(Logger &log) interfaces\n"
        "- MQ5 static interface consistency audit verifies read-only status snapshot interfaces remain aligned\n"
        "- TASK-283 baseline commit is 304b4aa TASK-280 implement no-trade development workflow closure audit\n"
        "- TASK-283 baseline tag is v0.5.80-task-280-no-trade-workflow-closure-audit\n"
        "- run_release_validation_bundle.py includes mq5-static-interface-consistency check\n"
        "- fast-no-trade-dev profile includes mq5-static-interface-consistency check\n"
        "- mq5-static-interface-consistency check is read-only and stdout-only\n"
        "- mq5-static-interface-consistency check does not run MT5\n"
        "- mq5-static-interface-consistency check does not modify MQ5 / MQH\n"
        "- mq5-static-interface-consistency check does not create manifest / fixture / report / directory\n"
        "- mq5-static-interface-consistency check does not copy external evidence\n"
        "- mq5-static-interface-consistency check confirms MQ5 inventory remains 7 files\n"
        "- mq5-static-interface-consistency check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no trading authorization\n"
        "- no manifest / fixture / report / directory\n"
        "- no external evidence\n"
        "- TASK-283 does not modify MQ5 / MQH\n"
        "- TASK-283 does not run MT5\n"
        "- TASK-283 does not execute backtest\n"
        "- TASK-283 does not enter simulated trading\n"
        "- TASK-283 does not enter real trading\n"
        "- TASK-283 does not create manifest / fixture / report / directory\n"
        "- TASK-283 does not copy external evidence\n"
        "- current task is TASK-284 implement MQ5 static include dependency consistency audit\n"
        "- TASK-284 implement MQ5 static include dependency consistency audit\n"
        "- TASK-283 completed\n"
        "- TASK-283 completion commit is 1dbf78f TASK-283 implement MQ5 static interface consistency audit\n"
        "- TASK-283 completion tag is v0.5.82-task-283-mq5-static-interface-audit\n"
        "- TASK-284 is a read-only static tooling task\n"
        "- TASK-284 adds mq5-static-include-consistency check\n"
        "- MQ5 static include dependency consistency audit verifies include paths resolve within mq5\n"
        "- MQ5 static include dependency consistency audit rejects absolute include paths\n"
        "- MQ5 static include dependency consistency audit rejects docs / tools / backtest include paths\n"
        "- MQ5 static include dependency consistency audit confirms MQ5 inventory remains 7 files\n"
        "- run_release_validation_bundle.py includes mq5-static-include-consistency check\n"
        "- fast-no-trade-dev profile includes mq5-static-include-consistency check\n"
        "- mq5-static-include-consistency check is read-only and stdout-only\n"
        "- mq5-static-include-consistency check does not run MT5\n"
        "- mq5-static-include-consistency check does not execute MQL5 compile\n"
        "- mq5-static-include-consistency check does not modify MQ5 / MQH\n"
        "- mq5-static-include-consistency check does not create manifest / fixture / report / directory\n"
        "- mq5-static-include-consistency check does not copy external evidence\n"
        "- mq5-static-include-consistency check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-284 does not modify MQ5 / MQH\n"
        "- TASK-284 does not run MT5\n"
        "- TASK-284 does not execute MQL5 compile\n"
        "- TASK-284 does not execute backtest\n"
        "- TASK-284 does not enter simulated trading\n"
        "- TASK-284 does not enter real trading\n"
        "- TASK-284 does not create manifest / fixture / report / directory\n"
        "- TASK-284 does not copy external evidence\n"
        "- v0.5.82-task-283-mq5-static-interface-audit\n"
        "- next candidate must be defined by ChatGPT before TASK-284\n"
        "- current task is TASK-285 implement read-only controller/logger duplicate output reduction contract\n"
        "- TASK-285 implement read-only controller/logger duplicate output reduction contract\n"
        "- TASK-284 completed\n"
        "- TASK-284 completion commit is 4636254 TASK-284 implement MQ5 static include dependency consistency audit\n"
        "- TASK-284 completion tag is v0.5.83-task-284-mq5-static-include-consistency\n"
        "- current HEAD is 4636254 TASK-284 implement MQ5 static include dependency consistency audit\n"
        "- current tag is v0.5.83-task-284-mq5-static-include-consistency\n"
        "- TASK-285 is a low-risk MQ5 implementation slice\n"
        "- TASK-285 implements read-only controller/logger duplicate output reduction contract\n"
        "- read-only controller/logger duplicate output reduction contract\n"
        "- duplicate_output_guard=active\n"
        "- controller_logger_deduplication=true\n"
        "- observability_output_reduction_snapshot=true\n"
        "- tick_output_requires_InpObservabilityLogOnTick=true\n"
        "- TASK-285 preserves TASK-243 through TASK-284 no-trade observability contract fields\n"
        "- TASK-285 does not run MT5\n"
        "- TASK-285 does not execute MQL5 compile\n"
        "- TASK-285 does not execute backtest\n"
        "- TASK-285 does not enter simulated trading\n"
        "- TASK-285 does not enter real trading\n"
        "- TASK-285 does not create manifest / fixture / report / directory\n"
        "- TASK-285 does not copy external evidence\n"
        "- TASK-285 does not modify forbidden MQ5 / MQH files\n"
        "- v0.5.83-task-284-mq5-static-include-consistency\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- no MT5 run\n"
        "- no MQL5 compile\n"
        "- no trading authorization\n"
        "- next candidate must be defined by ChatGPT before TASK-286\n"
        "- current task is TASK-286 implement MQ5 lifecycle route consistency audit\n"
        "- TASK-286 implement MQ5 lifecycle route consistency audit\n"
        "- TASK-285 completed\n"
        "- TASK-285 completion commit is 762041a TASK-285 implement read-only controller/logger duplicate output reduction contract\n"
        "- TASK-285 completion tag is v0.5.84-task-285-controller-logger-output-reduction\n"
        "- current HEAD is 762041a TASK-285 implement read-only controller/logger duplicate output reduction contract\n"
        "- current tag is v0.5.84-task-285-controller-logger-output-reduction\n"
        "- TASK-286 is a read-only static tooling task\n"
        "- TASK-286 adds mq5-lifecycle-route-consistency check\n"
        "- MQ5 lifecycle route consistency audit verifies OnInit / OnTick / OnDeinit route through EaController\n"
        "- mq5-lifecycle-route-consistency check is read-only and stdout-only\n"
        "- mq5-lifecycle-route-consistency check does not run MT5\n"
        "- mq5-lifecycle-route-consistency check does not execute MQL5 compile\n"
        "- mq5-lifecycle-route-consistency check does not modify MQ5 / MQH\n"
        "- fast-no-trade-dev profile includes mq5-lifecycle-route-consistency check\n"
        "- mq5-lifecycle-route-consistency PASS\n"
        "- OnInit\n"
        "- OnTick\n"
        "- OnDeinit\n"
        "- v0.5.84-task-285-controller-logger-output-reduction\n"
        "- MQ5 inventory remains 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- no MT5 run\n"
        "- no MQL5 compile\n"
        "- no trading authorization\n"
        "- next candidate must be defined by ChatGPT before TASK-287\n"
        "- current task is TASK-287 implement MQ5 observability helper call consistency audit\n"
        "- TASK-287 implement MQ5 observability helper call consistency audit\n"
        "- TASK-286 completed\n"
        "- TASK-286 completion commit is a870547 TASK-286 implement MQ5 lifecycle route consistency audit\n"
        "- TASK-286 completion tag is v0.5.85-task-286-mq5-lifecycle-route-consistency\n"
        "- current HEAD is a870547 TASK-286 implement MQ5 lifecycle route consistency audit\n"
        "- current tag is v0.5.85-task-286-mq5-lifecycle-route-consistency\n"
        "- TASK-287 is a read-only static tooling task\n"
        "- TASK-287 adds mq5-observability-helper-consistency check\n"
        "- MQ5 observability helper call consistency audit verifies EaController Logger helper calls are defined in Logger.mqh\n"
        "- mq5-observability-helper-consistency check is read-only and stdout-only\n"
        "- mq5-observability-helper-consistency check does not run MT5\n"
        "- mq5-observability-helper-consistency check does not execute MQL5 compile\n"
        "- mq5-observability-helper-consistency check does not modify MQ5 / MQH\n"
        "- fast-no-trade-dev profile includes mq5-observability-helper-consistency check\n"
        "- logger_helper_consistency=true\n"
        "- mq5-observability-helper-consistency PASS\n"
        "- v0.5.85-task-286-mq5-lifecycle-route-consistency\n"
        "- next candidate must be defined by ChatGPT before TASK-288\n"
        "- current task is TASK-288 implement MQ5 read-only observability telemetry final aggregation\n"
        "- TASK-288 implement MQ5 read-only observability telemetry final aggregation\n"
        "- TASK-287 completed\n"
        "- current HEAD is a870547 TASK-286 implement MQ5 lifecycle route consistency audit\n"
        "- current tag is v0.5.85-task-286-mq5-lifecycle-route-consistency\n"
        "- TASK-288 is a tooling efficiency / read-only telemetry task\n"
        "- TASK-288 adds mq5-telemetry-aggregation check\n"
        "- mq5-telemetry-aggregation check is read-only and stdout-only\n"
        "- fast_no_trade_telemetry_aggregation=true\n"
        "- all_observability_outputs_read_only=true\n"
        "- mq5-telemetry-aggregation PASS\n"
        "- TASK-288 does not run MT5\n"
        "- TASK-288 does not execute MQL5 compile\n"
        "- TASK-288 does not modify MQ5 / MQH\n"
        "- TASK-288 does not create manifest / fixture / report / directory\n"
        "- TASK-288 does not copy external evidence\n"
        "- next candidate must be defined by ChatGPT before TASK-289\n"
        "- current task is TASK-289 reconcile TASK-287 observability helper validator tracking gap\n"
        "- TASK-289 reconcile TASK-287 observability helper validator tracking gap\n"
        "- TASK-288 completed\n"
        "- TASK-288 completion commit is afaf7d3 TASK-288 implement MQ5 read-only observability telemetry final aggregation\n"
        "- TASK-288 completion tag is v0.5.87-task-288-mq5-telemetry-final-aggregation\n"
        "- current HEAD is afaf7d3 TASK-288 implement MQ5 read-only observability telemetry final aggregation\n"
        "- current tag is v0.5.87-task-288-mq5-telemetry-final-aggregation\n"
        "- TASK-289 is a reconciliation / tooling consistency task\n"
        "- TASK-287 helper consistency validator was left as an untracked item\n"
        "- TASK-289 brings tools/validate_mq5_observability_helper_consistency.py into tracking scope\n"
        "- TASK-289 brings tools/test_validate_mq5_observability_helper_consistency.py into tracking scope\n"
        "- mq5-observability-helper-consistency check remains read-only and stdout-only\n"
        "- fast-no-trade-dev profile includes mq5-observability-helper-consistency check\n"
        "- workflow-closure-audit includes mq5-observability-helper-consistency check\n"
        "- TASK-289 does not recreate old v0.5.86 tag\n"
        "- TASK-289 does not move historical tags\n"
        "- TASK-289 does not run MT5\n"
        "- TASK-289 does not execute MQL5 compile\n"
        "- TASK-289 does not modify MQ5 / MQH\n"
        "- TASK-289 does not create manifest / fixture / report / directory\n"
        "- TASK-289 does not copy external evidence\n"
        "- next candidate must be defined by ChatGPT before TASK-290\n"
        "- current task is TASK-290 implement final milestone closure / release-ready state report\n"
        "- TASK-290 implement final milestone closure / release-ready state report\n"
        "- TASK-289 completed\n"
        "- TASK-289 completion commit is 098a985 TASK-289 reconcile observability helper validator tracking gap\n"
        "- TASK-289 completion tag is v0.5.88-task-289-reconcile-observability-helper-validator-tracking\n"
        "- current HEAD is 098a985 TASK-289 reconcile observability helper validator tracking gap\n"
        "- current tag is v0.5.88-task-289-reconcile-observability-helper-validator-tracking\n"
        "- TASK-290 is a tooling + release audit task\n"
        "- TASK-290 adds --final-milestone-report\n"
        "- final_milestone_report=true\n"
        "- release_ready_milestone_closure=true\n"
        "- TASK-266 through TASK-289 closure summary\n"
        "- Trae handoff blocks\n"
        "- validator/self-test results\n"
        "- mq5-inventory PASS\n"
        "- mq5-no-trade-observability PASS\n"
        "- mq5-static-interface-consistency PASS\n"
        "- mq5-static-include-consistency PASS\n"
        "- mq5-lifecycle-route-consistency PASS\n"
        "- mq5-observability-helper-consistency PASS\n"
        "- mq5-telemetry-aggregation PASS\n"
        "- project-state-docs PASS\n"
        "- project-state-docs-self-test PASS\n"
        "- TASK-290 does not run MT5\n"
        "- TASK-290 does not execute MQL5 compile\n"
        "- TASK-290 does not modify MQ5 / MQH\n"
        "- TASK-290 does not create manifest / fixture / report / directory\n"
        "- TASK-290 does not copy external evidence\n"
        "- TASK-290 confirms MQ5 inventory remains 7 files\n"
        "- TASK-290 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- next candidate must be defined by ChatGPT after TASK-290\n"
        "- current task is TASK-291 implement MQ5 static symbol reference consistency audit\n"
        "- TASK-291 implement MQ5 static symbol reference consistency audit\n"
        "- TASK-290 completed\n"
        "- TASK-290 completion commit is f8b4a8f TASK-290 implement final milestone closure / release-ready state report\n"
        "- TASK-290 completion tag is v0.5.89-task-290-final-no-trade-workflow-milestone-report\n"
        "- current HEAD is f8b4a8f TASK-290 implement final milestone closure / release-ready state report\n"
        "- current tag is v0.5.89-task-290-final-no-trade-workflow-milestone-report\n"
        "- TASK-291 is a read-only static tooling task\n"
        "- TASK-291 adds mq5-static-symbol-consistency check\n"
        "- MQ5 static symbol reference consistency audit\n"
        "- mq5-static-symbol-consistency check is read-only and stdout-only\n"
        "- mq5-static-symbol-consistency PASS\n"
        "- symbol_reference_consistency=true\n"
        "- compile_readiness_static_only=true\n"
        "- fast-no-trade-dev profile includes mq5-static-symbol-consistency check\n"
        "- TASK-291 does not run MT5\n"
        "- TASK-291 does not execute MQL5 compile\n"
        "- TASK-291 does not modify MQ5 / MQH\n"
        "- TASK-291 does not create manifest / fixture / report / directory\n"
        "- TASK-291 does not copy external evidence\n"
        "- TASK-291 confirms MQ5 inventory remains 7 files\n"
        "- TASK-291 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- current task is TASK-292 implement MQ5 static compile-readiness aggregate audit\n"
        "- TASK-292 implement MQ5 static compile-readiness aggregate audit\n"
        "- TASK-291 completed\n"
        "- TASK-291 completion commit is d199707 TASK-291 implement MQ5 static symbol reference consistency audit\n"
        "- TASK-291 completion tag is v0.5.90-task-291-mq5-static-symbol-consistency\n"
        "- current HEAD is d199707 TASK-291 implement MQ5 static symbol reference consistency audit\n"
        "- current tag is v0.5.90-task-291-mq5-static-symbol-consistency\n"
        "- TASK-292 is a read-only static tooling task\n"
        "- TASK-292 adds mq5-static-compile-readiness check\n"
        "- MQ5 static compile-readiness aggregate audit\n"
        "- mq5-static-compile-readiness check is read-only and stdout-only\n"
        "- mq5-static-compile-readiness PASS\n"
        "- compile_readiness_static_only=true\n"
        "- mql5_compile_executed=false\n"
        "- fast-no-trade-dev profile includes mq5-static-compile-readiness check\n"
        "- TASK-292 does not run MT5\n"
        "- TASK-292 does not execute MQL5 compile\n"
        "- TASK-292 does not modify MQ5 / MQH\n"
        "- TASK-292 does not create manifest / fixture / report / directory\n"
        "- TASK-292 does not copy external evidence\n"
        "- TASK-292 confirms MQ5 inventory remains 7 files\n"
        "- TASK-292 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- current task is TASK-293 implement MQ5 compile-readiness final milestone summary report\n"
        "- TASK-293 implement MQ5 compile-readiness final milestone summary report\n"
        "- TASK-292 completed\n"
        "- TASK-292 completion commit is 74ce782 TASK-292 implement MQ5 static compile-readiness aggregate audit\n"
        "- TASK-292 completion tag is v0.5.91-task-292-mq5-static-compile-readiness\n"
        "- current HEAD is 74ce782 TASK-292 implement MQ5 static compile-readiness aggregate audit\n"
        "- current tag is v0.5.91-task-292-mq5-static-compile-readiness\n"
        "- TASK-293 is a tooling + release audit task\n"
        "- TASK-293 adds mq5-static-compile-readiness-summary check\n"
        "- TASK-293 adds --final-milestone-summary in release validation bundle\n"
        "- MQ5 compile-readiness final milestone summary report\n"
        "- final_milestone_summary=true\n"
        "- tasks_covered=TASK-266..TASK-292\n"
        "- fast_no_trade_state_report=true\n"
        "- fast_no_trade_review_summary=true\n"
        "- trae_handoff_summary=true\n"
        "- workflow_closure_audit=true\n"
        "- validator_self_test_summary=PASS\n"
        "- mq5-static-compile-readiness-summary PASS\n"
        "- milestone_closure_ready=PASS\n"
        "- TASK-293 does not run MT5\n"
        "- TASK-293 does not execute MQL5 compile\n"
        "- TASK-293 does not modify MQ5 / MQH\n"
        "- TASK-293 does not create manifest / fixture / report / directory\n"
        "- TASK-293 does not copy external evidence\n"
        "- TASK-293 confirms MQ5 inventory remains 7 files\n"
        "- TASK-293 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- current task is TASK-DOC-294 create future MQL5 compile-only boundary packet\n"
        "- TASK-DOC-294 create future MQL5 compile-only boundary packet\n"
        "- TASK-293 completed\n"
        "- TASK-293 completion commit is 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report\n"
        "- TASK-293 completion tag is v0.5.92-task-293-mq5-compile-readiness-final-summary\n"
        "- current HEAD is 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report\n"
        "- current tag is v0.5.92-task-293-mq5-compile-readiness-final-summary\n"
        "- TASK-DOC-294 is planning-only / boundary-only\n"
        "- TASK-DOC-294 creates docs/V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md\n"
        "- TASK-DOC-294 defines a future MQL5 compile-only candidate\n"
        "- TASK-DOC-294 is not implementation authorization\n"
        "- TASK-DOC-294 is not MT5 run authorization\n"
        "- TASK-DOC-294 is not Strategy Tester authorization\n"
        "- TASK-DOC-294 is not backtest authorization\n"
        "- TASK-DOC-294 is not simulation trading authorization\n"
        "- TASK-DOC-294 is not real trading authorization\n"
        "- TASK-DOC-294 is not evidence generation authorization\n"
        "- TASK-DOC-294 is not manifest generation authorization\n"
        "- TASK-DOC-294 is not external evidence copy authorization\n"
        "- mql5-compile-only-boundary check is added to release validation bundle\n"
        "- mq5-compile-readiness-final-summary alias check remains read-only and stdout-only\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-boundary check\n"
        "- no compile executed in TASK-DOC-294\n"
        "- no MetaEditor executed in TASK-DOC-294\n"
        "- no MetaEditor execution\n"
        "- no .ex5 artifact generated\n"
        "- no MQL5 compile\n"
        "- TASK-DOC-294 does not run MT5\n"
        "- TASK-DOC-294 does not execute MQL5 compile\n"
        "- TASK-DOC-294 does not modify MQ5 / MQH\n"
        "- TASK-DOC-294 does not create manifest / fixture / report / directory\n"
        "- TASK-DOC-294 does not copy external evidence\n"
        "- future compile-only task must be separately authorized by GPT\n"
        "- future compile-only task must remain no-trade\n"
        "- future compile-only task must not create manifest / evidence / report\n"
        "- future compile-only task must only produce stdout / terminal result unless separately authorized\n"
        "- TASK-295 must not be entered directly without a new GPT boundary\n"
        "- GPT must define a separate future boundary before TASK-295\n"
        "- current task is TASK-295 implement MQL5 compile-only command discovery boundary\n"
        "- TASK-295 implement MQL5 compile-only command discovery boundary\n"
        "- TASK-DOC-294 completed\n"
        "- TASK-DOC-294 completion commit is 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet\n"
        "- TASK-DOC-294 completion tag is v0.5.93-task-294-future-mql5-compile-only-boundary\n"
        "- current HEAD is 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet\n"
        "- current tag is v0.5.93-task-294-future-mql5-compile-only-boundary\n"
        "- TASK-295 is command-discovery-only\n"
        "- TASK-295 creates docs/V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md\n"
        "- mql5-compile-only-command-discovery check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-command-discovery check\n"
        "- mql5-compile-only-command-discovery PASS\n"
        "- metaeditor_executed=false\n"
        "- mql5_compile_executed=false\n"
        "- no MT5 run\n"
        "- no MQL5 compile\n"
        "- no MetaEditor execution\n"
        "- no .ex5 artifact\n"
        "- no compile log\n"
        "- no trading authorization\n"
        "- TASK-295 no trading authorization\n"
        "- TASK-295 does not modify MQ5 / MQH\n"
        "- TASK-295 does not run MT5\n"
        "- TASK-295 does not execute MetaEditor\n"
        "- TASK-295 does not execute MQL5 compile\n"
        "- TASK-295 does not create .ex5 artifact\n"
        "- TASK-295 does not create compile log\n"
        "- TASK-295 does not create manifest / fixture / report / directory\n"
        "- TASK-295 does not copy external evidence\n"
        "- TASK-295 confirms MQ5 inventory remains 7 files\n"
        "- TASK-295 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-296 must not be entered directly\n"
        "- current task is TASK-296 implement MQL5 compile-only artifact quarantine boundary\n"
        "- TASK-296 implement MQL5 compile-only artifact quarantine boundary\n"
        "- TASK-295 completed\n"
        "- TASK-295 completion commit is acda17c TASK-295 implement MQL5 compile-only command discovery boundary\n"
        "- TASK-295 completion tag is v0.5.94-task-295-mql5-compile-only-command-discovery\n"
        "- current HEAD is acda17c TASK-295 implement MQL5 compile-only command discovery boundary\n"
        "- current tag is v0.5.94-task-295-mql5-compile-only-command-discovery\n"
        "- TASK-296 is artifact-quarantine-only\n"
        "- TASK-296 creates docs/V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md\n"
        "- mql5-compile-only-artifact-quarantine check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-artifact-quarantine check\n"
        "- mql5-compile-only-artifact-quarantine PASS\n"
        "- repo_ex5_artifacts=false\n"
        "- repo_compile_logs=false\n"
        "- metaeditor_executed=false\n"
        "- mql5_compile_executed=false\n"
        "- no MT5 run\n"
        "- no MQL5 compile\n"
        "- no MetaEditor execution\n"
        "- no .ex5 artifact\n"
        "- no compile log\n"
        "- no trading authorization\n"
        "- TASK-296 does not modify MQ5 / MQH\n"
        "- TASK-296 does not run MT5\n"
        "- TASK-296 does not execute MetaEditor\n"
        "- TASK-296 does not execute MQL5 compile\n"
        "- TASK-296 does not create .ex5 artifact\n"
        "- TASK-296 does not create compile log\n"
        "- TASK-296 does not create manifest / fixture / report / directory\n"
        "- TASK-296 does not copy external evidence\n"
        "- TASK-296 confirms MQ5 inventory remains 7 files\n"
        "- TASK-296 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- future TASK-297 must be separately authorized by GPT before any compile execution\n"
        "- TASK-297 must not be entered directly\n"
        "- future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes\n"
        "- future compile-only execution must check repository has no .ex5 before and after compile\n"
        "- future compile-only execution must check repository has no compile log before and after compile\n"
        "- compile-only command may be executed only after GPT defines TASK-297 boundary\n"
        "- post-compile check: no MT5 run\n"
        "- post-compile check: no Strategy Tester\n"
        "- post-compile check: no trading\n"
        "- current task is TASK-297 implement future MQL5 compile-only execution boundary\n"
        "- TASK-297 implement future MQL5 compile-only execution boundary\n"
        "- TASK-296 completed\n"
        "- TASK-296 completion commit is 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary\n"
        "- TASK-296 completion tag is v0.5.95-task-296-mql5-compile-only-artifact-quarantine\n"
        "- current HEAD is 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary\n"
        "- current tag is v0.5.95-task-296-mql5-compile-only-artifact-quarantine\n"
        "- TASK-297 is compile-only-task\n"
        "- TASK-297 is future compile-only candidate\n"
        "- TASK-297 requires GPT explicit authorization\n"
        "- TASK-297 confirms artifact quarantine checked\n"
        "- TASK-297 creates docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md\n"
        "- mql5-compile-only-execution-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-execution-boundary check\n"
        "- mql5-compile-only-execution-boundary PASS\n"
        "- TASK-297 does not modify MQ5 / MQH\n"
        "- TASK-297 does not run MT5\n"
        "- TASK-297 does not execute MetaEditor\n"
        "- TASK-297 does not execute MQL5 compile\n"
        "- TASK-297 does not create .ex5 artifact\n"
        "- TASK-297 does not create compile log\n"
        "- TASK-297 does not create manifest / fixture / report / directory\n"
        "- TASK-297 does not copy external evidence\n"
        "- TASK-297 confirms MQ5 inventory remains 7 files\n"
        "- TASK-297 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- future TASK-298 must be separately authorized by GPT\n"
        "- future TASK-298 must not be entered directly\n"
        "- current task is TASK-298 implement MQL5 compile-only dry-run simulation\n"
        "- TASK-298 implement MQL5 compile-only dry-run simulation\n"
        "- TASK-298 is dry-run-only\n"
        "- TASK-298 enforces artifact-quarantine\n"
        "- TASK-298 uses stdout-only simulation\n"
        "- TASK-298 creates docs/V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md\n"
        "- mql5-compile-only-dryrun check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-dryrun check\n"
        "- mql5-compile-only-dryrun PASS\n"
        "- TASK-298 does not modify MQ5 / MQH\n"
        "- TASK-298 does not run MT5\n"
        "- TASK-298 does not execute MetaEditor\n"
        "- TASK-298 does not execute MQL5 compile\n"
        "- TASK-298 does not create .ex5 artifact\n"
        "- TASK-298 does not create compile log\n"
        "- TASK-298 does not create manifest / fixture / report / directory\n"
        "- TASK-298 does not copy external evidence\n"
        "- TASK-298 confirms MQ5 inventory remains 7 files\n"
        "- TASK-298 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-299 must not be entered directly\n"
        "- current task is TASK-299 reconcile TASK-297 MQL5 compile-only execution boundary tracking gap\n"
        "- TASK-299 reconcile TASK-297 MQL5 compile-only execution boundary tracking gap\n"
        "- TASK-298 completed\n"
        "- TASK-298 completion commit is 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary\n"
        "- TASK-298 completion tag is v0.5.96-task-298-mql5-compile-only-dryrun\n"
        "- current HEAD is 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary\n"
        "- current tag is v0.5.96-task-298-mql5-compile-only-dryrun\n"
        "- TASK-297 files were untracked tracking gap items before TASK-299 reconciliation\n"
        "- TASK-299 reconciles docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md\n"
        "- TASK-299 reconciles tools/validate_mql5_compile_only_execution_boundary.py\n"
        "- TASK-299 reconciles tools/test_validate_mql5_compile_only_execution_boundary.py\n"
        "- TASK-299 does not recreate old TASK-297 tag\n"
        "- TASK-299 does not move historical tags\n"
        "- TASK-299 keeps mql5-compile-only-execution-boundary in release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-execution-boundary check\n"
        "- workflow-closure-audit includes mql5-compile-only-execution-boundary check\n"
        "- mql5-compile-only-execution-boundary PASS\n"
        "- TASK-299 does not modify MQ5 / MQH\n"
        "- TASK-299 does not run MT5\n"
        "- TASK-299 does not execute MetaEditor\n"
        "- TASK-299 does not execute MQL5 compile\n"
        "- TASK-299 does not create .ex5 artifact\n"
        "- TASK-299 does not create compile log\n"
        "- TASK-299 does not create manifest / fixture / report / directory\n"
        "- TASK-299 does not copy external evidence\n"
        "- TASK-299 confirms MQ5 inventory remains 7 files\n"
        "- TASK-299 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-300 must not be entered directly\n"
        "- current task is TASK-300 implement MQL5 compile-only dry-run execution simulation\n"
        "- TASK-300 implement MQL5 compile-only dry-run execution simulation\n"
        "- TASK-299 completed\n"
        "- TASK-299 reconciled TASK-297 MQL5 compile-only execution boundary tracking gap\n"
        "- current HEAD is 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary\n"
        "- current tag is v0.5.96-task-298-mql5-compile-only-dryrun\n"
        "- TASK-300 creates docs/V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md\n"
        "- mql5-compile-only-dryrun-execution check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-dryrun-execution check\n"
        "- workflow-closure-audit includes mql5-compile-only-dryrun-execution check\n"
        "- mql5-compile-only-dryrun-execution PASS\n"
        "- TASK-300 is dry-run-execution-only\n"
        "- TASK-300 uses stdout-only simulation\n"
        "- TASK-300 enforces artifact-quarantine\n"
        "- TASK-300 generates stdout-only candidate output\n"
        "- TASK-300 does not modify MQ5 / MQH\n"
        "- TASK-300 does not run MT5\n"
        "- TASK-300 does not execute MetaEditor\n"
        "- TASK-300 does not execute MQL5 compile\n"
        "- TASK-300 does not create .ex5 artifact\n"
        "- TASK-300 does not create compile log\n"
        "- TASK-300 does not create manifest / fixture / report / directory\n"
        "- TASK-300 does not copy external evidence\n"
        "- TASK-300 confirms MQ5 inventory remains 7 files\n"
        "- TASK-300 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-301 must not be entered directly\n"
        "- current task is TASK-301 create v0.6.0 compile-readiness planning packet\n"
        "- TASK-301 create v0.6.0 compile-readiness planning packet\n"
        "- TASK-299-300 reconciliation completed\n"
        "- TASK-299-300 completion commit is fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation\n"
        "- TASK-299-300 completion tag is v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation\n"
        "- current HEAD is fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation\n"
        "- current tag is v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation\n"
        "- TASK-301 creates docs/V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md\n"
        "- v060-compile-readiness-planning check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes v060-compile-readiness-planning check\n"
        "- workflow-closure-audit includes v060-compile-readiness-planning check\n"
        "- v060-compile-readiness-planning PASS\n"
        "- TASK-301 is planning-only\n"
        "- TASK-301 is future compile-readiness candidate\n"
        "- TASK-301 is not implementation authorization\n"
        "- TASK-301 does not modify MQ5 / MQH\n"
        "- TASK-301 does not run MT5\n"
        "- TASK-301 does not run Strategy Tester\n"
        "- TASK-301 does not authorize backtest\n"
        "- TASK-301 does not authorize simulation / real trading\n"
        "- TASK-301 does not execute MetaEditor\n"
        "- TASK-301 does not execute MQL5 compile\n"
        "- TASK-301 does not create .ex5 artifact\n"
        "- TASK-301 does not create compile log\n"
        "- TASK-301 does not create evidence / manifest / report\n"
        "- TASK-301 does not create manifest / fixture / report / directory\n"
        "- TASK-301 does not copy external evidence\n"
        "- TASK-301 confirms MQ5 inventory 7 files\n"
        "- TASK-301 confirms MQ5 inventory remains 7 files\n"
        "- TASK-301 confirms Buy / Sell / OrderSend / PositionOpen / CTrade false\n"
        "- TASK-301 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- TASK-302 must not be entered directly without GPT authorization\n"
        "- current task is TASK-302 implement MQL5 compile-only execution preflight gate\n"
        "- TASK-302 implement MQL5 compile-only execution preflight gate\n"
        "- TASK-301 completed\n"
        "- TASK-301 completion commit is 2f0498b TASK-301 create v060 compile-readiness planning packet\n"
        "- TASK-301 completion tag is v0.5.98-task-301-v060-compile-readiness-planning\n"
        "- current HEAD is 2f0498b TASK-301 create v060 compile-readiness planning packet\n"
        "- current tag is v0.5.98-task-301-v060-compile-readiness-planning\n"
        "- TASK-302 creates docs/V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md\n"
        "- TASK-302 creates tools/validate_mql5_compile_only_preflight_gate.py\n"
        "- TASK-302 creates tools/test_validate_mql5_compile_only_preflight_gate.py\n"
        "- mql5-compile-only-preflight-gate check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-preflight-gate check\n"
        "- workflow-closure-audit includes mql5-compile-only-preflight-gate check\n"
        "- mql5-compile-only-preflight-gate PASS\n"
        "- TASK-302 is preflight-gate-only\n"
        "- TASK-302 does not modify MQ5 / MQH\n"
        "- TASK-302 does not run MT5\n"
        "- TASK-302 does not execute MetaEditor\n"
        "- TASK-302 does not execute MQL5 compile\n"
        "- TASK-302 does not execute /compile command\n"
        "- TASK-302 does not authorize Strategy Tester\n"
        "- TASK-302 does not authorize backtest\n"
        "- TASK-302 does not authorize trading\n"
        "- TASK-302 does not create .ex5 artifact\n"
        "- TASK-302 does not create compile log\n"
        "- TASK-302 does not create manifest / fixture / report / directory\n"
        "- TASK-302 does not copy external evidence\n"
        "- TASK-302 preflight gate confirms repository has no ex5 artifacts\n"
        "- TASK-302 preflight gate confirms repository has no compile logs\n"
        "- TASK-302 preflight gate confirms MetaEditor was not executed\n"
        "- TASK-302 preflight gate confirms MQL5 compile was not executed\n"
        "- TASK-302 preflight gate confirms MT5 was not run\n"
        "- TASK-302 preflight gate confirms trading remains unauthorized\n"
        "- TASK-302 preflight gate confirms compile execution remains unauthorized\n"
        "- TASK-302 preflight gate confirms future TASK-303 requires GPT boundary\n"
        "- all previous compile-only boundary checks must pass before future compile execution\n"
        "- artifact quarantine must pass before future compile execution\n"
        "- future compile-only command must remain stdout-only unless GPT separately authorizes artifact handling\n"
        "- TASK-303 must not be entered directly\n"
        "- future TASK-303 must be separately authorized by GPT before any compile execution\n"
        "- current task is TASK-303 create v0.6.0 compile-only execution authorization planning packet\n"
        "- TASK-303 create v0.6.0 compile-only execution authorization planning packet\n"
        "- TASK-302 completed\n"
        "- TASK-302 completion commit is 15c675e TASK-302 implement MQL5 compile-only execution preflight gate\n"
        "- TASK-302 completion tag is v0.5.99-task-302-mql5-compile-only-preflight-gate\n"
        "- current HEAD is 15c675e TASK-302 implement MQL5 compile-only execution preflight gate\n"
        "- current tag is v0.5.99-task-302-mql5-compile-only-preflight-gate\n"
        "- TASK-303 creates docs/V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md\n"
        "- TASK-303 creates tools/validate_mql5_compile_only_execution_authorization_plan.py\n"
        "- TASK-303 creates tools/test_validate_mql5_compile_only_execution_authorization_plan.py\n"
        "- mql5-compile-only-execution-authorization-plan check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-execution-authorization-plan check\n"
        "- workflow-closure-audit includes mql5-compile-only-execution-authorization-plan check\n"
        "- mql5-compile-only-execution-authorization-plan PASS\n"
        "- TASK-303 is planning-only\n"
        "- TASK-303 is authorization-boundary-only\n"
        "- TASK-303 is future compile-only execution candidate\n"
        "- TASK-303 does not modify MQ5 / MQH\n"
        "- TASK-303 does not run MT5\n"
        "- TASK-303 does not execute MetaEditor\n"
        "- TASK-303 does not execute MQL5 compile\n"
        "- TASK-303 does not execute /compile command\n"
        "- TASK-303 does not authorize Strategy Tester\n"
        "- TASK-303 does not authorize backtest\n"
        "- TASK-303 does not authorize simulation trading\n"
        "- TASK-303 does not authorize real trading\n"
        "- TASK-303 does not create .ex5 artifact\n"
        "- TASK-303 does not create compile log\n"
        "- TASK-303 does not create manifest / fixture / report / directory\n"
        "- TASK-303 does not copy external evidence\n"
        "- TASK-303 confirms compile execution remains unauthorized\n"
        "- TASK-303 confirms MetaEditor was not executed\n"
        "- TASK-303 confirms MQL5 compile was not executed\n"
        "- TASK-303 confirms future TASK-304 requires GPT boundary\n"
        "- compile_execution_authorized=false\n"
        "- future_task_304_requires_gpt_boundary=true\n"
        "- metaeditor_executed=false\n"
        "- mql5_compile_executed=false\n"
        "- all previous MQ5 static / no-trade / compile-readiness checks PASS\n"
        "- all previous MQL5 compile-only boundary / discovery / quarantine / dry-run / preflight checks PASS\n"
        "- TASK-304 must not be entered directly\n"
        "- future TASK-304 must be separately authorized by GPT before any compile execution\n"
        "- current task is TASK-305 implement MQL5 compile-only failure diagnostic capture\n"
        "- TASK-305 implement MQL5 compile-only failure diagnostic capture\n"
        "- TASK-304 failed, no success result doc created\n"
        "- TASK-304 is not compile success\n"
        "- TASK-304 compile_exit_code=1 was observed\n"
        "- current HEAD is 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet\n"
        "- current tag is v0.5.100-task-303-v060-compile-only-execution-authorization\n"
        "- TASK-305 creates docs/V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md\n"
        "- TASK-305 creates tools/validate_mql5_compile_only_failure_diagnostic.py\n"
        "- TASK-305 creates tools/test_validate_mql5_compile_only_failure_diagnostic.py\n"
        "- tools/run_mql5_compile_only_quarantined.py supports --diagnostic-capture\n"
        "- mql5-compile-only-failure-diagnostic check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-only-failure-diagnostic check\n"
        "- workflow-closure-audit includes mql5-compile-only-failure-diagnostic check\n"
        "- TASK-305 may re-run MetaEditor compile-only only against quarantine copy\n"
        "- TASK-305 diagnostic output is stdout-only\n"
        "- compile log must be stdout-only\n"
        "- compile log must not be saved to repository\n"
        "- no repo .ex5\n"
        "- no repo compile log\n"
        "- no MT5 terminal\n"
        "- no Strategy Tester\n"
        "- no trading\n"
        "- no manifest / evidence / report\n"
        "- TASK-306 requires GPT boundary\n"
        "- TASK-306 must not be entered directly\n"
        "- current task is TASK-306 implement MQL5 compile-only diagnostic result classification\n"
        "- TASK-306 implement MQL5 compile-only diagnostic result classification\n"
        "- TASK-305 completed\n"
        "- TASK-305 completion commit is c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture\n"
        "- TASK-305 completion tag is v0.5.101-task-305-mql5-compile-only-failure-diagnostic\n"
        "- current HEAD is c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture\n"
        "- current tag is v0.5.101-task-305-mql5-compile-only-failure-diagnostic\n"
        "- TASK-306 creates docs/V060_TASK_306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION.md\n"
        "- TASK-306 creates tools/validate_mql5_compile_diagnostic_result_classification.py\n"
        "- TASK-306 creates tools/test_validate_mql5_compile_diagnostic_result_classification.py\n"
        "- tools/run_mql5_compile_only_quarantined.py supports classify_compile_diagnostic_result\n"
        "- mql5-compile-diagnostic-result-classification check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-diagnostic-result-classification check\n"
        "- workflow-closure-audit includes mql5-compile-diagnostic-result-classification check\n"
        "- TASK-306 is diagnostic-classification-only\n"
        "- TASK-306 is not compile execution\n"
        "- TASK-306 has no new MetaEditor execution in TASK-306\n"
        "- not MetaEditor execution in TASK-306\n"
        "- TASK-306 does not run MT5 terminal\n"
        "- TASK-306 does not run Strategy Tester\n"
        "- TASK-306 does not run backtest\n"
        "- TASK-306 does not trade\n"
        "- compile_exit_code=1 observed in TASK-305\n"
        "- compile log semantic result indicates Result: 0 errors, 0 warnings\n"
        "- compile_result_classification=metaeditor_exit_code_anomaly\n"
        "- compile_log_semantic_success=true\n"
        "- compile_success=false\n"
        "- task304_success_result_created=false\n"
        "- followup_required=true\n"
        "- repo_ex5_artifacts=false\n"
        "- repo_compile_logs=false\n"
        "- TASK-307 requires GPT boundary before any compile retry or MQ5 fix\n"
        "- TASK-307 must not be entered directly\n"
        "- current task is TASK-307 implement MQL5 compile diagnostic artifact classification\n"
        "- TASK-307 implement MQL5 compile diagnostic artifact classification\n"
        "- TASK-306 completed\n"
        "- TASK-306 completion commit is 560079c TASK-306 implement MQL5 compile-only diagnostic result classification\n"
        "- TASK-306 completion tag is v0.5.102-task-306-mql5-compile-diagnostic-classification\n"
        "- current HEAD is 560079c TASK-306 implement MQL5 compile-only diagnostic result classification\n"
        "- current tag is v0.5.102-task-306-mql5-compile-diagnostic-classification\n"
        "- TASK-307 creates docs/V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md\n"
        "- TASK-307 creates tools/validate_mql5_compile_diagnostic_artifact_classification.py\n"
        "- TASK-307 creates tools/test_validate_mql5_compile_diagnostic_artifact_classification.py\n"
        "- tools/run_mql5_compile_only_quarantined.py supports quarantine artifact inspection before cleanup\n"
        "- tools/run_mql5_compile_only_quarantined.py reports quarantine_ex5_artifact_detected\n"
        "- tools/run_mql5_compile_only_quarantined.py reports quarantine_ex5_artifact_count\n"
        "- tools/run_mql5_compile_only_quarantined.py reports quarantine_compile_log_detected\n"
        "- mql5-compile-diagnostic-artifact-classification check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-diagnostic-artifact-classification check\n"
        "- workflow-closure-audit includes mql5-compile-diagnostic-artifact-classification check\n"
        "- TASK-307 is diagnostic-artifact-classification-only\n"
        "- TASK-307 is not TASK-304 success result\n"
        "- TASK-307 may re-run MetaEditor compile-only only against quarantine copy\n"
        "- quarantine artifact inspection before cleanup\n"
        "- quarantine .ex5 must not be copied to repository\n"
        "- compile_success=false unless a future GPT boundary explicitly reclassifies success\n"
        "- TASK-308 requires GPT boundary before any compile retry or MQ5 fix\n"
        "- TASK-308 must not be entered directly\n"
        "- current task is TASK-308 create MQL5 compile diagnostic artifact proof and success reclassification boundary\n"
        "- TASK-308 create MQL5 compile diagnostic artifact proof and success reclassification boundary\n"
        "- TASK-307 completed\n"
        "- TASK-307 completion commit is 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification\n"
        "- TASK-307 completion tag is v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification\n"
        "- current HEAD is 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification\n"
        "- current tag is v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification\n"
        "- TASK-308 creates docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md\n"
        "- TASK-308 creates tools/validate_mql5_compile_diagnostic_artifact_proof_boundary.py\n"
        "- TASK-308 creates tools/test_validate_mql5_compile_diagnostic_artifact_proof_boundary.py\n"
        "- mql5-compile-diagnostic-artifact-proof-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-diagnostic-artifact-proof-boundary check\n"
        "- workflow-closure-audit includes mql5-compile-diagnostic-artifact-proof-boundary check\n"
        "- TASK-308 is planning-only\n"
        "- TASK-308 is diagnostic-proof-boundary-only\n"
        "- TASK-308 is no compile execution\n"
        "- TASK-308 has no MetaEditor execution\n"
        "- no MetaEditor execution\n"
        "- no MQL5 compile\n"
        "- no .ex5 artifact\n"
        "- no compile log\n"
        "- no success reclassification in TASK-308\n"
        "- success_reclassification_done=false\n"
        "- TASK-307 observed quarantine_ex5_artifact_detected=true\n"
        "- TASK-307 observed compile_log_semantic_success=true\n"
        "- TASK-307 observed compile_exit_code=1\n"
        "- previous classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n"
        "- compiled_artifact_with_metaeditor_exit_code_anomaly\n"
        "- compile_success=false\n"
        "- task304_success_result_created=false\n"
        "- future_task_309_requires_gpt_boundary=true\n"
        "- future TASK-309 requires GPT boundary before any compile retry, MQ5 fix, artifact hash capture, or success reclassification\n"
        "- TASK-309 must not be entered directly\n"
        "- current task is TASK-309 create MQL5 compile-only success reclassification boundary\n"
        "- TASK-309 create MQL5 compile-only success reclassification boundary\n"
        "- TASK-308 completed\n"
        "- TASK-308 completion commit is 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary\n"
        "- TASK-308 completion tag is v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary\n"
        "- current HEAD is 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary\n"
        "- current tag is v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary\n"
        "- TASK-309 creates docs/V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md\n"
        "- TASK-309 creates tools/validate_mql5_compile_success_reclassification_boundary.py\n"
        "- TASK-309 creates tools/test_validate_mql5_compile_success_reclassification_boundary.py\n"
        "- mql5-compile-success-reclassification-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-success-reclassification-boundary check\n"
        "- workflow-closure-audit includes mql5-compile-success-reclassification-boundary check\n"
        "- TASK-309 is planning-only\n"
        "- TASK-309 is success-reclassification-boundary-only\n"
        "- TASK-309 is no compile execution\n"
        "- TASK-309 has no MetaEditor execution\n"
        "- no success reclassification in TASK-309\n"
        "- success_reclassification_done=false\n"
        "- TASK-307 observed quarantine_ex5_artifact_count=1\n"
        "- future_task_310_requires_gpt_boundary=true\n"
        "- future TASK-310 requires GPT boundary before any compile retry, artifact hash capture, success reclassification, or MQ5 fix\n"
        "- TASK-310 must not be entered directly\n"
        "- current task is TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic\n"
        "- TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic\n"
        "- TASK-309 completed\n"
        "- TASK-309 completion commit is f31b85e TASK-309 create MQL5 compile-only success reclassification boundary\n"
        "- TASK-309 completion tag is v0.5.105-task-309-mql5-compile-success-reclassification-boundary\n"
        "- current HEAD is f31b85e TASK-309 create MQL5 compile-only success reclassification boundary\n"
        "- current tag is v0.5.105-task-309-mql5-compile-success-reclassification-boundary\n"
        "- TASK-310 creates docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md\n"
        "- TASK-310 creates tools/validate_mql5_compile_artifact_hash_capture_boundary.py\n"
        "- TASK-310 creates tools/test_validate_mql5_compile_artifact_hash_capture_boundary.py\n"
        "- mql5-compile-artifact-hash-capture-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-artifact-hash-capture-boundary check\n"
        "- workflow-closure-audit includes mql5-compile-artifact-hash-capture-boundary check\n"
        "- TASK-310 is artifact-hash-capture-diagnostic-only\n"
        "- artifact hash stdout-only\n"
        "- artifact hash not saved to repository\n"
        "- compile_success=false\n"
        "- success_reclassification_done=false\n"
        "- task304_success_result_created=false\n"
        "- future_task_311_requires_gpt_boundary=true\n"
        "- future TASK-311 requires GPT boundary before success reclassification or MQ5 fix\n"
        "- TASK-311 must not be entered directly\n"
        "- current task is TASK-311 create MQL5 compile success reclassification decision boundary\n"
        "- TASK-311 create MQL5 compile success reclassification decision boundary\n"
        "- TASK-310 completed\n"
        "- TASK-310 completion commit is 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic\n"
        "- TASK-310 completion tag is v0.5.106-task-310-mql5-compile-artifact-hash-capture\n"
        "- current HEAD is 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic\n"
        "- current tag is v0.5.106-task-310-mql5-compile-artifact-hash-capture\n"
        "- TASK-311 creates docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md\n"
        "- TASK-311 creates tools/validate_mql5_compile_success_reclassification_decision_boundary.py\n"
        "- TASK-311 creates tools/test_validate_mql5_compile_success_reclassification_decision_boundary.py\n"
        "- mql5-compile-success-reclassification-decision-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-success-reclassification-decision-boundary check\n"
        "- workflow-closure-audit includes mql5-compile-success-reclassification-decision-boundary check\n"
        "- TASK-311 is planning-only\n"
        "- TASK-311 is success-reclassification-decision-boundary-only\n"
        "- no MetaEditor execution in TASK-311\n"
        "- no MQL5 compile in TASK-311\n"
        "- no success reclassification in TASK-311\n"
        "- artifact hash was stdout-only and must not be stored in repository\n"
        "- artifact_hash_stored_in_repo=false\n"
        "- previous classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly\n"
        "- compile_success=false\n"
        "- success_reclassification_done=false\n"
        "- task304_success_result_created=false\n"
        "- future_task_312_requires_gpt_boundary=true\n"
        "- future TASK-312 requires GPT boundary before success reclassification, MQ5 fix, or compile retry\n"
        "- TASK-312 must not be entered directly\n"
        "- current task is TASK-312 implement controlled MQL5 compile-only success reclassification decision\n"
        "- TASK-312 implement controlled MQL5 compile-only success reclassification decision\n"
        "- TASK-311 completed\n"
        "- TASK-311 completion commit is 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary\n"
        "- TASK-311 completion tag is v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary\n"
        "- current HEAD is 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary\n"
        "- current tag is v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary\n"
        "- TASK-312 creates docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md\n"
        "- TASK-312 creates tools/validate_mql5_compile_success_reclassification_decision.py\n"
        "- TASK-312 creates tools/test_validate_mql5_compile_success_reclassification_decision.py\n"
        "- mql5-compile-success-reclassification-decision check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mql5-compile-success-reclassification-decision check\n"
        "- workflow-closure-audit includes mql5-compile-success-reclassification-decision check\n"
        "- TASK-312 is controlled-success-reclassification-attempt\n"
        "- success_reclassification_decision=PASS\n"
        "- compile_only_reclassified_success=true\n"
        "- compile_success=true\n"
        "- compile_success_scope=compile-only-diagnostic\n"
        "- compile-only success does not imply trading authorization\n"
        "- compile-only success does not imply deployment readiness\n"
        "- compile-only success does not imply backtest readiness\n"
        "- compile-only success does not imply strategy readiness\n"
        "- artifact_hash_stdout_only=true\n"
        "- artifact_hash_saved_to_repo=false\n"
        "- do not include actual artifact hash value in this doc\n"
        "- future_task_313_requires_gpt_boundary=true\n"
        "- future TASK-313 requires GPT boundary before MT5 run, Strategy Tester, backtest, deployment, or trading-related step\n"
        "- TASK-313 must not be entered directly\n"
        "- current task is TASK-313 create MT5 terminal no-trade startup boundary packet\n"
        "- TASK-313 create MT5 terminal no-trade startup boundary packet\n"
        "- TASK-312 completed\n"
        "- TASK-312 completion commit is efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision\n"
        "- TASK-312 completion tag is v0.5.108-task-312-mql5-compile-success-reclassification-decision\n"
        "- current HEAD is efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision\n"
        "- current tag is v0.5.108-task-312-mql5-compile-success-reclassification-decision\n"
        "- TASK-313 creates docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md\n"
        "- TASK-313 creates tools/validate_mt5_no_trade_startup_boundary.py\n"
        "- TASK-313 creates tools/test_validate_mt5_no_trade_startup_boundary.py\n"
        "- mt5-no-trade-startup-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mt5-no-trade-startup-boundary check\n"
        "- workflow-closure-audit includes mt5-no-trade-startup-boundary check\n"
        "- TASK-313 is planning-only\n"
        "- TASK-313 is mt5-startup-boundary-only\n"
        "- no MT5 run in TASK-313\n"
        "- no terminal64 execution\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- compile_success_scope=compile-only-diagnostic\n"
        "- trading_authorization=false\n"
        "- deployment_readiness=false\n"
        "- backtest_readiness=false\n"
        "- strategy_readiness=false\n"
        "- future_task_314_requires_gpt_boundary=true\n"
        "- future TASK-314 requires GPT boundary before MT5 terminal startup attempt\n"
        "- TASK-314 must not be entered directly\n"
        "- current task is TASK-314 implement MT5 no-trade startup command discovery boundary\n"
        "- TASK-314 implement MT5 no-trade startup command discovery boundary\n"
        "- TASK-313 completed\n"
        "- TASK-313 completion commit is 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet\n"
        "- TASK-313 completion tag is v0.5.109-task-313-mt5-no-trade-startup-boundary\n"
        "- current HEAD is 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet\n"
        "- current tag is v0.5.109-task-313-mt5-no-trade-startup-boundary\n"
        "- TASK-314 creates docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md\n"
        "- TASK-314 creates tools/validate_mt5_no_trade_startup_command_discovery.py\n"
        "- TASK-314 creates tools/test_validate_mt5_no_trade_startup_command_discovery.py\n"
        "- mt5-no-trade-startup-command-discovery check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mt5-no-trade-startup-command-discovery check\n"
        "- workflow-closure-audit includes mt5-no-trade-startup-command-discovery check\n"
        "- TASK-314 is command-discovery-only\n"
        "- TASK-314 is mt5-startup-preparation-only\n"
        "- no MT5 run in TASK-314\n"
        "- no terminal64 execution\n"
        "- no terminal64.exe execution\n"
        "- no terminal.exe execution\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- compile_success_scope=compile-only-diagnostic\n"
        "- trading_authorization=false\n"
        "- deployment_readiness=false\n"
        "- backtest_readiness=false\n"
        "- strategy_readiness=false\n"
        "- future_task_315_requires_gpt_boundary=true\n"
        "- future TASK-315 requires GPT boundary before any MT5 terminal startup attempt\n"
        "- TASK-315 must not be entered directly\n"
        "- current task is TASK-315 implement MT5 no-trade startup quarantine preparation boundary\n"
        "- TASK-315 implement MT5 no-trade startup quarantine preparation boundary\n"
        "- TASK-314 completed\n"
        "- TASK-314 completion commit is ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary\n"
        "- TASK-314 completion tag is v0.5.110-task-314-mt5-no-trade-startup-command-discovery\n"
        "- current HEAD is ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary\n"
        "- current tag is v0.5.110-task-314-mt5-no-trade-startup-command-discovery\n"
        "- TASK-315 creates docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md\n"
        "- TASK-315 creates tools/validate_mt5_no_trade_startup_quarantine_preparation.py\n"
        "- TASK-315 creates tools/test_validate_mt5_no_trade_startup_quarantine_preparation.py\n"
        "- mt5-no-trade-startup-quarantine-preparation check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mt5-no-trade-startup-quarantine-preparation check\n"
        "- workflow-closure-audit includes mt5-no-trade-startup-quarantine-preparation check\n"
        "- TASK-315 is planning-only\n"
        "- TASK-315 is startup-quarantine-preparation-only\n"
        "- startup_quarantine_outside_repo_required=true\n"
        "- repo_terminal_data_directory=false\n"
        "- repo_startup_logs=false\n"
        "- no MT5 run in TASK-315\n"
        "- no terminal64.exe execution in TASK-315\n"
        "- no terminal.exe execution in TASK-315\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- compile_success_scope=compile-only-diagnostic\n"
        "- trading_authorization=false\n"
        "- deployment_readiness=false\n"
        "- backtest_readiness=false\n"
        "- strategy_readiness=false\n"
        "- future_task_316_requires_gpt_boundary=true\n"
        "- future TASK-316 requires GPT boundary before any MT5 terminal startup attempt\n"
        "- TASK-316 must not be entered directly\n"
        "- current task is TASK-316 implement MT5 no-trade startup dry-run config boundary\n"
        "- TASK-316 implement MT5 no-trade startup dry-run config boundary\n"
        "- TASK-315 completed\n"
        "- TASK-315 completion commit is 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary\n"
        "- TASK-315 completion tag is v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation\n"
        "- current HEAD is 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary\n"
        "- current tag is v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation\n"
        "- TASK-316 creates docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md\n"
        "- TASK-316 creates tools/validate_mt5_no_trade_startup_dryrun_config_boundary.py\n"
        "- TASK-316 creates tools/test_validate_mt5_no_trade_startup_dryrun_config_boundary.py\n"
        "- mt5-no-trade-startup-dryrun-config-boundary check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mt5-no-trade-startup-dryrun-config-boundary check\n"
        "- workflow-closure-audit includes mt5-no-trade-startup-dryrun-config-boundary check\n"
        "- TASK-316 is planning-only\n"
        "- TASK-316 is startup-dryrun-config-boundary-only\n"
        "- no_trade_config_generated_in_repo=false\n"
        "- no no-trade config file generated in repository\n"
        "- repo_terminal_data_directory=false\n"
        "- repo_startup_logs=false\n"
        "- no MT5 run in TASK-316\n"
        "- no terminal64.exe execution in TASK-316\n"
        "- no terminal.exe execution in TASK-316\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- compile_success_scope=compile-only-diagnostic\n"
        "- trading_authorization=false\n"
        "- deployment_readiness=false\n"
        "- backtest_readiness=false\n"
        "- strategy_readiness=false\n"
        "- future_task_317_requires_gpt_boundary=true\n"
        "- future TASK-317 requires GPT boundary before any MT5 terminal startup attempt\n"
        "- TASK-317 must not be entered directly\n"
        "- current task is TASK-317 implement MT5 no-trade startup config template preview\n"
        "- TASK-317 implement MT5 no-trade startup config template preview\n"
        "- TASK-316 completed\n"
        "- TASK-316 completion commit is a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary\n"
        "- TASK-316 completion tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary\n"
        "- current HEAD is a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary\n"
        "- current tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary\n"
        "- TASK-317 creates docs/V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md\n"
        "- TASK-317 creates tools/validate_mt5_no_trade_startup_config_template.py\n"
        "- TASK-317 creates tools/test_validate_mt5_no_trade_startup_config_template.py\n"
        "- mt5-no-trade-startup-config-template check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mt5-no-trade-startup-config-template check\n"
        "- workflow-closure-audit includes mt5-no-trade-startup-config-template check\n"
        "- TASK-317 is stdout-only-config-template-preview\n"
        "- config_file_generated=false\n"
        "- no_trade_config_generated_in_repo=false\n"
        "- no config file generated\n"
        "- no MT5 terminal executed\n"
        "- no terminal64 execution\n"
        "- no terminal.exe execution\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- no terminal data directory in repository\n"
        "- no startup log in repository\n"
        "- no no-trade config file generated in repository\n"
        "- future_task_318_requires_gpt_boundary=true\n"
        "- future TASK-318 requires GPT boundary before writing any startup config file or launching MT5\n"
        "- TASK-318 must not be entered directly\n"
        "- current task is TASK-318 implement MT5 no-trade startup authorization planning boundary\n"
        "- TASK-318 implement MT5 no-trade startup authorization planning boundary\n"
        "- TASK-317 completed\n"
        "- TASK-317 completion commit is a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview\n"
        "- TASK-317 completion tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary\n"
        "- current HEAD is a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview\n"
        "- current tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary\n"
        "- TASK-318 creates docs/V060_TASK_318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN.md\n"
        "- TASK-318 creates tools/validate_mt5_no_trade_startup_authorization_plan.py\n"
        "- TASK-318 creates tools/test_validate_mt5_no_trade_startup_authorization_plan.py\n"
        "- mt5-no-trade-startup-authorization-plan check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes mt5-no-trade-startup-authorization-plan check\n"
        "- workflow-closure-audit includes mt5-no-trade-startup-authorization-plan check\n"
        "- TASK-318 is planning-only\n"
        "- TASK-318 is authorization-boundary-only\n"
        "- config_file_generated=false\n"
        "- no_trade_config_generated_in_repo=false\n"
        "- no MT5 run in TASK-318\n"
        "- no terminal64.exe execution in TASK-318\n"
        "- no terminal.exe execution in TASK-318\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- no MetaEditor execution\n"
        "- no MQL5 compile\n"
        "- no .ex5 artifact\n"
        "- no compile log\n"
        "- no terminal data directory in repository\n"
        "- no startup log in repository\n"
        "- future_task_319_requires_gpt_boundary=true\n"
        "- future TASK-319 requires GPT boundary before any MT5 terminal startup execution\n"
        "- TASK-319 must not be entered directly\n"
        "- current task is TASK-321 implement parser pipeline integration completion\n"
        "- TASK-321 implement parser pipeline integration completion\n"
        "- TASK-319 completed\n"
        "- TASK-319 completion commit is 5f0a697 TASK-319 implement MT5 no-trade startup preflight gate\n"
        "- TASK-319 completion tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate\n"
        "- current HEAD is 9dfb42b TASK-321 implement parser pipeline integration completion\n"
        "- current tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate\n"
        "- TASK-321 creates docs/V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md\n"
        "- TASK-321 creates tools/parse_mql5_compile_log.py\n"
        "- TASK-321 creates tools/parse_backtest_set_params.py\n"
        "- TASK-321 creates tools/run_evidence_parser_pipeline.py\n"
        "- TASK-321 creates tools/validate_parser_manifest_integration.py\n"
        "- parser-manifest-integration check is added to release validation bundle\n"
        "- fast-no-trade-dev profile includes parser-manifest-integration check\n"
        "- fast-no-trade-dev profile includes backtest-set-params check\n"
        "- TASK-321 is parser-pipeline-integration-only\n"
        "- no MT5 run in TASK-321\n"
        "- no terminal64.exe execution in TASK-321\n"
        "- no Strategy Tester\n"
        "- no backtest\n"
        "- no trading authorization\n"
        "- no MetaEditor execution\n"
        "- no MQL5 compile\n"
        "- no .ex5 artifact\n"
        "- no compile log\n"
        "- no manifest generated in repository during TASK-321\n"
        "- no external evidence copied into repository\n"
        "- future_task_320_requires_gpt_boundary=true\n"
        "- future TASK-320 requires GPT boundary before any MT5 terminal startup attempt\n"
        "- TASK-320 must not be entered directly\n"
        "- no repo .ex5\n"
        "- no repo compile log\n"
        "- MQ5 inventory remains 7 files\n"
        "- MQ5 inventory 仍为 7 files\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n"
        "- Buy / Sell / OrderSend / PositionOpen / CTrade false\n"
        "- Inventory only; no MT5 run; no trading authorization.\n"
        "- mt5-no-trade-startup-preflight-gate PASS\n"
        "- parser-manifest-integration PASS\n"
        "- backtest-set-params PASS\n"
        "- current engineering gap: none after TASK-321 parser pipeline integration\n"
        "- do not directly enter TASK-284\n"
        "- do not directly enter v0.6.0 full implementation\n"
        "- do not directly enter trading, MT5 run, manifest creation, or backtest evidence\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "- current engineering gap: none\n"
        "- current safety boundary gap: none\n"
        "- current manifest gap: none\n"
        "- the next task boundary must be defined by ChatGPT\n\n"
        "## 当前下一步\n\n"
        f"{boundary_text}\n\n"
        "## 保留安全边界\n\n"
        "- 当前仍然不允许真实交易\n"
        "- SignalEngine 禁止下单\n"
        "- RiskManager 禁止被绕过\n"
        "- ExecutionManager 不能真实执行订单\n"
        "- InpEnableTrading 默认 false\n"
        "- 禁止 CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify\n"
        "- 禁止马丁、网格、补仓\n"
        + (role_boundary if include_role_boundary else "")
    )


def build_temp_project(
    temp_root,
    current_text=None,
    handoff_text=None,
    project_text=None,
    plan_text=DEFAULT_PLAN_TEXT,
    task238_boundary_text=DEFAULT_TASK238_BOUNDARY_TEXT,
    task239_boundary_text=DEFAULT_TASK239_BOUNDARY_TEXT,
    task260_observability_extension_plan_text=DEFAULT_TASK260_OBSERVABILITY_EXTENSION_PLAN_TEXT,
    task261_observability_extension_next_plan_text=DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT,
    task262_observability_extension_followup_plan_text=DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT,
    task263_observability_extension_future_plan_text=DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT,
    task294_mql5_compile_only_boundary_text=DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT,
    task295_mql5_compile_only_command_discovery_text=DEFAULT_TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_TEXT,
    task296_mql5_compile_only_artifact_quarantine_text=DEFAULT_TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_TEXT,
    task297_mql5_compile_only_execution_boundary_text=DEFAULT_TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_TEXT,
    task298_mql5_compile_only_dryrun_text=DEFAULT_TASK298_MQL5_COMPILE_ONLY_DRYRUN_TEXT,
    task300_mql5_compile_only_dryrun_execution_text=DEFAULT_TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_TEXT,
    task301_v060_compile_readiness_planning_text=DEFAULT_TASK301_V060_COMPILE_READINESS_PLANNING_TEXT,
    task302_mql5_compile_only_preflight_gate_text=DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT,
    task303_mql5_compile_only_execution_authorization_plan_text=DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT,
    task305_mql5_compile_only_failure_diagnostic_text=DEFAULT_TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_TEXT,
    task306_mql5_compile_diagnostic_result_classification_text=DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT,
    task307_mql5_compile_diagnostic_artifact_classification_text=DEFAULT_TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_TEXT,
    task308_mql5_compile_diagnostic_artifact_proof_boundary_text=DEFAULT_TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_TEXT,
    task309_mql5_compile_success_reclassification_boundary_text=DEFAULT_TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_TEXT,
    task310_mql5_compile_artifact_hash_capture_text=DEFAULT_TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_TEXT,
    task311_mql5_compile_success_reclassification_decision_boundary_text=DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT,
    task312_mql5_compile_success_reclassification_decision_text=DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT,
    task313_mt5_no_trade_startup_boundary_text=DEFAULT_TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_TEXT,
    task314_mt5_no_trade_startup_command_discovery_text=DEFAULT_TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_TEXT,
    task315_mt5_no_trade_startup_quarantine_preparation_text=DEFAULT_TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_TEXT,
    task316_mt5_no_trade_startup_dryrun_config_boundary_text=DEFAULT_TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_TEXT,
    task317_mt5_no_trade_startup_config_template_text=DEFAULT_TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_TEXT,
    task318_mt5_no_trade_startup_authorization_plan_text=DEFAULT_TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_TEXT,
    task319_mt5_no_trade_startup_preflight_gate_text=DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT,
    task321_parser_pipeline_integration_text=DEFAULT_TASK321_PARSER_PIPELINE_INTEGRATION_TEXT,
):
    write_text(
        temp_root / "tools" / "validate_project_state_docs.py",
        VALIDATOR_PATH.read_text(encoding="utf-8"),
    )
    write_text(
        temp_root / "docs" / "CURRENT_TASK.md",
        current_text if current_text is not None else doc_text(),
    )
    write_text(
        temp_root / "docs" / "HANDOFF_PROMPT.md",
        handoff_text if handoff_text is not None else doc_text(),
    )
    write_text(
        temp_root / "docs" / "PROJECT_STATE.md",
        project_text if project_text is not None else doc_text(),
    )
    if plan_text is not None:
        write_text(
            temp_root / "docs" / "V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md",
            plan_text,
        )
    if task238_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_238_NO_TRADE_SCAFFOLD_BOUNDARY.md",
            task238_boundary_text,
        )
    if task239_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_239_FIRST_IMPLEMENTATION_SLICE_BOUNDARY.md",
            task239_boundary_text,
        )
    if task260_observability_extension_plan_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md",
            task260_observability_extension_plan_text,
        )
    if task261_observability_extension_next_plan_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_261_OBSERVABILITY_EXTENSION_NEXT_PLAN.md",
            task261_observability_extension_next_plan_text,
        )
    if task262_observability_extension_followup_plan_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN.md",
            task262_observability_extension_followup_plan_text,
        )
    if task263_observability_extension_future_plan_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_263_OBSERVABILITY_EXTENSION_FUTURE_PLAN.md",
            task263_observability_extension_future_plan_text,
        )
    if task294_mql5_compile_only_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md",
            task294_mql5_compile_only_boundary_text,
        )
    if task295_mql5_compile_only_command_discovery_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
            task295_mql5_compile_only_command_discovery_text,
        )
    if task296_mql5_compile_only_artifact_quarantine_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
            task296_mql5_compile_only_artifact_quarantine_text,
        )
    if task297_mql5_compile_only_execution_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
            task297_mql5_compile_only_execution_boundary_text,
        )
    if task298_mql5_compile_only_dryrun_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md",
            task298_mql5_compile_only_dryrun_text,
        )
    if task300_mql5_compile_only_dryrun_execution_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md",
            task300_mql5_compile_only_dryrun_execution_text,
        )
    if task301_v060_compile_readiness_planning_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md",
            task301_v060_compile_readiness_planning_text,
        )
    if task302_mql5_compile_only_preflight_gate_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md",
            task302_mql5_compile_only_preflight_gate_text,
        )
    if task303_mql5_compile_only_execution_authorization_plan_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md",
            task303_mql5_compile_only_execution_authorization_plan_text,
        )
    if task305_mql5_compile_only_failure_diagnostic_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md",
            task305_mql5_compile_only_failure_diagnostic_text,
        )
    if task306_mql5_compile_diagnostic_result_classification_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION.md",
            task306_mql5_compile_diagnostic_result_classification_text,
        )
    if task307_mql5_compile_diagnostic_artifact_classification_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md",
            task307_mql5_compile_diagnostic_artifact_classification_text,
        )
    if task308_mql5_compile_diagnostic_artifact_proof_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md",
            task308_mql5_compile_diagnostic_artifact_proof_boundary_text,
        )
    if task309_mql5_compile_success_reclassification_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md",
            task309_mql5_compile_success_reclassification_boundary_text,
        )
    if task310_mql5_compile_artifact_hash_capture_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md",
            task310_mql5_compile_artifact_hash_capture_text,
        )
    if task311_mql5_compile_success_reclassification_decision_boundary_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md",
            task311_mql5_compile_success_reclassification_decision_boundary_text,
        )
    if task312_mql5_compile_success_reclassification_decision_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md",
            task312_mql5_compile_success_reclassification_decision_text,
        )
    if task313_mt5_no_trade_startup_boundary_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md",
            task313_mt5_no_trade_startup_boundary_text,
        )
    if task314_mt5_no_trade_startup_command_discovery_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md",
            task314_mt5_no_trade_startup_command_discovery_text,
        )
    if task315_mt5_no_trade_startup_quarantine_preparation_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md",
            task315_mt5_no_trade_startup_quarantine_preparation_text,
        )
    if task316_mt5_no_trade_startup_dryrun_config_boundary_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md",
            task316_mt5_no_trade_startup_dryrun_config_boundary_text,
        )
    if task317_mt5_no_trade_startup_config_template_text is not None:
        write_text(
            temp_root / "docs" / "V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md",
            task317_mt5_no_trade_startup_config_template_text,
        )
    if task318_mt5_no_trade_startup_authorization_plan_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN.md",
            task318_mt5_no_trade_startup_authorization_plan_text,
        )
    if task319_mt5_no_trade_startup_preflight_gate_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE.md",
            task319_mt5_no_trade_startup_preflight_gate_text,
        )
    if task321_parser_pipeline_integration_text is not None:
        write_text(
            temp_root
            / "docs"
            / "V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md",
            task321_parser_pipeline_integration_text,
        )


def expect_validation_failed(result, failure_name):
    output = combined_output(result)

    if result.returncode == 0:
        return f"{failure_name}\n{output}"

    if "Project state docs validation failed" not in output:
        return f"expected validation failed output not found\n{output}"

    return ""


def expect_static_interface_failed(result, failure_name):
    output = combined_output(result)

    if result.returncode == 0:
        return f"{failure_name}\n{output}"

    if "MQ5 static interface consistency validation failed" not in output:
        return f"expected static interface validation failed output not found\n{output}"

    return ""


def expect_validation_passed(result, failure_name):
    output = combined_output(result)

    if result.returncode != 0:
        return f"{failure_name}\n{output}"

    if "Project state docs validation passed" not in output:
        return f"expected validation passed output not found\n{output}"

    return ""


def positive_test_current_project():
    return expect_validation_passed(
        run_validator(ROOT_DIR),
        "positive validation did not pass",
    )


def positive_test_v050_current_phase_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        return expect_validation_passed(
            run_validator(temp_root),
            "v0.5.0 evidence archive policy boundary fixture did not pass",
        )


def positive_test_task_doc_077_update_state_commit_allowed():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            current_text=doc_text(
                current_commit="c22b31f TASK-DOC-077 update state after TASK-077"
            ),
            handoff_text=doc_text(
                current_commit="c22b31f TASK-DOC-077 update state after TASK-077"
            ),
            project_text=doc_text(
                current_commit="c22b31f TASK-DOC-077 update state after TASK-077"
            ),
        )
        result = run_validator(temp_root)
        error = expect_validation_passed(
            result,
            "TASK-DOC-077 update state commit fixture did not pass",
        )
        if error:
            return error

        output = combined_output(result)
        if "Current latest commit: c22b31f" not in output:
            return f"TASK-DOC-077 update state commit was not reported\n{output}"
        return ""


def positive_test_task_doc_role_boundary_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        return expect_validation_passed(
            run_validator(temp_root),
            "TASK-DOC role boundary fixture did not pass",
        )


def positive_test_dynamic_next_boundary_output():
    custom_boundary = [
        "当前下一步任务未定。",
        "不要直接进入 TASK-310。",
        "不要直接进入 v0.6.0。",
        "不要直接修改 MQ5。",
        "不要直接修改 backtest/sets。",
        "不要直接进入真实交易。",
        "必须先由 ChatGPT 制定下一任务边界。",
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            current_text=doc_text(boundary_lines=custom_boundary),
            handoff_text=doc_text(boundary_lines=custom_boundary),
            project_text=doc_text(boundary_lines=custom_boundary),
        )
        result = run_validator(temp_root)
        error = expect_validation_passed(
            result,
            "dynamic current next boundary fixture did not pass",
        )
        if error:
            return error

        output = combined_output(result)
        if "不要直接进入 TASK-310" not in output:
            return f"dynamic current next boundary was not printed\n{output}"
        if "不要直接进入 v0.6.0" not in output:
            return f"dynamic v0.6.0 boundary was not printed\n{output}"
        return ""


def expect_mojibake_failure(result, failure_name):
    error = expect_validation_failed(result, failure_name)
    if error:
        return error
    output = combined_output(result)
    required_words = ["mojibake", "garbled", "suspicious"]
    if not all(word in output for word in required_words):
        return f"mojibake failure reason not found\n{output}"
    return ""


def negative_test_current_task_mojibake_detected():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, current_text=doc_text() + suspicious_fragment())
        return expect_mojibake_failure(
            run_validator(temp_root),
            "CURRENT_TASK mojibake was not detected",
        )


def negative_test_handoff_mojibake_detected():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, handoff_text=doc_text() + suspicious_fragment())
        return expect_mojibake_failure(
            run_validator(temp_root),
            "HANDOFF mojibake was not detected",
        )


def negative_test_project_state_mojibake_detected():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, project_text=doc_text() + suspicious_fragment())
        return expect_mojibake_failure(
            run_validator(temp_root),
            "PROJECT_STATE mojibake was not detected",
        )


def negative_test_boundary_mismatch():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        project_boundary = [
            "当前下一步任务未定。",
            "不要直接进入 TASK-310。",
            "不要直接进入 v0.6.0。",
            "不要直接进入 TASK-998。",
            "不要直接修改 MQ5。",
            "不要直接修改 backtest/sets。",
            "不要直接进入真实交易。",
            "必须先由 ChatGPT 制定下一任务边界。",
        ]
        build_temp_project(
            temp_root,
            project_text=doc_text(boundary_lines=project_boundary),
        )
        result = run_validator(temp_root)
        error = expect_validation_failed(
            result,
            "current next boundary mismatch was not detected",
        )
        if error:
            return error
        if "current next boundary mismatch" not in combined_output(result):
            return "boundary mismatch failure reason not found"
        return ""


def negative_test_missing_real_trading_boundary():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        project_text = doc_text().replace(
            "不要直接进入真实交易。",
            "",
            1,
        )
        build_temp_project(temp_root, project_text=project_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing real trading next boundary was not detected",
        )


def negative_test_missing_handoff_role_boundary():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, handoff_text=doc_text(include_role_boundary=False))
        return expect_validation_failed(
            run_validator(temp_root),
            "missing HANDOFF TASK-DOC role boundary was not detected",
        )


def negative_test_missing_project_state_role_boundary():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, project_text=doc_text(include_role_boundary=False))
        return expect_validation_failed(
            run_validator(temp_root),
            "missing PROJECT_STATE TASK-DOC role boundary was not detected",
        )


def negative_test_missing_v060_first_low_risk_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, plan_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing V060 first low-risk implementation plan doc was not detected",
        )


def negative_test_v060_first_low_risk_plan_missing_safety_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_PLAN_TEXT.replace("no MQ5 modification", "", 1)
        build_temp_project(temp_root, plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing V060 first low-risk implementation plan safety phrase was not detected",
        )


def negative_test_missing_task238_no_trade_scaffold_boundary_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task238_boundary_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-238 no-trade scaffold boundary doc was not detected",
        )


def negative_test_task238_boundary_missing_safety_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        boundary_text = DEFAULT_TASK238_BOUNDARY_TEXT.replace(
            "Inventory only; no MT5 run; no trading authorization.",
            "",
            1,
        )
        build_temp_project(temp_root, task238_boundary_text=boundary_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-238 no-trade scaffold boundary safety phrase was not detected",
        )


def negative_test_missing_task239_first_implementation_slice_boundary_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task239_boundary_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-239 first implementation slice boundary doc was not detected",
        )


def negative_test_task239_boundary_missing_safety_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        boundary_text = DEFAULT_TASK239_BOUNDARY_TEXT.replace(
            "Inventory only; no MT5 run; no trading authorization.",
            "",
            1,
        )
        build_temp_project(temp_root, task239_boundary_text=boundary_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-239 first implementation slice boundary safety phrase was not detected",
        )


def negative_test_missing_task260_observability_extension_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task260_observability_extension_plan_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-260 observability extension plan doc was not detected",
        )


def negative_test_task260_plan_missing_planning_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK260_OBSERVABILITY_EXTENSION_PLAN_TEXT.replace(
            "planning-only",
            "",
            1,
        )
        build_temp_project(temp_root, task260_observability_extension_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-260 planning-only phrase was not detected",
        )


def negative_test_task260_plan_missing_future_no_trade_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK260_OBSERVABILITY_EXTENSION_PLAN_TEXT.replace(
            "future candidate",
            "",
            1,
        ).replace(
            "no-trade observability extension",
            "",
            1,
        )
        build_temp_project(temp_root, task260_observability_extension_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-260 future/no-trade phrase was not detected",
        )


def negative_test_task260_plan_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK260_OBSERVABILITY_EXTENSION_PLAN_TEXT.replace(
            "no MT5 run",
            "",
        ).replace(
            "no trading authorization",
            "",
        )
        build_temp_project(temp_root, task260_observability_extension_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-260 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task260_plan_missing_task261_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK260_OBSERVABILITY_EXTENSION_PLAN_TEXT.replace(
            "- TASK-261 must not be entered directly; GPT must define a separate future task boundary.\n",
            "",
            1,
        )
        build_temp_project(temp_root, task260_observability_extension_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-260 TASK-261 boundary phrase was not detected",
        )


def negative_test_missing_task261_observability_extension_next_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 observability extension next plan doc was not detected",
        )


def negative_test_task261_plan_missing_planning_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT.replace(
            "planning-only",
            "",
            1,
        )
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 planning-only phrase was not detected",
        )


def negative_test_task261_plan_missing_future_no_trade_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT.replace(
            "future candidate",
            "",
            1,
        ).replace(
            "no-trade observability extension",
            "",
            1,
        )
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 future/no-trade phrase was not detected",
        )


def negative_test_task261_plan_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT.replace(
            "no MT5 run",
            "",
        ).replace(
            "no trading authorization",
            "",
        )
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task261_plan_missing_task262_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT.replace(
            "- TASK-262 must not be entered directly.\n",
            "",
            1,
        ).replace(
            "- GPT must define a separate future boundary before TASK-262.\n",
            "",
            1,
        )
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 TASK-262 boundary phrase was not detected",
        )


def negative_test_task261_plan_missing_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT.replace(
            "- MQ5 inventory remains 7 files.\n",
            "",
            1,
        )
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 MQ5 inventory phrase was not detected",
        )


def negative_test_task261_plan_missing_trading_keyword_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_TEXT.replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.\n",
            "",
            1,
        )
        build_temp_project(temp_root, task261_observability_extension_next_plan_text=plan_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-261 trading keyword phrase was not detected",
        )


def negative_test_missing_task262_observability_extension_followup_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 observability extension follow-up plan doc was not detected",
        )


def negative_test_task262_plan_missing_planning_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT.replace(
            "- planning-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 planning-only phrase was not detected",
        )


def negative_test_task262_plan_missing_future_no_trade_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT.replace(
            "- future candidate\n",
            "",
            1,
        ).replace(
            "- no-trade observability extension\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 future no-trade phrase was not detected",
        )


def negative_test_task262_plan_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT.replace(
            "- no MT5 run\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        ).replace(
            "- Inventory only; no MT5 run; no trading authorization.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task262_plan_missing_task263_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT.replace(
            "- TASK-263 must not be entered directly.\n",
            "",
            1,
        ).replace(
            "- GPT must define a separate future boundary before TASK-263.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 TASK-263 boundary phrase was not detected",
        )


def negative_test_task262_plan_missing_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT.replace(
            "- MQ5 inventory remains 7 files.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 inventory phrase was not detected",
        )


def negative_test_task262_plan_missing_trading_keyword_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_TEXT.replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task262_observability_extension_followup_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-262 trading keyword phrase was not detected",
        )


def negative_test_missing_task263_observability_extension_future_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 observability extension future plan doc was not detected",
        )


def negative_test_task263_plan_missing_planning_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT.replace(
            "- planning-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 planning-only phrase was not detected",
        )


def negative_test_task263_plan_missing_future_no_trade_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT.replace(
            "- future candidate\n",
            "",
            1,
        ).replace(
            "- no-trade observability extension\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 future no-trade phrase was not detected",
        )


def negative_test_task263_plan_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT.replace(
            "- no MT5 run\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        ).replace(
            "- Inventory only; no MT5 run; no trading authorization.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task263_plan_missing_task264_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT.replace(
            "- TASK-264 must not be entered directly.\n",
            "",
            1,
        ).replace(
            "- GPT must define a separate future boundary before TASK-264.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 TASK-264 boundary phrase was not detected",
        )


def negative_test_task263_plan_missing_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT.replace(
            "- MQ5 inventory remains 7 files.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 inventory phrase was not detected",
        )


def negative_test_task263_plan_missing_trading_keyword_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        plan_text = DEFAULT_TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_TEXT.replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            task263_observability_extension_future_plan_text=plan_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-263 trading keyword phrase was not detected",
        )


def negative_test_task264_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-264 implement MQ5 read-only observability consolidation contract\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-264 current task phrase was not detected",
        )


def negative_test_task264_missing_latest_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current latest tag is v0.5.65-task-263-observability-extension-future-plan\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-264 latest tag phrase was not detected",
        )


def negative_test_task264_missing_no_planning_chain_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-264 must not continue planning packet chain\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-264 no planning chain phrase was not detected",
        )


def negative_test_task264_missing_inventory_trading_keyword_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-264 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-264 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-264 inventory/trading keyword phrase was not detected",
        )


def negative_test_task264_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-264 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-264 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-264 does not copy external evidence\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-264 no-MT5/no-output phrase was not detected",
        )


def negative_test_task265_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-265 implement MQ5 read-only observability contract registry snapshot\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-265 current task phrase was not detected",
        )


def negative_test_task265_missing_latest_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current latest tag is v0.5.66-task-264-read-only-observability-consolidation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-265 latest tag phrase was not detected",
        )


def negative_test_task265_missing_no_new_planning_packet_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-265 does not create a new planning packet\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-265 no-new-planning-packet phrase was not detected",
        )


def negative_test_task265_missing_inventory_trading_keyword_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-265 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-265 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-265 inventory/trading keyword phrase was not detected",
        )


def negative_test_task265_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-265 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-265 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-265 does not copy external evidence\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-265 no-MT5/no-output phrase was not detected",
        )


def negative_test_task266_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-266 implement fast no-trade development validation profile\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-266 current task phrase was not detected",
        )


def negative_test_task266_missing_fast_profile_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- python tools/run_release_validation_bundle.py --profile fast-no-trade-dev\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-266 fast profile phrase was not detected",
        )


def negative_test_task266_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-266 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-266 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task266_missing_no_mq5_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-266 does not modify MQ5 / MQH\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-266 no-MQ5 phrase was not detected",
        )


def negative_test_task266_missing_inventory_trading_keyword_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-266 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-266 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-266 inventory/trading keyword phrase was not detected",
        )


def negative_test_task267_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-267 implement one-command fast no-trade preflight runner\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-267 current task phrase was not detected",
        )


def negative_test_task267_missing_runner_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- new runner is tools/run_fast_no_trade_preflight.py\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-267 runner name phrase was not detected",
        )


def negative_test_task267_missing_doc_only_strict_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- runner supports --doc-only\n",
            "",
            1,
        ).replace(
            "- runner supports --strict-mq5\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-267 doc-only/strict-mq5 phrase was not detected",
        )


def negative_test_task267_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-267 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-267 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task268_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-268 implement allowed-change guard for fast no-trade preflight\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-268 current task phrase was not detected",
        )


def negative_test_task268_missing_allowed_change_guard_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "allowed-change guard",
            "allowed change guard",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-268 allowed-change guard phrase was not detected",
        )


def negative_test_task268_missing_allowed_change_parameters():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- --check-allowed-changes\n", "", 1)
            .replace("- --allow\n", "", 1)
            .replace("- --allow-prefix\n", "", 1)
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-268 allowed-change parameter phrase was not detected",
        )


def negative_test_task268_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-268 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-268 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_269_missing_error_snapshot_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_error_text = doc_text().replace(
            "- read-only observability error/exception logging contract records error_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_error_text,
            handoff_text=missing_error_text,
            project_text=missing_error_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-269 error snapshot phrase was not detected",
        )


def negative_test_task_269_missing_v070_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_tag_text = doc_text().replace(
            "- TASK-268 tag is v0.5.70-task-268-fast-no-trade-allowed-change-guard\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_tag_text,
            handoff_text=missing_tag_text,
            project_text=missing_tag_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-269 v0.5.70 tag phrase was not detected",
        )


def negative_test_task_269_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_state_text = doc_text().replace(
            "- TASK-269 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-269 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-269 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_state_text,
            handoff_text=missing_state_text,
            project_text=missing_state_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-269 no-MT5/no-output phrase was not detected",
        )


def negative_test_task_270_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-270 implement fast preflight allowed-change presets\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-270 current task phrase was not detected",
        )


def negative_test_task_270_missing_allow_preset_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_preset_text = doc_text().replace(
            "--allow-preset",
            "allow-preset",
        )
        build_temp_project(
            temp_root,
            current_text=missing_preset_text,
            handoff_text=missing_preset_text,
            project_text=missing_preset_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-270 --allow-preset phrase was not detected",
        )


def negative_test_task_270_missing_one_preset_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_preset_text = doc_text().replace(
            "mq5-observability",
            "mq5 observability",
        )
        build_temp_project(
            temp_root,
            current_text=missing_preset_text,
            handoff_text=missing_preset_text,
            project_text=missing_preset_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-270 preset phrase was not detected",
        )


def negative_test_task_270_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_state_text = doc_text().replace(
            "- TASK-270 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_state_text,
            handoff_text=missing_state_text,
            project_text=missing_state_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-270 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_271_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-271 implement read-only telemetry aggregation for error & metrics\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-271 current task phrase was not detected",
        )


def negative_test_task_271_missing_telemetry_field_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- read-only telemetry aggregation snapshot records telemetry_aggregation_snapshot=true\n",
            "",
            1,
        ).replace(
            "- read-only telemetry aggregation snapshot records aggregated_errors_linked=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-271 telemetry field phrase was not detected",
        )


def negative_test_task_271_missing_latest_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-270 tag is v0.5.72-task-270-fast-no-trade-preflight-presets\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-271 v0.5.72 tag phrase was not detected",
        )


def negative_test_task_271_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-271 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-271 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-271 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-271 no-MT5/no-output phrase was not detected",
        )


def negative_test_task_272_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-272 implement read-only controller summary snapshot\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-272 current task phrase was not detected",
        )


def negative_test_task_272_missing_controller_summary_field_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- read-only controller summary snapshot records controller_summary_snapshot=true\n",
            "",
            1,
        ).replace(
            "- read-only controller summary snapshot records init_path_linked=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-272 controller summary field phrase was not detected",
        )


def negative_test_task_272_missing_helper_gate_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- LogReadOnlyControllerSummarySnapshot\n",
            "",
            1,
        ).replace(
            "- OnTick controller summary remains gated by InpObservabilityLogOnTick\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-272 helper/gate phrase was not detected",
        )


def negative_test_task_272_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-272 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-272 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-272 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-272 no-MT5/no-output phrase was not detected",
        )


def negative_test_task_273_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-273 implement fast preflight review summary output\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-273 current task phrase was not detected",
        )


def negative_test_task_273_missing_review_summary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --review-summary\n",
            "",
            1,
        ).replace(
            "- --review-summary prints fast_no_trade_review_summary=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-273 review summary phrase was not detected",
        )


def negative_test_task_273_missing_suggested_git_add_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --review-summary prints suggested_git_add\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-273 suggested_git_add phrase was not detected",
        )


def negative_test_task_273_missing_latest_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-271/272 tag is v0.5.73-task-271-272-read-only-telemetry-controller-summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-273 latest tag phrase was not detected",
        )


def negative_test_task_273_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-273 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-273 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-273 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-273 no-MT5/no-output phrase was not detected",
        )


def negative_test_task_274_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-274 implement fast preflight Trae command preview output\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-274 current task phrase was not detected",
        )


def negative_test_task_274_missing_emit_trae_command_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --emit-trae-command\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-274 emit-trae-command phrase was not detected",
        )


def negative_test_task_274_missing_preview_parameter_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --emit-trae-command requires --task-id\n",
            "",
            1,
        ).replace(
            "- --emit-trae-command requires --commit-message\n",
            "",
            1,
        ).replace(
            "- --emit-trae-command requires --tag-name\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-274 preview parameter phrases were not detected",
        )


def negative_test_task_274_missing_latest_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-273 tag is v0.5.74-task-273-fast-preflight-review-summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-274 latest tag phrase was not detected",
        )


def negative_test_task_274_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-274 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        ).replace(
            "- TASK-274 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-274 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_275_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-275 implement fast preflight workflow presets\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-275 current task phrase was not detected",
        )


def negative_test_task_275_missing_workflow_preset_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --workflow-preset\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-275 workflow preset phrase was not detected",
        )


def negative_test_task_275_missing_one_preset_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --workflow-preset supports mq5-observability\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-275 workflow preset option was not detected",
        )


def negative_test_task_275_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-275 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        ).replace(
            "- TASK-275 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-275 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_276_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-276 implement fast preflight state report stdout\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-276 current task phrase was not detected",
        )


def negative_test_task_276_missing_state_report_support_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --state-report\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-276 --state-report support phrase was not detected",
        )


def negative_test_task_276_missing_state_report_field_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --state-report prints fast_no_trade_state_report=true\n",
            "",
            1,
        ).replace(
            "- --state-report prints current_head\n",
            "",
            1,
        ).replace(
            "- --state-report prints current_tags_at_head\n",
            "",
            1,
        ).replace(
            "- --state-report prints modified_files\n",
            "",
            1,
        ).replace(
            "- --state-report prints untracked_files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-276 state report fields were not detected",
        )


def negative_test_task_276_missing_state_report_safety_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- state report is stdout-only and does not create files\n",
            "",
            1,
        ).replace(
            "- state report does not execute git add / commit / tag\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-276 state report safety phrases were not detected",
        )


def negative_test_task_276_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-276 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-276 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-276 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-276 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_277_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-277 implement compact Trae handoff instruction output\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-277 current task phrase was not detected",
        )


def negative_test_task_277_missing_emit_trae_handoff_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --emit-trae-handoff\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-277 --emit-trae-handoff phrase was not detected",
        )


def negative_test_task_277_missing_handoff_marker_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --emit-trae-handoff prints trae_handoff_instruction=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-277 handoff marker phrase was not detected",
        )


def negative_test_task_277_missing_handoff_block_start_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --emit-trae-handoff prints handoff_block_start\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-277 handoff block start phrase was not detected",
        )


def negative_test_task_277_missing_send_to_trae_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --emit-trae-handoff prints 发给：Trae\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-277 send-to-Trae phrase was not detected",
        )


def negative_test_task_277_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-277 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        ).replace(
            "- TASK-277 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-277 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_278_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-278 implement compact preflight combined report output\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-278 current task phrase was not detected",
        )


def negative_test_task_278_missing_compact_report_parameter_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --compact-report\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-278 --compact-report phrase was not detected",
        )


def negative_test_task_278_missing_compact_report_field_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --compact-report prints current_head / current_tags_at_head\n",
            "",
            1,
        ).replace(
            "- --compact-report prints workflow_preset / profile\n",
            "",
            1,
        ).replace(
            "- --compact-report prints allowed_change_guard / allowed_change_check / unexpected_changes_count\n",
            "",
            1,
        ).replace(
            "- --compact-report prints modified_files / untracked_files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-278 compact report field phrases were not detected",
        )


def negative_test_task_278_missing_trae_review_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --compact-report includes Trae command preview\n",
            "",
            1,
        ).replace(
            "- --compact-report includes review-summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-278 Trae/review compact report phrases were not detected",
        )


def negative_test_task_278_missing_no_mt5_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-278 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-278 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- --compact-report prints trading_keywords=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-278 no-MT5/inventory phrase was not detected",
        )


def negative_test_task_279_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-279 implement release bundle summary compression\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-279 current task phrase was not detected",
        )


def negative_test_task_279_missing_compressed_summary_parameter_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_release_validation_bundle.py supports --compressed-summary\n",
            "",
            1,
        ).replace(
            "- new parameter is --compressed-summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-279 --compressed-summary phrase was not detected",
        )


def negative_test_task_279_missing_compressed_summary_field_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --compressed-summary prints release_validation_compressed_summary=true\n",
            "",
            1,
        ).replace(
            "- --compressed-summary includes fast_no_trade_state_report\n",
            "",
            1,
        ).replace(
            "- --compressed-summary prints workflow_preset\n",
            "",
            1,
        ).replace(
            "- --compressed-summary prints allowed_change_check\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-279 compressed summary field phrases were not detected",
        )


def negative_test_task_279_missing_trae_review_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --compressed-summary includes Trae command preview\n",
            "",
            1,
        ).replace(
            "- --compressed-summary includes review summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-279 Trae/review compressed summary phrases were not detected",
        )


def negative_test_task_279_missing_no_mt5_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-279 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-279 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- --compressed-summary prints trading_keywords=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-279 no-MT5/inventory phrase was not detected",
        )


def negative_test_task_280_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-280 implement no-trade development workflow closure audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-280 current task phrase was not detected",
        )


def negative_test_task_280_missing_workflow_closure_parameter_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- tools/run_fast_no_trade_preflight.py supports --workflow-closure-audit\n",
            "",
            1,
        ).replace(
            "- tools/run_release_validation_bundle.py supports --workflow-closure-audit\n",
            "",
            1,
        ).replace(
            "- new parameter is --workflow-closure-audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-280 --workflow-closure-audit phrase was not detected",
        )


def negative_test_task_280_missing_closure_audit_field_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --workflow-closure-audit prints workflow_closure_audit=true\n",
            "",
            1,
        ).replace(
            "- --workflow-closure-audit prints release_ready_closure_audit=true\n",
            "",
            1,
        ).replace(
            "- --workflow-closure-audit includes fast_no_trade_state_report\n",
            "",
            1,
        ).replace(
            "- --workflow-closure-audit prints allowed_change_check\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-280 closure audit field phrases were not detected",
        )


def negative_test_task_280_missing_trae_validator_summary_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- --workflow-closure-audit includes Trae handoff block status\n",
            "",
            1,
        ).replace(
            "- --workflow-closure-audit includes validator/self-test summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-280 Trae/validator summary phrases were not detected",
        )


def negative_test_task_280_missing_no_mt5_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-280 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-280 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- --workflow-closure-audit prints trading_keywords=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-280 no-MT5/inventory phrase was not detected",
        )


def negative_test_task_doc_281_missing_task280_completion_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-280 completed no-trade development workflow closure audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-281 TASK-280 completion phrase was not detected",
        )


def negative_test_task_doc_281_missing_v080_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-280 tag is v0.5.80-task-280-no-trade-workflow-closure-audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-281 v0.5.80 tag phrase was not detected",
        )


def negative_test_task_doc_281_missing_workflow_closure_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- run_fast_no_trade_preflight.py supports --workflow-closure-audit\n",
            "",
        ).replace(
            "- run_release_validation_bundle.py supports --workflow-closure-audit\n",
            "",
        ).replace(
            "- tools/run_fast_no_trade_preflight.py supports --workflow-closure-audit\n",
            "",
        ).replace(
            "- tools/run_release_validation_bundle.py supports --workflow-closure-audit\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-281 workflow closure audit phrase was not detected",
        )


def negative_test_task_doc_281_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-DOC-281 does not run MT5\n",
            "",
            1,
        ).replace(
            "- Inventory only; no MT5 run; no trading authorization.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-281 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_doc_281_missing_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-DOC-281 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-281 MQ5 inventory phrase was not detected",
        )


def negative_test_task_282_missing_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-282 implement read-only compile-readiness boundary\n",
            "",
            1,
        ).replace(
            "- TASK-282 implement read-only compile-readiness boundary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-282 boundary phrase was not detected",
        )


def negative_test_task_282_missing_compile_readiness_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- compile-readiness boundary verifies no-trade / read-only observability scaffold safety\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-282 compile-readiness phrase was not detected",
        )


def negative_test_task_282_missing_bundle_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- run_release_validation_bundle.py includes read-only compile-readiness boundary check\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-282 bundle compile-readiness phrase was not detected",
        )


def negative_test_task_282_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-282 does not run MT5\n",
            "",
            1,
        ).replace(
            "- Inventory only; no MT5 run; no trading authorization.\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-282 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_282_missing_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- compile-readiness check confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-282 MQ5 inventory phrase was not detected",
        )


def negative_test_task_283_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-283 implement MQ5 static interface consistency audit\n",
            "",
            1,
        ).replace(
            "- TASK-283 implement MQ5 static interface consistency audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-283 current task phrase was not detected",
        )


def negative_test_task_283_missing_static_interface_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- MQ5 static interface consistency audit verifies TradingSystem.mq5 routes OnInit / OnTick / OnDeinit through EaController\n",
            "",
            1,
        ).replace(
            "- MQ5 static interface consistency audit verifies Logger helper availability for no-trade observability scaffold\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-283 static interface phrase was not detected",
        )


def negative_test_task_283_missing_bundle_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- run_release_validation_bundle.py includes mq5-static-interface-consistency check\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-283 bundle check phrase was not detected",
        )


def negative_test_task_283_missing_no_mt5_inventory_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-283 does not run MT5\n",
            "",
            1,
        ).replace(
            "- mq5-static-interface-consistency check confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-283 no-MT5/inventory phrase was not detected",
        )


def negative_test_task_284_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-284 implement MQ5 static include dependency consistency audit\n",
            "",
            1,
        ).replace(
            "- TASK-284 implement MQ5 static include dependency consistency audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-284 current task phrase was not detected",
        )


def negative_test_task_284_missing_include_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- run_release_validation_bundle.py includes mq5-static-include-consistency check\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-284 include check phrase was not detected",
        )


def negative_test_task_284_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mq5-static-include-consistency check does not run MT5\n",
            "",
            1,
        ).replace(
            "- mq5-static-include-consistency check does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-284 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_284_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- MQ5 static include dependency consistency audit confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- mq5-static-include-consistency check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-284 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_285_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-285 implement read-only controller/logger duplicate output reduction contract\n",
            "",
            1,
        ).replace(
            "- TASK-285 implement read-only controller/logger duplicate output reduction contract\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-285 current task phrase was not detected",
        )


def negative_test_task_285_missing_duplicate_output_reduction_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- read-only controller/logger duplicate output reduction contract\n",
            "",
            1,
        ).replace(
            "- duplicate_output_guard=active\n",
            "",
            1,
        ).replace(
            "- controller_logger_deduplication=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-285 duplicate output reduction phrase was not detected",
        )


def negative_test_task_285_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-285 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-285 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-285 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_285_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "MQ5 inventory remains 7 files",
            "",
        ).replace(
            "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-285 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_286_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-286 implement MQ5 lifecycle route consistency audit\n",
            "",
            1,
        ).replace(
            "- TASK-286 implement MQ5 lifecycle route consistency audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-286 current task phrase was not detected",
        )


def negative_test_task_286_missing_lifecycle_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-286 adds mq5-lifecycle-route-consistency check\n",
            "",
            1,
        ).replace(
            "- mq5-lifecycle-route-consistency check is read-only and stdout-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-286 lifecycle check phrase was not detected",
        )


def negative_test_task_286_missing_lifecycle_route_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("OnInit", "").replace("OnTick", "").replace("OnDeinit", "")
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-286 lifecycle route phrase was not detected",
        )


def negative_test_task_286_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mq5-lifecycle-route-consistency check does not run MT5\n",
            "",
            1,
        ).replace(
            "- mq5-lifecycle-route-consistency check does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-286 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_286_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "MQ5 inventory remains 7 files",
            "",
        ).replace(
            "Buy / Sell / OrderSend / PositionOpen / CTrade",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-286 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_287_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-287 implement MQ5 observability helper call consistency audit\n",
            "",
            1,
        ).replace(
            "- TASK-287 implement MQ5 observability helper call consistency audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-287 current task phrase was not detected",
        )


def negative_test_task_287_missing_helper_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-287 adds mq5-observability-helper-consistency check\n",
            "",
            1,
        ).replace(
            "- mq5-observability-helper-consistency check is read-only and stdout-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-287 helper check phrase was not detected",
        )


def negative_test_task_287_missing_logger_helper_consistency_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- logger_helper_consistency=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-287 logger helper consistency phrase was not detected",
        )


def negative_test_task_287_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mq5-observability-helper-consistency check does not run MT5\n",
            "",
            1,
        ).replace(
            "- mq5-observability-helper-consistency check does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-287 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_287_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "MQ5 inventory remains 7 files",
            "",
        ).replace(
            "Buy / Sell / OrderSend / PositionOpen / CTrade",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-287 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_288_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-288 implement MQ5 read-only observability telemetry final aggregation\n",
            "",
            1,
        ).replace(
            "- TASK-288 implement MQ5 read-only observability telemetry final aggregation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-288 current task phrase was not detected",
        )


def negative_test_task_288_missing_telemetry_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-288 adds mq5-telemetry-aggregation check\n",
            "",
            1,
        ).replace(
            "- mq5-telemetry-aggregation check is read-only and stdout-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-288 telemetry check phrase was not detected",
        )


def negative_test_task_288_missing_telemetry_summary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- fast_no_trade_telemetry_aggregation=true\n",
            "",
            1,
        ).replace(
            "- all_observability_outputs_read_only=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-288 telemetry summary phrase was not detected",
        )


def negative_test_task_288_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-288 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-288 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-288 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_288_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "MQ5 inventory remains 7 files",
            "",
        ).replace(
            "Buy / Sell / OrderSend / PositionOpen / CTrade",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-288 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_289_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-289 reconcile TASK-287 observability helper validator tracking gap\n",
            "",
            1,
        ).replace(
            "- TASK-289 reconcile TASK-287 observability helper validator tracking gap\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-289 current task phrase was not detected",
        )


def negative_test_task_289_missing_helper_file_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-289 brings tools/validate_mq5_observability_helper_consistency.py into tracking scope\n",
            "",
            1,
        ).replace(
            "- TASK-289 brings tools/test_validate_mq5_observability_helper_consistency.py into tracking scope\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-289 helper consistency file phrase was not detected",
        )


def negative_test_task_289_missing_v087_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-288 completion tag is v0.5.87-task-288-mq5-telemetry-final-aggregation\n",
            "",
            1,
        ).replace(
            "- current tag is v0.5.87-task-288-mq5-telemetry-final-aggregation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-289 v0.5.87 tag phrase was not detected",
        )


def negative_test_task_289_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-289 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-289 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-289 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_289_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "MQ5 inventory remains 7 files",
            "",
        ).replace(
            "Buy / Sell / OrderSend / PositionOpen / CTrade",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-289 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_289_missing_tag_reconciliation_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-289 does not recreate old v0.5.86 tag\n",
            "",
            1,
        ).replace(
            "- TASK-289 does not move historical tags\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-289 tag reconciliation phrase was not detected",
        )


def negative_test_task_290_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-290 implement final milestone closure / release-ready state report\n",
            "",
            1,
        ).replace(
            "- TASK-290 implement final milestone closure / release-ready state report\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-290 current task phrase was not detected",
        )


def negative_test_task_290_missing_final_milestone_parameter_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-290 adds --final-milestone-report\n",
            "",
            1,
        ).replace(
            "- final_milestone_report=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-290 --final-milestone-report phrase was not detected",
        )


def negative_test_task_290_missing_closure_summary_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- release_ready_milestone_closure=true\n",
            "",
            1,
        ).replace(
            "- TASK-266 through TASK-289 closure summary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-290 closure summary phrase was not detected",
        )


def negative_test_task_290_missing_trae_validator_summary_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- Trae handoff blocks\n",
            "",
            1,
        ).replace(
            "- validator/self-test results\n",
            "",
            1,
        ).replace(
            "- project-state-docs-self-test PASS\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-290 Trae/validator summary phrase was not detected",
        )


def negative_test_task_290_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-290 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-290 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-290 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_290_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-290 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-290 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-290 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_291_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-291 implement MQ5 static symbol reference consistency audit\n",
            "",
            1,
        ).replace(
            "- TASK-291 implement MQ5 static symbol reference consistency audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-291 current task phrase was not detected",
        )


def negative_test_task_291_missing_check_id_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-291 adds mq5-static-symbol-consistency check\n",
            "",
            1,
        ).replace(
            "- mq5-static-symbol-consistency check is read-only and stdout-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-291 check id phrase was not detected",
        )


def negative_test_task_291_missing_symbol_and_compile_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- symbol_reference_consistency=true\n",
            "",
            1,
        ).replace(
            "- compile_readiness_static_only=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-291 symbol/compile flags were not detected",
        )


def negative_test_task_291_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-291 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-291 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-291 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_291_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-291 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-291 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-291 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_292_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-292 implement MQ5 static compile-readiness aggregate audit\n",
            "",
            1,
        ).replace(
            "- TASK-292 implement MQ5 static compile-readiness aggregate audit\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-292 current task phrase was not detected",
        )


def negative_test_task_292_missing_check_id_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-292 adds mq5-static-compile-readiness check\n",
            "",
            1,
        ).replace(
            "- mq5-static-compile-readiness check is read-only and stdout-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-292 check id phrase was not detected",
        )


def negative_test_task_292_missing_compile_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- compile_readiness_static_only=true\n",
            "",
        ).replace(
            "- mql5_compile_executed=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-292 compile flags were not detected",
        )


def negative_test_task_292_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-292 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-292 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-292 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_292_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-292 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-292 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-292 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_293_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-293 implement MQ5 compile-readiness final milestone summary report\n",
            "",
            1,
        ).replace(
            "- TASK-293 implement MQ5 compile-readiness final milestone summary report\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-293 current task phrase was not detected",
        )


def negative_test_task_293_missing_summary_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-293 adds mq5-static-compile-readiness-summary check\n",
            "",
            1,
        ).replace(
            "- mq5-static-compile-readiness-summary PASS\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-293 summary check phrase was not detected",
        )


def negative_test_task_293_missing_final_summary_fields():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- final_milestone_summary=true\n",
            "",
            1,
        ).replace(
            "- tasks_covered=TASK-266..TASK-292\n",
            "",
            1,
        ).replace(
            "- milestone_closure_ready=PASS\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-293 final summary fields were not detected",
        )


def negative_test_task_293_missing_no_mt5_compile_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-293 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-293 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-293 no-MT5/no-compile/no-trading phrase was not detected",
        )


def negative_test_task_293_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-293 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-293 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-293 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_doc_294_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task294_mql5_compile_only_boundary_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 MQL5 compile-only boundary doc was not detected",
        )


def negative_test_task_doc_294_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-DOC-294 create future MQL5 compile-only boundary packet\n",
            "",
            1,
        ).replace(
            "- TASK-DOC-294 create future MQL5 compile-only boundary packet\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 current task phrase was not detected",
        )


def negative_test_task_doc_294_missing_planning_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-DOC-294 is planning-only / boundary-only\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT.replace(
            "- planning-only / boundary-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task294_mql5_compile_only_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 planning-only boundary phrase was not detected",
        )


def negative_test_task_doc_294_missing_no_compile_no_metaeditor_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- no compile executed in TASK-DOC-294\n",
            "",
            1,
        ).replace(
            "- no MetaEditor executed in TASK-DOC-294\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated\n",
            "",
            1,
        ).replace(
            "- no MQL5 compile\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT.replace(
            "- no compile executed in TASK-DOC-294\n",
            "",
            1,
        ).replace(
            "- no MetaEditor executed in TASK-DOC-294\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task294_mql5_compile_only_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 no-compile/no-MetaEditor/no-ex5 phrase was not detected",
        )


def negative_test_task_doc_294_missing_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-DOC-294 is not MT5 run authorization\n",
            "",
            1,
        ).replace(
            "- TASK-DOC-294 does not run MT5\n",
            "",
            1,
        ).replace(
            "- no trading authorization\n",
            "",
        )
        boundary_text = DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT.replace(
            "- not MT5 run authorization\n",
            "",
            1,
        ).replace(
            "- not real trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task294_mql5_compile_only_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_doc_294_missing_task295_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-295 must not be entered directly without a new GPT boundary\n",
            "",
            1,
        ).replace(
            "- GPT must define a separate future boundary before TASK-295\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT.replace(
            "- TASK-295 must not be entered directly without a new GPT boundary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task294_mql5_compile_only_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 TASK-295 boundary phrase was not detected",
        )


def negative_test_task_doc_294_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- MQ5 inventory remains 7 files\n",
            "",
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
        )
        boundary_text = DEFAULT_TASK294_MQL5_COMPILE_ONLY_BOUNDARY_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task294_mql5_compile_only_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-294 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_295_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-295 implement MQL5 compile-only command discovery boundary\n",
            "",
            1,
        ).replace(
            "- TASK-295 implement MQL5 compile-only command discovery boundary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 current task phrase was not detected",
        )


def negative_test_task_295_missing_command_discovery_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-295 is command-discovery-only\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-command-discovery check is added to release validation bundle\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 command discovery phrase was not detected",
        )


def negative_test_task_295_missing_execution_false_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- metaeditor_executed=false\n",
            "",
        ).replace(
            "- mql5_compile_executed=false\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 execution false phrases were not detected",
        )


def negative_test_task_295_missing_no_compile_boundary_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- no MQL5 compile\n",
            "",
        ).replace(
            "- no MetaEditor execution\n",
            "",
        ).replace(
            "- no .ex5 artifact\n",
            "",
        ).replace(
            "- no compile log\n",
            "",
        ).replace(
            "- no MQL5 compile in TASK-311\n",
            "",
        ).replace(
            "- no MetaEditor execution in TASK-311\n",
            "",
        ).replace(
            "- no .ex5 artifact generated in repository\n",
            "",
        )
        task311_boundary_text = (
            DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT.replace(
                "- not compile execution\n",
                "",
                1,
            )
            .replace(
                "- not MetaEditor execution in TASK-311\n",
                "",
                1,
            )
            .replace(
                "- no .ex5 artifact generated in repository\n",
                "",
                1,
            )
            .replace(
                "- no compile log generated in repository\n",
                "",
                1,
            )
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task311_mql5_compile_success_reclassification_decision_boundary_text=task311_boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 no-compile boundary phrases were not detected",
        )


def negative_test_task_295_missing_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-295 no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 no trading authorization phrase was not detected",
        )


def negative_test_task_295_missing_task296_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-296 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_TEXT.replace(
            "- TASK-296 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task295_mql5_compile_only_command_discovery_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 TASK-296 boundary phrase was not detected",
        )


def negative_test_task_295_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-295 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-295 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task295_mql5_compile_only_command_discovery_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-295 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_296_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task296_mql5_compile_only_artifact_quarantine_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-296 artifact quarantine plan doc was not detected",
        )


def negative_test_task_296_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-296 implement MQL5 compile-only artifact quarantine boundary\n",
            "",
            1,
        ).replace(
            "- TASK-296 implement MQL5 compile-only artifact quarantine boundary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-296 current task phrase was not detected",
        )


def negative_test_task_296_missing_artifact_quarantine_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-296 is artifact-quarantine-only\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-artifact-quarantine check is added to release validation bundle\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_TEXT.replace(
            "- artifact-quarantine-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task296_mql5_compile_only_artifact_quarantine_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-296 artifact quarantine phrase was not detected",
        )


def negative_test_task_296_missing_repo_artifact_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-302 preflight gate confirms repository has no ex5 artifacts\n",
            "",
            1,
        ).replace(
            "- TASK-302 preflight gate confirms repository has no compile logs\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-296 repo artifact flags were not detected",
        )


def negative_test_task_296_missing_task297_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-297 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_TEXT.replace(
            "- TASK-297 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task296_mql5_compile_only_artifact_quarantine_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-296 TASK-297 boundary phrase was not detected",
        )


def negative_test_task_296_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-296 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-296 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task296_mql5_compile_only_artifact_quarantine_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-296 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_297_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task297_mql5_compile_only_execution_boundary_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-297 compile-only execution boundary doc was not detected",
        )


def negative_test_task_297_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-297 implement future MQL5 compile-only execution boundary\n",
            "",
            1,
        ).replace(
            "- TASK-297 implement future MQL5 compile-only execution boundary\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-297 current task phrase was not detected",
        )


def negative_test_task_297_missing_execution_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-297 is compile-only-task\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-execution-boundary check is added to release validation bundle\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_TEXT.replace(
            "- compile-only-task\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task297_mql5_compile_only_execution_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-297 compile-only execution phrase was not detected",
        )


def negative_test_task_297_missing_no_compile_no_artifact_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-297 does not execute MetaEditor\n",
            "",
            1,
        ).replace(
            "- TASK-297 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-297 does not create .ex5 artifact\n",
            "",
            1,
        ).replace(
            "- TASK-297 does not create compile log\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_TEXT.replace(
            "- no MQL5 compile executed\n",
            "",
            1,
        ).replace(
            "- no MetaEditor executed\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated\n",
            "",
            1,
        ).replace(
            "- no compile log\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task297_mql5_compile_only_execution_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-297 no-compile/no-artifact phrases were not detected",
        )


def negative_test_task_297_missing_task298_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- future TASK-298 must be separately authorized by GPT\n",
            "",
            1,
        ).replace(
            "- future TASK-298 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_TEXT.replace(
            "- future TASK-298 must be separately authorized by GPT\n",
            "",
            1,
        ).replace(
            "- future TASK-298 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task297_mql5_compile_only_execution_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-297 TASK-298 boundary phrase was not detected",
        )


def negative_test_task_297_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-297 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-297 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task297_mql5_compile_only_execution_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-297 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_298_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task298_mql5_compile_only_dryrun_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-298 compile-only dry-run doc was not detected",
        )


def negative_test_task_298_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-298 implement MQL5 compile-only dry-run simulation\n",
            "",
            1,
        ).replace(
            "- TASK-298 implement MQL5 compile-only dry-run simulation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-298 current task phrase was not detected",
        )


def negative_test_task_298_missing_dryrun_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-298 is dry-run-only\n",
            "",
            1,
        ).replace(
            "- TASK-298 uses stdout-only simulation\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-dryrun check is added to release validation bundle\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK298_MQL5_COMPILE_ONLY_DRYRUN_TEXT.replace(
            "- dry-run-only\n",
            "",
            1,
        ).replace(
            "- stdout-only simulation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task298_mql5_compile_only_dryrun_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-298 dry-run phrase was not detected",
        )


def negative_test_task_298_missing_no_compile_no_output_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-298 does not execute MetaEditor\n",
            "",
            1,
        ).replace(
            "- TASK-298 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-298 does not create .ex5 artifact\n",
            "",
            1,
        ).replace(
            "- TASK-298 does not create compile log\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-298 no-compile/no-output phrases were not detected",
        )


def negative_test_task_298_missing_task299_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-299 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK298_MQL5_COMPILE_ONLY_DRYRUN_TEXT.replace(
            "- TASK-299 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task298_mql5_compile_only_dryrun_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-298 TASK-299 boundary phrase was not detected",
        )


def negative_test_task_298_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-298 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-298 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK298_MQL5_COMPILE_ONLY_DRYRUN_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task298_mql5_compile_only_dryrun_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-298 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_299_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-299 reconcile TASK-297 MQL5 compile-only execution boundary tracking gap\n",
            "",
            1,
        ).replace(
            "- TASK-299 reconcile TASK-297 MQL5 compile-only execution boundary tracking gap\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-299 current task phrase was not detected",
        )


def negative_test_task_299_missing_task297_file_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-299 reconciles docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md\n",
            "",
            1,
        ).replace(
            "- TASK-299 reconciles tools/validate_mql5_compile_only_execution_boundary.py\n",
            "",
            1,
        ).replace(
            "- TASK-299 reconciles tools/test_validate_mql5_compile_only_execution_boundary.py\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-299 TASK-297 file reconciliation phrase was not detected",
        )


def negative_test_task_299_missing_v096_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-298 completion tag is v0.5.96-task-298-mql5-compile-only-dryrun\n",
            "",
            1,
        ).replace(
            "- current tag is v0.5.96-task-298-mql5-compile-only-dryrun\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-299 v0.5.96 tag phrase was not detected",
        )


def negative_test_task_299_missing_no_mt5_no_compile_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-299 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-299 does not execute MetaEditor\n",
            "",
            1,
        ).replace(
            "- TASK-299 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-299 does not create .ex5 artifact\n",
            "",
            1,
        ).replace(
            "- TASK-299 does not create compile log\n",
            "",
            1,
        ).replace(
            "- TASK-299 does not create manifest / fixture / report / directory\n",
            "",
            1,
        ).replace(
            "- TASK-299 does not copy external evidence\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-299 no-MT5/no-compile/no-output phrase was not detected",
        )


def negative_test_task_299_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-299 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-299 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-299 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_300_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task300_mql5_compile_only_dryrun_execution_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-300 compile-only dry-run execution doc was not detected",
        )


def negative_test_task_300_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-300 implement MQL5 compile-only dry-run execution simulation\n",
            "",
            1,
        ).replace(
            "- TASK-300 implement MQL5 compile-only dry-run execution simulation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-300 current task phrase was not detected",
        )


def negative_test_task_300_missing_dryrun_execution_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-300 is dry-run-execution-only\n",
            "",
            1,
        ).replace(
            "- TASK-300 uses stdout-only simulation\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-dryrun-execution check is added to release validation bundle\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_TEXT.replace(
            "- dry-run-execution-only\n",
            "",
            1,
        ).replace(
            "- stdout-only simulation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task300_mql5_compile_only_dryrun_execution_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-300 dry-run execution phrase was not detected",
        )


def negative_test_task_300_missing_no_compile_no_output_phrases():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-300 does not execute MetaEditor\n",
            "",
            1,
        ).replace(
            "- TASK-300 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-300 does not create .ex5 artifact\n",
            "",
            1,
        ).replace(
            "- TASK-300 does not create compile log\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-300 no-compile/no-output phrases were not detected",
        )


def negative_test_task_300_missing_task301_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-301 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_TEXT.replace(
            "- TASK-301 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task300_mql5_compile_only_dryrun_execution_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-300 TASK-301 boundary phrase was not detected",
        )


def negative_test_task_300_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-300 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-300 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task300_mql5_compile_only_dryrun_execution_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-300 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_301_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task301_v060_compile_readiness_planning_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-301 compile-readiness planning doc was not detected",
        )


def negative_test_task_301_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-301 create v0.6.0 compile-readiness planning packet\n",
            "",
            1,
        ).replace(
            "- TASK-301 create v0.6.0 compile-readiness planning packet\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-301 current task phrase was not detected",
        )


def negative_test_task_301_missing_planning_future_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-301 is planning-only\n",
            "",
            1,
        ).replace(
            "- TASK-301 is future compile-readiness candidate\n",
            "",
            1,
        ).replace(
            "- TASK-301 is not implementation authorization\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK301_V060_COMPILE_READINESS_PLANNING_TEXT.replace(
            "- planning-only\n",
            "",
            1,
        ).replace(
            "- future compile-readiness candidate\n",
            "",
            1,
        ).replace(
            "- not implementation authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task301_v060_compile_readiness_planning_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-301 planning/future phrase was not detected",
        )


def negative_test_task_301_missing_no_mt5_no_compile_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-301 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-301 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-301 does not create evidence / manifest / report\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK301_V060_COMPILE_READINESS_PLANNING_TEXT.replace(
            "- not MT5 run\n",
            "",
            1,
        ).replace(
            "- not evidence / manifest / report creation\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task301_v060_compile_readiness_planning_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-301 no-MT5/no-compile/no-output phrases were not detected",
        )


def negative_test_task_301_missing_task302_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-302 must not be entered directly without GPT authorization\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK301_V060_COMPILE_READINESS_PLANNING_TEXT.replace(
            "- TASK-302 must not be entered directly without GPT authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task301_v060_compile_readiness_planning_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-301 TASK-302 boundary phrase was not detected",
        )


def negative_test_task_301_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-301 confirms MQ5 inventory 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-301 confirms Buy / Sell / OrderSend / PositionOpen / CTrade false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK301_V060_COMPILE_READINESS_PLANNING_TEXT.replace(
            "- MQ5 inventory 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task301_v060_compile_readiness_planning_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-301 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_302_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task302_mql5_compile_only_preflight_gate_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 preflight gate doc was not detected",
        )


def negative_test_task_302_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-302 implement MQL5 compile-only execution preflight gate\n",
            "",
            1,
        ).replace(
            "- TASK-302 implement MQL5 compile-only execution preflight gate\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 current task phrase was not detected",
        )


def negative_test_task_302_missing_preflight_gate_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-302 is preflight-gate-only\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-preflight-gate check is added to release validation bundle\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT.replace(
            "- preflight-gate-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task302_mql5_compile_only_preflight_gate_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 preflight gate phrase was not detected",
        )


def negative_test_task_302_missing_repo_artifact_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- repo_ex5_artifacts=false\n",
            "",
            1,
        ).replace(
            "- repo_compile_logs=false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT.replace(
            "- preflight check: repo_ex5_artifacts=false\n",
            "",
            1,
        ).replace(
            "- preflight check: repo_compile_logs=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task302_mql5_compile_only_preflight_gate_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 repo artifact flags were not detected",
        )


def negative_test_task_302_missing_execution_false_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-302 preflight gate confirms MetaEditor was not executed\n",
            "",
            1,
        ).replace(
            "- TASK-302 preflight gate confirms MQL5 compile was not executed\n",
            "",
            1,
        ).replace(
            "- TASK-302 preflight gate confirms compile execution remains unauthorized\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 execution false flags were not detected",
        )


def negative_test_task_302_missing_no_mt5_no_compile_no_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-302 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-302 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-302 does not create .ex5 artifact\n",
            "",
            1,
        ).replace(
            "- TASK-302 does not create compile log\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT.replace(
            "- no MQL5 compile executed in TASK-302\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated\n",
            "",
            1,
        ).replace(
            "- no compile log generated\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task302_mql5_compile_only_preflight_gate_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 no-MT5/no-compile/no-artifact phrases were not detected",
        )


def negative_test_task_302_missing_no_trading_authorization_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-302 does not authorize trading\n",
            "",
            1,
        ).replace(
            "- TASK-302 preflight gate confirms trading remains unauthorized\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT.replace(
            "- not trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task302_mql5_compile_only_preflight_gate_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 no trading authorization phrase was not detected",
        )


def negative_test_task_302_missing_task303_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-303 must not be entered directly\n",
            "",
            1,
        ).replace(
            "- TASK-302 preflight gate confirms future TASK-303 requires GPT boundary\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT.replace(
            "- TASK-303 must not be entered directly\n",
            "",
            1,
        ).replace(
            "- future TASK-303 must be separately authorized by GPT before any compile execution\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task302_mql5_compile_only_preflight_gate_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 TASK-303 boundary phrase was not detected",
        )


def negative_test_task_302_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task302_mql5_compile_only_preflight_gate_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-302 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_303_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task303_mql5_compile_only_execution_authorization_plan_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 authorization plan doc was not detected",
        )


def negative_test_task_303_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-303 create v0.6.0 compile-only execution authorization planning packet\n",
            "",
            1,
        ).replace(
            "- TASK-303 create v0.6.0 compile-only execution authorization planning packet\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 current task phrase was not detected",
        )


def negative_test_task_303_missing_planning_authorization_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-303 is planning-only\n",
            "",
            1,
        ).replace(
            "- TASK-303 is authorization-boundary-only\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT.replace(
            "- planning-only\n",
            "",
            1,
        ).replace(
            "- authorization-boundary-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task303_mql5_compile_only_execution_authorization_plan_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 planning/authorization-boundary phrase was not detected",
        )


def negative_test_task_303_missing_bundle_check_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mql5-compile-only-execution-authorization-plan check is added to release validation bundle\n",
            "",
            1,
        ).replace(
            "- mql5-compile-only-execution-authorization-plan PASS\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 release bundle check phrase was not detected",
        )


def negative_test_task_303_missing_execution_authorization_false_flags():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-303 confirms compile execution remains unauthorized\n",
            "",
            1,
        ).replace(
            "- TASK-303 confirms MetaEditor was not executed\n",
            "",
            1,
        ).replace(
            "- TASK-303 confirms MQL5 compile was not executed\n",
            "",
            1,
        ).replace(
            "- compile_execution_authorized=false\n",
            "",
            1,
        ).replace(
            "- metaeditor_executed=false\n",
            "",
            1,
        ).replace(
            "- mql5_compile_executed=false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT.replace(
            "- compile-only execution authorization requires all preflight gates PASS\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task303_mql5_compile_only_execution_authorization_plan_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 execution authorization false flags were not detected",
        )


def negative_test_task_303_missing_no_mt5_no_compile_no_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-303 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-303 does not execute MQL5 compile\n",
            "",
            1,
        ).replace(
            "- TASK-303 does not execute MetaEditor\n",
            "",
            1,
        ).replace(
            "- TASK-303 does not create .ex5 artifact\n",
            "",
            1,
        ).replace(
            "- TASK-303 does not create compile log\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT.replace(
            "- no MQL5 compile executed in TASK-303\n",
            "",
            1,
        ).replace(
            "- no MetaEditor executed in TASK-303\n",
            "",
            1,
        ).replace(
            "- no MT5 run in TASK-303\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated\n",
            "",
            1,
        ).replace(
            "- no compile log generated\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task303_mql5_compile_only_execution_authorization_plan_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 no-MT5/no-compile/no-artifact phrases were not detected",
        )


def negative_test_task_303_missing_no_trading_authorization_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-303 does not authorize simulation trading\n",
            "",
            1,
        ).replace(
            "- TASK-303 does not authorize real trading\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT.replace(
            "- not simulation trading authorization\n",
            "",
            1,
        ).replace(
            "- not real trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task303_mql5_compile_only_execution_authorization_plan_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 no trading authorization phrase was not detected",
        )


def negative_test_task_303_missing_task304_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-304 must not be entered directly\n",
            "",
            1,
        ).replace(
            "- TASK-303 confirms future TASK-304 requires GPT boundary\n",
            "",
            1,
        ).replace(
            "- future_task_304_requires_gpt_boundary=true\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT.replace(
            "- TASK-304 must not be entered directly\n",
            "",
            1,
        ).replace(
            "- future TASK-304 must be separately authorized by GPT before any compile execution\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task303_mql5_compile_only_execution_authorization_plan_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 TASK-304 boundary phrase was not detected",
        )


def negative_test_task_303_missing_inventory_trading_keywords_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_TEXT.replace(
            "- MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- Buy / Sell / OrderSend / PositionOpen / CTrade remain false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task303_mql5_compile_only_execution_authorization_plan_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-303 inventory/trading keyword phrase was not detected",
        )


def negative_test_task_305_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task305_mql5_compile_only_failure_diagnostic_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-305 failure diagnostic doc was not detected",
        )


def negative_test_task_305_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-305 implement MQL5 compile-only failure diagnostic capture\n",
            "",
            1,
        ).replace(
            "- TASK-305 implement MQL5 compile-only failure diagnostic capture\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-305 current task phrase was not detected",
        )


def negative_test_task_305_missing_diagnostic_capture_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-304 failed, no success result doc created\n",
            "",
            1,
        ).replace(
            "- TASK-304 compile_exit_code=1 was observed\n",
            "",
            1,
        ).replace(
            "- TASK-305 diagnostic output is stdout-only\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_TEXT.replace(
            "- diagnostic-only\n",
            "",
            1,
        ).replace(
            "- compile_exit_code=1 was observed in TASK-304\n",
            "",
            1,
        ).replace(
            "- compile log must be stdout-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task305_mql5_compile_only_failure_diagnostic_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-305 diagnostic capture phrase was not detected",
        )


def negative_test_task_305_missing_no_artifact_no_mt5_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- no repo .ex5\n",
            "",
            1,
        ).replace(
            "- no repo compile log\n",
            "",
            1,
        ).replace(
            "- no MT5 terminal\n",
            "",
            1,
        ).replace(
            "- no Strategy Tester\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_TEXT.replace(
            "- no .ex5 artifact generated in repository\n",
            "",
            1,
        ).replace(
            "- no compile log generated in repository\n",
            "",
            1,
        ).replace(
            "- no MT5 terminal run\n",
            "",
            1,
        ).replace(
            "- no Strategy Tester run\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task305_mql5_compile_only_failure_diagnostic_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-305 no-artifact/no-MT5 phrases were not detected",
        )


def negative_test_task_305_missing_task306_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-306 requires GPT boundary\n",
            "",
            1,
        ).replace(
            "- TASK-306 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_TEXT.replace(
            "- TASK-306 must not be entered directly\n",
            "",
            1,
        ).replace(
            "- future TASK-306 must be separately authorized by GPT before any MQ5 fixes or compile retry\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task305_mql5_compile_only_failure_diagnostic_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-305 TASK-306 boundary phrase was not detected",
        )


def positive_test_task_306_complete_classification_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return "complete TASK-306 diagnostic classification fixture failed\n" + combined_output(result)
        return ""


def negative_test_task_306_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task306_mql5_compile_diagnostic_result_classification_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 diagnostic classification doc was not detected",
        )


def negative_test_task_306_missing_current_task_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- current task is TASK-306 implement MQL5 compile-only diagnostic result classification\n",
            "",
            1,
        ).replace(
            "- TASK-306 implement MQL5 compile-only diagnostic result classification\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 current task phrase was not detected",
        )


def negative_test_task_306_missing_classification_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-306 is diagnostic-classification-only\n",
            "",
            1,
        ).replace(
            "- compile_result_classification=metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT.replace(
            "- diagnostic-classification-only\n",
            "",
            1,
        ).replace(
            "- compile_result_classification=metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task306_mql5_compile_diagnostic_result_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 classification phrase was not detected",
        )


def negative_test_task_306_missing_compile_log_semantic_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- compile_exit_code=1 observed in TASK-305\n",
            "",
            1,
        ).replace(
            "- compile log semantic result indicates Result: 0 errors, 0 warnings\n",
            "",
            1,
        ).replace(
            "- compile_log_semantic_success=true\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT.replace(
            "- compile_exit_code=1 observed in TASK-305\n",
            "",
            1,
        ).replace(
            "- compile log excerpt indicated Result: 0 errors, 0 warnings\n",
            "",
            1,
        ).replace(
            "- compile_log_semantic_success=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task306_mql5_compile_diagnostic_result_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 compile log semantic phrase was not detected",
        )


def negative_test_task_306_missing_success_false_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- compile_success=false\n",
            "",
            1,
        ).replace(
            "- task304_success_result_created=false\n",
            "",
            1,
        ).replace(
            "- followup_required=true\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT.replace(
            "- compile_success=false\n",
            "",
            1,
        ).replace(
            "- task304_success_result_created=false\n",
            "",
            1,
        ).replace(
            "- followup_required=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task306_mql5_compile_diagnostic_result_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 success false phrase was not detected",
        )


def negative_test_task_306_missing_no_execution_no_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-306 is not compile execution\n",
            "",
            1,
        ).replace(
            "- TASK-306 has no new MetaEditor execution in TASK-306\n",
            "",
            1,
        ).replace(
            "- TASK-306 does not run MT5 terminal\n",
            "",
            1,
        ).replace(
            "- repo_ex5_artifacts=false\n",
            "",
            1,
        ).replace(
            "- repo_compile_logs=false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT.replace(
            "- not compile execution\n",
            "",
            1,
        ).replace(
            "- not MetaEditor execution in TASK-306\n",
            "",
            1,
        ).replace(
            "- not MT5 run\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated in repository\n",
            "",
            1,
        ).replace(
            "- no compile log generated in repository\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task306_mql5_compile_diagnostic_result_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 no-execution/no-artifact phrase was not detected",
        )


def negative_test_task_306_missing_task307_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-307 requires GPT boundary before any compile retry or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-307 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_TEXT.replace(
            "- future TASK-307 must be separately authorized by GPT before any compile retry or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-307 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task306_mql5_compile_diagnostic_result_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-306 TASK-307 boundary phrase was not detected",
        )


def positive_test_task_307_complete_artifact_classification_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return "complete TASK-307 diagnostic artifact classification fixture failed\n" + combined_output(result)
        return ""


def negative_test_task_307_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task307_mql5_compile_diagnostic_artifact_classification_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-307 diagnostic artifact classification doc was not detected",
        )


def negative_test_task_307_missing_artifact_classification_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-307 is diagnostic-artifact-classification-only\n",
            "",
            1,
        ).replace(
            "- quarantine artifact inspection before cleanup\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_TEXT.replace(
            "- diagnostic-artifact-classification-only\n",
            "",
            1,
        ).replace(
            "- quarantine artifact inspection before cleanup\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task307_mql5_compile_diagnostic_artifact_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-307 artifact classification phrase was not detected",
        )


def negative_test_task_307_missing_no_repo_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- quarantine .ex5 must not be copied to repository\n",
            "",
            1,
        ).replace(
            "- repo_ex5_artifacts=false\n",
            "",
            1,
        ).replace(
            "- repo_compile_logs=false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_TEXT.replace(
            "- quarantine .ex5 must not be copied to repository\n",
            "",
            1,
        ).replace(
            "- repo_ex5_artifacts=false\n",
            "",
            1,
        ).replace(
            "- repo_compile_logs=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task307_mql5_compile_diagnostic_artifact_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-307 no-repo-artifact phrase was not detected",
        )


def negative_test_task_307_missing_task308_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-308 requires GPT boundary before any compile retry or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-308 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_TEXT.replace(
            "- future TASK-308 must be separately authorized by GPT before any compile retry or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-308 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task307_mql5_compile_diagnostic_artifact_classification_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-307 TASK-308 boundary phrase was not detected",
        )


def positive_test_task_308_complete_artifact_proof_boundary_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return "complete TASK-308 diagnostic artifact proof boundary fixture failed\n" + combined_output(result)
        return ""


def negative_test_task_308_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task308_mql5_compile_diagnostic_artifact_proof_boundary_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-308 diagnostic artifact proof boundary doc was not detected",
        )


def negative_test_task_308_missing_diagnostic_proof_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-308 is diagnostic-proof-boundary-only\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_TEXT.replace(
            "- diagnostic-proof-boundary-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task308_mql5_compile_diagnostic_artifact_proof_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-308 diagnostic-proof-boundary phrase was not detected",
        )


def negative_test_task_308_missing_proof_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mql5-compile-diagnostic-artifact-proof-boundary check is added to release validation bundle\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-308 proof boundary check name was not detected",
        )


def negative_test_task_308_missing_previous_classification_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- previous classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        ).replace(
            "- compiled_artifact_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_TEXT.replace(
            "- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task308_mql5_compile_diagnostic_artifact_proof_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-308 previous classification phrase was not detected",
        )


def negative_test_task_308_missing_future_task309_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- future_task_309_requires_gpt_boundary=true\n",
            "",
            1,
        ).replace(
            "- future TASK-309 requires GPT boundary before any compile retry, MQ5 fix, artifact hash capture, or success reclassification\n",
            "",
            1,
        ).replace(
            "- TASK-309 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_TEXT.replace(
            "- future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification\n",
            "",
            1,
        ).replace(
            "- TASK-309 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task308_mql5_compile_diagnostic_artifact_proof_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-308 future TASK-309 boundary phrase was not detected",
        )


def negative_test_task_308_missing_no_mt5_no_compile_no_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- no MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no MetaEditor execution\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_TEXT.replace(
            "- not compile execution\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated in repository\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task308_mql5_compile_diagnostic_artifact_proof_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-308 no MT5/no compile/no artifact phrase was not detected",
        )


def positive_test_task_309_complete_success_reclassification_boundary_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return "complete TASK-309 success reclassification boundary fixture failed\n" + combined_output(result)
        return ""


def negative_test_task_309_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task309_mql5_compile_success_reclassification_boundary_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-309 success reclassification boundary doc was not detected",
        )


def negative_test_task_309_missing_success_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-309 is success-reclassification-boundary-only\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_TEXT.replace(
            "- success-reclassification-boundary-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task309_mql5_compile_success_reclassification_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-309 success-reclassification-boundary phrase was not detected",
        )


def negative_test_task_309_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mql5-compile-success-reclassification-boundary check is added to release validation bundle\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-309 success reclassification check name was not detected",
        )


def negative_test_task_309_missing_previous_classification_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- previous classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        ).replace(
            "- compiled_artifact_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_TEXT.replace(
            "- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task309_mql5_compile_success_reclassification_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-309 previous classification phrase was not detected",
        )


def negative_test_task_309_missing_future_task310_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- future_task_310_requires_gpt_boundary=true\n",
            "",
            1,
        ).replace(
            "- future TASK-310 requires GPT boundary before any compile retry, artifact hash capture, success reclassification, or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-310 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_TEXT.replace(
            "- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-310 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task309_mql5_compile_success_reclassification_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-309 future TASK-310 boundary phrase was not detected",
        )


def negative_test_task_309_missing_no_mt5_no_compile_no_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- no MQL5 compile\n",
            "",
            1,
        ).replace(
            "- no MetaEditor execution\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_TEXT.replace(
            "- not compile execution\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated in repository\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task309_mql5_compile_success_reclassification_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-309 no MT5/no compile/no artifact phrase was not detected",
        )


def positive_test_task_310_complete_artifact_hash_capture_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return "complete TASK-310 artifact hash capture fixture failed\n" + combined_output(result)
        return ""


def negative_test_task_310_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root, task310_mql5_compile_artifact_hash_capture_text=None)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-310 artifact hash capture doc was not detected",
        )


def negative_test_task_310_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mql5-compile-artifact-hash-capture-boundary check is added to release validation bundle\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-310 artifact hash capture check name was not detected",
        )


def negative_test_task_310_missing_stdout_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- artifact hash stdout-only\n",
            "",
            1,
        ).replace(
            "- artifact hash not saved to repository\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_TEXT.replace(
            "- artifact hash must be stdout-only\n",
            "",
            1,
        ).replace(
            "- artifact hash must not be saved to repository\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task310_mql5_compile_artifact_hash_capture_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-310 stdout-only artifact hash phrase was not detected",
        )


def negative_test_task_310_missing_no_success_reclassification_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- success_reclassification_done=false\n",
            "",
            1,
        ).replace(
            "- task304_success_result_created=false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_TEXT.replace(
            "- success_reclassification_done=false\n",
            "",
            1,
        ).replace(
            "- task304_success_result_created=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task310_mql5_compile_artifact_hash_capture_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-310 no success reclassification phrase was not detected",
        )


def negative_test_task_310_missing_future_task311_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- future_task_311_requires_gpt_boundary=true\n",
            "",
            1,
        ).replace(
            "- future TASK-311 requires GPT boundary before success reclassification or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-311 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_TEXT.replace(
            "- future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix\n",
            "",
            1,
        ).replace(
            "- TASK-311 must not be entered directly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task310_mql5_compile_artifact_hash_capture_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-310 future TASK-311 boundary phrase was not detected",
        )


def positive_test_task_311_complete_success_reclassification_decision_boundary_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-311 success reclassification decision boundary fixture failed\n"
                + combined_output(result)
            )
        return ""


def negative_test_task_311_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task311_mql5_compile_success_reclassification_decision_boundary_text=None,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 success reclassification decision boundary doc was not detected",
        )


def negative_test_task_311_missing_decision_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- TASK-311 is success-reclassification-decision-boundary-only\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT.replace(
            "- success-reclassification-decision-boundary-only\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task311_mql5_compile_success_reclassification_decision_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 decision boundary phrase was not detected",
        )


def negative_test_task_311_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mql5-compile-success-reclassification-decision-boundary check is added to release validation bundle\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 decision boundary check name was not detected",
        )


def negative_test_task_311_missing_previous_classification_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- previous classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT.replace(
            "- TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task311_mql5_compile_success_reclassification_decision_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 previous classification phrase was not detected",
        )


def negative_test_task_311_missing_artifact_hash_stdout_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- artifact hash was stdout-only and must not be stored in repository\n",
            "",
            1,
        ).replace(
            "- artifact_hash_stored_in_repo=false\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT.replace(
            "- TASK-310 artifact hash was stdout-only and must not be stored in repository\n",
            "",
            1,
        ).replace(
            "- TASK-311 does not store artifact hash\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task311_mql5_compile_success_reclassification_decision_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 artifact hash stdout-only phrase was not detected",
        )


def negative_test_task_311_missing_future_task312_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- future_task_312_requires_gpt_boundary=true\n",
            "",
            1,
        ).replace(
            "- future TASK-312 requires GPT boundary before success reclassification, MQ5 fix, or compile retry\n",
            "",
            1,
        ).replace(
            "- TASK-312 must not be entered directly\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT.replace(
            "- future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry\n",
            "",
            1,
        ).replace(
            "- TASK-312 must not be entered directly\n",
            "",
            1,
        ).replace(
            "- future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task311_mql5_compile_success_reclassification_decision_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 future TASK-312 boundary phrase was not detected",
        )


def negative_test_task_311_missing_no_mt5_no_compile_no_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- no MetaEditor execution in TASK-311\n",
            "",
            1,
        ).replace(
            "- no MQL5 compile in TASK-311\n",
            "",
            1,
        ).replace(
            "- no success reclassification in TASK-311\n",
            "",
            1,
        )
        boundary_text = DEFAULT_TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_TEXT.replace(
            "- not MetaEditor execution in TASK-311\n",
            "",
            1,
        ).replace(
            "- not compile execution\n",
            "",
            1,
        ).replace(
            "- no .ex5 artifact generated in repository\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task311_mql5_compile_success_reclassification_decision_boundary_text=boundary_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-311 no MT5/no compile/no artifact phrase was not detected",
        )


def positive_test_task_312_complete_success_reclassification_decision_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-312 success reclassification decision fixture failed\n"
                f"{combined_output(result)}"
            )
    return ""


def negative_test_task_312_missing_decision_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task312_mql5_compile_success_reclassification_decision_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-312 success reclassification decision doc was not detected",
        )


def negative_test_task_312_missing_pass_decision_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- success_reclassification_decision=PASS\n", "")
        decision_text = DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT.replace(
            "- success_reclassification_decision=PASS\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task312_mql5_compile_success_reclassification_decision_text=decision_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-312 PASS decision phrase was not detected",
        )


def negative_test_task_312_missing_compile_scope_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- compile_success_scope=compile-only-diagnostic\n", "")
        decision_text = DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT.replace(
            "- compile_success_scope=compile-only-diagnostic\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task312_mql5_compile_success_reclassification_decision_text=decision_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-312 compile-only scope phrase was not detected",
        )


def negative_test_task_312_missing_no_readiness_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- compile-only success does not imply trading authorization\n", "")
            .replace("- compile-only success does not imply deployment readiness\n", "")
            .replace("- compile-only success does not imply backtest readiness\n", "")
            .replace("- compile-only success does not imply strategy readiness\n", "")
        )
        decision_text = (
            DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT
            .replace("- not trading authorization\n", "")
            .replace("- not deployment readiness\n", "")
            .replace("- not backtest readiness\n", "")
            .replace("- not strategy readiness\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task312_mql5_compile_success_reclassification_decision_text=decision_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-312 no readiness phrase was not detected",
        )


def negative_test_task_312_missing_hash_stdout_only_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- artifact_hash_stdout_only=true\n", "")
            .replace("- artifact_hash_saved_to_repo=false\n", "")
            .replace("- do not include actual artifact hash value in this doc\n", "")
        )
        decision_text = (
            DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT
            .replace("- artifact_hash_stdout_only=true\n", "")
            .replace("- artifact_hash_saved_to_repo=false\n", "")
            .replace("- do not include actual artifact hash value in this doc\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task312_mql5_compile_success_reclassification_decision_text=decision_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-312 artifact hash stdout-only phrase was not detected",
        )


def negative_test_task_312_missing_future_task313_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_313_requires_gpt_boundary=true\n", "")
            .replace(
                "- future TASK-313 requires GPT boundary before MT5 run, Strategy Tester, backtest, deployment, or trading-related step\n",
                "",
            )
            .replace("- TASK-313 must not be entered directly\n", "")
        )
        decision_text = (
            DEFAULT_TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_TEXT
            .replace(
                "- future TASK-313 must be separately authorized by GPT before any MT5 run, Strategy Tester, backtest, deployment, or trading-related step\n",
                "",
            )
            .replace("- TASK-313 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task312_mql5_compile_success_reclassification_decision_text=decision_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-312 future TASK-313 boundary phrase was not detected",
        )


def positive_test_task_313_complete_mt5_no_trade_startup_boundary_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-313 MT5 no-trade startup boundary fixture failed\n"
                f"{combined_output(result)}"
            )
    return ""


def negative_test_task_313_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task313_mt5_no_trade_startup_boundary_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-313 MT5 startup boundary doc was not detected",
        )


def negative_test_task_313_missing_startup_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- TASK-313 is mt5-startup-boundary-only\n", "")
        boundary_text = DEFAULT_TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_TEXT.replace(
            "- mt5-startup-boundary-only\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task313_mt5_no_trade_startup_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-313 mt5-startup-boundary-only phrase was not detected",
        )


def negative_test_task_313_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- mt5-no-trade-startup-boundary check is added to release validation bundle\n", "")
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-313 startup boundary check name was not detected",
        )


def negative_test_task_313_missing_task312_compile_only_scope_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- compile_success_scope=compile-only-diagnostic\n", "")
        boundary_text = DEFAULT_TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_TEXT.replace(
            "- TASK-312 compile_success_scope=compile-only-diagnostic\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task313_mt5_no_trade_startup_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-313 TASK-312 compile-only scope phrase was not detected",
        )


def negative_test_task_313_missing_future_task314_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_314_requires_gpt_boundary=true\n", "")
            .replace("- future TASK-314 requires GPT boundary before MT5 terminal startup attempt\n", "")
            .replace("- TASK-314 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_TEXT
            .replace("- future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-314 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task313_mt5_no_trade_startup_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-313 future TASK-314 boundary phrase was not detected",
        )


def negative_test_task_313_missing_no_mt5_strategy_tester_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- no MT5 run in TASK-313\n", "")
            .replace("- no Strategy Tester\n", "")
            .replace("- no trading authorization\n", "")
        )
        boundary_text = (
            DEFAULT_TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_TEXT
            .replace("- not MT5 run in TASK-313\n", "")
            .replace("- not Strategy Tester authorization\n", "")
            .replace("- not trading authorization\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task313_mt5_no_trade_startup_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-313 no MT5/no Strategy Tester/no trading phrase was not detected",
        )


def positive_test_task_314_complete_mt5_no_trade_startup_command_discovery_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-314 MT5 no-trade startup command discovery fixture failed\n"
                f"{combined_output(result)}"
            )
    return ""


def negative_test_task_314_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task314_mt5_no_trade_startup_command_discovery_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-314 MT5 startup command discovery doc was not detected",
        )


def negative_test_task_314_missing_command_discovery_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- TASK-314 is command-discovery-only\n", "")
        boundary_text = DEFAULT_TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_TEXT.replace(
            "- command-discovery-only\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task314_mt5_no_trade_startup_command_discovery_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-314 command-discovery-only phrase was not detected",
        )


def negative_test_task_314_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- mt5-no-trade-startup-command-discovery check is added to release validation bundle\n", "")
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-314 startup command discovery check name was not detected",
        )


def negative_test_task_314_missing_task312_compile_only_scope_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- compile_success_scope=compile-only-diagnostic\n", "")
        boundary_text = DEFAULT_TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_TEXT.replace(
            "- TASK-312 compile_success_scope=compile-only-diagnostic\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task314_mt5_no_trade_startup_command_discovery_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-314 TASK-312 compile-only scope phrase was not detected",
        )


def negative_test_task_314_missing_future_task315_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_315_requires_gpt_boundary=true\n", "")
            .replace("- future TASK-315 requires GPT boundary before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-315 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_TEXT
            .replace("- future TASK-315 must be separately authorized by GPT before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-315 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task314_mt5_no_trade_startup_command_discovery_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-314 future TASK-315 boundary phrase was not detected",
        )


def negative_test_task_314_missing_no_mt5_terminal_strategy_tester_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- no MT5 run in TASK-314\n", "")
            .replace("- no terminal64.exe execution\n", "")
            .replace("- no Strategy Tester\n", "")
            .replace("- no trading authorization\n", "")
        )
        boundary_text = (
            DEFAULT_TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_TEXT
            .replace("- not MT5 run in TASK-314\n", "")
            .replace("- not terminal64.exe execution in TASK-314\n", "")
            .replace("- not Strategy Tester authorization\n", "")
            .replace("- not trading authorization\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task314_mt5_no_trade_startup_command_discovery_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-314 no MT5/no terminal/no Strategy Tester/no trading phrase was not detected",
        )


def positive_test_task_315_complete_mt5_no_trade_startup_quarantine_preparation_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-315 MT5 no-trade startup quarantine preparation fixture failed\n"
                f"{combined_output(result)}"
            )
    return ""


def negative_test_task_315_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task315_mt5_no_trade_startup_quarantine_preparation_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-315 MT5 startup quarantine preparation doc was not detected",
        )


def negative_test_task_315_missing_quarantine_preparation_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- TASK-315 is startup-quarantine-preparation-only\n", "")
        boundary_text = DEFAULT_TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_TEXT.replace(
            "- startup-quarantine-preparation-only\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task315_mt5_no_trade_startup_quarantine_preparation_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-315 startup-quarantine-preparation-only phrase was not detected",
        )


def negative_test_task_315_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- mt5-no-trade-startup-quarantine-preparation check is added to release validation bundle\n", "")
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-315 startup quarantine preparation check name was not detected",
        )


def negative_test_task_315_missing_task312_compile_only_scope_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- compile_success_scope=compile-only-diagnostic\n", "")
        boundary_text = DEFAULT_TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_TEXT.replace(
            "- TASK-312 compile_success_scope=compile-only-diagnostic\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task315_mt5_no_trade_startup_quarantine_preparation_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-315 TASK-312 compile-only scope phrase was not detected",
        )


def negative_test_task_315_missing_future_task316_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_316_requires_gpt_boundary=true\n", "")
            .replace("- future TASK-316 requires GPT boundary before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-316 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_TEXT
            .replace("- future TASK-316 must be separately authorized by GPT before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-316 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task315_mt5_no_trade_startup_quarantine_preparation_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-315 future TASK-316 boundary phrase was not detected",
        )


def negative_test_task_315_missing_no_terminal_data_startup_log_no_mt5_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- repo_terminal_data_directory=false\n", "")
            .replace("- repo_startup_logs=false\n", "")
            .replace("- no MT5 run in TASK-315\n", "")
            .replace("- no terminal64.exe execution in TASK-315\n", "")
            .replace("- no Strategy Tester\n", "")
            .replace("- no trading authorization\n", "")
        )
        boundary_text = (
            DEFAULT_TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_TEXT
            .replace("- no terminal data directory created in repository\n", "")
            .replace("- no startup log generated in repository\n", "")
            .replace("- not MT5 run in TASK-315\n", "")
            .replace("- not terminal64.exe execution in TASK-315\n", "")
            .replace("- not Strategy Tester authorization\n", "")
            .replace("- not trading authorization\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task315_mt5_no_trade_startup_quarantine_preparation_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-315 no terminal data/no startup log/no MT5/no trading phrase was not detected",
        )


def positive_test_task_316_complete_mt5_no_trade_startup_dryrun_config_boundary_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-316 MT5 no-trade startup dry-run config boundary fixture failed\n"
                f"{combined_output(result)}"
            )
    return ""


def negative_test_task_316_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task316_mt5_no_trade_startup_dryrun_config_boundary_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-316 MT5 startup dry-run config boundary doc was not detected",
        )


def negative_test_task_316_missing_dryrun_config_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- TASK-316 is startup-dryrun-config-boundary-only\n", "")
        boundary_text = DEFAULT_TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_TEXT.replace(
            "- startup-dryrun-config-boundary-only\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task316_mt5_no_trade_startup_dryrun_config_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-316 startup-dryrun-config-boundary-only phrase was not detected",
        )


def negative_test_task_316_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mt5-no-trade-startup-dryrun-config-boundary check is added to release validation bundle\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-316 startup dry-run config boundary check name was not detected",
        )


def negative_test_task_316_missing_task312_compile_only_scope_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- compile_success_scope=compile-only-diagnostic\n", "")
        boundary_text = DEFAULT_TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_TEXT.replace(
            "- TASK-312 compile_success_scope=compile-only-diagnostic\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task316_mt5_no_trade_startup_dryrun_config_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-316 TASK-312 compile-only scope phrase was not detected",
        )


def negative_test_task_316_missing_future_task317_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_317_requires_gpt_boundary=true\n", "")
            .replace("- future TASK-317 requires GPT boundary before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-317 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_TEXT
            .replace("- future TASK-317 must be separately authorized by GPT before any MT5 terminal startup attempt\n", "")
            .replace("- TASK-317 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task316_mt5_no_trade_startup_dryrun_config_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-316 future TASK-317 boundary phrase was not detected",
        )


def negative_test_task_316_missing_no_config_terminal_data_startup_log_no_mt5_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- no_trade_config_generated_in_repo=false\n", "")
            .replace("- no no-trade config file generated in repository\n", "")
            .replace("- repo_terminal_data_directory=false\n", "")
            .replace("- repo_startup_logs=false\n", "")
            .replace("- no MT5 run in TASK-316\n", "")
            .replace("- no terminal64.exe execution in TASK-316\n", "")
            .replace("- no terminal.exe execution in TASK-316\n", "")
            .replace("- no Strategy Tester\n", "")
            .replace("- no trading authorization\n", "")
        )
        boundary_text = (
            DEFAULT_TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_TEXT
            .replace("- no no-trade config file generated in repository\n", "")
            .replace("- no terminal data directory created in repository\n", "")
            .replace("- no startup log generated in repository\n", "")
            .replace("- not MT5 run in TASK-316\n", "")
            .replace("- not terminal64.exe execution in TASK-316\n", "")
            .replace("- not terminal.exe execution in TASK-316\n", "")
            .replace("- not Strategy Tester authorization\n", "")
            .replace("- not trading authorization\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task316_mt5_no_trade_startup_dryrun_config_boundary_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-316 no config/no terminal data/no startup log/no MT5/no trading phrase was not detected",
        )


def positive_test_task_317_complete_mt5_no_trade_startup_config_template_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        if result.returncode != 0:
            return (
                "complete TASK-317 MT5 no-trade startup config template fixture failed\n"
                f"{combined_output(result)}"
            )
    return ""


def negative_test_task_317_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task317_mt5_no_trade_startup_config_template_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-317 MT5 startup config template doc was not detected",
        )


def negative_test_task_317_missing_stdout_template_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- TASK-317 is stdout-only-config-template-preview\n", "")
        boundary_text = DEFAULT_TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_TEXT.replace(
            "- stdout-only-config-template-preview\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task317_mt5_no_trade_startup_config_template_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-317 stdout-only-config-template-preview phrase was not detected",
        )


def negative_test_task_317_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mt5-no-trade-startup-config-template check is added to release validation bundle\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-317 startup config template check name was not detected",
        )


def negative_test_task_317_missing_no_config_no_mt5_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- config_file_generated=false\n", "")
            .replace("- no_trade_config_generated_in_repo=false\n", "")
            .replace("- no config file generated\n", "")
            .replace("- no MT5 terminal executed\n", "")
            .replace("- no terminal64 execution\n", "")
            .replace("- no terminal.exe execution\n", "")
            .replace("- no Strategy Tester\n", "")
            .replace("- no trading authorization\n", "")
        )
        boundary_text = (
            DEFAULT_TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_TEXT
            .replace("- no config file generated in TASK-317\n", "")
            .replace("- not MT5 run in TASK-317\n", "")
            .replace("- not terminal64.exe execution in TASK-317\n", "")
            .replace("- not terminal.exe execution in TASK-317\n", "")
            .replace("- not Strategy Tester authorization\n", "")
            .replace("- not trading authorization\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task317_mt5_no_trade_startup_config_template_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-317 no config/no MT5/no terminal/no trading phrase was not detected",
        )


def negative_test_task_317_missing_future_task318_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_318_requires_gpt_boundary=true\n", "")
            .replace(
                "- future TASK-318 requires GPT boundary before writing any startup config file or launching MT5\n",
                "",
            )
            .replace("- TASK-318 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_TEXT
            .replace(
                "- future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5\n",
                "",
            )
            .replace("- TASK-318 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task317_mt5_no_trade_startup_config_template_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-317 future TASK-318 boundary phrase was not detected",
        )


def negative_test_task_317_missing_template_field_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        boundary_text = (
            DEFAULT_TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_TEXT
            .replace("- InpEnableTrading=false\n", "")
            .replace("- future no-trade config template\n", "")
        )
        build_temp_project(
            temp_root,
            task317_mt5_no_trade_startup_config_template_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-317 no-trade config template field phrase was not detected",
        )


def positive_test_task_318_complete_mt5_no_trade_startup_authorization_plan_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        return expect_validation_passed(
            result,
            "complete TASK-318 MT5 no-trade startup authorization plan fixture should pass",
        )


def negative_test_task_318_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task318_mt5_no_trade_startup_authorization_plan_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-318 MT5 no-trade startup authorization plan doc was not detected",
        )


def negative_test_task_318_missing_planning_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- TASK-318 is planning-only\n", "")
            .replace("- TASK-318 is authorization-boundary-only\n", "")
        )
        boundary_text = (
            DEFAULT_TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_TEXT
            .replace("- planning-only\n", "")
            .replace("- authorization-boundary-only\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task318_mt5_no_trade_startup_authorization_plan_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-318 planning/boundary phrase was not detected",
        )


def negative_test_task_318_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mt5-no-trade-startup-authorization-plan check is added to release validation bundle\n",
            "",
        )
        boundary_text = DEFAULT_TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_TEXT.replace(
            "- mt5-no-trade-startup-authorization-plan\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task318_mt5_no_trade_startup_authorization_plan_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-318 release bundle check name phrase was not detected",
        )


def negative_test_task_318_missing_future_task319_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_319_requires_gpt_boundary=true\n", "")
            .replace(
                "- future TASK-319 requires GPT boundary before any MT5 terminal startup execution\n",
                "",
            )
            .replace("- TASK-319 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_TEXT
            .replace("- future TASK-319 must be separately authorized by GPT\n", "")
            .replace("- TASK-319 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task318_mt5_no_trade_startup_authorization_plan_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-318 future TASK-319 boundary phrase was not detected",
        )


def negative_test_task_318_missing_no_mt5_compile_artifact_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- no MT5 run in TASK-318\n", "")
            .replace("- no MQL5 compile\n", "")
            .replace("- no .ex5 artifact\n", "")
            .replace("- no compile log\n", "")
        )
        boundary_text = (
            DEFAULT_TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_TEXT
            .replace("- not MT5 run in TASK-318\n", "")
            .replace("- not MQL5 compile in TASK-318\n", "")
            .replace("- no .ex5 artifact generated\n", "")
            .replace("- no compile log generated\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task318_mt5_no_trade_startup_authorization_plan_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-318 no MT5/no compile/no artifact phrase was not detected",
        )


def positive_test_task_319_complete_mt5_no_trade_startup_preflight_gate_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        result = run_validator(temp_root)
        return expect_validation_passed(
            result,
            "complete TASK-319 MT5 no-trade startup preflight gate fixture should pass",
        )


def negative_test_task_319_missing_plan_doc():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(
            temp_root,
            task319_mt5_no_trade_startup_preflight_gate_text=None,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-319 MT5 no-trade startup preflight gate doc was not detected",
        )


def negative_test_task_319_missing_preflight_gate_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace("- TASK-319 is startup-preflight-gate-only\n", "")
        boundary_text = DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT.replace(
            "- startup-preflight-gate-only\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task319_mt5_no_trade_startup_preflight_gate_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-319 startup-preflight-gate-only phrase was not detected",
        )


def negative_test_task_319_missing_check_name_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = doc_text().replace(
            "- mt5-no-trade-startup-preflight-gate check is added to release validation bundle\n",
            "",
        )
        boundary_text = DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT.replace(
            "- mt5-no-trade-startup-preflight-gate\n",
            "",
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task319_mt5_no_trade_startup_preflight_gate_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-319 release bundle check name phrase was not detected",
        )


def negative_test_task_319_missing_no_mt5_terminal_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- no MT5 run in TASK-319\n", "")
            .replace("- no terminal64.exe execution in TASK-319\n", "")
            .replace("- no terminal.exe execution in TASK-319\n", "")
            .replace("- no Strategy Tester\n", "")
            .replace("- no backtest\n", "")
            .replace("- no trading authorization\n", "")
        )
        boundary_text = (
            DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT
            .replace("- not MT5 run in TASK-319\n", "")
            .replace("- not terminal64.exe execution in TASK-319\n", "")
            .replace("- not terminal.exe execution in TASK-319\n", "")
            .replace("- not Strategy Tester authorization\n", "")
            .replace("- not trading authorization\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task319_mt5_no_trade_startup_preflight_gate_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-319 no MT5/no terminal/no trading phrase was not detected",
        )


def negative_test_task_319_missing_future_task320_boundary_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_text = (
            doc_text()
            .replace("- future_task_320_requires_gpt_boundary=true\n", "")
            .replace(
                "- future TASK-320 requires GPT boundary before any MT5 terminal startup attempt\n",
                "",
            )
            .replace("- TASK-320 must not be entered directly\n", "")
        )
        boundary_text = (
            DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT
            .replace(
                "- future TASK-320 must be separately authorized by GPT before any MT5 terminal startup attempt\n",
                "",
            )
            .replace("- TASK-320 must not be entered directly\n", "")
        )
        build_temp_project(
            temp_root,
            current_text=missing_text,
            handoff_text=missing_text,
            project_text=missing_text,
            task319_mt5_no_trade_startup_preflight_gate_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-319 future TASK-320 boundary phrase was not detected",
        )


def negative_test_task_319_missing_future_startup_condition_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        boundary_text = (
            DEFAULT_TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_TEXT
            .replace("- future startup must use no-trade config\n", "")
            .replace("- future startup must prove InpEnableTrading=false before startup\n", "")
            .replace("- future startup must not place orders\n", "")
        )
        build_temp_project(
            temp_root,
            task319_mt5_no_trade_startup_preflight_gate_text=boundary_text,
        )
        result = run_validator(temp_root)
        return expect_validation_failed(
            result,
            "missing TASK-319 future startup preflight condition was not detected",
        )


def write_static_interface_fixture(temp_root, overrides=None):
    overrides = overrides or {}
    files = {
        "mq5/TradingSystem.mq5": (
            '#property strict\n'
            '#include "core/EaController.mqh"\n'
            "EaController controller;\n"
            "int OnInit(){ return controller.OnInit(); }\n"
            "void OnTick(){ controller.OnTick(); }\n"
            "void OnDeinit(const int reason){ controller.OnDeinit(reason); }\n"
        ),
        "mq5/config/InputConfig.mqh": (
            "#ifndef INPUT_CONFIG_MQH\n#define INPUT_CONFIG_MQH\n"
            "input bool InpEnableTrading = false;\n"
            "input bool InpEnableNoTradeObservability = true;\n"
            "input bool InpObservabilityLogOnTick = false;\n"
            "#endif\n"
        ),
        "mq5/logger/Logger.mqh": (
            "#ifndef LOGGER_MQH\n#define LOGGER_MQH\n"
            '#include "../config/InputConfig.mqh"\n'
            "class Logger { public: bool Init(){ return true; }\n"
            "void NoTradeObservabilityStatusSnapshot(){}\n"
            "void NoTradeComponentStatusSnapshot(){}\n"
            "void LogReadOnlyControllerSummarySnapshot(){}\n"
            "void LogReadOnlyTelemetryAggregationSnapshot(){}\n"
            'string InventoryNotice(){ return "Inventory only; no MT5 run; no trading authorization."; }\n'
            "};\n#endif\n"
        ),
        "mq5/signals/SignalEngine.mqh": (
            "#ifndef SIGNAL_ENGINE_MQH\n#define SIGNAL_ENGINE_MQH\n"
            '#include "../logger/Logger.mqh"\n'
            "class SignalEngine { public: bool Init(Logger &log){ return true; }\n"
            'string GetSignalStatusSnapshot(){ return "signal_status=read-only framework"; }\n'
            'string GetReadOnlySignalContextSnapshot(){ return "signal_context_snapshot=true"; }\n'
            "};\n#endif\n"
        ),
        "mq5/risk/RiskManager.mqh": (
            "#ifndef RISK_MANAGER_MQH\n#define RISK_MANAGER_MQH\n"
            '#include "../logger/Logger.mqh"\n'
            "class RiskManager { public: bool Init(Logger &log){ return true; }\n"
            'string GetRiskStatusSnapshot(){ return "risk_status=read-only framework"; }\n'
            'string GetReadOnlyRiskContextSnapshot(){ return "risk_context_snapshot=true"; }\n'
            "};\n#endif\n"
        ),
        "mq5/execution/ExecutionManager.mqh": (
            "#ifndef EXECUTION_MANAGER_MQH\n#define EXECUTION_MANAGER_MQH\n"
            '#include "../logger/Logger.mqh"\n'
            '#include "../signals/SignalEngine.mqh"\n'
            "class ExecutionManager { public: bool Init(Logger &log){ return true; }\n"
            'string GetExecutionStatusSnapshot(){ return "execution_status=read-only framework"; }\n'
            'string GetReadOnlyExecutionContextSnapshot(){ return "execution_context_snapshot=true"; }\n'
            "};\n#endif\n"
        ),
        "mq5/core/EaController.mqh": (
            "#ifndef EA_CONTROLLER_MQH\n#define EA_CONTROLLER_MQH\n"
            '#include "../config/InputConfig.mqh"\n'
            '#include "../logger/Logger.mqh"\n'
            '#include "../signals/SignalEngine.mqh"\n'
            '#include "../risk/RiskManager.mqh"\n'
            '#include "../execution/ExecutionManager.mqh"\n'
            "class EaController { private: Logger logger; SignalEngine signalEngine; RiskManager riskManager; ExecutionManager executionManager;\n"
            "public: int OnInit(){ logger.Init(); signalEngine.Init(logger); riskManager.Init(logger); executionManager.Init(logger); WriteNoTradeObservability(); return 0; }\n"
            "void OnTick(){ if(InpObservabilityLogOnTick){ WriteNoTradeObservability(); } }\n"
            "void OnDeinit(const int reason){ WriteNoTradeObservability(); }\n"
            "void WriteNoTradeObservability(){ logger.NoTradeObservabilityStatusSnapshot(); logger.NoTradeComponentStatusSnapshot(); logger.LogReadOnlyControllerSummarySnapshot(); logger.LogReadOnlyTelemetryAggregationSnapshot(); signalEngine.GetSignalStatusSnapshot(); riskManager.GetRiskStatusSnapshot(); executionManager.GetExecutionStatusSnapshot(); signalEngine.GetReadOnlySignalContextSnapshot(); riskManager.GetReadOnlyRiskContextSnapshot(); executionManager.GetReadOnlyExecutionContextSnapshot(); }\n"
            "};\n#endif\n"
        ),
    }
    files.update(overrides)
    for rel_path, text in files.items():
        write_text(temp_root / rel_path, text)


def run_static_interface_validator(temp_root):
    return subprocess.run(
        [
            sys.executable,
            str(temp_root / "tools" / "validate_project_state_docs.py"),
            "--mq5-static-interface-consistency",
        ],
        cwd=str(temp_root),
        capture_output=True,
        text=True,
    )


def positive_test_mq5_static_interface_consistency_fixture():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        write_static_interface_fixture(temp_root)
        result = run_static_interface_validator(temp_root)
        if result.returncode != 0:
            return f"static interface fixture should pass\n{result.stdout}\n{result.stderr}"
        if "MQ5 static interface consistency validation passed" not in result.stdout:
            return f"static interface PASS output missing\n{result.stdout}"
        return ""


def negative_test_mq5_static_interface_missing_logger_helper():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        write_static_interface_fixture(
            temp_root,
            {
                "mq5/logger/Logger.mqh": (
                    "#ifndef LOGGER_MQH\n#define LOGGER_MQH\n"
                    "class Logger { public: bool Init(){ return true; } };\n#endif\n"
                )
            },
        )
        return expect_static_interface_failed(
            run_static_interface_validator(temp_root),
            "missing static interface logger helper was not detected",
        )


def negative_test_mq5_static_interface_module_mismatch():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        write_static_interface_fixture(
            temp_root,
            {
                "mq5/core/EaController.mqh": (
                    "#ifndef EA_CONTROLLER_MQH\n#define EA_CONTROLLER_MQH\n"
                    '#include "../config/InputConfig.mqh"\n'
                    '#include "../logger/Logger.mqh"\n'
                    '#include "../signals/SignalEngine.mqh"\n'
                    '#include "../risk/RiskManager.mqh"\n'
                    '#include "../execution/ExecutionManager.mqh"\n'
                    "class EaController { private: Logger logger; SignalEngine signalEngine; RiskManager riskManager; ExecutionManager executionManager;\n"
                    "public: int OnInit(){ logger.Init(); riskManager.Init(logger); executionManager.Init(logger); return 0; }\n"
                    "void OnTick(){ if(InpObservabilityLogOnTick){ } }\n"
                    "void OnDeinit(const int reason){} };\n#endif\n"
                )
            },
        )
        return expect_static_interface_failed(
            run_static_interface_validator(temp_root),
            "missing static interface module wiring was not detected",
        )


def negative_test_mq5_static_interface_trading_keyword():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        write_static_interface_fixture(
            temp_root,
            {
                "mq5/execution/ExecutionManager.mqh": (
                    "#ifndef EXECUTION_MANAGER_MQH\n#define EXECUTION_MANAGER_MQH\n"
                    '#include "../logger/Logger.mqh"\n'
                    '#include "../signals/SignalEngine.mqh"\n'
                    "class ExecutionManager { public: bool Init(Logger &log){ return true; }\n"
                    'string GetExecutionStatusSnapshot(){ return "execution_status=read-only framework"; }\n'
                    'string GetReadOnlyExecutionContextSnapshot(){ return "execution_context_snapshot=true"; }\n'
                    "void Unsafe(){ OrderSend(); }\n"
                    "};\n#endif\n"
                )
            },
        )
        return expect_static_interface_failed(
            run_static_interface_validator(temp_root),
            "static interface trading keyword was not detected",
        )


def negative_test_task_doc_241_missing_task240_sync_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_sync_text = doc_text().replace(
            "- TASK-240 completed no-trade observability scaffold\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_sync_text,
            handoff_text=missing_sync_text,
            project_text=missing_sync_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-241 TASK-240 sync phrase was not detected",
        )


def negative_test_task_242_missing_contract_validator_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_contract_text = doc_text().replace(
            "- TASK-242 objective is to implement a read-only MQ5 no-trade observability contract validator\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_contract_text,
            handoff_text=missing_contract_text,
            project_text=missing_contract_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-242 no-trade observability contract validator phrase was not detected",
        )


def negative_test_task_243_missing_structured_snapshot_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_snapshot_text = doc_text().replace(
            "- TASK-243 implementation scope is limited to structured no-trade observability status snapshot\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_snapshot_text,
            handoff_text=missing_snapshot_text,
            project_text=missing_snapshot_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-243 structured snapshot phrase was not detected",
        )


def negative_test_task_244_missing_component_snapshot_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_component_text = doc_text().replace(
            "- read-only MQ5 component status snapshot contract records all_components_no_trade=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_component_text,
            handoff_text=missing_component_text,
            project_text=missing_component_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-244 component status snapshot phrase was not detected",
        )


def negative_test_task_245_missing_lifecycle_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_lifecycle_text = doc_text().replace(
            "- no-trade lifecycle telemetry event contract records trading_authorization=false\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_lifecycle_text,
            handoff_text=missing_lifecycle_text,
            project_text=missing_lifecycle_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-245 lifecycle telemetry phrase was not detected",
        )


def negative_test_task_246_missing_runtime_snapshot_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_runtime_text = doc_text().replace(
            "- read-only runtime status snapshot logging records runtime_status_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_runtime_text,
            handoff_text=missing_runtime_text,
            project_text=missing_runtime_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-246 runtime status snapshot phrase was not detected",
        )


def negative_test_task_247_missing_performance_metrics_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_metrics_text = doc_text().replace(
            "- MQ5 no-trade performance metrics contract records runtime_metrics_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_metrics_text,
            handoff_text=missing_metrics_text,
            project_text=missing_metrics_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-247 performance metrics phrase was not detected",
        )


def negative_test_task_248_missing_safety_guard_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_safety_guard_text = doc_text().replace(
            "- no-trade safety guard invariant contract records safety_guard_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_safety_guard_text,
            handoff_text=missing_safety_guard_text,
            project_text=missing_safety_guard_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-248 safety guard invariant phrase was not detected",
        )


def negative_test_task_249_missing_metrics_aggregation_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_aggregation_text = doc_text().replace(
            "- read-only metrics aggregation & historical events contract records metrics_aggregation_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_aggregation_text,
            handoff_text=missing_aggregation_text,
            project_text=missing_aggregation_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-249 metrics aggregation phrase was not detected",
        )


def negative_test_task_250_missing_system_health_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_health_text = doc_text().replace(
            "- read-only system health & observability summary contract records system_health_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_health_text,
            handoff_text=missing_health_text,
            project_text=missing_health_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-250 system health phrase was not detected",
        )


def negative_test_task_251_missing_signal_context_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_signal_context_text = doc_text().replace(
            "- read-only signal context snapshot contract records signal_context_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_signal_context_text,
            handoff_text=missing_signal_context_text,
            project_text=missing_signal_context_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-251 signal context phrase was not detected",
        )


def negative_test_task_252_missing_risk_context_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_risk_context_text = doc_text().replace(
            "- read-only risk context snapshot contract records risk_context_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_risk_context_text,
            handoff_text=missing_risk_context_text,
            project_text=missing_risk_context_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-252 risk context phrase was not detected",
        )


def negative_test_task_253_missing_execution_context_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_execution_context_text = doc_text().replace(
            "- read-only execution context snapshot contract records execution_context_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_execution_context_text,
            handoff_text=missing_execution_context_text,
            project_text=missing_execution_context_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-253 execution context phrase was not detected",
        )


def negative_test_task_doc_254_missing_sync_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_sync_text = doc_text().replace(
            "- read-only execution context snapshot contract is synced to project state docs\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_sync_text,
            handoff_text=missing_sync_text,
            project_text=missing_sync_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-254 sync phrase was not detected",
        )


def negative_test_task_255_missing_pipeline_context_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_pipeline_text = doc_text().replace(
            "- read-only pipeline context aggregation snapshot contract records pipeline_context_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_pipeline_text,
            handoff_text=missing_pipeline_text,
            project_text=missing_pipeline_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-255 pipeline context phrase was not detected",
        )


def negative_test_task_doc_256_missing_task_255_completion_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_sync_text = doc_text().replace(
            "- TASK-255 completed read-only pipeline context aggregation snapshot contract\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_sync_text,
            handoff_text=missing_sync_text,
            project_text=missing_sync_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-256 TASK-255 completion phrase was not detected",
        )


def negative_test_task_doc_256_missing_v057_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_tag_text = doc_text().replace(
            "- TASK-255 tag is v0.5.57-task-255-read-only-pipeline-context\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_tag_text,
            handoff_text=missing_tag_text,
            project_text=missing_tag_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-256 v0.5.57 tag phrase was not detected",
        )


def negative_test_task_doc_256_missing_inventory_no_mt5_no_trading_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_state_text = doc_text().replace(
            "- TASK-DOC-256 confirms MQ5 inventory remains 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-DOC-256 confirms no MT5 run\n",
            "",
            1,
        ).replace(
            "- TASK-DOC-256 confirms no trading authorization\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_state_text,
            handoff_text=missing_state_text,
            project_text=missing_state_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-DOC-256 inventory/no-MT5/no-trading phrase was not detected",
        )


def negative_test_task_257_missing_authorization_matrix_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_auth_text = doc_text().replace(
            "- read-only authorization matrix snapshot contract records authorization_matrix_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_auth_text,
            handoff_text=missing_auth_text,
            project_text=missing_auth_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-257 authorization matrix phrase was not detected",
        )


def negative_test_task_257_missing_v058_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_tag_text = doc_text().replace(
            "- TASK-DOC-256 tag is v0.5.58-task-256-sync-task-255-state\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_tag_text,
            handoff_text=missing_tag_text,
            project_text=missing_tag_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-257 v0.5.58 tag phrase was not detected",
        )


def negative_test_task_257_missing_inventory_no_mt5_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_state_text = doc_text().replace(
            "- MQ5 inventory must remain 7 files\n",
            "",
            1,
        ).replace(
            "- TASK-257 does not run MT5\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_state_text,
            handoff_text=missing_state_text,
            project_text=missing_state_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-257 inventory/no-MT5 phrase was not detected",
        )


def negative_test_task_258_missing_decision_gate_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_decision_text = doc_text().replace(
            "- read-only decision gate snapshot contract records decision_gate_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_decision_text,
            handoff_text=missing_decision_text,
            project_text=missing_decision_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-258 decision gate phrase was not detected",
        )


def negative_test_task_258_missing_v059_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_tag_text = doc_text().replace(
            "- TASK-257 tag is v0.5.59-task-257-read-only-authorization-matrix\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_tag_text,
            handoff_text=missing_tag_text,
            project_text=missing_tag_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-258 v0.5.59 tag phrase was not detected",
        )


def negative_test_task_258_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_state_text = doc_text().replace(
            "- TASK-258 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-258 does not create manifest / fixture / report / directory\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_state_text,
            handoff_text=missing_state_text,
            project_text=missing_state_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-258 no-MT5/no-output phrase was not detected",
        )


def negative_test_task_259_missing_rejection_reason_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_rejection_text = doc_text().replace(
            "- read-only decision rejection reason snapshot contract records decision_rejection_snapshot=true\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_rejection_text,
            handoff_text=missing_rejection_text,
            project_text=missing_rejection_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-259 decision rejection phrase was not detected",
        )


def negative_test_task_259_missing_v060_tag_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_tag_text = doc_text().replace(
            "- TASK-258 tag is v0.5.60-task-258-read-only-decision-gate\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_tag_text,
            handoff_text=missing_tag_text,
            project_text=missing_tag_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-259 v0.5.60 tag phrase was not detected",
        )


def negative_test_task_259_missing_no_mt5_no_output_phrase():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        missing_state_text = doc_text().replace(
            "- TASK-259 does not run MT5\n",
            "",
            1,
        ).replace(
            "- TASK-259 does not create manifest / fixture / report / directory\n",
            "",
            1,
        )
        build_temp_project(
            temp_root,
            current_text=missing_state_text,
            handoff_text=missing_state_text,
            project_text=missing_state_text,
        )
        return expect_validation_failed(
            run_validator(temp_root),
            "missing TASK-259 no-MT5/no-output phrase was not detected",
        )


def negative_test_root_duplicate():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        build_temp_project(temp_root)
        write_text(temp_root / "CURRENT_TASK.md", "temporary duplicate\n")
        return expect_validation_failed(
            run_validator(temp_root),
            "root duplicate was not detected",
        )


def negative_test_missing_safety_keyword():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        project_text = doc_text().replace(
            "v0.3.0 still forbids real trading",
            "",
            1,
        )
        build_temp_project(temp_root, project_text=project_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "missing safety keyword was not detected",
        )


def negative_test_commit_mismatch():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        project_text = doc_text(
            current_commit="abc1234 TASK-DOC-088 update state after TASK-TAG-005"
        )
        build_temp_project(temp_root, project_text=project_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "current latest commit mismatch was not detected",
        )


def negative_test_functional_task_mismatch():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        project_text = doc_text(
            functional_task="abc1234 TASK-999 unexpected functional task"
        )
        build_temp_project(temp_root, project_text=project_text)
        return expect_validation_failed(
            run_validator(temp_root),
            "current latest functional task mismatch was not detected",
        )


def main():
    checks = [
        ensure_prerequisites,
        positive_test_current_project,
        positive_test_v050_current_phase_fixture,
        positive_test_task_doc_077_update_state_commit_allowed,
        positive_test_task_doc_role_boundary_fixture,
        positive_test_dynamic_next_boundary_output,
        negative_test_current_task_mojibake_detected,
        negative_test_handoff_mojibake_detected,
        negative_test_project_state_mojibake_detected,
        negative_test_boundary_mismatch,
        negative_test_missing_real_trading_boundary,
        negative_test_missing_handoff_role_boundary,
        negative_test_missing_project_state_role_boundary,
        negative_test_missing_v060_first_low_risk_plan_doc,
        negative_test_v060_first_low_risk_plan_missing_safety_phrase,
        negative_test_missing_task238_no_trade_scaffold_boundary_doc,
        negative_test_task238_boundary_missing_safety_phrase,
        negative_test_missing_task239_first_implementation_slice_boundary_doc,
        negative_test_task239_boundary_missing_safety_phrase,
        negative_test_missing_task260_observability_extension_plan_doc,
        negative_test_task260_plan_missing_planning_only_phrase,
        negative_test_task260_plan_missing_future_no_trade_phrase,
        negative_test_task260_plan_missing_no_mt5_no_trading_phrase,
        negative_test_task260_plan_missing_task261_boundary_phrase,
        negative_test_missing_task261_observability_extension_next_plan_doc,
        negative_test_task261_plan_missing_planning_only_phrase,
        negative_test_task261_plan_missing_future_no_trade_phrase,
        negative_test_task261_plan_missing_no_mt5_no_trading_phrase,
        negative_test_task261_plan_missing_task262_boundary_phrase,
        negative_test_task261_plan_missing_inventory_phrase,
        negative_test_task261_plan_missing_trading_keyword_phrase,
        negative_test_missing_task262_observability_extension_followup_plan_doc,
        negative_test_task262_plan_missing_planning_only_phrase,
        negative_test_task262_plan_missing_future_no_trade_phrase,
        negative_test_task262_plan_missing_no_mt5_no_trading_phrase,
        negative_test_task262_plan_missing_task263_boundary_phrase,
        negative_test_task262_plan_missing_inventory_phrase,
        negative_test_task262_plan_missing_trading_keyword_phrase,
        negative_test_missing_task263_observability_extension_future_plan_doc,
        negative_test_task263_plan_missing_planning_only_phrase,
        negative_test_task263_plan_missing_future_no_trade_phrase,
        negative_test_task263_plan_missing_no_mt5_no_trading_phrase,
        negative_test_task263_plan_missing_task264_boundary_phrase,
        negative_test_task263_plan_missing_inventory_phrase,
        negative_test_task263_plan_missing_trading_keyword_phrase,
        negative_test_task264_missing_current_task_phrase,
        negative_test_task264_missing_latest_tag_phrase,
        negative_test_task264_missing_no_planning_chain_phrase,
        negative_test_task264_missing_inventory_trading_keyword_phrase,
        negative_test_task264_missing_no_mt5_no_output_phrase,
        negative_test_task265_missing_current_task_phrase,
        negative_test_task265_missing_latest_tag_phrase,
        negative_test_task265_missing_no_new_planning_packet_phrase,
        negative_test_task265_missing_inventory_trading_keyword_phrase,
        negative_test_task265_missing_no_mt5_no_output_phrase,
        negative_test_task266_missing_current_task_phrase,
        negative_test_task266_missing_fast_profile_phrase,
        negative_test_task266_missing_no_mt5_no_trading_phrase,
        negative_test_task266_missing_no_mq5_phrase,
        negative_test_task266_missing_inventory_trading_keyword_phrase,
        negative_test_task267_missing_current_task_phrase,
        negative_test_task267_missing_runner_name_phrase,
        negative_test_task267_missing_doc_only_strict_phrase,
        negative_test_task267_missing_no_mt5_no_trading_phrase,
        negative_test_task268_missing_current_task_phrase,
        negative_test_task268_missing_allowed_change_guard_phrase,
        negative_test_task268_missing_allowed_change_parameters,
        negative_test_task268_missing_no_mt5_no_trading_phrase,
        negative_test_task_269_missing_error_snapshot_phrase,
        negative_test_task_269_missing_v070_tag_phrase,
        negative_test_task_269_missing_no_mt5_no_output_phrase,
        negative_test_task_270_missing_current_task_phrase,
        negative_test_task_270_missing_allow_preset_phrase,
        negative_test_task_270_missing_one_preset_phrase,
        negative_test_task_270_missing_no_mt5_no_trading_phrase,
        negative_test_task_271_missing_current_task_phrase,
        negative_test_task_271_missing_telemetry_field_phrase,
        negative_test_task_271_missing_latest_tag_phrase,
        negative_test_task_271_missing_no_mt5_no_output_phrase,
        negative_test_task_272_missing_current_task_phrase,
        negative_test_task_272_missing_controller_summary_field_phrase,
        negative_test_task_272_missing_helper_gate_phrase,
        negative_test_task_272_missing_no_mt5_no_output_phrase,
        negative_test_task_273_missing_current_task_phrase,
        negative_test_task_273_missing_review_summary_phrase,
        negative_test_task_273_missing_suggested_git_add_phrase,
        negative_test_task_273_missing_latest_tag_phrase,
        negative_test_task_273_missing_no_mt5_no_output_phrase,
        negative_test_task_274_missing_current_task_phrase,
        negative_test_task_274_missing_emit_trae_command_phrase,
        negative_test_task_274_missing_preview_parameter_phrases,
        negative_test_task_274_missing_latest_tag_phrase,
        negative_test_task_274_missing_no_mt5_no_trading_phrase,
        negative_test_task_275_missing_current_task_phrase,
        negative_test_task_275_missing_workflow_preset_phrase,
        negative_test_task_275_missing_one_preset_phrase,
        negative_test_task_275_missing_no_mt5_no_trading_phrase,
        negative_test_task_276_missing_current_task_phrase,
        negative_test_task_276_missing_state_report_support_phrase,
        negative_test_task_276_missing_state_report_field_phrases,
        negative_test_task_276_missing_state_report_safety_phrases,
        negative_test_task_276_missing_no_mt5_no_trading_phrase,
        negative_test_task_277_missing_current_task_phrase,
        negative_test_task_277_missing_emit_trae_handoff_phrase,
        negative_test_task_277_missing_handoff_marker_phrase,
        negative_test_task_277_missing_handoff_block_start_phrase,
        negative_test_task_277_missing_send_to_trae_phrase,
        negative_test_task_277_missing_no_mt5_no_trading_phrase,
        negative_test_task_278_missing_current_task_phrase,
        negative_test_task_278_missing_compact_report_parameter_phrase,
        negative_test_task_278_missing_compact_report_field_phrases,
        negative_test_task_278_missing_trae_review_phrases,
        negative_test_task_278_missing_no_mt5_inventory_phrase,
        negative_test_task_279_missing_current_task_phrase,
        negative_test_task_279_missing_compressed_summary_parameter_phrase,
        negative_test_task_279_missing_compressed_summary_field_phrases,
        negative_test_task_279_missing_trae_review_phrases,
        negative_test_task_279_missing_no_mt5_inventory_phrase,
        negative_test_task_280_missing_current_task_phrase,
        negative_test_task_280_missing_workflow_closure_parameter_phrase,
        negative_test_task_280_missing_closure_audit_field_phrases,
        negative_test_task_280_missing_trae_validator_summary_phrases,
        negative_test_task_280_missing_no_mt5_inventory_phrase,
        negative_test_task_doc_281_missing_task280_completion_phrase,
        negative_test_task_doc_281_missing_v080_tag_phrase,
        negative_test_task_doc_281_missing_workflow_closure_phrase,
        negative_test_task_doc_281_missing_no_mt5_no_trading_phrase,
        negative_test_task_doc_281_missing_inventory_phrase,
        negative_test_task_282_missing_boundary_phrase,
        negative_test_task_282_missing_compile_readiness_phrase,
        negative_test_task_282_missing_bundle_check_phrase,
        negative_test_task_282_missing_no_mt5_no_trading_phrase,
        negative_test_task_282_missing_inventory_phrase,
        negative_test_task_283_missing_current_task_phrase,
        negative_test_task_283_missing_static_interface_phrase,
        negative_test_task_283_missing_bundle_check_phrase,
        negative_test_task_283_missing_no_mt5_inventory_phrase,
        negative_test_task_284_missing_current_task_phrase,
        negative_test_task_284_missing_include_check_phrase,
        negative_test_task_284_missing_no_mt5_compile_trading_phrase,
        negative_test_task_284_missing_inventory_trading_keywords_phrase,
        negative_test_task_285_missing_current_task_phrase,
        negative_test_task_285_missing_duplicate_output_reduction_phrase,
        negative_test_task_285_missing_no_mt5_compile_trading_phrase,
        negative_test_task_285_missing_inventory_trading_keywords_phrase,
        negative_test_task_286_missing_current_task_phrase,
        negative_test_task_286_missing_lifecycle_check_phrase,
        negative_test_task_286_missing_lifecycle_route_phrase,
        negative_test_task_286_missing_no_mt5_compile_trading_phrase,
        negative_test_task_286_missing_inventory_trading_keywords_phrase,
        negative_test_task_287_missing_current_task_phrase,
        negative_test_task_287_missing_helper_check_phrase,
        negative_test_task_287_missing_logger_helper_consistency_phrase,
        negative_test_task_287_missing_no_mt5_compile_trading_phrase,
        negative_test_task_287_missing_inventory_trading_keywords_phrase,
        negative_test_task_288_missing_current_task_phrase,
        negative_test_task_288_missing_telemetry_check_phrase,
        negative_test_task_288_missing_telemetry_summary_phrase,
        negative_test_task_288_missing_no_mt5_compile_trading_phrase,
        negative_test_task_288_missing_inventory_trading_keywords_phrase,
        negative_test_task_289_missing_current_task_phrase,
        negative_test_task_289_missing_helper_file_phrase,
        negative_test_task_289_missing_v087_tag_phrase,
        negative_test_task_289_missing_no_mt5_compile_trading_phrase,
        negative_test_task_289_missing_inventory_trading_keywords_phrase,
        negative_test_task_289_missing_tag_reconciliation_phrase,
        negative_test_task_290_missing_current_task_phrase,
        negative_test_task_290_missing_final_milestone_parameter_phrase,
        negative_test_task_290_missing_closure_summary_phrases,
        negative_test_task_290_missing_trae_validator_summary_phrases,
        negative_test_task_290_missing_no_mt5_compile_trading_phrase,
        negative_test_task_290_missing_inventory_trading_keywords_phrase,
        negative_test_task_291_missing_current_task_phrase,
        negative_test_task_291_missing_check_id_phrase,
        negative_test_task_291_missing_symbol_and_compile_flags,
        negative_test_task_291_missing_no_mt5_compile_trading_phrase,
        negative_test_task_291_missing_inventory_trading_keywords_phrase,
        negative_test_task_292_missing_current_task_phrase,
        negative_test_task_292_missing_check_id_phrase,
        negative_test_task_292_missing_compile_flags,
        negative_test_task_292_missing_no_mt5_compile_trading_phrase,
        negative_test_task_292_missing_inventory_trading_keywords_phrase,
        negative_test_task_293_missing_current_task_phrase,
        negative_test_task_293_missing_summary_check_phrase,
        negative_test_task_293_missing_final_summary_fields,
        negative_test_task_293_missing_no_mt5_compile_trading_phrase,
        negative_test_task_293_missing_inventory_trading_keywords_phrase,
        negative_test_task_doc_294_missing_plan_doc,
        negative_test_task_doc_294_missing_current_task_phrase,
        negative_test_task_doc_294_missing_planning_only_phrase,
        negative_test_task_doc_294_missing_no_compile_no_metaeditor_phrase,
        negative_test_task_doc_294_missing_no_mt5_no_trading_phrase,
        negative_test_task_doc_294_missing_task295_boundary_phrase,
        negative_test_task_doc_294_missing_inventory_trading_keywords_phrase,
        negative_test_task_295_missing_current_task_phrase,
        negative_test_task_295_missing_command_discovery_phrase,
        negative_test_task_295_missing_execution_false_phrases,
        negative_test_task_295_missing_no_compile_boundary_phrases,
        negative_test_task_295_missing_no_trading_phrase,
        negative_test_task_295_missing_task296_boundary_phrase,
        negative_test_task_295_missing_inventory_trading_keywords_phrase,
        negative_test_task_296_missing_plan_doc,
        negative_test_task_296_missing_current_task_phrase,
        negative_test_task_296_missing_artifact_quarantine_phrase,
        negative_test_task_296_missing_repo_artifact_flags,
        negative_test_task_296_missing_task297_boundary_phrase,
        negative_test_task_296_missing_inventory_trading_keywords_phrase,
        negative_test_task_297_missing_plan_doc,
        negative_test_task_297_missing_current_task_phrase,
        negative_test_task_297_missing_execution_boundary_phrase,
        negative_test_task_297_missing_no_compile_no_artifact_phrases,
        negative_test_task_297_missing_task298_boundary_phrase,
        negative_test_task_297_missing_inventory_trading_keywords_phrase,
        negative_test_task_298_missing_plan_doc,
        negative_test_task_298_missing_current_task_phrase,
        negative_test_task_298_missing_dryrun_phrase,
        negative_test_task_298_missing_no_compile_no_output_phrases,
        negative_test_task_298_missing_task299_boundary_phrase,
        negative_test_task_298_missing_inventory_trading_keywords_phrase,
        negative_test_task_299_missing_current_task_phrase,
        negative_test_task_299_missing_task297_file_phrase,
        negative_test_task_299_missing_v096_tag_phrase,
        negative_test_task_299_missing_no_mt5_no_compile_no_trading_phrase,
        negative_test_task_299_missing_inventory_trading_keywords_phrase,
        negative_test_task_300_missing_plan_doc,
        negative_test_task_300_missing_current_task_phrase,
        negative_test_task_300_missing_dryrun_execution_phrase,
        negative_test_task_300_missing_no_compile_no_output_phrases,
        negative_test_task_300_missing_task301_boundary_phrase,
        negative_test_task_300_missing_inventory_trading_keywords_phrase,
        negative_test_task_301_missing_plan_doc,
        negative_test_task_301_missing_current_task_phrase,
        negative_test_task_301_missing_planning_future_phrase,
        negative_test_task_301_missing_no_mt5_no_compile_no_output_phrase,
        negative_test_task_301_missing_task302_boundary_phrase,
        negative_test_task_301_missing_inventory_trading_keywords_phrase,
        negative_test_task_302_missing_plan_doc,
        negative_test_task_302_missing_current_task_phrase,
        negative_test_task_302_missing_preflight_gate_phrase,
        negative_test_task_302_missing_repo_artifact_flags,
        negative_test_task_302_missing_execution_false_flags,
        negative_test_task_302_missing_no_mt5_no_compile_no_artifact_phrase,
        negative_test_task_302_missing_no_trading_authorization_phrase,
        negative_test_task_302_missing_task303_boundary_phrase,
        negative_test_task_302_missing_inventory_trading_keywords_phrase,
        negative_test_task_303_missing_plan_doc,
        negative_test_task_303_missing_current_task_phrase,
        negative_test_task_303_missing_planning_authorization_phrase,
        negative_test_task_303_missing_bundle_check_phrase,
        negative_test_task_303_missing_execution_authorization_false_flags,
        negative_test_task_303_missing_no_mt5_no_compile_no_artifact_phrase,
        negative_test_task_303_missing_no_trading_authorization_phrase,
        negative_test_task_303_missing_task304_boundary_phrase,
        negative_test_task_303_missing_inventory_trading_keywords_phrase,
        negative_test_task_305_missing_plan_doc,
        negative_test_task_305_missing_current_task_phrase,
        negative_test_task_305_missing_diagnostic_capture_phrase,
        negative_test_task_305_missing_no_artifact_no_mt5_phrase,
        negative_test_task_305_missing_task306_boundary_phrase,
        positive_test_task_306_complete_classification_fixture,
        negative_test_task_306_missing_plan_doc,
        negative_test_task_306_missing_current_task_phrase,
        negative_test_task_306_missing_classification_phrase,
        negative_test_task_306_missing_compile_log_semantic_phrase,
        negative_test_task_306_missing_success_false_phrase,
        negative_test_task_306_missing_no_execution_no_artifact_phrase,
        negative_test_task_306_missing_task307_boundary_phrase,
        positive_test_task_307_complete_artifact_classification_fixture,
        negative_test_task_307_missing_plan_doc,
        negative_test_task_307_missing_artifact_classification_phrase,
        negative_test_task_307_missing_no_repo_artifact_phrase,
        negative_test_task_307_missing_task308_boundary_phrase,
        positive_test_task_308_complete_artifact_proof_boundary_fixture,
        negative_test_task_308_missing_plan_doc,
        negative_test_task_308_missing_diagnostic_proof_boundary_phrase,
        negative_test_task_308_missing_proof_check_name_phrase,
        negative_test_task_308_missing_previous_classification_phrase,
        negative_test_task_308_missing_future_task309_boundary_phrase,
        negative_test_task_308_missing_no_mt5_no_compile_no_artifact_phrase,
        positive_test_task_309_complete_success_reclassification_boundary_fixture,
        negative_test_task_309_missing_plan_doc,
        negative_test_task_309_missing_success_boundary_phrase,
        negative_test_task_309_missing_check_name_phrase,
        negative_test_task_309_missing_previous_classification_phrase,
        negative_test_task_309_missing_future_task310_boundary_phrase,
        negative_test_task_309_missing_no_mt5_no_compile_no_artifact_phrase,
        positive_test_task_310_complete_artifact_hash_capture_fixture,
        negative_test_task_310_missing_plan_doc,
        negative_test_task_310_missing_check_name_phrase,
        negative_test_task_310_missing_stdout_only_phrase,
        negative_test_task_310_missing_no_success_reclassification_phrase,
        negative_test_task_310_missing_future_task311_boundary_phrase,
        positive_test_task_311_complete_success_reclassification_decision_boundary_fixture,
        negative_test_task_311_missing_plan_doc,
        negative_test_task_311_missing_decision_boundary_phrase,
        negative_test_task_311_missing_check_name_phrase,
        negative_test_task_311_missing_previous_classification_phrase,
        negative_test_task_311_missing_artifact_hash_stdout_only_phrase,
        negative_test_task_311_missing_future_task312_boundary_phrase,
        negative_test_task_311_missing_no_mt5_no_compile_no_artifact_phrase,
        positive_test_task_312_complete_success_reclassification_decision_fixture,
        negative_test_task_312_missing_decision_doc,
        negative_test_task_312_missing_pass_decision_phrase,
        negative_test_task_312_missing_compile_scope_phrase,
        negative_test_task_312_missing_no_readiness_phrase,
        negative_test_task_312_missing_hash_stdout_only_phrase,
        negative_test_task_312_missing_future_task313_boundary_phrase,
        positive_test_task_313_complete_mt5_no_trade_startup_boundary_fixture,
        negative_test_task_313_missing_plan_doc,
        negative_test_task_313_missing_startup_boundary_phrase,
        negative_test_task_313_missing_check_name_phrase,
        negative_test_task_313_missing_task312_compile_only_scope_phrase,
        negative_test_task_313_missing_future_task314_boundary_phrase,
        negative_test_task_313_missing_no_mt5_strategy_tester_no_trading_phrase,
        positive_test_task_314_complete_mt5_no_trade_startup_command_discovery_fixture,
        negative_test_task_314_missing_plan_doc,
        negative_test_task_314_missing_command_discovery_phrase,
        negative_test_task_314_missing_check_name_phrase,
        negative_test_task_314_missing_task312_compile_only_scope_phrase,
        negative_test_task_314_missing_future_task315_boundary_phrase,
        negative_test_task_314_missing_no_mt5_terminal_strategy_tester_no_trading_phrase,
        positive_test_task_315_complete_mt5_no_trade_startup_quarantine_preparation_fixture,
        negative_test_task_315_missing_plan_doc,
        negative_test_task_315_missing_quarantine_preparation_phrase,
        negative_test_task_315_missing_check_name_phrase,
        negative_test_task_315_missing_task312_compile_only_scope_phrase,
        negative_test_task_315_missing_future_task316_boundary_phrase,
        negative_test_task_315_missing_no_terminal_data_startup_log_no_mt5_phrase,
        positive_test_task_316_complete_mt5_no_trade_startup_dryrun_config_boundary_fixture,
        negative_test_task_316_missing_plan_doc,
        negative_test_task_316_missing_dryrun_config_boundary_phrase,
        negative_test_task_316_missing_check_name_phrase,
        negative_test_task_316_missing_task312_compile_only_scope_phrase,
        negative_test_task_316_missing_future_task317_boundary_phrase,
        negative_test_task_316_missing_no_config_terminal_data_startup_log_no_mt5_phrase,
        positive_test_task_317_complete_mt5_no_trade_startup_config_template_fixture,
        negative_test_task_317_missing_plan_doc,
        negative_test_task_317_missing_stdout_template_phrase,
        negative_test_task_317_missing_check_name_phrase,
        negative_test_task_317_missing_no_config_no_mt5_phrase,
        negative_test_task_317_missing_future_task318_boundary_phrase,
        negative_test_task_317_missing_template_field_phrase,
        positive_test_task_318_complete_mt5_no_trade_startup_authorization_plan_fixture,
        negative_test_task_318_missing_plan_doc,
        negative_test_task_318_missing_planning_boundary_phrase,
        negative_test_task_318_missing_check_name_phrase,
        negative_test_task_318_missing_future_task319_boundary_phrase,
        negative_test_task_318_missing_no_mt5_compile_artifact_phrase,
        positive_test_task_319_complete_mt5_no_trade_startup_preflight_gate_fixture,
        negative_test_task_319_missing_plan_doc,
        negative_test_task_319_missing_preflight_gate_phrase,
        negative_test_task_319_missing_check_name_phrase,
        negative_test_task_319_missing_no_mt5_terminal_trading_phrase,
        negative_test_task_319_missing_future_task320_boundary_phrase,
        negative_test_task_319_missing_future_startup_condition_phrase,
        positive_test_mq5_static_interface_consistency_fixture,
        negative_test_mq5_static_interface_missing_logger_helper,
        negative_test_mq5_static_interface_module_mismatch,
        negative_test_mq5_static_interface_trading_keyword,
        negative_test_task_doc_241_missing_task240_sync_phrase,
        negative_test_task_242_missing_contract_validator_phrase,
        negative_test_task_243_missing_structured_snapshot_phrase,
        negative_test_task_244_missing_component_snapshot_phrase,
        negative_test_task_245_missing_lifecycle_phrase,
        negative_test_task_246_missing_runtime_snapshot_phrase,
        negative_test_task_247_missing_performance_metrics_phrase,
        negative_test_task_248_missing_safety_guard_phrase,
        negative_test_task_249_missing_metrics_aggregation_phrase,
        negative_test_task_250_missing_system_health_phrase,
        negative_test_task_251_missing_signal_context_phrase,
        negative_test_task_252_missing_risk_context_phrase,
        negative_test_task_253_missing_execution_context_phrase,
        negative_test_task_doc_254_missing_sync_phrase,
        negative_test_task_255_missing_pipeline_context_phrase,
        negative_test_task_doc_256_missing_task_255_completion_phrase,
        negative_test_task_doc_256_missing_v057_tag_phrase,
        negative_test_task_doc_256_missing_inventory_no_mt5_no_trading_phrase,
        negative_test_task_257_missing_authorization_matrix_phrase,
        negative_test_task_257_missing_v058_tag_phrase,
        negative_test_task_257_missing_inventory_no_mt5_phrase,
        negative_test_task_258_missing_decision_gate_phrase,
        negative_test_task_258_missing_v059_tag_phrase,
        negative_test_task_258_missing_no_mt5_no_output_phrase,
        negative_test_task_259_missing_rejection_reason_phrase,
        negative_test_task_259_missing_v060_tag_phrase,
        negative_test_task_259_missing_no_mt5_no_output_phrase,
        negative_test_root_duplicate,
        negative_test_missing_safety_keyword,
        negative_test_commit_mismatch,
        negative_test_functional_task_mismatch,
    ]

    for check in checks:
        error = check()
        if error:
            return fail(error)

    print("Project state docs self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
