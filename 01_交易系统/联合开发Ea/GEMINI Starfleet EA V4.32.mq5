#property copyright "GEMINI Starfleet EA V4.32"
#property link      ""
#property version   "4.32"
#property strict

#include <Trade\Trade.mqh>

input double   InpRiskPercent       = 2.0;
input double   InpDailyDrawdownLimit = 3.0;
input int      InpAtrPeriod         = 14;
input double   InpAtrMultiplier     = 2.0;
input double   InpAtrDeadZone       = 0.5;
input int      InpDonchianPeriod    = 20;
input double   InpAdxThreshold      = 25.0;
input int      InpRsiPeriod         = 14;
input int      InpRsiOverbought     = 70;
input int      InpRsiOversold       = 30;
input bool     InpEnablePyramid     = true;
input int      InpMaxPositions      = 3;
input int      InpMagicNumber       = 20250416;
input double   InpMaxSpreadMultiplier = 3.0;
input int      InpTradeStartHour    = 1;
input int      InpTradeEndHour      = 22;
input bool     InpCloseOnFriday     = true;
input int      InpFridayCloseHour   = 21;

class CStarfleetSignal
{
private:
    int      m_handleRsi;
    int      m_handleAtr;
    int      m_handleAdx;
    string   m_symbol;
    datetime m_lastSilentLogTime;
    bool     m_hasSignalCandidate;
    double   m_prevHigh;
    double   m_prevLow;
    
    bool CheckDonchianBreakout(bool &isBuySignal);
    bool CheckRsiFilter(bool isBuySignal);
    bool CheckAtrFilter();
    bool CheckAdxFilter(bool isBuySignal);
    double GetCurrentAdx();
    double GetHighestHigh(int period);
    double GetLowestLow(int period);
    
public:
    void     CStarfleetSignal();
    void    ~CStarfleetSignal();
    bool     Init(string symbol);
    bool     GenerateSignal(bool &isBuySignal);
    double   GetCurrentAtr();
    bool     IsTrendExhausted();
};

class CStarfleetRisk
{
private:
    string   m_symbol;
    int      m_digits;
    double   m_point;
    double   m_dailyStartEquity;
    int      m_atrPeriod;
    int      m_handleAtr;
    int      m_magic;
    datetime m_sleepEndTime;
    datetime m_lastSleepLogTime;
    
public:
    void     CStarfleetRisk();
    bool     Init(string symbol, int digits, double point, int atrPeriod, int magic);
    double   CalculateDynamicSL(double atrValue, double multiplier);
    double   CalculateLotSize(double slPoints, double riskPercent);
    bool     CheckDailyEquityProtection(double limitPercent);
    void     ResetDailyEquity();
    int      GetTodayLossCount();
    bool     IsInSleepMode();
    void     CheckAndSetSleepMode();
};

class CStarfleetPositionManager
{
private:
    string   m_symbol;
    int      m_magic;
    double   m_point;
    int      m_digits;
    CTrade   m_trade;
    bool     m_l1BreakevenDone;
    bool     m_l3Active;
    double   m_lastSyncedSL;
    bool     m_l1PartialClosed;
    bool     m_l2PartialClosed;
    
    int      GetPositionCount(ENUM_POSITION_TYPE posType);
    bool     GetPositionByLayer(ENUM_POSITION_TYPE posType, int layer, ulong &ticket, double &openPrice, double &openVolume);
    bool     GetLastPositionInfo(ENUM_POSITION_TYPE posType, double &openPrice, double &openVolume, double &currentProfit);
    double   CalculatePyramidRisk(int layer);
    double   CalculatePyramidTriggerATR(int layer);
    bool     SyncStopLoss(ENUM_POSITION_TYPE posType, int newLayer, double atrValue);
    bool     MoveToBreakeven(ulong ticket, double targetPrice);
    double   GetPositionProfitDistance(ENUM_POSITION_TYPE posType, int layer, double atrValue);
    bool     CheckL1BreakevenTrigger(double atrValue, ENUM_POSITION_TYPE posType);
    bool     ExecuteL1Breakeven(double atrValue, ENUM_POSITION_TYPE posType);
    double   CalculateAtrStopLoss(double atrValue, ENUM_POSITION_TYPE posType, double currentPrice);
    void     ChandelierExit(double atrValue, bool emergencyMode = false);
    bool     CheckPartialCloseTrigger(int layer, double atrValue, ENUM_POSITION_TYPE posType);
    bool     ExecutePartialClose(int layer, double atrValue, ENUM_POSITION_TYPE posType);
    void     CheckAndExecutePartialClose(double atrValue, ENUM_POSITION_TYPE posType);
    
public:
    void     CStarfleetPositionManager();
    bool     Init(string symbol, int magic, double point, int digits);
    bool     ManagePyramid(double atrValue, bool isBuy);
    bool     CheckPyramidTrigger(double atrValue, bool isBuy);
    bool     ExecutePyramid(double atrValue, bool isBuy);
    void     UpdateAtrStops(double atrValue);
};

class CStarfleetExecutor
{
private:
    CTrade   m_trade;
    string   m_symbol;
    int      m_digits;
    double   m_point;
    int      m_magic;
    double   m_spreadHistory[];
    int      m_spreadCount;
    
    bool     CheckFreeMargin(double lots, ENUM_POSITION_TYPE posType);
    bool     CheckSpread(double maxMultiplier);
    double   GetAvgSpread(int bars);
    
public:
    void     CStarfleetExecutor();
    bool     Init(string symbol, int digits, double point, int magic);
    bool     OpenPosition(ENUM_POSITION_TYPE posType, double lots, double sl, double tp, string comment);
    bool     ClosePosition(ulong ticket);
    bool     ModifyPosition(ulong ticket, double sl, double tp);
    void     CloseAllPositions();
    void     UpdateSpreadHistory();
};

CTrade              g_trade;
string              g_symbol         = _Symbol;
int                 g_digits         = 0;
double              g_point          = 0.0;
CStarfleetSignal    g_signal;
CStarfleetRisk      g_risk;
CStarfleetPositionManager g_positionMgr;
CStarfleetExecutor  g_executor;
bool                g_fridayClosed   = false;
datetime            g_fridayCloseTime = 0;
datetime            g_lastBarTime    = 0;

void CStarfleetSignal::CStarfleetSignal()
{
    m_handleRsi = INVALID_HANDLE;
    m_handleAtr = INVALID_HANDLE;
    m_handleAdx = INVALID_HANDLE;
    m_symbol = "";
    m_lastSilentLogTime = 0;
    m_hasSignalCandidate = false;
    m_prevHigh = 0;
    m_prevLow = 0;
}

void CStarfleetSignal::~CStarfleetSignal()
{
    if(m_handleRsi != INVALID_HANDLE) IndicatorRelease(m_handleRsi);
    if(m_handleAtr != INVALID_HANDLE) IndicatorRelease(m_handleAtr);
    if(m_handleAdx != INVALID_HANDLE) IndicatorRelease(m_handleAdx);
}

