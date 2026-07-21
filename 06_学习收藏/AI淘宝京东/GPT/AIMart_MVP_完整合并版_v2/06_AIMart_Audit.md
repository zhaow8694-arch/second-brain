<!-- AIMart 完整合并版 v2：保留原始文件内容，并追加 Codex MVP 落地补充。生成日期：2026-06-06 -->

# AIMart 日志与审计文件：确保每一步可追溯

> 版本：v1.0 | 2026-06-07 | 状态：设计阶段

---

## 一、设计原则

### 1.1 核心原则

| 原则 | 说明 |
|------|------|
| **全程可追溯** | 从 Agent 搜索到最终结算，每一步操作都产生审计日志 |
| **不可篡改** | 审计日志采用追加写入 + 哈希链校验，任何篡改都可检测 |
| **最小必要** | 日志只记录业务操作和合规必需的数据，不记录业务内容（如输入文本） |
| **分层存储** | 热数据（7天）→ 温数据（90天）→ 冷数据（365天），按访问频率分存储层 |
| **隐私保护** | Agent 上下文数据不记入日志，只记录数据元信息（类型、大小、敏感度） |

### 1.2 日志生命周期

```
生成 → 采集 → 验证 → 存储 → 索引 → 查询 → 归档 → 销毁
 0ms   <1s    <1s    <1s    <5s    实时   按策略   按法规
```

---

## 二、日志分类与 Schema

### 2.1 日志分类

| 日志类别 | 日志 ID 前缀 | 保留期限 | 存储层 | 用途 |
|---------|-------------|---------|--------|------|
| 身份日志 | LOG-ID | 365 天 | 冷 | 身份操作审计 |
| 商品日志 | LOG-CT | 365 天 | 冷 | 商品上架/更新/下架审计 |
| 搜索日志 | LOG-SR | 30 天 | 温 | 搜索行为分析、推荐优化 |
| 交易日志 | LOG-EX | 365 天 | 温 | 交易全流程审计 |
| 支付日志 | LOG-PY | 365 天 | 冷 | 支付结算审计、合规 |
| 信任日志 | LOG-TR | 365 天 | 冷 | 信任评分变更审计 |
| 安全日志 | LOG-SC | 365 天 | 冷 | 安全事件审计 |
| 系统日志 | LOG-SY | 90 天 | 温 | 系统运行监控 |

### 2.2 通用日志 Schema

所有日志条目共享以下基础结构：

```json
{
  "log_id": "uuid",
  "log_type": "LOG-{category}-{event}",
  "timestamp": "2026-06-07T03:00:00.000Z",
  "trace_id": "uuid",
  "span_id": "uuid",
  "previous_hash": "sha256-of-previous-log-entry",

  "actor": {
    "actor_type": "agent | owner | provider | platform | certifier | facilitator | system",
    "actor_id": "uuid",
    "actor_name": "string",
    "session_id": "uuid"
  },

  "action": {
    "operation": "string",
    "target_type": "string",
    "target_id": "uuid",
    "result": "success | failure | pending",
    "error_code": "string | null",
    "error_message": "string | null"
  },

  "context": {
    "ip_address": "string (hashed)",
    "user_agent": "string (hashed for agents)",
    "api_version": "string",
    "environment": "dev | staging | prod"
  },

  "data_hash": "sha256-of-data-field",
  "data": {}
}
```

### 2.3 哈希链机制

```python
# 日志哈希链伪代码
class AuditLogEntry:
    def compute_hash(self):
        payload = f"{self.log_id}|{self.timestamp}|{self.actor_id}|{self.action}|{self.data_hash}|{self.previous_hash}"
        return sha256(payload.encode()).hexdigest()

# 验证链完整性
def verify_chain(entries: list[AuditLogEntry]) -> bool:
    for i in range(1, len(entries)):
        if entries[i].previous_hash != entries[i-1].compute_hash():
            return False  # 链断裂 = 篡改嫌疑
    return True

# 每 10000 条日志生成一个检查点（checkpoint）
# 检查点包含：起始/结束 log_id、起始/结束 hash、条目数、整体 merkle root
# 检查点写入区块链（可选，用于更高安全等级）
```

