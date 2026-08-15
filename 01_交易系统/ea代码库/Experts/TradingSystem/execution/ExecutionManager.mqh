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
