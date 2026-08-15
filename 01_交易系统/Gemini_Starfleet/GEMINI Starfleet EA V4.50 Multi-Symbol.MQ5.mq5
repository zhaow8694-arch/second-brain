#property copyright "GEMINI Starfleet EA V4.70 Armored Edition"
#property link      ""
#property version   "4.70"
#property strict

#include <Trade\Trade.mqh>

//=============================================================================
// 用户控制面板
//=============================================================================
input group "=== 核心运行模式 ==="
input string   InpTradeSymbols       = "CHINA50,EURUSD,SP500,XAUUSD"; 
input bool     InpOptimizationMode   = false; // 【优化模式】开启后忽略矩阵，只用下方参数跑单一品种

input group "=== 全局风控安全阀 ==="
input double   InpDailyDrawdownLimit = 5.0;   // 每日最大净值回撤(%)
input double   InpMaxLotSize         = 2.0;   // 【安全阀】单笔绝对最大手数封顶！(防止ATR过低导致爆仓)
input bool     InpEnableNotify       = true;  

input group "=== 策略参数 (优化用) ==="
input double   InpRiskPercent        = 2.0;
input int      InpEmaFilterPeriod    = 200;   // 【趋势过滤】EMA均线周期 (0为关闭)
input int      InpDonchianPeriod     = 20;    // 唐奇安突破周期
input double   InpAtrMultiplier      = 2.0;   // 止损ATR乘数
input double   InpAdxThreshold       = 25.0;  // ADX动能阈值
input int      InpAtrPeriod          = 14;
input double   InpAtrDeadZone        = 0.5;
input int      InpRsiPeriod          = 14;
input int      InpRsiOverbought      = 70;
input int      InpRsiOversold        = 30;

input group "=== 仓位与时间管理 ==="
input bool     InpEnablePyramid      = true;
input int      InpMaxPositions       = 3;
input int      InpMagicNumber        = 20250416;
input double   InpMaxSpreadMultiplier= 3.0;
input int      InpTradeStartHour     = 1;
input int      InpTradeEndHour       = 22;
input bool     InpCloseOnFriday      = true;
input int      InpFridayCloseHour    = 21;

//=============================================================================
// 核心：品种参数矩阵结构体
//=============================================================================
struct SSymbolConfig {
    double riskPercent;
    int    emaPeriod;
    int    donchianPeriod;
    double atrMultiplier;
    double adxThreshold;
};

void GetSymbolConfig(string sym, SSymbolConfig &cfg)
{
    // 1. 默认加载面板参数
    cfg.riskPercent    = InpRiskPercent;
    cfg.emaPeriod      = InpEmaFilterPeriod;
    cfg.donchianPeriod = InpDonchianPeriod;
    cfg.atrMultiplier  = InpAtrMultiplier;
    cfg.adxThreshold   = InpAdxThreshold;

    // 2. 如果开启了【优化模式】，直接返回面板参数，不使用矩阵覆盖
    if(InpOptimizationMode) return;

    // 3. 否则，应用“千人千面”独立覆写
    if(sym == "XAUUSD") {
        cfg.donchianPeriod = 20; cfg.atrMultiplier = 2.0; cfg.adxThreshold = 25.0;
    }
    else if(sym == "EURUSD") {
        cfg.donchianPeriod = 40; cfg.atrMultiplier = 1.5; cfg.adxThreshold = 30.0; 
    }
    else if(sym == "SP500") {
        cfg.donchianPeriod = 30; cfg.atrMultiplier = 2.5; cfg.adxThreshold = 20.0;
    }
    else if(sym == "CHINA50") {
        cfg.riskPercent = 1.5; cfg.donchianPeriod = 20; cfg.adxThreshold = 25.0;
    }
}

//=============================================================================
// 基础类前置声明与实现
//=============================================================================

class CStarfleetSignal
{
private:
    int      m_handleRsi, m_handleAtr, m_handleAdx, m_handleEma;
    string   m_symbol;
    int      m_donchianPeriod, m_emaPeriod;
    double   m_adxThreshold;

