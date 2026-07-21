from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
from loguru import logger
from .status_report import SystemStatus, SystemStatusReport

class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重

@dataclass
class Alert:
    """告警数据类"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Optional[Dict] = None

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        """初始化告警管理器"""
        self.alerts: Dict[str, Alert] = {}
        self.notifiers: Dict[AlertLevel, List[Callable]] = {
            level: [] for level in AlertLevel
        }
        self._alert_counter = 0
        
    def add_notifier(self, level: AlertLevel, notifier: Callable):
        """
        添加告警通知器
        
        Args:
            level: 告警级别
            notifier: 通知器函数
        """
        self.notifiers[level].append(notifier)
        
    def _generate_alert_id(self) -> str:
        """
        生成告警ID
        
        Returns:
            str: 告警ID
        """
        self._alert_counter += 1
        return f"alert_{self._alert_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_alert(self,
                    level: AlertLevel,
                    title: str,
                    message: str,
                    source: str,
                    metadata: Optional[Dict] = None) -> Alert:
        """
        创建告警
        
        Args:
            level: 告警级别
            title: 告警标题
            message: 告警消息
            source: 告警来源
            metadata: 告警元数据
            
        Returns:
            Alert: 创建的告警
        """
        alert = Alert(
            id=self._generate_alert_id(),
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            metadata=metadata
        )
        
        self.alerts[alert.id] = alert
        self._notify(alert)
        
        return alert
        
    def _notify(self, alert: Alert):
        """
        发送告警通知
        
        Args:
            alert: 告警对象
        """
        # 获取对应级别的所有通知器
        notifiers = self.notifiers[alert.level]
        
        # 调用所有通知器
        for notifier in notifiers:
            try:
                notifier(alert)
            except Exception as e:
                logger.error(f"发送告警通知时发生错误: {e}")
                
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        获取告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            Alert: 告警对象，如果不存在则返回None
        """
        return self.alerts.get(alert_id)
        
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """
        获取指定级别的所有告警
        
        Args:
            level: 告警级别
            
        Returns:
            List[Alert]: 告警列表
        """
        return [alert for alert in self.alerts.values() if alert.level == level]
        
    def get_active_alerts(self) -> List[Alert]:
        """
        获取所有活动告警
        
        Returns:
            List[Alert]: 告警列表
        """
        return list(self.alerts.values())
        
    def clear_alerts(self):
        """清除所有告警"""
        self.alerts.clear()
        
    def process_status_report(self, report: SystemStatusReport):
        """
        处理系统状态报告
        
        Args:
            report: 系统状态报告
        """
        # 处理整体状态
        if report.overall_status == SystemStatus.CRITICAL:
            self.create_alert(
                level=AlertLevel.CRITICAL,
                title="系统严重异常",
                message="系统整体状态为严重异常",
                source="system",
                metadata={"report": report}
            )
        elif report.overall_status == SystemStatus.WARNING:
            self.create_alert(
                level=AlertLevel.WARNING,
                title="系统警告",
                message="系统整体状态为警告",
                source="system",
                metadata={"report": report}
            )
            
        # 处理组件状态
        for component in report.components:
            if component.status == SystemStatus.CRITICAL:
                self.create_alert(
                    level=AlertLevel.CRITICAL,
                    title=f"组件严重异常: {component.name}",
                    message=component.message,
                    source=component.name,
                    metadata={"component": component}
                )
            elif component.status == SystemStatus.WARNING:
                self.create_alert(
                    level=AlertLevel.WARNING,
                    title=f"组件警告: {component.name}",
                    message=component.message,
                    source=component.name,
                    metadata={"component": component}
                )
                
        # 处理性能指标
        if report.performance_metrics:
            metrics = report.performance_metrics
            if metrics.error_rate > 0.1:  # 错误率超过10%
                self.create_alert(
                    level=AlertLevel.ERROR,
                    title="高错误率警告",
                    message=f"系统错误率过高: {metrics.error_rate:.2%}",
                    source="performance",
                    metadata={"metrics": metrics}
                )
            if metrics.response_time > 1000:  # 响应时间超过1秒
                self.create_alert(
                    level=AlertLevel.WARNING,
                    title="响应时间警告",
                    message=f"系统响应时间过长: {metrics.response_time:.2f}ms",
                    source="performance",
                    metadata={"metrics": metrics}
                ) 