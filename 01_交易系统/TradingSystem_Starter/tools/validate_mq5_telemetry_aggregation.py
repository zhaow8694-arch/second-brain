#!/usr/bin/env python3
"""Validate read-only MQ5 observability telemetry aggregation without running MT5."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MQ5_ROOT = ROOT_DIR / "mq5"

EXPECTED_FILES = {
    "TradingSystem.mq5",
    "config/InputConfig.mqh",
    "core/EaController.mqh",
    "execution/ExecutionManager.mqh",
    "logger/Logger.mqh",
    "risk/RiskManager.mqh",
    "signals/SignalEngine.mqh",
}

FORBIDDEN_TRADING_KEYWORDS = (
    "Buy",
    "Sell",
    "OrderSend",
    "PositionOpen",
    "CTrade",
)

REQUIRED_LOGGER_HELPERS = (
    "LogNoTradePerformanceMetrics",
    "LogReadOnlyMetricsAggregation",
    "LogReadOnlySystemHealth",
    "LogReadOnlyPipelineContextAggregationSnapshot",
    "LogReadOnlyObservabilityErrorSnapshot",
    "LogReadOnlyTelemetryAggregationSnapshot",
    "LogReadOnlyControllerSummarySnapshot",
)

REQUIRED_CONTROLLER_CALLS = (
    "WriteNoTradePerformanceMetrics(eventName);",
    "WriteReadOnlyMetricsAggregation(eventName);",
    "WriteReadOnlySystemHealth(eventName);",
    "WriteReadOnlyPipelineContextAggregationSnapshot(eventName);",
    "WriteReadOnlyObservabilityErrorSnapshot(eventName);",
    "WriteReadOnlyTelemetryAggregationSnapshot(eventName);",
    "WriteReadOnlyControllerSummarySnapshot(eventName);",
)

REQUIRED_LOGGER_FIELDS = (
    "runtime_metrics_snapshot=true",
    "metrics_aggregation_snapshot=true",
    "system_health_snapshot=true",
    "pipeline_context_snapshot=true",
    "error_snapshot=true",
    "telemetry_aggregation_snapshot=true",
    "controller_summary_snapshot=true",
    "performance_metrics_linked=true",
    "aggregated_errors_linked=true",
    "aggregated_metrics_linked=true",
    "all_observability_outputs_read_only=true",
    "no_trade_guard=active",
    "mt5_run_required=false",
    "trading_authorization=false",
    "evidence_generation=false",
    "manifest_generation=false",
)

PASS_NOTICE = "Inventory only; no MT5 run; no trading authorization."


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rel_path(path: Path, mq5_root: Path) -> str:
    return path.relative_to(mq5_root).as_posix()


def mq5_source_files(mq5_root: Path) -> list[Path]:
    if not mq5_root.exists():
        return []
    return sorted(
        path
        for path in mq5_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def collect_inventory_issues(mq5_root: Path, source_files: list[Path]) -> list[str]:
    actual_files = {rel_path(path, mq5_root) for path in source_files}
    missing_files = sorted(EXPECTED_FILES - actual_files)
    extra_files = sorted(actual_files - EXPECTED_FILES)
    issues: list[str] = []

    if missing_files:
        issues.append("MQ5 telemetry aggregation missing files: " + ", ".join(missing_files))
    if extra_files:
        issues.append("MQ5 telemetry aggregation unexpected files: " + ", ".join(extra_files))
    return issues


def logger_helper_definitions(logger_text: str) -> set[str]:
    return set(
        re.findall(
            r"\b(?:void|bool|int|double|string|long|datetime)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            logger_text,
        )
    )


def collect_telemetry_issues(actual_files: dict[str, Path]) -> list[str]:
    issues: list[str] = []
    logger_path = actual_files.get("logger/Logger.mqh")
    controller_path = actual_files.get("core/EaController.mqh")
    if logger_path is None or controller_path is None:
        return issues

    logger_text = read_text(logger_path)
    controller_text = read_text(controller_path)
    helpers = logger_helper_definitions(logger_text)

    for helper_name in REQUIRED_LOGGER_HELPERS:
        if helper_name not in helpers:
            issues.append(f"Logger.mqh missing telemetry helper: {helper_name}")

    for field in REQUIRED_LOGGER_FIELDS:
        if field not in logger_text:
            issues.append(f"Logger.mqh missing telemetry aggregation field: {field}")

    for call in REQUIRED_CONTROLLER_CALLS:
        count = controller_text.count(call)
        if count == 0:
            issues.append(f"EaController.mqh missing telemetry helper call: {call}")
        elif count > 1:
            issues.append(f"EaController.mqh duplicate telemetry helper call: {call}")

    if PASS_NOTICE not in logger_text:
        issues.append(f"Logger.mqh missing safety notice: {PASS_NOTICE}")

    return issues


def collect_trading_keyword_issues(mq5_root: Path, source_files: list[Path]) -> list[str]:
    issues: list[str] = []
    for source_file in source_files:
        source_rel = rel_path(source_file, mq5_root)
        text = read_text(source_file)
        for keyword in FORBIDDEN_TRADING_KEYWORDS:
            if keyword in text:
                issues.append(f"{source_rel} contains prohibited trading keyword: {keyword}")
    return issues


def collect_issues(mq5_root: Path = DEFAULT_MQ5_ROOT) -> list[str]:
    if not mq5_root.exists() or not mq5_root.is_dir():
        return [f"missing mq5 root: {mq5_root}"]

    source_files = mq5_source_files(mq5_root)
    actual_files = {rel_path(path, mq5_root): path for path in source_files}
    issues: list[str] = []
    issues.extend(collect_inventory_issues(mq5_root, source_files))
    issues.extend(collect_telemetry_issues(actual_files))
    issues.extend(collect_trading_keyword_issues(mq5_root, source_files))
    return issues


def print_summary() -> None:
    print("fast_no_trade_telemetry_aggregation=true")
    print("stdout_only=true")
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("controller_summary_linked=true")
    print("pipeline_context_linked=true")
    print("error_snapshot_linked=true")
    print("metrics_and_system_health_linked=true")
    print("all_observability_outputs_read_only=true")
    print("no_trade_guard=active")
    print("mt5_run_required=false")
    print("trading_authorization=false")
    print("manifest_generation=false")
    print("evidence_generation=false")
    print(PASS_NOTICE)


def main() -> int:
    issues = collect_issues()
    if issues:
        print("MQ5 telemetry aggregation validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 telemetry aggregation validation passed")
    print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
