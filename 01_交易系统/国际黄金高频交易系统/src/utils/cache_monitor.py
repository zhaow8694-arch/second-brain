from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import asyncio
import json

from src.utils.cache_stats import cache_stats
from src.utils.cache_manager import CacheManager
from src.utils.cache_cleaner import cache_cleaner

@dataclass
class CacheMetrics:
    """缓存性能指标"""
    total_hits: int = 0  # 总命中次数
    total_misses: int = 0  # 总未命中次数
    total_errors: int = 0  # 总错误次数
    hit_rate: float = 0.0  # 命中率
    error_rate: float = 0.0  # 错误率
    memory_usage: int = 0  # 内存使用量（字节）
    cache_size: int = 0  # 缓存项数量
    avg_response_time: float = 0.0  # 平均响应时间（毫秒）

class CacheMonitor:
    """缓存监控器"""
    
    def __init__(self):
        """初始化缓存监控器"""
        self._metrics_history: Dict[str, List[CacheMetrics]] = {}
        self._response_times: Dict[str, List[float]] = {}
        self._alert_thresholds = {
            'hit_rate': 0.5,  # 最低命中率阈值
            'error_rate': 0.1,  # 最高错误率阈值
            'memory_usage': 1024 * 1024 * 100,  # 最大内存使用量（100MB）
            'response_time': 100.0  # 最大响应时间（毫秒）
        }
    
    async def collect_metrics(self, cache_key: str) -> CacheMetrics:
        """收集缓存指标
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存性能指标
        """
        try:
            # 获取基础统计信息
            stats = cache_stats.get_stats(cache_key)
            hit_rate = cache_stats.get_hit_rate(cache_key)
            error_rate = cache_stats.get_error_rate(cache_key)
            
            # 计算平均响应时间
            response_times = self._response_times.get(cache_key, [])
            avg_response_time = (
                sum(response_times) / len(response_times)
                if response_times else 0.0
            )
            
            # 获取缓存大小信息
            cache_size = await CacheManager.get_cache_size(cache_key)
            memory_usage = await CacheManager.get_memory_usage(cache_key)
            
            # 创建指标对象
            metrics = CacheMetrics(
                total_hits=stats.hits,
                total_misses=stats.misses,
                total_errors=stats.errors,
                hit_rate=hit_rate,
                error_rate=error_rate,
                memory_usage=memory_usage,
                cache_size=cache_size,
                avg_response_time=avg_response_time
            )
            
            # 保存历史记录
            if cache_key not in self._metrics_history:
                self._metrics_history[cache_key] = []
            self._metrics_history[cache_key].append(metrics)
            
            # 只保留最近24小时的数据
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self._metrics_history[cache_key] = [
                m for m in self._metrics_history[cache_key]
                if m.timestamp > cutoff_time
            ]
            
            return metrics
        except Exception as e:
            logger.error(f"收集缓存指标失败: {str(e)}")
            return CacheMetrics()
    
    def record_response_time(self, cache_key: str, response_time: float):
        """记录响应时间
        
        Args:
            cache_key: 缓存键
            response_time: 响应时间（毫秒）
        """
        if cache_key not in self._response_times:
            self._response_times[cache_key] = []
        
        self._response_times[cache_key].append(response_time)
        
        # 只保留最近1000个样本
        if len(self._response_times[cache_key]) > 1000:
            self._response_times[cache_key] = self._response_times[cache_key][-1000:]
    
    def check_alerts(self, metrics: CacheMetrics) -> List[str]:
        """检查是否需要发出告警
        
        Args:
            metrics: 缓存性能指标
            
        Returns:
            告警消息列表
        """
        alerts = []
        
        # 检查命中率
        if metrics.hit_rate < self._alert_thresholds['hit_rate']:
            alerts.append(
                f"命中率过低: {metrics.hit_rate:.2%} "
                f"(阈值: {self._alert_thresholds['hit_rate']:.2%})"
            )
        
        # 检查错误率
        if metrics.error_rate > self._alert_thresholds['error_rate']:
            alerts.append(
                f"错误率过高: {metrics.error_rate:.2%} "
                f"(阈值: {self._alert_thresholds['error_rate']:.2%})"
            )
        
        # 检查内存使用量
        if metrics.memory_usage > self._alert_thresholds['memory_usage']:
            alerts.append(
                f"内存使用量过高: {metrics.memory_usage / 1024 / 1024:.2f}MB "
                f"(阈值: {self._alert_thresholds['memory_usage'] / 1024 / 1024:.2f}MB)"
            )
        
        # 检查响应时间
        if metrics.avg_response_time > self._alert_thresholds['response_time']:
            alerts.append(
                f"响应时间过长: {metrics.avg_response_time:.2f}ms "
                f"(阈值: {self._alert_thresholds['response_time']:.2f}ms)"
            )
        
        return alerts
    
    def get_metrics_history(
        self,
        cache_key: str,
        hours: int = 24
    ) -> List[CacheMetrics]:
        """获取历史指标数据
        
        Args:
            cache_key: 缓存键
            hours: 获取最近多少小时的数据
            
        Returns:
            历史指标数据列表
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            m for m in self._metrics_history.get(cache_key, [])
            if m.timestamp > cutoff_time
        ]
    
    def export_metrics(self, cache_key: str) -> str:
        """导出指标数据为JSON格式
        
        Args:
            cache_key: 缓存键
            
        Returns:
            JSON格式的指标数据
        """
        metrics = self.get_metrics_history(cache_key)
        return json.dumps([vars(m) for m in metrics], default=str)
    
    async def monitor_cache(self, cache_key: str, interval: int = 60):
        """持续监控缓存性能
        
        Args:
            cache_key: 缓存键
            interval: 监控间隔（秒）
        """
        while True:
            try:
                # 收集指标
                metrics = await self.collect_metrics(cache_key)
                
                # 检查告警
                alerts = self.check_alerts(metrics)
                if alerts:
                    logger.warning(
                        f"缓存性能告警 - {cache_key}:\n" +
                        "\n".join(alerts)
                    )
                
                # 记录指标
                logger.info(
                    f"缓存性能指标 - {cache_key}:\n"
                    f"命中率: {metrics.hit_rate:.2%}\n"
                    f"错误率: {metrics.error_rate:.2%}\n"
                    f"内存使用: {metrics.memory_usage / 1024 / 1024:.2f}MB\n"
                    f"缓存项数: {metrics.cache_size}\n"
                    f"平均响应时间: {metrics.avg_response_time:.2f}ms"
                )
                
                # 如果性能不佳，触发清理
                if (metrics.hit_rate < 0.3 or
                    metrics.error_rate > 0.2 or
                    metrics.memory_usage > self._alert_thresholds['memory_usage']):
                    await cache_cleaner.clean_low_hit_rate_cache(0.3)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控缓存失败: {str(e)}")
                await asyncio.sleep(interval)

# 创建全局缓存监控器实例
cache_monitor = CacheMonitor() 