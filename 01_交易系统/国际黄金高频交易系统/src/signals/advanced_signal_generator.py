from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from src.models.deepseek_analyzer import DeepSeekAnalyzer
from src.utils.db_manager import DatabaseManager
from src.signals.signal_generator import SignalGenerator

class AdvancedSignalGenerator(SignalGenerator):
    def __init__(self, deepseek_api_key: str):
        super().__init__(deepseek_api_key)
        self.min_lot_size = 0.01  # 最小交易单位
        self.max_positions = 5     # 最大持仓数量
        self.position_step = 0.01  # 头寸递增步长
        
    async def _get_current_positions(self, symbol: str) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        query = """
            SELECT * FROM orders 
            WHERE symbol = %s 
            AND status = 'open'
            ORDER BY time DESC
        """
        positions = await self.db_manager.execute_query(query, symbol)
        return positions
        
    def _calculate_position_size(self,
                               signal_strength: float,
                               current_positions: List[Dict[str, Any]],
                               account_balance: float) -> float:
        """计算头寸大小"""
        # 基础头寸大小（根据账户余额和信号强度）
        base_size = max(self.min_lot_size,
                       (account_balance * 0.02 * signal_strength) // 100 * self.min_lot_size)
                       
        # 根据现有持仓调整
        total_positions = len(current_positions)
        if total_positions >= self.max_positions:
            return 0
            
        # 根据持仓数量递减头寸大小
        position_size = base_size * (1 - total_positions * 0.1)
        
        # 确保不小于最小交易单位
        return max(self.min_lot_size, round(position_size, 2))
        
    def _should_lock_position(self,
                            current_positions: List[Dict[str, Any]],
                            new_signal: Dict[str, Any],
                            market_data: Dict[str, Any]) -> Tuple[bool, Optional[float]]:
        """判断是否需要锁仓"""
        if not current_positions:
            return False, None
            
        # 计算当前持仓的总方向和规模
        total_long = sum(
            p['volume'] for p in current_positions
            if p['direction'] == 'buy'
        )
        total_short = sum(
            p['volume'] for p in current_positions
            if p['direction'] == 'sell'
        )
        
        # 计算当前持仓的平均价格
        avg_long_price = sum(
            p['price'] * p['volume'] for p in current_positions
            if p['direction'] == 'buy'
        ) / total_long if total_long > 0 else 0
        
        avg_short_price = sum(
            p['price'] * p['volume'] for p in current_positions
            if p['direction'] == 'sell'
        ) / total_short if total_short > 0 else 0
        
        current_price = market_data['close']
        
        # 判断是否需要锁仓
        if total_long > total_short and new_signal['direction'] == 'sell':
            # 多头主导，出现卖出信号
            if current_price < avg_long_price * 0.995:  # 亏损超过0.5%
                return True, total_long - total_short
        elif total_short > total_long and new_signal['direction'] == 'buy':
            # 空头主导，出现买入信号
            if current_price > avg_short_price * 1.005:  # 亏损超过0.5%
                return True, total_short - total_long
                
        return False, None
        
    async def generate_advanced_signal(self,
                                     symbol: str,
                                     account_balance: float,
                                     lookback_hours: int = 24) -> Dict[str, Any]:
        """生成高级交易信号"""
        # 获取基础信号
        base_signal = await self.generate_signal(symbol, lookback_hours)
        
        # 获取当前持仓
        current_positions = await self._get_current_positions(symbol)
        
        # 判断是否需要锁仓
        should_lock, lock_size = self._should_lock_position(
            current_positions,
            base_signal,
            base_signal['metadata']['market_data']
        )
        
        # 计算头寸大小
        position_size = self._calculate_position_size(
            base_signal['confidence'],
            current_positions,
            account_balance
        )
        
        # 扩展基础信号
        advanced_signal = {
            **base_signal,
            'position_size': position_size,
            'should_lock': should_lock,
            'lock_size': lock_size if should_lock else None,
            'current_positions': len(current_positions),
            'total_exposure': sum(p['volume'] for p in current_positions),
            'signal_type': 'advanced_ai_combined'
        }
        
        # 添加高频交易相关的建议
        advanced_signal['trading_suggestions'] = self._generate_trading_suggestions(
            advanced_signal,
            current_positions
        )
        
        return advanced_signal
        
    def _generate_trading_suggestions(self,
                                    signal: Dict[str, Any],
                                    current_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成交易建议"""
        suggestions = {
            'action': None,
            'reason': None,
            'sub_positions': []
        }
        
        if signal['should_lock']:
            suggestions['action'] = 'lock'
            suggestions['reason'] = '检测到潜在风险，建议锁仓对冲'
            # 计算锁仓分批
            lock_size = signal['lock_size']
            while lock_size > self.min_lot_size:
                sub_size = min(lock_size, self.position_step * 2)
                suggestions['sub_positions'].append({
                    'size': round(sub_size, 2),
                    'type': 'lock',
                    'price_offset': 0.0001  # 价格偏移，用于高频交易
                })
                lock_size -= sub_size
        elif signal['position_size'] > 0:
            suggestions['action'] = 'open'
            suggestions['reason'] = '市场条件符合开仓要求'
            # 计算分批开仓
            remaining_size = signal['position_size']
            while remaining_size > self.min_lot_size:
                sub_size = min(remaining_size, self.position_step)
                suggestions['sub_positions'].append({
                    'size': round(sub_size, 2),
                    'type': 'open',
                    'price_offset': 0.0001 * len(suggestions['sub_positions'])
                })
                remaining_size -= sub_size
                
        return suggestions
        
    async def get_position_summary(self, symbol: str) -> Dict[str, Any]:
        """获取持仓摘要"""
        positions = await self._get_current_positions(symbol)
        
        summary = {
            'total_positions': len(positions),
            'total_long': sum(p['volume'] for p in positions if p['direction'] == 'buy'),
            'total_short': sum(p['volume'] for p in positions if p['direction'] == 'sell'),
            'net_exposure': 0,
            'average_long_price': 0,
            'average_short_price': 0,
            'profit_loss': 0
        }
        
        if summary['total_long'] > 0:
            summary['average_long_price'] = sum(
                p['price'] * p['volume'] for p in positions if p['direction'] == 'buy'
            ) / summary['total_long']
            
        if summary['total_short'] > 0:
            summary['average_short_price'] = sum(
                p['price'] * p['volume'] for p in positions if p['direction'] == 'sell'
            ) / summary['total_short']
            
        summary['net_exposure'] = summary['total_long'] - summary['total_short']
        
        return summary 