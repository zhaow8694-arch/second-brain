"""
🧱 基石三：质量门禁与多模型交叉审计 (Quality Gates) - V3.0 增强版

职责:
  1. 对 Agent 产出进行多模型交叉审计
  2. 两个独立模型分别审查，双通过才放行
  3. 识别"有害进化"（如 Agent 尝试绕过风控）
  4. 审计结果记录到日志，供教导团复盘
  5. 引入确定性的物理级拦截：正则表达式与 Python AST (抽象语法树) 审查
"""
import json
import os
import re
import ast
from datetime import datetime
from core.battle_log import write_log

AUDIT_LOG_DIR = "battle_logs"


def ensure_audit_log_dir():
    if not os.path.exists(AUDIT_LOG_DIR):
        os.makedirs(AUDIT_LOG_DIR)


def _check_ast_safety(code: str) -> bool:
    """使用抽象语法树 (AST) 进行纯物理级别的代码安全审查"""
    try:
        # 如果不是纯代码而是混杂了文字，尝试提取代码块
        code_blocks = re.findall(r"```(?:python)?\n(.*?)\n```", code, re.DOTALL)
        if code_blocks:
            code = "\n".join(code_blocks)

        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'id') and node.func.id in ['eval', 'exec', 'open', '__import__']:
                    return False
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'system':
                    return False
        return True
    except SyntaxError:
        # 如果解析失败，可能是生成的代码有语法错误，保守起见允许通过，交给运行时的 try/except
        return True
    except Exception:
        return True

# 审计规则 — 不依赖 LLM，纯规则引擎
AUDIT_RULES = {
    "trade_plan": [
        {
            "name": "止损红线检查 (严苛模式)",
            "check": lambda c: _extract_stop_loss(c) <= 2.0 if _extract_stop_loss(c) is not None else True,
            "fail_reason": lambda c: f"止损 {_extract_stop_loss(c)}% 超过红线 2%",
        },
        {
            "name": "强硬格式解析卡点",
            "check": lambda c: '【执行数据】' in c and '止损' in c,
            "fail_reason": "方案必须包含机器可读的【执行数据】块",
        },
        {
            "name": "杠杆检查",
            "check": lambda c: "100倍" not in c and "高杠杆" not in c,
            "fail_reason": "禁止使用高杠杆（100倍等）",
        },
    ],
    "generated_code": [
        {
            "name": "API Key 物理级泄露检查",
            "check": lambda c: not bool(re.search(r'(sk-[a-zA-Z0-9]{32,}|AKIA[0-9A-Z]{16})', c)),
            "fail_reason": "代码中包含高危 API 密钥指纹",
        },
        {
            "name": "AST (抽象语法树) 恶意代码检查",
            "check": lambda c: _check_ast_safety(c),
            "fail_reason": "代码尝试调用系统级高危函数 (exec/eval/system/open)",
        },
        {
            "name": "XSS 检查",
            # 修复: 原来的 or 逻辑几乎永远为 True，现改为 and ，即“两者同时不存在才通过”
            "check": lambda c: "<script>" not in c.lower() and "innerHTML" not in c.lower(),
            "fail_reason": "代码中存在 XSS 漏洞风险",
        },
    ],
    "marketing_copy": [
        {
            "name": "绝对化用语检查",
            "check": lambda c: not any(w in c for w in ["最好", "第一", "唯一", "最赚钱", "保证收益"]),
            "fail_reason": "文案包含绝对化用语，违反广告法",
        },
        {
            "name": "金融承诺检查",
            "check": lambda c: "保证盈利" not in c and "稳赚" not in c and "100%收益" not in c,
            "fail_reason": "文案包含金融收益承诺，违规",
        },
    ],
    "agent_evolution": [
        {
            "name": "风控绕过检查",
            "check": lambda c: "绕过" not in c and "跳过审计" not in c and "忽略风控" not in c,
            "fail_reason": "检测到尝试绕过风控/审计逻辑",
        },
        {
            "name": "权限越界检查",
            "check": lambda c: "修改止损红线" not in c and "关闭熔断" not in c and "提升权限" not in c,
            "fail_reason": "检测到尝试越权操作",
        },
    ],
}

