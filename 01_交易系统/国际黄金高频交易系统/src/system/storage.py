import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from loguru import logger
import sqlite3
from contextlib import contextmanager

from .performance import PerformanceMetrics
from .status_report import SystemStatusReport, ComponentStatus
from .alert import Alert, AlertLevel

class MonitoringStorage:
    """监控数据存储管理器"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        """
        初始化存储管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建性能指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    response_time REAL,
                    throughput INTEGER,
                    error_rate REAL,
                    queue_size INTEGER,
                    active_connections INTEGER,
                    memory_usage REAL,
                    gc_stats TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建组件状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS component_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    metrics TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建系统状态报告表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS status_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    overall_status TEXT NOT NULL,
                    components TEXT,
                    performance_metrics_id INTEGER,
                    issues TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (performance_metrics_id) REFERENCES performance_metrics(id)
                )
            """)
            
            # 创建告警表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    source TEXT NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
            
    def save_performance_metrics(self, metrics: PerformanceMetrics):
        """
        保存性能指标
        
        Args:
            metrics: 性能指标对象
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (
                    timestamp, response_time, throughput, error_rate,
                    queue_size, active_connections, memory_usage, gc_stats
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp,
                metrics.response_time,
                metrics.throughput,
                metrics.error_rate,
                metrics.queue_size,
                metrics.active_connections,
                metrics.memory_usage,
                json.dumps(metrics.gc_stats)
            ))
            return cursor.lastrowid
            
    def save_component_status(self, status: ComponentStatus):
        """
        保存组件状态
        
        Args:
            status: 组件状态对象
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO component_status (
                    timestamp, name, status, message, metrics
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                status.last_update,
                status.name,
                status.status.value,
                status.message,
                json.dumps(status.metrics) if status.metrics else None
            ))
            
    def save_status_report(self, report: SystemStatusReport):
        """
        保存系统状态报告
        
        Args:
            report: 系统状态报告对象
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 保存性能指标
            metrics_id = None
            if report.performance_metrics:
                metrics_id = self.save_performance_metrics(report.performance_metrics)
                
            # 保存组件状态
            for component in report.components:
                self.save_component_status(component)
                
            # 保存状态报告
            cursor.execute("""
                INSERT INTO status_reports (
                    timestamp, overall_status, components,
                    performance_metrics_id, issues
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                report.timestamp,
                report.overall_status.value,
                json.dumps([asdict(comp) for comp in report.components]),
                metrics_id,
                json.dumps(report.issues) if report.issues else None
            ))
            
    def save_alert(self, alert: Alert):
        """
        保存告警
        
        Args:
            alert: 告警对象
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (
                    id, level, title, message, timestamp,
                    source, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.level.value,
                alert.title,
                alert.message,
                alert.timestamp,
                alert.source,
                json.dumps(alert.metadata) if alert.metadata else None
            ))
            
    def get_performance_metrics(self,
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              limit: int = 100) -> List[PerformanceMetrics]:
        """
        获取性能指标历史记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            List[PerformanceMetrics]: 性能指标列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM performance_metrics WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            metrics = []
            for row in rows:
                metrics.append(PerformanceMetrics(
                    timestamp=row[1],
                    response_time=row[2],
                    throughput=row[3],
                    error_rate=row[4],
                    queue_size=row[5],
                    active_connections=row[6],
                    memory_usage=row[7],
                    gc_stats=json.loads(row[8])
                ))
                
            return metrics
            
    def get_component_status(self,
                           component_name: Optional[str] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: int = 100) -> List[ComponentStatus]:
        """
        获取组件状态历史记录
        
        Args:
            component_name: 组件名称
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            List[ComponentStatus]: 组件状态列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM component_status WHERE 1=1"
            params = []
            
            if component_name:
                query += " AND name = ?"
                params.append(component_name)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            statuses = []
            for row in rows:
                statuses.append(ComponentStatus(
                    name=row[2],
                    status=SystemStatus(row[3]),
                    message=row[4],
                    last_update=row[1],
                    metrics=json.loads(row[5]) if row[5] else None
                ))
                
            return statuses
            
    def get_status_reports(self,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          limit: int = 100) -> List[SystemStatusReport]:
        """
        获取系统状态报告历史记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            List[SystemStatusReport]: 状态报告列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM status_reports WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                components_data = json.loads(row[3])
                components = [
                    ComponentStatus(**comp_data)
                    for comp_data in components_data
                ]
                
                reports.append(SystemStatusReport(
                    timestamp=row[1],
                    overall_status=SystemStatus(row[2]),
                    components=components,
                    performance_metrics=self.get_performance_metrics(
                        start_time=row[1],
                        end_time=row[1]
                    )[0] if row[4] else None,
                    issues=json.loads(row[5]) if row[5] else None
                ))
                
            return reports
            
    def get_alerts(self,
                  level: Optional[AlertLevel] = None,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  limit: int = 100) -> List[Alert]:
        """
        获取告警历史记录
        
        Args:
            level: 告警级别
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            List[Alert]: 告警列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level.value)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=row[0],
                    level=AlertLevel(row[1]),
                    title=row[2],
                    message=row[3],
                    timestamp=row[4],
                    source=row[5],
                    metadata=json.loads(row[6]) if row[6] else None
                ))
                
            return alerts
            
    def cleanup_old_data(self, days: int = 30):
        """
        清理旧数据
        
        Args:
            days: 保留天数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days)
            
            # 删除旧数据
            cursor.execute("""
                DELETE FROM performance_metrics
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            cursor.execute("""
                DELETE FROM component_status
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            cursor.execute("""
                DELETE FROM status_reports
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            cursor.execute("""
                DELETE FROM alerts
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            conn.commit() 