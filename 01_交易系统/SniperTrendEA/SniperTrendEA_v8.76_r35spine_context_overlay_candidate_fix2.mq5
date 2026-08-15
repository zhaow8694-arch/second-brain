//+------------------------------------------------------------------+
//|                                          SniperTrendEA_v8.6.mq5 |
//|                    基于威科夫趋势线突破 + Evil MACD 狙击式交易系统 |
//|                    v8.6 - 动能确认与点火失败管理版                |
//|                                                                  |
//|  v8.6 在 v8.5 基础上新增：                                        |
//|                                                                  |
//|  【1】双向博弈过滤 (WickConflict)：                               |
//|       总影线 > 实体时拒绝入场，过滤十字星/针形等低质量突破。       |
//|       —— 对应《Not All Breakouts Are Equal》《Trade Like a Pro》  |
//|                                                                  |
//|  【2】动能优势确认 (MomentumDominance)：                          |
//|       突破K线实体须强于近N根反向K线最大实体，确认动能转换。       |
//|       —— 对应《市场结构观察》《High-Probability Structure Shift》 |
//|                                                                  |
//|  【3】点火失败快速平仓 (IgnitionExit)：                           |
//|       入场后若出现反向吞没/无跟随，在小亏损范围内快速离场。       |
//|       —— 对应《点火与跟随 (Ignition and Follow-Through)》       |
//|                                                                  |
//|  完整保留 v8.5 五层过滤 + v8.4 多因子框架。                       |
//|                                                                  |
//|  v8.61 新增过滤强度预设：保守(v8.5) / 均衡(默认) / 积极           |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.76 fix2 - r35 Spine + Normalized Context Overlay"
#property version   "8.76"
#property strict

//--- 过滤强度预设（解决 v8.5 开仓过少问题）
enum ENUM_FILTER_PRESET
{
   FILTER_CONSERVATIVE = 0,  // 保守：v8.5 原版参数，下单少、质量高
   FILTER_BALANCED     = 1,  // 均衡：推荐默认，适度增加下单频率
   FILTER_AGGRESSIVE   = 2,  // 积极：明显放宽，下单更多
   FILTER_CUSTOM       = 3   // 自定义：使用下方手动参数
};

//--- 输入参数


enum ENUM_V876_OVERLAY_MODE
{
   V876_OVERLAY_OFF        = 0,
   V876_OVERLAY_OBSERVE    = 1,
   V876_OVERLAY_SCALE      = 2,
   V876_OVERLAY_VETO_AWARE = 3
};

enum ENUM_V876_CONTEXT_CLASS
{
   V876_CONTEXT_UNKNOWN = 0,
   V876_CONTEXT_PROFIT_SPINE = 1,
   V876_CONTEXT_LOSS_COMPRESSION = 2,
   V876_CONTEXT_WEAK_CLUSTER = 3,
   V876_CONTEXT_MIXED = 4
};

enum ENUM_V876_COST_STATE
{
   V876_COST_NORMAL = 0,
   V876_COST_WATCH = 1,
   V876_COST_WEAK = 2,
   V876_COST_HARD_BLOCK = 3
};

input group "=== 过滤强度预设（v8.61）==="
input ENUM_FILTER_PRESET InpFilterPreset = FILTER_AGGRESSIVE; // 过滤强度（对齐 grok8.6 锚点默认=2）

input group "=== MACD 参数 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 趋势过滤（v8.5: Buffer 改用 ATR 倍数）==="
input int    InpMA200Period    = 200;
input bool   InpUseMA200Filter = true;
input double InpMA200BufferATR = 0.2;       // 仅 FILTER_CUSTOM 时生效

input group "=== 入场质量过滤（v8.5，仅 FILTER_CUSTOM 时生效）==="
input double InpBodyRatio          = 0.55;  // K线实体占比（均衡默认 0.55）
input double InpMaxCandleATR       = 3.0;   // 危险K线阈值（均衡默认 3.0）
input double InpMaxOppositeShadow  = 0.30;  // 反向影线上限（均衡默认 30%）
input bool   InpRequireFollowThrough = false;
input int    InpFollowThroughBars  = 3;
input int    InpConfirmBars        = 3;     // 翻转确认等待K线（均衡默认 3）
input bool   InpRequireMACDDir     = false;

input group "=== 入场质量过滤（v8.6，仅 FILTER_CUSTOM 时生效）==="
input bool   InpUseWickConflictFilter   = true;
input double InpMaxWickToBodyRatio       = 1.5;   // 均衡默认 1.5
input bool   InpRequireMomentumDominance = true;
input int    InpMomentumLookback         = 5;
input double InpMomentumMinRatio         = 0.85;  // 均衡默认 0.85

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
input bool   InpUseRiskThrottle = false;
input double InpMaxDailyDDPercent = 0.0;
input int    InpConsecutiveLossLimit = 0;
input int    InpCooldownBars = 0;
input int    InpMaxOpenPositions = 1;
input double InpRiskLotScale = 1.00;
input double InpRiskWarningDDRatio = 0.80;
input double InpMaxPeakDDPercent = 0.0;
input double InpPeakDDWarningRatio = 0.80;

input group "=== 持仓管理（v8.6 新增）==="
input bool   InpUseIgnitionExit     = true;   // 点火失败快速平仓
input int    InpIgnitionMaxBars     = 3;      // 入场后观察K线数
input double InpIgnitionEngulfRatio = 0.85;   // 反向实体/入场实体 触发阈值
input double InpIgnitionMaxLossATR  = 1.0;    // 仅在此ATR亏损范围内执行点火止损

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260618;
input string InpComment        = "SniperEA_v8.76_r35fix2";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

