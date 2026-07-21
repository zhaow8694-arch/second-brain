#ifndef _ENTRYEXITMANAGER_MQH_
#define _ENTRYEXITMANAGER_MQH_

#include <Trade/Trade.mqh>
#include "Defines.mqh"
#include "../Utils/TradeWrapper.mqh"
#include "../Utils/Logger.mqh"

class CEntryExitManager
{
private:
   CTradeWrapper* m_trade;
   CLogger*       m_logger;
   string         m_symbol;
   double         m_riskPercent;
   bool           m_useFixedLot;
   double         m_fixedLotSize;
   int            m_maxTrendPositions;
   int            m_maxRangePositions;
   int            m_maxTotalPositions;
   double         m_trendRiskMultiplier;
   double         m_rangeRiskMultiplier;
   int            m_atrHandle;
   int            m_atrPeriod;

public:
   CEntryExitManager()
   {
      m_trade               = NULL;
      m_logger              = NULL;
      m_riskPercent         = 1.0;
      m_useFixedLot         = false;
      m_fixedLotSize        = 0.1;
      m_maxTrendPositions   = 2;
      m_maxRangePositions   = 1;
      m_maxTotalPositions   = 3;
      m_trendRiskMultiplier = 1.3;
      m_rangeRiskMultiplier = 0.7;
      m_atrHandle           = INVALID_HANDLE;
      m_atrPeriod           = 14;
   }

   void Init(CTradeWrapper* trade, CLogger* logger, string symbol,
             double riskPercent, bool useFixedLot, double fixedLot,
             int maxTrend, int maxRange, int maxTotal, int atrPeriod = 14)
   {
      m_trade             = trade;
      m_logger            = logger;
      m_symbol            = symbol;
      m_riskPercent       = riskPercent;
      m_useFixedLot       = useFixedLot;
      m_fixedLotSize      = fixedLot;
      m_maxTrendPositions = maxTrend;
      m_maxRangePositions = maxRange;
      m_maxTotalPositions = maxTotal;
      m_atrPeriod         = atrPeriod;

      if(m_atrHandle != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
      m_atrHandle = iATR(m_symbol, PERIOD_CURRENT, m_atrPeriod);
   }

   void Deinit()
   {
      if(m_atrHandle != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
      m_atrHandle = INVALID_HANDLE;
   }

   bool GetATR(double &atrValue)
   {
      double atr[1];
      if(m_atrHandle == INVALID_HANDLE) return false;
      if(CopyBuffer(m_atrHandle, 0, 0, 1, atr) <= 0) return false;
      atrValue = atr[0];
      return atrValue > 0;
   }

   int CountPositionsByStrategy(ENUM_STRATEGY_TYPE strategyType)
   {
      int count = 0;
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != EA_MAGIC_NUMBER) continue;

         string comment = PositionGetString(POSITION_COMMENT);
         if(strategyType == STRATEGY_TREND && StringFind(comment, "TREND") >= 0)
            count++;
         else if(strategyType == STRATEGY_RANGING && StringFind(comment, "RANGE") >= 0)
            count++;
      }
      return count;
   }

