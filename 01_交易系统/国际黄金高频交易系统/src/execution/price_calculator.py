from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from .slippage_predictor import SlippagePredictor, MarketState, SlippageMetrics

@dataclass
class PriceRange:
    """价格范围"""
    optimal_price: float  # 最优执行价格
    min_price: float  # 最低可接受价格
    max_price: float  # 最高可接受价格
    confidence: float  # 价格区间置信度

@dataclass
class MarketDepthInfo:
    """市场深度信息"""
    total_bid_volume: float  # 买单总量
    total_ask_volume: float  # 卖单总量
    bid_depth: Dict[float, float]  # 买单深度
    ask_depth: Dict[float, float]  # 卖单深度
    weighted_bid_price: float  # 加权买价
    weighted_ask_price: float  # 加权卖价

class DynamicPriceCalculator:
    def __init__(self,
                 slippage_predictor: SlippagePredictor,
                 max_price_deviation: float = 0.01,  # 最大价格偏离
                 confidence_threshold: float = 0.7,  # 置信度阈值
                 depth_impact_factor: float = 0.5,  # 深度影响因子
                 urgency_multiplier: float = 1.5):  # 紧急度乘数
        """
        初始化动态限价计算器
        
        Args:
            slippage_predictor: 滑点预测器实例
            max_price_deviation: 最大价格偏离比例
            confidence_threshold: 最小置信度要求
            depth_impact_factor: 深度影响因子
            urgency_multiplier: 紧急度乘数
        """
        self.slippage_predictor = slippage_predictor
        self.max_price_deviation = max_price_deviation
        self.confidence_threshold = confidence_threshold
        self.depth_impact_factor = depth_impact_factor
        self.urgency_multiplier = urgency_multiplier
        
    def _calculate_weighted_price(self,
                                depths: Dict[float, float],
                                total_volume: float) -> float:
        """计算加权价格"""
        if not depths or total_volume == 0:
            return 0.0
            
        weighted_sum = sum(price * volume for price, volume in depths.items())
        return weighted_sum / total_volume
        
    def _analyze_market_depth(self,
                            bid_depths: Dict[float, float],
                            ask_depths: Dict[float, float]) -> MarketDepthInfo:
        """分析市场深度"""
        # 计算总量
        total_bid_volume = sum(bid_depths.values())
        total_ask_volume = sum(ask_depths.values())
        
        # 计算加权价格
        weighted_bid_price = self._calculate_weighted_price(
            bid_depths, total_bid_volume)
        weighted_ask_price = self._calculate_weighted_price(
            ask_depths, total_ask_volume)
            
        return MarketDepthInfo(
            total_bid_volume=total_bid_volume,
            total_ask_volume=total_ask_volume,
            bid_depth=bid_depths,
            ask_depth=ask_depths,
            weighted_bid_price=weighted_bid_price,
            weighted_ask_price=weighted_ask_price
        )
        
    def _adjust_price_for_depth(self,
                              base_price: float,
                              size: float,
                              side: str,
                              depth_info: MarketDepthInfo) -> float:
        """根据市场深度调整价格"""
        if side.lower() == "buy":
            relevant_volume = depth_info.total_ask_volume
            weighted_price = depth_info.weighted_ask_price
        else:
            relevant_volume = depth_info.total_bid_volume
            weighted_price = depth_info.weighted_bid_price
            
        # 计算订单大小对深度的影响
        volume_impact = min(1.0, size / relevant_volume)
        
        # 调整价格
        price_adjustment = (weighted_price - base_price) * volume_impact * self.depth_impact_factor
        return base_price + price_adjustment
        
    async def calculate_limit_price(self,
                                  current_price: float,
                                  size: float,
                                  side: str,
                                  urgency: float,
                                  bid_depths: Dict[float, float],
                                  ask_depths: Dict[float, float]) -> PriceRange:
        """
        计算限价范围
        
        Args:
            current_price: 当前市场价格
            size: 订单数量
            side: 交易方向 ("buy" or "sell")
            urgency: 执行紧急度 (0-1)
            bid_depths: 买单深度 {price: volume}
            ask_depths: 卖单深度 {price: volume}
            
        Returns:
            PriceRange: 计算出的价格范围
        """
        # 获取滑点预测
        slippage_metrics = await self.slippage_predictor.predict_slippage(
            size=size,
            urgency=urgency
        )
        
        # 分析市场深度
        depth_info = self._analyze_market_depth(bid_depths, ask_depths)
        
        # 计算基础价格范围
        expected_slippage = slippage_metrics.expected_slippage
        base_deviation = expected_slippage * (1 + urgency * self.urgency_multiplier)
        
        if side.lower() == "buy":
            base_price = current_price * (1 + expected_slippage)
            price_range = (
                current_price * (1 - base_deviation),  # min price
                current_price * (1 + base_deviation * 2)  # max price
            )
        else:  # sell
            base_price = current_price * (1 - expected_slippage)
            price_range = (
                current_price * (1 - base_deviation * 2),  # min price
                current_price * (1 + base_deviation)  # max price
            )
            
        # 根据市场深度调整价格
        optimal_price = self._adjust_price_for_depth(
            base_price, size, side, depth_info)
            
        # 确保价格在允许范围内
        optimal_price = min(max(optimal_price, price_range[0]), price_range[1])
        
        # 计算置信度
        confidence = min(
            slippage_metrics.confidence,
            1 - abs(optimal_price - current_price) / (current_price * self.max_price_deviation)
        )
        
        return PriceRange(
            optimal_price=optimal_price,
            min_price=price_range[0],
            max_price=price_range[1],
            confidence=confidence
        )
        
    def get_price_adjustment_factors(self) -> Dict:
        """获取价格调整因子"""
        return {
            'max_price_deviation': self.max_price_deviation,
            'confidence_threshold': self.confidence_threshold,
            'depth_impact_factor': self.depth_impact_factor,
            'urgency_multiplier': self.urgency_multiplier
        }
        
    def update_adjustment_factors(self,
                                max_price_deviation: Optional[float] = None,
                                confidence_threshold: Optional[float] = None,
                                depth_impact_factor: Optional[float] = None,
                                urgency_multiplier: Optional[float] = None):
        """更新价格调整因子"""
        if max_price_deviation is not None:
            self.max_price_deviation = max_price_deviation
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        if depth_impact_factor is not None:
            self.depth_impact_factor = depth_impact_factor
        if urgency_multiplier is not None:
            self.urgency_multiplier = urgency_multiplier 