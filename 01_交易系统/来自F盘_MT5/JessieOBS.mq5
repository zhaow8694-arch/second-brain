#property strict
#property version   "1.10"
#property description "JessieOBS adaptive market-state EA"

#include "Inputs/Parameters.mqh"
#include "Includes/Defines.mqh"
#include "Utils/Logger.mqh"
#include "Utils/TradeWrapper.mqh"
#include "Includes/MarketStateDetector.mqh"
#include "Includes/StateMachine.mqh"
#include "Includes/TrendStrategy.mqh"
#include "Includes/RangingStrategy.mqh"
#include "Includes/EntryExitManager.mqh"
#include "Includes/RiskManager.mqh"

CLogger              g_logger;
CTradeWrapper        g_trade;
CMarketStateDetector g_detector;
CStateMachine        g_state_machine;
CTrendStrategy       g_trend_strategy;
CRangingStrategy     g_ranging_strategy;
CEntryExitManager    g_entry_exit;
CRiskManager         g_risk_manager;

MarketDecision       g_last_decision;
bool                 g_ready = false;

int OnInit()
{
   g_logger.Init("JessieOBS");
   g_logger.Write(LOG_LEVEL_INFO, "Initializing JessieOBS v1.10");

   if(!g_trade.Init(InpMagicNumber, InpDeviationPoints, g_logger))
      return INIT_FAILED;

   if(!g_detector.Init(_Symbol, InpStateTimeframe, InpADXPeriod, InpMAPeriod, InpATRPeriod, g_logger))
      return INIT_FAILED;

   if(!g_trend_strategy.Init(_Symbol, InpStateTimeframe, InpTrendFastEMA, InpTrendSlowEMA, g_logger))
      return INIT_FAILED;

   if(!g_ranging_strategy.Init(_Symbol, InpStateTimeframe, InpRangeRSIPeriod,
                               InpRangeBandsPeriod, InpRangeBandsDeviation, g_logger))
      return INIT_FAILED;

   g_state_machine.Init(g_logger);
   g_entry_exit.Init(_Symbol, InpMagicNumber, g_trade, g_logger);
   g_risk_manager.Init(_Symbol, InpMagicNumber, g_logger);

   g_last_decision.state = MARKET_STATE_UNKNOWN;
   g_last_decision.confidence = 0.0;
   g_last_decision.adx = 0.0;
   g_last_decision.ma = 0.0;
   g_last_decision.atr = 0.0;
   g_last_decision.close_price = 0.0;

   g_ready = true;
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   g_detector.Deinit();
   g_trend_strategy.Deinit();
   g_ranging_strategy.Deinit();
   g_logger.Write(LOG_LEVEL_INFO, StringFormat("Deinitialized, reason=%d", reason));
}

void OnTick()
{
   if(!g_ready)
      return;

   if(IsSpreadTooWide())
      return;

   const bool stopped = g_risk_manager.CheckCircuitBreaker(InpDailyMaxDrawdownPercent,
                                                           InpMaxConsecutiveLosses,
                                                           InpMinEquityPercent);
   if(stopped)
   {
      if(InpCloseAllOnCircuitBreaker)
         g_entry_exit.CloseAll();
      return;
   }

   bool new_bar = false;
   if(g_detector.IsNewBar())
   {
      new_bar = true;
      MarketDecision decision;
      if(g_detector.Detect(decision, InpTrendADXThreshold, InpRangeADXThreshold))
      {
         g_last_decision = decision;
         const bool switched = g_state_machine.Update(decision, InpMinSwitchConfidence, InpMinSwitchBars);
         if(switched)
            g_entry_exit.ManageOpenPositions(g_state_machine.CurrentState(),
                                             InpTrendTrail_ATR,
                                             InpRangeSL_ATR,
                                             InpBreakEven_ATR,
                                             decision.atr);
      }
   }

   const MarketState active_state = g_state_machine.CurrentState();
   const double atr = g_last_decision.atr;
   if(active_state == MARKET_STATE_UNKNOWN || atr <= 0.0)
      return;

   g_entry_exit.ManageOpenPositions(active_state, InpTrendTrail_ATR, InpRangeSL_ATR, InpBreakEven_ATR, atr);

   if(!new_bar || !InpAllowNewTrades || g_entry_exit.HasOpenPosition())
      return;

   StrategySignal signal;
   if(active_state == MARKET_STATE_TRENDING)
   {
      if(g_trend_strategy.Evaluate(atr, InpTrendSL_ATR, InpTrendTP_ATR, signal) &&
         signal.signal != TRADE_SIGNAL_NONE)
         g_entry_exit.ExecuteSignal(signal, InpTrendRiskPercent,
                                    InpMaxSymbolExposurePercent,
                                    InpMaxTotalExposurePercent,
                                    "JessieOBS_TREND");
   }
   else if(active_state == MARKET_STATE_RANGING)
   {
      if(g_ranging_strategy.Evaluate(atr, InpRangeSL_ATR, InpRangeTP_ATR,
                                     InpRSIBuyLevel, InpRSISellLevel, signal) &&
         signal.signal != TRADE_SIGNAL_NONE)
         g_entry_exit.ExecuteSignal(signal, InpRangeRiskPercent,
                                    InpMaxSymbolExposurePercent,
                                    InpMaxTotalExposurePercent,
                                    "JessieOBS_RANGE");
   }
}

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   g_risk_manager.OnTradeTransaction(trans);
}

bool IsSpreadTooWide()
{
   const long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   return (spread > InpMaxSpreadPoints);
}
