#property copyright "Guardian Earth"
#property version   "2.00"
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

input group "Core Risk Parameters"
input double InpRiskBasePct          = 0.8;
input double InpMaxDailyDrawdownPct  = 10.0;
input int    InpMaxConcurrentPos     = 2;
input int    InpMagicNumber          = 25050901;
input int    InpSessionLondonFrom    = 8;
input int    InpSessionLondonTo      = 16;
input int    InpSessionNYFrom        = 13;
input int    InpSessionNYTo          = 21;
input int    InpWeekendCloseHour     = 21;
input bool   InpEnableSessionFilter  = true;
input bool   InpSendPush             = false;
input int    InpMaxSpreadPoints      = 280;
input int    InpMaxSlippagePoints    = 15;
input bool   InpEnableVolFilter      = true;
input int    InpSignalScoreMin       = 2;
input int    InpTradeDirection       = 0;
input int    InpMaxTradesPerDay      = 3;
input double InpMinBalanceToTrade    = 200.0;
input int    InpMarginFailCooldownMin = 10;

input group "Entry Parameters"
input int    InpEmaFastM15  = 14;
input int    InpEmaMidM15   = 21;
input int    InpEmaSlowM15  = 60;
input int    InpAtrPeriodM15 = 14;
input int    InpMacdFastH1  = 12;
input int    InpMacdSlowH1  = 26;
input int    InpMacdSigH1   = 9;
input int    InpEmaLongH4   = 576;
input double InpVolMomentumK = 1.20;

input group "Exit Parameters"
input double InpHwmRetreatLong  = 0.35;
input double InpHwmRetreatShort = 0.35;
input double InpTakeProfitAtrMul = 2.2;
input double InpTrailStartAtrMul = 1.2;
input double InpTrailAtrMul      = 1.0;

input group "Symbol Parameters"
input double InpRiskXAUUSD        = 0.80;
input double InpLongStopMulXAUUSD = 3.5;
input double InpShortStopMulXAUUSD= 2.5;
input double InpRiskXAGUSD        = 0.80;
input double InpLongStopMulXAGUSD = 3.5;
input double InpShortStopMulXAGUSD= 2.5;
input double InpRiskSPX500        = 0.80;
input double InpLongStopMulSPX500 = 3.5;
input double InpShortStopMulSPX500= 2.5;
input double InpRiskUS30          = 0.80;
input double InpLongStopMulUS30   = 3.5;
input double InpShortStopMulUS30  = 2.5;

int g_hEmaFastM15 = INVALID_HANDLE;
int g_hEmaMidM15  = INVALID_HANDLE;
int g_hEmaSlowM15 = INVALID_HANDLE;
int g_hAtrM15     = INVALID_HANDLE;
int g_hMacdH1     = INVALID_HANDLE;
int g_hEmaH4      = INVALID_HANDLE;

datetime g_lastSignalBar  = 0;
datetime g_dayStartTime   = 0;
double   g_dayStartEquity = 0.0;
datetime g_marginFailUntil = 0;
int      g_todayTrades    = 0;
int      g_tradeDay       = -1;

string   g_symbols[]      = {"XAUUSD","XAGUSD","SPX500","US30"};
double   g_hwmPrice[];
bool     g_halfClosed[];

int SymbolIndex(const string symbol)
{
   for(int i=0; i<ArraySize(g_symbols); i++)
      if(g_symbols[i] == symbol) return i;
   return -1;
}

double GetRiskPercent(const string symbol)
{
   if(symbol == "XAUUSD") return InpRiskXAUUSD;
   if(symbol == "XAGUSD") return InpRiskXAGUSD;
   if(symbol == "SPX500") return InpRiskSPX500;
   if(symbol == "US30")   return InpRiskUS30;
   return InpRiskBasePct;
}

double GetLongSLMul(const string symbol)
{
   if(symbol == "XAUUSD") return InpLongStopMulXAUUSD;
   if(symbol == "XAGUSD") return InpLongStopMulXAGUSD;
   if(symbol == "SPX500") return InpLongStopMulSPX500;
   if(symbol == "US30")   return InpLongStopMulUS30;
   return 3.5;
}

double GetShortSLMul(const string symbol)
{
   if(symbol == "XAUUSD") return InpShortStopMulXAUUSD;
   if(symbol == "XAGUSD") return InpShortStopMulXAGUSD;
   if(symbol == "SPX500") return InpShortStopMulSPX500;
   if(symbol == "US30")   return InpShortStopMulUS30;
   return 2.5;
}

