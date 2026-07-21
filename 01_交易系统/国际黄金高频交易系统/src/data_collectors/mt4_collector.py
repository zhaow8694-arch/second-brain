from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import MetaTrader5 as mt5
from loguru import logger
from src.data_collectors.base_collector import BaseDataCollector

class MT4DataCollector(BaseDataCollector):
    """MT4数据采集器"""
    
    def __init__(self):
        super().__init__()
        self.connected = False
        self.symbols = set()
        self._stop_event = asyncio.Event()
        
    async def connect(self) -> bool:
        """连接到MT4终端"""
        try:
            if not mt5.initialize():
                logger.error("MT4 initialization failed")
                return False
                
            # 获取账户信息
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
                
            self.connected = True
            logger.info(f"Connected to MT4 account: {account_info.login}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MT4: {e}")
            return False
            
    async def disconnect(self) -> bool:
        """断开MT4连接"""
        try:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT4")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from MT4: {e}")
            return False
            
    async def fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据"""
        try:
            # 获取当前价格
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {}
                
            # 获取K线数据
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
            if rates is None or len(rates) == 0:
                return {}
                
            rate = rates[0]
            
            return {
                'symbol': symbol,
                'price': tick.last,
                'volume': rate[5],
                'bid_price': tick.bid,
                'ask_price': tick.ask,
                'timestamp': datetime.fromtimestamp(rate[0]),
                'open': rate[1],
                'high': rate[2],
                'low': rate[3],
                'close': rate[4]
            }
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            return {}
            
    async def fetch_orderbook(self, symbol: str) -> Dict[str, Any]:
        """获取订单簿数据"""
        try:
            # MT4不直接提供订单簿数据，我们使用当前价格和深度信息
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {}
                
            # 获取深度信息
            depth = mt5.symbol_info(symbol)
            if depth is None:
                return {}
                
            return {
                'symbol': symbol,
                'bids': [[tick.bid, depth.volume_min]],
                'asks': [[tick.ask, depth.volume_min]],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to fetch orderbook for {symbol}: {e}")
            return {}
            
    async def fetch_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近成交数据"""
        try:
            # 获取历史交易数据
            history = mt5.history_deals_get(
                datetime.now().timestamp() - 3600,  # 最近1小时
                datetime.now().timestamp()
            )
            
            if history is None:
                return []
                
            # 过滤指定交易对的数据
            trades = [
                deal for deal in history
                if deal.symbol == symbol
            ][-limit:]
            
            return [{
                'symbol': trade.symbol,
                'price': trade.price,
                'quantity': trade.volume,
                'timestamp': datetime.fromtimestamp(trade.time),
                'is_buyer_maker': trade.type == mt5.DEAL_TYPE_BUY
            } for trade in trades]
        except Exception as e:
            logger.error(f"Failed to fetch trades for {symbol}: {e}")
            return []
            
    async def _start_market_data_stream(self, symbol: str):
        """启动市场数据流"""
        try:
            while not self._stop_event.is_set():
                data = await self.fetch_market_data(symbol)
                if data:
                    await self._notify_callbacks(data)
                await asyncio.sleep(1)  # 每秒更新一次
        except Exception as e:
            logger.error(f"Error in market data stream for {symbol}: {e}")
            
    async def subscribe_market_data(self, symbol: str):
        """订阅市场数据"""
        await super().subscribe_market_data(symbol)
        if symbol not in self.ws_streams:
            self.ws_streams[symbol] = asyncio.create_task(
                self._start_market_data_stream(symbol)
            )
            
    async def unsubscribe_market_data(self, symbol: str):
        """取消订阅市场数据"""
        await super().unsubscribe_market_data(symbol)
        if symbol in self.ws_streams:
            self.ws_streams[symbol].cancel()
            del self.ws_streams[symbol]
            
    async def stop(self):
        """停止数据采集"""
        for symbol in list(self.ws_streams.keys()):
            await self.unsubscribe_market_data(symbol)
        await super().stop()
        
    async def start_symbol_monitoring(self, symbol: str):
        """开始监控特定交易对"""
        if not self.connected:
            await self.connect()
            
        self.symbols.add(symbol)
        
        while not self._stop_event.is_set():
            try:
                data = await self.fetch_market_data(symbol)
                if data and self.validate_market_data(data):
                    await self.save_market_data(data)
                    
            except Exception as e:
                print(f"Error monitoring {symbol}: {str(e)}")
                
            await asyncio.sleep(1)  # 每秒更新一次数据
            
    async def stop_symbol_monitoring(self, symbol: str):
        """停止监控特定交易对"""
        self.symbols.remove(symbol)
        
    async def start_monitoring(self, symbols: list):
        """开始监控多个交易对"""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.start_symbol_monitoring(symbol))
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        
    def get_available_symbols(self) -> list:
        """获取可用的交易对列表"""
        if not self.connected:
            raise Exception("MT4 not connected")
            
        symbols = mt5.symbols_get()
        return [symbol.name for symbol in symbols] 