#property copyright "Vegas_H4_Trae1.0 - Multi-Symbol Trend Following EA"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

enum ENUM_VEGAS_SIGNAL
{
    VEGAS_SIGNAL_NONE = 0,
    VEGAS_SIGNAL_BUY  = 1,
    VEGAS_SIGNAL_SELL = 2
};

enum ENUM_LOT_MODE
{
    LOT_MODE_FIXED    = 0,
    LOT_MODE_PERCENT  = 1,
    LOT_MODE_RISK     = 2
};

input group "=== Vegas Channel Parameters ==="
input int      InpEmaFastPeriod      = 144;       // EMA Fast Period (Vegas Channel)
input int      InpEmaSlowPeriod      = 169;       // EMA Slow Period (Vegas Channel)
input int      InpSignalEmaPeriod    = 8;         // Signal EMA Period
input int      InpTunnelWidth        = 30;        // Vegas Tunnel Width (points)
input int      InpAtrPeriod          = 14;        // ATR Period
input double   InpAtrMultiplier      = 2.0;       // ATR SL Multiplier
input double   InpAtrTPMultiplier    = 3.0;       // ATR TP Multiplier
input int      InpMaxBarsAfterCross  = 30;        // Max Bars After EMA Cross (0=unlimited)
input bool     InpRequireBreakout    = false;     // Require Price Breakout
input int      InpBreakoutConfirm    = 0;         // Breakout Confirm Bars

input group "=== Multi-Symbol Settings ==="
input string   InpSymbolList         = "XAUUSD,EURUSD,SP500,CHINA50"; // Symbol List (comma separated)
input bool     InpUseCurrentSymbol   = false;     // Use Current Symbol Only
input int      InpMaxPositionsPerSymbol = 1;      // Max Positions Per Symbol
input int      InpMaxTotalPositions  = 5;         // Max Total Positions

input group "=== Position Management ==="
input ENUM_LOT_MODE InpLotMode       = LOT_MODE_RISK; // Lot Size Mode
input double   InpFixedLot           = 0.1;       // Fixed Lot Size
input double   InpRiskPercent        = 1.0;       // Risk Percent per Trade
input double   InpMaxLot             = 5.0;       // Maximum Lot Size
input double   InpMinLot             = 0.01;      // Minimum Lot Size

input group "=== Stop Loss & Take Profit ==="
input bool     InpUseDynamicSL       = true;      // Use Dynamic ATR Stop Loss
input double   InpFixedSLPoints      = 500;       // Fixed SL Points (if not dynamic)
input bool     InpUseDynamicTP       = true;      // Use Dynamic ATR Take Profit
input double   InpFixedTPPoints      = 1000;      // Fixed TP Points (if not dynamic)
input bool     InpUseTrailingStop    = true;      // Enable Trailing Stop
input double   InpTrailingStart      = 1.5;       // Trailing Start (ATR Multiplier)
input double   InpTrailingStep       = 0.5;       // Trailing Step (ATR Multiplier)
input bool     InpUseBreakeven       = true;      // Enable Breakeven
input double   InpBreakevenTrigger   = 1.0;       // Breakeven Trigger (ATR Multiplier)

input group "=== Trade Filters ==="
input int      InpTradeStartHour     = 0;         // Trade Start Hour (Server Time)
input int      InpTradeEndHour       = 23;        // Trade End Hour (Server Time)
input bool     InpCloseOnFriday      = true;      // Close All Positions on Friday
input int      InpFridayCloseHour    = 20;        // Friday Close Hour (Server Time)
input int      InpMaxSpreadPoints    = 30;        // Maximum Spread (points)
input int      InpMinStopLevel       = 50;        // Minimum Stop Level (points)

input group "=== Risk Management ==="
input double   InpDailyLossLimit     = 3.0;       // Daily Loss Limit (%)
input int      InpMaxDailyTrades     = 5;         // Max Daily Trades Per Symbol
input bool     InpUseEquityProtection= true;      // Enable Equity Protection
input double   InpEquityDropLimit    = 15.0;       // Equity Drop Limit (%)

input group "=== Notification Settings ==="
input bool     InpEnableNotification = true;      // Enable Mobile Notification
input bool     InpNotifyOnOpen       = true;      // Notify on Position Open
input bool     InpNotifyOnClose      = true;      // Notify on Position Close
input bool     InpNotifyOnBreakeven  = true;      // Notify on Breakeven
input bool     InpNotifyOnSL         = true;      // Notify on Stop Loss Hit
input bool     InpNotifyOnTP         = true;      // Notify on Take Profit Hit

input group "=== Daily Report Settings ==="
input bool     InpEnableDailyReport  = true;      // Enable Daily Report
input int      InpReportHourGMT8     = 11;        // Report Hour (GMT+8)
input bool     InpIncludeSwap        = true;      // Include Swap in Report
input bool     InpIncludeCommission  = true;      // Include Commission in Report

input group "=== EA Settings ==="
input int      InpMagicNumber        = 20250419;  // Magic Number
input string   InpTradeComment       = "Vegas_H4_Trae1.0"; // Trade Comment

class CVegasChannel
{
private:
    string   m_symbol;
    ENUM_TIMEFRAMES m_timeframe;
    int      m_handleEmaFast;
    int      m_handleEmaSlow;
    int      m_handleSignalEma;
    int      m_handleAtr;
    double   m_emaFastBuffer[];
    double   m_emaSlowBuffer[];
    double   m_signalBuffer[];
    double   m_atrBuffer[];
    datetime m_lastBarTime;
    
    bool     UpdateBuffers();
    int      FindLastCrossBars(bool isBullish);
    
public:
    void     CVegasChannel();
    void    ~CVegasChannel();
    bool     Init(string symbol, ENUM_TIMEFRAMES timeframe);
    ENUM_VEGAS_SIGNAL GetSignal();
    double   GetEmaFast(int shift = 0);
    double   GetEmaSlow(int shift = 0);
    double   GetSignalEma(int shift = 0);
    double   GetCurrentAtr();
    double   GetTunnelWidth();
    bool     IsBullishTrend();
    bool     IsBearishTrend();
    bool     IsPriceAboveTunnel();
    bool     IsPriceBelowTunnel();
};

class CVegasRisk
{
private:
    string   m_symbol;
    int      m_digits;
    double   m_point;
    double   m_tickValue;
    double   m_tickSize;
    int      m_magic;
    double   m_dailyStartEquity;
    double   m_accountStartEquity;
    int      m_dailyTradeCount;
    datetime m_lastTradeDate;
    
public:
    void     CVegasRisk();
    bool     Init(string symbol, int digits, double point, int magic);
    double   CalculateLotSize(double slDistance, ENUM_POSITION_TYPE posType);
    double   CalculateSLDistance(double atrValue);
    double   CalculateTPDistance(double atrValue);
    bool     CheckDailyLossLimit();
    bool     CheckEquityProtection();
    bool     CheckMaxDailyTrades();
    void     IncrementTradeCount();
    void     ResetDailyCounters();
    int      GetDailyTradeCount();
    double   GetDailyStartEquity();
};

