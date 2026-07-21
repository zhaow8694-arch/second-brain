import asyncio
import pytest
from datetime import datetime, timedelta
import numpy as np
from execution.market_impact_analyzer import MarketImpactAnalyzer
from execution.timing_optimizer import (
    TimingOptimizer,
    ExecutionWindow,
    ExecutionSpeed,
    MarketTiming
)

async def setup_test_environment():
    """设置测试环境"""
    # 创建市场冲击成本分析器
    impact_analyzer = MarketImpactAnalyzer(
        lookback_window=100,
        volatility_window=20
    )
    
    # 创建执行时机优化器
    optimizer = TimingOptimizer(
        impact_analyzer=impact_analyzer,
        min_execution_time=5,
        max_execution_time=120,
        time_window_size=60
    )
    
    # 生成并更新市场数据
    base_price = 50000.0
    base_volume = 1.0
    current_time = datetime.now()
    
    # 模拟一天的市场数据
    for i in range(24):
        # 生成每小时的数据
        price = base_price * (1 + np.random.normal(0, 0.001))
        volume = base_volume * (1 + np.random.normal(0, 0.2))
        spread = price * 0.0002
        
        await impact_analyzer.update_market_data(
            timestamp=current_time + timedelta(hours=i),
            price=price,
            volume=volume,
            bid_price=price - spread/2,
            ask_price=price + spread/2,
            bid_volume=volume * 0.48,  # 模拟轻微的买方压力
            ask_volume=volume * 0.52
        )
    
    return optimizer

async def test_market_timing_evaluation():
    """测试市场时机评估"""
    optimizer = await setup_test_environment()
    
    # 测试买入和卖出的时机评估
    for side in ["buy", "sell"]:
        timing = optimizer.evaluate_market_timing(
            optimizer.impact_analyzer.current_condition,
            side
        )
        
        # 验证评分范围
        assert isinstance(timing, MarketTiming)
        assert 0 <= timing.score <= 1
        assert 0 <= timing.volatility_score <= 1
        assert 0 <= timing.spread_score <= 1
        assert 0 <= timing.volume_score <= 1
        assert 0 <= timing.imbalance_score <= 1
        
        # 验证买卖方向的影响
        if side == "buy":
            # 买入时应该更偏好低波动率
            assert timing.volatility_score >= 0.4
        else:
            # 卖出时可以接受高波动率
            assert timing.volatility_score <= 0.6

async def test_execution_window():
    """测试执行时间窗口"""
    optimizer = await setup_test_environment()
    
    # 测试不同大小的订单
    test_sizes = [0.1, 1.0, 5.0]  # 小单、中单、大单
    
    for size in test_sizes:
        # 测试买入
        window = await optimizer.get_execution_window(
            size=size,
            side="buy"
        )
        
        assert isinstance(window, ExecutionWindow)
        assert window.start_time <= window.optimal_time <= window.end_time
        assert window.expected_cost >= 0
        assert 0 <= window.confidence <= 1
        
        # 测试带有成本限制的执行窗口
        max_cost = 0.001  # 限制成本为10bp
        window_with_limit = await optimizer.get_execution_window(
            size=size,
            side="buy",
            max_cost=max_cost
        )
        
        assert window_with_limit.expected_cost <= max_cost or \
               window_with_limit.end_time > window.end_time

async def test_execution_speed():
    """测试执行速度计算"""
    optimizer = await setup_test_environment()
    
    # 获取市场时机评估
    timing = optimizer.evaluate_market_timing(
        optimizer.impact_analyzer.current_condition,
        "buy"
    )
    
    # 测试不同剩余时间的执行速度
    test_cases = [
        (1.0, 60.0),  # 1个币，60分钟
        (2.0, 30.0),  # 2个币，30分钟
        (0.5, 120.0)  # 0.5个币，120分钟
    ]
    
    for size, remaining_time in test_cases:
        speed = optimizer.calculate_execution_speed(
            size=size,
            remaining_time=remaining_time,
            market_timing=timing
        )
        
        assert isinstance(speed, ExecutionSpeed)
        assert speed.min_speed <= speed.current_speed <= speed.max_speed
        assert abs(speed.base_speed - size/remaining_time) < 1e-6
        
        # 验证速度范围
        assert speed.max_speed >= speed.base_speed
        assert speed.min_speed <= speed.base_speed

async def test_execution_stats():
    """测试执行统计"""
    optimizer = await setup_test_environment()
    
    # 生成一些市场时机评估记录
    for _ in range(10):
        optimizer.evaluate_market_timing(
            optimizer.impact_analyzer.current_condition,
            "buy"
        )
    
    # 获取统计信息
    stats = optimizer.get_execution_stats()
    
    assert len(stats) > 0
    assert 'avg_timing_score' in stats
    assert 'std_timing_score' in stats
    assert 'max_timing_score' in stats
    assert 'min_timing_score' in stats
    assert stats['sample_count'] > 0

async def main():
    """运行所有测试"""
    print("开始测试执行时机优化器...")
    
    try:
        print("\n测试市场时机评估...")
        await test_market_timing_evaluation()
        print("✓ 市场时机评估测试通过")
        
        print("\n测试执行时间窗口...")
        await test_execution_window()
        print("✓ 执行时间窗口测试通过")
        
        print("\n测试执行速度计算...")
        await test_execution_speed()
        print("✓ 执行速度计算测试通过")
        
        print("\n测试执行统计...")
        await test_execution_stats()
        print("✓ 执行统计测试通过")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 