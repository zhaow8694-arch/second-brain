//+------------------------------------------------------------------+
//| Guardian Earth V25.11_DualThrust_Only_FIXED.mq5                  |
//| Copyright 2026, AI Commander                                     |
//| "星际重装铁骑版 - 纯Dual Thrust模式 (修复版)"                    |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V25.11_DualThrust_Only_FIXED"
#property version   "1.0"
#property strict
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- MT5 兼容性常量定义
#ifndef MARGIN_MODE_RETAIL_HEDGING
#define MARGIN_MODE_RETAIL_HEDGING 2
#endif
#ifndef TERMINAL_ALLOWED_WEBREQUEST
#define TERMINAL_ALLOWED_WEBREQUEST 71
#endif

//=== 🛡️ 核心风控与时间 ===
input group "=== 核心风控与时间 ==="
input double InpRiskPercent = 0.5; // 黄金市场风险控制在0.5%
input int    InpMaxSpread = 50;    // 黄金市场点差控制
input double InpDailyMaxLoss = 3.0; // 每日最大亏损3%
input int    InpStartHour = 0;
input int    InpEndHour = 24;
input bool   InpFridayExit = true;
input ulong  InpMagicNumber = 250000;
input string InpMagicComment = "DualThrust_GOLD";
input int    InpMaxSlippage = 10;   // 黄金市场滑点控制

//=== Dual Thrust参数 ===
input group "=== Dual Thrust参数 ==="
input int    InpDTRangePeriod = 5;  // 黄金市场最佳周期
input double InpDTLongFactor = 0.6; // 黄金多头因子
input double InpDTShortFactor = 0.6; // 黄金空头因子

//=== 出场规则 ===
input group "=== 出场规则 ==="
input bool   InpUseReverseExit = true;
input bool   InpUseTrailingStop = true;
input double InpTrailActivateATR = 1.2; // 黄金市场追踪止损激活点
input double InpTrailDistanceATR = 0.8; // 黄金市场追踪止损距离

//=== 进场过滤器 ===
input group "=== 进场过滤器 ==="
input double InpVolMultiplier = 1.2; // 黄金市场成交量过滤
input bool   InpUseMacroFilter = false;
input bool   InpUseADXFilter = true; // 启用ADX过滤器
input double InpMinADX = 20.0;       // 黄金市场ADX阈值

//=== 动态保本装甲 ===
input group "=== 动态保本装甲 ==="
input double InpHWM_ActivateATR = 1.5; // 黄金市场保本激活点
input double InpHWM_RetractATR = 0.8;  // 黄金市场保本回撤
input bool   InpStrictPartialLock = false;

//=== 品种校准 ===
input group "=== 品种校准 ==="
input double InpSL_Multiplier_XAUUSD = 2.5; // 黄金止损倍数
input double InpSL_Multiplier_XAGUSD = 2.0;
input double InpSL_Multiplier_SPX500 = 2.5;
input double InpSL_Multiplier_US30 = 2.5;
input double InpSL_Multiplier_Default = 2.0;

//=== 动态参数调整 ===
input group "=== 动态参数调整 ==="
input bool   InpUseDynamicFactors = true;
input double InpVolatilitySensitivity = 0.3; // 黄金市场波动率敏感度

//=== 运维监控 ===
input group "=== 运维监控 ==="
input bool   InpUsePeriodicReport = true;
input int    InpReportIntervalMinutes = 30; // 黄金市场报告间隔

//=== 账户与推送 ===
input group "=== 账户与推送 ==="
enum ENUM_ACC_TYPE { ACC_AUTO, ACC_CENT, ACC_USD };
input ENUM_ACC_TYPE InpAccountType = ACC_AUTO;
input string InpTelegramToken = "";
input string InpTelegramChatID = "";

//--- 全局对象
CTrade         trade;
CPositionInfo  posInfo;
CSymbolInfo    symInfo;
CAccountInfo   accInfo;

//--- 指标句柄
int h_ema576, h_atr, h_vol, h_adx, h_ema20;

//--- 品种校准
double Dyn_SL_Multiplier;

//--- 状态变量
double DailyStartBalance = 0.0;
double HighestProfitATR = 0.0;
bool   DailyLossTriggered = false;
bool   hasPartialThisWave = false;
datetime lastBarTime = 0;
int    lastDayOfYear = -1;
string CurrencyUnit = "美元";
string CurrencySymbol = "$";
string GV_BalanceKey = "";
string GV_DateKey = "";
double g_highestBalance = 0.0; // 历史最高余额
double g_maxDrawdown = 0.0;    // 当前最大回撤
bool   g_maxDrawdownTriggered = false; // 最大回撤触发标志
int    g_maxTradesPerDay = 10;  // 每日最大交易次数

//--- 全局雷达缓存
double g_ema576[];
double g_atr[];
double g_vol[];
double g_adx[];
double g_ema20[];  // 短期EMA

