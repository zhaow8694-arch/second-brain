//+------------------------------------------------------------------+
//| AI增强风险管理系统 - 扛单+锁仓+智能加仓完整版
//| 版本: 2.8.4 - 智能加仓完整集成版
//| 功能: 扛单策略 + 锁仓 + 虚拟移动止损 + AI智能决策 + 智能加仓
//+------------------------------------------------------------------+

#property copyright "AI Enhanced Trading System"
#property version   "2.69"
#property strict

//+------------------------------------------------------------------+
//| 市场状态枚举定义
//+------------------------------------------------------------------+
enum MARKET_REGIME {
    TRENDING_UP,      // 上升趋势
    TRENDING_DOWN,    // 下降趋势
    RANGING,          // 震荡
    BREAKOUT_UP,      // 向上突破
    BREAKOUT_DOWN,    // 向下突破
    REVERSAL_UP,      // 向上反转
    REVERSAL_DOWN     // 向下反转
};

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

//+------------------------------------------------------------------+
//| 全局变量
datetime g_last_prediction_time = 0;
int g_last_prediction = -1;
double g_last_confidence = 0.0;
bool g_ai_service_available = false;

// 确保所有全局变量正确初始化
bool g_variables_initialized = false;

// 信号确认变量
int g_signal_confirm_ticks = 0;
int g_last_signal = -1;
bool g_signal_confirmed = false;

// 建仓频率控制变量
datetime g_last_normal_order_time = 0;  // 普通仓最后建仓时间
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

DecisionScoreHistory g_decision_score_history[5] = {
    {0.0, 0.0, 0, 0},
    {0.0, 0.0, 0, 0},
    {0.0, 0.0, 0, 0},
    {0.0, 0.0, 0, 0},
    {0.0, 0.0, 0, 0}
};
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
datetime g_last_emergency_order_time = 0;         // 应急仓位最后建仓时间

//+------------------------------------------------------------------+
//| 智能加仓全局变量（新增）
//+------------------------------------------------------------------+
datetime g_last_smart_buy_time = 0;
int g_smart_buy_orders = 0;
double g_smart_buy_total_lots = 0.0;
bool g_smart_buy_triggered = false;

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

// 智能加仓记录数组
SmartBuyRecord g_smart_buy_records[2] = {{0, 0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, false}};
int g_smart_buy_record_count = 0;


// 输入参数
input int MaxOpenOrders = 12;             // 最大同时开仓数 (调整为12，支持四种仓位类型)
input double MaxSpreadPips = 50.0;        // 最大允许点差 (从8.0提高到50.0，适应实际市场条件)
input double MaxSlippage = 50.0;          // 最大允许滑点 (从20.0提高到50.0，适应黄金市场高波动)
input string DataFileName = "market_data.csv"; // 市场数据文件名
input string PredictionFileName = "ai_prediction.txt"; // AI预测文件名
input double MinAIConfidence = 0.6;       // 最小AI置信度 (从0.7降低到0.6)
input double TechnicalWeight = 0.7;       // 技术分析权重 (提升至70%)
input double MarketWeight = 0.3;          // 市场状态权重 (保持30%)
input double AIWeight = 0.0;              // AI预测权重 (禁用AI计分)

// 平仓管理参数
input bool EnableAI = false;              // 启用AI预测（禁用以只用技术+市场）
input bool EnableSmartClose = true;       // 启用智能平仓
input bool EnableTechnicalClose = false;  // 启用技术指标平仓（禁用，仅用固定出场）
input bool EnableTrailingStop = false;    // 移动止损（关闭，仅用固定出场）
input double TrailingStopMultiplier = 1.0; // 移动止损倍数 (调整为1.0，更紧密的利润保护)

// 信号确认参数
input int SignalConfirmTicks = 3;          // 信号确认tick数 - 需要3个tick确认
input bool EnableSignalConfirmation = true; // 启用信号确认 - 防止假信号

// 方向检查参数
input bool EnableSmartDirectionCheck = true; // 启用智能方向检查 - 限制同方向持仓数
input int MaxSameDirectionOrders = 8;      // 同方向最大持仓数 (普通仓位2个 + 应急仓位2个 + 智能加仓2个 + 锁仓2个)

// 固定手数设置
input bool UseFixedLotSize = true;         // 使用固定手数 (推荐启用)
input double FixedLotSize = 0.01;          // 固定手数大小

// 技术指标参数
input double RSIOverbought = 75.0;             // RSI超买阈值（黄金专用，更保守）
input double RSIOversold = 25.0;               // RSI超卖阈值（黄金专用，更保守）
input double ADXThreshold = 12.0;              // ADX阈值（从8提高到12，减少误平仓）

// 高级技术指标参数 - 新增
input bool EnableAdvancedIndicators = true;    // 启用高级技术指标
input double BollingerOverbought = 85.0;       // 布林带超买阈值
input double BollingerOversold = 15.0;         // 布林带超卖阈值
input double KDJOverbought = 80.0;             // KDJ超买阈值
input double KDJOversold = 20.0;               // KDJ超卖阈值

// 高级市场分析参数 - 新增
input bool EnableAdvancedMarketAnalysis = true; // 启用高级市场分析
input bool EnableMarketRegimeDetection = true;  // 启用市场状态检测
input bool EnableDynamicWeightAdjustment = true; // 启用动态权重调整
input bool EnableSynergyScoring = true;         // 启用协同评分机制
         // 波动率阈值
             // 成交量阈值
         // 市场情绪阈值

// 亏损管理参数（扛单模式下大幅调整）
input bool EnableLossManagement = true;        // 启用亏损管理

// 新增：扛单策略参数
input bool EnableHoldStrategy = true;      // 启用扛单策略
input double MaxHoldLossPips = 10000.0;    // 最大扛单亏损点数 (调整为10000点)

// 锁仓管理 - 统一触发模式
input bool EnableLockManagement = true;    // 启用锁仓管理
input double LockTriggerLevel = 1500.0;    // 锁仓触发点（1500点亏损）
input double LockLotMultiplier = 1.0;      // 锁仓手数倍数
input double UnlockProfit = 300.0;         // 锁仓解锁盈利点

// 建仓频率控制参数
input int MinOrderInterval = 900;          // 锁仓单最小建仓间隔(秒) - 15分钟
input int MaxNormalOrders = 2;             // 普通仓最多2个持仓
input int MaxLockOrders = 2;               // 锁仓单最多2个持仓

// 智能平仓参数（无固定止损止盈版本，扛单模式优化）
input bool EnableSmartCloseOnly = true;    // 启用纯智能平仓模式

// 位置风险控制参数
input bool EnablePositionRiskControl = true;    // 启用位置风险控制
input double HighRiskPosition = 80.0;           // 高位风险阈值（调整为80%）
input double LowRiskPosition = 20.0;            // 低位风险阈值（调整为20%）
input double TrendHighRiskPosition = 95.0;      // 趋势高位风险阈值
input double TrendLowRiskPosition = 5.0;        // 趋势低位风险阈值
input double StrongTrendADX = 30.0;             // 强趋势ADX阈值
input double HighConfidenceThreshold = 0.85;    // 高置信度阈值（降低到0.85）

// 位置感知增强参数 - 新增
input bool EnablePositionAwareness = true;      // 启用位置感知增强
input double ExtremePositionThreshold = 95.0;   // 极端位置阈值（调整为95%）
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
input int EmergencyOrderCount = 4;               // 应急仓位数量
input double EmergencyLotSize = 0.02;            // 应急仓位手数
input double EmergencyProfitTarget = 250.0;      // 应急仓位盈利目标(点位)
input double EmergencyStopLoss = 4000.0;          // 应急仓位止损(点位)
input double EmergencyTriggerScore = 0.3;        // 应急仓位触发阈值 (已废弃，现在使用DecisionReversalThreshold)

//+------------------------------------------------------------------+
//| 智能加仓参数（新增）
//+------------------------------------------------------------------+
input bool EnableSmartBuyStrategy = true;     // 启用智能加仓（默认开启，后续改为"决策评分触发"）
input double SmartBuyDecisionThreshold = 0.65;     // 智能加仓决策评分阈值（高评分触发）
input int MaxSmartBuyOrders = 2;              // 智能加仓最大订单数（不影响4个正常订单）
input double MaxSmartBuyTotalLots = 0.03;     // 智能加仓最大总手数（0.03手）
input int SmartBuyMinInterval = 900;          // 智能加仓最小间隔（15分钟）
input double SmartBuyLossThreshold = 50.0;   // 智能加仓触发亏损阈值（点数，可选）
input double SmartBuyMaxLossThreshold = 5000.0; // 智能加仓最大亏损阈值（点数，可选）
input bool SmartBuyUseLossTrigger = false;   // 是否使用亏损触发（false=仅用决策评分）
input double SmartBuyProfitTarget = 250.0;     // 智能加仓盈利目标（点数）
input double SmartBuyStopLoss = 4000.0;        // 智能加仓止损（点数）
input bool SmartBuyRequireDirectionMatch = false; // 是否要求AI预测方向与主导亏损方向一致（false=不要求）



//+------------------------------------------------------------------+
//| 统一日志管理器 - 优化：集中化日志处理
//+------------------------------------------------------------------+
class CLogManager
{
public:
    enum LOG_LEVEL
    {
        LOG_ERROR = 0,
        LOG_WARNING = 1,
        LOG_INFO = 2,
        LOG_DEBUG = 3
    };
    
    static void LogTrade(string action, int ticket, double lots, double price, string reason)
    {
        string log_entry = StringFormat("%s | 交易: %s | 订单: %d | 手数: %.2f | 价格: %.5f | 原因: %s | 余额: %.2f", 
                                       TimeToString(TimeCurrent()), action, ticket, lots, price, reason, AccountBalance());
        Print("💼 ", log_entry);
        
        // 写入文件日志
        WriteToFile("trade_activity_log.csv", log_entry);
    }
    
    static void LogClose(int ticket, string reason, double profit, string order_type)
    {
        string log_entry = StringFormat("%s | 平仓: %s | 订单: %d | 盈亏: %.2f | 原因: %s", 
                                       TimeToString(TimeCurrent()), order_type, ticket, profit, reason);
        Print("🔚 ", log_entry);
        
        // 写入文件日志
        WriteToFile("close_activity_log.csv", log_entry);
    }
    
    static void LogSystem(string message, int level = LOG_INFO)
    {
        // 优化：只在重要级别时输出日志，减少性能开销
        if(level >= LOG_INFO) // 只输出INFO及以上级别
        {
            string prefix = "";
            switch(level)
            {
                case LOG_ERROR:   prefix = "❌ "; break;
                case LOG_WARNING: prefix = "⚠️ "; break;
                case LOG_INFO:    prefix = "ℹ️ "; break;
                case LOG_DEBUG:   prefix = "🔧 "; break;
            }
            
            Print(prefix, message);
        }
    }
    
    static void LogError(string message)
    {
        LogSystem(message, LOG_ERROR);
    }
    
private:
    static void WriteToFile(string filename, string content)
    {
        int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_READ);
        if(handle != INVALID_HANDLE)
        {
            FileSeek(handle, 0, SEEK_END);
            FileWrite(handle, content);
            FileClose(handle);
        }
    }
};

//+------------------------------------------------------------------+
//| 统一锁仓单保护管理器 - 避免逻辑冲突
//+------------------------------------------------------------------+
class CLockOrderProtector
{
public:
    // 检查是否为锁仓单（当前已选中的订单）
    static bool IsCurrentLockOrder()
    {
        string comment = OrderComment();
        return (StringFind(comment, "锁仓") >= 0);
    }
    
    // 检查是否允许平仓锁仓单
    static bool CanCloseLockOrder(string reason)
    {
        // 允许更多必要的平仓操作
        return (StringFind(reason, "锁仓解锁") >= 0 || 
                StringFind(reason, "锁仓单亏损平仓") >= 0 ||
                StringFind(reason, "250点盈利平仓") >= 0 ||
                StringFind(reason, "移动止损触发") >= 0);
    }
    
    // 统一的锁仓单保护检查
    static bool ShouldSkipOperation(string reason = "")
    {
        if(!IsCurrentLockOrder()) return false;
        
        // 如果没有指定原因，默认跳过
        if(reason == "") return true;
        
        // 如果指定了原因，检查是否允许
        return !CanCloseLockOrder(reason);
    }
};

//+------------------------------------------------------------------+
//| 统一错误处理器 - 消除重复的错误处理代码
//+------------------------------------------------------------------+
class CErrorHandler
{
public:
    static void HandleOrderError(int error_code, string operation)
    {
        string error_msg = "";
        
        switch(error_code)
        {
            case 130: error_msg = "错误130: 无效止损/止盈"; break;
            case 131: error_msg = "错误131: 无效手数"; break;
            case 132: error_msg = "错误132: 市场关闭"; break;
            case 133: error_msg = "错误133: 交易禁用"; break;
            case 134: error_msg = "错误134: 资金不足"; break;
            case 135: error_msg = "错误135: 价格变化"; break;
            case 136: error_msg = "错误136: 无报价"; break;
            case 137: error_msg = "错误137: 经纪商忙"; break;
            case 138: error_msg = "错误138: 重复报价"; break;
            case 139: error_msg = "错误139: 订单被锁定"; break;
            case 140: error_msg = "错误140: 只允许做多"; break;
            case 141: error_msg = "错误141: 等待中的订单过多"; break;
            case 145: error_msg = "错误145: 修改被拒绝"; break;
            case 146: error_msg = "错误146: 交易系统忙"; break;
            case 147: error_msg = "错误147: 使用过期时间"; break;
            case 148: error_msg = "错误148: 订单数量变化"; break;
            default:  error_msg = StringFormat("错误%d: 未知错误", error_code); break;
        }
        
        CLogManager::LogSystem(StringFormat("%s失败: %s", operation, error_msg), LOG_ERROR);
    }
};

//+------------------------------------------------------------------+
//| 统一利润计算函数 - 优化：避免重复计算
//+------------------------------------------------------------------+
double GetOrderTotalProfit()
{
    return OrderProfit() + OrderSwap() + OrderCommission();
}

//+------------------------------------------------------------------+
//| 获取当前选中订单的总利润 - 当前订单已选中时使用
//+------------------------------------------------------------------+
double GetCurrentOrderTotalProfit()
{
    return OrderProfit() + OrderSwap() + OrderCommission();
}

//+------------------------------------------------------------------+
//| 统一订单过滤函数 - 消除重复检查
//+------------------------------------------------------------------+
bool IsOurOrder()
{
    return OrderSymbol() == Symbol() && OrderMagicNumber() == 12345;
}

//+------------------------------------------------------------------+
//| 指标缓存管理器 - 优化：避免重复计算技术指标
//+------------------------------------------------------------------+
class CIndicatorCache
{
private:
    datetime last_update_time;
    double cached_ma_fast;
    double cached_ma_slow;
    double cached_ma_long;
    double cached_ma_200;  // 新增：200周期MA缓存
    double cached_rsi;
    double cached_adx;
    double cached_atr;
    
public:
    CIndicatorCache()
    {
        last_update_time = 0;
        cached_ma_fast = 0;
        cached_ma_slow = 0;
        cached_ma_long = 0;
        cached_ma_200 = 0;  // 初始化200周期MA缓存
        cached_rsi = 0;
        cached_adx = 0;
        cached_atr = 0;
    }
    
    void UpdateIndicators()
    {
        datetime current_time = Time[0];
        
        // 优化：只在K线变化时更新指标，减少计算频率
        if(current_time != last_update_time)
        {
            // 批量计算所有指标，减少函数调用开销 - 优化MA类型选择
                    cached_ma_fast = iMA(Symbol(), Period(), 12, 0, MODE_EMA, PRICE_CLOSE, 0);  // 快线使用12周期EMA（黄金优化）
        cached_ma_slow = iMA(Symbol(), Period(), 26, 0, MODE_EMA, PRICE_CLOSE, 0);  // 慢线使用26周期EMA（黄金优化）
        cached_ma_long = iMA(Symbol(), Period(), 50, 0, MODE_SMA, PRICE_CLOSE, 0);  // 长线使用SMA更稳定
        cached_ma_200 = iMA(Symbol(), Period(), 200, 0, MODE_SMA, PRICE_CLOSE, 0);  // 200周期MA
            cached_rsi = iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 0);
            cached_adx = iADX(Symbol(), Period(), 14, PRICE_CLOSE, MODE_MAIN, 0);
            cached_atr = iATR(Symbol(), Period(), 14, 0);
            
            last_update_time = current_time;
            
            // 调试信息（可选）
            // Print("📊 技术指标已更新 - 时间: ", TimeToString(current_time));
        }
    }
    
    double GetMA(int period)
    {
        UpdateIndicators();
        if(period == 12) return cached_ma_fast;  // 12周期EMA（黄金优化）
        else if(period == 26) return cached_ma_slow;  // 26周期EMA（黄金优化）
        else if(period == 50) return cached_ma_long;  // 50周期SMA
        else if(period == 200) return cached_ma_200;  // 200周期MA
        else return iMA(Symbol(), Period(), period, 0, MODE_SMA, PRICE_CLOSE, 0); // 其他周期使用SMA
    }
    
    double GetRSI() { UpdateIndicators(); return cached_rsi; }
    double GetADX() { UpdateIndicators(); return cached_adx; }
    double GetATR() { UpdateIndicators(); return cached_atr; }
};

//+------------------------------------------------------------------+
//| 订单遍历基类 - 优化：统一订单循环逻辑
//+------------------------------------------------------------------+
class COrderIterator
{
public:
    // 遍历所有EA订单并执行回调函数（MQL4简化版本）
    static int ForEachOrder()
    {
        int processed_count = 0;
        
        for(int i = OrdersTotal() - 1; i >= 0; i--)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(IsOurOrder())
                {
                    processed_count++;
                }
            }
        }
        
        return processed_count;
    }
    
    // 统计EA订单信息（优化版本）
    static int CountEAOrders()
    {
        int count = 0;
        int total_orders = OrdersTotal();
        
        // 优化：使用局部变量避免重复调用OrdersTotal()
        for(int i = 0; i < total_orders; i++)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(IsOurOrder())
                {
                    count++;
                }
            }
        }
        return count;
    }
    
    // 检查是否存在指定类型的订单
    static bool HasOrderType(int order_type)
    {
        for(int i = 0; i < OrdersTotal(); i++)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(IsOurOrder() && OrderType() == order_type)
                {
                    return true;
                }
            }
        }
        return false;
    }
    
    // 新增：获取所有EA订单的ticket数组（优化版本）
    static int GetAllOrderTickets(int &tickets[])
    {
        ArrayResize(tickets, 0);
        int count = 0;
        
        for(int i = 0; i < OrdersTotal(); i++)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(IsOurOrder())
                {
                    int size = ArraySize(tickets);
                    ArrayResize(tickets, size + 1);
                    tickets[size] = OrderTicket();
                    count++;
                }
            }
        }
        
        return count; // 返回找到的订单数量
    }
    
    // 新增：获取指定类型的订单ticket数组 - 使用全局函数
    // void GetOrderTicketsByType(int order_type, int &tickets[]) - 已移至全局函数
};

//+------------------------------------------------------------------+
//| 交易计数管理器 - 优化：统一交易计数逻辑
//+------------------------------------------------------------------+
class CTradeCounter
{
private:
    // 使用全局变量替代静态成员变量（MQL4兼容）
    // static int daily_trade_count;
    // static datetime last_trade_time;
    // static datetime last_reset_date;
    
public:
    static void Init()
    {
        g_last_trade_time = 0;
        g_last_reset_date = TimeDay(TimeCurrent());
    }
    
    static bool CanPlaceOrder()
    {
        // 检查建仓频率限制
        datetime current_time = TimeCurrent();
        if(current_time - g_last_trade_time < 60) // 1分钟内只能建仓一次
        {
            return false;
        }
        
        return true;
    }
    
    static void UpdateLastTradeTime()
    {
        g_last_trade_time = TimeCurrent();
    }
    
    static datetime GetLastTradeTime() { return g_last_trade_time; }
};

// 全局变量已在前面统一定义

//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| 全局订单操作函数
//+------------------------------------------------------------------+
void GetOrderTicketsByType(int order_type, int &tickets[])
{
    ArrayResize(tickets, 0);
    
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(IsOurOrder() && OrderType() == order_type)
            {
                int size = ArraySize(tickets);
                ArrayResize(tickets, size + 1);
                tickets[size] = OrderTicket();
            }
        }
    }
}

//+------------------------------------------------------------------+
//| 建仓频率控制函数
//+------------------------------------------------------------------+
// 统计普通仓数量
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
                // 只统计普通订单，排除锁仓单、应急仓和智能加仓
                if(StringFind(comment, "锁仓") < 0 && StringFind(comment, "应急") < 0 && StringFind(comment, "智能加仓") < 0)
                {
                    count++;
                }
            }
        }
    }
    return count;
}

// 统计锁仓单数量
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
                if(StringFind(comment, "锁仓") >= 0)  // 是锁仓单
                {
                    count++;
                }
            }
        }
    }
    return count;
}

// 普通仓建仓检查
bool CanPlaceNormalOrder()
{
    // 检查持仓数量
    int normal_count = CountNormalOrders();
    if(normal_count >= MaxNormalOrders)
    {
        Print("📊 普通仓已达上限: ", normal_count, "/", MaxNormalOrders);
        return false;
    }
    
    // 检查时间间隔
    if(TimeCurrent() - g_last_normal_order_time < MinOrderInterval)
    {
        int remaining = (int)(MinOrderInterval - (TimeCurrent() - g_last_normal_order_time));
        Print("⏰ 普通仓建仓间隔不足，还需等待 ", remaining/60, "分", remaining%60, "秒");
        return false;
    }
    
    return true;
}