bool CStarfleetSignal::Init(string symbol)
{
    m_symbol = symbol;
    
    m_handleRsi = iRSI(m_symbol, PERIOD_CURRENT, InpRsiPeriod, PRICE_CLOSE);
    if(m_handleRsi == INVALID_HANDLE) return false;
    
    m_handleAtr = iATR(m_symbol, PERIOD_CURRENT, InpAtrPeriod);
    if(m_handleAtr == INVALID_HANDLE) return false;
    
    m_handleAdx = iADX(m_symbol, PERIOD_CURRENT, 14);
    if(m_handleAdx == INVALID_HANDLE) return false;
    
    return true;
}

double CStarfleetSignal::GetHighestHigh(int period)
{
    double high[];
    ArraySetAsSeries(high, true);
    
    if(CopyHigh(m_symbol, PERIOD_CURRENT, 1, period, high) < period)
        return 0;
    
    double highestHigh = high[0];
    for(int i = 1; i < period; i++)
    {
        if(high[i] > highestHigh)
            highestHigh = high[i];
    }
    
    return highestHigh;
}

double CStarfleetSignal::GetLowestLow(int period)
{
    double low[];
    ArraySetAsSeries(low, true);
    
    if(CopyLow(m_symbol, PERIOD_CURRENT, 1, period, low) < period)
        return 0;
    
    double lowestLow = low[0];
    for(int i = 1; i < period; i++)
    {
        if(low[i] < lowestLow)
            lowestLow = low[i];
    }
    
    return lowestLow;
}

bool CStarfleetSignal::CheckDonchianBreakout(bool &isBuySignal)
{
    double highestHigh = GetHighestHigh(InpDonchianPeriod);
    double lowestLow = GetLowestLow(InpDonchianPeriod);
    
    if(highestHigh == 0 || lowestLow == 0)
        return false;
    
    double currentAsk = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    double currentBid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
    
    if(currentAsk <= 0 || currentBid <= 0)
        return false;
    
    static datetime lastBreakoutLogTime = 0;
    
    if(currentAsk > highestHigh)
    {
        isBuySignal = true;
        m_prevHigh = highestHigh;
        if(TimeCurrent() - lastBreakoutLogTime >= 60)
        {
            PrintFormat("[GEMINI] 唐奇安向上突破！Ask:%.5f > 最高价%.5f", currentAsk, highestHigh);
            lastBreakoutLogTime = TimeCurrent();
        }
        return true;
    }
    else if(currentBid < lowestLow)
    {
        isBuySignal = false;
        m_prevLow = lowestLow;
        if(TimeCurrent() - lastBreakoutLogTime >= 60)
        {
            PrintFormat("[GEMINI] 唐奇安向下突破！Bid:%.5f < 最低价%.5f", currentBid, lowestLow);
            lastBreakoutLogTime = TimeCurrent();
        }
        return true;
    }
    
    return false;
}

bool CStarfleetSignal::CheckRsiFilter(bool isBuySignal)
{
    double rsi[];
    ArraySetAsSeries(rsi, true);
    
    if(CopyBuffer(m_handleRsi, 0, 0, 2, rsi) < 2) return false;
    
    if(isBuySignal)
    {
        return rsi[1] < InpRsiOverbought;
    }
    else
    {
        return rsi[1] > InpRsiOversold;
    }
}

bool CStarfleetSignal::CheckAtrFilter()
{
    double atrCurrent[], atrHistory[];
    ArraySetAsSeries(atrCurrent, true);
    ArraySetAsSeries(atrHistory, true);
    
    if(CopyBuffer(m_handleAtr, 0, 0, 1, atrCurrent) < 1) return false;
    if(CopyBuffer(m_handleAtr, 0, 0, 21, atrHistory) < 21) return false;
    
    double atrAvg = 0;
    for(int i = 1; i <= 20; i++)
    {
        atrAvg += atrHistory[i];
    }
    atrAvg /= 20;
    
    if(atrCurrent[0] < atrAvg * InpAtrDeadZone)
    {
        PrintFormat("[GEMINI] ATR死水过滤：当前ATR %.5f < 平均ATR %.5f × %.1f", atrCurrent[0], atrAvg, InpAtrDeadZone);
        return false;
    }
    
    return true;
}

bool CStarfleetSignal::CheckAdxFilter(bool isBuySignal)
{
    double adx[], diPlus[], diMinus[];
    ArraySetAsSeries(adx, true);
    ArraySetAsSeries(diPlus, true);
    ArraySetAsSeries(diMinus, true);
    
    if(CopyBuffer(m_handleAdx, 0, 0, 2, adx) < 2) return false;
    if(CopyBuffer(m_handleAdx, 1, 0, 2, diPlus) < 2) return false;
    if(CopyBuffer(m_handleAdx, 2, 0, 2, diMinus) < 2) return false;
    
    if(adx[1] < InpAdxThreshold)
    {
        if(m_hasSignalCandidate)
        {
            datetime currentTime = TimeCurrent();
            if(currentTime - m_lastSilentLogTime >= 3600)
            {
                PrintFormat("[GEMINI] 雷达静默：当前ADX未达%.1f门槛，正在扫描强趋势信号... ADX=%.2f", InpAdxThreshold, adx[1]);
                m_lastSilentLogTime = currentTime;
            }
        }
        return false;
    }
    
    if(isBuySignal)
    {
        if(diPlus[1] <= diMinus[1])
        {
            if(m_hasSignalCandidate)
            {
                datetime currentTime = TimeCurrent();
                if(currentTime - m_lastSilentLogTime >= 3600)
                {
                    PrintFormat("[GEMINI] 雷达静默：方向未共振，DI+=%.2f <= DI-=%.2f", diPlus[1], diMinus[1]);
                    m_lastSilentLogTime = currentTime;
                }
            }
            return false;
        }
    }
    else
    {
        if(diMinus[1] <= diPlus[1])
        {
            if(m_hasSignalCandidate)
            {
                datetime currentTime = TimeCurrent();
                if(currentTime - m_lastSilentLogTime >= 3600)
                {
                    PrintFormat("[GEMINI] 雷达静默：方向未共振，DI-=%.2f <= DI+=%.2f", diMinus[1], diPlus[1]);
                    m_lastSilentLogTime = currentTime;
                }
            }
            return false;
        }
    }
    
    PrintFormat("[GEMINI] ADX阀门开启！ADX=%.2f >= %.1f，方向共振确认", adx[1], InpAdxThreshold);
    return true;
}

double CStarfleetSignal::GetCurrentAdx()
{
    double adx[];
    ArraySetAsSeries(adx, true);
    
    if(CopyBuffer(m_handleAdx, 0, 0, 1, adx) < 1)
        return 0;
    
    return adx[0];
}

