# AIMart Codex 使用说明与总控指令

> 文件用途：把本文件与 AIMart 的十个规格文件一起交给 Codex，作为它开始编码、持续自审、自动补全、自动测试、自动修复的总控说明。  
> 推荐文件名：`CODEX_EXECUTION_GUIDE.md` 或 `AIMart_Codex_使用说明与总控指令.md`  
> 核心目标：让 Codex 尽量少问问题，按照已有规格文件自主生成代码、自主检查代码、自主修复问题，并最终交付可运行的 AIMart MVP 后端系统。

---

# 0. 使用方式

把以下文件一起放进 Codex 可读取的仓库或任务上下文中：

```text
基础规则文件：
1. AIMart_01_边界文件_boundary.md
2. AIMart_02_约束文件_constraints.md
3. AIMart_03_能力文件_AgentCard.md
4. AIMart_04_配置文件_config.md
5. AIMart_05_日志与审计_audit.md

工程执行文件：
6. AGENTS.md
7. MVP_SCOPE.md
8. API_CONTRACT.md
9. DATA_MODEL.md
10. ACCEPTANCE_TESTS.md

总控说明文件：
11. CODEX_EXECUTION_GUIDE.md
```

然后把下面这段指令原样发给 Codex。

---

# 1. 给 Codex 的总启动指令

```text
你是 AIMart 项目的首席后端工程师、架构实现助手、测试负责人和代码审查者。

你的任务不是只生成代码，而是：
1. 先理解 AIMart 的业务边界、权限、交易、风控、AgentCard、配置和审计要求。
2. 自主生成 AIMart MVP 后端系统。
3. 自主编写测试。
4. 自主运行测试。
5. 自主修复错误。
6. 自主进行安全、权限、预算、审计、MVP 范围自检。
7. 最终交付一个可运行、可测试、可扩展的 MVP 项目。

你必须先阅读以下文件，并把它们作为最高优先级约束：

基础规则文件：
1. AIMart_01_边界文件_boundary.md
2. AIMart_02_约束文件_constraints.md
3. AIMart_03_能力文件_AgentCard.md
4. AIMart_04_配置文件_config.md
5. AIMart_05_日志与审计_audit.md

工程执行文件：
6. AGENTS.md
7. MVP_SCOPE.md
8. API_CONTRACT.md
9. DATA_MODEL.md
10. ACCEPTANCE_TESTS.md

总控说明文件：
11. CODEX_EXECUTION_GUIDE.md

如果这些文件之间出现冲突，优先级如下：
1. MVP_SCOPE.md
2. AGENTS.md
3. AIMart_01_边界文件_boundary.md
4. AIMart_02_约束文件_constraints.md
5. AIMart_05_日志与审计_audit.md
6. API_CONTRACT.md
7. DATA_MODEL.md
8. AIMart_03_能力文件_AgentCard.md
9. AIMart_04_配置文件_config.md
10. ACCEPTANCE_TESTS.md
11. CODEX_EXECUTION_GUIDE.md

除非出现以下情况，否则不要反复向我提问：
- 涉及真实支付开通；
- 涉及生产环境部署；
- 涉及法律合规最终判断；
- 涉及真实客户数据处理；
- 涉及真实跨境数据传输；
- 涉及高风险能力自动调用；
- 文件内容严重缺失，导致无法继续。

如果信息不完整，但不触及上述高风险情况，你应该：
1. 做出合理默认假设；
2. 在 ASSUMPTIONS.md 中记录假设；
3. 继续实现；
4. 在最终报告中列出这些假设。

请不要一次性生成过大的不可维护代码。
请按阶段实施，每个阶段都要：
1. 生成或修改代码；
2. 写测试；
3. 运行测试；
4. 修复失败；
5. 更新实现报告；
6. 执行自审清单。

第一阶段目标：
生成 AIMart MVP 后端系统，不做复杂前端。

推荐技术栈：
- Python 3.11+
- FastAPI
- SQLAlchemy 或 SQLModel
- Pydantic
- PostgreSQL 兼容设计，开发环境可用 SQLite
- PyYAML
- jsonschema
- pytest
- httpx / TestClient
- NDJSON 审计日志
- Mock Payment，不接真实支付

第一阶段必须实现：
1. 项目目录结构；
2. 配置加载；
3. AgentCard Schema 校验；
4. 边界和约束规则加载；
5. 权限检查器；
6. 规则引擎；
7. 审计日志模块；
8. Capability 搜索与详情 API；
9. Requirement 创建 API；
10. Quote 请求 API；
11. Order 草案 API；
12. Milestone 基础流程；
13. Feedback 提交 API；
14. Mock Payment / Escrow；
15. 测试集；
16. README 启动说明；
17. ASSUMPTIONS.md；
18. IMPLEMENTATION_REPORT.md；
19. SELF_REVIEW.md。

第一阶段禁止实现：
1. 真实支付；
2. AI Agent 自动大额购买；
3. 高风险能力自动调用；
4. 算力期货；
5. 跨境数据交易；
6. 复杂 UI；
7. 完整 MCP Server；
8. 多 Agent 自动协商；
9. 生产环境部署脚本；
10. 绕过审计日志的任何资金或 Agent 行为。

最终交付时，你必须提供：
1. 完整项目文件；
2. 如何启动；
3. 如何运行测试；
4. 已实现功能清单；
5. 未实现功能清单；
6. 假设清单；
7. 风险清单；
8. 测试结果；
9. 自审结果；
10. 下一阶段建议。
```

