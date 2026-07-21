from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class BaseRiskController(ABC):
    """风险控制基类"""
    
    def __init__(self, max_position_size: float, max_drawdown: float):
        self.max_position_size = max_position_size  # 最大持仓规模
        self.max_drawdown = max_drawdown  # 最大回撤限制
        self.positions: Dict[str, List[Dict[str, Any]]] = {}  # 当前持仓
        self.trade_history: List[Dict[str, Any]] = []  # 交易历史
        
    @abstractmethod
    async def calculate_position_size(self,
                                    symbol: str,
                                    account_balance: float,
                                    risk_per_trade: float,
                                    current_price: float) -> float:
        """计算持仓规模"""
        pass
        
    @abstractmethod
    async def calculate_stop_loss(self,
                                symbol: str,
                                direction: str,
                                entry_price: float,
                                atr_value: float) -> float:
        """计算动态止损"""
        pass
        
    @abstractmethod
    async def should_adjust_stop_loss(self,
                                    position: Dict[str, Any],
                                    current_price: float,
                                    atr_value: float) -> Optional[float]:
        """判断是否需要调整止损"""
        pass
        
    @abstractmethod
    async def check_risk_limits(self,
                              account_info: Dict[str, Any],
                              new_position: Dict[str, Any]) -> bool:
        """检查风险限制"""
        pass
        
    @abstractmethod
    async def calculate_risk_metrics(self) -> Dict[str, float]:
        """计算风险指标"""
        pass
        
    def add_position(self, symbol: str, position: Dict[str, Any]):
        """添加持仓记录"""
        if symbol not in self.positions:
            self.positions[symbol] = []
        self.positions[symbol].append(position)
        
    def remove_position(self, symbol: str, position_id: str):
        """移除持仓记录"""
        if symbol in self.positions:
            self.positions[symbol] = [
                pos for pos in self.positions[symbol]
                if pos['id'] != position_id
            ]
            
    def add_trade_history(self, trade: Dict[str, Any]):
        """添加交易历史"""
        self.trade_history.append({
            **trade,
            'timestamp': datetime.now()
        })
        
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取持仓"""
        if symbol:
            return self.positions.get(symbol, [])
        return [pos for positions in self.positions.values() for pos in positions]
        
    def get_trade_history(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取交易历史"""
        if not start_time and not end_time:
            return self.trade_history
            
        filtered_history = []
        for trade in self.trade_history:
            if start_time and trade['timestamp'] < start_time:
                continue
            if end_time and trade['timestamp'] > end_time:
                continue
            filtered_history.append(trade)
            
        return filtered_history 