from crewai import Agent, Task, Crew, Process
from core.model_router import get_llm_config
from core.battle_log import write_log

PLATFORMS = {
    "twitter": "短帖文，280字符以内，带话题标签",
    "reddit": "论坛帖子，标题+正文，带讨论引导",
    "telegram": "频道公告，简洁有力，带行动号召",
}

CONTENT_TYPES = {
    "promo": "产品推广文案，突出卖点和行动号召",
    "educational": "教育型内容，提供价值的同时软性植入产品",
    "social_proof": "用户见证/案例分享，建立信任感",
    "comparison": "对比类内容，展示产品优势",
}


def create_post(session_id: str, product_name: str, product_desc: str, platform: str, language: str, content_type: str = "promo"):
    writer_llm = get_llm_config("low")

    writer = Agent(
        role="流量宣传军·爆款文案机",
        goal=f"为 {product_name} 撰写 {platform} 平台的{content_type}类推广文案",
        backstory="你是硅基远征军流量宣传军的王牌文案。你写的帖子转化率极高。",
        verbose=True,
        llm_config=writer_llm,
    )

    platform_spec = PLATFORMS.get(platform, "通用社交媒体")
    content_spec = CONTENT_TYPES.get(content_type, "通用推广内容")

    task = Task(
        description=f"""为以下产品撰写推广文案:
产品名称: {product_name}
产品描述: {product_desc}
平台: {platform} ({platform_spec})
内容类型: {content_type} ({content_spec})
语言: {language}

要求:
1. 吸引眼球的开头
2. 突出产品价值
3. 包含行动号召
4. 自然植入话题标签
5. 符合平台调性和内容类型""",
        expected_output=f"一篇 {language} 语言的 {platform} {content_type}文案",
        agent=writer,
    )

    crew = Crew(
        agents=[writer],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    if hasattr(result, 'raw'):
        result_text = result.raw
    elif hasattr(result, 'final_output'):
        result_text = result.final_output
    else:
        result_text = str(result)
    write_log(session_id, "CONTENT_GEN", f"{product_name}_{platform}_{language}_{content_type}", result_text)
    return result_text
