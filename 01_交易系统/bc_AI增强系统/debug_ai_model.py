#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型调试脚本
用于诊断模型输出NaN的问题
"""

import torch
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def debug_model_output():
    """调试模型输出"""
    print("🔍 AI模型调试开始")
    print("=" * 50)
    
    try:
        # 1. 加载数据处理器
        import joblib
        processor = joblib.load('trading_data_processor.pkl')
        print("✅ 数据处理器加载成功")
        print(f"   特征列数: {len(processor.feature_columns)}")
        print(f"   序列长度: {processor.sequence_length}")
        
        # 2. 加载模型
        from trading_transformer_model import TradingTransformer
        input_dim = len(processor.feature_columns)
        model = TradingTransformer(
            input_dim=input_dim,
            d_model=128,
            nhead=8,
            num_layers=6,
            num_classes=3,
            dropout=0.1
        )
        model.load_state_dict(torch.load('best_trading_model.pth', map_location='cpu'))
        model.eval()
        print("✅ 模型加载成功")
        
        # 3. 创建简单测试数据
        print("\n📝 创建测试数据...")
        # 创建简单的OHLCV数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        np.random.seed(42)
        
        data = []
        price = 2000
        for i in range(len(dates)):
            price_change = np.random.normal(0, 0.001)
            price *= (1 + price_change)
            
            volatility = abs(np.random.normal(0, 0.0005))
            data.append({
                'time': dates[i],
                'open': price,
                'high': price * (1 + volatility),
                'low': price * (1 - volatility),
                'close': price * (1 + np.random.normal(0, 0.0002)),
                'volume': np.random.randint(1000, 5000)
            })
        
        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        print(f"✅ 测试数据创建完成: {len(df)} 条记录")
        
        # 4. 特征工程
        print("\n🔧 执行特征工程...")
        df = processor.engineer_features(df)
        print(f"✅ 特征工程完成，特征数: {len(df.columns)}")
        
        # 5. 检查特征数据
        print("\n🔍 检查特征数据...")
        feature_cols = processor.feature_columns
        print(f"   特征列: {feature_cols[:5]}...")
        
        # 检查是否有NaN
        feature_data = df[feature_cols].values
        nan_count = np.isnan(feature_data).sum()
        print(f"   特征数据NaN数量: {nan_count}")
        
        if nan_count > 0:
            print("⚠️  发现NaN值，尝试修复...")
            # 使用前向填充
            df[feature_cols] = df[feature_cols].fillna(method='ffill')
            # 如果还有NaN，用0填充
            df[feature_cols] = df[feature_cols].fillna(0)
            feature_data = df[feature_cols].values
            nan_count = np.isnan(feature_data).sum()
            print(f"   修复后NaN数量: {nan_count}")
        
        # 6. 标准化
        print("\n📊 执行标准化...")
        try:
            feature_data_scaled = processor.scaler.transform(feature_data)
            print("✅ 标准化成功")
            
            # 检查标准化后的数据
            inf_count = np.isinf(feature_data_scaled).sum()
            nan_count = np.isnan(feature_data_scaled).sum()
            print(f"   标准化后无穷值数量: {inf_count}")
            print(f"   标准化后NaN数量: {nan_count}")
            
            if inf_count > 0 or nan_count > 0:
                print("⚠️  标准化后仍有问题值，尝试修复...")
                feature_data_scaled = np.nan_to_num(feature_data_scaled, nan=0.0, posinf=1.0, neginf=-1.0)
                inf_count = np.isinf(feature_data_scaled).sum()
                nan_count = np.isnan(feature_data_scaled).sum()
                print(f"   修复后无穷值数量: {inf_count}")
                print(f"   修复后NaN数量: {nan_count}")
            
        except Exception as e:
            print(f"❌ 标准化失败: {e}")
            return
        
        # 7. 创建序列数据
        print("\n📋 创建序列数据...")
        X = []
        for i in range(processor.sequence_length, len(df)):
            X.append(feature_data_scaled[i-processor.sequence_length:i])
        
        X = np.array(X)
        print(f"✅ 序列数据创建完成: {X.shape}")
        
        # 8. 模型预测
        print("\n🤖 执行模型预测...")
        with torch.no_grad():
            # 测试第一个序列
            input_tensor = torch.FloatTensor(X[0:1])
            print(f"   输入张量形状: {input_tensor.shape}")
            print(f"   输入张量范围: [{input_tensor.min():.6f}, {input_tensor.max():.6f}]")
            
            # 检查输入是否有问题
            input_nan = torch.isnan(input_tensor).sum().item()
            input_inf = torch.isinf(input_tensor).sum().item()
            print(f"   输入NaN数量: {input_nan}")
            print(f"   输入无穷值数量: {input_inf}")
            
            if input_nan > 0 or input_inf > 0:
                print("❌ 输入数据有问题，无法进行预测")
                return
            
            # 执行预测
            try:
                logits, attention_weights = model(input_tensor)
                print("✅ 模型前向传播成功")
                print(f"   Logits形状: {logits.shape}")
                print(f"   Logits范围: [{logits.min():.6f}, {logits.max():.6f}]")
                
                # 检查logits
                logits_nan = torch.isnan(logits).sum().item()
                logits_inf = torch.isinf(logits).sum().item()
                print(f"   Logits NaN数量: {logits_nan}")
                print(f"   Logits无穷值数量: {logits_inf}")
                
                if logits_nan > 0 or logits_inf > 0:
                    print("❌ Logits包含问题值")
                    return
                
                # 计算概率
                probabilities = torch.softmax(logits, dim=1)
                print("✅ Softmax计算成功")
                print(f"   概率形状: {probabilities.shape}")
                print(f"   概率和: {probabilities.sum(dim=1).item():.6f}")
                
                # 检查概率
                prob_nan = torch.isnan(probabilities).sum().item()
                prob_inf = torch.isinf(probabilities).sum().item()
                print(f"   概率NaN数量: {prob_nan}")
                print(f"   概率无穷值数量: {prob_inf}")
                
                if prob_nan > 0 or prob_inf > 0:
                    print("❌ 概率包含问题值")
                    return
                
                # 获取预测结果
                prediction = torch.argmax(logits, dim=1).item()
                confidence = probabilities[0][prediction].item()
                
                prediction_meanings = {0: "看跌", 1: "震荡", 2: "看涨"}
                
                print(f"\n🎯 预测结果:")
                print(f"   预测: {prediction} ({prediction_meanings[prediction]})")
                print(f"   置信度: {confidence:.6f}")
                print(f"   概率分布: 看跌={probabilities[0][0]:.6f}, 震荡={probabilities[0][1]:.6f}, 看涨={probabilities[0][2]:.6f}")
                
                # 测试多个样本
                print(f"\n📊 测试多个样本...")
                success_count = 0
                total_count = min(10, len(X))
                
                for i in range(total_count):
                    input_tensor = torch.FloatTensor(X[i:i+1])
                    logits, _ = model(input_tensor)
                    
                    if torch.isnan(logits).any() or torch.isinf(logits).any():
                        print(f"   样本 {i+1}: ❌ 失败")
                    else:
                        probabilities = torch.softmax(logits, dim=1)
                        prediction = torch.argmax(logits, dim=1).item()
                        confidence = probabilities[0][prediction].item()
                        print(f"   样本 {i+1}: ✅ {prediction_meanings[prediction]} (置信度: {confidence:.4f})")
                        success_count += 1
                
                print(f"\n📈 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
                
            except Exception as e:
                print(f"❌ 模型预测失败: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 调试过程失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_model_output() 