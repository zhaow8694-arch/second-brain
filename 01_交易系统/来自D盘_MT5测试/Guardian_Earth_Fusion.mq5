#property copyright "AI Commander"
#property version   "24.00"
#property strict

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>
#include <Trade/AccountInfo.mqh>

#ifndef MARGIN_MODE_RETAIL_HEDGING
#define MARGIN_MODE_RETAIL_HEDGING 2
#endif
#ifndef TERMINAL_ALLOWED_WEBREQUEST
#define TERMINAL_ALLOWED_WEBREQUEST 71
#endif

input group "Core Risk"
input double InpRiskPercent = 2.5;
input int    InpMaxSpread = 200;
input double InpDailyMaxLoss = 5.0;
input int    InpStartHour = 0;
input int    InpEndHour = 23;
input bool   InpFridayExit = true;
input ulong  InpMagicNumber = 208501;
input string InpMagicComment = "Fusion";
input int    InpMaxLevels = 6;
input int    InpMaxSlippage = 20;

input group "Margin Safety"
input double InpMinBalanceToTrade = 100.0;
input int    InpMarginFailCooldownMinutes = 60;

input group "Wolf Pack Martingale"
input double InpLevelMultiplier = 0.6;
input double InpLevelUpPct = 0.3;
input bool   InpUseSqrtLevelUp = false;
input int    InpBailoutLevel = 3;
input double InpBailoutPct = 0.2;

input group "Dynamic Armor"
input double InpHWM_Activate = 3.0;
input double InpHWM_Retract = 1.5;
input bool   InpStrictPartialLock = false;

input group "Entry Radar"
input double InpVolMultiplier = 0.5;
input double InpPullbackPct = 0.8;
input bool   InpUseMacroFilter = false;

input group "Pre-trade Risk"
input bool   InpUseVolatilityFilter = false;
input double InpATRMultiplier_Max = 2.0;
input bool   InpUseEventFilter = false;
input bool   InpUseADXFilter = false;
input double InpMinADX = 20.0;

input group "Fast Entry"
input bool   InpUseFastEntry = true;
input double InpFastEntryADXThreshold = 30.0;
input double InpFastEntryMargin = 0.15;
input bool   InpUseProfitTrail = true;
input double InpTrailActivatePct = 1.0;
input double InpTrailDistancePct = 0.5;
input bool   InpUseATRForTrail = false;
input double InpTrailATRMultiplier = 1.5;

input group "Symbol Calibration"
input double InpSL_Multiplier_XAUUSD = 3.5;
input double InpSL_Multiplier_XAGUSD = 3.5;
input double InpSL_Multiplier_SPX500 = 3.0;
input double InpSL_Multiplier_US30 = 3.0;
input double InpSL_Multiplier_Default = 3.0;

input group "Monitoring"
input bool   InpUsePeriodicReport = true;
input int    InpReportIntervalMinutes = 30;

input group "Telegram"
enum ENUM_ACC_TYPE { ACC_AUTO, ACC_CENT, ACC_USD };
input ENUM_ACC_TYPE InpAccountType = ACC_AUTO;
input string InpTelegramToken = "";
input string InpTelegramChatID = "";

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

string CurrencyUnit = "USD";
string CurrencySymbol = "$";
string GV_BalanceKey = "";
string GV_DateKey = "";

double g_ema14[], g_ema21[], g_ema60[], g_ema576[], g_atr[];
double g_macd_main[], g_macd_sig[];
double g_vol[];
double g_adx[];

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

int g_tickCounter = 0;
int g_cachedPositionCount = -1;
int g_cachedPositionType = -1;
double g_cachedProfitPct = 0.0;
double g_cachedOldestSL = 0.0;
const int CACHE_REFRESH_INTERVAL = 5;
int g_reconnectFails = 0;

string g_telegramQueue[];

bool IsConnectedMT5()
{
   return TerminalInfoInteger(TERMINAL_CONNECTED) != 0;
}