---

## 三、各类日志详细 Schema

### 3.1 身份日志（LOG-ID）

```json
// LOG-ID-REGISTER：参与者注册
{
  "log_type": "LOG-ID-REGISTER",
  "data": {
    "participant_type": "owner | provider | certifier | facilitator",
    "participant_id": "uuid",
    "jurisdiction": "CN",
    "kyc_method": "email | phone | id_document",
    "registration_source": "web | api | invitation"
  }
}

// LOG-ID-AGENT-REGISTER：Agent 注册
{
  "log_type": "LOG-ID-AGENT-REGISTER",
  "data": {
    "agent_id": "uuid",
    "owner_id": "uuid",
    "framework": "langchain",
    "initial_spending_authority": "L0"
  }
}

// LOG-ID-AGENT-TERMINATE：Agent 注销
{
  "log_type": "LOG-ID-AGENT-TERMINATE",
  "data": {
    "agent_id": "uuid",
    "owner_id": "uuid",
    "reason": "owner_request | policy_violation | inactivity",
    "active_orders_frozen": 3,
    "remaining_budget_returned_cny": 1500.00
  }
}

// LOG-ID-AUTH-FAILURE：认证失败
{
  "log_type": "LOG-ID-AUTH-FAILURE",
  "data": {
    "attempted_actor_id": "uuid",
    "failure_reason": "invalid_token | expired_token | revoked_key | mfa_required",
    "source_ip_hash": "sha256",
    "attempt_count_last_hour": 5
  }
}

// LOG-ID-KEY-ROTATE：密钥轮换
{
  "log_type": "LOG-ID-KEY-ROTATE",
  "data": {
    "actor_id": "uuid",
    "key_type": "api_key | oauth_token | mtls_cert",
    "rotation_reason": "scheduled | suspicious_activity | compromise_suspected"
  }
}
```

### 3.2 商品日志（LOG-CT）

```json
// LOG-CT-LIST：商品上架
{
  "log_type": "LOG-CT-LIST",
  "data": {
    "item_id": "uuid",
    "provider_id": "uuid",
    "item_type": "model | skill | expert | compute",
    "item_name": "ContractGuard-Law-v2",
    "item_version": "2.3.1",
    "pricing_model": "per_call",
    "price_per_call_cny": 0.05,
    "verification_status": "pending | passed | failed",
    "verification_duration_seconds": 180,
    "security_scan_result": "clean | warning | failed"
  }
}

// LOG-CT-UPDATE：商品更新
{
  "log_type": "LOG-CT-UPDATE",
  "data": {
    "item_id": "uuid",
    "old_version": "2.3.0",
    "new_version": "2.3.1",
    "change_type": "patch | minor | major",
    "changed_fields": ["performance_declaration", "pricing"],
    "requires_reverification": true,
    "active_subscriptions_affected": 42
  }
}

// LOG-CT-DELIST：商品下架
{
  "log_type": "LOG-CT-DELIST",
  "data": {
    "item_id": "uuid",
    "reason": "provider_request | trust_score_below_threshold | policy_violation | verification_failed",
    "active_subscriptions_affected": 42,
    "grace_period_end_date": "2026-06-14"
  }
}
```

### 3.3 搜索日志（LOG-SR）

```json
// LOG-SR-QUERY：搜索请求
{
  "log_type": "LOG-SR-QUERY",
  "data": {
    "query_id": "uuid",
    "agent_id": "uuid",
    "query_domains": ["legal", "contract_review"],
    "query_languages": ["zh-CN"],
    "result_count": 7,
    "top_result_item_id": "uuid",
    "top_result_match_score": 0.94,
    "response_time_ms": 120,
    "search_index_version": "2026-06-06-001"
  }
}

// LOG-SR-TRIAL：试用请求
{
  "log_type": "LOG-SR-TRIAL",
  "data": {
    "trial_id": "uuid",
    "agent_id": "uuid",
    "item_id": "uuid",
    "query_id": "uuid",
    "trial_result": "purchased | rejected | inconclusive",
    "trial_duration_seconds": 15,
    "trial_calls_made": 3,
    "trial_effect_score": 4
  }
}
```

