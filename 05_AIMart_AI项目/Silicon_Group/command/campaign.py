"""
🔄 跨部门联合战役编排 (Campaign Orchestrator)

职责:
  1. 定义标准战役模板（SOP）
  2. 按模板自动编排多部门协同任务
  3. 自动执行战役：按计划书自动调用各部门作战函数 [Phase 5]
  4. 跟踪战役进度，生成战役报告

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 调用 operations.py 中的现有作战函数
  - 所有输出写入 campaign_log/ 目录
"""
import os
import json
from datetime import datetime
from core.battle_log import write_log

CAMPAIGN_DIR = "campaign_log"


def ensure_campaign_dir():
    if not os.path.exists(CAMPAIGN_DIR):
        os.makedirs(CAMPAIGN_DIR)


CAMPAIGN_TEMPLATES = {
    "产品全生命周期": {
        "description": "从市场调研 → 产品开发 → 推广发布 → 数据回收 全流程",
        "phases": [
            {"name": "市场调研", "module": "军情局", "action": "分析目标市场需求"},
            {"name": "产品开发", "module": "兵工厂", "action": "AI 生成产品代码"},
            {"name": "质量审计", "module": "宪兵队", "action": "代码安全与功能审查"},
            {"name": "推广发布", "module": "宣发军", "action": "多语言多平台推广"},
            {"name": "数据回收", "module": "后勤部", "action": "记录成本与预估收益"},
        ],
    },
    "金融闪电战": {
        "description": "情报 → 量化 → 风控 快速交易决策",
        "phases": [
            {"name": "情报收集", "module": "军情局", "action": "抓取多标的实时数据"},
            {"name": "量化分析", "module": "金融军团", "action": "多标的策略制定"},
            {"name": "风控审计", "module": "宪兵队", "action": "2% 止损红线审查"},
            {"name": "战果记录", "module": "后勤部", "action": "记录交易盈亏"},
        ],
    },
    "全域内容轰炸": {
        "description": "针对已有产品，发动全平台全语言内容覆盖",
        "phases": [
            {"name": "内容生产", "module": "宣发军", "action": "生成 3 平台 × 4 语言文案"},
            {"name": "合规审查", "module": "宪兵队", "action": "检查文案是否触碰平台红线"},
            {"name": "发布跟踪", "module": "后勤部", "action": "记录发布成本"},
        ],
    },
}


def list_templates() -> dict:
    """列出所有可用战役模板"""
    return {k: {"description": v["description"], "phases": len(v["phases"])} for k, v in CAMPAIGN_TEMPLATES.items()}


def get_template(name: str) -> dict:
    """获取指定战役模板"""
    return CAMPAIGN_TEMPLATES.get(name)


def create_campaign(session_id: str, template_name: str, target: str = "") -> str:
    """创建一场联合战役，生成战役计划书"""
    ensure_campaign_dir()
    template = CAMPAIGN_TEMPLATES.get(template_name)
    if not template:
        return f"错误: 未找到战役模板 '{template_name}'"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    campaign_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    plan_lines = [
        f"# 🔄 联合战役计划书",
        f"**战役编号:** {campaign_id}",
        f"**模板:** {template_name}",
        f"**目标:** {target or '未指定'}",
        f"**创建时间:** {now}",
        f"**关联会话:** {session_id}",
        "",
        "---",
        "## 战役阶段",
        "",
    ]

    for i, phase in enumerate(template["phases"], 1):
        plan_lines.append(f"### 阶段 {i}: {phase['name']}")
        plan_lines.append(f"- **执行单位:** {phase['module']}")
        plan_lines.append(f"- **行动:** {phase['action']}")
        plan_lines.append(f"- **状态:** ⏳ 待执行")
        plan_lines.append("")

    plan_lines.extend([
        "---",
        "## 资源预估",
        "",
        "| 阶段 | 涉及模块 | 预估成本 |",
        "|------|----------|----------|",
    ])

    cost_map = {
        "军情局": "$0.01",
        "兵工厂": "$0.02",
        "宪兵队": "$0.01",
        "宣发军": "$0.01",
        "金融军团": "$0.02",
        "后勤部": "$0.00",
    }

    for phase in template["phases"]:
        plan_lines.append(f"| {phase['name']} | {phase['module']} | {cost_map.get(phase['module'], '$0.01')} |")

    plan_lines.append("")
    plan_lines.append(f"**预估总成本:** $0.05 ~ $0.10")
    plan_lines.append("")

    plan = "\n".join(plan_lines)

    campaign_file = f"{CAMPAIGN_DIR}/{campaign_id}.md"
    with open(campaign_file, "w", encoding="utf-8") as f:
        f.write(plan)

    write_log(session_id, "CAMPAIGN_CREATED", template_name, f"战役计划书已生成: {campaign_id}")

    return campaign_file


