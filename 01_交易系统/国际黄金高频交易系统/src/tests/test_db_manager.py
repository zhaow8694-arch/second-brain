import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from loguru import logger
from src.utils.db_manager import DatabaseManager

# 测试配置
TEST_SYMBOL = "BTCUSDT"
TEST_SOURCE = "binance"

@pytest.fixture
async def db_manager():
    """创建数据库管理器实例"""
    manager = DatabaseManager(
        host='localhost',
        port=3306,
        user='root',
        password='',
        database='trading_system_test'
    )
    await manager.connect()
    await manager.init_tables()
    yield manager
    await manager.disconnect()

@pytest.mark.asyncio
async def test_save_market_data(db_manager):
    """测试保存市场数据"""
    # 准备测试数据
    data = {
        'timestamp': datetime.now(),
        'symbol': TEST_SYMBOL,
        'source': TEST_SOURCE,
        'price': 50000.0,
        'volume': 1.5,
        'bid_price': 49999.0,
        'ask_price': 50001.0,
        'open': 49900.0,
        'high': 50100.0,
        'low': 49800.0
    }
    
    # 保存数据
    success = await db_manager.save_market_data(data)
    assert success
    
    # 验证数据
    start_time = datetime.now() - timedelta(minutes=1)
    end_time = datetime.now() + timedelta(minutes=1)
    market_data = await db_manager.get_market_data(
        TEST_SYMBOL, start_time, end_time, TEST_SOURCE
    )
    
    assert len(market_data) > 0
    assert market_data[0]['symbol'] == TEST_SYMBOL
    assert market_data[0]['source'] == TEST_SOURCE
    assert float(market_data[0]['price']) == 50000.0

@pytest.mark.asyncio
async def test_save_trading_signal(db_manager):
    """测试保存交易信号"""
    # 准备测试数据
    data = {
        'timestamp': datetime.now(),
        'symbol': TEST_SYMBOL,
        'signal_type': 'price_breakout',
        'direction': 'buy',
        'price': 50000.0,
        'confidence': 0.85,
        'metadata': {
            'breakout_level': 50000.0,
            'volume': 100.0
        }
    }
    
    # 保存数据
    success = await db_manager.save_trading_signal(data)
    assert success

@pytest.mark.asyncio
async def test_save_order(db_manager):
    """测试保存交易订单"""
    # 准备测试数据
    data = {
        'order_id': 'test_order_001',
        'timestamp': datetime.now(),
        'symbol': TEST_SYMBOL,
        'order_type': 'market',
        'direction': 'buy',
        'price': 50000.0,
        'volume': 0.1,
        'status': 'filled',
        'metadata': {
            'execution_time': 0.5,
            'slippage': 0.1
        }
    }
    
    # 保存数据
    success = await db_manager.save_order(data)
    assert success

@pytest.mark.asyncio
async def test_get_market_data(db_manager):
    """测试获取市场数据"""
    # 准备测试数据
    now = datetime.now()
    data = {
        'timestamp': now,
        'symbol': TEST_SYMBOL,
        'source': TEST_SOURCE,
        'price': 50000.0,
        'volume': 1.5,
        'bid_price': 49999.0,
        'ask_price': 50001.0
    }
    
    # 保存数据
    await db_manager.save_market_data(data)
    
    # 获取数据
    start_time = now - timedelta(minutes=1)
    end_time = now + timedelta(minutes=1)
    market_data = await db_manager.get_market_data(
        TEST_SYMBOL, start_time, end_time, TEST_SOURCE
    )
    
    assert len(market_data) > 0
    assert market_data[0]['symbol'] == TEST_SYMBOL
    assert market_data[0]['source'] == TEST_SOURCE
    assert float(market_data[0]['price']) == 50000.0

@pytest.mark.asyncio
async def test_error_handling(db_manager):
    """测试错误处理"""
    # 测试无效的市场数据
    invalid_data = {
        'timestamp': datetime.now(),
        'symbol': TEST_SYMBOL
        # 缺少必要的字段
    }
    
    success = await db_manager.save_market_data(invalid_data)
    assert not success
    
    # 测试无效的交易信号
    invalid_signal = {
        'timestamp': datetime.now(),
        'symbol': TEST_SYMBOL
        # 缺少必要的字段
    }
    
    success = await db_manager.save_trading_signal(invalid_signal)
    assert not success
    
    # 测试无效的订单
    invalid_order = {
        'timestamp': datetime.now(),
        'symbol': TEST_SYMBOL
        # 缺少必要的字段
    }
    
    success = await db_manager.save_order(invalid_order)
    assert not success 