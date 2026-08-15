#!/usr/bin/env python3
"""Validate static MQ5 safety guardrails without modifying project files."""

from pathlib import Path
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
MQ5_DIR = ROOT_DIR / "mq5"

SOURCE_PATTERNS = ("*.mq5", "*.mqh")

FORBIDDEN_CODE_PATTERNS = [
    ("CTrade", re.compile(r"\bCTrade\b")),
    ("OrderSend", re.compile(r"\bOrderSend\b")),
    ("PositionOpen", re.compile(r"\bPositionOpen\b")),
    ("OrderModify", re.compile(r"\bOrderModify\b")),
    ("PositionClose", re.compile(r"\bPositionClose\b")),
    ("OrderClose", re.compile(r"\bOrderClose\b")),
    ("trade.", re.compile(r"\btrade\s*\.")),
    ("m_trade", re.compile(r"\bm_trade\b")),
    ("OrderCalc", re.compile(r"\bOrderCalc[A-Za-z0-9_]*\b")),
    ("OrderCheck", re.compile(r"\bOrderCheck\b")),
    ("Buy(", re.compile(r"(?<![A-Za-z0-9_\.])Buy\s*\(")),
    ("Sell(", re.compile(r"(?<![A-Za-z0-9_\.])Sell\s*\(")),
    (".Buy(", re.compile(r"\.\s*Buy\s*\(")),
    (".Sell(", re.compile(r"\.\s*Sell\s*\(")),
]

FORBIDDEN_STRATEGY_PATTERNS = [
    ("Grid", re.compile(r"\bGrid\b", re.IGNORECASE)),
    ("Martingale", re.compile(r"\bMartingale\b", re.IGNORECASE)),
    ("Averaging", re.compile(r"\bAveraging\b", re.IGNORECASE)),
    ("ATR", re.compile(r"\bATR\b", re.IGNORECASE)),
    ("StopLoss", re.compile(r"\bStopLoss\b", re.IGNORECASE)),
    ("TakeProfit", re.compile(r"\bTakeProfit\b", re.IGNORECASE)),
    ("LotSize", re.compile(r"\bLotSize\b", re.IGNORECASE)),
    ("Lots", re.compile(r"\bLots\b", re.IGNORECASE)),
    ("PositionSizing", re.compile(r"\bPositionSizing\b", re.IGNORECASE)),
    ("RiskPercent", re.compile(r"\bRiskPercent\b", re.IGNORECASE)),
]

FORBIDDEN_INCLUDE_PATTERNS = [
    (
        "#include <Trade/Trade.mqh>",
        re.compile(r"#\s*include\s*<\s*Trade/Trade\.mqh\s*>", re.IGNORECASE),
    ),
    (
        '#include "Trade/Trade.mqh"',
        re.compile(r'#\s*include\s*"Trade/Trade\.mqh"', re.IGNORECASE),
    ),
]

TRADING_INPUT_PATTERN = re.compile(
    r"\b(?:input|extern)\s+bool\s+InpEnableTrading\s*=\s*(true|false)\b",
    re.IGNORECASE,
)
TRADING_NAME_PATTERN = re.compile(r"\bInpEnableTrading\b")

EXECUTION_MANAGER_PATH = MQ5_DIR / "execution" / "ExecutionManager.mqh"
EA_CONTROLLER_PATH = MQ5_DIR / "core" / "EaController.mqh"
RISK_MANAGER_PATH = MQ5_DIR / "risk" / "RiskManager.mqh"
SIGNAL_ENGINE_PATH = MQ5_DIR / "signals" / "SignalEngine.mqh"


def relative_path(path):
    return path.relative_to(ROOT_DIR).as_posix()


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="replace")


def strip_comments(text):
    output = []
    index = 0
    in_block_comment = False

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_block_comment:
            if char == "*" and next_char == "/":
                output.extend((" ", " "))
                index += 2
                in_block_comment = False
                continue
            output.append("\n" if char == "\n" else " ")
            index += 1
            continue

        if char == "/" and next_char == "*":
            output.extend((" ", " "))
            index += 2
            in_block_comment = True
            continue

        if char == "/" and next_char == "/":
            output.extend((" ", " "))
            index += 2
            while index < len(text) and text[index] != "\n":
                output.append(" ")
                index += 1
            continue

        output.append(char)
        index += 1

    return "".join(output)