int OnInit()
{
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("Fatal: Hedging account required");
      return(INIT_FAILED);
   }

   if(InpTelegramToken != "" && !TerminalInfoInteger(TERMINAL_ALLOWED_WEBREQUEST))
      Print("Warning: WebRequest not allowed, Telegram disabled");

   if(!EventSetTimer(1))
      Print("Warning: Timer failed");

   symInfo.Name(_Symbol); symInfo.Refresh();
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(InpMaxSlippage);

   AutoCalibrate();

   if(InpAccountType == ACC_CENT) { CurrencyUnit = "Cent"; CurrencySymbol = ""; }
   else if(InpAccountType == ACC_USD) { CurrencyUnit = "USD"; CurrencySymbol = "$"; }
   else
   {
      string accCur = AccountInfoString(ACCOUNT_CURRENCY);
      if(StringFind(accCur, "USC") >= 0 || StringFind(accCur, "cent") >= 0 || StringFind(accCur, "Cent") >= 0)
         { CurrencyUnit = "Cent"; CurrencySymbol = ""; }
      else
         { CurrencyUnit = "USD"; CurrencySymbol = "$"; }
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
   }
   else
   {
      DailyStartBalance = accInfo.Balance();
      GlobalVariableSet(GV_BalanceKey, DailyStartBalance);
      GlobalVariableSet(GV_DateKey, t.day_of_year);
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

   Print("Guardian Earth Fusion loaded on ", _Symbol);
   return INIT_SUCCEEDED;
}

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
      else Print("Telegram send failed: ", res);
   }
}

void OnDeinit(const int reason)
{
   EventKillTimer();

   if(reason != REASON_CLOSE && IsConnectedMT5())
      SendTelegramMessage("Guardian Earth Fusion offline: " + _Symbol);

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

bool ReinitializeHandles()
{
   Print("Reinitializing indicator handles...");
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

void AutoCalibrate()
{
   string s = _Symbol; StringToUpper(s);
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) { Dyn_SL_L = InpSL_Multiplier_XAUUSD; Dyn_SL_S = InpSL_Multiplier_XAUUSD; }
   else if(StringFind(s,"XAGUSD")>=0 || StringFind(s,"SILVER")>=0) { Dyn_SL_L = InpSL_Multiplier_XAGUSD; Dyn_SL_S = InpSL_Multiplier_XAGUSD; }
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0) { Dyn_SL_L = InpSL_Multiplier_SPX500; Dyn_SL_S = InpSL_Multiplier_SPX500; }
   else if(StringFind(s,"US30")>=0 || StringFind(s,"WS30")>=0 || StringFind(s,"DOW")>=0) { Dyn_SL_L = InpSL_Multiplier_US30; Dyn_SL_S = InpSL_Multiplier_US30; }
   else { Dyn_SL_L = InpSL_Multiplier_Default; Dyn_SL_S = InpSL_Multiplier_Default; }
}

double NormalizePrice(double price)
{
   double tickSize = symInfo.TickSize();
   if(tickSize <= 0) tickSize = _Point;
   return MathRound(price / tickSize) * tickSize;
}

bool IsSlippageValid(double executionPrice, double signalPrice, int maxSlippagePoints)
{
   double slippage = MathAbs(executionPrice - signalPrice) / _Point;
   if(slippage > maxSlippagePoints) return false;
   return true;
}

void HandleTradeError(int errorCode, string operation)
{
   string errorMsg = "";
   switch(errorCode)
   {
      case 10014: errorMsg = "Invalid price"; break;
      case 10016: errorMsg = "Trade rejected"; break;
      case 10018: errorMsg = "Market closed"; break;
      case 10019: errorMsg = "Insufficient funds"; break;
      case 10030: errorMsg = "Invalid SL"; break;
      case 10031: errorMsg = "Invalid TP"; break;
      default: errorMsg = "Error: " + IntegerToString(errorCode);
   }
   Print(operation + " failed: " + errorMsg);
}