// 锁仓单建仓检查
bool CanPlaceLockOrder()
{
    // 检查持仓数量
    int lock_count = CountLockOrders();
    if(lock_count >= MaxLockOrders)
    {
        Print("🔒 锁仓单已达上限: ", lock_count, "/", MaxLockOrders);
        return false;
    }
    
    // 检查时间间隔
    if(TimeCurrent() - g_last_lock_order_time < MinOrderInterval)
    {
        int remaining = (int)(MinOrderInterval - (TimeCurrent() - g_last_lock_order_time));
        Print("⏰ 锁仓单建仓间隔不足，还需等待 ", remaining/60, "分", remaining%60, "秒");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| 新型移动止损管理器 - 解决内存问题
//+------------------------------------------------------------------+
class CTrailingStopManager
{
private:
    // TrailingData结构体已移到全局定义
    // 使用全局变量替代静态成员变量（MQL4兼容）
    // static TrailingData trailing_records[100];  
    // static int record_count;
    
public:
    static void Init()
    {
        g_trailing_record_count = 0;
        // 清空所有记录
        for(int i = 0; i < 100; i++)
        {
            g_trailing_records[i].ticket = 0;
            g_trailing_records[i].highest_price = 0;
            g_trailing_records[i].lowest_price = 0;
            g_trailing_records[i].update_time = 0;
        }
    }
    
    static bool CheckTrailingStop(int ticket)
    {
        if(!EnableTrailingStop) return false;
        
                            // 统一的锁仓单保护检查
                    if(CLockOrderProtector::ShouldSkipOperation())
                    {
                        return false; // 锁仓单不执行移动止损
                    }
        
        double current_profit = ::GetCurrentOrderTotalProfit();
        if(current_profit <= 0) return false;  // 只对盈利订单执行
        
        double profit_pips = current_profit / Point; // 修复：XAUUSD 1点=0.01美元(0.01手)
        if(profit_pips < 400) return false;  // 最低盈利保护 (从200调整到400)
        
        double current_price = (OrderType() == OP_BUY) ? Bid : Ask;
        double atr = indicator_cache.GetATR(); // 使用缓存避免重复计算
        double trailing_distance = atr * TrailingStopMultiplier;
        
        // 查找或创建记录
        int record_index = FindOrCreateRecord(ticket);
        if(record_index < 0) return false;
        
        // MQL4不支持引用，使用直接数组访问
        
        if(OrderType() == OP_BUY)
        {
            // 更新最高价
            if(current_price > g_trailing_records[record_index].highest_price)
            {
                g_trailing_records[record_index].highest_price = current_price;
                g_trailing_records[record_index].update_time = TimeCurrent();
            }
            
            // 检查是否触发移动止损
            double stop_price = g_trailing_records[record_index].highest_price - trailing_distance;
            if(current_price <= stop_price)
            {
                CLogManager::LogClose(ticket, "移动止损触发", current_profit, "买入");
                CloseOrder(ticket, "虚拟移动止损");
                RemoveRecord(ticket);
                return true;
            }
        }
        else if(OrderType() == OP_SELL)
        {
            // 更新最低价
            if(current_price < g_trailing_records[record_index].lowest_price || g_trailing_records[record_index].lowest_price == 0)
            {
                g_trailing_records[record_index].lowest_price = current_price;
                g_trailing_records[record_index].update_time = TimeCurrent();
            }
            
            // 检查是否触发移动止损
            double stop_price = g_trailing_records[record_index].lowest_price + trailing_distance;
            if(current_price >= stop_price)
            {
                CLogManager::LogClose(ticket, "移动止损触发", current_profit, "卖出");
                CloseOrder(ticket, "虚拟移动止损");
                RemoveRecord(ticket);
                return true;
            }
        }
        
        return false;
    }
    
private:
    static int FindOrCreateRecord(int ticket)
    {
        // 查找现有记录
        for(int i = 0; i < g_trailing_record_count; i++)
        {
            if(g_trailing_records[i].ticket == ticket)
                return i;
        }
        
        // 创建新记录
        if(g_trailing_record_count < 100)
        {
            g_trailing_records[g_trailing_record_count].ticket = ticket;
            g_trailing_records[g_trailing_record_count].highest_price = (OrderType() == OP_BUY) ? Bid : 0;
            g_trailing_records[g_trailing_record_count].lowest_price = (OrderType() == OP_SELL) ? Ask : 999999;
            g_trailing_records[g_trailing_record_count].update_time = TimeCurrent();
            return g_trailing_record_count++;
        }
        
        return -1;  // 数组已满
    }
    
    static void RemoveRecord(int ticket)
    {
        for(int i = 0; i < g_trailing_record_count; i++)
        {
            if(g_trailing_records[i].ticket == ticket)
            {
                // 将最后一个记录移到当前位置
                g_trailing_records[i] = g_trailing_records[g_trailing_record_count - 1];
                g_trailing_record_count--;
                break;
            }
        }
    }
    
    static void CleanupInvalidRecords()
    {
        for(int i = g_trailing_record_count - 1; i >= 0; i--)
        {
            bool order_exists = false;
            for(int j = 0; j < OrdersTotal(); j++)
            {
                if(OrderSelect(j, SELECT_BY_POS, MODE_TRADES))
                {
                    if(OrderTicket() == g_trailing_records[i].ticket)
                    {
                        order_exists = true;
                        break;
                    }
                }
            }
            
            if(!order_exists)
            {
                RemoveRecord(g_trailing_records[i].ticket);
            }
        }
    }
};

// MQL4全局变量定义
TrailingData g_trailing_records[100];
int g_trailing_record_count = 0;

// 锁仓层级记录全局变量
LockLevelRecord g_lock_records[50];
int g_lock_record_count = 0;

//+------------------------------------------------------------------+
//| 资金管理类
//+------------------------------------------------------------------+
class CMoneyManager
{
private:
    double account_balance;
    
public:
    void Init()
    {
        UpdateAccountInfo();
    }
    
    double CalculateSafeLotSize(double stop_loss_pips)
    {
        // 如果启用固定手数，直接返回固定值
        if(UseFixedLotSize)
        {
            // 确保固定手数在允许范围内
            double max_lot = MarketInfo(Symbol(), MODE_MAXLOT);
            double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
            
            double safe_lot = MathMax(min_lot, MathMin(max_lot, FixedLotSize));
            Print("📊 使用固定手数: ", safe_lot, " (设置值: ", FixedLotSize, ")");
            return NormalizeDouble(safe_lot, 2);
        }
        

        
        // 默认返回固定手数
        Print("📊 使用默认固定手数: ", FixedLotSize);
        return NormalizeDouble(FixedLotSize, 2);
    }
    
    // 删除IsAccountHealthy函数，因为不再需要回撤检查
    
    void UpdateAccountInfo()
    {
        account_balance = AccountBalance();
    }
    
    
    // 删除GetDrawdownPercent函数，因为不再需要回撤计算
};

//+------------------------------------------------------------------+
//| 风险控制类
//+------------------------------------------------------------------+
class CRiskManager
{
private:
    int max_open_orders;
    double max_spread_pips;
    
public:
    void Init(int max_orders, double max_spread)
    {
        max_open_orders = max_orders;
        max_spread_pips = max_spread;
    }
    
    bool CanOpenNewOrder(int order_type)
    {
        // 检查点差
        if(MarketInfo(Symbol(), MODE_SPREAD) > max_spread_pips)
        {
            Print("点差过大: ", MarketInfo(Symbol(), MODE_SPREAD), " > ", max_spread_pips);
            return false;
        }
        

        

            
        // 检查开仓数量
        if(CountOpenOrders() >= max_open_orders)
        {
            Print("开仓数量已达上限: ", CountOpenOrders(), " >= ", max_open_orders);
            return false;
        }
            

            
        return true;
    }
    

    
    // 删除NeedEmergencyClose函数，因为不再需要紧急平仓机制
    
    int CountOpenOrders()
    {
        // 使用统一的订单遍历方法
        return COrderIterator::ForEachOrder();
    }
    

    
    // 删除GetTodayLoss和DebugTodayLoss函数，因为不再需要每日亏损检查
    
    // 检查是否已有相同方向的订单
    bool HasSameDirectionOrder(int order_type)
    {
        // 智能方向检查：限制同方向持仓数
        if(EnableSmartDirectionCheck)
        {
            int same_direction_count = 0;
            int tickets[];
            GetOrderTicketsByType(order_type, tickets);
            same_direction_count = ArraySize(tickets);
            
            if(same_direction_count >= MaxSameDirectionOrders)
            {
                Print("同方向持仓已达上限: ", same_direction_count, " >= ", MaxSameDirectionOrders);
                return true;
            }
        }
        
        return false;
    }
    
    // 新增：检查是否有锁仓（同时持有买卖订单）
    bool HasLockedPositions()
    {
        bool has_buy = false;
        bool has_sell = false;
        
        int buy_tickets[], sell_tickets[];
        GetOrderTicketsByType(OP_BUY, buy_tickets);
        GetOrderTicketsByType(OP_SELL, sell_tickets);
        
        has_buy = (ArraySize(buy_tickets) > 0);
        has_sell = (ArraySize(sell_tickets) > 0);
        
        return has_buy && has_sell;
    }
    
    // 锁仓管理 - 与扛单策略协同
    void ManageLockedPositions()
    {
        if(!EnableLockManagement) return;
        
        // 检查是否有锁仓状态
                if(!HasLockedPositions()) 
        {
            // 没有锁仓时，锁仓检查由主交易逻辑处理
            return;
        }
        

        
        double total_profit = 0.0;
        int buy_count = 0;
        int sell_count = 0;
        
        // 存储订单信息用于分批解锁 - 新增
        int order_tickets[];
        double order_profits[];
        datetime order_opentimes[];
        int order_types[];
        ArrayResize(order_tickets, 0);
        ArrayResize(order_profits, 0);
        ArrayResize(order_opentimes, 0);
        ArrayResize(order_types, 0);
        
        // 计算锁仓总盈亏（排除新单）
        for(int x = 0; x < OrdersTotal(); x++)
        {
            if(OrderSelect(x, SELECT_BY_POS, MODE_TRADES))
            {
                if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
                {
                    double profit = ::GetCurrentOrderTotalProfit();
                    datetime opentime = OrderOpenTime();
                    int ticket = OrderTicket();
                    int ordertype = OrderType();
                    

                    
                    total_profit += profit;
                    if(ordertype == OP_BUY) buy_count++;
                    if(ordertype == OP_SELL) sell_count++;
                    
                    // 存储订单信息 - 新增
                    int current_idx = ArraySize(order_tickets);
                    ArrayResize(order_tickets, current_idx + 1);
                    ArrayResize(order_profits, current_idx + 1);
                    ArrayResize(order_opentimes, current_idx + 1);
                    ArrayResize(order_types, current_idx + 1);
                    order_tickets[current_idx] = ticket;
                    order_profits[current_idx] = profit;
                    order_opentimes[current_idx] = opentime;
                    order_types[current_idx] = ordertype;
                }
            }
        }
        
        double total_pips = total_profit * 100; // 显示为美分，更清晰
        int total_orders = buy_count + sell_count;
        
        // 详细日志记录锁仓状态
        Print("🔒 锁仓状态检查 - 时间: ", TimeToString(TimeCurrent()));
        Print("   买入订单数: ", buy_count, " | 卖出订单数: ", sell_count);
        Print("   普通仓位: ", CountNormalOrders(), "/", MaxNormalOrders);
        Print("   锁仓仓位: ", CountLockOrders(), "/", MaxLockOrders);
        Print("   应急仓位: ", g_emergency_order_count, "/", EmergencyOrderCount);
        Print("   总盈亏: ", total_profit, " | 总点数: ", total_pips);
        Print("   锁仓触发点: ", LockTriggerLevel, "点");
        Print("   参与计算订单数: ", ArraySize(order_tickets), " (排除新单)");
        
        // 锁仓管理逻辑 - 简化版本
        Print("📊 锁仓状态监控 - 买单:", buy_count, "个 卖单:", sell_count, "个 总盈亏:", total_profit);
        
        // 锁仓单解锁检查
        CheckLockUnlock();
    }
    
    void UnlockPositions(string reason)
    {
        Print("🔓 执行锁仓解锁，原因: ", reason);
        
        // 计算每个方向的盈亏
        double buy_profit = 0.0, sell_profit = 0.0;
        int buy_count = 0, sell_count = 0;
        
        for(int w = 0; w < OrdersTotal(); w++)
        {
            if(OrderSelect(w, SELECT_BY_POS, MODE_TRADES))
            {
                if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
                {
                    double profit = ::GetCurrentOrderTotalProfit();
                    if(OrderType() == OP_BUY)
                    {
                        buy_profit += profit;
                        buy_count++;
                    }
                    else if(OrderType() == OP_SELL)
                    {
                        sell_profit += profit;
                        sell_count++;
                    }
                }
            }
        }
        
        // 策略1：平掉亏损方向
        if(buy_profit < sell_profit)
        {
            Print("📉 平掉买入方向，亏损: ", buy_profit);
            CloseOrdersByType(OP_BUY);
        }
        else if(sell_profit < buy_profit)
        {
            Print("📉 平掉卖出方向，亏损: ", sell_profit);
            CloseOrdersByType(OP_SELL);
        }
        // 策略2：如果盈亏相近，全部平仓
        else
        {
            Print("⚖️ 盈亏相近，全部平仓");
            CloseAllOrders();
        }
    }
    
    // 新增：按类型平仓 (使用COrderIterator统一)
    void CloseOrdersByType(int order_type)
    {
        for(int z = OrdersTotal() - 1; z >= 0; z--)
        {
            if(OrderSelect(z, SELECT_BY_POS, MODE_TRADES))
            {
                if(IsOurOrder() && OrderType() == order_type)
                {
                    // 锁仓单保护：跳过锁仓单
                    if(CLockOrderProtector::IsCurrentLockOrder())
                    {
                        Print("🛡️ 锁仓单保护：跳过订单 ", OrderTicket(), " 的类型平仓");
                        continue;
                    }
                    
                    bool close_result = false;
                    if(order_type == OP_BUY)
                        close_result = OrderClose(OrderTicket(), OrderLots(), Bid, 3, clrRed);
                    else if(order_type == OP_SELL)
                        close_result = OrderClose(OrderTicket(), OrderLots(), Ask, 3, clrRed);
                        
                    if(close_result)
                        Print("✅ 平仓成功: ", OrderTicket());
                    else
                        Print("❌ 平仓失败: ", OrderTicket(), " 错误: ", GetLastError());
                }
            }
        }
    }
    

    
            // 锁仓触发检查
    void CheckAndTriggerProgressiveLock(int ai_prediction, double ai_confidence)
    {
        if(!EnableLockManagement) return;
        
        // 检查每个亏损订单的锁仓需求
        for(int i = 0; i < OrdersTotal(); i++)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
                {
                    // 跳过锁仓单本身
                    if(CLockOrderProtector::IsCurrentLockOrder()) continue;
                    
                    // 检查亏损情况
                    double current_profit = ::GetCurrentOrderTotalProfit();
                    if(current_profit < 0)
                    {
                        double loss_pips = MathAbs(current_profit) / Point; // 修复：点位计算（current_profit已经包含手数信息）
                        int ticket = OrderTicket();
                        int order_type = OrderType();
                        
                        // 检查锁仓
                        CheckLockTrigger(ticket, order_type, loss_pips);
                    }
                }
            }
        }
    }
    
    // 检查锁仓触发
    void CheckLockTrigger(int ticket, int order_type, double loss_pips)
    {
        // 统一锁仓触发：1500点亏损
        if(loss_pips >= LockTriggerLevel && !HasLockOrder(ticket))
        {
            double lock_lot = FixedLotSize * LockLotMultiplier;
            int lock_order_type = (order_type == OP_BUY) ? OP_SELL : OP_BUY;
            ExecuteLockOrder(lock_order_type, "锁仓");
            Print("🔒 锁仓触发 - 订单: ", ticket, " 亏损: ", loss_pips, " 点, 手数: ", lock_lot);
        }
    }
    
    // 检查是否已有锁仓单
    bool HasLockOrder(int ticket)
    {
        for(int i = 0; i < g_lock_record_count; i++)
        {
            if(g_lock_records[i].original_ticket == ticket && 
               g_lock_records[i].is_active)
            {
                return true;
            }
        }
        return false;
    }
    
    // 执行锁仓订单
    void ExecuteLockOrder(int order_type, string comment)
    {
        // 建仓频率控制检查
        if(!CanPlaceLockOrder())
        {
            Print("⏰ 建仓频率限制：锁仓单建仓被阻止");
            return;
        }
        
        // 检查锁仓单数量限制
        int lock_count = CountLockOrders();
        if(lock_count >= MaxLockOrders)
        {
            Print("⚠️ 锁仓单已达上限(", MaxLockOrders, "单)，无法执行锁仓");
            return;
        }
        
        double lot_size = FixedLotSize * LockLotMultiplier;
        double price = (order_type == OP_BUY) ? Ask : Bid;
        
        // 计算锁仓单的止盈止损
        double stop_loss = 0.0;
        double take_profit = 0.0;
        
        if(order_type == OP_BUY)
        {
            stop_loss = price - LockOrderLossLimit * Point;    // 止损4000点
            take_profit = price + UnlockProfit * Point;        // 止盈300点
        }
        else if(order_type == OP_SELL)
        {
            stop_loss = price + LockOrderLossLimit * Point;    // 止损4000点
            take_profit = price - UnlockProfit * Point;        // 止盈300点
        }
        
        // 添加详细的调试日志
        Print("🔍 锁仓订单创建调试:");
        Print("   订单类型: ", (order_type == OP_BUY ? "买入" : "卖出"));
        Print("   手数: ", lot_size);
        Print("   价格: ", price);
        Print("   止损: ", stop_loss, " (", LockOrderLossLimit, "点)");
        Print("   止盈: ", take_profit, " (", UnlockProfit, "点)");
        Print("   注释: '", comment, "'");
        Print("   Magic Number: 12345");
        Print("   时间: ", TimeToString(TimeCurrent()));
        
        int ticket = OrderSend(Symbol(), order_type, lot_size, price, (int)MaxSlippage, stop_loss, take_profit, comment, 12345, 0, clrNONE);
        
        if(ticket > 0)
        {
            // 记录锁仓信息
            AddLockRecord(0, 1, TimeCurrent(), lot_size, ticket);
            Print("✅ 锁仓订单执行成功: ", ticket, " 类型: ", (order_type == OP_BUY ? "买入" : "卖出"));
            Print("   止损: ", LockOrderLossLimit, "点 止盈: ", UnlockProfit, "点 (MT4系统控制)");
            
            // 更新锁仓单建仓时间
            g_last_lock_order_time = TimeCurrent();
            Print("✅ 锁仓单建仓时间已更新: ", TimeToString(g_last_lock_order_time));
        }
        else
        {
            Print("❌ 锁仓订单执行失败: ", GetLastError());
        }
    }
    
    // 添加锁仓记录
    void AddLockRecord(int original_ticket, int level, datetime lock_time, double lot_size, int lock_ticket)
    {
        if(g_lock_record_count < 50)
        {
            g_lock_records[g_lock_record_count].original_ticket = original_ticket;
            g_lock_records[g_lock_record_count].lock_level = level;
            g_lock_records[g_lock_record_count].lock_time = lock_time;
            g_lock_records[g_lock_record_count].lock_lot = lot_size;
            g_lock_records[g_lock_record_count].lock_ticket = lock_ticket;
            g_lock_records[g_lock_record_count].is_active = true;
            g_lock_record_count++;
        }
    }
    
    // 统计锁仓单数量 - 使用全局函数CountLockOrders()
    
    // 锁仓单解锁检查
    void CheckLockUnlock()
    {
        for(int i = 0; i < OrdersTotal(); i++)
        {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            {
                if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
                {
                    string comment = OrderComment();
                    if(StringFind(comment, "锁仓") >= 0)
                    {
                        double profit = ::GetCurrentOrderTotalProfit();
                        double profit_pips = profit / Point; // 修复：XAUUSD 1点=0.01美元(0.01手)
                        int ticket = OrderTicket();
                        
                        // 锁仓单解锁检查
                        if(StringFind(comment, "锁仓") >= 0)
                        {
                            if(profit_pips >= UnlockProfit)
                            {
                                Print("💰 锁仓订单 ", ticket, " 盈利达到", UnlockProfit, "点，执行平仓");
                                CloseOrder(ticket, "锁仓解锁");
                                RemoveLockRecord(ticket);
                            }
                        }
                        
                        // 锁仓单亏损平仓：亏损4000点以内继续持有
                        if(profit_pips < 0)
                        {
                            double loss_pips = MathAbs(profit_pips);
                            if(loss_pips <= LockOrderLossLimit)
                            {
                                Print("🤲 锁仓订单 ", ticket, " 亏损 ", loss_pips, " 点，在平仓范围内，继续持有");
                            }
                            else
                            {
                                Print("🔴 锁仓订单 ", ticket, " 亏损 ", loss_pips, " 点，超过平仓极限，执行平仓");
                                CloseOrder(ticket, "锁仓单亏损平仓");
                                RemoveLockRecord(ticket);
                            }
                        }
                    }
                }
            }
        }
    }
    
    // 移除锁仓记录
    void RemoveLockRecord(int lock_ticket)
    {
        for(int i = 0; i < g_lock_record_count; i++)
        {
            if(g_lock_records[i].lock_ticket == lock_ticket)
            {
                g_lock_records[i].is_active = false;
                Print("📝 移除锁仓记录 - 订单: ", lock_ticket);
                break;
            }
        }
    }
    

    


    

};

//+------------------------------------------------------------------+
//| 价格位置检测结构 - 全局定义供所有类使用
//+------------------------------------------------------------------+
struct PricePosition
{
    double position_50;
    double position_100;
    bool is_high_risk;
    bool is_low_risk;
};

//+------------------------------------------------------------------+
//| 市场状态监控类
//+------------------------------------------------------------------+
class CMarketMonitor
{
private:
    double volatility_threshold;
    double trend_strength_threshold;
    
public:
    void Init(double vol_threshold, double trend_threshold)
    {
        volatility_threshold = vol_threshold;
        trend_strength_threshold = trend_threshold;
    }
    
    bool IsMarketSuitable()
    {
        // 使用缓存的技术指标，避免重复计算
        double atr = indicator_cache.GetATR();
        double adx = indicator_cache.GetADX();
        
        // 检查波动率
        double avg_atr = GetAverageATR(14);
        if(atr > avg_atr * volatility_threshold)
        {
            Print("波动率过高: ATR=", atr, ", 平均ATR=", avg_atr);
            return false;
        }
            
        // 检查趋势强度
        if(adx < trend_strength_threshold)
        {
            Print("趋势不明显: ADX=", adx, " < ", trend_strength_threshold);
            return false;
        }
            
        return true;
    }
    
    double GetMarketScore()
    {
        double score = 0.0;
        
        // 使用缓存的技术指标，避免重复计算
        double atr = indicator_cache.GetATR();
        double adx = indicator_cache.GetADX();
        
        // 波动率评分
        double avg_atr = GetAverageATR(14);
        double atr_ratio = atr / avg_atr;
        score += (1.0 - MathAbs(atr_ratio - 1.0)) * 30; // 波动率适中得高分
        
        // 趋势强度评分
        score += MathMin(adx / 100.0, 1.0) * 40; // ADX越高分数越高
        
        // 成交量评分
        double volume_ratio = Volume[0] / GetAverageVolume(20);
        score += MathMin(volume_ratio, 2.0) / 2.0 * 30; // 成交量适中得高分
        
        return score;
    }
    
    // 位置检测功能
    PricePosition GetPricePosition()
    {
        PricePosition pos;
        
        // 计算50周期位置
        double high_50 = High[iHighest(NULL, 0, MODE_HIGH, 50, 0)];
        double low_50 = Low[iLowest(NULL, 0, MODE_LOW, 50, 0)];
        pos.position_50 = (Close[0] - low_50) / (high_50 - low_50) * 100;
        
        // 计算100周期位置
        double high_100 = High[iHighest(NULL, 0, MODE_HIGH, 100, 0)];
        double low_100 = Low[iLowest(NULL, 0, MODE_LOW, 100, 0)];
        pos.position_100 = (Close[0] - low_100) / (high_100 - low_100) * 100;
        
        // 风险判断 - 50和100周期双重确认
        pos.is_high_risk = (pos.position_50 > HighRiskPosition && pos.position_100 > HighRiskPosition);
        pos.is_low_risk = (pos.position_50 < LowRiskPosition && pos.position_100 < LowRiskPosition);
        
        return pos;
    }
    
    bool IsPositionSuitable(int order_type)
    {
        if(!EnablePositionRiskControl) return true;
        
        PricePosition pos = GetPricePosition();
        
        if(order_type == OP_BUY && pos.is_high_risk)
        {
            Print("⚠️ 高位追涨风险: 50周期", DoubleToString(pos.position_50, 1), "%, 100周期", DoubleToString(pos.position_100, 1), "%");
            return false;
        }
        
        if(order_type == OP_SELL && pos.is_low_risk)
        {
            Print("⚠️ 低位追跌风险: 50周期", DoubleToString(pos.position_50, 1), "%, 100周期", DoubleToString(pos.position_100, 1), "%");
            return false;
        }
        
        return true;
    }
    
    bool IsStrongTrend()
    {
        // 使用缓存的技术指标，避免重复计算
        double adx = indicator_cache.GetADX();
        double atr = indicator_cache.GetATR();
        
        // 计算ATR相对值 - 使用缓存优化
        double atr_avg = GetAverageATR(20);
        double atr_ratio = (atr_avg > 0) ? atr / atr_avg : 1.0; // 防止除零错误
        
        return (adx > StrongTrendADX && atr_ratio > 1.2);
    }
    