   int CountAllPositions()
   {
      int count = 0;
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != EA_MAGIC_NUMBER) continue;
         count++;
      }
      return count;
   }

   double CalculateLotSize(double slDistance, ENUM_STRATEGY_TYPE strategyType)
   {
      if(m_useFixedLot && m_fixedLotSize > 0)
         return m_fixedLotSize;

      double riskMultiplier = (strategyType == STRATEGY_TREND) ? m_trendRiskMultiplier : m_rangeRiskMultiplier;
      double effectiveRisk  = m_riskPercent * riskMultiplier / 100.0;

      double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      double accountEquity  = AccountInfoDouble(ACCOUNT_EQUITY);
      double equity         = MathMin(accountBalance, accountEquity);

      double riskAmount     = equity * effectiveRisk;
      double tickValue      = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSize       = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_SIZE);

      if(tickValue <= 0 || tickSize <= 0 || slDistance <= 0)
      {
         double minLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
         return minLot;
      }

      double slPoints = slDistance / tickSize;
      double lotSize  = riskAmount / (slPoints * tickValue);

      double minLot   = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
      double maxLot   = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
      double lotStep  = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);

      double maxLotByEquity = equity * 0.05 / (SymbolInfoDouble(m_symbol, SYMBOL_TRADE_CONTRACT_SIZE) * SymbolInfoDouble(m_symbol, SYMBOL_BID));
      if(maxLotByEquity < minLot) maxLotByEquity = minLot;

      lotSize = MathMax(minLot, MathMin(maxLotByEquity, lotSize));
      lotSize = MathMin(lotSize, maxLot);
      lotSize = MathFloor(lotSize / lotStep) * lotStep;
      lotSize = NormalizeDouble(lotSize, 2);

      return lotSize;
   }

   bool ExecuteSignal(STradeSignal &signal)
   {
      if(!signal.isValid) return false;

      int totalPositions = CountAllPositions();
      if(totalPositions >= m_maxTotalPositions)
      {
         if(m_logger) m_logger.Warn("Max total positions reached: " + IntegerToString(totalPositions));
         return false;
      }

      if(signal.sourceStrategy == STRATEGY_TREND)
      {
         int trendPos = CountPositionsByStrategy(STRATEGY_TREND);
         if(trendPos >= m_maxTrendPositions)
         {
            if(m_logger) m_logger.Warn("Max trend positions reached: " + IntegerToString(trendPos));
            return false;
         }
      }
      else
      {
         int rangePos = CountPositionsByStrategy(STRATEGY_RANGING);
         if(rangePos >= m_maxRangePositions)
         {
            if(m_logger) m_logger.Warn("Max range positions reached: " + IntegerToString(rangePos));
            return false;
         }
      }

      double slDist = MathAbs(signal.entryPrice - signal.stopLoss);
      signal.lotSize = CalculateLotSize(slDist, signal.sourceStrategy);

      if(signal.lotSize < SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN))
      {
         if(m_logger) m_logger.Warn("Calculated lot size too small: " + DoubleToString(signal.lotSize, 2));
         return false;
      }

      string comment = (signal.sourceStrategy == STRATEGY_TREND) ? "JessieOBS_TREND" : "JessieOBS_RANGE";

      bool success = false;
      if(signal.direction == TRADE_BUY)
         success = m_trade.OpenBuy(signal.lotSize, signal.stopLoss, signal.takeProfit, comment);
      else if(signal.direction == TRADE_SELL)
         success = m_trade.OpenSell(signal.lotSize, signal.stopLoss, signal.takeProfit, comment);

      return success;
   }

   void ManagePositionHandover(ENUM_MARKET_STATE oldState, ENUM_MARKET_STATE newState)
   {
      if(oldState == newState) return;
      if(oldState == MARKET_STATE_UNKNOWN || newState == MARKET_STATE_UNKNOWN) return;

      double atrVal = 0;
      if(!GetATR(atrVal)) return;

      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != EA_MAGIC_NUMBER) continue;

         string comment = PositionGetString(POSITION_COMMENT);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double currentSL = PositionGetDouble(POSITION_SL);
         double currentTP = PositionGetDouble(POSITION_TP);
         long   posType   = PositionGetInteger(POSITION_TYPE);
         int    digits    = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);
         double profit    = PositionGetDouble(POSITION_PROFIT);
         double newSL     = currentSL;
         double newTP     = currentTP;

         if(oldState == MARKET_STATE_TRENDING && newState == MARKET_STATE_RANGING &&
            StringFind(comment, "TREND") >= 0)
         {
            if(m_logger) m_logger.Info("State handover: TREND->RANGE - tightening legacy trend stops");

            double tightSLDist = atrVal * 1.0;
            if(posType == POSITION_TYPE_BUY)
            {
               double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
               newSL = NormalizeDouble(bid - tightSLDist, digits);
               if(profit > 0)
                  newSL = NormalizeDouble(MathMax(newSL, openPrice + 5 * SymbolInfoDouble(m_symbol, SYMBOL_POINT)), digits);
            }
            else
            {
               double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
               newSL = NormalizeDouble(ask + tightSLDist, digits);
               if(profit > 0)
                  newSL = NormalizeDouble(MathMin(newSL, openPrice - 5 * SymbolInfoDouble(m_symbol, SYMBOL_POINT)), digits);
            }
         }
         else if(oldState == MARKET_STATE_RANGING && newState == MARKET_STATE_TRENDING &&
                 StringFind(comment, "RANGE") >= 0)
         {
            if(m_logger) m_logger.Info("State handover: RANGE->TREND - widening legacy range stops");

            double wideSLDist = atrVal * 2.0;
            if(posType == POSITION_TYPE_BUY)
            {
               double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
               double candidateSL = NormalizeDouble(bid - wideSLDist, digits);
               if(currentSL == 0 || candidateSL < currentSL) newSL = candidateSL;
            }
            else
            {
               double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
               double candidateSL = NormalizeDouble(ask + wideSLDist, digits);
               if(currentSL == 0 || candidateSL > currentSL) newSL = candidateSL;
            }
         }
         else
         {
            continue;
         }

         if(m_trade.ModifySLTP(ticket, newSL, newTP))
         {
            if(m_logger) m_logger.Info("Handover: adjusted SL on legacy position #" + IntegerToString(ticket));
         }
      }
   }

   void ManageTrailingStops(bool isTrendMode)
   {
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != EA_MAGIC_NUMBER) continue;

         string comment = PositionGetString(POSITION_COMMENT);

         double openPrice  = PositionGetDouble(POSITION_PRICE_OPEN);
         double currentSL  = PositionGetDouble(POSITION_SL);
         double currentTP  = PositionGetDouble(POSITION_TP);
         long   posType    = PositionGetInteger(POSITION_TYPE);
         double point      = SymbolInfoDouble(m_symbol, SYMBOL_POINT);
         int    digits     = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);

         double atrVal = 0;
         if(!GetATR(atrVal)) continue;

         double trailStart, trailStep;
         bool isTrendPos = (StringFind(comment, "TREND") >= 0);

         if(isTrendPos || isTrendMode)
         {
            trailStart = atrVal * 1.5;
            trailStep  = atrVal * 0.5;
         }
         else
         {
            trailStart = atrVal * 0.8;
            trailStep  = atrVal * 0.3;
         }

         double newSL = 0;
         if(posType == POSITION_TYPE_BUY)
         {
            double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
            double profitDist = bid - openPrice;

            if(profitDist >= trailStart)
            {
               newSL = NormalizeDouble(bid - trailStep, digits);
               if(newSL > currentSL + point * 3 || currentSL == 0)
               {
                  m_trade.ModifySLTP(ticket, newSL, currentTP);
               }
            }
         }
         else
         {
            double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
            double profitDist = openPrice - ask;

            if(profitDist >= trailStart)
            {
               newSL = NormalizeDouble(ask + trailStep, digits);
               if(newSL < currentSL - point * 3 || currentSL == 0)
               {
                  m_trade.ModifySLTP(ticket, newSL, currentTP);
               }
            }
         }
      }
   }

   void ClosePosition(ulong ticket)
   {
      m_trade.ClosePosition(ticket);
   }
};

#endif
