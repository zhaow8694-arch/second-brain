import asyncio
import pytest
from datetime import datetime, timedelta
import numpy as np
from execution.slippage_predictor import SlippagePredictor, MarketState, SlippageMetrics

def generate_market_data(base_price: float,
                        base_volume: float,
                        num_points: int,
                        volatility: float = 0.001) -> List[dict]:
    """生成模拟市场数据"""
    data = []
    current_time = datetime.now()
    
    price = base_price
    for i in range(num_points):
        # 生成价格变动
        price_change = np.random.normal(0, volatility)
        price = price * (1 + price_change)
        
        # 生成成交量
        volume = base_volume * (1 + np.random.uniform(-0.2, 0.2))
        
        # 生成买卖盘数据
        spread = price * 0.0002  # 0.02% 价差
        bid_price = price - spread / 2
        ask_price = price + spread / 2
        
        bid_volume = volume * (1 + np.random.uniform(-0.1, 0.1))
        ask_volume = volume * (1 + np.random.uniform(-0.1, 0.1))
        
        data.append({
            'timestamp': current_time + timedelta(minutes=i),
            'price': price,
            'volume': volume,
            'bid_price': bid_price,
            'ask_price': ask_price,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume
        })
    
    return data

def generate_execution_result(expected_price: float,
                            size: float,
                            base_slippage: float = 0.0002) -> dict:
    """生成模拟执行结果"""
    # 添加随机性到基础滑点
    slippage = base_slippage * (1 + np.random.uniform(-0.5, 0.5))
    executed_price = expected_price * (1 + slippage)
    
    return {
        'timestamp': datetime.now(),
        'size': size,
        'expected_price': expected_price,
        'executed_price': executed_price,
        'market_price': expected_price,
        'slippage': slippage
    }

async def test_market_state_update():
    """测试市场状态更新"""
    predictor = SlippagePredictor(
        lookback_window=100,
        volatility_window=20,
        update_interval=60,
        min_samples=50
    )
    
    # 生成市场数据
    market_data = generate_market_data(
        base_price=50000.0,
        base_volume=100.0,
        num_points=120,
        volatility=0.001
    )
    
    # 更新市场状态
    for data in market_data:
        await predictor.update_market_state(**data)
    
    # 验证市场状态更新
    assert len(predictor.market_states) == 100  # 验证窗口大小限制
    assert predictor.market_states[-1].timestamp == market_data[-1]['timestamp']
    
async def test_execution_history():
    """测试执行历史记录"""
    predictor = SlippagePredictor(min_samples=10)
    
    # 生成执行结果
    base_price = 50000.0
    for _ in range(20):
        result = generate_execution_result(
            expected_price=base_price,
            size=1.0,
            base_slippage=0.0002
        )
        await predictor.add_execution_result(**result)
    
    # 验证历史记录
    assert len(predictor.execution_history) == 20
    
    # 验证统计数据
    stats = predictor.get_historical_slippage()
    assert 'mean' in stats
    assert 'std' in stats
    assert abs(stats['mean']) < 0.001  # 平均滑点应该很小
    
async def test_slippage_prediction():
    """测试滑点预测"""
    predictor = SlippagePredictor(min_samples=50)
    
    # 生成市场数据和执行历史
    market_data = generate_market_data(
        base_price=50000.0,
        base_volume=100.0,
        num_points=100,
        volatility=0.002
    )
    
    # 更新市场状态和执行历史
    for data in market_data:
        await predictor.update_market_state(**data)
        
        # 添加执行结果
        result = generate_execution_result(
            expected_price=data['price'],
            size=1.0,
            base_slippage=0.0002
        )
        await predictor.add_execution_result(**result)
    
    # 测试不同情况下的预测
    # 1. 小订单，低紧急度
    small_order = await predictor.predict_slippage(size=0.1, urgency=0.2)
    assert isinstance(small_order, SlippageMetrics)
    assert small_order.expected_slippage > 0
    assert small_order.market_impact < 0.0001  # 市场冲击应该很小
    
    # 2. 大订单，高紧急度
    large_order = await predictor.predict_slippage(size=10.0, urgency=0.8)
    assert large_order.expected_slippage > small_order.expected_slippage
    assert large_order.market_impact > small_order.market_impact
    assert large_order.timing_cost > small_order.timing_cost
    
async def test_model_update():
    """测试模型更新"""
    predictor = SlippagePredictor(
        min_samples=20,
        update_interval=1
    )
    
    # 生成初始数据
    market_data = generate_market_data(
        base_price=50000.0,
        base_volume=100.0,
        num_points=30,
        volatility=0.001
    )
    
    # 更新数据并训练模型
    for data in market_data:
        await predictor.update_market_state(**data)
        result = generate_execution_result(
            expected_price=data['price'],
            size=1.0
        )
        await predictor.add_execution_result(**result)
    
    # 获取初始预测
    initial_prediction = await predictor.predict_slippage(size=1.0)
    
    # 添加新数据（高波动性）
    new_data = generate_market_data(
        base_price=50000.0,
        base_volume=100.0,
        num_points=10,
        volatility=0.005
    )
    
    for data in new_data:
        await predictor.update_market_state(**data)
        result = generate_execution_result(
            expected_price=data['price'],
            size=1.0,
            base_slippage=0.001  # 更大的滑点
        )
        await predictor.add_execution_result(**result)
    
    # 获取更新后的预测
    updated_prediction = await predictor.predict_slippage(size=1.0)
    
    # 验证模型适应性
    assert updated_prediction.expected_slippage > initial_prediction.expected_slippage
    assert updated_prediction.market_impact > initial_prediction.market_impact

async def main():
    """运行所有测试"""
    print("开始测试滑点预测器...")
    
    try:
        print("\n测试市场状态更新...")
        await test_market_state_update()
        print("✓ 市场状态更新测试通过")
        
        print("\n测试执行历史记录...")
        await test_execution_history()
        print("✓ 执行历史记录测试通过")
        
        print("\n测试滑点预测...")
        await test_slippage_prediction()
        print("✓ 滑点预测测试通过")
        
        print("\n测试模型更新...")
        await test_model_update()
        print("✓ 模型更新测试通过")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 