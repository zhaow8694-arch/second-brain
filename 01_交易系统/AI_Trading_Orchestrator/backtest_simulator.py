# backtest_simulator.py
# 简单回测模拟器 - V1.0

from risk_manager import RiskManager
from signal_generator import SignalGenerator
from datetime import datetime

class BacktestSimulator:
    def __init__(self):
        self.rm = RiskManager(total_capital=20000)
        self.sg = SignalGenerator()
        self.trades = []
        print("✅ 回测模拟器初始化完成")

    def run_simple_backtest(self, num_trades=20):
        """简单回测模拟"""
        print(f"\n=== 开始简单回测 ({num_trades} 笔交易) ===")
        
        win = 0
        total_pnl = 0.0
        
        for i in range(num_trades):
            # 模拟不同市场情况
            if i % 3 == 0:   # 做多
                signal = self.sg.generate_signal(price=4410, ema9_trend="up", ob_type="bull", ob_price=4405)
                pnl = 45 if i % 2 == 0 else -25
            else:            # 做空
                signal = self.sg.generate_signal(price=4430, ema9_trend="down", ob_type="bear", ob_price=4435)
                pnl = 60 if i % 2 == 0 else -30
            
            result = "盈利" if pnl > 0 else "亏损"
            if pnl > 0:
                win += 1
            
            total_pnl += pnl
            self.trades.append({"trade_id": i+1, "direction": signal["direction"], "pnl": pnl, "result": result})
            
            print(f"交易 {i+1:2d} | {signal['direction']:4} | 盈亏: {pnl:+.1f} USD | {result}")
        
        win_rate = round(win / num_trades * 100, 1)
        print(f"\n=== 回测结果 ===")
        print(f"总交易次数: {num_trades}")
        print(f"胜率: {win_rate}%")
        print(f"总盈亏: {total_pnl:.1f} USD")
        print(f"平均每单盈亏: {total_pnl/num_trades:.2f} USD")
        return win_rate, total_pnl

# 测试代码
if __name__ == "__main__":
    bt = BacktestSimulator()
    bt.run_simple_backtest(num_trades=20)