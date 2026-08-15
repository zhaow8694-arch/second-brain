//+------------------------------------------------------------------+
//|                                                ZWeiGoldEA_v1.0.mq5 |
//|                  基于 Z-Wei 交易体系 · 黄金专用狙击式交易EA          |
//|                                                                  |
//|  核心设计（一一对应 Z-Wei 理论）：                                  |
//|                                                                  |
//|  主周期: H4（4小时）- 结构识别 & 信号生成                          |
//|  分形确认: H1（1小时）- 自同构结构二次验证                          |
//|                                                                  |
//|  入场信号: MACD柱状图翻转 + ZigZag结构突破(BoS) 混合检测            |
//|                                                                  |
//|  5层质量过滤:                                                      |
//|    [1] MA200趋势方向 + ADX强度确认                                 |
//|    [2] K线实体占比 + MACD柱状图翻转                                |
//|    [3] 单边反向影线惩罚（做多禁上影、做空禁下影）                   |
//|    [4] 危险K线过滤（振幅 > N×ATR → 拒绝）                          |
//|    [5] 点火与跟随确认（突破后需共识跟进）                           |
//|                                                                  |
//|  风险管理: ATR动态止损 + 移动止盈 + 单笔%风险                       |
//|                                                                  |
//|  哲学根基:                                                         |
//|    - 市场不可预测 → 建立可重复执行的系统                            |
//|    - 交易是选择而非预测 → 狙击手式耐心等待高质量结构                |
//|    - 适应市场 → 无法分类的行情不参与                                |
//|    - 分形自同构 → H4信号需H1结构验证                                |
//|    - 放弃完整行情 → 只抓确定性波段，积少成多                        |
//+------------------------------------------------------------------+
#property copyright "Z-Wei Trading System | Gold Specialized EA v1.0"
#property version   "1.00"
#property description "Z-Wei Gold EA — Wyckoff + MACD + ZigZag BoS + 5-Layer Filter"
#property description "Primary: H4 | Fractal Confirm: H1 | Specialized for XAUUSD"
#property strict

//+------------------------------------------------------------------+
//| 枚举定义                                                           |
//+------------------------------------------------------------------+
enum ENUM_LOWER_TF
{
   LOWER_TF_M15  = PERIOD_M15,   // 15分钟（激进）
   LOWER_TF_M30  = PERIOD_M30,   // 30分钟（平衡）
   LOWER_TF_H1   = PERIOD_H1,    // 1小时（推荐）
};

enum ENUM_BOS_MODE
{
   BOS_MODE_STRICT  = 0,  // 严格模式：必须同时满足MACD+BoS
   BOS_MODE_FLEX    = 1,  // 灵活模式：MACD或BoS任一满足即入场
   BOS_MODE_MACD    = 2,  // 纯MACD模式
};

//+------------------------------------------------------------------+
//| 输入参数                                                           |
//+------------------------------------------------------------------+
input group "══════════════════════════════════════════════════════════"
input group "【1】MACD 参数"
input group "══════════════════════════════════════════════════════════"
input int      InpFastEMA           = 12;        // MACD 快线周期
input int      InpSlowEMA           = 26;        // MACD 慢线周期
input int      InpSignalSMA         = 9;         // MACD 信号线周期

input group "══════════════════════════════════════════════════════════"
input group "【2】ZigZag 结构突破 (BoS) 参数"
input group "══════════════════════════════════════════════════════════"
input int      InpZigZagDepth       = 12;        // ZigZag 深度
input int      InpZigZagDeviation   = 5;         // ZigZag 偏差（点数）
input int      InpZigZagBackstep    = 3;         // ZigZag 回退步数
input int      InpBoSLookback       = 5;         // BoS回看：分析最近N个ZigZag转折点
input bool     InpRequireBoS        = true;      // 是否启用ZigZag BoS结构确认

input group "══════════════════════════════════════════════════════════"
input group "【3】MA200 趋势过滤"
input group "══════════════════════════════════════════════════════════"
input int      InpMA200Period       = 200;       // MA200 周期
input bool     InpUseMA200Filter    = true;      // 启用MA200趋势过滤
input double   InpMA200BufferATR    = 0.5;       // MA200缓冲区 (ATR倍数，0=严格)

input group "══════════════════════════════════════════════════════════"
input group "【4】ADX 趋势强度过滤"
input group "══════════════════════════════════════════════════════════"
input bool     InpUseADX            = true;      // 启用ADX过滤
input int      InpADXPeriod         = 14;        // ADX 周期
input double   InpADXThreshold      = 20.0;      // ADX 阈值（≥此值允许入场）

input group "══════════════════════════════════════════════════════════"
input group "【5】K线质量过滤（第2-4层）"
input group "══════════════════════════════════════════════════════════"
input double   InpBodyRatio         = 0.60;      // [层2] K线实体占比阈值（≥60%）
input double   InpMaxOppositeShadow = 0.20;      // [层3] 反向影线最大占比（做多=上影/做空=下影）
input double   InpMaxCandleATR      = 2.5;       // [层4] 危险K线振幅上限（ATR倍数）

input group "══════════════════════════════════════════════════════════"
input group "【6】点火与跟随确认（第5层）"
input group "══════════════════════════════════════════════════════════"
input bool     InpRequireFollowThrough = false;  // [层5] 启用点火跟随确认
input int      InpFollowThroughBars = 3;         // 跟随确认回看K线数
input double   InpFollowThroughMinPct = 0.30;    // 跟进幅度最小比例（相对突破K线实体）

input group "══════════════════════════════════════════════════════════"
input group "【7】多周期分形确认"
input group "══════════════════════════════════════════════════════════"
input bool     InpUseMultiTF        = true;      // 启用多周期分形确认
input ENUM_LOWER_TF InpLowerTF      = LOWER_TF_H1;// 下级确认周期
input bool     InpRequireLowerBoS   = false;     // 要求下级周期也出现BoS结构
input bool     InpRequireLowerMACD  = true;      // 要求下级周期MACD方向一致

input group "══════════════════════════════════════════════════════════"
input group "【8】波动率过滤"
input group "══════════════════════════════════════════════════════════"
input bool     InpUseATRFilter      = false;     // 启用波动率过滤
input int      InpATRFilterPeriod   = 20;        // ATR过滤周期
input double   InpATRMinRatio       = 0.8;       // 当前ATR/历史ATR最小比值

input group "══════════════════════════════════════════════════════════"
input group "【9】时间过滤"
input group "══════════════════════════════════════════════════════════"
input bool     InpUseTimeFilter     = false;     // 启用时间过滤
input int      InpStartHour         = 0;         // 开始交易小时（0-23, 服务器时间）
input int      InpEndHour           = 24;        // 结束交易小时（0-24, 24=全天）

