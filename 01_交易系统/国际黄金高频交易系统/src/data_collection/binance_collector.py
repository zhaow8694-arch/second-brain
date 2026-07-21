import websocket
import json
import threading
import time
from typing import Dict, List, Optional, Callable
from loguru import logger
from .base_collector import BaseDataCollector, MarketData, TradeData, OrderBookData

class BinanceDataCollector(BaseDataCollector):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        self.ws_thread = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.is_connected = False
        self.last_ping = 0
        self.ping_interval = 20  # 20秒发送一次ping
        
    def connect(self):
        """建立WebSocket连接"""
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            "wss://stream.binance.com:9443/ws",
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
            on_ping=self._on_ping,
            on_pong=self._on_pong
        )
        
        # 在新线程中运行WebSocket
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # 启动心跳检测
        self._start_heartbeat()
        
    def _start_heartbeat(self):
        """启动心跳检测"""
        def heartbeat():
            while self.is_connected:
                if time.time() - self.last_ping > self.ping_interval * 2:
                    logger.warning("No ping received, reconnecting...")
                    self.reconnect()
                time.sleep(1)
                
        heartbeat_thread = threading.Thread(target=heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
    def _on_message(self, ws, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            
            # 处理心跳响应
            if "pong" in data:
                self.last_ping = time.time()
                return
                
            # 处理订阅数据
            if "e" in data:  # 事件类型
                event_type = data["e"]
                if event_type in self.subscriptions:
                    # 转换数据格式
                    processed_data = self._process_ws_data(data)
                    # 调用所有订阅的回调函数
                    for callback in self.subscriptions[event_type]:
                        callback(processed_data)
                        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def _process_ws_data(self, data: Dict) -> Optional[Union[MarketData, TradeData, OrderBookData]]:
        """处理WebSocket数据"""
        event_type = data["e"]
        
        if event_type == "kline":
            return MarketData(
                symbol=data["s"],
                timestamp=data["k"]["t"],
                open_price=float(data["k"]["o"]),
                high_price=float(data["k"]["h"]),
                low_price=float(data["k"]["l"]),
                close_price=float(data["k"]["c"]),
                volume=float(data["k"]["v"]),
                close_time=data["k"]["T"]
            )
            
        elif event_type == "trade":
            return TradeData(
                symbol=data["s"],
                timestamp=data["T"],
                price=float(data["p"]),
                quantity=float(data["q"]),
                buyer_maker=data["m"],
                trade_id=data["t"]
            )
            
        elif event_type == "depth":
            return OrderBookData(
                symbol=data["s"],
                timestamp=data["T"],
                bids=[[float(price), float(qty)] for price, qty in data["b"]],
                asks=[[float(price), float(qty)] for price, qty in data["a"]]
            )
            
        return None
        
    def subscribe_kline(self, symbol: str, interval: str, callback: Callable):
        """订阅K线数据"""
        stream = f"{symbol.lower()}@kline_{interval}"
        self._subscribe(stream, "kline", callback)
        
    def subscribe_trade(self, symbol: str, callback: Callable):
        """订阅实时成交数据"""
        stream = f"{symbol.lower()}@trade"
        self._subscribe(stream, "trade", callback)
        
    def subscribe_depth(self, symbol: str, callback: Callable):
        """订阅深度数据"""
        stream = f"{symbol.lower()}@depth"
        self._subscribe(stream, "depth", callback)
        
    def _subscribe(self, stream: str, event_type: str, callback: Callable):
        """订阅数据流"""
        if not self.is_connected:
            self.connect()
            
        # 添加回调函数
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(callback)
        
        # 发送订阅请求
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [stream],
            "id": len(self.subscriptions)
        }
        self.ws.send(json.dumps(subscribe_message))
        
    def unsubscribe(self, stream: str, event_type: str, callback: Callable):
        """取消订阅"""
        if event_type in self.subscriptions and callback in self.subscriptions[event_type]:
            self.subscriptions[event_type].remove(callback)
            
            # 如果没有其他订阅者，发送取消订阅请求
            if not self.subscriptions[event_type]:
                unsubscribe_message = {
                    "method": "UNSUBSCRIBE",
                    "params": [stream],
                    "id": len(self.subscriptions)
                }
                self.ws.send(json.dumps(unsubscribe_message))
                
    def _on_error(self, ws, error):
        """处理WebSocket错误"""
        logger.error(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """处理WebSocket连接关闭"""
        logger.info("WebSocket connection closed")
        self.is_connected = False
        
    def _on_open(self, ws):
        """处理WebSocket连接打开"""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        self.last_ping = time.time()
        
    def _on_ping(self, ws, message):
        """处理ping消息"""
        self.ws.send(message)
        
    def _on_pong(self, ws, message):
        """处理pong消息"""
        self.last_ping = time.time()
        
    def reconnect(self):
        """重新连接WebSocket"""
        if self.ws:
            self.ws.close()
        self.connect()
        
    def close(self):
        """关闭WebSocket连接"""
        if self.ws:
            self.ws.close()
        self.is_connected = False 