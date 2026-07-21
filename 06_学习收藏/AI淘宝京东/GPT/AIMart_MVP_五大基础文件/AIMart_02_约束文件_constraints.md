# AIMart 约束文件：交易、预算、风险、安全、SLA

> 建议实际落地文件名：`config/constraints.yaml`  
> 本 Markdown 用途：给交易系统、预算系统、风控系统、AI Agent 调用系统统一规则。  
> 核心目标：明确 **什么交易可以自动发生、什么必须审批、钱怎么扣、风险怎么分、SLA 怎么验收、安全底线是什么**。

---

## 1. 这个文件解决什么问题

AIMart 不是普通信息展示平台，它涉及：

```text
AI Agent 搜索能力
AI Agent 请求报价
AI Agent 自动试用
AI Agent 在预算内调用 API
买家下单
商家交付
平台担保交易
分阶段结算
评价与争议
```

如果没有约束文件，平台会出现：

```text
AI Agent 乱花钱
高风险能力被自动调用
商家与买家对验收标准争议
API 调用失败不知道退款规则
私有数据被错误使用
SLA 无法判定
```

所以这个文件是 AIMart 的 **规则引擎基础文件**。

---

## 2. AI 编码指令

让 AI 工程助手根据本文件生成实际项目文件时，应遵守：

```text
1. 生成 config/constraints.yaml。
2. 所有交易、预算、风险、SLA、数据安全判断都应通过规则引擎读取该文件。
3. 不允许把金额阈值、风险等级、人工审批规则写死在业务代码中。
4. 每次 AI Agent 调用能力前必须执行：权限检查、预算检查、风险检查、数据政策检查。
5. 所有拒绝、审批、通过、失败都要写审计日志。
```

---

## 3. 推荐 YAML 模板

