import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position, OrderBook

class TestMarketMakingStrategy:
    """做市商策略测试类"""
    
    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        return MarketMakingStrategy(
            spread_multiplier=1.5,
            min_spread=0.001,
            max_position_size=10.0,
            inventory_target=0.0,
            inventory_risk_limit=5.0,
            order_refresh_interval=60
        )
    
    @pytest.fixture
    def test_instrument(self):
        """创建测试交易品种"""
        return {
            'symbol': 'GOLD',
            'price': 50000.0,
            'volatility': 0.01
        }
    
    @pytest.fixture
    def test_order_book(self):
        """创建测试订单簿"""
        return OrderBook(
            bids=[
                {'price': 49999.0, 'quantity': 1.0},
                {'price': 49998.0, 'quantity': 2.0},
                {'price': 49997.0, 'quantity': 3.0}
            ],
            asks=[
                {'price': 50001.0, 'quantity': 1.0},
                {'price': 50002.0, 'quantity': 2.0},
                {'price': 50003.0, 'quantity': 3.0}
            ],
            timestamp=datetime.now()
        )
    
    async def test_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.spread_multiplier == 1.5
        assert strategy.min_spread == 0.001
        assert strategy.max_position_size == 10.0
        assert strategy.inventory_target == 0.0
        assert strategy.inventory_risk_limit == 5.0
        assert strategy.order_refresh_interval == 60
        assert strategy.positions == {}
        assert strategy.active_orders == {}
    
    async def test_spread_calculation(self, strategy, test_instrument):
        """测试价差计算"""
        # 计算基础价差
        base_spread = await strategy.calculate_base_spread(
            test_instrument['price'],
            test_instrument['volatility']
        )
        
        # 验证价差
        assert base_spread > 0
        assert base_spread >= strategy.min_spread
        
        # 计算调整后的价差
        adjusted_spread = await strategy.calculate_adjusted_spread(
            base_spread,
            inventory_imbalance=0.5
        )
        
        # 验证调整后的价差
        assert adjusted_spread > base_spread  # 库存不平衡时价差应该更大
    
    async def test_order_generation(self, strategy, test_instrument, test_order_book):
        """测试订单生成"""
        # 生成市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']},
            order_book=test_order_book
        )
        
        # 生成订单
        orders = await strategy.generate_orders(market_state)
        
        # 验证订单
        assert len(orders) > 0
        for order in orders:
            assert order.instrument_id == 'GOLD'
            assert order.quantity > 0
            assert order.price > 0
            assert order.order_type in ['LIMIT', 'MARKET']
    
    async def test_inventory_management(self, strategy, test_instrument):
        """测试库存管理"""
        # 创建初始仓位
        position = Position(
            instrument_id='GOLD',
            quantity=2.0,
            entry_price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 添加仓位
        await strategy.add_position(position)
        
        # 计算库存不平衡
        imbalance = await strategy.calculate_inventory_imbalance()
        
        # 验证库存不平衡
        assert imbalance > 0  # 多头仓位应该产生正的库存不平衡
        
        # 更新目标库存
        await strategy.update_inventory_target(-1.0)
        
        # 验证目标库存更新
        assert strategy.inventory_target == -1.0
    
    async def test_risk_management(self, strategy, test_instrument):
        """测试风险管理"""
        # 创建大仓位
        position = Position(
            instrument_id='GOLD',
            quantity=20.0,  # 超过最大仓位限制
            entry_price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 验证仓位限制
        with pytest.raises(ValueError):
            await strategy.add_position(position)
        
        # 验证库存风险限制
        await strategy.add_position(
            Position(
                instrument_id='GOLD',
                quantity=1.0,
                entry_price=test_instrument['price'],
                timestamp=datetime.now()
            )
        )
        
        # 检查库存风险
        assert await strategy.check_inventory_risk()
    
    async def test_order_refresh(self, strategy, test_instrument, test_order_book):
        """测试订单刷新"""
        # 生成初始订单
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']},
            order_book=test_order_book
        )
        
        initial_orders = await strategy.generate_orders(market_state)
        
        # 添加订单到活动订单列表
        for order in initial_orders:
            strategy.active_orders[order.order_id] = order
        
        # 模拟时间流逝
        strategy.last_refresh_time = datetime.now() - timedelta(seconds=strategy.order_refresh_interval + 1)
        
        # 刷新订单
        refreshed_orders = await strategy.refresh_orders(market_state)
        
        # 验证订单刷新
        assert len(refreshed_orders) > 0
        assert len(strategy.active_orders) == 0  # 旧订单应该被取消
    
    async def test_performance_metrics(self, strategy, test_instrument):
        """测试性能指标"""
        # 添加交易历史
        trade = {
            'timestamp': datetime.now(),
            'instrument_id': 'GOLD',
            'side': 'BUY',
            'quantity': 1.0,
            'price': test_instrument['price'],
            'profit': 100.0
        }
        strategy.trade_history.append(trade)
        
        # 计算性能指标
        metrics = await strategy.calculate_performance_metrics()
        
        # 验证指标
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'inventory_turnover' in metrics
        assert metrics['total_trades'] == 1
        assert 0 <= metrics['win_rate'] <= 1
    
    async def test_strategy_adaptation(self, strategy, test_instrument, test_order_book):
        """测试策略适应性"""
        # 初始市场状态
        initial_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']},
            order_book=test_order_book
        )
        
        # 获取初始订单
        initial_orders = await strategy.generate_orders(initial_state)
        
        # 模拟市场变化
        volatile_state = MarketState(
            timestamp=datetime.now() + timedelta(hours=1),
            prices={'GOLD': test_instrument['price'] * 1.02},
            volumes={'GOLD': 2000.0},
            volatility={'GOLD': test_instrument['volatility'] * 2},
            order_book=test_order_book
        )
        
        # 获取新订单
        new_orders = await strategy.generate_orders(volatile_state)
        
        # 验证策略适应性
        assert len(new_orders) > 0
        for order in new_orders:
            assert order.price > initial_orders[0].price  # 价格应该更高
            assert order.quantity < initial_orders[0].quantity  # 数量应该更小
    
    async def test_market_impact_adaptation(self, strategy, test_instrument, test_order_book):
        """测试市场冲击适应"""
        # 生成大订单簿
        large_order_book = OrderBook(
            bids=[
                {'price': 49999.0, 'quantity': 10.0},
                {'price': 49998.0, 'quantity': 20.0},
                {'price': 49997.0, 'quantity': 30.0}
            ],
            asks=[
                {'price': 50001.0, 'quantity': 10.0},
                {'price': 50002.0, 'quantity': 20.0},
                {'price': 50003.0, 'quantity': 30.0}
            ],
            timestamp=datetime.now()
        )
        
        # 生成市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']},
            order_book=large_order_book
        )
        
        # 生成订单
        orders = await strategy.generate_orders(market_state)
        
        # 验证订单适应
        for order in orders:
            assert order.quantity <= strategy.max_position_size
            assert order.price >= test_order_book.bids[0]['price']
            assert order.price <= test_order_book.asks[0]['price'] 