input group "══════════════════════════════════════════════════════════"
input group "【10】风险管理"
input group "══════════════════════════════════════════════════════════"
input double   InpRiskPercent       = 0.5;       // 单笔风险（账户%）
input double   InpATRMultiplier     = 1.5;       // 止损 = ATR × 倍数
input int      InpATRPeriod         = 14;        // ATR 计算周期
input double   InpTrailingStart     = 2.0;       // 移动止盈启动（ATR倍数）
input double   InpTrailingStep      = 1.5;       // 移动止盈步长（ATR倍数）
input double   InpTakeProfitATR     = 3.0;       // 止盈（ATR倍数，0=仅用移动止盈）

input group "══════════════════════════════════════════════════════════"
input group "【11】交易设置"
input group "══════════════════════════════════════════════════════════"
input int      InpMagicNumber       = 20260624;  // 魔术号
input string   InpComment           = "ZWeiGold";// 订单注释
input bool     InpEnableLong        = true;      // 允许做多
input bool     InpEnableShort       = true;      // 允许做空
input int      InpMaxPositions      = 1;         // 最大同向持仓
input double   InpMaxSpread         = 50;        // 最大点差限制
input bool     InpDebugMode         = true;      // 调试模式（输出日志）

//+------------------------------------------------------------------+
//| 全局变量 - 指标句柄（主周期 H4）                                    |
//+------------------------------------------------------------------+
// H4 句柄
int g_macdHandle_H4;
int g_atrHandle_H4;
int g_ma200Handle_H4;
int g_adxHandle_H4;
int g_zigzagHandle_H4;
int g_atrFilterHandle_H4;

// H1 句柄（分形确认）
int g_macdHandle_Lower;
int g_zigzagHandle_Lower;
int g_atrHandle_Lower;

//+------------------------------------------------------------------+
//| 全局变量 - 运行时状态                                               |
//+------------------------------------------------------------------+
datetime g_lastBarTime_H4    = 0;     // H4最后处理K线时间
datetime g_lastBarTime_Lower = 0;     // 下级周期最后处理K线时间
datetime g_lastTrailBarTime  = 0;     // 移动止盈最后处理时间
datetime g_lastSignalBarTime = 0;     // 上次信号K线时间（防重复）

bool     g_pendingLong        = false; // 待确认做多
bool     g_pendingShort       = false; // 待确认做空
int      g_pendingBars        = 0;     // 待确认已等待K线数
int      g_pendingMaxBars     = 3;     // 最大等待K线数（H4）

// 入场管理：防止同根K线重复入场
datetime g_lastLongEntryBar  = 0;
datetime g_lastShortEntryBar = 0;

//+------------------------------------------------------------------+
//| 结构体 - ZigZag转折点                                              |
//+------------------------------------------------------------------+
struct ZigZagPivot
{
   datetime time;       // 转折点时间
   double   price;      // 转折点价格
   int      index;      // K线索引
   bool     isHigh;     // true=高点, false=低点
};

//+------------------------------------------------------------------+
//| 结构体 - 入场信号评估结果                                            |
//+------------------------------------------------------------------+
struct SignalResult
{
   bool     valid;          // 信号是否有效
   int      direction;      // 1=做多, -1=做空, 0=无信号
   string   rejectReason;   // 拒绝原因（调试用）
   double   score;          // 信号评分（0-100）
   int      passedFilters;  // 通过过滤器数量
};

//+------------------------------------------------------------------+
//| 初始化                                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("══════════════════════════════════════════");
   Print("ZWeiGoldEA v1.0 初始化开始");
   Print("品种: ", _Symbol, " | 主周期: H4 | 下级确认: ", EnumToString((ENUM_TIMEFRAMES)InpLowerTF));
   Print("══════════════════════════════════════════");

//--- 创建H4指标句柄 ---
   g_macdHandle_H4 = iMACD(_Symbol, PERIOD_H4,
                           InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
   if(g_macdHandle_H4 == INVALID_HANDLE)
   {
      Print("❌ H4 MACD句柄创建失败！错误码: ", GetLastError());
      return INIT_FAILED;
   }

   g_atrHandle_H4 = iATR(_Symbol, PERIOD_H4, InpATRPeriod);
   if(g_atrHandle_H4 == INVALID_HANDLE)
   {
      Print("❌ H4 ATR句柄创建失败！错误码: ", GetLastError());
      return INIT_FAILED;
   }

   g_ma200Handle_H4 = iMA(_Symbol, PERIOD_H4, InpMA200Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_ma200Handle_H4 == INVALID_HANDLE)
   {
      Print("❌ H4 MA200句柄创建失败！错误码: ", GetLastError());
      return INIT_FAILED;
   }

   if(InpUseADX)
   {
      g_adxHandle_H4 = iADX(_Symbol, PERIOD_H4, InpADXPeriod);
      if(g_adxHandle_H4 == INVALID_HANDLE)
      {
         Print("❌ H4 ADX句柄创建失败！错误码: ", GetLastError());
         return INIT_FAILED;
      }
   }

   if(InpRequireBoS)
   {
      g_zigzagHandle_H4 = iCustom(_Symbol, PERIOD_H4, "Examples\\ZigZag",
                                   InpZigZagDepth, InpZigZagDeviation, InpZigZagBackstep);
      if(g_zigzagHandle_H4 == INVALID_HANDLE)
      {
         Print("⚠️ H4 ZigZag句柄创建失败（将使用价格动作BoS检测替代）。错误码: ", GetLastError());
         // 不致命，将使用基于价格动作的备用BoS检测
      }
   }

   if(InpUseATRFilter)
   {
      g_atrFilterHandle_H4 = iATR(_Symbol, PERIOD_H4, InpATRFilterPeriod);
   }

//--- 创建下级周期指标句柄 ---
   if(InpUseMultiTF)
   {
      g_macdHandle_Lower = iMACD(_Symbol, InpLowerTF,
                                  InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
      if(g_macdHandle_Lower == INVALID_HANDLE)
      {
         Print("⚠️ 下级MACD句柄创建失败。多周期确认将仅使用结构判断。");
      }

      if(InpRequireLowerBoS)
      {
         g_zigzagHandle_Lower = iCustom(_Symbol, InpLowerTF, "Examples\\ZigZag",
                                         InpZigZagDepth, InpZigZagDeviation, InpZigZagBackstep);
      }

      g_atrHandle_Lower = iATR(_Symbol, InpLowerTF, InpATRPeriod);
   }

//--- 初始化状态 ---
   g_lastBarTime_H4    = 0;
   g_lastBarTime_Lower = 0;
   g_lastTrailBarTime  = 0;
   g_lastSignalBarTime = 0;
   g_pendingLong       = false;
   g_pendingShort      = false;
   g_pendingBars       = 0;
   g_lastLongEntryBar  = 0;
   g_lastShortEntryBar = 0;

   Print("✅ ZWeiGoldEA v1.0 初始化成功！");
   Print("   主周期: H4 | 下级周期: ", EnumToString((ENUM_TIMEFRAMES)InpLowerTF));
   Print("   MA200过滤: ", InpUseMA200Filter ? "开" : "关");
   Print("   ADX过滤: ", InpUseADX ? "开" : "关");
   Print("   多周期分形: ", InpUseMultiTF ? "开" : "关");
   Print("   点火跟随: ", InpRequireFollowThrough ? "开" : "关");
   Print("   单笔风险: ", InpRiskPercent, "% | 魔法号: ", InpMagicNumber);
   Print("══════════════════════════════════════════");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 释放                                                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_macdHandle_H4      != INVALID_HANDLE) IndicatorRelease(g_macdHandle_H4);
   if(g_atrHandle_H4       != INVALID_HANDLE) IndicatorRelease(g_atrHandle_H4);
   if(g_ma200Handle_H4     != INVALID_HANDLE) IndicatorRelease(g_ma200Handle_H4);
   if(g_adxHandle_H4       != INVALID_HANDLE) IndicatorRelease(g_adxHandle_H4);
   if(g_zigzagHandle_H4    != INVALID_HANDLE) IndicatorRelease(g_zigzagHandle_H4);
   if(g_atrFilterHandle_H4 != INVALID_HANDLE) IndicatorRelease(g_atrFilterHandle_H4);
   if(g_macdHandle_Lower   != INVALID_HANDLE) IndicatorRelease(g_macdHandle_Lower);
   if(g_zigzagHandle_Lower != INVALID_HANDLE) IndicatorRelease(g_zigzagHandle_Lower);
   if(g_atrHandle_Lower    != INVALID_HANDLE) IndicatorRelease(g_atrHandle_Lower);

   Comment("");
   Print("ZWeiGoldEA v1.0 已释放。退出原因: ", reason);
}

