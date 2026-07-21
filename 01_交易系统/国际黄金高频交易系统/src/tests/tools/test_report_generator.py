import pytest
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from src.tests.tools.report_generator import ReportGenerator

@pytest.fixture
def report_generator():
    """创建报告生成器实例"""
    return ReportGenerator(
        config={
            'report': {
                'format': 'html',
                'template': 'default',
                'output_dir': 'test_reports'
            }
        }
    )

@pytest.fixture
def test_data():
    """创建测试数据"""
    # 创建预测结果数据
    predictions = {
        'accuracy': 0.85,
        'precision': 0.82,
        'recall': 0.88,
        'f1_score': 0.85,
        'confusion_matrix': [[80, 10], [5, 85]],
        'total_samples': 180
    }
    
    # 创建性能数据
    performance = {
        'execution_time': {
            'mean': 150.5,
            'std': 25.3,
            'min': 100.0,
            'max': 200.0,
            'p95': 180.0,
            'values': np.random.uniform(100, 200, 100)
        },
        'memory_usage': {
            'mean': 450.2,
            'std': 50.1,
            'min': 350.0,
            'max': 550.0,
            'p95': 500.0,
            'values': np.random.uniform(350, 550, 100)
        },
        'cpu_usage': {
            'mean': 65.3,
            'std': 15.2,
            'min': 40.0,
            'max': 90.0,
            'p95': 85.0,
            'values': np.random.uniform(40, 90, 100)
        },
        'network_io': {
            'mean': 120.5,
            'std': 30.1,
            'min': 80.0,
            'max': 160.0,
            'p95': 150.0,
            'values': np.random.uniform(80, 160, 100)
        }
    }
    
    # 创建错误数据
    errors = {
        'total_errors': 15,
        'error_types': {
            'validation': 5,
            'processing': 7,
            'system': 3
        },
        'severity_distribution': {
            'low': 5,
            'medium': 7,
            'high': 2,
            'critical': 1
        },
        'component_distribution': {
            'trading': 6,
            'data': 4,
            'strategy': 3,
            'model': 2
        }
    }
    
    # 创建趋势数据
    trends = {
        'performance_trends': {
            'execution_time': {
                'slope': -0.5,
                'direction': 'decreasing',
                'values': np.random.uniform(100, 200, 100)
            },
            'memory_usage': {
                'slope': 0.3,
                'direction': 'increasing',
                'values': np.random.uniform(350, 550, 100)
            }
        },
        'error_trends': {
            'slope': -0.2,
            'direction': 'decreasing',
            'values': np.random.randint(0, 5, 100)
        }
    }
    
    # 创建摘要数据
    summary = {
        'overall_status': 'pass',
        'key_metrics': {
            'accuracy': 0.85,
            'execution_time': 150.5,
            'error_rate': 0.083
        },
        'recommendations': [
            '优化内存使用，当前内存使用较高',
            '考虑增加错误重试机制',
            '建议添加更多的单元测试'
        ]
    }
    
    return {
        'predictions': predictions,
        'performance': performance,
        'errors': errors,
        'trends': trends,
        'summary': summary
    }

class TestReportGenerator:
    """测试报告生成器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, report_generator):
        """测试报告生成器初始化"""
        assert isinstance(report_generator.config, dict)
        assert 'report' in report_generator.config
        assert report_generator.template_dir.endswith('templates')
        assert report_generator.assets_dir.endswith('assets')
        
    @pytest.mark.asyncio
    async def test_generate_html_report(self, report_generator, test_data):
        """测试生成HTML报告"""
        # 生成HTML报告
        output_path = os.path.join('test_reports', 'test_report.html')
        report_path = await report_generator.generate_html_report(test_data, output_path)
        
        # 验证报告文件
        assert os.path.exists(report_path)
        assert report_path.endswith('.html')
        
        # 验证报告内容
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '测试报告' in content
            assert '测试摘要' in content
            assert '预测结果' in content
            assert '性能分析' in content
            assert '错误分析' in content
            assert '趋势分析' in content
            assert '改进建议' in content
            
    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, report_generator, test_data):
        """测试生成PDF报告"""
        # 生成PDF报告
        output_path = os.path.join('test_reports', 'test_report.pdf')
        report_path = await report_generator.generate_pdf_report(test_data, output_path)
        
        # 验证报告文件
        assert os.path.exists(report_path)
        assert report_path.endswith('.pdf')
        
    @pytest.mark.asyncio
    async def test_generate_charts(self, report_generator, test_data):
        """测试生成图表"""
        # 生成图表
        charts = await report_generator._generate_charts(test_data)
        
        # 验证图表
        assert isinstance(charts, dict)
        assert 'predictions' in charts
        assert 'performance' in charts
        assert 'errors' in charts
        assert 'trends' in charts
        
        # 验证图表内容
        assert 'Confusion Matrix' in charts['predictions']
        assert 'Execution Time' in charts['performance']
        assert 'Error Types Distribution' in charts['errors']
        assert 'Performance Trends' in charts['trends']
        
    @pytest.mark.asyncio
    async def test_generate_prediction_charts(self, report_generator, test_data):
        """测试生成预测结果图表"""
        # 生成预测结果图表
        chart_html = await report_generator._generate_prediction_charts(test_data['predictions'])
        
        # 验证图表
        assert isinstance(chart_html, str)
        assert 'Confusion Matrix' in chart_html
        assert 'Negative' in chart_html
        assert 'Positive' in chart_html
        
    @pytest.mark.asyncio
    async def test_generate_performance_charts(self, report_generator, test_data):
        """测试生成性能图表"""
        # 生成性能图表
        chart_html = await report_generator._generate_performance_charts(test_data['performance'])
        
        # 验证图表
        assert isinstance(chart_html, str)
        assert 'Execution Time' in chart_html
        assert 'Memory Usage' in chart_html
        assert 'CPU Usage' in chart_html
        assert 'Network I/O' in chart_html
        
    @pytest.mark.asyncio
    async def test_generate_error_charts(self, report_generator, test_data):
        """测试生成错误图表"""
        # 生成错误图表
        chart_html = await report_generator._generate_error_charts(test_data['errors'])
        
        # 验证图表
        assert isinstance(chart_html, str)
        assert 'Error Types Distribution' in chart_html
        assert 'Error Severity Distribution' in chart_html
        
    @pytest.mark.asyncio
    async def test_generate_trend_charts(self, report_generator, test_data):
        """测试生成趋势图表"""
        # 生成趋势图表
        chart_html = await report_generator._generate_trend_charts(test_data['trends'])
        
        # 验证图表
        assert isinstance(chart_html, str)
        assert 'Performance Trends' in chart_html
        assert 'Error Rate Trend' in chart_html
        
    @pytest.mark.asyncio
    async def test_error_handling(self, report_generator):
        """测试错误处理"""
        # 测试无效的报告格式
        with pytest.raises(ValueError):
            await report_generator.generate_report({}, 'test_report.txt')
            
        # 测试无效的输出路径
        with pytest.raises(ValueError):
            await report_generator.generate_report({}, '')
            
    @pytest.mark.asyncio
    async def test_concurrent_report_generation(self, report_generator, test_data):
        """测试并发报告生成"""
        # 并发生成不同类型的报告
        import asyncio
        tasks = [
            report_generator.generate_html_report(test_data, 'test_report1.html'),
            report_generator.generate_pdf_report(test_data, 'test_report2.pdf')
        ]
        
        # 等待所有报告生成完成
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 2
        assert all(os.path.exists(path) for path in results)
        assert results[0].endswith('.html')
        assert results[1].endswith('.pdf') 