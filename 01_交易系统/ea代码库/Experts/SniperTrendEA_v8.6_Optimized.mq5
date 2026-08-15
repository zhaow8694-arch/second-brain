//+------------------------------------------------------------------+
//|                                  SniperTrendEA_v8.6_Optimized.mq5 |
//|     基于威科夫趋势线突破 + Evil MACD + Z-Wei 哲学过滤的优化版本      |
//|                                                                  |
//|  v8.6 优化重点：                                                  |
//|  1) 保留 v8.5 核心交易哲学：MACD 翻转、MA200趋势、危险K线、影线过滤。 |
//|  2) 将 pending 状态改为单一方向状态，减少买卖状态互相残留。          |
//|  3) 增强交易执行：自动选择 Filling、检查交易权限、检查点差。          |
//|  4) 增强风控：止损距离自动适配 StopsLevel，手数不足不强行最小手。    |
//|  5) 增强移动止盈：支持保本保护 + 单次候选止损计算，减少重复改 SL。   |
//|  6) 减少重复 OHLC 读取：统一 K 线质量结构体。                       |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.6 - Optimized by ChatGPT"
#property version   "8.60"
#property strict

//+------------------------------------------------------------------+
//| 输入参数                                                          |
//+------------------------------------------------------------------+
input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 趋势过滤（Buffer 使用 ATR 倍数）==="
input int    InpMA200Period    = 200;       // 趋势均线周期
input bool   InpUseMA200Filter = true;      // 是否启用 MA200 过滤
input double InpMA200BufferATR = 0.0;       // MA200 缓冲区（ATR倍数，0=严格过滤）

input group "=== 入场质量过滤（Z-Wei 哲学）==="
input double InpBodyRatio            = 0.60;  // K线实体占比阈值
input double InpMaxCandleATR         = 2.5;   // K线最大振幅（ATR倍数），0=关闭
input double InpMaxOppositeShadow    = 0.20;  // 反向影线最大占比
input bool   InpRequireFollowThrough = false; // 是否要求收盘创近N根K线极值
input int    InpFollowThroughBars    = 3;     // 跟随确认回看K线数
input int    InpConfirmBars          = 4;     // 翻转后等待确认的最大K线数
input bool   InpRequireMACDDir       = false; // 是否要求 MACD 主线方向一致
input bool   InpCancelPendingOnOppositeFlip = true; // 反向翻转出现时是否取消旧 pending

input group "=== ADX 趋势过滤 ==="
input bool   InpUseADX          = false;
input int    InpADXPeriod       = 14;
input double InpADXThreshold    = 25.0;

input group "=== 时间过滤 ==="
input bool   InpUseTimeFilter   = false;
input int    InpStartHour       = 8;
input int    InpEndHour         = 20;

input group "=== 波动率过滤 ==="
input bool   InpUseATRFilter    = false;
input int    InpATRFilterPeriod = 20;
input double InpATRFilterRatio  = 1.0;

input group "=== 日线趋势确认 ==="
input bool   InpUseDailyFilter  = false;

input group "=== 风险管理 ==="
input double InpRiskPercent    = 0.5;       // 单笔风险占账户比例（%）
input bool   InpUseEquityRisk  = true;      // true=用净值计算风险，false=用余额
input double InpATRMultiplier  = 1.5;       // 初始止损 = ATR × 此倍数
input int    InpATRPeriod      = 14;        // ATR 周期
input bool   InpAllowMinLotWhenRiskTooSmall = false; // 风险手数低于最小手数时是否强制最小手
input int    InpMaxPositions   = 1;         // 最大持仓数量

input group "=== 保本与移动止盈 ==="
input bool   InpUseBreakEven     = true;    // 是否启用保本
input double InpBreakEvenStart   = 2.0;     // 浮盈达到 ATR×N 后启动保本
input double InpBreakEvenBuffer  = 0.10;    // 保本止损加减 ATR×N
input bool   InpUseTrailingStop  = true;    // 是否启用移动止盈
input double InpTrailingStart    = 5.0;     // 移动止盈启动（ATR倍数）
input double InpTrailingStep     = 2.5;     // 移动止盈步长（ATR倍数）

input group "=== 交易执行设置 ==="
input int    InpMagicNumber      = 20260506;
input string InpComment          = "SniperEA_v8.6_opt";
input bool   InpEnableBuy        = true;
input bool   InpEnableSell       = true;
input int    InpDeviationPoints  = 20;      // 最大允许滑点/偏差（points）
input bool   InpUseSpreadFilter  = false;   // 是否启用点差过滤
input int    InpMaxSpreadPoints  = 30;      // 最大允许点差（points）
input bool   InpDebugMode        = true;

//+------------------------------------------------------------------+
//| 全局变量                                                          |
//+------------------------------------------------------------------+
int g_macdHandle       = INVALID_HANDLE;
int g_atrHandle        = INVALID_HANDLE;
int g_ma200Handle      = INVALID_HANDLE;
int g_adxHandle        = INVALID_HANDLE;
int g_dailyMA200Handle = INVALID_HANDLE;

// pending 方向：0=无，1=等待做多，-1=等待做空
int      g_pendingDir  = 0;
int      g_pendingBars = 0;

datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

ENUM_ORDER_TYPE_FILLING g_fillingMode = ORDER_FILLING_IOC;

//+------------------------------------------------------------------+
//| K线质量结构体                                                     |
//+------------------------------------------------------------------+
struct SCandleQuality
{
   double open;
   double close;
   double high;
   double low;
   double range;
   double body;
   double bodyRatio;
   double upperRatio;
   double lowerRatio;
   bool   bullish;
   bool   bearish;
   bool   dangerous;
};

//+------------------------------------------------------------------+
//| 初始化                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!ValidateInputs())
      return INIT_PARAMETERS_INCORRECT;

   g_macdHandle = iMACD(_Symbol, PERIOD_CURRENT, InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
   if(g_macdHandle == INVALID_HANDLE)
   {
      Print("MACD 句柄创建失败，错误:", GetLastError());
      return INIT_FAILED;
   }

   g_atrHandle = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   if(g_atrHandle == INVALID_HANDLE)
   {
      Print("ATR 句柄创建失败，错误:", GetLastError());
      return INIT_FAILED;
   }

   g_ma200Handle = iMA(_Symbol, PERIOD_CURRENT, InpMA200Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_ma200Handle == INVALID_HANDLE)
   {
      Print("MA200 句柄创建失败，错误:", GetLastError());
      return INIT_FAILED;
   }

   if(InpUseADX)
   {
      g_adxHandle = iADX(_Symbol, PERIOD_CURRENT, InpADXPeriod);
      if(g_adxHandle == INVALID_HANDLE)
      {
         Print("ADX 句柄创建失败，错误:", GetLastError());
         return INIT_FAILED;
      }
   }


   if(InpUseDailyFilter)
   {
      g_dailyMA200Handle = iMA(_Symbol, PERIOD_D1, 200, 0, MODE_SMA, PRICE_CLOSE);
      if(g_dailyMA200Handle == INVALID_HANDLE)
      {
         Print("D1 MA200 句柄创建失败，错误:", GetLastError());
         return INIT_FAILED;
      }
   }

   g_fillingMode = DetectFillingMode();
   ResetPending();
   g_lastTrailBarTime = 0;
   g_lastEntryBarTime = 0;

   Print("SniperTrendEA v8.6 Optimized 初始化成功 | ", _Symbol, " ", EnumToString((ENUM_TIMEFRAMES)_Period),
         " | Filling:", EnumToString(g_fillingMode),
         " | 危险K线阈值:", InpMaxCandleATR, "×ATR",
         " | 反向影线限制:", DoubleToString(InpMaxOppositeShadow * 100.0, 0), "%",
         " | 保本:", InpUseBreakEven ? "ON" : "OFF",
         " | 移动止盈:", InpUseTrailingStop ? "ON" : "OFF");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 释放                                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_macdHandle       != INVALID_HANDLE) IndicatorRelease(g_macdHandle);
   if(g_atrHandle        != INVALID_HANDLE) IndicatorRelease(g_atrHandle);
   if(g_ma200Handle      != INVALID_HANDLE) IndicatorRelease(g_ma200Handle);
   if(g_adxHandle        != INVALID_HANDLE) IndicatorRelease(g_adxHandle);
   if(g_dailyMA200Handle != INVALID_HANDLE) IndicatorRelease(g_dailyMA200Handle);
   Comment("");
}