//+------------------------------------------------------------------+
//| 主循环 - OnTick                                                    |
//+------------------------------------------------------------------+
void OnTick()
{
//--- 1. 获取当前H4 K线时间 ---
   datetime currentBar_H4 = iTime(_Symbol, PERIOD_H4, 0);

//--- 2. 风险管理: 移动止盈（每个tick检查） ---
   ManageTrailingStop();

//--- 3. 仅在新K线开始时执行信号分析 ---
   if(currentBar_H4 == g_lastBarTime_H4 && g_lastBarTime_H4 != 0)
      return;  // 同一根H4 K线，已处理过

   g_lastBarTime_H4 = currentBar_H4;

//--- 4. 检查点差 ---
   if(!CheckSpread()) return;

//--- 5. 检查时间过滤 ---
   if(!CheckTimeFilter()) return;

//--- 6. 检查波动率 ---
   if(!CheckVolatility()) return;

//--- 7. 处理待确认信号（点火→跟随窗口） ---
   if(g_pendingLong || g_pendingShort)
   {
      ProcessPendingSignal();
   }

//--- 8. 主信号分析 ---
   SignalResult signal = AnalyzeSignal();

//--- 9. 输出调试信息 ---
   if(InpDebugMode && signal.valid)
   {
      Print("🎯 [信号] 方向=", signal.direction > 0 ? "做多" : "做空",
            " | 评分=", DoubleToString(signal.score, 1),
            " | 通过过滤层=", signal.passedFilters, "/5");
   }
   else if(InpDebugMode && signal.rejectReason != "")
   {
      // 仅在信号接近通过时输出拒绝原因，避免日志洪水
      if(signal.passedFilters >= 3)
         Print("🔸 [拒绝] ", signal.rejectReason, " (通过层数: ", signal.passedFilters, "/5)");
   }

//--- 10. 如果信号有效，触发入场流程 ---
   if(signal.valid)
   {
      if(InpRequireFollowThrough)
      {
         // 点火已确认，等待跟随
         if(signal.direction > 0)
         {
            g_pendingLong  = true;
            g_pendingShort = false;
         }
         else
         {
            g_pendingShort = true;
            g_pendingLong  = false;
         }
         g_pendingBars = 0;
         g_lastSignalBarTime = currentBar_H4;
      }
      else
      {
         // 不需要跟随确认，直接入场
         ExecuteEntry(signal.direction);
      }
   }

//--- 11. 更新图表注释 ---
   UpdateComment();
}

//+------------------------------------------------------------------+
//| 核心函数: 信号分析（5层过滤）                                        |
//+------------------------------------------------------------------+
SignalResult AnalyzeSignal()
{
   SignalResult result;
   ZeroMemory(result);
   result.direction = 0;
   result.valid = false;

//--- 获取H4数据 ---
   double macdMain[], macdSignal[];
   ArraySetAsSeries(macdMain, true);
   ArraySetAsSeries(macdSignal, true);

   if(CopyBuffer(g_macdHandle_H4, 0, 0, 5, macdMain) < 5)   // MACD主线
   { result.rejectReason = "MACD数据获取失败"; return result; }
   if(CopyBuffer(g_macdHandle_H4, 1, 0, 5, macdSignal) < 5) // MACD信号线
   { result.rejectReason = "MACD信号数据获取失败"; return result; }

   // MACD柱状图 = 主线 - 信号线
   double hist[5];
   for(int i = 0; i < 5; i++)
      hist[i] = macdMain[i] - macdSignal[i];

   double close[], open[], high[], low[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   if(CopyClose(_Symbol, PERIOD_H4, 0, 5, close) < 5)
   { result.rejectReason = "价格数据获取失败"; return result; }
   if(CopyOpen(_Symbol, PERIOD_H4, 0, 5, open) < 5)
   { result.rejectReason = "开盘价数据获取失败"; return result; }
   if(CopyHigh(_Symbol, PERIOD_H4, 0, 5, high) < 5)
   { result.rejectReason = "最高价数据获取失败"; return result; }
   if(CopyLow(_Symbol, PERIOD_H4, 0, 5, low) < 5)
   { result.rejectReason = "最低价数据获取失败"; return result; }

   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_atrHandle_H4, 0, 0, 3, atr) < 3)
   { result.rejectReason = "ATR数据获取失败"; return result; }

//--- 检测MACD柱状图翻转 ---
   // hist[1] = 前一根K线的柱状图, hist[2] = 更早一根
   // 做多信号: 柱状图由负翻正（hist[2]<0 && hist[1]>0）
   // 做空信号: 柱状图由正翻负（hist[2]>0 && hist[1]<0）

   bool macdBullFlip = (hist[2] < 0 && hist[1] > 0);  // 空转多
   bool macdBearFlip = (hist[2] > 0 && hist[1] < 0);  // 多转空

//--- 检测结构突破（BoS）—— 优先ZigZag，自动回退到价格动作检测 ---
   bool bosBull = false;
   bool bosBear = false;

   if(InpRequireBoS)
   {
      bosBull = DetectBullishBoS_H4();
      bosBear = DetectBearishBoS_H4();
   }

//--- 确定初步方向 ---
   int rawDirection = 0;
   if(InpRequireBoS)
   {
      // 混合模式：MACD + BoS 都需满足（严格）
      if(macdBullFlip && bosBull)
         rawDirection = 1;
      else if(macdBearFlip && bosBear)
         rawDirection = -1;
   }
   else
   {
      // 纯MACD模式
      if(macdBullFlip)      rawDirection = 1;
      else if(macdBearFlip) rawDirection = -1;
   }

   if(rawDirection == 0)
   {
      if(macdBullFlip || macdBearFlip)
         result.rejectReason = "MACD翻转但BoS结构未确认";
      else
         result.rejectReason = "无MACD翻转信号";
      return result;
   }

   result.passedFilters = 0;

