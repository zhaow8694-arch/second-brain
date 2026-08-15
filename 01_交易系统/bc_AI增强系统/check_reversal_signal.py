#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反转信号诊断脚本
检查反转信号计算和应急仓位触发条件
"""

import os
import time
from datetime import datetime

def check_reversal_signal_status():
    """检查反转信号状态"""
    print("🔍 反转信号诊断检查")
    print("=" * 50)
    
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
    
    # 诊断建议
    print("\n💡 诊断建议:")
    print("1. 检查MT4日志中的反转信号计算信息")
    print("2. 查找 '📊 统一反转信号检测' 日志")
    print("3. 查找 '📊 应急仓位触发失败' 日志")
    print("4. 确认决策评分历史是否足够 (需要5个历史记录)")
    print("5. 检查反转信号阈值是否达到 0.6")
    
    print("\n" + "=" * 50)
    print("诊断完成")

if __name__ == "__main__":
    check_reversal_signal_status() 