#!/usr/bin/env python3
"""Run CLI self-tests for the backtest runtime report validator."""

from pathlib import Path
import sys
import tempfile
import textwrap

import validate_backtest_runtime_report as validator


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT_DIR / "tools" / "validate_backtest_runtime_report.py"
POSITIVE_REPORTS = [
    ROOT_DIR / "backtest" / "reports" / "generated" / "TASK-012_generated_runtime_summary_sample.md",
    ROOT_DIR
    / "backtest"
    / "reports"
    / "generated"
    / "TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md",
]


def validate_report_path(report_path):
    text = validator.read_report(Path(report_path))
    return validator.find_missing_items(text)


def fail(message):
    print("Backtest runtime report validator self-test failed")
    print("Self-test failed")
    print(message)
    return 1


def validate_required_files():
    if not VALIDATOR.exists():
        return f"validator script not found: {VALIDATOR}"

    for report_path in POSITIVE_REPORTS:
        if not report_path.exists():
            return f"report file not found: {report_path}"

    return ""


def validate_positive_reports():
    for report_path in POSITIVE_REPORTS:
        missing = validate_report_path(report_path)

        if missing:
            return f"positive report did not pass: {report_path}\nmissing: {missing}"

    return ""


def write_temp_report_and_validate(report_text):
    with tempfile.TemporaryDirectory() as temp_dir:
        report_path = Path(temp_dir) / "runtime_report.md"
        report_path.write_text(report_text, encoding="utf-8")
        return validate_report_path(report_path)


def build_field_coverage_lines(not_found_set):
    total_fields = sum(len(fields) for _, fields in validator.SECTION_FIELDS)
    section_counts = []
    missing_fields = 0

    for section_title, fields in validator.SECTION_FIELDS:
        section_missing = sum(1 for field in fields if field in not_found_set)
        section_found = len(fields) - section_missing
        missing_fields += section_missing
        section_counts.append((section_title, section_found, section_missing))

    found_fields = total_fields - missing_fields
    missing_ratio = (missing_fields / total_fields * 100) if total_fields else 0

    lines = [
        "## Field Coverage Summary",
        f"- Total runtime fields: {total_fields}",
        f"- Found runtime fields: {found_fields}",
        f"- Missing runtime fields: {missing_fields}",
        f"- Missing field ratio: {missing_ratio:.2f}%",
        "- Not found values are not inferred.",
        "- Not found does not mean zero.",
        "- Not found does not mean the backtest failed.",
    ]

    for section_title, section_found, section_missing in section_counts:
        lines.append(f"- {section_title}: found {section_found} / missing {section_missing}")

    return lines


def build_signal_observation_lines(not_found_set):
    missing_fields = [
        field
        for field in validator.SIGNAL_OBSERVATION_FIELDS
        if field in not_found_set
    ]
    found_fields = len(validator.SIGNAL_OBSERVATION_FIELDS) - len(missing_fields)

    lines = ["## Signal Observation Summary"]
    for field in validator.SIGNAL_OBSERVATION_FIELDS:
        value = "Not found" if field in not_found_set else "1"
        lines.append(f"- {field}: {value}")

    lines.extend(
        [
            f"- Signal observation fields found: {found_fields}",
            f"- Signal observation fields missing: {len(missing_fields)}",
        ]
    )
    if missing_fields:
        lines.append("- Missing signal observation fields:")
        lines.extend(f"  - {field}" for field in missing_fields)
    else:
        lines.append("- Missing signal observation fields: none")

    lines.extend(
        [
            "- Signals are observation-only and are not trading instructions.",
            "- Signal observation values are parsed from source text only.",
            "- Not found signal fields are not inferred.",
            "- This section does not enable real trading.",
        ]
    )
    return lines


def build_risk_rejection_lines(not_found_set):
    missing_fields = [
        field
        for field in validator.RISK_REJECTION_FIELDS
        if field in not_found_set
    ]
    found_fields = len(validator.RISK_REJECTION_FIELDS) - len(missing_fields)

    lines = ["## Risk Rejection Summary"]
    for field in validator.RISK_REJECTION_FIELDS:
        value = "Not found" if field in not_found_set else "1"
        lines.append(f"- {field}: {value}")

    lines.extend(
        [
            f"- Risk rejection fields found: {found_fields}",
            f"- Risk rejection fields missing: {len(missing_fields)}",
        ]
    )
    if missing_fields:
        lines.append("- Missing risk rejection fields:")
        lines.extend(f"  - {field}" for field in missing_fields)
    else:
        lines.append("- Missing risk rejection fields: none")

    lines.extend(
        [
            "- Risk rejection values are parsed from source text only.",
            "- Not found risk rejection fields are not inferred.",
            "- Risk rejection summary does not enable real trading.",
            "- RiskManager must not be bypassed.",
        ]
    )
    return lines


