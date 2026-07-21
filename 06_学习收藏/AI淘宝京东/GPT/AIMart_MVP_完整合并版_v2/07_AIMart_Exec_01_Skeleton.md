<!-- AIMart 完整合并版 v2：保留原始文件内容，并追加 Codex MVP 落地补充。生成日期：2026-06-06 -->

# AIMart 工程执行文件 01：项目骨架

> Codex 执行起点：从此文件开始搭建项目结构、初始化依赖、配置基础设施

---

## 一、技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| 语言 | Python | 3.12 | 主服务 |
| 语言 | TypeScript | 5.4 | MCP/A2A 网关 |
| Web 框架 | FastAPI | 0.111 | 异步高性能 |
| 数据库 | PostgreSQL | 16 | 主存储 |
| 缓存 | Redis | 7 | 会话/限流/缓存 |
| 搜索 | Elasticsearch | 8 | 能力搜索索引 |
| 消息队列 | Kafka | 3.7 | 事件驱动 |
| 审计存储 | ClickHouse | 24 | 日志分析 |
| 对象存储 | MinIO/S3 | — | 模型权重/技能包 |
| 容器 | Docker + Compose | — | 开发环境 |
| 编排 | Kubernetes | — | 生产环境 |
| 链上交互 | web3.py | 6.x | x402 结算 |
| AI 框架集成 | langchain | 0.2+ | Agent 框架适配 |

---

## 二、项目目录结构

