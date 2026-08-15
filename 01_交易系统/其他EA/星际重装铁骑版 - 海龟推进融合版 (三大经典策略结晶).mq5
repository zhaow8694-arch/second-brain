//+------------------------------------------------------------------+
//| Guardian Earth V25.11_DualThrust_Only.mq5                        |
//| Copyright 2026, AI Commander                                     |
//| "星际重装铁骑版 - 纯Dual Thrust模式 (高频率突破验证版)"            |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V25.11_DualThrust_Only"
#property version   "25.11"
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

//--- 🛡️ 核心风控与时间 ---
input group "=== 核心风控与时间 ==="
input double InpRiskPercent = 1.0;           // 💥 单笔风险%(基于ATR)
input int    InpMaxSpread = 150;             // 🛑 最大允许点差
input double InpDailyMaxLoss = 5.0;          // 🥶 单日熔断回撤%
input int    InpStartHour = 0;               // 交易开始时间
input int    InpEndHour = 24;                // 交易结束时间
input bool   InpFridayExit = true;
input ulong  InpMagicNumber = 250000;
input string InpMagicComment = "DualThrust";
input int    InpMaxLevels = 1;               // 纯DT不加仓，固定1层
input int    InpMaxSlippage = 20;

input group "=== 资金与保证金安全 ==="
input double InpMinBalanceToTrade = 100.0;
input int    InpMarginFailCooldownMinutes = 60;

//=== Dual Thrust参数 ===
input group "=== Dual Thrust参数 ==="
input int    InpDTRangePeriod = 4;            // Range计算周期
input double InpDTLongFactor = 0.5;           // 做多系数K1
input double InpDTShortFactor = 0.5;          // 做空系数K2

//=== 出场规则 ===
input group "=== 出场规则 ==="
input bool   InpUseReverseExit = true;        // 反向信号出场
input bool   InpUseTrailingStop = true;       // 使用移动止损
input double InpTrailActivatePct = 3.0;       // 移动止损激活阈值%
input double InpTrailDistancePct = 2.0;       // 移动止损距离%
input bool   InpUseATRForTrail = true;
input double InpTrailATRMultiplier = 2.5;

//=== 进场过滤器 ===
input group "=== 进场过滤器 ==="
input double InpVolMultiplier = 1.0;          // 成交量倍数要求
input bool   InpUseMacroFilter = false;       // 启用宏观过滤
input bool   InpUseADXFilter = false;         // 启用ADX过滤
input double InpMinADX = 25.0;                // 最低ADX阈值

//=== 动态保本装甲 ===
input group "=== 动态保本装甲 ==="
input double InpHWM_Activate = 5.0;           // 保本激活阈值%
input double InpHWM_Retract = 2.5;            // 回撤触发对切%
input bool   InpStrictPartialLock = false;

//=== 品种校准 ===
input group "=== 品种校准 ==="
input double InpSL_Multiplier_XAUUSD = 2.0;   // ATR止损倍数
input double InpSL_Multiplier_XAGUSD = 2.0;
input double InpSL_Multiplier_SPX500 = 2.5;
input double InpSL_Multiplier_US30 = 2.5;
input double InpSL_Multiplier_Default = 2.0;

//=== 运维监控 ===
input group "=== 运维监控 ==="
input bool   InpUsePeriodicReport = true;
input int    InpReportIntervalMinutes = 60;

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
int h_ema576, h_atr, h_vol, h_adx;

//--- 品种校准
double Dyn_SL_Multiplier;

//--- 状态变量
double DailyStartBalance = 0.0;
double HighestProfitPct = 0.0;
bool   DailyLossTriggered = false;
bool   hasPartialThisWave = false;
datetime lastBarTime = 0;
int    lastDayOfYear = -1;

string CurrencyUnit = "美元";
string CurrencySymbol = "$";
string GV_BalanceKey = ""; 
string GV_DateKey = ""; 

//--- 全局雷达缓存
double g_ema576[];
double g_atr[];
double g_vol[];
double g_adx[];

//--- 信号缓存（性能优化）
double g_cachedDTHH = 0.0, g_cachedDTLC = DBL_MAX;
double g_cachedDTHC = 0.0, g_cachedDTLL = DBL_MAX;
datetime g_lastSignalCacheDay = 0;

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

