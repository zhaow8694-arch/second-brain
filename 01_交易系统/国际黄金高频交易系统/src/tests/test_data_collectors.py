import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from loguru import logger
from src.data_collectors.collector_manager import CollectorManager
from src.data_collectors.binance_collector import BinanceDataCollector
from src.data_collectors.mt4_collector import MT4DataCollector

# 测试配置
TEST_SYMBOL = "BTCUSDT"  # 测试交易对
TEST_SYMBOL_MT4 = "XAUUSD"  # MT4测试交易对

@pytest.fixture
async def collector_manager():
    """创建数据采集管理器实例"""
    manager = CollectorManager()
    yield manager
    await manager.stop()

@pytest.fixture
async def binance_collector():
    """创建币安数据采集器实例"""
    collector = BinanceDataCollector()
    yield collector
    await collector.stop()

@pytest.fixture
async def mt4_collector():
    """创建MT4数据采集器实例"""
    collector = MT4DataCollector()
    yield collector
    await collector.stop()

@pytest.mark.asyncio
async def test_binance_collector_connection(binance_collector):
    """测试币安数据采集器连接"""
    success = await binance_collector.connect()
    assert success
    assert binance_collector.connected
    
    success = await binance_collector.disconnect()
    assert success
    assert not binance_collector.connected

@pytest.mark.asyncio
async def test_mt4_collector_connection(mt4_collector):
    """测试MT4数据采集器连接"""
    success = await mt4_collector.connect()
    assert success
    assert mt4_collector.connected
    
    success = await mt4_collector.disconnect()
    assert success
    assert not mt4_collector.connected

@pytest.mark.asyncio
async def test_binance_market_data(binance_collector):
    """测试币安市场数据获取"""
    await binance_collector.connect()
    data = await binance_collector.fetch_market_data(TEST_SYMBOL)
    
    assert data
    assert 'symbol' in data
    assert 'price' in data
    assert 'volume' in data
    assert 'bid_price' in data
    assert 'ask_price' in data
    assert 'timestamp' in data
    
    await binance_collector.disconnect()

@pytest.mark.asyncio
async def test_mt4_market_data(mt4_collector):
    """测试MT4市场数据获取"""
    await mt4_collector.connect()
    data = await mt4_collector.fetch_market_data(TEST_SYMBOL_MT4)
    
    assert data
    assert 'symbol' in data
    assert 'price' in data
    assert 'volume' in data
    assert 'bid_price' in data
    assert 'ask_price' in data
    assert 'timestamp' in data
    
    await mt4_collector.disconnect()

@pytest.mark.asyncio
async def test_collector_manager(collector_manager):
    """测试数据采集管理器"""
    # 启动管理器
    await collector_manager.start()
    assert collector_manager.running
    
    # 测试市场数据获取
    data = await collector_manager.fetch_market_data(TEST_SYMBOL, 'binance')
    assert data
    assert 'symbol' in data
    assert 'price' in data
    
    # 测试订单簿数据获取
    orderbook = await collector_manager.fetch_orderbook(TEST_SYMBOL, 'binance')
    assert orderbook
    assert 'bids' in orderbook
    assert 'asks' in orderbook
    
    # 测试成交数据获取
    trades = await collector_manager.fetch_trades(TEST_SYMBOL, limit=10, source='binance')
    assert trades
    assert len(trades) <= 10
    
    # 停止管理器
    await collector_manager.stop()
    assert not collector_manager.running

@pytest.mark.asyncio
async def test_collector_callbacks(collector_manager):
    """测试数据采集回调功能"""
    received_data = []
    
    async def callback(data: Dict[str, Any]):
        received_data.append(data)
        
    # 添加回调
    collector_manager.add_callback(callback)
    
    # 启动管理器并订阅数据
    await collector_manager.start()
    await collector_manager.subscribe_market_data(TEST_SYMBOL, 'binance')
    
    # 等待一段时间接收数据
    await asyncio.sleep(5)
    
    # 验证是否收到数据
    assert len(received_data) > 0
    
    # 移除回调
    collector_manager.remove_callback(callback)
    
    # 停止管理器
    await collector_manager.stop()

@pytest.mark.asyncio
async def test_collector_error_handling(collector_manager):
    """测试数据采集错误处理"""
    # 测试无效的交易对
    data = await collector_manager.fetch_market_data("INVALID_SYMBOL", 'binance')
    assert not data
    
    # 测试无效的数据源
    data = await collector_manager.fetch_market_data(TEST_SYMBOL, 'invalid_source')
    assert not data
    
    # 测试断开连接后的操作
    await collector_manager.stop()
    data = await collector_manager.fetch_market_data(TEST_SYMBOL, 'binance')
    assert not data 