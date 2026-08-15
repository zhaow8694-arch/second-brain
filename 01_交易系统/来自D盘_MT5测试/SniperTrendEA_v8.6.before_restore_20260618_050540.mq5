//+------------------------------------------------------------------+
//|                                          SniperTrendEA_v8.6.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                    v8.6 - Structure Quality Upgrade             |
//|                                                                  |
//|  v8.5 在 v8.4 多因子框架基础上，融入 Z-Wei 交易体系核心理念：       |
//|                                                                  |
//|  【1】危险K线过滤 (MaxCandleATR)：                                 |
//|       拒绝异常巨大的K线（振幅 > N×ATR），                         |
//|       规避点火耗竭点的FOMO追高陷阱（订单失衡FVG风险）。            |
//|       —— 对应文章《危险的K线》                                     |
//|                                                                  |
//|  【2】单边影线惩罚 (MaxOppositeShadow)：                           |
//|       做多严格限制上影线占比；做空严格限制下影线占比。            |
//|       确保突破K线"干脆、肯定"，体现博弈方真正胜出。               |
//|       —— 对应文章《市场结构观察 #26-2-2》（K线干脆度）             |
//|                                                                  |
//|  【3】自适应MA200震荡带 (MA200BufferATR)：                         |
//|       将固定点数Buffer改为基于ATR的动态Buffer，                    |
//|       适应不同时期波动率，更准确识别真实震荡区。                   |
//|       —— 对应文章《分形几何思维解读市场》（结构自相似）            |
//|                                                                  |
//|  【4】点火与跟随确认 (RequireFollowThrough)：                      |
//|       可选要求突破K线收盘价创出近N根K线极值（确认共识形成）。     |
//|       —— 对应文章《点火与跟随》                                    |
//|                                                                  |
//|  【5】保留 v8.4 全部多因子过滤：                                    |
//|       ADX / 时间过滤 / 波动率过滤 / 日线MA200。                    |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.6 - Wyckoff + Evil MACD + Z-Wei Structure"
#property version   "8.60"
#property strict

//--- 输入参数
input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 趋势过滤（v8.5: Buffer 改用 ATR 倍数）==="
input int    InpMA200Period    = 200;       // 趋势均线周期（默认200）
input bool   InpUseMA200Filter = true;      // 是否启用MA200过滤
input double InpMA200BufferATR = 0.0;       // 【v8.5】MA200缓冲区（ATR倍数，0=严格过滤）

input group "=== 入场质量过滤（v8.5 新增 Z-Wei 哲学）==="
input double InpBodyRatio          = 0.60;  // K线实体占比阈值（≥60%）
input double InpMaxCandleATR       = 2.5;   // 【v8.5新增】K线最大振幅（ATR倍数），防追高耗竭
input double InpMaxOppositeShadow  = 0.20;  // 【v8.5新增】反向影线最大占比
input bool   InpRequireFollowThrough = false;// 【v8.5新增】是否要求收盘创近N根K线极值
input int    InpFollowThroughBars  = 3;     // 【v8.5新增】跟随确认回看K线数
input int    InpConfirmBars        = 4;     // 翻转后等待确认的最大K线数
input bool   InpRequireMACDDir     = false; // 是否要求MACD主线方向一致

input group "=== Structure Filter (v8.6) ==="
input bool   InpUseStructureFilter      = true;  // Enable validated trendline structure filter
input int    InpSwingLookback           = 3;     // Swing high/low bars on each side
input int    InpStructureScanBars       = 80;    // Historical bars to scan for structure
input int    InpMinTrendlineTouches     = 3;     // Minimum validated trendline touches
input double InpTrendlineTouchATR       = 0.25;  // Touch tolerance in ATR multiples
input double InpMinBreakoutDistanceATR  = 0.10;  // Minimum close distance beyond trendline
input double InpMinBreakoutScore        = 70.0;  // Minimum quality score for entry
input bool   InpRejectNoStructure       = true;  // Reject entries when no valid structure exists
input bool   InpShowStructureDebug      = true;  // Print structure diagnostics

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
input double InpRiskPercent    = 0.5;       // 单笔风险占账户比例（%）
input double InpATRMultiplier  = 1.5;       // 止损 = ATR × 此倍数
input int    InpATRPeriod      = 14;        // ATR 周期
input double InpTrailingStart  = 5.0;       // 移动止盈启动（ATR倍数）
input double InpTrailingStep   = 2.5;       // 移动止盈步长（ATR倍数）
input int    InpMaxPositions   = 1;         // 最大持仓数量

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260506;
input string InpComment        = "SniperEA_v8.6";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

