import asyncio
import json
from datetime import datetime, timedelta
from strategies.microstructure_strategy import MicrostructureStrategy

async def simulate_market_data(strategy: MicrostructureStrategy):
    """模拟市场数据"""
    # 模拟订单簿数据
    order_book = {
        'bids': [
            ['1900.00', '2.5'],
            ['1899.50', '3.0'],
            ['1899.00', '4.0'],
            ['1898.50', '5.0'],
            ['1898.00', '6.0']
        ],
        'asks': [
            ['1900.50', '2.0'],
            ['1901.00', '2.5'],
            ['1901.50', '3.0'],
            ['1902.00', '3.5'],
            ['1902.50', '4.0']
        ]
    }
    
    # 模拟成交数据
    trades = [
        {'timestamp': datetime.now(), 'price': 1900.25, 'volume': 1.2, 'side': 'buy'},
        {'timestamp': datetime.now(), 'price': 1900.30, 'volume': 0.8, 'side': 'buy'},
        {'timestamp': datetime.now(), 'price': 1900.20, 'volume': 1.5, 'side': 'sell'},
        {'timestamp': datetime.now(), 'price': 1900.35, 'volume': 1.0, 'side': 'buy'}
    ]
    
    # 模拟市场数据
    market_data = {
        'timestamp': datetime.now(),
        'price': 1900.25,
        'volume': 1.2,
        'open': 1900.00,
        'high': 1900.50,
        'low': 1899.50,
        'close': 1900.25
    }
    
    # 更新策略数据
    await strategy.on_order_book(order_book)
    for trade in trades:
        await strategy.on_trade(trade)
    await strategy.on_market_data(market_data)

async def test_microstructure_strategy():
    """测试市场微结构策略"""
    # 创建策略实例
    strategy = MicrostructureStrategy(
        symbol='XAUUSD',
        timeframe='1m',
        lookback_periods=100,
        imbalance_threshold=0.1,
        flow_threshold=0.1,
        vwap_deviation_threshold=0.002,
        min_spread=0.0001,
        max_spread=0.005,
        min_volume=0.5,
        signal_expire_seconds=30
    )
    
    # 初始化策略
    await strategy.initialize()
    
    print("开始测试市场微结构策略...")
    
    # 模拟市场数据
    await simulate_market_data(strategy)
    
    # 生成交易信号
    signals = await strategy.generate_signals()
    
    if signals:
        print("\n生成的交易信号:")
        for signal in signals:
            print("\n信号详情:")
            print(f"时间戳: {signal['timestamp']}")
            print(f"交易对: {signal['symbol']}")
            print(f"方向: {signal['direction']}")
            print(f"价格: {signal['price']:.2f}")
            print(f"信号强度: {signal['strength']:.4f}")
            print(f"持仓量: {signal['position_size']:.4f}")
            print(f"止损价: {signal['stop_loss']:.2f}")
            print(f"止盈价: {signal['take_profit']:.2f}")
            print("\n市场微观结构特征:")
            print(f"订单簿失衡: {signal['features']['order_book_imbalance']:.4f}")
            print(f"交易流量: {signal['features']['trade_flow']:.4f}")
            print(f"VWAP偏离: {signal['metadata']['signal_basis']['vwap_deviation']:.4f}")
            print(f"价格冲击: {signal['features']['price_impact']:.6f}")
    else:
        print("\n未生成交易信号")
    
    # 测试信号过期和更新
    print("\n测试信号过期和更新...")
    await asyncio.sleep(2)  # 等待2秒
    
    # 模拟价格变动
    new_market_data = {
        'timestamp': datetime.now(),
        'price': 1901.00,  # 价格上涨
        'volume': 1.5,
        'open': 1900.25,
        'high': 1901.00,
        'low': 1900.25,
        'close': 1901.00
    }
    await strategy.on_market_data(new_market_data)
    
    # 检查活跃信号
    print(f"\n当前活跃信号数量: {len(strategy.active_signals)}")
    
    # 测试批量信号生成
    print("\n测试批量信号生成...")
    for _ in range(3):
        await simulate_market_data(strategy)
        signals = await strategy.generate_signals()
        print(f"生成信号数量: {len(signals)}")

async def main():
    """主函数"""
    try:
        await test_microstructure_strategy()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 