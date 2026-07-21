import asyncio
import json
from datetime import datetime, timedelta
import numpy as np
from strategies.trend_following_strategy import TrendFollowingStrategy

async def simulate_market_data(strategy: TrendFollowingStrategy):
    """模拟市场数据"""
    # 生成趋势性的价格序列
    base_price = 1900.0
    trend_strength = 0.0003  # 上升趋势的强度
    volatility = 0.001  # 波动率
    
    # 生成价格序列
    np.random.seed(42)
    returns = np.random.normal(trend_strength, volatility, 100)  # 带有趋势的随机游走
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 生成成交量序列
    base_volume = 100.0
    volume_trend = np.linspace(1, 1.5, 100)  # 成交量逐渐增加
    volumes = base_volume * volume_trend * (1 + np.random.normal(0, 0.2, 100))
    
    # 模拟市场数据
    for i in range(len(prices)):
        # 计算当前bar的OHLC
        open_price = prices[i] * (1 - 0.0005)
        high_price = prices[i] * (1 + 0.001)
        low_price = prices[i] * (1 - 0.001)
        close_price = prices[i]
        
        market_data = {
            'timestamp': datetime.now() + timedelta(minutes=i),
            'symbol': strategy.symbol,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volumes[i],
            'price': close_price
        }
        
        # 更新策略数据
        await strategy.on_market_data(market_data)

async def test_trend_following_strategy():
    """测试趋势跟踪策略"""
    # 创建策略实例
    strategy = TrendFollowingStrategy(
        symbol='XAUUSD',
        timeframe='5m',
        lookback_periods=100,
        ma_fast=10,
        ma_slow=20,
        atr_periods=14,
        atr_multiplier=2.0,
        rsi_periods=14,
        rsi_overbought=70.0,
        rsi_oversold=30.0,
        volume_ma_periods=20,
        min_trend_strength=0.5,
        position_size_limit=1.0,
        signal_expire_seconds=300
    )
    
    # 初始化策略
    await strategy.initialize()
    
    print("开始测试趋势跟踪策略...")
    
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
            print(f"信号类型: {signal['type']}")
            print(f"方向: {signal['direction']}")
            print(f"价格: {signal['price']:.2f}")
            print(f"信号强度: {signal['strength']:.4f}")
            print(f"持仓量: {signal['position_size']:.4f}")
            print(f"止损价: {signal['stop_loss']:.2f}")
            print(f"止盈价: {signal['take_profit']:.2f}")
            print("\n技术指标:")
            print(f"快速均线: {signal['indicators']['ma_fast']:.2f}")
            print(f"慢速均线: {signal['indicators']['ma_slow']:.2f}")
            print(f"ATR: {signal['indicators']['atr']:.4f}")
            print(f"RSI: {signal['indicators']['rsi']:.2f}")
            print(f"趋势强度: {signal['indicators']['trend_strength']:.4f}")
            print(f"成交量比率: {signal['indicators']['volume_ratio']:.2f}")
            print("\n策略参数:")
            print(f"趋势强度: {signal['metadata']['trend_strength']:.4f}")
            print(f"成交量确认: {signal['metadata']['volume_confirmation']}")
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
        
    # 测试不同趋势环境
    print("\n测试不同趋势环境...")
    
    # 测试下降趋势
    print("\n测试下降趋势...")
    base_price = 1900.0
    trend_strength = -0.0003  # 下降趋势
    volatility = 0.001
    
    returns = np.random.normal(trend_strength, volatility, 100)
    prices = base_price * np.exp(np.cumsum(returns))
    volumes = base_volume * volume_trend * (1 + np.random.normal(0, 0.2, 100))
    
    for i in range(len(prices)):
        await strategy.on_market_data({
            'timestamp': datetime.now() + timedelta(minutes=i),
            'symbol': strategy.symbol,
            'open': prices[i] * (1 - 0.0005),
            'high': prices[i] * (1 + 0.001),
            'low': prices[i] * (1 - 0.001),
            'close': prices[i],
            'volume': volumes[i],
            'price': prices[i]
        })
    
    signals = await strategy.generate_signals()
    print(f"下降趋势生成信号数量: {len(signals)}")
    if signals:
        print(f"信号方向: {signals[0]['direction']}")
        
    # 测试震荡市场
    print("\n测试震荡市场...")
    trend_strength = 0.0  # 无趋势
    volatility = 0.002  # 更高的波动率
    
    returns = np.random.normal(trend_strength, volatility, 100)
    prices = base_price * np.exp(np.cumsum(returns))
    volumes = base_volume * np.ones(100) * (1 + np.random.normal(0, 0.2, 100))  # 稳定的成交量
    
    for i in range(len(prices)):
        await strategy.on_market_data({
            'timestamp': datetime.now() + timedelta(minutes=i),
            'symbol': strategy.symbol,
            'open': prices[i] * (1 - 0.0005),
            'high': prices[i] * (1 + 0.001),
            'low': prices[i] * (1 - 0.001),
            'close': prices[i],
            'volume': volumes[i],
            'price': prices[i]
        })
    
    signals = await strategy.generate_signals()
    print(f"震荡市场生成信号数量: {len(signals)}")

async def main():
    """主函数"""
    try:
        await test_trend_following_strategy()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 