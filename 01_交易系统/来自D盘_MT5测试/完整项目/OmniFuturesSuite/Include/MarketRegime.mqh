#ifndef MARKET_REGIME_MQH
#define MARKET_REGIME_MQH

#include "OmniTypes.mqh"

class COmniMarketRegime
{
private:
   string symbol;
   SOmniProfile profile;
   int h4Fast;
   int h4Slow;
   int h4Adx;
   int h4Atr;
   int h1Fast;
   int h1Slow;
   int h1Atr;
   int h1Rsi;
   int h1Bands;

   bool ReadBuffer(const int handle, const int buffer, const int shift, double &value)
   {
      double data[];
      ArrayResize(data, 1);
      ArraySetAsSeries(data, true);
      int copied = CopyBuffer(handle, buffer, shift, 1, data);
      if(copied != 1)
         return false;
      value = data[0];
      return MathIsValidNumber(value);
   }

   bool ReadRates(const ENUM_TIMEFRAMES timeframe, MqlRates &rate)
   {
      MqlRates rates[];
      ArrayResize(rates, 2);
      ArraySetAsSeries(rates, true);
      int copied = CopyRates(symbol, timeframe, 0, 2, rates);
      if(copied < 2)
         return false;
      rate = rates[1];
      return true;
   }

public:
   COmniMarketRegime()
   {
      symbol = "";
      h4Fast = INVALID_HANDLE;
      h4Slow = INVALID_HANDLE;
      h4Adx = INVALID_HANDLE;
      h4Atr = INVALID_HANDLE;
      h1Fast = INVALID_HANDLE;
      h1Slow = INVALID_HANDLE;
      h1Atr = INVALID_HANDLE;
      h1Rsi = INVALID_HANDLE;
      h1Bands = INVALID_HANDLE;
   }