//--- 信号缓存
double g_cachedDTHH = 0.0, g_cachedDTLC = DBL_MAX;
double g_cachedDTHC = 0.0, g_cachedDTLL = DBL_MAX;
datetime g_lastSignalCacheUpdate = 0;

//--- 持仓管理
datetime g_marginFailUntil = 0;
double   g_currentAtr = 0.0;
bool     g_isHighRiskWindow = false;
double   g_trailingStopLevel = 0.0;
bool     g_isTrailActive = false;
double   g_firstEntryPrice = 0.0;
datetime g_lastPeriodicReport = 0;
datetime g_lastTradeTime = 0;
int      g_tradesToday = 0;
datetime g_lastIndicatorUpdate = 0;
int      g_consecutiveLosses = 0; // 连续亏损次数
int      g_maxConsecutiveLosses = 5; // 最大连续亏损次数
int      g_trendDirection = 0;    // 趋势方向：1=多头，-1=空头，0=震荡

//--- 性能缓存
int g_tickCounter = 0;
int g_cachedPositionCount = -1;
int g_cachedPositionType = -1;
double g_cachedProfitATR = 0.0;
const int CACHE_REFRESH_INTERVAL = 5;
int g_reconnectFails = 0; 

//--- 异步推送队列
string g_telegramQueue[];
const int MAX_QUEUE_SIZE = 100;

//+------------------------------------------------------------------+
string URLEncode(string str)
{
   string result = ""; 
   uchar chars[]; 
   int count = StringToCharArray(str, chars, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i=0; i<count-1; i++) 
   {
      uchar c = chars[i];
      if((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0' && c<='9') || 
         c=='-' || c=='_' || c=='.' || c=='~') 
         result += StringFormat("%c", c);
      else if(c == ' ') 
         result += "+"; 
      else 
         result += StringFormat("%%%02X", c);
   }
   return result;
}

//+------------------------------------------------------------------+
void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   if(StringLen(msg) > 4000) msg = StringSubstr(msg, 0, 3900) + "\n...";
   int sz = ArraySize(g_telegramQueue);
   if(sz >= MAX_QUEUE_SIZE) return;
   ArrayResize(g_telegramQueue, sz+1);
   g_telegramQueue[sz] = msg;
}

//+------------------------------------------------------------------+
bool IsConnectedMT5() { return TerminalInfoInteger(TERMINAL_CONNECTED) != 0; }

