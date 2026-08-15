#ifndef _RISKMANAGER_MQH_
#define _RISKMANAGER_MQH_

#include "Defines.mqh"
#include "../Utils/TradeWrapper.mqh"
#include "../Utils/Logger.mqh"

class CRiskManager
{
private:
   CTradeWrapper* m_trade;
   CLogger*       m_logger;
   string         m_symbol;
   double         m_maxDailyLossPercent;
   int            m_maxConsecutiveLosses;
   double         m_maxTotalRiskPercent;
   double         m_initialBalance;
   double         m_dailyStartBalance;
   double         m_dailyStartEquity;
   datetime       m_lastDayCheck;
   int            m_consecutiveLosses;
   int            m_consecutiveWins;
   bool           m_circuitBreakerActive;
   datetime       m_circuitBreakerTime;
   int            m_todayTotalTrades;
   int            m_todayWinningTrades;
   int            m_todayLosingTrades;
   double         m_todayProfitLoss;

public:
   CRiskManager()
   {
      m_trade                = NULL;
      m_logger               = NULL;
      m_maxDailyLossPercent  = 5.0;
      m_maxConsecutiveLosses = 5;
      m_maxTotalRiskPercent  = 25.0;
      m_initialBalance       = 0;
      m_dailyStartBalance    = 0;
      m_dailyStartEquity     = 0;
      m_lastDayCheck         = 0;
      m_consecutiveLosses    = 0;
      m_consecutiveWins      = 0;
      m_circuitBreakerActive = false;
      m_circuitBreakerTime   = 0;
      m_todayTotalTrades     = 0;
      m_todayWinningTrades   = 0;
      m_todayLosingTrades    = 0;
      m_todayProfitLoss      = 0;
   }

   void Init(CTradeWrapper* trade, CLogger* logger, string symbol,
             double maxDailyLoss, int maxConsLoss, double maxTotalRisk)
   {
      m_trade                = trade;
      m_logger               = logger;
      m_symbol               = symbol;
      m_maxDailyLossPercent  = maxDailyLoss;
      m_maxConsecutiveLosses = maxConsLoss;
      m_maxTotalRiskPercent  = maxTotalRisk;
      m_initialBalance       = AccountInfoDouble(ACCOUNT_BALANCE);
      m_dailyStartBalance    = m_initialBalance;
      m_dailyStartEquity     = AccountInfoDouble(ACCOUNT_EQUITY);
      m_lastDayCheck         = TimeCurrent();
   }

   void CheckNewDay()
   {
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      MqlDateTime lastDt;
      TimeToStruct(m_lastDayCheck, lastDt);

      if(dt.day != lastDt.day || dt.mon != lastDt.mon || dt.year != lastDt.year)
      {
         m_dailyStartBalance  = AccountInfoDouble(ACCOUNT_BALANCE);
         m_dailyStartEquity   = AccountInfoDouble(ACCOUNT_EQUITY);
         m_lastDayCheck       = TimeCurrent();
         m_todayTotalTrades   = 0;
         m_todayWinningTrades = 0;
         m_todayLosingTrades  = 0;
         m_todayProfitLoss    = 0;

         if(m_logger) m_logger.Info("New trading day. Daily start equity: " +
            DoubleToString(m_dailyStartEquity, 2));
      }
   }

   void OnTradeClosed(double profit)
   {
      m_todayTotalTrades++;
      if(profit > 0)
      {
         m_consecutiveWins++;
         m_consecutiveLosses = 0;
         m_todayWinningTrades++;
         m_todayProfitLoss += profit;
      }
      else
      {
         m_consecutiveLosses++;
         m_consecutiveWins = 0;
         m_todayLosingTrades++;
         m_todayProfitLoss += profit;
      }

      if(m_logger) m_logger.Info("Trade closed | P/L=" + DoubleToString(profit, 2) +
         " | ConsecLosses=" + IntegerToString(m_consecutiveLosses) +
         " | TodayP/L=" + DoubleToString(m_todayProfitLoss, 2));
   }

   bool IsTradingAllowed()
   {
      CheckNewDay();

      if(m_circuitBreakerActive)
      {
         datetime now = TimeCurrent();
         if(now - m_circuitBreakerTime > 3600)
         {
            m_circuitBreakerActive = false;
            m_consecutiveLosses    = 0;
            if(m_logger) m_logger.Info("Circuit breaker reset after 1 hour cooldown");
         }
         else
         {
            return false;
         }
      }

      if(m_maxDailyLossPercent > 0 && m_dailyStartEquity > 0)
      {
         double currentEquity    = AccountInfoDouble(ACCOUNT_EQUITY);
         double dailyLossAmount  = m_dailyStartEquity - currentEquity;
         double dailyLossPercent = (dailyLossAmount / m_dailyStartEquity) * 100.0;

         if(dailyLossPercent >= m_maxDailyLossPercent)
         {
            ActivateCircuitBreaker("Daily loss limit reached: " + DoubleToString(dailyLossPercent, 1) + "%");
            return false;
         }
      }

      if(m_maxTotalRiskPercent > 0 && m_initialBalance > 0)
      {
         double currentEquity    = AccountInfoDouble(ACCOUNT_EQUITY);
         double totalLossPercent = ((m_initialBalance - currentEquity) / m_initialBalance) * 100.0;

         if(totalLossPercent >= m_maxTotalRiskPercent)
         {
            ActivateCircuitBreaker("Total account risk limit reached: " + DoubleToString(totalLossPercent, 1) + "%");
            return false;
         }
      }

      if(m_maxConsecutiveLosses > 0 && m_consecutiveLosses >= m_maxConsecutiveLosses)
      {
         ActivateCircuitBreaker("Max consecutive losses reached: " + IntegerToString(m_consecutiveLosses));
         return false;
      }

      double marginLevel = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
      if(marginLevel > 0 && marginLevel < 200)
      {
         if(m_logger) m_logger.Warn("Margin level critically low: " + DoubleToString(marginLevel, 0) + "%");
         return false;
      }

      return true;
   }

   void ActivateCircuitBreaker(string reason)
   {
      m_circuitBreakerActive = true;
      m_circuitBreakerTime   = TimeCurrent();
      if(m_logger) m_logger.Error("CIRCUIT BREAKER ACTIVATED: " + reason);

      int total = PositionsTotal();
      if(total > 0)
      {
         if(m_logger) m_logger.Warn("Emergency closing all positions...");
         m_trade.CloseAllPositions();
      }
   }

   bool IsCircuitBreakerActive() const { return m_circuitBreakerActive; }
   int  GetConsecutiveLosses()   const { return m_consecutiveLosses; }
   int  GetConsecutiveWins()     const { return m_consecutiveWins; }
   double GetTodayPL()           const { return m_todayProfitLoss; }
   int    GetTodayTrades()       const { return m_todayTotalTrades; }
   int    GetTodayWins()         const { return m_todayWinningTrades; }
};

#endif
