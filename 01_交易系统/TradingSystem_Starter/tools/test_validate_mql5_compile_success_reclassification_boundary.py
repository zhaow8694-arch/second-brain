#!/usr/bin/env python3
"""Self-test for TASK-309 MQL5 success reclassification boundary validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT_DIR / "tools" / "validate_mql5_compile_success_reclassification_boundary.py"
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
- quarantine_ex5_artifact_detected=true
- quarantine_ex5_artifact_count=1
- compile_log_semantic_success=true
- compile_exit_code=1
- classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- compile_success=false
- task304_success_result_created=false
- Inventory only; no MT5 run; no trading authorization.
"""

TASK308_DOC = """# TASK-308 MQL5 compile diagnostic artifact proof and success reclassification boundary

- diagnostic-proof-boundary-only
- TASK-308 defined diagnostic artifact proof boundary
- future task must compute quarantine artifact hash before deleting quarantine directory
- Inventory only; no MT5 run; no trading authorization.
"""

TASK309_DOC = """# TASK-309 MQL5 compile-only success reclassification boundary

- planning-only
- success-reclassification-boundary-only
- not compile execution
- not MetaEditor execution in TASK-309
- not MT5 run
- not Strategy Tester
- not backtest
- not trading
- not success reclassification in TASK-309
- TASK-307 observed quarantine_ex5_artifact_detected=true
- TASK-307 observed quarantine_ex5_artifact_count=1
- TASK-307 observed compile_log_semantic_success=true
- TASK-307 observed compile_exit_code=1
- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly
- TASK-307 compile_success=false
- TASK-307 task304_success_result_created=false
- TASK-308 defined diagnostic artifact proof boundary
- TASK-309 does not create TASK-304 success result doc
- TASK-309 does not reclassify compile success
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no .ex5 artifact generated in repository
- no compile log generated in repository
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 915b19f TASK-308 create MQL5 compile diagnostic artifact proof boundary
- current tag: v0.5.104-task-308-mql5-compile-diagnostic-artifact-proof-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix
- TASK-310 must not be entered directly
- future GPT boundary explicitly authorizes success reclassification attempt
- future task may re-run MetaEditor compile-only only against quarantine copy
- future task must capture quarantine .ex5 metadata before deletion
- future task must compute quarantine artifact hash before deleting quarantine directory
- future task must output quarantine artifact hash to stdout only
- future task must output quarantine artifact size
- future task must output quarantine artifact temporary path only
- future task must not copy .ex5 into repository
- future task must not save compile log into repository
- future task must capture compile log semantic result to stdout only
- future task must prove compile_log_semantic_success=true
- future task must prove compile_log_errors=0
- future task must prove quarantine_ex5_artifact_detected=true
- future task must prove quarantine_ex5_artifact_count>=1
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
"""


def fail(message: str) -> int:
    print("TASK-309 success reclassification boundary validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(
    root: Path,
    *,
    task309_doc: str | None = TASK309_DOC,
    task308_doc: str | None = TASK308_DOC,
    task307_doc: str | None = TASK307_DOC,
    mq5_files=None,
) -> None:
    if task309_doc is not None:
        write_text(
            root / "docs" / "V060_TASK_309_MQL5_COMPILE_ONLY_SUCCESS_RECLASSIFICATION_BOUNDARY.md",
            task309_doc,
        )
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
        root / "tools" / "validate_mql5_compile_success_reclassification_boundary.py",
        VALIDATOR_PATH.read_text(encoding="utf-8"),
    )


def load_validator(root: Path):
    validator_path = root / "tools" / "validate_mql5_compile_success_reclassification_boundary.py"
    spec = importlib.util.spec_from_file_location("task309_validator", validator_path)
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
            "mql5_compile_success_reclassification_boundary=true",
            "success_reclassification_boundary_only=true",
            "metaeditor_executed=false",
            "mql5_compile_executed=false",
            "success_reclassification_done=false",
            "task304_success_result_created=false",
            "compile_exit_code=1",
            "compile_log_semantic_success=true",
            "previous_classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
            "compile_success=false",
            "future_task_310_requires_gpt_boundary=true",
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
        ("missing TASK-309 doc", None, TASK308_DOC, TASK307_DOC),
        ("missing TASK-308 doc", TASK309_DOC, None, TASK307_DOC),
        ("missing TASK-307 doc", TASK309_DOC, TASK308_DOC, None),
        (
            "missing success boundary",
            TASK309_DOC.replace("- success-reclassification-boundary-only\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing no success reclassification",
            TASK309_DOC.replace("- not success reclassification in TASK-309\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing quarantine ex5 observation",
            TASK309_DOC.replace("- TASK-307 observed quarantine_ex5_artifact_detected=true\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing quarantine count observation",
            TASK309_DOC.replace("- TASK-307 observed quarantine_ex5_artifact_count=1\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing semantic success",
            TASK309_DOC.replace("- TASK-307 observed compile_log_semantic_success=true\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing compile exit code",
            TASK309_DOC.replace("- TASK-307 observed compile_exit_code=1\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing artifact anomaly classification",
            TASK309_DOC.replace(
                "- TASK-307 classification=compiled_artifact_with_metaeditor_exit_code_anomaly\n",
                "",
                1,
            ),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing compile success false",
            TASK309_DOC.replace("- TASK-307 compile_success=false\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing task304 false",
            TASK309_DOC.replace("- TASK-307 task304_success_result_created=false\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing TASK-310 boundary",
            TASK309_DOC.replace(
                "- future TASK-310 must be separately authorized by GPT before any compile retry, artifact hash capture, success reclassification, or MQ5 fix\n",
                "",
                1,
            ),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing future hash condition",
            TASK309_DOC.replace(
                "- future task must compute quarantine artifact hash before deleting quarantine directory\n",
                "",
                1,
            ),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing stdout-only hash condition",
            TASK309_DOC.replace(
                "- future task must output quarantine artifact hash to stdout only\n",
                "",
                1,
            ),
            TASK308_DOC,
            TASK307_DOC,
        ),
        (
            "missing no copy ex5 condition",
            TASK309_DOC.replace("- future task must not copy .ex5 into repository\n", "", 1),
            TASK308_DOC,
            TASK307_DOC,
        ),
    )
    for label, task309_doc, task308_doc, task307_doc in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(
                root,
                task309_doc=task309_doc,
                task308_doc=task308_doc,
                task307_doc=task307_doc,
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
        (
            "trading keyword",
            {},
            {**MQ5_FILES, "core/EaController.mqh": "class EaController { string x = 'OrderSend'; };\n"},
        ),
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
    print("TASK-309 success reclassification boundary validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
