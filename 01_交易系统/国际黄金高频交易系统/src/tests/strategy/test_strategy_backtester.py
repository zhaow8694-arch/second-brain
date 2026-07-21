import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.strategy_backtester import StrategyBacktester
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStrategyBacktester:
    """策略回测器测试类"""
    
    @pytest.fixture
    def backtester(self):
        """创建回测器实例"""
        return StrategyBacktester(
            initial_capital=1000000.0,
            commission_rate=0.0003,
            slippage=0.0001,
            min_trade_volume=0.01,
            max_trade_volume=100.0
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
    def historical_data(self, test_instrument):
        """创建历史数据"""
        data = []
        base_price = test_instrument['price']
        base_time = datetime.now()
        
        for i in range(1000):
            timestamp = base_time + timedelta(minutes=i)
            price = base_price * (1 + np.random.normal(0, 0.001))
            volume = 1000.0 * (1 + np.random.normal(0, 0.1))
            volatility = test_instrument['volatility'] * (1 + np.random.normal(0, 0.1))
            
            data.append({
                'timestamp': timestamp,
                'price': price,
                'volume': volume,
                'volatility': volatility,
                'bid_price': price * 0.999,
                'ask_price': price * 1.001,
                'bid_volume': volume * 0.5,
                'ask_volume': volume * 0.5
            })
        
        return data
    
    async def test_initialization(self, backtester):
        """测试回测器初始化"""
        assert backtester.initial_capital == 1000000.0
        assert backtester.commission_rate == 0.0003
        assert backtester.slippage == 0.0001
        assert backtester.min_trade_volume == 0.01
        assert backtester.max_trade_volume == 100.0
        assert len(backtester.trade_history) == 0
        assert len(backtester.positions) == 0
    
    async def test_data_preprocessing(self, backtester, historical_data):
        """测试数据预处理"""
        # 预处理数据
        processed_data = await backtester.preprocess_data(historical_data)
        
        # 验证数据格式
        assert len(processed_data) == len(historical_data)
        for data_point in processed_data:
            assert 'timestamp' in data_point
            assert 'price' in data_point
            assert 'volume' in data_point
            assert 'volatility' in data_point
            assert 'bid_price' in data_point
            assert 'ask_price' in data_point
            assert 'bid_volume' in data_point
            assert 'ask_volume' in data_point
    
    async def test_single_strategy_backtest(self, backtester, strategies, historical_data):
        """测试单策略回测"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行回测
        results = await backtester.run_backtest(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 验证回测结果
        assert 'equity_curve' in results
        assert 'trade_history' in results
        assert 'performance_metrics' in results
        assert 'position_history' in results
        
        # 验证性能指标
        metrics = results['performance_metrics']
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
    
    async def test_multi_strategy_backtest(self, backtester, strategies, historical_data):
        """测试多策略回测"""
        # 运行多策略回测
        results = await backtester.run_multi_strategy_backtest(
            strategies,
            historical_data
        )
        
        # 验证回测结果
        assert len(results) == len(strategies)
        for strategy_name, strategy_results in results.items():
            assert 'equity_curve' in strategy_results
            assert 'trade_history' in strategy_results
            assert 'performance_metrics' in strategy_results
            assert 'position_history' in strategy_results
    
    async def test_risk_management(self, backtester, strategies, historical_data):
        """测试风险管理"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 设置风险参数
        risk_params = {
            'max_position_size': 10.0,
            'max_drawdown': 0.2,
            'stop_loss': 0.05,
            'take_profit': 0.1
        }
        
        # 运行回测
        results = await backtester.run_backtest(
            strategy,
            historical_data,
            strategy_name,
            risk_params=risk_params
        )
        
        # 验证风险控制
        position_history = results['position_history']
        for position in position_history:
            assert position['size'] <= risk_params['max_position_size']
        
        # 验证回撤控制
        equity_curve = results['equity_curve']
        max_drawdown = max(
            (equity_curve[i] - equity_curve[i+1]) / equity_curve[i]
            for i in range(len(equity_curve)-1)
        )
        assert max_drawdown <= risk_params['max_drawdown']
    
    async def test_transaction_costs(self, backtester, strategies, historical_data):
        """测试交易成本"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行回测
        results = await backtester.run_backtest(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 验证交易成本
        trade_history = results['trade_history']
        total_commission = sum(
            trade['price'] * trade['quantity'] * backtester.commission_rate
            for trade in trade_history
        )
        total_slippage = sum(
            trade['price'] * trade['quantity'] * backtester.slippage
            for trade in trade_history
        )
        
        # 验证成本已计入权益曲线
        equity_curve = results['equity_curve']
        assert equity_curve[-1] <= backtester.initial_capital - total_commission - total_slippage
    
    async def test_performance_analysis(self, backtester, strategies, historical_data):
        """测试性能分析"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行回测
        results = await backtester.run_backtest(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 计算性能指标
        metrics = await backtester.calculate_performance_metrics(results)
        
        # 验证性能指标
        assert 'total_return' in metrics
        assert 'annual_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'sortino_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'avg_trade_profit' in metrics
        assert 'avg_holding_period' in metrics
    
    async def test_market_impact(self, backtester, strategies, historical_data):
        """测试市场冲击"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行回测
        results = await backtester.run_backtest(
            strategy,
            historical_data,
            strategy_name,
            include_market_impact=True
        )
        
        # 验证市场冲击
        trade_history = results['trade_history']
        for trade in trade_history:
            # 验证大额交易的价格影响
            if trade['quantity'] > backtester.max_trade_volume * 0.5:
                assert trade['execution_price'] > trade['price']  # 买入价格高于市场价格
                assert trade['execution_price'] < trade['price'] * (1 + 0.01)  # 价格影响不超过1%
    
    async def test_backtest_visualization(self, backtester, strategies, historical_data):
        """测试回测可视化"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行回测
        results = await backtester.run_backtest(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 生成可视化
        plots = await backtester.generate_plots(results)
        
        # 验证图表
        assert 'equity_curve' in plots
        assert 'drawdown' in plots
        assert 'trade_distribution' in plots
        assert 'monthly_returns' in plots
        assert 'position_history' in plots 