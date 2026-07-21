from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
from .performance import PerformanceCollector, PerformanceMetrics

class SystemStatus(Enum):
    """系统状态枚举"""
    HEALTHY = "healthy"  # 健康
    WARNING = "warning"  # 警告
    CRITICAL = "critical"  # 严重
    UNKNOWN = "unknown"  # 未知

@dataclass
class ComponentStatus:
    """组件状态数据类"""
    name: str
    status: SystemStatus
    message: str
    last_update: datetime
    metrics: Optional[Dict] = None

@dataclass
class SystemStatusReport:
    """系统状态报告数据类"""
    timestamp: datetime
    overall_status: SystemStatus
    components: List[ComponentStatus]
    performance_metrics: Optional[PerformanceMetrics] = None
    issues: List[str] = None

class StatusReporter:
    """系统状态报告生成器"""
    
    def __init__(self, performance_collector: PerformanceCollector):
        """
        初始化状态报告生成器
        
        Args:
            performance_collector: 性能指标收集器实例
        """
        self.performance_collector = performance_collector
        self.components: Dict[str, ComponentStatus] = {}
        self._last_report_time = 0
        
    def update_component_status(self, 
                              name: str,
                              status: SystemStatus,
                              message: str,
                              metrics: Optional[Dict] = None):
        """
        更新组件状态
        
        Args:
            name: 组件名称
            status: 组件状态
            message: 状态消息
            metrics: 组件指标数据
        """
        self.components[name] = ComponentStatus(
            name=name,
            status=status,
            message=message,
            last_update=datetime.now(),
            metrics=metrics
        )
        
    def _determine_overall_status(self) -> SystemStatus:
        """
        确定系统整体状态
        
        Returns:
            SystemStatus: 系统整体状态
        """
        if not self.components:
            return SystemStatus.UNKNOWN
            
        statuses = [comp.status for comp in self.components.values()]
        if SystemStatus.CRITICAL in statuses:
            return SystemStatus.CRITICAL
        elif SystemStatus.WARNING in statuses:
            return SystemStatus.WARNING
        elif all(s == SystemStatus.HEALTHY for s in statuses):
            return SystemStatus.HEALTHY
        else:
            return SystemStatus.UNKNOWN
            
    def _collect_issues(self) -> List[str]:
        """
        收集系统问题
        
        Returns:
            List[str]: 问题列表
        """
        issues = []
        for comp in self.components.values():
            if comp.status != SystemStatus.HEALTHY:
                issues.append(f"{comp.name}: {comp.message}")
        return issues
        
    def generate_report(self) -> Optional[SystemStatusReport]:
        """
        生成系统状态报告
        
        Returns:
            SystemStatusReport: 系统状态报告，如果生成失败则返回None
        """
        try:
            current_time = time.time()
            if current_time - self._last_report_time < 60.0:  # 每分钟最多生成一次报告
                return None
                
            self._last_report_time = current_time
            
            # 获取性能指标
            performance_metrics = self.performance_collector.get_latest_metrics()
            
            # 确定整体状态
            overall_status = self._determine_overall_status()
            
            # 收集问题
            issues = self._collect_issues()
            
            # 创建报告
            report = SystemStatusReport(
                timestamp=datetime.now(),
                overall_status=overall_status,
                components=list(self.components.values()),
                performance_metrics=performance_metrics,
                issues=issues
            )
            
            return report
            
        except Exception as e:
            logger.error(f"生成系统状态报告时发生错误: {e}")
            return None
            
    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """
        获取组件状态
        
        Args:
            name: 组件名称
            
        Returns:
            ComponentStatus: 组件状态，如果组件不存在则返回None
        """
        return self.components.get(name)
        
    def get_all_components(self) -> List[str]:
        """
        获取所有组件名称
        
        Returns:
            List[str]: 组件名称列表
        """
        return list(self.components.keys())
        
    def reset(self):
        """重置状态报告生成器"""
        self.components.clear()
        self._last_report_time = 0 