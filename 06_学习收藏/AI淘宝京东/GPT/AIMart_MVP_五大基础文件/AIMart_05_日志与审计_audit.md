# AIMart 日志与审计文件：每一步可追溯

> 建议实际落地文件名：  
> - `config/audit_policy.yaml`  
> - `schemas/audit_event.schema.json`  
> - `logs/audit.ndjson`  
> 本 Markdown 用途：定义 AIMart 的审计范围、日志格式、事件类型、留存策略和安全要求。  
> 核心目标：确保 **AI Agent 搜索、报价、下单、调用、支付、交付、验收、评价、退款、争议、风控** 每一步都可追溯。

---

## 1. 为什么 AIMart 必须重视审计

AIMart 涉及：

```text
AI Agent 自动行为
企业数据
支付与结算
商家交付
平台仲裁
高风险能力
API 调用
预算消耗
```

如果没有审计，会出现：

```text
不知道是谁调用了能力
不知道 AI 为什么花了钱
不知道商家是否按时交付
不知道数据是否被下载
不知道谁改了订单
不知道为什么评分变化
不知道争议证据在哪里
```

日志与审计是 AIMart 的安全底座。

---

## 2. AI 编码指令

让 AI 工程助手根据本文件生成实际项目文件时，应遵守：

```text
1. 生成 config/audit_policy.yaml。
2. 生成 schemas/audit_event.schema.json。
3. 所有关键操作必须写 audit event。
4. 审计日志不能被普通管理员删除或修改。
5. 每个事件必须包含 trace_id、actor、action、resource、result、timestamp。
6. AI Agent 的所有搜索、报价、调用、反馈都必须记录。
7. 资金操作必须记录 before/after 状态。
8. 敏感字段必须脱敏。
```

---

## 3. audit_policy.yaml 模板

```yaml
version: "0.1"
project: "AIMart"
file_type: "audit_policy"

principles:
  - "所有关键业务动作必须可追溯。"
  - "所有 AI Agent 动作必须可追溯。"
  - "所有资金动作必须可追溯。"
  - "所有权限变更必须可追溯。"
  - "审计日志不可被普通管理员修改或删除。"
  - "敏感数据写入日志前必须脱敏。"

audit:
  enabled: true
  format: "ndjson"
  require_trace_id: true
  require_actor: true
  require_resource: true
  require_result: true
  write_mode: "append_only"
  tamper_resistance:
    enabled: true
    method: "hash_chain"
    hash_algorithm: "sha256"

retention:
  default_days: 365
  payment_events_days: 1825
  security_events_days: 1825
  agent_execution_events_days: 730
  dispute_events_days: 1825

masking:
  enabled: true
  fields_to_mask:
    - "password"
    - "api_key"
    - "token"
    - "secret"
    - "phone"
    - "email"
    - "id_card"
    - "bank_card"
    - "raw_document_content"
  mask_strategy:
    email: "partial"
    phone: "partial"
    secret: "full"
    raw_document_content: "redact"

event_categories:
  identity:
    description: "登录、注册、权限、组织、Agent 身份"
    events:
      - "user.registered"
      - "user.login"
      - "user.logout"
      - "role.assigned"
      - "role.revoked"
      - "agent.created"
      - "agent.permission_updated"
      - "agent.budget_updated"

  seller:
    description: "商家入驻、认证、店铺"
    events:
      - "seller.applied"
      - "seller.reviewed"
      - "seller.approved"
      - "seller.rejected"
      - "store.created"
      - "store.updated"

  capability:
    description: "能力商品与 AgentCard"
    events:
      - "capability.created"
      - "capability.updated"
      - "capability.submitted_for_review"
      - "capability.approved"
      - "capability.rejected"
      - "capability.paused"
      - "capability.version_published"
      - "agentcard.validation_failed"
      - "agentcard.validation_passed"

  requirement:
    description: "买家需求"
    events:
      - "requirement.created"
      - "requirement.updated"
      - "requirement.diagnosed"
      - "requirement.matched"
      - "requirement.closed"

  quote:
    description: "报价"
    events:
      - "quote.requested"
      - "quote.created"
      - "quote.updated"
      - "quote.accepted"
      - "quote.rejected"
      - "quote.expired"

  order:
    description: "订单和履约"
    events:
      - "order.draft_created"
      - "order.created"
      - "order.paid"
      - "order.started"
      - "milestone.submitted"
      - "milestone.accepted"
      - "milestone.rejected"
      - "delivery.submitted"
      - "order.completed"
      - "order.cancelled"

  payment:
    description: "支付、担保、结算、退款"
    events:
      - "payment.created"
      - "payment.succeeded"
      - "payment.failed"
      - "escrow.created"
      - "escrow.frozen"
      - "escrow.released"
      - "settlement.requested"
      - "settlement.approved"
      - "settlement.paid"
      - "refund.requested"
      - "refund.approved"
      - "refund.rejected"
      - "refund.completed"

  agent:
    description: "AI Agent 行为"
    events:
      - "agent.capability_search"
      - "agent.capability_read"
      - "agent.capability_compare"
      - "agent.quote_request"
      - "agent.trial_request"
      - "agent.order_draft_create"
      - "agent.execution_requested"
      - "agent.execution_allowed"
      - "agent.execution_blocked"
      - "agent.feedback_submitted"
      - "agent.budget_exceeded"
      - "agent.approval_required"

  execution:
    description: "能力调用执行"
    events:
      - "execution.started"
      - "execution.input_validated"
      - "execution.output_validated"
      - "execution.succeeded"
      - "execution.failed"
      - "execution.timeout"
      - "execution.refunded"

  risk:
    description: "风险与安全"
    events:
      - "risk.detected"
      - "risk.review_required"
      - "risk.blocked"
      - "security.prompt_injection_detected"
      - "security.suspicious_activity"
      - "security.data_policy_violation"
      - "security.rate_limit_exceeded"

  review:
    description: "评价与评分"
    events:
      - "review.created"
      - "review.updated"
      - "review.flagged"
      - "score.updated"
      - "feedback.structured_submitted"

  dispute:
    description: "争议与仲裁"
    events:
      - "dispute.created"
      - "dispute.evidence_submitted"
      - "dispute.escrow_frozen"
      - "dispute.resolved"
      - "dispute.closed"

required_events:
  - "payment.succeeded"
  - "payment.failed"
  - "escrow.released"
  - "settlement.paid"
  - "agent.execution_requested"
  - "agent.execution_blocked"
  - "agent.budget_exceeded"
  - "security.data_policy_violation"
  - "order.completed"
  - "dispute.created"

storage:
  app_log_path: "./logs/app.ndjson"
  audit_log_path: "./logs/audit.ndjson"
  security_log_path: "./logs/security.ndjson"
  rotate_daily: true
  compress_after_days: 7
```

