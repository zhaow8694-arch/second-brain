#!/usr/bin/env python3
"""Self-test for the MQ5 static compile-readiness aggregate validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import io
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_static_compile_readiness.py"


EXPECTED_FILES = {
    "TradingSystem.mq5": """#property strict
#include "core/EaController.mqh"
EaController controller;
int OnInit(){ return controller.OnInit(); }
void OnTick(){ controller.OnTick(); }
void OnDeinit(const int reason){ controller.OnDeinit(reason); }
""",
    "config/InputConfig.mqh": """#ifndef INPUT_CONFIG_MQH
#define INPUT_CONFIG_MQH
input bool InpEnableTrading = false;
input bool InpEnableNoTradeObservability = true;
input bool InpObservabilityLogOnTick = false;
#endif
""",
    "core/EaController.mqh": """#ifndef EA_CONTROLLER_MQH
#define EA_CONTROLLER_MQH
#include "../config/InputConfig.mqh"
#include "../logger/Logger.mqh"
#include "../signals/SignalEngine.mqh"
#include "../risk/RiskManager.mqh"
#include "../execution/ExecutionManager.mqh"
class EaController { public: int OnInit(){ return 0; } void OnTick(){} void OnDeinit(const int reason){} };
#endif
""",
    "logger/Logger.mqh": """#ifndef LOGGER_MQH
#define LOGGER_MQH
class Logger {};
#endif
""",
    "signals/SignalEngine.mqh": """#ifndef SIGNAL_ENGINE_MQH
#define SIGNAL_ENGINE_MQH
class SignalEngine {};
#endif
""",
    "risk/RiskManager.mqh": """#ifndef RISK_MANAGER_MQH
#define RISK_MANAGER_MQH
class RiskManager {};
#endif
""",
    "execution/ExecutionManager.mqh": """#ifndef EXECUTION_MANAGER_MQH
#define EXECUTION_MANAGER_MQH
class ExecutionManager {};
#endif
""",
}


def fail(message: str) -> int:
    print("MQ5 static compile-readiness self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_mq5_static_compile_readiness", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_fixture(root: Path) -> Path:
    mq5_root = root / "mq5"
    for rel_path, text in EXPECTED_FILES.items():
        path = mq5_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return mq5_root


def run_main(module, mq5_root: Path, failing_validator: str = "", command_probe=None):
    calls = []

    def fake_runner(command):
        calls.append(tuple(command))
        command_text = " ".join(command).replace("\\", "/")
        if command_probe is not None:
            command_probe(command_text)
        if failing_validator and failing_validator in command_text:
            return subprocess.CompletedProcess(
                list(command),
                1,
                stdout=f"{failing_validator} failed",
                stderr="",
            )
        return subprocess.CompletedProcess(
            list(command),
            0,
            stdout="validator passed",
            stderr="",
        )

    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main(["--mq5-root", str(mq5_root)], runner=fake_runner)
    return result, calls, output.getvalue()


def expect_pass(result: int, output: str, failure_name: str) -> str:
    if result != 0:
        return f"{failure_name}\n{output}"
    required = (
        "MQ5 static compile-readiness aggregate validation passed",
        "Inventory only; no MT5 run; no trading authorization.",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "compile_readiness_static_only=true",
        "mql5_compile_executed=false",
        "mt5_run=false",
        "trading_authorization=false",
        "static_include_consistency=true",
        "lifecycle_route_consistency=true",
        "observability_helper_consistency=true",
        "telemetry_aggregation_consistency=true",
        "static_symbol_consistency=true",
        "static_interface_consistency=true",
        "no_trade_observability_consistency=true",
    )
    for text in required:
        if text not in output:
            return f"PASS output missing {text}\n{output}"
    return ""


def expect_fail(result: int, failure_name: str) -> str:
    if result == 0:
        return failure_name
    return ""


def test_complete_fixture_and_fake_validators_pass(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        result, calls, output = run_main(module, write_fixture(Path(temp_dir)))
        if len(calls) != 7:
            return f"expected 7 aggregate validator calls, got {len(calls)}"
        return expect_pass(result, output, "complete fixture did not pass")


def test_missing_mq5_root_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        result, _calls, _output = run_main(module, Path(temp_dir) / "missing")
        return expect_fail(result, "missing MQ5 root was not detected")


def test_missing_required_file_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        (mq5_root / "logger" / "Logger.mqh").unlink()
        result, _calls, _output = run_main(module, mq5_root)
        return expect_fail(result, "missing required MQ5/MQH file was not detected")


def test_extra_mq5_or_mqh_file_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        (mq5_root / "extra.mq5").write_text("// unexpected\n", encoding="utf-8")
        result, _calls, _output = run_main(module, mq5_root)
        return expect_fail(result, "extra MQ5/MQH file was not detected")


def test_trading_keyword_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "logger" / "Logger.mqh"
        path.write_text(path.read_text(encoding="utf-8") + "\n// CTrade\n", encoding="utf-8")
        result, _calls, _output = run_main(module, mq5_root)
        return expect_fail(result, "trading keyword was not detected")


def test_failing_aggregate_validator_fails_with_name(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        result, _calls, output = run_main(
            module,
            write_fixture(Path(temp_dir)),
            failing_validator="validate_mq5_telemetry_aggregation.py",
        )
        if result == 0:
            return "failing aggregate validator did not fail the overall check"
        if "mq5-telemetry-aggregation" not in output:
            return f"failure output did not name failing validator\n{output}"
        return ""


def test_does_not_call_mt5_or_compile_commands(module) -> str:
    forbidden_fragments = ("mt5", "metaeditor", "mql5", "powershell", ".ps1")

    def probe(command_text: str) -> None:
        lowered = command_text.lower()
        for fragment in forbidden_fragments:
            if fragment in lowered:
                raise AssertionError(f"forbidden command fragment: {fragment}")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            result, _calls, output = run_main(
                module,
                write_fixture(Path(temp_dir)),
                command_probe=probe,
            )
        except AssertionError as exc:
            return str(exc)
        return expect_pass(result, output, "safe command probe did not pass")


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    module = load_validator_module()
    tests = (
        test_complete_fixture_and_fake_validators_pass,
        test_missing_mq5_root_fails,
        test_missing_required_file_fails,
        test_extra_mq5_or_mqh_file_fails,
        test_trading_keyword_fails,
        test_failing_aggregate_validator_fails_with_name,
        test_does_not_call_mt5_or_compile_commands,
    )
    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQ5 static compile-readiness self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
