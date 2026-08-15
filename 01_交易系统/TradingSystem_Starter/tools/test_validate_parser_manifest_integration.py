#!/usr/bin/env python3
"""Self-test parser manifest integration validator."""

from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT_DIR / "tools" / "validate_parser_manifest_integration.py"
PASS_TEXT = "Parser manifest integration validator self-test passed"
FAIL_TEXT = "Parser manifest integration validator self-test failed"


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

    if "Parser manifest integration validation passed" not in completed.stdout:
        print(FAIL_TEXT)
        print("missing expected pass text")
        print(completed.stdout)
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())