def execute_campaign(session_id: str, template_name: str, target: str = "") -> str:
    """自动执行一场战役 — 按计划书自动调用各部门作战函数 [Phase 5]

    这是战役编排的核心升级：不再只是生成计划书，而是真正自动执行。
    """
    ensure_campaign_dir()
    template = CAMPAIGN_TEMPLATES.get(template_name)
    if not template:
        return f"错误: 未找到战役模板 '{template_name}'"

    campaign_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}")
    print(f"  🔄 战役自动执行: {template_name}")
    print(f"  战役编号: {campaign_id}")
    print(f"{'='*60}")

    results = []
    total_cost = 0.0

    for i, phase in enumerate(template["phases"], 1):
        print(f"\n{'─'*40}")
        print(f"  阶段 {i}/{len(template['phases'])}: {phase['name']} ({phase['module']})")
        print(f"  行动: {phase['action']}")
        print(f"{'─'*40}")

        phase_result = _execute_phase(session_id, phase, target)
        results.append(phase_result)
        total_cost += phase_result.get("cost", 0)

        print(f"  ✅ 阶段完成: {phase_result.get('status', 'unknown')}")

    report_lines = [
        f"# 🔄 战役执行报告",
        f"**战役编号:** {campaign_id}",
        f"**模板:** {template_name}",
        f"**目标:** {target or '未指定'}",
        f"**执行时间:** {now}",
        f"**关联会话:** {session_id}",
        f"**总成本:** ${total_cost:.2f}",
        "",
        "---",
        "## 执行记录",
        "",
    ]

    for i, r in enumerate(results, 1):
        report_lines.append(f"### 阶段 {i}: {r.get('phase_name', '')}")
        report_lines.append(f"- **状态:** {r.get('status', 'unknown')}")
        report_lines.append(f"- **结果:** {r.get('result', '无')[:200]}")
        report_lines.append(f"- **成本:** ${r.get('cost', 0):.2f}")
        report_lines.append("")

    report = "\n".join(report_lines)

    campaign_file = f"{CAMPAIGN_DIR}/{campaign_id}_executed.md"
    with open(campaign_file, "w", encoding="utf-8") as f:
        f.write(report)

    write_log(session_id, "CAMPAIGN_EXECUTED", template_name, f"战役自动执行完成: {campaign_id}, 总成本 ${total_cost:.2f}")

    return campaign_file


def _execute_phase(session_id: str, phase: dict, target: str) -> dict:
    """执行单个战役阶段

    根据阶段模块和行动，自动调用对应的作战函数。
    """
    from core.cost_watchdog import record_call

    module = phase.get("module", "")
    action = phase.get("action", "")
    phase_name = phase.get("name", "")

    try:
        if module == "兵工厂":
            from arsenal.product_blueprints import PRODUCT_BLUEPRINTS
            from arsenal.code_generator import generate_product

            product_name = target or list(PRODUCT_BLUEPRINTS.keys())[0]
            blueprint = PRODUCT_BLUEPRINTS.get(product_name)
            if blueprint:
                generate_product(session_id, product_name, blueprint)
                record_call("战役-兵工厂", 0, 0.02)
                return {"phase_name": phase_name, "status": "success", "result": f"产品 {product_name} 生成完成", "cost": 0.02}
            return {"phase_name": phase_name, "status": "skipped", "result": f"未找到产品蓝图: {product_name}", "cost": 0}

        elif module == "宣发军":
            from marketing.content_factory import create_post

            product_name = target or "默认产品"
            platforms = ["twitter", "reddit", "telegram"]
            languages = ["en", "zh", "id", "ja"]
            count = 0
            for platform in platforms:
                for lang in languages:
                    create_post(session_id, product_name, "", platform, lang)
                    count += 1
            record_call("战役-宣发军", 0, 0.01 * count)
            return {"phase_name": phase_name, "status": "success", "result": f"生成 {count} 条推广内容", "cost": 0.01 * count}

        elif module == "宪兵队":
            from core.quality_gate import cross_audit

            audit_content = f"战役自动审计: {action} - {target}"
            result = cross_audit(session_id, audit_content, "agent_evolution")
            record_call("战役-宪兵队", 0, 0.01)
            return {"phase_name": phase_name, "status": "passed" if result["passed"] else "rejected", "result": result["reason"], "cost": 0.01}

        elif module == "后勤部":
            from core.logistics import record_cost

            record_cost("战役执行", 0.05, f"战役阶段: {phase_name}")
            return {"phase_name": phase_name, "status": "success", "result": "成本已记录", "cost": 0}

        elif module == "军情局":
            return {"phase_name": phase_name, "status": "simulated", "result": f"军情局模拟: {action}", "cost": 0}

        elif module == "金融军团":
            return {"phase_name": phase_name, "status": "simulated", "result": f"金融军团模拟: {action}", "cost": 0}

        else:
            return {"phase_name": phase_name, "status": "unknown", "result": f"未知模块: {module}", "cost": 0}

    except Exception as e:
        return {"phase_name": phase_name, "status": "error", "result": f"执行异常: {str(e)}", "cost": 0}


def get_campaign_status() -> dict:
    """获取所有战役的状态"""
    ensure_campaign_dir()
    campaigns = []
    if os.path.exists(CAMPAIGN_DIR):
        for f in sorted(os.listdir(CAMPAIGN_DIR), reverse=True):
            if f.endswith(".md"):
                campaigns.append(f.replace(".md", ""))
    return {
        "total_campaigns": len(campaigns),
        "latest_campaign": campaigns[0] if campaigns else None,
        "available_templates": list(CAMPAIGN_TEMPLATES.keys()),
    }
