#property copyright "GEMINI Starfleet EA"
#property link      ""
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>

input double   InpLots           = 0.1;
input int      InpStopLoss       = 500;
input int      InpTakeProfit     = 1500;
input int      InpSlippage       = 30;
input double   InpMaxSpread      = 150.0;
input int      InpMagicNumber    = 20250415;

input int      InpTrailingStart  = 400;
input int      InpTrailingStep   = 200;

input bool     InpUseAutoLot     = true;
input double   InpRiskPercent    = 2.0;

input int      InpTradeStartHour = 1;
input int      InpTradeEndHour  = 22;
input bool     InpCloseOnFriday  = true;
input int      InpFridayCloseHour = 21;

input int      InpEmaFast        = 40;
input int      InpEmaSlow        = 100;
input int      InpMacdFast       = 12;
input int      InpMacdSlow       = 26;
input int      InpMacdSignal     = 9;
input bool     InpUseRsiFilter   = true;
input int      InpRsiPeriod      = 14;
input int      InpRsiOverbought  = 70;
input int      InpRsiOversold    = 30;

input bool     InpEnablePyramid  = true;
input int      InpPyramidDistance = 800;
input int      InpMaxPositions   = 3;

CTrade         g_trade;
string         g_symbol         = _Symbol;
int            g_slippage       = 0;
double         g_point          = 0.0;
int            g_digits         = 0;
double         g_maxSpreadPt    = 0.0;

int            g_handleEmaFast  = INVALID_HANDLE;
int            g_handleEmaSlow  = INVALID_HANDLE;
int            g_handleMacd     = INVALID_HANDLE;
int            g_handleRsi      = INVALID_HANDLE;

bool           g_fridayClosed   = false;

datetime       g_fridayCloseTime = 0;

