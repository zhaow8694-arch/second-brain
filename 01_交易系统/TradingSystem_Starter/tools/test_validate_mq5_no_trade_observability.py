#!/usr/bin/env python3
"""Self-test for the MQ5 no-trade observability contract validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mq5_no_trade_observability.py"

INPUT_CONFIG_TEXT = """#ifndef INPUT_CONFIG_MQH
#define INPUT_CONFIG_MQH

input bool InpEnableTrading = false;
input bool InpEnableNoTradeObservability = true;
input bool InpObservabilityLogOnInit = true;
input bool InpObservabilityLogOnTick = false;

#endif
"""

LOGGER_TEXT = """#ifndef LOGGER_MQH
#define LOGGER_MQH

class Logger
{
public:
   void NoTradeObservability(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "no-trade observability scaffold | Inventory only; no MT5 run; no trading authorization. | " + detail);
   }

   void NoTradeObservabilityStatusSnapshot(const string moduleName,
                                           const string eventName,
                                           const bool enableTrading,
                                           const bool observabilityEnabled,
                                           const bool initLogEnabled,
                                           const bool tickLogEnabled,
                                           const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "mode=no-trade observability scaffold"
            + " | inventory_notice=Inventory only; no MT5 run; no trading authorization."
            + " | enable_trading=" + BoolToText(enableTrading)
            + " | observability_enabled=" + BoolToText(observabilityEnabled)
            + " | init_log_enabled=" + BoolToText(initLogEnabled)
            + " | tick_log_enabled=" + BoolToText(tickLogEnabled)
            + " | instruction_state=no active trading instructions"
            + " | " + detail);
   }

   void NoTradeComponentStatusSnapshot(const string moduleName,
                                       const string eventName,
                                       const string signalStatus,
                                       const string riskStatus,
                                       const string executionStatus)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "component_status_snapshot=true"
            + " | controller_status=ready"
            + " | logger_status=ready"
            + " | " + signalStatus
            + " | " + riskStatus
            + " | " + executionStatus
            + " | all_components_no_trade=true"
            + " | Inventory only; no MT5 run; no trading authorization.");
   }

   string BuildLifecycleEventField(const string lifecycleName)
   {
      if(lifecycleName == "init")
      {
         return "lifecycle_event=init";
      }

      if(lifecycleName == "tick")
      {
         return "lifecycle_event=tick";
      }

      if(lifecycleName == "deinit")
      {
         return "lifecycle_event=deinit";
      }

      return "lifecycle_event=unknown";
   }

   void LogNoTradeLifecycleEvent(const string moduleName,
                                 const string eventName,
                                 const string lifecycleName,
                                 const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "no-trade observability scaffold"
            + " | " + BuildLifecycleEventField(lifecycleName)
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyRuntimeStatusSnapshot(const string moduleName,
                                         const string eventName,
                                         const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "runtime_status_snapshot=true"
            + " | controller_status=ready"
            + " | logger_status=ready"
            + " | signal_status=read-only framework"
            + " | risk_status=read-only framework"
            + " | execution_status=read-only framework"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogNoTradePerformanceMetrics(const string moduleName,
                                     const string eventName,
                                     const long tickCount,
                                     const long onInitCallCount,
                                     const long onDeinitCallCount,
                                     const datetime lastTickTimestamp,
                                     const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "runtime_metrics_snapshot=true"
            + " | tick_count=" + IntegerToString(tickCount)
            + " | oninit_call_count=" + IntegerToString(onInitCallCount)
            + " | ondeinit_call_count=" + IntegerToString(onDeinitCallCount)
            + " | last_tick_timestamp=" + TimeValueToText(lastTickTimestamp)
            + " | all_components_no_trade=true"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogNoTradeSafetyGuardInvariants(const string moduleName,
                                        const string eventName,
                                        const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "safety_guard_snapshot=true"
            + " | no_trade_guard=active"
            + " | invariant_trading_disabled=true"
            + " | invariant_execution_disabled=true"
            + " | invariant_order_submission_disabled=true"
            + " | invariant_position_management_disabled=true"
            + " | invariant_external_evidence_disabled=true"
            + " | invariant_manifest_generation_disabled=true"
            + " | invariant_mt5_run_required=false"
            + " | invariant_all_components_no_trade=true"
            + " | trading_authorization=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyMetricsAggregation(const string moduleName,
                                      const string eventName,
                                      const long historicalEventsCount,
                                      const string lastNTicksMetrics,
                                      const string aggregatedComponentStatus,
                                      const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "metrics_aggregation_snapshot=true"
            + " | historical_events_count=" + IntegerToString(historicalEventsCount)
            + " | last_n_ticks_metrics=" + lastNTicksMetrics
            + " | aggregated_component_status=" + aggregatedComponentStatus
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlySystemHealth(const string moduleName,
                                const string eventName,
                                const bool observabilityEnabled,
                                const datetime lastSnapshotTimestamp,
                                const string aggregatedComponentStatus,
                                const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "system_health_snapshot=true"
            + " | observability_enabled=" + BoolToText(observabilityEnabled)
            + " | last_snapshot_timestamp=" + TimeValueToText(lastSnapshotTimestamp)
            + " | aggregated_component_status=" + aggregatedComponentStatus
            + " | all_components_no_trade=true"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlySignalContextSnapshot(const string moduleName,
                                         const string eventName,
                                         const string signalContextSnapshot,
                                         const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            signalContextSnapshot
            + " | trading_authorization=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyRiskContextSnapshot(const string moduleName,
                                       const string eventName,
                                       const string riskContextSnapshot,
                                       const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            riskContextSnapshot
            + " | trading_authorization=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyExecutionContextSnapshot(const string moduleName,
                                            const string eventName,
                                            const string executionContextSnapshot,
                                            const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            executionContextSnapshot
            + " | trading_authorization=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyPipelineContextAggregationSnapshot(const string moduleName,
                                                      const string eventName,
                                                      const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "pipeline_context_snapshot=true"
            + " | pipeline_layer_mode=read-only framework"
            + " | signal_context_linked=true"
            + " | risk_context_linked=true"
            + " | execution_context_linked=true"
            + " | pipeline_authorization=false"
            + " | pipeline_direction_authorized=false"
            + " | pipeline_risk_authorized=false"
            + " | pipeline_execution_authorized=false"
            + " | pipeline_dispatch_authorized=false"
            + " | pipeline_intent=false"
            + " | all_pipeline_layers_no_trade=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyAuthorizationMatrixSnapshot(const string moduleName,
                                               const string eventName,
                                               const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "authorization_matrix_snapshot=true"
            + " | authorization_matrix_mode=read-only framework"
            + " | signal_authorization=false"
            + " | signal_direction_authorized=false"
            + " | risk_authorization=false"
            + " | risk_sizing_authorized=false"
            + " | risk_exposure_authorized=false"
            + " | execution_authorization=false"
            + " | execution_request_authorized=false"
            + " | execution_dispatch_authorized=false"
            + " | pipeline_authorization=false"
            + " | pipeline_intent=false"
            + " | trading_authorization=false"
            + " | all_authorizations_false=true"
            + " | all_pipeline_layers_no_trade=true"
            + " | no_trade_guard=active"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyDecisionGateSnapshot(const string moduleName,
                                        const string eventName,
                                        const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "decision_gate_snapshot=true"
            + " | decision_gate_mode=read-only framework"
            + " | decision_state=blocked_no_trade"
            + " | decision_candidate_available=false"
            + " | decision_direction_authorized=false"
            + " | decision_risk_authorized=false"
            + " | decision_execution_authorized=false"
            + " | decision_dispatch_authorized=false"
            + " | decision_output_authorized=false"
            + " | decision_intent=false"
            + " | all_authorizations_false=true"
            + " | all_pipeline_layers_no_trade=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyDecisionRejectionReasonSnapshot(const string moduleName,
                                                   const string eventName,
                                                   const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "decision_rejection_snapshot=true"
            + " | decision_rejection_mode=read-only framework"
            + " | rejection_reason=no_trade_guard_active"
            + " | rejection_trading_authorization=false"
            + " | rejection_signal_authorization=false"
            + " | rejection_risk_authorization=false"
            + " | rejection_execution_authorization=false"
            + " | rejection_pipeline_authorization=false"
            + " | rejection_external_evidence=false"
            + " | rejection_manifest_generation=false"
            + " | rejection_mt5_run_required=false"
            + " | decision_state=blocked_no_trade"
            + " | decision_intent=false"
            + " | all_authorizations_false=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyObservabilityConsolidationSnapshot(const string moduleName,
                                                      const string eventName,
                                                      const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "observability_consolidation_snapshot=true"
            + " | observability_consolidation_mode=read-only framework"
            + " | observability_contract_version=v0.6.0-no-trade"
            + " | structured_snapshot_linked=true"
            + " | component_status_linked=true"
            + " | lifecycle_telemetry_linked=true"
            + " | runtime_status_linked=true"
            + " | performance_metrics_linked=true"
            + " | safety_guard_linked=true"
            + " | signal_context_linked=true"
            + " | risk_context_linked=true"
            + " | execution_context_linked=true"
            + " | pipeline_context_linked=true"
            + " | authorization_matrix_linked=true"
            + " | decision_gate_linked=true"
            + " | decision_rejection_linked=true"
            + " | all_observability_outputs_read_only=true"
            + " | all_authorizations_false=true"
            + " | all_pipeline_layers_no_trade=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyObservabilityContractRegistrySnapshot(const string moduleName,
                                                         const string eventName,
                                                         const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "observability_contract_registry_snapshot=true"
            + " | observability_contract_registry_mode=read-only framework"
            + " | observability_contract_registry_version=v0.6.0-no-trade"
            + " | registered_contract_count=16"
            + " | registered_contracts_read_only=true"
            + " | registered_contracts_no_trade=true"
            + " | structured_snapshot_registered=true"
            + " | component_status_registered=true"
            + " | lifecycle_telemetry_registered=true"
            + " | runtime_status_registered=true"
            + " | performance_metrics_registered=true"
            + " | safety_guard_registered=true"
            + " | metrics_aggregation_registered=true"
            + " | system_health_registered=true"
            + " | signal_context_registered=true"
            + " | risk_context_registered=true"
            + " | execution_context_registered=true"
            + " | pipeline_context_registered=true"
            + " | authorization_matrix_registered=true"
            + " | decision_gate_registered=true"
            + " | decision_rejection_registered=true"
            + " | observability_consolidation_registered=true"
            + " | all_registered_contracts_static=true"
            + " | all_registered_contracts_read_only=true"
            + " | all_authorizations_false=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyObservabilityErrorSnapshot(const string moduleName,
                                              const string eventName,
                                              const datetime errorTimestamp,
                                              const string componentOrigin,
                                              const string errorDetails,
                                              const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "error_snapshot=true"
            + " | error_type=read-only framework"
            + " | error_timestamp=" + TimeValueToText(errorTimestamp)
            + " | component_origin=" + componentOrigin
            + " | error_details=" + errorDetails
            + " | all_observability_outputs_read_only=true"
            + " | all_authorizations_false=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyTelemetryAggregationSnapshot(const string moduleName,
                                                const string eventName,
                                                const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "telemetry_aggregation_snapshot=true"
            + " | aggregated_errors_linked=true"
            + " | aggregated_metrics_linked=true"
            + " | all_observability_outputs_read_only=true"
            + " | all_authorizations_false=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyControllerSummarySnapshot(const string moduleName,
                                             const string eventName,
                                             const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "controller_summary_snapshot=true"
            + " | init_path_linked=true"
            + " | tick_path_linked=true"
            + " | deinit_path_linked=true"
            + " | all_observability_outputs_read_only=true"
            + " | all_authorizations_false=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }

   void LogReadOnlyObservabilityOutputReductionSnapshot(const string moduleName,
                                                        const string eventName,
                                                        const string detail)
   {
      Write(moduleName,
            "INFO",
            eventName,
            "observability_output_reduction_snapshot=true"
            + " | output_reduction_mode=read-only framework"
            + " | duplicate_output_guard=active"
            + " | controller_logger_deduplication=true"
            + " | init_output_group=consolidated"
            + " | tick_output_group=gated"
            + " | deinit_output_group=final"
            + " | tick_output_requires_InpObservabilityLogOnTick=true"
            + " | all_observability_outputs_read_only=true"
            + " | all_authorizations_false=true"
            + " | all_pipeline_layers_no_trade=true"
            + " | no_trade_guard=active"
            + " | trading_authorization=false"
            + " | mt5_run_required=false"
            + " | evidence_generation=false"
            + " | manifest_generation=false"
            + " | Inventory only; no MT5 run; no trading authorization."
            + " | " + detail);
   }
};

#endif
"""

CONTROLLER_TEXT = """#ifndef EA_CONTROLLER_MQH
#define EA_CONTROLLER_MQH

class EaController
{
private:
   long totalTicks;
   long onInitCallCount;
   long onDeinitCallCount;
   datetime lastTickTimestamp;

   void WriteNoTradeObservability(const string eventName, const string lifecycleName)
   {
      logger.NoTradeObservabilityStatusSnapshot("CORE",
                                                eventName,
                                                InpEnableTrading,
                                                InpEnableNoTradeObservability,
                                                InpObservabilityLogOnInit,
                                                InpObservabilityLogOnTick,
                                                "active_trading_instruction=false");
      logger.NoTradeComponentStatusSnapshot("CORE",
                                            eventName,
                                            signalEngine.GetSignalStatusSnapshot(),
                                            riskManager.GetRiskStatusSnapshot(),
                                            executionManager.GetExecutionStatusSnapshot());
      logger.LogNoTradeLifecycleEvent("CORE",
                                      eventName,
                                      lifecycleName,
                                      "observability_only=true");
      WriteReadOnlyRuntimeStatusSnapshot(eventName);
      WriteNoTradePerformanceMetrics(eventName);
      WriteNoTradeSafetyGuardInvariants(eventName);
      WriteReadOnlyMetricsAggregation(eventName);
      WriteReadOnlySystemHealth(eventName);
      WriteReadOnlySignalContextSnapshot(eventName);
      WriteReadOnlyRiskContextSnapshot(eventName);
      WriteReadOnlyExecutionContextSnapshot(eventName);
      WriteReadOnlyPipelineContextAggregationSnapshot(eventName);
      WriteReadOnlyAuthorizationMatrixSnapshot(eventName);
      WriteReadOnlyDecisionGateSnapshot(eventName);
      WriteReadOnlyDecisionRejectionReasonSnapshot(eventName);
      WriteReadOnlyObservabilityConsolidationSnapshot(eventName);
      WriteReadOnlyObservabilityContractRegistrySnapshot(eventName);
      WriteReadOnlyObservabilityErrorSnapshot(eventName);
      WriteReadOnlyTelemetryAggregationSnapshot(eventName);
      WriteReadOnlyControllerSummarySnapshot(eventName);
      WriteReadOnlyObservabilityOutputReductionSnapshot(eventName);
   }

   void WriteReadOnlyRuntimeStatusSnapshot(const string eventName)
   {
      logger.LogReadOnlyRuntimeStatusSnapshot("CORE",
                                             eventName,
                                             "observability_only=true");
   }

   void WriteNoTradePerformanceMetrics(const string eventName)
   {
      logger.LogNoTradePerformanceMetrics("CORE",
                                          eventName,
                                          totalTicks,
                                          onInitCallCount,
                                          onDeinitCallCount,
                                          lastTickTimestamp,
                                          "observability_only=true");
   }

   void WriteNoTradeSafetyGuardInvariants(const string eventName)
   {
      logger.LogNoTradeSafetyGuardInvariants("CORE",
                                             eventName,
                                             "observability_only=true");
   }

   long CalculateHistoricalEventsCount()
   {
      return onInitCallCount + totalTicks + onDeinitCallCount;
   }

   string BuildLastNTicksMetrics()
   {
      return "total_ticks=" + IntegerToString(totalTicks);
   }

   string BuildAggregatedComponentStatus()
   {
      return "controller_status=ready,logger_status=ready";
   }

   void WriteReadOnlyMetricsAggregation(const string eventName)
   {
      logger.LogReadOnlyMetricsAggregation("CORE",
                                           eventName,
                                           CalculateHistoricalEventsCount(),
                                           BuildLastNTicksMetrics(),
                                           BuildAggregatedComponentStatus(),
                                           "observability_only=true");
   }

   void WriteReadOnlySystemHealth(const string eventName)
   {
      logger.LogReadOnlySystemHealth("CORE",
                                     eventName,
                                     InpEnableNoTradeObservability,
                                     TimeCurrent(),
                                     BuildAggregatedComponentStatus(),
                                     "observability_only=true");
   }

   void WriteReadOnlySignalContextSnapshot(const string eventName)
   {
      logger.LogReadOnlySignalContextSnapshot("CORE",
                                              eventName,
                                              signalEngine.GetReadOnlySignalContextSnapshot(),
                                              "observability_only=true");
   }

   void WriteReadOnlyRiskContextSnapshot(const string eventName)
   {
      logger.LogReadOnlyRiskContextSnapshot("CORE",
                                            eventName,
                                            riskManager.GetReadOnlyRiskContextSnapshot(),
                                            "observability_only=true");
   }

   void WriteReadOnlyExecutionContextSnapshot(const string eventName)
   {
      logger.LogReadOnlyExecutionContextSnapshot("CORE",
                                                 eventName,
                                                 executionManager.GetReadOnlyExecutionContextSnapshot(),
                                                 "observability_only=true");
   }

   void WriteReadOnlyPipelineContextAggregationSnapshot(const string eventName)
   {
      logger.LogReadOnlyPipelineContextAggregationSnapshot("CORE",
                                                          eventName,
                                                          "observability_only=true");
   }

   void WriteReadOnlyAuthorizationMatrixSnapshot(const string eventName)
   {
      logger.LogReadOnlyAuthorizationMatrixSnapshot("CORE",
                                                   eventName,
                                                   "observability_only=true");
   }

   void WriteReadOnlyDecisionGateSnapshot(const string eventName)
   {
      logger.LogReadOnlyDecisionGateSnapshot("CORE",
                                            eventName,
                                            "observability_only=true");
   }

   void WriteReadOnlyDecisionRejectionReasonSnapshot(const string eventName)
   {
      logger.LogReadOnlyDecisionRejectionReasonSnapshot("CORE",
                                                       eventName,
                                                       "observability_only=true");
   }

   void WriteReadOnlyObservabilityConsolidationSnapshot(const string eventName)
   {
      logger.LogReadOnlyObservabilityConsolidationSnapshot("CORE",
                                                          eventName,
                                                          "observability_only=true");
   }

   void WriteReadOnlyObservabilityContractRegistrySnapshot(const string eventName)
   {
      logger.LogReadOnlyObservabilityContractRegistrySnapshot("CORE",
                                                             eventName,
                                                             "observability_only=true");
   }

   void WriteReadOnlyObservabilityErrorSnapshot(const string eventName)
   {
      logger.LogReadOnlyObservabilityErrorSnapshot("CORE",
                                                  eventName,
                                                  TimeCurrent(),
                                                  "CORE",
                                                  "read_only_observability_status",
                                                  "observability_only=true");
   }

   void WriteReadOnlyTelemetryAggregationSnapshot(const string eventName)
   {
      logger.LogReadOnlyTelemetryAggregationSnapshot("CORE",
                                                    eventName,
                                                    "observability_only=true");
   }

   void WriteReadOnlyControllerSummarySnapshot(const string eventName)
   {
      logger.LogReadOnlyControllerSummarySnapshot("CORE",
                                                 eventName,
                                                 "observability_only=true");
   }

   void WriteReadOnlyObservabilityOutputReductionSnapshot(const string eventName)
   {
      logger.LogReadOnlyObservabilityOutputReductionSnapshot("CORE",
                                                            eventName,
                                                            "observability_only=true");
   }

public:
   int OnInit()
   {
      onInitCallCount++;
      if(InpObservabilityLogOnInit)
      {
         WriteNoTradeObservability("No-trade observability init", "init");
      }
      return INIT_SUCCEEDED;
   }

   void OnTick()
   {
      totalTicks++;
      lastTickTimestamp = TimeCurrent();
      if(InpObservabilityLogOnTick)
      {
         WriteNoTradeObservability("No-trade observability tick", "tick");
      }
   }

   void OnDeinit(const int reason)
   {
      onDeinitCallCount++;
      logger.LogNoTradeLifecycleEvent("CORE",
                                      "No-trade observability deinit",
                                      "deinit",
                                      "reason=" + IntegerToString(reason));
      WriteReadOnlyRuntimeStatusSnapshot("No-trade observability deinit");
      WriteNoTradePerformanceMetrics("No-trade observability deinit");
      WriteNoTradeSafetyGuardInvariants("No-trade observability deinit");
      WriteReadOnlyMetricsAggregation("No-trade observability deinit");
      WriteReadOnlySystemHealth("No-trade observability deinit");
      WriteReadOnlySignalContextSnapshot("No-trade observability deinit");
      WriteReadOnlyRiskContextSnapshot("No-trade observability deinit");
      WriteReadOnlyExecutionContextSnapshot("No-trade observability deinit");
      WriteReadOnlyPipelineContextAggregationSnapshot("No-trade observability deinit");
      WriteReadOnlyAuthorizationMatrixSnapshot("No-trade observability deinit");
      WriteReadOnlyDecisionGateSnapshot("No-trade observability deinit");
      WriteReadOnlyDecisionRejectionReasonSnapshot("No-trade observability deinit");
      WriteReadOnlyObservabilityConsolidationSnapshot("No-trade observability deinit");
      WriteReadOnlyObservabilityContractRegistrySnapshot("No-trade observability deinit");
      WriteReadOnlyObservabilityErrorSnapshot("No-trade observability deinit");
      WriteReadOnlyTelemetryAggregationSnapshot("No-trade observability deinit");
      WriteReadOnlyControllerSummarySnapshot("No-trade observability deinit");
      WriteReadOnlyObservabilityOutputReductionSnapshot("No-trade observability deinit");
   }
};

#endif
"""

SIGNAL_ENGINE_TEXT = """#ifndef SIGNAL_ENGINE_MQH
#define SIGNAL_ENGINE_MQH

enum SignalDirection
{
   SIGNAL_NONE = 0
};

class SignalEngine
{
public:
   string GetSignalStatusSnapshot()
   {
      return "signal_status=read-only framework | signal_active=false";
   }

   string GetReadOnlySignalContextSnapshot()
   {
      return "signal_context_snapshot=true"
             + " | signal_layer_mode=read-only framework"
             + " | signal_context_available=true"
             + " | signal_direction_authorized=false"
             + " | signal_execution_authorized=false"
             + " | signal_order_intent=false"
             + " | signal_external_evidence_required=false"
             + " | signal_manifest_generation=false"
             + " | no_trade_guard=active";
   }
};

#endif
"""

RISK_MANAGER_TEXT = """#ifndef RISK_MANAGER_MQH
#define RISK_MANAGER_MQH

class RiskManager
{
public:
   string GetRiskStatusSnapshot()
   {
      return "risk_status=read-only framework | risk_active=false";
   }

   string GetReadOnlyRiskContextSnapshot()
   {
      return "risk_context_snapshot=true"
             + " | risk_layer_mode=read-only framework"
             + " | risk_context_available=true"
             + " | risk_authorization=false"
             + " | risk_sizing_authorized=false"
             + " | risk_exposure_authorized=false"
             + " | risk_execution_authorized=false"
             + " | risk_external_evidence_required=false"
             + " | risk_manifest_generation=false"
             + " | no_trade_guard=active";
   }
};

#endif
"""

EXECUTION_MANAGER_TEXT = """#ifndef EXECUTION_MANAGER_MQH
#define EXECUTION_MANAGER_MQH

class ExecutionManager
{
public:
   string GetExecutionStatusSnapshot()
   {
      return "execution_status=read-only framework | execution_active=false";
   }

   string GetReadOnlyExecutionContextSnapshot()
   {
      return "execution_context_snapshot=true"
             + " | execution_layer_mode=read-only framework"
             + " | execution_context_available=true"
             + " | execution_authorization=false"
             + " | execution_request_authorized=false"
             + " | execution_route_authorized=false"
             + " | execution_dispatch_authorized=false"
             + " | execution_external_evidence_required=false"
             + " | execution_manifest_generation=false"
             + " | no_trade_guard=active";
   }
};

#endif
"""

TRADING_SYSTEM_TEXT = """#include "core/EaController.mqh"

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
"""

TASK269_ERROR_FIELDS = (
    "error_snapshot=true",
    "error_type=read-only framework",
    "error_timestamp",
    "component_origin",
    "error_details",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    "Inventory only; no MT5 run; no trading authorization.",
)

TASK271_TELEMETRY_AGGREGATION_FIELDS = (
    "telemetry_aggregation_snapshot=true",
    "aggregated_errors_linked=true",
    "aggregated_metrics_linked=true",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    "Inventory only; no MT5 run; no trading authorization.",
)

TASK272_CONTROLLER_SUMMARY_FIELDS = (
    "controller_summary_snapshot=true",
    " | init_path_linked=true",
    " | tick_path_linked=true",
    " | deinit_path_linked=true",
    "all_observability_outputs_read_only=true",
    "all_authorizations_false=true",
    "no_trade_guard=active",
    "trading_authorization=false",
    "mt5_run_required=false",
    "evidence_generation=false",
    "manifest_generation=false",
    "Inventory only; no MT5 run; no trading authorization.",
)


def fail(message: str) -> int:
    print("MQ5 no-trade observability contract self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_mq5_no_trade_observability",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def complete_required_files() -> dict[str, str | None]:
    return {
        "config/InputConfig.mqh": INPUT_CONFIG_TEXT,
        "core/EaController.mqh": CONTROLLER_TEXT,
        "logger/Logger.mqh": LOGGER_TEXT,
        "signals/SignalEngine.mqh": SIGNAL_ENGINE_TEXT,
        "risk/RiskManager.mqh": RISK_MANAGER_TEXT,
        "execution/ExecutionManager.mqh": EXECUTION_MANAGER_TEXT,
    }


def complete_source_texts() -> dict[str, str]:
    return {
        "config/InputConfig.mqh": INPUT_CONFIG_TEXT,
        "core/EaController.mqh": CONTROLLER_TEXT,
        "logger/Logger.mqh": LOGGER_TEXT,
        "signals/SignalEngine.mqh": SIGNAL_ENGINE_TEXT,
        "risk/RiskManager.mqh": RISK_MANAGER_TEXT,
        "execution/ExecutionManager.mqh": EXECUTION_MANAGER_TEXT,
        "TradingSystem.mq5": TRADING_SYSTEM_TEXT,
    }


def assert_passes(validator, files: dict[str, str | None], sources: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(files, sources)
    if failures:
        return f"{label}: expected PASS, got failures: {failures}"
    return ""


def assert_fails(validator, files: dict[str, str | None], sources: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(files, sources)
    if not failures:
        return f"{label}: expected failure, got PASS"
    return ""


def test_complete_fixture_passes(validator) -> str:
    return assert_passes(
        validator,
        complete_required_files(),
        complete_source_texts(),
        "complete no-trade observability fixture",
    )


def test_missing_input_config_fails(validator) -> str:
    files = complete_required_files()
    files["config/InputConfig.mqh"] = None
    sources = complete_source_texts()
    del sources["config/InputConfig.mqh"]
    return assert_fails(validator, files, sources, "missing InputConfig.mqh")


def test_enable_trading_true_fails(validator) -> str:
    files = complete_required_files()
    files["config/InputConfig.mqh"] = INPUT_CONFIG_TEXT.replace(
        "input bool InpEnableTrading = false;",
        "input bool InpEnableTrading = true;",
    )
    sources = complete_source_texts()
    sources["config/InputConfig.mqh"] = files["config/InputConfig.mqh"] or ""
    return assert_fails(validator, files, sources, "InpEnableTrading true default")


def test_missing_observability_text_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("no-trade observability scaffold", "")
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "missing observability scaffold text")


def test_missing_structured_snapshot_field_fails(validator) -> str:
    for field in validator.STRUCTURED_SNAPSHOT_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = LOGGER_TEXT.replace(field, "", 1)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing structured field {field}")
        if error:
            return error
    return ""


def test_missing_component_snapshot_field_fails(validator) -> str:
    for field in validator.LOGGER_COMPONENT_SNAPSHOT_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = LOGGER_TEXT.replace(field, "", 1)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing component field {field}")
        if error:
            return error
    return ""


def test_missing_lifecycle_telemetry_field_fails(validator) -> str:
    for field in validator.LIFECYCLE_TELEMETRY_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = LOGGER_TEXT.replace(field, "", 1)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing lifecycle field {field}")
        if error:
            return error
    return ""


def remove_runtime_field(field: str) -> str:
    marker = "LogReadOnlyRuntimeStatusSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_runtime_status_snapshot_field_fails(validator) -> str:
    for field in validator.RUNTIME_STATUS_SNAPSHOT_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_runtime_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing runtime field {field}")
        if error:
            return error
    return ""


def remove_performance_field(field: str) -> str:
    marker = "LogNoTradePerformanceMetrics"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_performance_metrics_field_fails(validator) -> str:
    for field in validator.PERFORMANCE_METRICS_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_performance_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing performance field {field}")
        if error:
            return error
    return ""


def remove_safety_guard_field(field: str) -> str:
    marker = "LogNoTradeSafetyGuardInvariants"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_safety_guard_invariant_field_fails(validator) -> str:
    for field in validator.SAFETY_GUARD_INVARIANT_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_safety_guard_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing safety guard field {field}")
        if error:
            return error
    return ""


def remove_metrics_aggregation_field(field: str) -> str:
    marker = "LogReadOnlyMetricsAggregation"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_metrics_aggregation_field_fails(validator) -> str:
    for field in validator.METRICS_AGGREGATION_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_metrics_aggregation_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing metrics aggregation field {field}")
        if error:
            return error
    return ""


def remove_system_health_field(field: str) -> str:
    marker = "LogReadOnlySystemHealth"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_system_health_field_fails(validator) -> str:
    for field in validator.SYSTEM_HEALTH_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_system_health_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing system health field {field}")
        if error:
            return error
    return ""


def remove_signal_context_field(field: str) -> str:
    marker = "GetReadOnlySignalContextSnapshot"
    before, after = SIGNAL_ENGINE_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_signal_context_field_fails(validator) -> str:
    for field in validator.SIGNAL_CONTEXT_FIELDS:
        files = complete_required_files()
        files["signals/SignalEngine.mqh"] = remove_signal_context_field(field)
        sources = complete_source_texts()
        sources["signals/SignalEngine.mqh"] = files["signals/SignalEngine.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing signal context field {field}")
        if error:
            return error
    return ""


def test_logger_missing_signal_context_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlySignalContextSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing signal context helper")


def remove_risk_context_field(field: str) -> str:
    marker = "GetReadOnlyRiskContextSnapshot"
    before, after = RISK_MANAGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_risk_context_field_fails(validator) -> str:
    for field in validator.RISK_CONTEXT_FIELDS:
        files = complete_required_files()
        files["risk/RiskManager.mqh"] = remove_risk_context_field(field)
        sources = complete_source_texts()
        sources["risk/RiskManager.mqh"] = files["risk/RiskManager.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing risk context field {field}")
        if error:
            return error
    return ""


def test_logger_missing_risk_context_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyRiskContextSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing risk context helper")


def remove_execution_context_field(field: str) -> str:
    marker = "GetReadOnlyExecutionContextSnapshot"
    before, after = EXECUTION_MANAGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_execution_context_field_fails(validator) -> str:
    for field in validator.EXECUTION_CONTEXT_FIELDS:
        files = complete_required_files()
        files["execution/ExecutionManager.mqh"] = remove_execution_context_field(field)
        sources = complete_source_texts()
        sources["execution/ExecutionManager.mqh"] = files["execution/ExecutionManager.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing execution context field {field}")
        if error:
            return error
    return ""


def test_logger_missing_execution_context_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyExecutionContextSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing execution context helper")


def remove_pipeline_context_field(field: str) -> str:
    marker = "LogReadOnlyPipelineContextAggregationSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_pipeline_context_aggregation_field_fails(validator) -> str:
    for field in validator.PIPELINE_CONTEXT_AGGREGATION_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_pipeline_context_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing pipeline context aggregation field {field}")
        if error:
            return error
    return ""


def test_logger_missing_pipeline_context_aggregation_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyPipelineContextAggregationSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing pipeline context aggregation helper")


def remove_authorization_matrix_field(field: str) -> str:
    marker = "LogReadOnlyAuthorizationMatrixSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_authorization_matrix_field_fails(validator) -> str:
    for field in validator.AUTHORIZATION_MATRIX_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_authorization_matrix_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing authorization matrix field {field}")
        if error:
            return error
    return ""


def test_logger_missing_authorization_matrix_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyAuthorizationMatrixSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing authorization matrix helper")


def remove_decision_gate_field(field: str) -> str:
    marker = "LogReadOnlyDecisionGateSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_decision_gate_field_fails(validator) -> str:
    for field in validator.DECISION_GATE_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_decision_gate_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing decision gate field {field}")
        if error:
            return error
    return ""


def test_logger_missing_decision_gate_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyDecisionGateSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing decision gate helper")


def remove_decision_rejection_field(field: str) -> str:
    marker = "LogReadOnlyDecisionRejectionReasonSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_decision_rejection_field_fails(validator) -> str:
    for field in validator.DECISION_REJECTION_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_decision_rejection_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing decision rejection field {field}")
        if error:
            return error
    return ""


def test_logger_missing_decision_rejection_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyDecisionRejectionReasonSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing decision rejection helper")


def remove_observability_consolidation_field(field: str) -> str:
    marker = "LogReadOnlyObservabilityConsolidationSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_observability_consolidation_field_fails(validator) -> str:
    for field in validator.OBSERVABILITY_CONSOLIDATION_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_observability_consolidation_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing observability consolidation field {field}")
        if error:
            return error
    return ""


def test_logger_missing_observability_consolidation_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyObservabilityConsolidationSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing observability consolidation helper")


def remove_observability_registry_field(field: str) -> str:
    marker = "LogReadOnlyObservabilityContractRegistrySnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "")


def test_missing_observability_registry_field_fails(validator) -> str:
    for field in validator.OBSERVABILITY_REGISTRY_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_observability_registry_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing observability registry field {field}")
        if error:
            return error
    return ""


def test_logger_missing_observability_registry_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyObservabilityContractRegistrySnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing observability registry helper")


def remove_observability_error_field(field: str) -> str:
    marker = "LogReadOnlyObservabilityErrorSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_observability_error_field_fails(validator) -> str:
    for field in TASK269_ERROR_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_observability_error_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing observability error field {field}")
        if error:
            return error
    return ""


def test_logger_missing_observability_error_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyObservabilityErrorSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing observability error helper")


def remove_telemetry_aggregation_field(field: str) -> str:
    marker = "LogReadOnlyTelemetryAggregationSnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_telemetry_aggregation_field_fails(validator) -> str:
    for field in TASK271_TELEMETRY_AGGREGATION_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_telemetry_aggregation_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing telemetry aggregation field {field}")
        if error:
            return error
    return ""


def test_logger_missing_telemetry_aggregation_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyTelemetryAggregationSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing telemetry aggregation helper")


def remove_controller_summary_field(field: str) -> str:
    marker = "LogReadOnlyControllerSummarySnapshot"
    before, after = LOGGER_TEXT.split(marker, 1)
    return before + marker + after.replace(field, "", 1)


def test_missing_controller_summary_field_fails(validator) -> str:
    for field in TASK272_CONTROLLER_SUMMARY_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = remove_controller_summary_field(field)
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing controller summary field {field}")
        if error:
            return error
    return ""


def test_logger_missing_controller_summary_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyControllerSummarySnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing controller summary helper")


def test_controller_missing_snapshot_helper_call_fails(validator) -> str:
    files = complete_required_files()
    files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(
        "NoTradeObservabilityStatusSnapshot",
        "NoTradeObservability",
    )
    sources = complete_source_texts()
    sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
    return assert_fails(
        validator,
        files,
        sources,
        "EaController missing structured snapshot helper call",
    )


def test_controller_missing_lifecycle_path_fails(validator) -> str:
    replacements = (
        ('"init"', '"missing_init"'),
        ('"tick"', '"missing_tick"'),
        ('"deinit"', '"missing_deinit"'),
    )
    for old, new in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(old, new, 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing lifecycle path {old}")
        if error:
            return error
    return ""


def test_controller_missing_runtime_snapshot_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyRuntimeStatusSnapshot(eventName);",
        'WriteReadOnlyRuntimeStatusSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyRuntimeStatusSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing runtime marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_performance_metrics_path_fails(validator) -> str:
    replacements = (
        "WriteNoTradePerformanceMetrics(eventName);",
        'WriteNoTradePerformanceMetrics("No-trade observability deinit");',
        'logger.LogNoTradePerformanceMetrics("CORE",',
        "onInitCallCount++",
        "onDeinitCallCount++",
        "lastTickTimestamp = TimeCurrent();",
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing performance marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_safety_guard_path_fails(validator) -> str:
    replacements = (
        "WriteNoTradeSafetyGuardInvariants(eventName);",
        'WriteNoTradeSafetyGuardInvariants("No-trade observability deinit");',
        'logger.LogNoTradeSafetyGuardInvariants("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing safety guard marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_metrics_aggregation_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyMetricsAggregation(eventName);",
        'WriteReadOnlyMetricsAggregation("No-trade observability deinit");',
        'logger.LogReadOnlyMetricsAggregation("CORE",',
        "CalculateHistoricalEventsCount(),",
        "BuildLastNTicksMetrics(),",
        "                                           BuildAggregatedComponentStatus(),",
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing metrics aggregation marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_system_health_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlySystemHealth(eventName);",
        'WriteReadOnlySystemHealth("No-trade observability deinit");',
        'logger.LogReadOnlySystemHealth("CORE",',
        "                                     BuildAggregatedComponentStatus(),",
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing system health marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_signal_context_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlySignalContextSnapshot(eventName);",
        'WriteReadOnlySignalContextSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlySignalContextSnapshot("CORE",',
        "signalEngine.GetReadOnlySignalContextSnapshot()",
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing signal context marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_risk_context_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyRiskContextSnapshot(eventName);",
        'WriteReadOnlyRiskContextSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyRiskContextSnapshot("CORE",',
        "riskManager.GetReadOnlyRiskContextSnapshot()",
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing risk context marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_execution_context_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyExecutionContextSnapshot(eventName);",
        'WriteReadOnlyExecutionContextSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyExecutionContextSnapshot("CORE",',
        "executionManager.GetReadOnlyExecutionContextSnapshot()",
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing execution context marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_pipeline_context_aggregation_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyPipelineContextAggregationSnapshot(eventName);",
        'WriteReadOnlyPipelineContextAggregationSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyPipelineContextAggregationSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing pipeline context aggregation marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_authorization_matrix_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyAuthorizationMatrixSnapshot(eventName);",
        'WriteReadOnlyAuthorizationMatrixSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyAuthorizationMatrixSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing authorization matrix marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_decision_gate_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyDecisionGateSnapshot(eventName);",
        'WriteReadOnlyDecisionGateSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyDecisionGateSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing decision gate marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_decision_rejection_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyDecisionRejectionReasonSnapshot(eventName);",
        'WriteReadOnlyDecisionRejectionReasonSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyDecisionRejectionReasonSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing decision rejection marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_observability_consolidation_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyObservabilityConsolidationSnapshot(eventName);",
        'WriteReadOnlyObservabilityConsolidationSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyObservabilityConsolidationSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing observability consolidation marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_observability_registry_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyObservabilityContractRegistrySnapshot(eventName);",
        'WriteReadOnlyObservabilityContractRegistrySnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyObservabilityContractRegistrySnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing observability registry marker {marker}")
        if error:
            return error
    return ""


def test_controller_missing_observability_error_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyObservabilityErrorSnapshot(eventName);",
        'WriteReadOnlyObservabilityErrorSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyObservabilityErrorSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing observability error marker {marker}")
        if error:
            return error
    return ""


def test_controller_observability_error_tick_gate_fails(validator) -> str:
    files = complete_required_files()
    files["core/EaController.mqh"] = CONTROLLER_TEXT.replace("InpObservabilityLogOnTick", "InpObservabilityTickDisabled")
    sources = complete_source_texts()
    sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
    return assert_fails(validator, files, sources, "EaController missing observability error tick gate")


def test_controller_missing_telemetry_aggregation_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyTelemetryAggregationSnapshot(eventName);",
        'WriteReadOnlyTelemetryAggregationSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyTelemetryAggregationSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing telemetry aggregation marker {marker}")
        if error:
            return error
    return ""


def test_controller_telemetry_aggregation_tick_gate_fails(validator) -> str:
    files = complete_required_files()
    files["core/EaController.mqh"] = CONTROLLER_TEXT.replace("InpObservabilityLogOnTick", "InpObservabilityTickDisabled")
    sources = complete_source_texts()
    sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
    return assert_fails(validator, files, sources, "EaController missing telemetry aggregation tick gate")


def test_controller_missing_controller_summary_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyControllerSummarySnapshot(eventName);",
        'WriteReadOnlyControllerSummarySnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyControllerSummarySnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing controller summary marker {marker}")
        if error:
            return error
    return ""


def test_controller_summary_tick_gate_fails(validator) -> str:
    files = complete_required_files()
    files["core/EaController.mqh"] = CONTROLLER_TEXT.replace("InpObservabilityLogOnTick", "InpObservabilityTickDisabled")
    sources = complete_source_texts()
    sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
    return assert_fails(validator, files, sources, "EaController missing controller summary tick gate")


def test_missing_observability_output_reduction_field_fails(validator) -> str:
    for field in validator.OBSERVABILITY_OUTPUT_REDUCTION_FIELDS:
        files = complete_required_files()
        files["logger/Logger.mqh"] = (files["logger/Logger.mqh"] or "").replace(field, "")
        sources = complete_source_texts()
        sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
        error = assert_fails(validator, files, sources, f"missing observability output reduction field {field}")
        if error:
            return error
    return ""


def test_missing_observability_output_reduction_helper_fails(validator) -> str:
    files = complete_required_files()
    files["logger/Logger.mqh"] = LOGGER_TEXT.replace("LogReadOnlyObservabilityOutputReductionSnapshot", "", 1)
    sources = complete_source_texts()
    sources["logger/Logger.mqh"] = files["logger/Logger.mqh"] or ""
    return assert_fails(validator, files, sources, "Logger missing observability output reduction helper")


def test_controller_missing_observability_output_reduction_path_fails(validator) -> str:
    replacements = (
        "WriteReadOnlyObservabilityOutputReductionSnapshot(eventName);",
        'WriteReadOnlyObservabilityOutputReductionSnapshot("No-trade observability deinit");',
        'logger.LogReadOnlyObservabilityOutputReductionSnapshot("CORE",',
    )
    for marker in replacements:
        files = complete_required_files()
        files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(marker, "", 1)
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
        error = assert_fails(validator, files, sources, f"EaController missing observability output reduction marker {marker}")
        if error:
            return error
    return ""


def test_observability_output_reduction_tick_gate_fails(validator) -> str:
    files = complete_required_files()
    files["core/EaController.mqh"] = CONTROLLER_TEXT.replace("InpObservabilityLogOnTick", "InpObservabilityTickDisabled")
    sources = complete_source_texts()
    sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
    return assert_fails(validator, files, sources, "EaController missing observability output reduction tick gate")


def test_controller_missing_component_snapshot_fails(validator) -> str:
    files = complete_required_files()
    files["core/EaController.mqh"] = CONTROLLER_TEXT.replace(
        "NoTradeComponentStatusSnapshot",
        "NoTradeObservabilityStatusSnapshot",
        1,
    )
    sources = complete_source_texts()
    sources["core/EaController.mqh"] = files["core/EaController.mqh"] or ""
    return assert_fails(
        validator,
        files,
        sources,
        "EaController missing component snapshot helper call",
    )


def test_component_missing_read_only_status_fails(validator) -> str:
    replacements = (
        ("signals/SignalEngine.mqh", "signal_status=read-only framework"),
        ("risk/RiskManager.mqh", "risk_status=read-only framework"),
        ("execution/ExecutionManager.mqh", "execution_status=read-only framework"),
    )
    for rel_path, field in replacements:
        files = complete_required_files()
        files[rel_path] = (files[rel_path] or "").replace(field, "", 1)
        sources = complete_source_texts()
        sources[rel_path] = files[rel_path] or ""
        error = assert_fails(validator, files, sources, f"{rel_path} missing {field}")
        if error:
            return error
    return ""


def test_forbidden_trading_keywords_fail(validator) -> str:
    for keyword in validator.FORBIDDEN_TRADING_KEYWORDS:
        files = complete_required_files()
        sources = complete_source_texts()
        sources["core/EaController.mqh"] = CONTROLLER_TEXT + f"\n// {keyword}\n"
        error = assert_fails(validator, files, sources, f"forbidden keyword {keyword}")
        if error:
            return error
    return ""


def test_extra_mq5_source_file_fails(validator) -> str:
    files = complete_required_files()
    sources = complete_source_texts()
    sources["extra/Unexpected.mqh"] = "#ifndef UNEXPECTED_MQH\n#define UNEXPECTED_MQH\n#endif\n"
    return assert_fails(validator, files, sources, "extra MQ5 source file")


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    validator = load_validator_module()
    tests = [
        test_complete_fixture_passes,
        test_missing_input_config_fails,
        test_enable_trading_true_fails,
        test_missing_observability_text_fails,
        test_missing_structured_snapshot_field_fails,
        test_missing_component_snapshot_field_fails,
        test_missing_lifecycle_telemetry_field_fails,
        test_missing_runtime_status_snapshot_field_fails,
        test_missing_performance_metrics_field_fails,
        test_missing_safety_guard_invariant_field_fails,
        test_missing_metrics_aggregation_field_fails,
        test_missing_system_health_field_fails,
        test_missing_signal_context_field_fails,
        test_logger_missing_signal_context_helper_fails,
        test_missing_risk_context_field_fails,
        test_logger_missing_risk_context_helper_fails,
        test_missing_execution_context_field_fails,
        test_logger_missing_execution_context_helper_fails,
        test_missing_pipeline_context_aggregation_field_fails,
        test_logger_missing_pipeline_context_aggregation_helper_fails,
        test_missing_authorization_matrix_field_fails,
        test_logger_missing_authorization_matrix_helper_fails,
        test_missing_decision_gate_field_fails,
        test_logger_missing_decision_gate_helper_fails,
        test_missing_decision_rejection_field_fails,
        test_logger_missing_decision_rejection_helper_fails,
        test_missing_observability_consolidation_field_fails,
        test_logger_missing_observability_consolidation_helper_fails,
        test_missing_observability_registry_field_fails,
        test_logger_missing_observability_registry_helper_fails,
        test_missing_observability_error_field_fails,
        test_logger_missing_observability_error_helper_fails,
        test_missing_telemetry_aggregation_field_fails,
        test_logger_missing_telemetry_aggregation_helper_fails,
        test_missing_controller_summary_field_fails,
        test_logger_missing_controller_summary_helper_fails,
        test_controller_missing_snapshot_helper_call_fails,
        test_controller_missing_lifecycle_path_fails,
        test_controller_missing_runtime_snapshot_path_fails,
        test_controller_missing_performance_metrics_path_fails,
        test_controller_missing_safety_guard_path_fails,
        test_controller_missing_metrics_aggregation_path_fails,
        test_controller_missing_system_health_path_fails,
        test_controller_missing_signal_context_path_fails,
        test_controller_missing_risk_context_path_fails,
        test_controller_missing_execution_context_path_fails,
        test_controller_missing_pipeline_context_aggregation_path_fails,
        test_controller_missing_authorization_matrix_path_fails,
        test_controller_missing_decision_gate_path_fails,
        test_controller_missing_decision_rejection_path_fails,
        test_controller_missing_observability_consolidation_path_fails,
        test_controller_missing_observability_registry_path_fails,
        test_controller_missing_observability_error_path_fails,
        test_controller_observability_error_tick_gate_fails,
        test_controller_missing_telemetry_aggregation_path_fails,
        test_controller_telemetry_aggregation_tick_gate_fails,
        test_controller_missing_controller_summary_path_fails,
        test_controller_summary_tick_gate_fails,
        test_missing_observability_output_reduction_field_fails,
        test_missing_observability_output_reduction_helper_fails,
        test_controller_missing_observability_output_reduction_path_fails,
        test_observability_output_reduction_tick_gate_fails,
        test_controller_missing_component_snapshot_fails,
        test_component_missing_read_only_status_fails,
        test_forbidden_trading_keywords_fail,
        test_extra_mq5_source_file_fails,
    ]
    for test in tests:
        error = test(validator)
        if error:
            return fail(error)

    print("MQ5 no-trade observability contract self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