    bool IsPositionSuitableWithTrend(int order_type)
    {
        if(!EnablePositionRiskControl) return true;
        
        PricePosition pos = GetPricePosition();
        bool is_strong_trend = IsStrongTrend();
        
        if(is_strong_trend)
        {
            // 强趋势时使用宽松阈值
            bool high_risk = (pos.position_50 > TrendHighRiskPosition && pos.position_100 > TrendHighRiskPosition);
            bool low_risk = (pos.position_50 < TrendLowRiskPosition && pos.position_100 < TrendLowRiskPosition);
            
            if(order_type == OP_BUY && high_risk)
            {
                Print("📈 强趋势高位风险: 50周期", DoubleToString(pos.position_50, 1), "%, 100周期", DoubleToString(pos.position_100, 1), "%");
                return false;
            }
            
            if(order_type == OP_SELL && low_risk)
            {
                Print("📉 强趋势低位风险: 50周期", DoubleToString(pos.position_50, 1), "%, 100周期", DoubleToString(pos.position_100, 1), "%");
                return false;
            }
        }
        else
        {
            // 正常趋势时使用严格阈值
            return IsPositionSuitable(order_type);
        }
        
        return true;
    }
    
    // 更新AI信号历史
    void UpdateAISignalHistory(int new_signal)
    {
        // 移动历史记录
        for(int i = 4; i > 0; i--)
        {
            g_ai_signal_history[i] = g_ai_signal_history[i-1];
        }
        g_ai_signal_history[0] = new_signal;
        
        // 计算连续信号
        g_signal_count = 0;
        for(int i = 0; i < 5; i++)
        {
            if(g_ai_signal_history[i] == new_signal)
            {
                g_signal_count++;
            }
            else
            {
                break;
            }
        }
    }
    
    // 检查强趋势信号
    bool IsStrongTrendSignal(int order_type)
    {
        // 连续3次以上同向信号
        return (g_signal_count >= 3 && g_ai_signal_history[0] == order_type);
    }
    
    // 综合位置检测
    bool IsPositionSuitableComprehensive(int order_type, double ai_confidence)
    {
        if(!EnablePositionRiskControl) return true;
        
        // 获取位置信息
        PricePosition pos = GetPricePosition();
        
        // 1. 极端位置检测 - 新增：在极端位置提高置信度要求
        bool is_extreme_position = false;
        if(pos.position_50 > ExtremePositionThreshold || pos.position_50 < (100 - ExtremePositionThreshold) ||
           pos.position_100 > ExtremePositionThreshold || pos.position_100 < (100 - ExtremePositionThreshold))
        {
            is_extreme_position = true;
            Print("🚨 检测到极端位置: 50周期", DoubleToString(pos.position_50, 1), "%, 100周期", DoubleToString(pos.position_100, 1), "%");
        }
        
        // 2. 高置信度检测 - 修改：极端位置需要更高置信度
        if(ai_confidence > HighConfidenceThreshold)
        {
            if(is_extreme_position)
            {
                // 极端位置需要更高置信度
                if(ai_confidence >= ExtremeConfidenceThreshold)
                {
                    Print("🎯 极端位置超高置信度", DoubleToString(ai_confidence, 3), "，突破位置限制");
                    return true;
                }
                else
                {
                    Print("⚠️ 极端位置置信度不足: ", DoubleToString(ai_confidence, 3), " < ", ExtremeConfidenceThreshold);
                    return false;
                }
            }
            else
            {
                Print("🎯 超高置信度", DoubleToString(ai_confidence, 3), "，突破位置限制");
                return true;
            }
        }
        
        // 3. 强趋势信号检测
        if(IsStrongTrendSignal(order_type))
        {
            if(is_extreme_position)
            {
                // 极端位置需要更强的趋势信号
                if(g_signal_count >= 5) // 从3次提高到5次
                {
                    Print("🔥 极端位置强趋势信号: 连续", g_signal_count, "次", (order_type == OP_BUY ? "买入" : "卖出"), "信号，突破位置限制");
                    return true;
                }
                else
                {
                    Print("⚠️ 极端位置趋势信号不足: 连续", g_signal_count, "次 < 5次");
                    return false;
                }
            }
            else
            {
                Print("🔥 连续", g_signal_count, "次", (order_type == OP_BUY ? "买入" : "卖出"), "信号，突破位置限制");
                return true;
            }
        }
        
        // 4. 强趋势检测
        if(IsStrongTrend())
        {
            Print("📈 强趋势模式，使用宽松阈值");
            return IsPositionSuitableWithTrend(order_type);
        }
        
        // 5. 正常位置检查
        return IsPositionSuitable(order_type);
    }
    
private:
    // GetAverageATR函数已移至全局作用域
    
    double GetAverageVolume(int period)
    {
        double sum = 0.0;
        for(int t = 0; t < period; t++)
        {
            sum += (double)Volume[t];
        }
        return (double)sum / period;
    }
};

//+------------------------------------------------------------------+
//| AI预测模块（文件共享方式）
//+------------------------------------------------------------------+
class CAIPredictor
{
private:
    string data_file_name;
    string prediction_file_name;
    int prediction_cache_time;
    
public:
    void Init(string data_file, string pred_file, int cache_time)
    {
        data_file_name = data_file;
        prediction_file_name = pred_file;
        prediction_cache_time = (int)MathMax(1, cache_time);
    }
    
    // 清除AI预测缓存，强制重新读取
    void ClearCache()
    {
        g_last_prediction_time = 0;
        g_last_prediction = -1;
        g_last_confidence = 0.0;
        Print("🔄 AI预测缓存已清除，将重新读取最新预测 - 时间: ", TimeToString(TimeCurrent()));
    }
    
    bool GetAIPrediction(int &prediction, double &confidence)
    {
        // 检查缓存 - 使用实际服务器时间而不是K线时间
        datetime current_time = TimeCurrent();
        if(g_last_prediction_time > 0 && current_time - g_last_prediction_time < prediction_cache_time)
        {
            prediction = g_last_prediction;
            confidence = g_last_confidence;
            int remaining_seconds = prediction_cache_time - (int)MathMax(0, current_time - g_last_prediction_time);
            Print("使用AI缓存预测: ", prediction, " 置信度: ", confidence, " 缓存剩余: ", remaining_seconds, "秒");
            return true;
        }
        
        // 清除旧缓存，强制读取新预测
        Print("缓存过期，强制读取新AI预测...");
        
        // 写入市场数据到文件
        if(WriteMarketDataToFile())
        {
            Print("市场数据已写入，等待AI预测...");
            
            // 等待AI处理（最多等待10秒）
            for(int i = 0; i < 10; i++)
            {
                if(ReadPredictionFromFile(prediction, confidence))
                {
                    g_last_prediction = prediction;
                    g_last_confidence = confidence;
                    g_last_prediction_time = TimeCurrent();
                    Print("AI预测成功: ", prediction, " 置信度: ", confidence, " 时间: ", TimeToString(TimeCurrent()));
                    return true;
                }
                Sleep(1000); // 等待1秒
            }
            
            Print("AI预测超时，使用默认值");
            // 如果AI没有响应，使用默认值
            prediction = -1;
            confidence = 0.0;
            return false;
        }
        
        Print("无法写入市场数据");
        return false;
    }
    
    // 统一反转信号计算 - 基于前5个决策评分对比
    ReversalSignalResult CalculateUnifiedReversalSignal()
    {
        ReversalSignalResult result = {false, -1, 0.0, 0, false};
        result.timestamp = TimeCurrent(); // 在函数内部设置时间戳
        
        if(!EnableDecisionScoreReversal)
        {
            return result;
        }
        
        // 计算当前决策评分
        double buy_score = 0.0;
        double sell_score = 0.0;
        
        // 调用决策评分计算逻辑
        CalculateDecisionScores(buy_score, sell_score);
        
        // 更新决策评分历史
        UpdateDecisionScoreHistory(buy_score, sell_score);
        
        // 检查是否有足够的历史数据
        if(g_decision_history_count < 5)
        {
            Print("📊 决策历史数据不足，需要至少5个历史记录，当前:", g_decision_history_count);
            return result;
        }
        
        // 确定当前决策方向
        int current_direction = 0;
        if(buy_score > sell_score)
            current_direction = 1; // 买入
        else if(sell_score > buy_score)
            current_direction = -1; // 卖出
        
        // 计算前5个决策评分的主要方向
        int historical_direction = CalculateHistoricalDirection();
        
        Print("📊 决策方向对比 - 当前:", (current_direction == 1 ? "买入" : current_direction == -1 ? "卖出" : "无方向"), 
              " 历史:", (historical_direction == 1 ? "买入" : historical_direction == -1 ? "卖出" : "无方向"));
        
        // 检查方向反转
        bool is_reversal = false;
        if(historical_direction != 0 && current_direction != 0 && historical_direction != current_direction)
        {
            is_reversal = true;
            result.signal_direction = (current_direction == 1) ? OP_BUY : OP_SELL;
            result.confidence = (current_direction == 1) ? buy_score : sell_score;
            
            Print("🔄 检测到决策方向反转: 历史方向=", (historical_direction == 1 ? "买入" : "卖出"), 
                  " -> 当前方向=", (current_direction == 1 ? "买入" : "卖出"));
        }
        
        if(is_reversal && result.confidence >= DecisionReversalThreshold)
        {
            result.has_reversal = true;
            result.is_valid = true;
            Print("🔴 决策评分反转信号确认: 方向=", result.signal_direction == OP_BUY ? "买入" : "卖出", 
                  " 评分=", result.confidence, " 时间=", TimeToString(result.timestamp));
        }
        
        return result;
    }
    
    // 决策评分反转检测 - 兼容旧版本 (修复Stack overflow)
    bool CheckDecisionScoreReversal(int current_position_type, int &reversal_signal, double &reversal_confidence)
    {
        // 简化版本，避免复杂计算
        reversal_signal = -1;
        reversal_confidence = 0.0;
        
        if(!EnableDecisionScoreReversal) return false;
        
        // 直接返回当前反转信号状态
        if(g_current_reversal_signal.has_reversal && g_current_reversal_signal.is_valid)
        {
            reversal_signal = g_current_reversal_signal.signal_direction;
            reversal_confidence = g_current_reversal_signal.confidence;
            return true;
        }
        
        return false;
    }
    
    // 更新决策评分历史 (修复版本)
    void UpdateDecisionScoreHistory(double buy_score, double sell_score)
    {
        // 将现有历史记录向后移动一位
        for(int i = 4; i > 0; i--)
        {
            g_decision_score_history[i] = g_decision_score_history[i-1];
        }
        
        // 更新最新的记录到位置0
        g_decision_score_history[0].buy_score = buy_score;
        g_decision_score_history[0].sell_score = sell_score;
        g_decision_score_history[0].timestamp = TimeCurrent();
        
        // 确定决策方向
        if(buy_score > sell_score)
            g_decision_score_history[0].decision_direction = 1;
        else if(sell_score > buy_score)
            g_decision_score_history[0].decision_direction = -1;
        else
            g_decision_score_history[0].decision_direction = 0;
        
        // 更新历史记录计数
        if(g_decision_history_count < 5)
        {
            g_decision_history_count++;
        }
        
        g_last_decision_time = TimeCurrent();
        
        // 添加调试信息
        Print("📊 决策评分历史更新 - 当前记录数:", g_decision_history_count, " 最新方向:", 
              (g_decision_score_history[0].decision_direction == 1 ? "买入" : 
               g_decision_score_history[0].decision_direction == -1 ? "卖出" : "无方向"));
    }
    
    // 计算前5个决策评分的主要方向 (修复版本)
    int CalculateHistoricalDirection()
    {
        // 检查是否有足够的历史数据
        if(g_decision_history_count < 3) 
        {
            Print("📊 历史方向计算: 数据不足，当前记录数:", g_decision_history_count);
            return 0;
        }
        
        // 计算前5个记录中买入和卖出的数量
        int buy_count = 0;
        int sell_count = 0;
        
        // 检查前5个记录（从位置1开始，因为位置0是当前记录）
        int check_count = MathMin(5, g_decision_history_count);
        for(int i = 1; i < check_count; i++)
        {
            if(g_decision_score_history[i].decision_direction == 1)
                buy_count++;
            else if(g_decision_score_history[i].decision_direction == -1)
                sell_count++;
        }
        
        Print("📊 历史方向计算: 买入=", buy_count, " 卖出=", sell_count, " 总记录=", check_count-1);
        
        if(buy_count > sell_count) 
        {
            Print("📊 历史方向: 买入");
            return 1;
        }
        else if(sell_count > buy_count) 
        {
            Print("📊 历史方向: 卖出");
            return -1;
        }
        else 
        {
            Print("📊 历史方向: 无明确方向");
            return 0;
        }
    }
    

    

    
    // 应急仓位管理函数 - 基于反转信号（修复版本）
    bool CanTriggerEmergencyOrder(int order_type, double buy_score, double sell_score)
    {
        // 🚨 修改：应急仓位基于反转信号，不再限制与普通仓相反
        // 条件1: 普通仓位已满
        if(CountNormalOrders() < MaxNormalOrders)
        {
            Print("📊 应急仓位触发失败: 普通仓位未满(", CountNormalOrders(), "/", MaxNormalOrders, ")");
            return false; // 普通仓位未满，不需要应急仓位
        }
        
        // 条件2: 应急仓位未满
        int emergency_count = CountEmergencyOrders();
        if(emergency_count >= EmergencyOrderCount)
        {
            Print("📊 应急仓位触发失败: 应急仓位已满(", emergency_count, "/", EmergencyOrderCount, ")");
            return false; // 应急仓位已满
        }
        
        // 新增：应急仓位频率控制
        datetime current_time = TimeCurrent();
        if(g_last_emergency_order_time > 0 && current_time - g_last_emergency_order_time < MinOrderInterval)
        {
            int remaining = (int)(MinOrderInterval - (current_time - g_last_emergency_order_time));
            Print("⏰ 应急仓位建仓间隔不足，还需等待 ", remaining/60, "分", remaining%60, "秒");
            Print("   上次建仓时间: ", TimeToString(g_last_emergency_order_time));
            Print("   当前时间: ", TimeToString(current_time));
            Print("   间隔要求: ", MinOrderInterval/60, "分钟");
            return false;
        }
        

        
        Print("📊 应急仓位触发检查 - 买入评分:", DoubleToString(buy_score, 6), " 卖出评分:", DoubleToString(sell_score, 6));
        
        // 条件3: 检查历史决策评分反转信号
        if(!g_current_reversal_signal.has_reversal || !g_current_reversal_signal.is_valid)
        {
            Print("📊 应急仓位触发失败: 未检测到决策评分反转信号");
            return false;
        }
        
        Print("✅ 应急仓位决策评分反转信号确认: 信号方向=", g_current_reversal_signal.signal_direction == OP_BUY ? "买入" : "卖出", " 评分=", g_current_reversal_signal.confidence);
        Print("📊 应急仓位建仓方向: ", order_type == OP_BUY ? "买入" : "卖出", " (基于决策评分反转)");
        
        // 条件5: 市场状态检查
        if(MarketInfo(Symbol(), MODE_SPREAD) > 50)
        {
            Print("📊 应急仓位触发失败: 点差过大");
            return false;
        }
        
        Print("🚨 应急仓位触发条件满足，准备建仓");
        return true;
    }
    
    // 检查市场状态是否适合应急仓位
    bool IsMarketSuitableForEmergency()
    {
        // 点差检查
        if(MarketInfo(Symbol(), MODE_SPREAD) > 50)
        {
            return false;
        }
        
        // 使用缓存的技术指标，避免重复计算
        double atr = indicator_cache.GetATR();
        double adx = indicator_cache.GetADX();
        
        // 波动率检查
        double avg_atr = GetAverageATR(14);
        if(atr > avg_atr * 2.0)
        {
            return false; // 波动率过高
        }
        
        // 趋势强度检查
        if(adx < 15)
        {
            return false; // 趋势不明显
        }
        
        return true;
    }
    
    // 执行应急仓位建仓（修复版本）
    void ExecuteEmergencyOrder(int order_type, double buy_score, double sell_score)
    {
        // 重新检查触发条件
        if(!CanTriggerEmergencyOrder(order_type, buy_score, sell_score))
        {
            return;
        }
        
        // 使用传入的order_type方向建仓，不再强制使用反转信号方向
        int emergency_order_type = order_type;
        
        if(emergency_order_type == OP_BUY)
        {
            // 不设置止盈止损，完全由EA控制
            Print("🔍 应急买入订单创建调试:");
            Print("   手数: ", EmergencyLotSize);
            Print("   价格: ", Ask);
            Print("   注释: '应急买入'");
            Print("   Magic Number: 12345");
            Print("   时间: ", TimeToString(TimeCurrent()));
            
            int ticket = OrderSend(Symbol(), OP_BUY, EmergencyLotSize, Ask, 
                                  (int)MaxSlippage, 
                                  Ask - EmergencyStopLoss * Point, Ask + EmergencyProfitTarget * Point,  // 止损=4000点，止盈=250点
                                  "应急买入", 12345, 0, clrYellow);
                                  
            if(ticket > 0)
            {
                g_emergency_order_count++;
                // 更新应急仓位建仓时间
                g_last_emergency_order_time = TimeCurrent();
                Print("✅ 应急仓位建仓时间已更新: ", TimeToString(g_last_emergency_order_time));
                Print("🚨 应急买入仓位建仓成功: 订单=", ticket, " 手数=", EmergencyLotSize, 
                      " 止损=0点 止盈=250点 (MT4系统控制)");
            }
            else
            {
                Print("❌ 应急买入仓位建仓失败，不更新建仓时间");
                int error = GetLastError();
                Print("❌ 应急买入仓位建仓失败: 错误=", error);
            }
        }
        else if(emergency_order_type == OP_SELL)
        {
            // 不设置止盈止损，完全由EA控制
            Print("🔍 应急卖出订单创建调试:");
            Print("   手数: ", EmergencyLotSize);
            Print("   价格: ", Bid);
            Print("   注释: '应急卖出'");
            Print("   Magic Number: 12345");
            Print("   时间: ", TimeToString(TimeCurrent()));
            
            int ticket = OrderSend(Symbol(), OP_SELL, EmergencyLotSize, Bid, 
                                  (int)MaxSlippage, 
                                  Bid + EmergencyStopLoss * Point, Bid - EmergencyProfitTarget * Point,  // 止损=4000点，止盈=250点
                                  "应急卖出", 12345, 0, clrOrange);
                                  
            if(ticket > 0)
            {
                g_emergency_order_count++;
                // 更新应急仓位建仓时间
                g_last_emergency_order_time = TimeCurrent();
                Print("✅ 应急仓位建仓时间已更新: ", TimeToString(g_last_emergency_order_time));
                Print("🚨 应急卖出仓位建仓成功: 订单=", ticket, " 手数=", EmergencyLotSize, 
                      " 止损=0点 止盈=250点 (MT4系统控制)");
            }
            else
            {
                Print("❌ 应急卖出仓位建仓失败，不更新建仓时间");
                int error = GetLastError();
                Print("❌ 应急卖出仓位建仓失败: 错误=", error);
            }
        }
    }
    
    // CountEmergencyOrders函数已移至全局作用域
    
    // GetAverageATR函数已移至全局作用域
    
private:
    bool WriteMarketDataToFile()
    {
        int handle = FileOpen(data_file_name, FILE_WRITE|FILE_CSV);
        if(handle != INVALID_HANDLE)
        {
                    // 获取服务器时间
        datetime server_time = TimeCurrent();
        string server_time_str = TimeToString(server_time);
        
        // 使用MT4客户端时间作为本地时间（更准确）
        datetime client_time = TimeLocal();
        string client_time_str = TimeToString(client_time);
        
        // 写入时间信息作为前两行
        FileWrite(handle, "ServerTime", server_time_str);
        FileWrite(handle, "ClientTime", client_time_str);
            
            // 写入最近50个数据点
            for(int idx1 = 49; idx1 >= 0; idx1--)
            {
                string time_str = TimeToString(Time[idx1]);
                FileWrite(handle, time_str, Open[idx1], High[idx1], Low[idx1], Close[idx1], Volume[idx1]);
            }
            FileClose(handle);
            Print("📊 市场数据已写入，服务器时间: ", server_time_str, " 客户端时间: ", client_time_str);
            return true;
        }
        else
        {
            Print("无法创建数据文件: ", data_file_name, " 错误代码: ", GetLastError());
            return false;
        }
    }
    
    bool ReadPredictionFromFile(int &prediction, double &confidence)
    {
        int handle = FileOpen(prediction_file_name, FILE_READ|FILE_TXT);
        if(handle != INVALID_HANDLE)
        {
            string line = FileReadString(handle);
            FileClose(handle);
            
            if(line != "")
            {
                return ParsePredictionLine(line, prediction, confidence);
            }
        }
        
        return false;
    }
    
    bool ParsePredictionLine(string line, int &prediction, double &confidence)
    {
        // 解析格式: "prediction,confidence,timestamp"
        int comma1 = StringFind(line, ",");
        if(comma1 >= 0)
        {
            string pred_str = StringSubstr(line, 0, comma1);
            prediction = (int)StringToInteger(pred_str);
            
            int comma2 = StringFind(line, ",", comma1 + 1);
            if(comma2 >= 0)
            {
                string conf_str = StringSubstr(line, comma1 + 1, comma2 - comma1 - 1);
                confidence = StringToDouble(conf_str);
                return true;
            }
        }
        
        return false;
    }
    

    

};

//+------------------------------------------------------------------+
//| 交易执行类
//+------------------------------------------------------------------+
class CTradeExecutor
{
private:
    CMoneyManager *money_manager;
    CRiskManager *risk_manager;
    CMarketMonitor *market_monitor;
    CAIPredictor *ai_predictor;
    
public:
    void Init(CMoneyManager &mm, CRiskManager &rm, CMarketMonitor &mcm, CAIPredictor &ap)
    {
        money_manager = &mm;
        risk_manager = &rm;
        market_monitor = &mcm;
        ai_predictor = &ap;
    }
    