//--- [层1] MA200 趋势方向过滤 ---
   if(InpUseMA200Filter)
   {
      double ma200[];
      ArraySetAsSeries(ma200, true);
      if(CopyBuffer(g_ma200Handle_H4, 0, 0, 2, ma200) >= 2)
      {
         double bufferDist = atr[1] * InpMA200BufferATR;
         double prevClose = close[1];  // 上一根已收盘K线

         if(rawDirection > 0)
         {
            // 做多: 收盘价应在MA200上方（或缓冲区允许范围内）
            if(prevClose < ma200[0] - bufferDist)
            {
               result.rejectReason = StringFormat("[层1] MA200拒绝做多: Close=%.2f < MA200=%.2f",
                                                  prevClose, ma200[0]);
               return result;
            }
         }
         else
         {
            // 做空: 收盘价应在MA200下方
            if(prevClose > ma200[0] + bufferDist)
            {
               result.rejectReason = StringFormat("[层1] MA200拒绝做空: Close=%.2f > MA200=%.2f",
                                                  prevClose, ma200[0]);
               return result;
            }
         }
      }
   }
   result.passedFilters++;

//--- [层1] ADX 趋势强度过滤 ---
   if(InpUseADX && g_adxHandle_H4 != INVALID_HANDLE)
   {
      double adxVal[];
      ArraySetAsSeries(adxVal, true);
      if(CopyBuffer(g_adxHandle_H4, 0, 0, 2, adxVal) >= 2)
      {
         if(adxVal[1] < InpADXThreshold)
         {
            result.rejectReason = StringFormat("[层1] ADX=%0.1f < 阈值%0.1f，趋势太弱",
                                               adxVal[1], InpADXThreshold);
            return result;
         }
      }
   }
   result.passedFilters++;

//--- [层2] K线实体占比过滤 ---
   double bodyCandle = MathAbs(close[1] - open[1]);     // 前一根K线（触发K线）
   double rangeCandle = high[1] - low[1];

   if(rangeCandle <= 0)
   {
      result.rejectReason = "[层2] K线振幅为0（异常数据）";
      return result;
   }

   double bodyRatio = bodyCandle / rangeCandle;
   if(bodyRatio < InpBodyRatio)
   {
      result.rejectReason = StringFormat("[层2] 实体占比=%0.1f%% < 阈值%0.0f%%",
                                         bodyRatio * 100, InpBodyRatio * 100);
      return result;
   }
   result.passedFilters++;

//--- [层3] 单边反向影线惩罚 ---
   double oppositeShadowRatio;
   if(rawDirection > 0)
   {
      // 做多: 惩罚上影线（卖压在上方）
      double upperShadow = high[1] - MathMax(open[1], close[1]);
      oppositeShadowRatio = (rangeCandle > 0) ? upperShadow / rangeCandle : 0;
   }
   else
   {
      // 做空: 惩罚下影线（买盘在下方承接）
      double lowerShadow = MathMin(open[1], close[1]) - low[1];
      oppositeShadowRatio = (rangeCandle > 0) ? lowerShadow / rangeCandle : 0;
   }

   if(oppositeShadowRatio > InpMaxOppositeShadow)
   {
      result.rejectReason = StringFormat("[层3] 反向影线占比=%0.1f%% > 阈值%0.0f%%（%s方博弈抵抗）",
                                         oppositeShadowRatio * 100,
                                         InpMaxOppositeShadow * 100,
                                         rawDirection > 0 ? "卖" : "买");
      return result;
   }
   result.passedFilters++;

//--- [层4] 危险K线过滤 ---
   if(rangeCandle > atr[1] * InpMaxCandleATR)
   {
      result.rejectReason = StringFormat("[层4] ⚠️ 危险K线！振幅=%0.1f > %0.1f×ATR(%0.1f) → 订单失衡风险，拒绝追高/追低",
                                         rangeCandle, InpMaxCandleATR, atr[1]);
      return result;
   }
   result.passedFilters++;

//--- [层5] 点火与跟随确认（本层仅标记，实际跟随检查在ProcessPendingSignal中） ---
   // 如果启用了跟随确认，信号标记为pending而非立即执行
   // 此处理在主循环中进行
   result.passedFilters++;

//--- 多周期分形确认 ---
   if(InpUseMultiTF)
   {
      if(!ConfirmLowerTimeframe(rawDirection))
      {
         result.rejectReason = "[分形] 下级周期("
                               + EnumToString((ENUM_TIMEFRAMES)InpLowerTF)
                               + ")未确认，分形结构不完整";
         return result;
      }
   }

//--- 信号综合评分 ---
   result.score = CalculateSignalScore(bodyRatio, oppositeShadowRatio,
                                        rangeCandle / atr[1], rawDirection);
   result.valid = true;
   result.direction = rawDirection;

   return result;
}

//+------------------------------------------------------------------+
//| ZigZag BoS检测: 看涨结构突破（下跌→上涨反转）                        |
//|                                                                  |
//| 逻辑: 最近N个ZigZag高点呈下降趋势（Lower Highs）                      |
//|       当前价格突破最近一个ZigZag高点 → 空头结构破坏 → 多头反转        |
//+------------------------------------------------------------------+
bool DetectBullishBoS_H4()
{
   ZigZagPivot pivots[];

   // 优先使用ZigZag指标，失败则回退到价格动作检测
   bool hasPivots = false;
   if(g_zigzagHandle_H4 != INVALID_HANDLE)
      hasPivots = GetZigZagPivots(g_zigzagHandle_H4, PERIOD_H4, InpBoSLookback * 2, pivots);

   if(!hasPivots)
      hasPivots = GetSwingPivotsFromPrice(PERIOD_H4, InpBoSLookback * 2, InpZigZagDepth, pivots);

   if(!hasPivots) return false;

   int count = ArraySize(pivots);
   if(count < 3) return false;  // 至少需要3个转折点

//--- 收集最近3个高点，检查是否呈下降趋势（Lower Highs） ---
   double highs[];
   ArrayResize(highs, 0);

   for(int i = 0; i < count && ArraySize(highs) < 3; i++)
   {
      if(pivots[i].isHigh)
      {
         int sz = ArraySize(highs);
         ArrayResize(highs, sz + 1);
         highs[sz] = pivots[i].price;
      }
   }

   if(ArraySize(highs) < 2) return false;

//--- 检查是否形成下降趋势（Lower Highs） ---
   bool lowerHighs = true;
   for(int i = 0; i < ArraySize(highs) - 1; i++)
   {
      if(highs[i] >= highs[i+1])  // 最新的高点应该比前一个低
      {
         lowerHighs = false;
         break;
      }
   }
   if(!lowerHighs) return false;

//--- 检查当前价格是否突破最近高点（BoS） ---
   double currentClose = iClose(_Symbol, PERIOD_H4, 1);  // 上一根已收盘K线
   double recentHigh = highs[0];  // 最近的高点

   return (currentClose > recentHigh);
}

