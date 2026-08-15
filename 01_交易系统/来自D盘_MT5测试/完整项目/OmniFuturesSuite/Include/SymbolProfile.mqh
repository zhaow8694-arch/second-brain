#ifndef SYMBOL_PROFILE_MQH
#define SYMBOL_PROFILE_MQH

#include "OmniTypes.mqh"

SOmniProfile BuildOmniProfile(const ENUM_OMNI_PRODUCT product)
{
   SOmniProfile profile;
   profile.product = product;
   profile.displayName = OmniProductName(product);
   profile.maxSpreadPoints = 350.0;
   profile.trendAdxThreshold = 22.0;
   profile.rangeAdxThreshold = 18.0;
   profile.dangerAtrMultiplier = 2.8;
   profile.stableMinConfidence = 68.0;
   profile.aggressiveMinConfidence = 58.0;
   profile.trendSlAtr = 2.2;
   profile.trendTpAtr = 4.5;
   profile.rangeSlAtr = 1.3;
   profile.rangeTpAtr = 2.0;
   profile.breakevenAtr = 1.6;
   profile.trailingAtr = 1.5;
   profile.partialCloseAtr = 2.0;
   profile.partialCloseRatio = 0.50;
   profile.addOnAtrGap = 1.6;
   profile.hedgeLossAtr = 2.8;
   profile.maxSymbolRiskPctStable = 2.0;
   profile.maxSymbolRiskPctAggressive = 7.0;

   if(product == OMNI_GOLD)
   {
      profile.displayName = "Gold";
      profile.maxSpreadPoints = 350.0;
      profile.trendAdxThreshold = 23.0;
      profile.rangeAdxThreshold = 17.0;
      profile.dangerAtrMultiplier = 3.0;
      profile.trendSlAtr = 1.9;
      profile.trendTpAtr = 3.8;
      profile.rangeSlAtr = 1.4;
      profile.rangeTpAtr = 2.1;
      profile.breakevenAtr = 1.0;
      profile.trailingAtr = 1.2;
      profile.partialCloseAtr = 1.8;
      profile.addOnAtrGap = 1.8;
      profile.hedgeLossAtr = 3.0;
   }
   else if(product == OMNI_SPX500)
   {
      profile.displayName = "SPX500";
      profile.maxSpreadPoints = 300.0;
      profile.trendAdxThreshold = 20.0;
      profile.rangeAdxThreshold = 16.0;
      profile.dangerAtrMultiplier = 2.6;
      profile.stableMinConfidence = 70.0;
      profile.trendSlAtr = 2.0;
      profile.trendTpAtr = 4.2;
      profile.rangeSlAtr = 1.1;
      profile.rangeTpAtr = 1.8;
   }
   else if(product == OMNI_A50)
   {
      profile.displayName = "A50";
      profile.maxSpreadPoints = 400.0;
      profile.trendAdxThreshold = 26.0;
      profile.rangeAdxThreshold = 16.0;
      profile.dangerAtrMultiplier = 2.5;
      profile.stableMinConfidence = 74.0;
      profile.aggressiveMinConfidence = 62.0;
      profile.trendSlAtr = 2.5;
      profile.trendTpAtr = 4.0;
      profile.rangeSlAtr = 1.5;
      profile.rangeTpAtr = 1.8;
      profile.addOnAtrGap = 2.0;
   }
   else if(product == OMNI_USOIL)
   {
      profile.displayName = "USOIL";
      profile.maxSpreadPoints = 350.0;
      profile.trendAdxThreshold = 24.0;
      profile.rangeAdxThreshold = 17.0;
      profile.dangerAtrMultiplier = 2.4;
      profile.trendSlAtr = 2.6;
      profile.trendTpAtr = 4.8;
      profile.rangeSlAtr = 1.4;
      profile.rangeTpAtr = 2.0;
      profile.addOnAtrGap = 1.9;
      profile.hedgeLossAtr = 2.6;
   }

   return profile;
}

#endif
