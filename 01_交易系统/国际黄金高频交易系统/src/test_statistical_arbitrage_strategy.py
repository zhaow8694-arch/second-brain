import asyncio
import json
from datetime import datetime, timedelta
import numpy as np
from strategies.statistical_arbitrage_strategy import StatisticalArbitrageStrategy

async def simulate_market_data(strategy: StatisticalArbitrageStrategy):
    """模拟市场数据"""
    # 生成相关的价格序列
    base_price_1 = 1900.0
    base_price_2 = 1000.0
    correlation = 0.8
    
    # 生成相关的随机价格变动
    np.random.seed(42)
    returns_1 = np.random.normal(0, 0.001, 100)
    returns_2 = correlation * returns_1 + np.sqrt(1 - correlation**2) * np.random.normal(0, 0.001, 100)
    
    prices_1 = base_price_1 * np.exp(np.cumsum(returns_1))
    prices_2 = base_price_2 * np.exp(np.cumsum(returns_2))
    
    # 模拟市场数据
    for i in range(len(prices_1)):
        # 第一个交易对的数据
        market_data_1 = {
            'symbol': strategy.symbol_pair[0],
            'timestamp': datetime.now() + timedelta(minutes=i),
            'price': prices_1[i],
            'volume': np.random.uniform(1, 5),
            'open': prices_1[i] * (1 - 0.0005),
            'high': prices_1[i] * (1 + 0.0005),
            'low': prices_1[i] * (1 - 0.0005),
            'close': prices_1[i]
        }
        
        # 第二个交易对的数据
        market_data_2 = {
            'symbol': strategy.symbol_pair[1],
            'timestamp': datetime.now() + timedelta(minutes=i),
            'price': prices_2[i],
            'volume': np.random.uniform(1, 5),
            'open': prices_2[i] * (1 - 0.0005),
            'high': prices_2[i] * (1 + 0.0005),
            'low': prices_2[i] * (1 - 0.0005),
            'close': prices_2[i]
        }
        
        # 更新策略数据
        await strategy.on_market_data(market_data_1)
        await strategy.on_market_data(market_data_2)

async def test_statistical_arbitrage_strategy():
    """测试统计套利策略"""
    # 创建策略实例
    strategy = StatisticalArbitrageStrategy(
        symbol_pair=('XAUUSD', 'XAGUSD'),
        timeframe='1m',
        lookback_periods=100,
        z_score_threshold=2.0,
        correlation_threshold=0.7,
        half_life=60,
        min_profit_threshold=0.001,
        position_size_limit=1.0,
        signal_expire_seconds=300
    )
    
    # 初始化策略
    await strategy.initialize()
    
    print("开始测试统计套利策略...")
    
    # 模拟市场数据
    await simulate_market_data(strategy)
    
    # 生成交易信号
    signals = await strategy.generate_signals()
    
    if signals:
        print("\n生成的交易信号:")
        for signal in signals:
            print("\n信号详情:")
            print(f"时间戳: {signal['timestamp']}")
            print(f"信号类型: {signal['type']}")
            print("\n第一腿:")
            print(f"交易对: {signal['leg1']['symbol']}")
            print(f"方向: {signal['leg1']['direction']}")
            print(f"价格: {signal['leg1']['price']:.2f}")
            print(f"数量: {signal['leg1']['size']:.4f}")
            print("\n第二腿:")
            print(f"交易对: {signal['leg2']['symbol']}")
            print(f"方向: {signal['leg2']['direction']}")
            print(f"价格: {signal['leg2']['price']:.2f}")
            print(f"数量: {signal['leg2']['size']:.4f}")
            print("\n统计指标:")
            print(f"信号强度: {signal['strength']:.4f}")
            print(f"Z分数: {signal['z_score']:.4f}")
            print(f"相关性: {signal['correlation']:.4f}")
            print(f"半衰期: {signal['half_life']:.2f}")
            print(f"预期利润: {signal['expected_profit']:.6f}")
            print(f"止损价差: {signal['stop_loss_spread']:.6f}")
            print(f"止盈价差: {signal['take_profit_spread']:.6f}")
            print("\n策略参数:")
            print(f"均值: {signal['metadata']['mean_spread']:.6f}")
            print(f"标准差: {signal['metadata']['spread_std']:.6f}")
            print(f"Beta: {signal['metadata']['beta']:.4f}")
    else:
        print("\n未生成交易信号")
    
    # 测试信号过期和更新
    print("\n测试信号过期和更新...")
    await asyncio.sleep(2)  # 等待2秒
    
    # 检查活跃信号
    print(f"\n当前活跃信号数量: {len(strategy.active_signals)}")
    
    # 测试批量信号生成
    print("\n测试批量信号生成...")
    for _ in range(3):
        await simulate_market_data(strategy)
        signals = await strategy.generate_signals()
        print(f"生成信号数量: {len(signals)}")
        
    # 测试相关性过滤
    print("\n测试相关性过滤...")
    # 生成低相关性的数据
    base_price_1 = 1900.0
    base_price_2 = 1000.0
    returns_1 = np.random.normal(0, 0.001, 100)
    returns_2 = np.random.normal(0, 0.001, 100)  # 独立的随机游走
    
    prices_1 = base_price_1 * np.exp(np.cumsum(returns_1))
    prices_2 = base_price_2 * np.exp(np.cumsum(returns_2))
    
    for i in range(len(prices_1)):
        await strategy.on_market_data({
            'symbol': strategy.symbol_pair[0],
            'timestamp': datetime.now() + timedelta(minutes=i),
            'price': prices_1[i],
            'volume': 1.0,
            'open': prices_1[i],
            'high': prices_1[i],
            'low': prices_1[i],
            'close': prices_1[i]
        })
        await strategy.on_market_data({
            'symbol': strategy.symbol_pair[1],
            'timestamp': datetime.now() + timedelta(minutes=i),
            'price': prices_2[i],
            'volume': 1.0,
            'open': prices_2[i],
            'high': prices_2[i],
            'low': prices_2[i],
            'close': prices_2[i]
        })
    
    signals = await strategy.generate_signals()
    print(f"低相关性数据生成信号数量: {len(signals)}")

async def main():
    """主函数"""
    try:
        await test_statistical_arbitrage_strategy()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 