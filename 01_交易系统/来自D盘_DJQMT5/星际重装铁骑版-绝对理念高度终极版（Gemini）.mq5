//+------------------------------------------------------------------+
//|                                     Guardian Earth V20.8.13.4.mq5|
//|                                  Copyright 2026, AI Commander    |
//|                 "星际重装铁骑版 - 绝对零度终极版 (封神终极量产版)"  |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V20.8.13.4_AbsoluteZero"
#property version   "20.81"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 🛡️ 核心风控与时间 ---
input group "=== 核心风控与时间 ==="
input double InpRiskPercent    = 2.5;     // 💥 L1 初始火力风险(%)
input int    InpMaxSpread      = 50;      // 🛑 最大允许点差 (单位:点 / Points)
input double InpDailyMaxLoss   = 5.0;     // 🥶 极寒单日最大熔断回撤(%)
input int    InpStartHour      = 15;
input int    InpEndHour        = 23;
input bool   InpFridayExit     = true;
input ulong  InpMagicNumber    = 208500;
input string InpMagicComment   = "AbsZero";// 📝 订单战区专属铭牌
input int    InpMaxLevels      = 4;

input group "=== 资金与保证金安全 ==="
input double InpMinBalanceToTrade = 100.0;
input int    InpMarginFailCooldownMinutes = 60;

//--- 🐺 狼群战术 (递减火力) ---
input group "=== 狼群追击战术 ==="
input double InpLevelMultiplier= 0.6;     // 📉 加仓火力衰减系数
input double InpLevelUpPct     = 0.3;     // 📏 加仓间距触发线(%)
input int    InpBailoutLevel   = 3;
input double InpBailoutPct     = 0.2;

//--- 💰 动态装甲 ---
input group "=== 动态保本装甲 ==="
input double InpHWM_Activate   = 3.0;
input double InpHWM_Retract    = 1.5;
input bool   InpStrictPartialLock = false; // 🔓 严格防重复锁(False=对切后可继续追击)

//--- 📡 信号灵敏度 ---
input group "=== 进场雷达调优 ==="
input double InpVolMultiplier  = 0.8;
input double InpPullbackPct    = 0.0;
input bool   InpUseMacroFilter = true;

//--- 🎯 事前风控：波动率与事件过滤器 ---
input group "=== 事前风控：波动率调整与事件过滤 ==="
input bool   InpUseVolatilityFilter = true;   // 📊 启用波动率层数调整
input double InpATRMultiplier_Max   = 2.0;    // 🔒 ATR倍数上限（超过则减少层数）
input bool   InpUseEventFilter = true;         // 📅 启用事件过滤器
input int    InpEventFilterHours = 2;          // ⏰ 高风险事件前后过滤小时数
input bool   InpUseADXFilter = true;           // 📈 启用ADX趋势强度过滤
input double InpMinADX = 20.0;                 // 🔻 最低ADX阈值（低于则谨慎入场）

//--- 🚀 加速响应：快速入场模式 ---
input group "=== 加速响应：快速入场模式 ==="
input bool   InpUseFastEntry = true;            // ⚡ 启用快速入场模式
input double InpFastEntryADXThreshold = 30.0;   // 🔥 触发快速入场的ADX阈值（趋势极强时放宽过滤）
input double InpFastEntryMargin = 0.15;        // 📉 快速入场时EMA14回踩容错空间(%)
input bool   InpUseProfitTrail = true;          // 🛡️ 启用移动止损保护
input double InpTrailActivatePct = 1.0;         // 📍 移动止损激活利润阈值(%)
input double InpTrailDistancePct = 0.5;         // 📏 移动止损保护距离(%)

//--- 📊 运维监控增强 ---
input group "=== 运维监控：定期报告与指标快照 ==="
input bool   InpUsePeriodicReport = true;       // 📋 启用定期持仓报告
input int    InpReportIntervalMinutes = 30;      // ⏰ 定期报告间隔（分钟）

//--- 📡 Telegram推送与账户 ---
input group "=== Telegram 与 账户设定 ==="
enum ENUM_ACC_TYPE { ACC_AUTO, ACC_CENT, ACC_USD };
input ENUM_ACC_TYPE InpAccountType = ACC_AUTO; // 🏦 账户资金类型(推荐AUTO自动侦测)
input string InpTelegramToken  = "";
input string InpTelegramChatID = "";

//--- 全局组件 ---
CTrade         trade;
CPositionInfo  posInfo;
CSymbolInfo    symInfo;
CAccountInfo   accInfo;

int            h_ema14, h_ema21, h_ema60, h_ema576, h_macd, h_atr, h_vol, h_adx;
double         Dyn_SL_L, Dyn_SL_S;
double         DailyStartBalance = 0.0;
double         HighestProfitPct  = 0.0;
bool           DailyLossTriggered= false;
bool           hasPartialThisWave= false;
datetime       lastBarTime       = 0;
int            lastDayOfYear     = -1;
string         CurrencyUnit      = "美分";
string         CurrencySymbol    = "";

//--- 📡 全局高速雷达缓存区 ---
double g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[];
double g_macd_main[], g_macd_sig[];
double g_vol[];
double g_adx[];

