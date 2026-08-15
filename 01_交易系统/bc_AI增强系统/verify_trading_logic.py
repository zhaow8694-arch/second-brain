#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证EA交易逻辑
检查普通仓、锁仓、应急仓的建仓平仓逻辑和反转信号处理
"""

import re
import os

def verify_normal_position_logic():
    """验证普通仓位的建仓平仓逻辑"""
    print("🔍 验证普通仓位的建仓平仓逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 普通仓位逻辑检查:")
    
    # 1. 检查普通仓位建仓条件
    print("\n1️⃣ 普通仓位建仓条件:")
    
    # 检查CanPlaceNormalOrder函数
    can_place_normal = re.search(r'bool\s+CanPlaceNormalOrder\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if can_place_normal:
        print("   ✅ 找到CanPlaceNormalOrder函数")
        
        # 检查建仓条件
        conditions = [
            r'CountNormalOrders\s*\(\s*\)\s*<\s*MaxNormalOrders',
            r'CountOpenOrders\s*\(\s*\)\s*<\s*MaxOpenOrders',
            r'GetCurrentOrderTotalProfit\s*\(\s*\)\s*>\s*-MaxLossThreshold'
        ]
        
        for condition in conditions:
            if re.search(condition, can_place_normal.group()):
                print(f"   ✅ 包含条件: {condition}")
            else:
                print(f"   ⚠️  缺少条件: {condition}")
    else:
        print("   ❌ 未找到CanPlaceNormalOrder函数")
    
    # 2. 检查普通仓位平仓逻辑
    print("\n2️⃣ 普通仓位平仓逻辑:")
    
    # 检查反转信号平仓
    reversal_close = re.search(r'CheckDecisionReversalClose\s*\([^)]*\)', content)
    if reversal_close:
        print("   ✅ 找到反转信号平仓检查")
    else:
        print("   ⚠️  未找到反转信号平仓检查")
    
    # 检查普通仓位的反转信号处理
    normal_reversal = re.search(r'普通仓位.*反转信号.*保持持有', content)
    if normal_reversal:
        print("   ✅ 普通仓位反转信号后保持持有")
    else:
        print("   ⚠️  未找到普通仓位反转信号处理逻辑")
    
    return True

def verify_lock_position_logic():
    """验证锁仓的建仓平仓逻辑"""
    print("\n🔍 验证锁仓的建仓平仓逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 锁仓逻辑检查:")
    
    # 1. 检查锁仓建仓条件
    print("\n1️⃣ 锁仓建仓条件:")
    
    # 检查CanPlaceLockOrder函数
    can_place_lock = re.search(r'bool\s+CanPlaceLockOrder\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if can_place_lock:
        print("   ✅ 找到CanPlaceLockOrder函数")
        
        # 检查锁仓条件
        lock_conditions = [
            r'CountLockOrders\s*\(\s*\)\s*<\s*MaxLockOrders',
            r'GetCurrentOrderTotalProfit\s*\(\s*\)\s*<\s*-LockTriggerThreshold'
        ]
        
        for condition in lock_conditions:
            if re.search(condition, can_place_lock.group()):
                print(f"   ✅ 包含条件: {condition}")
            else:
                print(f"   ⚠️  缺少条件: {condition}")
    else:
        print("   ❌ 未找到CanPlaceLockOrder函数")
    
    # 2. 检查锁仓平仓逻辑
    print("\n2️⃣ 锁仓平仓逻辑:")
    
    # 检查锁仓反转信号处理
    lock_reversal = re.search(r'锁仓单.*反转信号.*不执行平仓.*继续扛单', content)
    if lock_reversal:
        print("   ✅ 锁仓单反转信号后不执行平仓，继续扛单")
    else:
        print("   ⚠️  未找到锁仓单反转信号处理逻辑")
    
    # 检查CLockOrderProtector类
    lock_protector = re.search(r'class\s+CLockOrderProtector\s*\{[^}]*\}', content, re.DOTALL)
    if lock_protector:
        print("   ✅ 找到CLockOrderProtector类")
    else:
        print("   ❌ 未找到CLockOrderProtector类")
    
    return True

def verify_emergency_position_logic():
    """验证应急仓位的建仓平仓逻辑"""
    print("\n🔍 验证应急仓位的建仓平仓逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 应急仓位逻辑检查:")
    
    # 1. 检查应急仓位建仓条件
    print("\n1️⃣ 应急仓位建仓条件:")
    
    # 检查CanTriggerEmergencyOrder函数
    can_trigger_emergency = re.search(r'bool\s+CanTriggerEmergencyOrder\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if can_trigger_emergency:
        print("   ✅ 找到CanTriggerEmergencyOrder函数")
        
        # 检查应急仓位条件
        emergency_conditions = [
            r'CountNormalOrders\s*\(\s*\)\s*>=\s*MaxNormalOrders',
            r'CountEmergencyOrders\s*\(\s*\)\s*<\s*EmergencyOrderCount',
            r'has_reversal_signal',
            r'reversal_confidence\s*>=\s*EmergencyTriggerScore'
        ]
        
        for condition in emergency_conditions:
            if re.search(condition, can_trigger_emergency.group()):
                print(f"   ✅ 包含条件: {condition}")
            else:
                print(f"   ⚠️  缺少条件: {condition}")
    else:
        print("   ❌ 未找到CanTriggerEmergencyOrder函数")
    
    # 2. 检查应急仓位平仓逻辑
    print("\n2️⃣ 应急仓位平仓逻辑:")
    
    # 检查CheckEmergencyOrderClose函数
    emergency_close = re.search(r'bool\s+CheckEmergencyOrderClose\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if emergency_close:
        print("   ✅ 找到CheckEmergencyOrderClose函数")
    else:
        print("   ❌ 未找到CheckEmergencyOrderClose函数")
    
    # 检查应急仓位只给予反转信号
    emergency_reversal_only = re.search(r'应急仓位只给予反转信号', content)
    if emergency_reversal_only:
        print("   ✅ 应急仓位只给予反转信号")
    else:
        print("   ⚠️  未找到应急仓位反转信号限制")
    
    return True

def verify_reversal_signal_logic():
    """验证反转信号的处理逻辑"""
    print("\n🔍 验证反转信号的处理逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 反转信号逻辑检查:")
    
    # 1. 检查反转信号检测
    print("\n1️⃣ 反转信号检测:")
    
    # 检查CheckDecisionScoreReversal函数
    reversal_detection = re.search(r'bool\s+CheckDecisionScoreReversal\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if reversal_detection:
        print("   ✅ 找到CheckDecisionScoreReversal函数")
        
        # 检查反转信号条件
        reversal_conditions = [
            r'DecisionReversalThreshold',
            r'DecisionReversalTicks',
            r'UpdateDecisionReversalHistory'
        ]
        
        for condition in reversal_conditions:
            if re.search(condition, reversal_detection.group()):
                print(f"   ✅ 包含条件: {condition}")
            else:
                print(f"   ⚠️  缺少条件: {condition}")
    else:
        print("   ❌ 未找到CheckDecisionScoreReversal函数")
    
    # 2. 检查反转信号对不同仓位的影响
    print("\n2️⃣ 反转信号对不同仓位的影响:")
    
    # 检查普通仓位反转信号处理
    normal_reversal_effect = re.search(r'普通仓位.*反转信号.*保持持有.*不平仓', content)
    if normal_reversal_effect:
        print("   ✅ 普通仓位：反转信号后保持持有，不平仓")
    else:
        print("   ⚠️  未找到普通仓位反转信号处理")
    
    # 检查锁仓反转信号处理
    lock_reversal_effect = re.search(r'锁仓单.*反转信号.*不执行平仓.*继续扛单', content)
    if lock_reversal_effect:
        print("   ✅ 锁仓单：反转信号后不执行平仓，继续扛单")
    else:
        print("   ⚠️  未找到锁仓单反转信号处理")
    
    # 检查应急仓位反转信号处理
    emergency_reversal_effect = re.search(r'应急仓位.*反转信号.*触发', content)
    if emergency_reversal_effect:
        print("   ✅ 应急仓位：基于反转信号触发")
    else:
        print("   ⚠️  未找到应急仓位反转信号处理")
    
    return True

def verify_execute_trading_logic():
    """验证ExecuteTradingLogic函数中的逻辑"""
    print("\n🔍 验证ExecuteTradingLogic函数中的逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 ExecuteTradingLogic逻辑检查:")
    
    # 查找ExecuteTradingLogic函数
    execute_logic = re.search(r'void\s+ExecuteTradingLogic\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if execute_logic:
        print("   ✅ 找到ExecuteTradingLogic函数")
        
        logic_content = execute_logic.group()
        
        # 检查普通仓位逻辑
        print("\n1️⃣ 普通仓位逻辑:")
        if re.search(r'CanPlaceNormalOrder', logic_content):
            print("   ✅ 包含普通仓位建仓检查")
        else:
            print("   ❌ 缺少普通仓位建仓检查")
        
        # 检查锁仓逻辑
        print("\n2️⃣ 锁仓逻辑:")
        if re.search(r'CanPlaceLockOrder', logic_content):
            print("   ✅ 包含锁仓建仓检查")
        else:
            print("   ❌ 缺少锁仓建仓检查")
        
        # 检查应急仓位逻辑
        print("\n3️⃣ 应急仓位逻辑:")
        if re.search(r'CanTriggerEmergencyOrder', logic_content):
            print("   ✅ 包含应急仓位触发检查")
        else:
            print("   ❌ 缺少应急仓位触发检查")
        
        # 检查反转信号处理
        print("\n4️⃣ 反转信号处理:")
        if re.search(r'has_reversal.*reversal_confidence.*EmergencyTriggerScore', logic_content):
            print("   ✅ 包含反转信号应急仓位触发")
        else:
            print("   ❌ 缺少反转信号应急仓位触发")
        
        # 检查平仓逻辑
        print("\n5️⃣ 平仓逻辑:")
        if re.search(r'CheckDecisionReversalClose', logic_content):
            print("   ✅ 包含反转信号平仓检查")
        else:
            print("   ❌ 缺少反转信号平仓检查")
        
        if re.search(r'CheckEmergencyOrderClose', logic_content):
            print("   ✅ 包含应急仓位平仓检查")
        else:
            print("   ❌ 缺少应急仓位平仓检查")
        
    else:
        print("   ❌ 未找到ExecuteTradingLogic函数")
    
    return True

def verify_parameter_settings():
    """验证相关参数设置"""
    print("\n🔍 验证相关参数设置...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 参数设置检查:")
    
    # 检查关键参数
    key_parameters = [
        ('MaxNormalOrders', '普通仓位最大数量'),
        ('MaxLockOrders', '锁仓最大数量'),
        ('EmergencyOrderCount', '应急仓位最大数量'),
        ('EmergencyTriggerScore', '应急仓位触发评分'),
        ('DecisionReversalThreshold', '反转信号阈值'),
        ('DecisionReversalTicks', '反转信号确认tick数'),
        ('LockTriggerThreshold', '锁仓触发阈值')
    ]
    
    for param, description in key_parameters:
        if re.search(rf'input\s+\w+\s+{param}\s*=', content):
            print(f"   ✅ {param}: {description}")
        else:
            print(f"   ❌ {param}: {description} - 未找到")
    
    return True

def main():
    """主函数"""
    print("🚀 开始验证EA交易逻辑...")
    print("=" * 60)
    
    # 验证普通仓位逻辑
    verify_normal_position_logic()
    
    # 验证锁仓逻辑
    verify_lock_position_logic()
    
    # 验证应急仓位逻辑
    verify_emergency_position_logic()
    
    # 验证反转信号逻辑
    verify_reversal_signal_logic()
    
    # 验证ExecuteTradingLogic函数
    verify_execute_trading_logic()
    
    # 验证参数设置
    verify_parameter_settings()
    
    print("\n📊 验证总结:")
    print("=" * 60)
    print("✅ 交易逻辑验证完成！")
    print("请检查上述结果，确保所有逻辑都正确实现。")

if __name__ == "__main__":
    main() 