#!/usr/bin/env python3
"""Validate TASK-308 MQL5 compile diagnostic artifact proof boundary.

This validator is read-only. It does not execute MetaEditor, MT5, MQL5
compile, Strategy Tester, or any artifact-producing command.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK307_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md"
)
TASK308_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md"
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
    "TASK-308 MQL5 compile diagnostic artifact proof and success reclassification boundary",
    "planning-only",
    "diagnostic-proof-boundary-only",
    "not compile execution",
    "not MetaEditor execution in TASK-308",
    "not MT5 run",
    "not Strategy Tester",
    "not backtest",
    "not trading",
    "not success reclassification in TASK-308",
    "TASK-307 observed quarantine_ex5_artifact_detected=true",
    "TASK-307 observed compile_log_semantic_success=true",
    "TASK-307 observed compile_exit_code=1",
    "TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
    "TASK-307 compile_success=false",
    "TASK-307 task304_success_result_created=false",
    "TASK-308 does not create TASK-304 success result doc",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    SAFETY_NOTICE,
    "current HEAD: 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification",
    "current tag: v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification",
    "TASK-309 must not be entered directly",
    "future GPT boundary explicitly authorizes success reclassification attempt",
    "future task may re-run MetaEditor compile-only only against quarantine copy",
    "future task must capture quarantine .ex5 metadata before deletion",
    "future task must output artifact metadata to stdout only",
    "future task must not copy .ex5 into repository",
    "future task must not save compile log into repository",
    "future task must compute quarantine artifact hash before deleting quarantine directory",
    "future task must output quarantine artifact size",
    "future task must output quarantine artifact path as temporary path only",
    "future task must delete quarantine directory before completion",
    "future task must prove repo_ex5_artifacts=false after cleanup",
    "future task must prove repo_compile_logs=false after cleanup",
    "future task must prove repo_mq5_modified=false after cleanup",
    "future task must prove trading_keywords=false after cleanup",
    "future task must prove MQ5 inventory remains 7 files",
    "future task must still not run MT5 terminal",
    "future task must still not run Strategy Tester",
    "future task must still not trade",
    "future task must not create official manifest / evidence / report unless separately authorized",
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
    if not TASK307_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md"
        )
    if not TASK308_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md"
        )
        return issues

    text = read_text(TASK308_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md "
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
        print("MQL5 compile diagnostic artifact proof boundary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQL5 compile diagnostic artifact proof boundary validation passed")
    print("mql5_compile_diagnostic_artifact_proof_boundary=true")
    print("diagnostic_proof_boundary_only=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("success_reclassification_done=false")
    print("task304_success_result_created=false")
    print("compile_exit_code=1")
    print("compile_log_semantic_success=true")
    print("previous_classification=compiled_artifact_with_metaeditor_exit_code_anomaly")
    print("future_task_309_requires_gpt_boundary=true")
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
