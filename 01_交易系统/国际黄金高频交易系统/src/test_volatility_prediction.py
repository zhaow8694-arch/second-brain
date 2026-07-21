import pytest
import torch
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple

from models.volatility_prediction import VolatilityPredictionModel
from models.deepseek_interface import (
    MarketFeatures,
    ModelConfig,
    ModelPrediction
)

@pytest.fixture
def model_config():
    """创建测试用的模型配置"""
    return ModelConfig(
        model_type="volatility_prediction",
        input_features=[
            'price', 'volume', 'volatility', 'trend_strength',
            'momentum', 'order_imbalance', 'spread'
        ],
        output_features=['volatility'],
        time_horizon=5,
        update_interval=1,
        confidence_threshold=0.7,
        batch_size=32,
        use_gpu=False
    )

@pytest.fixture
def volatility_model(model_config):
    """创建波动率预测模型实例"""
    return VolatilityPredictionModel(model_config)

def generate_market_data(n_points: int = 100,
                        base_price: float = 50000.0,
                        base_volatility: float = 0.02) -> Tuple[List[MarketFeatures], List[float]]:
    """生成测试用的市场数据和波动率标签"""
    features_list = []
    volatility_labels = []
    
    # 生成价格序列
    prices = [base_price]
    returns = []
    for _ in range(n_points - 1):
        # 生成随机波动率
        current_volatility = base_volatility * (1 + np.random.normal(0, 0.2))
        volatility_labels.append(current_volatility)
        
        # 使用当前波动率生成价格
        price = prices[-1] * (1 + np.random.normal(0, current_volatility))
        prices.append(price)
        returns.append(np.log(price / prices[-1]))
    
    # 计算实现波动率
    window_size = 10
    for i in range(n_points):
        price = prices[i]
        if i >= window_size:
            realized_vol = np.std(returns[i-window_size:i]) * np.sqrt(252)
        else:
            realized_vol = base_volatility
            
        volume = np.random.lognormal(4, 0.5)
        spread = price * 0.0004
        
        features = MarketFeatures(
            timestamp=datetime.now() + timedelta(minutes=i),
            price=price,
            volume=volume,
            bid_price=price - spread/2,
            ask_price=price + spread/2,
            bid_volume=volume/2,
            ask_volume=volume/2,
            volatility=realized_vol,
            trend_strength=np.random.random(),
            momentum=np.random.normal(0, 1),
            order_imbalance=np.random.normal(0, 0.2),
            spread=spread,
            market_depth={'level_1': volume, 'level_2': volume*1.5},
            custom_indicators={
                'rsi': np.random.uniform(30, 70),
                'macd': np.random.normal(0, 1),
                'bb_width': realized_vol * 2
            }
        )
        features_list.append(features)
    
    return features_list, volatility_labels

async def test_model_initialization(volatility_model):
    """测试模型初始化"""
    await volatility_model.initialize_model()
    
    # 验证模型组件
    assert isinstance(volatility_model.model.lstm, torch.nn.LSTM)
    assert isinstance(volatility_model.optimizer, torch.optim.Optimizer)
    assert isinstance(volatility_model.criterion, torch.nn.Module)
    assert volatility_model.feature_scaler is not None
    assert volatility_model.device is not None
    assert len(volatility_model.feature_buffer) == 0

async def test_feature_preprocessing(volatility_model):
    """测试特征预处理"""
    # 生成测试数据
    features_list, _ = generate_market_data(n_points=15)
    
    # 预处理第一个特征
    processed_features = await volatility_model.preprocess_features(features_list[0])
    
    # 验证预处理结果
    assert isinstance(processed_features, np.ndarray)
    assert processed_features.shape[0] == volatility_model.sequence_length
    assert processed_features.shape[1] == len(volatility_model.config.input_features)
    assert not np.any(np.isnan(processed_features))
    assert not np.any(np.isinf(processed_features))
    
    # 验证序列缓存
    assert len(volatility_model.feature_buffer) == volatility_model.sequence_length

async def test_model_prediction(volatility_model):
    """测试模型预测"""
    # 初始化模型
    await volatility_model.initialize_model()
    
    # 生成测试数据
    features_list, _ = generate_market_data(n_points=15)
    
    # 执行预测
    prediction = await volatility_model.predict(features_list[-1])
    
    # 验证预测结果
    assert isinstance(prediction, ModelPrediction)
    assert isinstance(prediction.predicted_value, float)
    assert prediction.predicted_value > 0  # 波动率应该为正
    assert 0 <= prediction.confidence <= 1
    assert prediction.prediction_interval[0] <= prediction.predicted_value <= prediction.prediction_interval[1]
    assert all(importance >= 0 for importance in prediction.feature_importance.values())