//--- 📊 波动率动态层数缓存 ---
int    g_dynamicMaxLevels = 4;
double g_currentAtr = 0.0;
datetime g_lastEventCheck = 0;
bool   g_isHighRiskWindow = false;

//--- 🛡️ 移动止损追踪缓存 ---
double g_trailingStopLevel = 0.0;
bool   g_isTrailActive = false;

//--- 📋 运维报告缓存 ---
datetime g_lastPeriodicReport = 0;

datetime g_marginFailUntil = 0;

//+------------------------------------------------------------------+
//| 🛠️ 核心微米级打磨机：价格标准化，彻底封杀 10014/10016 报错
//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   double tickSize = symInfo.TickSize();
   if(tickSize == 0) return price;
   return MathRound(price / tickSize) * tickSize;
}

int VolumeDigitsFromStep(double step)
{
   if(step <= 0) return 0;
   double scaled = step;
   for(int digits=0; digits<=8; digits++)
   {
      double rounded = MathRound(scaled);
      if(MathAbs(scaled - rounded) < 1e-8) return digits;
      scaled *= 10.0;
   }
   return 8;
}

//+------------------------------------------------------------------+
int OnInit()
{
   symInfo.Name(_Symbol);
   symInfo.Refresh();
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   AutoCalibrate();

   // 🤖 智能账户侦测 + 日志输出
   if(InpAccountType == ACC_AUTO)
   {
      string accCur = AccountInfoString(ACCOUNT_CURRENCY);
      if(StringFind(accCur, "USC") >= 0 || StringFind(accCur, "cent") >= 0 || StringFind(accCur, "Cent") >= 0)
      {
         CurrencyUnit = "美分"; CurrencySymbol = "";
      }
      else
      {
         CurrencyUnit = "美元"; CurrencySymbol = "$";
      }
      Print("🏦 账户类型智能侦测完成 | 当前货币: ", accCur, " | 单位: ", CurrencyUnit);
   }
   else if(InpAccountType == ACC_CENT) { CurrencyUnit = "美分"; CurrencySymbol = ""; }
   else                                { CurrencyUnit = "美元"; CurrencySymbol = "$"; }

   h_ema14 = iMA(_Symbol, PERIOD_M15, 14, 0, MODE_EMA, PRICE_CLOSE);
   h_ema21 = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   h_ema60 = iMA(_Symbol, PERIOD_M15, 60, 0, MODE_EMA, PRICE_CLOSE);
   h_ema576= iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_macd  = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   h_atr   = iATR(_Symbol, PERIOD_M15, 14);
   h_vol   = iVolumes(_Symbol, PERIOD_M15, VOLUME_TICK);
   h_adx   = iADX(_Symbol, PERIOD_M15, 14);

   if(h_ema14==INVALID_HANDLE || h_macd==INVALID_HANDLE || h_atr==INVALID_HANDLE || h_vol==INVALID_HANDLE || h_ema576==INVALID_HANDLE || h_adx==INVALID_HANDLE)
   {
      Print("❌ 雷达初始化失败，请检查历史数据！");
      return(INIT_FAILED);
   }

   ArraySetAsSeries(g_ema14, true); ArraySetAsSeries(g_ema21, true); ArraySetAsSeries(g_ema60, true);
   ArraySetAsSeries(g_ema576, true); ArraySetAsSeries(g_atr, true);
   ArraySetAsSeries(g_macd_main, true); ArraySetAsSeries(g_macd_sig, true);
   ArraySetAsSeries(g_vol, true);
   ArraySetAsSeries(g_adx, true);

   DailyStartBalance = accInfo.Balance();
   HighestProfitPct = 0.0;
   hasPartialThisWave = false;
   g_dynamicMaxLevels = InpMaxLevels;

   MqlDateTime t;
   TimeCurrent(t);
   lastDayOfYear = t.day_of_year;

   string initMsg = "🚀 V20.8.13.4 封神量产版启动 | 初始基数: " + CurrencySymbol + DoubleToString(DailyStartBalance, 2) + " " + CurrencyUnit;
   Print(initMsg);
   SendTelegramMessage(initMsg);

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   string r = "";
   switch(reason)
   {
      case REASON_REMOVE: r = "手动移除"; break;
      case REASON_RECOMPILE: r = "代码重编译"; break;
      case REASON_CHARTCHANGE: r = "图表/周期切换"; break;
      case REASON_CHARTCLOSE: r = "图表关闭"; break;
      case REASON_PARAMETERS: r = "参数修改"; break;
      case REASON_ACCOUNT: r = "账户切换"; break;
      case REASON_TEMPLATE: r = "模板更换"; break;
      case REASON_INITFAILED: r = "初始化失败"; break;
      case REASON_CLOSE: r = "终端强关(VPS失联!)"; break;
      default: r = "未知(" + IntegerToString(reason) + ")";
   }
   Print("⚠️ 退出战场: ", r);
   SendTelegramMessage("⚠️ 警报！机甲已离线！\n战区: " + _Symbol + "\n原因: " + r);
}

