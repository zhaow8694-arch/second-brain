//+------------------------------------------------------------------+
//|                                     Guardian Earth V20.8.13.6.mq5|
//|                                  Copyright 2026, AI Commander    |
//|                 "星际重装铁骑版 - 绝对理念高度终极版 (封神量产版)"  |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V20.8.13.6_AbsoluteZero"
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

//--- 🐺 狼群战术 (狂暴配置) ---
input group "=== 狼群追击战术 ==="
input double InpLevelMultiplier= 1.0;     // 📉 加仓火力衰减系数 (1.0=全火力)
input double InpLevelUpPct     = 0.2;     // 📏 加仓间距触发线(%)
input int    InpBailoutLevel   = 3;
input double InpBailoutPct     = 0.2;

//--- 💰 动态装甲 ---
input group "=== 动态保本装甲 ==="
input double InpHWM_Activate   = 4.0;     // 💰 利润激活线 (4.0=模拟测试最优值)
input double InpHWM_Retract    = 1.5;
input bool   InpStrictPartialLock = false; 

//--- 📡 信号灵敏度 ---
input group "=== 进场雷达调优 ==="
input double InpVolMultiplier  = 0.8;
input double InpPullbackPct    = 0.0;
input bool   InpUseMacroFilter = true;

//--- 📡 Telegram推送与账户 ---
input group "=== Telegram 与 账户设定 ==="
enum ENUM_ACC_TYPE { ACC_AUTO, ACC_CENT, ACC_USD };
input ENUM_ACC_TYPE InpAccountType = ACC_AUTO; 
input string InpTelegramToken  = "";
input string InpTelegramChatID = "";

//--- 全局组件 ---
CTrade         trade;
CPositionInfo  posInfo;
CSymbolInfo    symInfo;
CAccountInfo   accInfo;

int            h_ema14, h_ema21, h_ema60, h_ema576, h_macd, h_atr, h_vol;
double         Dyn_SL_L, Dyn_SL_S;
double         DailyStartBalance = 0.0;
double         HighestProfitPct  = 0.0;
bool           DailyLossTriggered= false;
bool           hasPartialThisWave= false;
datetime       lastBarTime       = 0;
int            lastDayOfYear     = -1;
string         CurrencyUnit      = "美分";
string         CurrencySymbol    = "";

//--- 雷达缓存 ---
double g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[], g_macd_main[], g_macd_sig[], g_vol[];

//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   double tickSize = symInfo.TickSize();
   if(tickSize <= 0) return price;
   return MathRound(price / tickSize) * tickSize;
}

//+------------------------------------------------------------------+
int OnInit()
{
   symInfo.Name(_Symbol);
   
   // 🎯【核心修复】：将旧版 symInfo.Refresh() 修正为 symInfo.RefreshRates()
   symInfo.RefreshRates(); 
   
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   AutoCalibrate();

   if(InpAccountType == ACC_AUTO)
   {
      string accCur = AccountInfoString(ACCOUNT_CURRENCY);
      if(StringFind(accCur, "USC") >= 0 || StringFind(accCur, "cent") >= 0 || StringFind(accCur, "Cent") >= 0)
      { CurrencyUnit = "美分"; CurrencySymbol = ""; }
      else
      { CurrencyUnit = "美元"; CurrencySymbol = "$"; }
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

   if(h_ema14==INVALID_HANDLE || h_macd==INVALID_HANDLE || h_atr==INVALID_HANDLE || h_vol==INVALID_HANDLE || h_ema576==INVALID_HANDLE)
   { Print("❌ 雷达启动失败！检查历史数据。"); return(INIT_FAILED); }

   ArraySetAsSeries(g_ema14, true); ArraySetAsSeries(g_ema21, true); ArraySetAsSeries(g_ema60, true);
   ArraySetAsSeries(g_ema576, true); ArraySetAsSeries(g_atr, true); ArraySetAsSeries(g_macd_main, true); 
   ArraySetAsSeries(g_macd_sig, true); ArraySetAsSeries(g_vol, true);

   DailyStartBalance = accInfo.Balance();
   HighestProfitPct = 0.0; hasPartialThisWave = false;
   MqlDateTime t; TimeCurrent(t); lastDayOfYear = t.day_of_year;

   string initMsg = "🚀 V20.81 封神最终版启动 | 初始基数: " + CurrencySymbol + DoubleToString(DailyStartBalance, 2) + " " + CurrencyUnit;
   Print(initMsg); SendTelegramMessage(initMsg);

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   Print("⚠️ 阵地收放，原因: ", reason);
   SendTelegramMessage("⚠️ 警报！机甲已离线！原因代号: " + IntegerToString(reason));
}

void AutoCalibrate()
{
   string s = _Symbol; StringToUpper(s); 
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) { Dyn_SL_L = 3.5; Dyn_SL_S = 3.5; }
   else if(StringFind(s,"XAGUSD")>=0 || StringFind(s,"SILVER")>=0) { Dyn_SL_L = 3.5; Dyn_SL_S = 3.5; }
   else { Dyn_SL_L = 3.0; Dyn_SL_S = 3.0; }
   Print("🛰️ 雷达瞄准 ", s, " | SL: L-", Dyn_SL_L, " S-", Dyn_SL_S);
}

