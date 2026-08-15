#!/usr/bin/env python3
"""Validate consistency and readability of the current project state docs."""

from pathlib import Path
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]

DOC_PATHS = {
    "docs/CURRENT_TASK.md": ROOT_DIR / "docs" / "CURRENT_TASK.md",
    "docs/HANDOFF_PROMPT.md": ROOT_DIR / "docs" / "HANDOFF_PROMPT.md",
    "docs/PROJECT_STATE.md": ROOT_DIR / "docs" / "PROJECT_STATE.md",
}

PLAN_DOC_PATH = ROOT_DIR / "docs" / "V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md"
TASK238_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_238_NO_TRADE_SCAFFOLD_BOUNDARY.md"
)
TASK239_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_239_FIRST_IMPLEMENTATION_SLICE_BOUNDARY.md"
)
TASK260_OBSERVABILITY_EXTENSION_PLAN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md"
)
TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_261_OBSERVABILITY_EXTENSION_NEXT_PLAN.md"
)
TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN.md"
)
TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_263_OBSERVABILITY_EXTENSION_FUTURE_PLAN.md"
)
TASK294_MQL5_COMPILE_ONLY_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md"
)
TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md"
)
TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md"
)
TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md"
)
TASK298_MQL5_COMPILE_ONLY_DRYRUN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md"
)
TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md"
)
TASK301_V060_COMPILE_READINESS_PLANNING_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md"
)
TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md"
)
TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md"
)
TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md"
)
TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION.md"
)
TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md"
)
TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md"
)
TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md"
)
TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md"
)
TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_DOC_PATH = (
    ROOT_DIR
    / "docs"
    / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
)
TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
)
TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
)
TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
)
TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"
)
TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md"
)
TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md"
)
TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN.md"
)
TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE.md"
)
TASK321_PARSER_PIPELINE_INTEGRATION_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md"
)
MQ5_ROOT = ROOT_DIR / "mq5"

MQ5_STATIC_INTERFACE_EXPECTED_FILES = {
    "TradingSystem.mq5",
    "config/InputConfig.mqh",
    "core/EaController.mqh",
    "logger/Logger.mqh",
    "risk/RiskManager.mqh",
    "execution/ExecutionManager.mqh",
    "signals/SignalEngine.mqh",
}

MQ5_STATIC_INTERFACE_REQUIRED_KEYWORDS = {
    "TradingSystem.mq5": [
        '#include "core/EaController.mqh"',
        "EaController controller",
        "controller.OnInit()",
        "controller.OnTick()",
        "controller.OnDeinit(reason)",
    ],
    "config/InputConfig.mqh": [
        "input bool InpEnableTrading = false",
        "input bool InpEnableNoTradeObservability",
        "input bool InpObservabilityLogOnTick = false",
    ],
    "core/EaController.mqh": [
        '#include "../config/InputConfig.mqh"',
        '#include "../logger/Logger.mqh"',
        '#include "../signals/SignalEngine.mqh"',
        '#include "../risk/RiskManager.mqh"',
        '#include "../execution/ExecutionManager.mqh"',
        "Logger logger",
        "SignalEngine signalEngine",
        "RiskManager riskManager",
        "ExecutionManager executionManager",
        "logger.Init()",
        "signalEngine.Init(logger)",
        "riskManager.Init(logger)",
        "executionManager.Init(logger)",
        "void OnTick()",
        "InpObservabilityLogOnTick",
        "void OnDeinit(const int reason)",
        "WriteNoTradeObservability",
        "signalEngine.GetSignalStatusSnapshot()",
        "riskManager.GetRiskStatusSnapshot()",
        "executionManager.GetExecutionStatusSnapshot()",
        "signalEngine.GetReadOnlySignalContextSnapshot()",
        "riskManager.GetReadOnlyRiskContextSnapshot()",
        "executionManager.GetReadOnlyExecutionContextSnapshot()",
    ],
    "logger/Logger.mqh": [
        "class Logger",
        "bool Init()",
        "NoTradeObservabilityStatusSnapshot",
        "NoTradeComponentStatusSnapshot",
        "LogReadOnlyControllerSummarySnapshot",
        "LogReadOnlyTelemetryAggregationSnapshot",
        "Inventory only; no MT5 run; no trading authorization.",
    ],
    "signals/SignalEngine.mqh": [
        "class SignalEngine",
        "bool Init(Logger &log)",
        "GetSignalStatusSnapshot",
        "GetReadOnlySignalContextSnapshot",
    ],
    "risk/RiskManager.mqh": [
        "class RiskManager",
        "bool Init(Logger &log)",
        "GetRiskStatusSnapshot",
        "GetReadOnlyRiskContextSnapshot",
    ],
    "execution/ExecutionManager.mqh": [
        "class ExecutionManager",
        "bool Init(Logger &log)",
        "GetExecutionStatusSnapshot",
        "GetReadOnlyExecutionContextSnapshot",
    ],
}

MQ5_STATIC_INTERFACE_FORBIDDEN_KEYWORDS = [
    "Buy",
    "Sell",
    "OrderSend",
    "PositionOpen",
    "CTrade",
]

