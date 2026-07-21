from typing import Dict, Any, Optional, List
import numpy as np
from datetime import datetime, timedelta
from .base_risk_controller import BaseRiskController

class AdvancedRiskController(BaseRiskController):
    """高级风险控制器"""
    
    def __init__(self,
                 max_position_size: float,
                 max_drawdown: float,
                 risk_per_trade: float = 0.02,
                 trailing_stop_multiplier: float = 2.0,
                 max_positions_per_symbol: int = 3,
                 max_total_positions: int = 10):
        super().__init__(max_position_size, max_drawdown)
        self.risk_per_trade = risk_per_trade  # 每笔交易风险比例
        self.trailing_stop_multiplier = trailing_stop_multiplier  # 追踪止损倍数
        self.max_positions_per_symbol = max_positions_per_symbol  # 每个交易对最大持仓数
        self.max_total_positions = max_total_positions  # 总持仓限制
        
    async def calculate_position_size(self,
                                    symbol: str,
                                    account_balance: float,
                                    risk_per_trade: float,
                                    current_price: float) -> float:
        """计算持仓规模
        
        使用固定风险金额方法计算持仓规模:
        position_size = (account_balance * risk_per_trade) / (current_price * stop_loss_percentage)
        """
        # 获取当前ATR值用于计算止损距离
        atr_value = await self._get_atr(symbol)
        stop_loss_distance = atr_value * 2  # 使用2倍ATR作为止损距离
        
        # 计算风险金额
        risk_amount = account_balance * risk_per_trade
        
        # 计算持仓规模
        position_size = risk_amount / (stop_loss_distance * current_price)
        
        # 确保不超过最大持仓限制
        position_size = min(position_size, self.max_position_size)
        
        # 根据交易对调整精度
        position_size = self._adjust_position_size_precision(symbol, position_size)
        
        return position_size
        
    async def calculate_stop_loss(self,
                                symbol: str,
                                direction: str,
                                entry_price: float,
                                atr_value: float) -> float:
        """计算动态止损
        
        使用ATR的倍数来设置初始止损位置
        """
        stop_distance = atr_value * 2  # 使用2倍ATR作为止损距离
        
        if direction == 'buy':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance
            
        return self._adjust_price_precision(symbol, stop_loss)
        
    async def should_adjust_stop_loss(self,
                                    position: Dict[str, Any],
                                    current_price: float,
                                    atr_value: float) -> Optional[float]:
        """判断是否需要调整止损
        
        使用跟踪止损策略，当价格移动超过ATR的一定倍数时，调整止损位置
        """
        direction = position['direction']
        current_stop = position['stop_loss']
        entry_price = position['entry_price']
        
        # 计算价格移动距离
        price_movement = abs(current_price - entry_price)
        min_movement = atr_value * self.trailing_stop_multiplier
        
        # 如果价格移动超过最小距离
        if price_movement >= min_movement:
            if direction == 'buy':
                # 多头持仓，价格上涨时调整止损
                if current_price > entry_price:
                    new_stop = current_price - (atr_value * 2)
                    if new_stop > current_stop:
                        return self._adjust_price_precision(position['symbol'], new_stop)
            else:
                # 空头持仓，价格下跌时调整止损
                if current_price < entry_price:
                    new_stop = current_price + (atr_value * 2)
                    if new_stop < current_stop:
                        return self._adjust_price_precision(position['symbol'], new_stop)
                        
        return None
        
    async def check_risk_limits(self,
                              account_info: Dict[str, Any],
                              new_position: Dict[str, Any]) -> bool:
        """检查风险限制
        
        检查各项风险指标是否符合要求
        """
        symbol = new_position['symbol']
        
        # 检查当前持仓数量
        current_positions = self.get_positions(symbol)
        if len(current_positions) >= self.max_positions_per_symbol:
            return False
            
        total_positions = len(self.get_positions())
        if total_positions >= self.max_total_positions:
            return False
            
        # 检查账户回撤
        if self._calculate_drawdown(account_info) > self.max_drawdown:
            return False
            
        # 检查持仓规模
        total_exposure = self._calculate_total_exposure(account_info)
        new_exposure = new_position['volume'] * new_position['entry_price']
        if (total_exposure + new_exposure) / account_info['equity'] > self.max_position_size:
            return False
            
        return True
        
    async def calculate_risk_metrics(self) -> Dict[str, float]:
        """计算风险指标"""
        # 计算过去24小时的交易统计
        day_ago = datetime.now() - timedelta(days=1)
        recent_trades = self.get_trade_history(start_time=day_ago)
        
        if not recent_trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'largest_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'total_trades': 0
            }
            
        # 计算胜率
        winning_trades = [t for t in recent_trades if t['profit'] > 0]
        win_rate = len(winning_trades) / len(recent_trades)
        
        # 计算盈亏比
        total_profit = sum(t['profit'] for t in winning_trades)
        losing_trades = [t for t in recent_trades if t['profit'] <= 0]
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 计算平均盈亏
        average_win = total_profit / len(winning_trades) if winning_trades else 0
        average_loss = total_loss / len(losing_trades) if losing_trades else 0
        
        # 计算最大回撤
        cumulative_returns = np.array([t['profit'] for t in recent_trades])
        cumulative_returns = np.cumsum(cumulative_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = running_max - cumulative_returns
        largest_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        # 计算夏普比率
        returns = np.array([t['profit'] for t in recent_trades])
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
            
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'largest_drawdown': largest_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(recent_trades)
        }
        
    async def _get_atr(self, symbol: str) -> float:
        """获取ATR值"""
        # TODO: 实现从市场数据中获取ATR
        # 临时返回固定值
        return 100.0
        
    def _adjust_position_size_precision(self, symbol: str, size: float) -> float:
        """调整持仓规模精度"""
        # TODO: 根据交易对规则调整精度
        return round(size, 3)
        
    def _adjust_price_precision(self, symbol: str, price: float) -> float:
        """调整价格精度"""
        # TODO: 根据交易对规则调整精度
        return round(price, 2)
        
    def _calculate_drawdown(self, account_info: Dict[str, Any]) -> float:
        """计算账户回撤"""
        equity = account_info['equity']
        balance = account_info['balance']
        return (balance - equity) / balance if balance > 0 else 0
        
    def _calculate_total_exposure(self, account_info: Dict[str, Any]) -> float:
        """计算总持仓敞口"""
        positions = self.get_positions()
        return sum(pos['volume'] * pos['entry_price'] for pos in positions) 