//+------------------------------------------------------------------+
//| ZigZag BoS检测: 看跌结构突破（上涨→下跌反转）                        |
//+------------------------------------------------------------------+
bool DetectBearishBoS_H4()
{
   ZigZagPivot pivots[];

   bool hasPivots = false;
   if(g_zigzagHandle_H4 != INVALID_HANDLE)
      hasPivots = GetZigZagPivots(g_zigzagHandle_H4, PERIOD_H4, InpBoSLookback * 2, pivots);

   if(!hasPivots)
      hasPivots = GetSwingPivotsFromPrice(PERIOD_H4, InpBoSLookback * 2, InpZigZagDepth, pivots);

   if(!hasPivots) return false;

   int count = ArraySize(pivots);
   if(count < 3) return false;

//--- 收集最近3个低点，检查是否呈上升趋势（Higher Lows） ---
   double lows[];
   ArrayResize(lows, 0);

   for(int i = 0; i < count && ArraySize(lows) < 3; i++)
   {
      if(!pivots[i].isHigh)
      {
         int sz = ArraySize(lows);
         ArrayResize(lows, sz + 1);
         lows[sz] = pivots[i].price;
      }
   }

   if(ArraySize(lows) < 2) return false;

//--- 检查是否形成上升趋势（Higher Lows） ---
   bool higherLows = true;
   for(int i = 0; i < ArraySize(lows) - 1; i++)
   {
      if(lows[i] <= lows[i+1])  // 最新的低点应该比前一个高
      {
         higherLows = false;
         break;
      }
   }
   if(!higherLows) return false;

//--- 检查当前价格是否跌破最近低点（BoS） ---
   double currentClose = iClose(_Symbol, PERIOD_H4, 1);
   double recentLow = lows[0];  // 最近的低点

   return (currentClose < recentLow);
}

//+------------------------------------------------------------------+
//| 从ZigZag指标提取转折点                                              |
//| 注意: MT5 ZigZag在非转折点填充 EMPTY_VALUE (DBL_MAX)，而非0          |
//+------------------------------------------------------------------+
bool GetZigZagPivots(int zigzagHandle, ENUM_TIMEFRAMES tf,
                      int lookbackBars, ZigZagPivot &pivots[])
{
   ArrayResize(pivots, 0);

   if(zigzagHandle == INVALID_HANDLE)
      return false;

   double zigzagBuf[];
   ArraySetAsSeries(zigzagBuf, true);

   int copied = CopyBuffer(zigzagHandle, 0, 0, lookbackBars + 50, zigzagBuf);
   if(copied <= 0) return false;

   datetime timeBuf[];
   ArraySetAsSeries(timeBuf, true);
   if(CopyTime(_Symbol, tf, 0, lookbackBars + 50, timeBuf) <= 0)
      return false;

//--- 扫描ZigZag值，收集非空转折点 ---
   int pivotCount = 0;
   for(int i = 1; i < copied - 1 && pivotCount < InpBoSLookback * 2; i++)
   {
      // MT5 ZigZag: 非转折点填充 EMPTY_VALUE (≈DBL_MAX)
      if(zigzagBuf[i] == EMPTY_VALUE || zigzagBuf[i] == 0.0)
         continue;

      // 确认这是一个转折点: 前后值应小于当前值
      if(zigzagBuf[i] > zigzagBuf[i-1] && zigzagBuf[i] > zigzagBuf[i+1])
      {
         // 高点
         int sz = ArraySize(pivots);
         ArrayResize(pivots, sz + 1);
         pivots[sz].time   = timeBuf[i];
         pivots[sz].price  = zigzagBuf[i];
         pivots[sz].index  = i;
         pivots[sz].isHigh = true;
         pivotCount++;
      }
      else if(zigzagBuf[i] < zigzagBuf[i-1] && zigzagBuf[i] < zigzagBuf[i+1])
      {
         // 低点
         int sz = ArraySize(pivots);
         ArrayResize(pivots, sz + 1);
         pivots[sz].time   = timeBuf[i];
         pivots[sz].price  = zigzagBuf[i];
         pivots[sz].index  = i;
         pivots[sz].isHigh = false;
         pivotCount++;
      }
   }

   return (ArraySize(pivots) >= 2);
}

//+------------------------------------------------------------------+
//| 备用BoS检测: 基于价格动作的摆动高低点（不依赖ZigZag指标）             |
//|                                                                  |
//| 逻辑: 使用简单的N根K线最高/最低点来识别摆动点                         |
//|       左侧Strength根K线 & 右侧Strength根K线中，当前为极值 → 摆动点    |
//+------------------------------------------------------------------+
bool GetSwingPivotsFromPrice(ENUM_TIMEFRAMES tf, int lookbackBars,
                              int strength, ZigZagPivot &pivots[])
{
   ArrayResize(pivots, 0);

   int totalBars = lookbackBars + strength * 4;
   double high[], low[];
   datetime time[];

   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(time, true);

   if(CopyHigh(_Symbol, tf, 0, totalBars, high) < totalBars) return false;
   if(CopyLow(_Symbol, tf, 0, totalBars, low) < totalBars)   return false;
   if(CopyTime(_Symbol, tf, 0, totalBars, time) < totalBars) return false;

   int pivotCount = 0;
   int maxPivots = InpBoSLookback * 2;

//--- 从旧到新扫描（i从大到小），找到摆动高低点 ---
   for(int i = totalBars - strength - 1; i >= strength && pivotCount < maxPivots; i--)
   {
      // 检查是否是摆动高点
      bool isSwingHigh = true;
      double testHigh = high[i];
      for(int j = 1; j <= strength; j++)
      {
         if(high[i-j] >= testHigh || high[i+j] >= testHigh)
         {
            isSwingHigh = false;
            break;
         }
      }

      if(isSwingHigh)
      {
         int sz = ArraySize(pivots);
         ArrayResize(pivots, sz + 1);
         pivots[sz].time   = time[i];
         pivots[sz].price  = testHigh;
         pivots[sz].index  = i;
         pivots[sz].isHigh = true;
         pivotCount++;
         i -= strength;  // 跳过这个摆动区域
         continue;
      }

      // 检查是否是摆动低点
      bool isSwingLow = true;
      double testLow = low[i];
      for(int j = 1; j <= strength; j++)
      {
         if(low[i-j] <= testLow || low[i+j] <= testLow)
         {
            isSwingLow = false;
            break;
         }
      }

      if(isSwingLow)
      {
         int sz = ArraySize(pivots);
         ArrayResize(pivots, sz + 1);
         pivots[sz].time   = time[i];
         pivots[sz].price  = testLow;
         pivots[sz].index  = i;
         pivots[sz].isHigh = false;
         pivotCount++;
         i -= strength;
      }
   }

   return (ArraySize(pivots) >= 2);
}

