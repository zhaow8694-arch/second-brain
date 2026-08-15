from pathlib import Path
import importlib
import sys
import tempfile


VALIDATOR = importlib.import_module("validate_runtime_parser_input_samples")

SELF_TEST_PASS_TEXT = "Runtime parser input samples self-test passed"
SELF_TEST_FAIL_TEXT = "Runtime parser input samples self-test failed"


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_text(text, old, new):
    if old not in text:
        raise AssertionError(f"test fixture missing expected text: {old}")
    return text.replace(old, new, 1)


def replace_all_text(text, old, new):
    if old not in text:
        raise AssertionError(f"test fixture missing expected text: {old}")
    return text.replace(old, new)


def remove_text(text, target):
    return replace_text(text, target, "")


def remove_all_text(text, target):
    return replace_all_text(text, target, "")


def build_temp_project(real_project_root, mutate=None, omit=None):
    temp_dir = tempfile.TemporaryDirectory()
    temp_project = Path(temp_dir.name)
    omit = set(omit or [])

    sample_report_text = read_text(real_project_root / VALIDATOR.SAMPLE_REPORT)
    task_010_report_text = read_text(real_project_root / VALIDATOR.TASK_010_REPORT)
    sample_input_text = read_text(real_project_root / VALIDATOR.SAMPLE_INPUT)
    task_010_input_text = read_text(real_project_root / VALIDATOR.TASK_010_INPUT)

    if mutate is not None:
        sample_report_text, task_010_report_text = mutate(
            sample_report_text,
            task_010_report_text,
        )

    files = {
        VALIDATOR.SAMPLE_INPUT: sample_input_text,
        VALIDATOR.TASK_010_INPUT: task_010_input_text,
        VALIDATOR.SAMPLE_REPORT: sample_report_text,
        VALIDATOR.TASK_010_REPORT: task_010_report_text,
    }

    for relative_path, content in files.items():
        if relative_path in omit:
            continue
        write_text(temp_project / relative_path, content)

    return temp_dir, temp_project


def expect_success(project_root):
    return not VALIDATOR.validate_project(project_root)


def expect_failure(project_root, expected_text):
    issues = VALIDATOR.validate_project(project_root)
    output = "\n".join(issues)
    return bool(issues) and expected_text in output


def run_negative_case(real_project_root, expected_text, mutate=None, omit=None):
    temp_dir, temp_project = build_temp_project(real_project_root, mutate=mutate, omit=omit)
    try:
        return expect_failure(temp_project, expected_text)
    finally:
        temp_dir.cleanup()


def test_positive_current_project(real_project_root):
    return expect_success(real_project_root)


def test_missing_sample_log_input(real_project_root):
    return run_negative_case(
        real_project_root,
        "missing required file",
        omit=[VALIDATOR.SAMPLE_INPUT],
    )


def test_missing_task_010_input(real_project_root):
    return run_negative_case(
        real_project_root,
        "missing required file",
        omit=[VALIDATOR.TASK_010_INPUT],
    )


def test_missing_sample_generated_report(real_project_root):
    return run_negative_case(
        real_project_root,
        "missing required file",
        omit=[VALIDATOR.SAMPLE_REPORT],
    )


def test_missing_task_010_generated_report(real_project_root):
    return run_negative_case(
        real_project_root,
        "missing required file",
        omit=[VALIDATOR.TASK_010_REPORT],
    )


def test_sample_source_file_wrong(real_project_root):
    def mutate(sample, task_010):
        return (
            replace_text(
                sample,
                "Source File: backtest/reports/samples/TASK-012_runtime_summary_sample.log",
                "Source File: backtest/reports/samples/wrong.log",
            ),
            task_010,
        )

    return run_negative_case(real_project_root, "Source File:", mutate=mutate)


def test_task_010_source_file_wrong(real_project_root):
    def mutate(sample, task_010):
        return (
            sample,
            replace_text(
                task_010,
                "Source File: backtest/reports/TASK-010_v0.1.7_core_signal_log_throttle.md",
                "Source File: backtest/reports/wrong.md",
            ),
        )

    return run_negative_case(real_project_root, "Source File:", mutate=mutate)


def test_sample_total_ticks_not_found(real_project_root):
    def mutate(sample, task_010):
        return replace_text(sample, "totalTicks: 123456", "totalTicks: Not found"), task_010

    return run_negative_case(real_project_root, "totalTicks: 123456", mutate=mutate)


def test_sample_missing_fields_count_not_zero(real_project_root):
    def mutate(sample, task_010):
        return replace_text(sample, "Missing fields count: 0", "Missing fields count: 1"), task_010

    return run_negative_case(real_project_root, "Missing fields count: 0", mutate=mutate)


def test_sample_missing_runtime_fields_not_zero(real_project_root):
    def mutate(sample, task_010):
        return replace_text(sample, "Missing runtime fields: 0", "Missing runtime fields: 1"), task_010

    return run_negative_case(real_project_root, "Missing runtime fields: 0", mutate=mutate)


