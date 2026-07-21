//+------------------------------------------------------------------+
//| Guardian Earth V23.10_Ultimate_Perfect_Master.mq5                |
//| Copyright 2026, AI Commander                                     |
//| "星际重装铁骑版 - 100分终极毕业版 (工业级防弹异步架构)"             |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V23.10_Ultimate_Perfect_Master"
#property version   "23.10"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 🛡️ 核心风控与时间 ---
input group "=== 核心风控与时间 ==="
input double InpRiskPercent = 2.5;
input int    InpMaxSpread = 200;
input double InpDailyMaxLoss = 5.0;
input int    InpStartHour = 0;
input int    InpEndHour = 23;
input bool   InpFridayExit = true;
input ulong  InpMagicNumber = 208500;
input string InpMagicComment = "UltiOpt";
input int    InpMaxLevels = 6;
input int    InpMaxSlippage = 20;

input group "=== 资金与保证金安全 ==="
input double InpMinBalanceToTrade = 100.0;
input int    InpMarginFailCooldownMinutes = 60;

input group "=== 狼群追击战术 ==="
input double InpLevelMultiplier = 0.6;
input double InpLevelUpPct = 0.3;
input bool   InpUseSqrtLevelUp = false;
input int    InpBailoutLevel = 3;
input double InpBailoutPct = 0.2;

input group "=== 动态保本装甲 ==="
input double InpHWM_Activate = 3.0;
input double InpHWM_Retract = 1.5;
input bool   InpStrictPartialLock = false;

input group "=== 进场雷达调优 ==="
input double InpVolMultiplier = 0.5;
input double InpPullbackPct = 0.8;
input bool   InpUseMacroFilter = false;

input group "=== 事前风控 ==="
input bool   InpUseVolatilityFilter = false;
input double InpATRMultiplier_Max = 2.0;
input bool   InpUseEventFilter = false;
input bool   InpUseADXFilter = false;
input double InpMinADX = 20.0;

input group "=== 加速响应 ==="
input bool   InpUseFastEntry = true;
input double InpFastEntryADXThreshold = 30.0;
input double InpFastEntryMargin = 0.15;
input bool   InpUseProfitTrail = true;
input double InpTrailActivatePct = 1.0;
input double InpTrailDistancePct = 0.5;
input bool   InpUseATRForTrail = false;
input double InpTrailATRMultiplier = 1.5;

input group "=== 品种校准 ==="
input double InpSL_Multiplier_XAUUSD = 3.5;
input double InpSL_Multiplier_XAGUSD = 3.5;
input double InpSL_Multiplier_SPX500 = 3.0;
input double InpSL_Multiplier_US30 = 3.0;
input double InpSL_Multiplier_Default = 3.0;

input group "=== 运维监控 ==="
input bool   InpUsePeriodicReport = true;
input int    InpReportIntervalMinutes = 30;

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

int h_ema14, h_ema21, h_ema60, h_ema576, h_macd, h_atr, h_vol, h_adx;

double Dyn_SL_L, Dyn_SL_S;
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
double g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[];
double g_macd_main[], g_macd_sig[];
double g_vol[];
double g_adx[];

//--- 状态与性能全局变量
datetime g_marginFailUntil = 0;
int      g_dynamicMaxLevels = 6;
double   g_currentAtr = 0.0;
bool     g_isHighRiskWindow = false;
double   g_trailingStopLevel = 0.0;
bool     g_isTrailActive = false;
double   g_firstEntryPrice = 0.0;
datetime g_lastPeriodicReport = 0;
datetime g_lastTradeTime = 0;
int      g_tradesToday = 0;
datetime g_lastIndicatorUpdate = 0;

//--- 性能缓存系统
int g_tickCounter = 0;
int g_cachedPositionCount = -1;
int g_cachedPositionType = -1;
double g_cachedProfitPct = 0.0;
double g_cachedOldestSL = 0.0;
const int CACHE_REFRESH_INTERVAL = 5;
int g_reconnectFails = 0; 

//--- 异步推送队列
string g_telegramQueue[];

