# trade_logger.py
# 交易日志记录模块 - V1.0

import json
from datetime import datetime
import os

class TradeLogger:
    def __init__(self, log_file="trade_logs.json"):
        self.log_file = log_file
        self.logs = self.load_logs()
        print(f"✅ 交易日志系统初始化完成（共 {len(self.logs)} 条历史记录）")

    def load_logs(self):
        """加载历史日志"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_logs(self):
        """保存日志到文件"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

    def record_trade(self, signal: dict, result: str = "待执行", pnl: float = 0.0):
        """记录一笔交易"""
        trade = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "direction": signal.get("direction"),
            "entry_zone": signal.get("entry_zone"),
            "stop_loss": signal.get("stop_loss"),
            "lots": signal.get("lots"),
            "reason": signal.get("reason"),
            "result": result,          # 待执行 / 盈利 / 亏损 / 平仓
            "pnl": pnl                 # 盈亏金额
        }
        
        self.logs.append(trade)
        self.save_logs()
        
        print(f"📝 交易记录成功 | {trade['direction']} | 手数 {trade['lots']} | 结果：{trade['result']}")
        return trade

    def get_today_summary(self):
        """今日交易总结"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_trades = [t for t in self.logs if t["timestamp"].startswith(today)]
        
        if not today_trades:
            return "今日暂无交易记录"
        
        win = sum(1 for t in today_trades if t["result"] == "盈利")
        total = len(today_trades)
        win_rate = round(win / total * 100, 1) if total > 0 else 0
        
        return f"今日交易 {total} 单 | 胜率 {win_rate}% | 盈利 {win} 单"

# 测试代码
if __name__ == "__main__":
    logger = TradeLogger()
    
    test_signal = {
        'direction': '做空',
        'entry_zone': '4430.0 附近',
        'stop_loss': 4445,
        'lots': 0.03,
        'reason': '4H/Daily Bear OB + EMA9向下'
    }
    
    logger.record_trade(test_signal, result="待执行")
    print(logger.get_today_summary())