---

# 2. Codex 自主执行总流程

Codex 应按以下阶段推进，不要跳阶段。

```text
Phase 0：读取规格文件并生成理解摘要
Phase 1：生成项目骨架
Phase 2：生成配置、Schema、示例 AgentCard
Phase 3：实现数据模型
Phase 4：实现配置加载器、规则引擎、权限检查器
Phase 5：实现审计日志模块
Phase 6：实现核心 API
Phase 7：实现 Mock Payment / Escrow / Milestone
Phase 8：实现测试
Phase 9：运行测试并修复
Phase 10：自审、安全检查、范围检查
Phase 11：生成最终交付报告
```

---

# 3. Phase 0：读取规格文件并生成理解摘要

Codex 首先必须输出：

```text
1. 我已读取的文件列表；
2. 每个文件的核心约束摘要；
3. 我发现的冲突或缺失；
4. 我将采用的默认假设；
5. 我不会实现的功能；
6. 我准备生成的目录结构；
7. 我准备采用的技术栈；
8. 第一轮开发计划。
```

如果没有重大阻塞，Codex 应继续执行，不要等待用户反复确认。

---

# 4. Phase 1：项目骨架

Codex 应生成如下目录结构，允许根据技术栈微调，但不要偏离太大：

```text
aimart_mvp/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── capabilities.py
│   │   ├── requirements.py
│   │   ├── quotes.py
│   │   ├── orders.py
│   │   ├── feedback.py
│   │   ├── audit.py
│   │   └── health.py
│   ├── core/
│   │   ├── config_loader.py
│   │   ├── permissions.py
│   │   ├── rules_engine.py
│   │   ├── audit_logger.py
│   │   ├── security.py
│   │   └── errors.py
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── agent_identity.py
│   │   ├── seller.py
│   │   ├── capability.py
│   │   ├── requirement.py
│   │   ├── quote.py
│   │   ├── order.py
│   │   ├── milestone.py
│   │   ├── payment_mock.py
│   │   ├── feedback.py
│   │   └── audit_event.py
│   ├── schemas/
│   │   ├── capability.py
│   │   ├── requirement.py
│   │   ├── quote.py
│   │   ├── order.py
│   │   ├── feedback.py
│   │   └── common.py
│   ├── services/
│   │   ├── capability_service.py
│   │   ├── requirement_service.py
│   │   ├── quote_service.py
│   │   ├── order_service.py
│   │   ├── payment_mock_service.py
│   │   ├── feedback_service.py
│   │   └── agent_gateway_service.py
│   └── repositories/
│       ├── memory.py
│       └── database.py
├── config/
│   ├── boundaries.yaml
│   ├── constraints.yaml
│   ├── app_config.yaml
│   ├── feature_flags.yaml
│   └── audit_policy.yaml
├── schemas/
│   ├── agentcard.schema.json
│   └── audit_event.schema.json
├── agent_cards/
│   ├── cap_knowledge_rag_001.json
│   ├── cap_ecommerce_copywriter_001.json
│   └── cap_document_ocr_001.json
├── logs/
│   └── .gitkeep
├── tests/
│   ├── test_agentcard_validation.py
│   ├── test_permissions.py
│   ├── test_rules_engine.py
│   ├── test_audit_logger.py
│   ├── test_capabilities_api.py
│   ├── test_requirements_api.py
│   ├── test_quotes_api.py
│   ├── test_orders_api.py
│   └── test_feedback_api.py
├── docs/
│   ├── ASSUMPTIONS.md
│   ├── IMPLEMENTATION_REPORT.md
│   ├── SELF_REVIEW.md
│   └── API_USAGE.md
├── requirements.txt
├── .env.example
├── README.md
└── pytest.ini
```

