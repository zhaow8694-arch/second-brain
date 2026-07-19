"""
🔧 后勤保障处 (Logistics & Cost Control) — L3 财务自动化中枢

职责:
  1. 记录每笔交易的预估盈利
  2. 根据盈利动态调整 API 预算
  3. 生成财务日报（收入/支出/净利润）
  4. 利润再投资：盈利 → 增加预算上限

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 只读方式访问 cost_log.json
  - 所有输出写入 logistics_log/ 目录
"""
import os
import json
from datetime import datetime

FINANCE_LOG = "finance_log.json"
LOGISTICS_DIR = "logistics_log"


def ensure_logistics_dir():
    if not os.path.exists(LOGISTICS_DIR):
        os.makedirs(LOGISTICS_DIR)


def load_finance():
    try:
        with open(FINANCE_LOG, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"transactions": [], "total_profit": 0.0, "total_cost": 0.0}


def save_finance(data: dict):
    with open(FINANCE_LOG, "w") as f:
        json.dump(data, f, indent=2)


def record_profit(source: str, amount: float, description: str = ""):
    """记录一笔盈利"""
    data = load_finance()
    entry = {
        "time": datetime.now().isoformat(),
        "type": "profit",
        "source": source,
        "amount": round(amount, 2),
        "description": description,
    }
    data["transactions"].append(entry)
    data["total_profit"] = round(data["total_profit"] + amount, 2)
    save_finance(data)
    return entry


def record_cost(source: str, amount: float, description: str = ""):
    """记录一笔成本支出"""
    data = load_finance()
    entry = {
        "time": datetime.now().isoformat(),
        "type": "cost",
        "source": source,
        "amount": round(amount, 2),
        "description": description,
    }
    data["transactions"].append(entry)
    data["total_cost"] = round(data["total_cost"] + amount, 2)
    save_finance(data)
    return entry


def calculate_net_profit() -> float:
    """计算净利润"""
    data = load_finance()
    return round(data["total_profit"] - data["total_cost"], 2)


def suggest_budget_adjustment() -> dict:
    """根据盈利情况建议预算调整"""
    data = load_finance()
    net = calculate_net_profit()

    current_budget = float(os.getenv("DAILY_API_BUDGET", "5.0"))

    if net <= 0:
        return {
            "action": "维持",
            "reason": f"净利润 ${net}，尚未盈利，建议维持当前预算 ${current_budget}",
            "suggested_budget": current_budget,
        }

    reinvest_rate = 0.3
    additional = round(net * reinvest_rate, 2)
    suggested = round(current_budget + additional, 2)

    return {
        "action": "增资",
        "reason": f"净利润 ${net}，按 {reinvest_rate*100}% 再投资比例，建议增加 ${additional} 预算",
        "suggested_budget": suggested,
        "additional_budget": additional,
    }


def generate_finance_report(session_id: str) -> str:
    """生成财务报告"""
    ensure_logistics_dir()
    data = load_finance()
    net = calculate_net_profit()
    adjustment = suggest_budget_adjustment()

    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_transactions = [
        t for t in data["transactions"]
        if datetime.fromisoformat(t["time"]).date() == datetime.now().date()
    ]

    report_lines = [
        f"# 🔧 后勤保障处 — 财务日报",
        f"**生成时间:** {today}",
        f"**会话编号:** {session_id}",
        "",
        "---",
        "## 一、今日流水",
        "",
    ]

    if today_transactions:
        report_lines.append("| 时间 | 类型 | 来源 | 金额 |")
        report_lines.append("|------|------|------|------|")
        for t in today_transactions:
            emoji = "💰" if t["type"] == "profit" else "💸"
            report_lines.append(f"| {t['time'][:19]} | {emoji} {t['type']} | {t['source']} | ${t['amount']} |")
    else:
        report_lines.append("*今日无交易记录*")

    report_lines.extend([
        "",
        "---",
        "## 二、累计盈亏",
        "",
        f"| 指标 | 金额 |",
        f"|------|------|",
        f"| 累计收入 | ${data['total_profit']} |",
        f"| 累计支出 | ${data['total_cost']} |",
        f"| **净利润** | **${net}** |",
        "",
        "---",
        "## 三、预算建议",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 当前日预算 | ${float(os.getenv('DAILY_API_BUDGET', '5.0'))} |",
        f"| 建议操作 | {adjustment['action']} |",
        f"| 建议日预算 | ${adjustment['suggested_budget']} |",
        f"| 理由 | {adjustment['reason']} |",
        "",
    ])

    report = "\n".join(report_lines)

    report_file = f"{LOGISTICS_DIR}/{session_id}_finance.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    return report_file


def get_logistics_status() -> dict:
    """获取后勤状态"""
    data = load_finance()
    return {
        "total_profit": data["total_profit"],
        "total_cost": data["total_cost"],
        "net_profit": calculate_net_profit(),
        "transaction_count": len(data["transactions"]),
    }
