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
async def test_parallel_processing(optimizer: PerformanceOptimizer):
    """测试并行处理"""
    # 生成测试数据
    items = list(range(1000))
    
    def process_item(item: int) -> int:
        return item * item
        
    # 使用线程池
    results_thread = await optimizer.parallel_process(
        items,
        process_item,
        chunk_size=100,
        use_processes=False
    )
    
    # 使用进程池
    results_process = await optimizer.parallel_process(
        items,
        process_item,
        chunk_size=100,
        use_processes=True
    )
    
    # 验证结果
    assert len(results_thread) == len(items)
    assert len(results_process) == len(items)
    assert results_thread == results_process

@pytest.mark.asyncio
async def test_cached_computation(optimizer: PerformanceOptimizer):
    """测试缓存计算"""
    def expensive_computation(n: int) -> int:
        return sum(i * i for i in range(n))
        
    # 第一次计算
    start_time = asyncio.get_event_loop().time()
    result1 = optimizer.cached_computation(expensive_computation, 1000)
    time1 = asyncio.get_event_loop().time() - start_time
    
    # 第二次计算（应该使用缓存）
    start_time = asyncio.get_event_loop().time()
    result2 = optimizer.cached_computation(expensive_computation, 1000)
    time2 = asyncio.get_event_loop().time() - start_time
    
    # 验证结果和性能
    assert result1 == result2
    assert time2 < time1  # 第二次应该更快

@pytest.mark.asyncio
async def test_parallel_data_generation(
    optimizer: PerformanceOptimizer,
    data_generator: TestDataGenerator
):
    """测试并行数据生成"""
    # 准备参数列表
    params_list = [
        {
            'symbol': 'BTC/USDT',
            'timeframe': '1m',
            'count': 100
        }
        for _ in range(10)
    ]
    
    # 并行生成数据
    results = await optimizer.parallel_data_generation(
        data_generator.generate_market_data,
        params_list,
        chunk_size=2
    )
    
    # 验证结果
    assert len(results) == len(params_list)
    for df in results:
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100

@pytest.mark.asyncio
async def test_dataframe_optimization(optimizer: PerformanceOptimizer):
    """测试DataFrame优化"""
    # 创建测试数据
    df = pd.DataFrame({
        'int8_col': np.random.randint(-128, 127, 1000),
        'int16_col': np.random.randint(-32768, 32767, 1000),
        'int32_col': np.random.randint(-2147483648, 2147483647, 1000),
        'float16_col': np.random.uniform(-1, 1, 1000),
        'float32_col': np.random.uniform(-1, 1, 1000),
        'float64_col': np.random.uniform(-1, 1, 1000)
    })
    
    # 优化DataFrame
    optimized_df = optimizer.optimize_dataframe(df)
    
    # 验证数据类型
    assert optimized_df['int8_col'].dtype == np.int8
    assert optimized_df['int16_col'].dtype == np.int16
    assert optimized_df['int32_col'].dtype == np.int32
    assert optimized_df['float16_col'].dtype == np.float16
    assert optimized_df['float32_col'].dtype == np.float32
    assert optimized_df['float64_col'].dtype == np.float64

@pytest.mark.asyncio
async def test_batch_processing(optimizer: PerformanceOptimizer):
    """测试批量处理"""
    items = list(range(1000))
    
    async def process_batch(batch: List[int]) -> int:
        return sum(batch)
        
    results = await optimizer.batch_process(
        items,
        process_batch,
        batch_size=100
    )
    
    # 验证结果
    assert len(results) == 10  # 1000/100 = 10个批次
    assert sum(results) == sum(items)

@pytest.mark.asyncio
async def test_performance_measurement(tester: PerformanceTester):
    """测试性能测量"""
    def test_function(n: int) -> int:
        return sum(i * i for i in range(n))
        
    metrics = await tester.measure_performance(
        'test_function',
        test_function,
        1000,
        iterations=5
    )
    
    # 验证指标
    assert 'execution_time' in metrics
    assert 'memory_usage' in metrics
    assert 'cpu_usage' in metrics
    assert metrics['iterations'] == 5

@pytest.mark.asyncio
async def test_performance_comparison(tester: PerformanceTester):
    """测试性能比较"""
    def original_function(n: int) -> int:
        return sum(i * i for i in range(n))
        
    def optimized_function(n: int) -> int:
        return n * (n + 1) * (2 * n + 1) // 6
        
    comparison = await tester.compare_performance(
        'sum_squares',
        original_function,
        optimized_function,
        1000,
        iterations=5
    )
    
    # 验证比较结果
    assert 'original' in comparison
    assert 'optimized' in comparison
    assert 'improvement' in comparison
    assert comparison['improvement']['execution_time'] > 0  # 优化版本应该更快

@pytest.mark.asyncio
async def test_performance_report(tester: PerformanceTester):
    """测试性能报告生成"""
    def test_function(n: int) -> int:
        return sum(i * i for i in range(n))
        
    # 运行多次测试
    for _ in range(3):
        await tester.measure_performance(
            'test_function',
            test_function,
            1000,
            iterations=5
        )
        
    # 生成报告
    report = tester.generate_performance_report()
    
    # 验证报告内容
    assert 'test_function' in report
    assert '执行时间' in report
    assert '内存使用' in report
    assert 'CPU使用率' in report
    assert '性能趋势' in report
    
    # 保存报告
    tester.save_report('test_report.md')
    with open('test_report.md', 'r', encoding='utf-8') as f:
        saved_report = f.read()
    assert saved_report == report 