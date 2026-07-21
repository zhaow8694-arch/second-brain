<!-- AIMart 完整合并版 v2：保留原始文件内容，并追加 Codex MVP 落地补充。生成日期：2026-06-06 -->

# AIMart 配置文件：环境、接口、特性开关

> 版本：v1.0 | 2026-06-07 | 状态：设计阶段

---

## 一、环境配置

### 1.1 环境定义

| 环境名称 | 标识 | 用途 | 数据 | 访问控制 |
|---------|------|------|------|---------|
| 开发环境 | dev | 开发与调试 | 模拟数据 | 开发团队 |
| 测试环境 | staging | 集成测试与预发布 | 脱敏生产数据 | 开发团队 + 内测用户 |
| 预生产环境 | pre-prod | 最终验证 | 生产数据镜像 | 运维团队 |
| 生产环境 | prod | 正式运营 | 真实数据 | 全部参与者 |

### 1.2 全局环境变量

```yaml
# AIMart 全局环境配置
aimart:
  platform:
    name: AIMart
    version: "1.0.0"
    environment: dev | staging | pre-prod | prod
    base_url:
      dev: "http://localhost:8080"
      staging: "https://staging.aimart.dev"
      pre-prod: "https://preprod.aimart.dev"
      prod: "https://api.aimart.dev"
    api_version: "v1"
    timezone: "UTC"
    locale: "zh-CN"

  # 数据存储
  storage:
    primary_db:
      engine: "postgresql"
      version: "16"
      host: "${DB_HOST}"
      port: 5432
      database: "aimart_${ENVIRONMENT}"
      max_connections: 100
      connection_timeout_ms: 5000
    cache:
      engine: "redis"
      version: "7"
      host: "${REDIS_HOST}"
      port: 6379
      ttl_default_seconds: 3600
    search_index:
      engine: "elasticsearch"
      version: "8"
      host: "${ES_HOST}"
      port: 9200
    audit_log_store:
      engine: "clickhouse"
      version: "24"
      host: "${CLICKHOUSE_HOST}"
      port: 8123
      retention_days: 365
    object_storage:
      engine: "minio | s3"
      bucket: "aimart-${ENVIRONMENT}"
      region: "cn-north-1"

  # 消息队列
  messaging:
    engine: "kafka"
    version: "3.7"
    brokers: "${KAFKA_BROKERS}"
    topics:
      - name: "aimart.orders"
        partitions: 12
        retention_ms: 604800000  # 7 days
      - name: "aimart.payments"
        partitions: 12
        retention_ms: 604800000
      - name: "aimart.trust_events"
        partitions: 6
        retention_ms: 2592000000  # 30 days
      - name: "aimart.audit_log"
        partitions: 24
        retention_ms: 31536000000  # 365 days
      - name: "aimart.search_queries"
        partitions: 6
        retention_ms: 86400000  # 1 day
      - name: "aimart.effect_reports"
        partitions: 6
        retention_ms: 2592000000

  # 安全
  security:
    tls_min_version: "1.3"
    encryption_at_rest: "AES-256-GCM"
    encryption_in_transit: "TLS_AES_256_GCM_SHA384"
    jwt:
      algorithm: "RS256"
      access_token_ttl_minutes: 60
      refresh_token_ttl_days: 30
      issuer: "aimart.dev"
    rate_limiting:
      global_rps: 10000
      per_agent_rps: 100
      per_provider_rps: 500
    cors:
      allowed_origins:
        - "https://aimart.dev"
        - "https://*.aimart.dev"
      allowed_methods: ["GET", "POST", "PUT", "PATCH", "DELETE"]
      max_age_seconds: 86400

  # 监控
  monitoring:
    metrics:
      engine: "prometheus"
      port: 9090
      scrape_interval_seconds: 15
    tracing:
      engine: "jaeger"
      sample_rate: 0.1  # 10% 采样率
    alerting:
      engine: "alertmanager"
      channels: ["email", "webhook", "sms"]
```

