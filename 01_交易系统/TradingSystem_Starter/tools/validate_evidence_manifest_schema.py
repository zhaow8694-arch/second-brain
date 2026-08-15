#!/usr/bin/env python3
"""Validate a v0.4.0 evidence manifest JSON file."""

from pathlib import Path
import argparse
import json
import sys


PASS_TEXT = "Evidence manifest schema validation passed"
FAIL_TEXT = "Evidence manifest schema validation failed"

TOP_LEVEL_REQUIRED_FIELDS = [
    "schemaVersion",
    "taskId",
    "evidenceSetId",
    "source",
    "externalEvidenceRoot",
    "files",
    "mt5",
    "strategyTester",
    "expert",
    "inputs",
    "noTradeAssertions",
    "parserExpectations",
    "safetyAssertions",
    "repositoryState",
    "tags",
    "notes",
]

FILE_REQUIRED_FIELDS = [
    "fileName",
    "relativePath",
    "evidenceType",
    "required",
    "expectedParser",
    "expectedFields",
    "notes",
]

ALLOWED_EVIDENCE_TYPES = {
    "strategy_tester_html",
    "experts_log",
    "journal_log",
    "inputs_screenshot",
    "tester_screenshot",
    "runtime_summary_text",
    "other",
}

STRATEGY_TESTER_REQUIRED_FIELDS = [
    "expertName",
    "symbol",
    "period",
    "dateFrom",
    "dateTo",
    "model",
    "deposit",
    "leverage",
]

INPUTS_REQUIRED_FIELDS = [
    "InpEnableTrading",
    "InpEnableRiskObservation",
    "InpPrintRuntimeSummary",
]

NO_TRADE_REQUIRED_FIELDS = [
    "totalTrades",
    "totalDeals",
    "buyTrades",
    "sellTrades",
    "ordersOpened",
    "positionsOpened",
    "orderSendEvidence",
    "buySellEvidence",
    "executionAttempts",
    "riskApproved",
]

NO_TRADE_ZERO_FIELDS = [
    "totalTrades",
    "totalDeals",
    "buyTrades",
    "sellTrades",
    "ordersOpened",
    "positionsOpened",
    "executionAttempts",
    "riskApproved",
]

NO_TRADE_FALSE_FIELDS = [
    "orderSendEvidence",
    "buySellEvidence",
]

SAFETY_REQUIRED_FIELDS = [
    "noRealTrading",
    "noProfitOptimization",
    "noLiveTradingReadinessClaim",
    "noRealTradingAllowedClaim",
    "noProfitabilityClaim",
]

REPOSITORY_STATE_REQUIRED_FIELDS = [
    "head",
    "stableTag",
    "mq5Changed",
    "backtestSetsChanged",
    "backtestReportsChanged",
    "externalEvidenceCopiedIntoRepo",
    "mt5RunDuringTask",
]

REPOSITORY_STATE_FALSE_FIELDS = [
    "mq5Changed",
    "backtestSetsChanged",
    "backtestReportsChanged",
    "externalEvidenceCopiedIntoRepo",
    "mt5RunDuringTask",
]

TAGS_REQUIRED_FIELDS = [
    "stableTag",
    "stableTagTarget",
]

FORBIDDEN_INTERPRETATION_PHRASES = [
    "live trading ready",
    "real trading allowed",
    "real trading enabled",
    "profitable strategy",
    "profit optimized",
    "production trading ready",
]

ALLOWED_NEGATION_PREFIXES = (
    "no ",
    "not ",
    "not a ",
    "not an ",
    "does not ",
    "do not ",
    "doesn't ",
    "is not ",
    "are not ",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate a JSON evidence manifest schema."
    )
    parser.add_argument("manifest", help="Path to the manifest JSON file.")
    return parser.parse_args()


def require_object(value, path, issues):
    if not isinstance(value, dict):
        issues.append(f"{path} must be an object")
        return False
    return True


def require_fields(value, fields, path, issues):
    if not require_object(value, path, issues):
        return
    for field in fields:
        if field not in value:
            issues.append(f"{path} missing required field: {field}")