def test_sample_signal_observation_missing_not_zero(real_project_root):
    def mutate(sample, task_010):
        return (
            replace_text(
                sample,
                "Signal observation fields missing: 0",
                "Signal observation fields missing: 1",
            ),
            task_010,
        )

    return run_negative_case(
        real_project_root,
        "Signal observation fields missing: 0",
        mutate=mutate,
    )


def test_sample_risk_rejection_missing_not_zero(real_project_root):
    def mutate(sample, task_010):
        return (
            replace_text(
                sample,
                "Risk rejection fields missing: 0",
                "Risk rejection fields missing: 1",
            ),
            task_010,
        )

    return run_negative_case(
        real_project_root,
        "Risk rejection fields missing: 0",
        mutate=mutate,
    )


def test_sample_log_throttle_missing_not_zero(real_project_root):
    def mutate(sample, task_010):
        return (
            replace_text(
                sample,
                "Log throttle fields missing: 0",
                "Log throttle fields missing: 1",
            ),
            task_010,
        )

    return run_negative_case(
        real_project_root,
        "Log throttle fields missing: 0",
        mutate=mutate,
    )


def test_task_010_missing_field_changed_to_zero(real_project_root):
    def mutate(sample, task_010):
        return sample, replace_text(task_010, "totalTicks: Not found", "totalTicks: 0")

    return run_negative_case(real_project_root, "totalTicks: Not found", mutate=mutate)


def test_task_010_buy_signals_changed_to_zero(real_project_root):
    def mutate(sample, task_010):
        return sample, replace_all_text(task_010, "buySignals: Not found", "buySignals: 0")

    return run_negative_case(real_project_root, "buySignals: Not found", mutate=mutate)


def test_task_010_printed_risk_reject_logs_changed_to_zero(real_project_root):
    def mutate(sample, task_010):
        return (
            sample,
            replace_all_text(
                task_010,
                "printedRiskRejectLogs: Not found",
                "printedRiskRejectLogs: 0",
            ),
        )

    return run_negative_case(
        real_project_root,
        "printedRiskRejectLogs: Not found",
        mutate=mutate,
    )


def test_task_010_missing_not_found(real_project_root):
    def mutate(sample, task_010):
        return sample, task_010.replace("Not found", "Missing")

    return run_negative_case(real_project_root, "Not found", mutate=mutate)


def test_missing_safety_notes(real_project_root):
    def mutate(sample, task_010):
        return remove_text(sample, "## Safety Notes"), task_010

    return run_negative_case(real_project_root, "## Safety Notes", mutate=mutate)


def test_task_010_missing_safety_notes(real_project_root):
    def mutate(sample, task_010):
        return sample, remove_text(task_010, "## Safety Notes")

    return run_negative_case(real_project_root, "## Safety Notes", mutate=mutate)


def test_missing_real_trading_safety_statement(real_project_root):
    def mutate(sample, task_010):
        return (
            replace_text(
                sample,
                "The current system is not allowed to perform real trading.",
                "The current system stays in observation mode.",
            ),
            task_010,
        )

    return run_negative_case(
        real_project_root,
        "The current system is not allowed to perform real trading.",
        mutate=mutate,
    )


def test_task_010_missing_real_trading_safety_statement(real_project_root):
    def mutate(sample, task_010):
        return (
            sample,
            remove_text(
                task_010,
                "The current system is not allowed to perform real trading.",
            ),
        )

    return run_negative_case(
        real_project_root,
        "The current system is not allowed to perform real trading.",
        mutate=mutate,
    )


def test_missing_not_found_safety_statement(real_project_root):
    def mutate(sample, task_010):
        return (
            remove_text(
                sample,
                "Missing fields are reported as Not found and are not inferred.",
            ),
            task_010,
        )

    return run_negative_case(
        real_project_root,
        "Missing fields are reported as Not found and are not inferred.",
        mutate=mutate,
    )


def test_missing_risk_manager_safety_statement(real_project_root):
    def mutate(sample, task_010):
        return remove_all_text(sample, "RiskManager must not be bypassed."), task_010

    return run_negative_case(
        real_project_root,
        "RiskManager must not be bypassed.",
        mutate=mutate,
    )


def test_missing_execution_manager_safety_statement(real_project_root):
    def mutate(sample, task_010):
        return (
            remove_text(
                sample,
                "ExecutionManager must not execute real orders in the current stage.",
            ),
            task_010,
        )

    return run_negative_case(
        real_project_root,
        "ExecutionManager must not execute real orders in the current stage.",
        mutate=mutate,
    )