def strip_strings(text):
    output = []
    index = 0
    in_string = None

    while index < len(text):
        char = text[index]

        if in_string:
            if char == "\\" and index + 1 < len(text):
                output.extend((" ", " "))
                index += 2
                continue
            if char == in_string:
                output.append(" ")
                index += 1
                in_string = None
                continue
            output.append("\n" if char == "\n" else " ")
            index += 1
            continue

        if char in ("'", '"'):
            output.append(" ")
            index += 1
            in_string = char
            continue

        output.append(char)
        index += 1

    return "".join(output)


def line_at(lines, line_number):
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def find_forbidden_apis(path, original_text, code_without_comments, stripped_code):
    findings = []
    original_lines = original_text.splitlines()

    for line_number, line in enumerate(code_without_comments.splitlines(), start=1):
        for label, pattern in FORBIDDEN_INCLUDE_PATTERNS:
            if pattern.search(line):
                findings.append(
                    {
                        "path": relative_path(path),
                        "line": line_number,
                        "item": label,
                        "summary": line_at(original_lines, line_number),
                    }
                )

    for line_number, line in enumerate(stripped_code.splitlines(), start=1):
        for label, pattern in FORBIDDEN_CODE_PATTERNS:
            if pattern.search(line):
                findings.append(
                    {
                        "path": relative_path(path),
                        "line": line_number,
                        "item": label,
                        "summary": line_at(original_lines, line_number),
                    }
                )

    return findings


def find_forbidden_strategy_keywords(path, original_text, stripped_code):
    findings = []
    original_lines = original_text.splitlines()

    for line_number, line in enumerate(stripped_code.splitlines(), start=1):
        for label, pattern in FORBIDDEN_STRATEGY_PATTERNS:
            if pattern.search(line):
                findings.append(
                    {
                        "path": relative_path(path),
                        "line": line_number,
                        "item": label,
                        "summary": line_at(original_lines, line_number),
                    }
                )

    return findings