---

## 二、接口定义

### 2.1 API 概览

| 服务 | 基路径 | 描述 | 协议 |
|------|--------|------|------|
| Identity Service | `/api/v1/identity` | 身份认证与授权 | REST |
| Catalog Service | `/api/v1/catalog` | 商品管理 | REST |
| Search Service | `/api/v1/search` | 能力搜索与匹配 | REST |
| Exchange Service | `/api/v1/exchange` | 交易流程 | REST + WebSocket |
| Payment Service | `/api/v1/payment` | 预算与结算 | REST |
| Trust Service | `/api/v1/trust` | 信任评分与评价 | REST |
| Audit Service | `/api/v1/audit` | 审计日志查询 | REST |
| Sandbox Service | `/api/v1/sandbox` | 试用沙箱 | REST + gRPC |
| MCP Gateway | `/mcp` | MCP 协议网关 | MCP (SSE/stdio) |
| A2A Gateway | `/a2a` | A2A 协议网关 | A2A (HTTP/SSE) |

### 2.2 核心接口详情

#### Identity Service

```yaml
# 身份服务接口
POST /api/v1/identity/register:
  description: 注册参与者（Owner/Provider/Certifier/Facilitator）
  auth: none
  request:
    type: "owner | provider | certifier | facilitator"
    name: string
    email: string
    jurisdiction: string
    kyc_documents: file[]
  response:
    participant_id: uuid
    status: "pending_verification"

POST /api/v1/identity/agents:
  description: 注册 AI Agent
  auth: owner_token
  request:
    name: string
    framework: string
    capability_scope: string[]
    spending_authority_level: "L0 | L1 | L2 | L3"
  response:
    agent_id: uuid
    agent_credentials:
      api_key: string (encrypted)
      api_key_expires_at: datetime

POST /api/v1/identity/token:
  description: 获取访问令牌
  auth: api_key
  request:
    grant_type: "client_credentials"
  response:
    access_token: jwt
    token_type: "Bearer"
    expires_in: 3600

DELETE /api/v1/identity/agents/{agent_id}:
  description: 注销 Agent
  auth: owner_token + mfa
  response:
    status: "terminated"
    termination_effect: "all_active_orders_frozen"
```

#### Catalog Service

```yaml
# 商品服务接口
POST /api/v1/catalog/items:
  description: 上架能力商品
  auth: provider_token
  request:
    agentcard: object  # 完整 AgentCard JSON
  response:
    item_id: uuid
    status: "pending_verification"
    verification_estimate_minutes: 30

GET /api/v1/catalog/items/{item_id}:
  description: 获取商品详情
  auth: any_authenticated
  response:
    item: object  # 完整 AgentCard
    status: "active | pending | suspended | delisted"

PUT /api/v1/catalog/items/{item_id}:
  description: 更新商品信息
  auth: provider_token (owner of item)
  request:
    agentcard_patch: object  # AgentCard 变更部分
  response:
    item_id: uuid
    new_version: string
    status: "pending_verification"  # 更新需重新验证

DELETE /api/v1/catalog/items/{item_id}:
  description: 下架商品
  auth: provider_token (owner of item)
  response:
    item_id: uuid
    status: "delisted"
    active_subscriptions: integer  # 受影响的活跃订阅数
    grace_period_days: 7

GET /api/v1/catalog/items/{item_id}/agentcard:
  description: 获取机器可读 AgentCard
  auth: any_authenticated
  response:
    content_type: "application/json"
    schema_version: "1.0"
    body: object  # AgentCard JSON
```

#### Search Service