void AutoCalibrate()
{
   string s = _Symbol;
   StringToUpper(s); 
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) { Dyn_SL_L = 3.5; Dyn_SL_S = 3.5; }
   else if(StringFind(s,"XAGUSD")>=0 || StringFind(s,"SILVER")>=0) { Dyn_SL_L = 3.5; Dyn_SL_S = 3.5; }
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0) { Dyn_SL_L = 3.0; Dyn_SL_S = 2.0; }
   else if(StringFind(s,"US30")>=0 || StringFind(s,"WS30")>=0 || StringFind(s,"DOW")>=0) { Dyn_SL_L = 3.0; Dyn_SL_S = 2.5; }
   else { Dyn_SL_L = 3.0; Dyn_SL_S = 3.0; }
   
   Print("🛰️ 测向仪已锁定 - 战区: ", s, " | SL: L-", Dyn_SL_L, " S-", Dyn_SL_S, " | 建议Spread上限: ", InpMaxSpread, " 点");
}

bool UpdateIndicators()
{
   // 🔍 检查句柄有效性
   if(h_ema14 == INVALID_HANDLE || h_ema21 == INVALID_HANDLE || h_ema60 == INVALID_HANDLE || 
      h_atr == INVALID_HANDLE || h_vol == INVALID_HANDLE || h_macd == INVALID_HANDLE || h_adx == INVALID_HANDLE) return false;

   if(CopyBuffer(h_ema14, 0, 0, 4, g_ema14) < 4) return false;
   if(CopyBuffer(h_ema21, 0, 0, 4, g_ema21) < 4) return false;
   if(CopyBuffer(h_ema60, 0, 0, 4, g_ema60) < 4) return false;
   if(CopyBuffer(h_atr, 0, 0, 3, g_atr) < 3) return false;
   if(CopyBuffer(h_vol, 0, 0, 22, g_vol) < 22) return false;
   if(CopyBuffer(h_macd, 0, 0, 2, g_macd_main) < 2) return false;
   if(CopyBuffer(h_macd, 1, 0, 2, g_macd_sig) < 2) return false;
   if(CopyBuffer(h_adx, 0, 0, 2, g_adx) < 2) return false;
   
   if(InpUseMacroFilter) 
   { 
      if(h_ema576 == INVALID_HANDLE || CopyBuffer(h_ema576, 0, 0, 2, g_ema576) < 2) return false; 
   }
   
   g_currentAtr = g_atr[1];
   return true;
}

