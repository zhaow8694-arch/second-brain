# AGENTS.md — AIMart Project Context for Trae AI

> This file provides comprehensive context about the AIMart project so that
> Trae's AI assistant can understand the codebase, make informed decisions,
> and produce code that is consistent with the project's architecture and
> conventions.

---

## 1. Project Overview

**AIMart** is an AI marketplace platform where **AI Agents (not humans) are the primary customers**. It is the "AI capability marketplace" — a trading infrastructure that lets AI agents autonomously discover, evaluate, purchase, and consume AI capabilities (models, skills, experts, compute) without human involvement in the transaction loop.

The platform does **not** produce AI capabilities itself. Like Taobao, it is a two-sided marketplace: capability providers list their offerings, and AI agents (acting on behalf of their owners) search, trial, purchase, and consume them. The entire purchase flow — from need detection through payment settlement — is designed for machine-to-machine interaction.

### Key Differentiators from Existing Platforms

| Dimension | Human Marketplaces (HuggingFace, etc.) | AIMart |
|-----------|---------------------------------------|--------|
| Product descriptions | Natural language docs | Structured JSON (AgentCard) |
| Search | Keywords + filters | Intent-based CapabilityNeed protocol |
| Decision | Human judgment | AI scoring + sandbox trial |
| Payment | Register → bind card → confirm | M2M auto-settlement (x402/ACP) |
| Reviews | Text + star ratings | Structured effect reports + quality metrics |
| Support | Human/chatbot | Agent-to-Agent negotiation (A2A) |

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.12 |
| Framework | FastAPI | ≥0.111 |
| ORM | SQLAlchemy (async) | ≥2.0 |
| DB Driver | asyncpg | ≥0.29 |
| Primary DB | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Message Queue | Apache Kafka | 3.7 (via Confluent 7.6.0) |
| Analytics DB | ClickHouse | 24 |
| Search Engine | Elasticsearch | 8.13 |
| Object Storage | MinIO | latest |
| Migrations | Alembic | ≥1.13 |
| Validation | Pydantic v2 | ≥2.7 |
| Settings | pydantic-settings | ≥2.2 |
| Auth | python-jose + argon2-cffi + pyotp | — |
| Logging | structlog | ≥24.1 |
| HTTP Client | httpx | ≥0.27 |
| Containerization | Docker + Docker Compose | — |
| Linting | Ruff | ≥0.4 |
| Type Checking | mypy (strict) | ≥1.10 |

---

## 3. Architecture

AIMart follows **Domain-Driven Design (DDD)** with 7 core domains, a rules engine, and protocol adapters.

### 3.1 Domain Map

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│                  (aimart.main)                       │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ Identity │ Catalog  │ Search   │ Exchange │ Payment │
│          │          │          │          │         │
│ OAuth2   │ AgentCard│ Need-    │ Order    │ Budget  │
│ API Key  │ Validator│ Match    │ Escrow   │ x402    │
│ MFA      │ Version  │ Index    │ Sandbox  │ ACP     │
├──────────┼──────────┼──────────┤          │ Auth    │
│  Trust   │  Audit   │  Rules   │          │ Anomaly │
│ Scoring  │ HashChain│ Engine   │          │         │
│ Eval     │ Logger   │ Registry │          │         │
└──────────┴──────────┴──────────┴──────────┴─────────┘
         ▲                                  ▲
         │         Protocol Adapters         │
    ┌────┴────┬──────────┬──────────┬───────┴───┐
    │   MCP   │   A2A    │   x402   │ Integr.   │
    │ Gateway │ Gateway  │ Adapter  │ LangChain  │
    │         │          │          │ CrewAI    │
    └─────────┴──────────┴──────────┴───────────┘
