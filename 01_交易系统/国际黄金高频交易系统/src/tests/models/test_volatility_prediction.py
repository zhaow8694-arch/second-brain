import pytest
import torch
import numpy as np
from models.volatility_prediction import VolatilityPredictionModel
from ..data_generators import generate_market_data

@pytest.fixture
def volatility_model(model_config):
    """创建波动率预测模型实例"""
    return VolatilityPredictionModel(model_config)

class TestVolatilityPrediction:
    """波动率预测模型测试类"""
    
    async def test_model_initialization(self, volatility_model):
        """测试模型初始化"""
        await volatility_model.initialize_model()
        assert isinstance(volatility_model.model.lstm, torch.nn.LSTM)
        assert isinstance(volatility_model.optimizer, torch.optim.Optimizer)
        assert volatility_model.feature_scaler is not None
    
    async def test_feature_preprocessing(self, volatility_model):
        """测试特征预处理"""
        features_list, _ = generate_market_data(n_points=15)
        processed_features = await volatility_model.preprocess_features(features_list[0])
        assert isinstance(processed_features, np.ndarray)
        assert processed_features.shape[1] == len(volatility_model.config.input_features)
    
    async def test_prediction_workflow(self, volatility_model):
        """测试完整预测流程"""
        await volatility_model.initialize_model()
        
        # 训练数据
        train_features, train_labels = generate_market_data(n_points=100)
        await volatility_model.update_model(train_features, train_labels)
        
        # 预测
        test_features, test_labels = generate_market_data(n_points=10)
        prediction = await volatility_model.predict(test_features[-1])
        
        # 验证
        validation = await volatility_model.validate_prediction(
            prediction, test_labels[-1]
        )
        
        # 检查结果
        assert prediction.predicted_value > 0
        assert 0 <= prediction.confidence <= 1
        assert isinstance(validation['error'], float)
        assert len(volatility_model.prediction_history) > 0
    
    async def test_model_performance(self, volatility_model):
        """测试模型性能"""
        await volatility_model.initialize_model()
        
        # 训练和测试
        train_features, train_labels = generate_market_data(n_points=200)
        await volatility_model.update_model(train_features, train_labels)
        
        test_features, test_labels = generate_market_data(n_points=50)
        errors = []
        
        for features, actual_vol in zip(
            test_features[volatility_model.sequence_length:],
            test_labels[volatility_model.sequence_length-1:]
        ):
            prediction = await volatility_model.predict(features)
            validation = await volatility_model.validate_prediction(prediction, actual_vol)
            errors.append(validation['relative_error'])
        
        mean_error = np.mean(errors)
        assert mean_error < 0.2  # 相对误差应小于20% 