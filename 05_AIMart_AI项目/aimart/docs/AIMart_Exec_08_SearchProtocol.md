# AIMart 工程执行文件 08：搜索发现协议
tags: [aimart, search, protocol]

tags: [aimart, search, protocol]
> Codex 执行指令：实现 AI Agent 需求描述协议、能力匹配引擎、搜索结果排序与返回、ES 索引管理
tags: [aimart, search, protocol]

tags: [aimart, search, protocol]
---
tags: [aimart, search, protocol]

## 一、核心概念

### 1.1 为什么搜索协议是 AIMart 的核心壁垒

传统电商搜索是"人输入关键词 → 系统返回列表 → 人阅读决策"。AIMart 的搜索是"Agent 描述能力缺口 → 系统返回精确匹配 → Agent 评分决策"。区别在于：

| 维度 | 人类搜索 | Agent 搜索 |
|------|---------|-----------|
| 输入 | 关键词 + 筛选器 | 结构化能力需求描述 |
| 匹配 | 文本相似度 + 业务排序 | 语义匹配 + 约束求解 |
| 输出 | 商品列表 + 图片 + 价格 | 结构化能力声明 + 可比指标 |
| 决策 | 人综合判断 | Agent 评分函数 |

搜索协议定义了"AI 如何描述需求"和"市场如何返回结果"——谁定义了这个标准，谁就是平台。

### 1.2 搜索流程总览

```
Agent                          AIMart                         Elasticsearch
  │                               │                               │
  │── 1. CapabilityNeed ────────▶│                               │
  │                               │── 2. 解析 + 约束提取 ────────▶│
  │                               │◀── 3. 候选集返回 ────────────│
  │                               │── 4. 约束求解 + 评分 ────────▶│
  │                               │    (内存计算)                  │
  │◀── 5. CapabilityMatchList ───│                               │
  │                               │                               │
  │── 6. TrialRequest ──────────▶│                               │
  │                               │── 7. 沙箱调用 ───────────────▶│
  │◀── 8. TrialResult ───────────│                               │
  │                               │                               │
  │── 9. PurchaseDecision ──────▶│                               │
  │                               │── 10. 交易流程 ──────────────▶│
```

---

## 二、数据模型

```python
# src/aimart/search/models.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, JSON, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SearchQuery(Base):
    """搜索查询记录——用于搜索分析和推荐优化"""
    __tablename__ = "search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(String(64), nullable=True, comment="Agent 会话 ID")

    # 查询内容
    need_type = Column(String(20), nullable=False, comment="model | skill | expert | compute")
    domains = Column(JSONB, nullable=False, default=list, comment='["legal", "contract_review"]')
    task_description = Column(Text, nullable=True, comment="自然语言任务描述（可选）")
    constraints = Column(JSONB, nullable=False, default=dict, comment="结构化约束")
    scoring_weights = Column(JSONB, nullable=False, default=dict, comment="评分权重")

    # 结果
    result_count = Column(Integer, nullable=True)
    selected_item_id = Column(UUID(as_uuid=True), nullable=True, comment="Agent 最终选择的商品")
    trial_initiated = Column(Integer, nullable=False, default=0, comment="发起试用的数量")
    purchased = Column(Integer, nullable=False, default=0, comment="最终购买数量")

    # 性能
    query_latency_ms = Column(Integer, nullable=True, comment="查询耗时")
    match_latency_ms = Column(Integer, nullable=True, comment="匹配耗时")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_search_agent", "agent_id"),
        Index("ix_search_need_type", "need_type"),
        Index("ix_search_created", "created_at"),
    )


class CapabilityIndex(Base):
    """能力索引——ES 的镜像表，用于快速检索和关联查询"""
    __tablename__ = "capability_indices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    agentcard_version = Column(String(20), nullable=False)

    # 索引字段
    item_type = Column(String(20), nullable=False, comment="model | skill | expert | compute")
    domains = Column(JSONB, nullable=False, default=list)
    task_types = Column(JSONB, nullable=False, default=list)
    supported_languages = Column(JSONB, nullable=False, default=list)
    tags = Column(JSONB, nullable=False, default=list)

    # 性能指标（用于约束匹配）
    latency_p50_ms = Column(Integer, nullable=True)
    latency_p99_ms = Column(Integer, nullable=True)
    throughput_rps = Column(Integer, nullable=True)
    availability_sla = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=False, default=50.0)

    # 定价（用于预算匹配）
    pricing_model = Column(String(20), nullable=True, comment="per_call | per_token | per_hour | subscription | free")
    price_min = Column(Float, nullable=True, comment="最低价格")
    price_max = Column(Float, nullable=True, comment="最高价格")
    currency = Column(String(10), nullable=True)

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="active | delisted | suspended")
    es_index_version = Column(Integer, nullable=False, default=1, comment="ES 索引版本，用于判断是否需要重新索引")

    # 元信息
    provider_id = Column(UUID(as_uuid=True), nullable=False)
    provider_name = Column(String(255), nullable=True)
    certification_status = Column(String(20), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_cap_item_type", "item_type"),
        Index("ix_cap_domains", "domains", postgresql_using="gin"),
        Index("ix_cap_trust", "trust_score"),
        Index("ix_cap_status", "status"),
    )
```

---

## 三、搜索请求 Schema

