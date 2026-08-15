#!/usr/bin/env python3
"""Run the read-only engineering toolchain checks for this project."""

from pathlib import Path
import argparse
import json
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    ROOT_DIR / "tools" / "validate_backtest_runtime_report.py",
    ROOT_DIR / "tools" / "test_validate_backtest_runtime_report.py",
    ROOT_DIR / "tools" / "validate_runtime_parser_input_samples.py",
    ROOT_DIR / "tools" / "test_validate_runtime_parser_input_samples.py",
    ROOT_DIR / "tools" / "validate_project_state_docs.py",
    ROOT_DIR / "tools" / "test_validate_project_state_docs.py",
    ROOT_DIR / "tools" / "validate_mq5_safety_guardrails.py",
    ROOT_DIR / "tools" / "test_validate_mq5_safety_guardrails.py",
    ROOT_DIR / "tools" / "validate_backtest_set_safety.py",
    ROOT_DIR / "tools" / "test_validate_backtest_set_safety.py",
    ROOT_DIR / "tools" / "validate_python_tool_safety.py",
    ROOT_DIR / "tools" / "test_validate_python_tool_safety.py",
    ROOT_DIR / "tools" / "validate_evidence_manifest_schema.py",
    ROOT_DIR / "tools" / "test_validate_evidence_manifest_schema.py",
    ROOT_DIR / "tools" / "validate_official_manifest_path_policy.py",
    ROOT_DIR / "tools" / "test_validate_official_manifest_path_policy.py",
    ROOT_DIR / "tools" / "parse_strategy_tester_html_report.py",
    ROOT_DIR / "tools" / "test_parse_strategy_tester_html_report.py",
    ROOT_DIR / "tools" / "parse_mt5_log_no_trade_summary.py",
    ROOT_DIR / "tools" / "test_parse_mt5_log_no_trade_summary.py",
    ROOT_DIR / "tools" / "generate_evidence_manifest.py",
    ROOT_DIR / "tools" / "test_generate_evidence_manifest.py",
    ROOT_DIR / "tools" / "parse_mql5_compile_log.py",
    ROOT_DIR / "tools" / "test_parse_mql5_compile_log.py",
    ROOT_DIR / "tools" / "parse_backtest_set_params.py",
    ROOT_DIR / "tools" / "test_parse_backtest_set_params.py",
    ROOT_DIR / "tools" / "validate_backtest_set_params.py",
    ROOT_DIR / "tools" / "test_validate_backtest_set_params.py",
    ROOT_DIR / "tools" / "test_parse_backtest_runtime_summary.py",
    ROOT_DIR / "tools" / "run_evidence_parser_pipeline.py",
    ROOT_DIR / "tools" / "validate_parser_manifest_integration.py",
    ROOT_DIR / "tools" / "test_validate_parser_manifest_integration.py",
    ROOT_DIR / "backtest" / "reports" / "generated" / "TASK-012_generated_runtime_summary_sample.md",
    ROOT_DIR / "backtest" / "reports" / "generated" / "TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md",
    ROOT_DIR / "docs" / "CURRENT_TASK.md",
    ROOT_DIR / "docs" / "HANDOFF_PROMPT.md",
    ROOT_DIR / "docs" / "PROJECT_STATE.md",
]

