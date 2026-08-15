//+------------------------------------------------------------------+
//|                                          SniperTrendEA_v8.2.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                    v8.2 - 参数优化版（遗传算法优化最优参数）      |
//|                    v8.3 - 10年全量参数优化版（2015-2025最优参数） |
//|                                                                  |
//|  修复内容：                                                        |
//|  v7问题：在2020~2021年震荡市中，MACD柱状图频繁翻转导致连续亏损      |
//|          最大回撤高达94%，几乎爆仓                                  |
//|  v8方案：加入MA200（200期移动平均线）作为趋势过滤层                  |
//|          做多：价格（上根K线收盘）必须在MA200上方                    |
//|          做空：价格（上根K线收盘）必须在MA200下方                    |
//|          震荡市中价格在MA200附近来回穿越，大量假信号被过滤            |
//|          趋势市中价格单边运行，MA200过滤不影响主要信号               |
//|  v8.1修复：5个静态数组ArraySetAsSeries警告（改为动态数组+ArrayResize）|
//|  v8.2优化：遗传算法参数优化结果（XAUUSD H4 2020-2025）               |
//|           InpBodyRatio    0.55->0.65  InpConfirmBars  5->4          |
//|           InpTrailingStart 3.0->3.5  InpTrailingStep 1.5->3.0      |
//|           优化后：利润因子2.13，最大回撤26.3%（风险0.5%）             |
//|  v8.3优化：10年全量数据遗传算法优化（XAUUSD H4 2015-2025）           |
//|           InpBodyRatio    0.65->0.60  InpTrailingStart 3.5->5.0     |
//|           InpTrailingStep 3.0->2.5                                  |
//|           优化后：10年全周期利润因子1.84，最大回撤27.1%               |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.3 - Wyckoff + Evil MACD + MA200"
#property version   "8.30"
#property strict

//--- 输入参数
input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 趋势过滤 ==="
input int    InpMA200Period    = 200;      // 趋势均线周期（默认200）
input bool   InpUseMA200Filter = true;    // 是否启用MA200过滤（可关闭对比测试）
input double InpMA200Buffer    = 0.0;     // MA200缓冲区（点数，0=严格过滤）

input group "=== 入场过滤 ==="
input double InpBodyRatio      = 0.60;    // K线实体占比阈值（≥60%）[v8.3优化，原0.65]
input int    InpConfirmBars    = 4;       // 翻转后等待确认的最大K线数 [优化值，原5]
input bool   InpRequireMACDDir = false;   // 是否要求MACD主线方向一致

input group "=== 风险管理 ==="
input double InpRiskPercent    = 1.0;     // 单笔风险占账户比例（%）
input double InpATRMultiplier  = 1.5;     // 止损 = ATR × 此倍数
input int    InpATRPeriod      = 14;      // ATR 周期
input double InpTrailingStart  = 5.0;     // 移动止盈启动距离（ATR倍数）[v8.3优化，原3.5]
input double InpTrailingStep   = 2.5;     // 移动止盈步长（ATR倍数）[v8.3优化，原3.0]
input int    InpMaxPositions   = 1;       // 最大持仓数量

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260213;
input string InpComment        = "SniperEA_v8.3";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

//--- 指标句柄
int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;

//--- 待入场状态
bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

//--- K线时间戳（移动止盈和入场逻辑各自独立）
datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