```
aimart/
├── README.md
├── pyproject.toml                    # 项目依赖与构建配置
├── docker-compose.yml                # 开发环境编排
├── .env.example                      # 环境变量模板
├── Makefile                          # 常用命令快捷入口
│
├── schemas/                          # JSON Schema 定义
│   ├── agentcard_base_v1.json        # AgentCard 基础层 Schema
│   ├── agentcard_model_v1.json       # 模型类扩展 Schema
│   ├── agentcard_skill_v1.json       # 技能类扩展 Schema
│   ├── agentcard_expert_v1.json      # 专家类扩展 Schema
│   ├── agentcard_compute_v1.json     # 算力类扩展 Schema
│   ├── search_query_v1.json          # 搜索请求 Schema
│   ├── effect_report_v1.json         # 效果回传 Schema
│   └── audit_log_v1.json             # 审计日志 Schema
│
├── migrations/                       # 数据库迁移
│   ├── versions/
│   │   ├── 001_initial.py
│   │   ├── 002_catalog.py
│   │   ├── 003_exchange.py
│   │   ├── 004_payment.py
│   │   ├── 005_trust.py
│   │   └── 006_audit.py
│   └── env.py
│
├── src/
│   ├── aimart/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置加载（对应 AIMart_Config.md）
│   │   ├── dependencies.py           # 依赖注入
│   │   │
│   │   ├── identity/                 # 身份域
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # API 路由
│   │   │   ├── service.py            # 业务逻辑
│   │   │   ├── models.py             # SQLAlchemy 模型
│   │   │   ├── schemas.py            # Pydantic 请求/响应模型
│   │   │   └── auth.py               # 认证与授权
│   │   │
│   │   ├── catalog/                  # 商品域
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   └── validator.py          # AgentCard 校验（对应执行文件03）
│   │   │
│   │   ├── search/                   # 搜索域
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── indexer.py            # ES 索引管理
│   │   │   ├── matcher.py            # 能力匹配算法
│   │   │   └── schemas.py
│   │   │
│   │   ├── exchange/                 # 交易域
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── sandbox.py            # 试用沙箱管理
│   │   │   └── escrow.py             # 担保交易逻辑
│   │   │
│   │   ├── payment/                  # 支付域
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── budget.py             # 预算池管理
│   │   │   ├── authorization.py      # 分层授权逻辑
│   │   │   ├── anomaly.py            # 消费异常检测
│   │   │   ├── settle_x402.py        # x402 结算适配
│   │   │   └── settle_acp.py         # ACP 结算适配
│   │   │
│   │   ├── trust/                    # 信任域
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── scorer.py             # 动态评分引擎
│   │   │   └── certification.py       # 认证管理
│   │   │
│   │   ├── audit/                    # 审计域
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # 审计查询 API
│   │   │   ├── logger.py             # 审计日志写入（对应执行文件04）
│   │   │   ├── hashchain.py          # 哈希链机制
│   │   │   ├── models.py             # ClickHouse 模型
│   │   │   └── schemas.py
│   │   │
│   │   ├── rules/                    # 规则引擎
│   │   │   ├── __init__.py
│   │   │   ├── engine.py             # 规则引擎核心（对应执行文件02）
│   │   │   ├── trading_rules.py      # 交易规则
│   │   │   ├── budget_rules.py       # 预算规则
│   │   │   ├── security_rules.py     # 安全规则
│   │   │   ├── sla_rules.py          # SLA 规则
│   │   │   └── registry.py           # 规则注册表
│   │   │
│   │   ├── protocols/                # 协议适配层
│   │   │   ├── __init__.py
│   │   │   ├── mcp_gateway.py        # MCP 网关
│   │   │   ├── a2a_gateway.py        # A2A 网关
│   │   │   └── x402_adapter.py       # x402 适配器
│   │   │
│   │   └── integrations/             # Agent 框架集成
│   │       ├── __init__.py
│   │       ├── langchain_plugin/     # LangChain 集成包
│   │       │   ├── __init__.py
│   │       │   ├── search_tool.py
│   │       │   ├── purchase_tool.py
│   │       │   └── trial_tool.py
│   │       └── crewai_plugin/        # CrewAI 集成包
│   │           ├── __init__.py
│   │           ├── capability_provider.py
│   │           └── budget_integration.py
│
├── gateway/                          # TypeScript 网关服务
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── mcp/                      # MCP 协议服务
│   │   │   ├── server.ts
│   │   │   ├── handlers.ts
│   │   │   └── transport.ts
│   │   └── a2a/                      # A2A 协议服务
│   │       ├── server.ts
│   │       ├── agent_card.ts
│   │       └── task_manager.ts
│   └── Dockerfile
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_rules_engine.py
│   │   ├── test_agentcard_validator.py
│   │   ├── test_budget_authorization.py
│   │   ├── test_trust_scorer.py
│   │   └── test_audit_hashchain.py
│   ├── integration/
│   │   ├── test_search_flow.py
│   │   ├── test_exchange_flow.py
│   │   ├── test_payment_flow.py
│   │   └── test_audit_trace.py
│   └── e2e/
│       ├── test_agent_purchase_journey.py
│       └── test_dispute_resolution.py
│
├── scripts/
│   ├── seed_db.py                    # 种子数据
│   ├── generate_schemas.py           # 从 Schema 文件生成代码
│   └── load_test.py                  # 压测脚本
│
└── deploy/
    ├── Dockerfile                    # Python 主服务
    ├── k8s/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── secrets.yaml
    └── terraform/                    # 基础设施即代码
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## 三、pyproject.toml

```toml
[project]
name = "aimart"
version = "1.0.0"
description = "AIMart - AI-first Capability Marketplace Platform"
requires-python = ">=3.12"
dependencies = [
    # Web
    "fastapi>=0.111",
    "uvicorn[standard]>=0.30",
    "python-multipart>=0.0.9",

    # Database
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",

    # Cache
    "redis[hiredis]>=5.0",

    # Search
    "elasticsearch[async]>=8.13",

    # Messaging
    "aiokafka>=0.10",

    # ClickHouse
    "clickhouse-driver>=0.2",

    # Validation
    "pydantic>=2.7",
    "jsonschema>=4.22",

    # Auth
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",

    # HTTP
    "httpx>=0.27",

    # Blockchain
    "web3>=6.19",

    # Observability
    "prometheus-client>=0.20",
    "opentelemetry-api>=1.25",
    "opentelemetry-sdk>=1.25",
    "opentelemetry-instrumentation-fastapi>=0.46",

    # Utils
    "structlog>=24.1",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "ruff>=0.4",
    "mypy>=1.10",
    "pre-commit>=3.7",
]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
strict = true
```

---

## 四、docker-compose.yml

```yaml
version: "3.9"

