from pathlib import Path
import sys


PASS_TEXT = "Runtime parser input samples validation passed"
FAIL_TEXT = "Runtime parser input samples validation failed"

SAMPLE_INPUT = Path("backtest/reports/samples/TASK-012_runtime_summary_sample.log")
TASK_010_INPUT = Path("backtest/reports/TASK-010_v0.1.7_core_signal_log_throttle.md")
SAMPLE_REPORT = Path("backtest/reports/generated/TASK-012_generated_runtime_summary_sample.md")
TASK_010_REPORT = Path(
    "backtest/reports/generated/TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md"
)

SAMPLE_REPORT_REQUIRED_TEXT = [
    "Source File: backtest/reports/samples/TASK-012_runtime_summary_sample.log",
    "totalTicks: 123456",
    "newBarsDetected: 789",
    "signalsEvaluated: 789",
    "riskRejected: 789",
    "riskApproved: 0",
    "executionAttempts: 0",
    "finalBalance: 10000.00 USD",
    "Missing fields count: 0",
    "Missing runtime fields: 0",
    "Missing field ratio: 0.00%",
    "Signal observation fields found: 5",
    "Signal observation fields missing: 0",
    "Risk rejection fields found: 10",
    "Risk rejection fields missing: 0",
    "Log throttle fields found: 8",
    "Log throttle fields missing: 0",
    "The current system is not allowed to perform real trading.",
]

TASK_010_REPORT_REQUIRED_TEXT = [
    "Source File: backtest/reports/TASK-010_v0.1.7_core_signal_log_throttle.md",
    "totalTicks: Not found",
    "newBarsDetected: Not found",
    "signalsEvaluated: Not found",
    "riskRejected: Not found",
    "buySignals: Not found",
    "sellSignals: Not found",
    "printedRiskRejectLogs: Not found",
    "suppressedRiskRejectLogs: Not found",
    "totalNewBarLogEvents: 94013",
    "printedNewBarLogs: 95",
    "suppressedNewBarLogs: 93918",
    "totalSignalLogEvents: 94013",
    "printedSignalLogs: 1844",
    "suppressedSignalLogs: 92169",
    "Missing fields count:",
    "Missing runtime fields:",
    "Signal observation fields missing: 5",
    "Risk rejection fields missing: 9",
    "Log throttle fields missing: 2",
    "The current system is not allowed to perform real trading.",
    "Missing fields are reported as Not found and are not inferred.",
]

REQUIRED_SAFETY_TEXT = [
    "## Safety Notes",
    "The current system is not allowed to perform real trading.",
    "EMA signals are observation-only and are not a production trading strategy.",
    "RiskManager must not be bypassed.",
    "ExecutionManager must not execute real orders in the current stage.",
    "Missing fields are reported as Not found and are not inferred.",
]

PROHIBITED_TEXT = [
    "buy recommendation",
    "sell recommendation",
    "trading recommendation",
    "profitable strategy",
    "live trading ready",
    "can be used for real trading",
    "strategy optimization recommendation",
    "实盘可用",
    "保证盈利",
    "交易建议",
    "绕过风控",
]


def relative_path(path):
    return path.as_posix()


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def missing_file_issues(project_root):
    issues = []
    required_files = [
        SAMPLE_INPUT,
        TASK_010_INPUT,
        SAMPLE_REPORT,
        TASK_010_REPORT,
    ]

    for relative in required_files:
        path = project_root / relative
        if not path.exists():
            issues.append(f"missing required file: {relative_path(relative)}")
        elif not path.is_file():
            issues.append(f"required path is not a file: {relative_path(relative)}")

    return issues


def missing_required_text_issues(report_name, text, required_items):
    issues = []
    for required in required_items:
        if required not in text:
            issues.append(f"{report_name} missing required text: {required}")
    return issues


def prohibited_text_issues(report_name, text):
    issues = []
    lowered_text = text.lower()
    for prohibited in PROHIBITED_TEXT:
        if prohibited.lower() in lowered_text:
            issues.append(f"{report_name} prohibited content: {prohibited}")
    return issues


def report_issues(report_name, text, required_items):
    issues = []
    issues.extend(missing_required_text_issues(report_name, text, required_items))
    issues.extend(missing_required_text_issues(report_name, text, REQUIRED_SAFETY_TEXT))
    issues.extend(prohibited_text_issues(report_name, text))
    return issues


def validate_project(project_root):
    project_root = Path(project_root)
    issues = missing_file_issues(project_root)
    if issues:
        return issues

    sample_text = read_text(project_root / SAMPLE_REPORT)
    task_010_text = read_text(project_root / TASK_010_REPORT)

    issues.extend(
        report_issues("sample generated report", sample_text, SAMPLE_REPORT_REQUIRED_TEXT)
    )
    issues.extend(
        report_issues("TASK-010 generated report", task_010_text, TASK_010_REPORT_REQUIRED_TEXT)
    )

    return issues


def main():
    project_root = Path(__file__).resolve().parents[1]
    issues = validate_project(project_root)

    if issues:
        print(FAIL_TEXT)
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
