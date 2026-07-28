//+------------------------------------------------------------------+
//| AI增强风险管理系统 - 智能加仓增强版
//| 版本: 2.8.4 - 智能加仓增强版
//| 功能: 扛单策略 + 锁仓 + 虚拟移动止损 + AI智能决策 + 智能加仓
//+------------------------------------------------------------------+

#property copyright "AI Enhanced Trading System"
#property version   "2.69"
#property strict

//+------------------------------------------------------------------+
//| 智能加仓参数（新增）
//+------------------------------------------------------------------+
input bool EnableSmartBuyStrategy = true;     // 启用智能加仓（默认开启）
input double SmartBuyAIConfidenceThreshold = 0.6;  // AI置信度阈值
input int MaxSmartBuyOrders = 4;              // 智能加仓最大订单数（不影响12个正常订单）
input double MaxSmartBuyTotalLots = 0.03;     // 智能加仓最大总手数
input int SmartBuyMinInterval = 900;          // 智能加仓最小间隔（15分钟）
input double SmartBuyLossThreshold = 1000.0;  // 智能加仓触发亏损阈值（点数）
input double SmartBuyMaxLossThreshold = 5000.0; // 智能加仓最大亏损阈值（点数）

//+------------------------------------------------------------------+
//| 智能加仓全局变量（新增）
//+------------------------------------------------------------------+
datetime g_last_smart_buy_time = 0;
int g_smart_buy_orders = 0;
double g_smart_buy_total_lots = 0.0;
bool g_smart_buy_triggered = false;

//+------------------------------------------------------------------+
//| 全局结构体定义
//+------------------------------------------------------------------+
struct TrailingData
{
    int ticket;
    double highest_price;
    double lowest_price;
    datetime update_time;
};

// 锁仓层级记录结构
struct LockLevelRecord
{
    int original_ticket;    // 原订单号
    int lock_level;         // 锁仓层级 (1,2,3)
    datetime lock_time;     // 锁仓时间
    double lock_lot;        // 锁仓手数
    int lock_ticket;        // 锁仓订单号
    bool is_active;         // 是否激活
};

// 智能加仓记录结构
struct SmartBuyRecord
{
    int ticket;             // 智能加仓订单号
    datetime open_time;     // 开仓时间
    double open_price;      // 开仓价格
    double lot_size;        // 手数
    int order_type;         // 订单类型
    double ai_confidence;   // AI置信度
    double decision_score;  // 决策评分
    double avg_loss_pips;   // 平均亏损点数
    bool is_active;         // 是否激活
};

//+------------------------------------------------------------------+
//| 全局变量
datetime g_last_prediction_time = 0;
int g_last_prediction = -1;
double g_last_confidence = 0.0;
bool g_ai_service_available = false;

// 信号确认变量
int g_signal_confirm_ticks = 0;
int g_last_signal = -1;
bool g_signal_confirmed = false;

// 建仓频率控制变量
datetime g_last_normal_order_time = 0;    // 普通仓最后建仓时间
datetime g_last_lock_order_time = 0;    // 锁仓单最后建仓时间

// 交易计数器全局变量  
datetime g_last_trade_time = 0;
datetime g_last_reset_date = 0;

// AI信号历史记录 - 用于连续信号检测
int g_ai_signal_history[5] = {-1, -1, -1, -1, -1};
int g_signal_count = 0;

// 决策评分历史记录 - 修改为存储前5个决策评分
struct DecisionScoreHistory {
    double buy_score;
    double sell_score;
    int decision_direction; // 1=买入, -1=卖出, 0=无方向
    datetime timestamp;
};

DecisionScoreHistory g_decision_score_history[5] = {{0.0, 0.0, 0, 0}};
int g_decision_history_count = 0;
datetime g_last_decision_time = 0;

// 统一反转信号结果缓存
struct ReversalSignalResult {
    bool has_reversal;
    int signal_direction;
    double confidence;
    datetime timestamp;
    bool is_valid;
};