class CVegasPositionManager
{
private:
    string   m_symbol;
    int      m_magic;
    double   m_point;
    int      m_digits;
    CTrade   m_trade;
    double   m_lastTrailingPrice;
    datetime m_lastTrailingTime;
    
    int      GetPositionCount();
    bool     MoveToBreakeven(ulong ticket, double openPrice);
    bool     UpdateTrailingStop(ulong ticket, double atrValue);
    
public:
    void     CVegasPositionManager();
    bool     Init(string symbol, int magic, double point, int digits);
    bool     OpenPosition(ENUM_POSITION_TYPE posType, double lots, double sl, double tp, string comment);
    bool     ClosePosition(ulong ticket, string reason = "");
    bool     CloseAllPositions(string reason = "");
    void     ManagePositions(double atrValue);
    int      GetOpenPositionsCount();
    bool     HasOpenPosition();
    bool     GetPositionInfo(ulong &ticket, double &openPrice, double &volume, ENUM_POSITION_TYPE &posType);
};

class CVegasNotification
{
private:
    bool     m_enabled;
    datetime m_lastNotifyTime;
    int      m_notifyCooldown;
    
public:
    void     CVegasNotification();
    void     Init(bool enabled);
    void     SendOpenNotification(string symbol, ENUM_POSITION_TYPE posType, double lots, double price, double sl, double tp);
    void     SendCloseNotification(string symbol, ENUM_POSITION_TYPE posType, double lots, double profit, string reason);
    void     SendBreakevenNotification(string symbol, ulong ticket, double price);
    void     SendDailyReport(string symbol, double dailyProfit, double dailySwap, double dailyCommission, int tradeCount, double balance, double equity);
    void     SendAlert(string message);
};

class CVegasDailyReport
{
private:
    datetime m_lastReportDate;
    int      m_reportHourGMT8;
    double   m_yesterdayStartEquity;
    double   m_yesterdayProfit;
    double   m_yesterdaySwap;
    double   m_yesterdayCommission;
    int      m_yesterdayTradeCount;
    
    int      GetGMT8Hour();
    bool     IsReportTime();
    void     CalculateYesterdayStats();
    
public:
    void     CVegasDailyReport();
    void     Init(int reportHourGMT8);
    void     CheckAndSendReport(CVegasNotification &notify);
    void     OnTradeEvent(double profit, double swap, double commission);
};

class CVegasMultiSymbol
{
private:
    string   m_symbols[];
    int      m_symbolCount;
    bool     m_useCurrentSymbol;
    
public:
    void     CVegasMultiSymbol();
    bool     Init(string symbolList, bool useCurrentSymbol);
    int      GetSymbolCount();
    string   GetSymbol(int index);
    bool     IsValidSymbol(string symbol);
};

CVegasChannel          g_vegasChannel[];
CVegasRisk             g_vegasRisk[];
CVegasPositionManager  g_vegasPositionMgr[];
CVegasNotification     g_vegasNotify;
CVegasDailyReport      g_dailyReport;
CVegasMultiSymbol      g_multiSymbol;
CTrade                 g_trade;
datetime               g_lastBarTime[];
bool                   g_fridayClosed = false;
datetime               g_fridayCloseTime = 0;
bool                   g_equityProtectionTriggered = false;

void CVegasChannel::CVegasChannel()
{
    m_symbol = "";
    m_timeframe = PERIOD_H4;
    m_handleEmaFast = INVALID_HANDLE;
    m_handleEmaSlow = INVALID_HANDLE;
    m_handleSignalEma = INVALID_HANDLE;
    m_handleAtr = INVALID_HANDLE;
    m_lastBarTime = 0;
    ArraySetAsSeries(m_emaFastBuffer, true);
    ArraySetAsSeries(m_emaSlowBuffer, true);
    ArraySetAsSeries(m_signalBuffer, true);
    ArraySetAsSeries(m_atrBuffer, true);
}

CVegasChannel::~CVegasChannel()
{
    if(m_handleEmaFast != INVALID_HANDLE) IndicatorRelease(m_handleEmaFast);
    if(m_handleEmaSlow != INVALID_HANDLE) IndicatorRelease(m_handleEmaSlow);
    if(m_handleSignalEma != INVALID_HANDLE) IndicatorRelease(m_handleSignalEma);
    if(m_handleAtr != INVALID_HANDLE) IndicatorRelease(m_handleAtr);
}