```python
# src/aimart/search/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---- 能力需求描述 ----

class PerformanceConstraint(BaseModel):
    """性能约束"""
    latency_p50_ms_max: Optional[int] = Field(None, gt=0, description="P50延迟上限(ms)")
    latency_p99_ms_max: Optional[int] = Field(None, gt=0, description="P99延迟上限(ms)")
    throughput_rps_min: Optional[int] = Field(None, gt=0, description="吞吐量下限(rps)")
    availability_sla_min: Optional[float] = Field(None, gt=0, le=1, description="可用性下限(0-1)")


class BudgetConstraint(BaseModel):
    """预算约束"""
    max_price_per_call: Optional[float] = Field(None, gt=0, description="单次调用最大价格")
    max_price_per_token: Optional[float] = Field(None, gt=0, description="每 Token 最大价格")
    max_price_per_hour: Optional[float] = Field(None, gt=0, description="每小时最大价格")
    preferred_pricing_model: Optional[str] = Field(None, pattern="^(per_call|per_token|per_hour|subscription|free)$")
    currency: str = Field(default="CNY", pattern="^(CNY|USD|USDC)$")


class TrustConstraint(BaseModel):
    """信任约束"""
    min_trust_score: Optional[float] = Field(None, ge=0, le=100, description="最低信任评分")
    certification_required: bool = Field(default=False, description="是否要求已认证")
    min_transactions: Optional[int] = Field(None, gt=0, description="卖家最低交易量")


class CapabilityNeed(BaseModel):
    """
    能力需求描述——AI Agent 描述"我需要什么能力"的结构化请求。

    这是 AIMart 搜索协议的核心输入格式。
    Agent 必须使用此格式描述需求，而不是自然语言关键词。
    """
    need_type: str = Field(..., pattern="^(model|skill|expert|compute)$", description="需要的能力类型")
    domains: list[str] = Field(..., min_length=1, description='能力领域 ["legal","contract_review"]')
    task_description: Optional[str] = Field(None, max_length=500, description="任务描述（辅助语义匹配）")

    # 输入/输出规格
    input_format: Optional[dict] = Field(None, description="期望的输入格式 Schema")
    output_format: Optional[dict] = Field(None, description="期望的输出格式 Schema")
    supported_languages: Optional[list[str]] = Field(None, description='["zh-CN","en-US"]')

    # 约束
    performance: Optional[PerformanceConstraint] = None
    budget: Optional[BudgetConstraint] = None
    trust: Optional[TrustConstraint] = None

    # 评分权重——Agent 决定各维度在排序中的权重
    scoring_weights: Optional[dict] = Field(
        default={
            "capability_match": 0.35,    # 能力匹配度
            "performance": 0.20,         # 性能指标
            "price": 0.20,              # 价格竞争力
            "trust": 0.15,              # 信任评分
            "availability": 0.10,       # 可用性
        },
        description="各维度评分权重，总和必须为 1.0",
    )

    @field_validator("scoring_weights")
    @classmethod
    def validate_weights(cls, v):
        if v is not None:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"评分权重总和必须为1.0，当前为 {total}")
        return v


# ---- 搜索结果 ----

class MatchedItemScore(BaseModel):
    """单个匹配项的评分明细"""
    capability_match: float = Field(..., ge=0, le=1, description="能力匹配度")
    performance: float = Field(..., ge=0, le=1, description="性能评分")
    price: float = Field(..., ge=0, le=1, description="价格评分")
    trust: float = Field(..., ge=0, le=1, description="信任评分")
    availability: float = Field(..., ge=0, le=1, description="可用性评分")
    composite: float = Field(..., ge=0, le=1, description="综合评分（加权）")


class MatchedItem(BaseModel):
    """搜索结果中的单个匹配项"""
    item_id: UUID
    item_name: str
    item_type: str
    item_version: str
    provider_id: UUID
    provider_name: str

    # 能力摘要（不返回完整 AgentCard，只返回匹配相关的摘要）
    matched_domains: list[str]
    matched_task_types: list[str]
    performance_summary: dict
    pricing_summary: dict
    trust_score: float
    certification_status: Optional[str] = None

    # 评分
    scores: MatchedItemScore

    # 可操作
    trial_available: bool = Field(..., description="是否可试用")
    api_endpoint: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    query_id: UUID
    need_type: str
    total_matches: int
    returned_count: int = Field(..., le=20, description="最多返回20条")
    items: list[MatchedItem]
    query_latency_ms: int
    match_latency_ms: int


# ---- 试用请求 ----

class TrialRequest(BaseModel):
    """试用请求"""
    item_id: UUID
    need_type: str
    trial_input: dict = Field(..., description="试用输入数据")
    trial_config: Optional[dict] = Field(None, description="试用配置")


class TrialResult(BaseModel):
    """试用结果"""
    trial_id: UUID
    item_id: UUID
    success: bool
    output: Optional[dict] = None
    performance: Optional[dict] = Field(None, description='{"latency_ms": 1200, "tokens_used": 500}')
    errors: Optional[list[str]] = None
    sandbox_constraints: dict = Field(
        default={"input_scale_pct": 10, "max_calls": 5},
        description="沙箱限制信息",
    )
```

---

## 四、ES 索引管理

