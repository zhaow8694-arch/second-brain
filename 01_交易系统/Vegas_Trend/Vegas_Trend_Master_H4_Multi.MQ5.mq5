//+------------------------------------------------------------------+
//|                             Vegas_Trend_Master_H4_Multi.mq5      |
//|                                             Created by 编码助手 |
//+------------------------------------------------------------------+
#property copyright "编码助手"
#property version   "3.00" // 升级为3.0版本：专业保本止损与订单记忆

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade         trade;
CPositionInfo  posInfo;

//--- 输入参数 ---
input string   InpSymbols = "XAUUSD,XAGUSD,SP500,CHINA50"; // 测试品种(用英文逗号分隔)
input double   InpRiskPercent = 0.5;         // 单笔交易风险比例 (%)
input int      InpMagicNumber = 888888;      // EA魔术码
input double   InpPartialCloseRatio = 0.68;  // 第一平仓比例 (68%)
input bool     InpUseBreakEven = true;       // 【新增】是否启用保本止损(平仓68%后，剩余仓位不亏损)

//--- ADX 震荡过滤器参数 ---
input int      InpAdxPeriod = 14;            // ADX 计算周期
input double   InpAdxThreshold = 25.0;       // ADX 趋势阈值 (大于此值才认为有行情)

//--- 均线参数 ---
input int      InpEma12  = 12;   
input int      InpEma144 = 144;  
input int      InpEma169 = 169;  
input int      InpEma288 = 288;  
input int      InpEma338 = 338;  
input int      InpEma576 = 576;  
input int      InpEma676 = 676;  

//--- 为多品种定义结构体 ---
struct SymbolData
  {
   string   symbolName;
   int      h_ema12, h_ema144, h_ema169, h_ema288, h_ema338, h_ema576, h_ema676;
   int      h_adx; 
   datetime lastBarTime;
  };

SymbolData symbols[];

