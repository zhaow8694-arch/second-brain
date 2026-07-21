//+------------------------------------------------------------------+
//|                                     Guardian Earth V20.8.13.5.mq5|
//|                                  Copyright 2026, AI Commander    |
//|                 "星际重装铁骑版 - 绝对零度终极版 (封神终极量产版)"  |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V20.8.13.5_AbsoluteZero"
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

//--- 🐺 狼群战术 (火力配置) ---
input group "=== 狼群追击战术 ==="
input double InpLevelMultiplier= 1.0;     // 📈 加仓火力衰减系数 (1.0=全火力狂暴模式)
input double InpLevelUpPct     = 0.2;     // 📏 加仓间距触发线(%)
input int    InpBailoutLevel   = 3;
input double InpBailoutPct     = 0.2;

//--- 💰 动态装甲 ---
input group "=== 动态保本装甲 ==="
input double InpHWM_Activate   = 4.0;     // 💰 利润激活线 (4.0=模拟测试最优值)
input double InpHWM_Retract    = 1.5;
input bool   InpStrictPartialLock = false; // 🔓 严格防重复锁(False=对切后可继续追击)

//--- 📡 信号灵敏度 ---
input group "=== 进场雷达调优 ==="
input double InpVolMultiplier  = 0.8;
input double InpPullbackPct    = 0.0;
input bool   InpUseMacroFilter = true;

//--- 📡 Telegram推送与账户 ---
input group "=== Telegram 与 账户设定 ==="
enum ENUM_ACC_TYPE { ACC_AUTO, ACC_CENT, ACC_USD };
input ENUM_ACC_TYPE InpAccountType = ACC_AUTO; // 🏦 账户资金类型(自动侦测)
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

//--- 📡 全局高速雷达缓存区 ---
double g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[];
double g_macd_main[], g_macd_sig[];
double g_vol[];

//+------------------------------------------------------------------+
//| 🛠️ 核心价格打磨机
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
   symInfo.RefreshRates();
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   AutoCalibrate();

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
      Print("🏦 智能账户侦测完成 | 货币: ", accCur, " | 单位: ", CurrencyUnit);
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
   {
      Print("❌ 雷达启动失败！请检查历史数据。");
      return(INIT_FAILED);
   }

   ArraySetAsSeries(g_ema14, true); ArraySetAsSeries(g_ema21, true); ArraySetAsSeries(g_ema60, true);
   ArraySetAsSeries(g_ema576, true); ArraySetAsSeries(g_atr, true);
   ArraySetAsSeries(g_macd_main, true); ArraySetAsSeries(g_macd_sig, true);
   ArraySetAsSeries(g_vol, true);

   DailyStartBalance = accInfo.Balance();
   HighestProfitPct = 0.0;
   hasPartialThisWave = false;

   MqlDateTime t;
   TimeCurrent(t);
   lastDayOfYear = t.day_of_year;

   string initMsg = "🚀 V20.8.13.5 封神终极量产版已启动！\n初始资金: " + CurrencySymbol + DoubleToString(DailyStartBalance, 2) + " " + CurrencyUnit;
   Print(initMsg);
   SendTelegramMessage(initMsg);

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   Print("⚠️ 任务结束，机甲卸甲。原因: ", reason);
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
   Print("🛰️ 雷达已瞄准 ", s, " | SL: L-", Dyn_SL_L, " S-", Dyn_SL_S);
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
   if(InpUseMacroFilter) { if(CopyBuffer(h_ema576, 0, 0, 2, g_ema576) < 2) return false; }
   return true;
}

