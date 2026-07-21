from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

class MicrostructureStrategy(BaseStrategy):
    """市场微结构策略"""
    
    def __init__(self,
                 symbol: str,
                 timeframe: str = '1m',
                 lookback_periods: int = 100,
                 imbalance_threshold: float = 0.2,
                 flow_threshold: float = 0.15,
                 vwap_deviation_threshold: float = 0.001,
                 min_spread: float = 0.0001,
                 max_spread: float = 0.005,
                 min_volume: float = 1.0,
                 signal_expire_seconds: int = 30):
        super().__init__(symbol, timeframe, lookback_periods)
        self.imbalance_threshold = imbalance_threshold
        self.flow_threshold = flow_threshold
        self.vwap_deviation_threshold = vwap_deviation_threshold
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.min_volume = min_volume
        self.signal_expire_seconds = signal_expire_seconds
        self.last_signal_time: Optional[datetime] = None
        self.active_signals: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化策略"""
        # 可以在这里加载历史数据、设置初始参数等
        pass
        
    async def on_market_data(self, data: Dict[str, Any]):
        """处理市场数据更新"""
        self.update_market_data(data)
        await self._check_signals()
        
    async def on_order_book(self, order_book: Dict[str, Any]):
        """处理订单簿更新"""
        self.update_order_book(order_book)
        await self._check_signals()
        
    async def on_trade(self, trade: Dict[str, Any]):
        """处理成交信息"""
        self.update_trades(trade)
        await self._check_signals()
        
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成交易信号"""
        # 检查是否应该生成新信号
        if self.last_signal_time and \
           (datetime.now() - self.last_signal_time).total_seconds() < self.signal_expire_seconds:
            return []
            
        # 获取市场微观结构特征
        features = self.calculate_market_microstructure_features()
        
        # 获取当前价格
        current_price = float(self.order_book['bids'][0][0]) if self.order_book else \
                       self.market_data['price'].iloc[-1] if not self.market_data.empty else 0.0
                       
        if current_price == 0.0:
            return []
            
        signals = []
        
        # 检查买入条件
        if self._check_buy_conditions(features, current_price):
            signal = self._create_signal('buy', current_price, features)
            signals.append(signal)
            
        # 检查卖出条件
        elif self._check_sell_conditions(features, current_price):
            signal = self._create_signal('sell', current_price, features)
            signals.append(signal)
            
        if signals:
            self.last_signal_time = datetime.now()
            self.active_signals.extend(signals)
            
        return signals
        
    def _check_buy_conditions(self, features: Dict[str, float], current_price: float) -> bool:
        """检查买入条件"""
        # 检查订单簿失衡
        if features['order_book_imbalance'] < self.imbalance_threshold:
            return False
            
        # 检查交易流量
        if features['trade_flow'] < self.flow_threshold:
            return False
            
        # 检查VWAP偏离
        vwap_deviation = (features['vwap'] - current_price) / current_price
        if abs(vwap_deviation) > self.vwap_deviation_threshold:
            return False
            
        # 检查点差
        if not self.min_spread <= features['bid_ask_spread'] <= self.max_spread:
            return False
            
        # 检查最近成交量
        recent_volume = sum(t['volume'] for t in self.trades[-10:])
        if recent_volume < self.min_volume:
            return False
            
        return True
        
    def _check_sell_conditions(self, features: Dict[str, float], current_price: float) -> bool:
        """检查卖出条件"""
        # 检查订单簿失衡
        if features['order_book_imbalance'] > -self.imbalance_threshold:
            return False
            
        # 检查交易流量
        if features['trade_flow'] > -self.flow_threshold:
            return False
            
        # 检查VWAP偏离
        vwap_deviation = (features['vwap'] - current_price) / current_price
        if abs(vwap_deviation) > self.vwap_deviation_threshold:
            return False
            
        # 检查点差
        if not self.min_spread <= features['bid_ask_spread'] <= self.max_spread:
            return False
            
        # 检查最近成交量
        recent_volume = sum(t['volume'] for t in self.trades[-10:])
        if recent_volume < self.min_volume:
            return False
            
        return True
        
    def _create_signal(self,
                      direction: str,
                      current_price: float,
                      features: Dict[str, float]) -> Dict[str, Any]:
        """创建交易信号"""
        # 计算信号强度
        strength = self._calculate_signal_strength(direction, features)
        
        # 计算目标持仓量
        position_size = self._calculate_position_size(strength, current_price)
        
        # 计算止损和止盈价格
        stop_loss, take_profit = self._calculate_exit_prices(direction, current_price, features)
        
        return {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'direction': direction,
            'price': current_price,
            'strength': strength,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'features': features,
            'metadata': {
                'strategy_type': 'microstructure',
                'signal_basis': {
                    'order_book_imbalance': features['order_book_imbalance'],
                    'trade_flow': features['trade_flow'],
                    'vwap_deviation': (features['vwap'] - current_price) / current_price,
                    'price_impact': features['price_impact']
                }
            }
        }
        
    def _calculate_signal_strength(self,
                                 direction: str,
                                 features: Dict[str, float]) -> float:
        """计算信号强度"""
        # 将各个特征标准化到0-1之间
        imbalance_score = abs(features['order_book_imbalance']) / 1.0
        flow_score = abs(features['trade_flow']) / 1.0
        impact_score = 1.0 - min(features['price_impact'] / 0.01, 1.0)  # 价格冲击越小越好
        
        # 加权计算总分
        weights = {
            'imbalance': 0.4,
            'flow': 0.3,
            'impact': 0.3
        }
        
        total_score = (
            weights['imbalance'] * imbalance_score +
            weights['flow'] * flow_score +
            weights['impact'] * impact_score
        )
        
        return min(max(total_score, 0.0), 1.0)
        
    def _calculate_position_size(self, signal_strength: float, current_price: float) -> float:
        """计算目标持仓量"""
        # 基于信号强度和当前可用流动性计算持仓量
        base_size = self.min_volume
        max_size = min(
            float(self.order_book['bids'][0][1]),
            float(self.order_book['asks'][0][1])
        ) if self.order_book else base_size
        
        position_size = base_size + (max_size - base_size) * signal_strength
        return position_size
        
    def _calculate_exit_prices(self,
                             direction: str,
                             current_price: float,
                             features: Dict[str, float]) -> tuple[float, float]:
        """计算止损和止盈价格"""
        # 使用价格冲击作为最小价格变动单位
        price_impact = max(features['price_impact'], self.min_spread)
        
        if direction == 'buy':
            stop_loss = current_price * (1 - price_impact * 3)  # 止损设为3倍价格冲击
            take_profit = current_price * (1 + price_impact * 5)  # 止盈设为5倍价格冲击
        else:
            stop_loss = current_price * (1 + price_impact * 3)
            take_profit = current_price * (1 - price_impact * 5)
            
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
                
            # 检查是否触及止损或止盈
            current_price = float(self.order_book['bids'][0][0]) if self.order_book else \
                          self.market_data['price'].iloc[-1] if not self.market_data.empty else 0.0
                          
            if current_price > 0:
                if signal['direction'] == 'buy':
                    if current_price <= signal['stop_loss'] or current_price >= signal['take_profit']:
                        expired_signals.append(signal)
                else:
                    if current_price >= signal['stop_loss'] or current_price <= signal['take_profit']:
                        expired_signals.append(signal)
                        
        # 移除过期信号
        for signal in expired_signals:
            self.active_signals.remove(signal) 