#!/usr/bin/env python3
"""Validate the MQ5 no-trade observability scaffold contract.

This read-only validator performs static text checks only. It does not run MT5,
compile MQ5, create reports, create manifests, or copy external evidence.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MQ5_ROOT = ROOT_DIR / "mq5"

PASS_TEXT = "MQ5 no-trade observability contract validator PASS"
FAIL_TEXT = "MQ5 no-trade observability contract validator FAIL"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

SOURCE_EXTENSIONS = (".mq5", ".mqh")
EXPECTED_SOURCE_FILE_COUNT = 7
REQUIRED_FILES = (
    "config/InputConfig.mqh",
    "core/EaController.mqh",
    "logger/Logger.mqh",
    "signals/SignalEngine.mqh",
    "risk/RiskManager.mqh",
    "execution/ExecutionManager.mqh",
)
FORBIDDEN_TRADING_KEYWORDS = (
    "Buy",
    "Sell",
    "OrderSend",
    "PositionOpen",
    "CTrade",
)
STRUCTURED_SNAPSHOT_FIELDS = (
    "mode=no-trade observability scaffold",
    f"inventory_notice={SAFETY_NOTICE}",
    "enable_trading",
    "observability_enabled",
    "init_log_enabled",
    "tick_log_enabled",
)
LOGGER_COMPONENT_SNAPSHOT_FIELDS = (
    "component_status_snapshot=true",
    "controller_status=ready",
    "logger_status=ready",
    "all_components_no_trade=true",
)
COMPONENT_SNAPSHOT_FIELDS = (
    "signal_status=read-only framework",
    "risk_status=read-only framework",
    "execution_status=read-only framework",
)
COMPONENT_METHODS = (
    ("signals/SignalEngine.mqh", "GetSignalStatusSnapshot", "signal_active=false"),
    ("risk/RiskManager.mqh", "GetRiskStatusSnapshot", "risk_active=false"),
    ("execution/ExecutionManager.mqh", "GetExecutionStatusSnapshot", "execution_active=false"),
)
LIFECYCLE_TELEMETRY_FIELDS = (
    "lifecycle_event=init",
    "lifecycle_event=tick",
    "lifecycle_event=deinit",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
)
LIFECYCLE_CONTROLLER_MARKERS = (
    ('LogNoTradeLifecycleEvent("CORE"', "EaController missing lifecycle telemetry helper call"),
    ('"init"', "EaController missing init lifecycle path"),
    ('"tick"', "EaController missing tick lifecycle path"),
    ('"deinit"', "EaController missing deinit lifecycle path"),
    ("OnDeinit", "EaController missing deinit lifecycle method"),
)
RUNTIME_STATUS_SNAPSHOT_FIELDS = (
    "runtime_status_snapshot=true",
    "controller_status=ready",
    "logger_status=ready",
    "signal_status=read-only framework",
    "risk_status=read-only framework",
    "execution_status=read-only framework",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
RUNTIME_CONTROLLER_MARKERS = (
    ("WriteReadOnlyRuntimeStatusSnapshot(eventName);", "EaController missing init/tick runtime status snapshot path"),
    ('WriteReadOnlyRuntimeStatusSnapshot("No-trade observability deinit");', "EaController missing deinit runtime status snapshot path"),
    ('logger.LogReadOnlyRuntimeStatusSnapshot("CORE"', "EaController missing runtime status snapshot helper call"),
)
PERFORMANCE_METRICS_FIELDS = (
    "runtime_metrics_snapshot=true",
    "tick_count",
    "oninit_call_count",
    "ondeinit_call_count",
    "last_tick_timestamp",
    "all_components_no_trade=true",
    "trading_authorization=false",
    "mt5_run_required=false",
    SAFETY_NOTICE,
)
PERFORMANCE_CONTROLLER_MARKERS = (
    ("WriteNoTradePerformanceMetrics(eventName);", "EaController missing init/tick performance metrics path"),
    ('WriteNoTradePerformanceMetrics("No-trade observability deinit");', "EaController missing deinit performance metrics path"),
    ('logger.LogNoTradePerformanceMetrics("CORE"', "EaController missing performance metrics helper call"),
    ("onInitCallCount++", "EaController missing OnInit performance counter"),
    ("onDeinitCallCount++", "EaController missing OnDeinit performance counter"),
    ("lastTickTimestamp = TimeCurrent();", "EaController missing last tick timestamp update"),
)
SAFETY_GUARD_INVARIANT_FIELDS = (
    "safety_guard_snapshot=true",
    "no_trade_guard=active",
    "invariant_trading_disabled=true",
    "invariant_execution_disabled=true",
    "invariant_order_submission_disabled=true",
    "invariant_position_management_disabled=true",
    "invariant_external_evidence_disabled=true",
    "invariant_manifest_generation_disabled=true",
    "invariant_mt5_run_required=false",
    "invariant_all_components_no_trade=true",
    "trading_authorization=false",
    SAFETY_NOTICE,
)
SAFETY_GUARD_CONTROLLER_MARKERS = (
    ("WriteNoTradeSafetyGuardInvariants(eventName);", "EaController missing init/tick safety guard invariant path"),
    ('WriteNoTradeSafetyGuardInvariants("No-trade observability deinit");', "EaController missing deinit safety guard invariant path"),
    ('logger.LogNoTradeSafetyGuardInvariants("CORE"', "EaController missing safety guard invariant helper call"),
)
METRICS_AGGREGATION_FIELDS = (
    "metrics_aggregation_snapshot=true",
    "historical_events_count",
    "last_n_ticks_metrics",
    "aggregated_component_status",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
METRICS_AGGREGATION_CONTROLLER_MARKERS = (
    ("WriteReadOnlyMetricsAggregation(eventName);", "EaController missing init/tick metrics aggregation path"),
    ('WriteReadOnlyMetricsAggregation("No-trade observability deinit");', "EaController missing deinit metrics aggregation path"),
    ('logger.LogReadOnlyMetricsAggregation("CORE"', "EaController missing metrics aggregation helper call"),
    ("CalculateHistoricalEventsCount(),", "EaController missing historical event count aggregation"),
    ("BuildLastNTicksMetrics(),", "EaController missing last N ticks metrics aggregation"),
    ("                                           BuildAggregatedComponentStatus(),", "EaController missing component status aggregation"),
)
SYSTEM_HEALTH_FIELDS = (
    "system_health_snapshot=true",
    "observability_enabled",
    "last_snapshot_timestamp",
    "aggregated_component_status",
    "all_components_no_trade=true",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
SYSTEM_HEALTH_CONTROLLER_MARKERS = (
    ("WriteReadOnlySystemHealth(eventName);", "EaController missing init/tick system health path"),
    ('WriteReadOnlySystemHealth("No-trade observability deinit");', "EaController missing deinit system health path"),
    ('logger.LogReadOnlySystemHealth("CORE"', "EaController missing system health helper call"),
    ("                                     BuildAggregatedComponentStatus(),", "EaController missing system health component status aggregation"),
)
SIGNAL_CONTEXT_FIELDS = (
    "signal_context_snapshot=true",
    "signal_layer_mode=read-only framework",
    "signal_context_available=true",
    "signal_direction_authorized=false",
    "signal_execution_authorized=false",
    "signal_order_intent=false",
    "signal_external_evidence_required=false",
    "signal_manifest_generation=false",
    "no_trade_guard=active",
)
SIGNAL_CONTEXT_LOGGER_FIELDS = (
    "signalContextSnapshot",
    "trading_authorization=false",
    SAFETY_NOTICE,
)
SIGNAL_CONTEXT_CONTROLLER_MARKERS = (
    ("WriteReadOnlySignalContextSnapshot(eventName);", "EaController missing init/tick signal context path"),
    ('WriteReadOnlySignalContextSnapshot("No-trade observability deinit");', "EaController missing deinit signal context path"),
    ('logger.LogReadOnlySignalContextSnapshot("CORE"', "EaController missing signal context helper call"),
    ("signalEngine.GetReadOnlySignalContextSnapshot()", "EaController missing signal context source"),
)
RISK_CONTEXT_FIELDS = (
    "risk_context_snapshot=true",
    "risk_layer_mode=read-only framework",
    "risk_context_available=true",
    "risk_authorization=false",
    "risk_sizing_authorized=false",
    "risk_exposure_authorized=false",
    "risk_execution_authorized=false",
    "risk_external_evidence_required=false",
    "risk_manifest_generation=false",
    "no_trade_guard=active",
)
RISK_CONTEXT_LOGGER_FIELDS = (
    "riskContextSnapshot",
    "trading_authorization=false",
    SAFETY_NOTICE,
)
RISK_CONTEXT_CONTROLLER_MARKERS = (
    ("WriteReadOnlyRiskContextSnapshot(eventName);", "EaController missing init/tick risk context path"),
    ('WriteReadOnlyRiskContextSnapshot("No-trade observability deinit");', "EaController missing deinit risk context path"),
    ('logger.LogReadOnlyRiskContextSnapshot("CORE"', "EaController missing risk context helper call"),
    ("riskManager.GetReadOnlyRiskContextSnapshot()", "EaController missing risk context source"),
)
EXECUTION_CONTEXT_FIELDS = (
    "execution_context_snapshot=true",
    "execution_layer_mode=read-only framework",
    "execution_context_available=true",
    "execution_authorization=false",
    "execution_request_authorized=false",
    "execution_route_authorized=false",
    "execution_dispatch_authorized=false",
    "execution_external_evidence_required=false",
    "execution_manifest_generation=false",
    "no_trade_guard=active",
)
EXECUTION_CONTEXT_LOGGER_FIELDS = (
    "executionContextSnapshot",
    "trading_authorization=false",
    SAFETY_NOTICE,
)
EXECUTION_CONTEXT_CONTROLLER_MARKERS = (
    ("WriteReadOnlyExecutionContextSnapshot(eventName);", "EaController missing init/tick execution context path"),
    ('WriteReadOnlyExecutionContextSnapshot("No-trade observability deinit");', "EaController missing deinit execution context path"),
    ('logger.LogReadOnlyExecutionContextSnapshot("CORE"', "EaController missing execution context helper call"),
    ("executionManager.GetReadOnlyExecutionContextSnapshot()", "EaController missing execution context source"),
)
PIPELINE_CONTEXT_AGGREGATION_FIELDS = (
    "pipeline_context_snapshot=true",
    "pipeline_layer_mode=read-only framework",
    "signal_context_linked=true",
    "risk_context_linked=true",
    "execution_context_linked=true",
    "pipeline_authorization=false",
    "pipeline_direction_authorized=false",
    "pipeline_risk_authorized=false",
    "pipeline_execution_authorized=false",
    "pipeline_dispatch_authorized=false",
    "pipeline_intent=false",
    "all_pipeline_layers_no_trade=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
PIPELINE_CONTEXT_CONTROLLER_MARKERS = (
    ("WriteReadOnlyPipelineContextAggregationSnapshot(eventName);", "EaController missing init/tick pipeline context aggregation path"),
    ('WriteReadOnlyPipelineContextAggregationSnapshot("No-trade observability deinit");', "EaController missing deinit pipeline context aggregation path"),
    ('logger.LogReadOnlyPipelineContextAggregationSnapshot("CORE"', "EaController missing pipeline context aggregation helper call"),
)
AUTHORIZATION_MATRIX_FIELDS = (
    "authorization_matrix_snapshot=true",
    "authorization_matrix_mode=read-only framework",
    "signal_authorization=false",
    "signal_direction_authorized=false",
    "risk_authorization=false",
    "risk_sizing_authorized=false",
    "risk_exposure_authorized=false",
    "execution_authorization=false",
    "execution_request_authorized=false",
    "execution_dispatch_authorized=false",
    "pipeline_authorization=false",
    "pipeline_intent=false",
    "trading_authorization=false",
    "all_authorizations_false=true",
    "all_pipeline_layers_no_trade=true",
    "no_trade_guard=active",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
AUTHORIZATION_MATRIX_CONTROLLER_MARKERS = (
    ("WriteReadOnlyAuthorizationMatrixSnapshot(eventName);", "EaController missing init/tick authorization matrix path"),
    ('WriteReadOnlyAuthorizationMatrixSnapshot("No-trade observability deinit");', "EaController missing deinit authorization matrix path"),
    ('logger.LogReadOnlyAuthorizationMatrixSnapshot("CORE"', "EaController missing authorization matrix helper call"),
)
DECISION_GATE_FIELDS = (
    "decision_gate_snapshot=true",
    "decision_gate_mode=read-only framework",
    "decision_state=blocked_no_trade",
    "decision_candidate_available=false",
    "decision_direction_authorized=false",
    "decision_risk_authorized=false",
    "decision_execution_authorized=false",
    "decision_dispatch_authorized=false",
    "decision_output_authorized=false",
    "decision_intent=false",
    "all_authorizations_false=true",
    "all_pipeline_layers_no_trade=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
DECISION_GATE_CONTROLLER_MARKERS = (
    ("WriteReadOnlyDecisionGateSnapshot(eventName);", "EaController missing init/tick decision gate path"),
    ('WriteReadOnlyDecisionGateSnapshot("No-trade observability deinit");', "EaController missing deinit decision gate path"),
    ('logger.LogReadOnlyDecisionGateSnapshot("CORE"', "EaController missing decision gate helper call"),
)
DECISION_REJECTION_FIELDS = (
    "decision_rejection_snapshot=true",
    "decision_rejection_mode=read-only framework",
    "rejection_reason=no_trade_guard_active",
    "rejection_trading_authorization=false",
    "rejection_signal_authorization=false",
    "rejection_risk_authorization=false",
    "rejection_execution_authorization=false",
    "rejection_pipeline_authorization=false",
    "rejection_external_evidence=false",
    "rejection_manifest_generation=false",
    "rejection_mt5_run_required=false",
    "decision_state=blocked_no_trade",
    "decision_intent=false",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    SAFETY_NOTICE,
)
DECISION_REJECTION_CONTROLLER_MARKERS = (
    ("WriteReadOnlyDecisionRejectionReasonSnapshot(eventName);", "EaController missing init/tick decision rejection reason path"),
    ('WriteReadOnlyDecisionRejectionReasonSnapshot("No-trade observability deinit");', "EaController missing deinit decision rejection reason path"),
    ('logger.LogReadOnlyDecisionRejectionReasonSnapshot("CORE"', "EaController missing decision rejection reason helper call"),
)
OBSERVABILITY_CONSOLIDATION_FIELDS = (
    "observability_consolidation_snapshot=true",
    "observability_consolidation_mode=read-only framework",
    "observability_contract_version=v0.6.0-no-trade",
    "structured_snapshot_linked=true",
    "component_status_linked=true",
    "lifecycle_telemetry_linked=true",
    "runtime_status_linked=true",
    "performance_metrics_linked=true",
    "safety_guard_linked=true",
    "signal_context_linked=true",
    "risk_context_linked=true",
    "execution_context_linked=true",
    "pipeline_context_linked=true",
    "authorization_matrix_linked=true",
    "decision_gate_linked=true",
    "decision_rejection_linked=true",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "all_pipeline_layers_no_trade=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
OBSERVABILITY_CONSOLIDATION_CONTROLLER_MARKERS = (
    ("WriteReadOnlyObservabilityConsolidationSnapshot(eventName);", "EaController missing init/tick observability consolidation path"),
    ('WriteReadOnlyObservabilityConsolidationSnapshot("No-trade observability deinit");', "EaController missing deinit observability consolidation path"),
    ('logger.LogReadOnlyObservabilityConsolidationSnapshot("CORE"', "EaController missing observability consolidation helper call"),
)
OBSERVABILITY_REGISTRY_FIELDS = (
    "observability_contract_registry_snapshot=true",
    "observability_contract_registry_mode=read-only framework",
    "observability_contract_registry_version=v0.6.0-no-trade",
    "registered_contract_count",
    " | registered_contracts_read_only=true",
    "registered_contracts_no_trade=true",
    "structured_snapshot_registered=true",
    "component_status_registered=true",
    "lifecycle_telemetry_registered=true",
    "runtime_status_registered=true",
    "performance_metrics_registered=true",
    "safety_guard_registered=true",
    "metrics_aggregation_registered=true",
    "system_health_registered=true",
    "signal_context_registered=true",
    "risk_context_registered=true",
    "execution_context_registered=true",
    "pipeline_context_registered=true",
    "authorization_matrix_registered=true",
    "decision_gate_registered=true",
    "decision_rejection_registered=true",
    "observability_consolidation_registered=true",
    "all_registered_contracts_static=true",
    "all_registered_contracts_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
OBSERVABILITY_REGISTRY_CONTROLLER_MARKERS = (
    ("WriteReadOnlyObservabilityContractRegistrySnapshot(eventName);", "EaController missing init/tick observability registry path"),
    ('WriteReadOnlyObservabilityContractRegistrySnapshot("No-trade observability deinit");', "EaController missing deinit observability registry path"),
    ('logger.LogReadOnlyObservabilityContractRegistrySnapshot("CORE"', "EaController missing observability registry helper call"),
)
OBSERVABILITY_ERROR_FIELDS = (
    "error_snapshot=true",
    "error_type=read-only framework",
    "error_timestamp",
    "component_origin",
    "error_details",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
OBSERVABILITY_ERROR_CONTROLLER_MARKERS = (
    ("WriteReadOnlyObservabilityErrorSnapshot(eventName);", "EaController missing init/tick observability error path"),
    ('WriteReadOnlyObservabilityErrorSnapshot("No-trade observability deinit");', "EaController missing deinit observability error path"),
    ('logger.LogReadOnlyObservabilityErrorSnapshot("CORE"', "EaController missing observability error helper call"),
)
TELEMETRY_AGGREGATION_FIELDS = (
    "telemetry_aggregation_snapshot=true",
    "aggregated_errors_linked=true",
    "aggregated_metrics_linked=true",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
TELEMETRY_AGGREGATION_CONTROLLER_MARKERS = (
    ("WriteReadOnlyTelemetryAggregationSnapshot(eventName);", "EaController missing init/tick telemetry aggregation path"),
    ('WriteReadOnlyTelemetryAggregationSnapshot("No-trade observability deinit");', "EaController missing deinit telemetry aggregation path"),
    ('logger.LogReadOnlyTelemetryAggregationSnapshot("CORE"', "EaController missing telemetry aggregation helper call"),
)
CONTROLLER_SUMMARY_FIELDS = (
    "controller_summary_snapshot=true",
    " | init_path_linked=true",
    " | tick_path_linked=true",
    " | deinit_path_linked=true",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
CONTROLLER_SUMMARY_CONTROLLER_MARKERS = (
    ("WriteReadOnlyControllerSummarySnapshot(eventName);", "EaController missing init/tick controller summary path"),
    ('WriteReadOnlyControllerSummarySnapshot("No-trade observability deinit");', "EaController missing deinit controller summary path"),
    ('logger.LogReadOnlyControllerSummarySnapshot("CORE"', "EaController missing controller summary helper call"),
)
OBSERVABILITY_OUTPUT_REDUCTION_FIELDS = (
    "observability_output_reduction_snapshot=true",
    "output_reduction_mode=read-only framework",
    "duplicate_output_guard=active",
    "controller_logger_deduplication=true",
    "init_output_group=consolidated",
    "tick_output_group=gated",
    "deinit_output_group=final",
    "tick_output_requires_InpObservabilityLogOnTick=true",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "all_pipeline_layers_no_trade=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    SAFETY_NOTICE,
)
OBSERVABILITY_OUTPUT_REDUCTION_CONTROLLER_MARKERS = (
    ("WriteReadOnlyObservabilityOutputReductionSnapshot(eventName);", "EaController missing init/tick observability output reduction path"),
    ('WriteReadOnlyObservabilityOutputReductionSnapshot("No-trade observability deinit");', "EaController missing deinit observability output reduction path"),
    ('logger.LogReadOnlyObservabilityOutputReductionSnapshot("CORE"', "EaController missing observability output reduction helper call"),
)


def normalize_root(path: str | Path) -> Path:
    root = Path(path)
    if not root.is_absolute():
        root = ROOT_DIR / root
    return root.resolve()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="replace")


def find_source_files(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS
        ),
        key=lambda path: path.relative_to(root).as_posix().lower(),
    )


def bool_input_defaults_to(text: str, name: str, expected: str) -> bool:
    pattern = re.compile(
        rf"^\s*input\s+bool\s+{re.escape(name)}\s*=\s*{expected}\s*;",
        re.MULTILINE,
    )
    return bool(pattern.search(text))


def text_after_marker(text: str, marker: str) -> str:
    if marker not in text:
        return ""
    return text.split(marker, 1)[1]


def text_between_markers(text: str, start_marker: str, end_marker: str) -> str:
    section = text_after_marker(text, start_marker)
    if not section or end_marker not in section:
        return section
    return section.split(end_marker, 1)[0]


def validate_texts(
    files: dict[str, str | None],
    all_source_texts: dict[str, str],
) -> list[str]:
    failures: list[str] = []

    if len(all_source_texts) != EXPECTED_SOURCE_FILE_COUNT:
        failures.append(
            "MQ5 inventory source file count changed: "
            f"expected {EXPECTED_SOURCE_FILE_COUNT}, got {len(all_source_texts)}"
        )

    for rel_path in REQUIRED_FILES:
        if not files.get(rel_path):
            failures.append(f"missing required MQ5 source file: {rel_path}")

    input_config = files.get("config/InputConfig.mqh") or ""
    required_defaults = (
        ("InpEnableTrading", "false"),
        ("InpEnableNoTradeObservability", "true"),
        ("InpObservabilityLogOnInit", "true"),
        ("InpObservabilityLogOnTick", "false"),
    )
    for name, expected in required_defaults:
        if not bool_input_defaults_to(input_config, name, expected):
            failures.append(f"{name} default is not {expected}")

    logger = files.get("logger/Logger.mqh") or ""
    if "NoTradeObservability" not in logger:
        failures.append("Logger missing no-trade observability helper")
    if "NoTradeObservabilityStatusSnapshot" not in logger:
        failures.append("Logger missing structured status snapshot helper")
    if "no-trade observability scaffold" not in logger:
        failures.append("Logger missing no-trade observability scaffold text")
    if SAFETY_NOTICE not in logger:
        failures.append("Logger missing no MT5 / no trading authorization notice")
    structured_section = text_between_markers(
        logger,
        "NoTradeObservabilityStatusSnapshot",
        "NoTradeComponentStatusSnapshot",
    )
    for field in STRUCTURED_SNAPSHOT_FIELDS:
        if field not in structured_section:
            failures.append(f"Logger missing structured snapshot field: {field}")
    if "NoTradeComponentStatusSnapshot" not in logger:
        failures.append("Logger missing component status snapshot helper")
    component_section = text_between_markers(
        logger,
        "NoTradeComponentStatusSnapshot",
        "BuildLifecycleEventField",
    )
    for field in LOGGER_COMPONENT_SNAPSHOT_FIELDS:
        if field not in component_section:
            failures.append(f"Logger missing component snapshot field: {field}")
    if "LogNoTradeLifecycleEvent" not in logger:
        failures.append("Logger missing no-trade lifecycle telemetry helper")
    lifecycle_section = text_between_markers(
        logger,
        "BuildLifecycleEventField",
        "LogReadOnlyRuntimeStatusSnapshot",
    )
    for field in LIFECYCLE_TELEMETRY_FIELDS:
        if field not in lifecycle_section:
            failures.append(f"Logger missing lifecycle telemetry field: {field}")
    runtime_section = text_between_markers(
        logger,
        "LogReadOnlyRuntimeStatusSnapshot",
        "LogNoTradePerformanceMetrics",
    )
    if not runtime_section:
        failures.append("Logger missing read-only runtime status snapshot helper")
    for field in RUNTIME_STATUS_SNAPSHOT_FIELDS:
        if field not in runtime_section:
            failures.append(f"Logger missing runtime status snapshot field: {field}")
    performance_section = text_between_markers(
        logger,
        "LogNoTradePerformanceMetrics",
        "LogNoTradeSafetyGuardInvariants",
    )
    if not performance_section:
        failures.append("Logger missing no-trade performance metrics helper")
    for field in PERFORMANCE_METRICS_FIELDS:
        if field not in performance_section:
            failures.append(f"Logger missing performance metrics field: {field}")
    safety_guard_section = text_between_markers(
        logger,
        "LogNoTradeSafetyGuardInvariants",
        "LogReadOnlyMetricsAggregation",
    )
    if not safety_guard_section:
        failures.append("Logger missing no-trade safety guard invariant helper")
    for field in SAFETY_GUARD_INVARIANT_FIELDS:
        if field not in safety_guard_section:
            failures.append(f"Logger missing safety guard invariant field: {field}")
    aggregation_section = text_between_markers(
        logger,
        "LogReadOnlyMetricsAggregation",
        "LogReadOnlySystemHealth",
    )
    if not aggregation_section:
        failures.append("Logger missing read-only metrics aggregation helper")
    for field in METRICS_AGGREGATION_FIELDS:
        if field not in aggregation_section:
            failures.append(f"Logger missing metrics aggregation field: {field}")
    health_section = text_between_markers(
        logger,
        "LogReadOnlySystemHealth",
        "LogReadOnlySignalContextSnapshot",
    )
    if not health_section:
        failures.append("Logger missing read-only system health helper")
    for field in SYSTEM_HEALTH_FIELDS:
        if field not in health_section:
            failures.append(f"Logger missing system health field: {field}")
    signal_logger_section = text_between_markers(
        logger,
        "LogReadOnlySignalContextSnapshot",
        "LogReadOnlyRiskContextSnapshot",
    )
    if not signal_logger_section:
        failures.append("Logger missing read-only signal context snapshot helper")
    for field in SIGNAL_CONTEXT_LOGGER_FIELDS:
        if field not in signal_logger_section:
            failures.append(f"Logger missing signal context field: {field}")
    risk_logger_section = text_between_markers(
        logger,
        "LogReadOnlyRiskContextSnapshot",
        "LogReadOnlyExecutionContextSnapshot",
    )
    if not risk_logger_section:
        failures.append("Logger missing read-only risk context snapshot helper")
    for field in RISK_CONTEXT_LOGGER_FIELDS:
        if field not in risk_logger_section:
            failures.append(f"Logger missing risk context field: {field}")
    execution_logger_section = text_between_markers(
        logger,
        "LogReadOnlyExecutionContextSnapshot",
        "LogReadOnlyPipelineContextAggregationSnapshot",
    )
    if not execution_logger_section:
        failures.append("Logger missing read-only execution context snapshot helper")
    for field in EXECUTION_CONTEXT_LOGGER_FIELDS:
        if field not in execution_logger_section:
            failures.append(f"Logger missing execution context field: {field}")
    pipeline_logger_section = text_between_markers(
        logger,
        "LogReadOnlyPipelineContextAggregationSnapshot",
        "LogReadOnlyAuthorizationMatrixSnapshot",
    )
    if not pipeline_logger_section:
        failures.append("Logger missing read-only pipeline context aggregation snapshot helper")
    for field in PIPELINE_CONTEXT_AGGREGATION_FIELDS:
        if field not in pipeline_logger_section:
            failures.append(f"Logger missing pipeline context aggregation field: {field}")
    authorization_matrix_section = text_between_markers(
        logger,
        "LogReadOnlyAuthorizationMatrixSnapshot",
        "LogReadOnlyDecisionGateSnapshot",
    )
    if not authorization_matrix_section:
        failures.append("Logger missing read-only authorization matrix snapshot helper")
    for field in AUTHORIZATION_MATRIX_FIELDS:
        if field not in authorization_matrix_section:
            failures.append(f"Logger missing authorization matrix field: {field}")
    decision_gate_section = text_between_markers(
        logger,
        "LogReadOnlyDecisionGateSnapshot",
        "LogReadOnlyDecisionRejectionReasonSnapshot",
    )
    if not decision_gate_section:
        failures.append("Logger missing read-only decision gate snapshot helper")
    for field in DECISION_GATE_FIELDS:
        if field not in decision_gate_section:
            failures.append(f"Logger missing decision gate field: {field}")
    decision_rejection_section = text_between_markers(
        logger,
        "LogReadOnlyDecisionRejectionReasonSnapshot",
        "LogReadOnlyObservabilityConsolidationSnapshot",
    )
    if not decision_rejection_section:
        failures.append("Logger missing read-only decision rejection reason snapshot helper")
    for field in DECISION_REJECTION_FIELDS:
        if field not in decision_rejection_section:
            failures.append(f"Logger missing decision rejection reason field: {field}")
    observability_consolidation_section = text_between_markers(
        logger,
        "LogReadOnlyObservabilityConsolidationSnapshot",
        "LogReadOnlyObservabilityContractRegistrySnapshot",
    )
    if not observability_consolidation_section:
        failures.append("Logger missing read-only observability consolidation snapshot helper")
    for field in OBSERVABILITY_CONSOLIDATION_FIELDS:
        if field not in observability_consolidation_section:
            failures.append(f"Logger missing observability consolidation field: {field}")
    observability_registry_section = text_between_markers(
        logger,
        "LogReadOnlyObservabilityContractRegistrySnapshot",
        "LogReadOnlyObservabilityErrorSnapshot",
    )
    if not observability_registry_section:
        failures.append("Logger missing read-only observability contract registry snapshot helper")
    for field in OBSERVABILITY_REGISTRY_FIELDS:
        if field not in observability_registry_section:
            failures.append(f"Logger missing observability registry field: {field}")
    observability_error_section = text_between_markers(
        logger,
        "LogReadOnlyObservabilityErrorSnapshot",
        "LogReadOnlyTelemetryAggregationSnapshot",
    )
    if not observability_error_section:
        failures.append("Logger missing read-only observability error snapshot helper")
    for field in OBSERVABILITY_ERROR_FIELDS:
        if field not in observability_error_section:
            failures.append(f"Logger missing observability error field: {field}")
    telemetry_aggregation_section = text_between_markers(
        logger,
        "LogReadOnlyTelemetryAggregationSnapshot",
        "LogReadOnlyControllerSummarySnapshot",
    )
    if not telemetry_aggregation_section:
        failures.append("Logger missing read-only telemetry aggregation snapshot helper")
    for field in TELEMETRY_AGGREGATION_FIELDS:
        if field not in telemetry_aggregation_section:
            failures.append(f"Logger missing telemetry aggregation field: {field}")
    controller_summary_section = text_between_markers(
        logger,
        "LogReadOnlyControllerSummarySnapshot",
        "LogReadOnlyObservabilityOutputReductionSnapshot",
    )
    if not controller_summary_section:
        failures.append("Logger missing read-only controller summary snapshot helper")
    for field in CONTROLLER_SUMMARY_FIELDS:
        if field not in controller_summary_section:
            failures.append(f"Logger missing controller summary field: {field}")
    observability_output_reduction_section = text_between_markers(
        logger,
        "LogReadOnlyObservabilityOutputReductionSnapshot",
        "   string BoolToText",
    )
    if not observability_output_reduction_section:
        failures.append("Logger missing read-only observability output reduction snapshot helper")
    for field in OBSERVABILITY_OUTPUT_REDUCTION_FIELDS:
        if field not in observability_output_reduction_section:
            failures.append(f"Logger missing observability output reduction field: {field}")

    controller = files.get("core/EaController.mqh") or ""
    if "InpObservabilityLogOnInit" not in controller or "WriteNoTradeObservability" not in controller:
        failures.append("EaController missing OnInit no-trade observability path")
    if "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController missing input-controlled OnTick observability path")
    if "NoTradeObservabilityStatusSnapshot" not in controller:
        failures.append("EaController missing structured status snapshot helper call")
    if "NoTradeComponentStatusSnapshot" not in controller:
        failures.append("EaController missing component status snapshot helper call")
    for method_name in (
        "GetSignalStatusSnapshot",
        "GetRiskStatusSnapshot",
        "GetExecutionStatusSnapshot",
    ):
        if method_name not in controller:
            failures.append(f"EaController missing component snapshot source: {method_name}")
    for marker, message in LIFECYCLE_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in RUNTIME_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in PERFORMANCE_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in SAFETY_GUARD_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in METRICS_AGGREGATION_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in SYSTEM_HEALTH_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in SIGNAL_CONTEXT_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in RISK_CONTEXT_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in EXECUTION_CONTEXT_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in PIPELINE_CONTEXT_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in AUTHORIZATION_MATRIX_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in DECISION_GATE_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in DECISION_REJECTION_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in OBSERVABILITY_CONSOLIDATION_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in OBSERVABILITY_REGISTRY_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in OBSERVABILITY_ERROR_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in TELEMETRY_AGGREGATION_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in CONTROLLER_SUMMARY_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    for marker, message in OBSERVABILITY_OUTPUT_REDUCTION_CONTROLLER_MARKERS:
        if marker not in controller:
            failures.append(message)
    if "WriteReadOnlySignalContextSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController signal context tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyRiskContextSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController risk context tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyExecutionContextSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController execution context tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyPipelineContextAggregationSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController pipeline context aggregation tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyAuthorizationMatrixSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController authorization matrix tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyDecisionGateSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController decision gate tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyDecisionRejectionReasonSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController decision rejection reason tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyObservabilityConsolidationSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController observability consolidation tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyObservabilityContractRegistrySnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController observability registry tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyObservabilityErrorSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController observability error tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyTelemetryAggregationSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController telemetry aggregation tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyControllerSummarySnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController controller summary tick path is not controlled by InpObservabilityLogOnTick")
    if "WriteReadOnlyObservabilityOutputReductionSnapshot(eventName);" in controller and "InpObservabilityLogOnTick" not in controller:
        failures.append("EaController observability output reduction tick path is not controlled by InpObservabilityLogOnTick")

    for rel_path, method_name, active_field in COMPONENT_METHODS:
        component_text = files.get(rel_path) or ""
        if method_name not in component_text:
            failures.append(f"{rel_path} missing component snapshot method: {method_name}")
        if active_field not in component_text:
            failures.append(f"{rel_path} missing component active field: {active_field}")

    signal_text = files.get("signals/SignalEngine.mqh") or ""
    if "signal_status=read-only framework" not in signal_text:
        failures.append("SignalEngine missing read-only signal status field")
    if "GetReadOnlySignalContextSnapshot" not in signal_text:
        failures.append("SignalEngine missing read-only signal context snapshot method")
    signal_context_section = text_between_markers(
        signal_text,
        "GetReadOnlySignalContextSnapshot",
        "SignalResult Evaluate",
    )
    for field in SIGNAL_CONTEXT_FIELDS:
        if field not in signal_context_section:
            failures.append(f"SignalEngine missing signal context field: {field}")

    risk_text = files.get("risk/RiskManager.mqh") or ""
    if "risk_status=read-only framework" not in risk_text:
        failures.append("RiskManager missing read-only risk status field")
    if "GetReadOnlyRiskContextSnapshot" not in risk_text:
        failures.append("RiskManager missing read-only risk context snapshot method")
    risk_context_section = text_between_markers(
        risk_text,
        "GetReadOnlyRiskContextSnapshot",
        "bool CanExecuteSignal",
    )
    for field in RISK_CONTEXT_FIELDS:
        if field not in risk_context_section:
            failures.append(f"RiskManager missing risk context field: {field}")

    execution_text = files.get("execution/ExecutionManager.mqh") or ""
    if "execution_status=read-only framework" not in execution_text:
        failures.append("ExecutionManager missing read-only execution status field")
    if "GetReadOnlyExecutionContextSnapshot" not in execution_text:
        failures.append("ExecutionManager missing read-only execution context snapshot method")
    execution_context_section = text_between_markers(
        execution_text,
        "GetReadOnlyExecutionContextSnapshot",
        "bool ExecuteSignal",
    )
    for field in EXECUTION_CONTEXT_FIELDS:
        if field not in execution_context_section:
            failures.append(f"ExecutionManager missing execution context field: {field}")

    for rel_path, text in all_source_texts.items():
        for keyword in FORBIDDEN_TRADING_KEYWORDS:
            if keyword in text:
                failures.append(f"{rel_path} contains forbidden trading keyword: {keyword}")

    return failures


def load_repository_texts(mq5_root: Path) -> tuple[dict[str, str | None], dict[str, str]]:
    required = {}
    for rel_path in REQUIRED_FILES:
        path = mq5_root / rel_path
        required[rel_path] = read_text(path) if path.exists() else None

    all_sources = {}
    for path in find_source_files(mq5_root):
        rel_path = path.relative_to(mq5_root).as_posix()
        all_sources[rel_path] = read_text(path)
    return required, all_sources


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate MQ5 no-trade observability scaffold contract.",
    )
    parser.add_argument(
        "--mq5-root",
        default=str(DEFAULT_MQ5_ROOT),
        help="MQ5 source root to validate. Defaults to repository mq5/.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mq5_root = normalize_root(args.mq5_root)
    required_files, all_source_texts = load_repository_texts(mq5_root)
    failures = validate_texts(required_files, all_source_texts)

    if failures:
        print(FAIL_TEXT)
        print(SAFETY_NOTICE)
        print(f"scanned root: {mq5_root}")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(PASS_TEXT)
    print(SAFETY_NOTICE)
    print(f"scanned root: {mq5_root}")
    print("contract: no-trade observability scaffold is present and static-safe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
