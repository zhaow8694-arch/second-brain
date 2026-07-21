import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.strategy_evaluator import StrategyEvaluator
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStrategyEvaluator:
    """策略评估器测试类"""
    
    @pytest.fixture
    def evaluator(self):
        """创建评估器实例"""
        return StrategyEvaluator(
            evaluation_window=timedelta(days=30),
            min_trades=100,
            confidence_threshold=0.8,
            risk_free_rate=0.02,
            benchmark_return=0.1
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
    def backtest_results(self, test_instrument):
        """创建回测结果数据"""
        base_time = datetime.now()
        results = {
            'equity_curve': [],
            'trade_history': [],
            'position_history': [],
            'performance_metrics': {
                'total_return': 0.15,
                'annual_return': 0.18,
                'sharpe_ratio': 1.5,
                'sortino_ratio': 1.8,
                'max_drawdown': 0.1,
                'win_rate': 0.6,
                'profit_factor': 1.8,
                'avg_trade_profit': 100.0,
                'avg_holding_period': timedelta(hours=2)
            }
        }
        
        # 生成权益曲线
        for i in range(100):
            timestamp = base_time + timedelta(minutes=i)
            equity = 1000000.0 * (1 + 0.001 * i)
            results['equity_curve'].append({
                'timestamp': timestamp,
                'equity': equity
            })
        
        # 生成交易历史
        for i in range(50):
            trade = {
                'timestamp': base_time + timedelta(minutes=i*2),
                'instrument_id': 'GOLD',
                'side': 'BUY' if i % 2 == 0 else 'SELL',
                'quantity': 1.0,
                'price': test_instrument['price'] * (1 + np.random.normal(0, 0.001)),
                'profit': np.random.normal(100, 20)
            }
            results['trade_history'].append(trade)
        
        # 生成仓位历史
        for i in range(100):
            position = {
                'timestamp': base_time + timedelta(minutes=i),
                'instrument_id': 'GOLD',
                'size': np.random.uniform(-10, 10),
                'entry_price': test_instrument['price'] * (1 + np.random.normal(0, 0.001))
            }
            results['position_history'].append(position)
        
        return results
    
    async def test_initialization(self, evaluator):
        """测试评估器初始化"""
        assert evaluator.evaluation_window == timedelta(days=30)
        assert evaluator.min_trades == 100
        assert evaluator.confidence_threshold == 0.8
        assert evaluator.risk_free_rate == 0.02
        assert evaluator.benchmark_return == 0.1
        assert len(evaluator.evaluation_history) == 0
    
    async def test_performance_evaluation(self, evaluator, backtest_results):
        """测试性能评估"""
        # 评估性能
        performance = await evaluator.evaluate_performance(backtest_results)
        
        # 验证性能指标
        assert 'total_return' in performance
        assert 'annual_return' in performance
        assert 'sharpe_ratio' in performance
        assert 'sortino_ratio' in performance
        assert 'information_ratio' in performance
        assert 'alpha' in performance
        assert 'beta' in performance
        assert 'tracking_error' in performance
    
    async def test_risk_evaluation(self, evaluator, backtest_results):
        """测试风险评估"""
        # 评估风险
        risk = await evaluator.evaluate_risk(backtest_results)
        
        # 验证风险指标
        assert 'max_drawdown' in risk
        assert 'var_95' in risk
        assert 'cvar_95' in risk
        assert 'volatility' in risk
        assert 'downside_deviation' in risk
        assert 'calmar_ratio' in risk
        assert 'sortino_ratio' in risk
    
    async def test_stability_evaluation(self, evaluator, backtest_results):
        """测试稳定性评估"""
        # 评估稳定性
        stability = await evaluator.evaluate_stability(backtest_results)
        
        # 验证稳定性指标
        assert 'trade_consistency' in stability
        assert 'win_rate_stability' in stability
        assert 'profit_stability' in stability
        assert 'position_stability' in stability
        assert 'drawdown_stability' in stability
        assert 'recovery_time' in stability
    
    async def test_efficiency_evaluation(self, evaluator, backtest_results):
        """测试效率评估"""
        # 评估效率
        efficiency = await evaluator.evaluate_efficiency(backtest_results)
        
        # 验证效率指标
        assert 'profit_factor' in efficiency
        assert 'avg_trade_profit' in efficiency
        assert 'avg_holding_period' in efficiency
        assert 'trades_per_day' in efficiency
        assert 'capital_turnover' in efficiency
        assert 'cost_efficiency' in efficiency
    
    async def test_market_regime_adaptation(self, evaluator, backtest_results):
        """测试市场状态适应能力"""
        # 评估市场状态适应能力
        adaptation = await evaluator.evaluate_market_regime_adaptation(backtest_results)
        
        # 验证适应能力指标
        assert 'regime_detection' in adaptation
        assert 'regime_performance' in adaptation
        assert 'regime_transition' in adaptation
        assert 'regime_stability' in adaptation
        assert 'regime_risk' in adaptation
    
    async def test_comprehensive_evaluation(self, evaluator, backtest_results):
        """测试综合评估"""
        # 进行综合评估
        evaluation = await evaluator.evaluate_strategy(backtest_results)
        
        # 验证评估结果
        assert 'performance' in evaluation
        assert 'risk' in evaluation
        assert 'stability' in evaluation
        assert 'efficiency' in evaluation
        assert 'adaptation' in evaluation
        assert 'overall_score' in evaluation
        assert 'recommendations' in evaluation
    
    async def test_evaluation_history(self, evaluator, backtest_results):
        """测试评估历史记录"""
        # 进行多次评估
        for i in range(3):
            await evaluator.evaluate_strategy(backtest_results)
        
        # 验证历史记录
        assert len(evaluator.evaluation_history) == 3
        for record in evaluator.evaluation_history:
            assert 'timestamp' in record
            assert 'evaluation_results' in record
            assert 'overall_score' in record
            assert 'recommendations' in record
    
    async def test_evaluation_visualization(self, evaluator, backtest_results):
        """测试评估可视化"""
        # 生成评估可视化
        plots = await evaluator.generate_evaluation_plots(backtest_results)
        
        # 验证可视化结果
        assert 'performance_metrics' in plots
        assert 'risk_metrics' in plots
        assert 'stability_metrics' in plots
        assert 'efficiency_metrics' in plots
        assert 'adaptation_metrics' in plots
        assert 'trend_analysis' in plots
        assert 'correlation_analysis' in plots
    
    async def test_evaluation_report(self, evaluator, backtest_results):
        """测试评估报告生成"""
        # 生成评估报告
        report = await evaluator.generate_evaluation_report(backtest_results)
        
        # 验证报告内容
        assert 'summary' in report
        assert 'performance_analysis' in report
        assert 'risk_analysis' in report
        assert 'stability_analysis' in report
        assert 'efficiency_analysis' in report
        assert 'adaptation_analysis' in report
        assert 'recommendations' in report
        assert 'charts' in report 