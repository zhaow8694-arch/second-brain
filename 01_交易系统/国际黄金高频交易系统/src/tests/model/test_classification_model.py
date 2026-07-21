import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.model.classification_model import ClassificationModel

@pytest.fixture
def classification_model():
    """创建分类模型实例"""
    return ClassificationModel(
        model_type='lstm',
        input_size=10,
        hidden_size=64,
        num_layers=2,
        num_classes=3,  # 3分类问题
        learning_rate=0.001,
        batch_size=32,
        epochs=100,
        early_stopping_patience=10
    )

@pytest.fixture
def sample_training_data():
    """生成样本训练数据"""
    # 生成时间序列数据
    n_samples = 1000
    sequence_length = 10
    
    # 生成特征数据
    X = np.random.normal(0, 1, (n_samples, sequence_length, 5))  # 5个特征
    # 生成分类标签（3类）
    y = np.random.randint(0, 3, n_samples)
    
    return X, y

@pytest.fixture
def sample_test_data():
    """生成样本测试数据"""
    # 生成时间序列数据
    n_samples = 200
    sequence_length = 10
    
    # 生成特征数据
    X = np.random.normal(0, 1, (n_samples, sequence_length, 5))  # 5个特征
    # 生成分类标签
    y = np.random.randint(0, 3, n_samples)
    
    return X, y

class TestClassificationModel:
    """分类模型测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, classification_model):
        """测试模型初始化"""
        assert classification_model.model_type == 'lstm'
        assert classification_model.input_size == 10
        assert classification_model.hidden_size == 64
        assert classification_model.num_layers == 2
        assert classification_model.num_classes == 3
        assert classification_model.learning_rate == 0.001
        assert classification_model.batch_size == 32
        assert classification_model.epochs == 100
        assert classification_model.early_stopping_patience == 10
        
    @pytest.mark.asyncio
    async def test_build_model(self, classification_model):
        """测试模型构建"""
        # 构建模型
        model = await classification_model.build_model()
        
        # 验证模型结构
        assert model is not None
        assert hasattr(model, 'forward')
        assert hasattr(model, 'parameters')
        
    @pytest.mark.asyncio
    async def test_train_model(self, classification_model, sample_training_data):
        """测试模型训练"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        history = await classification_model.train_model(X_train, y_train)
        
        # 验证训练历史
        assert isinstance(history, dict)
        assert 'loss' in history
        assert 'val_loss' in history
        assert 'accuracy' in history
        assert 'val_accuracy' in history
        assert len(history['loss']) > 0
        assert len(history['val_loss']) > 0
        
    @pytest.mark.asyncio
    async def test_predict(self, classification_model, sample_training_data, sample_test_data):
        """测试模型预测"""
        X_train, y_train = sample_training_data
        X_test, y_test = sample_test_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 进行预测
        predictions = await classification_model.predict(X_test)
        
        # 验证预测结果
        assert isinstance(predictions, np.ndarray)
        assert predictions.shape == (len(X_test),)
        assert all(pred in range(classification_model.num_classes) for pred in predictions)
        
    @pytest.mark.asyncio
    async def test_predict_proba(self, classification_model, sample_training_data, sample_test_data):
        """测试概率预测"""
        X_train, y_train = sample_training_data
        X_test, y_test = sample_test_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 进行概率预测
        probabilities = await classification_model.predict_proba(X_test)
        
        # 验证概率预测结果
        assert isinstance(probabilities, np.ndarray)
        assert probabilities.shape == (len(X_test), classification_model.num_classes)
        assert np.allclose(np.sum(probabilities, axis=1), 1.0)
        assert np.all(probabilities >= 0) and np.all(probabilities <= 1)
        
    @pytest.mark.asyncio
    async def test_evaluate_model(self, classification_model, sample_training_data, sample_test_data):
        """测试模型评估"""
        X_train, y_train = sample_training_data
        X_test, y_test = sample_test_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 评估模型
        metrics = await classification_model.evaluate_model(X_test, y_test)
        
        # 验证评估指标
        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'confusion_matrix' in metrics
        assert all(isinstance(value, (float, np.ndarray)) for value in metrics.values())
        
    @pytest.mark.asyncio
    async def test_save_and_load_model(self, classification_model, sample_training_data):
        """测试模型保存和加载"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 保存模型
        model_path = "test_classification_model.pth"
        await classification_model.save_model(model_path)
        
        # 加载模型
        loaded_model = await classification_model.load_model(model_path)
        
        # 验证加载的模型
        assert loaded_model is not None
        assert hasattr(loaded_model, 'forward')
        assert hasattr(loaded_model, 'parameters')
        
    @pytest.mark.asyncio
    async def test_model_optimization(self, classification_model, sample_training_data):
        """测试模型优化"""
        X_train, y_train = sample_training_data
        
        # 优化模型
        optimized_model = await classification_model.optimize_model(X_train, y_train)
        
        # 验证优化结果
        assert optimized_model is not None
        assert hasattr(optimized_model, 'forward')
        assert hasattr(optimized_model, 'parameters')
        
    @pytest.mark.asyncio
    async def test_feature_importance(self, classification_model, sample_training_data):
        """测试特征重要性分析"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 计算特征重要性
        importance = await classification_model.get_feature_importance(X_train)
        
        # 验证特征重要性
        assert isinstance(importance, np.ndarray)
        assert importance.shape == (X_train.shape[2],)
        assert all(imp >= 0 for imp in importance)
        assert sum(importance) == pytest.approx(1.0, rel=1e-6)
        
    @pytest.mark.asyncio
    async def test_model_interpretability(self, classification_model, sample_training_data):
        """测试模型可解释性分析"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 生成可解释性分析
        interpretation = await classification_model.interpret_model(X_train)
        
        # 验证可解释性分析结果
        assert isinstance(interpretation, dict)
        assert 'feature_importance' in interpretation
        assert 'partial_dependence' in interpretation
        assert 'shap_values' in interpretation
        
    @pytest.mark.asyncio
    async def test_model_robustness(self, classification_model, sample_training_data):
        """测试模型鲁棒性"""
        X_train, y_train = sample_training_data
        
        # 训练模型
        await classification_model.train_model(X_train, y_train)
        
        # 测试模型鲁棒性
        robustness_metrics = await classification_model.test_robustness(X_train)
        
        # 验证鲁棒性指标
        assert isinstance(robustness_metrics, dict)
        assert 'noise_sensitivity' in robustness_metrics
        assert 'adversarial_robustness' in robustness_metrics
        assert 'outlier_sensitivity' in robustness_metrics 