import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.interface.data_interface import DataInterface

@pytest.fixture
def data_interface():
    """创建数据接口实例"""
    return DataInterface(
        data_source='test_source',
        api_key='test_api_key',
        api_secret='test_api_secret',
        cache_dir='test_cache'
    )

@pytest.fixture
def test_instrument():
    """创建测试交易品种"""
    return {
        'symbol': 'BTC/USDT',
        'base_currency': 'BTC',
        'quote_currency': 'USDT',
        'price_precision': 2,
        'quantity_precision': 6
    }

@pytest.fixture
def sample_market_data():
    """生成样本市场数据"""
    n_samples = 1000
    timestamps = pd.date_range(start='2024-01-01', periods=n_samples, freq='1min')
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'open': np.random.normal(50000, 1000, n_samples),
        'high': np.random.normal(50100, 1000, n_samples),
        'low': np.random.normal(49900, 1000, n_samples),
        'close': np.random.normal(50000, 1000, n_samples),
        'volume': np.random.normal(100, 20, n_samples),
        'trades': np.random.randint(100, 1000, n_samples)
    })
    
    return data

class TestDataInterface:
    """数据接口测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, data_interface):
        """测试接口初始化"""
        assert data_interface.data_source == 'test_source'
        assert data_interface.api_key == 'test_api_key'
        assert data_interface.api_secret == 'test_api_secret'
        assert data_interface.cache_dir == 'test_cache'
        
    @pytest.mark.asyncio
    async def test_connect(self, data_interface):
        """测试接口连接"""
        # 连接数据源
        success = await data_interface.connect()
        
        # 验证连接结果
        assert success is True
        assert data_interface.is_connected() is True
        
    @pytest.mark.asyncio
    async def test_authenticate(self, data_interface):
        """测试接口认证"""
        # 连接数据源
        await data_interface.connect()
        
        # 进行认证
        success = await data_interface.authenticate()
        
        # 验证认证结果
        assert success is True
        assert data_interface.is_authenticated() is True
        
    @pytest.mark.asyncio
    async def test_get_historical_data(self, data_interface, test_instrument):
        """测试获取历史数据"""
        # 连接并认证
        await data_interface.connect()
        await data_interface.authenticate()
        
        # 获取历史数据
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        historical_data = await data_interface.get_historical_data(
            symbol=test_instrument['symbol'],
            start_time=start_time,
            end_time=end_time,
            timeframe='1h'
        )
        
        # 验证历史数据
        assert isinstance(historical_data, pd.DataFrame)
        assert len(historical_data) > 0
        assert all(col in historical_data.columns for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
    @pytest.mark.asyncio
    async def test_get_realtime_data(self, data_interface, test_instrument):
        """测试获取实时数据"""
        # 连接并认证
        await data_interface.connect()
        await data_interface.authenticate()
        
        # 获取实时数据
        realtime_data = await data_interface.get_realtime_data(test_instrument['symbol'])
        
        # 验证实时数据
        assert isinstance(realtime_data, dict)
        assert 'timestamp' in realtime_data
        assert 'last_price' in realtime_data
        assert 'volume' in realtime_data
        
    @pytest.mark.asyncio
    async def test_get_orderbook(self, data_interface, test_instrument):
        """测试获取订单簿"""
        # 连接并认证
        await data_interface.connect()
        await data_interface.authenticate()
        
        # 获取订单簿
        orderbook = await data_interface.get_orderbook(test_instrument['symbol'])
        
        # 验证订单簿
        assert isinstance(orderbook, dict)
        assert 'bids' in orderbook
        assert 'asks' in orderbook
        assert len(orderbook['bids']) > 0
        assert len(orderbook['asks']) > 0
        
    @pytest.mark.asyncio
    async def test_get_trades(self, data_interface, test_instrument):
        """测试获取成交记录"""
        # 连接并认证
        await data_interface.connect()
        await data_interface.authenticate()
        
        # 获取成交记录
        trades = await data_interface.get_trades(
            symbol=test_instrument['symbol'],
            limit=100
        )
        
        # 验证成交记录
        assert isinstance(trades, list)
        if len(trades) > 0:
            assert 'timestamp' in trades[0]
            assert 'price' in trades[0]
            assert 'quantity' in trades[0]
            assert 'side' in trades[0]
            
    @pytest.mark.asyncio
    async def test_preprocess_data(self, data_interface, sample_market_data):
        """测试数据预处理"""
        # 预处理数据
        processed_data = await data_interface.preprocess_data(sample_market_data)
        
        # 验证预处理结果
        assert isinstance(processed_data, pd.DataFrame)
        assert len(processed_data) == len(sample_market_data)
        assert not processed_data.isnull().any().any()
        
    @pytest.mark.asyncio
    async def test_save_data(self, data_interface, sample_market_data):
        """测试数据保存"""
        # 保存数据
        success = await data_interface.save_data(
            data=sample_market_data,
            symbol='BTC/USDT',
            timeframe='1h'
        )
        
        # 验证保存结果
        assert success is True
        
    @pytest.mark.asyncio
    async def test_load_data(self, data_interface):
        """测试数据加载"""
        # 加载数据
        loaded_data = await data_interface.load_data(
            symbol='BTC/USDT',
            timeframe='1h',
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now()
        )
        
        # 验证加载结果
        assert isinstance(loaded_data, pd.DataFrame)
        assert len(loaded_data) > 0
        assert all(col in loaded_data.columns for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
    @pytest.mark.asyncio
    async def test_validate_data(self, data_interface, sample_market_data):
        """测试数据验证"""
        # 验证数据
        validation_result = await data_interface.validate_data(sample_market_data)
        
        # 验证结果
        assert isinstance(validation_result, dict)
        assert 'is_valid' in validation_result
        assert 'errors' in validation_result
        assert validation_result['is_valid'] is True
        
    @pytest.mark.asyncio
    async def test_error_handling(self, data_interface):
        """测试错误处理"""
        # 测试无效的数据源
        invalid_interface = DataInterface(
            data_source='invalid_source',
            api_key='test_api_key',
            api_secret='test_api_secret',
            cache_dir='test_cache'
        )
        
        # 尝试连接
        success = await invalid_interface.connect()
        assert success is False
        
        # 测试无效的交易品种
        with pytest.raises(ValueError):
            await data_interface.get_historical_data('INVALID/SYMBOL')
            
    @pytest.mark.asyncio
    async def test_rate_limiting(self, data_interface, test_instrument):
        """测试速率限制"""
        # 连接数据源
        await data_interface.connect()
        
        # 快速发送多个请求
        tasks = []
        for _ in range(10):
            tasks.append(data_interface.get_realtime_data(test_instrument['symbol']))
            
        # 等待所有请求完成
        results = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功完成
        assert len(results) == 10
        assert all(isinstance(result, dict) for result in results) 