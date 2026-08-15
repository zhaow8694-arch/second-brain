//+------------------------------------------------------------------+
//|                                  XAUUSD_Trend_Hedge_V4.mq5       |
//|                         华尔街高级量化架构师定制 - 黄金顺势对冲系统 |
//|                                  V4.0 加装智能追踪止盈与保本防线 |
//+------------------------------------------------------------------+
#property copyright "Wall Street Quant Architect"
#property link      ""
#property version   "4.00"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

//--- 【参数分组：资金管理与手数】 ---
input group "=== 资金管理与手数 ==="
input bool     InpUseDynamicLot     = false;    // 是否开启净值复利(测模型纯度建议关闭)
input double   InpFixedLotSize      = 0.5;      // 固定开仓手数(关闭复利时生效)
input double   InpMaxRiskPerTrade   = 1.0;      // 动态手数单笔最大风险(%)
input double   InpMaxDailyDrawdown  = 5.0;      // 单日最大回撤(%) - 强制上限5%
input int      InpMaxConsecutiveLoss= 3;        // 最大连续亏损次数熔断
input int      InpMaxPositions      = 3;        // 单向最大持仓单数(防深套)

//--- 【参数分组：V4新增 - 智能保本与追踪止损】 ---
input group "=== 智能保本与追踪防线 (V4核心) ==="
input bool     InpUseBreakEven      = true;     // 启用智能保本(锁定不亏钱)
input double   InpBreakEvenTrigger  = 1000;     // 保本触发距离(微点, 如1000=赚10美金时触发)
input double   InpBreakEvenProfit   = 150;      // 保本锁定利润(微点, 放在开仓价上方1.5美金防手续费)
input bool     InpUseTrailing       = true;     // 启用动态追踪止盈(让利润奔跑)
input double   InpTrailingDistance  = 1500;     // 追踪止盈距离(微点, 如距离现价15美金)
input double   InpTrailingStep      = 300;      // 追踪修改步长(微点, 防高频改单被服务器封禁)

//--- 【参数分组：趋势与震荡过滤引擎】 ---
input group "=== 趋势与震荡过滤引擎 ==="
input int      InpEmaFast           = 50;       // 快速EMA周期
input int      InpEmaSlow           = 200;      // 慢速EMA周期
input int      InpAdxPeriod         = 14;       // ADX周期 (判断趋势强度)
input double   InpAdxThreshold      = 30.0;     // ADX阈值 (严控开火权)
input color    InpColorLongZone     = clrNavy;  // 多头区间背景色(蓝)
input color    InpColorShortZone    = clrMaroon;// 空头区间背景色(橙)

//--- 【参数分组：ATR动态加仓与物理防线】 ---
input group "=== ATR加仓与物理防线 ==="
input int      InpAtrPeriod         = 14;       // ATR周期
input double   InpAtrMultiplier     = 1.5;      // 动态加仓ATR乘数
input double   InpLotMultiplier     = 0.8;      // 加仓倍率(强制<=1.0, 递减加仓)
input double   InpStopLossPoints    = 1500;     // 物理硬止损(微点, 15美金)
input double   InpTakeProfitPoints  = 5000;     // 物理硬止盈(微点)

//--- 【参数分组：全量化对冲平仓机制】 ---
input group "=== 动态对冲极速解套参数 ==="
input double   InpHedgeCoverage     = 1.02;     // 跨向对冲安全覆盖倍率(只要回本就跑)
input double   InpSameSideLockProfit= 150.0;    // 同向对冲触发阈值(高频锁润)

//--- 【参数分组：恶劣环境过滤】 ---
input group "=== 环境与时段过滤 ==="
input int      InpMaxSpread         = 80;       // 允许的最大点差(微点)
input bool     InpCloseOnFriday     = true;     // 周五收盘前强制清仓
input int      InpFridayCloseHour   = 21;       // 周五清仓时间(服务器小时)

//--- 【全局变量声明区域】 ---
CTrade         m_trade;
CPositionInfo  m_position;
int            m_handle_ema_fast;
int            m_handle_ema_slow;
int            m_handle_adx;
int            m_handle_atr;
double         m_start_of_day_equity;
int            m_consecutive_losses;
datetime       m_last_day;
bool           m_daily_fuse_active;
int            m_current_zone = 0; // 1: 多头, -1: 空头, 0: 震荡不明

