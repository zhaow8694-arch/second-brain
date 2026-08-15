//+------------------------------------------------------------------+
//|                               Vegas_Trend_Master_H4_Matrix_V6.mq5|
//|                    Created by 编码助手 | 2024 多品种动态ATR矩阵版 |
//+------------------------------------------------------------------+
#property copyright "编码助手"
#property version   "6.00"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade         trade;
CPositionInfo  posInfo;

//--- 开放的系统设置 ---
input string   InpSymbols = "XAUUSD,EURUSD,SP500,CHINA50"; 
input double   InpRiskPercent = 1.0;         // 单笔风险比例
input int      InpMagicNumber = 888888;      
input bool     InpUseBreakEven = true;       

//--- [V6.0 核心升级] 动态 ATR 移动止损 ---
input double   InpTrailingATR_Multiplier = 2.0;  // 移动止损距离 (几倍的ATR)
input double   InpTrailingStep_ATR       = 0.2;  // 移动步进距离 (几倍的ATR)

//--- 均线与指标参数 ---
input int      InpEma12  = 12;   
input int      InpEma144 = 144;  
input int      InpEma169 = 169;  
input int      InpEma288 = 288;  
input int      InpEma338 = 338;  
input int      InpEma576 = 576;  
input int      InpEma676 = 676;  
input int      InpATR_Period = 14;
input int      InpADX_Period = 14;

//--- 结构体 ---
struct SymbolData
  {
   string   symbolName;
   int      h_ema12, h_ema144, h_ema169, h_ema288, h_ema338, h_ema576, h_ema676;
   int      h_adx, h_atr; 
   double   optimized_adx; // [V6.0] 专属字典参数
   datetime lastBarTime;
  };

