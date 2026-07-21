from typing import List, Optional
from datetime import datetime
from loguru import logger
from src.models.database import MarketData
from src.utils.db_manager import db_manager
from src.utils.data_validator import DataValidator
from src.utils.cache_manager import CacheManager

class MarketDataDAL:
    """市场数据访问层"""
    
    # 缓存过期时间（秒）
    CACHE_EXPIRE_TIME = 300  # 5分钟
    
    @staticmethod
    async def save_market_data(data: dict) -> bool:
        """保存单个市场数据"""
        try:
            # 验证和清理数据
            cleaned_data = DataValidator.validate_market_data(data)
            if not cleaned_data:
                return False
            
            async with db_manager.get_pg_connection() as conn:
                await conn.execute('''
                    INSERT INTO market_data (
                        time, symbol, source, open, high, low, close,
                        volume, bid_price, ask_price, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ''', cleaned_data['time'], cleaned_data['symbol'],
                    cleaned_data['source'], cleaned_data['open'],
                    cleaned_data['high'], cleaned_data['low'],
                    cleaned_data['close'], cleaned_data['volume'],
                    cleaned_data.get('bid_price'), cleaned_data.get('ask_price'),
                    cleaned_data.get('created_at', datetime.utcnow()))
                
                # 更新缓存
                await CacheManager.cache_market_data(
                    cleaned_data['symbol'],
                    cleaned_data,
                    MarketDataDAL.CACHE_EXPIRE_TIME
                )
                
                return True
        except Exception as e:
            logger.error(f"保存市场数据失败: {str(e)}")
            return False
    
    @staticmethod
    async def save_market_data_batch(data_list: List[dict]) -> bool:
        """批量保存市场数据"""
        try:
            # 验证和清理数据
            cleaned_data_list = DataValidator.clean_batch_data(
                data_list, DataValidator.validate_market_data)
            
            if not cleaned_data_list:
                return False
            
            async with db_manager.get_pg_connection() as conn:
                await conn.executemany('''
                    INSERT INTO market_data (
                        time, symbol, source, open, high, low, close,
                        volume, bid_price, ask_price, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ''', [(d['time'], d['symbol'], d['source'], d['open'],
                       d['high'], d['low'], d['close'], d['volume'],
                       d.get('bid_price'), d.get('ask_price'),
                       d.get('created_at', datetime.utcnow()))
                      for d in cleaned_data_list])
                
                # 更新缓存
                for data in cleaned_data_list:
                    await CacheManager.cache_market_data(
                        data['symbol'],
                        data,
                        MarketDataDAL.CACHE_EXPIRE_TIME
                    )
                
                return True
        except Exception as e:
            logger.error(f"批量保存市场数据失败: {str(e)}")
            return False
    
    @staticmethod
    async def get_market_data(
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        source: Optional[str] = None
    ) -> List[MarketData]:
        """获取指定时间范围内的市场数据"""
        try:
            # 尝试从缓存获取最新数据
            cached_data = await CacheManager.get_cached_market_data(symbol)
            if cached_data:
                # 检查缓存数据是否在请求的时间范围内
                if start_time <= cached_data['time'] <= end_time:
                    if not source or cached_data['source'] == source:
                        return [MarketData(**cached_data)]
            
            # 从数据库获取数据
            query = '''
                SELECT * FROM market_data
                WHERE symbol = $1 AND time BETWEEN $2 AND $3
            '''
            params = [symbol, start_time, end_time]
            
            if source:
                query += ' AND source = $4'
                params.append(source)
            
            query += ' ORDER BY time DESC'
            
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch(query, *params)
                market_data_list = [MarketData(**dict(record)) for record in records]
                
                # 更新缓存
                if market_data_list:
                    latest_data = market_data_list[0]
                    await CacheManager.cache_market_data(
                        symbol,
                        latest_data.dict(),
                        MarketDataDAL.CACHE_EXPIRE_TIME
                    )
                
                return market_data_list
        except Exception as e:
            logger.error(f"获取市场数据失败: {str(e)}")
            return []
    
    @staticmethod
    async def get_latest_market_data(
        symbol: str,
        source: Optional[str] = None
    ) -> Optional[MarketData]:
        """获取最新的市场数据"""
        try:
            # 尝试从缓存获取
            cached_data = await CacheManager.get_cached_market_data(symbol)
            if cached_data:
                if not source or cached_data['source'] == source:
                    return MarketData(**cached_data)
            
            # 从数据库获取
            query = '''
                SELECT * FROM market_data
                WHERE symbol = $1
            '''
            params = [symbol]
            
            if source:
                query += ' AND source = $2'
                params.append(source)
            
            query += ' ORDER BY time DESC LIMIT 1'
            
            async with db_manager.get_pg_connection() as conn:
                record = await conn.fetchrow(query, *params)
                if record:
                    market_data = MarketData(**dict(record))
                    # 更新缓存
                    await CacheManager.cache_market_data(
                        symbol,
                        market_data.dict(),
                        MarketDataDAL.CACHE_EXPIRE_TIME
                    )
                    return market_data
                return None
        except Exception as e:
            logger.error(f"获取最新市场数据失败: {str(e)}")
            return None
    
    @staticmethod
    async def get_market_data_by_timeframe(
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: str,
        source: Optional[str] = None
    ) -> List[MarketData]:
        """获取指定时间范围内的市场数据，按时间周期聚合"""
        try:
            # 时间周期映射
            timeframe_map = {
                '1m': '1 minute',
                '5m': '5 minutes',
                '15m': '15 minutes',
                '30m': '30 minutes',
                '1h': '1 hour',
                '4h': '4 hours',
                '1d': '1 day'
            }
            
            if timeframe not in timeframe_map:
                logger.error(f"不支持的时间周期: {timeframe}")
                return []
            
            query = '''
                SELECT 
                    date_trunc($1, time) as time,
                    symbol,
                    source,
                    first(open) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close) as close,
                    sum(volume) as volume,
                    last(bid_price) as bid_price,
                    last(ask_price) as ask_price,
                    max(created_at) as created_at
                FROM market_data
                WHERE symbol = $2 AND time BETWEEN $3 AND $4
            '''
            params = [timeframe_map[timeframe], symbol, start_time, end_time]
            
            if source:
                query += ' AND source = $5'
                params.append(source)
            
            query += '''
                GROUP BY date_trunc($1, time), symbol, source
                ORDER BY time DESC
            '''
            
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch(query, *params)
                market_data_list = [MarketData(**dict(record)) for record in records]
                
                # 更新缓存
                if market_data_list:
                    latest_data = market_data_list[0]
                    await CacheManager.cache_market_data(
                        symbol,
                        latest_data.dict(),
                        MarketDataDAL.CACHE_EXPIRE_TIME
                    )
                
                return market_data_list
        except Exception as e:
            logger.error(f"获取聚合市场数据失败: {str(e)}")
            return [] 