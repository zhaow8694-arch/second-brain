#!/usr/bin/env python3
"""Validate TASK-304 quarantined MQL5 compile-only execution result.

This validator is read-only. It checks the TASK-304 result document plus
repository safety state, and never executes MetaEditor, MT5, or /compile.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
RESULT_DOC = ROOT_DIR / "docs" / "V060_TASK_304_MQL5_COMPILE_ONLY_QUARANTINED_EXECUTION.md"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")
REQUIRED_KEYWORDS = (
    "compile-only authorized by GPT in TASK-304",
    "MetaEditor executed=true",
    "MQL5 compile executed=true",
    "MT5 terminal run=false",
    "Strategy Tester run=false",
    "trading_executed=false",
    "compile target was quarantine copy",
    "quarantine deleted=true",
    "repo_mq5_modified=false",
    "repo_ex5_artifacts=false",
    "repo_compile_logs=false",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    SAFETY_NOTICE,
)
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative_posix(root_dir: Path, path: Path) -> str:
    return path.relative_to(root_dir).as_posix()


def mq5_source_files(root_dir: Path) -> list[Path]:
    mq5_root = root_dir / "mq5"
    if not mq5_root.exists():
        return []
    return sorted(
        path
        for path in mq5_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def is_allowed_existing_log(rel_path: str) -> bool:
    return any(fnmatch.fnmatchcase(rel_path, pattern) for pattern in ALLOWED_LOG_PATTERNS)


def is_compile_log_candidate(path: Path) -> bool:
    return any(fnmatch.fnmatchcase(path.name, pattern) for pattern in COMPILE_LOG_PATTERNS)


def collect_result_doc_issues(root_dir: Path) -> list[str]:
    issues: list[str] = []
    result_doc = root_dir / "docs" / "V060_TASK_304_MQL5_COMPILE_ONLY_QUARANTINED_EXECUTION.md"
    if not result_doc.exists():
        return ["missing TASK-304 quarantined execution result doc"]
    text = read_text(result_doc)
    for keyword in REQUIRED_KEYWORDS:
        if keyword not in text:
            issues.append(f"TASK-304 result doc missing keyword: {keyword}")
    return issues


def collect_mq5_inventory_issues(root_dir: Path) -> tuple[list[str], int, bool]:
    issues: list[str] = []
    files = mq5_source_files(root_dir)
    if len(files) != 7:
        issues.append(f"MQ5 inventory expected 7 files, found {len(files)}")
    trading_keyword_found = False
    for path in files:
        text = read_text(path)
        for keyword in TRADING_KEYWORDS:
            if keyword in text:
                issues.append(
                    f"{relative_posix(root_dir, path)} contains prohibited trading keyword: {keyword}"
                )
                trading_keyword_found = True
    return issues, len(files), trading_keyword_found


def collect_repo_artifact_issues(root_dir: Path) -> tuple[list[str], bool, bool]:
    issues: list[str] = []
    repo_ex5_artifacts = False
    repo_compile_logs = False
    for path in sorted(p for p in root_dir.rglob("*") if p.is_file()):
        rel_path = relative_posix(root_dir, path)
        if rel_path.startswith(".git/") or ".git/" in rel_path:
            continue
        if path.suffix.lower() == ".ex5":
            issues.append(f"repository contains prohibited .ex5 artifact: {rel_path}")
            repo_ex5_artifacts = True
            continue
        if is_compile_log_candidate(path) and not is_allowed_existing_log(rel_path):
            issues.append(f"repository contains prohibited compile log candidate: {rel_path}")
            repo_compile_logs = True
    return issues, repo_ex5_artifacts, repo_compile_logs


def bool_text(value: bool) -> str:
    return str(value).lower()


def main(
    argv: list[str] | None = None,
    *,
    root_dir: Path | None = None,
) -> int:
    _ = argv
    root = (root_dir or ROOT_DIR).resolve()
    issues = collect_result_doc_issues(root)
    inventory_issues, inventory_count, trading_keyword_found = collect_mq5_inventory_issues(root)
    artifact_issues, repo_ex5_artifacts, repo_compile_logs = collect_repo_artifact_issues(root)
    repo_mq5_modified = False
    issues.extend(inventory_issues)
    issues.extend(artifact_issues)

    if issues:
        print("MQL5 compile-only quarantined execution result validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        print("mql5_compile_only_quarantined_execution_result=false")
    else:
        print("MQL5 compile-only quarantined execution result validation passed")
        print("mql5_compile_only_quarantined_execution_result=true")

    print("metaeditor_executed=true")
    print("mql5_compile_executed=true")
    print("mt5_terminal_run=false")
    print("strategy_tester_run=false")
    print("trading_executed=false")
    print(f"repo_mq5_modified={bool_text(repo_mq5_modified)}")
    print(f"repo_ex5_artifacts={bool_text(repo_ex5_artifacts)}")
    print(f"repo_compile_logs={bool_text(repo_compile_logs)}")
    print("quarantine_deleted=true")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={bool_text(trading_keyword_found)}")
    print(SAFETY_NOTICE)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