input group "=== v8.76 r35 Selective Context Overlay ==="
input bool   InpUseV876ContextOverlay       = false;
input ENUM_V876_OVERLAY_MODE InpV876OverlayMode = V876_OVERLAY_OFF;
input bool   InpV876DecisionLog             = false;
input string InpV876DecisionLogFile         = "v876_r35spine_context_overlay_decisions.csv";
input bool   InpV876DecisionLogCommon       = false;
input bool   InpV876ProfitSpineVeto         = true;
input bool   InpV876ExecutionCostGuard      = false;
input double InpV876ProfitSpineMinBodyRatio = 0.50;
input double InpV876ProfitSpineMaxWickBody  = 2.00;
input double InpV876LossCompressionMinBodyRatio = 0.42;
input double InpV876WeakOppositeShadowRatio = 0.45;
input double InpV876WeakContextScale        = 0.30;
input double InpV876MixedContextScale       = 0.75;
input double InpV876UnknownContextScale     = 1.00;
input double InpV876SpreadWatchPoints       = 220.0;
input double InpV876SpreadWeakPoints        = 300.0;
input double InpV876SpreadHardBlockPoints   = 500.0;
input double InpV876SpreadWatchLotScale     = 0.75;
input double InpV876SpreadWeakLotScale      = 0.25;
input bool   InpV876RequireProfitSpineInWeakSpread = true;
input bool   InpV876UseDiAdxContext          = true;
input int    InpV876ContextADXPeriod         = 14;
input double InpV876MinDirectionalDiEdge     = 12.0;
input double InpV876LowAdxMax                = 25.0;
input bool   InpV876UseHourContext           = true;
input bool   InpV876WeakHour1                = true;
input bool   InpV876WeakHour8                = true;
input bool   InpV876WeakHour12               = true;
input bool   InpV876WeakHour20               = true;



//--- 指标句柄
int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;
int g_adxHandle = INVALID_HANDLE;
int g_atrFilterHandle = INVALID_HANDLE;
int g_dailyMA200Handle = INVALID_HANDLE;
int g_v876DecisionLogHandle = INVALID_HANDLE;
int g_v876AdxHandle = INVALID_HANDLE;

struct SV876Decision
{
   bool baseSignal;
   bool forBuy;
   string baseSignalReason;
   ENUM_V876_CONTEXT_CLASS contextClass;
   ENUM_V876_COST_STATE costState;
   bool profitSpineVeto;
   bool contextAllowsTrade;
   bool executionAllowsTrade;
   double bodyRatio;
   double oppositeShadowRatio;
   double wickToBody;
   bool wickConflict;
   bool momentumDominance;
   bool dangerCandle;
   double spreadPoints;
   double directionalEdge;
   double adx;
   int entryHour;
   bool weakHour;
   double contextLotScale;
   double spreadLotScale;
   double baseLot;
   double finalLot;
   string finalAction;
   string rejectReason;
};


//--- 待入场状态
bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

//--- K线时间戳
datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

//--- 入场跟踪（点火失败检测）
datetime g_entryBarTime  = 0;
double   g_entryBodySize = 0;
datetime g_lastRiskStateBar = 0;
int      g_riskCooldownBarsLeft = 0;
int      g_consecutiveLosses = 0;
double   g_dailyEquityHigh = 0.0;
double   g_dailyDrawdownPercent = 0.0;
double   g_peakEquityHigh = 0.0;
double   g_peakDrawdownPercent = 0.0;
int      g_riskCurrentDay = 0;

//--- 生效中的过滤参数（由预设或手动参数写入）
double g_bodyRatio;
double g_maxCandleATR;
double g_maxOppositeShadow;
double g_ma200BufferATR;
int    g_confirmBars;
bool   g_requireFollowThrough;
int    g_followThroughBars;
bool   g_useWickConflict;
double g_maxWickToBody;
bool   g_requireMomentum;
int    g_momentumLookback;
double g_momentumMinRatio;
string g_presetName = "";

