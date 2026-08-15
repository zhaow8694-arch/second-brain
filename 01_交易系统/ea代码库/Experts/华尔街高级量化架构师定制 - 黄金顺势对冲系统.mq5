//+------------------------------------------------------------------+
//|                                  XAUUSD_Dual_Engine_V5.0.mq5       |
//|                         华尔街高级量化架构师定制 - 黄金双引擎系统   |
//|              V5.0 趋势引擎(ADX≥20) + 震荡引擎(ADX<20)            |
//+------------------------------------------------------------------+
#property copyright "Wall Street Quant Architect"
#property link      ""
#property version   "5.00"

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
input double   InpBreakEvenTrigger  = 1400;     // 保本触发距离(微点, 冠军参数1400)
input double   InpBreakEvenProfit   = 150;      // 保本锁定利润(微点, 放在开仓价上方1.5美金防手续费)
input bool     InpUseTrailing       = true;     // 启用动态追踪止盈(让利润奔跑)
input double   InpTrailingDistance  = 2900;     // 追踪止盈距离(微点, 冠军参数2900)
input double   InpTrailingStep      = 300;      // 追踪修改步长(微点, 防高频改单被服务器封禁)

//--- 【参数分组：趋势与震荡过滤引擎】 ---
input group "=== 趋势与震荡过滤引擎 ==="
input int      InpEmaFast           = 50;       // 快速EMA周期
input int      InpEmaSlow           = 200;      // 慢速EMA周期
input int      InpAdxPeriod         = 14;       // ADX周期 (判断趋势强度)
input double   InpAdxThreshold      = 20.0;     // ADX阈值 (冠军参数20)
input int      InpRegimeMinBars      = 3;        // 模式切换最短冷却K线数(防抖动)
input double   InpRegimeTrendScore   = 3.0;      // 进入趋势需要的最低趋势分(0~7)
input double   InpRegimeRangeScore   = 1.0;      // 进入震荡需要低于的趋势分(0~7)
input double   InpRangeMinATRMult    = 2.0;      // 震荡区间最小ATR倍乘(区间宽度/Atr<此值不交易)
input color    InpColorLongZone     = clrNavy;  // 多头区间背景色(蓝)
input color    InpColorShortZone    = clrMaroon;// 空头区间背景色(橙)

//--- 【参数分组：ATR动态加仓与物理防线】 ---
input group "=== ATR加仓与物理防线 ==="
input int      InpAtrPeriod         = 14;       // ATR周期
input double   InpAtrMultiplier     = 2.5;      // 动态加仓ATR乘数 (冠军参数2.5)
input double   InpLotMultiplier     = 0.8;      // 加仓倍率(强制<=1.0, 递减加仓)
input double   InpStopLossPoints    = 1500;     // 物理硬止损(微点, 15美金)
input double   InpTakeProfitPoints  = 5000;     // 物理硬止盈(微点)

//--- 【参数分组：对冲解套机制 V4.2重构】 ---
input group "=== 动态对冲极速解套参数 ==="
input double   InpHedgeCoverage     = 0.8;      // 单向解套覆盖率(V4.2参数80%即可解套)
input double   InpSameSideLockProfit= 200.0;    // 同向锁润触发阈值(冠军参数200, 总浮盈超过此值则塔尖减仓)
input int      InpHedgeMinBars       = 0;        // 对冲冷静期(0=立即允许对冲, 仅保留参数兼容)

