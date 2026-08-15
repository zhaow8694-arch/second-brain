#!/usr/bin/env python3
"""Self-test the evidence manifest schema validator."""

from pathlib import Path
import copy
import importlib
import json
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "tools"))
VALIDATOR = importlib.import_module("validate_evidence_manifest_schema")

PASS_TEXT = VALIDATOR.PASS_TEXT
FAIL_TEXT = VALIDATOR.FAIL_TEXT
SELF_TEST_PASS_TEXT = "Evidence manifest schema self-test passed"
SELF_TEST_FAIL_TEXT = "Evidence manifest schema self-test failed"


def valid_manifest():
    return {
        "schemaVersion": "1.0",
        "taskId": "TASK-099",
        "evidenceSetId": "TASK-099-example",
        "source": "external_mt5",
        "externalEvidenceRoot": "E:/external/evidence",
        "files": [
            {
                "fileName": "TesterBacktest.html",
                "relativePath": "TesterBacktest.html",
                "evidenceType": "strategy_tester_html",
                "required": True,
                "expectedParser": "future_strategy_tester_html_parser",
                "expectedFields": ["expert", "symbol", "totalTrades"],
                "notes": "example only; no live trading readiness",
            }
        ],
        "mt5": {
            "terminalPath": "D:/MT5/terminal64.exe",
            "build": "unknown",
        },
        "strategyTester": {
            "expertName": "TradingSystem",
            "symbol": "EURUSD",
            "period": "M5",
            "dateFrom": "2024.01.01",
            "dateTo": "2024.01.31",
            "model": "Every tick",
            "deposit": "10000",
            "leverage": "1:100",
        },
        "expert": {
            "name": "TradingSystem",
        },
        "inputs": {
            "InpEnableTrading": False,
            "InpEnableRiskObservation": True,
            "InpPrintRuntimeSummary": True,
            "InpPrintNewBarLog": True,
            "InpNewBarLogEveryN": 1000,
            "InpPrintCoreLogStatsInSummary": True,
            "InpPrintSignalLog": True,
            "InpPrintSignalLogOnlyOnDirectionChange": True,
            "InpSignalLogEveryN": 1000,
            "InpPrintSignalLogStatsInSummary": True,
            "InpPrintRiskRejectLog": True,
            "InpRiskRejectLogEveryN": 1000,
            "InpPrintRiskLogStatsInSummary": True,
        },
        "noTradeAssertions": {
            "totalTrades": 0,
            "totalDeals": 0,
            "buyTrades": 0,
            "sellTrades": 0,
            "ordersOpened": 0,
            "positionsOpened": 0,
            "orderSendEvidence": False,
            "buySellEvidence": False,
            "executionAttempts": 0,
            "riskApproved": 0,
        },
        "parserExpectations": {
            "strategyTesterHtml": ["expert", "symbol", "period"],
            "logs": ["runtime summary", "riskApproved", "executionAttempts"],
        },
        "safetyAssertions": {
            "noRealTrading": True,
            "noProfitOptimization": True,
            "noLiveTradingReadinessClaim": True,
            "noRealTradingAllowedClaim": True,
            "noProfitabilityClaim": True,
        },
        "repositoryState": {
            "head": "cfda28f",
            "stableTag": "v0.4.0-evidence-archive-parser-entry-audit",
            "mq5Changed": False,
            "backtestSetsChanged": False,
            "backtestReportsChanged": False,
            "externalEvidenceCopiedIntoRepo": False,
            "mt5RunDuringTask": False,
        },
        "tags": {
            "stableTag": "v0.4.0-evidence-archive-parser-entry-audit",
            "stableTagTarget": "4478e3d",
        },
        "notes": [
            "no real trading",
            "no profit optimization",
            "not a profitability claim",
        ],
    }


def run_cli(manifest):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "tools" / "validate_evidence_manifest_schema.py"), str(path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )


def combined_output(result):
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def issues_for(manifest):
    return VALIDATOR.validate_manifest(manifest)


