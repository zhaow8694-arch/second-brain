import pytest
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .performance_optimizer import PerformanceOptimizer
from .performance_tester import PerformanceTester
from .data_generator import TestDataGenerator

@pytest.fixture
def config() -> Dict[str, Any]:
    """测试配置"""
    return {
        'cache_dir': 'test_cache',
        'max_workers': 4,
        'chunk_size': 100
    }

@pytest.fixture
async def optimizer(config: Dict[str, Any]) -> PerformanceOptimizer:
    """性能优化器"""
    async with PerformanceOptimizer(config) as opt:
        yield opt

@pytest.fixture
async def tester(config: Dict[str, Any]) -> PerformanceTester:
    """性能测试器"""
    async with PerformanceTester(config) as t:
        yield t

@pytest.fixture
def data_generator() -> TestDataGenerator:
    """数据生成器"""
    return TestDataGenerator({})

@pytest.mark.asyncio
async def test_orderbook_processing_performance(tester: PerformanceTester):
    """测试订单簿处理性能"""
    def process_orderbook(orderbook: pd.DataFrame) -> Dict[str, Any]:
        # 模拟订单簿处理逻辑
        bids = orderbook[orderbook['side'] == 'buy'].sort_values('price', ascending=False)
        asks = orderbook[orderbook['side'] == 'sell'].sort_values('price', ascending=True)
        
        return {
            'best_bid': bids.iloc[0]['price'] if not bids.empty else None,
            'best_ask': asks.iloc[0]['price'] if not asks.empty else None,
            'spread': (asks.iloc[0]['price'] - bids.iloc[0]['price']) if not (bids.empty or asks.empty) else None
        }
    
    # 生成测试数据
    orderbook_data = pd.DataFrame({
        'side': np.random.choice(['buy', 'sell'], 1000),
        'price': np.random.uniform(1800, 1900, 1000),
        'quantity': np.random.uniform(0.1, 10, 1000)
    })
    
    # 测量性能
    metrics = await tester.measure_performance(
        'orderbook_processing',
        process_orderbook,
        orderbook_data,
        iterations=100
    )
    
    # 验证性能指标
    assert metrics['execution_time'] < 1.0  # 处理100次应该在1秒内完成
    assert metrics['memory_usage'] < 50 * 1024 * 1024  # 内存使用应该小于50MB

@pytest.mark.asyncio
async def test_market_data_processing_performance(tester: PerformanceTester):
    """测试市场数据处理性能"""
    def process_market_data(data: pd.DataFrame) -> Dict[str, Any]:
        # 模拟市场数据处理逻辑
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=20).std()
        data['ma_20'] = data['close'].rolling(window=20).mean()
        
        return {
            'current_price': data['close'].iloc[-1],
            'volatility': data['volatility'].iloc[-1],
            'ma_20': data['ma_20'].iloc[-1]
        }
    
    # 生成测试数据
    market_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='1min'),
        'open': np.random.uniform(1800, 1900, 1000),
        'high': np.random.uniform(1800, 1900, 1000),
        'low': np.random.uniform(1800, 1900, 1000),
        'close': np.random.uniform(1800, 1900, 1000),
        'volume': np.random.uniform(100, 1000, 1000)
    })
    
    # 测量性能
    metrics = await tester.measure_performance(
        'market_data_processing',
        process_market_data,
        market_data,
        iterations=50
    )
    
    # 验证性能指标
    assert metrics['execution_time'] < 2.0  # 处理50次应该在2秒内完成
    assert metrics['memory_usage'] < 100 * 1024 * 1024  # 内存使用应该小于100MB