```python
# src/aimart/search/indexer.py

from __future__ import annotations

from typing import Any

import structlog
from elasticsearch import AsyncElasticsearch

logger = structlog.get_logger()


# ES 索引 Mapping
CAPABILITY_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "domain_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "edge_ngram_filter"],
                },
                "task_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
            },
            "filter": {
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "item_id": {"type": "keyword"},
            "item_type": {"type": "keyword"},
            "item_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "item_version": {"type": "keyword"},

            # 能力描述
            "domains": {"type": "keyword"},
            "task_types": {
                "type": "nested",
                "properties": {
                    "task_type_id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "task_analyzer"},
                    "description_machine": {"type": "text", "analyzer": "task_analyzer"},
                },
            },
            "supported_languages": {"type": "keyword"},
            "tags": {"type": "keyword"},

            # 性能指标
            "latency_p50_ms": {"type": "integer"},
            "latency_p99_ms": {"type": "integer"},
            "throughput_rps": {"type": "integer"},
            "availability_sla": {"type": "double"},

            # 定价
            "pricing_model": {"type": "keyword"},
            "price_min": {"type": "double"},
            "price_max": {"type": "double"},
            "currency": {"type": "keyword"},

            # 信任
            "trust_score": {"type": "double"},
            "certification_status": {"type": "keyword"},

            # 提供方
            "provider_id": {"type": "keyword"},
            "provider_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},

            # 状态
            "status": {"type": "keyword"},

            # 时间
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        },
    },
}


class CapabilityIndexer:
    """能力索引管理器——将 AgentCard 数据同步到 ES"""

    def __init__(self, es_client: AsyncElasticsearch, index_name: str = "aimart_capabilities"):
        self._es = es_client
        self._index = index_name

    async def ensure_index(self) -> None:
        """确保索引存在，不存在则创建"""
        exists = await self._es.indices.exists(index=self._index)
        if not exists:
            await self._es.indices.create(index=self._index, body=CAPABILITY_INDEX_MAPPING)
            logger.info("es_index_created", index=self._index)

    async def index_agentcard(self, agentcard: dict) -> None:
        """将一个 AgentCard 索引到 ES"""
        doc = self._agentcard_to_doc(agentcard)
        item_id = doc["item_id"]

        await self._es.index(
            index=self._index,
            id=item_id,
            body=doc,
            refresh=True,  # 即时可见（开发环境，生产环境改为 false）
        )

        logger.info("agentcard_indexed", item_id=item_id, item_type=doc["item_type"])

    async def bulk_index(self, agentcards: list[dict]) -> int:
        """批量索引 AgentCard"""
        actions = []
        for card in agentcards:
            doc = self._agentcard_to_doc(card)
            actions.append({"index": {"_id": doc["item_id"]}})
            actions.append(doc)

        if not actions:
            return 0

        result = await self._es.bulk(index=self._index, body=actions, refresh=True)
        success_count = len([item for item in result["items"] if item["index"]["status"] in (200, 201)])

        logger.info("bulk_index_complete", total=len(agentcards), success=success_count)
        return success_count

    async def remove_item(self, item_id: str) -> None:
        """从索引中移除商品"""
        await self._es.delete(index=self._index, id=item_id, refresh=True)
        logger.info("item_removed_from_index", item_id=item_id)

    async def update_trust_score(self, item_id: str, trust_score: float) -> None:
        """更新信任评分（高频更新，使用 partial update）"""
        await self._es.update(
            index=self._index,
            id=item_id,
            body={"doc": {"trust_score": trust_score}},
        )

    def _agentcard_to_doc(self, card: dict) -> dict:
        """将 AgentCard 转换为 ES 文档"""
        identity = card.get("identity", {})
        capability = card.get("capability_declaration", {})
        performance = card.get("performance_declaration", {})
        pricing = card.get("pricing", {})
        trust = card.get("trust", {})
        delivery = card.get("delivery", {})

        perf_constraints = performance.get("performance_constraints", {})

        # 价格范围
        pricing_details = pricing.get("details", {})
        prices = []
        if pricing_details.get("per_call"):
            prices.append(float(pricing_details["per_call"].get("price", 0)))
        if pricing_details.get("per_token"):
            prices.append(float(pricing_details["per_token"].get("input_price", 0)))
            prices.append(float(pricing_details["per_token"].get("output_price", 0)))
        if pricing_details.get("per_hour"):
            prices.append(float(pricing_details["per_hour"].get("price", 0)))

        return {
            "item_id": identity.get("item_id", ""),
            "item_type": identity.get("item_type", ""),
            "item_name": identity.get("item_name", ""),
            "item_version": identity.get("item_version", ""),
            "domains": capability.get("domains", []),
            "task_types": [
                {
                    "task_type_id": tt.get("task_type_id", ""),
                    "name": tt.get("name", ""),
                    "description_machine": tt.get("description_machine", ""),
                }
                for tt in capability.get("task_types", [])
            ],
            "supported_languages": capability.get("supported_languages", []),
            "tags": capability.get("domains", []) + [identity.get("item_type", "")],
            "latency_p50_ms": perf_constraints.get("latency_p50_ms"),
            "latency_p99_ms": perf_constraints.get("latency_p99_ms"),
            "throughput_rps": perf_constraints.get("throughput_rps"),
            "availability_sla": perf_constraints.get("availability_sla"),
            "pricing_model": pricing.get("model", ""),
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
            "currency": pricing.get("currency", "CNY"),
            "trust_score": trust.get("trust_score", 50.0),
            "certification_status": trust.get("certification_status", ""),
            "provider_id": identity.get("provider_id", ""),
            "provider_name": identity.get("provider_name", ""),
            "status": "active",
            "created_at": identity.get("item_release_date", ""),
            "updated_at": identity.get("item_release_date", ""),
        }
```

