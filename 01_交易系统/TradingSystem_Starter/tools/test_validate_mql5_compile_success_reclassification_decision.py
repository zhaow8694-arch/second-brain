#!/usr/bin/env python3
"""Self-test for TASK-312 MQL5 compile success reclassification decision validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_success_reclassification_decision.py"
FAKE_HASH = "a" * 64

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

TASK311_TEXT = """# TASK-311 MQL5 compile success reclassification decision boundary

- success-reclassification-decision-boundary-only
"""

TASK312_TEXT = """# TASK-312 MQL5 compile-only success reclassification decision

- controlled-success-reclassification-attempt
- success_reclassification_decision=PASS
- compile_only_reclassified_success=true
- compile_success=true
- compile_success_scope=compile-only-diagnostic
- not trading authorization
- not deployment readiness
- not backtest readiness
- not strategy readiness
- MetaEditor executed only against quarantine copy
- MQL5 compile executed only against quarantine copy
- MT5 terminal run=false
- Strategy Tester run=false
- trading_executed=false
- quarantine_ex5_artifact_detected=true
- quarantine_ex5_artifact_count>=1
- artifact_hash_captured=true
- artifact_hash_stdout_only=true
- artifact_hash_saved_to_repo=false
- do not include actual artifact hash value in this doc
- quarantine_ex5_artifact_size_bytes captured
- quarantine_deleted=true
- repo_ex5_artifacts=false
- repo_compile_logs=false
- repo_mq5_modified=false
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 9ce8ca5 TASK-311 create MQL5 compile success reclassification decision boundary
- current tag: v0.5.107-task-311-mql5-compile-success-reclassification-decision-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-313 must be separately authorized by GPT before any MT5 run, Strategy Tester, backtest, deployment, or trading-related step
- TASK-313 must not be entered directly
"""


def fail(message: str) -> int:
    print("MQL5 compile success reclassification decision validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mql5_compile_success_reclassification_decision",
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
    task311_text: str | None = TASK311_TEXT,
    task312_text: str | None = TASK312_TEXT,
    mq5_overrides=None,
) -> None:
    if task311_text is not None:
        write_text(
            root / "docs" / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md",
            task311_text,
        )
    if task312_text is not None:
        write_text(
            root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md",
            task312_text,
        )
    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_validator(module, root: Path):
    module.ROOT_DIR = root
    module.TASK311_DOC_PATH = (
        root / "docs" / "V060_TASK_311_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION_BOUNDARY.md"
    )
    module.TASK312_DOC_PATH = (
        root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
    )
    module.MQ5_ROOT = root / "mq5"
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def assert_fails_when(module, *, task311_text=TASK311_TEXT, task312_text=TASK312_TEXT, setup=None) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task311_text=task311_text, task312_text=task312_text)
        if setup:
            setup(root)
        result, output = run_validator(module, root)
        if result == 0:
            return f"expected validation failure\n{output}"
    return ""


def test_complete_fixture_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        result, output = run_validator(module, root)
        if result != 0:
            return f"complete fixture should pass\n{output}"
        required = (
            "mql5_compile_success_reclassification_decision=true",
            "success_reclassification_decision=PASS",
            "compile_only_reclassified_success=true",
            "compile_success=true",
            "compile_success_scope=compile-only-diagnostic",
            "trading_authorization=false",
            "deployment_readiness=false",
            "backtest_readiness=false",
            "strategy_readiness=false",
            "artifact_hash_stdout_only=true",
            "artifact_hash_saved_to_repo=false",
            "actual_artifact_hash_stored_in_repo=false",
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
                return f"complete fixture output missing {text}\n{output}"
    return ""


def test_missing_required_state_fails(module) -> str:
    cases = (
        ("missing TASK-312 doc", None, TASK311_TEXT),
        (
            "missing TASK-311 boundary doc",
            TASK312_TEXT,
            None,
        ),
        (
            "missing PASS decision",
            TASK312_TEXT.replace("- success_reclassification_decision=PASS\n", ""),
            TASK311_TEXT,
        ),
        (
            "missing reclassified success",
            TASK312_TEXT.replace("- compile_only_reclassified_success=true\n", ""),
            TASK311_TEXT,
        ),
        (
            "missing compile success scope",
            TASK312_TEXT.replace("- compile_success_scope=compile-only-diagnostic\n", ""),
            TASK311_TEXT,
        ),
        (
            "missing no trading authorization",
            TASK312_TEXT.replace("- not trading authorization\n", ""),
            TASK311_TEXT,
        ),
        (
            "missing deployment readiness denial",
            TASK312_TEXT.replace("- not deployment readiness\n", ""),
            TASK311_TEXT,
        ),
        (
            "missing hash stdout-only",
            TASK312_TEXT.replace("- artifact_hash_stdout_only=true\n", ""),
            TASK311_TEXT,
        ),
        (
            "missing hash not saved",
            TASK312_TEXT.replace("- artifact_hash_saved_to_repo=false\n", ""),
            TASK311_TEXT,
        ),
        (
            "contains actual hash-like value",
            TASK312_TEXT + f"\n- quarantine_ex5_artifact_sha256={FAKE_HASH}\n",
            TASK311_TEXT,
        ),
    )
    for label, task312_text, task311_text in cases:
        error = assert_fails_when(
            module,
            task311_text=task311_text,
            task312_text=task312_text,
        )
        if error:
            return f"{label}: {error}"
    return ""


def test_repo_artifact_inventory_and_keyword_failures(module) -> str:
    cases = (
        ("repo .ex5", lambda root: write_text(root / "mq5" / "TradingSystem.ex5", "artifact\n")),
        ("repo compile log", lambda root: write_text(root / "compile.log", "log\n")),
        ("missing MQ5 file", lambda root: (root / "mq5" / "logger" / "Logger.mqh").unlink()),
        (
            "trading keyword",
            lambda root: write_text(root / "mq5" / "core" / "EaController.mqh", "void Probe(){ CTrade; }\n"),
        ),
    )
    for label, setup in cases:
        error = assert_fails_when(module, setup=setup)
        if error:
            return f"{label}: {error}"
    return ""


def test_validator_does_not_call_subprocess_or_mt5(module) -> str:
    text = VALIDATOR_PATH.read_text(encoding="utf-8")
    forbidden = ("import subprocess", "subprocess.", "Popen(", "run(", "terminal64.exe", "/compile")
    for marker in forbidden:
        if marker in text:
            return f"validator source contains forbidden execution marker: {marker}"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")
    module = load_validator()
    tests = [
        test_complete_fixture_passes,
        test_missing_required_state_fails,
        test_repo_artifact_inventory_and_keyword_failures,
        test_validator_does_not_call_subprocess_or_mt5,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)
    print("MQL5 compile success reclassification decision validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
