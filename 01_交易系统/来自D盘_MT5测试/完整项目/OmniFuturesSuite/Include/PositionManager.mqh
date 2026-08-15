#ifndef POSITION_MANAGER_MQH
#define POSITION_MANAGER_MQH

#include "OmniTypes.mqh"
#include "TradeExecutor.mqh"
#include "NotificationCenter.mqh"

class COmniPositionManager
{
private:
   ulong magic;
   COmniTradeExecutor *executor;
   COmniNotificationCenter *notify;

   string PartialKey(const ulong ticket)
   {
      return "OMNI_PARTIAL_" + IntegerToString((long)magic) + "_" + IntegerToString((long)ticket);
   }

   bool IsFridayCloseTime(const int fridayCloseHour, const int fridayCloseMinute)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);
      if(now.day_of_week != 5) return false;
      if(now.hour > fridayCloseHour) return true;
      if(now.hour == fridayCloseHour && now.min >= fridayCloseMinute) return true;
      return false;
   }

   bool IsRangeForceCloseTime(const int closeHour, const int closeMinute)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);
      if(now.hour > closeHour) return true;
      if(now.hour == closeHour && now.min >= closeMinute) return true;
      return false;
   }

public:
   COmniPositionManager()
   {
      magic = 0;
      executor = NULL;
      notify = NULL;
   }

   bool Init(const ulong magicNumber,
             COmniTradeExecutor &tradeExecutor,
             COmniNotificationCenter &notificationCenter)
   {
      magic = magicNumber;
      executor = &tradeExecutor;
      notify = &notificationCenter;
      return true;
   }

   void GetExposure(const string symbol, SOmniExposure &exposure)
   {
      OmniResetExposure(exposure);
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != symbol) continue;
         if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;

         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double volume = PositionGetDouble(POSITION_VOLUME);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double profit = PositionGetDouble(POSITION_PROFIT);
         string comment = PositionGetString(POSITION_COMMENT);

         exposure.floatingProfit += profit;
         if(StringFind(comment, "HEDGE") >= 0)
            exposure.hedgeCount++;

         if(type == POSITION_TYPE_BUY)
         {
            exposure.buyCount++;
            exposure.buyVolume += volume;
            exposure.lastBuyPrice = openPrice;
            if(exposure.maxBuyOpenPrice == 0.0 || openPrice > exposure.maxBuyOpenPrice)
               exposure.maxBuyOpenPrice = openPrice;
         }
         else if(type == POSITION_TYPE_SELL)
         {
            exposure.sellCount++;
            exposure.sellVolume += volume;
            exposure.lastSellPrice = openPrice;
            if(exposure.minSellOpenPrice == 0.0 || openPrice < exposure.minSellOpenPrice)
               exposure.minSellOpenPrice = openPrice;
         }
      }
   }

   void Manage(const SOmniSymbol &item,
               const SOmniMarketSnapshot &snapshot,
               const bool forceFridayClose,
               const int fridayCloseHour,
               const int fridayCloseMinute,
               const int rangeCloseHour,
               const int rangeCloseMinute)
   {
      if(!item.enabled || executor == NULL) return;

      bool fridayClose = forceFridayClose && IsFridayCloseTime(fridayCloseHour, fridayCloseMinute);
      bool rangeClose = IsRangeForceCloseTime(rangeCloseHour, rangeCloseMinute);

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != item.resolvedSymbol) continue;
         if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;

         string comment = PositionGetString(POSITION_COMMENT);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double sl = PositionGetDouble(POSITION_SL);
         double tp = PositionGetDouble(POSITION_TP);
         double volume = PositionGetDouble(POSITION_VOLUME);
         double current = (type == POSITION_TYPE_BUY) ? snapshot.bid : snapshot.ask;
         double atr = snapshot.h1Atr;
         if(atr <= 0.0) continue;

         if(fridayClose)
         {
            executor.ClosePositionTicket(ticket, "Friday close");
            continue;
         }

         if(StringFind(comment, "RANGE") >= 0 && rangeClose)
         {
            executor.ClosePositionTicket(ticket, "Range no overnight");
            continue;
         }

         double profitDistance = (type == POSITION_TYPE_BUY) ? (current - openPrice) : (openPrice - current);
         double newSl = sl;

         if(profitDistance >= atr * item.profile.breakevenAtr)
         {
            double beSl = openPrice;
            if(type == POSITION_TYPE_BUY && (sl == 0.0 || beSl > sl))
               newSl = beSl;
            if(type == POSITION_TYPE_SELL && (sl == 0.0 || beSl < sl))
               newSl = beSl;
         }

         if(profitDistance >= atr * item.profile.trailingAtr)
         {
            double trailSl = (type == POSITION_TYPE_BUY)
                             ? current - atr * item.profile.trailingAtr
                             : current + atr * item.profile.trailingAtr;
            if(type == POSITION_TYPE_BUY && (newSl == 0.0 || trailSl > newSl))
               newSl = trailSl;
            if(type == POSITION_TYPE_SELL && (newSl == 0.0 || trailSl < newSl))
               newSl = trailSl;
         }

         if(newSl > 0.0)
         {
            int digits = (int)SymbolInfoInteger(item.resolvedSymbol, SYMBOL_DIGITS);
            double point = SymbolInfoDouble(item.resolvedSymbol, SYMBOL_POINT);
            if(point <= 0.0) point = _Point;
            double stopsDistance = (double)SymbolInfoInteger(item.resolvedSymbol, SYMBOL_TRADE_STOPS_LEVEL) * point;
            double minMove = MathMax(point * 10.0, atr * 0.05);
            newSl = NormalizeDouble(newSl, digits);

            bool improves = false;
            if(type == POSITION_TYPE_BUY)
            {
               improves = (sl == 0.0 || newSl > sl + minMove);
               if(stopsDistance > 0.0 && newSl > snapshot.bid - stopsDistance)
                  improves = false;
            }
            else
            {
               improves = (sl == 0.0 || newSl < sl - minMove);
               if(stopsDistance > 0.0 && newSl < snapshot.ask + stopsDistance)
                  improves = false;
            }

            if(improves)
               executor.ModifyStops(ticket, item.resolvedSymbol, newSl, tp);
         }

         string key = PartialKey(ticket);
         if(profitDistance >= atr * item.profile.partialCloseAtr &&
            !GlobalVariableCheck(key) &&
            volume > SymbolInfoDouble(item.resolvedSymbol, SYMBOL_VOLUME_MIN))
         {
            double closeVolume = volume * item.profile.partialCloseRatio;
            if(executor.ClosePartialTicket(ticket, item.resolvedSymbol, closeVolume, "Partial at ATR target"))
               GlobalVariableSet(key, TimeCurrent());
         }
      }
   }
};

#endif
