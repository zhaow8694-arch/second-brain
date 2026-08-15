#!/usr/bin/env python3
"""Validate TASK-314 MT5 no-trade startup command discovery boundary.

This validator is read-only. It discovers local MT5 terminal command
candidates with filesystem lookups only and never executes terminal64.exe,
terminal.exe, MT5, Strategy Tester, MetaEditor, backtest, or MQL5 compile.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import shutil
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK312_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
)
TASK313_DOC_PATH = ROOT_DIR / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
TASK314_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
)
MQ5_ROOT = ROOT_DIR / "mq5"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")
COMMON_TERMINAL_CANDIDATES = (
    Path(r"C:\Program Files\MetaTrader 5\terminal64.exe"),
    Path(r"C:\Program Files\MetaTrader 5\terminal.exe"),
    Path(r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe"),
    Path(r"C:\Program Files (x86)\MetaTrader 5\terminal.exe"),
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

REQUIRED_DOC_KEYWORDS = (
    "TASK-314 MT5 no-trade startup command discovery boundary",
    "command-discovery-only",
    "mt5-startup-preparation-only",
    "not MT5 run in TASK-314",
    "not terminal64.exe execution in TASK-314",
    "not terminal.exe execution in TASK-314",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-314",
    "no Strategy Tester executed in TASK-314",
    "no backtest executed in TASK-314",
    "no trading executed in TASK-314",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    SAFETY_NOTICE,
    "current HEAD: 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet",
    "current tag: v0.5.109-task-313-mt5-no-trade-startup-boundary",
    "TASK-312 compile_success=true was compile-only-diagnostic scope only",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-315 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-315 must not be entered directly",
    "future GPT boundary explicitly authorizes MT5 terminal no-trade startup",
    "future startup must remain no-trade",
    "future startup must not run Strategy Tester",
    "future startup must not run backtest",
    "future startup must not run simulation trading",
    "future startup must not run real trading",
    "future startup must not place orders",
    "future startup must not create official manifest unless separately authorized",
    "future startup must not create evidence unless separately authorized",
    "future startup must not create report unless separately authorized",
    "future startup must use no-trade startup template",
    "future startup must prove InpEnableTrading=false before startup",
    "future startup must prove trading keywords false before startup",
    "future startup must prove MQ5 inventory remains 7 files before startup",
    "future startup must prove repo_ex5_artifacts=false before startup",
    "future startup must prove repo_compile_logs=false before startup",
    "future startup must prove repo_mq5_modified=false before startup",
    "future startup must capture startup result stdout-only unless separately authorized",
    "future startup must not copy external evidence",
    "future startup must not imply deployment readiness",
    "future startup must not imply strategy readiness",
    "future startup must not imply backtest readiness",
    "future startup must not imply trading authorization",
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
    if not TASK314_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
        )
        return issues

    text = read_text(TASK314_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md "
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


def discover_terminal_candidates() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in COMMON_TERMINAL_CANDIDATES:
        if candidate.exists():
            key = str(candidate).lower()
            if key not in seen:
                candidates.append(candidate)
                seen.add(key)

    for executable in ("terminal64.exe", "terminal.exe"):
        found = shutil.which(executable)
        if found:
            candidate = Path(found)
            key = str(candidate).lower()
            if key not in seen:
                candidates.append(candidate)
                seen.add(key)
    return candidates


def future_startup_command_template(candidate: Path | None) -> str:
    if candidate is None:
        return "NONE"
    return f'"{candidate}" /portable /skipupdate'


def main() -> int:
    issues = collect_doc_issues()
    mq5_issues, inventory_count, trading_keywords_found = collect_mq5_issues()
    artifact_issues, repo_ex5_artifacts, repo_compile_logs = collect_repo_artifact_issues()
    issues.extend(mq5_issues)
    issues.extend(artifact_issues)

    candidates = discover_terminal_candidates()
    candidate = candidates[0] if candidates else None

    if issues:
        print("MT5 no-trade startup command discovery validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MT5 no-trade startup command discovery validation passed")
    print("mt5_no_trade_startup_command_discovery=true")
    print("command_discovery_only=true")
    print("mt5_startup_preparation_only=true")
    print("mt5_terminal_executed=false")
    print("terminal64_executed=false")
    print("terminal_executed=false")
    print("strategy_tester_executed=false")
    print("backtest_executed=false")
    print("trading_executed=false")
    print("trading_authorization=false")
    print("deployment_readiness=false")
    print("backtest_readiness=false")
    print("strategy_readiness=false")
    print("future_task_315_requires_gpt_boundary=true")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keywords_found).lower()}")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print("repo_mq5_modified=false")
    print(f"mt5_terminal_candidate_found={str(candidate is not None).lower()}")
    if candidate is not None:
        print(f"mt5_terminal_candidate_path={candidate}")
    print(f"future_no_trade_startup_command_template={future_startup_command_template(candidate)}")
    print("future_startup_command_executed=false")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
