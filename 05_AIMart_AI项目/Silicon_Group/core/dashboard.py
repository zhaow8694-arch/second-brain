"""
📊 全军战力看板 (War Dashboard) — Phase 5 智能进化

职责:
  1. 实时汇总各部门状态（军情局、兵工厂、宣发军、宪兵队、后勤部、教导团）
  2. 显示 API 预算消耗、熔断状态
  3. 显示今日作战次数、成功率
  4. 显示最新复盘报告摘要
  5. 一键生成全军战力报告

设计原则:
  - 只读方式访问所有模块
  - 不修改任何现有代码
  - 所有数据实时聚合
"""
import os
from datetime import datetime


def get_full_status() -> dict:
    """获取全军完整状态"""
    dashboard = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "budget": _get_budget_status(),
        "battle_log": _get_battle_log_status(),
        "academy": _get_academy_status(),
        "logistics": _get_logistics_status(),
        "campaign": _get_campaign_status(),
        "arsenal": _get_arsenal_status(),
        "marketing": _get_marketing_status(),
        "quality_gate": _get_quality_gate_status(),
    }
    return dashboard


def _get_budget_status() -> dict:
    """获取预算状态"""
    try:
        from core.cost_watchdog import get_status, is_meltdown
        status = get_status()
        return {
            "daily_budget": status.get("daily_budget", "unknown"),
            "total_spent": status.get("total_spent", 0),
            "remaining": status.get("remaining", 0),
            "meltdown": is_meltdown(),
        }
    except Exception as e:
        return {"error": str(e)}


def _get_battle_log_status() -> dict:
    """获取作战日志状态"""
    try:
        log_dir = "battle_logs"
        if not os.path.exists(log_dir):
            return {"total_sessions": 0, "total_logs": 0}
        files = [f for f in os.listdir(log_dir) if f.endswith(".md")]
        return {
            "total_sessions": len(files),
            "latest_log": sorted(files, reverse=True)[0] if files else None,
        }
    except Exception as e:
        return {"error": str(e)}


def _get_academy_status() -> dict:
    """获取教导团状态"""
    try:
        from core.academy import get_academy_status
        return get_academy_status()
    except Exception as e:
        return {"error": str(e)}


def _get_logistics_status() -> dict:
    """获取后勤状态"""
    try:
        from core.logistics import get_logistics_status
        return get_logistics_status()
    except Exception as e:
        return {"error": str(e)}


def _get_campaign_status() -> dict:
    """获取战役状态"""
    try:
        from command.campaign import get_campaign_status
        return get_campaign_status()
    except Exception as e:
        return {"error": str(e)}


def _get_arsenal_status() -> dict:
    """获取兵工厂状态"""
    try:
        from arsenal.product_blueprints import PRODUCT_BLUEPRINTS
        output_dir = "arsenal_output"
        products = []
        if os.path.exists(output_dir):
            products = [f for f in os.listdir(output_dir) if f.endswith(".html") or f.endswith(".py")]
        return {
            "blueprints": len(PRODUCT_BLUEPRINTS),
            "products_generated": len(products),
            "product_list": list(PRODUCT_BLUEPRINTS.keys()),
        }
    except Exception as e:
        return {"error": str(e)}


def _get_marketing_status() -> dict:
    """获取宣发军状态"""
    try:
        output_dir = "marketing_output"
        posts = []
        if os.path.exists(output_dir):
            posts = [f for f in os.listdir(output_dir) if f.endswith(".md")]
        return {
            "total_posts": len(posts),
            "latest_post": sorted(posts, reverse=True)[0] if posts else None,
        }
    except Exception as e:
        return {"error": str(e)}


def _get_quality_gate_status() -> dict:
    """获取质量门禁状态"""
    try:
        from core.quality_gate import get_audit_rules_summary
        return {
            "rules": get_audit_rules_summary(),
        }
    except Exception as e:
        return {"error": str(e)}


