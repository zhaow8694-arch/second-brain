#property strict

//---
// Expert Advisor derived from:
//   Heatmap Trailing Stop with Breakouts (Zeiierman) - Pine Script v6
// Functional focus:
//   Recreates breakout signal logic and ATR-based trailing stop behaviour
//   for automated trading on MetaTrader 4.
//---

extern double   InpLots                = 0.01;
extern int      InpMaxPositionsPerDirection = 5;
extern int      InpSlippage            = 3;
extern int      InpMagic               = 863451;
extern bool     InpAllowBuy            = true;
extern bool     InpAllowSell           = true;
extern bool     InpCloseOnReverse      = true;

extern int      InpStopAtrLength       = 28;
extern double   InpStopMultiplier      = 5.0;
extern int      InpHeatAtrLength       = 50;
extern int      InpHeatLevels          = 3;   // max 15 internally
extern int      InpHeatTouchThreshold  = 3;

extern int      InpScoreThreshold      = 6;
extern int      InpCooldownBars        = 20;
extern ENUM_TIMEFRAMES InpSignalTF     = PERIOD_CURRENT;

extern bool     InpUseTrailingStop     = true;
extern double   InpMinStopStepPoints   = 10;  // minimum distance required to move SL (in points)

//--- internal state
double gTrendUp        = 0.0;
double gTrendDown      = 0.0;
double gExtreme        = 0.0;
int    gTrendDir       = 1;
bool   gStateInitialised = false;

int    gLastLongBarIdx  = -1;
int    gLastShortBarIdx = -1;
datetime gLastProcessedBarTime = 0;

//--- diagnostics
int gRawLongHits          = 0;
int gRawShortHits         = 0;
int gScorePassLong        = 0;
int gScorePassShort       = 0;
int gScoreFailLong        = 0;
int gScoreFailShort       = 0;
int gCooldownBlockLong    = 0;
int gCooldownBlockShort   = 0;
int gSignalLongCount      = 0;
int gSignalShortCount     = 0;
int gProcessedBars        = 0;

//--- utilities --------------------------------------------------------------------------------------------------------

int    LimitHeatLevels()          { return MathMax(2, MathMin(15, InpHeatLevels)); }
double PointInPrice(double price) { return NormalizeDouble(price, (double)Digits); }

double TrueRange(int shift)
{
   if(Bars <= shift + 1) return 0.0;
   double high = iHigh(NULL, 0, shift);
   double low  = iLow(NULL, 0, shift);
   double prevClose = iClose(NULL, 0, shift + 1);
   double range1 = high - low;
   double range2 = MathAbs(high - prevClose);
   double range3 = MathAbs(low  - prevClose);
   return MathMax(range1, MathMax(range2, range3));
}

double EmaTrueRange(int period, int shift)
{
   if(period < 1) return 0.0;
   int start = shift + period + 1;
   if(Bars <= start) return 0.0;

   double alpha = 2.0 / (period + 1.0);
   double ema   = TrueRange(start);

   for(int i = start - 1; i >= shift; i--)
   {
      double tr = TrueRange(i);
      ema = alpha * tr + (1.0 - alpha) * ema;
   }
   return ema;
}

bool HasEnoughBars()
{
   int minBars = MathMax(InpStopAtrLength + 5, InpHeatAtrLength + 5);
   return Bars > minBars;
}

int CurrentBarIndex(int shift)
{
   return Bars - shift - 1;
}

double CountToScore(int count)
{
   double raw  = (double(count) - InpHeatTouchThreshold) / 10.0;
   double norm = MathMin(MathMax(raw, 0.0), 1.0);
   return MathRound(1.0 + norm * 9.0);
}

double ScoreFromLevels(double value, double &levels[], int &counts[], bool &valid[], int total)
{
   double bestScore = 1.0;
   double minDist   = 1e10;
   for(int i = 0; i < total; i++)
   {
      if(!valid[i]) continue;
      double dist = MathAbs(value - levels[i]);
      if(dist < minDist)
      {
         minDist   = dist;
         bestScore = CountToScore(counts[i]);
      }
   }
   return bestScore;
}

