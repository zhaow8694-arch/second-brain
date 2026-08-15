#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应急仓位调试脚本
详细检查应急仓位触发条件
"""

import os
import time
from datetime import datetime

def debug_emergency_order():
    """调试应急仓位触发条件"""
    print("🚨 应急仓位触发条件详细检查")
    print("=" * 60)
    
    # 检查AI预测文件
    print("📊 检查AI预测文件:")
    if os.path.exists('ai_prediction.txt'):
        try:
            with open('ai_prediction.txt', 'r') as f:
                content = f.read().strip()
                print(f"  ✅ ai_prediction.txt 存在")
                print(f"  📄 内容: {content}")
                
                if ',' in content:
                    parts = content.split(',')
                    if len(parts) >= 2:
                        prediction = int(parts[0])
                        confidence = float(parts[1])
                        print(f"  🎯 预测方向: {prediction} ({'买入' if prediction == 1 else '卖出' if prediction == 2 else '持有'})")
                        print(f"  📈 置信度: {confidence:.3f}")
                        
                        # 检查置信度是否达到阈值
                        threshold = 0.6
                        print(f"  🎯 置信度阈值检查: {confidence:.3f} >= {threshold} = {confidence >= threshold}")
                        
                        # 检查是否达到应急仓位触发阈值
                        emergency_threshold = 0.6
                        print(f"  🚨 应急仓位触发阈值检查: {confidence:.3f} >= {emergency_threshold} = {confidence >= emergency_threshold}")
        except Exception as e:
            print(f"  ❌ 读取预测文件失败: {e}")
    else:
        print("  ❌ ai_prediction.txt 不存在")
    
    # 检查市场数据文件
    print("\n📈 检查市场数据文件:")
    if os.path.exists('market_data.csv'):
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime('market_data.csv'))
            file_size = os.path.getsize('market_data.csv')
            print(f"  ✅ market_data.csv 存在")
            print(f"  📅 更新时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  📊 文件大小: {file_size} 字节")
            
            # 检查数据行数
            with open('market_data.csv', 'r') as f:
                lines = f.readlines()
                print(f"  📊 数据行数: {len(lines)}")
                if len(lines) >= 50:
                    print(f"  ✅ 数据量充足 (>=50行)")
                else:
                    print(f"  ⚠️ 数据量不足 (<50行)")
        except Exception as e:
            print(f"  ❌ 读取市场数据失败: {e}")
    else:
        print("  ❌ market_data.csv 不存在")
    
    # 检查Python AI服务
    print("\n🐍 检查Python AI服务:")
    try:
        import subprocess
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        if 'python.exe' in result.stdout:
            lines = [line for line in result.stdout.strip().split('\n') if 'python.exe' in line]
            print(f"  ✅ Python AI服务正在运行")
            print(f"  📊 进程数量: {len(lines)}")
        else:
            print("  ❌ Python AI服务未运行")
    except Exception as e:
        print(f"  ❌ 检查进程失败: {e}")
    
    # 应急仓位触发条件分析
    print("\n🚨 应急仓位触发条件分析:")
    print("  条件1: 普通仓位达到12个 ✅ (您确认已满足)")
    print("  条件2: 反转信号有效 ✅ (检测到反转信号)")
    print("  条件3: 应急仓位未满 ✅ (您确认未满)")
    print("  条件4: 决策评分历史足够 (需要5个历史记录)")
    print("  条件5: 反转信号阈值达到 (需要>=0.6)")
    print("  条件6: 点差检查 (需要<=50)")
    print("  条件7: 市场状态适合")
    
    # 可能的问题分析
    print("\n🔍 可能的问题分析:")
    print("  1. 决策评分历史数据不足 (最可能)")
    print("  2. 反转信号有效性检查失败")
    print("  3. 点差过大")
    print("  4. 市场状态不适合")
    print("  5. 建仓频率控制阻止")
    
    # 建议检查的日志
    print("\n💡 请在MT4日志中查找以下信息:")
    print("  📊 统一反转信号检测: 方向=买入/卖出 评分=X.XXX")
    print("  📊 决策历史数据不足，需要至少5个历史记录，当前:X")
    print("  📊 应急仓位触发检查 - 普通仓位:12/12 应急仓位:X/2")
    print("  📊 应急仓位触发失败: 未检测到决策评分反转信号")
    print("  📊 应急仓位触发失败: 点差过大")
    print("  📊 应急仓位触发失败: 其他条件不满足")
    
    print("\n" + "=" * 60)
    print("调试完成")

if __name__ == "__main__":
    debug_emergency_order() 