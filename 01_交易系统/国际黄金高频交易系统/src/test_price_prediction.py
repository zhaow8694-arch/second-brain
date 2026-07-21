import pytest
import torch
import numpy as np
from datetime import datetime, timedelta
from typing import List

from models.price_prediction import PricePredictionModel
from models.deepseek_interface import (
    MarketFeatures,
    ModelConfig,
    ModelPrediction
)

@pytest.fixture
def model_config():
    """创建测试用的模型配置"""
    return ModelConfig(
        model_type="price_prediction",
        input_features=[
            'price', 'volume', 'volatility', 'trend_strength',
            'momentum', 'order_imbalance', 'spread'
        ],
        output_features=['price'],
        time_horizon=5,
        update_interval=1,
        confidence_threshold=0.7,
        batch_size=32,
        use_gpu=False
    )

@pytest.fixture
def price_model(model_config):
    """创建价格预测模型实例"""
    return PricePredictionModel(model_config)

def generate_market_features(base_price: float = 50000.0, 
                           volatility: float = 0.02) -> MarketFeatures:
    """生成测试用的市场特征数据"""
    price = base_price * (1 + np.random.normal(0, volatility))
    volume = np.random.lognormal(4, 0.5)
    spread = base_price * 0.0004  # 4个基点的价差
    
    return MarketFeatures(
        timestamp=datetime.now(),
        price=price,
        volume=volume,
        bid_price=price - spread/2,
        ask_price=price + spread/2,
        bid_volume=volume/2,
        ask_volume=volume/2,
        volatility=volatility,
        trend_strength=np.random.random(),
        momentum=np.random.normal(0, 1),
        order_imbalance=np.random.normal(0, 0.2),
        spread=spread,
        market_depth={'level_1': volume, 'level_2': volume*1.5},
        custom_indicators={'rsi': np.random.uniform(30, 70),
                         'macd': np.random.normal(0, 1)}
    )

def generate_price_sequence(n_points: int = 100,
                          base_price: float = 50000.0,
                          volatility: float = 0.02) -> List[float]:
    """生成测试用的价格序列"""
    prices = [base_price]
    for _ in range(n_points - 1):
        price = prices[-1] * (1 + np.random.normal(0, volatility))
        prices.append(price)
    return prices

async def test_model_initialization(price_model):
    """测试模型初始化"""
    await price_model.initialize_model()
    
    # 验证模型组件
    assert isinstance(price_model.model, torch.nn.Module)
    assert isinstance(price_model.optimizer, torch.optim.Optimizer)
    assert isinstance(price_model.criterion, torch.nn.Module)
    assert price_model.feature_scaler is not None
    assert price_model.device is not None

async def test_feature_preprocessing(price_model):
    """测试特征预处理"""
    # 生成测试数据
    features = generate_market_features()
    
    # 预处理特征
    processed_features = await price_model.preprocess_features(features)
    
    # 验证预处理结果
    assert isinstance(processed_features, np.ndarray)
    assert processed_features.shape[1] == len(price_model.config.input_features)
    assert not np.any(np.isnan(processed_features))
    assert not np.any(np.isinf(processed_features))

async def test_model_prediction(price_model):
    """测试模型预测"""
    # 初始化模型
    await price_model.initialize_model()
    
    # 生成测试数据
    features = generate_market_features()
    
    # 执行预测
    prediction = await price_model.predict(features)
    
    # 验证预测结果
    assert isinstance(prediction, ModelPrediction)
    assert isinstance(prediction.predicted_value, float)
    assert 0 <= prediction.confidence <= 1
    assert prediction.prediction_interval[0] <= prediction.predicted_value <= prediction.prediction_interval[1]
    assert all(importance >= 0 for importance in prediction.feature_importance.values())

async def test_model_update(price_model):
    """测试模型更新"""
    # 初始化模型
    await price_model.initialize_model()
    
    # 生成训练数据
    n_samples = 100
    features = [generate_market_features() for _ in range(n_samples)]
    prices = generate_price_sequence(n_samples)
    
    # 更新模型
    await price_model.update_model(features, prices)
    
    # 验证更新结果
    assert price_model.last_update_time is not None
    assert len(price_model.training_history) > 0
    assert price_model.training_history[-1]['samples'] == n_samples

async def test_prediction_validation(price_model):
    """测试预测验证"""
    # 初始化模型
    await price_model.initialize_model()
    
    # 生成测试数据
    features = generate_market_features()
    prediction = await price_model.predict(features)
    actual_value = features.price * (1 + np.random.normal(0, 0.001))  # 小幅波动
    
    # 验证预测
    validation_result = await price_model.validate_prediction(prediction, actual_value)
    
    # 验证结果
    assert isinstance(validation_result, dict)
    assert 'error' in validation_result
    assert 'relative_error' in validation_result
    assert 'in_interval' in validation_result
    assert len(price_model.prediction_history) > 0

async def test_feature_importance(price_model):
    """测试特征重要性计算"""
    # 初始化模型
    await price_model.initialize_model()
    
    # 生成测试数据
    features = generate_market_features()
    
    # 计算特征重要性
    feature_tensor = torch.FloatTensor(
        await price_model.preprocess_features(features)
    ).to(price_model.device)
    
    importance = price_model._calculate_feature_importance(feature_tensor)
    
    # 验证结果
    assert isinstance(importance, dict)
    assert len(importance) == len(price_model.config.input_features)
    assert all(importance[f] >= 0 for f in importance)

async def test_model_performance(price_model):
    """测试模型性能"""
    # 初始化模型
    await price_model.initialize_model()
    
    # 生成训练数据
    n_train = 1000
    train_features = [generate_market_features() for _ in range(n_train)]
    train_prices = generate_price_sequence(n_train)
    
    # 训练模型
    await price_model.update_model(train_features, train_prices)
    
    # 生成测试数据
    n_test = 100
    test_features = [generate_market_features() for _ in range(n_test)]
    test_prices = generate_price_sequence(n_test)
    
    # 执行预测和验证
    errors = []
    for features, actual_price in zip(test_features, test_prices):
        prediction = await price_model.predict(features)
        validation = await price_model.validate_prediction(prediction, actual_price)
        errors.append(validation['relative_error'])
    
    # 验证性能
    mean_error = np.mean(errors)
    assert mean_error < 0.01  # 平均相对误差应小于1%
    
    # 验证预测指标
    metrics = price_model.get_prediction_metrics()
    assert 'mse' in metrics
    assert 'mae' in metrics
    assert metrics['sample_count'] == n_test

async def main():
    """运行所有测试"""
    config = model_config()
    model = PricePredictionModel(config)
    
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
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 