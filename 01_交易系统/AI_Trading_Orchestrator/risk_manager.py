# risk_manager.py
# 黄金交易风险管理系统 - V1.0

class RiskManager:
    def __init__(self, total_capital=20000):
        self.total_capital = total_capital
        self.trading_capital = total_capital * 0.3   # 只用30%资金交易
        self.max_risk_per_trade = 0.01               # 单笔最大风险 1%
        
    def calculate_position_size(self, entry_price, stop_loss):
        """
        计算黄金交易手数（严格控制1%风险）
        """
        if stop_loss == entry_price:
            return 0.0
            
        # 止损距离（美元）
        stop_distance = abs(entry_price - stop_loss)
        
        # 单笔最大风险金额
        risk_amount = self.trading_capital * self.max_risk_per_trade
        
        # 黄金1手每点价值 ≈ 100美元
        point_value = 100
        
        # 计算手数
        lots = risk_amount / (stop_distance * point_value)
        
        # 限制最大手数
        max_lots = 0.12
        lots = min(lots, max_lots)
        
        return round(lots, 2)
    
    def check_daily_loss_limit(self, today_pnl):
        """检查当日亏损是否超过限制"""
        daily_limit = self.trading_capital * 0.05   # 每日最大亏损5%
        if today_pnl <= -daily_limit:
            return False, f"⚠️ 今日亏损已达上限 {today_pnl:.2f}，系统自动停止交易"
        return True, f"今日亏损: {today_pnl:.2f} / 限额: {daily_limit:.2f}"
    
    def get_risk_status(self):
        """返回当前风险状态"""
        return {
            "总资金": self.total_capital,
            "交易资金": round(self.trading_capital, 2),
            "单笔最大风险": f"{self.max_risk_per_trade*100}%",
            "单笔最大亏损金额": round(self.trading_capital * self.max_risk_per_trade, 2),
            "每日最大亏损": round(self.trading_capital * 0.05, 2),
        }

# 测试代码（直接运行此文件可测试）
if __name__ == "__main__":
    rm = RiskManager(total_capital=20000)
    print("=== 风险管理系统初始化成功 ===")
    print(rm.get_risk_status())
    
    lots = rm.calculate_position_size(entry_price=4415, stop_loss=4400)
    print(f"建议手数: {lots} 手")