from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

class PricePressureStrategy(BaseStrategy):
    """价格压力策略"""
    
    def __init__(self,
                 symbol: str,
                 timeframe: str = '5m',
                 lookback_periods: int = 100,
                 support_resistance_periods: int = 20,  # 支撑阻力计算周期
                 price_levels_count: int = 3,  # 保留的价格水平数量
                 level_threshold: float = 0.001,  # 价格水平阈值
                 bounce_threshold: float = 0.002,  # 反弹阈值
                 volume_ratio_threshold: float = 1.5,  # 成交量比率阈值
                 position_size_limit: float = 1.0,  # 最大持仓限制
                 signal_expire_seconds: int = 300):  # 信号过期时间
        super().__init__(symbol, timeframe, lookback_periods)
        self.support_resistance_periods = support_resistance_periods
        self.price_levels_count = price_levels_count
        self.level_threshold = level_threshold
        self.bounce_threshold = bounce_threshold
        self.volume_ratio_threshold = volume_ratio_threshold
        self.position_size_limit = position_size_limit
        self.signal_expire_seconds = signal_expire_seconds
        
        self.last_signal_time: Optional[datetime] = None
        self.active_signals: List[Dict[str, Any]] = []
        self.support_levels: List[float] = []
        self.resistance_levels: List[float] = []
        
    async def initialize(self):
        """初始化策略"""
        pass
        
    def _identify_price_levels(self) -> Tuple[List[float], List[float]]:
        """识别支撑和阻力水平"""
        if len(self.market_data) < self.support_resistance_periods:
            return [], []
            
        df = self.market_data.tail(self.support_resistance_periods).copy()
        
        # 寻找局部高点和低点
        highs = []
        lows = []
        
        for i in range(1, len(df) - 1):
            # 局部高点
            if df['high'].iloc[i] > df['high'].iloc[i-1] and \
               df['high'].iloc[i] > df['high'].iloc[i+1]:
                highs.append(df['high'].iloc[i])
            
            # 局部低点
            if df['low'].iloc[i] < df['low'].iloc[i-1] and \
               df['low'].iloc[i] < df['low'].iloc[i+1]:
                lows.append(df['low'].iloc[i])
        
        # 对价格水平进行聚类
        def cluster_levels(levels: List[float], threshold: float) -> List[float]:
            if not levels:
                return []
                
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - np.mean(current_cluster)) / np.mean(current_cluster) < threshold:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]
            
            if current_cluster:
                clusters.append(np.mean(current_cluster))
            
            # 按重要性排序（根据价格水平出现的次数）
            return sorted(clusters, reverse=True)[:self.price_levels_count]
        
        resistance_levels = cluster_levels(highs, self.level_threshold)
        support_levels = cluster_levels(lows, self.level_threshold)
        
        return support_levels, resistance_levels
        
    def _calculate_pressure_indicators(self) -> Dict[str, Any]:
        """计算压力指标"""
        if len(self.market_data) < self.lookback_periods:
            return {}
            
        df = self.market_data.copy()
        current_price = df['close'].iloc[-1]
        
        # 计算成交量指标
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        volume_ratio = df['volume'].iloc[-1] / df['volume_ma'].iloc[-1]
        
        # 计算价格动量
        df['momentum'] = df['close'].diff(5)
        momentum = df['momentum'].iloc[-1]
        
        # 计算波动率
        df['returns'] = df['close'].pct_change()
        volatility = df['returns'].std() * np.sqrt(252)
        
        # 更新支撑和阻力水平
        self.support_levels, self.resistance_levels = self._identify_price_levels()
        
        # 找到最近的支撑和阻力水平
        closest_support = min((level for level in self.support_levels if level < current_price), 
                            default=current_price * 0.99)
        closest_resistance = min((level for level in self.resistance_levels if level > current_price), 
                               default=current_price * 1.01)
        
        # 计算到最近水平的距离
        distance_to_support = (current_price - closest_support) / current_price
        distance_to_resistance = (closest_resistance - current_price) / current_price
        
        return {
            'current_price': current_price,
            'volume_ratio': volume_ratio,
            'momentum': momentum,
            'volatility': volatility,
            'closest_support': closest_support,
            'closest_resistance': closest_resistance,
            'distance_to_support': distance_to_support,
            'distance_to_resistance': distance_to_resistance
        }
        
    def _check_pressure_conditions(self, indicators: Dict[str, Any]) -> Optional[str]:
        """检查压力条件"""
        if not indicators:
            return None
            
        # 检查成交量确认
        if indicators['volume_ratio'] < self.volume_ratio_threshold:
            return None
            
        # 在支撑位附近且有上涨动量
        if indicators['distance_to_support'] < self.bounce_threshold and \
           indicators['momentum'] > 0:
            return 'buy'
            
        # 在阻力位附近且有下跌动量
        if indicators['distance_to_resistance'] < self.bounce_threshold and \
           indicators['momentum'] < 0:
            return 'sell'
            
        return None
        
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成交易信号"""
        # 检查是否应该生成新信号
        if self.last_signal_time and \
           (datetime.now() - self.last_signal_time).total_seconds() < self.signal_expire_seconds:
            return []
            
        # 检查数据是否足够
        if len(self.market_data) < self.lookback_periods:
            return []
            
        # 计算压力指标
        indicators = self._calculate_pressure_indicators()
        if not indicators:
            return []
            
        # 检查压力条件
        pressure_direction = self._check_pressure_conditions(indicators)
        if not pressure_direction:
            return []
            
        signals = []
        
        # 生成交易信号
        signal = self._create_signal(
            'price_pressure',
            pressure_direction,
            indicators
        )
        signals.append(signal)
        
        if signals:
            self.last_signal_time = datetime.now()
            self.active_signals.extend(signals)
            
        return signals
        
    def _create_signal(self,
                      signal_type: str,
                      direction: str,
                      indicators: Dict[str, Any]) -> Dict[str, Any]:
        """创建交易信号"""
        # 计算信号强度
        strength = self._calculate_signal_strength(direction, indicators)
        
        # 计算目标持仓量
        position_size = self._calculate_position_size(strength)
        
        # 计算止损和止盈价格
        stop_loss, take_profit = self._calculate_exit_prices(
            direction,
            indicators['current_price'],
            indicators
        )
        
        return {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'type': signal_type,
            'direction': direction,
            'price': indicators['current_price'],
            'strength': strength,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'indicators': {
                'volume_ratio': indicators['volume_ratio'],
                'momentum': indicators['momentum'],
                'volatility': indicators['volatility'],
                'closest_support': indicators['closest_support'],
                'closest_resistance': indicators['closest_resistance']
            },
            'metadata': {
                'strategy_type': 'price_pressure',
                'support_levels': self.support_levels,
                'resistance_levels': self.resistance_levels,
                'volume_confirmation': indicators['volume_ratio'] > self.volume_ratio_threshold
            }
        }
        
    def _calculate_signal_strength(self,
                                 direction: str,
                                 indicators: Dict[str, Any]) -> float:
        """计算信号强度"""
        # 距离分数
        if direction == 'buy':
            distance_score = 1.0 - (indicators['distance_to_support'] / self.bounce_threshold)
        else:
            distance_score = 1.0 - (indicators['distance_to_resistance'] / self.bounce_threshold)
        distance_score = min(max(distance_score, 0.0), 1.0)
        
        # 动量分数
        momentum_score = min(abs(indicators['momentum']) / (indicators['current_price'] * 0.001), 1.0)
        
        # 成交量分数
        volume_score = min((indicators['volume_ratio'] - 1.0) / (self.volume_ratio_threshold - 1.0), 1.0)
        
        # 加权计算总分
        weights = {
            'distance': 0.4,
            'momentum': 0.3,
            'volume': 0.3
        }
        
        total_score = (
            weights['distance'] * distance_score +
            weights['momentum'] * momentum_score +
            weights['volume'] * volume_score
        )
        
        return min(max(total_score, 0.0), 1.0)
        
    def _calculate_position_size(self, signal_strength: float) -> float:
        """计算目标持仓量"""
        return self.position_size_limit * signal_strength
        
    def _calculate_exit_prices(self,
                             direction: str,
                             current_price: float,
                             indicators: Dict[str, Any]) -> tuple[float, float]:
        """计算止损和止盈价格"""
        if direction == 'buy':
            # 止损设在支撑位下方
            stop_loss = indicators['closest_support'] * (1 - self.bounce_threshold)
            # 止盈设在下一个阻力位
            take_profit = min((level for level in self.resistance_levels if level > current_price),
                            default=current_price * (1 + self.bounce_threshold * 3))
        else:
            # 止损设在阻力位上方
            stop_loss = indicators['closest_resistance'] * (1 + self.bounce_threshold)
            # 止盈设在下一个支撑位
            take_profit = max((level for level in self.support_levels if level < current_price),
                            default=current_price * (1 - self.bounce_threshold * 3))
            
        return stop_loss, take_profit
        
    async def _check_signals(self):
        """检查并更新现有信号"""
        now = datetime.now()
        expired_signals = []
        
        if len(self.market_data) > 0:
            current_price = self.market_data['close'].iloc[-1]
            
            for signal in self.active_signals:
                # 检查信号是否过期
                if (now - signal['timestamp']).total_seconds() > self.signal_expire_seconds:
                    expired_signals.append(signal)
                    continue
                    
                # 检查是否触及止损或止盈
                if signal['direction'] == 'buy':
                    if current_price <= signal['stop_loss'] or \
                       current_price >= signal['take_profit']:
                        expired_signals.append(signal)
                else:
                    if current_price >= signal['stop_loss'] or \
                       current_price <= signal['take_profit']:
                        expired_signals.append(signal)
                        
        # 移除过期信号
        for signal in expired_signals:
            self.active_signals.remove(signal) 