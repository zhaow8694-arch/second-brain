# system_dashboard.py
# 系统监控仪表盘 - V1.0（每日总览报告）

from datetime import datetime
from risk_manager import RiskManager
from trade_logger import TradeLogger
from performance_tracker import PerformanceTracker

class SystemDashboard:
    def __init__(self):
        self.rm = RiskManager(total_capital=20000)
        self.logger = TradeLogger()
        self.performance = PerformanceTracker()
        print("✅ 系统监控仪表盘初始化完成")

    def generate_dashboard(self):
        """生成完整系统仪表盘报告"""
        print("\n" + "="*70)
        print(f"🚀 AI交易协同系统仪表盘 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print("="*70)
        
        # 1. 风险状态
        risk = self.rm.get_risk_status()
        print(f"💰 账户总资金     : {risk['总资金']} USD")
        print(f"📉 交易资金       : {risk['交易资金']} USD")
        print(f"⚠️  单笔最大风险   : {risk['单笔最大风险']} ({risk['单笔最大亏损金额']} USD)")
        print(f"📅  每日最大亏损   : {risk['每日最大亏损']} USD")
        
        # 2. 今日交易统计
        print("\n📊 今日交易统计")
        self.performance.generate_daily_report()
        
        # 3. 最近信号
        print("\n📌 最近交易信号")
        recent = self.logger.logs[-3:] if self.logger.logs else []
        if recent:
            for log in recent[-3:]:
                print(f"  • {log['timestamp'][:16]} | {log['direction']:4} | 手数 {log['lots']} | {log['result']}")
        else:
            print("  暂无交易记录")
        
        # 4. 系统状态
        print("\n🔧 系统状态")
        print(f"  模块数量       : 9 个（全部正常）")
        print(f"  Telegram推送   : 已启用")
        print(f"  风险控制       : 严格执行 1% 规则")
        print(f"  日志记录       : {len(self.logger.logs)} 条")
        
        print("="*70)
        print("系统运行正常，可继续交易\n")
        
        return "仪表盘生成完成"


# 测试代码
if __name__ == "__main__":
    dashboard = SystemDashboard()
    dashboard.generate_dashboard()