---

## 五、能力匹配引擎

```python
# src/aimart/search/matcher.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog
from elasticsearch import AsyncElasticsearch

from aimart.search.schemas import (
    CapabilityNeed, MatchedItem, MatchedItemScore,
    PerformanceConstraint, BudgetConstraint, TrustConstraint,
)

logger = structlog.get_logger()


@dataclass
class MatcherConfig:
    """匹配引擎配置"""
    max_results: int = 20
    min_composite_score: float = 0.3    # 低于此分数的结果不返回
    domain_match_boost: float = 1.5     # 领域精确匹配的加权
    task_match_boost: float = 2.0       # 任务类型精确匹配的加权
    es_min_score: float = 0.1           # ES 查询最低分数阈值


class CapabilityMatcher:
    """
    能力匹配引擎——两阶段匹配：
    1. ES 粗筛：领域/任务类型/商品类型 → 候选集（~100条）
    2. 内存精排：约束求解 + 多维评分 → 排序结果（≤20条）
    """

    def __init__(self, es_client: AsyncElasticsearch, config: MatcherConfig | None = None):
        self._es = es_client
        self._config = config or MatcherConfig()

    async def match(self, need: CapabilityNeed, agent_id: UUID) -> list[MatchedItem]:
        """
        执行能力匹配。

        Args:
            need: Agent 的能力需求描述
            agent_id: 发起搜索的 Agent ID

        Returns:
            排序后的匹配结果列表（≤20条）
        """
        # Stage 1: ES 粗筛
        candidates = await self._es_candidates(need)
        logger.info("match_stage1_complete", agent_id=str(agent_id), candidates=len(candidates))

        if not candidates:
            return []

        # Stage 2: 内存精排
        scored = self._score_candidates(need, candidates)
        scored.sort(key=lambda x: x.scores.composite, reverse=True)

        # 过滤低分
        result = [item for item in scored if item.scores.composite >= self._config.min_composite_score]
        result = result[:self._config.max_results]

        logger.info(
            "match_stage2_complete",
            agent_id=str(agent_id),
            total_candidates=len(candidates),
            returned=len(result),
        )

        return result

    async def _es_candidates(self, need: CapabilityNeed) -> list[dict]:
        """ES 粗筛：构建查询并获取候选集"""
        query = self._build_es_query(need)

        result = await self._es.search(
            index="aimart_capabilities",
            body=query,
            size=100,  # 粗筛取100条
            min_score=self._config.es_min_score,
        )

        hits = result.get("hits", {}).get("hits", [])
        return [hit["_source"] for hit in hits]

    def _build_es_query(self, need: CapabilityNeed) -> dict:
        """构建 ES 查询"""
        must_clauses = [
            {"term": {"item_type": need.need_type}},
            {"term": {"status": "active"}},
        ]

        # 领域匹配（至少匹配一个领域）
        if need.domains:
            must_clauses.append({"terms": {"domains": need.domains}})

        # 任务类型匹配（嵌套查询）
        if need.task_description:
            must_clauses.append({
                "nested": {
                    "path": "task_types",
                    "query": {
                        "multi_match": {
                            "query": need.task_description,
                            "fields": ["task_types.name^2", "task_types.description_machine"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    },
                    "score_mode": "max",
                }
            })

        # 语言匹配
        if need.supported_languages:
            must_clauses.append({"terms": {"supported_languages": need.supported_languages}})

        should_clauses = []

        # 性能约束（作为 filter，不参与评分）
        filters = []
        if need.performance:
            if need.performance.latency_p50_ms_max:
                filters.append({"range": {"latency_p50_ms": {"lte": need.performance.latency_p50_ms_max}}})
            if need.performance.latency_p99_ms_max:
                filters.append({"range": {"latency_p99_ms": {"lte": need.performance.latency_p99_ms_max}}})
            if need.performance.throughput_rps_min:
                filters.append({"range": {"throughput_rps": {"gte": need.performance.throughput_rps_min}}})
            if need.performance.availability_sla_min:
                filters.append({"range": {"availability_sla": {"gte": need.performance.availability_sla_min}}})

        # 预算约束
        if need.budget:
            if need.budget.max_price_per_call:
                filters.append({"range": {"price_min": {"lte": need.budget.max_price_per_call}}})
            if need.budget.preferred_pricing_model:
                should_clauses.append({"term": {"pricing_model": {"value": need.budget.preferred_pricing_model, "boost": 2.0}}})

        # 信任约束
        if need.trust:
            if need.trust.min_trust_score:
                filters.append({"range": {"trust_score": {"gte": need.trust.min_trust_score}}})
            if need.trust.certification_required:
                filters.append({"term": {"certification_status": "certified"}})

        # 领域精确匹配加权
        for domain in need.domains:
            should_clauses.append({"term": {"domains": {"value": domain, "boost": self._config.domain_match_boost}}})

        query = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "should": should_clauses,
                    "filter": filters,
                    "minimum_should_match": 0,
                }
            },
            "sort": [
                "_score",
                {"trust_score": {"order": "desc"}},
            ],
        }

        return query

    def _score_candidates(self, need: CapabilityNeed, candidates: list[dict]) -> list[MatchedItem]:
        """内存精排：对候选集进行多维评分"""
        weights = need.scoring_weights or {
            "capability_match": 0.35,
            "performance": 0.20,
            "price": 0.20,
            "trust": 0.15,
            "availability": 0.10,
        }

        results = []
        for doc in candidates:
            scores = MatchedItemScore(
                capability_match=self._score_capability(need, doc),
                performance=self._score_performance(need, doc),
                price=self._score_price(need, doc),
                trust=self._score_trust(need, doc),
                availability=self._score_availability(doc),
                composite=0.0,  # 占位，下面计算
            )

            # 加权综合评分
            scores.composite = round(
                scores.capability_match * weights.get("capability_match", 0.35) +
                scores.performance * weights.get("performance", 0.20) +
                scores.price * weights.get("price", 0.20) +
                scores.trust * weights.get("trust", 0.15) +
                scores.availability * weights.get("availability", 0.10),
                4,
            )

            # 构建匹配项
            item = MatchedItem(
                item_id=UUID(doc["item_id"]),
                item_name=doc["item_name"],
                item_type=doc["item_type"],
                item_version=doc["item_version"],
                provider_id=UUID(doc["provider_id"]),
                provider_name=doc["provider_name"],
                matched_domains=list(set(doc.get("domains", [])) & set(need.domains)),
                matched_task_types=[],  # TODO: 从 task_types 提取
                performance_summary={
                    "latency_p50_ms": doc.get("latency_p50_ms"),
                    "latency_p99_ms": doc.get("latency_p99_ms"),
                    "throughput_rps": doc.get("throughput_rps"),
                    "availability_sla": doc.get("availability_sla"),
                },
                pricing_summary={
                    "model": doc.get("pricing_model"),
                    "price_min": doc.get("price_min"),
                    "price_max": doc.get("price_max"),
                    "currency": doc.get("currency"),
                },
                trust_score=doc.get("trust_score", 50.0),
                certification_status=doc.get("certification_status"),
                scores=scores,
                trial_available=doc.get("status") == "active",
            )
            results.append(item)

        return results

    # ---- 评分函数 ----

    def _score_capability(self, need: CapabilityNeed, doc: dict) -> float:
        """
        能力匹配度评分 (0-1)。
        - 领域交集占比
        - 任务类型匹配
        - 语言匹配
        """
        score = 0.0

        # 领域匹配（0-0.5）
        doc_domains = set(doc.get("domains", []))
        need_domains = set(need.domains)
        if need_domains:
            domain_overlap = len(doc_domains & need_domains) / len(need_domains)
            score += domain_overlap * 0.5

        # 语言匹配（0-0.3）
        if need.supported_languages:
            doc_langs = set(doc.get("supported_languages", []))
            need_langs = set(need.supported_languages)
            lang_overlap = len(doc_langs & need_langs) / len(need_langs) if need_langs else 0
            score += lang_overlap * 0.3
        else:
            score += 0.15  # 未指定语言，给中间分

        # 任务类型匹配（0-0.2）
        if need.task_description:
            # 简化：检查 task_types 中是否有名称包含描述关键词
            task_types = doc.get("task_types", [])
            task_names = " ".join([tt.get("name", "") for tt in task_types])
            # 简单关键词重叠
            keywords = need.task_description.lower().split()
            matched = sum(1 for kw in keywords if kw in task_names.lower())
            if keywords:
                score += min(matched / len(keywords), 1.0) * 0.2

        return min(score, 1.0)

    def _score_performance(self, need: CapabilityNeed, doc: dict) -> float:
        """
        性能评分 (0-1)。
        - 延迟越低越好
        - 吞吐量越高越好
        - 可用性越高越好
        """
        score = 0.5  # 基础分

        if need.performance:
            # 延迟评分
            declared_p99 = doc.get("latency_p99_ms")
            if declared_p99 and need.performance.latency_p99_ms_max:
                if declared_p99 <= need.performance.latency_p99_ms_max:
                    # 低于上限，越低越好
                    score += 0.2 * (1 - declared_p99 / need.performance.latency_p99_ms_max)
                else:
                    # 超出上限
                    score -= 0.3

            # 可用性评分
            availability = doc.get("availability_sla")
            if availability:
                score += 0.15 * availability  # 0.999 → +0.15
                if need.performance.availability_sla_min and availability < need.performance.availability_sla_min:
                    score -= 0.3

        return max(0.0, min(score, 1.0))

    def _score_price(self, need: CapabilityNeed, doc: dict) -> float:
        """
        价格评分 (0-1)。
        - 越便宜越好（在约束范围内）
        - free = 1.0
        """
        pricing_model = doc.get("pricing_model")
        price_min = doc.get("price_min")

        if pricing_model == "free":
            return 1.0

        if price_min is None or price_min <= 0:
            return 0.5  # 无价格信息

        # 预算约束内的价格竞争力
        if need.budget:
            max_price = need.budget.max_price_per_call or need.budget.max_price_per_token or need.budget.max_price_per_hour
            if max_price:
                if price_min > max_price:
                    return 0.0  # 超预算
                return round(1.0 - (price_min / max_price) * 0.7, 4)  # 0.3-1.0

        # 无预算约束：用信任评分区间内排序
        return max(0.3, 1.0 - price_min / 10.0)  # 粗略评分

    def _score_trust(self, need: CapabilityNeed, doc: dict) -> float:
        """信任评分 (0-1)"""
        trust_score = doc.get("trust_score", 50.0)
        base_score = trust_score / 100.0

        # 认证加分
        if doc.get("certification_status") == "certified":
            base_score = min(base_score + 0.1, 1.0)

        # 低于最低要求
        if need.trust and need.trust.min_trust_score:
            if trust_score < need.trust.min_trust_score:
                return 0.0

        return round(base_score, 4)

    def _score_availability(self, doc: dict) -> float:
        """可用性评分 (0-1)"""
        availability = doc.get("availability_sla", 0.99)
        return min(availability, 1.0)
```