bool CStarfleetSignal::IsTrendExhausted()
{
    double adx = GetCurrentAdx();
    
    if(adx > 0 && adx < 15)
    {
        PrintFormat("[GEMINI] 趋势动能枯竭！ADX=%.2f < 15，进入紧急落袋模式", adx);
        return true;
    }
    
    return false;
}

bool CStarfleetSignal::GenerateSignal(bool &isBuySignal)
{
    m_hasSignalCandidate = false;
    
    if(!CheckDonchianBreakout(isBuySignal))
        return false;
    
    if(!CheckRsiFilter(isBuySignal))
        return false;
    
    if(!CheckAtrFilter())
        return false;
    
    m_hasSignalCandidate = true;
    
    if(!CheckAdxFilter(isBuySignal))
        return false;
    
    return true;
}

double CStarfleetSignal::GetCurrentAtr()
{
    double atr[];
    ArraySetAsSeries(atr, true);
    
    if(CopyBuffer(m_handleAtr, 0, 0, 1, atr) < 1)
        return 0;
    
    return atr[0];
}

void CStarfleetRisk::CStarfleetRisk()
{
    m_symbol = "";
    m_digits = 0;
    m_point = 0;
    m_dailyStartEquity = 0;
    m_atrPeriod = 14;
    m_handleAtr = INVALID_HANDLE;
    m_magic = 0;
    m_sleepEndTime = 0;
    m_lastSleepLogTime = 0;
}

bool CStarfleetRisk::Init(string symbol, int digits, double point, int atrPeriod, int magic)
{
    m_symbol = symbol;
    m_digits = digits;
    m_point = point;
    m_atrPeriod = atrPeriod;
    m_magic = magic;
    m_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    m_sleepEndTime = 0;
    m_lastSleepLogTime = 0;
    
    m_handleAtr = iATR(m_symbol, PERIOD_CURRENT, m_atrPeriod);
    if(m_handleAtr == INVALID_HANDLE) return false;
    
    return true;
}

double CStarfleetRisk::CalculateDynamicSL(double atrValue, double multiplier)
{
    if(atrValue <= 0) return 0;
    
    double slDistance = atrValue * multiplier;
    double slPoints = slDistance / m_point;
    
    return slPoints;
}

double CStarfleetRisk::CalculateLotSize(double slPoints, double riskPercent)
{
    if(slPoints <= 0)
    {
        Print("[GEMINI] 动态止损为0，取消开仓！");
        return 0;
    }
    
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(equity <= 0)
    {
        Print("[GEMINI] 账户净值异常！");
        return 0;
    }
    
    double riskAmount = equity * (riskPercent / 100.0);
    
    double askPrice = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    if(askPrice == 0) return 0;
    
    double slPrice = askPrice - (slPoints * m_point);
    slPrice = NormalizeDouble(slPrice, m_digits);
    
    double lossForOneLot = 0;
    if(!OrderCalcProfit(ORDER_TYPE_BUY, m_symbol, 1.0, askPrice, slPrice, lossForOneLot))
    {
        PrintFormat("[GEMINI] OrderCalcProfit失败！错误码: %d", GetLastError());
        return 0;
    }
    
    double riskPerLot = MathAbs(lossForOneLot);
    if(riskPerLot <= 0)
    {
        Print("[GEMINI] 每手风险计算为0！");
        return 0;
    }
    
    double finalLot = riskAmount / riskPerLot;
    
    double minLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);
    
    if(minLot <= 0) minLot = 0.01;
    if(maxLot <= 0) maxLot = 100.0;
    if(lotStep <= 0) lotStep = 0.01;
    
    PrintFormat(">>> [X光雷达] 风险预算:$%.2f | 1手亏损:$%.2f | 理论手数:%.5f | 平台限额:[%.2f-%.2f] | 步长:%.2f", 
                riskAmount, riskPerLot, finalLot, minLot, maxLot, lotStep);
    
    if(finalLot < minLot)
    {
        PrintFormat("[GEMINI] 手数%.5f < 最小%.2f，调整为最小值", finalLot, minLot);
        finalLot = minLot;
    }
    else if(finalLot > maxLot)
    {
        PrintFormat("[GEMINI] 手数%.5f > 最大%.2f，调整为最大值", finalLot, maxLot);
        finalLot = maxLot;
    }
    
    finalLot = MathFloor(finalLot / lotStep) * lotStep;
    
    if(finalLot < minLot)
        finalLot = minLot;
    
    if(maxLot > 0 && finalLot > maxLot)
    {
        PrintFormat("[GEMINI] 手数%.5f超过平台最大限制%.2f，强制截断！", finalLot, maxLot);
        finalLot = maxLot;
    }
    
    return finalLot;
}

bool CStarfleetRisk::CheckDailyEquityProtection(double limitPercent)
{
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double drawdown = (m_dailyStartEquity - currentEquity) / m_dailyStartEquity * 100.0;
    
    if(drawdown >= limitPercent)
    {
        PrintFormat("[GEMINI] 每日熔断触发！当日回撤: %.2f%% >= 限额: %.2f%%", drawdown, limitPercent);
        return true;
    }
    
    return false;
}

void CStarfleetRisk::ResetDailyEquity()
{
    m_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
}

int CStarfleetRisk::GetTodayLossCount()
{
    datetime dayStart = iTime(m_symbol, PERIOD_D1, 0);
    if(dayStart == 0) return 0;
    
    if(!HistorySelect(dayStart, TimeCurrent())) return 0;
    
    int lossCount = 0;
    int totalDeals = HistoryDealsTotal();
    
    for(int i = 0; i < totalDeals; i++)
    {
        ulong dealTicket = HistoryDealGetTicket(i);
        if(dealTicket == 0) continue;
        
        if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) != m_symbol) continue;
        if(HistoryDealGetInteger(dealTicket, DEAL_MAGIC) != m_magic) continue;
        
        ENUM_DEAL_ENTRY dealEntry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
        if(dealEntry != DEAL_ENTRY_OUT) continue;
        
        double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
        if(profit < 0)
        {
            lossCount++;
        }
    }
    
    return lossCount;
}

bool CStarfleetRisk::IsInSleepMode()
{
    if(TimeCurrent() < m_sleepEndTime)
    {
        datetime currentTime = TimeCurrent();
        if(currentTime - m_lastSleepLogTime >= 3600)
        {
            int remainingHours = (int)((m_sleepEndTime - currentTime) / 3600);
            PrintFormat("[GEMINI] 系统休眠中...连续止损保护，剩余%d小时", remainingHours);
            m_lastSleepLogTime = currentTime;
        }
        return true;
    }
    return false;
}