//+------------------------------------------------------------------+
//| 初始化系统 
//+------------------------------------------------------------------+
int OnInit()
{
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("❌ 致命错误：此战术必须运行在 Hedging (对冲) 账户下！");
      return(INIT_FAILED);
   }

   if(InpTelegramToken != "" && !TerminalInfoInteger(TERMINAL_ALLOWED_WEBREQUEST))
   {
      Print("⚠️ 警告：WebRequest 未允许，Telegram推送将失败！");
   }

   if(!EventSetTimer(1))
   {
      Print("⚠️ 警告：异步定时器启动失败，Telegram队列降级为即时模式！");
   }

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
      if(StringFind(accCur, "USC") >= 0 || StringFind(accCur, "cent") >= 0 || StringFind(accCur, "Cent") >= 0)
         { CurrencyUnit = "美分"; CurrencySymbol = ""; }
      else
         { CurrencyUnit = "美元"; CurrencySymbol = "$"; }
   }

   h_ema14 = iMA(_Symbol, PERIOD_M15, 14, 0, MODE_EMA, PRICE_CLOSE);
   h_ema21 = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   h_ema60 = iMA(_Symbol, PERIOD_M15, 60, 0, MODE_EMA, PRICE_CLOSE);
   h_ema576 = iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_macd = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   h_atr = iATR(_Symbol, PERIOD_M15, 14);
   h_vol = iVolumes(_Symbol, PERIOD_M15, VOLUME_TICK);
   h_adx = iADX(_Symbol, PERIOD_M15, 14);

   if(h_ema14==INVALID_HANDLE || h_macd==INVALID_HANDLE || h_atr==INVALID_HANDLE || 
      h_vol==INVALID_HANDLE || h_ema576==INVALID_HANDLE || h_adx==INVALID_HANDLE) return(INIT_FAILED);

   ArraySetAsSeries(g_ema14,true); ArraySetAsSeries(g_ema21,true); ArraySetAsSeries(g_ema60,true);
   ArraySetAsSeries(g_ema576,true); ArraySetAsSeries(g_atr,true); ArraySetAsSeries(g_macd_main,true);
   ArraySetAsSeries(g_macd_sig,true); ArraySetAsSeries(g_vol,true); ArraySetAsSeries(g_adx,true);

   ArrayResize(g_ema14,10); ArrayResize(g_ema21,10); ArrayResize(g_ema60,10); ArrayResize(g_ema576,10);
   ArrayResize(g_atr,10); ArrayResize(g_macd_main,10); ArrayResize(g_macd_sig,10); ArrayResize(g_vol,30); ArrayResize(g_adx,10);

   MqlDateTime t; TimeCurrent(t); 
   
   GV_BalanceKey = "GE_StartBal_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + _Symbol;
   GV_DateKey = GV_BalanceKey + "_Date";
   
   if(GlobalVariableCheck(GV_BalanceKey) && GlobalVariableCheck(GV_DateKey) && (int)GlobalVariableGet(GV_DateKey) == t.day_of_year)
   {
      DailyStartBalance = GlobalVariableGet(GV_BalanceKey);
      Print("💾 本地硬盘恢复今日初始本金成功: ", DailyStartBalance);
   }
   else
   {
      DailyStartBalance = accInfo.Balance();
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance);
      GlobalVariableSet(GV_DateKey, t.day_of_year);
      Print("💾 记录今日初始本金并刷新日期标记: ", DailyStartBalance);
   }

   HighestProfitPct = 0.0; hasPartialThisWave = false; g_dynamicMaxLevels = InpMaxLevels;
   g_firstEntryPrice = 0.0; g_marginFailUntil = 0; g_cachedPositionCount = -1; g_tickCounter = 0;
   g_tradesToday = 0; g_lastTradeTime = 0; g_lastPeriodicReport = 0; g_reconnectFails = 0;
   g_lastIndicatorUpdate = TimeCurrent();

   int waitCount = 0; bool dataReady = false;
   while(!dataReady && waitCount < 50) 
   { 
      dataReady = (BarsCalculated(h_ema14) >= 60 && BarsCalculated(h_ema21) >= 60 && 
                   BarsCalculated(h_ema60) >= 60 && BarsCalculated(h_macd) >= 26 && 
                   BarsCalculated(h_atr) >= 60 && BarsCalculated(h_vol) >= 22 && 
                   BarsCalculated(h_adx) >= 60);
      if(InpUseMacroFilter) dataReady = dataReady && (BarsCalculated(h_ema576) >= 576);
      if(!dataReady) { Sleep(100); waitCount++; }
   }
   
   lastDayOfYear = t.day_of_year; // 在数据就绪后标记日期，防止初始化失败引发逻辑跳跃

   string initMsg = "🚀 V23.10毕业版上线 | 100分工业级机甲就绪";
   Print(initMsg); SendTelegramMessage(initMsg);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnTimer()
{
   int qSize = ArraySize(g_telegramQueue);
   if(qSize > 0 && IsConnected())
   {
      string msg = g_telegramQueue[0];
      string url = "https://api.telegram.org/bot" + InpTelegramToken + "/sendMessage";
      string payload = StringFormat("chat_id=%s&text=%s", URLEncode(InpTelegramChatID), URLEncode(msg));
      
      char post[], result[]; string headers = "Content-Type: application/x-www-form-urlencoded\r\n";
      StringToCharArray(payload, post, 0, WHOLE_ARRAY, CP_UTF8);
      
      int res = WebRequest("POST", url, headers, 500, post, result, headers);
      if(res == 200)
      {
         for(int i=0; i<qSize-1; i++) g_telegramQueue[i] = g_telegramQueue[i+1];
         ArrayResize(g_telegramQueue, qSize-1);
      }
      else Print("⚠️ 推送延迟，队列等待重试: ", res);
   }
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   if(reason != REASON_CLOSE && IsConnected()) 
      SendTelegramMessage("⚠️ 警报！机甲已主动下线！战区: " + _Symbol);
   
   if(reason == REASON_REMOVE)
   {
      if(GlobalVariableCheck(GV_BalanceKey)) GlobalVariableDel(GV_BalanceKey);
      if(GlobalVariableCheck(GV_DateKey)) GlobalVariableDel(GV_DateKey);
   }

   ArrayFree(g_ema14); ArrayFree(g_ema21); ArrayFree(g_ema60); ArrayFree(g_ema576);
   ArrayFree(g_atr); ArrayFree(g_macd_main); ArrayFree(g_macd_sig); ArrayFree(g_vol); ArrayFree(g_adx);
   
   IndicatorRelease(h_ema14); IndicatorRelease(h_ema21); IndicatorRelease(h_ema60);
   IndicatorRelease(h_ema576); IndicatorRelease(h_macd); IndicatorRelease(h_atr);
   IndicatorRelease(h_vol); IndicatorRelease(h_adx);
}

