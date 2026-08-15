#!/usr/bin/env python3
"""Parse MT5 Strategy Tester .set files into JSON parameter metadata."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys


PASS_SAFETY_NOTES = [
    "parsed set file is parameter metadata only",
    "not live trading readiness",
    "not real trading permission",
    "not profitability claim",
]

FALSE_VALUES = {"false", "0"}
TRUE_VALUES = {"true", "1"}

OBSERVATION_MODE_EXCEPTION_FILES = {
    "TASK-009_B_trading_true_observation_block.set",
    "TASK-009_C_risk_reject_log_off.set",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parse a Strategy Tester .set file into JSON metadata."
    )
    parser.add_argument("set_file", help="Path to a .set file.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise ValueError(f"set file not found: {path}") from None
    except OSError as error:
        raise ValueError(f"could not read set file: {error}") from None


def is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("#")
        or stripped.startswith(";")
        or stripped.startswith("//")
    )


def boolean_value(value: str) -> bool | None:
    normalized = value.strip().strip("\"'").lower()
    match = re.match(r"^(true|false|0|1)\b", normalized)
    if match:
        normalized = match.group(1)
    if normalized in FALSE_VALUES:
        return False
    if normalized in TRUE_VALUES:
        return True
    return None


def coerce_value(raw: str):
    parsed_bool = boolean_value(raw)
    if parsed_bool is not None:
        return parsed_bool
    stripped = raw.strip()
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if re.fullmatch(r"-?\d+\.\d+", stripped):
        return float(stripped)
    return stripped


def parse_set_file_text(text: str, *, file_name: str) -> dict[str, object]:
    parameters: dict[str, object] = {}
    raw_entries: list[dict[str, object]] = []
    issues: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if is_comment_or_blank(line) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        coerced = coerce_value(value)
        if key in parameters:
            issues.append(f"duplicate parameter at line {line_number}: {key}")
        parameters[key] = coerced
        raw_entries.append(
            {
                "name": key,
                "value": value,
                "parsedValue": coerced,
                "lineNumber": line_number,
            }
        )

    inp_enable_trading = parameters.get("InpEnableTrading")
    observation_exception = file_name in OBSERVATION_MODE_EXCEPTION_FILES
    no_trade_assertions = {
        "InpEnableTrading": inp_enable_trading,
        "InpEnableTradingIsFalse": inp_enable_trading is False,
        "observationModeException": observation_exception,
        "passed": inp_enable_trading is False or observation_exception,
    }

    if inp_enable_trading is None:
        issues.append("missing required parameter: InpEnableTrading")
    elif inp_enable_trading is not False and not observation_exception:
        issues.append("InpEnableTrading must be false unless observation-mode exception applies")

    return {
        "fileName": file_name,
        "parameterCount": len(parameters),
        "parameters": parameters,
        "entries": raw_entries,
        "noTradeAssertions": no_trade_assertions,
        "issues": issues,
        "safetyNotes": PASS_SAFETY_NOTES,
    }


def parse_set_file(path: str | Path) -> dict[str, object]:
    set_path = Path(path)
    text = read_text(set_path)
    return parse_set_file_text(text, file_name=set_path.name)


def main():
    args = parse_args()
    try:
        payload = parse_set_file(args.set_file)
    except ValueError as error:
        print(f"Backtest set parser failed: {error}", file=sys.stderr)
        return 1

    if payload["issues"]:
        print("Backtest set parser failed", file=sys.stderr)
        print("Issues:", file=sys.stderr)
        for issue in payload["issues"]:
            print(f"- {issue}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())