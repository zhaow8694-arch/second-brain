#!/usr/bin/env python3
"""Self-test for MQ5 observability helper consistency validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_observability_helper_consistency.py"


EXPECTED_NOTICE = "Inventory only; no MT5 run; no trading authorization."


REQUIRED_HELPERS = (
    "LogReadOnlyObservabilityConsolidationSnapshot",
    "LogReadOnlyObservabilityContractRegistrySnapshot",
    "LogReadOnlyObservabilityErrorSnapshot",
    "LogReadOnlyTelemetryAggregationSnapshot",
    "LogReadOnlyControllerSummarySnapshot",
    "LogReadOnlyObservabilityOutputReductionSnapshot",
)


def fail(message: str) -> int:
    print("MQ5 observability helper consistency self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_mq5_observability_helper_consistency",
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


def logger_text() -> str:
    helpers = "\n".join(f"   void {helper}(){{}}" for helper in REQUIRED_HELPERS)
    return (
        "#ifndef LOGGER_MQH\n#define LOGGER_MQH\n\n"
        "class Logger\n{\npublic:\n"
        "   void NoTradeObservabilityStatusSnapshot(){}\n"
        "   void LogNoTradeLifecycleEvent(){}\n"
        f"{helpers}\n"
        "   string Notice()\n   {\n"
        f'      return "{EXPECTED_NOTICE}";\n'
        "   }\n"
        "};\n\n#endif\n"
    )


def controller_text() -> str:
    calls = "\n".join(f"      logger.{helper}();" for helper in REQUIRED_HELPERS)
    return (
        "#ifndef EA_CONTROLLER_MQH\n#define EA_CONTROLLER_MQH\n\n"
        '#include "../config/InputConfig.mqh"\n'
        '#include "../logger/Logger.mqh"\n\n'
        "class EaController\n{\nprivate:\n"
        "   Logger logger;\n"
        "   void WriteNoTradeObservability(const string eventName, const string lifecycleName)\n"
        "   {\n"
        "      logger.NoTradeObservabilityStatusSnapshot();\n"
        "      logger.LogNoTradeLifecycleEvent();\n"
        f"{calls}\n"
        "   }\n"
        "public:\n"
        "   int OnInit()\n   {\n"
        "      WriteNoTradeObservability(\"No-trade observability init\", \"init\");\n"
        "      return 0;\n   }\n"
        "   void OnTick()\n   {\n"
        "      if(InpObservabilityLogOnTick)\n      {\n"
        "         WriteNoTradeObservability(\"No-trade observability tick\", \"tick\");\n"
        "      }\n"
        "   }\n"
        "   void OnDeinit(const int reason)\n   {\n"
        "      WriteNoTradeObservability(\"No-trade observability deinit\", \"deinit\");\n"
        "   }\n"
        "};\n\n#endif\n"
    )


def base_files() -> dict[str, str]:
    return {
        "TradingSystem.mq5": (
            '#property strict\n#include "core/EaController.mqh"\n\n'
            "EaController controller;\n"
            "int OnInit(){ return controller.OnInit(); }\n"
            "void OnTick(){ controller.OnTick(); }\n"
            "void OnDeinit(const int reason){ controller.OnDeinit(reason); }\n"
        ),
        "config/InputConfig.mqh": (
            "#ifndef INPUT_CONFIG_MQH\n#define INPUT_CONFIG_MQH\n"
            "input bool InpEnableTrading = false;\n"
            "input bool InpObservabilityLogOnTick = false;\n"
            "#endif\n"
        ),
        "core/EaController.mqh": controller_text(),
        "execution/ExecutionManager.mqh": "class ExecutionManager{};\n",
        "logger/Logger.mqh": logger_text(),
        "risk/RiskManager.mqh": "class RiskManager{};\n",
        "signals/SignalEngine.mqh": "class SignalEngine{};\n",
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


def with_temp_fixture(test_func):
    with tempfile.TemporaryDirectory() as temp_dir:
        return test_func(Path(temp_dir))


def assert_pass(module, mq5_root: Path) -> str:
    issues = module.collect_issues(mq5_root)
    if issues:
        return "expected PASS but got issues:\n" + "\n".join(issues)
    return ""


def assert_fail(module, mq5_root: Path, expected_fragment: str) -> str:
    issues = module.collect_issues(mq5_root)
    if not issues:
        return "expected FAIL but validator passed"
    issue_text = "\n".join(issues)
    if expected_fragment not in issue_text:
        return f"expected failure containing {expected_fragment!r}, got:\n{issue_text}"
    return ""


def test_complete_fixture_passes(module) -> str:
    def run(temp_root: Path) -> str:
        return assert_pass(module, write_fixture(temp_root))

    return with_temp_fixture(run)


def test_missing_root_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        issues = module.collect_issues(Path(temp_dir) / "missing-mq5")
    if not issues or "missing mq5 root" not in "\n".join(issues):
        return "missing mq5 root did not fail clearly"
    return ""


def test_missing_logger_fails(module) -> str:
    def run(temp_root: Path) -> str:
        return assert_fail(module, write_fixture(temp_root, {"logger/Logger.mqh": None}), "missing files")

    return with_temp_fixture(run)


def test_missing_controller_fails(module) -> str:
    def run(temp_root: Path) -> str:
        return assert_fail(module, write_fixture(temp_root, {"core/EaController.mqh": None}), "missing files")

    return with_temp_fixture(run)


def test_missing_required_helper_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = logger_text().replace("   void LogReadOnlyTelemetryAggregationSnapshot(){}\n", "")
        return assert_fail(
            module,
            write_fixture(temp_root, {"logger/Logger.mqh": text}),
            "LogReadOnlyTelemetryAggregationSnapshot",
        )

    return with_temp_fixture(run)


def test_unknown_controller_helper_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = controller_text().replace(
            "      logger.LogReadOnlyControllerSummarySnapshot();",
            "      logger.LogReadOnlyUnknownFutureSnapshot();",
        )
        return assert_fail(
            module,
            write_fixture(temp_root, {"core/EaController.mqh": text}),
            "LogReadOnlyUnknownFutureSnapshot",
        )

    return with_temp_fixture(run)


def test_tick_helper_without_gate_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = controller_text().replace("if(InpObservabilityLogOnTick)\n      {\n", "")
        text = text.replace("      }\n   }\n   void OnDeinit", "   }\n   void OnDeinit", 1)
        return assert_fail(module, write_fixture(temp_root, {"core/EaController.mqh": text}), "InpObservabilityLogOnTick")

    return with_temp_fixture(run)


def test_extra_source_file_fails(module) -> str:
    def run(temp_root: Path) -> str:
        return assert_fail(
            module,
            write_fixture(temp_root, {"extra/Unexpected.mqh": "#ifndef X\n#define X\n#endif\n"}),
            "unexpected files",
        )

    return with_temp_fixture(run)


def test_trading_keyword_fails(module) -> str:
    for keyword in ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade"):
        def run(temp_root: Path, keyword=keyword) -> str:
            return assert_fail(
                module,
                write_fixture(temp_root, {"logger/Logger.mqh": logger_text() + f"\n// {keyword}\n"}),
                keyword,
            )

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
        "MQ5 observability helper consistency validation passed",
        EXPECTED_NOTICE,
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "logger_helper_consistency=true",
    )
    for text in required:
        if text not in output:
            return f"validator output missing {text!r}\n{output}"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator not found: {VALIDATOR_PATH}")

    module = load_validator_module()
    tests = [
        test_complete_fixture_passes,
        test_missing_root_fails,
        test_missing_logger_fails,
        test_missing_controller_fails,
        test_missing_required_helper_fails,
        test_unknown_controller_helper_fails,
        test_tick_helper_without_gate_fails,
        test_extra_source_file_fails,
        test_trading_keyword_fails,
        test_pass_output_contains_notice,
    ]

    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQ5 observability helper consistency self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
