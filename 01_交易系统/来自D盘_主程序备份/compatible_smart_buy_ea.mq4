//+------------------------------------------------------------------+
//| 兼容性智能加仓策略EA
//| 与原有AI_Enhanced_Risk_EA完全兼容
//+------------------------------------------------------------------+
#property copyright "Compatible Smart Buy Strategy EA"
#property link      ""
#property version   "1.00"
#property strict

//--- 兼容性参数（与原有EA保持一致）
input bool EnableSmartBuyStrategy = true;     // 启用智能加仓
input double SmartBuyAIConfidenceThreshold = 0.7;  // AI置信度阈值
input double SmartBuyProfitTargetPips = 500.0;     // 盈利目标点数
input double SmartBuyStopLossPips = 8000.0;        // 止损点数

//--- 金字塔加仓参数（兼容原有EA限制）
input double PyramidLevel1 = 1000.0;          // 第一层加仓点位
input double PyramidLevel2 = 2000.0;          // 第二层加仓点位
input double PyramidLevel3 = 3000.0;          // 第三层加仓点位
input double PyramidLevel4 = 4000.0;          // 第四层加仓点位
input double PyramidLevel5 = 5000.0;          // 第五层加仓点位

input double PyramidLot1 = 2.0;               // 第一层手数倍数
input double PyramidLot2 = 3.0;               // 第二层手数倍数
input double PyramidLot3 = 5.0;               // 第三层手数倍数
input double PyramidLot4 = 8.0;               // 第四层手数倍数
input double PyramidLot5 = 13.0;              // 第五层手数倍数

//--- 使用原有EA的参数（不重复定义）
extern int MaxNormalOrders = 12;              // 普通仓最多12个（与原有EA一致）
extern int MinOrderInterval = 900;            // 15分钟间隔（与原有EA一致）
extern double FixedLotSize = 0.01;            // 基础手数（与原有EA一致）

//--- 全局变量
datetime g_last_smart_buy_time = 0;
int g_smart_buy_orders = 0;
double g_smart_buy_total_lots = 0.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🤖 兼容性智能加仓策略EA启动");
    Print("📊 兼容性参数设置:");
    Print("   启用智能加仓: ", EnableSmartBuyStrategy ? "是" : "否");
    Print("   AI置信度阈值: ", SmartBuyAIConfidenceThreshold);
    Print("   使用原有EA限制: MaxNormalOrders=", MaxNormalOrders, " MinOrderInterval=", MinOrderInterval);
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🤖 兼容性智能加仓策略EA停止");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    if(!EnableSmartBuyStrategy) return;
    
    // 更新智能加仓统计
    UpdateSmartBuyStats();
    
    // 检查AI预测
    int ai_prediction = GetAIPrediction();
    double ai_confidence = GetAIConfidence();
    
    // 如果AI预测看涨且置信度足够高
    if(ai_prediction == 2 && ai_confidence >= SmartBuyAIConfidenceThreshold)
    {
        // 检查是否应该加仓（使用原有EA的限制条件）
        if(ShouldExecuteSmartBuy(ai_confidence))
        {
            // 计算最优手数
            double optimal_lot = CalculateOptimalLotSize(ai_confidence);
            
            // 执行买入
            ExecuteSmartBuyOrder(optimal_lot, ai_confidence);
        }
    }
}

//+------------------------------------------------------------------+
//| 更新智能加仓统计                                                  |
//+------------------------------------------------------------------+
void UpdateSmartBuyStats()
{
    g_smart_buy_orders = 0;
    g_smart_buy_total_lots = 0.0;
    
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
}

//+------------------------------------------------------------------+
//| 获取AI预测                                                        |
//+------------------------------------------------------------------+
int GetAIPrediction()
{
    string file_path = "C:\\Program Files (x86)\\Hantec Markets V MT4 Terminal\\MQL4\\Files\\ai_prediction.txt";
    
    if(!FileIsExist(file_path))
        return -1;
    
    int file_handle = FileOpen(file_path, FILE_READ|FILE_TXT);
    if(file_handle == INVALID_HANDLE)
        return -1;
    
    string line = FileReadString(file_handle);
    FileClose(file_handle);
    
    // 解析预测结果
    if(StringFind(line, "AI预测: 2") >= 0)
        return 2;  // 看涨
    else if(StringFind(line, "AI预测: 1") >= 0)
        return 1;  // 看跌
    else if(StringFind(line, "AI预测: 0") >= 0)
        return 0;  // 震荡
    
    return -1;
}

