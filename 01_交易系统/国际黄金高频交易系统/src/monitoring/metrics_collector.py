from typing import Dict, List, Optional
from datetime import datetime, timedelta
import psutil
import time
from dataclasses import dataclass
from loguru import logger

@dataclass
class SystemMetrics:
    """系统性能指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: float
    disk_io_write: float
    network_io_sent: float
    network_io_recv: float

@dataclass
class DataMetrics:
    """数据处理性能指标数据类"""
    timestamp: datetime
    data_type: str
    records_processed: int
    processing_time: float
    error_count: int
    avg_record_size: float

@dataclass
class CacheMetrics:
    """缓存性能指标数据类"""
    timestamp: datetime
    hit_count: int
    miss_count: int
    hit_rate: float
    memory_usage: float
    cache_size: int

class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self):
        """初始化性能指标收集器"""
        self.logger = logger.bind(context="metrics_collector")
        self._system_metrics_history: List[SystemMetrics] = []
        self._data_metrics_history: List[DataMetrics] = []
        self._cache_metrics_history: List[CacheMetrics] = []
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._last_collection_time = time.time()
        
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统性能指标
        
        Returns:
            SystemMetrics: 系统性能指标
        """
        try:
            current_time = time.time()
            time_diff = current_time - self._last_collection_time
            
            # 收集CPU和内存使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # 收集磁盘IO
            current_disk_io = psutil.disk_io_counters()
            disk_io_read = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / time_diff
            disk_io_write = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / time_diff
            
            # 收集网络IO
            current_net_io = psutil.net_io_counters()
            network_io_sent = (current_net_io.bytes_sent - self._last_net_io.bytes_sent) / time_diff
            network_io_recv = (current_net_io.bytes_recv - self._last_net_io.bytes_recv) / time_diff
            
            # 更新上一次的IO计数
            self._last_disk_io = current_disk_io
            self._last_net_io = current_net_io
            self._last_collection_time = current_time
            
            # 创建指标对象
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io_read=disk_io_read,
                disk_io_write=disk_io_write,
                network_io_sent=network_io_sent,
                network_io_recv=network_io_recv
            )
            
            # 保存到历史记录
            self._system_metrics_history.append(metrics)
            
            # 只保留最近24小时的数据
            cutoff_time = datetime.now() - timedelta(hours=24)
            self._system_metrics_history = [
                m for m in self._system_metrics_history
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集系统性能指标时发生错误: {str(e)}")
            raise
            
    def collect_data_metrics(self, data_type: str, records_processed: int,
                           processing_time: float, error_count: int,
                           avg_record_size: float) -> DataMetrics:
        """收集数据处理性能指标
        
        Args:
            data_type: 数据类型（market_data/trading_signal/order）
            records_processed: 处理的记录数
            processing_time: 处理时间（秒）
            error_count: 错误数量
            avg_record_size: 平均记录大小（字节）
            
        Returns:
            DataMetrics: 数据处理性能指标
        """
        try:
            metrics = DataMetrics(
                timestamp=datetime.now(),
                data_type=data_type,
                records_processed=records_processed,
                processing_time=processing_time,
                error_count=error_count,
                avg_record_size=avg_record_size
            )
            
            # 保存到历史记录
            self._data_metrics_history.append(metrics)
            
            # 只保留最近24小时的数据
            cutoff_time = datetime.now() - timedelta(hours=24)
            self._data_metrics_history = [
                m for m in self._data_metrics_history
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集数据处理性能指标时发生错误: {str(e)}")
            raise
            
    def collect_cache_metrics(self, hit_count: int, miss_count: int,
                            memory_usage: float, cache_size: int) -> CacheMetrics:
        """收集缓存性能指标
        
        Args:
            hit_count: 缓存命中次数
            miss_count: 缓存未命中次数
            memory_usage: 内存使用量（MB）
            cache_size: 缓存大小（记录数）
            
        Returns:
            CacheMetrics: 缓存性能指标
        """
        try:
            # 计算命中率
            total_requests = hit_count + miss_count
            hit_rate = hit_count / total_requests if total_requests > 0 else 0.0
            
            metrics = CacheMetrics(
                timestamp=datetime.now(),
                hit_count=hit_count,
                miss_count=miss_count,
                hit_rate=hit_rate,
                memory_usage=memory_usage,
                cache_size=cache_size
            )
            
            # 保存到历史记录
            self._cache_metrics_history.append(metrics)
            
            # 只保留最近24小时的数据
            cutoff_time = datetime.now() - timedelta(hours=24)
            self._cache_metrics_history = [
                m for m in self._cache_metrics_history
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集缓存性能指标时发生错误: {str(e)}")
            raise
            
    def get_system_metrics_history(self, time_range: Optional[timedelta] = None) -> List[SystemMetrics]:
        """获取系统性能指标历史记录
        
        Args:
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[SystemMetrics]: 系统性能指标历史记录
        """
        if time_range is None:
            return self._system_metrics_history
            
        cutoff_time = datetime.now() - time_range
        return [
            m for m in self._system_metrics_history
            if m.timestamp > cutoff_time
        ]
        
    def get_data_metrics_history(self, data_type: Optional[str] = None,
                               time_range: Optional[timedelta] = None) -> List[DataMetrics]:
        """获取数据处理性能指标历史记录
        
        Args:
            data_type: 数据类型过滤
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[DataMetrics]: 数据处理性能指标历史记录
        """
        metrics = self._data_metrics_history
        
        if data_type:
            metrics = [m for m in metrics if m.data_type == data_type]
            
        if time_range:
            cutoff_time = datetime.now() - time_range
            metrics = [m for m in metrics if m.timestamp > cutoff_time]
            
        return metrics
        
    def get_cache_metrics_history(self, time_range: Optional[timedelta] = None) -> List[CacheMetrics]:
        """获取缓存性能指标历史记录
        
        Args:
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[CacheMetrics]: 缓存性能指标历史记录
        """
        if time_range is None:
            return self._cache_metrics_history
            
        cutoff_time = datetime.now() - time_range
        return [
            m for m in self._cache_metrics_history
            if m.timestamp > cutoff_time
        ]
        
    def clear_history(self):
        """清除所有历史记录"""
        self._system_metrics_history.clear()
        self._data_metrics_history.clear()
        self._cache_metrics_history.clear() 