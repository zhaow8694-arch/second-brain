#ifndef STABLE_STRATEGY_MQH
#define STABLE_STRATEGY_MQH

#include "OmniTypes.mqh"

class COmniStableStrategy
{
private:
   double ClampConfidence(const double value)
   {
      return MathMax(0.0, MathMin(100.0, value));
   }

   double BaseConfidence(const SOmniProfile &profile, const SOmniMarketSnapshot &snapshot)
   {
      double confidence = 50.0;
      if(snapshot.spreadPoints <= profile.maxSpreadPoints * 0.50) confidence += 10.0;
      else if(snapshot.spreadPoints <= profile.maxSpreadPoints * 0.80) confidence += 5.0;
      else confidence -= 10.0;

      if(snapshot.h4Adx >= profile.trendAdxThreshold) confidence += 10.0;
      if(snapshot.danger) confidence -= 40.0;
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
      signal.comment = "OmniStable " + OmniProductName(item.product);

      if(!snapshot.valid)
      {
         signal.reason = snapshot.reason;
         return false;
      }

      if(snapshot.regime == OMNI_REGIME_DANGER)
      {
         signal.reason = "danger candle filtered";
         return false;
      }

      SOmniProfile profile = item.profile;
      double confidence = BaseConfidence(profile, snapshot);

      if(snapshot.regime == OMNI_REGIME_TREND_UP &&
         snapshot.h1Close > snapshot.h1FastEma &&
         snapshot.h1FastEma > snapshot.h1SlowEma)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isTrend = true;
         signal.confidence = ClampConfidence(confidence + 18.0);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr;
         signal.reason = "H4 trend up + H1 EMA confirmation";
      }
      else if(snapshot.regime == OMNI_REGIME_TREND_DOWN &&
              snapshot.h1Close < snapshot.h1FastEma &&
              snapshot.h1FastEma < snapshot.h1SlowEma)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isTrend = true;
         signal.confidence = ClampConfidence(confidence + 18.0);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr;
         signal.reason = "H4 trend down + H1 EMA confirmation";
      }
      else if(snapshot.regime == OMNI_REGIME_RANGE &&
              snapshot.h1Close <= snapshot.h1BandLower &&
              snapshot.h1Rsi <= 34.0)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isRange = true;
         signal.confidence = ClampConfidence(confidence + 14.0);
         signal.slAtr = profile.rangeSlAtr;
         signal.tpAtr = profile.rangeTpAtr;
         signal.comment = "OmniStable RANGE " + OmniProductName(item.product);
         signal.reason = "H4 range + H1 lower band + RSI oversold";
      }
      else if(snapshot.regime == OMNI_REGIME_RANGE &&
              snapshot.h1Close >= snapshot.h1BandUpper &&
              snapshot.h1Rsi >= 66.0)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isRange = true;
         signal.confidence = ClampConfidence(confidence + 14.0);
         signal.slAtr = profile.rangeSlAtr;
         signal.tpAtr = profile.rangeTpAtr;
         signal.comment = "OmniStable RANGE " + OmniProductName(item.product);
         signal.reason = "H4 range + H1 upper band + RSI overbought";
      }
      else
      {
         signal.reason = "no stable setup";
         return false;
      }

      if(signal.confidence < profile.stableMinConfidence)
      {
         signal.reason = "confidence below stable threshold: " +
                         DoubleToString(signal.confidence, 1);
         signal.type = OMNI_SIGNAL_NONE;
         return false;
      }

      return true;
   }
};

#endif
