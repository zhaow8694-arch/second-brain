# AIMart 工程执行文件 05：核心 API
tags: [aimart, api, backend]

tags: [aimart, api, backend]
> Codex 执行指令：实现 6 个核心服务的 API 路由、Pydantic Schema 和 Service 骨架
tags: [aimart, api, backend]

tags: [aimart, api, backend]
---
tags: [aimart, api, backend]

## 一、Identity Service

```python
# src/aimart/identity/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---- 请求模型 ----

class RegisterParticipantRequest(BaseModel):
    type: str = Field(..., pattern="^(owner|provider|certifier|facilitator)$")
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    jurisdiction: str = Field(..., min_length=2, max_length=10)


class RegisterAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    framework: str = Field(..., pattern="^(langchain|crewai|autogen|dify|coze|custom)$")
    capability_scope: list[str] = Field(default_factory=list)
    spending_authority_level: str = Field(default="L0", pattern="^L[0-3]$")


class GetTokenRequest(BaseModel):
    grant_type: str = Field(default="client_credentials", pattern="^client_credentials$")


# ---- 响应模型 ----

class RegisterParticipantResponse(BaseModel):
    participant_id: UUID
    status: str = "pending_verification"


class RegisterAgentResponse(BaseModel):
    agent_id: UUID
    api_key: str = Field(..., description="API Key（仅创建时返回一次）")
    api_key_expires_at: datetime


class GetTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class ParticipantDetailResponse(BaseModel):
    id: UUID
    type: str
    name: str
    email: str
    jurisdiction: str
    kyc_status: str
    created_at: datetime


class AgentDetailResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    framework: str
    capability_scope: list[str]
    trust_score: float
    spending_authority: str
    status: str
    created_at: datetime
    last_active_at: Optional[datetime] = None
```

```python
# src/aimart/identity/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aimart.identity.schemas import (
    RegisterParticipantRequest, RegisterParticipantResponse,
    RegisterAgentRequest, RegisterAgentResponse,
    GetTokenRequest, GetTokenResponse,
    ParticipantDetailResponse, AgentDetailResponse,
)
from aimart.identity.auth import require_auth, require_owner, require_mfa
from aimart.identity import service as identity_service

router = APIRouter()


@router.post("/register", response_model=RegisterParticipantResponse, status_code=status.HTTP_201_CREATED)
async def register_participant(request: RegisterParticipantRequest):
    """注册参与者（Owner/Provider/Certifier/Facilitator）"""
    result = await identity_service.register_participant(request)
    return result


@router.post("/agents", response_model=RegisterAgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(request: RegisterAgentRequest, auth=Depends(require_owner)):
    """注册 AI Agent"""
    result = await identity_service.register_agent(request, owner_id=auth.participant_id)
    return result


@router.post("/token", response_model=GetTokenResponse)
async def get_token(request: GetTokenRequest, auth=Depends(Depends(lambda: None))):
    """获取访问令牌"""
    result = await identity_service.get_token(request)
    return result


@router.get("/participants/{participant_id}", response_model=ParticipantDetailResponse)
async def get_participant(participant_id: UUID, auth=Depends(require_auth)):
    """获取参与者详情"""
    result = await identity_service.get_participant(participant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    return result


@router.get("/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: UUID, auth=Depends(require_auth)):
    """获取 Agent 详情"""
    result = await identity_service.get_agent(agent_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.delete("/agents/{agent_id}", status_code=status.HTTP_200_OK)
async def terminate_agent(agent_id: UUID, auth=Depends(require_owner), mfa=Depends(require_mfa)):
    """注销 Agent"""
    result = await identity_service.terminate_agent(agent_id, owner_id=auth.participant_id)
    return result
```

