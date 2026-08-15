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
#property copyright "SniperTrendEA v8.6 - Wyckoff + Evil MACD + Z-Wei Philosophy"
#property version   "8.73"
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
enum ENUM_GOVERNOR_MODE
{
   GOVERNOR_OFF      = 0,
   GOVERNOR_SOFT     = 1,
   GOVERNOR_BALANCED = 2,
   GOVERNOR_STRICT   = 3
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
input group "=== Structure Score Soft Filter (v8.67 robust case0010 default) ==="
input bool   InpUseStructureScore       = true;
input bool   InpRejectNoStructure       = false;
input int    InpSwingLookback           = 3;
input int    InpStructureScanBars       = 80;
input int    InpMinTrendlineTouches     = 3;
input double InpTrendlineTouchATR       = 0.25;
input double InpMinBreakoutDistanceATR  = 0.10;
input double InpMinBreakoutScore        = 80.0;
input double InpNoStructurePenalty      = 0.995;
input double InpMinStructureQualityFloor= 0.990;
input bool   InpShowStructureDebug      = false;
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
input bool   InpUseRiskThrottle = true;
input double InpMaxDailyDDPercent = 0.0;
input int    InpConsecutiveLossLimit = 0;
input int    InpCooldownBars = 0;
input int    InpMaxOpenPositions = 1;
input double InpRiskLotScale = 1.000;
input double InpRiskWarningDDRatio = 0.80;
input double InpMaxPeakDDPercent = 24.0;
input double InpPeakDDWarningRatio = 0.98;

input group "=== Dynamic Risk Governor (v8.69) ==="
input bool   InpUseDynamicRiskGovernor = false;
input ENUM_GOVERNOR_MODE InpGovernorMode = GOVERNOR_OFF;
input double InpGovernorRiskScale = 0.80;
input int    InpGovernorConsecutiveLossTrigger = 2;
input int    InpGovernorCooldownBars = 4;
input double InpGovernorPeakDDTriggerPercent = 20.0;
input double InpGovernorDailyDDTriggerPercent = 0.0;
input double InpGovernorMinLotScale = 0.50;
input bool   InpGovernorDebug = false;

input group "=== Weak-Month Regime Gate (v8.69) ==="
input bool   InpUseV869RegimeGate        = false;
input int    InpRegimeGateMode           = 0;
input double InpRegimeRiskScaleWatch     = 0.95;
input double InpRegimeRiskScaleRisk      = 0.80;
input double InpRegimeHardBlockThreshold = 15.0;
input bool   InpRegimeDebugLog           = false;

input group "=== Targeted Weak-Month Entry Gate (v8.69 fix4) ==="
input bool   InpUseV869TimeClusterGate   = false;
input int    InpV869BlockedEntryHour     = 20;
input bool   InpV869BlockBuyAtHour       = true;
input bool   InpV869BlockSellAtHour      = true;
input int    InpV869TimeGateMinLosses    = 0;
input bool   InpV869TimeGateDebug        = false;

input group "=== v8.69 fix5 Entry Diagnostics ==="
input bool   InpV869EntryDiagnosticLog   = false;
input string InpV869EntryDiagnosticFile  = "v869_fix5_entry_diagnostics.csv";
input bool   InpV869EntryDiagnosticCommon = true;

input group "=== v8.69 fix5b DI Edge Hour Gate ==="
input bool   InpUseV869DiEdgeHourGate    = false;
input int    InpV869DiEdgeGateHour       = 20;
input double InpV869MinDirectionalDiEdge = 12.0;
input bool   InpV869DiEdgeGateDebug      = false;
input bool   InpUseV869DiEdgeHourScale   = false;
input double InpV869DiEdgeHourLotScale   = 0.50;

input group "=== v8.69 fix5d Residual-Hour Soft Scale ==="
input bool   InpUseV869ResidualHourScale = false;
input double InpV869ResidualHourLotScale = 0.25;
input double InpV869ResidualMinDiEdge    = 12.0;
input int    InpV869ResidualConditionMode = 1; // 0=AND weak DI + trend not aligned, 1=OR
input bool   InpV869ResidualScaleHour1   = true;
input bool   InpV869ResidualScaleHour8   = true;
input bool   InpV869ResidualScaleHour12  = true;
input bool   InpV869ResidualScaleHour20  = true;
input bool   InpV869ResidualScaleDebug   = false;

input group "=== v8.69 fix7 Context DI/Trend Soft Scale ==="
input bool   InpUseV869ContextScale = false;
input double InpV869ContextLotScale = 0.25;
input int    InpV869ContextMode = 1; // 0=weak DI, 1=weak DI + low ADX, 2=low ADX, 3=weak DI + trend not aligned
input double InpV869ContextMinDiEdge = 12.0;
input double InpV869ContextMaxAdx = 25.0;
input bool   InpV869ContextDebug = false;

input group "=== Spread Cost Governor (v8.70) ==="
input int    InpSpreadGovernorMode = 0;              // 0 off, 1 audit, 2 scale, 3 scale+weak gate
input double InpSpreadNormalMaxPoints = 100.0;
input double InpSpreadWeakStartPoints = 150.0;
input double InpSpreadHardBlockPoints = 220.0;
input double InpSpreadWatchLotMultiplier = 0.75;
input double InpSpreadWeakLotMultiplier = 0.25;
input bool   InpSpreadRequireStrongContextInWeakZone = true;
input bool   InpSpreadAuditPrint = false;

input group "=== Real Strong Context Gate (v8.71) ==="
input bool   InpUseV871RealStrongContext = false;
input int    InpV871StrongContextMode = 1; // 0 audit, 1 weak-spread only, 2 scale weak context, 3 block weak context
input double InpV871MinStrongContextScore = 65.0;
input double InpV871WeakContextLotScale = 0.50;
input bool   InpV871ContextAuditPrint = false;

input group "=== Context Diagnostics (v8.72) ==="
input bool   InpUseV872ContextDiagnostics = false;
input string InpV872ContextDiagnosticFile = "v872_context_diagnostics.csv";
input bool   InpV872ContextDiagnosticCommon = true;
input bool   InpV872ContextDiagnosticPrint = false;

input group "=== Context Scaling Candidate (v8.75) ==="
input bool   InpUseV873ContextScaling = false;
input double InpV873MidScoreMin = 55.0;
input double InpV873MidScoreMax = 65.0;
input double InpV873MidScoreLotScale = 0.75;
input double InpV873HighScoreMin = 70.0;
input double InpV873HighSpreadMinPoints = 50.0;
input double InpV873HighScoreHighSpreadLotScale = 0.30;
input bool   InpV873ContextScalePrint = false;
input bool   InpUseV875MidScoreSpreadGuard = false;
input double InpV875MidScoreMin = 55.0;
input double InpV875MidScoreMax = 65.0;
input double InpV875SpreadMinPoints = 20.0;
input double InpV875SpreadMaxPoints = 40.0;
input double InpV875MidScoreSpreadLotScale = 0.0;
input bool   InpV875MidScoreSpreadHardBlock = true;
input bool   InpV875MidScoreSpreadPrint = false;

input group "=== 持仓管理（v8.6 新增）==="
input bool   InpUseIgnitionExit     = true;   // 点火失败快速平仓
input int    InpIgnitionMaxBars     = 3;      // 入场后观察K线数
input double InpIgnitionEngulfRatio = 0.85;   // 反向实体/入场实体 触发阈值
input double InpIgnitionMaxLossATR  = 1.0;    // 仅在此ATR亏损范围内执行点火止损

input group "=== 交易设置 ==="
input int    InpMagicNumber    = 20260618;
input string InpComment = "SniperEA_v8.75_context_scale";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

input group "=== Production Telemetry (v8.67) ==="
input bool   InpEnableDecisionLog   = false;
input int    InpDecisionLogLevel    = 1;
input bool   InpLogSignalReasons    = false;
input bool   InpLogRiskState        = false;
input bool   InpLogStructureScore   = false;

//--- 指标句柄
int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;
int g_adxHandle = INVALID_HANDLE;
int g_atrFilterHandle = INVALID_HANDLE;
int g_dailyMA200Handle = INVALID_HANDLE;
int g_v869AtrHandle = INVALID_HANDLE;
int g_v869AdxHandle = INVALID_HANDLE;
int g_v869Ema50Handle = INVALID_HANDLE;

const string EA_VERSION_NAME      = "SniperTrendEA_v8.75_context_scaling_candidate";
const string EA_PARAMETER_PROFILE = "robust_main_case0010";
const string EA_RECOMMENDED_SET   = "v8.66_robust_main_case0010.set";

void DecisionLog(const int level, const string message)
{
   if(!InpEnableDecisionLog) return;
   if(level > InpDecisionLogLevel) return;
   Print("[", EA_VERSION_NAME, "] ", message);
}

//--- 待入场状态
int      g_v869DiagFileHandle = INVALID_HANDLE;
int      g_v872ContextDiagFileHandle = INVALID_HANDLE;

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

bool     g_governorActive = false;
string   g_governorReason = "";
int      g_governorCooldownBarsLeft = 0;
double   g_governorLotScale = 1.0;
datetime g_lastGovernorBar = 0;

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

   
   if(InpUseV869RegimeGate || InpV869EntryDiagnosticLog || InpUseV869DiEdgeHourGate || InpUseV869DiEdgeHourScale || InpUseV869ResidualHourScale || InpUseV869ContextScale || InpUseV871RealStrongContext || InpUseV872ContextDiagnostics || InpUseV873ContextScaling)
   {
      g_v869AtrHandle = iATR(_Symbol, PERIOD_CURRENT, 14);
      if(g_v869AtrHandle == INVALID_HANDLE) return INIT_FAILED;

      g_v869AdxHandle = iADX(_Symbol, PERIOD_CURRENT, 14);
      if(g_v869AdxHandle == INVALID_HANDLE) return INIT_FAILED;

      g_v869Ema50Handle = iMA(_Symbol, PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);
      if(g_v869Ema50Handle == INVALID_HANDLE) return INIT_FAILED;
   }

