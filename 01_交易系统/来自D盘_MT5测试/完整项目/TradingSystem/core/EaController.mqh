#ifndef EA_CONTROLLER_MQH
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
   long totalTicks;
   long newBarsDetected;
   long signalsEvaluated;
   long riskRejected;
   long riskApproved;
   long executionAttempts;
   long buySignals;
   long sellSignals;
   long noneSignals;
   long signalDirectionChanges;
   long riskRejectSignalNone;
   long riskRejectTradingDisabled;
   long riskRejectInvalidPrice;
   long riskRejectSpreadTooHigh;
   long riskRejectTimeBlocked;
   long riskRejectMaxPositions;
   long riskRejectObservationMode;
   long totalNewBarLogEvents;
   long printedNewBarLogs;
   long suppressedNewBarLogs;
   SignalDirection lastSignalDirection;
   SignalDirection previousSignalDirection;
   bool hasSignalDirection;
   long consecutiveSameDirectionSignals;
   long maxConsecutiveSameDirectionSignals;
   datetime lastBarTime;
   string lastSignalReason;
   string lastRiskRejectReason;

   void ResetRuntimeStats()
   {
      totalTicks = 0;
      newBarsDetected = 0;
      signalsEvaluated = 0;
      riskRejected = 0;
      riskApproved = 0;
      executionAttempts = 0;
      buySignals = 0;
      sellSignals = 0;
      noneSignals = 0;
      signalDirectionChanges = 0;
      riskRejectSignalNone = 0;
      riskRejectTradingDisabled = 0;
      riskRejectInvalidPrice = 0;
      riskRejectSpreadTooHigh = 0;
      riskRejectTimeBlocked = 0;
      riskRejectMaxPositions = 0;
      riskRejectObservationMode = 0;
      totalNewBarLogEvents = 0;
      printedNewBarLogs = 0;
      suppressedNewBarLogs = 0;
      lastSignalDirection = SIGNAL_NONE;
      previousSignalDirection = SIGNAL_NONE;
      hasSignalDirection = false;
      consecutiveSameDirectionSignals = 0;
      maxConsecutiveSameDirectionSignals = 0;
      lastBarTime = 0;
      lastSignalReason = "";
      lastRiskRejectReason = "";
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

   void UpdateSignalStats(const SignalResult &signal)
   {
      SignalDirection currentDirection = signal.direction;

      if(currentDirection == SIGNAL_BUY)
      {
         buySignals++;
      }
      else if(currentDirection == SIGNAL_SELL)
      {
         sellSignals++;
      }
      else if(currentDirection == SIGNAL_NONE)
      {
         noneSignals++;
      }

      if(!hasSignalDirection)
      {
         previousSignalDirection = currentDirection;
         lastSignalDirection = currentDirection;
         hasSignalDirection = true;
         consecutiveSameDirectionSignals = 1;
         maxConsecutiveSameDirectionSignals = 1;
         return;
      }

      previousSignalDirection = lastSignalDirection;

      if(currentDirection != lastSignalDirection)
      {
         signalDirectionChanges++;
         consecutiveSameDirectionSignals = 1;
      }
      else
      {
         consecutiveSameDirectionSignals++;
      }

      lastSignalDirection = currentDirection;

      if(consecutiveSameDirectionSignals > maxConsecutiveSameDirectionSignals)
      {
         maxConsecutiveSameDirectionSignals = consecutiveSameDirectionSignals;
      }
   }

   void UpdateRiskRejectStats(const RiskRejectCode rejectCode, const string rejectReason)
   {
      lastRiskRejectReason = rejectReason;

      if(rejectCode == RISK_REJECT_SIGNAL_NONE)
      {
         riskRejectSignalNone++;
      }
      else if(rejectCode == RISK_REJECT_TRADING_DISABLED)
      {
         riskRejectTradingDisabled++;
      }
      else if(rejectCode == RISK_REJECT_INVALID_PRICE)
      {
         riskRejectInvalidPrice++;
      }
      else if(rejectCode == RISK_REJECT_SPREAD_TOO_HIGH)
      {
         riskRejectSpreadTooHigh++;
      }
      else if(rejectCode == RISK_REJECT_TIME_BLOCKED)
      {
         riskRejectTimeBlocked++;
      }
      else if(rejectCode == RISK_REJECT_MAX_POSITIONS)
      {
         riskRejectMaxPositions++;
      }
      else if(rejectCode == RISK_REJECT_OBSERVATION_MODE)
      {
         riskRejectObservationMode++;
      }
   }

   string BuildStartupConfig()
   {
      return "eaName=" + InpEaName +
             ", magic=" + IntegerToString(InpMagicNumber) +
             ", enableTrading=" + logger.BoolToText(InpEnableTrading) +
             ", debugLog=" + logger.BoolToText(InpEnableDebugLog) +
             ", signalTimeframe=" + EnumToString(InpSignalTimeframe) +
             ", logEveryNTicks=" + IntegerToString(InpLogEveryNTicks) +
             ", heartbeatLog=" + logger.BoolToText(InpEnableHeartbeatLog) +
             ", newBarLog=" + logger.BoolToText(InpEnableNewBarLog) +
             ", runtimeSummary=" + logger.BoolToText(InpPrintRuntimeSummary);
   }

   void PrintRuntimeSummary()
   {
      logger.Info("CORE",
                  "Runtime summary counters",
                  "totalTicks=" + IntegerToString(totalTicks) +
                  ", newBarsDetected=" + IntegerToString(newBarsDetected) +
                  ", signalsEvaluated=" + IntegerToString(signalsEvaluated) +
                  ", riskRejected=" + IntegerToString(riskRejected) +
                  ", riskApproved=" + IntegerToString(riskApproved) +
                  ", executionAttempts=" + IntegerToString(executionAttempts));

      logger.Info("CORE",
                  "Runtime summary signal stats",
                  "buySignals=" + IntegerToString(buySignals) +
                  ", sellSignals=" + IntegerToString(sellSignals) +
                  ", noneSignals=" + IntegerToString(noneSignals) +
                  ", signalDirectionChanges=" + IntegerToString(signalDirectionChanges));

      logger.Info("CORE",
                  "Runtime summary signal state",
                  "previousSignalDirection=" + SignalDirectionToText(previousSignalDirection) +
                  ", lastSignalDirection=" + SignalDirectionToText(lastSignalDirection) +
                  ", consecutiveSameDirectionSignals=" + IntegerToString(consecutiveSameDirectionSignals) +
                  ", maxConsecutiveSameDirectionSignals=" + IntegerToString(maxConsecutiveSameDirectionSignals));

      logger.Info("CORE",
                  "Runtime summary risk stats",
                  "riskRejectSignalNone=" + IntegerToString(riskRejectSignalNone) +
                  ", riskRejectTradingDisabled=" + IntegerToString(riskRejectTradingDisabled) +
                  ", riskRejectInvalidPrice=" + IntegerToString(riskRejectInvalidPrice) +
                  ", riskRejectSpreadTooHigh=" + IntegerToString(riskRejectSpreadTooHigh) +
                  ", riskRejectTimeBlocked=" + IntegerToString(riskRejectTimeBlocked) +
                  ", riskRejectMaxPositions=" + IntegerToString(riskRejectMaxPositions) +
                  ", riskRejectObservationMode=" + IntegerToString(riskRejectObservationMode));

      if(InpPrintRiskLogStatsInSummary)
      {
         logger.Info("CORE",
                     "Runtime summary risk log stats",
                     "totalRiskRejects=" + IntegerToString(riskManager.GetTotalRiskRejects()) +
                     ", printedRiskRejectLogs=" + IntegerToString(riskManager.GetPrintedRiskRejectLogs()) +
                     ", suppressedRiskRejectLogs=" + IntegerToString(riskManager.GetSuppressedRiskRejectLogs()));
      }

      if(InpPrintCoreLogStatsInSummary)
      {
         logger.Info("CORE",
                     "Runtime summary core log stats",
                     "totalNewBarLogEvents=" + IntegerToString(totalNewBarLogEvents) +
                     ", printedNewBarLogs=" + IntegerToString(printedNewBarLogs) +
                     ", suppressedNewBarLogs=" + IntegerToString(suppressedNewBarLogs));
      }

      if(InpPrintSignalLogStatsInSummary)
      {
         logger.Info("CORE",
                     "Runtime summary signal log stats",
                     "totalSignalLogEvents=" + IntegerToString(signalEngine.GetTotalSignalLogEvents()) +
                     ", printedSignalLogs=" + IntegerToString(signalEngine.GetPrintedSignalLogs()) +
                     ", suppressedSignalLogs=" + IntegerToString(signalEngine.GetSuppressedSignalLogs()));
      }

      logger.Info("CORE", "Runtime summary last signal", lastSignalReason);
      logger.Info("CORE", "Runtime summary last risk", lastRiskRejectReason);
   }

   bool IsNewBar()
   {
      datetime currentBarTime = iTime(_Symbol, InpSignalTimeframe, 0);
      if(currentBarTime <= 0)
      {
         logger.Debug("CORE", "New bar check skipped", "No valid bar time");
         return false;
      }

      if(currentBarTime == lastBarTime)
      {
         return false;
      }

      lastBarTime = currentBarTime;
      newBarsDetected++;
      return true;
   }

   void WriteNewBarLog()
   {
      totalNewBarLogEvents++;

      if(!InpEnableNewBarLog || !InpPrintNewBarLog || InpNewBarLogEveryN <= 0)
      {
         suppressedNewBarLogs++;
         return;
      }

      if(newBarsDetected == 1)
      {
         printedNewBarLogs++;
         logger.Info("CORE",
                     "New bar detected",
                     "barTime=" + TimeToString(lastBarTime, TIME_DATE | TIME_SECONDS));
         return;
      }

      if((newBarsDetected % InpNewBarLogEveryN) == 0)
      {
         printedNewBarLogs++;
         logger.Info("CORE",
                     "New bar summary",
                     "newBarsDetected=" + IntegerToString(newBarsDetected) +
                     ", lastBarTime=" + TimeToString(lastBarTime, TIME_DATE | TIME_SECONDS) +
                     ", suppressedNewBarLogs=" + IntegerToString(suppressedNewBarLogs));
         return;
      }

      suppressedNewBarLogs++;
   }

   void WriteHeartbeat()
   {
      if(!InpEnableHeartbeatLog)
      {
         return;
      }

      if(InpLogEveryNTicks <= 0)
      {
         return;
      }

      if((totalTicks % InpLogEveryNTicks) == 0)
      {
         logger.Debug("CORE", "Tick heartbeat", "totalTicks=" + IntegerToString(totalTicks));
      }
   }

public:
   EaController()
   {
      ResetRuntimeStats();
   }

   int OnInit()
   {
      ResetRuntimeStats();

      if(!logger.Init())
      {
         return INIT_FAILED;
      }

      logger.Info("CORE", "EA starting", InpEaName);

      if(InpPrintStartupConfig)
      {
         logger.Info("CORE", "Startup config", BuildStartupConfig());
      }

      if(!signalEngine.Init(logger))
      {
         logger.Error("CORE", "Initialization failed", "SignalEngine");
         return INIT_FAILED;
      }

      if(!riskManager.Init(logger))
      {
         logger.Error("CORE", "Initialization failed", "RiskManager");
         return INIT_FAILED;
      }

      if(!executionManager.Init(logger))
      {
         logger.Error("CORE", "Initialization failed", "ExecutionManager");
         return INIT_FAILED;
      }

      logger.Info("CORE", "EA initialized", InpEaName);
      return INIT_SUCCEEDED;
   }

   void OnTick()
   {
      totalTicks++;
      WriteHeartbeat();

      if(!IsNewBar())
      {
         return;
      }

      WriteNewBarLog();

      SignalResult signal = signalEngine.Evaluate();
      signalsEvaluated++;
      UpdateSignalStats(signal);
      lastSignalReason = signal.reason;

      if(!riskManager.CanExecuteSignal(signal))
      {
         riskRejected++;
         UpdateRiskRejectStats(riskManager.GetLastRejectCode(), riskManager.GetLastRejectReason());
         return;
      }

      riskApproved++;
      executionAttempts++;
      executionManager.ExecuteSignal(signal);
   }

   void OnDeinit(const int reason)
   {
      logger.Info("CORE", "EA stopping", "reason=" + IntegerToString(reason));
      signalEngine.Deinit();

      if(InpPrintRuntimeSummary)
      {
         PrintRuntimeSummary();
      }

      logger.Info("CORE", "EA stopped", InpEaName);
   }
};

#endif
