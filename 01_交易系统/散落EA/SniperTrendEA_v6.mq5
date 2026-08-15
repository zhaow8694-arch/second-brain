//+------------------------------------------------------------------+
//|                                            SniperTrendEA_v6.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                              v6.0 - 结构性移动止盈                |
//|                                                                  |
//|  修复内容：                                                        |
//|  v5问题：移动止盈每个Tick都更新，止损贴价格太近，正常回调就出局      |
//|          空单在上涨行情中止损被反向推高，造成巨亏                    |
//|  v6方案：移动止盈只在新K线开始时（收盘确认后）更新一次              |
//|          这符合文章"结构性止盈"思路，给价格足够的呼吸空间           |
//|          同时调大TrailingStart和TrailingStep参数                   |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v6 - Wyckoff + Evil MACD"
#property version   "6.00"
#property strict

//--- 输入参数
input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== 入场过滤 ==="
input double InpBodyRatio      = 0.55;     // K线实体占比阈值（≥55%）
input int    InpConfirmBars    = 5;        // 翻转后等待确认的最大K线数
input bool   InpRequireMACDDir = false;    // 是否要求MACD主线方向一致

input group "=== 风险管理 ==="
input double InpRiskPercent    = 1.0;      // 单笔风险占账户比例（%）
input double InpATRMultiplier  = 1.5;      // 止损 = ATR × 此倍数
input int    InpATRPeriod      = 14;       // ATR 周期
input double InpTrailingStart  = 3.0;      // 移动止盈启动距离（ATR倍数）——v6调大，给利润空间
input double InpTrailingStep   = 1.5;      // 移动止盈步长（ATR倍数）——v6调大，避免贴价格
input int    InpMaxPositions   = 1;        // 最大持仓数量

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260213;
input string InpComment        = "SniperEA_v6";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

//--- 指标句柄
int g_macdHandle;
int g_atrHandle;

//--- 待入场状态
bool g_pendingBuy  = false;
bool g_pendingSell = false;
int  g_pendingBars = 0;

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

   g_pendingBuy  = false;
   g_pendingSell = false;
   g_pendingBars = 0;

   Print("SniperTrendEA v6 初始化成功 | 品种:", _Symbol,
         " | 周期:", EnumToString(Period()),
         " | 移动止盈：K线收盘更新 | 启动:", InpTrailingStart, "×ATR",
         " | 步长:", InpTrailingStep, "×ATR");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 释放                                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_macdHandle != INVALID_HANDLE) IndicatorRelease(g_macdHandle);
   if(g_atrHandle  != INVALID_HANDLE) IndicatorRelease(g_atrHandle);
   Comment("");
}

