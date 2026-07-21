#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找交易函数的具体实现位置
"""

import re
import os

def find_function_implementations():
    """查找交易函数的具体实现"""
    print("🔍 查找交易函数的具体实现位置...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 要查找的交易函数
    trading_functions = [
        'CanPlaceNormalOrder',
        'CanPlaceLockOrder', 
        'ExecuteLockOrder',
        'CanTriggerEmergencyOrder',
        'ExecuteEmergencyOrder',
        'CheckDecisionReversalClose',
        'CheckEmergencyOrderClose'
    ]
    
    print(f"\n📋 交易函数实现位置:")
    
    for func_name in trading_functions:
        print(f"\n🔍 查找函数: {func_name}")
        
        # 查找函数定义
        func_pattern = r'(?:bool|void|int)\s+' + func_name + r'\s*\([^)]*\)\s*\{[^}]*\}'
        matches = re.findall(func_pattern, content, re.DOTALL)
        
        if matches:
            print(f"   ✅ 找到 {len(matches)} 个实现:")
            for i, match in enumerate(matches):
                print(f"      {i+1}. 实现 {i+1}:")
                
                # 显示函数的前几行
                lines = match.split('\n')
                for j, line in enumerate(lines[:10]):  # 只显示前10行
                    if line.strip():
                        print(f"         {j+1}: {line.strip()}")
                if len(lines) > 10:
                    print(f"         ... 还有 {len(lines) - 10} 行")
                
                # 查找函数在文件中的位置
                start_pos = content.find(match)
                if start_pos != -1:
                    line_num = content[:start_pos].count('\n') + 1
                    print(f"         位置: 第 {line_num} 行")
        else:
            print(f"   ❌ 未找到实现")
    
    return True

def find_function_calls():
    """查找函数的调用位置"""
    print(f"\n🔍 查找函数的调用位置...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 要查找的函数调用
    function_calls = [
        'CanPlaceNormalOrder()',
        'CanPlaceLockOrder()',
        'ExecuteLockOrder',
        'CanTriggerEmergencyOrder',
        'ExecuteEmergencyOrder',
        'CheckDecisionReversalClose',
        'CheckEmergencyOrderClose'
    ]
    
    print(f"\n📋 函数调用位置:")
    
    for call in function_calls:
        print(f"\n🔍 查找调用: {call}")
        
        # 查找所有调用
        lines = content.split('\n')
        found_calls = []
        
        for i, line in enumerate(lines):
            if call in line:
                found_calls.append((i+1, line.strip()))
        
        if found_calls:
            print(f"   ✅ 找到 {len(found_calls)} 次调用:")
            for line_num, line_content in found_calls:
                print(f"      行 {line_num}: {line_content}")
        else:
            print(f"   ❌ 未找到调用")
    
    return True

def check_on_tick_complete_logic():
    """检查OnTick函数的完整逻辑"""
    print(f"\n🔍 检查OnTick函数的完整逻辑...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找OnTick函数
    ontick = re.search(r'void\s+OnTick\s*\([^)]*\)\s*\{[^}]*\}', content, re.DOTALL)
    if ontick:
        print("   ✅ 找到OnTick函数")
        
        ontick_content = ontick.group()
        lines = ontick_content.split('\n')
        
        print(f"\n📋 OnTick函数完整内容:")
        print("=" * 60)
        for i, line in enumerate(lines):
            if line.strip():
                print(f"{i+1:3d}: {line}")
        print("=" * 60)
        
        # 检查是否包含交易逻辑
        trading_keywords = [
            'CanPlaceNormalOrder', 'CanPlaceLockOrder', 'ExecuteLockOrder',
            'CanTriggerEmergencyOrder', 'ExecuteEmergencyOrder', 'OrderSend',
            'CheckDecisionReversalClose', 'CheckEmergencyOrderClose'
        ]
        
        print(f"\n🔍 OnTick中的交易逻辑检查:")
        found_keywords = []
        for keyword in trading_keywords:
            if keyword in ontick_content:
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"   ✅ 包含交易逻辑: {found_keywords}")
        else:
            print(f"   ⚠️  未发现交易逻辑")
            
            # 查找OnTick中调用的所有函数
            print(f"\n🔍 OnTick中调用的函数:")
            function_calls = re.findall(r'(\w+)\s*\.\s*(\w+)\s*\([^)]*\)', ontick_content)
            if function_calls:
                for obj, func in function_calls:
                    print(f"      - {obj}.{func}()")
            
            direct_calls = re.findall(r'(\w+)\s*\([^)]*\)', ontick_content)
            if direct_calls:
                for func in direct_calls:
                    if func not in ['if', 'for', 'while', 'switch', 'OnTick']:
                        print(f"      - {func}()")
    
    return True

def main():
    """主函数"""
    print("🚀 开始查找交易函数的具体实现位置...")
    print("=" * 60)
    
    # 查找函数实现
    find_function_implementations()
    
    # 查找函数调用
    find_function_calls()
    
    # 检查OnTick完整逻辑
    check_on_tick_complete_logic()
    
    print("\n📊 查找总结:")
    print("=" * 60)
    print("✅ 查找完成！")
    print("请根据上述结果分析交易逻辑的实际实现情况。")

if __name__ == "__main__":
    main() 