import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.strategy_reporter import StrategyReporter
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.market_making import MarketMakingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStrategyReporter:
    """策略报告生成器测试类"""
    
    @pytest.fixture
    def reporter(self):
        """创建报告生成器实例"""
        return StrategyReporter(
            report_format='html',
            include_charts=True,
            include_tables=True,
            include_summary=True,
            include_details=True,
            include_recommendations=True
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
    def backtest_results(self):
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
                'price': 50000.0 * (1 + np.random.normal(0, 0.001)),
                'profit': np.random.normal(100, 20)
            }
            results['trade_history'].append(trade)
        
        # 生成仓位历史
        for i in range(100):
            position = {
                'timestamp': base_time + timedelta(minutes=i),
                'instrument_id': 'GOLD',
                'size': np.random.uniform(-10, 10),
                'entry_price': 50000.0 * (1 + np.random.normal(0, 0.001))
            }
            results['position_history'].append(position)
        
        return results
    
    async def test_initialization(self, reporter):
        """测试报告生成器初始化"""
        assert reporter.report_format == 'html'
        assert reporter.include_charts is True
        assert reporter.include_tables is True
        assert reporter.include_summary is True
        assert reporter.include_details is True
        assert reporter.include_recommendations is True
        assert len(reporter.report_history) == 0
    
    async def test_summary_report(self, reporter, backtest_results):
        """测试摘要报告生成"""
        # 生成摘要报告
        summary = await reporter.generate_summary_report(backtest_results)
        
        # 验证报告内容
        assert 'performance_summary' in summary
        assert 'risk_summary' in summary
        assert 'trade_summary' in summary
        assert 'position_summary' in summary
        assert 'recommendations' in summary
    
    async def test_detailed_report(self, reporter, backtest_results):
        """测试详细报告生成"""
        # 生成详细报告
        detailed = await reporter.generate_detailed_report(backtest_results)
        
        # 验证报告内容
        assert 'performance_analysis' in detailed
        assert 'risk_analysis' in detailed
        assert 'trade_analysis' in detailed
        assert 'position_analysis' in detailed
        assert 'market_analysis' in detailed
        assert 'strategy_analysis' in detailed
    
    async def test_performance_charts(self, reporter, backtest_results):
        """测试性能图表生成"""
        # 生成性能图表
        charts = await reporter.generate_performance_charts(backtest_results)
        
        # 验证图表
        assert 'equity_curve' in charts
        assert 'drawdown_chart' in charts
        assert 'monthly_returns' in charts
        assert 'trade_distribution' in charts
        assert 'position_history' in charts
    
    async def test_performance_tables(self, reporter, backtest_results):
        """测试性能表格生成"""
        # 生成性能表格
        tables = await reporter.generate_performance_tables(backtest_results)
        
        # 验证表格
        assert 'trade_summary_table' in tables
        assert 'position_summary_table' in tables
        assert 'risk_metrics_table' in tables
        assert 'performance_metrics_table' in tables
        assert 'monthly_returns_table' in tables
    
    async def test_report_formatting(self, reporter, backtest_results):
        """测试报告格式化"""
        # 测试HTML格式
        html_report = await reporter.generate_report(backtest_results, format='html')
        assert isinstance(html_report, str)
        assert '<html>' in html_report
        assert '<body>' in html_report
        
        # 测试PDF格式
        pdf_report = await reporter.generate_report(backtest_results, format='pdf')
        assert isinstance(pdf_report, bytes)
        assert len(pdf_report) > 0
    
    async def test_report_customization(self, reporter, backtest_results):
        """测试报告自定义"""
        # 自定义报告选项
        options = {
            'include_charts': False,
            'include_tables': True,
            'include_summary': True,
            'include_details': False,
            'include_recommendations': True
        }
        
        # 生成自定义报告
        report = await reporter.generate_report(backtest_results, options=options)
        
        # 验证自定义选项
        assert 'charts' not in report
        assert 'tables' in report
        assert 'summary' in report
        assert 'details' not in report
        assert 'recommendations' in report
    
    async def test_report_history(self, reporter, backtest_results):
        """测试报告历史记录"""
        # 生成多个报告
        for i in range(3):
            await reporter.generate_report(backtest_results)
        
        # 验证历史记录
        assert len(reporter.report_history) == 3
        for record in reporter.report_history:
            assert 'timestamp' in record
            assert 'report_content' in record
            assert 'report_format' in record
            assert 'options' in record
    
    async def test_report_export(self, reporter, backtest_results):
        """测试报告导出"""
        # 测试导出为不同格式
        formats = ['html', 'pdf', 'excel']
        for format in formats:
            report = await reporter.export_report(backtest_results, format=format)
            assert report is not None
            if format in ['html', 'pdf']:
                assert isinstance(report, (str, bytes))
            elif format == 'excel':
                assert isinstance(report, bytes)
    
    async def test_report_scheduling(self, reporter, backtest_results):
        """测试报告调度"""
        # 设置报告调度
        schedule = {
            'frequency': 'daily',
            'time': '09:00',
            'format': 'html'
        }
        
        # 添加调度任务
        task_id = await reporter.schedule_report(backtest_results, schedule)
        
        # 验证调度任务
        assert task_id is not None
        assert task_id in reporter.scheduled_tasks
        assert reporter.scheduled_tasks[task_id]['schedule'] == schedule
    
    async def test_report_templates(self, reporter, backtest_results):
        """测试报告模板"""
        # 创建自定义模板
        template = {
            'header': 'Custom Header',
            'footer': 'Custom Footer',
            'style': 'custom_style.css'
        }
        
        # 使用模板生成报告
        report = await reporter.generate_report(backtest_results, template=template)
        
        # 验证模板应用
        assert template['header'] in report
        assert template['footer'] in report
        assert template['style'] in report 