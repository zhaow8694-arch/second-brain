#ifndef LOGGER_MQH
#define LOGGER_MQH

#include "../config/InputConfig.mqh"

class Logger
{
private:
   bool initialized;

   string BuildMessage(const string moduleName,
                       const string level,
                       const string eventName,
                       const string detail)
   {
      string timeText = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
      return timeText + " [" + moduleName + "] [" + level + "] [" + _Symbol + "] " + eventName + " | " + detail;
   }

   void Write(const string moduleName,
              const string level,
              const string eventName,
              const string detail)
   {
      Print(BuildMessage(moduleName, level, eventName, detail));
   }

   string TimeValueToText(const datetime value)
   {
      if(value <= 0)
      {
         return "none";
      }

      return TimeToString(value, TIME_DATE | TIME_SECONDS);
   }

public:
   Logger()
   {
      initialized = false;
   }

   bool Init()
   {
      initialized = true;
      return initialized;
   }

   void Info(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName, "INFO", eventName, detail);
   }

   void Warning(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName, "WARNING", eventName, detail);
   }

   void Error(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName, "ERROR", eventName, detail);
   }

   void Debug(const string moduleName, const string eventName, const string detail)
   {
      if(!InpEnableDebugLog)
      {
         return;
      }

      Write(moduleName, "DEBUG", eventName, detail);
   }

   void NoTradeObservability(const string moduleName, const string eventName, const string detail)
   {
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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
      if(!InpEnableNoTradeObservability)
      {
         return;
      }

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

   string BoolToText(const bool value)
   {
      if(value)
      {
         return "true";
      }

      return "false";
   }
};

#endif