```yaml
# 搜索服务接口
POST /api/v1/search/capabilities:
  description: 搜索匹配的能力商品
  auth: agent_token
  request:
    query:
      task_description: string
      required_domains: string[]
      required_languages: string[]
      performance_constraints: object
      cost_constraints: object
      trust_score_min: integer
      delivery_preference: string
      item_type_filter: string[]
      sort_by: "relevance | trust_score | price_asc | price_desc"
    pagination:
      offset: integer
      limit: integer (max 20)
  response:
    total_matches: integer
    results: array[SearchResultItem]
    query_id: uuid  # 用于后续试用/购买关联

GET /api/v1/search/capabilities/recommendations:
  description: 获取个性化推荐（基于 Agent 历史和能力缺口分析）
  auth: agent_token
  request:
    current_task_context: string
    capability_gap: string[]
    budget_remaining: float
  response:
    recommendations: array[SearchResultItem]
    reason: string  # 推荐理由（机器可读）
```

#### Exchange Service

```yaml
# 交易服务接口
POST /api/v1/exchange/trials:
  description: 发起试用
  auth: agent_token
  request:
    item_id: uuid
    query_id: uuid  # 关联搜索请求
    trial_input: object  # 符合商品 input_schema 的输入
  response:
    trial_id: uuid
    sandbox_endpoint: string
    trial_constraints:
      max_calls: 5
      input_size_limit_pct: 10
      expires_at: datetime

POST /api/v1/exchange/trials/{trial_id}/execute:
  description: 执行试用调用
  auth: agent_token
  request:
    input: object
  response:
    output: object
    performance_metrics:
      latency_ms: integer
      tokens_used: integer
    trial_remaining_calls: integer

POST /api/v1/exchange/orders:
  description: 创建订单
  auth: agent_token
  request:
    item_id: uuid
    query_id: uuid
    pricing_plan: string  # "per_call" | "subscription:monthly" | ...
    quantity: integer
    delivery_params: object
    escrow_enabled: boolean
  response:
    order_id: uuid
    status: "created"
    authorization_required: "none | owner_notification | owner_approval | owner_confirmation"
    payment_required: object
    expires_at: datetime  # 30秒

POST /api/v1/exchange/orders/{order_id}/confirm:
  description: 确认订单（Agent 或 Owner）
  auth: agent_token | owner_token
  request:
    confirmation: boolean
  response:
    order_id: uuid
    status: "authorized | rejected | expired"

POST /api/v1/exchange/orders/{order_id}/effect-report:
  description: 回传使用效果
  auth: agent_token
  request:
    success: boolean
    effect_score: integer  # 1-5
    actual_latency_ms: integer
    actual_cost_cny: float
    declaration_accuracy: float  # 声明与实际的一致性 0-1
    notes_machine: string
  response:
    report_id: uuid
    trust_score_impact: float  # 预计信任评分变化

POST /api/v1/exchange/disputes:
  description: 发起争议
  auth: agent_token | owner_token | provider_token
  request:
    order_id: uuid
    dispute_type: "quality | sla_violation | unauthorized_charge | false_declaration"
    evidence: object
    requested_resolution: "refund | partial_refund | replacement | other"
  response:
    dispute_id: uuid
    status: "open"
    estimated_resolution_days: 7
    fund_status: "frozen"
```

#### Payment Service