```python
# src/aimart/identity/auth.py

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

from aimart.config import settings

api_key_header = APIKeyHeader(name="X-API-Key")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/identity/token")


class AuthContext:
    def __init__(self, participant_id: str, participant_type: str, agent_id: str | None = None):
        self.participant_id = participant_id
        self.participant_type = participant_type
        self.agent_id = agent_id


async def verify_token(token: str) -> AuthContext:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.security_jwt_public_key,
            algorithms=[settings.security_jwt_algorithm],
            issuer=settings.security_jwt_issuer,
        )
        participant_id = payload.get("sub")
        participant_type = payload.get("type")
        agent_id = payload.get("agent_id")
        if participant_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return AuthContext(participant_id, participant_type, agent_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def require_auth(token: str = Depends(oauth2_scheme)) -> AuthContext:
    """任何已认证用户"""
    return await verify_token(token)


async def require_owner(token: str = Depends(oauth2_scheme)) -> AuthContext:
    """仅 Owner"""
    auth = await verify_token(token)
    if auth.participant_type != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return auth


async def require_platform_or_regulator(token: str = Depends(oauth2_scheme)) -> AuthContext:
    """仅 Platform 或 Regulator"""
    auth = await verify_token(token)
    if auth.participant_type not in ("platform", "regulator"):
        raise HTTPException(status_code=403, detail="Platform or regulator access required")
    return auth


async def require_mfa():
    """MFA 验证（占位，后续集成实际 MFA 服务）"""
    # TODO: 集成 MFA 服务
    return True
```

---

## 二、Catalog Service

```python
# src/aimart/catalog/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ListItemRequest(BaseModel):
    agentcard: dict[str, Any] = Field(..., description="完整的 AgentCard JSON")


class ListItemResponse(BaseModel):
    item_id: UUID
    status: str = "pending_verification"
    verification_estimate_minutes: int = 30
    errors: list[dict] | None = None
    warnings: list[dict] | None = None


class ItemDetailResponse(BaseModel):
    item_id: UUID
    provider_id: UUID
    item_name: str
    item_type: str
    item_version: str
    status: str
    agentcard: dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None


class UpdateItemRequest(BaseModel):
    agentcard_patch: dict[str, Any] = Field(..., description="AgentCard 变更部分")


class UpdateItemResponse(BaseModel):
    item_id: UUID
    new_version: str
    status: str = "pending_verification"


class AgentCardResponse(BaseModel):
    schema_version: str
    body: dict[str, Any]
```

```python
# src/aimart/catalog/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aimart.catalog.schemas import (
    ListItemRequest, ListItemResponse,
    ItemDetailResponse, UpdateItemRequest, UpdateItemResponse,
    AgentCardResponse,
)
from aimart.identity.auth import require_auth, require_owner_or_provider
from aimart.catalog import service as catalog_service
from aimart.config import settings

router = APIRouter()


@router.post("/items", response_model=ListItemResponse, status_code=status.HTTP_201_CREATED)
async def list_item(request: ListItemRequest, auth=Depends(require_owner_or_provider)):
    """上架能力商品"""
    # Feature flag check
    item_type = request.agentcard.get("identity", {}).get("item_type")
    if item_type == "model" and not settings.ff_catalog_model_enabled:
        raise HTTPException(status_code=403, detail="Model catalog is not enabled")
    if item_type == "skill" and not settings.ff_catalog_skill_enabled:
        raise HTTPException(status_code=403, detail="Skill catalog is not enabled")
    if item_type == "expert" and not settings.ff_catalog_expert_enabled:
        raise HTTPException(status_code=403, detail="Expert catalog is not enabled")
    if item_type == "compute" and not settings.ff_catalog_compute_enabled:
        raise HTTPException(status_code=403, detail="Compute catalog is not enabled")

    result = await catalog_service.list_item(provider_id=auth.participant_id, agentcard=request.agentcard)
    return result


@router.get("/items/{item_id}", response_model=ItemDetailResponse)
async def get_item(item_id: UUID, auth=Depends(require_auth)):
    """获取商品详情"""
    result = await catalog_service.get_item(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.put("/items/{item_id}", response_model=UpdateItemResponse)
async def update_item(item_id: UUID, request: UpdateItemRequest, auth=Depends(require_owner_or_provider)):
    """更新商品信息"""
    result = await catalog_service.update_item(item_id, request.agentcard_patch, provider_id=auth.participant_id)
    return result


@router.delete("/items/{item_id}")
async def delist_item(item_id: UUID, auth=Depends(require_owner_or_provider)):
    """下架商品"""
    result = await catalog_service.delist_item(item_id, provider_id=auth.participant_id)
    return result


@router.get("/items/{item_id}/agentcard", response_model=AgentCardResponse)
async def get_agentcard(item_id: UUID, auth=Depends(require_auth)):
    """获取机器可读 AgentCard"""
    result = await catalog_service.get_agentcard(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="AgentCard not found")
    return result
```

