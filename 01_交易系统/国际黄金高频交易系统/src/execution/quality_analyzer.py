from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from collections import deque

from .market_impact_analyzer import MarketImpactAnalyzer, ImpactCost
from .timing_optimizer import TimingOptimizer, MarketTiming, ExecutionWindow

@dataclass
class ExecutionMetrics:
    """执行指标"""
    implementation_shortfall: float  # 执行成本（相对于决策价格）
    market_impact: float            # 市场冲击成本
    timing_cost: float             # 时机选择成本
    delay_cost: float              # 延迟成本
    total_cost: float              # 总成本
    fill_rate: float               # 成交率
    participation_rate: float       # 参与率
    price_reversion: float         # 价格回复
    confidence: float              # 指标置信度

@dataclass
class BenchmarkMetrics:
    """基准指标"""
    vwap_deviation: float          # 相对VWAP偏差
    arrival_price_deviation: float  # 相对到达价偏差
    close_price_deviation: float    # 相对收盘价偏差
    spread_capture: float          # 价差捕获率
    timing_score: float            # 时机选择得分

@dataclass
class QualityReport:
    """质量报告"""
    execution_metrics: ExecutionMetrics  # 执行指标
    benchmark_metrics: BenchmarkMetrics  # 基准指标
    market_conditions: Dict             # 市场条件
    optimization_suggestions: List[str]  # 优化建议

