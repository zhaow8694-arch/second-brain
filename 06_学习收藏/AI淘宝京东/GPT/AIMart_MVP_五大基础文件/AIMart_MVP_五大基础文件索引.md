# AIMart MVP 五大基础文件索引

这是一组可以直接交给 AI 编码助手作为依据使用的 Markdown 规格文件。

## 文件列表

1. `AIMart_01_边界文件_boundary.md`  
   定义参与者、角色、权限、业务领域、能力类型、模块边界。

2. `AIMart_02_约束文件_constraints.md`  
   定义交易规则、预算规则、风险等级、安全约束、SLA、结算规则。

3. `AIMart_03_能力文件_AgentCard.md`  
   定义 AgentCard 机器可读能力商品标准、JSON Schema 和示例能力商品。

4. `AIMart_04_配置文件_config.md`  
   定义环境配置、接口配置、AI 服务配置、支付配置、功能开关。

5. `AIMart_05_日志与审计_audit.md`  
   定义审计策略、审计事件 Schema、日志格式、事件分类、追溯要求。

## 使用方式

把这五个 Markdown 文件交给你的 AI 编码助手，并要求它按照每个文件里的“AI 编码指令”和“提示词”生成实际项目文件。

建议生成的真实项目文件包括：

```text
config/boundaries.yaml
config/constraints.yaml
schemas/agentcard.schema.json
agent_cards/*.json
config/app_config.yaml
config/feature_flags.yaml
.env.example
config/audit_policy.yaml
schemas/audit_event.schema.json
```
