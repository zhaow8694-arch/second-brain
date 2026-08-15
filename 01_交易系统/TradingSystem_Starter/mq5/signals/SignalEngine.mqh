#ifndef SIGNAL_ENGINE_MQH
#define SIGNAL_ENGINE_MQH

#include "../logger/Logger.mqh"

enum SignalDirection
{
   SIGNAL_SELL = -1,
   SIGNAL_NONE = 0,
   SIGNAL_BUY = 1
};

struct SignalResult
{
   SignalDirection direction;
   double confidence;
   string reason;
};

class SignalEngine
{
private:
   Logger *logger;
   int fastEmaHandle;
   int slowEmaHandle;
   int totalSignalLogEvents;
   int printedSignalLogs;
   int suppressedSignalLogs;
   SignalDirection lastLoggedSignalDirection;
   SignalDirection lastSignalLogDirection;
   bool hasSignalLogDirection;
   bool hasLoggedSignalDirection;
   int sameDirectionSignalLogCount;

   void ResetLogStats()
   {
      totalSignalLogEvents = 0;
      printedSignalLogs = 0;
      suppressedSignalLogs = 0;
      lastLoggedSignalDirection = SIGNAL_NONE;
      lastSignalLogDirection = SIGNAL_NONE;
      hasSignalLogDirection = false;
      hasLoggedSignalDirection = false;
      sameDirectionSignalLogCount = 0;
   }

   SignalResult BuildResult(const SignalDirection direction,
                            const double confidence,
                            const string reason)
   {
      SignalResult result;
      result.direction = direction;
      result.confidence = confidence;
      result.reason = reason;
      return result;
   }

   bool HasValidParameters()
   {
      if(InpFastEmaPeriod <= 0 || InpSlowEmaPeriod <= 0)
      {
         return false;
      }

      if(InpFastEmaPeriod >= InpSlowEmaPeriod)
      {
         return false;
      }

      if(InpEmaLookbackShift < 1)
      {
         return false;
      }

      if(InpEmaMinDistancePoints < 0.0)
      {
         return false;
      }

      return true;
   }

