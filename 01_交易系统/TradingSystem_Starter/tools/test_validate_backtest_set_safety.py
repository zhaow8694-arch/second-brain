from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap


PASS_TEXT = "Backtest set safety validation passed"
FAIL_TEXT = "Backtest set safety validation failed"
SELF_TEST_PASS_TEXT = "Backtest set safety self-test passed"
SELF_TEST_FAIL_TEXT = "Backtest set safety self-test failed"


def combined_output(result):
    return f"{result.stdout}\n{result.stderr}"


def run_validator(project_root):
    return subprocess.run(
        [sys.executable, "tools/validate_backtest_set_safety.py"],
        cwd=project_root,
        text=True,
        capture_output=True,
    )


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def copy_validator(real_project_root, temp_project):
    source = real_project_root / "tools" / "validate_backtest_set_safety.py"
    target = temp_project / "tools" / "validate_backtest_set_safety.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def run_temp_case(real_project_root, set_files):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project = Path(temp_dir)
        copy_validator(real_project_root, temp_project)
        for filename, content in set_files.items():
            write_text(temp_project / "backtest" / "sets" / filename, content)
        return run_validator(temp_project)


def expect_failure(result, required_texts):
    output = combined_output(result)
    if result.returncode == 0:
        return False
    if FAIL_TEXT not in output:
        return False
    return all(required_text in output for required_text in required_texts)


def expect_success(result, required_texts):
    output = combined_output(result)
    if result.returncode != 0:
        return False
    if PASS_TEXT not in output:
        return False
    return all(required_text in output for required_text in required_texts)


def test_positive_current_project(real_project_root):
    result = run_validator(real_project_root)
    return expect_success(
        result,
        [
            "allowed observation exceptions count: 2",
            "dangerous enabled parameters: 0",
        ],
    )


def test_missing_inp_enable_trading(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"Test.set": "InpEnableDebugLog=true\n"},
    )
    return expect_failure(result, ["missing InpEnableTrading"])


def test_non_exception_trading_true(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"Test.set": "InpEnableTrading=true\n"},
    )
    return expect_failure(result, ["InpEnableTrading is not false"])


def test_allowed_observation_exceptions(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "TASK-009_B_trading_true_observation_block.set": "InpEnableTrading=true\n",
            "TASK-009_C_risk_reject_log_off.set": "InpEnableTrading=true\n",
        },
    )
    return expect_success(
        result,
        [
            "allowed observation-mode exception",
            "allowed observation exceptions count: 2",
        ],
    )


def test_non_exact_observation_exception(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"TASK-009_B_trading_true_observation_block_COPY.set": "InpEnableTrading=true\n"},
    )
    return expect_failure(result, ["InpEnableTrading is not false"])


def test_dangerous_parameter_in_exception(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "TASK-009_B_trading_true_observation_block.set": """
                InpEnableTrading=true
                EnableTrading=true
            """,
        },
    )
    return expect_failure(result, ["dangerous parameter enabled"])


def test_unknown_dangerous_parameter_value(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "Test.set": """
                InpEnableTrading=false
                EnableTrading=maybe
            """,
        },
    )
    return expect_failure(result, ["dangerous parameter value cannot be determined"])


def main():
    real_project_root = Path(__file__).resolve().parents[1]
    checks = [
        ("positive validation did not pass", test_positive_current_project),
        ("missing InpEnableTrading was not detected", test_missing_inp_enable_trading),
        (
            "non-exception InpEnableTrading=true was not detected",
            test_non_exception_trading_true,
        ),
        (
            "allowed observation exceptions did not pass",
            test_allowed_observation_exceptions,
        ),
        (
            "non-exact observation exception was incorrectly allowed",
            test_non_exact_observation_exception,
        ),
        (
            "dangerous parameter in exception file was not detected",
            test_dangerous_parameter_in_exception,
        ),
        (
            "unknown dangerous parameter value was not detected",
            test_unknown_dangerous_parameter_value,
        ),
    ]

    failures = []
    for failure_message, check in checks:
        if not check(real_project_root):
            failures.append(failure_message)

    if failures:
        print(SELF_TEST_FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(SELF_TEST_PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
