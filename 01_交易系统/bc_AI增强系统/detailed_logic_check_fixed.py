#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查EA交易逻辑实现
查看实际的函数实现和逻辑流程
"""

import re
import os

def find_and_show_function(function_name, content):
    """查找并显示函数内容"""
    print("\n🔍 查找函数: " + function_name)
    
    # 尝试不同的函数模式
    patterns = [
        r'bool\s+' + function_name + r'\s*\([^)]*\)\s*\{[^}]*\}',
        r'void\s+' + function_name + r'\s*\([^)]*\)\s*\{[^}]*\}',
        r'int\s+' + function_name + r'\s*\([^)]*\)\s*\{[^}]*\}',
        r'double\s+' + function_name + r'\s*\([^)]*\)\s*\{[^}]*\}',
        r'string\s+' + function_name + r'\s*\([^)]*\)\s*\{[^}]*\}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            print("   ✅ 找到函数: " + function_name)
            func_content = match.group()
            
            # 显示函数的关键部分
            lines = func_content.split('\n')
            print("   📝 函数内容预览:")
            for i, line in enumerate(lines[:10]):  # 只显示前10行
                if line.strip():
                    print(f"      {i+1}: {line.strip()}")
            if len(lines) > 10:
                print(f"      ... 还有 {len(lines) - 10} 行")
            
            return func_content
    
    print("   ❌ 未找到函数: " + function_name)
    return None

def check_execute_trading_logic_details():
    """详细检查ExecuteTradingLogic函数"""
    print("\n🔍 详细检查ExecuteTradingLogic函数...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找ExecuteTradingLogic函数
    execute_logic = re.search(r'void\s+ExecuteTradingLogic\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if execute_logic:
        print("   ✅ 找到ExecuteTradingLogic函数")
        
        logic_content = execute_logic.group()
        lines = logic_content.split('\n')
        
        print("   📝 ExecuteTradingLogic函数内容:")
        for i, line in enumerate(lines):
            if line.strip():
                print(f"      {i+1}: {line.strip()}")
        
        # 检查关键逻辑
        print("\n   🔍 关键逻辑检查:")
        
        # 检查普通仓位逻辑
        if re.search(r'CanPlaceNormalOrder', logic_content):
            print("      ✅ 包含CanPlaceNormalOrder调用")
        else:
            print("      ❌ 缺少CanPlaceNormalOrder调用")
        
        # 检查锁仓逻辑
        if re.search(r'CanPlaceLockOrder', logic_content):
            print("      ✅ 包含CanPlaceLockOrder调用")
        else:
            print("      ❌ 缺少CanPlaceLockOrder调用")
        
        # 检查应急仓位逻辑
        if re.search(r'CanTriggerEmergencyOrder', logic_content):
            print("      ✅ 包含CanTriggerEmergencyOrder调用")
        else:
            print("      ❌ 缺少CanTriggerEmergencyOrder调用")
        
        # 检查反转信号处理
        if re.search(r'has_reversal', logic_content):
            print("      ✅ 包含反转信号检查")
        else:
            print("      ❌ 缺少反转信号检查")
        
        # 检查应急仓位触发
        if re.search(r'EmergencyTriggerScore', logic_content):
            print("      ✅ 包含应急仓位触发评分检查")
        else:
            print("      ❌ 缺少应急仓位触发评分检查")
        
    else:
        print("   ❌ 未找到ExecuteTradingLogic函数")
    
    return True

def check_reversal_signal_implementation():
    """检查反转信号的具体实现"""
    print("\n🔍 检查反转信号的具体实现...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 反转信号实现检查:")
    
    # 检查CheckDecisionReversalClose函数
    reversal_close = find_and_show_function('CheckDecisionReversalClose', content)
    
    # 检查CheckDecisionScoreReversal函数
    reversal_detection = find_and_show_function('CheckDecisionScoreReversal', content)
    
    # 检查反转信号在ExecuteTradingLogic中的使用
    execute_logic = re.search(r'void\s+ExecuteTradingLogic\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if execute_logic:
        logic_content = execute_logic.group()
        
        print("\n🔍 反转信号在ExecuteTradingLogic中的使用:")
        
        # 查找反转信号相关的代码行
        lines = logic_content.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['reversal', '反转', 'CheckDecision']):
                print(f"      {i+1}: {line.strip()}")
    
    return True

def check_emergency_order_implementation():
    """检查应急仓位的具体实现"""
    print("\n🔍 检查应急仓位的具体实现...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 应急仓位实现检查:")
    
    # 检查CanTriggerEmergencyOrder函数
    can_trigger = find_and_show_function('CanTriggerEmergencyOrder', content)
    
    # 检查ExecuteEmergencyOrder函数
    execute_emergency = find_and_show_function('ExecuteEmergencyOrder', content)
    
    # 检查CheckEmergencyOrderClose函数
    emergency_close = find_and_show_function('CheckEmergencyOrderClose', content)
    
    # 检查应急仓位在ExecuteTradingLogic中的使用
    execute_logic = re.search(r'void\s+ExecuteTradingLogic\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if execute_logic:
        logic_content = execute_logic.group()
        
        print("\n🔍 应急仓位在ExecuteTradingLogic中的使用:")
        
        # 查找应急仓位相关的代码行
        lines = logic_content.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['Emergency', '应急', 'emergency']):
                print(f"      {i+1}: {line.strip()}")
    
    return True

def main():
    """主函数"""
    print("🚀 开始详细检查EA交易逻辑实现...")
    print("=" * 60)
    
    # 详细检查ExecuteTradingLogic函数
    check_execute_trading_logic_details()
    
    # 检查反转信号实现
    check_reversal_signal_implementation()
    
    # 检查应急仓位实现
    check_emergency_order_implementation()
    
    print("\n📊 详细检查总结:")
    print("=" * 60)
    print("✅ 详细检查完成！")
    print("请根据上述结果分析实际的逻辑实现情况。")

if __name__ == "__main__":
    main() 