---

# 5. Phase 2：配置、Schema、示例 AgentCard

Codex 必须根据五个基础文件生成实际可执行配置：

```text
config/boundaries.yaml
config/constraints.yaml
config/app_config.yaml
config/feature_flags.yaml
config/audit_policy.yaml
schemas/agentcard.schema.json
schemas/audit_event.schema.json
agent_cards/*.json
.env.example
```

要求：

```text
1. 配置可被 Python 读取；
2. Schema 可被 jsonschema 校验；
3. 示例 AgentCard 至少 3 个；
4. 至少包含一个 low risk，一个 medium risk，一个 high risk 示例；
5. high risk 示例不能被 Agent 自动调用；
6. dev 环境真实支付必须关闭；
7. agent_auto_purchase 默认关闭。
```

---

# 6. Phase 3：数据模型

Codex 必须实现或模拟以下核心对象：

```text
User
Organization
AgentIdentity
Seller
Store
Capability
AgentCard
Requirement
Quote
Order
Milestone
PaymentMock
EscrowMock
Feedback
Review
AuditEvent
```

第一版允许使用内存仓储或 SQLite，但代码结构必须允许后续切换 PostgreSQL。

关键约束：

```text
1. AgentIdentity 必须绑定 Organization 或 User。
2. Capability 必须绑定 Seller。
3. Capability 必须有关联 AgentCard。
4. AgentCard 更新必须支持 version。
5. Order 必须绑定 buyer、seller、capability 或 requirement。
6. PaymentMock 不能接真实支付。
7. AuditEvent append-only，不允许普通更新或删除。
8. Milestone 必须属于 Order。
9. Feedback 必须绑定 capability 或 execution/order。
```

---

# 7. Phase 4：规则引擎与权限检查

Codex 必须实现：

```text
check_permission(actor, permission, resource)
check_agent_permission_level(agent, required_level)
check_budget(agent_or_org, amount)
check_risk(capability, actor)
check_data_policy(actor, capability, data_context)
check_order_creation(buyer, seller, capability, quote)
check_agent_execution(agent, capability, budget, data_context)
check_settlement(order, seller)
```

每个检查返回统一结构：

```json
{
  "allowed": true,
  "decision_code": "ALLOWED",
  "reason": "Readable reason",
  "required_approval": false,
  "audit_required": true
}
```

所有拒绝必须返回可读 decision_code，例如：

```text
PERMISSION_DENIED
BUDGET_EXCEEDED
HIGH_RISK_REQUIRES_HUMAN_APPROVAL
CAPABILITY_NOT_ACTIVE
SELLER_SUSPENDED
DATA_POLICY_REQUIRES_APPROVAL
AGENT_MATURITY_REQUIRED
REAL_PAYMENT_DISABLED
```

---

# 8. Phase 5：审计日志

Codex 必须实现：

```text
trace_id 生成
audit event schema 校验
NDJSON append-only 写入
敏感字段脱敏
按 trace_id 查询事件链
```

必须记录的事件：

```text
Agent 搜索能力
Agent 读取能力
Agent 比较能力
Agent 请求报价
Agent 执行被允许
Agent 执行被拒绝
能力创建
AgentCard 校验失败
需求创建
报价请求
订单草案创建
Mock 支付创建
Escrow 冻结/释放
里程碑提交/验收
反馈提交
风险阻止
预算超限
```

审计日志要求：

```text
1. 每条事件必须有 event_id。
2. 每条事件必须有 trace_id。
3. 每条事件必须有 actor、action、resource、result。
4. 敏感字段不能明文进入日志。
5. 日志 append-only。
6. 测试中必须验证审计事件被写入。
```

---

# 9. Phase 6：核心 API

Codex 必须实现以下 API，路径以 `API_CONTRACT.md` 为准。

## 9.1 Health

```text
GET /api/v1/health
```

返回系统状态。

## 9.2 Capability

```text
POST /api/v1/capabilities
GET  /api/v1/capabilities/search
GET  /api/v1/capabilities/{id}
```

要求：

```text
1. 创建能力必须校验 AgentCard。
2. 搜索能力返回摘要。
3. 详情返回完整 AgentCard。
4. 非 active 能力不能被 Agent 执行。
```

