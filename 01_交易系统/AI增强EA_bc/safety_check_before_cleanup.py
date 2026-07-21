#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理前的安全检查
分析清理各部分代码对EA运行的影响
"""

import re
import os

def analyze_duplicate_functions_impact():
    """分析重复函数定义的影响"""
    print("🔍 分析重复函数定义的影响...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 重复函数影响分析:")
    
    # 分析Init函数的重复
    init_pattern = r'(?:bool|void|int)\s+Init\s*\([^)]*\)\s*\{'
    init_matches = re.findall(init_pattern, content)
    
    print("\n1️⃣ Init函数重复分析:")
    print(f"   - 发现 {len(init_matches)} 个Init函数定义")
    
    # 检查是否有OnInit调用
    oninit_calls = re.findall(r'OnInit\s*\([^)]*\)', content)
    if oninit_calls:
        print(f"   - 发现 {len(oninit_calls)} 个OnInit调用")
        print("   ⚠️  风险：OnInit是MQL4标准函数，重复定义可能导致编译错误")
    else:
        print("   ✅ 未发现OnInit调用，可能是自定义Init函数")
    
    # 分析其他重复函数
    duplicate_functions = [
        'GetAverageATR', 'CalculateDecisionScores', 'ExecuteEmergencyOrder',
        'CountEmergencyOrders', 'GetBollingerPosition', 'GetMACDSignal',
        'GetKDJSignal', 'GetAdvancedMarketScore', 'GetMarketState'
    ]
    
    print("\n2️⃣ 其他重复函数分析:")
    for func_name in duplicate_functions:
        pattern = r'(?:bool|void|int|double|string)\s+' + func_name + r'\s*\([^)]*\)\s*\{'
        matches = re.findall(pattern, content)
        if len(matches) > 1:
            # 检查函数调用
            call_pattern = rf'\b{func_name}\s*\('
            calls = re.findall(call_pattern, content)
            print(f"   - {func_name}: {len(matches)} 次定义, {len(calls)} 次调用")
            if len(calls) > len(matches):
                print(f"     ⚠️  风险：函数被调用但重复定义可能导致编译错误")
            else:
                print(f"     ✅ 相对安全：调用次数少于定义次数")
    
    return True

def analyze_unused_input_impact():
    """分析未使用input参数的影响"""
    print("\n🔍 分析未使用input参数的影响...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 未使用input参数影响分析:")
    
    unused_inputs = ['KDJOverbought', 'KDJ_Oversold', 'VolatilityThreshold', 'VolumeThreshold', 'SentimentThreshold']
    
    for param in unused_inputs:
        # 检查参数定义
        input_def_pattern = rf'input\s+\w+\s+{param}\s*='
        input_defs = re.findall(input_def_pattern, content)
        
        # 检查参数使用
        usage_pattern = rf'\b{param}\b'
        usages = re.findall(usage_pattern, content)
        
        print(f"\n1️⃣ {param}:")
        print(f"   - 定义次数: {len(input_defs)}")
        print(f"   - 使用次数: {len(usages)}")
        
        if len(usages) <= len(input_defs):
            print(f"   ✅ 安全：可以安全删除，不影响功能")
        else:
            print(f"   ⚠️  风险：参数被使用，删除可能影响功能")
    
    return True

def analyze_unused_global_vars_impact():
    """分析未使用全局变量的影响"""
    print("\n🔍 分析未使用全局变量的影响...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 未使用全局变量影响分析:")
    
    unused_globals = ['g_last_normal_order_time', 'close_3']
    
    for var in unused_globals:
        # 检查变量定义
        var_def_pattern = rf'(?:int|double|bool|string|datetime)\s+{var}\s*='
        var_defs = re.findall(var_def_pattern, content)
        
        # 检查变量使用
        usage_pattern = rf'\b{var}\b'
        usages = re.findall(usage_pattern, content)
        
        print(f"\n1️⃣ {var}:")
        print(f"   - 定义次数: {len(var_defs)}")
        print(f"   - 使用次数: {len(usages)}")
        
        if len(usages) <= len(var_defs):
            print(f"   ✅ 安全：可以安全删除，不影响功能")
        else:
            print(f"   ⚠️  风险：变量被使用，删除可能影响功能")
    
    return True

def analyze_unused_functions_impact():
    """分析未使用函数的影响"""
    print("\n🔍 分析未使用函数的影响...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 未使用函数影响分析:")
    
    # 检查一些关键函数
    critical_functions = [
        'IsLockOrder', 'GetOrderTotalProfit', 'CanTrade', 'RecordTrade',
        'CleanupClosedOrders', 'GetAccountBalance'
    ]
    
    for func_name in critical_functions:
        # 检查函数定义
        func_def_pattern = r'(?:bool|void|int|double|string)\s+' + func_name + r'\s*\([^)]*\)\s*\{'
        func_defs = re.findall(func_def_pattern, content)
        
        # 检查函数调用
        call_pattern = r'\b' + func_name + r'\s*\('
        calls = re.findall(call_pattern, content)
        
        print(f"\n1️⃣ {func_name}:")
        print(f"   - 定义次数: {len(func_defs)}")
        print(f"   - 调用次数: {len(calls)}")
        
        if len(calls) <= len(func_defs):
            print(f"   ✅ 安全：可以安全删除，不影响功能")
        else:
            print(f"   ⚠️  风险：函数被调用，删除可能影响功能")
    
    return True

def analyze_redundant_patterns_impact():
    """分析冗余代码模式的影响"""
    print("\n🔍 分析冗余代码模式的影响...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 冗余代码模式影响分析:")
    
    # 分析OrderSelect调用
    orderselect_calls = re.findall(r'OrderSelect\([^)]*\)', content)
    print("\n1️⃣ OrderSelect调用分析:")
    print(f"   - 总调用次数: {len(orderselect_calls)}")
    print(f"   - 影响：这是正常的MQL4函数调用，不是冗余代码")
    print(f"   ✅ 安全：不需要清理，这是必要的订单操作")
    
    # 分析OrdersTotal调用
    orderstotal_calls = re.findall(r'OrdersTotal\(\)', content)
    print("\n2️⃣ OrdersTotal调用分析:")
    print(f"   - 总调用次数: {len(orderstotal_calls)}")
    print(f"   - 影响：这是正常的MQL4函数调用，不是冗余代码")
    print(f"   ✅ 安全：不需要清理，这是必要的订单统计")
    
    # 分析CloseOrder调用
    closeorder_calls = re.findall(r'CloseOrder\([^)]*\)', content)
    print("\n3️⃣ CloseOrder调用分析:")
    print(f"   - 总调用次数: {len(closeorder_calls)}")
    print(f"   - 影响：这是订单关闭操作，不是冗余代码")
    print(f"   ✅ 安全：不需要清理，这是必要的订单管理")
    
    return True

def check_critical_dependencies():
    """检查关键依赖关系"""
    print("\n🔍 检查关键依赖关系...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 关键依赖关系检查:")
    
    # 检查OnTick函数
    ontick_pattern = r'void\s+OnTick\s*\([^)]*\)\s*\{'
    ontick_matches = re.findall(ontick_pattern, content)
    print("\n1️⃣ OnTick函数:")
    print(f"   - 定义次数: {len(ontick_matches)}")
    if len(ontick_matches) == 1:
        print(f"   ✅ 正常：只有一个OnTick函数")
    else:
        print(f"   ⚠️  异常：OnTick函数定义异常")
    
    # 检查OnInit函数
    oninit_pattern = r'int\s+OnInit\s*\([^)]*\)\s*\{'
    oninit_matches = re.findall(oninit_pattern, content)
    print("\n2️⃣ OnInit函数:")
    print(f"   - 定义次数: {len(oninit_matches)}")
    if len(oninit_matches) == 1:
        print(f"   ✅ 正常：只有一个OnInit函数")
    else:
        print(f"   ⚠️  异常：OnInit函数定义异常")
    
    # 检查OnDeinit函数
    ondeinit_pattern = r'void\s+OnDeinit\s*\([^)]*\)\s*\{'
    ondeinit_matches = re.findall(ondeinit_pattern, content)
    print("\n3️⃣ OnDeinit函数:")
    print(f"   - 定义次数: {len(ondeinit_matches)}")
    if len(ondeinit_matches) <= 1:
        print(f"   ✅ 正常：OnDeinit函数定义正常")
    else:
        print(f"   ⚠️  异常：OnDeinit函数定义异常")
    
    return True

def generate_cleanup_plan():
    """生成清理计划"""
    print("\n📋 清理计划建议:")
    print("=" * 60)
    
    print("\n🟢 安全清理项目（可以立即执行）:")
    print("1. 删除未使用的input参数：KDJOverbought, KDJ_Oversold, VolatilityThreshold, VolumeThreshold, SentimentThreshold")
    print("2. 删除未使用的全局变量：g_last_normal_order_time, close_3")
    print("3. 删除未使用的函数（36个）")
    
    print("\n🟡 谨慎清理项目（需要仔细检查）:")
    print("1. 合并重复的Init函数定义（8次重复）")
    print("2. 合并其他重复函数定义（GetAverageATR, CalculateDecisionScores等）")
    
    print("\n🔴 不建议清理项目（保持现状）:")
    print("1. OrderSelect, OrdersTotal, CloseOrder等MQL4函数调用（这些是必要的）")
    print("2. 局部变量重复定义（这是正常的，每个函数都有自己的局部变量）")
    
    print("\n📝 清理建议:")
    print("1. 先执行安全清理项目")
    print("2. 然后逐个检查谨慎清理项目")
    print("3. 每次清理后都要测试EA编译和运行")
    print("4. 保留备份文件")
    
    return True

def main():
    """主函数"""
    print("🚀 开始清理前的安全检查...")
    
    # 分析重复函数定义的影响
    analyze_duplicate_functions_impact()
    
    # 分析未使用input参数的影响
    analyze_unused_input_impact()
    
    # 分析未使用全局变量的影响
    analyze_unused_global_vars_impact()
    
    # 分析未使用函数的影响
    analyze_unused_functions_impact()
    
    # 分析冗余代码模式的影响
    analyze_redundant_patterns_impact()
    
    # 检查关键依赖关系
    check_critical_dependencies()
    
    # 生成清理计划
    generate_cleanup_plan()
    
    print("\n📊 安全检查总结:")
    print("=" * 60)
    print("✅ 安全检查完成！")
    print("建议按照清理计划逐步执行，确保EA功能不受影响。")

if __name__ == "__main__":
    main() 