bool CVegasChannel::Init(string symbol, ENUM_TIMEFRAMES timeframe)
{
    m_symbol = symbol;
    m_timeframe = timeframe;
    
    m_handleEmaFast = iMA(m_symbol, m_timeframe, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
    if(m_handleEmaFast == INVALID_HANDLE)
    {
        PrintFormat("[Vegas] EMA Fast 创建失败！Symbol: %s, Error: %d", m_symbol, GetLastError());
        return false;
    }
    
    m_handleEmaSlow = iMA(m_symbol, m_timeframe, InpEmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
    if(m_handleEmaSlow == INVALID_HANDLE)
    {
        PrintFormat("[Vegas] EMA Slow 创建失败！Symbol: %s, Error: %d", m_symbol, GetLastError());
        return false;
    }
    
    m_handleSignalEma = iMA(m_symbol, m_timeframe, InpSignalEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
    if(m_handleSignalEma == INVALID_HANDLE)
    {
        PrintFormat("[Vegas] Signal EMA 创建失败！Symbol: %s, Error: %d", m_symbol, GetLastError());
        return false;
    }
    
    m_handleAtr = iATR(m_symbol, m_timeframe, InpAtrPeriod);
    if(m_handleAtr == INVALID_HANDLE)
    {
        PrintFormat("[Vegas] ATR 创建失败！Symbol: %s, Error: %d", m_symbol, GetLastError());
        return false;
    }
    
    PrintFormat("[Vegas] 通道初始化成功！Symbol: %s, Timeframe: H4", m_symbol);
    return true;
}

bool CVegasChannel::UpdateBuffers()
{
    if(CopyBuffer(m_handleEmaFast, 0, 0, 3, m_emaFastBuffer) < 3) return false;
    if(CopyBuffer(m_handleEmaSlow, 0, 0, 3, m_emaSlowBuffer) < 3) return false;
    if(CopyBuffer(m_handleSignalEma, 0, 0, 3, m_signalBuffer) < 3) return false;
    if(CopyBuffer(m_handleAtr, 0, 0, 1, m_atrBuffer) < 1) return false;
    
    return true;
}

int CVegasChannel::FindLastCrossBars(bool isBullish)
{
    double emaFast[], emaSlow[];
    ArraySetAsSeries(emaFast, true);
    ArraySetAsSeries(emaSlow, true);
    
    int lookback = 50;
    if(CopyBuffer(m_handleEmaFast, 0, 0, lookback, emaFast) < lookback) return -1;
    if(CopyBuffer(m_handleEmaSlow, 0, 0, lookback, emaSlow) < lookback) return -1;
    
    for(int i = 1; i < lookback - 1; i++)
    {
        if(isBullish)
        {
            if(emaFast[i] > emaSlow[i] && emaFast[i+1] <= emaSlow[i+1])
                return i;
        }
        else
        {
            if(emaFast[i] < emaSlow[i] && emaFast[i+1] >= emaSlow[i+1])
                return i;
        }
    }
    
    return -1;
}

ENUM_VEGAS_SIGNAL CVegasChannel::GetSignal()
{
    if(!UpdateBuffers()) return VEGAS_SIGNAL_NONE;
    
    double emaFastCurrent = m_emaFastBuffer[0];
    double emaFastPrev = m_emaFastBuffer[1];
    double emaSlowCurrent = m_emaSlowBuffer[0];
    double emaSlowPrev = m_emaSlowBuffer[1];
    double signalEmaCurrent = m_signalBuffer[0];
    double signalEmaPrev = m_signalBuffer[1];
    
    double tunnelWidth = InpTunnelWidth * SymbolInfoDouble(m_symbol, SYMBOL_POINT);
    double tunnelTop = MathMax(emaFastCurrent, emaSlowCurrent) + tunnelWidth;
    double tunnelBottom = MathMin(emaFastCurrent, emaSlowCurrent) - tunnelWidth;
    
    double closePrice = iClose(m_symbol, m_timeframe, 0);
    double prevClosePrice = iClose(m_symbol, m_timeframe, 1);
    
    bool isBullish = (emaFastCurrent > emaSlowCurrent);
    bool isBearish = (emaFastCurrent < emaSlowCurrent);
    
    if(isBullish)
    {
        if(InpMaxBarsAfterCross > 0)
        {
            int barsSinceCross = FindLastCrossBars(true);
            if(barsSinceCross < 0 || barsSinceCross > InpMaxBarsAfterCross)
                return VEGAS_SIGNAL_NONE;
        }
        
        if(InpRequireBreakout)
        {
            if(closePrice <= tunnelTop)
                return VEGAS_SIGNAL_NONE;
            
            if(InpBreakoutConfirm > 0)
            {
                bool confirmed = false;
                for(int i = 1; i <= InpBreakoutConfirm; i++)
                {
                    double prevClose = iClose(m_symbol, m_timeframe, i);
                    double prevTunnelTop = MathMax(
                        GetEmaFast(i), GetEmaSlow(i)) + tunnelWidth;
                    if(prevClose > prevTunnelTop)
                    {
                        confirmed = true;
                        break;
                    }
                }
                if(!confirmed)
                    return VEGAS_SIGNAL_NONE;
            }
        }
        
        if(signalEmaCurrent <= signalEmaPrev)
            return VEGAS_SIGNAL_NONE;
        
        PrintFormat("[Vegas] 做多信号！EMA144(%.5f) > EMA169(%.5f), 价格(%.5f) > 通道上轨(%.5f)", 
                    emaFastCurrent, emaSlowCurrent, closePrice, tunnelTop);
        return VEGAS_SIGNAL_BUY;
    }
    
    if(isBearish)
    {
        if(InpMaxBarsAfterCross > 0)
        {
            int barsSinceCross = FindLastCrossBars(false);
            if(barsSinceCross < 0 || barsSinceCross > InpMaxBarsAfterCross)
                return VEGAS_SIGNAL_NONE;
        }
        
        if(InpRequireBreakout)
        {
            if(closePrice >= tunnelBottom)
                return VEGAS_SIGNAL_NONE;
            
            if(InpBreakoutConfirm > 0)
            {
                bool confirmed = false;
                for(int i = 1; i <= InpBreakoutConfirm; i++)
                {
                    double prevClose = iClose(m_symbol, m_timeframe, i);
                    double prevTunnelBottom = MathMin(
                        GetEmaFast(i), GetEmaSlow(i)) - tunnelWidth;
                    if(prevClose < prevTunnelBottom)
                    {
                        confirmed = true;
                        break;
                    }
                }
                if(!confirmed)
                    return VEGAS_SIGNAL_NONE;
            }
        }
        
        if(signalEmaCurrent >= signalEmaPrev)
            return VEGAS_SIGNAL_NONE;
        
        PrintFormat("[Vegas] 做空信号！EMA144(%.5f) < EMA169(%.5f), 价格(%.5f) < 通道下轨(%.5f)", 
                    emaFastCurrent, emaSlowCurrent, closePrice, tunnelBottom);
        return VEGAS_SIGNAL_SELL;
    }
    
    return VEGAS_SIGNAL_NONE;
}

double CVegasChannel::GetEmaFast(int shift = 0)
{
    double buffer[];
    ArraySetAsSeries(buffer, true);
    if(CopyBuffer(m_handleEmaFast, 0, 0, shift + 1, buffer) < shift + 1) return 0;
    return buffer[shift];
}

double CVegasChannel::GetEmaSlow(int shift = 0)
{
    double buffer[];
    ArraySetAsSeries(buffer, true);
    if(CopyBuffer(m_handleEmaSlow, 0, 0, shift + 1, buffer) < shift + 1) return 0;
    return buffer[shift];
}

double CVegasChannel::GetSignalEma(int shift = 0)
{
    double buffer[];
    ArraySetAsSeries(buffer, true);
    if(CopyBuffer(m_handleSignalEma, 0, 0, shift + 1, buffer) < shift + 1) return 0;
    return buffer[shift];
}

double CVegasChannel::GetCurrentAtr()
{
    double atr[];
    ArraySetAsSeries(atr, true);
    if(CopyBuffer(m_handleAtr, 0, 0, 1, atr) < 1) return 0;
    return atr[0];
}

double CVegasChannel::GetTunnelWidth()
{
    return InpTunnelWidth * SymbolInfoDouble(m_symbol, SYMBOL_POINT);
}

bool CVegasChannel::IsBullishTrend()
{
    if(!UpdateBuffers()) return false;
    return m_emaFastBuffer[0] > m_emaSlowBuffer[0];
}

bool CVegasChannel::IsBearishTrend()
{
    if(!UpdateBuffers()) return false;
    return m_emaFastBuffer[0] < m_emaSlowBuffer[0];
}

bool CVegasChannel::IsPriceAboveTunnel()
{
    if(!UpdateBuffers()) return false;
    
    double tunnelTop = MathMax(m_emaFastBuffer[0], m_emaSlowBuffer[0]) + GetTunnelWidth();
    double closePrice = iClose(m_symbol, m_timeframe, 0);
    
    return closePrice > tunnelTop;
}

bool CVegasChannel::IsPriceBelowTunnel()
{
    if(!UpdateBuffers()) return false;
    
    double tunnelBottom = MathMin(m_emaFastBuffer[0], m_emaSlowBuffer[0]) - GetTunnelWidth();
    double closePrice = iClose(m_symbol, m_timeframe, 0);
    
    return closePrice < tunnelBottom;
}

void CVegasRisk::CVegasRisk()
{
    m_symbol = "";
    m_digits = 0;
    m_point = 0;
    m_tickValue = 0;
    m_tickSize = 0;
    m_magic = 0;
    m_dailyStartEquity = 0;
    m_accountStartEquity = 0;
    m_dailyTradeCount = 0;
    m_lastTradeDate = 0;
}

bool CVegasRisk::Init(string symbol, int digits, double point, int magic)
{
    m_symbol = symbol;
    m_digits = digits;
    m_point = point;
    m_magic = magic;
    
    m_tickValue = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE);
    m_tickSize = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_SIZE);
    
    if(m_tickSize == 0 || m_tickValue == 0)
    {
        PrintFormat("[Vegas] %s 获取 Tick 信息失败！", m_symbol);
        return false;
    }
    
    m_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    m_accountStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    m_dailyTradeCount = 0;
    m_lastTradeDate = 0;
    
    PrintFormat("[Vegas] 风控模块初始化成功！Symbol: %s, Daily Start Equity: %.2f", m_symbol, m_dailyStartEquity);
    return true;
}

double CVegasRisk::CalculateLotSize(double slDistance, ENUM_POSITION_TYPE posType)
{
    if(slDistance <= 0) return 0;
    
    double lotSize = 0;
    
    switch(InpLotMode)
    {
        case LOT_MODE_FIXED:
            lotSize = InpFixedLot;
            break;
            
        case LOT_MODE_PERCENT:
            {
                double equity = AccountInfoDouble(ACCOUNT_EQUITY);
                double marginPerLot = 0;
                
                if(!OrderCalcMargin(posType == POSITION_TYPE_BUY ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, 
                                   m_symbol, 1.0, 
                                   posType == POSITION_TYPE_BUY ? SymbolInfoDouble(m_symbol, SYMBOL_ASK) : SymbolInfoDouble(m_symbol, SYMBOL_BID),
                                   marginPerLot))
                {
                    PrintFormat("[Vegas] OrderCalcMargin 失败！Error: %d", GetLastError());
                    return 0;
                }
                
                if(marginPerLot <= 0) return 0;
                
                double maxMargin = equity * (InpRiskPercent / 100.0);
                lotSize = (maxMargin / marginPerLot);
            }
            break;
            
        case LOT_MODE_RISK:
            {
                double equity = AccountInfoDouble(ACCOUNT_EQUITY);
                double riskAmount = equity * (InpRiskPercent / 100.0);
                
                double slPoints = slDistance / m_point;
                double lossPerLot = slPoints * m_tickValue * (m_tickSize / m_point);
                
                if(lossPerLot <= 0)
                {
                    double askPrice = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
                    double slPrice = posType == POSITION_TYPE_BUY ? askPrice - slDistance : askPrice + slDistance;
                    double lossForOneLot = 0;
                    
                    if(!OrderCalcProfit(posType == POSITION_TYPE_BUY ? ORDER_TYPE_BUY : ORDER_TYPE_SELL,
                                       m_symbol, 1.0, askPrice, slPrice, lossForOneLot))
                    {
                        PrintFormat("[Vegas] OrderCalcProfit 失败！Error: %d", GetLastError());
                        return 0;
                    }
                    
                    lossPerLot = MathAbs(lossForOneLot);
                }
                
                if(lossPerLot <= 0) return 0;
                
                lotSize = riskAmount / lossPerLot;
                
                PrintFormat("[Vegas] 风险计算: 净值=%.2f, 风险金额=%.2f, SL距离=%.5f, 每手亏损=%.2f, 计算手数=%.5f",
                           equity, riskAmount, slDistance, lossPerLot, lotSize);
            }
            break;
    }
    
    double minLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);
    
    if(minLot <= 0) minLot = InpMinLot;
    if(maxLot <= 0) maxLot = InpMaxLot;
    if(lotStep <= 0) lotStep = 0.01;
    
    lotSize = MathFloor(lotSize / lotStep) * lotStep;
    
    if(lotSize < minLot) lotSize = minLot;
    if(lotSize > maxLot) lotSize = maxLot;
    if(lotSize > InpMaxLot) lotSize = InpMaxLot;
    
    return NormalizeDouble(lotSize, 2);
}