def expected_log_ratio(numerator, denominator):
    if numerator is None or denominator is None:
        return "Not found"
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator * 100):.2f}%"


def build_log_throttle_lines(not_found_set):
    missing_fields = [
        field
        for field in validator.LOG_THROTTLE_FIELDS
        if field in not_found_set
    ]
    found_fields = len(validator.LOG_THROTTLE_FIELDS) - len(missing_fields)

    values = {}
    for field in validator.LOG_THROTTLE_FIELDS:
        values[field] = None if field in not_found_set else 1

    risk_total = None
    if (
        values["printedRiskRejectLogs"] is not None
        and values["suppressedRiskRejectLogs"] is not None
    ):
        risk_total = values["printedRiskRejectLogs"] + values["suppressedRiskRejectLogs"]

    lines = ["## Log Throttle Summary"]
    for field in validator.LOG_THROTTLE_FIELDS:
        value = "Not found" if field in not_found_set else "1"
        lines.append(f"- {field}: {value}")

    lines.extend(
        [
            f"- Risk reject log print ratio: {expected_log_ratio(values['printedRiskRejectLogs'], risk_total)}",
            f"- New bar log print ratio: {expected_log_ratio(values['printedNewBarLogs'], values['totalNewBarLogEvents'])}",
            f"- Signal log print ratio: {expected_log_ratio(values['printedSignalLogs'], values['totalSignalLogEvents'])}",
            f"- Log throttle fields found: {found_fields}",
            f"- Log throttle fields missing: {len(missing_fields)}",
        ]
    )
    if missing_fields:
        lines.append("- Missing log throttle fields:")
        lines.extend(f"  - {field}" for field in missing_fields)
    else:
        lines.append("- Missing log throttle fields: none")

    lines.extend(
        [
            "- Log throttle values are parsed from source text only.",
            "- Not found log throttle fields are not inferred.",
            "- Log throttle summary does not enable real trading.",
            "- Log throttle ratios are reporting metrics, not trading signals.",
        ]
    )
    return lines


def make_runtime_report(
    not_found_fields=None,
    missing_fields_count=None,
    include_missing_field_list=True,
    listed_fields=None,
):
    not_found_fields = list(not_found_fields or [])
    if listed_fields is None:
        listed_fields = not_found_fields
    listed_fields = list(listed_fields)
    not_found_set = set(not_found_fields)
    if missing_fields_count is None:
        missing_fields_count = len(not_found_fields)

    lines = [
        "# Backtest Runtime Summary Draft",
        "",
        "## Report Metadata",
        f"- {validator.REQUIRED_SUBSTRINGS[0]}",
        "- Generated By: tools/parse_backtest_runtime_summary.py",
        "",
        "## Runtime Summary Counters",
    ]

    for field in validator.RUNTIME_SUMMARY_FIELDS:
        value = "Not found" if field in not_found_set else "1"
        lines.append(f"- {field}: {value}")

    lines.extend(
        [
            "",
            "## Runtime Summary Signal Stats",
            "",
            "## Runtime Summary Risk Reject Stats",
            "",
            "## Runtime Summary Risk Log Stats",
            "",
            "## Runtime Summary Core / New Bar Log Stats",
            "",
            "## Runtime Summary Signal Log Stats",
            "",
            "## Final Balance",
            "- finalBalance: 10000.00",
            "",
            *build_field_coverage_lines(not_found_set),
            "",
            *build_signal_observation_lines(not_found_set),
            "",
            *build_risk_rejection_lines(not_found_set),
            "",
            *build_log_throttle_lines(not_found_set),
            "",
            "## Missing Field Notes",
            f"- Missing fields count: {missing_fields_count}",
            "- Missing fields are reported as Not found.",
            "- Not found means the field was not present in the parsed source text.",
            "- Not found values are not inferred.",
            "- Not found does not mean zero.",
            "- Not found does not mean the backtest failed.",
            "- Parser output is based on parsed text only.",
        ]
    )

    if include_missing_field_list and listed_fields:
        lines.append("- Missing fields:")
        for field in listed_fields:
            lines.append(f"  - {field}")

    lines.extend(
        [
            "",
            "## Safety Notes",
            "- This is a draft generated from parsed text only.",
            "- The current system is not allowed to perform real trading.",
            "- EMA signals are observation-only and are not a production trading strategy.",
            "- RiskManager must not be bypassed.",
            "- ExecutionManager must not execute real orders in the current stage.",
            "- Missing fields are reported as Not found and are not inferred.",
        ]
    )

    return "\n".join(lines) + "\n"


