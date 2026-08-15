#property copyright "JessieOBS"
#property version   "1.10"
#property description "Adaptive Market State Trading System"
#property description "Trend/Ranging detection + Smart strategy switching + Global risk control"
#property link      "https://github.com/jessieobs"

#include "Includes/Defines.mqh"
#include "Inputs/Parameters.mqh"
#include "Utils/Logger.mqh"
#include "Utils/TradeWrapper.mqh"
#include "Includes/StateMachine.mqh"
#include "Includes/MarketStateDetector.mqh"
#include "Includes/TrendStrategy.mqh"
#include "Includes/RangingStrategy.mqh"
#include "Includes/EntryExitManager.mqh"
#include "Includes/RiskManager.mqh"

CLogger              g_logger;
CTradeWrapper        g_trade;
CStateMachine        g_stateMachine;
CMarketStateDetector g_detector;
CTrendStrategy       g_trendStrategy;
CRangingStrategy     g_rangingStrategy;
CEntryExitManager    g_entryExit;
CRiskManager         g_riskManager;

ENUM_MARKET_STATE    g_currentState;
ENUM_MARKET_STATE    g_previousState;
SStateResult         g_lastDetection;
datetime             g_lastPositionCheck;
bool                 g_initialized;
ulong                g_lastClosedTicket;
double               g_lastClosedProfit;

int OnInit()
{
   g_initialized = false;
   g_currentState = MARKET_STATE_UNKNOWN;
   g_previousState = MARKET_STATE_UNKNOWN;
   g_lastPositionCheck = 0;
   g_lastClosedTicket = 0;
   g_lastClosedProfit = 0;
   ZeroMemory(g_lastDetection);

   g_logger.Init(InpEnableLogging, InpLogLevel, InpEnableAlert, InpEnablePushNotify);
   g_logger.Info("JessieOBS v" + EA_VERSION + " initializing...");
   g_logger.Info("Symbol: " + _Symbol + " | Timeframe: " + EnumToString(_Period));

   if(!g_trade.Initialize())
   {
      g_logger.Error("Failed to initialize trade wrapper");
      return INIT_FAILED;
   }
   g_trade.SetLogger(&g_logger);

   g_stateMachine.Init(InpStateSwitchBars, InpStateConfidenceReq);

   if(!g_detector.Init(_Symbol, _Period, InpADXPeriod, InpMAPeriod, InpATRPeriod,
                       InpADXTrendThreshold, InpADXRangeThreshold))
   {
      g_logger.Error("Failed to initialize market state detector");
      return INIT_FAILED;
   }

   if(!g_trendStrategy.Init(_Symbol, _Period, InpTrendFastEMA, InpTrendSlowEMA,
                            InpTrendSLMultiplier, InpTrendTPMultiplier,
                            InpTrendTrailStart, InpTrendTrailStep,
                            InpTrendMinADX, InpTrendCooldownBars))
   {
      g_logger.Error("Failed to initialize trend strategy");
      return INIT_FAILED;
   }

   if(!g_rangingStrategy.Init(_Symbol, _Period, InpRangeBBPeriod, InpRangeBBDeviations,
                              InpRangeRSIPeriod, InpRangeRSIOB, InpRangeRSIOS,
                              InpRangeSLMultiplier, InpRangeTPMultiplier,
                              InpRangeTrailStart, InpRangeTrailStep,
                              InpRangeCooldownBars))
   {
      g_logger.Error("Failed to initialize ranging strategy");
      return INIT_FAILED;
   }

   g_entryExit.Init(&g_trade, &g_logger, _Symbol,
                    InpRiskPercent, InpUseFixedLot, InpFixedLotSize,
                    InpMaxTrendPositions, InpMaxRangePositions, InpMaxTotalPositions);

   g_riskManager.Init(&g_trade, &g_logger, _Symbol,
                      InpMaxDailyLoss, InpMaxConsecLoss, InpMaxTotalRisk);

   g_initialized = true;
   g_logger.Info("JessieOBS initialization complete. Ready for trading.");
   g_logger.Info("Risk: " + DoubleToString(InpRiskPercent, 1) + "% | " +
                 "MaxDailyLoss: " + DoubleToString(InpMaxDailyLoss, 1) + "% | " +
                 "MaxConsLoss: " + IntegerToString(InpMaxConsecLoss));

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   g_logger.Info("JessieOBS shutting down. Reason: " + IntegerToString(reason));

   g_detector.Deinit();
   g_trendStrategy.Deinit();
   g_rangingStrategy.Deinit();

   g_logger.Info("JessieOBS shutdown complete.");
}

void OnTick()
{
   if(!g_initialized) return;

   if(!IsTradingTimeAllowed()) return;

   if(!g_riskManager.IsTradingAllowed())
   {
      if(g_riskManager.IsCircuitBreakerActive())
      {
         static datetime lastCircuitLog = 0;
         if(TimeCurrent() - lastCircuitLog > 300)
         {
            g_logger.Warn("Circuit breaker active - trading suspended");
            lastCircuitLog = TimeCurrent();
         }
      }
      return;
   }

   if(g_stateMachine.IsNewBar())
   {
      g_lastDetection = g_detector.Detect();
      g_previousState = g_currentState;
      g_stateMachine.UpdateState(g_lastDetection);
      g_currentState = g_stateMachine.GetState();

      if(g_currentState != g_previousState && g_previousState != MARKET_STATE_UNKNOWN)
      {
         g_logger.Info("MARKET STATE CHANGED: " +
            g_stateMachine.GetStateName() +
            " | Confidence: " + DoubleToString(g_lastDetection.confidence, 1) + "%" +
            " | ADX: " + DoubleToString(g_lastDetection.adxValue, 2) +
            " | TrendScore: " + DoubleToString(g_lastDetection.trendScore, 1) +
            " | RangeScore: " + DoubleToString(g_lastDetection.rangeScore, 1));

         g_entryExit.ManagePositionHandover(g_previousState, g_currentState);
      }

   }

   if(g_currentState == MARKET_STATE_UNKNOWN) return;

   ProcessTradeSignals();
   ManageExistingPositions();
   CheckClosedPositions();
}

