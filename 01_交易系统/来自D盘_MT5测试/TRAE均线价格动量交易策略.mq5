//+------------------------------------------------------------------+
//|                          均线价格动量交易策略                          |
//|                    基于均线系统和价格波动动量的趋势跟随策略                    |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, 量化交易策略"
#property link      ""
#property version   "1.00"
#property description "均线价格动量交易策略 - 国际期货版"
#property strict

// 策略参数
input int      MA1_Period = 1200;          // MA1周期
input int      MA2_Period = 100;           // MA2周期
input double   StopProfit = 0.001;         // 止盈比例
input double   RiskPercent = 1.0;          // 单笔风险百分比
input double   MaxDrawdown = 5.0;          // 最大回撤百分比
input bool     UseTrailingStop = false;    // 使用移动止损
input int      MagicNumber = 123456;       // 魔术数字
input string   SymbolName = "XAUUSD";      // 交易品种

// 全局变量
double MA1[], MA2[];
double change[], machange[], machange2[];
double DBF, KBF, DBL, KBL;
int bars_available = 0;
double initial_deposit = 0;
double max_equity = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // 检查K线数量
    bars_available = Bars(SymbolName, PERIOD_CURRENT);
    if(bars_available < MA1_Period + MA2_Period + 100)
    {
        Print("K线数量不足，至少需要 ", MA1_Period + MA2_Period + 100, " 根K线");
        return INIT_FAILED;
    }
    
    // 初始化账户信息
    initial_deposit = AccountBalance();
    max_equity = initial_deposit;
    
    Print("均线价格动量交易策略初始化完成");
    Print("MA1周期: ", MA1_Period, "，MA2周期: ", MA2_Period);
    Print("止盈比例: ", StopProfit * 100, "%");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("策略已停止，原因: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // 检查账户状态
    if(IsTradeAllowed() == false)
    {
        Print("交易未允许");
        return;
    }
    
    // 检查最大回撤
    double current_equity = AccountEquity();
    double drawdown = (max_equity - current_equity) / max_equity * 100;
    
    if(drawdown > MaxDrawdown)
    {
        Print("最大回撤已达 ", drawdown, "%，超过限制 ", MaxDrawdown, "%，策略暂停");
        CloseAllPositions();
        return;
    }
    
    if(current_equity > max_equity)
    {
        max_equity = current_equity;
    }
    
    // 计算指标
    CalculateIndicators();
    
    // 检查K线数量是否足够
    if(Bars(SymbolName, PERIOD_CURRENT) < MA1_Period + 1)
    {
        return;
    }
    
    // 获取当前价格
    double Ask = NormalizeDouble(SymbolInfoDouble(SymbolName, SYMBOL_ASK), _Digits);
    double Bid = NormalizeDouble(SymbolInfoDouble(SymbolName, SYMBOL_BID), _Digits);
    
    // 获取持仓信息
    int buy_tickets[] = GetPositionsByType(ORDER_TYPE_BUY);
    int sell_tickets[] = GetPositionsByType(ORDER_TYPE_SELL);
    
    // 交易逻辑
    if(buy_tickets[0] == -1 && sell_tickets[0] == -1) // 无持仓
    {
        // 多头开仓条件
        if(Bid > MA1[1] && MA1[1] > MA2[1] && change[1] > 0 && machange[1] > machange2[1])
        {
            double lot_size = CalculateLotSize(RiskPercent);
            if(lot_size > 0)
            {
                Print("触发多头开仓条件");
                bool result = OrderSend(SymbolName, ORDER_TYPE_BUY, lot_size, Ask, 3, 0, 0, "多头开仓", MagicNumber, 0, clrGreen);
                if(result)
                {
                    Print("多头开仓成功，手数: ", lot_size);
                }
                else
                {
                    Print("多头开仓失败，错误: ", GetLastError());
                }
            }
        }
        // 空头开仓条件
        else if(Ask < MA1[1] && MA1[1] < MA2[1] && change[1] < 0 && machange[1] < machange2[1])
        {
            double lot_size = CalculateLotSize(RiskPercent);
            if(lot_size > 0)
            {
                Print("触发空头开仓条件");
                bool result = OrderSend(SymbolName, ORDER_TYPE_SELL, lot_size, Bid, 3, 0, 0, "空头开仓", MagicNumber, 0, clrRed);
                if(result)
                {
                    Print("空头开仓成功，手数: ", lot_size);
                }
                else
                {
                    Print("空头开仓失败，错误: ", GetLastError());
                }
            }
        }
    }
    else if(buy_tickets[0] != -1) // 持有多头
    {
        // 获取持仓信息
        double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
        long ticket = buy_tickets[0];
        
        // 多头平仓条件
        if(Bid < MA1[1] && Bid > open_price * (1 + StopProfit))
        {
            Print("触发多头平仓条件");
            bool result = OrderSend(SymbolName, ORDER_TYPE_SELL, PositionGetDouble(POSITION_VOLUME), Bid, 3, 0, 0, "多头平仓", MagicNumber, 0, clrRed);
            if(result)
            {
                Print("多头平仓成功");
            }
            else
            {
                Print("多头平仓失败，错误: ", GetLastError());
            }
        }
        
        // 移动止损
        if(UseTrailingStop)
        {
            SetTrailingStop(ticket, OrderType(ticket));
        }
    }
    else if(sell_tickets[0] != -1) // 持有空头
    {
        // 获取持仓信息
        double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
        long ticket = sell_tickets[0];
        
        // 空头平仓条件
        if(Ask > MA1[1] && Ask < open_price * (1 - StopProfit))
        {
            Print("触发空头平仓条件");
            bool result = OrderSend(SymbolName, ORDER_TYPE_BUY, PositionGetDouble(POSITION_VOLUME), Ask, 3, 0, 0, "空头平仓", MagicNumber, 0, clrGreen);
            if(result)
            {
                Print("空头平仓成功");
            }
            else
            {
                Print("空头平仓失败，错误: ", GetLastError());
            }
        }
        
        // 移动止损
        if(UseTrailingStop)
        {
            SetTrailingStop(ticket, OrderType(ticket));
        }
    }
}

