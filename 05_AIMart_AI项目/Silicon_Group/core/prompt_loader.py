"""
🧱 基石二：动态指令加载器 (Dynamic Prompt Loader)

职责:
  1. 从 config/prompts/ 目录读取 Agent 指令文件
  2. 每次调用时重新读取（热加载），不缓存
  3. 提供统一的接口：get_prompt(agent_name) → dict
  4. 如果文件不存在，返回默认指令（兼容旧代码）

用法:
  from core.prompt_loader import get_prompt

  # 在创建 Agent 时：
  prompt = get_prompt("financial_intel")
  agent = Agent(
      role=prompt["role"],
      goal=prompt["goal"],
      backstory=prompt["backstory"],
      ...
  )

文件格式 (config/prompts/financial_intel.md):
  ---
  role: 全域情报特工
  goal: 抓取 {target} 的实时价格、支撑压力位及影响走势的重磅新闻。
  backstory: 你是远征军的眼睛，拥有最高信息采集权。
  ---
"""
import os
import re

PROMPTS_DIR = "config/prompts"


def ensure_prompts_dir():
    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR)


def get_prompt(agent_name: str) -> dict:
    """获取 Agent 指令

    从 config/prompts/{agent_name}.md 读取。
    如果文件不存在，返回空 dict（调用方使用默认值）。
    """
    filepath = os.path.join(PROMPTS_DIR, f"{agent_name}.md")
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    return _parse_prompt_file(content)


def _parse_prompt_file(content: str) -> dict:
    """解析 Markdown 格式的指令文件

    支持两种格式:
    1. YAML 风格 front matter (--- 之间)
    2. 直接写 key: value 对
    """
    result = {}

    yaml_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)
        for line in yaml_content.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result

    for line in content.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()

    return result


def list_available_agents() -> list:
    """列出所有可用的 Agent 指令文件"""
    ensure_prompts_dir()
    if not os.path.exists(PROMPTS_DIR):
        return []
    files = [f.replace(".md", "") for f in os.listdir(PROMPTS_DIR) if f.endswith(".md")]
    return sorted(files)


def get_prompt_status() -> dict:
    """获取指令加载器状态"""
    agents = list_available_agents()
    return {
        "total_agents": len(agents),
        "agents": agents,
        "prompts_dir": PROMPTS_DIR,
    }
