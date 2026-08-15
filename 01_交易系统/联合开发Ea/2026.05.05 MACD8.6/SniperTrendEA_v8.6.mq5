//+------------------------------------------------------------------+
//|                                          SniperTrendEA_v8.6.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                    v8.6 - ATR动态止盈版（最优解 TP=9.5）           |
//|                                                                  |
//|  唯一改动：开仓即设止盈 = 9.5 × ATR                               |
//|  入场逻辑 = v8.5 方案A 完全相同                                    |
//|                                                                  |
//|  十年全期 (2015-2025, H4, XAUUSD):                                 |
//|    PF 2.76  |  回撤 16.04%  |  采收 5.20  |  夏普 2.02            |
//|    TP=9.5 为灵敏度扫描最优值 (8.0~10.0 全部 PF>2.27, 参数稳健)      |
//|                                                                  |
//|  已知局限：震荡年 PF<1.5, 策略仅趋势年有效                          |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.6 - TP=9.5 Optimal"
#property version   "8.60"
#property strict

input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 趋势过滤（v8.5: Buffer 改用 ATR 倍数）==="
input int    InpMA200Period    = 200;
input bool   InpUseMA200Filter = true;
input double InpMA200BufferATR = 0.45;

input group "=== 入场质量过滤（v8trae 增强 Z-Wei 哲学）==="
input double InpBodyRatio          = 0.60;
input double InpMaxCandleATR       = 3.0;
input double InpDangerSuddenRatio  = 2.0;
input double InpMaxOppositeShadow  = 0.20;
input bool   InpRequireFollowThrough = false;
input int    InpFollowThroughBars  = 3;
input int    InpConfirmBars        = 4;
input bool   InpRequireMACDDir     = false;
input bool   InpRequireMomentumShift = true;

input group "=== v8.6 出场增强 ==="
input bool   InpUseBreakeven      = false;
input double InpBreakevenATR      = 3.0;
input double InpTakeProfitATR     = 9.5;

input group "=== ADX 趋势过滤 (v8.4) ==="
input bool   InpUseADX          = false;
input int    InpADXPeriod       = 14;
input double InpADXThreshold    = 25.0;

input group "=== 时间过滤 (v8.4) ==="
input bool   InpUseTimeFilter   = false;
input int    InpStartHour       = 8;
input int    InpEndHour         = 20;

input group "=== 波动率过滤 (v8.4) ==="
input bool   InpUseATRFilter    = false;
input int    InpATRFilterPeriod = 20;
input double InpATRFilterRatio  = 1.0;

input group "=== 日线趋势确认 (v8.4) ==="
input bool   InpUseDailyFilter  = false;

input group "=== 风险管理 ==="
input double InpRiskPercent    = 0.5;
input double InpATRMultiplier  = 1.5;
input int    InpATRPeriod      = 14;
input double InpTrailingStart  = 5.0;
input double InpTrailingStep   = 2.5;
input int    InpMaxPositions   = 1;

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260506;
input string InpComment        = "SniperEA_v8.6";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;
int g_adxHandle = INVALID_HANDLE;
int g_atrFilterHandle = INVALID_HANDLE;
int g_dailyMA200Handle = INVALID_HANDLE;

bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