void CStarfleetRisk::CheckAndSetSleepMode()
{
    int lossCount = GetTodayLossCount();
    
    if(lossCount >= 2 && m_sleepEndTime == 0)
    {
        m_sleepEndTime = TimeCurrent() + 12 * 3600;
        PrintFormat("[GEMINI] 连续止损%d次触发！系统进入12小时休眠期...", lossCount);
    }
}

void CStarfleetPositionManager::CStarfleetPositionManager()
{
    m_symbol = "";
    m_magic = 0;
    m_point = 0;
    m_digits = 0;
    m_l1BreakevenDone = false;
    m_l3Active = false;
    m_lastSyncedSL = 0;
    m_l1PartialClosed = false;
    m_l2PartialClosed = false;
}

bool CStarfleetPositionManager::Init(string symbol, int magic, double point, int digits)
{
    m_symbol = symbol;
    m_magic = magic;
    m_point = point;
    m_digits = digits;
    m_l1BreakevenDone = false;
    m_l3Active = false;
    m_lastSyncedSL = 0;
    m_l1PartialClosed = false;
    m_l2PartialClosed = false;
    m_trade.SetExpertMagicNumber(m_magic);
    return true;
}

int CStarfleetPositionManager::GetPositionCount(ENUM_POSITION_TYPE posType)
{
    int count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        if(PositionGetInteger(POSITION_TYPE) != posType) continue;
        count++;
    }
    return count;
}

bool CStarfleetPositionManager::GetPositionByLayer(ENUM_POSITION_TYPE posType, int layer, ulong &ticket, double &openPrice, double &openVolume)
{
    ticket = 0;
    openPrice = 0;
    openVolume = 0;
    
    datetime times[];
    ulong tickets[];
    int total = 0;
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong t = PositionGetTicket(i);
        if(t == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        if(PositionGetInteger(POSITION_TYPE) != posType) continue;
        
        total++;
        ArrayResize(times, total);
        ArrayResize(tickets, total);
        times[total - 1] = (datetime)PositionGetInteger(POSITION_TIME);
        tickets[total - 1] = t;
    }
    
    for(int i = 0; i < total - 1; i++)
    {
        for(int j = i + 1; j < total; j++)
        {
            if(times[i] > times[j])
            {
                datetime tempTime = times[i];
                times[i] = times[j];
                times[j] = tempTime;
                
                ulong tempTicket = tickets[i];
                tickets[i] = tickets[j];
                tickets[j] = tempTicket;
            }
        }
    }
    
    if(layer > 0 && layer <= total)
    {
        ticket = tickets[layer - 1];
        if(PositionSelectByTicket(ticket))
        {
            openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            openVolume = PositionGetDouble(POSITION_VOLUME);
            return true;
        }
    }
    
    return false;
}

bool CStarfleetPositionManager::GetLastPositionInfo(ENUM_POSITION_TYPE posType, double &openPrice, double &openVolume, double &currentProfit)
{
    openPrice = 0;
    openVolume = 0;
    currentProfit = 0;
    datetime lastTime = 0;
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        if(PositionGetInteger(POSITION_TYPE) != posType) continue;
        
        datetime posTime = (datetime)PositionGetInteger(POSITION_TIME);
        if(posTime > lastTime)
        {
            lastTime = posTime;
            openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            openVolume = PositionGetDouble(POSITION_VOLUME);
            currentProfit = PositionGetDouble(POSITION_PROFIT);
        }
    }
    
    return lastTime > 0;
}

double CStarfleetPositionManager::CalculatePyramidRisk(int layer)
{
    switch(layer)
    {
        case 1: return InpRiskPercent;
        case 2: return InpRiskPercent * 0.5;
        case 3: return InpRiskPercent * 0.25;
        default: return 0;
    }
}

double CStarfleetPositionManager::CalculatePyramidTriggerATR(int layer)
{
    switch(layer)
    {
        case 2: return 1.5;
        case 3: return 1.0;
        default: return 0;
    }
}

double CStarfleetPositionManager::GetPositionProfitDistance(ENUM_POSITION_TYPE posType, int layer, double atrValue)
{
    ulong ticket = 0;
    double openPrice = 0, openVolume = 0;
    
    if(!GetPositionByLayer(posType, layer, ticket, openPrice, openVolume))
        return 0;
    
    double currentPrice = (posType == POSITION_TYPE_BUY) ? 
                          SymbolInfoDouble(m_symbol, SYMBOL_BID) : 
                          SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    
    double distance = (posType == POSITION_TYPE_BUY) ? 
                      (currentPrice - openPrice) : 
                      (openPrice - currentPrice);
    
    return distance;
}

bool CStarfleetPositionManager::MoveToBreakeven(ulong ticket, double targetPrice)
{
    if(!PositionSelectByTicket(ticket)) return false;
    
    ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    double currentSL = PositionGetDouble(POSITION_SL);
    double currentTP = PositionGetDouble(POSITION_TP);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    
    targetPrice = NormalizeDouble(targetPrice, m_digits);
    
    bool shouldMove = false;
    
    if(posType == POSITION_TYPE_BUY)
    {
        if(targetPrice > openPrice && (currentSL == 0 || targetPrice > currentSL))
            shouldMove = true;
    }
    else
    {
        if(targetPrice < openPrice && (currentSL == 0 || targetPrice < currentSL))
            shouldMove = true;
    }
    
    if(shouldMove)
    {
        m_trade.SetExpertMagicNumber(m_magic);
        return m_trade.PositionModify(ticket, targetPrice, currentTP);
    }
    
    return true;
}

bool CStarfleetPositionManager::CheckL1BreakevenTrigger(double atrValue, ENUM_POSITION_TYPE posType)
{
    ulong ticket = 0;
    double openPrice = 0, openVolume = 0;
    
    if(!GetPositionByLayer(posType, 1, ticket, openPrice, openVolume))
        return false;
    
    double profitDistance = GetPositionProfitDistance(posType, 1, atrValue);
    double requiredDistance = atrValue * 1.5;
    
    if(profitDistance >= requiredDistance)
    {
        PrintFormat("[GEMINI] L1保本触发！盈利距离:%.5f >= 要求:%.5f (1.5×ATR)", profitDistance, requiredDistance);
        return true;
    }
    
    return false;
}

bool CStarfleetPositionManager::ExecuteL1Breakeven(double atrValue, ENUM_POSITION_TYPE posType)
{
    ulong ticket = 0;
    double openPrice = 0, openVolume = 0;
    
    if(!GetPositionByLayer(posType, 1, ticket, openPrice, openVolume))
        return false;
    
    if(MoveToBreakeven(ticket, openPrice))
    {
        m_l1BreakevenDone = true;
        PrintFormat("[GEMINI] L1保本完成！止损已移至成本价 %.5f", openPrice);
        return true;
    }
    
    return false;
}