double CalculateLotSize(int slPoints)
{
    if(!InpUseAutoLot)
        return InpLots;
    
    if(slPoints <= 0)
    {
        Print("[GEMINI] 开启 AutoLot 时止损不能为 0！");
        return 0;
    }
    
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(equity <= 0)
    {
        Print("[GEMINI] 账户净值异常，使用固定手数");
        return InpLots;
    }
    
    double riskAmount = equity * (InpRiskPercent / 100.0);
    
    double askPrice = SymbolInfoDouble(g_symbol, SYMBOL_ASK);
    if(askPrice == 0)
    {
        Print("[GEMINI] 无法获取Ask价格，使用固定手数");
        return InpLots;
    }
    
    double slPrice = askPrice - (slPoints * g_point);
    slPrice = NormalizeDouble(slPrice, g_digits);
    
    double lossForOneLot = 0;
    if(!OrderCalcProfit(ORDER_TYPE_BUY, g_symbol, 1.0, askPrice, slPrice, lossForOneLot))
    {
        PrintFormat("[GEMINI] OrderCalcProfit 调用失败！错误码: %d，使用固定手数", GetLastError());
        return InpLots;
    }
    
    double riskPerLot = MathAbs(lossForOneLot);
    
    if(riskPerLot <= 0)
    {
        Print("[GEMINI] 风险计算异常，使用固定手数");
        return InpLots;
    }
    
    double finalLot = riskAmount / riskPerLot;
    
    double minLot = SymbolInfoDouble(g_symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(g_symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(g_symbol, SYMBOL_VOLUME_STEP);
    
    PrintFormat(">>> [X光雷达] 亏损预算:$%.2f | 平台1手真实亏损:$%.2f | 理论手数:%.5f | 平台限额:[%.2f - %.2f]", riskAmount, riskPerLot, finalLot, minLot, maxLot);
    
    if(finalLot < minLot)
    {
        PrintFormat("[GEMINI] 计算手数 %.5f 小于最小手数 %.5f，使用最小值", finalLot, minLot);
        finalLot = minLot;
    }
    else if(finalLot > maxLot)
    {
        PrintFormat("[GEMINI] 计算手数 %.5f 大于最大手数 %.5f，使用最大值", finalLot, maxLot);
        finalLot = maxLot;
    }
    
    finalLot = MathFloor(finalLot / lotStep) * lotStep;
    
    return finalLot;
}

bool CheckTimeFilter(bool isEntry)
{
    if(!isEntry)
        return true;
    
    MqlDateTime dt;
    TimeCurrent(dt);
    
    int currentHour = dt.hour;
    
    if(currentHour < InpTradeStartHour || currentHour >= InpTradeEndHour)
    {
        PrintFormat("[GEMINI] 时间过滤：当前小时 %d 不在交易时段 %d-%d 之间", 
                    currentHour, InpTradeStartHour, InpTradeEndHour);
        return false;
    }
    
    return true;
}

void FridayCloseAll()
{
    if(!InpCloseOnFriday)
        return;
    
    MqlDateTime dt;
    TimeCurrent(dt);
    
    if(dt.day_of_week == 5)
    {
        if(dt.hour >= InpFridayCloseHour)
        {
            if(!g_fridayClosed || TimeCurrent() >= g_fridayCloseTime + 300)
            {
                int totalPositions = CountPositions(POSITION_TYPE_BUY) + CountPositions(POSITION_TYPE_SELL);
                
                if(totalPositions == 0)
                    return;
                
                g_fridayClosed = true;
                g_fridayCloseTime = TimeCurrent();
                
                for(int i = PositionsTotal() - 1; i >= 0; i--)
                {
                    ulong ticket = PositionGetTicket(i);
                    if(ticket == 0) continue;
                    
                    if(PositionGetString(POSITION_SYMBOL) != g_symbol) continue;
                    if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
                    
                    g_trade.SetExpertMagicNumber(InpMagicNumber);
                    g_trade.PositionClose(ticket, g_slippage);
                }
                
                Print("[GEMINI] 周末防爆协议启动：已清空所有仓位，落袋为安。");
            }
            
            return;
        }
    }
    else
    {
        g_fridayClosed = false;
    }
}

bool InitIndicators()
{
    g_handleEmaFast = iMA(g_symbol, PERIOD_CURRENT, InpEmaFast, 0, MODE_EMA, PRICE_CLOSE);
    if(g_handleEmaFast == INVALID_HANDLE)
    {
        PrintFormat("[GEMINI] 创建EMA快线(%d)失败！错误码: %d", InpEmaFast, GetLastError());
        return false;
    }
    
    g_handleEmaSlow = iMA(g_symbol, PERIOD_CURRENT, InpEmaSlow, 0, MODE_EMA, PRICE_CLOSE);
    if(g_handleEmaSlow == INVALID_HANDLE)
    {
        PrintFormat("[GEMINI] 创建EMA慢线(%d)失败！错误码: %d", InpEmaSlow, GetLastError());
        return false;
    }
    
    g_handleMacd = iMACD(g_symbol, PERIOD_CURRENT, InpMacdFast, InpMacdSlow, InpMacdSignal, PRICE_CLOSE);
    if(g_handleMacd == INVALID_HANDLE)
    {
        PrintFormat("[GEMINI] 创建MACD(%d,%d,%d)失败！错误码: %d", 
                    InpMacdFast, InpMacdSlow, InpMacdSignal, GetLastError());
        return false;
    }
    
    if(InpUseRsiFilter)
    {
        g_handleRsi = iRSI(g_symbol, PERIOD_CURRENT, InpRsiPeriod, PRICE_CLOSE);
        if(g_handleRsi == INVALID_HANDLE)
        {
            PrintFormat("[GEMINI] 创建RSI(%d)失败！错误码: %d", InpRsiPeriod, GetLastError());
            return false;
        }
    }
    
    Print("[GEMINI] 指标初始化完成。");
    return true;
}

void ReleaseIndicators()
{
    if(g_handleEmaFast != INVALID_HANDLE)
        IndicatorRelease(g_handleEmaFast);
    if(g_handleEmaSlow != INVALID_HANDLE)
        IndicatorRelease(g_handleEmaSlow);
    if(g_handleMacd != INVALID_HANDLE)
        IndicatorRelease(g_handleMacd);
    if(g_handleRsi != INVALID_HANDLE)
        IndicatorRelease(g_handleRsi);
}

int CountPositions(ENUM_POSITION_TYPE posType)
{
    int count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        
        if(PositionGetString(POSITION_SYMBOL) != g_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
        if(PositionGetInteger(POSITION_TYPE) != posType) continue;
        
        count++;
    }
    return count;
}

bool GetLastPositionInfo(ENUM_POSITION_TYPE posType, double &openPrice, datetime &openTime, double &openVolume)
{
    openPrice = 0;
    openTime = 0;
    openVolume = 0;
    bool found = false;
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        
        if(PositionGetString(POSITION_SYMBOL) != g_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
        if(PositionGetInteger(POSITION_TYPE) != posType) continue;
        
        datetime posTime = (datetime)PositionGetInteger(POSITION_TIME);
        if(posTime > openTime)
        {
            openTime = posTime;
            openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            openVolume = PositionGetDouble(POSITION_VOLUME);
            found = true;
        }
    }
    return found;
}

void TrailingPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        
        if(PositionGetString(POSITION_SYMBOL) != g_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
        
        ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
        double currentSL = PositionGetDouble(POSITION_SL);
        double currentTP = PositionGetDouble(POSITION_TP);
        double profitPoints = 0;
        double newSL = 0;
        double currentPrice = 0;
        bool shouldModify = false;
        
        if(posType == POSITION_TYPE_BUY)
        {
            currentPrice = SymbolInfoDouble(g_symbol, SYMBOL_BID);
            profitPoints = (currentPrice - openPrice) / g_point;
            
            if(profitPoints >= InpTrailingStart)
            {
                newSL = currentPrice - (InpTrailingStep * g_point);
                newSL = NormalizeDouble(newSL, g_digits);
                
                if(newSL > openPrice)
                {
                    if(currentSL == 0 || newSL > currentSL)
                    {
                        shouldModify = true;
                    }
                }
            }
        }
        else if(posType == POSITION_TYPE_SELL)
        {
            currentPrice = SymbolInfoDouble(g_symbol, SYMBOL_ASK);
            profitPoints = (openPrice - currentPrice) / g_point;
            
            if(profitPoints >= InpTrailingStart)
            {
                newSL = currentPrice + (InpTrailingStep * g_point);
                newSL = NormalizeDouble(newSL, g_digits);
                
                if(newSL < openPrice)
                {
                    if(currentSL == 0 || newSL < currentSL)
                    {
                        shouldModify = true;
                    }
                }
            }
        }
        
        if(shouldModify)
        {
            g_trade.SetExpertMagicNumber(InpMagicNumber);
            
            if(g_trade.PositionModify(ticket, newSL, currentTP))
            {
                PrintFormat("[GEMINI] 移动止损成功！Ticket: %d | 类型: %s | 新止损: %." + IntegerToString(g_digits) + "f | 盈利点数: %.0f",
                            ticket,
                            (posType == POSITION_TYPE_BUY ? "BUY" : "SELL"),
                            newSL,
                            profitPoints);
            }
            else
            {
                int errorCode = GetLastError();
                string errorDesc = ErrorDescription(errorCode);
                PrintFormat("[GEMINI] 移动止损失败！Ticket: %d | 错误码: %d | 描述: %s",
                            ticket, errorCode, errorDesc);
            }
        }
    }
}

bool CheckBuySignal()
{
    double emaFast[], emaSlow[], macdMain[];
    ArraySetAsSeries(emaFast, true);
    ArraySetAsSeries(emaSlow, true);
    ArraySetAsSeries(macdMain, true);
    
    if(CopyBuffer(g_handleEmaFast, 0, 0, 3, emaFast) < 3) return false;
    if(CopyBuffer(g_handleEmaSlow, 0, 0, 3, emaSlow) < 3) return false;
    if(CopyBuffer(g_handleMacd, 0, 0, 2, macdMain) < 2) return false;
    
    bool crossUp = (emaFast[2] <= emaSlow[2]) && (emaFast[1] > emaSlow[1]);
    bool macdConfirm = macdMain[1] > 0;
    
    if(!crossUp || !macdConfirm)
        return false;
    
    if(InpUseRsiFilter)
    {
        double rsi[];
        ArraySetAsSeries(rsi, true);
        if(CopyBuffer(g_handleRsi, 0, 0, 2, rsi) < 2) return false;
        
        if(rsi[1] >= InpRsiOverbought)
            return false;
    }
    
    return true;
}

bool CheckSellSignal()
{
    double emaFast[], emaSlow[], macdMain[];
    ArraySetAsSeries(emaFast, true);
    ArraySetAsSeries(emaSlow, true);
    ArraySetAsSeries(macdMain, true);
    
    if(CopyBuffer(g_handleEmaFast, 0, 0, 3, emaFast) < 3) return false;
    if(CopyBuffer(g_handleEmaSlow, 0, 0, 3, emaSlow) < 3) return false;
    if(CopyBuffer(g_handleMacd, 0, 0, 2, macdMain) < 2) return false;
    
    bool crossDown = (emaFast[2] >= emaSlow[2]) && (emaFast[1] < emaSlow[1]);
    bool macdConfirm = macdMain[1] < 0;
    
    if(!crossDown || !macdConfirm)
        return false;
    
    if(InpUseRsiFilter)
    {
        double rsi[];
        ArraySetAsSeries(rsi, true);
        if(CopyBuffer(g_handleRsi, 0, 0, 2, rsi) < 2) return false;
        
        if(rsi[1] <= InpRsiOversold)
            return false;
    }
    
    return true;
}

void CheckPyramiding()
{
    if(!InpEnablePyramid) return;
    
    int buyCount = CountPositions(POSITION_TYPE_BUY);
    int sellCount = CountPositions(POSITION_TYPE_SELL);
    
    if(buyCount > 0 && buyCount < InpMaxPositions)
    {
        double lastBuyPrice = 0;
        datetime lastBuyTime = 0;
        double lastBuyVolume = 0;
        
        if(GetLastPositionInfo(POSITION_TYPE_BUY, lastBuyPrice, lastBuyTime, lastBuyVolume))
        {
            double currentPrice = SymbolInfoDouble(g_symbol, SYMBOL_BID);
            double distance = (currentPrice - lastBuyPrice) / g_point;
            
            if(distance >= InpPyramidDistance)
            {
                PrintFormat("[GEMINI] 金字塔加仓信号-BUY | 当前价: %.5f | 上次开仓价: %.5f | 距离: %.0f 点 | 锁定手数: %.2f",
                            currentPrice, lastBuyPrice, distance, lastBuyVolume);
                OpenPosition(POSITION_TYPE_BUY, lastBuyVolume, InpStopLoss, InpTakeProfit, "PYRAMID_BUY");
            }
        }
    }
    
    if(sellCount > 0 && sellCount < InpMaxPositions)
    {
        double lastSellPrice = 0;
        datetime lastSellTime = 0;
        double lastSellVolume = 0;
        
        if(GetLastPositionInfo(POSITION_TYPE_SELL, lastSellPrice, lastSellTime, lastSellVolume))
        {
            double currentPrice = SymbolInfoDouble(g_symbol, SYMBOL_ASK);
            double distance = (lastSellPrice - currentPrice) / g_point;
            
            if(distance >= InpPyramidDistance)
            {
                PrintFormat("[GEMINI] 金字塔加仓信号-SELL | 当前价: %.5f | 上次开仓价: %.5f | 距离: %.0f 点 | 锁定手数: %.2f",
                            currentPrice, lastSellPrice, distance, lastSellVolume);
                OpenPosition(POSITION_TYPE_SELL, lastSellVolume, InpStopLoss, InpTakeProfit, "PYRAMID_SELL");
            }
        }
    }
}

void ExecuteEntrySignals()
{
    if(!CheckTimeFilter(true))
        return;
    
    int buyCount = CountPositions(POSITION_TYPE_BUY);
    int sellCount = CountPositions(POSITION_TYPE_SELL);
    
    double lotSize = CalculateLotSize(InpStopLoss);
    
    if(buyCount == 0 && CheckBuySignal())
    {
        Print("[GEMINI] 入场信号-BUY | EMA金叉 + MACD主线>0");
        OpenPosition(POSITION_TYPE_BUY, lotSize, InpStopLoss, InpTakeProfit, "ENTRY_BUY");
        return;
    }
    
    if(sellCount == 0 && CheckSellSignal())
    {
        Print("[GEMINI] 入场信号-SELL | EMA死叉 + MACD主线<0");
        OpenPosition(POSITION_TYPE_SELL, lotSize, InpStopLoss, InpTakeProfit, "ENTRY_SELL");
        return;
    }
}

bool OpenPosition(ENUM_POSITION_TYPE posType, double lots, int slPoints, int tpPoints, string comment = "")
{
    PrintFormat(">>> [开仓入口] 传入手数: %.5f | 类型: %s | 备注: %s", lots, (posType == POSITION_TYPE_BUY ? "BUY" : "SELL"), comment);
    
    if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
    {
        Print("[GEMINI] 交易终端禁止交易！");
        return false;
    }
    
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
    {
        Print("[GEMINI] EA禁止交易！");
        return false;
    }
    
    if(lots <= 0)
    {
        Print("[GEMINI] 手数为 0，取消本次开仓！");
        return false;
    }
    
    double currentSpread = SymbolInfoDouble(g_symbol, SYMBOL_ASK) - SymbolInfoDouble(g_symbol, SYMBOL_BID);
    double spreadPoints  = currentSpread / g_point;
    
    if(spreadPoints > g_maxSpreadPt)
    {
        PrintFormat("[GEMINI] 点差超限！当前: %.1f 点，最大允许: %.1f 点", 
                    spreadPoints, g_maxSpreadPt);
        return false;
    }
    
    double minLot = SymbolInfoDouble(g_symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(g_symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(g_symbol, SYMBOL_VOLUME_STEP);
    
    if(lots < minLot)
    {
        PrintFormat("[GEMINI] 手数 %.2f 小于最小手数 %.2f，已调整为最小值", lots, minLot);
        lots = minLot;
    }
    else if(lots > maxLot)
    {
        PrintFormat("[GEMINI] 手数 %.2f 大于最大手数 %.2f，已调整为最大值", lots, maxLot);
        lots = maxLot;
    }
    
    lots = MathFloor(lots / lotStep) * lotStep;
    
    ENUM_ORDER_TYPE orderTypeCheck = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    double requiredMargin = 0;
    
    if(!OrderCalcMargin(orderTypeCheck, g_symbol, lots, 
                        (posType == POSITION_TYPE_BUY) ? SymbolInfoDouble(g_symbol, SYMBOL_ASK) : SymbolInfoDouble(g_symbol, SYMBOL_BID), 
                        requiredMargin))
    {
        Print("[GEMINI] 无法计算所需保证金！");
        return false;
    }
    
    double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    
    if(freeMargin < requiredMargin)
    {
        PrintFormat("[GEMINI] 可用保证金不足，取消本次开仓！可用: %.2f | 需要: %.2f", freeMargin, requiredMargin);
        return false;
    }
    
    double tickSize = SymbolInfoDouble(g_symbol, SYMBOL_TRADE_TICK_SIZE);
    double tickValue = SymbolInfoDouble(g_symbol, SYMBOL_TRADE_TICK_VALUE);
    
    if(tickSize == 0 || tickValue == 0)
    {
        Print("[GEMINI] 无法获取tick信息！");
        return false;
    }
    
    double slValue = slPoints * g_point;
    double tpValue = tpPoints * g_point;
    
    double price = 0.0;
    double sl = 0.0;
    double tp = 0.0;
    ENUM_ORDER_TYPE orderType;
    
    if(posType == POSITION_TYPE_BUY)
    {
        price = SymbolInfoDouble(g_symbol, SYMBOL_ASK);
        if(price == 0)
        {
            Print("[GEMINI] 无法获取Ask价格！");
            return false;
        }
        sl = (slPoints > 0) ? price - slValue : 0;
        tp = (tpPoints > 0) ? price + tpValue : 0;
        orderType = ORDER_TYPE_BUY;
    }
    else if(posType == POSITION_TYPE_SELL)
    {
        price = SymbolInfoDouble(g_symbol, SYMBOL_BID);
        if(price == 0)
        {
            Print("[GEMINI] 无法获取Bid价格！");
            return false;
        }
        sl = (slPoints > 0) ? price + slValue : 0;
        tp = (tpPoints > 0) ? price - tpValue : 0;
        orderType = ORDER_TYPE_SELL;
    }
    else
    {
        Print("[GEMINI] 无效的持仓类型！");
        return false;
    }
    
    if(sl != 0)
        sl = NormalizeDouble(sl, g_digits);
    if(tp != 0)
        tp = NormalizeDouble(tp, g_digits);
    
    price = NormalizeDouble(price, g_digits);
    
    g_trade.SetExpertMagicNumber(InpMagicNumber);
    g_trade.SetDeviationInPoints(g_slippage);
    g_trade.SetTypeFilling(ORDER_FILLING_IOC);
    
    bool result = false;
    
    if(orderType == ORDER_TYPE_BUY)
    {
        result = g_trade.Buy(lots, g_symbol, price, sl, tp, comment);
    }
    else
    {
        result = g_trade.Sell(lots, g_symbol, price, sl, tp, comment);
    }
    
    if(result)
    {
        PrintFormat("[GEMINI] 开仓成功！类型: %s | 手数: %.2f | 价格: %." + IntegerToString(g_digits) + "f | SL: %." + IntegerToString(g_digits) + "f | TP: %." + IntegerToString(g_digits) + "f | 备注: %s",
                    (posType == POSITION_TYPE_BUY ? "BUY" : "SELL"),
                    lots, price, sl, tp, comment);
        return true;
    }
    else
    {
        int errorCode = GetLastError();
        string errorDesc = ErrorDescription(errorCode);
        PrintFormat("[GEMINI] 开仓失败！错误码: %d | 描述: %s | 类型: %s | 手数: %.2f | 价格: %." + IntegerToString(g_digits) + "f",
                    errorCode, errorDesc,
                    (posType == POSITION_TYPE_BUY ? "BUY" : "SELL"),
                    lots, price);
        return false;
    }
}

string ErrorDescription(int errorCode)
{
    switch(errorCode)
    {
        case 0:     return "无错误";
        case 10004: return "重新请求";
        case 10006: return "请求被拒绝";
        case 10007: return "请求被服务器取消";
        case 10010: return "只有部分成交";
        case 10011: return "交易错误";
        case 10012: return "请求超时";
        case 10013: return "无效请求";
        case 10014: return "无效交易量";
        case 10015: return "无效价格";
        case 10016: return "无效止损/止盈";
        case 10017: return "交易被禁用";
        case 10018: return "市场关闭";
        case 10019: return "资金不足";
        case 10020: return "价格已变化";
        case 10021: return "无报价";
        case 10022: return "无效过期时间";
        case 10023: return "订单状态改变";
        case 10024: return "请求过多";
        case 10025: return "无变化";
        case 10026: return "自动交易被禁用";
        case 10027: return "自动交易被客户端禁用";
        case 10028: return "请求被阻塞";
        case 10029: return "连接丢失";
        case 10030: return "仅允许持仓";
        case 10031: return "挂单数量超限";
        case 10032: return "持仓数量超限";
        case 10033: return "禁止卖空";
        case 10034: return "订单关闭失败";
        case 10035: return "仓位关闭失败";
        case 10036: return "订单重复";
        case 10038: return "多边交易系统错误";
        case 10039: return "订单关闭失败(已执行)";
        case 10040: return "订单仅允许撤销";
        case 4756:  return "交易请求失败";
        default:    return "未知错误";
    }
}

bool ValidateSymbol()
{
    if(!SymbolSelect(g_symbol, true))
    {
        PrintFormat("[GEMINI] 无法选择交易品种: %s", g_symbol);
        return false;
    }
    
    g_point = SymbolInfoDouble(g_symbol, SYMBOL_POINT);
    g_digits = (int)SymbolInfoInteger(g_symbol, SYMBOL_DIGITS);
    
    if(g_point == 0)
    {
        PrintFormat("[GEMINI] 无法获取品种 %s 的点值", g_symbol);
        return false;
    }
    
    g_slippage = InpSlippage;
    g_maxSpreadPt = InpMaxSpread;
    
    return true;
}

void PrintEAInfo()
{
    Print("========================================");
    Print("   GEMINI Starfleet EA v2.00");
    Print("   黄金量化交易系统 - 商业版");
    Print("========================================");
    PrintFormat("   交易品种: %s", g_symbol);
    PrintFormat("   最小点值: %.5f", g_point);
    PrintFormat("   小数位数: %d", g_digits);
    PrintFormat("   固定手数: %.2f", InpLots);
    PrintFormat("   止损点数: %d", InpStopLoss);
    PrintFormat("   止盈点数: %d", InpTakeProfit);
    PrintFormat("   最大滑点: %d 点", InpSlippage);
    PrintFormat("   最大点差: %.1f 点", InpMaxSpread);
    PrintFormat("   Magic ID: %d", InpMagicNumber);
    Print("----------------------------------------");
    PrintFormat("   移动止损启动: %d 点", InpTrailingStart);
    PrintFormat("   移动止损步长: %d 点", InpTrailingStep);
    Print("----------------------------------------");
    PrintFormat("   动态手数: %s", InpUseAutoLot ? "开启" : "关闭");
    if(InpUseAutoLot)
        PrintFormat("   风险比例: %.1f%%", InpRiskPercent);
    PrintFormat("   交易时段: %d:00 - %d:00", InpTradeStartHour, InpTradeEndHour);
    PrintFormat("   周五强制清仓: %s", InpCloseOnFriday ? "开启" : "关闭");
    if(InpCloseOnFriday)
        PrintFormat("   清仓时间: 周五 %d:00", InpFridayCloseHour);
    Print("----------------------------------------");
    PrintFormat("   EMA快线: %d | EMA慢线: %d", InpEmaFast, InpEmaSlow);
    PrintFormat("   MACD参数: %d,%d,%d", InpMacdFast, InpMacdSlow, InpMacdSignal);
    PrintFormat("   金字塔加仓: %s", InpEnablePyramid ? "开启" : "关闭");
    PrintFormat("   加仓间距: %d 点", InpPyramidDistance);
    PrintFormat("   最大层数: %d", InpMaxPositions);
    Print("========================================");
}

int OnInit()
{
    if(!ValidateSymbol())
    {
        Print("[GEMINI] 品种验证失败，EA初始化终止！");
        return INIT_FAILED;
    }
    
    if(!InitIndicators())
    {
        Print("[GEMINI] 指标初始化失败，EA初始化终止！");
        return INIT_FAILED;
    }
    
    PrintEAInfo();
    
    Print("[GEMINI] 系统初始化完成。等待交易信号...");
    
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
    ReleaseIndicators();
    
    string reasonText;
    
    switch(reason)
    {
        case REASON_PROGRAM:     reasonText = "EA自主终止"; break;
        case REASON_REMOVE:      reasonText = "EA从图表移除"; break;
        case REASON_RECOMPILE:   reasonText = "EA重新编译"; break;
        case REASON_CHARTCHANGE: reasonText = "图表周期/品种变更"; break;
        case REASON_CHARTCLOSE:  reasonText = "图表关闭"; break;
        case REASON_PARAMETERS:  reasonText = "参数变更"; break;
        case REASON_ACCOUNT:     reasonText = "账户变更"; break;
        default:                 reasonText = "未知原因"; break;
    }
    
    PrintFormat("[GEMINI] 系统终止。原因: %s", reasonText);
    Print("[GEMINI] GEMINI Starfleet EA 已离线。");
}

void OnTick()
{
    FridayCloseAll();
    
    MqlDateTime dt;
    TimeCurrent(dt);
    if(InpCloseOnFriday && dt.day_of_week == 5 && dt.hour >= InpFridayCloseHour)
    {
        return;
    }
    
    TrailingPositions();
    
    static datetime lastBarTime = 0;
    datetime currentBarTime = iTime(g_symbol, PERIOD_CURRENT, 0);
    
    if(currentBarTime == lastBarTime)
        return;
    
    lastBarTime = currentBarTime;
    
    ExecuteEntrySignals();
    
    CheckPyramiding();
}