### 3.4 交易日志（LOG-EX）

```json
// LOG-EX-ORDER-CREATE：订单创建
{
  "log_type": "LOG-EX-ORDER-CREATE",
  "data": {
    "order_id": "uuid",
    "agent_id": "uuid",
    "owner_id": "uuid",
    "item_id": "uuid",
    "provider_id": "uuid",
    "item_type": "model",
    "pricing_plan": "per_call",
    "quantity": 1,
    "amount_cny": 0.05,
    "authorization_level_required": "L0",
    "escrow_enabled": true,
    "query_id": "uuid",
    "trial_id": "uuid | null"
  }
}

// LOG-EX-ORDER-AUTHORIZE：订单授权
{
  "log_type": "LOG-EX-ORDER-AUTHORIZE",
  "data": {
    "order_id": "uuid",
    "authorization_type": "agent_auto | agent_l1_notification | owner_approved | owner_confirmed",
    "authorizer_id": "uuid",
    "authorization_latency_ms": 5,
    "budget_pool_id": "uuid",
    "budget_balance_before_cny": 5000.00,
    "budget_balance_after_cny": 4999.95
  }
}

// LOG-EX-ORDER-EXPIRE：订单过期
{
  "log_type": "LOG-EX-ORDER-EXPIRE",
  "data": {
    "order_id": "uuid",
    "reason": "payment_timeout | authorization_timeout",
    "age_seconds": 30
  }
}

// LOG-EX-DELIVERY：能力交付
{
  "log_type": "LOG-EX-DELIVERY",
  "data": {
    "order_id": "uuid",
    "delivery_method": "api_call | weight_download | code_package | instance",
    "delivery_endpoint": "https://api.aimart.dev/v1/...",
    "delivery_latency_ms": 200,
    "input_data_size_bytes": 5000,
    "output_data_size_bytes": 2000,
    "input_sensitivity_level": "confidential",
    "data_residency": "CN"
  }
}

// LOG-EX-EFFECT-REPORT：效果回传
{
  "log_type": "LOG-EX-EFFECT-REPORT",
  "data": {
    "report_id": "uuid",
    "order_id": "uuid",
    "agent_id": "uuid",
    "success": true,
    "effect_score": 4,
    "actual_latency_ms": 980,
    "declared_latency_ms": 1500,
    "latency_within_sla": true,
    "declaration_accuracy": 0.92,
    "trust_score_before": 82,
    "trust_score_after": 82.3,
    "trust_score_delta": 0.3
  }
}

// LOG-EX-DISPUTE：争议事件
{
  "log_type": "LOG-EX-DISPUTE",
  "data": {
    "dispute_id": "uuid",
    "order_id": "uuid",
    "initiator_type": "agent | owner | provider",
    "initiator_id": "uuid",
    "dispute_type": "quality | sla_violation | unauthorized_charge | false_declaration",
    "disputed_amount_cny": 50.00,
    "fund_status": "frozen",
    "evidence_hash": "sha256"
  }
}

// LOG-EX-ARBITRATION：仲裁结果
{
  "log_type": "LOG-EX-ARBITRATION",
  "data": {
    "dispute_id": "uuid",
    "arbitration_result": "buyer_wins | seller_wins | split | dismissed",
    "refund_amount_cny": 50.00,
    "provider_trust_score_delta": -5,
    "arbitration_duration_hours": 48,
    "arbitrator": "platform | human_arbitrator"
  }
}
```

### 3.5 支付日志（LOG-PY）