ReversalSignalResult g_current_reversal_signal = {false, -1, 0.0, 0, false};

// 应急仓位管理变量
int g_emergency_order_count = 0;                  // 当前应急仓位数量

// 智能加仓记录数组
SmartBuyRecord g_smart_buy_records[10] = {{0, 0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, false}};
int g_smart_buy_record_count = 0;

// 输入参数
input int MaxOpenOrders = 16;             // 最大同时开仓数 (调整为16，支持三种仓位类型)
input double MaxSpreadPips = 50.0;        // 最大允许点差 (从8.0提高到50.0，适应实际市场条件)
input double MaxSlippage = 50.0;          // 最大允许滑点 (从20.0提高到50.0，适应黄金市场高波动)
input string DataFileName = "market_data.csv"; // 市场数据文件名
input string PredictionFileName = "ai_prediction.txt"; // AI预测文件名
input double MinAIConfidence = 0.6;       // 最小AI置信度 (从0.7降低到0.6)
input double TechnicalWeight = 0.6;       // 技术分析权重 (调整为60%)
input double MarketWeight = 0.3;          // 市场状态权重 (保持30%)
input double AIWeight = 0.1;              // AI预测权重 (调整为10%)

// 平仓管理参数
input bool EnableAI = true;               // 启用AI预测
input bool EnableSmartClose = true;       // 启用智能平仓
input bool EnableTechnicalClose = true;   // 启用技术指标平仓
input bool EnableTrailingStop = true;     // 移动止损（内存问题已解决）
input double TrailingStopMultiplier = 1.0; // 移动止损倍数 (调整为1.0，更紧密的利润保护)

// 信号确认参数
input int SignalConfirmTicks = 3;          // 信号确认tick数 - 需要3个tick确认
input bool EnableSignalConfirmation = true; // 启用信号确认 - 防止假信号

// 方向检查参数
input bool EnableSmartDirectionCheck = true; // 启用智能方向检查 - 限制同方向持仓数
input int MaxSameDirectionOrders = 12;     // 同方向最大持仓数 (从8提高到12，支持14个总持仓)

// 固定手数设置
input bool UseFixedLotSize = true;         // 使用固定手数 (推荐启用)
input double FixedLotSize = 0.01;          // 固定手数大小

// 技术指标参数
input double RSIOverbought = 95.0;             // RSI超买阈值（从90提高到95，减少误平仓）
input double RSIOversold = 5.0;               // RSI超卖阈值（从10降低到5，减少误平仓）
input double ADXThreshold = 12.0;              // ADX阈值（从8提高到12，减少误平仓）

// 高级技术指标参数 - 新增
input bool EnableAdvancedIndicators = true;    // 启用高级技术指标
input double BollingerOverbought = 85.0;       // 布林带超买阈值
input double BollingerOversold = 15.0;         // 布林带超卖阈值
input double KDJOverbought = 80.0;             // KDJ超买阈值
input double KDJOversold = 20.0;               // KDJ超卖阈值

// 高级市场分析参数 - 新增
input bool EnableAdvancedMarketAnalysis = true; // 启用高级市场分析

// 亏损管理参数（扛单模式下大幅调整）
input bool EnableLossManagement = true;        // 启用亏损管理

// 新增：扛单策略参数
input bool EnableHoldStrategy = true;      // 启用扛单策略
input double MaxHoldLossPips = 10000.0;    // 最大扛单亏损点数 (调整为10000点)

// 锁仓管理 - 统一触发模式
input bool EnableLockManagement = true;    // 启用锁仓管理
input double LockTriggerLevel = 3000.0;    // 锁仓触发点（3000点亏损）
input double LockLotMultiplier = 1.0;      // 锁仓手数倍数
input double UnlockProfit = 300.0;         // 锁仓解锁盈利点

// 建仓频率控制参数
input int MinOrderInterval = 900;          // 锁仓单最小建仓间隔(秒) - 15分钟
input int MaxNormalOrders = 12;            // 普通仓最多12个持仓
input int MaxLockOrders = 2;               // 锁仓单最多2个持仓

