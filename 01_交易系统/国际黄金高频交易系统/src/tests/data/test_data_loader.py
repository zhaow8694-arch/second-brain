import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data.data_loader import DataLoader
from src.data.data_validator import DataValidator
from src.data.data_preprocessor import DataPreprocessor

@pytest.fixture
def data_loader():
    """创建数据加载器实例"""
    return DataLoader(
        data_dir="data/market_data",
        cache_dir="data/cache",
        update_interval=3600,
        max_retries=3,
        timeout=30
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

@pytest.fixture
def sample_instrument_info():
    """生成样本合约信息"""
    return {
        'symbol': 'XAUUSD',
        'exchange': 'FOREX',
        'type': 'SPOT',
        'tick_size': 0.1,
        'lot_size': 1,
        'min_trade_volume': 1,
        'max_trade_volume': 100,
        'price_precision': 2,
        'volume_precision': 0,
        'trading_hours': {
            'start': '00:00:00',
            'end': '23:59:59',
            'timezone': 'UTC'
        }
    }

class TestDataLoader:
    """数据加载器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, data_loader):
        """测试数据加载器初始化"""
        assert data_loader.data_dir == "data/market_data"
        assert data_loader.cache_dir == "data/cache"
        assert data_loader.update_interval == 3600
        assert data_loader.max_retries == 3
        assert data_loader.timeout == 30
        
    @pytest.mark.asyncio
    async def test_load_market_data(self, data_loader, sample_market_data):
        """测试加载市场数据"""
        # 模拟数据加载
        data_loader._load_market_data = lambda *args, **kwargs: sample_market_data
        
        # 加载数据
        data = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 验证数据
        assert isinstance(data, pd.DataFrame)
        assert len(data) == len(sample_market_data)
        assert all(col in data.columns for col in sample_market_data.columns)
        
    @pytest.mark.asyncio
    async def test_load_instrument_info(self, data_loader, sample_instrument_info):
        """测试加载合约信息"""
        # 模拟数据加载
        data_loader._load_instrument_info = lambda *args, **kwargs: sample_instrument_info
        
        # 加载合约信息
        info = await data_loader.load_instrument_info('XAUUSD')
        
        # 验证信息
        assert isinstance(info, dict)
        assert info['symbol'] == 'XAUUSD'
        assert info['exchange'] == 'FOREX'
        assert info['type'] == 'SPOT'
        
    @pytest.mark.asyncio
    async def test_load_multiple_symbols(self, data_loader, sample_market_data):
        """测试加载多个合约数据"""
        # 模拟数据加载
        data_loader._load_market_data = lambda *args, **kwargs: sample_market_data
        
        # 加载多个合约数据
        symbols = ['XAUUSD', 'EURUSD', 'GBPUSD']
        data_dict = await data_loader.load_multiple_symbols(
            symbols=symbols,
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 验证数据
        assert isinstance(data_dict, dict)
        assert len(data_dict) == len(symbols)
        assert all(symbol in data_dict for symbol in symbols)
        assert all(isinstance(data, pd.DataFrame) for data in data_dict.values())
        
    @pytest.mark.asyncio
    async def test_data_caching(self, data_loader, sample_market_data):
        """测试数据缓存功能"""
        # 模拟数据加载
        data_loader._load_market_data = lambda *args, **kwargs: sample_market_data
        
        # 首次加载数据
        data1 = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 从缓存加载数据
        data2 = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 验证数据一致性
        pd.testing.assert_frame_equal(data1, data2)
        
    @pytest.mark.asyncio
    async def test_data_update(self, data_loader, sample_market_data):
        """测试数据更新功能"""
        # 模拟数据加载
        data_loader._load_market_data = lambda *args, **kwargs: sample_market_data
        
        # 加载初始数据
        data1 = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 更新数据
        await data_loader.update_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 重新加载数据
        data2 = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 验证数据已更新
        pd.testing.assert_frame_equal(data1, data2)
        
    @pytest.mark.asyncio
    async def test_error_handling(self, data_loader):
        """测试错误处理"""
        # 模拟加载失败
        data_loader._load_market_data = lambda *args, **kwargs: raise Exception("Load failed")
        
        # 验证错误处理
        with pytest.raises(Exception):
            await data_loader.load_market_data(
                symbol='XAUUSD',
                start_time='2024-01-01',
                end_time='2024-01-10',
                timeframe='1min'
            )
            
    @pytest.mark.asyncio
    async def test_data_validation(self, data_loader, sample_market_data):
        """测试数据验证"""
        # 模拟数据加载
        data_loader._load_market_data = lambda *args, **kwargs: sample_market_data
        
        # 加载数据
        data = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 验证数据完整性
        assert not data.isnull().any().any()
        assert data['high'].ge(data['low']).all()
        assert data['close'].between(data['low'], data['high']).all()
        assert data['volume'].ge(0).all()
        
    @pytest.mark.asyncio
    async def test_data_preprocessing(self, data_loader, sample_market_data):
        """测试数据预处理"""
        # 模拟数据加载
        data_loader._load_market_data = lambda *args, **kwargs: sample_market_data
        
        # 加载数据
        data = await data_loader.load_market_data(
            symbol='XAUUSD',
            start_time='2024-01-01',
            end_time='2024-01-10',
            timeframe='1min'
        )
        
        # 验证数据预处理
        assert data.index.name == 'timestamp'
        assert data.index.is_monotonic_increasing
        assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume']) 