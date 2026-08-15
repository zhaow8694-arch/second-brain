#!/usr/bin/env python3
"""Self-test for the MQL5 compile-only command discovery validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_only_command_discovery.py"

TASK294_BOUNDARY_TEXT = """# TASK-DOC-294 future MQL5 compile-only boundary packet

- planning-only / boundary-only
- future MQL5 compile-only candidate
- Inventory only; no MT5 run; no trading authorization.
"""

TASK295_BOUNDARY_TEXT = """# TASK-295 MQL5 compile-only command discovery boundary

- command-discovery-only
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not trading authorization
- no MQL5 compile executed in TASK-295
- no MetaEditor executed in TASK-295
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 2de3d95 TASK-DOC-294 create future MQL5 compile-only boundary packet
- current tag: v0.5.93-task-294-future-mql5-compile-only-boundary
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- future TASK-296 must be separately authorized by GPT before any compile execution
- TASK-296 must not be entered directly
- future compile-only task must remain no-trade
- future compile-only task must not create manifest / evidence / report unless separately authorized
- future compile-only task must quarantine or prevent .ex5 artifact generation before compile execution is allowed
"""

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}


def fail(message: str) -> int:
    print("MQL5 compile-only command discovery self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mql5_compile_only_command_discovery",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_project(root: Path, task295_text: str | None = TASK295_BOUNDARY_TEXT, mq5_overrides=None) -> None:
    write_text(root / "docs" / "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md", TASK294_BOUNDARY_TEXT)
    if task295_text is not None:
        write_text(root / "docs" / "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md", task295_text)

    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_main(module, root: Path, path_exists=None, which=None):
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main(
            [],
            root_dir=root,
            path_exists=path_exists,
            which=which,
        )
    return result, output.getvalue()


def expect_pass(module, root: Path, message: str, path_exists=None, which=None) -> str:
    result, output = run_main(module, root, path_exists=path_exists, which=which)
    if result != 0:
        return f"{message}\n{output}"
    required = (
        "mql5_compile_only_command_discovery=true",
        "command_discovery_only=true",
        "metaeditor_executed=false",
        "mql5_compile_executed=false",
        "mt5_run=false",
        "trading_authorization=false",
        "ex5_artifact_generated=false",
        "compile_log_generated=false",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "future_compile_command_executed=false",
        "Inventory only; no MT5 run; no trading authorization.",
    )
    for text in required:
        if text not in output:
            return f"{message}: missing stdout field {text}\n{output}"
    return ""


def expect_fail(module, root: Path, message: str) -> str:
    result, output = run_main(module, root)
    if result == 0:
        return f"{message}\n{output}"
    if "MQL5 compile-only command discovery validation failed" not in output:
        return f"{message}: failure output missing header\n{output}"
    return ""


def positive_test_complete_fixture_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        return expect_pass(module, root, "complete fixture should pass")


def negative_test_missing_task295_boundary_doc(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=None)
        return expect_fail(module, root, "missing TASK-295 boundary doc should fail")


def negative_test_missing_command_discovery_only(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=TASK295_BOUNDARY_TEXT.replace("- command-discovery-only\n", ""))
        return expect_fail(module, root, "missing command-discovery-only should fail")


def negative_test_missing_no_mql5_compile(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=TASK295_BOUNDARY_TEXT.replace("- no MQL5 compile executed in TASK-295\n", ""))
        return expect_fail(module, root, "missing no MQL5 compile executed should fail")


def negative_test_missing_no_metaeditor(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=TASK295_BOUNDARY_TEXT.replace("- no MetaEditor executed in TASK-295\n", ""))
        return expect_fail(module, root, "missing no MetaEditor executed should fail")


def negative_test_missing_no_ex5(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=TASK295_BOUNDARY_TEXT.replace("- no .ex5 artifact generated\n", ""))
        return expect_fail(module, root, "missing no .ex5 artifact generated should fail")


def negative_test_missing_task296_boundary(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task295_text=TASK295_BOUNDARY_TEXT.replace("- TASK-296 must not be entered directly\n", ""))
        return expect_fail(module, root, "missing TASK-296 boundary should fail")


def negative_test_mq5_inventory_not_seven(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        (root / "mq5" / "logger" / "Logger.mqh").unlink()
        return expect_fail(module, root, "MQ5 inventory other than 7 should fail")


def negative_test_trading_keyword_present(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, mq5_overrides={"core/EaController.mqh": "void Probe(){ OrderSend; }\n"})
        return expect_fail(module, root, "trading keyword should fail")


def positive_test_candidate_found_from_path_exists(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)

        def fake_exists(path):
            return str(path).lower().endswith("metaeditor64.exe")

        result, output = run_main(module, root, path_exists=fake_exists)
        if result != 0:
            return f"candidate found should still pass\n{output}"
        if "metaeditor_candidate_found=true" not in output:
            return f"candidate found output missing\n{output}"
        if "future_compile_command_template=" not in output:
            return f"future compile command template missing\n{output}"
        if "/compile:" not in output:
            return f"future compile command template missing /compile marker\n{output}"
        return ""


def positive_test_candidate_not_found_still_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        result, output = run_main(
            module,
            root,
            path_exists=lambda path: False,
            which=lambda name: None,
        )
        if result != 0:
            return f"candidate not found should pass\n{output}"
        if "metaeditor_candidate_found=false" not in output:
            return f"candidate not found output missing\n{output}"
        return ""


def positive_test_does_not_call_subprocess(module) -> str:
    if hasattr(module, "subprocess"):
        return "validator module must not import subprocess"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    module = load_validator()
    tests = [
        positive_test_complete_fixture_passes,
        negative_test_missing_task295_boundary_doc,
        negative_test_missing_command_discovery_only,
        negative_test_missing_no_mql5_compile,
        negative_test_missing_no_metaeditor,
        negative_test_missing_no_ex5,
        negative_test_missing_task296_boundary,
        negative_test_mq5_inventory_not_seven,
        negative_test_trading_keyword_present,
        positive_test_candidate_found_from_path_exists,
        positive_test_candidate_not_found_still_passes,
        positive_test_does_not_call_subprocess,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQL5 compile-only command discovery self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
