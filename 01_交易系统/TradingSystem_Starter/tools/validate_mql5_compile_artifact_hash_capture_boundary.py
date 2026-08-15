#!/usr/bin/env python3
"""Validate TASK-310 MQL5 compile artifact hash capture boundary.

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
TASK310_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md"
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
    "TASK-310 MQL5 compile artifact hash capture diagnostic",
    "artifact-hash-capture-diagnostic-only",
    "not success reclassification",
    "not TASK-304 success result",
    "TASK-310 may re-run MetaEditor compile-only only against quarantine copy",
    "artifact hash must be stdout-only",
    "artifact hash must not be saved to repository",
    "quarantine .ex5 must not be copied to repository",
    "compile log must remain stdout-only",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "repo_mq5_modified=false",
    "success_reclassification_done=false",
    "task304_success_result_created=false",
    "compile_success=false",
    "future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix",
    "TASK-311 must not be entered directly",
    "no MT5 terminal run",
    "no Strategy Tester run",
    "no backtest",
    "no trading",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: f31b85e TASK-309 create MQL5 compile-only success reclassification boundary",
    "current tag: v0.5.105-task-309-mql5-compile-success-reclassification-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    SAFETY_NOTICE,
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
            "missing required docs file: "
            "docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md"
        )
        return issues

    text = read_text(TASK310_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md "
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
        print("MQL5 compile artifact hash capture boundary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQL5 compile artifact hash capture boundary validation passed")
    print("mql5_compile_artifact_hash_capture_boundary=true")
    print("artifact_hash_capture_diagnostic_only=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("success_reclassification_done=false")
    print("task304_success_result_created=false")
    print("compile_success=false")
    print("artifact_hash_stdout_only=true")
    print("artifact_hash_saved_to_repo=false")
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