//+------------------------------------------------------------------+
bool ReinitializeHandles()
{
   Print("🔄 尝试重新初始化指标句柄...");
   if(h_ema576 != INVALID_HANDLE) IndicatorRelease(h_ema576);
   if(h_atr != INVALID_HANDLE) IndicatorRelease(h_atr);
   if(h_vol != INVALID_HANDLE) IndicatorRelease(h_vol);
   if(h_adx != INVALID_HANDLE) IndicatorRelease(h_adx);
   if(h_ema20 != INVALID_HANDLE) IndicatorRelease(h_ema20);
   
   h_ema576 = iMA(_Symbol, PERIOD_D1, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_atr = iATR(_Symbol, PERIOD_D1, 20);
   h_vol = iVolumes(_Symbol, PERIOD_D1, VOLUME_TICK);
   h_adx = iADX(_Symbol, PERIOD_D1, 14);
   h_ema20 = iMA(_Symbol, PERIOD_D1, 20, 0, MODE_EMA, PRICE_CLOSE);
   
   return (h_ema576 != INVALID_HANDLE && h_atr != INVALID_HANDLE && 
           h_vol != INVALID_HANDLE && h_adx != INVALID_HANDLE && 
           h_ema20 != INVALID_HANDLE);
}

//+------------------------------------------------------------------+
void HandleTradeError(int errorCode, string operation)
{
   string errorMsg = "";
   switch(errorCode)
   {
      case 10014: errorMsg = "无效价格"; break;
      case 10016: errorMsg = "交易被拒绝"; break;
      case 10018: errorMsg = "市场关闭"; break;
      case 10019: errorMsg = "资金不足"; break;
      case 10021: errorMsg = "没有足够的资金"; break;
      case 10025: errorMsg = "账户被禁止交易"; break;
      case 10027: errorMsg = "自动交易被禁止"; break;
      case 10030: errorMsg = "无效止损"; break;
      case 10031: errorMsg = "无效止盈"; break;
      case 10049: errorMsg = "价格变化"; break;
      default: errorMsg = "未知错误: " + IntegerToString(errorCode);
   }
   Print("❌ ", operation, " 失败: ", errorMsg);
}

//+------------------------------------------------------------------+
bool IsSlippageValid(double executionPrice, double signalPrice, int maxSlippagePoints)
{
   double slippage = MathAbs(executionPrice - signalPrice) / _Point;
   if(slippage > maxSlippagePoints) 
   {
      Print("⚠️ 滑点超限: ", slippage, " > ", maxSlippagePoints); 
      return false; 
   }
   return true;
}

//+------------------------------------------------------------------+
// 安全开多单函数 - 带滑点保护和错误处理
//+------------------------------------------------------------------+
bool SafeTradeBuy(double lotSize, double signalPrice, double stopLoss, double takeProfit)
{
   double askPrice = symInfo.Ask();
   
   // 滑点检查
   if(!IsSlippageValid(askPrice, signalPrice, InpMaxSlippage))
   {
      Print("❌ 滑点超限，取消开多单");
      return false;
   }
   
   // 执行交易
   bool result = trade.Buy(lotSize, _Symbol, askPrice, stopLoss, takeProfit, InpMagicComment);
   if(!result)
   {
      int errorCode = GetLastError();
      HandleTradeError(errorCode, "开多单");
      return false;
   }
   
   Print("✅ 开多单成功: ", lotSize, " 手 | 价格: ", askPrice, " | 止损: ", stopLoss, " | 止盈: ", takeProfit);
   return true;
}

//+------------------------------------------------------------------+
// 安全开空单函数 - 带滑点保护和错误处理
//+------------------------------------------------------------------+
bool SafeTradeSell(double lotSize, double signalPrice, double stopLoss, double takeProfit)
{
   double bidPrice = symInfo.Bid();
   
   // 滑点检查
   if(!IsSlippageValid(bidPrice, signalPrice, InpMaxSlippage))
   {
      Print("❌ 滑点超限，取消开空单");
      return false;
   }
   
   // 执行交易
   bool result = trade.Sell(lotSize, _Symbol, bidPrice, stopLoss, takeProfit, InpMagicComment);
   if(!result)
   {
      int errorCode = GetLastError();
      HandleTradeError(errorCode, "开空单");
      return false;
   }
   
   Print("✅ 开空单成功: ", lotSize, " 手 | 价格: ", bidPrice, " | 止损: ", stopLoss, " | 止盈: ", takeProfit);
   return true;
}

//+------------------------------------------------------------------+
int OnInit()
{
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("❌ 致命错误：必须运行在 Hedging 账户下！");
      return(INIT_FAILED);
   }
   
   if(InpTelegramToken != "" && !TerminalInfoInteger(TERMINAL_ALLOWED_WEBREQUEST))
      Print("⚠️ 警告：WebRequest 未允许，Telegram推送将失败！");
   
   if(!EventSetTimer(1))
      Print("⚠️ 警告：异步定时器启动失败！");
   
   ArrayResize(g_telegramQueue, 0);
   symInfo.Name(_Symbol); symInfo.Refresh();
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(InpMaxSlippage);
   
   AutoCalibrate();
   
   if(InpAccountType == ACC_CENT) { CurrencyUnit = "美分"; CurrencySymbol = ""; }
   else if(InpAccountType == ACC_USD) { CurrencyUnit = "美元"; CurrencySymbol = "$"; }
   else 
   {
      string accCur = AccountInfoString(ACCOUNT_CURRENCY);
      if(StringFind(accCur, "USC") >= 0 || StringFind(accCur, "cent") >= 0)
      { CurrencyUnit = "美分"; CurrencySymbol = ""; }
      else
      { CurrencyUnit = "美元"; CurrencySymbol = "$"; }
   }
   
   if(!ReinitializeHandles()) return(INIT_FAILED);
   
   ArraySetAsSeries(g_ema576,true);
   ArraySetAsSeries(g_atr,true);
   ArraySetAsSeries(g_vol,true);
   ArraySetAsSeries(g_adx,true);
   ArraySetAsSeries(g_ema20,true);
   ArrayResize(g_ema576,10); 
   ArrayResize(g_atr,10); 
   ArrayResize(g_vol,30);
   ArrayResize(g_adx,10);
   ArrayResize(g_ema20,10);
   
   MqlDateTime t; TimeCurrent(t); 
   GV_BalanceKey = "GE_StartBal_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + _Symbol;
   GV_DateKey = GV_BalanceKey + "_Date";
   
   if(GlobalVariableCheck(GV_BalanceKey) && GlobalVariableCheck(GV_DateKey) && 
      (int)GlobalVariableGet(GV_DateKey) == t.day_of_year)
   {
      DailyStartBalance = GlobalVariableGet(GV_BalanceKey);
      Print("💾 恢复今日初始本金: ", DailyStartBalance);
   }
   else
   {
      DailyStartBalance = accInfo.Balance();
      if(!GlobalVariableCheck(GV_BalanceKey)) GlobalVariableTemp(GV_BalanceKey);
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance);
      GlobalVariableSet(GV_DateKey, t.day_of_year);
      Print("💾 记录今日初始本金: ", DailyStartBalance);
   }
   
   HighestProfitATR = 0.0; hasPartialThisWave = false;
   g_firstEntryPrice = 0.0; g_marginFailUntil = 0; g_cachedPositionCount = -1;
   g_tickCounter = 0; g_tradesToday = 0; g_lastTradeTime = 0; 
   g_lastPeriodicReport = 0; g_reconnectFails = 0;
   g_lastIndicatorUpdate = TimeCurrent();
   lastDayOfYear = t.day_of_year;
   g_highestBalance = accInfo.Balance(); // 初始化历史最高余额为当前余额
   
   int waitCount = 0; 
   while(waitCount < 100) 
   { 
      int atrBars = BarsCalculated(h_atr);
      int volBars = BarsCalculated(h_vol);
      int ema576Bars = BarsCalculated(h_ema576);
      int ema20Bars = BarsCalculated(h_ema20);
      int adxBars = BarsCalculated(h_adx);
      
      if(waitCount % 10 == 0)
      {
         Print("📊 指标初始化进度 - ATR: ", atrBars, ", VOL: ", volBars, ", EMA576: ", ema576Bars, ", EMA20: ", ema20Bars, ", ADX: ", adxBars);
      }
      
      if(atrBars >= 20 && volBars >= 10 && ema20Bars >= 20 && adxBars >= 14) break;
      Sleep(100); 
      waitCount++;
   }
   
   Print("✅ 指标初始化完成，等待时间: ", waitCount, " 次");
   
   Print("🚀 V25.11_FIXED 纯Dual Thrust模式启动 | 修复版");
   SendTelegramMessage("🚀 纯Dual Thrust修复版启动 | " + _Symbol);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void AutoCalibrate()
{
   string s = _Symbol; StringToUpper(s);
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) 
      Dyn_SL_Multiplier = InpSL_Multiplier_XAUUSD;
   else if(StringFind(s,"XAGUSD")>=0 || StringFind(s,"SILVER")>=0) 
      Dyn_SL_Multiplier = InpSL_Multiplier_XAGUSD;
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0) 
      Dyn_SL_Multiplier = InpSL_Multiplier_SPX500;
   else if(StringFind(s,"US30")>=0 || StringFind(s,"WS30")>=0) 
      Dyn_SL_Multiplier = InpSL_Multiplier_US30;
   else 
      Dyn_SL_Multiplier = InpSL_Multiplier_Default;
   
   Print("🛰️ 测向仪锁定 - ", s, " | ATR止损倍数: ", Dyn_SL_Multiplier);
}

