#!/usr/bin/env python3
"""Self-test for TASK-314 MT5 no-trade startup command discovery validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mt5_no_trade_startup_command_discovery.py"

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

- mt5-startup-boundary-only
- future TASK-314 must be separately authorized by GPT before any MT5 terminal startup attempt
"""

TASK314_TEXT = """# TASK-314 MT5 no-trade startup command discovery boundary

- command-discovery-only
- mt5-startup-preparation-only
- not MT5 run in TASK-314
- not terminal64.exe execution in TASK-314
- not terminal.exe execution in TASK-314
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-314
- no Strategy Tester executed in TASK-314
- no backtest executed in TASK-314
- no trading executed in TASK-314
- no manifest generated
- no evidence generated
- no report generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 6d1c8c1 TASK-313 create MT5 no-trade startup boundary packet
- current tag: v0.5.109-task-313-mt5-no-trade-startup-boundary
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-315 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-315 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup
- future startup must remain no-trade
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must not create official manifest unless separately authorized
- future startup must not create evidence unless separately authorized
- future startup must not create report unless separately authorized
- future startup must use no-trade startup template
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must capture startup result stdout-only unless separately authorized
- future startup must not copy external evidence
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
"""


def fail(message: str) -> int:
    print("MT5 no-trade startup command discovery validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mt5_no_trade_startup_command_discovery",
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
    task314_text: str | None = TASK314_TEXT,
    mq5_overrides=None,
) -> None:
    if task312_text is not None:
        write_text(root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md", task312_text)
    if task313_text is not None:
        write_text(root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md", task313_text)
    if task314_text is not None:
        write_text(root / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md", task314_text)
    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_validator(module, root: Path, *, candidates=(), which_result=None):
    module.ROOT_DIR = root
    module.TASK312_DOC_PATH = root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
    module.TASK313_DOC_PATH = root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
    module.TASK314_DOC_PATH = root / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
    module.MQ5_ROOT = root / "mq5"
    module.COMMON_TERMINAL_CANDIDATES = tuple(Path(path) for path in candidates)
    module.shutil.which = lambda executable: which_result
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def assert_fails_when(module, *, task312_text=TASK312_TEXT, task313_text=TASK313_TEXT, task314_text=TASK314_TEXT, setup=None) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task312_text=task312_text, task313_text=task313_text, task314_text=task314_text)
        if setup:
            setup(root)
        result, output = run_validator(module, root)
        if result == 0:
            return f"expected validation failure\n{output}"
    return ""


def test_complete_fixture_passes_with_candidate(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        candidate = root / "terminal64.exe"
        build_project(root)
        write_text(candidate, "fake executable\n")
        result, output = run_validator(module, root, candidates=(candidate,))
        if result != 0:
            return f"complete fixture with candidate should pass\n{output}"
        required = (
            "mt5_no_trade_startup_command_discovery=true",
            "command_discovery_only=true",
            "mt5_startup_preparation_only=true",
            "mt5_terminal_executed=false",
            "terminal64_executed=false",
            "terminal_executed=false",
            "strategy_tester_executed=false",
            "backtest_executed=false",
            "trading_executed=false",
            "future_task_315_requires_gpt_boundary=true",
            "mq5_inventory_files=7",
            "trading_keywords=false",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "repo_mq5_modified=false",
            "mt5_terminal_candidate_found=true",
            "mt5_terminal_candidate_path=",
            "future_no_trade_startup_command_template=",
            "future_startup_command_executed=false",
            "Inventory only; no MT5 run; no trading authorization.",
        )
        for text in required:
            if text not in output:
                return f"complete fixture output missing {text}\n{output}"
    return ""


def test_complete_fixture_passes_without_candidate(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        result, output = run_validator(module, root)
        if result != 0:
            return f"complete fixture without candidate should pass\n{output}"
        if "mt5_terminal_candidate_found=false" not in output:
            return f"missing no-candidate output\n{output}"
        if "future_startup_command_executed=false" not in output:
            return f"missing future command not executed output\n{output}"
    return ""


def test_missing_required_state_fails(module) -> str:
    cases = (
        ("missing TASK-314 doc", TASK312_TEXT, TASK313_TEXT, None),
        ("missing TASK-313 doc", TASK312_TEXT, None, TASK314_TEXT),
        ("missing TASK-312 doc", None, TASK313_TEXT, TASK314_TEXT),
        (
            "missing command-discovery-only",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- command-discovery-only\n", ""),
        ),
        (
            "missing mt5-startup-preparation-only",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- mt5-startup-preparation-only\n", ""),
        ),
        (
            "missing not MT5 run",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- not MT5 run in TASK-314\n", ""),
        ),
        (
            "missing not terminal64 execution",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- not terminal64.exe execution in TASK-314\n", ""),
        ),
        (
            "missing Strategy Tester authorization ban",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- not Strategy Tester authorization\n", ""),
        ),
        (
            "missing trading authorization ban",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- not trading authorization\n", ""),
        ),
        (
            "missing TASK-312 compile-only scope",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- TASK-312 compile_success_scope=compile-only-diagnostic\n", ""),
        ),
        (
            "missing future TASK-315 boundary",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- future TASK-315 must be separately authorized by GPT before any MT5 terminal startup attempt\n", ""),
        ),
        (
            "missing future InpEnableTrading proof",
            TASK312_TEXT,
            TASK313_TEXT,
            TASK314_TEXT.replace("- future startup must prove InpEnableTrading=false before startup\n", ""),
        ),
    )
    for label, task312_text, task313_text, task314_text in cases:
        error = assert_fails_when(
            module,
            task312_text=task312_text,
            task313_text=task313_text,
            task314_text=task314_text,
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
        "/compile",
        "terminal64.exe(",
        "terminal.exe(",
        "MetaEditor.exe(",
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
        test_complete_fixture_passes_with_candidate,
        test_complete_fixture_passes_without_candidate,
        test_missing_required_state_fails,
        test_repo_artifact_inventory_and_keyword_failures,
        test_validator_does_not_call_subprocess_or_mt5,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)
    print("MT5 no-trade startup command discovery validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
