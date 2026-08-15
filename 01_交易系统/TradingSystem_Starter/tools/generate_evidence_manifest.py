#!/usr/bin/env python3
"""Generate a v0.4.0 evidence manifest JSON from parser metadata."""

from pathlib import Path
import argparse
import json
import sys


SCHEMA_VERSION = "1.0"

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

HTML_REQUIRED_FIELDS = [
    "expertName",
    "symbol",
    "period",
    "dateFrom",
    "dateTo",
    "inputs",
    "totalTrades",
    "totalDeals",
    "buyTrades",
    "sellTrades",
]

LOG_REQUIRED_FIELDS = [
    "riskApproved",
    "executionAttempts",
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

SAFETY_NOTES = [
    "evidence manifest is metadata only",
    "no live trading readiness",
    "not real trading permission",
    "not a profitability claim",
    "no external evidence copied",
    "no MT5 run during generation",
]


class ManifestGenerationError(ValueError):
    """Raised when synthetic parser metadata cannot form a valid manifest."""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an evidence manifest JSON from parser output JSON files."
    )
    parser.add_argument("--html-json", required=True, help="HTML parser output JSON file.")
    parser.add_argument("--log-json", required=True, help="MT5 log parser output JSON file.")
    parser.add_argument("--files-json", required=True, help="Evidence file list JSON file.")
    parser.add_argument("--repo-json", required=True, help="Repository state JSON file.")
    parser.add_argument("--tags-json", required=True, help="Stable tag metadata JSON file.")
    parser.add_argument("--task-id", required=True, help="Task id for the manifest.")
    parser.add_argument("--evidence-set-id", required=True, help="Evidence set id.")
    parser.add_argument("--external-root", required=True, help="External evidence root metadata.")
    return parser.parse_args()


def load_json(path, label):
    json_path = Path(path)
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestGenerationError(f"{label} JSON file not found: {path}") from None
    except json.JSONDecodeError as error:
        raise ManifestGenerationError(f"{label} JSON is invalid: {error}") from None
    except OSError as error:
        raise ManifestGenerationError(f"could not read {label} JSON: {error}") from None


def require_object(value, label):
    if not isinstance(value, dict):
        raise ManifestGenerationError(f"{label} must be an object")


def require_fields(payload, fields, label):
    require_object(payload, label)
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ManifestGenerationError(
            f"{label} missing required field(s): {', '.join(missing)}"
        )


def as_zero_int(value, label):
    if isinstance(value, bool) or value is None:
        raise ManifestGenerationError(f"{label} must be numeric 0")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.strip().lstrip("-").isdigit():
        number = int(value.strip())
    else:
        raise ManifestGenerationError(f"{label} must be numeric 0")
    if number != 0:
        raise ManifestGenerationError(f"{label} must be 0")
    return number


def optional_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return default


def bool_evidence(payload, field):
    if field in payload:
        return optional_bool(payload.get(field), default=False)
    assertions = payload.get("noTradeAssertions")
    if isinstance(assertions, dict) and field in assertions:
        return optional_bool(assertions.get(field), default=False)
    return False


def normalize_input_value(value):
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return value


def merge_inputs(html_inputs, log_inputs):
    if not isinstance(html_inputs, dict):
        raise ManifestGenerationError("html.inputs must be an object")
    if log_inputs is None:
        log_inputs = {}
    if not isinstance(log_inputs, dict):
        raise ManifestGenerationError("log.inputs must be an object when present")

    merged = {
        key: normalize_input_value(value)
        for key, value in html_inputs.items()
    }
    for key, value in log_inputs.items():
        normalized_value = normalize_input_value(value)
        if key in merged:
            if merged[key] != normalized_value:
                raise ManifestGenerationError(
                    f"input conflict for {key}: html={merged[key]!r}, log={normalized_value!r}"
                )
            continue
        merged[key] = normalized_value
    return merged


def normalize_files(files_payload):
    if isinstance(files_payload, dict) and "files" in files_payload:
        files = files_payload["files"]
    else:
        files = files_payload

    if not isinstance(files, list):
        raise ManifestGenerationError("files JSON must be a list or an object with files[]")

    normalized = []
    for index, item in enumerate(files):
        label = f"files[{index}]"
        require_fields(item, FILE_REQUIRED_FIELDS, label)
        evidence_type = item.get("evidenceType")
        if evidence_type not in ALLOWED_EVIDENCE_TYPES:
            raise ManifestGenerationError(
                f"{label}.evidenceType invalid value: {evidence_type!r}"
            )
        normalized.append(dict(item))
    return normalized


def validate_repository_state(state):
    require_fields(state, REPOSITORY_STATE_REQUIRED_FIELDS, "repositoryState")
    for field in REPOSITORY_STATE_FALSE_FIELDS:
        if state.get(field) is not False:
            raise ManifestGenerationError(f"repositoryState.{field} must be false")
    return dict(state)


def validate_tags(tags):
    require_fields(tags, TAGS_REQUIRED_FIELDS, "tags")
    return dict(tags)


def resolve_open_count(field, html_payload, log_payload, trade_context, notes):
    for source in (html_payload, log_payload):
        if field not in source:
            continue
        value = source.get(field)
        if value == "unknown" or value is None:
            continue
        return as_zero_int(value, field)

    if trade_context:
        notes.append(
            f"{field} inferred as 0 from zero trades/deals and no trade API evidence"
        )
        return 0

    raise ManifestGenerationError(f"{field} could not be safely determined")


