import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.base_strategy import BaseStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestBaseStrategy:
    """策略基类测试类"""
    
    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        return BaseStrategy(
            max_position_size=10.0,
            stop_loss=0.05,
            take_profit=0.1,
            max_drawdown=0.2
        )
    
    @pytest.fixture
    def test_instrument(self):
        """创建测试交易品种"""
        return {
            'symbol': 'GOLD',
            'price': 50000.0,
            'volatility': 0.01
        }
    
    async def test_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.max_position_size == 10.0
        assert strategy.stop_loss == 0.05
        assert strategy.take_profit == 0.1
        assert strategy.max_drawdown == 0.2
        assert strategy.positions == {}
        assert strategy.trade_history == []
        assert strategy.active_orders == {}
        assert strategy.performance_metrics == {}
    
    async def test_position_management(self, strategy, test_instrument):
        """测试仓位管理"""
        # 创建初始仓位
        position = Position(
            instrument_id='GOLD',
            quantity=1.0,
            entry_price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 添加仓位
        await strategy.add_position(position)
        
        # 验证仓位
        assert 'GOLD' in strategy.positions
        assert strategy.positions['GOLD'].quantity == 1.0
        
        # 更新仓位
        await strategy.update_position(
            'GOLD',
            quantity=2.0,
            price=test_instrument['price'] * 1.01
        )
        
        # 验证更新
        assert strategy.positions['GOLD'].quantity == 2.0
        assert strategy.positions['GOLD'].entry_price == test_instrument['price'] * 1.01
        
        # 移除仓位
        await strategy.remove_position('GOLD')
        
        # 验证移除
        assert 'GOLD' not in strategy.positions
    
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
        
        # 验证止损
        await strategy.add_position(
            Position(
                instrument_id='GOLD',
                quantity=1.0,
                entry_price=test_instrument['price'],
                timestamp=datetime.now()
            )
        )
        
        # 模拟大幅亏损
        await strategy.update_position(
            'GOLD',
            quantity=1.0,
            price=test_instrument['price'] * 0.94  # 6%亏损
        )
        
        # 验证止损触发
        assert await strategy.check_stop_loss('GOLD')
        
        # 模拟大幅盈利
        await strategy.update_position(
            'GOLD',
            quantity=1.0,
            price=test_instrument['price'] * 1.11  # 11%盈利
        )
        
        # 验证止盈触发
        assert await strategy.check_take_profit('GOLD')
    
    async def test_drawdown_management(self, strategy, test_instrument):
        """测试回撤管理"""
        # 添加交易历史
        trades = [
            {
                'timestamp': datetime.now() - timedelta(hours=3),
                'instrument_id': 'GOLD',
                'side': 'BUY',
                'quantity': 1.0,
                'price': test_instrument['price'],
                'profit': 100.0
            },
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'instrument_id': 'GOLD',
                'side': 'SELL',
                'quantity': 1.0,
                'price': test_instrument['price'] * 1.05,
                'profit': 50.0
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'instrument_id': 'GOLD',
                'side': 'BUY',
                'quantity': 1.0,
                'price': test_instrument['price'] * 1.1,
                'profit': -200.0
            }
        ]
        strategy.trade_history.extend(trades)
        
        # 计算回撤
        drawdown = await strategy.calculate_drawdown()
        
        # 验证回撤
        assert drawdown > 0
        assert drawdown <= strategy.max_drawdown
    
    async def test_performance_metrics(self, strategy, test_instrument):
        """测试性能指标"""
        # 添加交易历史
        trades = [
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'instrument_id': 'GOLD',
                'side': 'BUY',
                'quantity': 1.0,
                'price': test_instrument['price'],
                'profit': 100.0
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'instrument_id': 'GOLD',
                'side': 'SELL',
                'quantity': 1.0,
                'price': test_instrument['price'] * 1.05,
                'profit': 50.0
            }
        ]
        strategy.trade_history.extend(trades)
        
        # 计算性能指标
        metrics = await strategy.calculate_performance_metrics()
        
        # 验证指标
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert metrics['total_trades'] == 2
        assert 0 <= metrics['win_rate'] <= 1
        assert metrics['profit_factor'] > 1  # 盈利因子应该大于1
    
    async def test_order_management(self, strategy, test_instrument):
        """测试订单管理"""
        # 创建订单
        order = Order(
            instrument_id='GOLD',
            order_type='LIMIT',
            side='BUY',
            quantity=1.0,
            price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 添加订单
        await strategy.add_order(order)
        
        # 验证订单
        assert order.order_id in strategy.active_orders
        assert strategy.active_orders[order.order_id] == order
        
        # 更新订单
        await strategy.update_order(
            order.order_id,
            quantity=2.0,
            price=test_instrument['price'] * 1.01
        )
        
        # 验证更新
        updated_order = strategy.active_orders[order.order_id]
        assert updated_order.quantity == 2.0
        assert updated_order.price == test_instrument['price'] * 1.01
        
        # 取消订单
        await strategy.cancel_order(order.order_id)
        
        # 验证取消
        assert order.order_id not in strategy.active_orders
    
    async def test_market_state_handling(self, strategy, test_instrument):
        """测试市场状态处理"""
        # 创建市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']}
        )
        
        # 更新市场状态
        await strategy.update_market_state(market_state)
        
        # 验证状态更新
        assert strategy.current_market_state == market_state
        assert strategy.last_update_time == market_state.timestamp
    
    async def test_strategy_state_persistence(self, strategy, test_instrument):
        """测试策略状态持久化"""
        # 添加一些状态
        await strategy.add_position(
            Position(
                instrument_id='GOLD',
                quantity=1.0,
                entry_price=test_instrument['price'],
                timestamp=datetime.now()
            )
        )
        
        # 保存状态
        state = await strategy.save_state()
        
        # 验证状态
        assert 'positions' in state
        assert 'trade_history' in state
        assert 'active_orders' in state
        assert 'performance_metrics' in state
        
        # 创建新策略实例
        new_strategy = BaseStrategy(
            max_position_size=10.0,
            stop_loss=0.05,
            take_profit=0.1,
            max_drawdown=0.2
        )
        
        # 加载状态
        await new_strategy.load_state(state)
        
        # 验证状态恢复
        assert 'GOLD' in new_strategy.positions
        assert new_strategy.positions['GOLD'].quantity == 1.0
        assert new_strategy.positions['GOLD'].entry_price == test_instrument['price'] 