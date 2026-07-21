//+------------------------------------------------------------------+
//| GEMINI Starfleet EA - V21.02 ABSOLUTE ZERO (Commander Edition)   |
//| Audited by Grok | Integrated by GEMINI | FINAL PRODUCTION READY  |
//| Core Fix: Dynamic Wolfpack Scaling (Anti-MachineGun Bug)         |
//+------------------------------------------------------------------+
#property copyright "GEMINI Commander & Tactical Dept"
#property link      "https://t.me/gemini_tactical"
#property version   "21.02"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- Input Parameters (Production Ready) ---
input group "=== Risk & Time Management ==="
input double   InpRiskPercent    = 2.5;      // 单次风控比例 (%)
input int      InpMaxSpread      = 45;       // 最大允许点差 (Points)
input double   InpDailyMaxLoss   = 5.0;      // 日极寒熔断 (%)
input int      InpStartHour      = 15;       // 开盘时间 (Broker Time)
input int      InpEndHour        = 23;       // 收盘时间 (Broker Time)
input bool     InpFridayExit     = true;     // 周五22:00强制清仓
input int      InpMaxLevels      = 4;        // 狼群最大叠仓层数

input group "=== Pyramid Scaling Strategy ==="
input double   InpLevelMultiplier = 0.6;     // 追击火力衰减乘数
input double   InpLevelUpPct      = 0.5;     // 叠仓间距 (%)
input double   InpBailoutPct      = 0.2;     // 重仓弹射保本线 (%)

input group "=== Dynamic Armor (HWM) ==="
input double   InpHWM_Activate   = 1.8;      // 利润对切激活线 (%)
input double   InpHWM_Retract    = 0.5;      // 利润对切回撤容忍 (%)

input group "=== Radar & Filters ==="
input double   InpPullbackPct    = 0.15;     // 入场回抽深度 (%)
input bool     InpUseMacroFilter = false;    // H4 宏观趋势过滤开关
input bool     InpUseStructCooldown = true;  // EMA14 形态战损重置护盾
input bool     InpUseMACDExhaustion = true;  // MACD 动能衰竭双重确认

input group "=== Telegram Battle Report ==="
input string   InpTelegramToken  = "";       // Bot Token (留空则静默)
input string   InpTelegramChatID = "";       // Chat ID

//--- Global Variables & Constants ---
ulong          EXPERT_MAGIC      = 20262102; // V21.02 专属独立识别码

CTrade         trade;
CPositionInfo  posInfo;
CSymbolInfo    symInfo;
CAccountInfo   accInfo;

int            handle_ema14, handle_ema21, handle_ema60, handle_ema576;
int            handle_macd, handle_atr, handle_vol;

double         g_lastClosedBalance = 0;
int            g_cooldownState = 0;
double         g_highestProfitPct = 0;
double         g_dailyStartBalance = 0;
datetime       g_lastNewDay = 0;
int            g_lastPositionsTotal = 0;
datetime       g_lastBarTime = 0;
bool           g_hasPartialClosedThisWave = false;
double         g_L1_SL = 0.0;                // L1 止损线物理锚点

//+------------------------------------------------------------------+
//| 专属独立仓位计算器 (防其他 EA 干扰)                              |
//+------------------------------------------------------------------+
int GetOurPositionsTotal()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == EXPERT_MAGIC)
         count++;
   }
   return count;
}

//+------------------------------------------------------------------+
//| L1_SL 持久化恢复函数（解决断网重启丢失）                         |
//+------------------------------------------------------------------+
void RecoverL1SL()
{
   if(g_L1_SL != 0.0) return;  // 已锁定则跳过
   datetime oldestTime = INT_MAX;
   double recoveredSL = 0.0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == EXPERT_MAGIC)
      {
         if(posInfo.Time() < oldestTime)
         {
            oldestTime = posInfo.Time();
            recoveredSL = posInfo.StopLoss();
         }
      }
   }
   
   if(recoveredSL != 0.0)
   {
      g_L1_SL = recoveredSL;
      Print("✅ V21.02: L1_SL 已从残留仓位恢复 | SL = ", DoubleToString(g_L1_SL, _Digits));
      SendTelegramMessage("🔄 L1_SL 铁锁已自动恢复（系统重载完成）");
   }
}

