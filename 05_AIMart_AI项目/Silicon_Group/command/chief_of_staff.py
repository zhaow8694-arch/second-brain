"""
👑 AI 总参谋长 (Chief of Staff) — 集团 CEO

职责:
  1. 理解总司令（你）的自然语言战略指令
  2. 自动拆解为子任务列表，按依赖关系排序
  3. 逐个调用对应部门作战函数
  4. 收集每个部门的输出，传递给下游部门
  5. 汇总最终报告

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 通过 import 调用 operations.py 中的现有作战函数
  - 所有输出写入 chief_log/ 目录
  - 可离线运行（不依赖 LLM），也支持 LLM 增强拆解
"""
import os
import json
import importlib
from datetime import datetime
from core.battle_log import write_log, save_snapshot, load_snapshot

CHIEF_LOG_DIR = "chief_log"


def ensure_chief_dir():
    if not os.path.exists(CHIEF_LOG_DIR):
        os.makedirs(CHIEF_LOG_DIR)


# ============================================================
# 部门注册表 — 总参谋长知道每个部门能做什么
# ============================================================
DEPARTMENT_REGISTRY = {
    "军情局": {
        "module": "core.market_data",
        "function": "get_market_data",
        "description": "获取实时行情数据与历史 K 线",
        "input": "symbol",
        "output": "行情数据字典",
        "auto_compatible": True,
    },
    "金融军团": {
        "module": "command.operations",
        "function": "run_financial_mission",
        "description": "多标的交易策略分析（情报+量化+风控）",
        "input": "session_id",
        "output": "交易分析报告",
        "auto_compatible": False,
        "accepts_targets": True,
    },
    "兵工厂": {
        "module": "command.operations",
        "function": "run_arsenal_mission",
        "description": "AI 批量生产小程序/小游戏/工具",
        "input": "session_id",
        "output": "产品代码文件路径",
        "auto_compatible": False,
    },
    "宣发军": {
        "module": "command.operations",
        "function": "run_marketing_mission",
        "description": "多语言多平台推广内容生成",
        "input": "session_id",
        "output": "推广内容文件路径",
        "auto_compatible": False,
    },
    "宪兵队": {
        "module": "core.quality_gate",
        "function": "get_audit_rules_summary",
        "description": "质量审计规则查询",
        "input": "",
        "output": "审计规则摘要",
        "auto_compatible": True,
    },
    "后勤部": {
        "module": "core.logistics",
        "function": "get_logistics_status",
        "description": "财务报告与预算建议",
        "input": "",
        "output": "财务状态字典",
        "auto_compatible": True,
    },
    "教导团": {
        "module": "core.academy",
        "function": "get_academy_status",
        "description": "AI 复盘失败记录，优化全军战力",
        "input": "",
        "output": "教导团状态字典",
        "auto_compatible": True,
    },
    "影子特工处": {
        "module": "core.identity_manager",
        "function": "get_identity_status",
        "description": "数字身份管理与指纹模拟",
        "input": "",
        "output": "身份状态字典",
        "auto_compatible": True,
    },
    "中央知识库": {
        "module": "core.rag_engine",
        "function": "get_rag_status",
        "description": "知识管理与检索",
        "input": "",
        "output": "知识库状态字典",
        "auto_compatible": True,
    },
    "物理防火墙": {
        "module": "core.guard_dog",
        "function": "patrol",
        "description": "系统安全巡逻与熔断",
        "input": "",
        "output": "巡逻报告字典",
        "auto_compatible": True,
    },
    "全军看板": {
        "module": "core.dashboard",
        "function": "get_full_status",
        "description": "实时显示各部门 KPI",
        "input": "",
        "output": "全系统状态字典",
        "auto_compatible": True,
    },
    "策略回测": {
        "module": "core.backtester",
        "function": "get_available_strategies",
        "description": "用历史数据验证交易策略",
        "input": "",
        "output": "可用策略字典",
        "auto_compatible": True,
    },
    "投资组合": {
        "module": "core.portfolio",
        "function": "get_portfolio_summary",
        "description": "查看虚拟仓位与盈亏",
        "input": "",
        "output": "组合摘要字典",
        "auto_compatible": True,
    },
}


