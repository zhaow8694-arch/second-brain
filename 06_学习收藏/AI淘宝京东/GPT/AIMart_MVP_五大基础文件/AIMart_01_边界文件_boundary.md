# AIMart 边界文件：参与者、角色、权限、业务领域

> 建议实际落地文件名：`config/boundaries.yaml`  
> 本 Markdown 用途：给产品、后端、前端、AI Agent、规则引擎统一边界。  
> 核心目标：明确 **谁能做什么、谁不能做什么、业务模块归谁负责、能力商品属于什么类型、AI Agent 的权限边界在哪里**。

---

## 1. 这个文件解决什么问题

AIMart 是多边市场，参与者很多：

```text
商家、买家、AI Agent、渠道方、平台运营、审核员、仲裁员、管理员。
```

如果没有边界文件，后续编码会出现问题：

```text
商家能不能直接改订单？
AI Agent 能不能直接付款？
渠道方能不能看到买家数据？
平台运营能不能查看企业上传文件？
专家服务和 API 商品是不是同一套交易规则？
哪些类目属于高风险？
```

所以这个文件是 AIMart 的 **身份与边界总约束**。

---

## 2. AI 编码指令

让 AI 工程助手根据本文件生成实际项目文件时，应遵守：

```text
1. 生成 config/boundaries.yaml。
2. 不要把权限写死在业务代码里。
3. 后端所有 API 鉴权必须读取 boundaries.yaml 或由它初始化到数据库。
4. AI Agent 的权限必须单独建模，不允许复用普通用户权限。
5. 角色权限、业务领域、能力类型、模块边界必须可扩展。
6. 未显式允许的动作，默认禁止。
```

---

## 3. 推荐 YAML 模板

