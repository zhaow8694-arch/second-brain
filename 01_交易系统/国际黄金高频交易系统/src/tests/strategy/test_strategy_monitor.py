import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.strategy_monitor import StrategyMonitor
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStrategyMonitor:
    """策略监控器测试类"""
    
    @pytest.fixture
    def monitor(self):
        """创建监控器实例"""
        return StrategyMonitor(
            update_interval=timedelta(minutes=1),
            risk_thresholds={
                'max_drawdown': 0.2,
                'max_position_size': 10.0,
                'max_daily_loss': 0.1
            },
            performance_thresholds={
                'min_sharpe_ratio': 1.0,
                'min_win_rate': 0.5,
                'min_profit_factor': 1.5
            },
            alert_levels={
                'warning': 0.8,
                'critical': 0.9
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
    
    @pytest.fixture
    def market_state(self, test_instrument):
        """创建市场状态"""
        return MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']}
        )
    
    async def test_initialization(self, monitor):
        """测试监控器初始化"""
        assert monitor.update_interval == timedelta(minutes=1)
        assert 'max_drawdown' in monitor.risk_thresholds
        assert 'max_position_size' in monitor.risk_thresholds
        assert 'max_daily_loss' in monitor.risk_thresholds
        assert 'min_sharpe_ratio' in monitor.performance_thresholds
        assert 'min_win_rate' in monitor.performance_thresholds
        assert 'min_profit_factor' in monitor.performance_thresholds
        assert 'warning' in monitor.alert_levels
        assert 'critical' in monitor.alert_levels
        assert len(monitor.monitoring_history) == 0
    
    async def test_strategy_registration(self, monitor, strategies):
        """测试策略注册"""
        # 注册策略
        for name, strategy in strategies.items():
            await monitor.register_strategy(name, strategy)
        
        # 验证注册
        assert len(monitor.registered_strategies) == len(strategies)
        for name in strategies:
            assert name in monitor.registered_strategies
    
    async def test_real_time_monitoring(self, monitor, strategies, market_state):
        """测试实时监控"""
        # 注册策略
        for name, strategy in strategies.items():
            await monitor.register_strategy(name, strategy)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 验证监控状态
        assert monitor.current_market_state == market_state
        assert monitor.last_update_time is not None
    
    async def test_risk_monitoring(self, monitor, strategies, market_state):
        """测试风险监控"""
        # 注册策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        await monitor.register_strategy(strategy_name, strategy)
        
        # 添加测试仓位
        position = Position(
            instrument_id='GOLD',
            quantity=15.0,  # 超过最大仓位限制
            entry_price=50000.0,
            timestamp=datetime.now()
        )
        await strategy.add_position(position)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 检查风险警报
        alerts = await monitor.check_risk_alerts()
        assert len(alerts) > 0
        assert any(alert['type'] == 'position_size' for alert in alerts)
    
    async def test_performance_monitoring(self, monitor, strategies, market_state):
        """测试性能监控"""
        # 注册策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        await monitor.register_strategy(strategy_name, strategy)
        
        # 添加测试交易历史
        trades = [
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'instrument_id': 'GOLD',
                'side': 'BUY',
                'quantity': 1.0,
                'price': 50000.0,
                'profit': 100.0
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'instrument_id': 'GOLD',
                'side': 'SELL',
                'quantity': 1.0,
                'price': 50000.0,
                'profit': -200.0
            }
        ]
        strategy.trade_history.extend(trades)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 检查性能警报
        alerts = await monitor.check_performance_alerts()
        assert len(alerts) > 0
        assert any(alert['type'] == 'daily_loss' for alert in alerts)
    
    async def test_alert_system(self, monitor, strategies, market_state):
        """测试警报系统"""
        # 注册策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        await monitor.register_strategy(strategy_name, strategy)
        
        # 添加测试仓位
        position = Position(
            instrument_id='GOLD',
            quantity=15.0,
            entry_price=50000.0,
            timestamp=datetime.now()
        )
        await strategy.add_position(position)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 生成警报
        alerts = await monitor.generate_alerts()
        
        # 验证警报
        assert len(alerts) > 0
        for alert in alerts:
            assert 'type' in alert
            assert 'level' in alert
            assert 'message' in alert
            assert 'timestamp' in alert
            assert alert['level'] in ['warning', 'critical']
    
    async def test_monitoring_history(self, monitor, strategies, market_state):
        """测试监控历史记录"""
        # 注册策略
        for name, strategy in strategies.items():
            await monitor.register_strategy(name, strategy)
        
        # 进行多次监控
        for i in range(3):
            await monitor.update_market_state(market_state)
            await monitor.generate_alerts()
        
        # 验证历史记录
        assert len(monitor.monitoring_history) == 3
        for record in monitor.monitoring_history:
            assert 'timestamp' in record
            assert 'market_state' in record
            assert 'alerts' in record
            assert 'metrics' in record
    
    async def test_strategy_health_check(self, monitor, strategies, market_state):
        """测试策略健康检查"""
        # 注册策略
        for name, strategy in strategies.items():
            await monitor.register_strategy(name, strategy)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 进行健康检查
        health_status = await monitor.check_strategy_health()
        
        # 验证健康状态
        assert len(health_status) == len(strategies)
        for name, status in health_status.items():
            assert 'is_healthy' in status
            assert 'issues' in status
            assert 'last_update' in status
            assert 'performance_score' in status
    
    async def test_monitoring_dashboard(self, monitor, strategies, market_state):
        """测试监控仪表板"""
        # 注册策略
        for name, strategy in strategies.items():
            await monitor.register_strategy(name, strategy)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 生成仪表板
        dashboard = await monitor.generate_dashboard()
        
        # 验证仪表板内容
        assert 'market_overview' in dashboard
        assert 'strategy_status' in dashboard
        assert 'risk_metrics' in dashboard
        assert 'performance_metrics' in dashboard
        assert 'active_alerts' in dashboard
        assert 'charts' in dashboard
    
    async def test_monitoring_report(self, monitor, strategies, market_state):
        """测试监控报告生成"""
        # 注册策略
        for name, strategy in strategies.items():
            await monitor.register_strategy(name, strategy)
        
        # 更新市场状态
        await monitor.update_market_state(market_state)
        
        # 生成监控报告
        report = await monitor.generate_monitoring_report()
        
        # 验证报告内容
        assert 'summary' in report
        assert 'market_analysis' in report
        assert 'strategy_analysis' in report
        assert 'risk_analysis' in report
        assert 'performance_analysis' in report
        assert 'recommendations' in report
        assert 'charts' in report 