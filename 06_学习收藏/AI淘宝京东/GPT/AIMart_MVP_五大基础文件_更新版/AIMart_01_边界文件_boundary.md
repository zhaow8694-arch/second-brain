# AIMart 边界文件（更新版）：参与者、角色、权限、业务领域

## 新增字段：Agent 成熟度 & 支付协议
agent_maturity:
  production_ready_required: true
  max_concurrent_execution: 5
  sandbox_required_for_new_agents: true

m2m_payment_protocols:
  - x402
  - ACP
  - SPT

legal_binding_required: true
