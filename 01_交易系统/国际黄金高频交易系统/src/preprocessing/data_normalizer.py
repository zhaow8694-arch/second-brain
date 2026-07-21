from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
from sklearn.preprocessing import StandardScaler, MinMaxScaler

class DataNormalizer:
    """数据标准化器类，用于对数据进行标准化处理"""
    
    def __init__(self):
        """初始化数据标准化器"""
        self.logger = logger.bind(context="data_normalizer")
        self.price_scaler = StandardScaler()
        self.volume_scaler = StandardScaler()
        self.confidence_scaler = MinMaxScaler()
        
    def normalize_market_data(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """标准化市场数据
        
        Args:
            data: 市场数据，可以是单个数据点或数据列表
            
        Returns:
            标准化后的市场数据
        """
        try:
            if isinstance(data, list):
                return [self._normalize_single_market_data(item) for item in data]
            return self._normalize_single_market_data(data)
        except Exception as e:
            self.logger.error(f"标准化市场数据时发生错误: {str(e)}")
            raise
            
    def _normalize_single_market_data(self, data: Dict) -> Dict:
        """标准化单个市场数据点
        
        Args:
            data: 单个市场数据点
            
        Returns:
            标准化后的市场数据点
        """
        normalized_data = data.copy()
        
        # 标准化价格数据
        price_fields = ['open', 'high', 'low', 'close', 'bid_price', 'ask_price']
        for field in price_fields:
            if field in normalized_data:
                normalized_data[field] = self._normalize_price(normalized_data[field])
                
        # 标准化成交量
        if 'volume' in normalized_data:
            normalized_data['volume'] = self._normalize_volume(normalized_data['volume'])
            
        return normalized_data
        
    def normalize_trading_signal(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """标准化交易信号数据
        
        Args:
            data: 交易信号数据，可以是单个数据点或数据列表
            
        Returns:
            标准化后的交易信号数据
        """
        try:
            if isinstance(data, list):
                return [self._normalize_single_trading_signal(item) for item in data]
            return self._normalize_single_trading_signal(data)
        except Exception as e:
            self.logger.error(f"标准化交易信号数据时发生错误: {str(e)}")
            raise
            
    def _normalize_single_trading_signal(self, data: Dict) -> Dict:
        """标准化单个交易信号数据点
        
        Args:
            data: 单个交易信号数据点
            
        Returns:
            标准化后的交易信号数据点
        """
        normalized_data = data.copy()
        
        # 标准化价格
        if 'price' in normalized_data:
            normalized_data['price'] = self._normalize_price(normalized_data['price'])
            
        # 标准化置信度
        if 'confidence' in normalized_data:
            normalized_data['confidence'] = self._normalize_confidence(normalized_data['confidence'])
            
        return normalized_data
        
    def normalize_order_data(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """标准化订单数据
        
        Args:
            data: 订单数据，可以是单个数据点或数据列表
            
        Returns:
            标准化后的订单数据
        """
        try:
            if isinstance(data, list):
                return [self._normalize_single_order_data(item) for item in data]
            return self._normalize_single_order_data(data)
        except Exception as e:
            self.logger.error(f"标准化订单数据时发生错误: {str(e)}")
            raise
            
    def _normalize_single_order_data(self, data: Dict) -> Dict:
        """标准化单个订单数据点
        
        Args:
            data: 单个订单数据点
            
        Returns:
            标准化后的订单数据点
        """
        normalized_data = data.copy()
        
        # 标准化价格
        if 'price' in normalized_data:
            normalized_data['price'] = self._normalize_price(normalized_data['price'])
            
        # 标准化数量
        if 'volume' in normalized_data:
            normalized_data['volume'] = self._normalize_volume(normalized_data['volume'])
            
        return normalized_data
        
    def _normalize_price(self, price: float) -> float:
        """标准化价格数据
        
        Args:
            price: 价格数据
            
        Returns:
            标准化后的价格
        """
        try:
            # 使用StandardScaler进行标准化
            price_array = np.array([[price]])
            normalized_price = self.price_scaler.fit_transform(price_array)[0][0]
            return float(normalized_price)
        except Exception as e:
            self.logger.error(f"标准化价格数据时发生错误: {str(e)}")
            raise
            
    def _normalize_volume(self, volume: float) -> float:
        """标准化成交量数据
        
        Args:
            volume: 成交量数据
            
        Returns:
            标准化后的成交量
        """
        try:
            # 使用StandardScaler进行标准化
            volume_array = np.array([[volume]])
            normalized_volume = self.volume_scaler.fit_transform(volume_array)[0][0]
            return float(normalized_volume)
        except Exception as e:
            self.logger.error(f"标准化成交量数据时发生错误: {str(e)}")
            raise
            
    def _normalize_confidence(self, confidence: float) -> float:
        """标准化置信度数据
        
        Args:
            confidence: 置信度数据
            
        Returns:
            标准化后的置信度
        """
        try:
            # 使用MinMaxScaler进行标准化，确保结果在0-1之间
            confidence_array = np.array([[confidence]])
            normalized_confidence = self.confidence_scaler.fit_transform(confidence_array)[0][0]
            return float(normalized_confidence)
        except Exception as e:
            self.logger.error(f"标准化置信度数据时发生错误: {str(e)}")
            raise
            
    def fit_scalers(self, market_data: List[Dict], trading_signals: List[Dict], orders: List[Dict]):
        """使用历史数据拟合标准化器
        
        Args:
            market_data: 历史市场数据
            trading_signals: 历史交易信号
            orders: 历史订单数据
        """
        try:
            # 提取价格数据
            prices = []
            for data in market_data:
                for field in ['open', 'high', 'low', 'close', 'bid_price', 'ask_price']:
                    if field in data:
                        prices.append(data[field])
            for signal in trading_signals:
                if 'price' in signal:
                    prices.append(signal['price'])
            for order in orders:
                if 'price' in order:
                    prices.append(order['price'])
                    
            # 提取成交量数据
            volumes = []
            for data in market_data:
                if 'volume' in data:
                    volumes.append(data['volume'])
            for order in orders:
                if 'volume' in order:
                    volumes.append(order['volume'])
                    
            # 提取置信度数据
            confidences = []
            for signal in trading_signals:
                if 'confidence' in signal:
                    confidences.append(signal['confidence'])
                    
            # 拟合标准化器
            if prices:
                self.price_scaler.fit(np.array(prices).reshape(-1, 1))
            if volumes:
                self.volume_scaler.fit(np.array(volumes).reshape(-1, 1))
            if confidences:
                self.confidence_scaler.fit(np.array(confidences).reshape(-1, 1))
                
        except Exception as e:
            self.logger.error(f"拟合标准化器时发生错误: {str(e)}")
            raise 