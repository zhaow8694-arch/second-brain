#!/usr/bin/env python3
"""Self-test for TASK-308 MQL5 diagnostic artifact proof boundary validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT_DIR / "tools" / "validate_mql5_compile_diagnostic_artifact_proof_boundary.py"
)

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
"""

TASK308_DOC = """# TASK-308 MQL5 compile diagnostic artifact proof and success reclassification boundary

- planning-only
- diagnostic-proof-boundary-only
- not compile execution
- not MetaEditor execution in TASK-308
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-308
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-307 compile_success=false
- TASK-307 task304_success_result_created=false
- TASK-308 does not create TASK-304 success result doc
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 499bebe TASK-307 implement MQL5 compile diagnostic artifact classification
- current tag: v0.5.103-task-307-mql5-compile-diagnostic-artifact-classification
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification
- TASK-309 must not be entered directly
- future GPT boundary explicitly authorizes success reclassification attempt
- future task may re-run MetaEditor compile-only only against quarantine copy
- future task must capture quarantine .ex5 metadata before deletion
- future task must output artifact metadata to stdout only
- future task must not copy .ex5 into repository
- future task must not save compile log into repository
- future task must compute quarantine artifact hash before deleting quarantine directory
- future task must output quarantine artifact size
- future task must output quarantine artifact path as temporary path only
- future task must delete quarantine directory before completion
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must still not run MT5 terminal
- future task must still not run Strategy Tester
- future task must still not trade
- future task must not create official manifest / evidence / report unless separately authorized
"""


def fail(message: str) -> int:
    print("TASK-308 diagnostic artifact proof boundary validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(
    root: Path,
    *,
    task308_doc: str | None = TASK308_DOC,
    task307_doc: str | None = TASK307_DOC,
    mq5_files=None,
) -> None:
    if task308_doc is not None:
        write_text(
            root / "docs" / "V060_TASK_308_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_PROOF_BOUNDARY.md",
            task308_doc,
        )
    if task307_doc is not None:
        write_text(
            root / "docs" / "V060_TASK_307_MQL5_COMPILE_DIAGNOSTIC_ARTIFACT_CLASSIFICATION.md",
            task307_doc,
        )
    for rel_path, text in (MQ5_FILES if mq5_files is None else mq5_files).items():
        write_text(root / "mq5" / rel_path, text)
    write_text(
        root / "tools" / "validate_mql5_compile_diagnostic_artifact_proof_boundary.py",
        VALIDATOR_PATH.read_text(encoding="utf-8"),
    )


def load_validator(root: Path):
    validator_path = root / "tools" / "validate_mql5_compile_diagnostic_artifact_proof_boundary.py"
    spec = importlib.util.spec_from_file_location("task308_validator", validator_path)
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
            "mql5_compile_diagnostic_artifact_proof_boundary=true",
            "diagnostic_proof_boundary_only=true",
            "metaeditor_executed=false",
            "mql5_compile_executed=false",
            "success_reclassification_done=false",
            "task304_success_result_created=false",
            "compile_exit_code=1",
            "compile_log_semantic_success=true",
            "previous_classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
            "future_task_309_requires_gpt_boundary=true",
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
        ("missing TASK-308 doc", None, TASK307_DOC),
        ("missing TASK-307 doc", TASK308_DOC, None),
        ("missing proof boundary", TASK308_DOC.replace("- diagnostic-proof-boundary-only\n", "", 1), TASK307_DOC),
        (
            "missing no success reclassification",
            TASK308_DOC.replace("- not success reclassification in TASK-308\n", "", 1),
            TASK307_DOC,
        ),
        (
            "missing quarantine ex5 observation",
            TASK308_DOC.replace("- TASK-307 observed quarantine_ex5_artifact_detected=true\n", "", 1),
            TASK307_DOC,
        ),
        (
            "missing semantic success",
            TASK308_DOC.replace("- TASK-307 observed compile_log_semantic_success=true\n", "", 1),
            TASK307_DOC,
        ),
        (
            "missing compile exit code",
            TASK308_DOC.replace("- TASK-307 observed compile_exit_code=1\n", "", 1),
            TASK307_DOC,
        ),
        (
            "missing artifact anomaly classification",
            TASK308_DOC.replace(
                "- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n",
                "",
                1,
            ),
            TASK307_DOC,
        ),
        (
            "missing task304 false",
            TASK308_DOC.replace("- TASK-307 task304_success_result_created=false\n", "", 1),
            TASK307_DOC,
        ),
        (
            "missing TASK-309 boundary",
            TASK308_DOC.replace(
                "- future TASK-309 must be separately authorized by GPT before any compile retry, MQ5 fix, artifact hash capture, or success reclassification\n",
                "",
                1,
            ),
            TASK307_DOC,
        ),
        (
            "missing future hash condition",
            TASK308_DOC.replace(
                "- future task must compute quarantine artifact hash before deleting quarantine directory\n",
                "",
                1,
            ),
            TASK307_DOC,
        ),
    )
    for label, task308_doc, task307_doc in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, task308_doc=task308_doc, task307_doc=task307_doc)
            result, output = run_validator(root)
            error = expect_fail(result, output, label)
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
            result, output = run_validator(root)
            error = expect_fail(result, output, label)
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
        test_missing_or_incomplete_docs_fail,
        test_repo_artifacts_inventory_and_trading_keywords_fail,
        test_validator_does_not_import_subprocess_or_compile_tools,
    ]
    for test in tests:
        error = test()
        if error:
            return fail(error)
    print("TASK-308 diagnostic artifact proof boundary validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
