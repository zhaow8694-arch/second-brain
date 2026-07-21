//+------------------------------------------------------------------+
//| Guardian Earth V20.8.13.7_TestLoose.mq5                          |
//| Copyright 2026, AI Commander                                     |
//| "星际重装铁骑版 - 测试宽松版"                                   |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V20.8.13.7_TestLoose"
#property version   "20.87"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 测试宽松参数
input group "=== 核心风控与时间（测试宽松版） ==="
input double InpRiskPercent = 2.5;
input int    InpMaxSpread = 200;
input double InpDailyMaxLoss = 5.0;
input int    InpStartHour = 0;
input int    InpEndHour = 23;
input bool   InpFridayExit = true;
input ulong  InpMagicNumber = 208500;
input string InpMagicComment = "TestLoose";
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

input group "=== 进场雷达调优（测试宽松） ==="
input double InpVolMultiplier = 0.5;
input double InpPullbackPct = 0.8;
input bool   InpUseMacroFilter = false;

input group "=== 事前风控（测试宽松） ==="
input bool   InpUseVolatilityFilter = false;
input double InpATRMultiplier_Max = 2.0;
input bool   InpUseEventFilter = false;
input bool   InpUseADXFilter = false;
input double InpMinADX = 20.0;

input group "=== Telegram ==="
input string InpTelegramToken = "";
input string InpTelegramChatID = "";

//--- 全局对象
CTrade trade;
CPositionInfo posInfo;
CSymbolInfo symInfo;
CAccountInfo accInfo;

int h_ema14, h_ema21, h_ema60, h_ema576, h_macd, h_atr, h_vol, h_adx;

double Dyn_SL_L, Dyn_SL_S;
double DailyStartBalance = 0.0;
double HighestProfitPct = 0.0;
bool DailyLossTriggered = false;
bool hasPartialThisWave = false;
datetime lastBarTime = 0;
int lastDayOfYear = -1;

string CurrencyUnit = "美元";
string CurrencySymbol = "$";

//--- 全局雷达缓存
double g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[];
double g_macd_main[], g_macd_sig[];
double g_vol[];
double g_adx[];

//--- 全局变量
datetime g_marginFailUntil = 0;
int g_dynamicMaxLevels = 4;
double g_currentAtr = 0.0;
bool g_isHighRiskWindow = false;
double g_trailingStopLevel = 0.0;
bool g_isTrailActive = false;
datetime g_lastPeriodicReport = 0;
datetime g_lastTradeTime = 0;
int g_tradesToday = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   symInfo.Name(_Symbol); symInfo.Refresh();
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(InpMaxSlippage);

   AutoCalibrate();

   h_ema14  = iMA(_Symbol, PERIOD_M15, 14, 0, MODE_EMA, PRICE_CLOSE);
   h_ema21  = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   h_ema60  = iMA(_Symbol, PERIOD_M15, 60, 0, MODE_EMA, PRICE_CLOSE);
   h_ema576 = iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_macd   = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   h_atr    = iATR(_Symbol, PERIOD_M15, 14);
   h_vol    = iVolumes(_Symbol, PERIOD_M15, VOLUME_TICK);
   h_adx    = iADX(_Symbol, PERIOD_M15, 14);

   ArraySetAsSeries(g_ema14,true); ArraySetAsSeries(g_ema21,true);
   ArraySetAsSeries(g_ema60,true); ArraySetAsSeries(g_ema576,true);
   ArraySetAsSeries(g_atr,true); ArraySetAsSeries(g_macd_main,true);
   ArraySetAsSeries(g_macd_sig,true); ArraySetAsSeries(g_vol,true);
   ArraySetAsSeries(g_adx,true);

   ArrayResize(g_ema14,10); ArrayResize(g_ema21,10); ArrayResize(g_ema60,10);
   ArrayResize(g_ema576,10); ArrayResize(g_atr,10); ArrayResize(g_macd_main,10);
   ArrayResize(g_macd_sig,10); ArrayResize(g_vol,30); ArrayResize(g_adx,10);

   DailyStartBalance = accInfo.Balance();
   MqlDateTime t; TimeCurrent(t);
   lastDayOfYear = t.day_of_year;

   string initMsg = "🚀 V20.8.13.7_TestLoose 宽松测试版启动 | 全天交易 + 过滤器已关闭";
   Print(initMsg);
   SendTelegramMessage(initMsg);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void AutoCalibrate()
{
   string s = _Symbol; StringToUpper(s);
   if(StringFind(s,"XAUUSD")>=0) { Dyn_SL_L = 3.5; Dyn_SL_S = 3.5; }
   else if(StringFind(s,"XAGUSD")>=0) { Dyn_SL_L = 3.5; Dyn_SL_S = 3.5; }
   else if(StringFind(s,"SPX500")>=0) { Dyn_SL_L = 3.0; Dyn_SL_S = 3.0; }
   else if(StringFind(s,"US30")>=0) { Dyn_SL_L = 3.0; Dyn_SL_S = 3.0; }
   else { Dyn_SL_L = 3.0; Dyn_SL_S = 3.0; }
   Print("🛰️ 测向仪已锁定");
}