//+------------------------------------------------------------------+
void OnTick()
{
   // 🛡️ 核心环境检查：如果交易未被允许，直接跳过所有逻辑
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED)) return;

   symInfo.RefreshRates();

   if(BarsCalculated(h_ema14) < 60 || BarsCalculated(h_macd) < 26 || BarsCalculated(h_vol) < 22) return;
   if(InpUseMacroFilter && BarsCalculated(h_ema576) < 576) return;

   static bool isFirstTick = true;
   bool isNewBarFlag = IsNewBar();
   bool shouldRunBarLogic = (isFirstTick || isNewBarFlag);
   
   if(shouldRunBarLogic)
   {
      if(!UpdateIndicators())
      {
         lastBarTime = 0;
         return;
      }
   }
   
   MqlDateTime timeInfo;
   TimeCurrent(timeInfo);
   
   if(timeInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance();
      DailyLossTriggered = false;
      HighestProfitPct = 0.0;
      hasPartialThisWave = false;
      g_marginFailUntil = 0;
      lastDayOfYear = timeInfo.day_of_year;
      Print("📅 新的一天开始了。重置每日基准。");
   }
   
   static int lastLevelCalcMin = -1;
   if(timeInfo.min != lastLevelCalcMin)
   {
      g_dynamicMaxLevels = CalculateDynamicMaxLevels();
      lastLevelCalcMin = timeInfo.min;
   }

   if(DailyLossTriggered) return;
   
   bool isHighRiskNow = IsHighRiskWindow(timeInfo);
   
   int total_positions = 0;
   int buy_count = 0;
   int sell_count = 0;
   double total_profit = 0.0;
   double oldest_sl = 0.0;
   datetime oldest_time = 0; 
   int current_type = -1;
   
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            total_positions++;
            double pos_p = posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
            total_profit += pos_p;
            
            if(posInfo.PositionType() == POSITION_TYPE_BUY) buy_count++;
            if(posInfo.PositionType() == POSITION_TYPE_SELL) sell_count++;
            
            if(oldest_time == 0 || posInfo.Time() < oldest_time)
            {
               oldest_time = posInfo.Time();
               oldest_sl = posInfo.StopLoss();
            }
         }
      }
   }
   
   if(total_positions == 0)
   {
      HighestProfitPct = 0.0;
      hasPartialThisWave = false; 
      if(isHighRiskNow) 
      {
         if(!g_isHighRiskWindow)
         {
            Print("⚠️ 高风险事件窗口，暂停新单。");
            g_isHighRiskWindow = true;
         }
         return;
      }
      g_isHighRiskWindow = false;
   }
   else
   {
      if(isHighRiskNow && !g_isHighRiskWindow)
      {
         Print("⚠️ 进入高风险事件窗口，收紧防线。");
         g_isHighRiskWindow = true;
      }
      else if(!isHighRiskNow)
      {
         g_isHighRiskWindow = false;
      }
      
      if(buy_count > 0 && sell_count == 0) current_type = POSITION_TYPE_BUY;
      else if(sell_count > 0 && buy_count == 0) current_type = POSITION_TYPE_SELL;
   }

   double current_equity = accInfo.Equity();
   double current_profit_pct = (total_positions > 0) ? ((total_profit / accInfo.Balance()) * 100.0) : 0.0;

   if(InpFridayExit && timeInfo.day_of_week == 5 && timeInfo.hour >= 22)
   {
      if(total_positions > 0)
      {
         double bal_before = accInfo.Balance();
         CloseAllPositions();
         ReportFinancials("🚩 周末避险强制撤离！清仓完毕！", bal_before);
      }
      return;
   }

   if((current_equity - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   {
      if(total_positions > 0) 
      {
         double bal_before = accInfo.Balance();
         CloseAllPositions();
         ReportFinancials("💥 极寒熔断触发！强制锁死阵地！", bal_before);
      }
      DailyLossTriggered = true;
      return;
   }

   if(total_positions > 0) ManageDynamicArmor(total_positions, current_profit_pct);

   // 📋 定期持仓报告（每30分钟一次）
   if(InpUsePeriodicReport && total_positions > 0)
   {
      datetime now = TimeCurrent();
      if(now - g_lastPeriodicReport >= InpReportIntervalMinutes * 60)
      {
         SendPeriodicStatusReport(total_positions, current_profit_pct);
         g_lastPeriodicReport = now;
      }
   }

   if(!shouldRunBarLogic) return; 

   datetime now2 = TimeCurrent();
   bool canOpenNewTrades = (accInfo.Balance() >= InpMinBalanceToTrade) && (now2 >= g_marginFailUntil);

   if(total_positions > 0 && current_type != -1)
   {
      double close1 = iClose(_Symbol, PERIOD_M15, 1);
      if((current_type == POSITION_TYPE_BUY && close1 < g_ema60[1]) || 
         (current_type == POSITION_TYPE_SELL && close1 > g_ema60[1]))
      {
         double bal_before = accInfo.Balance();
         CloseAllPositions();
         HighestProfitPct = 0.0;
         ReportFinancials("🚨 趋势破位，机甲紧急撤退！", bal_before);
      }
      else if(canOpenNewTrades && (!hasPartialThisWave || !InpStrictPartialLock) && total_positions < g_dynamicMaxLevels && current_profit_pct >= (InpLevelUpPct * total_positions))
      {
         ExecuteAddPosition(current_type, oldest_sl, total_positions);
      }
   }
   else if(total_positions == 0) 
   {
      if(canOpenNewTrades && timeInfo.hour >= InpStartHour && timeInfo.hour < InpEndHour)
      {
         CheckEntry();
      }
   }
   
   if(isFirstTick) isFirstTick = false; 
}

void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;

   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && profit_pct <= InpBailoutPct)
   {
      double bal_before = accInfo.Balance();
      CloseAllPositions();
      HighestProfitPct = 0.0;
      g_isTrailActive = false;
      g_trailingStopLevel = 0.0;
      ReportFinancials("⚠️ 冲锋受阻，L" + IntegerToString(count) + " 级 Bailout 弹射！", bal_before);
      return;
   }

   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave) 
      {
         double bal_before = accInfo.Balance();
         PartialCloseAndBE();
         HighestProfitPct = 0.0; 
         ReportFinancials("⚔️ 舰队物理对切！锁定胜局！", bal_before);
      }
   }
   
   // 🛡️ 移动止损追踪管理
   if(InpUseProfitTrail)
   {
      ManageTrailingStop(count, profit_pct);
   }
}

