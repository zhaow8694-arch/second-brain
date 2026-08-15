#!/usr/bin/env python3
"""Self-test for the MQ5 static symbol/reference consistency validator."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_static_symbol_consistency.py"


EXPECTED_FILES = {
    "TradingSystem.mq5": """#property strict

#include "core/EaController.mqh"

EaController controller;

int OnInit()
{
   return controller.OnInit();
}

void OnTick()
{
   controller.OnTick();
}

void OnDeinit(const int reason)
{
   controller.OnDeinit(reason);
}
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

class EaController
{
private:
   Logger logger;
   SignalEngine signalEngine;
   RiskManager riskManager;
   ExecutionManager executionManager;

   void WriteNoTradeObservability(const string eventName, const string lifecycleName)
   {
      logger.NoTradeObservabilityStatusSnapshot("CORE", eventName, false, true, true, false, "detail");
      logger.NoTradeComponentStatusSnapshot("CORE", eventName, signalEngine.GetSignalStatusSnapshot(), riskManager.GetRiskStatusSnapshot(), executionManager.GetExecutionStatusSnapshot());
      logger.LogNoTradeLifecycleEvent("CORE", eventName, lifecycleName, "detail");
      logger.LogReadOnlyObservabilityConsolidationSnapshot("CORE", eventName, "detail");
      logger.LogReadOnlyObservabilityContractRegistrySnapshot("CORE", eventName, "detail");
      logger.LogReadOnlyObservabilityErrorSnapshot("CORE", eventName, 0, "CORE", "detail", "detail");
      logger.LogReadOnlyTelemetryAggregationSnapshot("CORE", eventName, "detail");
      logger.LogReadOnlyControllerSummarySnapshot("CORE", eventName, "detail");
      logger.LogReadOnlyObservabilityOutputReductionSnapshot("CORE", eventName, "detail");
   }

public:
   int OnInit()
   {
      logger.Init();
      signalEngine.Init(logger);
      riskManager.Init(logger);
      executionManager.Init(logger);
      WriteNoTradeObservability("init", "init");
      return 0;
   }

   void OnTick()
   {
      if(InpObservabilityLogOnTick)
      {
         WriteNoTradeObservability("tick", "tick");
      }
   }

   void OnDeinit(const int reason)
   {
      WriteNoTradeObservability("deinit", "deinit");
   }
};

#endif
""",
    "logger/Logger.mqh": """#ifndef LOGGER_MQH
#define LOGGER_MQH

class Logger
{
public:
   bool Init() { return true; }
   void NoTradeObservabilityStatusSnapshot(const string moduleName, const string eventName, const bool enableTrading, const bool observabilityEnabled, const bool initLogEnabled, const bool tickLogEnabled, const string detail) {}
   void NoTradeComponentStatusSnapshot(const string moduleName, const string eventName, const string signalStatus, const string riskStatus, const string executionStatus) {}
   void LogNoTradeLifecycleEvent(const string moduleName, const string eventName, const string lifecycleName, const string detail) {}
   void LogReadOnlyObservabilityConsolidationSnapshot(const string moduleName, const string eventName, const string detail) {}
   void LogReadOnlyObservabilityContractRegistrySnapshot(const string moduleName, const string eventName, const string detail) {}
   void LogReadOnlyObservabilityErrorSnapshot(const string moduleName, const string eventName, const datetime errorTimestamp, const string componentOrigin, const string errorDetails, const string detail) {}
   void LogReadOnlyTelemetryAggregationSnapshot(const string moduleName, const string eventName, const string detail) {}
   void LogReadOnlyControllerSummarySnapshot(const string moduleName, const string eventName, const string detail) {}
   void LogReadOnlyObservabilityOutputReductionSnapshot(const string moduleName, const string eventName, const string detail) {}
};

#endif
""",
    "signals/SignalEngine.mqh": """#ifndef SIGNAL_ENGINE_MQH
#define SIGNAL_ENGINE_MQH

class SignalEngine
{
public:
   bool Init(Logger &log) { return true; }
   string GetSignalStatusSnapshot() { return "signal_status=read-only framework"; }
};

#endif
""",
    "risk/RiskManager.mqh": """#ifndef RISK_MANAGER_MQH
#define RISK_MANAGER_MQH

class RiskManager
{
public:
   bool Init(Logger &log) { return true; }
   string GetRiskStatusSnapshot() { return "risk_status=read-only framework"; }
};

#endif
""",
    "execution/ExecutionManager.mqh": """#ifndef EXECUTION_MANAGER_MQH
#define EXECUTION_MANAGER_MQH

class ExecutionManager
{
public:
   bool Init(Logger &log) { return true; }
   string GetExecutionStatusSnapshot() { return "execution_status=read-only framework"; }
};

