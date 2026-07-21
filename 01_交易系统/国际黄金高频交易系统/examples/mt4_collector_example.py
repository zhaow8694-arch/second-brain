import asyncio
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from src.core.market.collector.base import DataType
from src.core.market.collector.mt4 import MT4Collector

async def handle_kline_data(data):
    """处理K线数据"""
    logger.info(f"Received Kline data: {data.symbol} - {data.timestamp}")
    logger.info(f"Open: {data.open_price}, High: {data.high_price}, "
                f"Low: {data.low_price}, Close: {data.close_price}, "
                f"Volume: {data.volume}")

async def handle_tick_data(data):
    """处理实时行情数据"""
    logger.info(f"Received Tick data: {data.symbol} - {data.timestamp}")
    logger.info(f"Last: {data.last_price}, Bid: {data.bid_price}, "
                f"Ask: {data.ask_price}, Volume: {data.volume_24h}")

async def handle_trade_data(data):
    """处理成交记录数据"""
    logger.info(f"Received Trade data: {data.symbol} - {data.timestamp}")
    logger.info(f"Price: {data.price}, Volume: {data.volume}, "
                f"Side: {data.side}, Order ID: {data.order_id}")

def create_sample_data(data_dir: Path):
    """创建示例数据文件"""
    # 创建K线数据文件
    kline_file = data_dir / 'BTCUSDT_kline.csv'
    with open(kline_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'interval'
        ])
        writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'open': '35000.00',
            'high': '36000.00',
            'low': '34000.00',
            'close': '35500.00',
            'volume': '100.00',
            'interval': '1h'
        })
    
    # 创建实时行情数据文件
    tick_file = data_dir / 'BTCUSDT_tick.csv'
    with open(tick_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'timestamp', 'last', 'bid', 'ask', 'bid_volume', 'ask_volume', 'volume_24h'
        ])
        writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last': '35500.00',
            'bid': '35400.00',
            'ask': '35600.00',
            'bid_volume': '10.00',
            'ask_volume': '5.00',
            'volume_24h': '1000.00'
        })
    
    # 创建成交记录数据文件
    trade_file = data_dir / 'BTCUSDT_trade.csv'
    with open(trade_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'timestamp', 'price', 'volume', 'side', 'order_id'
        ])
        writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': '35500.00',
            'volume': '1.00',
            'side': 'buy',
            'order_id': '123456'
        })

async def simulate_mt4_data(data_dir: Path):
    """模拟MT4数据更新"""
    while True:
        # 更新K线数据
        kline_file = data_dir / 'BTCUSDT_kline.csv'
        with open(kline_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'interval'
            ])
            writer.writerow({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'open': '35500.00',
                'high': '36500.00',
                'low': '35000.00',
                'close': '36000.00',
                'volume': '150.00',
                'interval': '1h'
            })
        
        # 更新实时行情数据
        tick_file = data_dir / 'BTCUSDT_tick.csv'
        with open(tick_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'last', 'bid', 'ask', 'bid_volume', 'ask_volume', 'volume_24h'
            ])
            writer.writerow({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last': '36000.00',
                'bid': '35900.00',
                'ask': '36100.00',
                'bid_volume': '15.00',
                'ask_volume': '8.00',
                'volume_24h': '1500.00'
            })
        
        # 更新成交记录数据
        trade_file = data_dir / 'BTCUSDT_trade.csv'
        with open(trade_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'price', 'volume', 'side', 'order_id'
            ])
            writer.writerow({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'price': '36000.00',
                'volume': '2.00',
                'side': 'sell',
                'order_id': '123457'
            })
        
        await asyncio.sleep(1)  # 每秒更新一次数据

async def main():
    """主函数"""
    # 创建数据目录
    data_dir = Path('data/mt4')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建示例数据文件
    create_sample_data(data_dir)
    
    # 创建数据采集器
    config = {
        'data_dir': str(data_dir)
    }
    collector = MT4Collector(config)
    
    try:
        # 连接到MT4数据目录
        if not await collector.connect():
            logger.error("Failed to connect to MT4 data directory")
            return
        
        # 订阅数据
        symbol = 'BTCUSDT'
        
        # 订阅K线数据
        await collector.subscribe(symbol, DataType.KLINE)
        collector.add_subscriber(handle_kline_data)
        
        # 订阅实时行情数据
        await collector.subscribe(symbol, DataType.TICK)
        collector.add_subscriber(handle_tick_data)
        
        # 订阅成交记录数据
        await collector.subscribe(symbol, DataType.TRADE)
        collector.add_subscriber(handle_trade_data)
        
        # 获取历史数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        # 获取历史K线数据
        logger.info("Fetching historical kline data...")
        klines = await collector.get_historical_data(
            symbol,
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        logger.info(f"Retrieved {len(klines)} kline records")
        
        # 获取历史实时行情数据
        logger.info("Fetching historical tick data...")
        ticks = await collector.get_historical_data(
            symbol,
            DataType.TICK,
            start_time,
            end_time
        )
        logger.info(f"Retrieved {len(ticks)} tick records")
        
        # 获取历史成交记录
        logger.info("Fetching historical trade data...")
        trades = await collector.get_historical_data(
            symbol,
            DataType.TRADE,
            start_time,
            end_time
        )
        logger.info(f"Retrieved {len(trades)} trade records")
        
        # 启动数据模拟任务
        collector.is_running = True
        simulation_task = asyncio.create_task(simulate_mt4_data(data_dir))
        
        # 运行一段时间以接收实时数据
        logger.info("Starting to receive real-time data...")
        await asyncio.sleep(300)  # 运行5分钟
        
        # 停止数据模拟
        simulation_task.cancel()
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
    finally:
        # 断开连接
        collector.is_running = False
        await collector.disconnect()

if __name__ == "__main__":
    # 设置日志
    logger.add(
        "logs/mt4_collector_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # 运行主函数
    asyncio.run(main()) 