string DescribeRetcode(const long retcode)
{
   switch((int)retcode)
   {
      case TRADE_RETCODE_DONE:               return "DONE";
      case TRADE_RETCODE_DONE_PARTIAL:        return "DONE_PARTIAL";
      case TRADE_RETCODE_PLACED:             return "PLACED";
      case TRADE_RETCODE_REJECT:             return "REJECT";
      case TRADE_RETCODE_CANCEL:             return "CANCEL";
      case TRADE_RETCODE_REQUOTE:            return "REQUOTE";
      case TRADE_RETCODE_PRICE_CHANGED:       return "PRICE_CHANGED";
      case TRADE_RETCODE_PRICE_OFF:           return "PRICE_OFF";
      case TRADE_RETCODE_INVALID_VOLUME:      return "INVALID_VOLUME";
      case TRADE_RETCODE_INVALID_STOPS:       return "INVALID_STOPS";
      case TRADE_RETCODE_INVALID_PRICE:       return "INVALID_PRICE";
      case TRADE_RETCODE_TRADE_DISABLED:      return "TRADE_DISABLED";
      case TRADE_RETCODE_NO_MONEY:           return "NO_MONEY";
      case TRADE_RETCODE_INVALID_EXPIRATION:  return "INVALID_EXPIRATION";
      case TRADE_RETCODE_INVALID_FILL:        return "INVALID_FILL";
      case TRADE_RETCODE_TIMEOUT:            return "TIMEOUT";
      case TRADE_RETCODE_INVALID:             return "INVALID";
      default:                               return "UNKNOWN(" + (string)retcode + ")";
   }
}

void ReportTradeFailure(const string action, const string symbol, const ulong ticket, const long retcode, const int winerr)
{
   string detail = "GE trade failed. action=" + action + ", symbol=" + symbol;
   if(ticket > 0) detail += ", ticket=" + (string)ticket;
   detail += ", retcode=" + DescribeRetcode(retcode) + ", last_error=" + (string)winerr;
   Print(detail);
}

bool CheckTradePermissions(const string symbol)
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
   long trade_mode = (long)SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
   if(trade_mode == SYMBOL_TRADE_MODE_DISABLED) return false;
   long stops_level = (long)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   if(stops_level < 0) return false;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq < InpMinBalanceToTrade) return false;
   return true;
}

bool CheckSpread(const string symbol)
{
   if(InpMaxSpreadPoints <= 0) return true;
   long spread = (long)SymbolInfoInteger(symbol, SYMBOL_SPREAD);
   return (spread <= InpMaxSpreadPoints && spread >= 0);
}

void UpdateDailyCounters()
{
   MqlDateTime tm;
   TimeToStruct(TimeCurrent(), tm);
   if(tm.day != g_tradeDay)
   {
      g_tradeDay = tm.day;
      g_todayTrades = 0;
   }
}

bool ExecuteTradeResult(const bool ok, const string action, const string symbol, const ulong ticket)
{
   long rc = trade.ResultRetcode();
   int le = GetLastError();
   if(ok)
   {
      Print("GE trade ok: " + action + " | " + symbol + " | ticket=" + (string)trade.ResultOrder());
      return true;
   }
   ReportTradeFailure(action, symbol, ticket, rc, le);
   if(rc == TRADE_RETCODE_NO_MONEY || rc == TRADE_RETCODE_INVALID_VOLUME || rc == TRADE_RETCODE_INVALID_PRICE)
   {
      g_marginFailUntil = TimeCurrent() + 60 * MathMax(1, InpMarginFailCooldownMin);
   }
   return false;
}

bool ClosePositionSafely(const ulong ticket, const string reason="")
{
   if(TimeCurrent() < g_marginFailUntil) return false;
   if(!CheckTradePermissions(_Symbol)) return false;
   bool ok = trade.PositionClose(ticket);
   return ExecuteTradeResult(ok, "ClosePosition" + (reason != "" ? ("(" + reason + ")") : ""), _Symbol, ticket);
}

bool ClosePartialSafely(const ulong ticket, const double volume, const string reason="")
{
   if(TimeCurrent() < g_marginFailUntil) return false;
   if(!CheckTradePermissions(_Symbol)) return false;
   bool ok = trade.PositionClosePartial(ticket, volume);
   return ExecuteTradeResult(ok, "ClosePartial(" + reason + ")", _Symbol, ticket);
}