PLAN_DOC_REQUIRED_KEYWORDS = [
    "V060 First Low-Risk Implementation Plan",
    "planning-only",
    "not implementation authorization",
    "no MQ5 modification",
    "no MT5 run",
    "no trading authorization",
    "TASK-238 v0.6.0 no-trade observability scaffold",
    "Buy / Sell / OrderSend / PositionOpen / CTrade",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK238_BOUNDARY_REQUIRED_KEYWORDS = [
    "planning-only",
    "no-trade scaffold",
    "future candidate",
    "TASK-238",
    "Buy / Sell / OrderSend / PositionOpen / CTrade 均 false",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK239_BOUNDARY_REQUIRED_KEYWORDS = [
    "first authorized low-risk implementation slice",
    "planning + boundary only",
    "InpEnableTrading false",
    "Buy / Sell / OrderSend / PositionOpen / CTrade",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK260_OBSERVABILITY_EXTENSION_PLAN_REQUIRED_KEYWORDS = [
    "V060 TASK-260 First Observability Extension Plan",
    "planning-only",
    "future candidate",
    "no-trade observability extension",
    "not implementation authorization",
    "no MQ5 modification",
    "no MT5 run",
    "no trading authorization",
    "TASK-261",
    "6451e78",
    "v0.5.61-task-259-read-only-decision-rejection-reason",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade",
    "Inventory only; no MT5 run; no trading authorization.",
    "must not be entered directly",
    "GPT must define",
]

TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_REQUIRED_KEYWORDS = [
    "V060 TASK-261 Observability Extension Next Plan",
    "planning-only",
    "future candidate",
    "no-trade observability extension",
    "no-trade scaffold",
    "not implementation authorization",
    "no MQ5 modification",
    "no MT5 run",
    "no trading authorization",
    "TASK-262",
    "cb7675f",
    "v0.5.62-task-260-first-observability-extension-plan",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade",
    "Inventory only; no MT5 run; no trading authorization.",
    "TASK-262 must not be entered directly",
    "GPT must define a separate future boundary before TASK-262",
]

TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_REQUIRED_KEYWORDS = [
    "V060 TASK-262 Observability Extension Follow-up Plan",
    "planning-only",
    "future candidate",
    "no-trade observability extension",
    "no-trade scaffold",
    "not implementation authorization",
    "no MQ5 modification",
    "no MT5 run",
    "no trading authorization",
    "TASK-263",
    "527486d",
    "v0.5.63-task-261-observability-extension-next-plan",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade",
    "Inventory only; no MT5 run; no trading authorization.",
    "TASK-263 must not be entered directly",
    "GPT must define a separate future boundary before TASK-263",
]

TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_REQUIRED_KEYWORDS = [
    "V060 TASK-263 Observability Extension Future Plan",
    "planning-only",
    "future candidate",
    "no-trade observability extension",
    "no-trade scaffold",
    "not implementation authorization",
    "no MQ5 modification",
    "no MT5 run",
    "no trading authorization",
    "TASK-264",
    "69f12a6",
    "v0.5.64-task-262-observability-extension-followup-plan",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade",
    "Inventory only; no MT5 run; no trading authorization.",
    "TASK-264 must not be entered directly",
    "GPT must define a separate future boundary before TASK-264",
]

TASK294_MQL5_COMPILE_ONLY_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-DOC-294 future MQL5 compile-only boundary packet",
    "planning-only / boundary-only",
    "future MQL5 compile-only candidate",
    "not implementation authorization",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not evidence generation authorization",
    "not manifest generation authorization",
    "not external evidence copy authorization",
    "no compile executed in TASK-DOC-294",
    "no MetaEditor executed in TASK-DOC-294",
    "no .ex5 artifact generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report",
    "current tag: v0.5.92-task-293-mq5-compile-readiness-final-summary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future compile-only task must be separately authorized by GPT",
    "future compile-only task must remain no-trade",
    "future compile-only task must not create manifest / evidence / report",
    "future compile-only task must only produce stdout / terminal result unless separately authorized",
    "TASK-295 must not be entered directly without a new GPT boundary",
    "allowed action: invoke compile-only command only if explicitly authorized later",
    "forbidden action: MT5 terminal run",
    "forbidden action: Strategy Tester",
    "forbidden action: backtest",
    "forbidden action: simulation / real trading",
    "forbidden action: copying external evidence",
    "forbidden action: creating official manifest",
    "forbidden action: modifying mq5 trading behavior",
]

TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_REQUIRED_KEYWORDS = [
    "TASK-295 MQL5 compile-only command discovery boundary",
    "command-discovery-only",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MQL5 compile executed in TASK-295",
    "no MetaEditor executed in TASK-295",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet",
    "current tag: v0.5.93-task-294-future-mql5-compile-only-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-296 must be separately authorized by GPT before any compile execution",
    "TASK-296 must not be entered directly",
    "future compile-only task must remain no-trade",
    "future compile-only task must not create manifest / evidence / report unless separately authorized",
    "future compile-only task must quarantine or prevent .ex5 artifact generation before compile execution is allowed",
]

TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_REQUIRED_KEYWORDS = [
    "TASK-296 MQL5 compile-only artifact quarantine boundary",
    "artifact-quarantine-only",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MQL5 compile executed in TASK-296",
    "no MetaEditor executed in TASK-296",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: acda17c TASK-295 implement MQL5 compile-only command discovery boundary",
    "current tag: v0.5.94-task-295-mql5-compile-only-command-discovery",
    "MetaEditor candidate discovered in TASK-295",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-297 must be separately authorized by GPT before any compile execution",
    "TASK-297 must not be entered directly",
    "future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes",
    "future compile-only execution must check repository has no .ex5 before and after compile",
    "future compile-only execution must check repository has no compile log before and after compile",
    "future compile-only execution must not create official manifest / evidence / report",
    "future compile-only execution must remain no-trade",
    "pre-compile check: no .ex5 in repository",
    "pre-compile check: no compile log in repository",
    "pre-compile check: MQ5 inventory 7 files",
    "pre-compile check: trading keywords false",
    "compile-only command may be executed only after GPT defines TASK-297 boundary",
    "post-compile check: no .ex5 in repository unless separately authorized",
    "post-compile check: no compile log in repository unless separately authorized",
    "post-compile check: no MT5 run",
    "post-compile check: no Strategy Tester",
    "post-compile check: no trading",
]

TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-297 MQL5 compile-only execution boundary",
    "compile-only-task",
    "future compile-only candidate",
    "requires GPT explicit authorization",
    "artifact quarantine checked",
    "no MT5 run",
    "no Strategy Tester",
    "no backtest",
    "no trading",
    "no MQL5 compile executed",
    "no MetaEditor executed",
    "no .ex5 artifact generated",
    "no compile log",
    "no manifest generated",
    "no evidence generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "current tag: v0.5.95-task-296-mql5-compile-only-artifact-quarantine",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-298 must be separately authorized by GPT",
    "future TASK-298 must not be entered directly",
]

TASK298_MQL5_COMPILE_ONLY_DRYRUN_REQUIRED_KEYWORDS = [
    "TASK-298 MQL5 compile-only dry-run simulation",
    "dry-run-only",
    "artifact-quarantine enforced",
    "future compile-only task must be separately authorized by GPT",
    "stdout-only simulation",
    "current HEAD: 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "current tag: v0.5.95-task-296-mql5-compile-only-artifact-quarantine",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-299 must not be entered directly",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_REQUIRED_KEYWORDS = [
    "TASK-300 MQL5 compile-only dry-run execution simulation",
    "dry-run-execution-only",
    "artifact-quarantine enforced",
    "future compile-only task must be separately authorized by GPT",
    "stdout-only simulation",
    "current HEAD: 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary",
    "current tag: v0.5.96-task-298-mql5-compile-only-dryrun",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-301 must not be entered directly",
    "future compile-only execution must remain no-trade",
    "future compile-only execution must not create manifest / evidence / report unless separately authorized",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK301_V060_COMPILE_READINESS_PLANNING_REQUIRED_KEYWORDS = [
    "TASK-301 v0.6.0 compile-readiness planning packet",
    "planning-only",
    "future compile-readiness candidate",
    "not implementation authorization",
    "not MT5 run",
    "not Strategy Tester run",
    "not backtest authorization",
    "not simulation / real trading authorization",
    "not evidence / manifest / report creation",
    "current HEAD: fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation",
    "current tag: v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation",
    "MQ5 inventory 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade false",
    "TASK-302 must not be entered directly without GPT authorization",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_REQUIRED_KEYWORDS = [
    "TASK-302 MQL5 compile-only execution preflight gate",
    "preflight-gate-only",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MQL5 compile executed in TASK-302",
    "no MetaEditor executed in TASK-302",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 2f0498b TASK-301 create v060 compile-readiness planning packet",
    "current tag: v0.5.98-task-301-v060-compile-readiness-planning",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "all previous compile-only boundary checks must pass before future compile execution",
    "artifact quarantine must pass before future compile execution",
    "future compile-only command must remain stdout-only unless GPT separately authorizes artifact handling",
    "future TASK-303 must be separately authorized by GPT before any compile execution",
    "TASK-303 must not be entered directly",
    "preflight check: mql5-compile-only-boundary PASS",
    "preflight check: mql5-compile-only-command-discovery PASS",
    "preflight check: mql5-compile-only-artifact-quarantine PASS",
    "preflight check: mql5-compile-only-execution-boundary PASS",
    "preflight check: mql5-compile-only-dryrun PASS",
    "preflight check: mql5-compile-only-dryrun-execution PASS",
    "preflight check: v060-compile-readiness-planning PASS",
    "preflight check: MQ5 inventory 7 files",
    "preflight check: trading keywords false",
    "preflight check: repo_ex5_artifacts=false",
    "preflight check: repo_compile_logs=false",
    "post-compile requirement: no MT5 run",
    "post-compile requirement: no Strategy Tester",
    "post-compile requirement: no trading",
    "post-compile requirement: no manifest/evidence/report unless separately authorized",
]

TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_REQUIRED_KEYWORDS = [
    "TASK-303 v0.6.0 compile-only execution authorization planning packet",
    "planning-only",
    "authorization-boundary-only",
    "future compile-only execution candidate",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not manifest generation authorization",
    "not evidence generation authorization",
    "not report generation authorization",
    "no MQL5 compile executed in TASK-303",
    "no MetaEditor executed in TASK-303",
    "no MT5 run in TASK-303",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 15c675e TASK-302 implement MQL5 compile-only execution preflight gate",
    "current tag: v0.5.99-task-302-mql5-compile-only-preflight-gate",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-304 must not be entered directly",
    "future TASK-304 must be separately authorized by GPT before any compile execution",
    "compile-only execution authorization requires all preflight gates PASS",
    "compile-only execution authorization must remain no-trade",
    "compile-only execution authorization must not run MT5 terminal",
    "compile-only execution authorization must not run Strategy Tester",
    "compile-only execution authorization must not create official manifest",
    "compile-only execution authorization must not copy external evidence",
    "compile-only execution authorization must include pre/post repo artifact checks",
    "compile-only execution authorization must check repo_ex5_artifacts=false before execution",
    "compile-only execution authorization must check repo_compile_logs=false before execution",
    "compile-only execution authorization must check trading_keywords=false before execution",
    "compile-only execution authorization must check MQ5 inventory remains 7 files before execution",
    "mql5-compile-only-boundary PASS",
    "mql5-compile-only-command-discovery PASS",
    "mql5-compile-only-artifact-quarantine PASS",
    "mql5-compile-only-execution-boundary PASS",
    "mql5-compile-only-dryrun PASS",
    "mql5-compile-only-dryrun-execution PASS",
    "mql5-compile-only-preflight-gate PASS",
    "v060-compile-readiness-planning PASS",
    "mq5-static-compile-readiness PASS",
    "mq5-compile-readiness-final-summary PASS",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "future GPT boundary explicitly says compile execution is allowed",
]

TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_REQUIRED_KEYWORDS = [
    "TASK-305 MQL5 compile-only failure diagnostic capture",
    "diagnostic-only",
    "not compile success",
    "not TASK-304 success result",
    "compile_exit_code=1 was observed in TASK-304",
    "TASK-305 may re-run MetaEditor compile-only only against quarantine copy",
    "compile log must be stdout-only",
    "compile log must not be saved to repository",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no MT5 terminal run",
    "no Strategy Tester run",
    "no backtest",
    "no trading",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet",
    "current tag: v0.5.100-task-303-v060-compile-only-execution-authorization",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Inventory only; no MT5 run; no trading authorization.",
    "TASK-306 must not be entered directly",
    "future TASK-306 must be separately authorized by GPT before any MQ5 fixes or compile retry",
]

TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_REQUIRED_KEYWORDS = [
    "TASK-306 MQL5 compile-only diagnostic result classification",
    "diagnostic-classification-only",
    "not compile execution",
    "not MetaEditor execution in TASK-306",
    "not MT5 run",
    "not Strategy Tester",
    "not backtest",
    "not trading",
    "compile_exit_code=1 observed in TASK-305",
    "Result: 0 errors, 0 warnings",
    "compile_result_classification=metaeditor_exit_code_anomaly",
    "compile_log_semantic_success=true",
    "compile_success=false",
    "task304_success_result_created=false",
    "followup_required=true",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture",
    "current tag: v0.5.101-task-305-mql5-compile-only-failure-diagnostic",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Inventory only; no MT5 run; no trading authorization.",
    "TASK-307 must not be entered directly",
    "future TASK-307 must be separately authorized by GPT before any compile retry or MQ5 fix",
]

TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_REQUIRED_KEYWORDS = [
    "TASK-307 MQL5 compile diagnostic artifact classification",
    "diagnostic-artifact-classification-only",
    "not TASK-304 success result",
    "not MT5 run",
    "not Strategy Tester",
    "not backtest",
    "not trading",
    "TASK-307 may re-run MetaEditor compile-only only against quarantine copy",
    "quarantine artifact inspection before cleanup",
    "quarantine .ex5 must not be copied to repository",
    "compile log must remain stdout-only",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "task304_success_result_created=false",
    "compile_success=false unless a future GPT boundary explicitly reclassifies success",
    "current HEAD: 560079c TASK-306 implement MQL5 compile-only diagnostic result classification",
    "current tag: v0.5.102-task-306-mql5-compile-diagnostic-classification",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Inventory only; no MT5 run; no trading authorization.",
    "TASK-308 must not be entered directly",
    "future TASK-308 must be separately authorized by GPT before any compile retry or MQ5 fix",
]

TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-308 MQL5 compile diagnostic artifact proof and success reclassification boundary",
    "planning-only",
    "diagnostic-proof-boundary-only",
    "not compile execution",
    "not MetaEditor execution in TASK-308",
    "not MT5 run",
    "not Strategy Tester",
    "not backtest",
    "not trading",
    "not success reclassification in TASK-308",
    "TASK-307 observed quarantine_ex5_artifact_detected=true",
    "TASK-307 observed compile_log_semantic_success=true",
    "TASK-307 observed compile_exit_code=1",
    "TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
    "TASK-307 compile_success=false",
    "TASK-307 task304_success_result_created=false",
    "TASK-308 does not create TASK-304 success result doc",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification",
    "current tag: v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification",
    "TASK-309 must not be entered directly",
    "future GPT boundary explicitly authorizes success reclassification attempt",
    "future task may re-run MetaEditor compile-only only against quarantine copy",
    "future task must capture quarantine .ex5 metadata before deletion",
    "future task must output artifact metadata to stdout only",
    "future task must not copy .ex5 into repository",
    "future task must not save compile log into repository",
    "future task must compute quarantine artifact hash before deleting quarantine directory",
    "future task must output quarantine artifact size",
    "future task must output quarantine artifact path as temporary path only",
    "future task must delete quarantine directory before completion",
    "future task must prove repo_ex5_artifacts=false after cleanup",
    "future task must prove repo_compile_logs=false after cleanup",
    "future task must prove repo_mq5_modified=false after cleanup",
    "future task must prove trading_keywords=false after cleanup",
    "future task must prove MQ5 inventory remains 7 files",
    "future task must still not run MT5 terminal",
    "future task must still not run Strategy Tester",
    "future task must still not trade",
    "future task must not create official manifest / evidence / report unless separately authorized",
]

TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-309 MQL5 compile-only success reclassification boundary",
    "planning-only",
    "success-reclassification-boundary-only",
    "not compile execution",
    "not MetaEditor execution in TASK-309",
    "not MT5 run",
    "not Strategy Tester",
    "not backtest",
    "not trading",
    "not success reclassification in TASK-309",
    "TASK-307 observed quarantine_ex5_artifact_detected=true",
    "TASK-307 observed quarantine_ex5_artifact_count=1",
    "TASK-307 observed compile_log_semantic_success=true",
    "TASK-307 observed compile_exit_code=1",
    "TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
    "TASK-307 compile_success=false",
    "TASK-307 task304_success_result_created=false",
    "TASK-308 defined diagnostic artifact proof boundary",
    "TASK-309 does not create TASK-304 success result doc",
    "TASK-309 does not reclassify compile success",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "Inventory only; no MT5 run; no trading authorization.",
    "current HEAD: 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary",
    "current tag: v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix",
    "TASK-310 must not be entered directly",
    "future GPT boundary explicitly authorizes success reclassification attempt",
    "future task may re-run MetaEditor compile-only only against quarantine copy",
    "future task must capture quarantine .ex5 metadata before deletion",
    "future task must compute quarantine artifact hash before deleting quarantine directory",
    "future task must output quarantine artifact hash to stdout only",
    "future task must output quarantine artifact size",
    "future task must output quarantine artifact temporary path only",
    "future task must not copy .ex5 into repository",
    "future task must not save compile log into repository",
    "future task must capture compile log semantic result to stdout only",
    "future task must prove compile_log_semantic_success=true",
    "future task must prove compile_log_errors=0",
    "future task must prove quarantine_ex5_artifact_detected=true",
    "future task must prove quarantine_ex5_artifact_count>=1",
    "future task must delete quarantine directory before completion",
    "future task must prove quarantine_deleted=true",
    "future task must prove repo_ex5_artifacts=false after cleanup",
    "future task must prove repo_compile_logs=false after cleanup",
    "future task must prove repo_mq5_modified=false after cleanup",
    "future task must prove trading_keywords=false after cleanup",
    "future task must prove MQ5 inventory remains 7 files",
    "future task must not run MT5 terminal",
    "future task must not run Strategy Tester",
    "future task must not backtest",
    "future task must not trade",
    "future task must not create official manifest",
    "future task must not create evidence",
    "future task must not create report",
    "future task must not copy external evidence",
    "future success reclassification must remain compile-only and no-trade",
    "future success reclassification must not imply deployment readiness",
    "future success reclassification must not imply strategy readiness",
    "future success reclassification must not imply backtest readiness",
    "future success reclassification must not imply trading authorization",
]

TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_REQUIRED_KEYWORDS = [
    "TASK-310 MQL5 compile artifact hash capture diagnostic",
    "artifact-hash-capture-diagnostic-only",
    "not success reclassification",
    "not TASK-304 success result",
    "TASK-310 may re-run MetaEditor compile-only only against quarantine copy",
    "artifact hash must be stdout-only",
    "artifact hash must not be saved to repository",
    "quarantine .ex5 must not be copied to repository",
    "compile log must remain stdout-only",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "success_reclassification_done=false",
    "task304_success_result_created=false",
    "compile_success=false",
    "future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix",
    "TASK-311 must not be entered directly",
    "no MT5 terminal run",
    "no Strategy Tester run",
    "no backtest",
    "no trading",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: f31b85e TASK-309 create MQL5 compile-only success reclassification boundary",
    "current tag: v0.5.105-task-309-mql5-compile-success-reclassification-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-311 MQL5 compile success reclassification decision boundary",
    "planning-only",
    "success-reclassification-decision-boundary-only",
    "not compile execution",
    "not MetaEditor execution in TASK-311",
    "not success reclassification in TASK-311",
    "TASK-310 observed artifact_hash_captured=true",
    "TASK-310 observed quarantine_ex5_artifact_size_bytes=70178",
    "TASK-310 observed compile_exit_code=1",
    "TASK-310 observed compile_log_semantic_success=true",
    "TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly",
    "TASK-310 compile_success=false",
    "TASK-310 success_reclassification_done=false",
    "TASK-310 task304_success_result_created=false",
    "TASK-310 artifact hash was stdout-only and must not be stored in repository",
    "TASK-311 does not store artifact hash",
    "TASK-311 does not create TASK-304 success result doc",
    "current HEAD: 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic",
    "current tag: v0.5.106-task-310-mql5-compile-artifact-hash-capture",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry",
    "TASK-312 must not be entered directly",
    "future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash",
    "future success reclassification must remain compile-only and no-trade",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_REQUIRED_KEYWORDS = [
    "TASK-312 MQL5 compile-only success reclassification decision",
    "controlled-success-reclassification-attempt",
    "success_reclassification_decision=PASS",
    "compile_only_reclassified_success=true",
    "compile_success=true",
    "compile_success_scope=compile-only-diagnostic",
    "not trading authorization",
    "not deployment readiness",
    "not backtest readiness",
    "not strategy readiness",
    "MetaEditor executed only against quarantine copy",
    "MQL5 compile executed only against quarantine copy",
    "MT5 terminal run=false",
    "Strategy Tester run=false",
    "trading_executed=false",
    "quarantine_ex5_artifact_detected=true",
    "quarantine_ex5_artifact_count>=1",
    "artifact_hash_captured=true",
    "artifact_hash_stdout_only=true",
    "artifact_hash_saved_to_repo=false",
    "do not include actual artifact hash value in this doc",
    "quarantine_ex5_artifact_size_bytes captured",
    "quarantine_deleted=true",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary",
    "current tag: v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-313 must be separately authorized by GPT before any MT5 run, Strategy Tester, backtest, deployment, or trading-related step",
    "TASK-313 must not be entered directly",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-313 MT5 terminal no-trade startup boundary packet",
    "planning-only",
    "mt5-startup-boundary-only",
    "future MT5 terminal no-trade startup candidate",
    "not MT5 run in TASK-313",
    "not terminal64.exe execution in TASK-313",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "not evidence generation authorization",
    "not manifest generation authorization",
    "not report generation authorization",
    "no MT5 terminal run executed in TASK-313",
    "no Strategy Tester executed in TASK-313",
    "no backtest executed in TASK-313",
    "no trading executed in TASK-313",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision",
    "current tag: v0.5.108-task-312-mql5-compile-success-reclassification-decision",
    "TASK-312 compile_success=true was compile-only-diagnostic scope only",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-314 must not be entered directly",
    "future GPT boundary explicitly authorizes MT5 terminal no-trade startup",
    "future task must remain no-trade",
    "future task must not run Strategy Tester",
    "future task must not run backtest",
    "future task must not run simulation trading",
    "future task must not run real trading",
    "future task must not place orders",
    "future task must not create official manifest unless separately authorized",
    "future task must not create evidence unless separately authorized",
    "future task must not create report unless separately authorized",
    "future task must use a no-trade config",
    "future task must prove InpEnableTrading=false before startup",
    "future task must prove trading keywords false before startup",
    "future task must prove MQ5 inventory remains 7 files before startup",
    "future task must prove repo_ex5_artifacts=false before startup",
    "future task must prove repo_compile_logs=false before startup",
    "future task must prove repo_mq5_modified=false before startup",
    "future task must capture terminal startup result stdout-only unless separately authorized",
    "future task must not copy external evidence",
    "future task must not imply deployment readiness",
    "future task must not imply strategy readiness",
    "future task must not imply backtest readiness",
    "future task must not imply trading authorization",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_REQUIRED_KEYWORDS = [
    "TASK-314 MT5 no-trade startup command discovery boundary",
    "command-discovery-only",
    "mt5-startup-preparation-only",
    "not MT5 run in TASK-314",
    "not terminal64.exe execution in TASK-314",
    "not terminal.exe execution in TASK-314",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-314",
    "no Strategy Tester executed in TASK-314",
    "no backtest executed in TASK-314",
    "no trading executed in TASK-314",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet",
    "current tag: v0.5.109-task-313-mt5-no-trade-startup-boundary",
    "TASK-312 compile_success=true was compile-only-diagnostic scope only",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-315 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-315 must not be entered directly",
    "future GPT boundary explicitly authorizes MT5 terminal no-trade startup",
    "future startup must remain no-trade",
    "future startup must not run Strategy Tester",
    "future startup must not run backtest",
    "future startup must not run simulation trading",
    "future startup must not run real trading",
    "future startup must not place orders",
    "future startup must use no-trade startup template",
    "future startup must prove InpEnableTrading=false before startup",
    "future startup must prove trading keywords false before startup",
    "future startup must prove MQ5 inventory remains 7 files before startup",
    "future startup must prove repo_ex5_artifacts=false before startup",
    "future startup must prove repo_compile_logs=false before startup",
    "future startup must prove repo_mq5_modified=false before startup",
    "future startup must capture startup result stdout-only unless separately authorized",
    "future startup must not copy external evidence",
    "future startup must not imply deployment readiness",
    "future startup must not imply strategy readiness",
    "future startup must not imply backtest readiness",
    "future startup must not imply trading authorization",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_REQUIRED_KEYWORDS = [
    "TASK-315 MT5 no-trade startup quarantine preparation boundary",
    "planning-only",
    "startup-quarantine-preparation-only",
    "not MT5 run in TASK-315",
    "not terminal64.exe execution in TASK-315",
    "not terminal.exe execution in TASK-315",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-315",
    "no terminal64.exe executed in TASK-315",
    "no terminal.exe executed in TASK-315",
    "no Strategy Tester executed in TASK-315",
    "no backtest executed in TASK-315",
    "no trading executed in TASK-315",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "current HEAD: ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary",
    "current tag: v0.5.110-task-314-mt5-no-trade-startup-command-discovery",
    "TASK-314 discovered MT5 terminal candidate",
    "TASK-314 future_startup_command_executed=false",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-316 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-316 must not be entered directly",
    "future startup must use an isolated startup quarantine outside repository",
    "future startup must not use repository as terminal data directory",
    "future startup must not write terminal logs into repository",
    "future startup must prove InpEnableTrading=false before startup",
    "future startup must prove no terminal data directory exists in repository before startup",
    "future startup must prove no startup log exists in repository before startup",
    "future startup must not imply trading authorization",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-316 MT5 no-trade startup dry-run config boundary",
    "planning-only",
    "startup-dryrun-config-boundary-only",
    "not MT5 run in TASK-316",
    "not terminal64.exe execution in TASK-316",
    "not terminal.exe execution in TASK-316",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-316",
    "no terminal64.exe executed in TASK-316",
    "no terminal.exe executed in TASK-316",
    "no Strategy Tester executed in TASK-316",
    "no backtest executed in TASK-316",
    "no trading executed in TASK-316",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "no no-trade config file generated in repository",
    "current HEAD: 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary",
    "current tag: v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation",
    "TASK-314 discovered MT5 terminal candidate",
    "TASK-315 defined startup quarantine preparation",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-317 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-317 must not be entered directly",
    "future startup must use no-trade config",
    "future startup must prove InpEnableTrading=false before startup",
    "future startup must not run Strategy Tester",
    "future startup must not place orders",
    "future startup must not imply trading authorization",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_REQUIRED_KEYWORDS = [
    "TASK-317 MT5 no-trade startup config template preview",
    "stdout-only-config-template-preview",
    "no config file generated in TASK-317",
    "not MT5 run in TASK-317",
    "not terminal64.exe execution in TASK-317",
    "not terminal.exe execution in TASK-317",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-317",
    "no terminal64.exe executed in TASK-317",
    "no terminal.exe executed in TASK-317",
    "no Strategy Tester executed in TASK-317",
    "no backtest executed in TASK-317",
    "no trading executed in TASK-317",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "no no-trade config file generated in repository",
    "current HEAD: a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary",
    "current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
    "TASK-314 discovered MT5 terminal candidate",
    "TASK-315 defined startup quarantine preparation",
    "TASK-316 defined dry-run config boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5",
    "TASK-318 must not be entered directly",
    "future terminal path placeholder",
    "future quarantine data path placeholder outside repository",
    "future no-trade config template",
    "InpEnableTrading=false",
    "no Strategy Tester",
    "no backtest",
    "no trading",
    "no official manifest",
    "stdout-only startup result unless separately authorized",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_REQUIRED_KEYWORDS = [
    "TASK-318 MT5 no-trade startup authorization planning boundary",
    "planning-only",
    "authorization-boundary-only",
    "mt5-no-trade-startup-authorization-plan",
    "not MT5 run in TASK-318",
    "not terminal64.exe execution in TASK-318",
    "not terminal.exe execution in TASK-318",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not MetaEditor execution in TASK-318",
    "not MQL5 compile in TASK-318",
    "no MT5 terminal run executed in TASK-318",
    "no terminal64.exe executed in TASK-318",
    "no terminal.exe executed in TASK-318",
    "no Strategy Tester executed in TASK-318",
    "no backtest executed in TASK-318",
    "no trading executed in TASK-318",
    "no MetaEditor executed in TASK-318",
    "no MQL5 compile executed in TASK-318",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "no generated no-trade startup config in repository",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "current HEAD: a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview",
    "current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
    "TASK-317 defined stdout-only config template preview",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-319 must be separately authorized by GPT",
    "TASK-319 must not be entered directly",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK321_PARSER_PIPELINE_INTEGRATION_REQUIRED_KEYWORDS = [
    "TASK-321 parser pipeline integration",
    "parser-pipeline-integration-only",
    "parser-manifest-integration",
    "not MT5 run in TASK-321",
    "not terminal64.exe execution in TASK-321",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MT5 terminal run executed in TASK-321",
    "no manifest generated in repository during TASK-321",
    "no external evidence copied into repository",
    "TASK-319 completed",
    "TASK-319 completion commit is 5f0a697 TASK-319 implement MT5 no-trade startup preflight gate",
    "TASK-319 completion tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate",
    "future TASK-320 requires GPT boundary before any MT5 terminal startup attempt",
    "TASK-320 must not be entered directly",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK321_PARSER_PIPELINE_INTEGRATION_REQUIRED_KEYWORDS = [
    "TASK-321 parser pipeline integration",
    "parser-pipeline-integration-only",
    "parser-manifest-integration",
    "not MT5 run in TASK-321",
    "not terminal64.exe execution in TASK-321",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MT5 terminal run executed in TASK-321",
    "no manifest generated in repository during TASK-321",
    "no external evidence copied into repository",
    "TASK-319 completed",
    "TASK-319 completion commit is 5f0a697 TASK-319 implement MT5 no-trade startup preflight gate",
    "TASK-319 completion tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate",
    "future TASK-320 requires GPT boundary before any MT5 terminal startup attempt",
    "TASK-320 must not be entered directly",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Inventory only; no MT5 run; no trading authorization.",
]

TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_REQUIRED_KEYWORDS = [
    "TASK-319 MT5 no-trade startup preflight gate",
    "planning-only",
    "startup-preflight-gate-only",
    "mt5-no-trade-startup-preflight-gate",
    "not MT5 run in TASK-319",
    "not terminal64.exe execution in TASK-319",
    "not terminal.exe execution in TASK-319",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-319",
    "no terminal64.exe executed in TASK-319",
    "no terminal.exe executed in TASK-319",
    "no Strategy Tester executed in TASK-319",
    "no backtest executed in TASK-319",
    "no trading executed in TASK-319",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "no no-trade config file generated in repository",
    "current HEAD: 718c7cf TASK-317-318 implement MT5 no-trade startup config template and authorization boundaries",
    "current tag: v0.5.113-task-317-318-mt5-no-trade-startup-config-auth-boundaries",
    "TASK-314 discovered MT5 terminal candidate",
    "TASK-315 defined startup quarantine preparation",
    "TASK-316 defined dry-run config boundary",
    "TASK-317 defined stdout-only no-trade config template",
    "TASK-318 defined startup authorization plan",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-320 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-320 must not be entered directly",
    "future startup must use no-trade config",
    "future startup must prove InpEnableTrading=false before startup",
    "future startup must not run Strategy Tester",
    "future startup must not place orders",
    "Inventory only; no MT5 run; no trading authorization.",
]

ROOT_DUPLICATE_PATHS = {
    "CURRENT_TASK.md": ROOT_DIR / "CURRENT_TASK.md",
    "HANDOFF_PROMPT.md": ROOT_DIR / "HANDOFF_PROMPT.md",
}

COMMON_REQUIRED_KEYWORDS = [
    "80e162b TASK-085 add ExecutionManager explicit no-trade guard",
    "951bfe2 TASK-072 verify v0.2.0 Python tool safety coverage",
    "v0.2.2-execution-manager-no-trade-guard",
    "1c93d1b TASK-DOC-087 update state after TASK-086",
    "v0.2.1-mq5-safety-guardrails",
    "a808d8e TASK-DOC-084 update state after TASK-084",
    "v0.2.0-runtime-parser-input-samples",
    "e35a13b TASK-DOC-073 update state after TASK-072",
    "v0.1.9-runtime-report-quality",
    "v0.1.8-engineering-toolchain-stable",
    "v0.1.7-core-signal-log-throttle",
    "TASK-087 completed",
    "define v0.3.0 MQ5 backtest validation boundary",
    "v0.3.0 boundary defined as MQ5 backtest validation and no-trade execution-chain validation stage",
    "v0.3.0 allowed scope is MQ5 backtest entry audit",
    "v0.3.0 allowed scope is Strategy Tester / backtest run evidence recording",
    "v0.3.0 allowed scope is no-trade execution-chain validation",
    "v0.3.0 allowed scope is InpEnableTrading=false behavior validation",
    "v0.3.0 allowed scope is RiskManager / ExecutionManager rejection-path validation",
    "v0.3.0 allowed scope is backtest logs, reports, and sample-quality enhancement",
    "v0.3.0 does not represent live trading",
    "v0.3.0 does not represent real trading readiness",
    "v0.3.0 does not represent a completed profitable strategy",
    "v0.3.0 only allows no-trade backtest validation and evidence collection",
    "v0.3.0 still forbids real trading",
    "v0.3.0 still forbids CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify / PositionClose / OrderClose",
    "v0.3.0 still forbids ATR / position sizing / stop loss / take profit",
    "v0.3.0 still forbids AI / multi-symbol / multi-account",
    "v0.3.0 still forbids Martingale / grid / averaging-down",
    "v0.3.0 still forbids profit optimization",
    "v0.4.0：回测证据归档、报告解析与可复现性增强阶段",
    "TASK-097 completed",
    "define v0.4.0 backtest evidence archive and report parser quality boundary",
    "v0.3.0 phase closure audit completed",
    "v0.4.0 allowed scope: backtest evidence archive planning",
    "v0.4.0 allowed scope: Strategy Tester report / log evidence metadata normalization",
    "v0.4.0 allowed scope: report parser quality improvement",
    "v0.4.0 allowed scope: no-trade evidence reproducibility checks",
    "v0.4.0 allowed scope: evidence manifest / report consistency validation",
    "v0.4.0 allowed scope: parsing already generated MT5 reports or logs when explicitly provided",
    "v0.4.0 allowed scope: tool / docs improvements for evidence quality only",
    "v0.4.0 forbids real trading",
    "v0.4.0 forbids live trading readiness claim",
    "v0.4.0 forbids profit optimization",
    "v0.4.0 forbids parameter optimization for profit",
    "v0.4.0 forbids CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify",
    "v0.4.0 forbids ATR / position sizing / stop loss / take profit",
    "v0.4.0 forbids AI / multi-symbol / multi-account",
    "v0.4.0 forbids Martingale / grid / averaging-down",
    "v0.4.0 forbids direct MQ5 modification unless a future ChatGPT task explicitly allows it",
    "v0.4.0 forbids direct backtest/sets modification unless a future ChatGPT task explicitly allows it",
    "v0.4.0 forbids MT5 run unless a future ChatGPT task explicitly allows it",
    "TASK-097 does not add parser implementation",
    "TASK-097 does not create evidence files",
    "TASK-097 does not run MT5",
    "TASK-097 does not modify MQ5",
    "TASK-097 does not modify backtest/sets",
    "TASK-097 does not create tag",
    "v0.5.0：official evidence archive policy and reproducibility boundary",
    "TASK-112 completed",
    "38f1ce2 TASK-112 define v0.5.0 evidence archive policy boundary",
    "TASK-DOC-135 updated project state after TASK-112",
    "current latest engineering / boundary task updated to 38f1ce2 TASK-112 define v0.5.0 evidence archive policy boundary",
    "TASK-109 real external evidence read-only end-to-end manifest validation passed",
    "TASK-109 chain: real external TesterBacktest.html + 日志.txt -> parser outputs -> temporary manifest -> schema validator -> passed",
    "run_engineering_toolchain_checks.py passed, 17/17 PASS after TASK-112",
    "validate_python_tool_safety.py passed, 26 tools after TASK-112",
    "current next boundary remains TASK-118",
    "TASK-114 completed",
    "d432a37 TASK-114 define official manifest storage naming policy",
    "current latest engineering / policy task updated to d432a37 TASK-114 define official manifest storage naming policy",
    "official manifest storage path defined: backtest/reports/manifests/",
    "official manifest naming convention recorded: {taskId}_{evidenceSetId}_manifest.json",
    "metadata-only external evidence reference policy recorded",
    "official manifest creation boundary recorded",
    "reproducibility checklist placeholder recorded",
    "TASK-115 completed",
    "f87ac9c TASK-DOC-140 update state after TASK-TAG-028",
    "current stable tag remains v0.5.2-official-manifest-storage-naming-policy -> b3b30a7",
    "official manifest storage / naming policy coverage audited",
    "storage path backtest/reports/manifests/ is recorded",
    "backtest/reports/manifests/ is defined only and not created",
    "naming convention is recorded: {taskId}_{evidenceSetId}_manifest.json",
    "generate_evidence_manifest.py can generate schemaVersion, taskId, evidenceSetId, externalEvidenceRoot, files[], repositoryState, tags, notes, and safetyAssertions",
    "validate_evidence_manifest_schema.py can validate all required fields",
    "backtest/reports/manifests/ does not exist",
    "current gap: manifestRevision field is documented as a placeholder but generator does not implement it",
    "recommended next candidate: official manifest filename/path validator",
    "TASK-116 completed",
    "229997d TASK-DOC-142 update state after TASK-TAG-029",
    "current stable tag remains v0.5.3-official-manifest-storage-naming-coverage-audit -> e6b579f",
    "final official manifest naming convention is {taskId}_{evidenceSetId}_manifest.json",
    "docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md records {taskId}_{evidenceSetId}_manifest.json",
    "no conflicting format found: {evidenceSetId}_{taskId}_manifest.json",
    "docs are fully consistent on the official manifest naming convention",
    "generate_evidence_manifest.py does not hard-code filename rule",
    "no tool currently enforces {taskId}_{evidenceSetId}_manifest.json",
    "current gap: no official manifest filename/path validator exists",
    "current gap: naming convention is documented only",
    "recommended next candidate: official manifest creation preflight checklist",
    "TASK-118 completed",
    "9f27267 TASK-118 add deterministic local task acceptance reporter",
    "new tool added: tools/task_acceptance_report.ps1",
    "no files modified by TASK-118 outside tools/task_acceptance_report.ps1",
    "no tag moved by TASK-118",
    "no push by TASK-118",
    "no MT5 run by TASK-118",
    "no manifest created by TASK-118",
    "TASK-119 completed",
    "de16dcd TASK-DOC-147 update state after TASK-TAG-031",
    "tools/task_acceptance_report.ps1 coverage audited: PASS, 8/8 checks",
    "no files modified by TASK-119",
    "no tag moved by TASK-119",
    "no push by TASK-119",
    "no MT5 run by TASK-119",
    "no manifest created by TASK-119",
    "current next boundary updated to TASK-120",
    "current next boundary remains TASK-120",
    "TASK-120 completed",
    "10f248f TASK-120 add official manifest filename path validator",
    "new tool added: tools/validate_official_manifest_path_policy.py",
    "new tool added: tools/test_validate_official_manifest_path_policy.py",
    "integrated into run_engineering_toolchain_checks.py",
    "engineering toolchain 19/19 PASS after TASK-120",
    "no files modified by TASK-120 outside tools/",
    "no tag moved by TASK-120",
    "no push by TASK-120",
    "no MT5 run by TASK-120",
    "no manifest created by TASK-120",
    "current next boundary updated to TASK-121",
    "current next boundary remains TASK-121",
    "TASK-121 completed",
    "official manifest path policy validator coverage audit passed",
    "validator covers backtest/reports/manifests/ directory rule",
    "validator covers {taskId}_{evidenceSetId}_manifest.json filename format",
    "validator covers TASK-\\d+ taskId format",
    "validator covers ASCII-safe evidenceSetId",
    "validator rejects spaces in manifest filename",
    "validator rejects Chinese characters in manifest filename",
    "validator rejects absolute paths",
    "validator rejects path traversal",
    "validator rejects non-manifests directory",
    "validator rejects already existing target file",
    "validator self-test passed, 9/9 PASS",
    "engineering toolchain passed, 18/18 PASS",
    "task_acceptance_report.ps1 PASS after TASK-121",
    "current gap: none",
    "current next boundary updated to TASK-122",
    "current next boundary remains TASK-122",
    "TASK-122 completed",
    "official manifest creation preflight boundary audit passed",
    "official manifest storage policy is defined: backtest/reports/manifests/",
    "official manifest naming policy is defined: {taskId}_{evidenceSetId}_manifest.json",
    "official manifest filename/path validator completed",
    "evidence manifest generator completed",
    "evidence manifest schema validator completed",
    "Strategy Tester HTML parser completed",
    "MT5 log no-trade parser completed",
    "task_acceptance_report.ps1 available",
    "backtest/reports/manifests/ still not created",
    "no official manifest exists yet",
    "external evidence has not been copied",
    "MT5 has not been run",
    "suitable for future first official manifest dry-run task definition",
    "current next boundary updated to TASK-123",
    "current next boundary remains TASK-123",
    "TASK-123 completed",
    "b93ecb5 TASK-123 define first official manifest dry-run boundary",
    "TASK-122 / TASK-DOC-155 / TASK-TAG-036 / TASK-DOC-156 / TASK-123 closed loop completed",
    "first official manifest dry-run boundary defined",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "dry-run may generate manifest only in a temporary directory",
    "dry-run must use generate_evidence_manifest.py",
    "dry-run must use validate_evidence_manifest_schema.py",
    "dry-run must use validate_official_manifest_path_policy.py",
    "dry-run must use task_acceptance_report.ps1",
    "dry-run artifacts must be cleaned before task end",
    "dry-run does not represent official archive creation",
    "dry-run does not represent live trading readiness",
    "dry-run does not represent real trading availability",
    "dry-run does not represent profitability",
    "dry-run does not authorize real trading",
    "dry-run does not authorize copying evidence",
    "current next boundary updated to TASK-124",
    "current next boundary remains TASK-124",
    "TASK-124 completed",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "TASK-122 / TASK-DOC-155 / TASK-TAG-036 / TASK-DOC-156 / TASK-123 / TASK-DOC-157 closed loop completed",
    "first official manifest dry-run boundary defined",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-125",
    "current next boundary remains TASK-125",
    "TASK-125 completed",
    "current latest commit updated to a0e6ce7 TASK-DOC-158 update state after TASK-124",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run boundary defined",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-126",
    "current next boundary remains TASK-126",
    "TASK-126 completed",
    "current latest commit remains a0e6ce7 TASK-DOC-158 update state after TASK-124",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run boundary remains effective",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-127",
    "current next boundary remains TASK-127",
    "TASK-127 completed",
    "current latest commit updated to d09e87e TASK-DOC-160 update state after TASK-126",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-128",
    "current next boundary remains TASK-128",
    "TASK-128 completed",
    "current latest commit updated to 5f8a272 TASK-DOC-161 update state after TASK-127",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run boundary remains effective",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-129",
    "current next boundary remains TASK-129",
    "TASK-129 completed",
    "current latest commit updated to e3cfb79 TASK-DOC-162 update state after TASK-128",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-130",
    "current next boundary remains TASK-130",
    "TASK-130 completed",
    "current latest commit updated to f07f3ee TASK-DOC-163 update state after TASK-129",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-131",
    "current next boundary remains TASK-131",
    "TASK-131 completed",
    "current latest commit updated to a1ffd7b TASK-DOC-164 update state after TASK-130",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-132",
    "current next boundary remains TASK-132",
    "TASK-132 completed",
    "current latest commit updated to ea786a2 TASK-DOC-165 update state after TASK-131",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-133",
    "current next boundary remains TASK-133",
    "TASK-133 completed",
    "current latest commit updated to abfbcef TASK-DOC-166 update state after TASK-132",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-134",
    "current next boundary remains TASK-134",
    "TASK-134 completed",
    "current latest commit updated to fdf8643 TASK-DOC-167 update state after TASK-133",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-135",
    "current next boundary remains TASK-135",
    "TASK-135 completed",
    "current latest commit updated to e21ca46 TASK-DOC-168 update state after TASK-134",
    "current stable tag remains v0.5.10-official-manifest-creation-preflight-audit -> 890dfa5",
    "first official manifest dry-run completed",
    "future dry-run must not create official manifest",
    "future dry-run must not create fixture",
    "future dry-run must not create directory",
    "future dry-run must not copy external evidence",
    "future dry-run must not run MT5",
    "current next boundary updated to TASK-136",
    "current next boundary remains TASK-136",
    "TASK-136 completed",
    "first official manifest promotion readiness audit passed",
    "current HEAD is 2176692 TASK-DOC-170 update state after TASK-TAG-037",
    "current stable tag remains v0.5.11-first-official-manifest-dry-run-summary-closure",
    "v0.5.11-first-official-manifest-dry-run-summary-closure points to 29acb6b TASK-DOC-169 update state after TASK-135",
    "first official manifest dry-run closed loop completed",
    "backtest/reports/manifests/ still not created",
    "no official repository manifest exists",
    "official manifest storage policy defined",
    "official manifest naming policy defined",
    "official manifest path validator completed",
    "generator completed",
    "schema validator completed",
    "HTML parser completed",
    "log parser completed",
    "task_acceptance_report.ps1 available",
    "current gap: none",
    "suitable for future first official manifest creation authorization task",
    "current next boundary updated to TASK-137",
    "current next boundary remains TASK-137",
    "TASK-137 completed",
    "commit recorded: 7103cd0 TASK-137 define first official manifest creation authorization boundary",
    "first official manifest creation authorization boundary defined",
    "future creation task must be separately authorized by a future explicit task",
    "TASK-137 did not create official manifest",
    "TASK-137 did not create backtest/reports/manifests/",
    "TASK-137 did not create fixture",
    "TASK-137 did not copy external evidence",
    "TASK-137 did not run MT5",
    "TASK-137 did not enter real trading",
    "TASK-137 did not perform profit optimization",
    "future creation task must use path policy validator",
    "future creation task must use {taskId}_{evidenceSetId}_manifest.json naming convention",
    "future creation task must use backtest/reports/manifests/",
    "future creation task must use generate_evidence_manifest.py",
    "future creation task must use validate_evidence_manifest_schema.py",
    "future creation task must use validate_official_manifest_path_policy.py",
    "future creation task must use task_acceptance_report.ps1",
    "future creation task must record repositoryState",
    "future creation task must record tags",
    "future creation task must record files[] metadata only",
    "future creation task must not copy external evidence",
    "future creation task must not claim live trading readiness / real trading availability / profitability",
    "future creation task must not authorize real trading",
    "v0.5.12 only means promotion readiness audit closed",
    "v0.5.12 does not mean official manifest has been created",
    "no official repository manifest exists",
    "backtest/reports/manifests/ still not created",
    "current stable tag remains v0.5.12-first-official-manifest-promotion-readiness-audit -> 1d3dd4e",
    "current next boundary updated to TASK-138",
    "current next boundary remains TASK-138",
    "TASK-138 completed",
    "first official manifest creation authorization boundary coverage audit passed",
    "current HEAD is a8e5993 TASK-DOC-174 update state after TASK-TAG-039",
    "current stable tag remains v0.5.13-first-official-manifest-creation-authorization-boundary",
    "v0.5.13-first-official-manifest-creation-authorization-boundary points to e869bef TASK-DOC-173 update state after TASK-137",
    "v0.5.12-first-official-manifest-promotion-readiness-audit still points to 1d3dd4e",
    "v0.5.11-first-official-manifest-dry-run-summary-closure still points to 29acb6b",
    "v0.5.10-official-manifest-creation-preflight-audit still points to 890dfa5",
    "TASK-137 / TASK-DOC-173 / TASK-TAG-039 / TASK-DOC-174 / TASK-138 closed loop completed",
    "first official manifest creation authorization boundary coverage satisfied",
    "creation task must use path policy validator",
    "creation task must use {taskId}_{evidenceSetId}_manifest.json naming convention",
    "creation task must use backtest/reports/manifests/",
    "creation task must use generate_evidence_manifest.py",
    "creation task must use validate_evidence_manifest_schema.py",
    "creation task must use validate_official_manifest_path_policy.py",
    "creation task must use task_acceptance_report.ps1",
    "creation task must record repositoryState / tags / metadata-only files[]",
    "creation task must not copy external evidence",
    "creation task must not claim live trading readiness / real trading availability / profitability",
    "creation task must not authorize real trading",
    "current gap: none",
    "suitable for future first official manifest creation implementation task",
    "current next boundary updated to TASK-139",
    "current next boundary remains TASK-139",
    "TASK-139 completed",
    "1a57ed1 TASK-139 create first official evidence manifest",
    "first official repository manifest created",
    "official manifest path: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json",
    "backtest/reports/manifests/ directory created",
    "this manifest is the only authorized manifest created",
    "no other manifest / report created",
    "path policy validator passed with --no-check-overwrite",
    "schema validator passed",
    "engineering toolchain checks passed, 18/18 PASS",
    "noTradeAssertions.passed = true",
    "riskApproved = 0",
    "executionAttempts = 0",
    "totalTrades = 0",
    "totalDeals = 0",
    "buyTrades = 0",
    "sellTrades = 0",
    "InpEnableTrading = false",
    "stable tag recorded as v0.5.14-first-official-manifest-creation-authorization-coverage-audit -> e5f1405",
    "files[] records external evidence metadata only; no evidence copy",
    "safetyAssertions all true",
    "official manifest does not represent live trading readiness",
    "official manifest does not represent real trading availability",
    "official manifest does not represent profitability",
    "official manifest does not authorize real trading",
    "current latest engineering task updated to 1a57ed1 TASK-139 create first official evidence manifest",
    "current next boundary updated to TASK-140",
    "current next boundary remains TASK-140",
    "TASK-140 completed",
    "first official evidence manifest archive closure readiness audit passed",
    "current HEAD is 54e8e6a TASK-DOC-178 update state after TASK-TAG-041",
    "current stable tag is v0.5.15-first-official-evidence-manifest",
    "v0.5.15-first-official-evidence-manifest points to 0a57e91 TASK-DOC-177 update state after TASK-139",
    "v0.5.14-first-official-manifest-creation-authorization-coverage-audit still points to e5f1405",
    "v0.5.13-first-official-manifest-creation-authorization-boundary still points to e869bef",
    "v0.5.12-first-official-manifest-promotion-readiness-audit still points to 1d3dd4e",
    "v0.5.11-first-official-manifest-dry-run-summary-closure still points to 29acb6b",
    "v0.5.10-official-manifest-creation-preflight-audit still points to 890dfa5",
    "official manifest archive closure readiness satisfied",
    "official manifest exists",
    "official manifest is the only manifest",
    "official manifest path is correct: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json",
    "schema validator PASS",
    "path policy validator PASS with --no-check-overwrite",
    "engineering toolchain 18/18 PASS",
    "validate_project_state_docs.py PASS",
    "test_validate_project_state_docs.py PASS",
    "TesterBacktest.html was not copied",
    "日志.txt was not copied",
    "current gap: none",
    "suitable for future v0.5.0 official evidence archive closure audit / tag",
    "current next boundary updated to TASK-141",
    "current next boundary remains TASK-141",
    "TASK-141 completed",
    "v0.5.0 official evidence archive closure readiness audit passed",
    "current HEAD is 0543a09 TASK-DOC-180 update state after TASK-TAG-042",
    "current stable tag is v0.5.16-official-evidence-archive-closure-readiness-audit",
    "v0.5.16-official-evidence-archive-closure-readiness-audit points to ed5eb4b TASK-DOC-179 update state after TASK-140",
    "v0.5.0 official evidence archive policy defined",
    "official manifest storage policy defined",
    "official manifest naming policy defined",
    "official manifest path validator completed",
    "evidence manifest generator completed",
    "evidence manifest schema validator completed",
    "Strategy Tester HTML parser completed",
    "MT5 log no-trade parser completed",
    "task_acceptance_report.ps1 available",
    "first official manifest creation authorization boundary defined",
    "first official evidence manifest created",
    "suitable for future v0.5.0 phase closure audit / tag",
    "current next boundary updated to TASK-142",
    "current next boundary remains TASK-142",
    "TASK-142 completed",
    "v0.5.0 official evidence archive phase closure readiness audit passed",
    "current HEAD is e35bcf2 TASK-DOC-182 update state after TASK-TAG-043",
    "current stable tag is v0.5.17-v050-official-evidence-archive-closure-readiness",
    "v0.5.17-v050-official-evidence-archive-closure-readiness points to 8702fd5 TASK-DOC-181 update state after TASK-141",
    "suitable for future v0.5.0 phase closure stable tag",
    "current next boundary updated to TASK-143",
    "current next boundary remains TASK-143",
    "TASK-143 completed",
    "v0.5.0 official evidence archive final phase closure audit passed",
    "current HEAD is c6edc02 TASK-DOC-184 update state after TASK-TAG-044",
    "current stable tag is v0.5.18-v050-official-evidence-archive-phase-closure-readiness",
    "v0.5.18-v050-official-evidence-archive-phase-closure-readiness points to ed4017b TASK-DOC-183 update state after TASK-142",
    "v0.5.0 final phase closure satisfied",
    "suitable for future v0.5.0 final phase closure stable tag",
    "current next boundary updated to TASK-144",
    "current next boundary remains TASK-144",
    "TASK-144 completed",
    "v0.5.0 final phase closure tag completion audit passed",
    "current HEAD is 26caea9 TASK-DOC-186 update state after TASK-TAG-045",
    "current stable tag is v0.5.19-v050-official-evidence-archive-final-phase-closure",
    "v0.5.19-v050-official-evidence-archive-final-phase-closure points to 38b343c TASK-DOC-185 update state after TASK-143",
    "v0.5.0 final phase closure fixed by v0.5.19",
    "engineering toolchain 19/19 PASS",
    "suitable for future v0.5.0 final closure documentation / transition boundary",
    "current next boundary updated to TASK-145",
    "current next boundary remains TASK-145",
    "TASK-145 completed",
    "v0.5.0 final closure documentation transition boundary readiness audit passed",
    "current HEAD is 30025ea TASK-DOC-188 update state after TASK-TAG-046",
    "current stable tag is v0.5.20-v050-final-closure-documentation-transition-boundary-readiness",
    "v0.5.20-v050-final-closure-documentation-transition-boundary-readiness points to 61fb9c0 TASK-DOC-187 update state after TASK-144",
    "v0.5.0 final closure documentation / transition boundary readiness fixed by v0.5.20",
    "v0.5.0 official evidence archive final phase closure fixed by v0.5.19",
    "first official evidence manifest fixed by v0.5.15",
    "suitable for future v0.5.0 final closure documentation stable tag",
    "suitable for future ChatGPT-defined v0.6.0 transition boundary",
    "current next boundary updated to TASK-146",
    "current next boundary remains TASK-146",
    "do not directly enter v0.6.0",
    "TASK-146 completed",
    "v0.5.0 final closure documentation transition boundary completion audit passed",
    "current HEAD is 924debc TASK-DOC-190 update state after TASK-TAG-047",
    "current stable tag is v0.5.21-v050-final-closure-documentation-transition-boundary",
    "v0.5.21-v050-final-closure-documentation-transition-boundary points to 3d3cfd9 TASK-DOC-189 update state after TASK-145",
    "v0.5.0 final closure documentation / transition boundary fixed by v0.5.21",
    "v0.5.21 does not automatically enter v0.6.0",
    "suitable for future v0.6.0 transition boundary planning task",
    "current next boundary updated to TASK-147",
    "current next boundary remains TASK-147",
    "define v0.5.0 evidence archive policy boundary",
    "v0.4.0 phase closure completed",
    "v0.5.0 boundary defined as official evidence archive policy and reproducibility boundary",
    "v0.5.0 allowed scope: evidence archive policy definition",
    "v0.5.0 allowed scope: official repository manifest boundary definition",
    "v0.5.0 allowed scope: metadata-only evidence references",
    "v0.5.0 allowed scope: evidence sanitization policy",
    "v0.5.0 allowed scope: reproducibility checklist",
    "v0.5.0 allowed scope: official manifest naming/location convention",
    "v0.5.0 allowed scope: external evidence retention policy",
    "v0.5.0 allowed scope: parser/generator hardening only when explicitly authorized",
    "v0.5.0 allowed scope: documentation / validation tooling updates",
    "v0.5.0 forbidden scope: no real trading",
    "v0.5.0 forbidden scope: no live trading readiness claim",
    "v0.5.0 forbidden scope: no real trading allowed claim",
    "v0.5.0 forbidden scope: no profitability claim",
    "v0.5.0 forbidden scope: no profit optimization",
    "v0.5.0 forbidden scope: no MT5 run unless future task explicitly authorizes",
    "v0.5.0 forbidden scope: no copying external evidence unless future task explicitly authorizes",
    "v0.5.0 forbidden scope: no repository manifest creation unless future task explicitly authorizes",
    "v0.5.0 forbidden scope: no MQ5 modification unless future task explicitly authorizes",
    "v0.5.0 forbidden scope: no backtest/sets modification unless future task explicitly authorizes",
    "v0.5.0 forbidden scope: no OrderSend / Buy / Sell / CTrade / PositionOpen / PositionClose / OrderModify / OrderClose",
    "v0.5.0 does not mean live trading readiness",
    "v0.5.0 does not mean real trading availability",
    "v0.5.0 does not mean profitable strategy completion",
    "v0.5.0 does not mean permission to run MT5",
    "v0.5.0 does not mean permission to copy evidence",
    "v0.5.0 does not mean permission to create official manifest yet",
    "TASK-235 completed",
    "TASK-235 read-only MQ5 strategy inventory audit PASS",
    "current HEAD is 0fc2b95 TASK-DOC-234 update state after TASK-233",
    "tracked working tree clean before TASK-DOC-236 edits",
    "MQ5 root exists",
    "scanned 7 MQ5 files: 1 .mq5 and 6 .mqh",
    "scanned file: config/InputConfig.mqh",
    "scanned file: core/EaController.mqh",
    "scanned file: execution/ExecutionManager.mqh",
    "scanned file: logger/Logger.mqh",
    "scanned file: risk/RiskManager.mqh",
    "scanned file: signals/SignalEngine.mqh",
    "scanned file: TradingSystem.mq5",
    "input parameter lines: 34",
    "InpEnableTrading appears in 4 files",
    "RiskManager appears in 2 files",
    "SignalEngine appears in 4 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade trading keywords are all false",
    "current MQ5 codebase is pure framework / no active trading instructions",
    "OnInit / OnTick / OnDeinit are present in framework files",
    "Inventory only; no MT5 run; no trading authorization.",
    "tools/run_release_validation_bundle.py --only mq5-inventory PASS",
    "tools/run_release_validation_bundle.py --only project-state-docs PASS",
    "tools/run_release_validation_bundle.py --only project-state-docs-self-test PASS",
    "TASK-235 did not modify MQ5 files",
    "TASK-235 did not run MT5",
    "TASK-235 did not create manifest / fixture / report / directory",
    "TASK-235 did not copy external evidence",
    "v0.6.0 implementation has not started",
    "suitable for ChatGPT to define the first v0.6.0 low-risk implementation planning task",
    "TASK-DOC-237 is a doc-only planning task",
    "docs/V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md exists",
    "TASK-DOC-237 does not enter v0.6.0 implementation",
    "TASK-DOC-237 does not modify MQ5",
    "TASK-DOC-237 does not run MT5",
    "current latest tag is v0.5.38-task-236-project-state-synced",
    "future candidate slice is TASK-238 v0.6.0 no-trade observability scaffold",
    "TASK-238 is a future candidate only and is not authorized by TASK-DOC-237",
    "future TASK-238 candidate must not introduce Buy / Sell / OrderSend / PositionOpen / CTrade",
    "TASK-DOC-238 is planning-only and defines a future candidate boundary",
    "docs/V060_TASK_238_NO_TRADE_SCAFFOLD_BOUNDARY.md exists",
    "TASK-DOC-238 does not enter TASK-238 implementation",
    "TASK-DOC-238 does not enter v0.6.0 implementation",
    "TASK-DOC-238 does not modify MQ5",
    "TASK-DOC-238 does not run MT5",
    "TASK-DOC-238 does not create manifest / fixture / report / directory",
    "TASK-DOC-238 does not copy external evidence",
    "TASK-DOC-238 does not modify official manifest / backtest/sets",
    "current latest tag is v0.5.39-task-237-first-low-risk-plan",
    "TASK-238 future candidate scope is no-trade observability scaffold only",
    "InpEnableTrading false",
    "Buy / Sell / OrderSend / PositionOpen / CTrade 均 false",
    "current MQ5 codebase remains pure framework / no active trading instructions",
    "TASK-DOC-239 defines the first authorized low-risk implementation slice boundary",
    "docs/V060_TASK_239_FIRST_IMPLEMENTATION_SLICE_BOUNDARY.md exists",
    "TASK-DOC-239 is planning + boundary only",
    "TASK-DOC-239 does not modify MQ5",
    "TASK-DOC-239 does not run MT5",
    "TASK-DOC-239 does not create manifest / fixture / report / directory",
    "TASK-DOC-239 does not copy external evidence",
    "TASK-DOC-239 does not modify official manifest / backtest/sets",
    "TASK-DOC-239 does not enter TASK-240",
    "TASK-DOC-239 does not enter v0.6.0 full implementation",
    "current latest tag is v0.5.40-task-238-no-trade-scaffold-boundary",
    "TASK-240 is first authorized v0.6.0 low-risk implementation slice",
    "TASK-240 is limited to no-trade observability scaffold",
    "TASK-240 remains limited to no-trade observability scaffold",
    "TASK-240 does not enter v0.6.0 full implementation",
    "current latest tag is v0.5.41-task-239-first-implementation-slice-boundary",
    "no-trade observability scaffold output is read-only",
    "TASK-240 adds only read-only observability input controls",
    "TASK-240 adds only no-trade logging / telemetry contract helper output",
    "TASK-240 adds only OnInit and optional throttled OnTick observability state output",
    "TASK-240 does not modify execution/ExecutionManager.mqh",
    "TASK-240 does not modify risk/RiskManager.mqh",
    "TASK-240 does not modify signals/SignalEngine.mqh",
    "TASK-240 does not run MT5",
    "TASK-240 does not run backtest",
    "TASK-240 does not trigger real trading",
    "TASK-240 does not trigger simulated trading",
    "TASK-240 does not send orders",
    "TASK-240 does not create manifest / fixture / report / directory",
    "TASK-240 does not copy external evidence",
    "TASK-240 does not modify official manifest / backtest/sets",
    "MQ5 inventory must remain PASS with trading keywords false",
    "TASK-DOC-241 objective is to sync TASK-240 no-trade observability scaffold state to project docs",
    "TASK-240 completed no-trade observability scaffold",
    "current HEAD is f9771d9 TASK-240 implement no-trade observability scaffold",
    "current latest tag is v0.5.42-task-240-v060-no-trade-observability-scaffold",
    "TASK-240 MQ5 inventory remains PASS",
    "TASK-240 trading keywords remain all false",
    "TASK-DOC-241 does not modify MQ5 / MQH",
    "TASK-DOC-241 does not run MT5",
    "TASK-DOC-241 does not create manifest / fixture / report / directory",
    "TASK-DOC-241 does not copy external evidence",
    "TASK-DOC-241 does not modify official manifest / backtest/sets",
    "TASK-DOC-241 does not commit",
    "TASK-242 implement mq5 no-trade observability contract validator",
    "TASK-242 objective is to implement a read-only MQ5 no-trade observability contract validator",
    "current HEAD is d5babfa TASK-DOC-241 update state after TASK-240",
    "current latest tag is v0.5.43-task-241-sync-task-240-state",
    "mq5 no-trade observability contract validator checks no MT5 run",
    "mq5 no-trade observability contract validator checks no trading authorization",
    "mq5 no-trade observability contract validator checks no-trade observability scaffold",
    "mq5 no-trade observability contract validator checks Inventory only; no MT5 run; no trading authorization.",
    "mq5 no-trade observability contract validator checks Buy / Sell / OrderSend / PositionOpen / CTrade remain absent from mq5 source files",
    "v0.6.0 implementation slices remain limited to no-trade scaffold / static validation",
    "TASK-242 does not modify MQ5 / MQH",
    "TASK-242 does not run MT5",
    "TASK-242 does not create manifest / fixture / report / directory",
    "TASK-242 does not copy external evidence",
    "TASK-242 does not commit",
    "TASK-243 implement structured no-trade observability status snapshot",
    "TASK-243 is a low-risk MQ5 implementation slice",
    "TASK-243 implementation scope is limited to structured no-trade observability status snapshot",
    "current HEAD is 8f59b3b TASK-242 implement mq5 no-trade observability contract validator",
    "current latest tag is v0.5.44-task-242-mq5-no-trade-observability-validator",
    "structured no-trade observability status snapshot records mode=no-trade observability scaffold",
    "structured no-trade observability status snapshot records inventory_notice=Inventory only; no MT5 run; no trading authorization.",
    "structured no-trade observability status snapshot records enable_trading",
    "structured no-trade observability status snapshot records observability_enabled",
    "structured no-trade observability status snapshot records init_log_enabled",
    "structured no-trade observability status snapshot records tick_log_enabled",
    "MQ5 inventory and no-trade observability contract must continue PASS",
    "TASK-243 does not run MT5",
    "TASK-243 does not create manifest / fixture / report / directory",
    "TASK-243 does not copy external evidence",
    "TASK-243 does not commit",
    "TASK-244 implement read-only MQ5 component status snapshot contract",
    "TASK-244 is a low-risk MQ5 implementation slice",
    "TASK-244 implementation scope is limited to read-only MQ5 component status snapshot contract",
    "current HEAD is f28f788 TASK-243 implement structured no-trade observability status snapshot",
    "current latest tag is v0.5.45-task-243-structured-no-trade-observability-snapshot",
    "read-only MQ5 component status snapshot contract records controller_status=ready",
    "read-only MQ5 component status snapshot contract records logger_status=ready",
    "read-only MQ5 component status snapshot contract records signal_status=read-only framework",
    "read-only MQ5 component status snapshot contract records risk_status=read-only framework",
    "read-only MQ5 component status snapshot contract records execution_status=read-only framework",
    "read-only MQ5 component status snapshot contract records all_components_no_trade=true",
    "TASK-244 does not run MT5",
    "TASK-244 does not create manifest / fixture / report / directory",
    "TASK-244 does not copy external evidence",
    "TASK-244 does not commit",
    "TASK-245 implement no-trade lifecycle telemetry event contract",
    "TASK-245 is a low-risk MQ5 implementation slice",
    "TASK-245 implementation scope is limited to no-trade lifecycle telemetry event contract",
    "current HEAD is 98fb991 TASK-244 implement read-only MQ5 component status snapshot contract",
    "current latest tag is v0.5.46-task-244-read-only-component-status-snapshot",
    "no-trade lifecycle telemetry event contract records lifecycle_event=init",
    "no-trade lifecycle telemetry event contract records lifecycle_event=tick",
    "no-trade lifecycle telemetry event contract records lifecycle_event=deinit",
    "no-trade lifecycle telemetry event contract records no_trade_guard=active",
    "no-trade lifecycle telemetry event contract records trading_authorization=false",
    "no-trade lifecycle telemetry event contract records mt5_run_required=false",
    "no-trade lifecycle telemetry event contract records evidence_generation=false",
    "no-trade lifecycle telemetry event contract records manifest_generation=false",
    "TASK-245 does not run MT5",
    "TASK-245 does not create manifest / fixture / report / directory",
    "TASK-245 does not copy external evidence",
    "TASK-245 does not commit",
    "TASK-246 implement MQ5 read-only runtime status snapshot logging",
    "TASK-246 is a low-risk MQ5 implementation slice",
    "TASK-246 implementation scope is limited to read-only runtime status snapshot logging",
    "current HEAD is 8f6762c TASK-245 implement no-trade lifecycle telemetry event contract",
    "current latest tag is v0.5.47-task-245-no-trade-lifecycle-telemetry",
    "read-only runtime status snapshot logging records runtime_status_snapshot=true",
    "read-only runtime status snapshot logging records controller_status",
    "read-only runtime status snapshot logging records logger_status",
    "read-only runtime status snapshot logging records signal_status",
    "read-only runtime status snapshot logging records risk_status",
    "read-only runtime status snapshot logging records execution_status",
    "read-only runtime status snapshot logging records no_trade_guard=active",
    "read-only runtime status snapshot logging records trading_authorization=false",
    "read-only runtime status snapshot logging records mt5_run_required=false",
    "read-only runtime status snapshot logging records evidence_generation=false",
    "read-only runtime status snapshot logging records manifest_generation=false",
    "TASK-246 does not run MT5",
    "TASK-246 does not create manifest / fixture / report / directory",
    "TASK-246 does not copy external evidence",
    "TASK-246 does not commit",
    "TASK-247 implement MQ5 no-trade performance metrics contract",
    "TASK-247 is a low-risk MQ5 implementation slice",
    "TASK-247 implementation scope is limited to MQ5 no-trade performance metrics contract",
    "current HEAD is b85b824 TASK-246 implement read-only runtime status snapshot logging",
    "current latest tag is v0.5.48-task-246-read-only-runtime-status-snapshot",
    "MQ5 no-trade performance metrics contract records runtime_metrics_snapshot=true",
    "MQ5 no-trade performance metrics contract records tick_count",
    "MQ5 no-trade performance metrics contract records oninit_call_count",
    "MQ5 no-trade performance metrics contract records ondeinit_call_count",
    "MQ5 no-trade performance metrics contract records last_tick_timestamp",
    "MQ5 no-trade performance metrics contract records all_components_no_trade=true",
    "MQ5 no-trade performance metrics contract records trading_authorization=false",
    "MQ5 no-trade performance metrics contract records mt5_run_required=false",
    "TASK-247 does not run MT5",
    "TASK-247 does not create manifest / fixture / report / directory",
    "TASK-247 does not copy external evidence",
    "TASK-247 does not commit",
    "TASK-248 implement MQ5 no-trade safety guard invariant contract",
    "TASK-248 is a low-risk MQ5 implementation slice",
    "TASK-248 implementation scope is limited to no-trade safety guard invariant contract",
    "current HEAD is 99e3763 TASK-247 implement no-trade performance metrics contract",
    "current latest tag is v0.5.49-task-247-no-trade-performance-metrics",
    "no-trade safety guard invariant contract records safety_guard_snapshot=true",
    "no-trade safety guard invariant contract records invariant_trading_disabled=true",
    "no-trade safety guard invariant contract records invariant_execution_disabled=true",
    "no-trade safety guard invariant contract records invariant_order_submission_disabled=true",
    "no-trade safety guard invariant contract records invariant_position_management_disabled=true",
    "no-trade safety guard invariant contract records invariant_external_evidence_disabled=true",
    "no-trade safety guard invariant contract records invariant_manifest_generation_disabled=true",
    "no-trade safety guard invariant contract records invariant_mt5_run_required=false",
    "no-trade safety guard invariant contract records invariant_all_components_no_trade=true",
    "no-trade safety guard invariant contract records trading_authorization=false",
    "MQ5 inventory must remain 7 files",
    "TASK-248 does not run MT5",
    "TASK-248 does not create manifest / fixture / report / directory",
    "TASK-248 does not copy external evidence",
    "TASK-248 does not add MQ5 / MQH files",
    "TASK-248 does not commit",
    "TASK-249 implement MQ5 read-only metrics aggregation & historical events contract",
    "TASK-249 is a low-risk MQ5 implementation slice",
    "TASK-249 implementation scope is limited to read-only metrics aggregation & historical events contract",
    "current HEAD is 26ecbfe TASK-248 implement no-trade safety guard invariant contract",
    "current latest tag is v0.5.50-task-248-no-trade-safety-guard-invariant",
    "read-only metrics aggregation & historical events contract records metrics_aggregation_snapshot=true",
    "read-only metrics aggregation & historical events contract records historical_events_count",
    "read-only metrics aggregation & historical events contract records last_n_ticks_metrics",
    "read-only metrics aggregation & historical events contract records aggregated_component_status",
    "read-only metrics aggregation & historical events contract records no_trade_guard=active",
    "read-only metrics aggregation & historical events contract records trading_authorization=false",
    "read-only metrics aggregation & historical events contract records mt5_run_required=false",
    "read-only metrics aggregation & historical events contract records evidence_generation=false",
    "read-only metrics aggregation & historical events contract records manifest_generation=false",
    "TASK-249 does not run MT5",
    "TASK-249 does not create manifest / fixture / report / directory",
    "TASK-249 does not copy external evidence",
    "TASK-249 does not add MQ5 / MQH files",
    "TASK-249 does not commit",
    "TASK-250 implement MQ5 read-only system health & observability summary contract",
    "TASK-250 is a low-risk MQ5 implementation slice",
    "TASK-250 implementation scope is limited to read-only system health & observability summary contract",
    "current HEAD is 1ad896a TASK-249 implement read-only metrics aggregation & historical events contract",
    "current latest tag is v0.5.51-task-249-read-only-metrics-aggregation",
    "read-only system health & observability summary contract records system_health_snapshot=true",
    "read-only system health & observability summary contract records observability_enabled",
    "read-only system health & observability summary contract records last_snapshot_timestamp",
    "read-only system health & observability summary contract records aggregated_component_status",
    "read-only system health & observability summary contract records all_components_no_trade=true",
    "read-only system health & observability summary contract records trading_authorization=false",
    "read-only system health & observability summary contract records mt5_run_required=false",
    "read-only system health & observability summary contract records evidence_generation=false",
    "read-only system health & observability summary contract records manifest_generation=false",
    "TASK-250 does not run MT5",
    "TASK-250 does not create manifest / fixture / report / directory",
    "TASK-250 does not copy external evidence",
    "TASK-250 does not add MQ5 / MQH files",
    "TASK-250 does not commit",
    "TASK-251 implement MQ5 read-only signal context snapshot contract",
    "TASK-251 is a low-risk MQ5 implementation slice",
    "TASK-251 implementation scope is limited to read-only signal context snapshot contract",
    "current HEAD is d50c34b TASK-250 implement read-only system health & observability summary contract",
    "current latest tag is v0.5.52-task-250-read-only-system-health-observability",
    "read-only signal context snapshot contract records signal_context_snapshot=true",
    "read-only signal context snapshot contract records signal_layer_mode=read-only framework",
    "read-only signal context snapshot contract records signal_context_available=true",
    "read-only signal context snapshot contract records signal_direction_authorized=false",
    "read-only signal context snapshot contract records signal_execution_authorized=false",
    "read-only signal context snapshot contract records signal_order_intent=false",
    "read-only signal context snapshot contract records signal_external_evidence_required=false",
    "read-only signal context snapshot contract records signal_manifest_generation=false",
    "read-only signal context snapshot contract records no_trade_guard=active",
    "TASK-251 does not run MT5",
    "TASK-251 does not create manifest / fixture / report / directory",
    "TASK-251 does not copy external evidence",
    "TASK-251 does not add MQ5 / MQH files",
    "TASK-251 does not commit",
    "TASK-252 implement MQ5 read-only risk context snapshot contract",
    "TASK-252 is a low-risk MQ5 implementation slice",
    "TASK-252 implementation scope is limited to read-only risk context snapshot contract",
    "current HEAD is 56a8fae TASK-251 implement read-only signal context snapshot contract",
    "current latest tag is v0.5.53-task-251-read-only-signal-context",
    "read-only risk context snapshot contract records risk_context_snapshot=true",
    "read-only risk context snapshot contract records risk_layer_mode=read-only framework",
    "read-only risk context snapshot contract records risk_context_available=true",
    "read-only risk context snapshot contract records risk_authorization=false",
    "read-only risk context snapshot contract records risk_sizing_authorized=false",
    "read-only risk context snapshot contract records risk_exposure_authorized=false",
    "read-only risk context snapshot contract records risk_execution_authorized=false",
    "read-only risk context snapshot contract records risk_external_evidence_required=false",
    "read-only risk context snapshot contract records risk_manifest_generation=false",
    "read-only risk context snapshot contract records no_trade_guard=active",
    "TASK-252 does not run MT5",
    "TASK-252 does not create manifest / fixture / report / directory",
    "TASK-252 does not copy external evidence",
    "TASK-252 does not add MQ5 / MQH files",
    "TASK-252 does not commit",
    "TASK-253 implement MQ5 read-only execution context snapshot contract",
    "TASK-253 is a low-risk MQ5 implementation slice",
    "TASK-253 implementation scope is limited to read-only execution context snapshot contract",
    "current HEAD is 3dd463d TASK-252 implement read-only risk context snapshot contract",
    "current latest tag is v0.5.54-task-252-read-only-risk-context",
    "read-only execution context snapshot contract records execution_context_snapshot=true",
    "read-only execution context snapshot contract records execution_layer_mode=read-only framework",
    "read-only execution context snapshot contract records execution_context_available=true",
    "read-only execution context snapshot contract records execution_authorization=false",
    "read-only execution context snapshot contract records execution_request_authorized=false",
    "read-only execution context snapshot contract records execution_route_authorized=false",
    "read-only execution context snapshot contract records execution_dispatch_authorized=false",
    "read-only execution context snapshot contract records execution_external_evidence_required=false",
    "read-only execution context snapshot contract records execution_manifest_generation=false",
    "read-only execution context snapshot contract records no_trade_guard=active",
    "TASK-253 does not run MT5",
    "TASK-253 does not create manifest / fixture / report / directory",
    "TASK-253 does not copy external evidence",
    "TASK-253 does not add MQ5 / MQH files",
    "TASK-253 does not commit",
    "TASK-DOC-254 update project state docs after TASK-253",
    "TASK-DOC-254 is a project state docs sync task",
    "TASK-253 completed read-only execution context snapshot contract",
    "TASK-253 commit is 7773a2f TASK-253 implement read-only execution context snapshot contract",
    "TASK-253 tag is v0.5.55-task-253-read-only-execution-context",
    "current HEAD is 7773a2f TASK-253 implement read-only execution context snapshot contract",
    "current latest tag is v0.5.55-task-253-read-only-execution-context",
    "read-only execution context snapshot contract is synced to project state docs",
    "read-only execution context snapshot contract fields remain execution_context_snapshot=true",
    "read-only execution context snapshot contract fields remain execution_layer_mode=read-only framework",
    "read-only execution context snapshot contract fields remain execution_context_available=true",
    "read-only execution context snapshot contract fields remain execution_authorization=false",
    "read-only execution context snapshot contract fields remain execution_request_authorized=false",
    "read-only execution context snapshot contract fields remain execution_route_authorized=false",
    "read-only execution context snapshot contract fields remain execution_dispatch_authorized=false",
    "read-only execution context snapshot contract fields remain execution_external_evidence_required=false",
    "read-only execution context snapshot contract fields remain execution_manifest_generation=false",
    "read-only execution context snapshot contract fields remain no_trade_guard=active",
    "validate_mq5_no_trade_observability.py covers TASK-253 execution context fields and controller path",
    "test_validate_mq5_no_trade_observability.py covers TASK-253 execution context fields and controller path",
    "MQ5 inventory remains 7 files",
    "trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade",
    "TASK-DOC-256 confirms MQ5 inventory remains 7 files",
    "TASK-DOC-256 confirms no MT5 run",
    "TASK-DOC-256 confirms no trading authorization",
    "no MT5 run",
    "no trading authorization",
    "TASK-DOC-254 does not modify MQ5",
    "TASK-DOC-254 does not run MT5",
    "TASK-DOC-254 does not create manifest / fixture / report / directory",
    "TASK-DOC-254 does not copy external evidence",
    "TASK-DOC-254 does not commit",
    "TASK-255 implement MQ5 read-only pipeline context aggregation snapshot contract",
    "TASK-255 is a low-risk MQ5 implementation slice",
    "TASK-255 implementation scope is limited to read-only pipeline context aggregation snapshot contract",
    "current HEAD is 44369dd TASK-DOC-254 update project state docs after TASK-253",
    "current latest tag is v0.5.56-task-254-sync-task-253-state",
    "read-only pipeline context aggregation snapshot contract records pipeline_context_snapshot=true",
    "read-only pipeline context aggregation snapshot contract records pipeline_layer_mode=read-only framework",
    "read-only pipeline context aggregation snapshot contract records signal_context_linked=true",
    "read-only pipeline context aggregation snapshot contract records risk_context_linked=true",
    "read-only pipeline context aggregation snapshot contract records execution_context_linked=true",
    "read-only pipeline context aggregation snapshot contract records pipeline_authorization=false",
    "read-only pipeline context aggregation snapshot contract records pipeline_direction_authorized=false",
    "read-only pipeline context aggregation snapshot contract records pipeline_risk_authorized=false",
    "read-only pipeline context aggregation snapshot contract records pipeline_execution_authorized=false",
    "read-only pipeline context aggregation snapshot contract records pipeline_dispatch_authorized=false",
    "read-only pipeline context aggregation snapshot contract records pipeline_intent=false",
    "read-only pipeline context aggregation snapshot contract records all_pipeline_layers_no_trade=true",
    "read-only pipeline context aggregation snapshot contract records no_trade_guard=active",
    "read-only pipeline context aggregation snapshot contract records trading_authorization=false",
    "read-only pipeline context aggregation snapshot contract records mt5_run_required=false",
    "read-only pipeline context aggregation snapshot contract records evidence_generation=false",
    "read-only pipeline context aggregation snapshot contract records manifest_generation=false",
    "TASK-255 does not run MT5",
    "TASK-255 does not create manifest / fixture / report / directory",
    "TASK-255 does not copy external evidence",
    "TASK-255 does not add MQ5 / MQH files",
    "TASK-255 does not commit",
    "TASK-DOC-256 update state after TASK-255",
    "TASK-DOC-256 is a doc-only project state sync task",
    "TASK-255 completed read-only pipeline context aggregation snapshot contract",
    "TASK-255 commit is fc215ea TASK-255 implement read-only pipeline context aggregation snapshot contract",
    "TASK-255 tag is v0.5.57-task-255-read-only-pipeline-context",
    "current HEAD is fc215ea TASK-255 implement read-only pipeline context aggregation snapshot contract",
    "current latest tag is v0.5.57-task-255-read-only-pipeline-context",
    "read-only pipeline context aggregation snapshot contract is synced to project state docs",
    "MQ5 inventory remains 7 files",
    "mq5-no-trade-observability PASS",
    "mq5-inventory PASS",
    "project-state-docs PASS",
    "project-state-docs-self-test PASS",
    "trading keywords remain false for Buy / Sell / OrderSend / PositionOpen / CTrade",
    "no MT5 run",
    "no trading authorization",
    "TASK-DOC-256 does not modify MQ5",
    "TASK-DOC-256 does not modify MQH",
    "TASK-DOC-256 does not run MT5",
    "TASK-DOC-256 does not create manifest / fixture / report / directory",
    "TASK-DOC-256 does not copy external evidence",
    "TASK-DOC-256 does not commit",
    "TASK-DOC-256 does not create tag",
    "TASK-257 implement MQ5 read-only authorization matrix snapshot contract",
    "TASK-257 is a low-risk MQ5 implementation slice",
    "TASK-257 implementation scope is limited to read-only authorization matrix snapshot contract",
    "TASK-DOC-256 completed project state docs sync after TASK-255",
    "TASK-DOC-256 commit is 678a77f TASK-DOC-256 update state after TASK-255",
    "TASK-DOC-256 tag is v0.5.58-task-256-sync-task-255-state",
    "current HEAD is 678a77f TASK-DOC-256 update state after TASK-255",
    "current latest tag is v0.5.58-task-256-sync-task-255-state",
    "read-only authorization matrix snapshot contract records authorization_matrix_snapshot=true",
    "read-only authorization matrix snapshot contract records authorization_matrix_mode=read-only framework",
    "read-only authorization matrix snapshot contract records signal_authorization=false",
    "read-only authorization matrix snapshot contract records signal_direction_authorized=false",
    "read-only authorization matrix snapshot contract records risk_authorization=false",
    "read-only authorization matrix snapshot contract records risk_sizing_authorized=false",
    "read-only authorization matrix snapshot contract records risk_exposure_authorized=false",
    "read-only authorization matrix snapshot contract records execution_authorization=false",
    "read-only authorization matrix snapshot contract records execution_request_authorized=false",
    "read-only authorization matrix snapshot contract records execution_dispatch_authorized=false",
    "read-only authorization matrix snapshot contract records pipeline_authorization=false",
    "read-only authorization matrix snapshot contract records pipeline_intent=false",
    "read-only authorization matrix snapshot contract records trading_authorization=false",
    "read-only authorization matrix snapshot contract records all_authorizations_false=true",
    "read-only authorization matrix snapshot contract records all_pipeline_layers_no_trade=true",
    "read-only authorization matrix snapshot contract records no_trade_guard=active",
    "read-only authorization matrix snapshot contract records mt5_run_required=false",
    "read-only authorization matrix snapshot contract records evidence_generation=false",
    "read-only authorization matrix snapshot contract records manifest_generation=false",
    "TASK-257 does not run MT5",
    "TASK-257 does not create manifest / fixture / report / directory",
    "TASK-257 does not copy external evidence",
    "TASK-257 does not add MQ5 / MQH files",
    "TASK-257 does not commit",
    "TASK-258 implement MQ5 read-only decision gate snapshot contract",
    "TASK-258 is a low-risk MQ5 implementation slice",
    "TASK-258 implementation scope is limited to read-only decision gate snapshot contract",
    "TASK-257 completed read-only authorization matrix snapshot contract",
    "TASK-257 commit is 950a71e TASK-257 implement read-only authorization matrix snapshot contract",
    "TASK-257 tag is v0.5.59-task-257-read-only-authorization-matrix",
    "current HEAD is 950a71e TASK-257 implement read-only authorization matrix snapshot contract",
    "current latest tag is v0.5.59-task-257-read-only-authorization-matrix",
    "read-only decision gate snapshot contract records decision_gate_snapshot=true",
    "read-only decision gate snapshot contract records decision_gate_mode=read-only framework",
    "read-only decision gate snapshot contract records decision_state=blocked_no_trade",
    "read-only decision gate snapshot contract records decision_candidate_available=false",
    "read-only decision gate snapshot contract records decision_direction_authorized=false",
    "read-only decision gate snapshot contract records decision_risk_authorized=false",
    "read-only decision gate snapshot contract records decision_execution_authorized=false",
    "read-only decision gate snapshot contract records decision_dispatch_authorized=false",
    "read-only decision gate snapshot contract records decision_output_authorized=false",
    "read-only decision gate snapshot contract records decision_intent=false",
    "TASK-258 does not run MT5",
    "TASK-258 does not create manifest / fixture / report / directory",
    "TASK-258 does not copy external evidence",
    "TASK-258 does not add MQ5 / MQH files",
    "TASK-258 does not commit",
    "TASK-259 implement MQ5 read-only decision rejection reason snapshot contract",
    "TASK-259 is a low-risk MQ5 implementation slice",
    "TASK-259 implementation scope is limited to read-only decision rejection reason snapshot contract",
    "TASK-258 completed read-only decision gate snapshot contract",
    "TASK-258 commit is f1f53e6 TASK-258 implement read-only decision gate snapshot contract",
    "TASK-258 tag is v0.5.60-task-258-read-only-decision-gate",
    "current HEAD is f1f53e6 TASK-258 implement read-only decision gate snapshot contract",
    "current latest tag is v0.5.60-task-258-read-only-decision-gate",
    "read-only decision rejection reason snapshot contract records decision_rejection_snapshot=true",
    "read-only decision rejection reason snapshot contract records decision_rejection_mode=read-only framework",
    "read-only decision rejection reason snapshot contract records rejection_reason=no_trade_guard_active",
    "read-only decision rejection reason snapshot contract records rejection_trading_authorization=false",
    "read-only decision rejection reason snapshot contract records rejection_signal_authorization=false",
    "read-only decision rejection reason snapshot contract records rejection_risk_authorization=false",
    "read-only decision rejection reason snapshot contract records rejection_execution_authorization=false",
    "read-only decision rejection reason snapshot contract records rejection_pipeline_authorization=false",
    "read-only decision rejection reason snapshot contract records rejection_external_evidence=false",
    "read-only decision rejection reason snapshot contract records rejection_manifest_generation=false",
    "read-only decision rejection reason snapshot contract records rejection_mt5_run_required=false",
    "TASK-259 does not run MT5",
    "TASK-259 does not create manifest / fixture / report / directory",
    "TASK-259 does not copy external evidence",
    "TASK-259 does not add MQ5 / MQH files",
    "TASK-259 does not commit",
    "TASK-DOC-260 create first observability extension planning packet",
    "TASK-DOC-260 is planning-only",
    "TASK-DOC-260 creates docs/V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md",
    "TASK-DOC-260 does not authorize implementation",
    "TASK-259 completed read-only decision rejection reason snapshot contract",
    "TASK-259 commit is 6451e78 TASK-259 implement read-only decision rejection reason snapshot contract",
    "TASK-259 tag is v0.5.61-task-259-read-only-decision-rejection-reason",
    "current HEAD is 6451e78 TASK-259 implement read-only decision rejection reason snapshot contract",
    "current latest tag is v0.5.61-task-259-read-only-decision-rejection-reason",
    "first observability extension planning packet is future candidate only",
    "no-trade observability extension remains planning-only",
    "not implementation authorization",
    "MQ5 inventory remains 7 files",
    "mq5-inventory PASS",
    "mq5-no-trade-observability PASS",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-DOC-260 does not modify MQ5 / MQH",
    "TASK-DOC-260 does not run MT5",
    "TASK-DOC-260 does not create manifest / fixture / report / directory",
    "TASK-DOC-260 does not copy external evidence",
    "TASK-DOC-260 does not commit",
    "TASK-DOC-260 does not tag",
    "TASK-261 must not be entered directly",
    "GPT must define a separate future TASK-261 boundary",
    "TASK-DOC-261 create next observability extension planning packet",
    "TASK-DOC-261 is planning-only",
    "TASK-DOC-261 creates docs/V060_TASK_261_OBSERVABILITY_EXTENSION_NEXT_PLAN.md",
    "TASK-DOC-261 does not authorize implementation",
    "TASK-DOC-260 completed first observability extension planning packet",
    "TASK-DOC-260 commit is cb7675f TASK-DOC-260 create first observability extension planning packet",
    "TASK-DOC-260 tag is v0.5.62-task-260-first-observability-extension-plan",
    "current HEAD is cb7675f TASK-DOC-260 create first observability extension planning packet",
    "current latest tag is v0.5.62-task-260-first-observability-extension-plan",
    "next observability extension planning packet is future candidate only",
    "no-trade scaffold remains the active safety boundary",
    "TASK-DOC-261 does not modify MQ5 / MQH",
    "TASK-DOC-261 does not run MT5",
    "TASK-DOC-261 does not create manifest / fixture / report / directory",
    "TASK-DOC-261 does not copy external evidence",
    "TASK-DOC-261 does not commit",
    "TASK-DOC-261 does not tag",
    "TASK-262 must not be entered directly",
    "GPT must define a separate future boundary before TASK-262",
    "TASK-DOC-262 create follow-up observability extension planning packet",
    "TASK-DOC-262 is planning-only",
    "TASK-DOC-262 creates docs/V060_TASK_262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN.md",
    "TASK-DOC-262 does not authorize implementation",
    "TASK-DOC-261 completed next observability extension planning packet",
    "TASK-DOC-261 commit is 527486d TASK-DOC-261 create next observability extension planning packet",
    "TASK-DOC-261 tag is v0.5.63-task-261-observability-extension-next-plan",
    "current HEAD is 527486d TASK-DOC-261 create next observability extension planning packet",
    "current latest tag is v0.5.63-task-261-observability-extension-next-plan",
    "follow-up observability extension planning packet is future candidate only",
    "TASK-DOC-262 does not modify MQ5 / MQH",
    "TASK-DOC-262 does not run MT5",
    "TASK-DOC-262 does not create manifest / fixture / report / directory",
    "TASK-DOC-262 does not copy external evidence",
    "TASK-DOC-262 does not commit",
    "TASK-DOC-262 does not tag",
    "TASK-263 must not be entered directly",
    "GPT must define a separate future boundary before TASK-263",
    "TASK-DOC-263 create future observability extension planning packet",
    "TASK-DOC-263 is planning-only",
    "TASK-DOC-263 creates docs/V060_TASK_263_OBSERVABILITY_EXTENSION_FUTURE_PLAN.md",
    "TASK-DOC-263 does not authorize implementation",
    "TASK-DOC-262 completed follow-up observability extension planning packet",
    "TASK-DOC-262 commit is 69f12a6 TASK-DOC-262 create follow-up observability extension planning packet",
    "TASK-DOC-262 tag is v0.5.64-task-262-observability-extension-followup-plan",
    "current HEAD is 69f12a6 TASK-DOC-262 create follow-up observability extension planning packet",
    "current latest tag is v0.5.64-task-262-observability-extension-followup-plan",
    "future observability extension planning packet is future candidate only",
    "TASK-DOC-263 does not modify MQ5 / MQH",
    "TASK-DOC-263 does not run MT5",
    "TASK-DOC-263 does not create manifest / fixture / report / directory",
    "TASK-DOC-263 does not copy external evidence",
    "TASK-DOC-263 does not commit",
    "TASK-DOC-263 does not tag",
    "TASK-264 must not be entered directly",
    "GPT must define a separate future boundary before TASK-264",
    "current task is TASK-264 implement MQ5 read-only observability consolidation contract",
    "TASK-264 implement MQ5 read-only observability consolidation contract",
    "TASK-264 is a low-risk MQ5 implementation slice",
    "TASK-264 is not a planning packet",
    "TASK-264 must not continue planning packet chain",
    "TASK-DOC-263 completed future observability extension planning packet",
    "TASK-DOC-263 commit is d7fe9b6 TASK-DOC-263 create future observability extension planning packet",
    "TASK-DOC-263 tag is v0.5.65-task-263-observability-extension-future-plan",
    "current HEAD is d7fe9b6 TASK-DOC-263 create future observability extension planning packet",
    "current latest tag is v0.5.65-task-263-observability-extension-future-plan",
    "implementation scope is limited to read-only observability consolidation contract",
    "TASK-264 confirms MQ5 inventory remains 7 files",
    "mq5-inventory PASS",
    "mq5-no-trade-observability PASS",
    "project-state-docs PASS",
    "project-state-docs-self-test PASS",
    "TASK-264 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-264 does not run MT5",
    "TASK-264 does not create manifest / fixture / report / directory",
    "TASK-264 does not copy external evidence",
    "TASK-264 does not add MQ5 / MQH files",
    "do not directly enter trading, MT5 run, manifest creation, or backtest evidence",
    "current task is TASK-265 implement MQ5 read-only observability contract registry snapshot",
    "TASK-265 implement MQ5 read-only observability contract registry snapshot",
    "TASK-265 is a low-risk MQ5 implementation slice",
    "TASK-265 does not create a new planning packet",
    "TASK-264 completed read-only observability consolidation contract",
    "TASK-264 commit is 40896e9 TASK-264 implement read-only observability consolidation contract",
    "TASK-264 tag is v0.5.66-task-264-read-only-observability-consolidation",
    "current HEAD is 40896e9 TASK-264 implement read-only observability consolidation contract",
    "current latest tag is v0.5.66-task-264-read-only-observability-consolidation",
    "implementation scope is limited to read-only observability contract registry snapshot",
    "TASK-265 confirms MQ5 inventory remains 7 files",
    "TASK-265 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-265 does not run MT5",
    "TASK-265 does not create manifest / fixture / report / directory",
    "TASK-265 does not copy external evidence",
    "TASK-265 does not add MQ5 / MQH files",
    "Inventory only; no MT5 run; no trading authorization.",
    "current task is TASK-266 implement fast no-trade development validation profile",
    "TASK-266 implement fast no-trade development validation profile",
    "TASK-266 is a tooling efficiency task",
    "TASK-266 is tooling + docs + self-test update",
    "TASK-266 does not modify MQ5 / MQH",
    "TASK-266 does not run MT5",
    "TASK-266 does not create manifest / fixture / report / directory",
    "TASK-266 does not copy external evidence",
    "TASK-266 does not commit",
    "TASK-265 completed read-only observability contract registry snapshot",
    "TASK-265 commit is 139265d TASK-265 implement read-only observability contract registry snapshot",
    "TASK-265 tag is v0.5.67-task-265-observability-contract-registry",
    "current HEAD is 139265d TASK-265 implement read-only observability contract registry snapshot",
    "current latest tag is v0.5.67-task-265-observability-contract-registry",
    "implementation scope is limited to fast no-trade development validation profile",
    "new profile is fast-no-trade-dev",
    "python tools/run_release_validation_bundle.py --profile fast-no-trade-dev",
    "TASK-266 confirms MQ5 inventory remains 7 files",
    "TASK-266 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-267 implement one-command fast no-trade preflight runner",
    "TASK-267 implement one-command fast no-trade preflight runner",
    "TASK-267 is a tooling efficiency task",
    "TASK-267 is tooling + docs + self-test update",
    "TASK-266 completed fast no-trade development validation profile",
    "TASK-266 commit is f23ce3e TASK-266 implement fast no-trade development validation profile",
    "TASK-266 tag is v0.5.68-task-266-fast-no-trade-dev-profile",
    "current HEAD is f23ce3e TASK-266 implement fast no-trade development validation profile",
    "current latest tag is v0.5.68-task-266-fast-no-trade-dev-profile",
    "implementation scope is limited to one-command fast no-trade preflight runner",
    "new runner is tools/run_fast_no_trade_preflight.py",
    "python tools/run_fast_no_trade_preflight.py",
    "fast-no-trade-dev profile remains the default release validation profile",
    "runner supports --doc-only",
    "runner supports --strict-mq5",
    "TASK-267 does not modify MQ5 / MQH",
    "TASK-267 does not run MT5",
    "TASK-267 does not create manifest / fixture / report / directory",
    "TASK-267 does not copy external evidence",
    "TASK-267 confirms MQ5 inventory remains 7 files",
    "TASK-267 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-268 implement allowed-change guard for fast no-trade preflight",
    "TASK-268 implement allowed-change guard for fast no-trade preflight",
    "TASK-268 is a tooling efficiency task",
    "TASK-268 is tooling + docs + self-test update",
    "TASK-267 completed one-command fast no-trade preflight runner",
    "TASK-267 commit is 1f2de5c TASK-267 implement one-command fast no-trade preflight runner",
    "TASK-267 tag is v0.5.69-task-267-fast-no-trade-preflight",
    "current HEAD is 1f2de5c TASK-267 implement one-command fast no-trade preflight runner",
    "current latest tag is v0.5.69-task-267-fast-no-trade-preflight",
    "implementation scope is limited to allowed-change guard for fast no-trade preflight",
    "allowed-change guard",
    "run_fast_no_trade_preflight.py",
    "--check-allowed-changes",
    "\n- --allow\n",
    "\n- --allow-prefix\n",
    "TASK-268 does not modify MQ5 / MQH",
    "TASK-268 does not run MT5",
    "TASK-268 does not create manifest / fixture / report / directory",
    "TASK-268 does not copy external evidence",
    "TASK-268 confirms MQ5 inventory remains 7 files",
    "TASK-268 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-269 implement read-only observability error/exception logging contract",
    "TASK-269 implement read-only observability error/exception logging contract",
    "TASK-269 is a low-risk MQ5 implementation slice",
    "TASK-269 implementation scope is limited to read-only observability error/exception logging contract",
    "TASK-268 completed allowed-change guard for fast no-trade preflight",
    "TASK-268 commit is a0f0200 TASK-268 implement allowed-change guard for fast no-trade preflight",
    "TASK-268 tag is v0.5.70-task-268-fast-no-trade-allowed-change-guard",
    "current HEAD is a0f0200 TASK-268 implement allowed-change guard for fast no-trade preflight",
    "current latest tag is v0.5.70-task-268-fast-no-trade-allowed-change-guard",
    "read-only observability error/exception logging contract records error_snapshot=true",
    "read-only observability error/exception logging contract records error_type=read-only framework",
    "read-only observability error/exception logging contract records error_timestamp",
    "read-only observability error/exception logging contract records component_origin",
    "read-only observability error/exception logging contract records error_details",
    "read-only observability error/exception logging contract records all_observability_outputs_read_only=true",
    "read-only observability error/exception logging contract records all_authorizations_false=true",
    "read-only observability error/exception logging contract records no_trade_guard=active",
    "read-only observability error/exception logging contract records trading_authorization=false",
    "read-only observability error/exception logging contract records mt5_run_required=false",
    "read-only observability error/exception logging contract records evidence_generation=false",
    "read-only observability error/exception logging contract records manifest_generation=false",
    "read-only observability error/exception logging contract records Inventory only; no MT5 run; no trading authorization.",
    "LogReadOnlyObservabilityErrorSnapshot",
    "OnTick error/exception logging remains gated by InpObservabilityLogOnTick",
    "TASK-269 preserves TASK-243 through TASK-268 no-trade observability outputs",
    "TASK-269 does not run MT5",
    "TASK-269 does not create manifest / fixture / report / directory",
    "TASK-269 does not copy external evidence",
    "TASK-269 does not add MQ5 / MQH files",
    "TASK-269 does not commit",
    "TASK-269 confirms MQ5 inventory remains 7 files",
    "TASK-269 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-270 implement fast preflight allowed-change presets",
    "TASK-270 implement fast preflight allowed-change presets",
    "TASK-270 is a tooling efficiency task",
    "TASK-270 is tooling + docs + self-test update",
    "TASK-269 completed read-only observability error/exception logging contract",
    "TASK-269 commit is 5ebdf74 TASK-269 implement read-only observability error/exception logging contract",
    "TASK-269 tag is v0.5.71-task-269-read-only-observability-error-snapshot",
    "current HEAD is 5ebdf74 TASK-269 implement read-only observability error/exception logging contract",
    "current latest tag is v0.5.71-task-269-read-only-observability-error-snapshot",
    "implementation scope is limited to fast preflight allowed-change presets",
    "--allow-preset",
    "doc-state",
    "tooling-preflight",
    "mq5-observability",
    "allowed-change guard can now use short preset commands",
    "TASK-270 does not modify MQ5 / MQH",
    "TASK-270 does not run MT5",
    "TASK-270 does not create manifest / fixture / report / directory",
    "TASK-270 does not copy external evidence",
    "TASK-270 confirms MQ5 inventory remains 7 files",
    "TASK-270 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-271 implement read-only telemetry aggregation for error & metrics",
    "TASK-271 implement read-only telemetry aggregation for error & metrics",
    "TASK-271 is a low-risk MQ5 implementation slice",
    "TASK-271 implementation scope is limited to read-only telemetry aggregation snapshot",
    "TASK-270 completed fast preflight allowed-change presets",
    "TASK-270 commit is 6b9c3a8 TASK-270 implement fast no-trade preflight presets",
    "TASK-270 tag is v0.5.72-task-270-fast-no-trade-preflight-presets",
    "current HEAD is 6b9c3a8 TASK-270 implement fast no-trade preflight presets",
    "current latest tag is v0.5.72-task-270-fast-no-trade-preflight-presets",
    "read-only telemetry aggregation snapshot records telemetry_aggregation_snapshot=true",
    "read-only telemetry aggregation snapshot records aggregated_errors_linked=true",
    "read-only telemetry aggregation snapshot records aggregated_metrics_linked=true",
    "read-only telemetry aggregation snapshot records all_observability_outputs_read_only=true",
    "read-only telemetry aggregation snapshot records all_authorizations_false=true",
    "read-only telemetry aggregation snapshot records no_trade_guard=active",
    "read-only telemetry aggregation snapshot records trading_authorization=false",
    "read-only telemetry aggregation snapshot records mt5_run_required=false",
    "read-only telemetry aggregation snapshot records evidence_generation=false",
    "read-only telemetry aggregation snapshot records manifest_generation=false",
    "read-only telemetry aggregation snapshot records Inventory only; no MT5 run; no trading authorization.",
    "LogReadOnlyTelemetryAggregationSnapshot",
    "OnTick telemetry aggregation remains gated by InpObservabilityLogOnTick",
    "TASK-271 preserves TASK-243 through TASK-270 no-trade observability outputs",
    "TASK-271 does not run MT5",
    "TASK-271 does not create manifest / fixture / report / directory",
    "TASK-271 does not copy external evidence",
    "TASK-271 does not add MQ5 / MQH files",
    "TASK-271 confirms MQ5 inventory remains 7 files",
    "TASK-271 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-272 implement read-only controller summary snapshot",
    "TASK-272 implement read-only controller summary snapshot",
    "TASK-272 is a low-risk MQ5 implementation slice",
    "TASK-272 implementation scope is limited to read-only controller summary snapshot consolidation",
    "TASK-271 completed read-only telemetry aggregation for error & metrics in the current working tree",
    "read-only controller summary snapshot records controller_summary_snapshot=true",
    "read-only controller summary snapshot records init_path_linked=true",
    "read-only controller summary snapshot records tick_path_linked=true",
    "read-only controller summary snapshot records deinit_path_linked=true",
    "read-only controller summary snapshot records all_observability_outputs_read_only=true",
    "read-only controller summary snapshot records all_authorizations_false=true",
    "read-only controller summary snapshot records no_trade_guard=active",
    "read-only controller summary snapshot records trading_authorization=false",
    "read-only controller summary snapshot records mt5_run_required=false",
    "read-only controller summary snapshot records evidence_generation=false",
    "read-only controller summary snapshot records manifest_generation=false",
    "read-only controller summary snapshot records Inventory only; no MT5 run; no trading authorization.",
    "LogReadOnlyControllerSummarySnapshot",
    "OnTick controller summary remains gated by InpObservabilityLogOnTick",
    "TASK-272 preserves TASK-243 through TASK-271 no-trade observability outputs",
    "TASK-272 does not run MT5",
    "TASK-272 does not create manifest / fixture / report / directory",
    "TASK-272 does not copy external evidence",
    "TASK-272 does not add MQ5 / MQH files",
    "TASK-272 confirms MQ5 inventory remains 7 files",
    "TASK-272 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-273 implement fast preflight review summary output",
    "TASK-273 implement fast preflight review summary output",
    "TASK-273 is a tooling efficiency task",
    "TASK-273 implementation scope is limited to fast no-trade preflight review summary output",
    "TASK-271/272 completed and closed together",
    "TASK-271/272 commit is e691022 TASK-271-272 implement read-only telemetry aggregation and controller summary snapshots",
    "TASK-271/272 tag is v0.5.73-task-271-272-read-only-telemetry-controller-summary",
    "current HEAD is e691022 TASK-271-272 implement read-only telemetry aggregation and controller summary snapshots",
    "current latest tag is v0.5.73-task-271-272-read-only-telemetry-controller-summary",
    "tools/run_fast_no_trade_preflight.py supports --review-summary",
    "--review-summary prints fast_no_trade_review_summary=true",
    "--review-summary prints suggested_git_add",
    "review summary is stdout-only",
    "TASK-273 does not modify MQ5 / MQH",
    "TASK-273 does not run MT5",
    "TASK-273 does not create manifest / fixture / report / directory",
    "TASK-273 does not copy external evidence",
    "TASK-273 confirms MQ5 inventory remains 7 files",
    "TASK-273 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-274 implement fast preflight Trae command preview output",
    "TASK-274 implement fast preflight Trae command preview output",
    "TASK-274 is a tooling efficiency task",
    "TASK-274 implementation scope is limited to fast preflight Trae command preview output",
    "TASK-273 completed fast preflight review summary output",
    "TASK-273 commit is 2008abe TASK-273 implement fast preflight review summary output",
    "TASK-273 tag is v0.5.74-task-273-fast-preflight-review-summary",
    "current HEAD is 2008abe TASK-273 implement fast preflight review summary output",
    "current latest tag is v0.5.74-task-273-fast-preflight-review-summary",
    "tools/run_fast_no_trade_preflight.py supports --emit-trae-command",
    "--emit-trae-command requires --task-id",
    "--emit-trae-command requires --commit-message",
    "--emit-trae-command requires --tag-name",
    "Trae command preview prints trae_command_preview=true",
    "Trae command preview prints command_block_start and command_block_end",
    "Trae command preview does not execute git add / commit / tag",
    "TASK-274 does not modify MQ5 / MQH",
    "TASK-274 does not run MT5",
    "TASK-274 does not create manifest / fixture / report / directory",
    "TASK-274 does not copy external evidence",
    "TASK-274 confirms MQ5 inventory remains 7 files",
    "TASK-274 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-275 implement fast preflight workflow presets",
    "TASK-275 implement fast preflight workflow presets",
    "TASK-275 is a tooling efficiency task",
    "TASK-275 implementation scope is limited to fast preflight workflow presets",
    "TASK-274 completed fast preflight Trae command preview output",
    "TASK-274 commit is de9b66b TASK-274 implement fast preflight Trae command preview output",
    "TASK-274 tag is v0.5.75-task-274-fast-preflight-trae-command-preview",
    "current HEAD is de9b66b TASK-274 implement fast preflight Trae command preview output",
    "current latest tag is v0.5.75-task-274-fast-preflight-trae-command-preview",
    "tools/run_fast_no_trade_preflight.py supports --workflow-preset",
    "--workflow-preset supports doc-state",
    "--workflow-preset supports tooling-preflight",
    "--workflow-preset supports mq5-observability",
    "workflow preset summary prints workflow_preset=<NAME>",
    "workflow preset summary prints allowed_presets=",
    "workflow preset summary prints allowed_change_guard=true",
    "workflow preset summary prints allowed_change_check=PASS/FAIL",
    "workflow preset summary prints fast_no_trade_review_summary=true",
    "workflow preset Trae command preview prints trae_command_preview=true",
    "workflow preset does not execute git add / commit / tag",
    "TASK-275 does not modify MQ5 / MQH",
    "TASK-275 does not run MT5",
    "TASK-275 does not create manifest / fixture / report / directory",
    "TASK-275 does not copy external evidence",
    "TASK-275 confirms MQ5 inventory remains 7 files",
    "TASK-275 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-276 implement fast preflight state report stdout",
    "TASK-276 implement fast preflight state report stdout",
    "TASK-276 is a tooling efficiency task",
    "TASK-276 implementation scope is limited to fast preflight state report stdout",
    "TASK-275 completed fast preflight workflow presets",
    "TASK-275 commit is 1bc332c TASK-275 implement fast preflight workflow presets",
    "TASK-275 tag is v0.5.76-task-275-fast-preflight-workflow-presets",
    "current HEAD is 1bc332c TASK-275 implement fast preflight workflow presets",
    "current latest tag is v0.5.76-task-275-fast-preflight-workflow-presets",
    "tools/run_fast_no_trade_preflight.py supports --state-report",
    "--state-report prints fast_no_trade_state_report=true",
    "--state-report prints current_head",
    "--state-report prints current_tags_at_head",
    "--state-report prints modified_files",
    "--state-report prints untracked_files",
    "--state-report prints allowed_change_guard",
    "--state-report prints allowed_change_check",
    "--state-report prints unexpected_changes_count",
    "--state-report prints mq5_inventory_expected=7 files",
    "--state-report prints trading_keywords=false",
    "--state-report prints mt5_run=false",
    "state report is stdout-only and does not create files",
    "state report does not execute git add / commit / tag",
    "TASK-276 does not modify MQ5 / MQH",
    "TASK-276 does not run MT5",
    "TASK-276 does not create manifest / fixture / report / directory",
    "TASK-276 does not copy external evidence",
    "TASK-276 confirms MQ5 inventory remains 7 files",
    "TASK-276 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-277 implement compact Trae handoff instruction output",
    "TASK-277 implement compact Trae handoff instruction output",
    "TASK-277 is a tooling efficiency task",
    "TASK-277 implementation scope is limited to compact Trae handoff instruction output",
    "TASK-276 completed fast preflight state report stdout",
    "TASK-276 commit is 8217709 TASK-276 implement fast preflight state report stdout",
    "TASK-276 tag is v0.5.77-task-276-fast-preflight-state-report",
    "current HEAD is 8217709 TASK-276 implement fast preflight state report stdout",
    "current latest tag is v0.5.77-task-276-fast-preflight-state-report",
    "tools/run_fast_no_trade_preflight.py supports --emit-trae-handoff",
    "--emit-trae-handoff prints trae_handoff_instruction=true",
    "--emit-trae-handoff prints handoff_block_start",
    "--emit-trae-handoff prints 发给：Trae",
    "--emit-trae-handoff prints a compact Trae review / validation / commit / tag instruction block",
    "--emit-trae-handoff requires --state-report",
    "--emit-trae-handoff requires --review-summary",
    "--emit-trae-handoff requires --emit-trae-command",
    "--emit-trae-handoff requires --check-allowed-changes",
    "--emit-trae-handoff requires --task-id / --commit-message / --tag-name",
    "--emit-trae-handoff requires allowed_change_check=PASS",
    "--emit-trae-handoff requires suggested_git_add not BLOCKED and not SKIPPED",
    "handoff output is stdout-only and does not create files",
    "handoff output does not execute git add / commit / tag",
    "TASK-277 does not modify MQ5 / MQH",
    "TASK-277 does not run MT5",
    "TASK-277 does not create manifest / fixture / report / directory",
    "TASK-277 does not copy external evidence",
    "TASK-277 confirms MQ5 inventory remains 7 files",
    "TASK-277 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-278 implement compact preflight combined report output",
    "TASK-278 implement compact preflight combined report output",
    "TASK-278 is a tooling efficiency task",
    "TASK-278 implementation scope is limited to compact preflight combined report output",
    "TASK-277 completed compact Trae handoff instruction output",
    "TASK-277 commit is 90bb6b8 TASK-277 implement compact Trae handoff instruction output",
    "TASK-277 tag is v0.5.78-task-277-fast-preflight-trae-handoff",
    "current HEAD is 90bb6b8 TASK-277 implement compact Trae handoff instruction output",
    "current latest tag is v0.5.78-task-277-fast-preflight-trae-handoff",
    "tools/run_fast_no_trade_preflight.py supports --compact-report",
    "new parameter is --compact-report",
    "--compact-report prints fast_no_trade_compact_report=true",
    "--compact-report includes fast_no_trade_state_report",
    "--compact-report prints current_head / current_tags_at_head",
    "--compact-report prints workflow_preset / profile",
    "--compact-report prints allowed_change_guard / allowed_change_check / unexpected_changes_count",
    "--compact-report prints modified_files / untracked_files",
    "--compact-report includes Trae command preview",
    "--compact-report includes review-summary",
    "--compact-report prints mq5_inventory_expected=7 files",
    "--compact-report prints trading_keywords=false",
    "compact report is stdout-only and does not create files",
    "compact report does not execute git add / commit / tag",
    "TASK-278 does not modify MQ5 / MQH",
    "TASK-278 does not run MT5",
    "TASK-278 does not create manifest / fixture / report / directory",
    "TASK-278 does not copy external evidence",
    "TASK-278 confirms MQ5 inventory remains 7 files",
    "TASK-278 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-279 implement release bundle summary compression",
    "TASK-279 implement release bundle summary compression",
    "TASK-279 is a tooling efficiency task",
    "TASK-279 implementation scope is limited to release bundle summary compression",
    "TASK-278 completed compact preflight combined report output",
    "TASK-278 commit is 7e93d14 TASK-278 implement compact preflight combined report output",
    "TASK-278 tag is v0.5.79-task-278-compact-preflight-report",
    "current HEAD is 7e93d14 TASK-278 implement compact preflight combined report output",
    "current latest tag is v0.5.79-task-278-compact-preflight-report",
    "tools/run_release_validation_bundle.py supports --compressed-summary",
    "new parameter is --compressed-summary",
    "--compressed-summary prints release_validation_compressed_summary=true",
    "--compressed-summary includes fast_no_trade_state_report",
    "--compressed-summary prints workflow_preset",
    "--compressed-summary prints allowed_change_check",
    "--compressed-summary prints mq5_inventory_expected=7 files",
    "--compressed-summary prints trading_keywords=false",
    "--compressed-summary prints project-state-docs / project-state-docs-self-test",
    "--compressed-summary includes Trae command preview",
    "--compressed-summary includes review summary",
    "compressed summary is stdout-only and does not create files",
    "compressed summary does not execute git add / commit / tag",
    "TASK-279 does not modify MQ5 / MQH",
    "TASK-279 does not run MT5",
    "TASK-279 does not create manifest / fixture / report / directory",
    "TASK-279 does not copy external evidence",
    "TASK-279 confirms MQ5 inventory remains 7 files",
    "TASK-279 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-280 implement no-trade development workflow closure audit",
    "TASK-280 implement no-trade development workflow closure audit",
    "TASK-280 is a tooling + audit task",
    "TASK-280 implementation scope is limited to no-trade development workflow closure audit",
    "TASK-279 completed release bundle summary compression",
    "TASK-279 baseline commit is 7e93d14 TASK-278 implement release bundle summary compression",
    "TASK-279 tag is v0.5.79-task-278-compact-preflight-report",
    "current HEAD is 7e93d14 TASK-278 implement release bundle summary compression",
    "current latest tag is v0.5.79-task-278-compact-preflight-report",
    "tools/run_fast_no_trade_preflight.py supports --workflow-closure-audit",
    "tools/run_release_validation_bundle.py supports --workflow-closure-audit",
    "new parameter is --workflow-closure-audit",
    "--workflow-closure-audit prints workflow_closure_audit=true",
    "--workflow-closure-audit prints release_ready_closure_audit=true",
    "--workflow-closure-audit includes fast_no_trade_state_report",
    "--workflow-closure-audit includes fast_no_trade_review_summary",
    "--workflow-closure-audit prints workflow_preset",
    "--workflow-closure-audit prints allowed_change_check",
    "--workflow-closure-audit includes Trae handoff block status",
    "--workflow-closure-audit includes validator/self-test summary",
    "--workflow-closure-audit prints mq5_inventory_expected=7 files",
    "--workflow-closure-audit prints trading_keywords=false",
    "workflow closure audit is stdout-only and does not create files",
    "workflow closure audit does not execute git add / commit / tag",
    "TASK-280 does not modify MQ5 / MQH",
    "TASK-280 does not run MT5",
    "TASK-280 does not create manifest / fixture / report / directory",
    "TASK-280 does not copy external evidence",
    "TASK-280 confirms MQ5 inventory remains 7 files",
    "TASK-280 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-DOC-281 freeze no-trade workflow closure state after TASK-280",
    "TASK-DOC-281 freeze no-trade workflow closure state after TASK-280",
    "TASK-DOC-281 is doc/tooling state sync only",
    "TASK-280 completed no-trade development workflow closure audit",
    "TASK-280 commit is 304b4aa TASK-280 implement no-trade development workflow closure audit",
    "TASK-280 tag is v0.5.80-task-280-no-trade-workflow-closure-audit",
    "fast-no-trade-dev profile is the default fast validation entry",
    "run_fast_no_trade_preflight.py supports --workflow-preset",
    "run_fast_no_trade_preflight.py supports --state-report",
    "run_fast_no_trade_preflight.py supports --review-summary",
    "run_fast_no_trade_preflight.py supports --emit-trae-command",
    "run_fast_no_trade_preflight.py supports --emit-trae-handoff",
    "run_fast_no_trade_preflight.py supports --compact-report",
    "run_fast_no_trade_preflight.py supports --workflow-closure-audit",
    "run_release_validation_bundle.py supports --compressed-summary",
    "run_release_validation_bundle.py supports --workflow-closure-audit",
    "run_release_validation_bundle.py supports --profile fast-no-trade-dev",
    "current default Codex validation mode: py tools/run_release_validation_bundle.py --compressed-summary --workflow-closure-audit --profile fast-no-trade-dev",
    "current default Trae review mode uses generated Trae handoff block, continuous commit/tag, and validates tag points to HEAD",
    "TASK-DOC-281 confirms MQ5 inventory remains 7 files",
    "TASK-DOC-281 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-DOC-281 does not modify MQ5 / MQH",
    "TASK-DOC-281 does not run MT5",
    "TASK-DOC-281 does not create manifest / fixture / report / directory",
    "TASK-DOC-281 does not copy external evidence",
    "future preflight tooling optimization is frozen unless validation efficiency becomes bottleneck",
    "next candidate should shift to read-only compile-readiness / MQ5 static interface consistency, not more workflow tooling",
    "current task is TASK-282 implement read-only compile-readiness boundary",
    "TASK-282 implement read-only compile-readiness boundary",
    "TASK-282 is a read-only boundary verification task",
    "TASK-282 objective is to build MQ5 EA compile-readiness boundary",
    "compile-readiness boundary verifies no-trade / read-only observability scaffold safety",
    "compile-readiness boundary verifies MQ5 static interface consistency",
    "TASK-282 keeps the fast no-trade workflow tooling baseline",
    "TASK-282 baseline commit is 304b4aa TASK-280 implement no-trade development workflow closure audit",
    "TASK-282 baseline tag is v0.5.80-task-280-no-trade-workflow-closure-audit",
    "run_release_validation_bundle.py includes read-only compile-readiness boundary check",
    "fast-no-trade-dev profile includes read-only compile-readiness boundary check",
    "compile-readiness check is read-only and stdout-only",
    "compile-readiness check does not run MT5",
    "compile-readiness check does not modify MQ5 / MQH",
    "compile-readiness check does not create manifest / fixture / report / directory",
    "compile-readiness check does not copy external evidence",
    "compile-readiness check confirms MQ5 inventory remains 7 files",
    "compile-readiness check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-282 does not modify MQ5 / MQH",
    "TASK-282 does not run MT5",
    "TASK-282 does not execute backtest",
    "TASK-282 does not enter simulated trading",
    "TASK-282 does not enter real trading",
    "TASK-282 does not create manifest / fixture / report / directory",
    "TASK-282 does not copy external evidence",
    "next candidate should remain read-only MQ5 static interface consistency unless ChatGPT defines a new boundary",
    "current task is TASK-283 implement MQ5 static interface consistency audit",
    "TASK-283 implement MQ5 static interface consistency audit",
    "TASK-283 is a read-only / no-trade MQ5 interface audit",
    "TASK-283 objective is static consistency check for MQ5 core module interfaces",
    "MQ5 static interface consistency audit verifies TradingSystem.mq5 routes OnInit / OnTick / OnDeinit through EaController",
    "MQ5 static interface consistency audit verifies EaController includes InputConfig / Logger / SignalEngine / RiskManager / ExecutionManager",
    "MQ5 static interface consistency audit verifies Logger helper availability for no-trade observability scaffold",
    "MQ5 static interface consistency audit verifies SignalEngine / RiskManager / ExecutionManager Init(Logger &log) interfaces",
    "MQ5 static interface consistency audit verifies read-only status snapshot interfaces remain aligned",
    "TASK-283 baseline commit is 304b4aa TASK-280 implement no-trade development workflow closure audit",
    "TASK-283 baseline tag is v0.5.80-task-280-no-trade-workflow-closure-audit",
    "run_release_validation_bundle.py includes mq5-static-interface-consistency check",
    "fast-no-trade-dev profile includes mq5-static-interface-consistency check",
    "mq5-static-interface-consistency check is read-only and stdout-only",
    "mq5-static-interface-consistency check does not run MT5",
    "mq5-static-interface-consistency check does not modify MQ5 / MQH",
    "mq5-static-interface-consistency check does not create manifest / fixture / report / directory",
    "mq5-static-interface-consistency check does not copy external evidence",
    "mq5-static-interface-consistency check confirms MQ5 inventory remains 7 files",
    "mq5-static-interface-consistency check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-283 does not modify MQ5 / MQH",
    "TASK-283 does not run MT5",
    "TASK-283 does not execute backtest",
    "TASK-283 does not enter simulated trading",
    "TASK-283 does not enter real trading",
    "TASK-283 does not create manifest / fixture / report / directory",
    "TASK-283 does not copy external evidence",
    "current task is TASK-284 implement MQ5 static include dependency consistency audit",
    "TASK-284 implement MQ5 static include dependency consistency audit",
    "TASK-283 completed",
    "TASK-283 completion commit is 1dbf78f TASK-283 implement MQ5 static interface consistency audit",
    "TASK-283 completion tag is v0.5.82-task-283-mq5-static-interface-audit",
    "TASK-284 is a read-only static tooling task",
    "TASK-284 adds mq5-static-include-consistency check",
    "MQ5 static include dependency consistency audit verifies include paths resolve within mq5",
    "MQ5 static include dependency consistency audit rejects absolute include paths",
    "MQ5 static include dependency consistency audit rejects docs / tools / backtest include paths",
    "MQ5 static include dependency consistency audit confirms MQ5 inventory remains 7 files",
    "run_release_validation_bundle.py includes mq5-static-include-consistency check",
    "fast-no-trade-dev profile includes mq5-static-include-consistency check",
    "mq5-static-include-consistency check is read-only and stdout-only",
    "mq5-static-include-consistency check does not run MT5",
    "mq5-static-include-consistency check does not execute MQL5 compile",
    "mq5-static-include-consistency check does not modify MQ5 / MQH",
    "mq5-static-include-consistency check does not create manifest / fixture / report / directory",
    "mq5-static-include-consistency check does not copy external evidence",
    "mq5-static-include-consistency check confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-284 does not modify MQ5 / MQH",
    "TASK-284 does not run MT5",
    "TASK-284 does not execute MQL5 compile",
    "TASK-284 does not execute backtest",
    "TASK-284 does not enter simulated trading",
    "TASK-284 does not enter real trading",
    "TASK-284 does not create manifest / fixture / report / directory",
    "TASK-284 does not copy external evidence",
    "v0.5.82-task-283-mq5-static-interface-audit",
    "MQ5 inventory remains 7 files",
    "Inventory only; no MT5 run; no trading authorization.",
    "next candidate must be defined by ChatGPT before TASK-284",
    "current task is TASK-285 implement read-only controller/logger duplicate output reduction contract",
    "TASK-285 implement read-only controller/logger duplicate output reduction contract",
    "TASK-284 completed",
    "TASK-284 completion commit is 4636254 TASK-284 implement MQ5 static include dependency consistency audit",
    "TASK-284 completion tag is v0.5.83-task-284-mq5-static-include-consistency",
    "current HEAD is 4636254 TASK-284 implement MQ5 static include dependency consistency audit",
    "current tag is v0.5.83-task-284-mq5-static-include-consistency",
    "TASK-285 is a low-risk MQ5 implementation slice",
    "TASK-285 implements read-only controller/logger duplicate output reduction contract",
    "read-only controller/logger duplicate output reduction contract",
    "duplicate_output_guard=active",
    "controller_logger_deduplication=true",
    "observability_output_reduction_snapshot=true",
    "tick_output_requires_InpObservabilityLogOnTick=true",
    "TASK-285 preserves TASK-243 through TASK-284 no-trade observability contract fields",
    "TASK-285 does not run MT5",
    "TASK-285 does not execute MQL5 compile",
    "TASK-285 does not execute backtest",
    "TASK-285 does not enter simulated trading",
    "TASK-285 does not enter real trading",
    "TASK-285 does not create manifest / fixture / report / directory",
    "TASK-285 does not copy external evidence",
    "TASK-285 does not modify forbidden MQ5 / MQH files",
    "v0.5.83-task-284-mq5-static-include-consistency",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "no MT5 run",
    "no MQL5 compile",
    "no trading authorization",
    "next candidate must be defined by ChatGPT before TASK-286",
    "current task is TASK-286 implement MQ5 lifecycle route consistency audit",
    "TASK-286 implement MQ5 lifecycle route consistency audit",
    "TASK-285 completed",
    "TASK-285 completion commit is 762041a TASK-285 implement read-only controller/logger duplicate output reduction contract",
    "TASK-285 completion tag is v0.5.84-task-285-controller-logger-output-reduction",
    "current HEAD is 762041a TASK-285 implement read-only controller/logger duplicate output reduction contract",
    "current tag is v0.5.84-task-285-controller-logger-output-reduction",
    "TASK-286 is a read-only static tooling task",
    "TASK-286 adds mq5-lifecycle-route-consistency check",
    "MQ5 lifecycle route consistency audit verifies OnInit / OnTick / OnDeinit route through EaController",
    "mq5-lifecycle-route-consistency check is read-only and stdout-only",
    "mq5-lifecycle-route-consistency check does not run MT5",
    "mq5-lifecycle-route-consistency check does not execute MQL5 compile",
    "mq5-lifecycle-route-consistency check does not modify MQ5 / MQH",
    "fast-no-trade-dev profile includes mq5-lifecycle-route-consistency check",
    "mq5-lifecycle-route-consistency PASS",
    "OnInit",
    "OnTick",
    "OnDeinit",
    "v0.5.84-task-285-controller-logger-output-reduction",
    "next candidate must be defined by ChatGPT before TASK-287",
    "current task is TASK-287 implement MQ5 observability helper call consistency audit",
    "TASK-287 implement MQ5 observability helper call consistency audit",
    "TASK-286 completed",
    "TASK-286 completion commit is a870547 TASK-286 implement MQ5 lifecycle route consistency audit",
    "TASK-286 completion tag is v0.5.85-task-286-mq5-lifecycle-route-consistency",
    "current HEAD is a870547 TASK-286 implement MQ5 lifecycle route consistency audit",
    "current tag is v0.5.85-task-286-mq5-lifecycle-route-consistency",
    "TASK-287 is a read-only static tooling task",
    "TASK-287 adds mq5-observability-helper-consistency check",
    "MQ5 observability helper call consistency audit verifies EaController Logger helper calls are defined in Logger.mqh",
    "mq5-observability-helper-consistency check is read-only and stdout-only",
    "mq5-observability-helper-consistency check does not run MT5",
    "mq5-observability-helper-consistency check does not execute MQL5 compile",
    "mq5-observability-helper-consistency check does not modify MQ5 / MQH",
    "fast-no-trade-dev profile includes mq5-observability-helper-consistency check",
    "logger_helper_consistency=true",
    "mq5-observability-helper-consistency PASS",
    "v0.5.85-task-286-mq5-lifecycle-route-consistency",
    "next candidate must be defined by ChatGPT before TASK-288",
    "current task is TASK-288 implement MQ5 read-only observability telemetry final aggregation",
    "TASK-288 implement MQ5 read-only observability telemetry final aggregation",
    "TASK-287 completed",
    "current HEAD is a870547 TASK-286 implement MQ5 lifecycle route consistency audit",
    "current tag is v0.5.85-task-286-mq5-lifecycle-route-consistency",
    "TASK-288 is a tooling efficiency / read-only telemetry task",
    "TASK-288 adds mq5-telemetry-aggregation check",
    "mq5-telemetry-aggregation check is read-only and stdout-only",
    "fast_no_trade_telemetry_aggregation=true",
    "all_observability_outputs_read_only=true",
    "mq5-telemetry-aggregation PASS",
    "TASK-288 does not run MT5",
    "TASK-288 does not execute MQL5 compile",
    "TASK-288 does not modify MQ5 / MQH",
    "TASK-288 does not create manifest / fixture / report / directory",
    "TASK-288 does not copy external evidence",
    "next candidate must be defined by ChatGPT before TASK-289",
    "current task is TASK-289 reconcile TASK-287 observability helper validator tracking gap",
    "TASK-289 reconcile TASK-287 observability helper validator tracking gap",
    "TASK-288 completed",
    "TASK-288 completion commit is afaf7d3 TASK-288 implement MQ5 read-only observability telemetry final aggregation",
    "TASK-288 completion tag is v0.5.87-task-288-mq5-telemetry-final-aggregation",
    "current HEAD is afaf7d3 TASK-288 implement MQ5 read-only observability telemetry final aggregation",
    "current tag is v0.5.87-task-288-mq5-telemetry-final-aggregation",
    "TASK-289 is a reconciliation / tooling consistency task",
    "TASK-287 helper consistency validator was left as an untracked item",
    "TASK-289 brings tools/validate_mq5_observability_helper_consistency.py into tracking scope",
    "TASK-289 brings tools/test_validate_mq5_observability_helper_consistency.py into tracking scope",
    "mq5-observability-helper-consistency check remains read-only and stdout-only",
    "fast-no-trade-dev profile includes mq5-observability-helper-consistency check",
    "workflow-closure-audit includes mq5-observability-helper-consistency check",
    "TASK-289 does not recreate old v0.5.86 tag",
    "TASK-289 does not move historical tags",
    "TASK-289 does not run MT5",
    "TASK-289 does not execute MQL5 compile",
    "TASK-289 does not modify MQ5 / MQH",
    "TASK-289 does not create manifest / fixture / report / directory",
    "TASK-289 does not copy external evidence",
    "next candidate must be defined by ChatGPT before TASK-290",
    "current task is TASK-290 implement final milestone closure / release-ready state report",
    "TASK-290 implement final milestone closure / release-ready state report",
    "TASK-289 completed",
    "TASK-289 completion commit is 098a985 TASK-289 reconcile observability helper validator tracking gap",
    "TASK-289 completion tag is v0.5.88-task-289-reconcile-observability-helper-validator-tracking",
    "current HEAD is 098a985 TASK-289 reconcile observability helper validator tracking gap",
    "current tag is v0.5.88-task-289-reconcile-observability-helper-validator-tracking",
    "TASK-290 is a tooling + release audit task",
    "TASK-290 adds --final-milestone-report",
    "final_milestone_report=true",
    "release_ready_milestone_closure=true",
    "TASK-266 through TASK-289 closure summary",
    "Trae handoff blocks",
    "validator/self-test results",
    "mq5-inventory PASS",
    "mq5-no-trade-observability PASS",
    "mq5-static-interface-consistency PASS",
    "mq5-static-include-consistency PASS",
    "mq5-lifecycle-route-consistency PASS",
    "mq5-observability-helper-consistency PASS",
    "mq5-telemetry-aggregation PASS",
    "project-state-docs PASS",
    "project-state-docs-self-test PASS",
    "TASK-290 does not run MT5",
    "TASK-290 does not execute MQL5 compile",
    "TASK-290 does not modify MQ5 / MQH",
    "TASK-290 does not create manifest / fixture / report / directory",
    "TASK-290 does not copy external evidence",
    "TASK-290 confirms MQ5 inventory remains 7 files",
    "TASK-290 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "next candidate must be defined by ChatGPT after TASK-290",
    "current task is TASK-291 implement MQ5 static symbol reference consistency audit",
    "TASK-291 implement MQ5 static symbol reference consistency audit",
    "TASK-290 completed",
    "TASK-290 completion commit is f8b4a8f TASK-290 implement final milestone closure / release-ready state report",
    "TASK-290 completion tag is v0.5.89-task-290-final-no-trade-workflow-milestone-report",
    "current HEAD is f8b4a8f TASK-290 implement final milestone closure / release-ready state report",
    "current tag is v0.5.89-task-290-final-no-trade-workflow-milestone-report",
    "TASK-291 is a read-only static tooling task",
    "TASK-291 adds mq5-static-symbol-consistency check",
    "MQ5 static symbol reference consistency audit",
    "mq5-static-symbol-consistency check is read-only and stdout-only",
    "mq5-static-symbol-consistency PASS",
    "symbol_reference_consistency=true",
    "compile_readiness_static_only=true",
    "fast-no-trade-dev profile includes mq5-static-symbol-consistency check",
    "TASK-291 does not run MT5",
    "TASK-291 does not execute MQL5 compile",
    "TASK-291 does not modify MQ5 / MQH",
    "TASK-291 does not create manifest / fixture / report / directory",
    "TASK-291 does not copy external evidence",
    "TASK-291 confirms MQ5 inventory remains 7 files",
    "TASK-291 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-292 implement MQ5 static compile-readiness aggregate audit",
    "TASK-292 implement MQ5 static compile-readiness aggregate audit",
    "TASK-291 completed",
    "TASK-291 completion commit is d199707 TASK-291 implement MQ5 static symbol reference consistency audit",
    "TASK-291 completion tag is v0.5.90-task-291-mq5-static-symbol-consistency",
    "current HEAD is d199707 TASK-291 implement MQ5 static symbol reference consistency audit",
    "current tag is v0.5.90-task-291-mq5-static-symbol-consistency",
    "TASK-292 is a read-only static tooling task",
    "TASK-292 adds mq5-static-compile-readiness check",
    "MQ5 static compile-readiness aggregate audit",
    "mq5-static-compile-readiness check is read-only and stdout-only",
    "mq5-static-compile-readiness PASS",
    "compile_readiness_static_only=true",
    "mql5_compile_executed=false",
    "fast-no-trade-dev profile includes mq5-static-compile-readiness check",
    "TASK-292 does not run MT5",
    "TASK-292 does not execute MQL5 compile",
    "TASK-292 does not modify MQ5 / MQH",
    "TASK-292 does not create manifest / fixture / report / directory",
    "TASK-292 does not copy external evidence",
    "TASK-292 confirms MQ5 inventory remains 7 files",
    "TASK-292 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-293 implement MQ5 compile-readiness final milestone summary report",
    "TASK-293 implement MQ5 compile-readiness final milestone summary report",
    "TASK-292 completed",
    "TASK-292 completion commit is 74ce782 TASK-292 implement MQ5 static compile-readiness aggregate audit",
    "TASK-292 completion tag is v0.5.91-task-292-mq5-static-compile-readiness",
    "current HEAD is 74ce782 TASK-292 implement MQ5 static compile-readiness aggregate audit",
    "current tag is v0.5.91-task-292-mq5-static-compile-readiness",
    "TASK-293 is a tooling + release audit task",
    "TASK-293 adds mq5-static-compile-readiness-summary check",
    "TASK-293 adds --final-milestone-summary in release validation bundle",
    "MQ5 compile-readiness final milestone summary report",
    "final_milestone_summary=true",
    "tasks_covered=TASK-266..TASK-292",
    "fast_no_trade_state_report=true",
    "fast_no_trade_review_summary=true",
    "trae_handoff_summary=true",
    "workflow_closure_audit=true",
    "validator_self_test_summary=PASS",
    "mq5-static-compile-readiness-summary PASS",
    "milestone_closure_ready=PASS",
    "TASK-293 does not run MT5",
    "TASK-293 does not execute MQL5 compile",
    "TASK-293 does not modify MQ5 / MQH",
    "TASK-293 does not create manifest / fixture / report / directory",
    "TASK-293 does not copy external evidence",
    "TASK-293 confirms MQ5 inventory remains 7 files",
    "TASK-293 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "current task is TASK-DOC-294 create future MQL5 compile-only boundary packet",
    "TASK-DOC-294 create future MQL5 compile-only boundary packet",
    "TASK-293 completed",
    "TASK-293 completion commit is 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report",
    "TASK-293 completion tag is v0.5.92-task-293-mq5-compile-readiness-final-summary",
    "current HEAD is 47d942c TASK-293 implement MQ5 compile-readiness final milestone summary report",
    "current tag is v0.5.92-task-293-mq5-compile-readiness-final-summary",
    "TASK-DOC-294 is planning-only / boundary-only",
    "TASK-DOC-294 creates docs/V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md",
    "TASK-DOC-294 defines a future MQL5 compile-only candidate",
    "TASK-DOC-294 is not implementation authorization",
    "TASK-DOC-294 is not MT5 run authorization",
    "TASK-DOC-294 is not Strategy Tester authorization",
    "TASK-DOC-294 is not backtest authorization",
    "TASK-DOC-294 is not simulation trading authorization",
    "TASK-DOC-294 is not real trading authorization",
    "TASK-DOC-294 is not evidence generation authorization",
    "TASK-DOC-294 is not manifest generation authorization",
    "TASK-DOC-294 is not external evidence copy authorization",
    "mql5-compile-only-boundary check is added to release validation bundle",
    "mq5-compile-readiness-final-summary alias check remains read-only and stdout-only",
    "fast-no-trade-dev profile includes mql5-compile-only-boundary check",
    "no compile executed in TASK-DOC-294",
    "no MetaEditor executed in TASK-DOC-294",
    "no MetaEditor execution",
    "no .ex5 artifact generated",
    "no MQL5 compile",
    "TASK-DOC-294 does not run MT5",
    "TASK-DOC-294 does not execute MQL5 compile",
    "TASK-DOC-294 does not modify MQ5 / MQH",
    "TASK-DOC-294 does not create manifest / fixture / report / directory",
    "TASK-DOC-294 does not copy external evidence",
    "future compile-only task must be separately authorized by GPT",
    "future compile-only task must remain no-trade",
    "future compile-only task must not create manifest / evidence / report",
    "future compile-only task must only produce stdout / terminal result unless separately authorized",
    "TASK-295 must not be entered directly without a new GPT boundary",
    "GPT must define a separate future boundary before TASK-295",
    "current task is TASK-295 implement MQL5 compile-only command discovery boundary",
    "TASK-295 implement MQL5 compile-only command discovery boundary",
    "TASK-DOC-294 completed",
    "TASK-DOC-294 completion commit is 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet",
    "TASK-DOC-294 completion tag is v0.5.93-task-294-future-mql5-compile-only-boundary",
    "current HEAD is 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet",
    "current tag is v0.5.93-task-294-future-mql5-compile-only-boundary",
    "TASK-295 is command-discovery-only",
    "TASK-295 creates docs/V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
    "mql5-compile-only-command-discovery check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-command-discovery check",
    "mql5-compile-only-command-discovery PASS",
    "metaeditor_executed=false",
    "mql5_compile_executed=false",
    "no MT5 run",
    "no MQL5 compile",
    "no MetaEditor execution",
    "no .ex5 artifact",
    "no compile log",
    "no trading authorization",
    "TASK-295 no trading authorization",
    "TASK-295 does not modify MQ5 / MQH",
    "TASK-295 does not run MT5",
    "TASK-295 does not execute MetaEditor",
    "TASK-295 does not execute MQL5 compile",
    "TASK-295 does not create .ex5 artifact",
    "TASK-295 does not create compile log",
    "TASK-295 does not create manifest / fixture / report / directory",
    "TASK-295 does not copy external evidence",
    "TASK-295 confirms MQ5 inventory remains 7 files",
    "TASK-295 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-296 must not be entered directly",
    "current task is TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "TASK-295 completed",
    "TASK-295 completion commit is acda17c TASK-295 implement MQL5 compile-only command discovery boundary",
    "TASK-295 completion tag is v0.5.94-task-295-mql5-compile-only-command-discovery",
    "current HEAD is acda17c TASK-295 implement MQL5 compile-only command discovery boundary",
    "current tag is v0.5.94-task-295-mql5-compile-only-command-discovery",
    "TASK-296 is artifact-quarantine-only",
    "TASK-296 creates docs/V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
    "mql5-compile-only-artifact-quarantine check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-artifact-quarantine check",
    "mql5-compile-only-artifact-quarantine PASS",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "TASK-296 does not modify MQ5 / MQH",
    "TASK-296 does not run MT5",
    "TASK-296 does not execute MetaEditor",
    "TASK-296 does not execute MQL5 compile",
    "TASK-296 does not create .ex5 artifact",
    "TASK-296 does not create compile log",
    "TASK-296 does not create manifest / fixture / report / directory",
    "TASK-296 does not copy external evidence",
    "TASK-296 confirms MQ5 inventory remains 7 files",
    "TASK-296 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-297 must be separately authorized by GPT before any compile execution",
    "TASK-297 must not be entered directly",
    "future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes",
    "future compile-only execution must check repository has no .ex5 before and after compile",
    "future compile-only execution must check repository has no compile log before and after compile",
    "compile-only command may be executed only after GPT defines TASK-297 boundary",
    "post-compile check: no MT5 run",
    "post-compile check: no Strategy Tester",
    "post-compile check: no trading",
    "current task is TASK-297 implement future MQL5 compile-only execution boundary",
    "TASK-297 implement future MQL5 compile-only execution boundary",
    "TASK-296 completed",
    "TASK-296 completion commit is 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "TASK-296 completion tag is v0.5.95-task-296-mql5-compile-only-artifact-quarantine",
    "current HEAD is 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "current tag is v0.5.95-task-296-mql5-compile-only-artifact-quarantine",
    "TASK-297 is compile-only-task",
    "TASK-297 is future compile-only candidate",
    "TASK-297 requires GPT explicit authorization",
    "TASK-297 confirms artifact quarantine checked",
    "TASK-297 creates docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
    "mql5-compile-only-execution-boundary check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-execution-boundary check",
    "mql5-compile-only-execution-boundary PASS",
    "TASK-297 does not modify MQ5 / MQH",
    "TASK-297 does not run MT5",
    "TASK-297 does not execute MetaEditor",
    "TASK-297 does not execute MQL5 compile",
    "TASK-297 does not create .ex5 artifact",
    "TASK-297 does not create compile log",
    "TASK-297 does not create manifest / fixture / report / directory",
    "TASK-297 does not copy external evidence",
    "TASK-297 confirms MQ5 inventory remains 7 files",
    "TASK-297 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-298 must be separately authorized by GPT",
    "future TASK-298 must not be entered directly",
    "current task is TASK-298 implement MQL5 compile-only dry-run simulation",
    "TASK-298 implement MQL5 compile-only dry-run simulation",
    "TASK-298 is dry-run-only",
    "TASK-298 enforces artifact-quarantine",
    "TASK-298 uses stdout-only simulation",
    "TASK-298 creates docs/V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md",
    "mql5-compile-only-dryrun check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-dryrun check",
    "mql5-compile-only-dryrun PASS",
    "TASK-298 does not modify MQ5 / MQH",
    "TASK-298 does not run MT5",
    "TASK-298 does not execute MetaEditor",
    "TASK-298 does not execute MQL5 compile",
    "TASK-298 does not create .ex5 artifact",
    "TASK-298 does not create compile log",
    "TASK-298 does not create manifest / fixture / report / directory",
    "TASK-298 does not copy external evidence",
    "TASK-298 confirms MQ5 inventory remains 7 files",
    "TASK-298 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-299 must not be entered directly",
    "current task is TASK-299 reconcile TASK-297 MQL5 compile-only execution boundary tracking gap",
    "TASK-299 reconcile TASK-297 MQL5 compile-only execution boundary tracking gap",
    "TASK-298 completed",
    "TASK-298 completion commit is 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary",
    "TASK-298 completion tag is v0.5.96-task-298-mql5-compile-only-dryrun",
    "current HEAD is 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary",
    "current tag is v0.5.96-task-298-mql5-compile-only-dryrun",
    "TASK-297 files were untracked tracking gap items before TASK-299 reconciliation",
    "TASK-299 reconciles docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
    "TASK-299 reconciles tools/validate_mql5_compile_only_execution_boundary.py",
    "TASK-299 reconciles tools/test_validate_mql5_compile_only_execution_boundary.py",
    "TASK-299 does not recreate old TASK-297 tag",
    "TASK-299 does not move historical tags",
    "TASK-299 keeps mql5-compile-only-execution-boundary in release validation bundle",
    "workflow-closure-audit includes mql5-compile-only-execution-boundary check",
    "TASK-299 does not modify MQ5 / MQH",
    "TASK-299 does not run MT5",
    "TASK-299 does not execute MetaEditor",
    "TASK-299 does not execute MQL5 compile",
    "TASK-299 does not create .ex5 artifact",
    "TASK-299 does not create compile log",
    "TASK-299 does not create manifest / fixture / report / directory",
    "TASK-299 does not copy external evidence",
    "TASK-299 confirms MQ5 inventory remains 7 files",
    "TASK-299 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-300 must not be entered directly",
    "current task is TASK-300 implement MQL5 compile-only dry-run execution simulation",
    "TASK-300 implement MQL5 compile-only dry-run execution simulation",
    "TASK-299 completed",
    "TASK-299 reconciled TASK-297 MQL5 compile-only execution boundary tracking gap",
    "current HEAD is 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary",
    "current tag is v0.5.96-task-298-mql5-compile-only-dryrun",
    "TASK-300 creates docs/V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md",
    "mql5-compile-only-dryrun-execution check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-dryrun-execution check",
    "workflow-closure-audit includes mql5-compile-only-dryrun-execution check",
    "mql5-compile-only-dryrun-execution PASS",
    "TASK-300 is dry-run-execution-only",
    "TASK-300 uses stdout-only simulation",
    "TASK-300 enforces artifact-quarantine",
    "TASK-300 generates stdout-only candidate output",
    "TASK-300 does not modify MQ5 / MQH",
    "TASK-300 does not run MT5",
    "TASK-300 does not execute MetaEditor",
    "TASK-300 does not execute MQL5 compile",
    "TASK-300 does not create .ex5 artifact",
    "TASK-300 does not create compile log",
    "TASK-300 does not create manifest / fixture / report / directory",
    "TASK-300 does not copy external evidence",
    "TASK-300 confirms MQ5 inventory remains 7 files",
    "TASK-300 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-301 must not be entered directly",
    "current task is TASK-301 create v0.6.0 compile-readiness planning packet",
    "TASK-301 create v0.6.0 compile-readiness planning packet",
    "TASK-299-300 reconciliation completed",
    "TASK-299-300 completion commit is fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation",
    "TASK-299-300 completion tag is v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation",
    "current HEAD is fd10dac TASK-299-300 reconcile MQL5 compile-only boundary tracking and dry-run simulation",
    "current tag is v0.5.97-task-299-300-mql5-compile-only-boundary-dryrun-reconciliation",
    "TASK-301 creates docs/V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md",
    "v060-compile-readiness-planning check is added to release validation bundle",
    "fast-no-trade-dev profile includes v060-compile-readiness-planning check",
    "workflow-closure-audit includes v060-compile-readiness-planning check",
    "v060-compile-readiness-planning PASS",
    "TASK-301 is planning-only",
    "TASK-301 is future compile-readiness candidate",
    "TASK-301 is not implementation authorization",
    "TASK-301 does not modify MQ5 / MQH",
    "TASK-301 does not run MT5",
    "TASK-301 does not run Strategy Tester",
    "TASK-301 does not authorize backtest",
    "TASK-301 does not authorize simulation / real trading",
    "TASK-301 does not execute MetaEditor",
    "TASK-301 does not execute MQL5 compile",
    "TASK-301 does not create .ex5 artifact",
    "TASK-301 does not create compile log",
    "TASK-301 does not create evidence / manifest / report",
    "TASK-301 does not create manifest / fixture / report / directory",
    "TASK-301 does not copy external evidence",
    "TASK-301 confirms MQ5 inventory 7 files",
    "TASK-301 confirms MQ5 inventory remains 7 files",
    "TASK-301 confirms Buy / Sell / OrderSend / PositionOpen / CTrade false",
    "TASK-301 confirms Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-302 must not be entered directly without GPT authorization",
    "current task is TASK-302 implement MQL5 compile-only execution preflight gate",
    "TASK-302 implement MQL5 compile-only execution preflight gate",
    "TASK-301 completed",
    "TASK-301 completion commit is 2f0498b TASK-301 create v060 compile-readiness planning packet",
    "TASK-301 completion tag is v0.5.98-task-301-v060-compile-readiness-planning",
    "current HEAD is 2f0498b TASK-301 create v060 compile-readiness planning packet",
    "current tag is v0.5.98-task-301-v060-compile-readiness-planning",
    "TASK-302 creates docs/V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md",
    "TASK-302 creates tools/validate_mql5_compile_only_preflight_gate.py",
    "TASK-302 creates tools/test_validate_mql5_compile_only_preflight_gate.py",
    "mql5-compile-only-preflight-gate check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-preflight-gate check",
    "workflow-closure-audit includes mql5-compile-only-preflight-gate check",
    "mql5-compile-only-preflight-gate PASS",
    "TASK-302 is preflight-gate-only",
    "TASK-302 does not modify MQ5 / MQH",
    "TASK-302 does not run MT5",
    "TASK-302 does not execute MetaEditor",
    "TASK-302 does not execute MQL5 compile",
    "TASK-302 does not execute /compile command",
    "TASK-302 does not authorize Strategy Tester",
    "TASK-302 does not authorize backtest",
    "TASK-302 does not authorize trading",
    "TASK-302 does not create .ex5 artifact",
    "TASK-302 does not create compile log",
    "TASK-302 does not create manifest / fixture / report / directory",
    "TASK-302 does not copy external evidence",
    "TASK-302 preflight gate confirms repository has no ex5 artifacts",
    "TASK-302 preflight gate confirms repository has no compile logs",
    "TASK-302 preflight gate confirms MetaEditor was not executed",
    "TASK-302 preflight gate confirms MQL5 compile was not executed",
    "TASK-302 preflight gate confirms MT5 was not run",
    "TASK-302 preflight gate confirms trading remains unauthorized",
    "TASK-302 preflight gate confirms compile execution remains unauthorized",
    "TASK-302 preflight gate confirms future TASK-303 requires GPT boundary",
    "all previous compile-only boundary checks must pass before future compile execution",
    "artifact quarantine must pass before future compile execution",
    "future compile-only command must remain stdout-only unless GPT separately authorizes artifact handling",
    "TASK-303 must not be entered directly",
    "future TASK-303 must be separately authorized by GPT before any compile execution",
    "current task is TASK-303 create v0.6.0 compile-only execution authorization planning packet",
    "TASK-303 create v0.6.0 compile-only execution authorization planning packet",
    "TASK-302 completed",
    "TASK-302 completion commit is 15c675e TASK-302 implement MQL5 compile-only execution preflight gate",
    "TASK-302 completion tag is v0.5.99-task-302-mql5-compile-only-preflight-gate",
    "current HEAD is 15c675e TASK-302 implement MQL5 compile-only execution preflight gate",
    "current tag is v0.5.99-task-302-mql5-compile-only-preflight-gate",
    "TASK-303 creates docs/V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md",
    "TASK-303 creates tools/validate_mql5_compile_only_execution_authorization_plan.py",
    "TASK-303 creates tools/test_validate_mql5_compile_only_execution_authorization_plan.py",
    "mql5-compile-only-execution-authorization-plan check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-execution-authorization-plan check",
    "workflow-closure-audit includes mql5-compile-only-execution-authorization-plan check",
    "mql5-compile-only-execution-authorization-plan PASS",
    "TASK-303 is planning-only",
    "TASK-303 is authorization-boundary-only",
    "TASK-303 is future compile-only execution candidate",
    "TASK-303 does not modify MQ5 / MQH",
    "TASK-303 does not run MT5",
    "TASK-303 does not execute MetaEditor",
    "TASK-303 does not execute MQL5 compile",
    "TASK-303 does not execute /compile command",
    "TASK-303 does not authorize Strategy Tester",
    "TASK-303 does not authorize backtest",
    "TASK-303 does not authorize simulation trading",
    "TASK-303 does not authorize real trading",
    "TASK-303 does not create .ex5 artifact",
    "TASK-303 does not create compile log",
    "TASK-303 does not create manifest / fixture / report / directory",
    "TASK-303 does not copy external evidence",
    "TASK-303 confirms compile execution remains unauthorized",
    "TASK-303 confirms MetaEditor was not executed",
    "TASK-303 confirms MQL5 compile was not executed",
    "TASK-303 confirms future TASK-304 requires GPT boundary",
    "compile_execution_authorized=false",
    "future_task_304_requires_gpt_boundary=true",
    "metaeditor_executed=false",
    "mql5_compile_executed=false",
    "all previous MQ5 static / no-trade / compile-readiness checks PASS",
    "all previous MQL5 compile-only boundary / discovery / quarantine / dry-run / preflight checks PASS",
    "TASK-304 must not be entered directly",
    "future TASK-304 must be separately authorized by GPT before any compile execution",
    "current task is TASK-305 implement MQL5 compile-only failure diagnostic capture",
    "TASK-305 implement MQL5 compile-only failure diagnostic capture",
    "TASK-304 failed, no success result doc created",
    "TASK-304 is not compile success",
    "TASK-304 compile_exit_code=1 was observed",
    "current HEAD is 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet",
    "current tag is v0.5.100-task-303-v060-compile-only-execution-authorization",
    "TASK-305 creates docs/V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md",
    "TASK-305 creates tools/validate_mql5_compile_only_failure_diagnostic.py",
    "TASK-305 creates tools/test_validate_mql5_compile_only_failure_diagnostic.py",
    "tools/run_mql5_compile_only_quarantined.py supports --diagnostic-capture",
    "mql5-compile-only-failure-diagnostic check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-only-failure-diagnostic check",
    "workflow-closure-audit includes mql5-compile-only-failure-diagnostic check",
    "TASK-305 may re-run MetaEditor compile-only only against quarantine copy",
    "TASK-305 diagnostic output is stdout-only",
    "compile log must be stdout-only",
    "compile log must not be saved to repository",
    "no repo .ex5",
    "no repo compile log",
    "no MT5 terminal",
    "no Strategy Tester",
    "no trading",
    "no manifest / evidence / report",
    "TASK-306 requires GPT boundary",
    "TASK-306 must not be entered directly",
    "current task is TASK-306 implement MQL5 compile-only diagnostic result classification",
    "TASK-306 implement MQL5 compile-only diagnostic result classification",
    "TASK-305 completed",
    "TASK-305 completion commit is c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture",
    "TASK-305 completion tag is v0.5.101-task-305-mql5-compile-only-failure-diagnostic",
    "current HEAD is c82e4d6 TASK-305 implement MQL5 compile-only failure diagnostic capture",
    "current tag is v0.5.101-task-305-mql5-compile-only-failure-diagnostic",
    "TASK-306 creates docs/V060_TASK_306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION.md",
    "TASK-306 creates tools/validate_mql5_compile_diagnostic_result_classification.py",
    "TASK-306 creates tools/test_validate_mql5_compile_diagnostic_result_classification.py",
    "tools/run_mql5_compile_only_quarantined.py supports classify_compile_diagnostic_result",
    "mql5-compile-diagnostic-result-classification check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-diagnostic-result-classification check",
    "workflow-closure-audit includes mql5-compile-diagnostic-result-classification check",
    "TASK-306 is diagnostic-classification-only",
    "TASK-306 is not compile execution",
    "TASK-306 has no new MetaEditor execution in TASK-306",
    "not MetaEditor execution in TASK-306",
    "TASK-306 does not run MT5 terminal",
    "TASK-306 does not run Strategy Tester",
    "TASK-306 does not run backtest",
    "TASK-306 does not trade",
    "compile_exit_code=1 observed in TASK-305",
    "compile log semantic result indicates Result: 0 errors, 0 warnings",
    "compile_result_classification=metaeditor_exit_code_anomaly",
    "compile_log_semantic_success=true",
    "compile_success=false",
    "task304_success_result_created=false",
    "followup_required=true",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "TASK-307 requires GPT boundary before any compile retry or MQ5 fix",
    "TASK-307 must not be entered directly",
    "current task is TASK-307 implement MQL5 compile diagnostic artifact classification",
    "TASK-307 implement MQL5 compile diagnostic artifact classification",
    "TASK-306 completed",
    "TASK-306 completion commit is 560079c TASK-306 implement MQL5 compile-only diagnostic result classification",
    "TASK-306 completion tag is v0.5.102-task-306-mql5-compile-diagnostic-classification",
    "current HEAD is 560079c TASK-306 implement MQL5 compile-only diagnostic result classification",
    "current tag is v0.5.102-task-306-mql5-compile-diagnostic-classification",
    "TASK-307 creates docs/V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md",
    "TASK-307 creates tools/validate_mql5_compile_diagnostic_artifact_classification.py",
    "TASK-307 creates tools/test_validate_mql5_compile_diagnostic_artifact_classification.py",
    "tools/run_mql5_compile_only_quarantined.py supports quarantine artifact inspection before cleanup",
    "tools/run_mql5_compile_only_quarantined.py reports quarantine_ex5_artifact_detected",
    "tools/run_mql5_compile_only_quarantined.py reports quarantine_ex5_artifact_count",
    "tools/run_mql5_compile_only_quarantined.py reports quarantine_compile_log_detected",
    "mql5-compile-diagnostic-artifact-classification check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-diagnostic-artifact-classification check",
    "workflow-closure-audit includes mql5-compile-diagnostic-artifact-classification check",
    "TASK-307 is diagnostic-artifact-classification-only",
    "TASK-307 is not TASK-304 success result",
    "TASK-307 may re-run MetaEditor compile-only only against quarantine copy",
    "quarantine artifact inspection before cleanup",
    "quarantine .ex5 must not be copied to repository",
    "compile_success=false unless a future GPT boundary explicitly reclassifies success",
    "TASK-308 requires GPT boundary before any compile retry or MQ5 fix",
    "TASK-308 must not be entered directly",
    "current task is TASK-308 create MQL5 compile diagnostic artifact proof and success reclassification boundary",
    "TASK-308 create MQL5 compile diagnostic artifact proof and success reclassification boundary",
    "TASK-307 completed",
    "TASK-307 completion commit is 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification",
    "TASK-307 completion tag is v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification",
    "current HEAD is 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification",
    "current tag is v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification",
    "TASK-308 creates docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md",
    "TASK-308 creates tools/validate_mql5_compile_diagnostic_artifact_proof_boundary.py",
    "TASK-308 creates tools/test_validate_mql5_compile_diagnostic_artifact_proof_boundary.py",
    "mql5-compile-diagnostic-artifact-proof-boundary check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-diagnostic-artifact-proof-boundary check",
    "workflow-closure-audit includes mql5-compile-diagnostic-artifact-proof-boundary check",
    "TASK-308 is planning-only",
    "TASK-308 is diagnostic-proof-boundary-only",
    "TASK-308 is no compile execution",
    "TASK-308 has no MetaEditor execution",
    "no MetaEditor execution",
    "no MQL5 compile",
    "no .ex5 artifact",
    "no compile log",
    "no success reclassification in TASK-308",
    "success_reclassification_done=false",
    "TASK-307 observed quarantine_ex5_artifact_detected=true",
    "TASK-307 observed compile_log_semantic_success=true",
    "TASK-307 observed compile_exit_code=1",
    "previous classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
    "compiled_artifact_with_metaeditor_exit_code_anomaly",
    "compile_success=false",
    "task304_success_result_created=false",
    "future_task_309_requires_gpt_boundary=true",
    "future TASK-309 requires GPT boundary before any compile retry, MQ5 fix, artifact hash capture, or success reclassification",
    "TASK-309 must not be entered directly",
    "current task is TASK-309 create MQL5 compile-only success reclassification boundary",
    "TASK-309 create MQL5 compile-only success reclassification boundary",
    "TASK-308 completed",
    "TASK-308 completion commit is 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary",
    "TASK-308 completion tag is v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary",
    "current HEAD is 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary",
    "current tag is v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary",
    "TASK-309 creates docs/V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md",
    "TASK-309 creates tools/validate_mql5_compile_success_reclassification_boundary.py",
    "TASK-309 creates tools/test_validate_mql5_compile_success_reclassification_boundary.py",
    "mql5-compile-success-reclassification-boundary check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-success-reclassification-boundary check",
    "workflow-closure-audit includes mql5-compile-success-reclassification-boundary check",
    "TASK-309 is planning-only",
    "TASK-309 is success-reclassification-boundary-only",
    "TASK-309 is no compile execution",
    "TASK-309 has no MetaEditor execution",
    "no success reclassification in TASK-309",
    "TASK-307 observed quarantine_ex5_artifact_count=1",
    "future_task_310_requires_gpt_boundary=true",
    "future TASK-310 requires GPT boundary before any compile retry, artifact hash capture, success reclassification, or MQ5 fix",
    "TASK-310 must not be entered directly",
    "current task is TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic",
    "TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic",
    "TASK-309 completed",
    "TASK-309 completion commit is f31b85e TASK-309 create MQL5 compile-only success reclassification boundary",
    "TASK-309 completion tag is v0.5.105-task-309-mql5-compile-success-reclassification-boundary",
    "current HEAD is f31b85e TASK-309 create MQL5 compile-only success reclassification boundary",
    "current tag is v0.5.105-task-309-mql5-compile-success-reclassification-boundary",
    "TASK-310 creates docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md",
    "TASK-310 creates tools/validate_mql5_compile_artifact_hash_capture_boundary.py",
    "TASK-310 creates tools/test_validate_mql5_compile_artifact_hash_capture_boundary.py",
    "mql5-compile-artifact-hash-capture-boundary check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-artifact-hash-capture-boundary check",
    "workflow-closure-audit includes mql5-compile-artifact-hash-capture-boundary check",
    "TASK-310 is artifact-hash-capture-diagnostic-only",
    "artifact hash stdout-only",
    "artifact hash not saved to repository",
    "compile_success=false",
    "success_reclassification_done=false",
    "task304_success_result_created=false",
    "future_task_311_requires_gpt_boundary=true",
    "future TASK-311 requires GPT boundary before success reclassification or MQ5 fix",
    "TASK-311 must not be entered directly",
    "current task is TASK-311 create MQL5 compile success reclassification decision boundary",
    "TASK-311 create MQL5 compile success reclassification decision boundary",
    "TASK-310 completed",
    "TASK-310 completion commit is 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic",
    "TASK-310 completion tag is v0.5.106-task-310-mql5-compile-artifact-hash-capture",
    "current HEAD is 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic",
    "current tag is v0.5.106-task-310-mql5-compile-artifact-hash-capture",
    "TASK-311 creates docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md",
    "TASK-311 creates tools/validate_mql5_compile_success_reclassification_decision_boundary.py",
    "TASK-311 creates tools/test_validate_mql5_compile_success_reclassification_decision_boundary.py",
    "mql5-compile-success-reclassification-decision-boundary check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-success-reclassification-decision-boundary check",
    "workflow-closure-audit includes mql5-compile-success-reclassification-decision-boundary check",
    "TASK-311 is planning-only",
    "TASK-311 is success-reclassification-decision-boundary-only",
    "no MetaEditor execution in TASK-311",
    "no MQL5 compile in TASK-311",
    "no success reclassification in TASK-311",
    "artifact hash was stdout-only and must not be stored in repository",
    "artifact_hash_stored_in_repo=false",
    "previous classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly",
    "future_task_312_requires_gpt_boundary=true",
    "future TASK-312 requires GPT boundary before success reclassification, MQ5 fix, or compile retry",
    "TASK-312 must not be entered directly",
    "current task is TASK-312 implement controlled MQL5 compile-only success reclassification decision",
    "TASK-312 implement controlled MQL5 compile-only success reclassification decision",
    "TASK-311 completed",
    "TASK-311 completion commit is 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary",
    "TASK-311 completion tag is v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary",
    "current HEAD is 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary",
    "current tag is v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary",
    "TASK-312 creates docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md",
    "TASK-312 creates tools/validate_mql5_compile_success_reclassification_decision.py",
    "TASK-312 creates tools/test_validate_mql5_compile_success_reclassification_decision.py",
    "mql5-compile-success-reclassification-decision check is added to release validation bundle",
    "fast-no-trade-dev profile includes mql5-compile-success-reclassification-decision check",
    "workflow-closure-audit includes mql5-compile-success-reclassification-decision check",
    "TASK-312 is controlled-success-reclassification-attempt",
    "success_reclassification_decision=PASS",
    "compile_only_reclassified_success=true",
    "compile_success=true",
    "compile_success_scope=compile-only-diagnostic",
    "compile-only success does not imply trading authorization",
    "compile-only success does not imply deployment readiness",
    "compile-only success does not imply backtest readiness",
    "compile-only success does not imply strategy readiness",
    "artifact_hash_stdout_only=true",
    "artifact_hash_saved_to_repo=false",
    "do not include actual artifact hash value in this doc",
    "future_task_313_requires_gpt_boundary=true",
    "future TASK-313 requires GPT boundary before MT5 run, Strategy Tester, backtest, deployment, or trading-related step",
    "TASK-313 must not be entered directly",
    "当前仍然不允许真实交易",
    "SignalEngine 禁止下单",
    "RiskManager 禁止被绕过",
    "ExecutionManager 不能真实执行订单",
    "InpEnableTrading 默认 false",
    "禁止 CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify",
    "禁止马丁、网格、补仓",
]

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-313 create MT5 terminal no-trade startup boundary packet",
        "TASK-313 create MT5 terminal no-trade startup boundary packet",
        "TASK-312 completed",
        "TASK-312 completion commit is efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision",
        "TASK-312 completion tag is v0.5.108-task-312-mql5-compile-success-reclassification-decision",
        "current HEAD is efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision",
        "current tag is v0.5.108-task-312-mql5-compile-success-reclassification-decision",
        "TASK-313 creates docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md",
        "TASK-313 creates tools/validate_mt5_no_trade_startup_boundary.py",
        "TASK-313 creates tools/test_validate_mt5_no_trade_startup_boundary.py",
        "mt5-no-trade-startup-boundary check is added to release validation bundle",
        "fast-no-trade-dev profile includes mt5-no-trade-startup-boundary check",
        "workflow-closure-audit includes mt5-no-trade-startup-boundary check",
        "TASK-313 is planning-only",
        "TASK-313 is mt5-startup-boundary-only",
        "no MT5 run in TASK-313",
        "no terminal64 execution",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "future_task_314_requires_gpt_boundary=true",
        "future TASK-314 requires GPT boundary before MT5 terminal startup attempt",
        "TASK-314 must not be entered directly",
    ]
)

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-314 implement MT5 no-trade startup command discovery boundary",
        "TASK-314 implement MT5 no-trade startup command discovery boundary",
        "TASK-313 completed",
        "TASK-313 completion commit is 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet",
        "TASK-313 completion tag is v0.5.109-task-313-mt5-no-trade-startup-boundary",
        "current HEAD is 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet",
        "current tag is v0.5.109-task-313-mt5-no-trade-startup-boundary",
        "TASK-314 creates docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md",
        "TASK-314 creates tools/validate_mt5_no_trade_startup_command_discovery.py",
        "TASK-314 creates tools/test_validate_mt5_no_trade_startup_command_discovery.py",
        "mt5-no-trade-startup-command-discovery check is added to release validation bundle",
        "fast-no-trade-dev profile includes mt5-no-trade-startup-command-discovery check",
        "workflow-closure-audit includes mt5-no-trade-startup-command-discovery check",
        "TASK-314 is command-discovery-only",
        "TASK-314 is mt5-startup-preparation-only",
        "no MT5 run in TASK-314",
        "no terminal64 execution",
        "no terminal64.exe execution",
        "no terminal.exe execution",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "compile_success_scope=compile-only-diagnostic",
        "trading_authorization=false",
        "deployment_readiness=false",
        "backtest_readiness=false",
        "strategy_readiness=false",
        "future_task_315_requires_gpt_boundary=true",
        "future TASK-315 requires GPT boundary before any MT5 terminal startup attempt",
        "TASK-315 must not be entered directly",
    ]
)

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-315 implement MT5 no-trade startup quarantine preparation boundary",
        "TASK-315 implement MT5 no-trade startup quarantine preparation boundary",
        "TASK-314 completed",
        "TASK-314 completion commit is ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary",
        "TASK-314 completion tag is v0.5.110-task-314-mt5-no-trade-startup-command-discovery",
        "current HEAD is ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary",
        "current tag is v0.5.110-task-314-mt5-no-trade-startup-command-discovery",
        "TASK-315 creates docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md",
        "TASK-315 creates tools/validate_mt5_no_trade_startup_quarantine_preparation.py",
        "TASK-315 creates tools/test_validate_mt5_no_trade_startup_quarantine_preparation.py",
        "mt5-no-trade-startup-quarantine-preparation check is added to release validation bundle",
        "fast-no-trade-dev profile includes mt5-no-trade-startup-quarantine-preparation check",
        "workflow-closure-audit includes mt5-no-trade-startup-quarantine-preparation check",
        "TASK-315 is planning-only",
        "TASK-315 is startup-quarantine-preparation-only",
        "startup_quarantine_outside_repo_required=true",
        "repo_terminal_data_directory=false",
        "repo_startup_logs=false",
        "no MT5 run in TASK-315",
        "no terminal64.exe execution in TASK-315",
        "no terminal.exe execution in TASK-315",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "compile_success_scope=compile-only-diagnostic",
        "trading_authorization=false",
        "deployment_readiness=false",
        "backtest_readiness=false",
        "strategy_readiness=false",
        "future_task_316_requires_gpt_boundary=true",
        "future TASK-316 requires GPT boundary before any MT5 terminal startup attempt",
        "TASK-316 must not be entered directly",
    ]
)

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-316 implement MT5 no-trade startup dry-run config boundary",
        "TASK-316 implement MT5 no-trade startup dry-run config boundary",
        "TASK-315 completed",
        "TASK-315 completion commit is 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary",
        "TASK-315 completion tag is v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation",
        "current HEAD is 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary",
        "current tag is v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation",
        "TASK-316 creates docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md",
        "TASK-316 creates tools/validate_mt5_no_trade_startup_dryrun_config_boundary.py",
        "TASK-316 creates tools/test_validate_mt5_no_trade_startup_dryrun_config_boundary.py",
        "mt5-no-trade-startup-dryrun-config-boundary check is added to release validation bundle",
        "fast-no-trade-dev profile includes mt5-no-trade-startup-dryrun-config-boundary check",
        "workflow-closure-audit includes mt5-no-trade-startup-dryrun-config-boundary check",
        "TASK-316 is planning-only",
        "TASK-316 is startup-dryrun-config-boundary-only",
        "no_trade_config_generated_in_repo=false",
        "repo_terminal_data_directory=false",
        "repo_startup_logs=false",
        "no MT5 run in TASK-316",
        "no terminal64.exe execution in TASK-316",
        "no terminal.exe execution in TASK-316",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "compile_success_scope=compile-only-diagnostic",
        "trading_authorization=false",
        "deployment_readiness=false",
        "backtest_readiness=false",
        "strategy_readiness=false",
        "future_task_317_requires_gpt_boundary=true",
        "future TASK-317 requires GPT boundary before any MT5 terminal startup attempt",
        "TASK-317 must not be entered directly",
    ]
)

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-317 implement MT5 no-trade startup config template preview",
        "TASK-317 implement MT5 no-trade startup config template preview",
        "TASK-316 completed",
        "TASK-316 completion commit is a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary",
        "TASK-316 completion tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
        "current HEAD is a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary",
        "current tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
        "TASK-317 creates docs/V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md",
        "TASK-317 creates tools/validate_mt5_no_trade_startup_config_template.py",
        "TASK-317 creates tools/test_validate_mt5_no_trade_startup_config_template.py",
        "mt5-no-trade-startup-config-template check is added to release validation bundle",
        "fast-no-trade-dev profile includes mt5-no-trade-startup-config-template check",
        "workflow-closure-audit includes mt5-no-trade-startup-config-template check",
        "TASK-317 is stdout-only-config-template-preview",
        "config_file_generated=false",
        "no_trade_config_generated_in_repo=false",
        "no config file generated",
        "no MT5 terminal executed",
        "no terminal64 execution",
        "no terminal.exe execution",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "no terminal data directory in repository",
        "no startup log in repository",
        "no no-trade config file generated in repository",
        "future_task_318_requires_gpt_boundary=true",
        "future TASK-318 requires GPT boundary before writing any startup config file or launching MT5",
        "TASK-318 must not be entered directly",
    ]
)

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-318 implement MT5 no-trade startup authorization planning boundary",
        "TASK-318 implement MT5 no-trade startup authorization planning boundary",
        "TASK-317 completed",
        "TASK-317 completion commit is a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview",
        "TASK-317 completion tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
        "current HEAD is a5aa4c3 TASK-317 implement MT5 no-trade startup config template preview",
        "current tag is v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
        "TASK-318 creates docs/V060_TASK_318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN.md",
        "TASK-318 creates tools/validate_mt5_no_trade_startup_authorization_plan.py",
        "TASK-318 creates tools/test_validate_mt5_no_trade_startup_authorization_plan.py",
        "mt5-no-trade-startup-authorization-plan check is added to release validation bundle",
        "fast-no-trade-dev profile includes mt5-no-trade-startup-authorization-plan check",
        "workflow-closure-audit includes mt5-no-trade-startup-authorization-plan check",
        "TASK-318 is planning-only",
        "TASK-318 is authorization-boundary-only",
        "config_file_generated=false",
        "no_trade_config_generated_in_repo=false",
        "no MT5 run in TASK-318",
        "no terminal64.exe execution in TASK-318",
        "no terminal.exe execution in TASK-318",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "no MetaEditor execution",
        "no MQL5 compile",
        "no .ex5 artifact",
        "no compile log",
        "no terminal data directory in repository",
        "no startup log in repository",
        "future_task_319_requires_gpt_boundary=true",
        "future TASK-319 requires GPT boundary before any MT5 terminal startup execution",
        "TASK-319 must not be entered directly",
    ]
)