def validate_invalid_report():
    invalid_report = textwrap.dedent(
        f"""\
        # Invalid Backtest Runtime Summary Draft

        ## Report Metadata
        - {validator.REQUIRED_SUBSTRINGS[0]}
        - Generated By: tools/parse_backtest_runtime_summary.py

        ## Runtime Summary Counters
        - totalTicks: 1
        """
    )

    missing = write_temp_report_and_validate(invalid_report)
    if not missing:
        return "invalid report unexpectedly passed"

    return ""


def validate_section_order_negative_reports():
    no_missing_report = make_runtime_report([])

    negative_cases = [
        (
            "missing main report title",
            report_without_line_containing(no_missing_report, "# Backtest Runtime Summary Draft"),
            "# Backtest Runtime Summary Draft",
        ),
        (
            "missing Field Coverage Summary section",
            report_without_line_containing(no_missing_report, "## Field Coverage Summary"),
            "## Field Coverage Summary",
        ),
        (
            "missing Signal Observation Summary section",
            report_without_line_containing(no_missing_report, "## Signal Observation Summary"),
            "## Signal Observation Summary",
        ),
        (
            "missing Risk Rejection Summary section",
            report_without_line_containing(no_missing_report, "## Risk Rejection Summary"),
            "## Risk Rejection Summary",
        ),
        (
            "missing Log Throttle Summary section",
            report_without_line_containing(no_missing_report, "## Log Throttle Summary"),
            "## Log Throttle Summary",
        ),
        (
            "missing Missing Field Notes section",
            report_without_line_containing(no_missing_report, "## Missing Field Notes"),
            "## Missing Field Notes",
        ),
        (
            "missing Safety Notes section",
            report_without_line_containing(no_missing_report, "## Safety Notes"),
            "## Safety Notes",
        ),
        (
            "Safety Notes before Missing Field Notes",
            report_with_swapped_headings(
                no_missing_report,
                "## Missing Field Notes",
                "## Safety Notes",
            ),
            "Section order mismatch",
        ),
        (
            "Log Throttle Summary before Risk Rejection Summary",
            report_with_swapped_headings(
                no_missing_report,
                "## Risk Rejection Summary",
                "## Log Throttle Summary",
            ),
            "Section order mismatch",
        ),
        (
            "duplicate Safety Notes section",
            report_with_duplicate_heading(no_missing_report, "## Safety Notes"),
            "Duplicate required section: ## Safety Notes",
        ),
        (
            "duplicate Field Coverage Summary section",
            report_with_duplicate_heading(no_missing_report, "## Field Coverage Summary"),
            "Duplicate required section: ## Field Coverage Summary",
        ),
        (
            "required section order is shuffled",
            report_with_swapped_headings(
                no_missing_report,
                "## Runtime Summary Counters",
                "## Final Balance",
            ),
            "Section order mismatch",
        ),
        (
            "unknown Trading Recommendation section",
            report_with_unknown_section_at_end(
                no_missing_report,
                "## Trading Recommendation",
                "- Do not use runtime reports as trading instructions.",
            ),
            "unknown report section: ## Trading Recommendation",
        ),
        (
            "unknown Profit Analysis section",
            report_with_unknown_section_at_end(
                no_missing_report,
                "## Profit Analysis",
                "- Profit analysis is not part of this generated runtime report.",
            ),
            "unknown report section: ## Profit Analysis",
        ),
        (
            "unknown Live Trading Notes section",
            report_with_unknown_section_at_end(
                no_missing_report,
                "## Live Trading Notes",
                "- Live trading notes are not allowed in this report.",
            ),
            "unknown report section: ## Live Trading Notes",
        ),
        (
            "unknown Strategy Optimization section",
            report_with_unknown_section_at_end(
                no_missing_report,
                "## Strategy Optimization",
                "- Strategy optimization is not part of this report.",
            ),
            "unknown report section: ## Strategy Optimization",
        ),
        (
            "unknown section at report end",
            report_with_unknown_section_at_end(
                no_missing_report,
                "## Trading Recommendation",
            ),
            "unknown report section: ## Trading Recommendation",
        ),
        (
            "unknown section inserted between required sections",
            report_with_unknown_section_before(
                no_missing_report,
                "## Risk Rejection Summary",
                "## Profit Analysis",
            ),
            "unknown report section: ## Profit Analysis",
        ),
        (
            "empty unknown section fails",
            report_with_unknown_section_before(
                no_missing_report,
                "## Safety Notes",
                "## Live Trading Notes",
            ),
            "unknown report section: ## Live Trading Notes",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_allowed_safety_content():
    report = make_runtime_report([])
    allowed_phrases = [
        "The current system is not allowed to perform real trading.",
        "Signals are observation-only and are not trading instructions.",
        "This section does not enable real trading.",
        "RiskManager must not be bypassed.",
        "ExecutionManager must not execute real orders in the current stage.",
    ]

    for phrase in allowed_phrases:
        if phrase not in report:
            return f"allowed safety statement missing from test report: {phrase}"

    missing = write_temp_report_and_validate(report)
    if missing:
        return f"allowed safety statements were rejected: {missing}"

    return ""


def validate_prohibited_content_negative_reports():
    no_missing_report = make_runtime_report([])

    negative_cases = [
        (
            "buy recommendation in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Report Metadata",
                "- buy recommendation",
            ),
            "prohibited runtime report content: buy recommendation",
        ),
        (
            "sell recommendation in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Report Metadata",
                "- sell recommendation",
            ),
            "prohibited runtime report content: sell recommendation",
        ),
        (
            "profitable strategy in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Field Coverage Summary",
                "- profitable strategy",
            ),
            "prohibited runtime report content: profitable strategy",
        ),
        (
            "live trading ready in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Field Coverage Summary",
                "- live trading ready",
            ),
            "prohibited runtime report content: live trading ready",
        ),
        (
            "can be used for real trading in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Field Coverage Summary",
                "- can be used for real trading",
            ),
            "prohibited runtime report content: can be used for real trading",
        ),
        (
            "bypass RiskManager in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Missing Field Notes",
                "- bypass RiskManager",
            ),
            "prohibited runtime report content: bypass RiskManager",
        ),
        (
            "ExecutionManager can execute real orders in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Missing Field Notes",
                "- ExecutionManager can execute real orders",
            ),
            "prohibited runtime report content: ExecutionManager can execute real orders",
        ),
        (
            "strategy optimization recommendation in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Missing Field Notes",
                "- strategy optimization recommendation",
            ),
            "prohibited runtime report content: strategy optimization recommendation",
        ),
        (
            "Chinese live trading statement in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Report Metadata",
                "- 实盘可用",
            ),
            "prohibited runtime report content: 实盘可用",
        ),
        (
            "Chinese guaranteed profit statement in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Report Metadata",
                "- 保证盈利",
            ),
            "prohibited runtime report content: 保证盈利",
        ),
        (
            "Chinese trading recommendation in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Report Metadata",
                "- 交易建议",
            ),
            "prohibited runtime report content: 交易建议",
        ),
        (
            "Chinese risk bypass statement in legal section",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Report Metadata",
                "- 绕过风控",
            ),
            "prohibited runtime report content: 绕过风控",
        ),
        (
            "prohibited content in Safety Notes",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Safety Notes",
                "- trading recommendation",
            ),
            "prohibited runtime report content: trading recommendation",
        ),
        (
            "prohibited content in Signal Observation Summary",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "- should buy",
            ),
            "prohibited runtime report content: should buy",
        ),
        (
            "prohibited content in Risk Rejection Summary",
            report_with_inserted_line_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "- guaranteed profit",
            ),
            "prohibited runtime report content: guaranteed profit",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def report_without_line_containing(report_text, required_text):
    lines = report_text.splitlines()
    return "\n".join(line for line in lines if required_text not in line) + "\n"


