from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import time
from loguru import logger

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    response_time: float  # 响应时间（毫秒）
    throughput: int  # 吞吐量（每秒请求数）
    error_rate: float  # 错误率
    queue_size: int  # 队列大小
    active_connections: int  # 活动连接数
    memory_usage: float  # 内存使用量（MB）
    gc_stats: Dict[str, int]  # GC统计信息

class PerformanceCollector:
    """性能指标收集器"""
    
    def __init__(self, window_size: int = 100):
        """
        初始化性能指标收集器
        
        Args:
            window_size: 滑动窗口大小，用于计算统计值
        """
        self.window_size = window_size
        self.metrics_history: List[PerformanceMetrics] = []
        self.request_times: List[float] = []
        self.error_count = 0
        self.total_requests = 0
        self._last_collect_time = 0
        self._last_request_count = 0
        
    def record_request(self, response_time: float, is_error: bool = False):
        """
        记录请求信息
        
        Args:
            response_time: 响应时间（毫秒）
            is_error: 是否是错误请求
        """
        self.request_times.append(response_time)
        if len(self.request_times) > self.window_size:
            self.request_times.pop(0)
            
        self.total_requests += 1
        if is_error:
            self.error_count += 1
            
    def collect_metrics(self, 
                       queue_size: int,
                       active_connections: int,
                       memory_usage: float,
                       gc_stats: Dict[str, int]) -> Optional[PerformanceMetrics]:
        """
        收集性能指标
        
        Args:
            queue_size: 当前队列大小
            active_connections: 活动连接数
            memory_usage: 内存使用量（MB）
            gc_stats: GC统计信息
            
        Returns:
            PerformanceMetrics: 性能指标数据，如果收集失败则返回None
        """
        try:
            current_time = time.time()
            if current_time - self._last_collect_time < 1.0:  # 每秒最多收集一次
                return None
                
            self._last_collect_time = current_time
            
            # 计算响应时间统计
            avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
            
            # 计算吞吐量
            requests_diff = self.total_requests - self._last_request_count
            throughput = requests_diff
            self._last_request_count = self.total_requests
            
            # 计算错误率
            error_rate = self.error_count / self.total_requests if self.total_requests > 0 else 0
            
            # 创建指标对象
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                response_time=avg_response_time,
                throughput=throughput,
                error_rate=error_rate,
                queue_size=queue_size,
                active_connections=active_connections,
                memory_usage=memory_usage,
                gc_stats=gc_stats
            )
            
            # 添加到历史记录
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.window_size:
                self.metrics_history.pop(0)
                
            return metrics
            
        except Exception as e:
            logger.error(f"收集性能指标时发生错误: {e}")
            return None
            
    def get_metrics_history(self, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> List[PerformanceMetrics]:
        """
        获取指标历史记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[PerformanceMetrics]: 指标历史记录列表
        """
        if not start_time and not end_time:
            return self.metrics_history
            
        filtered_history = self.metrics_history
        if start_time:
            filtered_history = [m for m in filtered_history if m.timestamp >= start_time]
        if end_time:
            filtered_history = [m for m in filtered_history if m.timestamp <= end_time]
            
        return filtered_history
        
    def get_latest_metrics(self) -> Optional[PerformanceMetrics]:
        """
        获取最新的指标数据
        
        Returns:
            PerformanceMetrics: 最新的性能指标数据，如果没有数据则返回None
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
            "response_time": latest.response_time,
            "throughput": latest.throughput,
            "error_rate": latest.error_rate,
            "queue_size": latest.queue_size,
            "active_connections": latest.active_connections,
            "memory_usage": latest.memory_usage
        }
        
    def reset(self):
        """重置收集器状态"""
        self.metrics_history.clear()
        self.request_times.clear()
        self.error_count = 0
        self.total_requests = 0
        self._last_collect_time = 0
        self._last_request_count = 0 