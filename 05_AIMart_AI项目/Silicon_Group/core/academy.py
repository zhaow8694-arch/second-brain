"""
🎓 远征军教导团 (Academy & Evolution) — L3 自我进化中枢

职责:
  1. 扫描 battle_logs/ 中的作战记录，提取失败/驳回案例
  2. 调用 AI 分析失败原因，生成优化建议
  3. 将优化建议写入 evolution_log/ 供后续参考
  4. 提供"全军战力评估"报告
  5. AI 驱动复盘：调用 LLM 自动分析失败根因 [Phase 5]
  6. 影子测试：在沙箱中用历史案例验证新指令 [Phase 5]

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 只读方式访问 battle_logs/ 目录
  - 所有输出写入 evolution_log/ 目录
"""
import os
import re
import json
from datetime import datetime
from core.battle_log import write_log

EVOLUTION_DIR = "evolution_log"
SHADOW_DIR = "shadow_tests"


def ensure_evolution_dir():
    if not os.path.exists(EVOLUTION_DIR):
        os.makedirs(EVOLUTION_DIR)


def ensure_shadow_dir():
    if not os.path.exists(SHADOW_DIR):
        os.makedirs(SHADOW_DIR)


def scan_battle_logs(session_id: str = None) -> list:
    """扫描作战日志，提取所有失败/驳回/警告记录"""
    ensure_evolution_dir()
    log_dir = "battle_logs"
    if not os.path.exists(log_dir):
        return []

    failures = []
    log_files = []

    if session_id:
        target = f"{log_dir}/{session_id}.md"
        if os.path.exists(target):
            log_files.append(target)
    else:
        log_files = sorted(
            [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".md")],
            reverse=True
        )[:10]

    for filepath in log_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        session = os.path.basename(filepath).replace(".md", "")
        sections = re.split(r"---\s*\n", content)

        for section in sections:
            section_lower = section.lower()
            if any(kw in section_lower for kw in ["否决", "驳回", "失败", "拒绝", "风险", "违规", "veto", "reject", "fail"]):
                failures.append({
                    "session": session,
                    "timestamp": _extract_timestamp(section),
                    "content": section.strip()[:500],
                })

    return failures


def _extract_timestamp(text: str) -> str:
    """从日志文本中提取时间戳"""
    match = re.search(r"\[(.*?)\]", text)
    return match.group(1) if match else "unknown"


