from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from loguru import logger

from .metrics_collector import SystemMetrics, DataMetrics, CacheMetrics
from .metrics_storage import MetricsStorage

class MetricsDashboard:
    """性能监控仪表板"""
    
    def __init__(self, storage: MetricsStorage):
        """初始化性能监控仪表板
        
        Args:
            storage: 性能指标存储管理器
        """
        self.logger = logger.bind(context="metrics_dashboard")
        self.storage = storage
        
    def create_system_metrics_dashboard(self, time_range: Optional[timedelta] = None) -> go.Figure:
        """创建系统性能指标仪表板
        
        Args:
            time_range: 时间范围，默认为None（显示所有数据）
            
        Returns:
            go.Figure: Plotly图表对象
        """
        try:
            # 获取系统性能指标数据
            metrics = self.storage.get_system_metrics(time_range)
            if not metrics:
                self.logger.warning("没有可用的系统性能指标数据")
                return None
                
            # 创建数据框
            df = pd.DataFrame([vars(m) for m in metrics])
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('CPU和内存使用率', '磁盘IO', '网络IO', '系统资源使用趋势')
            )
            
            # CPU和内存使用率
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['cpu_percent'],
                    name='CPU使用率',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['memory_percent'],
                    name='内存使用率',
                    line=dict(color='red')
                ),
                row=1, col=1
            )
            
            # 磁盘IO
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['disk_io_read'],
                    name='磁盘读取',
                    line=dict(color='green')
                ),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['disk_io_write'],
                    name='磁盘写入',
                    line=dict(color='orange')
                ),
                row=1, col=2
            )
            
            # 网络IO
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['network_io_sent'],
                    name='网络发送',
                    line=dict(color='purple')
                ),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['network_io_recv'],
                    name='网络接收',
                    line=dict(color='brown')
                ),
                row=2, col=1
            )
            
            # 系统资源使用趋势
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['cpu_percent'],
                    name='CPU趋势',
                    line=dict(color='blue')
                ),
                row=2, col=2
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['memory_percent'],
                    name='内存趋势',
                    line=dict(color='red')
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text="系统性能指标监控",
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"创建系统性能指标仪表板时发生错误: {str(e)}")
            raise
            
    def create_data_metrics_dashboard(self, data_type: Optional[str] = None,
                                    time_range: Optional[timedelta] = None) -> go.Figure:
        """创建数据处理性能指标仪表板
        
        Args:
            data_type: 数据类型过滤
            time_range: 时间范围，默认为None（显示所有数据）
            
        Returns:
            go.Figure: Plotly图表对象
        """
        try:
            # 获取数据处理性能指标数据
            metrics = self.storage.get_data_metrics(data_type, time_range)
            if not metrics:
                self.logger.warning("没有可用的数据处理性能指标数据")
                return None
                
            # 创建数据框
            df = pd.DataFrame([vars(m) for m in metrics])
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('处理记录数', '处理时间', '错误率', '平均记录大小')
            )
            
            # 处理记录数
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['records_processed'],
                    name='处理记录数',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # 处理时间
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['processing_time'],
                    name='处理时间',
                    line=dict(color='red')
                ),
                row=1, col=2
            )
            
            # 错误率
            df['error_rate'] = df['error_count'] / df['records_processed']
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['error_rate'],
                    name='错误率',
                    line=dict(color='orange')
                ),
                row=2, col=1
            )
            
            # 平均记录大小
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['avg_record_size'],
                    name='平均记录大小',
                    line=dict(color='green')
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text="数据处理性能指标监控",
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"创建数据处理性能指标仪表板时发生错误: {str(e)}")
            raise
            
    def create_cache_metrics_dashboard(self, time_range: Optional[timedelta] = None) -> go.Figure:
        """创建缓存性能指标仪表板
        
        Args:
            time_range: 时间范围，默认为None（显示所有数据）
            
        Returns:
            go.Figure: Plotly图表对象
        """
        try:
            # 获取缓存性能指标数据
            metrics = self.storage.get_cache_metrics(time_range)
            if not metrics:
                self.logger.warning("没有可用的缓存性能指标数据")
                return None
                
            # 创建数据框
            df = pd.DataFrame([vars(m) for m in metrics])
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('缓存命中率', '缓存大小', '内存使用量', '请求统计')
            )
            
            # 缓存命中率
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['hit_rate'],
                    name='命中率',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # 缓存大小
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['cache_size'],
                    name='缓存大小',
                    line=dict(color='red')
                ),
                row=1, col=2
            )
            
            # 内存使用量
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['memory_usage'],
                    name='内存使用量',
                    line=dict(color='green')
                ),
                row=2, col=1
            )
            
            # 请求统计
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['hit_count'],
                    name='命中次数',
                    line=dict(color='blue')
                ),
                row=2, col=2
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['miss_count'],
                    name='未命中次数',
                    line=dict(color='red')
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text="缓存性能指标监控",
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"创建缓存性能指标仪表板时发生错误: {str(e)}")
            raise
            
    def export_dashboard(self, output_dir: str):
        """导出所有仪表板为HTML文件
        
        Args:
            output_dir: 输出目录
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            # 导出系统性能指标仪表板
            system_fig = self.create_system_metrics_dashboard()
            if system_fig:
                system_fig.write_html(os.path.join(output_dir, 'system_metrics.html'))
                
            # 导出数据处理性能指标仪表板
            data_fig = self.create_data_metrics_dashboard()
            if data_fig:
                data_fig.write_html(os.path.join(output_dir, 'data_metrics.html'))
                
            # 导出缓存性能指标仪表板
            cache_fig = self.create_cache_metrics_dashboard()
            if cache_fig:
                cache_fig.write_html(os.path.join(output_dir, 'cache_metrics.html'))
                
            self.logger.info(f"成功导出仪表板到目录: {output_dir}")
            
        except Exception as e:
            self.logger.error(f"导出仪表板时发生错误: {str(e)}")
            raise 