//--- 【参数分组：V5.0震荡引擎】 ---
input group "=== V5.0震荡引擎(ADX<20时激活) ==="
input int      InpRangeLookback      = 20;       // 区间计算回溯K线数(20根H1=约1天)
input double   InpRangeEntryZone     = 0.3;      // 区间边缘入场比例(0.3=距边界30%区间宽度内进场)
input double   InpRangeTPRatio       = 0.4;      // 区间止盈比例(区间宽度的40%)
input double   InpRangeSLATRMult     = 1.5;      // 区间止损ATR乘数(假突破时有宽度保护)
input int      InpRangeMaxPositions  = 2;        // 震荡方向最大持仓

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
datetime       m_last_open_bar = 0;  // 上次开仓所在K线
int            m_last_open_dir = 0;  // 该K线上已开仓方向(1多/-1空/0无)
double         m_range_high = 0;     // 震荡区间上沿
double         m_range_low = 0;      // 震荡区间下沿
double         m_adx_last = 0;       // 最新ADX值(供显示)
int            m_prev_regime = 0;    // 上一根K线的模式(0震荡/1趋势)
int            m_regime_bars = 0;    // 当前模式持续K线数

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
    m_trade.SetDeviationInPoints(50);

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

    Print("🟢 V5.0 双引擎启动成功！编译日期: ", __DATE__);
    Comment("V5.0 | 待命...");
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
    Comment("V5.0 | ADX: ", DoubleToString(m_adx_last, 1), " | Zone: ", m_current_zone,
            " | 持仓: ", PositionsTotal(), " | 净值: ", DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 0));

    if(m_current_zone == 0)
        EngineRange();
    else
        EngineTrend();

    if(IsNewBar()) 
    {
        if(m_current_zone == 0)
            CheckAndOpenRangePosition();
        else
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
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
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
//| V5.1 智能模式识别大脑 (多维评分 + 非对称遲滯 + 质量门)          |
//+------------------------------------------------------------------+
void UpdateMarketZone()
{
    if(!IsNewBarRaw()) return;

    int new_regime_raw = ClassifyRegime();

    if(new_regime_raw == m_prev_regime)
    {
        m_regime_bars++;
    }
    else
    {
        bool can_switch = false;

        if(m_prev_regime == 0 && new_regime_raw == 1)
        {
            if(m_regime_bars >= 1) can_switch = true;
        }
        else if(m_prev_regime == 1 && new_regime_raw == 0)
        {
            if(m_regime_bars >= InpRegimeMinBars)
            {
                UpdateRangeBounds();
                double atr_val[1];
                if(CopyBuffer(m_handle_atr, 0, 1, 1, atr_val) > 0)
                {
                    double range_width = (m_range_high - m_range_low) / SymbolInfoDouble(_Symbol, SYMBOL_POINT);
                    if(range_width > 0 && range_width >= InpRangeMinATRMult * atr_val[0])
                        can_switch = true;
                }
            }
        }

        if(can_switch)
        {
            m_prev_regime = new_regime_raw;
            m_regime_bars = 1;
        }
    }

    int regime = m_prev_regime;

    if(regime == 0)
    {
        if(m_current_zone != 0) { m_current_zone = 0; ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrDimGray); }
        return;
    }

    double ema_fast[1], ema_slow[1];
    if(CopyBuffer(m_handle_ema_fast, 0, 1, 1, ema_fast) <= 0 ||
       CopyBuffer(m_handle_ema_slow, 0, 1, 1, ema_slow) <= 0) return;

    int dir = 0;
    if(ema_fast[0] > ema_slow[0])       dir = 1;
    else if(ema_fast[0] < ema_slow[0])   dir = -1;

    if(dir != 0 && dir != m_current_zone)
    {
        m_current_zone = dir;
        if(dir == 1) ChartSetInteger(0, CHART_COLOR_BACKGROUND, InpColorLongZone);
        else         ChartSetInteger(0, CHART_COLOR_BACKGROUND, InpColorShortZone);
    }
}

int ClassifyRegime()
{
    double adx[4];
    if(CopyBuffer(m_handle_adx, 0, 0, 4, adx) < 4) return m_prev_regime;
    m_adx_last = adx[0];

    double score = 0;

    if(adx[0] > 25)       score += 3;
    else if(adx[0] > 22)  score += 2;
    else if(adx[0] > 20)  score += 1;
    else if(adx[0] < 15)  score -= 1;

    double adx_slope = adx[0] - adx[3];
    if(adx_slope > 1.5)       score += 1.5;
    else if(adx_slope > 0.3)  score += 0.5;
    else if(adx_slope < -1.5) score -= 1.5;
    else if(adx_slope < -0.3) score -= 0.5;

    double highs[6], lows[6];
    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 6, highs) >= 6 &&
       CopyLow(_Symbol, PERIOD_CURRENT, 0, 6, lows) >= 6)
    {
        bool higher_high = (highs[0] > highs[2] && highs[2] > highs[4]);
        bool higher_low  = (lows[0] > lows[2] && lows[2] > lows[4]);
        bool lower_high  = (highs[0] < highs[2] && highs[2] < highs[4]);
        bool lower_low   = (lows[0] < lows[2] && lows[2] < lows[4]);

        if(higher_high && higher_low)       score += 2;
        else if(lower_low && lower_high)    score += 2;
        else if(!higher_high && !lower_low) score -= 1;
    }

    if(score >= InpRegimeTrendScore) return 1;
    if(score <= InpRegimeRangeScore) return 0;
    return m_prev_regime;
}

