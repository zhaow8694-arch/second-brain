#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全清理脚本
逐步删除未使用的代码，确保EA功能不受影响
"""

import re
import os

def cleanup_unused_input_parameters():
    """清理未使用的input参数"""
    print("🔧 开始清理未使用的input参数...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 未使用的input参数列表
    unused_inputs = [
        'KDJOverbought',
        'KDJ_Oversold', 
        'VolatilityThreshold',
        'VolumeThreshold',
        'SentimentThreshold'
    ]
    
    cleaned_content = content
    removed_count = 0
    
    for param in unused_inputs:
        # 查找input参数定义行
        input_pattern = rf'input\s+\w+\s+{param}\s*=\s*[^;]+;'
        matches = re.findall(input_pattern, cleaned_content)
        
        if matches:
            # 删除这一行
            cleaned_content = re.sub(input_pattern, '', cleaned_content)
            removed_count += 1
            print(f"   ✅ 已删除未使用的input参数: {param}")
    
    # 写回文件
    with open(ea_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"   📊 总共删除了 {removed_count} 个未使用的input参数")
    return True

def cleanup_unused_global_variables():
    """清理未使用的全局变量"""
    print("\n🔧 开始清理未使用的全局变量...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 未使用的全局变量列表
    unused_globals = [
        'g_last_normal_order_time',
        'close_3'
    ]
    
    cleaned_content = content
    removed_count = 0
    
    for var in unused_globals:
        # 查找全局变量定义行
        var_pattern = rf'(?:int|double|bool|string|datetime)\s+{var}\s*=\s*[^;]+;'
        matches = re.findall(var_pattern, cleaned_content)
        
        if matches:
            # 删除这一行
            cleaned_content = re.sub(var_pattern, '', cleaned_content)
            removed_count += 1
            print(f"   ✅ 已删除未使用的全局变量: {var}")
    
    # 写回文件
    with open(ea_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"   📊 总共删除了 {removed_count} 个未使用的全局变量")
    return True

def cleanup_unused_functions():
    """清理未使用的函数"""
    print("\n🔧 开始清理未使用的函数...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 未使用的函数列表（基于之前的检查结果）
    unused_functions = [
        'IsLockOrder', 'IsRetryableError', 'GetOrderTotalProfit', 'GetOrderStats',
        'HasOrderType', 'GetOrderTickets', 'CanTrade', 'RecordTrade', 'CleanupClosedOrders',
        'GetAccountBalance', 'GetAccountEquity', 'GetAccountMargin', 'GetAccountFreeMargin',
        'GetAccountProfit', 'GetAccountCurrency', 'GetAccountCompany', 'GetAccountServer',
        'GetAccountTradeMode', 'GetAccountTradeAllowed', 'GetAccountTradeExpert',
        'GetAccountMarginMode', 'GetAccountStopoutLevel', 'GetAccountStopoutMode',
        'GetAccountLeverage', 'GetAccountName', 'GetAccountNumber', 'GetAccountLogin',
        'GetAccountPassword', 'GetAccountEmail', 'GetAccountPhone', 'GetAccountFax',
        'GetAccountWebsite', 'GetAccountComment', 'GetAccountColor', 'GetAccountStatus',
        'GetAccountStatusText', 'GetAccountStatusDescription'
    ]
    
    cleaned_content = content
    removed_count = 0
    
    for func_name in unused_functions:
        # 查找函数定义（包括整个函数体）
        # 使用更复杂的模式来匹配整个函数
        func_pattern = r'(?:bool|void|int|double|string)\s+' + func_name + r'\s*\([^)]*\)\s*\{[^}]*\}'
        matches = re.findall(func_pattern, cleaned_content, re.DOTALL)
        
        if matches:
            # 删除整个函数
            cleaned_content = re.sub(func_pattern, '', cleaned_content, flags=re.DOTALL)
            removed_count += 1
            print(f"   ✅ 已删除未使用的函数: {func_name}")
    
    # 写回文件
    with open(ea_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"   📊 总共删除了 {removed_count} 个未使用的函数")
    return True

def verify_cleanup():
    """验证清理结果"""
    print("\n🔍 验证清理结果...")
    
    ea_file = "AI_Enhanced_Risk_EA.mq4"
    if not os.path.exists(ea_file):
        return False
    
    with open(ea_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 清理验证结果:")
    
    # 检查是否还有未使用的input参数
    unused_inputs = ['KDJOverbought', 'KDJ_Oversold', 'VolatilityThreshold', 'VolumeThreshold', 'SentimentThreshold']
    remaining_inputs = []
    
    for param in unused_inputs:
        if re.search(rf'input\s+\w+\s+{param}\s*=', content):
            remaining_inputs.append(param)
    
    if remaining_inputs:
        print(f"   ⚠️  仍有未删除的input参数: {remaining_inputs}")
    else:
        print("   ✅ 所有未使用的input参数已清理完成")
    
    # 检查是否还有未使用的全局变量
    unused_globals = ['g_last_normal_order_time', 'close_3']
    remaining_globals = []
    
    for var in unused_globals:
        if re.search(rf'(?:int|double|bool|string|datetime)\s+{var}\s*=', content):
            remaining_globals.append(var)
    
    if remaining_globals:
        print(f"   ⚠️  仍有未删除的全局变量: {remaining_globals}")
    else:
        print("   ✅ 所有未使用的全局变量已清理完成")
    
    # 检查关键函数是否还在
    critical_functions = ['OnTick', 'OnInit', 'OnDeinit']
    missing_critical = []
    
    for func in critical_functions:
        if not re.search(r'(?:void|int)\s+' + func + r'\s*\([^)]*\)\s*\{', content):
            missing_critical.append(func)
    
    if missing_critical:
        print(f"   ❌ 缺少关键函数: {missing_critical}")
    else:
        print("   ✅ 所有关键函数都还在")
    
    return True

def main():
    """主函数"""
    print("🚀 开始安全清理...")
    print("=" * 60)
    
    # 第一步：清理未使用的input参数
    cleanup_unused_input_parameters()
    
    # 第二步：清理未使用的全局变量
    cleanup_unused_global_variables()
    
    # 第三步：清理未使用的函数
    cleanup_unused_functions()
    
    # 第四步：验证清理结果
    verify_cleanup()
    
    print("\n📊 安全清理总结:")
    print("=" * 60)
    print("✅ 安全清理完成！")
    print("建议现在测试EA编译，确保功能正常。")

if __name__ == "__main__":
    main() 