from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
import json
from loguru import logger

from src.utils.db_manager import db_manager

class CacheManager:
    """缓存管理器"""
    
    # 缓存键前缀
    MARKET_DATA_PREFIX = "market_data:"
    TRADING_SIGNAL_PREFIX = "trading_signal:"
    ORDER_PREFIX = "order:"
    
    # 默认缓存时间（秒）
    DEFAULT_EXPIRE_TIME = 3600  # 1小时
    
    @staticmethod
    async def set_cache(
        key: str,
        value: Any,
        expire_time: int = DEFAULT_EXPIRE_TIME
    ) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_time: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            
            # 设置缓存
            await db_manager.set_cache(key, value, expire_time)
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def get_cache(key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回 None
        """
        try:
            value = await db_manager.get_cache(key)
            if value is None:
                return None
            
            # 尝试反序列化
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
            
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None
    
    @staticmethod
    async def delete_cache(key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            await db_manager.delete_cache(key)
            return True
            
        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def clear_cache() -> bool:
        """清空所有缓存
        
        Returns:
            是否清空成功
        """
        try:
            await db_manager.clear_cache()
            return True
            
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def cache_market_data(
        symbol: str,
        data: Dict[str, Any],
        expire_time: int = DEFAULT_EXPIRE_TIME
    ) -> bool:
        """缓存市场数据
        
        Args:
            symbol: 交易对
            data: 市场数据
            expire_time: 过期时间（秒）
            
        Returns:
            是否缓存成功
        """
        key = f"{CacheManager.MARKET_DATA_PREFIX}{symbol}"
        return await CacheManager.set_cache(key, data, expire_time)
    
    @staticmethod
    async def get_cached_market_data(symbol: str) -> Optional[Dict[str, Any]]:
        """获取缓存的市场数据
        
        Args:
            symbol: 交易对
            
        Returns:
            市场数据，如果不存在则返回 None
        """
        key = f"{CacheManager.MARKET_DATA_PREFIX}{symbol}"
        return await CacheManager.get_cache(key)
    
    @staticmethod
    async def cache_trading_signals(
        symbol: str,
        signals: List[Dict[str, Any]],
        expire_time: int = DEFAULT_EXPIRE_TIME
    ) -> bool:
        """缓存交易信号
        
        Args:
            symbol: 交易对
            signals: 交易信号列表
            expire_time: 过期时间（秒）
            
        Returns:
            是否缓存成功
        """
        key = f"{CacheManager.TRADING_SIGNAL_PREFIX}{symbol}"
        return await CacheManager.set_cache(key, signals, expire_time)
    
    @staticmethod
    async def get_cached_trading_signals(symbol: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的交易信号
        
        Args:
            symbol: 交易对
            
        Returns:
            交易信号列表，如果不存在则返回 None
        """
        key = f"{CacheManager.TRADING_SIGNAL_PREFIX}{symbol}"
        return await CacheManager.get_cache(key)
    
    @staticmethod
    async def cache_order(
        order_id: str,
        order: Dict[str, Any],
        expire_time: int = DEFAULT_EXPIRE_TIME
    ) -> bool:
        """缓存订单
        
        Args:
            order_id: 订单ID
            order: 订单数据
            expire_time: 过期时间（秒）
            
        Returns:
            是否缓存成功
        """
        key = f"{CacheManager.ORDER_PREFIX}{order_id}"
        return await CacheManager.set_cache(key, order, expire_time)
    
    @staticmethod
    async def get_cached_order(order_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单数据，如果不存在则返回 None
        """
        key = f"{CacheManager.ORDER_PREFIX}{order_id}"
        return await CacheManager.get_cache(key)
    
    @staticmethod
    async def cache_active_orders(
        symbol: str,
        orders: List[Dict[str, Any]],
        expire_time: int = DEFAULT_EXPIRE_TIME
    ) -> bool:
        """缓存活跃订单
        
        Args:
            symbol: 交易对
            orders: 活跃订单列表
            expire_time: 过期时间（秒）
            
        Returns:
            是否缓存成功
        """
        key = f"{CacheManager.ORDER_PREFIX}active:{symbol}"
        return await CacheManager.set_cache(key, orders, expire_time)
    
    @staticmethod
    async def get_cached_active_orders(symbol: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的活跃订单
        
        Args:
            symbol: 交易对
            
        Returns:
            活跃订单列表，如果不存在则返回 None
        """
        key = f"{CacheManager.ORDER_PREFIX}active:{symbol}"
        return await CacheManager.get_cache(key) 