//+------------------------------------------------------------------+
//| 获取AI置信度                                                      |
//+------------------------------------------------------------------+
double GetAIConfidence()
{
    string file_path = "C:\\Program Files (x86)\\Hantec Markets V MT4 Terminal\\MQL4\\Files\\ai_prediction.txt";
    
    if(!FileIsExist(file_path))
        return 0.0;
    
    int file_handle = FileOpen(file_path, FILE_READ|FILE_TXT);
    if(file_handle == INVALID_HANDLE)
        return 0.0;
    
    string line = FileReadString(file_handle);
    FileClose(file_handle);
    
    // 解析置信度
    int pos = StringFind(line, "置信度: ");
    if(pos >= 0)
    {
        string confidence_str = StringSubstr(line, pos + 8, 6);
        return StringToDouble(confidence_str);
    }
    
    return 0.0;
}

//+------------------------------------------------------------------+
//| 检查是否应该执行智能加仓（兼容原有EA限制）                        |
//+------------------------------------------------------------------+
bool ShouldExecuteSmartBuy(double ai_confidence)
{
    // 检查时间间隔（使用原有EA的间隔）
    if(TimeCurrent() - g_last_smart_buy_time < MinOrderInterval)
    {
        int remaining = MinOrderInterval - (int)(TimeCurrent() - g_last_smart_buy_time);
        Print("⏰ 智能加仓间隔不足，还需等待 ", remaining/60, "分", remaining%60, "秒");
        return false;
    }
    
    // 检查总订单数量（使用原有EA的限制）
    int total_orders = CountTotalOrders();
    if(total_orders >= MaxNormalOrders)
    {
        Print("📊 总订单数已达上限: ", total_orders, "/", MaxNormalOrders);
        return false;
    }
    
    // 检查同方向订单数量（兼容原有EA逻辑）
    if(HasTooManySameDirectionOrders(OP_BUY))
    {
        Print("📊 同方向订单过多，跳过智能加仓");
        return false;
    }
    
    // 检查平均亏损
    double avg_loss_pips = CalculateAverageLossPips();
    if(avg_loss_pips >= SmartBuyStopLossPips)
    {
        Print("🛑 亏损过大，不建议继续加仓: ", DoubleToString(avg_loss_pips, 1), "点");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| 统计总订单数量                                                    |
//+------------------------------------------------------------------+
int CountTotalOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                count++;
            }
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| 检查同方向订单数量（兼容原有EA逻辑）                              |
//+------------------------------------------------------------------+
bool HasTooManySameDirectionOrders(int order_type)
{
    int same_direction_count = 0;
    
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                if(OrderType() == order_type)
                {
                    same_direction_count++;
                }
            }
        }
    }
    
    // 使用原有EA的同方向限制逻辑
    return same_direction_count >= 12;  // 原有EA限制同方向最多12个
}

//+------------------------------------------------------------------+
//| 计算平均亏损点数                                                  |
//+------------------------------------------------------------------+
double CalculateAverageLossPips()
{
    double total_loss_pips = 0.0;
    int buy_count = 0;
    
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                if(OrderType() == OP_BUY)
                {
                    double profit = OrderProfit() + OrderSwap() + OrderCommission();
                    if(profit < 0)
                    {
                        total_loss_pips += MathAbs(profit) / Point;
                        buy_count++;
                    }
                }
            }
        }
    }
    
    return buy_count > 0 ? total_loss_pips / buy_count : 0.0;
}