---

## 三、Search Service

```python
# src/aimart/search/schemas.py

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CapabilityQuery(BaseModel):
    task_description: str = Field(..., min_length=1)
    required_domains: list[str] = Field(default_factory=list)
    required_languages: list[str] = Field(default_factory=list)
    performance_constraints: Optional[dict] = None
    cost_constraints: Optional[dict] = None
    trust_score_min: int = Field(default=0, ge=0, le=100)
    delivery_preference: Optional[str] = None
    item_type_filter: list[str] = Field(default_factory=list)
    sort_by: str = Field(default="relevance", pattern="^(relevance|trust_score|price_asc|price_desc)$")


class SearchPagination(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=20)


class SearchCapabilitiesRequest(BaseModel):
    query: CapabilityQuery
    pagination: SearchPagination = Field(default_factory=SearchPagination)


class SearchResultItem(BaseModel):
    item_id: UUID
    item_name: str
    item_type: str
    provider_name: str
    match_score: float
    trust_score: float
    price_display: str  # e.g., "0.05 CNY/call"
    key_performance: dict[str, Any]
    certification_status: str
    agentcard_url: str


class SearchCapabilitiesResponse(BaseModel):
    total_matches: int
    results: list[SearchResultItem]
    query_id: UUID


class RecommendationRequest(BaseModel):
    current_task_context: str
    capability_gap: list[str]
    budget_remaining: float


class RecommendationResponse(BaseModel):
    recommendations: list[SearchResultItem]
    reason: str
```

```python
# src/aimart/search/router.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from aimart.search.schemas import (
    SearchCapabilitiesRequest, SearchCapabilitiesResponse,
    RecommendationRequest, RecommendationResponse,
)
from aimart.identity.auth import require_auth
from aimart.search import service as search_service
from aimart.config import settings

router = APIRouter()


@router.post("/capabilities", response_model=SearchCapabilitiesResponse)
async def search_capabilities(request: SearchCapabilitiesRequest, auth=Depends(require_auth)):
    """搜索匹配的能力商品"""
    if not settings.ff_search_capability_query_enabled:
        raise HTTPException(status_code=403, detail="Search capability is not enabled")

    result = await search_service.search_capabilities(
        query=request.query,
        pagination=request.pagination,
        agent_id=auth.agent_id,
    )
    return result


@router.get("/capabilities/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest, auth=Depends(require_auth)):
    """获取个性化推荐"""
    if not settings.ff_search_recommendation_enabled:
        raise HTTPException(status_code=403, detail="Recommendation feature is not enabled")

    result = await search_service.get_recommendations(
        request=request,
        agent_id=auth.agent_id,
    )
    return result
```

---

## 四、Exchange Service