//+------------------------------------------------------------------+
//| 主逻辑                                                            |
//| v6 关键改动：所有逻辑（含移动止盈）只在新K线时执行                  |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);

   // 只在新K线开始时执行（K线收盘确认后）
   if(currentBarTime == lastBarTime) return;
   lastBarTime = currentBarTime;

   // 读取指标数据
   // MT5 iMACD: Buffer 0 = 主线, Buffer 1 = 信号线
   double macdMain[4], macdSig[4], atrBuf[4];
   ArraySetAsSeries(macdMain, true);
   ArraySetAsSeries(macdSig,  true);
   ArraySetAsSeries(atrBuf,   true);

   int cm = CopyBuffer(g_macdHandle, 0, 0, 4, macdMain);
   int cs = CopyBuffer(g_macdHandle, 1, 0, 4, macdSig);
   int ca = CopyBuffer(g_atrHandle,  0, 0, 4, atrBuf);

   if(cm < 4 || cs < 4 || ca < 4) return;  // 预热期跳过

   // 计算柱状图 = 主线 - 信号线
   double hist1 = macdMain[1] - macdSig[1];  // 上根完成K线
   double hist2 = macdMain[2] - macdSig[2];  // 上上根
   double macd1 = macdMain[1];
   double macd2 = macdMain[2];
   double atr1  = atrBuf[1];   // 上根K线的ATR（已确认）

   if(atr1 <= 0) return;

   double bodyRatio = GetBodyRatio(1);

   // ===== 第一优先：管理已有持仓的移动止盈 =====
   // 在新K线时，用上根K线的收盘价和ATR来更新止盈
   // 这样每根K线只更新一次，避免Tick级别的过度敏感
   if(CountPositions() > 0)
      ManageTrailingStop(atr1);

   // ===== 屏幕显示 =====
   if(InpDebugMode)
   {
      string pendStr = "无";
      if(g_pendingBuy)  pendStr = "等待多头确认(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";
      if(g_pendingSell) pendStr = "等待空头确认(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";
      Comment("SniperEA v6 | ", _Symbol, " | ", EnumToString(Period()), "\n",
              "MACD主线[1]:", DoubleToString(macd1, 5),
              " 信号线[1]:", DoubleToString(macdSig[1], 5), "\n",
              "柱状图[1]:", DoubleToString(hist1, 5),
              " [2]:", DoubleToString(hist2, 5), "\n",
              "实体占比:", DoubleToString(bodyRatio * 100, 1), "% | 待入场:", pendStr, "\n",
              "ATR[1]:", DoubleToString(atr1, _Digits), " | 持仓:", CountPositions());
   }

   // ===== 入场逻辑 =====
   int posCount = CountPositions();
   if(posCount < InpMaxPositions)
   {
      // 检测MACD柱状图翻转
      bool flipUp   = (hist1 > 0 && hist2 <= 0);
      bool flipDown = (hist1 < 0 && hist2 >= 0);

      if(flipUp && InpEnableBuy && !g_pendingBuy)
      {
         g_pendingSell = false;
         g_pendingBuy  = true;
         g_pendingBars = 0;
         Print("【信号触发-多】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
               " | 柱状图:", DoubleToString(hist1, 5),
               " 前值:", DoubleToString(hist2, 5));
      }

      if(flipDown && InpEnableSell && !g_pendingSell)
      {
         g_pendingBuy  = false;
         g_pendingSell = true;
         g_pendingBars = 0;
         Print("【信号触发-空】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
               " | 柱状图:", DoubleToString(hist1, 5),
               " 前值:", DoubleToString(hist2, 5));
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

            // 做多确认：阳线 + 实体达标
            if(g_pendingBuy &&
               IsBullishCandle(1) &&
               bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdUp))
            {
               double ep  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
               double sl  = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
               double lot = CalculateLotSize(ep - sl);
               Print("【开多仓】实体:", DoubleToString(bodyRatio * 100, 1),
                     "% | 价格:", ep, " | SL:", sl, " | 手数:", lot);
               if(lot > 0)
               {
                  OpenPosition(ORDER_TYPE_BUY, ep, sl, lot);
                  g_pendingBuy  = false;
                  g_pendingBars = 0;
               }
            }

            // 做空确认：阴线 + 实体达标
            if(g_pendingSell &&
               IsBearishCandle(1) &&
               bodyRatio >= InpBodyRatio &&
               (!InpRequireMACDDir || macdDown))
            {
               double ep  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
               double sl  = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
               double lot = CalculateLotSize(sl - ep);
               Print("【开空仓】实体:", DoubleToString(bodyRatio * 100, 1),
                     "% | 价格:", ep, " | SL:", sl, " | 手数:", lot);
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
      // 有持仓时清除待入场状态
      g_pendingBuy  = false;
      g_pendingSell = false;
      g_pendingBars = 0;
   }
}

//+------------------------------------------------------------------+
//| 移动止盈（只在K线收盘时调用，每根K线最多更新一次）                  |
//| 逻辑：用上根K线的最高/最低价作为参考，而不是实时Bid/Ask             |
//+------------------------------------------------------------------+
void ManageTrailingStop(double atr)
{
   if(atr <= 0) return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curSL     = PositionGetDouble(POSITION_SL);

      // 使用上根K线的收盘价作为参考（已确认的价格，不是实时价）
      double refClose  = iClose(_Symbol, PERIOD_CURRENT, 1);

      ENUM_POSITION_TYPE posType =
         (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      if(posType == POSITION_TYPE_BUY)
      {
         // 多单：当上根K线收盘价超过开仓价 + TrailingStart×ATR 时启动
         double startLevel = openPrice + atr * InpTrailingStart;
         if(refClose > startLevel)
         {
            // 新止损 = 上根K线收盘价 - TrailingStep×ATR
            double newSL = NormalizeDouble(refClose - atr * InpTrailingStep, _Digits);
            // 止损只能往上移，不能往下
            if(newSL > curSL + _Point)
            {
               ModifyStopLoss(ticket, newSL);
               if(InpDebugMode)
                  Print("【移动止盈-多】票号:", ticket,
                        " | 参考收盘:", refClose,
                        " | 新SL:", newSL,
                        " | 旧SL:", curSL);
            }
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         // 空单：当上根K线收盘价低于开仓价 - TrailingStart×ATR 时启动
         double startLevel = openPrice - atr * InpTrailingStart;
         if(refClose < startLevel)
         {
            // 新止损 = 上根K线收盘价 + TrailingStep×ATR
            double newSL = NormalizeDouble(refClose + atr * InpTrailingStep, _Digits);
            // 止损只能往下移，不能往上
            if(curSL == 0 || newSL < curSL - _Point)
            {
               ModifyStopLoss(ticket, newSL);
               if(InpDebugMode)
                  Print("【移动止盈-空】票号:", ticket,
                        " | 参考收盘:", refClose,
                        " | 新SL:", newSL,
                        " | 旧SL:", curSL);
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