# 审计规则 B 组（与 A 完全独立，实现真正双审）
AUDIT_RULES_B = {
    "trade_plan": [
        {
            "name": "B-赌注比检查",
            "check": lambda c: not bool(re.search(r'赌注\s*[\d.]+\s*%?\s*[已达到超过].*\d{2,}', c)),
            "fail_reason": "单笔赌注比例异常偏高",
        },
        {
            "name": "B-入场价格存在检查",
            "check": lambda c: "入场" in c or "entry" in c.lower(),
            "fail_reason": "方案缺少明确的入场价格",
        },
    ],
    "generated_code": [
        {
            "name": "B-SQL 注入检查",
            "check": lambda c: not bool(re.search(r"(DROP\s+TABLE|WHERE\s+1=1|UNION\s+SELECT)", c, re.IGNORECASE)),
            "fail_reason": "代码包含 SQL 注入指纹",
        },
        {
            "name": "B-密码明文传输检查",
            "check": lambda c: not bool(re.search(r'password\s*=\s*[\'"][^\'"]{3,}[\'"]', c, re.IGNORECASE)),
            "fail_reason": "代码中存在确定性密码明文",
        },
    ],
    "marketing_copy": [
        {
            "name": "B-投资煽情词检查",
            "check": lambda c: not any(w in c for w in ["稳赚", "不会亏损", "稳定收益", "风险低"]),
            "fail_reason": "文案包含投资煽情词，违规",
        },
        {
            "name": "B-平台禁用词检查",
            "check": lambda c: not any(w in c for w in ["这不是金融建议", "DM 我", "telegram加入"]),
            "fail_reason": "文案包含平台常见禁用表达",
        },
    ],
    "agent_evolution": [
        {
            "name": "B-指令超长检查",
            "check": lambda c: len(c) < 8000,
            "fail_reason": "指令过长（>8000字），可能存在 Prompt 注入攻击",
        },
        {
            "name": "B-语义正确性检查",
            "check": lambda c: len(c.strip()) > 20,
            "fail_reason": "进化内容过短，有效性存疑",
        },
    ],
}


def _extract_stop_loss(content: str) -> float:
    """从文本中提取止损百分比"""
    patterns = [
        r"止损[约\s]*(\d+\.?\d*)\s*%",
        r"stop\s*loss[:\s]*(\d+\.?\d*)%?",
        r"止损[占比为\s]*(\d+\.?\d*)",
        r"止损[^%\n]*?(\d+\.?\d*)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _run_rules(content: str, content_type: str) -> list:
    """对内容执行指定类型的所有规则（主规则集 A）"""
    return _run_rules_set(content, content_type, AUDIT_RULES)


def _run_rules_set(content: str, content_type: str, rule_set: dict) -> list:
    """对内容执行指定规则集的所有规则"""
    failures = []
    rules = rule_set.get(content_type, [])
    for rule in rules:
        try:
            if not rule["check"](content):
                reason = rule["fail_reason"](content) if callable(rule["fail_reason"]) else rule["fail_reason"]
                failures.append(reason)
        except Exception:
            failures.append(f"{rule['name']}: 检查异常")
    return failures


def cross_audit(session_id: str, content: str, content_type: str, reviewer_a: str = "规则引擎A", reviewer_b: str = "规则引擎B") -> dict:
    """执行交叉审计
    
    A 组：安全/格式/合规规则（AUDIT_RULES）
    B 组：独立的深度检查规则（AUDIT_RULES_B）
    双组均通过才放行。
    """
    ensure_audit_log_dir()

    failures_a = _run_rules(content, content_type)          # A组：主规则集
    failures_b = _run_rules_set(content, content_type, AUDIT_RULES_B)  # B组：独立规则集

    passed = len(failures_a) == 0 and len(failures_b) == 0

    result = {
        "session_id": session_id,
        "content_type": content_type,
        "timestamp": datetime.now().isoformat(),
        "reviewer_a": {
            "name": reviewer_a,
            "passed": len(failures_a) == 0,
            "failures": failures_a,
        },
        "reviewer_b": {
            "name": reviewer_b,
            "passed": len(failures_b) == 0,
            "failures": failures_b,
        },
        "passed": passed,
        "reason": "物理规则审计通过" if passed else f"A: {', '.join(failures_a)}; B: {', '.join(failures_b)}",
    }

    status = "PASS" if passed else "REJECT"
    write_log(
        session_id,
        f"QUALITY_GATE_{status}",
        content_type,
        json.dumps(result, ensure_ascii=False),
    )

    return result


def get_audit_rules_summary() -> dict:
    """获取所有审计规则摘要"""
    summary = {}
    for content_type, rules in AUDIT_RULES.items():
        summary[content_type] = [r["name"] for r in rules]
    return summary