double CStarfleetPositionManager::CalculateAtrStopLoss(double atrValue, ENUM_POSITION_TYPE posType, double currentPrice)
{
    double sl = 0;
    
    if(posType == POSITION_TYPE_BUY)
    {
        sl = currentPrice - atrValue * InpAtrMultiplier;
    }
    else
    {
        sl = currentPrice + atrValue * InpAtrMultiplier;
    }
    
    return NormalizeDouble(sl, m_digits);
}

bool CStarfleetPositionManager::SyncStopLoss(ENUM_POSITION_TYPE posType, int newLayer, double atrValue)
{
    if(newLayer < 2) return false;
    
    double currentPrice = (posType == POSITION_TYPE_BUY) ? 
                          SymbolInfoDouble(m_symbol, SYMBOL_BID) : 
                          SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    
    double newSL = CalculateAtrStopLoss(atrValue, posType, currentPrice);
    
    for(int layer = 1; layer < newLayer; layer++)
    {
        ulong ticket = 0;
        double openPrice = 0, openVolume = 0;
        
        if(GetPositionByLayer(posType, layer, ticket, openPrice, openVolume))
        {
            if(!PositionSelectByTicket(ticket)) continue;
            
            double currentTP = PositionGetDouble(POSITION_TP);
            ENUM_POSITION_TYPE ticketPosType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            
            bool shouldModify = false;
            double currentSL = PositionGetDouble(POSITION_SL);
            
            if(ticketPosType == POSITION_TYPE_BUY)
            {
                if(newSL > openPrice && (currentSL == 0 || newSL > currentSL))
                    shouldModify = true;
            }
            else
            {
                if(newSL < openPrice && (currentSL == 0 || newSL < currentSL))
                    shouldModify = true;
            }
            
            if(shouldModify)
            {
                m_trade.SetExpertMagicNumber(m_magic);
                m_trade.PositionModify(ticket, newSL, currentTP);
            }
        }
    }
    
    PrintFormat("[GEMINI] ATR止损同步完成！L%d成交，L1-L%d止损已统一至ATR阶梯", newLayer, newLayer - 1);
    return true;
}

void CStarfleetPositionManager::ChandelierExit(double atrValue, bool emergencyMode = false)
{
    double atrMultiplier = emergencyMode ? 1.5 : InpAtrMultiplier;
    
    if(m_l1PartialClosed && !emergencyMode)
    {
        atrMultiplier = 3.0;
    }
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        
        ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        double currentSL = PositionGetDouble(POSITION_SL);
        double currentTP = PositionGetDouble(POSITION_TP);
        double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
        
        double currentPrice = (posType == POSITION_TYPE_BUY) ? 
                              SymbolInfoDouble(m_symbol, SYMBOL_BID) : 
                              SymbolInfoDouble(m_symbol, SYMBOL_ASK);
        
        double newSL = 0;
        if(posType == POSITION_TYPE_BUY)
        {
            newSL = currentPrice - atrValue * atrMultiplier;
        }
        else
        {
            newSL = currentPrice + atrValue * atrMultiplier;
        }
        newSL = NormalizeDouble(newSL, m_digits);
        
        bool shouldModify = false;
        
        if(posType == POSITION_TYPE_BUY)
        {
            if(newSL > openPrice && (currentSL == 0 || newSL > currentSL))
                shouldModify = true;
        }
        else
        {
            if(newSL < openPrice && (currentSL == 0 || newSL < currentSL))
                shouldModify = true;
        }
        
        if(shouldModify)
        {
            m_trade.SetExpertMagicNumber(m_magic);
            
            if(currentTP != 0)
            {
                m_trade.PositionModify(ticket, newSL, 0);
                if(emergencyMode)
                    PrintFormat("[GEMINI] 紧急落袋模式！ADX动能枯竭，止损收缩至ATR×1.5: %.5f", newSL);
                else if(m_l1PartialClosed)
                    PrintFormat("[GEMINI] 利润奔跑模式！L1分批止盈后，止损放宽至ATR×3.0: %.5f", newSL);
                else
                    PrintFormat("[GEMINI] 吊灯离场激活！移除TP，止损移至 %.5f", newSL);
            }
            else
            {
                m_trade.PositionModify(ticket, newSL, 0);
            }
        }
    }
}

bool CStarfleetPositionManager::CheckPartialCloseTrigger(int layer, double atrValue, ENUM_POSITION_TYPE posType)
{
    if(layer < 1 || layer > 2) return false;
    
    if(layer == 1 && m_l1PartialClosed) return false;
    if(layer == 2 && m_l2PartialClosed) return false;
    
    ulong ticket = 0;
    double openPrice = 0, openVolume = 0;
    
    if(!GetPositionByLayer(posType, layer, ticket, openPrice, openVolume))
        return false;
    
    double currentPrice = (posType == POSITION_TYPE_BUY) ? 
                          SymbolInfoDouble(m_symbol, SYMBOL_BID) : 
                          SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    
    double profitDistance = (posType == POSITION_TYPE_BUY) ? 
                            (currentPrice - openPrice) : 
                            (openPrice - currentPrice);
    
    double requiredDistance = atrValue * 1.5;
    
    if(profitDistance >= requiredDistance)
    {
        PrintFormat("[GEMINI] L%d分批止盈触发！盈利距离:%.5f >= 要求:%.5f (1.5×ATR)", 
                    layer, profitDistance, requiredDistance);
        return true;
    }
    
    return false;
}

bool CStarfleetPositionManager::ExecutePartialClose(int layer, double atrValue, ENUM_POSITION_TYPE posType)
{
    ulong ticket = 0;
    double openPrice = 0, openVolume = 0;
    
    if(!GetPositionByLayer(posType, layer, ticket, openPrice, openVolume))
        return false;
    
    double closeVolume = NormalizeDouble(openVolume * 0.5, 2);
    double minLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
    
    if(closeVolume < minLot)
    {
        PrintFormat("[GEMINI] L%d分批止盈失败！剩余手数%.5f < 最小手数%.2f", layer, closeVolume, minLot);
        return false;
    }
    
    m_trade.SetExpertMagicNumber(m_magic);
    
    bool result = m_trade.PositionClose(ticket, closeVolume);
    
    if(result)
    {
        PrintFormat("[GEMINI] L%d分批止盈成功！平仓50%% (%.5f手)，剩余%.5f手继续博弈大趋势！", 
                    layer, closeVolume, openVolume - closeVolume);
        
        if(layer == 1)
        {
            m_l1PartialClosed = true;
            if(!m_l1BreakevenDone)
            {
                if(MoveToBreakeven(ticket, openPrice))
                {
                    m_l1BreakevenDone = true;
                    PrintFormat("[GEMINI] L1止损同步推至保本价 %.5f", openPrice);
                }
            }
        }
        else if(layer == 2)
        {
            m_l2PartialClosed = true;
        }
        
        return true;
    }
    else
    {
        PrintFormat("[GEMINI] L%d分批止盈失败！错误码:%d", layer, GetLastError());
        return false;
    }
}