//--- 性能缓存
int g_tickCounter = 0;
int g_cachedPositionCount = -1;
int g_cachedPositionType = -1;
double g_cachedProfitPct = 0.0;
const int CACHE_REFRESH_INTERVAL = 5;
int g_reconnectFails = 0; 

//--- 异步推送队列
string g_telegramQueue[];
const int MAX_QUEUE_SIZE = 100;

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
   
   h_ema576 = iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_atr = iATR(_Symbol, PERIOD_D1, 20);
   h_vol = iVolumes(_Symbol, PERIOD_H1, VOLUME_TICK);
   h_adx = iADX(_Symbol, PERIOD_H1, 14);
   
   return (h_ema576 != INVALID_HANDLE && h_atr != INVALID_HANDLE && 
           h_vol != INVALID_HANDLE && h_adx != INVALID_HANDLE);
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

   ArrayResize(g_ema576,10); 
   ArrayResize(g_atr,10); 
   ArrayResize(g_vol,30);
   ArrayResize(g_adx,10);

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

   HighestProfitPct = 0.0; hasPartialThisWave = false;
   g_firstEntryPrice = 0.0; g_marginFailUntil = 0; g_cachedPositionCount = -1;
   g_tickCounter = 0; g_tradesToday = 0; g_lastTradeTime = 0; 
   g_lastPeriodicReport = 0; g_reconnectFails = 0;
   g_lastIndicatorUpdate = TimeCurrent();
   lastDayOfYear = t.day_of_year;

   int waitCount = 0; 
   while(waitCount < 50) 
   { 
      if(BarsCalculated(h_atr) >= 60 && BarsCalculated(h_vol) >= 22 &&
         BarsCalculated(h_ema576) >= 576) break;
      Sleep(100); 
      waitCount++; 
   }

   Print("🚀 V25.11 纯Dual Thrust模式启动 | 高频率突破验证版");
   SendTelegramMessage("🚀 纯Dual Thrust模式启动 | " + _Symbol);

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
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   if(reason != REASON_CLOSE && IsConnectedMT5()) 
      SendTelegramMessage("⚠️ 机甲已主动下线！战区: " + _Symbol);
   
   if(reason == REASON_REMOVE)
   {
      if(GlobalVariableCheck(GV_BalanceKey)) GlobalVariableDel(GV_BalanceKey);
      if(GlobalVariableCheck(GV_DateKey)) GlobalVariableDel(GV_DateKey);
   }

   IndicatorRelease(h_ema576); 
   IndicatorRelease(h_atr); 
   IndicatorRelease(h_vol);
   IndicatorRelease(h_adx);
   
   ArrayFree(g_ema576); 
   ArrayFree(g_atr); 
   ArrayFree(g_vol); 
   ArrayFree(g_adx);
   ArrayFree(g_telegramQueue);
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
   if(h_ema576 == INVALID_HANDLE || h_atr == INVALID_HANDLE || 
      h_vol == INVALID_HANDLE || h_adx == INVALID_HANDLE)
   {
      g_reconnectFails++;
      if(g_reconnectFails > 5) { Print("🚨 句柄重连失败"); return false; }
      if(!ReinitializeHandles()) return false;
      Sleep(100);
      g_reconnectFails = 0;
   }

   if(CopyBuffer(h_ema576,0,0,4,g_ema576)<3) return false;
   if(CopyBuffer(h_atr,0,0,4,g_atr)<3) return false;
   if(CopyBuffer(h_vol,0,0,25,g_vol)<22) return false;
   if(CopyBuffer(h_adx,0,0,4,g_adx)<3) return false;

   g_currentAtr = g_atr[1];
   g_lastIndicatorUpdate = TimeCurrent();
   return true;
}

//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime current = iTime(_Symbol, PERIOD_M15, 0);
   if(current != lastBarTime) { lastBarTime = current; return true; }
   return false;
}

//+------------------------------------------------------------------+
void RefreshSignalCache()
{
   datetime today = iTime(_Symbol, PERIOD_D1, 0);
   if(today == g_lastSignalCacheDay) return;
   g_lastSignalCacheDay = today;
   
   // Dual Thrust 缓存
   g_cachedDTHH = 0; g_cachedDTLC = DBL_MAX;
   g_cachedDTHC = 0; g_cachedDTLL = DBL_MAX;
   for(int i=1; i<=InpDTRangePeriod; i++)
   {
      double high = iHigh(_Symbol, PERIOD_D1, i);
      double low = iLow(_Symbol, PERIOD_D1, i);
      double close = iClose(_Symbol, PERIOD_D1, i);
      if(high <= 0 || low <= 0 || close <= 0) continue;
      if(high > g_cachedDTHH) g_cachedDTHH = high;
      if(low < g_cachedDTLL) g_cachedDTLL = low;
      if(close > g_cachedDTHC) g_cachedDTHC = close;
      if(close < g_cachedDTLC) g_cachedDTLC = close;
   }
}