//+------------------------------------------------------------------+
//| 主逻辑                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == 0)
      return;

   // 移动止盈 / 保本：每根 K 线只执行一次，避免同一根 K 线反复修改 SL。
   if(currentBarTime != g_lastTrailBarTime && CountPositions() > 0)
   {
      g_lastTrailBarTime = currentBarTime;

      double atrTrail[];
      ArrayResize(atrTrail, 1);
      ArraySetAsSeries(atrTrail, true);

      if(CopyBuffer(g_atrHandle, 0, 1, 1, atrTrail) == 1 && atrTrail[0] > 0.0)
         ManageProtectionStops(atrTrail[0]);
   }

   // 入场逻辑：每根新 K 线只执行一次。
   if(currentBarTime == g_lastEntryBarTime)
      return;
   g_lastEntryBarTime = currentBarTime;

   if(!MarketDataReady())
      return;

   double macdMain[], macdSig[], atrBuf[], ma200Buf[];
   ArrayResize(macdMain, 4);
   ArrayResize(macdSig, 4);
   ArrayResize(atrBuf, 4);
   ArrayResize(ma200Buf, 3);
   ArraySetAsSeries(macdMain, true);
   ArraySetAsSeries(macdSig, true);
   ArraySetAsSeries(atrBuf, true);
   ArraySetAsSeries(ma200Buf, true);

   if(CopyBuffer(g_macdHandle, 0, 0, 4, macdMain) < 4 ||
      CopyBuffer(g_macdHandle, 1, 0, 4, macdSig)  < 4 ||
      CopyBuffer(g_atrHandle,  0, 0, 4, atrBuf)   < 4 ||
      CopyBuffer(g_ma200Handle,0, 0, 3, ma200Buf) < 3)
   {
      return;
   }

   double hist1 = macdMain[1] - macdSig[1];
   double hist2 = macdMain[2] - macdSig[2];
   double macd1 = macdMain[1];
   double macd2 = macdMain[2];
   double atr1  = atrBuf[1];
   double ma200 = ma200Buf[1];

   if(atr1 <= 0.0 || ma200 <= 0.0)
      return;

   SCandleQuality candle;
   if(!GetCandleQuality(1, atr1, candle))
      return;

   double ma200Buffer = atr1 * InpMA200BufferATR;
   bool aboveMA200 = (candle.close > ma200 + ma200Buffer);
   bool belowMA200 = (candle.close < ma200 - ma200Buffer);

   bool adxOk       = CheckADXFilter();
   bool timeOk      = CheckTimeFilter(currentBarTime);
   bool atrFilterOk = CheckATRFilter(atr1);
   bool dailyUp     = true;
   bool dailyDown   = true;
   CheckDailyFilter(dailyUp, dailyDown);

   bool spreadOk = CheckSpreadFilter();

   if(InpDebugMode)
      ShowDebugComment(candle, atr1, ma200, aboveMA200, belowMA200, adxOk, timeOk, atrFilterOk, dailyUp, dailyDown, spreadOk);

   int posCount = CountPositions();
   if(posCount >= InpMaxPositions)
   {
      ResetPending();
      return;
   }

   bool flipUp   = (hist1 > 0.0 && hist2 <= 0.0);
   bool flipDown = (hist1 < 0.0 && hist2 >= 0.0);

   // 先处理 MACD 翻转，形成 pending 状态。
   if(flipUp)
   {
      if(InpCancelPendingOnOppositeFlip && g_pendingDir == -1)
         ResetPending();

      if(InpEnableBuy && (!InpUseMA200Filter || aboveMA200))
      {
         if(g_pendingDir != 1)
            StartPending(1);
      }
   }

   if(flipDown)
   {
      if(InpCancelPendingOnOppositeFlip && g_pendingDir == 1)
         ResetPending();

      if(InpEnableSell && (!InpUseMA200Filter || belowMA200))
      {
         if(g_pendingDir != -1)
            StartPending(-1);
      }
   }

   // 再处理 pending 确认。
   if(g_pendingDir == 0)
      return;

   g_pendingBars++;
   if(g_pendingBars > InpConfirmBars)
   {
      Print("【pending超时】方向:", PendingText(), " | 已等待:", g_pendingBars, " 根K线");
      ResetPending();
      return;
   }

   bool macdUp   = (macd1 >= macd2);
   bool macdDown = (macd1 <= macd2);

   if(g_pendingDir == 1)
      TryOpenBuy(candle, atr1, macdUp, aboveMA200, adxOk, timeOk, atrFilterOk, dailyUp, spreadOk);
   else if(g_pendingDir == -1)
      TryOpenSell(candle, atr1, macdDown, belowMA200, adxOk, timeOk, atrFilterOk, dailyDown, spreadOk);
}