   bool CreateEmaHandles()
   {
      fastEmaHandle = iMA(_Symbol, InpSignalTimeframe, InpFastEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      slowEmaHandle = iMA(_Symbol, InpSignalTimeframe, InpSlowEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);

      if(fastEmaHandle == INVALID_HANDLE || slowEmaHandle == INVALID_HANDLE)
      {
         if(fastEmaHandle != INVALID_HANDLE)
         {
            IndicatorRelease(fastEmaHandle);
            fastEmaHandle = INVALID_HANDLE;
         }

         if(slowEmaHandle != INVALID_HANDLE)
         {
            IndicatorRelease(slowEmaHandle);
            slowEmaHandle = INVALID_HANDLE;
         }

         return false;
      }

      return true;
   }

   bool ReadEmaValue(const int handle, const int shift, double &value)
   {
      double buffer[1];
      int copied = CopyBuffer(handle, 0, shift, 1, buffer);
      if(copied != 1)
      {
         return false;
      }

      value = buffer[0];
      return true;
   }

   string BuildEmaReason(const string directionText,
                         const double fastEma,
                         const double slowEma,
                         const double distancePoints)
   {
      return directionText +
             " | fastEMA=" + DoubleToString(fastEma, _Digits) +
             " | slowEMA=" + DoubleToString(slowEma, _Digits) +
             " | timeframe=" + EnumToString(InpSignalTimeframe) +
             " | shift=" + IntegerToString(InpEmaLookbackShift) +
             " | distancePoints=" + DoubleToString(distancePoints, 2);
   }

   string SignalDirectionToText(const SignalDirection direction)
   {
      if(direction == SIGNAL_BUY)
      {
         return "BUY";
      }

      if(direction == SIGNAL_SELL)
      {
         return "SELL";
      }

      if(direction == SIGNAL_NONE)
      {
         return "NONE";
      }

      return "UNKNOWN";
   }

   void UpdateSameDirectionCount(const SignalDirection direction)
   {
      if(hasSignalLogDirection && direction == lastSignalLogDirection)
      {
         sameDirectionSignalLogCount++;
      }
      else
      {
         sameDirectionSignalLogCount = 1;
      }

      lastSignalLogDirection = direction;
      hasSignalLogDirection = true;
   }

   void WriteSignalLog(const string eventName, const string detail)
   {
      if(logger != NULL)
      {
         logger.Debug("SIGNAL", eventName, detail);
      }
   }

   void ProcessSignalLog(const SignalResult &result)
   {
      totalSignalLogEvents++;
      UpdateSameDirectionCount(result.direction);

      if(!InpPrintSignalLog)
      {
         suppressedSignalLogs++;
         return;
      }

      bool shouldPrint = false;
      bool summaryLog = false;

      if(InpPrintSignalLogOnlyOnDirectionChange)
      {
         if(!hasLoggedSignalDirection || result.direction != lastLoggedSignalDirection)
         {
            shouldPrint = true;
         }
         else if(InpSignalLogEveryN > 0 && (sameDirectionSignalLogCount % InpSignalLogEveryN) == 0)
         {
            shouldPrint = true;
            summaryLog = true;
         }
      }
      else
      {
         if(InpSignalLogEveryN <= 0 || sameDirectionSignalLogCount == 1 || (sameDirectionSignalLogCount % InpSignalLogEveryN) == 0)
         {
            shouldPrint = true;
            summaryLog = (sameDirectionSignalLogCount > 1);
         }
      }

      if(shouldPrint)
      {
         printedSignalLogs++;
         lastLoggedSignalDirection = result.direction;
         hasLoggedSignalDirection = true;

         if(summaryLog)
         {
            WriteSignalLog("Signal evaluated summary",
                           "direction=" + SignalDirectionToText(result.direction) +
                           ", sameDirectionSignalLogCount=" + IntegerToString(sameDirectionSignalLogCount) +
                           ", reason=" + result.reason);
         }
         else
         {
            WriteSignalLog("Signal evaluated",
                           "direction=" + SignalDirectionToText(result.direction) +
                           ", reason=" + result.reason);
         }

         return;
      }

      suppressedSignalLogs++;
   }

   SignalResult FinalizeResult(SignalResult &result)
   {
      ProcessSignalLog(result);
      return result;
   }

public:
   SignalEngine()
   {
      logger = NULL;
      fastEmaHandle = INVALID_HANDLE;
      slowEmaHandle = INVALID_HANDLE;
      ResetLogStats();
   }

   bool Init(Logger &log)
   {
      logger = &log;
      ResetLogStats();

      if(!InpEnableEmaSignal)
      {
         logger.Info("SIGNAL", "SignalEngine initialized", "EMA signal disabled");
         return true;
      }

      if(!HasValidParameters())
      {
         logger.Error("SIGNAL", "SignalEngine initialization failed", "Invalid EMA parameters");
         return false;
      }

      if(!CreateEmaHandles())
      {
         logger.Warning("SIGNAL", "SignalEngine initialized with invalid EMA handle", "Evaluate will return SIGNAL_NONE");
         return true;
      }

      logger.Info("SIGNAL", "SignalEngine initialized", "EMA observation mode");
      return true;
   }

   void Deinit()
   {
      if(fastEmaHandle != INVALID_HANDLE)
      {
         IndicatorRelease(fastEmaHandle);
         fastEmaHandle = INVALID_HANDLE;
      }

      if(slowEmaHandle != INVALID_HANDLE)
      {
         IndicatorRelease(slowEmaHandle);
         slowEmaHandle = INVALID_HANDLE;
      }

      if(logger != NULL)
      {
         logger.Info("SIGNAL", "SignalEngine deinitialized", "EMA handles released");
      }
   }

   int GetTotalSignalLogEvents()
   {
      return totalSignalLogEvents;
   }

   int GetPrintedSignalLogs()
   {
      return printedSignalLogs;
   }

   int GetSuppressedSignalLogs()
   {
      return suppressedSignalLogs;
   }

   string GetLastLoggedSignalDirectionText()
   {
      return SignalDirectionToText(lastLoggedSignalDirection);
   }

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

   SignalResult Evaluate()
   {
      if(!InpEnableEmaSignal)
      {
         SignalResult result = BuildResult(SIGNAL_NONE, 0.0, "EMA signal disabled");
         return FinalizeResult(result);
      }

      if(!HasValidParameters())
      {
         SignalResult result = BuildResult(SIGNAL_NONE, 0.0, "Invalid EMA parameters");
         return FinalizeResult(result);
      }

      if(fastEmaHandle == INVALID_HANDLE || slowEmaHandle == INVALID_HANDLE)
      {
         SignalResult result = BuildResult(SIGNAL_NONE, 0.0, "Invalid EMA indicator handle");
         return FinalizeResult(result);
      }

      double fastEma = 0.0;
      double slowEma = 0.0;

      if(!ReadEmaValue(fastEmaHandle, InpEmaLookbackShift, fastEma))
      {
         SignalResult result = BuildResult(SIGNAL_NONE, 0.0, "CopyBuffer failed for fast EMA");
         return FinalizeResult(result);
      }

      if(!ReadEmaValue(slowEmaHandle, InpEmaLookbackShift, slowEma))
      {
         SignalResult result = BuildResult(SIGNAL_NONE, 0.0, "CopyBuffer failed for slow EMA");
         return FinalizeResult(result);
      }

      double distancePoints = MathAbs(fastEma - slowEma) / _Point;
      if(distancePoints < InpEmaMinDistancePoints)
      {
         SignalResult result = BuildResult(SIGNAL_NONE,
                                           0.0,
                                           "EMA distance insufficient | distancePoints=" + DoubleToString(distancePoints, 2) +
                                           " | minDistance=" + DoubleToString(InpEmaMinDistancePoints, 2));
         return FinalizeResult(result);
      }

      SignalResult result;
      if(fastEma > slowEma)
      {
         result = BuildResult(SIGNAL_BUY, 0.60, BuildEmaReason("EMA trend BUY", fastEma, slowEma, distancePoints));
      }
      else if(fastEma < slowEma)
      {
         result = BuildResult(SIGNAL_SELL, 0.60, BuildEmaReason("EMA trend SELL", fastEma, slowEma, distancePoints));
      }
      else
      {
         result = BuildResult(SIGNAL_NONE, 0.0, BuildEmaReason("EMA no trend", fastEma, slowEma, distancePoints));
      }

      return FinalizeResult(result);
   }
};

#endif