//+------------------------------------------------------------------+
//| 计算技术指标                                                      |
//+------------------------------------------------------------------+
void CalculateIndicators()
{
    // 计算MA1
    ArraySetAsSeries(MA1, true);
    int ma1_count = iMA(SymbolName, PERIOD_CURRENT, MA1_Period, 0, MODE_SMA, PRICE_CLOSE, 0, MA1_Period + 100, MA1);
    
    // 计算MA2 (MA1的MA)
    ArraySetAsSeries(MA2, true);
    for(int i = 0; i < MathMin(ma1_count, MA2_Period + 100); i++)
    {
        double sum = 0;
        for(int j = 0; j < MA2_Period; j++)
        {
            if(i + j < ma1_count)
            {
                sum += MA1[i + j];
            }
        }
        MA2[i] = sum / MA2_Period;
    }
    
    // 计算动量指标
    double S1 = 0.1; // 平滑因子
    ArraySetAsSeries(change, true);
    
    for(int i = 0; i < Bars(SymbolName, PERIOD_CURRENT) - 1; i++)
    {
        double high_current = High[i];
        double low_current = Low[i];
        double high_prev = High[i + 1];
        double low_prev = Low[i + 1];
        
        double current_sum = high_current + low_current;
        double prev_sum = high_prev + low_prev;
        
        // 计算DBF
        if(current_sum > prev_sum)
        {
            DBF = MathMax(high_current - high_prev, low_current - low_prev);
        }
        else
        {
            DBF = 0;
        }
        
        // 计算KBF
        if(current_sum < prev_sum)
        {
            KBF = MathMax(high_prev - high_current, low_prev - low_current);
        }
        else
        {
            KBF = 0;
        }
        
        // 计算动量比率
        DBL = (DBF + S1) / (DBF + KBF + 2 * S1);
        KBL = (KBF + S1) / (DBF + KBF + 2 * S1);
        
        change[i] = DBL - KBL;
    }
    
    // 计算machange (change的100周期平均值)
    ArraySetAsSeries(machange, true);
    for(int i = 0; i < Bars(SymbolName, PERIOD_CURRENT) - 100; i++)
    {
        double sum = 0;
        for(int j = 0; j < 100; j++)
        {
            sum += change[i + j];
        }
        machange[i] = sum / 100;
    }
    
    // 计算machange2 (machange的二次指数平滑)
    ArraySetAsSeries(machange2, true);
    double alpha = 0.1; // 平滑系数
    machange2[0] = machange[0];
    for(int i = 1; i < ArraySize(machange); i++)
    {
        machange2[i] = alpha * machange[i] + (1 - alpha) * machange2[i - 1];
    }
}