void CStarfleetPositionManager::CheckAndExecutePartialClose(double atrValue, ENUM_POSITION_TYPE posType)
{
    int posCount = GetPositionCount(posType);
    
    if(posCount >= 1)
    {
        if(!m_l1PartialClosed && CheckPartialCloseTrigger(1, atrValue, posType))
        {
            ExecutePartialClose(1, atrValue, posType);
        }
    }
    
    if(posCount >= 2)
    {
        if(!m_l2PartialClosed && CheckPartialCloseTrigger(2, atrValue, posType))
        {
            ExecutePartialClose(2, atrValue, posType);
        }
    }
}

void CStarfleetPositionManager::UpdateAtrStops(double atrValue)
{
    int buyCount = GetPositionCount(POSITION_TYPE_BUY);
    int sellCount = GetPositionCount(POSITION_TYPE_SELL);
    int totalPositions = buyCount + sellCount;
    
    if(totalPositions == 0)
    {
        m_l1BreakevenDone = false;
        m_l3Active = false;
        m_lastSyncedSL = 0;
        m_l1PartialClosed = false;
        m_l2PartialClosed = false;
        return;
    }
    
    if(buyCount > 0)
    {
        CheckAndExecutePartialClose(atrValue, POSITION_TYPE_BUY);
    }
    if(sellCount > 0)
    {
        CheckAndExecutePartialClose(atrValue, POSITION_TYPE_SELL);
    }
    
    if(g_signal.IsTrendExhausted())
    {
        ChandelierExit(atrValue, true);
        return;
    }
    
    if(buyCount >= InpMaxPositions || sellCount >= InpMaxPositions)
    {
        if(!m_l3Active)
        {
            m_l3Active = true;
            Print("[GEMINI] L3已激活，切换至吊灯离场模式，移除所有TP！");
        }
        
        ChandelierExit(atrValue, false);
        return;
    }
    
    m_l3Active = false;
}

bool CStarfleetPositionManager::CheckPyramidTrigger(double atrValue, bool isBuy)
{
    if(!InpEnablePyramid) return false;
    
    ENUM_POSITION_TYPE posType = isBuy ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
    int posCount = GetPositionCount(posType);
    
    if(posCount == 0 || posCount >= InpMaxPositions) return false;
    
    int nextLayer = posCount + 1;
    
    if(nextLayer == 2)
    {
        if(!m_l1BreakevenDone)
        {
            if(CheckL1BreakevenTrigger(atrValue, posType))
            {
                ExecuteL1Breakeven(atrValue, posType);
            }
            return false;
        }
    }
    
    double requiredATRMultiplier = CalculatePyramidTriggerATR(nextLayer);
    if(requiredATRMultiplier <= 0) return false;
    
    double requiredDistance = atrValue * requiredATRMultiplier;
    
    double lastOpenPrice = 0, lastVolume = 0, lastProfit = 0;
    if(!GetLastPositionInfo(posType, lastOpenPrice, lastVolume, lastProfit)) return false;
    
    double currentPrice = isBuy ? SymbolInfoDouble(m_symbol, SYMBOL_BID) : SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    double profitDistance = isBuy ? (currentPrice - lastOpenPrice) : (lastOpenPrice - currentPrice);
    
    if(profitDistance >= requiredDistance)
    {
        static datetime lastPyrTriggerLog = 0;
        if(TimeCurrent() - lastPyrTriggerLog >= 60)
        {
            PrintFormat("[GEMINI] 金字塔触发！层级:L%d | 盈利距离:%.5f >= 要求:%.5f (%.1f×ATR)", 
                        nextLayer, profitDistance, requiredDistance, requiredATRMultiplier);
            lastPyrTriggerLog = TimeCurrent();
        }
        return true;
    }
    
    return false;
}

bool CStarfleetPositionManager::ExecutePyramid(double atrValue, bool isBuy)
{
    ENUM_POSITION_TYPE posType = isBuy ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
    int posCount = GetPositionCount(posType);
    
    if(posCount >= InpMaxPositions) return false;
    
    int layer = posCount + 1;
    
    if(layer == 2)
    {
        if(!m_l1BreakevenDone)
        {
            static datetime lastL2RejectLog = 0;
            if(TimeCurrent() - lastL2RejectLog >= 60)
            {
                Print("[GEMINI] L2开仓被拒绝！L1尚未保本，禁止加仓！");
                lastL2RejectLog = TimeCurrent();
            }
            return false;
        }
        
        ulong ticket = 0;
        double openPrice = 0, openVolume = 0;
        if(GetPositionByLayer(posType, 1, ticket, openPrice, openVolume))
        {
            if(!PositionSelectByTicket(ticket))
            {
                Print("[GEMINI] L1仓位查询失败，禁止L2开仓！");
                return false;
            }
            
            double currentSL = PositionGetDouble(POSITION_SL);
            if(posType == POSITION_TYPE_BUY)
            {
                if(currentSL < openPrice - m_point)
                {
                    static datetime lastSLRejectLog = 0;
                    if(TimeCurrent() - lastSLRejectLog >= 60)
                    {
                        PrintFormat("[GEMINI] L1止损未保本！SL:%.5f < 开仓价:%.5f，禁止L2开仓！", currentSL, openPrice);
                        lastSLRejectLog = TimeCurrent();
                    }
                    return false;
                }
            }
            else
            {
                if(currentSL > openPrice + m_point || currentSL == 0)
                {
                    static datetime lastSLRejectLog = 0;
                    if(TimeCurrent() - lastSLRejectLog >= 60)
                    {
                        PrintFormat("[GEMINI] L1止损未保本！SL:%.5f > 开仓价:%.5f，禁止L2开仓！", currentSL, openPrice);
                        lastSLRejectLog = TimeCurrent();
                    }
                    return false;
                }
            }
        }
        
        Print("[GEMINI] L1保本验证通过，L2开仓权限释放！");
    }
    
    double layerRisk = CalculatePyramidRisk(layer);
    
    if(layerRisk <= 0) return false;
    
    double slPoints = atrValue * InpAtrMultiplier / m_point;
    double lots = g_risk.CalculateLotSize(slPoints, layerRisk);
    
    if(lots <= 0)
    {
        PrintFormat("[GEMINI] L%d手数计算失败！", layer);
        return false;
    }
    
    double price = isBuy ? SymbolInfoDouble(m_symbol, SYMBOL_ASK) : SymbolInfoDouble(m_symbol, SYMBOL_BID);
    double sl = CalculateAtrStopLoss(atrValue, posType, price);
    
    double tp = 0;
    if(layer < InpMaxPositions)
    {
        tp = isBuy ? price + atrValue * InpAtrMultiplier * 3 : price - atrValue * InpAtrMultiplier * 3;
        tp = NormalizeDouble(tp, m_digits);
    }
    
    m_trade.SetExpertMagicNumber(m_magic);
    bool result = false;
    
    PrintFormat(">>> [金字塔开仓] 层级:L%d | 风险:%.2f%% | 手数:%.5f | 价格:%.5f | ATR-SL:%.5f | TP:%.5f",
                layer, layerRisk, lots, price, sl, tp);
    
    if(isBuy)
        result = m_trade.Buy(lots, m_symbol, price, sl, tp, StringFormat("PYRAMID_L%d", layer));
    else
        result = m_trade.Sell(lots, m_symbol, price, sl, tp, StringFormat("PYRAMID_L%d", layer));
    
    if(result)
    {
        PrintFormat("[GEMINI] L%d金字塔加仓成功！风险权重:%.2f%% | 手数:%.5f | ATR阶梯止损:%.5f", layer, layerRisk, lots, sl);
        
        if(layer >= 2)
        {
            SyncStopLoss(posType, layer, atrValue);
        }
        
        if(layer >= InpMaxPositions)
        {
            m_l3Active = true;
            Print("[GEMINI] L3已激活，进入吊灯离场模式！");
        }
    }
    
    return result;
}