   if(InpV869EntryDiagnosticLog)
   {
      int flags = FILE_WRITE | FILE_CSV | FILE_ANSI;
      if(InpV869EntryDiagnosticCommon)
         flags |= FILE_COMMON;
      g_v869DiagFileHandle = FileOpen(InpV869EntryDiagnosticFile, flags, ',');
      if(g_v869DiagFileHandle == INVALID_HANDLE)
      {
         Print("[v8.69_fix5 EntryDiagnostics] FileOpen failed | file=", InpV869EntryDiagnosticFile,
               " err=", GetLastError());
         return INIT_FAILED;
      }
      FileWrite(g_v869DiagFileHandle,
                "symbol", "period", "bar_time", "signal_time", "direction", "entry_hour", "entry_dow",
                "entry_price", "stop_loss", "lot", "atr_signal", "atr14", "atr14_avg50", "atr_ratio_14_50",
                "adx14", "plus_di", "minus_di", "ema50_slope", "ma200_slope", "trend_alignment",
                "wick_to_body", "upper_shadow", "lower_shadow", "spread_points", "consecutive_losses",
                "danger_candle", "wick_conflict", "regime_score");
      FileFlush(g_v869DiagFileHandle);
   }
   if(InpUseV872ContextDiagnostics && !OpenV872ContextDiagnosticFile())
      return INIT_FAILED;
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