```json
// LOG-PY-BUDGET-CREATE：预算池创建
{
  "log_type": "LOG-PY-BUDGET-CREATE",
  "data": {
    "budget_pool_id": "uuid",
    "owner_id": "uuid",
    "currency": "CNY",
    "initial_balance_cny": 10000.00,
    "total_cap_cny": 50000.00,
    "daily_max_cny": 2000.00
  }
}

// LOG-PY-BUDGET-RECHARGE：预算充值
{
  "log_type": "LOG-PY-BUDGET-RECHARGE",
  "data": {
    "budget_pool_id": "uuid",
    "owner_id": "uuid",
    "recharge_amount_cny": 5000.00,
    "balance_before_cny": 2000.00,
    "balance_after_cny": 7000.00,
    "payment_method": "bank_transfer | credit_card | crypto"
  }
}

// LOG-PY-SETTLE-X402：x402 结算
{
  "log_type": "LOG-PY-SETTLE-X402",
  "data": {
    "order_id": "uuid",
    "amount_usdc": "0.007",
    "chain": "base",
    "facilitator_id": "uuid",
    "transaction_hash": "0xabc123...",
    "settlement_latency_ms": 3200,
    "gas_paid_by_facilitator": true,
    "block_number": 12345678
  }
}

// LOG-PY-SETTLE-ACP：ACP 结算
{
  "log_type": "LOG-PY-SETTLE-ACP",
  "data": {
    "order_id": "uuid",
    "amount_cny": 50.00,
    "spt_token_id": "uuid",
    "spt_remaining_limit_cny": 950.00,
    "settlement_status": "confirmed"
  }
}

// LOG-PY-ESCROW-FREEZE：担保冻结
{
  "log_type": "LOG-PY-ESCROW-FREEZE",
  "data": {
    "order_id": "uuid",
    "escrow_account_id": "uuid",
    "frozen_amount_cny": 50.00,
    "freeze_reason": "awaiting_effect_confirmation"
  }
}

// LOG-PY-ESCROW-RELEASE：担保释放
{
  "log_type": "LOG-PY-ESCROW-RELEASE",
  "data": {
    "order_id": "uuid",
    "escrow_account_id": "uuid",
    "release_amount_cny": 50.00,
    "release_to": "provider_id-uuid",
    "release_reason": "effect_confirmed | dispute_resolved_buyer_partial | timeout_default",
    "platform_commission_cny": 2.50,
    "provider_received_cny": 47.50
  }
}

// LOG-PY-ESCROW-REFUND：担保退款
{
  "log_type": "LOG-PY-ESCROW-REFUND",
  "data": {
    "order_id": "uuid",
    "escrow_account_id": "uuid",
    "refund_amount_cny": 50.00,
    "refund_to": "budget_pool_id-uuid",
    "refund_reason": "effect_not_achieved | dispute_resolved_buyer_wins",
    "provider_penalty_cny": 0
  }
}

// LOG-PY-ANOMALY：支付异常
{
  "log_type": "LOG-PY-ANOMALY",
  "data": {
    "anomaly_type": "burst_spend | high_frequency_micro | budget_depleted | single_seller_concentration | off_hours_large",
    "agent_id": "uuid",
    "budget_pool_id": "uuid",
    "detection_details": {
      "spend_last_hour_cny": 1200.00,
      "daily_limit_cny": 2000.00,
      "pct_of_daily_limit": 0.60
    },
    "auto_action_taken": "agent_suspended | rate_limited | notification_sent | no_action",
    "owner_notified": true
  }
}
```

### 3.6 信任日志（LOG-TR）

```json
// LOG-TR-SCORE-UPDATE：信任评分更新
{
  "log_type": "LOG-TR-SCORE-UPDATE",
  "data": {
    "item_id": "uuid",
    "score_before": 82.0,
    "score_after": 82.3,
    "delta": 0.3,
    "update_trigger": "effect_report | benchmark_update | certification | peer_review | dispute_result",
    "trigger_reference_id": "report_id | dispute_id | cert_id",
    "score_composition": {
      "benchmark_component": 24.5,
      "effect_report_component": 41.0,
      "peer_review_component": 12.3,
      "certification_component": 4.5
    }
  }
}

// LOG-TR-DELIST-TRIGGER：信任评分触发下架
{
  "log_type": "LOG-TR-DELIST-TRIGGER",
  "data": {
    "item_id": "uuid",
    "score_at_trigger": 28.5,
    "delist_threshold": 30,
    "consecutive_low_score_days": 7,
    "active_subscriptions_at_trigger": 15
  }
}

// LOG-TR-CERTIFICATION：认证事件
{
  "log_type": "LOG-TR-CERTIFICATION",
  "data": {
    "item_id": "uuid",
    "certifier_id": "uuid",
    "certification_level": "platform_certified | premium_certified",
    "valid_from": "2026-06-01",
    "valid_until": "2026-12-01",
    "score_boost": 3.0
  }
}
```