//+------------------------------------------------------------------+
int DualThrustSignal()
{
   RefreshSignalCache();
   double Range = MathMax(g_cachedDTHH - g_cachedDTLC, g_cachedDTHC - g_cachedDTLL);
   double open0 = iOpen(_Symbol, PERIOD_D1, 0);
   if(open0 <= 0) return 0;
   
   double upperBand = open0 + InpDTLongFactor * Range;
   double lowerBand = open0 - InpDTShortFactor * Range;
   double close1 = iClose(_Symbol, PERIOD_M15, 1);
   
   // 输出调试信息（每小时最多一次）
   static datetime lastDebug = 0;
   if(TimeCurrent() - lastDebug > 3600)
   {
      Print("📊 [DT] HH=", g_cachedDTHH, " LC=", g_cachedDTLC, 
            " HC=", g_cachedDTHC, " LL=", g_cachedDTLL);
      Print("📊 [DT] Range=", Range, " 开盘=", open0, 
            " 上轨=", upperBand, " 下轨=", lowerBand, " 现价=", close1);
      lastDebug = TimeCurrent();
   }
   
   if(close1 > upperBand) return 1;
   if(close1 < lowerBand) return -1;
   return 0;
}

//+------------------------------------------------------------------+
bool VolumeFilter()
{
   if(InpVolMultiplier <= 0) return true;
   double sumVol = 0; int validVolCount = 0;
   for(int i=2; i<=21 && i<ArraySize(g_vol); i++) 
   { if(g_vol[i] > 0) { sumVol += g_vol[i]; validVolCount++; } }
   if(validVolCount == 0) return false;
   return (g_vol[1] > (sumVol / validVolCount) * InpVolMultiplier);
}

//+------------------------------------------------------------------+
bool ADXFilter()
{
   if(!InpUseADXFilter) return true;
   if(ArraySize(g_adx) < 2) return false;
   return (g_adx[1] >= InpMinADX);
}

//+------------------------------------------------------------------+
bool MacroFilter(int direction)
{
   if(!InpUseMacroFilter) return true;
   if(ArraySize(g_ema576) < 3) return true;
   bool macroTrendUp = (g_ema576[1] > g_ema576[2]);
   bool macroTrendDown = (g_ema576[1] < g_ema576[2]);
   if(direction == 1 && !macroTrendUp) return false;
   if(direction == -1 && !macroTrendDown) return false;
   return true;
}

//+------------------------------------------------------------------+
double CalculateATRSL(double entryPrice, int direction)
{
   double atrValue = g_currentAtr;
   if(atrValue <= 0) atrValue = entryPrice * 0.01;
   double slDistance = atrValue * Dyn_SL_Multiplier;
   return NormalizePrice((direction == 1) ? entryPrice - slDistance : entryPrice + slDistance);
}