bool FetchHTFData(int shift, double &o, double &h, double &l, double &c, double &h1, double &h2, double &l1, double &l2)
{
   ENUM_TIMEFRAMES tf = InpSignalTF;
   if(tf == PERIOD_CURRENT)
   {
      if(Bars <= shift + 2) return false;
      o  = iOpen (NULL, tf, shift);
      h  = iHigh (NULL, tf, shift);
      l  = iLow  (NULL, tf, shift);
      c  = iClose(NULL, tf, shift);
      h1 = iHigh (NULL, tf, shift + 1);
      h2 = iHigh (NULL, tf, shift + 2);
      l1 = iLow  (NULL, tf, shift + 1);
      l2 = iLow  (NULL, tf, shift + 2);
      return true;
   }

   datetime barTime = Time[shift];
   int htfShift = iBarShift(NULL, tf, barTime, true);
   if(htfShift < 0) return false;
   if(iBars(NULL, tf) <= htfShift + 2) return false;

   o  = iOpen (NULL, tf, htfShift);
   h  = iHigh (NULL, tf, htfShift);
   l  = iLow  (NULL, tf, htfShift);
   c  = iClose(NULL, tf, htfShift);
   h1 = iHigh (NULL, tf, htfShift + 1);
   h2 = iHigh (NULL, tf, htfShift + 2);
   l1 = iLow  (NULL, tf, htfShift + 1);
   l2 = iLow  (NULL, tf, htfShift + 2);
   return true;
}

void CloseOppositePositions(int direction)
{
   if(!InpCloseOnReverse) return;
   int total = OrdersTotal();
   for(int i = total - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != InpMagic) continue;
      if(direction > 0 && OrderType() == OP_SELL)
      {
         double ask = MarketInfo(Symbol(), MODE_ASK);
         OrderClose(OrderTicket(), OrderLots(), ask, InpSlippage, clrRed);
      }
      else if(direction < 0 && OrderType() == OP_BUY)
      {
         double bid = MarketInfo(Symbol(), MODE_BID);
         OrderClose(OrderTicket(), OrderLots(), bid, InpSlippage, clrRed);
      }
   }
}

void OpenTrade(int direction, double stopLevel)
{
   if(direction > 0 && !InpAllowBuy)  return;
   if(direction < 0 && !InpAllowSell) return;

   double lots = InpLots;
   double ask  = MarketInfo(Symbol(), MODE_ASK);
   double bid  = MarketInfo(Symbol(), MODE_BID);

   if(direction > 0)
   {
      double sl = (stopLevel > 0.0) ? PointInPrice(stopLevel) : 0.0;
      if(OrderSend(Symbol(), OP_BUY, lots, ask, InpSlippage, sl, 0.0, "Heatmap Breakout Buy", InpMagic, 0, clrLime) < 0)
         Print("Failed to open BUY: ", GetLastError());
   }
   else if(direction < 0)
   {
      double sl = (stopLevel > 0.0) ? PointInPrice(stopLevel) : 0.0;
      if(OrderSend(Symbol(), OP_SELL, lots, bid, InpSlippage, sl, 0.0, "Heatmap Breakout Sell", InpMagic, 0, clrRed) < 0)
         Print("Failed to open SELL: ", GetLastError());
   }
}

void UpdateTrailingStops(double longStop, double shortStop)
{
   if(!InpUseTrailingStop) return;
   double minStep = InpMinStopStepPoints * Point;

   int total = OrdersTotal();
   for(int i = total - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != InpMagic) continue;

      if(OrderType() == OP_BUY && longStop > 0.0)
      {
         double newSL = PointInPrice(longStop);
         if(newSL < Bid - minStep)
         {
            if(OrderStopLoss() < newSL - Point/2.0)
               OrderModify(OrderTicket(), OrderOpenPrice(), newSL, OrderTakeProfit(), 0, clrLime);
         }
      }
      else if(OrderType() == OP_SELL && shortStop > 0.0)
      {
         double newSL = PointInPrice(shortStop);
         if(newSL > Ask + minStep)
         {
            if(OrderStopLoss() == 0.0 || OrderStopLoss() > newSL + Point/2.0)
               OrderModify(OrderTicket(), OrderOpenPrice(), newSL, OrderTakeProfit(), 0, clrRed);
         }
      }
   }
}

int CountOpenPositions(int direction)
{
   int count = 0;
   int total = OrdersTotal();
   for(int i = 0; i < total; i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != InpMagic) continue;
      if(direction > 0 && OrderType() == OP_BUY)
         count++;
      else if(direction < 0 && OrderType() == OP_SELL)
         count++;
   }
   return count;
}

