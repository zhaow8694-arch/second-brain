#!/usr/bin/env python3
"""Validate TASK-311 MQL5 compile success reclassification decision boundary.

This validator is read-only. It does not execute MetaEditor, MT5, MQL5
compile, Strategy Tester, or any artifact-producing command.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK309_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md"
)
TASK310_DOC_PATH = ROOT_DIR / "docs" / "V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md"
TASK311_DOC_PATH = (
    ROOT_DIR
    / "docs"
    / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
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

REQUIRED_DOC_KEYWORDS = (
    "TASK-311 MQL5 compile success reclassification decision boundary",
    "planning-only",
    "success-reclassification-decision-boundary-only",
    "not compile execution",
    "not MetaEditor execution in TASK-311",
    "not MT5 run",
    "not Strategy Tester",
    "not backtest",
    "not trading",
    "not success reclassification in TASK-311",
    "TASK-310 observed artifact_hash_captured=true",
    "TASK-310 observed quarantine_ex5_artifact_size_bytes=70178",
    "TASK-310 observed compile_exit_code=1",
    "TASK-310 observed compile_log_semantic_success=true",
    "TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly",
    "TASK-310 compile_success=false",
    "TASK-310 success_reclassification_done=false",
    "TASK-310 task304_success_result_created=false",
    "TASK-310 repo_ex5_artifacts=false",
    "TASK-310 repo_compile_logs=false",
    "TASK-310 repo_mq5_modified=false",
    "TASK-310 artifact hash was stdout-only and must not be stored in repository",
    "TASK-311 does not store artifact hash",
    "TASK-311 does not create TASK-304 success result doc",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    SAFETY_NOTICE,
    "current HEAD: 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic",
    "current tag: v0.5.106-task-310-mql5-compile-artifact-hash-capture",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry",
    "TASK-312 must not be entered directly",
    "future GPT boundary explicitly authorizes success reclassification decision",
    "future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash",
    "future task must not store artifact hash in repository unless GPT explicitly authorizes hash recording",
    "future task must keep artifact metadata stdout-only unless separately authorized",
    "future task must prove compile_log_semantic_success=true",
    "future task must prove compile_log_errors=0",
    "future task must prove quarantine_ex5_artifact_detected=true",
    "future task must prove quarantine_ex5_artifact_count>=1",
    "future task must prove quarantine artifact hash is captured",
    "future task must prove quarantine artifact size is captured",
    "future task must delete quarantine directory before completion",
    "future task must prove quarantine_deleted=true",
    "future task must prove repo_ex5_artifacts=false after cleanup",
    "future task must prove repo_compile_logs=false after cleanup",
    "future task must prove repo_mq5_modified=false after cleanup",
    "future task must prove trading_keywords=false after cleanup",
    "future task must prove MQ5 inventory remains 7 files",
    "future task must not run MT5 terminal",
    "future task must not run Strategy Tester",
    "future task must not backtest",
    "future task must not trade",
    "future task must not create official manifest",
    "future task must not create evidence",
    "future task must not create report",
    "future task must not copy external evidence",
    "future success reclassification must remain compile-only and no-trade",
    "future success reclassification must not imply deployment readiness",
    "future success reclassification must not imply strategy readiness",
    "future success reclassification must not imply backtest readiness",
    "future success reclassification must not imply trading authorization",
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
    if not TASK309_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md"
        )
    if not TASK310_DOC_PATH.exists():
        issues.append(
            "missing required docs file: docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md"
        )
    if not TASK311_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
        )
        return issues

    text = read_text(TASK311_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md "
        f"missing keyword: {keyword}"
        for keyword in REQUIRED_DOC_KEYWORDS
        if keyword not in text
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
        print("MQL5 compile success reclassification decision boundary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQL5 compile success reclassification decision boundary validation passed")
    print("mql5_compile_success_reclassification_decision_boundary=true")
    print("success_reclassification_decision_boundary_only=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("success_reclassification_done=false")
    print("task304_success_result_created=false")
    print("compile_exit_code=1")
    print("compile_log_semantic_success=true")
    print("previous_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly")
    print("compile_success=false")
    print("artifact_hash_stored_in_repo=false")
    print("future_task_312_requires_gpt_boundary=true")
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