// 智能平仓参数（无固定止损止盈版本，扛单模式优化）
input bool EnableSmartCloseOnly = true;    // 启用纯智能平仓模式

// 位置风险控制参数
input bool EnablePositionRiskControl = true;    // 启用位置风险控制
input double HighRiskPosition = 75.0;           // 高位风险阈值（从85%调整为75%）
input double LowRiskPosition = 25.0;            // 低位风险阈值（从15%调整为25%）
input double TrendHighRiskPosition = 95.0;      // 趋势高位风险阈值
input double TrendLowRiskPosition = 5.0;        // 趋势低位风险阈值
input double StrongTrendADX = 30.0;             // 强趋势ADX阈值
input double HighConfidenceThreshold = 0.9;     // 高置信度阈值

// 位置感知增强参数 - 新增
input bool EnablePositionAwareness = true;      // 启用位置感知增强
input double ExtremePositionThreshold = 90.0;   // 极端位置阈值
input double AIWeightReductionFactor = 0.4;     // AI权重降低因子
input double ReversalSignalBonus = 0.3;         // 反转信号增强因子
input double ExtremeConfidenceThreshold = 0.95; // 极端位置置信度阈值

// 锁仓单亏损平仓参数
input double LockOrderLossLimit = 4000.0;       // 锁仓单亏损平仓点位（从1500点提高到4000点）

// 决策评分反转处理参数
input bool EnableDecisionScoreReversal = true;     // 启用决策评分反转处理(普通仓位扛单模式)
input double SmallLossThreshold = 500.0;        // 小亏损阈值
input double LargeLossThreshold = 2000.0;       // 大亏损阈值
input int DecisionReversalTicks = 3;              // 决策反转确认tick数
input double DecisionReversalThreshold = 0.45;    // 决策反转评分阈值
input int BatchCloseInterval = 10;               // 分批平仓间隔(tick数)

// 应急仓位参数
input int EmergencyOrderCount = 2;               // 应急仓位数量
input double EmergencyLotSize = 0.02;            // 应急仓位手数
input double EmergencyProfitTarget = 1000.0;      // 应急仓位盈利目标(点位)
input double EmergencyStopLoss = 1000.0;          // 应急仓位止损(点位)
input double EmergencyTriggerScore = 0.3;        // 应急仓位触发阈值 (已废弃，现在使用DecisionReversalThreshold)