    bool CheckDonchianBreakout(bool &isBuySignal);
    bool CheckEmaFilter(bool isBuySignal); // 新增EMA过滤
    bool CheckRsiFilter(bool isBuySignal);
    bool CheckAtrFilter();
    bool CheckAdxFilter(bool isBuySignal);
    double GetHighestHigh(int period);
    double GetLowestLow(int period);
    
public:
    void     CStarfleetSignal() { m_handleRsi = m_handleAtr = m_handleAdx = m_handleEma = INVALID_HANDLE; }
    void     Deinit() {
        if(m_handleRsi != INVALID_HANDLE) IndicatorRelease(m_handleRsi);
        if(m_handleAtr != INVALID_HANDLE) IndicatorRelease(m_handleAtr);
        if(m_handleAdx != INVALID_HANDLE) IndicatorRelease(m_handleAdx);
        if(m_handleEma != INVALID_HANDLE) IndicatorRelease(m_handleEma);
    }
    bool     Init(string symbol, SSymbolConfig &cfg);
    bool     GenerateSignal(bool &isBuySignal);
    double   GetCurrentAtr();
    double   GetCurrentAdx();
    bool     IsTrendExhausted();
};

bool CStarfleetSignal::Init(string symbol, SSymbolConfig &cfg)
{
    m_symbol = symbol;
    m_donchianPeriod = cfg.donchianPeriod;
    m_adxThreshold   = cfg.adxThreshold;
    m_emaPeriod      = cfg.emaPeriod;
    
    m_handleRsi = iRSI(m_symbol, PERIOD_CURRENT, InpRsiPeriod, PRICE_CLOSE);
    m_handleAtr = iATR(m_symbol, PERIOD_CURRENT, InpAtrPeriod);
    m_handleAdx = iADX(m_symbol, PERIOD_CURRENT, 14);
    
    // 初始化大级别EMA
    if(m_emaPeriod > 0) m_handleEma = iMA(m_symbol, PERIOD_CURRENT, m_emaPeriod, 0, MODE_EMA, PRICE_CLOSE);
    
    return (m_handleRsi != INVALID_HANDLE && m_handleAtr != INVALID_HANDLE && m_handleAdx != INVALID_HANDLE);
}

double CStarfleetSignal::GetHighestHigh(int period) {
    double high[]; ArraySetAsSeries(high, true);
    if(CopyHigh(m_symbol, PERIOD_CURRENT, 1, period, high) < period) return 0;
    double highest = high[0];
    for(int i = 1; i < period; i++) if(high[i] > highest) highest = high[i];
    return highest;
}

double CStarfleetSignal::GetLowestLow(int period) {
    double low[]; ArraySetAsSeries(low, true);
    if(CopyLow(m_symbol, PERIOD_CURRENT, 1, period, low) < period) return 0;
    double lowest = low[0];
    for(int i = 1; i < period; i++) if(low[i] < lowest) lowest = low[i];
    return lowest;
}

bool CStarfleetSignal::CheckDonchianBreakout(bool &isBuySignal) {
    double highestHigh = GetHighestHigh(m_donchianPeriod);
    double lowestLow = GetLowestLow(m_donchianPeriod);
    if(highestHigh == 0 || lowestLow == 0) return false;
    
    double currentAsk = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    double currentBid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
    
    if(currentAsk > highestHigh) { isBuySignal = true; return true; }
    else if(currentBid < lowestLow) { isBuySignal = false; return true; }
    return false;
}

bool CStarfleetSignal::CheckEmaFilter(bool isBuySignal) {
    if(m_emaPeriod <= 0 || m_handleEma == INVALID_HANDLE) return true; // 未开启则直接通过
    
    double ema[], close[]; 
    ArraySetAsSeries(ema, true); ArraySetAsSeries(close, true);
    if(CopyBuffer(m_handleEma, 0, 0, 1, ema) < 1) return false;
    if(CopyClose(m_symbol, PERIOD_CURRENT, 0, 1, close) < 1) return false;
    
    // EMA过滤：价格在EMA之上只许做多，之下只许做空
    if(isBuySignal && close[0] < ema[0]) return false;
    if(!isBuySignal && close[0] > ema[0]) return false;
    
    return true;
}

bool CStarfleetSignal::CheckRsiFilter(bool isBuySignal) {
    double rsi[]; ArraySetAsSeries(rsi, true);
    if(CopyBuffer(m_handleRsi, 0, 0, 2, rsi) < 2) return false;
    return isBuySignal ? (rsi[1] < InpRsiOverbought) : (rsi[1] > InpRsiOversold);
}

bool CStarfleetSignal::CheckAtrFilter() {
    double atrCurrent[], atrHistory[];
    ArraySetAsSeries(atrCurrent, true); ArraySetAsSeries(atrHistory, true);
    if(CopyBuffer(m_handleAtr, 0, 0, 1, atrCurrent) < 1) return false;
    if(CopyBuffer(m_handleAtr, 0, 0, 21, atrHistory) < 21) return false;
    double atrAvg = 0;
    for(int i = 1; i <= 20; i++) atrAvg += atrHistory[i];
    atrAvg /= 20;
    return (atrCurrent[0] >= atrAvg * InpAtrDeadZone);
}

