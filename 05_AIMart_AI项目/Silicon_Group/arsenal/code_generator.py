import os
import re
from datetime import datetime
from core.battle_log import write_log
from core.cost_watchdog import record_call
from core.model_router import get_llm_config
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from core.quality_gate import cross_audit

ARSENAL_OUTPUT_DIR = "arsenal_output"

def ensure_output_dir():
    if not os.path.exists(ARSENAL_OUTPUT_DIR):
        os.makedirs(ARSENAL_OUTPUT_DIR)

def generate_product(session_id: str, product_name: str, blueprint: dict):
    """
    基于脚手架模板生成产品。
    不再让 AI 盲目生成完整的 HTML，而是要求其输出特定格式的插槽内容，
    然后注入到 modern_app.html 模板中，确保界面现代化且稳定。
    """
    ensure_output_dir()
    
    print(f"\n   [兵工厂] 开始为 {product_name} 编写代码...")
    
    # 1. 初始化 AI
    # 1. 初始化 AI（通过 model_router 统一调度，不绕过降级链）
    _cfg = get_llm_config("medium")
    coder_agent = Agent(
        role="高级前端开发工程师",
        goal=f"基于 Tailwind CSS 编写 {product_name} 的核心功能逻辑和界面",
        backstory="你是一位拥有 10 年经验的资深前端工程师。你擅长写出极具现代感、无 BUG 的 Vanilla JS 代码。你会确保所有用户交互都顺滑且美观。",
        verbose=True,
        llm=ChatOpenAI(
            model=_cfg["model"],
            api_key=_cfg["api_key"],
            base_url=_cfg["base_url"],
            temperature=0.2,
        ),
    )
    
    coder_task = Task(
        description=f"""你需要为产品 '{product_name}' 编写代码。
产品描述: {blueprint['description']}
变现模式: {blueprint['monetization']}

请严格按照以下要求输出，使用特定的 XML 标签包裹对应内容：

<TITLE>网页的标题内容</TITLE>

<HEADER_TITLE>主界面的醒目标题（建议短小精悍）</HEADER_TITLE>

<HEADER_DESC>标题下方的一两句介绍说明</HEADER_DESC>

<MAIN_CONTENT>
这里写主体界面的 HTML 结构，必须使用 Tailwind CSS 类名。
例如输入框、按钮、结果展示区等。
请勿包含 <html>, <body>, <main> 等外层标签，直接写内部元素。
</MAIN_CONTENT>

<EXTRA_CSS>
如果有额外的自定义 CSS 动画或微调，写在这里。不要写 <style> 标签本身。
</EXTRA_CSS>

<JAVASCRIPT>
<script>
// 这里编写核心业务逻辑，比如按钮点击事件、算法逻辑、与 DOM 的交互等。
// 请确保逻辑完整可用。如果有广告逻辑，加入模拟函数。
</script>
</JAVASCRIPT>
""",
        expected_output="包含 <TITLE>, <HEADER_TITLE>, <HEADER_DESC>, <MAIN_CONTENT>, <EXTRA_CSS>, <JAVASCRIPT> 标签的代码块。",
        agent=coder_agent,
    )
    
    crew = Crew(
        agents=[coder_agent],
        tasks=[coder_task],
        process=Process.sequential,
        verbose=True
    )
    
    try:
        raw_output = crew.kickoff()
        output_str = getattr(raw_output, 'raw', str(raw_output))
    except Exception as e:
        output_str = f"生成失败: {e}"
        print(f"   ❌ AI 生成失败: {e}")
        return
        
    record_call("兵工厂-代码生成", 0, 0.02)
    
    # 2. 交叉审计
    audit = cross_audit(session_id, output_str, "generated_code")
    if not audit["passed"]:
        print(f"   ❌ 质量门禁驳回: {audit['reason']}")
        write_log(session_id, "ARSENAL", product_name, f"生产失败 (被拦截): {audit['reason']}")
        return
        
    # 3. 解析 XML 插槽
    slots = {
        "TITLE": _extract_tag(output_str, "TITLE", product_name),
        "HEADER_TITLE": _extract_tag(output_str, "HEADER_TITLE", product_name),
        "HEADER_DESC": _extract_tag(output_str, "HEADER_DESC", blueprint['description']),
        "MAIN_CONTENT": _extract_tag(output_str, "MAIN_CONTENT", "<p>Content goes here</p>"),
        "EXTRA_CSS": _extract_tag(output_str, "EXTRA_CSS", ""),
        "JAVASCRIPT": _extract_tag(output_str, "JAVASCRIPT", ""),
    }
    
    # 4. 注入脚手架
    boilerplate_path = os.path.join(os.path.dirname(__file__), "boilerplates", "modern_app.html")
    try:
        with open(boilerplate_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"   ❌ 找不到脚手架文件: {boilerplate_path}")
        return
        
    for slot_name, slot_content in slots.items():
        template = template.replace(f"<!-- SLOT: {slot_name} -->", slot_content)
        
    # 5. 保存产品
    filename = f"{ARSENAL_OUTPUT_DIR}/{product_name.replace(' ', '_').lower()}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(template)
        
    print(f"   ✅ 产品 {product_name} 组装完成: {filename}")
    write_log(session_id, "ARSENAL", product_name, f"生产成功: {filename}")

def _extract_tag(text: str, tag: str, default: str) -> str:
    """提取特定的 XML 标签内容"""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return default
