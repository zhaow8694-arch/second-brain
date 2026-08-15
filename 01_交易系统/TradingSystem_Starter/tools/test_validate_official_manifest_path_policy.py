#!/usr/bin/env python3
"""Self-test the official manifest filename/path policy validator."""

from pathlib import Path
import importlib
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "tools"))
VALIDATOR = importlib.import_module("validate_official_manifest_path_policy")

PASS_TEXT = VALIDATOR.PASS_TEXT
FAIL_TEXT = VALIDATOR.FAIL_TEXT
SELF_PASS_TEXT = "Official manifest path policy self-test passed"
SELF_FAIL_TEXT = "Official manifest path policy self-test failed"

VALID_MANIFEST_PATH = "backtest/reports/manifests/TASK-099_example_manifest.json"


def run_validator(manifest_path, extra_args=None):
    args = [
        sys.executable,
        str(ROOT_DIR / "tools" / "validate_official_manifest_path_policy.py"),
        "--manifest-path",
        manifest_path,
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )


def combined_output(result):
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def expect_pass(result, name):
    output = combined_output(result)
    if result.returncode != 0 or PASS_TEXT not in output:
        return f"{name}\n{output}"
    return ""


def expect_fail(result, name):
    output = combined_output(result)
    if result.returncode == 0 or FAIL_TEXT not in output:
        return f"{name}\n{output}"
    return ""


def test_valid_path():
    result = run_validator(VALID_MANIFEST_PATH)
    return expect_pass(result, "valid manifest path should pass")


def test_non_manifests_directory():
    result = run_validator("backtest/reports/other/TASK-099_example_manifest.json")
    return expect_fail(result, "non-manifests directory should be rejected")


def test_invalid_task_id():
    result = run_validator(
        "backtest/reports/manifests/INVALID_99_example_manifest.json"
    )
    return expect_fail(result, "invalid taskId should be rejected")


def test_evidence_set_id_with_spaces():
    result = run_validator(
        "backtest/reports/manifests/TASK-099/bad evidence set/manifest.json"
    )
    return expect_fail(result, "spaces in evidenceSetId should be rejected")


def test_evidence_set_id_chinese():
    result = run_validator(
        "backtest/reports/manifests/TASK-099_测试_manifest.json"
    )
    return expect_fail(result, "Chinese in manifest filename should be rejected")


def test_absolute_path():
    result = run_validator("C:/backtest/reports/manifests/TASK-099_example_manifest.json")
    return expect_fail(result, "absolute path should be rejected")


def test_path_traversal():
    result = run_validator(
        "backtest/reports/manifests/../manifests/TASK-099_example_manifest.json"
    )
    return expect_fail(result, "path traversal should be rejected")


def test_invalid_filename_format():
    result = run_validator(
        "backtest/reports/manifests/TASK-099_example.json"
    )
    return expect_fail(result, "invalid filename format should be rejected")


def test_overwrite_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        manifests_dir = temp_root / "backtest" / "reports" / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        existing_file = manifests_dir / "TASK-099_example_manifest.json"
        existing_file.write_text("{}")

        issues = VALIDATOR.validate_manifest_path(
            VALID_MANIFEST_PATH,
            check_overwrite=True,
            root_dir=temp_root,
        )
        if not issues:
            return "overwrite should be rejected but was not"

        if not any("already exists" in issue.lower() for issue in issues):
            return f"overwrite rejection message not found: {issues}"

    return ""


def main():
    tests = [
        ("valid path", test_valid_path),
        ("non-manifests directory", test_non_manifests_directory),
        ("invalid taskId", test_invalid_task_id),
        ("evidenceSetId with spaces", test_evidence_set_id_with_spaces),
        ("evidenceSetId Chinese", test_evidence_set_id_chinese),
        ("absolute path", test_absolute_path),
        ("path traversal", test_path_traversal),
        ("invalid filename format", test_invalid_filename_format),
        ("overwrite rejected", test_overwrite_rejected),
    ]

    failures = []
    for name, func in tests:
        error = func()
        if error:
            print(f"[FAIL] {name}")
            print(f"       {error.split(chr(10))[0]}")
            failures.append(name)
        else:
            print(f"[PASS] {name}")

    if failures:
        print(f"\n{SELF_FAIL_TEXT}")
        print(f"failed: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"\n{SELF_PASS_TEXT}")
        sys.exit(0)


if __name__ == "__main__":
    main()
