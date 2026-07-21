from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from binance.client import AsyncClient
from binance.streams import BinanceSocketManager
from loguru import logger
from .base_collector import BaseDataCollector

class BinanceDataCollector(BaseDataCollector):
    """币安数据采集器"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        self.bm = None
        self.ws_streams = {}
        
    async def connect(self) -> bool:
        """连接到币安API"""
        try:
            self.client = await AsyncClient.create(self.api_key, self.api_secret)
            self.bm = BinanceSocketManager(self.client)
            self.connected = True
            logger.info("Connected to Binance API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance API: {e}")
            return False
            
    async def disconnect(self) -> bool:
        """断开币安API连接"""
        try:
            if self.bm:
                await self.bm.close()
            if self.client:
                await self.client.close_connection()
            self.connected = False
            logger.info("Disconnected from Binance API")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Binance API: {e}")
            return False
            
    async def fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据"""
        try:
            ticker = await self.client.get_ticker(symbol=symbol)
            return {
                'symbol': symbol,
                'price': float(ticker['lastPrice']),
                'volume': float(ticker['volume']),
                'bid_price': float(ticker['bidPrice']),
                'ask_price': float(ticker['askPrice']),
                'timestamp': datetime.fromtimestamp(ticker['closeTime'] / 1000)
            }
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            return {}
            
    async def fetch_orderbook(self, symbol: str) -> Dict[str, Any]:
        """获取订单簿数据"""
        try:
            depth = await self.client.get_order_book(symbol=symbol)
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
                'timestamp': datetime.fromtimestamp(depth['lastUpdateId'] / 1000)
            }
        except Exception as e:
            logger.error(f"Failed to fetch orderbook for {symbol}: {e}")
            return {}
            
    async def fetch_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近成交数据"""
        try:
            trades = await self.client.get_recent_trades(symbol=symbol, limit=limit)
            return [{
                'symbol': symbol,
                'price': float(trade['price']),
                'quantity': float(trade['qty']),
                'timestamp': datetime.fromtimestamp(trade['time'] / 1000),
                'is_buyer_maker': trade['isBuyerMaker']
            } for trade in trades]
        except Exception as e:
            logger.error(f"Failed to fetch trades for {symbol}: {e}")
            return []
            
    async def _start_market_data_stream(self, symbol: str):
        """启动市场数据流"""
        try:
            stream = self.bm.trade_socket(symbol)
            async with stream as tscm:
                while not self._stop_event.is_set():
                    msg = await tscm.recv()
                    if msg:
                        data = {
                            'symbol': msg['s'],
                            'price': float(msg['p']),
                            'quantity': float(msg['q']),
                            'timestamp': datetime.fromtimestamp(msg['T'] / 1000),
                            'is_buyer_maker': msg['m']
                        }
                        await self._notify_callbacks(data)
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