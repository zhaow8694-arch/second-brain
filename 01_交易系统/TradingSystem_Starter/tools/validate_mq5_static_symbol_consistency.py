#!/usr/bin/env python3
"""Validate MQ5 static symbol/reference consistency without running MT5."""

from __future__ import annotations

from pathlib import Path
import argparse
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MQ5_ROOT = ROOT_DIR / "mq5"

EXPECTED_SOURCE_FILES = {
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
    "LogReadOnlyObservabilityConsolidationSnapshot",
    "LogReadOnlyObservabilityContractRegistrySnapshot",
    "LogReadOnlyObservabilityErrorSnapshot",
    "LogReadOnlyTelemetryAggregationSnapshot",
    "LogReadOnlyControllerSummarySnapshot",
    "LogReadOnlyObservabilityOutputReductionSnapshot",
)

TRADING_SYSTEM_REQUIRED_SYMBOLS = (
    "EaController controller",
    "controller.OnInit()",
    "controller.OnTick()",
    "controller.OnDeinit(reason)",
)

TRADING_SYSTEM_REQUIRED_PATTERNS = {
    "OnInit function": r"\bint\s+OnInit\s*\(\s*\)",
    "OnTick function": r"\bvoid\s+OnTick\s*\(\s*\)",
    "OnDeinit function": r"\bvoid\s+OnDeinit\s*\(\s*const\s+int\s+reason\s*\)",
}

EA_CONTROLLER_REQUIRED_SYMBOLS = (
    "int OnInit()",
    "void OnTick()",
    "void OnDeinit(const int reason)",
    "Logger logger",
    "SignalEngine signalEngine",
    "RiskManager riskManager",
    "ExecutionManager executionManager",
    '#include "../config/InputConfig.mqh"',
    '#include "../logger/Logger.mqh"',
    '#include "../signals/SignalEngine.mqh"',
    '#include "../risk/RiskManager.mqh"',
    '#include "../execution/ExecutionManager.mqh"',
)