double CVegasRisk::CalculateSLDistance(double atrValue)
{
    if(InpUseDynamicSL && atrValue > 0)
    {
        return atrValue * InpAtrMultiplier;
    }
    return InpFixedSLPoints * m_point;
}

double CVegasRisk::CalculateTPDistance(double atrValue)
{
    if(InpUseDynamicTP && atrValue > 0)
    {
        return atrValue * InpAtrTPMultiplier;
    }
    return InpFixedTPPoints * m_point;
}

bool CVegasRisk::CheckDailyLossLimit()
{
    if(InpDailyLossLimit <= 0) return false;
    
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double drawdown = (m_dailyStartEquity - currentEquity) / m_dailyStartEquity * 100.0;
    
    if(drawdown >= InpDailyLossLimit)
    {
        PrintFormat("[Vegas] 每日亏损限额触发！回撤: %.2f%% >= 限额: %.2f%%", drawdown, InpDailyLossLimit);
        return true;
    }
    
    return false;
}

bool CVegasRisk::CheckEquityProtection()
{
    if(!InpUseEquityProtection) return false;
    
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double drop = (m_accountStartEquity - currentEquity) / m_accountStartEquity * 100.0;
    
    if(drop >= InpEquityDropLimit)
    {
        PrintFormat("[Vegas] 账户权益保护触发！权益下降: %.2f%% >= 限额: %.2f%%", drop, InpEquityDropLimit);
        return true;
    }
    
    return false;
}

bool CVegasRisk::CheckMaxDailyTrades()
{
    datetime today = iTime(m_symbol, PERIOD_D1, 0);
    
    if(m_lastTradeDate != today)
    {
        m_dailyTradeCount = 0;
        m_lastTradeDate = today;
    }
    
    return m_dailyTradeCount >= InpMaxDailyTrades;
}

void CVegasRisk::IncrementTradeCount()
{
    datetime today = iTime(m_symbol, PERIOD_D1, 0);
    
    if(m_lastTradeDate != today)
    {
        m_dailyTradeCount = 0;
        m_lastTradeDate = today;
    }
    
    m_dailyTradeCount++;
}

void CVegasRisk::ResetDailyCounters()
{
    datetime today = iTime(m_symbol, PERIOD_D1, 0);
    
    if(m_lastTradeDate != today)
    {
        m_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
        m_dailyTradeCount = 0;
        m_lastTradeDate = today;
        PrintFormat("[Vegas] 每日计数器重置！新日起始权益: %.2f", m_dailyStartEquity);
    }
}

int CVegasRisk::GetDailyTradeCount()
{
    return m_dailyTradeCount;
}

double CVegasRisk::GetDailyStartEquity()
{
    return m_dailyStartEquity;
}

