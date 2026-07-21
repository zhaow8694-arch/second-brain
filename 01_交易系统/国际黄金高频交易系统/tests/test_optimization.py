import pytest
import asyncio
from datetime import datetime, timedelta
import numpy as np
from src.execution.order_split import OrderSplitter
from src.execution.price_calculator import PriceCalculator
from src.execution.slippage_predictor import SlippagePredictor
from src.execution.smart_router import SmartRouter

@pytest.fixture
async def order_splitter():
    """创建订单拆分器实例"""
    splitter = OrderSplitter(
        min_size=0.001,
        max_size=1.0,
        time_window=300
    )
    await splitter.initialize()
    return splitter

@pytest.fixture
async def price_calculator():
    """创建价格计算器实例"""
    calculator = PriceCalculator(
        spread_factor=0.0002,
        impact_factor=0.0001
    )
    await calculator.initialize()
    return calculator

@pytest.fixture
async def slippage_predictor():
    """创建滑点预测器实例"""
    predictor = SlippagePredictor(
        lookback_window=100,
        volatility_window=20
    )
    await predictor.initialize()
    return predictor

@pytest.fixture
async def smart_router():
    """创建智能路由器实例"""
    router = SmartRouter(
        venues=['binance', 'huobi', 'okex'],
        min_venue_count=2
    )
    await router.initialize()
    return router

def generate_market_data(base_price: float, periods: int = 100):
    """生成模拟市场数据"""
    data = []
    current_time = datetime.now()
    
    # 生成价格序列
    prices = base_price * np.exp(np.random.normal(0, 0.001, periods).cumsum())
    
    for i in range(periods):
        data.append({
            'timestamp': current_time + timedelta(minutes=i),
            'price': prices[i],
            'volume': np.random.uniform(1, 10),
            'bid_price': prices[i] * (1 - 0.0002),
            'ask_price': prices[i] * (1 + 0.0002)
        })
    
    return data

async def test_order_splitting(splitter):
    """测试订单拆分"""
    # 测试大订单拆分
    order = {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'size': 5.0,
        'price': 50000.0
    }
    
    splits = await splitter.split_order(order)
    assert len(splits) > 1
    assert sum(s['size'] for s in splits) == order['size']
    
    # 验证每个拆分订单的大小限制
    for split in splits:
        assert split['size'] <= splitter.max_size
        assert split['size'] >= splitter.min_size

async def test_price_calculation(calculator):
    """测试价格计算"""
    # 生成市场数据
    market_data = generate_market_data(50000.0)
    
    # 测试买入价格计算
    buy_price = await calculator.calculate_price(
        side='buy',
        size=1.0,
        market_data=market_data[-1]
    )
    assert buy_price > market_data[-1]['price']
    
    # 测试卖出价格计算
    sell_price = await calculator.calculate_price(
        side='sell',
        size=1.0,
        market_data=market_data[-1]
    )
    assert sell_price < market_data[-1]['price']

async def test_slippage_prediction(predictor):
    """测试滑点预测"""
    # 生成市场数据
    market_data = generate_market_data(50000.0)
    
    # 更新预测器数据
    for data in market_data:
        await predictor.update_market_data(data)
    
    # 预测滑点
    slippage = await predictor.predict_slippage(
        size=1.0,
        side='buy'
    )
    assert slippage > 0
    assert slippage < 0.01  # 滑点应该在合理范围内

async def test_smart_routing(router):
    """测试智能路由"""
    # 更新交易所指标
    await router.update_venue_metrics('binance', {
        'liquidity': 0.9,
        'latency': 50,
        'cost': 0.001
    })
    
    await router.update_venue_metrics('huobi', {
        'liquidity': 0.8,
        'latency': 100,
        'cost': 0.002
    })
    
    # 测试订单路由
    order = {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'size': 1.0,
        'price': 50000.0
    }
    
    routes = await router.route_order(order)
    assert len(routes) >= router.min_venue_count
    assert sum(r['size'] for r in routes) == order['size']

async def main():
    """运行所有测试"""
    print("开始运行执行优化测试...")
    
    try:
        # 创建测试实例
        splitter = await order_splitter()
        calculator = await price_calculator()
        predictor = await slippage_predictor()
        router = await smart_router()
        
        # 运行测试
        print("\n测试订单拆分...")
        await test_order_splitting(splitter)
        print("✓ 订单拆分测试通过")
        
        print("\n测试价格计算...")
        await test_price_calculation(calculator)
        print("✓ 价格计算测试通过")
        
        print("\n测试滑点预测...")
        await test_slippage_prediction(predictor)
        print("✓ 滑点预测测试通过")
        
        print("\n测试智能路由...")
        await test_smart_routing(router)
        print("✓ 智能路由测试通过")
        
        print("\n所有执行优化测试通过！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 