def expect_success(manifest):
    result = run_cli(manifest)
    return result.returncode == 0 and PASS_TEXT in combined_output(result)


def expect_failure(manifest, expected_text):
    issues = issues_for(manifest)
    output = "\n".join(issues)
    return bool(issues) and expected_text in output


def mutated(change):
    manifest = copy.deepcopy(valid_manifest())
    change(manifest)
    return manifest


def test_positive_valid_minimal_manifest():
    manifest = valid_manifest()
    return expect_success(manifest) and not issues_for(manifest)


def test_missing_top_level_required_field():
    return expect_failure(
        mutated(lambda manifest: manifest.pop("schemaVersion")),
        "schemaVersion",
    )


def test_files_item_missing_field():
    return expect_failure(
        mutated(lambda manifest: manifest["files"][0].pop("expectedParser")),
        "expectedParser",
    )


def test_invalid_evidence_type():
    return expect_failure(
        mutated(lambda manifest: manifest["files"][0].update({"evidenceType": "html"})),
        "evidenceType invalid value",
    )


def test_total_trades_non_zero():
    return expect_failure(
        mutated(lambda manifest: manifest["noTradeAssertions"].update({"totalTrades": 1})),
        "noTradeAssertions.totalTrades must be 0",
    )


def test_execution_attempts_non_zero():
    return expect_failure(
        mutated(lambda manifest: manifest["noTradeAssertions"].update({"executionAttempts": 1})),
        "noTradeAssertions.executionAttempts must be 0",
    )


def test_order_send_evidence_true():
    return expect_failure(
        mutated(lambda manifest: manifest["noTradeAssertions"].update({"orderSendEvidence": True})),
        "noTradeAssertions.orderSendEvidence must be false",
    )


def test_safety_assertions_false():
    return expect_failure(
        mutated(lambda manifest: manifest["safetyAssertions"].update({"noRealTrading": False})),
        "safetyAssertions.noRealTrading must be true",
    )


def test_repository_state_mq5_changed_true():
    return expect_failure(
        mutated(lambda manifest: manifest["repositoryState"].update({"mq5Changed": True})),
        "repositoryState.mq5Changed must be false",
    )


def test_repository_state_external_evidence_copied_true():
    return expect_failure(
        mutated(
            lambda manifest: manifest["repositoryState"].update(
                {"externalEvidenceCopiedIntoRepo": True}
            )
        ),
        "repositoryState.externalEvidenceCopiedIntoRepo must be false",
    )


def test_forbidden_interpretation_string():
    return expect_failure(
        mutated(lambda manifest: manifest["notes"].append("production trading ready")),
        "forbidden interpretation text",
    )


def test_allowed_no_live_trading_readiness_wording():
    manifest = mutated(
        lambda item: item["notes"].extend(
            [
                "no live trading readiness",
                "no real trading",
                "no profit optimization",
                "not a profitability claim",
            ]
        )
    )
    return not issues_for(manifest)


def main():
    checks = [
        ("positive valid minimal manifest failed", test_positive_valid_minimal_manifest),
        ("missing top-level required field was not detected", test_missing_top_level_required_field),
        ("files item missing field was not detected", test_files_item_missing_field),
        ("invalid evidenceType was not detected", test_invalid_evidence_type),
        ("totalTrades non-zero was not detected", test_total_trades_non_zero),
        ("executionAttempts non-zero was not detected", test_execution_attempts_non_zero),
        ("orderSendEvidence true was not detected", test_order_send_evidence_true),
        ("safetyAssertions false was not detected", test_safety_assertions_false),
        ("repositoryState mq5Changed true was not detected", test_repository_state_mq5_changed_true),
        (
            "repositoryState externalEvidenceCopiedIntoRepo true was not detected",
            test_repository_state_external_evidence_copied_true,
        ),
        ("forbidden interpretation string was not detected", test_forbidden_interpretation_string),
        (
            "allowed no live trading readiness wording was rejected",
            test_allowed_no_live_trading_readiness_wording,
        ),
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
