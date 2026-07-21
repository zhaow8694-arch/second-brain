# AIMart 配置文件：环境、接口、特性开关

> 建议实际落地文件名：  
> - `config/app_config.yaml`  
> - `config/feature_flags.yaml`  
> - `.env.example`  
> 本 Markdown 用途：定义 AIMart MVP 的基础运行配置、外部接口配置、AI 服务配置、支付配置、日志配置和功能开关。  
> 核心目标：让系统可以在 dev / staging / production 多环境运行，避免把环境变量和密钥写死在代码中。

---

## 1. 这个文件解决什么问题

AIMart 涉及多个系统：

```text
Web 前台
商家后台
平台后台
REST API
Agent Gateway
AI 需求诊断
搜索系统
支付结算
对象存储
审计日志
规则引擎
```

如果没有统一配置文件，就会出现：

```text
数据库地址写死
支付开关混乱
AI Agent 功能无法灰度
MCP 接口和 REST 接口混在一起
开发环境误扣真实费用
日志级别不统一
密钥泄露
```

所以配置文件是系统工程化落地的基础。

---

## 2. AI 编码指令

让 AI 工程助手根据本文件生成实际项目文件时，应遵守：

```text
1. 生成 config/app_config.yaml。
2. 生成 config/feature_flags.yaml。
3. 生成 .env.example。
4. 敏感信息只能通过环境变量读取，不允许写入 YAML 明文。
5. dev 环境默认关闭真实支付。
6. Agent 自动付款功能默认关闭。
7. 所有配置读取需要有默认值和校验。
```

---

## 3. app_config.yaml 模板

```yaml
version: "0.1"
project: "AIMart"
file_type: "app_config"

environment:
  name: "dev"
  debug: true
  timezone: "Asia/Shanghai"
  default_currency: "CNY"

server:
  host: "0.0.0.0"
  port: 8000
  public_base_url: "http://localhost:8000"
  api_prefix: "/api/v1"
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:3000"
      - "http://localhost:5173"

database:
  type: "postgresql"
  host_env: "AIMART_DB_HOST"
  port_env: "AIMART_DB_PORT"
  database_env: "AIMART_DB_NAME"
  username_env: "AIMART_DB_USER"
  password_env: "AIMART_DB_PASSWORD"
  pool:
    min_size: 2
    max_size: 10

cache:
  type: "redis"
  enabled: false
  url_env: "AIMART_REDIS_URL"

object_storage:
  provider: "local"
  local_path: "./storage"
  max_upload_size_mb: 100
  allowed_file_types:
    - "pdf"
    - "docx"
    - "xlsx"
    - "csv"
    - "txt"
    - "png"
    - "jpg"
    - "jpeg"
    - "json"

search:
  mode: "basic"
  engines:
    keyword:
      enabled: true
    vector:
      enabled: false
      provider: "local"
      embedding_model_env: "AIMART_EMBEDDING_MODEL"
  indexes:
    capabilities: "aimart_capabilities"
    requirements: "aimart_requirements"
    sellers: "aimart_sellers"

ai_services:
  enabled: true
  default_provider: "openai_compatible"
  llm:
    provider_env: "AIMART_LLM_PROVIDER"
    base_url_env: "AIMART_LLM_BASE_URL"
    api_key_env: "AIMART_LLM_API_KEY"
    model_env: "AIMART_LLM_MODEL"
    timeout_seconds: 60
  use_cases:
    requirement_diagnosis:
      enabled: true
      max_tokens: 4000
    capability_card_assist:
      enabled: true
      max_tokens: 4000
    matching:
      enabled: true
      max_candidates: 20
    risk_detection:
      enabled: true

agent_gateway:
  enabled: true
  api_key_required: true
  default_permission_level: "L1"
  max_requests_per_minute: 60
  require_trace_id: true
  endpoints:
    search_capabilities: "/api/v1/agent/capabilities/search"
    get_capability_detail: "/api/v1/agent/capabilities/{capability_id}"
    compare_capabilities: "/api/v1/agent/capabilities/compare"
    request_quote: "/api/v1/agent/quotes/request"
    submit_feedback: "/api/v1/agent/feedback"
  mcp:
    enabled: false
    server_name: "aimart-mcp"
    tools:
      - "search_capabilities"
      - "get_capability_detail"
      - "compare_capabilities"
      - "request_quote"
      - "submit_feedback"

payments:
  enabled: false
  mode: "mock"
  real_payment_allowed_in_envs:
    - "production"
  providers:
    mock:
      enabled: true
    stripe:
      enabled: false
      secret_key_env: "STRIPE_SECRET_KEY"
    alipay:
      enabled: false
      app_id_env: "ALIPAY_APP_ID"
    wechat_pay:
      enabled: false
      mch_id_env: "WECHAT_PAY_MCH_ID"
  escrow:
    enabled: true
    mock_in_dev: true
  wallet:
    enabled: true
    allow_negative_balance: false

rules_engine:
  enabled: true
  boundary_file: "config/boundaries.yaml"
  constraints_file: "config/constraints.yaml"
  agentcard_schema_file: "schemas/agentcard.schema.json"
  reload_on_change: true

security:
  jwt_secret_env: "AIMART_JWT_SECRET"
  password_hash: "bcrypt"
  require_email_verification: false
  require_organization_verification_for_enterprise_orders: true
  session_timeout_minutes: 120
  api_key_prefix: "ak_aimart_"
  rate_limiting:
    enabled: true
    default_per_minute: 120
    agent_per_minute: 60
  data_masking:
    enabled: true
    mask_email: true
    mask_phone: true
    mask_api_keys: true

logging:
  level: "INFO"
  format: "json"
  audit_enabled: true
  audit_log_path: "./logs/audit.ndjson"
  app_log_path: "./logs/app.ndjson"
  security_log_path: "./logs/security.ndjson"
  include_trace_id: true
  include_actor_id: true

notifications:
  email:
    enabled: false
    provider: "smtp"
    smtp_host_env: "SMTP_HOST"
    smtp_user_env: "SMTP_USER"
    smtp_password_env: "SMTP_PASSWORD"
  webhook:
    enabled: true
    retry_count: 3

commission:
  seller_self_brought_customer:
    default_rate: 0.05
  platform_matched_customer:
    default_rate: 0.15
  api_usage:
    default_rate: 0.10
```

