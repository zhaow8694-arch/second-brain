#!/usr/bin/env python3
"""Self-test for TASK-307 MQL5 compile diagnostic artifact classification validator."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_diagnostic_artifact_classification.py"

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

TASK307_DOC = """# TASK-307 MQL5 compile diagnostic artifact classification

- diagnostic-artifact-classification-only
- not TASK-304 success result
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- TASK-307 may re-run MetaEditor compile-only only against quarantine copy
- quarantine artifact inspection before cleanup
- quarantine .ex5 must not be copied to repository
- compile log must remain stdout-only
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- task304_success_result_created=false
- compile_success=false unless a future GPT boundary explicitly reclassifies success
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 560079c TASK-306 implement MQL5 compile-only diagnostic result classification
- current tag: v0.5.102-task-306-mql5-compile-diagnostic-classification
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-308 must be separately authorized by GPT before any compile retry or MQ5 fix
- TASK-308 must not be entered directly
"""


def fail(message: str) -> int:
    print("TASK-307 diagnostic artifact classification validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(root: Path, *, doc_text: str | None = TASK307_DOC, mq5_files=None) -> None:
    if doc_text is not None:
        write_text(
            root / "docs" / "V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md",
            doc_text,
        )
    files = MQ5_FILES if mq5_files is None else mq5_files
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)
    write_text(
        root / "tools" / "validate_mql5_compile_diagnostic_artifact_classification.py",
        VALIDATOR_PATH.read_text(encoding="utf-8"),
    )


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "validate_mql5_compile_diagnostic_artifact_classification.py"),
        ],
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
            "mql5_compile_diagnostic_artifact_classification=true",
            "diagnostic_artifact_classification_only=true",
            "metaeditor_executed=false",
            "mql5_compile_executed=false",
            "task304_success_result_created=false",
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


def test_missing_or_incomplete_doc_fails() -> str:
    cases = (
        ("missing doc", None),
        ("missing classification", TASK307_DOC.replace("- diagnostic-artifact-classification-only\n", "", 1)),
        ("missing no task304", TASK307_DOC.replace("- not TASK-304 success result\n", "", 1)),
        ("missing quarantine inspection", TASK307_DOC.replace("- quarantine artifact inspection before cleanup\n", "", 1)),
        ("missing repo ex5 false", TASK307_DOC.replace("- repo_ex5_artifacts=false\n", "", 1)),
        ("missing repo compile logs false", TASK307_DOC.replace("- repo_compile_logs=false\n", "", 1)),
        ("missing task304 false", TASK307_DOC.replace("- task304_success_result_created=false\n", "", 1)),
        ("missing task308 boundary", TASK307_DOC.replace("- TASK-308 must not be entered directly\n", "", 1)),
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


def test_validator_does_not_import_subprocess_or_compile_tools() -> str:
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    forbidden = ("import subprocess", "MetaEditor(", "terminal64.exe", "/compile:")
    for text in forbidden:
        if text in source:
            return f"validator source should not contain {text}"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")
    tests = [
        test_complete_fixture_passes,
        test_missing_or_incomplete_doc_fails,
        test_repo_artifacts_inventory_and_trading_keywords_fail,
        test_validator_does_not_import_subprocess_or_compile_tools,
    ]
    for test in tests:
        error = test()
        if error:
            return fail(error)
    print("TASK-307 diagnostic artifact classification validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
