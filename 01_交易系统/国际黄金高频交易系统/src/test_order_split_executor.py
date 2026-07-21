import asyncio
import pytest
from datetime import datetime, timedelta
import numpy as np
from execution.order_split_executor import (
    OrderSplitExecutor,
    SplitConfig,
    AlgorithmType,
    MarketData,
    ExecutionResult
)

def generate_market_data(base_price: float, 
                        base_volume: float,
                        num_points: int,
                        volatility: float = 0.001) -> List[MarketData]:
    """生成模拟市场数据"""
    data = []
    current_time = datetime.now()
    
    for i in range(num_points):
        # 生成价格
        price_change = np.random.normal(0, volatility)
        price = base_price * (1 + price_change)
        
        # 生成成交量
        volume = base_volume * (1 + np.random.uniform(-0.2, 0.2))
        
        # 生成买卖盘数据
        spread = price * 0.0002  # 0.02% 价差
        bid_price = price - spread / 2
        ask_price = price + spread / 2
        
        bid_volume = volume * (1 + np.random.uniform(-0.1, 0.1))
        ask_volume = volume * (1 + np.random.uniform(-0.1, 0.1))
        
        data.append(MarketData(
            timestamp=current_time + timedelta(minutes=i),
            price=price,
            volume=volume,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_volume=bid_volume,
            ask_volume=ask_volume
        ))
    
    return data

async def test_twap_execution():
    """测试TWAP执行"""
    # 设置测试参数
    symbol = "BTC/USDT"
    side = "buy"
    total_size = 10.0
    target_price = 50000.0
    
    # 创建配置
    config = SplitConfig(
        algorithm=AlgorithmType.TWAP,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        num_splits=12,  # 5分钟一次
        min_split_size=0.1,
        max_split_size=2.0,
        urgency=0.5
    )
    
    # 创建执行器
    executor = OrderSplitExecutor(
        symbol=symbol,
        side=side,
        total_size=total_size,
        target_price=target_price,
        config=config
    )
    
    # 生成并更新市场数据
    market_data = generate_market_data(
        base_price=target_price,
        base_volume=100.0,
        num_points=20
    )
    
    for data in market_data:
        await executor.update_market_data(data)
    
    # 测试获取执行大小
    sizes = []
    while True:
        size = await executor.get_next_size()
        if size is None:
            break
        sizes.append(size)
        
        # 模拟执行结果
        result = ExecutionResult(
            executed_price=target_price * (1 + np.random.uniform(-0.001, 0.001)),
            executed_size=size,
            timestamp=datetime.now(),
            venue="binance",
            transaction_cost=size * 0.001,  # 0.1% 费率
            slippage=0.0002  # 0.02% 滑点
        )
        await executor.update_execution(result)
    
    # 验证结果
    stats = executor.get_execution_stats()
    assert abs(stats["total_executed"] - total_size) < 1e-6
    assert stats["remaining_size"] < 1e-6
    assert stats["completion_rate"] > 0.99
    
async def test_vwap_execution():
    """测试VWAP执行"""
    # 设置测试参数
    symbol = "BTC/USDT"
    side = "buy"
    total_size = 10.0
    target_price = 50000.0
    
    # 创建配置
    config = SplitConfig(
        algorithm=AlgorithmType.VWAP,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        num_splits=12,
        min_split_size=0.1,
        max_split_size=2.0,
        urgency=0.5
    )
    
    # 创建执行器
    executor = OrderSplitExecutor(
        symbol=symbol,
        side=side,
        total_size=total_size,
        target_price=target_price,
        config=config
    )
    
    # 生成并更新市场数据（模拟成交量分布）
    market_data = generate_market_data(
        base_price=target_price,
        base_volume=100.0,
        num_points=20,
        volatility=0.002
    )
    
    for data in market_data:
        await executor.update_market_data(data)
    
    # 测试获取执行大小
    sizes = []
    while True:
        size = await executor.get_next_size()
        if size is None:
            break
        sizes.append(size)
        
        # 模拟执行结果
        result = ExecutionResult(
            executed_price=target_price * (1 + np.random.uniform(-0.001, 0.001)),
            executed_size=size,
            timestamp=datetime.now(),
            venue="binance",
            transaction_cost=size * 0.001,
            slippage=0.0002
        )
        await executor.update_execution(result)
    
    # 验证结果
    stats = executor.get_execution_stats()
    assert abs(stats["total_executed"] - total_size) < 1e-6
    assert stats["remaining_size"] < 1e-6
    assert stats["completion_rate"] > 0.99
    
async def test_adaptive_execution():
    """测试自适应执行"""
    # 设置测试参数
    symbol = "BTC/USDT"
    side = "buy"
    total_size = 10.0
    target_price = 50000.0
    
    # 创建配置
    config = SplitConfig(
        algorithm=AlgorithmType.ADAPTIVE,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        num_splits=12,
        min_split_size=0.1,
        max_split_size=2.0,
        urgency=0.7  # 较高紧急度
    )
    
    # 创建执行器
    executor = OrderSplitExecutor(
        symbol=symbol,
        side=side,
        total_size=total_size,
        target_price=target_price,
        config=config
    )
    
    # 生成并更新市场数据（模拟高波动性）
    market_data = generate_market_data(
        base_price=target_price,
        base_volume=100.0,
        num_points=20,
        volatility=0.005
    )
    
    for data in market_data:
        await executor.update_market_data(data)
    
    # 测试获取执行大小
    sizes = []
    while True:
        size = await executor.get_next_size()
        if size is None:
            break
        sizes.append(size)
        
        # 模拟执行结果
        result = ExecutionResult(
            executed_price=target_price * (1 + np.random.uniform(-0.002, 0.002)),
            executed_size=size,
            timestamp=datetime.now(),
            venue="binance",
            transaction_cost=size * 0.001,
            slippage=0.0004  # 较大滑点
        )
        await executor.update_execution(result)
    
    # 验证结果
    stats = executor.get_execution_stats()
    assert abs(stats["total_executed"] - total_size) < 1e-6
    assert stats["remaining_size"] < 1e-6
    assert stats["completion_rate"] > 0.99
    assert len(sizes) > config.num_splits / 2  # 由于高波动，应该分成更多笔

async def main():
    """运行所有测试"""
    print("开始测试订单分拆执行器...")
    
    try:
        print("\n测试TWAP执行...")
        await test_twap_execution()
        print("✓ TWAP执行测试通过")
        
        print("\n测试VWAP执行...")
        await test_vwap_execution()
        print("✓ VWAP执行测试通过")
        
        print("\n测试自适应执行...")
        await test_adaptive_execution()
        print("✓ 自适应执行测试通过")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 