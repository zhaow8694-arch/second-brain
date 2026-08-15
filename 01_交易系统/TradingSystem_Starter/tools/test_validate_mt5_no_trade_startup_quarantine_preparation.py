#!/usr/bin/env python3
"""Self-test for TASK-315 MT5 no-trade startup quarantine preparation validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mt5_no_trade_startup_quarantine_preparation.py"

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

- compile_success_scope=compile-only-diagnostic
- trading_authorization=false
"""

TASK313_TEXT = """# TASK-313 MT5 terminal no-trade startup boundary packet

- mt5-startup-boundary-only
"""

TASK314_TEXT = """# TASK-314 MT5 no-trade startup command discovery boundary

- command-discovery-only
- future_startup_command_executed=false
"""

TASK315_TEXT = """# TASK-315 MT5 no-trade startup quarantine preparation boundary

- planning-only
- startup-quarantine-preparation-only
- not MT5 run in TASK-315
- not terminal64.exe execution in TASK-315
- not terminal.exe execution in TASK-315
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-315
- no terminal64.exe executed in TASK-315
- no terminal.exe executed in TASK-315
- no Strategy Tester executed in TASK-315
- no backtest executed in TASK-315
- no trading executed in TASK-315
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: ba2076e TASK-314 implement MT5 no-trade startup command discovery boundary
- current tag: v0.5.110-task-314-mt5-no-trade-startup-command-discovery
- TASK-314 discovered MT5 terminal candidate
- TASK-314 future_startup_command_executed=false
- TASK-312 compile_success=true was compile-only-diagnostic scope only
- TASK-312 compile_success_scope=compile-only-diagnostic
- TASK-312 trading_authorization=false
- TASK-312 deployment_readiness=false
- TASK-312 backtest_readiness=false
- TASK-312 strategy_readiness=false
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-316 must be separately authorized by GPT before any MT5 terminal startup attempt
- TASK-316 must not be entered directly
- future GPT boundary explicitly authorizes MT5 terminal no-trade startup attempt
- future startup must remain no-trade
- future startup must use an isolated startup quarantine outside repository
- future startup must not use repository as terminal data directory
- future startup must not write terminal logs into repository
- future startup must not create evidence / manifest / report unless separately authorized
- future startup must not copy external evidence
- future startup must not run Strategy Tester
- future startup must not run backtest
- future startup must not run simulation trading
- future startup must not run real trading
- future startup must not place orders
- future startup must not attach EA to live trading chart unless separately authorized
- future startup must prove InpEnableTrading=false before startup
- future startup must prove trading keywords false before startup
- future startup must prove MQ5 inventory remains 7 files before startup
- future startup must prove repo_ex5_artifacts=false before startup
- future startup must prove repo_compile_logs=false before startup
- future startup must prove repo_mq5_modified=false before startup
- future startup must prove no terminal data directory exists in repository before startup
- future startup must prove no startup log exists in repository before startup
- future startup must capture startup result stdout-only unless separately authorized
- future startup must clean up quarantine unless separately authorized
- future startup must prove repo_ex5_artifacts=false after startup
- future startup must prove repo_compile_logs=false after startup
- future startup must prove repo_mq5_modified=false after startup
- future startup must prove trading_keywords=false after startup
- future startup must not imply deployment readiness
- future startup must not imply strategy readiness
- future startup must not imply backtest readiness
- future startup must not imply trading authorization
"""


