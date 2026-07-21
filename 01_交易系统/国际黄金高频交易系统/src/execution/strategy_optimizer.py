from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from collections import deque
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from .quality_analyzer import QualityAnalyzer, ExecutionMetrics, QualityReport
from .timing_optimizer import TimingOptimizer
from .market_impact_analyzer import MarketImpactAnalyzer

@dataclass
class OptimizationResult:
    """优化结果"""
    participation_rate: float      # 最优参与率
    execution_window: int         # 最优执行窗口（分钟）
    urgency_factor: float        # 紧急度因子
    expected_cost: float         # 预期成本
    confidence: float            # 优化置信度
    
@dataclass
class StrategyParameters:
    """策略参数"""
    min_participation_rate: float  # 最小参与率
    max_participation_rate: float  # 最大参与率
    min_window_size: int          # 最小窗口大小
    max_window_size: int          # 最大窗口大小
    cost_weight: float            # 成本权重
    time_weight: float            # 时间权重

class StrategyOptimizer:
    def __init__(self,
                 quality_analyzer: QualityAnalyzer,
                 timing_optimizer: TimingOptimizer,
                 impact_analyzer: MarketImpactAnalyzer,
                 learning_rate: float = 0.01,
                 history_window: int = 1000,
                 min_samples: int = 50):
        """
        初始化策略优化器
        
        Args:
            quality_analyzer: 执行质量分析器实例
            timing_optimizer: 执行时机优化器实例
            impact_analyzer: 市场冲击分析器实例
            learning_rate: 学习率
            history_window: 历史数据窗口大小
            min_samples: 最小样本数量
        """
        self.quality_analyzer = quality_analyzer
        self.timing_optimizer = timing_optimizer
        self.impact_analyzer = impact_analyzer
        self.learning_rate = learning_rate
        self.history_window = history_window
        self.min_samples = min_samples
        
        # 机器学习模型
        self.cost_model = RandomForestRegressor(n_estimators=100)
        self.time_model = RandomForestRegressor(n_estimators=100)
        
        # 数据预处理
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        
        # 历史数据
        self.execution_history: List[Dict] = []
        self.model_features: List[str] = [
            'participation_rate',
            'window_size',
            'urgency',
            'volatility',
            'spread',
            'volume',
            'imbalance'
        ]
        
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """准备训练数据"""
        if len(self.execution_history) < self.min_samples:
            return np.array([]), np.array([]), np.array([])
            
        # 构建特征矩阵
        features = []
        costs = []
        times = []
        
        for record in self.execution_history:
            feature_vector = [
                record['participation_rate'],
                record['window_size'],
                record['urgency'],
                record['market_conditions']['volatility'],
                record['market_conditions']['spread'],
                record['market_conditions']['volume'],
                record['market_conditions']['imbalance']
            ]
            features.append(feature_vector)
            costs.append(record['execution_metrics'].total_cost)
            times.append(record['execution_metrics'].delay_cost)
            
        X = np.array(features)
        y_cost = np.array(costs)
        y_time = np.array(times)
        
        # 数据标准化
        X = self.feature_scaler.fit_transform(X)
        y_cost = self.target_scaler.fit_transform(y_cost.reshape(-1, 1)).ravel()
        
        return X, y_cost, y_time
        
    def _update_models(self):
        """更新机器学习模型"""
        X, y_cost, y_time = self._prepare_training_data()
        if len(X) == 0:
            return
            
        # 训练成本预测模型
        self.cost_model.fit(X, y_cost)
        
        # 训练时间预测模型
        self.time_model.fit(X, y_time)
        
    def _predict_metrics(self,
                        features: np.ndarray) -> Tuple[float, float]:
        """预测执行指标"""
        if len(self.execution_history) < self.min_samples:
            return 0.0, 0.0
            
        # 数据标准化
        X = self.feature_scaler.transform(features)
        
        # 预测成本和时间
        cost_pred = self.cost_model.predict(X)
        time_pred = self.time_model.predict(X)
        
        # 反标准化成本预测
        cost_pred = self.target_scaler.inverse_transform(
            cost_pred.reshape(-1, 1)
        ).ravel()
        
        return cost_pred[0], time_pred[0]
        
    def _calculate_optimization_score(self,
                                   cost: float,
                                   time: float,
                                   params: StrategyParameters) -> float:
        """计算优化分数"""
        # 归一化成本和时间
        normalized_cost = cost / params.cost_weight if params.cost_weight > 0 else 0
        normalized_time = time / params.time_weight if params.time_weight > 0 else 0
        
        # 计算加权分数
        return -(normalized_cost + normalized_time)
        
    def _generate_parameter_grid(self,
                               params: StrategyParameters,
                               market_conditions: Dict) -> List[Dict]:
        """生成参数网格"""
        # 根据市场条件调整参数范围
        volatility = market_conditions.get('volatility', 0.5)
        spread = market_conditions.get('spread', 0.5)
        volume = market_conditions.get('volume', 0.5)
        
        # 调整参与率范围
        base_min_rate = params.min_participation_rate
        base_max_rate = params.max_participation_rate
        if volatility > 0.7:  # 高波动时降低参与率
            base_max_rate *= 0.8
        if spread > 0.7:  # 高价差时降低参与率
            base_max_rate *= 0.8
        if volume < 0.3:  # 低成交量时降低参与率
            base_max_rate *= 0.7
            
        # 调整窗口大小范围
        base_min_window = params.min_window_size
        base_max_window = params.max_window_size
        if volatility > 0.7:  # 高波动时增加窗口
            base_min_window = int(base_min_window * 1.2)
        if volume < 0.3:  # 低成交量时增加窗口
            base_min_window = int(base_min_window * 1.2)
            
        # 生成参数组合
        param_grid = []
        participation_rates = np.linspace(base_min_rate, base_max_rate, 10)
        window_sizes = np.linspace(base_min_window, base_max_window, 10)
        urgency_factors = np.linspace(0.1, 0.9, 5)
        
        for rate in participation_rates:
            for window in window_sizes:
                for urgency in urgency_factors:
                    param_grid.append({
                        'participation_rate': rate,
                        'window_size': int(window),
                        'urgency': urgency
                    })
                    
        return param_grid
        
    async def optimize_strategy(self,
                              size: float,
                              side: str,
                              params: StrategyParameters) -> OptimizationResult:
        """
        优化执行策略
        
        Args:
            size: 订单数量
            side: 交易方向
            params: 策略参数
            
        Returns:
            OptimizationResult: 优化结果
        """
        # 获取当前市场状态
        market_conditions = {
            'volatility': self.impact_analyzer.current_condition.volatility_score,
            'spread': self.impact_analyzer.current_condition.avg_spread,
            'volume': self.impact_analyzer.current_condition.avg_volume,
            'imbalance': self.impact_analyzer.current_condition.bid_ask_imbalance
        }
        
        # 生成参数网格
        param_grid = self._generate_parameter_grid(params, market_conditions)
        
        # 更新模型
        self._update_models()
        
        # 评估每组参数
        best_score = float('-inf')
        best_params = None
        predictions = []
        
        for params in param_grid:
            # 构建特征向量
            features = np.array([[
                params['participation_rate'],
                params['window_size'],
                params['urgency'],
                market_conditions['volatility'],
                market_conditions['spread'],
                market_conditions['volume'],
                market_conditions['imbalance']
            ]])
            
            # 预测成本和时间
            cost_pred, time_pred = self._predict_metrics(features)
            
            # 计算优化分数
            score = self._calculate_optimization_score(
                cost_pred,
                time_pred,
                params
            )
            
            predictions.append({
                'params': params,
                'cost': cost_pred,
                'time': time_pred,
                'score': score
            })
            
            if score > best_score:
                best_score = score
                best_params = params
                
        if best_params is None:
            # 使用默认参数
            return OptimizationResult(
                participation_rate=0.1,
                execution_window=params.min_window_size,
                urgency_factor=0.5,
                expected_cost=0.0,
                confidence=0.0
            )
            
        # 计算预测置信度
        if len(predictions) > 1:
            scores = [p['score'] for p in predictions]
            score_std = np.std(scores)
            score_range = max(scores) - min(scores)
            confidence = 1.0 - (score_std / score_range) if score_range > 0 else 0.0
        else:
            confidence = 0.0
            
        return OptimizationResult(
            participation_rate=best_params['participation_rate'],
            execution_window=best_params['window_size'],
            urgency_factor=best_params['urgency'],
            expected_cost=abs(predictions[0]['cost']),
            confidence=confidence
        )
        
    async def update_execution_history(self,
                                    order_id: str,
                                    participation_rate: float,
                                    window_size: int,
                                    urgency: float,
                                    quality_report: QualityReport):
        """更新执行历史"""
        record = {
            'order_id': order_id,
            'participation_rate': participation_rate,
            'window_size': window_size,
            'urgency': urgency,
            'market_conditions': quality_report.market_conditions,
            'execution_metrics': quality_report.execution_metrics,
            'benchmark_metrics': quality_report.benchmark_metrics
        }
        
        self.execution_history.append(record)
        if len(self.execution_history) > self.history_window:
            self.execution_history.pop(0)
            
    def get_optimization_stats(self) -> Dict:
        """获取优化统计信息"""
        if not self.execution_history:
            return {}
            
        # 提取统计数据
        participation_rates = [r['participation_rate'] for r in self.execution_history]
        window_sizes = [r['window_size'] for r in self.execution_history]
        costs = [r['execution_metrics'].total_cost for r in self.execution_history]
        
        return {
            'avg_participation_rate': np.mean(participation_rates),
            'std_participation_rate': np.std(participation_rates),
            'avg_window_size': np.mean(window_sizes),
            'std_window_size': np.std(window_sizes),
            'avg_cost': np.mean(costs),
            'std_cost': np.std(costs),
            'sample_count': len(self.execution_history)
        } 