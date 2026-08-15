#ifndef EXECUTION_MANAGER_MQH
#define EXECUTION_MANAGER_MQH

#include "../config/InputConfig.mqh"
#include "../logger/Logger.mqh"
#include "../signals/SignalEngine.mqh"

class ExecutionManager
{
private:
   Logger *logger;

public:
   ExecutionManager()
   {
      logger = NULL;
   }

   bool Init(Logger &log)
   {
      logger = &log;
      logger.Info("EXECUTION", "ExecutionManager initialized", "Execution disabled in v0.1.0");
      return (logger != NULL);
   }

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

#endif