void CVegasPositionManager::CVegasPositionManager()
{
    m_symbol = "";
    m_magic = 0;
    m_point = 0;
    m_digits = 0;
    m_lastTrailingPrice = 0;
    m_lastTrailingTime = 0;
}

bool CVegasPositionManager::Init(string symbol, int magic, double point, int digits)
{
    m_symbol = symbol;
    m_magic = magic;
    m_point = point;
    m_digits = digits;
    
    m_trade.SetExpertMagicNumber(m_magic);
    m_trade.SetMarginMode();
    m_trade.SetTypeFillingBySymbol(m_symbol);
    m_trade.SetDeviationInPoints(30);
    
    PrintFormat("[Vegas] 仓位管理器初始化成功！Symbol: %s, Magic: %d", m_symbol, m_magic);
    return true;
}

int CVegasPositionManager::GetPositionCount()
{
    int count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        count++;
    }
    return count;
}

bool CVegasPositionManager::OpenPosition(ENUM_POSITION_TYPE posType, double lots, double sl, double tp, string comment)
{
    if(lots <= 0)
    {
        PrintFormat("[Vegas] 无效手数: %.5f", lots);
        return false;
    }
    
    if(GetPositionCount() >= InpMaxPositionsPerSymbol)
    {
        PrintFormat("[Vegas] %s 已达最大持仓数: %d", m_symbol, InpMaxPositionsPerSymbol);
        return false;
    }
    
    double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
    
    if(ask <= 0 || bid <= 0)
    {
        PrintFormat("[Vegas] 获取报价失败！");
        return false;
    }
    
    double openPrice = (posType == POSITION_TYPE_BUY) ? ask : bid;
    
    double minStop = SymbolInfoInteger(m_symbol, SYMBOL_TRADE_STOPS_LEVEL) * m_point;
    if(minStop < InpMinStopLevel * m_point) minStop = InpMinStopLevel * m_point;
    
    if(sl > 0)
    {
        if(posType == POSITION_TYPE_BUY)
        {
            sl = NormalizeDouble(MathMin(openPrice - minStop, sl), m_digits);
        }
        else
        {
            sl = NormalizeDouble(MathMax(openPrice + minStop, sl), m_digits);
        }
    }
    
    if(tp > 0)
    {
        if(posType == POSITION_TYPE_BUY)
        {
            tp = NormalizeDouble(MathMax(openPrice + minStop, tp), m_digits);
        }
        else
        {
            tp = NormalizeDouble(MathMin(openPrice - minStop, tp), m_digits);
        }
    }
    
    ENUM_ORDER_TYPE orderType = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    
    m_trade.SetExpertMagicNumber(m_magic);
    
    bool result = false;
    
    if(posType == POSITION_TYPE_BUY)
    {
        result = m_trade.Buy(lots, m_symbol, openPrice, sl, tp, comment);
    }
    else
    {
        result = m_trade.Sell(lots, m_symbol, openPrice, sl, tp, comment);
    }
    
    if(result)
    {
        PrintFormat("[Vegas] 开仓成功！%s %s %.2f手 @ %.5f, SL: %.5f, TP: %.5f",
                   m_symbol, posType == POSITION_TYPE_BUY ? "BUY" : "SELL", 
                   lots, openPrice, sl, tp);
    }
    else
    {
        PrintFormat("[Vegas] 开仓失败！Error: %d, RetCode: %d", GetLastError(), m_trade.ResultRetcode());
    }
    
    return result;
}

bool CVegasPositionManager::ClosePosition(ulong ticket, string reason = "")
{
    if(!PositionSelectByTicket(ticket)) return false;
    
    double volume = PositionGetDouble(POSITION_VOLUME);
    ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    
    m_trade.SetExpertMagicNumber(m_magic);
    
    bool result = m_trade.PositionClose(ticket);
    
    if(result)
    {
        double profit = PositionGetDouble(POSITION_PROFIT);
        PrintFormat("[Vegas] 平仓成功！Ticket: %I64u, Profit: %.2f, Reason: %s", ticket, profit, reason);
    }
    else
    {
        PrintFormat("[Vegas] 平仓失败！Ticket: %I64u, Error: %d", ticket, GetLastError());
    }
    
    return result;
}

bool CVegasPositionManager::CloseAllPositions(string reason = "")
{
    int closedCount = 0;
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        
        if(ClosePosition(ticket, reason))
        {
            closedCount++;
        }
    }
    
    PrintFormat("[Vegas] 关闭 %d 个仓位, Reason: %s", closedCount, reason);
    return closedCount > 0;
}

bool CVegasPositionManager::MoveToBreakeven(ulong ticket, double openPrice)
{
    if(!PositionSelectByTicket(ticket)) return false;
    
    ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    double currentSL = PositionGetDouble(POSITION_SL);
    double currentTP = PositionGetDouble(POSITION_TP);
    
    double newSL = NormalizeDouble(openPrice, m_digits);
    
    bool shouldMove = false;
    
    if(posType == POSITION_TYPE_BUY)
    {
        if(currentSL == 0 || currentSL < openPrice - m_point)
            shouldMove = true;
    }
    else
    {
        if(currentSL == 0 || currentSL > openPrice + m_point)
            shouldMove = true;
    }
    
    if(shouldMove)
    {
        m_trade.SetExpertMagicNumber(m_magic);
        bool result = m_trade.PositionModify(ticket, newSL, currentTP);
        
        if(result)
        {
            PrintFormat("[Vegas] 保本成功！Ticket: %I64u, SL: %.5f", ticket, newSL);
        }
        
        return result;
    }
    
    return false;
}

bool CVegasPositionManager::UpdateTrailingStop(ulong ticket, double atrValue)
{
    if(!PositionSelectByTicket(ticket)) return false;
    
    ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    double currentSL = PositionGetDouble(POSITION_SL);
    double currentTP = PositionGetDouble(POSITION_TP);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    
    double currentPrice = (posType == POSITION_TYPE_BUY) ? 
                          SymbolInfoDouble(m_symbol, SYMBOL_BID) : 
                          SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    
    double profitDistance = (posType == POSITION_TYPE_BUY) ? 
                            (currentPrice - openPrice) : 
                            (openPrice - currentPrice);
    
    double trailingTrigger = atrValue * InpTrailingStart;
    
    if(profitDistance < trailingTrigger) return false;
    
    double trailingStep = atrValue * InpTrailingStep;
    double newSL = 0;
    
    if(posType == POSITION_TYPE_BUY)
    {
        newSL = NormalizeDouble(currentPrice - trailingStep, m_digits);
        
        if(newSL <= openPrice) return false;
        if(currentSL > 0 && newSL <= currentSL + m_point) return false;
    }
    else
    {
        newSL = NormalizeDouble(currentPrice + trailingStep, m_digits);
        
        if(newSL >= openPrice) return false;
        if(currentSL > 0 && newSL >= currentSL - m_point) return false;
    }
    
    m_trade.SetExpertMagicNumber(m_magic);
    bool result = m_trade.PositionModify(ticket, newSL, currentTP);
    
    if(result)
    {
        PrintFormat("[Vegas] 移动止损成功！Ticket: %I64u, New SL: %.5f", ticket, newSL);
    }
    
    return result;
}