//+------------------------------------------------------------------+
double CalculateVolume(double entryPrice, double slPrice, int direction)
{
   datetime now = TimeCurrent();
   if(g_marginFailUntil > 0 && now < g_marginFailUntil) return 0; 
   symInfo.RefreshRates();
   
   double atrValue = g_currentAtr;
   if(atrValue <= 0) atrValue = entryPrice * 0.01;
   
   double tickValue = symInfo.TickValue();
   double tickSize = symInfo.TickSize();
   double pointValue = tickValue / tickSize;
   double riskAmount = accInfo.Balance() * (InpRiskPercent / 100.0);
   double rawVolume = riskAmount / (atrValue * Dyn_SL_Multiplier * pointValue);
   
   double lotStep = symInfo.LotsStep();
   double minLot = symInfo.LotsMin();
   double maxLot = symInfo.LotsMax();
   int volDigits = (lotStep < 1.0) ? (int)MathCeil(-MathLog10(lotStep)) : 0;
   double calcLot = NormalizeDouble(MathFloor(rawVolume / lotStep) * lotStep, volDigits);
   if(calcLot < minLot) calcLot = minLot;
   if(calcLot > maxLot) calcLot = maxLot;
   
   double freeMargin = accInfo.FreeMargin(), marginRequired = 0;
   ENUM_ORDER_TYPE orderType = (direction == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   
   if(!OrderCalcMargin(orderType, _Symbol, calcLot, entryPrice, marginRequired))
   {
       int err = GetLastError();
       HandleTradeError(err, "保证金预演");
       g_marginFailUntil = (err == 4001 || err == 4002 || err == 10018) ? now + 60 : now + InpMarginFailCooldownMinutes * 60;
       return 0;
   }
   
   if(marginRequired > freeMargin * 0.8)
   {
       calcLot = NormalizeDouble(MathFloor((calcLot * freeMargin * 0.8 / marginRequired) / lotStep) * lotStep, volDigits);
       if(calcLot < minLot) return 0;
   }
   return calcLot;
}

//+------------------------------------------------------------------+
void CheckEntry()
{
   symInfo.RefreshRates(); 
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;
   
   int signal = DualThrustSignal();
   if(signal == 0) return;
   
   if(!VolumeFilter()) return;
   if(!ADXFilter()) return;
   
   int direction = signal;
   if(!MacroFilter(direction)) return;
   
   double entryPrice = (direction == 1) ? symInfo.Ask() : symInfo.Bid();
   double sl = CalculateATRSL(entryPrice, direction);
   double lot = CalculateVolume(entryPrice, sl, direction);
   
   if(lot > 0)
   {
      bool success = false;
      if(direction == 1)
      {
         if(!IsSlippageValid(symInfo.Ask(), entryPrice, InpMaxSlippage)) return;
         success = SafeTradeBuy(lot, entryPrice, sl);
      }
      else
      {
         if(!IsSlippageValid(symInfo.Bid(), entryPrice, InpMaxSlippage)) return;
         success = SafeTradeSell(lot, entryPrice, sl);
      }
      if(success)
      {
         string dirStr = (direction == 1) ? "多" : "空";
         SendTelegramMessage("🔥 DT突破" + dirStr + " | ATR:" + DoubleToString(g_currentAtr,2));
      }
   }
}

//+------------------------------------------------------------------+
bool SafeTradeBuy(double lot, double signalPrice, double sl)
{
   if(TimeCurrent() - g_lastTradeTime < 1) return false;
   symInfo.RefreshRates(); 
   double ask = symInfo.Ask();
   if(!IsSlippageValid(ask, signalPrice, InpMaxSlippage)) return false;
   if(!trade.Buy(lot, _Symbol, ask, NormalizePrice(sl), 0, InpMagicComment)) 
      { HandleTradeError(trade.ResultRetcode(), "买入"); return false; }
   g_lastTradeTime = TimeCurrent(); g_tradesToday++;
   g_cachedPositionCount = -1;
   Print("📝 记录交易 #", g_tradesToday);
   return true;
}

//+------------------------------------------------------------------+
bool SafeTradeSell(double lot, double signalPrice, double sl)
{
   if(TimeCurrent() - g_lastTradeTime < 1) return false;
   symInfo.RefreshRates(); 
   double bid = symInfo.Bid();
   if(!IsSlippageValid(bid, signalPrice, InpMaxSlippage)) return false;
   if(!trade.Sell(lot, _Symbol, bid, NormalizePrice(sl), 0, InpMagicComment)) 
      { HandleTradeError(trade.ResultRetcode(), "卖出"); return false; }
   g_lastTradeTime = TimeCurrent(); g_tradesToday++;
   g_cachedPositionCount = -1;
   Print("📝 记录交易 #", g_tradesToday);
   return true;
}

//+------------------------------------------------------------------+
void RefreshPositionCache()
{
   g_cachedPositionCount = 0; 
   g_cachedPositionType = -1; 
   g_cachedProfitPct = 0.0;
   g_firstEntryPrice = 0.0;
   int buy = 0, sell = 0; 
   double totalP = 0.0; 
   datetime oldestT = 0;

   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         g_cachedPositionCount++;
         totalP += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
         if(posInfo.PositionType() == POSITION_TYPE_BUY) buy++; else sell++;
         if(oldestT == 0 || posInfo.Time() < oldestT)
         { oldestT = posInfo.Time(); g_firstEntryPrice = posInfo.PriceOpen(); }
      }
   }
   
   if(g_cachedPositionCount > 0)
   {
      g_cachedPositionType = (buy > 0 && sell == 0) ? POSITION_TYPE_BUY : 
                            (sell > 0 && buy == 0) ? POSITION_TYPE_SELL : -1;
      if(accInfo.Balance() > 0) g_cachedProfitPct = (totalP / accInfo.Balance()) * 100.0;
   }
   else
   {
      g_isTrailActive = false;
      g_trailingStopLevel = 0.0;
   }
}

