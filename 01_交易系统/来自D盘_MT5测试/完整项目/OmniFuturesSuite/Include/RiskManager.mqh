#ifndef RISK_MANAGER_MQH
#define RISK_MANAGER_MQH

#include "OmniTypes.mqh"
#include "AccountScale.mqh"
#include "NotificationCenter.mqh"

class COmniRiskManager
{
private:
   COmniAccountScale *account;
   COmniNotificationCenter *notify;
   double maxTotalDrawdownPct;
   double maxDailyLossPct;
   double maxGlobalRiskPct;
   int maxActiveProducts;
   int maxPositionsPerSymbol;
   double startEquityEffective;
   double dayStartEquityEffective;
   int trackedDayOfYear;
   bool hardStop;

   int DayOfYear()
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);
      return now.day_of_year;
   }

   bool TradingAllowed()
   {
      if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
      if(!MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
      if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
      return true;
   }

   bool SymbolTradeSessionOpen(const string symbol)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);
      int nowSeconds = now.hour * 3600 + now.min * 60 + now.sec;
      ENUM_DAY_OF_WEEK day = (ENUM_DAY_OF_WEEK)now.day_of_week;
      bool hasSessions = false;

      for(uint session = 0; session < 20; session++)
      {
         datetime fromTime = 0;
         datetime toTime = 0;
         if(!SymbolInfoSessionTrade(symbol, day, session, fromTime, toTime))
            break;

         hasSessions = true;
         int fromSeconds = (int)fromTime;
         int toSeconds = (int)toTime;

         if(fromSeconds == toSeconds)
            return true;

         if(toSeconds > fromSeconds)
         {
            if(nowSeconds >= fromSeconds && nowSeconds < toSeconds)
               return true;
         }
         else
         {
            if(nowSeconds >= fromSeconds || nowSeconds < toSeconds)
               return true;
         }
      }

      return !hasSessions;
   }

   int CountActiveProducts(const ulong magic)
   {
      bool active[OMNI_PRODUCT_COUNT];
      ArrayInitialize(active, false);
      int count = 0;

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
         if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;
         string comment = PositionGetString(POSITION_COMMENT);
         for(int p = 0; p < OMNI_PRODUCT_COUNT; p++)
         {
            if(StringFind(comment, OmniProductName((ENUM_OMNI_PRODUCT)p)) >= 0)
               active[p] = true;
         }
      }

      for(int p = 0; p < OMNI_PRODUCT_COUNT; p++)
         if(active[p]) count++;

      return count;
   }