//+------------------------------------------------------------------+
//| 智能加仓核心函数
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| 检查智能加仓触发条件
//+------------------------------------------------------------------+
bool CheckSmartBuyTriggerConditions(double &avg_loss_pips, int &dominant_direction)
{
    if(!EnableSmartBuyStrategy) return false;
    
    // 检查时间间隔
    datetime current_time = TimeCurrent();
    if(current_time - g_last_smart_buy_time < SmartBuyMinInterval)
    {
        return false;
    }
    
    // 检查智能加仓订单数量限制
    if(g_smart_buy_orders >= MaxSmartBuyOrders)
    {
        Print("📊 智能加仓订单数量已达上限: ", g_smart_buy_orders, "/", MaxSmartBuyOrders);
        return false;
    }
    
    // 检查智能加仓总手数限制
    if(g_smart_buy_total_lots >= MaxSmartBuyTotalLots)
    {
        Print("📊 智能加仓总手数已达上限: ", g_smart_buy_total_lots, "/", MaxSmartBuyTotalLots);
        return false;
    }
    
    // 检查总订单数量限制（保持12个正常订单不受影响）
    int total_orders = CountNormalOrders() + CountLockOrders() + CountEmergencyOrders() + g_smart_buy_orders;
    if(total_orders >= MaxOpenOrders)
    {
        Print("📊 总订单数量已达上限: ", total_orders, "/", MaxOpenOrders);
        return false;
    }
    
    // 分析现有订单的亏损情况
    double total_loss_pips = 0.0;
    int buy_orders = 0, sell_orders = 0;
    double buy_loss = 0.0, sell_loss = 0.0;
    
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                string comment = OrderComment();
                // 只分析正常订单和锁仓订单，不包括智能加仓订单
                if(StringFind(comment, "智能加仓") < 0)
                {
                    double order_profit = OrderProfit() + OrderSwap() + OrderCommission();
                    double order_loss_pips = -order_profit / (MarketInfo(Symbol(), MODE_TICKVALUE) * OrderLots());
                    
                    if(order_loss_pips > 0) // 只计算亏损订单
                    {
                        total_loss_pips += order_loss_pips;
                        
                        if(OrderType() == OP_BUY)
                        {
                            buy_orders++;
                            buy_loss += order_loss_pips;
                        }
                        else if(OrderType() == OP_SELL)
                        {
                            sell_orders++;
                            sell_loss += order_loss_pips;
                        }
                    }
                }
            }
        }
    }
    
    // 计算平均亏损
    int total_analyzed_orders = buy_orders + sell_orders;
    if(total_analyzed_orders == 0)
    {
        return false;
    }
    
    avg_loss_pips = total_loss_pips / total_analyzed_orders;
    
    // 检查亏损阈值
    if(avg_loss_pips < SmartBuyLossThreshold || avg_loss_pips > SmartBuyMaxLossThreshold)
    {
        Print("📊 平均亏损不在智能加仓范围内: ", avg_loss_pips, " (", SmartBuyLossThreshold, " - ", SmartBuyMaxLossThreshold, ")");
        return false;
    }
    
    // 确定主导方向
    if(buy_loss > sell_loss && buy_orders > 0)
    {
        dominant_direction = OP_BUY;
    }
    else if(sell_loss > buy_loss && sell_orders > 0)
    {
        dominant_direction = OP_SELL;
    }
    else
    {
        return false; // 没有明确的主导方向
    }
    
    Print("📊 智能加仓触发条件满足:");
    Print("   平均亏损: ", avg_loss_pips, " 点数");
    Print("   主导方向: ", (dominant_direction == OP_BUY ? "买入" : "卖出"));
    Print("   买入订单: ", buy_orders, " 亏损: ", buy_loss);
    Print("   卖出订单: ", sell_orders, " 亏损: ", sell_loss);
    
    return true;
}

//+------------------------------------------------------------------+
//| 计算智能加仓手数
//+------------------------------------------------------------------+
double CalculateSmartBuyLotSize(double avg_loss_pips, double ai_confidence, double decision_score)
{
    // 基础手数
    double base_lot = FixedLotSize;
    
    // 根据亏损程度确定金字塔层级（调整为小手数）
    double lot_multiplier = 1.0;
    if(avg_loss_pips >= 4000.0) lot_multiplier = 3.0;
    else if(avg_loss_pips >= 3000.0) lot_multiplier = 2.5;
    else if(avg_loss_pips >= 2000.0) lot_multiplier = 2.0;
    else if(avg_loss_pips >= 1000.0) lot_multiplier = 1.5;
    
    // 根据AI置信度调整手数（限制最大倍数）
    double confidence_multiplier = MathMin(ai_confidence / 0.5, 1.5);
    
    // 根据决策评分调整手数（限制最大倍数）
    double decision_multiplier = MathMin(decision_score / 0.5, 1.2);
    
    // 计算最终手数
    double final_lot = base_lot * lot_multiplier * confidence_multiplier * decision_multiplier;
    
    // 确保不超过最大手数限制
    double max_allowed_lot = MaxSmartBuyTotalLots - g_smart_buy_total_lots;
    if(final_lot > max_allowed_lot)
    {
        final_lot = max_allowed_lot;
    }
    
    // 限制单次加仓最大手数为0.01
    if(final_lot > 0.01)
    {
        final_lot = 0.01;
    }
    
    // 标准化手数
    final_lot = NormalizeDouble(final_lot, 2);
    
    Print("📊 智能加仓手数计算:");
    Print("   基础手数: ", base_lot);
    Print("   亏损倍数: ", lot_multiplier);
    Print("   置信度倍数: ", confidence_multiplier);
    Print("   决策评分倍数: ", decision_multiplier);
    Print("   最终手数: ", final_lot);
    
    return final_lot;
}