---

## 4. Audit Event JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://aimart.example/schemas/audit_event.schema.json",
  "title": "AIMart Audit Event",
  "type": "object",
  "required": [
    "event_id",
    "event_type",
    "timestamp",
    "trace_id",
    "actor",
    "action",
    "resource",
    "result"
  ],
  "properties": {
    "event_id": {
      "type": "string"
    },
    "event_type": {
      "type": "string"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "trace_id": {
      "type": "string"
    },
    "session_id": {
      "type": "string"
    },
    "actor": {
      "type": "object",
      "required": ["actor_type", "actor_id"],
      "properties": {
        "actor_type": {
          "type": "string",
          "enum": ["human_buyer", "seller", "ai_agent", "channel_partner", "platform_operator", "platform_admin", "system"]
        },
        "actor_id": { "type": "string" },
        "organization_id": { "type": "string" },
        "role": { "type": "string" },
        "agent_id": { "type": "string" },
        "permission_level": { "type": "string" },
        "ip": { "type": "string" },
        "user_agent": { "type": "string" }
      }
    },
    "action": {
      "type": "string"
    },
    "resource": {
      "type": "object",
      "required": ["resource_type"],
      "properties": {
        "resource_type": { "type": "string" },
        "resource_id": { "type": "string" },
        "capability_id": { "type": "string" },
        "order_id": { "type": "string" },
        "requirement_id": { "type": "string" },
        "seller_id": { "type": "string" },
        "buyer_id": { "type": "string" }
      }
    },
    "result": {
      "type": "object",
      "required": ["status"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["success", "failure", "blocked", "pending_approval", "error"]
        },
        "decision_code": { "type": "string" },
        "reason": { "type": "string" },
        "error_code": { "type": "string" }
      }
    },
    "risk": {
      "type": "object",
      "properties": {
        "risk_level": {
          "type": "string",
          "enum": ["low", "medium", "high", "prohibited"]
        },
        "risk_flags": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "payment": {
      "type": "object",
      "properties": {
        "amount": { "type": "number" },
        "currency": { "type": "string" },
        "before_balance": { "type": "number" },
        "after_balance": { "type": "number" },
        "payment_id": { "type": "string" }
      }
    },
    "metadata": {
      "type": "object"
    },
    "hash": {
      "type": "string"
    },
    "previous_hash": {
      "type": "string"
    }
  }
}
```

---

## 5. 审计日志示例：Agent 搜索能力

```json
{
  "event_id": "evt_001",
  "event_type": "agent.capability_search",
  "timestamp": "2026-06-06T10:00:00Z",
  "trace_id": "trace_abc123",
  "actor": {
    "actor_type": "ai_agent",
    "actor_id": "agent_runtime_001",
    "organization_id": "org_001",
    "role": "agent_identity",
    "agent_id": "agent_procurement_001",
    "permission_level": "L1",
    "ip": "127.0.0.1",
    "user_agent": "AIMart-Agent/0.1"
  },
  "action": "search_capabilities",
  "resource": {
    "resource_type": "capability_search"
  },
  "result": {
    "status": "success",
    "decision_code": "ALLOWED",
    "reason": "Agent has L1 search permission"
  },
  "metadata": {
    "query": "企业知识库问答",
    "result_count": 12
  },
  "previous_hash": "prev_hash",
  "hash": "current_hash"
}
```

---

## 6. 审计日志示例：Agent 被阻止调用高风险能力

```json
{
  "event_id": "evt_002",
  "event_type": "agent.execution_blocked",
  "timestamp": "2026-06-06T10:05:00Z",
  "trace_id": "trace_def456",
  "actor": {
    "actor_type": "ai_agent",
    "actor_id": "agent_runtime_002",
    "organization_id": "org_001",
    "role": "agent_identity",
    "agent_id": "agent_procurement_001",
    "permission_level": "L4"
  },
  "action": "execute_capability",
  "resource": {
    "resource_type": "capability",
    "resource_id": "cap_legal_final_opinion_001",
    "capability_id": "cap_legal_final_opinion_001"
  },
  "result": {
    "status": "blocked",
    "decision_code": "HIGH_RISK_REQUIRES_HUMAN_APPROVAL",
    "reason": "Capability risk level is high and cannot be executed automatically by Agent"
  },
  "risk": {
    "risk_level": "high",
    "risk_flags": ["regulated_industry", "requires_human_review"]
  },
  "metadata": {
    "required_approval": true
  },
  "previous_hash": "prev_hash",
  "hash": "current_hash"
}
```

---

## 7. 审计日志示例：资金释放

```json
{
  "event_id": "evt_003",
  "event_type": "escrow.released",
  "timestamp": "2026-06-06T11:00:00Z",
  "trace_id": "trace_pay789",
  "actor": {
    "actor_type": "platform_operator",
    "actor_id": "ops_001",
    "role": "platform_auditor"
  },
  "action": "release_escrow",
  "resource": {
    "resource_type": "order",
    "resource_id": "order_001",
    "order_id": "order_001",
    "seller_id": "seller_001",
    "buyer_id": "buyer_001"
  },
  "result": {
    "status": "success",
    "decision_code": "MILESTONE_ACCEPTED",
    "reason": "Buyer accepted milestone 2"
  },
  "payment": {
    "amount": 3000,
    "currency": "CNY",
    "payment_id": "pay_001"
  },
  "metadata": {
    "milestone_id": "mile_002",
    "release_ratio": 0.3
  },
  "previous_hash": "prev_hash",
  "hash": "current_hash"
}
```

---

## 8. 哪些动作必须审计

必须审计：

```text
1. 用户登录、注册、角色变更
2. 商家入驻、审核、暂停、封禁
3. 能力商品创建、修改、上架、下架、审核
4. AgentCard 校验通过/失败
5. 买家发布需求、需求诊断、需求匹配
6. 商家报价、买家接受报价
7. 订单创建、付款、开始、交付、验收、完成
8. 担保资金创建、冻结、释放
9. 退款、结算、提现
10. AI Agent 搜索、读取、比较、报价、调用、反馈
11. 预算变更、权限变更
12. 风险检测、调用阻止、安全事件
13. 争议创建、证据提交、仲裁结论
14. 评价创建、评分变化
```

---

## 9. 最小验收标准

```text
1. 任意 API 请求产生 trace_id。
2. Agent 搜索能力必须写 audit event。
3. Agent 调用能力前的允许或拒绝必须写 audit event。
4. 支付、担保、退款、结算必须写 audit event。
5. 订单里程碑提交和验收必须写 audit event。
6. 审计日志包含 actor、action、resource、result。
7. 敏感字段不能明文进入日志。
8. 审计日志 append-only。
9. 普通管理员不能删除或修改审计日志。
10. 至少支持按 trace_id 查询完整事件链路。
```

---

## 10. 给 AI 编码助手的提示词

```text
请根据本 Markdown 生成：
1. config/audit_policy.yaml
2. schemas/audit_event.schema.json
3. audit_logger.py
4. audit 中间件，为每个 API 请求生成 trace_id
5. log_audit_event(event_type, actor, action, resource, result, metadata)
6. 敏感字段脱敏工具 mask_sensitive_fields(data)
7. 审计日志使用 NDJSON append-only 格式写入 logs/audit.ndjson

要求：
- 所有 Agent 行为必须记录。
- 所有资金行为必须记录。
- 所有权限变更必须记录。
- 所有风险阻止必须记录。
- 审计事件必须能按 trace_id 串联查询。
```
