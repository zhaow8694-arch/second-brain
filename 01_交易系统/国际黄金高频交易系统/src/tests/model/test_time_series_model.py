import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.model.time_series_model import TimeSeriesModel

@pytest.fixture
def time_series_model():
    """创建时间序列模型实例"""
    return TimeSeriesModel(
        model_type='lstm',
        input_size=10,
        hidden_size=64,
        num_layers=2,
        output_size=1,
        learning_rate=0.001,
        batch_size=32,
        epochs=100,
        early_stopping_patience=10,
        forecast_horizon=5  # 预测未来5个时间步
    )

@pytest.fixture
def sample_training_data():
    """生成样本训练数据"""
    # 生成时间序列数据
    n_samples = 1000
    sequence_length = 10
    
    # 生成特征数据（包含时间特征）
    X = np.random.normal(0, 1, (n_samples, sequence_length, 5))  # 5个特征
    # 添加时间特征
    timestamps = pd.date_range(start='2024-01-01', periods=n_samples, freq='1min')
    time_features = np.column_stack([
        timestamps.hour.values,
        timestamps.dayofweek.values,
        timestamps.month.values,
        timestamps.dayofyear.values
    ])
    X = np.concatenate([X, time_features.reshape(n_samples, 1, 4)], axis=2)
    
    # 生成目标数据（带有时间依赖性的序列）
    y = np.sum(X[:, :, 0:2], axis=2) + np.sin(np.arange(n_samples) * 0.1) + np.random.normal(0, 0.1, n_samples)
    
    return X, y

@pytest.fixture
def sample_test_data():
    """生成样本测试数据"""
    # 生成时间序列数据
    n_samples = 200
    sequence_length = 10
    
    # 生成特征数据（包含时间特征）
    X = np.random.normal(0, 1, (n_samples, sequence_length, 5))  # 5个特征
    # 添加时间特征
    timestamps = pd.date_range(start='2024-01-02', periods=n_samples, freq='1min')
    time_features = np.column_stack([
        timestamps.hour.values,
        timestamps.dayofweek.values,
        timestamps.month.values,
        timestamps.dayofyear.values
    ])
    X = np.concatenate([X, time_features.reshape(n_samples, 1, 4)], axis=2)
    
    # 生成目标数据
    y = np.sum(X[:, :, 0:2], axis=2) + np.sin(np.arange(n_samples) * 0.1) + np.random.normal(0, 0.1, n_samples)
    
    return X, y

