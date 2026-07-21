import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from sklearn.preprocessing import StandardScaler
import logging

from .deepseek_interface import (
    DeepSeekModelInterface,
    MarketFeatures,
    ModelPrediction,
    ModelConfig
)

class PricePredictionNetwork(nn.Module):
    """价格预测神经网络"""
    
    def __init__(self, input_size: int, hidden_size: int = 128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, 1)
        )
        
        # 预测区间估计
        self.interval_network = nn.Sequential(
            nn.Linear(input_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 2)  # 输出上下界
        )
        
        # 置信度估计
        self.confidence_network = nn.Sequential(
            nn.Linear(input_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """前向传播"""
        prediction = self.network(x)
        intervals = self.interval_network(x)
        confidence = self.confidence_network(x)
        return prediction, intervals, confidence

class PricePredictionModel(DeepSeekModelInterface):
    """价格预测模型实现"""
    
    async def initialize_model(self):
        """初始化价格预测模型"""
        # 设置设备
        self.device = torch.device('cuda' if self.config.use_gpu and torch.cuda.is_available() else 'cpu')
        
        # 初始化特征处理器
        self.feature_scaler = StandardScaler()
        
        # 初始化神经网络
        input_size = len(self.config.input_features)
        self.model = PricePredictionNetwork(input_size).to(self.device)
        
        # 初始化优化器
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        # 初始化损失函数
        self.criterion = nn.MSELoss()
        self.interval_criterion = nn.HuberLoss()
        
        # 初始化特征重要性分析
        self.feature_importance = {feature: 0.0 for feature in self.config.input_features}
        
        logging.info("Price prediction model initialized")
        
    async def preprocess_features(self, features: MarketFeatures) -> np.ndarray:
        """预处理特征"""
        # 提取配置中指定的特征
        feature_vector = []
        for feature_name in self.config.input_features:
            if hasattr(features, feature_name):
                feature_vector.append(getattr(features, feature_name))
            elif feature_name in features.custom_indicators:
                feature_vector.append(features.custom_indicators[feature_name])
            elif feature_name in features.market_depth:
                feature_vector.append(features.market_depth[feature_name])
            else:
                raise ValueError(f"Feature {feature_name} not found in market features")
                
        # 转换为numpy数组
        feature_array = np.array(feature_vector).reshape(1, -1)
        
        # 标准化特征
        if not hasattr(self.feature_scaler, 'mean_'):
            self.feature_scaler.fit(feature_array)
        feature_array = self.feature_scaler.transform(feature_array)
        
        return feature_array
        
    async def predict(self, features: MarketFeatures) -> ModelPrediction:
        """执行预测"""
        # 预处理特征
        feature_array = await self.preprocess_features(features)
        feature_tensor = torch.FloatTensor(feature_array).to(self.device)
        
        # 设置为评估模式
        self.model.eval()
        
        with torch.no_grad():
            # 获取预测结果
            prediction, intervals, confidence = self.model(feature_tensor)
            
            # 转换预测结果
            predicted_value = prediction.item()
            confidence_value = confidence.item()
            lower_bound, upper_bound = intervals[0].tolist()
            
            # 计算特征重要性（使用梯度）
            feature_importance = self._calculate_feature_importance(feature_tensor)
            
        # 创建预测结果
        return ModelPrediction(
            predicted_value=predicted_value,
            confidence=confidence_value,
            prediction_horizon=self.config.time_horizon,
            feature_importance=feature_importance,
            prediction_interval=(lower_bound, upper_bound),
            timestamp=datetime.now()
        )
        
    async def update_model(self, features: List[MarketFeatures], labels: List[float]):
        """更新模型"""
        if len(features) != len(labels):
            raise ValueError("Features and labels must have the same length")
            
        # 预处理所有特征
        feature_arrays = []
        for feature in features:
            feature_array = await self.preprocess_features(feature)
            feature_arrays.append(feature_array)
            
        # 转换为张量
        X = torch.FloatTensor(np.vstack(feature_arrays)).to(self.device)
        y = torch.FloatTensor(labels).reshape(-1, 1).to(self.device)
        
        # 设置为训练模式
        self.model.train()
        
        # 批量训练
        batch_size = self.config.batch_size
        for i in range(0, len(X), batch_size):
            batch_X = X[i:i+batch_size]
            batch_y = y[i:i+batch_size]
            
            # 前向传播
            self.optimizer.zero_grad()
            predictions, intervals, confidence = self.model(batch_X)
            
            # 计算损失
            prediction_loss = self.criterion(predictions, batch_y)
            interval_loss = self.interval_criterion(intervals, 
                                                 torch.cat([batch_y * 0.99, batch_y * 1.01], dim=1))
            
            total_loss = prediction_loss + 0.1 * interval_loss
            
            # 反向传播
            total_loss.backward()
            self.optimizer.step()
            
        # 更新时间戳
        self.last_update_time = datetime.now()
        
        # 保存训练历史
        self.training_history.append({
            'timestamp': self.last_update_time,
            'loss': total_loss.item(),
            'samples': len(features)
        })
        
        logging.info(f"Model updated with {len(features)} samples")
        
    async def validate_prediction(self, prediction: ModelPrediction, actual_value: float):
        """验证预测结果"""
        # 计算预测误差
        error = abs(prediction.predicted_value - actual_value)
        relative_error = error / actual_value
        
        # 检查是否在预测区间内
        in_interval = (prediction.prediction_interval[0] <= actual_value <= 
                      prediction.prediction_interval[1])
        
        # 更新预测历史
        validation_result = {
            'timestamp': prediction.timestamp,
            'predicted_value': prediction.predicted_value,
            'actual_value': actual_value,
            'error': error,
            'relative_error': relative_error,
            'confidence': prediction.confidence,
            'in_interval': in_interval
        }
        
        self.prediction_history.append(validation_result)
        
        # 如果预测误差过大，可能需要更新模型
        if relative_error > 0.01 and len(self.prediction_history) >= 10:
            recent_errors = [p['relative_error'] for p in self.prediction_history[-10:]]
            if np.mean(recent_errors) > 0.005:  # 如果最近10次预测的平均相对误差超过0.5%
                logging.warning("High prediction error detected, model update recommended")
                
        return validation_result
        
    def _calculate_feature_importance(self, features: torch.Tensor) -> Dict[str, float]:
        """计算特征重要性"""
        features.requires_grad_(True)
        prediction, _, _ = self.model(features)
        
        # 计算梯度
        prediction.backward()
        gradients = features.grad.abs().mean(dim=0).cpu().numpy()
        
        # 更新特征重要性
        importance_dict = {}
        for feature_name, importance in zip(self.config.input_features, gradients):
            importance_dict[feature_name] = float(importance)
            
        return importance_dict 