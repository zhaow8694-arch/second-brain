import pytest
import asyncio
from datetime import datetime, timedelta
import numpy as np
from src.strategies.trend_following import TrendFollowingStrategy
from src.strategies.microstructure import MicrostructureStrategy
from src.strategies.statistical_arbitrage import StatisticalArbitrageStrategy

@pytest.fixture
async def trend_strategy():
    """创建趋势跟踪策略实例"""
    strategy = TrendFollowingStrategy(
        symbol='BTCUSDT',
        timeframe='1h',
        ma_fast=10,
        ma_slow=20,
        atr_periods=14
    )
    await strategy.initialize()
    return strategy

@pytest.fixture
async def microstructure_strategy():
    """创建市场微观结构策略实例"""
    strategy = MicrostructureStrategy(
        symbol='BTCUSDT',
        timeframe='1m',
        lookback_periods=100
    )
    await strategy.initialize()
    return strategy

@pytest.fixture
async def arbitrage_strategy():
    """创建统计套利策略实例"""
    strategy = StatisticalArbitrageStrategy(
        symbol_pair=('BTCUSDT', 'ETHUSDT'),
        timeframe='5m',
        lookback_periods=100
    )
    await strategy.initialize()
    return strategy

def generate_market_data(base_price: float, periods: int = 100):
    """生成模拟市场数据"""
    data = []
    current_time = datetime.now()
    
    # 生成价格序列
    prices = base_price * np.exp(np.random.normal(0, 0.001, periods).cumsum())
    
    for i in range(periods):
        data.append({
            'timestamp': current_time + timedelta(minutes=i),
            'open': prices[i] * (1 - 0.0005),
            'high': prices[i] * (1 + 0.001),
            'low': prices[i] * (1 - 0.001),
            'close': prices[i],
            'volume': np.random.uniform(1, 10)
        })
    
    return data

async def test_trend_following(strategy):
    """测试趋势跟踪策略"""
    # 生成市场数据
    market_data = generate_market_data(50000.0)
    
    # 更新策略数据
    for data in market_data:
        await strategy.on_market_data(data)
    
    # 生成信号
    signals = await strategy.generate_signals()
    assert len(signals) > 0
    
    # 验证信号
    signal = signals[0]
    assert 'direction' in signal
    assert 'price' in signal
    assert 'stop_loss' in signal
    assert 'take_profit' in signal

async def test_microstructure(strategy):
    """测试市场微观结构策略"""
    # 生成订单簿数据
    orderbook = {
        'bids': [[49900, 1.0], [49800, 2.0], [49700, 3.0]],
        'asks': [[50100, 1.0], [50200, 2.0], [50300, 3.0]]
    }
    
    # 更新策略数据
    await strategy.on_orderbook(orderbook)
    
    # 生成信号
    signals = await strategy.generate_signals()
    assert len(signals) > 0
    
    # 验证信号
    signal = signals[0]
    assert 'direction' in signal
    assert 'price' in signal
    assert 'size' in signal

async def test_statistical_arbitrage(strategy):
    """测试统计套利策略"""
    # 生成配对交易数据
    data1 = generate_market_data(50000.0)
    data2 = generate_market_data(3000.0)
    
    # 更新策略数据
    for d1, d2 in zip(data1, data2):
        await strategy.on_market_data(d1, 'BTCUSDT')
        await strategy.on_market_data(d2, 'ETHUSDT')
    
    # 生成信号
    signals = await strategy.generate_signals()
    assert len(signals) > 0
    
    # 验证信号
    signal = signals[0]
    assert 'leg1' in signal
    assert 'leg2' in signal
    assert 'spread' in signal

async def main():
    """运行所有测试"""
    print("开始运行策略测试...")
    
    try:
        # 创建策略实例
        trend = await trend_strategy()
        micro = await microstructure_strategy()
        arb = await arbitrage_strategy()
        
        # 运行测试
        print("\n测试趋势跟踪策略...")
        await test_trend_following(trend)
        print("✓ 趋势跟踪策略测试通过")
        
        print("\n测试市场微观结构策略...")
        await test_microstructure(micro)
        print("✓ 市场微观结构策略测试通过")
        
        print("\n测试统计套利策略...")
        await test_statistical_arbitrage(arb)
        print("✓ 统计套利策略测试通过")
        
        print("\n所有策略测试通过！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 