bool UpdateIndicators()
{
   if(CopyBuffer(h_ema14, 0, 0, 4, g_ema14) < 4) return false;
   if(CopyBuffer(h_ema21, 0, 0, 4, g_ema21) < 4) return false;
   if(CopyBuffer(h_ema60, 0, 0, 4, g_ema60) < 4) return false;
   if(CopyBuffer(h_atr, 0, 0, 2, g_atr) < 2) return false;
   if(CopyBuffer(h_vol, 0, 0, 22, g_vol) < 22) return false;
   if(CopyBuffer(h_macd, 0, 0, 2, g_macd_main) < 2) return false;
   if(CopyBuffer(h_macd, 1, 0, 2, g_macd_sig) < 2) return false;
   if(InpUseMacroFilter && CopyBuffer(h_ema576, 0, 0, 2, g_ema576) < 2) return false;
   return true;
}

void OnTick()
{
   symInfo.RefreshRates();
   if(BarsCalculated(h_ema14) < 60 || BarsCalculated(h_macd) < 26 || BarsCalculated(h_vol) < 22) return;
   
   static bool isFirstTick = true;
   bool isNewBarFlag = IsNewBar();
   if(isFirstTick || isNewBarFlag) { if(!UpdateIndicators()) return; }
   
   MqlDateTime timeInfo; TimeCurrent(timeInfo);
   if(timeInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance(); DailyLossTriggered = false;
      HighestProfitPct = 0.0; hasPartialThisWave = false; lastDayOfYear = timeInfo.day_of_year;
   }
   if(DailyLossTriggered) return;

   int tp = 0, bc = 0, sc = 0; double tprof = 0.0, osl = 0.0; datetime ot = 0; int cur_t = -1;
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         tp++; tprof += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
         if(posInfo.PositionType() == POSITION_TYPE_BUY) bc++;
         if(posInfo.PositionType() == POSITION_TYPE_SELL) sc++;
         if(ot == 0 || posInfo.Time() < ot) { ot = posInfo.Time(); osl = posInfo.StopLoss(); }
      }
   }
   if(tp == 0) { HighestProfitPct = 0.0; hasPartialThisWave = false; }
   else { if(bc > 0 && sc == 0) cur_t = POSITION_TYPE_BUY; else if(sc > 0 && bc == 0) cur_t = POSITION_TYPE_SELL; }

   double c_prof_pct = (tp > 0) ? ((tprof / accInfo.Balance()) * 100.0) : 0.0;
   if(InpFridayExit && timeInfo.day_of_week == 5 && timeInfo.hour >= 22)
   { if(tp > 0) { double bb = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚩 周末避险", bb); } return; }

   if((accInfo.Equity() - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   { if(tp > 0) { double bb = accInfo.Balance(); CloseAllPositions(); ReportFinancials("💥 熔断清仓", bb); } DailyLossTriggered = true; return; }

   if(tp > 0) ManageDynamicArmor(tp, c_prof_pct);
   if(!(isFirstTick || isNewBarFlag)) return;

   if(tp > 0 && cur_t != -1)
   {
      double cl1 = iClose(_Symbol, PERIOD_M15, 1);
      if((cur_t == POSITION_TYPE_BUY && cl1 < g_ema60[1]) || (cur_t == POSITION_TYPE_SELL && cl1 > g_ema60[1]))
      { double bb = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚨 破位撤退", bb); }
      else if((!hasPartialThisWave || !InpStrictPartialLock) && tp < InpMaxLevels && c_prof_pct >= (InpLevelUpPct * tp))
      { ExecuteAddPosition(cur_t, osl, tp); }
   }
   else if(tp == 0 && timeInfo.hour >= InpStartHour && timeInfo.hour < InpEndHour) CheckEntry();
   if(isFirstTick) isFirstTick = false; 
}

void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;
   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && profit_pct <= InpBailoutPct)
   { double bb = accInfo.Balance(); CloseAllPositions(); ReportFinancials("⚠️ 阻力回吐弹射", bb); return; }
   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   { if(!hasPartialThisWave) { double bb = accInfo.Balance(); PartialCloseAndBE(); ReportFinancials("⚔️ 利润对切锁定", bb); } }
}

void PartialCloseAndBE()
{
   double vs = symInfo.LotsStep(); double mv = symInfo.LotsMin();
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         double tp = (posInfo.TakeProfit() > 0) ? NormalizePrice(posInfo.TakeProfit()) : 0;
         double be = NormalizePrice(posInfo.PriceOpen());
         trade.PositionModify(posInfo.Ticket(), be, tp);
         double cv = MathFloor((posInfo.Volume() / 2.0) / vs) * vs;
         if(cv >= mv) trade.PositionClosePartial(posInfo.Ticket(), cv);
      }
   }
   hasPartialThisWave = true; 
}

