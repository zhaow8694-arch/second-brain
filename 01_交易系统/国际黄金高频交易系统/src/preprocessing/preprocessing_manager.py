from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from loguru import logger

from .data_cleaner import DataCleaner
from .data_normalizer import DataNormalizer
from .anomaly_detector import AnomalyDetector

class PreprocessingManager:
    """数据预处理管理器，整合数据清洗、标准化和异常检测功能"""
    
    def __init__(self, anomaly_contamination: float = 0.1):
        """初始化数据预处理管理器
        
        Args:
            anomaly_contamination: 预期的异常数据比例
        """
        self.logger = logger.bind(context="preprocessing_manager")
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        self.anomaly_detector = AnomalyDetector(contamination=anomaly_contamination)
        
    def preprocess_market_data(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """预处理市场数据
        
        Args:
            data: 市场数据，可以是单个数据点或数据列表
            
        Returns:
            预处理后的市场数据
        """
        try:
            # 清洗数据
            cleaned_data = self.cleaner.clean_market_data(data)
            
            # 检测异常
            if isinstance(cleaned_data, list):
                processed_data = []
                for item, is_anomaly in self.anomaly_detector.detect_market_data_anomalies(cleaned_data):
                    if not is_anomaly:
                        processed_data.append(item)
            else:
                processed_data, is_anomaly = self.anomaly_detector.detect_market_data_anomalies(cleaned_data)
                if is_anomaly:
                    return None
                    
            # 标准化数据
            normalized_data = self.normalizer.normalize_market_data(processed_data)
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"预处理市场数据时发生错误: {str(e)}")
            raise
            
    def preprocess_trading_signal(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """预处理交易信号数据
        
        Args:
            data: 交易信号数据，可以是单个数据点或数据列表
            
        Returns:
            预处理后的交易信号数据
        """
        try:
            # 清洗数据
            cleaned_data = self.cleaner.clean_trading_signal(data)
            
            # 检测异常
            if isinstance(cleaned_data, list):
                processed_data = []
                for item, is_anomaly in self.anomaly_detector.detect_trading_signal_anomalies(cleaned_data):
                    if not is_anomaly:
                        processed_data.append(item)
            else:
                processed_data, is_anomaly = self.anomaly_detector.detect_trading_signal_anomalies(cleaned_data)
                if is_anomaly:
                    return None
                    
            # 标准化数据
            normalized_data = self.normalizer.normalize_trading_signal(processed_data)
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"预处理交易信号数据时发生错误: {str(e)}")
            raise
            
    def preprocess_order_data(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """预处理订单数据
        
        Args:
            data: 订单数据，可以是单个数据点或数据列表
            
        Returns:
            预处理后的订单数据
        """
        try:
            # 清洗数据
            cleaned_data = self.cleaner.clean_order_data(data)
            
            # 检测异常
            if isinstance(cleaned_data, list):
                processed_data = []
                for item, is_anomaly in self.anomaly_detector.detect_order_data_anomalies(cleaned_data):
                    if not is_anomaly:
                        processed_data.append(item)
            else:
                processed_data, is_anomaly = self.anomaly_detector.detect_order_data_anomalies(cleaned_data)
                if is_anomaly:
                    return None
                    
            # 标准化数据
            normalized_data = self.normalizer.normalize_order_data(processed_data)
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"预处理订单数据时发生错误: {str(e)}")
            raise
            
    def fit_preprocessors(self, market_data: List[Dict], trading_signals: List[Dict], orders: List[Dict]):
        """使用历史数据拟合所有预处理器
        
        Args:
            market_data: 历史市场数据
            trading_signals: 历史交易信号
            orders: 历史订单数据
        """
        try:
            # 拟合标准化器
            self.normalizer.fit_scalers(market_data, trading_signals, orders)
            
            # 拟合异常检测器
            self.anomaly_detector.fit_detectors(market_data, trading_signals, orders)
            
            self.logger.info("成功拟合所有预处理器")
            
        except Exception as e:
            self.logger.error(f"拟合预处理器时发生错误: {str(e)}")
            raise 