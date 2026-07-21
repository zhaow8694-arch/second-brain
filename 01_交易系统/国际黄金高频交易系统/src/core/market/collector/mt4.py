import asyncio
import os
import csv
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
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

class MT4Collector(BaseCollector):
    """MT4数据采集器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.data_dir = Path(config.get('data_dir', 'data/mt4'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.watch_files = {}
        self.file_handles = {}
        self.last_positions = {}
    
    async def connect(self) -> bool:
        """连接到MT4数据目录"""
        try:
            if not self.data_dir.exists():
                logger.error(f"MT4 data directory does not exist: {self.data_dir}")
                return False
            
            logger.info(f"Successfully connected to MT4 data directory: {self.data_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MT4 data directory: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """断开MT4数据目录连接"""
        try:
            # 关闭所有文件句柄
            for handle in self.file_handles.values():
                handle.close()
            self.file_handles.clear()
            logger.info("Successfully disconnected from MT4 data directory")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from MT4 data directory: {str(e)}")
            return False
    
    async def subscribe(self, symbol: str, data_type: DataType) -> bool:
        """订阅MT4数据"""
        try:
            if symbol not in self.subscriptions:
                self.subscriptions[symbol] = set()
            
            if data_type not in self.subscriptions[symbol]:
                self.subscriptions[symbol].add(data_type)
                
                # 根据数据类型设置文件路径
                file_path = self._get_data_file_path(symbol, data_type)
                if not file_path.exists():
                    logger.error(f"Data file does not exist: {file_path}")
                    return False
                
                # 创建文件监控任务
                task = asyncio.create_task(
                    self._watch_data_file(symbol, data_type, file_path)
                )
                self.watch_files[(symbol, data_type)] = task
                
                logger.info(f"Successfully subscribed to {symbol} {data_type.value}")
                return True
            
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol} {data_type.value}: {str(e)}")
            return False
    
    async def unsubscribe(self, symbol: str, data_type: DataType) -> bool:
        """取消订阅MT4数据"""
        try:
            if symbol in self.subscriptions:
                if data_type in self.subscriptions[symbol]:
                    self.subscriptions[symbol].remove(data_type)
                    
                    # 取消文件监控任务
                    key = (symbol, data_type)
                    if key in self.watch_files:
                        self.watch_files[key].cancel()
                        del self.watch_files[key]
                    
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
        """获取MT4历史数据"""
        try:
            file_path = self._get_data_file_path(symbol, data_type)
            if not file_path.exists():
                logger.error(f"Data file does not exist: {file_path}")
                return []
            
            data = []
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if start_time <= timestamp <= end_time:
                        if data_type == DataType.KLINE:
                            data.append(KlineData(
                                symbol=symbol,
                                data_type=DataType.KLINE,
                                timestamp=timestamp,
                                source='mt4',
                                raw_data=row,
                                open_price=float(row['open']),
                                high_price=float(row['high']),
                                low_price=float(row['low']),
                                close_price=float(row['close']),
                                volume=float(row['volume']),
                                interval=interval or '1h'
                            ))
                        elif data_type == DataType.TICK:
                            data.append(TickData(
                                symbol=symbol,
                                data_type=DataType.TICK,
                                timestamp=timestamp,
                                source='mt4',
                                raw_data=row,
                                last_price=float(row['last']),
                                bid_price=float(row['bid']),
                                ask_price=float(row['ask']),
                                bid_volume=float(row['bid_volume']),
                                ask_volume=float(row['ask_volume']),
                                volume_24h=float(row['volume_24h'])
                            ))
                        elif data_type == DataType.TRADE:
                            data.append(TradeData(
                                symbol=symbol,
                                data_type=DataType.TRADE,
                                timestamp=timestamp,
                                source='mt4',
                                raw_data=row,
                                price=float(row['price']),
                                volume=float(row['volume']),
                                side=row['side'],
                                order_id=row['order_id']
                            ))
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            return []
    
    def _get_data_file_path(self, symbol: str, data_type: DataType) -> Path:
        """获取数据文件路径"""
        return self.data_dir / f"{symbol}_{data_type.value}.csv"
    
    async def _watch_data_file(self, symbol: str, data_type: DataType, file_path: Path):
        """监控数据文件变化"""
        try:
            # 获取文件初始大小
            if file_path.exists():
                self.last_positions[(symbol, data_type)] = file_path.stat().st_size
            
            while self.is_running:
                if not file_path.exists():
                    await asyncio.sleep(1)
                    continue
                
                current_size = file_path.stat().st_size
                last_position = self.last_positions.get((symbol, data_type), 0)
                
                if current_size > last_position:
                    # 读取新数据
                    with open(file_path, 'r') as f:
                        f.seek(last_position)
                        for line in f:
                            try:
                                row = csv.DictReader([line]).__next__()
                                data = self._parse_data_row(symbol, data_type, row)
                                if data:
                                    await self.notify_subscribers(data)
                            except Exception as e:
                                logger.error(f"Failed to parse data row: {str(e)}")
                    
                    self.last_positions[(symbol, data_type)] = current_size
                
                await asyncio.sleep(0.1)  # 避免过于频繁的文件检查
                
        except asyncio.CancelledError:
            logger.info(f"Stopped watching {symbol} {data_type.value}")
        except Exception as e:
            logger.error(f"Error watching data file: {str(e)}")
    
    def _parse_data_row(self, symbol: str, data_type: DataType, row: Dict[str, str]) -> Optional[MarketData]:
        """解析数据行"""
        try:
            timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            if data_type == DataType.KLINE:
                return KlineData(
                    symbol=symbol,
                    data_type=DataType.KLINE,
                    timestamp=timestamp,
                    source='mt4',
                    raw_data=row,
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=float(row['volume']),
                    interval=row.get('interval', '1h')
                )
            elif data_type == DataType.TICK:
                return TickData(
                    symbol=symbol,
                    data_type=DataType.TICK,
                    timestamp=timestamp,
                    source='mt4',
                    raw_data=row,
                    last_price=float(row['last']),
                    bid_price=float(row['bid']),
                    ask_price=float(row['ask']),
                    bid_volume=float(row['bid_volume']),
                    ask_volume=float(row['ask_volume']),
                    volume_24h=float(row['volume_24h'])
                )
            elif data_type == DataType.TRADE:
                return TradeData(
                    symbol=symbol,
                    data_type=DataType.TRADE,
                    timestamp=timestamp,
                    source='mt4',
                    raw_data=row,
                    price=float(row['price']),
                    volume=float(row['volume']),
                    side=row['side'],
                    order_id=row['order_id']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse data row: {str(e)}")
            return None 