//+------------------------------------------------------------------+
//| 获取指定类型的持仓列表                                             |
//+------------------------------------------------------------------+
int GetPositionsByType(int type)
{
    int positions[];
    int total = 0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionGetSymbol(i) == SymbolName && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
        {
            if(PositionGetInteger(POSITION_TYPE) == type)
            {
                positions[total++] = PositionGetInteger(POSITION_TICKET);
            }
        }
    }
    
    if(total == 0)
    {
        positions[0] = -1;
    }
    
    return positions;
}

//+------------------------------------------------------------------+
//| 计算开仓手数                                                      |
//+------------------------------------------------------------------+
double CalculateLotSize(double risk_percent)
{
    double account_balance = AccountBalance();
    double risk_amount = account_balance * risk_percent / 100;
    
    double tick_size = SymbolInfoDouble(SymbolName, SYMBOL_TRADE_TICK_SIZE);
    double tick_value = SymbolInfoDouble(SymbolName, SYMBOL_TRADE_TICK_VALUE);
    double stop_loss_points = MA1_Period * 0.1; // 简化的止损点数计算
    
    double lot_size = risk_amount / (stop_loss_points * tick_value);
    lot_size = NormalizeDouble(lot_size, SymbolInfoInteger(SymbolName, SYMBOL_VOLUME_DIGITS));
    
    // 检查最小手数
    double min_lot = SymbolInfoDouble(SymbolName, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(SymbolName, SYMBOL_VOLUME_MAX);
    
    lot_size = MathMax(lot_size, min_lot);
    lot_size = MathMin(lot_size, max_lot);
    
    return lot_size;
}

//+------------------------------------------------------------------+
//| 设置移动止损                                                      |
//+------------------------------------------------------------------+
void SetTrailingStop(long ticket, int order_type)
{
    double price = PositionGetDouble(POSITION_PRICE_OPEN);
    double current_price = order_type == ORDER_TYPE_BUY ? SymbolInfoDouble(SymbolName, SYMBOL_BID) : SymbolInfoDouble(SymbolName, SYMBOL_ASK);
    double profit = order_type == ORDER_TYPE_BUY ? (current_price - price) : (price - current_price);
    
    // 如果盈利超过20点，设置移动止损为10点
    double trail_points = 10;
    double trail_stop = order_type == ORDER_TYPE_BUY ? current_price - trail_points * SymbolInfoDouble(SymbolName, SYMBOL_TRADE_TICK_SIZE) : current_price + trail_points * SymbolInfoDouble(SymbolName, SYMBOL_TRADE_TICK_SIZE);
    
    if(profit > 20 * SymbolInfoDouble(SymbolName, SYMBOL_TRADE_TICK_SIZE))
    {
        PositionModify(ticket, trail_stop, 0);
    }
}

//+------------------------------------------------------------------+
//| 关闭所有持仓                                                      |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(PositionSelectByTicket(PositionGetInteger(POSITION_TICKET)))
        {
            if(PositionGetSymbol(0) == SymbolName && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            {
                int type = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
                double price = type == ORDER_TYPE_SELL ? SymbolInfoDouble(SymbolName, SYMBOL_BID) : SymbolInfoDouble(SymbolName, SYMBOL_ASK);
                
                bool result = OrderSend(SymbolName, type, PositionGetDouble(POSITION_VOLUME), price, 3, 0, 0, "紧急平仓", MagicNumber, 0, clrYellow);
                if(result)
                {
                    Print("已关闭持仓: ", PositionGetInteger(POSITION_TICKET));
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| 获取订单类型                                                      |
//+------------------------------------------------------------------+
int OrderType(long ticket)
{
    if(PositionSelectByTicket(ticket))
    {
        return PositionGetInteger(POSITION_TYPE);
    }
    return -1;
}