//+------------------------------------------------------------------+
//| EA初始化函数                                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    if(InpMaxRiskPerTrade > 1.0 || InpMaxDailyDrawdown > 5.0 || InpLotMultiplier > 1.0)
    {
        Alert("🔴 警告：风控参数超过安全红线！初始化失败。"); return INIT_FAILED;
    }

    m_trade.SetExpertMagicNumber(888888);
    m_trade.SetDeviationInPoints(20);

    m_handle_ema_fast = iMA(_Symbol, PERIOD_CURRENT, InpEmaFast, 0, MODE_EMA, PRICE_CLOSE);
    m_handle_ema_slow = iMA(_Symbol, PERIOD_CURRENT, InpEmaSlow, 0, MODE_EMA, PRICE_CLOSE);
    m_handle_adx      = iADX(_Symbol, PERIOD_CURRENT, InpAdxPeriod);
    m_handle_atr      = iATR(_Symbol, PERIOD_CURRENT, InpAtrPeriod);
    
    if(m_handle_ema_fast == INVALID_HANDLE || m_handle_ema_slow == INVALID_HANDLE || 
       m_handle_adx == INVALID_HANDLE || m_handle_atr == INVALID_HANDLE)
        return INIT_FAILED;

    m_start_of_day_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    m_last_day = iTime(_Symbol, PERIOD_D1, 0);
    m_daily_fuse_active = false;
    m_consecutive_losses = 0;

    Print("🟢 V4.0 智能追踪版启动成功！盈利装甲已挂载。");
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
    IndicatorRelease(m_handle_ema_fast);
    IndicatorRelease(m_handle_ema_slow);
    IndicatorRelease(m_handle_adx);
    IndicatorRelease(m_handle_atr);
    ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrBlack); 
}

//+------------------------------------------------------------------+
//| 每Tick执行主逻辑                                                 |
//+------------------------------------------------------------------+
void OnTick()
{
    datetime current_day = iTime(_Symbol, PERIOD_D1, 0);
    if(current_day != m_last_day)
    {
        m_start_of_day_equity = AccountInfoDouble(ACCOUNT_EQUITY);
        m_last_day = current_day;
        m_daily_fuse_active = false; 
    }

    if(CheckDailyFuse() || CheckFridayClose()) return;

    UpdateMarketZone(); 

    // V4新增：每次价格跳动都要检查是否可以保本或上移止损
    ProcessTrailingAndBreakEven();

    ProcessLegacyProfits(); 
    ProcessCrossHedge();    
    ProcessSameSideHedge(); 

    if(IsNewBar()) 
    {
        CheckAndOpenPosition();
    }
}

