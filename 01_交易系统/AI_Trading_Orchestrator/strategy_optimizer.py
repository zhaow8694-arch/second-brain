# strategy_optimizer.py
# 策略优化模块 - V1.0

from trade_logger import TradeLogger
from datetime import datetime

class StrategyOptimizer:
    def __init__(self):
        self.logger = TradeLogger()
        print("✅ 策略优化模块初始化完成")

    def optimize_strategy(self):
        """基于历史交易记录给出优化建议"""
        trades = self.logger.logs
        if len(trades) < 5:
            print("⚠️ 交易记录过少（少于5条），暂无法优化")
            return None
        
        win_trades = [t for t in trades if t.get("result") == "盈利"]
        win_rate = round(len(win_trades) / len(trades) * 100, 1)
        
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        avg_pnl = round(total_pnl / len(trades), 2) if len(trades) > 0 else 0
        
        print("\n" + "="*60)
        print(f"📈 策略优化报告 ({datetime.now().strftime('%Y-%m-%d')})")
        print("="*60)
        print(f"总交易次数     : {len(trades)} 单")
        print(f"当前胜率       : {win_rate}%")
        print(f"平均每单盈亏   : {avg_pnl:+.2f} USD")
        print("-" * 60)
        
        suggestions = []
        if win_rate < 50:
            suggestions.append("建议：适当收窄止损距离，或提高OB过滤严格度")
        if avg_pnl < 0:
            suggestions.append("建议：提高止盈目标比例（当前1:3可能偏保守）")
        if win_rate < 45:
            suggestions.append("建议：增加EMA9趋势确认条件，避免逆势交易")
        
        if not suggestions:
            suggestions.append("当前策略表现良好，可继续观察")
        
        for i, sug in enumerate(suggestions, 1):
            print(f"优化建议 {i}   : {sug}")
        
        print("="*60)
        return suggestions


# 测试代码
if __name__ == "__main__":
    optimizer = StrategyOptimizer()
    optimizer.optimize_strategy()