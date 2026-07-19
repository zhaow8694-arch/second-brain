import sys, os, json
sys.path.insert(0, '.')

# 重置投资组合
os.makedirs("portfolio_log", exist_ok=True)
default = {"cash": 100000, "positions": {}, "orders": [], "total_trades": 0, "realized_pnl": 0.0, "created_at": "2026-04-27T00:00:00"}
with open("portfolio_log/portfolio.json", "w") as f:
    json.dump(default, f, indent=2)
print("投资组合已重置: $100000 现金")

# 执行金融分析
from command.operations import run_financial_mission
result = run_financial_mission("auto_exec_test", symbols=["XAU/USD"])
print("\n=== 执行完成 ===")