COMMON_REQUIRED_KEYWORDS.extend(
    [
        "current task is TASK-321 implement parser pipeline integration completion",
        "TASK-321 implement parser pipeline integration completion",
        "TASK-319 completed",
        "TASK-319 completion commit is 5f0a697 TASK-319 implement MT5 no-trade startup preflight gate",
        "TASK-319 completion tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate",
        "current HEAD is 9dfb42b TASK-321 implement parser pipeline integration completion",
        "current tag is v0.5.114-task-319-mt5-no-trade-startup-preflight-gate",
        "TASK-321 creates docs/V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md",
        "TASK-321 creates tools/parse_mql5_compile_log.py",
        "TASK-321 creates tools/parse_backtest_set_params.py",
        "TASK-321 creates tools/run_evidence_parser_pipeline.py",
        "TASK-321 creates tools/validate_parser_manifest_integration.py",
        "parser-manifest-integration check is added to release validation bundle",
        "fast-no-trade-dev profile includes parser-manifest-integration check",
        "fast-no-trade-dev profile includes backtest-set-params check",
        "TASK-321 is parser-pipeline-integration-only",
        "no MT5 run in TASK-321",
        "no terminal64.exe execution in TASK-321",
        "no Strategy Tester",
        "no backtest",
        "no trading authorization",
        "no MetaEditor execution",
        "no MQL5 compile",
        "no .ex5 artifact",
        "no compile log",
        "no manifest generated in repository during TASK-321",
        "no external evidence copied into repository",
        "future_task_320_requires_gpt_boundary=true",
        "future TASK-320 requires GPT boundary before any MT5 terminal startup attempt",
        "TASK-320 must not be entered directly",
        "no repo .ex5",
        "no repo compile log",
        "MQ5 inventory remains 7 files",
        "MQ5 inventory 仍为 7 files",
        "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
        "Buy / Sell / OrderSend / PositionOpen / CTrade false",
        "Inventory only; no MT5 run; no trading authorization.",
        "mt5-no-trade-startup-preflight-gate PASS",
        "parser-manifest-integration PASS",
        "backtest-set-params PASS",
        "current engineering gap: none after TASK-321 parser pipeline integration",
    ]
)

