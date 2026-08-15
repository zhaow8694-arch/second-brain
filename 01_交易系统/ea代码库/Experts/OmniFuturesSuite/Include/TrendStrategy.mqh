#ifndef TREND_STRATEGY_MQH
#define TREND_STRATEGY_MQH

#include "OmniTypes.mqh"

class COmniTrendStrategy
{
private:
   double ClampConfidence(const double value)
   {
      return MathMax(0.0, MathMin(100.0, value));
   }

   double BaseConfidence(const SOmniProfile &profile,
                         const SOmniMarketSnapshot &snapshot)
   {
      double confidence = 52.0;
      if(snapshot.spreadPoints <= profile.maxSpreadPoints * 0.50) confidence += 10.0;
      else if(snapshot.spreadPoints <= profile.maxSpreadPoints * 0.80) confidence += 5.0;
      else confidence -= 12.0;

      if(snapshot.h4Adx >= profile.trendAdxThreshold) confidence += 14.0;
      if(snapshot.danger) confidence -= 45.0;
      return ClampConfidence(confidence);
   }

public:
   bool BuildSignal(const SOmniSymbol &item,
                    const SOmniMarketSnapshot &snapshot,
                    const double riskPct,
                    SOmniSignal &signal)
   {
      OmniResetSignal(signal);
      signal.product = item.product;
      signal.symbol = item.resolvedSymbol;
      signal.riskPct = riskPct;
      signal.comment = "OmniTrend TREND " + OmniProductName(item.product);

      if(!snapshot.valid)
      {
         signal.reason = snapshot.reason;
         return false;
      }

      if(snapshot.danger || snapshot.regime == OMNI_REGIME_DANGER)
      {
         signal.reason = "danger candle filtered";
         return false;
      }

      SOmniProfile profile = item.profile;
      double maxTrendEntryZScore = 2.00;
      double maxTrendDistanceAtr = 0.70;
      double minTrendBuyRsi = 45.0;
      double maxTrendBuyRsi = 68.0;
      double minTrendSellRsi = 32.0;
      double maxTrendSellRsi = 55.0;
      double confidence = BaseConfidence(profile, snapshot);
      double buyDistanceAtr = (snapshot.h1Atr > 0.0)
                              ? (snapshot.h1Close - snapshot.h1FastEma) / snapshot.h1Atr
                              : 999.0;
      double sellDistanceAtr = (snapshot.h1Atr > 0.0)
                               ? (snapshot.h1FastEma - snapshot.h1Close) / snapshot.h1Atr
                               : 999.0;

      if(snapshot.regime == OMNI_REGIME_TREND_UP &&
         snapshot.h1Close > snapshot.h1FastEma &&
         snapshot.h1FastEma > snapshot.h1SlowEma &&
         snapshot.h1Rsi >= minTrendBuyRsi &&
         snapshot.h1Rsi <= maxTrendBuyRsi &&
         snapshot.h1ZScore <= maxTrendEntryZScore &&
         buyDistanceAtr <= maxTrendDistanceAtr)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isTrend = true;
         signal.confidence = ClampConfidence(confidence + 18.0);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr;
         signal.reason = "trend buy: H4 up + H1 EMA confirmation";
      }
      else if(snapshot.regime == OMNI_REGIME_TREND_DOWN &&
              snapshot.h1Close < snapshot.h1FastEma &&
              snapshot.h1FastEma < snapshot.h1SlowEma &&
              snapshot.h1Rsi >= minTrendSellRsi &&
              snapshot.h1Rsi <= maxTrendSellRsi &&
              snapshot.h1ZScore >= -maxTrendEntryZScore &&
              sellDistanceAtr <= maxTrendDistanceAtr)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isTrend = true;
         signal.confidence = ClampConfidence(confidence + 18.0);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr;
         signal.reason = "trend sell: H4 down + H1 EMA confirmation";
      }
      else
      {
         signal.reason = "trend strategy skipped: regime=" + OmniRegimeName(snapshot.regime);
         return false;
      }

      if(signal.confidence < profile.stableMinConfidence)
      {
         signal.reason = "trend confidence below threshold: " +
                         DoubleToString(signal.confidence, 1);
         signal.type = OMNI_SIGNAL_NONE;
         return false;
      }

      return true;
   }
};

#endif