void ProcessTradeSignals()
{
   STradeSignal signal;
   ZeroMemory(signal);

   if(g_currentState == MARKET_STATE_TRENDING)
   {
      signal = g_trendStrategy.GenerateSignal();
   }
   else if(g_currentState == MARKET_STATE_RANGING)
   {
      signal = g_rangingStrategy.GenerateSignal();
   }

   if(signal.isValid)
   {
      if(g_entryExit.ExecuteSignal(signal))
      {
         if(g_currentState == MARKET_STATE_TRENDING)
            g_trendStrategy.OnTradeOpened();
         else
            g_rangingStrategy.OnTradeOpened();
      }
   }
}

void ManageExistingPositions()
{
   g_entryExit.ManageTrailingStops(g_currentState == MARKET_STATE_TRENDING);
}

void CheckClosedPositions()
{
   static int lastTotal = 0;
   int currentTotal = PositionsTotal();

   if(currentTotal < lastTotal)
   {
      HistorySelect(TimeCurrent() - 86400, TimeCurrent());
      int dealsTotal = HistoryDealsTotal();

      for(int i = dealsTotal - 1; i >= MathMax(0, dealsTotal - 5); i--)
      {
         ulong dealTicket = HistoryDealGetTicket(i);
         if(dealTicket <= 0) continue;
         if(dealTicket == g_lastClosedTicket) continue;

         if(HistoryDealGetInteger(dealTicket, DEAL_ENTRY) == DEAL_ENTRY_OUT ||
            HistoryDealGetInteger(dealTicket, DEAL_ENTRY) == DEAL_ENTRY_OUT_BY)
         {
            if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) != _Symbol) continue;
            if(HistoryDealGetInteger(dealTicket, DEAL_MAGIC) != EA_MAGIC_NUMBER) continue;

            double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT) +
                           HistoryDealGetDouble(dealTicket, DEAL_COMMISSION) +
                           HistoryDealGetDouble(dealTicket, DEAL_SWAP);

            g_lastClosedTicket = dealTicket;
            g_riskManager.OnTradeClosed(profit);

            g_logger.Info("Position outcome | Profit=" + DoubleToString(profit, 2) +
               " | ConsecLoss=" + IntegerToString(g_riskManager.GetConsecutiveLosses()));
         }
      }
   }
   lastTotal = currentTotal;
}

bool IsTradingTimeAllowed()
{
   if(!InpUseTimeFilter) return true;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   if(InpAvoidFridayClose && dt.day_of_week == 5 && dt.hour >= InpFridayStopHour)
   {
      static datetime lastFriLog = 0;
      if(TimeCurrent() - lastFriLog > 300)
      {
         g_logger.Info("Friday close restriction active");
         lastFriLog = TimeCurrent();
      }
      return false;
   }

   if(InpStartHour < InpEndHour)
   {
      if(dt.hour < InpStartHour || dt.hour >= InpEndHour)
         return false;
   }
   else
   {
      if(dt.hour < InpStartHour && dt.hour >= InpEndHour)
         return false;
   }

   return true;
}

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest&     request,
                        const MqlTradeResult&      result)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(trans.deal_type == DEAL_TYPE_SELL || trans.deal_type == DEAL_TYPE_BUY)
      {
         if(HistoryDealSelect(trans.deal))
         {
            ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
            if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
            {
               if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) == _Symbol &&
                  HistoryDealGetInteger(trans.deal, DEAL_MAGIC) == EA_MAGIC_NUMBER)
               {
                  double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT) +
                                 HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) +
                                 HistoryDealGetDouble(trans.deal, DEAL_SWAP);

                  if(trans.deal != g_lastClosedTicket)
                  {
                     g_lastClosedTicket = trans.deal;
                     g_lastClosedProfit = profit;
                  }
               }
            }
         }
      }
   }

   if(trans.type == TRADE_TRANSACTION_REQUEST)
   {
      if(result.retcode != 10009 && result.retcode != 0)
      {
         g_logger.Warn("Trade request result: " + IntegerToString(result.retcode));
      }
   }
}

double OnTester()
{
   double profitFactor   = TesterStatistics(STAT_PROFIT_FACTOR);
   double recoveryFactor = TesterStatistics(STAT_RECOVERY_FACTOR);
   double sharpeRatio    = TesterStatistics(STAT_SHARPE_RATIO);
   double maxDrawdown    = TesterStatistics(STAT_BALANCE_DD_RELATIVE);
   double totalTrades    = TesterStatistics(STAT_TRADES);
   double winRate = TesterStatistics(STAT_PROFIT_TRADES) / MathMax(1, totalTrades) * 100.0;

   double customScore = profitFactor * 0.3 +
                        recoveryFactor * 0.2 +
                        sharpeRatio * 3.0 * 0.15 +
                        (100.0 - MathMin(100, maxDrawdown)) * 0.004 * 0.15 +
                        winRate / 100.0 * 0.2;

   return customScore;
}