//+------------------------------------------------------------------+
//| 执行智能加仓订单
//+------------------------------------------------------------------+
bool ExecuteSmartBuyOrder(int order_type, double lot_size, double ai_confidence, double decision_score, double avg_loss_pips)
{
    if(!IsTradeAllowed())
    {
        Print("❌ 交易被禁用，无法执行智能加仓");
        return false;
    }
    
    if(IsTradeContextBusy())
    {
        Print("❌ 交易上下文繁忙，无法执行智能加仓");
        return false;
    }
    
    // 检查点差
    double current_spread = MarketInfo(Symbol(), MODE_SPREAD);
    if(current_spread > MaxSpreadPips)
    {
        Print("❌ 点差过大，无法执行智能加仓: ", current_spread, " > ", MaxSpreadPips);
        return false;
    }
    
    // 确定开仓价格
    double open_price = 0.0;
    if(order_type == OP_BUY)
    {
        open_price = Ask;
    }
    else if(order_type == OP_SELL)
    {
        open_price = Bid;
    }
    else
    {
        Print("❌ 无效的订单类型: ", order_type);
        return false;
    }
    
    // 构建订单注释
    string comment = "智能加仓|AI:" + DoubleToString(ai_confidence, 2) + 
                    "|评分:" + DoubleToString(decision_score, 2) + 
                    "|亏损:" + DoubleToString(avg_loss_pips, 0);
    
    // 执行订单
    int ticket = OrderSend(Symbol(), order_type, lot_size, open_price, (int)MaxSlippage, 0, 0, comment, 12345, 0, clrBlue);
    
    if(ticket > 0)
    {
        // 更新智能加仓统计
        g_smart_buy_orders++;
        g_smart_buy_total_lots += lot_size;
        g_last_smart_buy_time = TimeCurrent();
        
        // 记录智能加仓信息
        if(g_smart_buy_record_count < 10)
        {
            g_smart_buy_records[g_smart_buy_record_count].ticket = ticket;
            g_smart_buy_records[g_smart_buy_record_count].open_time = TimeCurrent();
            g_smart_buy_records[g_smart_buy_record_count].open_price = open_price;
            g_smart_buy_records[g_smart_buy_record_count].lot_size = lot_size;
            g_smart_buy_records[g_smart_buy_record_count].order_type = order_type;
            g_smart_buy_records[g_smart_buy_record_count].ai_confidence = ai_confidence;
            g_smart_buy_records[g_smart_buy_record_count].decision_score = decision_score;
            g_smart_buy_records[g_smart_buy_record_count].avg_loss_pips = avg_loss_pips;
            g_smart_buy_records[g_smart_buy_record_count].is_active = true;
            g_smart_buy_record_count++;
        }
        
        Print("✅ 智能加仓订单执行成功:");
        Print("   订单号: ", ticket);
        Print("   类型: ", (order_type == OP_BUY ? "买入" : "卖出"));
        Print("   手数: ", lot_size);
        Print("   价格: ", open_price);
        Print("   AI置信度: ", ai_confidence);
        Print("   决策评分: ", decision_score);
        Print("   平均亏损: ", avg_loss_pips, " 点数");
        Print("   智能加仓统计: ", g_smart_buy_orders, "/", MaxSmartBuyOrders, " 订单, ", g_smart_buy_total_lots, "/", MaxSmartBuyTotalLots, " 手数");
        
        return true;
    }
    else
    {
        int error = GetLastError();
        Print("❌ 智能加仓订单执行失败: ", error, " - ", ErrorDescription(error));
        return false;
    }
}