//+------------------------------------------------------------------+
//| 参数校验                                                          |
//+------------------------------------------------------------------+
bool ValidateInputs()
{
   if(InpFastEMA <= 0 || InpSlowEMA <= 0 || InpSignalSMA <= 0)
   {
      Print("参数错误：MACD 周期必须大于 0");
      return false;
   }
   if(InpFastEMA >= InpSlowEMA)
   {
      Print("参数错误：InpFastEMA 必须小于 InpSlowEMA");
      return false;
   }
   if(InpMA200Period < 20)
   {
      Print("参数错误：MA 周期过小，建议 >= 20");
      return false;
   }
   if(InpATRPeriod <= 0 || InpATRMultiplier <= 0.0)
   {
      Print("参数错误：ATR 周期和 ATR 止损倍数必须大于 0");
      return false;
   }
   if(InpBodyRatio < 0.0 || InpBodyRatio > 1.0)
   {
      Print("参数错误：InpBodyRatio 必须在 0~1 之间");
      return false;
   }
   if(InpMaxOppositeShadow < 0.0 || InpMaxOppositeShadow > 1.0)
   {
      Print("参数错误：InpMaxOppositeShadow 必须在 0~1 之间");
      return false;
   }
   if(InpMaxCandleATR < 0.0 || InpMA200BufferATR < 0.0)
   {
      Print("参数错误：ATR 倍数不能为负数");
      return false;
   }
   if(InpFollowThroughBars <= 0 || InpConfirmBars <= 0)
   {
      Print("参数错误：确认K线数量必须大于 0");
      return false;
   }
   if(InpRiskPercent <= 0.0 || InpRiskPercent > 10.0)
   {
      Print("参数错误：InpRiskPercent 建议在 0~10 之间，且必须大于 0");
      return false;
   }
   if(InpMaxPositions <= 0)
   {
      Print("参数错误：InpMaxPositions 必须大于 0");
      return false;
   }
   if(InpUseADX && (InpADXPeriod <= 0 || InpADXThreshold < 0.0))
   {
      Print("参数错误：ADX 周期必须大于0，阈值不能为负");
      return false;
   }
   if(InpUseATRFilter && (InpATRFilterPeriod <= 0 || InpATRFilterRatio <= 0.0))
   {
      Print("参数错误：ATR过滤周期和比例必须大于0");
      return false;
   }
   if(InpUseSpreadFilter && InpMaxSpreadPoints <= 0)
   {
      Print("参数错误：启用点差过滤时 InpMaxSpreadPoints 必须大于0");
      return false;
   }
   if(InpDeviationPoints < 0)
   {
      Print("参数错误：InpDeviationPoints 不能为负");
      return false;
   }
   if(InpUseBreakEven && (InpBreakEvenStart <= 0.0 || InpBreakEvenBuffer < 0.0))
   {
      Print("参数错误：保本启动倍数必须大于0，保本缓冲不能为负");
      return false;
   }
   if(InpUseTrailingStop && (InpTrailingStart <= 0.0 || InpTrailingStep <= 0.0))
   {
      Print("参数错误：移动止盈启动和步长必须大于0");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| 市场数据和指标准备检查                                             |
//+------------------------------------------------------------------+
bool MarketDataReady()
{
   int needBars = MathMax(InpMA200Period + 5, InpSlowEMA + InpSignalSMA + 10);
   needBars = MathMax(needBars, InpFollowThroughBars + 10);
   needBars = MathMax(needBars, InpATRPeriod + 10);

   if(Bars(_Symbol, PERIOD_CURRENT) < needBars)
      return false;

   if(BarsCalculated(g_macdHandle) < 4 ||
      BarsCalculated(g_atrHandle) < 4 ||
      BarsCalculated(g_ma200Handle) < 3)
      return false;

   if(InpUseADX && BarsCalculated(g_adxHandle) < 2)
      return false;

   if(InpUseATRFilter && BarsCalculated(g_atrHandle) < InpATRFilterPeriod + 2)
      return false;

   if(InpUseDailyFilter)
   {
      if(Bars(_Symbol, PERIOD_D1) < 205 || BarsCalculated(g_dailyMA200Handle) < 2)
         return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| 自动选择 Filling 模式                                              |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING DetectFillingMode()
{
   long filling = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);

   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;

   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;

   return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
//| pending 状态管理                                                   |
//+------------------------------------------------------------------+
void ResetPending()
{
   g_pendingDir  = 0;
   g_pendingBars = 0;
}

void StartPending(int direction)
{
   g_pendingDir  = direction;
   g_pendingBars = 0;

   if(InpDebugMode)
      Print("【pending建立】方向:", PendingText());
}

string PendingText()
{
   if(g_pendingDir == 1)
      return "BUY";
   if(g_pendingDir == -1)
      return "SELL";
   return "NONE";
}

//+------------------------------------------------------------------+
//| K线质量                                                           |
//+------------------------------------------------------------------+
bool GetCandleQuality(int shift, double atr, SCandleQuality &c)
{
   c.open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   c.close = iClose(_Symbol, PERIOD_CURRENT, shift);
   c.high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   c.low   = iLow  (_Symbol, PERIOD_CURRENT, shift);

   if(c.high <= c.low)
      return false;

   c.range = c.high - c.low;
   c.body  = MathAbs(c.close - c.open);
   c.bodyRatio  = c.body / c.range;
   c.upperRatio = (c.high - MathMax(c.open, c.close)) / c.range;
   c.lowerRatio = (MathMin(c.open, c.close) - c.low) / c.range;
   c.bullish    = (c.close > c.open);
   c.bearish    = (c.close < c.open);
   c.dangerous  = (InpMaxCandleATR > 0.0 && atr > 0.0 && c.range > atr * InpMaxCandleATR);

   return true;
}

bool IsHighestClose(int shift, int lookback)
{
   double targetClose = iClose(_Symbol, PERIOD_CURRENT, shift);
   if(targetClose <= 0.0)
      return false;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      double oldClose = iClose(_Symbol, PERIOD_CURRENT, i);
      if(oldClose <= 0.0 || oldClose >= targetClose)
         return false;
   }
   return true;
}

bool IsLowestClose(int shift, int lookback)
{
   double targetClose = iClose(_Symbol, PERIOD_CURRENT, shift);
   if(targetClose <= 0.0)
      return false;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      double oldClose = iClose(_Symbol, PERIOD_CURRENT, i);
      if(oldClose <= 0.0 || oldClose <= targetClose)
         return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| 多因子过滤                                                        |
//+------------------------------------------------------------------+
bool CheckADXFilter()
{
   if(!InpUseADX || g_adxHandle == INVALID_HANDLE)
      return true;

   double adxBuf[];
   ArrayResize(adxBuf, 2);
   ArraySetAsSeries(adxBuf, true);

   if(CopyBuffer(g_adxHandle, 0, 0, 2, adxBuf) < 2)
      return false;

   return (adxBuf[1] > InpADXThreshold);
}

bool CheckTimeFilter(datetime barTime)
{
   if(!InpUseTimeFilter)
      return true;

   MqlDateTime dt;
   TimeToStruct(barTime, dt);

   if(InpStartHour <= InpEndHour)
      return (dt.hour >= InpStartHour && dt.hour <= InpEndHour);

   return (dt.hour >= InpStartHour || dt.hour <= InpEndHour);
}

bool CheckATRFilter(double atr1)
{
   if(!InpUseATRFilter)
      return true;

   if(atr1 <= 0.0 || InpATRFilterPeriod <= 0)
      return false;

   // 使用已存在的 ATR 句柄直接计算最近 N 根已收盘 ATR 的均值，
   // 避免额外创建“ATR 的 MA”指标句柄，兼容性更高。
   double atrAvgBuf[];
   ArrayResize(atrAvgBuf, InpATRFilterPeriod);
   ArraySetAsSeries(atrAvgBuf, true);

   if(CopyBuffer(g_atrHandle, 0, 1, InpATRFilterPeriod, atrAvgBuf) < InpATRFilterPeriod)
      return false;

   double sum = 0.0;
   for(int i = 0; i < InpATRFilterPeriod; i++)
   {
      if(atrAvgBuf[i] <= 0.0)
         return false;
      sum += atrAvgBuf[i];
   }

   double atrAvg = sum / (double)InpATRFilterPeriod;
   return (atr1 > atrAvg * InpATRFilterRatio);
}

void CheckDailyFilter(bool &dailyUp, bool &dailyDown)
{
   dailyUp   = true;
   dailyDown = true;

   if(!InpUseDailyFilter || g_dailyMA200Handle == INVALID_HANDLE)
      return;

   dailyUp   = false;
   dailyDown = false;

   double dMaBuf[];
   ArrayResize(dMaBuf, 2);
   ArraySetAsSeries(dMaBuf, true);

   if(CopyBuffer(g_dailyMA200Handle, 0, 0, 2, dMaBuf) < 2)
      return;

   double dClose = iClose(_Symbol, PERIOD_D1, 1);
   if(dClose <= 0.0 || dMaBuf[1] <= 0.0)
      return;

   dailyUp   = (dClose > dMaBuf[1]);
   dailyDown = (dClose < dMaBuf[1]);
}

bool CheckSpreadFilter()
{
   if(!InpUseSpreadFilter)
      return true;

   double spread = CurrentSpreadPoints();
   if(spread < 0.0)
      return false;

   return (spread <= (double)InpMaxSpreadPoints);
}

double CurrentSpreadPoints()
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return -1.0;

   if(tick.ask <= 0.0 || tick.bid <= 0.0 || tick.ask < tick.bid)
      return -1.0;

   return (tick.ask - tick.bid) / _Point;
}

//+------------------------------------------------------------------+
//| 入场处理                                                          |
//+------------------------------------------------------------------+
void TryOpenBuy(SCandleQuality &c, double atr, bool macdUp, bool aboveMA200,
                bool adxOk, bool timeOk, bool atrFilterOk, bool dailyUp, bool spreadOk)
{
   // 与 v8.5 保持一致：方向K线 + 实体合格之后才检查危险K线和影线。
   if(!c.bullish || c.bodyRatio < InpBodyRatio)
      return;

   if((InpRequireMACDDir && !macdUp) ||
      (InpUseMA200Filter && !aboveMA200) ||
      !adxOk || !timeOk || !atrFilterOk || !dailyUp || !spreadOk)
      return;

   if(c.dangerous)
   {
      Print("【危险K线-多】振幅>", InpMaxCandleATR, "×ATR，疑似耗竭，放弃");
      ResetPending();
      return;
   }

   if(c.upperRatio > InpMaxOppositeShadow)
   {
      Print("【上影过长-多】上影>", DoubleToString(InpMaxOppositeShadow * 100.0, 0), "% ，存在卖压，放弃");
      ResetPending();
      return;
   }

   if(InpRequireFollowThrough && !IsHighestClose(1, InpFollowThroughBars))
   {
      Print("【跟随确认失败-多】未创近", InpFollowThroughBars, "根K线新高，继续等待");
      return;
   }

   double price = 0.0;
   double sl    = 0.0;
   double lot   = 0.0;
   string reason = "";

   if(!PrepareTradePlan(ORDER_TYPE_BUY, atr, price, sl, lot, reason))
   {
      Print("【开多准备失败】", reason);
      return;
   }

   Print("【开多】实体:", DoubleToString(c.bodyRatio * 100.0, 1), "%",
         " | 上影:", DoubleToString(c.upperRatio * 100.0, 1), "%",
         " | EP:", DoubleToString(price, _Digits),
         " | SL:", DoubleToString(sl, _Digits),
         " | Lot:", DoubleToString(lot, VolumeDigits()));

   if(OpenPosition(ORDER_TYPE_BUY, price, sl, lot))
      ResetPending();
}

void TryOpenSell(SCandleQuality &c, double atr, bool macdDown, bool belowMA200,
                 bool adxOk, bool timeOk, bool atrFilterOk, bool dailyDown, bool spreadOk)
{
   if(!c.bearish || c.bodyRatio < InpBodyRatio)
      return;

   if((InpRequireMACDDir && !macdDown) ||
      (InpUseMA200Filter && !belowMA200) ||
      !adxOk || !timeOk || !atrFilterOk || !dailyDown || !spreadOk)
      return;

   if(c.dangerous)
   {
      Print("【危险K线-空】振幅>", InpMaxCandleATR, "×ATR，疑似耗竭，放弃");
      ResetPending();
      return;
   }

   if(c.lowerRatio > InpMaxOppositeShadow)
   {
      Print("【下影过长-空】下影>", DoubleToString(InpMaxOppositeShadow * 100.0, 0), "% ，存在买盘，放弃");
      ResetPending();
      return;
   }

   if(InpRequireFollowThrough && !IsLowestClose(1, InpFollowThroughBars))
   {
      Print("【跟随确认失败-空】未创近", InpFollowThroughBars, "根K线新低，继续等待");
      return;
   }

   double price = 0.0;
   double sl    = 0.0;
   double lot   = 0.0;
   string reason = "";

   if(!PrepareTradePlan(ORDER_TYPE_SELL, atr, price, sl, lot, reason))
   {
      Print("【开空准备失败】", reason);
      return;
   }

   Print("【开空】实体:", DoubleToString(c.bodyRatio * 100.0, 1), "%",
         " | 下影:", DoubleToString(c.lowerRatio * 100.0, 1), "%",
         " | EP:", DoubleToString(price, _Digits),
         " | SL:", DoubleToString(sl, _Digits),
         " | Lot:", DoubleToString(lot, VolumeDigits()));

   if(OpenPosition(ORDER_TYPE_SELL, price, sl, lot))
      ResetPending();
}

//+------------------------------------------------------------------+
//| 交易计划：价格、止损、手数、保证金                                 |
//+------------------------------------------------------------------+
bool PrepareTradePlan(ENUM_ORDER_TYPE type, double atr, double &price, double &sl, double &lot, string &reason)
{
   reason = "";

   if(!CanTradeNow(reason))
      return false;

   if(atr <= 0.0)
   {
      reason = "ATR 无效";
      return false;
   }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || tick.ask <= 0.0 || tick.bid <= 0.0)
   {
      reason = "无法获取有效报价";
      return false;
   }

   price = (type == ORDER_TYPE_BUY ? tick.ask : tick.bid);

   double slDist = atr * InpATRMultiplier;
   double minStopDist = MinOpenStopDistance();

   if(type == ORDER_TYPE_BUY)
   {
      sl = price - slDist;
      // Buy 的 SL 与当前 Bid 的距离必须满足 StopsLevel。
      if(minStopDist > 0.0 && (tick.bid - sl) < minStopDist)
         sl = tick.bid - minStopDist;
   }
   else if(type == ORDER_TYPE_SELL)
   {
      sl = price + slDist;
      // Sell 的 SL 与当前 Ask 的距离必须满足 StopsLevel。
      if(minStopDist > 0.0 && (sl - tick.ask) < minStopDist)
         sl = tick.ask + minStopDist;
   }
   else
   {
      reason = "订单类型不是 BUY/SELL";
      return false;
   }

   sl = NormalizePrice(sl);
   slDist = MathAbs(price - sl);

   if(slDist <= 0.0)
   {
      reason = "止损距离无效";
      return false;
   }

   lot = CalculateLotSize(slDist);
   if(lot <= 0.0)
   {
      reason = "按当前风险计算出的手数无效或低于最小手数";
      return false;
   }

   if(!HasEnoughMargin(type, lot, price, reason))
      return false;

   return true;
}

double MinOpenStopDistance()
{
   long stopsLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   if(stopsLevel <= 0)
      return 0.0;

   return ((double)stopsLevel + 2.0) * _Point;
}

double MinModifyStopDistance()
{
   long stopsLevel  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   long freezeLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   long level = (stopsLevel > freezeLevel ? stopsLevel : freezeLevel);

   if(level <= 0)
      return 0.0;

   return ((double)level + 2.0) * _Point;
}

double NormalizePrice(double price)
{
   return NormalizeDouble(price, _Digits);
}

//+------------------------------------------------------------------+
//| 手数计算                                                          |
//+------------------------------------------------------------------+
double CalculateLotSize(double slDist)
{
   if(slDist <= 0.0)
      return 0.0;

   double riskBase = InpUseEquityRisk ? AccountInfoDouble(ACCOUNT_EQUITY) : AccountInfoDouble(ACCOUNT_BALANCE);
   if(riskBase <= 0.0)
      return 0.0;

   double riskMoney = riskBase * InpRiskPercent / 100.0;

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickValue <= 0.0)
      tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);

   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickValue <= 0.0 || tickSize <= 0.0)
      return 0.0;

   double lossPerLot = (slDist / tickSize) * tickValue;
   if(lossPerLot <= 0.0)
      return 0.0;

   double rawLot = riskMoney / lossPerLot;
   double lot = NormalizeVolume(rawLot);

   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(lot < minLot)
   {
      if(InpAllowMinLotWhenRiskTooSmall)
         lot = minLot;
      else
         return 0.0;
   }

   if(lot > maxLot)
      lot = maxLot;

   return NormalizeVolume(lot);
}