bool UpdateIndicators()
{
   if(h_ema14 == INVALID_HANDLE || h_ema21 == INVALID_HANDLE || h_ema60 == INVALID_HANDLE ||
      h_atr == INVALID_HANDLE || h_vol == INVALID_HANDLE || h_macd == INVALID_HANDLE || h_adx == INVALID_HANDLE ||
      (InpUseMacroFilter && h_ema576 == INVALID_HANDLE))
   {
      g_reconnectFails++;
      if(g_reconnectFails > 5) { SendTelegramMessage("Indicators failed, cannot recover"); return false; }
      if(!ReinitializeHandles()) return false;
      int wait = 0; while(BarsCalculated(h_ema14) < 60 && wait++ < 30) Sleep(100);
      if(BarsCalculated(h_ema14) < 60) return false;
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

bool IsNewBar()
{
   datetime current = iTime(_Symbol, PERIOD_M15, 0);
   if(current != lastBarTime) { lastBarTime = current; return true; }
   return false;
}

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

bool CanTradeNow()
{
   if(TimeCurrent() - g_lastTradeTime < 1) return false;
   return true;
}

void RecordTrade()
{
   g_lastTradeTime = TimeCurrent(); g_tradesToday++;
   g_cachedPositionCount = -1;
}

double CalculateAverageEntryPrice()
{
   double totalCost = 0; double totalLots = 0;
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         totalCost += posInfo.PriceOpen() * posInfo.Volume();
         totalLots += posInfo.Volume();
      }
   }
   if(totalLots > 0) return totalCost / totalLots;
   return 0;
}

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
   else
      g_cachedPositionCount = -1;
}

void PartialCloseAndBE()
{
   double vs = symInfo.LotsStep(); double mv = symInfo.LotsMin();
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
      {
         double be = NormalizePrice(posInfo.PriceOpen());
         double currentTP = (posInfo.TakeProfit() > 0) ? NormalizePrice(posInfo.TakeProfit()) : 0;
         trade.PositionModify(posInfo.Ticket(), be, currentTP);
         double cv = MathFloor((posInfo.Volume() / 2.0) / vs) * vs;
         if(cv >= mv) trade.PositionClosePartial(posInfo.Ticket(), cv);
      }
   }
   hasPartialThisWave = true;
}

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
      return 0;
   }

   if(marginRequired > freeMargin * 0.8)
   {
      double factor = (freeMargin * 0.8) / marginRequired;
      calcVol = NormalizeDouble(MathFloor((calcVol * factor) / lotStep) * lotStep, volDigits);
      if(calcVol < minLot) return 0;
   }
   return calcVol;
}

bool SafeTradeBuy(double lot, double signalPrice, double sl)
{
   if(!CanTradeNow()) return false;
   symInfo.RefreshRates(); double ask = symInfo.Ask();
   if(!IsSlippageValid(ask, signalPrice, InpMaxSlippage)) return false;

   if(!trade.Buy(lot, _Symbol, ask, NormalizePrice(sl), 0, InpMagicComment))
      { HandleTradeError(trade.ResultRetcode(), "Buy"); return false; }

   RecordTrade();
   return true;
}

