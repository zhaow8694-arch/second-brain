import psutil
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io_bytes_sent: int
    network_io_bytes_recv: int
    process_count: int
    thread_count: int

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, collect_interval: float = 1.0):
        """
        初始化系统监控器
        
        Args:
            collect_interval: 指标收集间隔（秒）
        """
        self.collect_interval = collect_interval
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000  # 最大历史记录数
        self._last_collect_time = 0
        
    def collect_metrics(self) -> Optional[SystemMetrics]:
        """
        收集系统指标
        
        Returns:
            SystemMetrics: 系统指标数据，如果收集失败则返回None
        """
        try:
            current_time = time.time()
            if current_time - self._last_collect_time < self.collect_interval:
                return None
                
            self._last_collect_time = current_time
            
            # 收集CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 收集内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 收集磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # 收集网络IO
            net_io = psutil.net_io_counters()
            network_io_bytes_sent = net_io.bytes_sent
            network_io_bytes_recv = net_io.bytes_recv
            
            # 收集进程和线程数
            process_count = len(psutil.pids())
            thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']))
            
            # 创建指标对象
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io_bytes_sent=network_io_bytes_sent,
                network_io_bytes_recv=network_io_bytes_recv,
                process_count=process_count,
                thread_count=thread_count
            )
            
            # 添加到历史记录
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
                
            return metrics
            
        except Exception as e:
            logger.error(f"收集系统指标时发生错误: {e}")
            return None
            
    def get_metrics_history(self, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> List[SystemMetrics]:
        """
        获取指标历史记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[SystemMetrics]: 指标历史记录列表
        """
        if not start_time and not end_time:
            return self.metrics_history
            
        filtered_history = self.metrics_history
        if start_time:
            filtered_history = [m for m in filtered_history if m.timestamp >= start_time]
        if end_time:
            filtered_history = [m for m in filtered_history if m.timestamp <= end_time]
            
        return filtered_history
        
    def get_latest_metrics(self) -> Optional[SystemMetrics]:
        """
        获取最新的指标数据
        
        Returns:
            SystemMetrics: 最新的系统指标数据，如果没有数据则返回None
        """
        return self.metrics_history[-1] if self.metrics_history else None
        
    def get_metrics_summary(self) -> Dict[str, float]:
        """
        获取指标统计摘要
        
        Returns:
            Dict[str, float]: 指标统计摘要
        """
        if not self.metrics_history:
            return {}
            
        latest = self.metrics_history[-1]
        return {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "disk_usage_percent": latest.disk_usage_percent,
            "network_io_bytes_sent": latest.network_io_bytes_sent,
            "network_io_bytes_recv": latest.network_io_bytes_recv,
            "process_count": latest.process_count,
            "thread_count": latest.thread_count
        } 