#endif
""",
}


def fail(message: str) -> int:
    print("MQ5 static symbol consistency self-test failed")
    print(message)
    return 1


def write_fixture(root: Path) -> Path:
    mq5_root = root / "mq5"
    for rel_path, text in EXPECTED_FILES.items():
        path = mq5_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return mq5_root


def run_validator(mq5_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--mq5-root",
            str(mq5_root),
        ],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def expect_pass(result: subprocess.CompletedProcess[str], failure_name: str) -> str:
    output = combined_output(result)
    if result.returncode != 0:
        return f"{failure_name}\n{output}"
    required = (
        "MQ5 static symbol consistency validation passed",
        "Inventory only; no MT5 run; no trading authorization.",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "symbol_reference_consistency=true",
        "compile_readiness_static_only=true",
    )
    for text in required:
        if text not in output:
            return f"PASS output missing {text}\n{output}"
    return ""


def expect_fail(result: subprocess.CompletedProcess[str], failure_name: str) -> str:
    if result.returncode == 0:
        return f"{failure_name}\n{combined_output(result)}"
    return ""


def positive_test_complete_fixture_passes() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        return expect_pass(run_validator(mq5_root), "complete fixture did not pass")


def negative_test_missing_mq5_root_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        return expect_fail(
            run_validator(Path(temp_dir) / "missing-mq5"),
            "missing MQ5 root was not detected",
        )


def negative_test_missing_required_file_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        (mq5_root / "logger" / "Logger.mqh").unlink()
        return expect_fail(run_validator(mq5_root), "missing required file was not detected")


def negative_test_extra_source_file_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        (mq5_root / "extra.mqh").write_text("// unexpected\n", encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "extra MQ5/MQH file was not detected")


def negative_test_missing_trading_system_lifecycle_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "TradingSystem.mq5"
        path.write_text(path.read_text(encoding="utf-8").replace("void OnTick()", "void MissingOnTick()"), encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "missing TradingSystem lifecycle was not detected")


def negative_test_trading_system_missing_controller_reference_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "TradingSystem.mq5"
        text = path.read_text(encoding="utf-8").replace("controller.OnTick();", "// no controller route")
        path.write_text(text, encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "missing controller reference was not detected")


def negative_test_controller_missing_lifecycle_handler_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "core" / "EaController.mqh"
        text = path.read_text(encoding="utf-8").replace("void OnDeinit(const int reason)", "void MissingOnDeinit(const int reason)")
        path.write_text(text, encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "missing controller lifecycle handler was not detected")


def negative_test_unknown_logger_helper_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "core" / "EaController.mqh"
        text = path.read_text(encoding="utf-8").replace(
            "logger.LogReadOnlyControllerSummarySnapshot",
            "logger.LogMissingReadOnlyControllerSummarySnapshot",
        )
        path.write_text(text, encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "unknown Logger helper was not detected")


def negative_test_logger_missing_key_helper_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "logger" / "Logger.mqh"
        text = path.read_text(encoding="utf-8").replace(
            "LogReadOnlyTelemetryAggregationSnapshot",
            "LogMissingTelemetryAggregationSnapshot",
        )
        path.write_text(text, encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "missing key Logger helper was not detected")


def negative_test_input_config_missing_trading_disabled_trace_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "config" / "InputConfig.mqh"
        text = path.read_text(encoding="utf-8").replace("input bool InpEnableTrading = false;\n", "")
        path.write_text(text, encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "missing InpEnableTrading trace was not detected")


def negative_test_controller_missing_ontick_gate_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "core" / "EaController.mqh"
        text = path.read_text(encoding="utf-8").replace("if(InpObservabilityLogOnTick)", "if(true)")
        path.write_text(text, encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "missing OnTick observability gate was not detected")


def negative_test_trading_keyword_fails() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_root = write_fixture(Path(temp_dir))
        path = mq5_root / "logger" / "Logger.mqh"
        path.write_text(path.read_text(encoding="utf-8") + "\n// OrderSend\n", encoding="utf-8")
        return expect_fail(run_validator(mq5_root), "trading keyword was not detected")


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    tests = (
        positive_test_complete_fixture_passes,
        negative_test_missing_mq5_root_fails,
        negative_test_missing_required_file_fails,
        negative_test_extra_source_file_fails,
        negative_test_missing_trading_system_lifecycle_fails,
        negative_test_trading_system_missing_controller_reference_fails,
        negative_test_controller_missing_lifecycle_handler_fails,
        negative_test_unknown_logger_helper_fails,
        negative_test_logger_missing_key_helper_fails,
        negative_test_input_config_missing_trading_disabled_trace_fails,
        negative_test_controller_missing_ontick_gate_fails,
        negative_test_trading_keyword_fails,
    )
    for test in tests:
        error = test()
        if error:
            return fail(error)

    print("MQ5 static symbol consistency self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
