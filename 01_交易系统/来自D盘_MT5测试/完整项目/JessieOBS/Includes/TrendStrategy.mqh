#ifndef _TRENDSTRATEGY_MQH_
#define _TRENDSTRATEGY_MQH_

#include "Defines.mqh"

class CTrendStrategy
{
private:
   int              m_fastEMAHandle;
   int              m_slowEMAHandle;
   int              m_atrHandle;
   int              m_adxHandle;
   int              m_fastPeriod;
   int              m_slowPeriod;
   double           m_slMultiplier;
   double           m_tpMultiplier;
   double           m_trailStart;
   double           m_trailStep;
   int              m_minADX;
   int              m_cooldownBars;
   string           m_symbol;
   ENUM_TIMEFRAMES  m_timeframe;
   int              m_barsSinceLastTrade;
   bool             m_initialized;
   datetime         m_lastBarTime;

public:
   CTrendStrategy()
   {
      m_fastEMAHandle     = INVALID_HANDLE;
      m_slowEMAHandle     = INVALID_HANDLE;
      m_atrHandle         = INVALID_HANDLE;
      m_adxHandle         = INVALID_HANDLE;
      m_fastPeriod        = 21;
      m_slowPeriod        = 55;
      m_slMultiplier      = 2.0;
      m_tpMultiplier      = 3.5;
      m_trailStart        = 1.5;
      m_trailStep         = 0.5;
      m_minADX            = 22;
      m_cooldownBars      = 4;
      m_barsSinceLastTrade = 999;
      m_initialized       = false;
      m_lastBarTime       = 0;
   }

