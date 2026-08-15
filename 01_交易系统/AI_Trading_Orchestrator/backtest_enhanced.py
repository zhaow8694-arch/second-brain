# backtest_enhanced.py
# 高级回测 + 详细胜率统计模块 - V1.0

from trade_logger import TradeLogger
from datetime import datetime

class BacktestEnhanced:
    def __init__(self):
        self.logger = TradeLogger()
        print("✅ 高级回测模块初始化完成")

    def run_enhanced_backtest(self):
        """生成详细回测报告"""
        trades = self.logger.logs
        if len(trades) < 3:
            print("⚠️ 交易记录过少（少于3条），暂无法生成详细回测")
            return None
        
        total = len(trades)
        win = sum(1 for t in trades if t.get("result") == "盈利")
        win_rate = round(win / total * 100, 1)
        
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        avg_pnl = round(total_pnl / total, 2) if total > 0 else 0
        
        # 连续盈利/亏损统计
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 0
        current_is_win = None
        
        for t in trades:
            is_win = t.get("result") == "盈利"
            if current_is_win == is_win:
                current_streak += 1
            else:
                current_streak = 1
                current_is_win = is_win
            if is_win:
                max_win_streak = max(max_win_streak, current_streak)
            else:
                max_loss_streak = max(max_loss_streak, current_streak)
        
        report = {
            "日期": datetime.now().strftime("%Y-%m-%d"),
            "总交易次数": total,
            "胜率": f"{win_rate}%",
            "盈利交易": win,
            "亏损交易": total - win,
            "总盈亏": f"{total_pnl:+.2f} USD",
            "平均每单盈亏": f"{avg_pnl:+.2f} USD",
            "最大连续盈利": max_win_streak,
            "最大连续亏损": max_loss_streak,
        }
        
        print("\n" + "="*60)
        print(f"📊 高级回测报告 ({report['日期']})")
        print("="*60)
        for key, value in report.items():
            print(f"{key:12} : {value}")
        print("="*60)
        
        return report


# 测试代码
if __name__ == "__main__":
    bt = BacktestEnhanced()
    bt.run_enhanced_backtest()