   Print("SniperTrendEA v8.61 初始化成功 | ", _Symbol, " ", EnumToString(Period()),
         " | 预设:", g_presetName,
         " | 实体≥", DoubleToString(g_bodyRatio * 100, 0), "%",
         " | 反向影≤", DoubleToString(g_maxOppositeShadow * 100, 0), "%",
         " | 危险K≤", g_maxCandleATR, "×ATR",
         " | 博弈:", g_useWickConflict ? "ON" : "OFF",
         " | 动能:", g_requireMomentum ? "ON" : "OFF",
         " | 点火止损:", InpUseIgnitionExit ? "ON" : "OFF");
   DecisionLog(1, "profile=" + EA_PARAMETER_PROFILE + " | recommended_set=" + EA_RECOMMENDED_SET);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 释放                                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_v869DiagFileHandle != INVALID_HANDLE)
   {
      FileFlush(g_v869DiagFileHandle);
      FileClose(g_v869DiagFileHandle);
      g_v869DiagFileHandle = INVALID_HANDLE;
   }
   CloseV872ContextDiagnosticFile();
   if(g_macdHandle  != INVALID_HANDLE) IndicatorRelease(g_macdHandle);
   if(g_atrHandle   != INVALID_HANDLE) IndicatorRelease(g_atrHandle);
   if(g_ma200Handle != INVALID_HANDLE) IndicatorRelease(g_ma200Handle);
   if(g_adxHandle   != INVALID_HANDLE) IndicatorRelease(g_adxHandle);
   if(g_atrFilterHandle  != INVALID_HANDLE) IndicatorRelease(g_atrFilterHandle);
   if(g_dailyMA200Handle != INVALID_HANDLE) IndicatorRelease(g_dailyMA200Handle);
   if(g_v869AtrHandle != INVALID_HANDLE) IndicatorRelease(g_v869AtrHandle);
   if(g_v869AdxHandle != INVALID_HANDLE) IndicatorRelease(g_v869AdxHandle);
   if(g_v869Ema50Handle != INVALID_HANDLE) IndicatorRelease(g_v869Ema50Handle);
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
   EvaluateDynamicRiskGovernor(currentBarTime);

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
      Comment("SniperEA v8.61 | 预设:", g_presetName, " | ", _Symbol, " ", EnumToString(Period()), "\n",
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
   if(posCount < riskPositionLimit && !IsRiskInCooldown() && !IsGovernorInCooldown())
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
                  if(IsV869DiEdgeHourBlocked(true))
                  {
                     g_pendingBuy = false; g_pendingBars = 0;
                  }
                  else if(IsV869TimeClusterBlocked(true))
                  {
                     g_pendingBuy = false; g_pendingBars = 0;
                  }
                  else
                  {
                     double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                     double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
                     double structureFactor = GetStructureLotFactor(true, atr1, dangerCandle);
                     double rawLot = CalculateLotSize(ep - sl) * structureFactor * GetV869DiEdgeHourLotScale(true) * GetV869ResidualHourLotScale(true) * GetV869ContextLotScale(true);
                     double lot = (rawLot > 0.0 ? AdjustLotSize(rawLot) : 0.0);
                     bool strong_context = IsV871StrongSpreadContext(true);
                     if(!ApplySpreadCostGovernor(lot, strong_context) || !ApplyV871ContextGate(lot, true) || !ApplyV873ContextScaling(lot, true) || !ApplyV875MidScoreSpreadGuard(lot, true))
                     {
                        g_pendingBuy = false; g_pendingBars = 0;
                     }
                     else
                     {
                        Print("【开多】实体:", DoubleToString(bodyRatio * 100, 1), "%",
                              " | 影/体:", DoubleToString(GetWickToBodyRatio(1), 2),
                              " | EP:", ep, " SL:", sl, " Lot:", lot);
                        WriteV872ContextDiagnostics(true, ep, sl, lot);
                        WriteV869EntryDiagnostics(true, ep, sl, lot, atr1, dangerCandle, wickConflict);
                        if(lot > 0 && OpenPosition(ORDER_TYPE_BUY, ep, sl, lot))
                        {
                           g_pendingBuy = false; g_pendingBars = 0;
                        }
                     }
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
                  if(IsV869DiEdgeHourBlocked(false))
                  {
                     g_pendingSell = false; g_pendingBars = 0;
                  }
                  else if(IsV869TimeClusterBlocked(false))
                  {
                     g_pendingSell = false; g_pendingBars = 0;
                  }
                  else
                  {
                     double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                     double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
                     double structureFactor = GetStructureLotFactor(false, atr1, dangerCandle);
                     double rawLot = CalculateLotSize(sl - ep) * structureFactor * GetV869DiEdgeHourLotScale(false) * GetV869ResidualHourLotScale(false) * GetV869ContextLotScale(false);
                     double lot = (rawLot > 0.0 ? AdjustLotSize(rawLot) : 0.0);
                     bool strong_context = IsV871StrongSpreadContext(false);
                     if(!ApplySpreadCostGovernor(lot, strong_context) || !ApplyV871ContextGate(lot, false) || !ApplyV873ContextScaling(lot, false) || !ApplyV875MidScoreSpreadGuard(lot, false))
                     {
                        g_pendingSell = false; g_pendingBars = 0;
                     }
                     else
                     {
                        Print("【开空】实体:", DoubleToString(bodyRatio * 100, 1), "%",
                              " | 影/体:", DoubleToString(GetWickToBodyRatio(1), 2),
                              " | EP:", ep, " SL:", sl, " Lot:", lot);
                        WriteV872ContextDiagnostics(false, ep, sl, lot);
                        WriteV869EntryDiagnostics(false, ep, sl, lot, atr1, dangerCandle, wickConflict);
                        if(lot > 0 && OpenPosition(ORDER_TYPE_SELL, ep, sl, lot))
                        {
                           g_pendingSell = false; g_pendingBars = 0;
                        }
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

bool IsDynamicGovernorEnabled()
{
   return (InpUseDynamicRiskGovernor && InpGovernorMode != GOVERNOR_OFF);
}

double ClampGovernorScale(double scale)
{
   double floorScale = InpGovernorMinLotScale;
   if(floorScale <= 0.0 || floorScale > 1.0)
      floorScale = 0.50;
   if(scale <= 0.0)
      scale = floorScale;
   return MathMax(floorScale, MathMin(1.0, scale));
}

double GetModeGovernorScale()
{
   double configured = ClampGovernorScale(InpGovernorRiskScale);
   if(InpGovernorMode == GOVERNOR_SOFT)
      return MathMax(configured, 0.80);
   if(InpGovernorMode == GOVERNOR_BALANCED)
      return configured;
   if(InpGovernorMode == GOVERNOR_STRICT)
      return MathMin(configured, 0.65);
   return 1.0;
}

void AppendGovernorReason(string reason)
{
   if(g_governorReason == "")
      g_governorReason = reason;
   else
      g_governorReason = g_governorReason + ";" + reason;
}

void EvaluateDynamicRiskGovernor(datetime barTime)
{
   if(!IsDynamicGovernorEnabled())
   {
      g_governorActive = false;
      g_governorReason = "";
      g_governorLotScale = 1.0;
      g_governorCooldownBarsLeft = 0;
      g_lastGovernorBar = barTime;
      return;
   }

   bool newBar = (g_lastGovernorBar != barTime);
   if(newBar)
   {
      g_lastGovernorBar = barTime;
      if(g_governorCooldownBarsLeft > 0)
         g_governorCooldownBarsLeft--;
   }

   g_governorActive = false;
   g_governorReason = "";
   g_governorLotScale = 1.0;

   int losses = GetConsecutiveLosses();
   bool lossPressure = (InpGovernorConsecutiveLossTrigger > 0 && losses >= InpGovernorConsecutiveLossTrigger);
   bool peakPressure = (InpGovernorPeakDDTriggerPercent > 0.0 && g_peakDrawdownPercent >= InpGovernorPeakDDTriggerPercent);
   bool dailyPressure = (InpGovernorDailyDDTriggerPercent > 0.0 && g_dailyDrawdownPercent >= InpGovernorDailyDDTriggerPercent);

   if(lossPressure) AppendGovernorReason("loss_streak");
   if(peakPressure) AppendGovernorReason("peak_dd");
   if(dailyPressure) AppendGovernorReason("daily_dd");

   if(lossPressure || peakPressure || dailyPressure)
   {
      g_governorActive = true;
      g_governorLotScale = GetModeGovernorScale();
      if(newBar && InpGovernorCooldownBars > 0 &&
         (InpGovernorMode == GOVERNOR_BALANCED || InpGovernorMode == GOVERNOR_STRICT) &&
         (lossPressure || dailyPressure))
      {
         int cooldownBars = InpGovernorCooldownBars;
         if(InpGovernorMode == GOVERNOR_STRICT)
            cooldownBars = MathMax(cooldownBars, InpGovernorCooldownBars * 2);
         g_governorCooldownBarsLeft = MathMax(g_governorCooldownBarsLeft, cooldownBars);
      }
   }

   if(g_governorCooldownBarsLeft > 0)
   {
      g_governorActive = true;
      AppendGovernorReason("cooldown");
      g_governorLotScale = MathMin(g_governorLotScale, GetModeGovernorScale());
   }

   g_governorLotScale = ClampGovernorScale(g_governorLotScale);

   if(InpGovernorDebug && g_governorActive && newBar)
   {
      Print("[v8.69 Governor] reason=", g_governorReason,
            " scale=", DoubleToString(g_governorLotScale, 2),
            " cooldown=", g_governorCooldownBarsLeft,
            " losses=", losses,
            " dailyDD=", DoubleToString(g_dailyDrawdownPercent, 2),
            " peakDD=", DoubleToString(g_peakDrawdownPercent, 2));
   }
}

bool IsGovernorInCooldown()
{
   return (IsDynamicGovernorEnabled() && g_governorCooldownBarsLeft > 0);
}

double GetDynamicGovernorLotScale()
{
   if(!IsDynamicGovernorEnabled())
      return 1.0;
   if(!g_governorActive)
      return 1.0;
   return ClampGovernorScale(g_governorLotScale);
}

//+------------------------------------------------------------------+
//| 【v8.65】风险缩放手数                                            |
//+------------------------------------------------------------------+

double GetV869IndicatorValue(int handle, int bufferIndex, int shift)
{
   if(handle == INVALID_HANDLE)
      return 0.0;

   double values[];
   ArraySetAsSeries(values, true);
   int copied = CopyBuffer(handle, bufferIndex, shift, 1, values);

   if(copied <= 0)
   {
      if(InpRegimeDebugLog)
         Print("[v8.69_fix2b RegimeGate] CopyBuffer failed | handle=", handle,
               " buffer=", bufferIndex, " shift=", shift, " err=", GetLastError());
      return 0.0;
   }

   return values[0];
}

double GetV869ATRValue(int period, int shift)
{
   return GetV869IndicatorValue(g_v869AtrHandle, 0, shift);
}

double GetV869ADXValue(int period, int shift)
{
   return GetV869IndicatorValue(g_v869AdxHandle, 0, shift);
}

double GetV869EMAValue(int period, int shift)
{
   return GetV869IndicatorValue(g_v869Ema50Handle, 0, shift);
}

double GetV869RegimeScore()
{
   if(!InpUseV869RegimeGate)
      return 100.0;

   double score = 100.0;

   double atrNow = GetV869ATRValue(14, 1);
   double atrPast = GetV869ATRValue(14, 20);
   if(atrNow > 0.0 && atrPast > 0.0)
   {
      double atrRatio = atrNow / atrPast;
      if(atrRatio > 2.20)
         score -= 18.0;
      else if(atrRatio > 1.60)
         score -= 8.0;
      else if(atrRatio < 0.55)
         score -= 8.0;
   }

   double adx = GetV869ADXValue(14, 1);
   if(adx > 0.0)
   {
      if(adx < 12.0)
         score -= 18.0;
      else if(adx < 18.0)
         score -= 8.0;
   }

   double emaNow = GetV869EMAValue(50, 1);
   double emaPast = GetV869EMAValue(50, 6);
   if(atrNow > 0.0 && emaNow > 0.0 && emaPast > 0.0)
   {
      double slopeAtr = MathAbs(emaNow - emaPast) / atrNow;
      if(slopeAtr < 0.10)
         score -= 12.0;
      else if(slopeAtr < 0.20)
         score -= 6.0;
   }

   double wickToBody = GetWickToBodyRatio(1);
   if(wickToBody > 4.0)
      score -= 18.0;
   else if(wickToBody > 2.5)
      score -= 8.0;

   int recentLosses = GetConsecutiveLosses();
   if(recentLosses >= 3)
      score -= 20.0;
   else if(recentLosses >= 2)
      score -= 10.0;

   if(score < 0.0) score = 0.0;
   if(score > 100.0) score = 100.0;

   if(InpRegimeDebugLog)
      Print("[v8.69_fix1 RegimeGate] score=", DoubleToString(score, 1),
            " atr=", DoubleToString(atrNow, _Digits),
            " adx=", DoubleToString(adx, 1),
            " wickBody=", DoubleToString(wickToBody, 2),
            " losses=", recentLosses);

   return score;
}

double GetV869RegimeRiskMultiplier()
{
   if(!InpUseV869RegimeGate)
      return 1.0;

   double score = GetV869RegimeScore();
   double multiplier = 1.0;

   if(score <= InpRegimeHardBlockThreshold)
      multiplier = 0.0;
   else if(score < 40.0)
      multiplier = InpRegimeRiskScaleRisk;
   else if(score < 70.0)
      multiplier = InpRegimeRiskScaleWatch;

   if(InpRegimeDebugLog)
      Print("[v8.69_fix2b RegimeGate] multiplier=", DoubleToString(multiplier, 2),
            " score=", DoubleToString(score, 1),
            " threshold=", DoubleToString(InpRegimeHardBlockThreshold, 1));

   return multiplier;
}

double V869DiagBufferValue(const int handle, const int bufferIndex, const int shift)
{
   if(handle == INVALID_HANDLE)
      return 0.0;

   double values[];
   ArraySetAsSeries(values, true);
   int copied = CopyBuffer(handle, bufferIndex, shift, 1, values);
   if(copied <= 0)
      return 0.0;

   return values[0];
}

double V869DiagAtrAverage(const int shift, const int count)
{
   if(g_v869AtrHandle == INVALID_HANDLE || count <= 0)
      return 0.0;

   double values[];
   ArraySetAsSeries(values, true);
   int copied = CopyBuffer(g_v869AtrHandle, 0, shift, count, values);
   if(copied <= 0)
      return 0.0;

   double sum = 0.0;
   for(int i = 0; i < copied; i++)
      sum += values[i];

   return sum / copied;
}

void WriteV869EntryDiagnostics(bool forBuy, double entryPrice, double stopLoss, double lot,
                               double atrSignal, bool dangerCandle, bool wickConflict)
{
   if(!InpV869EntryDiagnosticLog || g_v869DiagFileHandle == INVALID_HANDLE)
      return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   datetime signalTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   MqlDateTime dt;
   TimeToStruct(barTime, dt);

   double atr14 = V869DiagBufferValue(g_v869AtrHandle, 0, 1);
   double atrAvg50 = V869DiagAtrAverage(1, 50);
   double atrRatio = (atrAvg50 > 0.0 ? atr14 / atrAvg50 : 0.0);
   double adx14 = V869DiagBufferValue(g_v869AdxHandle, 0, 1);
   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double ema50Now = V869DiagBufferValue(g_v869Ema50Handle, 0, 1);
   double ema50Prev = V869DiagBufferValue(g_v869Ema50Handle, 0, 2);
   double ma200Now = V869DiagBufferValue(g_ma200Handle, 0, 1);
   double ma200Prev = V869DiagBufferValue(g_ma200Handle, 0, 2);
   double ema50Slope = ema50Now - ema50Prev;
   double ma200Slope = ma200Now - ma200Prev;
   int trendAlignment = 0;
   if(forBuy && ema50Slope > 0.0 && ema50Now >= ma200Now)
      trendAlignment = 1;
   if(!forBuy && ema50Slope < 0.0 && ema50Now <= ma200Now)
      trendAlignment = 1;

   long spreadPoints = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   int consecutiveLosses = GetConsecutiveLosses();
   double regimeScore = GetV869RegimeScore();

   FileWrite(g_v869DiagFileHandle,
             _Symbol,
             EnumToString((ENUM_TIMEFRAMES)Period()),
             TimeToString(barTime, TIME_DATE | TIME_MINUTES),
             TimeToString(signalTime, TIME_DATE | TIME_MINUTES),
             (forBuy ? "buy" : "sell"),
             dt.hour,
             dt.day_of_week,
             DoubleToString(entryPrice, _Digits),
             DoubleToString(stopLoss, _Digits),
             DoubleToString(lot, 2),
             DoubleToString(atrSignal, _Digits),
             DoubleToString(atr14, _Digits),
             DoubleToString(atrAvg50, _Digits),
             DoubleToString(atrRatio, 4),
             DoubleToString(adx14, 2),
             DoubleToString(plusDi, 2),
             DoubleToString(minusDi, 2),
             DoubleToString(ema50Slope, _Digits),
             DoubleToString(ma200Slope, _Digits),
             trendAlignment,
             DoubleToString(GetWickToBodyRatio(1), 4),
             DoubleToString(GetUpperShadowRatio(1), 4),
             DoubleToString(GetLowerShadowRatio(1), 4),
             spreadPoints,
             consecutiveLosses,
             (dangerCandle ? 1 : 0),
             (wickConflict ? 1 : 0),
             DoubleToString(regimeScore, 2));
   FileFlush(g_v869DiagFileHandle);
}

double GetV869DiEdgeHourLotScale(bool forBuy)
{
   if(!InpUseV869DiEdgeHourScale)
      return 1.0;

   if(InpV869DiEdgeGateHour < 0 || InpV869DiEdgeGateHour > 23)
      return 1.0;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime <= 0)
      return 1.0;

   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   if(dt.hour != InpV869DiEdgeGateHour)
      return 1.0;

   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double directionalEdge = (forBuy ? plusDi - minusDi : minusDi - plusDi);
   if(directionalEdge >= InpV869MinDirectionalDiEdge)
      return 1.0;

   double scale = InpV869DiEdgeHourLotScale;
   if(scale < 0.0) scale = 0.0;
   if(scale > 1.0) scale = 1.0;

   if(InpV869DiEdgeGateDebug)
   {
      Print("[v8.69_fix5d DiEdgeScale] scaled ",
            (forBuy ? "BUY" : "SELL"),
            " hour=", dt.hour,
            " edge=", DoubleToString(directionalEdge, 2),
            " minEdge=", DoubleToString(InpV869MinDirectionalDiEdge, 2),
            " scale=", DoubleToString(scale, 2),
            " plusDI=", DoubleToString(plusDi, 2),
            " minusDI=", DoubleToString(minusDi, 2),
            " bar=", TimeToString(barTime, TIME_DATE | TIME_MINUTES));
   }

   return scale;
}

double GetV869ContextLotScale(bool forBuy)
{
   if(!InpUseV869ContextScale)
      return 1.0;

   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double adx = V869DiagBufferValue(g_v869AdxHandle, 0, 1);
   double directionalEdge = (forBuy ? plusDi - minusDi : minusDi - plusDi);

   bool weakDi = (directionalEdge < InpV869ContextMinDiEdge);
   bool lowAdx = (adx < InpV869ContextMaxAdx);
   double ema50Now = V869DiagBufferValue(g_v869Ema50Handle, 0, 1);
   double ema50Prev = V869DiagBufferValue(g_v869Ema50Handle, 0, 2);
   double ma200Now = V869DiagBufferValue(g_ma200Handle, 0, 1);
   double ema50Slope = ema50Now - ema50Prev;
   bool trendAligned = false;
   if(forBuy && ema50Slope > 0.0 && ema50Now >= ma200Now)
      trendAligned = true;
   if(!forBuy && ema50Slope < 0.0 && ema50Now <= ma200Now)
      trendAligned = true;

   bool active = false;

   if(InpV869ContextMode == 0)
      active = weakDi;
   else if(InpV869ContextMode == 2)
      active = lowAdx;
   else if(InpV869ContextMode == 3)
      active = (weakDi && !trendAligned);
   else
      active = (weakDi && lowAdx);

   if(!active)
      return 1.0;

   double scale = InpV869ContextLotScale;
   if(scale < 0.0) scale = 0.0;
   if(scale > 1.0) scale = 1.0;

   if(InpV869ContextDebug)
   {
      Print("[v8.69_fix6 ContextScale] scaled ",
            (forBuy ? "BUY" : "SELL"),
            " edge=", DoubleToString(directionalEdge, 2),
            " adx=", DoubleToString(adx, 2),
            " weakDi=", weakDi,
            " lowAdx=", lowAdx,
            " trendAligned=", trendAligned,
            " mode=", InpV869ContextMode,
            " scale=", DoubleToString(scale, 2));
   }

   return scale;
}

bool IsV869ResidualScaleHour(const int hour)
{
   if(hour == 1)  return InpV869ResidualScaleHour1;
   if(hour == 8)  return InpV869ResidualScaleHour8;
   if(hour == 12) return InpV869ResidualScaleHour12;
   if(hour == 20) return InpV869ResidualScaleHour20;
   return false;
}

double GetV869ResidualHourLotScale(bool forBuy)
{
   if(!InpUseV869ResidualHourScale)
      return 1.0;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime <= 0)
      return 1.0;

   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   if(!IsV869ResidualScaleHour(dt.hour))
      return 1.0;

   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double directionalEdge = (forBuy ? plusDi - minusDi : minusDi - plusDi);
   bool weakDi = (directionalEdge < InpV869ResidualMinDiEdge);

   double ema50Now = V869DiagBufferValue(g_v869Ema50Handle, 0, 1);
   double ema50Prev = V869DiagBufferValue(g_v869Ema50Handle, 0, 2);
   double ma200Now = V869DiagBufferValue(g_ma200Handle, 0, 1);
   double ema50Slope = ema50Now - ema50Prev;
   bool trendAligned = false;
   if(forBuy && ema50Slope > 0.0 && ema50Now >= ma200Now)
      trendAligned = true;
   if(!forBuy && ema50Slope < 0.0 && ema50Now <= ma200Now)
      trendAligned = true;

   bool active = false;
   if(InpV869ResidualConditionMode == 0)
      active = (weakDi && !trendAligned);
   else
      active = (weakDi || !trendAligned);

   if(!active)
      return 1.0;

   double scale = InpV869ResidualHourLotScale;
   if(scale < 0.0) scale = 0.0;
   if(scale > 1.0) scale = 1.0;

   if(InpV869ResidualScaleDebug)
   {
      Print("[v8.69_fix5d ResidualHourScale] scaled ",
            (forBuy ? "BUY" : "SELL"),
            " hour=", dt.hour,
            " edge=", DoubleToString(directionalEdge, 2),
            " weakDi=", weakDi,
            " trendAligned=", trendAligned,
            " mode=", InpV869ResidualConditionMode,
            " scale=", DoubleToString(scale, 2),
            " bar=", TimeToString(barTime, TIME_DATE | TIME_MINUTES));
   }

   return scale;
}

bool IsV869DiEdgeHourBlocked(bool forBuy)
{
   if(!InpUseV869DiEdgeHourGate)
      return false;

   if(InpV869DiEdgeGateHour < 0 || InpV869DiEdgeGateHour > 23)
      return false;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime <= 0)
      return false;

   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   if(dt.hour != InpV869DiEdgeGateHour)
      return false;

   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double directionalEdge = (forBuy ? plusDi - minusDi : minusDi - plusDi);
   bool blocked = (directionalEdge < InpV869MinDirectionalDiEdge);

   if(blocked && InpV869DiEdgeGateDebug)
   {
      Print("[v8.69_fix5d DiEdgeGate] blocked ",
            (forBuy ? "BUY" : "SELL"),
            " hour=", dt.hour,
            " edge=", DoubleToString(directionalEdge, 2),
            " minEdge=", DoubleToString(InpV869MinDirectionalDiEdge, 2),
            " plusDI=", DoubleToString(plusDi, 2),
            " minusDI=", DoubleToString(minusDi, 2),
            " bar=", TimeToString(barTime, TIME_DATE | TIME_MINUTES));
   }

   return blocked;
}

bool IsV869TimeClusterBlocked(bool forBuy)
{
   if(!InpUseV869TimeClusterGate)
      return false;

   if(InpV869BlockedEntryHour < 0 || InpV869BlockedEntryHour > 23)
      return false;

   if(forBuy && !InpV869BlockBuyAtHour)
      return false;

   if(!forBuy && !InpV869BlockSellAtHour)
      return false;

   int lossesForTimeGate = GetConsecutiveLosses();
   if(lossesForTimeGate < InpV869TimeGateMinLosses)
      return false;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime <= 0)
      barTime = TimeCurrent();

   MqlDateTime dt;
   TimeToStruct(barTime, dt);

   bool blocked = (dt.hour == InpV869BlockedEntryHour);
   if(blocked && InpV869TimeGateDebug)
   {
      Print("[v8.69_fix5d TimeGate] blocked ",
            (forBuy ? "BUY" : "SELL"),
            " entry at hour=", dt.hour,
            " lossesForTimeGate=", lossesForTimeGate,
            " minLosses=", InpV869TimeGateMinLosses,
            " bar=", TimeToString(barTime, TIME_DATE | TIME_MINUTES));
   }

   return blocked;
}

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

   scale *= GetDynamicGovernorLotScale();
   double v869RegimeMultiplier = GetV869RegimeRiskMultiplier();
   if(v869RegimeMultiplier <= 0.0)
   {
      if(InpRegimeDebugLog)
         Print("[v8.69 RegimeGate] new entry blocked by regime multiplier");
      return 0.0;
   }
   scale *= v869RegimeMultiplier;
   double adjustedLot = lot * scale;
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   adjustedLot = MathMax(minLot, MathMin(maxLot, adjustedLot));
   adjustedLot = MathFloor(adjustedLot / step) * step;

   return NormalizeDouble(adjustedLot, 2);
}