//+------------------------------------------------------------------+
//| 🛡️ 移动止损追踪：分批离场 + 移动止损保护                         |
//+------------------------------------------------------------------+
void ManageTrailingStop(int count, double profit_pct)
{
   if(count <= 0) return;
   
   int tradeDir = lastTradeDirection();
   if(tradeDir == -1) return;
   
   double curAsk = symInfo.Ask();
   double curBid = symInfo.Bid();
   
   double activateThreshold = InpTrailActivatePct;
   double trailDistance = InpTrailDistancePct;
   
   if(!g_isTrailActive)
   {
      if(profit_pct >= activateThreshold)
      {
         g_isTrailActive = true;
         double entryAvg = CalculateAverageEntryPrice();
         if(entryAvg > 0)
         {
            double trailDistanceAbs = entryAvg * (trailDistance / 100.0);
            double desiredLevel = (tradeDir == POSITION_TYPE_BUY) ? (curBid - trailDistanceAbs) : (curAsk + trailDistanceAbs);
            g_trailingStopLevel = NormalizePrice(desiredLevel);
            Print("🛡️ 移动止损激活 | 触发利润: ", DoubleToString(profit_pct, 2), "% | 追踪位: ", DoubleToString(g_trailingStopLevel, _Digits));
         }
      }
   }
   else
   {
      double entryAvg = CalculateAverageEntryPrice();
      if(entryAvg > 0)
      {
         double trailDistanceAbs = entryAvg * (trailDistance / 100.0);
         double desiredLevel = (tradeDir == POSITION_TYPE_BUY) ? (curBid - trailDistanceAbs) : (curAsk + trailDistanceAbs);
         double newTrailLevel = NormalizePrice(desiredLevel);
         
         bool shouldUpdate = (tradeDir == POSITION_TYPE_BUY && newTrailLevel > g_trailingStopLevel) ||
                           (tradeDir == POSITION_TYPE_SELL && newTrailLevel < g_trailingStopLevel);
         
         if(shouldUpdate)
         {
            g_trailingStopLevel = newTrailLevel;
         }
         
         bool shouldTrigger = (tradeDir == POSITION_TYPE_BUY && curBid <= g_trailingStopLevel) ||
                            (tradeDir == POSITION_TYPE_SELL && curAsk >= g_trailingStopLevel);
         
         if(shouldTrigger)
         {
            double bal_before = accInfo.Balance();
            CloseAllPositions();
            g_isTrailActive = false;
            g_trailingStopLevel = 0.0;
            ReportFinancials("🛡️ 移动止损保护触发！锁定利润！", bal_before);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 📊 计算平均入场价                                                |
//+------------------------------------------------------------------+
double CalculateAverageEntryPrice()
{
   double totalCost = 0;
   double totalLots = 0;
   
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            totalCost += posInfo.PriceOpen() * posInfo.Volume();
            totalLots += posInfo.Volume();
         }
      }
   }
   
   if(totalLots > 0) return totalCost / totalLots;
   return 0;
}

//+------------------------------------------------------------------+
//| 📊 获取最后交易方向                                              |
//+------------------------------------------------------------------+
int lastTradeDirection()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            return (int)posInfo.PositionType();
         }
      }
   }
   return -1;
}

void PartialCloseAndBE()
{
   double volStep = symInfo.LotsStep(); 
   double minVol = symInfo.LotsMin();
   
   ulong tickets[]; double openPrices[]; long posTypes[];
   double currentVols[]; double currentSLs[]; double currentTPs[]; 
   
   int total = PositionsTotal();
   ArrayResize(tickets, total); ArrayResize(openPrices, total); ArrayResize(posTypes, total);
   ArrayResize(currentVols, total); ArrayResize(currentSLs, total); ArrayResize(currentTPs, total);
   
   int count = 0;
   for(int i=total-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            tickets[count] = posInfo.Ticket(); openPrices[count] = posInfo.PriceOpen();
            posTypes[count] = posInfo.PositionType(); currentVols[count] = posInfo.Volume();
            currentSLs[count] = posInfo.StopLoss(); currentTPs[count] = posInfo.TakeProfit(); 
            count++;
         }
      }
   }
   
   double safeLevel = symInfo.StopsLevel() * symInfo.Point();
   double curAsk = symInfo.Ask();
   double curBid = symInfo.Bid();
   
   for(int j=0; j<count; j++)
   {
      double safeTP = (currentTPs[j] > 0) ? NormalizePrice(currentTPs[j]) : 0;
      double beSL = NormalizePrice(openPrices[j]); 
      
      if(posTypes[j] == POSITION_TYPE_BUY && currentSLs[j] < openPrices[j])
      {
         if(curBid > openPrices[j] + safeLevel) {
            if(!trade.PositionModify(tickets[j], beSL, safeTP))
               Print("❌ BE 失败: ", trade.ResultRetcodeDescription());
         }
      }
      else if(posTypes[j] == POSITION_TYPE_SELL && currentSLs[j] > openPrices[j])
      {
         if(curAsk < openPrices[j] - safeLevel) {
            if(!trade.PositionModify(tickets[j], beSL, safeTP))
               Print("❌ BE 失败: ", trade.ResultRetcodeDescription());
         }
      }
         
      double closeVol = MathFloor((currentVols[j] / 2.0) / volStep) * volStep;
      if(closeVol >= minVol) 
      {
         if(!trade.PositionClosePartial(tickets[j], closeVol)) {
            Print("❌ 部分平仓失败: ", trade.ResultRetcodeDescription());
         }
      }
   }
   hasPartialThisWave = true; 
}

void CloseAllPositions()
{
   ulong tickets[];
   int total = PositionsTotal();
   ArrayResize(tickets, total);
   int count = 0;
   
   for(int i=total-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            tickets[count] = posInfo.Ticket();
            count++;
         }
      }
   }
   for(int j=0; j<count; j++) 
   {
      if(!trade.PositionClose(tickets[j])) {
         Print("❌ 清仓失败: ", trade.ResultRetcodeDescription());
         SendTelegramMessage("⚠️ 紧急！单子强制平仓失败: " + trade.ResultRetcodeDescription());
      }
   }
   
   g_isTrailActive = false;
   g_trailingStopLevel = 0.0;
}