//+------------------------------------------------------------------+
//| EA初始化函数                                                      |
//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);

   ushort separator = StringGetCharacter(",", 0);
   string result[];
   int count = StringSplit(InpSymbols, separator, result);
   
   if(count == 0) return(INIT_FAILED);

   ArrayResize(symbols, count);

   for(int i = 0; i < count; i++)
     {
      StringTrimLeft(result[i]);
      StringTrimRight(result[i]);
      symbols[i].symbolName = result[i];
      SymbolSelect(symbols[i].symbolName, true); 

      symbols[i].h_ema12  = iMA(symbols[i].symbolName, PERIOD_H4, InpEma12, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema144 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma144, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema169 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma169, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema288 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma288, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema338 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma338, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema576 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma576, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema676 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma676, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_adx    = iADX(symbols[i].symbolName, PERIOD_H4, InpAdxPeriod);
      
      symbols[i].lastBarTime = 0;
     }

   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| 每次价格变动时触发的函数                                           |
//+------------------------------------------------------------------+
void OnTick()
  {
   for(int i = 0; i < ArraySize(symbols); i++)
     {
      ProcessSymbol(i);
     }
  }

//+------------------------------------------------------------------+
//| 核心逻辑：处理单个品种的交易                                       |
//+------------------------------------------------------------------+
void ProcessSymbol(int index)
  {
   string sym = symbols[index].symbolName;
   datetime currentBarTime = iTime(sym, PERIOD_H4, 0);
   if(currentBarTime == 0 || currentBarTime == symbols[index].lastBarTime) return; 
   
   double ema12[], ema144[], ema169[], ema288[], ema338[], ema576[], ema676[], adx[];
   ArraySetAsSeries(ema12, true); ArraySetAsSeries(ema144, true); ArraySetAsSeries(ema169, true);
   ArraySetAsSeries(ema288, true); ArraySetAsSeries(ema338, true); ArraySetAsSeries(ema576, true); ArraySetAsSeries(ema676, true);
   ArraySetAsSeries(adx, true); 

   CopyBuffer(symbols[index].h_ema12, 0, 0, 3, ema12);
   CopyBuffer(symbols[index].h_ema144, 0, 0, 3, ema144);
   CopyBuffer(symbols[index].h_ema169, 0, 0, 3, ema169);
   CopyBuffer(symbols[index].h_ema288, 0, 0, 3, ema288);
   CopyBuffer(symbols[index].h_ema338, 0, 0, 3, ema338);
   CopyBuffer(symbols[index].h_ema576, 0, 0, 3, ema576);
   CopyBuffer(symbols[index].h_ema676, 0, 0, 3, ema676);
   CopyBuffer(symbols[index].h_adx, 0, 0, 3, adx); 

   double closePrice1 = iClose(sym, PERIOD_H4, 1);

   // 2. 检查持仓状态 (【升级】获取精确的订单Ticket和开仓价)
   bool hasBuyPosition = false;
   bool hasSellPosition = false;
   ulong posTicket = 0;
   double currentVolume = 0.0;
   double openPrice = 0.0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i))
        {
         if(posInfo.Symbol() == sym && posInfo.Magic() == InpMagicNumber)
           {
            posTicket = posInfo.Ticket();
            currentVolume = posInfo.Volume();
            openPrice = posInfo.PriceOpen();
            if(posInfo.PositionType() == POSITION_TYPE_BUY) hasBuyPosition = true;
            if(posInfo.PositionType() == POSITION_TYPE_SELL) hasSellPosition = true;
            break; // 假设同一魔术码该品种只有一笔订单
           }
        }
     }

   // 3. 【全新升级】出场与保本平仓逻辑
   if(hasBuyPosition)
     {
      bool isPartiallyClosed = HasPartiallyClosed(posTicket);

      // 第一优先级：跌破生命线(EMA338)，全部平仓
      if(closePrice1 < ema338[1])
        {
         trade.PositionClose(posTicket);
         Print(sym, " 多头全部清仓 (跌破EMA338)");
        }
      // 第二优先级：【新增】保本止损。如果已经落袋过68%，且价格跌回开仓价下方，剩余部分保本出局
      else if(InpUseBreakEven && isPartiallyClosed && closePrice1 < openPrice)
        {
         trade.PositionClose(posTicket);
         Print(sym, " 🛡️ 多头触发保本止损，剩余仓位平仓出局");
        }
      // 第三优先级：跌破减仓线(EMA288)，且之前没减过仓，则执行 68% 部分平仓
      else if(!isPartiallyClosed && closePrice1 < ema288[1])
        {
         double closeVol = NormalizeVolume(sym, currentVolume * InpPartialCloseRatio);
         trade.PositionClosePartial(posTicket, closeVol);
         Print(sym, " 多头获利减仓 68% (跌破EMA288)");
        }
     }
     
   if(hasSellPosition)
     {
      bool isPartiallyClosed = HasPartiallyClosed(posTicket);

      if(closePrice1 > ema338[1])
        {
         trade.PositionClose(posTicket);
         Print(sym, " 空头全部清仓 (突破EMA338)");
        }
      else if(InpUseBreakEven && isPartiallyClosed && closePrice1 > openPrice)
        {
         trade.PositionClose(posTicket);
         Print(sym, " 🛡️ 空头触发保本止损，剩余仓位平仓出局");
        }
      else if(!isPartiallyClosed && closePrice1 > ema288[1])
        {
         double closeVol = NormalizeVolume(sym, currentVolume * InpPartialCloseRatio);
         trade.PositionClosePartial(posTicket, closeVol);
         Print(sym, " 空头获利减仓 68% (突破EMA288)");
        }
     }

   // 4. 开仓逻辑
   if(!hasBuyPosition && !hasSellPosition)
     {
      bool isTrending = (adx[1] > InpAdxThreshold);

      // 多头
      bool bullAlignment = (ema144[1] > ema169[1]) && (ema576[1] > ema676[1]);
      bool bullSlope = (ema169[0] > ema169[1]) && (ema676[0] > ema676[1]);
      bool bullCross = (ema12[1] > ema144[1] && ema12[1] > ema169[1]) && 
                       (ema12[2] <= ema144[2] || ema12[2] <= ema169[2]);

      if(bullAlignment && bullSlope && bullCross && isTrending)
        {
         double lotSize = CalculateLotSize(sym, ema338[1], POSITION_TYPE_BUY);
         if(lotSize > 0) trade.Buy(lotSize, sym, 0, 0, 0, "Vegas Bull");
        }

      // 空头
      bool bearAlignment = (ema144[1] < ema169[1]) && (ema576[1] < ema676[1]);
      bool bearSlope = (ema169[0] < ema169[1]) && (ema676[0] < ema676[1]);
      bool bearCross = (ema12[1] < ema144[1] && ema12[1] < ema169[1]) && 
                       (ema12[2] >= ema144[2] || ema12[2] >= ema169[2]);

      if(bearAlignment && bearSlope && bearCross && isTrending)
        {
         double lotSize = CalculateLotSize(sym, ema338[1], POSITION_TYPE_SELL);
         if(lotSize > 0) trade.Sell(lotSize, sym, 0, 0, 0, "Vegas Bear");
        }
     }

   symbols[index].lastBarTime = currentBarTime;
  }

//+------------------------------------------------------------------+
//| 【全新增加】查询历史记录，精准判断该笔订单是否已经发生过部分平仓       |
//+------------------------------------------------------------------+
bool HasPartiallyClosed(ulong position_ticket)
  {
   // 定位到该持仓单据的全部相关历史交易(Deals)
   if(HistorySelectByPosition(position_ticket))
     {
      int deals = HistoryDealsTotal();
      int out_deals = 0;
      
      // 遍历该仓位的所有动作
      for(int i = 0; i < deals; i++)
        {
         ulong deal_ticket = HistoryDealGetTicket(i);
         // 如果发现了方向为 OUT (离场/平仓) 的记录
         if(HistoryDealGetInteger(deal_ticket, DEAL_ENTRY) == DEAL_ENTRY_OUT)
           {
            out_deals++;
           }
        }
      // 如果有过至少一次平仓动作(且当前依然持仓)，必定是经历了部分平仓
      if(out_deals > 0) return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| 资金管理计算                                                      |
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

   double moneyLostPerLot = slDistanceTicks * tickValue;
   double calcLot = riskAmount / moneyLostPerLot;
   
   return NormalizeVolume(sym, calcLot);
  }

//+------------------------------------------------------------------+
//| 手数规范化                                                        |
//+------------------------------------------------------------------+
double NormalizeVolume(string sym, double vol)
  {
   double minLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   
   double lot = MathFloor(vol / stepLot) * stepLot;
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;
   return lot;
  }
//+------------------------------------------------------------------+