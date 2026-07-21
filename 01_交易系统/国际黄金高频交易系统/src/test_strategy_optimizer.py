import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

from execution.strategy_optimizer import (
    StrategyOptimizer,
    StrategyParameters,
    OptimizationResult
)
from execution.quality_analyzer import QualityAnalyzer, ExecutionMetrics, QualityReport
from execution.timing_optimizer import TimingOptimizer
from execution.market_impact_analyzer import MarketImpactAnalyzer

class MockMarketCondition:
    def __init__(self):
        self.volatility_score = 0.5
        self.avg_spread = 0.002
        self.avg_volume = 1000.0
        self.bid_ask_imbalance = 0.1

class MockMarketImpactAnalyzer:
    def __init__(self):
        self.current_condition = MockMarketCondition()

def create_mock_quality_report() -> QualityReport:
    """创建模拟的质量报告"""
    execution_metrics = ExecutionMetrics(
        total_cost=0.001,
        market_impact=0.0005,
        timing_cost=0.0003,
        delay_cost=0.0002,
        completion_rate=0.99
    )
    
    market_conditions = {
        'volatility': 0.5,
        'spread': 0.002,
        'volume': 1000.0,
        'imbalance': 0.1
    }
    
    return QualityReport(
        order_id="test_order",
        execution_metrics=execution_metrics,
        benchmark_metrics=execution_metrics,
        market_conditions=market_conditions,
        optimization_suggestions=[]
    )

@pytest.fixture
def optimizer():
    """创建策略优化器实例"""
    quality_analyzer = QualityAnalyzer()
    timing_optimizer = TimingOptimizer()
    impact_analyzer = MockMarketImpactAnalyzer()
    
    return StrategyOptimizer(
        quality_analyzer=quality_analyzer,
        timing_optimizer=timing_optimizer,
        impact_analyzer=impact_analyzer,
        learning_rate=0.01,
        history_window=100,
        min_samples=10
    )

@pytest.fixture
def strategy_params():
    """创建策略参数实例"""
    return StrategyParameters(
        min_participation_rate=0.05,
        max_participation_rate=0.3,
        min_window_size=5,
        max_window_size=30,
        cost_weight=1.0,
        time_weight=0.5
    )

async def test_initial_optimization(optimizer, strategy_params):
    """测试初始优化"""
    # 执行优化
    result = await optimizer.optimize_strategy(
        size=1000.0,
        side="buy",
        params=strategy_params
    )
    
    # 验证结果
    assert isinstance(result, OptimizationResult)
    assert 0.05 <= result.participation_rate <= 0.3
    assert 5 <= result.execution_window <= 30
    assert 0.1 <= result.urgency_factor <= 0.9
    assert result.expected_cost >= 0
    assert 0 <= result.confidence <= 1.0

async def test_optimization_with_history(optimizer, strategy_params):
    """测试有历史数据时的优化"""
    # 添加历史数据
    for i in range(20):
        await optimizer.update_execution_history(
            order_id=f"test_order_{i}",
            participation_rate=0.1,
            window_size=10,
            urgency=0.5,
            quality_report=create_mock_quality_report()
        )
    
    # 执行优化
    result = await optimizer.optimize_strategy(
        size=1000.0,
        side="buy",
        params=strategy_params
    )
    
    # 验证结果
    assert isinstance(result, OptimizationResult)
    assert result.confidence > 0  # 有历史数据时应该有置信度

async def test_market_condition_impact(optimizer, strategy_params):
    """测试市场条件对优化的影响"""
    # 修改市场条件
    optimizer.impact_analyzer.current_condition.volatility_score = 0.8
    optimizer.impact_analyzer.current_condition.avg_spread = 0.005
    
    # 执行优化
    result = await optimizer.optimize_strategy(
        size=1000.0,
        side="buy",
        params=strategy_params
    )
    
    # 验证结果
    assert result.participation_rate < strategy_params.max_participation_rate * 0.8
    assert result.execution_window > strategy_params.min_window_size

def test_optimization_stats(optimizer):
    """测试优化统计信息"""
    # 添加历史数据
    for i in range(10):
        optimizer.execution_history.append({
            'participation_rate': 0.1,
            'window_size': 10,
            'urgency': 0.5,
            'execution_metrics': ExecutionMetrics(
                total_cost=0.001,
                market_impact=0.0005,
                timing_cost=0.0003,
                delay_cost=0.0002,
                completion_rate=0.99
            )
        })
    
    # 获取统计信息
    stats = optimizer.get_optimization_stats()
    
    # 验证统计信息
    assert 'avg_participation_rate' in stats
    assert 'avg_window_size' in stats
    assert 'avg_cost' in stats
    assert stats['sample_count'] == 10

async def test_parameter_grid_generation(optimizer, strategy_params):
    """测试参数网格生成"""
    # 生成参数网格
    market_conditions = {
        'volatility': 0.5,
        'spread': 0.002,
        'volume': 1000.0,
        'imbalance': 0.1
    }
    
    param_grid = optimizer._generate_parameter_grid(
        strategy_params,
        market_conditions
    )
    
    # 验证参数网格
    assert len(param_grid) > 0
    for params in param_grid:
        assert 'participation_rate' in params
        assert 'window_size' in params
        assert 'urgency' in params
        assert strategy_params.min_participation_rate <= params['participation_rate'] <= strategy_params.max_participation_rate
        assert strategy_params.min_window_size <= params['window_size'] <= strategy_params.max_window_size

async def main():
    """运行所有测试"""
    optimizer = optimizer()
    params = strategy_params()
    
    try:
        print("Testing initial optimization...")
        await test_initial_optimization(optimizer, params)
        print("✓ Initial optimization test passed")
        
        print("Testing optimization with history...")
        await test_optimization_with_history(optimizer, params)
        print("✓ Optimization with history test passed")
        
        print("Testing market condition impact...")
        await test_market_condition_impact(optimizer, params)
        print("✓ Market condition impact test passed")
        
        print("Testing optimization stats...")
        test_optimization_stats(optimizer)
        print("✓ Optimization stats test passed")
        
        print("Testing parameter grid generation...")
        await test_parameter_grid_generation(optimizer, params)
        print("✓ Parameter grid generation test passed")
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 