TASK_DOC_ROLE_BOUNDARY_DOCS = [
    "docs/HANDOFF_PROMPT.md",
    "docs/PROJECT_STATE.md",
]

TASK_DOC_ROLE_BOUNDARY_REQUIRED_KEYWORDS = [
    "TASK-DOC docs edits must be made by Codex.",
    "Builder / Trae may only review, validate, git add, and git commit.",
    "Builder / Trae must not directly write docs content.",
    "Builder / Trae must not define the next stage boundary.",
    "The next task boundary must be defined by ChatGPT.",
]

PROHIBITED_KEYWORDS = [
    "v0.3.0 represents live trading",
    "v0.3.0 represents real trading readiness",
    "v0.3.0 represents a completed profitable strategy",
    "v0.3.0 enables real trading",
    "v0.3.0 allows real trading",
    "v0.4.0 represents live trading",
    "v0.4.0 represents real trading readiness",
    "v0.4.0 represents a completed profitable strategy",
    "v0.4.0 enables real trading",
    "v0.4.0 allows real trading",
    "v0.5.0 represents live trading",
    "v0.5.0 represents real trading readiness",
    "v0.5.0 represents a completed profitable strategy",
    "v0.5.0 enables real trading",
    "v0.5.0 allows real trading",
]

# Built from code points so this source file does not contain the suspicious
# rendered fragments that the guard is meant to catch in docs.
MOJIBAKE_CODEPOINT_SEQUENCES = [
    [0x8930, 0x64B3, 0x58A0],
    [0x6D93, 0x5DB6],
    [0x934F],
    [0x7ECB, 0x51B2],
    [0x6D60, 0x8BF2],
    [0x951B],
    [0x9286],
    [0x20AC, 0x003F],
    [0xE6E6],
    [0xE18C],
]