```python
# src/aimart/exchange/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateTrialRequest(BaseModel):
    item_id: UUID
    query_id: Optional[UUID] = None
    trial_input: dict[str, Any]


class CreateTrialResponse(BaseModel):
    trial_id: UUID
    sandbox_endpoint: str
    trial_constraints: dict[str, Any]


class ExecuteTrialRequest(BaseModel):
    input: dict[str, Any]


class ExecuteTrialResponse(BaseModel):
    output: dict[str, Any]
    performance_metrics: dict[str, Any]
    trial_remaining_calls: int


class CreateOrderRequest(BaseModel):
    item_id: UUID
    query_id: Optional[UUID] = None
    pricing_plan: str
    quantity: int = 1
    delivery_params: Optional[dict] = None
    escrow_enabled: bool = True


class CreateOrderResponse(BaseModel):
    order_id: UUID
    status: str
    authorization_required: str  # none | owner_notification | owner_approval | owner_confirmation
    payment_required: Optional[dict] = None
    expires_at: datetime


class ConfirmOrderRequest(BaseModel):
    confirmation: bool


class ConfirmOrderResponse(BaseModel):
    order_id: UUID
    status: str


class EffectReportRequest(BaseModel):
    success: bool
    effect_score: int = Field(..., ge=1, le=5)
    actual_latency_ms: int
    actual_cost_cny: float
    declaration_accuracy: float = Field(..., ge=0, le=1)
    notes_machine: Optional[str] = None


class EffectReportResponse(BaseModel):
    report_id: UUID
    trust_score_impact: float


class CreateDisputeRequest(BaseModel):
    order_id: UUID
    dispute_type: str = Field(..., pattern="^(quality|sla_violation|unauthorized_charge|false_declaration)$")
    evidence: dict[str, Any]
    requested_resolution: str = Field(..., pattern="^(refund|partial_refund|replacement|other)$")


class CreateDisputeResponse(BaseModel):
    dispute_id: UUID
    status: str = "open"
    estimated_resolution_days: int = 7
    fund_status: str = "frozen"
```

```python
# src/aimart/exchange/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aimart.exchange.schemas import (
    CreateTrialRequest, CreateTrialResponse,
    ExecuteTrialRequest, ExecuteTrialResponse,
    CreateOrderRequest, CreateOrderResponse,
    ConfirmOrderRequest, ConfirmOrderResponse,
    EffectReportRequest, EffectReportResponse,
    CreateDisputeRequest, CreateDisputeResponse,
)
from aimart.identity.auth import require_auth, require_owner
from aimart.exchange import service as exchange_service
from aimart.config import settings

router = APIRouter()


@router.post("/trials", response_model=CreateTrialResponse, status_code=status.HTTP_201_CREATED)
async def create_trial(request: CreateTrialRequest, auth=Depends(require_auth)):
    """发起试用"""
    if not settings.ff_exchange_trial_enabled:
        raise HTTPException(status_code=403, detail="Trial feature is not enabled")
    result = await exchange_service.create_trial(
        item_id=request.item_id,
        agent_id=auth.agent_id or auth.participant_id,
        query_id=request.query_id,
        trial_input=request.trial_input,
    )
    return result


@router.post("/trials/{trial_id}/execute", response_model=ExecuteTrialResponse)
async def execute_trial(trial_id: UUID, request: ExecuteTrialRequest, auth=Depends(require_auth)):
    """执行试用调用"""
    result = await exchange_service.execute_trial(trial_id, request.input)
    return result


@router.post("/orders", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(request: CreateOrderRequest, auth=Depends(require_auth)):
    """创建订单"""
    result = await exchange_service.create_order(
        item_id=request.item_id,
        agent_id=auth.agent_id or auth.participant_id,
        owner_id=auth.participant_id,
        query_id=request.query_id,
        pricing_plan=request.pricing_plan,
        quantity=request.quantity,
        delivery_params=request.delivery_params,
        escrow_enabled=request.escrow_enabled,
    )
    return result


@router.post("/orders/{order_id}/confirm", response_model=ConfirmOrderResponse)
async def confirm_order(order_id: UUID, request: ConfirmOrderRequest, auth=Depends(require_auth)):
    """确认订单"""
    result = await exchange_service.confirm_order(
        order_id=order_id,
        confirmation=request.confirmation,
        confirmer_id=auth.participant_id,
    )
    return result


@router.post("/orders/{order_id}/effect-report", response_model=EffectReportResponse)
async def submit_effect_report(order_id: UUID, request: EffectReportRequest, auth=Depends(require_auth)):
    """回传使用效果"""
    result = await exchange_service.submit_effect_report(
        order_id=order_id,
        agent_id=auth.agent_id or auth.participant_id,
        report=request,
    )
    return result


@router.post("/disputes", response_model=CreateDisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(request: CreateDisputeRequest, auth=Depends(require_auth)):
    """发起争议"""
    result = await exchange_service.create_dispute(
        order_id=request.order_id,
        initiator_type=auth.participant_type,
        initiator_id=auth.participant_id,
        dispute_type=request.dispute_type,
        evidence=request.evidence,
        requested_resolution=request.requested_resolution,
    )
    return result
```

