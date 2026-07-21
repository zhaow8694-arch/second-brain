import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data.data_transformer import DataTransformer

@pytest.fixture
def data_transformer():
    """创建数据转换器实例"""
    return DataTransformer(
        target_columns=['close', 'volume'],
        feature_columns=['open', 'high', 'low', 'bid_price', 'ask_price'],
        sequence_length=10,
        prediction_horizon=1
    )

@pytest.fixture
def sample_market_data():
    """生成样本市场数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1min')
    data = {
        'timestamp': dates,
        'open': np.random.normal(100, 1, len(dates)),
        'high': np.random.normal(101, 1, len(dates)),
        'low': np.random.normal(99, 1, len(dates)),
        'close': np.random.normal(100, 1, len(dates)),
        'volume': np.random.randint(1000, 10000, len(dates)),
        'bid_price': np.random.normal(99.9, 0.1, len(dates)),
        'ask_price': np.random.normal(100.1, 0.1, len(dates)),
        'bid_volume': np.random.randint(100, 1000, len(dates)),
        'ask_volume': np.random.randint(100, 1000, len(dates))
    }
    return pd.DataFrame(data)

class TestDataTransformer:
    """数据转换器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, data_transformer):
        """测试数据转换器初始化"""
        assert data_transformer.target_columns == ['close', 'volume']
        assert data_transformer.feature_columns == ['open', 'high', 'low', 'bid_price', 'ask_price']
        assert data_transformer.sequence_length == 10
        assert data_transformer.prediction_horizon == 1
        
    @pytest.mark.asyncio
    async def test_prepare_sequences(self, data_transformer, sample_market_data):
        """测试序列准备"""
        # 准备序列数据
        X, y = await data_transformer.prepare_sequences(sample_market_data)
        
        # 验证序列形状
        expected_sequences = len(sample_market_data) - data_transformer.sequence_length
        assert X.shape == (expected_sequences, data_transformer.sequence_length, len(data_transformer.feature_columns))
        assert y.shape == (expected_sequences, len(data_transformer.target_columns))
        
    @pytest.mark.asyncio
    async def test_transform_features(self, data_transformer, sample_market_data):
        """测试特征转换"""
        # 转换特征
        transformed_data = await data_transformer.transform_features(sample_market_data)
        
        # 验证转换结果
        assert isinstance(transformed_data, pd.DataFrame)
        assert all(col in transformed_data.columns for col in data_transformer.feature_columns)
        assert transformed_data.shape[0] == len(sample_market_data)
        
    @pytest.mark.asyncio
    async def test_transform_targets(self, data_transformer, sample_market_data):
        """测试目标变量转换"""
        # 转换目标变量
        transformed_data = await data_transformer.transform_targets(sample_market_data)
        
        # 验证转换结果
        assert isinstance(transformed_data, pd.DataFrame)
        assert all(col in transformed_data.columns for col in data_transformer.target_columns)
        assert transformed_data.shape[0] == len(sample_market_data)
        
    @pytest.mark.asyncio
    async def test_create_time_features(self, data_transformer, sample_market_data):
        """测试时间特征创建"""
        # 创建时间特征
        transformed_data = await data_transformer.create_time_features(sample_market_data)
        
        # 验证时间特征
        assert 'hour' in transformed_data.columns
        assert 'day' in transformed_data.columns
        assert 'month' in transformed_data.columns
        assert 'dayofweek' in transformed_data.columns
        
    @pytest.mark.asyncio
    async def test_create_technical_features(self, data_transformer, sample_market_data):
        """测试技术特征创建"""
        # 创建技术特征
        transformed_data = await data_transformer.create_technical_features(sample_market_data)
        
        # 验证技术特征
        assert 'returns' in transformed_data.columns
        assert 'log_returns' in transformed_data.columns
        assert 'volatility' in transformed_data.columns
        assert 'spread' in transformed_data.columns
        
    @pytest.mark.asyncio
    async def test_create_market_features(self, data_transformer, sample_market_data):
        """测试市场特征创建"""
        # 创建市场特征
        transformed_data = await data_transformer.create_market_features(sample_market_data)
        
        # 验证市场特征
        assert 'volume_ratio' in transformed_data.columns
        assert 'price_range' in transformed_data.columns
        assert 'bid_ask_spread' in transformed_data.columns
        assert 'volume_imbalance' in transformed_data.columns
        
    @pytest.mark.asyncio
    async def test_transform_data(self, data_transformer, sample_market_data):
        """测试完整的数据转换流程"""
        # 执行完整的数据转换
        transformed_data = await data_transformer.transform_data(sample_market_data)
        
        # 验证转换结果
        assert isinstance(transformed_data, pd.DataFrame)
        assert all(col in transformed_data.columns for col in data_transformer.feature_columns)
        assert all(col in transformed_data.columns for col in data_transformer.target_columns)
        assert transformed_data.shape[0] == len(sample_market_data)
        
    @pytest.mark.asyncio
    async def test_inverse_transform(self, data_transformer, sample_market_data):
        """测试反向转换"""
        # 转换数据
        transformed_data = await data_transformer.transform_data(sample_market_data)
        
        # 反向转换
        original_data = await data_transformer.inverse_transform(transformed_data)
        
        # 验证反向转换结果
        assert isinstance(original_data, pd.DataFrame)
        assert original_data.shape == sample_market_data.shape
        pd.testing.assert_frame_equal(original_data, sample_market_data)
        
    @pytest.mark.asyncio
    async def test_transform_batch(self, data_transformer, sample_market_data):
        """测试批量数据转换"""
        # 创建批量数据
        batch_size = 32
        batch_data = sample_market_data.iloc[:batch_size]
        
        # 转换批量数据
        transformed_batch = await data_transformer.transform_batch(batch_data)
        
        # 验证批量转换结果
        assert isinstance(transformed_batch, tuple)
        assert len(transformed_batch) == 2  # X, y
        assert transformed_batch[0].shape[0] == batch_size - data_transformer.sequence_length
        assert transformed_batch[1].shape[0] == batch_size - data_transformer.sequence_length 