#!/usr/bin/env python3
"""Validate MQ5 observability helper call consistency without running MT5."""

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

REQUIRED_LOGGER_HELPERS = (
    "LogReadOnlyObservabilityConsolidationSnapshot",
    "LogReadOnlyObservabilityContractRegistrySnapshot",
    "LogReadOnlyObservabilityErrorSnapshot",
    "LogReadOnlyTelemetryAggregationSnapshot",
    "LogReadOnlyControllerSummarySnapshot",
    "LogReadOnlyObservabilityOutputReductionSnapshot",
)

FORBIDDEN_TRADING_KEYWORDS = (
    "Buy",
    "Sell",
    "OrderSend",
    "PositionOpen",
    "CTrade",
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
        issues.append("MQ5 observability helper consistency missing files: " + ", ".join(missing_files))
    if extra_files:
        issues.append("MQ5 observability helper consistency unexpected files: " + ", ".join(extra_files))
    return issues


def logger_helper_definitions(logger_text: str) -> set[str]:
    return set(
        re.findall(
            r"\b(?:void|bool|int|double|string|long|datetime)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            logger_text,
        )
    )


def controller_logger_calls(controller_text: str) -> set[str]:
    calls = set(re.findall(r"\blogger\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", controller_text))
    return {
        call
        for call in calls
        if call.startswith("LogReadOnly")
        or call.startswith("LogNoTrade")
        or "Observability" in call
    }


def controller_on_tick_section(controller_text: str) -> str:
    match = re.search(r"\bvoid\s+OnTick\s*\([^)]*\)\s*\{", controller_text)
    if not match:
        return ""
    start = match.end()
    next_lifecycle = re.search(r"\bvoid\s+OnDeinit\s*\(", controller_text[start:])
    if next_lifecycle is None:
        return controller_text[start:]
    return controller_text[start : start + next_lifecycle.start()]


def collect_helper_issues(actual_files: dict[str, Path]) -> list[str]:
    issues: list[str] = []
    logger_path = actual_files.get("logger/Logger.mqh")
    controller_path = actual_files.get("core/EaController.mqh")
    if logger_path is None or controller_path is None:
        return issues

    logger_text = read_text(logger_path)
    controller_text = read_text(controller_path)
    definitions = logger_helper_definitions(logger_text)
    calls = controller_logger_calls(controller_text)

    for helper_name in REQUIRED_LOGGER_HELPERS:
        if helper_name not in definitions:
            issues.append(f"Logger.mqh missing required read-only observability helper: {helper_name}")

    for helper_name in sorted(calls):
        if helper_name not in definitions:
            issues.append(f"EaController.mqh calls Logger helper missing in Logger.mqh: {helper_name}")

    tick_section = controller_on_tick_section(controller_text)
    if not tick_section:
        issues.append("EaController.mqh missing OnTick section for observability helper gate validation")
    elif any(marker in tick_section for marker in ("WriteNoTradeObservability", "LogReadOnly", "LogNoTrade", "Observability")):
        if "InpObservabilityLogOnTick" not in tick_section:
            issues.append("EaController.mqh OnTick observability helper output missing InpObservabilityLogOnTick gate")

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
    issues.extend(collect_helper_issues(actual_files))
    issues.extend(collect_trading_keyword_issues(mq5_root, source_files))
    return issues


def main() -> int:
    issues = collect_issues()
    if issues:
        print("MQ5 observability helper consistency validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 observability helper consistency validation passed")
    print(PASS_NOTICE)
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print("logger_helper_consistency=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
