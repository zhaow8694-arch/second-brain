#!/usr/bin/env python3
"""Parse MT5 log no-trade summary metadata for evidence review."""

from pathlib import Path
import argparse
import json
import re
import sys


PASS_SAFETY_NOTES = [
    "parsed log is evidence metadata only",
    "not live trading readiness",
    "not real trading permission",
    "not profitability claim",
]

FORBIDDEN_EVIDENCE_PATTERNS = (
    ("OrderSend", re.compile(r"\bOrderSend\b")),
    ("PositionOpen", re.compile(r"\bPositionOpen\b")),
    ("OrderModify", re.compile(r"\bOrderModify\b")),
    ("PositionClose", re.compile(r"\bPositionClose\b")),
    ("OrderClose", re.compile(r"\bOrderClose\b")),
    ("CTrade", re.compile(r"\bCTrade\b")),
    ("Buy(", re.compile(r"\bBuy\s*\(")),
    ("Sell(", re.compile(r"\bSell\s*\(")),
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parse an MT5 log into no-trade summary JSON metadata."
    )
    parser.add_argument("log_file", help="Path to an MT5 log file.")
    parser.add_argument(
        "--allow-expert",
        default="TradingSystem",
        help="Expected expert name. Defaults to TradingSystem.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def normalize_space(value):
    return " ".join(str(value).split())


def read_log(path):
    log_path = Path(path)
    try:
        return log_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"MT5 log not found: {path}") from None
    except UnicodeDecodeError as error:
        raise ValueError(f"could not decode MT5 log as UTF-8: {error}") from None
    except OSError as error:
        raise ValueError(f"could not read MT5 log: {error}") from None


def bool_from_input(value):
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered == "false":
        return False
    if lowered == "true":
        return True
    return None


def parse_int(value):
    if value is None:
        return None
    match = re.search(r"[-+]?\d+", str(value).replace(" ", ""))
    if not match:
        return None
    return int(match.group(0))


def extract_expert_from_path(expert_path):
    parts = [part for part in re.split(r"[\\/]+", expert_path.strip()) if part]
    if not parts:
        return None
    file_name = parts[-1]
    if file_name.lower().endswith(".ex5"):
        return file_name[:-4]
    return file_name