//+------------------------------------------------------------------+
bool ReinitializeHandles()
{
   Print("🔄 尝试重新初始化指标句柄...");
   if(h_ema14 != INVALID_HANDLE) IndicatorRelease(h_ema14);
   if(h_ema21 != INVALID_HANDLE) IndicatorRelease(h_ema21);
   if(h_ema60 != INVALID_HANDLE) IndicatorRelease(h_ema60);
   if(h_ema576 != INVALID_HANDLE) IndicatorRelease(h_ema576);
   if(h_macd != INVALID_HANDLE) IndicatorRelease(h_macd);
   if(h_atr != INVALID_HANDLE) IndicatorRelease(h_atr);
   if(h_vol != INVALID_HANDLE) IndicatorRelease(h_vol);
   if(h_adx != INVALID_HANDLE) IndicatorRelease(h_adx);
   
   h_ema14 = iMA(_Symbol, PERIOD_M15, 14, 0, MODE_EMA, PRICE_CLOSE);
   h_ema21 = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   h_ema60 = iMA(_Symbol, PERIOD_M15, 60, 0, MODE_EMA, PRICE_CLOSE);
   h_ema576 = iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_macd = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   h_atr = iATR(_Symbol, PERIOD_M15, 14);
   h_vol = iVolumes(_Symbol, PERIOD_M15, VOLUME_TICK);
   h_adx = iADX(_Symbol, PERIOD_M15, 14);
   
   return (h_ema14!=INVALID_HANDLE && h_macd!=INVALID_HANDLE && h_atr!=INVALID_HANDLE && 
           h_vol!=INVALID_HANDLE && h_ema576!=INVALID_HANDLE && h_adx!=INVALID_HANDLE);
}