# ============================================================
# 任务拆解引擎
# ============================================================
TASK_TEMPLATES = {
    "金融分析": {
        "description": "分析某个标的的市场情况",
        "steps": [
            {"department": "军情局", "action": "获取 {target} 实时行情与历史数据", "depends_on": []},
            {"department": "策略回测", "action": "对 {target} 运行策略回测", "depends_on": ["军情局"]},
            {"department": "金融军团", "action": "综合情报与回测结果进行交易分析", "depends_on": ["军情局", "策略回测"]},
            {"department": "后勤部", "action": "记录本次分析成本", "depends_on": ["金融军团"]},
        ],
    },
    "产品开发推广": {
        "description": "开发一个数字产品并推广到全球",
        "steps": [
            {"department": "兵工厂", "action": "生产 {target} 产品代码", "depends_on": []},
            {"department": "宪兵队", "action": "审计产品代码安全与质量", "depends_on": ["兵工厂"]},
            {"department": "宣发军", "action": "为 {target} 生成多语言推广内容", "depends_on": ["兵工厂"]},
            {"department": "后勤部", "action": "记录生产成本与预估收益", "depends_on": ["宣发军"]},
        ],
    },
    "全系统体检": {
        "description": "检查全系统各部门运行状态",
        "steps": [
            {"department": "全军看板", "action": "生成各部门 KPI 看板", "depends_on": []},
            {"department": "物理防火墙", "action": "执行系统安全巡逻", "depends_on": []},
            {"department": "后勤部", "action": "生成财务报告", "depends_on": []},
            {"department": "教导团", "action": "检查近期失败记录", "depends_on": []},
        ],
    },
    "知识沉淀": {
        "description": "将某个经验沉淀到中央知识库",
        "steps": [
            {"department": "中央知识库", "action": "搜索已有相关知识", "depends_on": []},
            {"department": "教导团", "action": "分析相关失败记录", "depends_on": ["中央知识库"]},
            {"department": "中央知识库", "action": "添加新知识条目", "depends_on": ["教导团"]},
        ],
    },
    "全域总攻": {
        "description": "全自动流水线：生产 → 推广 → 记录",
        "steps": [
            {"department": "兵工厂", "action": "生产 {target} 产品代码", "depends_on": []},
            {"department": "宣发军", "action": "为 {target} 生成多语言推广内容", "depends_on": ["兵工厂"]},
            {"department": "后勤部", "action": "记录本次总攻成本", "depends_on": ["宣发军"]},
        ],
    },
    "自定义": {
        "description": "自由组合各部门任务",
        "steps": [],
    },
}


def list_departments() -> dict:
    """列出总参谋长知道的所有部门"""
    return {k: {"description": v["description"]} for k, v in DEPARTMENT_REGISTRY.items()}


def list_task_templates() -> dict:
    """列出所有可用任务模板"""
    return {k: {"description": v["description"], "steps": len(v["steps"])} for k, v in TASK_TEMPLATES.items()}


def _call_department(department: str, session_id: str, target: str = "", all_targets: list = None) -> str:
    """调用指定部门的作战函数

    支持两种模式:
      1. auto_compatible=True: 直接调用底层模块函数（无交互，适合自动执行）
      2. auto_compatible=False: 走 operations.py 的交互式包装（需要用户输入）
    """
    dept_info = DEPARTMENT_REGISTRY.get(department)
    if not dept_info:
        return f"错误: 未知部门 '{department}'"

    if all_targets is None:
        all_targets = [target] if target else []

    try:
        mod = importlib.import_module(dept_info["module"])
        func = getattr(mod, dept_info["function"])

        if dept_info.get("auto_compatible", False):
            func_name = dept_info["function"]
            if func_name == "get_market_data":
                result = func(target or "XAU/USD")
            else:
                result = func()
        elif dept_info.get("accepts_targets", False):
            result = func(session_id, symbols=all_targets)
        else:
            result = func(session_id)

        if isinstance(result, dict):
            lines = []
            for k, v in result.items():
                if isinstance(v, dict):
                    lines.append(f"  {k}: {json.dumps(v, ensure_ascii=False)[:100]}")
                elif isinstance(v, list):
                    lines.append(f"  {k}: [{len(v)} 项]")
                else:
                    lines.append(f"  {k}: {v}")
            return "\n".join(lines)
        return str(result)
    except Exception as e:
        return f"错误: 调用 {department} 失败 — {str(e)}"