CURRENT_COMMIT_LABEL_PATTERN = re.compile(
    r"当前最新提交：\s*(?P<commit>[0-9a-f]{7,40}\s+\S.*)",
    re.MULTILINE,
)

CURRENT_FUNCTIONAL_TASK_PATTERN = re.compile(
    r"当前最新功能任务：\s*(?P<task>[0-9a-f]{7,40}\s+\S.*)",
    re.MULTILINE,
)

NEXT_STEP_HEADING = "## 当前下一步"
NEXT_BOUNDARY_REQUIRED_KEYWORDS = [
    "不要直接进入 v0.6.0",
    "不要直接修改 MQ5",
    "不要直接修改 backtest/sets",
    "不要直接进入真实交易",
    "必须先由 ChatGPT 制定下一任务边界",
]


def read_text(path):
    return path.read_text(encoding="utf-8")


def suspicious_mojibake_fragments():
    return [
        "".join(chr(codepoint) for codepoint in sequence)
        for sequence in MOJIBAKE_CODEPOINT_SEQUENCES
    ]


def collect_file_issues():
    issues = []

    for label, path in DOC_PATHS.items():
        if not path.exists():
            issues.append(f"missing required docs file: {label}")

    for label, path in ROOT_DUPLICATE_PATHS.items():
        if path.exists():
            issues.append(f"root duplicate found: {label}")

    if not PLAN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md")
    if not TASK238_BOUNDARY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_238_NO_TRADE_SCAFFOLD_BOUNDARY.md")
    if not TASK239_BOUNDARY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_239_FIRST_IMPLEMENTATION_SLICE_BOUNDARY.md")
    if not TASK260_OBSERVABILITY_EXTENSION_PLAN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md")
    if not TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_261_OBSERVABILITY_EXTENSION_NEXT_PLAN.md")
    if not TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN.md")
    if not TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_263_OBSERVABILITY_EXTENSION_FUTURE_PLAN.md")
    if not TASK294_MQL5_COMPILE_ONLY_BOUNDARY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md")
    if not TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md")
    if not TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md")
    if not TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md")
    if not TASK298_MQL5_COMPILE_ONLY_DRYRUN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md")
    if not TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md")
    if not TASK301_V060_COMPILE_READINESS_PLANNING_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md")
    if not TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md")
    if not TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md")
    if not TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md")
    if not TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION.md")
    if not TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md")
    if not TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md")
    if not TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md")
    if not TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_DOC_PATH.exists():
        issues.append("missing required docs file: docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md")

    return issues


