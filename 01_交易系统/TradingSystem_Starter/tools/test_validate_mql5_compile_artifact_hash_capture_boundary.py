#!/usr/bin/env python3
"""Self-test for TASK-310 MQL5 compile artifact hash capture boundary validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_artifact_hash_capture_boundary.py"

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

TASK309_DOC = """# TASK-309 MQL5 compile-only success reclassification boundary

- success-reclassification-boundary-only
- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix
- Inventory only; no MT5 run; no trading authorization.
"""

TASK310_DOC = """# TASK-310 MQL5 compile artifact hash capture diagnostic

- artifact-hash-capture-diagnostic-only
- not success reclassification
- not TASK-304 success result
- TASK-310 may re-run MetaEditor compile-only only against quarantine copy
- artifact hash must be stdout-only
- artifact hash must not be saved to repository
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- success_reclassification_done=false
- task304_success_result_created=false
- compile_success=false
- future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix
- TASK-311 must not be entered directly
- no MT5 terminal run
- no Strategy Tester run
- no backtest
- no trading
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: f31b85e TASK-309 create MQL5 compile-only success reclassification boundary
- current tag: v0.5.105-task-309-mql5-compile-success-reclassification-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
"""


def fail(message: str) -> int:
    print("TASK-310 artifact hash capture boundary validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(
    root: Path,
    *,
    task310_doc: str | None = TASK310_DOC,
    task309_doc: str | None = TASK309_DOC,
    mq5_files=None,
) -> None:
    if task310_doc is not None:
        write_text(root / "docs" / "V060_TASK_310_MQL5_COMPILE_ARTIFACT_HASH_CAPTURE.md", task310_doc)
    if task309_doc is not None:
        write_text(
            root / "docs" / "V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md",
            task309_doc,
        )
    for rel_path, text in (MQ5_FILES if mq5_files is None else mq5_files).items():
        write_text(root / "mq5" / rel_path, text)
    write_text(
        root / "tools" / "validate_mql5_compile_artifact_hash_capture_boundary.py",
        VALIDATOR_PATH.read_text(encoding="utf-8"),
    )


def load_validator(root: Path):
    validator_path = root / "tools" / "validate_mql5_compile_artifact_hash_capture_boundary.py"
    spec = importlib.util.spec_from_file_location("task310_validator", validator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_validator(root: Path) -> tuple[int, str]:
    module = load_validator(root)
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def expect_fail(result: int, output: str, label: str) -> str:
    if result == 0:
        return f"{label} should fail\n{output}"
    return ""


def test_complete_fixture_passes() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        result, output = run_validator(root)
        if result != 0:
            return f"complete fixture should pass\n{output}"
        required = (
            "mql5_compile_artifact_hash_capture_boundary=true",
            "artifact_hash_capture_diagnostic_only=true",
            "metaeditor_executed=false",
            "mql5_compile_executed=false",
            "success_reclassification_done=false",
            "task304_success_result_created=false",
            "compile_success=false",
            "artifact_hash_stdout_only=true",
            "artifact_hash_saved_to_repo=false",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "repo_mq5_modified=false",
            "mt5_terminal_run=false",
            "strategy_tester_run=false",
            "trading_executed=false",
            "mq5_inventory_files=7",
            "trading_keywords=false",
            "Inventory only; no MT5 run; no trading authorization.",
        )
        for text in required:
            if text not in output:
                return f"validator output missing {text}\n{output}"
    return ""


def test_missing_or_incomplete_docs_fail() -> str:
    cases = (
        ("missing TASK-310 doc", None, TASK309_DOC),
        ("missing TASK-309 doc", TASK310_DOC, None),
        ("missing artifact-hash-capture-diagnostic-only", TASK310_DOC.replace("- artifact-hash-capture-diagnostic-only\n", "", 1), TASK309_DOC),
        ("missing not success reclassification", TASK310_DOC.replace("- not success reclassification\n", "", 1), TASK309_DOC),
        ("missing hash stdout only", TASK310_DOC.replace("- artifact hash must be stdout-only\n", "", 1), TASK309_DOC),
        ("missing hash not saved", TASK310_DOC.replace("- artifact hash must not be saved to repository\n", "", 1), TASK309_DOC),
        ("missing no ex5 copy", TASK310_DOC.replace("- quarantine .ex5 must not be copied to repository\n", "", 1), TASK309_DOC),
        ("missing success_reclassification_done=false", TASK310_DOC.replace("- success_reclassification_done=false\n", "", 1), TASK309_DOC),
        ("missing task304 false", TASK310_DOC.replace("- task304_success_result_created=false\n", "", 1), TASK309_DOC),
        ("missing future TASK-311", TASK310_DOC.replace("- future TASK-311 must be separately authorized by GPT before success reclassification or MQ5 fix\n", "", 1), TASK309_DOC),
    )
    for label, task310_doc, task309_doc in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, task310_doc=task310_doc, task309_doc=task309_doc)
            result, output = run_validator(root)
            error = expect_fail(result, output, label)
            if error:
                return error
    return ""


def test_repo_artifact_and_mq5_guards_fail() -> str:
    cases = (
        ("repo ex5 artifact", {"repo_artifact.ex5": ""}, None),
        ("repo compile log", {"compile.log": "log"}, None),
        ("MQ5 inventory not seven", {}, {k: v for k, v in MQ5_FILES.items() if k != "signals/SignalEngine.mqh"}),
        ("trading keyword", {}, {**MQ5_FILES, "core/EaController.mqh": "class EaController { string x = 'OrderSend'; };\n"}),
    )
    for label, extra_files, mq5_files in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, mq5_files=mq5_files)
            for rel_path, text in extra_files.items():
                write_text(root / rel_path, text)
            result, output = run_validator(root)
            error = expect_fail(result, output, label)
            if error:
                return error
    return ""


def test_validator_source_does_not_call_external_tools() -> str:
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    prohibited = (
        "import subprocess",
        "from subprocess",
        "MetaEditor(",
        "terminal64.exe",
        "/compile:",
    )
    for text in prohibited:
        if text in source:
            return f"validator source contains prohibited execution marker: {text}"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"missing validator: {VALIDATOR_PATH}")
    tests = (
        test_complete_fixture_passes,
        test_missing_or_incomplete_docs_fail,
        test_repo_artifact_and_mq5_guards_fail,
        test_validator_source_does_not_call_external_tools,
    )
    failures = [failure for test in tests if (failure := test())]
    if failures:
        return fail("\n".join(failures))
    print("TASK-310 artifact hash capture boundary validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
