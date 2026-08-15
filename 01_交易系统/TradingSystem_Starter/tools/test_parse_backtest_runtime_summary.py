#!/usr/bin/env python3
"""Self-test runtime summary parser JSON output."""

from pathlib import Path
import importlib
import json
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "tools"))
PARSER = importlib.import_module("parse_backtest_runtime_summary")
CLI = ROOT_DIR / "tools" / "parse_backtest_runtime_summary.py"
SAMPLE = ROOT_DIR / "backtest" / "reports" / "samples" / "TASK-012_runtime_summary_sample.log"
PASS_TEXT = "Backtest runtime summary parser self-test passed"
FAIL_TEXT = "Backtest runtime summary parser self-test failed"


def test_json_payload():
    text = SAMPLE.read_text(encoding="utf-8")
    parsed = PARSER.parse_runtime_summary(text)
    payload = PARSER.build_json_payload(str(SAMPLE), parsed)
    assert payload["fields"]["riskApproved"] != PARSER.NOT_FOUND
    assert payload["fields"]["executionAttempts"] != PARSER.NOT_FOUND
    assert payload["fieldCoverage"]["foundFields"] > 0


def test_cli_json_round_trip():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "summary.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--input",
                str(SAMPLE),
                "--output",
                str(output_path),
                "--format",
                "json",
                "--pretty",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert payload["reportType"] == "runtime_summary_metadata"


def main():
    tests = (
        test_json_payload,
        test_cli_json_round_trip,
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