class TestTimeSeriesModel:
    """时间序列模型测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, time_series_model):
        """测试模型初始化"""
        assert time_series_model.model_type == 'lstm'
        assert time_series_model.input_size == 10
        assert time_series_model.hidden_size == 64
        assert time_series_model.num_layers == 2
        assert time_series_model.output_size == 1
        assert time_series_model.learning_rate == 0.001
        assert time_series_model.batch_size == 32
        assert time_series_model.epochs == 100
        assert time_series_model.early_stopping_patience == 10
        assert time_series_model.forecast_horizon == 5
        
    @pytest.mark.asyncio
    async def test_build_model(self, time_series_model):
        """测试模型构建"""
        # 构建模型
        model = await time_series_model.build_model()
        
        # 验证模型结构
        assert model is not None
        assert hasattr(model, 'forward')
        assert hasattr(model, 'parameters')
        
    @pytest.mark.asyncio
    async def test_train_model(self, time_series_model, sample_training_data):
        """测试模型训练"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        history = await time_series_model.train_model(X_train, y_train)
        
        # 验证训练历史
        assert isinstance(history, dict)
        assert 'loss' in history
        assert 'val_loss' in history
        assert len(history['loss']) > 0
        assert len(history['val_loss']) > 0
        
    @pytest.mark.asyncio
    async def test_predict(self, time_series_model, sample_training_data, sample_test_data):
        """测试模型预测"""
        X_train, y_train = sample_training_data
        X_test, y_test = sample_test_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 进行预测
        predictions = await time_series_model.predict(X_test)
        
        # 验证预测结果
        assert isinstance(predictions, np.ndarray)
        assert predictions.shape == (len(X_test), time_series_model.output_size)
        
    @pytest.mark.asyncio
    async def test_forecast(self, time_series_model, sample_training_data):
        """测试模型预测未来值"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 预测未来值
        last_sequence = X_train[-1:]
        forecast = await time_series_model.forecast(last_sequence)
        
        # 验证预测结果
        assert isinstance(forecast, np.ndarray)
        assert forecast.shape == (time_series_model.forecast_horizon, time_series_model.output_size)
        
    @pytest.mark.asyncio
    async def test_evaluate_model(self, time_series_model, sample_training_data, sample_test_data):
        """测试模型评估"""
        X_train, y_train = sample_training_data
        X_test, y_test = sample_test_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 评估模型
        metrics = await time_series_model.evaluate_model(X_test, y_test)
        
        # 验证评估指标
        assert isinstance(metrics, dict)
        assert 'mse' in metrics
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert 'mape' in metrics  # 时间序列特有的评估指标
        assert all(isinstance(value, float) for value in metrics.values())
        
    @pytest.mark.asyncio
    async def test_save_and_load_model(self, time_series_model, sample_training_data):
        """测试模型保存和加载"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 保存模型
        model_path = "test_time_series_model.pth"
        await time_series_model.save_model(model_path)
        
        # 加载模型
        loaded_model = await time_series_model.load_model(model_path)
        
        # 验证加载的模型
        assert loaded_model is not None
        assert hasattr(loaded_model, 'forward')
        assert hasattr(loaded_model, 'parameters')
        
    @pytest.mark.asyncio
    async def test_model_optimization(self, time_series_model, sample_training_data):
        """测试模型优化"""
        X_train, y_train = sample_training_data
        
        # 优化模型
        optimized_model = await time_series_model.optimize_model(X_train, y_train)
        
        # 验证优化结果
        assert optimized_model is not None
        assert hasattr(optimized_model, 'forward')
        assert hasattr(optimized_model, 'parameters')
        
    @pytest.mark.asyncio
    async def test_feature_importance(self, time_series_model, sample_training_data):
        """测试特征重要性分析"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 计算特征重要性
        importance = await time_series_model.get_feature_importance(X_train)
        
        # 验证特征重要性
        assert isinstance(importance, np.ndarray)
        assert importance.shape == (X_train.shape[2],)
        assert all(imp >= 0 for imp in importance)
        assert sum(importance) == pytest.approx(1.0, rel=1e-6)
        
    @pytest.mark.asyncio
    async def test_model_interpretability(self, time_series_model, sample_training_data):
        """测试模型可解释性分析"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 生成可解释性分析
        interpretation = await time_series_model.interpret_model(X_train)
        
        # 验证可解释性分析结果
        assert isinstance(interpretation, dict)
        assert 'feature_importance' in interpretation
        assert 'partial_dependence' in interpretation
        assert 'shap_values' in interpretation
        assert 'time_dependence' in interpretation  # 时间序列特有的可解释性分析
        
    @pytest.mark.asyncio
    async def test_model_robustness(self, time_series_model, sample_training_data):
        """测试模型鲁棒性"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await time_series_model.train_model(X_train, y_train)
        
        # 测试模型鲁棒性
        robustness_metrics = await time_series_model.test_robustness(X_train)
        
        # 验证鲁棒性指标
        assert isinstance(robustness_metrics, dict)
        assert 'noise_sensitivity' in robustness_metrics
        assert 'adversarial_robustness' in robustness_metrics
        assert 'outlier_sensitivity' in robustness_metrics
        assert 'seasonality_robustness' in robustness_metrics  # 时间序列特有的鲁棒性指标 