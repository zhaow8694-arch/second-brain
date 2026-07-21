import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.strategy_optimizer import StrategyOptimizer
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStrategyOptimizer:
    """策略优化器测试类"""
    
    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        return StrategyOptimizer(
            optimization_window=timedelta(days=30),
            min_trades=100,
            confidence_threshold=0.8,
            max_iterations=100,
            population_size=50,
            mutation_rate=0.1,
            crossover_rate=0.8,
            elitism_size=2
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
    
    async def test_initialization(self, optimizer):
        """测试优化器初始化"""
        assert optimizer.optimization_window == timedelta(days=30)
        assert optimizer.min_trades == 100
        assert optimizer.confidence_threshold == 0.8
        assert optimizer.max_iterations == 100
        assert optimizer.population_size == 50
        assert optimizer.mutation_rate == 0.1
        assert optimizer.crossover_rate == 0.8
        assert optimizer.elitism_size == 2
        assert len(optimizer.optimization_history) == 0
    
    async def test_parameter_space_definition(self, optimizer, strategies):
        """测试参数空间定义"""
        # 定义参数空间
        param_spaces = await optimizer.define_parameter_spaces(strategies)
        
        # 验证参数空间
        for name, space in param_spaces.items():
            assert name in strategies
            assert isinstance(space, dict)
            assert 'bounds' in space
            assert 'types' in space
            assert 'constraints' in space
    
    async def test_optimization_objective(self, optimizer, strategies, historical_data):
        """测试优化目标"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 定义优化目标
        objectives = [
            'sharpe_ratio',
            'max_drawdown',
            'win_rate'
        ]
        
        # 验证目标函数
        for objective in objectives:
            score = await optimizer.calculate_objective(
                strategy,
                historical_data,
                objective
            )
            assert isinstance(score, float)
            assert not np.isnan(score)
            assert not np.isinf(score)
    
    async def test_optimization_process(self, optimizer, strategies, historical_data):
        """测试优化过程"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行优化
        best_params, best_performance = await optimizer.optimize_strategy(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 验证优化结果
        assert best_params is not None
        assert best_performance is not None
        assert 'sharpe_ratio' in best_performance
        assert 'max_drawdown' in best_performance
        assert 'win_rate' in best_performance
    
    async def test_parameter_constraints(self, optimizer, strategies, historical_data):
        """测试参数约束"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 定义参数约束
        constraints = {
            'lookback_period': (10, 50),
            'entry_threshold': (1.5, 3.0),
            'exit_threshold': (0.5, 2.0)
        }
        
        # 运行优化
        best_params, _ = await optimizer.optimize_strategy(
            strategy,
            historical_data,
            strategy_name,
            constraints=constraints
        )
        
        # 验证参数约束
        assert constraints['lookback_period'][0] <= best_params['lookback_period'] <= constraints['lookback_period'][1]
        assert constraints['entry_threshold'][0] <= best_params['entry_threshold'] <= constraints['entry_threshold'][1]
        assert constraints['exit_threshold'][0] <= best_params['exit_threshold'] <= constraints['exit_threshold'][1]
    
    async def test_optimization_history(self, optimizer, strategies, historical_data):
        """测试优化历史记录"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行优化
        await optimizer.optimize_strategy(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 验证历史记录
        assert len(optimizer.optimization_history) > 0
        history = optimizer.optimization_history[strategy_name]
        assert 'parameters' in history
        assert 'performance' in history
        assert 'timestamp' in history
        assert 'iteration' in history
    
    async def test_robustness_analysis(self, optimizer, strategies, historical_data):
        """测试稳健性分析"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行稳健性分析
        robustness_results = await optimizer.analyze_robustness(
            strategy,
            historical_data,
            strategy_name
        )
        
        # 验证分析结果
        assert 'parameter_sensitivity' in robustness_results
        assert 'performance_stability' in robustness_results
        assert 'market_regime_adaptation' in robustness_results
        assert 'outlier_analysis' in robustness_results
    
    async def test_optimization_convergence(self, optimizer, strategies, historical_data):
        """测试优化收敛性"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行优化并记录收敛过程
        convergence_data = await optimizer.optimize_strategy(
            strategy,
            historical_data,
            strategy_name,
            track_convergence=True
        )
        
        # 验证收敛性
        assert 'iteration_history' in convergence_data
        history = convergence_data['iteration_history']
        assert len(history) > 0
        assert 'parameters' in history[0]
        assert 'performance' in history[0]
        
        # 验证性能是否在改善
        performances = [h['performance']['sharpe_ratio'] for h in history]
        assert max(performances) == performances[-1]  # 最佳性能应该在最后一次迭代
    
    async def test_multi_objective_optimization(self, optimizer, strategies, historical_data):
        """测试多目标优化"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 定义多个优化目标
        objectives = [
            'sharpe_ratio',
            'max_drawdown',
            'win_rate'
        ]
        
        # 运行多目标优化
        pareto_front = await optimizer.optimize_strategy(
            strategy,
            historical_data,
            strategy_name,
            objectives=objectives
        )
        
        # 验证帕累托前沿
        assert len(pareto_front) > 0
        for solution in pareto_front:
            assert 'parameters' in solution
            assert 'objectives' in solution
            assert all(obj in solution['objectives'] for obj in objectives)
    
    async def test_optimization_visualization(self, optimizer, strategies, historical_data):
        """测试优化可视化"""
        # 选择策略
        strategy_name = 'statistical_arbitrage'
        strategy = strategies[strategy_name]
        
        # 运行优化
        results = await optimizer.optimize_strategy(
            strategy,
            historical_data,
            strategy_name,
            track_convergence=True
        )
        
        # 生成可视化
        plots = await optimizer.generate_optimization_plots(results)
        
        # 验证可视化结果
        assert 'convergence_curve' in plots
        assert 'parameter_distribution' in plots
        assert 'objective_space' in plots
        assert 'robustness_analysis' in plots
        assert 'sensitivity_analysis' in plots 