double NormalizeSpreadGovernorLot(double lot)
{
   if(lot <= 0.0)
      return 0.0;

   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(minLot <= 0.0 || maxLot <= 0.0 || step <= 0.0)
      return lot;

   if(lot < minLot)
      return 0.0;

   double adjustedLot = MathFloor(MathMin(maxLot, lot) / step) * step;
   if(adjustedLot < minLot)
      return 0.0;

   return NormalizeDouble(adjustedLot, 2);
}

double GetCurrentSpreadPoints()
{
   long spread = 0;
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD, spread))
      return (double)spread;

   double ask = 0.0;
   double bid = 0.0;
   double point = 0.0;
   SymbolInfoDouble(_Symbol, SYMBOL_ASK, ask);
   SymbolInfoDouble(_Symbol, SYMBOL_BID, bid);
   SymbolInfoDouble(_Symbol, SYMBOL_POINT, point);

   if(point <= 0.0)
      return 0.0;

   return MathMax(0.0, (ask - bid) / point);
}

int ClassifySpreadZone(const double spread_points)
{
   if(spread_points >= InpSpreadHardBlockPoints)
      return 3;
   if(spread_points >= InpSpreadWeakStartPoints)
      return 2;
   if(spread_points > InpSpreadNormalMaxPoints)
      return 1;
   return 0;
}