double NormalizeVolume(double volume)
{
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(step <= 0.0)
      return 0.0;

   double normalized = MathFloor(volume / step + 1e-8) * step;
   normalized = NormalizeDouble(normalized, VolumeDigits());

   if(normalized < 0.0)
      normalized = 0.0;
   if(normalized > maxLot)
      normalized = maxLot;

   // 不在这里强制拉到 minLot，避免小资金账户被动超额风险。
   if(normalized < minLot)
      return normalized;

   return normalized;
}

int VolumeDigits()
{
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0.0)
      return 2;

   int digits = 0;
   double value = step;

   while(MathAbs(value - MathRound(value)) > 1e-8 && digits < 8)
   {
      value *= 10.0;
      digits++;
   }

   return digits;
}

bool HasEnoughMargin(ENUM_ORDER_TYPE type, double lot, double price, string &reason)
{
   double margin = 0.0;
   if(!OrderCalcMargin(type, _Symbol, lot, price, margin))
   {
      reason = "保证金计算失败，错误:" + IntegerToString(GetLastError());
      return false;
   }

   double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(margin > freeMargin)
   {
      reason = "可用保证金不足，需要:" + DoubleToString(margin, 2) + " 可用:" + DoubleToString(freeMargin, 2);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| 交易执行                                                          |
//+------------------------------------------------------------------+
bool OpenPosition(ENUM_ORDER_TYPE type, double price, double sl, double lot)
{
   string reason = "";
   if(!CanTradeNow(reason))
   {
      Print("开仓失败 | ", reason);
      return false;
   }

   MqlTradeRequest req;
   MqlTradeResult  res;
   ZeroMemory(req);
   ZeroMemory(res);

   req.action       = TRADE_ACTION_DEAL;
   req.symbol       = _Symbol;
   req.volume       = lot;
   req.type         = type;
   req.price        = NormalizePrice(price);
   req.sl           = NormalizePrice(sl);
   req.tp           = 0.0;
   req.deviation    = (ulong)InpDeviationPoints;
   req.magic        = InpMagicNumber;
   req.comment      = InpComment;
   req.type_time    = ORDER_TIME_GTC;
   req.type_filling = g_fillingMode;

   ResetLastError();
   bool sent = OrderSend(req, res);
   if(!sent)
   {
      Print("开仓失败 | OrderSend=false | 错误:", GetLastError(),
            " | 类型:", EnumToString(type),
            " | 手数:", DoubleToString(lot, VolumeDigits()),
            " | 价格:", DoubleToString(req.price, _Digits),
            " | SL:", DoubleToString(req.sl, _Digits));
      return false;
   }

   if(res.retcode != TRADE_RETCODE_DONE &&
      res.retcode != TRADE_RETCODE_DONE_PARTIAL &&
      res.retcode != TRADE_RETCODE_PLACED)
   {
      Print("开仓被服务器拒绝 | retcode:", res.retcode,
            " | comment:", res.comment,
            " | deal:", res.deal,
            " | order:", res.order);
      return false;
   }

   Print("开仓成功 | retcode:", res.retcode,
         " | deal:", res.deal,
         " | order:", res.order,
         " | 成交价:", DoubleToString(res.price, _Digits));

   return true;
}

bool CanTradeNow(string &reason)
{
   reason = "";

   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      reason = "终端未允许自动交易";
      return false;
   }
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
   {
      reason = "EA 未被允许交易";
      return false;
   }
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
   {
      reason = "账户未允许交易";
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| 保本与移动止盈                                                    |
//+------------------------------------------------------------------+
void ManageProtectionStops(double atr)
{
   if(atr <= 0.0)
      return;

   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   if(prevClose <= 0.0)
      return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curSL     = PositionGetDouble(POSITION_SL);
      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      bool hasCandidate = false;
      double candidateSL = curSL;

      if(posType == POSITION_TYPE_BUY)
      {
         if(InpUseBreakEven && prevClose > openPrice + atr * InpBreakEvenStart)
         {
            double beSL = NormalizePrice(openPrice + atr * InpBreakEvenBuffer);
            if(curSL == 0.0 || beSL > candidateSL)
            {
               candidateSL = beSL;
               hasCandidate = true;
            }
         }

         if(InpUseTrailingStop && prevClose > openPrice + atr * InpTrailingStart)
         {
            double trailSL = NormalizePrice(prevClose - atr * InpTrailingStep);
            if(curSL == 0.0 || trailSL > candidateSL)
            {
               candidateSL = trailSL;
               hasCandidate = true;
            }
         }

         if(hasCandidate && (curSL == 0.0 || candidateSL > curSL + _Point))
            ModifyStopLoss(ticket, candidateSL);
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         if(InpUseBreakEven && prevClose < openPrice - atr * InpBreakEvenStart)
         {
            double beSL = NormalizePrice(openPrice - atr * InpBreakEvenBuffer);
            if(curSL == 0.0 || beSL < candidateSL)
            {
               candidateSL = beSL;
               hasCandidate = true;
            }
         }

         if(InpUseTrailingStop && prevClose < openPrice - atr * InpTrailingStart)
         {
            double trailSL = NormalizePrice(prevClose + atr * InpTrailingStep);
            if(curSL == 0.0 || trailSL < candidateSL)
            {
               candidateSL = trailSL;
               hasCandidate = true;
            }
         }

         if(hasCandidate && (curSL == 0.0 || candidateSL < curSL - _Point))
            ModifyStopLoss(ticket, candidateSL);
      }
   }
}

bool ModifyStopLoss(ulong ticket, double newSL)
{
   string reason = "";
   if(!CanTradeNow(reason))
   {
      Print("修改止损失败 | ", reason);
      return false;
   }

   if(!PositionSelectByTicket(ticket))
      return false;

   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

   if(!StopLossCanBeModified(posType, newSL, reason))
   {
      if(InpDebugMode)
         Print("修改止损跳过 | 票号:", ticket, " | ", reason, " | 新SL:", DoubleToString(newSL, _Digits));
      return false;
   }

   MqlTradeRequest req;
   MqlTradeResult  res;
   ZeroMemory(req);
   ZeroMemory(res);

   req.action   = TRADE_ACTION_SLTP;
   req.position = ticket;
   req.symbol   = _Symbol;
   req.sl       = NormalizePrice(newSL);
   req.tp       = PositionGetDouble(POSITION_TP);
   req.magic    = InpMagicNumber;

   ResetLastError();
   bool sent = OrderSend(req, res);
   if(!sent)
   {
      Print("修改止损失败 | 票号:", ticket,
            " | 错误:", GetLastError(),
            " | 新SL:", DoubleToString(req.sl, _Digits));
      return false;
   }

   if(res.retcode != TRADE_RETCODE_DONE && res.retcode != TRADE_RETCODE_PLACED)
   {
      Print("修改止损被服务器拒绝 | 票号:", ticket,
            " | retcode:", res.retcode,
            " | comment:", res.comment,
            " | 新SL:", DoubleToString(req.sl, _Digits));
      return false;
   }

   Print("修改止损成功 | 票号:", ticket, " | 新SL:", DoubleToString(req.sl, _Digits));
   return true;
}

bool StopLossCanBeModified(ENUM_POSITION_TYPE posType, double newSL, string &reason)
{
   reason = "";

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || tick.ask <= 0.0 || tick.bid <= 0.0)
   {
      reason = "报价无效";
      return false;
   }

   double minDist = MinModifyStopDistance();

   if(posType == POSITION_TYPE_BUY)
   {
      if(newSL >= tick.bid)
      {
         reason = "Buy SL 不能高于或等于当前 Bid";
         return false;
      }
      if(minDist > 0.0 && (tick.bid - newSL) < minDist)
      {
         reason = "Buy SL 距离当前 Bid 过近";
         return false;
      }
   }
   else if(posType == POSITION_TYPE_SELL)
   {
      if(newSL <= tick.ask)
      {
         reason = "Sell SL 不能低于或等于当前 Ask";
         return false;
      }
      if(minDist > 0.0 && (newSL - tick.ask) < minDist)
      {
         reason = "Sell SL 距离当前 Ask 过近";
         return false;
      }
   }
   else
   {
      reason = "未知持仓类型";
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| 持仓统计                                                          |
//+------------------------------------------------------------------+
int CountPositions()
{
   int count = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;

      count++;
   }

   return count;
}

//+------------------------------------------------------------------+
//| 调试显示                                                          |
//+------------------------------------------------------------------+
void ShowDebugComment(SCandleQuality &c, double atr, double ma200,
                      bool aboveMA200, bool belowMA200,
                      bool adxOk, bool timeOk, bool atrFilterOk,
                      bool dailyUp, bool dailyDown, bool spreadOk)
{
   string trendStr = "震荡区";
   if(aboveMA200)
      trendStr = "多头趋势";
   if(belowMA200)
      trendStr = "空头趋势";

   string dailyStr = "OFF";
   if(InpUseDailyFilter)
   {
      if(dailyUp)
         dailyStr = "UP";
      else if(dailyDown)
         dailyStr = "DOWN";
      else
         dailyStr = "FAIL";
   }

   Comment("SniperEA v8.6 Optimized | ", _Symbol, " ", EnumToString((ENUM_TIMEFRAMES)_Period), "\n",
           "趋势:", trendStr,
           " | MA200:", DoubleToString(ma200, _Digits),
           " | Close:", DoubleToString(c.close, _Digits), "\n",
           "ATR:", DoubleToString(atr, _Digits),
           " | 实体:", DoubleToString(c.bodyRatio * 100.0, 1), "%",
           " | 危险K:", c.dangerous ? "YES" : "NO", "\n",
           "上影:", DoubleToString(c.upperRatio * 100.0, 1), "%",
           " | 下影:", DoubleToString(c.lowerRatio * 100.0, 1), "%\n",
           "ADX:", adxOk ? "OK" : "FAIL",
           " | Time:", timeOk ? "OK" : "FAIL",
           " | ATR Filter:", atrFilterOk ? "OK" : "FAIL",
           " | Daily:", dailyStr,
           " | Spread:", spreadOk ? "OK" : "FAIL", "\n",
           "Pending:", PendingText(), "(", g_pendingBars, "/", InpConfirmBars, ")",
           " | 持仓:", CountPositions(), "/", InpMaxPositions);
}

//+------------------------------------------------------------------+