bool ModifyPositionSafely(const ulong ticket, const double stopLoss, const double takeProfit, const string reason="")
{
   if(TimeCurrent() < g_marginFailUntil) return false;
   if(!CheckTradePermissions(_Symbol)) return false;
   bool ok = trade.PositionModify(ticket, stopLoss, takeProfit);
   return ExecuteTradeResult(ok, "PositionModify(" + reason + ")", _Symbol, ticket);
}

bool GetBufValue(const int handle, const int buffer, const int shift, double &value)
{
   double arr[];
   ArraySetAsSeries(arr, true);
   if(CopyBuffer(handle, buffer, shift, 1, arr) < 1) return false;
   value = arr[0];
   return true;
}

double NormalizeVolume(const double vol, const string symbol)
{
   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double minLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   if(lotStep <= 0.0 || minLot <= 0.0 || maxLot <= 0.0) return 0.0;
   double v = MathFloor(vol / lotStep) * lotStep;
   v = MathMax(minLot, MathMin(maxLot, v));
   int digits = 2;
   if(lotStep < 0.01) digits = 3;
   if(lotStep < 0.001) digits = 4;
   return NormalizeDouble(v, digits);
}

double CalcLotByATR(const string symbol, const double stopDistance)
{
   if(stopDistance <= 0.0) return 0.0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity <= 0.0) return 0.0;
   double riskMoney = equity * (GetRiskPercent(symbol) / 100.0);
   double tickSize  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickVal   = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize <= 0.0 || tickVal <= 0.0) return 0.0;
   double lossPerLot = (stopDistance / tickSize) * tickVal;
   if(lossPerLot <= 0.0) return 0.0;
   double lot = riskMoney / lossPerLot;
   return NormalizeVolume(lot, symbol);
}

double NormalizePriceBySymbol(const string symbol, const double price)
{
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   return NormalizeDouble(price, digits);
}

bool StopLossIsTradable(const string symbol, const long type, const double stopLoss)
{
   if(stopLoss <= 0.0) return false;
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   long stopsLevel = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist = MathMax((long)1, stopsLevel) * point;
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   if(type == POSITION_TYPE_BUY) return (stopLoss < bid - minDist);
   if(type == POSITION_TYPE_SELL) return (stopLoss > ask + minDist);
   return false;
}

int CountMyPositions(const string symbol="")
{
   int count = 0;
   int total = PositionsTotal();
   for(int i = total - 1; i >= 0; --i)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(symbol != "" && PositionGetString(POSITION_SYMBOL) != symbol) continue;
      count++;
   }
   return count;
}

bool IsInTradeSession()
{
   if(!InpEnableSessionFilter) return true;
   MqlDateTime tm;
   TimeToStruct(TimeCurrent(), tm);
   bool london = (tm.hour >= InpSessionLondonFrom && tm.hour <= InpSessionLondonTo);
   bool ny     = (tm.hour >= InpSessionNYFrom && tm.hour <= InpSessionNYTo);
   return (london || ny);
}

void UpdateDailyDrawdown()
{
   datetime today = iTime(_Symbol, PERIOD_D1, 0);
   if(today != g_dayStartTime)
   {
      g_dayStartTime   = today;
      g_dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   }
   if(g_dayStartEquity <= 0.0) return;
   double dd = (g_dayStartEquity - AccountInfoDouble(ACCOUNT_EQUITY)) / g_dayStartEquity * 100.0;
   if(dd >= InpMaxDailyDrawdownPct)
   {
      for(int i=PositionsTotal()-1; i>=0; --i)
      {
         ulong ticket = PositionGetTicket(i);
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
         if(!ClosePositionSafely(ticket, "daily drawdown")) ExecuteTradeResult(false, "ClosePosition(daily_drawdown)", _Symbol, ticket);
      }
      SendNotification("Guardian Earth: daily drawdown cutoff triggered, all positions closed.");
   }
}

