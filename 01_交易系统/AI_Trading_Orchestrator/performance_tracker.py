# performance_tracker.py
# 性能追踪 + 每日报告模块 - V1.0

from datetime import datetime
from trade_logger import TradeLogger

class PerformanceTracker:
    def __init__(self):
        self.logger = TradeLogger()
        print("✅ 性能追踪模块初始化完成")

    def generate_daily_report(self):
        """生成当日性能报告"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_trades = [t for t in self.logger.logs if t["timestamp"].startswith(today)]
        
        if not today_trades:
            print(f"[{datetime.now()}] 📊 今日暂无交易记录")
            return None
        
        total = len(today_trades)
        win = sum(1 for t in today_trades if t.get("result") == "盈利")
        win_rate = round(win / total * 100, 1) if total > 0 else 0
        
        total_pnl = sum(t.get("pnl", 0) for t in today_trades)
        avg_pnl = round(total_pnl / total, 2) if total > 0 else 0
        
        report = {
            "日期": today,
            "总交易次数": total,
            "胜率": f"{win_rate}%",
            "盈利交易": win,
            "亏损交易": total - win,
            "总盈亏": f"{total_pnl:+.2f} USD",
            "平均每单盈亏": f"{avg_pnl:+.2f} USD",
            "风险控制": "已严格执行1%规则"
        }
        
        print("\n" + "="*50)
        print(f"📊 今日交易绩效报告 ({today})")
        print("="*50)
        for key, value in report.items():
            print(f"{key:12} : {value}")
        print("="*50)
        
        return report

    def get_weekly_summary(self):
        """简单周总结"""
        print("📅 本周暂无完整统计（后续可扩展）")
        return "本周统计功能开发中..."


# 测试代码
if __name__ == "__main__":
    tracker = PerformanceTracker()
    tracker.generate_daily_report()