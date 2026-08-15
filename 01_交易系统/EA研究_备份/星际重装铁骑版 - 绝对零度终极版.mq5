//+------------------------------------------------------------------+
//|                                     Guardian Earth V20.8.10.mq5  |
//|                                  Copyright 2026, AI Commander    |
//|                             "星际重装铁骑版 - 绝对零度终极版"    |
//+------------------------------------------------------------------+
#property copyright "AI Commander"
#property link      "GuardianEarth_V20.8.10_AbsoluteZero"
#property version   "20.81"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 🛡️ 核心风控与时间 ---
input group "=== 核心风控与时间 ==="
input double   InpRiskPercent    = 2.5;      
input double   InpDailyMaxLoss   = 5.0;      
input int      InpStartHour      = 15;       
input int      InpEndHour        = 23;       
input bool     InpFridayExit     = true;     
input ulong    InpMagicNumber    = 208500;   
input int      InpMaxLevels      = 4;        

//--- 💰 动态装甲 ---
input group "=== 动态保本装甲 ==="
input double   InpHWM_Activate   = 3.0;      
input double   InpHWM_Retract    = 1.5;      

//--- 🐺 狼群战术 ---
input group "=== 狼群追击战术 ==="
input double   InpLevelUpPct     = 0.3;      
input int      InpBailoutLevel   = 3;        
input double   InpBailoutPct     = 0.2;      

//--- 📡 信号灵敏度 ---
input group "=== 进场雷达调优 ==="
input double   InpVolMultiplier  = 0.8;      
input double   InpPullbackPct    = 0.0;      
input bool     InpUseMacroFilter = true;     

//--- 📡 Telegram推送 ---
input group "=== Telegram 战报推送 ==="
input string   InpTelegramToken  = "";       
input string   InpTelegramChatID = "";       

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
datetime       lastBarTime       = 0;
int            lastDayOfYear     = -1; 

//--- 📡 全局高速雷达缓存区 ---
double         g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[];
double         g_macd_main[], g_macd_sig[];
double         g_vol[];

//+------------------------------------------------------------------+
int OnInit()
{
   symInfo.Name(_Symbol);
   symInfo.Refresh();
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();

   AutoCalibrate();

   h_ema14 = iMA(_Symbol, PERIOD_M15, 14, 0, MODE_EMA, PRICE_CLOSE);
   h_ema21 = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   h_ema60 = iMA(_Symbol, PERIOD_M15, 60, 0, MODE_EMA, PRICE_CLOSE);
   h_ema576= iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   h_macd  = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   h_atr   = iATR(_Symbol, PERIOD_M15, 14);
   h_vol   = iVolumes(_Symbol, PERIOD_M15, VOLUME_TICK);

   if(h_ema14==INVALID_HANDLE || h_macd==INVALID_HANDLE || h_atr==INVALID_HANDLE || h_vol==INVALID_HANDLE || h_ema576==INVALID_HANDLE)
   {
      Print("❌ 雷达初始化失败，请检查历史数据！");
      return(INIT_FAILED);
   }

   ArraySetAsSeries(g_ema14, true); ArraySetAsSeries(g_ema21, true); ArraySetAsSeries(g_ema60, true);
   ArraySetAsSeries(g_ema576, true); ArraySetAsSeries(g_atr, true);
   ArraySetAsSeries(g_macd_main, true); ArraySetAsSeries(g_macd_sig, true);
   ArraySetAsSeries(g_vol, true);

   DailyStartBalance = accInfo.Balance();
   HighestProfitPct = 0.0;
   
   MqlDateTime t;
   TimeCurrent(t);
   lastDayOfYear = t.day_of_year; 
   
   string initMsg = "🚀 V20.8.10 绝对零度版启动 | 初始基数: " + DoubleToString(DailyStartBalance, 2);
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
   Print("⚠️ V20.8.10 退出战场: ", r);
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
   Print("🛰️ 测向仪已锁定 - 战区: ", s, " | SL: L-", Dyn_SL_L, " S-", Dyn_SL_S);
}

bool UpdateIndicators()
{
   if(CopyBuffer(h_ema14, 0, 0, 3, g_ema14) < 3) return false;
   if(CopyBuffer(h_ema21, 0, 0, 3, g_ema21) < 3) return false;
   if(CopyBuffer(h_ema60, 0, 0, 3, g_ema60) < 3) return false;
   if(CopyBuffer(h_atr, 0, 0, 1, g_atr) < 1) return false;
   if(CopyBuffer(h_vol, 0, 0, 22, g_vol) < 22) return false;
   if(CopyBuffer(h_macd, 0, 0, 1, g_macd_main) < 1) return false;
   if(CopyBuffer(h_macd, 1, 0, 1, g_macd_sig) < 1) return false;
   
   if(InpUseMacroFilter)
   {
      if(CopyBuffer(h_ema576, 0, 0, 1, g_ema576) < 1) return false;
   }
   return true;
}