def fail(message: str) -> int:
    print("MT5 no-trade startup quarantine preparation validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mt5_no_trade_startup_quarantine_preparation",
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
    task315_text: str | None = TASK315_TEXT,
    mq5_overrides=None,
) -> None:
    docs = {
        "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md": task312_text,
        "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md": task313_text,
        "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md": task314_text,
        "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md": task315_text,
    }
    for filename, text in docs.items():
        if text is not None:
            write_text(root / "docs" / filename, text)

    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_validator(module, root: Path):
    module.ROOT_DIR = root
    module.TASK312_DOC_PATH = (
        root / "docs" / "V060_TASK_312_MQL5_COMPILE_SUCCESS_RECLASSIFICATION_DECISION.md"
    )
    module.TASK313_DOC_PATH = root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
    module.TASK314_DOC_PATH = (
        root / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
    )
    module.TASK315_DOC_PATH = (
        root / "docs" / "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"
    )
    module.MQ5_ROOT = root / "mq5"
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def assert_fails_when(
    module,
    *,
    task312_text=TASK312_TEXT,
    task313_text=TASK313_TEXT,
    task314_text=TASK314_TEXT,
    task315_text=TASK315_TEXT,
    setup=None,
) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(
            root,
            task312_text=task312_text,
            task313_text=task313_text,
            task314_text=task314_text,
            task315_text=task315_text,
        )
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
            "mt5_no_trade_startup_quarantine_preparation=true",
            "startup_quarantine_preparation_only=true",
            "mt5_terminal_executed=false",
            "terminal64_executed=false",
            "terminal_executed=false",
            "strategy_tester_executed=false",
            "backtest_executed=false",
            "trading_executed=false",
            "future_task_316_requires_gpt_boundary=true",
            "startup_quarantine_outside_repo_required=true",
            "repo_terminal_data_directory=false",
            "repo_startup_logs=false",
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


def test_missing_required_docs_and_phrases_fail(module) -> str:
    cases = (
        ("missing TASK-315 doc", {"task315_text": None}),
        ("missing TASK-314 doc", {"task314_text": None}),
        ("missing TASK-313 doc", {"task313_text": None}),
        ("missing TASK-312 doc", {"task312_text": None}),
        (
            "missing startup-quarantine-preparation-only",
            {"task315_text": TASK315_TEXT.replace("- startup-quarantine-preparation-only\n", "")},
        ),
        (
            "missing not MT5 run",
            {"task315_text": TASK315_TEXT.replace("- not MT5 run in TASK-315\n", "")},
        ),
        (
            "missing no terminal64 executed",
            {"task315_text": TASK315_TEXT.replace("- no terminal64.exe executed in TASK-315\n", "")},
        ),
        (
            "missing no terminal data directory",
            {"task315_text": TASK315_TEXT.replace("- no terminal data directory created in repository\n", "")},
        ),
        (
            "missing no startup log",
            {"task315_text": TASK315_TEXT.replace("- no startup log generated in repository\n", "")},
        ),
        (
            "missing future TASK-316 boundary",
            {
                "task315_text": TASK315_TEXT
                .replace("- future TASK-316 must be separately authorized by GPT before any MT5 terminal startup attempt\n", "")
                .replace("- TASK-316 must not be entered directly\n", "")
            },
        ),
        (
            "missing isolated quarantine requirement",
            {
                "task315_text": TASK315_TEXT.replace(
                    "- future startup must use an isolated startup quarantine outside repository\n",
                    "",
                )
            },
        ),
        (
            "missing InpEnableTrading proof",
            {
                "task315_text": TASK315_TEXT.replace(
                    "- future startup must prove InpEnableTrading=false before startup\n",
                    "",
                )
            },
        ),
    )
    for label, kwargs in cases:
        error = assert_fails_when(module, **kwargs)
        if error:
            return f"{label}: {error}"
    return ""


def test_repo_artifact_inventory_and_keyword_failures(module) -> str:
    cases = (
        ("repo .ex5", lambda root: write_text(root / "mq5" / "TradingSystem.ex5", "artifact\n")),
        ("repo compile log", lambda root: write_text(root / "compile.log", "log\n")),
        ("repo terminal data dir", lambda root: (root / "MQL5" / "Profiles").mkdir(parents=True)),
        ("repo startup log", lambda root: write_text(root / "terminal-startup.log", "startup\n")),
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


def test_allowed_existing_logs_and_mq5_config_do_not_fail(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "logs" / "localhost-3000.debug.log", "existing dev log\n")
        result, output = run_validator(module, root)
        if result != 0:
            return f"allowed localhost log or mq5/config was misclassified\n{output}"
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
        test_complete_fixture_passes,
        test_missing_required_docs_and_phrases_fail,
        test_repo_artifact_inventory_and_keyword_failures,
        test_allowed_existing_logs_and_mq5_config_do_not_fail,
        test_validator_does_not_call_subprocess_or_mt5,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)
    print("MT5 no-trade startup quarantine preparation validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