def test_prohibited_live_trading_ready(real_project_root):
    def mutate(sample, task_010):
        return sample + "\n- live trading ready\n", task_010

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_can_be_used_for_real_trading(real_project_root):
    def mutate(sample, task_010):
        return sample, task_010 + "\n- can be used for real trading\n"

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_profitable_strategy(real_project_root):
    def mutate(sample, task_010):
        return sample + "\n- profitable strategy\n", task_010

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_buy_recommendation(real_project_root):
    def mutate(sample, task_010):
        return sample, task_010 + "\n- buy recommendation\n"

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_live_trading_ready_in_safety_notes(real_project_root):
    def mutate(sample, task_010):
        return (
            replace_text(
                sample,
                "## Safety Notes",
                "## Safety Notes\n\n- live trading ready",
            ),
            task_010,
        )

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_profitable_strategy_in_task_010(real_project_root):
    def mutate(sample, task_010):
        return sample, task_010 + "\n- profitable strategy\n"

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_chinese_live_trading_ready(real_project_root):
    def mutate(sample, task_010):
        return sample + f"\n- {VALIDATOR.PROHIBITED_TEXT[7]}\n", task_010

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_chinese_guaranteed_profit(real_project_root):
    def mutate(sample, task_010):
        return sample + f"\n- {VALIDATOR.PROHIBITED_TEXT[8]}\n", task_010

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_chinese_trading_advice(real_project_root):
    def mutate(sample, task_010):
        return sample, task_010 + f"\n- {VALIDATOR.PROHIBITED_TEXT[9]}\n"

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def test_prohibited_chinese_bypass_risk(real_project_root):
    def mutate(sample, task_010):
        return sample, task_010 + f"\n- {VALIDATOR.PROHIBITED_TEXT[10]}\n"

    return run_negative_case(real_project_root, "prohibited content", mutate=mutate)


def main():
    real_project_root = Path(__file__).resolve().parents[1]
    checks = [
        ("positive current project validation failed", test_positive_current_project),
        ("missing sample log input was not detected", test_missing_sample_log_input),
        ("missing TASK-010 input was not detected", test_missing_task_010_input),
        ("missing sample generated report was not detected", test_missing_sample_generated_report),
        ("missing TASK-010 generated report was not detected", test_missing_task_010_generated_report),
        ("sample Source File mismatch was not detected", test_sample_source_file_wrong),
        ("TASK-010 Source File mismatch was not detected", test_task_010_source_file_wrong),
        ("sample totalTicks Not found was not detected", test_sample_total_ticks_not_found),
        (
            "sample Missing fields count mismatch was not detected",
            test_sample_missing_fields_count_not_zero,
        ),
        (
            "sample Missing runtime fields mismatch was not detected",
            test_sample_missing_runtime_fields_not_zero,
        ),
        (
            "sample Signal observation fields missing mismatch was not detected",
            test_sample_signal_observation_missing_not_zero,
        ),
        (
            "sample Risk rejection fields missing mismatch was not detected",
            test_sample_risk_rejection_missing_not_zero,
        ),
        (
            "sample Log throttle fields missing mismatch was not detected",
            test_sample_log_throttle_missing_not_zero,
        ),
        (
            "TASK-010 totalTicks changed to zero was not detected",
            test_task_010_missing_field_changed_to_zero,
        ),
        (
            "TASK-010 buySignals changed to zero was not detected",
            test_task_010_buy_signals_changed_to_zero,
        ),
        (
            "TASK-010 printedRiskRejectLogs changed to zero was not detected",
            test_task_010_printed_risk_reject_logs_changed_to_zero,
        ),
        ("TASK-010 missing Not found was not detected", test_task_010_missing_not_found),
        ("missing Safety Notes was not detected", test_missing_safety_notes),
        ("missing TASK-010 Safety Notes was not detected", test_task_010_missing_safety_notes),
        (
            "missing real trading safety statement was not detected",
            test_missing_real_trading_safety_statement,
        ),
        (
            "missing TASK-010 real trading safety statement was not detected",
            test_task_010_missing_real_trading_safety_statement,
        ),
        (
            "missing Not found safety statement was not detected",
            test_missing_not_found_safety_statement,
        ),
        (
            "missing RiskManager safety statement was not detected",
            test_missing_risk_manager_safety_statement,
        ),
        (
            "missing ExecutionManager safety statement was not detected",
            test_missing_execution_manager_safety_statement,
        ),
        ("live trading ready was not detected", test_prohibited_live_trading_ready),
        (
            "can be used for real trading was not detected",
            test_prohibited_can_be_used_for_real_trading,
        ),
        ("profitable strategy was not detected", test_prohibited_profitable_strategy),
        ("buy recommendation was not detected", test_prohibited_buy_recommendation),
        (
            "live trading ready in Safety Notes was not detected",
            test_prohibited_live_trading_ready_in_safety_notes,
        ),
        (
            "profitable strategy in TASK-010 report was not detected",
            test_prohibited_profitable_strategy_in_task_010,
        ),
        (
            "Chinese live trading ready was not detected",
            test_prohibited_chinese_live_trading_ready,
        ),
        (
            "Chinese guaranteed profit was not detected",
            test_prohibited_chinese_guaranteed_profit,
        ),
        (
            "Chinese trading advice was not detected",
            test_prohibited_chinese_trading_advice,
        ),
        ("Chinese bypass risk was not detected", test_prohibited_chinese_bypass_risk),
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