def build_no_trade_assertions(html_payload, log_payload, notes):
    total_trades = as_zero_int(html_payload.get("totalTrades"), "totalTrades")
    total_deals = as_zero_int(html_payload.get("totalDeals"), "totalDeals")
    buy_trades = as_zero_int(html_payload.get("buyTrades"), "buyTrades")
    sell_trades = as_zero_int(html_payload.get("sellTrades"), "sellTrades")
    risk_approved = as_zero_int(log_payload.get("riskApproved"), "riskApproved")
    execution_attempts = as_zero_int(
        log_payload.get("executionAttempts"),
        "executionAttempts",
    )

    order_send_evidence = bool_evidence(html_payload, "orderSendEvidence") or bool_evidence(
        log_payload,
        "orderSendEvidence",
    )
    buy_sell_evidence = bool_evidence(html_payload, "buySellEvidence") or bool_evidence(
        log_payload,
        "buySellEvidence",
    )
    if order_send_evidence:
        raise ManifestGenerationError("orderSendEvidence must be false")
    if buy_sell_evidence:
        raise ManifestGenerationError("buySellEvidence must be false")

    trade_context_allows_inference = all(
        (
            total_trades == 0,
            total_deals == 0,
            order_send_evidence is False,
            buy_sell_evidence is False,
        )
    )
    orders_opened = resolve_open_count(
        "ordersOpened",
        html_payload,
        log_payload,
        trade_context_allows_inference,
        notes,
    )
    positions_opened = resolve_open_count(
        "positionsOpened",
        html_payload,
        log_payload,
        trade_context_allows_inference,
        notes,
    )

    return {
        "totalTrades": total_trades,
        "totalDeals": total_deals,
        "buyTrades": buy_trades,
        "sellTrades": sell_trades,
        "ordersOpened": orders_opened,
        "positionsOpened": positions_opened,
        "orderSendEvidence": False,
        "buySellEvidence": False,
        "executionAttempts": execution_attempts,
        "riskApproved": risk_approved,
    }


def build_parser_expectations(model_unknown, inferred_open_counts):
    known_gaps = []
    if model_unknown:
        known_gaps.append("model may be unknown")
    if inferred_open_counts:
        known_gaps.append("ordersOpened / positionsOpened may be inferred")

    return {
        "htmlParser": [
            "strategyTester",
            "inputs",
            "trade stats",
        ],
        "logParser": [
            "riskApproved",
            "executionAttempts",
            "risk rejection summary",
        ],
        "manifestValidator": [
            "schema",
            "no-trade assertions",
        ],
        "knownGaps": known_gaps,
    }


def generate_manifest(
    html_payload,
    log_payload,
    files_payload,
    repo_payload,
    tags_payload,
    task_id,
    evidence_set_id,
    external_root,
):
    require_fields(html_payload, HTML_REQUIRED_FIELDS, "html parser output")
    require_fields(log_payload, LOG_REQUIRED_FIELDS, "log parser output")
    files = normalize_files(files_payload)
    repository_state = validate_repository_state(repo_payload)
    tags = validate_tags(tags_payload)
    notes = list(SAFETY_NOTES)

    model = html_payload.get("model")
    model_unknown = model is None or model == ""
    if model_unknown:
        model = "unknown"
        notes.append("model missing from parser output; recorded as unknown")

    inputs = merge_inputs(html_payload.get("inputs"), log_payload.get("inputs"))
    no_trade_assertions = build_no_trade_assertions(html_payload, log_payload, notes)
    inferred_open_counts = any("inferred as 0" in note for note in notes)

    strategy_tester = {
        "expertName": html_payload["expertName"],
        "symbol": html_payload["symbol"],
        "period": html_payload["period"],
        "dateFrom": html_payload["dateFrom"],
        "dateTo": html_payload["dateTo"],
        "build": html_payload.get("build", "unknown"),
        "model": model,
        "deposit": html_payload.get("deposit") or html_payload.get("initialDeposit"),
        "leverage": html_payload.get("leverage"),
    }
    if not strategy_tester["deposit"]:
        raise ManifestGenerationError("html parser output missing deposit / initialDeposit")
    if not strategy_tester["leverage"]:
        raise ManifestGenerationError("html parser output missing leverage")

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "taskId": task_id,
        "evidenceSetId": evidence_set_id,
        "source": "parser_metadata",
        "externalEvidenceRoot": external_root,
        "files": files,
        "mt5": {
            "build": strategy_tester["build"],
        },
        "strategyTester": strategy_tester,
        "expert": {
            "name": html_payload["expertName"],
        },
        "inputs": inputs,
        "noTradeAssertions": no_trade_assertions,
        "parserExpectations": build_parser_expectations(
            model_unknown,
            inferred_open_counts,
        ),
        "safetyAssertions": {
            "noRealTrading": True,
            "noProfitOptimization": True,
            "noLiveTradingReadinessClaim": True,
            "noRealTradingAllowedClaim": True,
            "noProfitabilityClaim": True,
        },
        "repositoryState": repository_state,
        "tags": tags,
        "notes": notes,
    }
    return manifest


def generate_manifest_from_files(args):
    return generate_manifest(
        load_json(args.html_json, "html parser output"),
        load_json(args.log_json, "log parser output"),
        load_json(args.files_json, "files"),
        load_json(args.repo_json, "repository state"),
        load_json(args.tags_json, "tags"),
        args.task_id,
        args.evidence_set_id,
        args.external_root,
    )


def main():
    args = parse_args()
    try:
        manifest = generate_manifest_from_files(args)
    except ManifestGenerationError as error:
        print(f"Evidence manifest generation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