//+------------------------------------------------------------------+
void OnTick()
{
   symInfo.RefreshRates();

   if(BarsCalculated(h_ema14) < 60 || BarsCalculated(h_ema21) < 60 || 
      BarsCalculated(h_ema60) < 60 || BarsCalculated(h_macd) < 26 || 
      BarsCalculated(h_atr) < 14 || BarsCalculated(h_vol) < 22) return;
   
   if(InpUseMacroFilter && BarsCalculated(h_ema576) < 576) return;

   static bool isFirstTick = true;
   bool isNewBarFlag = IsNewBar();
   bool shouldRunBarLogic = (isFirstTick || isNewBarFlag);
   
   if(shouldRunBarLogic)
   {
      if(!UpdateIndicators()) return; 
   }
   
   MqlDateTime timeInfo;
   TimeCurrent(timeInfo);
   
   if(timeInfo.day_of_year != lastDayOfYear)
   {
      DailyStartBalance = accInfo.Balance();
      DailyLossTriggered = false;
      HighestProfitPct = 0.0;
      lastDayOfYear = timeInfo.day_of_year;
   }

   if(DailyLossTriggered) return;

   // ==========================================
   // 🛡️ Tick 级防守
   // ==========================================
   int total_positions = 0;
   double total_profit = 0.0;
   double oldest_sl = 0.0;
   datetime oldest_time = INT_MAX;
   int current_type = -1;
   
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            total_positions++;
            total_profit += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
            current_type = posInfo.PositionType();
            
            if(posInfo.Time() < oldest_time)
            {
               oldest_time = posInfo.Time();
               oldest_sl = posInfo.StopLoss();
            }
         }
      }
   }

   double current_profit_pct = (total_profit / accInfo.Balance()) * 100.0;

   if(InpFridayExit && timeInfo.day_of_week == 5 && timeInfo.hour >= 22)
   {
      if(total_positions > 0)
      {
         CloseAllPositions();
         SendTelegramMessage("🚩 周末避险强制撤离！");
      }
      return;
   }

   if((accInfo.Equity() - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   {
      if(total_positions > 0) CloseAllPositions();
      DailyLossTriggered = true;
      SendTelegramMessage("💥 极寒熔断触发！强制锁死！");
      return;
   }

   if(total_positions > 0) ManageDynamicArmor(total_positions, current_profit_pct);

   // ==========================================
   // ⚔️ Bar 级战术进攻
   // ==========================================
   if(!shouldRunBarLogic) return; 

   if(total_positions > 0)
   {
      double close1 = iClose(_Symbol, PERIOD_M15, 1);
      if((current_type == POSITION_TYPE_BUY && close1 < g_ema60[1]) || 
         (current_type == POSITION_TYPE_SELL && close1 > g_ema60[1]))
      {
         CloseAllPositions();
         SendTelegramMessage("🚨 破位防线被击穿，撤退！");
         HighestProfitPct = 0.0;
      }
      else if(total_positions < InpMaxLevels && current_profit_pct >= (InpLevelUpPct * total_positions))
      {
         ExecuteAddPosition(current_type, oldest_sl, total_positions);
      }
   }
   else 
   {
      HighestProfitPct = 0.0;
      if(timeInfo.hour >= InpStartHour && timeInfo.hour < InpEndHour)
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
      CloseAllPositions();
      SendTelegramMessage("⚠️ 冲锋受阻，L" + IntegerToString(count) + " 级 Bailout 弹射！");
      HighestProfitPct = 0.0;
      return;
   }

   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      PartialCloseAndBE();
      SendTelegramMessage("⚔️ 舰队物理对切！锁定保本！");
      HighestProfitPct = 0.0; 
   }
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
   
   // 🟢 物理排雷1：读取券商规定的安全距离，封杀 10016 报错！
   double safeLevel = symInfo.StopsLevel() * symInfo.Point();
   double curAsk = symInfo.Ask();
   double curBid = symInfo.Bid();
   
   for(int j=0; j<count; j++)
   {
      double safeTP = currentTPs[j];
      if(safeTP < 0) safeTP = 0;
      
      // 只有当价格已完全脱离危险区（水上状态），才允许移动止损！
      if(posTypes[j] == POSITION_TYPE_BUY && currentSLs[j] < openPrices[j])
      {
         if(curBid > openPrices[j] + safeLevel)
            trade.PositionModify(tickets[j], openPrices[j], safeTP); 
      }
      else if(posTypes[j] == POSITION_TYPE_SELL && currentSLs[j] > openPrices[j])
      {
         if(curAsk < openPrices[j] - safeLevel)
            trade.PositionModify(tickets[j], openPrices[j], safeTP);
      }
         
      double closeVol = MathFloor((currentVols[j] / 2.0) / volStep) * volStep;
      if(closeVol >= minVol) trade.PositionClosePartial(tickets[j], closeVol);
   }
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
   for(int j=0; j<count; j++) trade.PositionClose(tickets[j]);
}