   bool Init(string symbol, ENUM_TIMEFRAMES tf,
             int fastPeriod, int slowPeriod, double slMult, double tpMult,
             double trailStart, double trailStep, int minADX, int cooldown)
   {
      m_symbol       = symbol;
      m_timeframe    = tf;
      m_fastPeriod   = fastPeriod;
      m_slowPeriod   = slowPeriod;
      m_slMultiplier = slMult;
      m_tpMultiplier = tpMult;
      m_trailStart   = trailStart;
      m_trailStep    = trailStep;
      m_minADX       = minADX;
      m_cooldownBars = cooldown;

      m_fastEMAHandle = iMA(m_symbol, m_timeframe, m_fastPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_slowEMAHandle = iMA(m_symbol, m_timeframe, m_slowPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_atrHandle     = iATR(m_symbol, m_timeframe, 14);
      m_adxHandle     = iADX(m_symbol, m_timeframe, 14);

      if(m_fastEMAHandle == INVALID_HANDLE || m_slowEMAHandle == INVALID_HANDLE ||
         m_atrHandle == INVALID_HANDLE || m_adxHandle == INVALID_HANDLE)
      {
         Print("TrendStrategy: Failed to create indicator handles");
         return false;
      }

      m_initialized = true;
      return true;
   }

   void Deinit()
   {
      if(m_fastEMAHandle != INVALID_HANDLE) IndicatorRelease(m_fastEMAHandle);
      if(m_slowEMAHandle != INVALID_HANDLE) IndicatorRelease(m_slowEMAHandle);
      if(m_atrHandle     != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
      if(m_adxHandle     != INVALID_HANDLE) IndicatorRelease(m_adxHandle);
      m_fastEMAHandle = INVALID_HANDLE;
      m_slowEMAHandle = INVALID_HANDLE;
      m_atrHandle     = INVALID_HANDLE;
      m_adxHandle     = INVALID_HANDLE;
      m_initialized   = false;
   }

   bool IsNewBar()
   {
      datetime curBar = iTime(m_symbol, m_timeframe, 0);
      if(curBar != m_lastBarTime && curBar > 0)
      {
         m_lastBarTime = curBar;
         return true;
      }
      return false;
   }

   void OnNewBar() { m_barsSinceLastTrade++; }

   STradeSignal GenerateSignal()
   {
      STradeSignal signal;
      ZeroMemory(signal);

      if(!m_initialized) return signal;
      if(m_barsSinceLastTrade < m_cooldownBars) return signal;
      if(!IsNewBar()) return signal;
      OnNewBar();

      double fast[2], slow[2], atr[1], adx[1];

      if(CopyBuffer(m_fastEMAHandle, 0, 0, 2, fast) < 2 ||
         CopyBuffer(m_slowEMAHandle, 0, 0, 2, slow) < 2 ||
         CopyBuffer(m_atrHandle, 0, 0, 1, atr) < 1 ||
         CopyBuffer(m_adxHandle, 0, 0, 1, adx) < 1)
         return signal;

      if(adx[0] < m_minADX) return signal;

      double point    = SymbolInfoDouble(m_symbol, SYMBOL_POINT);
      int    digits   = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);
      double askPrice = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double bidPrice = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      double atrVal   = atr[0];

      bool buySignal  = (fast[1] <= slow[1] && fast[0] > slow[0]);
      bool sellSignal = (fast[1] >= slow[1] && fast[0] < slow[0]);

      if(!buySignal && !sellSignal) return signal;

      if(buySignal)
      {
         double slDist = atrVal * m_slMultiplier;
         double tpDist = atrVal * m_tpMultiplier;

         signal.direction      = TRADE_BUY;
         signal.entryPrice     = askPrice;
         signal.stopLoss       = NormalizeDouble(askPrice - slDist, digits);
         signal.takeProfit     = NormalizeDouble(askPrice + tpDist, digits);
         signal.sourceStrategy = STRATEGY_TREND;
         signal.isValid        = true;
      }
      else
      {
         double slDist = atrVal * m_slMultiplier;
         double tpDist = atrVal * m_tpMultiplier;

         signal.direction      = TRADE_SELL;
         signal.entryPrice     = bidPrice;
         signal.stopLoss       = NormalizeDouble(bidPrice + slDist, digits);
         signal.takeProfit     = NormalizeDouble(bidPrice - tpDist, digits);
         signal.sourceStrategy = STRATEGY_TREND;
         signal.isValid        = true;
      }

      return signal;
   }

   void OnTradeOpened() { m_barsSinceLastTrade = 0; }

   bool ShouldTrailStop(ulong ticket)
   {
      if(!PositionSelectByTicket(ticket)) return false;

      double openPrice  = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL  = PositionGetDouble(POSITION_SL);
      long   posType    = PositionGetInteger(POSITION_TYPE);
      double point      = SymbolInfoDouble(m_symbol, SYMBOL_POINT);
      int    digits     = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);

      double atr[1];
      if(CopyBuffer(m_atrHandle, 0, 0, 1, atr) <= 0) return false;

      double trailDist  = atr[0] * m_trailStart;
      double stepDist   = atr[0] * m_trailStep;

      if(posType == POSITION_TYPE_BUY)
      {
         double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
         double profitDist = bid - openPrice;

         if(profitDist >= trailDist)
         {
            double newSL = NormalizeDouble(bid - stepDist, digits);
            if(newSL > currentSL + point * 5)
               return true;
         }
      }
      else
      {
         double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
         double profitDist = openPrice - ask;

         if(profitDist >= trailDist)
         {
            double newSL = NormalizeDouble(ask + stepDist, digits);
            if(newSL < currentSL - point * 5 || currentSL == 0)
               return true;
         }
      }

      return false;
   }

   void ApplyTrailingStop(ulong ticket, double &newSL, double &newTP)
   {
      newSL = 0;
      newTP = 0;

      if(!PositionSelectByTicket(ticket)) return;

      double openPrice  = PositionGetDouble(POSITION_PRICE_OPEN);
      long   posType    = PositionGetInteger(POSITION_TYPE);
      double point      = SymbolInfoDouble(m_symbol, SYMBOL_POINT);
      int    digits     = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);

      double atr[1];
      if(CopyBuffer(m_atrHandle, 0, 0, 1, atr) <= 0) return;

      double trailDist  = atr[0] * m_trailStart;
      double stepDist   = atr[0] * m_trailStep;

      newTP = PositionGetDouble(POSITION_TP);

      if(posType == POSITION_TYPE_BUY)
      {
         double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
         double profitDist = bid - openPrice;

         if(profitDist >= trailDist)
         {
            newSL = NormalizeDouble(bid - stepDist, digits);
         }
      }
      else
      {
         double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
         double profitDist = openPrice - ask;

         if(profitDist >= trailDist)
         {
            newSL = NormalizeDouble(ask + stepDist, digits);
         }
      }
   }

   bool IsInitialized() const { return m_initialized; }
};

#endif