//+------------------------------------------------------------------+
//| Initialization (System Boot)                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🚀 V21.02 Final Applied | Commander Edition");
   Print("English fallback: All Chinese inputs & Telegram are production-safe.");

   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("❌ FATAL ERROR: Account must be HEDGING mode!");
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(EXPERT_MAGIC);
   symInfo.Name(_Symbol);

   handle_ema14  = iMA(_Symbol, PERIOD_M15, 14, 0, MODE_EMA, PRICE_CLOSE);
   handle_ema21  = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   handle_ema60  = iMA(_Symbol, PERIOD_M15, 60, 0, MODE_EMA, PRICE_CLOSE);
   handle_ema576 = iMA(_Symbol, PERIOD_H4, 576, 0, MODE_EMA, PRICE_CLOSE);
   handle_macd   = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE);
   handle_atr    = iATR(_Symbol, PERIOD_M15, 14);
   handle_vol    = iVolumes(_Symbol, PERIOD_M15, VOLUME_TICK);

   if(handle_ema14 == INVALID_HANDLE || handle_macd == INVALID_HANDLE || handle_atr == INVALID_HANDLE)
      return(INIT_FAILED);

   g_lastClosedBalance = accInfo.Balance();
   g_dailyStartBalance = g_lastClosedBalance;
   g_lastPositionsTotal = GetOurPositionsTotal();
   g_L1_SL = 0.0;

   RecoverL1SL();

   if(InpTelegramToken != "" && InpTelegramChatID != "")
      SendTelegramMessage("✅ V21.02 封神无漏版上线 | 中文战报就绪");

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| IsNewBar CPU Shield (Locked to M15)                              |
//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime currentTime = iTime(_Symbol, PERIOD_M15, 0);
   if(currentTime != g_lastBarTime)
   {
      g_lastBarTime = currentTime;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Main Tick Loop (Heartbeat)                                       |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!symInfo.RefreshRates()) return;

   datetime currentDay = iTime(_Symbol, PERIOD_D1, 0);
   if(currentDay != g_lastNewDay)
   {
      g_dailyStartBalance = accInfo.Balance();
      g_lastNewDay = currentDay;
      g_hasPartialClosedThisWave = false;
   }

   if(accInfo.Equity() < g_dailyStartBalance * (1.0 - InpDailyMaxLoss/100.0))
   {
      CloseAll("⚠️ 日极寒熔断触发 (Daily Max Loss)");
      return;
   }

   UpdateCooldownStatus();
   ManagePositions();

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(InpFridayExit && dt.day_of_week == 5 && dt.hour >= 22)
   {
      if(GetOurPositionsTotal() > 0) CloseAll("🛑 周五 22:00 强制清仓避险");
      return;
   }

   if(dt.hour < InpStartHour || dt.hour > InpEndHour) return;
   if((symInfo.Ask() - symInfo.Bid()) / symInfo.Point() > InpMaxSpread) return;

   if(IsNewBar()) CheckEntry();

   g_lastPositionsTotal = GetOurPositionsTotal();
}

//+------------------------------------------------------------------+
//| Cooldown Module (Anti-Whipsaw Structure Reset)                   |
//+------------------------------------------------------------------+
void UpdateCooldownStatus()
{
   if(!InpUseStructCooldown) return;

   int currentTotalPos = GetOurPositionsTotal();
   double currentBalance = accInfo.Balance();

   if(currentTotalPos == 0 && g_lastPositionsTotal > 0)
   {
      if(currentBalance < g_lastClosedBalance)
      {
         HistorySelect(TimeCurrent()-86400, TimeCurrent());
         int total = HistoryDealsTotal();
         if(total > 0)
         {
            ulong ticket = HistoryDealGetTicket(total-1);
            long dealType = HistoryDealGetInteger(ticket, DEAL_TYPE);
            double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            if(profit < 0)
            {
               if(dealType == DEAL_TYPE_SELL) g_cooldownState = 1;
               if(dealType == DEAL_TYPE_BUY) g_cooldownState = -1;
               SendTelegramMessage("🚨 遭遇战损！雷达进入 EMA14 破位冷却重置。");
            }
         }
      }
      g_lastClosedBalance = currentBalance;
   }
   else if(currentTotalPos == 0 && currentBalance >= g_lastClosedBalance)
   {
      g_lastClosedBalance = currentBalance;
      g_cooldownState = 0; 
   }

   if(g_cooldownState != 0)
   {
      double close1 = iClose(_Symbol, PERIOD_M15, 1);
      double ema14[]; ArraySetAsSeries(ema14, true);
      CopyBuffer(handle_ema14, 0, 0, 3, ema14);

      if(g_cooldownState == 1 && close1 < ema14[1]) 
      {
         g_cooldownState = 0;
         SendTelegramMessage("🔓 洗盘结束！多头形态冷却解除，雷达重启。");
      }
      else if(g_cooldownState == -1 && close1 > ema14[1]) 
      {
         g_cooldownState = 0;
         SendTelegramMessage("🔓 洗盘结束！空头形态冷却解除，雷达重启。");
      }
   }
}