int OnInit()
{
   g_macdHandle = iMACD(_Symbol, PERIOD_CURRENT, InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
   if(g_macdHandle == INVALID_HANDLE) return INIT_FAILED;

   g_atrHandle = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   if(g_atrHandle == INVALID_HANDLE) return INIT_FAILED;

   g_ma200Handle = iMA(_Symbol, PERIOD_CURRENT, InpMA200Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_ma200Handle == INVALID_HANDLE) return INIT_FAILED;

   if(InpUseADX)
   {
      g_adxHandle = iADX(_Symbol, PERIOD_CURRENT, InpADXPeriod);
      if(g_adxHandle == INVALID_HANDLE) return INIT_FAILED;
   }

   if(InpUseATRFilter)
   {
      g_atrFilterHandle = iMA(_Symbol, PERIOD_CURRENT, InpATRFilterPeriod, 0, MODE_SMA, g_atrHandle);
      if(g_atrFilterHandle == INVALID_HANDLE) return INIT_FAILED;
   }

   if(InpUseDailyFilter)
   {
      g_dailyMA200Handle = iMA(_Symbol, PERIOD_D1, 200, 0, MODE_SMA, PRICE_CLOSE);
      if(g_dailyMA200Handle == INVALID_HANDLE) return INIT_FAILED;
   }

   g_pendingBuy       = false;
   g_pendingSell      = false;
   g_pendingBars      = 0;
   g_lastTrailBarTime = 0;
   g_lastEntryBarTime = 0;

   Print("SniperTrendEA v8.6 初始化成功 | ", _Symbol, " ", EnumToString(Period()),
         " | TP:", InpTakeProfitATR, "xATR",
         " | Shadow:", DoubleToString(InpMaxOppositeShadow * 100, 0), "%",
         " | MS:", InpRequireMomentumShift ? "ON" : "OFF");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_macdHandle  != INVALID_HANDLE) IndicatorRelease(g_macdHandle);
   if(g_atrHandle   != INVALID_HANDLE) IndicatorRelease(g_atrHandle);
   if(g_ma200Handle != INVALID_HANDLE) IndicatorRelease(g_ma200Handle);
   if(g_adxHandle   != INVALID_HANDLE) IndicatorRelease(g_adxHandle);
   if(g_atrFilterHandle  != INVALID_HANDLE) IndicatorRelease(g_atrFilterHandle);
   if(g_dailyMA200Handle != INVALID_HANDLE) IndicatorRelease(g_dailyMA200Handle);
   Comment("");
}

