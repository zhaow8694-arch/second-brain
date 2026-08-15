#ifndef RISK_MANAGER_MQH
#define RISK_MANAGER_MQH

#include "../config/InputConfig.mqh"
#include "../logger/Logger.mqh"
#include "../signals/SignalEngine.mqh"

enum RiskRejectCode
{
   RISK_REJECT_NONE = 0,
   RISK_REJECT_SIGNAL_NONE,
   RISK_REJECT_TRADING_DISABLED,
   RISK_REJECT_INVALID_PRICE,
   RISK_REJECT_SPREAD_TOO_HIGH,
   RISK_REJECT_TIME_BLOCKED,
   RISK_REJECT_MAX_POSITIONS,
   RISK_REJECT_OBSERVATION_MODE
};

class RiskManager
{
private:
   Logger *logger;
   string lastRejectReason;
   RiskRejectCode lastRejectCode;
   int totalRiskRejects;
   int printedRiskRejectLogs;
   int suppressedRiskRejectLogs;
   string lastLoggedRejectReason;
   int sameReasonRejectCount;

   string RejectCodeToText(const RiskRejectCode code)
   {
      if(code == RISK_REJECT_SIGNAL_NONE)
      {
         return "RISK_REJECT_SIGNAL_NONE";
      }

      if(code == RISK_REJECT_TRADING_DISABLED)
      {
         return "RISK_REJECT_TRADING_DISABLED";
      }

      if(code == RISK_REJECT_INVALID_PRICE)
      {
         return "RISK_REJECT_INVALID_PRICE";
      }

      if(code == RISK_REJECT_SPREAD_TOO_HIGH)
      {
         return "RISK_REJECT_SPREAD_TOO_HIGH";
      }

      if(code == RISK_REJECT_TIME_BLOCKED)
      {
         return "RISK_REJECT_TIME_BLOCKED";
      }

      if(code == RISK_REJECT_MAX_POSITIONS)
      {
         return "RISK_REJECT_MAX_POSITIONS";
      }

      if(code == RISK_REJECT_OBSERVATION_MODE)
      {
         return "RISK_REJECT_OBSERVATION_MODE";
      }

      return "RISK_REJECT_NONE";
   }

   void WriteRiskRejectLog(const string eventName, const string detail)
   {
      if(logger != NULL)
      {
         logger.Warning("RISK", eventName, detail);
      }
   }

   void UpdateSameReasonCount(const string reason)
   {
      if(reason == lastRejectReason)
      {
         sameReasonRejectCount++;
      }
      else
      {
         sameReasonRejectCount = 1;
      }
   }

   void Reject(const RiskRejectCode code, const string reason, const string detail)
   {
      UpdateSameReasonCount(reason);
      lastRejectReason = reason;
      lastRejectCode = code;
      totalRiskRejects++;

      bool shouldPrint = false;
      bool summaryLog = false;

      if(!InpPrintRiskObservationLog || !InpPrintRiskRejectLog)
      {
         suppressedRiskRejectLogs++;
         return;
      }

      if(InpPrintRiskRejectOnlyOnReasonChange)
      {
         if(reason != lastLoggedRejectReason)
         {
            shouldPrint = true;
         }
         else if(InpRiskRejectLogEveryN > 0 && (sameReasonRejectCount % InpRiskRejectLogEveryN) == 0)
         {
            shouldPrint = true;
            summaryLog = true;
         }
      }
      else
      {
         if(InpRiskRejectLogEveryN <= 0 || sameReasonRejectCount == 1 || (sameReasonRejectCount % InpRiskRejectLogEveryN) == 0)
         {
            shouldPrint = true;
            summaryLog = (sameReasonRejectCount > 1);
         }
      }

      if(shouldPrint)
      {
         printedRiskRejectLogs++;
         lastLoggedRejectReason = reason;

         if(summaryLog)
         {
            WriteRiskRejectLog("Risk rejected summary",
                               "reason=" + reason +
                               ", code=" + RejectCodeToText(code) +
                               ", sameReasonRejectCount=" + IntegerToString(sameReasonRejectCount));
         }
         else
         {
            WriteRiskRejectLog("Risk rejected signal",
                               reason + " | code=" + RejectCodeToText(code) + " | " + detail);
         }

         return;
      }

      suppressedRiskRejectLogs++;
   }

   void PrintAccountState()
   {
      if(logger == NULL || !InpPrintAccountStateOnInit)
      {
         return;
      }

      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      double margin = AccountInfoDouble(ACCOUNT_MARGIN);
      double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      long leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);