bool IsNewBarRaw()
{
    static datetime last_bar = 0;
    datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_bar != last_bar) { last_bar = current_bar; return true; }
    return false;
}

//+------------------------------------------------------------------+
//| V5.0 趋势引擎 (原有逻辑封装)                                     |
//+------------------------------------------------------------------+
void EngineTrend()
{
    ProcessTrailingAndBreakEven();
    ProcessSameSideHedge();    
    ProcessLegacyProfits(); 
    ProcessCrossHedge(); 
}

//+------------------------------------------------------------------+
//| V5.0 震荡引擎 (区间网格)                                         |
//+------------------------------------------------------------------+
void EngineRange()
{
    ProcessTrailingAndBreakEven();
    ProcessRangeClose();
}

void ProcessRangeClose()
{
    ulong close_tickets[];
    int close_count = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
        {
            double profit = m_position.Profit();
            double tp_price = 0;
            double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

            if(m_range_high <= m_range_low) continue;

            double range_width = (m_range_high - m_range_low) / point;
            double tp_points = range_width * InpRangeTPRatio;

            if(m_position.PositionType() == POSITION_TYPE_BUY)
            {
                tp_price = m_position.PriceOpen() + tp_points * point;
                if(SymbolInfoDouble(_Symbol, SYMBOL_BID) >= tp_price && profit > 0)
                {
                    ArrayResize(close_tickets, close_count + 1);
                    close_tickets[close_count++] = m_position.Ticket();
                }
            }
            else if(m_position.PositionType() == POSITION_TYPE_SELL)
            {
                tp_price = m_position.PriceOpen() - tp_points * point;
                if(SymbolInfoDouble(_Symbol, SYMBOL_ASK) <= tp_price && profit > 0)
                {
                    ArrayResize(close_tickets, close_count + 1);
                    close_tickets[close_count++] = m_position.Ticket();
                }
            }
        }
    }

    for(int i = 0; i < close_count; i++) ExecuteClose(close_tickets[i]);
}

void UpdateRangeBounds()
{
    double highs[], lows[];
    ArraySetAsSeries(highs, true);
    ArraySetAsSeries(lows, true);

    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, InpRangeLookback, highs) < InpRangeLookback) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, InpRangeLookback, lows) < InpRangeLookback) return;

    m_range_high = highs[ArrayMaximum(highs, 0, InpRangeLookback)];
    m_range_low  = lows[ArrayMinimum(lows, 0, InpRangeLookback)];
}

void CheckAndOpenRangePosition()
{
    if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;

    UpdateRangeBounds();

    if(m_range_high <= m_range_low) return;

    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double range_width = (m_range_high - m_range_low) / point;
    double entry_buffer = range_width * InpRangeEntryZone * point;
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double atr_val[1];
    if(CopyBuffer(m_handle_atr, 0, 1, 1, atr_val) <= 0) return;

    int buy_positions = 0, sell_positions = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
        {
            if(m_position.PositionType() == POSITION_TYPE_BUY)  buy_positions++;
            else                                                 sell_positions++;
        }
    }

    if(buy_positions < InpRangeMaxPositions && ask <= m_range_low + entry_buffer)
    {
        double sl = ask - atr_val[0] * InpRangeSLATRMult;
        ExecuteOpen(ORDER_TYPE_BUY, InpFixedLotSize, ask, sl, 0);
    }

    if(sell_positions < InpRangeMaxPositions && bid >= m_range_high - entry_buffer)
    {
        double sl = bid + atr_val[0] * InpRangeSLATRMult;
        ExecuteOpen(ORDER_TYPE_SELL, InpFixedLotSize, bid, sl, 0);
    }
}

