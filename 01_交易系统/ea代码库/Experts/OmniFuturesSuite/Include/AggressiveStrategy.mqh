#ifndef AGGRESSIVE_STRATEGY_MQH
#define AGGRESSIVE_STRATEGY_MQH

#include "OmniTypes.mqh"

class COmniAggressiveStrategy
{
private:
   double ClampConfidence(const double value)
   {
      return MathMax(0.0, MathMin(100.0, value));
   }

   bool BuildInitial(const SOmniSymbol &item,
                     const SOmniMarketSnapshot &snapshot,
                     const double riskPct,
                     SOmniSignal &signal)
   {
      SOmniProfile profile = item.profile;
      double confidence = 52.0;
      if(snapshot.spreadPoints < profile.maxSpreadPoints * 0.75) confidence += 8.0;
      if(snapshot.h4Adx >= profile.trendAdxThreshold) confidence += 12.0;
      if(snapshot.danger) confidence -= 35.0;

      if(snapshot.regime == OMNI_REGIME_TREND_UP &&
         snapshot.h1Close > snapshot.h1FastEma)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isTrend = true;
         signal.confidence = ClampConfidence(confidence + 12.0);
         signal.reason = "aggressive trend buy";
      }
      else if(snapshot.regime == OMNI_REGIME_TREND_DOWN &&
              snapshot.h1Close < snapshot.h1FastEma)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isTrend = true;
         signal.confidence = ClampConfidence(confidence + 12.0);
         signal.reason = "aggressive trend sell";
      }
      else if(snapshot.regime == OMNI_REGIME_RANGE &&
              snapshot.h1Close <= snapshot.h1BandLower &&
              snapshot.h1Rsi <= 38.0)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isRange = true;
         signal.confidence = ClampConfidence(confidence + 8.0);
         signal.reason = "aggressive range buy";
      }
      else if(snapshot.regime == OMNI_REGIME_RANGE &&
              snapshot.h1Close >= snapshot.h1BandUpper &&
              snapshot.h1Rsi >= 62.0)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isRange = true;
         signal.confidence = ClampConfidence(confidence + 8.0);
         signal.reason = "aggressive range sell";
      }
      else
      {
         return false;
      }

      signal.product = item.product;
      signal.symbol = item.resolvedSymbol;
      signal.riskPct = riskPct;
      signal.slAtr = signal.isRange ? profile.rangeSlAtr : profile.trendSlAtr;
      signal.tpAtr = signal.isRange ? profile.rangeTpAtr : profile.trendTpAtr;
      signal.comment = "OmniAggressive " + (signal.isRange ? "RANGE " : "TREND ") +
                       OmniProductName(item.product);
      return true;
   }

public:
   bool BuildSignal(const SOmniSymbol &item,
                    const SOmniMarketSnapshot &snapshot,
                    const SOmniExposure &exposure,
                    const double riskPct,
                    const bool allowAddOn,
                    const bool allowHedge,
                    const int maxAddOnLayers,
                    SOmniSignal &signal)
   {
      OmniResetSignal(signal);
      signal.product = item.product;
      signal.symbol = item.resolvedSymbol;
      signal.riskPct = riskPct;

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

      if(allowHedge && exposure.buyCount > 0 &&
         snapshot.regime == OMNI_REGIME_TREND_DOWN &&
         exposure.floatingProfit < 0.0 &&
         exposure.hedgeCount < 1)
      {
         signal.type = OMNI_SIGNAL_HEDGE_SELL;
         signal.isHedge = true;
         signal.confidence = 78.0;
         signal.riskPct = MathMax(0.20, riskPct * 0.65);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr * 0.70;
         signal.comment = "OmniAggressive HEDGE " + OmniProductName(item.product);
         signal.reason = "protective hedge sell: long exposure + H4 down";
         return true;
      }

      if(allowHedge && exposure.sellCount > 0 &&
         snapshot.regime == OMNI_REGIME_TREND_UP &&
         exposure.floatingProfit < 0.0 &&
         exposure.hedgeCount < 1)
      {
         signal.type = OMNI_SIGNAL_HEDGE_BUY;
         signal.isHedge = true;
         signal.confidence = 78.0;
         signal.riskPct = MathMax(0.20, riskPct * 0.65);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr * 0.70;
         signal.comment = "OmniAggressive HEDGE " + OmniProductName(item.product);
         signal.reason = "protective hedge buy: short exposure + H4 up";
         return true;
      }

      if(allowAddOn && exposure.buyCount > 0 && exposure.buyCount < maxAddOnLayers + 1 &&
         exposure.floatingProfit > 0.0 &&
         snapshot.regime == OMNI_REGIME_TREND_UP &&
         exposure.maxBuyOpenPrice > 0.0 &&
         snapshot.bid - exposure.maxBuyOpenPrice >= snapshot.h1Atr * profile.addOnAtrGap)
      {
         signal.type = OMNI_SIGNAL_BUY;
         signal.isTrend = true;
         signal.isAddOn = true;
         signal.confidence = 72.0;
         signal.riskPct = MathMax(0.20, riskPct * 0.70);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr;
         signal.comment = "OmniAggressive ADDON " + OmniProductName(item.product);
         signal.reason = "allowAddOn trend buy: profit and ATR gap";
         return true;
      }

      if(allowAddOn && exposure.sellCount > 0 && exposure.sellCount < maxAddOnLayers + 1 &&
         exposure.floatingProfit > 0.0 &&
         snapshot.regime == OMNI_REGIME_TREND_DOWN &&
         exposure.minSellOpenPrice > 0.0 &&
         exposure.minSellOpenPrice - snapshot.ask >= snapshot.h1Atr * profile.addOnAtrGap)
      {
         signal.type = OMNI_SIGNAL_SELL;
         signal.isTrend = true;
         signal.isAddOn = true;
         signal.confidence = 72.0;
         signal.riskPct = MathMax(0.20, riskPct * 0.70);
         signal.slAtr = profile.trendSlAtr;
         signal.tpAtr = profile.trendTpAtr;
         signal.comment = "OmniAggressive ADDON " + OmniProductName(item.product);
         signal.reason = "allowAddOn trend sell: profit and ATR gap";
         return true;
      }

      if(exposure.buyCount == 0 && exposure.sellCount == 0)
      {
         if(!BuildInitial(item, snapshot, riskPct, signal))
            return false;
         if(signal.confidence < profile.aggressiveMinConfidence)
         {
            signal.reason = "confidence below aggressive threshold";
            signal.type = OMNI_SIGNAL_NONE;
            return false;
         }
         return true;
      }

      signal.reason = "existing exposure, no add-on or hedge condition";
      return false;
   }
};

#endif
