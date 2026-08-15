#!/usr/bin/env python3
"""Parse MT5 Strategy Tester HTML report metadata for no-trade evidence review."""

from html.parser import HTMLParser
from pathlib import Path
import argparse
import html
import json
import re
import sys


PASS_SAFETY_NOTES = [
    "parsed report is evidence metadata only",
    "not live trading readiness",
    "not real trading permission",
    "not profitability claim",
]

ENCODING_BOMS = (
    (b"\xef\xbb\xbf", "utf-8-sig"),
    (b"\xff\xfe", "utf-16"),
    (b"\xfe\xff", "utf-16"),
)


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        text = html.unescape(data).strip()
        if text:
            self.parts.append(text)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parse a Strategy Tester HTML report into JSON metadata."
    )
    parser.add_argument("html_report", help="Path to a Strategy Tester HTML report.")
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


def read_html(path):
    report_path = Path(path)
    try:
        raw = report_path.read_bytes()
    except FileNotFoundError:
        raise ValueError(f"HTML report not found: {path}") from None
    except OSError as error:
        raise ValueError(f"could not read HTML report: {error}") from None

    for signature, encoding in ENCODING_BOMS:
        if raw.startswith(signature):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError as error:
                raise ValueError(
                    f"could not decode HTML report with detected {encoding} BOM: {error}"
                ) from None

    errors = []
    for encoding in ("utf-8", "utf-16"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as error:
            errors.append(f"{encoding}: {error}")

    details = "; ".join(errors)
    raise ValueError(f"could not decode HTML report as UTF-8 or UTF-16: {details}")


def collect_tokens(html_text):
    collector = TextCollector()
    collector.feed(html_text)
    return collector.parts


def normalize_space(value):
    return " ".join(str(value).split())


def normalized_text(tokens):
    return "\n".join(normalize_space(token) for token in tokens if normalize_space(token))


def compact_label(value):
    return re.sub(r"\s+", "", value).rstrip(":：")


def value_after_label(tokens, labels):
    label_set = {compact_label(label) for label in labels}
    separators = (":", "：")
    for index, token in enumerate(tokens):
        stripped = normalize_space(token)
        compact = compact_label(stripped)
        if compact in label_set:
            for next_token in tokens[index + 1 :]:
                candidate = normalize_space(next_token)
                if candidate:
                    return candidate
        if any(compact.startswith(lc) for lc in label_set):
            for next_token in tokens[index + 1 :]:
                candidate = normalize_space(next_token)
                if candidate:
                    return candidate
        for label in labels:
            for separator in separators:
                prefix = f"{label}{separator}"
                if stripped.startswith(prefix):
                    value = normalize_space(stripped[len(prefix) :])
                    if value:
                        return value
    return None


def extract_build(text):
    match = re.search(r"Build\s+(\d+)", text, re.IGNORECASE)
    return match.group(1) if match else None


def normalize_amount(value):
    if value is None:
        return None
    match = re.search(r"[-+]?\d[\d\s,]*\.?\d*", value)
    if not match:
        return None
    return match.group(0).replace(" ", "").replace(",", "")


def parse_integer(value):
    if value is None:
        return None
    match = re.search(r"[-+]?\d+", value.replace(" ", ""))
    if not match:
        return None
    return int(match.group(0))


def parse_period_and_dates(value):
    if not value:
        return None, None, None
    match = re.search(
        r"^\s*([A-Za-z0-9_]+)\s*\(\s*(\d{4}\.\d{2}\.\d{2})\s*-\s*(\d{4}\.\d{2}\.\d{2})\s*\)",
        value,
    )
    if not match:
        return None, None, None
    return match.group(1), match.group(2), match.group(3)


def extract_inputs(text):
    inputs = {}
    for match in re.finditer(r"\b(Inp[A-Za-z0-9_]+)\s*=\s*([^\s<>]+)", text):
        inputs[match.group(1)] = match.group(2).strip()
    return inputs


def bool_from_input(value):
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered == "false":
        return False
    if lowered == "true":
        return True
    return None


def require_field(name, value, issues):
    if value is None or value == "":
        issues.append(f"missing required field: {name}")


def build_no_trade_assertions(parsed):
    assertions = {
        "totalTrades": parsed["totalTrades"],
        "totalDeals": parsed["totalDeals"],
        "buyTrades": parsed["buyTrades"],
        "sellTrades": parsed["sellTrades"],
        "ordersOpened": parsed["ordersOpened"],
        "positionsOpened": parsed["positionsOpened"],
        "InpEnableTrading": bool_from_input(parsed["inputs"].get("InpEnableTrading")),
    }
    assertions["passed"] = all(
        (
            assertions["totalTrades"] == 0,
            assertions["totalDeals"] == 0,
            assertions["buyTrades"] == 0,
            assertions["sellTrades"] == 0,
            assertions["ordersOpened"] in (0, "unknown"),
            assertions["positionsOpened"] in (0, "unknown"),
            assertions["InpEnableTrading"] is False,
        )
    )
    return assertions


def parse_report(html_text, expected_expert="TradingSystem"):
    tokens = collect_tokens(html_text)
    text = normalized_text(tokens)
    issues = []

    expert_name = value_after_label(tokens, ["专家", "Expert", "Expert Advisor"])
    symbol = value_after_label(tokens, ["交易品种", "Symbol"])
    period_value = value_after_label(tokens, ["期间", "Period"])
    period, date_from, date_to = parse_period_and_dates(period_value)

    parsed = {
        "expertName": expert_name,
        "symbol": symbol,
        "period": period,
        "dateFrom": date_from,
        "dateTo": date_to,
        "build": extract_build(text),
        "initialDeposit": normalize_amount(
            value_after_label(tokens, ["初始存款", "初始入金", "Deposit", "Initial deposit"])
        ),
        "leverage": value_after_label(tokens, ["杠杆", "Leverage"]),
        "inputs": extract_inputs(text),
        "totalTrades": parse_integer(value_after_label(tokens, ["交易总计", "Total Trades"])),
        "totalDeals": parse_integer(value_after_label(tokens, ["总成交", "Total Deals"])),
        "buyTrades": parse_integer(value_after_label(tokens, ["买入交易", "Buy Trades"])),
        "sellTrades": parse_integer(value_after_label(tokens, ["卖出交易", "Sell Trades"])),
        "ordersOpened": parse_integer(value_after_label(tokens, ["订单", "Orders"])),
        "positionsOpened": parse_integer(value_after_label(tokens, ["持仓", "Positions"])),
        "warnings": [],
        "safetyNotes": PASS_SAFETY_NOTES,
    }

    for field in (
        "expertName",
        "symbol",
        "period",
        "dateFrom",
        "dateTo",
        "totalTrades",
        "totalDeals",
        "buyTrades",
        "sellTrades",
    ):
        require_field(field, parsed[field], issues)

    if expected_expert and expert_name and expert_name != expected_expert:
        issues.append(
            f"expertName must be {expected_expert!r}, got {expert_name!r}"
        )

    if "InpEnableTrading" not in parsed["inputs"]:
        issues.append("missing required input: InpEnableTrading")
    elif bool_from_input(parsed["inputs"].get("InpEnableTrading")) is not False:
        issues.append("InpEnableTrading must be false for no-trade evidence")

    for field in ("totalTrades", "totalDeals", "buyTrades", "sellTrades"):
        value = parsed[field]
        if value is not None and value != 0:
            issues.append(f"{field} must be 0 for no-trade evidence")

    for field in ("ordersOpened", "positionsOpened"):
        value = parsed[field]
        if isinstance(value, int) and value != 0:
            issues.append(f"{field} must be 0 for no-trade evidence")

    if parsed["ordersOpened"] is None:
        parsed["ordersOpened"] = "unknown"
        parsed["warnings"].append("ordersOpened could not be safely determined")
    if parsed["positionsOpened"] is None:
        parsed["positionsOpened"] = "unknown"
        parsed["warnings"].append("positionsOpened could not be safely determined")

    parsed["noTradeAssertions"] = build_no_trade_assertions(parsed)
    return parsed, issues


def main():
    args = parse_args()
    try:
        html_text = read_html(args.html_report)
        payload, issues = parse_report(html_text, expected_expert=args.allow_expert)
    except ValueError as error:
        print(f"Strategy Tester HTML parser failed: {error}", file=sys.stderr)
        return 1

    if issues:
        print("Strategy Tester HTML parser failed", file=sys.stderr)
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
