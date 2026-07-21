from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from collections import deque

@dataclass
class ImpactCost:
    """市场冲击成本"""
    temporary_impact: float  # 临时性冲击成本
    permanent_impact: float  # 永久性冲击成本
    timing_cost: float  # 时机成本
    total_cost: float  # 总成本
    confidence: float  # 预测置信度

@dataclass
class MarketCondition:
    """市场状态"""
    volatility: float  # 波动率
    avg_spread: float  # 平均价差
    avg_volume: float  # 平均成交量
    volume_profile: Dict[int, float]  # 成交量分布
    bid_ask_imbalance: float  # 买卖失衡度

class MarketImpactAnalyzer:
    def __init__(self,
                 lookback_window: int = 100,
                 volatility_window: int = 20,
                 decay_factor: float = 0.94,  # 衰减因子
                 impact_horizon: int = 30):  # 冲击影响期（分钟）
        """
        初始化市场冲击成本分析器
        
        Args:
            lookback_window: 历史数据窗口大小
            volatility_window: 波动率计算窗口
            decay_factor: 冲击衰减因子
            impact_horizon: 冲击影响期（分钟）
        """
        self.lookback_window = lookback_window
        self.volatility_window = volatility_window
        self.decay_factor = decay_factor
        self.impact_horizon = impact_horizon
        
        # 历史数据
        self.price_history = deque(maxlen=lookback_window)
        self.volume_history = deque(maxlen=lookback_window)
        self.spread_history = deque(maxlen=lookback_window)
        self.trade_history: List[Dict] = []
        
        # 市场状态
        self.current_condition: Optional[MarketCondition] = None
        
    def _calculate_volatility(self, prices: List[float]) -> float:
        """计算波动率"""
        if len(prices) < 2:
            return 0.0
        returns = np.diff(np.log(prices))
        return np.std(returns) * np.sqrt(252 * 1440)  # 年化分钟波动率
        
    def _calculate_volume_profile(self, volumes: List[float]) -> Dict[int, float]:
        """计算成交量分布"""
        if not volumes:
            return {}
            
        total_volume = sum(volumes)
        if total_volume == 0:
            return {}
            
        # 按时间段分组
        hourly_volumes = {}
        for i, vol in enumerate(volumes):
            hour = (i % 24)
            hourly_volumes[hour] = hourly_volumes.get(hour, 0) + vol
            
        # 计算占比
        return {h: v/total_volume for h, v in hourly_volumes.items()}
        
    async def update_market_data(self,
                               timestamp: datetime,
                               price: float,
                               volume: float,
                               bid_price: float,
                               ask_price: float,
                               bid_volume: float,
                               ask_volume: float):
        """更新市场数据"""
        # 更新历史数据
        self.price_history.append(price)
        self.volume_history.append(volume)
        self.spread_history.append(ask_price - bid_price)
        
        # 计算市场状态
        if len(self.price_history) >= self.volatility_window:
            volatility = self._calculate_volatility(list(self.price_history)[-self.volatility_window:])
            avg_spread = np.mean(list(self.spread_history))
            avg_volume = np.mean(list(self.volume_history))
            volume_profile = self._calculate_volume_profile(list(self.volume_history))
            
            total_volume = bid_volume + ask_volume
            bid_ask_imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
            
            self.current_condition = MarketCondition(
                volatility=volatility,
                avg_spread=avg_spread,
                avg_volume=avg_volume,
                volume_profile=volume_profile,
                bid_ask_imbalance=bid_ask_imbalance
            )
            
    async def add_trade_result(self,
                             timestamp: datetime,
                             size: float,
                             side: str,
                             expected_price: float,
                             executed_price: float,
                             market_price: float,
                             time_to_completion: float):
        """添加交易结果"""
        result = {
            'timestamp': timestamp,
            'size': size,
            'side': side,
            'expected_price': expected_price,
            'executed_price': executed_price,
            'market_price': market_price,
            'time_to_completion': time_to_completion,
            'price_impact': (executed_price - market_price) / market_price,
            'completion_time': time_to_completion
        }
        
        self.trade_history.append(result)
        
    def _estimate_temporary_impact(self,
                                 size: float,
                                 market_condition: MarketCondition) -> float:
        """估算临时性冲击"""
        if not market_condition or market_condition.avg_volume == 0:
            return 0.0
            
        # 基于订单大小和市场条件计算临时性冲击
        relative_size = size / market_condition.avg_volume
        spread_factor = market_condition.avg_spread / market_condition.avg_volume
        vol_factor = market_condition.volatility * np.sqrt(self.impact_horizon / 1440)
        
        return (
            relative_size * spread_factor * (1 + vol_factor) *
            (1 + abs(market_condition.bid_ask_imbalance))
        )
        
    def _estimate_permanent_impact(self,
                                 size: float,
                                 market_condition: MarketCondition) -> float:
        """估算永久性冲击"""
        if not market_condition or market_condition.avg_volume == 0:
            return 0.0
            
        # 基于历史交易数据和市场条件估算永久性冲击
        relative_size = size / market_condition.avg_volume
        base_impact = relative_size * market_condition.volatility
        
        # 应用衰减因子
        decay = self.decay_factor ** (self.impact_horizon / 60)
        return base_impact * (1 - decay)
        
    def _estimate_timing_cost(self,
                            size: float,
                            urgency: float,
                            market_condition: MarketCondition) -> float:
        """估算时机成本"""
        if not market_condition:
            return 0.0
            
        # 基于成交量分布和紧急度估算时机成本
        current_hour = datetime.now().hour
        volume_profile = market_condition.volume_profile
        
        # 计算当前时段的不利程度
        current_vol_ratio = volume_profile.get(current_hour, 0)
        avg_vol_ratio = 1.0 / len(volume_profile) if volume_profile else 0
        timing_penalty = max(0, (avg_vol_ratio - current_vol_ratio) / avg_vol_ratio)
        
        return timing_penalty * urgency * market_condition.avg_spread
        
    def _calculate_confidence(self,
                            size: float,
                            market_condition: MarketCondition) -> float:
        """计算预测置信度"""
        if not market_condition or market_condition.avg_volume == 0:
            return 0.0
            
        # 基于数据质量和市场条件计算置信度
        data_quality = min(1.0, len(self.price_history) / self.lookback_window)
        size_factor = 1 - min(1.0, size / (market_condition.avg_volume * 5))
        volatility_factor = 1 / (1 + market_condition.volatility * 10)
        
        return data_quality * size_factor * volatility_factor
        
    async def estimate_impact_cost(self,
                                 size: float,
                                 side: str,
                                 urgency: float = 0.5) -> ImpactCost:
        """
        估算市场冲击成本
        
        Args:
            size: 订单数量
            side: 交易方向
            urgency: 执行紧急度 (0-1)
            
        Returns:
            ImpactCost: 冲击成本估算
        """
        if not self.current_condition:
            return ImpactCost(0.0, 0.0, 0.0, 0.0, 0.0)
            
        # 计算各项成本
        temp_impact = self._estimate_temporary_impact(size, self.current_condition)
        perm_impact = self._estimate_permanent_impact(size, self.current_condition)
        timing_cost = self._estimate_timing_cost(size, urgency, self.current_condition)
        
        # 根据交易方向调整符号
        sign = 1 if side.lower() == "buy" else -1
        temp_impact *= sign
        perm_impact *= sign
        
        # 计算总成本和置信度
        total_cost = temp_impact + perm_impact + timing_cost
        confidence = self._calculate_confidence(size, self.current_condition)
        
        return ImpactCost(
            temporary_impact=temp_impact,
            permanent_impact=perm_impact,
            timing_cost=timing_cost,
            total_cost=total_cost,
            confidence=confidence
        )
        
    def get_historical_impact(self) -> Dict:
        """获取历史冲击统计"""
        if not self.trade_history:
            return {}
            
        impacts = [t['price_impact'] for t in self.trade_history]
        completion_times = [t['completion_time'] for t in self.trade_history]
        
        return {
            'avg_impact': np.mean(impacts),
            'std_impact': np.std(impacts),
            'max_impact': np.max(impacts),
            'min_impact': np.min(impacts),
            'avg_completion_time': np.mean(completion_times),
            'impact_decay': self.decay_factor,
            'sample_count': len(self.trade_history)
        } 