#!/usr/bin/env python3
"""Validate TASK-317 MT5 no-trade startup config template preview.

This validator is read-only. It emits a stdout-only future config template
preview and never executes MT5, terminal64.exe, terminal.exe, Strategy Tester,
MetaEditor, backtest, or MQL5 compile.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
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
TASK317_DOC_PATH = ROOT_DIR / "docs" / "V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md"
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

REQUIRED_TASK317_KEYWORDS = (
    "TASK-317 MT5 no-trade startup config template preview",
    "stdout-only-config-template-preview",
    "no config file generated in TASK-317",
    "not MT5 run in TASK-317",
    "not terminal64.exe execution in TASK-317",
    "not terminal.exe execution in TASK-317",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not simulation trading authorization",
    "not real trading authorization",
    "not trading authorization",
    "not deployment readiness",
    "not strategy readiness",
    "no MT5 terminal run executed in TASK-317",
    "no terminal64.exe executed in TASK-317",
    "no terminal.exe executed in TASK-317",
    "no Strategy Tester executed in TASK-317",
    "no backtest executed in TASK-317",
    "no trading executed in TASK-317",
    "no manifest generated",
    "no evidence generated",
    "no report generated",
    "no startup log generated in repository",
    "no terminal data directory created in repository",
    "no no-trade config file generated in repository",
    SAFETY_NOTICE,
    "current HEAD: a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary",
    "current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary",
    "TASK-314 discovered MT5 terminal candidate",
    "TASK-315 defined startup quarantine preparation",
    "TASK-316 defined dry-run config boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5",
    "TASK-318 must not be entered directly",
    "future terminal path placeholder",
    "future quarantine data path placeholder outside repository",
    "future no-trade config template",
    "InpEnableTrading=false",
    "no Strategy Tester",
    "no backtest",
    "no trading",
    "no official manifest",
    "no evidence",
    "no report",
    "stdout-only startup result unless separately authorized",
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
        (TASK313_DOC_PATH, "docs/V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"),
        (TASK314_DOC_PATH, "docs/V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"),
        (TASK315_DOC_PATH, "docs/V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"),
        (TASK316_DOC_PATH, "docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md"),
    )
    for path, label in required_existing_docs:
        if not path.exists():
            issues.append(f"missing required docs file: {label}")

    if not TASK317_DOC_PATH.exists():
        issues.append(
            "missing required docs file: "
            "docs/V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md"
        )
        return issues

    task317_text = read_text(TASK317_DOC_PATH)
    issues.extend(
        "docs/V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md "
        f"missing keyword: {keyword}"
        for keyword in REQUIRED_TASK317_KEYWORDS
        if keyword not in task317_text
    )

    if TASK316_DOC_PATH.exists():
        task316_text = read_text(TASK316_DOC_PATH)
        if "startup-dryrun-config-boundary-only" not in task316_text:
            issues.append(
                "docs/V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md "
                "missing keyword: startup-dryrun-config-boundary-only"
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
        print("MT5 no-trade startup config template validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("MT5 no-trade startup config template validation passed")
    print("mt5_no_trade_startup_config_template=true")
    print("stdout_only_config_template_preview=true")
    print("config_file_generated=false")
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
    print("future_task_318_requires_gpt_boundary=true")
    print(f"no_trade_config_generated_in_repo={str(repo_no_trade_config).lower()}")
    print("startup_quarantine_outside_repo_required=true")
    print(f"repo_terminal_data_directory={str(repo_terminal_data_directory).lower()}")
    print(f"repo_startup_logs={str(repo_startup_logs).lower()}")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keywords_found).lower()}")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print("repo_mq5_modified=false")
    print("template_InpEnableTrading=false")
    print("template_strategy_tester_enabled=false")
    print("template_backtest_enabled=false")
    print("template_trading_enabled=false")
    print("template_evidence_generation=false")
    print("template_manifest_generation=false")
    print("template_report_generation=false")
    print(SAFETY_NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