//+------------------------------------------------------------------+
//| 多周期分形确认                                                      |
//| H4信号需要在H1（或指定下级周期）找到自同构确认结构                     |
//+------------------------------------------------------------------+
bool ConfirmLowerTimeframe(int direction)
{
   if(!InpUseMultiTF) return true;

   bool confirmed = true;

//--- 确认1: 下级周期MACD方向一致 ---
   if(InpRequireLowerMACD && g_macdHandle_Lower != INVALID_HANDLE)
   {
      double lowerMACDMain[], lowerMACDSignal[];
      ArraySetAsSeries(lowerMACDMain, true);
      ArraySetAsSeries(lowerMACDSignal, true);

      if(CopyBuffer(g_macdHandle_Lower, 0, 0, 3, lowerMACDMain) >= 3 &&
         CopyBuffer(g_macdHandle_Lower, 1, 0, 3, lowerMACDSignal) >= 3)
      {
         double lowerHist = lowerMACDMain[1] - lowerMACDSignal[1];

         if(direction > 0 && lowerHist <= 0)  // H4做多但H1 MACD≤0
         {
            if(InpDebugMode)
               Print("  [分形] H1 MACD(", DoubleToString(lowerHist, 6),
                     ") 不支持做多方向");
            confirmed = false;
         }
         else if(direction < 0 && lowerHist >= 0)  // H4做空但H1 MACD≥0
         {
            if(InpDebugMode)
               Print("  [分形] H1 MACD(", DoubleToString(lowerHist, 6),
                     ") 不支持做空方向");
            confirmed = false;
         }
      }
   }

//--- 确认2: 下级周期BoS结构（可选，默认关闭） ---
   if(InpRequireLowerBoS && g_zigzagHandle_Lower != INVALID_HANDLE && confirmed)
   {
      if(direction > 0)
         confirmed = DetectBullishBoS_Lower();
      else
         confirmed = DetectBearishBoS_Lower();
   }

   return confirmed;
}

//+------------------------------------------------------------------+
//| 下级周期看涨BoS检测                                                 |
//+------------------------------------------------------------------+
bool DetectBullishBoS_Lower()
{
   ZigZagPivot pivots[];

   bool hasPivots = false;
   if(g_zigzagHandle_Lower != INVALID_HANDLE)
      hasPivots = GetZigZagPivots(g_zigzagHandle_Lower, InpLowerTF, InpBoSLookback * 2, pivots);

   if(!hasPivots)
      hasPivots = GetSwingPivotsFromPrice(InpLowerTF, InpBoSLookback * 2, InpZigZagDepth, pivots);

   if(!hasPivots) return false;

   int count = ArraySize(pivots);
   if(count < 3) return false;

   double highs[];
   ArrayResize(highs, 0);
   for(int i = 0; i < count && ArraySize(highs) < 3; i++)
   {
      if(pivots[i].isHigh)
      {
         int sz = ArraySize(highs);
         ArrayResize(highs, sz + 1);
         highs[sz] = pivots[i].price;
      }
   }
   if(ArraySize(highs) < 2) return false;

   bool lowerHighs = true;
   for(int i = 0; i < ArraySize(highs) - 1; i++)
   {
      if(highs[i] >= highs[i+1]) { lowerHighs = false; break; }
   }
   if(!lowerHighs) return false;

   double close = iClose(_Symbol, InpLowerTF, 1);
   return (close > highs[0]);
}

//+------------------------------------------------------------------+
//| 下级周期看跌BoS检测                                                 |
//+------------------------------------------------------------------+
bool DetectBearishBoS_Lower()
{
   ZigZagPivot pivots[];

   bool hasPivots = false;
   if(g_zigzagHandle_Lower != INVALID_HANDLE)
      hasPivots = GetZigZagPivots(g_zigzagHandle_Lower, InpLowerTF, InpBoSLookback * 2, pivots);

   if(!hasPivots)
      hasPivots = GetSwingPivotsFromPrice(InpLowerTF, InpBoSLookback * 2, InpZigZagDepth, pivots);

   if(!hasPivots) return false;

   int count = ArraySize(pivots);
   if(count < 3) return false;

   double lows[];
   ArrayResize(lows, 0);
   for(int i = 0; i < count && ArraySize(lows) < 3; i++)
   {
      if(!pivots[i].isHigh)
      {
         int sz = ArraySize(lows);
         ArrayResize(lows, sz + 1);
         lows[sz] = pivots[i].price;
      }
   }
   if(ArraySize(lows) < 2) return false;

   bool higherLows = true;
   for(int i = 0; i < ArraySize(lows) - 1; i++)
   {
      if(lows[i] <= lows[i+1]) { higherLows = false; break; }
   }
   if(!higherLows) return false;

   double close = iClose(_Symbol, InpLowerTF, 1);
   return (close < lows[0]);
}

//+------------------------------------------------------------------+
//| 处理待确认信号（点火与跟随窗口）                                      |
//| Z-Wei 理论: 点火发出后，观察是否有"跟随者"形成共识                    |
//+------------------------------------------------------------------+
void ProcessPendingSignal()
{
   g_pendingBars++;

//--- 超时：等待超过最大K线数，放弃信号 ---
   if(g_pendingBars > g_pendingMaxBars)
   {
      if(InpDebugMode)
         Print("⏰ [跟随] 等待超时(", g_pendingBars, "根H4 K线)，放弃待确认信号");

      g_pendingLong  = false;
      g_pendingShort = false;
      g_pendingBars  = 0;
      return;
   }

//--- 获取确认所需的后续K线数据 ---
   double close[], high[], low[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   int barsNeeded = InpFollowThroughBars + 2;
   if(CopyClose(_Symbol, PERIOD_H4, 0, barsNeeded, close) < barsNeeded) return;
   if(CopyHigh(_Symbol, PERIOD_H4, 0, barsNeeded, high) < barsNeeded) return;
   if(CopyLow(_Symbol, PERIOD_H4, 0, barsNeeded, low) < barsNeeded) return;

   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_atrHandle_H4, 0, 0, 2, atr) < 2) return;

//--- 对于做多信号 ---
   if(g_pendingLong)
   {
      // 跟随确认: 后续K线至少有一根收盘价突破点火K线高点
      double ignitionHigh = high[g_pendingBars];  // 点火K线高点

      bool followThrough = false;
      for(int i = 0; i < g_pendingBars; i++)
      {
         if(close[i] > ignitionHigh)
         {
            followThrough = true;
            break;
         }
      }

      if(followThrough)
      {
         if(InpDebugMode)
            Print("✅ [跟随] 做多共识确认！在第", g_pendingBars, "根K线后确认跟随");

         g_pendingLong = false;
         g_pendingBars = 0;
         ExecuteEntry(1);
      }
      else if(g_pendingBars >= g_pendingMaxBars)
      {
         // 最后检查: 即使没有创新高，如果价格维持在点火K线实体50%以上，也算弱确认
         double ignitionClose = close[g_pendingBars];
         double ignitionOpen  = iOpen(_Symbol, PERIOD_H4, g_pendingBars);
         double midPoint = (ignitionClose + ignitionOpen) / 2.0;

         if(close[0] > midPoint)
         {
            if(InpDebugMode)
               Print("⚠️ [跟随] 弱确认：价格维持在点火K线中点上方，谨慎入场");

            g_pendingLong = false;
            g_pendingBars = 0;
            ExecuteEntry(1);
         }
         else
         {
            if(InpDebugMode)
               Print("❌ [跟随] 做多共识失败：点火未被跟随，放弃信号");

            g_pendingLong = false;
            g_pendingBars = 0;
         }
      }
   }