def extract_testing_metadata(text):
    match = re.search(
        r"testing of\s+(.+?)\s+from\s+(\d{4}\.\d{2}\.\d{2})"
        r"(?:\s+\d{2}:\d{2}(?::\d{2})?)?\s+to\s+(\d{4}\.\d{2}\.\d{2})",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None, None
    return extract_expert_from_path(match.group(1)), match.group(2), match.group(3)


def extract_symbol_period(text):
    for line in text.splitlines():
        match = re.search(
            r"\b([A-Z][A-Z0-9._-]{1,31}),\s*(M\d+|H\d+|D1|W1|MN1)\b",
            line,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1), match.group(2).upper()
    return None, None


def extract_inputs(text):
    inputs = {}
    for match in re.finditer(r"\b(Inp[A-Za-z0-9_]+)\s*=\s*([^\s,;]+)", text):
        inputs[match.group(1)] = match.group(2).strip()
    return inputs


def extract_counter(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return parse_int(match.group(1))
    return None


def extract_counters(text):
    return {
        "riskApproved": extract_counter(text, (r"\briskApproved\s*=\s*(-?\d+)",)),
        "executionAttempts": extract_counter(text, (r"\bexecutionAttempts\s*=\s*(-?\d+)",)),
        "riskRejected": extract_counter(text, (r"\briskRejected\s*=\s*(-?\d+)",)),
        "riskRejectTradingDisabled": extract_counter(
            text,
            (r"\briskRejectTradingDisabled\s*=\s*(-?\d+)",),
        ),
        "riskRejectObservationMode": extract_counter(
            text,
            (r"\briskRejectObservationMode\s*=\s*(-?\d+)",),
        ),
        "totalTrades": extract_counter(
            text,
            (r"\btotal\s+trades\s*=\s*(-?\d+)", r"\btotalTrades\s*=\s*(-?\d+)"),
        ),
        "totalDeals": extract_counter(
            text,
            (r"\btotal\s+deals\s*=\s*(-?\d+)", r"\btotalDeals\s*=\s*(-?\d+)"),
        ),
    }


def is_negative_evidence_line(line):
    lowered = normalize_space(line).lower()
    return "no " in lowered and "evidence" in lowered


def detect_forbidden_evidence(text):
    issues = []
    order_send_evidence = False
    buy_sell_evidence = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        normalized = normalize_space(line)
        if not normalized or is_negative_evidence_line(normalized):
            continue

        for label, pattern in FORBIDDEN_EVIDENCE_PATTERNS:
            if pattern.search(normalized):
                issues.append(
                    f"forbidden real trading evidence found: {label} on line {line_number}"
                )
                if label == "OrderSend":
                    order_send_evidence = True
                if label in {"Buy(", "Sell("}:
                    buy_sell_evidence = True

    return issues, order_send_evidence, buy_sell_evidence


def require_field(name, value, issues):
    if value is None or value == "":
        issues.append(f"missing required field: {name}")


def build_no_trade_assertions(parsed, risk_observation_blocks):
    inp_enable_trading = bool_from_input(parsed["inputs"].get("InpEnableTrading"))
    trading_guard_ok = inp_enable_trading is False or risk_observation_blocks
    total_trades = parsed["totalTrades"]
    total_deals = parsed["totalDeals"]
    assertions = {
        "riskApproved": parsed["riskApproved"],
        "executionAttempts": parsed["executionAttempts"],
        "riskApprovedIsZero": parsed["riskApproved"] == 0,
        "executionAttemptsIsZero": parsed["executionAttempts"] == 0,
        "totalTrades": total_trades,
        "totalDeals": total_deals,
        "totalTradesIsZeroWhenPresent": total_trades in (None, 0),
        "totalDealsIsZeroWhenPresent": total_deals in (None, 0),
        "orderSendEvidence": parsed["orderSendEvidence"],
        "buySellEvidence": parsed["buySellEvidence"],
        "InpEnableTrading": inp_enable_trading,
        "riskObservationModeBlocksTrading": risk_observation_blocks,
        "tradingGuardPresent": trading_guard_ok,
    }
    assertions["passed"] = all(
        (
            assertions["riskApprovedIsZero"],
            assertions["executionAttemptsIsZero"],
            assertions["totalTradesIsZeroWhenPresent"],
            assertions["totalDealsIsZeroWhenPresent"],
            assertions["orderSendEvidence"] is False,
            assertions["buySellEvidence"] is False,
            assertions["tradingGuardPresent"],
        )
    )
    return assertions


def parse_log(text, expected_expert="TradingSystem"):
    issues = []
    expert_name, date_from, date_to = extract_testing_metadata(text)
    symbol, period = extract_symbol_period(text)
    inputs = extract_inputs(text)
    counters = extract_counters(text)
    forbidden_issues, order_send_evidence, buy_sell_evidence = detect_forbidden_evidence(text)
    risk_observation_blocks = "Risk observation mode blocks all real trading" in text

    parsed = {
        "expertName": expert_name,
        "symbol": symbol,
        "period": period,
        "dateFrom": date_from,
        "dateTo": date_to,
        "inputs": inputs,
        "riskApproved": counters["riskApproved"],
        "executionAttempts": counters["executionAttempts"],
        "riskRejected": counters["riskRejected"],
        "riskRejectTradingDisabled": counters["riskRejectTradingDisabled"],
        "riskRejectObservationMode": counters["riskRejectObservationMode"],
        "totalTrades": counters["totalTrades"],
        "totalDeals": counters["totalDeals"],
        "orderSendEvidence": order_send_evidence,
        "buySellEvidence": buy_sell_evidence,
        "warnings": [],
        "safetyNotes": PASS_SAFETY_NOTES,
    }

    for field in ("expertName", "symbol", "period", "dateFrom", "dateTo"):
        require_field(field, parsed[field], issues)

    if expected_expert and expert_name and expert_name != expected_expert:
        issues.append(
            f"expertName must be {expected_expert!r}, got {expert_name!r}"
        )

    if "InpEnableTrading" not in inputs and not risk_observation_blocks:
        issues.append(
            "missing required input: InpEnableTrading unless risk observation mode blocks trading"
        )
    elif bool_from_input(inputs.get("InpEnableTrading")) is True and not risk_observation_blocks:
        issues.append(
            "InpEnableTrading must be false unless risk observation mode blocks all real trading"
        )

    if parsed["riskApproved"] is None and parsed["executionAttempts"] is None:
        issues.append("missing required fields: riskApproved and executionAttempts")
    else:
        if parsed["riskApproved"] is None:
            issues.append("missing required field: riskApproved")
        if parsed["executionAttempts"] is None:
            issues.append("missing required field: executionAttempts")

    if parsed["riskApproved"] is not None and parsed["riskApproved"] != 0:
        issues.append("riskApproved must be 0 for no-trade evidence")
    if parsed["executionAttempts"] is not None and parsed["executionAttempts"] != 0:
        issues.append("executionAttempts must be 0 for no-trade evidence")
    if parsed["totalTrades"] is not None and parsed["totalTrades"] != 0:
        issues.append("totalTrades must be 0 when present for no-trade evidence")
    if parsed["totalDeals"] is not None and parsed["totalDeals"] != 0:
        issues.append("totalDeals must be 0 when present for no-trade evidence")

    issues.extend(forbidden_issues)

    if parsed["riskRejected"] is None:
        parsed["warnings"].append("riskRejected could not be safely determined")
    if parsed["totalTrades"] is None:
        parsed["warnings"].append("totalTrades not present in log")
    if parsed["totalDeals"] is None:
        parsed["warnings"].append("totalDeals not present in log")

    parsed["noTradeAssertions"] = build_no_trade_assertions(
        parsed,
        risk_observation_blocks,
    )
    return parsed, issues


def parse_log_file(path, expected_expert="TradingSystem"):
    return parse_log(read_log(path), expected_expert=expected_expert)


def main():
    args = parse_args()
    try:
        payload, issues = parse_log_file(args.log_file, expected_expert=args.allow_expert)
    except ValueError as error:
        print(f"MT5 log no-trade parser failed: {error}", file=sys.stderr)
        return 1

    if issues:
        print("MT5 log no-trade parser failed", file=sys.stderr)
        print("Issues:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
