//+------------------------------------------------------------------+
//| Guardian Earth V24.00_Fusion_Masterpiece.mq5                     |
//| Copyright 2026, AI Commander                                     |
//| "星际重装铁骑版 - 终极融合典藏版 (V20.91+V23.10 完美融合)"         |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V24.00_Fusion_Masterpiece"
#property version   "24.00"
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
//| 检查网络连接状态 (MT5兼容)                                        |
//+------------------------------------------------------------------+
bool IsConnectedMT5()
{
   return TerminalInfoInteger(TERMINAL_CONNECTED) != 0;
}

//+------------------------------------------------------------------+
//| 初始化系统                                                        |
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
      Print("⚠️ 警告：WebRequest 未允许，Telegram推送将失败！请在工具->选项->EA交易中配置URL白名单。");
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

   if(h_ema14==INVALID_HANDLE || h_ema21==INVALID_HANDLE || h_ema60==INVALID_HANDLE || 
      h_ema576==INVALID_HANDLE || h_macd==INVALID_HANDLE || h_atr==INVALID_HANDLE || 
      h_vol==INVALID_HANDLE || h_adx==INVALID_HANDLE) return(INIT_FAILED);

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
   
   lastDayOfYear = t.day_of_year;

   string initMsg = "🚀 V24.00 终极融合典藏版启动 | V20.91+V23.10 完美融合";
   Print(initMsg); SendTelegramMessage(initMsg);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| 异步推送队列处理中心                                              |
//+------------------------------------------------------------------+
void OnTimer()
{
   int qSize = ArraySize(g_telegramQueue);
   if(qSize > 0 && IsConnectedMT5())
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
//| 反初始化                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   if(reason != REASON_CLOSE && IsConnectedMT5()) 
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
//| 重新初始化指标句柄                                                |
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
   
   return (h_ema14!=INVALID_HANDLE && h_ema21!=INVALID_HANDLE && h_ema60!=INVALID_HANDLE &&
           h_ema576!=INVALID_HANDLE && h_macd!=INVALID_HANDLE && h_atr!=INVALID_HANDLE && 
           h_vol!=INVALID_HANDLE && h_adx!=INVALID_HANDLE);
}

//+------------------------------------------------------------------+
//| 品种自动校准                                                      |
//+------------------------------------------------------------------+
void AutoCalibrate()
{
   string s = _Symbol; StringToUpper(s);
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) { Dyn_SL_L = InpSL_Multiplier_XAUUSD; Dyn_SL_S = InpSL_Multiplier_XAUUSD; }
   else if(StringFind(s,"XAGUSD")>=0 || StringFind(s,"SILVER")>=0) { Dyn_SL_L = InpSL_Multiplier_XAGUSD; Dyn_SL_S = InpSL_Multiplier_XAGUSD; }
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0) { Dyn_SL_L = InpSL_Multiplier_SPX500; Dyn_SL_S = InpSL_Multiplier_SPX500; }
   else if(StringFind(s,"US30")>=0 || StringFind(s,"WS30")>=0 || StringFind(s,"DOW")>=0) { Dyn_SL_L = InpSL_Multiplier_US30; Dyn_SL_S = InpSL_Multiplier_US30; }
   else { Dyn_SL_L = InpSL_Multiplier_Default; Dyn_SL_S = InpSL_Multiplier_Default; }
   Print("🛰️ 测向仪已锁定 - 战区: ", s, " | SL倍数: L-", Dyn_SL_L, " S-", Dyn_SL_S);
}

//+------------------------------------------------------------------+
//| 价格标准化                                                        |
//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   double tickSize = symInfo.TickSize();
   if(tickSize <= 0) tickSize = _Point;
   return MathRound(price / tickSize) * tickSize;
}