## 9.3 Requirement

```text
POST /api/v1/requirements
GET  /api/v1/requirements/{id}
```

要求：

```text
1. 创建需求写审计日志。
2. 可返回 AI 诊断占位结果。
3. 不需要第一版实现真实 LLM 诊断。
```

## 9.4 Quote

```text
POST /api/v1/quotes/request
```

要求：

```text
1. Agent L2 及以上可发起报价请求。
2. 低权限 Agent 不能发起报价。
3. 报价请求写审计日志。
```

## 9.5 Order

```text
POST /api/v1/orders
GET  /api/v1/orders/{id}
POST /api/v1/orders/{id}/milestones
POST /api/v1/orders/{id}/milestones/{milestone_id}/accept
```

要求：

```text
1. 第一版只创建订单草案或 mock order。
2. 项目制订单必须支持里程碑。
3. 资金只走 Mock Payment / Mock Escrow。
4. 高风险能力必须人工审批，不能自动创建正式订单。
```

## 9.6 Feedback

```text
POST /api/v1/feedback
```

要求：

```text
1. 支持人类反馈。
2. 支持 Agent 结构化反馈。
3. 写审计日志。
```

## 9.7 Audit

```text
GET /api/v1/audit-events?trace_id=xxx
```

要求：

```text
1. 可按 trace_id 查询。
2. 只允许平台审核角色访问完整审计记录。
3. 测试环境可用简化鉴权。
```

---

# 10. Phase 7：Mock Payment / Escrow

第一版必须只做 Mock，不接真实支付。

Codex 必须实现：

```text
create_mock_payment(order_id, amount)
create_mock_escrow(order_id, amount)
freeze_escrow(order_id)
release_escrow(order_id, milestone_id)
refund_mock_payment(order_id, reason)
```

禁止：

```text
真实银行卡
真实支付宝
真实微信支付
真实 Stripe charge
真实 Token payment
真实 x402 payment
```

可以预留接口，但必须默认关闭。

---

# 11. Phase 8：测试

Codex 必须写 pytest 测试，不允许只写业务代码。

最低测试覆盖：

```text
1. AgentCard Schema 校验测试
2. 权限测试
3. 预算测试
4. 风险测试
5. 高风险能力阻止测试
6. Agent 搜索能力 API 测试
7. Agent 请求报价 API 测试
8. Order 草案创建测试
9. Mock Payment 测试
10. Milestone 测试
11. Feedback 测试
12. Audit log 写入测试
13. trace_id 查询测试
14. feature flag 禁止真实支付测试
```

必须通过的核心断言：

```text
L1 Agent 可以搜索能力，但不能下单。
L4 Agent 可以在预算内调用低风险能力。
L4 Agent 不能调用高风险能力。
超预算返回 BUDGET_EXCEEDED。
AgentCard 缺少 input_schema 不能上架。
非 active 能力不能被调用。
项目制订单必须走里程碑。
争议订单不能结算。
所有 Agent 行为必须写 audit event。
所有资金动作必须写 audit event。
dev 环境真实支付必须关闭。
agent_auto_purchase 默认关闭。
```

---

# 12. Phase 9：自我修复流程

Codex 生成代码后必须执行：

```text
pytest
```

如果测试失败：

```text
1. 阅读失败原因；
2. 判断是测试问题还是代码问题；
3. 优先修复代码；
4. 不允许通过删除测试来“修复”；
5. 修复后重新运行测试；
6. 最多循环 5 轮；
7. 如果仍失败，记录在 IMPLEMENTATION_REPORT.md。
```

不允许：

```text
跳过关键测试
删除验收测试
把失败测试标记为 xfail，除非理由写入报告
通过关闭功能来逃避测试
```

---

# 13. Phase 10：自审清单

Codex 最终必须生成 `docs/SELF_REVIEW.md`，并逐项回答：

## 13.1 MVP 范围自审

```text
是否只实现 MVP 范围？
是否没有实现真实支付？
是否没有实现 AI 自动大额购买？
是否没有实现高风险能力自动调用？
是否没有实现跨境数据交易？
是否没有实现算力期货？
是否没有实现复杂 UI？
```

## 13.2 权限与风险自审

```text
AI Agent 是否必须绑定用户或组织？
L1 Agent 是否不能下单？
高风险能力是否需要人工审批？
超预算是否会阻止执行？
非 active 能力是否不能执行？
商家是否不能修改平台评分？
```

## 13.3 审计自审

