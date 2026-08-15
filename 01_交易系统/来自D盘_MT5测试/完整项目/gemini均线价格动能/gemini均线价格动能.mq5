//+------------------------------------------------------------------+
//|                                     Gold_Momentum_Strategy.mq5   |
//|                                  Copyright 2026, 编码助手         |
//+------------------------------------------------------------------+
#property strict

// --- 输入参数 ---
input int      InpMA1Period   = 1200;    // MA1 周期 (趋势线)
input int      InpMA2Period   = 100;     // MA2 周期 (平滑线)
input int      InpMomPeriod   = 100;     // 动量平均周期
input double   InpS1          = 0.001;   // 动量平滑因子
input double   InpST          = 0.005;   // 止盈比例 (0.5%)
input double   InpSL          = 0.003;   // 强制止损比例 (0.3%)
input double   InpRiskPercent = 2.0;     // 资金单次风险比例 (默认2%)

// --- 全局变量 ---
int      handleMA1, handleMA2;
double   bufferMA1[], bufferMA2[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   handleMA1 = iMA(_Symbol, _Period, InpMA1Period, 0, MODE_SMA, PRICE_CLOSE);
   handleMA2 = iMA(_Symbol, _Period, InpMA2Period, 0, MODE_SMA, PRICE_CLOSE); 
   
   if(handleMA1 == INVALID_HANDLE || handleMA2 == INVALID_HANDLE) return(INIT_FAILED);
   
   ArraySetAsSeries(bufferMA1, true);
   ArraySetAsSeries(bufferMA2, true);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if(Bars(_Symbol, _Period) < InpMA1Period + InpMA2Period) return;

   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, _Period, 0, 3, rates) < 3) return;

   if(CopyBuffer(handleMA1, 0, 0, 3, bufferMA1) < 3) return;
   if(CopyBuffer(handleMA2, 0, 0, 3, bufferMA2) < 3) return;

   double price = rates[0].close;
   double ma1 = bufferMA1[0];
   double ma2 = bufferMA2[0];

   // --- 动量核心逻辑计算 ---
   double h_diff = rates[0].high - rates[1].high;
   double l_diff = rates[0].low - rates[1].low;
   bool cond_up = (rates[0].high + rates[0].low) > (rates[1].high + rates[1].low);

   double dbf = cond_up ? MathMax(h_diff, l_diff) : 0;
   double kbf = !cond_up ? MathMax(h_diff, l_diff) : 0;
   if(dbf < 0) dbf = 0; if(kbf < 0) kbf = 0;

   double denom = dbf + kbf + 2 * InpS1;
   double dbl = (dbf + InpS1) / denom;
   double kbl = (kbf + InpS1) / denom;
   double change = dbl - kbl;

   bool hasPosition = PositionSelect(_Symbol);
   
   // --- 开仓逻辑 ---
   if(!hasPosition)
   {
      if(price > ma1 && ma1 > ma2 && change > 0)
      {
         TradeOrder(ORDER_TYPE_BUY, price);
      }
      else if(price < ma1 && ma1 < ma2 && change < 0)
      {
         TradeOrder(ORDER_TYPE_SELL, price);
      }
   }
   else // --- 平仓/止盈逻辑 ---
   {
      long type = PositionGetInteger(POSITION_TYPE);
      double entryPrice = PositionGetDouble(POSITION_PRICE_OPEN);

      if(type == POSITION_TYPE_BUY)
      {
         if(price < entryPrice * (1 - InpSL) || (price < ma1 && price > entryPrice * (1 + InpST)))
            TradeClose();
      }
      else if(type == POSITION_TYPE_SELL)
      {
         if(price > entryPrice * (1 + InpSL) || (price > ma1 && price < entryPrice * (1 - InpST)))
            TradeClose();
      }
   }
}

//+------------------------------------------------------------------+
//| 动态计算下单手数函数                                               |
//+------------------------------------------------------------------+
double CalculateDynamicLotSize(double current_price)
{
   // 1. 获取当前账户余额
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   // 2. 计算本次交易允许的最大亏损金额
   double risk_amount = balance * (InpRiskPercent / 100.0);
   
   // 3. 根据止损比例计算真实的止损价格距离
   double sl_distance = current_price * InpSL; 
   
   // 4. 获取品种跳动属性
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   
   // 5. 计算下一手，如果触及止损会亏损多少钱
   if(tick_size == 0 || tick_value == 0) return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double loss_per_lot = (sl_distance / tick_size) * tick_value;
   if(loss_per_lot <= 0) return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   
   // 6. 得出理论手数
   double target_lot = risk_amount / loss_per_lot;
   
   // --- 手数合规与平台限制检查 ---
   double min_vol = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_vol = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double vol_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   // 防止手数过大或过小
   if(target_lot < min_vol) target_lot = min_vol;
   if(target_lot > max_vol) target_lot = max_vol;
   
   // 修正为平台支持的步长 (例如将 0.156 修正为 0.15)
   target_lot = MathFloor(target_lot / vol_step) * vol_step;
   
   return target_lot;
}

// --- 交易辅助函数 ---
void TradeOrder(ENUM_ORDER_TYPE type, double price)
{
   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   // 调用新函数，根据资金量动态获取手数
   double dynamic_lot = CalculateDynamicLotSize(price);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = dynamic_lot; 
   request.type   = type;
   request.price  = (type == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   request.magic  = 123456;
   request.deviation = 10;
   
   if(!OrderSend(request, result))
   {
      Print("开仓错误，错误代码: ", GetLastError(), " | 尝试下单手数: ", dynamic_lot);
   }
}

void TradeClose()
{
   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = PositionGetDouble(POSITION_VOLUME);
   request.magic  = 123456;
   request.deviation = 10;
   
   if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
   {
      request.type  = ORDER_TYPE_SELL;
      request.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   }
   else
   {
      request.type  = ORDER_TYPE_BUY;
      request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   }
   
   if(!OrderSend(request, result))
   {
      Print("平仓错误，错误代码: ", GetLastError());
   }
}