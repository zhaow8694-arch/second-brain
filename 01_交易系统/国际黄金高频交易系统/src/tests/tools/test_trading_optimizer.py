import pytest
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.tests.tools.trading_optimizer import TradingOptimizer
from src.tests.tools.performance_tester import PerformanceTester

@pytest.fixture
def config(test_config: Dict[str, Any]) -> Dict[str, Any]:
    """测试配置"""
    return test_config

@pytest.fixture
async def optimizer(config: Dict[str, Any]) -> TradingOptimizer:
    """交易优化器"""
    async with TradingOptimizer(config) as opt:
        yield opt

@pytest.fixture
async def tester(config: Dict[str, Any]) -> PerformanceTester:
    """性能测试器"""
    async with PerformanceTester(config) as t:
        yield t

@pytest.mark.asyncio
async def test_orderbook_optimization(optimizer: TradingOptimizer):
    """测试订单簿优化"""
    # 生成测试数据
    orderbook_data = pd.DataFrame({
        'side': np.random.choice(['buy', 'sell'], 1000),
        'price': np.random.uniform(1800, 1900, 1000),
        'quantity': np.random.uniform(0.1, 10, 1000)
    })
    
    # 优化订单簿
    optimized_orderbook = optimizer.optimize_orderbook(orderbook_data)
    
    # 验证优化结果
    assert optimized_orderbook.index.names == ['side', 'price']
    assert optimized_orderbook.index.is_monotonic_increasing
    assert optimized_orderbook.dtypes['quantity'] in [np.float16, np.float32]
    
    # 缓存订单簿
    optimizer.cache_orderbook('XAUUSD', optimized_orderbook)
    
    # 验证缓存
    cached_orderbook = optimizer.get_cached_orderbook('XAUUSD')
    assert cached_orderbook is not None
    assert len(cached_orderbook) == len(optimized_orderbook)

@pytest.mark.asyncio
async def test_orderbook_updates_performance(optimizer: TradingOptimizer, tester: PerformanceTester):
    """测试订单簿更新性能"""
    # 生成测试数据
    orderbook_data = pd.DataFrame({
        'side': np.random.choice(['buy', 'sell'], 1000),
        'price': np.random.uniform(1800, 1900, 1000),
        'quantity': np.random.uniform(0.1, 10, 1000)
    })
    
    # 优化并缓存订单簿
    optimized_orderbook = optimizer.optimize_orderbook(orderbook_data)
    optimizer.cache_orderbook('XAUUSD', optimized_orderbook)
    
    # 生成更新数据
    updates = [
        {
            'side': np.random.choice(['buy', 'sell']),
            'price': np.random.uniform(1800, 1900),
            'quantity': np.random.uniform(0.1, 10)
        }
        for _ in range(1000)
    ]
    
    # 测量性能
    metrics = await tester.measure_performance(
        'orderbook_updates',
        optimizer.process_orderbook_updates,
        updates,
        'XAUUSD',
        iterations=10
    )
    
    # 验证性能指标
    assert metrics['execution_time'] < 2.0  # 处理1000次更新应该在2秒内完成
    assert metrics['memory_usage'] < 100 * 1024 * 1024  # 内存使用应该小于100MB

@pytest.mark.asyncio
async def test_market_data_optimization(optimizer: TradingOptimizer):
    """测试市场数据优化"""
    # 生成测试数据
    market_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='1min'),
        'open': np.random.uniform(1800, 1900, 1000),
        'high': np.random.uniform(1800, 1900, 1000),
        'low': np.random.uniform(1800, 1900, 1000),
        'close': np.random.uniform(1800, 1900, 1000),
        'volume': np.random.uniform(100, 1000, 1000)
    })
    
    # 优化市场数据
    optimized_data = optimizer.optimize_market_data(market_data)
    
    # 验证优化结果
    assert optimized_data.index.name == 'timestamp'
    assert 'returns' in optimized_data.columns
    assert 'volatility' in optimized_data.columns
    assert 'ma_20' in optimized_data.columns
    assert optimized_data.dtypes['close'] in [np.float16, np.float32]
    
    # 缓存市场数据
    optimizer.cache_market_data('XAUUSD', optimized_data)
    
    # 验证缓存
    cached_data = optimizer.get_cached_market_data('XAUUSD')
    assert cached_data is not None
    assert len(cached_data) == len(optimized_data)