def _parse_user_command(command: str) -> dict:
    """解析用户命令，识别意图和参数

    支持离线解析（基于关键词），不依赖 LLM。
    如果命令中包含已知关键词，直接匹配对应模板。

    智能识别场景:
      - "黄金" / "黄金，原油" / "黄金和比特币" → 金融分析 + 多标的
      - "生产一个外汇计算器" → 产品开发推广
      - "检查系统状态" → 全系统体检
    """
    cmd_lower = command.lower()

    # 1. 提取所有已知标的
    symbol_map = {
        "黄金": "XAU/USD", "金": "XAU/USD", "xau": "XAU/USD",
        "白银": "XAG/USD", "银": "XAG/USD", "xag": "XAG/USD",
        "比特币": "BTC/USDT", "大饼": "BTC/USDT", "btc": "BTC/USDT",
        "以太坊": "ETH/USDT", "eth": "ETH/USDT",
        "sol": "SOL/USDT", "solana": "SOL/USDT",
        "狗狗币": "DOGE/USDT", "doge": "DOGE/USDT",
        "英伟达": "NVDA", "nvda": "NVDA", "nvidia": "NVDA",
        "苹果": "AAPL", "aapl": "AAPL",
        "特斯拉": "TSLA", "tsla": "TSLA",
        "微软": "MSFT", "msft": "MSFT",
        "亚马逊": "AMZN", "amzn": "AMZN",
        "谷歌": "GOOGL", "googl": "GOOGL",
        "meta": "META",
        "标普": "SPY", "spy": "SPY",
        "纳斯达克": "QQQ", "qqq": "QQQ",
        "道琼斯": "DJI", "dji": "DJI",
        "原油": "USO", "石油": "USO", "uso": "USO",
    }
    targets = []
    for keyword, symbol in symbol_map.items():
        if keyword in cmd_lower and symbol not in targets:
            targets.append(symbol)

    # 2. 识别意图 — 按优先级匹配
    # 如果命令中只有标的名称（如"黄金"、"黄金，原油"），默认走金融分析
    has_action_keyword = any(w in cmd_lower for w in
        ["分析", "行情", "交易", "金融", "投资", "回测", "怎么看", "怎么样", "建议"])

    if has_action_keyword or (targets and not any(w in cmd_lower for w in
        ["生产", "开发", "产品", "兵工厂", "小程序", "工具", "体检", "检查", "状态",
         "看板", "巡逻", "知识", "学习", "沉淀", "经验", "总攻", "全自动", "流水线"])):
        return {"template": "金融分析", "target": targets[0] if targets else "XAU/USD",
                "all_targets": targets}

    if any(w in cmd_lower for w in ["生产", "开发", "产品", "兵工厂", "小程序", "工具"]):
        return {"template": "产品开发推广", "target": targets[0] if targets else "默认产品"}

    if any(w in cmd_lower for w in ["体检", "检查", "状态", "看板", "巡逻"]):
        return {"template": "全系统体检", "target": ""}

    if any(w in cmd_lower for w in ["知识", "学习", "沉淀", "经验"]):
        return {"template": "知识沉淀", "target": ""}

    if any(w in cmd_lower for w in ["总攻", "全自动", "流水线"]):
        return {"template": "全域总攻", "target": targets[0] if targets else "默认产品"}

    return {"template": None, "target": ""}


def _get_steps_from_template(template_name: str, target: str) -> list:
    """从模板获取步骤列表，替换 {target} 占位符"""
    template = TASK_TEMPLATES.get(template_name)
    if not template:
        return []

    steps = []
    for step in template["steps"]:
        action = step["action"].replace("{target}", target)
        steps.append({
            "department": step["department"],
            "action": action,
            "depends_on": step["depends_on"],
        })
    return steps


def _topological_sort(steps: list) -> list:
    """拓扑排序 — 按依赖关系排列执行顺序"""
    sorted_steps = []
    executed_ids = set()

    remaining = list(steps)
    max_iter = len(steps) * 2
    iterations = 0

    while remaining and iterations < max_iter:
        iterations += 1
        for step in remaining[:]:
            deps = step.get("depends_on", [])
            dep_departments = []
            for dep in deps:
                for s in steps:
                    if s["department"] == dep and id(s) not in executed_ids:
                        dep_departments.append(dep)
            if all(d not in dep_departments for d in deps):
                sorted_steps.append(step)
                executed_ids.add(id(step))
                remaining.remove(step)

    if remaining:
        sorted_steps.extend(remaining)

    return sorted_steps


