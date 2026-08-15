//+------------------------------------------------------------------+
//|                                        CE_RSI_Matrix_Trading.mq5 |
//|                                  Copyright 2024, Quant Developer |
//|                                  V4.1 多品种矩阵全自动对冲版       |
//+------------------------------------------------------------------+
#property copyright "Quant Developer"
#property link      ""
#property version   "4.10" 

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\DealInfo.mqh>

CTrade         trade;
CPositionInfo  posInfo;

//--- 界面输入参数 ---
input group "=== 多品种矩阵设置 ==="
input string   InpSymbols      = "XAUUSD,EURUSD,SP500,CHINA50"; // 交易品种列表 (用英文逗号分隔)
input ulong    InpMagicNumber  = 88888;                         // EA 魔术数 (独立风控标识)

input group "=== 信号引擎 (CE & RSI) ==="
input int      InpRsiFast      = 34;       // 短周期 RSI
input int      InpRsiSlow      = 144;      // 长周期 RSI
input int      InpCePeriod     = 14;       // CE ATR 周期
input double   InpCeMultiplier = 3.0;      // CE ATR 乘数

input group "=== 宏观趋势过滤 ==="
input int      InpEmaPeriod    = 200;      // 宏观趋势 EMA 周期

input group "=== 交易时间过滤 (平台服务器时间) ==="
input int      InpStartHour    = 6;        // 允许开仓起始小时 (避开亚盘)
input int      InpEndHour      = 23;       // 允许开仓结束小时

input group "=== 风控与开仓管理 ==="
input double   InpLotSize      = 0.1;      // 基础开仓手数
input int      InpAtrPeriod    = 14;       // 波动率判断 ATR 周期
input double   InpAtrThreshold = 2.0;      // 大K线判定倍数
input int      InpSwingLookback= 24;       // 近期高低点回溯根数

input group "=== 财报设置 ==="
input int      InpReportHour   = 11;       // 财报推送时间 (MT5服务器时间)

//+------------------------------------------------------------------+
//| 品种数据对象类 (独立封装每个品种的状态，彻底隔离数据串扰)              |
//+------------------------------------------------------------------+
class CSymbolData
{
public:
    string      symbol;
    int         h_rsi_fast, h_rsi_slow, h_atr, h_ema;
    datetime    last_bar_time;
    
    // CE 与 HA 状态机
    double      prev_ha_open, prev_ha_close;
    double      prev_long_stop, prev_short_stop;
    int         prev_ce_dir, current_ce_dir;
    double      current_ha_atr;
    double      ha_close_hist[];

