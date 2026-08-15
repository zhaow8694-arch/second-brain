#!/usr/bin/env python3
"""Read-only MQL5 compile-only command discovery validator.

The validator only discovers whether a local MetaEditor executable candidate is
visible and prints a future command template. It never executes MetaEditor,
MT5, MQL5 compile commands, or any command that can create .ex5 artifacts.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK294_BOUNDARY_DOC = ROOT_DIR / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md"
TASK295_BOUNDARY_DOC = (
    ROOT_DIR / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md"
)
MQ5_ROOT = ROOT_DIR / "mq5"
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

COMMON_METAEDITOR_CANDIDATES = (
    Path(r"C:\Program Files\MetaTrader 5\metaeditor64.exe"),
    Path(r"C:\Program Files\MetaTrader 5\MetaEditor64.exe"),
    Path(r"C:\Program Files (x86)\MetaTrader 5\metaeditor64.exe"),
    Path(r"C:\Program Files (x86)\MetaTrader 5\MetaEditor64.exe"),
)
PATH_METAEDITOR_CANDIDATES = ("metaeditor64.exe", "metaeditor.exe")
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")

TASK295_REQUIRED_KEYWORDS = (
    "TASK-295 MQL5 compile-only command discovery boundary",
    "command-discovery-only",
    "not compile execution",
    "not MetaEditor execution",
    "not MT5 run authorization",
    "not Strategy Tester authorization",
    "not backtest authorization",
    "not trading authorization",
    "no MQL5 compile executed in TASK-295",
    "no MetaEditor executed in TASK-295",
    "no .ex5 artifact generated",
    "no compile log generated",
    "no manifest generated",
    "no evidence generated",
    SAFETY_NOTICE,
    "current HEAD: 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet",
    "current tag: v0.5.93-task-294-future-mql5-compile-only-boundary",
    "MQ5 inventory remains 7 files",
    "Buy / Sell / OrderSend / PositionOpen / CTrade remain false",
    "future TASK-296 must be separately authorized by GPT before any compile execution",
    "TASK-296 must not be entered directly",
    "future compile-only task must remain no-trade",
    "future compile-only task must not create manifest / evidence / report unless separately authorized",
    "future compile-only task must quarantine or prevent .ex5 artifact generation before compile execution is allowed",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    task294_path = root_dir / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md"
    task295_path = root_dir / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md"

    if not task294_path.exists():
        issues.append("missing TASK-DOC-294 boundary doc")
    if not task295_path.exists():
        issues.append("missing TASK-295 command discovery boundary doc")
        return issues

    task295_text = read_text(task295_path)
    for keyword in TASK295_REQUIRED_KEYWORDS:
        if keyword not in task295_text:
            issues.append(f"TASK-295 boundary doc missing keyword: {keyword}")
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
                    f"{path.relative_to(root_dir).as_posix()} contains prohibited trading keyword: {keyword}"
                )
                trading_keyword_found = True
    return issues, len(files), trading_keyword_found


def discover_metaeditor_candidate(path_exists=None, which=None) -> str:
    exists = path_exists or (lambda path: path.exists())
    which_func = which or shutil.which

    for candidate in COMMON_METAEDITOR_CANDIDATES:
        if exists(candidate):
            return str(candidate)

    for executable in PATH_METAEDITOR_CANDIDATES:
        candidate = which_func(executable)
        if candidate:
            return str(candidate)

    return ""


def future_compile_command_template(metaeditor_path: str) -> str:
    return (
        f'"{metaeditor_path}" '
        "/compile:\"mq5/TradingSystem.mq5\" "
        "/log:\"<stdout-only-or-quarantined-log-path-if-separately-authorized>\""
    )


def print_success(root_dir: Path, inventory_count: int, candidate_path: str) -> None:
    print("MQL5 compile-only command discovery validation passed")
    print("mql5_compile_only_command_discovery=true")
    print("command_discovery_only=true")
    print("metaeditor_executed=false")
    print("mql5_compile_executed=false")
    print("mt5_run=false")
    print("trading_authorization=false")
    print("ex5_artifact_generated=false")
    print("compile_log_generated=false")
    print("mq5_inventory_files=7")
    print("trading_keywords=false")
    print(SAFETY_NOTICE)
    print(f"repository_root={root_dir}")
    if candidate_path:
        print("metaeditor_candidate_found=true")
        print(f"metaeditor_candidate_path={candidate_path}")
        print(f"future_compile_command_template={future_compile_command_template(candidate_path)}")
    else:
        print("metaeditor_candidate_found=false")
    print("future_compile_command_executed=false")
    print(f"discovered_mq5_inventory_count={inventory_count}")


def main(argv: list[str] | None = None, *, root_dir: Path | None = None, path_exists=None, which=None) -> int:
    _ = argv
    root = (root_dir or ROOT_DIR).resolve()
    issues = collect_boundary_issues(root)
    inventory_issues, inventory_count, trading_keyword_found = collect_mq5_inventory_issues(root)
    issues.extend(inventory_issues)

    if issues:
        print("MQL5 compile-only command discovery validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        print("metaeditor_executed=false")
        print("mql5_compile_executed=false")
        print("mt5_run=false")
        print("trading_authorization=false")
        print("ex5_artifact_generated=false")
        print("compile_log_generated=false")
        print(f"mq5_inventory_files={inventory_count}")
        print(f"trading_keywords={str(trading_keyword_found).lower()}")
        print(SAFETY_NOTICE)
        return 1

    candidate_path = discover_metaeditor_candidate(path_exists=path_exists, which=which)
    print_success(root, inventory_count, candidate_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