//+------------------------------------------------------------------+
void OnTimer()
{
   int qSize = ArraySize(g_telegramQueue);
   if(qSize > 0 && IsConnectedMT5())
   {
      string msg = g_telegramQueue[0];
      string url = "https://api.telegram.org/bot" + InpTelegramToken + "/sendMessage";
      string payload = StringFormat("chat_id=%s&text=%s", URLEncode(InpTelegramChatID), URLEncode(msg));
      char post[], result[]; 
      string headers = "Content-Type: application/x-www-form-urlencoded\r\n";
      StringToCharArray(payload, post, 0, WHOLE_ARRAY, CP_UTF8);
      int res = WebRequest("POST", url, headers, 500, post, result, headers);
      if(res == 200)
      {
         for(int i=0; i<qSize-1; i++) g_telegramQueue[i] = g_telegramQueue[i+1];
         ArrayResize(g_telegramQueue, qSize-1);
      }
      else
         Print("⚠️ Telegram发送失败，HTTP: ", res);
   }
}

//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
// 清理资源
// 释放指标句柄和内存
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   // 发送下线通知
   if(reason != REASON_CLOSE && IsConnectedMT5()) 
      SendTelegramMessage("⚠️ 机甲已主动下线！战区: " + _Symbol);
   
   // 清理全局变量
   if(reason == REASON_REMOVE)
   {
      if(GlobalVariableCheck(GV_BalanceKey)) GlobalVariableDel(GV_BalanceKey);
      if(GlobalVariableCheck(GV_DateKey)) GlobalVariableDel(GV_DateKey);
   }
   
   // 释放指标句柄
   if(h_ema576 != INVALID_HANDLE) IndicatorRelease(h_ema576); 
   if(h_atr != INVALID_HANDLE) IndicatorRelease(h_atr); 
   if(h_vol != INVALID_HANDLE) IndicatorRelease(h_vol);
   if(h_adx != INVALID_HANDLE) IndicatorRelease(h_adx);
   if(h_ema20 != INVALID_HANDLE) IndicatorRelease(h_ema20);
   
   // 释放内存
   ArrayFree(g_ema576); 
   ArrayFree(g_atr); 
   ArrayFree(g_vol); 
   ArrayFree(g_adx);
   ArrayFree(g_ema20);
   ArrayFree(g_telegramQueue);
   
   Print("🔄 资源已清理完毕");
}

//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   double tickSize = symInfo.TickSize();
   if(tickSize <= 0) tickSize = _Point;
   return MathRound(price / tickSize) * tickSize;
}