---

## 六、搜索 Service

```python
# src/aimart/search/service.py

from __future__ import annotations

import time
from uuid import UUID, uuid4

import structlog

from aimart.search.schemas import (
    CapabilityNeed, SearchResponse, MatchedItem,
    TrialRequest, TrialResult,
)
from aimart.search.matcher import CapabilityMatcher
from aimart.search.indexer import CapabilityIndexer
from aimart.audit.logger import AuditLogger

logger = structlog.get_logger()


class SearchService:
    """搜索域服务"""

    def __init__(
        self,
        matcher: CapabilityMatcher,
        indexer: CapabilityIndexer,
        audit_logger: AuditLogger,
        query_repo,
        sandbox_service=None,
    ):
        self._matcher = matcher
        self._indexer = indexer
        self._audit = audit_logger
        self._queries = query_repo
        self._sandbox = sandbox_service

    async def search(self, need: CapabilityNeed, agent_id: UUID) -> SearchResponse:
        """
        执行搜索。

        流程：
        1. 记录搜索查询
        2. 执行能力匹配
        3. 构建响应
        4. 审计日志
        """
        query_id = uuid4()

        # 1. 记录查询
        start_time = time.monotonic()

        # 2. 执行匹配
        match_start = time.monotonic()
        items = await self._matcher.match(need, agent_id)
        match_latency = int((time.monotonic() - match_start) * 1000)

        query_latency = int((time.monotonic() - start_time) * 1000)

        # 3. 构建响应
        response = SearchResponse(
            query_id=query_id,
            need_type=need.need_type,
            total_matches=len(items),
            returned_count=min(len(items), 20),
            items=items,
            query_latency_ms=query_latency,
            match_latency_ms=match_latency,
        )

        # 4. 持久化查询记录
        await self._queries.create(
            id=query_id,
            agent_id=agent_id,
            need_type=need.need_type,
            domains=need.domains,
            constraints=need.model_dump(exclude={"domains", "need_type", "task_description"}),
            scoring_weights=need.scoring_weights,
            result_count=len(items),
            query_latency_ms=query_latency,
            match_latency_ms=match_latency,
        )

        # 5. 审计日志
        await self._audit.log(
            log_type="SEARCH-QUERY",
            actor_type="agent",
            actor_id=str(agent_id),
            action="search",
            data={
                "query_id": str(query_id),
                "need_type": need.need_type,
                "domains": need.domains,
                "result_count": len(items),
                "query_latency_ms": query_latency,
            },
        )

        return response

    async def trial(self, request: TrialRequest, agent_id: UUID) -> TrialResult:
        """
        执行试用。

        流程：
        1. 校验试用限制（每个商品每日最多3次）
        2. 构建沙箱调用
        3. 执行受限调用
        4. 返回结构化结果
        """
        # 1. 试用限制检查
        today_trials = await self._queries.count_today_trials(agent_id, request.item_id)
        if today_trials >= 3:
            raise ValueError("该商品今日试用次数已达上限（3次）")

        # 2. 执行沙箱调用
        trial_start = time.monotonic()

        try:
            result = await self._sandbox.execute(
                item_id=request.item_id,
                input_data=request.trial_input,
                constraints={
                    "input_scale_pct": 10,   # 输入规模限制为正常10%
                    "max_calls": 5,          # 最多5次调用
                    "timeout_ms": 30000,     # 30秒超时
                },
            )

            latency = int((time.monotonic() - trial_start) * 1000)

            trial_result = TrialResult(
                trial_id=uuid4(),
                item_id=request.item_id,
                success=result.get("success", False),
                output=result.get("output"),
                performance={
                    "latency_ms": latency,
                    "tokens_used": result.get("tokens_used", 0),
                },
                errors=result.get("errors"),
                sandbox_constraints={"input_scale_pct": 10, "max_calls": 5},
            )
        except Exception as e:
            trial_result = TrialResult(
                trial_id=uuid4(),
                item_id=request.item_id,
                success=False,
                errors=[str(e)],
                sandbox_constraints={"input_scale_pct": 10, "max_calls": 5},
            )

        # 3. 审计日志
        await self._audit.log(
            log_type="SEARCH-TRIAL",
            actor_type="agent",
            actor_id=str(agent_id),
            target_type="item",
            target_id=str(request.item_id),
            action="trial",
            data={
                "success": trial_result.success,
                "latency_ms": trial_result.performance.get("latency_ms") if trial_result.performance else None,
            },
        )

        return trial_result
```

