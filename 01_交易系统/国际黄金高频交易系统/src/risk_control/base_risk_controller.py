from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

@dataclass
class RiskLimit:
    """风险限制配置"""
    max_position_size: float  # 最大持仓量
    max_daily_loss: float    # 最大日亏损
    max_drawdown: float      # 最大回撤
    max_leverage: float      # 最大杠杆
    min_margin_ratio: float  # 最小保证金率
    max_order_size: float    # 最大单笔订单量
    max_orders_per_minute: int  # 每分钟最大订单数

@dataclass
class RiskAlert:
    """风险预警信息"""
    timestamp: datetime
    level: str  # WARNING, ERROR, CRITICAL
    type: str   # POSITION, ORDER, ACCOUNT
    message: str
    details: Dict

class BaseRiskController:
    """风控基础控制器"""
    
    def __init__(self, risk_limits: RiskLimit):
        self.risk_limits = risk_limits
        self.alerts: List[RiskAlert] = []
        self.positions: Dict[str, float] = {}  # 当前持仓
        self.daily_pnl: float = 0.0  # 当日盈亏
        self.max_balance: float = 0.0  # 最高账户余额
        self.current_balance: float = 0.0  # 当前账户余额
        
    def check_position_risk(self, symbol: str, size: float) -> bool:
        """检查持仓风险"""
        try:
            # 检查是否超过最大持仓量
            if size > self.risk_limits.max_position_size:
                self._add_alert(
                    "ERROR",
                    "POSITION",
                    f"持仓量 {size} 超过最大限制 {self.risk_limits.max_position_size}",
                    {"symbol": symbol, "size": size}
                )
                return False
                
            # 检查杠杆率
            if self._calculate_leverage(symbol, size) > self.risk_limits.max_leverage:
                self._add_alert(
                    "ERROR",
                    "POSITION",
                    f"杠杆率超过最大限制 {self.risk_limits.max_leverage}",
                    {"symbol": symbol, "size": size}
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"检查持仓风险时发生错误: {e}")
            return False
            
    def check_order_risk(self, symbol: str, size: float, price: float) -> bool:
        """检查订单风险"""
        try:
            # 检查订单大小
            if size > self.risk_limits.max_order_size:
                self._add_alert(
                    "ERROR",
                    "ORDER",
                    f"订单量 {size} 超过最大限制 {self.risk_limits.max_order_size}",
                    {"symbol": symbol, "size": size, "price": price}
                )
                return False
                
            # 检查保证金率
            margin_ratio = self._calculate_margin_ratio(symbol, size, price)
            if margin_ratio < self.risk_limits.min_margin_ratio:
                self._add_alert(
                    "ERROR",
                    "ORDER",
                    f"保证金率 {margin_ratio} 低于最小要求 {self.risk_limits.min_margin_ratio}",
                    {"symbol": symbol, "size": size, "price": price}
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"检查订单风险时发生错误: {e}")
            return False
            
    def check_account_risk(self) -> bool:
        """检查账户风险"""
        try:
            # 检查日亏损
            if self.daily_pnl < -self.risk_limits.max_daily_loss:
                self._add_alert(
                    "CRITICAL",
                    "ACCOUNT",
                    f"日亏损 {self.daily_pnl} 超过最大限制 {self.risk_limits.max_daily_loss}",
                    {"daily_pnl": self.daily_pnl}
                )
                return False
                
            # 检查回撤
            drawdown = self._calculate_drawdown()
            if drawdown > self.risk_limits.max_drawdown:
                self._add_alert(
                    "CRITICAL",
                    "ACCOUNT",
                    f"回撤 {drawdown} 超过最大限制 {self.risk_limits.max_drawdown}",
                    {"drawdown": drawdown}
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"检查账户风险时发生错误: {e}")
            return False
            
    def update_position(self, symbol: str, size: float):
        """更新持仓信息"""
        self.positions[symbol] = size
        
    def update_pnl(self, pnl: float):
        """更新盈亏信息"""
        self.daily_pnl += pnl
        
    def update_balance(self, balance: float):
        """更新账户余额"""
        self.current_balance = balance
        self.max_balance = max(self.max_balance, balance)
        
    def _calculate_leverage(self, symbol: str, size: float) -> float:
        """计算杠杆率"""
        # TODO: 实现杠杆率计算逻辑
        return 1.0
        
    def _calculate_margin_ratio(self, symbol: str, size: float, price: float) -> float:
        """计算保证金率"""
        # TODO: 实现保证金率计算逻辑
        return 1.0
        
    def _calculate_drawdown(self) -> float:
        """计算回撤"""
        if self.max_balance == 0:
            return 0.0
        return (self.max_balance - self.current_balance) / self.max_balance
        
    def _add_alert(self, level: str, type: str, message: str, details: Dict):
        """添加风险预警"""
        alert = RiskAlert(
            timestamp=datetime.now(),
            level=level,
            type=type,
            message=message,
            details=details
        )
        self.alerts.append(alert)
        logger.warning(f"风险预警: {message}")
        
    def get_alerts(self, level: Optional[str] = None) -> List[RiskAlert]:
        """获取风险预警"""
        if level:
            return [alert for alert in self.alerts if alert.level == level]
        return self.alerts 