```yaml
# 支付服务接口
POST /api/v1/payment/budget-pools:
  description: 创建预算池
  auth: owner_token + mfa
  request:
    currency: "CNY | USD | USDC"
    initial_balance: float
    limits: object
    recharge_policy: object
  response:
    budget_pool_id: uuid
    status: "active"

POST /api/v1/payment/budget-pools/{pool_id}/agents:
  description: 为 Agent 分配预算
  auth: owner_token
  request:
    agent_id: uuid
    daily_max: float
    per_call_max: float
  response:
    allocation_id: uuid
    status: "active"

GET /api/v1/payment/budget-pools/{pool_id}/status:
  description: 查询预算池状态
  auth: owner_token
  response:
    balance: float
    daily_spent: float
    weekly_spent: float
    monthly_spent: float
    active_allocations: integer
    pending_escrows: object[]

POST /api/v1/payment/settle/x402:
  description: x402 协议微支付结算
  auth: internal (系统内部调用)
  request:
    order_id: uuid
    amount: string  # USDC amount
    chain: "base | ethereum | solana"
    facilitator_id: uuid
    payment_header: string  # X-PAYMENT header value
  response:
    transaction_hash: string
    settlement_status: "confirmed | pending | failed"
    settlement_time_ms: integer

POST /api/v1/payment/settle/acp:
  description: ACP 协议支付结算
  auth: internal
  request:
    order_id: uuid
    spt_token: string  # Shared Payment Token
    amount: float
    currency: "CNY | USD"
  response:
    settlement_id: uuid
    settlement_status: "confirmed | pending | failed"

GET /api/v1/payment/transactions:
  description: 查询交易记录
  auth: owner_token | agent_token (own only) | provider_token (own only)
  request:
    filters:
      date_from: date
      date_to: date
      agent_id: uuid (owner only)
      item_id: uuid
      status: string
    pagination: object
  response:
    transactions: array[TransactionRecord]
    total_count: integer
```

#### Trust Service

```yaml
# 信任服务接口
GET /api/v1/trust/items/{item_id}/score:
  description: 获取商品信任评分
  auth: any_authenticated
  response:
    item_id: uuid
    trust_score: float (0-100)
    score_composition:
      benchmark_weight: float
      effect_reports_weight: float
      peer_reviews_weight: float
      certification_weight: float
    trend: "improving | stable | declining"
    last_updated: datetime

GET /api/v1/trust/providers/{provider_id}/score:
  description: 获取卖家信任评分
  auth: any_authenticated
  response:
    provider_id: uuid
    overall_rating: float (0-5)
    trust_score: float (0-100)
    listing_count: integer
    dispute_rate: float
    avg_effect_score: float

POST /api/v1/trust/certifications:
  description: 申请/签发认证
  auth: certifier_token
  request:
    item_id: uuid
    certification_level: "platform_certified | premium_certified"
    benchmark_results: object[]
    valid_until: date
  response:
    certification_id: uuid
    status: "active"
```

### 2.3 WebSocket 接口

```yaml
# 实时通知接口
WS /api/v1/ws/notifications:
  description: 实时事件推送
  auth: any_token
  events:
    - event: "order.created"
      payload: { order_id, item_id, amount }
    - event: "payment.completed"
      payload: { order_id, transaction_hash }
    - event: "trust.score_updated"
      payload: { item_id, old_score, new_score }
    - event: "authorization.required"
      payload: { order_id, agent_id, amount, required_level }
    - event: "budget.alert"
      payload: { pool_id, alert_type, current_balance }
    - event: "item.version_changed"
      payload: { item_id, old_version, new_version }
    - event: "dispute.opened"
      payload: { dispute_id, order_id, dispute_type }
```

### 2.4 MCP 网关接口

```yaml
# MCP 协议适配
GET /mcp/servers/{item_id}:
  description: 获取商品的 MCP Server 描述
  response:
    name: string
    version: string
    tools: array[MCPTool]
    resources: array[MCPResource]

POST /mcp/servers/{item_id}/tools/{tool_name}:
  description: 通过 MCP 调用商品能力
  auth: agent_token + x402 payment (if paid)
  request:
    arguments: object
  response:
    content: array[MCPContent]
    is_error: boolean
```

### 2.5 A2A 网关接口

```yaml
# A2A 协议适配
GET /a2a/agents/{item_id}/card:
  description: 获取商品的 A2A Agent Card
  response:
    agent_card: object  # A2A AgentCard format

POST /a2a/agents/{item_id}/tasks:
  description: 通过 A2A 提交任务
  auth: agent_token
  request:
    task_id: uuid
    message: object
  response:
    task: object
    status: "submitted"

GET /a2a/agents/{item_id}/tasks/{task_id}:
  description: 查询 A2A 任务状态
  auth: agent_token
  response:
    task: object
    status: "submitted | working | input_required | completed | failed | cancelled"
```

