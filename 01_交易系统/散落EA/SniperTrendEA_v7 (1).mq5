//+------------------------------------------------------------------+
//|                                            SniperTrendEA_v7.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                              v7.0 - 严格K线级别移动止盈            |
//|                                                                  |
//|  修复内容：                                                        |
//|  v6问题：移动止盈虽在OnTick新K线判断内调用，但参考价格(iClose[1])   |
//|          在新K线刚开始时等于上根收盘价，随后每个Tick价格变动都会     |
//|          重新触发条件判断，导致止损仍然Tick级别更新                  |
//|  v7方案：用全局变量 g_trailBarTime 记录"本根K线已执行过移动止盈"    |
//|          每根K线只在第一个Tick时执行一次，之后的Tick全部跳过        |
//|          移动止盈参考价格固定为上根K线收盘价(已确认，不随Tick变化)   |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v7 - Wyckoff + Evil MACD"
#property version   "7.00"
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
input double InpTrailingStart  = 3.0;      // 移动止盈启动距离（ATR倍数）
input double InpTrailingStep   = 1.5;      // 移动止盈步长（ATR倍数）
input int    InpMaxPositions   = 1;        // 最大持仓数量

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260213;
input string InpComment        = "SniperEA_v7";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

//--- 指标句柄
int g_macdHandle;
int g_atrHandle;

//--- 待入场状态
bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

//--- 关键修复：记录上次执行移动止盈的K线时间
//    每根K线只允许执行一次移动止盈
datetime g_lastTrailBarTime = 0;

//--- 记录上次执行入场逻辑的K线时间
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

   g_pendingBuy       = false;
   g_pendingSell      = false;
   g_pendingBars      = 0;
   g_lastTrailBarTime = 0;
   g_lastEntryBarTime = 0;

   Print("SniperTrendEA v7 初始化成功 | 品种:", _Symbol,
         " | 周期:", EnumToString(Period()),
         " | 移动止盈：严格K线级别（每根K线仅执行一次）",
         " | 启动:", InpTrailingStart, "×ATR",
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
//| v7 核心：移动止盈和入场逻辑完全分离，各自独立判断K线时间            |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == 0) return;

   // ================================================================
   // 【移动止盈】每根K线只执行一次
   // 使用独立的时间戳 g_lastTrailBarTime 控制
   // ================================================================
   if(currentBarTime != g_lastTrailBarTime && CountPositions() > 0)
   {
      g_lastTrailBarTime = currentBarTime;  // 立即标记，防止本根K线内重复执行

      // 读取上根K线已确认的ATR值（shift=1，已收盘，不会再变化）
      double atrBuf[2];
      ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2)
      {
         double atr1 = atrBuf[0];  // 上根K线的ATR（已确认）
         if(atr1 > 0)
            ManageTrailingStop(atr1);
      }
   }

   // ================================================================
   // 【入场逻辑】每根K线只执行一次
   // 使用独立的时间戳 g_lastEntryBarTime 控制
   // ================================================================
   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

   // 读取指标数据（使用已确认的上根K线数据，shift=1）
   double macdMain[4], macdSig[4], atrBuf2[4];
   ArraySetAsSeries(macdMain, true);
   ArraySetAsSeries(macdSig,  true);
   ArraySetAsSeries(atrBuf2,  true);

   int cm = CopyBuffer(g_macdHandle, 0, 0, 4, macdMain);
   int cs = CopyBuffer(g_macdHandle, 1, 0, 4, macdSig);
   int ca = CopyBuffer(g_atrHandle,  0, 0, 4, atrBuf2);

   if(cm < 4 || cs < 4 || ca < 4) return;  // 预热期跳过

   // 柱状图 = 主线 - 信号线（MT5 iMACD 无 Buffer 2）
   double hist1 = macdMain[1] - macdSig[1];  // 上根完成K线
   double hist2 = macdMain[2] - macdSig[2];  // 上上根
   double macd1 = macdMain[1];
   double macd2 = macdMain[2];
   double atr1  = atrBuf2[1];

   if(atr1 <= 0) return;

   double bodyRatio = GetBodyRatio(1);

   // 屏幕显示
   if(InpDebugMode)
   {
      string pendStr = "无";
      if(g_pendingBuy)  pendStr = "等待多头确认(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";
      if(g_pendingSell) pendStr = "等待空头确认(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";
      Comment("SniperEA v7 | ", _Symbol, " | ", EnumToString(Period()), "\n",
              "MACD主线[1]:", DoubleToString(macd1, 5),
              " 信号线[1]:", DoubleToString(macdSig[1], 5), "\n",
              "柱状图[1]:", DoubleToString(hist1, 5),
              " [2]:", DoubleToString(hist2, 5), "\n",
              "实体占比:", DoubleToString(bodyRatio * 100, 1), "% | 待入场:", pendStr, "\n",
              "ATR[1]:", DoubleToString(atr1, _Digits), " | 持仓:", CountPositions());
   }

   // 入场逻辑
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
      g_pendingBuy  = false;
      g_pendingSell = false;
      g_pendingBars = 0;
   }
}

//+------------------------------------------------------------------+
//| 移动止盈（严格K线级别，每根K线只调用一次）                          |
//| 参考价格：上根K线收盘价（iClose[1]，已确认，整根K线内固定不变）      |
//+------------------------------------------------------------------+
void ManageTrailingStop(double atr)
{
   if(atr <= 0) return;

   // 使用上根K线收盘价作为参考（shift=1，已确认，不随Tick变化）
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
         // 多单：上根K线收盘价超过 开仓价 + TrailingStart×ATR 时启动
         double startLevel = openPrice + atr * InpTrailingStart;
         if(prevClose > startLevel)
         {
            // 新止损 = 上根K线收盘价 - TrailingStep×ATR
            double newSL = NormalizeDouble(prevClose - atr * InpTrailingStep, _Digits);
            // 止损只能往上移，不能往下
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
         // 空单：上根K线收盘价低于 开仓价 - TrailingStart×ATR 时启动
         double startLevel = openPrice - atr * InpTrailingStart;
         if(prevClose < startLevel)
         {
            // 新止损 = 上根K线收盘价 + TrailingStep×ATR
            double newSL = NormalizeDouble(prevClose + atr * InpTrailingStep, _Digits);
            // 止损只能往下移，不能往上
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
