#!/usr/bin/env python3
"""Aggregate read-only MQ5 static compile-readiness checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import os
import subprocess
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


@dataclass(frozen=True)
class AggregateCheck:
    check_id: str
    command: tuple[str, ...]
    success_field: str


def python_command(script_rel_path: str, *args: str, python_executable: str) -> tuple[str, ...]:
    return (
        python_executable,
        str(ROOT_DIR / script_rel_path),
        *args,
    )


def build_aggregate_checks(python_executable: str) -> tuple[AggregateCheck, ...]:
    return (
        AggregateCheck(
            "mq5-static-include-consistency",
            python_command("tools/validate_mq5_static_include_consistency.py", python_executable=python_executable),
            "static_include_consistency=true",
        ),
        AggregateCheck(
            "mq5-lifecycle-route-consistency",
            python_command("tools/validate_mq5_lifecycle_route_consistency.py", python_executable=python_executable),
            "lifecycle_route_consistency=true",
        ),
        AggregateCheck(
            "mq5-observability-helper-consistency",
            python_command("tools/validate_mq5_observability_helper_consistency.py", python_executable=python_executable),
            "observability_helper_consistency=true",
        ),
        AggregateCheck(
            "mq5-telemetry-aggregation",
            python_command("tools/validate_mq5_telemetry_aggregation.py", python_executable=python_executable),
            "telemetry_aggregation_consistency=true",
        ),
        AggregateCheck(
            "mq5-static-symbol-consistency",
            python_command("tools/validate_mq5_static_symbol_consistency.py", python_executable=python_executable),
            "static_symbol_consistency=true",
        ),
        AggregateCheck(
            "mq5-static-interface-consistency",
            python_command(
                "tools/validate_project_state_docs.py",
                "--mq5-static-interface-consistency",
                python_executable=python_executable,
            ),
            "static_interface_consistency=true",
        ),
        AggregateCheck(
            "mq5-no-trade-observability",
            python_command("tools/validate_mq5_no_trade_observability.py", python_executable=python_executable),
            "no_trade_observability_consistency=true",
        ),
    )


def source_files(mq5_root: Path) -> list[Path]:
    return sorted(
        path
        for path in mq5_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def rel_path(mq5_root: Path, path: Path) -> str:
    return path.relative_to(mq5_root).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def collect_trading_keyword_issues(mq5_root: Path) -> list[str]:
    issues: list[str] = []
    for path in source_files(mq5_root):
        text = read_text(path)
        for keyword in FORBIDDEN_TRADING_KEYWORDS:
            if keyword in text:
                issues.append(f"{rel_path(mq5_root, path)} contains trading keyword: {keyword}")
    return issues


def run_subprocess(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        list(command),
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        env=env,
    )


def collect_aggregate_issues(
    checks: tuple[AggregateCheck, ...],
    runner=run_subprocess,
) -> list[str]:
    issues: list[str] = []
    for check in checks:
        result = runner(check.command)
        if result.returncode != 0:
            output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
            detail = f": {output}" if output else ""
            issues.append(f"{check.check_id} failed{detail}")
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate read-only MQ5 static compile-readiness checks."
    )
    parser.add_argument(
        "--mq5-root",
        default=str(DEFAULT_MQ5_ROOT),
        help="MQ5 root directory to scan for static inventory and keywords.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, runner=run_subprocess) -> int:
    args = parse_args(argv)
    mq5_root = Path(args.mq5_root)
    issues = collect_inventory_issues(mq5_root)
    if not issues:
        issues.extend(collect_trading_keyword_issues(mq5_root))
    if not issues:
        issues.extend(collect_aggregate_issues(build_aggregate_checks(sys.executable), runner=runner))

    if issues:
        print("MQ5 static compile-readiness aggregate validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        print("mql5_compile_executed=false")
        print("mt5_run=false")
        print("trading_authorization=false")
        return 1

    print("MQ5 static compile-readiness aggregate validation passed")
    print("Inventory only; no MT5 run; no trading authorization.")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print("compile_readiness_static_only=true")
    print("mql5_compile_executed=false")
    print("mt5_run=false")
    print("trading_authorization=false")
    for check in build_aggregate_checks(sys.executable):
        print(check.success_field)
    return 0


if __name__ == "__main__":
    sys.exit(main())
