#!/usr/bin/env python3
"""Self-test MQL5 compile log parser."""

from pathlib import Path
import importlib
import json
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "tools"))
PARSER = importlib.import_module("parse_mql5_compile_log")
CLI = ROOT_DIR / "tools" / "parse_mql5_compile_log.py"
PASS_TEXT = "MQL5 compile log parser self-test passed"
FAIL_TEXT = "MQL5 compile log parser self-test failed"


def run_cli(log_text: str, *, exit_code: int = 0, quarantine: bool = False) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "compile.log"
        log_path.write_text(log_text, encoding="utf-8")
        command = [sys.executable, str(CLI), str(log_path), "--exit-code", str(exit_code)]
        if quarantine:
            command.append("--quarantine-ex5-detected")
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr.strip() or completed.stdout.strip())
        return completed.returncode, json.loads(completed.stdout)


def test_success_classification():
    text = """
Compiling 'TradingSystem.mq5'
MetaEditor build 5836
Result: 0 errors, 1 warnings
warning: unused variable
"""
    payload = PARSER.parse_compile_log(text, encoding="utf-8", exit_code=0)
    assert payload["compile_success"] is True
    assert payload["compile_log_errors"] == 0
    assert payload["compile_result_classification"] == "compile_log_success_exit_success"


def test_error_classification():
    text = "Compiling 'TradingSystem.mq5'\nResult: 2 errors, 0 warnings\nerror: missing semicolon"
    payload = PARSER.parse_compile_log(text, encoding="utf-8", exit_code=1)
    assert payload["compile_success"] is False
    assert payload["compile_log_errors"] == 2
    assert payload["compile_result_classification"] == "compile_errors_present"


def test_cli_round_trip():
    _, payload = run_cli(
        "Compiling 'TradingSystem.mq5'\nResult: 0 errors, 0 warnings\n",
        quarantine=True,
    )
    assert payload["quarantineEx5Detected"] is True
    assert payload["compile_success"] is True


def main():
    tests = (
        test_success_classification,
        test_error_classification,
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