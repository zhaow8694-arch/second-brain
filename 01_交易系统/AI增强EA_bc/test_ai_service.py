#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务测试脚本
"""

import os
import time
import pandas as pd
from datetime import datetime

def test_ai_service():
    """测试AI服务是否正常工作"""
    print("=== AI服务测试 ===")
    
    # 检查必要文件
    required_files = [
        'continuous_ai_monitor.py',
        'trading_data_processor.pkl',
        'trading_transformer_model.py'
    ]
    
    print("📁 检查必要文件:")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - 缺失")
    
    # 检查AI预测文件
    print("\n📊 检查AI预测文件:")
    if os.path.exists('ai_prediction.txt'):
        try:
            with open('ai_prediction.txt', 'r') as f:
                content = f.read().strip()
                print(f"  ✅ ai_prediction.txt 存在")
                print(f"  📄 内容: {content}")
                
                # 解析预测结果
                if ',' in content:
                    parts = content.split(',')
                    if len(parts) >= 2:
                        prediction = int(parts[0])
                        confidence = float(parts[1])
                        print(f"  🎯 预测方向: {prediction} ({'看跌' if prediction == 0 else '震荡' if prediction == 1 else '看涨'})")
                        print(f"  📈 置信度: {confidence:.3f}")
        except Exception as e:
            print(f"  ❌ 读取预测文件失败: {e}")
    else:
        print("  ❌ ai_prediction.txt 不存在")
    
    # 检查市场数据文件
    print("\n📈 检查市场数据文件:")
    if os.path.exists('market_data.csv'):
        try:
            df = pd.read_csv('market_data.csv')
            print(f"  ✅ market_data.csv 存在")
            print(f"  📊 数据行数: {len(df)}")
            print(f"  📊 数据列数: {len(df.columns)}")
            if len(df) > 0:
                print(f"  📅 最新时间: {df.iloc[0, 0] if len(df.columns) > 0 else 'N/A'}")
        except Exception as e:
            print(f"  ❌ 读取市场数据失败: {e}")
    else:
        print("  ❌ market_data.csv 不存在")
    
    # 检查Python进程
    print("\n🐍 检查Python进程:")
    try:
        import subprocess
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        if 'python.exe' in result.stdout:
            print("  ✅ Python AI服务正在运行")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'python.exe' in line:
                    print(f"  📋 {line}")
        else:
            print("  ❌ Python AI服务未运行")
    except Exception as e:
        print(f"  ❌ 检查进程失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_ai_service() 