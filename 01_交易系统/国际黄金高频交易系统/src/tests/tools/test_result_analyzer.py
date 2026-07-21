import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from src.tests.tools.result_analyzer import TestResultAnalyzer

@pytest.fixture
def result_analyzer():
    """创建测试结果分析器实例"""
    return TestResultAnalyzer(
        config={
            'report': {
                'format': 'html',
                'template': 'default',
                'output_dir': 'test_reports'
            },
            'analysis': {
                'metrics': ['accuracy', 'precision', 'recall', 'f1_score'],
                'thresholds': {
                    'accuracy': 0.8,
                    'precision': 0.7,
                    'recall': 0.7,
                    'f1_score': 0.7
                }
            },
            'performance': {
                'metrics': ['execution_time', 'memory_usage', 'cpu_usage'],
                'thresholds': {
                    'execution_time': 1000,  # ms
                    'memory_usage': 500,     # MB
                    'cpu_usage': 80          # %
                }
            }
        }
    )

@pytest.fixture
def test_results():
    """创建测试结果数据"""
    # 创建预测结果
    predictions = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='1H'),
        'actual': np.random.randint(0, 2, 100),
        'predicted': np.random.randint(0, 2, 100)
    })
    
    # 创建性能数据
    performance = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='1H'),
        'execution_time': np.random.uniform(100, 2000, 100),
        'memory_usage': np.random.uniform(100, 1000, 100),
        'cpu_usage': np.random.uniform(20, 100, 100)
    })
    
    # 创建错误数据
    errors = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=10, freq='1H'),
        'component': np.random.choice(['trading', 'data', 'strategy', 'model'], 10),
        'error_type': np.random.choice(['validation', 'processing', 'system'], 10),
        'message': [f'Test error {i}' for i in range(10)],
        'severity': np.random.choice(['low', 'medium', 'high', 'critical'], 10)
    })
    
    return {
        'predictions': predictions,
        'performance': performance,
        'errors': errors
    }

class TestResultAnalyzer:
    """测试结果分析器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, result_analyzer):
        """测试结果分析器初始化"""
        assert isinstance(result_analyzer.config, dict)
        assert 'report' in result_analyzer.config
        assert 'analysis' in result_analyzer.config
        assert 'performance' in result_analyzer.config
        
    @pytest.mark.asyncio
    async def test_analyze_predictions(self, result_analyzer, test_results):
        """测试预测结果分析"""
        # 分析预测结果
        analysis = await result_analyzer.analyze_predictions(test_results['predictions'])
        
        # 验证分析结果
        assert isinstance(analysis, dict)
        assert all(metric in analysis for metric in ['accuracy', 'precision', 'recall', 'f1_score'])
        assert all(0 <= value <= 1 for value in analysis.values())
        
    @pytest.mark.asyncio
    async def test_analyze_performance(self, result_analyzer, test_results):
        """测试性能分析"""
        # 分析性能数据
        analysis = await result_analyzer.analyze_performance(test_results['performance'])
        
        # 验证分析结果
        assert isinstance(analysis, dict)
        assert all(metric in analysis for metric in ['execution_time', 'memory_usage', 'cpu_usage'])
        assert all('mean' in stats for stats in analysis.values())
        assert all('std' in stats for stats in analysis.values())
        
    @pytest.mark.asyncio
    async def test_analyze_errors(self, result_analyzer, test_results):
        """测试错误分析"""
        # 分析错误数据
        analysis = await result_analyzer.analyze_errors(test_results['errors'])
        
        # 验证分析结果
        assert isinstance(analysis, dict)
        assert 'total_errors' in analysis
        assert 'error_types' in analysis
        assert 'severity_distribution' in analysis
        assert 'component_distribution' in analysis
        
    @pytest.mark.asyncio
    async def test_generate_report(self, result_analyzer, test_results):
        """测试生成报告"""
        # 生成报告
        report_path = await result_analyzer.generate_report(test_results)
        
        # 验证报告
        assert isinstance(report_path, str)
        assert report_path.endswith('.html')
        
    @pytest.mark.asyncio
    async def test_export_analysis(self, result_analyzer, test_results):
        """测试导出分析结果"""
        # 导出分析结果
        export_path = await result_analyzer.export_analysis(test_results)
        
        # 验证导出结果
        assert isinstance(export_path, str)
        assert export_path.endswith('.json')
        
    @pytest.mark.asyncio
    async def test_check_thresholds(self, result_analyzer, test_results):
        """测试阈值检查"""
        # 检查阈值
        violations = await result_analyzer.check_thresholds(test_results)
        
        # 验证结果
        assert isinstance(violations, dict)
        assert 'performance' in violations
        assert 'metrics' in violations
        
    @pytest.mark.asyncio
    async def test_generate_summary(self, result_analyzer, test_results):
        """测试生成摘要"""
        # 生成摘要
        summary = await result_analyzer.generate_summary(test_results)
        
        # 验证摘要
        assert isinstance(summary, dict)
        assert 'overall_status' in summary
        assert 'key_metrics' in summary
        assert 'recommendations' in summary
        
    @pytest.mark.asyncio
    async def test_analyze_trends(self, result_analyzer, test_results):
        """测试趋势分析"""
        # 分析趋势
        trends = await result_analyzer.analyze_trends(test_results)
        
        # 验证趋势
        assert isinstance(trends, dict)
        assert 'performance_trends' in trends
        assert 'error_trends' in trends
        assert 'metric_trends' in trends
        
    @pytest.mark.asyncio
    async def test_error_handling(self, result_analyzer):
        """测试错误处理"""
        # 测试无效的预测数据
        with pytest.raises(ValueError):
            await result_analyzer.analyze_predictions(pd.DataFrame())
            
        # 测试无效的性能数据
        with pytest.raises(ValueError):
            await result_analyzer.analyze_performance(pd.DataFrame())
            
        # 测试无效的报告格式
        result_analyzer.config['report']['format'] = 'invalid'
        with pytest.raises(ValueError):
            await result_analyzer.generate_report({})
            
    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, result_analyzer, test_results):
        """测试并发分析"""
        # 并发生成不同类型的分析
        import asyncio
        tasks = [
            result_analyzer.analyze_predictions(test_results['predictions']),
            result_analyzer.analyze_performance(test_results['performance']),
            result_analyzer.analyze_errors(test_results['errors'])
        ]
        
        # 等待所有分析完成
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results) 