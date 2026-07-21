import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from src.tests.tools.data_generator import TestDataGenerator

@pytest.fixture
def data_generator():
    """创建测试数据生成器实例"""
    return TestDataGenerator(
        config={
            'market_data': {
                'symbols': ['BTC/USDT', 'ETH/USDT', 'XRP/USDT'],
                'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'features': ['open', 'high', 'low', 'close', 'volume', 'trades']
            },
            'trade_data': {
                'order_types': ['market', 'limit', 'stop'],
                'side_types': ['buy', 'sell'],
                'status_types': ['open', 'filled', 'cancelled', 'rejected'],
                'price_range': {'min': 100, 'max': 1000},
                'volume_range': {'min': 0.1, 'max': 10}
            },
            'system_data': {
                'metrics': ['cpu', 'memory', 'disk', 'network'],
                'status_levels': ['normal', 'warning', 'error', 'critical'],
                'components': ['trading', 'data', 'strategy', 'model']
            }
        }
    )

class TestDataGenerator:
    """测试数据生成器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, data_generator):
        """测试数据生成器初始化"""
        assert isinstance(data_generator.config, dict)
        assert 'market_data' in data_generator.config
        assert 'trade_data' in data_generator.config
        assert 'system_data' in data_generator.config
        
    @pytest.mark.asyncio
    async def test_generate_market_data(self, data_generator):
        """测试生成市场数据"""
        # 生成市场数据
        market_data = await data_generator.generate_market_data(
            symbol='BTC/USDT',
            timeframe='1h',
            start_date='2024-01-01',
            end_date='2024-01-31'
        )
        
        # 验证数据
        assert isinstance(market_data, pd.DataFrame)
        assert len(market_data) > 0
        assert all(col in market_data.columns for col in ['open', 'high', 'low', 'close', 'volume', 'trades'])
        assert isinstance(market_data.index, pd.DatetimeIndex)
        
    @pytest.mark.asyncio
    async def test_generate_trade_data(self, data_generator):
        """测试生成交易数据"""
        # 生成交易数据
        trade_data = await data_generator.generate_trade_data(
            symbol='BTC/USDT',
            num_trades=100
        )
        
        # 验证数据
        assert isinstance(trade_data, pd.DataFrame)
        assert len(trade_data) == 100
        assert all(col in trade_data.columns for col in ['order_id', 'type', 'side', 'price', 'volume', 'status'])
        assert all(trade_data['price'].between(100, 1000))
        assert all(trade_data['volume'].between(0.1, 10))
        
    @pytest.mark.asyncio
    async def test_generate_system_data(self, data_generator):
        """测试生成系统数据"""
        # 生成系统数据
        system_data = await data_generator.generate_system_data(
            duration_hours=24,
            interval_minutes=5
        )
        
        # 验证数据
        assert isinstance(system_data, pd.DataFrame)
        assert len(system_data) == 288  # 24 * 60 / 5
        assert all(col in system_data.columns for col in ['timestamp', 'component', 'metric', 'value', 'status'])
        assert all(system_data['status'].isin(['normal', 'warning', 'error', 'critical']))
        
    @pytest.mark.asyncio
    async def test_generate_orderbook(self, data_generator):
        """测试生成订单簿数据"""
        # 生成订单簿数据
        orderbook = await data_generator.generate_orderbook(
            symbol='BTC/USDT',
            depth=10
        )
        
        # 验证数据
        assert isinstance(orderbook, dict)
        assert 'bids' in orderbook
        assert 'asks' in orderbook
        assert len(orderbook['bids']) == 10
        assert len(orderbook['asks']) == 10
        assert all(bid[0] < ask[0] for bid, ask in zip(orderbook['bids'], orderbook['asks']))
        
    @pytest.mark.asyncio
    async def test_generate_trade_history(self, data_generator):
        """测试生成交易历史数据"""
        # 生成交易历史数据
        trade_history = await data_generator.generate_trade_history(
            symbol='BTC/USDT',
            num_trades=50
        )
        
        # 验证数据
        assert isinstance(trade_history, pd.DataFrame)
        assert len(trade_history) == 50
        assert all(col in trade_history.columns for col in ['timestamp', 'price', 'volume', 'side'])
        assert all(trade_history['price'].between(100, 1000))
        assert all(trade_history['volume'].between(0.1, 10))
        
    @pytest.mark.asyncio
    async def test_generate_performance_data(self, data_generator):
        """测试生成性能数据"""
        # 生成性能数据
        performance_data = await data_generator.generate_performance_data(
            duration_hours=24,
            interval_minutes=5
        )
        
        # 验证数据
        assert isinstance(performance_data, pd.DataFrame)
        assert len(performance_data) == 288  # 24 * 60 / 5
        assert all(col in performance_data.columns for col in ['timestamp', 'metric', 'value', 'threshold'])
        assert all(performance_data['value'].between(0, 100))
        
    @pytest.mark.asyncio
    async def test_generate_error_data(self, data_generator):
        """测试生成错误数据"""
        # 生成错误数据
        error_data = await data_generator.generate_error_data(
            num_errors=10
        )
        
        # 验证数据
        assert isinstance(error_data, pd.DataFrame)
        assert len(error_data) == 10
        assert all(col in error_data.columns for col in ['timestamp', 'component', 'error_type', 'message', 'severity'])
        assert all(error_data['severity'].isin(['low', 'medium', 'high', 'critical']))
        
    @pytest.mark.asyncio
    async def test_generate_test_scenarios(self, data_generator):
        """测试生成测试场景"""
        # 生成测试场景
        scenarios = await data_generator.generate_test_scenarios(
            num_scenarios=5
        )
        
        # 验证数据
        assert isinstance(scenarios, list)
        assert len(scenarios) == 5
        assert all(isinstance(scenario, dict) for scenario in scenarios)
        assert all('description' in scenario for scenario in scenarios)
        assert all('data' in scenario for scenario in scenarios)
        
    @pytest.mark.asyncio
    async def test_error_handling(self, data_generator):
        """测试错误处理"""
        # 测试无效的时间范围
        with pytest.raises(ValueError):
            await data_generator.generate_market_data(
                symbol='BTC/USDT',
                timeframe='1h',
                start_date='2024-01-31',
                end_date='2024-01-01'
            )
            
        # 测试无效的深度
        with pytest.raises(ValueError):
            await data_generator.generate_orderbook(
                symbol='BTC/USDT',
                depth=-1
            )
            
        # 测试无效的交易数量
        with pytest.raises(ValueError):
            await data_generator.generate_trade_data(
                symbol='BTC/USDT',
                num_trades=0
            )
            
    @pytest.mark.asyncio
    async def test_concurrent_data_generation(self, data_generator):
        """测试并发数据生成"""
        # 并发生成不同类型的数据
        import asyncio
        tasks = [
            data_generator.generate_market_data('BTC/USDT', '1h', '2024-01-01', '2024-01-31'),
            data_generator.generate_trade_data('BTC/USDT', 100),
            data_generator.generate_system_data(24, 5)
        ]
        
        # 等待所有数据生成完成
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 3
        assert isinstance(results[0], pd.DataFrame)
        assert isinstance(results[1], pd.DataFrame)
        assert isinstance(results[2], pd.DataFrame) 