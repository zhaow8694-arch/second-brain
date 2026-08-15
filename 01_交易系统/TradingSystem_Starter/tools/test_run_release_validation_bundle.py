#!/usr/bin/env python3
"""Self-test for the release validation bundle command builder."""

from __future__ import annotations

from pathlib import Path
from contextlib import redirect_stdout
import importlib.util
import io
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT_DIR / "tools" / "run_release_validation_bundle.py"


def fail(message: str) -> int:
    print("Release validation bundle self-test failed")
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


def command_lines(checks) -> list[str]:
    return [" ".join(check.command) for check in checks]


def has_command_containing(checks, *parts: str) -> bool:
    return any(
        all(part in " ".join(check.command).replace("\\", "/") for part in parts)
        for check in checks
    )


def run_main_with_fake_runner(bundle, args):
    calls = []

    def fake_runner(command):
        calls.append(tuple(command))
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


def test_default_manifest_path(bundle) -> str:
    checks = bundle.build_checks(python_executable="PY")
    expected = bundle.DEFAULT_MANIFEST_PATH
    if not has_command_containing(checks, expected):
        return f"default manifest path missing from commands: {expected}"
    return ""


def test_required_commands(bundle) -> str:
    checks = bundle.build_checks(python_executable="PY")
    requirements = [
        ("tools/validate_project_state_docs.py",),
        ("tools/test_validate_project_state_docs.py",),
        ("tools/validate_workflow_simplification_policy.py",),
        ("tools/validate_v060_transition_boundary.py",),
        ("tools/validate_v060_implementation_planning_boundary.py",),
        ("tools/validate_v060_implementation_boundary.py",),
        ("tools/validate_v060_implementation_readiness.py",),
        ("tools/inspect_mq5_strategy_inventory.py", "--mq5-root", "MQ5", "--json"),
        ("tools/run_engineering_toolchain_checks.py",),
        ("tools/validate_evidence_manifest_schema.py",),
        ("tools/validate_official_manifest_path_policy.py",),
        ("--no-check-overwrite",),
        ("git", "diff", "--check"),
    ]
    lines = "\n".join(command_lines(checks))
    for requirement in requirements:
        if not has_command_containing(checks, *requirement):
            return f"required command missing {requirement}\n{lines}"
    if has_command_containing(checks, "--fail-on-missing-root"):
        return f"inventory scanner must not use --fail-on-missing-root by default\n{lines}"
    return ""


def test_list_does_not_run_subcommands(bundle) -> str:
    def failing_runner(command):
        raise AssertionError(f"--list must not run subcommands: {command}")

    output = io.StringIO()
    with redirect_stdout(output):
        result = bundle.main(["--list"], runner=failing_runner)

    text = output.getvalue()
    if result != 0:
        return "--list returned non-zero"
    if "project-state-docs" not in text:
        return f"--list did not print available check ids\n{text}"
    return ""


def test_only_runs_selected_check(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "project-state-docs"],
    )
    if result != 0:
        return f"--only project-state-docs failed\n{output}"
    if len(calls) != 1:
        return f"--only project-state-docs ran {len(calls)} checks"
    if not any("validate_project_state_docs.py" in part for part in calls[0]):
        return f"--only project-state-docs ran wrong command: {calls[0]}"
    return ""


def test_multiple_only_runs_selected_checks(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        [
            "--only",
            "project-state-docs",
            "--only",
            "git-diff-check",
        ],
    )
    if result != 0:
        return f"multiple --only failed\n{output}"
    if len(calls) != 2:
        return f"multiple --only ran {len(calls)} checks"
    lines = "\n".join(" ".join(command) for command in calls)
    if "validate_project_state_docs.py" not in lines or "git diff --check" not in lines:
        return f"multiple --only ran wrong commands\n{lines}"
    return ""


def test_skip_check_id(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--skip", "engineering-toolchain"],
    )
    if result != 0:
        return f"--skip engineering-toolchain failed\n{output}"
    lines = "\n".join(" ".join(command) for command in calls)
    if "run_engineering_toolchain_checks.py" in lines:
        return "engineering toolchain was not skipped by --skip"
    return ""


def test_skip_engineering_toolchain_alias_cli(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--skip-engineering-toolchain"],
    )
    if result != 0:
        return f"--skip-engineering-toolchain failed\n{output}"
    lines = "\n".join(" ".join(command) for command in calls)
    if "run_engineering_toolchain_checks.py" in lines:
        return "engineering toolchain was not skipped by alias"
    return ""


def test_only_and_skip_conflict(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "project-state-docs", "--skip", "git-diff-check"],
    )
    if result == 0:
        return "--only and --skip conflict did not fail"
    if calls:
        return "--only and --skip conflict ran subcommands"
    if "--only cannot be used together" not in output:
        return f"conflict output was not clear\n{output}"
    return ""


def test_unknown_check_id_fails(bundle) -> str:
    result, calls, output = run_main_with_fake_runner(
        bundle,
        ["--only", "missing-check"],
    )
    if result == 0:
        return "unknown check id did not fail"
    if calls:
        return "unknown check id ran subcommands"
    if "missing-check" not in output or "Available validation checks" not in output:
        return f"unknown check id output was not clear\n{output}"
    return ""


def test_skip_engineering_toolchain(bundle) -> str:
    checks = bundle.build_checks(
        skip_engineering_toolchain=True,
        python_executable="PY",
    )
    if has_command_containing(checks, "tools/run_engineering_toolchain_checks.py"):
        return "engineering toolchain was not skipped"
    return ""


def test_custom_manifest_path(bundle) -> str:
    custom_path = "backtest/reports/manifests/TASK-999_custom_manifest.json"
    checks = bundle.build_checks(manifest_path=custom_path, python_executable="PY")
    if not has_command_containing(checks, custom_path):
        return "custom manifest path missing from commands"
    if has_command_containing(checks, bundle.DEFAULT_MANIFEST_PATH):
        return "default manifest path still present with custom manifest path"
    return ""


def test_failure_exit_code(bundle) -> str:
    checks = [
        bundle.ValidationCheck("pass-check", "pass check", ("pass",)),
        bundle.ValidationCheck("fail-check", "fail check", ("fail",)),
    ]

    def fake_runner(command):
        returncode = 1 if command == ("fail",) else 0
        return subprocess.CompletedProcess(
            list(command),
            returncode,
            stdout="fake stdout",
            stderr="fake stderr" if returncode else "",
        )

    result = bundle.run_checks(checks, runner=fake_runner)
    if result == 0:
        return "failing subcommand did not fail bundle"
    return ""


def main() -> int:
    if not BUNDLE_PATH.exists():
        return fail(f"bundle script not found: {BUNDLE_PATH}")

    bundle = load_bundle_module()
    tests = [
        test_default_manifest_path,
        test_required_commands,
        test_list_does_not_run_subcommands,
        test_only_runs_selected_check,
        test_multiple_only_runs_selected_checks,
        test_skip_check_id,
        test_skip_engineering_toolchain,
        test_skip_engineering_toolchain_alias_cli,
        test_custom_manifest_path,
        test_only_and_skip_conflict,
        test_unknown_check_id_fails,
        test_failure_exit_code,
    ]

    for test in tests:
        error = test(bundle)
        if error:
            return fail(error)

    print("Release validation bundle self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