//+------------------------------------------------------------------+
void AutoCalibrate()
{
   string s = _Symbol; StringToUpper(s);
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) { Dyn_SL_L = InpSL_Multiplier_XAUUSD; Dyn_SL_S = InpSL_Multiplier_XAUUSD; }
   else if(StringFind(s,"XAGUSD")>=0 || StringFind(s,"SILVER")>=0) { Dyn_SL_L = InpSL_Multiplier_XAGUSD; Dyn_SL_S = InpSL_Multiplier_XAGUSD; }
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0) { Dyn_SL_L = InpSL_Multiplier_SPX500; Dyn_SL_S = InpSL_Multiplier_SPX500; }
   else if(StringFind(s,"US30")>=0 || StringFind(s,"WS30")>=0 || StringFind(s,"DOW")>=0) { Dyn_SL_L = InpSL_Multiplier_US30; Dyn_SL_S = InpSL_Multiplier_US30; }
   else { Dyn_SL_L = InpSL_Multiplier_Default; Dyn_SL_S = InpSL_Multiplier_Default; }
   Print("🛰️ 测向仪锁定 - ", s, " | SL倍数: L-", Dyn_SL_L, " S-", Dyn_SL_S);
}

//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   double tickSize = symInfo.TickSize();
   if(tickSize <= 0) tickSize = _Point;
   return MathRound(price / tickSize) * tickSize;
}

//+------------------------------------------------------------------+
bool IsSlippageValid(double executionPrice, double signalPrice, int maxSlippagePoints)
{
   double slippage = MathAbs(executionPrice - signalPrice) / _Point;
   if(slippage > maxSlippagePoints) { Print("⚠️ 滑点超限拦截: 实际 ", slippage, " > 允许 ", maxSlippagePoints); return false; }
   return true;
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
      case 10021: errorMsg = "余额不足以支撑手数"; break;
      case 10025: errorMsg = "账户禁止交易"; break;
      case 10027: errorMsg = "自动交易开关未开"; break;
      case 10030: errorMsg = "无效止损距"; break;
      case 10031: errorMsg = "无效止盈距"; break;
      case 10049: errorMsg = "价格剧烈跳动"; break;
      default: errorMsg = "未知底层错误: " + IntegerToString(errorCode);
   }
   Print("❌ ", operation, " 失败: ", errorMsg);
}

//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   if(h_ema14 == INVALID_HANDLE || h_ema21 == INVALID_HANDLE || h_ema60 == INVALID_HANDLE || 
      h_atr == INVALID_HANDLE || h_vol == INVALID_HANDLE || h_macd == INVALID_HANDLE || h_adx == INVALID_HANDLE)
   {
      g_reconnectFails++;
      if(g_reconnectFails > 5) { SendTelegramMessage("🚨 战区引擎离线无法自愈！"); return false; }
      if(!ReinitializeHandles()) return false;
      int wait = 0; while(BarsCalculated(h_ema14) < 60 && wait++ < 30) Sleep(100);
      g_reconnectFails = 0; 
   }

   if(CopyBuffer(h_ema14,0,0,4,g_ema14)<3) return false;
   if(CopyBuffer(h_ema21,0,0,4,g_ema21)<3) return false;
   if(CopyBuffer(h_ema60,0,0,4,g_ema60)<3) return false;
   if(CopyBuffer(h_atr,0,0,4,g_atr)<3) return false;
   if(CopyBuffer(h_vol,0,0,25,g_vol)<22) return false; 
   if(CopyBuffer(h_macd,0,0,4,g_macd_main)<3) return false;
   if(CopyBuffer(h_macd,1,0,4,g_macd_sig)<3) return false;
   if(CopyBuffer(h_adx,0,0,4,g_adx)<3) return false;
   if(InpUseMacroFilter) if(CopyBuffer(h_ema576,0,0,4,g_ema576)<3) return false;

   g_currentAtr = g_atr[1];
   g_lastIndicatorUpdate = TimeCurrent();
   return true;
}