```

### 3.2 Domain Summaries

| Domain | Path | Responsibility |
|--------|------|---------------|
| **Identity** | `domains/identity/` | OAuth2, API key management, MFA, agent registration, JWT auth |
| **Catalog** | `domains/catalog/` | AgentCard CRUD, validation, versioning, listing management |
| **Search** | `domains/search/` | CapabilityNeed protocol, semantic matching, Elasticsearch indexing |
| **Exchange** | `domains/exchange/` | Order lifecycle, escrow transactions, sandbox trial, effect confirmation |
| **Payment** | `domains/payment/` | Budget pools, layered authorization (L0–L3), x402 crypto settlement, ACP fiat settlement, anomaly detection |
| **Trust** | `domains/trust/` | Dynamic trust scoring, effect evaluation, certification tracking |
| **Audit** | `domains/audit/` | Hash-chain audit logging, immutable log storage in ClickHouse |
| **Rules** | `domains/rules/` | Trading rule engine, rule registry, configurable business rules |

### 3.3 Protocol Adapters

| Adapter | Path | Protocol |
|---------|------|----------|
| MCP Gateway | `protocols/mcp_gateway.py` | Model Context Protocol (SSE streaming) — exposes AIMart as MCP tools |
| A2A Gateway | `protocols/a2a_gateway.py` | Agent-to-Agent — inter-agent messaging and negotiation |
| x402 Adapter | `protocols/x402_adapter.py` | x402 HTTP 402 Payment — M2M crypto micro-payments |

### 3.4 Integration Plugins

| Plugin | Path | Framework |
|--------|------|-----------|
| Search Tool | `integrations/langchain_plugin/search_tool.py` | LangChain BaseTool |
| Purchase Tool | `integrations/langchain_plugin/purchase_tool.py` | LangChain BaseTool |
| Capability Provider | `integrations/crewai_plugin/capability_provider.py` | CrewAI tool provider |

---

## 4. Key Design Decisions

### 4.1 AgentCard — Machine-Readable Product Descriptions

Every capability listed on AIMart must provide an **AgentCard**: a structured JSON document that declares capabilities, performance benchmarks, pricing, delivery methods, and trust information. Unlike HuggingFace model cards (natural language), AgentCards are designed for machine parsing and programmatic comparison.

Schema version: `1.0` — see `docs/AIMart_Capability.md` for full specification.

### 4.2 CapabilityNeed Search Protocol

Agents express their needs as structured `CapabilityNeed` objects rather than keyword queries. A need specifies: type (model/skill/expert/compute), domain tags, optional task description, price ceiling, and minimum trust score. The search engine performs semantic matching and returns ranked results.

### 4.3 Escrow Transactions with Effect-Based Release

Purchases follow an escrow pattern:
1. Agent places order → funds frozen in escrow
2. Capability delivered → agent trials in sandbox
3. Agent submits structured effect report
4. If effect ≥ threshold → funds released to provider
5. If effect < threshold → dispute / A2A negotiation / refund

### 4.4 Layered Authorization (L0–L3)

| Level | Amount Range | Auth Method | Timeout |
|-------|-------------|-------------|---------|
| L0 — Full auto | ≤ ¥0.01/call | Agent decides | — |
| L1 — Post-hoc notify | ¥0.01 – ¥1.00 | Agent decides, owner notified | — |
| L2 — Pre-approval | ¥1.00 – ¥100 | Owner authorizes | 30 min auto-reject |
| L3 — Human confirm | > ¥100 | Owner personally confirms | 1 hr auto-reject |

### 4.5 Dual Settlement

- **x402** — HTTP 402-based crypto micro-payments for small, high-frequency transactions (USDC on Base/Arbitrum)
- **ACP (Agent Commerce Protocol)** — fiat settlement via traditional payment rails for larger transactions

### 4.6 Hash-Chain Audit Logging

Every significant action generates an audit log entry. Each entry contains the SHA-256 hash of the previous entry, forming an append-only hash chain. Tampering with any entry breaks the chain and is immediately detectable. Logs are stored in ClickHouse for efficient analytical queries.

---

## 5. Directory Structure

```
aimart/
├── AGENTS.md                 ← This file
├── Dockerfile                ← Multi-stage Docker build
├── Makefile                  ← Common dev commands
├── alembic.ini               ← Alembic configuration
├── docker-compose.yml        ← Full dev stack
├── pyproject.toml            ← Project metadata & dependencies
├── docs/                     ← Design documents
│   ├── AIMart_Whitepaper.md
│   ├── AIMart_Boundary.md
│   ├── AIMart_Constraints.md
│   ├── AIMart_Capability.md
│   ├── AIMart_Config.md
│   └── AIMart_Audit.md
├── migrations/
│   ├── env.py                ← Async Alembic env
│   └── versions/             ← Migration files
└── src/
    └── aimart/
        ├── __init__.py
        ├── main.py           ← FastAPI app + lifespan
        ├── config.py         ← pydantic-settings configuration
        ├── dependencies.py   ← Shared FastAPI dependencies
        ├── db/               ← Database infrastructure
        │   ├── __init__.py
        │   ├── base.py       ← DeclarativeBase + TimestampMixin
        │   └── session.py    ← Async engine/session factory
        ├── domains/          ← Core business domains (DDD)
        │   ├── identity/     ← Auth, OAuth2, API keys, MFA
        │   ├── catalog/      ← AgentCard CRUD & validation
        │   ├── search/       ← CapabilityNeed matching
        │   ├── exchange/     ← Orders, escrow, sandbox
        │   ├── payment/      ← Budget, settlement, auth, anomaly
        │   ├── trust/        ← Scoring, evaluation
        │   ├── audit/        ← Hash-chain logging
        │   └── rules/        ← Trading rule engine
        ├── protocols/        ← External protocol adapters
        │   ├── __init__.py
        │   ├── mcp_gateway.py
        │   ├── a2a_gateway.py
        │   └── x402_adapter.py
        └── integrations/     ← Framework plugins
            ├── langchain_plugin/
            │   ├── __init__.py
            │   ├── search_tool.py
            │   └── purchase_tool.py
            └── crewai_plugin/
                ├── __init__.py
                └── capability_provider.py
