import argparse
import json
import re
import sys
from pathlib import Path


COUNTER_FIELDS = [
    "totalTicks",
    "newBarsDetected",
    "signalsEvaluated",
    "riskRejected",
    "riskApproved",
    "executionAttempts",
]

SIGNAL_FIELDS = [
    "buySignals",
    "sellSignals",
    "noneSignals",
    "signalDirectionChanges",
]

RISK_REJECT_FIELDS = [
    "riskRejectSignalNone",
    "riskRejectTradingDisabled",
    "riskRejectInvalidPrice",
    "riskRejectSpreadTooHigh",
    "riskRejectTimeBlocked",
    "riskRejectMaxPositions",
    "riskRejectObservationMode",
    "totalRiskRejects",
]

RISK_LOG_FIELDS = [
    "printedRiskRejectLogs",
    "suppressedRiskRejectLogs",
]

CORE_LOG_FIELDS = [
    "totalNewBarLogEvents",
    "printedNewBarLogs",
    "suppressedNewBarLogs",
]

SIGNAL_LOG_FIELDS = [
    "totalSignalLogEvents",
    "printedSignalLogs",
    "suppressedSignalLogs",
]

ALL_FIELDS = (
    COUNTER_FIELDS
    + SIGNAL_FIELDS
    + RISK_REJECT_FIELDS
    + RISK_LOG_FIELDS
    + CORE_LOG_FIELDS
    + SIGNAL_LOG_FIELDS
)

NOT_FOUND = "Not found"

SECTION_FIELDS = [
    ("Runtime Summary Counters", COUNTER_FIELDS),
    ("Runtime Summary Signal Stats", SIGNAL_FIELDS),
    ("Runtime Summary Risk Reject Stats", RISK_REJECT_FIELDS),
    ("Runtime Summary Risk Log Stats", RISK_LOG_FIELDS),
    ("Runtime Summary Core / New Bar Log Stats", CORE_LOG_FIELDS),
    ("Runtime Summary Signal Log Stats", SIGNAL_LOG_FIELDS),
    ("Final Balance", ["finalBalance"]),
]

SIGNAL_OBSERVATION_FIELDS = [
    "signalsEvaluated",
    "buySignals",
    "sellSignals",
    "noneSignals",
    "signalDirectionChanges",
]

RISK_REJECTION_SUMMARY_FIELDS = [
    "riskRejected",
    "riskApproved",
    "totalRiskRejects",
    "riskRejectSignalNone",
    "riskRejectTradingDisabled",
    "riskRejectInvalidPrice",
    "riskRejectSpreadTooHigh",
    "riskRejectTimeBlocked",
    "riskRejectMaxPositions",
    "riskRejectObservationMode",
]

LOG_THROTTLE_SUMMARY_FIELDS = [
    "printedRiskRejectLogs",
    "suppressedRiskRejectLogs",
    "totalNewBarLogEvents",
    "printedNewBarLogs",
    "suppressedNewBarLogs",
    "totalSignalLogEvents",
    "printedSignalLogs",
    "suppressedSignalLogs",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parse MT5 Runtime summary text into markdown or JSON metadata."
    )
    parser.add_argument("--input", required=True, help="Input text file")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Defaults to markdown.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output when --format json is used.",
    )
    return parser.parse_args()


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def extract_field(text, field):
    pattern = re.compile(
        r"(?:^|[\s,\|\-])"
        + re.escape(field)
        + r"\s*(?:=|:)\s*([^,\|\r\n]+)",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    if match is None:
        return NOT_FOUND
    return match.group(1).strip()


def extract_final_balance(text):
    patterns = [
        re.compile(
            r"(?:^|[\s,\|\-])finalBalance\s*(?:=|:)\s*([^,\|\r\n]+)",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"(?:^|[\s,\|\-])final\s+balance\s*(?:=|:)\s*([^,\|\r\n]+)",
            re.IGNORECASE | re.MULTILINE,
        ),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match is not None:
            return match.group(1).strip()
    return NOT_FOUND


def parse_runtime_summary(text):
    parsed = {field: extract_field(text, field) for field in ALL_FIELDS}
    parsed["finalBalance"] = extract_final_balance(text)
    return parsed


def render_field(field, parsed):
    return f"- {field}: {parsed.get(field, NOT_FOUND)}"


def render_section(title, fields, parsed):
    lines = [f"## {title}"]
    lines.extend(render_field(field, parsed) for field in fields)
    return "\n".join(lines)


def render_missing_field_notes(parsed):
    missing_fields = [field for field in ALL_FIELDS if parsed.get(field, NOT_FOUND) == NOT_FOUND]
    lines = [
        "## Missing Field Notes",
        f"- Missing fields count: {len(missing_fields)}",
        "- Missing fields are reported as Not found.",
        "- Not found means the field was not present in the parsed source text.",
        "- Not found values are not inferred.",
        "- Not found does not mean zero.",
        "- Not found does not mean the backtest failed.",
        "- Parser output is based on parsed text only.",
    ]
    if missing_fields:
        lines.append("- Missing fields:")
        lines.extend(f"  - {field}" for field in missing_fields)
    return "\n".join(lines)


def count_found_missing(fields, parsed):
    found = 0
    missing = 0
    for field in fields:
        if parsed.get(field, NOT_FOUND) == NOT_FOUND:
            missing += 1
        else:
            found += 1
    return found, missing


def parse_non_negative_int(value):
    if value == NOT_FOUND:
        return None
    if not re.fullmatch(r"\d+", value):
        return None
    return int(value)


def format_ratio(numerator, denominator):
    if numerator is None or denominator is None:
        return NOT_FOUND
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator * 100):.2f}%"


