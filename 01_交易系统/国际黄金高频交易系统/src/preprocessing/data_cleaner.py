from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger

class DataCleaner:
    """数据清洗器类，用于处理原始数据中的异常值、缺失值和重复数据"""
    
    def __init__(self):
        """初始化数据清洗器"""
        self.logger = logger.bind(context="data_cleaner")
        
    def clean_market_data(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """清洗市场数据
        
        Args:
            data: 市场数据，可以是单个数据点或数据列表
            
        Returns:
            清洗后的市场数据
        """
        try:
            if isinstance(data, list):
                return [self._clean_single_market_data(item) for item in data]
            return self._clean_single_market_data(data)
        except Exception as e:
            self.logger.error(f"清洗市场数据时发生错误: {str(e)}")
            raise
            
    def _clean_single_market_data(self, data: Dict) -> Dict:
        """清洗单个市场数据点
        
        Args:
            data: 单个市场数据点
            
        Returns:
            清洗后的市场数据点
        """
        cleaned_data = data.copy()
        
        # 处理时间戳
        if 'time' in cleaned_data:
            cleaned_data['time'] = self._clean_timestamp(cleaned_data['time'])
            
        # 处理价格数据
        price_fields = ['open', 'high', 'low', 'close', 'bid_price', 'ask_price']
        for field in price_fields:
            if field in cleaned_data:
                cleaned_data[field] = self._clean_price(cleaned_data[field])
                
        # 处理成交量
        if 'volume' in cleaned_data:
            cleaned_data['volume'] = self._clean_volume(cleaned_data['volume'])
            
        return cleaned_data
        
    def clean_trading_signal(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """清洗交易信号数据
        
        Args:
            data: 交易信号数据，可以是单个数据点或数据列表
            
        Returns:
            清洗后的交易信号数据
        """
        try:
            if isinstance(data, list):
                return [self._clean_single_trading_signal(item) for item in data]
            return self._clean_single_trading_signal(data)
        except Exception as e:
            self.logger.error(f"清洗交易信号数据时发生错误: {str(e)}")
            raise
            
    def _clean_single_trading_signal(self, data: Dict) -> Dict:
        """清洗单个交易信号数据点
        
        Args:
            data: 单个交易信号数据点
            
        Returns:
            清洗后的交易信号数据点
        """
        cleaned_data = data.copy()
        
        # 处理时间戳
        if 'time' in cleaned_data:
            cleaned_data['time'] = self._clean_timestamp(cleaned_data['time'])
            
        # 处理价格
        if 'price' in cleaned_data:
            cleaned_data['price'] = self._clean_price(cleaned_data['price'])
            
        # 处理置信度
        if 'confidence' in cleaned_data:
            cleaned_data['confidence'] = self._clean_confidence(cleaned_data['confidence'])
            
        return cleaned_data
        
    def clean_order_data(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """清洗订单数据
        
        Args:
            data: 订单数据，可以是单个数据点或数据列表
            
        Returns:
            清洗后的订单数据
        """
        try:
            if isinstance(data, list):
                return [self._clean_single_order_data(item) for item in data]
            return self._clean_single_order_data(data)
        except Exception as e:
            self.logger.error(f"清洗订单数据时发生错误: {str(e)}")
            raise
            
    def _clean_single_order_data(self, data: Dict) -> Dict:
        """清洗单个订单数据点
        
        Args:
            data: 单个订单数据点
            
        Returns:
            清洗后的订单数据点
        """
        cleaned_data = data.copy()
        
        # 处理时间戳
        if 'time' in cleaned_data:
            cleaned_data['time'] = self._clean_timestamp(cleaned_data['time'])
            
        # 处理价格
        if 'price' in cleaned_data:
            cleaned_data['price'] = self._clean_price(cleaned_data['price'])
            
        # 处理数量
        if 'volume' in cleaned_data:
            cleaned_data['volume'] = self._clean_volume(cleaned_data['volume'])
            
        return cleaned_data
        
    def _clean_timestamp(self, timestamp: Union[str, int, datetime]) -> datetime:
        """清洗时间戳
        
        Args:
            timestamp: 时间戳
            
        Returns:
            清洗后的datetime对象
        """
        try:
            if isinstance(timestamp, datetime):
                return timestamp
            elif isinstance(timestamp, str):
                return pd.to_datetime(timestamp)
            elif isinstance(timestamp, int):
                return pd.to_datetime(timestamp, unit='ms')
            else:
                raise ValueError(f"不支持的时间戳格式: {type(timestamp)}")
        except Exception as e:
            self.logger.error(f"清洗时间戳时发生错误: {str(e)}")
            raise
            
    def _clean_price(self, price: Union[float, str]) -> float:
        """清洗价格数据
        
        Args:
            price: 价格数据
            
        Returns:
            清洗后的价格
        """
        try:
            if isinstance(price, str):
                price = float(price)
            if not isinstance(price, (int, float)) or np.isnan(price) or price <= 0:
                raise ValueError(f"无效的价格数据: {price}")
            return float(price)
        except Exception as e:
            self.logger.error(f"清洗价格数据时发生错误: {str(e)}")
            raise
            
    def _clean_volume(self, volume: Union[float, str]) -> float:
        """清洗成交量数据
        
        Args:
            volume: 成交量数据
            
        Returns:
            清洗后的成交量
        """
        try:
            if isinstance(volume, str):
                volume = float(volume)
            if not isinstance(volume, (int, float)) or np.isnan(volume) or volume < 0:
                raise ValueError(f"无效的成交量数据: {volume}")
            return float(volume)
        except Exception as e:
            self.logger.error(f"清洗成交量数据时发生错误: {str(e)}")
            raise
            
    def _clean_confidence(self, confidence: Union[float, str]) -> float:
        """清洗置信度数据
        
        Args:
            confidence: 置信度数据
            
        Returns:
            清洗后的置信度
        """
        try:
            if isinstance(confidence, str):
                confidence = float(confidence)
            if not isinstance(confidence, (int, float)) or np.isnan(confidence):
                raise ValueError(f"无效的置信度数据: {confidence}")
            # 确保置信度在0-1之间
            return max(0.0, min(1.0, float(confidence)))
        except Exception as e:
            self.logger.error(f"清洗置信度数据时发生错误: {str(e)}")
            raise 