//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   Print("📊 开始更新指标");
   
   if(h_ema576 == INVALID_HANDLE || h_atr == INVALID_HANDLE || 
      h_vol == INVALID_HANDLE || h_adx == INVALID_HANDLE || h_ema20 == INVALID_HANDLE)
   {
      g_reconnectFails++;
      if(g_reconnectFails > 5) { Print("🚨 句柄重连失败"); return false; }
      if(!ReinitializeHandles()) return false;
      Sleep(100);
      g_reconnectFails = 0;
   }
   
   int ema576Count = CopyBuffer(h_ema576,0,0,4,g_ema576);
   int atrCount = CopyBuffer(h_atr,0,0,4,g_atr);
   int volCount = CopyBuffer(h_vol,0,0,4,g_vol);
   int adxCount = CopyBuffer(h_adx,0,0,4,g_adx);
   int ema20Count = CopyBuffer(h_ema20,0,0,4,g_ema20);
   
   Print("📊 指标数据获取 - EMA576: ", ema576Count, " ATR: ", atrCount, " VOL: ", volCount, " ADX: ", adxCount, " EMA20: ", ema20Count);
   
   if(ema576Count < 3 || atrCount < 3 || volCount < 3 || adxCount < 3 || ema20Count < 3)
   {
      Print("📊 指标数据不足，跳过本次循环");
      return false;
   }
   
   g_currentAtr = g_atr[1]; // 使用上一根已收盘的K线数据
   
   // 趋势识别 - 使用上一根已收盘的K线数据
   if(g_ema20[1] > g_ema20[2] && g_ema20[2] > g_ema20[3])
      g_trendDirection = 1; // 多头趋势
   else if(g_ema20[1] < g_ema20[2] && g_ema20[2] < g_ema20[3])
      g_trendDirection = -1; // 空头趋势
   else
      g_trendDirection = 0; // 震荡
   
   Print("📊 指标更新完成 - ATR: ", g_currentAtr, " 趋势方向: ", g_trendDirection, " EMA20: ", g_ema20[1], " ADX: ", g_adx[1]);
   
   return true;
}

//+------------------------------------------------------------------+
// 计算Dual Thrust交易信号
// 根据历史波动范围计算上下突破阈值
//+------------------------------------------------------------------+
bool CalculateDualThrust(double &highThreshold, double &lowThreshold)
{
   // 检查足够的历史数据
   int bars = Bars(_Symbol, PERIOD_D1);
   int actualPeriod = InpDTRangePeriod;
   
   // 自适应调整周期，确保有足够的历史数据
   if(bars < actualPeriod + 1)
   {
      actualPeriod = MathMax(1, bars - 1);
      Print("⚠️ 历史数据不足，自动调整周期为: ", actualPeriod);
   }
   
   double high[];
   double low[];
   
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   
   // 复制历史数据
   if(CopyHigh(_Symbol, PERIOD_D1, 0, actualPeriod + 1, high) < actualPeriod + 1)
   {
      Print("⚠️ 无法复制最高价数据");
      return false;
   }
   
   if(CopyLow(_Symbol, PERIOD_D1, 0, actualPeriod + 1, low) < actualPeriod + 1)
   {
      Print("⚠️ 无法复制最低价数据");
      return false;
   }
   
   // 计算波动范围
   double range = 0;
   for(int i = 1; i <= actualPeriod; i++)
   {
      double barRange = high[i] - low[i];
      if(barRange > range) range = barRange;
   }
   
   if(range <= 0)
   {
      Print("⚠️ 波动范围为零，无法计算Dual Thrust信号");
      return false;
   }
   
   // 获取当前开盘价
   double openPrice = iOpen(_Symbol, PERIOD_D1, 0);
   if(openPrice <= 0)
   {
      Print("⚠️ 开盘价无效，无法计算Dual Thrust信号");
      return false;
   }
   
   // 动态调整因子
   double longFactor = InpDTLongFactor;
   double shortFactor = InpDTShortFactor;
   
   if(InpUseDynamicFactors && g_currentAtr > 0)
   {
      double volatility = g_currentAtr / openPrice;
      double adjustment = volatility * InpVolatilitySensitivity * 100;
      longFactor = MathMax(0.1, MathMin(1.0, longFactor + adjustment));
      shortFactor = MathMax(0.1, MathMin(1.0, shortFactor + adjustment));
   }
   
   // 计算突破阈值
   highThreshold = openPrice + range * longFactor;
   lowThreshold = openPrice - range * shortFactor;
   
   return true;
}