//+------------------------------------------------------------------+
//| 计算最优加仓手数                                                  |
//+------------------------------------------------------------------+
double CalculateOptimalLotSize(double ai_confidence)
{
    double avg_loss_pips = CalculateAverageLossPips();
    double lot_multiplier = 1.0;
    
    // 根据亏损程度确定金字塔层级
    if(avg_loss_pips >= PyramidLevel5)
        lot_multiplier = PyramidLot5;
    else if(avg_loss_pips >= PyramidLevel4)
        lot_multiplier = PyramidLot4;
    else if(avg_loss_pips >= PyramidLevel3)
        lot_multiplier = PyramidLot3;
    else if(avg_loss_pips >= PyramidLevel2)
        lot_multiplier = PyramidLot2;
    else if(avg_loss_pips >= PyramidLevel1)
        lot_multiplier = PyramidLot1;
    
    // 根据AI置信度调整手数
    double confidence_multiplier = MathMin(ai_confidence / 0.5, 2.0);
    
    // 计算最终手数
    double optimal_lot = FixedLotSize * lot_multiplier * confidence_multiplier;
    
    // 限制最大手数
    optimal_lot = MathMin(optimal_lot, 0.1);  // 最大0.1手
    
    return MathMax(optimal_lot, 0.01);
}

//+------------------------------------------------------------------+
//| 执行智能加仓订单                                                  |
//+------------------------------------------------------------------+
void ExecuteSmartBuyOrder(double lot_size, double ai_confidence)
{
    double price = Ask;
    string comment = "智能加仓";
    
    int ticket = OrderSend(Symbol(), OP_BUY, lot_size, price, 3, 0, 0, comment, 12345, 0, clrBlue);
    
    if(ticket > 0)
    {
        g_last_smart_buy_time = TimeCurrent();
        Print("✅ 智能加仓成功: 订单#", ticket, " 手数:", DoubleToString(lot_size, 2), " AI置信度:", DoubleToString(ai_confidence, 3));
        
        // 更新统计
        UpdateSmartBuyStats();
        
        // 显示加仓效果分析
        ShowSmartBuyEffectAnalysis(lot_size, price);
    }
    else
    {
        Print("❌ 智能加仓失败: 错误代码", GetLastError());
    }
}

//+------------------------------------------------------------------+
//| 显示智能加仓效果分析                                              |
//+------------------------------------------------------------------+
void ShowSmartBuyEffectAnalysis(double new_lot, double new_price)
{
    double total_lots = g_smart_buy_total_lots + new_lot;
    double weighted_price = 0.0;
    double total_value = 0.0;
    
    // 计算加权平均价格
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == 12345)
            {
                if(OrderType() == OP_BUY)
                {
                    weighted_price += OrderOpenPrice() * OrderLots();
                    total_value += OrderLots();
                }
            }
        }
    }
    
    // 加上新订单
    weighted_price += new_price * new_lot;
    total_value += new_lot;
    
    double avg_price = weighted_price / total_value;
    
    Print("📊 智能加仓效果分析:");
    Print("   新订单价格: ", DoubleToString(new_price, 2));
    Print("   加权平均价格: ", DoubleToString(avg_price, 2));
    Print("   总手数: ", DoubleToString(total_lots, 2));
    Print("   成本降低: ", DoubleToString((avg_price - new_price) * 10, 2), "美元");
    
    // 计算盈利目标
    double target_price = avg_price + (SmartBuyProfitTargetPips * Point);
    double potential_profit = (target_price - avg_price) * total_lots * 10;
    
    Print("   盈利目标价格: ", DoubleToString(target_price, 2));
    Print("   潜在盈利: ", DoubleToString(potential_profit, 2), "美元");
}

//+------------------------------------------------------------------+
//| 自定义函数：获取智能加仓信息                                      |
//+------------------------------------------------------------------+
string GetSmartBuyInfo()
{
    string info = "📊 智能加仓信息:\n";
    info += "   智能加仓订单数: " + IntegerToString(g_smart_buy_orders) + "\n";
    info += "   智能加仓总手数: " + DoubleToString(g_smart_buy_total_lots, 2) + "\n";
    info += "   平均亏损: " + DoubleToString(CalculateAverageLossPips(), 1) + "点\n";
    info += "   启用状态: " + (EnableSmartBuyStrategy ? "是" : "否") + "\n";
    
    return info;
} 