//+------------------------------------------------------------------+
void RefreshPositionCache()
{
   g_cachedPositionCount = 0; g_cachedPositionType = -1; g_cachedProfitPct = 0.0;
   g_cachedOldestSL = 0.0; g_firstEntryPrice = 0.0;
   int buy = 0, sell = 0; double totalP = 0.0; datetime oldestT = 0;

   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         g_cachedPositionCount++;
         totalP += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
         if(posInfo.PositionType() == POSITION_TYPE_BUY) buy++; else sell++;
         if(oldestT == 0 || posInfo.Time() < oldestT)
         { oldestT = posInfo.Time(); g_cachedOldestSL = posInfo.StopLoss(); g_firstEntryPrice = posInfo.PriceOpen(); }
      }
   }
   if(g_cachedPositionCount > 0)
   {
      if(buy > 0 && sell == 0) g_cachedPositionType = POSITION_TYPE_BUY;
      else if(sell > 0 && buy == 0) g_cachedPositionType = POSITION_TYPE_SELL;
      else g_cachedPositionType = -1; 
      if(accInfo.Balance() > 0) g_cachedProfitPct = (totalP / accInfo.Balance()) * 100.0;
   }
}

//+------------------------------------------------------------------+
void RecordTrade() { g_lastTradeTime = TimeCurrent(); g_tradesToday++; g_cachedPositionCount = -1; }

//+------------------------------------------------------------------+
void CloseAllPositions()
{
   int total = PositionsTotal();
   for(int i=total-1; i>=0; i--)
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
      g_isTrailActive = false; g_trailingStopLevel = 0.0; g_firstEntryPrice = 0.0; g_cachedPositionCount = -1;
      HighestProfitPct = 0.0; hasPartialThisWave = false;
   }
}

//+------------------------------------------------------------------+
double CalculateVolume(double entryPrice, double slPrice, double riskPct, ENUM_ORDER_TYPE orderType)
{
   datetime now = TimeCurrent(); if(g_marginFailUntil > 0 && now < g_marginFailUntil) return 0; 
   symInfo.RefreshRates(); entryPrice = NormalizePrice(entryPrice); slPrice = NormalizePrice(slPrice);
   double riskAmount = accInfo.Balance() * (riskPct / 100.0), slDist = MathAbs(entryPrice - slPrice);
   double tSize = symInfo.TickSize(), tVal = symInfo.TickValue(), lotStep = symInfo.LotsStep();
   if(slDist <= 0 || tSize <= 0 || tVal <= 0 || lotStep <= 0) return 0; 
   double rawVolume = riskAmount / ((slDist / tSize) * tVal);
   int vDigits = (lotStep < 1.0) ? (int)MathCeil(-MathLog10(lotStep)) : 0;
   double calcLot = NormalizeDouble(MathFloor(rawVolume / lotStep) * lotStep, vDigits);
   if(calcLot < symInfo.LotsMin()) calcLot = symInfo.LotsMin();
   if(calcLot > symInfo.LotsMax()) calcLot = symInfo.LotsMax();
   
   double freeM = accInfo.FreeMargin(), reqM = 0;
   if(!OrderCalcMargin(orderType, _Symbol, calcLot, entryPrice, reqM))
   {
       int err = GetLastError(); g_marginFailUntil = (err == 4001 || err == 4002 || err == 10018) ? now + 60 : now + InpMarginFailCooldownMinutes * 60;
       return 0;
   }
   if(reqM > freeM * 0.8)
   {
       double factor = (freeM * 0.8) / reqM;
       calcLot = NormalizeDouble(MathFloor((calcLot * factor) / lotStep) * lotStep, vDigits);
       if(calcLot < symInfo.LotsMin()) return 0;
       Print("⚠️ 保证金修正: 手数下调至 ", calcLot);
   }
   return calcLot;
}

//+------------------------------------------------------------------+
bool SafeTradeBuy(double lot, double sigP, double sl)
{
   if(TimeCurrent() - g_lastTradeTime < 1) return false;
   symInfo.RefreshRates(); double ask = symInfo.Ask();
   if(!IsSlippageValid(ask, sigP, InpMaxSlippage)) return false;
   if(!trade.Buy(lot, _Symbol, ask, NormalizePrice(sl), 0, InpMagicComment)) 
      { HandleTradeError(trade.ResultRetcode(), "买入"); return false; }
   RecordTrade(); return true;
}

