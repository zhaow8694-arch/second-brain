"""
交易执行器模块
负责执行具体的交易操作
"""
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

from config import Config as config
from core.exchange_client import exchange_client
from core.risk_manager import risk_manager
from core.notify import telegram_notifier
from core.strategy_engine import strategy_engine

logger = logging.getLogger(__name__)


class TradeExecutor:
    """交易执行器"""
    
    def __init__(self):
        # 持仓状态跟踪
        self.positions = {}  # 当前持仓
        self.position_history = []  # 历史交易记录
        self._max_history_size = 200
        
        # 状态跟踪
        self.entry_prices = {}
        self.target_prices = {}
        self.target_prices_tp2 = {}
        self.stop_losses = {}
        self.position_levels = {}
        self.base_sizes = {}
        self.entry_atrs = {}
        
        # 部分平仓记录
        self.partial_closes = {}
        
        # 同步的持仓
        self.synced_positions = set()
        
        # 行情缓存 {symbol: (timestamp, price)}
        self._ticker_cache = {}
        self._ticker_cache_ttl = 5  # 5秒缓存
    
    def _normalize_symbol(self, symbol: str) -> str:
        """规范化symbol为简称格式"""
        return symbol.split('/')[0].replace(':', '')
    
    def _to_full_symbol(self, short_symbol: str) -> str:
        """短名转全名: ETH → ETH/USDT"""
        return f"{short_symbol}/USDT"
        
    def sync_positions(self) -> None:
        """同步实际持仓到内存状态"""
        try:
            # 获取实际持仓
            actual_positions = exchange_client.get_positions()
            
            for symbol, position in actual_positions.items():
                if symbol not in self.synced_positions:
                    # 新发现的持仓，同步到内存状态
                    self._sync_new_position(symbol, position)
            
            # 清理已平仓的持仓
            for symbol in list(self.positions.keys()):
                if symbol not in actual_positions:
                    self._cleanup_position(symbol)
            
        except Exception as e:
            logger.error(f"同步持仓失败: {e}")
    
    def _sync_new_position(self, symbol: str, position: Dict) -> None:
        """同步新持仓"""
        try:
            entry_price = position['entry_price']
            if entry_price <= 0:
                logger.warning(f"无效的入场价格: {symbol} {entry_price}")
                return
            
            # 添加到同步集合
            self.synced_positions.add(symbol)
            
            # 更新持仓状态
            self.positions[symbol] = position
            self.entry_prices[symbol] = entry_price
            self.position_levels[symbol] = 1
            self.base_sizes[symbol] = entry_price * position['contracts']
            
            # 设置杠杆
            leverage = 20 if symbol in config.get_high_leverage_coins() else 5
            full_sym = self._to_full_symbol(symbol)
            exchange_client.set_leverage(full_sym, leverage)
            
            # 计算ATR和止损
            df_15m = exchange_client.fetch_ohlcv(full_sym, '15m')
            if df_15m is not None and len(df_15m) > 20:
                # 这里简化ATR计算，实际应该使用策略引擎的计算
                atr = df_15m['close'].iloc[-1] * 0.02
            else:
                atr = entry_price * 0.02
            
            self.entry_atrs[symbol] = atr
            
            # 计算止损
            stop_loss = risk_manager.calculate_stop_loss(
                entry_price, atr, position['side']
            )
            self.stop_losses[symbol] = stop_loss
            
            # 计算目标价
            tp1, tp2 = risk_manager.calculate_take_profit(
                entry_price, atr, position['side']
            )
            self.target_prices[symbol] = tp1
            self.target_prices_tp2[symbol] = tp2
            
            # 开始计时
            risk_manager.start_position_timer(symbol)
            
            logger.info(f"同步持仓: {symbol} {position['side']} @ {entry_price}")
            
            # 发送通知
            telegram_notifier.send_trade_alert(
                "持仓同步",
                f"币种: {symbol}\n"
                f"方向: {position['side']}\n"
                f"入场价: {entry_price:.4f}\n"
                f"数量: {position['contracts']:.2f}\n"
                f"杠杆: {leverage}x"
            )
            
        except Exception as e:
            logger.error(f"同步新持仓失败 {symbol}: {e}")
    
    def _cleanup_position(self, symbol: str) -> None:
        """清理已平仓的持仓"""
        if symbol in self.positions:
            del self.positions[symbol]
        
        for dict_name in [
            self.entry_prices, self.target_prices, self.target_prices_tp2,
            self.stop_losses, self.position_levels, self.base_sizes,
            self.entry_atrs, self.partial_closes
        ]:
            dict_name.pop(symbol, None)
        
        self.synced_positions.discard(symbol)
        
        logger.debug(f"清理持仓状态: {symbol}")
    
    def execute_trade(self, signal: Dict) -> bool:
        """执行交易"""
        try:
            full_symbol = signal['symbol']  # BTC/USDT 格式，保留用于交易所操作
            short_symbol = self._normalize_symbol(full_symbol)  # BTC 短格式，用于内部跟踪
            direction = signal['direction']
            current_price = signal['current_price']
            atr = signal['atr']
            
            # 检查风险限制
            if not risk_manager.can_trade_today:
                logger.warning("当日交易已熔断，跳过交易")
                return False
            
            # 检查持仓限制
            if not risk_manager.check_position_limit(self.positions, short_symbol):
                return False
            
            # 获取账户权益
            balance = exchange_client.get_balance()
            account_equity = balance.get('total', 0) or 0
            
            # 计算仓位大小
            position_size = risk_manager.calculate_position_size(
                short_symbol, current_price, account_equity
            )
            
            if position_size <= 0:
                logger.warning(f"仓位大小无效: {position_size}")
                return False
            
            # 设置杠杆
            leverage = 20 if short_symbol in config.get_high_leverage_coins() else 5
            exchange_client.set_leverage(full_symbol, leverage)
            
            # 计算合约数量
            market_info = exchange_client.markets.get(full_symbol)
            if not market_info:
                logger.error(f"找不到市场信息: {full_symbol}")
                return False
            
            # 计算合约数量
            contract_size = position_size / current_price
            
            # 考虑最小数量限制
            min_qty = market_info.get('limits', {}).get('amount', {}).get('min', 0)
            if min_qty > 0 and contract_size < min_qty:
                contract_size = min_qty
            
            # 考虑精度
            amount_step = market_info.get('precision', {}).get('amount', 0.001)
            # 用 CCXT 格式化金额
            contract_size = float(exchange_client.exchange.amount_to_precision(full_symbol, contract_size))
            
            if contract_size <= 0:
                logger.warning(f"合约数量无效: {contract_size}")
                return False
            
            # 执行市价单
            order_side = 'buy' if direction == 'long' else 'sell'
            position_side = 'LONG' if direction == 'long' else 'SHORT'
            order = exchange_client.create_market_order(
                full_symbol, order_side, contract_size,
                params={'positionSide': position_side}
            )
            
            if order is None:
                logger.error(f"下单失败: {full_symbol}")
                risk_manager.add_cooldown(short_symbol, 1800)  # 30分钟冷却
                return False
            
            # 更新持仓状态
            self.positions[short_symbol] = {
                'symbol': short_symbol,
                'side': direction,
                'contracts': contract_size,
                'entry_price': current_price,
                'mark_price': current_price,
                'unrealized_pnl': 0,
                'leverage': leverage
            }
            
            self.entry_prices[short_symbol] = current_price
            self.position_levels[short_symbol] = 1
            self.base_sizes[short_symbol] = current_price * contract_size
            self.entry_atrs[short_symbol] = atr
            
            # 计算止损
            stop_loss = risk_manager.calculate_stop_loss(current_price, atr, direction)
            self.stop_losses[short_symbol] = stop_loss
            
            # 计算目标价
            tp1, tp2 = risk_manager.calculate_take_profit(current_price, atr, direction)
            self.target_prices[short_symbol] = tp1
            self.target_prices_tp2[short_symbol] = tp2
            
            # 开始计时
            risk_manager.start_position_timer(short_symbol)
            self.synced_positions.add(short_symbol)
            
            # 记录交易历史
            trade_record = {
                'timestamp': time.time(),
                'symbol': short_symbol,
                'direction': direction,
                'entry_price': current_price,
                'size': contract_size,
                'position_value': position_size,
                'leverage': leverage,
                'stop_loss': stop_loss,
                'take_profit': tp1,
                'order_id': order.get('id', 'unknown')
            }
            self.position_history.append(trade_record)
            if len(self.position_history) > self._max_history_size:
                self.position_history = self.position_history[-self._max_history_size:]
            
            # 发送通知
            telegram_notifier.send_trade_alert(
                "新开仓位",
                f"币种: {short_symbol}\n"
                f"方向: {direction}\n"
                f"入场价: {current_price:.4f}\n"
                f"数量: {contract_size:.2f}\n"
                f"价值: {position_size:.2f} USDT\n"
                f"杠杆: {leverage}x\n"
                f"止损: {stop_loss:.4f}\n"
                f"目标: {tp1:.4f}"
            )
            
            logger.info(f"交易执行成功: {short_symbol} {direction} {contract_size:.2f} @ {current_price:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"执行交易失败 {signal.get('symbol', 'unknown')}: {e}")
            telegram_notifier.send_error_alert(str(e), "执行交易")
            return False
    
    def close_position(self, symbol: str, reason: str = "手动平仓") -> bool:
        """平仓"""
        try:
            if symbol not in self.positions:
                logger.warning(f"找不到持仓: {symbol}")
                return False
            
            position = self.positions[symbol]
            
            # 计算平仓方向
            close_side = 'sell' if position['side'] == 'long' else 'buy'
            
            # 确定持仓方向参数（双向持仓模式必需）
            position_side = 'LONG' if position['side'] == 'long' else 'SHORT'
            
            # 执行平仓单
            full_symbol = self._to_full_symbol(position['symbol'])
            order = exchange_client.create_market_order(
                full_symbol, close_side, position['contracts'],
                params={'reduceOnly': True, 'positionSide': position_side}
            )
            
            if order is None:
                logger.error(f"平仓下单失败: {symbol}")
                return False
            
            # 计算盈亏
            ticker = exchange_client.fetch_ticker(full_symbol)
            current_price = ticker.get('last') if ticker else position.get('mark_price', 0)
            pnl = self._calculate_pnl(symbol, current_price)
            
            # 清理持仓状态
            self._cleanup_position(symbol)
            
            # 添加冷却
            risk_manager.add_cooldown(symbol)
            
            # 记录历史
            close_record = {
                'timestamp': time.time(),
                'symbol': symbol,
                'direction': position['side'],
                'exit_price': current_price,
                'size': position['contracts'],
                'pnl': pnl,
                'reason': reason,
                'order_id': order.get('id', 'unknown')
            }
            self.position_history.append(close_record)
            
            # 发送通知
            pnl_sign = "[+]" if pnl >= 0 else "[-]"
            telegram_notifier.send_trade_alert(
                "平仓",
                f"币种: {symbol}\n"
                f"方向: {position['side']}\n"
                f"出场价: {current_price:.4f}\n"
                f"数量: {position['contracts']:.2f}\n"
                f"盈亏: {pnl_sign} {pnl:.2f} USDT\n"
                f"原因: {reason}"
            )
            
            logger.info(f"平仓成功: {symbol} {position['side']} @ {current_price:.4f}, PnL: {pnl:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"平仓失败 {symbol}: {e}")
            telegram_notifier.send_error_alert(str(e), f"平仓 {symbol}")
            return False
    
    def partial_close(self, symbol: str, percentage: float, reason: str = "部分止盈") -> bool:
        """部分平仓，金额不足时自动改为全平"""
        try:
            if symbol not in self.positions:
                return False
            
            if percentage <= 0 or percentage >= 1:
                logger.warning(f"无效的平仓比例: {percentage}")
                return False
            
            position = self.positions[symbol]
            
            # 计算平仓数量
            close_amount = position['contracts'] * percentage
            
            # 格式化精度
            full_symbol = self._to_full_symbol(position['symbol'])
            close_amount = float(exchange_client.exchange.amount_to_precision(full_symbol, close_amount))
            
            # 检查剩余数量是否低于最小值
            remain = position['contracts'] - close_amount
            remain = float(exchange_client.exchange.amount_to_precision(full_symbol, remain))
            market_info = exchange_client.markets.get(full_symbol, {})
            min_qty = market_info.get('limits', {}).get('amount', {}).get('min', 0)
            
            if close_amount <= 0 or (remain > 0 and remain < min_qty):
                # 部分平仓后剩余太少，或平仓量无效，改为全平
                logger.info(f"{symbol} 部分平仓金额不足，改为全平")
                return self.close_position(symbol, f"TP1全平 (金额不足部分平)")
            
            # 执行平仓单
            close_side = 'sell' if position['side'] == 'long' else 'buy'
            position_side = 'LONG' if position['side'] == 'long' else 'SHORT'
            order = exchange_client.create_market_order(
                full_symbol, close_side, close_amount,
                params={'reduceOnly': True, 'positionSide': position_side}
            )
            
            if order is None:
                return False
            
            # 更新持仓数量
            new_amount = position['contracts'] - close_amount
            self.positions[symbol]['contracts'] = new_amount
            self.base_sizes[symbol] = self.entry_prices[symbol] * new_amount
            
            # 更新仓位层级
            current_level = self.position_levels.get(symbol, 1)
            self.position_levels[symbol] = max(1, current_level - 1)
            
            # 记录部分平仓
            if symbol not in self.partial_closes:
                self.partial_closes[symbol] = []
            
            self.partial_closes[symbol].append({
                'timestamp': time.time(),
                'percentage': percentage,
                'amount': close_amount,
                'reason': reason
            })
            
            # 发送通知
            telegram_notifier.send_trade_alert(
                "部分平仓",
                f"币种: {symbol}\n"
                f"方向: {position['side']}\n"
                f"平仓比例: {percentage:.1%}\n"
                f"平仓数量: {close_amount:.2f}\n"
                f"剩余数量: {new_amount:.2f}\n"
                f"原因: {reason}"
            )
            
            logger.info(f"部分平仓成功: {symbol} {percentage:.1%}")
            return True
            
        except Exception as e:
            logger.error(f"部分平仓失败 {symbol}: {e}")
            return False
    
    def _get_cached_price(self, full_symbol: str) -> Optional[float]:
        """获取缓存价格，减少API调用"""
        now = time.time()
        if full_symbol in self._ticker_cache:
            ts, price = self._ticker_cache[full_symbol]
            if now - ts < self._ticker_cache_ttl:
                return price
        ticker = exchange_client.fetch_ticker(full_symbol)
        if ticker:
            self._ticker_cache[full_symbol] = (now, ticker['last'])
            return ticker['last']
        return None

    def check_stop_loss(self) -> List[str]:
        """检查止损触发 — 强制实时价格，不使用缓存"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            full_symbol = self._to_full_symbol(position['symbol'])
            ticker = exchange_client.fetch_ticker(full_symbol)
            current_price = ticker.get('last') if ticker else None
            if current_price is None:
                continue
            stop_loss = self.stop_losses.get(symbol)
            
            if stop_loss and risk_manager.check_stop_loss(
                current_price, stop_loss, position['side']
            ):
                positions_to_close.append(symbol)
                logger.info(f"触发止损: {symbol} @ {current_price:.4f}")
        
        return positions_to_close
    
    def check_take_profit(self) -> List[Tuple[str, str, float]]:
        """
        检查止盈触发
        返回: [(symbol, action, profit_pct)]
          action: 'partial' (TP1部分平50%) 或 'full' (TP2全平)
        """
        positions_to_manage = []
        
        for symbol, position in self.positions.items():
            current_price = self._get_cached_price(self._to_full_symbol(position['symbol']))
            if current_price is None:
                continue
            entry_price = self.entry_prices.get(symbol, current_price)
            entry_atr = self.entry_atrs.get(symbol, 0)
            
            if position['side'] == 'long':
                profit_pct = (current_price - entry_price) / entry_price
            else:
                profit_pct = (entry_price - current_price) / entry_price
            
            # TP2 全平优先检查
            tp2 = self.target_prices_tp2.get(symbol)
            if tp2 and risk_manager.check_take_profit(current_price, tp2, position['side']):
                positions_to_manage.append((symbol, 'full', profit_pct))
                continue
            
            # TP1 部分平仓 (用ATR比例代替固定3%)
            tp1 = self.target_prices.get(symbol)
            atr_pct = entry_atr / entry_price if entry_price > 0 else 0
            should_partial, _ = risk_manager.should_take_profit_by_atr(profit_pct, atr_pct)
            
            if tp1 and should_partial:
                positions_to_manage.append((symbol, 'partial', profit_pct))
        
        return positions_to_manage
    
    def update_trailing_stop(self) -> None:
        """更新移动止损"""
        for symbol, position in self.positions.items():
            current_price = self._get_cached_price(self._to_full_symbol(position['symbol']))
            if current_price is None:
                continue
            entry_price = self.entry_prices.get(symbol, current_price)
            
            new_stop = risk_manager.update_high_water_mark(
                symbol, current_price, entry_price, position['side']
            )
            
            if new_stop:
                current_stop = self.stop_losses.get(symbol)
                if position['side'] == 'long' and (current_stop is None or new_stop > current_stop):
                    self.stop_losses[symbol] = new_stop
                elif position['side'] == 'short' and (current_stop is None or new_stop < current_stop):
                    self.stop_losses[symbol] = new_stop
    
    def check_momentum_exit(self) -> List[str]:
        """
        Z-Wei: 动能减弱就退出
        多头: RSI从高位回落 > 阈值 → 平仓
        空头: RSI从低位反弹 > 阈值 → 平仓
        """
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            momentum = strategy_engine.get_position_momentum(symbol)
            if not momentum:
                continue
            
            rsi = momentum.get('rsi', 50)
            rsi_prev = momentum.get('rsi_prev', 50)
            
            if position['side'] == 'long':
                if rsi_prev > config.MOMENTUM_RSI_OVERBOUGHT and rsi < rsi_prev - config.MOMENTUM_RSI_DELTA:
                    positions_to_close.append(symbol)
                    logger.info(f"动量衰减退出(多头): {symbol} RSI {rsi_prev:.1f}→{rsi:.1f}")
            else:
                if rsi_prev < config.MOMENTUM_RSI_OVERSOLD and rsi > rsi_prev + config.MOMENTUM_RSI_DELTA:
                    positions_to_close.append(symbol)
                    logger.info(f"动量衰减退出(空头): {symbol} RSI {rsi_prev:.1f}→{rsi:.1f}")
        
        return positions_to_close
    
    def check_dangerous_candle_exit(self) -> List[str]:
        """
        Z-Wei: 反向出现突兀大K线 + 放量 → 紧急退出
        需要同时满足: 实体>阈值 且 成交量也异常放大
        """
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            df = exchange_client.fetch_ohlcv(self._to_full_symbol(position['symbol']), '15m', limit=25)
            if df is None or len(df) < 21:
                continue
            
            bodies = abs(df['close'] - df['open'])
            volumes = df['volume']
            latest_body = bodies.iloc[-1]
            avg_body = bodies.iloc[-21:-1].mean()
            latest_vol = volumes.iloc[-1]
            avg_vol = volumes.iloc[-21:-1].mean()
            
            # 实体放大 且 成交量也放大（避免普通波动误判）
            body_ratio = latest_body / avg_body if avg_body > 0 else 0
            vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 0
            
            if body_ratio < config.DANGEROUS_BODY_MULTIPLIER or vol_ratio < 1.5:
                continue
            
            is_bearish_dangerous = df['close'].iloc[-1] < df['open'].iloc[-1]
            is_bullish_dangerous = df['close'].iloc[-1] > df['open'].iloc[-1]
            
            if position['side'] == 'long' and is_bearish_dangerous:
                positions_to_close.append(symbol)
                logger.info(f"危险K线退出(多头): {symbol} body={body_ratio:.1f}x vol={vol_ratio:.1f}x")
            elif position['side'] == 'short' and is_bullish_dangerous:
                positions_to_close.append(symbol)
                logger.info(f"危险K线退出(空头): {symbol} body={body_ratio:.1f}x vol={vol_ratio:.1f}x")
        
        return positions_to_close
    
    def check_time_exit(self) -> List[str]:
        """持仓超时 → 平仓"""
        positions_to_close = []
        
        for symbol in list(self.positions.keys()):
            duration_hours = risk_manager.get_position_duration(symbol) / 3600
            if duration_hours > config.MAX_HOLD_HOURS:
                positions_to_close.append(symbol)
                logger.info(f"时间止损: {symbol} 持仓 {duration_hours:.1f}h > {config.MAX_HOLD_HOURS}h")
        
        return positions_to_close
    
    def _calculate_pnl(self, symbol: str, exit_price: float) -> float:
        """计算盈亏"""
        if symbol not in self.positions or symbol not in self.entry_prices:
            return 0
        
        position = self.positions[symbol]
        entry_price = self.entry_prices[symbol]
        
        if position['side'] == 'long':
            pnl = (exit_price - entry_price) * position['contracts']
        else:
            pnl = (entry_price - exit_price) * position['contracts']
        
        return pnl
    
    def get_position_summary(self) -> Dict:
        """获取持仓摘要"""
        summary = {
            'total_positions': len(self.positions),
            'total_value': 0,
            'total_unrealized_pnl': 0,
            'positions': []
        }
        
        for symbol, position in self.positions.items():
            current_price = self._get_cached_price(self._to_full_symbol(position['symbol']))
            if current_price is None:
                current_price = position.get('mark_price', 0)
            entry_price = self.entry_prices.get(symbol, current_price)
            
            if current_price <= 0:
                current_price = entry_price
            
            # 计算持仓价值
            position_value = current_price * position['contracts']
            
            # 计算未实现盈亏
            if position['side'] == 'long':
                unrealized_pnl = (current_price - entry_price) * position['contracts']
            else:
                unrealized_pnl = (entry_price - current_price) * position['contracts']
            
            summary['total_value'] += position_value
            summary['total_unrealized_pnl'] += unrealized_pnl
            
            entry_value = entry_price * position['contracts']
            unrealized_pnl_pct = unrealized_pnl / entry_value if entry_value > 0 else 0.0
            
            summary['positions'].append({
                'symbol': symbol,
                'side': position['side'],
                'size': position['contracts'],
                'entry_price': entry_price,
                'current_price': current_price,
                'position_value': position_value,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'leverage': position['leverage'],
                'stop_loss': self.stop_losses.get(symbol),
                'take_profit': self.target_prices.get(symbol),
                'duration_hours': risk_manager.get_position_duration(symbol) / 3600
            })
        
        return summary


# 创建全局交易执行器实例
trade_executor = TradeExecutor()