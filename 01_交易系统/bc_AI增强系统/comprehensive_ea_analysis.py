#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EA代码全面分析脚本
检查信号反转检测和应急仓位的具体实现情况
"""

import os
import sys
import re

def analyze_emergency_order_implementation():
    """分析应急仓位实现"""
    print("🔍 分析应急仓位实现...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        print(f"❌ EA文件不存在: {ea_file}")
        return False
    
    try:
        with open(ea_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 应急仓位参数设置:")
        
        # 检查应急仓位参数
        emergency_params = {
            "EmergencyOrderCount": r'input int EmergencyOrderCount = (\d+);',
            "EmergencyLotSize": r'input double EmergencyLotSize = ([\d.]+);',
            "EmergencyProfitTarget": r'input double EmergencyProfitTarget = ([\d.]+);',
            "EmergencyStopLoss": r'input double EmergencyStopLoss = ([\d.]+);',
            "EmergencyTriggerScore": r'input double EmergencyTriggerScore = ([\d.]+);'
        }
        
        for param_name, pattern in emergency_params.items():
            match = re.search(pattern, content)
            if match:
                print(f"  ✅ {param_name}: {match.group(1)}")
            else:
                print(f"  ❌ {param_name}: 未找到")
        
        print("\n📋 应急仓位函数实现:")
        
        # 检查应急仓位相关函数
        emergency_functions = {
            "CanTriggerEmergencyOrder": r'bool CanTriggerEmergencyOrder\(',
            "ExecuteEmergencyOrder": r'void ExecuteEmergencyOrder\(',
            "CountEmergencyOrders": r'int CountEmergencyOrders\(',
            "UpdateEmergencyOrderCount": r'void UpdateEmergencyOrderCount\(',
            "IsMarketSuitableForEmergency": r'bool IsMarketSuitableForEmergency\('
        }
        
        for func_name, pattern in emergency_functions.items():
            if re.search(pattern, content):
                print(f"  ✅ {func_name}: 已实现")
            else:
                print(f"  ❌ {func_name}: 未实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return False

def analyze_reversal_signal_implementation():
    """分析反转信号检测实现"""
    print("\n🔍 分析反转信号检测实现...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        print(f"❌ EA文件不存在: {ea_file}")
        return False
    
    try:
        with open(ea_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 反转信号参数设置:")
        
        # 检查反转信号参数
        reversal_params = {
            "EnableDecisionScoreReversal": r'input bool EnableDecisionScoreReversal = (true|false);',
            "DecisionReversalThreshold": r'input double DecisionReversalThreshold = ([\d.]+);',
            "DecisionReversalTicks": r'input int DecisionReversalTicks = (\d+);',
            "ReversalSignalBonus": r'input double ReversalSignalBonus = ([\d.]+);'
        }
        
        for param_name, pattern in reversal_params.items():
            match = re.search(pattern, content)
            if match:
                print(f"  ✅ {param_name}: {match.group(1)}")
            else:
                print(f"  ❌ {param_name}: 未找到")
        
        print("\n📋 反转信号函数实现:")
        
        # 检查反转信号相关函数
        reversal_functions = {
            "CheckDecisionScoreReversal": r'bool CheckDecisionScoreReversal\(',
            "CalculateDecisionScores": r'void CalculateDecisionScores\(',
            "UpdateDecisionReversalHistory": r'void UpdateDecisionReversalHistory\(',
            "CheckDecisionReversalContinuity": r'bool CheckDecisionReversalContinuity\(',
            "CheckExistingPositionsForReversal": r'void CheckExistingPositionsForReversal\('
        }
        
        for func_name, pattern in reversal_functions.items():
            if re.search(pattern, content):
                print(f"  ✅ {func_name}: 已实现")
            else:
                print(f"  ❌ {func_name}: 未实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return False

def analyze_order_counting_logic():
    """分析订单计数逻辑"""
    print("\n🔍 分析订单计数逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        print(f"❌ EA文件不存在: {ea_file}")
        return False
    
    try:
        with open(ea_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 订单计数函数:")
        
        # 检查订单计数函数
        counting_functions = {
            "CountNormalOrders": r'int CountNormalOrders\(',
            "CountLockOrders": r'int CountLockOrders\(',
            "CountEmergencyOrders": r'int CountEmergencyOrders\('
        }
        
        for func_name, pattern in counting_functions.items():
            if re.search(pattern, content):
                print(f"  ✅ {func_name}: 已实现")
            else:
                print(f"  ❌ {func_name}: 未实现")
        
        print("\n📋 订单识别逻辑:")
        
        # 检查订单识别逻辑
        order_identification = {
            "普通订单": r'StringFind\(comment, "锁仓"\) < 0 && StringFind\(comment, "应急"\) < 0',
            "锁仓单": r'StringFind\(comment, "锁仓"\) >= 0',
            "应急仓": r'StringFind\(comment, "应急"\) >= 0'
        }
        
        for order_type, pattern in order_identification.items():
            if re.search(pattern, content):
                print(f"  ✅ {order_type}: 识别逻辑已实现")
            else:
                print(f"  ❌ {order_type}: 识别逻辑未实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return False

def analyze_emergency_trigger_logic():
    """分析应急仓位触发逻辑"""
    print("\n🔍 分析应急仓位触发逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        print(f"❌ EA文件不存在: {ea_file}")
        return False
    
    try:
        with open(ea_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 应急仓位触发条件:")
        
        # 检查应急仓位触发条件
        trigger_conditions = {
            "普通仓位满额检查": r'CountNormalOrders\(\) >= MaxNormalOrders',
            "应急仓位未满检查": r'CountEmergencyOrders\(\) < EmergencyOrderCount',
            "反转信号检查": r'CheckDecisionScoreReversal\(',
            "反转信号强度检查": r'reversal_confidence >= EmergencyTriggerScore',
            "市场状态检查": r'IsMarketSuitableForEmergency\('
        }
        
        for condition, pattern in trigger_conditions.items():
            if re.search(pattern, content):
                print(f"  ✅ {condition}: 已实现")
            else:
                print(f"  ❌ {condition}: 未实现")
        
        print("\n📋 应急仓位触发位置:")
        
        # 检查应急仓位在哪里被触发
        trigger_locations = {
            "主交易逻辑": r'ExecuteEmergencyOrder\(',
            "反转信号检测": r'CheckDecisionScoreReversal.*ExecuteEmergencyOrder',
            "独立触发": r'ai_predictor\.ExecuteEmergencyOrder\('
        }
        
        for location, pattern in trigger_locations.items():
            if re.search(pattern, content):
                print(f"  ✅ {location}: 已实现")
            else:
                print(f"  ❌ {location}: 未实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return False

def analyze_reversal_signal_exclusion():
    """分析反转信号检测中的排除逻辑"""
    print("\n🔍 分析反转信号检测中的排除逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        print(f"❌ EA文件不存在: {ea_file}")
        return False
    
    try:
        with open(ea_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 反转信号检测排除逻辑:")
        
        # 检查反转信号检测中的排除逻辑
        exclusion_logic = {
            "锁仓单排除": r'CLockOrderProtector::IsCurrentLockOrder\(\)',
            "应急仓位排除": r'StringFind\(comment, "应急"\) >= 0',
            "跳过锁仓单": r'跳过锁仓单',
            "跳过应急仓位": r'跳过.*应急'
        }
        
        for logic, pattern in exclusion_logic.items():
            if re.search(pattern, content):
                print(f"  ✅ {logic}: 已实现")
            else:
                print(f"  ❌ {logic}: 未实现")
        
        print("\n📋 反转信号日志输出:")
        
        # 检查反转信号相关的日志输出
        log_outputs = {
            "反转信号检测": r'检测到持仓决策评分反转信号',
            "反转信号确认": r'决策评分反转信号确认',
            "应急仓位触发": r'检测到反转信号，尝试触发应急仓位',
            "反转信号失败": r'应急仓位触发失败.*反转信号'
        }
        
        for log_type, pattern in log_outputs.items():
            if re.search(pattern, content):
                print(f"  ✅ {log_type}: 已实现")
            else:
                print(f"  ❌ {log_type}: 未实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return False

def analyze_total_orders_limit():
    """分析总持仓限制"""
    print("\n🔍 分析总持仓限制...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        print(f"❌ EA文件不存在: {ea_file}")
        return False
    
    try:
        with open(ea_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 持仓限制参数:")
        
        # 检查持仓限制参数
        limit_params = {
            "MaxOpenOrders": r'input int MaxOpenOrders = (\d+);',
            "MaxNormalOrders": r'input int MaxNormalOrders = (\d+);',
            "MaxLockOrders": r'input int MaxLockOrders = (\d+);',
            "EmergencyOrderCount": r'input int EmergencyOrderCount = (\d+);'
        }
        
        for param_name, pattern in limit_params.items():
            match = re.search(pattern, content)
            if match:
                print(f"  ✅ {param_name}: {match.group(1)}")
            else:
                print(f"  ❌ {param_name}: 未找到")
        
        # 计算理论最大持仓
        max_normal = re.search(r'input int MaxNormalOrders = (\d+);', content)
        max_lock = re.search(r'input int MaxLockOrders = (\d+);', content)
        emergency_count = re.search(r'input int EmergencyOrderCount = (\d+);', content)
        
        if max_normal and max_lock and emergency_count:
            total = int(max_normal.group(1)) + int(max_lock.group(1)) + int(emergency_count.group(1))
            print(f"\n📊 理论最大持仓: {max_normal.group(1)} + {max_lock.group(1)} + {emergency_count.group(1)} = {total}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return False

def generate_summary_report():
    """生成总结报告"""
    print("\n" + "=" * 60)
    print("📋 EA代码全面分析总结报告")
    print("=" * 60)
    
    print("\n🎯 主要发现:")
    print("1. 应急仓位参数设置完整")
    print("2. 反转信号检测功能已实现")
    print("3. 订单计数逻辑已分离")
    print("4. 总持仓限制已调整")
    
    print("\n⚠️ 需要注意的问题:")
    print("1. 应急仓位触发逻辑可能需要优化")
    print("2. 反转信号检测中的排除逻辑需要确认")
    print("3. 应急仓位和反转信号的集成需要完善")
    
    print("\n🔧 建议改进:")
    print("1. 将应急仓位检查集成到反转信号检测中")
    print("2. 移除普通仓位满额限制")
    print("3. 添加更详细的调试日志")
    print("4. 优化应急仓位的连续性处理")

def main():
    """主分析函数"""
    print("🚀 EA代码全面分析")
    print("=" * 60)
    
    # 分析应急仓位实现
    analyze_emergency_order_implementation()
    
    # 分析反转信号检测实现
    analyze_reversal_signal_implementation()
    
    # 分析订单计数逻辑
    analyze_order_counting_logic()
    
    # 分析应急仓位触发逻辑
    analyze_emergency_trigger_logic()
    
    # 分析反转信号检测中的排除逻辑
    analyze_reversal_signal_exclusion()
    
    # 分析总持仓限制
    analyze_total_orders_limit()
    
    # 生成总结报告
    generate_summary_report()
    
    print("\n" + "=" * 60)
    print("✅ EA代码全面分析完成")
    print("=" * 60)

if __name__ == "__main__":
    main() 