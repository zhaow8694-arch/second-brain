#!/usr/bin/env python3
"""Read-only MQL5 compile-only dry-run validator.

The validator simulates the compile-only execution boundary as stdout-only
static validation. It never executes MetaEditor, MT5, terminal64.exe, or MQL5
compile commands.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")

TASK294_DOC = ROOT_DIR / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md"
TASK295_DOC = ROOT_DIR / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md"
TASK296_DOC = ROOT_DIR / "docs" / "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md"
TASK297_DOC = ROOT_DIR / "docs" / "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md"
TASK298_DOC = ROOT_DIR / "docs" / "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md"

TASK298_REQUIRED_KEYWORDS = (
    "TASK-298 MQL5 compile-only dry-run simulation",
    "dry-run-only",
    "artifact-quarantine enforced",
    "future compile-only task must be separately authorized by GPT",
    "stdout-only simulation",
    "current HEAD: 2423211 TASK-296 implement MQL5 compile-only artifact quarantine boundary",
    "current tag: v0.5.95-task-296-mql5-compile-only-artifact-quarantine",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "TASK-299 must not be entered directly",
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
    root = root_dir / "mq5"
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def collect_boundary_issues(root_dir: Path) -> list[str]:
    issues: list[str] = []
    docs = (
        ("TASK-DOC-294 boundary doc", root_dir / "docs" / TASK294_DOC.name),
        ("TASK-295 command discovery boundary doc", root_dir / "docs" / TASK295_DOC.name),
        ("TASK-296 artifact quarantine boundary doc", root_dir / "docs" / TASK296_DOC.name),
        ("TASK-297 compile-only execution boundary doc", root_dir / "docs" / TASK297_DOC.name),
        ("TASK-298 compile-only dry-run doc", root_dir / "docs" / TASK298_DOC.name),
    )

    for label, path in docs:
        if not path.exists():
            issues.append(f"missing {label}")

    task298_path = root_dir / "docs" / TASK298_DOC.name
    if not task298_path.exists():
        return issues

    text = read_text(task298_path)
    for keyword in TASK298_REQUIRED_KEYWORDS:
        if keyword not in text:
            issues.append(f"TASK-298 dry-run doc missing keyword: {keyword}")
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
        if ".git/" in rel_path or rel_path.startswith(".git/"):
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
    print("MQL5 compile-only dry-run validation failed")
    print("Issues:")
    for issue in issues:
        print(f"- {issue}")
    print("mql5_compile_only_dryrun=false")
    print("dry_run_only=true")
    print("stdout_only_simulation=true")
    print("artifact_quarantine_enforced=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("mt5_run=false")
    print("ex5_artifact_generated=false")
    print("compile_log_generated=false")
    print("manifest_generated=false")
    print("evidence_generated=false")
    print("report_generated=false")
    print(f"repo_ex5_artifacts={str(repo_ex5_artifacts).lower()}")
    print(f"repo_compile_logs={str(repo_compile_logs).lower()}")
    print(f"mq5_inventory_files={inventory_count}")
    print(f"trading_keywords={str(trading_keyword_found).lower()}")
    print(SAFETY_NOTICE)


def print_success(root_dir: Path, inventory_count: int) -> None:
    print("MQL5 compile-only dry-run validation passed")
    print("mql5_compile_only_dryrun=true")
    print("dry_run_only=true")
    print("stdout_only_simulation=true")
    print("artifact_quarantine_enforced=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("mt5_run=false")
    print("ex5_artifact_generated=false")
    print("compile_log_generated=false")
    print("manifest_generated=false")
    print("evidence_generated=false")
    print("report_generated=false")
    print("repo_ex5_artifacts=false")
    print("repo_compile_logs=false")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print("future_compile_only_task_requires_GPT_authorization=true")
    print("TASK_299_must_not_be_entered_directly=true")
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