    void ExecuteTradingLogic()
    {
        // 1. 更新账户信息
        money_manager.UpdateAccountInfo();
        
        // 2. 检查账户健康状态 - 已删除，不再需要回撤检查
        
        // 3. 检查市场状态
        bool market_suitable = market_monitor.IsMarketSuitable();
        if(!market_suitable)
        {
            Print("市场状态不适合交易 - 但继续获取AI预测");
        }
        
        // 4. 获取AI预测（强制获取，无论市场状态如何）
        int ai_prediction = -1;
        double ai_confidence = 0.0;
        bool has_ai_signal = false;
        
        if(EnableAI)
        {
            Print("正在获取AI预测...(已禁用AI计分)");
            has_ai_signal = ai_predictor.GetAIPrediction(ai_prediction, ai_confidence);
            if(has_ai_signal)
            {
                Print("AI预测成功: ", ai_prediction, " 置信度: ", ai_confidence);
            }
            else
            {
                Print("AI预测失败或无信号");
            }
        }
        
        // 5. 更新AI信号历史
        if(has_ai_signal && ai_prediction != 1) // 非震荡信号
        {
            market_monitor.UpdateAISignalHistory(ai_prediction == 2 ? OP_BUY : OP_SELL);
        }
        
        // 5.5. 统一计算反转信号（基于决策评分历史对比）
        if(EnableDecisionScoreReversal)
        {
            // 计算基于决策评分历史对比的反转信号（不依赖持仓方向）
            g_current_reversal_signal = ai_predictor.CalculateUnifiedReversalSignal();
            
            // 监控反转信号（仅用于记录）
            if(g_current_reversal_signal.has_reversal)
            {
                Print("📊 统一反转信号检测: 方向=", g_current_reversal_signal.signal_direction == OP_BUY ? "买入" : "卖出", 
                      " 评分=", g_current_reversal_signal.confidence);
            }
        }
        
        // 6. 计算决策评分（用于应急仓位检查）
        double buy_score = 0.0, sell_score = 0.0;
        CalculateDecisionScores(buy_score, sell_score);
        
        // 6.5. 检查并执行智能加仓（在原有逻辑之后）
        ::CheckAndExecuteSmartBuy(ai_confidence, buy_score, sell_score, ai_prediction);
        
        // 7. 检查应急仓位触发条件（基于反转信号，不再限制与普通仓相反）
        ::UpdateEmergencyOrderCount(); // 更新应急仓位计数
        
        // 🚨 添加详细调试日志
        int normal_count = ::CountNormalOrders();
        int emergency_count = ::CountEmergencyOrders();
        Print("📊 应急仓位触发检查 - 普通仓位:", normal_count, "/", MaxNormalOrders, " 应急仓位:", emergency_count, "/", EmergencyOrderCount);
        
        if(::CountNormalOrders() >= MaxNormalOrders)
        {
            Print("📊 普通仓位已满，开始检查应急仓位触发条件");
            
            // 🚨 使用已计算的决策评分，避免重复计算
            Print("📊 决策评分计算 - 买入:", DoubleToString(buy_score, 6), " 卖出:", DoubleToString(sell_score, 6));
            
            // 检查应急仓位触发条件 - 基于历史决策评分反转
            Print("📊 开始检查应急仓位触发条件");
            
            // 检查是否有历史决策评分反转信号
            if(g_current_reversal_signal.has_reversal && g_current_reversal_signal.is_valid)
            {
                Print("🔄 检测到决策评分反转信号，开始检查应急仓位触发条件");
                Print("📊 反转信号: 方向=", g_current_reversal_signal.signal_direction == OP_BUY ? "买入" : "卖出", 
                      " 评分=", g_current_reversal_signal.confidence);
                
                // 基于反转信号确定应急仓位方向
                int emergency_direction = g_current_reversal_signal.signal_direction;
                Print("📊 应急仓位方向: ", emergency_direction == OP_BUY ? "买入" : "卖出", " (基于决策评分反转)");
                
                if(ai_predictor.CanTriggerEmergencyOrder(emergency_direction, buy_score, sell_score))
                {
                    Print("🚨 应急仓位触发条件满足，准备建仓");
                    ai_predictor.ExecuteEmergencyOrder(emergency_direction, buy_score, sell_score);
                }
                else
                {
                    Print("📊 应急仓位触发失败: 其他条件不满足");
                }
            }
            else
            {
                Print("📊 应急仓位触发失败: 未检测到决策评分反转信号");
            }
        }
        else
        {
            Print("📊 应急仓位检查跳过: 普通仓位未满(", normal_count, "/", MaxNormalOrders, ")");
        }
        
        // 7. 综合决策 - 使用已计算的决策评分
        int final_decision = MakeFinalDecision(ai_prediction, ai_confidence, has_ai_signal, market_suitable, buy_score, sell_score);
        
        // 8. 位置风险检查
        if(final_decision != -1)
        {
            bool position_suitable = market_monitor.IsPositionSuitableComprehensive(final_decision, ai_confidence);
            if(!position_suitable)
            {
                Print("🚫 位置风险控制阻止开仓");
                return;
            }
        }
        
        // 9. 信号确认检查
        if(EnableSignalConfirmation && final_decision != -1)
        {
            if(!ConfirmSignal(final_decision))
            {
                Print("信号未确认，跳过开仓");
                return;
            }
        }
        
        // 10. 检查锁仓触发
        risk_manager.CheckAndTriggerProgressiveLock(ai_prediction, ai_confidence);
        
        // 11. 执行交易 - 只有在市场适合时才执行
        if(final_decision != -1 && market_suitable)
        {
            ExecuteOrder(final_decision);
        }
        else if(final_decision != -1 && !market_suitable)
        {
            Print("有交易信号但市场不适合，跳过开仓");
        }
    }
    
private:
    int MakeFinalDecision(int ai_prediction, double ai_confidence, bool has_ai_signal, bool market_suitable, double buy_score, double sell_score)
    {
        // 使用已计算的决策评分，避免重复计算
        // 直接使用传入的buy_score和sell_score参数
        
        Print("🎯 使用已计算的决策评分 - 买入: ", DoubleToString(buy_score, 2), " 卖出: ", DoubleToString(sell_score, 2));
        
        // 最终决策 - 优化阈值平衡交易频率和质量
        double decision_threshold = 0.45; // 下调至0.45，配合渐进式评分系统
        if(buy_score > decision_threshold && buy_score > sell_score)
            return OP_BUY;
        else if(sell_score > decision_threshold && sell_score > buy_score)
            return OP_SELL;
            
        return -1; // 无明确信号
    }
    

    
    void ExecuteOrder(int order_type)
    {
        // 检查交易权限
        if(!IsTradeAllowed())
        {
            Print("交易被禁用，请检查账户设置");
            return;
        }
        
        if(IsTradeContextBusy())
        {
            Print("交易上下文繁忙，请稍后重试");
            return;
        }
        

        
        // 检查是否已有相同方向的订单
        if(risk_manager.HasSameDirectionOrder(order_type))
        {
            return;
        }
        
        // 建仓频率控制检查
        if(!CanPlaceNormalOrder())
        {
            Print("⏰ 建仓频率限制：普通仓建仓被阻止");
            return;
        }
        
        // 全局建仓频率控制检查
        if(!CTradeCounter::CanPlaceOrder())
        {
            Print("⏰ 全局建仓频率限制：1分钟内只能建仓一次");
            return;
        }
        
        // 风险控制检查已禁用 - 允许AI自由交易
        // if(!risk_manager.CanOpenNewOrder(order_type))
        // {
        //     Print("风险控制阻止开仓");
        //     return;
        // }
        
        // 计算手数
        double lot_size = money_manager.CalculateSafeLotSize(50.0);
        
        if(order_type == OP_BUY)
        {
            Print("🔍 普通买入订单创建调试:");
            Print("   手数: ", lot_size);
            Print("   价格: ", Ask);
            Print("   注释: '普通订单'");
            Print("   Magic Number: 12345");
            Print("   时间: ", TimeToString(TimeCurrent()));
            
            int ticket = OrderSend(Symbol(), OP_BUY, lot_size, Ask, (int)MaxSlippage, 
                                 0.0, Ask + 250 * Point,  // 止损=0，止盈=250点
                                 "普通订单", 12345, 0.0, clrGreen);
                                 
            if(ticket > 0)
            {
                Print("买入订单执行成功，订单号: ", ticket, " 手数: ", lot_size, 
                      " 模式: 智能平仓");

                // 更新普通订单建仓时间
                g_last_normal_order_time = TimeCurrent();
                Print("✅ 普通订单建仓时间已更新: ", TimeToString(g_last_normal_order_time));
                
                // 重置信号确认
                g_signal_confirm_ticks = 0;
                g_signal_confirmed = false;
            }
            else
            {
                int error = GetLastError();
                CErrorHandler::HandleOrderError(error, "买入订单");
                
                // 详细错误信息
                switch(error)
                {
                    case 133: Print("错误133: 交易被禁用 - 请检查账户设置和交易权限"); break;
                    case 134: Print("错误134: 资金不足"); break;
                    case 135: Print("错误135: 价格已改变"); break;
                    case 136: Print("错误136: 离线交易"); break;
                    case 137: Print("错误137: 经纪商忙"); break;
                    case 138: Print("错误138: 重新报价"); break;
                    case 139: Print("错误139: 订单被锁定"); break;
                    case 146: Print("错误146: 交易子系统忙"); break;
                    default: Print("未知错误: ", error); break;
                }
            }
        }
        else if(order_type == OP_SELL)
        {
            Print("🔍 普通卖出订单创建调试:");
            Print("   手数: ", lot_size);
            Print("   价格: ", Bid);
            Print("   注释: '普通订单'");
            Print("   Magic Number: 12345");
            Print("   时间: ", TimeToString(TimeCurrent()));
            
            int sell_ticket = OrderSend(Symbol(), OP_SELL, lot_size, Bid, (int)MaxSlippage, 
                                 0.0, Bid - 250 * Point,  // 止损=0，止盈=250点
                                 "普通订单", 12345, 0.0, clrRed);
                                 
            if(sell_ticket > 0)
            {
                Print("卖出订单执行成功，订单号: ", sell_ticket, " 手数: ", lot_size,
                      " 模式: 智能平仓");

                // 更新普通订单建仓时间
                g_last_normal_order_time = TimeCurrent();
                Print("✅ 普通订单建仓时间已更新: ", TimeToString(g_last_normal_order_time));
                
                // 重置信号确认
                g_signal_confirm_ticks = 0;
                g_signal_confirmed = false;
            }
            else
            {
                int sell_error = GetLastError();
                CErrorHandler::HandleOrderError(sell_error, "卖出订单");
                
                // 详细错误信息
                switch(sell_error)
                {
                    case 133: Print("错误133: 交易被禁用 - 请检查账户设置和交易权限"); break;
                    case 134: Print("错误134: 资金不足"); break;
                    case 135: Print("错误135: 价格已改变"); break;
                    case 136: Print("错误136: 离线交易"); break;
                    case 137: Print("错误137: 经纪商忙"); break;
                    case 138: Print("错误138: 重新报价"); break;
                    case 139: Print("错误139: 订单被锁定"); break;
                    case 146: Print("错误146: 交易子系统忙"); break;
                    default: Print("未知错误: ", sell_error); break;
                }
            }
        }
    }
    

    
public:
    // 检查交易状态
    void CheckTradingStatus()
    {
        Print("=== 交易状态检查 ===");
        Print("交易允许: ", IsTradeAllowed() ? "是" : "否");
        Print("交易上下文繁忙: ", IsTradeContextBusy() ? "是" : "否");
        Print("自动交易: ", IsExpertEnabled() ? "是" : "否");
        Print("账户余额: ", AccountBalance());
        Print("账户净值: ", AccountEquity());
        Print("可用保证金: ", AccountFreeMargin());
        Print("当前点差: ", MarketInfo(Symbol(), MODE_SPREAD));
        Print("最小手数: ", MarketInfo(Symbol(), MODE_MINLOT));
        Print("最大手数: ", MarketInfo(Symbol(), MODE_MAXLOT));
        Print("==================");
    }
    
    // 信号确认方法
    bool ConfirmSignal(int signal)
    {
        if(signal == g_last_signal)
        {
            g_signal_confirm_ticks++;
            if(g_signal_confirm_ticks >= SignalConfirmTicks)
            {
                g_signal_confirmed = true;
                // Print("信号确认完成，持续 ", g_signal_confirm_ticks, " 个tick"); // 注释减少内存使用
                return true;
            }
            else
            {
                // Print("信号确认中，已持续 ", g_signal_confirm_ticks, "/", SignalConfirmTicks, " 个tick"); // 注释减少内存使用
                return false;
            }
        }
        else
        {
            // 信号改变，重置确认计数
            g_last_signal = signal;
            g_signal_confirm_ticks = 1;
            g_signal_confirmed = false;
            Print("信号改变，开始确认新信号");
            return false;
        }
    }
    

};

//+------------------------------------------------------------------+
//| 平仓管理类
//+------------------------------------------------------------------+
class CCloseManager
{
private:
    CAIPredictor *ai_predictor;
    CMarketMonitor *market_monitor;
    
public:
    void Init(CAIPredictor &ap, CMarketMonitor &mcm)
    {
        ai_predictor = &ap;
        market_monitor = &mcm;
    }
    
    void CheckAndCloseOrders()
    {
        if(!EnableSmartClose) {
            Print("❌ 智能平仓已禁用，跳过平仓检查");
            return;
        }
        
        Print("🔍 开始检查订单，总订单数: ", OrdersTotal());
        for(int idx2 = OrdersTotal() - 1; idx2 >= 0; idx2--)
        {
            if(OrderSelect(idx2, SELECT_BY_POS, MODE_TRADES))
            {
                if(IsOurOrder())
                {
                    double current_profit = ::GetCurrentOrderTotalProfit();
                    string comment = OrderComment();
                    bool is_smart_buy = (StringFind(comment, "智能加仓") >= 0);
                    bool is_emergency = (StringFind(comment, "应急") >= 0);
                    
                    // 0. 250点盈利平仓（最高优先级）- 智能加仓订单和应急仓位除外
                    if(!is_smart_buy && !is_emergency) // 智能加仓订单和应急仓位跳过通用250点盈利平仓
                    {
                        // 修复：点位计算（current_profit已经包含手数信息）
                        double profit_pips = current_profit / Point; // 正确计算点位
                        Print("📊 订单 ", OrderTicket(), " 盈利检查: 美元=", current_profit, " 点位=", profit_pips, " 手数=", OrderLots());
                        if(profit_pips >= 250.0)
                        {
                            Print("🎯 订单 ", OrderTicket(), " 达到250点盈利，执行平仓");
                            CloseOrder(OrderTicket(), "250点盈利平仓");
                            continue;
                        }
                    }
                    else if(is_emergency)
                    {
                        Print("🚨 应急仓位 ", OrderTicket(), " 跳过通用250点盈利平仓检查，使用应急仓位专用平仓逻辑");
                    }
                    else if(is_smart_buy)
                    {
                        Print("🔒 智能加仓订单 ", OrderTicket(), " 跳过通用250点盈利平仓检查，使用独立平仓逻辑");
                    }
                    else
                    {
                        Print("🔒 智能加仓订单 ", OrderTicket(), " 跳过通用250点盈利平仓检查，使用独立平仓逻辑");
                    }
                    
                    // 锁仓单检查：先检查亏损平仓，再检查分层解锁
                    if(CLockOrderProtector::IsCurrentLockOrder())
                    {
                        Print("🔒 锁仓单 ", OrderTicket(), " 进入锁仓单平仓检查");
                        // 检查锁仓单亏损平仓
                        if(CheckLockOrderLossLimit(OrderTicket())) {
                            continue;
                        }
                        // 锁仓单分层解锁检查（300点）
                        if(CheckLockUnlockCondition(OrderTicket())) {
                            continue;
                        }
                        // 锁仓单跳过其他平仓逻辑，但保留移动止损
                        CTrailingStopManager::CheckTrailingStop(OrderTicket());
                        continue;
                    }
                    
                    // 1. 决策评分反转平仓（第二优先级）
                    if(CheckDecisionReversalClose(OrderTicket())) continue;
                    
                    // 1.5. 应急仓位特殊处理（新增）
                    if(CheckEmergencyOrderClose(OrderTicket())) continue;
                    
                    // 1.6. 智能加仓订单特殊处理（新增）
                    if(CheckSmartBuyOrderClose(OrderTicket())) continue;
                    
                    // 2. 紧急止损（第三优先级）
                    if(CheckEmergencyStopLoss(OrderTicket())) continue;
                    // 3. 亏损管理（含扛单）
                    if(current_profit < 0 && CheckLossManagement(OrderTicket())) continue;
                    // 4. 技术指标平仓（AI信号只做辅助）
                    if(CheckTechnicalCloseCondition(OrderTicket())) continue;
                    // 5. 移动止损 - 应急订单和智能加仓订单跳过移动止损
                    if(!is_emergency && !is_smart_buy)
                    {
                        CTrailingStopManager::CheckTrailingStop(OrderTicket());
                    }
                    else if(is_emergency)
                    {
                        Print("🚨 应急订单 ", OrderTicket(), " 跳过移动止损检查");
                    }
                    else if(is_smart_buy)
                    {
                        Print("🔒 智能加仓订单 ", OrderTicket(), " 跳过移动止损检查");
                    }
                }
            }
        }
    }
    
private:
    
    // 决策评分反转平仓检查 - 应急订单和智能加仓订单跳过反转信号平仓
    bool CheckDecisionReversalClose(int ticket)
    {
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        
        string comment = OrderComment();
        bool is_emergency = (StringFind(comment, "应急") >= 0);
        bool is_smart_buy = (StringFind(comment, "智能加仓") >= 0);
        
        // 🚫 修改：锁仓单、应急订单、智能加仓订单都不执行反转信号平仓
        if(CLockOrderProtector::IsCurrentLockOrder())
        {
            // 🚫 锁仓单：不执行反转信号平仓，保持扛单
            Print("🔒 锁仓单 ", ticket, " 检测到反转信号，但不执行平仓，继续扛单");
            return false;
        }
        else if(is_emergency)
        {
            // 🚫 应急订单：不执行反转信号平仓，保持扛单
            Print("🚨 应急订单 ", ticket, " 检测到反转信号，但不执行平仓，继续扛单");
            return false;
        }
        else if(is_smart_buy)
        {
            // 🚫 智能加仓订单：不执行反转信号平仓，保持扛单
            Print("🔒 智能加仓订单 ", ticket, " 检测到反转信号，但不执行平仓，继续扛单");
            return false;
        }
        else
        {
            // 普通仓位：反转信号后保持持有，不平仓
            Print("📊 普通仓位 ", ticket, " 检测到反转信号，但保持持有进行扛单");
        }
        
        return false;
    }
    
    // 分批平仓条件检查 - 仅用于锁仓单
    bool CheckBatchCloseCondition(int ticket, double reversal_confidence)
    {
        static datetime last_batch_close_time = 0;
        static int batch_close_count = 0;
        
        datetime current_time = TimeCurrent();
        
        // 检查是否到了分批平仓时间
        if(current_time - last_batch_close_time >= BatchCloseInterval)
        {
            // 根据置信度决定平仓概率
            double close_probability = reversal_confidence * 0.8; // 降低平仓概率
            double random_value = MathRand() / 32768.0;
            
            if(random_value < close_probability)
            {
                CloseOrder(ticket, "锁仓单决策评分反转分批平仓 - 评分:" + DoubleToString(reversal_confidence, 2));
                last_batch_close_time = current_time;
                batch_close_count++;
                return true;
            }
        }
        
        return false;
    }
    
    // 锁仓单分层解锁检查
    bool CheckLockUnlockCondition(int ticket)
    {
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        
        string comment = OrderComment();
        
        // 检查是否是锁仓单
        if(StringFind(comment, "锁仓") >= 0)
        {
            double current_profit = ::GetCurrentOrderTotalProfit();
            double profit_pips = current_profit / Point; // 修复：点位计算（current_profit已经包含手数信息）
            
            Print("🔒 锁仓单 ", ticket, " 分层解锁检查: 盈利=", profit_pips, "点 目标=", UnlockProfit, "点");
            
            // 锁仓单解锁检查：达到300点盈利时解锁
            if(profit_pips >= UnlockProfit)
            {
                Print("💰 锁仓订单 ", ticket, " 盈利达到", UnlockProfit, "点，执行分层解锁");
                CloseOrder(ticket, "锁仓分层解锁");
                return true;
            }
        }
        
        return false;
    }
    
    // 锁仓单亏损平仓检查
    bool CheckLockOrderLossLimit(int ticket)
    {
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        
        string comment = OrderComment();
        
        // 检查是否是锁仓单
        if(StringFind(comment, "锁仓") >= 0)
        {
            double current_profit = ::GetCurrentOrderTotalProfit();
            double loss_pips = MathAbs(current_profit) / Point; // 修复：点位计算（current_profit已经包含手数信息）
            
            if(loss_pips >= LockOrderLossLimit)
            {
                CloseOrder(ticket, "锁仓单亏损平仓 - " + DoubleToString(loss_pips, 0) + "点");
                return true;
            }
        }
        
        return false;
    }
    
    bool CheckTechnicalCloseCondition(int ticket)
    {
        if(!EnableTechnicalClose || !EnableSmartCloseOnly) return false;
        
        // 新增：智能加仓订单和应急订单不执行技术指标平仓
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        string comment = OrderComment();
        if(StringFind(comment, "智能加仓") >= 0)
        {
            Print("🔒 智能加仓订单 ", ticket, " 跳过技术指标平仓检查");
            return false; // 智能加仓订单跳过技术指标平仓
        }
        
        // 新增：应急订单跳过技术指标平仓
        if(StringFind(comment, "应急") >= 0)
        {
            Print("🚨 应急订单 ", ticket, " 跳过技术指标平仓检查");
            return false; // 应急订单跳过技术指标平仓
        }
        
        // 使用缓存的技术指标 - 性能优化
        double ma_fast = indicator_cache.GetMA(12);  // 12周期EMA（黄金优化）
        double ma_slow = indicator_cache.GetMA(26);  // 26周期EMA（黄金优化）
        double ma_long = indicator_cache.GetMA(50);
        double rsi = indicator_cache.GetRSI();
        double adx = indicator_cache.GetADX();
        // AI信号辅助
        int ai_prediction = -1;
        double ai_confidence = 0.0;
        bool ai_ok = ai_predictor.GetAIPrediction(ai_prediction, ai_confidence);

        double current_profit = ::GetCurrentOrderTotalProfit();
        double profit_pips = current_profit / Point; // 修复：XAUUSD 1点=0.01美元(0.01手)
        // MA交叉平仓
        if(OrderType() == OP_BUY && ma_fast < ma_slow) {
            if(ma_slow > ma_long && Close[0] > ma_slow) return false;
            if(profit_pips > 0 && MathAbs(ma_fast - ma_slow) < 0.0001) return false;
            // 扛单策略：亏损订单不因MA交叉平仓
            if(EnableHoldStrategy && profit_pips < 0) return false;
            // AI信号辅助过滤：如果AI预测与当前持仓方向一致且置信度高，则不平仓
            if(ai_ok && ai_confidence > 0.8 && ai_prediction == 2) return false;
            CloseOrder(ticket, "MA交叉反转+AI辅助");
            return true;
        } else if(OrderType() == OP_SELL && ma_fast > ma_slow) {
            if(ma_slow < ma_long && Close[0] < ma_slow) return false;
            if(profit_pips > 0 && MathAbs(ma_fast - ma_slow) < 0.0001) return false;
            // 扛单策略：亏损订单不因MA交叉平仓
            if(EnableHoldStrategy && profit_pips < 0) return false;
            if(ai_ok && ai_confidence > 0.8 && ai_prediction == 0) return false;
            CloseOrder(ticket, "MA交叉反转+AI辅助");
            return true;
        }
        // RSI超买超卖（黄金期货优化阈值）
        if(OrderType() == OP_BUY && rsi > RSIOverbought) {
            if(profit_pips > 0 && rsi < 85.0) return false; // 调整为85，与新的RSI阈值一致
            // 扛单策略：亏损订单不因RSI超买平仓
            if(EnableHoldStrategy && profit_pips < 0) return false;
            if(ai_ok && ai_confidence > 0.8 && ai_prediction == 2) return false;
            CloseOrder(ticket, "RSI超买+AI辅助");
            return true;
        } else if(OrderType() == OP_SELL && rsi < RSIOversold) {
            if(profit_pips > 0 && rsi > 15.0) return false; // 调整为15，与新的RSI阈值一致
            // 扛单策略：亏损订单不因RSI超卖平仓
            if(EnableHoldStrategy && profit_pips < 0) return false;
            if(ai_ok && ai_confidence > 0.8 && ai_prediction == 0) return false;
            CloseOrder(ticket, "RSI超卖+AI辅助");
            return true;
        }
        // ADX趋势消失
        if(adx < ADXThreshold) {
            if(profit_pips > 0 && adx > 8.0) return false;
            // 扛单策略：亏损订单不因ADX趋势消失平仓
            if(EnableHoldStrategy && profit_pips < 0) return false;
            CloseOrder(ticket, "ADX趋势消失");
            return true;
        }
        return false;
    }
    
    bool CheckLossManagement(int ticket)
    {
        if(!EnableLossManagement) return false;
        
        // 锁仓单保护：跳过亏损管理
        if(CLockOrderProtector::IsCurrentLockOrder())
        {
            return false; // 锁仓单不执行亏损管理
        }
        
        // 新增：应急订单保护：跳过亏损管理
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        string comment = OrderComment();
        if(StringFind(comment, "应急") >= 0)
        {
            Print("🚨 应急订单 ", ticket, " 跳过亏损管理检查");
            return false; // 应急订单跳过亏损管理
        }
        
        double current_profit = ::GetCurrentOrderTotalProfit();
        if(current_profit >= 0) return false; // 只处理亏损单
        
        double loss_pips = MathAbs(current_profit) / Point; // 修复：点位计算（current_profit已经包含手数信息）
        
        // 扛单模式下的亏损管理逻辑
        if(EnableHoldStrategy)
        {
            // 1. 扛单范围内（10000点以内）- 坚持持有
            if(loss_pips <= MaxHoldLossPips)
            {
        
                return false; // 不平仓，继续扛单
            }
            
            // 2. 超过扛单极限时的处理
            if(loss_pips > MaxHoldLossPips)
            {
                // 检查是否有反转信号支持继续扛单
                if(HasReversalSignal(ticket))
                {
            
                    return false; // 有反转信号，继续扛单
                }
                else
                {
                    CloseOrder(ticket, "扛单极限平仓 - 亏损" + DoubleToString(loss_pips, 1) + "点");
                    Print("🔴 扛单极限触发且无反转信号 - 订单: " + DoubleToString(ticket, 0) + " 亏损: " + DoubleToString(loss_pips, 1) + " 点");
                    return true; // 强制平仓
                }
            }
        }
        
        return false;
    }
    
