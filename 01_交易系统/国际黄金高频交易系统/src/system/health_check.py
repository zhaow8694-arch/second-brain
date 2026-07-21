from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from loguru import logger

from .monitor import SystemMonitor, SystemMetrics

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"  # 健康
    WARNING = "warning"  # 警告
    CRITICAL = "critical"  # 严重

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    timestamp: datetime
    status: HealthStatus
    metrics: SystemMetrics
    warnings: List[str]
    errors: List[str]

class HealthChecker:
    """系统健康检查器"""
    
    def __init__(self, 
                 monitor: SystemMonitor,
                 warning_thresholds: Optional[Dict[str, float]] = None,
                 critical_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化健康检查器
        
        Args:
            monitor: 系统监控器实例
            warning_thresholds: 警告阈值
            critical_thresholds: 严重阈值
        """
        self.monitor = monitor
        self.warning_thresholds = warning_thresholds or {
            "cpu_percent": 80.0,
            "memory_percent": 80.0,
            "disk_usage_percent": 80.0,
            "process_count": 1000,
            "thread_count": 5000
        }
        self.critical_thresholds = critical_thresholds or {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "disk_usage_percent": 90.0,
            "process_count": 2000,
            "thread_count": 10000
        }
        
    def check_health(self) -> HealthCheckResult:
        """
        执行健康检查
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        # 获取最新指标
        metrics = self.monitor.get_latest_metrics()
        if not metrics:
            return HealthCheckResult(
                timestamp=datetime.now(),
                status=HealthStatus.CRITICAL,
                metrics=None,
                warnings=[],
                errors=["无法获取系统指标"]
            )
            
        warnings = []
        errors = []
        
        # 检查CPU使用率
        if metrics.cpu_percent >= self.critical_thresholds["cpu_percent"]:
            errors.append(f"CPU使用率过高: {metrics.cpu_percent:.2f}%")
        elif metrics.cpu_percent >= self.warning_thresholds["cpu_percent"]:
            warnings.append(f"CPU使用率较高: {metrics.cpu_percent:.2f}%")
            
        # 检查内存使用率
        if metrics.memory_percent >= self.critical_thresholds["memory_percent"]:
            errors.append(f"内存使用率过高: {metrics.memory_percent:.2f}%")
        elif metrics.memory_percent >= self.warning_thresholds["memory_percent"]:
            warnings.append(f"内存使用率较高: {metrics.memory_percent:.2f}%")
            
        # 检查磁盘使用率
        if metrics.disk_usage_percent >= self.critical_thresholds["disk_usage_percent"]:
            errors.append(f"磁盘使用率过高: {metrics.disk_usage_percent:.2f}%")
        elif metrics.disk_usage_percent >= self.warning_thresholds["disk_usage_percent"]:
            warnings.append(f"磁盘使用率较高: {metrics.disk_usage_percent:.2f}%")
            
        # 检查进程数
        if metrics.process_count >= self.critical_thresholds["process_count"]:
            errors.append(f"进程数过多: {metrics.process_count}")
        elif metrics.process_count >= self.warning_thresholds["process_count"]:
            warnings.append(f"进程数较多: {metrics.process_count}")
            
        # 检查线程数
        if metrics.thread_count >= self.critical_thresholds["thread_count"]:
            errors.append(f"线程数过多: {metrics.thread_count}")
        elif metrics.thread_count >= self.warning_thresholds["thread_count"]:
            warnings.append(f"线程数较多: {metrics.thread_count}")
            
        # 确定健康状态
        if errors:
            status = HealthStatus.CRITICAL
        elif warnings:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
            
        return HealthCheckResult(
            timestamp=datetime.now(),
            status=status,
            metrics=metrics,
            warnings=warnings,
            errors=errors
        )
        
    def update_thresholds(self, 
                         warning_thresholds: Optional[Dict[str, float]] = None,
                         critical_thresholds: Optional[Dict[str, float]] = None):
        """
        更新阈值设置
        
        Args:
            warning_thresholds: 新的警告阈值
            critical_thresholds: 新的严重阈值
        """
        if warning_thresholds:
            self.warning_thresholds.update(warning_thresholds)
        if critical_thresholds:
            self.critical_thresholds.update(critical_thresholds)
            
    def get_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        获取当前阈值设置
        
        Returns:
            Dict[str, Dict[str, float]]: 当前阈值设置
        """
        return {
            "warning": self.warning_thresholds,
            "critical": self.critical_thresholds
        } 