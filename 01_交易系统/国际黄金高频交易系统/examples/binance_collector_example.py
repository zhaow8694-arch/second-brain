import asyncio
import os
from datetime import datetime, timedelta
from loguru import logger

from src.core.market.collector.base import DataType
from src.core.market.collector.binance import BinanceCollector

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

async def main():
    """主函数"""
    # 从环境变量获取API密钥
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return
    
    # 创建数据采集器
    config = {
        'api_key': api_key,
        'api_secret': api_secret
    }
    collector = BinanceCollector(config)
    
    try:
        # 连接到Binance
        if not await collector.connect():
            logger.error("Failed to connect to Binance")
            return
        
        # 订阅数据
        symbol = 'BTCUSDT'
        
        # 订阅K线数据
        await collector.subscribe(symbol, DataType.KLINE)
        collector.add_subscriber(DataType.KLINE, handle_kline_data)
        
        # 订阅实时行情数据
        await collector.subscribe(symbol, DataType.TICK)
        collector.add_subscriber(DataType.TICK, handle_tick_data)
        
        # 订阅成交记录数据
        await collector.subscribe(symbol, DataType.TRADE)
        collector.add_subscriber(DataType.TRADE, handle_trade_data)
        
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
            '1m'
        )
        logger.info(f"Retrieved {len(klines)} kline records")
        
        # 获取历史成交记录
        logger.info("Fetching historical trade data...")
        trades = await collector.get_historical_data(
            symbol,
            DataType.TRADE,
            start_time,
            end_time
        )
        logger.info(f"Retrieved {len(trades)} trade records")
        
        # 运行一段时间以接收实时数据
        logger.info("Starting to receive real-time data...")
        collector.is_running = True
        await asyncio.sleep(300)  # 运行5分钟
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
    finally:
        # 断开连接
        collector.is_running = False
        await collector.disconnect()

if __name__ == "__main__":
    # 设置日志
    logger.add(
        "logs/binance_collector_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # 运行主函数
    asyncio.run(main()) 