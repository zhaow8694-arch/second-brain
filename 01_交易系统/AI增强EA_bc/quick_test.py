#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 用于日常检查关键功能
"""

import os
import sys
import time
from datetime import datetime

def quick_ai_test():
    """快速AI功能测试"""
    print("🧠 快速AI测试...")
    
    try:
        from continuous_ai_monitor import EATradingPredictor
        
        # 检查模型加载
        predictor = EATradingPredictor()
        if predictor.model is None:
            print("❌ AI模型加载失败")
            return False
            
        # 快速预测测试
        if os.path.exists("market_data.csv"):
            prediction, confidence = predictor.make_prediction_from_file("market_data.csv")
            if prediction is not None:
                print(f"✅ AI预测正常: {prediction}, 置信度: {confidence:.3f}")
                return True
            else:
                print("❌ AI预测失败")
                return False
        else:
            print("⚠️ 缺少市场数据文件，跳过预测测试")
            return True
            
    except Exception as e:
        print(f"❌ AI测试失败: {e}")
        return False

def quick_file_test():
    """快速文件通讯测试"""
    print("📁 快速文件通讯测试...")
    
    try:
        # 创建测试数据
        test_data = f"""ServerTime,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ClientTime,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
2024-01-01 10:00:00,2000.0,2010.0,1990.0,2005.0,1000
2024-01-01 09:59:00,1995.0,2005.0,1985.0,2000.0,1200
2024-01-01 09:58:00,1990.0,2000.0,1980.0,1995.0,800"""
        
        # 写入测试文件
        with open("quick_test_data.csv", "w") as f:
            f.write(test_data)
        
        # 测试AI读取
        from continuous_ai_monitor import EATradingPredictor
        predictor = EATradingPredictor()
        df = predictor.parse_market_data("quick_test_data.csv")
        
        if df is not None:
            print(f"✅ 文件读取正常: {len(df)} 行数据")
            
            # 清理测试文件
            os.remove("quick_test_data.csv")
            return True
        else:
            print("❌ 文件读取失败")
            return False
            
    except Exception as e:
        print(f"❌ 文件测试失败: {e}")
        return False

def quick_environment_check():
    """快速环境检查"""
    print("🔍 快速环境检查...")
    
    issues = []
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        issues.append("Python版本过低")
    
    # 检查关键包
    try:
        import torch
        import numpy as np
        import pandas as pd
    except ImportError as e:
        issues.append(f"缺少Python包: {e}")
    
    # 检查关键文件
    required_files = [
        "best_trading_model.pth",
        "trading_data_processor.pkl",
        "continuous_ai_monitor.py",
        "AI_Enhanced_Risk_EA.mq4"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"缺少文件: {file}")
    
    if issues:
        print("❌ 环境问题:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ 环境检查通过")
        return True

def quick_performance_test():
    """快速性能测试"""
    print("⚡ 快速性能测试...")
    
    try:
        from continuous_ai_monitor import EATradingPredictor
        
        predictor = EATradingPredictor()
        if predictor.model is None:
            print("❌ 模型未加载，跳过性能测试")
            return False
        
        # 测试预测速度
        if os.path.exists("market_data.csv"):
            start_time = time.time()
            prediction, confidence = predictor.make_prediction_from_file("market_data.csv")
            end_time = time.time()
            
            duration = end_time - start_time
            
            if prediction is not None:
                if duration < 2.0:
                    print(f"✅ 性能良好: {duration:.3f}秒")
                    return True
                else:
                    print(f"⚠️ 性能较慢: {duration:.3f}秒")
                    return True
            else:
                print("❌ 预测失败")
                return False
        else:
            print("⚠️ 缺少测试数据，跳过性能测试")
            return True
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 EA + AI 系统快速检查")
    print("=" * 50)
    
    start_time = time.time()
    
    tests = [
        ("环境检查", quick_environment_check),
        ("AI功能", quick_ai_test),
        ("文件通讯", quick_file_test),
        ("性能检查", quick_performance_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}测试:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
        
        time.sleep(0.5)  # 短暂延迟
    
    # 总结
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print("📊 快速测试结果")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n📈 总结: {passed}/{total} 项通过")
    print(f"⏱️ 耗时: {duration:.2f} 秒")
    
    if passed == total:
        print("🎉 所有快速测试通过！系统状态良好")
    elif passed >= total * 0.8:
        print("⚠️ 大部分测试通过，请关注失败项目")
    else:
        print("❌ 多项测试失败，建议运行完整测试")
    
    print("\n💡 提示:")
    print("   - 如需完整测试，请运行: py run_all_tests.py")
    print("   - 如需启动AI服务，请运行: py continuous_ai_monitor.py mt4")

if __name__ == "__main__":
    main() 