MODULE_SYMBOLS = {
    "signals/SignalEngine.mqh": (
        "class SignalEngine",
        "GetSignalStatusSnapshot",
    ),
    "risk/RiskManager.mqh": (
        "class RiskManager",
        "GetRiskStatusSnapshot",
    ),
    "execution/ExecutionManager.mqh": (
        "class ExecutionManager",
        "GetExecutionStatusSnapshot",
    ),
    "config/InputConfig.mqh": (
        "InpEnableTrading",
    ),
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_files(mq5_root: Path) -> list[Path]:
    return sorted(
        path
        for path in mq5_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def rel_path(mq5_root: Path, path: Path) -> str:
    return path.relative_to(mq5_root).as_posix()


def find_function_body(text: str, function_signature_pattern: str) -> str:
    match = re.search(function_signature_pattern, text)
    if not match:
        return ""

    open_brace = text.find("{", match.end())
    if open_brace == -1:
        return ""

    depth = 0
    for index in range(open_brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace:index + 1]
    return ""


def logger_methods(logger_text: str) -> set[str]:
    pattern = re.compile(
        r"\b(?:void|bool|string|int|long|double|datetime)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
    )
    return set(pattern.findall(logger_text))


def logger_calls(controller_text: str) -> set[str]:
    return set(re.findall(r"\blogger\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", controller_text))


def collect_inventory_issues(mq5_root: Path) -> list[str]:
    if not mq5_root.exists():
        return [f"missing MQ5 root: {mq5_root}"]
    if not mq5_root.is_dir():
        return [f"MQ5 root is not a directory: {mq5_root}"]

    actual = {rel_path(mq5_root, path) for path in source_files(mq5_root)}
    issues: list[str] = []
    missing = sorted(EXPECTED_SOURCE_FILES - actual)
    extra = sorted(actual - EXPECTED_SOURCE_FILES)

    if len(actual) != 7:
        issues.append(f"expected 7 MQ5/MQH source files, found {len(actual)}")
    if missing:
        issues.append("missing required MQ5/MQH file(s): " + ", ".join(missing))
    if extra:
        issues.append("unexpected MQ5/MQH file(s): " + ", ".join(extra))
    return issues


def collect_keyword_issues(mq5_root: Path) -> list[str]:
    issues: list[str] = []
    for path in source_files(mq5_root):
        text = read_text(path)
        for keyword in FORBIDDEN_TRADING_KEYWORDS:
            if keyword in text:
                issues.append(f"{rel_path(mq5_root, path)} contains trading keyword: {keyword}")
    return issues


def collect_symbol_issues(mq5_root: Path) -> list[str]:
    issues: list[str] = []

    trading_system = read_text(mq5_root / "TradingSystem.mq5")
    controller = read_text(mq5_root / "core" / "EaController.mqh")
    logger = read_text(mq5_root / "logger" / "Logger.mqh")
    input_config = read_text(mq5_root / "config" / "InputConfig.mqh")

    for symbol in TRADING_SYSTEM_REQUIRED_SYMBOLS:
        if symbol not in trading_system:
            issues.append(f"TradingSystem.mq5 missing symbol/reference: {symbol}")

    for label, pattern in TRADING_SYSTEM_REQUIRED_PATTERNS.items():
        if not re.search(pattern, trading_system):
            issues.append(f"TradingSystem.mq5 missing lifecycle symbol: {label}")

    for symbol in EA_CONTROLLER_REQUIRED_SYMBOLS:
        if symbol not in controller:
            issues.append(f"core/EaController.mqh missing symbol/reference: {symbol}")

    for rel_file, symbols in MODULE_SYMBOLS.items():
        text = read_text(mq5_root / rel_file)
        for symbol in symbols:
            if symbol not in text:
                issues.append(f"{rel_file} missing symbol/reference: {symbol}")

    if "InpEnableTrading" not in input_config and "trading disabled" not in input_config.lower():
        issues.append("config/InputConfig.mqh missing InpEnableTrading or trading disabled input trace")

    tick_body = find_function_body(controller, r"\bvoid\s+OnTick\s*\([^)]*\)")
    if not tick_body:
        issues.append("core/EaController.mqh missing OnTick body")
    elif "InpObservabilityLogOnTick" not in tick_body:
        issues.append("core/EaController.mqh OnTick observability path is not gated by InpObservabilityLogOnTick")

    methods = logger_methods(logger)
    for helper in REQUIRED_LOGGER_HELPERS:
        if helper not in methods:
            issues.append(f"logger/Logger.mqh missing required read-only helper: {helper}")

    unknown_calls = sorted(logger_calls(controller) - methods)
    if unknown_calls:
        issues.append("core/EaController.mqh calls unknown Logger helper(s): " + ", ".join(unknown_calls))

    if "signalEngine" in controller and not (mq5_root / "signals" / "SignalEngine.mqh").exists():
        issues.append("EaController references SignalEngine but signals/SignalEngine.mqh is missing")
    if "riskManager" in controller and not (mq5_root / "risk" / "RiskManager.mqh").exists():
        issues.append("EaController references RiskManager but risk/RiskManager.mqh is missing")
    if "executionManager" in controller and not (mq5_root / "execution" / "ExecutionManager.mqh").exists():
        issues.append("EaController references ExecutionManager but execution/ExecutionManager.mqh is missing")

    return issues


def collect_issues(mq5_root: Path) -> list[str]:
    issues = collect_inventory_issues(mq5_root)
    if issues:
        return issues
    issues.extend(collect_keyword_issues(mq5_root))
    issues.extend(collect_symbol_issues(mq5_root))
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate MQ5 static symbol/reference consistency without MT5."
    )
    parser.add_argument(
        "--mq5-root",
        default=str(DEFAULT_MQ5_ROOT),
        help="MQ5 root directory to scan.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mq5_root = Path(args.mq5_root)
    issues = collect_issues(mq5_root)
    if issues:
        print("MQ5 static symbol consistency validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 static symbol consistency validation passed")
    print("Inventory only; no MT5 run; no trading authorization.")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print("symbol_reference_consistency=true")
    print("compile_readiness_static_only=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
