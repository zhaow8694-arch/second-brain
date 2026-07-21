from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.utils.db_manager import db_manager
from src.utils.cache_manager import CacheManager
from src.models.database import MarketData, TradingSignal, Order

class CacheWarmer:
    """缓存预热器"""
    
    @staticmethod
    async def warm_market_data(
        symbols: List[str],
        lookback_minutes: int = 60
    ) -> bool:
        """预热市场数据缓存
        
        Args:
            symbols: 交易对列表
            lookback_minutes: 回溯时间（分钟）
            
        Returns:
            是否预热成功
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=lookback_minutes)
            
            for symbol in symbols:
                async with db_manager.get_pg_connection() as conn:
                    # 获取最新市场数据
                    records = await conn.fetch('''
                        SELECT * FROM market_data
                        WHERE symbol = $1 AND time BETWEEN $2 AND $3
                        ORDER BY time DESC
                    ''', symbol, start_time, end_time)
                    
                    if records:
                        market_data_list = [dict(record) for record in records]
                        # 缓存数据
                        await CacheManager.cache_market_data(
                            symbol,
                            market_data_list[0],  # 最新数据
                            300  # 5分钟过期
                        )
                        logger.info(f"预热市场数据缓存成功: {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"预热市场数据缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def warm_trading_signals(
        symbols: List[str],
        lookback_minutes: int = 60
    ) -> bool:
        """预热交易信号缓存
        
        Args:
            symbols: 交易对列表
            lookback_minutes: 回溯时间（分钟）
            
        Returns:
            是否预热成功
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=lookback_minutes)
            
            for symbol in symbols:
                async with db_manager.get_pg_connection() as conn:
                    # 获取最近的交易信号
                    records = await conn.fetch('''
                        SELECT * FROM trading_signals
                        WHERE symbol = $1 AND time BETWEEN $2 AND $3
                        ORDER BY time DESC
                    ''', symbol, start_time, end_time)
                    
                    if records:
                        signal_list = [dict(record) for record in records]
                        # 缓存数据
                        await CacheManager.cache_trading_signals(
                            symbol,
                            signal_list,
                            300  # 5分钟过期
                        )
                        logger.info(f"预热交易信号缓存成功: {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"预热交易信号缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def warm_active_orders(symbols: List[str]) -> bool:
        """预热活跃订单缓存
        
        Args:
            symbols: 交易对列表
            
        Returns:
            是否预热成功
        """
        try:
            for symbol in symbols:
                async with db_manager.get_pg_connection() as conn:
                    # 获取活跃订单
                    records = await conn.fetch('''
                        SELECT * FROM orders
                        WHERE symbol = $1 AND status IN ('pending', 'open')
                        ORDER BY time DESC
                    ''', symbol)
                    
                    if records:
                        order_list = [dict(record) for record in records]
                        # 缓存订单列表
                        await CacheManager.cache_orders(
                            symbol,
                            order_list,
                            300  # 5分钟过期
                        )
                        
                        # 缓存单个订单
                        for order in order_list:
                            await CacheManager.cache_order(
                                order['order_id'],
                                order,
                                300  # 5分钟过期
                            )
                        
                        logger.info(f"预热活跃订单缓存成功: {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"预热活跃订单缓存失败: {str(e)}")
            return False
    
    @staticmethod
    async def warm_all(
        symbols: List[str],
        lookback_minutes: int = 60
    ) -> bool:
        """预热所有缓存
        
        Args:
            symbols: 交易对列表
            lookback_minutes: 回溯时间（分钟）
            
        Returns:
            是否预热成功
        """
        try:
            # 预热市场数据
            market_data_success = await CacheWarmer.warm_market_data(
                symbols, lookback_minutes)
            
            # 预热交易信号
            signals_success = await CacheWarmer.warm_trading_signals(
                symbols, lookback_minutes)
            
            # 预热活跃订单
            orders_success = await CacheWarmer.warm_active_orders(symbols)
            
            success = all([
                market_data_success,
                signals_success,
                orders_success
            ])
            
            if success:
                logger.info("所有缓存预热成功")
            else:
                logger.warning("部分缓存预热失败")
            
            return success
        except Exception as e:
            logger.error(f"预热所有缓存失败: {str(e)}")
            return False

# 创建全局缓存预热器实例
cache_warmer = CacheWarmer() 