void OnTick()
{
   symInfo.RefreshRates();
   if(BarsCalculated(h_ema14) < 60 || BarsCalculated(h_macd) < 26 || BarsCalculated(h_vol) < 22) return;
   
   static bool isFirstTick = true;
   bool isNewBarFlag = IsNewBar();
   if(isFirstTick || isNewBarFlag) { if(!UpdateIndicators()) return; }
   
   MqlDateTime timeInfo;
   TimeCurrent(timeInfo);
   
   if(timeInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance();
      DailyLossTriggered = false;
      HighestProfitPct = 0.0;
      hasPartialThisWave = false;
      lastDayOfYear = timeInfo.day_of_year;
   }
   if(DailyLossTriggered) return;

   int total_positions = 0; int buy_count = 0; int sell_count = 0;
   double total_profit = 0.0; double oldest_sl = 0.0; datetime oldest_time = 0; int current_type = -1;

   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            total_positions++;
            total_profit += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
            if(posInfo.PositionType() == POSITION_TYPE_BUY) buy_count++;
            if(posInfo.PositionType() == POSITION_TYPE_SELL) sell_count++;
            if(oldest_time == 0 || posInfo.Time() < oldest_time) { oldest_time = posInfo.Time(); oldest_sl = posInfo.StopLoss(); }
         }
      }
   }

   if(total_positions == 0) { HighestProfitPct = 0.0; hasPartialThisWave = false; }
   else {
      if(buy_count > 0 && sell_count == 0) current_type = POSITION_TYPE_BUY;
      else if(sell_count > 0 && buy_count == 0) current_type = POSITION_TYPE_SELL;
   }

   double current_profit_pct = (total_positions > 0) ? ((total_profit / accInfo.Balance()) * 100.0) : 0.0;

   if(InpFridayExit && timeInfo.day_of_week == 5 && timeInfo.hour >= 22)
   {
      if(total_positions > 0) { double bal_before = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚩 周末避险清仓", bal_before); }
      return;
   }

   if((accInfo.Equity() - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   {
      if(total_positions > 0) { double bal_before = accInfo.Balance(); CloseAllPositions(); ReportFinancials("💥 熔断清仓", bal_before); }
      DailyLossTriggered = true;
      return;
   }

   if(total_positions > 0) ManageDynamicArmor(total_positions, current_profit_pct);

   if(!(isFirstTick || isNewBarFlag)) return;

   if(total_positions > 0 && current_type != -1)
   {
      double close1 = iClose(_Symbol, PERIOD_M15, 1);
      if((current_type == POSITION_TYPE_BUY && close1 < g_ema60[1]) || (current_type == POSITION_TYPE_SELL && close1 > g_ema60[1]))
      {
         double bal_before = accInfo.Balance(); CloseAllPositions(); ReportFinancials("🚨 均线破位撤退", bal_before);
      }
      else if((!hasPartialThisWave || !InpStrictPartialLock) && total_positions < InpMaxLevels && current_profit_pct >= (InpLevelUpPct * total_positions))
      {
         ExecuteAddPosition(current_type, oldest_sl, total_positions);
      }
   }
   else if(total_positions == 0) { if(timeInfo.hour >= InpStartHour && timeInfo.hour < InpEndHour) CheckEntry(); }

   if(isFirstTick) isFirstTick = false;
}

void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;
   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && profit_pct <= InpBailoutPct)
   {
      double bal_before = accInfo.Balance(); CloseAllPositions(); ReportFinancials("⚠️ 冲锋回撤弹射", bal_before);
      return;
   }
   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave) { double bal_before = accInfo.Balance(); PartialCloseAndBE(); ReportFinancials("⚔️ 利润对切锁定", bal_before); }
   }
}

void PartialCloseAndBE()
{
   double volStep = symInfo.LotsStep(); double minVol = symInfo.LotsMin();
   int total = PositionsTotal();
   for(int i=total-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         double safeTP = (posInfo.TakeProfit() > 0) ? NormalizePrice(posInfo.TakeProfit()) : 0;
         double beSL = NormalizePrice(posInfo.PriceOpen());
         trade.PositionModify(posInfo.Ticket(), beSL, safeTP);
         double closeVol = MathFloor((posInfo.Volume() / 2.0) / volStep) * volStep;
         if(closeVol >= minVol) trade.PositionClosePartial(posInfo.Ticket(), closeVol);
      }
   }
   hasPartialThisWave = true;
}

void CloseAllPositions()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         trade.PositionClose(posInfo.Ticket());
   }
}

void CheckEntry()
{
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;
   if(InpUseMacroFilter)
   {
      double currentPrice = iClose(_Symbol, PERIOD_M15, 1);
      if(g_ema14[1] > g_ema21[1] && currentPrice < g_ema576[1]) return;
      if(g_ema14[1] < g_ema21[1] && currentPrice > g_ema576[1]) return;
   }
   double sumVol = 0; for(int i=2; i<=21; i++) sumVol += g_vol[i];
   bool volBreakout = (g_vol[1] > (sumVol/20.0) * InpVolMultiplier);

   if(g_ema14[1] > g_ema21[1] && g_ema21[1] > g_ema60[1] && volBreakout && g_macd_main[1] > g_macd_sig[1] && g_macd_main[1] > 0)
   {
      if(iLow(_Symbol, PERIOD_M15, 1) <= g_ema14[1])
      {
         double ask = symInfo.Ask(); double sl = NormalizePrice(ask - (g_atr[1] * Dyn_SL_L));
         double lot = CalculateVolume(ask, sl, InpRiskPercent);
         if(lot > 0) if(SafeTradeBuy(lot, ask, sl)) SendTelegramMessage("🐺 L1 侦察兵做多");
      }
   }
   else if(g_ema14[1] < g_ema21[1] && g_ema21[1] < g_ema60[1] && volBreakout && g_macd_main[1] < g_macd_sig[1] && g_macd_main[1] < 0)
   {
      if(iHigh(_Symbol, PERIOD_M15, 1) >= g_ema14[1])
      {
         double bid = symInfo.Bid(); double sl = NormalizePrice(bid + (g_atr[1] * Dyn_SL_S));
         double lot = CalculateVolume(bid, sl, InpRiskPercent);
         if(lot > 0) if(SafeTradeSell(lot, bid, sl)) SendTelegramMessage("🐺 L1 侦察兵做空");
      }
   }
}

