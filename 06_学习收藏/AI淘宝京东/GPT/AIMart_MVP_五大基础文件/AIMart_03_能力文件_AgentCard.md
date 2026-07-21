# AIMart 能力文件：AgentCard 机器可读能力商品标准

> 建议实际落地文件名：  
> - `schemas/agentcard.schema.json`  
> - `agent_cards/cap_xxx.json`  
> 本 Markdown 用途：给所有能力商品定义统一、机器可读、可搜索、可比较、可调用、可交易的标准。  
> 核心目标：让 AI Agent 能读懂商品，而不是只让人类看懂商品。

---

## 1. 这个文件解决什么问题

传统商品页给人看：

```text
标题、图片、介绍、价格、评价。
```

AIMart 的能力商品必须给 AI Agent 看：

```text
输入是什么？
输出是什么？
怎么调用？
多少钱？
延迟多少？
风险多大？
是否需要人工审批？
是否保存数据？
是否可私有化？
调用失败如何处理？
能和哪些能力组合？
```

所以需要 AgentCard。

AgentCard 是 AIMart 的核心资产之一。

---

## 2. AI 编码指令

让 AI 工程助手根据本文件生成实际项目文件时，应遵守：

```text
1. 生成 schemas/agentcard.schema.json。
2. 生成 agent_cards/ 目录。
3. 生成至少 3 个示例 AgentCard JSON。
4. 所有商品上架必须通过 AgentCard Schema 校验。
5. 搜索、推荐、AI Agent 接口都读取 AgentCard。
6. AgentCard 需要支持版本管理。
7. 人类商品页可以由 AgentCard 渲染生成，但 AgentCard 是底层事实来源。
```

---

## 3. AgentCard 字段分层

```text
基础身份层：id、名称、类型、类目、商家、版本
人类描述层：给人看的描述、案例、适用场景
机器描述层：给 AI 读的描述、输入输出 Schema
调用执行层：API、MCP、Webhook、项目交付、私有部署
价格结算层：按次、订阅、项目制、报价制、担保交易
权限数据层：需要什么数据、是否外部写入、是否需要审批
风险安全层：风险等级、禁用场景、人工复核要求
质量评价层：评分、成功率、退款率、样本量
组合依赖层：能和哪些能力组合、前置依赖
```

---