def report_with_replaced_line(report_text, required_text, replacement):
    lines = report_text.splitlines()
    replaced_lines = [
        replacement if required_text in line else line
        for line in lines
    ]
    return "\n".join(replaced_lines) + "\n"


def report_without_line_containing_in_section(report_text, heading, required_text):
    lines = report_text.splitlines()
    filtered_lines = []
    in_section = False

    for line in lines:
        if line == heading:
            in_section = True
            filtered_lines.append(line)
            continue
        if in_section and line.startswith("## "):
            in_section = False

        if in_section and required_text in line:
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines) + "\n"


def report_with_replaced_line_in_section(report_text, heading, required_text, replacement):
    lines = report_text.splitlines()
    replaced_lines = []
    in_section = False

    for line in lines:
        if line == heading:
            in_section = True
            replaced_lines.append(line)
            continue
        if in_section and line.startswith("## "):
            in_section = False

        if in_section and required_text in line:
            replaced_lines.append(replacement)
        else:
            replaced_lines.append(line)

    return "\n".join(replaced_lines) + "\n"


def report_with_inserted_line_in_section(report_text, heading, inserted_line):
    lines = report_text.splitlines()
    updated_lines = []
    inserted = False

    for line in lines:
        updated_lines.append(line)
        if line == heading and not inserted:
            updated_lines.append(inserted_line)
            inserted = True

    return "\n".join(updated_lines) + "\n"


def report_with_swapped_headings(report_text, first_heading, second_heading):
    first_marker = "__TEMP_SWAPPED_HEADING__"
    lines = report_text.splitlines()
    swapped_lines = []

    for line in lines:
        if line == first_heading:
            swapped_lines.append(first_marker)
        elif line == second_heading:
            swapped_lines.append(first_heading)
        else:
            swapped_lines.append(line)

    swapped_lines = [
        second_heading if line == first_marker else line
        for line in swapped_lines
    ]
    return "\n".join(swapped_lines) + "\n"