//+------------------------------------------------------------------+
//| 滑点校验                                                          |
//+------------------------------------------------------------------+
bool IsSlippageValid(double executionPrice, double signalPrice, int maxSlippagePoints)
{
   double slippage = MathAbs(executionPrice - signalPrice) / _Point;
   if(slippage > maxSlippagePoints) { Print("⚠️ 滑点超限拦截: 实际 ", slippage, " > 允许 ", maxSlippagePoints); return false; }
   return true;
}

//+------------------------------------------------------------------+
//| 交易错误处理                                                      |
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
      case 10030: errorMsg = "无效止损(止损位距离当前价格太近)"; break;
      case 10031: errorMsg = "无效止盈"; break;
      case 10049: errorMsg = "价格变化"; break;
      default: errorMsg = "未知错误: " + IntegerToString(errorCode);
   }
   Print("❌ ", operation, " 失败: ", errorMsg);
   if(errorCode == 10019 || errorCode == 10021 || errorCode == 10025 || errorCode == 10027)
      SendTelegramMessage("🚨 严重交易错误！\n操作: " + operation + "\n错误: " + errorMsg);
}

//+------------------------------------------------------------------+
//| 更新指标数据                                                      |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   if(h_ema14 == INVALID_HANDLE || h_ema21 == INVALID_HANDLE || h_ema60 == INVALID_HANDLE || 
      h_atr == INVALID_HANDLE || h_vol == INVALID_HANDLE || h_macd == INVALID_HANDLE || h_adx == INVALID_HANDLE ||
      (InpUseMacroFilter && h_ema576 == INVALID_HANDLE))
   {
      g_reconnectFails++;
      Print("❌ 指标句柄失效，尝试重新初始化 (第", g_reconnectFails, "次)...");
      if(g_reconnectFails > 5) { SendTelegramMessage("🚨 战区引擎离线无法自愈！"); return false; }
      if(!ReinitializeHandles()) return false;
      int wait = 0; while(BarsCalculated(h_ema14) < 60 && wait++ < 30) Sleep(100);
      if(BarsCalculated(h_ema14) < 60) { Print("⚠️ 重连后数据仍不足"); return false; }
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
//| 检查新K线                                                         |
//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime current = iTime(_Symbol, PERIOD_M15, 0);
   if(current != lastBarTime) { lastBarTime = current; return true; }
   return false;
}

//+------------------------------------------------------------------+
//| 刷新持仓缓存                                                      |
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
//| 交易频率检查                                                      |
//+------------------------------------------------------------------+
bool CanTradeNow()
{
   if(TimeCurrent() - g_lastTradeTime < 1) return false;
   return true;
}

//+------------------------------------------------------------------+
//| 记录交易                                                          |
//+------------------------------------------------------------------+
void RecordTrade()
{
   g_lastTradeTime = TimeCurrent(); g_tradesToday++;
   g_cachedPositionCount = -1;
   Print("📝 记录交易 #", g_tradesToday);
}

//+------------------------------------------------------------------+
//| 计算平均入场价                                                    |
//+------------------------------------------------------------------+
double CalculateAverageEntryPrice()
{
   double totalCost = 0, totalLots = 0;
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      { totalCost += posInfo.PriceOpen() * posInfo.Volume(); totalLots += posInfo.Volume(); }
   }
   return totalLots > 0 ? totalCost / totalLots : 0;
}

