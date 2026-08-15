#ifndef RANGE_STRATEGY_MQH
#define RANGE_STRATEGY_MQH

#include "OmniTypes.mqh"

class COmniRangeStrategy
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

      if(snapshot.h4Adx <= profile.rangeAdxThreshold) confidence += 14.0;
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
      signal.comment = "OmniRange RANGE " + OmniProductName(item.product);

      if(!snapshot.valid)
      {
         signal.reason = snapshot.reason;
         return false;
      }

      if(snapshot.regime != OMNI_REGIME_RANGE)
      {
         signal.reason = "range strategy skipped: regime=" + OmniRegimeName(snapshot.regime);
         return false;
      }

      if(snapshot.danger)
      {
         signal.reason = "danger candle filtered";
         return false;
      }

      SOmniProfile profile = item.profile;
      double minMeanReversionZScore = 1.65;
      double maxRangeBandWidthAtrRatio = 8.0;
      double confidence = BaseConfidence(profile, snapshot);

      if(snapshot.h1BandWidthAtrRatio > maxRangeBandWidthAtrRatio)
      {
         signal.reason = "range skipped: band width/ATR too wide " +
                         DoubleToString(snapshot.h1BandWidthAtrRatio, 2);
         return false;
      }

      if(snapshot.h1Close <= snapshot.h1BandLower &&
         snapshot.h1Rsi <= 34.0 &&
         snapshot.h1ZScore <= -minMeanReversionZScore)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isRange = true;
         signal.confidence = ClampConfidence(confidence + 16.0 + MathMin(8.0, MathAbs(snapshot.h1ZScore)));
         signal.slAtr = profile.rangeSlAtr;
         signal.tpAtr = profile.rangeTpAtr;
         signal.reason = "range buy: lower band + RSI oversold + negative Z-Score";
      }
      else if(snapshot.h1Close >= snapshot.h1BandUpper &&
              snapshot.h1Rsi >= 66.0 &&
              snapshot.h1ZScore >= minMeanReversionZScore)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isRange = true;
         signal.confidence = ClampConfidence(confidence + 16.0 + MathMin(8.0, MathAbs(snapshot.h1ZScore)));
         signal.slAtr = profile.rangeSlAtr;
         signal.tpAtr = profile.rangeTpAtr;
         signal.reason = "range sell: upper band + RSI overbought + positive Z-Score";
      }
      else
      {
         signal.reason = "no range setup";
         return false;
      }

      if(signal.confidence < profile.stableMinConfidence)
      {
         signal.reason = "range confidence below threshold: " +
                         DoubleToString(signal.confidence, 1);
         signal.type = OMNI_SIGNAL_NONE;
         return false;
      }

      return true;
   }
};

#endif