//+------------------------------------------------------------------+
//| 初始化                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   g_macdHandle = iMACD(_Symbol, PERIOD_CURRENT,
                        InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
   if(g_macdHandle == INVALID_HANDLE)
   {
      Print("错误：MACD句柄创建失败，错误码:", GetLastError());
      return INIT_FAILED;
   }

   g_atrHandle = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   if(g_atrHandle == INVALID_HANDLE)
   {
      Print("错误：ATR句柄创建失败，错误码:", GetLastError());
      return INIT_FAILED;
   }

   g_ma200Handle = iMA(_Symbol, PERIOD_CURRENT,
                       InpMA200Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_ma200Handle == INVALID_HANDLE)
   {
      Print("错误：MA200句柄创建失败，错误码:", GetLastError());
      return INIT_FAILED;
   }

   g_pendingBuy       = false;
   g_pendingSell      = false;
   g_pendingBars      = 0;
   g_lastTrailBarTime = 0;
   g_lastEntryBarTime = 0;

   Print("SniperTrendEA v8.3 初始化成功 | 品种:", _Symbol,
         " | 周期:", EnumToString(Period()),
         " | MA200过滤:", InpUseMA200Filter ? "开启" : "关闭",
         " | 移动止盈：严格K线级别",
         " | 启动:", InpTrailingStart, "×ATR",
         " | 步长:", InpTrailingStep, "×ATR");
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
   Comment("");
}

