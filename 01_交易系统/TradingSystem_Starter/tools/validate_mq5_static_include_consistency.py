#!/usr/bin/env python3
"""Validate MQ5 include and dependency consistency without running MT5."""

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

FORBIDDEN_INCLUDE_PARTS = {
    "backtest",
    "docs",
    "tools",
    "external evidence",
    "external_evidence",
}

REQUIRED_KEYWORDS = {
    "TradingSystem.mq5": (
        '#include "core/EaController.mqh"',
        "EaController controller",
        "int OnInit()",
        "void OnTick()",
        "void OnDeinit(const int reason)",
        "controller.OnInit()",
        "controller.OnTick()",
        "controller.OnDeinit(reason)",
    ),
    "core/EaController.mqh": (
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
        "int OnInit()",
        "void OnTick()",
        "void OnDeinit(const int reason)",
    ),
    "config/InputConfig.mqh": (
        "input bool InpEnableTrading = false",
        "input bool InpEnableNoTradeObservability",
        "input bool InpObservabilityLogOnTick = false",
    ),
    "execution/ExecutionManager.mqh": (
        "class ExecutionManager",
        '#include "../config/InputConfig.mqh"',
        '#include "../logger/Logger.mqh"',
        '#include "../signals/SignalEngine.mqh"',
        "bool Init(Logger &log)",
    ),
    "logger/Logger.mqh": (
        "class Logger",
        '#include "../config/InputConfig.mqh"',
        "bool Init()",
        "Inventory only; no MT5 run; no trading authorization.",
    ),
    "risk/RiskManager.mqh": (
        "class RiskManager",
        '#include "../config/InputConfig.mqh"',
        '#include "../logger/Logger.mqh"',
        '#include "../signals/SignalEngine.mqh"',
        "bool Init(Logger &log)",
    ),
    "signals/SignalEngine.mqh": (
        "class SignalEngine",
        '#include "../logger/Logger.mqh"',
        "bool Init(Logger &log)",
    ),
}

INCLUDE_PATTERN = re.compile(r'^\s*#include\s+(?:"(?P<quoted>[^"]+)"|<(?P<angled>[^>]+)>)')


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


def include_targets(text: str) -> list[str]:
    targets: list[str] = []
    for line in text.splitlines():
        match = INCLUDE_PATTERN.match(line)
        if match:
            targets.append(match.group("quoted") or match.group("angled") or "")
    return targets


def is_forbidden_include_target(include_path: str) -> bool:
    lowered = include_path.replace("\\", "/").lower()
    return any(part in lowered for part in FORBIDDEN_INCLUDE_PARTS)


def resolve_include(source_file: Path, include_path: str, mq5_root: Path) -> Path:
    raw_path = Path(include_path)
    if raw_path.is_absolute():
        return raw_path
    return (source_file.parent / raw_path).resolve()


def collect_include_issues(mq5_root: Path, source_files: list[Path]) -> list[str]:
    issues: list[str] = []
    resolved_root = mq5_root.resolve()

    for source_file in source_files:
        source_rel = rel_path(source_file, mq5_root)
        text = read_text(source_file)
        for include_path in include_targets(text):
            if Path(include_path).is_absolute():
                issues.append(f"{source_rel} uses absolute include: {include_path}")
                continue
            if is_forbidden_include_target(include_path):
                issues.append(f"{source_rel} includes forbidden path: {include_path}")
                continue

            resolved = resolve_include(source_file, include_path, mq5_root)
            try:
                resolved.relative_to(resolved_root)
            except ValueError:
                issues.append(f"{source_rel} include escapes mq5 root: {include_path}")
                continue

            if not resolved.exists() or not resolved.is_file():
                issues.append(f"{source_rel} include target missing: {include_path}")
                continue

            if resolved.suffix.lower() not in {".mq5", ".mqh"}:
                issues.append(f"{source_rel} include target is not MQ5/MQH: {include_path}")

    return issues


def collect_inventory_issues(mq5_root: Path, source_files: list[Path]) -> list[str]:
    actual_files = {rel_path(path, mq5_root) for path in source_files}
    missing_files = sorted(EXPECTED_FILES - actual_files)
    extra_files = sorted(actual_files - EXPECTED_FILES)
    issues: list[str] = []

    if missing_files:
        issues.append("MQ5 include consistency missing files: " + ", ".join(missing_files))
    if extra_files:
        issues.append("MQ5 include consistency unexpected files: " + ", ".join(extra_files))

    return issues


def collect_keyword_issues(mq5_root: Path, source_files: list[Path]) -> list[str]:
    actual_files = {rel_path(path, mq5_root): path for path in source_files}
    issues: list[str] = []

    for file_rel, keywords in REQUIRED_KEYWORDS.items():
        path = actual_files.get(file_rel)
        if path is None:
            continue
        text = read_text(path)
        for keyword in keywords:
            if keyword not in text:
                issues.append(f"{file_rel} missing required dependency keyword: {keyword}")
        for keyword in FORBIDDEN_TRADING_KEYWORDS:
            if keyword in text:
                issues.append(f"{file_rel} contains prohibited trading keyword: {keyword}")

    return issues


def collect_issues(mq5_root: Path = DEFAULT_MQ5_ROOT) -> list[str]:
    if not mq5_root.exists() or not mq5_root.is_dir():
        return [f"missing mq5 root: {mq5_root}"]

    source_files = mq5_source_files(mq5_root)
    issues: list[str] = []
    issues.extend(collect_inventory_issues(mq5_root, source_files))
    issues.extend(collect_include_issues(mq5_root, source_files))
    issues.extend(collect_keyword_issues(mq5_root, source_files))
    return issues


def main() -> int:
    issues = collect_issues()
    if issues:
        print("MQ5 static include consistency validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 static include consistency validation passed")
    print("Inventory only; no MT5 run; no trading authorization.")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