def extract_function_body(stripped_code, function_name):
    match = re.search(r"\b" + re.escape(function_name) + r"\s*\(", stripped_code)
    if not match:
        return None

    brace_start = stripped_code.find("{", match.end())
    if brace_start < 0:
        return None

    depth = 0
    for index in range(brace_start, len(stripped_code)):
        char = stripped_code[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped_code[brace_start : index + 1]

    return None


def extract_braced_block(stripped_code, brace_start):
    if brace_start < 0 or brace_start >= len(stripped_code) or stripped_code[brace_start] != "{":
        return None

    depth = 0
    for index in range(brace_start, len(stripped_code)):
        char = stripped_code[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped_code[brace_start : index + 1]

    return None


def collect_trading_input_status(path, stripped_code):
    definitions = []
    name_occurrences = []

    for line_number, line in enumerate(stripped_code.splitlines(), start=1):
        if TRADING_NAME_PATTERN.search(line):
            name_occurrences.append((path, line_number, line.strip()))

        match = TRADING_INPUT_PATTERN.search(line)
        if match:
            definitions.append(
                {
                    "path": relative_path(path),
                    "line": line_number,
                    "default": match.group(1).lower(),
                    "summary": line.strip(),
                }
            )

    return definitions, name_occurrences


def require_file(path, issues, description):
    if not path.exists():
        issues.append(f"{description} file not found: {relative_path(path)}")
        return False
    return True


def validate_execution_manager(issues):
    if not require_file(EXECUTION_MANAGER_PATH, issues, "ExecutionManager"):
        return

    original_text = read_text(EXECUTION_MANAGER_PATH)
    code_without_comments = strip_comments(original_text)
    stripped_code = strip_strings(code_without_comments)
    body = extract_function_body(stripped_code, "ExecuteSignal")

    if body is None:
        issues.append("execution no-trade guard missing: ExecutionManager.ExecuteSignal() not found")
        return

    if re.search(r"\breturn\s+true\s*;", stripped_code):
        issues.append("execution no-trade guard failed: ExecutionManager must not return true")

    if not re.search(r"\breturn\s+false\s*;", body):
        issues.append("execution no-trade guard missing: ExecuteSignal() must return false")

    if re.search(r"\breturn\s+true\s*;", body):
        issues.append("execution no-trade guard failed: ExecuteSignal() must not return true")

    if "InpEnableTrading" not in body:
        issues.append(
            "execution InpEnableTrading disabled guard missing: "
            "ExecutionManager.ExecuteSignal() must check InpEnableTrading for no-trade safety"
        )
    elif not re.search(r"!\s*InpEnableTrading", body):
        issues.append(
            "execution InpEnableTrading disabled guard missing: "
            "ExecutionManager.ExecuteSignal() must explicitly block when InpEnableTrading is false"
        )
    else:
        disabled_guard = re.search(r"if\s*\(\s*!\s*InpEnableTrading\s*\)", body)
        guard_body = None
        if disabled_guard:
            brace_start = body.find("{", disabled_guard.end())
            guard_body = extract_braced_block(body, brace_start)

        if guard_body is None or not re.search(r"\breturn\s+false\s*;", guard_body):
            issues.append(
                "execution InpEnableTrading disabled guard invalid: "
                "no-trade disabled guard must return false"
            )

    log_text = code_without_comments.lower()
    if not (
        "execution disabled" in log_text
        or "execution skipped" in log_text
        or "skipped" in log_text
        or "disabled" in log_text
    ):
        issues.append(
            "execution no-trade guard missing: ExecutionManager must keep disabled/skipped log semantics"
        )


def validate_ea_controller_call_chain(issues):
    if not require_file(EA_CONTROLLER_PATH, issues, "EaController"):
        return

    original_text = read_text(EA_CONTROLLER_PATH)
    stripped_code = strip_strings(strip_comments(original_text))

    signal_index = stripped_code.find("signalEngine.Evaluate")
    risk_index = stripped_code.find("riskManager.CanExecuteSignal")
    execution_index = stripped_code.find("executionManager.ExecuteSignal")

    if signal_index < 0:
        issues.append("risk gate call-chain missing: SignalEngine.Evaluate() not found in EaController")

    if risk_index < 0:
        issues.append("risk gate call-chain missing: RiskManager.CanExecuteSignal(...) not found in EaController")

    if execution_index < 0:
        issues.append("risk gate call-chain missing: ExecutionManager.ExecuteSignal(...) not found in EaController")

    if risk_index >= 0 and execution_index >= 0 and execution_index < risk_index:
        issues.append(
            "risk gate call-chain order invalid: ExecutionManager.ExecuteSignal() appears before RiskManager.CanExecuteSignal()"
        )


def validate_risk_manager_guardrails(issues):
    if not require_file(RISK_MANAGER_PATH, issues, "RiskManager"):
        return

    original_text = read_text(RISK_MANAGER_PATH)
    code_without_comments = strip_comments(original_text)
    stripped_code = strip_strings(code_without_comments)
    body = extract_function_body(stripped_code, "CanExecuteSignal")

    if body is None:
        issues.append("risk gate missing: RiskManager.CanExecuteSignal() not found")
        return

    if "InpEnableTrading" not in body or not re.search(r"!\s*InpEnableTrading", body):
        issues.append("risk gate missing: InpEnableTrading=false blocking not found in CanExecuteSignal()")

    if "RISK_REJECT_TRADING_DISABLED" not in stripped_code:
        issues.append("risk gate missing: RISK_REJECT_TRADING_DISABLED not found")

    observation_checks = [
        "RISK_REJECT_OBSERVATION_MODE" in body,
        "real trading remains blocked" in code_without_comments.lower(),
        bool(re.search(r"\breturn\s+false\s*;", body)),
    ]
    if not all(observation_checks):
        issues.append(
            "observation mode fallback missing: RiskManager must reject with RISK_REJECT_OBSERVATION_MODE and return false"
        )


def validate_signal_engine_guardrails(issues):
    if not require_file(SIGNAL_ENGINE_PATH, issues, "SignalEngine"):
        return

    original_text = read_text(SIGNAL_ENGINE_PATH)
    code_without_comments = strip_comments(original_text)
    stripped_code = strip_strings(code_without_comments)
    findings = find_forbidden_apis(
        SIGNAL_ENGINE_PATH,
        original_text,
        code_without_comments,
        stripped_code,
    )

    for finding in findings:
        issues.append(
            "SignalEngine forbidden trading API found: "
            f"{finding['item']} at {finding['path']}:{finding['line']} "
            f"| {finding['summary']}"
        )


def discover_source_files():
    if not MQ5_DIR.exists():
        return None

    files = []
    for pattern in SOURCE_PATTERNS:
        files.extend(MQ5_DIR.rglob(pattern))

    return sorted(path for path in files if path.is_file())


def validate_sources(source_files):
    issues = []
    forbidden_findings = []
    forbidden_strategy_findings = []
    trading_definitions = []
    trading_occurrences = []

    for path in source_files:
        original_text = read_text(path)
        code_without_comments = strip_comments(original_text)
        stripped_code = strip_strings(code_without_comments)

        forbidden_findings.extend(
            find_forbidden_apis(path, original_text, code_without_comments, stripped_code)
        )
        forbidden_strategy_findings.extend(
            find_forbidden_strategy_keywords(path, original_text, stripped_code)
        )
        definitions, occurrences = collect_trading_input_status(path, stripped_code)
        trading_definitions.extend(definitions)
        trading_occurrences.extend(occurrences)

    if forbidden_findings:
        for finding in forbidden_findings:
            issues.append(
                "forbidden API found: "
                f"{finding['item']} at {finding['path']}:{finding['line']} "
                f"| {finding['summary']}"
                )

    if forbidden_strategy_findings:
        for finding in forbidden_strategy_findings:
            issues.append(
                "dangerous strategy keyword found: "
                f"{finding['item']} at {finding['path']}:{finding['line']} "
                f"| {finding['summary']}"
            )

    if not trading_occurrences:
        issues.append("InpEnableTrading not found")
    elif not trading_definitions:
        first_path, first_line, first_summary = trading_occurrences[0]
        issues.append(
            "InpEnableTrading default is not false or cannot be determined: "
            f"{relative_path(first_path)}:{first_line} | {first_summary}"
        )
    else:
        for definition in trading_definitions:
            if definition["default"] != "false":
                issues.append(
                    "InpEnableTrading default is not false: "
                    f"{definition['path']}:{definition['line']} | {definition['summary']}"
                )

    validate_execution_manager(issues)
    validate_ea_controller_call_chain(issues)
    validate_risk_manager_guardrails(issues)
    validate_signal_engine_guardrails(issues)

    return issues, forbidden_findings, forbidden_strategy_findings, trading_definitions


def main():
    source_files = discover_source_files()

    if source_files is None:
        print("MQ5 safety guardrails validation failed")
        print("Issues:")
        print("- mq5/ directory not found")
        return 1

    if not source_files:
        print("MQ5 safety guardrails validation failed")
        print("Issues:")
        print("- no .mq5 or .mqh files found under mq5/")
        return 1

    issues, forbidden_findings, forbidden_strategy_findings, trading_definitions = validate_sources(source_files)

    if issues:
        print("MQ5 safety guardrails validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQ5 safety guardrails validation passed")
    print(f"- scanned files count: {len(source_files)}")
    print("- InpEnableTrading default: false")
    print(f"- forbidden trading API findings: {len(forbidden_findings)}")
    print(f"- dangerous strategy keyword findings: {len(forbidden_strategy_findings)}")
    print("- ExecutionManager no-trade guard: passed")
    print("- EaController Signal -> Risk -> Execution call-chain guard: passed")
    print("- RiskManager InpEnableTrading and observation mode guard: passed")
    print("- SignalEngine no-trade guard: passed")
    print(f"- InpEnableTrading definitions checked: {len(trading_definitions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
