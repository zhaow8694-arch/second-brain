from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from collections import deque

from .market_impact_analyzer import MarketImpactAnalyzer, MarketCondition, ImpactCost

@dataclass
class ExecutionWindow:
    """执行时间窗口"""
    start_time: datetime  # 开始时间
    end_time: datetime    # 结束时间
    optimal_time: datetime  # 最优执行时间
    expected_cost: float  # 预期成本
    confidence: float     # 预测置信度

@dataclass
class ExecutionSpeed:
    """执行速度建议"""
    base_speed: float     # 基础执行速度（每分钟）
    min_speed: float      # 最小执行速度
    max_speed: float      # 最大执行速度
    current_speed: float  # 当前建议速度

@dataclass
class MarketTiming:
    """市场时机评估"""
    score: float         # 市场时机得分 (0-1)
    volatility_score: float  # 波动率评分
    spread_score: float     # 价差评分
    volume_score: float     # 成交量评分
    imbalance_score: float  # 买卖失衡评分

class TimingOptimizer:
    def __init__(self,
                 impact_analyzer: MarketImpactAnalyzer,
                 min_execution_time: int = 5,    # 最小执行时间（分钟）
                 max_execution_time: int = 120,  # 最大执行时间（分钟）
                 time_window_size: int = 60,     # 时间窗口大小（分钟）
                 volatility_weight: float = 0.3, # 波动率权重
                 spread_weight: float = 0.2,     # 价差权重
                 volume_weight: float = 0.3,     # 成交量权重
                 imbalance_weight: float = 0.2): # 买卖失衡权重
        """
        初始化执行时机优化器
        
        Args:
            impact_analyzer: 市场冲击成本分析器实例
            min_execution_time: 最小执行时间（分钟）
            max_execution_time: 最大执行时间（分钟）
            time_window_size: 时间窗口大小（分钟）
            volatility_weight: 波动率权重
            spread_weight: 价差权重
            volume_weight: 成交量权重
            imbalance_weight: 买卖失衡权重
        """
        self.impact_analyzer = impact_analyzer
        self.min_execution_time = min_execution_time
        self.max_execution_time = max_execution_time
        self.time_window_size = time_window_size
        
        # 权重设置
        self.weights = {
            'volatility': volatility_weight,
            'spread': spread_weight,
            'volume': volume_weight,
            'imbalance': imbalance_weight
        }
        
        # 历史评分
        self.timing_scores: deque = deque(maxlen=100)
        
    def _calculate_volatility_score(self, 
                                  market_condition: MarketCondition,
                                  side: str) -> float:
        """计算波动率评分"""
        if not market_condition:
            return 0.5
            
        # 根据交易方向评估波动率
        # 买入时希望波动率较低，卖出时可以接受较高波动率
        vol_score = 1.0 / (1.0 + market_condition.volatility * 10)
        return vol_score if side.lower() == "buy" else (1 - vol_score)
        
    def _calculate_spread_score(self,
                              market_condition: MarketCondition) -> float:
        """计算价差评分"""
        if not market_condition or market_condition.avg_volume == 0:
            return 0.5
            
        # 相对价差（相对于平均成交量）
        relative_spread = market_condition.avg_spread / market_condition.avg_volume
        return 1.0 / (1.0 + relative_spread * 100)
        
    def _calculate_volume_score(self,
                              market_condition: MarketCondition) -> float:
        """计算成交量评分"""
        if not market_condition:
            return 0.5
            
        # 当前小时的成交量比例
        current_hour = datetime.now().hour
        current_vol_ratio = market_condition.volume_profile.get(current_hour, 0)
        avg_vol_ratio = 1.0 / len(market_condition.volume_profile) if market_condition.volume_profile else 0
        
        return min(1.0, current_vol_ratio / avg_vol_ratio) if avg_vol_ratio > 0 else 0.5
        
    def _calculate_imbalance_score(self,
                                 market_condition: MarketCondition,
                                 side: str) -> float:
        """计算买卖失衡评分"""
        if not market_condition:
            return 0.5
            
        # 根据交易方向评估买卖失衡
        imbalance = market_condition.bid_ask_imbalance
        if side.lower() == "buy":
            # 买入时希望卖盘较厚
            return (1 - imbalance) / 2
        else:
            # 卖出时希望买盘较厚
            return (1 + imbalance) / 2
            
    def evaluate_market_timing(self,
                             market_condition: MarketCondition,
                             side: str) -> MarketTiming:
        """评估市场时机"""
        # 计算各项评分
        volatility_score = self._calculate_volatility_score(market_condition, side)
        spread_score = self._calculate_spread_score(market_condition)
        volume_score = self._calculate_volume_score(market_condition)
        imbalance_score = self._calculate_imbalance_score(market_condition, side)
        
        # 计算加权总分
        total_score = (
            self.weights['volatility'] * volatility_score +
            self.weights['spread'] * spread_score +
            self.weights['volume'] * volume_score +
            self.weights['imbalance'] * imbalance_score
        )
        
        timing = MarketTiming(
            score=total_score,
            volatility_score=volatility_score,
            spread_score=spread_score,
            volume_score=volume_score,
            imbalance_score=imbalance_score
        )
        
        self.timing_scores.append(timing)
        return timing
        
    def _estimate_optimal_time(self,
                             market_condition: MarketCondition,
                             size: float,
                             side: str,
                             start_time: datetime,
                             end_time: datetime) -> Tuple[datetime, float]:
        """估计最优执行时间"""
        if not market_condition:
            return start_time, 0.0
            
        best_time = start_time
        min_cost = float('inf')
        current_time = start_time
        
        # 在时间窗口内搜索最优时间点
        while current_time <= end_time:
            # 计算该时间点的成本
            hour = current_time.hour
            vol_ratio = market_condition.volume_profile.get(hour, 0)
            
            # 基于成交量分布调整紧急度
            urgency = 1.0 - vol_ratio
            
            # 估算该时间点的冲击成本
            impact_cost = asyncio.run(self.impact_analyzer.estimate_impact_cost(
                size=size,
                side=side,
                urgency=urgency
            ))
            
            if impact_cost.total_cost < min_cost:
                min_cost = impact_cost.total_cost
                best_time = current_time
                
            current_time += timedelta(minutes=5)
            
        return best_time, min_cost
        
    async def get_execution_window(self,
                                 size: float,
                                 side: str,
                                 max_cost: Optional[float] = None) -> ExecutionWindow:
        """获取执行时间窗口"""
        current_time = datetime.now()
        start_time = current_time
        end_time = current_time + timedelta(minutes=self.time_window_size)
        
        if not self.impact_analyzer.current_condition:
            return ExecutionWindow(
                start_time=start_time,
                end_time=end_time,
                optimal_time=start_time,
                expected_cost=0.0,
                confidence=0.0
            )
            
        # 估计最优执行时间和成本
        optimal_time, expected_cost = self._estimate_optimal_time(
            market_condition=self.impact_analyzer.current_condition,
            size=size,
            side=side,
            start_time=start_time,
            end_time=end_time
        )
        
        # 如果成本超过限制，调整执行窗口
        if max_cost is not None and expected_cost > max_cost:
            # 扩大执行窗口以降低成本
            end_time += timedelta(minutes=self.time_window_size)
            optimal_time, expected_cost = self._estimate_optimal_time(
                market_condition=self.impact_analyzer.current_condition,
                size=size,
                side=side,
                start_time=start_time,
                end_time=end_time
            )
            
        # 计算置信度
        timing = self.evaluate_market_timing(
            self.impact_analyzer.current_condition,
            side
        )
        confidence = timing.score * self.impact_analyzer.current_condition.avg_volume / size
        
        return ExecutionWindow(
            start_time=start_time,
            end_time=end_time,
            optimal_time=optimal_time,
            expected_cost=expected_cost,
            confidence=min(1.0, confidence)
        )
        
    def calculate_execution_speed(self,
                                size: float,
                                remaining_time: float,
                                market_timing: MarketTiming) -> ExecutionSpeed:
        """计算执行速度"""
        if remaining_time <= 0:
            return ExecutionSpeed(0.0, 0.0, 0.0, 0.0)
            
        # 计算基础速度
        base_speed = size / remaining_time
        
        # 根据市场时机调整速度范围
        speed_range = 0.5  # 允许速度变化的范围（±50%）
        min_speed = base_speed * (1 - speed_range * market_timing.score)
        max_speed = base_speed * (1 + speed_range * market_timing.score)
        
        # 根据当前市场时机评分调整执行速度
        current_speed = base_speed * (1 + (market_timing.score - 0.5) * speed_range)
        
        return ExecutionSpeed(
            base_speed=base_speed,
            min_speed=min_speed,
            max_speed=max_speed,
            current_speed=current_speed
        )
        
    def get_execution_stats(self) -> Dict:
        """获取执行统计信息"""
        if not self.timing_scores:
            return {}
            
        scores = [t.score for t in self.timing_scores]
        return {
            'avg_timing_score': np.mean(scores),
            'std_timing_score': np.std(scores),
            'max_timing_score': np.max(scores),
            'min_timing_score': np.min(scores),
            'sample_count': len(scores)
        } 