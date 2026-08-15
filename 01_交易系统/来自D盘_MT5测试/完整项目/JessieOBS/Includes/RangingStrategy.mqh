#ifndef _RANGINGSTRATEGY_MQH_
#define _RANGINGSTRATEGY_MQH_

#include "Defines.mqh"

class CRangingStrategy
{
private:
   int              m_bbHandle;
   int              m_rsiHandle;
   int              m_atrHandle;
   int              m_bbPeriod;
   double           m_bbDeviations;
   int              m_rsiPeriod;
   double           m_rsiOB;
   double           m_rsiOS;
   double           m_slMultiplier;
   double           m_tpMultiplier;
   double           m_trailStart;
   double           m_trailStep;
   int              m_cooldownBars;
   string           m_symbol;
   ENUM_TIMEFRAMES  m_timeframe;
   int              m_barsSinceLastTrade;
   bool             m_initialized;
   datetime         m_lastBarTime;
   datetime         m_lastSignalTime;

public:
   CRangingStrategy()
   {
      m_bbHandle          = INVALID_HANDLE;
      m_rsiHandle         = INVALID_HANDLE;
      m_atrHandle         = INVALID_HANDLE;
      m_bbPeriod          = 20;
      m_bbDeviations      = 2.0;
      m_rsiPeriod         = 14;
      m_rsiOB             = 68.0;
      m_rsiOS             = 32.0;
      m_slMultiplier      = 0.9;
      m_tpMultiplier      = 1.8;
      m_trailStart        = 0.8;
      m_trailStep         = 0.3;
      m_cooldownBars      = 2;
      m_barsSinceLastTrade = 999;
      m_initialized       = false;
      m_lastBarTime       = 0;
      m_lastSignalTime    = 0;
   }

   bool Init(string symbol, ENUM_TIMEFRAMES tf,
             int bbPeriod, double bbDeviations, int rsiPeriod,
             double rsiOB, double rsiOS, double slMult, double tpMult,
             double trailStart, double trailStep, int cooldown)
   {
      m_symbol       = symbol;
      m_timeframe    = tf;
      m_bbPeriod     = bbPeriod;
      m_bbDeviations = bbDeviations;
      m_rsiPeriod    = rsiPeriod;
      m_rsiOB        = rsiOB;
      m_rsiOS        = rsiOS;
      m_slMultiplier = slMult;
      m_tpMultiplier = tpMult;
      m_trailStart   = trailStart;
      m_trailStep    = trailStep;
      m_cooldownBars = cooldown;

      m_bbHandle  = iBands(m_symbol, m_timeframe, m_bbPeriod, 0, m_bbDeviations, PRICE_CLOSE);
      m_rsiHandle = iRSI(m_symbol, m_timeframe, m_rsiPeriod, PRICE_CLOSE);
      m_atrHandle = iATR(m_symbol, m_timeframe, 14);

      if(m_bbHandle == INVALID_HANDLE || m_rsiHandle == INVALID_HANDLE || m_atrHandle == INVALID_HANDLE)
      {
         Print("RangingStrategy: Failed to create indicator handles");
         return false;
      }

      m_initialized = true;
      return true;
   }

   void Deinit()
   {
      if(m_bbHandle  != INVALID_HANDLE) IndicatorRelease(m_bbHandle);
      if(m_rsiHandle != INVALID_HANDLE) IndicatorRelease(m_rsiHandle);
      if(m_atrHandle != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
      m_bbHandle  = INVALID_HANDLE;
      m_rsiHandle = INVALID_HANDLE;
      m_atrHandle = INVALID_HANDLE;
      m_initialized = false;
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

      double upper[1], middle[1], lower[1];
      double rsi[1], atr[1];

      if(CopyBuffer(m_bbHandle, 1, 0, 1, upper) < 1 ||
         CopyBuffer(m_bbHandle, 0, 0, 1, middle) < 1 ||
         CopyBuffer(m_bbHandle, 2, 0, 1, lower) < 1 ||
         CopyBuffer(m_rsiHandle, 0, 0, 1, rsi) < 1 ||
         CopyBuffer(m_atrHandle, 0, 0, 1, atr) < 1)
         return signal;

      double askPrice = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double bidPrice = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      double atrVal   = atr[0];
      int    digits   = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);

      double bbWidth = upper[0] - lower[0];
      if(bbWidth < atrVal * 0.8 && atrVal > 0) return signal;

      bool buySignal  = false;
      bool sellSignal = false;

      if(bidPrice <= lower[0] && rsi[0] <= m_rsiOS)
         buySignal = true;
      else if(askPrice >= upper[0] && rsi[0] >= m_rsiOB)
         sellSignal = true;
      else if(bidPrice <= middle[0] - atrVal * 0.5 && rsi[0] < 40)
         buySignal = true;
      else if(askPrice >= middle[0] + atrVal * 0.5 && rsi[0] > 60)
         sellSignal = true;

      if(!buySignal && !sellSignal) return signal;

      if(buySignal)
      {
         double slDist = atrVal * m_slMultiplier;
         double tpDist = atrVal * m_tpMultiplier;

         signal.direction      = TRADE_BUY;
         signal.entryPrice     = askPrice;
         signal.stopLoss       = NormalizeDouble(askPrice - slDist, digits);
         signal.takeProfit     = NormalizeDouble(askPrice + tpDist, digits);
         signal.sourceStrategy = STRATEGY_RANGING;
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
         signal.sourceStrategy = STRATEGY_RANGING;
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
            if(newSL > currentSL + point * 3)
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
            if(newSL < currentSL - point * 3 || currentSL == 0)
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