   bool Init(const string resolvedSymbol, const SOmniProfile &symbolProfile)
   {
      symbol = resolvedSymbol;
      profile = symbolProfile;

      h4Fast = iMA(symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
      h4Slow = iMA(symbol, PERIOD_H4, 200, 0, MODE_EMA, PRICE_CLOSE);
      h4Adx = iADX(symbol, PERIOD_H4, 14);
      h4Atr = iATR(symbol, PERIOD_H4, 14);
      h1Fast = iMA(symbol, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
      h1Slow = iMA(symbol, PERIOD_H1, 55, 0, MODE_EMA, PRICE_CLOSE);
      h1Atr = iATR(symbol, PERIOD_H1, 14);
      h1Rsi = iRSI(symbol, PERIOD_H1, 14, PRICE_CLOSE);
      h1Bands = iBands(symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE);

      return (h4Fast != INVALID_HANDLE && h4Slow != INVALID_HANDLE &&
              h4Adx != INVALID_HANDLE && h4Atr != INVALID_HANDLE &&
              h1Fast != INVALID_HANDLE && h1Slow != INVALID_HANDLE &&
              h1Atr != INVALID_HANDLE && h1Rsi != INVALID_HANDLE &&
              h1Bands != INVALID_HANDLE);
   }

   void Deinit()
   {
      if(h4Fast != INVALID_HANDLE) IndicatorRelease(h4Fast);
      if(h4Slow != INVALID_HANDLE) IndicatorRelease(h4Slow);
      if(h4Adx != INVALID_HANDLE) IndicatorRelease(h4Adx);
      if(h4Atr != INVALID_HANDLE) IndicatorRelease(h4Atr);
      if(h1Fast != INVALID_HANDLE) IndicatorRelease(h1Fast);
      if(h1Slow != INVALID_HANDLE) IndicatorRelease(h1Slow);
      if(h1Atr != INVALID_HANDLE) IndicatorRelease(h1Atr);
      if(h1Rsi != INVALID_HANDLE) IndicatorRelease(h1Rsi);
      if(h1Bands != INVALID_HANDLE) IndicatorRelease(h1Bands);
   }

   bool Refresh(SOmniMarketSnapshot &snapshot)
   {
      snapshot.symbol = symbol;
      snapshot.product = profile.product;
      snapshot.valid = false;
      snapshot.reason = "";
      snapshot.regime = OMNI_REGIME_UNKNOWN;
      snapshot.danger = false;
      snapshot.h1BandStdDev = 0.0;
      snapshot.h1ZScore = 0.0;
      snapshot.h1BandWidthAtrRatio = 0.0;

      MqlRates h4Rate;
      MqlRates h1Rate;
      if(!ReadRates(PERIOD_H4, h4Rate) || !ReadRates(PERIOD_H1, h1Rate))
      {
         snapshot.reason = "not enough H4/H1 bars";
         return false;
      }

      snapshot.h4BarTime = h4Rate.time;
      snapshot.h1BarTime = h1Rate.time;
      snapshot.h4Close = h4Rate.close;
      snapshot.h1Close = h1Rate.close;
      snapshot.h1High = h1Rate.high;
      snapshot.h1Low = h1Rate.low;
      snapshot.bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      snapshot.ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      if(point <= 0.0) point = _Point;
      snapshot.spreadPoints = (snapshot.ask - snapshot.bid) / point;

      if(!ReadBuffer(h4Fast, 0, 1, snapshot.h4FastEma) ||
         !ReadBuffer(h4Slow, 0, 1, snapshot.h4SlowEma) ||
         !ReadBuffer(h4Adx, 0, 1, snapshot.h4Adx) ||
         !ReadBuffer(h4Atr, 0, 1, snapshot.h4Atr) ||
         !ReadBuffer(h1Fast, 0, 1, snapshot.h1FastEma) ||
         !ReadBuffer(h1Slow, 0, 1, snapshot.h1SlowEma) ||
         !ReadBuffer(h1Atr, 0, 1, snapshot.h1Atr) ||
         !ReadBuffer(h1Rsi, 0, 1, snapshot.h1Rsi) ||
         !ReadBuffer(h1Bands, 0, 1, snapshot.h1BandMiddle) ||
         !ReadBuffer(h1Bands, 1, 1, snapshot.h1BandUpper) ||
         !ReadBuffer(h1Bands, 2, 1, snapshot.h1BandLower))
      {
         snapshot.reason = "indicator data unavailable";
         return false;
      }

      snapshot.h1BandStdDev = MathAbs(snapshot.h1BandUpper - snapshot.h1BandMiddle) / 2.0;
      if(snapshot.h1BandStdDev <= 0.0)
         snapshot.h1BandStdDev = MathAbs(snapshot.h1BandMiddle - snapshot.h1BandLower) / 2.0;

      if(snapshot.h1BandStdDev > 0.0)
         snapshot.h1ZScore = (snapshot.h1Close - snapshot.h1BandMiddle) / snapshot.h1BandStdDev;

      if(snapshot.h1Atr > 0.0)
         snapshot.h1BandWidthAtrRatio = (snapshot.h1BandUpper - snapshot.h1BandLower) / snapshot.h1Atr;

      double h1Range = snapshot.h1High - snapshot.h1Low;
      bool rangeSpike = (snapshot.h1Atr > 0.0 &&
                         h1Range > snapshot.h1Atr * profile.dangerAtrMultiplier);
      bool bandExpansion = (snapshot.h1BandWidthAtrRatio > 9.0);
      bool statisticalShock = (MathAbs(snapshot.h1ZScore) > 3.2);
      snapshot.danger = (rangeSpike || bandExpansion || statisticalShock);

      if(snapshot.danger)
      {
         snapshot.regime = OMNI_REGIME_DANGER;
      }
      else if(snapshot.h4Adx >= profile.trendAdxThreshold &&
              snapshot.h4Close > snapshot.h4FastEma &&
              snapshot.h4FastEma > snapshot.h4SlowEma)
      {
         snapshot.regime = OMNI_REGIME_TREND_UP;
      }
      else if(snapshot.h4Adx >= profile.trendAdxThreshold &&
              snapshot.h4Close < snapshot.h4FastEma &&
              snapshot.h4FastEma < snapshot.h4SlowEma)
      {
         snapshot.regime = OMNI_REGIME_TREND_DOWN;
      }
      else if(snapshot.h4Adx <= profile.rangeAdxThreshold)
      {
         snapshot.regime = OMNI_REGIME_RANGE;
      }
      else
      {
         snapshot.regime = OMNI_REGIME_UNKNOWN;
      }

      snapshot.valid = true;
      snapshot.reason = "ok";
      return true;
   }
};

#endif
