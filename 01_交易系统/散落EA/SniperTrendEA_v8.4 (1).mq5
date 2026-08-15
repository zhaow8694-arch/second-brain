//+------------------------------------------------------------------+
//|                                          SniperTrendEA_v8.4.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                    v8.4 - 多因子优化版（ADX/时间/波动率/日线过滤） |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.4 - Wyckoff + Evil MACD + MA200 + Multi-Factor"
#property version   "8.40"
#property strict

//--- 输入参数
input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 趋势过滤 ==="
input int    InpMA200Period    = 200;      // 趋势均线周期（默认200）
input bool   InpUseMA200Filter = true;     // 是否启用MA200过滤（可关闭对比测试）
input double InpMA200Buffer    = 0.0;      // MA200缓冲区（点数，0=严格过滤）

input group "=== ADX 趋势过滤 ==="
input bool   InpUseADX          = false;   // 是否启用ADX过滤
input int    InpADXPeriod       = 14;      // ADX周期
input double InpADXThreshold    = 25.0;    // ADX阈值（>此值才入场）

input group "=== 时间过滤 ==="
input bool   InpUseTimeFilter   = false;   // 是否启用时间过滤
input int    InpStartHour       = 8;       // 交易开始小时(0-23)
input int    InpEndHour         = 20;      // 交易结束小时(0-23)

input group "=== 波动率过滤 ==="
input bool   InpUseATRFilter    = false;   // 是否启用波动率过滤
input int    InpATRFilterPeriod = 20;      // 波动率均值周期
input double InpATRFilterRatio  = 1.0;     // 当前ATR需大于均值的倍数

input group "=== 日线趋势确认 ==="
input bool   InpUseDailyFilter  = false;   // 是否启用日线MA200过滤

input group "=== 入场过滤 ==="
input double InpBodyRatio      = 0.60;     // K线实体占比阈值（≥60%）
input int    InpConfirmBars    = 4;        // 翻转后等待确认的最大K线数
input bool   InpRequireMACDDir = false;    // 是否要求MACD主线方向一致

input group "=== 风险管理 ==="
input double InpRiskPercent    = 0.5;      // 单笔风险占账户比例（%）
input double InpATRMultiplier  = 1.5;      // 止损 = ATR × 此倍数
input int    InpATRPeriod      = 14;       // ATR 周期
input double InpTrailingStart  = 5.0;      // 移动止盈启动距离（ATR倍数）
input double InpTrailingStep   = 2.5;      // 移动止盈步长（ATR倍数）
input int    InpMaxPositions   = 1;        // 最大持仓数量

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260213;
input string InpComment        = "SniperEA_v8.4";
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

   Print("SniperTrendEA v8.4 初始化成功");
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

   // 移动止盈
   if(currentBarTime != g_lastTrailBarTime && CountPositions() > 0)
   {
      g_lastTrailBarTime = currentBarTime;
      double atrBuf[]; ArrayResize(atrBuf, 2); ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2 && atrBuf[0] > 0)
         ManageTrailingStop(atrBuf[0]);
   }

   // 入场逻辑
   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

   double macdMain[], macdSig[], atrBuf2[], ma200Buf[];
   ArrayResize(macdMain, 4); ArrayResize(macdSig, 4); ArrayResize(atrBuf2, 4); ArrayResize(ma200Buf, 3);
   ArraySetAsSeries(macdMain, true); ArraySetAsSeries(macdSig, true); ArraySetAsSeries(atrBuf2, true); ArraySetAsSeries(ma200Buf, true);

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

   bool aboveMA200 = (prevClose > ma200 + InpMA200Buffer);
   bool belowMA200 = (prevClose < ma200 - InpMA200Buffer);

   // 新增因子状态
   bool adxOk = true;
   bool timeOk = true;
   bool atrFilterOk = true;
   bool dailyUp = true;
   bool dailyDown = true;

   if(InpUseADX && g_adxHandle != INVALID_HANDLE)
   {
      double adxBuf[]; ArrayResize(adxBuf, 2); ArraySetAsSeries(adxBuf, true);
      if(CopyBuffer(g_adxHandle, 0, 0, 2, adxBuf) >= 2)
         adxOk = (adxBuf[1] > InpADXThreshold);
   }

   if(InpUseTimeFilter)
   {
      MqlDateTime dt; TimeToStruct(currentBarTime, dt);
      if(InpStartHour <= InpEndHour) timeOk = (dt.hour >= InpStartHour && dt.hour <= InpEndHour);
      else timeOk = (dt.hour >= InpStartHour || dt.hour <= InpEndHour);
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
         dailyUp = (dClose > dMaBuf[1]);
         dailyDown = (dClose < dMaBuf[1]);
      }
   }

   if(InpDebugMode)
   {
      Comment("SniperEA v8.4 | ", _Symbol, "\n",
              "MA200:", DoubleToString(ma200, 2), " | 收盘:", DoubleToString(prevClose, 2), "\n",
              "ADX OK:", adxOk, " | Time OK:", timeOk, " | ATR OK:", atrFilterOk, "\n",
              "Daily Up:", dailyUp, " | Daily Down:", dailyDown);
   }

   int posCount = CountPositions();
   if(posCount < InpMaxPositions)
   {
      bool flipUp   = (hist1 > 0 && hist2 <= 0);
      bool flipDown = (hist1 < 0 && hist2 >= 0);

      if(flipUp && InpEnableBuy && !g_pendingBuy)
      {
         if(!InpUseMA200Filter || aboveMA200)
         {
            g_pendingSell = false; g_pendingBuy = true; g_pendingBars = 0;
         }
      }

      if(flipDown && InpEnableSell && !g_pendingSell)
      {
         if(!InpUseMA200Filter || belowMA200)
         {
            g_pendingBuy = false; g_pendingSell = true; g_pendingBars = 0;
         }
      }

      if(g_pendingBuy || g_pendingSell)
      {
         g_pendingBars++;
         if(g_pendingBars > InpConfirmBars)
         {
            g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0;
         }
         else
         {
            bool macdUp   = (macd1 >= macd2);
            bool macdDown = (macd1 <= macd2);

            if(g_pendingBuy && IsBullishCandle(1) && bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdUp) && (!InpUseMA200Filter || aboveMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyUp))
            {
               double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
               double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
               double lot = CalculateLotSize(ep - sl);
               if(lot > 0)
               {
                  OpenPosition(ORDER_TYPE_BUY, ep, sl, lot);
                  g_pendingBuy = false; g_pendingBars = 0;
               }
            }

            if(g_pendingSell && IsBearishCandle(1) && bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdDown) && (!InpUseMA200Filter || belowMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyDown))
            {
               double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
               double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
               double lot = CalculateLotSize(sl - ep);
               if(lot > 0)
               {
                  OpenPosition(ORDER_TYPE_SELL, ep, sl, lot);
                  g_pendingSell = false; g_pendingBars = 0;
               }
            }
         }
      }
   }
   else
   {
      g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0;
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
            if(curSL == 0 || newSL < curSL - _Point) ModifyStopLoss(ticket, newSL);
         }
      }
   }
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
