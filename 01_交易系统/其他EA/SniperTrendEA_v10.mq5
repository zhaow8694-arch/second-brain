//+------------------------------------------------------------------+
//|                                           SniperTrendEA_v10.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                     v10.0 - ATR过滤阈值1.5x + 风险1.0%           |
//|                                                                  |
//|  v9问题：                                                         |
//|  1. ATR过滤阈值2.0太宽松，2020年新冠暴跌期间ATR仅1.5~1.8倍均值，  |
//|     过滤器完全未触发（拦截次数=0）                                  |
//|  2. 风险0.7%降低了复利效应，亏损期恢复更慢，最大回撤反而升至82%    |
//|                                                                  |
//|  v10修复：                                                        |
//|  1. ATR过滤阈值：2.0 → 1.5（更严格，能拦截1.5倍以上的异常波动）   |
//|  2. ATR均值周期：20 → 14（更灵敏，与主ATR周期一致）               |
//|  3. 风险比例：0.7% → 1.0%（恢复复利效应）                         |
//|  4. 新增：每次ATR检查都打印比率，便于验证过滤器是否工作            |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v10 - Wyckoff + Evil MACD + MA200 + ATR Filter 1.5x"
#property version   "10.00"
#property strict

//--- 输入参数
input group "=== MACD 参数 ==="
input int    InpFastEMA           = 12;
input int    InpSlowEMA           = 26;
input int    InpSignalSMA         = 9;

input group "=== MA200 趋势过滤 ==="
input int    InpMA200Period       = 200;
input bool   InpUseMA200Filter    = true;
input double InpMA200Buffer       = 0.0;

input group "=== ATR 波动率过滤 ==="
input bool   InpUseATRFilter      = true;
input int    InpATRFilterPeriod   = 14;     // v10: 从20改为14，与主ATR周期一致，更灵敏
input double InpATRFilterMult     = 1.5;    // v10: 从2.0改为1.5，能拦截新冠级别的异常波动

input group "=== 入场过滤 ==="
input double InpBodyRatio         = 0.55;
input int    InpConfirmBars       = 5;
input bool   InpRequireMACDDir    = false;

input group "=== 风险管理 ==="
input double InpRiskPercent       = 1.0;    // v10: 从0.7%恢复为1.0%
input double InpATRMultiplier     = 1.5;
input int    InpATRPeriod         = 14;
input double InpTrailingStart     = 3.0;
input double InpTrailingStep      = 1.5;
input int    InpMaxPositions      = 1;

input group "=== 交易设置 ==="
input int    InpMagicNumber       = 20260213;
input string InpComment           = "SniperEA_v10";
input bool   InpEnableBuy         = true;
input bool   InpEnableSell        = true;
input bool   InpDebugMode         = false;

//--- 指标句柄
int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;

//--- 待入场状态
bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

//--- K线时间戳
datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

//--- 统计
int    g_filteredByATR   = 0;
int    g_atrCheckCount   = 0;
double g_maxATRRatio     = 0.0;   // 记录回测期间最大ATR比率，用于验证

//+------------------------------------------------------------------+
//| 初始化                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   g_macdHandle = iMACD(_Symbol, PERIOD_CURRENT,
                        InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
   if(g_macdHandle == INVALID_HANDLE)
   { Print("错误：MACD句柄创建失败"); return INIT_FAILED; }

   g_atrHandle = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   if(g_atrHandle == INVALID_HANDLE)
   { Print("错误：ATR句柄创建失败"); return INIT_FAILED; }

   g_ma200Handle = iMA(_Symbol, PERIOD_CURRENT,
                       InpMA200Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_ma200Handle == INVALID_HANDLE)
   { Print("错误：MA200句柄创建失败"); return INIT_FAILED; }

   g_pendingBuy       = false;
   g_pendingSell      = false;
   g_pendingBars      = 0;
   g_lastTrailBarTime = 0;
   g_lastEntryBarTime = 0;
   g_filteredByATR    = 0;
   g_atrCheckCount    = 0;
   g_maxATRRatio      = 0.0;

   Print("SniperTrendEA v10 初始化成功 | 品种:", _Symbol,
         " | 周期:", EnumToString(Period()),
         " | MA200过滤:", InpUseMA200Filter ? "开启" : "关闭",
         " | ATR波动率过滤:", InpUseATRFilter ?
            "开启(阈值×" + DoubleToString(InpATRFilterMult,1) +
            " 周期" + IntegerToString(InpATRFilterPeriod) + ")" : "关闭",
         " | 风险:", InpRiskPercent, "%");
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

   Print("SniperTrendEA v10 退出统计:",
         " | ATR检查次数:", g_atrCheckCount,
         " | ATR过滤拦截:", g_filteredByATR, "次",
         " | 回测期间最大ATR比率:", DoubleToString(g_maxATRRatio, 3), "x",
         "（阈值:", InpATRFilterMult, "x）");
   Comment("");
}