services:
  # Python 主服务
  aimart-api:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    ports:
      - "8080:8080"
    env_file: .env
    depends_on:
      - postgres
      - redis
      - elasticsearch
      - kafka
      - clickhouse
    volumes:
      - ./src:/app/src
    command: uvicorn aimart.main:app --host 0.0.0.0 --port 8080 --reload

  # TypeScript 网关
  aimart-gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    ports:
      - "8081:8081"
    env_file: .env
    depends_on:
      - aimart-api

  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: aimart_dev
      POSTGRES_USER: aimart
      POSTGRES_PASSWORD: aimart_dev_pwd
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  elasticsearch:
    image: elasticsearch:8.13.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - esdata:/usr/share/elasticsearch/data

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  clickhouse:
    image: clickhouse/clickhouse-server:24
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - chdata:/var/lib/clickhouse

  minio:
    image: minio/minio
    ports:
      - "9001:9001"
      - "9000:9000"
    environment:
      MINIO_ROOT_USER: aimart
      MINIO_ROOT_PASSWORD: aimart_dev_pwd
    command: server /data --console-address ":9001"
    volumes:
      - miniodata:/data

volumes:
  pgdata:
  esdata:
  chdata:
  miniodata:
```

---

## 五、FastAPI 应用入口

```python
# src/aimart/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from aimart.config import settings
from aimart.identity.router import router as identity_router
from aimart.catalog.router import router as catalog_router
from aimart.search.router import router as search_router
from aimart.exchange.router import router as exchange_router
from aimart.payment.router import router as payment_router
from aimart.trust.router import router as trust_router
from aimart.audit.router import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化连接，关闭时释放资源"""
    # 启动
    from aimart.dependencies import init_db, init_redis, init_es, init_kafka, init_clickhouse

    await init_db()
    await init_redis()
    await init_es()
    await init_kafka()
    await init_clickhouse()

    yield

    # 关闭
    from aimart.dependencies import close_db, close_redis, close_kafka, close_clickhouse

    await close_db()
    await close_redis()
    await close_kafka()
    await close_clickhouse()


app = FastAPI(
    title="AIMart API",
    version="1.0.0",
    description="AI-first Capability Marketplace Platform",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security_cors_allowed_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=86400,
)

# 路由注册
app.include_router(identity_router, prefix="/api/v1/identity", tags=["Identity"])
app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
app.include_router(exchange_router, prefix="/api/v1/exchange", tags=["Exchange"])
app.include_router(payment_router, prefix="/api/v1/payment", tags=["Payment"])
app.include_router(trust_router, prefix="/api/v1/trust", tags=["Trust"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

---

## 六、配置加载

```python
# src/aimart/config.py

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """从环境变量加载配置，对应 AIMart_Config.md 全局环境变量"""

    # Platform
    platform_environment: str = "dev"
    platform_base_url: str = "http://localhost:8080"
    platform_api_version: str = "v1"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "aimart_dev"
    db_user: str = "aimart"
    db_password: str = "aimart_dev_pwd"
    db_max_connections: int = 100

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl_default: int = 3600

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    # Elasticsearch
    es_host: str = "localhost"
    es_port: int = 9200

    @property
    def es_url(self) -> str:
        return f"http://{self.es_host}:{self.es_port}"

    # Kafka
    kafka_brokers: str = "localhost:9092"

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123

    # Security
    security_tls_min_version: str = "1.3"
    security_jwt_algorithm: str = "RS256"
    security_jwt_access_token_ttl_minutes: int = 60
    security_jwt_refresh_token_ttl_days: int = 30
    security_jwt_issuer: str = "aimart.dev"
    security_jwt_public_key: Optional[str] = None
    security_jwt_private_key: Optional[str] = None
    security_cors_allowed_origins: list[str] = ["https://aimart.dev", "https://*.aimart.dev"]
    security_rate_limit_global_rps: int = 10000
    security_rate_limit_per_agent_rps: int = 100
    security_rate_limit_per_provider_rps: int = 500

    # x402
    x402_enabled: bool = True
    x402_facilitator_base_url: str = "https://facilitator.example.com"
    x402_supported_chains: list[str] = ["base", "ethereum"]
    x402_max_settlement_time_ms: int = 5000

    # Feature Flags
    ff_catalog_model_enabled: bool = True
    ff_catalog_skill_enabled: bool = True
    ff_catalog_expert_enabled: bool = False
    ff_catalog_compute_enabled: bool = False
    ff_exchange_trial_enabled: bool = True
    ff_exchange_escrow_enabled: bool = True
    ff_exchange_a2a_negotiation_enabled: bool = False
    ff_payment_x402_enabled: bool = True
    ff_payment_acp_enabled: bool = False
    ff_payment_fiat_settlement_enabled: bool = True
    ff_trust_dynamic_score_enabled: bool = True
    ff_trust_auto_delist_enabled: bool = True
    ff_trust_auto_delist_threshold: int = 30
    ff_search_capability_query_enabled: bool = True
    ff_security_sandbox_strict_mode: bool = True
    ff_security_anomaly_detection_enabled: bool = True
    ff_onboarding_zero_commission_enabled: bool = True

    model_config = {"env_prefix": "AIMART_", "env_file": ".env"}


settings = Settings()
```

---

## 七、数据库迁移起始

```python
# migrations/versions/001_initial.py

"""Initial schema - participants and agents

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None