bool CStarfleetSignal::CheckAdxFilter(bool isBuySignal) {
    double adx[], diPlus[], diMinus[];
    ArraySetAsSeries(adx, true); ArraySetAsSeries(diPlus, true); ArraySetAsSeries(diMinus, true);
    if(CopyBuffer(m_handleAdx, 0, 0, 2, adx) < 2) return false;
    if(CopyBuffer(m_handleAdx, 1, 0, 2, diPlus) < 2) return false;
    if(CopyBuffer(m_handleAdx, 2, 0, 2, diMinus) < 2) return false;
    
    if(adx[1] < m_adxThreshold) return false;
    if(isBuySignal) return (diPlus[1] > diMinus[1]);
    else return (diMinus[1] > diPlus[1]);
}

double CStarfleetSignal::GetCurrentAdx() {
    double adx[]; ArraySetAsSeries(adx, true);
    return (CopyBuffer(m_handleAdx, 0, 0, 1, adx) > 0) ? adx[0] : 0;
}

double CStarfleetSignal::GetCurrentAtr() {
    double atr[]; ArraySetAsSeries(atr, true);
    return (CopyBuffer(m_handleAtr, 0, 0, 1, atr) > 0) ? atr[0] : 0;
}

bool CStarfleetSignal::IsTrendExhausted() { return (GetCurrentAdx() > 0 && GetCurrentAdx() < 15); }

bool CStarfleetSignal::GenerateSignal(bool &isBuySignal) {
    if(!CheckDonchianBreakout(isBuySignal)) return false;
    if(!CheckEmaFilter(isBuySignal)) return false;  // 执行EMA过滤
    if(!CheckRsiFilter(isBuySignal)) return false;
    if(!CheckAtrFilter()) return false;
    if(!CheckAdxFilter(isBuySignal)) return false;
    return true;
}

//=============================================================================

class CStarfleetRisk
{
private:
    string   m_symbol;
    int      m_digits;
    double   m_point;
    int      m_magic;
    double   m_riskPercent;
    
public:
    void     CStarfleetRisk() {}
    bool     Init(string symbol, int digits, double point, int magic, SSymbolConfig &cfg);
    double   CalculateDynamicSL(double atrValue, double multiplier);
    double   CalculateLotSize(double slPoints);
};

bool CStarfleetRisk::Init(string symbol, int digits, double point, int magic, SSymbolConfig &cfg) {
    m_symbol = symbol; m_digits = digits; m_point = point; m_magic = magic;
    m_riskPercent = cfg.riskPercent;
    return true;
}

double CStarfleetRisk::CalculateDynamicSL(double atrValue, double multiplier) {
    if(atrValue <= 0) return 0;
    return (atrValue * multiplier) / m_point;
}

double CStarfleetRisk::CalculateLotSize(double slPoints) {
    if(slPoints <= 0) return 0;
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(equity <= 0) return 0;
    
    double riskAmount = equity * (m_riskPercent / 100.0);
    double askPrice = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
    double slPrice = NormalizeDouble(askPrice - (slPoints * m_point), m_digits);
    
    double lossForOneLot = 0;
    if(!OrderCalcProfit(ORDER_TYPE_BUY, m_symbol, 1.0, askPrice, slPrice, lossForOneLot)) return 0;
    
    double riskPerLot = MathAbs(lossForOneLot);
    if(riskPerLot <= 0) return 0;
    
    double finalLot = riskAmount / riskPerLot;
    double minLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);
    
    finalLot = MathFloor(finalLot / lotStep) * lotStep;
    if(finalLot < minLot) finalLot = minLot;
    
    // 【核心修复】单笔最大手数绝对封顶！防止震荡市由于ATR极低导致爆仓开仓
    if(finalLot > InpMaxLotSize) {
        PrintFormat("[防爆拦截] %s 计算手数 %.2f 触发封顶限制，截断为 %.2f 手!", m_symbol, finalLot, InpMaxLotSize);
        finalLot = InpMaxLotSize;
    }
    else if(finalLot > maxLot) {
        finalLot = maxLot;
    }
    
    return finalLot;
}

//=============================================================================