def is_forbidden_interpretation(text, phrase):
    lowered = " ".join(text.lower().split())
    start = lowered.find(phrase)
    while start != -1:
        prefix_window = lowered[max(0, start - 40) : start]
        if not any(prefix_window.rstrip().endswith(prefix) for prefix in ALLOWED_NEGATION_PREFIXES):
            return True
        start = lowered.find(phrase, start + 1)
    return False


def collect_string_values(value, path="$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from collect_string_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from collect_string_values(child, f"{path}[{index}]")


def validate_files(payload, issues):
    files = payload.get("files")
    if not isinstance(files, list):
        issues.append("files must be a list")
        return

    for index, item in enumerate(files):
        item_path = f"files[{index}]"
        require_fields(item, FILE_REQUIRED_FIELDS, item_path, issues)
        if not isinstance(item, dict):
            continue

        evidence_type = item.get("evidenceType")
        if evidence_type not in ALLOWED_EVIDENCE_TYPES:
            issues.append(
                f"{item_path}.evidenceType invalid value: {evidence_type!r}"
            )


def validate_no_trade_assertions(payload, issues):
    no_trade = payload.get("noTradeAssertions")
    require_fields(no_trade, NO_TRADE_REQUIRED_FIELDS, "noTradeAssertions", issues)
    if not isinstance(no_trade, dict):
        return

    for field in NO_TRADE_ZERO_FIELDS:
        if no_trade.get(field) != 0:
            issues.append(f"noTradeAssertions.{field} must be 0")

    for field in NO_TRADE_FALSE_FIELDS:
        if no_trade.get(field) is not False:
            issues.append(f"noTradeAssertions.{field} must be false")


def validate_safety_assertions(payload, issues):
    safety = payload.get("safetyAssertions")
    require_fields(safety, SAFETY_REQUIRED_FIELDS, "safetyAssertions", issues)
    if not isinstance(safety, dict):
        return

    for field in SAFETY_REQUIRED_FIELDS:
        if safety.get(field) is not True:
            issues.append(f"safetyAssertions.{field} must be true")


def validate_repository_state(payload, issues):
    state = payload.get("repositoryState")
    require_fields(state, REPOSITORY_STATE_REQUIRED_FIELDS, "repositoryState", issues)
    if not isinstance(state, dict):
        return

    for field in REPOSITORY_STATE_FALSE_FIELDS:
        if state.get(field) is not False:
            issues.append(f"repositoryState.{field} must be false")


def validate_forbidden_interpretations(payload, issues):
    for path, text in collect_string_values(payload):
        for phrase in FORBIDDEN_INTERPRETATION_PHRASES:
            if is_forbidden_interpretation(text, phrase):
                issues.append(
                    f"{path} contains forbidden interpretation text: {phrase}"
                )


def validate_manifest(payload):
    issues = []
    if not isinstance(payload, dict):
        return ["manifest top-level value must be an object"]

    require_fields(payload, TOP_LEVEL_REQUIRED_FIELDS, "manifest", issues)
    validate_files(payload, issues)
    require_fields(
        payload.get("strategyTester"),
        STRATEGY_TESTER_REQUIRED_FIELDS,
        "strategyTester",
        issues,
    )
    require_fields(payload.get("inputs"), INPUTS_REQUIRED_FIELDS, "inputs", issues)
    validate_no_trade_assertions(payload, issues)
    validate_safety_assertions(payload, issues)
    validate_repository_state(payload, issues)
    require_fields(payload.get("tags"), TAGS_REQUIRED_FIELDS, "tags", issues)
    validate_forbidden_interpretations(payload, issues)
    return issues


def load_manifest(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle), []
    except FileNotFoundError:
        return None, [f"manifest JSON file not found: {path}"]
    except json.JSONDecodeError as error:
        return None, [f"manifest JSON is invalid: {error}"]
    except OSError as error:
        return None, [f"could not read manifest JSON: {error}"]


def main():
    args = parse_args()
    payload, load_issues = load_manifest(args.manifest)
    issues = load_issues if load_issues else validate_manifest(payload)

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