## 4. AgentCard JSON Schema v0.1

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://aimart.example/schemas/agentcard.schema.json",
  "title": "AIMart AgentCard",
  "type": "object",
  "required": [
    "agentcard_version",
    "capability_id",
    "name",
    "type",
    "category",
    "seller_id",
    "version",
    "status",
    "human_description",
    "machine_description",
    "input_schema",
    "output_schema",
    "execution",
    "pricing",
    "risk",
    "data_policy"
  ],
  "properties": {
    "agentcard_version": {
      "type": "string",
      "description": "AgentCard 规范版本，例如 0.1"
    },
    "capability_id": {
      "type": "string",
      "pattern": "^cap_[a-z0-9_]+$"
    },
    "name": {
      "type": "string",
      "minLength": 2
    },
    "type": {
      "type": "string",
      "enum": [
        "model",
        "api",
        "agent",
        "workflow",
        "expert_service",
        "solution",
        "compute",
        "data_service",
        "evaluation_service",
        "security_service"
      ]
    },
    "category": {
      "type": "string"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "seller_id": {
      "type": "string"
    },
    "version": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["draft", "pending_review", "active", "paused", "rejected", "deprecated"]
    },
    "human_description": {
      "type": "string"
    },
    "machine_description": {
      "type": "string"
    },
    "use_cases": {
      "type": "array",
      "items": { "type": "string" }
    },
    "not_suitable_for": {
      "type": "array",
      "items": { "type": "string" }
    },
    "input_schema": {
      "type": "object",
      "description": "JSON Schema describing input"
    },
    "output_schema": {
      "type": "object",
      "description": "JSON Schema describing output"
    },
    "execution": {
      "type": "object",
      "required": ["modes"],
      "properties": {
        "modes": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["api", "mcp", "webhook", "human_service", "project_delivery", "private_deployment"]
          }
        },
        "protocol": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["REST", "MCP", "GraphQL", "SDK", "Manual", "Webhook"]
          }
        },
        "endpoint": { "type": "string" },
        "auth_type": {
          "type": "string",
          "enum": ["none", "api_key", "oauth", "platform_proxy", "manual"]
        },
        "rate_limit": { "type": "string" }
      }
    },
    "pricing": {
      "type": "object",
      "required": ["model", "currency"],
      "properties": {
        "model": {
          "type": "string",
          "enum": ["free", "fixed", "usage_based", "subscription", "quote_based", "milestone_based"]
        },
        "unit": {
          "type": "string",
          "enum": ["request", "token", "document", "image", "minute", "hour", "month", "project", "custom"]
        },
        "price": { "type": "number" },
        "starting_price": { "type": "number" },
        "currency": { "type": "string" },
        "trial_supported": { "type": "boolean" },
        "trial_limit": { "type": "string" }
      }
    },
    "sla": {
      "type": "object",
      "properties": {
        "average_latency_ms": { "type": "number" },
        "uptime_target": { "type": "string" },
        "support_response_time": { "type": "string" },
        "delivery_time": { "type": "string" }
      }
    },
    "permissions": {
      "type": "object",
      "properties": {
        "data_required": {
          "type": "array",
          "items": { "type": "string" }
        },
        "external_write_permission": { "type": "boolean" },
        "payment_permission_required": { "type": "boolean" },
        "human_approval_required": { "type": "boolean" },
        "minimum_agent_permission_level": {
          "type": "string",
          "enum": ["L0", "L1", "L2", "L3", "L4", "L5"]
        }
      }
    },
    "data_policy": {
      "type": "object",
      "required": ["store_user_data", "use_data_for_training"],
      "properties": {
        "store_user_data": { "type": "boolean" },
        "use_data_for_training": { "type": "boolean" },
        "retention_days": { "type": "number" },
        "private_deployment_supported": { "type": "boolean" },
        "data_deletion_supported": { "type": "boolean" },
        "seller_can_download_raw_data": { "type": "boolean" }
      }
    },
    "risk": {
      "type": "object",
      "required": ["risk_level"],
      "properties": {
        "risk_level": {
          "type": "string",
          "enum": ["low", "medium", "high", "prohibited"]
        },
        "sensitive_data_involved": { "type": "boolean" },
        "regulated_industry": { "type": "boolean" },
        "requires_human_review": { "type": "boolean" },
        "prohibited_use_cases": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "evaluation": {
      "type": "object",
      "properties": {
        "platform_score": { "type": "number" },
        "task_success_rate": { "type": "number" },
        "refund_rate": { "type": "number" },
        "average_rating": { "type": "number" },
        "sample_size": { "type": "number" }
      }
    },
    "composability": {
      "type": "object",
      "properties": {
        "can_chain_with": {
          "type": "array",
          "items": { "type": "string" }
        },
        "dependencies": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "settlement": {
      "type": "object",
      "properties": {
        "settlement_mode": {
          "type": "string",
          "enum": ["prepaid_balance", "escrow", "postpaid", "manual_invoice", "micropayment"]
        },
        "escrow_supported": { "type": "boolean" },
        "micropayment_supported": { "type": "boolean" }
      }
    }
  }
}
```

---

## 5. 示例 AgentCard：企业知识库问答 Agent

```json
{
  "agentcard_version": "0.1",
  "capability_id": "cap_knowledge_rag_001",
  "name": "企业知识库问答 Agent",
  "type": "agent",
  "category": "knowledge_management",
  "tags": ["RAG", "知识库", "企业文档", "问答"],
  "seller_id": "seller_001",
  "version": "1.0.0",
  "status": "active",
  "human_description": "帮助企业将制度、产品文档、SOP、FAQ 转化为可问答的 AI 助手。",
  "machine_description": "Answers questions based on uploaded enterprise documents using retrieval augmented generation and citation-based responses.",
  "use_cases": ["企业制度问答", "产品资料问答", "SOP 查询", "新人培训助手"],
  "not_suitable_for": ["医疗诊断", "法律最终意见", "金融投资建议"],
  "input_schema": {
    "type": "object",
    "required": ["question", "knowledge_base_id"],
    "properties": {
      "question": { "type": "string" },
      "knowledge_base_id": { "type": "string" },
      "user_role": { "type": "string" }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "answer": { "type": "string" },
      "citations": {
        "type": "array",
        "items": { "type": "string" }
      },
      "confidence": { "type": "number" },
      "need_human_review": { "type": "boolean" }
    }
  },
  "execution": {
    "modes": ["api", "project_delivery", "private_deployment"],
    "protocol": ["REST", "MCP"],
    "endpoint": "https://api.aimart.example/capabilities/cap_knowledge_rag_001/run",
    "auth_type": "platform_proxy",
    "rate_limit": "100 requests/minute"
  },
  "pricing": {
    "model": "usage_based",
    "unit": "request",
    "price": 0.02,
    "currency": "CNY",
    "trial_supported": true,
    "trial_limit": "100 requests"
  },
  "sla": {
    "average_latency_ms": 1500,
    "uptime_target": "99.5%",
    "support_response_time": "24h",
    "delivery_time": "7-21 days for project delivery"
  },
  "permissions": {
    "data_required": ["enterprise_documents", "user_question"],
    "external_write_permission": false,
    "payment_permission_required": false,
    "human_approval_required": false,
    "minimum_agent_permission_level": "L4"
  },
  "data_policy": {
    "store_user_data": false,
    "use_data_for_training": false,
    "retention_days": 0,
    "private_deployment_supported": true,
    "data_deletion_supported": true,
    "seller_can_download_raw_data": false
  },
  "risk": {
    "risk_level": "medium",
    "sensitive_data_involved": true,
    "regulated_industry": false,
    "requires_human_review": false,
    "prohibited_use_cases": ["自动生成法律最终意见", "医疗诊断"]
  },
  "evaluation": {
    "platform_score": 4.6,
    "task_success_rate": 0.91,
    "refund_rate": 0.03,
    "average_rating": 4.7,
    "sample_size": 1280
  },
  "composability": {
    "can_chain_with": ["cap_document_parser_001", "cap_ocr_001", "cap_enterprise_wechat_connector_001"],
    "dependencies": ["knowledge_base_setup"]
  },
  "settlement": {
    "settlement_mode": "prepaid_balance",
    "escrow_supported": true,
    "micropayment_supported": true
  }
}
```

---

## 6. 示例 AgentCard：电商商品文案生成 Agent

```json
{
  "agentcard_version": "0.1",
  "capability_id": "cap_ecommerce_copywriter_001",
  "name": "电商商品文案生成 Agent",
  "type": "agent",
  "category": "content_generation",
  "tags": ["电商", "文案", "小红书", "淘宝", "抖音"],
  "seller_id": "seller_ai_content_001",
  "version": "1.0.0",
  "status": "active",
  "human_description": "为电商商家生成标题、卖点、详情页文案和社媒种草文案。",
  "machine_description": "Generates ecommerce product copy based on product attributes, target platform, tone and audience.",
  "use_cases": ["商品标题生成", "卖点提炼", "详情页文案", "小红书种草文案"],
  "not_suitable_for": ["虚假宣传", "医疗功效夸大", "违法广告"],
  "input_schema": {
    "type": "object",
    "required": ["product_name", "product_attributes", "target_platform"],
    "properties": {
      "product_name": { "type": "string" },
      "product_attributes": { "type": "object" },
      "target_platform": {
        "type": "string",
        "enum": ["taobao", "tmall", "pinduoduo", "xiaohongshu", "douyin"]
      },
      "tone": { "type": "string" }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "title": { "type": "string" },
      "selling_points": {
        "type": "array",
        "items": { "type": "string" }
      },
      "long_description": { "type": "string" },
      "social_post": { "type": "string" }
    }
  },
  "execution": {
    "modes": ["api"],
    "protocol": ["REST"],
    "endpoint": "https://api.aimart.example/capabilities/cap_ecommerce_copywriter_001/run",
    "auth_type": "platform_proxy",
    "rate_limit": "300 requests/minute"
  },
  "pricing": {
    "model": "usage_based",
    "unit": "request",
    "price": 0.05,
    "currency": "CNY",
    "trial_supported": true,
    "trial_limit": "50 requests"
  },
  "sla": {
    "average_latency_ms": 1200,
    "uptime_target": "99.0%",
    "support_response_time": "48h"
  },
  "permissions": {
    "data_required": ["product_attributes"],
    "external_write_permission": false,
    "payment_permission_required": false,
    "human_approval_required": false,
    "minimum_agent_permission_level": "L4"
  },
  "data_policy": {
    "store_user_data": false,
    "use_data_for_training": false,
    "retention_days": 0,
    "private_deployment_supported": false,
    "data_deletion_supported": true,
    "seller_can_download_raw_data": false
  },
  "risk": {
    "risk_level": "low",
    "sensitive_data_involved": false,
    "regulated_industry": false,
    "requires_human_review": false,
    "prohibited_use_cases": ["虚假宣传", "违法广告"]
  },
  "evaluation": {
    "platform_score": 4.5,
    "task_success_rate": 0.88,
    "refund_rate": 0.01,
    "average_rating": 4.6,
    "sample_size": 900
  },
  "composability": {
    "can_chain_with": ["cap_product_image_generator_001", "cap_content_quality_checker_001"],
    "dependencies": []
  },
  "settlement": {
    "settlement_mode": "prepaid_balance",
    "escrow_supported": false,
    "micropayment_supported": true
  }
}
```

---

## 7. AgentCard 最小验收标准

```text
1. 每个能力商品必须有 capability_id、type、category、seller_id。
2. 每个可调用能力必须有 input_schema、output_schema。
3. 每个能力必须声明 pricing、risk、data_policy。
4. 高风险能力必须 requires_human_review=true。
5. 商品状态不是 active 时，不能被 Agent 调用。
6. Agent 搜索结果必须可以返回 AgentCard 的摘要字段。
7. API 调用前必须校验 input_schema。
8. API 返回后必须校验 output_schema。
9. AgentCard 更新必须产生新版本，不允许静默覆盖历史版本。
```

---

## 8. 给 AI 编码助手的提示词

```text
请根据本 Markdown 生成：
1. schemas/agentcard.schema.json
2. agent_cards/cap_knowledge_rag_001.json
3. agent_cards/cap_ecommerce_copywriter_001.json
4. AgentCard 校验器 validate_agentcard(card)
5. 输入输出校验器 validate_capability_input(capability_id, payload) 和 validate_capability_output(capability_id, result)

要求：
- 所有能力商品上架前必须通过 schema 校验。
- 所有 Agent 调用前必须校验 input_schema。
- 所有能力返回后必须校验 output_schema。
- AgentCard 必须支持 version 字段。
```