//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber) 
         trade.PositionClose(posInfo.Ticket());
   
   int checkResidual = 0;
   for(int retry=0; retry<3; retry++)
   {
      checkResidual = 0;
      for(int k=PositionsTotal()-1; k>=0; k--)
         if(posInfo.SelectByIndex(k) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber) checkResidual++;
      if(checkResidual == 0) break;
      Sleep(50);
      for(int k=PositionsTotal()-1; k>=0; k--)
         if(posInfo.SelectByIndex(k) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
            trade.PositionClose(posInfo.Ticket());
   }
   
   if(checkResidual == 0)
   {
      g_isTrailActive = false; g_trailingStopLevel = 0.0; g_firstEntryPrice = 0.0; 
      g_cachedPositionCount = -1; HighestProfitPct = 0.0; hasPartialThisWave = false;
   }
}

//+------------------------------------------------------------------+
void CheckReverseExit()
{
   int t_pos = g_cachedPositionCount, c_type = g_cachedPositionType;
   if(t_pos == 0 || c_type == -1) return;
   
   int signal = DualThrustSignal();
   
   // 反向信号出场
   if((c_type == POSITION_TYPE_BUY && signal == -1) ||
      (c_type == POSITION_TYPE_SELL && signal == 1))
   {
      double b = accInfo.Balance(); 
      CloseAllPositions(); 
      ReportFinancials("🔄 DT反向信号出场", b);
   }
}

//+------------------------------------------------------------------+
void ManageTrailingStop(int count, double profit_pct)
{
   if(count <= 0 || !InpUseTrailingStop) return;
   int tradeDir = g_cachedPositionType;
   if(tradeDir == -1) return;

   symInfo.RefreshRates();
   double curPrice = (tradeDir == POSITION_TYPE_BUY) ? symInfo.Bid() : symInfo.Ask();
   double basePrice = (g_firstEntryPrice > 0) ? g_firstEntryPrice : 0;
   if(basePrice <= 0) return;

   double trailDist = InpUseATRForTrail && g_currentAtr > 0 ? 
                      g_currentAtr * InpTrailATRMultiplier : basePrice * (InpTrailDistancePct / 100.0);

   if(!g_isTrailActive)
   {
      if(profit_pct >= InpTrailActivatePct)
      {
         g_isTrailActive = true;
         g_trailingStopLevel = NormalizePrice((tradeDir == POSITION_TYPE_BUY) ? curPrice - trailDist : curPrice + trailDist);
         Print("🛡️ 移动止损激活: ", g_trailingStopLevel);
      }
   }
   else
   {
      if(tradeDir == POSITION_TYPE_BUY)
      {
         double newLevel = NormalizePrice(curPrice - trailDist);
         if(newLevel > g_trailingStopLevel) g_trailingStopLevel = newLevel;
         if(curPrice <= g_trailingStopLevel)
         { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🛡️ 多单追踪止损", b); }
      }
      else
      {
         double newLevel = NormalizePrice(curPrice + trailDist);
         if(newLevel < g_trailingStopLevel) g_trailingStopLevel = newLevel;
         if(curPrice >= g_trailingStopLevel)
         { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🛡️ 空单追踪止损", b); }
      }
   }
}

//+------------------------------------------------------------------+
void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;
   
   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave || !InpStrictPartialLock) 
      { 
         double b = accInfo.Balance(); 
         CloseAllPositions();
         HighestProfitPct = 0.0; 
         hasPartialThisWave = true; 
         ReportFinancials("⚔️ HWM保本对切", b); 
      }
   }
   
   ManageTrailingStop(count, profit_pct);
}

//+------------------------------------------------------------------+
bool IsHighRiskWindow(MqlDateTime &t)
{
   if(t.day_of_week == 0 || t.day_of_week == 6) return true;
   if(t.day_of_week == 5 && t.hour >= 20) return true;
   if(t.day_of_week == 1 && t.hour < 8) return true;
   symInfo.RefreshRates(); 
   return (SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread * 2);
}