def render_field_coverage_summary(parsed):
    total_fields = sum(len(fields) for _, fields in SECTION_FIELDS)
    missing_fields = sum(
        1
        for _, fields in SECTION_FIELDS
        for field in fields
        if parsed.get(field, NOT_FOUND) == NOT_FOUND
    )
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

    for section_title, fields in SECTION_FIELDS:
        found, missing = count_found_missing(fields, parsed)
        lines.append(f"- {section_title}: found {found} / missing {missing}")

    return "\n".join(lines)


def render_signal_observation_summary(parsed):
    missing_fields = [
        field
        for field in SIGNAL_OBSERVATION_FIELDS
        if parsed.get(field, NOT_FOUND) == NOT_FOUND
    ]
    found_fields = len(SIGNAL_OBSERVATION_FIELDS) - len(missing_fields)

    lines = [
        "## Signal Observation Summary",
        render_field("signalsEvaluated", parsed),
        render_field("buySignals", parsed),
        render_field("sellSignals", parsed),
        render_field("noneSignals", parsed),
        render_field("signalDirectionChanges", parsed),
        f"- Signal observation fields found: {found_fields}",
        f"- Signal observation fields missing: {len(missing_fields)}",
    ]
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
    return "\n".join(lines)


def render_risk_rejection_summary(parsed):
    missing_fields = [
        field
        for field in RISK_REJECTION_SUMMARY_FIELDS
        if parsed.get(field, NOT_FOUND) == NOT_FOUND
    ]
    found_fields = len(RISK_REJECTION_SUMMARY_FIELDS) - len(missing_fields)

    lines = [
        "## Risk Rejection Summary",
        render_field("riskRejected", parsed),
        render_field("riskApproved", parsed),
        render_field("totalRiskRejects", parsed),
        render_field("riskRejectSignalNone", parsed),
        render_field("riskRejectTradingDisabled", parsed),
        render_field("riskRejectInvalidPrice", parsed),
        render_field("riskRejectSpreadTooHigh", parsed),
        render_field("riskRejectTimeBlocked", parsed),
        render_field("riskRejectMaxPositions", parsed),
        render_field("riskRejectObservationMode", parsed),
        f"- Risk rejection fields found: {found_fields}",
        f"- Risk rejection fields missing: {len(missing_fields)}",
    ]
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
    return "\n".join(lines)


def render_log_throttle_summary(parsed):
    missing_fields = [
        field
        for field in LOG_THROTTLE_SUMMARY_FIELDS
        if parsed.get(field, NOT_FOUND) == NOT_FOUND
    ]
    found_fields = len(LOG_THROTTLE_SUMMARY_FIELDS) - len(missing_fields)

    printed_risk_reject_logs = parse_non_negative_int(
        parsed.get("printedRiskRejectLogs", NOT_FOUND)
    )
    suppressed_risk_reject_logs = parse_non_negative_int(
        parsed.get("suppressedRiskRejectLogs", NOT_FOUND)
    )
    risk_reject_total = None
    if printed_risk_reject_logs is not None and suppressed_risk_reject_logs is not None:
        risk_reject_total = printed_risk_reject_logs + suppressed_risk_reject_logs

    total_new_bar_events = parse_non_negative_int(
        parsed.get("totalNewBarLogEvents", NOT_FOUND)
    )
    printed_new_bar_logs = parse_non_negative_int(
        parsed.get("printedNewBarLogs", NOT_FOUND)
    )
    total_signal_events = parse_non_negative_int(
        parsed.get("totalSignalLogEvents", NOT_FOUND)
    )
    printed_signal_logs = parse_non_negative_int(
        parsed.get("printedSignalLogs", NOT_FOUND)
    )

    lines = [
        "## Log Throttle Summary",
        render_field("printedRiskRejectLogs", parsed),
        render_field("suppressedRiskRejectLogs", parsed),
        render_field("totalNewBarLogEvents", parsed),
        render_field("printedNewBarLogs", parsed),
        render_field("suppressedNewBarLogs", parsed),
        render_field("totalSignalLogEvents", parsed),
        render_field("printedSignalLogs", parsed),
        render_field("suppressedSignalLogs", parsed),
        f"- Risk reject log print ratio: {format_ratio(printed_risk_reject_logs, risk_reject_total)}",
        f"- New bar log print ratio: {format_ratio(printed_new_bar_logs, total_new_bar_events)}",
        f"- Signal log print ratio: {format_ratio(printed_signal_logs, total_signal_events)}",
        f"- Log throttle fields found: {found_fields}",
        f"- Log throttle fields missing: {len(missing_fields)}",
    ]
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
    return "\n".join(lines)