void CloseAllPositions()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   { if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber) trade.PositionClose(posInfo.Ticket()); }
}

void CheckEntry()
{
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;
   if(InpUseMacroFilter)
   {
      double cur = iClose(_Symbol, PERIOD_M15, 1);
      if(g_ema14[1] > g_ema21[1] && cur < g_ema576[1]) return;
      if(g_ema14[1] < g_ema21[1] && cur > g_ema576[1]) return;
   }
   double sV = 0; for(int i=2; i<=21; i++) sV += g_vol[i];
   bool vB = (g_vol[1] > (sV/20.0) * InpVolMultiplier);
   if(g_ema14[1] > g_ema21[1] && g_ema21[1] > g_ema60[1] && vB && g_macd_main[1] > g_macd_sig[1] && g_macd_main[1] > 0)
   {
      if(iLow(_Symbol, PERIOD_M15, 1) <= g_ema14[1])
      {
         double ask = symInfo.Ask(); double sl = NormalizePrice(ask - (g_atr[1] * Dyn_SL_L));
         double lt = CalculateVolume(ask, sl, InpRiskPercent);
         if(lt > 0) if(SafeTradeBuy(lt, ask, sl)) SendTelegramMessage("🐺 L1 侦察兵做多");
      }
   }
   else if(g_ema14[1] < g_ema21[1] && g_ema21[1] < g_ema60[1] && vB && g_macd_main[1] < g_macd_sig[1] && g_macd_main[1] < 0)
   {
      if(iHigh(_Symbol, PERIOD_M15, 1) >= g_ema14[1])
      {
         double bid = symInfo.Bid(); double sl = NormalizePrice(bid + (g_atr[1] * Dyn_SL_S));
         double lt = CalculateVolume(bid, sl, InpRiskPercent);
         if(lt > 0) if(SafeTradeSell(lt, bid, sl)) SendTelegramMessage("🐺 L1 侦察兵做空");
      }
   }
}

