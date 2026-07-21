<!-- AIMart 完整合并版 v2：保留原始文件内容，并追加 Codex MVP 落地补充。生成日期：2026-06-06 -->

# AIMart 能力文件：AgentCard 机器可读规范

> 版本：v1.0 | 2026-06-07 | 状态：设计阶段

---

## 一、AgentCard 总体规范

### 1.1 设计原则

- **机器可读**：所有字段使用 JSON Schema 定义，AI Agent 可直接解析，无需自然语言理解
- **结构化声明**：能力描述不是文案，而是可验证的结构化声明——每个性能指标都可以与基准测试结果对照
- **分层设计**：基础层（所有商品共有）+ 扩展层（按商品类型特化），避免冗余同时保持灵活性
- **版本化**：AgentCard 自身版本化，支持 Agent 指定所需版本

### 1.2 Schema 版本

```
agentcard_schema_version: "1.0"
规范 URI: https://aimart.dev/schemas/agentcard/v1.0
```

---

## 二、基础层 Schema（所有商品共有）

```json
{
  "$schema": "https://aimart.dev/schemas/agentcard/v1.0/base",
  "agentcard_id": "ac-uuid-001",
  "agentcard_version": "1.0.0",
  "schema_version": "1.0",

  "identity": {
    "provider_id": "provider-uuid-001",
    "provider_name": "LegalAI Corp",
    "item_id": "item-uuid-001",
    "item_name": "ContractGuard-Law-v2",
    "item_type": "model | skill | expert | compute",
    "item_version": "2.3.1",
    "item_release_date": "2026-05-15",
    "item_changelog_url": "https://provider.example.com/changelog/contractguard/v2.3.1"
  },

  "capability_declaration": {
    "domains": ["legal", "contract_review", "compliance"],
    "supported_languages": ["zh-CN", "en-US"],
    "task_types": [
      {
        "task_type_id": "tt-001",
        "name": "contract_compliance_review",
        "description_machine": "Review contract text for compliance with specified jurisdiction regulations",
        "input_schema": {
          "type": "object",
          "properties": {
            "contract_text": { "type": "string", "maxLength": 50000 },
            "jurisdiction": { "type": "string", "enum": ["CN", "US-CA", "US-NY", "EU"] },
            "review_focus": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": ["compliance", "risk_clause", "obligation_balance", "termination_clause"]
              }
            }
          },
          "required": ["contract_text", "jurisdiction"]
        },
        "output_schema": {
          "type": "object",
          "properties": {
            "compliance_score": { "type": "number", "minimum": 0, "maximum": 100 },
            "risk_clauses": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "clause_text": { "type": "string" },
                  "risk_level": { "type": "string", "enum": ["high", "medium", "low"] },
                  "risk_reason": { "type": "string" },
                  "suggested_revision": { "type": "string" }
                }
              }
            },
            "summary": { "type": "string" }
          }
        }
      }
    ],
    "boundary_declaration": {
      "in_scope": ["中文和英文商业合同审查", "合规性检查", "风险条款识别"],
      "out_of_scope": ["非商业合同（如劳动合同）", "非法律领域的文本分析", "提供法律建议（非AI可替代）"],
      "performance_degradation_triggers": [
        "输入文本超过50000字符时精度下降约5%",
        "非声明司法管辖区时结果不可靠"
      ]
    }
  },

  "performance_declaration": {
    "benchmarks": [
      {
        "benchmark_id": "bench-001",
        "benchmark_name": "AIMart-ContractReview-Bench-v1",
        "metric": "f1_score",
        "declared_value": 0.92,
        "verified_value": 0.89,
        "verified_by": "certifier-uuid-001",
        "verified_date": "2026-05-20",
        "sample_size": 5000
      },
      {
        "benchmark_id": "bench-002",
        "benchmark_name": "AIMart-ContractReview-Bench-v1",
        "metric": "latency_p99_ms",
        "declared_value": 1500,
        "verified_value": 1420,
        "verified_by": "certifier-uuid-001",
        "verified_date": "2026-05-20",
        "sample_size": 10000
      }
    ],
    "performance_constraints": {
      "latency_p50_ms": 800,
      "latency_p99_ms": 1500,
      "throughput_rps": 100,
      "availability_sla": 0.999,
      "output_consistency": 0.95
    }
  },

  "pricing": {
    "model": "per_call | per_token | per_minute | per_hour | subscription | free",
    "currency": "CNY | USD | USDC",
    "details": {
      "per_call": { "price": 0.05, "unit": "CNY/call" },
      "per_token": { "input_price": 0.00001, "output_price": 0.00003, "unit": "CNY/token" },
      "per_minute": null,
      "per_hour": null,
      "subscription": { "monthly_price": 99.00, "calls_per_month": 5000, "overage_price": 0.03 },
      "free_tier": { "calls_per_month": 10, "input_token_limit": 1000 }
    },
    "bulk_discount": [
      { "min_calls": 1000, "discount_pct": 10 },
      { "min_calls": 10000, "discount_pct": 20 }
    ]
  },

  "delivery": {
    "method": "api_call | weight_download | code_package | instance",
    "api_endpoint": "https://api.aimart.dev/v1/contractguard/v2",
    "supported_protocols": ["rest", "mcp", "a2a"],
    "api_version": "2.3",
    "rate_limit": {
      "requests_per_second": 10,
      "requests_per_day": 10000,
      "concurrent_connections": 5
    }
  },

  "trust": {
    "trust_score": 82,
    "trust_score_updated_at": "2026-06-06T12:00:00Z",
    "certification_status": "certified",
    "certifications": [
      {
        "certifier_id": "certifier-uuid-001",
        "certifier_name": "AI Quality Lab",
        "certification_level": "platform_certified",
        "valid_until": "2026-12-01"
      }
    ],
    "usage_statistics": {
      "total_calls": 1250000,
      "total_agents_served": 3500,
      "avg_success_rate": 0.91,
      "avg_effect_score": 4.2,
      "dispute_count": 12,
      "dispute_win_rate": 0.75
    },
    "recent_reviews": [
      {
        "reviewer_agent_id": "agent-uuid-xxx",
        "review_date": "2026-06-05",
        "task_type": "contract_compliance_review",
        "effect_score": 4,
        "success": true,
        "actual_latency_ms": 980,
        "notes_machine": "accuracy_met_declaration:true; latency_within_sla:true; jurisdiction_coverage:partial"
      }
    ]
  },

  "compatibility": {
    "min_agent_framework_version": {
      "langchain": "0.1.0",
      "crewai": "0.28.0",
      "autogen": "0.2.0"
    },
    "required_capabilities": ["text_input", "json_output"],
    "conflict_items": ["item-uuid-yyy"],
    "dependency_items": ["item-uuid-zzz"]
  },

  "legal": {
    "license": "MIT | Apache-2.0 | Commercial | Proprietary",
    "data_handling": {
      "input_data_retention": "none | 30d | 90d | indefinite",
      "input_data_usage": "service_only | training_allowed | analytics_only",
      "data_residency": "CN | US | EU | any"
    },
    "terms_url": "https://provider.example.com/terms/contractguard",
    "privacy_policy_url": "https://provider.example.com/privacy"
  }
}
```

