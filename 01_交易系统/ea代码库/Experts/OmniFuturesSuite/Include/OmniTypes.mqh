#ifndef OMNI_TYPES_MQH
#define OMNI_TYPES_MQH

#define OMNI_PRODUCT_COUNT 4

enum ENUM_OMNI_PRODUCT
{
   OMNI_GOLD = 0,
   OMNI_SPX500 = 1,
   OMNI_A50 = 2,
   OMNI_USOIL = 3
};

enum ENUM_OMNI_ACCOUNT_SCALE
{
   OMNI_SCALE_AUTO = 0,
   OMNI_SCALE_STANDARD = 1,
   OMNI_SCALE_CENT_100X_BALANCE = 2,
   OMNI_SCALE_CUSTOM = 3
};

enum ENUM_OMNI_REGIME
{
   OMNI_REGIME_UNKNOWN = 0,
   OMNI_REGIME_TREND_UP = 1,
   OMNI_REGIME_TREND_DOWN = 2,
   OMNI_REGIME_RANGE = 3,
   OMNI_REGIME_DANGER = 4
};

enum ENUM_OMNI_SIGNAL
{
   OMNI_SIGNAL_NONE = 0,
   OMNI_SIGNAL_BUY = 1,
   OMNI_SIGNAL_SELL = -1,
   OMNI_SIGNAL_CLOSE = 2,
   OMNI_SIGNAL_HEDGE_BUY = 3,
   OMNI_SIGNAL_HEDGE_SELL = -3
};

struct SOmniProfile
{
   ENUM_OMNI_PRODUCT product;
   string displayName;
   double maxSpreadPoints;
   double trendAdxThreshold;
   double rangeAdxThreshold;
   double dangerAtrMultiplier;
   double stableMinConfidence;
   double aggressiveMinConfidence;
   double trendSlAtr;
   double trendTpAtr;
   double rangeSlAtr;
   double rangeTpAtr;
   double breakevenAtr;
   double trailingAtr;
   double partialCloseAtr;
   double partialCloseRatio;
   double addOnAtrGap;
   double hedgeLossAtr;
   double maxSymbolRiskPctStable;
   double maxSymbolRiskPctAggressive;
};

struct SOmniSymbol
{
   ENUM_OMNI_PRODUCT product;
   string logicalName;
   string inputSymbol;
   string resolvedSymbol;
   bool enabled;
   string disabledReason;
   SOmniProfile profile;
   datetime lastH1BarTime;
   datetime lastH4BarTime;
};

struct SOmniMarketSnapshot
{
   ENUM_OMNI_PRODUCT product;
   string symbol;
   bool valid;
   string reason;
   datetime h1BarTime;
   datetime h4BarTime;
   double bid;
   double ask;
   double spreadPoints;
   double h4Close;
   double h4FastEma;
   double h4SlowEma;
   double h4Adx;
   double h4Atr;
   double h1Close;
   double h1High;
   double h1Low;
   double h1FastEma;
   double h1SlowEma;
   double h1Atr;
   double h1Rsi;
   double h1BandUpper;
   double h1BandMiddle;
   double h1BandLower;
   double h1BandStdDev;
   double h1ZScore;
   double h1BandWidthAtrRatio;
   ENUM_OMNI_REGIME regime;
   bool danger;
};

struct SOmniSignal
{
   ENUM_OMNI_PRODUCT product;
   string symbol;
   ENUM_OMNI_SIGNAL type;
   bool isTrend;
   bool isRange;
   bool isAddOn;
   bool isHedge;
   double confidence;
   double riskPct;
   double slAtr;
   double tpAtr;
   string comment;
   string reason;
};

struct SOmniExposure
{
   int buyCount;
   int sellCount;
   int hedgeCount;
   double buyVolume;
   double sellVolume;
   double floatingProfit;
   double lastBuyPrice;
   double lastSellPrice;
   double maxBuyOpenPrice;
   double minSellOpenPrice;
};

struct SOmniRiskDecision
{
   bool allowed;
   string reason;
   double volume;
   double riskMoneyBroker;
   double effectiveRiskPct;
};

string OmniProductName(const ENUM_OMNI_PRODUCT product)
{
   if(product == OMNI_GOLD) return "Gold";
   if(product == OMNI_SPX500) return "SPX500";
   if(product == OMNI_A50) return "A50";
   if(product == OMNI_USOIL) return "USOIL";
   return "Unknown";
}

string OmniSignalName(const ENUM_OMNI_SIGNAL signal)
{
   if(signal == OMNI_SIGNAL_BUY) return "BUY";
   if(signal == OMNI_SIGNAL_SELL) return "SELL";
   if(signal == OMNI_SIGNAL_CLOSE) return "CLOSE";
   if(signal == OMNI_SIGNAL_HEDGE_BUY) return "HEDGE_BUY";
   if(signal == OMNI_SIGNAL_HEDGE_SELL) return "HEDGE_SELL";
   return "NONE";
}

string OmniRegimeName(const ENUM_OMNI_REGIME regime)
{
   if(regime == OMNI_REGIME_TREND_UP) return "TREND_UP";
   if(regime == OMNI_REGIME_TREND_DOWN) return "TREND_DOWN";
   if(regime == OMNI_REGIME_RANGE) return "RANGE";
   if(regime == OMNI_REGIME_DANGER) return "DANGER";
   return "UNKNOWN";
}

bool OmniIsBuySignal(const ENUM_OMNI_SIGNAL signal)
{
   return (signal == OMNI_SIGNAL_BUY || signal == OMNI_SIGNAL_HEDGE_BUY);
}

bool OmniIsSellSignal(const ENUM_OMNI_SIGNAL signal)
{
   return (signal == OMNI_SIGNAL_SELL || signal == OMNI_SIGNAL_HEDGE_SELL);
}

void OmniResetSignal(SOmniSignal &signal)
{
   signal.product = OMNI_GOLD;
   signal.symbol = "";
   signal.type = OMNI_SIGNAL_NONE;
   signal.isTrend = false;
   signal.isRange = false;
   signal.isAddOn = false;
   signal.isHedge = false;
   signal.confidence = 0.0;
   signal.riskPct = 0.0;
   signal.slAtr = 0.0;
   signal.tpAtr = 0.0;
   signal.comment = "";
   signal.reason = "";
}

void OmniResetExposure(SOmniExposure &exposure)
{
   exposure.buyCount = 0;
   exposure.sellCount = 0;
   exposure.hedgeCount = 0;
   exposure.buyVolume = 0.0;
   exposure.sellVolume = 0.0;
   exposure.floatingProfit = 0.0;
   exposure.lastBuyPrice = 0.0;
   exposure.lastSellPrice = 0.0;
   exposure.maxBuyOpenPrice = 0.0;
   exposure.minSellOpenPrice = 0.0;
}

#endif