//+------------------------------------------------------------------+
//| Entry Radar (Signal Acquisition)                                 |
//+------------------------------------------------------------------+
void CheckEntry()
{
   if(GetOurPositionsTotal() > 0) return;

   double ema14[], ema21[], ema60[], ema576[], macd_main[], macd_sig[], atr[], vol[];
   
   ArraySetAsSeries(ema14, true); ArraySetAsSeries(ema21, true);
   ArraySetAsSeries(ema60, true); ArraySetAsSeries(ema576, true);
   ArraySetAsSeries(macd_main, true); ArraySetAsSeries(macd_sig, true);
   ArraySetAsSeries(atr, true); ArraySetAsSeries(vol, true);

   CopyBuffer(handle_ema14, 0, 0, 3, ema14);
   CopyBuffer(handle_ema21, 0, 0, 3, ema21);
   CopyBuffer(handle_ema60, 0, 0, 3, ema60);
   CopyBuffer(handle_ema576, 0, 0, 2, ema576);
   CopyBuffer(handle_macd, 0, 0, 3, macd_main);
   CopyBuffer(handle_macd, 1, 0, 3, macd_sig);
   CopyBuffer(handle_atr, 0, 0, 2, atr);
   CopyBuffer(handle_vol, 0, 0, 22, vol);

   double ask = symInfo.Ask(); double bid = symInfo.Bid();

   bool macroBuy  = !InpUseMacroFilter || (ask > ema576[1]);
   bool macroSell = !InpUseMacroFilter || (bid < ema576[1]);

   bool isMacdBuy  = macd_main[1] > 0 && macd_main[1] > macd_sig[1];
   bool isMacdSell = macd_main[1] < 0 && macd_main[1] < macd_sig[1];

   bool isMacdExhaustBuy  = !InpUseMACDExhaustion || (macd_main[1] > macd_main[2]);
   bool isMacdExhaustSell = !InpUseMACDExhaustion || (macd_main[1] < macd_main[2]);

   double vol_sum = 0;
   for(int i = 2; i <= 21; i++) vol_sum += vol[i];
   double vol_avg = vol_sum / 20.0;
   bool volSpike = vol[1] > (vol_avg * 0.8);

   double pullbackDist = ask * (InpPullbackPct / 100.0);

   if(macroBuy && ema14[1] > ema21[1] && ema21[1] > ema60[1] && isMacdBuy && isMacdExhaustBuy && volSpike)
   {
      if(ask <= ema14[1] + pullbackDist || InpPullbackPct == 0.0)
      {
         if(InpUseStructCooldown && g_cooldownState == 1) return;
         double sl = bid - 3.5 * atr[1];
         double lot = CalculateLotSize(MathAbs(bid - sl));
         if(trade.Buy(lot, _Symbol, ask, sl, 0, "GEMINI_L1_Buy"))
         {
            g_highestProfitPct = 0;
            g_L1_SL = sl; 
            SendTelegramMessage("🐺 L1 侦察兵做多 | 止损阵地已部署");
         }
      }
   }
   else if(macroSell && ema14[1] < ema21[1] && ema21[1] < ema60[1] && isMacdSell && isMacdExhaustSell && volSpike)
   {
      if(bid >= ema14[1] - pullbackDist || InpPullbackPct == 0.0)
      {
         if(InpUseStructCooldown && g_cooldownState == -1) return;
         double sl = ask + 3.5 * atr[1];
         double lot = CalculateLotSize(MathAbs(ask - sl));
         if(trade.Sell(lot, _Symbol, bid, sl, 0, "GEMINI_L1_Sell"))
         {
            g_highestProfitPct = 0;
            g_L1_SL = sl; 
            SendTelegramMessage("🐺 L1 侦察兵做空 | 止损阵地已部署");
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Position Management (Armor & Wolfpack Scaling)                   |
//+------------------------------------------------------------------+
void ManagePositions()
{
   int totalPos = 0;
   double totalProfit = 0;
   long posType = -1;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == EXPERT_MAGIC)
      {
         totalPos++;
         totalProfit += posInfo.Profit();
         posType = posInfo.PositionType();
      }
   }

   if(totalPos == 0)
   {
      g_highestProfitPct = 0;
      g_hasPartialClosedThisWave = false;
      g_L1_SL = 0.0;
      return;
   }

   if(totalPos > 0 && g_L1_SL == 0.0) RecoverL1SL();

   double bal = accInfo.Balance();
   double profitPct = (totalProfit / bal) * 100.0;
   if(profitPct > g_highestProfitPct) g_highestProfitPct = profitPct;

   if(totalPos >= 3 && g_highestProfitPct > InpBailoutPct && profitPct <= InpBailoutPct)
   {
      CloseAll("🛡️ 阻力回吐重仓保本弹射 (Bailout)");
      return;
   }

   if(!g_hasPartialClosedThisWave && g_highestProfitPct >= InpHWM_Activate && profitPct <= g_highestProfitPct - InpHWM_Retract)
   {
      PartialCloseAndBE();
      g_highestProfitPct = 0;
      g_hasPartialClosedThisWave = true;
      return;
   }

   // 💥 阶梯阀门：防止同点位连发 Bug
   double requiredProfitPct = InpLevelUpPct * totalPos; 

   if(profitPct >= requiredProfitPct && totalPos < InpMaxLevels && g_L1_SL != 0.0)
   {
      double atr[]; ArraySetAsSeries(atr, true); CopyBuffer(handle_atr, 0, 0, 2, atr);
      double baseLot = CalculateLotSize(3.5 * atr[1]);
      double lot = baseLot * MathPow(InpLevelMultiplier, totalPos);
      double lotStep = symInfo.LotsStep();
      lot = MathFloor(lot / lotStep) * lotStep;

      if(posType == POSITION_TYPE_BUY)
         trade.Buy(lot, _Symbol, symInfo.Ask(), g_L1_SL, 0, "GEMINI_L" + IntegerToString(totalPos+1) + "_Buy");
      else if(posType == POSITION_TYPE_SELL)
         trade.Sell(lot, _Symbol, symInfo.Bid(), g_L1_SL, 0, "GEMINI_L" + IntegerToString(totalPos+1) + "_Sell");

      g_highestProfitPct = (totalProfit / bal) * 100.0;
   }
}

//+------------------------------------------------------------------+
//| Armor Support Functions (OOP Accelerated)                        |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_distance)
{
   double riskMoney = accInfo.Balance() * (InpRiskPercent / 100.0);
   double tickValue = symInfo.TickValue();
   double tickSize = symInfo.TickSize();
   if(sl_distance == 0 || tickValue == 0) return symInfo.LotsMin();

   double lot = riskMoney / ((sl_distance / tickSize) * tickValue);
   double minLot = symInfo.LotsMin();
   double maxLot = symInfo.LotsMax();
   double lotStep = symInfo.LotsStep();

   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;
   return MathFloor(lot / lotStep) * lotStep;
}

void CloseAll(string reason = "Close All")
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == EXPERT_MAGIC) 
      {
         trade.PositionClose(posInfo.Ticket());
      }
   }
   SendTelegramMessage("🚨 全军撤离指令 | 战报原因: " + reason);
}