bool ApplySpreadCostGovernor(double &lots, const bool strong_context)
{
   if(InpSpreadGovernorMode <= 0)
      return true;

   double spread_points = GetCurrentSpreadPoints();
   int zone = ClassifySpreadZone(spread_points);
   double lots_before = lots;

   if(InpSpreadAuditPrint)
      Print("SPREAD_GOVERNOR_AUDIT spread=", DoubleToString(spread_points, 1),
            " zone=", zone,
            " lots_before=", DoubleToString(lots_before, 2),
            " mode=", InpSpreadGovernorMode);

   if(InpSpreadGovernorMode == 1)
      return true;

   if(zone >= 3)
   {
      if(InpSpreadAuditPrint)
         Print("SPREAD_GOVERNOR_AUDIT blocked new entry by hard spread zone");
      lots = 0.0;
      return false;
   }

   if(zone == 2)
   {
      if(InpSpreadGovernorMode >= 3 && InpSpreadRequireStrongContextInWeakZone && !strong_context)
      {
         if(InpSpreadAuditPrint)
            Print("SPREAD_GOVERNOR_AUDIT blocked new entry by weak spread context gate");
         lots = 0.0;
         return false;
      }
      lots *= InpSpreadWeakLotMultiplier;
   }
   else if(zone == 1)
   {
      lots *= InpSpreadWatchLotMultiplier;
   }

   lots = NormalizeSpreadGovernorLot(lots);

   if(InpSpreadAuditPrint)
      Print("SPREAD_GOVERNOR_AUDIT lots_after=", DoubleToString(lots, 2));

   return lots > 0.0;
}

