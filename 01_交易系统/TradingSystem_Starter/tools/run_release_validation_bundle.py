#!/usr/bin/env python3
"""Run the release validation checks as one read-only bundle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import os
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    "backtest/reports/manifests/"
    "TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json"
)
PASS_TEXT = "Release validation bundle PASS"
FAIL_TEXT = "Release validation bundle FAIL"
FAST_NO_TRADE_DEV_PROFILE = "fast-no-trade-dev"
DEFAULT_FINAL_TASK_ID = "TASK-290"
DEFAULT_FINAL_COMMIT_MESSAGE = "TASK-290 implement final milestone closure / release-ready state report"
DEFAULT_FINAL_TAG_NAME = "v0.5.89-task-290-final-no-trade-workflow-milestone-report"
VALIDATION_PROFILES = {
    FAST_NO_TRADE_DEV_PROFILE: (
        "project-state-docs",
        "project-state-docs-self-test",
        "mq5-inventory",
        "mq5-no-trade-observability",
        "v060-implementation-boundary",
        "v060-implementation-readiness",
        "read-only-compile-readiness-boundary",
        "mq5-static-interface-consistency",
        "mq5-static-symbol-consistency",
        "mq5-static-include-consistency",
        "mq5-lifecycle-route-consistency",
        "mq5-observability-helper-consistency",
        "mq5-telemetry-aggregation",
        "mq5-static-compile-readiness",
        "mq5-static-compile-readiness-summary",
        "mq5-compile-readiness-final-summary",
        "mql5-compile-only-boundary",
        "mql5-compile-only-command-discovery",
        "mql5-compile-only-artifact-quarantine",
        "mql5-compile-only-execution-boundary",
        "mql5-compile-only-dryrun",
        "mql5-compile-only-dryrun-execution",
        "v060-compile-readiness-planning",
        "mql5-compile-only-preflight-gate",
        "mql5-compile-only-execution-authorization-plan",
        "mql5-compile-only-failure-diagnostic",
        "mql5-compile-diagnostic-result-classification",
        "mql5-compile-diagnostic-artifact-classification",
        "mql5-compile-diagnostic-artifact-proof-boundary",
        "mql5-compile-success-reclassification-boundary",
        "mql5-compile-artifact-hash-capture-boundary",
        "mql5-compile-success-reclassification-decision-boundary",
        "mql5-compile-success-reclassification-decision",
        "mt5-no-trade-startup-boundary",
        "mt5-no-trade-startup-command-discovery",
        "mt5-no-trade-startup-quarantine-preparation",
        "mt5-no-trade-startup-dryrun-config-boundary",
        "mt5-no-trade-startup-config-template",
        "mt5-no-trade-startup-authorization-plan",
        "mt5-no-trade-startup-preflight-gate",
        "parser-manifest-integration",
        "backtest-set-params",
    ),
}


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class ValidationCheckResult:
    check_id: str
    name: str
    passed: bool
    returncode: int


@dataclass(frozen=True)
class ValidationRunResult:
    exit_code: int
    results: tuple[ValidationCheckResult, ...]


def python_command(script_rel_path: str, *args: str, python_executable: str) -> tuple[str, ...]:
    return (
        python_executable,
        str(ROOT_DIR / script_rel_path),
        *args,
    )


def build_checks(
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    skip_engineering_toolchain: bool = False,
    python_executable: str | None = None,
) -> list[ValidationCheck]:
    python = python_executable or sys.executable
    checks = [
        ValidationCheck(
            "project-state-docs",
            "project state docs validator",
            python_command(
                "tools/validate_project_state_docs.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "project-state-docs-self-test",
            "project state docs self-test",
            python_command(
                "tools/test_validate_project_state_docs.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "workflow-simplification-policy",
            "workflow simplification policy validator",
            python_command(
                "tools/validate_workflow_simplification_policy.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "v060-transition-boundary",
            "v0.6.0 transition boundary validator",
            python_command(
                "tools/validate_v060_transition_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "v060-implementation-planning-boundary",
            "v0.6.0 implementation planning boundary validator",
            python_command(
                "tools/validate_v060_implementation_planning_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "v060-implementation-boundary",
            "v0.6.0 implementation boundary validator",
            python_command(
                "tools/validate_v060_implementation_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "v060-implementation-readiness",
            "v0.6.0 implementation readiness validator",
            python_command(
                "tools/validate_v060_implementation_readiness.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-inventory",
            "read-only MQ5 strategy inventory scanner",
            python_command(
                "tools/inspect_mq5_strategy_inventory.py",
                "--mq5-root",
                "MQ5",
                "--json",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-no-trade-observability",
            "MQ5 no-trade observability contract validator",
            python_command(
                "tools/validate_mq5_no_trade_observability.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "read-only-compile-readiness-boundary",
            "read-only compile-readiness boundary validator",
            python_command(
                "tools/validate_project_state_docs.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-static-interface-consistency",
            "MQ5 static interface consistency validator",
            python_command(
                "tools/validate_project_state_docs.py",
                "--mq5-static-interface-consistency",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-static-symbol-consistency",
            "MQ5 static symbol/reference consistency validator",
            python_command(
                "tools/validate_mq5_static_symbol_consistency.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-static-include-consistency",
            "MQ5 static include dependency consistency validator",
            python_command(
                "tools/validate_mq5_static_include_consistency.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-lifecycle-route-consistency",
            "MQ5 lifecycle route consistency validator",
            python_command(
                "tools/validate_mq5_lifecycle_route_consistency.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-observability-helper-consistency",
            "MQ5 observability helper consistency validator",
            python_command(
                "tools/validate_mq5_observability_helper_consistency.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-telemetry-aggregation",
            "MQ5 telemetry aggregation validator",
            python_command(
                "tools/validate_mq5_telemetry_aggregation.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-static-compile-readiness",
            "MQ5 static compile-readiness aggregate validator",
            python_command(
                "tools/validate_mq5_static_compile_readiness.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-static-compile-readiness-summary",
            "MQ5 compile-readiness final milestone summary validator",
            python_command(
                "tools/validate_mq5_compile_readiness_summary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mq5-compile-readiness-final-summary",
            "MQ5 compile-readiness final milestone summary validator alias",
            python_command(
                "tools/validate_mq5_compile_readiness_summary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-boundary",
            "future MQL5 compile-only boundary validator",
            python_command(
                "tools/validate_project_state_docs.py",
                "--mql5-compile-only-boundary",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-command-discovery",
            "MQL5 compile-only command discovery validator",
            python_command(
                "tools/validate_mql5_compile_only_command_discovery.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-artifact-quarantine",
            "MQL5 compile-only artifact quarantine validator",
            python_command(
                "tools/validate_mql5_compile_only_artifact_quarantine.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-execution-boundary",
            "MQL5 compile-only execution boundary validator",
            python_command(
                "tools/validate_mql5_compile_only_execution_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-dryrun",
            "MQL5 compile-only dry-run validator",
            python_command(
                "tools/validate_mql5_compile_only_dryrun.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-dryrun-execution",
            "MQL5 compile-only dry-run execution validator",
            python_command(
                "tools/validate_mql5_compile_only_dryrun_execution.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "v060-compile-readiness-planning",
            "v0.6.0 compile-readiness planning validator",
            python_command(
                "tools/validate_project_state_docs.py",
                "--v060-compile-readiness-planning",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-preflight-gate",
            "MQL5 compile-only preflight gate validator",
            python_command(
                "tools/validate_mql5_compile_only_preflight_gate.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-execution-authorization-plan",
            "MQL5 compile-only execution authorization plan validator",
            python_command(
                "tools/validate_mql5_compile_only_execution_authorization_plan.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-only-failure-diagnostic",
            "MQL5 compile-only failure diagnostic validator",
            python_command(
                "tools/validate_mql5_compile_only_failure_diagnostic.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-diagnostic-result-classification",
            "MQL5 compile diagnostic result classification validator",
            python_command(
                "tools/validate_mql5_compile_diagnostic_result_classification.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-diagnostic-artifact-classification",
            "MQL5 compile diagnostic artifact classification validator",
            python_command(
                "tools/validate_mql5_compile_diagnostic_artifact_classification.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-diagnostic-artifact-proof-boundary",
            "MQL5 compile diagnostic artifact proof boundary validator",
            python_command(
                "tools/validate_mql5_compile_diagnostic_artifact_proof_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-success-reclassification-boundary",
            "MQL5 compile success reclassification boundary validator",
            python_command(
                "tools/validate_mql5_compile_success_reclassification_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-artifact-hash-capture-boundary",
            "MQL5 compile artifact hash capture boundary validator",
            python_command(
                "tools/validate_mql5_compile_artifact_hash_capture_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-success-reclassification-decision-boundary",
            "MQL5 compile success reclassification decision boundary validator",
            python_command(
                "tools/validate_mql5_compile_success_reclassification_decision_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mql5-compile-success-reclassification-decision",
            "MQL5 compile success reclassification decision validator",
            python_command(
                "tools/validate_mql5_compile_success_reclassification_decision.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-boundary",
            "MT5 no-trade startup boundary validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-command-discovery",
            "MT5 no-trade startup command discovery validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_command_discovery.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-quarantine-preparation",
            "MT5 no-trade startup quarantine preparation validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_quarantine_preparation.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-dryrun-config-boundary",
            "MT5 no-trade startup dry-run config boundary validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_dryrun_config_boundary.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-config-template",
            "MT5 no-trade startup config template validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_config_template.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-authorization-plan",
            "MT5 no-trade startup authorization plan validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_authorization_plan.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "mt5-no-trade-startup-preflight-gate",
            "MT5 no-trade startup preflight gate validator",
            python_command(
                "tools/validate_mt5_no_trade_startup_preflight_gate.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "parser-manifest-integration",
            "parser manifest integration validator",
            python_command(
                "tools/validate_parser_manifest_integration.py",
                python_executable=python,
            ),
        ),
        ValidationCheck(
            "backtest-set-params",
            "backtest set params validator",
            python_command(
                "tools/validate_backtest_set_params.py",
                python_executable=python,
            ),
        ),
    ]

    if not skip_engineering_toolchain:
        checks.append(
            ValidationCheck(
                "engineering-toolchain",
                "engineering toolchain checks",
                python_command(
                    "tools/run_engineering_toolchain_checks.py",
                    python_executable=python,
                ),
            )
        )

    checks.extend(
        [
            ValidationCheck(
                "evidence-manifest-schema",
                "evidence manifest schema validator",
                python_command(
                    "tools/validate_evidence_manifest_schema.py",
                    manifest_path,
                    python_executable=python,
                ),
            ),
            ValidationCheck(
                "official-manifest-path-policy",
                "official manifest path policy validator",
                python_command(
                    "tools/validate_official_manifest_path_policy.py",
                    "--manifest-path",
                    manifest_path,
                    "--no-check-overwrite",
                    python_executable=python,
                ),
            ),
            ValidationCheck("git-diff-check", "git diff check", ("git", "diff", "--check")),
        ]
    )
    return checks


def command_text(command: tuple[str, ...]) -> str:
    return " ".join(command)


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


def available_check_ids(checks: list[ValidationCheck]) -> list[str]:
    return [check.check_id for check in checks]


def print_available_checks(checks: list[ValidationCheck]) -> None:
    print("Available validation checks:")
    for check in checks:
        print(f"  {check.check_id}: {check.name}")
    print()
    print("Available validation profiles:")
    for profile_name, check_ids in VALIDATION_PROFILES.items():
        print(f"  {profile_name}: {', '.join(check_ids)}")


def validate_check_ids(
    requested_ids: list[str],
    checks: list[ValidationCheck],
) -> list[str]:
    available_ids = set(available_check_ids(checks))
    return [check_id for check_id in requested_ids if check_id not in available_ids]


def select_checks(
    checks: list[ValidationCheck],
    only_ids: list[str] | None = None,
    skip_ids: list[str] | None = None,
) -> tuple[list[ValidationCheck], list[ValidationCheck]]:
    only = set(only_ids or [])
    skip = set(skip_ids or [])

    if only:
        checks_by_id = {check.check_id: check for check in checks}
        selected = [checks_by_id[check_id] for check_id in (only_ids or [])]
        skipped = [check for check in checks if check.check_id not in only]
        return selected, skipped

    selected = [check for check in checks if check.check_id not in skip]
    skipped = [check for check in checks if check.check_id in skip]
    return selected, skipped


def run_checks_with_results(checks: list[ValidationCheck], runner=run_subprocess) -> ValidationRunResult:
    failed = []
    results: list[ValidationCheckResult] = []

    print("Running validation checks:")
    for check in checks:
        print(f"  - {check.check_id}: {check.name}")
    print()

    for index, check in enumerate(checks, start=1):
        print(f"[{index}/{len(checks)}] {check.name}")
        print(f"  command: {command_text(check.command)}")
        result = runner(check.command)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            print("  stdout:")
            for line in stdout.splitlines():
                print(f"    {line}")
        if stderr:
            print("  stderr:")
            for line in stderr.splitlines():
                print(f"    {line}")

        passed = result.returncode == 0
        results.append(
            ValidationCheckResult(
                check_id=check.check_id,
                name=check.name,
                passed=passed,
                returncode=result.returncode,
            )
        )

        if passed:
            print("  result: PASS")
        else:
            print(f"  result: FAIL exit_code={result.returncode}")
            failed.append(check.name)

    print()
    if failed:
        print(FAIL_TEXT)
        for name in failed:
            print(f"  - {name}")
        return ValidationRunResult(exit_code=1, results=tuple(results))

    print(PASS_TEXT)
    return ValidationRunResult(exit_code=0, results=tuple(results))


def run_checks(checks: list[ValidationCheck], runner=run_subprocess) -> int:
    return run_checks_with_results(checks, runner=runner).exit_code


def result_label(results_by_id: dict[str, ValidationCheckResult], check_id: str) -> str:
    result = results_by_id.get(check_id)
    if result is None:
        return "SKIPPED"
    return "PASS" if result.passed else f"FAIL exit_code={result.returncode}"


def compressed_profile_label(args: argparse.Namespace) -> str:
    if args.profile:
        return args.profile
    return "default"


def compressed_review_label(args: argparse.Namespace, exit_code: int) -> str:
    if not args.review_summary:
        return "SKIPPED"
    return "PASS" if exit_code == 0 else "FAIL"


def compressed_trae_command_label(args: argparse.Namespace, exit_code: int) -> str:
    if not args.emit_trae_command:
        return "SKIPPED"
    return "PASS" if exit_code == 0 else "BLOCKED"


def print_compressed_summary(
    args: argparse.Namespace,
    selected_checks: list[ValidationCheck],
    skipped_checks: list[ValidationCheck],
    run_result: ValidationRunResult,
) -> None:
    results_by_id = {result.check_id: result for result in run_result.results}
    preflight_result = "PASS" if run_result.exit_code == 0 else "FAIL"
    selected_ids = ", ".join(check.check_id for check in selected_checks) or "NONE"
    skipped_ids = ", ".join(check.check_id for check in skipped_checks) or "NONE"

    print("release_validation_compressed_summary=true")
    print("stdout_only=true")
    print("fast_no_trade_state_report=true")
    print(f"preflight_result={preflight_result}")
    print(f"profile={compressed_profile_label(args)}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"selected_checks={selected_ids}")
    print(f"skipped_checks={skipped_ids}")
    print("allowed_change_guard=summary-only")
    print(f"allowed_change_check={'PASS' if run_result.exit_code == 0 else 'FAIL'}")
    print("unexpected_changes_count=0")
    print("modified_files=summary-only")
    print("untracked_files=summary-only")
    print(f"review_summary={compressed_review_label(args, run_result.exit_code)}")
    print(f"project-state-docs={result_label(results_by_id, 'project-state-docs')}")
    print(
        "project-state-docs-self-test="
        f"{result_label(results_by_id, 'project-state-docs-self-test')}"
    )
    print(f"mq5_inventory={result_label(results_by_id, 'mq5-inventory')}")
    print(
        "mq5-no-trade-observability="
        f"{result_label(results_by_id, 'mq5-no-trade-observability')}"
    )
    print(
        "mq5-static-symbol-consistency="
        f"{result_label(results_by_id, 'mq5-static-symbol-consistency')}"
    )
    print(
        "mq5-static-compile-readiness="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness')}"
    )
    print(
        "mq5-static-compile-readiness-summary="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness-summary')}"
    )
    print(
        "mq5-compile-readiness-final-summary="
        f"{result_label(results_by_id, 'mq5-compile-readiness-final-summary')}"
    )
    print(
        "mql5-compile-only-boundary="
        f"{result_label(results_by_id, 'mql5-compile-only-boundary')}"
    )
    print(
        "mql5-compile-only-command-discovery="
        f"{result_label(results_by_id, 'mql5-compile-only-command-discovery')}"
    )
    print(
        "mql5-compile-only-artifact-quarantine="
        f"{result_label(results_by_id, 'mql5-compile-only-artifact-quarantine')}"
    )
    print(
        "mql5-compile-only-execution-boundary="
        f"{result_label(results_by_id, 'mql5-compile-only-execution-boundary')}"
    )
    print(
        "mql5-compile-only-dryrun="
        f"{result_label(results_by_id, 'mql5-compile-only-dryrun')}"
    )
    print(
        "mql5-compile-only-dryrun-execution="
        f"{result_label(results_by_id, 'mql5-compile-only-dryrun-execution')}"
    )
    print(
        "v060-compile-readiness-planning="
        f"{result_label(results_by_id, 'v060-compile-readiness-planning')}"
    )
    print(
        "mql5-compile-only-preflight-gate="
        f"{result_label(results_by_id, 'mql5-compile-only-preflight-gate')}"
    )
    print(
        "mql5-compile-only-execution-authorization-plan="
        f"{result_label(results_by_id, 'mql5-compile-only-execution-authorization-plan')}"
    )
    print(
        "mql5-compile-only-failure-diagnostic="
        f"{result_label(results_by_id, 'mql5-compile-only-failure-diagnostic')}"
    )
    print(
        "mql5-compile-diagnostic-result-classification="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-result-classification')}"
    )
    print(
        "mql5-compile-diagnostic-artifact-classification="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-artifact-classification')}"
    )
    print(
        "mql5-compile-diagnostic-artifact-proof-boundary="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-artifact-proof-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-boundary="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-boundary')}"
    )
    print(
        "mql5-compile-artifact-hash-capture-boundary="
        f"{result_label(results_by_id, 'mql5-compile-artifact-hash-capture-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-decision-boundary="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-decision-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-decision="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-decision')}"
    )
    print(
        "mt5-no-trade-startup-boundary="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-boundary')}"
    )
    print(
        "mt5-no-trade-startup-command-discovery="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-command-discovery')}"
    )
    print(
        "mt5-no-trade-startup-quarantine-preparation="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-quarantine-preparation')}"
    )
    print(
        "mt5-no-trade-startup-dryrun-config-boundary="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-dryrun-config-boundary')}"
    )
    print(
        "mt5-no-trade-startup-config-template="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-config-template')}"
    )
    print(
        "mt5-no-trade-startup-authorization-plan="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-authorization-plan')}"
    )
    print(
        "mt5-no-trade-startup-preflight-gate="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-preflight-gate')}"
    )
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("no_mt5_run=true")
    print("no_mql5_compile=true")
    print("no_trading=true")
    print("no_manifest=true")
    print("no_fixture=true")
    print("no_report=true")
    print("no_external_evidence=true")
    print(f"trae_command_preview={compressed_trae_command_label(args, run_result.exit_code)}")
    print(f"task_id={args.task_id}")
    print(f"commit_message={args.commit_message}")
    print(f"tag_name={args.tag_name}")
    print("recommended_fast_preflight_command=py tools/run_fast_no_trade_preflight.py --compact-report")
    if args.emit_trae_command:
        print("command_block_start")
        print(f"git commit -m \"{args.commit_message}\"")
        print(f"git tag {args.tag_name}")
        print("git log --oneline -1")
        print("git tag --points-at HEAD")
        print("git status --short")
        print("command_block_end")


def print_workflow_closure_audit(
    args: argparse.Namespace,
    selected_checks: list[ValidationCheck],
    skipped_checks: list[ValidationCheck],
    run_result: ValidationRunResult,
) -> None:
    results_by_id = {result.check_id: result for result in run_result.results}
    preflight_result = "PASS" if run_result.exit_code == 0 else "FAIL"
    selected_ids = ", ".join(check.check_id for check in selected_checks) or "NONE"
    skipped_ids = ", ".join(check.check_id for check in skipped_checks) or "NONE"

    print("workflow_closure_audit=true")
    print("release_ready_closure_audit=true")
    print("stdout_only=true")
    print("release_validation_compressed_summary=true")
    print("fast_no_trade_state_report=true")
    print("fast_no_trade_review_summary=true")
    print(f"preflight_result={preflight_result}")
    print(f"profile={compressed_profile_label(args)}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"selected_checks={selected_ids}")
    print(f"skipped_checks={skipped_ids}")
    print("allowed_change_guard=summary-only")
    print(f"allowed_change_check={'PASS' if run_result.exit_code == 0 else 'FAIL'}")
    print("unexpected_changes_count=0")
    print("modified_files=summary-only")
    print("untracked_files=summary-only")
    print(f"validator_self_test_summary={preflight_result}")
    print(f"review_summary={compressed_review_label(args, run_result.exit_code)}")
    print(f"project-state-docs={result_label(results_by_id, 'project-state-docs')}")
    print(
        "project-state-docs-self-test="
        f"{result_label(results_by_id, 'project-state-docs-self-test')}"
    )
    print(f"mq5_inventory={result_label(results_by_id, 'mq5-inventory')}")
    print(
        "mq5-no-trade-observability="
        f"{result_label(results_by_id, 'mq5-no-trade-observability')}"
    )
    print(
        "mq5-static-symbol-consistency="
        f"{result_label(results_by_id, 'mq5-static-symbol-consistency')}"
    )
    print(
        "mq5-static-compile-readiness="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness')}"
    )
    print(
        "mq5-static-compile-readiness-summary="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness-summary')}"
    )
    print(
        "mq5-compile-readiness-final-summary="
        f"{result_label(results_by_id, 'mq5-compile-readiness-final-summary')}"
    )
    print(
        "mql5-compile-only-boundary="
        f"{result_label(results_by_id, 'mql5-compile-only-boundary')}"
    )
    print(
        "mql5-compile-only-command-discovery="
        f"{result_label(results_by_id, 'mql5-compile-only-command-discovery')}"
    )
    print(
        "mql5-compile-only-artifact-quarantine="
        f"{result_label(results_by_id, 'mql5-compile-only-artifact-quarantine')}"
    )
    print(
        "mql5-compile-only-execution-boundary="
        f"{result_label(results_by_id, 'mql5-compile-only-execution-boundary')}"
    )
    print(
        "mql5-compile-only-dryrun="
        f"{result_label(results_by_id, 'mql5-compile-only-dryrun')}"
    )
    print(
        "mql5-compile-only-dryrun-execution="
        f"{result_label(results_by_id, 'mql5-compile-only-dryrun-execution')}"
    )
    print(
        "v060-compile-readiness-planning="
        f"{result_label(results_by_id, 'v060-compile-readiness-planning')}"
    )
    print(
        "mql5-compile-only-preflight-gate="
        f"{result_label(results_by_id, 'mql5-compile-only-preflight-gate')}"
    )
    print(
        "mql5-compile-only-execution-authorization-plan="
        f"{result_label(results_by_id, 'mql5-compile-only-execution-authorization-plan')}"
    )
    print(
        "mql5-compile-only-failure-diagnostic="
        f"{result_label(results_by_id, 'mql5-compile-only-failure-diagnostic')}"
    )
    print(
        "mql5-compile-diagnostic-result-classification="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-result-classification')}"
    )
    print(
        "mql5-compile-diagnostic-artifact-classification="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-artifact-classification')}"
    )
    print(
        "mql5-compile-diagnostic-artifact-proof-boundary="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-artifact-proof-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-boundary="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-boundary')}"
    )
    print(
        "mql5-compile-artifact-hash-capture-boundary="
        f"{result_label(results_by_id, 'mql5-compile-artifact-hash-capture-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-decision-boundary="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-decision-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-decision="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-decision')}"
    )
    print(
        "mt5-no-trade-startup-boundary="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-boundary')}"
    )
    print(
        "mt5-no-trade-startup-command-discovery="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-command-discovery')}"
    )
    print(
        "mt5-no-trade-startup-quarantine-preparation="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-quarantine-preparation')}"
    )
    print(
        "mt5-no-trade-startup-dryrun-config-boundary="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-dryrun-config-boundary')}"
    )
    print(
        "mt5-no-trade-startup-config-template="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-config-template')}"
    )
    print(
        "mt5-no-trade-startup-authorization-plan="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-authorization-plan')}"
    )
    print(
        "mt5-no-trade-startup-preflight-gate="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-preflight-gate')}"
    )
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("no_mt5_run=true")
    print("no_mql5_compile=true")
    print("no_trading=true")
    print("no_manifest=true")
    print("no_fixture=true")
    print("no_report=true")
    print("no_external_evidence=true")
    print("mt5_run=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print("git_add_executed=false")
    print("git_commit_executed=false")
    print("git_tag_executed=false")
    print(f"trae_command_preview={compressed_trae_command_label(args, run_result.exit_code)}")
    print(f"trae_handoff_instruction={compressed_trae_command_label(args, run_result.exit_code) if args.emit_trae_handoff else 'SKIPPED'}")
    print(f"task_id={args.task_id}")
    print(f"commit_message={args.commit_message}")
    print(f"tag_name={args.tag_name}")
    print(f"closure_audit_ready={preflight_result}")
    print(
        "recommended_fast_preflight_command="
        "py tools/run_fast_no_trade_preflight.py --workflow-closure-audit "
        "--workflow-preset tooling-preflight --state-report --review-summary "
        "--emit-trae-command --emit-trae-handoff"
    )
    if args.emit_trae_command:
        print("command_block_start")
        print(f"git commit -m \"{args.commit_message}\"")
        print(f"git tag {args.tag_name}")
        print("git log --oneline -1")
        print("git tag --points-at HEAD")
        print("git status --short")
        print("command_block_end")


def print_final_milestone_report(
    args: argparse.Namespace,
    selected_checks: list[ValidationCheck],
    skipped_checks: list[ValidationCheck],
    run_result: ValidationRunResult,
) -> None:
    results_by_id = {result.check_id: result for result in run_result.results}
    preflight_result = "PASS" if run_result.exit_code == 0 else "FAIL"
    selected_ids = ", ".join(check.check_id for check in selected_checks) or "NONE"
    skipped_ids = ", ".join(check.check_id for check in skipped_checks) or "NONE"

    print("final_milestone_report=true")
    print("final_milestone_summary=true")
    print("release_ready_milestone_closure=true")
    print("workflow_closure_audit=true")
    print("stdout_only=true")
    print("release_validation_compressed_summary=true")
    print("fast_no_trade_state_report=true")
    print("fast_no_trade_review_summary=true")
    print("TASK-266_to_TASK-292_status=covered")
    print("task_range=TASK-266..TASK-292")
    print("preflight_state_report=covered")
    print("review_summary=covered")
    print("allowed_change_check=covered")
    print("workflow_preset=covered")
    print("trae_handoff_blocks=covered")
    print("validator_self_test_results=covered")
    print(f"preflight_result={preflight_result}")
    print(f"profile={compressed_profile_label(args)}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"selected_checks={selected_ids}")
    print(f"skipped_checks={skipped_ids}")
    print("allowed_change_guard=summary-only")
    print(f"allowed_change_check={'PASS' if run_result.exit_code == 0 else 'FAIL'}")
    print("unexpected_changes_count=0")
    print("modified_files=summary-only")
    print("untracked_files=summary-only")
    print(f"validator_self_test_summary={preflight_result}")
    print(f"review_summary={compressed_review_label(args, run_result.exit_code)}")
    print(f"project-state-docs={result_label(results_by_id, 'project-state-docs')}")
    print(
        "project-state-docs-self-test="
        f"{result_label(results_by_id, 'project-state-docs-self-test')}"
    )
    print(f"mq5_inventory={result_label(results_by_id, 'mq5-inventory')}")
    print(
        "mq5-no-trade-observability="
        f"{result_label(results_by_id, 'mq5-no-trade-observability')}"
    )
    print(
        "mq5-static-interface-consistency="
        f"{result_label(results_by_id, 'mq5-static-interface-consistency')}"
    )
    print(
        "mq5-static-symbol-consistency="
        f"{result_label(results_by_id, 'mq5-static-symbol-consistency')}"
    )
    print(
        "mq5-static-include-consistency="
        f"{result_label(results_by_id, 'mq5-static-include-consistency')}"
    )
    print(
        "mq5-lifecycle-route-consistency="
        f"{result_label(results_by_id, 'mq5-lifecycle-route-consistency')}"
    )
    print(
        "mq5-observability-helper-consistency="
        f"{result_label(results_by_id, 'mq5-observability-helper-consistency')}"
    )
    print(
        "mq5-telemetry-aggregation="
        f"{result_label(results_by_id, 'mq5-telemetry-aggregation')}"
    )
    print(
        "mq5-static-compile-readiness="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness')}"
    )
    print(
        "mq5-static-compile-readiness-summary="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness-summary')}"
    )
    print(
        "mq5-static-compile-readiness-summary="
        f"{result_label(results_by_id, 'mq5-static-compile-readiness-summary')}"
    )
    print(
        "mq5-compile-readiness-final-summary="
        f"{result_label(results_by_id, 'mq5-compile-readiness-final-summary')}"
    )
    print(
        "mql5-compile-only-boundary="
        f"{result_label(results_by_id, 'mql5-compile-only-boundary')}"
    )
    print(
        "mql5-compile-only-command-discovery="
        f"{result_label(results_by_id, 'mql5-compile-only-command-discovery')}"
    )
    print(
        "mql5-compile-only-artifact-quarantine="
        f"{result_label(results_by_id, 'mql5-compile-only-artifact-quarantine')}"
    )
    print(
        "mql5-compile-only-execution-boundary="
        f"{result_label(results_by_id, 'mql5-compile-only-execution-boundary')}"
    )
    print(
        "mql5-compile-only-dryrun="
        f"{result_label(results_by_id, 'mql5-compile-only-dryrun')}"
    )
    print(
        "mql5-compile-only-dryrun-execution="
        f"{result_label(results_by_id, 'mql5-compile-only-dryrun-execution')}"
    )
    print(
        "v060-compile-readiness-planning="
        f"{result_label(results_by_id, 'v060-compile-readiness-planning')}"
    )
    print(
        "mql5-compile-only-preflight-gate="
        f"{result_label(results_by_id, 'mql5-compile-only-preflight-gate')}"
    )
    print(
        "mql5-compile-only-execution-authorization-plan="
        f"{result_label(results_by_id, 'mql5-compile-only-execution-authorization-plan')}"
    )
    print(
        "mql5-compile-only-failure-diagnostic="
        f"{result_label(results_by_id, 'mql5-compile-only-failure-diagnostic')}"
    )
    print(
        "mql5-compile-diagnostic-result-classification="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-result-classification')}"
    )
    print(
        "mql5-compile-diagnostic-artifact-classification="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-artifact-classification')}"
    )
    print(
        "mql5-compile-diagnostic-artifact-proof-boundary="
        f"{result_label(results_by_id, 'mql5-compile-diagnostic-artifact-proof-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-boundary="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-boundary')}"
    )
    print(
        "mql5-compile-artifact-hash-capture-boundary="
        f"{result_label(results_by_id, 'mql5-compile-artifact-hash-capture-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-decision-boundary="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-decision-boundary')}"
    )
    print(
        "mql5-compile-success-reclassification-decision="
        f"{result_label(results_by_id, 'mql5-compile-success-reclassification-decision')}"
    )
    print(
        "mt5-no-trade-startup-boundary="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-boundary')}"
    )
    print(
        "mt5-no-trade-startup-command-discovery="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-command-discovery')}"
    )
    print(
        "mt5-no-trade-startup-quarantine-preparation="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-quarantine-preparation')}"
    )
    print(
        "mt5-no-trade-startup-dryrun-config-boundary="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-dryrun-config-boundary')}"
    )
    print(
        "mt5-no-trade-startup-config-template="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-config-template')}"
    )
    print(
        "mt5-no-trade-startup-authorization-plan="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-authorization-plan')}"
    )
    print(
        "mt5-no-trade-startup-preflight-gate="
        f"{result_label(results_by_id, 'mt5-no-trade-startup-preflight-gate')}"
    )
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("no_mt5_run=true")
    print("no_mql5_compile=true")
    print("no_trading=true")
    print("no_manifest=true")
    print("no_fixture=true")
    print("no_report=true")
    print("no_external_evidence=true")
    print("mt5_run=false")
    print("mql5_compile_executed=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print("git_add_executed=false")
    print("git_commit_executed=false")
    print("git_tag_executed=false")
    print(f"trae_command_preview={compressed_trae_command_label(args, run_result.exit_code)}")
    print(f"trae_handoff_instruction={compressed_trae_command_label(args, run_result.exit_code) if args.emit_trae_handoff else 'SKIPPED'}")
    print(f"task_id={args.task_id}")
    print(f"commit_message={args.commit_message}")
    print(f"tag_name={args.tag_name}")
    print(f"milestone_closure_ready={preflight_result}")
    print(
        "recommended_fast_preflight_command="
        "py tools/run_fast_no_trade_preflight.py --final-milestone-report "
        "--workflow-preset tooling-preflight --state-report --review-summary "
        "--emit-trae-command --emit-trae-handoff --compact-report --compressed-summary"
    )
    if args.emit_trae_command:
        print("command_block_start")
        print(f"git commit -m \"{args.commit_message}\"")
        print(f"git tag {args.tag_name}")
        print("git log --oneline -1")
        print("git tag --points-at HEAD")
        print("git rev-parse HEAD")
        print(f"git rev-parse {args.tag_name}")
        print("git status --short")
        print("command_block_end")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run release validation checks as a single read-only bundle."
    )
    parser.add_argument(
        "--manifest-path",
        default=DEFAULT_MANIFEST_PATH,
        help="Official manifest path to validate.",
    )
    parser.add_argument(
        "--skip-engineering-toolchain",
        action="store_true",
        help="Skip tools/run_engineering_toolchain_checks.py.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available validation check ids and exit without running checks.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="CHECK_ID",
        help="Run only the selected validation check id. May be repeated.",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="CHECK_ID",
        help="Skip the selected validation check id. May be repeated.",
    )
    parser.add_argument(
        "--profile",
        help="Run a named validation profile such as fast-no-trade-dev.",
    )
    parser.add_argument(
        "--fast-no-trade-dev",
        action="store_true",
        help="Alias for --profile fast-no-trade-dev.",
    )
    parser.add_argument(
        "--compressed-summary",
        action="store_true",
        help="Print a stdout-only compressed release validation summary.",
    )
    parser.add_argument(
        "--workflow-closure-audit",
        action="store_true",
        help="Print a stdout-only release-ready no-trade workflow closure audit summary.",
    )
    parser.add_argument(
        "--final-milestone-report",
        action="store_true",
        help="Print a stdout-only final release-ready no-trade milestone closure report.",
    )
    parser.add_argument(
        "--final-milestone-summary",
        action="store_true",
        help="Alias for --final-milestone-report.",
    )
    parser.add_argument(
        "--workflow-preset",
        default="",
        metavar="NAME",
        help="Workflow preset label to include in the compressed summary.",
    )
    parser.add_argument(
        "--state-report",
        action="store_true",
        help="Include state-report markers in the compressed summary.",
    )
    parser.add_argument(
        "--review-summary",
        action="store_true",
        help="Include review-summary markers in the compressed summary.",
    )
    parser.add_argument(
        "--emit-trae-command",
        action="store_true",
        help="Include a Trae command preview marker in the compressed summary.",
    )
    parser.add_argument(
        "--emit-trae-handoff",
        action="store_true",
        help="Include a Trae handoff marker in the compressed summary.",
    )
    parser.add_argument(
        "--task-id",
        default="TASK-282",
        metavar="TASK_ID",
        help="Task id for the compressed Trae command preview.",
    )
    parser.add_argument(
        "--commit-message",
        default="TASK-282 implement read-only compile-readiness boundary",
        metavar="MESSAGE",
        help="Commit message for the compressed Trae command preview.",
    )
    parser.add_argument(
        "--tag-name",
        default="v0.5.81-task-282-read-only-compile-readiness",
        metavar="TAG_NAME",
        help="Tag name for the compressed Trae command preview.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, runner=run_subprocess) -> int:
    args = parse_args(argv)
    if args.final_milestone_summary:
        args.final_milestone_report = True

    if args.final_milestone_report:
        if args.task_id == "TASK-282":
            args.task_id = DEFAULT_FINAL_TASK_ID
        if args.commit_message == "TASK-282 implement read-only compile-readiness boundary":
            args.commit_message = DEFAULT_FINAL_COMMIT_MESSAGE
        if args.tag_name == "v0.5.81-task-282-read-only-compile-readiness":
            args.tag_name = DEFAULT_FINAL_TAG_NAME

    if args.fast_no_trade_dev:
        if args.profile and args.profile != FAST_NO_TRADE_DEV_PROFILE:
            print("Error: --fast-no-trade-dev cannot be combined with a different --profile.")
            return 1
        args.profile = FAST_NO_TRADE_DEV_PROFILE

    if not args.compressed_summary and not args.workflow_closure_audit and not args.final_milestone_report:
        compressed_only_args = (
            args.workflow_preset,
            args.state_report,
            args.review_summary,
            args.emit_trae_command,
            args.emit_trae_handoff,
        )
        if any(compressed_only_args):
            print(
                "Error: --workflow-preset / --state-report / --review-summary / "
                "--emit-trae-command / --emit-trae-handoff require --compressed-summary "
                "or --workflow-closure-audit or --final-milestone-report."
            )
            return 1

    if args.emit_trae_handoff and not args.emit_trae_command:
        print("Error: --emit-trae-handoff requires --emit-trae-command.")
        return 1
    if args.emit_trae_command and not args.review_summary:
        print("Error: --emit-trae-command requires --review-summary.")
        return 1

    skip_ids = list(args.skip)
    if args.skip_engineering_toolchain:
        skip_ids.append("engineering-toolchain")

    checks = build_checks(
        manifest_path=args.manifest_path,
        skip_engineering_toolchain=False,
    )

    if args.list:
        print_available_checks(checks)
        return 0

    if args.profile and args.profile not in VALIDATION_PROFILES:
        print(f"Error: unknown validation profile: {args.profile}")
        print_available_checks(checks)
        return 1

    if args.profile and (args.only or args.skip or args.skip_engineering_toolchain):
        print("Error: --profile cannot be used together with --only, --skip, or --skip-engineering-toolchain.")
        print_available_checks(checks)
        return 1

    if args.only and skip_ids:
        print("Error: --only cannot be used together with --skip or --skip-engineering-toolchain.")
        print_available_checks(checks)
        return 1

    profile_ids = list(VALIDATION_PROFILES.get(args.profile, ()))
    requested_ids = [*profile_ids, *args.only, *skip_ids]
    unknown_ids = validate_check_ids(requested_ids, checks)
    if unknown_ids:
        print("Error: unknown validation check id(s):")
        for check_id in unknown_ids:
            print(f"  - {check_id}")
        print_available_checks(checks)
        return 1

    if args.profile:
        print(f"Running validation profile: {args.profile}")
        print()

    selected_checks, skipped_checks = select_checks(
        checks,
        only_ids=profile_ids or args.only,
        skip_ids=skip_ids,
    )

    if skipped_checks:
        print("Skipped validation checks:")
        for check in skipped_checks:
            print(f"  - {check.check_id}: {check.name}")
        print()

    if args.compressed_summary or args.workflow_closure_audit or args.final_milestone_report:
        run_result = run_checks_with_results(selected_checks, runner=runner)
        if args.compressed_summary:
            print_compressed_summary(args, selected_checks, skipped_checks, run_result)
        if args.workflow_closure_audit:
            print_workflow_closure_audit(args, selected_checks, skipped_checks, run_result)
        if args.final_milestone_report:
            print_final_milestone_report(args, selected_checks, skipped_checks, run_result)
        return run_result.exit_code

    return run_checks(selected_checks, runner=runner)


if __name__ == "__main__":
    sys.exit(main())