void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == 0) return;

   double macdMain[], macdSig[], atrBuf2[], ma200Buf[];
   ArrayResize(macdMain, 4); ArrayResize(macdSig, 4); ArrayResize(atrBuf2, 4); ArrayResize(ma200Buf, 3);
   ArraySetAsSeries(macdMain, true); ArraySetAsSeries(macdSig, true);
   ArraySetAsSeries(atrBuf2, true); ArraySetAsSeries(ma200Buf, true);

   if(CopyBuffer(g_macdHandle, 0, 0, 4, macdMain) < 4 ||
      CopyBuffer(g_macdHandle, 1, 0, 4, macdSig) < 4 ||
      CopyBuffer(g_atrHandle, 0, 0, 4, atrBuf2) < 4 ||
      CopyBuffer(g_ma200Handle, 0, 0, 3, ma200Buf) < 3) return;

   double hist1 = macdMain[1] - macdSig[1];
   double hist2 = macdMain[2] - macdSig[2];
   double macd1 = macdMain[1];
   double macd2 = macdMain[2];
   double atr1  = atrBuf2[1];
   double ma200 = ma200Buf[1];

   if(atr1 <= 0 || ma200 <= 0) return;

   if(currentBarTime != g_lastTrailBarTime && CountPositions() > 0)
   {
      g_lastTrailBarTime = currentBarTime;
      ManageBreakeven(atr1);
      ManageTrailingStop(atr1);
   }

   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   double bodyRatio = GetBodyRatio(1);

   double ma200Buffer = atr1 * InpMA200BufferATR;
   bool aboveMA200 = (prevClose > ma200 + ma200Buffer);
   bool belowMA200 = (prevClose < ma200 - ma200Buffer);

   bool adxOk = true, timeOk = true, atrFilterOk = true;
   bool dailyUp = true, dailyDown = true;

   if(InpUseADX && g_adxHandle != INVALID_HANDLE)
   {
      double adxBuf[]; ArrayResize(adxBuf, 2); ArraySetAsSeries(adxBuf, true);
      if(CopyBuffer(g_adxHandle, 0, 0, 2, adxBuf) >= 2)
         adxOk = (adxBuf[1] > InpADXThreshold);
   }

   if(InpUseTimeFilter)
   {
      MqlDateTime dt; TimeToStruct(currentBarTime, dt);
      if(InpStartHour <= InpEndHour)
         timeOk = (dt.hour >= InpStartHour && dt.hour <= InpEndHour);
      else
         timeOk = (dt.hour >= InpStartHour || dt.hour <= InpEndHour);
   }

   if(InpUseATRFilter && g_atrFilterHandle != INVALID_HANDLE)
   {
      double atrAvgBuf[]; ArrayResize(atrAvgBuf, 2); ArraySetAsSeries(atrAvgBuf, true);
      if(CopyBuffer(g_atrFilterHandle, 0, 0, 2, atrAvgBuf) >= 2)
         atrFilterOk = (atr1 > atrAvgBuf[1] * InpATRFilterRatio);
   }

   if(InpUseDailyFilter && g_dailyMA200Handle != INVALID_HANDLE)
   {
      double dMaBuf[]; ArrayResize(dMaBuf, 2); ArraySetAsSeries(dMaBuf, true);
      if(CopyBuffer(g_dailyMA200Handle, 0, 0, 2, dMaBuf) >= 2)
      {
         double dClose = iClose(_Symbol, PERIOD_D1, 1);
         dailyUp   = (dClose > dMaBuf[1]);
         dailyDown = (dClose < dMaBuf[1]);
      }
   }

   if(InpDebugMode)
   {
      string trendStr = "震荡区";
      if(aboveMA200) trendStr = "多头趋势";
      if(belowMA200) trendStr = "空头趋势";
      Comment("SniperEA v8.6 | ", _Symbol, " ", EnumToString(Period()), "\n",
              "趋势:", trendStr, " | MA200:", DoubleToString(ma200, _Digits),
              " | 收盘:", DoubleToString(prevClose, _Digits), "\n",
              "ATR:", DoubleToString(atr1, _Digits),
              " | 实体:", DoubleToString(bodyRatio * 100, 1), "%\n",
              "盈亏平衡:", InpUseBreakeven ? "ON" : "OFF",
              "(", InpBreakevenATR, "xATR)", "\n",
              "持仓:", CountPositions(), "/", InpMaxPositions);
   }

   int posCount = CountPositions();
   if(posCount < InpMaxPositions)
   {
      bool flipUp   = (hist1 > 0 && hist2 <= 0);
      bool flipDown = (hist1 < 0 && hist2 >= 0);

      if(flipUp && InpEnableBuy && !g_pendingBuy)
      {
         if(!InpUseMA200Filter || aboveMA200)
         { g_pendingSell = false; g_pendingBuy = true; g_pendingBars = 0; }
      }

      if(flipDown && InpEnableSell && !g_pendingSell)
      {
         if(!InpUseMA200Filter || belowMA200)
         { g_pendingBuy = false; g_pendingSell = true; g_pendingBars = 0; }
      }

      if(g_pendingBuy || g_pendingSell)
      {
         g_pendingBars++;
         if(g_pendingBars > InpConfirmBars)
         { g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0; }
         else
         {
            bool macdUp   = (macd1 >= macd2);
            bool macdDown = (macd1 <= macd2);
            bool dangerCandle = IsDangerousCandle(1, atr1);

            if(g_pendingBuy && IsBullishCandle(1) && bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdUp) && (!InpUseMA200Filter || aboveMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyUp))
            {
               if(dangerCandle)
               {
                  Print("【危险K线-多】振幅>", InpMaxCandleATR, "xATR，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(GetUpperShadowRatio(1) > InpMaxOppositeShadow)
               {
                  Print("【上影过长-多】上影>", DoubleToString(InpMaxOppositeShadow * 100, 0), "%，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(InpRequireMomentumShift && !IsMomentumIncreasing(1))
               {
                  Print("【动能未递增-多】d点动能不足，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(InpRequireFollowThrough && !IsHighestClose(1, InpFollowThroughBars))
               {
                  Print("【跟随确认失败-多】未创近", InpFollowThroughBars, "根新高，等待");
               }
               else
               {
                  double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                  double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
                  double tp = (InpTakeProfitATR > 0) ? NormalizeDouble(ep + atr1 * InpTakeProfitATR, _Digits) : 0;
                  double lot = CalculateLotSize(ep - sl);
                  Print("【开多】实体:", DoubleToString(bodyRatio*100,1), "%",
                        " | EP:", ep, " SL:", sl, " TP:", tp, " Lot:", lot);
                  if(lot > 0)
                  {
                     OpenPosition(ORDER_TYPE_BUY, ep, sl, tp, lot);
                     g_pendingBuy = false; g_pendingBars = 0;
                  }
               }
            }

            if(g_pendingSell && IsBearishCandle(1) && bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdDown) && (!InpUseMA200Filter || belowMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyDown))
            {
               if(dangerCandle)
               {
                  Print("【危险K线-空】振幅>", InpMaxCandleATR, "xATR，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(GetLowerShadowRatio(1) > InpMaxOppositeShadow)
               {
                  Print("【下影过长-空】下影>", DoubleToString(InpMaxOppositeShadow * 100, 0), "%，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(InpRequireMomentumShift && !IsMomentumIncreasing(1))
               {
                  Print("【动能未递增-空】d点动能不足，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(InpRequireFollowThrough && !IsLowestClose(1, InpFollowThroughBars))
               {
                  Print("【跟随确认失败-空】未创近", InpFollowThroughBars, "根新低，等待");
               }
               else
               {
                  double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                  double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
                  double tp = (InpTakeProfitATR > 0) ? NormalizeDouble(ep - atr1 * InpTakeProfitATR, _Digits) : 0;
                  double lot = CalculateLotSize(sl - ep);
                  Print("【开空】实体:", DoubleToString(bodyRatio*100,1), "%",
                        " | EP:", ep, " SL:", sl, " TP:", tp, " Lot:", lot);
                  if(lot > 0)
                  {
                     OpenPosition(ORDER_TYPE_SELL, ep, sl, tp, lot);
                     g_pendingSell = false; g_pendingBars = 0;
                  }
               }
            }
         }
      }
   }
   else
   { g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0; }
}

//+------------------------------------------------------------------+
//| 【v8.6】盈亏平衡保护                                              |
//+------------------------------------------------------------------+
void ManageBreakeven(double atr)
{
   if(atr <= 0 || !InpUseBreakeven || InpBreakevenATR <= 0) return;
   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   if(prevClose <= 0) return;

   double breakevenDist = atr * InpBreakevenATR;
   double spread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curSL     = PositionGetDouble(POSITION_SL);
      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      if(posType == POSITION_TYPE_BUY)
      {
         double beSL = openPrice + spread;
         if(prevClose > openPrice + breakevenDist && curSL < beSL - _Point)
            ModifyStopLoss(ticket, beSL);
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         double beSL = openPrice - spread;
         if(prevClose < openPrice - breakevenDist && curSL > beSL + _Point)
            ModifyStopLoss(ticket, beSL);
      }
   }
}

//+------------------------------------------------------------------+
//| 移动止盈                                                          |
//+------------------------------------------------------------------+
void ManageTrailingStop(double atr)
{
   if(atr <= 0) return;
   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   if(prevClose <= 0) return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curSL     = PositionGetDouble(POSITION_SL);
      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      if(posType == POSITION_TYPE_BUY)
      {
         double startLevel = openPrice + atr * InpTrailingStart;
         if(prevClose > startLevel)
         {
            double newSL = NormalizeDouble(prevClose - atr * InpTrailingStep, _Digits);
            if(newSL > curSL + _Point) ModifyStopLoss(ticket, newSL);
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         double startLevel = openPrice - atr * InpTrailingStart;
         if(prevClose < startLevel)
         {
            double newSL = NormalizeDouble(prevClose + atr * InpTrailingStep, _Digits);
            if(newSL < curSL - _Point) ModifyStopLoss(ticket, newSL);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 危险K线判断                                                        |
//+------------------------------------------------------------------+
bool IsDangerousCandle(int shift, double atr)
{
   if(InpMaxCandleATR <= 0 || atr <= 0) return false;
   double range = iHigh(_Symbol, PERIOD_CURRENT, shift) - iLow(_Symbol, PERIOD_CURRENT, shift);
   double prevRange = iHigh(_Symbol, PERIOD_CURRENT, shift + 1) - iLow(_Symbol, PERIOD_CURRENT, shift + 1);
   if(prevRange <= 0) return (range > atr * InpMaxCandleATR);
   return (range > atr * InpMaxCandleATR && range > prevRange * InpDangerSuddenRatio);
}

double GetUpperShadowRatio(int shift)
{
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double range = high - low;
   if(range <= 0) return 0;
   return (high - MathMax(open, close)) / range;
}

double GetLowerShadowRatio(int shift)
{
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double range = high - low;
   if(range <= 0) return 0;
   return (MathMin(open, close) - low) / range;
}

bool IsHighestClose(int shift, int lookback)
{
   double targetClose = iClose(_Symbol, PERIOD_CURRENT, shift);
   for(int i = shift + 1; i <= shift + lookback; i++)
      if(iClose(_Symbol, PERIOD_CURRENT, i) >= targetClose) return false;
   return true;
}

bool IsLowestClose(int shift, int lookback)
{
   double targetClose = iClose(_Symbol, PERIOD_CURRENT, shift);
   for(int i = shift + 1; i <= shift + lookback; i++)
      if(iClose(_Symbol, PERIOD_CURRENT, i) <= targetClose) return false;
   return true;
}

double GetBodyRatio(int shift)
{
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double range = high - low;
   if(range <= 0) return 0;
   return MathAbs(close - open) / range;
}

bool IsBullishCandle(int shift) { return iClose(_Symbol, PERIOD_CURRENT, shift) > iOpen(_Symbol, PERIOD_CURRENT, shift); }
bool IsBearishCandle(int shift) { return iClose(_Symbol, PERIOD_CURRENT, shift) < iOpen(_Symbol, PERIOD_CURRENT, shift); }

bool IsMomentumIncreasing(int shift)
{
   double body     = MathAbs(iClose(_Symbol, PERIOD_CURRENT, shift)     - iOpen(_Symbol, PERIOD_CURRENT, shift));
   double prevBody = MathAbs(iClose(_Symbol, PERIOD_CURRENT, shift + 1) - iOpen(_Symbol, PERIOD_CURRENT, shift + 1));
   if(prevBody <= 0) return false;
   return (body > prevBody);
}

double CalculateLotSize(double slDist)
{
   if(slDist <= 0) return 0;
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk     = balance * InpRiskPercent / 100.0;
   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0 || tickVal <= 0) return 0;
   double lot = risk / (slDist / tickSize * tickVal);
   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / step) * step;
   return MathMax(minL, MathMin(maxL, lot));
}

void OpenPosition(ENUM_ORDER_TYPE type, double price, double sl, double tp, double lot)
{
   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL; req.symbol = _Symbol; req.volume = lot;
   req.type = type; req.price = price; req.sl = sl; req.tp = tp;
   req.deviation = 20; req.magic = InpMagicNumber; req.comment = InpComment;
   req.type_filling = ORDER_FILLING_IOC;
   if(!OrderSend(req, res))
      Print("开仓失败 | 错误:", GetLastError(), " | 类型:", EnumToString(type), " | 手数:", lot);
   else
      Print("开仓成功 | 票号:", res.order, " | 价格:", res.price);
}

void ModifyStopLoss(ulong ticket, double newSL)
{
   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_SLTP; req.position = ticket; req.symbol = _Symbol;
   req.sl = newSL; req.tp = PositionGetDouble(POSITION_TP);
   if(!OrderSend(req, res))
      Print("修改止损失败 | 票号:", ticket, " | 错误:", GetLastError());
}

int CountPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      count++;
   }
   return count;
}
//+------------------------------------------------------------------+
