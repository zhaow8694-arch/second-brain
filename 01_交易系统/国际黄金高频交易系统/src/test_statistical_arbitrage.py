import asyncio
import numpy as np
from datetime import datetime, timedelta
from strategies.statistical_arbitrage_strategy import StatisticalArbitrageStrategy

async def simulate_cointegrated_prices(periods: int = 100, mean_reversion: float = 0.02):
    """模拟协整的价格序列"""
    # 生成随机游走序列作为基准价格
    price1 = 100.0
    price2 = 100.0
    prices1 = []
    prices2 = []
    
    # 添加长期均衡关系
    equilibrium = 1.0
    
    for i in range(periods):
        # 生成相关的随机波动
        noise1 = np.random.normal(0, 0.002)
        noise2 = noise1 * 0.8 + np.random.normal(0, 0.001)
        
        # 添加均值回归
        spread = np.log(price1) - np.log(price2)
        mean_reversion_effect = -mean_reversion * (spread - np.log(equilibrium))
        
        # 更新价格
        price1 *= np.exp(noise1 + mean_reversion_effect)
        price2 *= np.exp(noise2)
        
        prices1.append(price1)
        prices2.append(price2)
        
    return prices1, prices2

async def simulate_market_data(symbol_pairs: list[tuple[str, str]], periods: int = 100):
    """模拟市场数据"""
    market_data_list = []
    
    for pair in symbol_pairs:
        # 生成协整的价格序列
        prices1, prices2 = await simulate_cointegrated_prices(periods)
        
        # 生成成交量序列
        base_volume = 100.0
        volumes1 = []
        volumes2 = []
        
        for i in range(periods):
            # 在价格变动较大时增加成交量
            price_change1 = abs(prices1[i] / prices1[i-1] - 1) if i > 0 else 0
            price_change2 = abs(prices2[i] / prices2[i-1] - 1) if i > 0 else 0
            
            volume1 = base_volume * (1 + 5 * price_change1) * (1 + np.random.normal(0, 0.2))
            volume2 = base_volume * (1 + 5 * price_change2) * (1 + np.random.normal(0, 0.2))
            
            volumes1.append(volume1)
            volumes2.append(volume2)
            
        # 生成市场数据
        for i in range(periods):
            # 第一个交易对的数据
            market_data1 = {
                'timestamp': datetime.now() + timedelta(minutes=i),
                'symbol': pair[0],
                'open': prices1[i] * (1 - 0.0005),
                'high': prices1[i] * (1 + 0.001),
                'low': prices1[i] * (1 - 0.001),
                'close': prices1[i],
                'volume': volumes1[i],
                'price': prices1[i]
            }
            market_data_list.append(market_data1)
            
            # 第二个交易对的数据
            market_data2 = {
                'timestamp': datetime.now() + timedelta(minutes=i),
                'symbol': pair[1],
                'open': prices2[i] * (1 - 0.0005),
                'high': prices2[i] * (1 + 0.001),
                'low': prices2[i] * (1 - 0.001),
                'close': prices2[i],
                'volume': volumes2[i],
                'price': prices2[i]
            }
            market_data_list.append(market_data2)
            
    return market_data_list

async def test_statistical_arbitrage():
    """测试统计套利策略"""
    print("开始测试统计套利策略...")
    
    # 定义交易对
    symbol_pairs = [
        ('BTCUSDT', 'ETHUSDT'),  # 加密货币对
        ('XAUUSD', 'XAGUSD')     # 贵金属对
    ]
    
    # 创建策略实例
    strategy = StatisticalArbitrageStrategy(
        symbol='BTCUSDT',  # 主交易对
        timeframe='5m',
        lookback_periods=50,
        z_score_threshold=2.0,
        mean_reversion_threshold=0.02,
        correlation_threshold=0.8,
        position_size_limit=1.0,
        signal_expire_seconds=300,
        pairs=symbol_pairs
    )
    
    # 初始化策略
    await strategy.initialize()
    print("策略初始化完成")
    
    # 生成模拟市场数据
    market_data_list = await simulate_market_data(symbol_pairs)
    print("\n生成模拟市场数据完成")
    
    # 测试信号生成
    print("\n开始测试信号生成...")
    signal_count = 0
    position_count = 0
    
    for market_data in market_data_list:
        # 更新市场数据
        await strategy.on_market_data(market_data)
        
        # 生成交易信号
        signals = await strategy.generate_signals()
        
        if signals:
            signal_count += len(signals)
            for signal in signals:
                position_count += 1
                print(f"\n在时间 {market_data['timestamp']} 生成新信号:")
                print(f"\n信号详情:")
                print(f"主交易对: {signal['symbol']}")
                print(f"配对交易对: {signal['pair_symbol']}")
                print(f"策略类型: {signal['type']}")
                print(f"主交易方向: {signal['direction1']}")
                print(f"配对交易方向: {signal['direction2']}")
                print(f"主交易价格: {signal['price1']:.2f}")
                print(f"配对交易价格: {signal['price2']:.2f}")
                print(f"信号强度: {signal['strength']:.4f}")
                print(f"持仓量: {signal['position_size']:.4f}")
                print(f"\n指标:")
                print(f"Z分数: {signal['indicators']['z_score']:.4f}")
                print(f"相关性: {signal['indicators']['correlation']:.4f}")
                print(f"价差: {signal['indicators']['spread']:.4f}")
                print(f"\n止损止盈:")
                print(f"主交易止损: {signal['stop_loss1']:.2f}")
                print(f"主交易止盈: {signal['take_profit1']:.2f}")
                print(f"配对交易止损: {signal['stop_loss2']:.2f}")
                print(f"配对交易止盈: {signal['take_profit2']:.2f}")
                
    print(f"\n总共生成信号数量: {signal_count}")
    print(f"总共开仓次数: {position_count}")
    
    # 测试信号过期和平仓
    print("\n测试信号过期和平仓...")
    expired_count = 0
    for signal in strategy.active_signals:
        signal['timestamp'] = datetime.now() - timedelta(seconds=strategy.signal_expire_seconds + 1)
        expired_count += 1
        
    await strategy._check_signals()
    print(f"过期信号数量: {expired_count}")
    print(f"剩余活跃信号: {len(strategy.active_signals)}")
    
async def main():
    """主函数"""
    try:
        await test_statistical_arbitrage()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 