//--- 指标句柄
int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;
int g_adxHandle = INVALID_HANDLE;
int g_atrFilterHandle = INVALID_HANDLE;
int g_dailyMA200Handle = INVALID_HANDLE;

//--- 待入场状态
bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

//--- K线时间戳
datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

//+------------------------------------------------------------------+
//| 初始化                                                            |
//+------------------------------------------------------------------+
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
         " | 危险K线阈值:", InpMaxCandleATR, "×ATR",
         " | 反向影线限制:", DoubleToString(InpMaxOppositeShadow * 100, 0), "%",
         " | 跟随确认:", InpRequireFollowThrough ? "ON" : "OFF",
         " | MA200自适应Buffer:", InpMA200BufferATR, "×ATR");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 释放                                                              |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| 主逻辑                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == 0) return;

   // 移动止盈（每根K线一次）
   if(currentBarTime != g_lastTrailBarTime && CountPositions() > 0)
   {
      g_lastTrailBarTime = currentBarTime;
      double atrBuf[]; ArrayResize(atrBuf, 2); ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2 && atrBuf[0] > 0)
         ManageTrailingStop(atrBuf[0]);
   }

   // 入场逻辑（每根K线一次）
   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

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

   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   double bodyRatio = GetBodyRatio(1);

   // v8.5: MA200 自适应 Buffer
   double ma200Buffer = atr1 * InpMA200BufferATR;
   bool aboveMA200 = (prevClose > ma200 + ma200Buffer);
   bool belowMA200 = (prevClose < ma200 - ma200Buffer);

   // ===== 多因子过滤（v8.4 保留）=====
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
      Comment("SniperEA v8.6 结构过滤版 | ", _Symbol, " ", EnumToString(Period()), "\n",
              "趋势:", trendStr, " | MA200:", DoubleToString(ma200, _Digits),
              " | 收盘:", DoubleToString(prevClose, _Digits), "\n",
              "ATR:", DoubleToString(atr1, _Digits),
              " | 实体:", DoubleToString(bodyRatio * 100, 1), "%\n",
              "上影:", DoubleToString(GetUpperShadowRatio(1) * 100, 1), "%",
              " | 下影:", DoubleToString(GetLowerShadowRatio(1) * 100, 1), "%\n",
              "ADX:", adxOk ? "OK" : "FAIL",
              " | Time:", timeOk ? "OK" : "FAIL",
              " | ATR Filter:", atrFilterOk ? "OK" : "FAIL",
              " | Daily:", (dailyUp || dailyDown) ? "OK" : "FAIL", "\n",
              "Structure Filter:", InpUseStructureFilter ? "ON" : "OFF", "\n",
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

            // v8.5：危险K线判断（多空共用）
            bool dangerCandle = IsDangerousCandle(1, atr1);

            // ===== 做多确认 =====
            if(g_pendingBuy && IsBullishCandle(1) && bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdUp) && (!InpUseMA200Filter || aboveMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyUp))
            {
               // 哲学过滤层
               if(dangerCandle)
               {
                  Print("【危险K线-多】振幅>", InpMaxCandleATR, "×ATR，疑似耗竭，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(GetUpperShadowRatio(1) > InpMaxOppositeShadow)
               {
                  Print("【上影过长-多】上影>", DoubleToString(InpMaxOppositeShadow * 100, 0), "%，存在卖压，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(InpRequireFollowThrough && !IsHighestClose(1, InpFollowThroughBars))
               {
                  Print("【跟随确认失败-多】未创近", InpFollowThroughBars, "根K线新高，等待");
                  // 不取消pending，等待下一根再试
               }
               else
               {
                  STrendlineInfo structure;
                  if(!PassStructureFilter(true, atr1, dangerCandle, structure))
                  {
                     g_pendingBuy = false; g_pendingBars = 0;
                     Print("【结构过滤-多】评分不足或无有效结构，放弃");
                  }
                  else
                  {
                     double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                     double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
                     double lot = CalculateLotSize(ep - sl);
                     Print("【开多】实体:", DoubleToString(bodyRatio*100,1), "%",
                           " | 上影:", DoubleToString(GetUpperShadowRatio(1)*100,1), "%",
                           " | 结构评分:", DoubleToString(structure.score, 1),
                           " | EP:", ep, " SL:", sl, " Lot:", lot);
                     if(lot > 0)
                     {
                        OpenPosition(ORDER_TYPE_BUY, ep, sl, lot);
                        g_pendingBuy = false; g_pendingBars = 0;
                     }
                  }
               }
            }

            // ===== 做空确认 =====
            if(g_pendingSell && IsBearishCandle(1) && bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdDown) && (!InpUseMA200Filter || belowMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyDown))
            {
               if(dangerCandle)
               {
                  Print("【危险K线-空】振幅>", InpMaxCandleATR, "×ATR，疑似耗竭，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(GetLowerShadowRatio(1) > InpMaxOppositeShadow)
               {
                  Print("【下影过长-空】下影>", DoubleToString(InpMaxOppositeShadow * 100, 0), "%，存在买盘，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(InpRequireFollowThrough && !IsLowestClose(1, InpFollowThroughBars))
               {
                  Print("【跟随确认失败-空】未创近", InpFollowThroughBars, "根K线新低，等待");
               }
               else
               {
                  STrendlineInfo structure;
                  if(!PassStructureFilter(false, atr1, dangerCandle, structure))
                  {
                     g_pendingSell = false; g_pendingBars = 0;
                     Print("【结构过滤-空】评分不足或无有效结构，放弃");
                  }
                  else
                  {
                     double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                     double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
                     double lot = CalculateLotSize(sl - ep);
                     Print("【开空】实体:", DoubleToString(bodyRatio*100,1), "%",
                           " | 下影:", DoubleToString(GetLowerShadowRatio(1)*100,1), "%",
                           " | 结构评分:", DoubleToString(structure.score, 1),
                           " | EP:", ep, " SL:", sl, " Lot:", lot);
                     if(lot > 0)
                     {
                        OpenPosition(ORDER_TYPE_SELL, ep, sl, lot);
                        g_pendingSell = false; g_pendingBars = 0;
                     }
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
            if(curSL == 0 || newSL < curSL - _Point) ModifyStopLoss(ticket, newSL);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 【v8.5新增】危险K线判断                                            |
//+------------------------------------------------------------------+
bool IsDangerousCandle(int shift, double atr)
{
   if(InpMaxCandleATR <= 0 || atr <= 0) return false;
   double range = iHigh(_Symbol, PERIOD_CURRENT, shift) - iLow(_Symbol, PERIOD_CURRENT, shift);
   return (range > atr * InpMaxCandleATR);
}

//+------------------------------------------------------------------+
//| 【v8.5新增】上影线占比                                             |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| 【v8.5新增】下影线占比                                             |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| 【v8.5新增】跟随确认                                               |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| 【v8.6新增】结构过滤与突破评分                                     |
//+------------------------------------------------------------------+
struct STrendlineInfo
{
   bool   valid;
   int    touches;
   int    anchorShiftOld;
   int    anchorShiftNew;
   double anchorPriceOld;
   double anchorPriceNew;
   double lineAtSignal;
   double breakoutDistance;
   double breakoutDistanceATR;
   double score;
};

void ResetTrendlineInfo(STrendlineInfo &info)
{
   info.valid = false;
   info.touches = 0;
   info.anchorShiftOld = -1;
   info.anchorShiftNew = -1;
   info.anchorPriceOld = 0.0;
   info.anchorPriceNew = 0.0;
   info.lineAtSignal = 0.0;
   info.breakoutDistance = 0.0;
   info.breakoutDistanceATR = 0.0;
   info.score = 0.0;
}

double ClampDouble(double value, double minValue, double maxValue)
{
   return MathMax(minValue, MathMin(maxValue, value));
}

bool IsSwingHigh(int shift, int lookback)
{
   if(shift - lookback < 1) return false;
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(shift + lookback >= bars) return false;

   double high = iHigh(_Symbol, PERIOD_CURRENT, shift);
   for(int i = 1; i <= lookback; i++)
   {
      if(iHigh(_Symbol, PERIOD_CURRENT, shift - i) >= high) return false;
      if(iHigh(_Symbol, PERIOD_CURRENT, shift + i) >= high) return false;
   }
   return true;
}

bool IsSwingLow(int shift, int lookback)
{
   if(shift - lookback < 1) return false;
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(shift + lookback >= bars) return false;

   double low = iLow(_Symbol, PERIOD_CURRENT, shift);
   for(int i = 1; i <= lookback; i++)
   {
      if(iLow(_Symbol, PERIOD_CURRENT, shift - i) <= low) return false;
      if(iLow(_Symbol, PERIOD_CURRENT, shift + i) <= low) return false;
   }
   return true;
}

double LineValueAtShift(int oldShift, double oldPrice, int newShift, double newPrice, int targetShift)
{
   if(newShift == oldShift) return newPrice;
   double slope = (newPrice - oldPrice) / (double)(newShift - oldShift);
   return oldPrice + slope * (double)(targetShift - oldShift);
}

int CountTrendlineTouches(bool forBuy, int oldShift, double oldPrice, int newShift, double newPrice, double atr)
{
   if(atr <= 0) return 0;
   double touchDistance = atr * InpTrendlineTouchATR;
   int touches = 0;

   for(int shift = oldShift; shift >= newShift; shift--)
   {
      double lineValue = LineValueAtShift(oldShift, oldPrice, newShift, newPrice, shift);
      double actual = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, shift) : iLow(_Symbol, PERIOD_CURRENT, shift);
      if(MathAbs(actual - lineValue) <= touchDistance)
         touches++;
   }

   return touches;
}

bool FindValidatedTrendline(bool forBuy, double atr, STrendlineInfo &info)
{
   ResetTrendlineInfo(info);
   if(atr <= 0 || InpSwingLookback < 1 || InpMinTrendlineTouches < 2) return false;

   int bars = Bars(_Symbol, PERIOD_CURRENT);
   int maxShift = MathMin(InpStructureScanBars, bars - InpSwingLookback - 2);
   int minShift = InpSwingLookback + 1;
   if(maxShift <= minShift + InpSwingLookback) return false;

   for(int newShift = minShift; newShift <= maxShift - InpSwingLookback; newShift++)
   {
      bool newSwing = forBuy ? IsSwingHigh(newShift, InpSwingLookback) : IsSwingLow(newShift, InpSwingLookback);
      if(!newSwing) continue;

      double newPrice = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, newShift) : iLow(_Symbol, PERIOD_CURRENT, newShift);

      for(int oldShift = newShift + InpSwingLookback; oldShift <= maxShift; oldShift++)
      {
         bool oldSwing = forBuy ? IsSwingHigh(oldShift, InpSwingLookback) : IsSwingLow(oldShift, InpSwingLookback);
         if(!oldSwing) continue;

         double oldPrice = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, oldShift) : iLow(_Symbol, PERIOD_CURRENT, oldShift);
         if(forBuy && newPrice >= oldPrice) continue;
         if(!forBuy && newPrice <= oldPrice) continue;

         int touches = CountTrendlineTouches(forBuy, oldShift, oldPrice, newShift, newPrice, atr);
         if(touches < InpMinTrendlineTouches) continue;

         double lineAtSignal = LineValueAtShift(oldShift, oldPrice, newShift, newPrice, 1);
         double close = iClose(_Symbol, PERIOD_CURRENT, 1);
         double distance = forBuy ? close - lineAtSignal : lineAtSignal - close;
         double distanceATR = distance / atr;
         if(distanceATR < InpMinBreakoutDistanceATR) continue;

         bool better = (!info.valid ||
                        touches > info.touches ||
                        (touches == info.touches && newShift < info.anchorShiftNew));
         if(better)
         {
            info.valid = true;
            info.touches = touches;
            info.anchorShiftOld = oldShift;
            info.anchorShiftNew = newShift;
            info.anchorPriceOld = oldPrice;
            info.anchorPriceNew = newPrice;
            info.lineAtSignal = lineAtSignal;
            info.breakoutDistance = distance;
            info.breakoutDistanceATR = distanceATR;
         }
      }
   }

   return info.valid;
}

double CalculateBreakoutScore(bool forBuy, double atr, STrendlineInfo &info, bool dangerousCandle)
{
   double bodyRatio = GetBodyRatio(1);
   double bodyScore = (InpBodyRatio <= 0) ? 30.0 : ClampDouble(bodyRatio / InpBodyRatio, 0.0, 1.0) * 30.0;

   double shadow = forBuy ? GetUpperShadowRatio(1) : GetLowerShadowRatio(1);
   double shadowScore = 0.0;
   if(InpMaxOppositeShadow <= 0)
      shadowScore = (shadow <= 0) ? 25.0 : 0.0;
   else if(shadow <= InpMaxOppositeShadow)
      shadowScore = 25.0;
   else
      shadowScore = ClampDouble(1.0 - ((shadow - InpMaxOppositeShadow) / InpMaxOppositeShadow), 0.0, 1.0) * 25.0;

   double distanceTarget = InpMinBreakoutDistanceATR * 2.0;
   double distanceScore = (distanceTarget <= 0) ? 25.0 : ClampDouble(info.breakoutDistanceATR / distanceTarget, 0.0, 1.0) * 25.0;

   double score = bodyScore + shadowScore + distanceScore;
   if(dangerousCandle) score -= 30.0;
   if(InpRequireFollowThrough)
   {
      bool followOk = forBuy ? IsHighestClose(1, InpFollowThroughBars) : IsLowestClose(1, InpFollowThroughBars);
      if(followOk) score += 20.0;
   }

   return ClampDouble(score, 0.0, 100.0);
}

bool PassStructureFilter(bool forBuy, double atr, bool dangerousCandle, STrendlineInfo &info)
{
   ResetTrendlineInfo(info);
   if(!InpUseStructureFilter)
   {
      info.valid = true;
      info.score = 100.0;
      return true;
   }

   bool found = FindValidatedTrendline(forBuy, atr, info);
   if(!found)
   {
      if(InpShowStructureDebug)
         Print("【v8.6结构】", forBuy ? "多" : "空", "：无有效趋势线结构");

      if(!InpRejectNoStructure)
      {
         info.valid = false;
         info.score = 100.0;
         return true;
      }
      return false;
   }

   info.score = CalculateBreakoutScore(forBuy, atr, info, dangerousCandle);
   if(InpShowStructureDebug)
   {
      Print("【v8.6结构】", forBuy ? "多" : "空",
            " | touches:", info.touches,
            " | line:", DoubleToString(info.lineAtSignal, _Digits),
            " | distanceATR:", DoubleToString(info.breakoutDistanceATR, 2),
            " | score:", DoubleToString(info.score, 1));
   }

   return (info.score >= InpMinBreakoutScore);
}

//+------------------------------------------------------------------+
//| K线实体占比                                                        |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| 手数计算                                                          |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| 开仓                                                              |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE type, double price, double sl, double lot)
{
   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL; req.symbol = _Symbol; req.volume = lot;
   req.type = type; req.price = price; req.sl = sl; req.tp = 0;
   req.deviation = 20; req.magic = InpMagicNumber; req.comment = InpComment;
   req.type_filling = ORDER_FILLING_IOC;
   if(!OrderSend(req, res))
      Print("开仓失败 | 错误:", GetLastError(), " | 类型:", EnumToString(type), " | 手数:", lot);
   else
      Print("开仓成功 | 票号:", res.order, " | 价格:", res.price);
}

//+------------------------------------------------------------------+
//| 修改止损                                                          |
//+------------------------------------------------------------------+
void ModifyStopLoss(ulong ticket, double newSL)
{
   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_SLTP; req.position = ticket; req.symbol = _Symbol;
   req.sl = newSL; req.tp = PositionGetDouble(POSITION_TP);
   if(!OrderSend(req, res))
      Print("修改止损失败 | 票号:", ticket, " | 错误:", GetLastError());
}

//+------------------------------------------------------------------+
//| 统计持仓数量                                                       |
//+------------------------------------------------------------------+
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
