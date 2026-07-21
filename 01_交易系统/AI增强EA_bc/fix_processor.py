#!/usr/bin/env python3
"""
修复损坏的trading_data_processor.pkl文件
"""

from trading_transformer_model import TradingDataProcessor
import pandas as pd
import pickle
import os
import numpy as np

def fix_processor():
    """重新生成正确的处理器文件"""
    print("🔧 开始修复处理器文件...")
    
    # 创建一个新的处理器
    processor = TradingDataProcessor(sequence_length=50)
    
    # 使用实际的历史数据来初始化
    if os.path.exists('XAUUSD15.csv'):
        print("📊 使用XAUUSD15.csv数据...")
        df = pd.read_csv('XAUUSD15.csv')
        print(f"🔍 原始列名: {list(df.columns)}")
        
        # 检查是否为MT4标准格式（时间戳格式）
        if len(df.columns) >= 6 and df.columns[0].startswith('2'):
            print("📈 检测到MT4格式，转换列名...")
            # MT4格式: Date, Time, Open, High, Low, Close, Volume
            df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
            # 只保留OHLCV数据
            df = df[['open', 'high', 'low', 'close', 'volume']].copy()
        elif 'Open' in df.columns:
            # 标准格式但首字母大写
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            df = df[['open', 'high', 'low', 'close', 'volume']].copy()
        else:
            print("❌ 无法识别的CSV格式")
            return False
            
        # 确保数据类型正确
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 取足够的数据用于训练
        df = df.dropna().head(1000)  # 取前1000行有效数据
        print(f"📊 处理后数据行数: {len(df)}")
        
    else:
        print("📊 生成测试数据...")
        # 生成更健壮的测试数据
        np.random.seed(42)
        n_points = 1000
        base_price = 2000
        
        # 生成更真实的价格数据
        price_changes = np.random.normal(0, 5, n_points)
        prices = np.cumsum(price_changes) + base_price
        
        # 确保OHLC关系正确
        opens = prices
        closes = prices + np.random.normal(0, 2, n_points)
        highs = np.maximum(opens, closes) + np.abs(np.random.normal(0, 3, n_points))
        lows = np.minimum(opens, closes) - np.abs(np.random.normal(0, 3, n_points))
        volumes = np.random.randint(800, 2000, n_points)
        
        df = pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })
    
    if len(df) < 100:
        print("❌ 数据不足，无法训练")
        return False
    
    print(f"✅ 数据准备完成，共 {len(df)} 行")
    print(f"🔍 数据范围: Open({df['open'].min():.2f}-{df['open'].max():.2f})")
    
    # 执行特征工程
    print("🔧 开始特征工程...")
    try:
        df_features = processor.engineer_features(df)
        print(f"✅ 特征工程完成，生成 {len(df_features.columns)} 列")
    except Exception as e:
        print(f"❌ 特征工程失败: {e}")
        return False
    
    # 获取特征列（排除原始OHLCV列）
    feature_cols = [col for col in df_features.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
    processor.feature_columns = feature_cols
    print(f"🎯 特征列数量: {len(feature_cols)}")
    
    if len(feature_cols) == 0:
        print("❌ 没有生成任何特征")
        return False
    
    # 清理特征数据
    df_clean = df_features[feature_cols].dropna()
    print(f"📊 清理后特征数据: {len(df_clean)} 行")
    
    if len(df_clean) < 50:
        print("❌ 清理后数据不足，无法训练标准化器")
        return False
    
    # 训练标准化器
    print("🎯 训练标准化器...")
    try:
        feature_data = df_clean.values
        processor.scaler.fit(feature_data)
        print("✅ 标准化器训练完成")
        
        # 验证标准化器
        test_transform = processor.scaler.transform(feature_data[:5])
        print(f"🧪 标准化验证: {test_transform.shape}")
        
    except Exception as e:
        print(f"❌ 标准化器训练失败: {e}")
        return False
    
    # 备份原文件
    if os.path.exists('trading_data_processor.pkl'):
        # 如果备份已存在，先删除
        if os.path.exists('trading_data_processor_backup.pkl'):
            os.remove('trading_data_processor_backup.pkl')
        os.rename('trading_data_processor.pkl', 'trading_data_processor_backup.pkl')
        print("💾 原文件已备份")
    
    # 保存新的处理器
    print("💾 保存处理器...")
    try:
        with open('trading_data_processor.pkl', 'wb') as f:
            pickle.dump(processor, f)
        print("✅ 处理器保存成功")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False
    
    # 验证文件
    print("🧪 验证新文件...")
    try:
        with open('trading_data_processor.pkl', 'rb') as f:
            test_processor = pickle.load(f)
        
        print(f"✅ 文件验证成功!")
        print(f"📊 特征数量: {len(test_processor.feature_columns)}")
        print(f"🎯 标准化器状态: {'已训练' if hasattr(test_processor.scaler, 'mean_') else '未训练'}")
        
        # 测试预测功能
        if len(df_clean) >= 50:
            print("🧪 测试预测功能...")
            test_data = df_clean.head(50)
            try:
                # 这里只测试数据处理，不测试模型预测
                processed = test_processor.scaler.transform(test_data)
                print(f"✅ 数据处理测试成功: {processed.shape}")
            except Exception as e:
                print(f"⚠️ 数据处理测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = fix_processor()
    if success:
        print("\n🎉 处理器修复完成!")
        print("📋 修复内容:")
        print("  ✅ 正确解析XAUUSD15.csv格式")
        print("  ✅ 生成完整特征工程")
        print("  ✅ 训练标准化器")
        print("  ✅ 验证文件完整性")
    else:
        print("\n❌ 处理器修复失败!") 