double ClampV871Score(double value)
{
   return MathMax(0.0, MathMin(100.0, value));
}

double GetV871DirectionalContextScore(const bool forBuy)
{
   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double adx = V869DiagBufferValue(g_v869AdxHandle, 0, 1);
   double ema50Now = V869DiagBufferValue(g_v869Ema50Handle, 0, 1);
   double ema50Prev = V869DiagBufferValue(g_v869Ema50Handle, 0, 2);
   double ma200Now = V869DiagBufferValue(g_ma200Handle, 0, 1);

   double directionalEdge = forBuy ? plusDi - minusDi : minusDi - plusDi;
   double score = 0.0;

   score += ClampDouble(directionalEdge / 20.0, 0.0, 1.0) * 30.0;
   score += ClampDouble(adx / 30.0, 0.0, 1.0) * 20.0;

   double emaSlope = ema50Now - ema50Prev;
   bool trendAligned = false;
   if(forBuy && emaSlope > 0.0 && ema50Now >= ma200Now)
      trendAligned = true;
   if(!forBuy && emaSlope < 0.0 && ema50Now <= ma200Now)
      trendAligned = true;
   if(trendAligned)
      score += 20.0;

   double bodyRatio = GetBodyRatio(1);
   double wickToBody = GetWickToBodyRatio(1);
   score += ClampDouble(bodyRatio / MathMax(g_bodyRatio, 0.01), 0.0, 1.0) * 10.0;
   if(wickToBody <= 1.5)
      score += 5.0;

   return ClampV871Score(score);
}

