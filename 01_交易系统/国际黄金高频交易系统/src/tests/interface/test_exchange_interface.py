import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.interface.exchange_interface import ExchangeInterface

@pytest.fixture
def exchange_interface():
    """创建交易所接口实例"""
    return ExchangeInterface(
        exchange_name='test_exchange',
        api_key='test_api_key',
        api_secret='test_api_secret',
        testnet=True
    )

@pytest.fixture
def test_instrument():
    """创建测试交易品种"""
    return {
        'symbol': 'BTC/USDT',
        'base_currency': 'BTC',
        'quote_currency': 'USDT',
        'price_precision': 2,
        'quantity_precision': 6,
        'min_quantity': 0.001,
        'max_quantity': 100,
        'min_price': 100,
        'max_price': 100000
    }

class TestExchangeInterface:
    """交易所接口测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, exchange_interface):
        """测试接口初始化"""
        assert exchange_interface.exchange_name == 'test_exchange'
        assert exchange_interface.api_key == 'test_api_key'
        assert exchange_interface.api_secret == 'test_api_secret'
        assert exchange_interface.testnet is True
        
    @pytest.mark.asyncio
    async def test_connect(self, exchange_interface):
        """测试接口连接"""
        # 连接交易所
        success = await exchange_interface.connect()
        
        # 验证连接结果
        assert success is True
        assert exchange_interface.is_connected() is True
        
    @pytest.mark.asyncio
    async def test_authenticate(self, exchange_interface):
        """测试接口认证"""
        # 连接交易所
        await exchange_interface.connect()
        
        # 进行认证
        success = await exchange_interface.authenticate()
        
        # 验证认证结果
        assert success is True
        assert exchange_interface.is_authenticated() is True
        
    @pytest.mark.asyncio
    async def test_get_account_info(self, exchange_interface):
        """测试获取账户信息"""
        # 连接并认证
        await exchange_interface.connect()
        await exchange_interface.authenticate()
        
        # 获取账户信息
        account_info = await exchange_interface.get_account_info()
        
        # 验证账户信息
        assert isinstance(account_info, dict)
        assert 'balances' in account_info
        assert 'total_equity' in account_info
        assert 'available_equity' in account_info
        
    @pytest.mark.asyncio
    async def test_get_market_data(self, exchange_interface, test_instrument):
        """测试获取市场数据"""
        # 连接交易所
        await exchange_interface.connect()
        
        # 获取市场数据
        market_data = await exchange_interface.get_market_data(test_instrument['symbol'])
        
        # 验证市场数据
        assert isinstance(market_data, dict)
        assert 'last_price' in market_data
        assert 'bid_price' in market_data
        assert 'ask_price' in market_data
        assert 'volume' in market_data
        
    @pytest.mark.asyncio
    async def test_get_orderbook(self, exchange_interface, test_instrument):
        """测试获取订单簿"""
        # 连接交易所
        await exchange_interface.connect()
        
        # 获取订单簿
        orderbook = await exchange_interface.get_orderbook(test_instrument['symbol'])
        
        # 验证订单簿
        assert isinstance(orderbook, dict)
        assert 'bids' in orderbook
        assert 'asks' in orderbook
        assert len(orderbook['bids']) > 0
        assert len(orderbook['asks']) > 0
        
    @pytest.mark.asyncio
    async def test_place_order(self, exchange_interface, test_instrument):
        """测试下单"""
        # 连接并认证
        await exchange_interface.connect()
        await exchange_interface.authenticate()
        
        # 创建订单
        order = {
            'symbol': test_instrument['symbol'],
            'side': 'buy',
            'type': 'limit',
            'price': 50000,
            'quantity': 0.001,
            'time_in_force': 'GTC'
        }
        
        # 下单
        order_result = await exchange_interface.place_order(order)
        
        # 验证订单结果
        assert isinstance(order_result, dict)
        assert 'order_id' in order_result
        assert 'status' in order_result
        assert order_result['status'] in ['open', 'filled', 'cancelled']
        
    @pytest.mark.asyncio
    async def test_cancel_order(self, exchange_interface, test_instrument):
        """测试撤单"""
        # 连接并认证
        await exchange_interface.connect()
        await exchange_interface.authenticate()
        
        # 创建订单
        order = {
            'symbol': test_instrument['symbol'],
            'side': 'buy',
            'type': 'limit',
            'price': 50000,
            'quantity': 0.001,
            'time_in_force': 'GTC'
        }
        
        # 下单
        order_result = await exchange_interface.place_order(order)
        
        # 撤单
        cancel_result = await exchange_interface.cancel_order(order_result['order_id'])
        
        # 验证撤单结果
        assert isinstance(cancel_result, dict)
        assert 'status' in cancel_result
        assert cancel_result['status'] == 'cancelled'
        
    @pytest.mark.asyncio
    async def test_get_order_status(self, exchange_interface, test_instrument):
        """测试获取订单状态"""
        # 连接并认证
        await exchange_interface.connect()
        await exchange_interface.authenticate()
        
        # 创建订单
        order = {
            'symbol': test_instrument['symbol'],
            'side': 'buy',
            'type': 'limit',
            'price': 50000,
            'quantity': 0.001,
            'time_in_force': 'GTC'
        }
        
        # 下单
        order_result = await exchange_interface.place_order(order)
        
        # 获取订单状态
        order_status = await exchange_interface.get_order_status(order_result['order_id'])
        
        # 验证订单状态
        assert isinstance(order_status, dict)
        assert 'status' in order_status
        assert 'filled_quantity' in order_status
        assert 'remaining_quantity' in order_status
        
    @pytest.mark.asyncio
    async def test_get_trade_history(self, exchange_interface, test_instrument):
        """测试获取交易历史"""
        # 连接并认证
        await exchange_interface.connect()
        await exchange_interface.authenticate()
        
        # 获取交易历史
        trades = await exchange_interface.get_trade_history(
            symbol=test_instrument['symbol'],
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now()
        )
        
        # 验证交易历史
        assert isinstance(trades, list)
        if len(trades) > 0:
            assert 'trade_id' in trades[0]
            assert 'price' in trades[0]
            assert 'quantity' in trades[0]
            assert 'side' in trades[0]
            
    @pytest.mark.asyncio
    async def test_get_positions(self, exchange_interface, test_instrument):
        """测试获取持仓信息"""
        # 连接并认证
        await exchange_interface.connect()
        await exchange_interface.authenticate()
        
        # 获取持仓信息
        positions = await exchange_interface.get_positions()
        
        # 验证持仓信息
        assert isinstance(positions, list)
        for position in positions:
            assert 'symbol' in position
            assert 'quantity' in position
            assert 'entry_price' in position
            assert 'unrealized_pnl' in position
            
    @pytest.mark.asyncio
    async def test_error_handling(self, exchange_interface):
        """测试错误处理"""
        # 测试无效的API密钥
        invalid_interface = ExchangeInterface(
            exchange_name='test_exchange',
            api_key='invalid_key',
            api_secret='invalid_secret',
            testnet=True
        )
        
        # 尝试连接
        success = await invalid_interface.connect()
        assert success is False
        
        # 测试无效的交易品种
        with pytest.raises(ValueError):
            await exchange_interface.get_market_data('INVALID/SYMBOL')
            
    @pytest.mark.asyncio
    async def test_rate_limiting(self, exchange_interface, test_instrument):
        """测试速率限制"""
        # 连接交易所
        await exchange_interface.connect()
        
        # 快速发送多个请求
        tasks = []
        for _ in range(10):
            tasks.append(exchange_interface.get_market_data(test_instrument['symbol']))
            
        # 等待所有请求完成
        results = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功完成
        assert len(results) == 10
        assert all(isinstance(result, dict) for result in results) 