---

## 三、扩展层 Schema（按商品类型）

### 3.1 模型类扩展（Model Extension）

```json
{
  "model_extension": {
    "model_architecture": {
      "type": "llm | diffusion | multimodal | embedding | reranker",
      "parameter_count": "7B | 13B | 70B | 175B | unknown",
      "architecture_name": "transformer | mamba | hybrid",
      "context_window": 32768,
      "max_output_tokens": 4096
    },
    "supported_modalities": {
      "input": ["text", "image", "audio"],
      "output": ["text", "image"]
    },
    "weight_download": {
      "available": true,
      "format": "safetensors | gguf | onnx",
      "size_bytes": 14000000000,
      "download_url": "https://aimart.dev/download/item-uuid-001/v2.3.1",
      "checksum_sha256": "a1b2c3d4..."
    },
    "fine_tuning_support": {
      "available": true,
      "methods": ["lora", "qlora", "full"],
      "base_model_id": null
    },
    "tokenization": {
      "tokenizer_type": "bpe | sentencepiece",
      "vocab_size": 32000,
      "token_counter_endpoint": "https://api.aimart.dev/v1/contractguard/v2/count_tokens"
    }
  }
}
```

### 3.2 技能类扩展（Skill Extension）

```json
{
  "skill_extension": {
    "skill_type": "tool | workflow | agent_template | mcp_server",
    "runtime": {
      "environment": "python3.12 | nodejs20 | wasm",
      "package_format": "pip | npm | docker | wasm_binary",
      "entry_point": "aimart_skill.main:execute",
      "dependencies": [
        { "name": "openai", "version": ">=1.0.0" },
        { "name": "pydantic", "version": ">=2.0.0" }
      ]
    },
    "resource_requirements": {
      "cpu_cores_max": 2,
      "memory_mb_max": 4096,
      "network_access": {
        "allowed": true,
        "whitelist": ["api.openai.com", "api.aimart.dev"]
      },
      "execution_timeout_seconds": 60,
      "temp_storage_mb_max": 100
    },
    "security_scan": {
      "last_scan_date": "2026-05-15",
      "scan_result": "clean | warning | failed",
      "scan_details_url": "https://aimart.dev/security/item-uuid-002/scan",
      "sandbox_verified": true
    },
    "context_data_access": {
      "requires_agent_context": false,
      "context_fields_needed": [],
      "data_sensitivity_max": "public"
    },
    "mcp_server_config": {
      "available": true,
      "transport": "stdio | sse | streamable-http",
      "tools": [
        {
          "tool_name": "review_contract",
          "description": "Review a contract for compliance issues",
          "input_schema": { "...": "..." },
          "output_schema": { "...": "..." }
        }
      ]
    }
  }
}
```