void ExecuteAddPosition(int type, double first_sl, int currentLevel)
{
   double price = (type == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
   double currentRiskPct = InpRiskPercent * MathPow(InpLevelMultiplier, currentLevel);
   double lot = CalculateVolume(price, first_sl, currentRiskPct);
   if(lot <= 0) return;
   if(type == POSITION_TYPE_BUY) { if(SafeTradeBuy(lot, price, first_sl)) SendTelegramMessage("🔥 狼群追击 L" + IntegerToString(currentLevel+1) + " 多"); }
   else { if(SafeTradeSell(lot, price, first_sl)) SendTelegramMessage("🔥 狼群追击 L" + IntegerToString(currentLevel+1) + " 空"); }
}

bool SafeTradeBuy(double lot, double price, double sl)
{
   price = NormalizePrice(price); sl = NormalizePrice(sl);
   return trade.Buy(lot, _Symbol, price, sl, 0, InpMagicComment);
}

bool SafeTradeSell(double lot, double price, double sl)
{
   price = NormalizePrice(price); sl = NormalizePrice(sl);
   return trade.Sell(lot, _Symbol, price, sl, 0, InpMagicComment);
}

double CalculateVolume(double entryPrice, double slPrice, double riskPct)
{
   entryPrice = NormalizePrice(entryPrice); slPrice = NormalizePrice(slPrice);
   double riskAmount = accInfo.Balance() * (riskPct / 100.0);
   double slDistance = MathAbs(entryPrice - slPrice);
   if(slDistance <= 0 || symInfo.TickValue() <= 0) return 0;
   double rawVolume = riskAmount / ((slDistance / symInfo.TickSize()) * symInfo.TickValue());
   double volStep = symInfo.LotsStep();
   double calcVol = MathFloor(rawVolume / volStep) * volStep;
   return MathMax(MathMin(calcVol, symInfo.LotsMax()), symInfo.LotsMin());
}

bool IsNewBar()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_M15, 0);
   if(currentBarTime != lastBarTime) { lastBarTime = currentBarTime; return true; }
   return false;
}

string URLEncode(string str)
{
   string result = ""; uchar chars[];
   int count = StringToCharArray(str, chars, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i=0; i<count-1; i++) {
      uchar c = chars[i];
      if((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0' && c<='9') || c=='-' || c=='_' || c=='.' || c=='~') result += StringFormat("%c", c);
      else result += (c==' ') ? "+" : StringFormat("%%%02X", c);
   }
   return result;
}

void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   string url = "https://api.telegram.org/bot" + InpTelegramToken + "/sendMessage";
   string payload = StringFormat("chat_id=%s&text=%s", URLEncode(InpTelegramChatID), URLEncode(msg));
   char post[], result[]; string headers; StringToCharArray(payload, post, 0, WHOLE_ARRAY, CP_UTF8);
   WebRequest("POST", url, "Content-Type: application/x-www-form-urlencoded\r\n", 5000, post, result, headers);
}

void ReportFinancials(string baseMsg, double bal_before)
{
   Sleep(500);
   double bal_after = accInfo.Balance(); double delta = bal_after - bal_before;
   double dailyTotal = bal_after - DailyStartBalance;
   string emoji = (delta >= 0) ? "💰 净利: +" : "💀 战损: -";
   string dailyEmoji = (dailyTotal >= 0) ? "📈 今日累计: +" : "📉 今日累计: -";
   string finalMsg = baseMsg + "\n" + emoji + CurrencySymbol + DoubleToString(MathAbs(delta), 2) + " " + CurrencyUnit + "\n" +
                     dailyEmoji + CurrencySymbol + DoubleToString(MathAbs(dailyTotal), 2) + " " + CurrencyUnit + "\n" +
                     "🏦 金库: " + CurrencySymbol + DoubleToString(bal_after, 2) + " " + CurrencyUnit;
   SendTelegramMessage(finalMsg);
}
//+------------------------------------------------------------------+