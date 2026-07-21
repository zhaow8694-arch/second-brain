import asyncio
import pytest
from datetime import datetime
import numpy as np
from execution.price_calculator import (
    DynamicPriceCalculator,
    PriceRange,
    MarketDepthInfo
)
from execution.slippage_predictor import SlippagePredictor

def generate_depth_data(base_price: float,
                       base_volume: float,
                       levels: int = 10,
                       spread: float = 0.0002) -> Tuple[Dict[float, float], Dict[float, float]]:
    """生成模拟深度数据"""
    bid_depths = {}
    ask_depths = {}
    
    # 生成买单深度
    for i in range(levels):
        price = base_price * (1 - spread * (i + 1))
        volume = base_volume * (1 - i * 0.08)  # 越远离中间价，量越小
        bid_depths[price] = volume
        
    # 生成卖单深度
    for i in range(levels):
        price = base_price * (1 + spread * (i + 1))
        volume = base_volume * (1 - i * 0.08)
        ask_depths[price] = volume
        
    return bid_depths, ask_depths

async def setup_test_environment():
    """设置测试环境"""
    # 创建滑点预测器
    predictor = SlippagePredictor(
        lookback_window=100,
        volatility_window=20,
        update_interval=60,
        min_samples=50
    )
    
    # 创建价格计算器
    calculator = DynamicPriceCalculator(
        slippage_predictor=predictor,
        max_price_deviation=0.01,
        confidence_threshold=0.7,
        depth_impact_factor=0.5,
        urgency_multiplier=1.5
    )
    
    return predictor, calculator

async def test_basic_price_calculation():
    """测试基本价格计算"""
    predictor, calculator = await setup_test_environment()
    
    # 生成深度数据
    base_price = 50000.0
    base_volume = 100.0
    bid_depths, ask_depths = generate_depth_data(base_price, base_volume)
    
    # 测试买单价格计算
    buy_price_range = await calculator.calculate_limit_price(
        current_price=base_price,
        size=1.0,
        side="buy",
        urgency=0.5,
        bid_depths=bid_depths,
        ask_depths=ask_depths
    )
    
    assert isinstance(buy_price_range, PriceRange)
    assert buy_price_range.min_price < base_price < buy_price_range.max_price
    assert buy_price_range.confidence > 0
    
    # 测试卖单价格计算
    sell_price_range = await calculator.calculate_limit_price(
        current_price=base_price,
        size=1.0,
        side="sell",
        urgency=0.5,
        bid_depths=bid_depths,
        ask_depths=ask_depths
    )
    
    assert isinstance(sell_price_range, PriceRange)
    assert sell_price_range.min_price < base_price < sell_price_range.max_price
    assert sell_price_range.confidence > 0

async def test_depth_impact():
    """测试深度影响"""
    predictor, calculator = await setup_test_environment()
    
    # 生成深度数据
    base_price = 50000.0
    base_volume = 100.0
    bid_depths, ask_depths = generate_depth_data(base_price, base_volume)
    
    # 测试小订单
    small_order = await calculator.calculate_limit_price(
        current_price=base_price,
        size=0.1,  # 小订单
        side="buy",
        urgency=0.5,
        bid_depths=bid_depths,
        ask_depths=ask_depths
    )
    
    # 测试大订单
    large_order = await calculator.calculate_limit_price(
        current_price=base_price,
        size=50.0,  # 大订单
        side="buy",
        urgency=0.5,
        bid_depths=bid_depths,
        ask_depths=ask_depths
    )
    
    # 验证大订单的价格偏差更大
    assert abs(large_order.optimal_price - base_price) > abs(small_order.optimal_price - base_price)
    assert large_order.confidence < small_order.confidence

async def test_urgency_impact():
    """测试紧急度影响"""
    predictor, calculator = await setup_test_environment()
    
    # 生成深度数据
    base_price = 50000.0
    base_volume = 100.0
    bid_depths, ask_depths = generate_depth_data(base_price, base_volume)
    
    # 测试低紧急度
    low_urgency = await calculator.calculate_limit_price(
        current_price=base_price,
        size=1.0,
        side="buy",
        urgency=0.2,
        bid_depths=bid_depths,
        ask_depths=ask_depths
    )
    
    # 测试高紧急度
    high_urgency = await calculator.calculate_limit_price(
        current_price=base_price,
        size=1.0,
        side="buy",
        urgency=0.8,
        bid_depths=bid_depths,
        ask_depths=ask_depths
    )
    
    # 验证高紧急度的价格范围更宽
    assert (high_urgency.max_price - high_urgency.min_price) > (low_urgency.max_price - low_urgency.min_price)
    assert high_urgency.optimal_price > low_urgency.optimal_price

async def test_adjustment_factors():
    """测试调整因子"""
    predictor, calculator = await setup_test_environment()
    
    # 获取初始因子
    initial_factors = calculator.get_price_adjustment_factors()
    
    # 更新因子
    calculator.update_adjustment_factors(
        max_price_deviation=0.02,
        depth_impact_factor=0.7
    )
    
    # 验证更新
    updated_factors = calculator.get_price_adjustment_factors()
    assert updated_factors['max_price_deviation'] == 0.02
    assert updated_factors['depth_impact_factor'] == 0.7
    assert updated_factors['confidence_threshold'] == initial_factors['confidence_threshold']
    assert updated_factors['urgency_multiplier'] == initial_factors['urgency_multiplier']

async def main():
    """运行所有测试"""
    print("开始测试动态限价计算器...")
    
    try:
        print("\n测试基本价格计算...")
        await test_basic_price_calculation()
        print("✓ 基本价格计算测试通过")
        
        print("\n测试深度影响...")
        await test_depth_impact()
        print("✓ 深度影响测试通过")
        
        print("\n测试紧急度影响...")
        await test_urgency_impact()
        print("✓ 紧急度影响测试通过")
        
        print("\n测试调整因子...")
        await test_adjustment_factors()
        print("✓ 调整因子测试通过")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 