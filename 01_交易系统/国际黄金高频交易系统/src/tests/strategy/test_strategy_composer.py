import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.strategy_composer import StrategyComposer
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStrategyComposer:
    """策略组合器测试类"""
    
    @pytest.fixture
    def composer(self):
        """创建策略组合器实例"""
        return StrategyComposer(
            max_total_position=20.0,
            max_drawdown=0.2,
            position_limits={
                'statistical_arbitrage': 0.4,
                'trend_following': 0.3,
                'market_making': 0.3
            }
        )
    
    @pytest.fixture
    def strategies(self):
        """创建测试策略实例"""
        return {
            'statistical_arbitrage': StatisticalArbitrageStrategy(
                lookback_period=20,
                entry_threshold=2.0,
                exit_threshold=1.0,
                max_position_size=10.0,
                min_profit_threshold=0.001
            ),
            'trend_following': TrendFollowingStrategy(
                short_window=10,
                long_window=30,
                entry_threshold=0.02,
                exit_threshold=0.01,
                max_position_size=10.0,
                stop_loss=0.05
            ),
            'market_making': MarketMakingStrategy(
                spread_multiplier=1.5,
                min_spread=0.001,
                max_position_size=10.0,
                inventory_target=0.0,
                inventory_risk_limit=5.0,
                order_refresh_interval=60
            )
        }
    
    @pytest.fixture
    def test_instrument(self):
        """创建测试交易品种"""
        return {
            'symbol': 'GOLD',
            'price': 50000.0,
            'volatility': 0.01
        }
    
    async def test_initialization(self, composer):
        """测试策略组合器初始化"""
        assert composer.max_total_position == 20.0
        assert composer.max_drawdown == 0.2
        assert len(composer.strategies) == 0
        assert composer.position_limits == {
            'statistical_arbitrage': 0.4,
            'trend_following': 0.3,
            'market_making': 0.3
        }
    
    async def test_strategy_registration(self, composer, strategies):
        """测试策略注册"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 验证注册
        assert len(composer.strategies) == 3
        for name in strategies:
            assert name in composer.strategies
            assert composer.strategies[name] == strategies[name]
    
    async def test_position_allocation(self, composer, strategies, test_instrument):
        """测试仓位分配"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 创建市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']}
        )
        
        # 生成信号
        signals = await composer.generate_signals(market_state)
        
        # 验证信号
        assert len(signals) == 3
        for name, signal in signals.items():
            assert signal is not None
            assert 'action' in signal
            assert 'confidence' in signal
            assert 'target_price' in signal
        
        # 分配仓位
        allocations = await composer.allocate_positions(signals)
        
        # 验证分配
        total_allocation = sum(allocations.values())
        assert total_allocation <= composer.max_total_position
        for name, allocation in allocations.items():
            assert allocation <= composer.position_limits[name] * composer.max_total_position
    
    async def test_risk_management(self, composer, strategies, test_instrument):
        """测试风险管理"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 添加大仓位
        position = Position(
            instrument_id='GOLD',
            quantity=25.0,  # 超过最大总仓位限制
            entry_price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 验证仓位限制
        with pytest.raises(ValueError):
            await composer.add_position(position)
        
        # 验证策略仓位限制
        for name, strategy in strategies.items():
            strategy_position = Position(
                instrument_id='GOLD',
                quantity=15.0,  # 超过策略仓位限制
                entry_price=test_instrument['price'],
                timestamp=datetime.now()
            )
            with pytest.raises(ValueError):
                await composer.add_strategy_position(name, strategy_position)
    
    async def test_performance_monitoring(self, composer, strategies, test_instrument):
        """测试性能监控"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 添加交易历史
        for name, strategy in strategies.items():
            trade = {
                'timestamp': datetime.now(),
                'instrument_id': 'GOLD',
                'side': 'BUY',
                'quantity': 1.0,
                'price': test_instrument['price'],
                'profit': 100.0,
                'strategy': name
            }
            strategy.trade_history.append(trade)
        
        # 计算组合性能指标
        metrics = await composer.calculate_performance_metrics()
        
        # 验证指标
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'strategy_metrics' in metrics
        assert len(metrics['strategy_metrics']) == 3
    
    async def test_strategy_coordination(self, composer, strategies, test_instrument):
        """测试策略协调"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 创建市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']}
        )
        
        # 更新市场状态
        await composer.update_market_state(market_state)
        
        # 验证所有策略都收到更新
        for strategy in strategies.values():
            assert strategy.current_market_state == market_state
            assert strategy.last_update_time == market_state.timestamp
    
    async def test_dynamic_weight_adjustment(self, composer, strategies, test_instrument):
        """测试动态权重调整"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 添加不同性能的交易历史
        for name, strategy in strategies.items():
            trades = []
            if name == 'statistical_arbitrage':
                trades = [
                    {'profit': 100.0},
                    {'profit': 150.0},
                    {'profit': 200.0}
                ]
            elif name == 'trend_following':
                trades = [
                    {'profit': 50.0},
                    {'profit': 75.0},
                    {'profit': 100.0}
                ]
            else:  # market_making
                trades = [
                    {'profit': 25.0},
                    {'profit': 50.0},
                    {'profit': 75.0}
                ]
            
            for trade in trades:
                strategy.trade_history.append({
                    'timestamp': datetime.now(),
                    'instrument_id': 'GOLD',
                    'side': 'BUY',
                    'quantity': 1.0,
                    'price': test_instrument['price'],
                    'profit': trade['profit']
                })
        
        # 调整权重
        await composer.adjust_strategy_weights()
        
        # 验证权重调整
        new_weights = composer.position_limits
        assert new_weights['statistical_arbitrage'] > 0.4  # 表现最好的策略权重增加
        assert new_weights['market_making'] < 0.3  # 表现最差的策略权重减少
        assert sum(new_weights.values()) == 1.0  # 权重总和保持为1
    
    async def test_strategy_state_persistence(self, composer, strategies, test_instrument):
        """测试策略状态持久化"""
        # 注册策略
        for name, strategy in strategies.items():
            await composer.register_strategy(name, strategy)
        
        # 添加一些状态
        for name, strategy in strategies.items():
            await strategy.add_position(
                Position(
                    instrument_id='GOLD',
                    quantity=1.0,
                    entry_price=test_instrument['price'],
                    timestamp=datetime.now()
                )
            )
        
        # 保存状态
        state = await composer.save_state()
        
        # 验证状态
        assert 'strategies' in state
        assert 'position_limits' in state
        assert 'max_total_position' in state
        
        # 创建新组合器实例
        new_composer = StrategyComposer(
            max_total_position=20.0,
            max_drawdown=0.2,
            position_limits={
                'statistical_arbitrage': 0.4,
                'trend_following': 0.3,
                'market_making': 0.3
            }
        )
        
        # 注册策略
        for name, strategy in strategies.items():
            await new_composer.register_strategy(name, strategy)
        
        # 加载状态
        await new_composer.load_state(state)
        
        # 验证状态恢复
        for name, strategy in new_composer.strategies.items():
            assert 'GOLD' in strategy.positions
            assert strategy.positions['GOLD'].quantity == 1.0
            assert strategy.positions['GOLD'].entry_price == test_instrument['price'] 