---

## 4. feature_flags.yaml 模板

```yaml
version: "0.1"
project: "AIMart"
file_type: "feature_flags"

features:
  seller_onboarding:
    enabled: true
    description: "商家入驻"

  capability_listing:
    enabled: true
    description: "能力商品上架"

  agentcard_validation:
    enabled: true
    description: "AgentCard Schema 校验"

  buyer_requirement_posting:
    enabled: true
    description: "买家发布需求"

  ai_requirement_diagnosis:
    enabled: true
    description: "AI 需求诊断"

  quote_system:
    enabled: true
    description: "报价系统"

  order_system:
    enabled: true
    description: "订单系统"

  escrow_payment:
    enabled: true
    description: "担保交易"
    rollout: "mock_only"

  real_payment:
    enabled: false
    description: "真实支付"
    rollout: "production_only"

  milestone_delivery:
    enabled: true
    description: "里程碑交付"

  review_system:
    enabled: true
    description: "评价系统"

  agent_gateway:
    enabled: true
    description: "AI Agent 接口"

  agent_auto_purchase:
    enabled: false
    description: "AI Agent 自动购买"
    reason: "MVP 阶段必须关闭，等待预算、权限、审计成熟"

  agent_low_risk_auto_execution:
    enabled: false
    description: "AI Agent 自动调用低风险能力"
    reason: "初期先做搜索、比较、报价请求"

  mcp_server:
    enabled: false
    description: "MCP Server 接入"

  channel_commission:
    enabled: false
    description: "渠道分佣"

  vector_search:
    enabled: false
    description: "向量搜索"

  sandbox_trial:
    enabled: false
    description: "试用沙箱"

  risk_auto_detection:
    enabled: true
    description: "AI 辅助风险识别"

  audit_log:
    enabled: true
    description: "审计日志"

  security_event_alert:
    enabled: true
    description: "安全事件告警"
```

---

## 5. .env.example 模板

```bash
# AIMart Environment
AIMART_ENV=dev
AIMART_DEBUG=true

# Server
AIMART_PUBLIC_BASE_URL=http://localhost:8000

# Database
AIMART_DB_HOST=localhost
AIMART_DB_PORT=5432
AIMART_DB_NAME=aimart
AIMART_DB_USER=aimart_user
AIMART_DB_PASSWORD=change_me

# Redis
AIMART_REDIS_URL=redis://localhost:6379/0

# Security
AIMART_JWT_SECRET=change_me_to_a_long_random_secret

# LLM / AI Service
AIMART_LLM_PROVIDER=openai_compatible
AIMART_LLM_BASE_URL=https://api.example.com/v1
AIMART_LLM_API_KEY=replace_with_key
AIMART_LLM_MODEL=gpt-4.1-mini
AIMART_EMBEDDING_MODEL=text-embedding-3-small

# Payment Providers
STRIPE_SECRET_KEY=
ALIPAY_APP_ID=
WECHAT_PAY_MCH_ID=

# Email
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
```

---

## 6. 配置加载最小验收标准

```text
1. 系统启动时加载 app_config.yaml 和 feature_flags.yaml。
2. 缺少必要环境变量时，启动失败并给出清晰错误。
3. dev 环境真实支付必须关闭。
4. agent_auto_purchase 默认关闭。
5. audit_log 默认开启。
6. Agent Gateway 必须强制 API Key。
7. 所有日志必须包含 trace_id。
8. 所有密钥只能从环境变量读取。
```

---

## 7. 给 AI 编码助手的提示词

```text
请根据本 Markdown 生成：
1. config/app_config.yaml
2. config/feature_flags.yaml
3. .env.example
4. 配置加载模块 config_loader.py

要求：
- 支持 dev/staging/production 三个环境。
- 敏感字段只从环境变量读取。
- 启动时校验必要配置。
- feature_flags 控制功能开关。
- dev 环境禁止真实支付。
- agent_auto_purchase 默认关闭。
```