---

## 三、特性开关（Feature Flags）

### 3.1 开关定义

```yaml
feature_flags:
  # ===== 商品域 =====
  catalog_model_enabled:
    description: "模型类商品上架与交易"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  catalog_skill_enabled:
    description: "技能类商品上架与交易"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  catalog_expert_enabled:
    description: "专家类商品上架与交易"
    default: false
    rollout_pct: 0
    environments: [dev, staging]
    target_rollout: "Phase 2"

  catalog_compute_enabled:
    description: "算力类商品上架与交易"
    default: false
    rollout_pct: 0
    environments: [dev]
    target_rollout: "Phase 2"

  # ===== 交易域 =====
  exchange_trial_enabled:
    description: "试用沙箱功能"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  exchange_escrow_enabled:
    description: "担保交易机制"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  exchange_a2a_negotiation_enabled:
    description: "Agent 间 A2A 协商"
    default: false
    rollout_pct: 0
    environments: [dev]
    target_rollout: "Phase 3"

  exchange_auto_dispute_enabled:
    description: "SLA 违约自动争议"
    default: false
    rollout_pct: 0
    environments: [staging]
    target_rollout: "Phase 2"

  # ===== 支付域 =====
  payment_x402_enabled:
    description: "x402 微支付结算"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]
    config:
      supported_chains: ["base", "ethereum"]
      max_settlement_time_ms: 5000

  payment_acp_enabled:
    description: "ACP 共享支付令牌"
    default: false
    rollout_pct: 0
    environments: [dev, staging]
    target_rollout: "Phase 2"

  payment_ap2_enabled:
    description: "AP2 加密签名支付"
    default: false
    rollout_pct: 0
    environments: [dev]
    target_rollout: "Phase 2"

  payment_mpp_enabled:
    description: "MPP 机器支付协议"
    default: false
    rollout_pct: 0
    environments: []
    target_rollout: "Phase 3"

  payment_fiat_settlement_enabled:
    description: "法币结算通道"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  # ===== 信任域 =====
  trust_dynamic_score_enabled:
    description: "动态信任评分"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  trust_peer_review_enabled:
    description: "Agent 间口碑传播"
    default: false
    rollout_pct: 0
    environments: [dev]
    target_rollout: "Phase 3"

  trust_auto_delist_enabled:
    description: "信任评分低于阈值自动下架"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]
    config:
      delist_threshold: 30
      warning_threshold: 50

  # ===== 搜索域 =====
  search_capability_query_enabled:
    description: "AI 能力搜索协议"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  search_recommendation_enabled:
    description: "个性化能力推荐"
    default: false
    rollout_pct: 20
    environments: [staging]
    target_rollout: "Phase 2"

  # ===== 安全 =====
  security_sandbox_strict_mode:
    description: "沙箱严格模式（网络完全隔离）"
    default: true
    rollout_pct: 100
    environments: [prod]
    config:
      allow_network: false
      max_cpu_cores: 2
      max_memory_mb: 4096
      max_runtime_seconds: 60

  security_anomaly_detection_enabled:
    description: "消费异常检测"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  # ===== 冷启动 =====
  onboarding_zero_commission_enabled:
    description: "新卖家 90 天零佣金"
    default: true
    rollout_pct: 100
    environments: [dev, staging, prod]

  onboarding_huggingface_sync_enabled:
    description: "HuggingFace 商品自动同步"
    default: false
    rollout_pct: 0
    environments: [dev]
    target_rollout: "Phase 1 后期"
```

### 3.2 开关管理规则