CHECKS = [
    {
        "name": "validate generated sample report",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_backtest_runtime_report.py"),
            "--report",
            str(
                ROOT_DIR
                / "backtest"
                / "reports"
                / "generated"
                / "TASK-012_generated_runtime_summary_sample.md"
            ),
        ],
        "expected": "Validation passed",
    },
    {
        "name": "validate generated TASK-010 report",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_backtest_runtime_report.py"),
            "--report",
            str(
                ROOT_DIR
                / "backtest"
                / "reports"
                / "generated"
                / "TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md"
            ),
        ],
        "expected": "Validation passed",
    },
    {
        "name": "validate backtest runtime report validator self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_backtest_runtime_report.py"),
        ],
        "expected": "Self-test passed",
    },
    {
        "name": "validate runtime parser input samples",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_runtime_parser_input_samples.py"),
        ],
        "expected": "Runtime parser input samples validation passed",
    },
    {
        "name": "validate runtime parser input samples self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_runtime_parser_input_samples.py"),
        ],
        "expected": "Runtime parser input samples self-test passed",
    },
    {
        "name": "validate project state docs",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_project_state_docs.py"),
        ],
        "expected": "Project state docs validation passed",
    },
    {
        "name": "validate project state docs self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_project_state_docs.py"),
        ],
        "expected": "Project state docs self-test passed",
    },
    {
        "name": "validate MQ5 safety guardrails",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_mq5_safety_guardrails.py"),
        ],
        "expected": "MQ5 safety guardrails validation passed",
    },
    {
        "name": "validate MQ5 safety guardrails self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_mq5_safety_guardrails.py"),
        ],
        "expected": "MQ5 safety guardrails self-test passed",
    },
    {
        "name": "validate backtest set safety",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_backtest_set_safety.py"),
        ],
        "expected": "Backtest set safety validation passed",
    },
    {
        "name": "validate backtest set safety self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_backtest_set_safety.py"),
        ],
        "expected": "Backtest set safety self-test passed",
    },
    {
        "name": "validate Python tool safety",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_python_tool_safety.py"),
        ],
        "expected": "Python tool safety validation passed",
    },
    {
        "name": "validate Python tool safety self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_python_tool_safety.py"),
        ],
        "expected": "Python tool safety self-test passed",
    },
    {
        "name": "validate evidence manifest schema self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_evidence_manifest_schema.py"),
        ],
        "expected": "Evidence manifest schema self-test passed",
    },
    {
        "name": "validate Strategy Tester HTML parser self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_parse_strategy_tester_html_report.py"),
        ],
        "expected": "Strategy Tester HTML parser self-test passed",
    },
    {
        "name": "validate MT5 log no-trade parser self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_parse_mt5_log_no_trade_summary.py"),
        ],
        "expected": "MT5 log no-trade parser self-test passed",
    },
    {
        "name": "validate evidence manifest generator self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_generate_evidence_manifest.py"),
        ],
        "expected": "Evidence manifest generator self-test passed",
    },
    {
        "name": "validate MQL5 compile log parser self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_parse_mql5_compile_log.py"),
        ],
        "expected": "MQL5 compile log parser self-test passed",
    },
    {
        "name": "validate backtest set params parser self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_parse_backtest_set_params.py"),
        ],
        "expected": "Backtest set params parser self-test passed",
    },
    {
        "name": "validate backtest runtime summary parser self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_parse_backtest_runtime_summary.py"),
        ],
        "expected": "Backtest runtime summary parser self-test passed",
    },
    {
        "name": "validate parser manifest integration",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_parser_manifest_integration.py"),
        ],
        "expected": "Parser manifest integration validation passed",
    },
    {
        "name": "validate official manifest path policy",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "validate_official_manifest_path_policy.py"),
            "--manifest-path",
            "backtest/reports/manifests/TASK-099_example_manifest.json",
        ],
        "expected": "Official manifest path policy validation passed",
    },
    {
        "name": "validate official manifest path policy self-test",
        "command": [
            sys.executable,
            str(ROOT_DIR / "tools" / "test_validate_official_manifest_path_policy.py"),
        ],
        "expected": "Official manifest path policy self-test passed",
    },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the read-only engineering toolchain checks."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the engineering toolchain checks without running them.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the --list output as JSON.",
    )
    return parser.parse_args()


def combined_output(result):
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def summarize_output(text, limit=400):
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def check_required_paths():
    missing = []
    for path in REQUIRED_PATHS:
        if not path.exists():
            missing.append(path.relative_to(ROOT_DIR).as_posix())
    return missing


def run_check(check):
    result = subprocess.run(
        check["command"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    output = combined_output(result)
    passed = result.returncode == 0 and check["expected"] in output
    return {
        "name": check["name"],
        "passed": passed,
        "returncode": result.returncode,
        "output": output,
    }


def print_check_list():
    print("Engineering toolchain checks list")
    for index, check in enumerate(CHECKS, start=1):
        print(f"{index}. {check['name']}")


def build_check_list_payload():
    return {
        "name": "engineering_toolchain_checks",
        "mode": "list",
        "checks": [
            {"index": index, "name": check["name"]}
            for index, check in enumerate(CHECKS, start=1)
        ],
    }


def print_check_list_json():
    print(json.dumps(build_check_list_payload(), indent=2))


def main():
    args = parse_args()
    if args.list:
        if args.json:
            print_check_list_json()
        else:
            print_check_list()
        return 0

    missing = check_required_paths()
    if missing:
        print("Engineering toolchain checks failed")
        print("Missing required files:")
        for item in missing:
            print(f"- {item}")
        return 1

    failures = []
    for check in CHECKS:
        result = run_check(check)
        if result["passed"]:
            print(f"[PASS] {result['name']}")
        else:
            failures.append(result)

    if failures:
        print("Engineering toolchain checks failed")
        for failure in failures:
            print(f"- {failure['name']}")
            print(f"  exit code: {failure['returncode']}")
            print(f"  output: {summarize_output(failure['output'])}")
        return 1

    print("Engineering toolchain checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
