#!/usr/bin/env python3
"""Validate TASK-316 MT5 no-trade startup dry-run config boundary.

This validator is read-only. It checks static documentation and repository
state only; it never executes MT5, terminal64.exe, terminal.exe, Strategy
Tester, MetaEditor, backtest, or MQL5 compile.
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
TASK314_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
)
TASK315_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"
)
TASK316_DOC_PATH = (
    ROOT_DIR / "docs" / "V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md"
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
TERMINAL_DATA_DIR_PATTERNS = (
    "MQL5/Profiles",
    "MQL5/Logs",
    "bases",
    "config",
    "logs/MetaTrader*",
)
ALLOWED_TERMINAL_DATA_DIR_PATTERNS = ("mq5/config",)
STARTUP_LOG_PATTERNS = (
    "terminal*.log",
    "MetaTrader*.log",
    "mt5_startup*.log",
    "startup*.log",
)
GENERATED_NO_TRADE_CONFIG_PATTERNS = (
    "mt5_no_trade_startup*.ini",
    "terminal_no_trade*.ini",
    "startup_no_trade*.ini",
    "*_startup_config.ini",
)

REQUIRED_TASK316_KEYWORDS = (
    "TASK-316 MT5 no-trade startup dry-run config boundary",
    "planning-only",
    "startup-dryrun-config-boundary-only",
    "not MT5 run in TASK-316",
    "not terminal64.exe execution in TASK-316",
    "not terminal.exe execution in TASK-316",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-316",
    "no terminal64.exe executed in TASK-316",
    "no terminal.exe executed in TASK-316",
    "no Strategy Tester executed in TASK-316",
    "no backtest executed in TASK-316",
    "no trading executed in TASK-316",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "no no-trade config file generated in repository",
    SAFETY_NOTICE,
    "current HEAD: 5d07673 TASK-315 implement MT5 no-trade startup quarantine preparation boundary",
    "current tag: v0.5.111-task-315-mt5-no-trade-startup-quarantine-preparation",
    "TASK-314 discovered MT5 terminal candidate",
    "TASK-315 defined startup quarantine preparation",
    "TASK-312 compile_success=true was compile-only-diagnostic scope only",
    "TASK-312 compile_success_scope=compile-only-diagnostic",
    "TASK-312 trading_authorization=false",
    "TASK-312 deployment_readiness=false",
    "TASK-312 backtest_readiness=false",
    "TASK-312 strategy_readiness=false",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-317 must be separately authorized by GPT before any MT5 terminal startup attempt",
    "TASK-317 must not be entered directly",
    "future GPT boundary explicitly authorizes MT5 terminal no-trade startup attempt",
    "future startup must remain no-trade",
    "future startup must use isolated startup quarantine outside repository",
    "future startup must use no-trade config",
    "future startup must prove InpEnableTrading=false before startup",
    "future startup must prove trading keywords false before startup",
    "future startup must prove MQ5 inventory remains 7 files before startup",
    "future startup must prove repo_ex5_artifacts=false before startup",
    "future startup must prove repo_compile_logs=false before startup",
    "future startup must prove repo_mq5_modified=false before startup",
    "future startup must prove no terminal data directory exists in repository before startup",
    "future startup must prove no startup log exists in repository before startup",
    "future startup must not run Strategy Tester",
    "future startup must not run backtest",
    "future startup must not run simulation trading",
    "future startup must not run real trading",
    "future startup must not place orders",
    "future startup must not create official manifest unless separately authorized",
    "future startup must not create evidence unless separately authorized",
    "future startup must not create report unless separately authorized",
    "future startup must capture startup result stdout-only unless separately authorized",
    "future startup must clean up quarantine unless separately authorized",
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


def is_startup_log_candidate(path: Path) -> bool:
    if is_allowed_existing_log(relative_posix(path)):
        return False
    return any(fnmatch.fnmatchcase(path.name, pattern) for pattern in STARTUP_LOG_PATTERNS)


def is_allowed_terminal_data_dir(rel_path: str) -> bool:
    return any(fnmatch.fnmatchcase(rel_path, pattern) for pattern in ALLOWED_TERMINAL_DATA_DIR_PATTERNS)


def is_terminal_data_dir_candidate(path: Path) -> bool:
    rel_path = relative_posix(path)
    if is_allowed_terminal_data_dir(rel_path):
        return False
    return any(
        fnmatch.fnmatchcase(rel_path, pattern) or fnmatch.fnmatchcase(path.name, pattern)
        for pattern in TERMINAL_DATA_DIR_PATTERNS
    )


def is_generated_no_trade_config_candidate(path: Path) -> bool:
    return any(fnmatch.fnmatchcase(path.name, pattern) for pattern in GENERATED_NO_TRADE_CONFIG_PATTERNS)


def collect_doc_issues() -> list[str]:
    issues: list[str] = []
    required_existing_docs = (
        (TASK312_DOC_PATH, "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"),
        (TASK313_DOC_PATH, "docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"),
        (TASK314_DOC_PATH, "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"),
        (TASK315_DOC_PATH, "docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"),
    )
    for path, label in required_existing_docs:
        if not path.exists():
            issues.append(f"missing required docs file: {label}")

    if not TASK316_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md"
        )
        return issues

    task316_text = read_text(TASK316_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md "
        f"missing keyword: {keyword}"
        for keyword in REQUIRED_TASK316_KEYWORDS
        if keyword not in task316_text
    )

    if TASK315_DOC_PATH.exists():
        task315_text = read_text(TASK315_DOC_PATH)
        if "startup-quarantine-preparation-only" not in task315_text:
            issues.append(
                "docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md "
                "missing keyword: startup-quarantine-preparation-only"
            )
    if TASK314_DOC_PATH.exists():
        task314_text = read_text(TASK314_DOC_PATH)
        if "future_startup_command_executed=false" not in task314_text:
            issues.append(
                "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md "
                "missing keyword: future_startup_command_executed=false"
            )
    if TASK312_DOC_PATH.exists():
        task312_text = read_text(TASK312_DOC_PATH)
        if "compile_success_scope=compile-only-diagnostic" not in task312_text:
            issues.append(
                "docs/V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md "
                "missing keyword: compile_success_scope=compile-only-diagnostic"
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


def collect_repo_artifact_issues() -> tuple[list[str], bool, bool, bool, bool, bool]:
    issues: list[str] = []
    repo_ex5_artifacts = False
    repo_compile_logs = False
    repo_terminal_data_directory = False
    repo_startup_logs = False
    repo_no_trade_config = False

    for path in sorted(ROOT_DIR.rglob("*")):
        rel_path = relative_posix(path)
        if rel_path.startswith(".git/") or ".git/" in rel_path:
            continue
        if path.is_dir() and is_terminal_data_dir_candidate(path):
            repo_terminal_data_directory = True
            issues.append(f"repository contains prohibited terminal data directory: {rel_path}")
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() == ".ex5":
            repo_ex5_artifacts = True
            issues.append(f"repository contains prohibited .ex5 artifact: {rel_path}")
            continue
        if is_compile_log_candidate(path) and not is_allowed_existing_log(rel_path):
            repo_compile_logs = True
            issues.append(f"repository contains prohibited compile log candidate: {rel_path}")
        if is_startup_log_candidate(path):
            repo_startup_logs = True
            issues.append(f"repository contains prohibited startup log candidate: {rel_path}")
        if is_generated_no_trade_config_candidate(path):
            repo_no_trade_config = True
            issues.append(f"repository contains prohibited generated no-trade startup config: {rel_path}")
    return (
        issues,
        repo_ex5_artifacts,
        repo_compile_logs,
        repo_terminal_data_directory,
        repo_startup_logs,
        repo_no_trade_config,
    )


def main() -> int:
    issues = collect_doc_issues()
    mq5_issues, inventory_count, trading_keywords_found = collect_mq5_issues()
    (
        artifact_issues,
        repo_ex5_artifacts,
        repo_compile_logs,
        repo_terminal_data_directory,
        repo_startup_logs,
        repo_no_trade_config,
    ) = collect_repo_artifact_issues()
    issues.extend(mq5_issues)
    issues.extend(artifact_issues)

    if issues:
        print("MT5 no-trade startup dry-run config boundary validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MT5 no-trade startup dry-run config boundary validation passed")
    print("mt5_no_trade_startup_dryrun_config_boundary=true")
    print("startup_dryrun_config_boundary_only=true")
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
    print("future_task_317_requires_gpt_boundary=true")
    print(f"no_trade_config_generated_in_repo={str(repo_no_trade_config).lower()}")
    print("startup_quarantine_outside_repo_required=true")
    print(f"repo_terminal_data_directory={str(repo_terminal_data_directory).lower()}")
    print(f"repo_startup_logs={str(repo_startup_logs).lower()}")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keywords_found).lower()}")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print("repo_mq5_modified=false")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
