#!/usr/bin/env python3
"""Self-test the evidence manifest generator."""

from pathlib import Path
import copy
import importlib
import json
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "tools"))
GENERATOR = importlib.import_module("generate_evidence_manifest")
VALIDATOR = importlib.import_module("validate_evidence_manifest_schema")

SELF_TEST_PASS_TEXT = "Evidence manifest generator self-test passed"
SELF_TEST_FAIL_TEXT = "Evidence manifest generator self-test failed"


def valid_html():
    return {
        "expertName": "TradingSystem",
        "symbol": "EURUSD",
        "period": "M5",
        "dateFrom": "2024.01.01",
        "dateTo": "2024.01.31",
        "build": "5836",
        "initialDeposit": "10000.00",
        "leverage": "1:100",
        "model": "Every tick",
        "inputs": {
            "InpEnableTrading": "false",
            "InpEnableRiskObservation": "true",
            "InpPrintRuntimeSummary": "true",
            "InpPrintNewBarLog": "true",
            "InpNewBarLogEveryN": "1000",
        },
        "totalTrades": 0,
        "totalDeals": 0,
        "buyTrades": 0,
        "sellTrades": 0,
        "ordersOpened": "unknown",
        "positionsOpened": "unknown",
        "noTradeAssertions": {
            "passed": True,
        },
        "warnings": [],
        "safetyNotes": [
            "parsed report is evidence metadata only",
            "no live trading readiness",
            "not a profitability claim",
        ],
    }


def valid_log():
    return {
        "expertName": "TradingSystem",
        "symbol": "EURUSD",
        "period": "M5",
        "dateFrom": "2024.01.01",
        "dateTo": "2024.01.31",
        "inputs": {
            "InpEnableTrading": "false",
            "InpEnableRiskObservation": "true",
            "InpPrintRuntimeSummary": "true",
        },
        "riskApproved": 0,
        "executionAttempts": 0,
        "riskRejected": 6047,
        "riskRejectTradingDisabled": 6047,
        "riskRejectObservationMode": None,
        "totalTrades": 0,
        "totalDeals": 0,
        "orderSendEvidence": False,
        "buySellEvidence": False,
        "noTradeAssertions": {
            "passed": True,
        },
        "warnings": [],
        "safetyNotes": [
            "parsed log is evidence metadata only",
            "no live trading readiness",
            "not a profitability claim",
        ],
    }


def valid_files():
    return {
        "files": [
            {
                "fileName": "TesterBacktest.html",
                "relativePath": "TesterBacktest.html",
                "evidenceType": "strategy_tester_html",
                "required": True,
                "expectedParser": "parse_strategy_tester_html_report.py",
                "expectedFields": [
                    "expertName",
                    "symbol",
                    "totalTrades",
                    "totalDeals",
                ],
                "notes": "synthetic file-list fixture; no live trading readiness",
            },
            {
                "fileName": "log.txt",
                "relativePath": "log.txt",
                "evidenceType": "experts_log",
                "required": True,
                "expectedParser": "parse_mt5_log_no_trade_summary.py",
                "expectedFields": [
                    "riskApproved",
                    "executionAttempts",
                ],
                "notes": "synthetic file-list fixture; not a profitability claim",
            },
        ]
    }


def valid_repo():
    return {
        "head": "a265676",
        "stableTag": "v0.4.7-mt5-log-no-trade-parser",
        "mq5Changed": False,
        "backtestSetsChanged": False,
        "backtestReportsChanged": False,
        "externalEvidenceCopiedIntoRepo": False,
        "mt5RunDuringTask": False,
    }