---

## 五、Payment Service

```python
# src/aimart/payment/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateBudgetPoolRequest(BaseModel):
    currency: str = Field(..., pattern="^(CNY|USD|USDC)$")
    initial_balance: float = Field(..., gt=0)
    limits: BudgetLimits
    recharge_policy: Optional[RechargePolicy] = None


class BudgetLimits(BaseModel):
    total_cap: float = Field(..., gt=0)
    single_transaction_max: float = Field(..., gt=0)
    daily_max: float = Field(..., gt=0)
    weekly_max: float = Field(..., gt=0)
    monthly_max: float = Field(..., gt=0)


class RechargePolicy(BaseModel):
    auto_recharge: bool = False
    threshold: float = Field(..., gt=0)
    recharge_amount: float = Field(..., gt=0)


class AllocateBudgetRequest(BaseModel):
    agent_id: UUID
    daily_max: float = Field(..., gt=0)
    per_call_max: float = Field(..., gt=0)


class BudgetPoolResponse(BaseModel):
    budget_pool_id: UUID
    status: str = "active"


class BudgetAllocationResponse(BaseModel):
    allocation_id: UUID
    status: str = "active"


class BudgetStatusResponse(BaseModel):
    balance: float
    daily_spent: float
    weekly_spent: float
    monthly_spent: float
    active_allocations: int
    pending_escrows: list[dict[str, Any]]


class TransactionFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    agent_id: Optional[UUID] = None
    item_id: Optional[UUID] = None
    status: Optional[str] = None


class TransactionRecord(BaseModel):
    transaction_id: UUID
    order_id: UUID
    amount: float
    currency: str
    settlement_method: str
    status: str
    created_at: datetime


class TransactionListResponse(BaseModel):
    transactions: list[TransactionRecord]
    total_count: int
```

```python
# src/aimart/payment/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aimart.payment.schemas import (
    CreateBudgetPoolRequest, BudgetPoolResponse,
    AllocateBudgetRequest, BudgetAllocationResponse,
    BudgetStatusResponse,
    TransactionFilter, TransactionListResponse,
)
from aimart.identity.auth import require_auth, require_owner
from aimart.payment import service as payment_service

router = APIRouter()


@router.post("/budget-pools", response_model=BudgetPoolResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_pool(request: CreateBudgetPoolRequest, auth=Depends(require_owner)):
    """创建预算池"""
    result = await payment_service.create_budget_pool(
        owner_id=auth.participant_id,
        currency=request.currency,
        initial_balance=request.initial_balance,
        limits=request.limits,
        recharge_policy=request.recharge_policy,
    )
    return result


@router.post("/budget-pools/{pool_id}/agents", response_model=BudgetAllocationResponse)
async def allocate_budget(pool_id: UUID, request: AllocateBudgetRequest, auth=Depends(require_owner)):
    """为 Agent 分配预算"""
    result = await payment_service.allocate_budget(
        pool_id=pool_id,
        owner_id=auth.participant_id,
        agent_id=request.agent_id,
        daily_max=request.daily_max,
        per_call_max=request.per_call_max,
    )
    return result


@router.get("/budget-pools/{pool_id}/status", response_model=BudgetStatusResponse)
async def get_budget_status(pool_id: UUID, auth=Depends(require_owner)):
    """查询预算池状态"""
    result = await payment_service.get_budget_status(pool_id, owner_id=auth.participant_id)
    return result


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(filters: TransactionFilter = Depends(), auth=Depends(require_auth)):
    """查询交易记录"""
    result = await payment_service.list_transactions(
        filters=filters,
        requester_id=auth.participant_id,
        requester_type=auth.participant_type,
    )
    return result
```

---

## 六、Trust Service

