import os
import time
from loguru import logger
from src.data_collection.binance_collector import BinanceDataCollector

def on_kline(data):
    """处理K线数据"""
    logger.info(f"收到K线数据: {data}")

def on_trade(data):
    """处理成交数据"""
    logger.info(f"收到成交数据: {data}")

def on_depth(data):
    """处理深度数据"""
    logger.info(f"收到深度数据: {data}")

def main():
    # 配置日志
    logger.add("logs/binance_websocket.log", rotation="500 MB")
    
    # 从环境变量获取API密钥
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("请设置BINANCE_API_KEY和BINANCE_API_SECRET环境变量")
        return
    
    # 创建采集器实例
    collector = BinanceDataCollector(api_key=api_key, api_secret=api_secret)
    
    try:
        # 订阅BTCUSDT的1分钟K线数据
        collector.subscribe_kline("BTCUSDT", "1m", on_kline)
        logger.info("已订阅BTCUSDT 1分钟K线数据")
        
        # 订阅BTCUSDT的实时成交数据
        collector.subscribe_trade("BTCUSDT", on_trade)
        logger.info("已订阅BTCUSDT实时成交数据")
        
        # 订阅BTCUSDT的深度数据
        collector.subscribe_depth("BTCUSDT", on_depth)
        logger.info("已订阅BTCUSDT深度数据")
        
        # 保持程序运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("正在关闭连接...")
    finally:
        # 关闭连接
        collector.close()
        logger.info("连接已关闭")

if __name__ == "__main__":
    main() 