### 3.3 专家类扩展（Expert Extension）

```json
{
  "expert_extension": {
    "domain": {
      "primary_domain": "legal",
      "sub_domains": ["contract_law", "corporate_law"],
      "jurisdictions_covered": ["CN", "US-CA", "US-NY"],
      "jurisdictions_excluded": ["EU-GDPR-specific"]
    },
    "knowledge_base": {
      "sources": [
        "中国法律法规数据库",
        "美国加州商法典",
        "合同法判例库"
      ],
      "last_updated": "2026-06-01",
      "update_frequency": "weekly | monthly | quarterly",
      "document_count": 150000,
      "coverage_declaration": "中国现行商业法律覆盖率 ≥ 90%"
    },
    "consultation_mode": {
      "type": "qa | review | drafting | analysis",
      "max_input_tokens": 50000,
      "max_output_tokens": 4096,
      "follow_up_supported": true,
      "multi_turn_max": 5
    },
    "domain_accuracy": {
      "self_declared": 0.95,
      "verified": 0.89,
      "verified_by": "certifier-uuid-002",
      "verification_method": "blind_expert_comparison",
      "verification_sample": 500
    }
  }
}
```

### 3.4 算力类扩展（Compute Extension）

```json
{
  "compute_extension": {
    "instance_type": {
      "gpu_type": "A100_80G | H100_80G | A6000 | L40S | custom",
      "gpu_count": 8,
      "vcpu_count": 96,
      "memory_gb": 640,
      "storage_gb": 4000,
      "storage_type": "nvme_ssd | hdd"
    },
    "availability": {
      "sla_uptime_pct": 99.5,
      "current_availability": "available | limited | unavailable",
      "queue_position": 0,
      "estimated_wait_minutes": 0,
      "peak_hours": ["08:00-12:00 UTC", "14:00-18:00 UTC"],
      "maintenance_windows": [
        {
          "start": "2026-07-01T02:00:00Z",
          "end": "2026-07-01T06:00:00Z",
          "advance_notice_days": 7
        }
      ]
    },
    "networking": {
      "bandwidth_gbps": 10,
      "internet_access": true,
      "private_vpc": true,
      "allowed_ingress_ports": [22, 443, 8080]
    },
    "deployment": {
      "startup_time_seconds": 120,
      "supported_os": ["ubuntu22.04", "debian12"],
      "pre_installed": ["cuda12.4", "pytorch2.4", "transformers4.40"],
      "custom_image_support": true
    },
    "scaling": {
      "max_concurrent_instances": 64,
      "auto_scale": true,
      "scale_up_cooldown_seconds": 300,
      "scale_down_cooldown_seconds": 600
    }
  }
}
```

---

## 四、AgentCard 注册与发现

### 4.1 注册流程

```
1. Provider 创建 AgentCard（JSON 格式）
2. 提交至 AIMart 商品域 API: POST /api/v1/catalog/items
3. 平台自动验证：
   a. Schema 合规性检查（必须符合 v1.0 规范）
   b. 能力声明 vs 基准测试偏差检查（≤ 110%）
   c. 安全扫描（技能类必须通过）
   d. 定价合理性检查（不得与同类商品差异超过 10 倍，防止刷单）
4. 验证通过 → 商品上架，AgentCard 索引至搜索域
5. 验证失败 → 返回具体失败原因，Provider 修改后重新提交
6. 认证（可选）：Provider 可申请第三方认证，提升信任评分
```

### 4.2 发现机制

Agent 通过搜索域 API 发现能力商品：

