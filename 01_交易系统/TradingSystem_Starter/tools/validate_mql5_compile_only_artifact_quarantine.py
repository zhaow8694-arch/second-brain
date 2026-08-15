#!/usr/bin/env python3
"""Read-only MQL5 compile-only artifact quarantine validator.

This validator checks that the TASK-296 boundary exists and that the repository
does not already contain compile artifacts or compile logs. It never executes
MetaEditor, MT5, or MQL5 compile commands.
"""

from __future__ import annotations

from pathlib import Path
import fnmatch
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
MQ5_ROOT = ROOT_DIR / "mq5"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")

TASK294_DOC = ROOT_DIR / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md"
TASK295_DOC = ROOT_DIR / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md"
TASK296_DOC = ROOT_DIR / "docs" / "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md"

TASK296_REQUIRED_KEYWORDS = (
    "TASK-296 MQL5 compile-only artifact quarantine boundary",
    "artifact-quarantine-only",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MQL5 compile executed in TASK-296",
    "no MetaEditor executed in TASK-296",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    SAFETY_NOTICE,
    "current HEAD: acda17c TASK-295 implement MQL5 compile-only command discovery boundary",
    "current tag: v0.5.94-task-295-mql5-compile-only-command-discovery",
    "MetaEditor candidate discovered in TASK-295",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-297 must be separately authorized by GPT before any compile execution",
    "TASK-297 must not be entered directly",
    "future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes",
    "future compile-only execution must check repository has no .ex5 before and after compile",
    "future compile-only execution must check repository has no compile log before and after compile",
    "future compile-only execution must not create official manifest / evidence / report",
    "future compile-only execution must remain no-trade",
    "pre-compile check: no .ex5 in repository",
    "pre-compile check: no compile log in repository",
    "pre-compile check: MQ5 inventory 7 files",
    "pre-compile check: trading keywords false",
    "compile-only command may be executed only after GPT defines TASK-297 boundary",
    "post-compile check: no .ex5 in repository unless separately authorized",
    "post-compile check: no compile log in repository unless separately authorized",
    "post-compile check: no MT5 run",
    "post-compile check: no Strategy Tester",
    "post-compile check: no trading",
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
    )

    for label, path in docs:
        if not path.exists():
            issues.append(f"missing {label}")

    task296_path = root_dir / "docs" / TASK296_DOC.name
    if not task296_path.exists():
        return issues

    text = read_text(task296_path)
    for keyword in TASK296_REQUIRED_KEYWORDS:
        if keyword not in text:
            issues.append(f"TASK-296 boundary doc missing keyword: {keyword}")
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
    name = path.name
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in COMPILE_LOG_PATTERNS)


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
    print("MQL5 compile-only artifact quarantine validation failed")
    print("Issues:")
    for issue in issues:
        print(f"- {issue}")
    print("mql5_compile_only_artifact_quarantine=false")
    print("artifact_quarantine_only=true")
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
    print(SAFETY_NOTICE)


def print_success(root_dir: Path, inventory_count: int) -> None:
    print("MQL5 compile-only artifact quarantine validation passed")
    print("mql5_compile_only_artifact_quarantine=true")
    print("artifact_quarantine_only=true")
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
