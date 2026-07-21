# AIMart MVP 完整合并版 v2：文件索引与验收清单

> 生成日期：2026-06-06  
> 用途：直接交给 Codex。  
> 内容来源：你上传的 11 个文件 + 进一步合并补充的 Codex 自主执行、自审、自测、Agent 成熟度、跨境合规、算力金融化限制、MVP 禁止项。

---

## 1. 本包文件

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
```

---

## 2. 给 Codex 的第一条消息

请把下面内容直接发给 Codex：

```text
你是 AIMart 项目的首席后端工程师、架构实现助手、测试负责人和代码审查者。

请先阅读本仓库中的 00_AIMart_Codex_总控指令.md，并按其指定顺序读取所有 AIMart 规格文件。

你的目标是生成 AIMart MVP 后端系统。你必须自主编写代码、自主编写测试、自主运行测试、自主修复错误、自主生成 SELF_REVIEW.md 和 IMPLEMENTATION_REPORT.md。

不要频繁问我问题。除非涉及真实支付、生产部署、高风险能力自动调用、真实跨境数据、算力金融产品、真实客户敏感数据，否则请自行做合理默认假设并记录在 ASSUMPTIONS.md。

第一阶段只做 MVP：
- FastAPI 后端
- 配置加载
- AgentCard 校验
- 规则引擎
- 权限/预算/风险/成熟度/合规检查
- 审计日志
- Capability/Requirement/Quote/Order/Feedback API
- Mock Payment / Mock Escrow
- Milestone
- pytest 测试

禁止：
- 真实支付
- AI 自动大额购买
- 高风险能力自动调用
- 算力期货或金融衍生品
- 真实跨境数据交易
- 复杂 UI
- 完整 MCP/A2A 生态

请先输出你的理解摘要、目录结构和实施计划，然后继续分阶段实现。
```

---

## 3. Codex 最终必须交付

```text
README.md
requirements.txt
pytest.ini
.env.example
app/
config/
schemas/
agent_cards/
tests/
docs/ASSUMPTIONS.md
docs/IMPLEMENTATION_REPORT.md
docs/SELF_REVIEW.md
docs/API_USAGE.md
```

---

## 4. 最低验收清单

```text
[ ] pytest 能运行。
[ ] AgentCard Schema 校验有效。
[ ] 高风险能力不能被 Agent 自动调用。
[ ] L1 Agent 不能下单。
[ ] L4 Agent 只能在预算内调用低风险能力。
[ ] Agent 成熟度不足会被阻止。
[ ] 超预算返回 BUDGET_EXCEEDED。
[ ] 跨境数据默认阻止或需要审批。
[ ] 算力金融衍生品被阻止。
[ ] dev 环境真实支付关闭。
[ ] 所有 Agent 行为写审计。
[ ] 所有资金行为写审计。
[ ] 审计日志 append-only。
[ ] 可以按 trace_id 查询审计链路。
[ ] 生成 SELF_REVIEW.md。
[ ] 生成 IMPLEMENTATION_REPORT.md。
```

---

## 5. 注意

本包不是只给 Codex 读的战略文档，而是让 Codex 落地系统的施工规则。  
如果 Codex 只生成文档而不生成代码，让它重新按照 `00_AIMart_Codex_总控指令.md` 的 Phase 0-11 执行。