def build_field_coverage(parsed):
    total_fields = sum(len(fields) for _, fields in SECTION_FIELDS)
    missing_fields = [
        field
        for _, fields in SECTION_FIELDS
        for field in fields
        if parsed.get(field, NOT_FOUND) == NOT_FOUND
    ]
    found_fields = total_fields - len(missing_fields)
    missing_ratio = (len(missing_fields) / total_fields * 100) if total_fields else 0.0
    sections = {}
    for section_title, fields in SECTION_FIELDS:
        found, missing = count_found_missing(fields, parsed)
        sections[section_title] = {
            "found": found,
            "missing": missing,
        }
    return {
        "totalFields": total_fields,
        "foundFields": found_fields,
        "missingFields": len(missing_fields),
        "missingFieldRatioPercent": round(missing_ratio, 2),
        "missingFieldNames": missing_fields,
        "sections": sections,
    }


def build_json_payload(input_file, parsed):
    return {
        "sourceFile": input_file,
        "reportType": "runtime_summary_metadata",
        "generatedBy": "tools/parse_backtest_runtime_summary.py",
        "fields": parsed,
        "fieldCoverage": build_field_coverage(parsed),
        "safetyNotes": [
            "parsed runtime summary is metadata only",
            "not live trading readiness",
            "not real trading permission",
            "not profitability claim",
            "Not found values are not inferred",
            "RiskManager must not be bypassed",
        ],
    }


def render_markdown(input_file, parsed):
    sections = [
        "# Backtest Runtime Summary Draft",
        "## Report Metadata",
        "- Report Type: Draft / 草稿",
        f"- Source File: {input_file}",
        "- Generated By: tools/parse_backtest_runtime_summary.py",
        render_section("Runtime Summary Counters", COUNTER_FIELDS, parsed),
        render_section("Runtime Summary Signal Stats", SIGNAL_FIELDS, parsed),
        render_section("Runtime Summary Risk Reject Stats", RISK_REJECT_FIELDS, parsed),
        render_section("Runtime Summary Risk Log Stats", RISK_LOG_FIELDS, parsed),
        render_section("Runtime Summary Core / New Bar Log Stats", CORE_LOG_FIELDS, parsed),
        render_section("Runtime Summary Signal Log Stats", SIGNAL_LOG_FIELDS, parsed),
        "## Final Balance",
        render_field("finalBalance", parsed),
        render_field_coverage_summary(parsed),
        render_signal_observation_summary(parsed),
        render_risk_rejection_summary(parsed),
        render_log_throttle_summary(parsed),
        render_missing_field_notes(parsed),
        "## Safety Notes",
        "- This is a draft generated from parsed text only.",
        "- The current system is not allowed to perform real trading.",
        "- EMA signals are observation-only and are not a production trading strategy.",
        "- RiskManager must not be bypassed.",
        "- ExecutionManager must not execute real orders in the current stage.",
        "- Missing fields are reported as Not found and are not inferred.",
    ]
    return "\n\n".join(sections) + "\n"


def write_text(path, text):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    source_text = read_text(input_path)
    parsed = parse_runtime_summary(source_text)

    if args.format == "json":
        payload = build_json_payload(str(input_path), parsed)
        rendered = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            if args.pretty
            else json.dumps(payload, ensure_ascii=False, sort_keys=True)
        )
        if args.output:
            write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0

    if not args.output:
        print("Output path is required for markdown format", file=sys.stderr)
        return 1

    markdown = render_markdown(args.input, parsed)
    write_text(args.output, markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
