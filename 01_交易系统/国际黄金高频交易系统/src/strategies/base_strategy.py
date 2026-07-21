from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class BaseStrategy:
    """基础策略类"""
    
    def __init__(self,
                 symbol: str,
                 timeframe: str = '1m',
                 lookback_periods: int = 100):
        self.symbol = symbol
        self.timeframe = timeframe
        self.lookback_periods = lookback_periods
        
        # 市场数据
        self.market_data = pd.DataFrame()
        self.order_book: Optional[Dict[str, List[List[float]]]] = None
        self.trades: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化策略"""
        raise NotImplementedError
        
    async def on_market_data(self, data: Dict[str, Any]):
        """处理市场数据更新"""
        raise NotImplementedError
        
    async def on_order_book(self, order_book: Dict[str, Any]):
        """处理订单簿更新"""
        raise NotImplementedError
        
    async def on_trade(self, trade: Dict[str, Any]):
        """处理成交信息"""
        raise NotImplementedError
        
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成交易信号"""
        raise NotImplementedError
        
    def update_market_data(self, data: Dict[str, Any]):
        """更新市场数据"""
        new_data = pd.DataFrame([data])
        self.market_data = pd.concat([self.market_data, new_data]).tail(self.lookback_periods)
        
    def update_order_book(self, order_book: Dict[str, Any]):
        """更新订单簿数据"""
        self.order_book = order_book
        
    def update_trades(self, trade: Dict[str, Any]):
        """更新成交数据"""
        self.trades.append(trade)
        if len(self.trades) > self.lookback_periods:
            self.trades = self.trades[-self.lookback_periods:]
            
    def calculate_market_microstructure_features(self) -> Dict[str, float]:
        """计算市场微观结构特征"""
        features = {}
        
        # 计算订单簿失衡
        if self.order_book:
            bid_volume = sum(float(level[1]) for level in self.order_book['bids'][:5])
            ask_volume = sum(float(level[1]) for level in self.order_book['asks'][:5])
            total_volume = bid_volume + ask_volume
            features['order_book_imbalance'] = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0.0
            
            # 计算买卖价差
            best_bid = float(self.order_book['bids'][0][0])
            best_ask = float(self.order_book['asks'][0][0])
            features['bid_ask_spread'] = (best_ask - best_bid) / best_bid
        else:
            features['order_book_imbalance'] = 0.0
            features['bid_ask_spread'] = 0.0
            
        # 计算交易流量
        if self.trades:
            recent_trades = self.trades[-10:]  # 使用最近10笔成交
            buy_volume = sum(t['volume'] for t in recent_trades if t['side'] == 'buy')
            sell_volume = sum(t['volume'] for t in recent_trades if t['side'] == 'sell')
            total_volume = buy_volume + sell_volume
            features['trade_flow'] = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0.0
        else:
            features['trade_flow'] = 0.0
            
        # 计算VWAP
        if not self.market_data.empty:
            vwap_data = self.market_data.tail(20)  # 使用最近20个周期
            features['vwap'] = (vwap_data['price'] * vwap_data['volume']).sum() / vwap_data['volume'].sum()
        else:
            features['vwap'] = 0.0
            
        # 计算价格冲击
        if self.order_book:
            volume_threshold = 10.0  # 假设要交易10个单位
            impact_buy = self._calculate_price_impact('buy', volume_threshold)
            impact_sell = self._calculate_price_impact('sell', volume_threshold)
            features['price_impact'] = (impact_buy + impact_sell) / 2
        else:
            features['price_impact'] = 0.0
            
        return features
        
    def _calculate_price_impact(self, side: str, volume: float) -> float:
        """计算价格冲击"""
        if not self.order_book:
            return 0.0
            
        levels = self.order_book['asks'] if side == 'buy' else self.order_book['bids']
        base_price = float(levels[0][0])
        remaining_volume = volume
        weighted_price = 0.0
        
        for price, size in levels:
            price = float(price)
            size = float(size)
            
            if remaining_volume <= 0:
                break
                
            executed_volume = min(remaining_volume, size)
            weighted_price += price * executed_volume
            remaining_volume -= executed_volume
            
        if volume - remaining_volume <= 0:
            return 0.0
            
        average_price = weighted_price / (volume - remaining_volume)
        return abs(average_price - base_price) / base_price 