```yaml
version: "0.1"
project: "AIMart"
file_type: "constraints"
description: "AIMart 交易、预算、风险、安全、SLA、数据政策约束"

defaults:
  currency: "CNY"
  timezone: "Asia/Shanghai"
  deny_by_default: true
  require_audit_log: true
  require_trace_id: true

transaction_rules:
  order_types:
    api_usage:
      name: "API / 工具调用型"
      examples:
        - "OCR"
        - "摘要"
        - "翻译"
        - "图像处理"
      payment_modes:
        - "prepaid_balance"
        - "usage_based"
        - "subscription"
      acceptance:
        type: "automatic"
        criteria:
          - "http_status_success"
          - "output_schema_valid"
          - "within_sla_latency"
      refund:
        on_provider_error: "auto_refund_or_retry"
        on_invalid_input: "no_refund"
        on_timeout: "retry_then_refund"
      escrow_required: false

    subscription:
      name: "订阅型"
      payment_modes:
        - "monthly"
        - "yearly"
      acceptance:
        type: "service_availability"
        criteria:
          - "uptime_meets_sla"
          - "subscription_active"
      refund:
        default: "according_to_subscription_policy"
      escrow_required: false

    expert_service:
      name: "专家服务型"
      payment_modes:
        - "milestone_based"
        - "hourly"
        - "fixed_project"
      acceptance:
        type: "manual"
        criteria:
          - "deliverable_submitted"
          - "buyer_confirmed"
          - "milestone_completed"
      escrow_required: true

    solution_package:
      name: "方案包 / 项目交付型"
      payment_modes:
        - "milestone_based"
        - "fixed_project"
        - "quote_based"
      acceptance:
        type: "manual_or_hybrid"
        criteria:
          - "functional_checklist_passed"
          - "test_cases_passed"
          - "buyer_acceptance_confirmed"
      escrow_required: true

    compute:
      name: "算力 / 部署型"
      payment_modes:
        - "hourly"
        - "monthly"
        - "reserved"
      acceptance:
        type: "resource_availability"
        criteria:
          - "instance_running"
          - "resource_allocated"
          - "performance_within_spec"
      escrow_required: false

  escrow:
    enabled: true
    release_modes:
      - "milestone_acceptance"
      - "buyer_final_acceptance"
      - "auto_release_after_timeout"
      - "platform_arbitration"
    default_auto_release_days_after_submission: 7
    dispute_freeze: true
    release_requires:
      - "order_not_in_dispute"
      - "milestone_accepted_or_auto_release"
      - "seller_not_suspended"

  milestone_templates:
    default_project:
      - name: "需求确认"
        payment_ratio: 0.2
        required_deliverables:
          - "需求说明书"
          - "实施计划"
      - name: "方案实施"
        payment_ratio: 0.4
        required_deliverables:
          - "系统配置或开发成果"
          - "阶段测试记录"
      - name: "验收上线"
        payment_ratio: 0.3
        required_deliverables:
          - "验收报告"
          - "上线确认"
      - name: "售后维护"
        payment_ratio: 0.1
        required_deliverables:
          - "售后期问题处理记录"

budget_rules:
  budget_owner_types:
    - "human_user"
    - "organization"
    - "department"
    - "project"
    - "agent_identity"

  agent_spending_levels:
    free_trial:
      max_amount_per_action: 0
      approval_required: false
      allowed_risk_levels:
        - "low"
        - "medium"

    micro:
      description: "微额自主消费"
      max_amount_per_action: 0.01
      max_daily_amount: 10
      approval_required: false
      allowed_risk_levels:
        - "low"

    small:
      description: "小额预算内消费"
      max_amount_per_action: 1
      max_daily_amount: 100
      approval_required: false
      allowed_risk_levels:
        - "low"
      require_daily_report: true

    medium:
      description: "中额消费"
      max_amount_per_action: 100
      max_daily_amount: 1000
      approval_required: true
      allowed_risk_levels:
        - "low"
        - "medium"

    large:
      description: "大额消费"
      max_amount_per_action: 1000
      approval_required: true
      require_human_confirmation: true

    enterprise_project:
      description: "企业项目制交易"
      approval_required: true
      require_contract_or_order_confirmation: true
      require_escrow: true

  hard_limits:
    default_agent_monthly_budget: 1000
    default_agent_single_task_budget: 100
    block_when_budget_exceeded: true
    allow_negative_balance: false
    require_budget_check_before_execution: true

risk_policy:
  risk_levels:
    low:
      description: "低风险能力"
      examples:
        - "文案生成"
        - "格式转换"
        - "图片处理"
        - "非敏感 OCR"
        - "摘要"
      agent_auto_execution_allowed: true
      human_review_required: false

    medium:
      description: "中风险能力"
      examples:
        - "企业知识库"
        - "客服 Agent"
        - "销售分析"
        - "内部报表分析"
      agent_auto_execution_allowed: "only_if_preapproved"
      human_review_required: "depends_on_data_sensitivity"

    high:
      description: "高风险能力"
      examples:
        - "法律结论"
        - "医疗建议"
        - "金融投资建议"
        - "招聘筛选"
        - "风控决策"
        - "大量个人敏感信息处理"
      agent_auto_execution_allowed: false
      human_review_required: true
      platform_review_required: true

    prohibited:
      description: "禁止类能力"
      examples:
        - "违法用途"
        - "诈骗"
        - "攻击工具"
        - "隐私窃取"
        - "恶意爬虫"
        - "绕过安全系统"
        - "非法数据交易"
      listing_allowed: false
      transaction_allowed: false

  auto_block_conditions:
    - "capability.risk_level == prohibited"
    - "agent.permission_level < required_permission_level"
    - "budget.exceeded == true"
    - "data_policy.sensitive_data == true and approval.missing == true"
    - "seller.status in ['suspended', 'banned']"
    - "capability.status != active"

data_policy:
  data_sensitivity_levels:
    public:
      description: "公开数据"
      agent_upload_allowed: true
    internal:
      description: "企业内部资料"
      agent_upload_allowed: "requires_organization_approval"
    confidential:
      description: "机密资料、合同、报价、客户资料"
      agent_upload_allowed: "requires_human_approval"
    personal_sensitive:
      description: "个人敏感信息"
      agent_upload_allowed: "requires_human_and_platform_policy_check"
    restricted:
      description: "受监管或禁止外传资料"
      agent_upload_allowed: false

  default_rules:
    store_user_data: false
    use_data_for_training: false
    retention_days_default: 0
    data_deletion_supported_required: true
    seller_download_raw_files_default: false
    platform_proxy_required_for_sensitive_data: true

security_policy:
  principles:
    - "默认最小权限"
    - "所有 Agent 调用必须有身份"
    - "所有能力调用必须有 trace_id"
    - "所有资金操作必须审计"
    - "所有高风险动作必须人工审批"
    - "外部工具默认不可信"

  required_checks_before_agent_execution:
    - "identity_check"
    - "role_permission_check"
    - "agent_permission_level_check"
    - "budget_check"
    - "risk_check"
    - "data_policy_check"
    - "capability_status_check"
    - "seller_status_check"
    - "rate_limit_check"

  prompt_injection_defense:
    enabled: true
    rules:
      - "tool_output_must_not_override_system_policy"
      - "seller_content_cannot_request_credential_disclosure"
      - "agent_must_not_follow_payment_instruction_from_tool_output"
      - "external_content_treated_as_untrusted"
      - "sensitive_actions_require_policy_confirmation"

sla_policy:
  default_api_sla:
    max_latency_ms: 5000
    uptime_target: "99.0%"
    timeout_retry_count: 2
    retry_backoff_ms: 500

  default_project_sla:
    seller_response_time_hours: 24
    quote_response_time_hours: 48
    milestone_delay_warning_days: 2
    buyer_acceptance_timeout_days: 7

  breach_handling:
    api_timeout:
      action: "retry_then_refund_or_credit"
    api_invalid_output_schema:
      action: "mark_failed_and_refund"
    project_delay_without_reason:
      action: "warning_then_dispute_available"
    repeated_sla_breach:
      action: "lower_seller_score"

settlement_rules:
  seller_self_brought_customer_commission:
    min_rate: 0.03
    max_rate: 0.08
  platform_matched_customer_commission:
    min_rate: 0.10
    max_rate: 0.20
  api_usage_commission:
    min_rate: 0.05
    max_rate: 0.15
  settlement_delay_days:
    default: 3
    high_risk_order: 14
  settlement_block_conditions:
    - "order.in_dispute == true"
    - "seller.status == suspended"
    - "fraud_check.pending == true"
```