```

---

## 6. Current Implementation Status

### ✅ Implemented

- Project skeleton (`pyproject.toml`, config, FastAPI app with lifespan)
- All 7 domain routers, models, schemas, and services (structural)
- Database infrastructure (Base, TimestampMixin, async session factory)
- Protocol adapters (MCP gateway, A2A gateway, x402 adapter)
- Integration plugins (LangChain search/purchase tools, CrewAI provider)
- Docker Compose dev stack (PostgreSQL, Redis, Kafka, ClickHouse, Elasticsearch, MinIO)
- Alembic migrations infrastructure (async env.py)
- Design documentation (Whitepaper, Boundary, Constraints, Capability, Config, Audit)

### 🚧 Needs Implementation / Enhancement

- **Database models**: Domain models exist but need full column definitions and relationships
- **Service layer**: Domain services are structural; business logic needs to be wired to actual DB operations
- **Kafka consumers**: Event-driven processing for orders, payments, trust updates
- **Elasticsearch indexing**: AgentCard → ES index pipeline for search
- **ClickHouse schema**: Audit log table creation and query layer
- **x402 on-chain integration**: Actual blockchain transaction signing and verification
- **Sandbox runtime**: Isolated execution environment for skill trial
- **A2A real delivery**: HTTP message delivery to remote agent endpoints
- **Rate limiting middleware**: Redis-backed rate limiting
- **Monitoring & alerting**: Prometheus metrics, Jaeger tracing
- **Test suite**: Unit tests, integration tests, end-to-end tests
- **CI/CD pipeline**: GitHub Actions or similar

---

## 7. Coding Conventions

### General

- **Python version**: 3.12+ — use modern syntax (type aliases, pattern matching, etc.)
- **Imports**: Always use `from __future__ import annotations` at the top of every file
- **Logging**: Use `structlog` exclusively — never `print()` or stdlib `logging`
  ```python
  import structlog
  logger = structlog.get_logger()
  logger.info("event_name", key=value)
  ```
- **Async-first**: All I/O-bound operations must be async. Use `asyncpg`, `httpx.AsyncClient`, `redis.asyncio`, etc.
- **Type hints**: All functions must have full type annotations. Run mypy in strict mode.

### Pydantic

- Use **Pydantic v2** style: `model_config = ConfigDict(...)` instead of `class Config:`
- Use `Field()` for all schema fields with descriptions
- Prefer `model_validate` over `parse_obj`

### SQLAlchemy

- Use **SQLAlchemy 2.0** style: `Mapped[str]`, `mapped_column()`, `DeclarativeBase`
- All models inherit from `Base` (from `aimart.db.base`)
- Use `TimestampMixin` for any model that needs `created_at` / `updated_at`
- Use async sessions exclusively — never sync `Session`

### FastAPI

- Use `async def` for all endpoints
- Use dependency injection via `Depends()` for DB sessions, auth, etc.
- Router prefix pattern: `/api/v1/{domain}`
- Tag each router with its domain name

### File Structure

- Each domain is a package under `domains/` with: `__init__.py`, `router.py`, `service.py`, `models.py`, `schemas.py`
- Keep routers thin — delegate to service functions
- Services own the business logic and DB operations
- Schemas are Pydantic models for request/response validation

### Testing

- Use `pytest` with `pytest-asyncio` (auto mode)
- Test file mirror: `tests/domains/identity/test_service.py`
- Use `httpx.AsyncClient` with `ASGITransport` for API tests
- Use fixtures for DB setup/teardown

---

## 8. Environment Variables

All configuration is loaded from environment variables (with `.env` file support). Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `dev` | dev / staging / pre-prod / prod |
| `DATABASE_URL` | `postgresql+asyncpg://aimart:aimart@localhost:5432/aimart` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `KAFKA_BROKERS` | `localhost:9092` | Kafka broker addresses |
| `CLICKHOUSE_URL` | `clickhouse://localhost:9000/default` | ClickHouse connection string |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch URL |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO endpoint |
| `JWT_PRIVATE_KEY_PATH` | `keys/private.pem` | RS256 private key path |
| `JWT_PUBLIC_KEY_PATH` | `keys/public.pem` | RS256 public key path |

See `aimart/config.py` for the full settings class.

---

## 9. Common Commands

```bash
# Install for development
make dev

# Start the full dev stack
make up

# Run migrations
make migrate

# Run tests
make test

# Lint and type-check
make lint

# Stop all services
make down

# Build Docker image
make build

# Clean artifacts
make clean
```

---

## 10. References

- **Whitepaper**: `docs/AIMart_Whitepaper.md` — vision, market analysis, architecture
- **Boundary**: `docs/AIMart_Boundary.md` — participants, roles, permissions, business domains
- **Constraints**: `docs/AIMart_Constraints.md` — trading rules, budgets, risk, SLA
- **Capability**: `docs/AIMart_Capability.md` — AgentCard schema specification
- **Config**: `docs/AIMart_Config.md` — environments, API definitions, feature flags
- **Audit**: `docs/AIMart_Audit.md` — logging schema, hash-chain mechanism, retention
