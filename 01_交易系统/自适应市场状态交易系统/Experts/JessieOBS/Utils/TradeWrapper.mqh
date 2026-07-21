#ifndef _TRADEWRAPPER_MQH_
#define _TRADEWRAPPER_MQH_

#include <Trade/Trade.mqh>
#include "../Includes/Defines.mqh"
#include "Logger.mqh"

class CTradeWrapper
{
private:
   CTrade   m_trade;
   CLogger* m_logger;
   int      m_maxRetries;
   int      m_retryDelayMs;

public:
   CTradeWrapper()
   {
      m_maxRetries   = 3;
      m_retryDelayMs = 100;
      m_logger       = NULL;
   }

   void SetLogger(CLogger* logger) { m_logger = logger; }

   void SetRetryParams(int retries, int delayMs)
   {
      m_maxRetries   = retries;
      m_retryDelayMs = delayMs;
   }

   void SetMagicNumber(ulong magic)
   {
      m_trade.SetExpertMagicNumber(magic);
   }

   bool Initialize()
   {
      m_trade.SetExpertMagicNumber(EA_MAGIC_NUMBER);
      m_trade.SetDeviationInPoints(30);
      m_trade.SetTypeFilling(ORDER_FILLING_IOC);
      m_trade.SetAsyncMode(false);
      return true;
   }

   bool OpenBuy(double volume, double sl, double tp, string comment)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

      double price = NormalizeDouble(ask, digits);
      if(sl > 0) sl = NormalizeDouble(sl, digits);
      if(tp > 0) tp = NormalizeDouble(tp, digits);

      for(int i = 0; i < m_maxRetries; i++)
      {
         m_trade.SetDeviationInPoints(30);

         if(m_trade.Buy(volume, _Symbol, price, sl, tp, comment))
         {
            ulong ticket = m_trade.ResultOrder();
            if(m_logger) m_logger.Info("BUY opened | Ticket=" + IntegerToString(ticket) +
               " | Vol=" + DoubleToString(volume, 2) +
               " | Price=" + DoubleToString(price, digits) +
               " | SL=" + DoubleToString(sl, digits) +
               " | TP=" + DoubleToString(tp, digits));
            return true;
         }
         uint ret = m_trade.ResultRetcode();
         if(ret == 10004 || ret == 10005 || ret == 10006 || ret == 10016 || ret == 10030)
         {
            if(m_logger) m_logger.Warn("BUY retry " + IntegerToString(i+1) + "/" +
               IntegerToString(m_maxRetries) + " | Error=" + IntegerToString(ret));
            Sleep(m_retryDelayMs * (i + 1));
            continue;
         }
         if(m_logger) m_logger.Error("BUY failed | Error=" + IntegerToString(ret));
         return false;
      }
      return false;
   }

   bool OpenSell(double volume, double sl, double tp, string comment)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

      double price = NormalizeDouble(bid, digits);
      if(sl > 0) sl = NormalizeDouble(sl, digits);
      if(tp > 0) tp = NormalizeDouble(tp, digits);

      for(int i = 0; i < m_maxRetries; i++)
      {
         m_trade.SetDeviationInPoints(30);

         if(m_trade.Sell(volume, _Symbol, price, sl, tp, comment))
         {
            ulong ticket = m_trade.ResultOrder();
            if(m_logger) m_logger.Info("SELL opened | Ticket=" + IntegerToString(ticket) +
               " | Vol=" + DoubleToString(volume, 2) +
               " | Price=" + DoubleToString(price, digits) +
               " | SL=" + DoubleToString(sl, digits) +
               " | TP=" + DoubleToString(tp, digits));
            return true;
         }
         uint ret = m_trade.ResultRetcode();
         if(ret == 10004 || ret == 10005 || ret == 10006 || ret == 10016 || ret == 10030)
         {
            if(m_logger) m_logger.Warn("SELL retry " + IntegerToString(i+1) + "/" +
               IntegerToString(m_maxRetries) + " | Error=" + IntegerToString(ret));
            Sleep(m_retryDelayMs * (i + 1));
            continue;
         }
         if(m_logger) m_logger.Error("SELL failed | Error=" + IntegerToString(ret));
         return false;
      }
      return false;
   }

   bool ClosePosition(ulong ticket)
   {
      for(int i = 0; i < m_maxRetries; i++)
      {
         if(m_trade.PositionClose(ticket))
         {
            if(m_logger) m_logger.Info("Position closed | Ticket=" + IntegerToString(ticket));
            return true;
         }
         uint ret = m_trade.ResultRetcode();
         if(ret == 10004 || ret == 10016 || ret == 10030)
         {
            Sleep(m_retryDelayMs * (i + 1));
            continue;
         }
         if(m_logger) m_logger.Error("Close failed | Ticket=" + IntegerToString(ticket) +
            " | Error=" + IntegerToString(ret));
         return false;
      }
      return false;
   }

   bool CloseAllPositions(string symbol = "", ulong magic = 0)
   {
      int total = PositionsTotal();
      bool allOk = true;
      for(int i = total - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         if(symbol != "" && PositionGetString(POSITION_SYMBOL) != symbol) continue;
         if(magic > 0 && PositionGetInteger(POSITION_MAGIC) != (long)magic) continue;
         if(!ClosePosition(ticket)) allOk = false;
      }
      return allOk;
   }

   bool ModifySLTP(ulong ticket, double sl, double tp)
   {
      int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
      if(sl > 0) sl = NormalizeDouble(sl, digits);
      if(tp > 0) tp = NormalizeDouble(tp, digits);

      for(int i = 0; i < m_maxRetries; i++)
      {
         if(m_trade.PositionModify(ticket, sl, tp))
         {
            return true;
         }
         uint ret = m_trade.ResultRetcode();
         if(ret == 10004 || ret == 10016 || ret == 10030)
         {
            Sleep(m_retryDelayMs * (i + 1));
            continue;
         }
         return false;
      }
      return false;
   }
};

#endif
