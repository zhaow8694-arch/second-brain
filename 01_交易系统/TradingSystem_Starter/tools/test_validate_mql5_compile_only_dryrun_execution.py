#!/usr/bin/env python3
"""Self-test for the MQL5 compile-only dry-run execution validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_only_dryrun_execution.py"

SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

TASK294_BOUNDARY_TEXT = """# TASK-DOC-294 future MQL5 compile-only boundary packet

- planning-only / boundary-only
- future MQL5 compile-only candidate
- Inventory only; no MT5 run; no trading authorization.
"""

TASK295_BOUNDARY_TEXT = """# TASK-295 MQL5 compile-only command discovery boundary

- command-discovery-only
- not compile execution
- not MetaEditor execution
- Inventory only; no MT5 run; no trading authorization.
"""

TASK296_BOUNDARY_TEXT = """# TASK-296 MQL5 compile-only artifact quarantine boundary

- artifact-quarantine-only
- no .ex5 artifact generated
- no compile log generated
- Inventory only; no MT5 run; no trading authorization.
"""

TASK297_BOUNDARY_TEXT = """# TASK-297 MQL5 compile-only execution boundary

- compile-only-task
- future compile-only candidate
- requires GPT explicit authorization
- artifact quarantine checked
- Inventory only; no MT5 run; no trading authorization.
"""

TASK298_DRYRUN_TEXT = """# TASK-298 MQL5 compile-only dry-run simulation

- dry-run-only
- artifact-quarantine enforced
- future compile-only task must be separately authorized by GPT
- stdout-only simulation
- Inventory only; no MT5 run; no trading authorization.
"""

TASK300_DRYRUN_EXECUTION_TEXT = """# TASK-300 MQL5 compile-only dry-run execution simulation

- dry-run-execution-only
- artifact-quarantine enforced
- future compile-only task must be separately authorized by GPT
- stdout-only simulation
- current HEAD: 2dab115 TASK-298 implement MQL5 compile-only dry-run boundary
- current tag: v0.5.96-task-298-mql5-compile-only-dryrun
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- TASK-301 must not be entered directly
- future compile-only execution must remain no-trade
- future compile-only execution must not create manifest / evidence / report unless separately authorized
- Inventory only; no MT5 run; no trading authorization.
"""

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}


def fail(message: str) -> int:
    print("MQL5 compile-only dry-run execution self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mql5_compile_only_dryrun_execution",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_project(
    root: Path,
    *,
    task300_text: str | None = TASK300_DRYRUN_EXECUTION_TEXT,
    mq5_overrides: dict[str, str] | None = None,
) -> None:
    write_text(root / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md", TASK294_BOUNDARY_TEXT)
    write_text(
        root / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
        TASK295_BOUNDARY_TEXT,
    )
    write_text(
        root / "docs" / "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
        TASK296_BOUNDARY_TEXT,
    )
    write_text(
        root / "docs" / "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
        TASK297_BOUNDARY_TEXT,
    )
    write_text(root / "docs" / "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md", TASK298_DRYRUN_TEXT)
    if task300_text is not None:
        write_text(
            root / "docs" / "V060_TASK_300_MQL5_COMPILE_ONLY_DRYRUN_SIMULATION.md",
            task300_text,
        )

    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_main(module, root: Path):
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main([], root_dir=root)
    return result, output.getvalue()


def expect_pass(module, root: Path, message: str) -> str:
    result, output = run_main(module, root)
    if result != 0:
        return f"{message}\n{output}"
    required = (
        "MQL5 compile-only dry-run execution validation passed",
        "mql5_compile_only_dryrun_execution=true",
        "dry_run_execution_only=true",
        "stdout_only_simulation=true",
        "artifact_quarantine_enforced=true",
        "future_compile_only_task_requires_GPT_authorization=true",
        "candidate_compile_command_generated=true",
        "candidate_compile_command_executed=false",
        "metaeditor_executed=false",
        "mql5_compile_executed=false",
        "mt5_run=false",
        "ex5_artifact_generated=false",
        "compile_log_generated=false",
        "manifest_generated=false",
        "evidence_generated=false",
        "report_generated=false",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "TASK_301_must_not_be_entered_directly=true",
        SAFETY_NOTICE,
    )
    for text in required:
        if text not in output:
            return f"{message}: missing stdout field {text}\n{output}"
    return ""


def expect_fail(module, root: Path, message: str) -> str:
    result, output = run_main(module, root)
    if result == 0:
        return f"{message}\n{output}"
    if "MQL5 compile-only dry-run execution validation failed" not in output:
        return f"{message}: failure output missing header\n{output}"
    return ""


def positive_test_complete_fixture_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        return expect_pass(module, root, "complete fixture should pass")


def negative_test_missing_task300_doc(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task300_text=None)
        return expect_fail(module, root, "missing TASK-300 doc should fail")


def negative_test_missing_dry_run_execution_keyword(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task300_text=TASK300_DRYRUN_EXECUTION_TEXT.replace("- dry-run-execution-only\n", ""))
        return expect_fail(module, root, "missing dry-run-execution-only should fail")


def negative_test_mq5_inventory_not_seven(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        (root / "mq5" / "logger" / "Logger.mqh").unlink()
        return expect_fail(module, root, "MQ5 inventory other than 7 should fail")


def negative_test_trading_keyword_present(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, mq5_overrides={"core/EaController.mqh": "void Probe(){ OrderSend; }\n"})
        return expect_fail(module, root, "trading keyword should fail")


def negative_test_repo_ex5_artifact_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "mq5" / "TradingSystem.ex5", "binary placeholder\n")
        return expect_fail(module, root, ".ex5 artifact in repo should fail")


def negative_test_compile_log_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "compile.log", "compile log placeholder\n")
        return expect_fail(module, root, "compile log in repo should fail")


def positive_test_stdout_only_does_not_create_artifacts(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
        error = expect_pass(module, root, "stdout-only dry-run execution should pass")
        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
        if before != after:
            return f"validator created or removed files\nbefore={before}\nafter={after}"
        return error


def positive_test_existing_localhost_logs_allowed(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "logs" / "localhost-3000.debug.log", "existing local dev log\n")
        return expect_pass(module, root, "localhost dev log should be allowed")


def positive_test_does_not_call_subprocess(module) -> str:
    if hasattr(module, "subprocess"):
        return "validator module must not import subprocess"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    module = load_validator()
    tests = [
        positive_test_complete_fixture_passes,
        negative_test_missing_task300_doc,
        negative_test_missing_dry_run_execution_keyword,
        negative_test_mq5_inventory_not_seven,
        negative_test_trading_keyword_present,
        negative_test_repo_ex5_artifact_fails,
        negative_test_compile_log_fails,
        positive_test_stdout_only_does_not_create_artifacts,
        positive_test_existing_localhost_logs_allowed,
        positive_test_does_not_call_subprocess,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQL5 compile-only dry-run execution self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