    // 扛单策略已合并进亏损管理，不再单独调用
    // ... existing code ...
    
    // 应急仓位平仓检查
    bool CheckEmergencyOrderClose(int ticket)
    {
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        
        // 检查是否是应急仓位
        string comment = OrderComment();
        if(StringFind(comment, "应急") < 0)
        {
            return false; // 不是应急仓位
        }
        
        // 应急仓位基于点位检查平仓条件
        double current_profit = OrderProfit() + OrderSwap() + OrderCommission();
        double profit_pips = current_profit / Point; // 修复：点位计算（current_profit已经包含手数信息）
        
        // 手动执行平仓逻辑
        if(profit_pips >= EmergencyProfitTarget)
        {
            Print("🎯 应急仓位达到盈利目标: 订单=", ticket, " 盈利=", profit_pips, "点 目标=", EmergencyProfitTarget, "点");
            CloseOrder(ticket, "应急仓位盈利目标平仓");
            return true;
        }
        else if(profit_pips <= -EmergencyStopLoss)
        {
            Print("🛑 应急仓位触发止损: 订单=", ticket, " 亏损=", profit_pips, "点 止损=", EmergencyStopLoss, "点");
            CloseOrder(ticket, "应急仓位止损平仓");
            return true;
        }
        
        return false; // 未达到平仓条件，继续持有
    }
    
    // 智能加仓订单平仓检查
    bool CheckSmartBuyOrderClose(int ticket)
    {
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) 
        {
            Print("❌ 智能加仓平仓检查失败：无法选择订单 ", ticket);
            return false;
        }
        
        // 检查是否是智能加仓订单
        string comment = OrderComment();
        Print("📊 智能加仓平仓检查：订单=", ticket, " 注释=", comment);
        
        if(StringFind(comment, "智能加仓") < 0)
        {
            Print("❌ 订单 ", ticket, " 不是智能加仓订单，跳过平仓检查");
            return false; // 不是智能加仓订单
        }
        
        // 智能加仓订单基于点位检查平仓条件
        double current_profit = OrderProfit() + OrderSwap() + OrderCommission();
        double profit_pips = current_profit / Point; // 修复：点位计算（current_profit已经包含手数信息）
        
        // 记录智能加仓订单状态
        Print("📊 智能加仓订单状态检查: 订单=", ticket, " 盈利=", profit_pips, "点 目标=", SmartBuyProfitTarget, "点 止损=", SmartBuyStopLoss, "点");
        
        // 手动执行平仓逻辑
        if(profit_pips >= SmartBuyProfitTarget)
        {
            Print("🎯 智能加仓订单达到盈利目标: 订单=", ticket, " 盈利=", profit_pips, "点 目标=", SmartBuyProfitTarget, "点");
            CloseOrder(ticket, "智能加仓盈利目标平仓");
            return true;
        }
        else if(profit_pips <= -SmartBuyStopLoss)
        {
            Print("🛑 智能加仓订单触发止损: 订单=", ticket, " 亏损=", profit_pips, "点 止损=", SmartBuyStopLoss, "点");
            CloseOrder(ticket, "智能加仓止损平仓");
            return true;
        }
        
        return false; // 未达到平仓条件，继续持有
    }
    
    bool CheckEmergencyStopLoss(int ticket)
    {
        // 锁仓单保护：跳过紧急止损
        if(CLockOrderProtector::IsCurrentLockOrder())
        {
            return false; // 锁仓单不执行紧急止损
        }
        
        // 新增：应急订单保护：跳过紧急止损
        if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
        string comment = OrderComment();
        if(StringFind(comment, "应急") >= 0)
        {
            Print("🚨 应急订单 ", ticket, " 跳过紧急止损检查");
            return false; // 应急订单跳过紧急止损
        }
        
        // 计算当前亏损
        double current_profit = ::GetCurrentOrderTotalProfit();
        double loss_pips = MathAbs(current_profit) / Point; // 修复：点位计算（current_profit已经包含手数信息）
        
        // 扛单模式下：不执行任何止损检查，完全扛单
        if(EnableHoldStrategy)
        {
            return false; // 扛单模式下不执行任何止损检查
        }
        

        
        return false;
    }
    
    
    
    
    
    // 检查是否有反转信号（扛单策略核心逻辑 - 简化版，避免Stack overflow）
    bool HasReversalSignal(int ticket)
    {
        // 简化反转信号检查
        if(EnableDecisionScoreReversal && g_current_reversal_signal.has_reversal && g_current_reversal_signal.is_valid)
        {
            return true; // 有反转信号，继续扛单
        }
        
        double current_profit = ::GetCurrentOrderTotalProfit();
        double loss_pips = MathAbs(current_profit) / Point; // 修复：点位计算（current_profit已经包含手数信息）
        
        // 简化扛单条件
        if(loss_pips <= MaxHoldLossPips)
        {
            return true; // 在扛单范围内
        }
        
            // 简化趋势检查 - 使用缓存避免重复计算
    double ma_50 = indicator_cache.GetMA(50);
    double current_price = (OrderType() == OP_BUY) ? Bid : Ask;
        
        if(OrderType() == OP_BUY && current_price > ma_50)
        {
            return true; // 买入订单价格在均线上方
        }
        else if(OrderType() == OP_SELL && current_price < ma_50)
        {
            return true; // 卖出订单价格在均线下方
        }
        
        return false;
    }
    

    

    
    // 检查长期趋势是否仍然有利 - 使用缓存避免重复计算
    bool CheckLongTermTrendFavorable(int ticket)
    {
        double ma_50 = indicator_cache.GetMA(50);
        double ma_200 = indicator_cache.GetMA(200); // 使用缓存获取MA200
        double current_price = (OrderType() == OP_BUY) ? Bid : Ask;
        
        // 买入订单：如果长期趋势向上，继续扛单
        if(OrderType() == OP_BUY)
        {
            if(ma_50 > ma_200 && current_price > ma_50)
                return true;
        }
        // 卖出订单：如果长期趋势向下，继续扛单
        else if(OrderType() == OP_SELL)
        {
            if(ma_50 < ma_200 && current_price < ma_50)
                return true;
        }
        
        return false;
    }
    
    // 检查反弹信号
    bool CheckBounceSignal(int ticket, double loss_pips)
    {
        // 获取最近的价格数据
        double close_0 = Close[0];
        double close_1 = Close[1];
        double close_2 = Close[2];
        
        
        // 检查是否出现反弹模式
        if(OrderType() == OP_BUY)
        {
            // 买入订单：检查是否出现底部反弹
            if(close_0 > close_1 && close_1 > close_2 && loss_pips > 50)
            {
                // 连续上涨，可能是反弹开始
                return true;
            }
        }
        else if(OrderType() == OP_SELL)
        {
            // 卖出订单：检查是否出现顶部回落
            if(close_0 < close_1 && close_1 < close_2 && loss_pips > 50)
            {
                // 连续下跌，可能是回落开始
                return true;
            }
        }
        
        return false;
    }
    
    // 检查波动性收缩 - 使用传入的ATR值，避免重复计算
    bool CheckVolatilityContraction(double atr)
    {
        // 计算平均ATR
        double avg_atr = 0;
        for(int ag = 1; ag <= 10; ag++)
        {
            avg_atr += iATR(Symbol(), Period(), 14, ag);
        }
        avg_atr /= 10;
        
        // 如果当前ATR明显低于平均ATR，说明波动性收缩
        if(avg_atr > 0 && atr < avg_atr * 0.7)
        {
            return true;
        }
        
        return false;
    }
    
    // 检查RSI反弹信号 - 使用传入的RSI值和统一阈值
    bool CheckRSIBounce(int ticket, double rsi)
    {
        if(OrderType() == OP_BUY)
        {
            // 买入订单：RSI超卖后开始回升
            if(rsi < RSIOversold && rsi > iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 1))
            {
                return true;
            }
        }
        else if(OrderType() == OP_SELL)
        {
            // 卖出订单：RSI超买后开始回落
            if(rsi > RSIOverbought && rsi < iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 1))
            {
                return true;
            }
        }
        
        return false;
    }
    
    // 检查重要支撑/阻力位
    bool CheckKeyLevelSupport(int ticket, double loss_pips)
    {
        double current_price = (OrderType() == OP_BUY) ? Bid : Ask;
        
        // 获取最近的支撑/阻力位
        double support_level = GetNearestSupport(current_price);
        double resistance_level = GetNearestResistance(current_price);
        
        if(OrderType() == OP_BUY)
        {
            // 买入订单：接近支撑位
            double distance_to_support = (current_price - support_level) / Point; // 修复：XAUUSD 1点=0.01美元
            if(distance_to_support < 20 && loss_pips > 50)
            {
                return true;
            }
        }
        else if(OrderType() == OP_SELL)
        {
            // 卖出订单：接近阻力位
            double distance_to_resistance = (resistance_level - current_price) / Point; // 修复：XAUUSD 1点=0.01美元
            if(distance_to_resistance < 20 && loss_pips > 50)
            {
                return true;
            }
        }
        
        return false;
    }
    
    // 获取最近的支撑位
    double GetNearestSupport(double current_price)
    {
        // 简化的支撑位计算：使用最近的低点
        double lowest = current_price;
        for(int ak = 1; ak <= 20; ak++)
        {
            if(Low[ak] < lowest)
                lowest = Low[ak];
        }
        return lowest;
    }
    
    // 获取最近的阻力位
    double GetNearestResistance(double current_price)
    {
        // 简化的阻力位计算：使用最近的高点
        double highest = current_price;
        for(int aj = 1; aj <= 20; aj++)
        {
            if(High[aj] > highest)
                highest = High[aj];
        }
        return highest;
    }
};

//+------------------------------------------------------------------+
//| 高级技术指标类 - 新增功能，不影响现有指标
//+------------------------------------------------------------------+
class CAdvancedIndicators
{
private:
    // 布林带缓存
    double cached_bb_upper;
    double cached_bb_middle;
    double cached_bb_lower;
    
    // MACD缓存
    double cached_macd_main;
    double cached_macd_signal;
    double cached_macd_histogram;
    
    // KDJ缓存
    double cached_k_value;
    double cached_d_value;
    double cached_j_value;
    
    datetime last_update_time;
    
public:
    CAdvancedIndicators()
    {
        last_update_time = 0;
        cached_bb_upper = 0;
        cached_bb_middle = 0;
        cached_bb_lower = 0;
        cached_macd_main = 0;
        cached_macd_signal = 0;
        cached_macd_histogram = 0;
        cached_k_value = 0;
        cached_d_value = 0;
        cached_j_value = 0;
    }
    
    void UpdateAdvancedIndicators()
    {
        datetime current_time = Time[0];
        
        // 每10个tick更新一次指标，确保实时性
        static int advanced_indicator_tick_count = 0;
        advanced_indicator_tick_count++;
        
        if(current_time != last_update_time || advanced_indicator_tick_count >= 10)
        {
            // 布林带计算 (20周期，2标准差) - 使用内置函数确保精度
            cached_bb_upper = iBands(Symbol(), Period(), 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 0);
            cached_bb_middle = iBands(Symbol(), Period(), 20, 2, 0, PRICE_CLOSE, MODE_MAIN, 0);
            cached_bb_lower = iBands(Symbol(), Period(), 20, 2, 0, PRICE_CLOSE, MODE_LOWER, 0);
            
            // MACD计算 (12,26,9) - 使用内置函数确保正确性
            cached_macd_main = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
            cached_macd_signal = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 0);
            cached_macd_histogram = cached_macd_main - cached_macd_signal;
            
            // KDJ计算 (5,3,3) - 使用内置函数确保正确性
            cached_k_value = iStochastic(Symbol(), Period(), 5, 3, 3, MODE_SMA, 0, MODE_MAIN, 0);
            cached_d_value = iStochastic(Symbol(), Period(), 5, 3, 3, MODE_SMA, 0, MODE_SIGNAL, 0);
            cached_j_value = 3 * cached_k_value - 2 * cached_d_value;
            
            last_update_time = current_time;
            advanced_indicator_tick_count = 0; // 重置tick计数
        }
    }
    
    // 布林带指标
    double GetBollingerUpper() { UpdateAdvancedIndicators(); return cached_bb_upper; }
    double GetBollingerMiddle() { UpdateAdvancedIndicators(); return cached_bb_middle; }
    double GetBollingerLower() { UpdateAdvancedIndicators(); return cached_bb_lower; }
    
    // MACD指标
    double GetMACDMain() { UpdateAdvancedIndicators(); return cached_macd_main; }
    double GetMACDSignalLine() { UpdateAdvancedIndicators(); return cached_macd_signal; }
    double GetMACDHistogram() { UpdateAdvancedIndicators(); return cached_macd_histogram; }
    
    // KDJ指标
    double GetKValue() { UpdateAdvancedIndicators(); return cached_k_value; }
    double GetDValue() { UpdateAdvancedIndicators(); return cached_d_value; }
    double GetJValue() { UpdateAdvancedIndicators(); return cached_j_value; }
    
    // 布林带位置判断 - 增强边界处理和精度
    double GetBollingerPosition()
    {
        UpdateAdvancedIndicators();
        
        // 检查布林带是否有效
        if(cached_bb_upper <= cached_bb_lower || cached_bb_upper == 0 || cached_bb_lower == 0)
        {
            return 50.0; // 布林带无效时返回中间位置
        }
        
        double position = (Close[0] - cached_bb_lower) / (cached_bb_upper - cached_bb_lower) * 100;
        // 限制位置在0-100范围内，并处理极端情况
        return MathMax(0.0, MathMin(100.0, position));
    }
    
    // MACD信号判断 - 增强信号逻辑
    int GetMACDSignal()
    {
        UpdateAdvancedIndicators();
        
        // 检查MACD值是否有效
        if(cached_macd_main == 0 && cached_macd_signal == 0)
        {
            return 0; // MACD无效时返回中性
        }
        
        // 增强的MACD信号判断逻辑
        if(cached_macd_main > cached_macd_signal && cached_macd_histogram > 0)
            return 1;  // 看涨信号：主线在信号线上方且柱状图为正
        else if(cached_macd_main < cached_macd_signal && cached_macd_histogram < 0)
            return -1; // 看跌信号：主线在信号线下方且柱状图为负
        else if(cached_macd_main > cached_macd_signal && cached_macd_histogram < 0)
            return 0;  // 中性：主线在信号线上方但柱状图为负（可能反转）
        else if(cached_macd_main < cached_macd_signal && cached_macd_histogram > 0)
            return 0;  // 中性：主线在信号线下方但柱状图为正（可能反转）
        else
            return 0;  // 中性
    }
    
    // KDJ信号判断 - 使用输入参数统一阈值
    int GetKDJSignal()
    {
        UpdateAdvancedIndicators();
        if(cached_k_value > KDJOverbought && cached_d_value > KDJOverbought)
            return -1; // 超买，看跌信号
        else if(cached_k_value < KDJOversold && cached_d_value < KDJOversold)
            return 1;  // 超卖，看涨信号
        else
            return 0;  // 中性
    }
};

//+------------------------------------------------------------------+
//| 高级市场状态分析类 - 新增功能，不影响现有市场监控
//+------------------------------------------------------------------+
class CAdvancedMarketAnalysis
{
private:
    // 波动率分析缓存
    double cached_historical_volatility;
    double cached_volatility_ratio;
    double cached_volatility_trend;
    
    // 成交量分析缓存
    double cached_vwap;
    double cached_money_flow;
    double cached_volume_trend;
    
    // 市场情绪缓存
    double cached_market_breadth;
    double cached_sentiment_score;
    
    // 市场状态检测缓存
    MARKET_REGIME current_market_regime;
    MARKET_REGIME previous_market_regime;
    datetime regime_change_time;
    double regime_confidence;
    
    datetime last_update_time;
    
public:
    CAdvancedMarketAnalysis()
    {
        last_update_time = 0;
        cached_historical_volatility = 0;
        cached_volatility_ratio = 0;
        cached_volatility_trend = 0;
        cached_vwap = 0;
        cached_money_flow = 0;
        cached_volume_trend = 0;
        cached_market_breadth = 0;
        cached_sentiment_score = 0;
        
        // 市场状态检测初始化
        current_market_regime = RANGING;
        previous_market_regime = RANGING;
        regime_change_time = 0;
        regime_confidence = 0.0;
    }
    
    void UpdateAdvancedMarketData()
    {
        datetime current_time = Time[0];
        
        // 每10个tick更新一次，与技术指标缓存保持一致
        static int market_analysis_tick_count = 0;
        market_analysis_tick_count++;
        
        if(current_time != last_update_time || market_analysis_tick_count >= 10)
        {
            // 历史波动率计算 (20周期)
            double returns[20] = {0};
            for(int i = 0; i < 19; i++)
            {
                returns[i] = (Close[i] - Close[i+1]) / Close[i+1];
            }
            
            double mean_return = 0;
            for(int i = 0; i < 19; i++)
            {
                mean_return += returns[i];
            }
            mean_return /= 19;
            
            double variance = 0;
            for(int i = 0; i < 19; i++)
            {
                variance += MathPow(returns[i] - mean_return, 2);
            }
            variance /= 18; // 样本方差
            
            cached_historical_volatility = (variance > 0) ? MathSqrt(variance) * MathSqrt(252) * 100 : 0; // 年化波动率，防止负方差
            
            // 波动率比率 - 使用缓存避免重复计算
            double current_atr = indicator_cache.GetATR();
            double avg_atr = GetAverageATR(20);
            cached_volatility_ratio = (avg_atr > 0) ? current_atr / avg_atr : 1.0; // 防止除零错误
            
            // 波动率趋势 - 优化计算逻辑，减少重复调用
            double atr_5 = 0, atr_15 = 0;
            for(int i = 0; i < 5; i++) atr_5 += iATR(Symbol(), Period(), 14, i);
            for(int i = 0; i < 15; i++) atr_15 += iATR(Symbol(), Period(), 14, i);
            atr_5 /= 5; atr_15 /= 15;
            cached_volatility_trend = (atr_15 > 0) ? atr_5 / atr_15 : 1.0; // 防止除零错误
            
            // VWAP计算 (20周期) - 增强边界处理
            double volume_sum = 0;
            double price_volume_sum = 0;
            for(int i = 0; i < 20; i++)
            {
                volume_sum += (double)Volume[i];
                price_volume_sum += Close[i] * (double)Volume[i];
            }
            cached_vwap = (volume_sum > 0) ? price_volume_sum / volume_sum : Close[0]; // 防止除零错误
            
            // 资金流向
            double typical_price = (High[0] + Low[0] + Close[0]) / 3;
            double prev_typical_price = (High[1] + Low[1] + Close[1]) / 3;
            double money_flow_multiplier = (typical_price > prev_typical_price) ? 1 : -1;
            cached_money_flow = typical_price * (double)Volume[0] * money_flow_multiplier;
            
            // 成交量趋势 - 增强边界处理
            double volume_5 = 0, volume_15 = 0;
            for(int i = 0; i < 5; i++) volume_5 += (double)Volume[i];
            for(int i = 0; i < 15; i++) volume_15 += (double)Volume[i];
            volume_5 /= 5; volume_15 /= 15;
            cached_volume_trend = (volume_15 > 0) ? volume_5 / volume_15 : 1.0; // 防止除零错误
            
            // 市场宽度 (简化版)
            int up_bars = 0, down_bars = 0;
            for(int i = 0; i < 20; i++)
            {
                if(Close[i] > Open[i]) up_bars++;
                else if(Close[i] < Open[i]) down_bars++;
            }
            cached_market_breadth = (double)(up_bars - down_bars) / 20.0 * 100;
            
            // 市场情绪评分 (综合指标) - 优化计算逻辑和极端情况处理
            double volatility_score = MathMax(0.0, MathMin(30.0, (1.0 - MathAbs(cached_volatility_ratio - 1.0)) * 30));
            double volume_score = MathMax(0.0, MathMin(30.0, MathMin(cached_volume_trend, 2.0) / 2.0 * 30));
            double breadth_score = MathMax(0.0, MathMin(40.0, (cached_market_breadth + 100) / 200.0 * 40));
            cached_sentiment_score = MathMax(0.0, MathMin(100.0, volatility_score + volume_score + breadth_score));
            
            last_update_time = current_time;
            market_analysis_tick_count = 0; // 重置tick计数
        }
    }
    
    // 高级波动率分析
    double GetHistoricalVolatility() { UpdateAdvancedMarketData(); return cached_historical_volatility; }
    double GetVolatilityRatio() { UpdateAdvancedMarketData(); return cached_volatility_ratio; }
    double GetVolatilityTrend() { UpdateAdvancedMarketData(); return cached_volatility_trend; }
    
    // 高级成交量分析
    double GetVWAP() { UpdateAdvancedMarketData(); return cached_vwap; }
    double GetMoneyFlow() { UpdateAdvancedMarketData(); return cached_money_flow; }
    double GetVolumeTrend() { UpdateAdvancedMarketData(); return cached_volume_trend; }
    
    // 市场情绪分析
    double GetMarketBreadth() { UpdateAdvancedMarketData(); return cached_market_breadth; }
    double GetSentimentScore() { UpdateAdvancedMarketData(); return cached_sentiment_score; }
    
    // 高级市场评分 - 增强边界处理和精度
    double GetAdvancedMarketScore()
    {
        UpdateAdvancedMarketData();
        
        double score = 0.0;
        
        // 波动率评分 (30%) - 增强边界处理
        double volatility_score = MathMax(0.0, MathMin(30.0, (1.0 - MathAbs(cached_volatility_ratio - 1.0)) * 30));
        score += volatility_score;
        
        // 成交量评分 (30%) - 增强边界处理
        double volume_score = MathMax(0.0, MathMin(30.0, MathMin(cached_volume_trend, 2.0) / 2.0 * 30));
        score += volume_score;
        
        // 市场情绪评分 (40%) - 增强边界处理
        double sentiment_score = MathMax(0.0, MathMin(40.0, cached_sentiment_score * 0.4));
        score += sentiment_score;
        
        return MathMax(0.0, MathMin(100.0, score));
    }
    
    // 市场状态检测函数
    bool IsTrendingUp()
    {
        // 1. MA斜率判断
        double ma_12 = indicator_cache.GetMA(12);
        double ma_26 = indicator_cache.GetMA(26);
        double ma_12_prev = iMA(Symbol(), Period(), 12, 0, MODE_EMA, PRICE_CLOSE, 5);
        double ma_26_prev = iMA(Symbol(), Period(), 26, 0, MODE_EMA, PRICE_CLOSE, 10);
        
        double ma_12_slope = (ma_12 - ma_12_prev) / 5;
        double ma_26_slope = (ma_26 - ma_26_prev) / 10;
        
        // 2. ADX趋势强度
        double adx = indicator_cache.GetADX();
        
        // 3. MACD趋势确认
        double macd_main = advanced_indicators.GetMACDMain();
        double macd_signal = advanced_indicators.GetMACDSignalLine();
        
        // 4. 价格位置
        double bb_position = GetBollingerPosition();
        
        return (ma_12_slope > 0 && ma_26_slope > 0 && 
                adx > 25 && macd_main > macd_signal && 
                bb_position > 30);
    }
    