//+------------------------------------------------------------------+
//| V4核心模块：智能保本与阶梯追踪止损                               |
//+------------------------------------------------------------------+
void ProcessTrailingAndBreakEven()
{
    if(!InpUseBreakEven && !InpUseTrailing) return;

    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            ulong ticket = m_position.Ticket();
            double open_price = m_position.PriceOpen();
            double current_sl = m_position.StopLoss();
            double current_tp = m_position.TakeProfit();
            long type = m_position.PositionType();

            double new_sl = current_sl;
            bool need_modify = false;

            if(type == POSITION_TYPE_BUY)
            {
                // 1. 保本逻辑 (Break-Even)
                if(InpUseBreakEven && (bid - open_price) >= (InpBreakEvenTrigger * point))
                {
                    double be_price = open_price + (InpBreakEvenProfit * point);
                    if(current_sl < be_price) 
                    {
                        new_sl = be_price;
                        need_modify = true;
                    }
                }
                
                // 2. 追踪止损逻辑 (Trailing Stop)
                if(InpUseTrailing && (bid - open_price) >= (InpTrailingDistance * point))
                {
                    double trail_price = bid - (InpTrailingDistance * point);
                    // 只有新止损比老止损高出一个步长(Step)，才允许修改，防API滥发
                    if(trail_price > current_sl + (InpTrailingStep * point))
                    {
                        new_sl = trail_price;
                        need_modify = true;
                    }
                }
            }
            else if(type == POSITION_TYPE_SELL)
            {
                // 1. 保本逻辑
                if(InpUseBreakEven && (open_price - ask) >= (InpBreakEvenTrigger * point))
                {
                    double be_price = open_price - (InpBreakEvenProfit * point);
                    if(current_sl > be_price || current_sl == 0.0) 
                    {
                        new_sl = be_price;
                        need_modify = true;
                    }
                }
                
                // 2. 追踪止损逻辑
                if(InpUseTrailing && (open_price - ask) >= (InpTrailingDistance * point))
                {
                    double trail_price = ask + (InpTrailingDistance * point);
                    if(trail_price < current_sl - (InpTrailingStep * point) || current_sl == 0.0)
                    {
                        new_sl = trail_price;
                        need_modify = true;
                    }
                }
            }

            // 执行修改
            if(need_modify)
            {
                m_trade.PositionModify(ticket, NormalizeDouble(new_sl, _Digits), current_tp);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| 多空区间判定                                                     |
//+------------------------------------------------------------------+
void UpdateMarketZone()
{
    double ema_fast[1], ema_slow[1], adx[1];
    if(CopyBuffer(m_handle_ema_fast, 0, 1, 1, ema_fast) <= 0 || 
       CopyBuffer(m_handle_ema_slow, 0, 1, 1, ema_slow) <= 0 ||
       CopyBuffer(m_handle_adx, 0, 1, 1, adx) <= 0) return;

    if(adx[0] < InpAdxThreshold)
    {
        m_current_zone = 0; 
        ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrDimGray); 
        return;
    }

    if(ema_fast[0] > ema_slow[0]) 
    {
        m_current_zone = 1; 
        ChartSetInteger(0, CHART_COLOR_BACKGROUND, InpColorLongZone);
    }
    else if(ema_fast[0] < ema_slow[0]) 
    {
        m_current_zone = -1; 
        ChartSetInteger(0, CHART_COLOR_BACKGROUND, InpColorShortZone);
    }
}

//+------------------------------------------------------------------+
//| 跨向对冲与同向减仓逻辑                                           |
//+------------------------------------------------------------------+
void ProcessCrossHedge()
{
    ulong worst_counter_ticket = 0;
    double worst_counter_loss = 0.0;
    ulong best_trend_ticket = 0;
    double best_trend_profit = 0.0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            double profit = m_position.Profit();
            
            if(m_current_zone == 1) 
            {
                if(m_position.PositionType() == POSITION_TYPE_BUY && profit > best_trend_profit)
                    { best_trend_profit = profit; best_trend_ticket = m_position.Ticket(); }
                if(m_position.PositionType() == POSITION_TYPE_SELL && profit < worst_counter_loss)
                    { worst_counter_loss = profit; worst_counter_ticket = m_position.Ticket(); }
            }
            else if(m_current_zone == -1) 
            {
                if(m_position.PositionType() == POSITION_TYPE_SELL && profit > best_trend_profit)
                    { best_trend_profit = profit; best_trend_ticket = m_position.Ticket(); }
                if(m_position.PositionType() == POSITION_TYPE_BUY && profit < worst_counter_loss)
                    { worst_counter_loss = profit; worst_counter_ticket = m_position.Ticket(); }
            }
        }
    }

    if(worst_counter_ticket > 0 && best_trend_ticket > 0)
    {
        if(best_trend_profit >= MathAbs(worst_counter_loss) * InpHedgeCoverage)
        {
            ExecuteClose(worst_counter_ticket);
            ExecuteClose(best_trend_ticket);
        }
    }
}

void ProcessSameSideHedge()
{
    ulong largest_lot_ticket = 0;
    double largest_lot = 0;
    int same_side_count = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            if((m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_BUY) ||
               (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_SELL))
            {
                same_side_count++;
                if(m_position.Volume() > largest_lot && m_position.Profit() > InpSameSideLockProfit)
                {
                    largest_lot = m_position.Volume();
                    largest_lot_ticket = m_position.Ticket();
                }
            }
        }
    }

    if(same_side_count > 1 && largest_lot_ticket > 0) ExecuteClose(largest_lot_ticket);
}

void ProcessLegacyProfits()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            if(m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_SELL && m_position.Profit() > 0)
                ExecuteClose(m_position.Ticket());
            else if(m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_BUY && m_position.Profit() > 0)
                ExecuteClose(m_position.Ticket());
        }
    }
}

