#!/usr/bin/env python3
"""Self-test for TASK-305 MQL5 compile-only failure diagnostic validator."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_only_failure_diagnostic.py"

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

TASK305_DOC = """# TASK-305 MQL5 compile-only failure diagnostic capture

- diagnostic-only
- not compile success
- not TASK-304 success result
- compile_exit_code=1 was observed in TASK-304
- TASK-305 may re-run MetaEditor compile-only only against quarantine copy
- compile log must be stdout-only
- compile log must not be saved to repository
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no MT5 terminal run
- no Strategy Tester run
- no backtest
- no trading
- no manifest generated
- no evidence generated
- no report generated
- current HEAD: 4cbf091 TASK-303 create v0.6.0 compile-only execution authorization planning packet
- current tag: v0.5.100-task-303-v060-compile-only-execution-authorization
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
- TASK-306 must not be entered directly
- future TASK-306 must be separately authorized by GPT before any MQ5 fixes or compile retry
"""


def fail(message: str) -> int:
    print("TASK-305 failure diagnostic validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(root: Path, *, doc_text: str | None = TASK305_DOC, mq5_files=None) -> None:
    if doc_text is not None:
        write_text(root / "docs" / "V060_TASK_305_MQL5_COMPILE_ONLY_FAILURE_DIAGNOSTIC.md", doc_text)
    files = MQ5_FILES if mq5_files is None else mq5_files
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)
    write_text(root / "tools" / "validate_mql5_compile_only_failure_diagnostic.py", VALIDATOR_PATH.read_text(encoding="utf-8"))


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "tools" / "validate_mql5_compile_only_failure_diagnostic.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or "") + (result.stderr or "")


def expect_fail(result: subprocess.CompletedProcess[str], label: str) -> str:
    if result.returncode == 0:
        return f"{label} should fail\n{combined_output(result)}"
    return ""


def test_complete_fixture_passes() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        result = run_validator(root)
        output = combined_output(result)
        if result.returncode != 0:
            return f"complete fixture should pass\n{output}"
        required = (
            "mql5_compile_only_failure_diagnostic=true",
            "diagnostic_only=true",
            "compile_success=false",
            "task304_success_result_created=false",
            "metaeditor_execution_allowed_for_diagnostic=true",
            "compile_log_stdout_only=true",
            "compile_log_saved_to_repo=false",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "repo_mq5_modified=false",
            "mt5_terminal_run=false",
            "strategy_tester_run=false",
            "trading_executed=false",
            "mq5_inventory_files=7",
            "trading_keywords=false",
        )
        for text in required:
            if text not in output:
                return f"validator output missing {text}\n{output}"
    return ""


def test_missing_or_incomplete_doc_fails() -> str:
    cases = (
        ("missing doc", None),
        ("missing diagnostic-only", TASK305_DOC.replace("- diagnostic-only\n", "", 1)),
        ("missing compile exit phrase", TASK305_DOC.replace("- compile_exit_code=1 was observed in TASK-304\n", "", 1)),
        ("missing TASK-304 success phrase", TASK305_DOC.replace("- not TASK-304 success result\n", "", 1)),
        ("missing stdout-only phrase", TASK305_DOC.replace("- compile log must be stdout-only\n", "", 1)),
    )
    for label, doc_text in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, doc_text=doc_text)
            error = expect_fail(run_validator(root), label)
            if error:
                return error
    return ""


def test_repo_artifacts_inventory_and_trading_keywords_fail() -> str:
    cases = (
        ("repo ex5", {"artifact": ("mq5/TradingSystem.ex5", "binary\n")}),
        ("repo compile log", {"artifact": ("compile.log", "log\n")}),
        ("inventory not seven", {"remove": "logger/Logger.mqh"}),
        ("trading keyword", {"mq5_files": {**MQ5_FILES, "core/EaController.mqh": "void Probe(){ CTrade; }\n"}}),
    )
    for label, case in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            files = dict(case.get("mq5_files", MQ5_FILES))
            if "remove" in case:
                files.pop(case["remove"])
            build_project(root, mq5_files=files)
            if "artifact" in case:
                rel_path, text = case["artifact"]
                write_text(root / rel_path, text)
            error = expect_fail(run_validator(root), label)
            if error:
                return error
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")
    tests = [
        test_complete_fixture_passes,
        test_missing_or_incomplete_doc_fails,
        test_repo_artifacts_inventory_and_trading_keywords_fail,
    ]
    for test in tests:
        error = test()
        if error:
            return fail(error)
    print("TASK-305 failure diagnostic validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