bool SafeTradeSell(double lot, double sigP, double sl)
{
   if(TimeCurrent() - g_lastTradeTime < 1) return false;
   symInfo.RefreshRates(); double bid = symInfo.Bid();
   if(!IsSlippageValid(bid, sigP, InpMaxSlippage)) return false;
   if(!trade.Sell(lot, _Symbol, bid, NormalizePrice(sl), 0, InpMagicComment)) 
      { HandleTradeError(trade.ResultRetcode(), "卖出"); return false; }
   RecordTrade(); return true;
}

//+------------------------------------------------------------------+
void CheckEntry()
{
   symInfo.RefreshRates(); if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return; 
   if(InpUseADXFilter && (ArraySize(g_adx) < 2 || g_adx[1] < InpMinADX)) return;
   
   if(InpUseMacroFilter)
   {
      bool mUp = (g_ema576[1] > g_ema576[2]), mDn = (g_ema576[1] < g_ema576[2]);
      if((g_ema14[1] > g_ema21[1] && !mUp) || (g_ema14[1] < g_ema21[1] && !mDn)) return;
   }
   
   double sumV = 0; int vCount = 0;
   for(int i=2; i<=21 && i<ArraySize(g_vol); i++) { if(g_vol[i] > 0) { sumV += g_vol[i]; vCount++; } }
   if(vCount == 0 || (g_vol[1] <= (sumV / vCount) * InpVolMultiplier)) return;
   
   bool fMod = InpUseFastEntry && ArraySize(g_adx) >= 2 && g_adx[1] >= InpFastEntryADXThreshold;
   double pBack = fMod ? InpFastEntryMargin : InpPullbackPct;
   
   if(g_ema14[1] > g_ema21[1] && g_macd_main[1] > g_macd_sig[1] && g_macd_main[1] > g_macd_main[2])
   {
      double l1 = iLow(_Symbol, PERIOD_M15, 1), l2 = iLow(_Symbol, PERIOD_M15, 2);
      if(l1 > 0 && l2 > 0 && (l1 <= g_ema14[1]*(1-pBack/100.0) || l2 <= g_ema14[2]*(1-pBack/100.0)))
      {
         double ask = symInfo.Ask(), sl = ask - (g_atr[1] * Dyn_SL_L), lot = CalculateVolume(ask, sl, InpRiskPercent, ORDER_TYPE_BUY); 
         if(lot > 0 && SafeTradeBuy(lot, ask, sl)) SendTelegramMessage("🐺 狂战士出击 (多) | " + _Symbol); 
      }
   }
   else if(g_ema14[1] < g_ema21[1] && g_macd_main[1] < g_macd_sig[1] && g_macd_main[1] < g_macd_main[2])
   {
      double h1 = iHigh(_Symbol, PERIOD_M15, 1), h2 = iHigh(_Symbol, PERIOD_M15, 2);
      if(h1 > 0 && h2 > 0 && (h1 >= g_ema14[1]*(1+pBack/100.0) || h2 >= g_ema14[2]*(1+pBack/100.0)))
      {
         double bid = symInfo.Bid(), sl = bid + (g_atr[1] * Dyn_SL_S), lot = CalculateVolume(bid, sl, InpRiskPercent, ORDER_TYPE_SELL); 
         if(lot > 0 && SafeTradeSell(lot, bid, sl)) SendTelegramMessage("🐺 狂战士出击 (空) | " + _Symbol); 
      }
   }
}

