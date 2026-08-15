#!/usr/bin/env python3
"""Self-test backtest set params validator."""

from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT_DIR / "tools" / "validate_backtest_set_params.py"
PASS_TEXT = "Backtest set params validator self-test passed"
FAIL_TEXT = "Backtest set params validator self-test failed"


def main():
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        print(FAIL_TEXT)
        print((completed.stdout + completed.stderr).strip())
        return 1

    if "Backtest set params validation passed" not in completed.stdout:
        print(FAIL_TEXT)
        print(completed.stdout)
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())