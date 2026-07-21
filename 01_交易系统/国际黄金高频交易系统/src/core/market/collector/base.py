from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class DataType(Enum):
    """数据类型枚举"""
    KLINE = "kline"           # K线数据
    TICK = "tick"            # 实时行情
    ORDERBOOK = "orderbook"   # 订单簿
    TRADE = "trade"          # 成交记录
    FUNDING_RATE = "funding_rate"  # 资金费率

@dataclass
class MarketData:
    """市场数据基类"""
    symbol: str
    data_type: DataType
    timestamp: datetime
    source: str
    raw_data: Dict[str, Any]

@dataclass
class KlineData(MarketData):
    """K线数据"""
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    interval: str

@dataclass
class TickData(MarketData):
    """实时行情数据"""
    last_price: float
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float
    volume_24h: float

@dataclass
class OrderBookData(MarketData):
    """订单簿数据"""
    bids: List[tuple]  # [(price, volume), ...]
    asks: List[tuple]  # [(price, volume), ...]
    depth: int

@dataclass
class TradeData(MarketData):
    """成交记录数据"""
    price: float
    volume: float
    side: str  # buy/sell
    order_id: str

@dataclass
class FundingRateData(MarketData):
    """资金费率数据"""
    rate: float
    next_funding_time: datetime

class BaseCollector(ABC):
    """数据采集器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.subscribers = []
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开数据源连接"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbol: str, data_type: DataType) -> bool:
        """订阅数据"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, symbol: str, data_type: DataType) -> bool:
        """取消订阅数据"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: datetime,
        interval: Optional[str] = None
    ) -> List[MarketData]:
        """获取历史数据"""
        pass
    
    def add_subscriber(self, callback):
        """添加数据订阅者"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
    
    def remove_subscriber(self, callback):
        """移除数据订阅者"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    async def notify_subscribers(self, data: MarketData):
        """通知所有订阅者"""
        for subscriber in self.subscribers:
            try:
                await subscriber(data)
            except Exception as e:
                print(f"Error notifying subscriber: {str(e)}")
    
    async def start(self):
        """启动数据采集"""
        if not self.is_running:
            self.is_running = True
            await self.connect()
    
    async def stop(self):
        """停止数据采集"""
        if self.is_running:
            self.is_running = False
            await self.disconnect() 