//+------------------------------------------------------------------+
//| 主逻辑                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == 0) return;

   // ================================================================
   // 【移动止盈】每根K线只执行一次
   // ================================================================
   if(currentBarTime != g_lastTrailBarTime && CountPositions() > 0)
   {
      g_lastTrailBarTime = currentBarTime;
      double atrBuf[];
      ArrayResize(atrBuf, 2);
      ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2 && atrBuf[0] > 0)
         ManageTrailingStop(atrBuf[0]);
   }

   // ================================================================
   // 【入场逻辑】每根K线只执行一次
   // ================================================================
   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

   // 读取指标数据（全部使用shift=1已确认K线）
   double macdMain[], macdSig[], atrBuf2[], ma200Buf[];
   ArrayResize(macdMain,  4);
   ArrayResize(macdSig,   4);
   ArrayResize(atrBuf2,   4);
   ArrayResize(ma200Buf,  3);
   ArraySetAsSeries(macdMain,  true);
   ArraySetAsSeries(macdSig,   true);
   ArraySetAsSeries(atrBuf2,   true);
   ArraySetAsSeries(ma200Buf,  true);

   int cm  = CopyBuffer(g_macdHandle,  0, 0, 4, macdMain);
   int cs  = CopyBuffer(g_macdHandle,  1, 0, 4, macdSig);
   int ca  = CopyBuffer(g_atrHandle,   0, 0, 4, atrBuf2);
   int cma = CopyBuffer(g_ma200Handle, 0, 0, 3, ma200Buf);

   if(cm < 4 || cs < 4 || ca < 4 || cma < 3) return;

   // 柱状图 = 主线 - 信号线
   double hist1 = macdMain[1] - macdSig[1];
   double hist2 = macdMain[2] - macdSig[2];
   double macd1 = macdMain[1];
   double macd2 = macdMain[2];
   double atr1  = atrBuf2[1];
   double ma200 = ma200Buf[1];   // 上根K线的MA200值（已确认）

   if(atr1 <= 0 || ma200 <= 0) return;

   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   double bodyRatio = GetBodyRatio(1);

   // ===== MA200 趋势判断 =====
   // 价格在MA200上方 = 多头趋势
   // 价格在MA200下方 = 空头趋势
   bool aboveMA200 = (prevClose > ma200 + InpMA200Buffer);
   bool belowMA200 = (prevClose < ma200 - InpMA200Buffer);

   // 屏幕显示
   if(InpDebugMode)
   {
      string trendStr = "震荡区（MA200附近）";
      if(aboveMA200) trendStr = "多头趋势（价格在MA200上方）";
      if(belowMA200) trendStr = "空头趋势（价格在MA200下方）";

      string pendStr = "无";
      if(g_pendingBuy)  pendStr = "等待多头确认(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";
      if(g_pendingSell) pendStr = "等待空头确认(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";

      Comment("SniperEA v8.3 | ", _Symbol, " | ", EnumToString(Period()), "\n",
              "MA200:", DoubleToString(ma200, _Digits),
              " | 收盘:", DoubleToString(prevClose, _Digits), "\n",
              "趋势:", trendStr, "\n",
              "柱状图[1]:", DoubleToString(hist1, 5),
              " [2]:", DoubleToString(hist2, 5), "\n",
              "实体占比:", DoubleToString(bodyRatio * 100, 1), "% | 待入场:", pendStr, "\n",
              "ATR[1]:", DoubleToString(atr1, _Digits), " | 持仓:", CountPositions());
   }

   // 入场逻辑
   int posCount = CountPositions();
   if(posCount < InpMaxPositions)
   {
      bool flipUp   = (hist1 > 0 && hist2 <= 0);
      bool flipDown = (hist1 < 0 && hist2 >= 0);

      // ===== MA200过滤：翻转信号必须与大趋势方向一致 =====
      // 做多信号：柱状图向上翻转 + 价格在MA200上方
      if(flipUp && InpEnableBuy && !g_pendingBuy)
      {
         bool trendOk = !InpUseMA200Filter || aboveMA200;
         if(trendOk)
         {
            g_pendingSell = false;
            g_pendingBuy  = true;
            g_pendingBars = 0;
            Print("【信号触发-多】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                  " | 柱状图:", DoubleToString(hist1, 5),
                  " 前值:", DoubleToString(hist2, 5),
                  " | 收盘:", prevClose, " MA200:", DoubleToString(ma200, 2));
         }
         else
         {
            if(InpDebugMode)
               Print("【信号过滤-多】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                     " | 价格在MA200下方，不允许做多 | 收盘:", prevClose,
                     " MA200:", DoubleToString(ma200, 2));
         }
      }

      // 做空信号：柱状图向下翻转 + 价格在MA200下方
      if(flipDown && InpEnableSell && !g_pendingSell)
      {
         bool trendOk = !InpUseMA200Filter || belowMA200;
         if(trendOk)
         {
            g_pendingBuy  = false;
            g_pendingSell = true;
            g_pendingBars = 0;
            Print("【信号触发-空】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                  " | 柱状图:", DoubleToString(hist1, 5),
                  " 前值:", DoubleToString(hist2, 5),
                  " | 收盘:", prevClose, " MA200:", DoubleToString(ma200, 2));
         }
         else
         {
            if(InpDebugMode)
               Print("【信号过滤-空】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                     " | 价格在MA200上方，不允许做空 | 收盘:", prevClose,
                     " MA200:", DoubleToString(ma200, 2));
         }
      }

      // 确认入场
      if(g_pendingBuy || g_pendingSell)
      {
         g_pendingBars++;

         if(g_pendingBars > InpConfirmBars)
         {
            Print("【信号过期】等待", g_pendingBars - 1, "根K线未确认，取消");
            g_pendingBuy  = false;
            g_pendingSell = false;
            g_pendingBars = 0;
         }
         else
         {
            bool macdUp   = (macd1 >= macd2);
            bool macdDown = (macd1 <= macd2);

            // 做多确认：阳线 + 实体达标 + MA200方向确认
            if(g_pendingBuy &&
               IsBullishCandle(1) &&
               bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdUp) &&
               (!InpUseMA200Filter || aboveMA200))  // 确认时再次检查MA200
            {
               double ep  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
               double sl  = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
               double lot = CalculateLotSize(ep - sl);
               Print("【开多仓】实体:", DoubleToString(bodyRatio * 100, 1),
                     "% | 价格:", ep, " | SL:", sl, " | 手数:", lot,
                     " | MA200:", DoubleToString(ma200, 2));
               if(lot > 0)
               {
                  OpenPosition(ORDER_TYPE_BUY, ep, sl, lot);
                  g_pendingBuy  = false;
                  g_pendingBars = 0;
               }
            }

            // 做空确认：阴线 + 实体达标 + MA200方向确认
            if(g_pendingSell &&
               IsBearishCandle(1) &&
               bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdDown) &&
               (!InpUseMA200Filter || belowMA200))  // 确认时再次检查MA200
            {
               double ep  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
               double sl  = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
               double lot = CalculateLotSize(sl - ep);
               Print("【开空仓】实体:", DoubleToString(bodyRatio * 100, 1),
                     "% | 价格:", ep, " | SL:", sl, " | 手数:", lot,
                     " | MA200:", DoubleToString(ma200, 2));
               if(lot > 0)
               {
                  OpenPosition(ORDER_TYPE_SELL, ep, sl, lot);
                  g_pendingSell = false;
                  g_pendingBars = 0;
               }
            }
         }
      }
   }
   else
   {
      g_pendingBuy  = false;
      g_pendingSell = false;
      g_pendingBars = 0;
   }
}

