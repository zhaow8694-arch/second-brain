#!/usr/bin/env python3
"""Self-test for the MQ5 compile-readiness final milestone summary validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_compile_readiness_summary.py"


def fail(message: str) -> int:
    print("MQ5 compile-readiness summary self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_mq5_compile_readiness_summary",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_main(module, failing_fragment: str = "", command_probe=None):
    calls = []

    def fake_runner(command):
        calls.append(tuple(command))
        command_text = " ".join(command).replace("\\", "/")
        if command_probe is not None:
            command_probe(command_text)
        if failing_fragment and failing_fragment in command_text:
            return subprocess.CompletedProcess(
                list(command),
                1,
                stdout=f"{failing_fragment} failed",
                stderr="",
            )
        return subprocess.CompletedProcess(
            list(command),
            0,
            stdout="dependency validator passed",
            stderr="",
        )

    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main([], runner=fake_runner)
    return result, calls, output.getvalue()


def expect_fail(result: int, failure_name: str) -> str:
    if result == 0:
        return failure_name
    return ""


def test_complete_summary_passes(module) -> str:
    result, calls, output = run_main(module)
    if result != 0:
        return f"complete summary did not pass\n{output}"
    if len(calls) != 3:
        return f"expected 3 dependency validator calls, got {len(calls)}"
    for field in module.REQUIRED_SUMMARY_FIELDS:
        if field not in output:
            return f"PASS output missing {field}\n{output}"
    if "MQ5 compile-readiness final milestone summary validation passed" not in output:
        return f"PASS output missing success heading\n{output}"
    return ""


def test_missing_task_coverage_fails(module) -> str:
    summary = module.build_summary().replace("tasks_covered=TASK-266..TASK-292\n", "", 1)
    return expect_fail(
        0 if module.validate_summary(summary) else 1,
        "missing task coverage was not detected",
    )


def test_missing_mq5_inventory_fails(module) -> str:
    summary = module.build_summary().replace("mq5_inventory_expected=7 files\n", "", 1)
    return expect_fail(
        0 if module.validate_summary(summary) else 1,
        "missing MQ5 inventory was not detected",
    )


def test_missing_trading_keywords_fails(module) -> str:
    summary = module.build_summary().replace("trading_keywords=false\n", "", 1)
    return expect_fail(
        0 if module.validate_summary(summary) else 1,
        "missing trading keyword state was not detected",
    )


def test_missing_no_mt5_and_no_trading_fails(module) -> str:
    summary = module.build_summary().replace("no_mt5_run=true\n", "", 1).replace(
        "no_trading=true\n",
        "",
        1,
    )
    return expect_fail(
        0 if module.validate_summary(summary) else 1,
        "missing no-MT5/no-trading state was not detected",
    )


def test_missing_manifest_and_evidence_fails(module) -> str:
    summary = module.build_summary().replace("no_manifest=true\n", "", 1).replace(
        "no_external_evidence=true\n",
        "",
        1,
    )
    return expect_fail(
        0 if module.validate_summary(summary) else 1,
        "missing no-manifest/no-evidence state was not detected",
    )


def test_failing_dependency_fails_with_name(module) -> str:
    result, _calls, output = run_main(module, failing_fragment="validate_mq5_static_compile_readiness.py")
    if result == 0:
        return "failing dependency did not fail the summary"
    if "mq5-static-compile-readiness failed" not in output:
        return f"dependency failure did not name check\n{output}"
    return ""


def test_does_not_call_mt5_or_compile_commands(module) -> str:
    forbidden_fragments = ("mt5", "metaeditor", "mql5", "powershell", ".ps1")

    def probe(command_text: str) -> None:
        lowered = command_text.lower()
        for fragment in forbidden_fragments:
            if fragment in lowered:
                raise AssertionError(f"forbidden command fragment: {fragment}")

    try:
        result, _calls, output = run_main(module, command_probe=probe)
    except AssertionError as exc:
        return str(exc)
    if result != 0:
        return f"safe command probe did not pass\n{output}"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    module = load_validator_module()
    tests = (
        test_complete_summary_passes,
        test_missing_task_coverage_fails,
        test_missing_mq5_inventory_fails,
        test_missing_trading_keywords_fails,
        test_missing_no_mt5_and_no_trading_fails,
        test_missing_manifest_and_evidence_fails,
        test_failing_dependency_fails_with_name,
        test_does_not_call_mt5_or_compile_commands,
    )
    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQ5 compile-readiness summary self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