void CVegasPositionManager::ManagePositions(double atrValue)
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        
        ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
        double currentSL = PositionGetDouble(POSITION_SL);
        
        double currentPrice = (posType == POSITION_TYPE_BUY) ? 
                              SymbolInfoDouble(m_symbol, SYMBOL_BID) : 
                              SymbolInfoDouble(m_symbol, SYMBOL_ASK);
        
        double profitDistance = (posType == POSITION_TYPE_BUY) ? 
                                (currentPrice - openPrice) : 
                                (openPrice - currentPrice);
        
        if(InpUseBreakeven && atrValue > 0)
        {
            double breakevenTrigger = atrValue * InpBreakevenTrigger;
            
            if(profitDistance >= breakevenTrigger)
            {
                if((posType == POSITION_TYPE_BUY && (currentSL == 0 || currentSL < openPrice)) ||
                   (posType == POSITION_TYPE_SELL && (currentSL == 0 || currentSL > openPrice)))
                {
                    if(MoveToBreakeven(ticket, openPrice))
                    {
                        g_vegasNotify.SendBreakevenNotification(m_symbol, ticket, openPrice);
                    }
                }
            }
        }
        
        if(InpUseTrailingStop && atrValue > 0)
        {
            UpdateTrailingStop(ticket, atrValue);
        }
    }
}

int CVegasPositionManager::GetOpenPositionsCount()
{
    return GetPositionCount();
}

bool CVegasPositionManager::HasOpenPosition()
{
    return GetPositionCount() > 0;
}

bool CVegasPositionManager::GetPositionInfo(ulong &ticket, double &openPrice, double &volume, ENUM_POSITION_TYPE &posType)
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong t = PositionGetTicket(i);
        if(t == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        
        ticket = t;
        openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
        volume = PositionGetDouble(POSITION_VOLUME);
        posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        return true;
    }
    
    return false;
}

void CVegasNotification::CVegasNotification()
{
    m_enabled = false;
    m_lastNotifyTime = 0;
    m_notifyCooldown = 5;
}

void CVegasNotification::Init(bool enabled)
{
    m_enabled = enabled;
}

void CVegasNotification::SendOpenNotification(string symbol, ENUM_POSITION_TYPE posType, double lots, double price, double sl, double tp)
{
    if(!m_enabled || !InpNotifyOnOpen) return;
    
    string message = StringFormat("[Vegas H4] 开仓通知\n品种: %s\n方向: %s\n手数: %.2f\n价格: %.5f\n止损: %.5f\n止盈: %.5f\n时间: %s",
                                  symbol,
                                  posType == POSITION_TYPE_BUY ? "做多" : "做空",
                                  lots, price, sl, tp,
                                  TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES));
    
    if(SendNotification(message))
    {
        PrintFormat("[Vegas] 开仓通知发送成功！");
    }
}

void CVegasNotification::SendCloseNotification(string symbol, ENUM_POSITION_TYPE posType, double lots, double profit, string reason)
{
    if(!m_enabled || !InpNotifyOnClose) return;
    
    string message = StringFormat("[Vegas H4] 平仓通知\n品种: %s\n方向: %s\n手数: %.2f\n盈亏: %.2f\n原因: %s\n时间: %s",
                                  symbol,
                                  posType == POSITION_TYPE_BUY ? "多单" : "空单",
                                  lots, profit, reason,
                                  TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES));
    
    if(SendNotification(message))
    {
        PrintFormat("[Vegas] 平仓通知发送成功！");
    }
}

void CVegasNotification::SendBreakevenNotification(string symbol, ulong ticket, double price)
{
    if(!m_enabled || !InpNotifyOnBreakeven) return;
    
    string message = StringFormat("[Vegas H4] 保本通知\n品种: %s\n单号: %d\n保本价: %.5f\n时间: %s",
                                  symbol, ticket, price,
                                  TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES));
    
    if(SendNotification(message))
    {
        PrintFormat("[Vegas] 保本通知发送成功！");
    }
}

void CVegasNotification::SendDailyReport(string symbol, double dailyProfit, double dailySwap, double dailyCommission, int tradeCount, double balance, double equity)
{
    if(!m_enabled) return;
    
    string message = StringFormat("[Vegas H4] 每日财报\n日期: %s\n交易次数: %d\n盈亏: %.2f\n隔夜利息: %.2f\n手续费: %.2f\n净盈亏: %.2f\n余额: %.2f\n净值: %.2f",
                                  TimeToString(TimeCurrent() - 86400, TIME_DATE),
                                  tradeCount,
                                  dailyProfit,
                                  dailySwap,
                                  dailyCommission,
                                  dailyProfit + dailySwap + dailyCommission,
                                  balance,
                                  equity);
    
    if(SendNotification(message))
    {
        PrintFormat("[Vegas] 每日财报发送成功！");
    }
}

void CVegasNotification::SendAlert(string message)
{
    if(!m_enabled) return;
    
    SendNotification(message);
}

void CVegasDailyReport::CVegasDailyReport()
{
    m_lastReportDate = 0;
    m_reportHourGMT8 = 11;
    m_yesterdayStartEquity = 0;
    m_yesterdayProfit = 0;
    m_yesterdaySwap = 0;
    m_yesterdayCommission = 0;
    m_yesterdayTradeCount = 0;
}

void CVegasDailyReport::Init(int reportHourGMT8)
{
    m_reportHourGMT8 = reportHourGMT8;
    m_yesterdayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
}

int CVegasDailyReport::GetGMT8Hour()
{
    MqlDateTime dt;
    TimeCurrent(dt);
    
    datetime gmtTime = TimeCurrent();
    datetime gmt8Time = gmtTime + 8 * 3600;
    
    MqlDateTime dtGMT8;
    TimeToStruct(gmt8Time, dtGMT8);
    
    return dtGMT8.hour;
}

bool CVegasDailyReport::IsReportTime()
{
    int currentHour = GetGMT8Hour();
    datetime today = iTime(_Symbol, PERIOD_D1, 0);
    
    if(currentHour == m_reportHourGMT8 && m_lastReportDate != today)
    {
        return true;
    }
    
    return false;
}