def print_dashboard():
    """打印全军战力看板到控制台"""
    status = get_full_status()

    print(f"\n{'='*60}")
    print(f"  📊 硅基远征军 — 全军战力看板")
    print(f"  {status['timestamp']}")
    print(f"{'='*60}")

    budget = status.get("budget", {})
    meltdown_icon = "🔴" if budget.get("meltdown") else "🟢"
    print(f"\n  💰 预算状态 {meltdown_icon}")
    print(f"     日预算: ${budget.get('daily_budget', '?')}")
    print(f"     已消耗: ${budget.get('total_spent', 0):.2f}")
    print(f"     剩余: ${budget.get('remaining', 0):.2f}")

    logs = status.get("battle_log", {})
    print(f"\n  📋 作战日志")
    print(f"     总会话数: {logs.get('total_sessions', 0)}")
    if logs.get("latest_log"):
        print(f"     最新日志: {logs['latest_log']}")

    academy = status.get("academy", {})
    print(f"\n  🎓 教导团")
    print(f"     复盘报告: {academy.get('total_reports', 0)} 份")

    logistics = status.get("logistics", {})
    print(f"\n  🔧 后勤部")
    print(f"     净利润: ${logistics.get('net_profit', 0)}")
    print(f"     交易次数: {logistics.get('transaction_count', 0)}")

    arsenal = status.get("arsenal", {})
    print(f"\n  🏭 兵工厂")
    print(f"     产品蓝图: {arsenal.get('blueprints', 0)} 个")
    print(f"     已生成: {arsenal.get('products_generated', 0)} 个")

    marketing = status.get("marketing", {})
    print(f"\n  🌊 宣发军")
    print(f"     已发布: {marketing.get('total_posts', 0)} 条")

    campaign = status.get("campaign", {})
    print(f"\n  🔄 战役编排")
    print(f"     总战役: {campaign.get('total_campaigns', 0)} 次")
    print(f"     可用模板: {len(campaign.get('available_templates', []))} 个")

    quality = status.get("quality_gate", {})
    rules = quality.get("rules", [])
    print(f"\n  🛡️ 质量门禁")
    print(f"     审计规则: {len(rules) if isinstance(rules, list) else 0} 条")

    print(f"\n{'='*60}")
    print(f"  ✅ 全军状态报告完毕")
    print(f"{'='*60}\n")


def generate_dashboard_report(session_id: str) -> str:
    """生成全军战力报告文件"""
    status = get_full_status()

    report_dir = "dashboard_reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    lines = [
        f"# 📊 硅基远征军 — 全军战力报告",
        f"**生成时间:** {status['timestamp']}",
        f"**会话编号:** {session_id}",
        "",
        "---",
        "## 一、预算状态",
        "",
    ]

    budget = status.get("budget", {})
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 日预算 | ${budget.get('daily_budget', '?')} |")
    lines.append(f"| 已消耗 | ${budget.get('total_spent', 0):.2f} |")
    lines.append(f"| 剩余 | ${budget.get('remaining', 0):.2f} |")
    lines.append(f"| 熔断状态 | {'🔴 已触发' if budget.get('meltdown') else '🟢 正常'} |")
    lines.append("")

    logs = status.get("battle_log", {})
    lines.append("---")
    lines.append("## 二、作战日志")
    lines.append("")
    lines.append(f"- 总会话数: {logs.get('total_sessions', 0)}")
    lines.append(f"- 最新日志: {logs.get('latest_log', '无')}")
    lines.append("")

    academy = status.get("academy", {})
    lines.append("---")
    lines.append("## 三、教导团")
    lines.append("")
    lines.append(f"- 复盘报告: {academy.get('total_reports', 0)} 份")
    lines.append(f"- 最新报告: {academy.get('latest_report', '无')}")
    lines.append("")

    logistics = status.get("logistics", {})
    lines.append("---")
    lines.append("## 四、后勤部")
    lines.append("")
    lines.append(f"| 指标 | 金额 |")
    lines.append(f"|------|------|")
    lines.append(f"| 累计收入 | ${logistics.get('total_profit', 0)} |")
    lines.append(f"| 累计支出 | ${logistics.get('total_cost', 0)} |")
    lines.append(f"| 净利润 | ${logistics.get('net_profit', 0)} |")
    lines.append("")

    arsenal = status.get("arsenal", {})
    lines.append("---")
    lines.append("## 五、兵工厂")
    lines.append("")
    lines.append(f"- 产品蓝图: {arsenal.get('blueprints', 0)} 个")
    lines.append(f"- 已生成产品: {arsenal.get('products_generated', 0)} 个")
    lines.append(f"- 产品线: {', '.join(arsenal.get('product_list', []))}")
    lines.append("")

    marketing = status.get("marketing", {})
    lines.append("---")
    lines.append("## 六、宣发军")
    lines.append("")
    lines.append(f"- 已发布内容: {marketing.get('total_posts', 0)} 条")
    lines.append(f"- 最新内容: {marketing.get('latest_post', '无')}")
    lines.append("")

    campaign = status.get("campaign", {})
    lines.append("---")
    lines.append("## 七、战役编排")
    lines.append("")
    lines.append(f"- 总战役次数: {campaign.get('total_campaigns', 0)}")
    lines.append(f"- 可用模板: {', '.join(campaign.get('available_templates', []))}")
    lines.append("")

    quality = status.get("quality_gate", {})
    rules = quality.get("rules", [])
    lines.append("---")
    lines.append("## 八、质量门禁")
    lines.append("")
    lines.append(f"- 审计规则: {len(rules) if isinstance(rules, list) else 0} 条")
    lines.append("")

    report = "\n".join(lines)

    report_file = f"{report_dir}/{session_id}_dashboard.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    return report_file
