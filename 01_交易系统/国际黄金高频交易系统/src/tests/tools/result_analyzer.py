import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import asyncio
import json
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class TestResultAnalyzer:
    """测试结果分析器"""
    
    def __init__(self, config: Dict):
        """初始化测试结果分析器
        
        Args:
            config: 配置字典，包含报告和分析参数
        """
        self.config = config
        
    async def analyze_predictions(
        self,
        predictions: pd.DataFrame
    ) -> Dict:
        """分析预测结果
        
        Args:
            predictions: 包含实际值和预测值的DataFrame
            
        Returns:
            包含各种评估指标的字典
        """
        if predictions.empty:
            raise ValueError('预测数据不能为空')
            
        # 计算评估指标
        metrics = {}
        metrics['accuracy'] = accuracy_score(
            predictions['actual'],
            predictions['predicted']
        )
        metrics['precision'] = precision_score(
            predictions['actual'],
            predictions['predicted']
        )
        metrics['recall'] = recall_score(
            predictions['actual'],
            predictions['predicted']
        )
        metrics['f1_score'] = f1_score(
            predictions['actual'],
            predictions['predicted']
        )
        
        return metrics
        
    async def analyze_performance(
        self,
        performance: pd.DataFrame
    ) -> Dict:
        """分析性能数据
        
        Args:
            performance: 包含性能指标的DataFrame
            
        Returns:
            包含性能统计信息的字典
        """
        if performance.empty:
            raise ValueError('性能数据不能为空')
            
        # 计算统计信息
        stats = {}
        for metric in self.config['performance']['metrics']:
            stats[metric] = {
                'mean': performance[metric].mean(),
                'std': performance[metric].std(),
                'min': performance[metric].min(),
                'max': performance[metric].max(),
                'p95': performance[metric].quantile(0.95)
            }
            
        return stats
        
    async def analyze_errors(
        self,
        errors: pd.DataFrame
    ) -> Dict:
        """分析错误数据
        
        Args:
            errors: 包含错误信息的DataFrame
            
        Returns:
            包含错误分析结果的字典
        """
        if errors.empty:
            return {
                'total_errors': 0,
                'error_types': {},
                'severity_distribution': {},
                'component_distribution': {}
            }
            
        # 计算错误统计信息
        analysis = {
            'total_errors': len(errors),
            'error_types': errors['error_type'].value_counts().to_dict(),
            'severity_distribution': errors['severity'].value_counts().to_dict(),
            'component_distribution': errors['component'].value_counts().to_dict()
        }
        
        return analysis
        
    async def generate_report(
        self,
        results: Dict
    ) -> str:
        """生成测试报告
        
        Args:
            results: 包含测试结果的字典
            
        Returns:
            报告文件路径
        """
        # 验证报告格式
        if self.config['report']['format'] not in ['html', 'pdf', 'json']:
            raise ValueError(f'不支持的报告格式: {self.config["report"]["format"]}')
            
        # 创建报告目录
        os.makedirs(self.config['report']['output_dir'], exist_ok=True)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(
            self.config['report']['output_dir'],
            f'test_report_{timestamp}.{self.config["report"]["format"]}'
        )
        
        # 生成报告内容
        report = {
            'timestamp': timestamp,
            'summary': await self.generate_summary(results),
            'predictions': await self.analyze_predictions(results['predictions']),
            'performance': await self.analyze_performance(results['performance']),
            'errors': await self.analyze_errors(results['errors']),
            'trends': await self.analyze_trends(results)
        }
        
        # 保存报告
        if self.config['report']['format'] == 'json':
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=4)
        else:
            # TODO: 实现HTML和PDF报告生成
            pass
            
        return report_path
        
    async def export_analysis(
        self,
        results: Dict
    ) -> str:
        """导出分析结果
        
        Args:
            results: 包含测试结果的字典
            
        Returns:
            导出文件路径
        """
        # 创建导出目录
        os.makedirs('analysis_exports', exist_ok=True)
        
        # 生成导出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_path = os.path.join(
            'analysis_exports',
            f'analysis_{timestamp}.json'
        )
        
        # 生成导出内容
        export = {
            'timestamp': timestamp,
            'predictions': await self.analyze_predictions(results['predictions']),
            'performance': await self.analyze_performance(results['performance']),
            'errors': await self.analyze_errors(results['errors']),
            'trends': await self.analyze_trends(results)
        }
        
        # 保存导出文件
        with open(export_path, 'w') as f:
            json.dump(export, f, indent=4)
            
        return export_path
        
    async def check_thresholds(
        self,
        results: Dict
    ) -> Dict:
        """检查阈值违规
        
        Args:
            results: 包含测试结果的字典
            
        Returns:
            包含阈值违规信息的字典
        """
        violations = {
            'performance': {},
            'metrics': {}
        }
        
        # 检查性能指标阈值
        performance_stats = await self.analyze_performance(results['performance'])
        for metric, threshold in self.config['performance']['thresholds'].items():
            if performance_stats[metric]['mean'] > threshold:
                violations['performance'][metric] = {
                    'threshold': threshold,
                    'actual': performance_stats[metric]['mean']
                }
                
        # 检查评估指标阈值
        prediction_metrics = await self.analyze_predictions(results['predictions'])
        for metric, threshold in self.config['analysis']['thresholds'].items():
            if prediction_metrics[metric] < threshold:
                violations['metrics'][metric] = {
                    'threshold': threshold,
                    'actual': prediction_metrics[metric]
                }
                
        return violations
        
    async def generate_summary(
        self,
        results: Dict
    ) -> Dict:
        """生成测试摘要
        
        Args:
            results: 包含测试结果的字典
            
        Returns:
            包含测试摘要的字典
        """
        # 分析各项指标
        predictions = await self.analyze_predictions(results['predictions'])
        performance = await self.analyze_performance(results['performance'])
        errors = await self.analyze_errors(results['errors'])
        violations = await self.check_thresholds(results)
        
        # 生成摘要
        summary = {
            'overall_status': 'pass',
            'key_metrics': {
                'accuracy': predictions['accuracy'],
                'execution_time': performance['execution_time']['mean'],
                'error_rate': errors['total_errors'] / len(results['predictions'])
            },
            'recommendations': []
        }
        
        # 检查整体状态
        if violations['performance'] or violations['metrics']:
            summary['overall_status'] = 'fail'
            
        # 生成建议
        if violations['performance']:
            summary['recommendations'].append('性能指标超出阈值，需要优化')
        if violations['metrics']:
            summary['recommendations'].append('评估指标未达到要求，需要改进')
        if errors['total_errors'] > 0:
            summary['recommendations'].append('存在错误，需要修复')
            
        return summary
        
    async def analyze_trends(
        self,
        results: Dict
    ) -> Dict:
        """分析趋势
        
        Args:
            results: 包含测试结果的字典
            
        Returns:
            包含趋势分析结果的字典
        """
        trends = {
            'performance_trends': {},
            'error_trends': {},
            'metric_trends': {}
        }
        
        # 分析性能趋势
        for metric in self.config['performance']['metrics']:
            values = results['performance'][metric].values
            trend = np.polyfit(range(len(values)), values, 1)[0]
            trends['performance_trends'][metric] = {
                'slope': trend,
                'direction': 'increasing' if trend > 0 else 'decreasing'
            }
            
        # 分析错误趋势
        error_counts = results['errors'].groupby('timestamp').size()
        if not error_counts.empty:
            error_trend = np.polyfit(range(len(error_counts)), error_counts.values, 1)[0]
            trends['error_trends'] = {
                'slope': error_trend,
                'direction': 'increasing' if error_trend > 0 else 'decreasing'
            }
            
        # 分析评估指标趋势
        for metric in self.config['analysis']['metrics']:
            values = results['predictions'][metric].values
            trend = np.polyfit(range(len(values)), values, 1)[0]
            trends['metric_trends'][metric] = {
                'slope': trend,
                'direction': 'increasing' if trend > 0 else 'decreasing'
            }
            
        return trends 