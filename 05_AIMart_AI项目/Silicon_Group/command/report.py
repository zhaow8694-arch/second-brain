import os
import subprocess
from datetime import datetime
from core.cost_watchdog import get_status


def generate_report(session_id: str, watch_list: list, final_output: str) -> str:
    cost_status = get_status()
    report_name = "SILICON_GROUP_REPORT.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_content = f"""# ⚔️ 硅基远征军：统帅部作战报告
---
**会话编号:** {session_id}
**执行时间:** {now}

## 💰 成本消耗
- 今日已消耗: **${cost_status['today_cost']}**
- 日预算: **${cost_status['daily_budget']}**
- 剩余: **${cost_status['remaining']}**
- 熔断状态: {'❌ 已熔断' if cost_status['meltdown'] else '✅ 正常'}

## 🎖️ 作战结果
{final_output}

---
*本报告由统帅部自动签发。详细日志见 battle_logs/ 目录。*
"""

    with open(report_name, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_name


def open_report(report_name: str):
    try:
        if os.name == "nt":
            os.startfile(report_name)
        else:
            subprocess.call(("open" if os.uname().sysname == "Darwin" else "xdg-open", report_name))
    except:
        pass
