"""
风险管理模块
负责交易风险控制和资金管理
"""
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date

from config import Config as config

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        self.daily_start_equity = None
        self.daily_date = None
        self.initial_equity = None
        self.can_trade_today = True
        
        # 冷却记录 {symbol: expiry_timestamp}
        self.cooldown_log = {}
        
        # 持仓计时器 {symbol: start_timestamp}
        self.position_timers = {}
        
        # 高水位线 {symbol: price}
        self.high_water_marks = {}
        
    def initialize(self, initial_equity: float) -> None:
        """初始化风险管理器"""
        self.initial_equity = initial_equity
        self.daily_start_equity = initial_equity
        self.daily_date = date.today().isoformat()
        self.can_trade_today = True
        
        logger.info(f"风险管理器初始化完成 - 初始权益: {initial_equity:.2f} USDT")
    
    def check_daily_loss_limit(self, current_equity: float) -> Tuple[bool, float]:
        """检查日亏损限制"""
        today = date.today().isoformat()
        
        # 如果是新的一天，重置日统计
        if today != self.daily_date:
            self.daily_date = today
            self.daily_start_equity = current_equity
            self.can_trade_today = True
            logger.info(f"新的一天开始 - 日起始权益: {current_equity:.2f} USDT")
        
        if self.daily_start_equity is None or self.daily_start_equity <= 0:
            logger.error(f"日起始权益异常: {self.daily_start_equity}")
            self.can_trade_today = False
            return False, 0.0
        
        # 计算当日盈亏
        daily_pnl = current_equity - self.daily_start_equity
        daily_pnl_pct = daily_pnl / self.daily_start_equity
        
        # 检查是否触发日亏损熔断
        if daily_pnl_pct <= -config.DAILY_MAX_LOSS:
            if self.can_trade_today:
                logger.error(f"触发日亏损熔断! 当日亏损: {daily_pnl_pct:.2%} (限制: {config.DAILY_MAX_LOSS:.1%})")
                self.can_trade_today = False
            
            return False, daily_pnl_pct
        
        return True, daily_pnl_pct
    
    def check_position_limit(self, current_positions: Dict, symbol: str) -> bool:
        """检查持仓限制"""
        self._cleanup_expired_cooldowns()
        
        # 检查总持仓数量
        if len(current_positions) >= config.MAX_POSITIONS:
            logger.warning(f"达到最大持仓限制: {len(current_positions)}/{config.MAX_POSITIONS}")
            return False
        
        # 检查普通持仓数量（排除VIP币种）
        regular_positions = [
            sym for sym in current_positions.keys() 
            if sym not in config.get_high_leverage_coins()
        ]
        
        if len(regular_positions) >= config.MAX_REGULAR_POSITIONS:
            logger.warning(f"达到普通持仓限制: {len(regular_positions)}/{config.MAX_REGULAR_POSITIONS}")
            return False
        
        # 检查是否在冷却期
        if symbol in self.cooldown_log:
            expiry_time = self.cooldown_log[symbol]
            if time.time() < expiry_time:
                remaining = expiry_time - time.time()
                logger.debug(f"{symbol} 仍在冷却期: {remaining:.0f}秒")
                return False
            else:
                # 冷却期已过，清理记录
                del self.cooldown_log[symbol]
        
        return True
    
    def _cleanup_expired_cooldowns(self) -> None:
        """清理过期的冷却记录"""
        now = time.time()
        expired = [sym for sym, expiry in self.cooldown_log.items() if now >= expiry]
        for sym in expired:
            del self.cooldown_log[sym]
    
    def calculate_position_size(self, symbol: str, current_price: float, account_equity: float) -> float:
        """计算仓位大小"""
        # 基础仓位大小 = 账户权益 * 风险比例
        base_size = account_equity * config.RISK_PCT
        
        # 根据币种类型调整
        if symbol in config.get_high_leverage_coins():
            # VIP币种使用较高杠杆，但单笔风险相同
            size = base_size
        else:
            # 普通币种
            size = base_size
        
        # 确保不超过单笔最大保证金限制（默认10%）
        max_margin = account_equity * 0.10
        size = min(size, max_margin)
        
        logger.debug(f"仓位计算: {symbol} - 基础: {base_size:.2f}, 最终: {size:.2f}")
        return size
    
    def add_cooldown(self, symbol: str, duration: int = None) -> None:
        """添加冷却期"""
        if duration is None:
            duration = config.COOLDOWN_TIME
        
        expiry = time.time() + duration
        self.cooldown_log[symbol] = expiry
        logger.info(f"{symbol} 进入冷却期: {duration}秒")
    
    def start_position_timer(self, symbol: str) -> None:
        """开始持仓计时"""
        self.position_timers[symbol] = time.time()
    
    def get_position_duration(self, symbol: str) -> float:
        """获取持仓持续时间（秒）"""
        if symbol in self.position_timers:
            return time.time() - self.position_timers[symbol]
        return 0
    
    def calculate_stop_loss(self, entry_price: float, atr: float, side: str) -> float:
        """计算止损价格"""
        if side == 'long':
            # 多头止损 = 入场价 - ATR * 多头止损倍数
            stop_loss = entry_price - atr * config.ATR_SL_LONG
        else:
            # 空头止损 = 入场价 + ATR * 空头止损倍数
            stop_loss = entry_price + atr * config.ATR_SL_SHORT
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price: float, atr: float, side: str) -> Tuple[float, float]:
        """计算止盈价格（第一目标和第二目标）"""
        if side == 'long':
            # 多头止盈
            tp1 = entry_price + atr * 2.0  # 2倍ATR
            tp2 = entry_price + atr * 4.0  # 4倍ATR
        else:
            # 空头止盈
            tp1 = entry_price - atr * 2.0  # 2倍ATR
            tp2 = entry_price - atr * 4.0  # 4倍ATR
        
        return tp1, tp2
    
    def should_take_profit_by_atr(self, profit_pct: float, entry_atr_pct: float) -> Tuple[bool, bool]:
        """
        Z-Wei: 用ATR比例替代固定%判断止盈
        entry_atr_pct = entry_atr / entry_price
        返回: (should_partial_close, should_full_close)
        """
        if entry_atr_pct <= 0:
            return False, False
        
        ratio = profit_pct / entry_atr_pct
        return ratio >= 1.0, ratio >= 2.0
    
    def check_stop_loss(self, current_price: float, stop_loss: float, side: str) -> bool:
        """检查是否触发止损"""
        if side == 'long':
            # 多头：当前价 <= 止损价
            return current_price <= stop_loss
        else:
            # 空头：当前价 >= 止损价
            return current_price >= stop_loss
    
    def check_take_profit(self, current_price: float, take_profit: float, side: str) -> bool:
        """检查是否触发止盈"""
        if side == 'long':
            # 多头：当前价 >= 止盈价
            return current_price >= take_profit
        else:
            # 空头：当前价 <= 止盈价
            return current_price <= take_profit
    
    def update_high_water_mark(self, symbol: str, current_price: float, entry_price: float, side: str) -> Optional[float]:
        """更新最高水位线并返回移动止损价格"""
        if side == 'long':
            price_change = (current_price - entry_price) / entry_price
            if price_change >= config.HWM_ACTIVATE_LONG:
                hwm = max(current_price, self.high_water_marks.get(symbol, entry_price))
                self.high_water_marks[symbol] = hwm
                new_stop = hwm * (1 - config.HWM_RETRACT_LONG)
                logger.debug(f"{symbol} 激活移动止损: HWM={hwm:.4f}, new_stop={new_stop:.4f}")
                return new_stop
        else:
            price_change = (entry_price - current_price) / entry_price
            if price_change >= config.HWM_ACTIVATE_SHORT:
                hwm = min(current_price, self.high_water_marks.get(symbol, entry_price))
                self.high_water_marks[symbol] = hwm
                new_stop = hwm * (1 + config.HWM_RETRACT_SHORT)
                logger.debug(f"{symbol} 激活移动止损: HWM={hwm:.4f}, new_stop={new_stop:.4f}")
                return new_stop
        
        return None
    
    def get_risk_report(self, current_equity: float, positions: Dict) -> Dict:
        """获取风险报告"""
        initial_equity = self.initial_equity if self.initial_equity is not None else current_equity
        daily_start_equity = self.daily_start_equity if self.daily_start_equity is not None else current_equity
        
        total_pnl = current_equity - initial_equity
        if initial_equity > 0:
            total_pnl_pct = total_pnl / initial_equity
        else:
            total_pnl_pct = 0.0
        
        daily_pnl = current_equity - daily_start_equity
        if daily_start_equity > 0:
            daily_pnl_pct = daily_pnl / daily_start_equity
        else:
            daily_pnl_pct = 0.0
        
        # 计算风险等级
        if daily_pnl_pct <= -0.05:
            risk_level = "高"
        elif daily_pnl_pct <= -0.02:
            risk_level = "中"
        else:
            risk_level = "低"
        
        # 计算持仓风险
        position_risk = 0
        for pos in positions.values():
            unrealized_pnl = pos.get('unrealized_pnl', 0)
            entry_value = pos.get('entry_price', 0) * pos.get('contracts', 0)
            leverage = pos.get('leverage', 1)
            if entry_value > 0:
                position_risk += abs(unrealized_pnl) / entry_value * leverage
        
        avg_position_risk = position_risk / len(positions) if positions else 0
        
        return {
            'total_equity': current_equity,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'daily_pnl': daily_pnl,
            'daily_pnl_pct': daily_pnl_pct,
            'positions_count': len(positions),
            'can_trade': self.can_trade_today,
            'risk_level': risk_level,
            'avg_position_risk': avg_position_risk,
            'cooldown_count': len(self.cooldown_log),
            'initial_equity': self.initial_equity,
            'daily_start_equity': self.daily_start_equity
        }


# 创建全局风险管理器实例
risk_manager = RiskManager()