    bool IsTrendingDown()
    {
        // 反向逻辑
        double ma_12 = indicator_cache.GetMA(12);
        double ma_26 = indicator_cache.GetMA(26);
        double ma_12_prev = iMA(Symbol(), Period(), 12, 0, MODE_EMA, PRICE_CLOSE, 5);
        double ma_26_prev = iMA(Symbol(), Period(), 26, 0, MODE_EMA, PRICE_CLOSE, 10);
        
        double ma_12_slope = (ma_12 - ma_12_prev) / 5;
        double ma_26_slope = (ma_26 - ma_26_prev) / 10;
        
        double adx = indicator_cache.GetADX();
        double macd_main = advanced_indicators.GetMACDMain();
        double macd_signal = advanced_indicators.GetMACDSignalLine();
        double bb_position = GetBollingerPosition();
        
        return (ma_12_slope < 0 && ma_26_slope < 0 && 
                adx > 25 && macd_main < macd_signal && 
                bb_position < 70);
    }
    
    bool IsRanging()
    {
        // 1. ADX低值（趋势弱）
        double adx = indicator_cache.GetADX();
        
        // 2. 布林带收缩
        double bb_upper = advanced_indicators.GetBollingerUpper();
        double bb_lower = advanced_indicators.GetBollingerLower();
        double bb_middle = (bb_upper + bb_lower) / 2;
        double bb_width = (bb_upper - bb_lower) / bb_middle;
        
        // 3. ATR低波动
        double atr_ratio = cached_volatility_ratio;
        
        // 4. RSI中性区域 - 使用统一的RSI阈值范围
        double rsi = indicator_cache.GetRSI();
        
        return (adx < 20 && bb_width < 0.05 && 
                atr_ratio < 0.8 && rsi > RSIOversold && rsi < RSIOverbought);
    }
    
    bool IsBreakoutUp()
    {
        // 1. 价格突破布林带上轨
        double bb_position = GetBollingerPosition();
        
        // 2. 成交量放大
        double volume_ratio = cached_volume_trend;
        
        // 3. RSI超买但继续上涨 - 使用统一的RSI阈值
        double rsi = indicator_cache.GetRSI();
        
        // 4. MACD柱状图放大
        double macd_histogram = advanced_indicators.GetMACDHistogram();
        double prev_macd_histogram = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1) - 
                                   iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
        
        return (bb_position > 95 && volume_ratio > 1.5 && 
                rsi > RSIOverbought && macd_histogram > prev_macd_histogram);
    }
    
    bool IsBreakoutDown()
    {
        // 反向逻辑 - 使用统一的RSI阈值
        double bb_position = GetBollingerPosition();
        double volume_ratio = cached_volume_trend;
        double rsi = indicator_cache.GetRSI();
        double macd_histogram = advanced_indicators.GetMACDHistogram();
        double prev_macd_histogram = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1) - 
                                   iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
        
        return (bb_position < 5 && volume_ratio > 1.5 && 
                rsi < RSIOversold && macd_histogram < prev_macd_histogram);
    }
    
    bool IsReversalUp()
    {
        // 1. 价格从低位反弹
        double bb_position = GetBollingerPosition();
        
        // 2. RSI从超卖反弹 - 使用统一的RSI阈值
        double rsi = indicator_cache.GetRSI();
        double rsi_prev = iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 1);
        
        // 3. MACD金叉
        double macd_main = advanced_indicators.GetMACDMain();
        double macd_signal = advanced_indicators.GetMACDSignalLine();
        double macd_main_prev = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1);
        double macd_signal_prev = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
        
        // 4. 成交量确认
        double volume_ratio = cached_volume_trend;
        
        return (bb_position < 20 && rsi < RSIOversold && rsi > rsi_prev && 
                macd_main_prev < macd_signal_prev && macd_main > macd_signal && 
                volume_ratio > 1.2);
    }
    
    bool IsReversalDown()
    {
        // 反向逻辑 - 使用统一的RSI阈值
        double bb_position = GetBollingerPosition();
        double rsi = indicator_cache.GetRSI();
        double rsi_prev = iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 1);
        double macd_main = advanced_indicators.GetMACDMain();
        double macd_signal = advanced_indicators.GetMACDSignalLine();
        double macd_main_prev = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1);
        double macd_signal_prev = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
        double volume_ratio = cached_volume_trend;
        
        return (bb_position > 80 && rsi > RSIOverbought && rsi < rsi_prev && 
                macd_main_prev > macd_signal_prev && macd_main < macd_signal && 
                volume_ratio > 1.2);
    }
    
    // 获取市场状态 - 增加容错机制
    MARKET_REGIME GetMarketRegime()
    {
        UpdateAdvancedMarketData();
        
        // 检查数据有效性
        if(cached_volatility_ratio <= 0 || cached_volume_trend <= 0) {
            return RANGING; // 数据无效时返回震荡状态
        }
        
        // 优先级：反转 > 突破 > 趋势 > 震荡
        if(IsReversalUp()) return REVERSAL_UP;
        if(IsReversalDown()) return REVERSAL_DOWN;
        if(IsBreakoutUp()) return BREAKOUT_UP;
        if(IsBreakoutDown()) return BREAKOUT_DOWN;
        if(IsTrendingUp()) return TRENDING_UP;
        if(IsTrendingDown()) return TRENDING_DOWN;
        if(IsRanging()) return RANGING;
        
        return RANGING; // 默认震荡
    }
    
    // 检查市场状态变化
    bool CheckRegimeChange()
    {
        previous_market_regime = current_market_regime;
        current_market_regime = GetMarketRegime();
        
        if(current_market_regime != previous_market_regime) {
            regime_change_time = Time[0];
            Print("🔄 市场状态变化: ", GetRegimeName(previous_market_regime), " → ", GetRegimeName(current_market_regime));
            return true;
        }
        
        return false;
    }
    
    // 获取状态名称
    string GetRegimeName(MARKET_REGIME regime)
    {
        switch(regime) {
            case TRENDING_UP: return "上升趋势";
            case TRENDING_DOWN: return "下降趋势";
            case RANGING: return "震荡";
            case BREAKOUT_UP: return "向上突破";
            case BREAKOUT_DOWN: return "向下突破";
            case REVERSAL_UP: return "向上反转";
            case REVERSAL_DOWN: return "向下反转";
            default: return "未知";
        }
    }
    
    // 获取当前市场状态
    MARKET_REGIME GetCurrentRegime() { return current_market_regime; }
    
    // 获取状态变化时间
    datetime GetRegimeChangeTime() { return regime_change_time; }
    
    // 获取状态变化后的时间间隔
    int GetTimeSinceRegimeChange()
    {
        if(regime_change_time == 0) return 0;
        return (int)(Time[0] - regime_change_time);
    }
    
    // 动态权重调整结构
    struct WeightAllocation {
        double technical_weight;
        double market_weight;
        double synergy_bonus;
    };
    
    // 获取动态权重分配
    WeightAllocation GetWeightAllocation(MARKET_REGIME regime)
    {
        WeightAllocation weights;
        
        switch(regime) {
            case TRENDING_UP:
            case TRENDING_DOWN:
                // 趋势市场：技术指标权重高，市场状况权重低
                weights.technical_weight = 0.75; // 75%
                weights.market_weight = 0.25;    // 25%
                weights.synergy_bonus = 0.1;     // 10%协同奖励
                break;
                
            case RANGING:
                // 震荡市场：接近基础权重的平衡分配
                weights.technical_weight = 0.6;  // 60% (接近基础的70%)
                weights.market_weight = 0.4;     // 40% (接近基础的30%)
                weights.synergy_bonus = 0.2;     // 20%协同奖励
                break;
                
            case BREAKOUT_UP:
            case BREAKOUT_DOWN:
                // 突破市场：市场状况权重高
                weights.technical_weight = 0.4;  // 40%
                weights.market_weight = 0.6;     // 60%
                weights.synergy_bonus = 0.15;    // 15%协同奖励
                break;
                
            case REVERSAL_UP:
            case REVERSAL_DOWN:
                // 反转市场：技术指标权重最高
                weights.technical_weight = 0.8;  // 80%
                weights.market_weight = 0.2;     // 20%
                weights.synergy_bonus = 0.05;    // 5%协同奖励
                break;
                
            default:
                // 默认：接近基础权重
                weights.technical_weight = 0.7;  // 70% (基础权重)
                weights.market_weight = 0.3;     // 30% (基础权重)
                weights.synergy_bonus = 0.1;
                break;
        }
        
        return weights;
    }
    
    // 获取动态技术权重 - 修复权重分配逻辑
    double GetDynamicTechnicalWeight(MARKET_REGIME regime)
    {
        WeightAllocation weights = GetWeightAllocation(regime);
        // 动态权重应该重新分配总权重，而不是缩放原有权重
        return weights.technical_weight;
    }
    
    // 获取动态市场权重 - 修复权重分配逻辑
    double GetDynamicMarketWeight(MARKET_REGIME regime)
    {
        WeightAllocation weights = GetWeightAllocation(regime);
        // 动态权重应该重新分配总权重，而不是缩放原有权重
        return weights.market_weight;
    }
    
    // 平滑权重过渡
    double GetSmoothWeight(double target_weight, double current_weight, double smoothing_factor = 0.1)
    {
        return current_weight + (target_weight - current_weight) * smoothing_factor;
    }
    
    // 协同评分计算
    double GetSynergyScore(double technical_score, double market_score, MARKET_REGIME regime)
    {
        WeightAllocation weights = GetWeightAllocation(regime);
        
        // 基础加权评分
        double base_score = technical_score * weights.technical_weight + 
                           market_score * weights.market_weight;
        
        // 协同奖励
        double synergy_bonus = CalculateSynergyBonus(technical_score, market_score, regime);
        
        return base_score + synergy_bonus;
    }
    
    // 协同奖励计算
    double CalculateSynergyBonus(double technical_score, double market_score, MARKET_REGIME regime)
    {
        WeightAllocation weights = GetWeightAllocation(regime);
        
        // 1. 方向一致性奖励
        double direction_consistency = 0;
        if((technical_score > 0 && market_score > 0) || 
           (technical_score < 0 && market_score < 0)) {
            direction_consistency = MathMin(MathAbs(technical_score), MathAbs(market_score)) * 0.2;
        }
        
        // 2. 强度匹配奖励
        double intensity_match = 0;
        double tech_intensity = MathAbs(technical_score);
        double market_intensity = MathAbs(market_score);
        if(MathAbs(tech_intensity - market_intensity) < 0.1) {
            intensity_match = MathMin(tech_intensity, market_intensity) * 0.15;
        }
        
        // 3. 市场状态特定奖励
        double regime_bonus = 0;
        switch(regime) {
            case TRENDING_UP:
            case TRENDING_DOWN:
                // 趋势市场：技术指标主导
                if(tech_intensity > market_intensity * 1.5) {
                    regime_bonus = tech_intensity * 0.1;
                }
                break;
                
            case RANGING:
                // 震荡市场：平衡奖励
                if(MathAbs(tech_intensity - market_intensity) < 0.2) {
                    regime_bonus = (tech_intensity + market_intensity) * 0.1;
                }
                break;
                
            case BREAKOUT_UP:
            case BREAKOUT_DOWN:
                // 突破市场：市场状况主导
                if(market_intensity > tech_intensity * 1.5) {
                    regime_bonus = market_intensity * 0.1;
                }
                break;
                
            case REVERSAL_UP:
            case REVERSAL_DOWN:
                // 反转市场：技术指标主导
                if(tech_intensity > market_intensity * 2.0) {
                    regime_bonus = tech_intensity * 0.15;
                }
                break;
        }
        
        return (direction_consistency + intensity_match + regime_bonus) * weights.synergy_bonus;
    }
    
    // 时间衰减奖励
    double GetTimeDecayBonus(MARKET_REGIME regime, int time_since_change)
    {
        // 状态变化后的时间衰减
        double decay_factor = MathExp(-time_since_change / 10.0); // 10个tick衰减
        
        switch(regime) {
            case TRENDING_UP:
            case TRENDING_DOWN:
                return 0.1 * decay_factor; // 趋势状态衰减较慢
            case RANGING:
                return 0.05 * decay_factor; // 震荡状态衰减中等
            case BREAKOUT_UP:
            case BREAKOUT_DOWN:
                return 0.2 * decay_factor; // 突破状态衰减较快
            case REVERSAL_UP:
            case REVERSAL_DOWN:
                return 0.15 * decay_factor; // 反转状态衰减中等
        }
        
        return 0;
    }
    
    // 置信度加权评分
    double GetConfidenceWeightedScore(double technical_score, double market_score, 
                                     double tech_confidence, double market_confidence)
    {
        // 根据置信度调整权重
        double total_confidence = tech_confidence + market_confidence;
        
        if(total_confidence > 0) {
            double tech_weight = tech_confidence / total_confidence;
            double market_weight = market_confidence / total_confidence;
            
            return technical_score * tech_weight + market_score * market_weight;
        }
        
        return (technical_score + market_score) / 2.0;
    }
    
    // 市场状态分类 - 增强判断逻辑和边界处理（保持兼容性）
    int GetMarketState()
    {
        UpdateAdvancedMarketData();
        
        // 检查数据有效性
        if(cached_sentiment_score < 0 || cached_volatility_ratio < 0)
        {
            return 0; // 数据无效时返回震荡市场
        }
        
        // 根据综合指标判断市场状态 - 增强逻辑
        if(cached_sentiment_score > 70 && cached_volatility_ratio < 1.5)
            return 1;  // 强势市场：高情绪 + 低波动
        else if(cached_sentiment_score < 30 || cached_volatility_ratio > 2.0)
            return -1; // 弱势市场：低情绪 或 高波动
        else
            return 0;  // 震荡市场：中等情绪和波动
    }
};

//+------------------------------------------------------------------+
//| 全局工具函数
//+------------------------------------------------------------------+
// 获取平均ATR值 - 全局函数
double GetAverageATR(int period)
{
    double sum = 0.0;
    for(int i = 0; i < period; i++)
    {
        sum += iATR(Symbol(), Period(), 14, i);
    }
    return sum / period;
}

//+------------------------------------------------------------------+
//| 全局对象
//+------------------------------------------------------------------+
CMoneyManager money_manager;
CRiskManager risk_manager;
CMarketMonitor market_monitor;
CAIPredictor ai_predictor;
CTradeExecutor trade_executor;
CCloseManager close_manager;
CIndicatorCache indicator_cache;  // 新增：指标缓存管理器
CAdvancedIndicators advanced_indicators;  // 新增：高级技术指标管理器
CAdvancedMarketAnalysis advanced_market_analysis;  // 新增：高级市场分析管理器

//+------------------------------------------------------------------+
//| Expert initialization function
//+------------------------------------------------------------------+
int OnInit()
{
    // 全局变量初始化检查
    if(!g_variables_initialized)
    {
        g_last_prediction_time = 0;
        g_last_prediction = -1;
        g_last_confidence = 0.0;
        g_ai_service_available = false;
        g_variables_initialized = true;
        Print("✅ 全局变量初始化完成");
    }
    
    Print("=== AI增强风险管理EA启动 ===");
    Print("版本: 2.8.2 - 协同优化版 🎯");
    Print("🔧 关键升级:");
            Print("  🔒 锁仓: 1500点统一触发");
            Print("  📊 锁仓手数: 1.0倍基础手数");
            Print("  💰 锁仓解锁: 300点盈利解锁");
    Print("  📈 持仓上限: ", MaxNormalOrders, "单普通 + ", MaxLockOrders, "单锁仓");
    Print("  ⏰ 建仓频率: 15分钟间隔控制");
    Print("🆕 协同优化升级:");
    Print("  🎯 权重计算: 修复双重应用错误");
    Print("  📊 参数统一: RSI/ATR标准化");
    Print("  🤝 协同评分: 技术指标与市场状况协调");
    Print("🔧 核心功能:");
    Print("  ✅ 扛单策略: 10000点极限，无时间限制");
            Print("  ✅ 锁仓: 1500点触发，300点解锁");
    Print("  ✅ 盈利目标: 400点获利，移动止损1.0倍ATR保护");
    Print("  ✅ 账户保护: 30%强制平仓保护");
    Print("  ✅ 决策权重: 技术70% + 市场30% (AI禁用) - 黄金期货优化");
    if(EnableMarketRegimeDetection) {
        Print("  ✅ 市场状态检测: 已启用");
    }
    if(EnableDynamicWeightAdjustment) {
        Print("  ✅ 动态权重调整: 已启用");
    }
    if(EnableSynergyScoring) {
        Print("  ✅ 协同评分机制: 已启用");
    }
    Print("  ✅ 高频交易支持: 移除时间和次数限制");
    Print("  🛡️ 位置风险控制: 防止追涨追跌");
    Print("  🧠 位置感知增强: 动态权重调整 + 反转信号增强");
    Print("========================");
    
    // 初始化风控参数
    money_manager.Init();
    risk_manager.Init(MaxOpenOrders, MaxSpreadPips);
    market_monitor.Init(2.5, 12.0); // 波动率阈值2.5，趋势强度阈值12 (从15降低到12，让ADX=13.6871能通过)
    ai_predictor.Init(DataFileName, PredictionFileName, 5); // 5秒缓存（配合实时预测服务）
    
    // 清除AI缓存，确保立即读取最新预测
    ai_predictor.ClearCache();
    
    // 初始化新的管理器
    CTradeCounter::Init();
    CTrailingStopManager::Init();
    
    // 初始化锁仓记录系统
    InitLockRecordSystem();
    
    // 初始化交易执行器
    trade_executor.Init(money_manager, risk_manager, market_monitor, ai_predictor);
    close_manager.Init(ai_predictor, market_monitor);
    
    // 初始化指标缓存管理器（使用构造函数自动初始化）
    // indicator_cache 已在声明时自动初始化
    
    // 测试AI文件服务
    if(EnableAI)
    {
        TestAIFileService();
    }
    
    Print("AI增强风控EA初始化完成");
    Print("🚀 全面优化套件已启用:");
    Print("  📊 交易逻辑: 每10个tick执行 (减少AI调用)");
    Print("  ⚡ 平仓检查: 每5个tick执行 (保证及时响应)");
    Print("  🔄 锁仓管理: 每20个tick执行 (降低计算负担)");
    Print("  📈 指标缓存: 按K线更新 (避免重复计算)");
    Print("  💰 利润计算: 统一函数 (100%代码复用)");
    Print("  🛡️ 移动止损: 内存安全版本 (固定数组)");
    Print("  📝 日志系统: 统一管理 (集中化处理)");
    Print("  🔢 交易计数: 统一管理 (数据一致性)");
    Print("=== 风控参数 ===");
            Print("最大开仓数: ", MaxOpenOrders);
    Print("最大点差: ", MaxSpreadPips, " 点");
    Print("最大滑点: ", MaxSlippage, " 点");
    Print("锁仓单建仓间隔: ", MinOrderInterval/60, " 分钟");
    Print("普通仓上限: ", MaxNormalOrders, " 单 (无时间限制)");
    Print("锁仓单上限: ", MaxLockOrders, " 单");
    Print("=== 高级功能 ===");

    Print("=== 平仓管理 ===");
    Print("智能平仓: ", (EnableSmartClose ? "启用" : "禁用"));
    Print("技术指标平仓: ", (EnableTechnicalClose ? "启用" : "禁用"));
    
    Print("虚拟移动止损: ", (EnableTrailingStop ? "启用 (内存安全版)" : "禁用"));

    Print("移动止损倍数: ", TrailingStopMultiplier, " (基于ATR)");
    Print("=== 开仓频率控制 ===");

    Print("信号确认tick数: ", SignalConfirmTicks);

    Print("信号确认: ", (EnableSignalConfirmation ? "启用" : "禁用"));
    Print("智能方向检查: ", (EnableSmartDirectionCheck ? "启用" : "禁用"));
    Print("同方向最大持仓: ", MaxSameDirectionOrders, " (普通仓位2个 + 应急仓位2个 + 智能加仓2个)");
    Print("=== 手数设置 ===");
    Print("固定手数: ", (UseFixedLotSize ? "启用" : "禁用"));
    Print("手数大小: ", FixedLotSize);

    Print("=== 高级策略 ===");
    Print("=== 扛单与锁仓 ===");
    Print("扛单策略: ", (EnableHoldStrategy ? "启用" : "禁用"));
    Print("最大扛单亏损: ", MaxHoldLossPips, " 点");
            Print("账户保护: 已禁用 (完全扛单模式)");
            Print("锁仓管理: ", (EnableLockManagement ? "启用" : "禁用"));
            Print("锁仓触发: ", LockTriggerLevel, " 点 (手数倍数: ", LockLotMultiplier, ")");
    Print("锁仓解锁: ", UnlockProfit, "点");
        Print("锁仓单亏损平仓: ", LockOrderLossLimit, "点");
        Print("建仓频率控制: 锁仓单15分钟间隔");
        Print("普通仓限制: 最多2个持仓 (无时间限制)");
        Print("锁仓单限制: 最多2个持仓");
        Print("智能解锁: 已移除 (锁仓单按分层盈利点平仓)");
    
    Print("=== 位置风险控制 ===");
    Print("位置风险控制: ", (EnablePositionRiskControl ? "启用" : "禁用"));
    Print("高位风险阈值: ", HighRiskPosition, "%");
    Print("低位风险阈值: ", LowRiskPosition, "%");
    Print("强趋势ADX阈值: ", StrongTrendADX);
    Print("高置信度阈值: ", HighConfidenceThreshold);
    
    Print("=== 位置感知增强 ===");
    Print("位置感知增强: ", (EnablePositionAwareness ? "启用" : "禁用"));
    Print("极端位置阈值: ", ExtremePositionThreshold, "%");
    Print("AI权重降低因子: ", AIWeightReductionFactor, " (AI已禁用)");
    Print("反转信号增强因子: ", ReversalSignalBonus);
    Print("极端位置置信度阈值: ", ExtremeConfidenceThreshold);
    
    Print("=== 锁仓单风险控制 ===");
    Print("锁仓单亏损平仓: ", LockOrderLossLimit, "点");
    
    Print("=== 决策评分反转处理 ===");
    Print("决策评分反转: ", (EnableDecisionScoreReversal ? "启用" : "禁用"));
    Print("🚫 新模式：锁仓单不给予反转信号平仓，完全扛单模式");
    Print("📊 普通仓位：反转信号后保持持有，不平仓");
    Print("🔒 锁仓单：反转信号后继续扛单，不平仓");
            Print("基础反转阈值: ", DecisionReversalThreshold, " (基于前5个决策评分对比)");
        Print("决策反转确认tick数: ", DecisionReversalTicks);
        Print("反转信号系统: 基于前5个决策评分方向对比，不依赖持仓");
    Print("小亏损阈值: ", SmallLossThreshold, "点 (已禁用)");
    Print("大亏损阈值: ", LargeLossThreshold, "点 (已禁用)");
    Print("分批平仓间隔: ", BatchCloseInterval, "tick (已禁用)");
    
    Print("=== 应急仓位参数 ===");
    Print("应急仓位数量: ", EmergencyOrderCount, " 个");
    Print("应急仓位手数: ", EmergencyLotSize);
    Print("应急盈利目标: ", EmergencyProfitTarget, " 点位");
    Print("应急止损: ", EmergencyStopLoss, " 点位");
            Print("应急触发阈值: ", EmergencyTriggerScore, " (已废弃，现在使用DecisionReversalThreshold: ", DecisionReversalThreshold, ")");
    Print("🚨 应急仓位只给予反转信号");
    
    Print("=== 智能加仓参数 ===");
    Print("启用智能加仓: ", (EnableSmartBuyStrategy ? "是" : "否"));
    Print("决策评分阈值: ", SmartBuyDecisionThreshold);
    Print("最大智能加仓订单: ", MaxSmartBuyOrders, " 个");
    Print("最大智能加仓手数: ", MaxSmartBuyTotalLots, " 手");
    Print("智能加仓最小间隔: ", SmartBuyMinInterval, " 秒");
    Print("亏损触发: ", (SmartBuyUseLossTrigger ? "启用" : "禁用"), " (阈值: ", SmartBuyLossThreshold, " - ", SmartBuyMaxLossThreshold, " 点数)");
    Print("盈利目标: ", SmartBuyProfitTarget, " 点数");
    Print("止损设置: ", SmartBuyStopLoss, " 点数");
    Print("🎯 智能加仓：同向亏损单方向建仓，最大0.03手");
    
    // 初始化智能加仓变量
    g_last_smart_buy_time = 0;
    g_smart_buy_orders = 0;
    g_smart_buy_total_lots = 0.0;
    g_smart_buy_triggered = false;
    g_smart_buy_record_count = 0;
    
    // 初始化智能加仓记录数组
    for(int i = 0; i < 2; i++)
    {
        g_smart_buy_records[i].ticket = 0;
        g_smart_buy_records[i].open_time = 0;
        g_smart_buy_records[i].open_price = 0.0;
        g_smart_buy_records[i].lot_size = 0.0;
        g_smart_buy_records[i].order_type = 0;
        g_smart_buy_records[i].ai_confidence = 0.0;
        g_smart_buy_records[i].decision_score = 0.0;
        g_smart_buy_records[i].avg_loss_pips = 0.0;
        g_smart_buy_records[i].is_active = false;
    }
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 EA卸载 - 原因代码: ", reason);
    
    // 清理资源
    CLogManager::LogSystem("EA卸载 - 原因代码: " + IntegerToString(reason), 2); // 2 = LOG_INFO
    
    Print("✅ EA卸载完成");
}