void CheckEntry()
{
   // 📶 基础过滤：点差检查
   long currentSpread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(currentSpread > InpMaxSpread) return; 

   // 📈 ADX 趋势强度过滤（最低门槛）
   if(InpUseADXFilter && g_adx[1] < InpMinADX)
   {
      return;
   }

   // 🔭 宏观过滤 (EMA576 方向过滤)
   if(InpUseMacroFilter)
   {
      double currentPrice = iClose(_Symbol, PERIOD_M15, 1);
      if(g_ema14[1] > g_ema21[1] && currentPrice < g_ema576[1]) return;
      if(g_ema14[1] < g_ema21[1] && currentPrice > g_ema576[1]) return;
   }

   // ⚡ 成交量突破检查 (20周期均值突破)
   double sumVol = 0; 
   for(int i=2; i<=21; i++) sumVol += g_vol[i];
   double avgVol20 = sumVol / 20.0;
   bool volBreakout = (g_vol[1] > avgVol20 * InpVolMultiplier || g_vol[2] > avgVol20 * InpVolMultiplier);

   bool isFastMode = InpUseFastEntry && g_adx[1] >= InpFastEntryADXThreshold;
   double pullbackMargin = isFastMode ? InpFastEntryMargin : InpPullbackPct;
   
   double emaSpreadThreshold = isFastMode ? 0 : 1;
   
   // 🏹 做多信号逻辑
   bool longCondition = (g_ema14[1] > g_ema21[1]) && 
                        (!isFastMode || g_ema21[1] >= g_ema60[1] - emaSpreadThreshold * g_atr[1]) &&
                        volBreakout && g_macd_main[1] > g_macd_sig[1] && g_macd_main[1] > 0;
   
   if(longCondition)
   {
      double low1 = iLow(_Symbol, PERIOD_M15, 1);
      double low2 = iLow(_Symbol, PERIOD_M15, 2);
      
      double pullbackLevel = g_ema14[1] * (1.0 + pullbackMargin/100.0);
      double pullbackLevel2 = g_ema14[2] * (1.0 + pullbackMargin/100.0);
      
      if(low1 <= pullbackLevel || low2 <= pullbackLevel2)
      {
         double ask = symInfo.Ask();
         double sl = NormalizePrice(ask - (g_atr[1] * Dyn_SL_L)); 
         double lot = CalculateVolume(ask, sl, InpRiskPercent, ORDER_TYPE_BUY); 
         if(lot > 0) 
         {
            if(SafeTradeBuy(lot, ask, sl)) 
            {
               string modeTag = isFastMode ? "⚡快速模式" : "";
               SendTelegramMessage("🐺 L1 侦察兵做多 " + modeTag + " | " + _Symbol + " | 价格: " + DoubleToString(ask, _Digits) + " | ADX: " + DoubleToString(g_adx[1], 1));
            }
         }
      }
   }
   // 🏹 做空信号逻辑
   bool shortCondition = (g_ema14[1] < g_ema21[1]) && 
                         (!isFastMode || g_ema21[1] <= g_ema60[1] + emaSpreadThreshold * g_atr[1]) &&
                         volBreakout && g_macd_main[1] < g_macd_sig[1] && g_macd_main[1] < 0;
   
   if(shortCondition)
   {
      double high1 = iHigh(_Symbol, PERIOD_M15, 1);
      double high2 = iHigh(_Symbol, PERIOD_M15, 2);
      
      double pullbackLevel = g_ema14[1] * (1.0 - pullbackMargin/100.0);
      double pullbackLevel2 = g_ema14[2] * (1.0 - pullbackMargin/100.0);
      
      if(high1 >= pullbackLevel || high2 >= pullbackLevel2)
      {
         double bid = symInfo.Bid();
         double sl = NormalizePrice(bid + (g_atr[1] * Dyn_SL_S));
         double lot = CalculateVolume(bid, sl, InpRiskPercent, ORDER_TYPE_SELL); 
         if(lot > 0)
         {
            if(SafeTradeSell(lot, bid, sl)) 
            {
               string modeTag = isFastMode ? "⚡快速模式" : "";
               SendTelegramMessage("🐺 L1 侦察兵做空 " + modeTag + " | " + _Symbol + " | 价格: " + DoubleToString(bid, _Digits) + " | ADX: " + DoubleToString(g_adx[1], 1));
            }
         }
      }
   }
}