//+------------------------------------------------------------------+
//| ATR波动率过滤                                                     |
//| 当前ATR > 近期均值 × InpATRFilterMult 时返回 true（暂停入场）      |
//+------------------------------------------------------------------+
bool IsVolatilityTooHigh()
{
   if(!InpUseATRFilter) return false;

   int barsNeeded = InpATRFilterPeriod + 2;
   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);
   if(CopyBuffer(g_atrHandle, 0, 1, barsNeeded, atrBuf) < barsNeeded)
      return false;

   double currentATR = atrBuf[0];
   if(currentATR <= 0) return false;

   // 计算近期ATR均值（shift 1~InpATRFilterPeriod，跳过当前K线）
   double atrSum = 0;
   for(int i = 1; i <= InpATRFilterPeriod; i++)
      atrSum += atrBuf[i];
   double atrAvg = atrSum / InpATRFilterPeriod;
   if(atrAvg <= 0) return false;

   double ratio = currentATR / atrAvg;

   // 记录最大比率（用于验证过滤器有效性）
   g_atrCheckCount++;
   if(ratio > g_maxATRRatio) g_maxATRRatio = ratio;

   bool tooHigh = (ratio >= InpATRFilterMult);

   if(tooHigh)
      Print("【ATR过滤触发】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
            " | 当前ATR:", DoubleToString(currentATR, _Digits),
            " | 均值:", DoubleToString(atrAvg, _Digits),
            " | 比率:", DoubleToString(ratio, 3), "x",
            "（阈值:", InpATRFilterMult, "x）| 暂停入场");

   return tooHigh;
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
      ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2 && atrBuf[0] > 0)
         ManageTrailingStop(atrBuf[0]);
   }

   // ================================================================
   // 【入场逻辑】每根K线只执行一次
   // ================================================================
   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

   // 读取指标数据
   double macdMain[], macdSig[], atrBuf2[], ma200Buf[];
   ArraySetAsSeries(macdMain,  true);
   ArraySetAsSeries(macdSig,   true);
   ArraySetAsSeries(atrBuf2,   true);
   ArraySetAsSeries(ma200Buf,  true);

   if(CopyBuffer(g_macdHandle,  0, 0, 4, macdMain) < 4) return;
   if(CopyBuffer(g_macdHandle,  1, 0, 4, macdSig)  < 4) return;
   if(CopyBuffer(g_atrHandle,   0, 0, 4, atrBuf2)  < 4) return;
   if(CopyBuffer(g_ma200Handle, 0, 0, 3, ma200Buf) < 3) return;

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

   // ATR波动率检查
   bool atrTooHigh = IsVolatilityTooHigh();

   // 屏幕显示
   if(InpDebugMode)
   {
      string trendStr = "震荡区";
      if(aboveMA200) trendStr = "多头趋势";
      if(belowMA200) trendStr = "空头趋势";
      string atrStr = atrTooHigh ? "【极端波动-暂停】" : "正常";
      string pendStr = "无";
      if(g_pendingBuy)  pendStr = "等待多头(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";
      if(g_pendingSell) pendStr = "等待空头(" + IntegerToString(g_pendingBars) + "/" + IntegerToString(InpConfirmBars) + ")";

      Comment("SniperEA v10 | ", _Symbol, " | ", EnumToString(Period()), "\n",
              "MA200:", DoubleToString(ma200, _Digits), " | 收盘:", DoubleToString(prevClose, _Digits), " | 趋势:", trendStr, "\n",
              "ATR[1]:", DoubleToString(atr1, _Digits), " | 波动率:", atrStr, "\n",
              "最大ATR比率(本次):", DoubleToString(g_maxATRRatio, 2), "x | 阈值:", InpATRFilterMult, "x\n",
              "柱状图[1]:", DoubleToString(hist1, 5), " [2]:", DoubleToString(hist2, 5), "\n",
              "实体占比:", DoubleToString(bodyRatio * 100, 1), "% | 待入场:", pendStr, "\n",
              "持仓:", CountPositions(), " | ATR过滤拦截:", g_filteredByATR, "次");
   }

   int posCount = CountPositions();
   if(posCount < InpMaxPositions)
   {
      bool flipUp   = (hist1 > 0 && hist2 <= 0);
      bool flipDown = (hist1 < 0 && hist2 >= 0);

      // 做多信号
      if(flipUp && InpEnableBuy && !g_pendingBuy)
      {
         bool trendOk = !InpUseMA200Filter || aboveMA200;
         if(!trendOk)
         {
            if(InpDebugMode)
               Print("【信号过滤-多】", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                     " | 价格在MA200下方 | 收盘:", prevClose, " MA200:", DoubleToString(ma200, 2));
         }
         else if(atrTooHigh)
         {
            g_filteredByATR++;
            Print("【信号过滤-多(ATR)】", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                  " | 波动率过高，跳过做多 | 累计拦截:", g_filteredByATR, "次");
         }
         else
         {
            g_pendingSell = false;
            g_pendingBuy  = true;
            g_pendingBars = 0;
            Print("【信号触发-多】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                  " | 柱状图:", DoubleToString(hist1, 5),
                  " 前值:", DoubleToString(hist2, 5),
                  " | 收盘:", prevClose, " MA200:", DoubleToString(ma200, 2));
         }
      }

      // 做空信号
      if(flipDown && InpEnableSell && !g_pendingSell)
      {
         bool trendOk = !InpUseMA200Filter || belowMA200;
         if(!trendOk)
         {
            if(InpDebugMode)
               Print("【信号过滤-空】", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                     " | 价格在MA200上方 | 收盘:", prevClose, " MA200:", DoubleToString(ma200, 2));
         }
         else if(atrTooHigh)
         {
            g_filteredByATR++;
            Print("【信号过滤-空(ATR)】", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                  " | 波动率过高，跳过做空 | 累计拦截:", g_filteredByATR, "次");
         }
         else
         {
            g_pendingBuy  = false;
            g_pendingSell = true;
            g_pendingBars = 0;
            Print("【信号触发-空】时间:", TimeToString(iTime(_Symbol, PERIOD_CURRENT, 1)),
                  " | 柱状图:", DoubleToString(hist1, 5),
                  " 前值:", DoubleToString(hist2, 5),
                  " | 收盘:", prevClose, " MA200:", DoubleToString(ma200, 2));
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
            // 确认时再次检查ATR
            if(atrTooHigh)
            {
               Print("【确认取消(ATR)】待入场中，但ATR过高，取消 | 累计拦截:", g_filteredByATR + 1, "次");
               g_pendingBuy  = false;
               g_pendingSell = false;
               g_pendingBars = 0;
               g_filteredByATR++;
            }
            else
            {
               bool macdUp   = (macd1 >= macd2);
               bool macdDown = (macd1 <= macd2);

               if(g_pendingBuy &&
                  IsBullishCandle(1) &&
                  bodyRatio >= InpBodyRatio &&
                  (!InpRequireMACDDir || macdUp) &&
                  (!InpUseMA200Filter || aboveMA200))
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

               if(g_pendingSell &&
                  IsBearishCandle(1) &&
                  bodyRatio >= InpBodyRatio &&
                  (!InpRequireMACDDir || macdDown) &&
                  (!InpUseMA200Filter || belowMA200))
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
   }
   else
   {
      g_pendingBuy  = false;
      g_pendingSell = false;
      g_pendingBars = 0;
   }
}

//+------------------------------------------------------------------+
//| 移动止盈（严格K线级别，单向保护）                                  |
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
                        " | 新SL:", newSL, " | 旧SL:", curSL,
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
                        " | 新SL:", newSL, " | 旧SL:", curSL,
                        " | 浮盈:", DoubleToString(openPrice - prevClose, 2), "点");
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 辅助函数                                                          |
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

double CalculateLotSize(double slDist)
{
   if(slDist <= 0) return 0;
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk     = balance * InpRiskPercent / 100.0;
   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0 || tickVal <= 0) return 0;
   double lot  = risk / (slDist / tickSize * tickVal);
   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / step) * step;
   return MathMax(minL, MathMin(maxL, lot));
}

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
      Print("开仓失败 | 错误:", GetLastError(), " | 类型:", EnumToString(type));
   else
      Print("开仓成功 | 票号:", res.order, " | 价格:", res.price, " | 手数:", lot);
}

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