int DetectSignal(datetime &signalBarTime)
{
   if(!IsInTradeSession()) return 0;

   double e14[], e21[], e60[], atr[], macdMain[], macdSig[], hist[], e4h[];
   ArrayResize(e14,3); ArrayResize(e21,3); ArrayResize(e60,3);
   ArrayResize(atr,3); ArrayResize(macdMain,3); ArrayResize(macdSig,3);
   ArrayResize(hist,3); ArrayResize(e4h,2);
   ArraySetAsSeries(e14, true); ArraySetAsSeries(e21, true); ArraySetAsSeries(e60, true);
   ArraySetAsSeries(atr, true); ArraySetAsSeries(macdMain, true); ArraySetAsSeries(macdSig, true);
   ArraySetAsSeries(hist, true); ArraySetAsSeries(e4h, true);

   if(CopyBuffer(g_hEmaFastM15,0,1,3,e14) < 3) return 0;
   if(CopyBuffer(g_hEmaMidM15,0,1,3,e21) < 3) return 0;
   if(CopyBuffer(g_hEmaSlowM15,0,1,3,e60) < 3) return 0;
   if(CopyBuffer(g_hAtrM15,0,1,3,atr) < 3) return 0;
   if(CopyBuffer(g_hMacdH1,0,1,3,macdMain) < 3) return 0;
   if(CopyBuffer(g_hMacdH1,1,1,3,macdSig) < 3) return 0;
   if(CopyBuffer(g_hEmaH4,0,1,2,e4h) < 2) return 0;

   for(int i=0; i<3; ++i)
      hist[i] = macdMain[i] - macdSig[i];

   double v1 = (double)iVolume(_Symbol, PERIOD_M15, 1);
   double v0 = (double)iVolume(_Symbol, PERIOD_M15, 2);
   bool volOk = true;
   if(InpEnableVolFilter)
   {
      if(v0 <= 0.0 || v1 < v0 * InpVolMomentumK) volOk = false;
   }

   bool h4Up = e4h[0] > e4h[1];
   bool h4Dn = e4h[0] < e4h[1];
   bool maBull = (e14[0] > e21[0] && e21[0] > e60[0]);
   bool maBear = (e14[0] < e21[0] && e21[0] < e60[0]);
   bool breakBull = (iClose(_Symbol, PERIOD_M15, 1) > e14[0]);
   bool breakBear = (iClose(_Symbol, PERIOD_M15, 1) < e14[0]);
   bool macdBull = (hist[0] > 0.0 && hist[0] > hist[1]);
   bool macdBear = (hist[0] < 0.0 && hist[0] < hist[1]);
   bool atrPositive = (atr[1] > 0.0);

   int bullScore = 0;
   int bearScore = 0;
   if(h4Up) bullScore++;
   if(h4Dn) bearScore++;
   if(maBull) bullScore++;
   if(maBear) bearScore++;
   if(breakBull) bullScore++;
   if(breakBear) bearScore++;
   if(macdBull) bullScore++;
   if(macdBear) bearScore++;
   if(InpEnableVolFilter)
   {
      if(volOk) bullScore++;
      if(volOk) bearScore++;
   }
   if(atrPositive)
   {
      bullScore++;
      bearScore++;
   }

   signalBarTime = iTime(_Symbol, PERIOD_M15, 1);
   if(InpTradeDirection >= 0 && bullScore >= InpSignalScoreMin && bullScore > bearScore) return 1;
   if(InpTradeDirection <= 0 && bearScore >= InpSignalScoreMin && bearScore > bullScore) return -1;
   return 0;
}

void EnsureSymbolState(const string symbol)
{
   int idx = SymbolIndex(symbol);
   if(idx < 0) return;
   bool hasPos = (CountMyPositions(symbol) > 0);
   if(!hasPos)
   {
      g_hwmPrice[idx] = 0.0;
      g_halfClosed[idx] = false;
   }
}

