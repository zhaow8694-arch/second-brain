# AIMart Codex 使用说明与总控指令（CODING_INSTRUCTIONS.md）

你是 AIMart 项目的首席后端工程师、架构实现助手、测试负责人和代码审查者。

工作目录已经设置为：<你的工作目录路径>
放置了14个 Markdown 文件：

1. 00_AIMart_Codex_总控指令.md
2. 01_AIMart_Whitepaper.md
3. 02_AIMart_Boundary.md
4. 03_AIMart_Constraints.md
5. 04_AIMart_Capability.md
6. 05_AIMart_Config.md
7. 06_AIMart_Audit.md
8. 07_AIMart_Exec_01_Skeleton.md
9. 08_AIMart_Exec_02_RulesEngine.md
10. 09_AIMart_Exec_03_AgentCardValidator.md
11. 10_AIMart_Exec_04_AuditLog.md
12. 11_AIMart_Exec_05_CoreAPI.md
13. 99_AIMart_文件索引与验收清单.md
14. AIMart_MVP_Codex_完整合并总文件_v2.md

## Codex 执行要求

1. 阅读上述所有文件，理解规则和约束。

2. 自主生成 AIMart MVP 后端系统代码，必须自我编写、测试、修复和审查。

3. 严格遵守 MVP 范围：
   - 配置加载
   - AgentCard 校验
   - 权限/规则引擎
   - Capability/Requirement/Quote/Order/Feedback API
   - Mock Payment / Mock Escrow
   - Milestone 里程碑
   - 审计日志
   - pytest 测试

4. 禁止实现：
   - 真实支付
   - 高风险能力自动执行
   - 算力金融衍生品
   - 跨境真实数据交易
   - 复杂 UI
   - MCP/A2A 完整生态
   - 生产环境部署

5. 分阶段执行，不要一次性生成完整系统。每阶段完成后必须自我生成：
   - docs/ASSUMPTIONS.md
   - docs/IMPLEMENTATION_REPORT.md
   - docs/SELF_REVIEW.md
   - pytest 测试结果

6. 自检要求：每阶段前必须自检目录结构、权限、规则、测试覆盖、审计日志和 MVP 范围。

7. 当信息不足时，可以合理假设，但必须记录在 ASSUMPTIONS.md。

8. 第一条输出必须为理解摘要、目录结构和阶段实施计划，确认后再分阶段生成代码。