def upgrade() -> None:
    # Participants (Owner / Provider / Certifier / Facilitator)
    op.create_table(
        "participants",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False),  # owner|provider|certifier|facilitator
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("jurisdiction", sa.String(10), nullable=False),
        sa.Column("kyc_status", sa.String(20), default="pending"),
        sa.Column("risk_level", sa.String(10), default="low"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # AI Agents
    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_id", sa.UUID(), sa.ForeignKey("participants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("capability_scope", postgresql.JSONB(), default=[]),
        sa.Column("trust_score", sa.Float(), default=50.0),
        sa.Column("spending_authority", sa.String(5), default="L0"),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("api_key_hash", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_active_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"])
    op.create_index("ix_agents_status", "agents", ["status"])


def downgrade() -> None:
    op.drop_table("agents")
    op.drop_table("participants")
```

---

## 八、Makefile

```makefile
.PHONY: help setup dev test lint migrate seed clean

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup
	python -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"
	cp .env.example .env
	pre-commit install

dev: ## Start development environment
	docker-compose up -d
	. .venv/bin/activate && uvicorn aimart.main:app --reload --port 8080

test: ## Run tests
	. .venv/bin/activate && pytest -v --cov=aimart tests/

lint: ## Lint and type check
	. .venv/bin/activate && ruff check src/ && mypy src/

migrate: ## Run database migrations
	. .venv/bin/activate && alembic upgrade head

seed: ## Load seed data
	. .venv/bin/activate && python scripts/seed_db.py

clean: ## Clean up
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache
```

---

## 九、Codex 执行指令

```
1. 创建上述目录结构（mkdir -p 所有路径）
2. 写入 pyproject.toml、docker-compose.yml、Makefile、.env.example
3. 写入 src/aimart/main.py 和 src/aimart/config.py
4. 写入 migrations/versions/001_initial.py
5. 将 schemas/ 目录下的 JSON Schema 文件从 AIMart_Capability.md 提取生成
6. 为每个域（identity/catalog/search/exchange/payment/trust/audit）创建 router.py、service.py、models.py、schemas.py 骨架
7. 运行 docker-compose up -d 启动基础设施
8. 运行 pip install -e ".[dev]" 安装依赖
9. 运行 alembic upgrade head 创建数据库表
10. 运行 pytest tests/ 验证项目可启动
```

---

# v2.0 Codex 执行补充：MVP 骨架简化原则

## 1. 不要过度工程化

如果原文档中提到 Kafka、ClickHouse、Elasticsearch、Kubernetes 等重型组件，Codex 第一版可以只保留接口抽象，不需要实际接入。

MVP 默认：

```text
SQLite 或内存仓储
本地 NDJSON 审计日志
本地 JSON/YAML 配置
Mock Payment
FastAPI
pytest
```

## 2. 必须生成的自审文件

```text
docs/ASSUMPTIONS.md
docs/IMPLEMENTATION_REPORT.md
docs/SELF_REVIEW.md
docs/API_USAGE.md
```

## 3. 最小可运行要求

```text
uvicorn app.main:app --reload
pytest
```

这两个命令必须能运行。

