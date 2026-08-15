//+------------------------------------------------------------------+
//|                                  XAUUSD_Trend_Hedge_V4.1.mq5     |
//|                         华尔街高级量化架构师定制 - 黄金顺势对冲系统 |
//|                               V4.1 加装无阻塞异步消息通讯指挥模块 |
//+------------------------------------------------------------------+
#property copyright "Wall Street Quant Architect"
#property link      ""
#property version   "4.10"

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

//--- 【参数分组：智能保本与追踪防线】 ---
input group "=== 智能保本与追踪防线 (V4核心) ==="
input bool     InpUseBreakEven      = true;     // 启用智能保本(锁定不亏钱)
input double   InpBreakEvenTrigger  = 1400;     // 保本触发距离(微点, 建议1400)
input double   InpBreakEvenProfit   = 150;      // 保本锁定利润(微点, 放在开仓价上方1.5美金防手续费)
input bool     InpUseTrailing       = true;     // 启用动态追踪止盈(让利润奔跑)
input double   InpTrailingDistance  = 2900;     // 追踪止盈距离(微点, 建议2900)
input double   InpTrailingStep      = 300;      // 追踪修改步长(微点, 防高频改单被服务器封禁)

//--- 【参数分组：趋势与震荡过滤引擎】 ---
input group "=== 趋势与震荡过滤引擎 ==="
input int      InpEmaFast           = 50;       // 快速EMA周期
input int      InpEmaSlow           = 200;      // 慢速EMA周期
input int      InpAdxPeriod         = 14;       // ADX周期 (判断趋势强度)
input double   InpAdxThreshold      = 20.0;     // ADX阈值 (严控开火权, 建议20)
input color    InpColorLongZone     = clrNavy;  // 多头区间背景色(蓝)
input color    InpColorShortZone    = clrMaroon;// 空头区间背景色(橙)

//--- 【参数分组：ATR加仓与物理防线】 ---
input group "=== ATR加仓与物理防线 ==="
input int      InpAtrPeriod         = 14;       // ATR周期
input double   InpAtrMultiplier     = 2.5;      // 动态加仓ATR乘数 (建议2.5)
input double   InpLotMultiplier     = 0.8;      // 加仓倍率(强制<=1.0, 递减加仓)
input double   InpStopLossPoints    = 1500;     // 物理硬止损(微点, 15美金)
input double   InpTakeProfitPoints  = 5000;     // 物理硬止盈(微点)

//--- 【参数分组：动态对冲极速解套参数】 ---
input group "=== 动态对冲极速解套参数 ==="
input double   InpHedgeCoverage     = 1.02;     // 跨向对冲安全覆盖倍率(只要回本就跑)
input double   InpSameSideLockProfit= 200.0;    // 同向对冲触发阈值(高频锁润)

//--- 【参数分组：环境与时段过滤】 ---
input group "=== 环境与时段过滤 ==="
input int      InpMaxSpread         = 80;       // 允许的最大点差(微点)
input bool     InpCloseOnFriday     = true;     // 周五收盘前强制清仓
input int      InpFridayCloseHour   = 21;       // 周五清仓时间(服务器小时)

//--- 【新增参数分组：消息指挥中心】 ---
input group "=== 消息指挥中心 (V4.1新增) ==="
input bool     InpEnablePushNotify  = true;     // 开启手机APP异步推送战报

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
int            m_current_zone = 0; 
string         m_msg_queue[]; // 异步消息缓冲池 (核心装甲)

//+------------------------------------------------------------------+
//| EA初始化函数                                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    if(InpMaxRiskPerTrade > 1.0 || InpMaxDailyDrawdown > 5.0 || InpLotMultiplier > 1.0)
    {
        Alert("🔴 警告：风控参数超过安全红线！"); return INIT_FAILED;
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

    // V4.1新增：开启1秒毫秒级定时器，由它在后台静默发送消息
    if(InpEnablePushNotify) EventSetTimer(1);

    Print("🟢 V4.1 异步指挥版启动成功！消息装甲已挂载。");
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
    IndicatorRelease(m_handle_ema_fast);
    IndicatorRelease(m_handle_ema_slow);
    IndicatorRelease(m_handle_adx);
    IndicatorRelease(m_handle_atr);
    ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrBlack); 
    EventKillTimer(); // 关闭定时器
}