```
POST /api/v1/search/capabilities

请求体：
{
  "query": {
    "task_description": "审查中文法律合同的合规性",
    "required_domains": ["legal", "contract_review"],
    "required_languages": ["zh-CN"],
    "performance_constraints": {
      "latency_p99_ms_max": 2000,
      "accuracy_min": 0.85
    },
    "cost_constraints": {
      "max_per_call_cny": 0.05,
      "pricing_model_preference": "per_call"
    },
    "trust_score_min": 60,
    "delivery_preference": "api_call",
    "item_type_filter": ["model", "expert"],
    "sort_by": "relevance | trust_score | price_asc | price_desc"
  },
  "pagination": {
    "offset": 0,
    "limit": 20
  }
}

响应体：
{
  "total_matches": 7,
  "results": [
    {
      "item_id": "item-uuid-001",
      "item_name": "ContractGuard-Law-v2",
      "item_type": "model",
      "provider_name": "LegalAI Corp",
      "match_score": 0.94,
      "trust_score": 82,
      "price_per_call_cny": 0.05,
      "key_performance": {
        "latency_p99_ms": 1500,
        "verified_accuracy": 0.89
      },
      "certification_status": "certified",
      "agentcard_url": "/api/v1/catalog/items/item-uuid-001/agentcard"
    }
  ]
}
```

### 4.3 版本管理

```
VERSION-001: AgentCard 每次更新创建新版本，旧版本保留 90 天
VERSION-002: Agent 可在请求中指定所需版本（默认最新）
VERSION-003: 重大变更（能力声明下调、定价上涨、接口不兼容）需标记为 major version
VERSION-004: 订阅制商品的 AgentCard 重大变更需提前 7 天通知已订阅 Agent
VERSION-005: 已下架商品的 AgentCard 保留 365 天（供审计和争议追溯）
```

---

## 五、AgentCard 与协议栈的映射

| AgentCard 字段 | MCP | A2A | UCP | x402 |
|----------------|-----|-----|-----|------|
| delivery.supported_protocols | mcp → 注册为 MCP Server | — | — | — |
| capability_declaration.task_types | — | 注册为 A2A AgentCard capabilities | — | — |
| pricing | — | — | 映射为 UCP offer schema | 映射为 x402 payment params |
| delivery.api_endpoint | MCP tool endpoint | A2A task endpoint | UCP product endpoint | x402 server endpoint |
| performance_constraints | MCP tool metadata | A2A AgentCard metrics | UCP SLA fields | — |
| trust.trust_score | — | A2A AgentCard reputation | UCP rating | — |

---

# v2.0 落地补充：AgentCard 交易型扩展字段

## 1. 必须新增的 AgentCard 字段

为了让 Codex 实现时覆盖 Agent 成熟度、法律绑定、合规与支付边界，AgentCard 需要扩展以下字段。

```json
{
  "legal_binding": {
    "agent_can_contract": false,
    "requires_owner_as_legal_counterparty": true,
    "buyer_legal_entity_required": true,
    "terms_acceptance_required_by": "owner_or_organization"
  },
  "agent_maturity_requirement": {
    "minimum_maturity_level_for_search": "M0",
    "minimum_maturity_level_for_quote": "M1",
    "minimum_maturity_level_for_execution": "M2",
    "production_ready_required": false,
    "sandbox_required_before_execution": true
  },
  "compliance": {
    "supported_regions": ["CN"],
    "data_residency_required": false,
    "cross_border_data_allowed": false,
    "gdpr_relevant": false,
    "pipl_relevant": true,
    "requires_local_processing_for_sensitive_data": true
  },
  "payment_protocols": {
    "mock_payment_supported": true,
    "prepaid_balance_supported": true,
    "escrow_supported": true,
    "x402_supported": false,
    "acp_supported": false,
    "ap2_supported": false
  },
  "sandbox": {
    "trial_supported": true,
    "sandbox_required_for_new_agents": true,
    "max_trial_calls_per_day": 3,
    "max_input_size_ratio": 0.1
  },
  "failure_modes": [
    {
      "code": "LOW_CONFIDENCE",
      "description": "Output confidence below declared threshold",
      "refund_eligible": false
    },
    {
      "code": "OUTPUT_SCHEMA_INVALID",
      "description": "Output failed schema validation",
      "refund_eligible": true
    }
  ]
}
```

## 2. AgentCard 上架校验新增规则

```text
1. 高风险能力必须 requires_owner_as_legal_counterparty=true。
2. 高风险能力必须 minimum_maturity_level_for_execution=M3 或更高。
3. MVP 中 x402/acp/ap2 字段可以存在，但必须 enabled=false。
4. cross_border_data_allowed=true 的能力在 MVP 中不得 active 上架，只能 pending_review。
5. 算力金融衍生品不得作为能力商品上架。
6. API 能力必须有 input_schema 与 output_schema。
7. 人工专家服务可没有 API endpoint，但必须有 delivery 和 acceptance_criteria。
```

