import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data.data_preprocessor import DataPreprocessor

@pytest.fixture
def data_preprocessor():
    """创建数据预处理器实例"""
    return DataPreprocessor(
        fill_method='ffill',
        remove_outliers=True,
        outlier_std_threshold=3,
        add_technical_indicators=True,
        add_market_features=True
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

class TestDataPreprocessor:
    """数据预处理器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, data_preprocessor):
        """测试数据预处理器初始化"""
        assert data_preprocessor.fill_method == 'ffill'
        assert data_preprocessor.remove_outliers is True
        assert data_preprocessor.outlier_std_threshold == 3
        assert data_preprocessor.add_technical_indicators is True
        assert data_preprocessor.add_market_features is True
        
    @pytest.mark.asyncio
    async def test_handle_missing_values(self, data_preprocessor, sample_market_data):
        """测试处理缺失值"""
        # 添加一些缺失值
        data = sample_market_data.copy()
        data.loc[10:20, 'close'] = np.nan
        
        # 处理缺失值
        processed_data = await data_preprocessor.handle_missing_values(data)
        
        # 验证结果
        assert not processed_data.isnull().any().any()
        assert processed_data['close'].iloc[10:20].notna().all()
        
    @pytest.mark.asyncio
    async def test_remove_outliers(self, data_preprocessor, sample_market_data):
        """测试异常值处理"""
        # 添加一些异常值
        data = sample_market_data.copy()
        data.loc[10, 'close'] = 1000  # 添加一个明显的异常值
        
        # 处理异常值
        processed_data = await data_preprocessor.remove_outliers(data)
        
        # 验证结果
        assert processed_data['close'].iloc[10] < 1000
        assert processed_data['close'].iloc[10] > 0
        
    @pytest.mark.asyncio
    async def test_add_technical_indicators(self, data_preprocessor, sample_market_data):
        """测试添加技术指标"""
        # 处理数据
        processed_data = await data_preprocessor.add_technical_indicators(sample_market_data)
        
        # 验证技术指标
        assert 'sma_20' in processed_data.columns
        assert 'ema_20' in processed_data.columns
        assert 'rsi_14' in processed_data.columns
        assert 'macd' in processed_data.columns
        assert 'macd_signal' in processed_data.columns
        assert 'macd_hist' in processed_data.columns
        assert 'bb_upper' in processed_data.columns
        assert 'bb_middle' in processed_data.columns
        assert 'bb_lower' in processed_data.columns
        
    @pytest.mark.asyncio
    async def test_add_market_features(self, data_preprocessor, sample_market_data):
        """测试添加市场特征"""
        # 处理数据
        processed_data = await data_preprocessor.add_market_features(sample_market_data)
        
        # 验证市场特征
        assert 'returns' in processed_data.columns
        assert 'log_returns' in processed_data.columns
        assert 'volatility' in processed_data.columns
        assert 'spread' in processed_data.columns
        assert 'volume_ratio' in processed_data.columns
        
    @pytest.mark.asyncio
    async def test_normalize_features(self, data_preprocessor, sample_market_data):
        """测试特征标准化"""
        # 添加一些特征
        data = await data_preprocessor.add_technical_indicators(sample_market_data)
        data = await data_preprocessor.add_market_features(data)
        
        # 标准化特征
        processed_data = await data_preprocessor.normalize_features(data)
        
        # 验证标准化结果
        numeric_columns = processed_data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            assert processed_data[col].mean() < 1e-10
            assert abs(processed_data[col].std() - 1) < 1e-10
            
    @pytest.mark.asyncio
    async def test_preprocess_data(self, data_preprocessor, sample_market_data):
        """测试完整的数据预处理流程"""
        # 执行完整的预处理流程
        processed_data = await data_preprocessor.preprocess_data(sample_market_data)
        
        # 验证预处理结果
        assert not processed_data.isnull().any().any()
        assert processed_data.index.name == 'timestamp'
        assert processed_data.index.is_monotonic_increasing
        assert all(col in processed_data.columns for col in [
            'open', 'high', 'low', 'close', 'volume',
            'sma_20', 'ema_20', 'rsi_14', 'macd',
            'returns', 'log_returns', 'volatility'
        ])
        
    @pytest.mark.asyncio
    async def test_feature_selection(self, data_preprocessor, sample_market_data):
        """测试特征选择"""
        # 添加所有特征
        data = await data_preprocessor.add_technical_indicators(sample_market_data)
        data = await data_preprocessor.add_market_features(data)
        
        # 选择特征
        selected_features = ['close', 'volume', 'sma_20', 'rsi_14', 'returns']
        processed_data = await data_preprocessor.select_features(data, selected_features)
        
        # 验证特征选择结果
        assert all(col in processed_data.columns for col in selected_features)
        assert len(processed_data.columns) == len(selected_features)
        
    @pytest.mark.asyncio
    async def test_time_series_split(self, data_preprocessor, sample_market_data):
        """测试时间序列分割"""
        # 预处理数据
        processed_data = await data_preprocessor.preprocess_data(sample_market_data)
        
        # 分割数据
        train_data, test_data = await data_preprocessor.time_series_split(
            processed_data,
            test_size=0.2
        )
        
        # 验证分割结果
        assert len(train_data) + len(test_data) == len(processed_data)
        assert train_data.index[-1] < test_data.index[0]
        assert len(test_data) / len(processed_data) == pytest.approx(0.2, rel=1e-2) 