def report_with_duplicate_heading(report_text, heading):
    return report_text.rstrip() + f"\n\n{heading}\n"


def report_with_unknown_section_at_end(report_text, heading, content=""):
    section_lines = ["", heading]
    if content:
        section_lines.extend(["", content])
    return report_text.rstrip() + "\n" + "\n".join(section_lines) + "\n"


def report_with_unknown_section_before(report_text, before_heading, unknown_heading):
    return report_text.replace(
        before_heading,
        f"{unknown_heading}\n\n{before_heading}",
        1,
    )


def report_without_missing_field_list(report_text):
    lines = report_text.splitlines()
    filtered_lines = []
    in_missing_fields = False
    for line in lines:
        if line == "- Missing fields:":
            in_missing_fields = True
            continue
        if in_missing_fields and line.startswith("  - "):
            continue
        in_missing_fields = False
        filtered_lines.append(line)
    return "\n".join(filtered_lines) + "\n"


def validate_negative_case(name, report_text, expected_missing):
    missing = write_temp_report_and_validate(report_text)
    if not missing:
        return f"{name} unexpectedly passed"
    if expected_missing not in "\n".join(missing):
        return f"{name} did not report expected missing item: {expected_missing}\nmissing: {missing}"
    return ""


def validate_missing_field_notes_negative_reports():
    sample_report = POSITIVE_REPORTS[0].read_text(encoding="utf-8")
    task_010_report = POSITIVE_REPORTS[1].read_text(encoding="utf-8")

    negative_cases = [
        (
            "missing Missing Field Notes section",
            report_without_line_containing(sample_report, "## Missing Field Notes"),
            "Missing Field Notes",
        ),
        (
            "missing Missing fields count",
            report_without_line_containing(sample_report, "Missing fields count:"),
            "Missing fields count",
        ),
        (
            "missing Not found source text explanation",
            report_without_line_containing(
                sample_report,
                "Not found means the field was not present in the parsed source text.",
            ),
            "Not found means the field was not present in the parsed source text.",
        ),
        (
            "missing Not found inferred explanation",
            report_without_line_containing(sample_report, "Not found values are not inferred."),
            "Not found values are not inferred.",
        ),
        (
            "missing Not found zero explanation",
            report_without_line_containing(sample_report, "Not found does not mean zero."),
            "Not found does not mean zero.",
        ),
        (
            "missing Not found failed explanation",
            report_without_line_containing(sample_report, "Not found does not mean the backtest failed."),
            "Not found does not mean the backtest failed.",
        ),
        (
            "missing parsed text only explanation",
            report_without_line_containing(sample_report, "Parser output is based on parsed text only."),
            "Parser output is based on parsed text only.",
        ),
        (
            "missing Not found field list",
            report_without_missing_field_list(task_010_report),
            "Missing Field Notes listed field name",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_missing_fields_count_negative_reports():
    negative_cases = [
        (
            "no Not found fields but nonzero Missing fields count",
            make_runtime_report([], missing_fields_count=1),
            "Missing fields count mismatch",
        ),
        (
            "two Not found fields but Missing fields count is one",
            make_runtime_report(["totalTicks", "newBarsDetected"], missing_fields_count=1),
            "Missing fields count mismatch",
        ),
        (
            "one Not found field but Missing fields count is zero",
            make_runtime_report(["totalTicks"], missing_fields_count=0),
            "Missing fields count mismatch",
        ),
        (
            "non-integer Missing fields count",
            make_runtime_report([], missing_fields_count="many"),
            "Missing fields count is not an integer",
        ),
        (
            "Not found fields without Missing Field Notes field list",
            make_runtime_report(["totalTicks"], include_missing_field_list=False),
            "Missing Field Notes listed field name",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_missing_fields_list_negative_reports():
    negative_cases = [
        (
            "two Not found fields but only one listed field",
            make_runtime_report(
                ["totalTicks", "newBarsDetected"],
                listed_fields=["totalTicks"],
            ),
            "Missing Field Notes missing field: newBarsDetected",
        ),
        (
            "one Not found field with extra unknown listed field",
            make_runtime_report(
                ["totalTicks"],
                listed_fields=["totalTicks", "unknownFutureField"],
            ),
            "Unknown Missing Field Notes field: unknownFutureField",
        ),
        (
            "no Not found fields but listed field exists",
            make_runtime_report([], listed_fields=["totalTicks"]),
            "Missing Field Notes unexpected field: totalTicks",
        ),
        (
            "Not found field listed with typo",
            make_runtime_report(["totalTicks"], listed_fields=["totalTick"]),
            "Unknown Missing Field Notes field: totalTick",
        ),
        (
            "correct count but incomplete field list",
            make_runtime_report(
                ["totalTicks", "newBarsDetected"],
                missing_fields_count=2,
                listed_fields=["totalTicks"],
            ),
            "Missing Field Notes missing field: newBarsDetected",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_field_coverage_negative_reports():
    no_missing_report = make_runtime_report([])
    missing_report = make_runtime_report(["totalTicks", "newBarsDetected"])

    negative_cases = [
        (
            "missing Field Coverage Summary section",
            report_without_line_containing(no_missing_report, "## Field Coverage Summary"),
            "Field Coverage Summary",
        ),
        (
            "missing Total runtime fields",
            report_without_line_containing(no_missing_report, "Total runtime fields:"),
            "Total runtime fields",
        ),
        (
            "missing Found runtime fields",
            report_without_line_containing(no_missing_report, "Found runtime fields:"),
            "Found runtime fields",
        ),
        (
            "missing Missing runtime fields",
            report_without_line_containing(no_missing_report, "Missing runtime fields:"),
            "Missing runtime fields",
        ),
        (
            "missing Missing field ratio",
            report_without_line_containing(no_missing_report, "Missing field ratio:"),
            "Missing field ratio",
        ),
        (
            "non-integer Total runtime fields",
            report_with_replaced_line(no_missing_report, "Total runtime fields:", "- Total runtime fields: many"),
            "Total runtime fields is not an integer",
        ),
        (
            "non-integer Missing runtime fields",
            report_with_replaced_line(no_missing_report, "Missing runtime fields:", "- Missing runtime fields: many"),
            "Missing runtime fields is not an integer",
        ),
        (
            "Missing field ratio is not a percentage",
            report_with_replaced_line(no_missing_report, "Missing field ratio:", "- Missing field ratio: many"),
            "Missing field ratio is not a percentage",
        ),
        (
            "total does not equal found plus missing",
            report_with_replaced_line(no_missing_report, "Found runtime fields:", "- Found runtime fields: 26"),
            "Field coverage total mismatch",
        ),
        (
            "missing count does not match actual Not found fields",
            report_with_replaced_line(missing_report, "Missing runtime fields:", "- Missing runtime fields: 1"),
            "Field coverage missing mismatch",
        ),
        (
            "missing ratio does not match missing over total",
            report_with_replaced_line(missing_report, "Missing field ratio:", "- Missing field ratio: 0.00%"),
            "Missing field ratio mismatch",
        ),
        (
            "missing section distribution line",
            report_without_line_containing(no_missing_report, "Runtime Summary Counters:"),
            "Field coverage section missing: Runtime Summary Counters",
        ),
        (
            "section distribution total does not match summary",
            report_with_replaced_line(
                no_missing_report,
                "Runtime Summary Counters:",
                "- Runtime Summary Counters: found 5 / missing 0",
            ),
            "Field coverage section totals mismatch",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_signal_observation_negative_reports():
    no_missing_report = make_runtime_report([])
    missing_report = make_runtime_report(
        [
            "signalsEvaluated",
            "buySignals",
            "sellSignals",
            "noneSignals",
            "signalDirectionChanges",
        ]
    )
    one_missing_report = make_runtime_report(["signalsEvaluated"])

    negative_cases = [
        (
            "missing Signal Observation Summary section",
            report_without_line_containing(no_missing_report, "## Signal Observation Summary"),
            "Signal Observation Summary",
        ),
        (
            "missing signalsEvaluated field in Signal Observation Summary",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "signalsEvaluated:",
            ),
            "Signal Observation Summary missing field: signalsEvaluated",
        ),
        (
            "missing Signal observation fields found",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "Signal observation fields found:",
            ),
            "Signal observation fields found",
        ),
        (
            "missing Signal observation fields missing",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "Signal observation fields missing:",
            ),
            "Signal observation fields missing",
        ),
        (
            "missing Missing signal observation fields",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "Missing signal observation fields",
            ),
            "Missing signal observation fields",
        ),
        (
            "missing observation-only safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "Signals are observation-only and are not trading instructions.",
            ),
            "Signals are observation-only and are not trading instructions.",
        ),
        (
            "Signal Observation Summary value does not match runtime summary",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "buySignals:",
                "- buySignals: 2",
            ),
            "Signal Observation Summary value mismatch: buySignals",
        ),
        (
            "Signal observation found count does not match actual fields",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Signal Observation Summary",
                "Signal observation fields found:",
                "- Signal observation fields found: 5",
            ),
            "Signal observation found mismatch",
        ),
        (
            "Signal observation missing count does not match actual fields",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Signal Observation Summary",
                "Signal observation fields missing:",
                "- Signal observation fields missing: 0",
            ),
            "Signal observation missing mismatch",
        ),
        (
            "no missing signal fields but missing list is not none",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Signal Observation Summary",
                "Missing signal observation fields:",
                "- Missing signal observation fields:\n  - signalsEvaluated",
            ),
            "Signal observation missing fields should be none",
        ),
        (
            "missing signal fields but one field omitted from list",
            report_without_line_containing_in_section(
                missing_report,
                "## Signal Observation Summary",
                "  - signalDirectionChanges",
            ),
            "Signal Observation missing field: signalDirectionChanges",
        ),
        (
            "missing signal fields list includes unknown field",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Signal Observation Summary",
                "  - signalsEvaluated",
                "  - signalsEvaluated\n  - unexpectedSignalField",
            ),
            "Unknown Signal Observation missing field: unexpectedSignalField",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_risk_rejection_negative_reports():
    no_missing_report = make_runtime_report([])
    missing_report = make_runtime_report(
        [
            "riskRejected",
            "totalRiskRejects",
            "riskRejectSignalNone",
            "riskRejectTradingDisabled",
            "riskRejectInvalidPrice",
            "riskRejectSpreadTooHigh",
            "riskRejectTimeBlocked",
            "riskRejectMaxPositions",
            "riskRejectObservationMode",
        ]
    )
    one_missing_report = make_runtime_report(["riskRejected"])

    negative_cases = [
        (
            "missing Risk Rejection Summary section",
            report_without_line_containing(no_missing_report, "## Risk Rejection Summary"),
            "Risk Rejection Summary",
        ),
        (
            "missing riskRejected field in Risk Rejection Summary",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "riskRejected:",
            ),
            "Risk Rejection Summary missing field: riskRejected",
        ),
        (
            "missing totalRiskRejects field in Risk Rejection Summary",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "totalRiskRejects:",
            ),
            "Risk Rejection Summary missing field: totalRiskRejects",
        ),
        (
            "missing Risk rejection fields found",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Risk rejection fields found:",
            ),
            "Risk rejection fields found",
        ),
        (
            "missing Risk rejection fields missing",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Risk rejection fields missing:",
            ),
            "Risk rejection fields missing",
        ),
        (
            "missing Missing risk rejection fields",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Missing risk rejection fields",
            ),
            "Missing risk rejection fields",
        ),
        (
            "missing parsed from source text only safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Risk rejection values are parsed from source text only.",
            ),
            "Risk rejection values are parsed from source text only.",
        ),
        (
            "missing not inferred safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Not found risk rejection fields are not inferred.",
            ),
            "Not found risk rejection fields are not inferred.",
        ),
        (
            "missing no real trading safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Risk rejection summary does not enable real trading.",
            ),
            "Risk rejection summary does not enable real trading.",
        ),
        (
            "missing RiskManager safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "RiskManager must not be bypassed.",
            ),
            "RiskManager must not be bypassed.",
        ),
        (
            "Risk Rejection Summary value does not match runtime summary",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "riskRejected:",
                "- riskRejected: 2",
            ),
            "Risk Rejection Summary value mismatch: riskRejected",
        ),
        (
            "Risk rejection found count does not match actual fields",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Risk Rejection Summary",
                "Risk rejection fields found:",
                "- Risk rejection fields found: 10",
            ),
            "Risk rejection found mismatch",
        ),
        (
            "Risk rejection missing count does not match actual fields",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Risk Rejection Summary",
                "Risk rejection fields missing:",
                "- Risk rejection fields missing: 0",
            ),
            "Risk rejection missing mismatch",
        ),
        (
            "no missing risk rejection fields but missing list is not none",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Risk Rejection Summary",
                "Missing risk rejection fields:",
                "- Missing risk rejection fields:\n  - riskRejected",
            ),
            "Risk rejection missing fields should be none",
        ),
        (
            "missing risk rejection fields but one field omitted from list",
            report_without_line_containing_in_section(
                missing_report,
                "## Risk Rejection Summary",
                "  - riskRejectObservationMode",
            ),
            "Risk Rejection missing field: riskRejectObservationMode",
        ),
        (
            "missing risk rejection fields list includes unknown field",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Risk Rejection Summary",
                "  - riskRejected",
                "  - riskRejected\n  - unexpectedRiskField",
            ),
            "Unknown Risk Rejection missing field: unexpectedRiskField",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def validate_log_throttle_negative_reports():
    no_missing_report = make_runtime_report([])
    missing_report = make_runtime_report(
        [
            "printedRiskRejectLogs",
            "suppressedRiskRejectLogs",
        ]
    )
    one_missing_report = make_runtime_report(["printedRiskRejectLogs"])

    negative_cases = [
        (
            "missing Log Throttle Summary section",
            report_without_line_containing(no_missing_report, "## Log Throttle Summary"),
            "Log Throttle Summary",
        ),
        (
            "missing printedRiskRejectLogs field in Log Throttle Summary",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "printedRiskRejectLogs:",
            ),
            "Log Throttle Summary missing field: printedRiskRejectLogs",
        ),
        (
            "missing totalNewBarLogEvents field in Log Throttle Summary",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "totalNewBarLogEvents:",
            ),
            "Log Throttle Summary missing field: totalNewBarLogEvents",
        ),
        (
            "missing totalSignalLogEvents field in Log Throttle Summary",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "totalSignalLogEvents:",
            ),
            "Log Throttle Summary missing field: totalSignalLogEvents",
        ),
        (
            "missing Risk reject log print ratio",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Risk reject log print ratio:",
            ),
            "Risk reject log print ratio",
        ),
        (
            "missing New bar log print ratio",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "New bar log print ratio:",
            ),
            "New bar log print ratio",
        ),
        (
            "missing Signal log print ratio",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Signal log print ratio:",
            ),
            "Signal log print ratio",
        ),
        (
            "missing Log throttle fields found",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Log throttle fields found:",
            ),
            "Log throttle fields found",
        ),
        (
            "missing Log throttle fields missing",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Log throttle fields missing:",
            ),
            "Log throttle fields missing",
        ),
        (
            "missing Missing log throttle fields",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Missing log throttle fields",
            ),
            "Missing log throttle fields",
        ),
        (
            "missing parsed from source text only safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Log throttle values are parsed from source text only.",
            ),
            "Log throttle values are parsed from source text only.",
        ),
        (
            "missing not inferred safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Not found log throttle fields are not inferred.",
            ),
            "Not found log throttle fields are not inferred.",
        ),
        (
            "missing no real trading safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Log throttle summary does not enable real trading.",
            ),
            "Log throttle summary does not enable real trading.",
        ),
        (
            "missing reporting metrics safety statement",
            report_without_line_containing_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Log throttle ratios are reporting metrics, not trading signals.",
            ),
            "Log throttle ratios are reporting metrics, not trading signals.",
        ),
        (
            "Log Throttle Summary value does not match runtime summary",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "printedSignalLogs:",
                "- printedSignalLogs: 2",
            ),
            "Log Throttle Summary value mismatch: printedSignalLogs",
        ),
        (
            "Risk reject log print ratio does not match printed over suppressed",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Risk reject log print ratio:",
                "- Risk reject log print ratio: 0.00%",
            ),
            "Risk reject log print ratio mismatch",
        ),
        (
            "New bar log print ratio does not match printed over total",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "New bar log print ratio:",
                "- New bar log print ratio: 0.00%",
            ),
            "New bar log print ratio mismatch",
        ),
        (
            "Signal log print ratio does not match printed over total",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Signal log print ratio:",
                "- Signal log print ratio: 0.00%",
            ),
            "Signal log print ratio mismatch",
        ),
        (
            "Log throttle found count does not match actual fields",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Log Throttle Summary",
                "Log throttle fields found:",
                "- Log throttle fields found: 8",
            ),
            "Log throttle found mismatch",
        ),
        (
            "Log throttle missing count does not match actual fields",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Log Throttle Summary",
                "Log throttle fields missing:",
                "- Log throttle fields missing: 0",
            ),
            "Log throttle missing mismatch",
        ),
        (
            "no missing log throttle fields but missing list is not none",
            report_with_replaced_line_in_section(
                no_missing_report,
                "## Log Throttle Summary",
                "Missing log throttle fields:",
                "- Missing log throttle fields:\n  - printedRiskRejectLogs",
            ),
            "Log throttle missing fields should be none",
        ),
        (
            "missing log throttle fields but one field omitted from list",
            report_without_line_containing_in_section(
                missing_report,
                "## Log Throttle Summary",
                "  - suppressedRiskRejectLogs",
            ),
            "Log Throttle missing field: suppressedRiskRejectLogs",
        ),
        (
            "missing log throttle fields list includes unknown field",
            report_with_replaced_line_in_section(
                one_missing_report,
                "## Log Throttle Summary",
                "  - printedRiskRejectLogs",
                "  - printedRiskRejectLogs\n  - unexpectedLogField",
            ),
            "Unknown Log Throttle missing field: unexpectedLogField",
        ),
    ]

    for name, report_text, expected_missing in negative_cases:
        error = validate_negative_case(name, report_text, expected_missing)
        if error:
            return error

    return ""


def main():
    for check in (
        validate_required_files,
        validate_positive_reports,
        validate_invalid_report,
        validate_section_order_negative_reports,
        validate_allowed_safety_content,
        validate_prohibited_content_negative_reports,
        validate_missing_field_notes_negative_reports,
        validate_missing_fields_count_negative_reports,
        validate_missing_fields_list_negative_reports,
        validate_field_coverage_negative_reports,
        validate_signal_observation_negative_reports,
        validate_risk_rejection_negative_reports,
        validate_log_throttle_negative_reports,
    ):
        error = check()
        if error:
            return fail(error)

    print("Backtest runtime report validator self-test passed")
    print("Self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
