import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from src.system.performance import PerformanceMetrics
from src.system.status_report import SystemStatusReport, ComponentStatus
from src.system.alert import Alert
from src.system.storage import MonitoringStorage
from src.system.logger import logger

class DataVisualizer:
    """数据可视化类"""
    
    def __init__(self, storage: MonitoringStorage):
        """初始化数据可视化器
        
        Args:
            storage: 数据存储管理器实例
        """
        self.storage = storage
        plt.style.use('seaborn')
    
    def plot_performance_metrics(self, 
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               metrics: List[str] = None) -> None:
        """绘制性能指标图表
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            metrics: 要绘制的指标列表
        """
        # 获取性能指标数据
        data = self.storage.get_performance_metrics(
            start_time=start_time,
            end_time=end_time
        )
        
        if not data:
            logger.warning("没有找到性能指标数据")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'timestamp': m.timestamp,
            'response_time': m.response_time,
            'throughput': m.throughput,
            'error_rate': m.error_rate,
            'queue_size': m.queue_size,
            'active_connections': m.active_connections,
            'memory_usage': m.memory_usage
        } for m in data])
        
        # 设置要绘制的指标
        if metrics is None:
            metrics = ['response_time', 'throughput', 'error_rate']
        
        # 创建图表
        fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 4*len(metrics)))
        if len(metrics) == 1:
            axes = [axes]
        
        # 绘制每个指标
        for i, metric in enumerate(metrics):
            ax = axes[i]
            ax.plot(df['timestamp'], df[metric])
            ax.set_title(f'{metric.replace("_", " ").title()}')
            ax.set_xlabel('Time')
            ax.set_ylabel(metric.replace("_", " ").title())
            ax.grid(True)
        
        plt.tight_layout()
        plt.savefig('performance_metrics.png')
        plt.close()
        logger.info("性能指标图表已保存为 performance_metrics.png")
    
    def plot_component_status(self, 
                            component_name: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> None:
        """绘制组件状态图表
        
        Args:
            component_name: 组件名称
            start_time: 开始时间
            end_time: 结束时间
        """
        # 获取组件状态数据
        data = self.storage.get_component_status(
            component_name=component_name,
            start_time=start_time,
            end_time=end_time
        )
        
        if not data:
            logger.warning(f"没有找到组件 {component_name} 的状态数据")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'timestamp': s.last_update,
            'status': s.status.value,
            'message': s.message
        } for s in data])
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制状态
        ax.plot(df['timestamp'], df['status'], 'o-')
        ax.set_title(f'Component {component_name} Status')
        ax.set_xlabel('Time')
        ax.set_ylabel('Status')
        ax.grid(True)
        
        # 添加状态标签
        status_labels = {
            'HEALTHY': 0,
            'WARNING': 1,
            'CRITICAL': 2
        }
        ax.set_yticks(list(status_labels.values()))
        ax.set_yticklabels(list(status_labels.keys()))
        
        plt.tight_layout()
        plt.savefig(f'component_status_{component_name}.png')
        plt.close()
        logger.info(f"组件状态图表已保存为 component_status_{component_name}.png")
    
    def plot_alert_trend(self,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> None:
        """绘制告警趋势图表
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
        """
        # 获取告警数据
        data = self.storage.get_alerts(
            start_time=start_time,
            end_time=end_time
        )
        
        if not data:
            logger.warning("没有找到告警数据")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'timestamp': a.timestamp,
            'level': a.level.value,
            'title': a.title
        } for a in data])
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制告警级别
        ax.scatter(df['timestamp'], df['level'], c=df['level'], cmap='RdYlGn_r')
        ax.set_title('Alert Trend')
        ax.set_xlabel('Time')
        ax.set_ylabel('Alert Level')
        ax.grid(True)
        
        # 添加告警级别标签
        level_labels = {
            'INFO': 0,
            'WARNING': 1,
            'ERROR': 2,
            'CRITICAL': 3
        }
        ax.set_yticks(list(level_labels.values()))
        ax.set_yticklabels(list(level_labels.keys()))
        
        plt.tight_layout()
        plt.savefig('alert_trend.png')
        plt.close()
        logger.info("告警趋势图表已保存为 alert_trend.png")
    
    def generate_dashboard(self,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> None:
        """生成完整的监控仪表板
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
        """
        # 设置默认时间范围
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=24)
        
        # 生成所有图表
        self.plot_performance_metrics(start_time, end_time)
        self.plot_component_status('database', start_time, end_time)
        self.plot_component_status('cache', start_time, end_time)
        self.plot_component_status('api', start_time, end_time)
        self.plot_alert_trend(start_time, end_time)
        
        logger.info("监控仪表板已生成完成") 