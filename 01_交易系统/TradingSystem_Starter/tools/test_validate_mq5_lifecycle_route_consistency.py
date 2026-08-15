#!/usr/bin/env python3
"""Self-test for MQ5 lifecycle route consistency validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_lifecycle_route_consistency.py"


def fail(message: str) -> int:
    print("MQ5 lifecycle route consistency self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_mq5_lifecycle_route_consistency",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def base_files() -> dict[str, str]:
    return {
        "TradingSystem.mq5": (
            '#property strict\n\n'
            '#include "core/EaController.mqh"\n\n'
            "EaController controller;\n\n"
            "int OnInit()\n{\n   return controller.OnInit();\n}\n\n"
            "void OnTick()\n{\n   controller.OnTick();\n}\n\n"
            "void OnDeinit(const int reason)\n{\n   controller.OnDeinit(reason);\n}\n"
        ),
        "config/InputConfig.mqh": (
            "#ifndef INPUT_CONFIG_MQH\n#define INPUT_CONFIG_MQH\n\n"
            "input bool InpEnableTrading = false;\n"
            "input bool InpEnableNoTradeObservability = true;\n"
            "input bool InpObservabilityLogOnInit = true;\n"
            "input bool InpObservabilityLogOnTick = false;\n\n"
            "#endif\n"
        ),
        "core/EaController.mqh": (
            "#ifndef EA_CONTROLLER_MQH\n#define EA_CONTROLLER_MQH\n\n"
            '#include "../config/InputConfig.mqh"\n'
            '#include "../logger/Logger.mqh"\n'
            '#include "../signals/SignalEngine.mqh"\n'
            '#include "../risk/RiskManager.mqh"\n'
            '#include "../execution/ExecutionManager.mqh"\n\n'
            "class EaController\n{\nprivate:\n"
            "   Logger logger;\n"
            "   SignalEngine signalEngine;\n"
            "   RiskManager riskManager;\n"
            "   ExecutionManager executionManager;\n"
            "   void WriteNoTradeObservability(const string eventName, const string lifecycleName)\n"
            "   {\n"
            "      logger.NoTradeObservabilityStatusSnapshot(\"CORE\", eventName, false, true, true, false, \"observability_only=true\");\n"
            "      logger.LogReadOnlyControllerSummarySnapshot(\"CORE\", eventName, \"observability_only=true\");\n"
            "   }\n"
            "   void WriteReadOnlyControllerSummarySnapshot(const string eventName)\n"
            "   {\n"
            "      logger.LogReadOnlyControllerSummarySnapshot(\"CORE\", eventName, \"observability_only=true\");\n"
            "   }\n"
            "public:\n"
            "   int OnInit()\n   {\n"
            "      logger.Init();\n"
            "      if(InpObservabilityLogOnInit)\n      {\n"
            "         WriteNoTradeObservability(\"No-trade observability init\", \"init\");\n"
            "      }\n"
            "      signalEngine.Init(logger);\n"
            "      riskManager.Init(logger);\n"
            "      executionManager.Init(logger);\n"
            "      return 0;\n   }\n"
            "   void OnTick()\n   {\n"
            "      if(InpObservabilityLogOnTick)\n      {\n"
            "         WriteNoTradeObservability(\"No-trade observability tick\", \"tick\");\n"
            "      }\n"
            "   }\n"
            "   void OnDeinit(const int reason)\n   {\n"
            "      logger.LogNoTradeLifecycleEvent(\"CORE\", \"No-trade observability deinit\", \"deinit\", \"reason\");\n"
            "      WriteNoTradeObservability(\"No-trade observability deinit\", \"deinit\");\n"
            "      WriteReadOnlyControllerSummarySnapshot(\"No-trade observability deinit\");\n"
            "   }\n"
            "};\n\n#endif\n"
        ),
        "execution/ExecutionManager.mqh": (
            "#ifndef EXECUTION_MANAGER_MQH\n#define EXECUTION_MANAGER_MQH\n\n"
            '#include "../config/InputConfig.mqh"\n'
            '#include "../logger/Logger.mqh"\n'
            '#include "../signals/SignalEngine.mqh"\n\n'
            "class ExecutionManager\n{\npublic:\n"
            "   bool Init(Logger &log)\n   {\n      return true;\n   }\n"
            "};\n\n#endif\n"
        ),
        "logger/Logger.mqh": (
            "#ifndef LOGGER_MQH\n#define LOGGER_MQH\n\n"
            '#include "../config/InputConfig.mqh"\n\n'
            "class Logger\n{\npublic:\n"
            "   bool Init()\n   {\n      return true;\n   }\n"
            "   void NoTradeObservabilityStatusSnapshot(){}\n"
            "   void LogNoTradeLifecycleEvent(){}\n"
            "   void LogReadOnlyControllerSummarySnapshot(){}\n"
            "   string Notice()\n   {\n"
            '      return "Inventory only; no MT5 run; no trading authorization.";\n'
            "   }\n"
            "};\n\n#endif\n"
        ),
        "risk/RiskManager.mqh": (
            "#ifndef RISK_MANAGER_MQH\n#define RISK_MANAGER_MQH\n\n"
            '#include "../config/InputConfig.mqh"\n'
            '#include "../logger/Logger.mqh"\n'
            '#include "../signals/SignalEngine.mqh"\n\n'
            "class RiskManager\n{\npublic:\n"
            "   bool Init(Logger &log)\n   {\n      return true;\n   }\n"
            "};\n\n#endif\n"
        ),
        "signals/SignalEngine.mqh": (
            "#ifndef SIGNAL_ENGINE_MQH\n#define SIGNAL_ENGINE_MQH\n\n"
            '#include "../logger/Logger.mqh"\n\n'
            "class SignalEngine\n{\npublic:\n"
            "   bool Init(Logger &log)\n   {\n      return true;\n   }\n"
            "};\n\n#endif\n"
        ),
    }


def write_fixture(root: Path, overrides: dict[str, str | None] | None = None) -> Path:
    mq5_root = root / "mq5"
    files = base_files()
    for rel_path, content in (overrides or {}).items():
        if content is None:
            files.pop(rel_path, None)
        else:
            files[rel_path] = content

    for rel_path, content in files.items():
        write_text(mq5_root / rel_path, content)
    return mq5_root


def run_validator(module, mq5_root: Path) -> list[str]:
    return module.collect_issues(mq5_root)


def assert_pass(module, mq5_root: Path) -> str:
    issues = run_validator(module, mq5_root)
    if issues:
        return "expected PASS but got issues:\n" + "\n".join(issues)
    return ""


def assert_fail(module, mq5_root: Path, expected_fragment: str) -> str:
    issues = run_validator(module, mq5_root)
    if not issues:
        return "expected FAIL but validator passed"
    issue_text = "\n".join(issues)
    if expected_fragment not in issue_text:
        return f"expected failure containing {expected_fragment!r}, got:\n{issue_text}"
    return ""


def with_temp_fixture(test_func):
    with tempfile.TemporaryDirectory() as temp_dir:
        return test_func(Path(temp_dir))


def test_complete_fixture_passes(module) -> str:
    def run(temp_root: Path) -> str:
        mq5_root = write_fixture(temp_root)
        return assert_pass(module, mq5_root)

    return with_temp_fixture(run)


def test_missing_root_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        issues = module.collect_issues(Path(temp_dir) / "missing-mq5")
    if not issues:
        return "missing mq5 root did not fail"
    if "missing mq5 root" not in "\n".join(issues):
        return "missing mq5 root failure text was not clear"
    return ""


def test_missing_trading_system_fails(module) -> str:
    def run(temp_root: Path) -> str:
        mq5_root = write_fixture(temp_root, {"TradingSystem.mq5": None})
        return assert_fail(module, mq5_root, "missing files")

    return with_temp_fixture(run)


def test_missing_ea_controller_fails(module) -> str:
    def run(temp_root: Path) -> str:
        mq5_root = write_fixture(temp_root, {"core/EaController.mqh": None})
        return assert_fail(module, mq5_root, "missing files")

    return with_temp_fixture(run)


def test_missing_lifecycle_entries_fail(module) -> str:
    replacements = (
        ("int OnInit()\n{\n   return controller.OnInit();\n}\n\n", "int OnInit()"),
        ("void OnTick()\n{\n   controller.OnTick();\n}\n\n", "void OnTick()"),
        ("void OnDeinit(const int reason)\n{\n   controller.OnDeinit(reason);\n}\n", "void OnDeinit"),
    )
    for removed_text, expected in replacements:
        def run(temp_root: Path, removed_text=removed_text, expected=expected) -> str:
            text = base_files()["TradingSystem.mq5"].replace(removed_text, "")
            mq5_root = write_fixture(temp_root, {"TradingSystem.mq5": text})
            return assert_fail(module, mq5_root, expected)

        error = with_temp_fixture(run)
        if error:
            return error
    return ""


def test_trading_system_unrouted_lifecycle_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = base_files()["TradingSystem.mq5"].replace("controller.OnTick();", "")
        mq5_root = write_fixture(temp_root, {"TradingSystem.mq5": text})
        return assert_fail(module, mq5_root, "controller.OnTick()")

    return with_temp_fixture(run)


def test_controller_missing_lifecycle_handler_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = base_files()["core/EaController.mqh"].replace("void OnTick()\n   {\n", "void OnTimer()\n   {\n")
        mq5_root = write_fixture(temp_root, {"core/EaController.mqh": text})
        return assert_fail(module, mq5_root, "EaController missing lifecycle handler")

    return with_temp_fixture(run)


def test_controller_tick_missing_gate_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = base_files()["core/EaController.mqh"].replace("InpObservabilityLogOnTick", "InpObservabilityTickDisabled")
        mq5_root = write_fixture(temp_root, {"core/EaController.mqh": text})
        return assert_fail(module, mq5_root, "InpObservabilityLogOnTick")

    return with_temp_fixture(run)


def test_extra_source_file_fails(module) -> str:
    def run(temp_root: Path) -> str:
        mq5_root = write_fixture(temp_root, {"extra/Unexpected.mqh": "#ifndef X\n#define X\n#endif\n"})
        return assert_fail(module, mq5_root, "unexpected files")

    return with_temp_fixture(run)


def test_trading_keyword_fails(module) -> str:
    for keyword in ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade"):
        def run(temp_root: Path, keyword=keyword) -> str:
            text = base_files()["logger/Logger.mqh"] + f"\n// {keyword}\n"
            mq5_root = write_fixture(temp_root, {"logger/Logger.mqh": text})
            return assert_fail(module, mq5_root, keyword)

        error = with_temp_fixture(run)
        if error:
            return error
    return ""


def test_pass_output_contains_notice(module) -> str:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    required = (
        "MQ5 lifecycle route consistency validation passed",
        "Inventory only; no MT5 run; no trading authorization.",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "lifecycle_routes=OnInit,OnTick,OnDeinit",
    )
    for text in required:
        if text not in output and text not in VALIDATOR_PATH.read_text(encoding="utf-8"):
            return f"validator output missing {text!r}\n{output}"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator not found: {VALIDATOR_PATH}")

    module = load_validator_module()
    tests = [
        test_complete_fixture_passes,
        test_missing_root_fails,
        test_missing_trading_system_fails,
        test_missing_ea_controller_fails,
        test_missing_lifecycle_entries_fail,
        test_trading_system_unrouted_lifecycle_fails,
        test_controller_missing_lifecycle_handler_fails,
        test_controller_tick_missing_gate_fails,
        test_extra_source_file_fails,
        test_trading_keyword_fails,
        test_pass_output_contains_notice,
    ]

    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQ5 lifecycle route consistency self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