//+------------------------------------------------------------------+
//| 对冲层：单向解套 + 塔尖减仓 + 逆势残留清理                        |
//+------------------------------------------------------------------+
void ProcessCrossHedge()
{
    double total_trend_profit = 0.0;
    double total_counter_loss = 0.0;
    ulong counter_tickets[];
    int counter_count = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
        {
            double profit = m_position.Profit();
            bool is_trend = (m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_BUY) ||
                            (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_SELL);

            if(is_trend && profit > 0)
                total_trend_profit += profit;
            else if(!is_trend && profit < 0)
            {
                total_counter_loss += MathAbs(profit);
                ArrayResize(counter_tickets, counter_count + 1);
                counter_tickets[counter_count++] = m_position.Ticket();
            }
        }
    }

    if(counter_count > 0 && total_trend_profit >= total_counter_loss * InpHedgeCoverage)
    {
        for(int i = 0; i < counter_count; i++) ExecuteClose(counter_tickets[i]);
    }
}

void ProcessSameSideHedge()
{
    int same_side_count = 0;
    double same_side_total_profit = 0.0;
    ulong smallest_lot_ticket = 0;
    double smallest_lot = DBL_MAX;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
        {
            if((m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_BUY) ||
               (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_SELL))
            {
                same_side_count++;
                same_side_total_profit += m_position.Profit();
                if(m_position.Volume() < smallest_lot && m_position.Profit() > 0)
                {
                    smallest_lot = m_position.Volume();
                    smallest_lot_ticket = m_position.Ticket();
                }
            }
        }
    }

    if(same_side_count > 1 && same_side_total_profit > InpSameSideLockProfit && smallest_lot_ticket > 0)
        ExecuteClose(smallest_lot_ticket);
}

void ProcessLegacyProfits()
{
    ulong legacy_tickets[];
    int legacy_count = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
        {
            if(m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_SELL && m_position.Profit() > 0)
            {
                ArrayResize(legacy_tickets, legacy_count + 1);
                legacy_tickets[legacy_count++] = m_position.Ticket();
            }
            else if(m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_BUY && m_position.Profit() > 0)
            {
                ArrayResize(legacy_tickets, legacy_count + 1);
                legacy_tickets[legacy_count++] = m_position.Ticket();
            }
        }
    }

    for(int i = 0; i < legacy_count; i++) ExecuteClose(legacy_tickets[i]);
}

//+------------------------------------------------------------------+
//| 顺势开仓与动态手数                                               |
//+------------------------------------------------------------------+
void CheckAndOpenPosition()
{
    if(m_current_zone == 0) return; 
    if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;

    datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_bar != m_last_open_bar)
    {
        m_last_open_bar = current_bar;
        m_last_open_dir = 0;
    }

    if(m_last_open_dir != 0 && m_last_open_dir != m_current_zone) return;

    int trend_positions = 0;
    double last_entry_price = 0.0;
    double last_lot_size = 0.0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
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
        m_last_open_dir = m_current_zone;
    }
    else if(m_current_zone == -1)
    {
        sl = bid + InpStopLossPoints * point;
        tp = bid - InpTakeProfitPoints * point;
        ExecuteOpen(ORDER_TYPE_SELL, target_lot, bid, sl, tp);
        m_last_open_dir = m_current_zone;
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
        ulong tickets[];
        int count = 0;
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
            {
                ArrayResize(tickets, count + 1);
                tickets[count++] = m_position.Ticket();
            }
        }
        for(int i = 0; i < count; i++) ExecuteClose(tickets[i], false);
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
        ulong tickets[];
        int count = 0;
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
            {
                ArrayResize(tickets, count + 1);
                tickets[count++] = m_position.Ticket();
            }
        }
        for(int i = 0; i < count; i++) ExecuteClose(tickets[i], false);
        return true;
    }
    return false;
}

void ExecuteOpen(ENUM_ORDER_TYPE type, double vol, double &price, double sl, double tp)
{
    for(int retry = 0; retry < 2; retry++)
    {
        if(type == ORDER_TYPE_BUY) { if(m_trade.Buy(vol, _Symbol, price, sl, tp)) break; }
        else                       { if(m_trade.Sell(vol, _Symbol, price, sl, tp)) break; }
        Sleep(100);
        price = SymbolInfoDouble(_Symbol, (type == ORDER_TYPE_BUY ? SYMBOL_ASK : SYMBOL_BID));
    }
}

void ExecuteClose(ulong ticket, bool track_loss = true)
{
    if(track_loss && m_position.SelectByTicket(ticket))
    {
        if(m_position.Profit() < 0)
            m_consecutive_losses++;
        else
            m_consecutive_losses = 0;
    }

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