```yaml
version: "0.1"
project: "AIMart"
file_type: "boundary"
description: "AIMart 平台参与者、角色、权限、业务领域与模块边界定义"

principles:
  - "战略上不限制客户、行业和能力类型；执行上必须限制权限、交易规则和风险边界。"
  - "未显式允许的权限默认禁止。"
  - "AI Agent 不是法律主体，必须绑定自然人或企业组织。"
  - "商家可以带客户，但交易、评价、履约数据必须沉淀在平台。"
  - "平台不直接生产 AI 产品，但负责交易规则、能力标准、信任评价和安全治理。"

participant_types:
  human_buyer:
    name: "人类买家"
    description: "个人、团队或企业用户，购买 AI 能力或发布需求"
    examples:
      - "个人 AI 使用者"
      - "企业客户"
      - "工厂"
      - "电商团队"
      - "内容团队"
      - "咨询公司"
    can:
      - "浏览能力商品"
      - "发布需求"
      - "请求报价"
      - "下单"
      - "验收交付"
      - "评价商家与商品"
      - "设置企业预算和审批规则"
    cannot:
      - "修改商家能力卡片"
      - "绕过平台结算"
      - "查看其他买家的私有数据"
      - "代替平台仲裁争议"

  seller:
    name: "能力供给方 / 商家"
    description: "出售 AI 能力、服务、API、模型、专家、算力或方案包的供给方"
    examples:
      - "AI 服务商"
      - "Agent 开发者"
      - "模型/API 提供商"
      - "系统集成商"
      - "行业专家"
      - "算力供应商"
      - "SaaS 厂商"
      - "数据服务团队"
    can:
      - "申请入驻"
      - "开店"
      - "上架能力商品"
      - "填写 AgentCard"
      - "接收客户需求"
      - "提交报价"
      - "管理订单交付"
      - "提交交付物"
      - "申请结算"
    cannot:
      - "伪造平台评分"
      - "删除历史订单审计记录"
      - "查看未授权买家数据"
      - "绕开平台收款并仍要求平台担保"
      - "上架禁止类能力"

  ai_agent:
    name: "AI Agent 买家 / 调用者"
    description: "代表人或企业搜索、比较、请求报价、调用能力的 AI 实体"
    examples:
      - "企业采购 Agent"
      - "个人助理 Agent"
      - "工作流自动化 Agent"
      - "SaaS 内嵌 Agent"
    must_bind_to:
      - "human_buyer"
      - "organization"
    can:
      - "读取公开能力信息"
      - "搜索能力"
      - "比较能力"
      - "生成采购建议"
      - "发起报价请求"
      - "在授权预算内调用低风险能力"
      - "提交结构化反馈"
    cannot:
      - "匿名下单"
      - "绕过预算限制"
      - "自动调用高风险能力"
      - "自动上传敏感数据，除非获得授权"
      - "自动签合同"
      - "自动进行大额付款"

  channel_partner:
    name: "渠道方"
    description: "引入客户或商家的合作方"
    examples:
      - "行业协会"
      - "产业园区"
      - "培训机构"
      - "咨询公司"
      - "自媒体"
      - "商家私域渠道"
    can:
      - "生成渠道链接"
      - "导入线索"
      - "查看自己来源的线索状态"
      - "查看分佣数据"
    cannot:
      - "查看非自己来源客户数据"
      - "干预平台仲裁"
      - "修改商家商品信息"

  platform_operator:
    name: "平台运营"
    description: "负责商家审核、商品审核、撮合、内容、案例和日常运营"
    can:
      - "审核商家"
      - "审核商品"
      - "协助能力包装"
      - "查看订单状态"
      - "处理普通运营问题"
    cannot:
      - "直接改动资金结算"
      - "导出敏感客户文件，除非获得高级授权"
      - "修改审计日志"

  platform_auditor:
    name: "平台审核 / 仲裁员"
    description: "负责纠纷处理、风控审核、安全事件调查"
    can:
      - "查看争议订单材料"
      - "冻结争议资金"
      - "给出仲裁建议"
      - "标记风险事件"
    cannot:
      - "私自释放资金"
      - "删除争议记录"
      - "越权访问无关订单"

  platform_admin:
    name: "平台管理员"
    description: "最高管理权限角色"
    can:
      - "管理系统配置"
      - "管理权限策略"
      - "处理安全事件"
      - "执行紧急冻结"
    cannot:
      - "删除审计日志"
      - "绕过双人审批执行高风险资金操作"

roles:
  buyer_owner:
    scope: "organization"
    description: "企业买方负责人"
    permissions:
      - "buyer.requirement.create"
      - "buyer.order.create"
      - "buyer.order.approve"
      - "buyer.budget.manage"
      - "agent.identity.create"
      - "agent.permission.manage"

  buyer_member:
    scope: "organization"
    description: "企业买方成员"
    permissions:
      - "buyer.requirement.create"
      - "buyer.capability.search"
      - "buyer.quote.request"
      - "buyer.order.view"

  seller_owner:
    scope: "store"
    description: "商家店铺负责人"
    permissions:
      - "seller.store.manage"
      - "seller.capability.create"
      - "seller.capability.update"
      - "seller.quote.create"
      - "seller.order.manage"
      - "seller.settlement.request"

  seller_operator:
    scope: "store"
    description: "商家运营成员"
    permissions:
      - "seller.capability.create"
      - "seller.capability.update"
      - "seller.quote.create"
      - "seller.order.view"
      - "seller.delivery.submit"

  channel_owner:
    scope: "channel"
    description: "渠道负责人"
    permissions:
      - "channel.link.create"
      - "channel.lead.view"
      - "channel.commission.view"

  agent_identity:
    scope: "organization"
    description: "AI Agent 身份"
    permissions:
      - "agent.capability.search"
      - "agent.capability.read"
      - "agent.capability.compare"
      - "agent.quote.request"
      - "agent.feedback.submit"

  platform_ops:
    scope: "platform"
    description: "平台运营人员"
    permissions:
      - "platform.seller.review"
      - "platform.capability.review"
      - "platform.requirement.match"
      - "platform.order.view"
      - "platform.content.manage"

  platform_auditor:
    scope: "platform"
    description: "平台审核与仲裁人员"
    permissions:
      - "platform.dispute.view"
      - "platform.dispute.freeze"
      - "platform.risk.review"
      - "platform.audit.view"

  platform_super_admin:
    scope: "platform"
    description: "平台超级管理员"
    permissions:
      - "*"

agent_permission_levels:
  L0:
    name: "只读公开信息"
    allowed_actions:
      - "agent.capability.search"
      - "agent.capability.read"
    requires_human_approval: false

  L1:
    name: "比较与推荐"
    allowed_actions:
      - "agent.capability.search"
      - "agent.capability.read"
      - "agent.capability.compare"
      - "agent.recommendation.generate"
    requires_human_approval: false

  L2:
    name: "发起报价"
    allowed_actions:
      - "agent.quote.request"
      - "agent.trial.request"
    requires_human_approval: false

  L3:
    name: "创建订单草案"
    allowed_actions:
      - "agent.order.draft_create"
    requires_human_approval: true

  L4:
    name: "预算内自动调用低风险能力"
    allowed_actions:
      - "agent.execution.run_low_risk"
      - "agent.payment.micro_spend"
    requires_human_approval: "depends_on_budget_and_risk"

  L5:
    name: "高风险或大额动作"
    allowed_actions:
      - "agent.execution.run_high_risk"
      - "agent.payment.large_spend"
      - "agent.data.upload_sensitive"
    requires_human_approval: true

business_domains:
  knowledge_management:
    name: "知识库 / RAG"
    default_risk: "medium"
  content_generation:
    name: "内容生成"
    default_risk: "low"
  customer_service:
    name: "客服 / 售后"
    default_risk: "medium"
  data_processing:
    name: "数据处理 / OCR / 摘要"
    default_risk: "low"
  workflow_automation:
    name: "工作流自动化"
    default_risk: "medium"
  model_api:
    name: "模型 / API"
    default_risk: "medium"
  compute:
    name: "算力 / 部署"
    default_risk: "medium"
  expert_service:
    name: "专家服务"
    default_risk: "medium"
  security_evaluation:
    name: "安全 / 评测"
    default_risk: "medium"
  solution_package:
    name: "行业方案包"
    default_risk: "medium"

capability_types:
  model:
    description: "模型 API、权重授权、私有部署、微调"
  api:
    description: "标准 API 能力，如 OCR、翻译、摘要、图像处理"
  agent:
    description: "可执行特定任务的 Agent"
  workflow:
    description: "Prompt、自动化流程、工作流模板"
  expert_service:
    description: "咨询、审核、部署、培训等人类专家服务"
  solution:
    description: "面向业务问题的组合方案包"
  compute:
    description: "GPU、推理端点、部署环境"
  data_service:
    description: "数据清洗、标注、解析、知识库处理"
  evaluation_service:
    description: "模型评测、Agent 测试、质量评估"
  security_service:
    description: "权限、审计、合规、安全红队测试"

module_boundaries:
  identity_module:
    owns:
      - "User"
      - "Organization"
      - "Role"
      - "AgentIdentity"
    cannot_own:
      - "Order settlement logic"
      - "Capability pricing logic"

  seller_module:
    owns:
      - "Seller"
      - "Store"
      - "SellerVerification"
      - "CapabilityDraft"
    cannot_own:
      - "Platform score calculation"
      - "Buyer private requirements"

  capability_module:
    owns:
      - "Capability"
      - "AgentCard"
      - "CapabilityVersion"
      - "CapabilityStatus"
    cannot_own:
      - "Payment"
      - "Settlement"

  requirement_module:
    owns:
      - "Requirement"
      - "RequirementDiagnosis"
      - "RequirementAttachment"
    cannot_own:
      - "Seller private data"

  transaction_module:
    owns:
      - "Quote"
      - "Order"
      - "Milestone"
      - "Delivery"
      - "Acceptance"
    cannot_own:
      - "Raw payment credential"

  payment_module:
    owns:
      - "Payment"
      - "Escrow"
      - "Settlement"
      - "Invoice"
      - "Refund"
    cannot_own:
      - "Capability content editing"

  review_module:
    owns:
      - "Review"
      - "Feedback"
      - "Rating"
      - "ReputationScore"
    cannot_own:
      - "Order amount modification"

  agent_gateway_module:
    owns:
      - "Agent API access"
      - "Agent permission checks"
      - "Agent budget checks"
      - "Agent execution proxy"
    cannot_own:
      - "Direct seller payout"

  audit_module:
    owns:
      - "AuditEvent"
      - "RiskEvent"
      - "SecurityLog"
    cannot_own:
      - "Business object mutation"

global_invariants:
  - id: "INV-001"
    rule: "AI Agent 必须绑定用户或组织，不允许匿名下单或付款。"
  - id: "INV-002"
    rule: "所有资金相关操作必须记录审计日志。"
  - id: "INV-003"
    rule: "能力商品上架前必须通过 AgentCard 基础字段校验。"
  - id: "INV-004"
    rule: "高风险能力不得由 AI Agent 全自动购买或调用。"
  - id: "INV-005"
    rule: "商家不能修改平台评分、真实交易评价和审计日志。"
  - id: "INV-006"
    rule: "买家上传的私有数据默认只用于当前订单或授权范围内的能力调用。"
  - id: "INV-007"
    rule: "平台运营访问敏感资料必须有理由、记录和权限。"
  - id: "INV-008"
    rule: "所有能力调用必须带 trace_id，方便审计和追踪。"
```

---

## 4. 最小验收标准

开发完成后，应能通过这些检查：

```text
1. 创建一个商家角色，只能管理自己的店铺和能力商品。
2. 创建一个企业买家角色，只能看到自己的需求和订单。
3. 创建一个 L1 Agent，只能搜索和比较能力，不能下单。
4. 创建一个 L4 Agent，在预算内只能调用低风险能力。
5. 高风险商品即使被搜索到，也不能被 Agent 自动购买。
6. 平台运营可以审核商品，但不能修改审计日志。
7. 资金结算必须走 payment_module，其他模块不能直接结算。
```

---

## 5. 给 AI 编码助手的提示词

```text
请根据本 Markdown 生成 config/boundaries.yaml，并在后端实现统一的权限检查器。
要求：
1. 权限不要硬编码在 API 路由里。
2. 每个 API 调用都必须检查 actor_type、role、scope、permission。
3. AI Agent 需要额外检查 permission_level、budget、risk_level。
4. 未在 boundaries.yaml 中声明的权限默认拒绝。
5. 为每条拒绝原因返回可读错误码。
```
