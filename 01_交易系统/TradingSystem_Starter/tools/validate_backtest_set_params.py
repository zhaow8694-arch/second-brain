#!/usr/bin/env python3
"""Validate repository backtest .set files through the set parameter parser."""

from __future__ import annotations

from pathlib import Path
import importlib
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SETS_DIR = ROOT_DIR / "backtest" / "sets"
EXPECTED_SET_COUNT = 6
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

sys.path.insert(0, str(ROOT_DIR / "tools"))
SET_PARSER = importlib.import_module("parse_backtest_set_params")


def collect_set_files() -> list[Path]:
    if not SETS_DIR.exists():
        return []
    return sorted(path for path in SETS_DIR.glob("*.set") if path.is_file())


def main():
    issues: list[str] = []
    set_files = collect_set_files()

    if len(set_files) != EXPECTED_SET_COUNT:
        issues.append(
            f"expected {EXPECTED_SET_COUNT} backtest set files, found {len(set_files)}"
        )

    for set_path in set_files:
        payload = SET_PARSER.parse_set_file(set_path)
        if payload["issues"]:
            for issue in payload["issues"]:
                issues.append(f"{set_path.name}: {issue}")
        assertions = payload.get("noTradeAssertions", {})
        if not assertions.get("passed"):
            issues.append(f"{set_path.name}: no-trade assertions failed")

    if issues:
        print("Backtest set params validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Backtest set params validation passed")
    print(f"backtest_set_count={len(set_files)}")
    print("inp_enable_trading_guard=true")
    print("observation_mode_exceptions_allowed=true")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())