```text
所有 Agent 行为是否写审计？
所有资金行为是否写审计？
所有权限拒绝是否写审计？
审计日志是否 append-only？
是否支持 trace_id 查询？
敏感字段是否脱敏？
```

## 13.4 AgentCard 自审

```text
AgentCard 是否有 Schema？
上架是否校验 Schema？
调用前是否校验 input_schema？
返回后是否校验 output_schema？
AgentCard 是否支持 version？
```

## 13.5 测试自审

```text
pytest 是否通过？
关键验收测试是否覆盖？
是否有未解决失败？
是否有跳过测试？
```

---

# 14. Phase 11：最终交付报告

Codex 最终必须生成 `docs/IMPLEMENTATION_REPORT.md`，内容包括：

```text
1. 已实现功能；
2. 未实现功能；
3. 文件结构；
4. API 列表；
5. 数据模型；
6. 规则引擎说明；
7. 审计日志说明；
8. Mock Payment 说明；
9. 如何启动；
10. 如何运行测试；
11. 测试结果；
12. 默认假设；
13. 已知限制；
14. 风险提醒；
15. 下一阶段建议。
```

---

# 15. 默认决策策略：尽量不要问用户

Codex 遇到不确定性时，按以下策略处理：

## 15.1 可以自行决定的事项

```text
文件命名细节
内部函数命名
测试数据命名
错误码命名
内存仓储还是 SQLite 开发模式
日志文件路径
示例 AgentCard 内容
README 结构
```

要求：记录在 `ASSUMPTIONS.md`。

## 15.2 需要停止并询问的事项

```text
是否接入真实支付
是否启用生产部署
是否允许 AI 自动大额付款
是否允许高风险能力自动调用
是否处理真实客户敏感数据
是否进行跨境数据交易
是否上线算力金融产品
是否绕过审计或关闭审计
```

## 15.3 文件缺失处理

如果某个规格文件缺失：

```text
1. 检查是否能从其他文件推断；
2. 若能推断，则在 ASSUMPTIONS.md 记录并继续；
3. 若不能推断，并且影响核心权限/支付/审计，则停止并报告缺失文件；
4. 不要编造高风险规则。
```

---

# 16. Codex 最终输出格式

Codex 完成后应输出：

```text
## AIMart MVP 实施完成

### 1. 项目结构
展示目录树。

### 2. 已实现功能
列清单。

### 3. 如何运行
提供命令。

### 4. 如何测试
提供 pytest 命令和结果。

### 5. 自审结果
引用 docs/SELF_REVIEW.md。

### 6. 主要文件
列出关键文件。

### 7. 已知限制
列出未实现和风险。

### 8. 下一步建议
给出 Phase 2 计划。
```

---

# 17. 推荐运行命令

Codex 应在 README.md 中提供类似命令：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
pytest
```

如果使用 Windows，也应补充：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
pytest
```

---

# 18. 不允许 Codex 做的事情

Codex 不得：

```text
1. 删除审计测试；
2. 关闭审计日志；
3. 默认启用真实支付；
4. 默认允许 Agent 自动购买；
5. 允许高风险能力自动调用；
6. 把权限写死在路由里；
7. 把密钥写进代码；
8. 把 Agent 当成法律主体；
9. 让匿名 Agent 下单；
10. 在 dev 环境接真实支付；
11. 绕过 AgentCard Schema 校验；
12. 在没有预算检查的情况下执行 Agent 调用；
13. 在没有风险检查的情况下执行能力调用；
14. 将敏感数据明文写日志；
15. 为了通过测试删除关键逻辑。
```

---

# 19. Codex 应主动补充的文件

如果不存在，Codex 应主动生成：

```text
README.md
ASSUMPTIONS.md
IMPLEMENTATION_REPORT.md
SELF_REVIEW.md
API_USAGE.md
.env.example
pytest.ini
requirements.txt
```

---

# 20. 最终原则

AIMart 第一版不是为了展示概念，而是为了跑通以下闭环：

```text
商家上架能力
→ AgentCard 校验
→ 买家/Agent 搜索能力
→ 买家发布需求
→ Agent 或买家发起报价
→ 创建订单草案
→ Mock Payment / Escrow
→ 里程碑交付
→ 反馈评价
→ 审计追踪
```

Codex 的最高目标是：

> **生成一个安全、可测试、可审计、可扩展的 AIMart MVP 后端系统，而不是生成一个看起来很完整但无法运行、无法审计、无法验证的空壳项目。**