//+------------------------------------------------------------------+
//| 每Tick执行主逻辑 (绝对不能放堵塞代码在这里)                       |
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
    ProcessTrailingAndBreakEven();
    ProcessLegacyProfits(); 
    ProcessCrossHedge();    
    ProcessSameSideHedge(); 

    if(IsNewBar()) CheckAndOpenPosition();
}

//+------------------------------------------------------------------+
//| V4.1新增核心：底层交易监听器 (OnTradeTransaction)                |
//| 说明：当开平仓真实发生并计入历史时，系统会瞬间捕捉，并推入异步队列  |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
    if(!InpEnablePushNotify) return;

    // 只捕捉"交易达成并记录"的瞬间
    if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
    {
        if(HistoryDealSelect(trans.deal))
        {
            string symbol = HistoryDealGetString(trans.deal, DEAL_SYMBOL);
            if(symbol != _Symbol) return; 

            long magic = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
            if(magic != 888888) return; // 必须是本系统的订单

            long deal_entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
            long deal_type  = HistoryDealGetInteger(trans.deal, DEAL_TYPE);
            double volume   = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
            double price    = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
            double profit   = HistoryDealGetDouble(trans.deal, DEAL_PROFIT);

            string msg = "📝 【V4.1 战报】 " + symbol + "\n";
            
            // 组装战报内容
            if(deal_entry == DEAL_ENTRY_IN) 
            {
                msg += (deal_type == DEAL_TYPE_BUY ? "🟢 狙击开多" : "🔴 狙击开空") + " " + DoubleToString(volume, 2) + "手\n";
                msg += "成交均价: " + DoubleToString(price, _Digits) + "\n";
            } 
            else if(deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_INOUT) 
            {
                msg += (deal_type == DEAL_TYPE_BUY ? "🟢 空单平仓" : "🔴 多单平仓") + " " + DoubleToString(volume, 2) + "手\n";
                msg += "平仓均价: " + DoubleToString(price, _Digits) + "\n";
                msg += (profit >= 0 ? "💰 落袋盈利: +$" : "🩸 截断亏损: -$") + DoubleToString(MathAbs(profit), 2) + "\n";
            }

            // 统计剩余兵力与粮草
            int current_pos = 0;
            double current_floating = 0;
            for(int i = PositionsTotal() - 1; i >= 0; i--)
            {
                if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol && m_position.Magic() == 888888)
                {
                    current_pos++;
                    current_floating += m_position.Profit();
                }
            }
            
            msg += "---\n";
            msg += "📊 当前阵地持仓: " + IntegerToString(current_pos) + " 单\n";
            msg += "🌊 阵地总浮盈亏: $" + DoubleToString(current_floating, 2) + "\n";
            msg += "🏦 基地可用净值: $" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2);

            // 将战报推入无阻塞缓冲池
            PushNotificationToQueue(msg);
        }
    }
}

//+------------------------------------------------------------------+
//| V4.1修正：缓冲池发报员 (OnTimer)                                 |
//| 说明：修复了枚举报错。现在直接尝试发送，失败则抛弃并报错提示。     |
//+------------------------------------------------------------------+
void OnTimer()
{
    int queue_size = ArraySize(m_msg_queue);
    if(queue_size > 0)
    {
        // 尝试发送队列中的第一封战报
        if(SendNotification(m_msg_queue[0]))
        {
            // 发送成功，将后续战报往前挪
            for(int i = 1; i < queue_size; i++) m_msg_queue[i-1] = m_msg_queue[i];
            ArrayResize(m_msg_queue, queue_size - 1);
        }
        else
        {
            // 发送失败（可能是没填手机ID，或网络拥堵）
            Print("❌ 战报发送失败！请确保MT5[工具]-[选项]-[通知]中已填入正确的ID。");
            
            // 强行丢弃这条发不出去的消息，防止后面的战报被堵死
            for(int i = 1; i < queue_size; i++) m_msg_queue[i-1] = m_msg_queue[i];
            ArrayResize(m_msg_queue, queue_size - 1);
        }
    }
}
void PushNotificationToQueue(string msg)
{
    int size = ArraySize(m_msg_queue);
    ArrayResize(m_msg_queue, size + 1);
    m_msg_queue[size] = msg;
}

