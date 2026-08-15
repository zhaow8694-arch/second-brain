#!/usr/bin/env python3
"""Self-test backtest .set parameter parser."""

from pathlib import Path
import importlib
import json
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "tools"))
PARSER = importlib.import_module("parse_backtest_set_params")
CLI = ROOT_DIR / "tools" / "parse_backtest_set_params.py"
PASS_TEXT = "Backtest set params parser self-test passed"
FAIL_TEXT = "Backtest set params parser self-test failed"


def test_default_trading_off():
    sample = ROOT_DIR / "backtest" / "sets" / "TASK-009_A_default_trading_off.set"
    payload = PARSER.parse_set_file(sample)
    assert not payload["issues"]
    assert payload["noTradeAssertions"]["passed"] is True
    assert payload["parameters"]["InpEnableTrading"] is False


def test_observation_exception():
    sample = ROOT_DIR / "backtest" / "sets" / "TASK-009_B_trading_true_observation_block.set"
    payload = PARSER.parse_set_file(sample)
    assert not payload["issues"]
    assert payload["noTradeAssertions"]["observationModeException"] is True


def test_cli_round_trip():
    sample = ROOT_DIR / "backtest" / "sets" / "TASK-009_A_default_trading_off.set"
    completed = subprocess.run(
        [sys.executable, str(CLI), str(sample)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["parameterCount"] > 0


def main():
    tests = (
        test_default_trading_off,
        test_observation_exception,
        test_cli_round_trip,
    )
    for test in tests:
        try:
            test()
        except AssertionError as error:
            print(FAIL_TEXT)
            print(f"- {test.__name__}: {error}")
            return 1
        except Exception as error:
            print(FAIL_TEXT)
            print(f"- {test.__name__} raised {type(error).__name__}: {error}")
            return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())