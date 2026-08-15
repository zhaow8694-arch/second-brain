#ifndef TRADE_EXECUTOR_MQH
#define TRADE_EXECUTOR_MQH

#include <Trade/Trade.mqh>
#include "OmniTypes.mqh"
#include "NotificationCenter.mqh"

class COmniTradeExecutor
{
private:
   CTrade trade;
   ulong magic;
   int deviationPoints;
   COmniNotificationCenter *notify;

   int VolumeDigits(const double step)
   {
      double value = step;
      int digits = 0;
      while(value < 1.0 && digits < 8)
      {
         value *= 10.0;
         digits++;
      }
      return digits;
   }

public:
   COmniTradeExecutor()
   {
      magic = 0;
      deviationPoints = 30;
      notify = NULL;
   }

   bool Init(const ulong magicNumber,
             const int slippagePoints,
             COmniNotificationCenter &notificationCenter)
   {
      magic = magicNumber;
      deviationPoints = slippagePoints;
      notify = &notificationCenter;
      trade.SetExpertMagicNumber(magic);
      trade.SetDeviationInPoints(deviationPoints);
      return true;
   }

   double NormalizeVolume(const string symbol, const double volume)
   {
      double minVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
      double maxVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
      double step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

      if(step <= 0.0) step = 0.01;
      double normalized = MathFloor(volume / step) * step;
      normalized = MathMax(minVolume, MathMin(maxVolume, normalized));
      return NormalizeDouble(normalized, VolumeDigits(step));
   }

   bool OpenMarket(const SOmniSignal &signal,
                   const double volume,
                   const double sl,
                   const double tp)
   {
      if(signal.symbol == "" || volume <= 0.0)
         return false;

      trade.SetExpertMagicNumber(magic);
      trade.SetDeviationInPoints(deviationPoints);
      trade.SetTypeFillingBySymbol(signal.symbol);

      string comment = signal.comment;
      if(comment == "")
         comment = "Omni " + OmniSignalName(signal.type);

      bool ok = false;
      if(OmniIsBuySignal(signal.type))
         ok = trade.Buy(volume, signal.symbol, 0.0, sl, tp, comment);
      else if(OmniIsSellSignal(signal.type))
         ok = trade.Sell(volume, signal.symbol, 0.0, sl, tp, comment);

      string detail = signal.symbol + " " + OmniSignalName(signal.type) +
                      " volume=" + DoubleToString(volume, 2) +
                      " sl=" + DoubleToString(sl, (int)SymbolInfoInteger(signal.symbol, SYMBOL_DIGITS)) +
                      " tp=" + DoubleToString(tp, (int)SymbolInfoInteger(signal.symbol, SYMBOL_DIGITS)) +
                      " retcode=" + IntegerToString((int)trade.ResultRetcode()) +
                      " " + trade.ResultRetcodeDescription();

      if(ok)
      {
         if(notify != NULL) notify.Trade("Opened " + detail);
      }
      else
      {
         if(notify != NULL) notify.Warn("Open failed " + detail);
      }
      return ok;
   }

   bool ModifyStops(const ulong ticket, const string symbol, const double sl, const double tp)
   {
      trade.SetExpertMagicNumber(magic);
      bool ok = trade.PositionModify(ticket, sl, tp);
      if(!ok && notify != NULL)
      {
         notify.Warn("Modify failed " + symbol +
                     " ticket=" + IntegerToString((long)ticket) +
                     " retcode=" + IntegerToString((int)trade.ResultRetcode()) +
                     " " + trade.ResultRetcodeDescription());
      }
      return ok;
   }

   bool ClosePositionTicket(const ulong ticket, const string reason)
   {
      trade.SetExpertMagicNumber(magic);
      bool ok = trade.PositionClose(ticket);
      if(notify != NULL)
      {
         string message = "Close ticket=" + IntegerToString((long)ticket) +
                          " reason=" + reason +
                          " retcode=" + IntegerToString((int)trade.ResultRetcode());
         if(ok) notify.Trade(message);
         else notify.Warn("Close failed " + message + " " + trade.ResultRetcodeDescription());
      }
      return ok;
   }

   bool ClosePartialTicket(const ulong ticket,
                           const string symbol,
                           const double volume,
                           const string reason)
   {
      double normalized = NormalizeVolume(symbol, volume);
      trade.SetExpertMagicNumber(magic);
      bool ok = trade.PositionClosePartial(ticket, normalized);
      if(notify != NULL)
      {
         string message = "Partial close " + symbol +
                          " ticket=" + IntegerToString((long)ticket) +
                          " volume=" + DoubleToString(normalized, 2) +
                          " reason=" + reason +
                          " retcode=" + IntegerToString((int)trade.ResultRetcode());
         if(ok) notify.Trade(message);
         else notify.Warn("Partial close failed " + message + " " + trade.ResultRetcodeDescription());
      }
      return ok;
   }

   int CountPositions(const string symbol)
   {
      int count = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != symbol) continue;
         if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;
         count++;
      }
      return count;
   }

   int CloseSymbolPositions(const string symbol, const string reason)
   {
      int closed = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) != symbol) continue;
         if((ulong)PositionGetInteger(POSITION_MAGIC) != magic) continue;
         if(ClosePositionTicket(ticket, reason))
            closed++;
      }
      return closed;
   }
};

#endif