def collect_missing_keywords(label, text, keywords, issue_label="required keyword"):
    issues = []
    for keyword in keywords:
        if keyword not in text:
            issues.append(f"{label} missing {issue_label}: {keyword}")
    return issues


def collect_keyword_issues(docs_text):
    issues = []

    for label, text in docs_text.items():
        issues.extend(collect_missing_keywords(label, text, COMMON_REQUIRED_KEYWORDS))

    for label in TASK_DOC_ROLE_BOUNDARY_DOCS:
        issues.extend(
            collect_missing_keywords(
                label,
                docs_text[label],
                TASK_DOC_ROLE_BOUNDARY_REQUIRED_KEYWORDS,
                issue_label="TASK-DOC role boundary",
            )
        )

    return issues


def collect_plan_doc_issues():
    if not PLAN_DOC_PATH.exists():
        return []

    text = read_text(PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_FIRST_LOW_RISK_IMPLEMENTATION_PLAN.md",
        text,
        PLAN_DOC_REQUIRED_KEYWORDS,
        issue_label="planning packet keyword",
    )


def collect_task238_boundary_doc_issues():
    if not TASK238_BOUNDARY_DOC_PATH.exists():
        return []

    text = read_text(TASK238_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_238_NO_TRADE_SCAFFOLD_BOUNDARY.md",
        text,
        TASK238_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-238 boundary keyword",
    )