bool CStarfleetPositionManager::ManagePyramid(double atrValue, bool isBuy)
{
    if(!InpEnablePyramid) return false;
    
    ENUM_POSITION_TYPE posType = isBuy ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
    int posCount = GetPositionCount(posType);
    
    if(posCount > 0)
    {
        if(!m_l1BreakevenDone && posCount == 1)
        {
            if(CheckL1BreakevenTrigger(atrValue, posType))
            {
                ExecuteL1Breakeven(atrValue, posType);
            }
        }
    }
    
    if(CheckPyramidTrigger(atrValue, isBuy))
    {
        return ExecutePyramid(atrValue, isBuy);
    }
    
    return false;
}

void CStarfleetExecutor::CStarfleetExecutor()
{
    m_symbol = "";
    m_digits = 0;
    m_point = 0;
    m_magic = 0;
    m_spreadCount = 0;
    ArrayResize(m_spreadHistory, 100);
}

bool CStarfleetExecutor::Init(string symbol, int digits, double point, int magic)
{
    m_symbol = symbol;
    m_digits = digits;
    m_point = point;
    m_magic = magic;
    m_trade.SetExpertMagicNumber(magic);
    m_trade.SetDeviationInPoints(30);
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);
    return true;
}

bool CStarfleetExecutor::CheckFreeMargin(double lots, ENUM_POSITION_TYPE posType)
{
    ENUM_ORDER_TYPE orderType = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    double price = (posType == POSITION_TYPE_BUY) ? 
                   SymbolInfoDouble(m_symbol, SYMBOL_ASK) : 
                   SymbolInfoDouble(m_symbol, SYMBOL_BID);
    
    double requiredMargin = 0;
    if(!OrderCalcMargin(orderType, m_symbol, lots, price, requiredMargin))
        return false;
    
    double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    
    if(freeMargin < requiredMargin)
    {
        PrintFormat("[GEMINI] 保证金不足！可用:%.2f 需要:%.2f", freeMargin, requiredMargin);
        return false;
    }
    
    return true;
}

double CStarfleetExecutor::GetAvgSpread(int bars)
{
    double sum = 0;
    int count = MathMin(bars, m_spreadCount);
    
    if(count == 0) return 0;
    
    for(int i = 0; i < count; i++)
    {
        sum += m_spreadHistory[i];
    }
    
    return sum / count;
}

void CStarfleetExecutor::UpdateSpreadHistory()
{
    double spread = SymbolInfoDouble(m_symbol, SYMBOL_ASK) - SymbolInfoDouble(m_symbol, SYMBOL_BID);
    spread = spread / m_point;
    
    if(m_spreadCount >= 100)
    {
        for(int i = 0; i < 99; i++)
        {
            m_spreadHistory[i] = m_spreadHistory[i + 1];
        }
        m_spreadHistory[99] = spread;
    }
    else
    {
        m_spreadHistory[m_spreadCount] = spread;
        m_spreadCount++;
    }
}

bool CStarfleetExecutor::CheckSpread(double maxMultiplier)
{
    UpdateSpreadHistory();
    
    double currentSpread = SymbolInfoDouble(m_symbol, SYMBOL_ASK) - SymbolInfoDouble(m_symbol, SYMBOL_BID);
    currentSpread = currentSpread / m_point;
    
    double avgSpread = GetAvgSpread(60);
    
    if(avgSpread > 0 && currentSpread > avgSpread * maxMultiplier)
    {
        PrintFormat("[GEMINI] 点差异常！当前:%.1f > 平均:%.1f × %.1f", currentSpread, avgSpread, maxMultiplier);
        return false;
    }
    
    return true;
}

bool CStarfleetExecutor::OpenPosition(ENUM_POSITION_TYPE posType, double lots, double sl, double tp, string comment)
{
    if(!MQLInfoInteger(MQL_TESTER))
    {
        if(!SymbolInfoInteger(m_symbol, SYMBOL_SESSION_DEALS))
        {
            PrintFormat("[GEMINI] 平台休市拦截！当前品种 %s 处于非交易时段，拒绝发送订单。", m_symbol);
            return false;
        }
        
        if(SymbolInfoInteger(m_symbol, SYMBOL_TRADE_MODE) != SYMBOL_TRADE_MODE_FULL)
        {
            PrintFormat("[GEMINI] 交易模式异常！当前品种 %s 不支持完整交易，拒绝发送订单。", m_symbol);
            return false;
        }
    }
    
    if(lots <= 0)
    {
        Print("[GEMINI] 手数为0，取消开仓！");
        return false;
    }
    
    double tickValue = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE);
    double tickSize = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_SIZE);
    
    if(tickValue <= 0 || tickSize <= 0)
    {
        PrintFormat("[GEMINI] tick_value/tick_size异常！tickValue:%.5f tickSize:%.5f，取消开仓！", tickValue, tickSize);
        return false;
    }
    
    if(!CheckFreeMargin(lots, posType))
        return false;
    
    if(!CheckSpread(InpMaxSpreadMultiplier))
        return false;
    
    double signalPrice = (posType == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(m_symbol, SYMBOL_ASK) : 
                         SymbolInfoDouble(m_symbol, SYMBOL_BID);
    
    signalPrice = NormalizeDouble(signalPrice, m_digits);
    sl = NormalizeDouble(sl, m_digits);
    tp = NormalizeDouble(tp, m_digits);
    
    m_trade.SetExpertMagicNumber(m_magic);
    
    PrintFormat(">>> [开仓入口] 手数:%.5f | 类型:%s | 信号价:%.5f | SL:%.5f | TP:%.5f", 
                lots, (posType == POSITION_TYPE_BUY ? "BUY" : "SELL"), signalPrice, sl, tp);
    
    bool result = false;
    if(posType == POSITION_TYPE_BUY)
        result = m_trade.Buy(lots, m_symbol, signalPrice, sl, tp, comment);
    else
        result = m_trade.Sell(lots, m_symbol, signalPrice, sl, tp, comment);
    
    if(result)
    {
        Sleep(100);
        
        int total = PositionsTotal();
        for(int i = total - 1; i >= 0; i--)
        {
            ulong ticket = PositionGetTicket(i);
            if(ticket == 0) continue;
            if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
            
            double filledPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            double slippage = (posType == POSITION_TYPE_BUY) ? 
                              (filledPrice - signalPrice) : 
                              (signalPrice - filledPrice);
            double slippagePoints = slippage / m_point;
            
            PrintFormat("[GEMINI] 成交确认！成交价:%.5f | 滑点:%.1f点 (%.5f) | tick_value:%.5f", 
                        filledPrice, slippagePoints, slippage, tickValue);
            break;
        }
    }
    
    return result;
}