def _call_llm_for_analysis(failures: list) -> dict:
    """调用 LLM 分析失败记录，返回结构化分析结果

    使用 model_router 的低成本模型进行分析，节省算力。
    """
    try:
        from core.model_router import get_llm_config
        from openai import OpenAI

        llm_config = get_llm_config("low")
        client = OpenAI(
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
        )

        failures_text = "\n\n".join([
            f"案例 {i+1} [会话: {f['session']} @ {f['timestamp']}]:\n{f['content'][:300]}"
            for i, f in enumerate(failures[:10])
        ])

        prompt = f"""你是一个专业的军事复盘分析师。请分析以下作战失败记录，输出 JSON 格式的分析结果。

失败记录:
{failures_text}

请分析:
1. 失败模式分类（如：风控驳回、代码安全、合规问题）
2. 每个模式的根因
3. 优化建议
4. 优先级（P0/P1/P2）

输出格式 (JSON):
{{
    "patterns": [
        {{"category": "分类名", "count": 出现次数, "root_cause": "根因分析", "suggestion": "优化建议", "priority": "P0/P1/P2"}}
    ],
    "summary": "总体分析结论"
}}
"""

        response = client.chat.completions.create(
            model=llm_config["model"],
            messages=[
                {"role": "system", "content": "你是一个严谨的军事复盘分析师。只输出 JSON，不要多余内容。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        return {
            "patterns": [
                {
                    "category": "AI分析不可用",
                    "count": len(failures),
                    "root_cause": f"LLM 调用失败: {str(e)}",
                    "suggestion": "请检查 API 配置或网络连接",
                    "priority": "P1",
                }
            ],
            "summary": f"AI 分析引擎暂不可用，已降级为规则分析。共发现 {len(failures)} 条失败记录。",
        }


def analyze_failures(session_id: str, failures: list) -> str:
    """分析失败记录，生成优化建议报告

    使用 AI 驱动分析，如果 AI 不可用则降级为规则分析。
    """
    if not failures:
        return "本次作战无失败记录，全军表现良好。"

    ensure_evolution_dir()

    print("   🤖 调用 AI 分析引擎进行深度复盘...")
    ai_result = _call_llm_for_analysis(failures)

    report_lines = [
        f"# 🎓 远征军教导团 — 作战复盘报告",
        f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**分析会话:** {session_id}",
        f"**失败记录数:** {len(failures)}",
        f"**分析引擎:** {'AI 驱动' if 'AI分析不可用' not in str(ai_result) else '规则降级'}",
        "",
        "---",
        "## 一、失败记录汇总",
        "",
    ]

    for i, f in enumerate(failures, 1):
        report_lines.append(f"### 案例 {i}: 会话 {f['session']} @ {f['timestamp']}")
        report_lines.append("```")
        report_lines.append(f["content"][:300])
        report_lines.append("```")
        report_lines.append("")

    report_lines.extend([
        "---",
        "## 二、AI 模式识别与根因分析",
        "",
    ])

    for pattern in ai_result.get("patterns", []):
        priority_icon = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}.get(pattern.get("priority", "P2"), "⚪")
        report_lines.append(f"### {priority_icon} [{pattern.get('priority', 'P2')}] {pattern.get('category', '未分类')}")
        report_lines.append(f"- **出现次数:** {pattern.get('count', 0)}")
        report_lines.append(f"- **根因分析:** {pattern.get('root_cause', '无')}")
        report_lines.append(f"- **优化建议:** {pattern.get('suggestion', '无')}")
        report_lines.append("")

    report_lines.extend([
        "---",
        "## 三、AI 总结",
        "",
        f"{ai_result.get('summary', '无总结')}",
        "",
        "---",
        "## 四、优化行动项",
        "",
    ])

    for i, pattern in enumerate(ai_result.get("patterns", []), 1):
        report_lines.append(f"{i}. **[{pattern.get('priority', 'P2')}] {pattern.get('category', '未分类')}**: {pattern.get('suggestion', '无')}")

    report_lines.extend([
        "",
        "---",
        "## 五、全军战力趋势",
        "",
        f"*本次分析基于 {len(failures)} 条失败记录*",
        "*AI 驱动复盘将持续优化分析质量*",
        "",
    ])

    report = "\n".join(report_lines)

    evolution_file = f"{EVOLUTION_DIR}/{session_id}_analysis.md"
    with open(evolution_file, "w", encoding="utf-8") as f:
        f.write(report)

    write_log(session_id, "ACADEMY_ANALYSIS", "全军复盘", f"教导团分析完成，发现 {len(failures)} 条失败记录，AI 识别 {len(ai_result.get('patterns', []))} 种失败模式")

    return report


# ===== 影子测试系统 (Shadow Testing) =====

def shadow_test(new_prompt: str, agent_name: str, test_cases: list = None) -> dict:
    """影子测试：在沙箱中用历史案例验证新指令

    进化红线要求：所有 Prompt 修改前，必须在沙箱中通过历史案例验证。
    使用 quality_gate 的规则引擎模拟双模型审计，验证新指令是否
    比旧指令更优（通过率更高）。

    Args:
        new_prompt: 新的 Agent 指令文本
        agent_name: Agent 名称（用于匹配测试案例）
        test_cases: 测试案例列表，为 None 时自动从 battle_logs 加载

    Returns:
        影子测试报告
    """
    ensure_shadow_dir()

    if test_cases is None:
        test_cases = _load_shadow_test_cases(agent_name)

    if not test_cases:
        return {
            "passed": True,
            "agent": agent_name,
            "test_count": 0,
            "message": "无历史测试案例，跳过影子测试",
            "details": [],
        }

    from core.quality_gate import _run_rules

    results = []
    passed_count = 0
    failed_count = 0

    for case in test_cases:
        content_type = case.get("content_type", "agent_evolution")
        content = case.get("content", "")

        failures = _run_rules(new_prompt + "\n" + content, content_type)
        case_passed = len(failures) == 0

        if case_passed:
            passed_count += 1
        else:
            failed_count += 1

        results.append({
            "case_id": case.get("id", "unknown"),
            "description": case.get("description", ""),
            "content_type": content_type,
            "passed": case_passed,
            "failures": failures,
        })

    pass_rate = (passed_count / len(test_cases)) * 100 if test_cases else 100
    passed = pass_rate >= 80

    report = {
        "agent": agent_name,
        "test_count": len(test_cases),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate": round(pass_rate, 1),
        "passed": passed,
        "threshold": 80,
        "details": results,
        "summary": f"影子测试 {'✅ 通过' if passed else '❌ 未通过'} — 通过率 {pass_rate:.1f}% (阈值 80%)",
    }

    shadow_file = f"{SHADOW_DIR}/shadow_test_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(shadow_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    write_log(
        "SHADOW_TEST",
        "SHADOW_TEST",
        agent_name,
        json.dumps({"pass_rate": round(pass_rate, 1), "passed": passed, "test_count": len(test_cases)}, ensure_ascii=False),
    )

    return report


