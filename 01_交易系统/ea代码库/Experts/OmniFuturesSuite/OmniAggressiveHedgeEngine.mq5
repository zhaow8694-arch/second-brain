#property copyright "Omni Futures Suite"
#property version   "1.00"
#property strict

#include "Include/OmniTypes.mqh"

input group "=== Core ==="
input bool   InpEnableTrading = true;
input ulong  InpMagicNumber = 26061502;
input int    InpTimerSeconds = 30;
input bool   InpOptimizationMode = false;
input ENUM_OMNI_PRODUCT InpOptimizationProduct = OMNI_GOLD;

input group "=== Symbols ==="
input string InpGoldSymbol = "XAUUSD.c";
input string InpSPX500Symbol = "SPX500.c";
input string InpA50Symbol = "A50.c";
input string InpUSOILSymbol = "USOIL.c";

input group "=== Account Scaling ==="
input ENUM_OMNI_ACCOUNT_SCALE InpAccountScaleMode = OMNI_SCALE_AUTO;
input double InpCustomAccountScale = 1.0;

input group "=== Risk ==="
input double InpMaxTotalDrawdownPct = 50.0;
input double InpMaxDailyLossPct = 9.0;
input double InpMaxGlobalRiskPct = 18.0;
input int    InpMaxActiveProducts = 4;
input int    InpMaxPositionsPerSymbol = 5;
input double InpRiskMultiplier = 1.0;

input group "=== Aggressive Controls ==="
input bool   InpEnableAddOn = true;
input int    InpMaxAddOnLayers = 3;
input bool   InpEnableProtectiveHedge = true;
input int    InpMaxHedgeLayers = 1;

input group "=== Time Management ==="
input bool   InpCloseOnFriday = true;
input int    InpFridayCloseHour = 21;
input int    InpFridayCloseMinute = 30;
input int    InpRangeForceCloseHour = 22;
input int    InpRangeForceCloseMinute = 30;

input group "=== Execution ==="
input int    InpSlippagePoints = 35;

input group "=== Notifications ==="
input bool   InpEnablePushNotifications = true;
input bool   InpVerboseLog = true;
input string InpPushPrefix = "OmniAggressive";
input int    InpDailyReportHour = 11;

#include "Include/AccountScale.mqh"
#include "Include/SymbolResolver.mqh"
#include "Include/NotificationCenter.mqh"
#include "Include/RiskManager.mqh"
#include "Include/TradeExecutor.mqh"
#include "Include/MarketRegime.mqh"
#include "Include/PositionManager.mqh"
#include "Include/EntryGuard.mqh"
#include "Include/AggressiveStrategy.mqh"

SOmniSymbol g_symbols[];
COmniMarketRegime g_market[];
COmniAccountScale g_account;
COmniSymbolResolver g_resolver;
COmniNotificationCenter g_notify;
COmniRiskManager g_risk;
COmniTradeExecutor g_trade;
COmniPositionManager g_positions;
COmniEntryGuard g_entryGuard;
COmniAggressiveStrategy g_strategy;
bool g_hedgingAccount = false;

bool IsProductEnabled(const int index)
{
   if(index < 0 || index >= ArraySize(g_symbols)) return false;
   if(!g_symbols[index].enabled) return false;
   if(!InpOptimizationMode) return true;
   return (g_symbols[index].product == InpOptimizationProduct ||
           g_symbols[index].resolvedSymbol == _Symbol);
}

bool InitializeMarkets()
{
   ArrayResize(g_market, ArraySize(g_symbols));
   bool any = false;
   for(int i = 0; i < ArraySize(g_symbols); i++)
   {
      if(!g_symbols[i].enabled)
      {
         g_notify.Warn(g_symbols[i].logicalName + " disabled: " + g_symbols[i].disabledReason);
         continue;
      }

      if(!g_market[i].Init(g_symbols[i].resolvedSymbol, g_symbols[i].profile))
      {
         g_symbols[i].enabled = false;
         g_symbols[i].disabledReason = "indicator handle initialization failed";
         g_notify.Warn(g_symbols[i].logicalName + " disabled: " + g_symbols[i].disabledReason);
         continue;
      }

      any = true;
      g_notify.Info("Resolved " + g_symbols[i].logicalName + " => " + g_symbols[i].resolvedSymbol);
   }
   return any;
}

