from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .metrics_collector import SystemMetrics, DataMetrics, CacheMetrics
from .metrics_storage import MetricsStorage

@dataclass
class AlertThreshold:
    """告警阈值配置"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str  # 'gt' (greater than) or 'lt' (less than)
    description: str

@dataclass
class Alert:
    """告警信息"""
    timestamp: datetime
    level: str  # 'warning' or 'critical'
    metric_name: str
    current_value: float
    threshold: float
    description: str

class MetricsAlert:
    """性能指标告警系统"""
    
    def __init__(self, storage: MetricsStorage, smtp_config: Dict[str, Any]):
        """初始化性能指标告警系统
        
        Args:
            storage: 性能指标存储管理器
            smtp_config: SMTP服务器配置
        """
        self.logger = logger.bind(context="metrics_alert")
        self.storage = storage
        self.smtp_config = smtp_config
        self.thresholds = self._init_thresholds()
        self.alert_history: List[Alert] = []
        
    def _init_thresholds(self) -> List[AlertThreshold]:
        """初始化告警阈值配置
        
        Returns:
            List[AlertThreshold]: 告警阈值配置列表
        """
        return [
            # 系统性能指标阈值
            AlertThreshold(
                metric_name='cpu_percent',
                warning_threshold=80.0,
                critical_threshold=90.0,
                comparison='gt',
                description='CPU使用率过高'
            ),
            AlertThreshold(
                metric_name='memory_percent',
                warning_threshold=80.0,
                critical_threshold=90.0,
                comparison='gt',
                description='内存使用率过高'
            ),
            AlertThreshold(
                metric_name='disk_io_read',
                warning_threshold=1000.0,  # MB/s
                critical_threshold=2000.0,  # MB/s
                comparison='gt',
                description='磁盘读取速度过高'
            ),
            AlertThreshold(
                metric_name='disk_io_write',
                warning_threshold=1000.0,  # MB/s
                critical_threshold=2000.0,  # MB/s
                comparison='gt',
                description='磁盘写入速度过高'
            ),
            
            # 数据处理性能指标阈值
            AlertThreshold(
                metric_name='processing_time',
                warning_threshold=1.0,  # 秒
                critical_threshold=2.0,  # 秒
                comparison='gt',
                description='数据处理时间过长'
            ),
            AlertThreshold(
                metric_name='error_rate',
                warning_threshold=0.01,  # 1%
                critical_threshold=0.05,  # 5%
                comparison='gt',
                description='数据处理错误率过高'
            ),
            
            # 缓存性能指标阈值
            AlertThreshold(
                metric_name='hit_rate',
                warning_threshold=0.8,  # 80%
                critical_threshold=0.6,  # 60%
                comparison='lt',
                description='缓存命中率过低'
            ),
            AlertThreshold(
                metric_name='memory_usage',
                warning_threshold=1000.0,  # MB
                critical_threshold=2000.0,  # MB
                comparison='gt',
                description='缓存内存使用量过高'
            )
        ]
        
    def check_system_metrics(self, metrics: SystemMetrics) -> List[Alert]:
        """检查系统性能指标
        
        Args:
            metrics: 系统性能指标
            
        Returns:
            List[Alert]: 告警列表
        """
        alerts = []
        
        # 检查CPU使用率
        cpu_threshold = next(t for t in self.thresholds if t.metric_name == 'cpu_percent')
        if self._check_threshold(metrics.cpu_percent, cpu_threshold):
            alerts.append(self._create_alert(metrics.cpu_percent, cpu_threshold))
            
        # 检查内存使用率
        memory_threshold = next(t for t in self.thresholds if t.metric_name == 'memory_percent')
        if self._check_threshold(metrics.memory_percent, memory_threshold):
            alerts.append(self._create_alert(metrics.memory_percent, memory_threshold))
            
        # 检查磁盘IO
        disk_read_threshold = next(t for t in self.thresholds if t.metric_name == 'disk_io_read')
        if self._check_threshold(metrics.disk_io_read, disk_read_threshold):
            alerts.append(self._create_alert(metrics.disk_io_read, disk_read_threshold))
            
        disk_write_threshold = next(t for t in self.thresholds if t.metric_name == 'disk_io_write')
        if self._check_threshold(metrics.disk_io_write, disk_write_threshold):
            alerts.append(self._create_alert(metrics.disk_io_write, disk_write_threshold))
            
        return alerts
        
    def check_data_metrics(self, metrics: DataMetrics) -> List[Alert]:
        """检查数据处理性能指标
        
        Args:
            metrics: 数据处理性能指标
            
        Returns:
            List[Alert]: 告警列表
        """
        alerts = []
        
        # 检查处理时间
        processing_time_threshold = next(t for t in self.thresholds if t.metric_name == 'processing_time')
        if self._check_threshold(metrics.processing_time, processing_time_threshold):
            alerts.append(self._create_alert(metrics.processing_time, processing_time_threshold))
            
        # 检查错误率
        error_rate = metrics.error_count / metrics.records_processed if metrics.records_processed > 0 else 0
        error_rate_threshold = next(t for t in self.thresholds if t.metric_name == 'error_rate')
        if self._check_threshold(error_rate, error_rate_threshold):
            alerts.append(self._create_alert(error_rate, error_rate_threshold))
            
        return alerts
        
    def check_cache_metrics(self, metrics: CacheMetrics) -> List[Alert]:
        """检查缓存性能指标
        
        Args:
            metrics: 缓存性能指标
            
        Returns:
            List[Alert]: 告警列表
        """
        alerts = []
        
        # 检查命中率
        hit_rate_threshold = next(t for t in self.thresholds if t.metric_name == 'hit_rate')
        if self._check_threshold(metrics.hit_rate, hit_rate_threshold):
            alerts.append(self._create_alert(metrics.hit_rate, hit_rate_threshold))
            
        # 检查内存使用量
        memory_usage_threshold = next(t for t in self.thresholds if t.metric_name == 'memory_usage')
        if self._check_threshold(metrics.memory_usage, memory_usage_threshold):
            alerts.append(self._create_alert(metrics.memory_usage, memory_usage_threshold))
            
        return alerts
        
    def _check_threshold(self, value: float, threshold: AlertThreshold) -> bool:
        """检查是否超过阈值
        
        Args:
            value: 当前值
            threshold: 阈值配置
            
        Returns:
            bool: 是否超过阈值
        """
        if threshold.comparison == 'gt':
            return value > threshold.warning_threshold
        else:  # lt
            return value < threshold.warning_threshold
            
    def _create_alert(self, value: float, threshold: AlertThreshold) -> Alert:
        """创建告警信息
        
        Args:
            value: 当前值
            threshold: 阈值配置
            
        Returns:
            Alert: 告警信息
        """
        level = 'critical' if (
            (threshold.comparison == 'gt' and value > threshold.critical_threshold) or
            (threshold.comparison == 'lt' and value < threshold.critical_threshold)
        ) else 'warning'
        
        return Alert(
            timestamp=datetime.now(),
            level=level,
            metric_name=threshold.metric_name,
            current_value=value,
            threshold=threshold.warning_threshold if level == 'warning' else threshold.critical_threshold,
            description=threshold.description
        )
        
    def send_alert(self, alert: Alert, recipients: List[str]):
        """发送告警邮件
        
        Args:
            alert: 告警信息
            recipients: 收件人列表
        """
        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['Subject'] = f'性能告警 - {alert.level.upper()}'
            msg['From'] = self.smtp_config['sender']
            msg['To'] = ', '.join(recipients)
            
            body = f"""
            告警时间: {alert.timestamp}
            告警级别: {alert.level.upper()}
            指标名称: {alert.metric_name}
            当前值: {alert.current_value}
            阈值: {alert.threshold}
            描述: {alert.description}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
                
            self.logger.info(f"成功发送告警邮件给: {recipients}")
            
        except Exception as e:
            self.logger.error(f"发送告警邮件时发生错误: {str(e)}")
            raise
            
    def check_and_alert(self, recipients: List[str]):
        """检查所有性能指标并发送告警
        
        Args:
            recipients: 告警邮件收件人列表
        """
        try:
            # 获取最新的性能指标
            system_metrics = self.storage.get_system_metrics(timedelta(minutes=5))[0]
            data_metrics = self.storage.get_data_metrics(time_range=timedelta(minutes=5))
            cache_metrics = self.storage.get_cache_metrics(timedelta(minutes=5))[0]
            
            # 检查系统性能指标
            system_alerts = self.check_system_metrics(system_metrics)
            
            # 检查数据处理性能指标
            data_alerts = []
            for metrics in data_metrics:
                data_alerts.extend(self.check_data_metrics(metrics))
                
            # 检查缓存性能指标
            cache_alerts = self.check_cache_metrics(cache_metrics)
            
            # 合并所有告警
            all_alerts = system_alerts + data_alerts + cache_alerts
            
            # 发送告警
            for alert in all_alerts:
                self.send_alert(alert, recipients)
                self.alert_history.append(alert)
                
            # 只保留最近24小时的告警历史
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.alert_history = [
                a for a in self.alert_history
                if a.timestamp > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"检查性能指标并发送告警时发生错误: {str(e)}")
            raise
            
    def get_alert_history(self, time_range: Optional[timedelta] = None) -> List[Alert]:
        """获取告警历史记录
        
        Args:
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[Alert]: 告警历史记录
        """
        if time_range is None:
            return self.alert_history
            
        cutoff_time = datetime.now() - time_range
        return [
            a for a in self.alert_history
            if a.timestamp > cutoff_time
        ] 