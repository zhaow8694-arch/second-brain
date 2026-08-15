#!/usr/bin/env python3
"""Validate TASK-305 MQL5 compile-only failure diagnostic boundary.

This validator is read-only. It does not execute MetaEditor, MT5, MQL5
compile, Strategy Tester, or any artifact-producing command.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK305_DOC_PATH = ROOT_DIR / "docs" / "V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md"
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
    "TASK-305 MQL5 compile-only failure diagnostic capture",
    "diagnostic-only",
    "not compile success",
    "not TASK-304 success result",
    "compile_exit_code=1 was observed in TASK-304",
    "TASK-305 may re-run MetaEditor compile-only only against quarantine copy",
    "compile log must be stdout-only",
    "compile log must not be saved to repository",
    "no .ex5 artifact generated in repository",
    "no compile log generated in repository",
    "no MT5 terminal run",
    "no Strategy Tester run",
    "no backtest",
    "no trading",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "current HEAD: 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet",
    "current tag: v0.5.100-task-303-v060-compile-only-execution-authorization",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    SAFETY_NOTICE,
    "TASK-306 must not be entered directly",
    "future TASK-306 must be separately authorized by GPT before any MQ5 fixes or compile retry",
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
    if not TASK305_DOC_PATH.exists():
        return ["missing required docs file: docs/V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md"]
    text = read_text(TASK305_DOC_PATH)
    return [
        f"docs/V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md missing keyword: {keyword}"
        for keyword in REQUIRED_DOC_KEYWORDS
        if keyword not in text
    ]


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
        print("MQL5 compile-only failure diagnostic validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MQL5 compile-only failure diagnostic validation passed")
    print("mql5_compile_only_failure_diagnostic=true")
    print("diagnostic_only=true")
    print("compile_success=false")
    print("task304_success_result_created=false")
    print("metaeditor_execution_allowed_for_diagnostic=true")
    print("compile_log_stdout_only=true")
    print("compile_log_saved_to_repo=false")
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
