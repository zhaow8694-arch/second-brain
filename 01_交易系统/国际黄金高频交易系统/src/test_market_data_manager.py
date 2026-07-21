import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from data.market_data_manager import MarketDataManager

# 用于存储接收到的数据
received_data = {
    'binance': [],
    'mt4': []
}

async def market_data_callback(data: dict):
    """市场数据回调函数"""
    source = data['source']
    symbol = data['symbol']
    timestamp = data['timestamp']
    
    if 'type' in data and data['type'] == 'orderbook':
        print(f"\n收到{source}订单簿数据:")
        print(f"交易对: {symbol}")
        print(f"时间: {timestamp}")
        print(f"买盘前5档: {data['bids'][:5]}")
        print(f"卖盘前5档: {data['asks'][:5]}")
    else:
        print(f"\n收到{source} K线数据:")
        print(f"交易对: {symbol}")
        print(f"时间: {timestamp}")
        print(f"开盘价: {data['open']:.4f}")
        print(f"最高价: {data['high']:.4f}")
        print(f"最低价: {data['low']:.4f}")
        print(f"收盘价: {data['close']:.4f}")
        print(f"成交量: {data['volume']:.4f}")
        
    # 存储数据
    received_data[source].append(data)

async def test_market_data_manager():
    """测试市场数据管理器"""
    print("开始测试市场数据管理器...")
    
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    binance_api_key = os.getenv('BINANCE_API_KEY')
    binance_api_secret = os.getenv('BINANCE_API_SECRET')
    mt4_login = int(os.getenv('MT4_LOGIN', 0))
    mt4_password = os.getenv('MT4_PASSWORD', '')
    mt4_server = os.getenv('MT4_SERVER', '')
    
    if not all([binance_api_key, binance_api_secret, mt4_login, mt4_password, mt4_server]):
        raise ValueError("请在.env文件中设置所有必要的API密钥和MT4账户信息")
        
    try:
        # 创建市场数据管理器实例
        manager = MarketDataManager(
            binance_api_key=binance_api_key,
            binance_api_secret=binance_api_secret,
            mt4_login=mt4_login,
            mt4_password=mt4_password,
            mt4_server=mt4_server
        )
        
        # 初始化连接
        await manager.initialize()
        print("市场数据管理器初始化成功")
        
        # 添加数据回调
        manager.add_callback(market_data_callback)
        
        # 订阅交易对
        # 币安交易对
        await manager.subscribe_binance('BTCUSDT')
        await manager.subscribe_binance('ETHUSDT')
        
        # MT4交易对
        await manager.subscribe_mt4('XAUUSD')
        await manager.subscribe_mt4('XAGUSD')
        
        print("\n开始接收市场数据...")
        
        # 启动数据管理器
        await manager.start()
        
        # 运行一段时间
        await asyncio.sleep(60)
        
        # 打印统计信息
        print("\n数据统计:")
        print(f"收到币安数据数量: {len(received_data['binance'])}")
        print(f"收到MT4数据数量: {len(received_data['mt4'])}")
        
        # 停止数据管理器
        await manager.stop()
        print("\n市场数据管理器已停止")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        raise
        
async def main():
    """主函数"""
    try:
        await test_market_data_manager()
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 