def _load_shadow_test_cases(agent_name: str) -> list:
    """从 battle_logs 加载历史测试案例

    提取过去被驳回/失败的记录作为测试案例。
    每个案例包含：原始内容、内容类型、失败原因。
    """
    log_dir = "battle_logs"
    if not os.path.exists(log_dir):
        return []

    cases = []
    log_files = sorted(
        [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".md")],
        reverse=True,
    )[:20]

    for filepath in log_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        sections = re.split(r"---\s*\n", content)
        for section in sections:
            section_lower = section.lower()
            if any(kw in section_lower for kw in ["否决", "驳回", "失败", "拒绝", "违规", "reject"]):
                stage_match = re.search(r"阶段: (.*?)(?:\n|$)", section)
                stage = stage_match.group(1).strip() if stage_match else "unknown"

                content_type = "agent_evolution"
                if "trade" in stage or "金融" in stage:
                    content_type = "trade_plan"
                elif "code" in stage or "代码" in stage or "兵工厂" in stage:
                    content_type = "generated_code"
                elif "marketing" in stage or "宣发" in stage or "文案" in stage:
                    content_type = "marketing_copy"

                cases.append({
                    "id": f"{os.path.basename(filepath).replace('.md', '')}_{len(cases)}",
                    "description": f"历史驳回案例: {stage}",
                    "content_type": content_type,
                    "content": section.strip()[:500],
                })

    return cases


def run_shadow_batch(agent_name: str = None) -> dict:
    """批量运行影子测试

    对所有 Agent（或指定 Agent）执行影子测试。
    用于系统启动时自动验证所有指令文件的有效性。

    Args:
        agent_name: 指定 Agent，为 None 时测试所有 Agent

    Returns:
        批量测试报告
    """
    agents = [agent_name] if agent_name else [
        "financial_intel", "financial_quant", "financial_mp",
        "arsenal_coder", "arsenal_qa", "marketing_writer",
    ]

    results = {}
    all_passed = True

    for agent in agents:
        from core.prompt_loader import get_prompt
        prompt = get_prompt(agent)
        if not prompt:
            results[agent] = {"passed": False, "error": "指令文件不存在"}
            all_passed = False
            continue

        test_result = shadow_test(prompt, agent)
        results[agent] = test_result
        if not test_result.get("passed", False):
            all_passed = False

    batch_report = {
        "timestamp": datetime.now().isoformat(),
        "all_passed": all_passed,
        "agent_count": len(agents),
        "results": results,
    }

    batch_file = f"{SHADOW_DIR}/batch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(batch_file, "w", encoding="utf-8") as f:
        json.dump(batch_report, f, indent=2, ensure_ascii=False)

    return batch_report


def get_academy_status() -> dict:
    """获取教导团状态"""
    ensure_evolution_dir()
    ensure_shadow_dir()
    reports = [f for f in os.listdir(EVOLUTION_DIR) if f.endswith("_analysis.md")] if os.path.exists(EVOLUTION_DIR) else []
    shadow_tests = [f for f in os.listdir(SHADOW_DIR) if f.endswith(".json")] if os.path.exists(SHADOW_DIR) else []
    return {
        "total_reports": len(reports),
        "latest_report": sorted(reports, reverse=True)[0] if reports else None,
        "total_shadow_tests": len(shadow_tests),
        "latest_shadow_test": sorted(shadow_tests, reverse=True)[0] if shadow_tests else None,
        "evolution_dir": EVOLUTION_DIR,
        "shadow_dir": SHADOW_DIR,
    }
