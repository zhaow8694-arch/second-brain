from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.models.database import TradingSignal
from src.utils.db_manager import db_manager
from src.utils.data_validator import DataValidator
from src.utils.cache_manager import CacheManager

class TradingSignalDAL:
    """交易信号数据访问层"""
    
    # 缓存过期时间（秒）
    CACHE_EXPIRE_TIME = 300  # 5分钟
    
    @staticmethod
    async def save_trading_signal(data: dict) -> bool:
        """保存单个交易信号"""
        try:
            # 验证和清理数据
            cleaned_data = DataValidator.validate_trading_signal(data)
            if not cleaned_data:
                return False
            
            async with db_manager.get_pg_connection() as conn:
                await conn.execute('''
                    INSERT INTO trading_signals (
                        time, symbol, signal_type, direction, price,
                        confidence, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ''', cleaned_data['time'], cleaned_data['symbol'],
                    cleaned_data['signal_type'], cleaned_data['direction'],
                    cleaned_data['price'], cleaned_data['confidence'],
                    cleaned_data.get('metadata'), cleaned_data.get('created_at', datetime.utcnow()))
                
                # 更新缓存
                await CacheManager.cache_trading_signals(
                    cleaned_data['symbol'],
                    [cleaned_data],
                    TradingSignalDAL.CACHE_EXPIRE_TIME
                )
                
                return True
        except Exception as e:
            logger.error(f"保存交易信号失败: {str(e)}")
            return False
    
    @staticmethod
    async def save_trading_signals_batch(data_list: List[dict]) -> bool:
        """批量保存交易信号"""
        try:
            # 验证和清理数据
            cleaned_data_list = DataValidator.clean_batch_data(
                data_list, DataValidator.validate_trading_signal)
            
            if not cleaned_data_list:
                return False
            
            async with db_manager.get_pg_connection() as conn:
                await conn.executemany('''
                    INSERT INTO trading_signals (
                        time, symbol, signal_type, direction, price,
                        confidence, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ''', [(d['time'], d['symbol'], d['signal_type'],
                       d['direction'], d['price'], d['confidence'],
                       d.get('metadata'), d.get('created_at', datetime.utcnow()))
                      for d in cleaned_data_list])
                
                # 更新缓存
                if cleaned_data_list:
                    symbol = cleaned_data_list[0]['symbol']
                    await CacheManager.cache_trading_signals(
                        symbol,
                        cleaned_data_list,
                        TradingSignalDAL.CACHE_EXPIRE_TIME
                    )
                
                return True
        except Exception as e:
            logger.error(f"批量保存交易信号失败: {str(e)}")
            return False
    
    @staticmethod
    async def get_trading_signals(
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        signal_type: Optional[str] = None
    ) -> List[TradingSignal]:
        """获取指定时间范围内的交易信号"""
        try:
            # 尝试从缓存获取
            cached_signals = await CacheManager.get_cached_trading_signals(symbol)
            if cached_signals:
                # 过滤缓存数据
                filtered_signals = [
                    signal for signal in cached_signals
                    if start_time <= signal['time'] <= end_time
                    and (not signal_type or signal['signal_type'] == signal_type)
                ]
                if filtered_signals:
                    return [TradingSignal(**signal) for signal in filtered_signals]
            
            # 从数据库获取
            query = '''
                SELECT * FROM trading_signals
                WHERE symbol = $1 AND time BETWEEN $2 AND $3
            '''
            params = [symbol, start_time, end_time]
            
            if signal_type:
                query += ' AND signal_type = $4'
                params.append(signal_type)
            
            query += ' ORDER BY time DESC'
            
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch(query, *params)
                signals = [TradingSignal(**dict(record)) for record in records]
                
                # 更新缓存
                if signals:
                    await CacheManager.cache_trading_signals(
                        symbol,
                        [signal.dict() for signal in signals],
                        TradingSignalDAL.CACHE_EXPIRE_TIME
                    )
                
                return signals
        except Exception as e:
            logger.error(f"获取交易信号失败: {str(e)}")
            return []
    
    @staticmethod
    async def get_latest_trading_signal(
        symbol: str,
        signal_type: Optional[str] = None
    ) -> Optional[TradingSignal]:
        """获取最新的交易信号"""
        try:
            # 尝试从缓存获取
            cached_signals = await CacheManager.get_cached_trading_signals(symbol)
            if cached_signals:
                for signal in cached_signals:
                    if not signal_type or signal['signal_type'] == signal_type:
                        return TradingSignal(**signal)
            
            # 从数据库获取
            query = '''
                SELECT * FROM trading_signals
                WHERE symbol = $1
            '''
            params = [symbol]
            
            if signal_type:
                query += ' AND signal_type = $2'
                params.append(signal_type)
            
            query += ' ORDER BY time DESC LIMIT 1'
            
            async with db_manager.get_pg_connection() as conn:
                record = await conn.fetchrow(query, *params)
                if record:
                    signal = TradingSignal(**dict(record))
                    # 更新缓存
                    cached_signals = await CacheManager.get_cached_trading_signals(symbol) or []
                    cached_signals.insert(0, signal.dict())
                    await CacheManager.cache_trading_signals(
                        symbol,
                        cached_signals,
                        TradingSignalDAL.CACHE_EXPIRE_TIME
                    )
                    return signal
                return None
        except Exception as e:
            logger.error(f"获取最新交易信号失败: {str(e)}")
            return None
    
    @staticmethod
    async def get_trading_signals_by_confidence(
        symbol: str,
        min_confidence: float,
        limit: int = 100
    ) -> List[TradingSignal]:
        """获取置信度高于指定值的交易信号"""
        try:
            # 尝试从缓存获取
            cached_signals = await CacheManager.get_cached_trading_signals(symbol)
            if cached_signals:
                filtered_signals = [
                    signal for signal in cached_signals
                    if signal['confidence'] >= min_confidence
                ]
                if filtered_signals:
                    return [TradingSignal(**signal) for signal in filtered_signals[:limit]]
            
            # 从数据库获取
            async with db_manager.get_pg_connection() as conn:
                records = await conn.fetch('''
                    SELECT * FROM trading_signals
                    WHERE symbol = $1 AND confidence >= $2
                    ORDER BY confidence DESC, time DESC
                    LIMIT $3
                ''', symbol, min_confidence, limit)
                signals = [TradingSignal(**dict(record)) for record in records]
                
                # 更新缓存
                if signals:
                    await CacheManager.cache_trading_signals(
                        symbol,
                        [signal.dict() for signal in signals],
                        TradingSignalDAL.CACHE_EXPIRE_TIME
                    )
                
                return signals
        except Exception as e:
            logger.error(f"获取高置信度交易信号失败: {str(e)}")
            return [] 