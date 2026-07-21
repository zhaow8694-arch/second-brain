import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor
from collections import deque

@dataclass
class MarketState:
    """市场状态"""
    timestamp: datetime
    price: float
    volume: float
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float
    volatility: float  # 短期波动率
    spread: float  # 买卖价差
    order_imbalance: float  # 订单失衡度

@dataclass
class SlippageMetrics:
    """滑点指标"""
    expected_slippage: float  # 预期滑点
    confidence: float  # 预测置信度
    market_impact: float  # 市场冲击
    timing_cost: float  # 时机成本
    
class SlippagePredictor:
    def __init__(self,
                 lookback_window: int = 100,
                 volatility_window: int = 20,
                 update_interval: int = 60,
                 min_samples: int = 50):
        """
        初始化滑点预测器
        
        Args:
            lookback_window: 历史数据窗口大小
            volatility_window: 波动率计算窗口
            update_interval: 模型更新间隔（秒）
            min_samples: 训练所需最小样本数
        """
        self.lookback_window = lookback_window
        self.volatility_window = volatility_window
        self.update_interval = update_interval
        self.min_samples = min_samples
        
        # 历史数据
        self.market_states = deque(maxlen=lookback_window)
        self.execution_history: List[Dict] = []
        
        # 预测模型
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        # 最近更新时间
        self.last_update: Optional[datetime] = None
        
    def _calculate_volatility(self, prices: List[float]) -> float:
        """计算波动率"""
        if len(prices) < 2:
            return 0.0
        returns = np.diff(np.log(prices))
        return np.std(returns) * np.sqrt(252)  # 年化波动率
        
    def _calculate_order_imbalance(self, 
                                 bid_volume: float,
                                 ask_volume: float) -> float:
        """计算订单失衡度"""
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.0
        return (bid_volume - ask_volume) / total_volume
        
    async def update_market_state(self,
                                timestamp: datetime,
                                price: float,
                                volume: float,
                                bid_price: float,
                                ask_price: float,
                                bid_volume: float,
                                ask_volume: float):
        """更新市场状态"""
        # 计算波动率
        prices = [state.price for state in self.market_states]
        prices.append(price)
        volatility = self._calculate_volatility(prices[-self.volatility_window:])
        
        # 计算其他指标
        spread = (ask_price - bid_price) / price
        order_imbalance = self._calculate_order_imbalance(bid_volume, ask_volume)
        
        # 创建市场状态
        state = MarketState(
            timestamp=timestamp,
            price=price,
            volume=volume,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            volatility=volatility,
            spread=spread,
            order_imbalance=order_imbalance
        )
        
        self.market_states.append(state)
        
        # 检查是否需要更新模型
        if (self.last_update is None or
            (timestamp - self.last_update).seconds > self.update_interval):
            await self._update_model()
            
    async def add_execution_result(self,
                                 timestamp: datetime,
                                 size: float,
                                 expected_price: float,
                                 executed_price: float,
                                 market_price: float):
        """添加执行结果"""
        result = {
            'timestamp': timestamp,
            'size': size,
            'expected_price': expected_price,
            'executed_price': executed_price,
            'market_price': market_price,
            'slippage': (executed_price - expected_price) / expected_price
        }
        
        self.execution_history.append(result)
        
    def _prepare_features(self, state: MarketState, size: float) -> np.ndarray:
        """准备特征数据"""
        return np.array([
            state.volatility,
            state.spread,
            state.order_imbalance,
            size / state.volume,  # 相对订单大小
            state.bid_volume / state.ask_volume,  # 买卖盘比例
            state.volume  # 成交量
        ]).reshape(1, -1)
        
    async def _update_model(self):
        """更新预测模型"""
        if len(self.execution_history) < self.min_samples:
            return
            
        # 准备训练数据
        X = []
        y = []
        
        for result in self.execution_history[-self.min_samples:]:
            # 找到对应时间的市场状态
            state = None
            for s in self.market_states:
                if s.timestamp <= result['timestamp']:
                    state = s
                    break
                    
            if state is None:
                continue
                
            # 添加特征和标签
            X.append(self._prepare_features(state, result['size']).flatten())
            y.append(result['slippage'])
            
        if len(X) < self.min_samples:
            return
            
        # 训练模型
        X = np.array(X)
        y = np.array(y)
        self.model.fit(X, y)
        self.last_update = datetime.now()
        
    async def predict_slippage(self, 
                             size: float,
                             urgency: float = 0.5) -> SlippageMetrics:
        """
        预测滑点
        
        Args:
            size: 订单数量
            urgency: 执行紧急度 (0-1)
            
        Returns:
            SlippageMetrics: 滑点预测指标
        """
        if not self.market_states:
            return SlippageMetrics(0.0, 0.0, 0.0, 0.0)
            
        current_state = self.market_states[-1]
        features = self._prepare_features(current_state, size)
        
        # 预测基础滑点
        if len(self.execution_history) >= self.min_samples:
            base_slippage = self.model.predict(features)[0]
            confidence = 0.8  # 可以通过模型方差等方式计算实际置信度
        else:
            # 使用启发式方法
            base_slippage = current_state.spread / 2
            confidence = 0.5
            
        # 计算市场冲击
        relative_size = size / current_state.volume
        market_impact = relative_size * current_state.volatility
        
        # 计算时机成本
        timing_cost = current_state.spread * urgency
        
        # 总滑点
        expected_slippage = (
            base_slippage +
            market_impact * (1 + urgency) +
            timing_cost
        )
        
        return SlippageMetrics(
            expected_slippage=expected_slippage,
            confidence=confidence,
            market_impact=market_impact,
            timing_cost=timing_cost
        )
        
    def get_historical_slippage(self) -> Dict:
        """获取历史滑点统计"""
        if not self.execution_history:
            return {}
            
        slippages = [r['slippage'] for r in self.execution_history]
        return {
            'mean': np.mean(slippages),
            'std': np.std(slippages),
            'min': np.min(slippages),
            'max': np.max(slippages),
            'median': np.median(slippages)
        } 