//+------------------------------------------------------------------+
string URLEncode(string str)
{
   string result = ""; uchar chars[]; 
   int count = StringToCharArray(str, chars, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i=0; i<count-1; i++) 
   {
      uchar c = chars[i];
      if((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0' && c<='9') || 
         c=='-' || c=='_' || c=='.' || c=='~') result += StringFormat("%c", c);
      else if(c == ' ') result += "+"; 
      else result += StringFormat("%%%02X", c);
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
void ReportFinancials(string baseMsg, double bal_before=0)
{
   double bal_after = accInfo.Balance();
   double delta = (bal_before > 0) ? (bal_after - bal_before) : 0;
   double dailyTotal = bal_after - DailyStartBalance; 
   string emoji = (delta >= 0) ? "💰 净利: +" : "💀 战损: -";
   string finalMsg = baseMsg + "\n" + emoji + DoubleToString(MathAbs(delta), 2) + 
                     "\n今日: " + DoubleToString(dailyTotal, 2);
   SendTelegramMessage(finalMsg);
}

//+------------------------------------------------------------------+
void OnTick()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || 
      !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)) return;
      
   symInfo.RefreshRates();
   
   if(BarsCalculated(h_atr) < 60 || BarsCalculated(h_ema576) < 576 || 
      BarsCalculated(h_vol) < 22) return;
   
   static bool isFirstTick = true; 
   bool isNewBarFlag = IsNewBar();
   bool shouldRunBarLogic = (isFirstTick || isNewBarFlag);
   
   g_tickCounter++; 
   
   if(shouldRunBarLogic) 
   { 
      if(!UpdateIndicators()) return; 
      RefreshSignalCache();
   }
   
   MqlDateTime tInfo; TimeCurrent(tInfo);
   
   if(tInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance(); 
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance); 
      GlobalVariableSet(GV_DateKey, tInfo.day_of_year);
      DailyLossTriggered = false; HighestProfitPct = 0.0; hasPartialThisWave = false; 
      g_tradesToday = 0; g_firstEntryPrice = 0.0; g_cachedPositionCount = -1; 
      g_tickCounter = 0; g_marginFailUntil = 0; g_lastPeriodicReport = 0; 
      g_lastIndicatorUpdate = 0;
      lastDayOfYear = tInfo.day_of_year;
   }
   
   if(DailyLossTriggered) return;
   
   bool isHighRiskNow = IsHighRiskWindow(tInfo);
   
   if(g_cachedPositionCount == -1 || g_tickCounter % CACHE_REFRESH_INTERVAL == 0) 
      RefreshPositionCache();
   
   int t_pos = g_cachedPositionCount, c_type = g_cachedPositionType;
   double c_profit = g_cachedProfitPct;
   
   if(t_pos == 0)
   {
      HighestProfitPct = 0.0; hasPartialThisWave = false; 
      g_isTrailActive = false; g_trailingStopLevel = 0.0; g_firstEntryPrice = 0.0; 
      g_cachedPositionType = -1;
      if(isHighRiskNow) { g_isHighRiskWindow = true; return; }
      g_isHighRiskWindow = false;
   }
   else
   {
      g_isHighRiskWindow = isHighRiskNow;
   }
   
   double eq = accInfo.Equity();
   
   if(InpFridayExit && tInfo.day_of_week == 5 && tInfo.hour >= 22 && t_pos > 0) 
   { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚩周末避险", b); return; }
   
   if(DailyStartBalance > 0 && (eq - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   { if(t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("💥极寒熔断", b); } 
     DailyLossTriggered = true; return; }
   
   if(t_pos > 0) 
   {
      if(InpUseReverseExit) CheckReverseExit();
      ManageDynamicArmor(t_pos, c_profit);
   }
   
   if(InpUsePeriodicReport && t_pos > 0 && TimeCurrent() - g_lastPeriodicReport >= InpReportIntervalMinutes * 60)
   { SendTelegramMessage("📋 持仓" + IntegerToString(t_pos) + "层 | 浮盈" + DoubleToString(c_profit,2) + "%"); 
     g_lastPeriodicReport = TimeCurrent(); }
   
   if(!shouldRunBarLogic) return; 
   
   if(t_pos == 0 && tInfo.hour >= InpStartHour && tInfo.hour < InpEndHour)
      CheckEntry();
   
   if(isFirstTick) isFirstTick = false; 
}
//+------------------------------------------------------------------+