bool IsV871StrongSpreadContext(const bool forBuy)
{
   if(!InpUseV871RealStrongContext)
      return true;

   double score = GetV871DirectionalContextScore(forBuy);
   bool strong = (score >= InpV871MinStrongContextScore);

   if(InpV871ContextAuditPrint)
      Print("V871_CONTEXT_AUDIT direction=", (forBuy ? "BUY" : "SELL"),
            " score=", DoubleToString(score, 1),
            " strong=", strong,
            " threshold=", DoubleToString(InpV871MinStrongContextScore, 1),
            " mode=", InpV871StrongContextMode);

   if(InpV871StrongContextMode <= 0)
      return true;

   return strong;
}

bool ApplyV871ContextGate(double &lots, const bool forBuy)
{
   if(!InpUseV871RealStrongContext || InpV871StrongContextMode <= 1)
      return true;

   bool strong = IsV871StrongSpreadContext(forBuy);
   if(strong)
      return true;

   if(InpV871StrongContextMode >= 3)
   {
      if(InpV871ContextAuditPrint)
         Print("V871_CONTEXT_AUDIT blocked weak context new entry");
      lots = 0.0;
      return false;
   }

   lots *= InpV871WeakContextLotScale;
   lots = NormalizeSpreadGovernorLot(lots);

   if(InpV871ContextAuditPrint)
      Print("V871_CONTEXT_AUDIT scaled weak context lots=", DoubleToString(lots, 2));

   return lots > 0.0;
}

// V873_CONTEXT_SCALING
// Default-off context-aware lot scaling candidate. Does not alter signal generation.
double ClampV873ContextScale(double value)
{
   if(value < 0.0)
      return 0.0;
   if(value > 1.0)
      return 1.0;
   return value;
}

double GetV873ContextScalingMultiplier(const bool forBuy)
{
   if(!InpUseV873ContextScaling)
      return 1.0;

   double multiplier = 1.0;
   double score = GetV871DirectionalContextScore(forBuy);
   double spreadPoints = GetCurrentSpreadPoints();

   if(score >= InpV873MidScoreMin && score < InpV873MidScoreMax)
      multiplier = MathMin(multiplier, ClampV873ContextScale(InpV873MidScoreLotScale));

   if(score >= InpV873HighScoreMin && spreadPoints >= InpV873HighSpreadMinPoints)
      multiplier = MathMin(multiplier, ClampV873ContextScale(InpV873HighScoreHighSpreadLotScale));

   return ClampV873ContextScale(multiplier);
}

bool ApplyV873ContextScaling(double &lots, const bool forBuy)
{
   if(!InpUseV873ContextScaling)
      return true;

   if(lots <= 0.0)
      return false;

   double multiplier = GetV873ContextScalingMultiplier(forBuy);
   if(multiplier <= 0.0)
   {
      if(InpV873ContextScalePrint)
         Print("V873_CONTEXT_SCALING block | direction=", (forBuy ? "buy" : "sell"), " | multiplier=", DoubleToString(multiplier, 2));
      return false;
   }

   double originalLots = lots;
   double scaledLots = lots * multiplier;
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(minLot > 0.0 && scaledLots < minLot)
   {
      if(InpV873ContextScalePrint)
         Print("V873_CONTEXT_SCALING below min lot | direction=", (forBuy ? "buy" : "sell"),
               " | original=", DoubleToString(originalLots, 2),
               " | scaled=", DoubleToString(scaledLots, 2),
               " | min=", DoubleToString(minLot, 2));
      return false;
   }

   lots = AdjustLotSize(scaledLots);
   if(lots <= 0.0)
      return false;

   if(InpV873ContextScalePrint && MathAbs(lots - originalLots) > 0.0000001)
   {
      double score = GetV871DirectionalContextScore(forBuy);
      double spreadPoints = GetCurrentSpreadPoints();
      Print("V873_CONTEXT_SCALING scale | direction=", (forBuy ? "buy" : "sell"),
            " | score=", DoubleToString(score, 2),
            " | spread=", DoubleToString(spreadPoints, 1),
            " | multiplier=", DoubleToString(multiplier, 2),
            " | lot=", DoubleToString(originalLots, 2), "->", DoubleToString(lots, 2));
   }

   return true;
}
bool OpenV872ContextDiagnosticFile()
{
   if(!InpUseV872ContextDiagnostics)
      return true;

   int flags = FILE_WRITE | FILE_CSV | FILE_ANSI;
   if(InpV872ContextDiagnosticCommon)
      flags |= FILE_COMMON;

   g_v872ContextDiagFileHandle = FileOpen(InpV872ContextDiagnosticFile, flags, ',');
   if(g_v872ContextDiagFileHandle == INVALID_HANDLE)
   {
      Print("V872_CONTEXT_DIAG FileOpen failed | file=", InpV872ContextDiagnosticFile,
            " err=", GetLastError());
      return false;
   }

   FileWrite(g_v872ContextDiagFileHandle,
             "symbol", "period", "bar_time", "signal_time", "direction", "entry_hour", "entry_dow",
             "entry_price", "stop_loss", "lot", "context_score", "strong_context", "threshold",
             "spread_points", "adx14", "plus_di", "minus_di", "directional_edge",
             "body_ratio", "wick_to_body", "trade_send_stage");
   FileFlush(g_v872ContextDiagFileHandle);
   return true;
}

void CloseV872ContextDiagnosticFile()
{
   if(g_v872ContextDiagFileHandle == INVALID_HANDLE)
      return;

   FileFlush(g_v872ContextDiagFileHandle);
   FileClose(g_v872ContextDiagFileHandle);
   g_v872ContextDiagFileHandle = INVALID_HANDLE;
}

