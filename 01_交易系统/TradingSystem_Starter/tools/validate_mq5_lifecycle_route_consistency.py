#!/usr/bin/env python3
"""Validate MQ5 lifecycle route consistency without running MT5."""

from __future__ import annotations

from pathlib import Path
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

TRADING_SYSTEM_ROUTE_KEYWORDS = {
    "OnInit": (
        "int OnInit()",
        "controller.OnInit()",
    ),
    "OnTick": (
        "void OnTick()",
        "controller.OnTick()",
    ),
    "OnDeinit": (
        "void OnDeinit",
        "controller.OnDeinit(reason)",
    ),
}

EA_CONTROLLER_LIFECYCLE_KEYWORDS = {
    "OnInit": (
        "int OnInit()",
        "logger.Init()",
        "InpObservabilityLogOnInit",
        'WriteNoTradeObservability("No-trade observability init"',
    ),
    "OnTick": (
        "void OnTick()",
        "InpObservabilityLogOnTick",
        'WriteNoTradeObservability("No-trade observability tick"',
    ),
    "OnDeinit": (
        "void OnDeinit",
        "No-trade observability deinit",
        "WriteReadOnly",
    ),
}

LOGGER_OBSERVABILITY_KEYWORDS = (
    "NoTradeObservability",
    "NoTradeObservabilityStatusSnapshot",
    "LogNoTradeLifecycleEvent",
    "LogReadOnlyControllerSummarySnapshot",
    "Inventory only; no MT5 run; no trading authorization.",
)

COMPONENT_REQUIRED_KEYWORDS = {
    "signals/SignalEngine.mqh": ("class SignalEngine",),
    "risk/RiskManager.mqh": ("class RiskManager",),
    "execution/ExecutionManager.mqh": ("class ExecutionManager",),
}


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
        issues.append("MQ5 lifecycle route consistency missing files: " + ", ".join(missing_files))
    if extra_files:
        issues.append("MQ5 lifecycle route consistency unexpected files: " + ", ".join(extra_files))

    return issues


def collect_keyword_issues(actual_files: dict[str, Path]) -> list[str]:
    issues: list[str] = []

    trading_system = actual_files.get("TradingSystem.mq5")
    if trading_system is not None:
        text = read_text(trading_system)
        for lifecycle_name, keywords in TRADING_SYSTEM_ROUTE_KEYWORDS.items():
            for keyword in keywords:
                if keyword not in text:
                    issues.append(f"TradingSystem.mq5 missing {lifecycle_name} route keyword: {keyword}")

    controller = actual_files.get("core/EaController.mqh")
    if controller is not None:
        text = read_text(controller)
        for lifecycle_name, keywords in EA_CONTROLLER_LIFECYCLE_KEYWORDS.items():
            if not any(handler in text for handler in (f"int {lifecycle_name}()", f"void {lifecycle_name}")):
                issues.append(f"EaController missing lifecycle handler: {lifecycle_name}")
            for keyword in keywords:
                if keyword not in text:
                    issues.append(f"EaController missing {lifecycle_name} lifecycle keyword: {keyword}")

        tick_section = text.split("void OnTick()", 1)[1] if "void OnTick()" in text else ""
        if "WriteNoTradeObservability" in tick_section and "InpObservabilityLogOnTick" not in tick_section:
            issues.append("EaController OnTick observability path missing InpObservabilityLogOnTick gate")

    input_config = actual_files.get("config/InputConfig.mqh")
    if input_config is not None:
        text = read_text(input_config)
        if "input bool InpEnableTrading = false" not in text:
            issues.append("InputConfig.mqh missing default trading disabled configuration")
        if "InpObservabilityLogOnTick" not in text:
            issues.append("InputConfig.mqh missing InpObservabilityLogOnTick configuration")

    logger = actual_files.get("logger/Logger.mqh")
    if logger is not None:
        text = read_text(logger)
        for keyword in LOGGER_OBSERVABILITY_KEYWORDS:
            if keyword not in text:
                issues.append(f"Logger.mqh missing read-only observability helper trace: {keyword}")

    for rel_name, keywords in COMPONENT_REQUIRED_KEYWORDS.items():
        path = actual_files.get(rel_name)
        if path is None:
            continue
        text = read_text(path)
        for keyword in keywords:
            if keyword not in text:
                issues.append(f"{rel_name} missing required lifecycle dependency keyword: {keyword}")

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
    issues.extend(collect_keyword_issues(actual_files))
    issues.extend(collect_trading_keyword_issues(mq5_root, source_files))
    return issues


def main() -> int:
    issues = collect_issues()
    if issues:
        print("MQ5 lifecycle route consistency validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 lifecycle route consistency validation passed")
    print("Inventory only; no MT5 run; no trading authorization.")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print("lifecycle_routes=OnInit,OnTick,OnDeinit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
