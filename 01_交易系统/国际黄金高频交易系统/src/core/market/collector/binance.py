import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.exceptions import BinanceAPIException
from loguru import logger

from .base import (
    BaseCollector,
    DataType,
    MarketData,
    KlineData,
    TickData,
    OrderBookData,
    TradeData,
    FundingRateData
)

class BinanceCollector(BaseCollector):
    """Binance数据采集器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.bm = None
        self.subscriptions = {}
        self.websocket_tasks = []
    
    async def connect(self) -> bool:
        """连接到Binance"""
        try:
            self.client = Client(
                self.config['api_key'],
                self.config['api_secret']
            )
            self.bm = BinanceSocketManager(self.client)
            logger.info("Successfully connected to Binance")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """断开Binance连接"""
        try:
            if self.bm:
                self.bm.stop()
            if self.client:
                self.client.close_connection()
            logger.info("Successfully disconnected from Binance")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Binance: {str(e)}")
            return False
    
    async def subscribe(self, symbol: str, data_type: DataType) -> bool:
        """订阅Binance数据"""
        try:
            if symbol not in self.subscriptions:
                self.subscriptions[symbol] = set()
            
            if data_type not in self.subscriptions[symbol]:
                self.subscriptions[symbol].add(data_type)
                
                if data_type == DataType.KLINE:
                    task = asyncio.create_task(
                        self._handle_kline_stream(symbol)
                    )
                    self.websocket_tasks.append(task)
                elif data_type == DataType.TICK:
                    task = asyncio.create_task(
                        self._handle_ticker_stream(symbol)
                    )
                    self.websocket_tasks.append(task)
                elif data_type == DataType.TRADE:
                    task = asyncio.create_task(
                        self._handle_trade_stream(symbol)
                    )
                    self.websocket_tasks.append(task)
                
                logger.info(f"Successfully subscribed to {symbol} {data_type.value}")
                return True
                
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol} {data_type.value}: {str(e)}")
            return False
    
    async def unsubscribe(self, symbol: str, data_type: DataType) -> bool:
        """取消订阅Binance数据"""
        try:
            if symbol in self.subscriptions:
                if data_type in self.subscriptions[symbol]:
                    self.subscriptions[symbol].remove(data_type)
                    logger.info(f"Successfully unsubscribed from {symbol} {data_type.value}")
                    return True
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {symbol} {data_type.value}: {str(e)}")
            return False
    
    async def get_historical_data(
        self,
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: datetime,
        interval: Optional[str] = None
    ) -> List[MarketData]:
        """获取Binance历史数据"""
        try:
            if data_type == DataType.KLINE:
                if not interval:
                    interval = '1h'
                
                klines = self.client.get_historical_klines(
                    symbol,
                    interval,
                    start_time.strftime("%d %b %Y %H:%M:%S"),
                    end_time.strftime("%d %b %Y %H:%M:%S")
                )
                
                return [
                    KlineData(
                        symbol=symbol,
                        data_type=DataType.KLINE,
                        timestamp=datetime.fromtimestamp(kline[0] / 1000),
                        source='binance',
                        raw_data={'kline': kline},
                        open_price=float(kline[1]),
                        high_price=float(kline[2]),
                        low_price=float(kline[3]),
                        close_price=float(kline[4]),
                        volume=float(kline[5]),
                        interval=interval
                    )
                    for kline in klines
                ]
            
            elif data_type == DataType.TRADE:
                trades = self.client.get_historical_trades(
                    symbol=symbol,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000)
                )
                
                return [
                    TradeData(
                        symbol=symbol,
                        data_type=DataType.TRADE,
                        timestamp=datetime.fromtimestamp(trade['time'] / 1000),
                        source='binance',
                        raw_data={'trade': trade},
                        price=float(trade['price']),
                        volume=float(trade['qty']),
                        side=trade['isBuyerMaker'] and 'sell' or 'buy',
                        order_id=str(trade['id'])
                    )
                    for trade in trades
                ]
            
            return []
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            return []
    
    async def _handle_kline_stream(self, symbol: str):
        """处理K线数据流"""
        try:
            conn_key = self.bm.start_kline_socket(
                symbol.lower(),
                self._process_kline_message
            )
            self.bm.start()
            
            while self.is_running:
                await asyncio.sleep(1)
            
            self.bm.stop_socket(conn_key)
            
        except Exception as e:
            logger.error(f"Error in kline stream handler: {str(e)}")
    
    async def _handle_ticker_stream(self, symbol: str):
        """处理实时行情数据流"""
        try:
            conn_key = self.bm.start_symbol_ticker_socket(
                symbol.lower(),
                self._process_ticker_message
            )
            self.bm.start()
            
            while self.is_running:
                await asyncio.sleep(1)
            
            self.bm.stop_socket(conn_key)
            
        except Exception as e:
            logger.error(f"Error in ticker stream handler: {str(e)}")
    
    async def _handle_trade_stream(self, symbol: str):
        """处理成交记录数据流"""
        try:
            conn_key = self.bm.start_trade_socket(
                symbol.lower(),
                self._process_trade_message
            )
            self.bm.start()
            
            while self.is_running:
                await asyncio.sleep(1)
            
            self.bm.stop_socket(conn_key)
            
        except Exception as e:
            logger.error(f"Error in trade stream handler: {str(e)}")
    
    def _process_kline_message(self, msg):
        """处理K线消息"""
        if msg['e'] == 'kline':
            kline = msg['k']
            data = KlineData(
                symbol=kline['s'],
                data_type=DataType.KLINE,
                timestamp=datetime.fromtimestamp(kline['t'] / 1000),
                source='binance',
                raw_data={'kline': kline},
                open_price=float(kline['o']),
                high_price=float(kline['h']),
                low_price=float(kline['l']),
                close_price=float(kline['c']),
                volume=float(kline['v']),
                interval=kline['i']
            )
            asyncio.create_task(self.notify_subscribers(data))
    
    def _process_ticker_message(self, msg):
        """处理实时行情消息"""
        if msg['e'] == 'ticker':
            ticker = msg['t']
            data = TickData(
                symbol=ticker['s'],
                data_type=DataType.TICK,
                timestamp=datetime.fromtimestamp(ticker['E'] / 1000),
                source='binance',
                raw_data={'ticker': ticker},
                last_price=float(ticker['c']),
                bid_price=float(ticker['b']),
                ask_price=float(ticker['a']),
                bid_volume=float(ticker['B']),
                ask_volume=float(ticker['A']),
                volume_24h=float(ticker['v'])
            )
            asyncio.create_task(self.notify_subscribers(data))
    
    def _process_trade_message(self, msg):
        """处理成交记录消息"""
        if msg['e'] == 'trade':
            trade = msg['t']
            data = TradeData(
                symbol=trade['s'],
                data_type=DataType.TRADE,
                timestamp=datetime.fromtimestamp(trade['T'] / 1000),
                source='binance',
                raw_data={'trade': trade},
                price=float(trade['p']),
                volume=float(trade['q']),
                side=trade['m'] and 'sell' or 'buy',
                order_id=str(trade['t'])
            )
            asyncio.create_task(self.notify_subscribers(data)) 