class QualityAnalyzer:
    def __init__(self,
                 impact_analyzer: MarketImpactAnalyzer,
                 timing_optimizer: TimingOptimizer,
                 metrics_window: int = 100,      # 指标窗口大小
                 vwap_weight: float = 0.4,       # VWAP权重
                 arrival_weight: float = 0.3,    # 到达价权重
                 close_weight: float = 0.3):     # 收盘价权重
        """
        初始化执行质量分析器
        
        Args:
            impact_analyzer: 市场冲击成本分析器实例
            timing_optimizer: 执行时机优化器实例
            metrics_window: 指标窗口大小
            vwap_weight: VWAP权重
            arrival_weight: 到达价权重
            close_weight: 收盘价权重
        """
        self.impact_analyzer = impact_analyzer
        self.timing_optimizer = timing_optimizer
        self.metrics_window = metrics_window
        
        # 权重设置
        self.weights = {
            'vwap': vwap_weight,
            'arrival': arrival_weight,
            'close': close_weight
        }
        
        # 历史指标
        self.execution_history: deque = deque(maxlen=metrics_window)
        self.benchmark_history: deque = deque(maxlen=metrics_window)
        
    def _calculate_implementation_shortfall(self,
                                         decision_price: float,
                                         executed_price: float,
                                         size: float,
                                         side: str) -> float:
        """计算执行成本"""
        sign = 1 if side.lower() == "buy" else -1
        return sign * (executed_price - decision_price) / decision_price * size
        
    def _calculate_market_impact(self,
                               pre_trade_price: float,
                               executed_price: float,
                               size: float,
                               side: str) -> float:
        """计算市场冲击"""
        sign = 1 if side.lower() == "buy" else -1
        return sign * (executed_price - pre_trade_price) / pre_trade_price * size
        
    def _calculate_timing_cost(self,
                             executed_price: float,
                             vwap_price: float,
                             size: float) -> float:
        """计算时机成本"""
        return abs(executed_price - vwap_price) / vwap_price * size
        
    def _calculate_delay_cost(self,
                            optimal_time: datetime,
                            execution_time: datetime,
                            market_timing: MarketTiming,
                            executed_price: float,
                            market_price: float) -> float:
        """计算延迟成本"""
        time_diff = (execution_time - optimal_time).total_seconds() / 60.0  # 转换为分钟
        price_impact = abs(executed_price - market_price) / market_price
        
        return time_diff * price_impact * (1 - market_timing.score)
        
    def _calculate_fill_rate(self,
                           executed_size: float,
                           target_size: float) -> float:
        """计算成交率"""
        return executed_size / target_size if target_size > 0 else 0.0
        
    def _calculate_participation_rate(self,
                                   executed_size: float,
                                   market_volume: float) -> float:
        """计算参与率"""
        return executed_size / market_volume if market_volume > 0 else 0.0
        
    def _calculate_price_reversion(self,
                                 executed_price: float,
                                 post_trade_price: float,
                                 side: str) -> float:
        """计算价格回复"""
        sign = 1 if side.lower() == "buy" else -1
        return sign * (post_trade_price - executed_price) / executed_price
        
    def _calculate_benchmark_deviations(self,
                                      executed_price: float,
                                      vwap_price: float,
                                      arrival_price: float,
                                      close_price: float) -> Tuple[float, float, float]:
        """计算基准偏差"""
        vwap_dev = (executed_price - vwap_price) / vwap_price
        arrival_dev = (executed_price - arrival_price) / arrival_price
        close_dev = (executed_price - close_price) / close_price
        
        return vwap_dev, arrival_dev, close_dev
        
    def _calculate_spread_capture(self,
                                executed_price: float,
                                bid_price: float,
                                ask_price: float,
                                side: str) -> float:
        """计算价差捕获率"""
        spread = ask_price - bid_price
        if spread <= 0:
            return 0.0
            
        if side.lower() == "buy":
            return (ask_price - executed_price) / spread
        else:
            return (executed_price - bid_price) / spread
            
    def _generate_optimization_suggestions(self,
                                        metrics: ExecutionMetrics,
                                        benchmarks: BenchmarkMetrics,
                                        market_timing: MarketTiming) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 分析执行成本
        if metrics.implementation_shortfall > 0.001:  # 10bp
            suggestions.append("建议: 考虑增加执行时间窗口，减少市场冲击")
            
        if metrics.market_impact > 0.0005:  # 5bp
            suggestions.append("建议: 考虑降低参与率，减少市场冲击")
            
        if metrics.timing_cost > 0.0003:  # 3bp
            suggestions.append("建议: 优化执行时机选择，关注成交量分布")
            
        # 分析基准偏差
        if abs(benchmarks.vwap_deviation) > 0.0002:  # 2bp
            suggestions.append("建议: 调整执行速度，更好地跟踪VWAP")
            
        if benchmarks.timing_score < 0.6:
            suggestions.append("建议: 改善市场时机选择，关注市场条件变化")
            
        # 分析市场条件
        if market_timing.volatility_score < 0.4:
            suggestions.append("建议: 在波动率较低时执行大单")
            
        if market_timing.spread_score < 0.5:
            suggestions.append("建议: 等待价差收窄时执行")
            
        return suggestions
        
    async def analyze_execution(self,
                              order_id: str,
                              decision_price: float,
                              executed_price: float,
                              executed_size: float,
                              target_size: float,
                              side: str,
                              execution_time: datetime,
                              execution_window: ExecutionWindow,
                              market_data: Dict) -> QualityReport:
        """
        分析执行质量
        
        Args:
            order_id: 订单ID
            decision_price: 决策价格
            executed_price: 执行价格
            executed_size: 执行数量
            target_size: 目标数量
            side: 交易方向
            execution_time: 执行时间
            execution_window: 执行窗口
            market_data: 市场数据
            
        Returns:
            QualityReport: 质量报告
        """
        # 提取市场数据
        pre_trade_price = market_data.get('pre_trade_price', decision_price)
        post_trade_price = market_data.get('post_trade_price', executed_price)
        vwap_price = market_data.get('vwap_price', executed_price)
        arrival_price = market_data.get('arrival_price', decision_price)
        close_price = market_data.get('close_price', post_trade_price)
        market_volume = market_data.get('market_volume', 0.0)
        bid_price = market_data.get('bid_price', executed_price * 0.9999)
        ask_price = market_data.get('ask_price', executed_price * 1.0001)
        
        # 获取市场时机评估
        market_timing = self.timing_optimizer.evaluate_market_timing(
            self.impact_analyzer.current_condition,
            side
        )
        
        # 计算执行指标
        implementation_shortfall = self._calculate_implementation_shortfall(
            decision_price, executed_price, executed_size, side
        )
        
        market_impact = self._calculate_market_impact(
            pre_trade_price, executed_price, executed_size, side
        )
        
        timing_cost = self._calculate_timing_cost(
            executed_price, vwap_price, executed_size
        )
        
        delay_cost = self._calculate_delay_cost(
            execution_window.optimal_time,
            execution_time,
            market_timing,
            executed_price,
            pre_trade_price
        )
        
        fill_rate = self._calculate_fill_rate(executed_size, target_size)
        participation_rate = self._calculate_participation_rate(executed_size, market_volume)
        price_reversion = self._calculate_price_reversion(executed_price, post_trade_price, side)
        
        # 计算基准偏差
        vwap_dev, arrival_dev, close_dev = self._calculate_benchmark_deviations(
            executed_price, vwap_price, arrival_price, close_price
        )
        
        spread_capture = self._calculate_spread_capture(
            executed_price, bid_price, ask_price, side
        )
        
        # 创建指标对象
        execution_metrics = ExecutionMetrics(
            implementation_shortfall=implementation_shortfall,
            market_impact=market_impact,
            timing_cost=timing_cost,
            delay_cost=delay_cost,
            total_cost=implementation_shortfall + market_impact + timing_cost + delay_cost,
            fill_rate=fill_rate,
            participation_rate=participation_rate,
            price_reversion=price_reversion,
            confidence=market_timing.score
        )
        
        benchmark_metrics = BenchmarkMetrics(
            vwap_deviation=vwap_dev,
            arrival_price_deviation=arrival_dev,
            close_price_deviation=close_dev,
            spread_capture=spread_capture,
            timing_score=market_timing.score
        )
        
        # 生成优化建议
        suggestions = self._generate_optimization_suggestions(
            execution_metrics,
            benchmark_metrics,
            market_timing
        )
        
        # 更新历史记录
        self.execution_history.append(execution_metrics)
        self.benchmark_history.append(benchmark_metrics)
        
        # 创建报告
        report = QualityReport(
            execution_metrics=execution_metrics,
            benchmark_metrics=benchmark_metrics,
            market_conditions={
                'volatility': market_timing.volatility_score,
                'spread': market_timing.spread_score,
                'volume': market_timing.volume_score,
                'imbalance': market_timing.imbalance_score
            },
            optimization_suggestions=suggestions
        )
        
        return report
        
    def get_historical_metrics(self) -> Dict:
        """获取历史指标统计"""
        if not self.execution_history:
            return {}
            
        # 计算执行指标统计
        total_costs = [m.total_cost for m in self.execution_history]
        fill_rates = [m.fill_rate for m in self.execution_history]
        participation_rates = [m.participation_rate for m in self.execution_history]
        
        # 计算基准指标统计
        vwap_devs = [m.vwap_deviation for m in self.benchmark_history]
        timing_scores = [m.timing_score for m in self.benchmark_history]
        
        return {
            'avg_total_cost': np.mean(total_costs),
            'std_total_cost': np.std(total_costs),
            'avg_fill_rate': np.mean(fill_rates),
            'avg_participation_rate': np.mean(participation_rates),
            'avg_vwap_deviation': np.mean(vwap_devs),
            'avg_timing_score': np.mean(timing_scores),
            'sample_count': len(self.execution_history)
        } 