//+------------------------------------------------------------------+
//| Expert tick function
//+------------------------------------------------------------------+
void OnTick()
{
    // 更新智能加仓统计
    ::UpdateSmartBuyStats();
    
    // 优化：使用不同频率控制不同功能
    static int tick_count = 0;
    tick_count++;
    
    // 平仓检查 - 每5个tick检查一次 (更频繁，保证及时平仓)
    if(tick_count % 5 == 0)
    {
        // 移除不必要的日志输出，提高性能
        close_manager.CheckAndCloseOrders();
    }
    
    // 交易逻辑 - 每10个tick执行一次 (减少AI调用频率)
    if(tick_count % 10 == 0)
    {
        trade_executor.ExecuteTradingLogic();
    }
    
    // 锁仓管理 - 每20个tick检查一次 (降低频率)
    if(EnableLockManagement && tick_count % 20 == 0)
    {
        risk_manager.ManageLockedPositions();
    }
    
    // 交易状态检查 - 每100个tick检查一次 (保持原频率)
    if(tick_count % 100 == 0)
    {
        trade_executor.CheckTradingStatus();
    }
    
    // 防止tick_count溢出
    if(tick_count >= 1000) tick_count = 0;
}



//+------------------------------------------------------------------+
//| 锁仓记录系统初始化
//+------------------------------------------------------------------+
void InitLockRecordSystem()
{
    g_lock_record_count = 0;
    // 清空所有锁仓记录
    for(int i = 0; i < 50; i++)
    {
        g_lock_records[i].original_ticket = 0;
        g_lock_records[i].lock_level = 0;
        g_lock_records[i].lock_time = 0;
        g_lock_records[i].lock_lot = 0.0;
        g_lock_records[i].lock_ticket = 0;
        g_lock_records[i].is_active = false;
    }
    Print("🔒 锁仓记录系统初始化完成");
}

//+------------------------------------------------------------------+
//| 测试AI文件服务
//+------------------------------------------------------------------+
void TestAIFileService()
{
    // 创建测试数据文件
    int handle = FileOpen("market_data.csv", FILE_WRITE|FILE_CSV);
    if(handle != INVALID_HANDLE)
    {
        // 获取服务器时间
        datetime server_time = TimeCurrent();
        string server_time_str = TimeToString(server_time);
        
        // 使用MT4客户端时间作为本地时间（更准确）
        datetime client_time = TimeLocal();
        string client_time_str = TimeToString(client_time);
        
        // 写入时间信息作为前两行
        FileWrite(handle, "ServerTime", server_time_str);
        FileWrite(handle, "ClientTime", client_time_str);
        
        // 写入最近50个数据点（与WriteMarketDataToFile保持一致）
        for(int idx1 = 49; idx1 >= 0; idx1--)
        {
            string time_str = TimeToString(Time[idx1]);
            FileWrite(handle, time_str, Open[idx1], High[idx1], Low[idx1], Close[idx1], Volume[idx1]);
        }
        FileClose(handle);
        
        g_ai_service_available = true;
        Print("✅ AI文件服务测试成功");
        Print("📊 市场数据已写入，服务器时间: ", server_time_str, " 客户端时间: ", client_time_str);
        Print("📁 数据文件: ", DataFileName);
        Print("📁 预测文件: ", PredictionFileName);
        Print("💡 请启动Python AI服务: py continuous_ai_monitor.py");
    }
    else
    {
        g_ai_service_available = false;
        Print("❌ AI文件服务测试失败，无法创建数据文件");
        Print("错误代码: ", GetLastError());
    }
}

//+------------------------------------------------------------------+
//| 详细日志记录函数
//+------------------------------------------------------------------+

// 锁仓活动日志记录
void LogLockActivity(string action, double total_pips, int buy_count, int sell_count)
{
    string log_entry = StringFormat("%s | 锁仓活动: %s | 总点数: %.1f | 买入: %d | 卖出: %d | 账户: %.2f", 
                                   TimeToString(TimeCurrent()), action, total_pips, buy_count, sell_count, AccountBalance());
    
    // 写入日志文件 - 使用追加模式避免文件冲突
    int handle = FileOpen("lock_activity_log.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_READ);
    if(handle != INVALID_HANDLE)
    {
        // 移动到文件末尾
        FileSeek(handle, 0, SEEK_END);
        FileWrite(handle, TimeToString(TimeCurrent()), action, total_pips, buy_count, sell_count, AccountBalance());
        FileClose(handle);
    }
    else
    {
        // 如果文件不存在，创建新文件
        handle = FileOpen("lock_activity_log.csv", FILE_WRITE|FILE_CSV|FILE_ANSI);
        if(handle != INVALID_HANDLE)
        {
            FileWrite(handle, "时间", "活动", "总点数", "买入数量", "卖出数量", "账户余额");
            FileWrite(handle, TimeToString(TimeCurrent()), action, total_pips, buy_count, sell_count, AccountBalance());
            FileClose(handle);
        }
    }
    
    Print("📝 ", log_entry);
}



// 智能持仓活动日志记录
void LogHoldActivity(string action, int ticket, double loss_pips, string hold_reason, bool trend_favorable)
{
    string log_entry = StringFormat("%s | 智能持仓: %s | 订单: %d | 亏损: %.1f点 | 原因: %s | 趋势: %s", 
                                   TimeToString(TimeCurrent()), action, ticket, loss_pips, hold_reason, 
                                   trend_favorable ? "有利" : "不利");
    
    // 写入日志文件 - 使用追加模式避免文件冲突
    int handle = FileOpen("hold_activity_log.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_READ);
    if(handle != INVALID_HANDLE)
    {
        // 移动到文件末尾
        FileSeek(handle, 0, SEEK_END);
        FileWrite(handle, TimeToString(TimeCurrent()), action, ticket, loss_pips, hold_reason, trend_favorable ? "有利" : "不利");
        FileClose(handle);
    }
    else
    {
        // 如果文件不存在，创建新文件
        handle = FileOpen("hold_activity_log.csv", FILE_WRITE|FILE_CSV|FILE_ANSI);
        if(handle != INVALID_HANDLE)
        {
            FileWrite(handle, "时间", "活动", "订单号", "亏损点数", "持仓原因", "趋势状态");
            FileWrite(handle, TimeToString(TimeCurrent()), action, ticket, loss_pips, hold_reason, trend_favorable ? "有利" : "不利");
            FileClose(handle);
        }
    }
    
    Print("🤲 ", log_entry);
}



// 综合状态日志
void LogSystemStatus()
{
    int total_orders = 0;
    int buy_orders = 0;
    int sell_orders = 0;
    double total_profit = 0.0;
    bool has_lock = false;
    
    // 统计当前持仓
    for(int ad = 0; ad < OrdersTotal(); ad++)
    {
        if(OrderSelect(ad, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                total_orders++;
                total_profit += OrderProfit() + OrderSwap() + OrderCommission();
                
                if(OrderType() == OP_BUY)
                    buy_orders++;
                else if(OrderType() == OP_SELL)
                    sell_orders++;
            }
        }
    }
    
    has_lock = (buy_orders > 0 && sell_orders > 0);
    
    string status_log = StringFormat("📈 系统状态 | 总持仓: %d | 买入: %d | 卖出: %d | 总盈亏: %.2f | 锁仓: %s | 账户: %.2f", 
                                    total_orders, buy_orders, sell_orders, total_profit, 
                                    has_lock ? "是" : "否", AccountBalance());
    
    Print(status_log);
    
    // 每小时记录一次系统状态
    static datetime last_status_time = 0;
    if(TimeCurrent() - last_status_time > 3600) // 1小时
    {
        int handle = FileOpen("system_status_log.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_READ);
        if(handle != INVALID_HANDLE)
        {
            // 移动到文件末尾
            FileSeek(handle, 0, SEEK_END);
            FileWrite(handle, TimeToString(TimeCurrent()), total_orders, buy_orders, sell_orders, 
                     total_profit, has_lock ? "是" : "否", AccountBalance());
            FileClose(handle);
        }
        else
        {
            // 如果文件不存在，创建新文件
            handle = FileOpen("system_status_log.csv", FILE_WRITE|FILE_CSV|FILE_ANSI);
            if(handle != INVALID_HANDLE)
            {
                FileWrite(handle, "时间", "总持仓", "买入数量", "卖出数量", "总盈亏", "锁仓状态", "账户余额");
                FileWrite(handle, TimeToString(TimeCurrent()), total_orders, buy_orders, sell_orders, 
                         total_profit, has_lock ? "是" : "否", AccountBalance());
                FileClose(handle);
            }
        }
        last_status_time = TimeCurrent();
    }
}

// 全局变量已移至代码开头，此处删除重复定义

//+------------------------------------------------------------------+
//| 分批解锁全局函数
//+------------------------------------------------------------------+
void PartialUnlockByProfit(int &tickets[], double &profits[], datetime &opentimes[], int &types[], int unlock_count)
{
    // 安全检查：确保数组大小一致且不为空
    int array_size = ArraySize(tickets);
    if(array_size == 0 || array_size != ArraySize(profits) || array_size != ArraySize(opentimes) || array_size != ArraySize(types))
    {
        Print("❌ 分批解锁失败：数组大小不一致或为空");
        return;
    }
    
    // 限制解锁数量不超过数组大小
    if(unlock_count > array_size)
    {
        unlock_count = array_size;
        Print("⚠️ 解锁数量调整为数组大小: ", unlock_count);
    }
    
    // 按盈利排序（从高到低）
    for(int sort_i = 0; sort_i < array_size - 1; sort_i++)
    {
        for(int sort_j = sort_i + 1; sort_j < array_size; sort_j++)
        {
            if(profits[sort_i] < profits[sort_j])
            {
                // 交换位置
                int temp_ticket = tickets[sort_i];
                double temp_profit = profits[sort_i];
                datetime temp_opentime = opentimes[sort_i];
                int temp_type = types[sort_i];
                
                tickets[sort_i] = tickets[sort_j];
                profits[sort_i] = profits[sort_j];
                opentimes[sort_i] = opentimes[sort_j];
                types[sort_i] = types[sort_j];
                
                tickets[sort_j] = temp_ticket;
                profits[sort_j] = temp_profit;
                opentimes[sort_j] = temp_opentime;
                types[sort_j] = temp_type;
            }
        }
    }
    
    // 平掉盈利最多的订单
    for(int unlock_k = 0; unlock_k < unlock_count; unlock_k++)
    {
        // 安全检查：确保数组索引有效
        if(unlock_k >= array_size)
        {
            Print("❌ 数组索引越界: ", unlock_k, " >= ", array_size);
            break;
        }
        
        if(OrderSelect(tickets[unlock_k], SELECT_BY_TICKET))
        {
            if(types[unlock_k] == OP_BUY)
            {
                bool buy_close_result = OrderClose(tickets[unlock_k], OrderLots(), Bid, 3, clrRed);
                if(buy_close_result)
                {
                    Print("✅ 分批解锁成功 - 买入订单: ", tickets[unlock_k], " 盈利: ", profits[unlock_k]);
                }
                else
                {
                    Print("❌ 分批解锁失败 - 买入订单: ", tickets[unlock_k], " 错误: ", GetLastError());
                }
            }
            else if(types[unlock_k] == OP_SELL)
            {
                bool sell_close_result = OrderClose(tickets[unlock_k], OrderLots(), Ask, 3, clrRed);
                if(sell_close_result)
                {
                    Print("✅ 分批解锁成功 - 卖出订单: ", tickets[unlock_k], " 盈利: ", profits[unlock_k]);
                }
                else
                {
                    Print("❌ 分批解锁失败 - 卖出订单: ", tickets[unlock_k], " 错误: ", GetLastError());
                }
            }
        }
        else
        {
            Print("❌ 无法选择订单: ", tickets[unlock_k]);
        }
    }
}

//+------------------------------------------------------------------+
//| 全局平仓函数
//+------------------------------------------------------------------+
void CloseOrder(int ticket, string reason)
{
    // 改进：增强订单状态验证
    if(!OrderSelect(ticket, SELECT_BY_TICKET))
    {
        Print("⚠️ 平仓失败 - 无法选择订单: ", ticket, " (订单可能已不存在)");
        return;
    }
    
    // 检查订单是否为市价单（只有市价单才能平仓）
    if(OrderType() != OP_BUY && OrderType() != OP_SELL)
    {
        Print("⚠️ 平仓跳过 - 订单 ", ticket, " 不是市价单 (类型: ", OrderType(), ")");
        return;
    }
    
    // 检查订单是否属于当前EA
    if(OrderSymbol() != Symbol() || OrderMagicNumber() != 12345)
    {
        Print("⚠️ 平仓跳过 - 订单 ", ticket, " 不属于当前EA");
        return;
    }
    
    // 智能加仓订单特殊处理：跳过锁仓单保护
    string comment = OrderComment();
    bool is_smart_buy_order = (StringFind(comment, "智能加仓") >= 0);
    
    // 统一的锁仓单保护检查（智能加仓订单跳过此检查）
    if(!is_smart_buy_order && CLockOrderProtector::ShouldSkipOperation(reason))
    {
        Print("🛡️ 锁仓单保护：订单 ", ticket, " 不允许 ", reason, " 平仓");
        return;
    }
    
    // 获取订单信息（在OrderClose之前获取，因为平仓后无法获取）
    double profit = OrderProfit() + OrderSwap() + OrderCommission();
    double lots = OrderLots();
    int order_type = OrderType();
    string order_symbol = OrderSymbol();
    
    // 验证报价可用性
    double close_price = (order_type == OP_BUY) ? Bid : Ask;
    if(close_price <= 0)
    {
        Print("⚠️ 平仓失败 - 无效的平仓价格: ", close_price, " 订单: ", ticket);
        return;
    }
    
    // 验证手数有效性
    if(lots <= 0)
    {
        Print("⚠️ 平仓失败 - 无效的手数: ", lots, " 订单: ", ticket);
        return;
    }
    
    // 执行平仓
    Print("📝 尝试平仓 - 订单: ", ticket, " 手数: ", lots, " 价格: ", close_price, " 原因: ", reason);
    
    if(!OrderClose(ticket, lots, close_price, (int)MaxSlippage, clrRed))
    {
        int error_code = GetLastError();
        Print("❌ 平仓失败 - 订单: ", ticket, " 错误代码: ", error_code);
        CErrorHandler::HandleOrderError(error_code, "平仓");
    }
    else
    {
        Print("✅ 平仓成功 - 订单: ", ticket, " 原因: ", reason, " 盈亏: ", DoubleToString(profit, 2));
        CLogManager::LogClose(ticket, reason, profit, (order_type == OP_BUY ? "买入" : "卖出"));
    }
}

void CloseAllOrders()
{
    for(int i = OrdersTotal() - 1; i >= 0; i--)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                // 统一的锁仓单保护检查
                if(CLockOrderProtector::ShouldSkipOperation())
                {
                    Print("🛡️ 锁仓单保护：跳过订单 ", OrderTicket(), " 的全部平仓");
                    continue;
                }
                
                CloseOrder(OrderTicket(), "全部平仓");
            }
        }
    }
}

//+------------------------------------------------------------------+
//| 全局函数 - 用于简化高级指标调用
//+------------------------------------------------------------------+

// 布林带位置判断
double GetBollingerPosition()
{
    return advanced_indicators.GetBollingerPosition();
}

// MACD信号判断
int GetMACDSignal()
{
    return advanced_indicators.GetMACDSignal();
}

// KDJ信号判断
int GetKDJSignal()
{
    return advanced_indicators.GetKDJSignal();
}

// 高级市场评分
double GetAdvancedMarketScore()
{
    return advanced_market_analysis.GetAdvancedMarketScore();
}

// 市场状态分类
int GetMarketState()
{
    return advanced_market_analysis.GetMarketState();
}

// 更新应急仓位计数
void UpdateEmergencyOrderCount()
{
    g_emergency_order_count = CountEmergencyOrders();
}

