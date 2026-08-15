#!/usr/bin/env python3
"""Self-test for the MQL5 compile-only artifact quarantine validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_only_artifact_quarantine.py"

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
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not trading authorization
- no MQL5 compile executed in TASK-296
- no MetaEditor executed in TASK-296
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: acda17c TASK-295 implement MQL5 compile-only command discovery boundary
- current tag: v0.5.94-task-295-mql5-compile-only-command-discovery
- MetaEditor candidate discovered in TASK-295
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-297 must be separately authorized by GPT before any compile execution
- TASK-297 must not be entered directly
- future compile-only execution must quarantine outputs outside repository or prove no repo artifact writes
- future compile-only execution must check repository has no .ex5 before and after compile
- future compile-only execution must check repository has no compile log before and after compile
- future compile-only execution must not create official manifest / evidence / report
- future compile-only execution must remain no-trade
- pre-compile check: no .ex5 in repository
- pre-compile check: no compile log in repository
- pre-compile check: MQ5 inventory 7 files
- pre-compile check: trading keywords false
- compile-only command may be executed only after GPT defines TASK-297 boundary
- post-compile check: no .ex5 in repository unless separately authorized
- post-compile check: no compile log in repository unless separately authorized
- post-compile check: no MT5 run
- post-compile check: no Strategy Tester
- post-compile check: no trading
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
    print("MQL5 compile-only artifact quarantine self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mql5_compile_only_artifact_quarantine",
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
    task294_text: str | None = TASK294_BOUNDARY_TEXT,
    task295_text: str | None = TASK295_BOUNDARY_TEXT,
    task296_text: str | None = TASK296_BOUNDARY_TEXT,
    mq5_overrides: dict[str, str] | None = None,
) -> None:
    if task294_text is not None:
        write_text(root / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md", task294_text)
    if task295_text is not None:
        write_text(
            root / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
            task295_text,
        )
    if task296_text is not None:
        write_text(
            root / "docs" / "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
            task296_text,
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
        "mql5_compile_only_artifact_quarantine=true",
        "artifact_quarantine_only=true",
        "metaeditor_executed=false",
        "mql5_compile_executed=false",
        "mt5_run=false",
        "trading_authorization=false",
        "ex5_artifact_generated=false",
        "compile_log_generated=false",
        "repo_ex5_artifacts=false",
        "repo_compile_logs=false",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "Inventory only; no MT5 run; no trading authorization.",
    )
    for text in required:
        if text not in output:
            return f"{message}: missing stdout field {text}\n{output}"
    return ""


def expect_fail(module, root: Path, message: str) -> str:
    result, output = run_main(module, root)
    if result == 0:
        return f"{message}\n{output}"
    if "MQL5 compile-only artifact quarantine validation failed" not in output:
        return f"{message}: failure output missing header\n{output}"
    return ""


def positive_test_complete_fixture_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        return expect_pass(module, root, "complete fixture should pass")


def negative_test_missing_task296_doc(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task296_text=None)
        return expect_fail(module, root, "missing TASK-296 doc should fail")


def negative_test_missing_task295_doc(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=None)
        return expect_fail(module, root, "missing TASK-295 doc should fail")


def negative_test_missing_task294_doc(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task294_text=None)
        return expect_fail(module, root, "missing TASK-294 doc should fail")


def negative_test_missing_artifact_quarantine_only(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task296_text=TASK296_BOUNDARY_TEXT.replace("- artifact-quarantine-only\n", ""))
        return expect_fail(module, root, "missing artifact-quarantine-only should fail")


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
        write_text(root / "mql5_compile.txt", "compile log placeholder\n")
        return expect_fail(module, root, "compile log in repo should fail")


def positive_test_existing_localhost_logs_allowed(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "logs" / "localhost-3000.debug.log", "existing local dev log\n")
        return expect_pass(module, root, "localhost dev log should be allowed")


def positive_test_existing_runtime_sample_log_allowed(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(
            root / "backtest" / "reports" / "samples" / "TASK-012_runtime_summary_sample.log",
            "existing non-compile runtime sample log\n",
        )
        return expect_pass(module, root, "existing runtime sample log should be allowed")


def negative_test_mq5_inventory_not_seven(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        (root / "mq5" / "logger" / "Logger.mqh").unlink()
        return expect_fail(module, root, "MQ5 inventory other than 7 should fail")


def negative_test_trading_keyword_present(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, mq5_overrides={"core/EaController.mqh": "void Probe(){ CTrade; }\n"})
        return expect_fail(module, root, "trading keyword should fail")


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
        negative_test_missing_task296_doc,
        negative_test_missing_task295_doc,
        negative_test_missing_task294_doc,
        negative_test_missing_artifact_quarantine_only,
        negative_test_repo_ex5_artifact_fails,
        negative_test_compile_log_fails,
        positive_test_existing_localhost_logs_allowed,
        positive_test_existing_runtime_sample_log_allowed,
        negative_test_mq5_inventory_not_seven,
        negative_test_trading_keyword_present,
        positive_test_does_not_call_subprocess,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQL5 compile-only artifact quarantine self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