void UpdatePositionBySymbol(const string symbol, const int signalDir)
{
   int idx = SymbolIndex(symbol);
   if(idx < 0) return;

   for(int i=PositionsTotal()-1; i>=0; --i)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != symbol) continue;

      long type = PositionGetInteger(POSITION_TYPE);
      double entry = PositionGetDouble(POSITION_PRICE_OPEN);
      double vol   = PositionGetDouble(POSITION_VOLUME);
      double sl    = PositionGetDouble(POSITION_SL);
      double tp    = PositionGetDouble(POSITION_TP);
      double price = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(symbol, SYMBOL_BID) : SymbolInfoDouble(symbol, SYMBOL_ASK);
      double atr;
      if(!GetBufValue(g_hAtrM15, 0, 1, atr) || atr <= 0.0) continue;

      if((signalDir == 1 && type == POSITION_TYPE_SELL) || (signalDir == -1 && type == POSITION_TYPE_BUY))
      {
         if(!ClosePositionSafely(ticket, "reverse signal")) ExecuteTradeResult(false, "ClosePosition(reverse_signal)", symbol, ticket);
         continue;
      }

      double initSl = (type == POSITION_TYPE_BUY) ? (entry - atr * GetLongSLMul(symbol)) : (entry + atr * GetShortSLMul(symbol));
      initSl = NormalizePriceBySymbol(symbol, initSl);
      if(sl == 0.0 && StopLossIsTradable(symbol, type, initSl)) ModifyPositionSafely(ticket, initSl, tp, "initial stop init");

      if(g_hwmPrice[idx] <= 0.0) g_hwmPrice[idx] = price;
      if(type == POSITION_TYPE_BUY)
         g_hwmPrice[idx] = MathMax(g_hwmPrice[idx], price);
      else
         g_hwmPrice[idx] = MathMin(g_hwmPrice[idx], price);

      bool retreat = (type == POSITION_TYPE_BUY)
         ? (price <= g_hwmPrice[idx] - atr * InpHwmRetreatLong)
         : (price >= g_hwmPrice[idx] + atr * InpHwmRetreatShort);

      if(retreat && !g_halfClosed[idx])
      {
         double half = NormalizeVolume(vol / 2.0, symbol);
         if(half > 0.0)
         {
            ClosePartialSafely(ticket, half, "HWM retreat");
            g_halfClosed[idx] = true;
         }
      }

      if(g_halfClosed[idx])
      {
         double newSl = entry;
         if((type == POSITION_TYPE_BUY && (sl == 0.0 || sl < entry)) || (type == POSITION_TYPE_SELL && (sl == 0.0 || sl > entry)))
         {
            newSl = NormalizePriceBySymbol(symbol, newSl);
            if(StopLossIsTradable(symbol, type, newSl)) ModifyPositionSafely(ticket, newSl, tp, "break-even");
         }
      }

      double profitMove = (type == POSITION_TYPE_BUY) ? (price - entry) : (entry - price);
      if(profitMove >= atr * InpTrailStartAtrMul)
      {
         double trailSl = (type == POSITION_TYPE_BUY) ? (price - atr * InpTrailAtrMul) : (price + atr * InpTrailAtrMul);
         trailSl = NormalizePriceBySymbol(symbol, trailSl);
         bool improve = (type == POSITION_TYPE_BUY)
            ? (sl == 0.0 || trailSl > sl)
            : (sl == 0.0 || trailSl < sl);
         if(improve && StopLossIsTradable(symbol, type, trailSl)) ModifyPositionSafely(ticket, trailSl, tp, "atr trail");
      }
   }
}

void DrawHUD()
{
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double bal= AccountInfoDouble(ACCOUNT_BALANCE);
   double dd = (g_dayStartEquity > 0.0) ? ((g_dayStartEquity - eq) / g_dayStartEquity) * 100.0 : 0.0;
   int pos = CountMyPositions();
   string txt = StringFormat("Guardian Earth | Eq: %.2f | Bal: %.2f | DD: %.2f%% | Pos: %d",
                            eq, bal, dd, pos);
   if(ObjectFind(0, "GE_HUD") < 0) ObjectCreate(0, "GE_HUD", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "GE_HUD", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, "GE_HUD", OBJPROP_XDISTANCE, 10);
   ObjectSetInteger(0, "GE_HUD", OBJPROP_YDISTANCE, 10);
   ObjectSetInteger(0, "GE_HUD", OBJPROP_FONTSIZE, 11);
   ObjectSetInteger(0, "GE_HUD", OBJPROP_COLOR, clrAqua);
   ObjectSetInteger(0, "GE_HUD", OBJPROP_BACK, true);
   ObjectSetString(0, "GE_HUD", OBJPROP_TEXT, txt);
}

void CloseWeekendPositions()
{
   MqlDateTime tm;
   TimeToStruct(TimeCurrent(), tm);
   if(tm.day_of_week == 5 && tm.hour >= InpWeekendCloseHour)
   {
      for(int i = PositionsTotal()-1; i >= 0; --i)
      {
         ulong ticket = PositionGetTicket(i);
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
         ClosePositionSafely(ticket, "weekend flatten");
      }
   }
}