---

## 七、API 路由

```python
# src/aimart/search/router.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from aimart.identity.auth import require_auth, require_agent, AuthContext
from aimart.search.schemas import (
    CapabilityNeed, SearchResponse,
    TrialRequest, TrialResult,
)
from aimart.search import service as search_service

router = APIRouter()


@router.post("/capability", response_model=SearchResponse)
async def search_capability(need: CapabilityNeed, auth: AuthContext = Depends(require_auth)):
    """
    能力搜索——AI Agent 提交结构化能力需求描述，市场返回精确匹配的商品列表。

    这是 AIMart 搜索协议的核心入口。
    Agent 必须使用 CapabilityNeed 格式描述需求。
    """
    agent_id = auth.agent_id or auth.participant_id
    return await search_service.search(need, agent_id=agent_id)


@router.post("/trial", response_model=TrialResult)
async def trial_capability(request: TrialRequest, auth: AuthContext = Depends(require_agent)):
    """
    能力试用——Agent 在沙箱中试用商品，验证效果后再决定是否购买。

    限制：每个商品每日最多3次试用。
    """
    return await search_service.trial(request, agent_id=auth.agent_id)


@router.get("/suggest/domains")
async def suggest_domains(q: str, auth: AuthContext = Depends(require_auth)):
    """
    领域建议——Agent 输入部分关键词，返回匹配的领域标签列表。

    用于辅助 Agent 构造 CapabilityNeed。
    """
    # TODO: 从 ES 的 domains 聚合中获取建议
    return {"domains": [], "query": q}


@router.get("/suggest/task-types")
async def suggest_task_types(domain: str, auth: AuthContext = Depends(require_auth)):
    """
    任务类型建议——Agent 选择领域后，返回该领域下的任务类型列表。
    """
    # TODO: 从 ES 的 task_types 聚合中获取建议
    return {"task_types": [], "domain": domain}
```