void CheckEntry()
{
   if(InpUseMacroFilter)
   {
      double currentPrice = iClose(_Symbol, PERIOD_M15, 1);
      if(g_ema14[0] > g_ema21[0] && currentPrice < g_ema576[0]) return;
      if(g_ema14[0] < g_ema21[0] && currentPrice > g_ema576[0]) return;
   }

   double sumVol = 0; 
   for(int i=2; i<=21; i++) sumVol += g_vol[i];
   double avgVol20 = sumVol / 20.0;
   bool volBreakout = (g_vol[0] > avgVol20 * InpVolMultiplier || g_vol[1] > avgVol20 * InpVolMultiplier);

   if(g_ema14[0] > g_ema21[0] && g_ema21[0] > g_ema60[0] && volBreakout && g_macd_main[0] > g_macd_sig[0] && g_macd_main[0] > 0)
   {
      double low1 = iLow(_Symbol, PERIOD_M15, 1);
      double low2 = iLow(_Symbol, PERIOD_M15, 2);
      
      if(low1 <= g_ema14[1] * (1.0 + InpPullbackPct/100.0) || low2 <= g_ema14[2] * (1.0 + InpPullbackPct/100.0))
      {
         double ask = symInfo.Ask();
         double sl = ask - (g_atr[0] * Dyn_SL_L);
         double lot = CalculateVolume(ask, sl);
         if(lot > 0) 
         {
            trade.Buy(lot, _Symbol, ask, sl, 0);
            SendTelegramMessage("🐺 L1 侦察兵做多 | 目标锁定");
         }
      }
   }
   else if(g_ema14[0] < g_ema21[0] && g_ema21[0] < g_ema60[0] && volBreakout && g_macd_main[0] < g_macd_sig[0] && g_macd_main[0] < 0)
   {
      double high1 = iHigh(_Symbol, PERIOD_M15, 1);
      double high2 = iHigh(_Symbol, PERIOD_M15, 2);
      if(high1 >= g_ema14[1] * (1.0 - InpPullbackPct/100.0) || high2 >= g_ema14[2] * (1.0 - InpPullbackPct/100.0))
      {
         double bid = symInfo.Bid();
         double sl = bid + (g_atr[0] * Dyn_SL_S);
         double lot = CalculateVolume(bid, sl);
         if(lot > 0)
         {
            trade.Sell(lot, _Symbol, bid, sl, 0);
            SendTelegramMessage("🐺 L1 侦察兵做空 | 目标锁定");
         }
      }
   }
}

void ExecuteAddPosition(int type, double first_sl, int currentLevel)
{
   double price = (type == POSITION_TYPE_BUY) ? symInfo.Ask() : symInfo.Bid();
   double lot = CalculateVolume(price, first_sl);
   
   // 🟢 物理排雷2：绝对阻断无弹药走火！
   if(lot <= 0) return; 

   if(type == POSITION_TYPE_BUY)
   {
      trade.Buy(lot, _Symbol, price, first_sl, 0);
      SendTelegramMessage("🔥 狼群追击 L" + IntegerToString(currentLevel+1) + " 多 | SL: " + DoubleToString(first_sl,2));
   }
   else if(type == POSITION_TYPE_SELL)
   {
      trade.Sell(lot, _Symbol, price, first_sl, 0);
      SendTelegramMessage("🔥 狼群追击 L" + IntegerToString(currentLevel+1) + " 空 | SL: " + DoubleToString(first_sl,2));
   }
}

double CalculateVolume(double entryPrice, double slPrice)
{
   double riskAmount = accInfo.Balance() * (InpRiskPercent / 100.0);
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
   double calcVol = MathFloor(rawVolume / volStep) * volStep;
   
   if(calcVol < symInfo.LotsMin()) calcVol = symInfo.LotsMin();
   if(calcVol > symInfo.LotsMax()) calcVol = symInfo.LotsMax();
   
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
//+------------------------------------------------------------------+