void CVegasDailyReport::CalculateYesterdayStats()
{
    datetime yesterdayStart = iTime(_Symbol, PERIOD_D1, 1);
    datetime yesterdayEnd = iTime(_Symbol, PERIOD_D1, 0) - 1;
    
    if(!HistorySelect(yesterdayStart, yesterdayEnd))
    {
        PrintFormat("[Vegas] 无法获取历史交易记录！");
        return;
    }
    
    m_yesterdayProfit = 0;
    m_yesterdaySwap = 0;
    m_yesterdayCommission = 0;
    m_yesterdayTradeCount = 0;
    
    int totalDeals = HistoryDealsTotal();
    
    for(int i = 0; i < totalDeals; i++)
    {
        ulong dealTicket = HistoryDealGetTicket(i);
        if(dealTicket == 0) continue;
        
        ENUM_DEAL_ENTRY dealEntry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
        if(dealEntry != DEAL_ENTRY_OUT) continue;
        
        if(HistoryDealGetInteger(dealTicket, DEAL_MAGIC) != InpMagicNumber) continue;
        
        m_yesterdayProfit += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
        
        if(InpIncludeSwap)
        {
            m_yesterdaySwap += HistoryDealGetDouble(dealTicket, DEAL_SWAP);
        }
        
        if(InpIncludeCommission)
        {
            m_yesterdayCommission += HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
        }
        
        m_yesterdayTradeCount++;
    }
    
    PrintFormat("[Vegas] 昨日统计: 盈亏=%.2f, 隔夜利息=%.2f, 手续费=%.2f, 交易次数=%d",
               m_yesterdayProfit, m_yesterdaySwap, m_yesterdayCommission, m_yesterdayTradeCount);
}

void CVegasDailyReport::CheckAndSendReport(CVegasNotification &notify)
{
    if(!InpEnableDailyReport) return;
    
    if(IsReportTime())
    {
        CalculateYesterdayStats();
        
        double balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double equity = AccountInfoDouble(ACCOUNT_EQUITY);
        
        notify.SendDailyReport(_Symbol, m_yesterdayProfit, m_yesterdaySwap, m_yesterdayCommission, 
                              m_yesterdayTradeCount, balance, equity);
        
        m_lastReportDate = iTime(_Symbol, PERIOD_D1, 0);
        
        PrintFormat("[Vegas] 每日财报已发送！");
    }
}

void CVegasDailyReport::OnTradeEvent(double profit, double swap, double commission)
{
}

void CVegasMultiSymbol::CVegasMultiSymbol()
{
    m_symbolCount = 0;
    m_useCurrentSymbol = true;
}

bool CVegasMultiSymbol::Init(string symbolList, bool useCurrentSymbol)
{
    m_useCurrentSymbol = useCurrentSymbol;
    
    if(useCurrentSymbol)
    {
        ArrayResize(m_symbols, 1);
        m_symbols[0] = _Symbol;
        m_symbolCount = 1;
        PrintFormat("[Vegas] 使用当前品种: %s", _Symbol);
        return true;
    }
    
    string symbols[];
    int count = StringSplit(symbolList, ',', symbols);
    
    if(count <= 0)
    {
        PrintFormat("[Vegas] 品种列表解析失败！");
        return false;
    }
    
    ArrayResize(m_symbols, count);
    m_symbolCount = 0;
    
    for(int i = 0; i < count; i++)
    {
        string symbol = symbols[i];
        StringTrimLeft(symbol);
        StringTrimRight(symbol);
        
        if(SymbolSelect(symbol, true))
        {
            m_symbols[m_symbolCount] = symbol;
            m_symbolCount++;
            PrintFormat("[Vegas] 添加品种: %s", symbol);
        }
        else
        {
            PrintFormat("[Vegas] 无法添加品种: %s, Error: %d", symbol, GetLastError());
        }
    }
    
    if(m_symbolCount == 0)
    {
        PrintFormat("[Vegas] 没有有效品种！");
        return false;
    }
    
    ArrayResize(m_symbols, m_symbolCount);
    PrintFormat("[Vegas] 共加载 %d 个品种", m_symbolCount);
    
    return true;
}

int CVegasMultiSymbol::GetSymbolCount()
{
    return m_symbolCount;
}

string CVegasMultiSymbol::GetSymbol(int index)
{
    if(index < 0 || index >= m_symbolCount) return "";
    return m_symbols[index];
}

bool CVegasMultiSymbol::IsValidSymbol(string symbol)
{
    for(int i = 0; i < m_symbolCount; i++)
    {
        if(m_symbols[i] == symbol) return true;
    }
    return false;
}

int GetTotalOpenPositions()
{
    int count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
        count++;
    }
    return count;
}

bool CheckTradeTime()
{
    MqlDateTime dt;
    TimeCurrent(dt);
    
    if(dt.day_of_week == 0 || dt.day_of_week == 6)
    {
        return false;
    }
    
    if(dt.hour < InpTradeStartHour || dt.hour > InpTradeEndHour)
    {
        return false;
    }
    
    return true;
}

bool CheckSpread(string symbol)
{
    long spreadValue = SymbolInfoInteger(symbol, SYMBOL_SPREAD);
    return spreadValue <= InpMaxSpreadPoints;
}

void FridayCloseAll()
{
    if(!InpCloseOnFriday) return;
    
    MqlDateTime dt;
    TimeCurrent(dt);
    
    if(dt.day_of_week == 5 && dt.hour >= InpFridayCloseHour)
    {
        if(!g_fridayClosed)
        {
            for(int i = 0; i < g_multiSymbol.GetSymbolCount(); i++)
            {
                string symbol = g_multiSymbol.GetSymbol(i);
                g_vegasPositionMgr[i].CloseAllPositions("周五收盘平仓");
            }
            
            g_fridayClosed = true;
            g_fridayCloseTime = TimeCurrent();
            
            g_vegasNotify.SendAlert("[Vegas H4] 周五收盘，所有仓位已平仓！");
            PrintFormat("[Vegas] 周五收盘平仓完成！");
        }
    }
    else if(dt.day_of_week != 5)
    {
        g_fridayClosed = false;
    }
}

bool IsNewBar(string symbol, int symbolIndex)
{
    datetime currentBarTime = iTime(symbol, PERIOD_H4, 0);
    
    if(currentBarTime == 0) return false;
    
    if(currentBarTime != g_lastBarTime[symbolIndex])
    {
        g_lastBarTime[symbolIndex] = currentBarTime;
        return true;
    }
    
    return false;
}

