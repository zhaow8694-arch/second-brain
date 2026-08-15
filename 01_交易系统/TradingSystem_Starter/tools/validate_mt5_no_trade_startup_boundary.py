#!/usr/bin/env python3
"""Validate TASK-313 MT5 no-trade startup boundary.

This validator is read-only. It validates the boundary document and repository
safety state without executing MT5, terminal startup, Strategy Tester, backtest,
MetaEditor, or MQL5 compile.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK312_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
)
TASK313_DOC_PATH = ROOT_DIR / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
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
    "TASK-313 MT5 terminal no-trade startup boundary packet",
    "planning-only",
    "mt5-startup-boundary-only",
    "future MT5 terminal no-trade startup candidate",
    "not MT5 run in TASK-313",
    "not terminal64.exe execution in TASK-313",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "not evidence generation authorization",
    "not manifest generation authorization",
    "not report generation authorization",
    "no MT5 terminal run executed in TASK-313",
    "no Strategy Tester executed in TASK-313",
    "no backtest executed in TASK-313",
    "no trading executed in TASK-313",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    SAFETY_NOTICE,
    "current HEAD: efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision",
    "current tag: v0.5.108-task-312-mql5-compile-success-reclassification-decision",
    "TASK-312 compile_success=true was compile-only-diagnostic scope only",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-314 must not be entered directly",
    "future GPT boundary explicitly authorizes MT5 terminal no-trade startup",
    "future task must remain no-trade",
    "future task must not run Strategy Tester",
    "future task must not run backtest",
    "future task must not run simulation trading",
    "future task must not run real trading",
    "future task must not place orders",
    "future task must not create official manifest unless separately authorized",
    "future task must not create evidence unless separately authorized",
    "future task must not create report unless separately authorized",
    "future task must use a no-trade config",
    "future task must prove InpEnableTrading=false before startup",
    "future task must prove trading keywords false before startup",
    "future task must prove MQ5 inventory remains 7 files before startup",
    "future task must prove repo_ex5_artifacts=false before startup",
    "future task must prove repo_compile_logs=false before startup",
    "future task must prove repo_mq5_modified=false before startup",
    "future task must capture terminal startup result stdout-only unless separately authorized",
    "future task must not copy external evidence",
    "future task must not imply deployment readiness",
    "future task must not imply strategy readiness",
    "future task must not imply backtest readiness",
    "future task must not imply trading authorization",
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
    if not TASK312_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
        )
    if not TASK313_DOC_PATH.exists():
        issues.append(
            "missing required docs file: docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
        )
        return issues

    text = read_text(TASK313_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md "
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
        print("MT5 no-trade startup boundary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MT5 no-trade startup boundary validation passed")
    print("mt5_no_trade_startup_boundary=true")
    print("mt5_startup_boundary_only=true")
    print("mt5_terminal_executed=false")
    print("terminal64_executed=false")
    print("strategy_tester_executed=false")
    print("backtest_executed=false")
    print("trading_executed=false")
    print("trading_authorization=false")
    print("deployment_readiness=false")
    print("backtest_readiness=false")
    print("strategy_readiness=false")
    print("future_task_314_requires_gpt_boundary=true")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keywords_found).lower()}")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print("repo_mq5_modified=false")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