class CStarfleetExecutor {
private:
    CTrade   m_trade;
    string   m_symbol;
    int      m_digits;
    double   m_point;
    int      m_magic;
    double   m_spreadHistory[];
    int      m_spreadCount;
    
    ENUM_ORDER_TYPE_FILLING GetFillingMode();
public:
    void     CStarfleetExecutor() { m_spreadCount = 0; ArrayResize(m_spreadHistory, 100); }
    bool     Init(string symbol, int digits, double point, int magic);
    bool     OpenPosition(ENUM_POSITION_TYPE posType, double lots, double sl, double tp, string comment);
    void     CloseAllPositions();
    void     UpdateSpreadHistory();
    bool     CheckSpread(double maxMultiplier);
    CTrade* GetTradeObj() { return GetPointer(m_trade); }
};

ENUM_ORDER_TYPE_FILLING CStarfleetExecutor::GetFillingMode() {
    int filling = (int)SymbolInfoInteger(m_symbol, SYMBOL_FILLING_MODE);
    if((filling & SYMBOL_FILLING_FOK) != 0) return ORDER_FILLING_FOK;
    if((filling & SYMBOL_FILLING_IOC) != 0) return ORDER_FILLING_IOC;
    return ORDER_FILLING_RETURN;
}

bool CStarfleetExecutor::Init(string symbol, int digits, double point, int magic) {
    m_symbol = symbol; m_digits = digits; m_point = point; m_magic = magic;
    m_trade.SetExpertMagicNumber(magic);
    m_trade.SetDeviationInPoints(30);
    m_trade.SetTypeFilling(GetFillingMode());
    return true;
}

void CStarfleetExecutor::UpdateSpreadHistory() {
    double spread = (SymbolInfoDouble(m_symbol, SYMBOL_ASK) - SymbolInfoDouble(m_symbol, SYMBOL_BID)) / m_point;
    if(m_spreadCount >= 100) {
        for(int i = 0; i < 99; i++) m_spreadHistory[i] = m_spreadHistory[i + 1];
        m_spreadHistory[99] = spread;
    } else {
        m_spreadHistory[m_spreadCount++] = spread;
    }
}

bool CStarfleetExecutor::CheckSpread(double maxMultiplier) {
    if(m_spreadCount == 0) return true;
    double currentSpread = (SymbolInfoDouble(m_symbol, SYMBOL_ASK) - SymbolInfoDouble(m_symbol, SYMBOL_BID)) / m_point;
    double sum = 0;
    for(int i = 0; i < m_spreadCount; i++) sum += m_spreadHistory[i];
    return currentSpread <= (sum / m_spreadCount) * maxMultiplier;
}

bool CStarfleetExecutor::OpenPosition(ENUM_POSITION_TYPE posType, double lots, double sl, double tp, string comment) {
    if(lots <= 0 || !CheckSpread(InpMaxSpreadMultiplier)) return false;
    double price = NormalizeDouble(posType == POSITION_TYPE_BUY ? SymbolInfoDouble(m_symbol, SYMBOL_ASK) : SymbolInfoDouble(m_symbol, SYMBOL_BID), m_digits);
    sl = NormalizeDouble(sl, m_digits); tp = NormalizeDouble(tp, m_digits);
    return posType == POSITION_TYPE_BUY ? m_trade.Buy(lots, m_symbol, price, sl, tp, comment) : m_trade.Sell(lots, m_symbol, price, sl, tp, comment);
}

void CStarfleetExecutor::CloseAllPositions() {
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(PositionGetTicket(i) > 0 && PositionGetString(POSITION_SYMBOL) == m_symbol && PositionGetInteger(POSITION_MAGIC) == m_magic)
            m_trade.PositionClose(PositionGetInteger(POSITION_TICKET));
    }
}

//=============================================================================

class CStarfleetPositionManager {
private:
    string   m_symbol;
    int      m_magic;
    double   m_point;
    int      m_digits;
    CTrade* m_tradePtr;
    double   m_atrMultiplier;
public:
    void     Init(string symbol, int magic, double point, int digits, CTrade* tradeObj, SSymbolConfig &cfg) {
        m_symbol = symbol; m_magic = magic; m_point = point; m_digits = digits; m_tradePtr = tradeObj;
        m_atrMultiplier = cfg.atrMultiplier;
    }
    int      GetPositionCount(ENUM_POSITION_TYPE posType);
};

int CStarfleetPositionManager::GetPositionCount(ENUM_POSITION_TYPE posType) {
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++) {
        if(PositionGetTicket(i) > 0 && PositionGetString(POSITION_SYMBOL) == m_symbol && PositionGetInteger(POSITION_MAGIC) == m_magic && PositionGetInteger(POSITION_TYPE) == posType)
            count++;
    }
    return count;
}