public:
   COmniRiskManager()
   {
      account = NULL;
      notify = NULL;
      maxTotalDrawdownPct = 20.0;
      maxDailyLossPct = 4.0;
      maxGlobalRiskPct = 8.0;
      maxActiveProducts = 2;
      maxPositionsPerSymbol = 2;
      startEquityEffective = 0.0;
      dayStartEquityEffective = 0.0;
      trackedDayOfYear = -1;
      hardStop = false;
   }

   bool Init(COmniAccountScale &accountScale,
             COmniNotificationCenter &notificationCenter,
             const double totalDrawdownPct,
             const double dailyLossPct,
             const double globalRiskPct,
             const int activeProducts,
             const int positionsPerSymbol)
   {
      account = &accountScale;
      notify = &notificationCenter;
      maxTotalDrawdownPct = totalDrawdownPct;
      maxDailyLossPct = dailyLossPct;
      maxGlobalRiskPct = globalRiskPct;
      maxActiveProducts = activeProducts;
      maxPositionsPerSymbol = positionsPerSymbol;
      startEquityEffective = account.EffectiveEquity();
      dayStartEquityEffective = startEquityEffective;
      trackedDayOfYear = DayOfYear();
      hardStop = false;
      return true;
   }

   void RefreshDay()
   {
      int today = DayOfYear();
      if(today != trackedDayOfYear)
      {
         trackedDayOfYear = today;
         dayStartEquityEffective = account.EffectiveEquity();
         hardStop = false;
         if(notify != NULL)
            notify.Info("New trading day. Day start effective equity=" +
                        DoubleToString(dayStartEquityEffective, 2));
      }
   }

   double AdaptiveRiskPct(const bool aggressive)
   {
      double balance = account.EffectiveBalance();
      if(balance < 500.0)
         return aggressive ? 0.45 : 0.30;
      if(balance < 2000.0)
         return aggressive ? 0.60 : 0.45;
      if(balance < 10000.0)
         return aggressive ? 0.80 : 0.60;
      return aggressive ? 0.70 : 0.50;
   }

   bool IsHardStopped()
   {
      return hardStop;
   }

   bool CheckAccountLimits(string &reason)
   {
      RefreshDay();
      if(hardStop)
      {
         reason = "hard stop active";
         return false;
      }

      if(!TradingAllowed())
      {
         reason = "terminal, MQL, or account trading is disabled";
         return false;
      }

      double equity = account.EffectiveEquity();
      if(startEquityEffective > 0.0)
      {
         double totalDd = 100.0 * (startEquityEffective - equity) / startEquityEffective;
         if(totalDd >= maxTotalDrawdownPct)
         {
            hardStop = true;
            reason = "total drawdown hard stop " + DoubleToString(totalDd, 2) + "%";
            if(notify != NULL) notify.Warn(reason);
            return false;
         }
      }

      if(dayStartEquityEffective > 0.0)
      {
         double dailyLoss = 100.0 * (dayStartEquityEffective - equity) / dayStartEquityEffective;
         if(dailyLoss >= maxDailyLossPct)
         {
            hardStop = true;
            reason = "daily loss hard stop " + DoubleToString(dailyLoss, 2) + "%";
            if(notify != NULL) notify.Warn(reason);
            return false;
         }
      }

      reason = "ok";
      return true;
   }

   bool CanOpen(const SOmniSymbol &item,
                const SOmniMarketSnapshot &snapshot,
                const SOmniSignal &signal,
                const ulong magic,
                SOmniRiskDecision &decision)
   {
      decision.allowed = false;
      decision.reason = "";
      decision.volume = 0.0;
      decision.riskMoneyBroker = 0.0;
      decision.effectiveRiskPct = signal.riskPct;

      string accountReason;
      if(!CheckAccountLimits(accountReason))
      {
         decision.reason = accountReason;
         return false;
      }

      if(!item.enabled)
      {
         decision.reason = item.disabledReason;
         return false;
      }

      if(signal.type == OMNI_SIGNAL_NONE)
      {
         decision.reason = "no signal";
         return false;
      }

      if(!SymbolTradeSessionOpen(item.resolvedSymbol))
      {
         decision.reason = "symbol trade session closed";
         return false;
      }

      if(snapshot.spreadPoints > item.profile.maxSpreadPoints)
      {
         decision.reason = "spread too high " + DoubleToString(snapshot.spreadPoints, 1);
         return false;
      }

      if(CountActiveProducts(magic) >= maxActiveProducts)
      {
         int ownCount = 0;
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            ulong ticket = PositionGetTicket(i);
            if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
            if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;
            if(PositionGetString(POSITION_SYMBOL) == item.resolvedSymbol) ownCount++;
         }
         if(ownCount == 0)
         {
            decision.reason = "max active products reached";
            return false;
         }
      }

      int symbolPositions = 0;
      int sameDirectionPositions = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
         if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;
         if(PositionGetString(POSITION_SYMBOL) == item.resolvedSymbol) symbolPositions++;
         if(PositionGetString(POSITION_SYMBOL) != item.resolvedSymbol) continue;

         ENUM_POSITION_TYPE positionType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         if((OmniIsBuySignal(signal.type) && positionType == POSITION_TYPE_BUY) ||
            (OmniIsSellSignal(signal.type) && positionType == POSITION_TYPE_SELL))
            sameDirectionPositions++;
      }
      if(symbolPositions >= maxPositionsPerSymbol && !signal.isHedge && !signal.isAddOn)
      {
         decision.reason = "max positions per symbol reached";
         return false;
      }

      if(sameDirectionPositions > 0 && !signal.isHedge && !signal.isAddOn)
      {
         decision.reason = "same direction position already open";
         return false;
      }

      decision.allowed = true;
      decision.reason = "allowed";
      return true;
   }

   double CalculateVolume(const string symbol,
                          const ENUM_OMNI_SIGNAL signalType,
                          const double entry,
                          const double sl,
                          const double effectiveRiskPct,
                          double &riskMoneyBroker,
                          string &reason)
   {
      riskMoneyBroker = 0.0;
      if(entry <= 0.0 || sl <= 0.0 || entry == sl)
      {
         reason = "invalid entry/sl";
         return 0.0;
      }

      ENUM_ORDER_TYPE orderType = OmniIsBuySignal(signalType) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double oneLotProfit = 0.0;
      if(!OrderCalcProfit(orderType, symbol, 1.0, entry, sl, oneLotProfit))
      {
         reason = "OrderCalcProfit failed";
         return 0.0;
      }

      double oneLotLoss = MathAbs(oneLotProfit);
      if(oneLotLoss <= 0.0)
      {
         reason = "one lot loss is zero";
         return 0.0;
      }

      double effectiveRiskMoney = account.EffectiveBalance() * effectiveRiskPct / 100.0;
      riskMoneyBroker = account.ToBrokerMoney(effectiveRiskMoney);
      double rawVolume = riskMoneyBroker / oneLotLoss;

      double minVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
      double maxVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
      double step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
      if(step <= 0.0) step = 0.01;

      double normalized = MathFloor(rawVolume / step) * step;
      normalized = MathMax(0.0, MathMin(maxVolume, normalized));
      if(normalized < minVolume)
      {
         reason = "risk too small for min lot";
         return 0.0;
      }

      reason = "volume ok";
      return normalized;
   }
};

#endif