//+------------------------------------------------------------------+
//| 应用过滤强度预设                                                  |
//+------------------------------------------------------------------+
void ApplyFilterPreset()
{
   switch(InpFilterPreset)
   {
      case FILTER_CONSERVATIVE:
         g_bodyRatio            = 0.60;
         g_maxCandleATR         = 2.5;
         g_maxOppositeShadow    = 0.20;
         g_ma200BufferATR       = 0.0;
         g_confirmBars          = 4;
         g_requireFollowThrough = false;
         g_followThroughBars    = 3;
         g_useWickConflict      = true;
         g_maxWickToBody        = 1.0;
         g_requireMomentum      = true;
         g_momentumLookback     = 5;
         g_momentumMinRatio     = 1.0;
         g_presetName           = "保守(v8.5)";
         break;

      case FILTER_BALANCED:
         g_bodyRatio            = 0.55;
         g_maxCandleATR         = 3.0;
         g_maxOppositeShadow    = 0.30;
         g_ma200BufferATR       = 0.2;
         g_confirmBars          = 3;
         g_requireFollowThrough = false;
         g_followThroughBars    = 3;
         g_useWickConflict      = true;
         g_maxWickToBody        = 1.5;
         g_requireMomentum      = true;
         g_momentumLookback     = 5;
         g_momentumMinRatio     = 0.85;
         g_presetName           = "均衡(推荐)";
         break;

      case FILTER_AGGRESSIVE:
         g_bodyRatio            = 0.50;
         g_maxCandleATR         = 3.5;
         g_maxOppositeShadow    = 0.35;
         g_ma200BufferATR       = 0.3;
         g_confirmBars          = 3;
         g_requireFollowThrough = false;
         g_followThroughBars    = 2;
         g_useWickConflict      = false;
         g_maxWickToBody        = 2.0;
         g_requireMomentum      = false;
         g_momentumLookback     = 5;
         g_momentumMinRatio     = 0.75;
         g_presetName           = "积极";
         break;

      default:
         g_bodyRatio            = InpBodyRatio;
         g_maxCandleATR         = InpMaxCandleATR;
         g_maxOppositeShadow    = InpMaxOppositeShadow;
         g_ma200BufferATR       = InpMA200BufferATR;
         g_confirmBars          = InpConfirmBars;
         g_requireFollowThrough = InpRequireFollowThrough;
         g_followThroughBars    = InpFollowThroughBars;
         g_useWickConflict      = InpUseWickConflictFilter;
         g_maxWickToBody        = InpMaxWickToBodyRatio;
         g_requireMomentum      = InpRequireMomentumDominance;
         g_momentumLookback     = InpMomentumLookback;
         g_momentumMinRatio     = InpMomentumMinRatio;
         g_presetName           = "自定义";
         break;
   }
}

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
   g_entryBarTime     = 0;
   g_entryBodySize    = 0;
   g_lastRiskStateBar = 0;
   g_riskCooldownBarsLeft = 0;
   g_consecutiveLosses = 0;
   g_dailyEquityHigh = 0.0;
   g_dailyDrawdownPercent = 0.0;
   g_peakEquityHigh = 0.0;
   g_peakDrawdownPercent = 0.0;
   g_riskCurrentDay = 0;

   ApplyFilterPreset();
   UpdateRiskState(iTime(_Symbol, PERIOD_CURRENT, 0), AccountInfoDouble(ACCOUNT_EQUITY));

   Print("SniperTrendEA v8.76_r35spine1 初始化成功 | ", _Symbol, " ", EnumToString(Period()),
         " | 预设:", g_presetName,
         " | 实体≥", DoubleToString(g_bodyRatio * 100, 0), "%",
         " | 反向影≤", DoubleToString(g_maxOppositeShadow * 100, 0), "%",
         " | 危险K≤", g_maxCandleATR, "×ATR",
         " | 博弈:", g_useWickConflict ? "ON" : "OFF",
         " | 动能:", g_requireMomentum ? "ON" : "OFF",
         " | 点火止损:", InpUseIgnitionExit ? "ON" : "OFF");
   if((InpUseV876ContextOverlay || InpV876DecisionLog) && InpV876UseDiAdxContext)
   {
      g_v876AdxHandle = iADX(_Symbol, PERIOD_CURRENT, InpV876ContextADXPeriod);
      if(g_v876AdxHandle == INVALID_HANDLE)
         return INIT_FAILED;
   }

   if(InpV876DecisionLog && !OpenV876DecisionLogFile())
      return INIT_FAILED;

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 释放                                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   CloseV876DecisionLogFile();
   if(g_v876AdxHandle != INVALID_HANDLE) IndicatorRelease(g_v876AdxHandle);
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
   UpdateRiskState(currentBarTime, AccountInfoDouble(ACCOUNT_EQUITY));

   int posCount = CountPositions();

   // 持仓管理（每根K线一次）
   if(currentBarTime != g_lastTrailBarTime && posCount > 0)
   {
      g_lastTrailBarTime = currentBarTime;
      double atrBuf[]; ArrayResize(atrBuf, 2); ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2 && atrBuf[0] > 0)
      {
         SyncEntryTracking();
         ManageIgnitionExit(atrBuf[0]);
         if(CountPositions() > 0)
            ManageTrailingStop(atrBuf[0]);
      }
   }

   if(posCount == 0)
   {
      g_entryBarTime  = 0;
      g_entryBodySize = 0;
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

   double ma200Buffer = atr1 * g_ma200BufferATR;
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
      Comment("SniperEA v8.76_r35fix1 | 预设:", g_presetName, " | ", _Symbol, " ", EnumToString(Period()), "\n",
              "趋势:", trendStr, " | MA200:", DoubleToString(ma200, _Digits),
              " | 收盘:", DoubleToString(prevClose, _Digits), "\n",
              "ATR:", DoubleToString(atr1, _Digits),
              " | 实体:", DoubleToString(bodyRatio * 100, 1), "%",
              " (需≥", DoubleToString(g_bodyRatio * 100, 0), "%)",
              " | 影/体:", DoubleToString(GetWickToBodyRatio(1), 2), "\n",
              "动能:", g_requireMomentum ?
                     (HasMomentumDominance(true, 1) ? "多OK" : "多弱") : "OFF",
              " | 博弈:", IsWickConflictCandle(1) ? "冲突" : "干净", "\n",
              "ADX:", adxOk ? "OK" : "FAIL",
              " | 持仓:", CountPositions(), "/", InpMaxPositions,
              " | 点火监控:", (g_entryBarTime > 0 && InpUseIgnitionExit) ? "ON" : "OFF");
   }

   posCount = CountPositions();
   int riskPositionLimit = MathMax(1, MathMin(InpMaxPositions, InpMaxOpenPositions));
   if(posCount < riskPositionLimit && !IsRiskInCooldown())
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
         if(g_pendingBars > g_confirmBars)
         { g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0; }
         else
         {
            bool macdUp   = (macd1 >= macd2);
            bool macdDown = (macd1 <= macd2);
            bool dangerCandle = IsDangerousCandle(1, atr1);
            bool wickConflict = IsWickConflictCandle(1);

            if(g_pendingBuy && IsBullishCandle(1) && bodyRatio >= g_bodyRatio &&
               (!InpRequireMACDDir || macdUp) && (!InpUseMA200Filter || aboveMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyUp))
            {
               if(dangerCandle)
               {
                  Print("【危险K线-多】振幅>", g_maxCandleATR, "×ATR，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(wickConflict)
               {
                  Print("【双向博弈-多】总影线/实体=", DoubleToString(GetWickToBodyRatio(1), 2),
                        " > ", g_maxWickToBody, "，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(GetUpperShadowRatio(1) > g_maxOppositeShadow)
               {
                  Print("【上影过长-多】放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(g_requireMomentum && !HasMomentumDominance(true, 1))
               {
                  Print("【动能不足-多】实体未强于近", g_momentumLookback, "根阴线，放弃");
                  g_pendingBuy = false; g_pendingBars = 0;
               }
               else if(g_requireFollowThrough && !IsHighestClose(1, g_followThroughBars))
               {
                  Print("【跟随确认失败-多】未创新高，等待");
               }
               else
               {
                  double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                  double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
                  double lot = AdjustLotSize(CalculateLotSize(ep - sl));
                  if(InpUseV876ContextOverlay || InpV876DecisionLog)
                  {
                     SV876Decision v876Decision;
                     BuildV876Decision(v876Decision,
                                       true,
                                       "r35_buy_signal",
                                       bodyRatio,
                                       GetUpperShadowRatio(1),
                                       dangerCandle,
                                       lot);
                     if(!ApplyV876OverlayDecision(v876Decision, lot))
                     {
                        if(InpDebugMode)
                           Print("V876 BUY blocked: ", v876Decision.rejectReason);
                        g_pendingBuy = false;
                        g_pendingBars = 0;
                        return;
                     }
                  }
                  Print("【开多】实体:", DoubleToString(bodyRatio * 100, 1), "%",
                        " | 影/体:", DoubleToString(GetWickToBodyRatio(1), 2),
                        " | EP:", ep, " SL:", sl, " Lot:", lot);
                  if(lot > 0 && OpenPosition(ORDER_TYPE_BUY, ep, sl, lot))
                  {
                     g_pendingBuy = false; g_pendingBars = 0;
                  }
               }
            }

            if(g_pendingSell && IsBearishCandle(1) && bodyRatio >= g_bodyRatio &&
               (!InpRequireMACDDir || macdDown) && (!InpUseMA200Filter || belowMA200) &&
               adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyDown))
            {
               if(dangerCandle)
               {
                  Print("【危险K线-空】放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(wickConflict)
               {
                  Print("【双向博弈-空】总影线/实体=", DoubleToString(GetWickToBodyRatio(1), 2),
                        " > ", g_maxWickToBody, "，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(GetLowerShadowRatio(1) > g_maxOppositeShadow)
               {
                  Print("【下影过长-空】放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(g_requireMomentum && !HasMomentumDominance(false, 1))
               {
                  Print("【动能不足-空】实体未强于近", g_momentumLookback, "根阳线，放弃");
                  g_pendingSell = false; g_pendingBars = 0;
               }
               else if(g_requireFollowThrough && !IsLowestClose(1, g_followThroughBars))
               {
                  Print("【跟随确认失败-空】未创新低，等待");
               }
               else
               {
                  double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                  double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
                  double lot = AdjustLotSize(CalculateLotSize(sl - ep));
                  if(InpUseV876ContextOverlay || InpV876DecisionLog)
                  {
                     SV876Decision v876Decision;
                     BuildV876Decision(v876Decision,
                                       false,
                                       "r35_sell_signal",
                                       bodyRatio,
                                       GetLowerShadowRatio(1),
                                       dangerCandle,
                                       lot);
                     if(!ApplyV876OverlayDecision(v876Decision, lot))
                     {
                        if(InpDebugMode)
                           Print("V876 SELL blocked: ", v876Decision.rejectReason);
                        g_pendingSell = false;
                        g_pendingBars = 0;
                        return;
                     }
                  }
                  Print("【开空】实体:", DoubleToString(bodyRatio * 100, 1), "%",
                        " | 影/体:", DoubleToString(GetWickToBodyRatio(1), 2),
                        " | EP:", ep, " SL:", sl, " Lot:", lot);
                  if(lot > 0 && OpenPosition(ORDER_TYPE_SELL, ep, sl, lot))
                  {
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
//| 【v8.65】风险状态更新                                            |
//+------------------------------------------------------------------+
void UpdateRiskState(datetime barTime, double equity)
{
   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   int dayKey = dt.year * 10000 + dt.mon * 100 + dt.day;

   if(g_riskCurrentDay != dayKey)
   {
      g_riskCurrentDay = dayKey;
      g_dailyEquityHigh = equity;
      g_dailyDrawdownPercent = 0.0;
   }

   if(g_dailyEquityHigh <= 0.0 || equity > g_dailyEquityHigh)
      g_dailyEquityHigh = equity;

   if(g_peakEquityHigh <= 0.0 || equity > g_peakEquityHigh)
      g_peakEquityHigh = equity;

   g_dailyDrawdownPercent = (g_dailyEquityHigh > 0.0) ? (g_dailyEquityHigh - equity) / g_dailyEquityHigh * 100.0 : 0.0;
   g_peakDrawdownPercent = (g_peakEquityHigh > 0.0) ? (g_peakEquityHigh - equity) / g_peakEquityHigh * 100.0 : 0.0;

   if(g_lastRiskStateBar != barTime)
   {
      g_lastRiskStateBar = barTime;

      if(g_riskCooldownBarsLeft > 0)
         g_riskCooldownBarsLeft--;

      if(InpUseRiskThrottle)
      {
         bool dailyStop = (InpMaxDailyDDPercent > 0.0 && g_dailyDrawdownPercent >= InpMaxDailyDDPercent);
         bool lossStop = (InpConsecutiveLossLimit > 0 && GetConsecutiveLosses() >= InpConsecutiveLossLimit);

         if((dailyStop || lossStop) && InpCooldownBars > 0)
            g_riskCooldownBarsLeft = MathMax(g_riskCooldownBarsLeft, InpCooldownBars);
      }
   }
}

//+------------------------------------------------------------------+
//| 【v8.65】风险冷却状态                                            |
//+------------------------------------------------------------------+
bool IsRiskInCooldown()
{
   return (InpUseRiskThrottle && g_riskCooldownBarsLeft > 0);
}

//+------------------------------------------------------------------+
//| 【v8.65】风险缩放手数                                            |
//+------------------------------------------------------------------+
double AdjustLotSize(double lot)
{
   if(!InpUseRiskThrottle)
      return lot;

   double scale = 1.0;

   if(InpRiskLotScale > 0.0 && InpRiskLotScale < 1.0)
   {
      bool dailyWarning = (InpMaxDailyDDPercent > 0.0 &&
                           InpRiskWarningDDRatio > 0.0 &&
                           g_dailyDrawdownPercent >= InpMaxDailyDDPercent * InpRiskWarningDDRatio);

      bool lossWarning = (InpConsecutiveLossLimit > 0 &&
                          GetConsecutiveLosses() >= MathMax(1, (int)MathFloor(InpConsecutiveLossLimit * InpRiskWarningDDRatio)));

      bool peakWarning = (InpMaxPeakDDPercent > 0.0 &&
                          InpPeakDDWarningRatio > 0.0 &&
                          g_peakDrawdownPercent >= InpMaxPeakDDPercent * InpPeakDDWarningRatio);

      if(dailyWarning || lossWarning || peakWarning)
         scale = InpRiskLotScale;
   }

   double adjustedLot = lot * scale;
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   adjustedLot = MathMax(minLot, MathMin(maxLot, adjustedLot));
   adjustedLot = MathFloor(adjustedLot / step) * step;

   return NormalizeDouble(adjustedLot, 2);
}

//+------------------------------------------------------------------+
//| 【v8.65】统计最近连续亏损                                        |
//+------------------------------------------------------------------+
int GetConsecutiveLosses()
{
   int consecutiveLosses = 0;
   datetime fromTime = 0;
   datetime toTime = TimeCurrent();

   if(!HistorySelect(fromTime, toTime))
      return g_consecutiveLosses;

   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;

      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol)
         continue;

      if((long)HistoryDealGetInteger(ticket, DEAL_MAGIC) != InpMagicNumber)
         continue;

      if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;

      double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT)
                    + HistoryDealGetDouble(ticket, DEAL_SWAP)
                    + HistoryDealGetDouble(ticket, DEAL_COMMISSION);

      if(profit < 0.0)
      {
         consecutiveLosses++;
         continue;
      }

      break;
   }

   g_consecutiveLosses = consecutiveLosses;
   return consecutiveLosses;
}

//+------------------------------------------------------------------+
//| 【v8.6】点火失败快速平仓                                          |
//+------------------------------------------------------------------+
void ManageIgnitionExit(double atr)
{
   if(!InpUseIgnitionExit || atr <= 0 || g_entryBarTime == 0) return;

   int entryShift = iBarShift(_Symbol, PERIOD_CURRENT, g_entryBarTime, true);
   if(entryShift < 0) { g_entryBarTime = 0; return; }

   int barsSinceEntry = entryShift - 1;
   if(barsSinceEntry < 1 || barsSinceEntry > InpIgnitionMaxBars) return;

   double entryBody = g_entryBodySize;
   if(entryBody <= 0) entryBody = GetCandleBody(entryShift);

   double entryOpen  = iOpen (_Symbol, PERIOD_CURRENT, entryShift);
   double entryClose = iClose(_Symbol, PERIOD_CURRENT, entryShift);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      bool ignitionFailed = false;
      string failReason = "";

      if(posType == POSITION_TYPE_BUY)
      {
         if(IsIgnitionFailedLong(entryShift, entryBody, entryOpen, entryClose, failReason))
            ignitionFailed = true;
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         if(IsIgnitionFailedShort(entryShift, entryBody, entryOpen, entryClose, failReason))
            ignitionFailed = true;
      }

      if(!ignitionFailed) continue;

      double curPrice = (posType == POSITION_TYPE_BUY) ?
                        SymbolInfoDouble(_Symbol, SYMBOL_BID) :
                        SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double lossDist = (posType == POSITION_TYPE_BUY) ?
                        (openPrice - curPrice) : (curPrice - openPrice);

      if(lossDist <= atr * InpIgnitionMaxLossATR)
      {
         Print("【点火失败平仓】", failReason, " | 亏损:", DoubleToString(lossDist, _Digits),
               " (≤", InpIgnitionMaxLossATR, "×ATR)");
         ClosePosition(ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| 多头点火失败：反向吞没 / 无跟随                                    |
//+------------------------------------------------------------------+
bool IsIgnitionFailedLong(int entryShift, double entryBody, double entryOpen,
                          double entryClose, string &reason)
{
   double body1 = GetCandleBody(1);
   if(body1 <= 0) return false;

   if(IsBearishCandle(1) && body1 >= entryBody * InpIgnitionEngulfRatio)
   {
      reason = "反向阴线实体≥入场实体";
      return true;
   }

   if(IsBearishCandle(1) &&
      iOpen(_Symbol, PERIOD_CURRENT, 1) >= entryClose &&
      iClose(_Symbol, PERIOD_CURRENT, 1) <= entryOpen)
   {
      reason = "看跌吞没入场K线";
      return true;
   }

   if(IsBullishCandle(1) && GetUpperShadowRatio(1) > 0.45)
   {
      reason = "上影线过长，多方动能衰竭";
      return true;
   }

   if(IsBullishCandle(1) && entryShift >= 2)
   {
      double body2 = GetCandleBody(2);
      if(body2 > 0 && body1 < body2 * 0.6 && !IsHighestClose(1, 1))
      {
         reason = "跟随乏力：阳线缩量且未创新高";
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| 空头点火失败：反向吞没 / 无跟随                                    |
//+------------------------------------------------------------------+
bool IsIgnitionFailedShort(int entryShift, double entryBody, double entryOpen,
                           double entryClose, string &reason)
{
   double body1 = GetCandleBody(1);
   if(body1 <= 0) return false;

   if(IsBullishCandle(1) && body1 >= entryBody * InpIgnitionEngulfRatio)
   {
      reason = "反向阳线实体≥入场实体";
      return true;
   }

   if(IsBullishCandle(1) &&
      iOpen(_Symbol, PERIOD_CURRENT, 1) <= entryClose &&
      iClose(_Symbol, PERIOD_CURRENT, 1) >= entryOpen)
   {
      reason = "看涨吞没入场K线";
      return true;
   }

   if(IsBearishCandle(1) && GetLowerShadowRatio(1) > 0.45)
   {
      reason = "下影线过长，空方动能衰竭";
      return true;
   }

   if(IsBearishCandle(1) && entryShift >= 2)
   {
      double body2 = GetCandleBody(2);
      if(body2 > 0 && body1 < body2 * 0.6 && !IsLowestClose(1, 1))
      {
         reason = "跟随乏力：阴线缩量且未创新低";
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| 从持仓恢复入场K线跟踪                                             |
//+------------------------------------------------------------------+

string V876OverlayModeToString()
{
   if(InpV876OverlayMode == V876_OVERLAY_OFF) return "off";
   if(InpV876OverlayMode == V876_OVERLAY_OBSERVE) return "observe";
   if(InpV876OverlayMode == V876_OVERLAY_SCALE) return "scale";
   if(InpV876OverlayMode == V876_OVERLAY_VETO_AWARE) return "veto_aware";
   return "unknown";
}

string V876ContextClassToString(ENUM_V876_CONTEXT_CLASS value)
{
   if(value == V876_CONTEXT_PROFIT_SPINE) return "profit_spine";
   if(value == V876_CONTEXT_LOSS_COMPRESSION) return "loss_compression_candidate";
   if(value == V876_CONTEXT_WEAK_CLUSTER) return "weak_cluster";
   if(value == V876_CONTEXT_MIXED) return "mixed";
   return "unknown";
}

string V876CostStateToString(ENUM_V876_COST_STATE value)
{
   if(value == V876_COST_NORMAL) return "normal";
   if(value == V876_COST_WATCH) return "watch";
   if(value == V876_COST_WEAK) return "weak";
   if(value == V876_COST_HARD_BLOCK) return "hard_block";
   return "unknown";
}

void ResetV876Decision(SV876Decision &d)
{
   d.baseSignal = false;
   d.forBuy = true;
   d.baseSignalReason = "";
   d.contextClass = V876_CONTEXT_UNKNOWN;
   d.costState = V876_COST_NORMAL;
   d.profitSpineVeto = false;
   d.contextAllowsTrade = true;
   d.executionAllowsTrade = true;
   d.bodyRatio = 0.0;
   d.oppositeShadowRatio = 0.0;
   d.wickToBody = 0.0;
   d.wickConflict = false;
   d.momentumDominance = false;
   d.dangerCandle = false;
   d.spreadPoints = 0.0;
   d.directionalEdge = 0.0;
   d.adx = 0.0;
   d.entryHour = -1;
   d.weakHour = false;
   d.contextLotScale = 1.0;
   d.spreadLotScale = 1.0;
   d.baseLot = 0.0;
   d.finalLot = 0.0;
   d.finalAction = "open_full";
   d.rejectReason = "";
}

bool OpenV876DecisionLogFile()
{
   if(!InpV876DecisionLog)
      return true;

   int flags = FILE_WRITE | FILE_CSV | FILE_ANSI;
   if(InpV876DecisionLogCommon)
      flags |= FILE_COMMON;

   g_v876DecisionLogHandle = FileOpen(InpV876DecisionLogFile, flags, ',');
   if(g_v876DecisionLogHandle == INVALID_HANDLE)
   {
      Print("V876_DECISION_LOG_OPEN_FAILED file=", InpV876DecisionLogFile, " error=", GetLastError());
      return false;
   }

   FileWrite(g_v876DecisionLogHandle,
             "timestamp", "symbol", "timeframe", "bar_time", "direction",
             "base_signal", "base_signal_reason", "body_ratio", "opposite_shadow_ratio",
             "wick_to_body", "wick_conflict", "momentum_dominance", "danger_candle",
             "spread_points", "directional_edge", "adx", "entry_hour", "weak_hour", "context_class", "profit_spine_veto", "cost_state",
             "context_lot_scale", "spread_lot_scale", "base_lot", "final_lot",
             "final_action", "reject_reason", "overlay_mode");
   FileFlush(g_v876DecisionLogHandle);
   return true;
}

void CloseV876DecisionLogFile()
{
   if(g_v876DecisionLogHandle != INVALID_HANDLE)
   {
      FileClose(g_v876DecisionLogHandle);
      g_v876DecisionLogHandle = INVALID_HANDLE;
   }
}

void WriteV876DecisionLog(SV876Decision &d)
{
   if(!InpV876DecisionLog)
      return;
   if(g_v876DecisionLogHandle == INVALID_HANDLE)
      return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   FileWrite(g_v876DecisionLogHandle,
             TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
             _Symbol,
             EnumToString((ENUM_TIMEFRAMES)_Period),
             TimeToString(barTime, TIME_DATE | TIME_SECONDS),
             d.forBuy ? "BUY" : "SELL",
             d.baseSignal ? "true" : "false",
             d.baseSignalReason,
             DoubleToString(d.bodyRatio, 3),
             DoubleToString(d.oppositeShadowRatio, 3),
             DoubleToString(d.wickToBody, 3),
             d.wickConflict ? "true" : "false",
             d.momentumDominance ? "true" : "false",
             d.dangerCandle ? "true" : "false",
             DoubleToString(d.spreadPoints, 1),
             DoubleToString(d.directionalEdge, 2),
             DoubleToString(d.adx, 2),
             d.entryHour,
             d.weakHour ? "true" : "false",
             V876ContextClassToString(d.contextClass),
             d.profitSpineVeto ? "true" : "false",
             V876CostStateToString(d.costState),
             DoubleToString(d.contextLotScale, 3),
             DoubleToString(d.spreadLotScale, 3),
             DoubleToString(d.baseLot, 2),
             DoubleToString(d.finalLot, 2),
             d.finalAction,
             d.rejectReason,
             V876OverlayModeToString());
   FileFlush(g_v876DecisionLogHandle);
}


double GetV876IndicatorValue(const int handle, const int bufferIndex, const int shift)
{
   if(handle == INVALID_HANDLE)
      return EMPTY_VALUE;
   double values[];
   ArraySetAsSeries(values, true);
   if(CopyBuffer(handle, bufferIndex, shift, 1, values) != 1)
      return EMPTY_VALUE;
   return values[0];
}

double GetV876DirectionalEdge(const bool forBuy)
{
   if(!InpV876UseDiAdxContext)
      return 999.0;
   double plusDi = GetV876IndicatorValue(g_v876AdxHandle, 1, 1);
   double minusDi = GetV876IndicatorValue(g_v876AdxHandle, 2, 1);
   if(plusDi == EMPTY_VALUE || minusDi == EMPTY_VALUE)
      return 0.0;
   return forBuy ? (plusDi - minusDi) : (minusDi - plusDi);
}

double GetV876AdxValue()
{
   if(!InpV876UseDiAdxContext)
      return 999.0;
   double adx = GetV876IndicatorValue(g_v876AdxHandle, 0, 1);
   if(adx == EMPTY_VALUE)
      return 0.0;
   return adx;
}

bool IsV876WeakHour(const int hour)
{
   if(!InpV876UseHourContext)
      return false;
   if(hour == 1 && InpV876WeakHour1) return true;
   if(hour == 8 && InpV876WeakHour8) return true;
   if(hour == 12 && InpV876WeakHour12) return true;
   if(hour == 20 && InpV876WeakHour20) return true;
   return false;
}

ENUM_V876_CONTEXT_CLASS ClassifyV876Context(SV876Decision &d)
{
   bool cleanCandle = (!d.dangerCandle && !d.wickConflict && d.oppositeShadowRatio <= InpV876WeakOppositeShadowRatio);
   bool profitBody = (d.bodyRatio >= InpV876ProfitSpineMinBodyRatio);
   bool acceptableWick = (d.wickToBody <= InpV876ProfitSpineMaxWickBody);
   bool weakDi = (InpV876UseDiAdxContext && d.directionalEdge < InpV876MinDirectionalDiEdge);
   bool lowAdx = (InpV876UseDiAdxContext && d.adx > 0.0 && d.adx < InpV876LowAdxMax);

   if(d.dangerCandle || d.wickConflict || d.oppositeShadowRatio > InpV876WeakOppositeShadowRatio)
      return V876_CONTEXT_WEAK_CLUSTER;

   if(d.weakHour && weakDi)
      return V876_CONTEXT_WEAK_CLUSTER;

   if(cleanCandle && profitBody && acceptableWick && !weakDi && !d.weakHour)
      return V876_CONTEXT_PROFIT_SPINE;

   if(weakDi || lowAdx || d.weakHour)
      return V876_CONTEXT_LOSS_COMPRESSION;

   if(d.bodyRatio >= InpV876LossCompressionMinBodyRatio)
      return V876_CONTEXT_MIXED;

   return V876_CONTEXT_UNKNOWN;
}

void BuildV876Decision(SV876Decision &d,
                       const bool forBuy,
                       const string baseReason,
                       const double bodyRatio,
                       const double oppositeShadowRatio,
                       const bool dangerCandle,
                       const double rawLot)
{
   ResetV876Decision(d);
   d.baseSignal = true;
   d.forBuy = forBuy;
   d.baseSignalReason = baseReason;
   d.bodyRatio = bodyRatio;
   d.oppositeShadowRatio = oppositeShadowRatio;
   d.dangerCandle = dangerCandle;
   d.baseLot = rawLot;
   d.finalLot = rawLot;
   d.wickToBody = GetWickToBodyRatio(1);
   d.wickConflict = IsWickConflictCandle(1);
   d.momentumDominance = HasMomentumDominance(forBuy, 1);
   d.spreadPoints = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   d.directionalEdge = GetV876DirectionalEdge(forBuy);
   d.adx = GetV876AdxValue();
   datetime signalTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   MqlDateTime dt;
   TimeToStruct(signalTime, dt);
   d.entryHour = dt.hour;
   d.weakHour = IsV876WeakHour(d.entryHour);
   d.contextClass = ClassifyV876Context(d);
   d.finalAction = "open_full";
}

ENUM_V876_COST_STATE ClassifyV876CostState(const double spreadPoints)
{
   if(spreadPoints >= InpV876SpreadHardBlockPoints)
      return V876_COST_HARD_BLOCK;
   if(spreadPoints >= InpV876SpreadWeakPoints)
      return V876_COST_WEAK;
   if(spreadPoints >= InpV876SpreadWatchPoints)
      return V876_COST_WATCH;
   return V876_COST_NORMAL;
}

double NormalizeV876Lot(const double lot)
{
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0.0)
      step = 0.01;
   double clamped = MathMax(minLot, MathMin(maxLot, lot));
   double stepped = MathFloor(clamped / step) * step;
   return NormalizeDouble(stepped, 2);
}
bool ApplyV876ContextAction(SV876Decision &d)
{
   d.contextLotScale = 1.0;
   d.profitSpineVeto = false;

   if(!InpUseV876ContextOverlay || InpV876OverlayMode == V876_OVERLAY_OFF || InpV876OverlayMode == V876_OVERLAY_OBSERVE)
      return true;

   if(d.contextClass == V876_CONTEXT_PROFIT_SPINE)
   {
      d.profitSpineVeto = InpV876ProfitSpineVeto;
      return true;
   }

   if(d.contextClass == V876_CONTEXT_WEAK_CLUSTER)
      d.contextLotScale = InpV876WeakContextScale;
   else if(d.contextClass == V876_CONTEXT_MIXED || d.contextClass == V876_CONTEXT_LOSS_COMPRESSION)
      d.contextLotScale = InpV876MixedContextScale;
   else
      d.contextLotScale = InpV876UnknownContextScale;

   d.contextLotScale = MathMax(0.0, MathMin(1.0, d.contextLotScale));
   if(InpV876OverlayMode == V876_OVERLAY_VETO_AWARE && d.contextClass == V876_CONTEXT_WEAK_CLUSTER && d.contextLotScale <= 0.0)
   {
      d.contextAllowsTrade = false;
      d.finalAction = "reject_context";
      d.rejectReason = "v876_weak_cluster_context";
      return false;
   }

   d.finalLot *= d.contextLotScale;
   if(d.contextLotScale < 1.0)
      d.finalAction = "open_scaled";
   return true;
}

bool ApplyV876ExecutionCostGuard(SV876Decision &d)
{
   d.costState = ClassifyV876CostState(d.spreadPoints);
   d.spreadLotScale = 1.0;

   if(!InpV876ExecutionCostGuard || !InpUseV876ContextOverlay || InpV876OverlayMode == V876_OVERLAY_OFF || InpV876OverlayMode == V876_OVERLAY_OBSERVE)
      return true;

   if(d.costState == V876_COST_HARD_BLOCK)
   {
      d.executionAllowsTrade = false;
      d.finalAction = "reject_execution_cost";
      d.rejectReason = "v876_spread_hard_block";
      return false;
   }

   if(d.costState == V876_COST_WEAK)
   {
      if(InpV876RequireProfitSpineInWeakSpread && d.contextClass != V876_CONTEXT_PROFIT_SPINE)
      {
         d.executionAllowsTrade = false;
         d.finalAction = "reject_execution_cost";
         d.rejectReason = "v876_weak_spread_without_profit_spine";
         return false;
      }
      d.spreadLotScale = InpV876SpreadWeakLotScale;
   }
   else if(d.costState == V876_COST_WATCH)
   {
      d.spreadLotScale = InpV876SpreadWatchLotScale;
   }

   d.spreadLotScale = MathMax(0.0, MathMin(1.0, d.spreadLotScale));
   d.finalLot = NormalizeV876Lot(d.finalLot * d.spreadLotScale);
   if(d.spreadLotScale < 1.0)
      d.finalAction = "open_scaled";
   return true;
}

bool ApplyV876OverlayDecision(SV876Decision &d, double &lots)
{
   d.finalLot = lots;

   bool contextOk = ApplyV876ContextAction(d);
   bool costOk = ApplyV876ExecutionCostGuard(d);

   if(!contextOk || !costOk)
   {
      WriteV876DecisionLog(d);
      return false;
   }

   if(InpUseV876ContextOverlay && InpV876OverlayMode != V876_OVERLAY_OFF && InpV876OverlayMode != V876_OVERLAY_OBSERVE)
   {
      lots = NormalizeV876Lot(d.finalLot);
      d.finalLot = lots;
   }
   else
      d.finalLot = lots;

   if(lots <= 0.0)
   {
      d.finalAction = "reject_context";
      d.rejectReason = "v876_final_lot_zero";
      WriteV876DecisionLog(d);
      return false;
   }

   WriteV876DecisionLog(d);
   return true;
}

void SyncEntryTracking()
{
   if(g_entryBarTime > 0) return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      datetime posTime = (datetime)PositionGetInteger(POSITION_TIME);
      int shift = iBarShift(_Symbol, PERIOD_CURRENT, posTime, true);
      if(shift < 0) shift = 1;

      g_entryBarTime  = iTime(_Symbol, PERIOD_CURRENT, shift);
      g_entryBodySize = GetCandleBody(shift);
      break;
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
//| 【v8.6】双向博弈：总影线 vs 实体                                   |
//+------------------------------------------------------------------+
bool IsWickConflictCandle(int shift)
{
   if(!g_useWickConflict) return false;
   return (GetWickToBodyRatio(shift) > g_maxWickToBody);
}

double GetWickToBodyRatio(int shift)
{
   double body = GetCandleBody(shift);
   if(body <= 0) return 999.0;
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double wicks = (high - MathMax(open, close)) + (MathMin(open, close) - low);
   return wicks / body;
}

//+------------------------------------------------------------------+
//| 【v8.6】动能优势：突破实体强于近期反向K线                          |
//+------------------------------------------------------------------+
bool HasMomentumDominance(bool forBuy, int shift)
{
   if(!g_requireMomentum) return true;

   double entryBody = GetCandleBody(shift);
   if(entryBody <= 0) return false;

   double maxOppBody = 0;
   int lookback = MathMax(1, g_momentumLookback);

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isOpposite = forBuy ? IsBearishCandle(i) : IsBullishCandle(i);
      if(!isOpposite) continue;
      double b = GetCandleBody(i);
      if(b > maxOppBody) maxOppBody = b;
   }

   if(maxOppBody <= 0) return true;
   return (entryBody >= maxOppBody * g_momentumMinRatio);
}

//+------------------------------------------------------------------+
//| K线实体（绝对值）                                                  |
//+------------------------------------------------------------------+
double GetCandleBody(int shift)
{
   return MathAbs(iClose(_Symbol, PERIOD_CURRENT, shift) -
                iOpen (_Symbol, PERIOD_CURRENT, shift));
}

//+------------------------------------------------------------------+
//| 【v8.5】危险K线判断                                                |
//+------------------------------------------------------------------+
bool IsDangerousCandle(int shift, double atr)
{
   if(g_maxCandleATR <= 0 || atr <= 0) return false;
   double range = iHigh(_Symbol, PERIOD_CURRENT, shift) - iLow(_Symbol, PERIOD_CURRENT, shift);
   return (range > atr * g_maxCandleATR);
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
   double range = iHigh(_Symbol, PERIOD_CURRENT, shift) - iLow(_Symbol, PERIOD_CURRENT, shift);
   if(range <= 0) return 0;
   return GetCandleBody(shift) / range;
}

bool IsBullishCandle(int shift)
{
   return iClose(_Symbol, PERIOD_CURRENT, shift) > iOpen(_Symbol, PERIOD_CURRENT, shift);
}

bool IsBearishCandle(int shift)
{
   return iClose(_Symbol, PERIOD_CURRENT, shift) < iOpen(_Symbol, PERIOD_CURRENT, shift);
}

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
//| 开仓（成功时记录入场K线供点火检测）                                |
//+------------------------------------------------------------------+
bool OpenPosition(ENUM_ORDER_TYPE type, double price, double sl, double lot)
{
   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL; req.symbol = _Symbol; req.volume = lot;
   req.type = type; req.price = price; req.sl = sl; req.tp = 0;
   req.deviation = 20; req.magic = InpMagicNumber; req.comment = InpComment;
   req.type_filling = ORDER_FILLING_IOC;
   if(!OrderSend(req, res))
   {
      Print("开仓失败 | 错误:", GetLastError(), " | 类型:", EnumToString(type), " | 手数:", lot);
      return false;
   }

   g_entryBarTime  = iTime(_Symbol, PERIOD_CURRENT, 1);
   g_entryBodySize = GetCandleBody(1);
   Print("开仓成功 | 票号:", res.order, " | 价格:", res.price,
         " | 入场实体:", DoubleToString(g_entryBodySize, _Digits));
   return true;
}

//+------------------------------------------------------------------+
//| 平仓                                                              |
//+------------------------------------------------------------------+
void ClosePosition(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;

   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);

   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action    = TRADE_ACTION_DEAL;
   req.position  = ticket;
   req.symbol    = _Symbol;
   req.volume    = volume;
   req.deviation = 20;
   req.magic     = InpMagicNumber;
   req.comment   = InpComment;

   if(posType == POSITION_TYPE_BUY)
   {
      req.type  = ORDER_TYPE_SELL;
      req.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   }
   else
   {
      req.type  = ORDER_TYPE_BUY;
      req.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   }

   if(!OrderSend(req, res))
      Print("平仓失败 | 票号:", ticket, " | 错误:", GetLastError());
   else
   {
      Print("平仓成功 | 票号:", ticket);
      g_entryBarTime  = 0;
      g_entryBodySize = 0;
   }
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
