#!/usr/bin/env python3
"""Self-test for release validation bundle profiles."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT_DIR / "tools" / "run_release_validation_bundle.py"
FAST_PROFILE_CHECKS = (
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
)


def fail(message: str) -> int:
    print("Release validation bundle profile self-test failed")
    print(message)
    return 1


def load_bundle_module():
    spec = importlib.util.spec_from_file_location("run_release_validation_bundle", BUNDLE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {BUNDLE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_main_with_fake_runner(bundle, args, failing_check_id: str = ""):
    calls = []

    def fake_runner(command):
        calls.append(tuple(command))
        command_text = " ".join(command).replace("\\", "/")
        if failing_check_id and failing_check_id in command_text:
            return subprocess.CompletedProcess(
                list(command),
                1,
                stdout="fake failure stdout",
                stderr="fake failure stderr",
            )
        return subprocess.CompletedProcess(
            list(command),
            0,
            stdout="fake stdout",
            stderr="",
        )

    output = io.StringIO()
    with redirect_stdout(output):
        result = bundle.main(args, runner=fake_runner)
    return result, calls, output.getvalue()


def command_texts(calls) -> list[str]:
    return [" ".join(command).replace("\\", "/") for command in calls]


def test_list_includes_fast_profile(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(bundle, ["--list"])
    if result != 0:
        return "--list returned non-zero"
    if calls:
        return "--list ran subcommands"
    if "Available validation profiles" not in output:
        return f"--list did not print profile section\n{output}"
    if "fast-no-trade-dev" not in output:
        return f"--list did not include fast-no-trade-dev\n{output}"
    if "mq5-static-include-consistency" not in output:
        return f"--list did not include mq5-static-include-consistency\n{output}"
    if "mq5-lifecycle-route-consistency" not in output:
        return f"--list did not include mq5-lifecycle-route-consistency\n{output}"
    if "mq5-observability-helper-consistency" not in output:
        return f"--list did not include mq5-observability-helper-consistency\n{output}"
    if "mq5-telemetry-aggregation" not in output:
        return f"--list did not include mq5-telemetry-aggregation\n{output}"
    if "mq5-static-symbol-consistency" not in output:
        return f"--list did not include mq5-static-symbol-consistency\n{output}"
    if "mq5-static-compile-readiness" not in output:
        return f"--list did not include mq5-static-compile-readiness\n{output}"
    if "mq5-static-compile-readiness-summary" not in output:
        return f"--list did not include mq5-static-compile-readiness-summary\n{output}"
    if "mq5-compile-readiness-final-summary" not in output:
        return f"--list did not include mq5-compile-readiness-final-summary\n{output}"
    if "mql5-compile-only-boundary" not in output:
        return f"--list did not include mql5-compile-only-boundary\n{output}"
    if "mql5-compile-only-command-discovery" not in output:
        return f"--list did not include mql5-compile-only-command-discovery\n{output}"
    if "mql5-compile-only-artifact-quarantine" not in output:
        return f"--list did not include mql5-compile-only-artifact-quarantine\n{output}"
    if "mql5-compile-only-execution-boundary" not in output:
        return f"--list did not include mql5-compile-only-execution-boundary\n{output}"
    if "mql5-compile-only-dryrun" not in output:
        return f"--list did not include mql5-compile-only-dryrun\n{output}"
    if "mql5-compile-only-dryrun-execution" not in output:
        return f"--list did not include mql5-compile-only-dryrun-execution\n{output}"
    if "v060-compile-readiness-planning" not in output:
        return f"--list did not include v060-compile-readiness-planning\n{output}"
    if "mql5-compile-only-preflight-gate" not in output:
        return f"--list did not include mql5-compile-only-preflight-gate\n{output}"
    if "mql5-compile-only-execution-authorization-plan" not in output:
        return f"--list did not include mql5-compile-only-execution-authorization-plan\n{output}"
    if "mql5-compile-only-failure-diagnostic" not in output:
        return f"--list did not include mql5-compile-only-failure-diagnostic\n{output}"
    if "mql5-compile-diagnostic-result-classification" not in output:
        return f"--list did not include mql5-compile-diagnostic-result-classification\n{output}"
    if "mql5-compile-diagnostic-artifact-classification" not in output:
        return f"--list did not include mql5-compile-diagnostic-artifact-classification\n{output}"
    if "mql5-compile-diagnostic-artifact-proof-boundary" not in output:
        return f"--list did not include mql5-compile-diagnostic-artifact-proof-boundary\n{output}"
    if "mql5-compile-success-reclassification-boundary" not in output:
        return f"--list did not include mql5-compile-success-reclassification-boundary\n{output}"
    if "mql5-compile-artifact-hash-capture-boundary" not in output:
        return f"--list did not include mql5-compile-artifact-hash-capture-boundary\n{output}"
    if "mql5-compile-success-reclassification-decision-boundary" not in output:
        return f"--list did not include mql5-compile-success-reclassification-decision-boundary\n{output}"
    if "mql5-compile-success-reclassification-decision" not in output:
        return f"--list did not include mql5-compile-success-reclassification-decision\n{output}"
    if "mt5-no-trade-startup-boundary" not in output:
        return f"--list did not include mt5-no-trade-startup-boundary\n{output}"
    if "mt5-no-trade-startup-command-discovery" not in output:
        return f"--list did not include mt5-no-trade-startup-command-discovery\n{output}"
    if "mt5-no-trade-startup-quarantine-preparation" not in output:
        return f"--list did not include mt5-no-trade-startup-quarantine-preparation\n{output}"
    if "mt5-no-trade-startup-dryrun-config-boundary" not in output:
        return f"--list did not include mt5-no-trade-startup-dryrun-config-boundary\n{output}"
    if "mt5-no-trade-startup-config-template" not in output:
        return f"--list did not include mt5-no-trade-startup-config-template\n{output}"
    if "mt5-no-trade-startup-authorization-plan" not in output:
        return f"--list did not include mt5-no-trade-startup-authorization-plan\n{output}"
    if "mt5-no-trade-startup-preflight-gate" not in output:
        return f"--list did not include mt5-no-trade-startup-preflight-gate\n{output}"
    return ""


def test_fast_profile_selects_expected_checks(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--profile", "fast-no-trade-dev"],
    )
    if result != 0:
        return f"fast profile failed\n{output}"
    if "Running validation profile: fast-no-trade-dev" not in output:
        return f"fast profile output did not identify profile\n{output}"
    if len(calls) != len(FAST_PROFILE_CHECKS):
        return f"fast profile ran {len(calls)} checks, expected {len(FAST_PROFILE_CHECKS)}"

    selected_ids = [check.check_id for check in bundle.select_checks(
        bundle.build_checks(python_executable="PY"),
        only_ids=list(FAST_PROFILE_CHECKS),
    )[0]]
    if tuple(selected_ids) != FAST_PROFILE_CHECKS:
        return f"fast profile check order mismatch: {selected_ids}"

    lines = "\n".join(command_texts(calls))
    required_parts = (
        "tools/validate_project_state_docs.py",
        "tools/test_validate_project_state_docs.py",
        "tools/inspect_mq5_strategy_inventory.py",
        "tools/validate_mq5_no_trade_observability.py",
        "tools/validate_v060_implementation_boundary.py",
        "tools/validate_v060_implementation_readiness.py",
        "tools/validate_project_state_docs.py",
        "--mq5-static-interface-consistency",
        "tools/validate_mq5_static_symbol_consistency.py",
        "tools/validate_mq5_static_include_consistency.py",
        "tools/validate_mq5_lifecycle_route_consistency.py",
        "tools/validate_mq5_observability_helper_consistency.py",
        "tools/validate_mq5_telemetry_aggregation.py",
        "tools/validate_mq5_static_compile_readiness.py",
        "tools/validate_mq5_compile_readiness_summary.py",
        "--mql5-compile-only-boundary",
        "tools/validate_mql5_compile_only_command_discovery.py",
        "tools/validate_mql5_compile_only_artifact_quarantine.py",
        "tools/validate_mql5_compile_only_execution_boundary.py",
        "tools/validate_mql5_compile_only_dryrun.py",
        "tools/validate_mql5_compile_only_dryrun_execution.py",
        "tools/validate_mql5_compile_only_failure_diagnostic.py",
        "tools/validate_mql5_compile_diagnostic_result_classification.py",
        "tools/validate_mql5_compile_diagnostic_artifact_proof_boundary.py",
        "tools/validate_mql5_compile_success_reclassification_boundary.py",
        "tools/validate_mql5_compile_artifact_hash_capture_boundary.py",
        "tools/validate_mql5_compile_success_reclassification_decision_boundary.py",
        "tools/validate_mql5_compile_success_reclassification_decision.py",
        "tools/validate_mt5_no_trade_startup_boundary.py",
        "tools/validate_mt5_no_trade_startup_command_discovery.py",
        "tools/validate_mt5_no_trade_startup_quarantine_preparation.py",
        "tools/validate_mt5_no_trade_startup_dryrun_config_boundary.py",
        "tools/validate_mt5_no_trade_startup_config_template.py",
        "tools/validate_mt5_no_trade_startup_authorization_plan.py",
        "tools/validate_mt5_no_trade_startup_preflight_gate.py",
    )
    for part in required_parts:
        if part not in lines:
            return f"fast profile missing command: {part}\n{lines}"
    if "read-only-compile-readiness-boundary" not in output:
        return f"fast profile missing compile-readiness check\n{output}"
    if "mq5-static-interface-consistency" not in output:
        return f"fast profile missing MQ5 static interface consistency check\n{output}"
    if "mq5-static-symbol-consistency" not in output:
        return f"fast profile missing MQ5 static symbol consistency check\n{output}"
    if "mq5-static-include-consistency" not in output:
        return f"fast profile missing MQ5 static include consistency check\n{output}"
    if "mq5-lifecycle-route-consistency" not in output:
        return f"fast profile missing MQ5 lifecycle route consistency check\n{output}"
    if "mq5-observability-helper-consistency" not in output:
        return f"fast profile missing MQ5 observability helper consistency check\n{output}"
    if "mq5-telemetry-aggregation" not in output:
        return f"fast profile missing MQ5 telemetry aggregation check\n{output}"
    if "mq5-static-compile-readiness" not in output:
        return f"fast profile missing MQ5 static compile-readiness check\n{output}"
    if "mq5-static-compile-readiness-summary" not in output:
        return f"fast profile missing MQ5 static compile-readiness summary check\n{output}"
    if "mq5-compile-readiness-final-summary" not in output:
        return f"fast profile missing MQ5 compile-readiness final summary alias check\n{output}"
    if "mql5-compile-only-boundary" not in output:
        return f"fast profile missing MQL5 compile-only boundary check\n{output}"
    if "mql5-compile-only-command-discovery" not in output:
        return f"fast profile missing MQL5 compile-only command discovery check\n{output}"
    if "mql5-compile-only-artifact-quarantine" not in output:
        return f"fast profile missing MQL5 compile-only artifact quarantine check\n{output}"
    if "mql5-compile-only-execution-boundary" not in output:
        return f"fast profile missing MQL5 compile-only execution boundary check\n{output}"
    if "mql5-compile-only-dryrun" not in output:
        return f"fast profile missing MQL5 compile-only dry-run check\n{output}"
    if "mql5-compile-only-dryrun-execution" not in output:
        return f"fast profile missing MQL5 compile-only dry-run execution check\n{output}"
    if "v060-compile-readiness-planning" not in output:
        return f"fast profile missing v0.6.0 compile-readiness planning check\n{output}"
    if "mql5-compile-only-preflight-gate" not in output:
        return f"fast profile missing MQL5 compile-only preflight gate check\n{output}"
    if "mql5-compile-only-execution-authorization-plan" not in output:
        return f"fast profile missing MQL5 compile-only execution authorization plan check\n{output}"
    if "mql5-compile-only-failure-diagnostic" not in output:
        return f"fast profile missing MQL5 compile-only failure diagnostic check\n{output}"
    if "mql5-compile-diagnostic-result-classification" not in output:
        return f"fast profile missing MQL5 compile diagnostic result classification check\n{output}"
    if "mql5-compile-diagnostic-artifact-proof-boundary" not in output:
        return f"fast profile missing MQL5 compile diagnostic artifact proof boundary check\n{output}"
    if "mql5-compile-success-reclassification-boundary" not in output:
        return f"fast profile missing MQL5 compile success reclassification boundary check\n{output}"
    if "mql5-compile-artifact-hash-capture-boundary" not in output:
        return f"fast profile missing MQL5 compile artifact hash capture boundary check\n{output}"
    if "mql5-compile-success-reclassification-decision-boundary" not in output:
        return f"fast profile missing MQL5 compile success reclassification decision boundary check\n{output}"
    if "mql5-compile-success-reclassification-decision" not in output:
        return f"fast profile missing MQL5 compile success reclassification decision check\n{output}"
    if "mt5-no-trade-startup-boundary" not in output:
        return f"fast profile missing MT5 no-trade startup boundary check\n{output}"
    if "mt5-no-trade-startup-command-discovery" not in output:
        return f"fast profile missing MT5 no-trade startup command discovery check\n{output}"
    if "mt5-no-trade-startup-quarantine-preparation" not in output:
        return f"fast profile missing MT5 no-trade startup quarantine preparation check\n{output}"
    if "mt5-no-trade-startup-dryrun-config-boundary" not in output:
        return f"fast profile missing MT5 no-trade startup dry-run config boundary check\n{output}"
    if "mt5-no-trade-startup-config-template" not in output:
        return f"fast profile missing MT5 no-trade startup config template check\n{output}"
    if "mt5-no-trade-startup-authorization-plan" not in output:
        return f"fast profile missing MT5 no-trade startup authorization plan check\n{output}"
    if "mt5-no-trade-startup-preflight-gate" not in output:
        return f"fast profile missing MT5 no-trade startup preflight gate check\n{output}"
    if "tools/run_mql5_compile_only_quarantined.py" in lines:
        return "fast profile unexpectedly ran actual diagnostic compile runner"
    if "terminal64" in lines.lower():
        return "fast profile unexpectedly referenced terminal64 execution"
    if "tools/run_engineering_toolchain_checks.py" in lines:
        return "fast profile unexpectedly ran engineering toolchain"
    if "git diff --check" in lines:
        return "fast profile unexpectedly ran git diff check"
    return ""


def test_profile_and_only_conflict(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--profile", "fast-no-trade-dev", "--only", "project-state-docs"],
    )
    if result == 0:
        return "--profile and --only conflict did not fail"
    if calls:
        return "--profile and --only conflict ran subcommands"
    if "--profile cannot be used together" not in output:
        return f"profile conflict output was not clear\n{output}"
    return ""


def test_unknown_profile_fails(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--profile", "missing-profile"],
    )
    if result == 0:
        return "unknown profile did not fail"
    if calls:
        return "unknown profile ran subcommands"
    if "unknown validation profile" not in output or "missing-profile" not in output:
        return f"unknown profile output was not clear\n{output}"
    return ""


def test_existing_only_behavior(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "project-state-docs"],
    )
    if result != 0:
        return f"existing --only behavior failed\n{output}"
    if len(calls) != 1:
        return f"--only ran {len(calls)} checks"
    if not any("validate_project_state_docs.py" in part for part in calls[0]):
        return f"--only ran wrong command: {calls[0]}"
    return ""


def test_existing_skip_behavior(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--skip", "engineering-toolchain"],
    )
    if result != 0:
        return f"existing --skip behavior failed\n{output}"
    lines = "\n".join(command_texts(calls))
    if "tools/run_engineering_toolchain_checks.py" in lines:
        return "engineering toolchain was not skipped"
    return ""


def test_compressed_summary_outputs_required_fields(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        [
            "--compressed-summary",
            "--workflow-preset",
            "tooling-preflight",
            "--state-report",
            "--review-summary",
            "--emit-trae-command",
            "--emit-trae-handoff",
        ],
    )
    if result != 0:
        return f"compressed summary failed\n{output}"
    if not calls:
        return "compressed summary did not run validation checks"
    required = (
        "release_validation_compressed_summary=true",
        "fast_no_trade_state_report=true",
        "workflow_preset=tooling-preflight",
        "profile=default",
        "allowed_change_check=",
        "mq5_inventory_expected=7 files",
        "mq5_inventory=",
        "trading_keywords=false",
        "mq5-static-symbol-consistency=",
        "mq5-static-compile-readiness=",
        "mq5-static-compile-readiness-summary=",
        "mq5-compile-readiness-final-summary=",
        "mql5-compile-only-boundary=",
        "mql5-compile-only-command-discovery=",
        "mql5-compile-only-artifact-quarantine=",
        "mql5-compile-only-execution-boundary=",
        "mql5-compile-only-dryrun=",
        "mql5-compile-only-dryrun-execution=",
        "v060-compile-readiness-planning=",
        "mql5-compile-only-preflight-gate=",
        "mql5-compile-only-execution-authorization-plan=",
        "mql5-compile-only-failure-diagnostic=",
        "mql5-compile-diagnostic-result-classification=",
        "mql5-compile-diagnostic-artifact-proof-boundary=",
        "mql5-compile-success-reclassification-boundary=",
        "mql5-compile-artifact-hash-capture-boundary=",
        "mql5-compile-success-reclassification-decision-boundary=",
        "mql5-compile-success-reclassification-decision=",
        "mt5-no-trade-startup-boundary=",
        "mt5-no-trade-startup-command-discovery=",
        "mt5-no-trade-startup-quarantine-preparation=",
        "mt5-no-trade-startup-dryrun-config-boundary=",
        "mt5-no-trade-startup-config-template=",
        "mt5-no-trade-startup-authorization-plan=",
        "mt5-no-trade-startup-preflight-gate=",
        "preflight_result=PASS",
        "review_summary=PASS",
        "project-state-docs=",
        "project-state-docs-self-test=",
        "trae_command_preview=PASS",
        "no_mt5_run=true",
        "no_mql5_compile=true",
        "no_trading=true",
        "no_manifest=true",
        "no_external_evidence=true",
    )
    for text in required:
        if text not in output:
            return f"compressed summary missing {text}\n{output}"
    return ""


def test_compressed_summary_fast_no_trade_dev_alias(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--compressed-summary", "--fast-no-trade-dev", "--workflow-preset", "doc-state", "--review-summary"],
    )
    if result != 0:
        return f"compressed summary fast-no-trade-dev alias failed\n{output}"
    if len(calls) != len(FAST_PROFILE_CHECKS):
        return f"fast-no-trade-dev alias ran {len(calls)} checks"
    if "Running validation profile: fast-no-trade-dev" not in output:
        return f"fast-no-trade-dev alias did not select profile\n{output}"
    if "profile=fast-no-trade-dev" not in output:
        return f"compressed summary missing selected profile\n{output}"
    if "workflow_preset=doc-state" not in output:
        return f"compressed summary missing workflow preset\n{output}"
    return ""


def test_compressed_summary_preserves_only_behavior(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--compressed-summary", "--only", "project-state-docs", "--workflow-preset", "tooling-preflight"],
    )
    if result != 0:
        return f"compressed summary --only failed\n{output}"
    if len(calls) != 1:
        return f"compressed summary --only ran {len(calls)} checks"
    if "project-state-docs=PASS" not in output:
        return f"compressed summary did not report only check\n{output}"
    return ""


def test_compressed_summary_rejects_handoff_without_command(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--compressed-summary", "--review-summary", "--emit-trae-handoff"],
    )
    if result == 0:
        return "compressed summary handoff without command did not fail"
    if calls:
        return "compressed summary invalid handoff ran subcommands"
    if "--emit-trae-handoff requires --emit-trae-command" not in output:
        return f"compressed summary invalid handoff output was not clear\n{output}"
    return ""


def test_workflow_closure_audit_outputs_required_fields(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        [
            "--workflow-closure-audit",
            "--workflow-preset",
            "tooling-preflight",
            "--state-report",
            "--review-summary",
            "--emit-trae-command",
            "--emit-trae-handoff",
        ],
    )
    if result != 0:
        return f"workflow closure audit failed\n{output}"
    if not calls:
        return "workflow closure audit did not run validation checks"
    required = (
        "workflow_closure_audit=true",
        "release_ready_closure_audit=true",
        "stdout_only=true",
        "fast_no_trade_state_report=true",
        "fast_no_trade_review_summary=true",
        "workflow_preset=tooling-preflight",
        "profile=default",
        "allowed_change_check=PASS",
        "validator_self_test_summary=PASS",
        "project-state-docs=PASS",
        "project-state-docs-self-test=PASS",
        "mq5_inventory=PASS",
        "mq5-no-trade-observability=PASS",
        "mq5-static-symbol-consistency=PASS",
        "mq5-static-compile-readiness=PASS",
        "mq5-static-compile-readiness-summary=PASS",
        "mq5-compile-readiness-final-summary=PASS",
        "mql5-compile-only-boundary=PASS",
        "mql5-compile-only-command-discovery=PASS",
        "mql5-compile-only-artifact-quarantine=PASS",
        "mql5-compile-only-execution-boundary=PASS",
        "mql5-compile-only-dryrun=PASS",
        "mql5-compile-only-dryrun-execution=PASS",
        "v060-compile-readiness-planning=PASS",
        "mql5-compile-only-preflight-gate=PASS",
        "mql5-compile-only-execution-authorization-plan=PASS",
        "mql5-compile-only-failure-diagnostic=PASS",
        "mql5-compile-diagnostic-result-classification=PASS",
        "mql5-compile-diagnostic-artifact-classification=PASS",
        "mql5-compile-diagnostic-artifact-proof-boundary=PASS",
        "mql5-compile-success-reclassification-boundary=PASS",
        "mql5-compile-artifact-hash-capture-boundary=PASS",
        "mql5-compile-success-reclassification-decision-boundary=PASS",
        "mql5-compile-success-reclassification-decision=PASS",
        "mt5-no-trade-startup-boundary=PASS",
        "mt5-no-trade-startup-command-discovery=PASS",
        "mt5-no-trade-startup-quarantine-preparation=PASS",
        "mt5-no-trade-startup-dryrun-config-boundary=PASS",
        "mt5-no-trade-startup-config-template=PASS",
        "mt5-no-trade-startup-authorization-plan=PASS",
        "mt5-no-trade-startup-preflight-gate=PASS",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "no_mt5_run=true",
        "no_mql5_compile=true",
        "no_trading=true",
        "no_manifest=true",
        "no_fixture=true",
        "no_report=true",
        "no_external_evidence=true",
        "trae_command_preview=PASS",
        "trae_handoff_instruction=PASS",
        "closure_audit_ready=PASS",
    )
    for text in required:
        if text not in output:
            return f"workflow closure audit missing {text}\n{output}"
    return ""


def test_workflow_closure_audit_preserves_only_behavior(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--workflow-closure-audit", "--only", "project-state-docs", "--workflow-preset", "doc-state"],
    )
    if result != 0:
        return f"workflow closure audit --only failed\n{output}"
    if len(calls) != 1:
        return f"workflow closure audit --only ran {len(calls)} checks"
    if "project-state-docs=PASS" not in output:
        return f"workflow closure audit did not report only check\n{output}"
    if "closure_audit_ready=PASS" not in output:
        return f"workflow closure audit did not report PASS readiness\n{output}"
    return ""


def test_workflow_closure_audit_reports_failure(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--workflow-closure-audit", "--only", "project-state-docs"],
        failing_check_id="validate_project_state_docs.py",
    )
    if result == 0:
        return "workflow closure audit failure scenario did not fail"
    if len(calls) != 1:
        return f"workflow closure audit failure ran {len(calls)} checks"
    required = (
        "workflow_closure_audit=true",
        "preflight_result=FAIL",
        "validator_self_test_summary=FAIL",
        "project-state-docs=FAIL exit_code=1",
        "allowed_change_check=FAIL",
        "trae_command_preview=SKIPPED",
        "trae_handoff_instruction=SKIPPED",
        "closure_audit_ready=FAIL",
    )
    for text in required:
        if text not in output:
            return f"workflow closure audit failure output missing {text}\n{output}"
    return ""


def test_final_milestone_report_outputs_required_fields(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        [
            "--final-milestone-report",
            "--workflow-preset",
            "tooling-preflight",
            "--state-report",
            "--review-summary",
            "--emit-trae-command",
            "--emit-trae-handoff",
        ],
    )
    if result != 0:
        return f"final milestone report failed\n{output}"
    if not calls:
        return "final milestone report did not run validation checks"
    required = (
        "final_milestone_report=true",
        "final_milestone_summary=true",
        "release_ready_milestone_closure=true",
        "stdout_only=true",
        "TASK-266_to_TASK-292_status=covered",
        "task_range=TASK-266..TASK-292",
        "preflight_state_report=covered",
        "review_summary=covered",
        "allowed_change_check=covered",
        "workflow_preset=tooling-preflight",
        "trae_handoff_blocks=covered",
        "validator_self_test_results=covered",
        "validator_self_test_summary=PASS",
        "project-state-docs=PASS",
        "project-state-docs-self-test=PASS",
        "mq5_inventory=PASS",
        "mq5-no-trade-observability=PASS",
        "mq5-static-interface-consistency=PASS",
        "mq5-static-symbol-consistency=PASS",
        "mq5-static-include-consistency=PASS",
        "mq5-lifecycle-route-consistency=PASS",
        "mq5-observability-helper-consistency=PASS",
        "mq5-telemetry-aggregation=PASS",
        "mq5-static-compile-readiness=PASS",
        "mq5-static-compile-readiness-summary=PASS",
        "mq5-compile-readiness-final-summary=PASS",
        "mql5-compile-only-boundary=PASS",
        "mql5-compile-only-command-discovery=PASS",
        "mql5-compile-only-artifact-quarantine=PASS",
        "mql5-compile-only-execution-boundary=PASS",
        "mql5-compile-only-dryrun=PASS",
        "mql5-compile-only-dryrun-execution=PASS",
        "v060-compile-readiness-planning=PASS",
        "mql5-compile-only-preflight-gate=PASS",
        "mql5-compile-only-execution-authorization-plan=PASS",
        "mql5-compile-only-failure-diagnostic=PASS",
        "mql5-compile-diagnostic-result-classification=PASS",
        "mql5-compile-diagnostic-artifact-classification=PASS",
        "mql5-compile-diagnostic-artifact-proof-boundary=PASS",
        "mql5-compile-success-reclassification-boundary=PASS",
        "mql5-compile-artifact-hash-capture-boundary=PASS",
        "mql5-compile-success-reclassification-decision-boundary=PASS",
        "mql5-compile-success-reclassification-decision=PASS",
        "mt5-no-trade-startup-boundary=PASS",
        "mt5-no-trade-startup-command-discovery=PASS",
        "mt5-no-trade-startup-quarantine-preparation=PASS",
        "mt5-no-trade-startup-dryrun-config-boundary=PASS",
        "mt5-no-trade-startup-config-template=PASS",
        "mt5-no-trade-startup-authorization-plan=PASS",
        "mt5-no-trade-startup-preflight-gate=PASS",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "no_mt5_run=true",
        "no_mql5_compile=true",
        "no_trading=true",
        "no_manifest=true",
        "no_fixture=true",
        "no_report=true",
        "no_external_evidence=true",
        "mql5_compile_executed=false",
        "git_add_executed=false",
        "git_commit_executed=false",
        "git_tag_executed=false",
        "trae_command_preview=PASS",
        "trae_handoff_instruction=PASS",
        "task_id=TASK-290",
        "tag_name=v0.5.89-task-290-final-no-trade-workflow-milestone-report",
        "milestone_closure_ready=PASS",
        "command_block_start",
    )
    for text in required:
        if text not in output:
            return f"final milestone report missing {text}\n{output}"
    return ""


def test_final_milestone_report_preserves_only_behavior(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--final-milestone-report", "--only", "project-state-docs", "--workflow-preset", "doc-state"],
    )
    if result != 0:
        return f"final milestone report --only failed\n{output}"
    if len(calls) != 1:
        return f"final milestone report --only ran {len(calls)} checks"
    if "project-state-docs=PASS" not in output:
        return f"final milestone report did not report only check\n{output}"
    if "milestone_closure_ready=PASS" not in output:
        return f"final milestone report did not report PASS readiness\n{output}"
    return ""


def test_final_milestone_report_reports_failure(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--final-milestone-report", "--only", "project-state-docs"],
        failing_check_id="validate_project_state_docs.py",
    )
    if result == 0:
        return "final milestone report failure scenario did not fail"
    if len(calls) != 1:
        return f"final milestone report failure ran {len(calls)} checks"
    required = (
        "final_milestone_report=true",
        "preflight_result=FAIL",
        "validator_self_test_summary=FAIL",
        "project-state-docs=FAIL exit_code=1",
        "allowed_change_check=FAIL",
        "trae_command_preview=SKIPPED",
        "trae_handoff_instruction=SKIPPED",
        "milestone_closure_ready=FAIL",
    )
    for text in required:
        if text not in output:
            return f"final milestone report failure output missing {text}\n{output}"
    return ""


def test_final_milestone_summary_alias_outputs_final_report(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        [
            "--final-milestone-summary",
            "--only",
            "mq5-static-compile-readiness-summary",
            "--workflow-preset",
            "tooling-preflight",
        ],
    )
    if result != 0:
        return f"final milestone summary alias failed\n{output}"
    if len(calls) != 1:
        return f"final milestone summary alias ran {len(calls)} checks"
    required = (
        "final_milestone_report=true",
        "final_milestone_summary=true",
        "task_range=TASK-266..TASK-292",
        "mq5-static-compile-readiness-summary=PASS",
        "milestone_closure_ready=PASS",
    )
    for text in required:
        if text not in output:
            return f"final milestone summary alias missing {text}\n{output}"
    return ""


def test_compile_readiness_check_available_and_uses_project_state_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "read-only-compile-readiness-boundary"],
    )
    if result != 0:
        return f"compile-readiness boundary check failed\n{output}"
    if len(calls) != 1:
        return f"compile-readiness boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_project_state_docs.py" not in line:
        return f"compile-readiness boundary used wrong command\n{line}"
    if "read-only compile-readiness boundary validator" not in output:
        return f"compile-readiness check name missing\n{output}"
    return ""


def test_compile_readiness_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "read-only-compile-readiness-boundary"],
        failing_check_id="validate_project_state_docs.py",
    )
    if result == 0:
        return "compile-readiness failure scenario did not fail"
    if len(calls) != 1:
        return f"compile-readiness failure ran {len(calls)} checks"
    if "read-only compile-readiness boundary validator" not in output:
        return f"compile-readiness failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"compile-readiness failure output missing exit code\n{output}"
    return ""


def test_fast_profile_reports_project_state_self_test_failure(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--profile", "fast-no-trade-dev"],
        failing_check_id="test_validate_project_state_docs.py",
    )
    if result == 0:
        return "fast profile self-test failure scenario did not fail"
    if len(calls) != len(FAST_PROFILE_CHECKS):
        return f"fast profile self-test failure ran {len(calls)} checks"
    if "project state docs self-test" not in output:
        return f"fast profile self-test failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"fast profile self-test failure output missing exit code\n{output}"
    return ""


def test_mq5_static_interface_check_available_and_uses_validator_mode(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-interface-consistency"],
    )
    if result != 0:
        return f"MQ5 static interface check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 static interface check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_project_state_docs.py" not in line:
        return f"MQ5 static interface check used wrong command\n{line}"
    if "--mq5-static-interface-consistency" not in line:
        return f"MQ5 static interface check missing CLI mode\n{line}"
    if "MQ5 static interface consistency validator" not in output:
        return f"MQ5 static interface check name missing\n{output}"
    return ""


def test_mq5_static_interface_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-interface-consistency"],
        failing_check_id="--mq5-static-interface-consistency",
    )
    if result == 0:
        return "MQ5 static interface failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 static interface failure ran {len(calls)} checks"
    if "MQ5 static interface consistency validator" not in output:
        return f"MQ5 static interface failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 static interface failure output missing exit code\n{output}"
    return ""


def test_mq5_static_include_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-include-consistency"],
    )
    if result != 0:
        return f"MQ5 static include check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 static include check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_static_include_consistency.py" not in line:
        return f"MQ5 static include check used wrong command\n{line}"
    if "MQ5 static include dependency consistency validator" not in output:
        return f"MQ5 static include check name missing\n{output}"
    return ""


def test_mq5_static_include_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-include-consistency"],
        failing_check_id="validate_mq5_static_include_consistency.py",
    )
    if result == 0:
        return "MQ5 static include failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 static include failure ran {len(calls)} checks"
    if "MQ5 static include dependency consistency validator" not in output:
        return f"MQ5 static include failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 static include failure output missing exit code\n{output}"
    return ""


def test_mq5_static_symbol_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-symbol-consistency"],
    )
    if result != 0:
        return f"MQ5 static symbol check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 static symbol check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_static_symbol_consistency.py" not in line:
        return f"MQ5 static symbol check used wrong command\n{line}"
    if "MQ5 static symbol/reference consistency validator" not in output:
        return f"MQ5 static symbol check name missing\n{output}"
    return ""


def test_mq5_static_symbol_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-symbol-consistency"],
        failing_check_id="validate_mq5_static_symbol_consistency.py",
    )
    if result == 0:
        return "MQ5 static symbol failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 static symbol failure ran {len(calls)} checks"
    if "MQ5 static symbol/reference consistency validator" not in output:
        return f"MQ5 static symbol failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 static symbol failure output missing exit code\n{output}"
    return ""


def test_mq5_static_compile_readiness_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-compile-readiness"],
    )
    if result != 0:
        return f"MQ5 static compile-readiness check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 static compile-readiness check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_static_compile_readiness.py" not in line:
        return f"MQ5 static compile-readiness check used wrong command\n{line}"
    if "MQ5 static compile-readiness aggregate validator" not in output:
        return f"MQ5 static compile-readiness check name missing\n{output}"
    return ""


def test_mq5_static_compile_readiness_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-compile-readiness"],
        failing_check_id="validate_mq5_static_compile_readiness.py",
    )
    if result == 0:
        return "MQ5 static compile-readiness failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 static compile-readiness failure ran {len(calls)} checks"
    if "MQ5 static compile-readiness aggregate validator" not in output:
        return f"MQ5 static compile-readiness failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 static compile-readiness failure output missing exit code\n{output}"
    return ""


def test_mq5_static_compile_readiness_summary_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-compile-readiness-summary"],
    )
    if result != 0:
        return f"MQ5 static compile-readiness summary check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 static compile-readiness summary check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_compile_readiness_summary.py" not in line:
        return f"MQ5 static compile-readiness summary check used wrong command\n{line}"
    if "MQ5 compile-readiness final milestone summary validator" not in output:
        return f"MQ5 static compile-readiness summary check name missing\n{output}"
    return ""


def test_mq5_static_compile_readiness_summary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-static-compile-readiness-summary"],
        failing_check_id="validate_mq5_compile_readiness_summary.py",
    )
    if result == 0:
        return "MQ5 static compile-readiness summary failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 static compile-readiness summary failure ran {len(calls)} checks"
    if "MQ5 compile-readiness final milestone summary validator" not in output:
        return f"MQ5 static compile-readiness summary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 static compile-readiness summary failure output missing exit code\n{output}"
    return ""


def test_mq5_compile_readiness_final_summary_alias_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-compile-readiness-final-summary"],
    )
    if result != 0:
        return f"MQ5 compile-readiness final summary alias check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 compile-readiness final summary alias ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_compile_readiness_summary.py" not in line:
        return f"MQ5 compile-readiness final summary alias used wrong command\n{line}"
    if "MQ5 compile-readiness final milestone summary validator alias" not in output:
        return f"MQ5 compile-readiness final summary alias name missing\n{output}"
    return ""


def test_mql5_compile_only_boundary_check_available_and_uses_project_state_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-boundary"],
    )
    if result != 0:
        return f"MQL5 compile-only boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only boundary check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_project_state_docs.py" not in line:
        return f"MQL5 compile-only boundary check used wrong command\n{line}"
    if "--mql5-compile-only-boundary" not in line:
        return f"MQL5 compile-only boundary check missing validator mode\n{line}"
    if "future MQL5 compile-only boundary validator" not in output:
        return f"MQL5 compile-only boundary check name missing\n{output}"
    return ""


def test_mql5_compile_only_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-boundary"],
        failing_check_id="--mql5-compile-only-boundary",
    )
    if result == 0:
        return "MQL5 compile-only boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only boundary failure ran {len(calls)} checks"
    if "future MQL5 compile-only boundary validator" not in output:
        return f"MQL5 compile-only boundary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only boundary failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_command_discovery_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-command-discovery"],
    )
    if result != 0:
        return f"MQL5 compile-only command discovery check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only command discovery ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_command_discovery.py" not in line:
        return f"MQL5 compile-only command discovery used wrong command\n{line}"
    if "MQL5 compile-only command discovery validator" not in output:
        return f"MQL5 compile-only command discovery check name missing\n{output}"
    return ""


def test_mql5_compile_only_command_discovery_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-command-discovery"],
        failing_check_id="validate_mql5_compile_only_command_discovery.py",
    )
    if result == 0:
        return "MQL5 compile-only command discovery failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only command discovery failure ran {len(calls)} checks"
    if "MQL5 compile-only command discovery validator" not in output:
        return f"MQL5 compile-only command discovery failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only command discovery failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_artifact_quarantine_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-artifact-quarantine"],
    )
    if result != 0:
        return f"MQL5 compile-only artifact quarantine check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only artifact quarantine ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_artifact_quarantine.py" not in line:
        return f"MQL5 compile-only artifact quarantine used wrong command\n{line}"
    if "MQL5 compile-only artifact quarantine validator" not in output:
        return f"MQL5 compile-only artifact quarantine check name missing\n{output}"
    return ""


def test_mql5_compile_only_artifact_quarantine_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-artifact-quarantine"],
        failing_check_id="validate_mql5_compile_only_artifact_quarantine.py",
    )
    if result == 0:
        return "MQL5 compile-only artifact quarantine failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only artifact quarantine failure ran {len(calls)} checks"
    if "MQL5 compile-only artifact quarantine validator" not in output:
        return f"MQL5 compile-only artifact quarantine failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only artifact quarantine failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_execution_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-execution-boundary"],
    )
    if result != 0:
        return f"MQL5 compile-only execution boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only execution boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_execution_boundary.py" not in line:
        return f"MQL5 compile-only execution boundary used wrong command\n{line}"
    if "MQL5 compile-only execution boundary validator" not in output:
        return f"MQL5 compile-only execution boundary check name missing\n{output}"
    return ""


def test_mql5_compile_only_execution_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-execution-boundary"],
        failing_check_id="validate_mql5_compile_only_execution_boundary.py",
    )
    if result == 0:
        return "MQL5 compile-only execution boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only execution boundary failure ran {len(calls)} checks"
    if "MQL5 compile-only execution boundary validator" not in output:
        return f"MQL5 compile-only execution boundary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only execution boundary failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_dryrun_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-dryrun"],
    )
    if result != 0:
        return f"MQL5 compile-only dry-run check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only dry-run ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_dryrun.py" not in line:
        return f"MQL5 compile-only dry-run used wrong command\n{line}"
    if "MQL5 compile-only dry-run validator" not in output:
        return f"MQL5 compile-only dry-run check name missing\n{output}"
    return ""


def test_mql5_compile_only_dryrun_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-dryrun"],
        failing_check_id="validate_mql5_compile_only_dryrun.py",
    )
    if result == 0:
        return "MQL5 compile-only dry-run failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only dry-run failure ran {len(calls)} checks"
    if "MQL5 compile-only dry-run validator" not in output:
        return f"MQL5 compile-only dry-run failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only dry-run failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_dryrun_execution_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-dryrun-execution"],
    )
    if result != 0:
        return f"MQL5 compile-only dry-run execution check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only dry-run execution ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_dryrun_execution.py" not in line:
        return f"MQL5 compile-only dry-run execution used wrong command\n{line}"
    if "MQL5 compile-only dry-run execution validator" not in output:
        return f"MQL5 compile-only dry-run execution check name missing\n{output}"
    return ""


def test_mql5_compile_only_dryrun_execution_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-dryrun-execution"],
        failing_check_id="validate_mql5_compile_only_dryrun_execution.py",
    )
    if result == 0:
        return "MQL5 compile-only dry-run execution failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only dry-run execution failure ran {len(calls)} checks"
    if "MQL5 compile-only dry-run execution validator" not in output:
        return f"MQL5 compile-only dry-run execution failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only dry-run execution failure output missing exit code\n{output}"
    return ""


def test_v060_compile_readiness_planning_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "v060-compile-readiness-planning"],
    )
    if result != 0:
        return f"v0.6.0 compile-readiness planning check failed\n{output}"
    if len(calls) != 1:
        return f"v0.6.0 compile-readiness planning ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_project_state_docs.py" not in line:
        return f"v0.6.0 compile-readiness planning used wrong command\n{line}"
    if "--v060-compile-readiness-planning" not in line:
        return f"v0.6.0 compile-readiness planning missing validator mode\n{line}"
    if "v0.6.0 compile-readiness planning validator" not in output:
        return f"v0.6.0 compile-readiness planning check name missing\n{output}"
    return ""


def test_v060_compile_readiness_planning_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "v060-compile-readiness-planning"],
        failing_check_id="--v060-compile-readiness-planning",
    )
    if result == 0:
        return "v0.6.0 compile-readiness planning failure scenario did not fail"
    if len(calls) != 1:
        return f"v0.6.0 compile-readiness planning failure ran {len(calls)} checks"
    if "v0.6.0 compile-readiness planning validator" not in output:
        return f"v0.6.0 compile-readiness planning failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"v0.6.0 compile-readiness planning failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_preflight_gate_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-preflight-gate"],
    )
    if result != 0:
        return f"MQL5 compile-only preflight gate check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only preflight gate ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_preflight_gate.py" not in line:
        return f"MQL5 compile-only preflight gate used wrong command\n{line}"
    if "MQL5 compile-only preflight gate validator" not in output:
        return f"MQL5 compile-only preflight gate check name missing\n{output}"
    return ""


def test_mql5_compile_only_preflight_gate_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-preflight-gate"],
        failing_check_id="validate_mql5_compile_only_preflight_gate.py",
    )
    if result == 0:
        return "MQL5 compile-only preflight gate failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only preflight gate failure ran {len(calls)} checks"
    if "MQL5 compile-only preflight gate validator" not in output:
        return f"MQL5 compile-only preflight gate failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only preflight gate failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_execution_authorization_plan_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-execution-authorization-plan"],
    )
    if result != 0:
        return f"MQL5 compile-only execution authorization plan check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only execution authorization plan ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_execution_authorization_plan.py" not in line:
        return f"MQL5 compile-only execution authorization plan used wrong command\n{line}"
    if "MQL5 compile-only execution authorization plan validator" not in output:
        return f"MQL5 compile-only execution authorization plan check name missing\n{output}"
    return ""


def test_mql5_compile_only_execution_authorization_plan_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-execution-authorization-plan"],
        failing_check_id="validate_mql5_compile_only_execution_authorization_plan.py",
    )
    if result == 0:
        return "MQL5 compile-only execution authorization plan failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only execution authorization plan failure ran {len(calls)} checks"
    if "MQL5 compile-only execution authorization plan validator" not in output:
        return f"MQL5 compile-only execution authorization plan failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only execution authorization plan failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_only_failure_diagnostic_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-failure-diagnostic"],
    )
    if result != 0:
        return f"MQL5 compile-only failure diagnostic check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile-only failure diagnostic ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_only_failure_diagnostic.py" not in line:
        return f"MQL5 compile-only failure diagnostic used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile-only failure diagnostic ran actual compile runner\n{line}"
    if "MQL5 compile-only failure diagnostic validator" not in output:
        return f"MQL5 compile-only failure diagnostic check name missing\n{output}"
    return ""


def test_mql5_compile_only_failure_diagnostic_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-only-failure-diagnostic"],
        failing_check_id="validate_mql5_compile_only_failure_diagnostic.py",
    )
    if result == 0:
        return "MQL5 compile-only failure diagnostic failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile-only failure diagnostic failure ran {len(calls)} checks"
    if "MQL5 compile-only failure diagnostic validator" not in output:
        return f"MQL5 compile-only failure diagnostic failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile-only failure diagnostic failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_diagnostic_result_classification_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-diagnostic-result-classification"],
    )
    if result != 0:
        return f"MQL5 compile diagnostic result classification check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile diagnostic result classification ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_diagnostic_result_classification.py" not in line:
        return f"MQL5 compile diagnostic result classification used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile diagnostic result classification ran actual compile runner\n{line}"
    if "MQL5 compile diagnostic result classification validator" not in output:
        return f"MQL5 compile diagnostic result classification check name missing\n{output}"
    return ""


def test_mql5_compile_diagnostic_result_classification_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-diagnostic-result-classification"],
        failing_check_id="validate_mql5_compile_diagnostic_result_classification.py",
    )
    if result == 0:
        return "MQL5 compile diagnostic result classification failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile diagnostic result classification failure ran {len(calls)} checks"
    if "MQL5 compile diagnostic result classification validator" not in output:
        return f"MQL5 compile diagnostic result classification failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile diagnostic result classification failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_diagnostic_artifact_classification_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-diagnostic-artifact-classification"],
    )
    if result != 0:
        return f"MQL5 compile diagnostic artifact classification check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile diagnostic artifact classification ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_diagnostic_artifact_classification.py" not in line:
        return f"MQL5 compile diagnostic artifact classification used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile diagnostic artifact classification ran actual compile runner\n{line}"
    if "MQL5 compile diagnostic artifact classification validator" not in output:
        return f"MQL5 compile diagnostic artifact classification check name missing\n{output}"
    return ""


def test_mql5_compile_diagnostic_artifact_classification_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-diagnostic-artifact-classification"],
        failing_check_id="validate_mql5_compile_diagnostic_artifact_classification.py",
    )
    if result == 0:
        return "MQL5 compile diagnostic artifact classification failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile diagnostic artifact classification failure ran {len(calls)} checks"
    if "MQL5 compile diagnostic artifact classification validator" not in output:
        return f"MQL5 compile diagnostic artifact classification failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile diagnostic artifact classification failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_diagnostic_artifact_proof_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-diagnostic-artifact-proof-boundary"],
    )
    if result != 0:
        return f"MQL5 compile diagnostic artifact proof boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile diagnostic artifact proof boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_diagnostic_artifact_proof_boundary.py" not in line:
        return f"MQL5 compile diagnostic artifact proof boundary used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile diagnostic artifact proof boundary ran actual compile runner\n{line}"
    if "MQL5 compile diagnostic artifact proof boundary validator" not in output:
        return f"MQL5 compile diagnostic artifact proof boundary check name missing\n{output}"
    return ""


def test_mql5_compile_diagnostic_artifact_proof_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-diagnostic-artifact-proof-boundary"],
        failing_check_id="validate_mql5_compile_diagnostic_artifact_proof_boundary.py",
    )
    if result == 0:
        return "MQL5 compile diagnostic artifact proof boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile diagnostic artifact proof boundary failure ran {len(calls)} checks"
    if "MQL5 compile diagnostic artifact proof boundary validator" not in output:
        return f"MQL5 compile diagnostic artifact proof boundary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile diagnostic artifact proof boundary failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_success_reclassification_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-success-reclassification-boundary"],
    )
    if result != 0:
        return f"MQL5 compile success reclassification boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile success reclassification boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_success_reclassification_boundary.py" not in line:
        return f"MQL5 compile success reclassification boundary used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile success reclassification boundary ran actual compile runner\n{line}"
    if "MQL5 compile success reclassification boundary validator" not in output:
        return f"MQL5 compile success reclassification boundary check name missing\n{output}"
    return ""


def test_mql5_compile_success_reclassification_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-success-reclassification-boundary"],
        failing_check_id="validate_mql5_compile_success_reclassification_boundary.py",
    )
    if result == 0:
        return "MQL5 compile success reclassification boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile success reclassification boundary failure ran {len(calls)} checks"
    if "MQL5 compile success reclassification boundary validator" not in output:
        return f"MQL5 compile success reclassification boundary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile success reclassification boundary failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_artifact_hash_capture_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-artifact-hash-capture-boundary"],
    )
    if result != 0:
        return f"MQL5 compile artifact hash capture boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile artifact hash capture boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_artifact_hash_capture_boundary.py" not in line:
        return f"MQL5 compile artifact hash capture boundary used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile artifact hash capture boundary ran actual compile runner\n{line}"
    if "MQL5 compile artifact hash capture boundary validator" not in output:
        return f"MQL5 compile artifact hash capture boundary check name missing\n{output}"
    return ""


def test_mql5_compile_artifact_hash_capture_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-artifact-hash-capture-boundary"],
        failing_check_id="validate_mql5_compile_artifact_hash_capture_boundary.py",
    )
    if result == 0:
        return "MQL5 compile artifact hash capture boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile artifact hash capture boundary failure ran {len(calls)} checks"
    if "MQL5 compile artifact hash capture boundary validator" not in output:
        return f"MQL5 compile artifact hash capture boundary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQL5 compile artifact hash capture boundary failure output missing exit code\n{output}"
    return ""


def test_mql5_compile_success_reclassification_decision_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-success-reclassification-decision-boundary"],
    )
    if result != 0:
        return f"MQL5 compile success reclassification decision boundary check failed\n{output}"
    if len(calls) != 1:
        return (
            "MQL5 compile success reclassification decision boundary ran "
            f"{len(calls)} checks"
        )
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_success_reclassification_decision_boundary.py" not in line:
        return (
            "MQL5 compile success reclassification decision boundary used wrong "
            f"command\n{line}"
        )
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return (
            "MQL5 compile success reclassification decision boundary ran actual "
            f"compile runner\n{line}"
        )
    if "MQL5 compile success reclassification decision boundary validator" not in output:
        return (
            "MQL5 compile success reclassification decision boundary check name "
            f"missing\n{output}"
        )
    return ""


def test_mql5_compile_success_reclassification_decision_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-success-reclassification-decision-boundary"],
        failing_check_id="validate_mql5_compile_success_reclassification_decision_boundary.py",
    )
    if result == 0:
        return (
            "MQL5 compile success reclassification decision boundary failure "
            "scenario did not fail"
        )
    if len(calls) != 1:
        return (
            "MQL5 compile success reclassification decision boundary failure ran "
            f"{len(calls)} checks"
        )
    if "MQL5 compile success reclassification decision boundary validator" not in output:
        return (
            "MQL5 compile success reclassification decision boundary failure output "
            f"missing check name\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MQL5 compile success reclassification decision boundary failure output "
            f"missing exit code\n{output}"
        )
    return ""


def test_mql5_compile_success_reclassification_decision_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-success-reclassification-decision"],
    )
    if result != 0:
        return f"MQL5 compile success reclassification decision check failed\n{output}"
    if len(calls) != 1:
        return f"MQL5 compile success reclassification decision ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mql5_compile_success_reclassification_decision.py" not in line:
        return f"MQL5 compile success reclassification decision used wrong command\n{line}"
    if "tools/run_mql5_compile_only_quarantined.py" in line:
        return f"MQL5 compile success reclassification decision ran actual compile runner\n{line}"
    if "MQL5 compile success reclassification decision validator" not in output:
        return f"MQL5 compile success reclassification decision check name missing\n{output}"
    return ""


def test_mql5_compile_success_reclassification_decision_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mql5-compile-success-reclassification-decision"],
        failing_check_id="validate_mql5_compile_success_reclassification_decision.py",
    )
    if result == 0:
        return "MQL5 compile success reclassification decision failure scenario did not fail"
    if len(calls) != 1:
        return f"MQL5 compile success reclassification decision failure ran {len(calls)} checks"
    if "MQL5 compile success reclassification decision validator" not in output:
        return (
            "MQL5 compile success reclassification decision failure output "
            f"missing check name\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MQL5 compile success reclassification decision failure output "
            f"missing exit code\n{output}"
        )
    return ""


def test_mt5_no_trade_startup_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-boundary"],
    )
    if result != 0:
        return f"MT5 no-trade startup boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_boundary.py" not in line:
        return f"MT5 no-trade startup boundary used wrong command\n{line}"
    if "terminal64" in line.lower():
        return f"MT5 no-trade startup boundary unexpectedly referenced terminal64 execution\n{line}"
    if "MT5 no-trade startup boundary validator" not in output:
        return f"MT5 no-trade startup boundary check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-boundary"],
        failing_check_id="validate_mt5_no_trade_startup_boundary.py",
    )
    if result == 0:
        return "MT5 no-trade startup boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup boundary failure ran {len(calls)} checks"
    if "MT5 no-trade startup boundary validator" not in output:
        return f"MT5 no-trade startup boundary failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MT5 no-trade startup boundary failure output missing exit code\n{output}"
    return ""


def test_mt5_no_trade_startup_command_discovery_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-command-discovery"],
    )
    if result != 0:
        return f"MT5 no-trade startup command discovery check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup command discovery ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_command_discovery.py" not in line:
        return f"MT5 no-trade startup command discovery used wrong command\n{line}"
    if "terminal64.exe" in line.lower() or "terminal.exe" in line.lower():
        return (
            "MT5 no-trade startup command discovery unexpectedly referenced "
            f"terminal execution\n{line}"
        )
    if "MT5 no-trade startup command discovery validator" not in output:
        return f"MT5 no-trade startup command discovery check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_command_discovery_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-command-discovery"],
        failing_check_id="validate_mt5_no_trade_startup_command_discovery.py",
    )
    if result == 0:
        return "MT5 no-trade startup command discovery failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup command discovery failure ran {len(calls)} checks"
    if "MT5 no-trade startup command discovery validator" not in output:
        return (
            "MT5 no-trade startup command discovery failure output missing check name"
            f"\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MT5 no-trade startup command discovery failure output missing exit code"
            f"\n{output}"
        )
    return ""


def test_mt5_no_trade_startup_quarantine_preparation_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-quarantine-preparation"],
    )
    if result != 0:
        return f"MT5 no-trade startup quarantine preparation check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup quarantine preparation ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_quarantine_preparation.py" not in line:
        return f"MT5 no-trade startup quarantine preparation used wrong command\n{line}"
    if "terminal64.exe" in line.lower() or "terminal.exe" in line.lower():
        return (
            "MT5 no-trade startup quarantine preparation unexpectedly referenced "
            f"terminal execution\n{line}"
        )
    if "MT5 no-trade startup quarantine preparation validator" not in output:
        return f"MT5 no-trade startup quarantine preparation check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_quarantine_preparation_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-quarantine-preparation"],
        failing_check_id="validate_mt5_no_trade_startup_quarantine_preparation.py",
    )
    if result == 0:
        return "MT5 no-trade startup quarantine preparation failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup quarantine preparation failure ran {len(calls)} checks"
    if "MT5 no-trade startup quarantine preparation validator" not in output:
        return (
            "MT5 no-trade startup quarantine preparation failure output missing check name"
            f"\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MT5 no-trade startup quarantine preparation failure output missing exit code"
            f"\n{output}"
        )
    return ""


def test_mt5_no_trade_startup_dryrun_config_boundary_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-dryrun-config-boundary"],
    )
    if result != 0:
        return f"MT5 no-trade startup dry-run config boundary check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup dry-run config boundary ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_dryrun_config_boundary.py" not in line:
        return f"MT5 no-trade startup dry-run config boundary used wrong command\n{line}"
    if "terminal64.exe" in line.lower() or "terminal.exe" in line.lower():
        return (
            "MT5 no-trade startup dry-run config boundary unexpectedly referenced "
            f"terminal execution\n{line}"
        )
    if "MT5 no-trade startup dry-run config boundary validator" not in output:
        return f"MT5 no-trade startup dry-run config boundary check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_dryrun_config_boundary_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-dryrun-config-boundary"],
        failing_check_id="validate_mt5_no_trade_startup_dryrun_config_boundary.py",
    )
    if result == 0:
        return "MT5 no-trade startup dry-run config boundary failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup dry-run config boundary failure ran {len(calls)} checks"
    if "MT5 no-trade startup dry-run config boundary validator" not in output:
        return (
            "MT5 no-trade startup dry-run config boundary failure output missing check name"
            f"\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MT5 no-trade startup dry-run config boundary failure output missing exit code"
            f"\n{output}"
        )
    return ""


def test_mt5_no_trade_startup_config_template_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-config-template"],
    )
    if result != 0:
        return f"MT5 no-trade startup config template check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup config template ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_config_template.py" not in line:
        return f"MT5 no-trade startup config template used wrong command\n{line}"
    if "terminal64.exe" in line.lower() or "terminal.exe" in line.lower():
        return (
            "MT5 no-trade startup config template unexpectedly referenced "
            f"terminal execution\n{line}"
        )
    if "MT5 no-trade startup config template validator" not in output:
        return f"MT5 no-trade startup config template check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_config_template_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-config-template"],
        failing_check_id="validate_mt5_no_trade_startup_config_template.py",
    )
    if result == 0:
        return "MT5 no-trade startup config template failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup config template failure ran {len(calls)} checks"
    if "MT5 no-trade startup config template validator" not in output:
        return (
            "MT5 no-trade startup config template failure output missing check name"
            f"\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MT5 no-trade startup config template failure output missing exit code"
            f"\n{output}"
        )
    return ""


def test_mt5_no_trade_startup_authorization_plan_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-authorization-plan"],
    )
    if result != 0:
        return f"MT5 no-trade startup authorization plan check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup authorization plan ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_authorization_plan.py" not in line:
        return f"MT5 no-trade startup authorization plan used wrong command\n{line}"
    if "terminal64.exe" in line.lower() or "terminal.exe" in line.lower():
        return (
            "MT5 no-trade startup authorization plan unexpectedly referenced "
            f"terminal execution\n{line}"
        )
    if "MT5 no-trade startup authorization plan validator" not in output:
        return f"MT5 no-trade startup authorization plan check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_authorization_plan_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-authorization-plan"],
        failing_check_id="validate_mt5_no_trade_startup_authorization_plan.py",
    )
    if result == 0:
        return "MT5 no-trade startup authorization plan failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup authorization plan failure ran {len(calls)} checks"
    if "MT5 no-trade startup authorization plan validator" not in output:
        return (
            "MT5 no-trade startup authorization plan failure output missing check name"
            f"\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MT5 no-trade startup authorization plan failure output missing exit code"
            f"\n{output}"
        )
    return ""


def test_mt5_no_trade_startup_preflight_gate_check_available(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-preflight-gate"],
    )
    if result != 0:
        return f"MT5 no-trade startup preflight gate check failed\n{output}"
    if len(calls) != 1:
        return f"MT5 no-trade startup preflight gate ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mt5_no_trade_startup_preflight_gate.py" not in line:
        return f"MT5 no-trade startup preflight gate used wrong command\n{line}"
    if "terminal64.exe" in line.lower() or "terminal.exe" in line.lower():
        return (
            "MT5 no-trade startup preflight gate unexpectedly referenced "
            f"terminal execution\n{line}"
        )
    if "MT5 no-trade startup preflight gate validator" not in output:
        return f"MT5 no-trade startup preflight gate check name missing\n{output}"
    return ""


def test_mt5_no_trade_startup_preflight_gate_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mt5-no-trade-startup-preflight-gate"],
        failing_check_id="validate_mt5_no_trade_startup_preflight_gate.py",
    )
    if result == 0:
        return "MT5 no-trade startup preflight gate failure scenario did not fail"
    if len(calls) != 1:
        return f"MT5 no-trade startup preflight gate failure ran {len(calls)} checks"
    if "MT5 no-trade startup preflight gate validator" not in output:
        return (
            "MT5 no-trade startup preflight gate failure output missing check name"
            f"\n{output}"
        )
    if "FAIL exit_code=1" not in output:
        return (
            "MT5 no-trade startup preflight gate failure output missing exit code"
            f"\n{output}"
        )
    return ""


def test_mq5_lifecycle_route_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-lifecycle-route-consistency"],
    )
    if result != 0:
        return f"MQ5 lifecycle route check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 lifecycle route check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_lifecycle_route_consistency.py" not in line:
        return f"MQ5 lifecycle route check used wrong command\n{line}"
    if "MQ5 lifecycle route consistency validator" not in output:
        return f"MQ5 lifecycle route check name missing\n{output}"
    return ""


def test_mq5_lifecycle_route_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-lifecycle-route-consistency"],
        failing_check_id="validate_mq5_lifecycle_route_consistency.py",
    )
    if result == 0:
        return "MQ5 lifecycle route failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 lifecycle route failure ran {len(calls)} checks"
    if "MQ5 lifecycle route consistency validator" not in output:
        return f"MQ5 lifecycle route failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 lifecycle route failure output missing exit code\n{output}"
    return ""


def test_mq5_observability_helper_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-observability-helper-consistency"],
    )
    if result != 0:
        return f"MQ5 observability helper check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 observability helper check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_observability_helper_consistency.py" not in line:
        return f"MQ5 observability helper check used wrong command\n{line}"
    if "MQ5 observability helper consistency validator" not in output:
        return f"MQ5 observability helper check name missing\n{output}"
    return ""


def test_mq5_observability_helper_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-observability-helper-consistency"],
        failing_check_id="validate_mq5_observability_helper_consistency.py",
    )
    if result == 0:
        return "MQ5 observability helper failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 observability helper failure ran {len(calls)} checks"
    if "MQ5 observability helper consistency validator" not in output:
        return f"MQ5 observability helper failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 observability helper failure output missing exit code\n{output}"
    return ""


def test_mq5_telemetry_aggregation_check_available_and_uses_validator(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-telemetry-aggregation"],
    )
    if result != 0:
        return f"MQ5 telemetry aggregation check failed\n{output}"
    if len(calls) != 1:
        return f"MQ5 telemetry aggregation check ran {len(calls)} checks"
    line = command_texts(calls)[0]
    if "tools/validate_mq5_telemetry_aggregation.py" not in line:
        return f"MQ5 telemetry aggregation check used wrong command\n{line}"
    if "MQ5 telemetry aggregation validator" not in output:
        return f"MQ5 telemetry aggregation check name missing\n{output}"
    return ""


def test_mq5_telemetry_aggregation_failure_is_reported(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "mq5-telemetry-aggregation"],
        failing_check_id="validate_mq5_telemetry_aggregation.py",
    )
    if result == 0:
        return "MQ5 telemetry aggregation failure scenario did not fail"
    if len(calls) != 1:
        return f"MQ5 telemetry aggregation failure ran {len(calls)} checks"
    if "MQ5 telemetry aggregation validator" not in output:
        return f"MQ5 telemetry aggregation failure output missing check name\n{output}"
    if "FAIL exit_code=1" not in output:
        return f"MQ5 telemetry aggregation failure output missing exit code\n{output}"
    return ""


def main() -> int:
    if not BUNDLE_PATH.exists():
        return fail(f"bundle script not found: {BUNDLE_PATH}")

    bundle = load_bundle_module()
    tests = [
        test_list_includes_fast_profile,
        test_fast_profile_selects_expected_checks,
        test_profile_and_only_conflict,
        test_unknown_profile_fails,
        test_existing_only_behavior,
        test_existing_skip_behavior,
        test_compressed_summary_outputs_required_fields,
        test_compressed_summary_fast_no_trade_dev_alias,
        test_compressed_summary_preserves_only_behavior,
        test_compressed_summary_rejects_handoff_without_command,
        test_workflow_closure_audit_outputs_required_fields,
        test_workflow_closure_audit_preserves_only_behavior,
        test_workflow_closure_audit_reports_failure,
        test_final_milestone_report_outputs_required_fields,
        test_final_milestone_report_preserves_only_behavior,
        test_final_milestone_report_reports_failure,
        test_final_milestone_summary_alias_outputs_final_report,
        test_compile_readiness_check_available_and_uses_project_state_validator,
        test_compile_readiness_failure_is_reported,
        test_fast_profile_reports_project_state_self_test_failure,
        test_mq5_static_interface_check_available_and_uses_validator_mode,
        test_mq5_static_interface_failure_is_reported,
        test_mq5_static_include_check_available_and_uses_validator,
        test_mq5_static_include_failure_is_reported,
        test_mq5_static_symbol_check_available_and_uses_validator,
        test_mq5_static_symbol_failure_is_reported,
        test_mq5_static_compile_readiness_check_available_and_uses_validator,
        test_mq5_static_compile_readiness_failure_is_reported,
        test_mq5_static_compile_readiness_summary_check_available_and_uses_validator,
        test_mq5_static_compile_readiness_summary_failure_is_reported,
        test_mq5_compile_readiness_final_summary_alias_available,
        test_mql5_compile_only_boundary_check_available_and_uses_project_state_validator,
        test_mql5_compile_only_boundary_failure_is_reported,
        test_mql5_compile_only_command_discovery_check_available,
        test_mql5_compile_only_command_discovery_failure_is_reported,
        test_mql5_compile_only_artifact_quarantine_check_available,
        test_mql5_compile_only_artifact_quarantine_failure_is_reported,
        test_mql5_compile_only_execution_boundary_check_available,
        test_mql5_compile_only_execution_boundary_failure_is_reported,
        test_mql5_compile_only_dryrun_check_available,
        test_mql5_compile_only_dryrun_failure_is_reported,
        test_mql5_compile_only_dryrun_execution_check_available,
        test_mql5_compile_only_dryrun_execution_failure_is_reported,
        test_v060_compile_readiness_planning_check_available,
        test_v060_compile_readiness_planning_failure_is_reported,
        test_mql5_compile_only_preflight_gate_check_available,
        test_mql5_compile_only_preflight_gate_failure_is_reported,
        test_mql5_compile_only_execution_authorization_plan_check_available,
        test_mql5_compile_only_execution_authorization_plan_failure_is_reported,
        test_mql5_compile_only_failure_diagnostic_check_available,
        test_mql5_compile_only_failure_diagnostic_failure_is_reported,
        test_mql5_compile_diagnostic_result_classification_check_available,
        test_mql5_compile_diagnostic_result_classification_failure_is_reported,
        test_mql5_compile_diagnostic_artifact_classification_check_available,
        test_mql5_compile_diagnostic_artifact_classification_failure_is_reported,
        test_mql5_compile_diagnostic_artifact_proof_boundary_check_available,
        test_mql5_compile_diagnostic_artifact_proof_boundary_failure_is_reported,
        test_mql5_compile_success_reclassification_boundary_check_available,
        test_mql5_compile_success_reclassification_boundary_failure_is_reported,
        test_mql5_compile_artifact_hash_capture_boundary_check_available,
        test_mql5_compile_artifact_hash_capture_boundary_failure_is_reported,
        test_mql5_compile_success_reclassification_decision_boundary_check_available,
        test_mql5_compile_success_reclassification_decision_boundary_failure_is_reported,
        test_mql5_compile_success_reclassification_decision_check_available,
        test_mql5_compile_success_reclassification_decision_failure_is_reported,
        test_mt5_no_trade_startup_boundary_check_available,
        test_mt5_no_trade_startup_boundary_failure_is_reported,
        test_mt5_no_trade_startup_command_discovery_check_available,
        test_mt5_no_trade_startup_command_discovery_failure_is_reported,
        test_mt5_no_trade_startup_quarantine_preparation_check_available,
        test_mt5_no_trade_startup_quarantine_preparation_failure_is_reported,
        test_mt5_no_trade_startup_dryrun_config_boundary_check_available,
        test_mt5_no_trade_startup_dryrun_config_boundary_failure_is_reported,
        test_mt5_no_trade_startup_config_template_check_available,
        test_mt5_no_trade_startup_config_template_failure_is_reported,
        test_mt5_no_trade_startup_authorization_plan_check_available,
        test_mt5_no_trade_startup_authorization_plan_failure_is_reported,
        test_mt5_no_trade_startup_preflight_gate_check_available,
        test_mt5_no_trade_startup_preflight_gate_failure_is_reported,
        test_mq5_lifecycle_route_check_available_and_uses_validator,
        test_mq5_lifecycle_route_failure_is_reported,
        test_mq5_observability_helper_check_available_and_uses_validator,
        test_mq5_observability_helper_failure_is_reported,
        test_mq5_telemetry_aggregation_check_available_and_uses_validator,
        test_mq5_telemetry_aggregation_failure_is_reported,
    ]

    for test in tests:
        error = test(bundle)
        if error:
            return fail(error)

    print("Release validation bundle profile self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