void ExecuteAddPosition(int type, double first_sl, int currentLevel)
{
   double price = (type == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
   double currentRiskPct = InpRiskPercent * MathPow(InpLevelMultiplier, currentLevel); 
   ENUM_ORDER_TYPE orderType = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double lot = CalculateVolume(price, first_sl, currentRiskPct, orderType);
   
   if(lot <= 0) return; 

   if(type == POSITION_TYPE_BUY)
   {
      if(SafeTradeBuy(lot, price, first_sl)) 
         SendTelegramMessage("🔥 狼群追击 L" + IntegerToString(currentLevel+1) + " 多 | 风险递减至: " + DoubleToString(currentRiskPct,2) + "%");
   }
   else if(type == POSITION_TYPE_SELL)
   {
      if(SafeTradeSell(lot, price, first_sl)) 
         SendTelegramMessage("🔥 狼群追击 L" + IntegerToString(currentLevel+1) + " 空 | 风险递减至: " + DoubleToString(currentRiskPct,2) + "%");
   }
}

bool SafeTradeBuy(double lot, double price, double sl)
{
   price = NormalizePrice(price);
   sl    = NormalizePrice(sl);
   if(!trade.Buy(lot, _Symbol, price, sl, 0, InpMagicComment)) {
      Print("❌ Buy执行失败: ", trade.ResultRetcodeDescription());
      SendTelegramMessage("⚠️ 致命异常！多单被拒绝: " + trade.ResultRetcodeDescription());
      return false;
   }
   return true;
}

bool SafeTradeSell(double lot, double price, double sl)
{
   price = NormalizePrice(price);
   sl    = NormalizePrice(sl);
   if(!trade.Sell(lot, _Symbol, price, sl, 0, InpMagicComment)) {
      Print("❌ Sell执行失败: ", trade.ResultRetcodeDescription());
      SendTelegramMessage("⚠️ 致命异常！空单被拒绝: " + trade.ResultRetcodeDescription());
      return false;
   }
   return true;
}

double CalculateVolume(double entryPrice, double slPrice, double riskPct, ENUM_ORDER_TYPE orderType)
{
   entryPrice = NormalizePrice(entryPrice);
   slPrice    = NormalizePrice(slPrice);

   double riskAmount = accInfo.Balance() * (riskPct / 100.0);
   double slDistance = MathAbs(entryPrice - slPrice);
   
   double tickSize = symInfo.TickSize();
   double tickValue = symInfo.TickValue();
   
   if(slDistance <= 0 || tickSize <= 0 || tickValue <= 0) 
   { 
      Print("⚠️ 数据未同步或止损距离为0，已拦截开火！");
      return 0; 
   }
   
   double rawVolume = riskAmount / ((slDistance / tickSize) * tickValue);
   double volStep = symInfo.LotsStep(); 
   if(volStep <= 0) return 0;
   int volDigits = VolumeDigitsFromStep(volStep);
   double calcVol = NormalizeDouble(MathFloor(rawVolume / volStep) * volStep, volDigits);
   double minVol = symInfo.LotsMin();
   double maxVol = symInfo.LotsMax();
   if(calcVol < minVol) calcVol = minVol;
   if(calcVol > maxVol) calcVol = maxVol;
   
   double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   double marginRequired = 0;
   if(!OrderCalcMargin(orderType, _Symbol, calcVol, entryPrice, marginRequired))
   {
       static datetime lastMarginErrLog = 0;
       datetime now = TimeCurrent();
       if(InpMarginFailCooldownMinutes > 0)
       {
          datetime until = now + InpMarginFailCooldownMinutes * 60;
          if(until > g_marginFailUntil) g_marginFailUntil = until;
       }
       if(now - lastMarginErrLog >= 60)
       {
          Print("❌ 保证金计算失败: ", GetLastError(), " | type=", (int)orderType, " vol=", DoubleToString(calcVol, volDigits), " price=", DoubleToString(entryPrice, _Digits));
          lastMarginErrLog = now;
       }
       return 0;
   }
   
   if(marginRequired > freeMargin * 0.8)
   {
       double factor = (freeMargin * 0.8) / marginRequired;
       calcVol = NormalizeDouble(MathFloor((calcVol * factor) / volStep) * volStep, volDigits);
       if(calcVol < minVol) return 0;
       if(calcVol > maxVol) calcVol = maxVol;
   }
   
   return calcVol;
}

bool IsNewBar()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_M15, 0);
   if(currentBarTime != lastBarTime)
   {
      lastBarTime = currentBarTime;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| 📊 波动率层数动态调整：根据 ATR 动态修正最大层数                  |
//+------------------------------------------------------------------+
int CalculateDynamicMaxLevels()
{
   if(!InpUseVolatilityFilter) return InpMaxLevels;
   
   double atrValue = g_currentAtr;
   if(atrValue <= 0) return InpMaxLevels;
   
   if(ArraySize(g_atr) < 3) return InpMaxLevels;
   double prevAtr = g_atr[2];
   if(prevAtr <= 0) return InpMaxLevels;
   double atrMultiplier = MathAbs(g_atr[1] / prevAtr);
   
   if(atrMultiplier > InpATRMultiplier_Max)
   {
      int reducedLevels = MathMax(2, InpMaxLevels - 1);
      if(atrMultiplier > InpATRMultiplier_Max * 1.5)
      {
         reducedLevels = MathMax(1, InpMaxLevels - 2);
      }
      return reducedLevels;
   }
   
   return InpMaxLevels;
}

//+------------------------------------------------------------------+
//| 📅 事件过滤器：检测高风险事件时段（周末、重大数据发布窗口）      |
//+------------------------------------------------------------------+
bool IsHighRiskWindow(MqlDateTime &t)
{
   if(!InpUseEventFilter) return false;
   
   if(t.day_of_week == 0 || t.day_of_week == 6) return true;
   
   if(t.day_of_week == 5 && t.hour >= 20) return true;
   if(t.day_of_week == 1 && t.hour < 8) return true;
   
   int hour = t.hour;
   int minute = t.min;
   
   if(t.day_of_week == 3)
   {
      if((hour == 20 && minute >= 0) || (hour == 21 && minute < 30)) return true;
   }
   
   if(t.day_of_week == 4 || t.day_of_week == 5)
   {
      if(hour >= 8 && hour < 10) return true;
   }
   
   return false;
}

string URLEncode(string str)
{
   string result = "";
   uchar chars[];
   
   int count = StringToCharArray(str, chars, 0, WHOLE_ARRAY, CP_UTF8);
   int len = count - 1; 
   
   for(int i=0; i<len; i++) 
   {
      uchar c = chars[i];
      if((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0' && c<='9') || c=='-' || c=='_' || c=='.' || c=='~') 
      {
         result += StringFormat("%c", c);
      } 
      else if(c == ' ') 
      {
         result += "+";
      } 
      else 
      {
         result += StringFormat("%%%02X", c);
      }
   }
   return result;
}

void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   
   string url = "https://api.telegram.org/bot" + InpTelegramToken + "/sendMessage";
   
   string payload = StringFormat("chat_id=%s&text=%s", URLEncode(InpTelegramChatID), URLEncode(msg));
   
   char post[], result[];
   string headers;
   StringToCharArray(payload, post, 0, WHOLE_ARRAY, CP_UTF8);
   
   int res = WebRequest("POST", url, "Content-Type: application/x-www-form-urlencoded\r\n", 5000, post, result, headers);
   
   if(res != 200) Print("❌ Telegram 发送失败！错误码: ", res);
}

//--- 💰 战地财务结算模块 💰 ---
void ReportFinancials(string baseMsg, double bal_before)
{
   Sleep(500); 
   double bal_after = accInfo.Balance();
   double delta = bal_after - bal_before;
   
   double dailyTotal = bal_after - DailyStartBalance; 

   string emoji = (delta >= 0) ? "💰 本次净利: +" : "💀 本次战损: -";
   string deltaStr = DoubleToString(MathAbs(delta), 2);
   
   string dailyEmoji = (dailyTotal >= 0) ? "📈 今日累计: +" : "📉 今日累计: -";
   string dailyStr = DoubleToString(MathAbs(dailyTotal), 2);
   
   string balStr = DoubleToString(bal_after, 2);

   string finalMsg = baseMsg + "\n" + 
                     emoji + CurrencySymbol + deltaStr + " " + CurrencyUnit + "\n" +
                     dailyEmoji + CurrencySymbol + dailyStr + " " + CurrencyUnit + "\n" +
                     "🏦 帝国金库: " + CurrencySymbol + balStr + " " + CurrencyUnit;
                     
   SendTelegramMessage(finalMsg);
}

//+------------------------------------------------------------------+
//| 📋 定期运维状态报告：每30分钟推送持仓+指标快照                    |
//+------------------------------------------------------------------+
void SendPeriodicStatusReport(int posCount, double profitPct)
{
   double equity = accInfo.Equity();
   double balance = accInfo.Balance();
   double dailyPnL = equity - DailyStartBalance;
   double dailyPnLPct = (DailyStartBalance > 0) ? (dailyPnL / DailyStartBalance * 100.0) : 0;
   
   string posType = "";
   double avgEntry = CalculateAverageEntryPrice();
   
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            posType = (posInfo.PositionType() == POSITION_TYPE_BUY) ? "多" : "空";
            break;
         }
      }
   }
   
   string report = "📋 【定期运维报告】\n";
   report += "⏰ 时间: " + TimeToString(TimeCurrent(), TIME_DATE | TIME_MINUTES) + "\n";
   report += "🏦 净值: " + CurrencySymbol + DoubleToString(equity, 2) + " | 余额: " + CurrencySymbol + DoubleToString(balance, 2) + "\n";
   report += "📊 今日浮盈: " + (dailyPnL >= 0 ? "+" : "") + CurrencySymbol + DoubleToString(dailyPnL, 2) + " (" + DoubleToString(dailyPnLPct, 2) + "%)\n";
   report += "📈 当前持仓: " + IntegerToString(posCount) + " 层 | 方向: " + posType + "\n";
   report += "💰 持仓浮盈: " + DoubleToString(profitPct, 2) + "%\n";
   report += "🎯 入场均价: " + DoubleToString(avgEntry, _Digits) + "\n";
   string atr_val = (g_currentAtr > 0) ? DoubleToString(g_currentAtr, _Digits) : "Calc...";
   string adx_val = (ArraySize(g_adx) >= 2) ? DoubleToString(g_adx[1], 1) : "Calc...";
   report += "📊 ATR: " + atr_val + " | ADX: " + adx_val + "\n";
   report += "🛡️ 动态层数: " + IntegerToString(g_dynamicMaxLevels) + "\n";
   report += "⚡ 快速模式: " + (InpUseFastEntry ? "开启" : "关闭") + " | 移动止损: " + (InpUseProfitTrail ? (g_isTrailActive ? "已激活" : "待激活") : "关闭") + "\n";
   
   SendTelegramMessage(report);
}
//+------------------------------------------------------------------+