```python
# src/aimart/trust/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TrustScoreResponse(BaseModel):
    item_id: UUID
    trust_score: float
    score_composition: dict[str, float]
    trend: str  # improving | stable | declining
    last_updated: datetime


class ProviderScoreResponse(BaseModel):
    provider_id: UUID
    overall_rating: float
    trust_score: float
    listing_count: int
    dispute_rate: float
    avg_effect_score: float


class CertifyItemRequest(BaseModel):
    item_id: UUID
    certification_level: str = Field(..., pattern="^(platform_certified|premium_certified)$")
    benchmark_results: list[dict[str, Any]]
    valid_until: datetime


class CertifyItemResponse(BaseModel):
    certification_id: UUID
    status: str = "active"
```

```python
# src/aimart/trust/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from aimart.trust.schemas import (
    TrustScoreResponse, ProviderScoreResponse,
    CertifyItemRequest, CertifyItemResponse,
)
from aimart.identity.auth import require_auth, require_certifier
from aimart.trust import service as trust_service
from aimart.config import settings

router = APIRouter()


@router.get("/items/{item_id}/score", response_model=TrustScoreResponse)
async def get_item_trust_score(item_id: UUID, auth=Depends(require_auth)):
    """获取商品信任评分"""
    if not settings.ff_trust_dynamic_score_enabled:
        raise HTTPException(status_code=403, detail="Dynamic trust score is not enabled")
    result = await trust_service.get_item_score(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.get("/providers/{provider_id}/score", response_model=ProviderScoreResponse)
async def get_provider_score(provider_id: UUID, auth=Depends(require_auth)):
    """获取卖家信任评分"""
    result = await trust_service.get_provider_score(provider_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return result


@router.post("/certifications", response_model=CertifyItemResponse)
async def certify_item(request: CertifyItemRequest, auth=Depends(require_certifier)):
    """申请/签发认证"""
    result = await trust_service.certify_item(
        item_id=request.item_id,
        certifier_id=auth.participant_id,
        certification_level=request.certification_level,
        benchmark_results=request.benchmark_results,
        valid_until=request.valid_until,
    )
    return result
```

---

## 七、Service 骨架模板

每个 service 文件遵循统一结构：

```python
# src/aimart/{domain}/service.py 模板

from __future__ import annotations

import structlog

from aimart.dependencies import audit_logger
from aimart.rules.registry import rules_engine
from aimart.rules.engine import RuleContext

logger = structlog.get_logger()


class {Domain}Service:

    async def {method}(self, ...) -> dict:
        """
        业务方法模板：
        1. 构建规则上下文
        2. 规则引擎评估
        3. 审计日志记录
        4. 执行业务逻辑
        5. 返回结果
        """
        # 1. 规则评估
        # context = RuleContext(...)
        # rule_result = await rules_engine.evaluate(context)
        # if rule_result.blocked:
        #     raise RuleViolationError(...)

        # 2. 审计日志
        # await audit_logger.log(...)

        # 3. 业务逻辑
        # ...

        # 4. 返回
        return {...}


# 模块级单例
{domain}_service = {Domain}Service()
```

---

## 八、Codex 执行指令

```
1. 实现 src/aimart/identity/ 全部4个文件（schemas/router/service/auth）
2. 实现 src/aimart/catalog/ 全部4个文件（schemas/router/service/validator）
3. 实现 src/aimart/search/ 全部4个文件（schemas/router/service/matcher）
4. 实现 src/aimart/exchange/ 全部4个文件（schemas/router/service/sandbox）
5. 实现 src/aimart/payment/ 全部5个文件（schemas/router/service/budget/authorization/anomaly）
6. 实现 src/aimart/trust/ 全部4个文件（schemas/router/service/scorer）
7. 每个 service.py 实现核心方法的完整逻辑（数据库操作用 asyncpg/raw SQL）
8. 每个 router.py 确保所有端点与 AIMart_Config.md 中定义的接口一致
9. 每个关键操作集成规则引擎评估和审计日志记录
10. 编写 tests/integration/test_search_flow.py：搜索 → 试用 → 下单完整流程
11. 编写 tests/integration/test_payment_flow.py：预算创建 → 分配 → 消费 → 异常检测
12. 运行 pytest tests/ 验证所有 API 端点可正常响应
13. 运行 uvicorn aimart.main:app 启动完整服务，访问 /docs 查看 Swagger 文档
```