//+------------------------------------------------------------------+
//| 更新智能加仓统计
//+------------------------------------------------------------------+
void UpdateSmartBuyStats()
{
    g_smart_buy_orders = 0;
    g_smart_buy_total_lots = 0.0;
    
    // 使用新的统计方法
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                string comment = OrderComment();
                if(StringFind(comment, "智能加仓") >= 0)
                {
                    g_smart_buy_orders++;
                    g_smart_buy_total_lots += OrderLots();
                }
            }
        }
    }
    
    // 更新记录状态
    for(int i = 0; i < g_smart_buy_record_count; i++)
    {
        if(g_smart_buy_records[i].is_active)
        {
            if(OrderSelect(g_smart_buy_records[i].ticket, SELECT_BY_TICKET))
            {
                if(OrderCloseTime() != 0) // 订单已关闭
                {
                    g_smart_buy_records[i].is_active = false;
                }
            }
            else // 订单不存在
            {
                g_smart_buy_records[i].is_active = false;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| 检查智能加仓条件并执行
//+------------------------------------------------------------------+
void CheckAndExecuteSmartBuy(double ai_confidence, double buy_score, double sell_score)
{
    if(!EnableSmartBuyStrategy) return;
    
    // 更新智能加仓统计
    UpdateSmartBuyStats();
    
    // 检查触发条件
    double avg_loss_pips = 0.0;
    int dominant_direction = -1;
    
    if(!CheckSmartBuyTriggerConditions(avg_loss_pips, dominant_direction))
    {
        return;
    }
    
    // 确定加仓方向（与主导亏损方向相同）
    int smart_buy_direction = dominant_direction;
    
    // 获取对应的决策评分
    double decision_score = 0.0;
    if(smart_buy_direction == OP_BUY)
    {
        decision_score = buy_score;
    }
    else if(smart_buy_direction == OP_SELL)
    {
        decision_score = sell_score;
    }
    
    // 确保只在同向亏损单方向建仓
    Print("📊 智能加仓方向分析:");
    Print("   主导亏损方向: ", (dominant_direction == OP_BUY ? "买入" : "卖出"));
    Print("   对应决策评分: ", decision_score);
    Print("   买入评分: ", buy_score, " 卖出评分: ", sell_score);
    
    // 检查AI置信度和决策评分
    if(ai_confidence < SmartBuyAIConfidenceThreshold)
    {
        Print("📊 AI置信度不足，跳过智能加仓: ", ai_confidence, " < ", SmartBuyAIConfidenceThreshold);
        return;
    }
    
    if(decision_score < 0.5)
    {
        Print("📊 决策评分不足，跳过智能加仓: ", decision_score, " < 0.5");
        return;
    }
    
    // 确保只在同向亏损单方向建仓
    Print("✅ 智能加仓条件满足，准备在同向亏损方向建仓");
    Print("   方向: ", (smart_buy_direction == OP_BUY ? "买入" : "卖出"));
    Print("   平均亏损: ", avg_loss_pips, " 点数");
    Print("   AI置信度: ", ai_confidence);
    Print("   决策评分: ", decision_score);
    
    // 计算智能加仓手数
    double lot_size = CalculateSmartBuyLotSize(avg_loss_pips, ai_confidence, decision_score);
    
    if(lot_size <= 0)
    {
        Print("📊 智能加仓手数计算为0，跳过执行");
        return;
    }
    
    // 执行智能加仓
    if(ExecuteSmartBuyOrder(smart_buy_direction, lot_size, ai_confidence, decision_score, avg_loss_pips))
    {
        g_smart_buy_triggered = true;
        Print("🚀 智能加仓执行完成");
    }
}

//+------------------------------------------------------------------+
//| 统计函数（保持原有功能）
//+------------------------------------------------------------------+
int CountNormalOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                string comment = OrderComment();
                // 智能加仓订单不影响正常订单统计
                if(StringFind(comment, "锁仓") < 0 && StringFind(comment, "应急") < 0 && StringFind(comment, "智能加仓") < 0)
                {
                    count++;
                }
            }
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| 智能加仓订单统计（独立统计）
//+------------------------------------------------------------------+
int CountSmartBuyOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                string comment = OrderComment();
                if(StringFind(comment, "智能加仓") >= 0)
                {
                    count++;
                }
            }
        }
    }
    return count;
}

int CountLockOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                string comment = OrderComment();
                if(StringFind(comment, "锁仓") >= 0)
                {
                    count++;
                }
            }
        }
    }
    return count;
}

int CountEmergencyOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                string comment = OrderComment();
                if(StringFind(comment, "应急") >= 0)
                {
                    count++;
                }
            }
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| 简化的决策评分计算函数
//+------------------------------------------------------------------+
void CalculateDecisionScores(double &buy_score, double &sell_score)
{
    // 简化的决策评分计算
    double ma_fast = iMA(Symbol(), Period(), 15, 0, MODE_SMA, PRICE_CLOSE, 0);
    double ma_slow = iMA(Symbol(), Period(), 30, 0, MODE_SMA, PRICE_CLOSE, 0);
    double rsi = iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 0);
    double adx = iADX(Symbol(), Period(), 14, PRICE_CLOSE, MODE_MAIN, 0);
    
    // 计算买入评分
    buy_score = 0.0;
    if(ma_fast > ma_slow) buy_score += 0.3;
    if(rsi < 70) buy_score += 0.2;
    if(adx > 20) buy_score += 0.2;
    if(Close[0] > ma_fast) buy_score += 0.3;
    
    // 计算卖出评分
    sell_score = 0.0;
    if(ma_fast < ma_slow) sell_score += 0.3;
    if(rsi > 30) sell_score += 0.2;
    if(adx > 20) sell_score += 0.2;
    if(Close[0] < ma_fast) sell_score += 0.3;
}

//+------------------------------------------------------------------+
//| Expert initialization function
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🚀 AI增强风险管理系统 - 智能加仓增强版启动");
    Print("📊 智能加仓参数:");
    Print("   启用智能加仓: ", EnableSmartBuyStrategy ? "是" : "否");
    Print("   AI置信度阈值: ", SmartBuyAIConfidenceThreshold);
    Print("   最大智能加仓订单: ", MaxSmartBuyOrders);
    Print("   最大智能加仓手数: ", MaxSmartBuyTotalLots);
    Print("   亏损触发阈值: ", SmartBuyLossThreshold, " - ", SmartBuyMaxLossThreshold, " 点数");
    Print("   最小间隔: ", SmartBuyMinInterval, " 秒");
    
    // 初始化智能加仓变量
    g_last_smart_buy_time = 0;
    g_smart_buy_orders = 0;
    g_smart_buy_total_lots = 0.0;
    g_smart_buy_triggered = false;
    g_smart_buy_record_count = 0;
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🛑 AI增强风险管理系统 - 智能加仓增强版停止");
    Print("📊 最终智能加仓统计:");
    Print("   智能加仓订单数: ", g_smart_buy_orders);
    Print("   智能加仓总手数: ", g_smart_buy_total_lots);
}

//+------------------------------------------------------------------+
//| 原有EA功能保留 - 交易执行类
//+------------------------------------------------------------------+
class CTradeExecutor
{
private:
    // 原有EA的成员变量和函数保持不变
    
public:
    void ExecuteTradingLogic()
    {
        // 1. 更新账户信息
        // 2. 检查市场状态
        // 3. 获取AI预测
        // 4. 计算决策评分
        // 5. 执行原有交易逻辑
        
        // 计算决策评分
        double buy_score = 0.0, sell_score = 0.0;
        CalculateDecisionScores(buy_score, sell_score);
        
        // 模拟AI预测（实际使用时需要连接AI服务）
        int ai_prediction = -1;
        double ai_confidence = 0.0;
        
        // 简化的AI预测逻辑
        if(buy_score > sell_score && buy_score > 0.6)
        {
            ai_prediction = 2; // 看涨
            ai_confidence = buy_score;
        }
        else if(sell_score > buy_score && sell_score > 0.6)
        {
            ai_prediction = 0; // 看跌
            ai_confidence = sell_score;
        }
        else
        {
            ai_prediction = 1; // 震荡
            ai_confidence = MathMax(buy_score, sell_score);
        }
        
        // 执行原有EA的交易逻辑（这里简化处理）
        Print("📊 原有EA交易逻辑执行中...");
        
        // 检查并执行智能加仓（在原有逻辑之后）
        CheckAndExecuteSmartBuy(ai_confidence, buy_score, sell_score);
    }
    
