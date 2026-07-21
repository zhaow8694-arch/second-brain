from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.models.database import Order
from src.utils.db_manager import db_manager
from src.utils.data_validator import DataValidator
from src.utils.cache_manager import CacheManager

class OrderDAL:
    """订单数据访问层"""
    
    # 缓存过期时间（秒）
    CACHE_EXPIRE_TIME = 300  # 5分钟
    
    @staticmethod
    async def save_order(data: dict) -> bool:
        """保存单个订单"""
        try:
            # 验证和清理数据
            cleaned_data = DataValidator.validate_order(data)
            if not cleaned_data:
                return False
            
            async with db_manager.get_pg_connection() as conn:
                await conn.execute('''
                    INSERT INTO orders (
                        order_id, time, symbol, order_type, direction,
                        price, volume, status, signal_id, metadata,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ''', cleaned_data['order_id'], cleaned_data['time'],
                    cleaned_data['symbol'], cleaned_data['order_type'],
                    cleaned_data['direction'], cleaned_data['price'],
                    cleaned_data['volume'], cleaned_data['status'],
                    cleaned_data.get('signal_id'), cleaned_data.get('metadata'),
                    cleaned_data.get('created_at', datetime.utcnow()),
                    cleaned_data.get('updated_at', datetime.utcnow()))
                
                # 更新缓存
                await CacheManager.cache_orders(
                    cleaned_data['symbol'],
                    [cleaned_data],
                    OrderDAL.CACHE_EXPIRE_TIME
                )
                
                # 更新单个订单缓存
                await CacheManager.cache_order(
                    cleaned_data['order_id'],
                    cleaned_data,
                    OrderDAL.CACHE_EXPIRE_TIME
                )
                
                return True
        except Exception as e:
            logger.error(f"保存订单失败: {str(e)}")
            return False
    
    @staticmethod
    async def save_orders_batch(data_list: List[dict]) -> bool:
        """批量保存订单"""
        try:
            # 验证和清理数据
            cleaned_data_list = DataValidator.clean_batch_data(
                data_list, DataValidator.validate_order)
            
            if not cleaned_data_list:
                return False
            
            async with db_manager.get_pg_connection() as conn:
                await conn.executemany('''
                    INSERT INTO orders (
                        order_id, time, symbol, order_type, direction,
                        price, volume, status, signal_id, metadata,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ''', [(d['order_id'], d['time'], d['symbol'],
                       d['order_type'], d['direction'], d['price'],
                       d['volume'], d['status'], d.get('signal_id'),
                       d.get('metadata'), d.get('created_at', datetime.utcnow()),
                       d.get('updated_at', datetime.utcnow()))
                      for d in cleaned_data_list])
                
                # 按交易对分组更新缓存
                symbol_orders = {}
                for data in cleaned_data_list:
                    symbol = data['symbol']
                    if symbol not in symbol_orders:
                        symbol_orders[symbol] = []
                    symbol_orders[symbol].append(data)
                
                for symbol, orders in symbol_orders.items():
                    await CacheManager.cache_orders(
                        symbol,
                        orders,
                        OrderDAL.CACHE_EXPIRE_TIME
                    )
                
                # 更新单个订单缓存
                for data in cleaned_data_list:
                    await CacheManager.cache_order(
                        data['order_id'],
                        data,
                        OrderDAL.CACHE_EXPIRE_TIME
                    )
                
                return True
        except Exception as e:
            logger.error(f"批量保存订单失败: {str(e)}")
            return False
    
    @staticmethod
    async def update_order_status(
        order_id: str,
        status: str,
        updated_at: datetime = None
    ) -> bool:
        """更新订单状态"""
        try:
            if updated_at is None:
                updated_at = datetime.utcnow()
                
            async with db_manager.get_pg_connection() as conn:
                # 先获取订单信息
                record = await conn.fetchrow('''
                    SELECT * FROM orders WHERE order_id = $1
                ''', order_id)
                
                if not record:
                    return False
                
                # 更新状态
                await conn.execute('''
                    UPDATE orders
                    SET status = $1, updated_at = $2
                    WHERE order_id = $3
                ''', status, updated_at, order_id)
                
                # 更新缓存
                order_data = dict(record)
                order_data['status'] = status
                order_data['updated_at'] = updated_at
                
                await CacheManager.cache_order(
                    order_id,
                    order_data,
                    OrderDAL.CACHE_EXPIRE_TIME
                )
                
                # 更新交易对订单列表缓存
                symbol = order_data['symbol']
                cached_orders = await CacheManager.get_cached_orders(symbol) or []
                for i, order in enumerate(cached_orders):
                    if order['order_id'] == order_id:
                        cached_orders[i] = order_data
                        break
                await CacheManager.cache_orders(
                    symbol,
                    cached_orders,
                    OrderDAL.CACHE_EXPIRE_TIME
                )
                
                return True
        except Exception as e:
            logger.error(f"更新订单状态失败: {str(e)}")
            return False
    
    @staticmethod
    async def get_order(order_id: str) -> Optional[Order]:
        """获取指定订单"""
        try:
            # 尝试从缓存获取
            cached_order = await CacheManager.get_cached_order(order_id)
            if cached_order:
                return Order(**cached_order)
            
            # 从数据库获取
            async with db_manager.get_pg_connection() as conn:
                record = await conn.fetchrow('''
                    SELECT * FROM orders WHERE order_id = $1
                ''', order_id)
                
                if record:
                    order_data = dict(record)
                    # 更新缓存
                    await CacheManager.cache_order(
                        order_id,
                        order_data,
                        OrderDAL.CACHE_EXPIRE_TIME
                    )
                    return Order(**order_data)
                return None
        except Exception as e:
            logger.error(f"获取订单失败: {str(e)}")
            return None
    
    @staticmethod
    async def get_orders(
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        status: Optional[str] = None
    ) -> List[Order]:
        """获取指定时间范围内的订单"""
        try:
            # 尝试从缓存获取
            cached_orders = await CacheManager.get_cached_orders(symbol)
            if cached_orders:
                # 过滤缓存数据
                filtered_orders = [
                    order for order in cached_orders
                    if start_time <= order['time'] <= end_time
                    and (not status or order['status'] == status)
                ]
                if filtered_orders:
                    return [Order(**order) for order in filtered_orders]
            
            # 从数据库获取
            query = '''
                SELECT * FROM orders
                WHERE symbol = $1 AND time BETWEEN $2 AND $3
            '''
            params = [symbol, start_time, end_time]
            
            if status:
                query += ' AND status = $4'
                params.append(status)
            
            query += ' ORDER BY time DESC'
            
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch(query, *params)
                orders = [Order(**dict(record)) for record in records]
                
                # 更新缓存
                if orders:
                    await CacheManager.cache_orders(
                        symbol,
                        [order.dict() for order in orders],
                        OrderDAL.CACHE_EXPIRE_TIME
                    )
                
                return orders
        except Exception as e:
            logger.error(f"获取订单列表失败: {str(e)}")
            return []
    
    @staticmethod
    async def get_orders_by_signal(signal_id: int) -> List[Order]:
        """获取与指定信号相关的订单"""
        try:
            # 从数据库获取
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch('''
                    SELECT * FROM orders
                    WHERE signal_id = $1
                    ORDER BY time DESC
                ''', signal_id)
                
                orders = [Order(**dict(record)) for record in records]
                
                # 按交易对分组更新缓存
                symbol_orders = {}
                for order in orders:
                    symbol = order.symbol
                    if symbol not in symbol_orders:
                        symbol_orders[symbol] = []
                    symbol_orders[symbol].append(order.dict())
                
                for symbol, symbol_order_list in symbol_orders.items():
                    await CacheManager.cache_orders(
                        symbol,
                        symbol_order_list,
                        OrderDAL.CACHE_EXPIRE_TIME
                    )
                
                return orders
        except Exception as e:
            logger.error(f"获取信号相关订单失败: {str(e)}")
            return []
    
    @staticmethod
    async def get_active_orders(symbol: str) -> List[Order]:
        """获取活跃订单"""
        try:
            # 尝试从缓存获取
            cached_orders = await CacheManager.get_cached_orders(symbol)
            if cached_orders:
                # 过滤活跃订单
                active_orders = [
                    order for order in cached_orders
                    if order['status'] in ('pending', 'open')
                ]
                if active_orders:
                    return [Order(**order) for order in active_orders]
            
            # 从数据库获取
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch('''
                    SELECT * FROM orders
                    WHERE symbol = $1 AND status IN ('pending', 'open')
                    ORDER BY time DESC
                ''', symbol)
                
                orders = [Order(**dict(record)) for record in records]
                
                # 更新缓存
                if orders:
                    await CacheManager.cache_orders(
                        symbol,
                        [order.dict() for order in orders],
                        OrderDAL.CACHE_EXPIRE_TIME
                    )
                
                return orders
        except Exception as e:
            logger.error(f"获取活跃订单失败: {str(e)}")
            return [] 