void WriteV872ContextDiagnostics(bool forBuy, double entryPrice, double stopLoss, double lot)
{
   if(!InpUseV872ContextDiagnostics)
      return;
   if(g_v872ContextDiagFileHandle == INVALID_HANDLE)
      return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   datetime signalTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   MqlDateTime dt;
   TimeToStruct(signalTime > 0 ? signalTime : barTime, dt);

   double score = GetV871DirectionalContextScore(forBuy);
   bool strong = (score >= InpV871MinStrongContextScore);
   double plusDi = V869DiagBufferValue(g_v869AdxHandle, 1, 1);
   double minusDi = V869DiagBufferValue(g_v869AdxHandle, 2, 1);
   double adx = V869DiagBufferValue(g_v869AdxHandle, 0, 1);
   double directionalEdge = forBuy ? plusDi - minusDi : minusDi - plusDi;
   double bodyRatio = GetBodyRatio(1);
   double wickToBody = GetWickToBodyRatio(1);
   double spreadPoints = GetCurrentSpreadPoints();

   FileWrite(g_v872ContextDiagFileHandle,
             _Symbol,
             EnumToString((ENUM_TIMEFRAMES)Period()),
             TimeToString(barTime, TIME_DATE | TIME_MINUTES),
             TimeToString(signalTime, TIME_DATE | TIME_MINUTES),
             (forBuy ? "buy" : "sell"),
             dt.hour,
             dt.day_of_week,
             DoubleToString(entryPrice, _Digits),
             DoubleToString(stopLoss, _Digits),
             DoubleToString(lot, 2),
             DoubleToString(score, 2),
             (strong ? 1 : 0),
             DoubleToString(InpV871MinStrongContextScore, 2),
             DoubleToString(spreadPoints, 1),
             DoubleToString(adx, 2),
             DoubleToString(plusDi, 2),
             DoubleToString(minusDi, 2),
             DoubleToString(directionalEdge, 2),
             DoubleToString(bodyRatio, 4),
             DoubleToString(wickToBody, 2),
             "pre_send");
   FileFlush(g_v872ContextDiagFileHandle);

   if(InpV872ContextDiagnosticPrint)
      Print("V872_CONTEXT_DIAG direction=", (forBuy ? "BUY" : "SELL"),
            " score=", DoubleToString(score, 2),
            " strong=", strong,
            " spread=", DoubleToString(spreadPoints, 1),
            " lot=", DoubleToString(lot, 2));
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

double ClampDouble(double value, double minValue, double maxValue)
{
   return MathMax(minValue, MathMin(maxValue, value));
}

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

         bool better = (!info.valid || touches > info.touches || (touches == info.touches && newShift < info.anchorShiftNew));
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
   double bodyScore = (g_bodyRatio <= 0) ? 30.0 : ClampDouble(bodyRatio / g_bodyRatio, 0.0, 1.0) * 30.0;
   double shadow = forBuy ? GetUpperShadowRatio(1) : GetLowerShadowRatio(1);
   double shadowScore = 0.0;

   if(g_maxOppositeShadow <= 0)
      shadowScore = (shadow <= 0) ? 25.0 : 0.0;
   else if(shadow <= g_maxOppositeShadow)
      shadowScore = 25.0;
   else
      shadowScore = ClampDouble(1.0 - ((shadow - g_maxOppositeShadow) / g_maxOppositeShadow), 0.0, 1.0) * 25.0;

   double distanceTarget = InpMinBreakoutDistanceATR * 2.0;
   double distanceScore = (distanceTarget <= 0) ? 25.0 : ClampDouble(info.breakoutDistanceATR / distanceTarget, 0.0, 1.0) * 25.0;
   double score = bodyScore + shadowScore + distanceScore;

   if(dangerousCandle) score -= 30.0;
   if(g_requireFollowThrough)
   {
      bool followOk = forBuy ? IsHighestClose(1, g_followThroughBars) : IsLowestClose(1, g_followThroughBars);
      if(followOk) score += 20.0;
   }

   return ClampDouble(score, 0.0, 100.0);
}

bool GetStructureQualityFactor(bool forBuy, double atr, bool dangerousCandle, STrendlineInfo &info, double &quality)
{
   quality = 1.0;
   ResetTrendlineInfo(info);

   if(!InpUseStructureScore)
   {
      info.valid = true;
      info.score = 100.0;
      return true;
   }

   bool found = FindValidatedTrendline(forBuy, atr, info);
   if(!found)
   {
      if(InpShowStructureDebug)
         Print("Structure score: ", (forBuy ? "BUY" : "SELL"), " no valid structure");

      if(!InpRejectNoStructure)
      {
         quality = ClampDouble(InpNoStructurePenalty, 0.0, 1.0);
         info.valid = false;
         info.score = 0.0;
         return true;
      }

      return false;
   }

   info.score = CalculateBreakoutScore(forBuy, atr, info, dangerousCandle);
   if(InpShowStructureDebug)
   {
      Print("Structure score: ", (forBuy ? "BUY" : "SELL"),
            " | touches:", info.touches,
            " | distanceATR:", DoubleToString(info.breakoutDistanceATR, 2),
            " | score:", DoubleToString(info.score, 1));
   }

   if(InpMinBreakoutScore <= 0)
      quality = 1.0;
   else
      quality = ClampDouble(info.score / InpMinBreakoutScore,
                            ClampDouble(InpMinStructureQualityFloor, 0.0, 1.0),
                            1.0);

   return true;
}

double GetStructureLotFactor(bool forBuy, double atr, bool dangerousCandle)
{
   STrendlineInfo info;
   double quality = 1.0;
   if(!GetStructureQualityFactor(forBuy, atr, dangerousCandle, info, quality))
      return 0.0;
   double factor = ClampDouble(quality, 0.0, 1.0);
   if(InpLogStructureScore || InpLogSignalReasons)
   {
      DecisionLog(2, StringFormat("structure %s factor=%.3f score=%.1f touches=%d valid=%s",
                                  (forBuy ? "BUY" : "SELL"),
                                  factor,
                                  info.score,
                                  info.touches,
                                  (info.valid ? "true" : "false")));
   }
   return factor;
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






// V875_MIDSCORE_SPREAD_GUARD
// Default-off narrow guard derived from weak-cluster trade-level simulation.
// It targets only the intersection of mid context score and moderate spread.
double GetV875MidScoreSpreadMultiplier(const bool forBuy)
{
   if(!InpUseV875MidScoreSpreadGuard)
      return 1.0;

   double score = GetV871DirectionalContextScore(forBuy);
   double spread = GetCurrentSpreadPoints();

   bool scoreMatch = (score >= InpV875MidScoreMin && score < InpV875MidScoreMax);
   bool spreadMatch = (spread >= InpV875SpreadMinPoints && spread < InpV875SpreadMaxPoints);

   if(!(scoreMatch && spreadMatch))
      return 1.0;

   if(InpV875MidScoreSpreadHardBlock)
      return 0.0;

   double scale = InpV875MidScoreSpreadLotScale;
   if(scale < 0.0) scale = 0.0;
   if(scale > 1.0) scale = 1.0;
   return scale;
}

bool ApplyV875MidScoreSpreadGuard(double &lots, const bool forBuy)
{
   if(!InpUseV875MidScoreSpreadGuard)
      return true;

   if(lots <= 0.0)
      return false;

   double score = GetV871DirectionalContextScore(forBuy);
   double spread = GetCurrentSpreadPoints();
   double multiplier = GetV875MidScoreSpreadMultiplier(forBuy);

   if(multiplier <= 0.0)
   {
      if(InpV875MidScoreSpreadPrint)
         Print("V875_MIDSCORE_SPREAD_GUARD block | direction=", (forBuy ? "buy" : "sell"),
               " | score=", DoubleToString(score, 2),
               " | spread=", DoubleToString(spread, 1));
      lots = 0.0;
      return false;
   }

   if(multiplier >= 1.0)
      return true;

   double originalLots = lots;
   lots = NormalizeSpreadGovernorLot(lots * multiplier);
   if(lots <= 0.0)
      return false;

   if(InpV875MidScoreSpreadPrint && MathAbs(lots - originalLots) > 0.0000001)
      Print("V875_MIDSCORE_SPREAD_GUARD scale | direction=", (forBuy ? "buy" : "sell"),
            " | score=", DoubleToString(score, 2),
            " | spread=", DoubleToString(spread, 1),
            " | lot=", DoubleToString(originalLots, 2), "->", DoubleToString(lots, 2));

   return true;
}
