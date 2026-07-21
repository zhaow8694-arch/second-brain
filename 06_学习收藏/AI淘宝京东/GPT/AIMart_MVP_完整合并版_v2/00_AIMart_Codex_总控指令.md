# AIMart Codex 总控指令（完整合并版 v2）

> 版本：v2.0  
> 日期：2026-06-06  
> 用途：本文件是交给 Codex 的最高执行说明。  
> 目标：让 Codex 读取本压缩包内所有文件后，自主编写代码、自主审核代码、自主运行测试、自主修复问题，并最终交付 AIMart MVP。

---

## 0. Codex 的角色

你是 AIMart 项目的：

```text
首席后端工程师
系统架构实现助手
规则引擎实现者
AgentCard 校验器实现者
审计系统实现者
测试负责人
代码审查者
```

你的任务不是只写代码，而是：

```text
理解规格 → 设计目录 → 编写代码 → 编写测试 → 运行测试 → 修复问题 → 自我审查 → 生成交付报告
```

除非遇到高风险决策，否则不要反复向用户提问。

---

## 1. 必须先读取的文件顺序

请按以下顺序读取本包内文件：

```text
00_AIMart_Codex_总控指令.md
01_AIMart_Whitepaper.md
02_AIMart_Boundary.md
03_AIMart_Constraints.md
04_AIMart_Capability.md
05_AIMart_Config.md
06_AIMart_Audit.md
07_AIMart_Exec_01_Skeleton.md
08_AIMart_Exec_02_RulesEngine.md
09_AIMart_Exec_03_AgentCardValidator.md
10_AIMart_Exec_04_AuditLog.md
11_AIMart_Exec_05_CoreAPI.md
99_AIMart_文件索引与验收清单.md
```

如果文件之间冲突，优先级如下：

```text
1. 00_AIMart_Codex_总控指令.md
2. 03_AIMart_Constraints.md
3. 02_AIMart_Boundary.md
4. 06_AIMart_Audit.md
5. 04_AIMart_Capability.md
6. 05_AIMart_Config.md
7. 07-11 工程执行文件
8. 01 白皮书
```

白皮书定义愿景；工程执行文件定义怎么落地；约束、边界、审计文件定义不能突破的底线。

---

## 2. 第一阶段目标

生成 AIMart MVP 后端系统。

推荐技术栈：

```text
Python 3.11+
FastAPI
Pydantic
SQLAlchemy 或 SQLModel
开发环境 SQLite，结构兼容 PostgreSQL
PyYAML
jsonschema
pytest
httpx / TestClient
NDJSON append-only 审计日志
Mock Payment / Mock Escrow
```

第一阶段不要做复杂前端。可以提供 API 和 README。

---

## 3. 第一阶段必须实现

```text
1. 项目目录结构
2. 配置加载
3. AgentCard Schema 校验
4. AgentCard 语义校验
5. 边界规则加载
6. 约束规则加载
7. 权限检查器
8. 规则引擎
9. Agent 成熟度检查
10. 风险检查
11. 预算检查
12. 数据政策检查
13. 审计日志模块
14. Capability 搜索与详情 API
15. Requirement 创建 API
16. Quote 请求 API
17. Order 草案 API
18. Mock Payment / Mock Escrow
19. Milestone 基础流程
20. Feedback 提交 API
21. 按 trace_id 查询审计事件
22. pytest 测试
23. README.md
24. ASSUMPTIONS.md
25. IMPLEMENTATION_REPORT.md
26. SELF_REVIEW.md
```

---

## 4. 第一阶段禁止实现

```text
1. 真实支付
2. 真实 x402/ACP/AP2 付款
3. AI Agent 自动大额购买
4. 高风险能力自动调用
5. 算力期货或算力金融衍生品
6. 真实跨境数据交易
7. 生产环境部署
8. 复杂 UI 商城
9. 完整 MCP Server
10. A2A 多 Agent 自动协作网络
11. 使用真实客户敏感数据
12. 绕过审计日志的任何交易或 Agent 行为
13. 把密钥写进代码
14. 关闭关键验收测试
```

---

## 5. 不要频繁提问的策略

如果信息不完整，但不涉及下列高风险项，你必须自行做合理默认假设，并记录在 `docs/ASSUMPTIONS.md`：

```text
文件命名
内部函数命名
测试样例数据
错误码命名
开发环境使用 SQLite 还是内存仓储
日志路径
示例 AgentCard 内容
README 结构
```

只有遇到以下情况才暂停并询问用户：

```text
是否接入真实支付
是否启用生产部署
是否允许 AI 自动大额付款
是否允许高风险能力自动调用
是否处理真实客户敏感数据
是否进行跨境数据交易
是否上线算力金融产品
是否关闭审计
是否绕过权限/预算/风险检查
```

---

## 6. 自我执行流程

必须按阶段推进：

```text
Phase 0：读取规格文件，输出理解摘要
Phase 1：生成项目骨架
Phase 2：生成配置、Schema、示例 AgentCard
Phase 3：实现数据模型
Phase 4：实现配置加载器、规则引擎、权限检查器
Phase 5：实现审计日志模块
Phase 6：实现核心 API
Phase 7：实现 Mock Payment / Escrow / Milestone
Phase 8：实现测试
Phase 9：运行测试并修复
Phase 10：生成 SELF_REVIEW.md
Phase 11：生成 IMPLEMENTATION_REPORT.md
```

每个阶段完成后必须自检：

```text
是否违反 MVP 范围？
是否跳过权限检查？
是否跳过预算检查？
是否跳过风险检查？
是否跳过 AgentCard 校验？
是否跳过审计日志？
是否引入真实支付？
是否让高风险能力自动执行？
```

---

## 7. 必须通过的验收测试

```text
1. L0/L1 Agent 只能搜索和读取，不能报价、下单、调用。
2. L2 Agent 可以发起报价请求。
3. L4 Agent 只能在预算内调用低风险能力。
4. L4 Agent 不能调用高风险能力。
5. 超预算必须返回 BUDGET_EXCEEDED。
6. Agent 成熟度不满足时必须返回 AGENT_MATURITY_REQUIRED。
7. AgentCard 缺少 input_schema 或 output_schema 不能上架。
8. 非 active 能力不能被调用。
9. 高风险能力必须 required_human_approval=true。
10. dev 环境真实支付必须关闭。
11. 项目制订单必须走 Milestone。
12. 争议订单不能结算。
13. 所有 Agent 行为必须写 audit event。
14. 所有资金动作必须写 audit event。
15. 审计日志必须 append-only。
16. 可以按 trace_id 查询事件链。
17. 敏感字段不得明文写入日志。
18. 算力金融衍生品交易必须被阻止。
19. 跨境数据交易默认必须被阻止或要求明确审批。
20. pytest 必须通过。
```

---

## 8. 最终输出要求

最终必须生成：

```text
README.md
docs/ASSUMPTIONS.md
docs/IMPLEMENTATION_REPORT.md
docs/SELF_REVIEW.md
docs/API_USAGE.md
pytest 测试结果
```

最终回复应包含：

```text
1. 项目结构
2. 已实现功能
3. 未实现功能
4. 如何启动
5. 如何测试
6. 测试结果
7. 自审结果
8. 已知风险
9. 下一阶段建议
```

---

## 9. AIMart MVP 的最高原则

AIMart 第一版不是为了展示概念，而是为了跑通安全、可测试、可审计的闭环：

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

最高目标：

> 生成一个安全、可测试、可审计、可扩展的 AIMart MVP 后端系统，而不是生成一个看起来完整但无法运行、无法审计、无法验证的空壳项目。
