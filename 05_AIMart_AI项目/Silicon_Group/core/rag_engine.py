"""
📚 中央知识库 (RAG Engine) — L3 基建与进化中枢

职责:
  1. 跨部门经验向量化存储
  2. 相似案例检索（失败/成功经验复用）
  3. 知识条目自动摘要
  4. 实现"一处学到，全军进化"

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 使用轻量级 JSON 存储（未来可升级为向量数据库）
  - 所有知识数据存储在 config/knowledge_base/ 目录
"""
import os
import json
import hashlib
import re
from datetime import datetime
from core.battle_log import write_log

KNOWLEDGE_DIR = "config/knowledge_base"


def ensure_knowledge_dir():
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)


def _get_knowledge_file() -> str:
    ensure_knowledge_dir()
    return f"{KNOWLEDGE_DIR}/knowledge_base.json"


def load_knowledge_base() -> list:
    """加载知识库"""
    filepath = _get_knowledge_file()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_knowledge_base(kb: list):
    """保存知识库"""
    filepath = _get_knowledge_file()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)


def _generate_knowledge_id(content: str) -> str:
    """根据内容生成唯一知识 ID"""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def _extract_keywords(text: str) -> list:
    """从文本中提取关键词"""
    stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它", "们"}
    words = re.findall(r'[\w]+', text.lower())
    return list(set(w for w in words if len(w) > 2 and w not in stop_words))[:10]


def add_knowledge(source: str, content: str, category: str, session_id: str = "", tags: list = None) -> dict:
    """添加一条知识到知识库

    Args:
        source: 知识来源（如：金融重击、兵工厂、宣发军）
        content: 知识内容
        category: 知识分类（如：失败经验、成功经验、策略、规则）
        session_id: 关联会话
        tags: 自定义标签

    Returns:
        创建的知识条目
    """
    kb = load_knowledge_base()

    entry = {
        "id": _generate_knowledge_id(content),
        "source": source,
        "category": category,
        "content": content[:1000],
        "tags": tags or _extract_keywords(content),
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "usage_count": 0,
    }

    kb.append(entry)
    save_knowledge_base(kb)

    if session_id:
        write_log(session_id, "KNOWLEDGE_ADDED", source, f"新增知识 [{category}]: {content[:60]}...")

    return entry


def search_knowledge(query: str, category: str = "", top_k: int = 5) -> list:
    """搜索知识库 — 基于关键词匹配

    未来可升级为向量相似度搜索。

    Args:
        query: 搜索关键词
        category: 按分类筛选（可选）
        top_k: 返回结果数量

    Returns:
        匹配的知识条目列表
    """
    kb = load_knowledge_base()
    query_lower = query.lower()
    query_keywords = set(re.findall(r'[\w]+', query_lower))

    scored = []
    for entry in kb:
        if category and entry.get("category") != category:
            continue

        content_lower = entry.get("content", "").lower()
        tags = [t.lower() for t in entry.get("tags", [])]

        keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
        tag_matches = sum(1 for kw in query_keywords if kw in tags)
        exact_match = 10 if query_lower in content_lower else 0

        score = keyword_matches + tag_matches * 2 + exact_match
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [entry for _, entry in scored[:top_k]]

    for entry in results:
        entry["usage_count"] = entry.get("usage_count", 0) + 1
    save_knowledge_base(kb)

    return results


def get_knowledge_by_source(source: str) -> list:
    """按来源获取知识"""
    kb = load_knowledge_base()
    return [e for e in kb if e.get("source") == source]


def get_knowledge_by_category(category: str) -> list:
    """按分类获取知识"""
    kb = load_knowledge_base()
    return [e for e in kb if e.get("category") == category]


def get_knowledge_stats() -> dict:
    """获取知识库统计"""
    kb = load_knowledge_base()
    categories = {}
    sources = {}

    for entry in kb:
        cat = entry.get("category", "未分类")
        src = entry.get("source", "未知")
        categories[cat] = categories.get(cat, 0) + 1
        sources[src] = sources.get(src, 0) + 1

    return {
        "total_entries": len(kb),
        "categories": categories,
        "sources": sources,
        "top_tags": _get_top_tags(kb, 10),
    }


def _get_top_tags(kb: list, n: int = 10) -> list:
    """获取最常用的标签"""
    tag_count = {}
    for entry in kb:
        for tag in entry.get("tags", []):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
    return [{"tag": tag, "count": count} for tag, count in sorted_tags[:n]]


def learn_from_failure(session_id: str, source: str, failure_content: str, root_cause: str, solution: str):
    """从失败中学习 — 自动将失败经验存入知识库

    这是教导团与知识库的联动接口。
    """
    knowledge_entry = f"""【失败经验】来源: {source}
根因: {root_cause}
解决方案: {solution}
原始记录: {failure_content[:200]}"""

    add_knowledge(
        source=source,
        content=knowledge_entry,
        category="失败经验",
        session_id=session_id,
        tags=[source, "失败经验", "复盘"] + _extract_keywords(root_cause),
    )


def learn_from_success(session_id: str, source: str, success_content: str, key_factors: str):
    """从成功中学习 — 将成功经验存入知识库"""
    knowledge_entry = f"""【成功经验】来源: {source}
关键因素: {key_factors}
原始记录: {success_content[:200]}"""

    add_knowledge(
        source=source,
        content=knowledge_entry,
        category="成功经验",
        session_id=session_id,
        tags=[source, "成功经验", "最佳实践"] + _extract_keywords(key_factors),
    )


def get_rag_status() -> dict:
    """获取中央知识库状态"""
    stats = get_knowledge_stats()
    return {
        "total_entries": stats["total_entries"],
        "categories": stats["categories"],
        "sources": stats["sources"],
        "top_tags": stats["top_tags"],
    }