def collect_task239_boundary_doc_issues():
    if not TASK239_BOUNDARY_DOC_PATH.exists():
        return []

    text = read_text(TASK239_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_239_FIRST_IMPLEMENTATION_SLICE_BOUNDARY.md",
        text,
        TASK239_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-239 boundary keyword",
    )


def collect_task260_observability_extension_plan_doc_issues():
    if not TASK260_OBSERVABILITY_EXTENSION_PLAN_DOC_PATH.exists():
        return []

    text = read_text(TASK260_OBSERVABILITY_EXTENSION_PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md",
        text,
        TASK260_OBSERVABILITY_EXTENSION_PLAN_REQUIRED_KEYWORDS,
        issue_label="TASK-260 observability extension planning keyword",
    )


def collect_task261_observability_extension_next_plan_doc_issues():
    if not TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_DOC_PATH.exists():
        return []

    text = read_text(TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_261_OBSERVABILITY_EXTENSION_NEXT_PLAN.md",
        text,
        TASK261_OBSERVABILITY_EXTENSION_NEXT_PLAN_REQUIRED_KEYWORDS,
        issue_label="TASK-261 observability extension planning keyword",
    )


def collect_task262_observability_extension_followup_plan_doc_issues():
    if not TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_DOC_PATH.exists():
        return []

    text = read_text(TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN.md",
        text,
        TASK262_OBSERVABILITY_EXTENSION_FOLLOWUP_PLAN_REQUIRED_KEYWORDS,
        issue_label="TASK-262 observability extension planning keyword",
    )


