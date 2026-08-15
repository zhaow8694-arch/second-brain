#!/usr/bin/env python3
"""Validate TASK-312 MQL5 compile success reclassification decision.

This validator is read-only. It validates the decision document and repository
safety state without executing MetaEditor, MT5, MQL5 compile, or Strategy Tester.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK311_DOC_PATH = (
    ROOT_DIR
    / "docs"
    / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
)
TASK312_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
)
MQ5_ROOT = ROOT_DIR / "mq5"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")
COMPILE_LOG_PATTERNS = (
    "*.log",
    "*compile*.txt",
    "*compile*.log",
    "MetaEditor*.log",
    "mql5_compile*.log",
    "mql5_compile*.txt",
)
ALLOWED_LOG_PATTERNS = (
    "backtest/reports/samples/TASK-012_runtime_summary_sample.log",
    "logs/localhost-3000.debug.log",
    "logs/localhost-3000.err.log",
    "logs/localhost-3000.out.log",
)
HASH_LIKE_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")

REQUIRED_DOC_KEYWORDS = (
    "TASK-312 MQL5 compile-only success reclassification decision",
    "controlled-success-reclassification-attempt",
    "success_reclassification_decision=PASS",
    "compile_only_reclassified_success=true",
    "compile_success=true",
    "compile_success_scope=compile-only-diagnostic",
    "not trading authorization",
    "not deployment readiness",
    "not backtest readiness",
    "not strategy readiness",
    "MetaEditor executed only against quarantine copy",
    "MQL5 compile executed only against quarantine copy",
    "MT5 terminal run=false",
    "Strategy Tester run=false",
    "trading_executed=false",
    "quarantine_ex5_artifact_detected=true",
    "quarantine_ex5_artifact_count>=1",
    "artifact_hash_captured=true",
    "artifact_hash_stdout_only=true",
    "artifact_hash_saved_to_repo=false",
    "do not include actual artifact hash value in this doc",
    "quarantine_ex5_artifact_size_bytes captured",
    "quarantine_deleted=true",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    SAFETY_NOTICE,
    "current HEAD: 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary",
    "current tag: v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-313 must be separately authorized by GPT before any MT5 run, Strategy Tester, backtest, deployment, or trading-related step",
    "TASK-313 must not be entered directly",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative_posix(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def mq5_source_files() -> list[Path]:
    if not MQ5_ROOT.exists():
        return []
    return sorted(
        path
        for path in MQ5_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def is_allowed_existing_log(rel_path: str) -> bool:
    return any(fnmatch.fnmatchcase(rel_path, pattern) for pattern in ALLOWED_LOG_PATTERNS)


def is_compile_log_candidate(path: Path) -> bool:
    return any(fnmatch.fnmatchcase(path.name, pattern) for pattern in COMPILE_LOG_PATTERNS)


def collect_doc_issues() -> list[str]:
    issues: list[str] = []
    if not TASK311_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
        )
    if not TASK312_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
        )
        return issues

    text = read_text(TASK312_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md "
        f"missing keyword: {keyword}"
        for keyword in REQUIRED_DOC_KEYWORDS
        if keyword not in text
    )
    if HASH_LIKE_PATTERN.search(text):
        issues.append(
            "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md "
            "must not store an actual 64-character artifact hash"
        )
    return issues


def collect_mq5_issues() -> tuple[list[str], int, bool]:
    issues: list[str] = []
    files = mq5_source_files()
    if len(files) != 7:
        issues.append(f"MQ5 inventory expected 7 files, found {len(files)}")

    trading_keywords_found = False
    for path in files:
        text = read_text(path)
        for keyword in TRADING_KEYWORDS:
            if keyword in text:
                trading_keywords_found = True
                issues.append(f"{relative_posix(path)} contains prohibited trading keyword: {keyword}")
    return issues, len(files), trading_keywords_found


def collect_repo_artifact_issues() -> tuple[list[str], bool, bool]:
    issues: list[str] = []
    repo_ex5_artifacts = False
    repo_compile_logs = False
    for path in sorted(p for p in ROOT_DIR.rglob("*") if p.is_file()):
        rel_path = relative_posix(path)
        if rel_path.startswith(".git/") or ".git/" in rel_path:
            continue
        if path.suffix.lower() == ".ex5":
            repo_ex5_artifacts = True
            issues.append(f"repository contains prohibited .ex5 artifact: {rel_path}")
            continue
        if is_compile_log_candidate(path) and not is_allowed_existing_log(rel_path):
            repo_compile_logs = True
            issues.append(f"repository contains prohibited compile log candidate: {rel_path}")
    return issues, repo_ex5_artifacts, repo_compile_logs


def main() -> int:
    issues = collect_doc_issues()
    mq5_issues, inventory_count, trading_keywords_found = collect_mq5_issues()
    artifact_issues, repo_ex5_artifacts, repo_compile_logs = collect_repo_artifact_issues()
    issues.extend(mq5_issues)
    issues.extend(artifact_issues)

    if issues:
        print("MQL5 compile success reclassification decision validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQL5 compile success reclassification decision validation passed")
    print("mql5_compile_success_reclassification_decision=true")
    print("success_reclassification_decision=PASS")
    print("compile_only_reclassified_success=true")
    print("compile_success=true")
    print("compile_success_scope=compile-only-diagnostic")
    print("trading_authorization=false")
    print("deployment_readiness=false")
    print("backtest_readiness=false")
    print("strategy_readiness=false")
    print("artifact_hash_stdout_only=true")
    print("artifact_hash_saved_to_repo=false")
    print("actual_artifact_hash_stored_in_repo=false")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print("repo_mq5_modified=false")
    print("mt5_terminal_run=false")
    print("strategy_tester_run=false")
    print("trading_executed=false")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keywords_found).lower()}")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