int OnInit()
{
    PrintFormat("========================================");
    PrintFormat("[Vegas H4 Trae1.0] 初始化开始...");
    PrintFormat("========================================");
    
    if(!g_multiSymbol.Init(InpSymbolList, InpUseCurrentSymbol))
    {
        PrintFormat("[Vegas] 多品种模块初始化失败！");
        return INIT_FAILED;
    }
    
    int symbolCount = g_multiSymbol.GetSymbolCount();
    
    ArrayResize(g_vegasChannel, symbolCount);
    ArrayResize(g_vegasRisk, symbolCount);
    ArrayResize(g_vegasPositionMgr, symbolCount);
    ArrayResize(g_lastBarTime, symbolCount);
    
    for(int i = 0; i < symbolCount; i++)
    {
        g_lastBarTime[i] = 0;
    }
    
    for(int i = 0; i < symbolCount; i++)
    {
        string symbol = g_multiSymbol.GetSymbol(i);
        
        int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        
        if(!g_vegasChannel[i].Init(symbol, PERIOD_H4))
        {
            PrintFormat("[Vegas] %s 通道初始化失败！", symbol);
            return INIT_FAILED;
        }
        
        if(!g_vegasRisk[i].Init(symbol, digits, point, InpMagicNumber))
        {
            PrintFormat("[Vegas] %s 风控初始化失败！", symbol);
            return INIT_FAILED;
        }
        
        if(!g_vegasPositionMgr[i].Init(symbol, InpMagicNumber, point, digits))
        {
            PrintFormat("[Vegas] %s 仓位管理器初始化失败！", symbol);
            return INIT_FAILED;
        }
    }
    
    g_vegasNotify.Init(InpEnableNotification);
    g_dailyReport.Init(InpReportHourGMT8);
    
    g_trade.SetExpertMagicNumber(InpMagicNumber);
    
    PrintFormat("========================================");
    PrintFormat("[Vegas H4 Trae1.0] 初始化完成！");
    PrintFormat("品种数量: %d", symbolCount);
    PrintFormat("时间框架: H4");
    PrintFormat("EMA快速周期: %d", InpEmaFastPeriod);
    PrintFormat("EMA慢速周期: %d", InpEmaSlowPeriod);
    PrintFormat("信号EMA周期: %d", InpSignalEmaPeriod);
    PrintFormat("风险百分比: %.2f%%", InpRiskPercent);
    PrintFormat("每日亏损限额: %.2f%%", InpDailyLossLimit);
    PrintFormat("手机推送: %s", InpEnableNotification ? "启用" : "禁用");
    PrintFormat("每日财报: %s", InpEnableDailyReport ? "启用" : "禁用");
    PrintFormat("========================================");
    
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
    PrintFormat("[Vegas H4 Trae1.0] 卸载完成！Reason: %d", reason);
}

void OnTick()
{
    if(!TerminalInfoInteger(TERMINAL_CONNECTED))
    {
        return;
    }
    
    static datetime lastDate = 0;
    datetime currentDate = iTime(_Symbol, PERIOD_D1, 0);
    if(currentDate != 0 && currentDate != lastDate)
    {
        lastDate = currentDate;
        g_equityProtectionTriggered = false;
    }
    
    if(g_equityProtectionTriggered)
    {
        return;
    }
    
    // 全局权益保护检查
    for(int i = 0; i < g_multiSymbol.GetSymbolCount(); i++)
    {
        if(g_vegasRisk[i].CheckEquityProtection())
        {
            for(int j = 0; j < g_multiSymbol.GetSymbolCount(); j++)
            {
                g_vegasPositionMgr[j].CloseAllPositions("账户权益保护");
            }
            g_equityProtectionTriggered = true;
            g_vegasNotify.SendAlert("[Vegas H4] 账户权益保护触发，EA已停止交易！");
            return;
        }
    }
    
    FridayCloseAll();
    
    for(int i = 0; i < g_multiSymbol.GetSymbolCount(); i++)
    {
        g_vegasRisk[i].ResetDailyCounters();
    }
    
    g_dailyReport.CheckAndSendReport(g_vegasNotify);
    
    for(int i = 0; i < g_multiSymbol.GetSymbolCount(); i++)
    {
        string symbol = g_multiSymbol.GetSymbol(i);
        
        if(g_vegasRisk[i].CheckDailyLossLimit())
        {
            continue;
        }
        
        if(g_vegasRisk[i].CheckMaxDailyTrades())
        {
            continue;
        }
        
        double atrValue = g_vegasChannel[i].GetCurrentAtr();
        
        g_vegasPositionMgr[i].ManagePositions(atrValue);
        
        if(!IsNewBar(symbol, i))
        {
            continue;
        }
        
        if(!CheckTradeTime())
        {
            continue;
        }
        
        if(!CheckSpread(symbol))
        {
            continue;
        }
        
        if(GetTotalOpenPositions() >= InpMaxTotalPositions)
        {
            continue;
        }
        
        if(g_vegasPositionMgr[i].HasOpenPosition())
        {
            continue;
        }
        
        ENUM_VEGAS_SIGNAL signal = g_vegasChannel[i].GetSignal();
        
        if(signal == VEGAS_SIGNAL_NONE)
        {
            continue;
        }
        
        ENUM_POSITION_TYPE posType = (signal == VEGAS_SIGNAL_BUY) ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
        
        double slDistance = g_vegasRisk[i].CalculateSLDistance(atrValue);
        double tpDistance = g_vegasRisk[i].CalculateTPDistance(atrValue);
        
        double lots = g_vegasRisk[i].CalculateLotSize(slDistance, posType);
        
        if(lots <= 0)
        {
            PrintFormat("[Vegas] %s 手数计算失败！", symbol);
            continue;
        }
        
        double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
        double openPrice = (posType == POSITION_TYPE_BUY) ? ask : bid;
        
        double sl = 0, tp = 0;
        
        if(posType == POSITION_TYPE_BUY)
        {
            sl = NormalizeDouble(openPrice - slDistance, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
            tp = NormalizeDouble(openPrice + tpDistance, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
        }
        else
        {
            sl = NormalizeDouble(openPrice + slDistance, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
            tp = NormalizeDouble(openPrice - tpDistance, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
        }
        
        if(g_vegasPositionMgr[i].OpenPosition(posType, lots, sl, tp, InpTradeComment))
        {
            g_vegasRisk[i].IncrementTradeCount();
            g_vegasNotify.SendOpenNotification(symbol, posType, lots, openPrice, sl, tp);
        }
    }
}

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
    if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
    {
        ulong dealTicket = trans.deal;
        
        if(HistoryDealSelect(dealTicket))
        {
            ENUM_DEAL_TYPE dealType = (ENUM_DEAL_TYPE)HistoryDealGetInteger(dealTicket, DEAL_TYPE);
            ENUM_DEAL_ENTRY dealEntry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
            
            if(dealEntry == DEAL_ENTRY_OUT)
            {
                string symbol = HistoryDealGetString(dealTicket, DEAL_SYMBOL);
                double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
                double volume = HistoryDealGetDouble(dealTicket, DEAL_VOLUME);
                
                ENUM_POSITION_TYPE posType;
                if(dealType == DEAL_TYPE_SELL)
                    posType = POSITION_TYPE_BUY;
                else
                    posType = POSITION_TYPE_SELL;
                
                string reason = "手动平仓";
                
                if(profit < 0)
                {
                    reason = "止损出场";
                    if(InpNotifyOnSL)
                    {
                        g_vegasNotify.SendCloseNotification(symbol, posType, volume, profit, reason);
                    }
                }
                else if(profit > 0)
                {
                    reason = "止盈出场";
                    if(InpNotifyOnTP)
                    {
                        g_vegasNotify.SendCloseNotification(symbol, posType, volume, profit, reason);
                    }
                }
                else
                {
                    if(InpNotifyOnClose)
                    {
                        g_vegasNotify.SendCloseNotification(symbol, posType, volume, profit, reason);
                    }
                }
            }
        }
    }
}