def collect_task263_observability_extension_future_plan_doc_issues():
    if not TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_DOC_PATH.exists():
        return []

    text = read_text(TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_263_OBSERVABILITY_EXTENSION_FUTURE_PLAN.md",
        text,
        TASK263_OBSERVABILITY_EXTENSION_FUTURE_PLAN_REQUIRED_KEYWORDS,
        issue_label="TASK-263 observability extension planning keyword",
    )


def collect_task294_mql5_compile_only_boundary_doc_issues():
    if not TASK294_MQL5_COMPILE_ONLY_BOUNDARY_DOC_PATH.exists():
        return []

    text = read_text(TASK294_MQL5_COMPILE_ONLY_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md",
        text,
        TASK294_MQL5_COMPILE_ONLY_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-DOC-294 MQL5 compile-only boundary keyword",
    )


def collect_task295_mql5_compile_only_command_discovery_doc_issues():
    if not TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_DOC_PATH.exists():
        return []

    text = read_text(TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
        text,
        TASK295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY_REQUIRED_KEYWORDS,
        issue_label="TASK-295 MQL5 compile-only command discovery keyword",
    )


def collect_task296_mql5_compile_only_artifact_quarantine_doc_issues():
    if not TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_DOC_PATH.exists():
        return []

    text = read_text(TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
        text,
        TASK296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE_REQUIRED_KEYWORDS,
        issue_label="TASK-296 MQL5 compile-only artifact quarantine keyword",
    )


def collect_task297_mql5_compile_only_execution_boundary_doc_issues():
    if not TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_DOC_PATH.exists():
        return []

    text = read_text(TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
        text,
        TASK297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-297 MQL5 compile-only execution boundary keyword",
    )


def collect_task298_mql5_compile_only_dryrun_doc_issues():
    if not TASK298_MQL5_COMPILE_ONLY_DRYRUN_DOC_PATH.exists():
        return []

    text = read_text(TASK298_MQL5_COMPILE_ONLY_DRYRUN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md",
        text,
        TASK298_MQL5_COMPILE_ONLY_DRYRUN_REQUIRED_KEYWORDS,
        issue_label="TASK-298 MQL5 compile-only dry-run keyword",
    )


def collect_task300_mql5_compile_only_dryrun_execution_doc_issues():
    if not TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_DOC_PATH.exists():
        return []

    text = read_text(TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md",
        text,
        TASK300_MQL5_COMPILE_ONLY_DRYRUN_EXECUTION_REQUIRED_KEYWORDS,
        issue_label="TASK-300 MQL5 compile-only dry-run execution keyword",
    )


def collect_task301_v060_compile_readiness_planning_doc_issues():
    if not TASK301_V060_COMPILE_READINESS_PLANNING_DOC_PATH.exists():
        return []

    text = read_text(TASK301_V060_COMPILE_READINESS_PLANNING_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md",
        text,
        TASK301_V060_COMPILE_READINESS_PLANNING_REQUIRED_KEYWORDS,
        issue_label="TASK-301 v0.6.0 compile-readiness planning keyword",
    )


def collect_task302_mql5_compile_only_preflight_gate_doc_issues():
    if not TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_DOC_PATH.exists():
        return []

    text = read_text(TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md",
        text,
        TASK302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE_REQUIRED_KEYWORDS,
        issue_label="TASK-302 MQL5 compile-only preflight gate keyword",
    )


def collect_task303_mql5_compile_only_execution_authorization_plan_doc_issues():
    if not TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_DOC_PATH.exists():
        return []

    text = read_text(TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md",
        text,
        TASK303_MQL5_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN_REQUIRED_KEYWORDS,
        issue_label="TASK-303 MQL5 compile-only execution authorization plan keyword",
    )


def collect_task305_mql5_compile_only_failure_diagnostic_doc_issues():
    if not TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_DOC_PATH.exists():
        return []

    text = read_text(TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md",
        text,
        TASK305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC_REQUIRED_KEYWORDS,
        issue_label="TASK-305 MQL5 compile-only failure diagnostic keyword",
    )


def collect_task306_mql5_compile_diagnostic_result_classification_doc_issues():
    if not TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_DOC_PATH.exists():
        return []

    text = read_text(TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION.md",
        text,
        TASK306_MQL5_COMPILE_DIAGNOSTIC_RESULT_CLASSIFICATION_REQUIRED_KEYWORDS,
        issue_label="TASK-306 MQL5 compile diagnostic result classification keyword",
    )


def collect_task307_mql5_compile_diagnostic_artifact_classification_doc_issues():
    if not TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_DOC_PATH.exists():
        return ["missing required docs file: docs/V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md"]
    text = read_text(TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md",
        text,
        TASK307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION_REQUIRED_KEYWORDS,
        issue_label="TASK-307 MQL5 compile diagnostic artifact classification keyword",
    )


def collect_task308_mql5_compile_diagnostic_artifact_proof_boundary_doc_issues():
    if not TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_DOC_PATH.exists():
        return ["missing required docs file: docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md"]
    text = read_text(TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md",
        text,
        TASK308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-308 MQL5 compile diagnostic artifact proof boundary keyword",
    )


def collect_task309_mql5_compile_success_reclassification_boundary_doc_issues():
    if not TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_DOC_PATH.exists():
        return ["missing required docs file: docs/V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md"]
    text = read_text(TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md",
        text,
        TASK309_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-309 MQL5 compile success reclassification boundary keyword",
    )


def collect_task310_mql5_compile_artifact_hash_capture_doc_issues():
    if not TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_DOC_PATH.exists():
        return ["missing required docs file: docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md"]
    text = read_text(TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md",
        text,
        TASK310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE_REQUIRED_KEYWORDS,
        issue_label="TASK-310 MQL5 compile artifact hash capture keyword",
    )


def collect_task311_mql5_compile_success_reclassification_decision_boundary_doc_issues():
    if not TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
        ]
    text = read_text(TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md",
        text,
        TASK311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-311 MQL5 compile success reclassification decision boundary keyword",
    )


def collect_task312_mql5_compile_success_reclassification_decision_doc_issues():
    if not TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
        ]
    text = read_text(TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_DOC_PATH)
    issues = collect_missing_keywords(
        "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md",
        text,
        TASK312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_REQUIRED_KEYWORDS,
        issue_label="TASK-312 MQL5 compile success reclassification decision keyword",
    )
    if re.search(r"\b[0-9a-fA-F]{64}\b", text):
        issues.append(
            "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md "
            "must not store an actual 64-character artifact hash"
        )
    return issues


def collect_task313_mt5_no_trade_startup_boundary_doc_issues():
    if not TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
        ]
    text = read_text(TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md",
        text,
        TASK313_MT5_NO_TRADE_STARTUP_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-313 MT5 no-trade startup boundary keyword",
    )


def collect_task314_mt5_no_trade_startup_command_discovery_doc_issues():
    if not TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
        ]
    text = read_text(TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md",
        text,
        TASK314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY_REQUIRED_KEYWORDS,
        issue_label="TASK-314 MT5 no-trade startup command discovery keyword",
    )


def collect_task315_mt5_no_trade_startup_quarantine_preparation_doc_issues():
    if not TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"
        ]
    text = read_text(TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md",
        text,
        TASK315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION_REQUIRED_KEYWORDS,
        issue_label="TASK-315 MT5 no-trade startup quarantine preparation keyword",
    )


def collect_task316_mt5_no_trade_startup_dryrun_config_boundary_doc_issues():
    if not TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md"
        ]
    text = read_text(TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md",
        text,
        TASK316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY_REQUIRED_KEYWORDS,
        issue_label="TASK-316 MT5 no-trade startup dry-run config boundary keyword",
    )


def collect_task317_mt5_no_trade_startup_config_template_doc_issues():
    if not TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md"
        ]
    text = read_text(TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md",
        text,
        TASK317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE_REQUIRED_KEYWORDS,
        issue_label="TASK-317 MT5 no-trade startup config template keyword",
    )


def collect_task318_mt5_no_trade_startup_authorization_plan_doc_issues():
    if not TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN.md"
        ]
    text = read_text(TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN.md",
        text,
        TASK318_MT5_NO_TRADE_STARTUP_AUTHORIZATION_PLAN_REQUIRED_KEYWORDS,
        issue_label="TASK-318 MT5 no-trade startup authorization plan keyword",
    )


def collect_task319_mt5_no_trade_startup_preflight_gate_doc_issues():
    if not TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE.md"
        ]
    text = read_text(TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE.md",
        text,
        TASK319_MT5_NO_TRADE_STARTUP_PREFLIGHT_GATE_REQUIRED_KEYWORDS,
        issue_label="TASK-319 MT5 no-trade startup preflight gate keyword",
    )


def collect_task321_parser_pipeline_integration_doc_issues():
    if not TASK321_PARSER_PIPELINE_INTEGRATION_DOC_PATH.exists():
        return [
            "missing required docs file: "
            "docs/V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md"
        ]
    text = read_text(TASK321_PARSER_PIPELINE_INTEGRATION_DOC_PATH)
    return collect_missing_keywords(
        "docs/V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md",
        text,
        TASK321_PARSER_PIPELINE_INTEGRATION_REQUIRED_KEYWORDS,
        issue_label="TASK-321 parser pipeline integration keyword",
    )


def collect_mojibake_issues(docs_text):
    issues = []
    fragments = suspicious_mojibake_fragments()
    for label, text in docs_text.items():
        for fragment in fragments:
            if fragment in text:
                codepoints = " ".join(f"U+{ord(char):04X}" for char in fragment)
                issues.append(
                    f"{label} contains suspicious mojibake / garbled Chinese text: "
                    f"{codepoints}"
                )
    return issues


def collect_prohibited_keyword_issues(docs_text):
    issues = []
    for label, text in docs_text.items():
        for keyword in PROHIBITED_KEYWORDS:
            if keyword in text:
                issues.append(f"{label} contains prohibited state text: {keyword}")
    return issues


def extract_section(text, heading):
    start = text.find(heading)
    if start == -1:
        return ""

    next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def extract_current_next_boundary(label, text):
    section = extract_section(text, NEXT_STEP_HEADING)
    if not section:
        return "", f"{label} missing current next step section"

    lines = [
        line.strip().lstrip("-").strip()
        for line in section.splitlines()
        if line.strip()
    ]
    boundary_lines = [
        line
        for line in lines
        if "不要直接进入" in line
        or "不要直接修改" in line
        or "必须先由 ChatGPT 制定下一任务边界" in line
    ]
    boundary = "\n".join(boundary_lines)
    if not boundary:
        return "", f"{label} missing current next boundary"

    missing = [
        keyword
        for keyword in NEXT_BOUNDARY_REQUIRED_KEYWORDS
        if keyword not in boundary
    ]
    if missing:
        return boundary, (
            f"{label} current next boundary missing: " + ", ".join(missing)
        )

    return boundary, None


def collect_dynamic_consistency_issues(docs_text):
    issues = []
    current_commits = {}
    functional_tasks = {}
    current_boundaries = {}

    for label, text in docs_text.items():
        commit_match = CURRENT_COMMIT_LABEL_PATTERN.search(text)
        if not commit_match:
            issues.append(f"{label} missing current latest commit")
        else:
            current_commits[label] = commit_match.group("commit").strip()

        task_match = CURRENT_FUNCTIONAL_TASK_PATTERN.search(text)
        if not task_match:
            issues.append(f"{label} missing current latest functional task")
        else:
            functional_tasks[label] = task_match.group("task").strip()

        boundary, issue = extract_current_next_boundary(label, text)
        if issue:
            issues.append(issue)
        else:
            current_boundaries[label] = boundary

    if len(set(current_commits.values())) > 1:
        issues.append(
            "current latest commit mismatch: "
            + ", ".join(f"{label}={value}" for label, value in current_commits.items())
        )

    if len(set(functional_tasks.values())) > 1:
        issues.append(
            "current latest functional task mismatch: "
            + ", ".join(f"{label}={value}" for label, value in functional_tasks.items())
        )

    if len(set(current_boundaries.values())) > 1:
        issues.append(
            "current next boundary mismatch: "
            + ", ".join(
                f"{label}={value}" for label, value in current_boundaries.items()
            )
        )

    return issues, current_commits, current_boundaries


def mq5_source_files():
    if not MQ5_ROOT.exists():
        return []
    return sorted(
        path
        for path in MQ5_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def mq5_rel_path(path):
    return path.relative_to(MQ5_ROOT).as_posix()


def collect_mq5_static_interface_consistency_issues():
    issues = []
    if not MQ5_ROOT.exists():
        return ["missing MQ5 root: mq5"]

    source_files = mq5_source_files()
    actual_files = {mq5_rel_path(path) for path in source_files}
    missing_files = sorted(MQ5_STATIC_INTERFACE_EXPECTED_FILES - actual_files)
    extra_files = sorted(actual_files - MQ5_STATIC_INTERFACE_EXPECTED_FILES)

    if missing_files:
        issues.append("MQ5 static interface missing files: " + ", ".join(missing_files))
    if extra_files:
        issues.append("MQ5 static interface unexpected files: " + ", ".join(extra_files))

    for rel_path in sorted(MQ5_STATIC_INTERFACE_EXPECTED_FILES & actual_files):
        text = read_text(MQ5_ROOT / rel_path)
        for keyword in MQ5_STATIC_INTERFACE_REQUIRED_KEYWORDS.get(rel_path, []):
            if keyword not in text:
                issues.append(f"{rel_path} missing static interface keyword: {keyword}")
        for keyword in MQ5_STATIC_INTERFACE_FORBIDDEN_KEYWORDS:
            if keyword in text:
                issues.append(f"{rel_path} contains prohibited trading keyword: {keyword}")

    return issues


def main_mq5_static_interface_consistency():
    issues = collect_mq5_static_interface_consistency_issues()
    if issues:
        print("MQ5 static interface consistency validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 static interface consistency validation passed")
    print("MQ5 inventory remains 7 files")
    print("Buy / Sell / OrderSend / PositionOpen / CTrade remain false")
    print("Inventory only; no MT5 run; no trading authorization.")
    return 0


def main_mql5_compile_only_boundary():
    issues = collect_file_issues()
    if not issues:
        docs_text = {
            label: read_text(path)
            for label, path in DOC_PATHS.items()
        }
        issues.extend(collect_keyword_issues(docs_text))
        issues.extend(collect_task294_mql5_compile_only_boundary_doc_issues())
        issues.extend(collect_task295_mql5_compile_only_command_discovery_doc_issues())
        issues.extend(collect_task296_mql5_compile_only_artifact_quarantine_doc_issues())
        issues.extend(collect_task297_mql5_compile_only_execution_boundary_doc_issues())
        issues.extend(collect_task298_mql5_compile_only_dryrun_doc_issues())
        issues.extend(collect_task300_mql5_compile_only_dryrun_execution_doc_issues())
        issues.extend(collect_task301_v060_compile_readiness_planning_doc_issues())
        issues.extend(collect_task302_mql5_compile_only_preflight_gate_doc_issues())
        issues.extend(collect_task303_mql5_compile_only_execution_authorization_plan_doc_issues())
        issues.extend(collect_task305_mql5_compile_only_failure_diagnostic_doc_issues())
        issues.extend(collect_task306_mql5_compile_diagnostic_result_classification_doc_issues())
        issues.extend(collect_task307_mql5_compile_diagnostic_artifact_classification_doc_issues())
        issues.extend(collect_task308_mql5_compile_diagnostic_artifact_proof_boundary_doc_issues())
        issues.extend(collect_task309_mql5_compile_success_reclassification_boundary_doc_issues())
        issues.extend(collect_task310_mql5_compile_artifact_hash_capture_doc_issues())
        issues.extend(collect_task311_mql5_compile_success_reclassification_decision_boundary_doc_issues())
        issues.extend(collect_task312_mql5_compile_success_reclassification_decision_doc_issues())
        issues.extend(collect_task313_mt5_no_trade_startup_boundary_doc_issues())
        issues.extend(collect_task314_mt5_no_trade_startup_command_discovery_doc_issues())
        issues.extend(collect_task315_mt5_no_trade_startup_quarantine_preparation_doc_issues())
        issues.extend(collect_task316_mt5_no_trade_startup_dryrun_config_boundary_doc_issues())
        issues.extend(collect_task317_mt5_no_trade_startup_config_template_doc_issues())
        issues.extend(collect_task318_mt5_no_trade_startup_authorization_plan_doc_issues())
        issues.extend(collect_task319_mt5_no_trade_startup_preflight_gate_doc_issues())
        issues.extend(collect_mojibake_issues(docs_text))
        issues.extend(collect_prohibited_keyword_issues(docs_text))

    if issues:
        print("MQL5 compile-only boundary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQL5 compile-only boundary validation passed")
    print("mql5_compile_only_boundary=true")
    print("planning_only_boundary_only=true")
    print("future_mql5_compile_only_candidate=true")
    print("no_mt5_run=true")
    print("no_mql5_compile=true")
    print("no_metaeditor_execution=true")
    print("no_ex5_artifact=true")
    print("no_trading_authorization=true")
    print("MQ5 inventory remains 7 files")
    print("Buy / Sell / OrderSend / PositionOpen / CTrade remain false")
    print("Inventory only; no MT5 run; no trading authorization.")
    return 0


def main_v060_compile_readiness_planning():
    issues = collect_file_issues()
    if not issues:
        docs_text = {
            label: read_text(path)
            for label, path in DOC_PATHS.items()
        }
        issues.extend(collect_keyword_issues(docs_text))
        issues.extend(collect_task301_v060_compile_readiness_planning_doc_issues())
        issues.extend(collect_task302_mql5_compile_only_preflight_gate_doc_issues())
        issues.extend(collect_task303_mql5_compile_only_execution_authorization_plan_doc_issues())
        issues.extend(collect_task305_mql5_compile_only_failure_diagnostic_doc_issues())
        issues.extend(collect_task306_mql5_compile_diagnostic_result_classification_doc_issues())
        issues.extend(collect_task307_mql5_compile_diagnostic_artifact_classification_doc_issues())
        issues.extend(collect_task308_mql5_compile_diagnostic_artifact_proof_boundary_doc_issues())
        issues.extend(collect_task309_mql5_compile_success_reclassification_boundary_doc_issues())
        issues.extend(collect_task310_mql5_compile_artifact_hash_capture_doc_issues())
        issues.extend(collect_task311_mql5_compile_success_reclassification_decision_boundary_doc_issues())
        issues.extend(collect_task312_mql5_compile_success_reclassification_decision_doc_issues())
        issues.extend(collect_task313_mt5_no_trade_startup_boundary_doc_issues())
        issues.extend(collect_task314_mt5_no_trade_startup_command_discovery_doc_issues())
        issues.extend(collect_task315_mt5_no_trade_startup_quarantine_preparation_doc_issues())
        issues.extend(collect_task316_mt5_no_trade_startup_dryrun_config_boundary_doc_issues())
        issues.extend(collect_task317_mt5_no_trade_startup_config_template_doc_issues())
        issues.extend(collect_task318_mt5_no_trade_startup_authorization_plan_doc_issues())
        issues.extend(collect_task319_mt5_no_trade_startup_preflight_gate_doc_issues())
        issues.extend(collect_mojibake_issues(docs_text))
        issues.extend(collect_prohibited_keyword_issues(docs_text))

    if issues:
        print("v0.6.0 compile-readiness planning validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("v0.6.0 compile-readiness planning validation passed")
    print("v060_compile_readiness_planning=true")
    print("planning_only=true")
    print("future_compile_readiness_candidate=true")
    print("not_implementation_authorization=true")
    print("no_mt5_run=true")
    print("no_strategy_tester_run=true")
    print("no_mql5_compile=true")
    print("no_metaeditor_execution=true")
    print("no_ex5_artifact=true")
    print("no_manifest=true")
    print("no_evidence=true")
    print("no_report=true")
    print("MQ5 inventory 7 files")
    print("Buy / Sell / OrderSend / PositionOpen / CTrade false")
    print("Inventory only; no MT5 run; no trading authorization.")
    return 0


def main():
    issues = collect_file_issues()
    current_commit = None
    current_boundary = None

    if not issues:
        docs_text = {
            label: read_text(path)
            for label, path in DOC_PATHS.items()
        }
        issues.extend(collect_keyword_issues(docs_text))
        issues.extend(collect_plan_doc_issues())
        issues.extend(collect_task238_boundary_doc_issues())
        issues.extend(collect_task239_boundary_doc_issues())
        issues.extend(collect_task260_observability_extension_plan_doc_issues())
        issues.extend(collect_task261_observability_extension_next_plan_doc_issues())
        issues.extend(collect_task262_observability_extension_followup_plan_doc_issues())
        issues.extend(collect_task263_observability_extension_future_plan_doc_issues())
        issues.extend(collect_task294_mql5_compile_only_boundary_doc_issues())
        issues.extend(collect_task295_mql5_compile_only_command_discovery_doc_issues())
        issues.extend(collect_task296_mql5_compile_only_artifact_quarantine_doc_issues())
        issues.extend(collect_task297_mql5_compile_only_execution_boundary_doc_issues())
        issues.extend(collect_task298_mql5_compile_only_dryrun_doc_issues())
        issues.extend(collect_task300_mql5_compile_only_dryrun_execution_doc_issues())
        issues.extend(collect_task301_v060_compile_readiness_planning_doc_issues())
        issues.extend(collect_task302_mql5_compile_only_preflight_gate_doc_issues())
        issues.extend(collect_task303_mql5_compile_only_execution_authorization_plan_doc_issues())
        issues.extend(collect_task305_mql5_compile_only_failure_diagnostic_doc_issues())
        issues.extend(collect_task306_mql5_compile_diagnostic_result_classification_doc_issues())
        issues.extend(collect_task307_mql5_compile_diagnostic_artifact_classification_doc_issues())
        issues.extend(collect_task308_mql5_compile_diagnostic_artifact_proof_boundary_doc_issues())
        issues.extend(collect_task309_mql5_compile_success_reclassification_boundary_doc_issues())
        issues.extend(collect_task310_mql5_compile_artifact_hash_capture_doc_issues())
        issues.extend(collect_task311_mql5_compile_success_reclassification_decision_boundary_doc_issues())
        issues.extend(collect_task312_mql5_compile_success_reclassification_decision_doc_issues())
        issues.extend(collect_task313_mt5_no_trade_startup_boundary_doc_issues())
        issues.extend(collect_task314_mt5_no_trade_startup_command_discovery_doc_issues())
        issues.extend(collect_task315_mt5_no_trade_startup_quarantine_preparation_doc_issues())
        issues.extend(collect_task316_mt5_no_trade_startup_dryrun_config_boundary_doc_issues())
        issues.extend(collect_task317_mt5_no_trade_startup_config_template_doc_issues())
        issues.extend(collect_task318_mt5_no_trade_startup_authorization_plan_doc_issues())
        issues.extend(collect_task319_mt5_no_trade_startup_preflight_gate_doc_issues())
        issues.extend(collect_task321_parser_pipeline_integration_doc_issues())
        issues.extend(collect_mojibake_issues(docs_text))
        issues.extend(collect_prohibited_keyword_issues(docs_text))

        dynamic_issues, current_commits, current_boundaries = (
            collect_dynamic_consistency_issues(docs_text)
        )
        issues.extend(dynamic_issues)
        if current_commits:
            current_commit = next(iter(current_commits.values())).split()[0]
        if current_boundaries:
            current_boundary = next(iter(current_boundaries.values()))

    if issues:
        print("Project state docs validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Project state docs validation passed")
    if current_commit:
        print(f"Current latest commit: {current_commit}")
    if current_boundary:
        print(f"Current next boundary: {current_boundary}")
    return 0


if __name__ == "__main__":
    if "--mq5-static-interface-consistency" in sys.argv[1:]:
        sys.exit(main_mq5_static_interface_consistency())
    if "--mql5-compile-only-boundary" in sys.argv[1:]:
        sys.exit(main_mql5_compile_only_boundary())
    if "--v060-compile-readiness-planning" in sys.argv[1:]:
        sys.exit(main_v060_compile_readiness_planning())
    sys.exit(main())