bool CStarfleetExecutor::ClosePosition(ulong ticket)
{
    m_trade.SetExpertMagicNumber(m_magic);
    return m_trade.PositionClose(ticket);
}

bool CStarfleetExecutor::ModifyPosition(ulong ticket, double sl, double tp)
{
    m_trade.SetExpertMagicNumber(m_magic);
    return m_trade.PositionModify(ticket, sl, tp);
}

void CStarfleetExecutor::CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
        if(PositionGetInteger(POSITION_MAGIC) != m_magic) continue;
        
        m_trade.SetExpertMagicNumber(m_magic);
        m_trade.PositionClose(ticket);
    }
}

int OnInit()
{
    g_digits = (int)SymbolInfoInteger(g_symbol, SYMBOL_DIGITS);
    g_point = SymbolInfoDouble(g_symbol, SYMBOL_POINT);
    
    if(g_point == 0)
    {
        Print("[GEMINI] 无法获取品种点值！");
        return INIT_FAILED;
    }
    
    if(!g_signal.Init(g_symbol))
    {
        Print("[GEMINI] 信号模块初始化失败！");
        return INIT_FAILED;
    }
    
    if(!g_risk.Init(g_symbol, g_digits, g_point, InpAtrPeriod, InpMagicNumber))
    {
        Print("[GEMINI] 风控模块初始化失败！");
        return INIT_FAILED;
    }
    
    if(!g_positionMgr.Init(g_symbol, InpMagicNumber, g_point, g_digits))
    {
        Print("[GEMINI] 仓位管理模块初始化失败！");
        return INIT_FAILED;
    }
    
    if(!g_executor.Init(g_symbol, g_digits, g_point, InpMagicNumber))
    {
        Print("[GEMINI] 执行模块初始化失败！");
        return INIT_FAILED;
    }
    
    Print("[GEMINI] GEMINI Starfleet EA V4.32 唐奇安通道突破引擎启动成功！");
    PrintFormat("[GEMINI] Donchian:%d | ADX:%.1f | RSI:%d | ATR:%d | 风险:%.1f%% | 熔断:%.1f%%", 
                InpDonchianPeriod, InpAdxThreshold, InpRsiPeriod, InpAtrPeriod, InpRiskPercent, InpDailyDrawdownLimit);
    
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
    Print("[GEMINI] GEMINI Starfleet EA V4.32 已离线。");
}

void OnTick()
{
    if(!TerminalInfoInteger(TERMINAL_CONNECTED)) return;
    
    FridayCloseAll();
    
    MqlDateTime dt;
    TimeCurrent(dt);
    
    static int lastDay = -1;
    if(dt.day_of_year != lastDay)
    {
        g_risk.ResetDailyEquity();
        lastDay = dt.day_of_year;
        PrintFormat("[GEMINI] 新交易日开始，净值基准已重置！Day:%d", lastDay);
    }
    
    if(InpCloseOnFriday && dt.day_of_week == 5 && dt.hour >= InpFridayCloseHour)
        return;
    
    g_executor.UpdateSpreadHistory();
    
    if(!CheckTradeTime(dt))
        return;
    
    if(g_risk.CheckDailyEquityProtection(InpDailyDrawdownLimit))
        return;
    
    g_risk.CheckAndSetSleepMode();
    
    if(g_risk.IsInSleepMode())
        return;
    
    double atrValue = g_signal.GetCurrentAtr();
    if(atrValue <= 0) return;
    
    g_positionMgr.UpdateAtrStops(atrValue);
    
    if(InpEnablePyramid)
    {
        g_positionMgr.ManagePyramid(atrValue, true);
        g_positionMgr.ManagePyramid(atrValue, false);
    }
    
    static datetime lastEntryBarTime = 0;
    
    bool isBuySignal = false;
    if(g_signal.GenerateSignal(isBuySignal))
    {
        ENUM_POSITION_TYPE posType = isBuySignal ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
        int posCount = CountPositions(posType);
        
        if(posCount == 0)
        {
            if(iTime(g_symbol, PERIOD_CURRENT, 0) == lastEntryBarTime)
            {
                // 同一根K线已尝试过首仓开仓，跳过
            }
            else
            {
                double slPoints = g_risk.CalculateDynamicSL(atrValue, InpAtrMultiplier);
                double lots = g_risk.CalculateLotSize(slPoints, InpRiskPercent);
                
                if(lots > 0)
                {
                    double price = isBuySignal ? SymbolInfoDouble(g_symbol, SYMBOL_ASK) : SymbolInfoDouble(g_symbol, SYMBOL_BID);
                    double sl = isBuySignal ? price - atrValue * InpAtrMultiplier : price + atrValue * InpAtrMultiplier;
                    double tp = isBuySignal ? price + atrValue * InpAtrMultiplier * 3 : price - atrValue * InpAtrMultiplier * 3;
                    
                    if(g_executor.OpenPosition(posType, lots, sl, tp, "ENTRY_L1"))
                    {
                        lastEntryBarTime = iTime(g_symbol, PERIOD_CURRENT, 0);
                    }
                }
            }
        }
    }
    
    datetime currentBarTime = iTime(g_symbol, PERIOD_CURRENT, 0);
    if(currentBarTime == g_lastBarTime)
        return;
    g_lastBarTime = currentBarTime;
}

bool CheckTradeTime(MqlDateTime &dt)
{
    if(dt.hour < InpTradeStartHour || dt.hour >= InpTradeEndHour)
        return false;
    return true;
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

void FridayCloseAll()
{
    if(!InpCloseOnFriday) return;
    
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
                
                g_executor.CloseAllPositions();
                
                Print("[GEMINI] 周末防爆协议启动：已清空所有仓位。");
            }
            return;
        }
    }
    else
    {
        g_fridayClosed = false;
    }
}