//+------------------------------------------------------------------+
//| 顺势开仓与动态手数                                               |
//+------------------------------------------------------------------+
void CheckAndOpenPosition()
{
    if(m_current_zone == 0) return; 
    if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;

    int trend_positions = 0;
    double last_entry_price = 0.0;
    double last_lot_size = 0.0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            if((m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_BUY) ||
               (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_SELL))
            {
                trend_positions++;
                if(trend_positions == 1) 
                {
                    last_entry_price = m_position.PriceOpen();
                    last_lot_size = m_position.Volume();
                }
            }
        }
    }

    if(trend_positions >= InpMaxPositions) return;

    if(trend_positions > 0)
    {
        double atr[1];
        if(CopyBuffer(m_handle_atr, 0, 1, 1, atr) <= 0) return;
        double dynamic_distance = atr[0] * InpAtrMultiplier;
        
        double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        
        if(m_current_zone == 1 && (ask - last_entry_price) < dynamic_distance) return;
        if(m_current_zone == -1 && (last_entry_price - bid) < dynamic_distance) return;
    }

    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    
    double target_lot = GetProperLotSize();
    if(trend_positions > 0) target_lot = NormalizeDouble(last_lot_size * InpLotMultiplier, 2); 
    
    double sl = 0, tp = 0;
    if(m_current_zone == 1)
    {
        sl = ask - InpStopLossPoints * point;
        tp = ask + InpTakeProfitPoints * point;
        ExecuteOpen(ORDER_TYPE_BUY, target_lot, ask, sl, tp);
    }
    else if(m_current_zone == -1)
    {
        sl = bid + InpStopLossPoints * point;
        tp = bid - InpTakeProfitPoints * point;
        ExecuteOpen(ORDER_TYPE_SELL, target_lot, bid, sl, tp);
    }
}

double GetProperLotSize()
{
    if(!InpUseDynamicLot) return InpFixedLotSize; 

    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double risk_amount = equity * (InpMaxRiskPerTrade / 100.0);
    double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    
    double loss_per_lot = (InpStopLossPoints * point / tick_size) * tick_value;
    if(loss_per_lot == 0) return InpFixedLotSize; 
    
    double raw_lot = risk_amount / loss_per_lot;
    double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    raw_lot = MathFloor(raw_lot / step) * step;
    return MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), MathMin(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX), raw_lot));
}

//+------------------------------------------------------------------+
//| 风控与执行辅助                                                   |
//+------------------------------------------------------------------+
bool CheckDailyFuse()
{
    if(m_daily_fuse_active) return true; 
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double dd_percent = (m_start_of_day_equity - current_equity) / m_start_of_day_equity * 100.0;
    if(dd_percent >= InpMaxDailyDrawdown || m_consecutive_losses >= InpMaxConsecutiveLoss)
    {
        m_daily_fuse_active = true;
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol) ExecuteClose(m_position.Ticket());
        }
        return true;
    }
    return false;
}

bool CheckFridayClose()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    if(InpCloseOnFriday && dt.day_of_week == 5 && dt.hour >= InpFridayCloseHour)
    {
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol) ExecuteClose(m_position.Ticket());
        }
        return true;
    }
    return false;
}

void ExecuteOpen(ENUM_ORDER_TYPE type, double vol, double price, double sl, double tp)
{
    for(int retry = 0; retry < 2; retry++)
    {
        if(type == ORDER_TYPE_BUY) { if(m_trade.Buy(vol, _Symbol, price, sl, tp)) break; }
        else                       { if(m_trade.Sell(vol, _Symbol, price, sl, tp)) break; }
        Sleep(100);
        SymbolInfoDouble(_Symbol, (type == ORDER_TYPE_BUY ? SYMBOL_ASK : SYMBOL_BID), price);
    }
}

void ExecuteClose(ulong ticket)
{
    for(int retry = 0; retry < 2; retry++)
    {
        if(m_trade.PositionClose(ticket)) break;
        Sleep(100);
    }
}

bool IsNewBar()
{
    static datetime last_time = 0;
    datetime current_time = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_time != last_time)
    {
        last_time = current_time;
        return true;
    }
    return false;
}
//+------------------------------------------------------------------+