bool BuildStops(const SOmniSignal &signal,
                const SOmniMarketSnapshot &snapshot,
                double &entry,
                double &sl,
                double &tp)
{
   if(snapshot.h1Atr <= 0.0) return false;
   bool buy = OmniIsBuySignal(signal.type);
   entry = buy ? snapshot.ask : snapshot.bid;
   if(entry <= 0.0) return false;

   sl = buy ? entry - snapshot.h1Atr * signal.slAtr
            : entry + snapshot.h1Atr * signal.slAtr;
   tp = buy ? entry + snapshot.h1Atr * signal.tpAtr
            : entry - snapshot.h1Atr * signal.tpAtr;

   int digits = (int)SymbolInfoInteger(signal.symbol, SYMBOL_DIGITS);
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);
   return true;
}

bool ExecuteSignal(const SOmniSymbol &item,
                   const SOmniMarketSnapshot &snapshot,
                   SOmniSignal &signal)
{
   if(!InpEnableTrading)
   {
      g_notify.Info("Trading disabled. Signal skipped: " + signal.reason);
      return false;
   }

   SOmniRiskDecision decision;
   if(!g_risk.CanOpen(item, snapshot, signal, InpMagicNumber, decision))
   {
      g_notify.Info(item.logicalName + " rejected: " + decision.reason + " | " + signal.reason);
      return false;
   }

   double entry, sl, tp;
   if(!BuildStops(signal, snapshot, entry, sl, tp))
   {
      g_notify.Warn(item.logicalName + " rejected: cannot build stops");
      return false;
   }

   double riskMoneyBroker = 0.0;
   string volumeReason = "";
   double volume = g_risk.CalculateVolume(signal.symbol,
                                          signal.type,
                                          entry,
                                          sl,
                                          signal.riskPct,
                                          riskMoneyBroker,
                                          volumeReason);
   volume = g_trade.NormalizeVolume(signal.symbol, volume);
   if(volume <= 0.0)
   {
      g_notify.Info(item.logicalName + " rejected: " + volumeReason);
      return false;
   }

   if(signal.isHedge)
      volume = g_trade.NormalizeVolume(signal.symbol, volume * 0.80);

   signal.comment = signal.comment + " " + DoubleToString(signal.confidence, 0);
   return g_trade.OpenMarket(signal, volume, sl, tp);
}

void ManagePositions()
{
   for(int i = 0; i < ArraySize(g_symbols); i++)
   {
      if(!IsProductEnabled(i)) continue;
      SOmniMarketSnapshot snapshot;
      if(!g_market[i].Refresh(snapshot)) continue;
      g_positions.Manage(g_symbols[i],
                         snapshot,
                         InpCloseOnFriday,
                         InpFridayCloseHour,
                         InpFridayCloseMinute,
                         InpRangeForceCloseHour,
                         InpRangeForceCloseMinute);
   }
}

void SendDailyReport()
{
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   if(now.hour != InpDailyReportHour) return;

   string text = "equityEffective=" + DoubleToString(g_account.EffectiveEquity(), 2) +
                 ", balanceEffective=" + DoubleToString(g_account.EffectiveBalance(), 2) +
                 ", hardStop=" + (g_risk.IsHardStopped() ? "true" : "false") +
                 ", hedgeAccount=" + (g_hedgingAccount ? "true" : "false");
   g_notify.Daily(text);
}