    // 初始化指标
    bool Init(string sym_name)
    {
        symbol = sym_name;
        h_rsi_fast = iRSI(symbol, _Period, InpRsiFast, PRICE_CLOSE);
        h_rsi_slow = iRSI(symbol, _Period, InpRsiSlow, PRICE_CLOSE);
        h_atr      = iATR(symbol, _Period, InpAtrPeriod);
        h_ema      = iMA(symbol, _Period, InpEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
        
        if(h_rsi_fast == INVALID_HANDLE || h_rsi_slow == INVALID_HANDLE || h_atr == INVALID_HANDLE || h_ema == INVALID_HANDLE) 
            return false;
            
        ArrayResize(ha_close_hist, InpCePeriod);
        ArrayInitialize(ha_close_hist, 0);
        current_ha_atr = 0;
        return true;
    }

    // 预热 CE 状态机
    void WarmUp()
    {
        int warmupBars = 100;
        prev_ha_open = iOpen(symbol, _Period, warmupBars);
        prev_ha_close = iClose(symbol, _Period, warmupBars);
        prev_long_stop = 0;
        prev_short_stop = 999999;
        prev_ce_dir = 1;
        
        for(int i = warmupBars - 1; i >= 1; i--) {
            UpdateCE(i);
        }
    }

    // 步进计算 CE 状态
    void UpdateCE(int shift)
    {
        double o = iOpen(symbol, _Period, shift);
        double h = iHigh(symbol, _Period, shift);
        double l = iLow(symbol, _Period, shift);
        double c = iClose(symbol, _Period, shift);
        
        double ha_close = (o + h + l + c) / 4.0;
        double ha_open  = (prev_ha_open + prev_ha_close) / 2.0;
        double ha_high  = MathMax(h, MathMax(ha_open, ha_close));
        double ha_low   = MathMin(l, MathMin(ha_open, ha_close));
        
        double tr = MathMax(ha_high - ha_low, MathMax(MathAbs(ha_high - prev_ha_close), MathAbs(ha_low - prev_ha_close)));
        
        if(current_ha_atr == 0) current_ha_atr = tr;
        else current_ha_atr = (current_ha_atr * (InpCePeriod - 1) + tr) / InpCePeriod;
        
        for(int i = InpCePeriod - 1; i > 0; i--) {
            ha_close_hist[i] = ha_close_hist[i-1];
        }
        ha_close_hist[0] = ha_close;
        
        double highestClose = ha_close_hist[0];
        double lowestClose = ha_close_hist[0];
        for(int i = 0; i < InpCePeriod; i++) {
            if(ha_close_hist[i] != 0 && ha_close_hist[i] > highestClose) highestClose = ha_close_hist[i];
            if(ha_close_hist[i] != 0 && ha_close_hist[i] < lowestClose) lowestClose = ha_close_hist[i];
        }
        
        double atr = current_ha_atr * InpCeMultiplier;
        
        double longStop = highestClose - atr;
        if(prev_ha_close > prev_long_stop) longStop = MathMax(longStop, prev_long_stop);
        
        double shortStop = lowestClose + atr;
        if(prev_ha_close < prev_short_stop) shortStop = MathMin(shortStop, prev_short_stop);
        
        current_ce_dir = prev_ce_dir;
        if(ha_close > prev_short_stop) current_ce_dir = 1;      
        else if(ha_close < prev_long_stop) current_ce_dir = -1; 
        
        prev_ha_open = ha_open;
        prev_ha_close = ha_close;
        prev_long_stop = longStop;
        prev_short_stop = shortStop;
        prev_ce_dir = current_ce_dir;
    }

    // 检查新K线
    bool IsNewBar()
    {
        datetime current_time = iTime(symbol, _Period, 0);
        if(current_time != last_bar_time) {
            last_bar_time = current_time;
            return true;
        }
        return false;
    }
};

// 全局多品种数据数组 (修复关键字冲突)
CSymbolData ArrSymbols[];
int last_report_day = -1;

//+------------------------------------------------------------------+
//| 获取品种指针的辅助函数                                               |
//+------------------------------------------------------------------+
CSymbolData* GetSymbolData(string sym)
{
    for(int i=0; i<ArraySize(ArrSymbols); i++) {
        if(ArrSymbols[i].symbol == sym) return GetPointer(ArrSymbols[i]);
    }
    return NULL;
}

//+------------------------------------------------------------------+
//| EA 初始化函数                                                      |
//+------------------------------------------------------------------+
int OnInit()
{
    trade.SetExpertMagicNumber(InpMagicNumber); 
    
    string syms[];
    ushort sep = StringGetCharacter(",", 0);
    int count = StringSplit(InpSymbols, sep, syms);
    
    ArrayResize(ArrSymbols, count);
    int validCount = 0;
    
    for(int i=0; i<count; i++) 
    {
        StringTrimLeft(syms[i]);
        StringTrimRight(syms[i]);
        
        if(syms[i] == "") continue;
        
        if(ArrSymbols[validCount].Init(syms[i])) {
            ArrSymbols[validCount].WarmUp();
            Print("✅ 成功加载品种: ", syms[i]);
            validCount++;
        } else {
            Print("❌ 无法加载品种: ", syms[i], " (请检查拼写或市场报价中是否有该品种)");
        }
    }
    
    if(validCount == 0) {
        Print("❌ 没有任何有效品种被加载，EA 停止运行。");
        return(INIT_FAILED);
    }
    
    ArrayResize(ArrSymbols, validCount);
    EventSetTimer(60); 
    
    Print("🚀 V4.1 自动矩阵启动完成！共监控 ", validCount, " 个品种。");
    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
    EventKillTimer();
    for(int i=0; i<ArraySize(ArrSymbols); i++) {
        IndicatorRelease(ArrSymbols[i].h_rsi_fast);
        IndicatorRelease(ArrSymbols[i].h_rsi_slow);
        IndicatorRelease(ArrSymbols[i].h_atr);
        IndicatorRelease(ArrSymbols[i].h_ema);
    }
}

//+------------------------------------------------------------------+
//| 执行交易与自适应止损计算 (更新为支持多品种)                             |
//+------------------------------------------------------------------+
void ExecuteTrade(string sym, ENUM_ORDER_TYPE type, double currentAtr)
{
    double entryPrice = (type == ORDER_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_ASK) : SymbolInfoDouble(sym, SYMBOL_BID);
    double slPrice = 0;
    
    double kHigh = iHigh(sym, _Period, 1);
    double kLow  = iLow(sym, _Period, 1);
    double kRange = kHigh - kLow;
    
    if(kRange > InpAtrThreshold * currentAtr) 
    {
        slPrice = (type == ORDER_TYPE_BUY) ? kLow : kHigh;
    }
    else 
    {
        int lowestIdx  = iLowest(sym, _Period, MODE_LOW, InpSwingLookback, 1);
        int highestIdx = iHighest(sym, _Period, MODE_HIGH, InpSwingLookback, 1);
        slPrice = (type == ORDER_TYPE_BUY) ? iLow(sym, _Period, lowestIdx) : iHigh(sym, _Period, highestIdx);
    }
    
    if(type == ORDER_TYPE_BUY) {
        trade.Buy(InpLotSize, sym, entryPrice, slPrice, 0, "CE_Matrix Buy");
        SendNotification(StringFormat("🟢 %s 多单入场！(Magic: %d)", sym, InpMagicNumber));
    } else {
        trade.Sell(InpLotSize, sym, entryPrice, slPrice, 0, "CE_Matrix Sell");
        SendNotification(StringFormat("🔴 %s 空单入场！(Magic: %d)", sym, InpMagicNumber));
    }
}

//+------------------------------------------------------------------+
//| 仓位管理：1:1 分批止盈、保本与动态追踪止损 (支持多品种矩阵)               |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(posInfo.SelectByIndex(i) && posInfo.Magic() == InpMagicNumber)
        {
            string sym = posInfo.Symbol();
            CSymbolData *symData = GetSymbolData(sym);
            if(symData == NULL) continue;
            
            double openPrice = posInfo.PriceOpen();
            double currentPrice = posInfo.PriceCurrent();
            double slPrice = posInfo.StopLoss();
            double volume = posInfo.Volume();
            
            double risk = MathAbs(openPrice - slPrice);
            if(risk == 0) continue; 
            
            double targetPrice1 = (posInfo.PositionType() == POSITION_TYPE_BUY) ? (openPrice + risk) : (openPrice - risk);
            
            if(NormalizeDouble(volume, 2) == NormalizeDouble(InpLotSize, 2)) 
            {
                bool reachTarget = (posInfo.PositionType() == POSITION_TYPE_BUY && currentPrice >= targetPrice1) ||
                                   (posInfo.PositionType() == POSITION_TYPE_SELL && currentPrice <= targetPrice1);
                                   
                if(reachTarget)
                {
                    double minLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
                    double lotStep = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
                    double halfLot = MathFloor((volume / 2.0) / lotStep) * lotStep;
                    
                    if(halfLot >= minLot)
                    {
                        if(trade.PositionClosePartial(posInfo.Ticket(), halfLot)) {
                            trade.PositionModify(posInfo.Ticket(), openPrice, 0); 
                            SendNotification(StringFormat("💰 %s 达到 1:1，已平仓 %.2f 手并设保本！", sym, halfLot));
                        }
                    }
                }
            }
            else 
            {
                if(posInfo.PositionType() == POSITION_TYPE_BUY) 
                {
                    if(symData.prev_long_stop > slPrice && symData.prev_long_stop < currentPrice) {
                        trade.PositionModify(posInfo.Ticket(), symData.prev_long_stop, 0);
                    }
                }
                else if(posInfo.PositionType() == POSITION_TYPE_SELL)
                {
                    if((symData.prev_short_stop < slPrice || slPrice == 0) && symData.prev_short_stop > currentPrice) {
                        trade.PositionModify(posInfo.Ticket(), symData.prev_short_stop, 0);
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| EA 核心跳动执行函数 (多品种矩阵循环扫描)                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // 1. 24小时风控管理 (遍历矩阵下所有的订单)
    ManageOpenPositions();

    // 2. 遍历矩阵中的每一个品种，独立检测开平仓信号
    for(int i=0; i<ArraySize(ArrSymbols); i++)
    {
        string current_sym = ArrSymbols[i].symbol;
        
        if(ArrSymbols[i].IsNewBar())
        {
            ArrSymbols[i].UpdateCE(1);
            
            // --- 反向强制平仓 (独立扫描该品种) ---
            for(int p = PositionsTotal() - 1; p >= 0; p--)
            {
                if(posInfo.SelectByIndex(p) && posInfo.Magic() == InpMagicNumber && posInfo.Symbol() == current_sym)
                {
                    if(posInfo.PositionType() == POSITION_TYPE_BUY && ArrSymbols[i].current_ce_dir == -1) {
                        trade.PositionClose(posInfo.Ticket());
                    }
                    else if(posInfo.PositionType() == POSITION_TYPE_SELL && ArrSymbols[i].current_ce_dir == 1) {
                        trade.PositionClose(posInfo.Ticket());
                    }
                }
            }
            
            // --- 时间过滤 (服务器时间限制) ---
            MqlDateTime dt;
            TimeToStruct(TimeCurrent(), dt);
            if(dt.hour < InpStartHour || dt.hour > InpEndHour) continue; 
            
            // --- 开仓检测 ---
            double rsiFast[], rsiSlow[], atrData[], emaData[];
            if(CopyBuffer(ArrSymbols[i].h_rsi_fast, 0, 1, 2, rsiFast) < 2 ||
               CopyBuffer(ArrSymbols[i].h_rsi_slow, 0, 1, 2, rsiSlow) < 2 ||
               CopyBuffer(ArrSymbols[i].h_atr, 0, 1, 1, atrData) < 1 ||
               CopyBuffer(ArrSymbols[i].h_ema, 0, 1, 1, emaData) < 1) continue;
               
            bool hasPosition = false;
            for(int p=0; p<PositionsTotal(); p++) {
                if(PositionGetSymbol(p) == current_sym && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber) hasPosition = true;
            }
            
            double kClose = iClose(current_sym, _Period, 1);
            
            // 做多
            if(!hasPosition && ArrSymbols[i].current_ce_dir == 1 && rsiFast[0] <= rsiSlow[0] && rsiFast[1] > rsiSlow[1])
            {
                if(kClose > emaData[0]) ExecuteTrade(current_sym, ORDER_TYPE_BUY, atrData[0]);
            }
            // 做空 (补全被截断的这部分！)
            else if(!hasPosition && ArrSymbols[i].current_ce_dir == -1 && rsiFast[0] >= rsiSlow[0] && rsiFast[1] < rsiSlow[1])
            {
                if(kClose < emaData[0]) ExecuteTrade(current_sym, ORDER_TYPE_SELL, atrData[0]);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| 定时器：每日财报汇总 (根据 Magic Number 精准统计)                     |
//+------------------------------------------------------------------+
void OnTimer()
{
    datetime now = TimeCurrent();
    MqlDateTime dt;
    TimeToStruct(now, dt);
    
    if(dt.hour == InpReportHour && dt.day != last_report_day)
    {
        last_report_day = dt.day; 
        datetime from = now - 86400; 
        HistorySelect(from, now);
        
        double totalProfit = 0;
        int deals = HistoryDealsTotal();
        
        for(int i=0; i<deals; i++) {
            ulong ticket = HistoryDealGetTicket(i);
            // 确保这笔历史订单属于我们这个 EA
            if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == InpMagicNumber) {
                totalProfit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
                totalProfit += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
                totalProfit += HistoryDealGetDouble(ticket, DEAL_SWAP); 
            }
        }
        
        double balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double equity = AccountInfoDouble(ACCOUNT_EQUITY);
        
        string report = StringFormat("📊 【矩阵每日财报】\n昨日矩阵总盈亏: %.2f\n当前余额: %.2f\n当前净值: %.2f", 
                                     totalProfit, balance, equity);
        SendNotification(report);
        Print(report);
    }
}
//+------------------------------------------------------------------+