import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass

@dataclass
class VenueMetrics:
    """交易所评分指标"""
    liquidity_score: float  # 流动性评分
    execution_speed: float  # 执行速度（毫秒）
    historical_slippage: float  # 历史滑点
    trading_cost: float  # 交易成本
    success_rate: float  # 成功率
    
@dataclass
class OrderRouteResult:
    """订单路由结果"""
    venue_allocations: Dict[str, float]  # 各交易所分配比例
    estimated_cost: float  # 预估成本
    estimated_slippage: float  # 预估滑点
    execution_time: float  # 预估执行时间
    
class SmartOrderRouter:
    def __init__(self, 
                 min_venue_count: int = 2,
                 max_venue_count: int = 5,
                 slippage_threshold: float = 0.001,
                 cost_threshold: float = 0.002,
                 update_interval: int = 60):
        """
        初始化智能订单路由器
        
        Args:
            min_venue_count: 最小交易所数量
            max_venue_count: 最大交易所数量
            slippage_threshold: 滑点阈值
            cost_threshold: 成本阈值
            update_interval: 指标更新间隔（秒）
        """
        self.min_venue_count = min_venue_count
        self.max_venue_count = max_venue_count
        self.slippage_threshold = slippage_threshold
        self.cost_threshold = cost_threshold
        self.update_interval = update_interval
        
        # 交易所指标
        self.venue_metrics: Dict[str, VenueMetrics] = {}
        # 交易所权重
        self.venue_weights: Dict[str, float] = {}
        # 最近更新时间
        self.last_update: Optional[datetime] = None
        
    async def update_venue_metrics(self, venue: str, metrics: VenueMetrics):
        """更新交易所指标"""
        self.venue_metrics[venue] = metrics
        await self._update_venue_weights()
        
    async def _update_venue_weights(self):
        """更新交易所权重"""
        if not self.venue_metrics:
            return
            
        weights = {}
        total_score = 0
        
        for venue, metrics in self.venue_metrics.items():
            # 计算综合得分
            score = (
                0.3 * metrics.liquidity_score +
                0.2 * (1 / (metrics.execution_speed + 1)) +
                0.2 * (1 - metrics.historical_slippage) +
                0.2 * (1 - metrics.trading_cost) +
                0.1 * metrics.success_rate
            )
            weights[venue] = score
            total_score += score
            
        # 归一化权重
        if total_score > 0:
            self.venue_weights = {
                venue: weight / total_score 
                for venue, weight in weights.items()
            }
        
        self.last_update = datetime.now()
        
    def _calculate_optimal_split(self, 
                               order_size: float,
                               max_slippage: float) -> Dict[str, float]:
        """计算最优订单分配"""
        if not self.venue_weights:
            return {}
            
        # 按权重排序交易所
        sorted_venues = sorted(
            self.venue_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 选择前N个交易所
        n = min(
            max(self.min_venue_count,
                int(len(sorted_venues) * 0.6)),
            self.max_venue_count
        )
        selected_venues = sorted_venues[:n]
        
        # 重新归一化权重
        total_weight = sum(weight for _, weight in selected_venues)
        allocations = {
            venue: (weight / total_weight) * order_size
            for venue, weight in selected_venues
        }
        
        return allocations
        
    async def route_order(self,
                         symbol: str,
                         side: str,
                         size: float,
                         max_slippage: Optional[float] = None) -> OrderRouteResult:
        """
        路由订单到最优交易所组合
        
        Args:
            symbol: 交易对
            side: 买/卖方向
            size: 订单数量
            max_slippage: 最大允许滑点
            
        Returns:
            OrderRouteResult: 订单路由结果
        """
        # 检查是否需要更新指标
        if (self.last_update is None or
            (datetime.now() - self.last_update).seconds > self.update_interval):
            await self._update_venue_weights()
            
        # 使用默认滑点阈值
        if max_slippage is None:
            max_slippage = self.slippage_threshold
            
        # 计算订单分配
        allocations = self._calculate_optimal_split(size, max_slippage)
        
        # 计算预估指标
        estimated_cost = 0
        estimated_slippage = 0
        max_execution_time = 0
        
        for venue, amount in allocations.items():
            metrics = self.venue_metrics[venue]
            estimated_cost += amount * metrics.trading_cost
            estimated_slippage += amount * metrics.historical_slippage
            max_execution_time = max(max_execution_time, metrics.execution_speed)
            
        return OrderRouteResult(
            venue_allocations=allocations,
            estimated_cost=estimated_cost,
            estimated_slippage=estimated_slippage,
            execution_time=max_execution_time
        )
        
    async def get_venue_metrics(self, venue: str) -> Optional[VenueMetrics]:
        """获取交易所指标"""
        return self.venue_metrics.get(venue)
        
    async def get_all_venue_metrics(self) -> Dict[str, VenueMetrics]:
        """获取所有交易所指标"""
        return self.venue_metrics.copy()
        
    async def get_venue_weights(self) -> Dict[str, float]:
        """获取交易所权重"""
        return self.venue_weights.copy() 