//--- 对于做空信号 ---
   if(g_pendingShort)
   {
      double ignitionLow = low[g_pendingBars];  // 点火K线低点

      bool followThrough = false;
      for(int i = 0; i < g_pendingBars; i++)
      {
         if(close[i] < ignitionLow)
         {
            followThrough = true;
            break;
         }
      }

      if(followThrough)
      {
         if(InpDebugMode)
            Print("✅ [跟随] 做空共识确认！在第", g_pendingBars, "根K线后确认跟随");

         g_pendingShort = false;
         g_pendingBars = 0;
         ExecuteEntry(-1);
      }
      else if(g_pendingBars >= g_pendingMaxBars)
      {
         double ignitionClose = close[g_pendingBars];
         double ignitionOpen  = iOpen(_Symbol, PERIOD_H4, g_pendingBars);
         double midPoint = (ignitionClose + ignitionOpen) / 2.0;

         if(close[0] < midPoint)
         {
            if(InpDebugMode)
               Print("⚠️ [跟随] 弱确认：价格维持在点火K线中点下方，谨慎入场");

            g_pendingShort = false;
            g_pendingBars = 0;
            ExecuteEntry(-1);
         }
         else
         {
            if(InpDebugMode)
               Print("❌ [跟随] 做空共识失败：点火未被跟随，放弃信号");

            g_pendingShort = false;
            g_pendingBars = 0;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 执行入场                                                           |
//+------------------------------------------------------------------+
void ExecuteEntry(int direction)
{
//--- 防重复入场检查 ---
   datetime currentBarTime = iTime(_Symbol, PERIOD_H4, 0);

   if(direction > 0 && g_lastLongEntryBar == currentBarTime)
   {
      if(InpDebugMode) Print("⚠️ 同根K线已入场做多，跳过重复信号");
      return;
   }
   if(direction < 0 && g_lastShortEntryBar == currentBarTime)
   {
      if(InpDebugMode) Print("⚠️ 同根K线已入场做空，跳过重复信号");
      return;
   }

//--- 检查持仓数量 ---
   int posCount = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
            PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
         {
            if(direction > 0 && PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
               posCount++;
            if(direction < 0 && PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
               posCount++;
         }
      }
   }

   if(posCount >= InpMaxPositions)
   {
      if(InpDebugMode) Print("⚠️ 已达最大持仓数(", InpMaxPositions, ")，跳过信号");
      return;
   }

//--- 计算手数 ---
   double lotSize = CalculateLotSize(direction);
   if(lotSize <= 0)
   {
      Print("❌ 手数计算异常: ", lotSize);
      return;
   }

//--- 获取价格 ---
   double price, sl, tp;
   double atr[];
   ArraySetAsSeries(atr, true);
   CopyBuffer(g_atrHandle_H4, 0, 0, 2, atr);

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(direction > 0)  // 做多
   {
      price = ask;
      sl = price - atr[0] * InpATRMultiplier;
      tp = (InpTakeProfitATR > 0) ? price + atr[0] * InpTakeProfitATR : 0;

      // 规范化止损（至少距离当前价20点）
      double minSL = price - 20 * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      if(sl > minSL) sl = minSL;
   }
   else  // 做空
   {
      price = bid;
      sl = price + atr[0] * InpATRMultiplier;
      tp = (InpTakeProfitATR > 0) ? price - atr[0] * InpTakeProfitATR : 0;

      double minSL = price + 20 * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      if(sl < minSL) sl = minSL;
   }

//--- 发送订单 ---
   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = _Symbol;
   request.volume    = lotSize;
   request.type      = (direction > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price     = price;
   request.sl        = NormalizeDouble(sl, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS));
   request.tp        = (tp > 0) ? NormalizeDouble(tp, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)) : 0;
   request.deviation = 30;
   request.magic     = InpMagicNumber;
   request.comment   = InpComment + "|" + (direction > 0 ? "L" : "S");

   if(!OrderSend(request, result))
   {
      Print("❌ 入场失败！错误码: ", result.retcode,
            " | 方向: ", direction > 0 ? "做多" : "做空",
            " | 手数: ", lotSize,
            " | 价格: ", price,
            " | 止损: ", request.sl);
      return;
   }

//--- 记录入场时间 ---
   if(direction > 0)
      g_lastLongEntryBar = currentBarTime;
   else
      g_lastShortEntryBar = currentBarTime;

   Print("✅ 入场成功！");
   Print("   方向: ", direction > 0 ? "做多 📈" : "做空 📉");
   Print("   手数: ", DoubleToString(lotSize, 2));
   Print("   入场价: ", price);
   Print("   止损: ", DoubleToString(request.sl, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)));
   if(tp > 0)
      Print("   止盈: ", DoubleToString(request.tp, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)));
   Print("   风险: ", DoubleToString(InpRiskPercent, 2), "% 账户");
   Print("══════════════════════");
}

//+------------------------------------------------------------------+
//| 计算手数（基于固定百分比风险）                                        |
//+------------------------------------------------------------------+
double CalculateLotSize(int direction)
{
   double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = accountBalance * InpRiskPercent / 100.0;

   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_atrHandle_H4, 0, 0, 1, atr) < 1)
      return 0;

   double stopDistance = atr[0] * InpATRMultiplier;
   if(stopDistance <= 0) return 0;

   double pointValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double pointSize  = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double tickSize   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   if(pointSize <= 0 || tickSize <= 0) return 0;

   // 每手每点的价值
   double valuePerPoint = pointValue * (pointSize / tickSize);

   if(valuePerPoint <= 0) return 0;

   // 手数 = 风险金额 / (止损点数 × 每点价值)
   double lotSize = riskAmount / (stopDistance / pointSize * valuePerPoint);

   // 规范化手数
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double lotMin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotMax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   lotSize = MathMax(lotMin, MathMin(lotMax, lotSize));

   return NormalizeDouble(lotSize, 2);
}

