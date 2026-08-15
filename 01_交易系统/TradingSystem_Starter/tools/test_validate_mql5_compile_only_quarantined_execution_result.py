#!/usr/bin/env python3
"""Self-test for TASK-304 quarantined compile result validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT_DIR / "tools" / "validate_mql5_compile_only_quarantined_execution_result.py"
)
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

RESULT_DOC = """# TASK-304 quarantined MQL5 compile-only execution

- TASK-304 quarantined MQL5 compile-only execution
- compile-only authorized by GPT in TASK-304
- current HEAD: 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet
- current tag: v0.5.100-task-303-v060-compile-only-execution-authorization
- MetaEditor executed=true
- MQL5 compile executed=true
- MT5 terminal run=false
- Strategy Tester run=false
- trading_executed=false
- compile target was quarantine copy
- quarantine deleted=true
- repo_mq5_modified=false
- repo_ex5_artifacts=false
- repo_compile_logs=false
- no manifest generated
- no evidence generated
- no report generated
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
- TASK-305 must not be entered directly without GPT boundary
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
    print("TASK-304 quarantined execution result validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mql5_compile_only_quarantined_execution_result",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_project(root: Path, *, result_doc: str | None = RESULT_DOC, mq5_overrides=None) -> None:
    if result_doc is not None:
        write_text(root / "docs" / "V060_TASK_304_MQL5_COMPILE_ONLY_QUARANTINED_EXECUTION.md", result_doc)
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
    before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    result, output = run_main(module, root)
    after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    if before != after:
        return f"{message}: validator modified files"
    if result != 0:
        return f"{message}\n{output}"
    for text in (
        "mql5_compile_only_quarantined_execution_result=true",
        "metaeditor_executed=true",
        "mql5_compile_executed=true",
        "mt5_terminal_run=false",
        "strategy_tester_run=false",
        "trading_executed=false",
        "repo_mq5_modified=false",
        "repo_ex5_artifacts=false",
        "repo_compile_logs=false",
        "quarantine_deleted=true",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        SAFETY_NOTICE,
    ):
        if text not in output:
            return f"{message}: missing stdout field {text}\n{output}"
    return ""


def expect_fail(module, root: Path, message: str) -> str:
    result, output = run_main(module, root)
    if result == 0:
        return f"{message}\n{output}"
    if "validation failed" not in output:
        return f"{message}: failure output missing header\n{output}"
    return ""


def test_complete_result_doc_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        return expect_pass(module, root, "complete TASK-304 result doc should pass")


def test_missing_result_doc_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, result_doc=None)
        return expect_fail(module, root, "missing result doc should fail")


def test_missing_required_result_fields_fail(module) -> str:
    fields = (
        "MetaEditor executed=true",
        "MQL5 compile executed=true",
        "quarantine deleted=true",
    )
    for field in fields:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, result_doc=RESULT_DOC.replace(f"- {field}\n", ""))
            error = expect_fail(module, root, f"missing {field} should fail")
            if error:
                return error
    return ""


def test_repo_artifacts_mq5_diff_and_trading_keyword_fail(module) -> str:
    cases = (
        ("repo .ex5", {"artifact": ("mq5/TradingSystem.ex5", "binary\n")}),
        ("repo compile log", {"artifact": ("mql5_compile.log", "log\n")}),
        ("trading keyword", {"mq5_overrides": {"core/EaController.mqh": "void Probe(){ OrderSend; }\n"}}),
    )
    for label, case in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, mq5_overrides=case.get("mq5_overrides"))
            if "artifact" in case:
                rel_path, text = case["artifact"]
                write_text(root / rel_path, text)
            error = expect_fail(
                module,
                root,
                f"{label} should fail",
            )
            if error:
                return error
    return ""


def test_validator_does_not_import_subprocess(module) -> str:
    if hasattr(module, "subprocess"):
        return "validator should not import subprocess"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")
    module = load_validator()
    tests = [
        test_complete_result_doc_passes,
        test_missing_result_doc_fails,
        test_missing_required_result_fields_fail,
        test_repo_artifacts_mq5_diff_and_trading_keyword_fail,
        test_validator_does_not_import_subprocess,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)
    print("TASK-304 quarantined execution result validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
