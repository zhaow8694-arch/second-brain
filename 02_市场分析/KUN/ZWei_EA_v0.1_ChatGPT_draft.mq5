//+------------------------------------------------------------------+
//|                                                   ZWei_EA.mq5     |
//|                     Multi-layer Structure Trading System         |
//|                        Author: ChatGPT Pro (o1 pro simulation)   |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

//+---------------------- INPUT PARAMETERS -------------------------+
input double RiskPercent = 1.0;           // 单笔风险百分比
input int    MagicNumber = 20260101;

input int MA_Period = 200;
input ENUM_TIMEFRAMES TrendTF = PERIOD_D1;

input int ADX_Period = 14;
input double ADX_Threshold = 20.0;

input int ATR_Period = 14;
input double ATR_Multiplier_Danger = 2.5;

input int MACD_Fast = 12;
input int MACD_Slow = 26;
input int MACD_Signal = 9;

input int BreakoutLookback = 20;

input bool EnableBuy = true;
input bool EnableSell = true;

//+---------------------- GLOBAL HANDLES ---------------------------+
int maHandle, adxHandle, atrHandle, macdHandle;

//+---------------------- INIT -------------------------------------+
int OnInit()
{
   maHandle   = iMA(_Symbol, TrendTF, MA_Period, 0, MODE_EMA, PRICE_CLOSE);
   adxHandle  = iADX(_Symbol, _Period, ADX_Period);
   atrHandle  = iATR(_Symbol, _Period, ATR_Period);
   macdHandle = iMACD(_Symbol, _Period, MACD_Fast, MACD_Slow, MACD_Signal, PRICE_CLOSE);

   if(maHandle < 0 || adxHandle < 0 || atrHandle < 0 || macdHandle < 0)
   {
      Print("Indicator initialization failed");
      return INIT_FAILED;
   }

   return INIT_SUCCEEDED;
}

//+---------------------- UTILS ------------------------------------+
double GetBufferValue(int handle, int buffer, int shift)
{
   double val[];
   if(CopyBuffer(handle, buffer, shift, 1, val) <= 0)
      return 0;
   return val[0];
}

// 计算仓位
double CalculateLot(double stopLossPoints)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney = balance * RiskPercent / 100.0;

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   double valuePerPoint = tickValue / tickSize;

   double lot = riskMoney / (stopLossPoints * valuePerPoint);

   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;

   return NormalizeDouble(lot, 2);
}

// K线质量过滤（影线比例）
bool CandleQualityOK(bool isBuy)
{
   double open = iOpen(_Symbol, _Period, 1);
   double close = iClose(_Symbol, _Period, 1);
   double high = iHigh(_Symbol, _Period, 1);
   double low = iLow(_Symbol, _Period, 1);

   double body = MathAbs(close - open);
   double upperWick = high - MathMax(open, close);
   double lowerWick = MathMin(open, close) - low;

   if(body <= 0) return false;

   double upperRatio = upperWick / body;
   double lowerRatio = lowerWick / body;

   if(isBuy && upperRatio > 0.2) return false;
   if(!isBuy && lowerRatio > 0.2) return false;

   return true;
}

// 危险K线过滤
bool IsDangerCandle()
{
   double atr = GetBufferValue(atrHandle, 0, 1);

   double high = iHigh(_Symbol, _Period, 1);
   double low  = iLow(_Symbol, _Period, 1);

   double range = high - low;

   if(range > atr * ATR_Multiplier_Danger)
      return true;

   return false;
}

// MA200趋势过滤（日线）
bool TrendFilter(bool isBuy)
{
   double ma = GetBufferValue(maHandle, 0, 1);
   double price = iClose(_Symbol, TrendTF, 1);

   if(isBuy && price < ma) return false;
   if(!isBuy && price > ma) return false;

   return true;
}

// ADX趋势强度
bool ADXFilter()
{
   double adx = GetBufferValue(adxHandle, 0, 1);
   return adx >= ADX_Threshold;
}

// MACD结构信号（Evil MACD simplified）
bool MACDSignal(bool isBuy)
{
   double macdMain   = GetBufferValue(macdHandle, 0, 1);
   double macdSignal = GetBufferValue(macdHandle, 1, 1);

   if(isBuy && macdMain > macdSignal) return true;
   if(!isBuy && macdMain < macdSignal) return true;

   return false;
}