def valid_tags():
    return {
        "stableTag": "v0.4.7-mt5-log-no-trade-parser",
        "stableTagTarget": "14e2702",
    }


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_with_temp_files(
    html=None,
    log=None,
    files=None,
    repo=None,
    tags=None,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        paths = {
            "html_json": temp_path / "html.json",
            "log_json": temp_path / "log.json",
            "files_json": temp_path / "files.json",
            "repo_json": temp_path / "repo.json",
            "tags_json": temp_path / "tags.json",
        }
        write_json(paths["html_json"], html if html is not None else valid_html())
        write_json(paths["log_json"], log if log is not None else valid_log())
        write_json(paths["files_json"], files if files is not None else valid_files())
        write_json(paths["repo_json"], repo if repo is not None else valid_repo())
        write_json(paths["tags_json"], tags if tags is not None else valid_tags())

        class Args:
            pass

        args = Args()
        args.html_json = str(paths["html_json"])
        args.log_json = str(paths["log_json"])
        args.files_json = str(paths["files_json"])
        args.repo_json = str(paths["repo_json"])
        args.tags_json = str(paths["tags_json"])
        args.task_id = "TASK-108"
        args.evidence_set_id = "TASK-108-synthetic"
        args.external_root = "E:/synthetic/external/root"
        return GENERATOR.generate_manifest_from_files(args)


def generated_manifest_issues(manifest):
    return VALIDATOR.validate_manifest(manifest)


def expect_failure(change, expected_text):
    html = valid_html()
    log = valid_log()
    files = valid_files()
    repo = valid_repo()
    tags = valid_tags()
    change(html, log, files, repo, tags)
    try:
        generate_with_temp_files(html, log, files, repo, tags)
    except GENERATOR.ManifestGenerationError as error:
        return expected_text in str(error)
    return False


def test_positive_valid_manifest_generation():
    manifest = generate_with_temp_files()
    return (
        manifest["taskId"] == "TASK-108"
        and manifest["evidenceSetId"] == "TASK-108-synthetic"
        and not generated_manifest_issues(manifest)
    )


def test_missing_html_required_field():
    return expect_failure(
        lambda html, log, files, repo, tags: html.pop("expertName"),
        "expertName",
    )


def test_missing_log_risk_fields():
    return expect_failure(
        lambda html, log, files, repo, tags: (
            log.pop("riskApproved"),
            log.pop("executionAttempts"),
        ),
        "riskApproved",
    )


def test_repo_mq5_changed_true():
    return expect_failure(
        lambda html, log, files, repo, tags: repo.update({"mq5Changed": True}),
        "repositoryState.mq5Changed must be false",
    )


def test_repo_external_evidence_copied_true():
    return expect_failure(
        lambda html, log, files, repo, tags: repo.update(
            {"externalEvidenceCopiedIntoRepo": True}
        ),
        "repositoryState.externalEvidenceCopiedIntoRepo must be false",
    )


def test_files_invalid_evidence_type():
    return expect_failure(
        lambda html, log, files, repo, tags: files["files"][0].update(
            {"evidenceType": "html"}
        ),
        "evidenceType invalid value",
    )


def test_order_send_evidence_true():
    return expect_failure(
        lambda html, log, files, repo, tags: log.update({"orderSendEvidence": True}),
        "orderSendEvidence must be false",
    )


def test_buy_sell_evidence_true():
    return expect_failure(
        lambda html, log, files, repo, tags: log.update({"buySellEvidence": True}),
        "buySellEvidence must be false",
    )


def test_model_missing_records_unknown_gap():
    html = valid_html()
    html.pop("model")
    manifest = generate_with_temp_files(html=html)
    notes = "\n".join(manifest["notes"])
    gaps = manifest["parserExpectations"]["knownGaps"]
    return (
        manifest["strategyTester"]["model"] == "unknown"
        and "model missing" in notes
        and "model may be unknown" in gaps
        and not generated_manifest_issues(manifest)
    )


def test_orders_positions_inferred_from_zero_trade_context():
    html = valid_html()
    html["ordersOpened"] = "unknown"
    html["positionsOpened"] = "unknown"
    manifest = generate_with_temp_files(html=html)
    notes = "\n".join(manifest["notes"])
    return (
        manifest["noTradeAssertions"]["ordersOpened"] == 0
        and manifest["noTradeAssertions"]["positionsOpened"] == 0
        and "ordersOpened inferred as 0" in notes
        and "positionsOpened inferred as 0" in notes
        and not generated_manifest_issues(manifest)
    )


def test_notes_contain_safety_wording():
    manifest = generate_with_temp_files()
    notes = "\n".join(manifest["notes"])
    return (
        "no live trading readiness" in notes
        and "not a profitability claim" in notes
        and "no external evidence copied" in notes
        and "no MT5 run during generation" in notes
    )


def test_html_inputs_preserved_when_log_has_extra_input():
    log = valid_log()
    log["inputs"] = copy.deepcopy(log["inputs"])
    log["inputs"]["InpPrintSignalLog"] = "true"
    manifest = generate_with_temp_files(log=log)
    return (
        manifest["inputs"]["InpEnableTrading"] is False
        and manifest["inputs"]["InpPrintSignalLog"] is True
        and not generated_manifest_issues(manifest)
    )


def main():
    checks = [
        ("positive valid manifest generation failed", test_positive_valid_manifest_generation),
        ("missing html parser required field was not detected", test_missing_html_required_field),
        ("missing log riskApproved / executionAttempts was not detected", test_missing_log_risk_fields),
        ("repo_state mq5Changed=true was not detected", test_repo_mq5_changed_true),
        (
            "repo_state externalEvidenceCopiedIntoRepo=true was not detected",
            test_repo_external_evidence_copied_true,
        ),
        ("files[] invalid evidenceType was not detected", test_files_invalid_evidence_type),
        ("orderSendEvidence=true was not detected", test_order_send_evidence_true),
        ("buySellEvidence=true was not detected", test_buy_sell_evidence_true),
        ("missing model did not record unknown gap", test_model_missing_records_unknown_gap),
        (
            "ordersOpened / positionsOpened inference failed",
            test_orders_positions_inferred_from_zero_trade_context,
        ),
        ("safety notes were missing", test_notes_contain_safety_wording),
        ("html/log input merge failed", test_html_inputs_preserved_when_log_has_extra_input),
    ]

    failures = []
    for message, check in checks:
        if not check():
            failures.append(message)

    if failures:
        print(SELF_TEST_FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(SELF_TEST_PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