//+------------------------------------------------------------------+
//| 移动止盈管理                                                        |
//| Z-Wei 理论: 动态保护本金，拒绝死扛                                    |
//+------------------------------------------------------------------+
void ManageTrailingStop()
{
   datetime currentBar_H4 = iTime(_Symbol, PERIOD_H4, 0);
   if(currentBar_H4 == g_lastTrailBarTime)
      return;  // 同一根H4 K线已处理
   g_lastTrailBarTime = currentBar_H4;

   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_atrHandle_H4, 0, 0, 1, atr) < 1) return;

   double trailDistance = atr[0] * InpTrailingStart;
   double trailStep     = atr[0] * InpTrailingStep;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;

      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;

      double currentSL = PositionGetDouble(POSITION_SL);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      long   posType   = PositionGetInteger(POSITION_TYPE);

      if(posType == POSITION_TYPE_BUY)
      {
         double profitDistance = bid - openPrice;

         // 检查是否达到移动止盈启动条件
         if(profitDistance >= trailDistance)
         {
            double newSL = bid - trailDistance;

            // 加上步长防止过度移动
            if(currentSL > 0)
               newSL = MathMax(newSL, currentSL + trailStep);

            newSL = NormalizeDouble(newSL, digits);

            if(newSL > currentSL && newSL < bid)
            {
               if(PositionModify(ticket, newSL, PositionGetDouble(POSITION_TP)))
               {
                  if(InpDebugMode)
                     Print("🛡️ [移动止盈] 做多 | 新止损: ",
                           DoubleToString(newSL, digits),
                           " | 浮盈: ", DoubleToString(profitDistance / atr[0], 1), "×ATR");
               }
            }
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         double profitDistance = openPrice - ask;

         if(profitDistance >= trailDistance)
         {
            double newSL = ask + trailDistance;

            if(currentSL > 0)
               newSL = MathMin(newSL, currentSL - trailStep);

            newSL = NormalizeDouble(newSL, digits);

            if((newSL < currentSL || currentSL == 0) && newSL > ask)
            {
               if(PositionModify(ticket, newSL, PositionGetDouble(POSITION_TP)))
               {
                  if(InpDebugMode)
                     Print("🛡️ [移动止盈] 做空 | 新止损: ",
                           DoubleToString(newSL, digits),
                           " | 浮盈: ", DoubleToString(profitDistance / atr[0], 1), "×ATR");
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 点差检查                                                           |
//+------------------------------------------------------------------+
bool CheckSpread()
{
   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                  - SymbolInfoDouble(_Symbol, SYMBOL_BID))
                  / SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   if(spread > InpMaxSpread)
   {
      if(InpDebugMode && g_lastBarTime_H4 != iTime(_Symbol, PERIOD_H4, 0))
         Print("⚠️ 点差过大: ", DoubleToString(spread, 0), " > ", InpMaxSpread);
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| 时间过滤                                                           |
//+------------------------------------------------------------------+
bool CheckTimeFilter()
{
   if(!InpUseTimeFilter) return true;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   int currentHour = dt.hour;
   if(InpStartHour <= InpEndHour)
   {
      return (currentHour >= InpStartHour && currentHour < InpEndHour);
   }
   else
   {
      // 跨午夜情况（如 StartHour=20, EndHour=4）
      return (currentHour >= InpStartHour || currentHour < InpEndHour);
   }
}

//+------------------------------------------------------------------+
//| 波动率过滤                                                         |
//+------------------------------------------------------------------+
bool CheckVolatility()
{
   if(!InpUseATRFilter || g_atrFilterHandle_H4 == INVALID_HANDLE)
      return true;

   double atrCurrent[], atrLong[];
   ArraySetAsSeries(atrCurrent, true);
   ArraySetAsSeries(atrLong, true);

   if(CopyBuffer(g_atrHandle_H4, 0, 0, 1, atrCurrent) < 1) return true;
   if(CopyBuffer(g_atrFilterHandle_H4, 0, 0, 1, atrLong) < 1) return true;

   if(atrLong[0] <= 0) return true;

   double ratio = atrCurrent[0] / atrLong[0];
   if(ratio < InpATRMinRatio)
   {
      if(InpDebugMode)
         Print("🔸 波动率过低: ", DoubleToString(ratio, 2), " < ", InpATRMinRatio);
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| 信号评分                                                           |
//+------------------------------------------------------------------+
double CalculateSignalScore(double bodyRatio, double oppositeShadow,
                             double candleATRRatio, int direction)
{
   double score = 50.0;  // 基础分

//--- 实体占比贡献 (±15分) ---
   score += (bodyRatio - 0.5) * 30;  // 0.5→0分, 1.0→+15分

//--- 反向影线贡献 (±15分) ---
   score += (InpMaxOppositeShadow - oppositeShadow) * 75;  // 影线越小越好

//--- K线相对大小贡献 (±10分) ---
   if(candleATRRatio < 1.5)
      score += 10;     // 适中的K线最好
   else if(candleATRRatio < 2.0)
      score += 5;      // 偏大
   else
      score -= 5;      // 接近危险线

//--- MACD柱状图强度贡献 (±10分) ---
   double macdMain[], macdSignal[];
   ArraySetAsSeries(macdMain, true);
   ArraySetAsSeries(macdSignal, true);

   if(CopyBuffer(g_macdHandle_H4, 0, 0, 2, macdMain) >= 2 &&
      CopyBuffer(g_macdHandle_H4, 1, 0, 2, macdSignal) >= 2)
   {
      double histStrength = MathAbs(macdMain[1] - macdSignal[1]);
      // 归一化到0-10分
      double histScore = MathMin(10.0, histStrength * 10000);
      score += histScore * (double)direction;  // 方向一致加分
   }

   return MathMax(0.0, MathMin(100.0, score));
}

//+------------------------------------------------------------------+
//| 图表注释                                                           |
//+------------------------------------------------------------------+
void UpdateComment()
{
   string info = "";
   info += "━━━━━━ ZWeiGoldEA v1.0 ━━━━━━\n";
   info += "品种: " + _Symbol + " | 主周期: H4\n";
   info += "下级周期: " + EnumToString((ENUM_TIMEFRAMES)InpLowerTF) + "\n";
   info += "时间: " + TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES) + "\n";
   info += "━━━━━━━━━━━━━━━━━━━━━━━\n";

   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_atrHandle_H4, 0, 0, 1, atr) >= 1)
      info += "ATR(H4): " + DoubleToString(atr[0], 1) + "\n";

   // 显示当前持仓
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;

      double openP  = PositionGetDouble(POSITION_PRICE_OPEN);
      double currP  = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
                      ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                      : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double profit = PositionGetDouble(POSITION_PROFIT);
      double pips   = (currP - openP) / SymbolInfoDouble(_Symbol, SYMBOL_POINT);

      info += "━━━━━━━━━━━━━━━━━━━━━━━\n";
      info += StringFormat("持仓 #%I64u: %s\n", ticket,
                           PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "做多📈" : "做空📉");
      info += StringFormat("入场: %s | 当前: %s\n",
                           DoubleToString(openP, 2), DoubleToString(currP, 2));
      info += StringFormat("浮盈: %s | 点数: %s\n",
                           DoubleToString(profit, 2), DoubleToString(pips, 1));
   }

   info += "━━━━━━━━━━━━━━━━━━━━━━━\n";
   info += "待确认: " + (g_pendingLong ? "做多⏳" : g_pendingShort ? "做空⏳" : "无");

   Comment(info);
}

//+------------------------------------------------------------------+
//| End of ZWeiGoldEA_v1.0.mq5                                        |
//|                                                                  |
//| "我去适应市场，只抓我能理解的那部分行情。"                           |
//|                                       —— Z-Wei 交易哲学            |
//+------------------------------------------------------------------+