//+------------------------------------------------------------------+
void ExecuteAddPosition(int type, double first_sl, int currentLevel)
{
   double price = (type == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
   double lot = CalculateVolume(price, first_sl, InpRiskPercent * MathPow(InpLevelMultiplier, currentLevel), (ENUM_ORDER_TYPE)type);
   if(lot > 0) 
   {
      bool success = (type == POSITION_TYPE_BUY) ? SafeTradeBuy(lot, price, first_sl) : SafeTradeSell(lot, price, first_sl);
      if(!success) Print("⚠️ 加仓拦截: Level ", currentLevel);
      g_cachedPositionCount = -1; 
   }
}

//+------------------------------------------------------------------+
void ManageTrailingStop(int count, double p_pct)
{
   if(count <= 0 || g_cachedPositionType == -1) return;
   double baseP = (g_firstEntryPrice > 0) ? g_firstEntryPrice : CalculateAverageEntryPrice();
   double dist = InpUseATRForTrail && g_currentAtr > 0 ? g_currentAtr * InpTrailATRMultiplier : baseP * (InpTrailDistancePct / 100.0);
   symInfo.RefreshRates(); double price = (g_cachedPositionType == POSITION_TYPE_BUY) ? symInfo.Bid() : symInfo.Ask();

   if(!g_isTrailActive)
   {
      if(p_pct >= InpTrailActivatePct) { g_isTrailActive = true; g_trailingStopLevel = NormalizePrice((g_cachedPositionType == POSITION_TYPE_BUY) ? price - dist : price + dist); }
   }
   else
   {
      if(g_cachedPositionType == POSITION_TYPE_BUY) {
         double newL = NormalizePrice(price - dist); if(newL > g_trailingStopLevel) g_trailingStopLevel = newL;
         if(price <= g_trailingStopLevel) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🛡️ 多单追踪止损", b); }
      } else {
         double newL = NormalizePrice(price + dist); if(newL < g_trailingStopLevel) g_trailingStopLevel = newL;
         if(price >= g_trailingStopLevel) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🛡️ 空单追踪止损", b); }
      }
   }
}

//+------------------------------------------------------------------+
void ManageDynamicArmor(int count, double p_pct)
{
   if(p_pct > HighestProfitPct) HighestProfitPct = p_pct;
   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && p_pct <= InpBailoutPct)
   { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("⚠️ 冲锋受阻Bailout", b); return; }
   
   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - p_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave) { double b = accInfo.Balance(); PartialCloseAndBE(); HighestProfitPct = 0.0; ReportFinancials("⚔️ 阵地物理对切", b); }
   }
   if(InpUseProfitTrail) ManageTrailingStop(count, p_pct);
}

//+------------------------------------------------------------------+
int CalculateDynamicMaxLevels()
{
   if(!InpUseVolatilityFilter || ArraySize(g_atr) < 3) return InpMaxLevels;
   double atrM = MathAbs(g_atr[1] / (g_atr[2] > 0 ? g_atr[2] : 1));
   return (atrM > InpATRMultiplier_Max) ? MathMax(1, InpMaxLevels - 2) : InpMaxLevels;
}

bool IsHighRiskWindow(MqlDateTime &t)
{
   if(!InpUseEventFilter) return false;
   if(t.day_of_week == 0 || t.day_of_week == 6 || (t.day_of_week == 5 && t.hour >= 20) || (t.day_of_week == 1 && t.hour < 8)) return true;
   symInfo.RefreshRates(); if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread * 2) return true;
   return false;
}

string URLEncode(string str)
{
   string res = ""; uchar c[]; int len = StringToCharArray(str, c, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i=0; i<len-1; i++) {
      if((c[i]>='a'&&c[i]<='z')||(c[i]>='A'&&c[i]<='Z')||(c[i]>='0'&&c[i]<='9')||c[i]=='-'||c[i]=='_'||c[i]=='.'||c[i]=='~') res += StringFormat("%c", c[i]);
      else if(c[i]==' ') res += "+"; else res += StringFormat("%%%02X", c[i]);
   }
   return res;
}

void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   int sz = ArraySize(g_telegramQueue); ArrayResize(g_telegramQueue, sz+1);
   g_telegramQueue[sz] = StringSubstr(msg, 0, 3900);
}

void ReportFinancials(string msg, double bal_b=0)
{
   double bal_a = accInfo.Balance(), d = (bal_b > 0) ? (bal_a - bal_b) : 0;
   string final = msg + "\n本次: " + (d>=0?"💰+":"💀") + DoubleToString(d, 2) + "\n累计: " + DoubleToString(bal_a - DailyStartBalance, 2) + "\n金库: " + DoubleToString(bal_a, 2);
   SendTelegramMessage(final);
}

