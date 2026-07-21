from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

class StatisticalArbitrageStrategy(BaseStrategy):
    """统计套利策略"""
    
    def __init__(self,
                 symbol: str,
                 timeframe: str = '5m',
                 lookback_periods: int = 100,
                 z_score_threshold: float = 2.0,  # z分数阈值
                 mean_reversion_threshold: float = 0.02,  # 均值回归阈值
                 correlation_threshold: float = 0.8,  # 相关性阈值
                 position_size_limit: float = 1.0,  # 最大持仓限制
                 signal_expire_seconds: int = 300,  # 信号过期时间
                 pairs: List[Tuple[str, str]] = None):  # 交易对列表
        super().__init__(symbol, timeframe, lookback_periods)
        self.z_score_threshold = z_score_threshold
        self.mean_reversion_threshold = mean_reversion_threshold
        self.correlation_threshold = correlation_threshold
        self.position_size_limit = position_size_limit
        self.signal_expire_seconds = signal_expire_seconds
        
        # 初始化交易对
        self.pairs = pairs or []
        self.pair_data: Dict[str, pd.DataFrame] = {}
        self.spread_data: Dict[str, pd.DataFrame] = {}
        self.last_signal_time: Optional[datetime] = None
        self.active_signals: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化策略"""
        # 初始化每个交易对的数据
        for pair in self.pairs:
            self.pair_data[f"{pair[0]}_{pair[1]}"] = pd.DataFrame()
            self.spread_data[f"{pair[0]}_{pair[1]}"] = pd.DataFrame()
            
    def _calculate_spread(self, pair_key: str) -> pd.DataFrame:
        """计算价差"""
        if pair_key not in self.pair_data or len(self.pair_data[pair_key]) < self.lookback_periods:
            return pd.DataFrame()
            
        df = self.pair_data[pair_key].copy()
        
        # 计算对数价格
        df['log_price1'] = np.log(df['price1'])
        df['log_price2'] = np.log(df['price2'])
        
        # 计算价差
        df['spread'] = df['log_price1'] - df['log_price2']
        
        # 计算z分数
        df['spread_mean'] = df['spread'].rolling(window=self.lookback_periods).mean()
        df['spread_std'] = df['spread'].rolling(window=self.lookback_periods).std()
        df['z_score'] = (df['spread'] - df['spread_mean']) / df['spread_std']
        
        # 计算相关性
        df['correlation'] = df['log_price1'].rolling(window=self.lookback_periods).corr(df['log_price2'])
        
        return df
        
    def _check_pair_conditions(self, spread_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """检查交易对条件"""
        if spread_data.empty or len(spread_data) < self.lookback_periods:
            return None
            
        # 获取最新数据
        latest = spread_data.iloc[-1]
        
        # 检查相关性
        if abs(latest['correlation']) < self.correlation_threshold:
            return None
            
        # 检查z分数
        if abs(latest['z_score']) < self.z_score_threshold:
            return None
            
        # 生成交易信号
        if latest['z_score'] > self.z_score_threshold:
            return {
                'direction1': 'sell',
                'direction2': 'buy',
                'z_score': latest['z_score'],
                'correlation': latest['correlation'],
                'spread': latest['spread']
            }
        elif latest['z_score'] < -self.z_score_threshold:
            return {
                'direction1': 'buy',
                'direction2': 'sell',
                'z_score': latest['z_score'],
                'correlation': latest['correlation'],
                'spread': latest['spread']
            }
            
        return None
        
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成交易信号"""
        # 检查是否应该生成新信号
        if self.last_signal_time and \
           (datetime.now() - self.last_signal_time).total_seconds() < self.signal_expire_seconds:
            return []
            
        signals = []
        
        # 对每个交易对生成信号
        for pair in self.pairs:
            pair_key = f"{pair[0]}_{pair[1]}"
            
            # 更新价差数据
            spread_data = self._calculate_spread(pair_key)
            if spread_data.empty:
                continue
                
            # 检查交易条件
            pair_signal = self._check_pair_conditions(spread_data)
            if not pair_signal:
                continue
                
            # 创建交易信号
            signal = self._create_signal(
                'statistical_arbitrage',
                pair,
                pair_signal,
                spread_data
            )
            signals.append(signal)
            
        if signals:
            self.last_signal_time = datetime.now()
            self.active_signals.extend(signals)
            
        return signals
        
    def _create_signal(self,
                      signal_type: str,
                      pair: Tuple[str, str],
                      pair_signal: Dict[str, Any],
                      spread_data: pd.DataFrame) -> Dict[str, Any]:
        """创建交易信号"""
        # 计算信号强度
        strength = self._calculate_signal_strength(pair_signal)
        
        # 计算目标持仓量
        position_size = self._calculate_position_size(strength)
        
        # 获取最新数据
        latest = spread_data.iloc[-1]
        
        # 计算止损和止盈价格
        stop_loss1, take_profit1 = self._calculate_exit_prices(
            pair_signal['direction1'],
            latest['price1'],
            latest['spread_mean'],
            latest['spread_std']
        )
        
        stop_loss2, take_profit2 = self._calculate_exit_prices(
            pair_signal['direction2'],
            latest['price2'],
            latest['spread_mean'],
            latest['spread_std']
        )
        
        return {
            'timestamp': datetime.now(),
            'symbol': pair[0],  # 主交易对
            'pair_symbol': pair[1],  # 配对交易对
            'type': signal_type,
            'direction1': pair_signal['direction1'],
            'direction2': pair_signal['direction2'],
            'price1': latest['price1'],
            'price2': latest['price2'],
            'strength': strength,
            'position_size': position_size,
            'stop_loss1': stop_loss1,
            'take_profit1': take_profit1,
            'stop_loss2': stop_loss2,
            'take_profit2': take_profit2,
            'indicators': {
                'z_score': pair_signal['z_score'],
                'correlation': pair_signal['correlation'],
                'spread': pair_signal['spread'],
                'spread_mean': latest['spread_mean'],
                'spread_std': latest['spread_std']
            },
            'metadata': {
                'strategy_type': 'statistical_arbitrage',
                'pair_key': f"{pair[0]}_{pair[1]}",
                'mean_reversion_threshold': self.mean_reversion_threshold
            }
        }
        
    def _calculate_signal_strength(self, pair_signal: Dict[str, Any]) -> float:
        """计算信号强度"""
        # z分数分数
        z_score_strength = min(abs(pair_signal['z_score']) / (self.z_score_threshold * 2), 1.0)
        
        # 相关性分数
        correlation_strength = min(abs(pair_signal['correlation']) / self.correlation_threshold, 1.0)
        
        # 加权计算总分
        weights = {
            'z_score': 0.6,
            'correlation': 0.4
        }
        
        total_score = (
            weights['z_score'] * z_score_strength +
            weights['correlation'] * correlation_strength
        )
        
        return min(max(total_score, 0.0), 1.0)
        
    def _calculate_position_size(self, signal_strength: float) -> float:
        """计算目标持仓量"""
        return self.position_size_limit * signal_strength
        
    def _calculate_exit_prices(self,
                             direction: str,
                             current_price: float,
                             spread_mean: float,
                             spread_std: float) -> Tuple[float, float]:
        """计算止损和止盈价格"""
        # 根据z分数计算价格变动范围
        price_range = current_price * spread_std
        
        if direction == 'buy':
            stop_loss = current_price * (1 - self.mean_reversion_threshold)
            take_profit = current_price * (1 + spread_std * self.z_score_threshold)
        else:
            stop_loss = current_price * (1 + self.mean_reversion_threshold)
            take_profit = current_price * (1 - spread_std * self.z_score_threshold)
            
        return stop_loss, take_profit
        
    async def _check_signals(self):
        """检查并更新现有信号"""
        now = datetime.now()
        expired_signals = []
        
        for signal in self.active_signals:
            # 检查信号是否过期
            if (now - signal['timestamp']).total_seconds() > self.signal_expire_seconds:
                expired_signals.append(signal)
                continue
                
            # 获取最新价格
            pair_key = signal['metadata']['pair_key']
            if pair_key not in self.pair_data or self.pair_data[pair_key].empty:
                continue
                
            latest = self.pair_data[pair_key].iloc[-1]
            
            # 检查是否触及止损或止盈
            if signal['direction1'] == 'buy':
                if latest['price1'] <= signal['stop_loss1'] or \
                   latest['price1'] >= signal['take_profit1']:
                    expired_signals.append(signal)
            else:
                if latest['price1'] >= signal['stop_loss1'] or \
                   latest['price1'] <= signal['take_profit1']:
                    expired_signals.append(signal)
                    
            # 检查配对交易
            if signal['direction2'] == 'buy':
                if latest['price2'] <= signal['stop_loss2'] or \
                   latest['price2'] >= signal['take_profit2']:
                    expired_signals.append(signal)
            else:
                if latest['price2'] >= signal['stop_loss2'] or \
                   latest['price2'] <= signal['take_profit2']:
                    expired_signals.append(signal)
                    
        # 移除过期信号
        for signal in expired_signals:
            self.active_signals.remove(signal)
            
    async def on_market_data(self, market_data: Dict[str, Any]):
        """处理市场数据更新"""
        await super().on_market_data(market_data)
        
        # 更新交易对数据
        symbol = market_data['symbol']
        for pair in self.pairs:
            if symbol in pair:
                pair_key = f"{pair[0]}_{pair[1]}"
                if pair_key not in self.pair_data:
                    self.pair_data[pair_key] = pd.DataFrame()
                    
                # 更新价格数据
                if symbol == pair[0]:
                    self.pair_data[pair_key].loc[market_data['timestamp'], 'price1'] = market_data['close']
                else:
                    self.pair_data[pair_key].loc[market_data['timestamp'], 'price2'] = market_data['close']
                    
        # 检查现有信号
        await self._check_signals() 