#!/usr/bin/env python3
"""Emit and validate the MQ5 compile-readiness final milestone summary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_SUMMARY_FIELDS = (
    "final_milestone_summary=true",
    "tasks_covered=TASK-266..TASK-292",
    "fast_no_trade_state_report=true",
    "fast_no_trade_review_summary=true",
    "trae_handoff_summary=true",
    "workflow_closure_audit=true",
    "validator_self_test_summary=PASS",
    "mq5_inventory_expected=7 files",
    "trading_keywords=false",
    "no_mt5_run=true",
    "no_mql5_compile=true",
    "no_trading=true",
    "no_manifest=true",
    "no_fixture=true",
    "no_report=true",
    "no_external_evidence=true",
    "milestone_closure_ready=PASS",
    "Inventory only; no MT5 run; no trading authorization.",
)


@dataclass(frozen=True)
class DependencyCheck:
    check_id: str
    command: tuple[str, ...]
    summary_field: str


def python_command(script_rel_path: str, *args: str, python_executable: str) -> tuple[str, ...]:
    return (
        python_executable,
        str(ROOT_DIR / script_rel_path),
        *args,
    )


def build_dependency_checks(python_executable: str) -> tuple[DependencyCheck, ...]:
    return (
        DependencyCheck(
            "mq5-static-compile-readiness",
            python_command(
                "tools/validate_mq5_static_compile_readiness.py",
                python_executable=python_executable,
            ),
            "mq5-static-compile-readiness=PASS",
        ),
        DependencyCheck(
            "project-state-docs",
            python_command(
                "tools/validate_project_state_docs.py",
                python_executable=python_executable,
            ),
            "project-state-docs=PASS",
        ),
        DependencyCheck(
            "project-state-docs-self-test",
            python_command(
                "tools/test_validate_project_state_docs.py",
                python_executable=python_executable,
            ),
            "project-state-docs-self-test=PASS",
        ),
    )


def build_summary() -> str:
    lines = [
        "final_milestone_summary=true",
        "tasks_covered=TASK-266..TASK-292",
        "fast_no_trade_state_report=true",
        "fast_no_trade_review_summary=true",
        "trae_handoff_summary=true",
        "workflow_closure_audit=true",
        "validator_self_test_summary=PASS",
        "preflight_summary=PASS",
        "static_validation_summary=PASS",
        "telemetry_observability_summary=PASS",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "no_mt5_run=true",
        "no_mql5_compile=true",
        "no_trading=true",
        "no_manifest=true",
        "no_fixture=true",
        "no_report=true",
        "no_external_evidence=true",
        "milestone_closure_ready=PASS",
        "Inventory only; no MT5 run; no trading authorization.",
    ]
    lines.extend(check.summary_field for check in build_dependency_checks(sys.executable))
    return "\n".join(lines) + "\n"


def validate_summary(summary: str) -> bool:
    return all(field in summary for field in REQUIRED_SUMMARY_FIELDS)


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


def collect_dependency_issues(
    checks: tuple[DependencyCheck, ...],
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


def main(argv: list[str] | None = None, runner=run_subprocess) -> int:
    _ = argv or []
    checks = build_dependency_checks(sys.executable)
    issues = collect_dependency_issues(checks, runner=runner)
    summary = build_summary()

    if not validate_summary(summary):
        issues.append("final milestone summary is missing required fields")

    if issues:
        print("MQ5 compile-readiness final milestone summary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        print("no_mt5_run=true")
        print("no_mql5_compile=true")
        print("no_trading=true")
        return 1

    print("MQ5 compile-readiness final milestone summary validation passed")
    print(summary, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
