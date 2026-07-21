from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetector:
    """异常检测器类，用于检测数据中的异常值"""
    
    def __init__(self, contamination: float = 0.1):
        """初始化异常检测器
        
        Args:
            contamination: 预期的异常数据比例
        """
        self.logger = logger.bind(context="anomaly_detector")
        self.contamination = contamination
        self.price_detector = IsolationForest(contamination=contamination)
        self.volume_detector = IsolationForest(contamination=contamination)
        self.confidence_detector = IsolationForest(contamination=contamination)
        self.price_scaler = StandardScaler()
        self.volume_scaler = StandardScaler()
        self.confidence_scaler = StandardScaler()
        
    def detect_market_data_anomalies(self, data: Union[Dict, List[Dict]]) -> Union[Tuple[Dict, bool], List[Tuple[Dict, bool]]]:
        """检测市场数据中的异常
        
        Args:
            data: 市场数据，可以是单个数据点或数据列表
            
        Returns:
            数据点和是否异常的元组，或元组列表
        """
        try:
            if isinstance(data, list):
                return [self._detect_single_market_data_anomalies(item) for item in data]
            return self._detect_single_market_data_anomalies(data)
        except Exception as e:
            self.logger.error(f"检测市场数据异常时发生错误: {str(e)}")
            raise
            
    def _detect_single_market_data_anomalies(self, data: Dict) -> Tuple[Dict, bool]:
        """检测单个市场数据点的异常
        
        Args:
            data: 单个市场数据点
            
        Returns:
            数据点和是否异常的元组
        """
        is_anomaly = False
        
        # 检测价格异常
        price_fields = ['open', 'high', 'low', 'close', 'bid_price', 'ask_price']
        for field in price_fields:
            if field in data:
                price = data[field]
                if self._is_price_anomaly(price):
                    is_anomaly = True
                    self.logger.warning(f"检测到价格异常: {field}={price}")
                    
        # 检测成交量异常
        if 'volume' in data:
            volume = data['volume']
            if self._is_volume_anomaly(volume):
                is_anomaly = True
                self.logger.warning(f"检测到成交量异常: volume={volume}")
                
        return data, is_anomaly
        
    def detect_trading_signal_anomalies(self, data: Union[Dict, List[Dict]]) -> Union[Tuple[Dict, bool], List[Tuple[Dict, bool]]]:
        """检测交易信号中的异常
        
        Args:
            data: 交易信号数据，可以是单个数据点或数据列表
            
        Returns:
            数据点和是否异常的元组，或元组列表
        """
        try:
            if isinstance(data, list):
                return [self._detect_single_trading_signal_anomalies(item) for item in data]
            return self._detect_single_trading_signal_anomalies(data)
        except Exception as e:
            self.logger.error(f"检测交易信号异常时发生错误: {str(e)}")
            raise
            
    def _detect_single_trading_signal_anomalies(self, data: Dict) -> Tuple[Dict, bool]:
        """检测单个交易信号数据点的异常
        
        Args:
            data: 单个交易信号数据点
            
        Returns:
            数据点和是否异常的元组
        """
        is_anomaly = False
        
        # 检测价格异常
        if 'price' in data:
            price = data['price']
            if self._is_price_anomaly(price):
                is_anomaly = True
                self.logger.warning(f"检测到价格异常: price={price}")
                
        # 检测置信度异常
        if 'confidence' in data:
            confidence = data['confidence']
            if self._is_confidence_anomaly(confidence):
                is_anomaly = True
                self.logger.warning(f"检测到置信度异常: confidence={confidence}")
                
        return data, is_anomaly
        
    def detect_order_data_anomalies(self, data: Union[Dict, List[Dict]]) -> Union[Tuple[Dict, bool], List[Tuple[Dict, bool]]]:
        """检测订单数据中的异常
        
        Args:
            data: 订单数据，可以是单个数据点或数据列表
            
        Returns:
            数据点和是否异常的元组，或元组列表
        """
        try:
            if isinstance(data, list):
                return [self._detect_single_order_data_anomalies(item) for item in data]
            return self._detect_single_order_data_anomalies(data)
        except Exception as e:
            self.logger.error(f"检测订单数据异常时发生错误: {str(e)}")
            raise
            
    def _detect_single_order_data_anomalies(self, data: Dict) -> Tuple[Dict, bool]:
        """检测单个订单数据点的异常
        
        Args:
            data: 单个订单数据点
            
        Returns:
            数据点和是否异常的元组
        """
        is_anomaly = False
        
        # 检测价格异常
        if 'price' in data:
            price = data['price']
            if self._is_price_anomaly(price):
                is_anomaly = True
                self.logger.warning(f"检测到价格异常: price={price}")
                
        # 检测数量异常
        if 'volume' in data:
            volume = data['volume']
            if self._is_volume_anomaly(volume):
                is_anomaly = True
                self.logger.warning(f"检测到数量异常: volume={volume}")
                
        return data, is_anomaly
        
    def _is_price_anomaly(self, price: float) -> bool:
        """检测价格是否异常
        
        Args:
            price: 价格数据
            
        Returns:
            是否异常
        """
        try:
            # 标准化价格
            price_array = np.array([[price]])
            normalized_price = self.price_scaler.fit_transform(price_array)
            
            # 使用IsolationForest检测异常
            prediction = self.price_detector.predict(normalized_price)
            return prediction[0] == -1
        except Exception as e:
            self.logger.error(f"检测价格异常时发生错误: {str(e)}")
            raise
            
    def _is_volume_anomaly(self, volume: float) -> bool:
        """检测成交量是否异常
        
        Args:
            volume: 成交量数据
            
        Returns:
            是否异常
        """
        try:
            # 标准化成交量
            volume_array = np.array([[volume]])
            normalized_volume = self.volume_scaler.fit_transform(volume_array)
            
            # 使用IsolationForest检测异常
            prediction = self.volume_detector.predict(normalized_volume)
            return prediction[0] == -1
        except Exception as e:
            self.logger.error(f"检测成交量异常时发生错误: {str(e)}")
            raise
            
    def _is_confidence_anomaly(self, confidence: float) -> bool:
        """检测置信度是否异常
        
        Args:
            confidence: 置信度数据
            
        Returns:
            是否异常
        """
        try:
            # 标准化置信度
            confidence_array = np.array([[confidence]])
            normalized_confidence = self.confidence_scaler.fit_transform(confidence_array)
            
            # 使用IsolationForest检测异常
            prediction = self.confidence_detector.predict(normalized_confidence)
            return prediction[0] == -1
        except Exception as e:
            self.logger.error(f"检测置信度异常时发生错误: {str(e)}")
            raise
            
    def fit_detectors(self, market_data: List[Dict], trading_signals: List[Dict], orders: List[Dict]):
        """使用历史数据拟合异常检测器
        
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
                    
            # 拟合异常检测器
            if prices:
                normalized_prices = self.price_scaler.fit_transform(np.array(prices).reshape(-1, 1))
                self.price_detector.fit(normalized_prices)
            if volumes:
                normalized_volumes = self.volume_scaler.fit_transform(np.array(volumes).reshape(-1, 1))
                self.volume_detector.fit(normalized_volumes)
            if confidences:
                normalized_confidences = self.confidence_scaler.fit_transform(np.array(confidences).reshape(-1, 1))
                self.confidence_detector.fit(normalized_confidences)
                
        except Exception as e:
            self.logger.error(f"拟合异常检测器时发生错误: {str(e)}")
            raise 