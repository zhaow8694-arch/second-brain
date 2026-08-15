#!/usr/bin/env python3
"""Self-test for TASK-317 MT5 no-trade startup config template validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mt5_no_trade_startup_config_template.py"

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

TASK313_TEXT = """# TASK-313 MT5 terminal no-trade startup boundary packet

- mt5-startup-boundary-only
"""

TASK314_TEXT = """# TASK-314 MT5 no-trade startup command discovery boundary

- command-discovery-only
- future_startup_command_executed=false
"""

TASK315_TEXT = """# TASK-315 MT5 no-trade startup quarantine preparation boundary

- startup-quarantine-preparation-only
"""

TASK316_TEXT = """# TASK-316 MT5 no-trade startup dry-run config boundary

- startup-dryrun-config-boundary-only
"""

TASK317_TEXT = """# TASK-317 MT5 no-trade startup config template preview

- stdout-only-config-template-preview
- no config file generated in TASK-317
- not MT5 run in TASK-317
- not terminal64.exe execution in TASK-317
- not terminal.exe execution in TASK-317
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not trading authorization
- not deployment readiness
- not strategy readiness
- no MT5 terminal run executed in TASK-317
- no terminal64.exe executed in TASK-317
- no terminal.exe executed in TASK-317
- no Strategy Tester executed in TASK-317
- no backtest executed in TASK-317
- no trading executed in TASK-317
- no manifest generated
- no evidence generated
- no report generated
- no startup log generated in repository
- no terminal data directory created in repository
- no no-trade config file generated in repository
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: a5aa4c3 TASK-316 implement MT5 no-trade startup dry-run config boundary
- current tag: v0.5.112-task-316-mt5-no-trade-startup-dryrun-config-boundary
- TASK-314 discovered MT5 terminal candidate
- TASK-315 defined startup quarantine preparation
- TASK-316 defined dry-run config boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5
- TASK-318 must not be entered directly
- future terminal path placeholder
- future quarantine data path placeholder outside repository
- future no-trade config template
- InpEnableTrading=false
- no Strategy Tester
- no backtest
- no trading
- no official manifest
- no evidence
- no report
- stdout-only startup result unless separately authorized
"""


def fail(message: str) -> int:
    print("MT5 no-trade startup config template validator self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mt5_no_trade_startup_config_template",
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
    task313_text: str | None = TASK313_TEXT,
    task314_text: str | None = TASK314_TEXT,
    task315_text: str | None = TASK315_TEXT,
    task316_text: str | None = TASK316_TEXT,
    task317_text: str | None = TASK317_TEXT,
    mq5_overrides=None,
) -> None:
    docs = {
        "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md": task313_text,
        "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md": task314_text,
        "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md": task315_text,
        "V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md": task316_text,
        "V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md": task317_text,
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
    module.TASK313_DOC_PATH = root / "docs" / "V060_TASK_313_MT5_NO_TRADE_STARTUP_BOUNDARY.md"
    module.TASK314_DOC_PATH = (
        root / "docs" / "V060_TASK_314_MT5_NO_TRADE_STARTUP_COMMAND_DISCOVERY.md"
    )
    module.TASK315_DOC_PATH = (
        root / "docs" / "V060_TASK_315_MT5_NO_TRADE_STARTUP_QUARANTINE_PREPARATION.md"
    )
    module.TASK316_DOC_PATH = (
        root / "docs" / "V060_TASK_316_MT5_NO_TRADE_STARTUP_DRYRUN_CONFIG_BOUNDARY.md"
    )
    module.TASK317_DOC_PATH = (
        root / "docs" / "V060_TASK_317_MT5_NO_TRADE_STARTUP_CONFIG_TEMPLATE.md"
    )
    module.MQ5_ROOT = root / "mq5"
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def assert_fails_when(module, *, setup=None, **kwargs) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, **kwargs)
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
            "mt5_no_trade_startup_config_template=true",
            "stdout_only_config_template_preview=true",
            "config_file_generated=false",
            "mt5_terminal_executed=false",
            "terminal64_executed=false",
            "terminal_executed=false",
            "strategy_tester_executed=false",
            "backtest_executed=false",
            "trading_executed=false",
            "future_task_318_requires_gpt_boundary=true",
            "no_trade_config_generated_in_repo=false",
            "repo_terminal_data_directory=false",
            "repo_startup_logs=false",
            "mq5_inventory_files=7",
            "trading_keywords=false",
            "template_InpEnableTrading=false",
            "template_strategy_tester_enabled=false",
            "template_backtest_enabled=false",
            "template_trading_enabled=false",
            "template_evidence_generation=false",
            "template_manifest_generation=false",
            "template_report_generation=false",
            "Inventory only; no MT5 run; no trading authorization.",
        )
        for text in required:
            if text not in output:
                return f"complete fixture output missing {text}\n{output}"
    return ""


def test_missing_required_docs_and_phrases_fail(module) -> str:
    cases = (
        ("missing TASK-317 doc", {"task317_text": None}),
        ("missing TASK-316 doc", {"task316_text": None}),
        ("missing TASK-315 doc", {"task315_text": None}),
        ("missing TASK-314 doc", {"task314_text": None}),
        ("missing TASK-313 doc", {"task313_text": None}),
        (
            "missing stdout-only-config-template-preview",
            {"task317_text": TASK317_TEXT.replace("- stdout-only-config-template-preview\n", "")},
        ),
        (
            "missing no config file generated",
            {"task317_text": TASK317_TEXT.replace("- no config file generated in TASK-317\n", "")},
        ),
        (
            "missing InpEnableTrading=false",
            {"task317_text": TASK317_TEXT.replace("- InpEnableTrading=false\n", "")},
        ),
        (
            "missing future TASK-318 boundary",
            {
                "task317_text": TASK317_TEXT
                .replace("- future TASK-318 must be separately authorized by GPT before writing any startup config file or launching MT5\n", "")
                .replace("- TASK-318 must not be entered directly\n", "")
            },
        ),
    )
    for label, kwargs in cases:
        error = assert_fails_when(module, **kwargs)
        if error:
            return f"{label}: {error}"
    return ""


def test_repo_artifact_inventory_config_and_keyword_failures(module) -> str:
    cases = (
        ("repo .ex5", lambda root: write_text(root / "mq5" / "TradingSystem.ex5", "artifact\n")),
        ("repo compile log", lambda root: write_text(root / "compile.log", "log\n")),
        ("repo terminal data dir", lambda root: (root / "MQL5" / "Profiles").mkdir(parents=True)),
        ("repo startup log", lambda root: write_text(root / "mt5_startup.log", "startup\n")),
        (
            "generated no-trade startup ini",
            lambda root: write_text(root / "terminal_no_trade_startup.ini", "[Common]\n"),
        ),
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


def test_allowed_existing_logs_and_mq5_config_do_not_fail(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "logs" / "localhost-3000.debug.log", "existing dev log\n")
        result, output = run_validator(module, root)
        if result != 0:
            return f"allowed localhost log or mq5/config was misclassified\n{output}"
    return ""


def test_validator_does_not_call_subprocess_or_terminals(module) -> str:
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
        test_repo_artifact_inventory_config_and_keyword_failures,
        test_allowed_existing_logs_and_mq5_config_do_not_fail,
        test_validator_does_not_call_subprocess_or_terminals,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)
    print("MT5 no-trade startup config template validator self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
