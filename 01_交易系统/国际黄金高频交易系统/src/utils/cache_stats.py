from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger

@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0  # 缓存命中次数
    misses: int = 0  # 缓存未命中次数
    sets: int = 0  # 缓存写入次数
    deletes: int = 0  # 缓存删除次数
    errors: int = 0  # 缓存操作错误次数
    last_hit_time: Optional[datetime] = None  # 最后一次命中时间
    last_miss_time: Optional[datetime] = None  # 最后一次未命中时间
    last_set_time: Optional[datetime] = None  # 最后一次写入时间
    last_error_time: Optional[datetime] = None  # 最后一次错误时间

class CacheStatsManager:
    """缓存统计管理器"""
    
    def __init__(self):
        """初始化缓存统计管理器"""
        self._stats: Dict[str, CacheStats] = {}
        self._global_stats = CacheStats()
    
    def record_hit(self, cache_key: str):
        """记录缓存命中"""
        if cache_key not in self._stats:
            self._stats[cache_key] = CacheStats()
        
        self._stats[cache_key].hits += 1
        self._stats[cache_key].last_hit_time = datetime.utcnow()
        self._global_stats.hits += 1
        self._global_stats.last_hit_time = datetime.utcnow()
    
    def record_miss(self, cache_key: str):
        """记录缓存未命中"""
        if cache_key not in self._stats:
            self._stats[cache_key] = CacheStats()
        
        self._stats[cache_key].misses += 1
        self._stats[cache_key].last_miss_time = datetime.utcnow()
        self._global_stats.misses += 1
        self._global_stats.last_miss_time = datetime.utcnow()
    
    def record_set(self, cache_key: str):
        """记录缓存写入"""
        if cache_key not in self._stats:
            self._stats[cache_key] = CacheStats()
        
        self._stats[cache_key].sets += 1
        self._stats[cache_key].last_set_time = datetime.utcnow()
        self._global_stats.sets += 1
        self._global_stats.last_set_time = datetime.utcnow()
    
    def record_delete(self, cache_key: str):
        """记录缓存删除"""
        if cache_key not in self._stats:
            self._stats[cache_key] = CacheStats()
        
        self._stats[cache_key].deletes += 1
        self._global_stats.deletes += 1
    
    def record_error(self, cache_key: str):
        """记录缓存错误"""
        if cache_key not in self._stats:
            self._stats[cache_key] = CacheStats()
        
        self._stats[cache_key].errors += 1
        self._stats[cache_key].last_error_time = datetime.utcnow()
        self._global_stats.errors += 1
        self._global_stats.last_error_time = datetime.utcnow()
    
    def get_stats(self, cache_key: Optional[str] = None) -> CacheStats:
        """获取缓存统计信息
        
        Args:
            cache_key: 缓存键，如果为 None 则返回全局统计信息
            
        Returns:
            缓存统计信息
        """
        if cache_key is None:
            return self._global_stats
        return self._stats.get(cache_key, CacheStats())
    
    def get_hit_rate(self, cache_key: Optional[str] = None) -> float:
        """获取缓存命中率
        
        Args:
            cache_key: 缓存键，如果为 None 则返回全局命中率
            
        Returns:
            缓存命中率
        """
        stats = self.get_stats(cache_key)
        total = stats.hits + stats.misses
        return stats.hits / total if total > 0 else 0.0
    
    def get_error_rate(self, cache_key: Optional[str] = None) -> float:
        """获取缓存错误率
        
        Args:
            cache_key: 缓存键，如果为 None 则返回全局错误率
            
        Returns:
            缓存错误率
        """
        stats = self.get_stats(cache_key)
        total = stats.hits + stats.misses + stats.sets + stats.deletes
        return stats.errors / total if total > 0 else 0.0
    
    def reset_stats(self, cache_key: Optional[str] = None):
        """重置缓存统计信息
        
        Args:
            cache_key: 缓存键，如果为 None 则重置所有统计信息
        """
        if cache_key is None:
            self._stats.clear()
            self._global_stats = CacheStats()
        elif cache_key in self._stats:
            self._stats[cache_key] = CacheStats()
    
    def log_stats(self, cache_key: Optional[str] = None):
        """记录缓存统计信息到日志
        
        Args:
            cache_key: 缓存键，如果为 None 则记录全局统计信息
        """
        stats = self.get_stats(cache_key)
        hit_rate = self.get_hit_rate(cache_key)
        error_rate = self.get_error_rate(cache_key)
        
        logger.info(
            f"缓存统计信息 - {'全局' if cache_key is None else f'键: {cache_key}'}\n"
            f"命中次数: {stats.hits}\n"
            f"未命中次数: {stats.misses}\n"
            f"写入次数: {stats.sets}\n"
            f"删除次数: {stats.deletes}\n"
            f"错误次数: {stats.errors}\n"
            f"命中率: {hit_rate:.2%}\n"
            f"错误率: {error_rate:.2%}\n"
            f"最后命中时间: {stats.last_hit_time}\n"
            f"最后未命中时间: {stats.last_miss_time}\n"
            f"最后写入时间: {stats.last_set_time}\n"
            f"最后错误时间: {stats.last_error_time}"
        )

# 创建全局缓存统计管理器实例
cache_stats = CacheStatsManager() 