void ExecuteAddPosition(int t, double fsl, int l)
{
   double p = (t == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
   double lt = CalculateVolume(p, fsl, InpRiskPercent * MathPow(InpLevelMultiplier, l));
   if(lt <= 0) return;
   if(t == POSITION_TYPE_BUY) { if(SafeTradeBuy(lt, p, fsl)) SendTelegramMessage("🔥 狼群 L" + IntegerToString(l+1) + " 多"); }
   else { if(SafeTradeSell(lt, p, fsl)) SendTelegramMessage("🔥 狼群 L" + IntegerToString(l+1) + " 空"); }
}

bool SafeTradeBuy(double lot, double price, double sl) { return trade.Buy(lot, _Symbol, NormalizePrice(price), NormalizePrice(sl), 0, InpMagicComment); }
bool SafeTradeSell(double lot, double price, double sl) { return trade.Sell(lot, _Symbol, NormalizePrice(price), NormalizePrice(sl), 0, InpMagicComment); }

double CalculateVolume(double ent, double sl, double rsk)
{
   double d = MathAbs(NormalizePrice(ent) - NormalizePrice(sl));
   if(d <= 0 || symInfo.TickValue() <= 0) return 0;
   double rv = (accInfo.Balance() * (rsk / 100.0)) / ((d / symInfo.TickSize()) * symInfo.TickValue());
   double vs = symInfo.LotsStep(); double cv = MathFloor(rv / vs) * vs;
   return MathMax(MathMin(cv, symInfo.LotsMax()), symInfo.LotsMin());
}

bool IsNewBar() { datetime t = iTime(_Symbol, PERIOD_M15, 0); if(t != lastBarTime) { lastBarTime = t; return true; } return false; }

string URLEncode(string s)
{
   string res = ""; uchar c[]; int n = StringToCharArray(s, c, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i=0; i<n-1; i++) {
      if((c[i]>='a'&&c[i]<='z')||(c[i]>='A'&&c[i]<='Z')||(c[i]>='0'&&c[i]<='9')||c[i]=='-'||c[i]=='_'||c[i]=='.'||c[i]=='~') res += StringFormat("%c", c[i]);
      else res += (c[i] == ' ') ? "+" : StringFormat("%%%02X", c[i]);
   }
   return res;
}

void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   string url = "https://api.telegram.org/bot" + InpTelegramToken + "/sendMessage";
   string pld = StringFormat("chat_id=%s&text=%s", URLEncode(InpTelegramChatID), URLEncode(msg));
   char post[], result[]; string head; StringToCharArray(pld, post, 0, WHOLE_ARRAY, CP_UTF8);
   int res = WebRequest("POST", url, "Content-Type: application/x-www-form-urlencoded\r\n", 10000, post, result, head);
   if(res != 200 && res != 1003) Print("❌ Telegram 链路干扰: ", res);
}

void ReportFinancials(string base, double bb)
{
   Sleep(500); double ba = accInfo.Balance(); double d = ba - bb; double dt = ba - DailyStartBalance;
   string em = (d >= 0) ? "💰 净利: +" : "💀 战损: -";
   string dem = (dt >= 0) ? "📈 今日累计: +" : "📉 今日累计: -";
   string final = base + "\n" + em + CurrencySymbol + DoubleToString(MathAbs(d), 2) + " " + CurrencyUnit + "\n" +
                  dem + CurrencySymbol + DoubleToString(MathAbs(dt), 2) + " " + CurrencyUnit + "\n" +
                  "🏦 金库: " + CurrencySymbol + DoubleToString(ba, 2) + " " + CurrencyUnit;
   SendTelegramMessage(final);
}
//+------------------------------------------------------------------+