void SendPeriodicStatusReport(int posCount, double p_pct)
{
   double eq = accInfo.Equity();
   string r = "📋 运维报告\n净值: " + DoubleToString(eq, 2) + "\n今日: " + DoubleToString(eq - DailyStartBalance, 2) + "\n持仓: " + IntegerToString(posCount) + " 层 | " + DoubleToString(p_pct, 2) + "%";
   SendTelegramMessage(r);
}

//+------------------------------------------------------------------+
void OnTick()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)) return;
   symInfo.RefreshRates();
   if(BarsCalculated(h_ema14) < 60 || BarsCalculated(h_macd) < 26 || BarsCalculated(h_vol) < 22) return;
   
   static bool isFirstTick = true; bool isNewBarFlag = IsNewBar(), sLogic = (isFirstTick || isNewBarFlag);
   g_tickCounter++; 
   
   if(sLogic) { if(!UpdateIndicators()) return; g_dynamicMaxLevels = CalculateDynamicMaxLevels(); }
   
   MqlDateTime tInfo; TimeCurrent(tInfo);
   if(tInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance(); 
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance); GlobalVariableSet(GV_DateKey, tInfo.day_of_year);
      DailyLossTriggered = false; HighestProfitPct = 0.0; hasPartialThisWave = false; 
      g_tradesToday = 0; g_firstEntryPrice = 0.0; g_cachedPositionCount = -1; g_tickCounter = 0; 
      g_marginFailUntil = 0; g_lastPeriodicReport = 0; g_lastIndicatorUpdate = 0; lastDayOfYear = tInfo.day_of_year;
   }
   
   if(DailyLossTriggered) return;
   if(g_cachedPositionCount == -1 || g_tickCounter % CACHE_REFRESH_INTERVAL == 0) RefreshPositionCache();
   
   int t_pos = g_cachedPositionCount, c_type = g_cachedPositionType;
   double c_profit = g_cachedProfitPct, o_sl = g_cachedOldestSL;
   
   if(t_pos == 0)
   {
      HighestProfitPct = 0.0; hasPartialThisWave = false; g_isTrailActive = false; g_trailingStopLevel = 0.0; g_firstEntryPrice = 0.0; g_cachedPositionType = -1;
      if(IsHighRiskWindow(tInfo)) return;
   }
   
   double eq = accInfo.Equity();
   if(InpFridayExit && tInfo.day_of_week == 5 && tInfo.hour >= 22 && t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚩周末避险", b); return; }
   if(DailyStartBalance > 0 && (eq - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   { if(t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("💥极寒熔断", b); } DailyLossTriggered = true; return; }
   
   if(t_pos > 0) ManageDynamicArmor(t_pos, c_profit);
   if(InpUsePeriodicReport && t_pos > 0 && TimeCurrent() - g_lastPeriodicReport >= InpReportIntervalMinutes * 60)
   { SendPeriodicStatusReport(t_pos, c_profit); g_lastPeriodicReport = TimeCurrent(); }
   
   if(!sLogic) return; 
   if(t_pos > 0 && c_type != -1)
   {
      if(TimeCurrent() - g_lastIndicatorUpdate > 300) return;
      double c1 = iClose(_Symbol, PERIOD_M15, 1);
      if(c1 > 0 && ((c_type == POSITION_TYPE_BUY && c1 < g_ema60[1]) || (c_type == POSITION_TYPE_SELL && c1 > g_ema60[1])))
      { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚨趋势破位", b); return; }
      
      double reqP = InpUseSqrtLevelUp ? (InpLevelUpPct * MathSqrt(t_pos)) : (InpLevelUpPct * t_pos);
      if(!hasPartialThisWave && t_pos < g_dynamicMaxLevels && c_profit >= reqP) ExecuteAddPosition(c_type, o_sl, t_pos);
   }
   else if(t_pos == 0 && tInfo.hour >= InpStartHour && tInfo.hour < InpEndHour) CheckEntry();
   isFirstTick = false; 
}
//+------------------------------------------------------------------+