---

## 八、搜索协议规范（机器可读）

```json
{
  "$schema": "https://aimart.dev/schemas/search-protocol/v1.0",
  "protocol_name": "AIMart Capability Search Protocol",
  "version": "1.0",
  "description": "定义 AI Agent 如何描述能力需求、市场如何返回匹配结果",

  "input": {
    "type": "object",
    "required": ["need_type", "domains"],
    "properties": {
      "need_type": {
        "type": "string",
        "enum": ["model", "skill", "expert", "compute"],
        "description": "需要的能力类型"
      },
      "domains": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 1,
        "description": "能力领域标签，至少一个"
      },
      "task_description": {
        "type": "string",
        "maxLength": 500,
        "description": "自然语言任务描述（可选，辅助语义匹配）"
      },
      "supported_languages": {
        "type": "array",
        "items": {"type": "string"},
        "description": "期望支持的语言"
      },
      "performance": {
        "type": "object",
        "properties": {
          "latency_p50_ms_max": {"type": "integer", "exclusiveMinimum": 0},
          "latency_p99_ms_max": {"type": "integer", "exclusiveMinimum": 0},
          "throughput_rps_min": {"type": "integer", "exclusiveMinimum": 0},
          "availability_sla_min": {"type": "number", "exclusiveMinimum": 0, "maximum": 1}
        }
      },
      "budget": {
        "type": "object",
        "properties": {
          "max_price_per_call": {"type": "number", "exclusiveMinimum": 0},
          "max_price_per_token": {"type": "number", "exclusiveMinimum": 0},
          "max_price_per_hour": {"type": "number", "exclusiveMinimum": 0},
          "preferred_pricing_model": {
            "type": "string",
            "enum": ["per_call", "per_token", "per_hour", "subscription", "free"]
          },
          "currency": {"type": "string", "enum": ["CNY", "USD", "USDC"]}
        }
      },
      "trust": {
        "type": "object",
        "properties": {
          "min_trust_score": {"type": "number", "minimum": 0, "maximum": 100},
          "certification_required": {"type": "boolean"},
          "min_transactions": {"type": "integer", "exclusiveMinimum": 0}
        }
      },
      "scoring_weights": {
        "type": "object",
        "properties": {
          "capability_match": {"type": "number", "minimum": 0, "maximum": 1},
          "performance": {"type": "number", "minimum": 0, "maximum": 1},
          "price": {"type": "number", "minimum": 0, "maximum": 1},
          "trust": {"type": "number", "minimum": 0, "maximum": 1},
          "availability": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "custom": "各权重之和必须为1.0"
      }
    }
  },

  "output": {
    "type": "object",
    "properties": {
      "query_id": {"type": "string", "format": "uuid"},
      "need_type": {"type": "string"},
      "total_matches": {"type": "integer"},
      "returned_count": {"type": "integer", "maximum": 20},
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "item_id": {"type": "string", "format": "uuid"},
            "item_name": {"type": "string"},
            "item_type": {"type": "string"},
            "scores": {
              "type": "object",
              "properties": {
                "capability_match": {"type": "number", "minimum": 0, "maximum": 1},
                "performance": {"type": "number", "minimum": 0, "maximum": 1},
                "price": {"type": "number", "minimum": 0, "maximum": 1},
                "trust": {"type": "number", "minimum": 0, "maximum": 1},
                "availability": {"type": "number", "minimum": 0, "maximum": 1},
                "composite": {"type": "number", "minimum": 0, "maximum": 1}
              }
            },
            "trial_available": {"type": "boolean"}
          }
        }
      }
    }
  },

  "constraints": {
    "max_results_per_query": 20,
    "max_trials_per_item_per_day": 3,
    "trial_input_scale_pct": 10,
    "trial_max_calls": 5,
    "trial_timeout_ms": 30000,
    "min_composite_score": 0.3,
    "scoring_weights_must_sum_to": 1.0
  }
}
```