//+------------------------------------------------------------------+
//| 以下为V4原版逻辑 (包含智能保本、跨向对冲等核心算法)                |
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
                if(InpUseBreakEven && (bid - open_price) >= (InpBreakEvenTrigger * point))
                {
                    double be_price = open_price + (InpBreakEvenProfit * point);
                    if(current_sl < be_price) { new_sl = be_price; need_modify = true; }
                }
                if(InpUseTrailing && (bid - open_price) >= (InpTrailingDistance * point))
                {
                    double trail_price = bid - (InpTrailingDistance * point);
                    if(trail_price > current_sl + (InpTrailingStep * point)) { new_sl = trail_price; need_modify = true; }
                }
            }
            else if(type == POSITION_TYPE_SELL)
            {
                if(InpUseBreakEven && (open_price - ask) >= (InpBreakEvenTrigger * point))
                {
                    double be_price = open_price - (InpBreakEvenProfit * point);
                    if(current_sl > be_price || current_sl == 0.0) { new_sl = be_price; need_modify = true; }
                }
                if(InpUseTrailing && (open_price - ask) >= (InpTrailingDistance * point))
                {
                    double trail_price = ask + (InpTrailingDistance * point);
                    if(trail_price < current_sl - (InpTrailingStep * point) || current_sl == 0.0) { new_sl = trail_price; need_modify = true; }
                }
            }
            if(need_modify) m_trade.PositionModify(ticket, NormalizeDouble(new_sl, _Digits), current_tp);
        }
    }
}

void UpdateMarketZone()
{
    double ema_fast[1], ema_slow[1], adx[1];
    if(CopyBuffer(m_handle_ema_fast, 0, 1, 1, ema_fast) <= 0 || 
       CopyBuffer(m_handle_ema_slow, 0, 1, 1, ema_slow) <= 0 ||
       CopyBuffer(m_handle_adx, 0, 1, 1, adx) <= 0) return;

    if(adx[0] < InpAdxThreshold) { m_current_zone = 0; ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrDimGray); return; }
    if(ema_fast[0] > ema_slow[0]) { m_current_zone = 1; ChartSetInteger(0, CHART_COLOR_BACKGROUND, InpColorLongZone); }
    else if(ema_fast[0] < ema_slow[0]) { m_current_zone = -1; ChartSetInteger(0, CHART_COLOR_BACKGROUND, InpColorShortZone); }
}

void ProcessCrossHedge()
{
    ulong worst_counter_ticket = 0; double worst_counter_loss = 0.0;
    ulong best_trend_ticket = 0; double best_trend_profit = 0.0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            double profit = m_position.Profit();
            if(m_current_zone == 1) 
            {
                if(m_position.PositionType() == POSITION_TYPE_BUY && profit > best_trend_profit) { best_trend_profit = profit; best_trend_ticket = m_position.Ticket(); }
                if(m_position.PositionType() == POSITION_TYPE_SELL && profit < worst_counter_loss) { worst_counter_loss = profit; worst_counter_ticket = m_position.Ticket(); }
            }
            else if(m_current_zone == -1) 
            {
                if(m_position.PositionType() == POSITION_TYPE_SELL && profit > best_trend_profit) { best_trend_profit = profit; best_trend_ticket = m_position.Ticket(); }
                if(m_position.PositionType() == POSITION_TYPE_BUY && profit < worst_counter_loss) { worst_counter_loss = profit; worst_counter_ticket = m_position.Ticket(); }
            }
        }
    }
    if(worst_counter_ticket > 0 && best_trend_ticket > 0 && best_trend_profit >= MathAbs(worst_counter_loss) * InpHedgeCoverage)
    {
        ExecuteClose(worst_counter_ticket); ExecuteClose(best_trend_ticket);
    }
}

void ProcessSameSideHedge()
{
    ulong largest_lot_ticket = 0; double largest_lot = 0; int same_side_count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            if((m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_BUY) || (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_SELL))
            {
                same_side_count++;
                if(m_position.Volume() > largest_lot && m_position.Profit() > InpSameSideLockProfit) { largest_lot = m_position.Volume(); largest_lot_ticket = m_position.Ticket(); }
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
            if((m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_SELL && m_position.Profit() > 0) ||
               (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_BUY && m_position.Profit() > 0))
                ExecuteClose(m_position.Ticket());
        }
    }
}