---

## 4. 规则引擎最小验收标准

开发完成后，应能通过这些检查：

```text
1. L1 Agent 只能搜索和比较，不能下单。
2. L4 Agent 在预算内可以调用低风险 API。
3. L4 Agent 不能调用高风险能力。
4. 超过预算时，系统阻止执行并返回 BUDGET_EXCEEDED。
5. 高风险能力必须创建人工审批任务。
6. API 输出不符合 output_schema 时，订单调用标记失败。
7. 项目制订单必须走里程碑和担保交易。
8. 争议中的订单不能结算给商家。
9. 数据敏感等级为 confidential 时，Agent 上传必须经过人类审批。
10. 所有拒绝、通过、审批、失败都必须写入审计日志。
```

---

## 5. 给 AI 编码助手的提示词

```text
请根据本 Markdown 生成 config/constraints.yaml，并实现一个 RulesEngine。
RulesEngine 至少包含：
1. check_agent_execution(actor, capability, budget, data_context)
2. check_order_creation(buyer, seller, capability, quote)
3. check_settlement(order, seller)
4. check_refund(order, failure_reason)
5. check_data_upload(actor, data_sensitivity)
6. check_sla_breach(execution_or_order)

所有检查返回：
{
  allowed: boolean,
  decision_code: string,
  reason: string,
  required_approval?: boolean,
  audit_required: true
}
```