//+------------------------------------------------------------------+
// 计算仓位大小
// 根据风险百分比和ATR计算合适的仓位大小
//+------------------------------------------------------------------+
double CalculatePositionSize(double riskPercent)
{
   double balance = accInfo.Balance();
   if(balance <= 0) return 0;
   
   double riskAmount = balance * riskPercent / 100.0;
   if(riskAmount <= 0) return 0;
   
   if(g_currentAtr <= 0) return 0;
   
   double stopLoss = g_currentAtr * Dyn_SL_Multiplier;
   double tickValue = symInfo.TickValue();
   if(tickValue <= 0) return 0;
   
   double tickSize = symInfo.TickSize();
   if(tickSize <= 0) tickSize = _Point;
   
   double ticksPerATR = stopLoss / tickSize;
   if(ticksPerATR <= 0) return 0;
   
   double lotSize = riskAmount / (ticksPerATR * tickValue);
   lotSize = MathMax(0.01, lotSize); // 最小仓位
   lotSize = MathMin(symInfo.LotsMax(), lotSize); // 最大仓位
   
   return NormalizeDouble(lotSize, 2);
}

//+------------------------------------------------------------------+
bool CheckRiskManagement()
{
   // 检查每日最大亏损
   double currentBalance = accInfo.Balance();
   double dailyLoss = (DailyStartBalance - currentBalance) / DailyStartBalance * 100.0;
   
   Print("📊 风险管理检查 - 余额: ", currentBalance, " 每日亏损: ", dailyLoss, "%");
   
   if(dailyLoss >= InpDailyMaxLoss)
   {
      if(!DailyLossTriggered)
      {
         DailyLossTriggered = true;
         Print("🚨 每日最大亏损触发: ", dailyLoss, "%");
         SendTelegramMessage("🚨 每日最大亏损触发: " + DoubleToString(dailyLoss, 2) + "%");
         
         // 平仓所有持仓 - 倒序遍历避免数组塌陷
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber)
            {
               if(posInfo.Type() == POSITION_TYPE_BUY)
                  trade.PositionClose(posInfo.Ticket());
               else if(posInfo.Type() == POSITION_TYPE_SELL)
                  trade.PositionClose(posInfo.Ticket());
            }
         }
      }
      return false;
   }
   
   // 检查最大回撤 (40%)
   if(currentBalance > g_highestBalance)
   {
      g_highestBalance = currentBalance;
      g_maxDrawdownTriggered = false;
   }
   
   g_maxDrawdown = (g_highestBalance - currentBalance) / g_highestBalance * 100.0;
   if(g_maxDrawdown >= 40.0)
   {
      if(!g_maxDrawdownTriggered)
      {
         g_maxDrawdownTriggered = true;
         Print("🚨 最大回撤触发: ", g_maxDrawdown, "%");
         SendTelegramMessage("🚨 最大回撤触发: " + DoubleToString(g_maxDrawdown, 2) + "%");
         
         // 平仓所有持仓 - 倒序遍历避免数组塌陷
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber)
            {
               if(posInfo.Type() == POSITION_TYPE_BUY)
                  trade.PositionClose(posInfo.Ticket());
               else if(posInfo.Type() == POSITION_TYPE_SELL)
                  trade.PositionClose(posInfo.Ticket());
            }
         }
      }
      return false;
   }
   
   // 检查连续亏损
   if(g_consecutiveLosses >= g_maxConsecutiveLosses)
   {
      Print("🚨 连续亏损触发: ", g_consecutiveLosses, " 次");
      SendTelegramMessage("🚨 连续亏损触发: " + IntegerToString(g_consecutiveLosses) + " 次");
      // 重置连续亏损次数，避免一直停止交易
      g_consecutiveLosses = 0;
      return false;
   }
   
   // 检查时间范围
   MqlDateTime t;
   TimeCurrent(t);
   if(t.hour < InpStartHour || t.hour >= InpEndHour)
      return false;
   
   // 检查周五平仓
   if(InpFridayExit && t.day_of_week == 5 && t.hour >= 22)
      return false;
   
   // 检查滑点
   if(symInfo.Spread() > InpMaxSpread)
      return false;
   
   return true;
}

//+------------------------------------------------------------------+
bool CheckEntryFilters()
{
   // 成交量过滤器
   if(InpVolMultiplier > 1.0)
   {
      double avgVolume = 0;
      int validVolCount = 0;
      for(int i = 1; i <= 20; i++)
      {
         if(i < ArraySize(g_vol) && g_vol[i] > 0)
         {
            avgVolume += g_vol[i];
            validVolCount++;
         }
      }
      if(validVolCount > 0)
      {
         avgVolume /= validVolCount;
         if(g_vol[0] < avgVolume * InpVolMultiplier)
         {
            Print("📊 成交量过滤器过滤 - 当前: ", g_vol[0], " 平均: ", avgVolume, " 倍数: ", InpVolMultiplier);
            return false;
         }
      }
   }
   
   // ADX过滤器 - 使用上一根已收盘的K线数据
   if(InpUseADXFilter && g_adx[1] < InpMinADX)
   {
      Print("📊 ADX过滤器过滤 - 当前: ", g_adx[1], " 阈值: ", InpMinADX);
      return false;
   }
   
   // 趋势过滤器 - 只在有明显趋势时交易
   if(g_trendDirection == 0 && g_adx[1] < 25)
   {
      Print("📊 趋势过滤器过滤 - 趋势方向: ", g_trendDirection, " ADX: ", g_adx[1]);
      return false;
   }
   
   // 波动率过滤器 - 避免在极端波动时交易
   double avgATR = 0;
   int validAtrCount = 0;
   for(int i = 1; i <= 10; i++)
   {
      if(i < ArraySize(g_atr) && g_atr[i] > 0)
      {
         avgATR += g_atr[i];
         validAtrCount++;
      }
   }
   if(validAtrCount > 0)
   {
      avgATR /= validAtrCount;
      if(g_currentAtr > avgATR * 2.0)
      {
         Print("📊 波动率过滤器过滤 - 当前: ", g_currentAtr, " 平均: ", avgATR);
         return false;
      }
   }
   
   Print("📊 所有过滤器通过");
   return true;
}