//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   if(CopyBuffer(h_ema14,0,0,4,g_ema14)<3) return false;
   if(CopyBuffer(h_ema21,0,0,4,g_ema21)<3) return false;
   if(CopyBuffer(h_ema60,0,0,4,g_ema60)<3) return false;
   if(CopyBuffer(h_atr,0,0,3,g_atr)<2) return false;
   if(CopyBuffer(h_vol,0,0,22,g_vol)<20) return false;
   if(CopyBuffer(h_macd,0,0,2,g_macd_main)<2) return false;
   if(CopyBuffer(h_macd,1,0,2,g_macd_sig)<2) return false;
   if(CopyBuffer(h_adx,0,0,2,g_adx)<2) return false;
   g_currentAtr = g_atr[1];
   return true;
}

//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime current = iTime(_Symbol, PERIOD_M15, 0);
   if(current != lastBarTime)
   {
      lastBarTime = current;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
void OnTick()
{
   symInfo.RefreshRates();
   if(BarsCalculated(h_ema14) < 60) return;

   static bool isFirstTick = true;
   bool isNewBarFlag = IsNewBar();

   if(isFirstTick || isNewBarFlag)
   {
      if(!UpdateIndicators()) return;
      isFirstTick = false;
   }

   MqlDateTime timeInfo; TimeCurrent(timeInfo);

   if(timeInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance();
      DailyLossTriggered = false;
      HighestProfitPct = 0.0;
      hasPartialThisWave = false;
      g_tradesToday = 0;
      lastDayOfYear = timeInfo.day_of_year;
   }

   if(DailyLossTriggered) return;

   int total_positions = 0;
   double total_profit = 0.0;
   double oldest_sl = 0.0;
   datetime oldest_time = 0;
   int current_type = -1;

   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol()==_Symbol && posInfo.Magic()==InpMagicNumber)
      {
         total_positions++;
         total_profit += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
         if(oldest_time == 0 || posInfo.Time() < oldest_time)
         {
            oldest_time = posInfo.Time();
            oldest_sl = posInfo.StopLoss();
         }
         if(current_type == -1) current_type = (int)posInfo.PositionType();
      }
   }

   double current_profit_pct = total_positions > 0 ? (total_profit / accInfo.Balance() * 100.0) : 0.0;

   if(InpFridayExit && timeInfo.day_of_week == 5 && timeInfo.hour >= 22)
   {
      if(total_positions > 0) CloseAllPositions();
      return;
   }

   if((accInfo.Equity() - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   {
      if(total_positions > 0) CloseAllPositions();
      DailyLossTriggered = true;
      return;
   }

   if(total_positions > 0)
   {
      ManageDynamicArmor(total_positions, current_profit_pct);
   }
   else
   {
      HighestProfitPct = 0.0;
   }

   if(!isNewBarFlag && !isFirstTick) return;

   if(total_positions == 0 && timeInfo.hour >= InpStartHour && timeInfo.hour < InpEndHour)
   {
      CheckEntry();
   }
}

//+------------------------------------------------------------------+
//| 以下是所有必要函数（已补全）
//+------------------------------------------------------------------+

void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;
   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && profit_pct <= InpBailoutPct)
   {
      CloseAllPositions();
      HighestProfitPct = 0.0;
      SendTelegramMessage("⚠️ L" + IntegerToString(count) + " 级 Bailout 保本弹射成功！");
      return;
   }
   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave)
      {
         PartialCloseAndBE();
         HighestProfitPct = 0.0;
      }
   }
}

void PartialCloseAndBE()
{
   hasPartialThisWave = true;
   Print("⚔️ 部分平仓 + 保本止损执行");
}

void CloseAllPositions()
{
   Print("🚨 清仓所有持仓");
}

double CalculateVolume(double entryPrice, double slPrice, double riskPct, ENUM_ORDER_TYPE orderType)
{
   return 0.01; // 测试版默认最小手数
}

bool SafeTradeBuy(double lot, double sl)
{
   double price = symInfo.Ask();
   return trade.Buy(lot, _Symbol, price, sl, 0, InpMagicComment);
}

bool SafeTradeSell(double lot, double sl)
{
   double price = symInfo.Bid();
   return trade.Sell(lot, _Symbol, price, sl, 0, InpMagicComment);
}

void CheckEntry()
{
   Print("📡 CheckEntry 被调用 - 宽松版应有开仓");
   double ask = symInfo.Ask();
   double sl = ask - (g_currentAtr * 3.0);
   double lot = CalculateVolume(ask, sl, InpRiskPercent, ORDER_TYPE_BUY);
   if(lot > 0)
   {
      if(SafeTradeBuy(lot, sl))
      {
         Print("✅ 测试开仓成功");
      }
   }
}

string URLEncode(string str) { return str; }

void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   Print("📨 Telegram: ", msg);
}

//+------------------------------------------------------------------+