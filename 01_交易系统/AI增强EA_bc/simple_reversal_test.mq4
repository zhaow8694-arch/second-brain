//+------------------------------------------------------------------+
//| 简化反转信号测试脚本
//| 专门用于快速测试反转信号的检测和执行
//+------------------------------------------------------------------+
#property copyright "Simple Reversal Test"
#property link      ""
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| 脚本启动函数
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== 简化反转信号测试 ===");
    Print("测试时间: ", TimeToString(TimeCurrent()));
    Print("货币对: ", Symbol());
    Print("周期: ", Period());
    
    // 测试1: 计算决策评分
    TestDecisionScores();
    
    // 测试2: 模拟反转信号检测
    TestReversalDetection();
    
    // 测试3: 检查当前仓位状态
    TestCurrentPositions();
    
    // 测试4: 模拟应急仓位触发
    TestEmergencyTrigger();
    
    Print("=== 测试完成 ===");
}

//+------------------------------------------------------------------+
//| 测试决策评分计算
//+------------------------------------------------------------------+
void TestDecisionScores()
{
    Print("\n--- 测试决策评分计算 ---");
    
    double buy_score = 0.0, sell_score = 0.0;
    
    // 技术指标评分
    double ma_fast = iMA(Symbol(), Period(), 15, 0, MODE_SMA, PRICE_CLOSE, 0);
    double ma_slow = iMA(Symbol(), Period(), 30, 0, MODE_SMA, PRICE_CLOSE, 0);
    double rsi = iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 0);
    double macd_main = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
    double macd_signal = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 0);
    
    Print("技术指标值:");
    Print("  MA(15): ", DoubleToString(ma_fast, 5));
    Print("  MA(30): ", DoubleToString(ma_slow, 5));
    Print("  RSI: ", DoubleToString(rsi, 2));
    Print("  MACD主: ", DoubleToString(macd_main, 5));
    Print("  MACD信号: ", DoubleToString(macd_signal, 5));
    
    // 计算评分 (使用EA的权重设置)
    double TechnicalWeight = 0.6;  // 技术分析权重60%
    double MarketWeight = 0.3;     // 市场状态权重30%
    double AIWeight = 0.1;         // AI预测权重10%
    
    // MA信号 (权重50%)
    if(ma_fast > ma_slow)
    {
        buy_score += TechnicalWeight * 0.5;
        Print("  MA信号: 买入 +", DoubleToString(TechnicalWeight * 0.5, 3));
    }
    else
    {
        sell_score += TechnicalWeight * 0.5;
        Print("  MA信号: 卖出 +", DoubleToString(TechnicalWeight * 0.5, 3));
    }
    
    // RSI信号 (权重50%)
    if(rsi < 30)
    {
        buy_score += TechnicalWeight * 0.5;
        Print("  RSI信号: 超买 +", DoubleToString(TechnicalWeight * 0.5, 3));
    }
    else if(rsi > 70)
    {
        sell_score += TechnicalWeight * 0.5;
        Print("  RSI信号: 超卖 +", DoubleToString(TechnicalWeight * 0.5, 3));
    }
    
    // MACD信号 (权重100%)
    if(macd_main > macd_signal)
    {
        buy_score += TechnicalWeight * 1.0;
        Print("  MACD信号: 买入 +", DoubleToString(TechnicalWeight * 1.0, 3));
    }
    else
    {
        sell_score += TechnicalWeight * 1.0;
        Print("  MACD信号: 卖出 +", DoubleToString(TechnicalWeight * 1.0, 3));
    }
    
    // 市场状态评分 (简化)
    double market_score = 50.0; // 假设中性市场
    buy_score += MarketWeight * (market_score / 100.0);
    sell_score += MarketWeight * (market_score / 100.0);
    Print("  市场评分: 中性 +", DoubleToString(MarketWeight * (market_score / 100.0), 3));
    
    // AI预测评分 (简化)
    double ai_confidence = 0.5; // 假设AI置信度0.5
    buy_score += AIWeight * ai_confidence;
    sell_score += AIWeight * ai_confidence;
    Print("  AI评分: 中性 +", DoubleToString(AIWeight * ai_confidence, 3));
    
    Print("最终评分:");
    Print("  买入评分: ", DoubleToString(buy_score, 6));
    Print("  卖出评分: ", DoubleToString(sell_score, 6));
    Print("  评分差值: ", DoubleToString(buy_score - sell_score, 6));
}