//+------------------------------------------------------------------+
void UpdateTrailingStop()
{
   // 倒序遍历避免数组塌陷
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber)
      {
         double currentPrice = (posInfo.Type() == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
         double entryPrice = posInfo.PriceOpen();
         double profitPoints = 0;
         if(posInfo.Type() == POSITION_TYPE_BUY)
             profitPoints = currentPrice - entryPrice;
         else if(posInfo.Type() == POSITION_TYPE_SELL)
             profitPoints = entryPrice - currentPrice;
         double profitATR = profitPoints / g_currentAtr;
         
         if(InpUseTrailingStop && profitATR >= InpTrailActivateATR)
         {
            double trailLevel = (posInfo.Type() == POSITION_TYPE_BUY) ? 
                               currentPrice - g_currentAtr * InpTrailDistanceATR : 
                               currentPrice + g_currentAtr * InpTrailDistanceATR;
            
            if(!g_isTrailActive || trailLevel > g_trailingStopLevel)
            {
               g_trailingStopLevel = trailLevel;
               g_isTrailActive = true;
               
               // 更新止损
               trade.PositionModify(posInfo.Ticket(), NormalizePrice(trailLevel), posInfo.TakeProfit());
            }
         }
         
         // 动态保本装甲
         if(profitATR >= InpHWM_ActivateATR)
         {
            double breakEvenLevel = (posInfo.Type() == POSITION_TYPE_BUY) ? 
                               entryPrice + g_currentAtr * InpHWM_RetractATR : 
                               entryPrice - g_currentAtr * InpHWM_RetractATR;
            
            if(profitATR > HighestProfitATR)
            {
               HighestProfitATR = profitATR;
               // 更新保本止损
               trade.PositionModify(posInfo.Ticket(), NormalizePrice(breakEvenLevel), posInfo.TakeProfit());
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
void OnTick()
{
   g_tickCounter++;
   if(g_tickCounter % CACHE_REFRESH_INTERVAL != 0) return;
   
   // 检查跨日重置
   MqlDateTime t;
   TimeCurrent(t);
   if(t.day_of_year != lastDayOfYear)
   {
      lastDayOfYear = t.day_of_year;
      DailyStartBalance = accInfo.Balance();
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance);
      GlobalVariableSet(GV_DateKey, t.day_of_year);
      DailyLossTriggered = false;
      g_tradesToday = 0;
      Print("📅 跨日重置 - 新的每日初始本金: ", DailyStartBalance);
   }
   
   // 更新指标
   if(!UpdateIndicators()) return;
   
   // 检查当前价格
   double bid = symInfo.Bid();
   double ask = symInfo.Ask();
   double currentPrice = (bid + ask) / 2;
   
   // 检查价格有效性
   if(bid <= 0 || ask <= 0 || currentPrice <= 0)
   {
      Print("⚠️ 价格无效 - 买价: ", bid, " 卖价: ", ask);
      // 尝试使用symInfo
      symInfo.Refresh();
      bid = symInfo.Bid();
      ask = symInfo.Ask();
      currentPrice = (bid + ask) / 2;
      if(bid <= 0 || ask <= 0 || currentPrice <= 0)
      {
         Print("🚨 价格仍然无效，跳过本次循环");
         return;
      }
   }
   
   Print("📊 价格信息 - 买价: ", bid, " 卖价: ", ask, " 当前价格: ", currentPrice);
   
   // 风险管理检查
   if(!CheckRiskManagement()) return;
   
   // 计算Dual Thrust信号
   double highThreshold, lowThreshold;
   if(!CalculateDualThrust(highThreshold, lowThreshold))
   {
      Print("📊 Dual Thrust信号计算失败");
      return;
   }
   
   Print("📊 Dual Thrust信号 - 高阈值: ", highThreshold, " 低阈值: ", lowThreshold, " 当前价格: ", currentPrice);
   
   // 检查进场过滤器
   if(!CheckEntryFilters())
   {
      Print("📊 进场过滤器过滤掉信号");
      return;
   }
   
   Print("📊 进场过滤器通过 - 趋势方向: ", g_trendDirection, " ADX: ", g_adx[0], " ATR: ", g_currentAtr);
   
   // 更新当前价格
   currentPrice = (symInfo.Bid() + symInfo.Ask()) / 2;
   
   // 检查持仓
   int buyPositions = 0, sellPositions = 0;
   double buyVolume = 0, sellVolume = 0;
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber)
      {
         if(posInfo.Type() == POSITION_TYPE_BUY)
         {
            buyPositions++;
            buyVolume += posInfo.Volume();
         }
         else if(posInfo.Type() == POSITION_TYPE_SELL)
         {
            sellPositions++;
            sellVolume += posInfo.Volume();
         }
      }
   }
   
   // 计算仓位大小
   double lotSize = CalculatePositionSize(InpRiskPercent);
   if(lotSize <= 0)
   {
      Print("📊 仓位大小计算失败: ", lotSize);
      return;
   }
   
   Print("📊 仓位大小: ", lotSize, " 手");
   
   // 检查交易频率
   if(g_tradesToday >= g_maxTradesPerDay)
   {
      Print("⚠️ 每日交易次数已达上限: ", g_tradesToday, "/", g_maxTradesPerDay);
      return;
   }
   
   Print("📊 交易频率检查通过 - 今日交易次数: ", g_tradesToday, "/", g_maxTradesPerDay);
   
   // 多头信号 - 与趋势方向一致
   if(currentPrice > highThreshold && buyPositions == 0 && (g_trendDirection == 1 || g_trendDirection == 0))
   {
      if(sellPositions > 0 && InpUseReverseExit)
      {
         // 反向出场 - 倒序遍历避免数组塌陷
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber && posInfo.Type() == POSITION_TYPE_SELL)
            {
               trade.PositionClose(posInfo.Ticket());
            }
         }
      }
      
      // 开多单
      double stopLoss = NormalizePrice(currentPrice - g_currentAtr * Dyn_SL_Multiplier);
      double takeProfit = NormalizePrice(currentPrice + g_currentAtr * Dyn_SL_Multiplier * 2);
      
      if(SafeTradeBuy(lotSize, currentPrice, stopLoss, takeProfit))
      {
         g_firstEntryPrice = currentPrice;
         g_lastTradeTime = TimeCurrent();
         g_tradesToday++;
         
         SendTelegramMessage("📈 开多单: " + DoubleToString(lotSize, 2) + " 手 | " + _Symbol + " | 价格: " + DoubleToString(currentPrice, 5));
      }
   }
   
   // 空头信号 - 与趋势方向一致
   if(currentPrice < lowThreshold && sellPositions == 0 && (g_trendDirection == -1 || g_trendDirection == 0))
   {
      if(buyPositions > 0 && InpUseReverseExit)
      {
         // 反向出场 - 倒序遍历避免数组塌陷
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber && posInfo.Type() == POSITION_TYPE_BUY)
            {
               trade.PositionClose(posInfo.Ticket());
            }
         }
      }
      
      // 开空单
      double stopLoss = NormalizePrice(currentPrice + g_currentAtr * Dyn_SL_Multiplier);
      double takeProfit = NormalizePrice(currentPrice - g_currentAtr * Dyn_SL_Multiplier * 2);
      
      if(SafeTradeSell(lotSize, currentPrice, stopLoss, takeProfit))
      {
         g_firstEntryPrice = currentPrice;
         g_lastTradeTime = TimeCurrent();
         g_tradesToday++;
         
         SendTelegramMessage("📉 开空单: " + DoubleToString(lotSize, 2) + " 手 | " + _Symbol + " | 价格: " + DoubleToString(currentPrice, 5));
      }
   }
   
   // 更新追踪止损
   UpdateTrailingStop();
   
   // 定期报告
   if(InpUsePeriodicReport && TimeCurrent() - g_lastPeriodicReport >= InpReportIntervalMinutes * 60)
   {
      string report = "📊 定期报告 | " + _Symbol + "\n";
      report += "余额: " + DoubleToString(accInfo.Balance(), 2) + " " + CurrencyUnit + "\n";
      report += "净值: " + DoubleToString(accInfo.Equity(), 2) + " " + CurrencyUnit + "\n";
      report += "今日盈亏: " + DoubleToString(accInfo.Balance() - DailyStartBalance, 2) + " " + CurrencyUnit + "\n";
      report += "持仓: " + IntegerToString(buyPositions + sellPositions) + " 笔\n";
      report += "ATR: " + DoubleToString(g_currentAtr, 5) + "\n";
      report += "交易次数: " + IntegerToString(g_tradesToday) + " 次";
      
      Print(report);
      SendTelegramMessage(report);
      g_lastPeriodicReport = TimeCurrent();
   }
}

//+------------------------------------------------------------------+