@pytest.mark.asyncio
async def test_trade_execution_performance(tester: PerformanceTester):
    """测试交易执行性能"""
    async def execute_trade(order: Dict[str, Any]) -> Dict[str, Any]:
        # 模拟交易执行逻辑
        await asyncio.sleep(0.001)  # 模拟网络延迟
        return {
            'order_id': order['order_id'],
            'status': 'filled',
            'executed_price': order['price'],
            'executed_quantity': order['quantity']
        }
    
    # 生成测试订单
    orders = [
        {
            'order_id': f'order_{i}',
            'symbol': 'XAUUSD',
            'side': np.random.choice(['buy', 'sell']),
            'price': np.random.uniform(1800, 1900),
            'quantity': np.random.uniform(0.1, 10)
        }
        for i in range(100)
    ]
    
    # 测量性能
    metrics = await tester.measure_performance(
        'trade_execution',
        execute_trade,
        orders[0],  # 测试单个订单执行
        iterations=100
    )
    
    # 验证性能指标
    assert metrics['execution_time'] < 0.5  # 单个订单执行应该在0.5秒内完成

@pytest.mark.asyncio
async def test_parallel_order_processing(optimizer: PerformanceOptimizer):
    """测试并行订单处理"""
    async def process_order(order: Dict[str, Any]) -> Dict[str, Any]:
        # 模拟订单处理逻辑
        await asyncio.sleep(0.001)  # 模拟处理时间
        return {
            'order_id': order['order_id'],
            'processed': True
        }
    
    # 生成测试订单
    orders = [
        {
            'order_id': f'order_{i}',
            'symbol': 'XAUUSD',
            'side': np.random.choice(['buy', 'sell']),
            'price': np.random.uniform(1800, 1900),
            'quantity': np.random.uniform(0.1, 10)
        }
        for i in range(1000)
    ]
    
    # 并行处理订单
    results = await optimizer.parallel_process(
        orders,
        process_order,
        chunk_size=100,
        use_processes=True
    )
    
    # 验证结果
    assert len(results) == len(orders)
    assert all(r['processed'] for r in results)

@pytest.mark.asyncio
async def test_memory_optimization(optimizer: PerformanceOptimizer):
    """测试内存优化"""
    # 创建大型DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=1000000, freq='1min'),
        'price': np.random.uniform(1800, 1900, 1000000),
        'volume': np.random.uniform(100, 1000, 1000000),
        'side': np.random.choice(['buy', 'sell'], 1000000),
        'order_id': [f'order_{i}' for i in range(1000000)]
    })
    
    # 记录原始内存使用
    original_memory = df.memory_usage(deep=True).sum()
    
    # 优化DataFrame
    optimized_df = optimizer.optimize_dataframe(df)
    
    # 记录优化后内存使用
    optimized_memory = optimized_df.memory_usage(deep=True).sum()
    
    # 验证内存优化效果
    assert optimized_memory < original_memory
    assert optimized_memory / original_memory < 0.8  # 至少减少20%的内存使用

@pytest.mark.asyncio
async def test_concurrent_market_data_processing(optimizer: PerformanceOptimizer):
    """测试并发市场数据处理"""
    async def process_market_data_chunk(data: pd.DataFrame) -> pd.DataFrame:
        # 模拟市场数据处理逻辑
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=20).std()
        return data
    
    # 生成测试数据
    market_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=10000, freq='1min'),
        'open': np.random.uniform(1800, 1900, 10000),
        'high': np.random.uniform(1800, 1900, 10000),
        'low': np.random.uniform(1800, 1900, 10000),
        'close': np.random.uniform(1800, 1900, 10000),
        'volume': np.random.uniform(100, 1000, 10000)
    })
    
    # 将数据分成多个块
    chunks = [market_data[i:i+1000] for i in range(0, len(market_data), 1000)]
    
    # 并行处理数据块
    results = await optimizer.parallel_process(
        chunks,
        process_market_data_chunk,
        chunk_size=2,
        use_processes=True
    )
    
    # 合并结果
    processed_data = pd.concat(results)
    
    # 验证结果
    assert len(processed_data) == len(market_data)
    assert 'returns' in processed_data.columns
    assert 'volatility' in processed_data.columns 