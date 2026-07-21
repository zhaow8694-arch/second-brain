import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.interface.model_interface import ModelInterface
from src.model.base_model import BaseModel

class TestModel(BaseModel):
    """测试模型类"""
    def __init__(self, name: str, parameters: Dict):
        super().__init__(name, parameters)
        
    async def initialize(self):
        """初始化模型"""
        pass
        
    async def train(self, X: np.ndarray, y: np.ndarray):
        """训练模型"""
        pass
        
    async def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return np.zeros(len(X))
        
    async def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """评估模型"""
        return {
            'accuracy': 0.5,
            'precision': 0.5,
            'recall': 0.5,
            'f1_score': 0.5
        }

@pytest.fixture
def model_interface():
    """创建模型接口实例"""
    return ModelInterface(
        interface_name='test_interface',
        config={
            'max_models': 10,
            'model_cache_dir': 'test_cache',
            'evaluation_metrics': ['accuracy', 'precision', 'recall', 'f1_score']
        }
    )

@pytest.fixture
def test_model():
    """创建测试模型实例"""
    return TestModel(
        name='test_model',
        parameters={
            'model_type': 'classification',
            'input_size': 10,
            'output_size': 2,
            'learning_rate': 0.001,
            'batch_size': 32
        }
    )

@pytest.fixture
def sample_data():
    """生成样本数据"""
    n_samples = 1000
    X = np.random.randn(n_samples, 10)
    y = np.random.randint(0, 2, n_samples)
    return X, y

class TestModelInterface:
    """模型接口测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, model_interface):
        """测试接口初始化"""
        assert model_interface.interface_name == 'test_interface'
        assert model_interface.config['max_models'] == 10
        assert model_interface.config['model_cache_dir'] == 'test_cache'
        assert 'evaluation_metrics' in model_interface.config
        
    @pytest.mark.asyncio
    async def test_register_model(self, model_interface, test_model):
        """测试模型注册"""
        # 注册模型
        success = await model_interface.register_model(test_model)
        
        # 验证注册结果
        assert success is True
        assert test_model.name in model_interface.get_registered_models()
        
    @pytest.mark.asyncio
    async def test_unregister_model(self, model_interface, test_model):
        """测试模型注销"""
        # 注册模型
        await model_interface.register_model(test_model)
        
        # 注销模型
        success = await model_interface.unregister_model(test_model.name)
        
        # 验证注销结果
        assert success is True
        assert test_model.name not in model_interface.get_registered_models()
        
    @pytest.mark.asyncio
    async def test_update_model_parameters(self, model_interface, test_model):
        """测试更新模型参数"""
        # 注册模型
        await model_interface.register_model(test_model)
        
        # 更新参数
        new_parameters = {
            'model_type': 'regression',
            'input_size': 20,
            'output_size': 1,
            'learning_rate': 0.0001,
            'batch_size': 64
        }
        
        success = await model_interface.update_model_parameters(
            model_name=test_model.name,
            parameters=new_parameters
        )
        
        # 验证更新结果
        assert success is True
        assert model_interface.get_model_parameters(test_model.name) == new_parameters
        
    @pytest.mark.asyncio
    async def test_train_model(self, model_interface, test_model, sample_data):
        """测试模型训练"""
        # 注册模型
        await model_interface.register_model(test_model)
        
        # 训练模型
        X, y = sample_data
        success = await model_interface.train_model(test_model.name, X, y)
        
        # 验证训练结果
        assert success is True
        assert model_interface.is_model_trained(test_model.name) is True
        
    @pytest.mark.asyncio
    async def test_predict(self, model_interface, test_model, sample_data):
        """测试模型预测"""
        # 注册并训练模型
        await model_interface.register_model(test_model)
        X, y = sample_data
        await model_interface.train_model(test_model.name, X, y)
        
        # 预测
        X_test = np.random.randn(100, 10)
        predictions = await model_interface.predict(test_model.name, X_test)
        
        # 验证预测结果
        assert isinstance(predictions, np.ndarray)
        assert len(predictions) == len(X_test)
        
    @pytest.mark.asyncio
    async def test_evaluate_model(self, model_interface, test_model, sample_data):
        """测试模型评估"""
        # 注册并训练模型
        await model_interface.register_model(test_model)
        X, y = sample_data
        await model_interface.train_model(test_model.name, X, y)
        
        # 评估模型
        metrics = await model_interface.evaluate_model(test_model.name, X, y)
        
        # 验证评估结果
        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        
    @pytest.mark.asyncio
    async def test_save_model(self, model_interface, test_model, sample_data):
        """测试保存模型"""
        # 注册并训练模型
        await model_interface.register_model(test_model)
        X, y = sample_data
        await model_interface.train_model(test_model.name, X, y)
        
        # 保存模型
        success = await model_interface.save_model(test_model.name)
        
        # 验证保存结果
        assert success is True
        assert model_interface.is_model_saved(test_model.name) is True
        
    @pytest.mark.asyncio
    async def test_load_model(self, model_interface, test_model, sample_data):
        """测试加载模型"""
        # 注册、训练并保存模型
        await model_interface.register_model(test_model)
        X, y = sample_data
        await model_interface.train_model(test_model.name, X, y)
        await model_interface.save_model(test_model.name)
        
        # 加载模型
        success = await model_interface.load_model(test_model.name)
        
        # 验证加载结果
        assert success is True
        assert model_interface.is_model_loaded(test_model.name) is True
        
    @pytest.mark.asyncio
    async def test_get_model_status(self, model_interface, test_model):
        """测试获取模型状态"""
        # 注册模型
        await model_interface.register_model(test_model)
        
        # 获取模型状态
        status = model_interface.get_model_status(test_model.name)
        
        # 验证状态信息
        assert isinstance(status, dict)
        assert 'is_trained' in status
        assert 'is_saved' in status
        assert 'is_loaded' in status
        assert 'last_update' in status
        
    @pytest.mark.asyncio
    async def test_error_handling(self, model_interface):
        """测试错误处理"""
        # 测试注册不存在的模型
        with pytest.raises(ValueError):
            await model_interface.train_model('non_existent_model', np.array([]), np.array([]))
            
        # 测试重复注册模型
        test_model = TestModel('test_model', {})
        await model_interface.register_model(test_model)
        with pytest.raises(ValueError):
            await model_interface.register_model(test_model)
            
    @pytest.mark.asyncio
    async def test_concurrent_model_execution(self, model_interface):
        """测试并发模型执行"""
        # 创建多个模型
        models = []
        for i in range(3):
            model = TestModel(f'test_model_{i}', {})
            models.append(model)
            await model_interface.register_model(model)
            
        # 训练所有模型
        X, y = np.random.randn(100, 10), np.random.randint(0, 2, 100)
        for model in models:
            await model_interface.train_model(model.name, X, y)
            
        # 验证所有模型都已训练
        for model in models:
            assert model_interface.is_model_trained(model.name) is True 