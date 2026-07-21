from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from loguru import logger
from src.utils.db_manager import DatabaseManager

class BaseDataCollector(ABC):
    """基础数据采集器抽象基类"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.connected = False
        self.symbols = set()
        self._stop_event = asyncio.Event()
        self._callbacks = []
        
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源
        
        Returns:
            bool: 连接是否成功
        """
        pass
        
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开数据源连接
        
        Returns:
            bool: 断开是否成功
        """
        pass
        
    @abstractmethod
    async def fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据
        
        Args:
            symbol (str): 交易对符号
            
        Returns:
            Dict[str, Any]: 市场数据字典
        """
        pass
        
    @abstractmethod
    async def fetch_orderbook(self, symbol: str) -> Dict[str, Any]:
        """获取订单簿数据
        
        Args:
            symbol (str): 交易对符号
            
        Returns:
            Dict[str, Any]: 订单簿数据字典
        """
        pass
        
    @abstractmethod
    async def fetch_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近成交数据
        
        Args:
            symbol (str): 交易对符号
            limit (int): 获取数量限制
            
        Returns:
            List[Dict[str, Any]]: 成交数据列表
        """
        pass
        
    def add_callback(self, callback):
        """添加数据回调函数
        
        Args:
            callback: 回调函数
        """
        self._callbacks.append(callback)
        
    def remove_callback(self, callback):
        """移除数据回调函数
        
        Args:
            callback: 回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            
    async def _notify_callbacks(self, data: Dict[str, Any]):
        """通知所有回调函数
        
        Args:
            data (Dict[str, Any]): 数据字典
        """
        for callback in self._callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
                
    async def subscribe_market_data(self, symbol: str):
        """订阅市场数据
        
        Args:
            symbol (str): 交易对符号
        """
        if symbol not in self.symbols:
            self.symbols.add(symbol)
            logger.info(f"Subscribed to market data for {symbol}")
            
    async def unsubscribe_market_data(self, symbol: str):
        """取消订阅市场数据
        
        Args:
            symbol (str): 交易对符号
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            logger.info(f"Unsubscribed from market data for {symbol}")
            
    async def start(self):
        """启动数据采集"""
        if not self.connected:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to data source")
                
        self._stop_event.clear()
        logger.info("Data collector started")
        
    async def stop(self):
        """停止数据采集"""
        self._stop_event.set()
        await self.disconnect()
        logger.info("Data collector stopped")
        
    async def save_market_data(self, data: Dict[str, Any]):
        """保存市场数据到数据库"""
        query = """
            INSERT INTO market_data (
                time, symbol, source, open, high, low, close,
                volume, bid_price, ask_price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            data['time'],
            data['symbol'],
            data['source'],
            data['open'],
            data['high'],
            data['low'],
            data['close'],
            data['volume'],
            data.get('bid_price'),  # 可能为空
            data.get('ask_price')   # 可能为空
        )
        
        await self.db_manager.execute_query(query, *values)
        
    async def save_market_data_batch(self, data_list: List[Dict[str, Any]]):
        """批量保存市场数据"""
        query = """
            INSERT INTO market_data (
                time, symbol, source, open, high, low, close,
                volume, bid_price, ask_price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = [
            (
                data['time'],
                data['symbol'],
                data['source'],
                data['open'],
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
                data.get('bid_price'),
                data.get('ask_price')
            )
            for data in data_list
        ]
        
        await self.db_manager.execute_many(query, values)
        
    def validate_market_data(self, data: Dict[str, Any]) -> bool:
        """验证市场数据的完整性和有效性"""
        required_fields = ['time', 'symbol', 'source', 'open', 'high', 'low', 'close', 'volume']
        
        # 检查必填字段
        if not all(field in data for field in required_fields):
            return False
            
        # 检查数值有效性
        if any(not isinstance(data[field], (int, float)) 
               for field in ['open', 'high', 'low', 'close', 'volume']):
            return False
            
        # 检查价格逻辑
        if not (data['low'] <= data['open'] <= data['high'] and 
                data['low'] <= data['close'] <= data['high']):
            return False
            
        # 检查时间有效性
        if not isinstance(data['time'], datetime):
            return False
            
        return True 