//+------------------------------------------------------------------+
//| 移动止损管理                                                      |
//+------------------------------------------------------------------+
void ManageTrailingStop(int count, double profit_pct)
{
   if(count <= 0) return;
   int tradeDir = g_cachedPositionType;
   if(tradeDir == -1) return;

   symInfo.RefreshRates();
   double curAsk = symInfo.Ask(), curBid = symInfo.Bid();
   double curPrice = (tradeDir == POSITION_TYPE_BUY) ? curBid : curAsk;
   double basePrice = (g_firstEntryPrice > 0) ? g_firstEntryPrice : CalculateAverageEntryPrice();
   if(basePrice <= 0) return;

   double trailDistanceAbs = InpUseATRForTrail && g_currentAtr > 0 ? g_currentAtr * InpTrailATRMultiplier : basePrice * (InpTrailDistancePct / 100.0);

   if(!g_isTrailActive)
   {
      if(profit_pct >= InpTrailActivatePct)
      {
         g_isTrailActive = true;
         g_trailingStopLevel = NormalizePrice((tradeDir == POSITION_TYPE_BUY) ? curPrice - trailDistanceAbs : curPrice + trailDistanceAbs);
         Print("🛡️ 移动止损激活 | 初始追踪位: ", DoubleToString(g_trailingStopLevel, _Digits));
      }
   }
   else
   {
      if(tradeDir == POSITION_TYPE_BUY)
      {
         double newTrailLevel = NormalizePrice(curPrice - trailDistanceAbs);
         if(newTrailLevel > g_trailingStopLevel) g_trailingStopLevel = newTrailLevel;
         if(curBid <= g_trailingStopLevel)
         {
            double bal = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🛡️ 多单移动止损触发！", bal);
         }
      }
      else
      {
         double newTrailLevel = NormalizePrice(curPrice + trailDistanceAbs);
         if(newTrailLevel < g_trailingStopLevel) g_trailingStopLevel = newTrailLevel;
         if(curAsk >= g_trailingStopLevel)
         {
            double bal = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🛡️ 空单移动止损触发！", bal);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 部分平仓与保本止损                                                |
//+------------------------------------------------------------------+
void PartialCloseAndBE()
{
   symInfo.RefreshRates();
   double volStep = symInfo.LotsStep(), minVol = symInfo.LotsMin();
   ulong tickets[]; double openPrices[]; long posTypes[]; double currentVols[]; double currentSLs[]; double currentTPs[];
   int total = PositionsTotal(), count = 0;

   ArrayResize(tickets, total); ArrayResize(openPrices, total); ArrayResize(posTypes, total);
   ArrayResize(currentVols, total); ArrayResize(currentSLs, total); ArrayResize(currentTPs, total);

   for(int i=total-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         tickets[count] = posInfo.Ticket(); openPrices[count] = posInfo.PriceOpen();
         posTypes[count] = posInfo.PositionType(); currentVols[count] = posInfo.Volume();
         currentSLs[count] = posInfo.StopLoss(); currentTPs[count] = posInfo.TakeProfit(); count++;
      }
   }

   long stops = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double stops_level = (stops > 0) ? (double)stops : 10.0;
   double safeLevel = MathAbs(stops_level * _Point);

   double curAsk = symInfo.Ask(), curBid = symInfo.Bid(); bool partialSuccess = false;

   for(int j=0; j<count; j++)
   {
      double safeTP = (currentTPs[j] > 0) ? NormalizePrice(currentTPs[j]) : 0;
      double beSL = NormalizePrice(openPrices[j]);

      if(posTypes[j] == POSITION_TYPE_BUY && currentSLs[j] < openPrices[j] && curBid > openPrices[j] + safeLevel)
         if(!trade.PositionModify(tickets[j], beSL, safeTP)) HandleTradeError(trade.ResultRetcode(), "保本止损");
      else if(posTypes[j] == POSITION_TYPE_SELL && currentSLs[j] > openPrices[j] && curAsk < openPrices[j] - safeLevel)
         if(!trade.PositionModify(tickets[j], beSL, safeTP)) HandleTradeError(trade.ResultRetcode(), "保本止损");

      double closeVol = MathFloor((currentVols[j] / 2.0) / volStep) * volStep;
      if(closeVol < minVol) closeVol = minVol;
      if(closeVol >= currentVols[j] - minVol/2.0) closeVol = MathMax(minVol, currentVols[j] - minVol);

      if(closeVol >= minVol && closeVol < currentVols[j])
         if(trade.PositionClosePartial(tickets[j], closeVol)) partialSuccess = true;
   }

   if(partialSuccess) { hasPartialThisWave = true; g_cachedPositionCount = -1; Print("⚔️ 物理对切完成"); }
}

//+------------------------------------------------------------------+
//| 清仓所有持仓                                                      |
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
      Print("⚠️ 侦测到 ", checkResidual, " 个残留订单，第 ", retry+1, " 次执行补枪强平！");
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
   else
   {
      Print("🚨 严重警告：多轮补枪后仍有 ", checkResidual, " 个未平仓订单，状态暂缓清零！");
      g_cachedPositionCount = -1;
   }
}

//+------------------------------------------------------------------+
//| 计算开仓手数                                                      |
//+------------------------------------------------------------------+
double CalculateVolume(double entryPrice, double slPrice, double riskPct, ENUM_ORDER_TYPE orderType)
{
   datetime now = TimeCurrent();
   if(g_marginFailUntil > 0 && now < g_marginFailUntil) return 0; 
   
   symInfo.RefreshRates(); 
   entryPrice = NormalizePrice(entryPrice); slPrice = NormalizePrice(slPrice);
   double riskAmount = accInfo.Balance() * (riskPct / 100.0);
   double slDistance = MathAbs(entryPrice - slPrice);
   
   double tickSize = symInfo.TickSize(), tickValue = symInfo.TickValue(), lotStep = symInfo.LotsStep();
   double minLot = symInfo.LotsMin(), maxLot = symInfo.LotsMax();
   
   if(slDistance <= 0 || tickSize <= 0 || tickValue <= 0 || lotStep <= 0) return 0; 
   
   double slPoints = slDistance / tickSize;
   double rawVolume = riskAmount / (slPoints * tickValue);
   int volDigits = (lotStep < 1.0) ? (int)MathCeil(-MathLog10(lotStep)) : 0;
   double calcVol = NormalizeDouble(MathFloor(rawVolume / lotStep) * lotStep, volDigits);
   
   if(calcVol < minLot) calcVol = minLot; if(calcVol > maxLot) calcVol = maxLot;
   
   double freeMargin = accInfo.FreeMargin(), marginRequired = 0;
   if(!OrderCalcMargin(orderType, _Symbol, calcVol, entryPrice, marginRequired))
   {
       int err = GetLastError();
       if(err == 4001 || err == 4002 || err == 10018) g_marginFailUntil = now + 60; 
       else g_marginFailUntil = now + InpMarginFailCooldownMinutes * 60;
       
       Print("❌ 保证金预演失败，错误码: ", err);
       return 0;
   }
   
   if(marginRequired > freeMargin * 0.8)
   {
       double originalVol = calcVol;
       double factor = (freeMargin * 0.8) / marginRequired;
       calcVol = NormalizeDouble(MathFloor((calcVol * factor) / lotStep) * lotStep, volDigits);
       if(calcVol < minLot) 
       { 
          Print("⚠️ 保证金严重不足，调整后小于最小手数，放弃开仓"); 
          return 0; 
       }
       Print("⚠️ 保证金不足，手数已从 ", originalVol, " 缩减至 ", calcVol);
   }
   return calcVol;
}

//+------------------------------------------------------------------+
//| 安全买入                                                          |
//+------------------------------------------------------------------+
bool SafeTradeBuy(double lot, double signalPrice, double sl)
{
   if(!CanTradeNow()) return false;
   symInfo.RefreshRates(); double ask = symInfo.Ask();
   if(!IsSlippageValid(ask, signalPrice, InpMaxSlippage)) return false;
   
   if(!trade.Buy(lot, _Symbol, ask, NormalizePrice(sl), 0, InpMagicComment)) 
      { HandleTradeError(trade.ResultRetcode(), "买入"); return false; }
   
   RecordTrade();
   return true;
}

//+------------------------------------------------------------------+
//| 安全卖出                                                          |
//+------------------------------------------------------------------+
bool SafeTradeSell(double lot, double signalPrice, double sl)
{
   if(!CanTradeNow()) return false;
   symInfo.RefreshRates(); double bid = symInfo.Bid();
   if(!IsSlippageValid(bid, signalPrice, InpMaxSlippage)) return false;
   
   if(!trade.Sell(lot, _Symbol, bid, NormalizePrice(sl), 0, InpMagicComment)) 
      { HandleTradeError(trade.ResultRetcode(), "卖出"); return false; }
   
   RecordTrade();
   return true;
}

//+------------------------------------------------------------------+
//| 入场信号检查                                                      |
//+------------------------------------------------------------------+
void CheckEntry()
{
   symInfo.RefreshRates(); 
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return; 
   
   if(InpUseADXFilter) 
   {
      if(ArraySize(g_adx) < 2) return;
      if(g_adx[1] < InpMinADX) return;
   }
   
   if(InpUseMacroFilter)
   {
      bool macroTrendUp = (g_ema576[1] > g_ema576[2]), macroTrendDown = (g_ema576[1] < g_ema576[2]);
      bool shortTrendUp = (g_ema14[1] > g_ema21[1]), shortTrendDown = (g_ema14[1] < g_ema21[1]);
      if(shortTrendUp && !macroTrendUp) return;
      if(shortTrendDown && !macroTrendDown) return;
   }
   
   double sumVol = 0; int validVolCount = 0;
   for(int i=2; i<=21 && i<ArraySize(g_vol); i++) { if(g_vol[i] > 0) { sumVol += g_vol[i]; validVolCount++; } }
   if(validVolCount == 0) return;
   
   double avgVol20 = sumVol / validVolCount;
   if(!(g_vol[1] > avgVol20 * InpVolMultiplier || g_vol[2] > avgVol20 * InpVolMultiplier)) return;
   
   bool isFastMode = InpUseFastEntry && ArraySize(g_adx) >= 2 && g_adx[1] >= InpFastEntryADXThreshold;
   double pullbackMargin = isFastMode ? InpFastEntryMargin : InpPullbackPct;
   double emaSpreadThreshold = isFastMode ? 0 : 1;
   
   bool longCondition = (g_ema14[1] > g_ema21[1]) && 
                        (!isFastMode || g_ema21[1] >= g_ema60[1] - emaSpreadThreshold * g_atr[1]) &&
                        g_macd_main[1] > g_macd_sig[1] && g_macd_main[1] > g_macd_main[2]; 
   
   if(longCondition)
   {
      double low1 = iLow(_Symbol, PERIOD_M15, 1), low2 = iLow(_Symbol, PERIOD_M15, 2);
      if(low1 <= 0 || low2 <= 0) return; 
      
      double pullbackLevel = g_ema14[1] * (1.0 - pullbackMargin/100.0), pullbackLevel2 = g_ema14[2] * (1.0 - pullbackMargin/100.0);
      
      if(low1 <= pullbackLevel || low2 <= pullbackLevel2)
      {
         double ask = symInfo.Ask(), sl = NormalizePrice(ask - (g_atr[1] * Dyn_SL_L)); 
         double lot = CalculateVolume(ask, sl, InpRiskPercent, ORDER_TYPE_BUY); 
         if(lot > 0)
         {
            if(SafeTradeBuy(lot, ask, sl)) SendTelegramMessage("🐺 狂战士出击 (多) | " + _Symbol); 
         }
      }
   }
   
   bool shortCondition = (g_ema14[1] < g_ema21[1]) && 
                         (!isFastMode || g_ema21[1] <= g_ema60[1] + emaSpreadThreshold * g_atr[1]) &&
                         g_macd_main[1] < g_macd_sig[1] && g_macd_main[1] < g_macd_main[2];
   
   if(shortCondition)
   {
      double high1 = iHigh(_Symbol, PERIOD_M15, 1), high2 = iHigh(_Symbol, PERIOD_M15, 2);
      if(high1 <= 0 || high2 <= 0) return; 
      
      double pullbackLevel = g_ema14[1] * (1.0 + pullbackMargin/100.0), pullbackLevel2 = g_ema14[2] * (1.0 + pullbackMargin/100.0);
      
      if(high1 >= pullbackLevel || high2 >= pullbackLevel2)
      {
         double bid = symInfo.Bid(), sl = NormalizePrice(bid + (g_atr[1] * Dyn_SL_S));
         double lot = CalculateVolume(bid, sl, InpRiskPercent, ORDER_TYPE_SELL); 
         if(lot > 0)
         {
            if(SafeTradeSell(lot, bid, sl)) SendTelegramMessage("🐺 狂战士出击 (空) | " + _Symbol); 
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 执行加仓                                                          |
//+------------------------------------------------------------------+
void ExecuteAddPosition(int type, double first_sl, int currentLevel)
{
   double price = (type == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
   double currentRiskPct = InpRiskPercent * MathPow(InpLevelMultiplier, currentLevel); 
   ENUM_ORDER_TYPE orderType = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double lot = CalculateVolume(price, first_sl, currentRiskPct, orderType);
   
   if(lot > 0) 
   {
      bool success = false;
      if(type == POSITION_TYPE_BUY) success = SafeTradeBuy(lot, price, first_sl);
      else if(type == POSITION_TYPE_SELL) success = SafeTradeSell(lot, price, first_sl);
      
      if(!success) Print("⚠️ 加仓执行失败，Level=", currentLevel);
      g_cachedPositionCount = -1; 
   }
}

//+------------------------------------------------------------------+
//| 动态装甲管理                                                      |
//+------------------------------------------------------------------+
void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;
   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && profit_pct <= InpBailoutPct)
   {
      double bal_before = accInfo.Balance(); CloseAllPositions(); 
      ReportFinancials("⚠️ 冲锋受阻，L" + IntegerToString(count) + " 级 Bailout 弹射！", bal_before); return;
   }
   
   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave) 
      {
         double bal_before = accInfo.Balance(); PartialCloseAndBE();  
         HighestProfitPct = 0.0;
         ReportFinancials("⚔️ 阵地物理对切！锁定胜局！", bal_before);
      }
   }
   if(InpUseProfitTrail) ManageTrailingStop(count, profit_pct);
}

//+------------------------------------------------------------------+
//| 计算动态最大层数                                                  |
//+------------------------------------------------------------------+
int CalculateDynamicMaxLevels()
{
   if(!InpUseVolatilityFilter) return InpMaxLevels;
   double atrValue = g_currentAtr; if(atrValue <= 0 || ArraySize(g_atr) < 3) return InpMaxLevels;
   double prevAtr = g_atr[2]; if(prevAtr <= 0) return InpMaxLevels;
   
   double atrMultiplier = MathAbs(g_atr[1] / prevAtr);
   if(atrMultiplier > InpATRMultiplier_Max) return MathMax(1, InpMaxLevels - 2);
   return InpMaxLevels;
}

//+------------------------------------------------------------------+
//| 检查高风险窗口                                                    |
//+------------------------------------------------------------------+
bool IsHighRiskWindow(MqlDateTime &t)
{
   if(!InpUseEventFilter) return false;
   if(t.day_of_week == 0 || t.day_of_week == 6) return true;
   if(t.day_of_week == 5 && t.hour >= 20) return true;
   if(t.day_of_week == 1 && t.hour < 8) return true;
   symInfo.RefreshRates(); 
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread * 2) return true;
   return false;
}

//+------------------------------------------------------------------+
//| URL编码                                                           |
//+------------------------------------------------------------------+
string URLEncode(string str)
{
   string result = ""; uchar chars[]; int count = StringToCharArray(str, chars, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i=0; i<count-1; i++) 
   {
      uchar c = chars[i];
      if((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0' && c<='9') || c=='-' || c=='_' || c=='.' || c=='~') result += StringFormat("%c", c);
      else if(c == ' ') result += "+"; else result += StringFormat("%%%02X", c);
   }
   return result;
}

//+------------------------------------------------------------------+
//| 发送Telegram消息 (异步入队)                                        |
//+------------------------------------------------------------------+
void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   if(StringLen(msg) > 4000) msg = StringSubstr(msg, 0, 3900) + "\n...";
   
   int sz = ArraySize(g_telegramQueue); 
   ArrayResize(g_telegramQueue, sz+1);
   g_telegramQueue[sz] = msg;
}

//+------------------------------------------------------------------+
//| 财务报告                                                          |
//+------------------------------------------------------------------+
void ReportFinancials(string baseMsg, double bal_before=0)
{
   double bal_after = accInfo.Balance();
   double delta = (bal_before > 0) ? (bal_after - bal_before) : 0;
   double dailyTotal = bal_after - DailyStartBalance; 
   string emoji = (delta >= 0) ? "💰 本次净利: +" : "💀 本次战损: -";
   string dailyEmoji = (dailyTotal >= 0) ? "📈 今日累计: +" : "📉 今日累计: -";
   
   string finalMsg = baseMsg + "\n" + emoji + CurrencySymbol + DoubleToString(MathAbs(delta), 2) + " " + CurrencyUnit + "\n" +
                     dailyEmoji + CurrencySymbol + DoubleToString(MathAbs(dailyTotal), 2) + " " + CurrencyUnit + "\n" +
                     "🏦 帝国金库: " + CurrencySymbol + DoubleToString(bal_after, 2) + " " + CurrencyUnit;
   SendTelegramMessage(finalMsg);
}

//+------------------------------------------------------------------+
//| 定期状态报告                                                      |
//+------------------------------------------------------------------+
void SendPeriodicStatusReport(int posCount, double profitPct)
{
   double equity = accInfo.Equity(), dailyPnL = equity - DailyStartBalance;
   double dailyPnLPct = (DailyStartBalance > 0) ? (dailyPnL / DailyStartBalance * 100.0) : 0;
   string posType = (g_cachedPositionType == POSITION_TYPE_BUY) ? "多" : (g_cachedPositionType == POSITION_TYPE_SELL ? "空" : "锁仓/未知");
   
   string report = "📋 【定期运维报告】\n🏦 净值: " + CurrencySymbol + DoubleToString(equity, 2) + "\n" +
                   "📊 浮盈: " + (dailyPnL >= 0 ? "+" : "") + DoubleToString(dailyPnLPct, 2) + "%\n" +
                   "📈 持仓: " + IntegerToString(posCount) + " 层 | 方向: " + posType + "\n💰 阵地浮盈: " + DoubleToString(profitPct, 2) + "%\n";
   if(g_isTrailActive) report += "🛡️ 追踪位: " + DoubleToString(g_trailingStopLevel, _Digits) + "\n";
   SendTelegramMessage(report);
}

//+------------------------------------------------------------------+
//| OnTick 主循环                                                      |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)) return;
   symInfo.RefreshRates();
   
   if(BarsCalculated(h_ema14) < 60 || BarsCalculated(h_macd) < 26 || BarsCalculated(h_vol) < 22) return;
   
   static bool isFirstTick = true; 
   bool isNewBarFlag = IsNewBar();
   bool shouldRunBarLogic = (isFirstTick || isNewBarFlag);
   
   g_tickCounter++; 
   
   if(shouldRunBarLogic) 
   { 
      if(!UpdateIndicators()) return; 
      g_dynamicMaxLevels = CalculateDynamicMaxLevels();
   }
   
   MqlDateTime tInfo; TimeCurrent(tInfo);
   if(tInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance(); 
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance); 
      GlobalVariableSet(GV_DateKey, tInfo.day_of_year);
      
      DailyLossTriggered = false; HighestProfitPct = 0.0; hasPartialThisWave = false; 
      g_tradesToday = 0; g_firstEntryPrice = 0.0; g_cachedPositionCount = -1; g_tickCounter = 0; 
      g_marginFailUntil = 0; g_lastPeriodicReport = 0; g_lastIndicatorUpdate = 0; 
      lastDayOfYear = tInfo.day_of_year;
   }
   
   if(DailyLossTriggered) return;
   
   bool isHighRiskNow = IsHighRiskWindow(tInfo);
   
   if(g_cachedPositionCount == -1 || g_tickCounter % CACHE_REFRESH_INTERVAL == 0) RefreshPositionCache();
   
   int t_pos = g_cachedPositionCount, c_type = g_cachedPositionType;
   double c_profit = g_cachedProfitPct, o_sl = g_cachedOldestSL;
   
   if(t_pos == 0)
   {
      HighestProfitPct = 0.0; hasPartialThisWave = false; g_isTrailActive = false; 
      g_trailingStopLevel = 0.0; g_firstEntryPrice = 0.0; g_cachedPositionType = -1;
      if(isHighRiskNow) { g_isHighRiskWindow = true; if(isFirstTick) isFirstTick = false; return; }
      g_isHighRiskWindow = false;
   }
   else
   {
      g_isHighRiskWindow = isHighRiskNow;
   }
   
   double eq = accInfo.Equity();
   if(InpFridayExit && tInfo.day_of_week == 5 && tInfo.hour >= 22)
   {
      if(t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚩 周末避险强制撤离！", b); }
      if(isFirstTick) isFirstTick = false;
      return;
   }
   
   if(DailyStartBalance > 0 && (eq - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   {
      if(t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("💥 极寒熔断触发！", b); }
      DailyLossTriggered = true; 
      if(isFirstTick) isFirstTick = false;
      return;
   }
   
   if(t_pos > 0) ManageDynamicArmor(t_pos, c_profit);
   
   if(InpUsePeriodicReport && t_pos > 0 && TimeCurrent() - g_lastPeriodicReport >= InpReportIntervalMinutes * 60)
   { SendPeriodicStatusReport(t_pos, c_profit); g_lastPeriodicReport = TimeCurrent(); }
   
   if(!shouldRunBarLogic) { if(isFirstTick) isFirstTick = false; return; }
   
   if(t_pos > 0 && c_type != -1)
   {
      if(TimeCurrent() - g_lastIndicatorUpdate > 300) 
      {
         Print("⚠️ 指标数据可能过时，跳过趋势破位检查");
      }
      else
      {
         double c1 = iClose(_Symbol, PERIOD_M15, 1);
         if(c1 > 0 && ((c_type == POSITION_TYPE_BUY && c1 < g_ema60[1]) || (c_type == POSITION_TYPE_SELL && c1 > g_ema60[1])))
         {
            double b = accInfo.Balance(); CloseAllPositions(); 
            ReportFinancials("🚨 趋势破位，紧急撤退！", b);
            if(isFirstTick) isFirstTick = false;
            return;
         }
      }
      
      double reqP = InpUseSqrtLevelUp ? (InpLevelUpPct * MathSqrt(t_pos)) : (InpLevelUpPct * t_pos);
      if((!hasPartialThisWave || !InpStrictPartialLock) && t_pos < g_dynamicMaxLevels && c_profit >= reqP) 
         ExecuteAddPosition(c_type, o_sl, t_pos);
   }
   else if(t_pos == 0 && tInfo.hour >= InpStartHour && tInfo.hour < InpEndHour)
   {
      CheckEntry();
   }
   
   if(isFirstTick) isFirstTick = false; 
}
//+------------------------------------------------------------------+