@pytest.mark.asyncio
async def test_market_data_updates_performance(optimizer: TradingOptimizer, tester: PerformanceTester):
    """测试市场数据更新性能"""
    # 生成测试数据
    market_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='1min'),
        'open': np.random.uniform(1800, 1900, 1000),
        'high': np.random.uniform(1800, 1900, 1000),
        'low': np.random.uniform(1800, 1900, 1000),
        'close': np.random.uniform(1800, 1900, 1000),
        'volume': np.random.uniform(100, 1000, 1000)
    })
    
    # 优化并缓存市场数据
    optimized_data = optimizer.optimize_market_data(market_data)
    optimizer.cache_market_data('XAUUSD', optimized_data)
    
    # 生成更新数据
    updates = [
        {
            'timestamp': pd.Timestamp('2024-01-01') + pd.Timedelta(minutes=i),
            'open': np.random.uniform(1800, 1900),
            'high': np.random.uniform(1800, 1900),
            'low': np.random.uniform(1800, 1900),
            'close': np.random.uniform(1800, 1900),
            'volume': np.random.uniform(100, 1000)
        }
        for i in range(1000)
    ]
    
    # 测量性能
    metrics = await tester.measure_performance(
        'market_data_updates',
        optimizer.process_market_data_updates,
        updates,
        'XAUUSD',
        iterations=10
    )
    
    # 验证性能指标
    assert metrics['execution_time'] < 2.0  # 处理1000次更新应该在2秒内完成
    assert metrics['memory_usage'] < 100 * 1024 * 1024  # 内存使用应该小于100MB

@pytest.mark.asyncio
async def test_trade_execution_performance(optimizer: TradingOptimizer, tester: PerformanceTester):
    """测试交易执行性能"""
    # 生成测试数据
    orderbook_data = pd.DataFrame({
        'side': np.random.choice(['buy', 'sell'], 1000),
        'price': np.random.uniform(1800, 1900, 1000),
        'quantity': np.random.uniform(0.1, 10, 1000)
    })
    
    # 优化并缓存订单簿
    optimized_orderbook = optimizer.optimize_orderbook(orderbook_data)
    optimizer.cache_orderbook('XAUUSD', optimized_orderbook)
    
    # 生成测试订单
    trades = [
        {
            'order_id': f'order_{i}',
            'symbol': 'XAUUSD',
            'side': np.random.choice(['buy', 'sell']),
            'price': np.random.uniform(1800, 1900),
            'quantity': np.random.uniform(0.1, 10)
        }
        for i in range(1000)
    ]
    
    # 测量性能
    metrics = await tester.measure_performance(
        'trade_execution',
        optimizer.execute_trades,
        trades,
        'XAUUSD',
        iterations=5
    )
    
    # 验证性能指标
    assert metrics['execution_time'] < 5.0  # 处理1000个订单应该在5秒内完成
    assert metrics['memory_usage'] < 200 * 1024 * 1024  # 内存使用应该小于200MB

@pytest.mark.asyncio
async def test_cache_management(optimizer: TradingOptimizer):
    """测试缓存管理"""
    # 生成测试数据
    symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD']
    
    # 填充缓存
    for symbol in symbols:
        # 订单簿数据
        orderbook_data = pd.DataFrame({
            'side': np.random.choice(['buy', 'sell'], 100),
            'price': np.random.uniform(1800, 1900, 100),
            'quantity': np.random.uniform(0.1, 10, 100)
        })
        optimized_orderbook = optimizer.optimize_orderbook(orderbook_data)
        optimizer.cache_orderbook(symbol, optimized_orderbook)
        
        # 市场数据
        market_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='1min'),
            'open': np.random.uniform(1800, 1900, 100),
            'high': np.random.uniform(1800, 1900, 100),
            'low': np.random.uniform(1800, 1900, 100),
            'close': np.random.uniform(1800, 1900, 100),
            'volume': np.random.uniform(100, 1000, 100)
        })
        optimized_data = optimizer.optimize_market_data(market_data)
        optimizer.cache_market_data(symbol, optimized_data)
    
    # 验证缓存大小
    assert len(optimizer._orderbook_cache) <= optimizer._cache_size
    assert len(optimizer._market_data_cache) <= optimizer._cache_size
    
    # 添加新数据
    new_symbol = 'AUDUSD'
    orderbook_data = pd.DataFrame({
        'side': np.random.choice(['buy', 'sell'], 100),
        'price': np.random.uniform(1800, 1900, 100),
        'quantity': np.random.uniform(0.1, 10, 100)
    })
    optimized_orderbook = optimizer.optimize_orderbook(orderbook_data)
    optimizer.cache_orderbook(new_symbol, optimized_orderbook)
    
    # 验证旧数据被移除
    assert new_symbol in optimizer._orderbook_cache
    assert len(optimizer._orderbook_cache) <= optimizer._cache_size 