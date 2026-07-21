from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

class TrendFollowingStrategy(BaseStrategy):
    """趋势跟踪策略"""
    
    def __init__(self,
                 symbol: str,
                 timeframe: str = '5m',
                 lookback_periods: int = 100,
                 ma_fast: int = 10,  # 快速移动平均
                 ma_slow: int = 20,  # 慢速移动平均
                 atr_periods: int = 14,  # ATR周期
                 atr_multiplier: float = 2.0,  # ATR乘数
                 rsi_periods: int = 14,  # RSI周期
                 rsi_overbought: float = 70.0,  # RSI超买阈值
                 rsi_oversold: float = 30.0,  # RSI超卖阈值
                 volume_ma_periods: int = 20,  # 成交量移动平均周期
                 min_trend_strength: float = 0.5,  # 最小趋势强度
                 position_size_limit: float = 1.0,  # 最大持仓限制
                 signal_expire_seconds: int = 300):  # 信号过期时间
        super().__init__(symbol, timeframe, lookback_periods)
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.atr_periods = atr_periods
        self.atr_multiplier = atr_multiplier
        self.rsi_periods = rsi_periods
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_ma_periods = volume_ma_periods
        self.min_trend_strength = min_trend_strength
        self.position_size_limit = position_size_limit
        self.signal_expire_seconds = signal_expire_seconds
        
        self.last_signal_time: Optional[datetime] = None
        self.active_signals: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化策略"""
        pass
        
    def _calculate_indicators(self) -> Dict[str, Any]:
        """计算技术指标"""
        if len(self.market_data) < self.lookback_periods:
            return {}
            
        df = self.market_data.copy()
        
        # 计算移动平均
        df['ma_fast'] = df['close'].rolling(window=self.ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=self.ma_slow).mean()
        
        # 计算ATR
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift())
        df['low_close'] = abs(df['low'] - df['close'].shift())
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=self.atr_periods).mean()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_periods).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 计算成交量移动平均
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_periods).mean()
        
        # 计算趋势强度
        df['trend_strength'] = abs(df['ma_fast'] - df['ma_slow']) / df['atr']
        
        return {
            'ma_fast': df['ma_fast'].iloc[-1],
            'ma_slow': df['ma_slow'].iloc[-1],
            'atr': df['atr'].iloc[-1],
            'rsi': df['rsi'].iloc[-1],
            'volume_ma': df['volume_ma'].iloc[-1],
            'trend_strength': df['trend_strength'].iloc[-1],
            'current_volume': df['volume'].iloc[-1]
        }
        
    def _check_trend_conditions(self, indicators: Dict[str, Any]) -> Optional[str]:
        """检查趋势条件"""
        if not indicators:
            return None
            
        # 检查趋势强度
        if indicators['trend_strength'] < self.min_trend_strength:
            return None
            
        # 检查移动平均趋势
        if indicators['ma_fast'] > indicators['ma_slow']:
            # 上升趋势
            if indicators['rsi'] < self.rsi_overbought and \
               indicators['current_volume'] > indicators['volume_ma']:
                return 'buy'
        else:
            # 下降趋势
            if indicators['rsi'] > self.rsi_oversold and \
               indicators['current_volume'] > indicators['volume_ma']:
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
            
        # 计算技术指标
        indicators = self._calculate_indicators()
        if not indicators:
            return []
            
        # 检查趋势条件
        trend_direction = self._check_trend_conditions(indicators)
        if not trend_direction:
            return []
            
        signals = []
        
        # 获取当前价格
        current_price = self.market_data['close'].iloc[-1]
        
        # 生成交易信号
        signal = self._create_signal(
            'trend_follow',
            trend_direction,
            current_price,
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
                      current_price: float,
                      indicators: Dict[str, Any]) -> Dict[str, Any]:
        """创建交易信号"""
        # 计算信号强度
        strength = self._calculate_signal_strength(direction, indicators)
        
        # 计算目标持仓量
        position_size = self._calculate_position_size(strength)
        
        # 计算止损和止盈价格
        stop_loss, take_profit = self._calculate_exit_prices(
            direction,
            current_price,
            indicators['atr']
        )
        
        return {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'type': signal_type,
            'direction': direction,
            'price': current_price,
            'strength': strength,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'indicators': {
                'ma_fast': indicators['ma_fast'],
                'ma_slow': indicators['ma_slow'],
                'atr': indicators['atr'],
                'rsi': indicators['rsi'],
                'trend_strength': indicators['trend_strength'],
                'volume_ratio': indicators['current_volume'] / indicators['volume_ma']
            },
            'metadata': {
                'strategy_type': 'trend_following',
                'trend_strength': indicators['trend_strength'],
                'volume_confirmation': indicators['current_volume'] > indicators['volume_ma']
            }
        }
        
    def _calculate_signal_strength(self,
                                 direction: str,
                                 indicators: Dict[str, Any]) -> float:
        """计算信号强度"""
        # 基于趋势强度的基础分数
        base_score = min(indicators['trend_strength'] / 2.0, 1.0)
        
        # RSI确认分数
        rsi_score = 0.0
        if direction == 'buy':
            rsi_score = (self.rsi_overbought - indicators['rsi']) / (self.rsi_overbought - self.rsi_oversold)
        else:
            rsi_score = (indicators['rsi'] - self.rsi_oversold) / (self.rsi_overbought - self.rsi_oversold)
        rsi_score = min(max(rsi_score, 0.0), 1.0)
        
        # 成交量确认分数
        volume_score = min(indicators['current_volume'] / indicators['volume_ma'], 2.0) / 2.0
        
        # 加权计算总分
        weights = {
            'trend': 0.5,
            'rsi': 0.3,
            'volume': 0.2
        }
        
        total_score = (
            weights['trend'] * base_score +
            weights['rsi'] * rsi_score +
            weights['volume'] * volume_score
        )
        
        return min(max(total_score, 0.0), 1.0)
        
    def _calculate_position_size(self, signal_strength: float) -> float:
        """计算目标持仓量"""
        return self.position_size_limit * signal_strength
        
    def _calculate_exit_prices(self,
                             direction: str,
                             current_price: float,
                             atr: float) -> tuple[float, float]:
        """计算止损和止盈价格"""
        # 使用ATR计算止损距离
        stop_distance = self.atr_multiplier * atr
        
        if direction == 'buy':
            stop_loss = current_price - stop_distance
            take_profit = current_price + (stop_distance * 2)  # 2:1的盈亏比
        else:
            stop_loss = current_price + stop_distance
            take_profit = current_price - (stop_distance * 2)
            
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