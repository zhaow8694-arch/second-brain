#!/usr/bin/env python3
"""Validate parser-to-manifest integration readiness (read-only)."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK321_DOC = ROOT_DIR / "docs" / "V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md"
ARCHITECTURE_DOC = ROOT_DIR / "docs" / "Strategy_Pipeline_Architecture_v0.md"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

REQUIRED_TOOLS = (
    "tools/parse_strategy_tester_html_report.py",
    "tools/parse_mt5_log_no_trade_summary.py",
    "tools/parse_backtest_runtime_summary.py",
    "tools/parse_mql5_compile_log.py",
    "tools/parse_backtest_set_params.py",
    "tools/generate_evidence_manifest.py",
    "tools/validate_evidence_manifest_schema.py",
    "tools/validate_backtest_set_params.py",
    "tools/run_evidence_parser_pipeline.py",
)

REQUIRED_TESTS = (
    "tools/test_parse_strategy_tester_html_report.py",
    "tools/test_parse_mt5_log_no_trade_summary.py",
    "tools/test_parse_mql5_compile_log.py",
    "tools/test_parse_backtest_set_params.py",
    "tools/test_parse_backtest_runtime_summary.py",
    "tools/test_generate_evidence_manifest.py",
)

REQUIRED_TASK321_KEYWORDS = (
    "TASK-321 parser pipeline integration",
    "parser-pipeline-integration-only",
    "parser-manifest-integration",
    "not MT5 run in TASK-321",
    "not terminal64.exe execution in TASK-321",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MT5 terminal run executed in TASK-321",
    "no manifest generated in repository during TASK-321",
    "no external evidence copied into repository",
    "future TASK-320 requires GPT boundary before any MT5 terminal startup attempt",
    "TASK-320 must not be entered directly",
    "Inventory only; no MT5 run; no trading authorization.",
)


def collect_missing_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword not in text]


def main():
    issues: list[str] = []

    for rel_path in REQUIRED_TOOLS:
        if not (ROOT_DIR / rel_path).exists():
            issues.append(f"missing required tool: {rel_path}")

    for rel_path in REQUIRED_TESTS:
        if not (ROOT_DIR / rel_path).exists():
            issues.append(f"missing required test: {rel_path}")

    if not TASK321_DOC.exists():
        issues.append("missing docs/V060_TASK_321_PARSER_PIPELINE_INTEGRATION.md")
    else:
        text = TASK321_DOC.read_text(encoding="utf-8")
        missing = collect_missing_keywords(text, REQUIRED_TASK321_KEYWORDS)
        issues.extend(
            f"TASK-321 doc missing keyword: {keyword}" for keyword in missing
        )

    if not ARCHITECTURE_DOC.exists():
        issues.append("missing docs/Strategy_Pipeline_Architecture_v0.md")

    pipeline = subprocess.run(
        [sys.executable, str(ROOT_DIR / "tools" / "run_evidence_parser_pipeline.py"), "--mode", "full"],
        capture_output=True,
        text=True,
        check=False,
    )
    if pipeline.returncode != 0:
        detail = (pipeline.stdout + pipeline.stderr).strip().splitlines()
        summary = detail[-1] if detail else "no output"
        issues.append(f"run_evidence_parser_pipeline.py --mode full failed: {summary}")

    set_validator = subprocess.run(
        [sys.executable, str(ROOT_DIR / "tools" / "validate_backtest_set_params.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    if set_validator.returncode != 0:
        detail = (set_validator.stdout + set_validator.stderr).strip().splitlines()
        summary = detail[-1] if detail else "no output"
        issues.append(f"validate_backtest_set_params.py failed: {summary}")

    if issues:
        print("Parser manifest integration validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Parser manifest integration validation passed")
    print("parser_manifest_integration=true")
    print("parser_pipeline_full_mode=true")
    print("backtest_set_params=true")
    print("strategy_pipeline_architecture_doc=true")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())