// 突破确认
bool BreakoutConfirm(bool isBuy)
{
   double close = iClose(_Symbol, _Period, 1);

   double highest = -DBL_MAX;
   double lowest  = DBL_MAX;

   for(int i=2; i<BreakoutLookback; i++)
   {
      double h = iHigh(_Symbol, _Period, i);
      double l = iLow(_Symbol, _Period, i);

      if(h > highest) highest = h;
      if(l < lowest) lowest = l;
   }

   if(isBuy && close > highest) return true;
   if(!isBuy && close < lowest) return true;

   return false;
}

// 趋势线验证（简化：3次触碰模拟）
bool TrendLineValidation()
{
   int touches = 0;

   for(int i=5; i<30; i++)
   {
      double h1 = iHigh(_Symbol, _Period, i);
      double h2 = iHigh(_Symbol, _Period, i+1);

      if(MathAbs(h1 - h2) < _Point * 10)
         touches++;
   }

   return touches >= 3;
}

//+---------------------- ENTRY LOGIC ------------------------------+
bool BuySignal()
{
   if(!EnableBuy) return false;

   if(IsDangerCandle()) return false;
   if(!ADXFilter()) return false;
   if(!TrendFilter(true)) return false;
   if(!CandleQualityOK(true)) return false;
   if(!MACDSignal(true)) return false;
   if(!BreakoutConfirm(true)) return false;
   if(!TrendLineValidation()) return false;

   return true;
}

bool SellSignal()
{
   if(!EnableSell) return false;

   if(IsDangerCandle()) return false;
   if(!ADXFilter()) return false;
   if(!TrendFilter(false)) return false;
   if(!CandleQualityOK(false)) return false;
   if(!MACDSignal(false)) return false;
   if(!BreakoutConfirm(false)) return false;
   if(!TrendLineValidation()) return false;

   return true;
}

//+---------------------- TRADE EXECUTION --------------------------+
void OpenTrade(bool isBuy)
{
   double atr = GetBufferValue(atrHandle, 0, 1);
   double sl_points = atr * 2;

   double lot = CalculateLot(sl_points);

   double price = isBuy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                        : SymbolInfoDouble(_Symbol, SYMBOL_BID);

   double sl = isBuy ? price - sl_points * _Point
                     : price + sl_points * _Point;

   double tp = isBuy ? price + sl_points * 2 * _Point
                     : price - sl_points * 2 * _Point;

   trade.SetExpertMagicNumber(MagicNumber);

   if(isBuy)
      trade.Buy(lot, _Symbol, price, sl, tp);
   else
      trade.Sell(lot, _Symbol, price, sl, tp);
}

//+---------------------- TRAILING STOP ----------------------------+
void ManageTrailing()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(PositionSelectByIndex(i))
      {
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber)
            continue;

         double atr = GetBufferValue(atrHandle, 0, 1);
         double trail = atr * 1.5;

         ulong ticket = PositionGetInteger(POSITION_TICKET);
         double sl = PositionGetDouble(POSITION_SL);
         double price = PositionGetDouble(POSITION_PRICE_OPEN);
         bool isBuy = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY;

         double current = isBuy ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                : SymbolInfoDouble(_Symbol, SYMBOL_ASK);

         double newSL;

         if(isBuy)
         {
            newSL = current - trail * _Point;
            if(newSL > sl)
               trade.PositionModify(ticket, newSL, 0);
         }
         else
         {
            newSL = current + trail * _Point;
            if(newSL < sl || sl == 0)
               trade.PositionModify(ticket, newSL, 0);
         }
      }
   }
}

//+---------------------- MAIN LOOP --------------------------------+
void OnTick()
{
   ManageTrailing();

   if(PositionsTotal() > 0) return;

   if(BuySignal())
      OpenTrade(true);

   if(SellSignal())
      OpenTrade(false);
}

//+---------------------- DEINIT -----------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(maHandle);
   IndicatorRelease(adxHandle);
   IndicatorRelease(atrHandle);
   IndicatorRelease(macdHandle);
}
//+------------------------------------------------------------------+