bool SafeTradeSell(double lot, double signalPrice, double sl)
{
   if(!CanTradeNow()) return false;
   symInfo.RefreshRates(); double bid = symInfo.Bid();
   if(!IsSlippageValid(bid, signalPrice, InpMaxSlippage)) return false;

   if(!trade.Sell(lot, _Symbol, bid, NormalizePrice(sl), 0, InpMagicComment))
      { HandleTradeError(trade.ResultRetcode(), "Sell"); return false; }

   RecordTrade();
   return true;
}

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

   bool longCondition = (g_ema14[1] > g_ema21[1]) &&
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
            if(SafeTradeBuy(lot, ask, sl)) SendTelegramMessage("Fusion Long: " + _Symbol);
         }
      }
   }

   bool shortCondition = (g_ema14[1] < g_ema21[1]) &&
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
            if(SafeTradeSell(lot, bid, sl)) SendTelegramMessage("Fusion Short: " + _Symbol);
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

   if(lot > 0)
   {
      bool success = false;
      if(type == POSITION_TYPE_BUY) success = SafeTradeBuy(lot, price, first_sl);
      else if(type == POSITION_TYPE_SELL) success = SafeTradeSell(lot, price, first_sl);

      if(!success) Print("Add position failed, Level=", currentLevel);
      g_cachedPositionCount = -1;
   }
}

void ManageDynamicArmor(int count, double profit_pct)
{
   if(profit_pct > HighestProfitPct) HighestProfitPct = profit_pct;
   if(count >= InpBailoutLevel && HighestProfitPct > InpBailoutPct && profit_pct <= InpBailoutPct)
   {
      double bal_before = accInfo.Balance(); CloseAllPositions();
      ReportFinancials("Bailout L" + IntegerToString(count), bal_before); return;
   }

   if(HighestProfitPct >= InpHWM_Activate && (HighestProfitPct - profit_pct) >= InpHWM_Retract)
   {
      if(!hasPartialThisWave)
      {
         double bal_before = accInfo.Balance(); PartialCloseAndBE();
         HighestProfitPct = 0.0;
         ReportFinancials("HWM Armor triggered", bal_before);
      }
   }
   if(InpUseProfitTrail) ManageTrailingStop(count, profit_pct);
}

void ManageTrailingStop(int count, double profit_pct)
{
   if(count <= 0) return;

   int tradeDir = g_cachedPositionType;
   if(tradeDir == -1) return;

   double curBid = symInfo.Bid();
   double curAsk = symInfo.Ask();

   double distPct = InpTrailDistancePct;
   if(InpUseATRForTrail && g_currentAtr > 0)
   {
      double entryAvg = CalculateAverageEntryPrice();
      if(entryAvg > 0)
      {
         if(tradeDir == POSITION_TYPE_BUY)
         {
            double newLevel = NormalizePrice(curBid - g_currentAtr * InpTrailATRMultiplier);
            if(!g_isTrailActive) { g_isTrailActive = true; g_trailingStopLevel = newLevel; }
            else if(newLevel > g_trailingStopLevel) g_trailingStopLevel = newLevel;

            if(curBid <= g_trailingStopLevel)
            { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("Trail stop (ATR)", b); }
         }
         else
         {
            double newLevel = NormalizePrice(curAsk + g_currentAtr * InpTrailATRMultiplier);
            if(!g_isTrailActive) { g_isTrailActive = true; g_trailingStopLevel = newLevel; }
            else if(newLevel < g_trailingStopLevel) g_trailingStopLevel = newLevel;

            if(curAsk >= g_trailingStopLevel)
            { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("Trail stop (ATR)", b); }
         }
         return;
      }
   }

   double entryAvg = CalculateAverageEntryPrice();
   if(entryAvg <= 0) return;
   double trailDist = entryAvg * (distPct / 100.0);

   if(tradeDir == POSITION_TYPE_BUY)
   {
      double newLevel = NormalizePrice(curBid - trailDist);
      if(!g_isTrailActive) { g_isTrailActive = true; g_trailingStopLevel = newLevel; }
      else if(newLevel > g_trailingStopLevel) g_trailingStopLevel = newLevel;

      if(curBid <= g_trailingStopLevel)
      { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("Trail stop", b); }
   }
   else
   {
      double newLevel = NormalizePrice(curAsk + trailDist);
      if(!g_isTrailActive) { g_isTrailActive = true; g_trailingStopLevel = newLevel; }
      else if(newLevel < g_trailingStopLevel) g_trailingStopLevel = newLevel;

      if(curAsk >= g_trailingStopLevel)
      { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("Trail stop", b); }
   }
}

