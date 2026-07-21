import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import jinja2
import pdfkit
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, config: Dict):
        """初始化报告生成器
        
        Args:
            config: 配置字典，包含报告生成参数
        """
        self.config = config
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        # 创建必要的目录
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir)
        )
        
        # 配置PDF生成器
        self.pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None
        }
        
    async def generate_html_report(
        self,
        data: Dict,
        output_path: str
    ) -> str:
        """生成HTML格式的测试报告
        
        Args:
            data: 包含测试数据的字典
            output_path: 输出文件路径
            
        Returns:
            生成的报告文件路径
        """
        # 生成图表
        charts = await self._generate_charts(data)
        
        # 准备模板数据
        template_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': data['summary'],
            'predictions': data['predictions'],
            'performance': data['performance'],
            'errors': data['errors'],
            'trends': data['trends'],
            'charts': charts
        }
        
        # 渲染HTML模板
        template = self.jinja_env.get_template('report_template.html')
        html_content = template.render(**template_data)
        
        # 保存HTML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return output_path
        
    async def generate_pdf_report(
        self,
        data: Dict,
        output_path: str
    ) -> str:
        """生成PDF格式的测试报告
        
        Args:
            data: 包含测试数据的字典
            output_path: 输出文件路径
            
        Returns:
            生成的报告文件路径
        """
        # 生成HTML内容
        html_path = output_path.replace('.pdf', '.html')
        await self.generate_html_report(data, html_path)
        
        # 转换为PDF
        pdfkit.from_file(html_path, output_path, options=self.pdf_options)
        
        # 删除临时HTML文件
        os.remove(html_path)
        
        return output_path
        
    async def _generate_charts(
        self,
        data: Dict
    ) -> Dict:
        """生成报告所需的图表
        
        Args:
            data: 包含测试数据的字典
            
        Returns:
            包含图表HTML的字典
        """
        charts = {}
        
        # 生成预测结果图表
        charts['predictions'] = await self._generate_prediction_charts(data['predictions'])
        
        # 生成性能图表
        charts['performance'] = await self._generate_performance_charts(data['performance'])
        
        # 生成错误图表
        charts['errors'] = await self._generate_error_charts(data['errors'])
        
        # 生成趋势图表
        charts['trends'] = await self._generate_trend_charts(data['trends'])
        
        return charts
        
    async def _generate_prediction_charts(
        self,
        predictions: Dict
    ) -> str:
        """生成预测结果相关的图表
        
        Args:
            predictions: 预测结果数据
            
        Returns:
            图表HTML
        """
        # 创建混淆矩阵
        fig = go.Figure(data=go.Heatmap(
            z=[[predictions['confusion_matrix'][0][0], predictions['confusion_matrix'][0][1]],
               [predictions['confusion_matrix'][1][0], predictions['confusion_matrix'][1][1]]],
            x=['Negative', 'Positive'],
            y=['Negative', 'Positive'],
            text=[[f"{predictions['confusion_matrix'][0][0]}", f"{predictions['confusion_matrix'][0][1]}"],
                  [f"{predictions['confusion_matrix'][1][0]}", f"{predictions['confusion_matrix'][1][1]}"]],
            texttemplate='%{text}',
            textfont={"size": 16}
        ))
        
        fig.update_layout(
            title='Confusion Matrix',
            xaxis_title='Predicted',
            yaxis_title='Actual'
        )
        
        return fig.to_html(full_html=False)
        
    async def _generate_performance_charts(
        self,
        performance: Dict
    ) -> str:
        """生成性能相关的图表
        
        Args:
            performance: 性能数据
            
        Returns:
            图表HTML
        """
        # 创建性能指标时间序列图
        fig = make_subplots(rows=2, cols=2, subplot_titles=(
            'Execution Time', 'Memory Usage',
            'CPU Usage', 'Network I/O'
        ))
        
        # 添加执行时间
        fig.add_trace(
            go.Scatter(
                y=performance['execution_time'],
                mode='lines',
                name='Execution Time'
            ),
            row=1, col=1
        )
        
        # 添加内存使用
        fig.add_trace(
            go.Scatter(
                y=performance['memory_usage'],
                mode='lines',
                name='Memory Usage'
            ),
            row=1, col=2
        )
        
        # 添加CPU使用
        fig.add_trace(
            go.Scatter(
                y=performance['cpu_usage'],
                mode='lines',
                name='CPU Usage'
            ),
            row=2, col=1
        )
        
        # 添加网络I/O
        fig.add_trace(
            go.Scatter(
                y=performance['network_io'],
                mode='lines',
                name='Network I/O'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=True)
        
        return fig.to_html(full_html=False)
        
    async def _generate_error_charts(
        self,
        errors: Dict
    ) -> str:
        """生成错误相关的图表
        
        Args:
            errors: 错误数据
            
        Returns:
            图表HTML
        """
        # 创建错误分布饼图
        fig = make_subplots(rows=1, cols=2, subplot_titles=(
            'Error Types Distribution',
            'Error Severity Distribution'
        ))
        
        # 添加错误类型分布
        fig.add_trace(
            go.Pie(
                labels=list(errors['error_types'].keys()),
                values=list(errors['error_types'].values()),
                name='Error Types'
            ),
            row=1, col=1
        )
        
        # 添加错误严重程度分布
        fig.add_trace(
            go.Pie(
                labels=list(errors['severity_distribution'].keys()),
                values=list(errors['severity_distribution'].values()),
                name='Error Severity'
            ),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=True)
        
        return fig.to_html(full_html=False)
        
    async def _generate_trend_charts(
        self,
        trends: Dict
    ) -> str:
        """生成趋势相关的图表
        
        Args:
            trends: 趋势数据
            
        Returns:
            图表HTML
        """
        # 创建趋势分析图
        fig = make_subplots(rows=2, cols=1, subplot_titles=(
            'Performance Trends',
            'Error Rate Trend'
        ))
        
        # 添加性能趋势
        for metric, trend in trends['performance_trends'].items():
            fig.add_trace(
                go.Scatter(
                    y=trend['values'],
                    mode='lines',
                    name=metric
                ),
                row=1, col=1
            )
            
        # 添加错误率趋势
        fig.add_trace(
            go.Scatter(
                y=trends['error_trends']['values'],
                mode='lines',
                name='Error Rate'
            ),
            row=2, col=1
        )
        
        fig.update_layout(height=800, showlegend=True)
        
        return fig.to_html(full_html=False)
        
    async def generate_report(
        self,
        data: Dict,
        output_path: str
    ) -> str:
        """生成测试报告
        
        Args:
            data: 包含测试数据的字典
            output_path: 输出文件路径
            
        Returns:
            生成的报告文件路径
        """
        # 验证报告格式
        report_format = os.path.splitext(output_path)[1][1:].lower()
        if report_format not in ['html', 'pdf']:
            raise ValueError(f'不支持的报告格式: {report_format}')
            
        # 创建输出目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 根据格式生成报告
        if report_format == 'html':
            return await self.generate_html_report(data, output_path)
        else:
            return await self.generate_pdf_report(data, output_path) 