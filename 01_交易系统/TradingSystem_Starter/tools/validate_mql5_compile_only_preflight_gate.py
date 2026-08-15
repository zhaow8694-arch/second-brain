#!/usr/bin/env python3
"""Read-only MQL5 compile-only preflight gate validator.

The validator checks the future compile-only execution gate without executing
MetaEditor, terminal64.exe, MT5, Strategy Tester, or any /compile command.
It is stdout-only and does not create artifacts, logs, reports, manifests, or
evidence.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")

DOC_NAMES = (
    "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md",
    "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
    "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
    "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
    "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md",
    "V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md",
    "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md",
)

TASK302_DOC_NAME = "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md"
TASK302_REQUIRED_KEYWORDS = (
    "TASK-302 MQL5 compile-only execution preflight gate",
    "preflight-gate-only",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MQL5 compile executed in TASK-302",
    "no MetaEditor executed in TASK-302",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    SAFETY_NOTICE,
    "current HEAD: 2f0498b TASK-301 create v060 compile-readiness planning packet",
    "current tag: v0.5.98-task-301-v060-compile-readiness-planning",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "all previous compile-only boundary checks must pass before future compile execution",
    "artifact quarantine must pass before future compile execution",
    "future compile-only command must remain stdout-only unless GPT separately authorizes artifact handling",
    "future TASK-303 must be separately authorized by GPT before any compile execution",
    "TASK-303 must not be entered directly",
    "preflight check: mql5-compile-only-boundary PASS",
    "preflight check: mql5-compile-only-command-discovery PASS",
    "preflight check: mql5-compile-only-artifact-quarantine PASS",
    "preflight check: mql5-compile-only-execution-boundary PASS",
    "preflight check: mql5-compile-only-dryrun PASS",
    "preflight check: mql5-compile-only-dryrun-execution PASS",
    "preflight check: v060-compile-readiness-planning PASS",
    "preflight check: MQ5 inventory 7 files",
    "preflight check: trading keywords false",
    "preflight check: repo_ex5_artifacts=false",
    "preflight check: repo_compile_logs=false",
    "post-compile requirement: no MT5 run",
    "post-compile requirement: no Strategy Tester",
    "post-compile requirement: no trading",
    "post-compile requirement: no manifest/evidence/report unless separately authorized",
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


def collect_boundary_issues(root_dir: Path) -> list[str]:
    issues: list[str] = []
    docs_root = root_dir / "docs"

    for name in DOC_NAMES:
        if not (docs_root / name).exists():
            issues.append(f"missing required compile-only boundary doc: docs/{name}")

    task302_path = docs_root / TASK302_DOC_NAME
    if not task302_path.exists():
        return issues

    text = read_text(task302_path)
    for keyword in TASK302_REQUIRED_KEYWORDS:
        if keyword not in text:
            issues.append(f"TASK-302 preflight gate doc missing keyword: {keyword}")
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


def is_allowed_existing_log(rel_path: str) -> bool:
    return any(fnmatch.fnmatchcase(rel_path, pattern) for pattern in ALLOWED_LOG_PATTERNS)


def is_compile_log_candidate(path: Path) -> bool:
    return any(fnmatch.fnmatchcase(path.name, pattern) for pattern in COMPILE_LOG_PATTERNS)


def collect_artifact_issues(root_dir: Path) -> tuple[list[str], bool, bool]:
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


def print_failure(
    issues: list[str],
    *,
    inventory_count: int,
    trading_keyword_found: bool,
    repo_ex5_artifacts: bool,
    repo_compile_logs: bool,
) -> None:
    print("MQL5 compile-only preflight gate validation failed")
    print("Issues:")
    for issue in issues:
        print(f"- {issue}")
    print("mql5_compile_only_preflight_gate=false")
    print("preflight_gate_only=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("mt5_run=false")
    print("trading_authorization=false")
    print("ex5_artifact_generated=false")
    print("compile_log_generated=false")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keyword_found).lower()}")
    print("future_task_303_requires_gpt_boundary=true")
    print("compile_execution_authorized=false")
    print(SAFETY_NOTICE)


def print_success(root_dir: Path, inventory_count: int) -> None:
    print("MQL5 compile-only preflight gate validation passed")
    print("mql5_compile_only_preflight_gate=true")
    print("preflight_gate_only=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("mt5_run=false")
    print("trading_authorization=false")
    print("ex5_artifact_generated=false")
    print("compile_log_generated=false")
    print("repo_ex5_artifacts=false")
    print("repo_compile_logs=false")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print("future_task_303_requires_gpt_boundary=true")
    print("compile_execution_authorized=false")
    print(SAFETY_NOTICE)
    print(f"repository_root={root_dir}")
    print(f"discovered_mq5_inventory_count={inventory_count}")


def main(argv: list[str] | None = None, *, root_dir: Path | None = None) -> int:
    _ = argv
    root = (root_dir or ROOT_DIR).resolve()

    issues = collect_boundary_issues(root)
    inventory_issues, inventory_count, trading_keyword_found = collect_mq5_inventory_issues(root)
    artifact_issues, repo_ex5_artifacts, repo_compile_logs = collect_artifact_issues(root)
    issues.extend(inventory_issues)
    issues.extend(artifact_issues)

    if issues:
        print_failure(
            issues,
            inventory_count=inventory_count,
            trading_keyword_found=trading_keyword_found,
            repo_ex5_artifacts=repo_ex5_artifacts,
            repo_compile_logs=repo_compile_logs,
        )
        return 1

    print_success(root, inventory_count)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