async def test_model_update(volatility_model):
    """测试模型更新"""
    # 初始化模型
    await volatility_model.initialize_model()
    
    # 生成训练数据
    features_list, volatility_labels = generate_market_data(n_points=100)
    
    # 更新模型
    await volatility_model.update_model(features_list, volatility_labels)
    
    # 验证更新结果
    assert volatility_model.last_update_time is not None
    assert len(volatility_model.training_history) > 0
    assert volatility_model.training_history[-1]['samples'] == len(features_list)

async def test_prediction_validation(volatility_model):
    """测试预测验证"""
    # 初始化模型
    await volatility_model.initialize_model()
    
    # 生成测试数据
    features_list, volatility_labels = generate_market_data(n_points=15)
    prediction = await volatility_model.predict(features_list[-1])
    
    # 验证预测
    validation_result = await volatility_model.validate_prediction(
        prediction, 
        volatility_labels[-1]
    )
    
    # 验证结果
    assert isinstance(validation_result, dict)
    assert 'error' in validation_result
    assert 'relative_error' in validation_result
    assert 'in_interval' in validation_result
    assert len(volatility_model.prediction_history) > 0

async def test_feature_importance(volatility_model):
    """测试特征重要性计算"""
    # 初始化模型
    await volatility_model.initialize_model()
    
    # 生成测试数据
    features_list, _ = generate_market_data(n_points=15)
    
    # 预处理特征
    feature_array = await volatility_model.preprocess_features(features_list[-1])
    feature_tensor = torch.FloatTensor(feature_array).unsqueeze(0).to(volatility_model.device)
    
    # 计算特征重要性
    importance = volatility_model._calculate_feature_importance(feature_tensor)
    
    # 验证结果
    assert isinstance(importance, dict)
    assert len(importance) == len(volatility_model.config.input_features)
    assert all(importance[f] >= 0 for f in importance)

async def test_model_performance(volatility_model):
    """测试模型性能"""
    # 初始化模型
    await volatility_model.initialize_model()
    
    # 生成训练数据
    train_features, train_labels = generate_market_data(n_points=1000)
    
    # 训练模型
    await volatility_model.update_model(train_features, train_labels)
    
    # 生成测试数据
    test_features, test_labels = generate_market_data(n_points=100)
    
    # 执行预测和验证
    errors = []
    for features, actual_vol in zip(test_features[volatility_model.sequence_length:],
                                  test_labels[volatility_model.sequence_length-1:]):
        prediction = await volatility_model.predict(features)
        validation = await volatility_model.validate_prediction(prediction, actual_vol)
        errors.append(validation['relative_error'])
    
    # 验证性能
    mean_error = np.mean(errors)
    assert mean_error < 0.2  # 波动率预测的相对误差应小于20%
    
    # 验证预测指标
    metrics = volatility_model.get_prediction_metrics()
    assert 'mse' in metrics
    assert 'mae' in metrics
    assert metrics['sample_count'] > 0

async def test_sequence_handling(volatility_model):
    """测试序列处理"""
    # 初始化模型
    await volatility_model.initialize_model()
    
    # 生成测试数据
    features_list, _ = generate_market_data(n_points=20)
    
    # 测试序列积累
    for i in range(15):
        processed_features = await volatility_model.preprocess_features(features_list[i])
        if i < volatility_model.sequence_length - 1:
            assert len(volatility_model.feature_buffer) == i + 1
        else:
            assert len(volatility_model.feature_buffer) == volatility_model.sequence_length
            
    # 验证序列形状
    assert processed_features.shape == (volatility_model.sequence_length, 
                                     len(volatility_model.config.input_features))

async def main():
    """运行所有测试"""
    config = model_config()
    model = VolatilityPredictionModel(config)
    
    try:
        print("Testing model initialization...")
        await test_model_initialization(model)
        print("✓ Model initialization test passed")
        
        print("Testing feature preprocessing...")
        await test_feature_preprocessing(model)
        print("✓ Feature preprocessing test passed")
        
        print("Testing model prediction...")
        await test_model_prediction(model)
        print("✓ Model prediction test passed")
        
        print("Testing model update...")
        await test_model_update(model)
        print("✓ Model update test passed")
        
        print("Testing prediction validation...")
        await test_prediction_validation(model)
        print("✓ Prediction validation test passed")
        
        print("Testing feature importance...")
        await test_feature_importance(model)
        print("✓ Feature importance test passed")
        
        print("Testing model performance...")
        await test_model_performance(model)
        print("✓ Model performance test passed")
        
        print("Testing sequence handling...")
        await test_sequence_handling(model)
        print("✓ Sequence handling test passed")
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 