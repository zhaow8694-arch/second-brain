from pathlib import Path
import re
import sys


FALSE_VALUES = {"false", "0"}
TRUE_VALUES = {"true", "1"}

REQUIRED_PARAMETER = "InpEnableTrading"
DENIED_TRUE_PARAMETERS = {
    "EnableTrading",
    "AllowTrading",
    "LiveTrading",
    "RealTrading",
    "UseLiveTrading",
    "EnableOrders",
    "EnableExecution",
    "AllowOrders",
    "AllowExecution",
    "UseOrderSend",
    "UseCTrade",
    "EnableCTrade",
    "EnableBuySell",
}
OBSERVATION_MODE_EXCEPTION_FILES = {
    "TASK-009_B_trading_true_observation_block.set",
    "TASK-009_C_risk_reject_log_off.set",
}


def relative_path(path, project_root):
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def is_comment_or_blank(line):
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("#")
        or stripped.startswith(";")
        or stripped.startswith("//")
    )


def parse_set_parameters(path):
    parameters = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if is_comment_or_blank(line) or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        parameters.append((key, value, line_number))
    return parameters


def boolean_value(value):
    normalized = value.strip().strip("\"'").lower()
    match = re.match(r"^(true|false|0|1)\b", normalized)
    if match:
        normalized = match.group(1)

    if normalized in FALSE_VALUES:
        return False
    if normalized in TRUE_VALUES:
        return True
    return None


def validate_set_file(path, project_root):
    issues = []
    allowed_exceptions = []
    parameters = parse_set_parameters(path)
    display_path = relative_path(path, project_root)
    is_observation_exception = path.name in OBSERVATION_MODE_EXCEPTION_FILES

    inp_enable_trading_found = False
    inp_enable_trading_false_count = 0

    for key, value, line_number in parameters:
        parsed_bool = boolean_value(value)

        if key == REQUIRED_PARAMETER:
            inp_enable_trading_found = True
            if parsed_bool is False:
                inp_enable_trading_false_count += 1
            elif parsed_bool is True:
                if is_observation_exception:
                    allowed_exceptions.append(
                        f"allowed observation-mode exception: {display_path} {key}={value}"
                    )
                else:
                    issues.append(
                        f"{display_path}:{line_number} {key} is not false: {value}"
                    )
            else:
                issues.append(
                    f"{display_path}:{line_number} {key} value cannot be determined: {value}"
                )

        if key in DENIED_TRUE_PARAMETERS:
            if parsed_bool is True:
                issues.append(
                    f"{display_path}:{line_number} dangerous parameter enabled: {key}={value}"
                )
            elif parsed_bool is None:
                issues.append(
                    f"{display_path}:{line_number} dangerous parameter value cannot be determined: {key}={value}"
                )

    if not inp_enable_trading_found:
        issues.append(f"{display_path} missing {REQUIRED_PARAMETER}")

    return issues, inp_enable_trading_false_count, allowed_exceptions


def validate_project(project_root):
    set_dir = project_root / "backtest" / "sets"
    issues = []

    if not set_dir.exists():
        return [f"{relative_path(set_dir, project_root)} directory not found"], 0, 0, []
    if not set_dir.is_dir():
        return [f"{relative_path(set_dir, project_root)} is not a directory"], 0, 0, []

    set_files = sorted(set_dir.glob("*.set"))
    if not set_files:
        return [f"{relative_path(set_dir, project_root)} contains no .set files"], 0, 0, []

    false_count = 0
    allowed_exceptions = []
    for set_file in set_files:
        file_issues, file_false_count, file_allowed_exceptions = validate_set_file(
            set_file, project_root
        )
        issues.extend(file_issues)
        false_count += file_false_count
        allowed_exceptions.extend(file_allowed_exceptions)

    return issues, len(set_files), false_count, allowed_exceptions


def main():
    project_root = Path(__file__).resolve().parents[1]
    issues, set_file_count, false_count, allowed_exceptions = validate_project(project_root)

    if issues:
        print("Backtest set safety validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Backtest set safety validation passed")
    for allowed_exception in allowed_exceptions:
        print(f"- {allowed_exception}")
    print(f"scanned set files count: {set_file_count}")
    print(f"InpEnableTrading false count: {false_count}")
    print(f"allowed observation exceptions count: {len(allowed_exceptions)}")
    print("dangerous enabled parameters: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