def execute_command(session_id: str, command: str) -> str:
    """总参谋长入口 — 执行总司令的一条命令

    流程:
      1. 解析命令 → 识别意图
      2. 拆解为步骤列表
      3. 拓扑排序
      4. 逐个执行，传递上下文
      5. 生成汇总报告
    """
    ensure_chief_dir()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chief_id = f"CHIEF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"\n{'='*60}")
    print(f"  👑 AI 总参谋长启动")
    print(f"  指令编号: {chief_id}")
    print(f"  总司令命令: {command}")
    print(f"{'='*60}")

    parsed = _parse_user_command(command)
    template_name = parsed.get("template")
    target = parsed.get("target", "")
    all_targets = parsed.get("all_targets", [target] if target else [])

    if template_name:
        targets_str = ", ".join(all_targets) if all_targets else (target or "无")
        print(f"\n  📋 匹配模板: {template_name} (目标: {targets_str})")

        # 金融分析模板：直接走金融军团（内部已包含 5 Agent 完整流水线）
        if template_name == "金融分析":
            steps = [{"department": "金融军团", "action": f"多标的交易策略分析: {targets_str}", "depends_on": []}]
        else:
            steps = []
            for t in all_targets:
                t_steps = _get_steps_from_template(template_name, t)
                for s in t_steps:
                    s["action"] = f"{s['action']} ({t})"
                steps.extend(t_steps)
            if not steps:
                steps = _get_steps_from_template(template_name, target)
    else:
        print(f"\n  📋 未匹配到模板，使用自定义模式")
        steps = []

    if not steps:
        print(f"\n  ⚠️  无法自动拆解命令，请手动选择部门:")
        depts = list(DEPARTMENT_REGISTRY.keys())
        for i, dept in enumerate(depts, 1):
            print(f"     {i}. {dept} — {DEPARTMENT_REGISTRY[dept]['description']}")
        print(f"     {len(depts)+1}. 全部执行")

        choice = input("\n🎯 请选择: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(depts):
                selected_depts = [depts[idx]]
            else:
                selected_depts = depts
        except ValueError:
            selected_depts = [depts[0]]

        steps = [{"department": d, "action": f"执行 {d} 标准任务", "depends_on": []} for d in selected_depts]

    sorted_steps = _topological_sort(steps)

    print(f"\n  📋 执行计划 ({len(sorted_steps)} 个阶段):")
    for i, step in enumerate(sorted_steps, 1):
        dept = step["department"]
        dept_info = DEPARTMENT_REGISTRY.get(dept, {})
        dept_desc = dept_info.get("description", "")
        print(f"     {i}. [{dept}] {step['action']}")
        if step.get("depends_on"):
            print(f"        依赖: {', '.join(step['depends_on'])}")

    print(f"\n{'='*60}")
    print(f"  🔄 开始执行")
    print(f"{'='*60}")

    results = []
    all_success = True

    for i, step in enumerate(sorted_steps, 1):
        dept = step["department"]
        action = step["action"]

        print(f"\n{'─'*40}")
        print(f"  阶段 {i}/{len(sorted_steps)}: [{dept}]")
        print(f"  行动: {action}")
        print(f"{'─'*40}")

        save_snapshot(session_id, f"chief_{chief_id}_step_{i}", {
            "department": dept,
            "action": action,
            "step_index": i,
            "total_steps": len(sorted_steps),
        })

        result = _call_department(dept, session_id, target, all_targets)

        status_icon = "✅" if not result.startswith("错误:") else "❌"
        print(f"\n  {status_icon} 执行结果:")
        result_preview = result[:200] + "..." if len(result) > 200 else result
        print(f"     {result_preview}")

        if result.startswith("错误:"):
            all_success = False

        results.append({
            "department": dept,
            "action": action,
            "status": "success" if not result.startswith("错误:") else "failed",
            "result_preview": result,
        })

    print(f"\n{'='*60}")
    print(f"  📊 总参谋长执行报告")
    print(f"{'='*60}")
    print(f"  指令编号: {chief_id}")
    print(f"  总司令命令: {command}")
    print(f"  执行时间: {now}")
    print(f"  总阶段数: {len(sorted_steps)}")
    print(f"  总体状态: {'✅ 全部成功' if all_success else '⚠️ 部分失败'}")

    for i, r in enumerate(results, 1):
        icon = "✅" if r["status"] == "success" else "❌"
        print(f"  {icon} 阶段{i}: [{r['department']}] {r['status']}")

    report_lines = [
        f"# 👑 AI 总参谋长执行报告",
        f"",
        f"**指令编号:** {chief_id}",
        f"**总司令命令:** {command}",
        f"**执行时间:** {now}",
        f"**关联会话:** {session_id}",
        f"**总体状态:** {'✅ 全部成功' if all_success else '⚠️ 部分失败'}",
        f"",
        f"---",
        f"## 执行详情",
        f"",
    ]

    for i, r in enumerate(results, 1):
        report_lines.append(f"### 阶段 {i}: [{r['department']}]")
        report_lines.append(f"- **行动:** {r['action']}")
        report_lines.append(f"- **状态:** {r['status']}")
        report_lines.append(f"- **结果:** {r['result_preview']}")
        report_lines.append("")

    report = "\n".join(report_lines)
    report_file = f"{CHIEF_LOG_DIR}/{chief_id}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    write_log(session_id, "CHIEF_OF_STAFF", command, f"总参谋长执行完成: {chief_id}, 状态: {'全部成功' if all_success else '部分失败'}")

    print(f"\n  📁 完整报告: {report_file}")
    print(f"  📁 作战日志: battle_logs/{session_id}.md")

    return report_file