int CalculateDynamicMaxLevels()
{
   if(!InpUseVolatilityFilter) return InpMaxLevels;
   double atrValue = g_currentAtr; if(atrValue <= 0 || ArraySize(g_atr) < 3) return InpMaxLevels;
   double prevAtr = g_atr[2]; if(prevAtr <= 0) return InpMaxLevels;

   double atrMultiplier = MathAbs(g_atr[1] / prevAtr);
   if(atrMultiplier > InpATRMultiplier_Max) return MathMax(1, InpMaxLevels - 2);
   return InpMaxLevels;
}

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

void SendTelegramMessage(string msg)
{
   if(InpTelegramToken == "" || InpTelegramChatID == "") return;
   if(StringLen(msg) > 4000) msg = StringSubstr(msg, 0, 3900) + "\n...";

   int sz = ArraySize(g_telegramQueue);
   ArrayResize(g_telegramQueue, sz+1);
   g_telegramQueue[sz] = msg;
}

void ReportFinancials(string baseMsg, double bal_before=0)
{
   double bal_after = accInfo.Balance();
   double delta = (bal_before > 0) ? (bal_after - bal_before) : 0;
   double dailyTotal = bal_after - DailyStartBalance;
   string emoji = (delta >= 0) ? "Profit: +" : "Loss: -";
   string dailyEmoji = (dailyTotal >= 0) ? "Daily: +" : "Daily: -";

   string finalMsg = baseMsg + "\n" + emoji + CurrencySymbol + DoubleToString(MathAbs(delta), 2) + "\n" +
                     dailyEmoji + CurrencySymbol + DoubleToString(MathAbs(dailyTotal), 2) + "\n" +
                     "Balance: " + CurrencySymbol + DoubleToString(bal_after, 2);
   SendTelegramMessage(finalMsg);
}

void SendPeriodicStatusReport(int posCount, double profitPct)
{
   double equity = accInfo.Equity(), dailyPnL = equity - DailyStartBalance;
   double dailyPnLPct = (DailyStartBalance > 0) ? (dailyPnL / DailyStartBalance * 100.0) : 0;
   string posType = (g_cachedPositionType == POSITION_TYPE_BUY) ? "Long" : (g_cachedPositionType == POSITION_TYPE_SELL ? "Short" : "Mixed");

   string report = "Status Report:\nEquity: " + CurrencySymbol + DoubleToString(equity, 2) + "\n" +
                   "P&L: " + (dailyPnL >= 0 ? "+" : "") + DoubleToString(dailyPnLPct, 2) + "%\n" +
                   "Positions: " + IntegerToString(posCount) + " | Dir: " + posType + "\nFloat: " + DoubleToString(profitPct, 2) + "%\n";
   if(g_isTrailActive) report += "Trail: " + DoubleToString(g_trailingStopLevel, _Digits) + "\n";
   SendTelegramMessage(report);
}

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
      if(t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("Weekend flatten", b); }
      if(isFirstTick) isFirstTick = false;
      return;
   }

   if(DailyStartBalance > 0 && (eq - DailyStartBalance) / DailyStartBalance * 100.0 <= -InpDailyMaxLoss)
   {
      if(t_pos > 0) { double b = accInfo.Balance(); CloseAllPositions(); ReportFinancials("Daily max loss", b); }
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
         Print("Indicator data may be stale, skipping trend breach check");
      }
      else
      {
         double c1 = iClose(_Symbol, PERIOD_M15, 1);
         if(c1 > 0 && ((c_type == POSITION_TYPE_BUY && c1 < g_ema60[1]) || (c_type == POSITION_TYPE_SELL && c1 > g_ema60[1])))
         {
            double b = accInfo.Balance(); CloseAllPositions();
            ReportFinancials("Trend breach, emergency exit", b);
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