//=============================================================================
// 调度器包装类
//=============================================================================

class CSymbolBot {
public:
    string   symbol;
    int      digits;
    double   point;
    datetime lastEntryBarTime;
    SSymbolConfig cfg; 
    
    CStarfleetSignal          signal;
    CStarfleetRisk            risk;
    CStarfleetExecutor        executor;
    CStarfleetPositionManager posMgr;

    bool Init(string symName) {
        symbol = symName;
        SymbolSelect(symbol, true);
        digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
        point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        lastEntryBarTime = 0;
        
        GetSymbolConfig(symbol, cfg);
        
        if(!signal.Init(symbol, cfg)) return false;
        if(!risk.Init(symbol, digits, point, InpMagicNumber, cfg)) return false;
        if(!executor.Init(symbol, digits, point, InpMagicNumber)) return false;
        posMgr.Init(symbol, InpMagicNumber, point, digits, executor.GetTradeObj(), cfg);
        
        return true;
    }
    
    void Deinit() { signal.Deinit(); }
    
    void ProcessTick(double &globalEquityDrawdown) {
        MqlDateTime dt; TimeCurrent(dt);
        
        if(InpCloseOnFriday && dt.day_of_week == 5 && dt.hour >= InpFridayCloseHour) {
            executor.CloseAllPositions(); return;
        }
        if(dt.hour < InpTradeStartHour || dt.hour >= InpTradeEndHour) return;
        if(globalEquityDrawdown >= InpDailyDrawdownLimit) return; 
        
        executor.UpdateSpreadHistory();
        double atr = signal.GetCurrentAtr();
        if(atr <= 0) return;
        
        bool isBuy = false;
        if(signal.GenerateSignal(isBuy)) {
            ENUM_POSITION_TYPE posType = isBuy ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
            if(posMgr.GetPositionCount(posType) == 0) {
                datetime currentBar = iTime(symbol, PERIOD_CURRENT, 0);
                if(currentBar != lastEntryBarTime) {
                    double slPts = risk.CalculateDynamicSL(atr, cfg.atrMultiplier); 
                    double lots = risk.CalculateLotSize(slPts);                     
                    if(lots > 0) {
                        double price = isBuy ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
                        double sl = isBuy ? price - atr*cfg.atrMultiplier : price + atr*cfg.atrMultiplier;
                        double tp = isBuy ? price + atr*cfg.atrMultiplier*3 : price - atr*cfg.atrMultiplier*3;
                        
                        if(executor.OpenPosition(posType, lots, sl, tp, "ENTRY_L1")) {
                            lastEntryBarTime = currentBar;
                        }
                    }
                }
            }
        }
    }
};

//=============================================================================
// 全局管理区
//=============================================================================

CSymbolBot g_bots[];
int g_botCount = 0;
double g_dailyStartEquity = 0;

int OnInit() {
    g_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    
    // 【核心】如果开启优化模式，强行覆盖输入品种，确保只测试图表当前品种
    string symbols[];
    if(InpOptimizationMode) {
        Print(">>> [启动提示] 优化模式已开启！仅针对当前单一图表品种进行回测。 <<<");
        ArrayResize(symbols, 1);
        symbols[0] = _Symbol;
    } else {
        StringSplit(InpTradeSymbols, ',', symbols);
    }
    
    for(int i = 0; i < ArraySize(symbols); i++) {
        StringTrimLeft(symbols[i]); StringTrimRight(symbols[i]);
        if(symbols[i] == "") continue;
        
        ArrayResize(g_bots, g_botCount + 1);
        if(g_bots[g_botCount].Init(symbols[i])) g_botCount++;
    }
    if(g_botCount == 0) return INIT_FAILED;
    EventSetTimer(1); 
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
    EventKillTimer();
    for(int i = 0; i < g_botCount; i++) g_bots[i].Deinit();
}

void OnTimer() {
    MqlDateTime dt; TimeCurrent(dt);
    static int lastDay = -1;
    if(dt.day_of_year != lastDay) { 
        g_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY); 
        lastDay = dt.day_of_year; 
    }
    
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double globalDrawdown = (g_dailyStartEquity - currentEquity) / g_dailyStartEquity * 100.0;

    for(int i = 0; i < g_botCount; i++) {
        g_bots[i].ProcessTick(globalDrawdown);
    }
}