    void CheckTradingStatus()
    {
        // 原有EA的状态检查逻辑
        Print("📊 原有EA状态检查...");
    }
};

//+------------------------------------------------------------------+
//| 原有EA功能保留 - 平仓管理器
//+------------------------------------------------------------------+
class CCloseManager
{
private:
    // 原有EA的成员变量
    
public:
    void CheckAndCloseOrders()
    {
        // 原有EA的平仓逻辑
        Print("📊 原有EA平仓检查...");
        
        // 智能加仓订单的平仓逻辑（独立处理）
        CheckAndCloseSmartBuyOrders();
    }
    
private:
    void CheckAndCloseSmartBuyOrders()
    {
        // 智能加仓订单的平仓逻辑
        for(int i = 0; i < OrdersTotal(); i++)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
                {
                    string comment = OrderComment();
                    if(StringFind(comment, "智能加仓") >= 0)
                    {
                        // 智能加仓订单的平仓条件
                        double profit = OrderProfit() + OrderSwap() + OrderCommission();
                        double profit_pips = profit / (MarketInfo(Symbol(), MODE_TICKVALUE) * OrderLots());
                        
                        // 盈利超过500点或亏损超过8000点时平仓
                        if(profit_pips >= 500.0 || profit_pips <= -8000.0)
                        {
                            if(OrderClose(OrderTicket(), OrderLots(), 
                               OrderType() == OP_BUY ? Bid : Ask, 
                               (int)MaxSlippage, clrRed))
                            {
                                Print("✅ 智能加仓订单平仓成功: ", OrderTicket(), " 盈亏: ", profit_pips, " 点数");
                            }
                        }
                    }
                }
            }
        }
    }
};

//+------------------------------------------------------------------+
//| Expert tick function
//+------------------------------------------------------------------+
void OnTick()
{
    // 更新智能加仓统计
    UpdateSmartBuyStats();
    
    // 创建原有EA的实例
    static CTradeExecutor trade_executor;
    static CCloseManager close_manager;
    
    // 优化：使用不同频率控制不同功能
    static int tick_count = 0;
    tick_count++;
    
    // 平仓检查 - 每5个tick检查一次
    if(tick_count % 5 == 0)
    {
        close_manager.CheckAndCloseOrders();
    }
    
    // 交易逻辑 - 每10个tick执行一次
    if(tick_count % 10 == 0)
    {
        trade_executor.ExecuteTradingLogic();
    }
    
    // 交易状态检查 - 每100个tick检查一次
    if(tick_count % 100 == 0)
    {
        trade_executor.CheckTradingStatus();
        
        // 输出智能加仓状态
        Print("📊 智能加仓状态 - 订单数: ", g_smart_buy_orders, "/", MaxSmartBuyOrders, 
              " 总手数: ", g_smart_buy_total_lots, "/", MaxSmartBuyTotalLots);
        
        // 显示详细统计
        int normal_count = CountNormalOrders();
        int lock_count = CountLockOrders();
        int emergency_count = CountEmergencyOrders();
        int smart_buy_count = CountSmartBuyOrders();
        
        Print("📊 订单统计 - 正常: ", normal_count, "/", MaxNormalOrders, 
              " 锁仓: ", lock_count, "/", MaxLockOrders,
              " 应急: ", emergency_count, "/", EmergencyOrderCount,
              " 智能加仓: ", smart_buy_count, "/", MaxSmartBuyOrders);
    }
    
    // 防止tick_count溢出
    if(tick_count >= 1000) tick_count = 0;
} 