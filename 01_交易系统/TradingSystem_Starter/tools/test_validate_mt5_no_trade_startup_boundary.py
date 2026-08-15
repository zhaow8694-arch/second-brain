#!/usr/bin/env python3
"""Self-test for TASK-313 MT5 no-trade startup boundary validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mt5_no_trade_startup_boundary.py"

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

TASK312_TEXT = """# TASK-312 MQL5 compile-only success reclassification decision

- controlled-success-reclassification-attempt
- compile_success_scope=compile-only-diagnostic
"""

TASK313_TEXT = """# TASK-313 MT5 terminal no-trade startup boundary packet

- planning-only
- mt5-startup-boundary-only
- future MT5 terminal no-trade startup candidate
- not MT5 run in TASK-313
- not terminal64.exe execution in TASK-313
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- not evidence generation authorization
- not manifest generation authorization
- not report generation authorization
- no MT5 terminal run executed in TASK-313
- no Strategy Tester executed in TASK-313
- no backtest executed in TASK-313
- no trading executed in TASK-313
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: efb4a45 TASK-312 implement controlled MQL5 compile-only success reclassification decision
- current tag: v0.5.108-task-312-mql5-compile-success-reclassification-decision
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-314 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup
- future task must remain no-trade
- future task must not run Strategy Tester
- future task must not run backtest
- future task must not run simulation trading
- future task must not run real trading
- future task must not place orders
- future task must not create official manifest unless separately authorized
- future task must not create evidence unless separately authorized
- future task must not create report unless separately authorized
- future task must use a no-trade config
- future task must prove InpEnableTrading=false before startup
- future task must prove trading keywords false before startup
- future task must prove MQ5 inventory remains 7 files before startup
- future task must prove repo_ex5_artifacts=false before startup
- future task must prove repo_compile_logs=false before startup
- future task must prove repo_mq5_modified=false before startup
- future task must capture terminal startup result stdout-only unless separately authorized
- future task must not copy external evidence
- future task must not imply deployment readiness
- future task must not imply strategy readiness
- future task must not imply backtest readiness
- future task must not imply trading authorization
"""


def fail(message: str) -> int:
    print("MT5 no-trade startup boundary validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mt5_no_trade_startup_boundary",
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
    task312_text: str | None = TASK312_TEXT,
    task313_text: str | None = TASK313_TEXT,
    mq5_overrides=None,
) -> None:
    if task312_text is not None:
        write_text(root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md", task312_text)
    if task313_text is not None:
        write_text(root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md", task313_text)
    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_validator(module, root: Path):
    module.ROOT_DIR = root
    module.TASK312_DOC_PATH = root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
    module.TASK313_DOC_PATH = root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
    module.MQ5_ROOT = root / "mq5"
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def assert_fails_when(module, *, task312_text=TASK312_TEXT, task313_text=TASK313_TEXT, setup=None) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task312_text=task312_text, task313_text=task313_text)
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
            "mt5_no_trade_startup_boundary=true",
            "mt5_startup_boundary_only=true",
            "mt5_terminal_executed=false",
            "terminal64_executed=false",
            "strategy_tester_executed=false",
            "backtest_executed=false",
            "trading_executed=false",
            "trading_authorization=false",
            "deployment_readiness=false",
            "backtest_readiness=false",
            "strategy_readiness=false",
            "future_task_314_requires_gpt_boundary=true",
            "mq5_inventory_files=7",
            "trading_keywords=false",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "repo_mq5_modified=false",
            "Inventory only; no MT5 run; no trading authorization.",
        )
        for text in required:
            if text not in output:
                return f"complete fixture output missing {text}\n{output}"
    return ""


def test_missing_required_state_fails(module) -> str:
    cases = (
        ("missing TASK-313 doc", TASK312_TEXT, None),
        ("missing TASK-312 doc", None, TASK313_TEXT),
        (
            "missing mt5-startup-boundary-only",
            TASK312_TEXT,
            TASK313_TEXT.replace("- mt5-startup-boundary-only\n", ""),
        ),
        (
            "missing not MT5 run in TASK-313",
            TASK312_TEXT,
            TASK313_TEXT.replace("- not MT5 run in TASK-313\n", ""),
        ),
        (
            "missing not Strategy Tester authorization",
            TASK312_TEXT,
            TASK313_TEXT.replace("- not Strategy Tester authorization\n", ""),
        ),
        (
            "missing not trading authorization",
            TASK312_TEXT,
            TASK313_TEXT.replace("- not trading authorization\n", ""),
        ),
        (
            "missing TASK-312 compile-only scope",
            TASK312_TEXT,
            TASK313_TEXT.replace("- TASK-312 compile_success_scope=compile-only-diagnostic\n", ""),
        ),
        (
            "missing TASK-312 trading authorization false",
            TASK312_TEXT,
            TASK313_TEXT.replace("- TASK-312 trading_authorization=false\n", ""),
        ),
        (
            "missing future TASK-314 boundary",
            TASK312_TEXT,
            TASK313_TEXT.replace("- future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt\n", ""),
        ),
        (
            "missing InpEnableTrading future proof",
            TASK312_TEXT,
            TASK313_TEXT.replace("- future task must prove InpEnableTrading=false before startup\n", ""),
        ),
        (
            "missing future Strategy Tester prohibition",
            TASK312_TEXT,
            TASK313_TEXT.replace("- future task must not run Strategy Tester\n", ""),
        ),
    )
    for label, task312_text, task313_text in cases:
        error = assert_fails_when(
            module,
            task312_text=task312_text,
            task313_text=task313_text,
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
            lambda root: write_text(root / "mq5" / "core" / "EaController.mqh", "void Probe(){ OrderSend; }\n"),
        ),
    )
    for label, setup in cases:
        error = assert_fails_when(module, setup=setup)
        if error:
            return f"{label}: {error}"
    return ""


def test_validator_does_not_call_subprocess_or_mt5(module) -> str:
    text = VALIDATOR_PATH.read_text(encoding="utf-8")
    forbidden = (
        "import subprocess",
        "subprocess.",
        "Popen(",
        "run(",
        "/compile",
    )
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
    print("MT5 no-trade startup boundary validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