int OnInit()
{
   g_hEmaFastM15 = iMA(_Symbol, PERIOD_M15, InpEmaFastM15, 0, MODE_EMA, PRICE_CLOSE);
   g_hEmaMidM15  = iMA(_Symbol, PERIOD_M15, InpEmaMidM15, 0, MODE_EMA, PRICE_CLOSE);
   g_hEmaSlowM15 = iMA(_Symbol, PERIOD_M15, InpEmaSlowM15, 0, MODE_EMA, PRICE_CLOSE);
   g_hAtrM15     = iATR(_Symbol, PERIOD_M15, InpAtrPeriodM15);
   g_hMacdH1     = iMACD(_Symbol, PERIOD_H1, InpMacdFastH1, InpMacdSlowH1, InpMacdSigH1, PRICE_CLOSE);
   g_hEmaH4      = iMA(_Symbol, PERIOD_H4, InpEmaLongH4, 0, MODE_EMA, PRICE_CLOSE);

   if(g_hEmaFastM15 == INVALID_HANDLE || g_hEmaMidM15 == INVALID_HANDLE || g_hEmaSlowM15 == INVALID_HANDLE ||
      g_hAtrM15 == INVALID_HANDLE || g_hMacdH1 == INVALID_HANDLE || g_hEmaH4 == INVALID_HANDLE)
   {
      Print("Indicator init failed");
      return INIT_FAILED;
   }

   ArrayResize(g_hwmPrice, ArraySize(g_symbols));
   ArrayResize(g_halfClosed, ArraySize(g_symbols));
   for(int i=0; i<ArraySize(g_symbols); i++){ g_hwmPrice[i]=0.0; g_halfClosed[i]=false; }

   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(MathMax(1, InpMaxSlippagePoints));
   trade.SetTypeFillingBySymbol(_Symbol);
   EventSetTimer(1);

   Print("Guardian Earth Classic loaded on ", _Symbol);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectDelete(0, "GE_HUD");
   if(g_hEmaFastM15 != INVALID_HANDLE) IndicatorRelease(g_hEmaFastM15);
   if(g_hEmaMidM15  != INVALID_HANDLE) IndicatorRelease(g_hEmaMidM15);
   if(g_hEmaSlowM15 != INVALID_HANDLE) IndicatorRelease(g_hEmaSlowM15);
   if(g_hAtrM15     != INVALID_HANDLE) IndicatorRelease(g_hAtrM15);
   if(g_hMacdH1     != INVALID_HANDLE) IndicatorRelease(g_hMacdH1);
   if(g_hEmaH4      != INVALID_HANDLE) IndicatorRelease(g_hEmaH4);
}

void OnTick()
{
   UpdateDailyDrawdown();
   UpdateDailyCounters();

   for(int i=0; i<ArraySize(g_symbols); i++)
      EnsureSymbolState(g_symbols[i]);

   bool trade_allowed = CheckTradePermissions(_Symbol);
   bool spread_ok = CheckSpread(_Symbol);
   bool cooldown_ok = (TimeCurrent() >= g_marginFailUntil);

   UpdatePositionBySymbol(_Symbol, 0);

   datetime sigBar = 0;
   int dir = DetectSignal(sigBar);
   if(dir == 0 || sigBar == g_lastSignalBar) return;
   g_lastSignalBar = sigBar;

   UpdatePositionBySymbol(_Symbol, dir);

   if(!trade_allowed || !spread_ok || !cooldown_ok) return;
   if(g_todayTrades >= InpMaxTradesPerDay) return;
   if(CountMyPositions() >= InpMaxConcurrentPos) return;

   double atr;
   if(!GetBufValue(g_hAtrM15, 0, 1, atr) || atr <= 0.0) return;
   double stop = atr * (dir > 0 ? GetLongSLMul(_Symbol) : GetShortSLMul(_Symbol));
   double lot = CalcLotByATR(_Symbol, stop);
   if(lot <= 0.0) return;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double openPrice = (dir > 0) ? ask : bid;
   double sl  = (dir > 0) ? (openPrice - stop) : (openPrice + stop);
   double tp  = 0.0;
   if(InpTakeProfitAtrMul > 0.0)
      tp = (dir > 0) ? (openPrice + atr * InpTakeProfitAtrMul) : (openPrice - atr * InpTakeProfitAtrMul);
   sl = NormalizePriceBySymbol(_Symbol, sl);
   if(tp > 0.0) tp = NormalizePriceBySymbol(_Symbol, tp);

   bool ok = (dir > 0)
              ? trade.Buy(lot, _Symbol, 0, sl, tp, "GuardianEarth")
              : trade.Sell(lot, _Symbol, 0, sl, tp, "GuardianEarth");
   if(!ExecuteTradeResult(ok, (dir > 0 ? "BUY" : "SELL") + " open", _Symbol, 0)) return;
   g_todayTrades++;

   if(InpSendPush)
      SendNotification("GuardianEarth order: " + _Symbol + " " + (dir > 0 ? "BUY" : "SELL") + " lot " + DoubleToString(lot, 2));
}

void OnTimer()
{
   DrawHUD();
   CloseWeekendPositions();
}