void UpdateDiagnosticsComment()
{
   string text =
      "Processed bars: " + IntegerToString(gProcessedBars) +
      "\nLong raw: "    + IntegerToString(gRawLongHits)    +
      " pass: "         + IntegerToString(gScorePassLong)  +
      " fail: "         + IntegerToString(gScoreFailLong)  +
      " cooldown block: " + IntegerToString(gCooldownBlockLong) +
      " signals: "      + IntegerToString(gSignalLongCount) +
      "\nShort raw: "   + IntegerToString(gRawShortHits)   +
      " pass: "         + IntegerToString(gScorePassShort) +
      " fail: "         + IntegerToString(gScoreFailShort) +
      " cooldown block: " + IntegerToString(gCooldownBlockShort) +
      " signals: "      + IntegerToString(gSignalShortCount);
   Comment(text);
}

//--- core logic -------------------------------------------------------------------------------------------------------

void ProcessBar(int shift)
{
   if(!HasEnoughBars()) return;

   gProcessedBars++;

   double closeCurr = iClose(NULL, 0, shift);
   double closePrev = iClose(NULL, 0, shift + 1);
   double highCurr  = iHigh (NULL, 0, shift);
   double lowCurr   = iLow  (NULL, 0, shift);

   double atrTrail  = EmaTrueRange(InpStopAtrLength, shift);
   double stopOffset = InpStopMultiplier * atrTrail;
   double bullStop   = highCurr - stopOffset;
   double bearStop   = lowCurr  + stopOffset;

   double prevTrendUp   = gTrendUp;
   double prevTrendDown = gTrendDown;
   int    prevTrendDir  = gTrendDir;
   double prevExtreme   = gExtreme;

   if(!gStateInitialised || prevTrendUp == 0.0 || prevTrendDown == 0.0)
   {
      prevTrendUp   = bullStop;
      prevTrendDown = bearStop;
      prevTrendDir  = (closeCurr >= closePrev) ? 1 : -1;
      prevExtreme   = (prevTrendDir == 1) ? highCurr : lowCurr;
      gStateInitialised = true;
   }

   double trendUp   = (closePrev > prevTrendUp)   ? MathMax(bullStop, prevTrendUp)   : bullStop;
   double trendDown = (closePrev < prevTrendDown) ? MathMin(bearStop, prevTrendDown) : bearStop;

   int trendDir;
   if(closeCurr > prevTrendDown)      trendDir = 1;
   else if(closeCurr < prevTrendUp)   trendDir = -1;
   else                               trendDir = (prevTrendDir != 0) ? prevTrendDir : 1;

   bool bullFlip = (trendDir == 1  && prevTrendDir == -1);
   bool bearFlip = (trendDir == -1 && prevTrendDir == 1);

   double extreme;
   if(trendDir != prevTrendDir)
      extreme = (trendDir == 1) ? highCurr : lowCurr;
   else if(trendDir == 1)
      extreme = MathMax(prevExtreme, highCurr);
   else
      extreme = MathMin(prevExtreme, lowCurr);

   double trail = (trendDir == 1) ? trendUp : trendDown;

   double fib61 = extreme + (trail - extreme) * 0.618;
   double fib78 = extreme + (trail - extreme) * 0.786;
   double fib88 = extreme + (trail - extreme) * 0.886;
   double l100  = trail;

   double highest = highCurr;
   double lowest  = lowCurr;
   for(int i = 1; i < InpHeatAtrLength; i++)
   {
      double h = iHigh(NULL, 0, shift + i);
      double l = iLow (NULL, 0, shift + i);
      highest = MathMax(highest, h);
      lowest  = MathMin(lowest, l);
   }
   double range = highest - lowest;
   double step  = (LimitHeatLevels() > 0) ? range / LimitHeatLevels() : 0.0;

   double levelValues[15];
   int    levelCounts[15];
   bool   levelValid[15];
   ArrayInitialize(levelValues, 0.0);
   ArrayInitialize(levelCounts, 0);
   ArrayInitialize(levelValid , false);

   int levels = LimitHeatLevels();
   for(int i = 0; i < 15; i++)
   {
      if(i >= levels)
      {
         levelValid[i] = false;
         continue;
      }

      double lvl = lowest + step * i;
      int touches = 0;
      for(int j = 0; j <= InpHeatAtrLength; j++)
      {
         int idx = shift + j;
         if(idx >= Bars) break;
         double hh = iHigh(NULL, 0, idx);
         double ll = iLow (NULL, 0, idx);
         if(hh >= lvl && ll <= lvl)
            touches++;
      }

      levelValues[i] = lvl;
      levelCounts[i] = touches;
      levelValid[i]  = true;
   }

   double scoreTrail = ScoreFromLevels(trail, levelValues, levelCounts, levelValid, 15);
   double score61    = ScoreFromLevels(fib61, levelValues, levelCounts, levelValid, 15);
   double score78    = ScoreFromLevels(fib78, levelValues, levelCounts, levelValid, 15);
   double score88    = ScoreFromLevels(fib88, levelValues, levelCounts, levelValid, 15);
   double scoreL100  = ScoreFromLevels(l100 , levelValues, levelCounts, levelValid, 15);

   double score = (scoreTrail + score61 + score78 + score88 + scoreL100) / 5.0;

   double o, h, l, c, h1, h2, l1, l2;
   if(!FetchHTFData(shift, o, h, l, c, h1, h2, l1, l2))
      return;

   bool bull = (c > o) && ((c - o) > (h - l) * 0.5);
   bool bear = (c < o) && ((o - c) > (h - l) * 0.5);
   bool momUp = (c > h1) && (c > h2);
   bool momDn = (c < l1) && (c < l2);

   bool rawLong  = bull && momUp && (trendDir == 1);
   bool rawShort = bear && momDn && (trendDir == -1);

   if(rawLong)
   {
      gRawLongHits++;
      if(score > InpScoreThreshold) gScorePassLong++;
      else                          gScoreFailLong++;
   }
   if(rawShort)
   {
      gRawShortHits++;
      if(score > InpScoreThreshold) gScorePassShort++;
      else                          gScoreFailShort++;
   }

   int barIdx = CurrentBarIndex(shift);
   bool cooldownLong  = (gLastLongBarIdx < 0)  || (barIdx - gLastLongBarIdx > InpCooldownBars)  || (gLastShortBarIdx > gLastLongBarIdx);
   bool cooldownShort = (gLastShortBarIdx < 0) || (barIdx - gLastShortBarIdx > InpCooldownBars) || (gLastLongBarIdx > gLastShortBarIdx);

   bool signalLong  = rawLong  && cooldownLong  && (score > InpScoreThreshold);
   bool signalShort = rawShort && cooldownShort && (score > InpScoreThreshold);

   if(signalLong)
   {
      gLastLongBarIdx = barIdx;
      CloseOppositePositions(+1);
      int desiredLongs = MathMax(0, InpMaxPositionsPerDirection);
      int currentLongs = CountOpenPositions(+1);
      for(int k = currentLongs; k < desiredLongs; k++)
         OpenTrade(+1, trendUp);
      gSignalLongCount++;
   }
   else if(rawLong && (score > InpScoreThreshold) && !cooldownLong)
   {
      gCooldownBlockLong++;
   }
   if(signalShort)
   {
      gLastShortBarIdx = barIdx;
      CloseOppositePositions(-1);
      int desiredShorts = MathMax(0, InpMaxPositionsPerDirection);
      int currentShorts = CountOpenPositions(-1);
      for(int k = currentShorts; k < desiredShorts; k++)
         OpenTrade(-1, trendDown);
      gSignalShortCount++;
   }
   else if(rawShort && (score > InpScoreThreshold) && !cooldownShort)
   {
      gCooldownBlockShort++;
   }

   if(signalLong || signalShort)
      Print("Signal generated. Score=", DoubleToString(score, 2), " TrendDir=", trendDir);

   gTrendUp   = trendUp;
   gTrendDown = trendDown;
   gTrendDir  = trendDir;
   gExtreme   = extreme;

   UpdateTrailingStops(trendUp, trendDown);
}

//--- MT4 entry points -------------------------------------------------------------------------------------------------

int OnInit()
{
   if(!HasEnoughBars())
      Print("Warning: not enough bars yet for reliable calculations.");
   gTrendUp = gTrendDown = gExtreme = 0.0;
   gTrendDir = 1;
   gStateInitialised = false;
   gLastProcessedBarTime = 0;
   gRawLongHits = gRawShortHits = 0;
   gScorePassLong = gScorePassShort = 0;
   gScoreFailLong = gScoreFailShort = 0;
   gCooldownBlockLong = gCooldownBlockShort = 0;
   gSignalLongCount = gSignalShortCount = 0;
   gProcessedBars = 0;
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   if(!HasEnoughBars()) return;
   datetime lastBarTime = iTime(NULL, 0, 1);
   if(lastBarTime != gLastProcessedBarTime)
   {
      gLastProcessedBarTime = lastBarTime;
      ProcessBar(1);
   }
   else if(InpUseTrailingStop)
   {
      UpdateTrailingStops(gTrendUp, gTrendDown);
   }
   UpdateDiagnosticsComment();
}

void OnDeinit(const int reason)
{
   // Nothing to clean up
   Comment("");
}