void CheckAndOpenPosition()
{
    if(m_current_zone == 0 || SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;
    int trend_positions = 0; double last_entry_price = 0.0; double last_lot_size = 0.0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol)
        {
            if((m_current_zone == 1 && m_position.PositionType() == POSITION_TYPE_BUY) || (m_current_zone == -1 && m_position.PositionType() == POSITION_TYPE_SELL))
            {
                trend_positions++;
                if(trend_positions == 1) { last_entry_price = m_position.PriceOpen(); last_lot_size = m_position.Volume(); }
            }
        }
    }
    if(trend_positions >= InpMaxPositions) return;

    if(trend_positions > 0)
    {
        double atr[1]; if(CopyBuffer(m_handle_atr, 0, 1, 1, atr) <= 0) return;
        double dynamic_distance = atr[0] * InpAtrMultiplier;
        double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        if((m_current_zone == 1 && (ask - last_entry_price) < dynamic_distance) || (m_current_zone == -1 && (last_entry_price - bid) < dynamic_distance)) return;
    }

    double target_lot = GetProperLotSize();
    if(trend_positions > 0) target_lot = NormalizeDouble(last_lot_size * InpLotMultiplier, 2); 
    
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    if(m_current_zone == 1) ExecuteOpen(ORDER_TYPE_BUY, target_lot, ask, ask - InpStopLossPoints * point, ask + InpTakeProfitPoints * point);
    else if(m_current_zone == -1) ExecuteOpen(ORDER_TYPE_SELL, target_lot, bid, bid + InpStopLossPoints * point, bid - InpTakeProfitPoints * point);
}

double GetProperLotSize()
{
    if(!InpUseDynamicLot) return InpFixedLotSize; 
    double loss_per_lot = (InpStopLossPoints * SymbolInfoDouble(_Symbol, SYMBOL_POINT) / SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE)) * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    if(loss_per_lot == 0) return InpFixedLotSize; 
    double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    double raw_lot = MathFloor((AccountInfoDouble(ACCOUNT_EQUITY) * (InpMaxRiskPerTrade / 100.0) / loss_per_lot) / step) * step;
    return MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), MathMin(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX), raw_lot));
}

bool CheckDailyFuse()
{
    if(m_daily_fuse_active) return true; 
    if((m_start_of_day_equity - AccountInfoDouble(ACCOUNT_EQUITY)) / m_start_of_day_equity * 100.0 >= InpMaxDailyDrawdown || m_consecutive_losses >= InpMaxConsecutiveLoss)
    {
        m_daily_fuse_active = true;
        for(int i = PositionsTotal() - 1; i >= 0; i--) if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol) ExecuteClose(m_position.Ticket());
        return true;
    }
    return false;
}

bool CheckFridayClose()
{
    MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
    if(InpCloseOnFriday && dt.day_of_week == 5 && dt.hour >= InpFridayCloseHour)
    {
        for(int i = PositionsTotal() - 1; i >= 0; i--) if(m_position.SelectByIndex(i) && m_position.Symbol() == _Symbol) ExecuteClose(m_position.Ticket());
        return true;
    }
    return false;
}

void ExecuteOpen(ENUM_ORDER_TYPE type, double vol, double price, double sl, double tp)
{
    for(int retry = 0; retry < 2; retry++)
    {
        if(type == ORDER_TYPE_BUY ? m_trade.Buy(vol, _Symbol, price, sl, tp) : m_trade.Sell(vol, _Symbol, price, sl, tp)) break;
        Sleep(100); SymbolInfoDouble(_Symbol, (type == ORDER_TYPE_BUY ? SYMBOL_ASK : SYMBOL_BID), price);
    }
}

void ExecuteClose(ulong ticket) { for(int retry = 0; retry < 2; retry++) { if(m_trade.PositionClose(ticket)) break; Sleep(100); } }

bool IsNewBar()
{
    static datetime last_time = 0; datetime current_time = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_time != last_time) { last_time = current_time; return true; }
    return false;
}
//+------------------------------------------------------------------+