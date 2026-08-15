#!/usr/bin/env python3
"""Self-test for TASK-311 success reclassification decision boundary validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT_DIR
    / "tools"
    / "validate_mql5_compile_success_reclassification_decision_boundary.py"
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

TASK309_DOC = """# TASK-309 MQL5 compile-only success reclassification boundary

- success-reclassification-boundary-only
- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix
- Inventory only; no MT5 run; no trading authorization.
"""

TASK310_DOC = """# TASK-310 MQL5 compile artifact hash capture diagnostic

- artifact-hash-capture-diagnostic-only
- artifact hash must be stdout-only
- artifact hash must not be saved to repository
- compile_success=false
- success_reclassification_done=false
- task304_success_result_created=false
- Inventory only; no MT5 run; no trading authorization.
"""

TASK311_DOC = """# TASK-311 MQL5 compile success reclassification decision boundary

- planning-only
- success-reclassification-decision-boundary-only
- not compile execution
- not MetaEditor execution in TASK-311
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-311
- TASK-310 observed artifact_hash_captured=true
- TASK-310 observed quarantine_ex5_artifact_size_bytes=70178
- TASK-310 observed compile_exit_code=1
- TASK-310 observed compile_log_semantic_success=true
- TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly
- TASK-310 compile_success=false
- TASK-310 success_reclassification_done=false
- TASK-310 task304_success_result_created=false
- TASK-310 repo_ex5_artifacts=false
- TASK-310 repo_compile_logs=false
- TASK-310 repo_mq5_modified=false
- TASK-310 artifact hash was stdout-only and must not be stored in repository
- TASK-311 does not store artifact hash
- TASK-311 does not create TASK-304 success result doc
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry
- TASK-312 must not be entered directly
- future GPT boundary explicitly authorizes success reclassification decision
- future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash
- future task must not store artifact hash in repository unless GPT explicitly authorizes hash recording
- future task must keep artifact metadata stdout-only unless separately authorized
- future task must prove compile_log_semantic_success=true
- future task must prove compile_log_errors=0
- future task must prove quarantine_ex5_artifact_detected=true
- future task must prove quarantine_ex5_artifact_count>=1
- future task must prove quarantine artifact hash is captured
- future task must prove quarantine artifact size is captured
- future task must delete quarantine directory before completion
- future task must prove quarantine_deleted=true
- future task must prove repo_ex5_artifacts=false after cleanup
- future task must prove repo_compile_logs=false after cleanup
- future task must prove repo_mq5_modified=false after cleanup
- future task must prove trading_keywords=false after cleanup
- future task must prove MQ5 inventory remains 7 files
- future task must not run MT5 terminal
- future task must not run Strategy Tester
- future task must not backtest
- future task must not trade
- future task must not create official manifest
- future task must not create evidence
- future task must not create report
- future task must not copy external evidence
- future success reclassification must remain compile-only and no-trade
- future success reclassification must not imply deployment readiness
- future success reclassification must not imply strategy readiness
- future success reclassification must not imply backtest readiness
- future success reclassification must not imply trading authorization
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- current HEAD: 8cc7593 TASK-310 implement quarantined MQL5 compile artifact hash capture diagnostic
- current tag: v0.5.106-task-310-mql5-compile-artifact-hash-capture
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- Inventory only; no MT5 run; no trading authorization.
"""


def fail(message: str) -> int:
    print("TASK-311 success reclassification decision boundary validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(
    root: Path,
    *,
    task311_doc: str | None = TASK311_DOC,
    task310_doc: str | None = TASK310_DOC,
    task309_doc: str | None = TASK309_DOC,
    mq5_files=None,
) -> None:
    if task311_doc is not None:
        write_text(
            root / "docs" / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md",
            task311_doc,
        )
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
        root / "tools" / "validate_mql5_compile_success_reclassification_decision_boundary.py",
        VALIDATOR_PATH.read_text(encoding="utf-8"),
    )


def load_validator(root: Path):
    validator_path = (
        root
        / "tools"
        / "validate_mql5_compile_success_reclassification_decision_boundary.py"
    )
    spec = importlib.util.spec_from_file_location("task311_validator", validator_path)
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
            "mql5_compile_success_reclassification_decision_boundary=true",
            "success_reclassification_decision_boundary_only=true",
            "metaeditor_executed=false",
            "mql5_compile_executed=false",
            "success_reclassification_done=false",
            "task304_success_result_created=false",
            "compile_exit_code=1",
            "compile_log_semantic_success=true",
            "previous_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly",
            "compile_success=false",
            "artifact_hash_stored_in_repo=false",
            "future_task_312_requires_gpt_boundary=true",
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
        ("missing TASK-311 doc", None, TASK310_DOC, TASK309_DOC),
        ("missing TASK-310 doc", TASK311_DOC, None, TASK309_DOC),
        ("missing TASK-309 doc", TASK311_DOC, TASK310_DOC, None),
        (
            "missing success-reclassification-decision-boundary-only",
            TASK311_DOC.replace("- success-reclassification-decision-boundary-only\n", "", 1),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing not success reclassification",
            TASK311_DOC.replace("- not success reclassification in TASK-311\n", "", 1),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing artifact hash captured",
            TASK311_DOC.replace("- TASK-310 observed artifact_hash_captured=true\n", "", 1),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing artifact hash stdout-only",
            TASK311_DOC.replace(
                "- TASK-310 artifact hash was stdout-only and must not be stored in repository\n",
                "",
                1,
            ),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing previous classification",
            TASK311_DOC.replace(
                "- TASK-310 observed compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly\n",
                "",
                1,
            ),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing compile_success=false",
            TASK311_DOC.replace("- TASK-310 compile_success=false\n", "", 1),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing success_reclassification_done=false",
            TASK311_DOC.replace("- TASK-310 success_reclassification_done=false\n", "", 1),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing task304 false",
            TASK311_DOC.replace("- TASK-310 task304_success_result_created=false\n", "", 1),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing future TASK-312",
            TASK311_DOC.replace(
                "- future TASK-312 must be separately authorized by GPT before any success reclassification, MQ5 fix, or compile retry\n",
                "",
                1,
            ),
            TASK310_DOC,
            TASK309_DOC,
        ),
        (
            "missing future hash reuse condition",
            TASK311_DOC.replace(
                "- future task must re-run quarantine artifact hash capture or explicitly authorize use of previous stdout hash\n",
                "",
                1,
            ),
            TASK310_DOC,
            TASK309_DOC,
        ),
    )
    for label, task311_doc, task310_doc, task309_doc in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(
                root,
                task311_doc=task311_doc,
                task310_doc=task310_doc,
                task309_doc=task309_doc,
            )
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
        ("trading keyword", {}, {**MQ5_FILES, "core/EaController.mqh": "class EaController { string x = 'CTrade'; };\n"}),
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
    print("TASK-311 success reclassification decision boundary validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
