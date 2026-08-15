#!/usr/bin/env python3
"""Generate the TASK-069 runtime parser input samples audit report."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys


CURRENT_LATEST_COMMIT = "d208052 TASK-DOC-071 update state after TASK-070"
CURRENT_FUNCTIONAL_TASK = (
    "d0de1cb TASK-070 extend runtime parser input sample negative coverage"
)
CURRENT_STABLE_TAG = "v0.1.9-runtime-report-quality"
PREVIOUS_STABLE_TAG_REFERENCE = "v0.1.8-engineering-toolchain-stable"
HISTORICAL_STABLE_TAG_REFERENCE = "v0.1.7-core-signal-log-throttle"
REPORT_RELATIVE_PATH = (
    "backtest/reports/generated/TASK-069_runtime_parser_input_samples_audit.md"
)

INPUT_SAMPLES = [
    "backtest/reports/samples/TASK-012_runtime_summary_sample.log",
    "backtest/reports/TASK-010_v0.1.7_core_signal_log_throttle.md",
]

GENERATED_REPORTS = [
    "backtest/reports/generated/TASK-012_generated_runtime_summary_sample.md",
    "backtest/reports/generated/TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md",
]

COVERAGE_VALIDATORS = [
    "tools/validate_runtime_parser_input_samples.py",
    "tools/test_validate_runtime_parser_input_samples.py",
    "tools/run_engineering_toolchain_checks.py",
]

COMPLETED_SCOPE = [
    "Sample log input exists.",
    "TASK-010 markdown input exists.",
    "Sample generated runtime summary report exists.",
    "TASK-010 generated runtime summary report exists.",
    "Generated reports preserve Source File mapping.",
    "Sample report covers complete runtime fields.",
    "TASK-010 report covers missing-field behavior.",
    "Missing fields remain Not found and are not inferred.",
    "Safety Notes are preserved.",
    "Prohibited live trading / profit / recommendation claims are rejected.",
    "Runtime parser input samples validator is included in engineering toolchain checks.",
    "Runtime parser input samples self-test is included in engineering toolchain checks.",
    "Engineering toolchain default/list/json modes include runtime parser input sample checks.",
    "Malformed Source File mapping is covered by self-test.",
    "Complete sample coverage corruption is covered by self-test.",
    "TASK-010 missing-field corruption is covered by self-test.",
    "Safety Notes removal is covered by self-test.",
    "Prohibited live trading / profit / recommendation claims are covered by self-test.",
]

MALFORMED_INPUT_NEGATIVE_COVERAGE = [
    "Malformed Source File mapping",
    "Broken complete sample coverage",
    "Broken TASK-010 missing-field behavior",
    "Missing Safety Notes",
    "Missing real trading prohibition statement",
    "Missing Not found inference statement",
    "Missing RiskManager safety statement",
    "Missing ExecutionManager safety statement",
    "Prohibited live trading claims",
    "Prohibited profit claims",
    "Prohibited trading recommendation claims",
    "Prohibited RiskManager bypass claims",
]

SELF_TEST_COVERAGE_NOTES = [
    "Negative coverage is implemented in tools/test_validate_runtime_parser_input_samples.py.",
    "Negative samples are created in tempfile directories only.",
    "Real project files are not modified by self-tests.",
    "Generated runtime summary reports are not modified by self-tests.",
    "Missing fields must remain Not found and must not be inferred.",
    "Prohibited live trading / profit / recommendation claims must fail validation.",
]

ENGINEERING_TOOLCHAIN_COVERAGE = [
    "validate runtime parser input samples",
    "validate runtime parser input samples self-test",
    "Engineering toolchain checks are expected to include 13 checks after TASK-068.",
    "List mode and JSON list mode are expected to include 13 checks.",
]

EXPECTED_COMMANDS = [
    "py tools/validate_runtime_parser_input_samples.py",
    "py tools/test_validate_runtime_parser_input_samples.py",
    "py tools/run_engineering_toolchain_checks.py --list --json",
    "py tools/run_engineering_toolchain_checks.py --list",
    "py tools/run_engineering_toolchain_checks.py",
    "py tools/test_run_engineering_toolchain_checks.py",
    "py tools/validate_python_tool_safety.py",
    "py tools/test_validate_python_tool_safety.py",
    "py tools/validate_project_state_docs.py",
    "py tools/test_validate_project_state_docs.py",
    "py tools/validate_mq5_safety_guardrails.py",
    "py tools/test_validate_mq5_safety_guardrails.py",
    "py tools/validate_backtest_set_safety.py",
    "py tools/test_validate_backtest_set_safety.py",
]

SAFETY_STATUS = [
    "Current system is still not allowed to perform real trading.",
    "SignalEngine must not place orders.",
    "RiskManager must not be bypassed.",
    "ExecutionManager must not execute real orders in the current stage.",
    "InpEnableTrading default remains false.",
    "CTrade / OrderSend / PositionOpen / Buy / Sell / OrderModify remain forbidden in current stage.",
    "Martingale, grid, and averaging-down remain forbidden.",
    "EMA signals remain observation-only and are not a production trading strategy.",
    "Runtime parser input sample validation must not infer missing fields.",
    "Runtime parser input sample validation must not claim live trading readiness.",
]

NOT_INCLUDED = [
    "No ATR implementation.",
    "No position sizing.",
    "No stop loss / take profit implementation.",
    "No AI trading logic.",
    "No multi-symbol trading.",
    "No multi-account trading.",
    "No live execution.",
    "No tag creation.",
    "No strategy optimization.",
    "No generated runtime summary report modification in this audit task.",
]


def bullet_lines(items):
    return [f"- {item}" for item in items]


def build_report():
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    coverage_snapshot = json.dumps(
        {
            "input_samples": INPUT_SAMPLES,
            "generated_reports": GENERATED_REPORTS,
            "coverage_validators": COVERAGE_VALIDATORS,
            "malformed_input_negative_coverage": MALFORMED_INPUT_NEGATIVE_COVERAGE,
        },
        ensure_ascii=True,
    )

    lines = [
        "# Runtime Parser Input Samples Audit",
        "",
        "## Report Metadata",
        "",
        "- Report Type: Runtime Parser Input Samples Audit",
        "- Generated By: tools/generate_runtime_parser_input_samples_audit.py",
        f"- Generated At UTC: {generated_at}",
        f"- Current Latest Commit: {CURRENT_LATEST_COMMIT}",
        f"- Current Latest Functional Task: {CURRENT_FUNCTIONAL_TASK}",
        f"- Current Stable Tag: {CURRENT_STABLE_TAG}",
        f"- Previous Stable Tag Reference: {PREVIOUS_STABLE_TAG_REFERENCE}",
        f"- Historical Stable Tag Reference: {HISTORICAL_STABLE_TAG_REFERENCE}",
        "- Tag Created In This Task: No",
        "",
        "## Scope",
        "",
        "- This audit summarizes the v0.2.0 runtime parser input sample coverage stage.",
        "- This audit does not enable real trading.",
        "- This audit does not modify MQ5.",
        "- This audit does not modify backtest/sets.",
        "- This audit does not modify existing generated runtime summary reports.",
        "- This audit does not create a tag.",
        "",
        "## Input Samples Under Coverage",
        "",
        *bullet_lines(INPUT_SAMPLES),
        "",
        "## Generated Reports Under Coverage",
        "",
        *bullet_lines(GENERATED_REPORTS),
        "",
        "## Coverage Validators",
        "",
        *bullet_lines(COVERAGE_VALIDATORS),
        "",
        "## Completed Runtime Parser Input Sample Scope",
        "",
        *bullet_lines(COMPLETED_SCOPE),
        "",
        "## Engineering Toolchain Coverage",
        "",
        *bullet_lines(ENGINEERING_TOOLCHAIN_COVERAGE),
        "",
        "## Malformed Input Negative Coverage",
        "",
        *bullet_lines(MALFORMED_INPUT_NEGATIVE_COVERAGE),
        "",
        "## Self-Test Coverage Notes",
        "",
        *bullet_lines(SELF_TEST_COVERAGE_NOTES),
        "",
        "Machine-readable coverage snapshot:",
        "",
        "```json",
        coverage_snapshot,
        "```",
        "",
        "## Expected Verification Commands",
        "",
        "```text",
        *EXPECTED_COMMANDS,
        "```",
        "",
        "## Safety Status",
        "",
        *bullet_lines(SAFETY_STATUS),
        "",
        "## Not Included",
        "",
        *bullet_lines(NOT_INCLUDED),
        "",
        "## Audit Conclusion",
        "",
        "- Runtime parser input sample coverage stage includes malformed input negative coverage.",
        "- Tag creation is not part of TASK-071.",
        "- A future tag decision must be made explicitly by ChatGPT after manual verification.",
        "",
    ]
    return "\n".join(lines)


def main():
    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / REPORT_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report(), encoding="utf-8")
    print("Runtime parser input samples audit generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
