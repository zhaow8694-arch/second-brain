#!/usr/bin/env python3
"""Run the evidence parser pipeline in dry-run or batch-readiness mode."""

from __future__ import annotations

from pathlib import Path
import argparse
import importlib
import json
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT_DIR / "tools"
SETS_DIR = ROOT_DIR / "backtest" / "sets"
EXPECTED_SET_COUNT = 6
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

sys.path.insert(0, str(TOOLS_DIR))
HTML_PARSER = importlib.import_module("parse_strategy_tester_html_report")
LOG_PARSER = importlib.import_module("parse_mt5_log_no_trade_summary")
MANIFEST_GENERATOR = importlib.import_module("generate_evidence_manifest")
SET_PARSER = importlib.import_module("parse_backtest_set_params")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run parser-to-manifest pipeline checks without MT5 execution."
    )
    parser.add_argument(
        "--mode",
        choices=("dry-run", "validate-sets", "full"),
        default="full",
        help="Pipeline mode. full runs dry-run manifest synthesis and set parsing.",
    )
    return parser.parse_args()


def synthetic_html_text() -> str:
    return """<!doctype html>
    <html><body>
      <div>MetaQuotes-Demo (Build 5836)</div>
      <table>
        <tr><td>专家:</td><td>TradingSystem</td></tr>
        <tr><td>交易品种:</td><td>EURUSD</td></tr>
        <tr><td>期间:</td><td>M5 (2024.01.01 - 2024.01.31)</td></tr>
        <tr><td>初始存款:</td><td>10 000.00</td></tr>
        <tr><td>杠杆:</td><td>1:100</td></tr>
        <tr><td>交易总计:</td><td>0</td></tr>
        <tr><td>总成交:</td><td>0</td></tr>
        <tr><td>买入交易:</td><td>0</td></tr>
        <tr><td>卖出交易:</td><td>0</td></tr>
      </table>
      InpEnableTrading=false
      InpEnableRiskObservation=true
      InpPrintRuntimeSummary=true
    </body></html>"""


def synthetic_log_text() -> str:
    return """
testing of TradingSystem.ex5 from 2024.01.01 to 2024.01.31
EURUSD, M5
InpEnableTrading=false
InpEnableRiskObservation=true
riskApproved=0
executionAttempts=0
riskRejected=10
riskRejectTradingDisabled=10
no OrderSend evidence
no Buy( evidence
no Sell( evidence
"""


def dry_run_manifest_synthesis() -> dict[str, object]:
    html_payload, html_issues = HTML_PARSER.parse_report(
        synthetic_html_text(),
        expected_expert="TradingSystem",
    )
    if html_issues:
        raise ValueError("synthetic HTML parse issues: " + "; ".join(html_issues))

    log_payload, log_issues = LOG_PARSER.parse_log(
        synthetic_log_text(),
        expected_expert="TradingSystem",
    )
    if log_issues:
        raise ValueError("synthetic log parse issues: " + "; ".join(log_issues))

    files_payload = {
        "files": [
            {
                "fileName": "TesterBacktest.html",
                "relativePath": "TesterBacktest.html",
                "evidenceType": "strategy_tester_html",
                "required": True,
                "expectedParser": "tools/parse_strategy_tester_html_report.py",
                "expectedFields": [
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
                ],
                "notes": ["dry-run synthetic evidence only"],
            },
            {
                "fileName": "Experts.log",
                "relativePath": "Experts.log",
                "evidenceType": "experts_log",
                "required": True,
                "expectedParser": "tools/parse_mt5_log_no_trade_summary.py",
                "expectedFields": [
                    "riskApproved",
                    "executionAttempts",
                    "noTradeAssertions",
                ],
                "notes": ["dry-run synthetic evidence only"],
            },
        ]
    }
    repo_payload = {
        "head": "dry-run",
        "stableTag": "dry-run",
        "mq5Changed": False,
        "backtestSetsChanged": False,
        "backtestReportsChanged": False,
        "externalEvidenceCopiedIntoRepo": False,
        "mt5RunDuringTask": False,
    }
    tags_payload = {
        "stableTag": "dry-run",
        "stableTagTarget": "dry-run",
    }

    manifest = MANIFEST_GENERATOR.generate_manifest(
        html_payload,
        log_payload,
        files_payload,
        repo_payload,
        tags_payload,
        task_id="TASK-321-DRY-RUN",
        evidence_set_id="parser-pipeline-dry-run",
        external_root="external://dry-run/quarantine",
    )
    return manifest


def validate_backtest_sets() -> tuple[int, list[str]]:
    issues: list[str] = []
    set_files = sorted(SETS_DIR.glob("*.set")) if SETS_DIR.exists() else []
    if len(set_files) != EXPECTED_SET_COUNT:
        issues.append(
            f"expected {EXPECTED_SET_COUNT} backtest set files, found {len(set_files)}"
        )
    for set_path in set_files:
        payload = SET_PARSER.parse_set_file(set_path)
        if payload["issues"]:
            issues.extend(f"{set_path.name}: {issue}" for issue in payload["issues"])
        if not payload.get("noTradeAssertions", {}).get("passed"):
            issues.append(f"{set_path.name}: no-trade assertions failed")
    return len(set_files), issues


def run_parser_self_tests() -> list[str]:
    tests = (
        "test_parse_strategy_tester_html_report.py",
        "test_parse_mt5_log_no_trade_summary.py",
        "test_generate_evidence_manifest.py",
        "test_parse_mql5_compile_log.py",
        "test_parse_backtest_set_params.py",
        "test_parse_backtest_runtime_summary.py",
    )
    issues: list[str] = []
    for test_name in tests:
        command = [sys.executable, str(TOOLS_DIR / test_name)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = (completed.stdout + completed.stderr).strip().splitlines()
            summary = detail[-1] if detail else "no output"
            issues.append(f"{test_name} failed: {summary}")
    return issues


def main():
    args = parse_args()
    issues: list[str] = []

    if args.mode in {"dry-run", "full"}:
        try:
            manifest = dry_run_manifest_synthesis()
        except (ValueError, MANIFEST_GENERATOR.ManifestGenerationError) as error:
            issues.append(f"dry-run manifest synthesis failed: {error}")
        else:
            if manifest.get("schemaVersion") != "1.0":
                issues.append("dry-run manifest missing schemaVersion 1.0")
            if not manifest.get("noTradeAssertions"):
                issues.append("dry-run manifest missing noTradeAssertions")

    if args.mode in {"validate-sets", "full"}:
        _, set_issues = validate_backtest_sets()
        issues.extend(set_issues)

    if args.mode == "full":
        issues.extend(run_parser_self_tests())

    if issues:
        print("Evidence parser pipeline failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Evidence parser pipeline passed")
    print(f"mode={args.mode}")
    print("dry_run_manifest_synthesis=true")
    print("backtest_sets_parsed=true")
    print("parser_self_tests=true")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())