```
FF-001: 特性开关变更需经平台运营审批
FF-002: 生产环境开关开启前必须在 staging 环境运行至少 7 天
FF-003: 灰度发布按 rollout_pct 百分比逐步推进，每次增幅不超过 20%
FF-004: 出现线上问题时，可在 5 分钟内关闭任何特性开关（无需审批）
FF-005: 已全量开启（rollout_pct=100）的开关，至少保留 30 天后才可移除
FF-006: 所有开关变更记录写入审计日志
```

---

## 四、外部服务集成配置

### 4.1 协议适配层

```yaml
protocol_adapters:
  mcp:
    enabled: true
    supported_versions: ["2024-11-05", "2025-11-25"]
    transport: ["sse", "streamable-http"]
    max_concurrent_sessions: 10000

  a2a:
    enabled: false
    supported_versions: ["0.3"]
    transport: ["http", "sse", "grpc"]
    max_concurrent_tasks: 5000

  x402:
    enabled: true
    facilitators:
      - id: "coinbase-cdp"
        chain: "base"
        fee_rate: 0
        max_amount_usdc: 1000
      - id: "payai-solana"
        chain: "solana"
        fee_rate: 0.001
        max_amount_usdc: 500
    supported_tokens:
      - "USDC" (EIP-3009, SPL)
      - "EURC" (EIP-3009)

  acp:
    enabled: false
    stripe_integration:
      mode: "test | live"
      webhook_url: "/api/v1/payment/webhooks/acp"

  ucp:
    enabled: false
    google_integration:
      project_id: "${GOOGLE_CLOUD_PROJECT}"
      merchant_center_id: "${MERCHANT_CENTER_ID}"
```

### 4.2 Agent 框架集成

```yaml
agent_framework_integrations:
  langchain:
    enabled: true
    package: "aimart-langchain"
    version: ">=0.1.0"
    integration_type: "tool_provider"
    config:
      search_tool: true
      purchase_tool: true
      trial_tool: true

  crewai:
    enabled: true
    package: "aimart-crewai"
    version: ">=0.1.0"
    integration_type: "capability_provider"
    config:
      auto_discovery: true
      budget_integration: true

  autogen:
    enabled: false
    target_rollout: "Phase 1 后期"

  dify:
    enabled: false
    target_rollout: "Phase 1 后期"

  coze:
    enabled: false
    target_rollout: "Phase 2"
```

---

# v2.0 落地补充：MVP 简化配置与 Codex 默认值

## 1. MVP profile

尽管正式架构可以包含 PostgreSQL、Redis、Kafka、ClickHouse、Elasticsearch，Codex 第一版实现必须支持本地最小运行。

```yaml
mvp_profile:
  enabled: true
  database: "sqlite"
  search: "in_memory_or_sqlite"
  cache: "disabled"
  kafka: "disabled"
  clickhouse: "disabled"
  elasticsearch: "disabled"
  object_storage: "local"
  real_payment: false
  mock_payment: true
  mcp_server: false
  x402: false
  acp: false
  ap2: false
  a2a: false
```

## 2. Agent 成熟度配置

```yaml
agent_maturity:
  enabled: true
  default_level: "M0"
  sandbox_required_for_new_agents: true
  min_level_for_quote: "M1"
  min_level_for_low_risk_execution: "M2"
  min_level_for_medium_risk_execution: "M3"
  high_risk_auto_execution_allowed: false
```

## 3. 合规配置

```yaml
compliance:
  cross_border_data_default_allowed: false
  local_storage_required_for_sensitive_data: true
  block_unknown_data_region: true
  pipl_mode: true
  gdpr_mode: false
  compute_derivatives_allowed: false
```

## 4. Feature flags 默认值

```yaml
feature_flags:
  real_payment: false
  mock_payment: true
  agent_auto_purchase: false
  agent_low_risk_auto_execution: false
  high_risk_auto_execution: false
  mcp_server: false
  a2a_network: false
  x402_payment: false
  acp_payment: false
  ap2_payment: false
  compute_derivatives: false
  cross_border_data_trade: false
  audit_log: true
  agentcard_validation: true
  rules_engine: true
```