### 3.7 安全日志（LOG-SC）

```json
// LOG-SC-SANDBOX-VIOLATION：沙箱违规
{
  "log_type": "LOG-SC-SANDBOX-VIOLATION",
  "data": {
    "trial_id": "uuid",
    "item_id": "uuid",
    "provider_id": "uuid",
    "violation_type": "unauthorized_network_access | file_system_escape | resource_limit_exceeded | data_exfiltration_attempt",
    "violation_details": "Attempted connection to external IP 203.0.113.42 not in whitelist",
    "action_taken": "skill_terminated | provider_suspended | provider_banned",
    "agents_affected": 3
  }
}

// LOG-SC-DATA-LEAK：数据泄露嫌疑
{
  "log_type": "LOG-SC-DATA-LEAK",
  "data": {
    "agent_id": "uuid",
    "item_id": "uuid",
    "suspicion_type": "context_data_in_output | unexpected_data_transmission",
    "data_sensitivity_level": "confidential",
    "action_taken": "item_suspended | agent_suspended | investigation_opened",
    "owner_notified": true
  }
}

// LOG-SC-FRAUD-DETECT：欺诈检测
{
  "log_type": "LOG-SC-FRAUD-DETECT",
  "data": {
    "fraud_type": "review_manipulation | price_manipulation | sybil_attack | wash_trading",
    "suspected_participant_id": "uuid",
    "participant_type": "provider | agent",
    "evidence_summary": "3 agents from same owner all rating same item 5 stars within 5 minutes",
    "action_taken": "ratings_invalidated | participant_suspended | investigation_opened"
  }
}
```

---

## 四、审计查询接口

### 4.1 查询 API

```yaml
# 审计查询接口
POST /api/v1/audit/query:
  description: 查询审计日志
  auth: owner_token | provider_token | platform_token | regulator_token
  request:
    filters:
      log_types: string[]           # 日志类型过滤
      actor_id: uuid                # 特定参与者
      target_id: uuid               # 特定目标对象
      date_from: datetime
      date_to: datetime
      result: "success | failure"   # 操作结果过滤
    pagination:
      offset: integer
      limit: integer (max 100)
    sort:
      field: "timestamp"
      order: "desc"
  response:
    entries: array[AuditLogEntry]
    total_count: integer
    chain_integrity_verified: boolean  # 本次查询范围内链完整性

GET /api/v1/audit/trace/{trace_id}:
  description: 按追踪ID查询完整交易链路
  auth: any_authenticated (involved party only)
  response:
    trace_id: uuid
    entries: array[AuditLogEntry]  # 按 timestamp 排序
    timeline:
      - event: "search_query"
        timestamp: "..."
        log_id: "..."
      - event: "trial_start"
        timestamp: "..."
        log_id: "..."
      - event: "order_create"
        timestamp: "..."
        log_id: "..."
      - event: "payment_settle"
        timestamp: "..."
        log_id: "..."
      - event: "delivery"
        timestamp: "..."
        log_id: "..."
      - event: "effect_report"
        timestamp: "..."
        log_id: "..."

GET /api/v1/audit/checkpoint/{date}:
  description: 获取指定日期的哈希链检查点
  auth: platform_token | regulator_token
  response:
    date: date
    first_log_id: uuid
    last_log_id: uuid
    entry_count: integer
    merkle_root: string
    previous_checkpoint_hash: string

POST /api/v1/audit/verify:
  description: 验证指定范围的日志链完整性
  auth: platform_token | regulator_token
  request:
    date_from: date
    date_to: date
  response:
    verified: boolean
    total_entries_checked: integer
    broken_at_log_id: uuid | null
    broken_at_timestamp: datetime | null
```

### 4.2 权限矩阵