bool EntryGuardAllowsSignal(const int index,
                            const SOmniMarketSnapshot &snapshot,
                            const SOmniSignal &signal)
{
   string reason = "";
   if(signal.isRange &&
      g_entryGuard.ShouldBlockRangeNewEntry(InpRangeForceCloseHour,
                                            InpRangeForceCloseMinute,
                                            reason))
   {
      if(InpVerboseLog)
         g_notify.Info(g_symbols[index].logicalName + " skipped: " + reason);
      return false;
   }

   if(!signal.isAddOn && !signal.isHedge &&
      !g_entryGuard.AllowInitialEntry(signal.product, snapshot.h1BarTime, reason))
   {
      if(InpVerboseLog)
         g_notify.Info(g_symbols[index].logicalName + " skipped: " + reason);
      return false;
   }

   return true;
}

void ScanSignals()
{
   string entryBlockReason = "";
   if(g_entryGuard.ShouldBlockAllNewEntries(InpCloseOnFriday,
                                            InpFridayCloseHour,
                                            InpFridayCloseMinute,
                                            entryBlockReason))
   {
      if(InpVerboseLog)
         g_notify.Info("New entries paused: " + entryBlockReason);
      return;
   }

   bool allowHedge = (InpEnableProtectiveHedge && g_hedgingAccount && InpMaxHedgeLayers > 0);

   for(int i = 0; i < ArraySize(g_symbols); i++)
   {
      if(!IsProductEnabled(i)) continue;

      SOmniMarketSnapshot snapshot;
      if(!g_market[i].Refresh(snapshot))
      {
         g_notify.Info(g_symbols[i].logicalName + " market unavailable: " + snapshot.reason);
         continue;
      }

      SOmniExposure exposure;
      g_positions.GetExposure(g_symbols[i].resolvedSymbol, exposure);

      SOmniSignal signal;
      double riskPct = g_risk.AdaptiveRiskPct(true) * InpRiskMultiplier;
      if(!g_strategy.BuildSignal(g_symbols[i],
                                 snapshot,
                                 exposure,
                                 riskPct,
                                 InpEnableAddOn,
                                 allowHedge,
                                 InpMaxAddOnLayers,
                                 signal))
      {
         if(InpVerboseLog)
            g_notify.Info(g_symbols[i].logicalName + ": " + signal.reason);
         continue;
      }

      if(!EntryGuardAllowsSignal(i, snapshot, signal))
         continue;

      if(ExecuteSignal(g_symbols[i], snapshot, signal) &&
         !signal.isAddOn &&
         !signal.isHedge)
      {
         g_entryGuard.MarkInitialEntry(signal.product, snapshot.h1BarTime);
      }
   }
}

int OnInit()
{
   g_notify.Init(InpEnablePushNotifications, InpPushPrefix, InpVerboseLog);
   g_account.Init(InpAccountScaleMode, InpCustomAccountScale);
   g_hedgingAccount = (AccountInfoInteger(ACCOUNT_MARGIN_MODE) == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);
   g_notify.Info("Starting OmniAggressiveHedgeEngine. " + g_account.Summary());
   if(!g_hedgingAccount)
      g_notify.Warn("Account is not hedging mode. Protective hedge disabled.");

   if(!g_resolver.ResolveAll(g_symbols, InpGoldSymbol, InpSPX500Symbol, InpA50Symbol, InpUSOILSymbol))
      return INIT_FAILED;

   if(!InitializeMarkets())
      return INIT_FAILED;

   g_risk.Init(g_account, g_notify, InpMaxTotalDrawdownPct, InpMaxDailyLossPct,
               InpMaxGlobalRiskPct, InpMaxActiveProducts, InpMaxPositionsPerSymbol);
   g_trade.Init(InpMagicNumber, InpSlippagePoints, g_notify);
   g_positions.Init(InpMagicNumber, g_trade, g_notify);
   g_entryGuard.Reset();

   EventSetTimer(InpTimerSeconds);
   ScanSignals();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   for(int i = 0; i < ArraySize(g_market); i++)
      g_market[i].Deinit();
   g_notify.Info("OmniAggressiveHedgeEngine stopped. reason=" + IntegerToString(reason));
}

void OnTick()
{
   ManagePositions();
}

void OnTimer()
{
   ManagePositions();
   ScanSignals();
   SendDailyReport();
}