SymbolData symbols[];
int lastReportDay = -1; 

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);
   string result[];
   int count = StringSplit(InpSymbols, StringGetCharacter(",", 0), result);
   if(count == 0) return(INIT_FAILED);

   ArrayResize(symbols, count);

   for(int i = 0; i < count; i++)
     {
      StringTrimLeft(result[i]); StringTrimRight(result[i]);
      string sym = result[i];
      symbols[i].symbolName = sym;
      SymbolSelect(sym, true); 

      // [V6.0] 核心字典逻辑：为不同品种赋予不同的灵魂
      if(StringFind(sym, "XAU") >= 0)      symbols[i].optimized_adx = 15.0;
      else if(StringFind(sym, "EUR") >= 0) symbols[i].optimized_adx = 15.0;
      else if(StringFind(sym, "SP500")>=0) symbols[i].optimized_adx = 10.0; // 慢牛不需要高ADX
      else if(StringFind(sym, "CHINA")>=0) symbols[i].optimized_adx = 30.0; // 极度震荡，必须高门槛
      else                                 symbols[i].optimized_adx = 20.0; // 默认值

      symbols[i].h_ema12  = iMA(sym, PERIOD_H4, InpEma12, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema144 = iMA(sym, PERIOD_H4, InpEma144, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema169 = iMA(sym, PERIOD_H4, InpEma169, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema288 = iMA(sym, PERIOD_H4, InpEma288, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema338 = iMA(sym, PERIOD_H4, InpEma338, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema576 = iMA(sym, PERIOD_H4, InpEma576, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema676 = iMA(sym, PERIOD_H4, InpEma676, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_adx    = iADX(sym, PERIOD_H4, InpADX_Period);
      symbols[i].h_atr    = iATR(sym, PERIOD_H4, InpATR_Period);
      
      symbols[i].lastBarTime = 0;
     }
     
   Print("🚀 Vegas V6.0 矩阵版启动！专属 ADX 字典与 ATR 动态风控已加载。");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   for(int i = 0; i < ArraySize(symbols); i++)
     {
      ProcessSymbol(i);
      ApplyATRTrailingStop(i); 
     }
  }

//+------------------------------------------------------------------+
//| [V6.0] 动态 ATR 移动止损                                           |
//+------------------------------------------------------------------+
void ApplyATRTrailingStop(int index)
  {
   string sym = symbols[index].symbolName;
   double atr[];
   CopyBuffer(symbols[index].h_atr, 0, 0, 1, atr);
   if(atr[0] == 0) return;

   double trailingDistance = atr[0] * InpTrailingATR_Multiplier;
   double trailingStep = atr[0] * InpTrailingStep_ATR;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == sym && posInfo.Magic() == InpMagicNumber)
        {
         double price = (posInfo.PositionType() == POSITION_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_BID) : SymbolInfoDouble(sym, SYMBOL_ASK);
         double sl = posInfo.StopLoss();

         if(posInfo.PositionType() == POSITION_TYPE_BUY)
           {
            if(price - posInfo.PriceOpen() > trailingDistance)
              {
               if(sl < price - (trailingDistance + trailingStep))
                  trade.PositionModify(posInfo.Ticket(), price - trailingDistance, 0);
              }
           }
         else if(posInfo.PositionType() == POSITION_TYPE_SELL)
           {
            if(posInfo.PriceOpen() - price > trailingDistance)
              {
               if(sl > price + (trailingDistance + trailingStep) || sl == 0)
                  trade.PositionModify(posInfo.Ticket(), price + trailingDistance, 0);
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
void ProcessSymbol(int index)
  {
   string sym = symbols[index].symbolName;
   datetime currentBarTime = iTime(sym, PERIOD_H4, 0);
   if(currentBarTime == 0 || currentBarTime == symbols[index].lastBarTime) return; 
   
   double ema12[], ema144[], ema169[], ema338[], ema576[], ema676[], adx[], atr[];
   ArraySetAsSeries(ema12, true); ArraySetAsSeries(ema144, true); ArraySetAsSeries(ema169, true);
   ArraySetAsSeries(ema338, true); ArraySetAsSeries(ema576, true); ArraySetAsSeries(ema676, true);
   ArraySetAsSeries(adx, true); ArraySetAsSeries(atr, true);

   CopyBuffer(symbols[index].h_ema12, 0, 0, 3, ema12);
   CopyBuffer(symbols[index].h_ema144, 0, 0, 3, ema144);
   CopyBuffer(symbols[index].h_ema169, 0, 0, 3, ema169);
   CopyBuffer(symbols[index].h_ema338, 0, 0, 3, ema338);
   CopyBuffer(symbols[index].h_ema576, 0, 0, 3, ema576);
   CopyBuffer(symbols[index].h_ema676, 0, 0, 3, ema676);
   CopyBuffer(symbols[index].h_adx, 0, 0, 3, adx); 
   CopyBuffer(symbols[index].h_atr, 0, 0, 2, atr); 

   double closePrice1 = iClose(sym, PERIOD_H4, 1);
   bool hasBuyPosition = false; bool hasSellPosition = false;
   ulong posTicket = 0; double openPrice = 0.0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == sym && posInfo.Magic() == InpMagicNumber)
        {
         posTicket = posInfo.Ticket(); openPrice = posInfo.PriceOpen();
         if(posInfo.PositionType() == POSITION_TYPE_BUY) hasBuyPosition = true;
         if(posInfo.PositionType() == POSITION_TYPE_SELL) hasSellPosition = true;
         break; 
        }
     }

   // --- 平仓逻辑 ---
   if(hasBuyPosition && closePrice1 < ema338[1])
      trade.PositionClose(posTicket);
   if(hasSellPosition && closePrice1 > ema338[1])
      trade.PositionClose(posTicket);

   // --- 开仓逻辑 ---
   if(!hasBuyPosition && !hasSellPosition)
     {
      // [V6.0] 提取专属字典里的 ADX 阈值
      bool isTrending = (adx[1] > symbols[index].optimized_adx); 

      // 多头
      bool bullCross = (ema12[1] > ema144[1] && ema12[1] > ema169[1]) && (ema12[2] <= ema144[2] || ema12[2] <= ema169[2]);
      if(bullCross && isTrending && (ema576[1] > ema676[1]))
        {
         double stopLoss = closePrice1 - (atr[1] * InpTrailingATR_Multiplier); // 动态ATR止损
         double lotSize = CalculateLotSize(sym, stopLoss, POSITION_TYPE_BUY);
         if(lotSize > 0) trade.Buy(lotSize, sym, 0, stopLoss, 0, "Vegas Bull");
        }

      // 空头
      bool bearCross = (ema12[1] < ema144[1] && ema12[1] < ema169[1]) && (ema12[2] >= ema144[2] || ema12[2] >= ema169[2]);
      if(bearCross && isTrending && (ema576[1] < ema676[1]))
        {
         double stopLoss = closePrice1 + (atr[1] * InpTrailingATR_Multiplier);
         double lotSize = CalculateLotSize(sym, stopLoss, POSITION_TYPE_SELL);
         if(lotSize > 0) trade.Sell(lotSize, sym, 0, stopLoss, 0, "Vegas Bear");
        }
     }

   symbols[index].lastBarTime = currentBarTime;
  }

//+------------------------------------------------------------------+
double CalculateLotSize(string sym, double slPrice, ENUM_POSITION_TYPE type)
  {
   double currentPrice = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_ASK) : SymbolInfoDouble(sym, SYMBOL_BID);
   double riskAmount = AccountInfoDouble(ACCOUNT_BALANCE) * (InpRiskPercent / 100.0);
   double tickSize = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize == 0 || tickValue == 0) return 0; 
   double slDistanceTicks = MathAbs(currentPrice - slPrice) / tickSize;
   if(slDistanceTicks <= 0) slDistanceTicks = 1; 
   double calcLot = riskAmount / (slDistanceTicks * tickValue);
   
   double minLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   double lot = MathFloor(calcLot / stepLot) * stepLot;
   if(lot < minLot) lot = minLot;
   return lot;
  }