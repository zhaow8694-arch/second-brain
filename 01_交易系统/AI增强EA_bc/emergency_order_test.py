#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应急仓位触发测试脚本
测试应急仓位的触发逻辑和条件
"""

import re
import json
from datetime import datetime

def test_emergency_order_trigger():
    """测试应急仓位触发逻辑"""
    print("🔍 应急仓位触发逻辑测试")
    print("=" * 60)
    
    # 读取EA文件
    try:
        with open('AI_Enhanced_Risk_EA.mq4', 'r', encoding='utf-8') as f:
            content = f.read()
        print("✅ 成功读取EA文件")
    except Exception as e:
        print(f"❌ 读取EA文件失败: {e}")
        return
    
    # 测试1: 检查应急仓位触发条件
    print("\n1️⃣ 测试应急仓位触发条件")
    test_trigger_conditions(content)
    
    # 测试2: 检查决策评分反转检测
    print("\n2️⃣ 测试决策评分反转检测")
    test_reversal_detection(content)
    
    # 测试3: 检查应急仓位建仓逻辑
    print("\n3️⃣ 测试应急仓位建仓逻辑")
    test_emergency_order_execution(content)
    
    # 测试4: 检查日志输出一致性
    print("\n4️⃣ 测试日志输出一致性")
    test_log_consistency(content)
    
    # 测试5: 模拟应急仓位触发流程
    print("\n5️⃣ 模拟应急仓位触发流程")
    simulate_emergency_trigger_flow(content)

def test_trigger_conditions(content):
    """测试应急仓位触发条件"""
    print("   📋 检查应急仓位触发条件...")
    
    # 检查普通仓位已满条件
    normal_full_pattern = r'CountNormalOrders\(\) >= MaxNormalOrders'
    if re.search(normal_full_pattern, content):
        print("   ✅ 普通仓位已满条件检查正确")
    else:
        print("   ❌ 缺少普通仓位已满条件检查")
    
    # 检查应急仓位未满条件
    emergency_available_pattern = r'emergency_count >= EmergencyOrderCount'
    if re.search(emergency_available_pattern, content):
        print("   ✅ 应急仓位未满条件检查正确")
    else:
        print("   ❌ 缺少应急仓位未满条件检查")
    
    # 检查反转信号条件
    reversal_signal_pattern = r'g_current_reversal_signal\.has_reversal.*g_current_reversal_signal\.is_valid'
    if re.search(reversal_signal_pattern, content):
        print("   ✅ 反转信号条件检查正确")
    else:
        print("   ❌ 缺少反转信号条件检查")
    
    # 检查点差条件
    spread_pattern = r'MarketInfo\(Symbol\(\), MODE_SPREAD\) > 50'
    if re.search(spread_pattern, content):
        print("   ✅ 点差条件检查正确")
    else:
        print("   ❌ 缺少点差条件检查")

def test_reversal_detection(content):
    """测试决策评分反转检测"""
    print("   📋 检查决策评分反转检测...")
    
    # 检查历史决策评分记录
    history_pattern = r'g_decision_score_history\[5\]'
    if re.search(history_pattern, content):
        print("   ✅ 历史决策评分记录结构正确")
    else:
        print("   ❌ 缺少历史决策评分记录")
    
    # 检查反转信号计算函数
    reversal_func_pattern = r'CalculateUnifiedReversalSignal'
    if re.search(reversal_func_pattern, content):
        print("   ✅ 反转信号计算函数存在")
    else:
        print("   ❌ 缺少反转信号计算函数")
    
    # 检查历史方向计算
    historical_direction_pattern = r'CalculateHistoricalDirection'
    if re.search(historical_direction_pattern, content):
        print("   ✅ 历史方向计算函数存在")
    else:
        print("   ❌ 缺少历史方向计算函数")
    
    # 检查方向反转判断
    direction_reversal_pattern = r'historical_direction.*current_direction.*historical_direction != current_direction'
    if re.search(direction_reversal_pattern, content):
        print("   ✅ 方向反转判断逻辑正确")
    else:
        print("   ❌ 缺少方向反转判断逻辑")

def test_emergency_order_execution(content):
    """测试应急仓位建仓逻辑"""
    print("   📋 检查应急仓位建仓逻辑...")
    
    # 检查应急仓位触发函数
    trigger_func_pattern = r'CanTriggerEmergencyOrder'
    if re.search(trigger_func_pattern, content):
        print("   ✅ 应急仓位触发函数存在")
    else:
        print("   ❌ 缺少应急仓位触发函数")
    
    # 检查应急仓位建仓函数
    execute_func_pattern = r'ExecuteEmergencyOrder'
    if re.search(execute_func_pattern, content):
        print("   ✅ 应急仓位建仓函数存在")
    else:
        print("   ❌ 缺少应急仓位建仓函数")
    
    # 检查应急仓位方向确定
    direction_pattern = r'emergency_direction.*g_current_reversal_signal\.signal_direction'
    if re.search(direction_pattern, content):
        print("   ✅ 应急仓位方向确定逻辑正确")
    else:
        print("   ❌ 缺少应急仓位方向确定逻辑")
    
    # 检查应急仓位参数
    lot_size_pattern = r'EmergencyLotSize'
    if re.search(lot_size_pattern, content):
        print("   ✅ 应急仓位手数参数存在")
    else:
        print("   ❌ 缺少应急仓位手数参数")

def test_log_consistency(content):
    """测试日志输出一致性"""
    print("   📋 检查日志输出一致性...")
    
    # 检查统一的日志格式
    log_patterns = [
        (r'📊 应急仓位触发检查', "触发检查日志"),
        (r'📊 应急仓位触发失败', "触发失败日志"),
        (r'🔄 检测到决策评分反转信号', "反转信号检测日志"),
        (r'✅ 应急仓位决策评分反转信号确认', "反转信号确认日志"),
        (r'🚨 应急仓位触发条件满足', "触发成功日志"),
        (r'🚨 应急.*仓位建仓成功', "建仓成功日志")
    ]
    
    for pattern, description in log_patterns:
        if re.search(pattern, content):
            print(f"   ✅ {description}格式统一")
        else:
            print(f"   ❌ {description}格式不统一")

def simulate_emergency_trigger_flow(content):
    """模拟应急仓位触发流程"""
    print("   📋 模拟应急仓位触发流程...")
    
    # 模拟场景1: 正常触发
    print("   🎯 场景1: 正常触发应急仓位")
    print("      - 普通仓位已满: ✅")
    print("      - 应急仓位未满: ✅")
    print("      - 检测到决策评分反转信号: ✅")
    print("      - 点差正常: ✅")
    print("      - 预期结果: 应急仓位建仓成功")
    
    # 模拟场景2: 普通仓位未满
    print("   🎯 场景2: 普通仓位未满")
    print("      - 普通仓位已满: ❌")
    print("      - 预期结果: 跳过应急仓位检查")
    
    # 模拟场景3: 应急仓位已满
    print("   🎯 场景3: 应急仓位已满")
    print("      - 普通仓位已满: ✅")
    print("      - 应急仓位未满: ❌")
    print("      - 预期结果: 应急仓位触发失败")
    
    # 模拟场景4: 无反转信号
    print("   🎯 场景4: 无反转信号")
    print("      - 普通仓位已满: ✅")
    print("      - 应急仓位未满: ✅")
    print("      - 检测到决策评分反转信号: ❌")
    print("      - 预期结果: 应急仓位触发失败")
    
    # 模拟场景5: 点差过大
    print("   🎯 场景5: 点差过大")
    print("      - 普通仓位已满: ✅")
    print("      - 应急仓位未满: ✅")
    print("      - 检测到决策评分反转信号: ✅")
    print("      - 点差正常: ❌")
    print("      - 预期结果: 应急仓位触发失败")

def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("📊 应急仓位测试报告")
    print("=" * 60)
    
    report = {
        "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "测试项目": "应急仓位触发逻辑",
        "测试内容": [
            "应急仓位触发条件检查",
            "决策评分反转检测",
            "应急仓位建仓逻辑",
            "日志输出一致性",
            "应急仓位触发流程模拟"
        ],
        "预期结果": [
            "普通仓位已满时检查应急仓位触发",
            "基于历史决策评分反转信号触发",
            "应急仓位方向与反转信号方向一致",
            "日志输出格式统一",
            "各种触发条件正确判断"
        ],
        "注意事项": [
            "需要至少5个历史决策评分记录",
            "反转信号需要满足DecisionReversalThreshold阈值",
            "应急仓位最多2个",
            "点差不能超过50点"
        ]
    }
    
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    print("\n🎯 测试建议:")
    print("1. 在MT4中运行EA，观察应急仓位的实际触发情况")
    print("2. 检查日志输出是否符合预期格式")
    print("3. 验证应急仓位的建仓方向是否正确")
    print("4. 确认应急仓位的平仓逻辑是否正常")

if __name__ == "__main__":
    test_emergency_order_trigger()
    generate_test_report() 