---

## 九、Agent 框架集成示例

```python
# src/aimart/integrations/langchain_plugin/search_tool.py

from __future__ import annotations

from typing import Optional, Type

import httpx
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class AIMartSearchInput(BaseModel):
    """AIMart 搜索工具输入"""
    need_type: str = Field(..., description="需要的能力类型: model | skill | expert | compute")
    domains: list[str] = Field(..., description="能力领域，如 ['legal', 'contract_review']")
    task_description: Optional[str] = Field(None, description="任务描述")
    max_price: Optional[float] = Field(None, description="最大价格(CNY)")
    min_trust_score: Optional[float] = Field(None, description="最低信任评分(0-100)")


class AIMartSearchTool(BaseTool):
    """LangChain 集成——AIMart 能力搜索工具"""

    name: str = "aimart_capability_search"
    description: str = (
        "在 AIMart 市场搜索 AI 能力（模型、技能、专家、算力）。"
        "当你发现当前能力不足以完成任务时，使用此工具搜索可购买的能力。"
    )
    args_schema: Type[BaseModel] = AIMartSearchInput

    base_url: str = "https://api.aimart.dev/api/v1"
    api_key: str = ""

    def _run(self, need_type: str, domains: list[str], task_description: str = None,
             max_price: float = None, min_trust_score: float = None) -> str:
        """同步执行搜索"""
        import json

        payload = {
            "need_type": need_type,
            "domains": domains,
        }
        if task_description:
            payload["task_description"] = task_description
        if max_price:
            payload["budget"] = {"max_price_per_call": max_price, "currency": "CNY"}
        if min_trust_score:
            payload["trust"] = {"min_trust_score": min_trust_score}

        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/search/capability",
                json=payload,
                headers={"X-API-Key": self.api_key},
                timeout=10.0,
            )

        if response.status_code == 200:
            result = response.json()
            # 为 LLM 友好地格式化结果
            items = result.get("items", [])
            if not items:
                return "未找到匹配的能力商品。"

            output_lines = [f"找到 {len(items)} 个匹配结果：\n"]
            for i, item in enumerate(items[:5], 1):
                output_lines.append(
                    f"{i}. {item['item_name']} (v{item['item_version']})\n"
                    f"   类型: {item['item_type']} | 评分: {item['scores']['composite']:.2f}\n"
                    f"   价格: {item['pricing_summary'].get('model', 'N/A')} "
                    f"({item['pricing_summary'].get('price_min', 'N/A')} {item['pricing_summary'].get('currency', 'CNY')})\n"
                    f"   信任: {item['trust_score']} | 可试用: {'是' if item['trial_available'] else '否'}"
                )

            return "\n".join(output_lines)
        else:
            return f"搜索失败: {response.status_code} {response.text}"

    async def _arun(self, need_type: str, domains: list[str], **kwargs) -> str:
        """异步执行搜索"""
        # 异步版本，使用 httpx.AsyncClient
        return self._run(need_type, domains, **kwargs)
```

---

## 十、Codex 执行检查清单

| # | 检查项 | 预期结果 |
|---|--------|---------|
| 1 | 创建 2 张数据表 | `search_queries`, `capability_indices` |
| 2 | ES 索引创建 | `aimart_capabilities` 索引含正确 mapping（nested task_types、domain_analyzer） |
| 3 | AgentCard → ES 文档转换 | 所有字段正确映射，价格区间计算正确 |
| 4 | 批量索引 | bulk_index 返回成功数量 |
| 5 | CapabilityNeed 校验 | need_type 必填、domains 至少1个、scoring_weights 总和为1.0 |
| 6 | ES 粗筛查询 | bool(must+should+filter) 正确构建，领域/语言/任务类型均有匹配条件 |
| 7 | 性能约束过滤 | latency_p99_max → range filter, throughput_min → range filter |
| 8 | 预算约束过滤 | max_price → price_min range filter, preferred_pricing_model → boost |
| 9 | 信任约束过滤 | min_trust_score → range filter, certification_required → term filter |
| 10 | 五维评分 | capability_match/performance/price/trust/availability 各 0-1，composite 加权求和 |
| 11 | 结果排序 | composite 降序，min_composite_score 过滤，max 20 条 |
| 12 | 试用限制 | 每商品每日3次，沙箱 input_scale=10%, max_calls=5 |
| 13 | LangChain 集成 | AIMartSearchTool 可注册为 LangChain Tool，输入输出正确 |
| 14 | 审计日志 | 搜索查询和试用都有 AUDIT 记录 |