| 查询者 | 可查询范围 | 可见字段 |
|--------|-----------|---------|
| Agent Owner | 所属 Agent 的所有日志 | 全部（除其他 Owner 的预算数据） |
| AI Agent | 自身的操作日志 | 全部（除 Owner 预算详情、其他 Agent 数据） |
| Provider | 自身商品的交易日志 | 交易量、评价、争议（不含买方身份和上下文） |
| Platform | 全部日志 | 全部 |
| Certifier | 认证相关日志 | 认证对象的基准测试、评分变更 |
| Facilitator | 结算相关日志 | 结算金额、时间、状态（不含业务内容） |
| Regulator | 全部日志（依法令） | 全部（需出示合规令状） |

---

## 五、审计场景

### 5.1 典型审计场景

#### 场景一：Agent 被诱导消费调查

```
触发：Owner 报告 Agent 异常消费
查询路径：
  1. LOG-PY-ANOMALY → 找到异常检测记录
  2. LOG-EX-ORDER-CREATE → 找到所有相关订单
  3. LOG-SR-QUERY → 检查搜索是否被操纵（搜索结果是否异常偏向某卖家）
  4. LOG-EX-EFFECT-REPORT → 检查效果回传是否正常（是否被篡改跳过）
  5. LOG-SC-FRAUD-DETECT → 检查是否有刷分/操纵行为
  6. 汇总：确认是否为诱导消费，确定责任方，执行赔偿
```

#### 场景二：卖家虚假声明调查

```
触发：Agent 效果回传与卖家声明偏差持续超过 20%
查询路径：
  1. LOG-TR-SCORE-UPDATE → 信任评分变化历史
  2. LOG-EX-EFFECT-REPORT → 所有效果回传记录
  3. LOG-CT-LIST → 商品上架时的声明数据
  4. 对比声明值与效果回传的实际值
  5. LOG-EX-DISPUTE → 相关争议记录
  6. 汇总：确认虚假声明程度，执行下架和保证金扣除
```

#### 场景三：沙箱逃逸安全事件

```
触发：沙箱监控检测到违规行为
查询路径：
  1. LOG-SC-SANDBOX-VIOLATION → 违规详情
  2. LOG-EX-ORDER-CREATE → 使用该技能的所有订单
  3. LOG-EX-DELIVERY → 检查是否有数据泄露
  4. LOG-SC-DATA-LEAK → 数据泄露嫌疑检查
  5. LOG-ID-AGENT-TERMINATE → 受影响 Agent 处理
  6. 汇总：评估影响范围，通知受影响 Owner，封禁 Provider
```

#### 场景四：合规审计（监管机构）

```
触发：监管机构依法令要求审计
查询路径：
  1. GET /api/v1/audit/checkpoint/{date} → 获取检查点
  2. POST /api/v1/audit/verify → 验证日志完整性
  3. 按需求查询特定时间范围、特定参与者的日志
  4. 验证关键业务流程合规性：
     - 所有交易是否有对应授权
     - 支付结算是否符合法规
     - 跨境数据传输是否合规
     - Agent 操作是否在授权范围内
```

### 5.2 交易全链路追踪

一笔完整交易的审计追踪示例：

```
[搜索阶段]
LOG-SR-QUERY    agent→market: 搜索"法律合同审查"能力
  └─ query_id: q-001, results: 7, top_match: item-001

[试用阶段]
LOG-SR-TRIAL    agent→item-001: 发起试用
  └─ trial_id: t-001, calls: 3, result: "purchased"

[下单阶段]
LOG-EX-ORDER-CREATE  agent→order: 创建订单
  └─ order_id: o-001, amount: 0.05 CNY, auth_level: L0

[授权阶段]
LOG-EX-ORDER-AUTHORIZE  agent_auto: L0 自动授权
  └─ authorizer: agent-001, latency: 5ms

[支付阶段]
LOG-PY-ESCROW-FREEZE   budget_pool: 冻结担保资金
  └─ frozen: 0.05 CNY
LOG-PY-SETTLE-X402     x402: 链上微支付结算
  └─ tx_hash: 0xabc..., latency: 3200ms

[交付阶段]
LOG-EX-DELIVERY   provider→agent: 能力交付
  └─ method: api_call, latency: 200ms

[回传阶段]
LOG-EX-EFFECT-REPORT  agent→trust: 效果回传
  └─ success: true, score: 4, latency_within_sla: true

[评分阶段]
LOG-TR-SCORE-UPDATE   trust: 评分更新
  └─ 82.0 → 82.3, trigger: effect_report

[释放阶段]
LOG-PY-ESCROW-RELEASE  escrow: 担保资金释放
  └─ provider_received: 0.0485 CNY, commission: 0.0015 CNY

全程追踪：trace_id = tr-001 (串联以上所有日志)
```