      logger.Info("RISK",
                  "Account state",
                  "balance=" + DoubleToString(balance, 2) +
                  ", equity=" + DoubleToString(equity, 2) +
                  ", margin=" + DoubleToString(margin, 2) +
                  ", freeMargin=" + DoubleToString(freeMargin, 2) +
                  ", leverage=" + IntegerToString(leverage));
   }

   bool CheckSpread()
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

      if(ask <= 0.0 || bid <= 0.0 || _Point <= 0.0 || ask < bid)
      {
         Reject(RISK_REJECT_INVALID_PRICE,
                "Invalid bid/ask",
                "ask=" + DoubleToString(ask, _Digits) +
                ", bid=" + DoubleToString(bid, _Digits));
         return false;
      }

      double spreadPoints = (ask - bid) / _Point;
      if(spreadPoints > InpMaxSpreadPoints)
      {
         Reject(RISK_REJECT_SPREAD_TOO_HIGH,
                "Spread too high",
                "spreadPoints=" + DoubleToString(spreadPoints, 2) +
                ", maxSpreadPoints=" + DoubleToString(InpMaxSpreadPoints, 2));
         return false;
      }

      return true;
   }

   bool IsTradingHourAllowed(const int currentHour)
   {
      int startHour = InpTradingStartHour;
      int endHour = InpTradingEndHour;

      if(startHour < 0 || startHour > 23 || endHour < 0 || endHour > 23)
      {
         return false;
      }

      if(startHour <= endHour)
      {
         return (currentHour >= startHour && currentHour <= endHour);
      }

      return (currentHour >= startHour || currentHour <= endHour);
   }

   bool CheckTradingTime()
   {
      if(!InpEnableTradingTimeFilter)
      {
         return true;
      }

      MqlDateTime currentTime;
      TimeToStruct(TimeCurrent(), currentTime);
      int currentHour = currentTime.hour;

      if(!IsTradingHourAllowed(currentHour))
      {
         Reject(RISK_REJECT_TIME_BLOCKED,
                "Trading time blocked",
                "currentHour=" + IntegerToString(currentHour) +
                ", startHour=" + IntegerToString(InpTradingStartHour) +
                ", endHour=" + IntegerToString(InpTradingEndHour));
         return false;
      }

      return true;
   }

   int CountCurrentSymbolPositions()
   {
      int count = 0;
      int total = PositionsTotal();

      for(int i = 0; i < total; i++)
      {
         string positionSymbol = PositionGetSymbol(i);
         if(positionSymbol == _Symbol)
         {
            count++;
         }
      }

      return count;
   }

   bool CheckMaxOpenPositions()
   {
      int currentSymbolPositions = CountCurrentSymbolPositions();

      if(currentSymbolPositions >= InpMaxOpenPositions)
      {
         Reject(RISK_REJECT_MAX_POSITIONS,
                "Max open positions reached",
                "currentSymbolPositions=" + IntegerToString(currentSymbolPositions) +
                ", maxOpenPositions=" + IntegerToString(InpMaxOpenPositions));
         return false;
      }

      return true;
   }

public:
   RiskManager()
   {
      logger = NULL;
      lastRejectReason = "";
      lastRejectCode = RISK_REJECT_NONE;
      totalRiskRejects = 0;
      printedRiskRejectLogs = 0;
      suppressedRiskRejectLogs = 0;
      lastLoggedRejectReason = "";
      sameReasonRejectCount = 0;
   }

   bool Init(Logger &log)
   {
      logger = &log;
      logger.Info("RISK", "RiskManager initialized", "Risk observation mode blocks all real trading");
      PrintAccountState();
      return true;
   }

   string GetLastRejectReason()
   {
      return lastRejectReason;
   }

   RiskRejectCode GetLastRejectCode()
   {
      return lastRejectCode;
   }

   string GetLastRejectCodeText()
   {
      return RejectCodeToText(lastRejectCode);
   }

   int GetTotalRiskRejects()
   {
      return totalRiskRejects;
   }

   int GetPrintedRiskRejectLogs()
   {
      return printedRiskRejectLogs;
   }

   int GetSuppressedRiskRejectLogs()
   {
      return suppressedRiskRejectLogs;
   }

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

   bool CanExecuteSignal(const SignalResult &signal)
   {
      if(signal.direction == SIGNAL_NONE)
      {
         Reject(RISK_REJECT_SIGNAL_NONE, "Signal direction is NONE", "reason=" + signal.reason);
         return false;
      }

      if(InpEnableRiskObservation)
      {
         if(!CheckSpread())
         {
            return false;
         }

         if(!CheckTradingTime())
         {
            return false;
         }

         if(!CheckMaxOpenPositions())
         {
            return false;
         }
      }

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

#endif
