from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from loguru import logger
from .base_collector import BaseDataCollector
from .binance_collector import BinanceDataCollector
from .mt4_collector import MT4DataCollector

class CollectorManager:
    """数据采集管理器"""
    
    def __init__(self, binance_api_key: str = None, binance_api_secret: str = None):
        self.binance_collector = BinanceDataCollector(binance_api_key, binance_api_secret)
        self.mt4_collector = MT4DataCollector()
        self.collectors: Dict[str, BaseDataCollector] = {
            'binance': self.binance_collector,
            'mt4': self.mt4_collector
        }
        self.running = False
        self._stop_event = asyncio.Event()
        self._callbacks = []
        
    def add_callback(self, callback):
        """添加数据回调函数"""
        self._callbacks.append(callback)
        # 为所有采集器添加回调
        for collector in self.collectors.values():
            collector.add_callback(callback)
            
    def remove_callback(self, callback):
        """移除数据回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            # 从所有采集器中移除回调
            for collector in self.collectors.values():
                collector.remove_callback(callback)
                
    async def _notify_callbacks(self, data: Dict[str, Any]):
        """通知所有回调函数"""
        for callback in self._callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
                
    async def start(self):
        """启动所有数据采集器"""
        if self.running:
            return
            
        # 连接所有采集器
        for name, collector in self.collectors.items():
            try:
                success = await collector.connect()
                if not success:
                    logger.error(f"Failed to connect {name} collector")
                    continue
            except Exception as e:
                logger.error(f"Error connecting {name} collector: {e}")
                continue
                
        self.running = True
        self._stop_event.clear()
        logger.info("All collectors started")
        
    async def stop(self):
        """停止所有数据采集器"""
        if not self.running:
            return
            
        self._stop_event.set()
        
        # 停止所有采集器
        for name, collector in self.collectors.items():
            try:
                await collector.stop()
            except Exception as e:
                logger.error(f"Error stopping {name} collector: {e}")
                
        self.running = False
        logger.info("All collectors stopped")
        
    async def subscribe_market_data(self, symbol: str, source: str = None):
        """订阅市场数据
        
        Args:
            symbol (str): 交易对符号
            source (str, optional): 数据源名称，如果为None则订阅所有数据源
        """
        if source:
            if source not in self.collectors:
                logger.error(f"Unknown data source: {source}")
                return
            await self.collectors[source].subscribe_market_data(symbol)
        else:
            for collector in self.collectors.values():
                await collector.subscribe_market_data(symbol)
                
    async def unsubscribe_market_data(self, symbol: str, source: str = None):
        """取消订阅市场数据
        
        Args:
            symbol (str): 交易对符号
            source (str, optional): 数据源名称，如果为None则取消订阅所有数据源
        """
        if source:
            if source not in self.collectors:
                logger.error(f"Unknown data source: {source}")
                return
            await self.collectors[source].unsubscribe_market_data(symbol)
        else:
            for collector in self.collectors.values():
                await collector.unsubscribe_market_data(symbol)
                
    async def fetch_market_data(self, symbol: str, source: str = None) -> Dict[str, Any]:
        """获取市场数据
        
        Args:
            symbol (str): 交易对符号
            source (str, optional): 数据源名称，如果为None则从所有数据源获取
            
        Returns:
            Dict[str, Any]: 市场数据字典
        """
        if source:
            if source not in self.collectors:
                logger.error(f"Unknown data source: {source}")
                return {}
            return await self.collectors[source].fetch_market_data(symbol)
        else:
            # 从所有数据源获取数据并合并
            all_data = {}
            for name, collector in self.collectors.items():
                data = await collector.fetch_market_data(symbol)
                if data:
                    all_data[name] = data
            return all_data
            
    async def fetch_orderbook(self, symbol: str, source: str = None) -> Dict[str, Any]:
        """获取订单簿数据
        
        Args:
            symbol (str): 交易对符号
            source (str, optional): 数据源名称，如果为None则从所有数据源获取
            
        Returns:
            Dict[str, Any]: 订单簿数据字典
        """
        if source:
            if source not in self.collectors:
                logger.error(f"Unknown data source: {source}")
                return {}
            return await self.collectors[source].fetch_orderbook(symbol)
        else:
            # 从所有数据源获取数据并合并
            all_data = {}
            for name, collector in self.collectors.items():
                data = await collector.fetch_orderbook(symbol)
                if data:
                    all_data[name] = data
            return all_data
            
    async def fetch_trades(self, symbol: str, limit: int = 100, source: str = None) -> List[Dict[str, Any]]:
        """获取最近成交数据
        
        Args:
            symbol (str): 交易对符号
            limit (int): 获取数量限制
            source (str, optional): 数据源名称，如果为None则从所有数据源获取
            
        Returns:
            List[Dict[str, Any]]: 成交数据列表
        """
        if source:
            if source not in self.collectors:
                logger.error(f"Unknown data source: {source}")
                return []
            return await self.collectors[source].fetch_trades(symbol, limit)
        else:
            # 从所有数据源获取数据并合并
            all_trades = []
            for collector in self.collectors.values():
                trades = await collector.fetch_trades(symbol, limit)
                all_trades.extend(trades)
            # 按时间排序并限制数量
            all_trades.sort(key=lambda x: x['timestamp'])
            return all_trades[-limit:] 