//+------------------------------------------------------------------+
//| 全局决策评分计算函数
//+------------------------------------------------------------------+
void CalculateDecisionScores(double &buy_score, double &sell_score)
{
    // 使用缓存的技术指标 - 性能优化
    double ma_fast = indicator_cache.GetMA(12);  // 12周期EMA（黄金优化）
    double ma_slow = indicator_cache.GetMA(26);  // 26周期EMA（黄金优化）
    double rsi = indicator_cache.GetRSI();
    
    // 获取位置信息 - 新增位置感知
    PricePosition pos = market_monitor.GetPricePosition();
    
    // 市场评分
    double market_score = market_monitor.GetMarketScore();
    
    // 决策权重分配
    buy_score = 0.0;
    sell_score = 0.0;
    
    // 技术评分累加器 - 新增限制机制
    double technical_buy_score = 0.0;
    double technical_sell_score = 0.0;
    
    // 市场评分累加器 - 移到函数开头确保作用域正确
    double market_buy_score = 0.0;
    double market_sell_score = 0.0;
    
    // 原技术指标评分代码已移动到动态权重计算后，避免重复计算
    
    // 获取当前市场状态（如果启用）
    MARKET_REGIME current_regime = RANGING; // 默认震荡
    bool regime_changed = false;
    double final_technical_weight = TechnicalWeight;
    double final_market_weight = MarketWeight;
    
    if(EnableMarketRegimeDetection) {
        current_regime = advanced_market_analysis.GetCurrentRegime();
        regime_changed = advanced_market_analysis.CheckRegimeChange();
    }
    
    // 获取最终权重（如果启用动态调整）
    if(EnableDynamicWeightAdjustment) {
        final_technical_weight = advanced_market_analysis.GetDynamicTechnicalWeight(current_regime);
        final_market_weight = advanced_market_analysis.GetDynamicMarketWeight(current_regime);
    }
    
    // 重新计算技术评分 - 使用最终权重，避免双重应用
    technical_buy_score = 0.0;
    technical_sell_score = 0.0;
    
    // EMA渐进式评分 - 根据差距大小给分
    double ma_diff = ma_fast - ma_slow;
    double ma_diff_pct = MathAbs(ma_diff) / ma_slow * 10000; // 转换为万分比
    double ema_score_factor = MathMin(ma_diff_pct / 5.0, 1.0); // 5个万分点为满分
    
    if(ma_fast > ma_slow) {
        technical_buy_score += final_technical_weight * 0.3 * ema_score_factor;
        Print("📊 EMA信号: 快线(", DoubleToString(ma_fast, 5), ") > 慢线(", DoubleToString(ma_slow, 5), ") 差距:", DoubleToString(ma_diff_pct, 2), "万分点 → 买入评分 +", DoubleToString(final_technical_weight * 0.3 * ema_score_factor, 3));
    } else {
        technical_sell_score += final_technical_weight * 0.3 * ema_score_factor;
        Print("📊 EMA信号: 快线(", DoubleToString(ma_fast, 5), ") < 慢线(", DoubleToString(ma_slow, 5), ") 差距:", DoubleToString(ma_diff_pct, 2), "万分点 → 卖出评分 +", DoubleToString(final_technical_weight * 0.3 * ema_score_factor, 3));
    }
    
    // RSI渐进式评分 - 不只在极端时给分
    double rsi_score_factor = 0.0;
    if(rsi < RSIOversold) {
        rsi_score_factor = 1.0; // 完全超卖
        technical_buy_score += final_technical_weight * 0.2;
        Print("📊 RSI信号: 强超卖 ", DoubleToString(rsi, 1), " < ", DoubleToString(RSIOversold, 1), " → 买入评分 +", DoubleToString(final_technical_weight * 0.2, 2));
    } else if(rsi < RSIOversold + 10) {
        rsi_score_factor = (RSIOversold + 10 - rsi) / 10.0; // 渐进评分
        technical_buy_score += final_technical_weight * 0.2 * rsi_score_factor;
        Print("📊 RSI信号: 偏超卖 ", DoubleToString(rsi, 1), " → 买入评分 +", DoubleToString(final_technical_weight * 0.2 * rsi_score_factor, 3));
    } else if(rsi > RSIOverbought) {
        rsi_score_factor = 1.0; // 完全超买
        technical_sell_score += final_technical_weight * 0.2;
        Print("📊 RSI信号: 强超买 ", DoubleToString(rsi, 1), " > ", DoubleToString(RSIOverbought, 1), " → 卖出评分 +", DoubleToString(final_technical_weight * 0.2, 2));
    } else if(rsi > RSIOverbought - 10) {
        rsi_score_factor = (rsi - (RSIOverbought - 10)) / 10.0; // 渐进评分
        technical_sell_score += final_technical_weight * 0.2 * rsi_score_factor;
        Print("📊 RSI信号: 偏超买 ", DoubleToString(rsi, 1), " → 卖出评分 +", DoubleToString(final_technical_weight * 0.2 * rsi_score_factor, 3));
    } else {
        Print("📊 RSI信号: 中性 ", DoubleToString(rsi, 1));
    }
    
    // 高级技术指标 - 使用最终权重
    if(EnableAdvancedIndicators) {
        double bb_position = GetBollingerPosition();
        if(bb_position > BollingerOverbought) {
            technical_sell_score += final_technical_weight * 0.05;
            Print("📊 布林带信号: 超买 ", DoubleToString(bb_position, 1), "% → 卖出评分 +", DoubleToString(final_technical_weight * 0.05, 2));
        } else if(bb_position < BollingerOversold) {
            technical_buy_score += final_technical_weight * 0.05;
            Print("📊 布林带信号: 超卖 ", DoubleToString(bb_position, 1), "% → 买入评分 +", DoubleToString(final_technical_weight * 0.05, 2));
        } else {
            Print("📊 布林带信号: 中性 ", DoubleToString(bb_position, 1), "%");
        }
        
        int macd_signal = GetMACDSignal();
        double macd_main = advanced_indicators.GetMACDMain();
        double macd_signal_line = advanced_indicators.GetMACDSignalLine();
        double macd_histogram = advanced_indicators.GetMACDHistogram();
        
        // MACD渐进式评分 - 基于柱状图强度
        double macd_strength = MathAbs(macd_histogram);
        double macd_score_factor = MathMin(macd_strength * 1000, 1.0); // 柱状图强度转换为评分因子
        
        if(macd_signal == 1) {
            technical_buy_score += final_technical_weight * 0.25 * macd_score_factor;
            Print("📊 MACD信号: 看涨强度", DoubleToString(macd_score_factor, 3), " → 买入评分 +", DoubleToString(final_technical_weight * 0.25 * macd_score_factor, 3), " (主=", DoubleToString(macd_main, 5), " 柱=", DoubleToString(macd_histogram, 5), ")");
        } else if(macd_signal == -1) {
            technical_sell_score += final_technical_weight * 0.25 * macd_score_factor;
            Print("📊 MACD信号: 看跌强度", DoubleToString(macd_score_factor, 3), " → 卖出评分 +", DoubleToString(final_technical_weight * 0.25 * macd_score_factor, 3), " (主=", DoubleToString(macd_main, 5), " 柱=", DoubleToString(macd_histogram, 5), ")");
        } else if(macd_histogram > 0) {
            // 即使没有明确信号，柱状图为正也给予轻微买入倾向
            technical_buy_score += final_technical_weight * 0.25 * macd_score_factor * 0.3;
            Print("📊 MACD信号: 微弱看涨 → 买入评分 +", DoubleToString(final_technical_weight * 0.25 * macd_score_factor * 0.3, 3), " (柱=", DoubleToString(macd_histogram, 5), ")");
        } else if(macd_histogram < 0) {
            // 即使没有明确信号，柱状图为负也给予轻微卖出倾向
            technical_sell_score += final_technical_weight * 0.25 * macd_score_factor * 0.3;
            Print("📊 MACD信号: 微弱看跌 → 卖出评分 +", DoubleToString(final_technical_weight * 0.25 * macd_score_factor * 0.3, 3), " (柱=", DoubleToString(macd_histogram, 5), ")");
        } else {
            Print("📊 MACD信号: 中性 (主=", DoubleToString(macd_main, 5), " 信号=", DoubleToString(macd_signal_line, 5), " 柱=", DoubleToString(macd_histogram, 5), ")");
        }
        
        // ATR波动率判断
        double atr_value = indicator_cache.GetATR();
        double atr_avg = GetAverageATR(14); // 统一使用GetAverageATR函数
        if(atr_value > atr_avg * 1.2) {
            technical_buy_score += final_technical_weight * 0.2;
            technical_sell_score += final_technical_weight * 0.2;
            Print("📊 ATR信号: 高波动期 ", DoubleToString(atr_value, 2), " > ", DoubleToString(atr_avg * 1.2, 2), " → 双向评分 +", DoubleToString(final_technical_weight * 0.2, 2));
        } else if(atr_value < atr_avg * 0.8) {
            Print("📊 ATR信号: 低波动期 ", DoubleToString(atr_value, 2), " < ", DoubleToString(atr_avg * 0.8, 2), " → 谨慎交易");
        } else {
            Print("📊 ATR信号: 正常波动期 ", DoubleToString(atr_value, 2));
        }
    }
    
    // 限制技术评分最大值
    double max_technical_score = final_technical_weight * 1.0; // 最大值为最终权重的1.0倍
    technical_buy_score = MathMin(technical_buy_score, max_technical_score);
    technical_sell_score = MathMin(technical_sell_score, max_technical_score);
    
    // 将技术评分添加到总评分
    buy_score += technical_buy_score;
    sell_score += technical_sell_score;
    
    // 市场状态评分 - 增强版（修复不平衡问题）
    bool market_suitable = market_monitor.IsMarketSuitable();
    if(market_suitable)
    {
        // 重置市场评分累加器
        market_buy_score = 0.0;
        market_sell_score = 0.0;
        
        // 基础市场评分 - 使用最终权重
        if(market_score > 50) {
            // 市场评分高于50，偏向买入
            market_buy_score += final_market_weight * ((market_score - 50) / 50.0);
            if(EnableDynamicWeightAdjustment) {
                Print("📈 市场评分: 看涨 ", DoubleToString(market_score, 1), " → 买入评分 +", DoubleToString(final_market_weight * ((market_score - 50) / 50.0), 2), " (最终权重: ", DoubleToString(final_market_weight, 2), ")");
            } else {
                Print("📈 市场评分: 看涨 ", DoubleToString(market_score, 1), " → 买入评分 +", DoubleToString(final_market_weight * ((market_score - 50) / 50.0), 2));
            }
        } else {
            // 市场评分低于50，偏向卖出
            market_sell_score += final_market_weight * ((50 - market_score) / 50.0);
            if(EnableDynamicWeightAdjustment) {
                Print("📉 市场评分: 看跌 ", DoubleToString(market_score, 1), " → 卖出评分 +", DoubleToString(final_market_weight * ((50 - market_score) / 50.0), 2), " (最终权重: ", DoubleToString(final_market_weight, 2), ")");
            } else {
                Print("📉 市场评分: 看跌 ", DoubleToString(market_score, 1), " → 卖出评分 +", DoubleToString(final_market_weight * ((50 - market_score) / 50.0), 2));
            }
        }
        
        // 价格位置补充评分 - 增强低位买入/高位卖出倾向
        PricePosition pos = market_monitor.GetPricePosition();
        if(pos.position_50 < 40.0) {
            // 价格在40%以下，增加买入倾向
            double position_bonus = (40.0 - pos.position_50) / 40.0 * final_market_weight * 0.2;
            market_buy_score += position_bonus;
            Print("📍 价格位置: 低位", DoubleToString(pos.position_50, 1), "% → 买入评分 +", DoubleToString(position_bonus, 3));
        } else if(pos.position_50 > 60.0) {
            // 价格在60%以上，增加卖出倾向
            double position_bonus = (pos.position_50 - 60.0) / 40.0 * final_market_weight * 0.2;
            market_sell_score += position_bonus;
            Print("📍 价格位置: 高位", DoubleToString(pos.position_50, 1), "% → 卖出评分 +", DoubleToString(position_bonus, 3));
        } else {
            Print("📍 价格位置: 中性", DoubleToString(pos.position_50, 1), "%");
        }
        
        // 高级市场分析评分 - 新增集成（修复：方向化分配）
        if(EnableAdvancedMarketAnalysis)
        {
            double advanced_market_score = GetAdvancedMarketScore();
            int market_state = GetMarketState();
            
            // 根据市场状态和高级评分决定方向 - 使用最终权重
            if(market_state == 1) // 强势市场
            {
                // 强势市场偏向买入
                double bonus = final_market_weight * (advanced_market_score / 100.0) * 0.3; // 降低高级分析权重避免过度影响
                market_buy_score += bonus;
                if(EnableDynamicWeightAdjustment) {
                    Print("📈 高级市场分析: 强势市场 → 买入评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), " 最终权重: ", DoubleToString(final_market_weight, 2), ")");
                } else {
                    Print("📈 高级市场分析: 强势市场 → 买入评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), ")");
                }
            }
            else if(market_state == -1) // 弱势市场
            {
                // 弱势市场偏向卖出
                double bonus = final_market_weight * (advanced_market_score / 100.0) * 0.3; // 降低高级分析权重避免过度影响
                market_sell_score += bonus;
                if(EnableDynamicWeightAdjustment) {
                    Print("📉 高级市场分析: 弱势市场 → 卖出评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), " 最终权重: ", DoubleToString(final_market_weight, 2), ")");
                } else {
                    Print("📉 高级市场分析: 弱势市场 → 卖出评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), ")");
                }
            }
            else // 震荡市场
            {
                // 震荡市场根据高级评分分配
                if(advanced_market_score > 50) {
                    double bonus = final_market_weight * (advanced_market_score / 100.0) * 0.2; // 震荡市场进一步降低权重
                    market_buy_score += bonus;
                    if(EnableDynamicWeightAdjustment) {
                        Print("📊 高级市场分析: 震荡市场看涨 → 买入评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), " 最终权重: ", DoubleToString(final_market_weight, 2), ")");
                    } else {
                        Print("📊 高级市场分析: 震荡市场看涨 → 买入评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), ")");
                    }
                } else {
                    double bonus = final_market_weight * ((100 - advanced_market_score) / 100.0) * 0.2; // 震荡市场进一步降低权重
                    market_sell_score += bonus;
                    if(EnableDynamicWeightAdjustment) {
                        Print("📊 高级市场分析: 震荡市场看跌 → 卖出评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), " 最终权重: ", DoubleToString(final_market_weight, 2), ")");
                    } else {
                        Print("📊 高级市场分析: 震荡市场看跌 → 卖出评分 +", DoubleToString(bonus, 2), " (评分=", DoubleToString(advanced_market_score, 1), ")");
                    }
                }
            }
        }
        
        // 限制市场评分最大值 - 使用最终权重
        double max_market_score = final_market_weight * 1.0; // 最大市场评分为最终权重的1.0倍
        market_buy_score = MathMin(market_buy_score, max_market_score);
        market_sell_score = MathMin(market_sell_score, max_market_score);
        
        // 将市场评分添加到总评分
        buy_score += market_buy_score;
        sell_score += market_sell_score;
    }
    
    // AI预测评分（如果可用且置信度足够且AI权重不为0）
    int ai_prediction = -1;
    double ai_confidence = 0.0;
    bool has_ai_signal = false;
    
    if(EnableAI && AIWeight > 0)
    {
        has_ai_signal = ai_predictor.GetAIPrediction(ai_prediction, ai_confidence);
    }
    
    if(has_ai_signal && ai_confidence >= MinAIConfidence && AIWeight > 0)
    {
        // 位置感知动态权重调整
        double position_adjusted_weight = AIWeight;
        
        if(EnablePositionAwareness)
        {
            // 根据价格位置调整AI权重 - 修复逻辑
            if(pos.is_high_risk && ai_prediction == 2)  // 高位看涨，风险较高
            {
                position_adjusted_weight *= AIWeightReductionFactor;
                Print("📊 位置感知：高位看涨，AI权重降低至 ", DoubleToString(position_adjusted_weight, 2));
            }
            else if(pos.is_low_risk && ai_prediction == 0)  // 低位看跌，风险较高
            {
                position_adjusted_weight *= AIWeightReductionFactor;
                Print("📊 位置感知：低位看跌，AI权重降低至 ", DoubleToString(position_adjusted_weight, 2));
            }
        }
        
        // AI评分累加器 - 新增限制机制
        double ai_buy_score = 0.0;
        double ai_sell_score = 0.0;
        
        if(ai_prediction == 2)  // 2 = 买入信号
        {
            ai_buy_score += position_adjusted_weight * ai_confidence;
            Print("🤖 AI信号: 买入 (置信度=", DoubleToString(ai_confidence, 2), ") → 买入评分 +", DoubleToString(position_adjusted_weight * ai_confidence, 2));
        }
        else if(ai_prediction == 0)  // 0 = 卖出信号
        {
            ai_sell_score += position_adjusted_weight * ai_confidence;
            Print("🤖 AI信号: 卖出 (置信度=", DoubleToString(ai_confidence, 2), ") → 卖出评分 +", DoubleToString(position_adjusted_weight * ai_confidence, 2));
        }
        else
        {
            Print("🤖 AI信号: 中性 (预测值=", ai_prediction, ", 置信度=", DoubleToString(ai_confidence, 2), ")");
        }
        
        // 限制AI评分最大值
        double max_ai_score = AIWeight * 1.0; // 最大AI评分为权重本身
        ai_buy_score = MathMin(ai_buy_score, max_ai_score);
        ai_sell_score = MathMin(ai_sell_score, max_ai_score);
        
        // 将AI评分添加到总评分
        buy_score += ai_buy_score;
        sell_score += ai_sell_score;
    }
    
    // 反转信号奖励 - 修复逻辑
    if(EnableDecisionScoreReversal)
    {
        int reversal_signal = -1;
        double reversal_confidence = 0.0;
        bool has_reversal = ai_predictor.CheckDecisionScoreReversal(0, reversal_signal, reversal_confidence);
        if(has_reversal && reversal_confidence > 0.8) // 修复：使用反转置信度而不是AI置信度
        {
            double reversal_bonus = ReversalSignalBonus * 0.5; // 降低奖励值
            if(reversal_signal == 2)  // 反转信号为买入
            {
                buy_score += reversal_bonus;
                Print("🔄 决策评分反转奖励：买入评分 +", DoubleToString(reversal_bonus, 2), " (反转信号=", reversal_signal, ", 置信度=", DoubleToString(reversal_confidence, 2), ")");
            }
            else if(reversal_signal == 0)  // 反转信号为卖出
            {
                sell_score += reversal_bonus;
                Print("🔄 决策评分反转奖励：卖出评分 +", DoubleToString(reversal_bonus, 2), " (反转信号=", reversal_signal, ", 置信度=", DoubleToString(reversal_confidence, 2), ")");
            }
        }
        else if(has_reversal)
        {
            Print("🔄 反转信号存在但置信度不足: ", DoubleToString(reversal_confidence, 2), " < 0.8");
        }
    }
    
    // 确保评分不超过100%
    buy_score = MathMin(buy_score, 100.0);
    sell_score = MathMin(sell_score, 100.0);
    
    // 添加协同评分和状态信息
    if(EnableMarketRegimeDetection && regime_changed) {
        Print("🔄 市场状态变化检测: ", advanced_market_analysis.GetRegimeName(current_regime));
    }
    
    // 计算协同评分（如果启用）
    if(EnableSynergyScoring) {
        double synergy_buy = advanced_market_analysis.GetSynergyScore(technical_buy_score, market_buy_score, current_regime);
        double synergy_sell = advanced_market_analysis.GetSynergyScore(technical_sell_score, market_sell_score, current_regime);
        Print("🤝 协同评分 - 买入: ", DoubleToString(synergy_buy, 2), " 卖出: ", DoubleToString(synergy_sell, 2));
    }
    
    // 添加详细的调试信息
    Print("🎯 最终决策评分 - 买入: ", DoubleToString(buy_score, 2), " 卖出: ", DoubleToString(sell_score, 2));
    if(EnableDynamicWeightAdjustment) {
        Print("📊 技术评分 - 买入: ", DoubleToString(technical_buy_score, 2), " 卖出: ", DoubleToString(technical_sell_score, 2), " (最终权重: ", DoubleToString(final_technical_weight, 2), ")");
    } else {
        Print("📊 技术评分 - 买入: ", DoubleToString(technical_buy_score, 2), " 卖出: ", DoubleToString(technical_sell_score, 2), " (基础权重: ", DoubleToString(TechnicalWeight, 2), ")");
    }
    if(market_suitable) {
        if(EnableDynamicWeightAdjustment) {
            Print("📈 市场评分 - 基础: ", DoubleToString(market_score, 2), " (最终权重: ", DoubleToString(final_market_weight, 2), ")");
        } else {
            Print("📈 市场评分 - 基础: ", DoubleToString(market_score, 2), " (基础权重: ", DoubleToString(MarketWeight, 2), ")");
        }
    }
    if(has_ai_signal && ai_confidence >= MinAIConfidence) {
        Print("🤖 AI评分 - 预测: ", ai_prediction, " 置信度: ", DoubleToString(ai_confidence, 2));
    }
    Print("📍 价格位置 - 50周期: ", DoubleToString(pos.position_50, 1), "% 100周期: ", DoubleToString(pos.position_100, 1), "%");
    if(EnableMarketRegimeDetection) {
        Print("🏛️ 市场状态: ", advanced_market_analysis.GetRegimeName(current_regime), " (状态变化后时间: ", advanced_market_analysis.GetTimeSinceRegimeChange(), " ticks)");
    }
    Print("🔍 决策评分计算完成 - 时间: ", TimeToString(TimeCurrent()));
}

//+------------------------------------------------------------------+




//+------------------------------------------------------------------+
//| 全局应急仓位统计函数
//+------------------------------------------------------------------+
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
//| 智能加仓核心函数
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| 检查是否可以触发智能加仓
//+------------------------------------------------------------------+
bool CanTriggerSmartBuy()
{
    double avg_loss_pips;
    int dominant_direction;
    return CheckSmartBuyTriggerConditions(avg_loss_pips, dominant_direction);
}

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
    
    // 智能加仓不受总订单数量限制，可以在正常仓位满的情况下下单
    int total_orders = CountNormalOrders() + CountLockOrders() + CountEmergencyOrders() + g_smart_buy_orders;
    Print("📊 当前总订单数量: ", total_orders, "/", MaxOpenOrders, " (智能加仓不受此限制)");
    
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
                    double order_loss_pips = -order_profit / Point;
                    
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
    
    // 检查亏损阈值（可选条件）
    if(SmartBuyUseLossTrigger)
    {
        Print("📊 智能加仓亏损检查: 平均亏损=", avg_loss_pips, " 触发阈值=", SmartBuyLossThreshold, " 最大阈值=", SmartBuyMaxLossThreshold);
        if(avg_loss_pips < SmartBuyLossThreshold || avg_loss_pips > SmartBuyMaxLossThreshold)
        {
            Print("📊 平均亏损不在智能加仓范围内: ", avg_loss_pips, " (", SmartBuyLossThreshold, " - ", SmartBuyMaxLossThreshold, ")");
            return false;
        }
        
        // 确定主导方向（仅在使用亏损触发时）
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
    }
    else
    {
        Print("📊 智能加仓使用决策评分触发，跳过亏损检查");
        // 主导方向将由决策评分确定，这里设为-1表示不限制
        dominant_direction = -1;
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
    
    // 简化手数计算逻辑，避免过度复杂
    double lot_multiplier = 1.0;
    if(avg_loss_pips >= 3000.0) lot_multiplier = 1.5;
    else if(avg_loss_pips >= 2000.0) lot_multiplier = 1.3;
    else if(avg_loss_pips >= 1000.0) lot_multiplier = 1.2;
    
    // 简化倍数计算，避免过度放大
    double confidence_multiplier = MathMin(ai_confidence, 1.0);
    double decision_multiplier = MathMin(decision_score / 100.0, 1.0);
    
    // 计算最终手数，添加更严格的上限
    double final_lot = base_lot * lot_multiplier * confidence_multiplier * decision_multiplier;
    
    // 确保不超过最大手数限制
    double max_allowed_lot = MaxSmartBuyTotalLots - g_smart_buy_total_lots;
    if(max_allowed_lot <= 0)
    {
        return 0.0;
    }
    
    // 更严格的手数限制
    final_lot = MathMin(final_lot, max_allowed_lot);
    final_lot = MathMin(final_lot, 0.01); // 单次最大0.01手
    final_lot = MathMax(final_lot, 0.01); // 最小0.01手
    
    // 标准化手数
    final_lot = NormalizeDouble(final_lot, 2);
    
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
    
    // 修复：执行前再次检查订单数量
    UpdateSmartBuyStats();
    if(g_smart_buy_orders >= MaxSmartBuyOrders)
    {
        Print("📊 执行前检查：智能加仓订单数量已达上限: ", g_smart_buy_orders, "/", MaxSmartBuyOrders);
        return false;
    }
    
    // 构建订单注释 - 简化格式避免MT4显示问题
    string comment = "智能加仓";
    
    // 计算止盈止损价格
    double stop_loss = 0.0;
    double take_profit = 0.0;
    
    if(order_type == OP_BUY)
    {
        stop_loss = open_price - SmartBuyStopLoss * Point;
        take_profit = open_price + SmartBuyProfitTarget * Point;
    }
    else if(order_type == OP_SELL)
    {
        stop_loss = open_price + SmartBuyStopLoss * Point;
        take_profit = open_price - SmartBuyProfitTarget * Point;
    }
    
    // 执行订单
    int ticket = OrderSend(Symbol(), order_type, lot_size, open_price, (int)MaxSlippage, stop_loss, take_profit, comment, 12345, 0, clrBlue);
    
    if(ticket > 0)
    {
        // 立即验证订单注释是否正确设置
        if(OrderSelect(ticket, SELECT_BY_TICKET))
        {
            string actual_comment = OrderComment();
            if(StringFind(actual_comment, "智能加仓") >= 0)
            {
                Print("✅ 智能加仓订单注释验证成功: ", actual_comment);
            }
            else
            {
                Print("⚠️ 智能加仓订单注释验证失败: 期望包含'智能加仓'，实际为: '", actual_comment, "'");
            }
        }
        else
        {
            Print("⚠️ 无法选择订单进行注释验证: ", ticket);
        }
        
        // 修复：重新统计而不是手动增加
        UpdateSmartBuyStats();
        g_last_smart_buy_time = TimeCurrent();
        
        // 记录智能加仓信息
        if(g_smart_buy_record_count < 2)
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
        else
        {
            Print("⚠️ 智能加仓记录数组已满(2个)，无法记录新订单信息");
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
        Print("❌ 智能加仓订单执行失败: ", error);
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
    
    // 优化：使用局部变量避免重复调用OrdersTotal()
    int total_orders = OrdersTotal();
    
    // 简化统计方法，减少日志输出
    for(int i = 0; i < total_orders; i++)
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
    for(int i = 0; i < g_smart_buy_record_count && i < 2; i++)
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

//+------------------------------------------------------------------+
//| 检查智能加仓条件并执行
//+------------------------------------------------------------------+
void CheckAndExecuteSmartBuy(double ai_confidence, double buy_score, double sell_score, int ai_prediction = -1)
{
    if(!EnableSmartBuyStrategy) return;
    
    // 更新智能加仓统计
    UpdateSmartBuyStats();
    
    // 使用传入的决策评分参数
    Print("📊 智能加仓检查 - 买入评分: ", buy_score, " 卖出评分: ", sell_score);
    
    // 检查决策评分是否足够高
    double max_decision_score = MathMax(buy_score, sell_score);
    if(max_decision_score < SmartBuyDecisionThreshold)
    {
        Print("📊 决策评分不足，跳过智能加仓: ", max_decision_score, " < ", SmartBuyDecisionThreshold);
        return;
    }
    
    // 检查基础触发条件（时间间隔、数量限制等）
    double avg_loss_pips = 0.0;
    int dominant_direction = -1;
    
    if(!CheckSmartBuyTriggerConditions(avg_loss_pips, dominant_direction))
    {
        return;
    }
    
    // 确定加仓方向（基于决策评分，而非亏损方向）
    int smart_buy_direction = -1;
    if(buy_score > sell_score && buy_score >= SmartBuyDecisionThreshold)
    {
        smart_buy_direction = OP_BUY;
    }
    else if(sell_score > buy_score && sell_score >= SmartBuyDecisionThreshold)
    {
        smart_buy_direction = OP_SELL;
    }
    else
    {
        Print("📊 决策评分不足以确定加仓方向");
        return;
    }
    
    // 检查AI预测方向是否与决策方向一致（可选条件，仅作参考）
    bool ai_direction_match = false;
    if(smart_buy_direction == OP_BUY && ai_prediction == 2) // 买入方向且AI预测为买入
    {
        ai_direction_match = true;
    }
    else if(smart_buy_direction == OP_SELL && ai_prediction == 0) // 卖出方向且AI预测为卖出
    {
        ai_direction_match = true;
    }
    
    // 记录方向一致性（仅作参考，不影响执行）
    if(ai_direction_match)
    {
        Print("📊 AI预测方向与决策方向一致，增强信心");
    }
    else
    {
        Print("📊 AI预测方向与决策方向不一致，但基于决策评分执行");
        Print("   决策方向: ", (smart_buy_direction == OP_BUY ? "买入" : "卖出"));
        Print("   AI预测方向: ", (ai_prediction == 2 ? "买入" : (ai_prediction == 0 ? "卖出" : "中性")));
    }
    
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
    
    // 智能加仓方向分析
    Print("📊 智能加仓方向分析:");
    Print("   决策方向: ", (smart_buy_direction == OP_BUY ? "买入" : "卖出"));
    Print("   决策评分: ", decision_score, " (阈值: ", SmartBuyDecisionThreshold, ")");
    Print("   买入评分: ", buy_score, " 卖出评分: ", sell_score);
    
    // 智能加仓执行确认
    Print("✅ 智能加仓条件满足，准备基于决策评分建仓");
    Print("   方向: ", (smart_buy_direction == OP_BUY ? "买入" : "卖出"));
    Print("   决策评分: ", decision_score, " (阈值: ", SmartBuyDecisionThreshold, ")");
    Print("   平均亏损: ", avg_loss_pips, " 点数");
    Print("   AI置信度: ", ai_confidence, " (仅供参考)");
    
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