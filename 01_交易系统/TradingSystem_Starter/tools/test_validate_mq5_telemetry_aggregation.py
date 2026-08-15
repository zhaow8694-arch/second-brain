#!/usr/bin/env python3
"""Self-test for MQ5 read-only telemetry aggregation validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_telemetry_aggregation.py"
NOTICE = "Inventory only; no MT5 run; no trading authorization."


def fail(message: str) -> int:
    print("MQ5 telemetry aggregation self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_mq5_telemetry_aggregation",
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
    return (
        "#ifndef LOGGER_MQH\n#define LOGGER_MQH\n\n"
        "class Logger\n{\npublic:\n"
        "   void LogNoTradePerformanceMetrics(){ string line = \"runtime_metrics_snapshot=true | all_components_no_trade=true | trading_authorization=false | mt5_run_required=false\"; }\n"
        "   void LogReadOnlyMetricsAggregation(){ string line = \"metrics_aggregation_snapshot=true | historical_events_count=0 | last_n_ticks_metrics=none | aggregated_component_status=ready | no_trade_guard=active | trading_authorization=false | mt5_run_required=false | evidence_generation=false | manifest_generation=false\"; }\n"
        "   void LogReadOnlySystemHealth(){ string line = \"system_health_snapshot=true | observability_enabled=true | last_snapshot_timestamp=none | aggregated_component_status=ready | all_components_no_trade=true | trading_authorization=false | mt5_run_required=false | evidence_generation=false | manifest_generation=false\"; }\n"
        "   void LogReadOnlyPipelineContextAggregationSnapshot(){ string line = \"pipeline_context_snapshot=true | all_pipeline_layers_no_trade=true | no_trade_guard=active | trading_authorization=false | mt5_run_required=false\"; }\n"
        "   void LogReadOnlyObservabilityErrorSnapshot(){ string line = \"error_snapshot=true | error_type=read-only framework | all_observability_outputs_read_only=true | all_authorizations_false=true | no_trade_guard=active | trading_authorization=false | mt5_run_required=false | evidence_generation=false | manifest_generation=false\"; }\n"
        "   void LogReadOnlyTelemetryAggregationSnapshot(){ string line = \"telemetry_aggregation_snapshot=true | performance_metrics_linked=true | aggregated_errors_linked=true | aggregated_metrics_linked=true | all_observability_outputs_read_only=true | all_authorizations_false=true | no_trade_guard=active | trading_authorization=false | mt5_run_required=false | evidence_generation=false | manifest_generation=false\"; }\n"
        "   void LogReadOnlyControllerSummarySnapshot(){ string line = \"controller_summary_snapshot=true | init_path_linked=true | tick_path_linked=true | deinit_path_linked=true | all_observability_outputs_read_only=true | all_authorizations_false=true | no_trade_guard=active | trading_authorization=false | mt5_run_required=false | evidence_generation=false | manifest_generation=false\"; }\n"
        f"   string Notice(){{ return \"{NOTICE}\"; }}\n"
        "};\n\n#endif\n"
    )


def controller_text() -> str:
    return (
        "#ifndef EA_CONTROLLER_MQH\n#define EA_CONTROLLER_MQH\n\n"
        '#include "../config/InputConfig.mqh"\n'
        '#include "../logger/Logger.mqh"\n\n'
        "class EaController\n{\nprivate:\n"
        "   Logger logger;\n"
        "   void WriteNoTradeObservability(const string eventName, const string lifecycleName)\n"
        "   {\n"
        "      WriteNoTradePerformanceMetrics(eventName);\n"
        "      WriteReadOnlyMetricsAggregation(eventName);\n"
        "      WriteReadOnlySystemHealth(eventName);\n"
        "      WriteReadOnlyPipelineContextAggregationSnapshot(eventName);\n"
        "      WriteReadOnlyObservabilityErrorSnapshot(eventName);\n"
        "      WriteReadOnlyTelemetryAggregationSnapshot(eventName);\n"
        "      WriteReadOnlyControllerSummarySnapshot(eventName);\n"
        "   }\n"
        "   void WriteNoTradePerformanceMetrics(const string eventName){ logger.LogNoTradePerformanceMetrics(); }\n"
        "   void WriteReadOnlyMetricsAggregation(const string eventName){ logger.LogReadOnlyMetricsAggregation(); }\n"
        "   void WriteReadOnlySystemHealth(const string eventName){ logger.LogReadOnlySystemHealth(); }\n"
        "   void WriteReadOnlyPipelineContextAggregationSnapshot(const string eventName){ logger.LogReadOnlyPipelineContextAggregationSnapshot(); }\n"
        "   void WriteReadOnlyObservabilityErrorSnapshot(const string eventName){ logger.LogReadOnlyObservabilityErrorSnapshot(); }\n"
        "   void WriteReadOnlyTelemetryAggregationSnapshot(const string eventName){ logger.LogReadOnlyTelemetryAggregationSnapshot(); }\n"
        "   void WriteReadOnlyControllerSummarySnapshot(const string eventName){ logger.LogReadOnlyControllerSummarySnapshot(); }\n"
        "public:\n"
        "   int OnInit(){ WriteNoTradeObservability(\"No-trade observability init\", \"init\"); return 0; }\n"
        "   void OnTick(){ if(InpObservabilityLogOnTick){ WriteNoTradeObservability(\"No-trade observability tick\", \"tick\"); } }\n"
        "   void OnDeinit(const int reason){ WriteNoTradeObservability(\"No-trade observability deinit\", \"deinit\"); }\n"
        "};\n\n#endif\n"
    )


def base_files() -> dict[str, str]:
    return {
        "TradingSystem.mq5": (
            '#property strict\n#include "core/EaController.mqh"\n'
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


def test_stdout_summary_contains_required_fields(module) -> str:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    required = (
        "fast_no_trade_telemetry_aggregation=true",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "all_observability_outputs_read_only=true",
        "no_trade_guard=active",
        "mt5_run_required=false",
        "trading_authorization=false",
        NOTICE,
    )
    for text in required:
        if text not in output:
            return f"validator output missing {text!r}\n{output}"
    return ""


def test_missing_telemetry_field_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = logger_text().replace("telemetry_aggregation_snapshot=true", "")
        return assert_fail(
            module,
            write_fixture(temp_root, {"logger/Logger.mqh": text}),
            "telemetry_aggregation_snapshot=true",
        )

    return with_temp_fixture(run)


def test_missing_helper_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = logger_text().replace("   void LogReadOnlyTelemetryAggregationSnapshot(){ string line = \"", "   void MissingTelemetryAggregationSnapshot(){ string line = \"")
        return assert_fail(
            module,
            write_fixture(temp_root, {"logger/Logger.mqh": text}),
            "LogReadOnlyTelemetryAggregationSnapshot",
        )

    return with_temp_fixture(run)


def test_duplicate_helper_call_fails(module) -> str:
    def run(temp_root: Path) -> str:
        text = controller_text().replace(
            "      WriteReadOnlyTelemetryAggregationSnapshot(eventName);\n",
            "      WriteReadOnlyTelemetryAggregationSnapshot(eventName);\n      WriteReadOnlyTelemetryAggregationSnapshot(eventName);\n",
        )
        return assert_fail(
            module,
            write_fixture(temp_root, {"core/EaController.mqh": text}),
            "duplicate telemetry helper call",
        )

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


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator not found: {VALIDATOR_PATH}")

    module = load_validator_module()
    tests = [
        test_complete_fixture_passes,
        test_stdout_summary_contains_required_fields,
        test_missing_telemetry_field_fails,
        test_missing_helper_fails,
        test_duplicate_helper_call_fails,
        test_extra_source_file_fails,
        test_trading_keyword_fails,
    ]

    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQ5 telemetry aggregation self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