---

## 六、合规与保留策略

### 6.1 数据保留

| 数据类型 | 保留期限 | 到期处理 | 法规依据 |
|---------|---------|---------|---------|
| 交易记录 | 5 年 | 匿名化归档 | 电商法规 |
| 支付记录 | 5 年 | 匿名化归档 | 金融法规 |
| 身份认证记录 | 5 年 | 删除 | 隐私法规 |
| 审计日志 | 365 天（热） → 5 年（冷） | 归档 | 合规要求 |
| 搜索日志 | 30 天 | 删除 | 最小必要原则 |
| 安全事件日志 | 5 年 | 匿名化归档 | 安全法规 |
| 争议记录 | 5 年 | 匿名化归档 | 电商法规 |

### 6.2 数据脱敏规则

```
DESENSITIZE-001: Agent 输入/输出内容不记入日志，只记元信息（大小、类型、敏感度）
DESENSITIZE-002: IP 地址存储时使用 SHA-256 哈希，不存原始 IP
DESENSITIZE-003: 预算余额信息对非 Owner 参与者不可见
DESENSITIZE-004: 争议证据中的业务内容按需提供，审计日志只记哈希
DESENSITIZE-005: 日志归档时，Agent 的 framework 和能力范围信息做匿名化处理
DESENSITIZE-006: 跨境日志查询必须经过双重合规验证（源法域 + 目标法域）
```

### 6.3 审计报告

```
自动生成周期：
  - 日报：异常事件汇总、交易量统计
  - 周报：信任评分变动、争议处理统计、安全事件统计
  - 月报：合规状态、SLA 达标率、资金流向分析
  - 季报：平台运营审计报告（提交监管机构）

报告访问权限：
  - 日报/周报：Platform 运维团队
  - 月报：Platform 管理层 + 参与者（自身数据）
  - 季报：Platform 管理层 + Regulator
```

---

# v2.0 落地补充：新增审计事件与 Codex 验收要求

## 1. 必须新增事件类型

```yaml
agent_maturity_events:
  - "agent.maturity_check_passed"
  - "agent.maturity_check_failed"
  - "agent.sandbox_required"
  - "agent.production_ready_required"

compliance_events:
  - "compliance.cross_border_data_blocked"
  - "compliance.local_storage_required"
  - "compliance.data_region_unknown"
  - "compliance.owner_approval_required"

compute_finance_events:
  - "compute.derivative_attempt_blocked"
  - "compute.financial_license_required"

mvp_guardrail_events:
  - "mvp.real_payment_blocked"
  - "mvp.high_risk_auto_execution_blocked"
  - "mvp.agent_auto_purchase_blocked"

self_review_events:
  - "codex.self_review_started"
  - "codex.self_review_completed"
  - "codex.test_run_started"
  - "codex.test_run_completed"
```

## 2. 审计事件必须覆盖的拒绝场景

```text
1. Agent 成熟度不足。
2. Agent 预算不足。
3. Agent 尝试调用高风险能力。
4. dev/MVP 环境尝试真实支付。
5. 跨境数据交易被阻止。
6. 算力金融衍生品交易被阻止。
7. AgentCard 校验失败。
8. 订单结算被阻止。
9. 争议订单资金冻结。
```

## 3. Codex 实现要求

MVP 可以先用本地 NDJSON，不强制 ClickHouse/Kafka。

```text
1. 审计日志必须 append-only。
2. 每个请求必须有 trace_id。
3. 每个 Agent 行为必须写日志。
4. 每个资金动作必须写日志。
5. 每个规则拒绝必须写日志。
6. 敏感字段必须脱敏。
7. 测试必须验证审计日志写入。
```