//+------------------------------------------------------------------+
//| 测试反转信号检测
//+------------------------------------------------------------------+
void TestReversalDetection()
{
    Print("\n--- 测试反转信号检测 ---");
    
    // 模拟不同持仓情况
    TestReversalForPosition(OP_BUY, "持多仓");
    TestReversalForPosition(OP_SELL, "持空仓");
    TestReversalForPosition(-1, "无持仓");
}

//+------------------------------------------------------------------+
//| 测试特定持仓的反转信号
//+------------------------------------------------------------------+
void TestReversalForPosition(int position_type, string position_name)
{
    Print("\n测试", position_name, ":");
    
    // 计算决策评分
    double buy_score = 0.0, sell_score = 0.0;
    CalculateSimpleScores(buy_score, sell_score);
    
    // 检查反转信号
    bool is_reversal = false;
    int reversal_signal = -1;
    double reversal_confidence = 0.0;
    
    if(position_type == OP_BUY && sell_score > buy_score)
    {
        // 持多仓，但决策看跌
        is_reversal = true;
        reversal_signal = OP_SELL;
        reversal_confidence = sell_score;
    }
    else if(position_type == OP_SELL && buy_score > sell_score)
    {
        // 持空仓，但决策看涨
        is_reversal = true;
        reversal_signal = OP_BUY;
        reversal_confidence = buy_score;
    }
    
    Print("  持仓类型: ", position_name);
    Print("  买入评分: ", DoubleToString(buy_score, 6));
    Print("  卖出评分: ", DoubleToString(sell_score, 6));
    Print("  检测到反转: ", (is_reversal ? "是" : "否"));
    
    if(is_reversal)
    {
        Print("  反转方向: ", (reversal_signal == OP_BUY ? "买入" : "卖出"));
        Print("  反转置信度: ", DoubleToString(reversal_confidence, 6));
        
        // 检查阈值
        double DecisionReversalThreshold = 0.6;
        double EmergencyTriggerScore = 0.8;
        
        Print("  基础阈值(0.6): ", (reversal_confidence >= DecisionReversalThreshold ? "通过" : "未通过"));
        Print("  应急阈值(0.8): ", (reversal_confidence >= EmergencyTriggerScore ? "通过" : "未通过"));
        Print("  强反转阈值(0.8): ", (reversal_confidence >= 0.8 ? "通过" : "未通过"));
        Print("  强制平仓阈值(0.9): ", (reversal_confidence >= 0.9 ? "通过" : "未通过"));
    }
}

//+------------------------------------------------------------------+
//| 检查当前仓位状态
//+------------------------------------------------------------------+
void TestCurrentPositions()
{
    Print("\n--- 检查当前仓位状态 ---");
    
    int total_orders = OrdersTotal();
    int normal_orders = 0;
    int emergency_orders = 0;
    int lock_orders = 0;
    
    Print("总订单数: ", total_orders);
    
    for(int i = 0; i < total_orders; i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol())
            {
                string comment = OrderComment();
                if(StringFind(comment, "应急") >= 0)
                {
                    emergency_orders++;
                }
                else if(StringFind(comment, "锁仓") >= 0)
                {
                    lock_orders++;
                }
                else
                {
                    normal_orders++;
                }
            }
        }
    }
    
    Print("普通仓位: ", normal_orders, "/12");
    Print("应急仓位: ", emergency_orders, "/2");
    Print("锁仓单: ", lock_orders, "/2");
    
    // 检查应急仓位触发条件
    bool normal_full = (normal_orders >= 12);
    bool emergency_available = (emergency_orders < 2);
    
    Print("普通仓位已满: ", (normal_full ? "是" : "否"));
    Print("应急仓位可用: ", (emergency_available ? "是" : "否"));
    Print("应急仓位可触发: ", (normal_full && emergency_available ? "是" : "否"));
}