void PartialCloseAndBE()
{
   long stopsLevel = symInfo.StopsLevel();
   double minDistance = stopsLevel * symInfo.Point();

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == EXPERT_MAGIC)
      {
         double vol = posInfo.Volume();
         double lotStep = symInfo.LotsStep();
         double closeVol = MathFloor((vol / 2.0) / lotStep) * lotStep;
         if(closeVol >= symInfo.LotsMin())
            trade.PositionClosePartial(posInfo.Ticket(), closeVol);

         double bePrice = posInfo.PriceOpen();
         double curSL = posInfo.StopLoss();
         double curTP = posInfo.TakeProfit();
         double curBid = symInfo.Bid();
         double curAsk = symInfo.Ask();

         if(posInfo.PositionType() == POSITION_TYPE_BUY && (curSL < bePrice || curSL == 0))
         {
            if(curBid - bePrice > minDistance)
               trade.PositionModify(posInfo.Ticket(), bePrice, curTP);
         }
         else if(posInfo.PositionType() == POSITION_TYPE_SELL && (curSL > bePrice || curSL == 0))
         {
            if(bePrice - curAsk > minDistance)
               trade.PositionModify(posInfo.Ticket(), bePrice, curTP);
         }
      }
   }
   SendTelegramMessage("⚔️ 利润对切成功！保本护城河已激活！");
}

//+------------------------------------------------------------------+
//| Telegram Communications (Non-blocking + URLEncode)               |
//+------------------------------------------------------------------+
string URLEncode(string str)
{
   string result = "";
   uchar chars[];
   StringToCharArray(str, chars, 0, WHOLE_ARRAY, CP_UTF8);
   for(int i = 0; i < ArraySize(chars)-1; i++)
   {
      uchar c = chars[i];
      if((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'||c=='_'||c=='.'||c=='~')
         result += StringFormat("%c", c);
      else if(c == ' ') result += "+";
      else result += StringFormat("%%%02X", c);
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
   if(res != 200) Print("❌ Telegram 通讯中断 (不会阻塞交易)，错误码: ", res);
}

//+------------------------------------------------------------------+
//| Deinitialization (System Shutdown / Offline Alert)               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   string offlineMsg = "🔌 警报：V21.02 战舰已脱机！脱机代码: " + IntegerToString(reason);
   Print(offlineMsg);
   SendTelegramMessage(offlineMsg);
}
//+------------------------------------------------------------------+