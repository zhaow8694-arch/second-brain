from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.utils.db_manager import db_manager
from src.utils.cache_manager import CacheManager
from src.utils.cache_stats import cache_stats

class CacheCleaner:
    """缓存清理器"""
    
    @staticmethod
    async def clean_expired_market_data(symbols: List[str]) -> bool:
        """清理过期的市场数据缓存
        
        Args:
            symbols: 交易对列表
            
        Returns:
            是否清理成功
        """
        try:
            for symbol in symbols:
                # 获取缓存的市场数据
                cached_data = await CacheManager.get_cached_market_data(symbol)
                if cached_data:
                    # 检查数据是否过期（超过5分钟）
                    data_time = cached_data['time']
                    if datetime.utcnow() - data_time > timedelta(minutes=5):
                        await CacheManager.delete_market_data_cache(symbol)
                        logger.info(f"清理过期市场数据缓存: {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"清理过期市场数据缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def clean_expired_trading_signals(symbols: List[str]) -> bool:
        """清理过期的交易信号缓存
        
        Args:
            symbols: 交易对列表
            
        Returns:
            是否清理成功
        """
        try:
            for symbol in symbols:
                # 获取缓存的交易信号
                cached_signals = await CacheManager.get_cached_trading_signals(symbol)
                if cached_signals:
                    # 检查信号是否过期（超过5分钟）
                    current_time = datetime.utcnow()
                    valid_signals = [
                        signal for signal in cached_signals
                        if current_time - signal['time'] <= timedelta(minutes=5)
                    ]
                    
                    if len(valid_signals) < len(cached_signals):
                        if valid_signals:
                            # 更新缓存为未过期的信号
                            await CacheManager.cache_trading_signals(
                                symbol,
                                valid_signals,
                                300  # 5分钟过期
                            )
                        else:
                            # 删除缓存
                            await CacheManager.delete_trading_signals_cache(symbol)
                        logger.info(f"清理过期交易信号缓存: {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"清理过期交易信号缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def clean_expired_orders(symbols: List[str]) -> bool:
        """清理过期的订单缓存
        
        Args:
            symbols: 交易对列表
            
        Returns:
            是否清理成功
        """
        try:
            for symbol in symbols:
                # 获取缓存的订单
                cached_orders = await CacheManager.get_cached_orders(symbol)
                if cached_orders:
                    # 检查订单是否过期（已完成或取消的订单超过5分钟）
                    current_time = datetime.utcnow()
                    valid_orders = []
                    expired_order_ids = []
                    
                    for order in cached_orders:
                        if order['status'] in ('completed', 'cancelled'):
                            if current_time - order['updated_at'] > timedelta(minutes=5):
                                expired_order_ids.append(order['order_id'])
                                continue
                        valid_orders.append(order)
                    
                    if expired_order_ids:
                        # 更新订单列表缓存
                        if valid_orders:
                            await CacheManager.cache_orders(
                                symbol,
                                valid_orders,
                                300  # 5分钟过期
                            )
                        else:
                            await CacheManager.delete_orders_cache(symbol)
                        
                        # 删除过期订单的单个缓存
                        for order_id in expired_order_ids:
                            await CacheManager.delete_order_cache(order_id)
                        
                        logger.info(f"清理过期订单缓存: {symbol}, {len(expired_order_ids)}个订单")
            
            return True
        except Exception as e:
            logger.error(f"清理过期订单缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def clean_low_hit_rate_cache(min_hit_rate: float = 0.1) -> bool:
        """清理命中率低的缓存
        
        Args:
            min_hit_rate: 最小命中率阈值
            
        Returns:
            是否清理成功
        """
        try:
            # 获取所有缓存键的统计信息
            stats = cache_stats._stats
            
            for cache_key, stat in stats.items():
                hit_rate = cache_stats.get_hit_rate(cache_key)
                if hit_rate < min_hit_rate:
                    # 根据缓存键类型删除缓存
                    if 'market_data' in cache_key:
                        symbol = cache_key.split(':')[-1]
                        await CacheManager.delete_market_data_cache(symbol)
                    elif 'trading_signals' in cache_key:
                        symbol = cache_key.split(':')[-1]
                        await CacheManager.delete_trading_signals_cache(symbol)
                    elif 'orders' in cache_key:
                        if ':order:' in cache_key:
                            order_id = cache_key.split(':')[-1]
                            await CacheManager.delete_order_cache(order_id)
                        else:
                            symbol = cache_key.split(':')[-1]
                            await CacheManager.delete_orders_cache(symbol)
                    
                    logger.info(f"清理低命中率缓存: {cache_key}, 命中率: {hit_rate:.2%}")
            
            return True
        except Exception as e:
            logger.error(f"清理低命中率缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def clean_all(
        symbols: List[str],
        min_hit_rate: float = 0.1
    ) -> bool:
        """清理所有过期和低效的缓存
        
        Args:
            symbols: 交易对列表
            min_hit_rate: 最小命中率阈值
            
        Returns:
            是否清理成功
        """
        try:
            # 清理过期数据
            market_data_success = await CacheCleaner.clean_expired_market_data(symbols)
            signals_success = await CacheCleaner.clean_expired_trading_signals(symbols)
            orders_success = await CacheCleaner.clean_expired_orders(symbols)
            
            # 清理低命中率缓存
            hit_rate_success = await CacheCleaner.clean_low_hit_rate_cache(min_hit_rate)
            
            success = all([
                market_data_success,
                signals_success,
                orders_success,
                hit_rate_success
            ])
            
            if success:
                logger.info("所有缓存清理成功")
            else:
                logger.warning("部分缓存清理失败")
            
            return success
        except Exception as e:
            logger.error(f"清理所有缓存失败: {str(e)}")
            return False

# 创建全局缓存清理器实例
cache_cleaner = CacheCleaner() 