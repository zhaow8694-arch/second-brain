"""
主应用程序模块
整合所有组件，提供完整的交易系统
"""
import time
import logging
import logging.handlers
import signal
import sys
from datetime import datetime, date
from typing import Dict, List, Optional

from config import Config as config
from core.exchange_client import exchange_client
from core.risk_manager import risk_manager
from core.strategy_engine import strategy_engine
from core.trade_executor import trade_executor
from core.notify import telegram_notifier
from core.state_store import StateManager
from web_dashboard import start_dashboard, update_state

logger = logging.getLogger(__name__)


class TradingApp:
    """交易应用程序"""
    
    def __init__(self):
        self.running = False
        self.last_report_time = 0
        self.last_display_time = 0
        self.start_time = None
        self.state_manager = StateManager()
        
        # 设置日志
        self._setup_logging()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> None:
        """设置日志"""
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return
        
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        
        file_handler = logging.handlers.RotatingFileHandler(
            'trading_system.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
    
    def _signal_handler(self, signum, frame) -> None:
        """信号处理"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False
    
    def initialize(self) -> bool:
        """初始化应用程序"""
        try:
            logger.info("=" * 60)
            logger.info(">>> 交易系统启动")
            logger.info("=" * 60)
            
            # 验证配置
            config.validate()
            logger.info("[OK] 配置验证通过")
            
            # 测试Telegram连接
            if not telegram_notifier.test_connection():
                logger.warning("[WARN] Telegram连接测试失败，通知功能可能不可用")
            else:
                logger.info("[OK] Telegram连接测试成功")
            
            # 初始化交易所连接
            if not exchange_client.initialize(demo_mode=True):
                logger.error("[ERROR] 交易所初始化失败")
                return False
            
            logger.info("[OK] 交易所初始化成功")
            
            # 获取初始余额
            balance = exchange_client.get_balance()
            initial_equity = balance.get('total', 0) or 0
            
            if initial_equity <= 0:
                logger.error(f"[ERROR] 账户余额无效: {initial_equity}")
                return False
            
            logger.info(f"[BALANCE] 初始账户权益: {initial_equity:.2f} USDT")
            
            # 初始化风险管理器
            risk_manager.initialize(initial_equity)
            
            # 加载状态
            self.state_manager.load_state()
            
            # 同步持仓
            trade_executor.sync_positions()
            
            # 发送启动通知
            telegram_notifier.send_trade_alert(
                "系统启动",
                f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"账户权益: {initial_equity:.2f} USDT\n"
                f"交易对数量: {len(exchange_client.symbols)}\n"
                f"风险比例: {config.RISK_PCT:.1%}\n"
                f"日亏损限制: {config.DAILY_MAX_LOSS:.1%}"
            )
            
            # 启动 Web 监控面板
            start_dashboard(8080)
            logger.info("[OK] Web 监控面板已启动: http://localhost:8080")
            
            logger.info("[OK] 应用程序初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 应用程序初始化失败: {e}")
            telegram_notifier.send_error_alert(str(e), "应用程序初始化")
            return False
    
    def run_cycle(self) -> None:
        """运行一个交易周期"""
        try:
            # 获取账户信息
            balance = exchange_client.get_balance()
            current_equity = balance.get('total', 0) or 0
            
            # 检查日亏损限制
            can_trade, daily_pnl_pct = risk_manager.check_daily_loss_limit(current_equity)
            
            if not can_trade:
                logger.warning("当日交易已熔断，等待至次日")
                now = datetime.now()
                seconds_until_midnight = (
                    datetime(now.year, now.month, now.day + 1) - now
                ).seconds if now.hour < 23 else 3600
                time.sleep(min(seconds_until_midnight, 3600))
                return
            
            # 同步持仓
            trade_executor.sync_positions()
            
            # ===== 平仓检查（按优先级降序） =====
            # P0: 危险K线反向 — 最高优先级，保命级退出
            danger_exits = trade_executor.check_dangerous_candle_exit()
            for symbol in danger_exits:
                trade_executor.close_position(symbol, "危险K线反向退出")
            
            # P1: 止损 — 强制实时价格
            stop_losses = trade_executor.check_stop_loss()
            for symbol in stop_losses:
                trade_executor.close_position(symbol, "止损触发")
            
            # P2: 动量衰减 — Z-Wei 动能减弱
            momentum_exits = trade_executor.check_momentum_exit()
            for symbol in momentum_exits:
                trade_executor.close_position(symbol, "动量衰减退出")
            
            # P3: 时间止损 — 持仓超时
            time_exits = trade_executor.check_time_exit()
            for symbol in time_exits:
                trade_executor.close_position(symbol, "时间止损")
            
            # P4: 止盈 — TP1部分平 / TP2全平
            take_profits = trade_executor.check_take_profit()
            for symbol, action, profit_pct in take_profits:
                if action == 'full':
                    trade_executor.close_position(symbol, f"TP2全平 ({profit_pct:.1%})")
                else:
                    trade_executor.partial_close(symbol, 0.5, f"TP1部分止盈 ({profit_pct:.1%})")
            
            # P5: 更新移动止损
            trade_executor.update_trailing_stop()
            # =====================================
            
            # 扫描交易机会（仅在非震荡市下才能生成信号）
            if len(trade_executor.positions) < config.MAX_POSITIONS:
                signals = strategy_engine.scan_markets()
                
                for signal in signals:
                    if not self.running:
                        break
                    
                    # 执行交易
                    if trade_executor.execute_trade(signal):
                        time.sleep(2)  # 交易后短暂暂停
            
            # 定期报告
            current_time = time.time()
            if current_time - self.last_report_time >= config.REPORT_INTERVAL:
                self._generate_report(current_equity)
                self.last_report_time = current_time
            
            # 定期显示状态
            if current_time - self.last_display_time >= 10:
                self._display_status(current_equity, daily_pnl_pct)
                self.last_display_time = current_time
            
            # 保存状态
            self.state_manager.save_state()
            
        except Exception as e:
            logger.error(f"交易周期执行失败: {e}")
            telegram_notifier.send_error_alert(str(e), "交易周期")
    
    def _generate_report(self, current_equity: float) -> None:
        """生成报告"""
        try:
            risk_report = risk_manager.get_risk_report(current_equity, trade_executor.positions)
            position_summary = trade_executor.get_position_summary()
            
            report_data = {
                'total_pnl': risk_report.get('total_pnl', 0) or 0,
                'total_pnl_pct': risk_report.get('total_pnl_pct', 0) or 0,
                'daily_pnl': risk_report.get('daily_pnl', 0) or 0,
                'daily_pnl_pct': risk_report.get('daily_pnl_pct', 0) or 0,
                'positions_count': risk_report.get('positions_count', 0) or 0,
                'win_rate': self._calculate_win_rate(),
                'risk_level': risk_report.get('risk_level', '低') or '低',
                'total_value': position_summary.get('total_value', 0) or 0,
                'total_unrealized_pnl': position_summary.get('total_unrealized_pnl', 0) or 0
            }
            
            telegram_notifier.send_daily_report(report_data)
            logger.info("[STATS] 日报已发送")
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
    
    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        history = trade_executor.position_history
        if not history:
            return 0.0
        
        closed_trades = [t for t in history if 'pnl' in t]
        if not closed_trades:
            return 0.0
        
        winning_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
        return len(winning_trades) / len(closed_trades)
    
    def _display_status(self, current_equity: float, daily_pnl_pct: float) -> None:
        """显示状态"""
        try:
            position_summary = trade_executor.get_position_summary()
            
            total_value = position_summary.get('total_value', 0) or 0
            total_unrealized_pnl = position_summary.get('total_unrealized_pnl', 0) or 0
            total_positions = position_summary.get('total_positions', 0) or 0
            
            # 更新 Web 面板状态
            initial_equity = risk_manager.initial_equity or current_equity
            total_pnl_pct = (current_equity - initial_equity) / initial_equity if initial_equity > 0 else 0
            update_state(
                current_equity=current_equity,
                initial_equity=initial_equity,
                daily_pnl_pct=daily_pnl_pct,
                total_pnl_pct=total_pnl_pct,
                positions=position_summary.get('positions', []),
                win_rate=self._calculate_win_rate(),
                total_trades=len(trade_executor.position_history or []),
                risk_level='低' if daily_pnl_pct > -0.03 else ('中' if daily_pnl_pct > -0.06 else '高'),
                last_update=datetime.now().strftime('%H:%M:%S'),
                uptime=self._get_uptime(),
                cooldown_until=None,
            )
            
            logger.info("-" * 60)
            logger.info(f"[BALANCE] 账户权益: {current_equity:.2f} USDT")
            logger.info(f"[STATS] 当日盈亏: {daily_pnl_pct:+.2%}")
            logger.info(f"[CHART] 持仓数量: {total_positions}/{config.MAX_POSITIONS}")
            logger.info(f"[VALUE] 持仓总值: {total_value:.2f} USDT")
            logger.info(f"[PNL] 未实现盈亏: {total_unrealized_pnl:+.2f} USDT")
            
            positions = position_summary.get('positions', [])
            if positions:
                logger.info("[LIST] 持仓详情:")
                for pos in positions[:5]:
                    unrealized_pnl = pos.get('unrealized_pnl', 0) or 0
                    unrealized_pnl_pct = pos.get('unrealized_pnl_pct', 0) or 0
                    pnl_emoji = "[UP]" if unrealized_pnl >= 0 else "[DN]"
                    logger.info(
                        f"  {pos.get('symbol', '?')} {pos.get('side', '?')}: "
                        f"{pos.get('size', 0):.2f} @ {pos.get('entry_price', 0):.4f} → "
                        f"{pos.get('current_price', 0):.4f} "
                        f"{pnl_emoji} {unrealized_pnl:+.2f} ({unrealized_pnl_pct:+.2%})"
                    )
            
            logger.info("-" * 60)
            
        except Exception as e:
            logger.error(f"显示状态失败: {e}")
    
    def run(self) -> None:
        """运行主循环"""
        if not self.initialize():
            logger.error("初始化失败，程序退出")
            sys.exit(1)
        
        self.running = True
        self.start_time = time.time()
        logger.info(">>> 开始主循环")
        
        try:
            while self.running:
                start_time = time.time()
                
                self.run_cycle()
                
                # 控制循环频率
                cycle_time = time.time() - start_time
                sleep_time = max(5, 30 - cycle_time)  # 至少等待5秒，最多30秒一个周期
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("[BYE] 用户中断")
        except Exception as e:
            logger.error(f"主循环异常: {e}")
            telegram_notifier.send_error_alert(str(e), "主循环")
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """关闭应用程序"""
        logger.info("正在关闭应用程序...")
        
        # 保存最终状态
        self.state_manager.save_state()
        
        # 发送关闭通知
        try:
            balance = exchange_client.get_balance()
            current_equity = balance.get('total', 0) or 0
        except Exception:
            current_equity = 0
        
        telegram_notifier.send_trade_alert(
            "系统关闭",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"最终账户权益: {current_equity:.2f} USDT\n"
            f"运行时间: {self._get_uptime()}"
        )
        
        logger.info("应用程序已关闭")
    
    def _get_uptime(self) -> str:
        """获取运行时间"""
        if self.start_time is None:
            return "未知"
        
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"


def main():
    """主函数"""
    app = TradingApp()
    app.run()


if __name__ == "__main__":
    main()