//+------------------------------------------------------------------+
//| 移动止盈（严格K线级别，每根K线只调用一次）                          |
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
      ENUM_POSITION_TYPE posType =
         (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      if(posType == POSITION_TYPE_BUY)
      {
         double startLevel = openPrice + atr * InpTrailingStart;
         if(prevClose > startLevel)
         {
            double newSL = NormalizeDouble(prevClose - atr * InpTrailingStep, _Digits);
            if(newSL > curSL + _Point)
            {
               ModifyStopLoss(ticket, newSL);
               if(InpDebugMode)
                  Print("【移动止盈-多】票号:", ticket,
                        " | K线收盘:", prevClose,
                        " | 新SL:", newSL,
                        " | 旧SL:", curSL,
                        " | 浮盈:", DoubleToString(prevClose - openPrice, 2), "点");
            }
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         double startLevel = openPrice - atr * InpTrailingStart;
         if(prevClose < startLevel)
         {
            double newSL = NormalizeDouble(prevClose + atr * InpTrailingStep, _Digits);
            if(curSL == 0 || newSL < curSL - _Point)
            {
               ModifyStopLoss(ticket, newSL);
               if(InpDebugMode)
                  Print("【移动止盈-空】票号:", ticket,
                        " | K线收盘:", prevClose,
                        " | 新SL:", newSL,
                        " | 旧SL:", curSL,
                        " | 浮盈:", DoubleToString(openPrice - prevClose, 2), "点");
            }
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

bool IsBullishCandle(int shift)
{ return iClose(_Symbol, PERIOD_CURRENT, shift) > iOpen(_Symbol, PERIOD_CURRENT, shift); }

bool IsBearishCandle(int shift)
{ return iClose(_Symbol, PERIOD_CURRENT, shift) < iOpen(_Symbol, PERIOD_CURRENT, shift); }

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
   MqlTradeRequest req = {};
   MqlTradeResult  res = {};
   req.action       = TRADE_ACTION_DEAL;
   req.symbol       = _Symbol;
   req.volume       = lot;
   req.type         = type;
   req.price        = price;
   req.sl           = sl;
   req.tp           = 0;
   req.deviation    = 20;
   req.magic        = InpMagicNumber;
   req.comment      = InpComment;
   req.type_filling = ORDER_FILLING_IOC;
   if(!OrderSend(req, res))
      Print("开仓失败 | 错误:", GetLastError(), " | 类型:", EnumToString(type),
            " | 价格:", price, " | SL:", sl, " | 手数:", lot);
   else
      Print("开仓成功 | 票号:", res.order, " | 价格:", res.price, " | 手数:", lot);
}

//+------------------------------------------------------------------+
//| 修改止损                                                          |
//+------------------------------------------------------------------+
void ModifyStopLoss(ulong ticket, double newSL)
{
   MqlTradeRequest req = {};
   MqlTradeResult  res = {};
   req.action   = TRADE_ACTION_SLTP;
   req.position = ticket;
   req.symbol   = _Symbol;
   req.sl       = newSL;
   req.tp       = PositionGetDouble(POSITION_TP);
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
