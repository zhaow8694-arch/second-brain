#!/usr/bin/env python3
"""Self-test the MQ5 safety guardrails validator CLI."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT_DIR / "tools" / "validate_mq5_safety_guardrails.py"
PASS_TEXT = "MQ5 safety guardrails validation passed"
FAIL_TEXT = "MQ5 safety guardrails validation failed"
SELF_PASS_TEXT = "MQ5 safety guardrails self-test passed"
SELF_FAIL_TEXT = "MQ5 safety guardrails self-test failed"


BASE_FILES = {
    "mq5/config/InputConfig.mqh": """
        input bool InpEnableTrading = false;
    """,
    "mq5/logger/Logger.mqh": """
        class Logger
        {
        public:
           void Warning(const string module, const string eventName, const string detail) {}
        };
    """,
    "mq5/signals/SignalEngine.mqh": """
        enum SignalDirection
        {
           SIGNAL_NONE = 0,
           SIGNAL_BUY = 1,
           SIGNAL_SELL = -1
        };

        struct SignalResult
        {
           SignalDirection direction;
           string reason;
        };

        class SignalEngine
        {
        public:
           SignalResult Evaluate()
           {
              SignalResult result;
              result.direction = SIGNAL_NONE;
              result.reason = "observation only";
              return result;
           }
        };
    """,
    "mq5/risk/RiskManager.mqh": """
        #include "../config/InputConfig.mqh"
        #include "../signals/SignalEngine.mqh"

        enum RiskRejectCode
        {
           RISK_REJECT_NONE = 0,
           RISK_REJECT_TRADING_DISABLED,
           RISK_REJECT_OBSERVATION_MODE
        };

        class RiskManager
        {
        private:
           void Reject(const RiskRejectCode code, const string reason, const string detail) {}

        public:
           bool CanExecuteSignal(const SignalResult &signal)
           {
              if(!InpEnableTrading)
              {
                 Reject(RISK_REJECT_TRADING_DISABLED, "InpEnableTrading is false", "Trading is disabled by input");
                 return false;
              }

              Reject(RISK_REJECT_OBSERVATION_MODE,
                     "Trading disabled in risk observation mode",
                     "All observation checks passed, real trading remains blocked");
              return false;
           }
        };
    """,
    "mq5/execution/ExecutionManager.mqh": """
        #include "../config/InputConfig.mqh"
        #include "../logger/Logger.mqh"
        #include "../signals/SignalEngine.mqh"

        class ExecutionManager
        {
        private:
           Logger *logger;

        public:
           bool ExecuteSignal(const SignalResult &signal)
           {
              if(!InpEnableTrading)
              {
                 if(logger != NULL)
                 {
                    logger.Warning("EXECUTION", "Execution skipped", "Execution disabled by InpEnableTrading=false");
                 }

                 return false;
              }

              if(logger != NULL)
              {
                 logger.Warning("EXECUTION", "Execution skipped", "Execution disabled no-trade stub");
              }

              return false;
           }
        };
    """,
    "mq5/core/EaController.mqh": """
        #include "../signals/SignalEngine.mqh"
        #include "../risk/RiskManager.mqh"
        #include "../execution/ExecutionManager.mqh"

        class EaController
        {
        private:
           SignalEngine signalEngine;
           RiskManager riskManager;
           ExecutionManager executionManager;

        public:
           void OnTick()
           {
              SignalResult signal = signalEngine.Evaluate();

              if(!riskManager.CanExecuteSignal(signal))
              {
                 return;
              }

              executionManager.ExecuteSignal(signal);
           }
        };
    """,
}


def combined_output(result):
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def run_validator(project_root):
    return subprocess.run(
        [
            sys.executable,
            str(project_root / "tools" / "validate_mq5_safety_guardrails.py"),
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )


def write_file(project_root, relative_path, content):
    path = project_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def write_temp_project(project_root, overrides=None):
    tools_dir = project_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VALIDATOR, tools_dir / "validate_mq5_safety_guardrails.py")

    files = dict(BASE_FILES)
    if overrides:
        files.update(overrides)

    for relative_path, content in files.items():
        write_file(project_root, relative_path, content)


def expect_pass(result, failure_label):
    output = combined_output(result)
    if result.returncode != 0 or PASS_TEXT not in output:
        return [failure_label, output]
    return []


def expect_fail(result, failure_label, required_text=None):
    output = combined_output(result)
    if result.returncode == 0:
        return [failure_label, output]
    if FAIL_TEXT not in output:
        return ["expected validation failed output not found", output]
    if required_text and required_text not in output:
        return [f"expected failure reason not found: {required_text}", output]
    return []


def run_temp_case(overrides, expect_success, failure_label, required_text=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        write_temp_project(project_root, overrides)
        result = run_validator(project_root)
        if expect_success:
            return expect_pass(result, failure_label)
        return expect_fail(result, failure_label, required_text)


def positive_current_project():
    if not VALIDATOR.exists():
        return ["validator script not found", str(VALIDATOR)]
    result = run_validator(ROOT_DIR)
    return expect_pass(result, "positive validation did not pass")


def positive_execution_manager_no_trade_fixture():
    return run_temp_case(
        {},
        True,
        "ExecutionManager no-trade fixture did not pass",
    )


def negative_trading_enabled_true():
    return run_temp_case(
        {
            "mq5/config/InputConfig.mqh": """
                input bool InpEnableTrading = true;
            """,
        },
        False,
        "InpEnableTrading true was not detected",
        "InpEnableTrading default is not false",
    )


def negative_order_send():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": """
                #include "../config/InputConfig.mqh"
                #include "../signals/SignalEngine.mqh"

                class ExecutionManager
                {
                public:
                   bool ExecuteSignal(const SignalResult &signal)
                   {
                      if(!InpEnableTrading)
                      {
                         return false;
                      }

                      OrderSend(request, result);
                      return false;
                   }
                };
            """,
        },
        False,
        "OrderSend was not detected",
        "forbidden API found",
    )


def negative_ctrade_include():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": """
                #include <Trade/Trade.mqh>
                #include "../config/InputConfig.mqh"
                #include "../signals/SignalEngine.mqh"

                CTrade trade;

                class ExecutionManager
                {
                public:
                   bool ExecuteSignal(const SignalResult &signal)
                   {
                      if(!InpEnableTrading)
                      {
                         return false;
                      }

                      return false;
                   }
                };
            """,
        },
        False,
        "CTrade / Trade.mqh was not detected",
        "forbidden API found",
    )


def negative_buy_sell_call():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": """
                #include "../config/InputConfig.mqh"
                #include "../signals/SignalEngine.mqh"

                class ExecutionManager
                {
                public:
                   bool ExecuteSignal(const SignalResult &signal)
                   {
                      if(!InpEnableTrading)
                      {
                         return false;
                      }

                      Buy(1);
                      return false;
                   }
                };
            """,
        },
        False,
        "Buy / Sell was not detected",
        "forbidden API found",
    )


def negative_execution_return_true():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": BASE_FILES["mq5/execution/ExecutionManager.mqh"].replace(
                "return false;", "return true;", 1
            ),
        },
        False,
        "ExecutionManager return true was not detected",
        "no-trade",
    )


def negative_execution_missing_return_false():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": BASE_FILES["mq5/execution/ExecutionManager.mqh"].replace(
                "return false;", "return signal.direction == SIGNAL_NONE;", 1
            ),
        },
        False,
        "ExecutionManager missing return false was not detected",
        "no-trade",
    )


def negative_execution_missing_inp_enable_trading_guard():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": """
                #include "../logger/Logger.mqh"
                #include "../signals/SignalEngine.mqh"

                class ExecutionManager
                {
                private:
                   Logger *logger;

                public:
                   bool ExecuteSignal(const SignalResult &signal)
                   {
                      if(logger != NULL)
                      {
                         logger.Warning("EXECUTION", "Execution skipped", "Execution disabled no-trade stub");
                      }

                      return false;
                   }
                };
            """,
        },
        False,
        "ExecutionManager missing InpEnableTrading disabled guard was not detected",
        "InpEnableTrading disabled guard",
    )


def negative_execution_inp_enable_trading_guard_missing_return_false():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": """
                #include "../config/InputConfig.mqh"
                #include "../logger/Logger.mqh"
                #include "../signals/SignalEngine.mqh"

                class ExecutionManager
                {
                private:
                   Logger *logger;

                public:
                   bool ExecuteSignal(const SignalResult &signal)
                   {
                      if(!InpEnableTrading)
                      {
                         if(logger != NULL)
                         {
                            logger.Warning("EXECUTION", "Execution skipped", "Execution disabled by InpEnableTrading=false");
                         }
                      }

                      if(logger != NULL)
                      {
                         logger.Warning("EXECUTION", "Execution skipped", "Execution disabled no-trade stub");
                      }

                      return false;
                   }
                };
            """,
        },
        False,
        "ExecutionManager InpEnableTrading guard missing return false was not detected",
        "disabled guard",
    )


def negative_missing_risk_gate():
    return run_temp_case(
        {
            "mq5/core/EaController.mqh": """
                #include "../signals/SignalEngine.mqh"
                #include "../execution/ExecutionManager.mqh"

                class EaController
                {
                private:
                   SignalEngine signalEngine;
                   ExecutionManager executionManager;

                public:
                   void OnTick()
                   {
                      SignalResult signal = signalEngine.Evaluate();
                      executionManager.ExecuteSignal(signal);
                   }
                };
            """,
        },
        False,
        "missing RiskManager.CanExecuteSignal risk gate was not detected",
        "risk gate",
    )


def negative_execution_before_risk_gate():
    return run_temp_case(
        {
            "mq5/core/EaController.mqh": """
                #include "../signals/SignalEngine.mqh"
                #include "../risk/RiskManager.mqh"
                #include "../execution/ExecutionManager.mqh"

                class EaController
                {
                private:
                   SignalEngine signalEngine;
                   RiskManager riskManager;
                   ExecutionManager executionManager;

                public:
                   void OnTick()
                   {
                      SignalResult signal = signalEngine.Evaluate();
                      executionManager.ExecuteSignal(signal);
                      riskManager.CanExecuteSignal(signal);
                   }
                };
            """,
        },
        False,
        "ExecutionManager before risk gate was not detected",
        "risk gate",
    )


def negative_risk_missing_trading_disabled_block():
    return run_temp_case(
        {
            "mq5/risk/RiskManager.mqh": """
                #include "../config/InputConfig.mqh"
                #include "../signals/SignalEngine.mqh"

                enum RiskRejectCode
                {
                   RISK_REJECT_NONE = 0,
                   RISK_REJECT_TRADING_DISABLED,
                   RISK_REJECT_OBSERVATION_MODE
                };

                class RiskManager
                {
                private:
                   void Reject(const RiskRejectCode code, const string reason, const string detail) {}

                public:
                   bool CanExecuteSignal(const SignalResult &signal)
                   {
                      Reject(RISK_REJECT_OBSERVATION_MODE,
                             "Trading disabled in risk observation mode",
                             "All observation checks passed, real trading remains blocked");
                      return false;
                   }
                };
            """,
        },
        False,
        "missing InpEnableTrading=false block was not detected",
        "InpEnableTrading",
    )


def negative_risk_missing_observation_mode_fallback():
    return run_temp_case(
        {
            "mq5/risk/RiskManager.mqh": """
                #include "../config/InputConfig.mqh"
                #include "../signals/SignalEngine.mqh"

                enum RiskRejectCode
                {
                   RISK_REJECT_NONE = 0,
                   RISK_REJECT_TRADING_DISABLED,
                   RISK_REJECT_OBSERVATION_MODE
                };

                class RiskManager
                {
                private:
                   void Reject(const RiskRejectCode code, const string reason, const string detail) {}

                public:
                   bool CanExecuteSignal(const SignalResult &signal)
                   {
                      if(!InpEnableTrading)
                      {
                         Reject(RISK_REJECT_TRADING_DISABLED, "InpEnableTrading is false", "Trading is disabled by input");
                         return false;
                      }

                      return false;
                   }
                };
            """,
        },
        False,
        "missing observation mode fallback was not detected",
        "observation mode",
    )


def negative_signal_engine_trading_api():
    return run_temp_case(
        {
            "mq5/signals/SignalEngine.mqh": BASE_FILES["mq5/signals/SignalEngine.mqh"].replace(
                "return result;",
                "OrderSend(request, result);\n              return result;",
                1,
            ),
        },
        False,
        "SignalEngine trading API was not detected",
        "SignalEngine forbidden trading API",
    )


def positive_comment_and_string_false_positive():
    return run_temp_case(
        {
            "mq5/execution/ExecutionManager.mqh": """
                #include "../config/InputConfig.mqh"
                #include "../logger/Logger.mqh"
                #include "../signals/SignalEngine.mqh"

                class ExecutionManager
                {
                private:
                   Logger *logger;

                public:
                   bool ExecuteSignal(const SignalResult &signal)
                   {
                      // OrderSend should be ignored in comments.
                      // CTrade Buy( Sell( should be ignored in comments.
                      string note = "CTrade Buy( Sell( OrderSend should be ignored in strings";
                      if(!InpEnableTrading)
                      {
                         if(logger != NULL)
                         {
                            logger.Warning("EXECUTION", "Execution skipped", "Execution disabled by InpEnableTrading=false");
                         }

                         return false;
                      }

                      if(logger != NULL)
                      {
                         logger.Warning("EXECUTION", "Execution skipped", "Execution disabled no-trade stub");
                      }
                      return false;
                   }
                };
            """,
        },
        True,
        "comment or string false positive detected",
    )


def main():
    failures = []
    tests = [
        positive_current_project,
        positive_execution_manager_no_trade_fixture,
        negative_trading_enabled_true,
        negative_order_send,
        negative_ctrade_include,
        negative_buy_sell_call,
        negative_execution_return_true,
        negative_execution_missing_return_false,
        negative_execution_missing_inp_enable_trading_guard,
        negative_execution_inp_enable_trading_guard_missing_return_false,
        negative_missing_risk_gate,
        negative_execution_before_risk_gate,
        negative_risk_missing_trading_disabled_block,
        negative_risk_missing_observation_mode_fallback,
        negative_signal_engine_trading_api,
        positive_comment_and_string_false_positive,
    ]

    for test in tests:
        result = test()
        if result:
            failures.append(result)

    if failures:
        print(SELF_FAIL_TEXT)
        for failure in failures:
            label = failure[0]
            output = failure[1] if len(failure) > 1 else ""
            print(f"- {label}")
            if output:
                print(output)
        return 1

    print(SELF_PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