//+------------------------------------------------------------------+
//| 模拟应急仓位触发
//+------------------------------------------------------------------+
void TestEmergencyTrigger()
{
    Print("\n--- 模拟应急仓位触发 ---");
    
    // 检查当前仓位
    int normal_orders = CountNormalOrders();
    int emergency_orders = CountEmergencyOrders();
    
    Print("当前状态:");
    Print("  普通仓位: ", normal_orders, "/12");
    Print("  应急仓位: ", emergency_orders, "/2");
    
    // 模拟反转信号
    double reversal_confidence = 1.258; // 使用日志中的评分
    Print("模拟反转置信度: ", DoubleToString(reversal_confidence, 6));
    
    // 检查触发条件
    bool condition1 = (normal_orders >= 12); // 普通仓位已满
    bool condition2 = (emergency_orders < 2); // 应急仓位未满
    bool condition3 = (reversal_confidence >= 0.8); // 反转信号强度足够
    
    Print("触发条件检查:");
    Print("  条件1(普通仓位已满): ", (condition1 ? "通过" : "未通过"));
    Print("  条件2(应急仓位可用): ", (condition2 ? "通过" : "未通过"));
    Print("  条件3(反转信号强度): ", (condition3 ? "通过" : "未通过"));
    
    bool can_trigger = condition1 && condition2 && condition3;
    Print("应急仓位可触发: ", (can_trigger ? "是" : "否"));
    
    if(can_trigger)
    {
        Print("预期行为: 触发应急仓位建仓");
    }
    else
    {
        Print("预期行为: 不触发应急仓位");
    }
}

//+------------------------------------------------------------------+
//| 简化决策评分计算
//+------------------------------------------------------------------+
void CalculateSimpleScores(double &buy_score, double &sell_score)
{
    // 技术指标
    double ma_fast = iMA(Symbol(), Period(), 15, 0, MODE_SMA, PRICE_CLOSE, 0);
    double ma_slow = iMA(Symbol(), Period(), 30, 0, MODE_SMA, PRICE_CLOSE, 0);
    double rsi = iRSI(Symbol(), Period(), 14, PRICE_CLOSE, 0);
    double macd_main = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
    double macd_signal = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 0);
    
    // 权重设置
    double TechnicalWeight = 0.6;
    double MarketWeight = 0.3;
    double AIWeight = 0.1;
    
    // MA信号
    if(ma_fast > ma_slow)
        buy_score += TechnicalWeight * 0.5;
    else
        sell_score += TechnicalWeight * 0.5;
    
    // RSI信号
    if(rsi < 30)
        buy_score += TechnicalWeight * 0.5;
    else if(rsi > 70)
        sell_score += TechnicalWeight * 0.5;
    
    // MACD信号 (权重100%)
    if(macd_main > macd_signal)
        buy_score += TechnicalWeight * 1.0;
    else
        sell_score += TechnicalWeight * 1.0;
    
    // 市场状态评分
    double market_score = 50.0;
    buy_score += MarketWeight * (market_score / 100.0);
    sell_score += MarketWeight * (market_score / 100.0);
    
    // AI预测评分
    double ai_confidence = 0.5;
    buy_score += AIWeight * ai_confidence;
    sell_score += AIWeight * ai_confidence;
}

//+------------------------------------------------------------------+
//| 统计普通仓位数量
//+------------------------------------------------------------------+
int CountNormalOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol())
            {
                string comment = OrderComment();
                if(StringFind(comment, "应急") < 0 && StringFind(comment, "锁仓") < 0)
                {
                    count++;
                }
            }
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| 统计应急仓位数量
//+------------------------------------------------------------------+
int CountEmergencyOrders()
{
    int count = 0;
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol())
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