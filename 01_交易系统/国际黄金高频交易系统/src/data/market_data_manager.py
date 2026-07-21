from typing import Dict, Any, List, Optional, Set, Callable
import asyncio
import json
import websockets
import logging
from datetime import datetime
from binance import AsyncClient, BinanceSocketManager
import MetaTrader5 as mt5

class MarketDataManager:
    """市场数据管理器"""
    
    def __init__(self,
                 binance_api_key: Optional[str] = None,
                 binance_api_secret: Optional[str] = None,
                 mt4_login: Optional[int] = None,
                 mt4_password: Optional[str] = None,
                 mt4_server: Optional[str] = None):
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret
        self.mt4_login = mt4_login
        self.mt4_password = mt4_password
        self.mt4_server = mt4_server
        
        # 初始化连接
        self.binance_client = None
        self.binance_socket_manager = None
        self.mt4_initialized = False
        
        # 存储订阅的交易对
        self.binance_symbols: Set[str] = set()
        self.mt4_symbols: Set[str] = set()
        
        # 存储WebSocket连接
        self.ws_streams: Dict[str, Any] = {}
        
        # 存储回调函数
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """初始化连接"""
        try:
            # 初始化币安连接
            if self.binance_api_key and self.binance_api_secret:
                self.binance_client = await AsyncClient.create(
                    self.binance_api_key,
                    self.binance_api_secret
                )
                self.binance_socket_manager = BinanceSocketManager(self.binance_client)
                self.logger.info("币安API连接初始化成功")
                
            # 初始化MT4连接
            if self.mt4_login and self.mt4_password and self.mt4_server:
                if not mt5.initialize():
                    raise Exception("MT4初始化失败")
                    
                # 登录MT4账户
                if not mt5.login(
                    login=self.mt4_login,
                    password=self.mt4_password,
                    server=self.mt4_server
                ):
                    raise Exception("MT4登录失败")
                    
                self.mt4_initialized = True
                self.logger.info("MT4连接初始化成功")
                
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            raise
            
    async def subscribe_binance(self, symbol: str):
        """订阅币安交易对"""
        if not self.binance_client:
            raise Exception("币安API未初始化")
            
        if symbol in self.binance_symbols:
            return
            
        try:
            # 创建K线数据流
            kline_stream = self.binance_socket_manager.kline_socket(
                symbol=symbol,
                interval='5m'
            )
            
            # 创建订单簿数据流
            depth_stream = self.binance_socket_manager.depth_socket(
                symbol=symbol
            )
            
            # 启动数据流
            await kline_stream.__aenter__()
            await depth_stream.__aenter__()
            
            # 存储数据流
            self.ws_streams[f"{symbol}_kline"] = kline_stream
            self.ws_streams[f"{symbol}_depth"] = depth_stream
            
            # 添加到已订阅列表
            self.binance_symbols.add(symbol)
            
            self.logger.info(f"成功订阅币安交易对: {symbol}")
            
        except Exception as e:
            self.logger.error(f"订阅币安交易对失败 {symbol}: {e}")
            raise
            
    async def subscribe_mt4(self, symbol: str):
        """订阅MT4交易对"""
        if not self.mt4_initialized:
            raise Exception("MT4未初始化")
            
        if symbol in self.mt4_symbols:
            return
            
        try:
            # 检查交易品种是否存在
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                raise Exception(f"MT4交易品种不存在: {symbol}")
                
            # 启用市场数据
            if not mt5.symbol_select(symbol, True):
                raise Exception(f"启用MT4市场数据失败: {symbol}")
                
            # 添加到已订阅列表
            self.mt4_symbols.add(symbol)
            
            self.logger.info(f"成功订阅MT4交易对: {symbol}")
            
        except Exception as e:
            self.logger.error(f"订阅MT4交易对失败 {symbol}: {e}")
            raise
            
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加数据回调函数"""
        self.callbacks.append(callback)
        
    async def _process_binance_kline(self, msg: Dict[str, Any]):
        """处理币安K线数据"""
        try:
            kline = msg['k']
            
            market_data = {
                'timestamp': datetime.fromtimestamp(kline['t'] / 1000),
                'symbol': kline['s'],
                'source': 'binance',
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
                'is_closed': kline['x']
            }
            
            # 调用回调函数
            for callback in self.callbacks:
                await callback(market_data)
                
        except Exception as e:
            self.logger.error(f"处理币安K线数据失败: {e}")
            
    async def _process_binance_depth(self, msg: Dict[str, Any]):
        """处理币安订单簿数据"""
        try:
            market_data = {
                'timestamp': datetime.fromtimestamp(msg['E'] / 1000),
                'symbol': msg['s'],
                'source': 'binance',
                'type': 'orderbook',
                'bids': msg['b'],
                'asks': msg['a']
            }
            
            # 调用回调函数
            for callback in self.callbacks:
                await callback(market_data)
                
        except Exception as e:
            self.logger.error(f"处理币安订单簿数据失败: {e}")
            
    async def _fetch_mt4_data(self):
        """获取MT4市场数据"""
        while True:
            try:
                for symbol in self.mt4_symbols:
                    # 获取最新价格
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1)
                    if rates is None or len(rates) == 0:
                        continue
                        
                    rate = rates[0]
                    
                    market_data = {
                        'timestamp': datetime.fromtimestamp(rate[0]),
                        'symbol': symbol,
                        'source': 'mt4',
                        'open': rate[1],
                        'high': rate[2],
                        'low': rate[3],
                        'close': rate[4],
                        'volume': rate[5],
                        'is_closed': True
                    }
                    
                    # 调用回调函数
                    for callback in self.callbacks:
                        await callback(market_data)
                        
            except Exception as e:
                self.logger.error(f"获取MT4市场数据失败: {e}")
                
            # 等待5秒
            await asyncio.sleep(5)
            
    async def start(self):
        """启动市场数据管理器"""
        try:
            # 启动MT4数据获取
            if self.mt4_initialized:
                asyncio.create_task(self._fetch_mt4_data())
                
            # 启动币安数据处理
            if self.binance_client:
                for symbol in self.binance_symbols:
                    kline_stream = self.ws_streams.get(f"{symbol}_kline")
                    depth_stream = self.ws_streams.get(f"{symbol}_depth")
                    
                    if kline_stream:
                        asyncio.create_task(self._process_binance_stream(kline_stream))
                    if depth_stream:
                        asyncio.create_task(self._process_binance_stream(depth_stream))
                        
            self.logger.info("市场数据管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动市场数据管理器失败: {e}")
            raise
            
    async def _process_binance_stream(self, stream):
        """处理币安数据流"""
        try:
            async with stream as tscm:
                while True:
                    msg = await tscm.recv()
                    if msg.get('e') == 'kline':
                        await self._process_binance_kline(msg)
                    elif msg.get('e') == 'depthUpdate':
                        await self._process_binance_depth(msg)
                        
        except Exception as e:
            self.logger.error(f"处理币安数据流失败: {e}")
            
    async def stop(self):
        """停止市场数据管理器"""
        try:
            # 关闭币安连接
            if self.binance_client:
                for stream in self.ws_streams.values():
                    await stream.__aexit__(None, None, None)
                await self.binance_client.close_connection()
                
            # 关闭MT4连接
            if self.mt4_initialized:
                mt5.shutdown()
                
            self.logger.info("市场数据管理器停止成功")
            
        except Exception as e:
            self.logger.error(f"停止市场数据管理器失败: {e}")
            raise 